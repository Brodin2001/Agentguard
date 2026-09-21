"""Harmless source-level fixture for the execution-boundary challenge.

This fixture mirrors the relevant shape of an MCP tool handler that receives the
current call arguments and forwards them to a consequential downstream effect.

It is NOT a live test of achetronic/hass-mcp and does not claim a vulnerability.
Its purpose is to make the A -> mutate B question reproducible with no external
side effect, then show how AgentGuard's action-bound receipt behaves on the same
negative path.
"""

from agentguard import AgentGuard


class RecordingHomeAssistantBoundary:
    """Record would-be effects instead of touching a real Home Assistant."""

    def __init__(self):
        self.calls = []

    def entity_action(self, entity_id: str, action: str):
        call = {"entity_id": entity_id, "action": action}
        self.calls.append(call)
        return call


def run_fixture():
    authorized_a = {
        "entity_id": "light.living_room",
        "action": "off",
    }
    mutated_b = {
        "entity_id": "light.kitchen",
        "action": "off",
    }

    # Control 1: an unbound downstream handler receives B and therefore
    # has no earlier A to compare against. No real device is touched.
    raw_boundary = RecordingHomeAssistantBoundary()
    raw_boundary.entity_action(**mutated_b)

    # Control 2: AgentGuard binds a receipt to exact action A.
    protected_boundary = RecordingHomeAssistantBoundary()
    guard = AgentGuard({
        "execution": {
            "allowed_tools": ["entity_action"],
        }
    })
    guard.bind_tool("entity_action", protected_boundary.entity_action)

    negative_receipt = guard.issue_receipt(
        state="execution",
        tool="entity_action",
        arguments=authorized_a,
        target=authorized_a["entity_id"],
        agent_id="agent-fixture",
        runtime_id="run-fixture",
    )

    negative = guard.execute_receipt(
        negative_receipt,
        arguments=mutated_b,
        target=mutated_b["entity_id"],
        agent_id="agent-fixture",
        runtime_id="run-fixture",
    )

    assert raw_boundary.calls == [mutated_b]
    assert negative["allowed"] is False
    assert negative["executed"] is False
    assert protected_boundary.calls == []

    positive_receipt = guard.issue_receipt(
        state="execution",
        tool="entity_action",
        arguments=authorized_a,
        target=authorized_a["entity_id"],
        agent_id="agent-fixture",
        runtime_id="run-fixture-positive",
    )

    positive = guard.execute_receipt(
        positive_receipt,
        arguments=authorized_a,
        target=authorized_a["entity_id"],
        agent_id="agent-fixture",
        runtime_id="run-fixture-positive",
    )

    assert positive["allowed"] is True
    assert positive["executed"] is True
    assert protected_boundary.calls == [authorized_a]

    return {
        "raw_mutated_effect": raw_boundary.calls[0],
        "negative_control": {
            "allowed": negative["allowed"],
            "executed": negative["executed"],
            "reason": negative["reason"],
        },
        "positive_control": {
            "allowed": positive["allowed"],
            "executed": positive["executed"],
            "result": positive["result"],
        },
    }


if __name__ == "__main__":
    result = run_fixture()
    print("RAW BOUNDARY:", result["raw_mutated_effect"])
    print("NEGATIVE CONTROL:", result["negative_control"])
    print("POSITIVE CONTROL:", result["positive_control"])
