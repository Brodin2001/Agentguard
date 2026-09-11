from agentguard import AgentGuard


def refund(customer_id, amount):
    return f"Refunded ${amount} to {customer_id}"


guard = AgentGuard({
    "execution": {
        "allowed_tools": ["refund"],
        "argument_rules": {
            "refund": {
                "amount": {"min": 1, "max": 500}
            }
        },
    }
})

arguments = {"customer_id": "customer-123", "amount": 100}

receipt = guard.issue_receipt(
    state="execution",
    tool="refund",
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)

allowed = guard.execute_receipt(
    receipt,
    refund,
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)
print("ALLOWED:", allowed)

attack_receipt = guard.issue_receipt(
    state="execution",
    tool="refund",
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)

changed = guard.execute_receipt(
    attack_receipt,
    refund,
    arguments={"customer_id": "customer-123", "amount": 400},
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)
print("CHANGED ARGUMENT:", changed)
