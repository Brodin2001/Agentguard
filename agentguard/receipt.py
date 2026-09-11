"""Action-bound authorization receipts for AgentGuard v0.2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Callable, Mapping


def canonicalize(value: Any) -> str:
    """Return a deterministic JSON representation of an action value."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def action_digest(
    tool: str,
    arguments: Mapping[str, Any],
    target: str | None,
    agent_id: str | None,
    runtime_id: str | None,
) -> str:
    """Hash the exact candidate action that the receipt authorizes."""
    action = {
        "tool": tool,
        "arguments": arguments,
        "target": target,
        "agent_id": agent_id,
        "runtime_id": runtime_id,
    }
    return hashlib.sha256(canonicalize(action).encode("utf-8")).hexdigest()


def policy_digest(policy: Mapping[str, Any]) -> str:
    """Hash the policy used to issue the receipt."""
    return hashlib.sha256(canonicalize(policy).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorizationReceipt:
    """Short-lived authority for one exact action and executable capability.

    The MAC makes the receipt tamper-evident within the AgentGuard process.
    It is not a claim of protection against arbitrary malicious code with
    equivalent access to the same Python process.
    """

    state: str
    tool: str
    capability_id: str
    arguments_hash: str
    target: str | None
    agent_id: str | None
    runtime_id: str | None
    policy_hash: str
    issued_at: float
    expires_at: float
    nonce: str
    _mac: str

    @property
    def decision_id(self) -> str:
        return self.nonce


class ReceiptAuthority:
    """Issue and consume action-bound authorization receipts."""

    def __init__(
        self,
        policy_provider: Callable[[], Mapping[str, Any]],
        secret: bytes | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._policy_provider = policy_provider
        self._secret = secret or secrets.token_bytes(32)
        self._clock = clock
        self._consumed: set[str] = set()

    def issue(
        self,
        state: str,
        tool: str,
        capability_id: str,
        arguments: Mapping[str, Any],
        target: str | None = None,
        agent_id: str | None = None,
        runtime_id: str | None = None,
        ttl_seconds: float = 30.0,
    ) -> AuthorizationReceipt:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        issued_at = self._clock()
        expires_at = issued_at + ttl_seconds
        nonce = secrets.token_urlsafe(18)
        arguments_hash = action_digest(
            tool, arguments, target, agent_id, runtime_id
        )
        policies = self._policy_provider()
        policy_hash = policy_digest(policies[state])

        unsigned = self._signing_payload(
            state=state,
            tool=tool,
            capability_id=capability_id,
            arguments_hash=arguments_hash,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
            policy_hash=policy_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            nonce=nonce,
        )
        mac = hmac.new(
            self._secret,
            unsigned.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return AuthorizationReceipt(
            state=state,
            tool=tool,
            capability_id=capability_id,
            arguments_hash=arguments_hash,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
            policy_hash=policy_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            nonce=nonce,
            _mac=mac,
        )

    def verify_and_consume(
        self,
        receipt: AuthorizationReceipt,
        tool: str,
        capability_id: str,
        arguments: Mapping[str, Any],
        target: str | None = None,
        agent_id: str | None = None,
        runtime_id: str | None = None,
    ) -> tuple[bool, str]:
        """Verify exact action, capability, policy freshness, expiry, integrity, and replay."""
        now = self._clock()

        if receipt.nonce in self._consumed:
            return False, "Authorization receipt has already been consumed."

        expected_mac = hmac.new(
            self._secret,
            self._signing_payload(
                state=receipt.state,
                tool=receipt.tool,
                capability_id=receipt.capability_id,
                arguments_hash=receipt.arguments_hash,
                target=receipt.target,
                agent_id=receipt.agent_id,
                runtime_id=receipt.runtime_id,
                policy_hash=receipt.policy_hash,
                issued_at=receipt.issued_at,
                expires_at=receipt.expires_at,
                nonce=receipt.nonce,
            ).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(receipt._mac, expected_mac):
            return False, "Authorization receipt integrity check failed."

        if now >= receipt.expires_at:
            return False, "Authorization receipt has expired."

        policies = self._policy_provider()
        if receipt.state not in policies:
            return False, "Authorization receipt state no longer exists."
        current_policy_hash = policy_digest(policies[receipt.state])
        if receipt.policy_hash != current_policy_hash:
            return False, "Authorization receipt policy is stale."

        if receipt.tool != tool:
            return False, "Tool does not match the authorized action."

        if receipt.capability_id != capability_id:
            return False, "Executable capability does not match the authorized action."

        if receipt.target != target:
            return False, "Target does not match the authorized action."

        if receipt.agent_id != agent_id:
            return False, "Agent identity does not match the authorized action."

        if receipt.runtime_id != runtime_id:
            return False, "Runtime identity does not match the authorized action."

        expected_digest = action_digest(
            tool, arguments, target, agent_id, runtime_id
        )
        if receipt.arguments_hash != expected_digest:
            return False, "Arguments do not match the authorized action."

        self._consumed.add(receipt.nonce)
        return True, "Authorization receipt verified."

    @staticmethod
    def _signing_payload(**values: Any) -> str:
        return canonicalize(values)
