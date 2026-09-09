"""Minimal AgentGuard adapter for OpenWorkProof's apply-patch boundary.

Target OWP release: v1.4.0
Target OWP commit: 14e967501ac164ba966c635a90b819c8bd60c2fb

This example deliberately does not modify OpenWorkProof. It places the
AgentGuard receipt check immediately before the call into OWP's protected
``execute_apply_patch`` path.

The OWP executor remains responsible for its own authorization, validation,
receipt/evidence publication, and filesystem mutation. AgentGuard is the
additional execution-boundary check under test.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from agentguard import AgentGuard


OWP_TOOL = "owp.apply_patch"


def build_guard() -> AgentGuard:
    """Create the smallest policy needed for this experiment."""
    return AgentGuard(
        {
            "patch": {
                "allowed_tools": [OWP_TOOL],
            }
        }
    )


def guarded_apply_patch(
    *,
    guard: AgentGuard,
    action_arguments: Mapping[str, Any],
    workspace_target: str,
    agent_id: str,
    runtime_id: str,
    execute_owp: Callable[[], Any],
    ttl_seconds: float = 30.0,
) -> dict[str, Any]:
    """Run one OWP apply-patch operation behind an AgentGuard receipt.

    ``action_arguments`` must describe the exact action that is about to be
    handed to OWP. For the v1.4.0 experiment this should include, at minimum,
    the operation name, declared target paths, patch digest, and patch size.
    ``workspace_target`` identifies the disposable candidate workspace.

    ``execute_owp`` should be a zero-argument closure around the real OWP
    ``execute_apply_patch(...)`` invocation. The closure prevents the caller
    from silently substituting a different OWP call after AgentGuard has
    authorized the candidate action.
    """
    arguments = dict(action_arguments)

    receipt = guard.issue_receipt(
        state="patch",
        tool=OWP_TOOL,
        arguments=arguments,
        target=workspace_target,
        agent_id=agent_id,
        runtime_id=runtime_id,
        ttl_seconds=ttl_seconds,
    )

    # This is the intended AgentGuard placement: verification/consumption
    # happens immediately before entering OpenWorkProof's protected executor.
    return guard.execute_receipt(
        receipt,
        lambda **_: execute_owp(),
        arguments=arguments,
        target=workspace_target,
        agent_id=agent_id,
        runtime_id=runtime_id,
    )


if __name__ == "__main__":
    guard = build_guard()
    action = {
        "operation": OWP_TOOL,
        "target_paths": ["src/demo.py"],
        "patch_digest": "replace-with-sha256-of-patch-bytes",
        "patch_size_bytes": 42,
    }

    result = guarded_apply_patch(
        guard=guard,
        action_arguments=action,
        workspace_target="disposable-openworkproof-workspace",
        agent_id="openworkproof-test-agent",
        runtime_id="agentguard-owp-v1.4.0-test",
        execute_owp=lambda: print(
            "Call the pinned OpenWorkProof execute_apply_patch(...) here."
        ),
    )
    print(result)
