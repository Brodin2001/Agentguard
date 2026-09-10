"""Minimal AgentGuard adapter for OpenWorkProof's apply-patch boundary.

Target OWP release: v1.4.0
Target OWP commit: 14e967501ac164ba966c635a90b819c8bd60c2fb

This example deliberately does not modify OpenWorkProof. It derives the
AgentGuard action from the exact OWP execution inputs and binds the receipt
to that executable capability before entering OWP's protected executor.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from agentguard import AgentGuard


OWP_TOOL = "owp.apply_patch"


def build_guard() -> AgentGuard:
    """Create the smallest policy needed for this experiment."""
    return AgentGuard({"patch": {"allowed_tools": [OWP_TOOL]}})


def make_owp_executor(
    *,
    ledger_path: Path,
    evidence_root: Path,
    context: Any,
    request: Any,
    request_arguments: Any,
    execution_facts: Any,
    sidecar_private_key: Any,
    patch_bytes: bytes,
    candidate_workspace: Any,
    handler: Callable[..., Any],
    clock: Callable[[], datetime],
) -> Callable[[], Any]:
    """Bind the exact pinned OWP ``execute_apply_patch`` call."""
    from openworkproof.mcp_server import execute_apply_patch

    def execute() -> Any:
        return execute_apply_patch(
            ledger_path,
            evidence_root=evidence_root,
            context=context,
            request=request,
            request_arguments=request_arguments,
            execution_facts=execution_facts,
            sidecar_private_key=sidecar_private_key,
            patch_bytes=patch_bytes,
            candidate_workspace=candidate_workspace,
            handler=handler,
            clock=clock,
        )

    return execute


def guarded_apply_patch(
    *,
    guard: AgentGuard,
    ledger_path: Path,
    evidence_root: Path,
    context: Any,
    request: Any,
    request_arguments: Any,
    execution_facts: Any,
    sidecar_private_key: Any,
    patch_bytes: bytes,
    candidate_workspace: Any,
    handler: Callable[..., Any],
    clock: Callable[[], datetime],
    ttl_seconds: float = 30.0,
) -> dict[str, Any]:
    """Authorize and execute the exact OWP apply-patch operation.

    The caller cannot supply a separate AgentGuard declaration or arbitrary
    execution closure. The action is derived from the actual OWP request,
    arguments, patch payload, candidate workspace, and execution facts.

    Mutable caller-owned execution inputs are snapshotted before authorization.
    Authorization and execution therefore operate on the same execution
    snapshots.
    """
    execution_request = deepcopy(request)
    execution_request_arguments = deepcopy(request_arguments)
    execution_facts_snapshot = deepcopy(execution_facts)
    execution_candidate_workspace = deepcopy(candidate_workspace)

    target_paths = list(execution_request_arguments.target_paths)

    actual_patch_digest = hashlib.sha256(patch_bytes).hexdigest()

    action_arguments = {
        "operation": OWP_TOOL,
        "target_paths": target_paths,
        "patch_digest": actual_patch_digest,
        "patch_size_bytes": len(patch_bytes),
    }

    workspace_target = str(
        execution_candidate_workspace.worktree.resolve()
    )

    agent_id = execution_request.actor_id
    runtime_id = execution_facts_snapshot.execution_context_id

    executor = make_owp_executor(
        ledger_path=ledger_path,
        evidence_root=evidence_root,
        context=context,
        request=execution_request,
        request_arguments=execution_request_arguments,
        execution_facts=execution_facts_snapshot,
        sidecar_private_key=sidecar_private_key,
        patch_bytes=patch_bytes,
        candidate_workspace=execution_candidate_workspace,
        handler=handler,
        clock=clock,
    )

    def bound_executor(**_arguments: Any) -> Any:
        return executor()

    capability_id = guard.bind_tool(
        OWP_TOOL,
        bound_executor,
    )

    receipt = guard.issue_receipt(
        state="patch",
        tool=OWP_TOOL,
        arguments=action_arguments,
        target=workspace_target,
        agent_id=agent_id,
        runtime_id=runtime_id,
        ttl_seconds=ttl_seconds,
        capability_id=capability_id,
    )

    return guard.execute_receipt(
        receipt,
        arguments=action_arguments,
        target=workspace_target,
        agent_id=agent_id,
        runtime_id=runtime_id,
    )


if __name__ == "__main__":
    print(
        "Use guarded_apply_patch(...) with the pinned "
        "OpenWorkProof execution context."
    )
