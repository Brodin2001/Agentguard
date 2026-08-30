from agentguard import AgentGuard


# --------------------------------
# Real tools
# --------------------------------

def search(query):
    print(f"[TOOL EXECUTED] search: {query}")
    return f"Results for '{query}'"


def delete_customer(customer_id):
    print(f"[TOOL EXECUTED] DELETE CUSTOMER: {customer_id}")
    return f"Customer {customer_id} deleted"


def issue_refund(customer_id, amount):
    print(
        f"[TOOL EXECUTED] REFUND: "
        f"customer={customer_id}, amount=${amount}"
    )
    return f"Refunded ${amount}"


# --------------------------------
# Security policy
# --------------------------------

policies = {
    "research": {
        "allowed_tools": [
            "search"
        ]
    },

    "execution": {
        "allowed_tools": [
            "search",
            "issue_refund"
        ],
        "argument_rules": {
            "issue_refund": {
                "amount": {
                    "max": 500,
                    "min": 1
                }
            }
        }
    }
}


guard = AgentGuard(policies)


# --------------------------------
# Attack 1
# Unauthorized tool
# --------------------------------

print("\n=== ATTACK 1: UNAUTHORIZED TOOL ===")

result = guard.call(
    state="research",
    tool="delete_customer",
    function=delete_customer,
    arguments={
        "customer_id": "123"
    }
)

print(result)


# --------------------------------
# Attack 2
# Dangerous argument
# --------------------------------

print("\n=== ATTACK 2: EXCESSIVE REFUND ===")

result = guard.call(
    state="execution",
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "customer_id": "123",
        "amount": 5000
    }
)

print(result)


# --------------------------------
# Legitimate action
# --------------------------------

print("\n=== LEGITIMATE ACTION ===")

result = guard.call(
    state="execution",
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "customer_id": "123",
        "amount": 100
    }
)

print(result)


# --------------------------------
# Security check
# --------------------------------

print("\n=== AUDIT LOG ===")

for event in guard.audit_log.get_events():
    print(
        f"{event['decision']} | "
        f"{event['state']} | "
        f"{event['tool']} | "
        f"{event['reason']}"
    )