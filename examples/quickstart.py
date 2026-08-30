"""Run with: python examples/quickstart.py"""

from agentguard import AgentGuard


def search(query):
    print(f"[TOOL EXECUTED] search({query!r})")
    return f"Search results for {query!r}"


def refund(customer_id, amount):
    print(f"[TOOL EXECUTED] refund({customer_id!r}, {amount})")
    return f"Refunded ${amount} to {customer_id}"


guard = AgentGuard({
    "research": {"allowed_tools": ["search"]},
    "execution": {
        "allowed_tools": ["search", "refund"],
        "argument_rules": {"refund": {"amount": {"max": 500}}},
    },
})


def show(label, **request):
    print(f"\n{label}")
    result = guard.call(**request)
    print(result)


show(
    "1. Allowed call: the search function runs.",
    state="research",
    tool="search",
    function=search,
    arguments={"query": "agent authorization"},
)
show(
    "2. Unauthorized call: refund does not run in research.",
    state="research",
    tool="refund",
    function=refund,
    arguments={"customer_id": "cust_123", "amount": 100},
)
show(
    "3. Dangerous argument: refund does not run above the $500 limit.",
    state="execution",
    tool="refund",
    function=refund,
    arguments={"customer_id": "cust_123", "amount": 5_000},
)

print("\nAudit decisions:")
for event in guard.audit_log.get_events():
    print(f"{event['decision']}: {event['state']} / {event['tool']} - {event['reason']}")
