from agentguard import AgentGuard


# --------------------------------
# Example tools
# --------------------------------

def search(query):
    print(f"  [TOOL] Searching for: {query}")
    return f"Results for '{query}'"


def issue_refund(customer_id, amount):
    print(
        f"  [TOOL] REFUND EXECUTED "
        f"customer={customer_id}, amount=${amount}"
    )
    return f"Refunded ${amount} to customer {customer_id}"


# --------------------------------
# AgentGuard policy
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
                    "max": 500
                }
            }
        }
    }
}


guard = AgentGuard(policies)


# --------------------------------
# Simulated agent requests
# --------------------------------

requests = [
    {
        "description": "Research customer complaints",
        "state": "research",
        "tool": "search",
        "function": search,
        "arguments": {
            "query": "customer complaints"
        }
    },

    {
        "description": "Attempt refund during research",
        "state": "research",
        "tool": "issue_refund",
        "function": issue_refund,
        "arguments": {
            "customer_id": "123",
            "amount": 100
        }
    },

    {
        "description": "Issue approved refund",
        "state": "execution",
        "tool": "issue_refund",
        "function": issue_refund,
        "arguments": {
            "customer_id": "123",
            "amount": 100
        }
    },

    {
        "description": "Attempt excessive refund",
        "state": "execution",
        "tool": "issue_refund",
        "function": issue_refund,
        "arguments": {
            "customer_id": "123",
            "amount": 5000
        }
    }
]


# --------------------------------
# Run requests through AgentGuard
# --------------------------------

print("\n======================================")
print("        AgentGuard v0.1 Demo")
print("======================================")

for request in requests:

    print(f"\nRequest: {request['description']}")

    result = guard.call(
        state=request["state"],
        tool=request["tool"],
        function=request["function"],
        arguments=request["arguments"]
    )

    if result["allowed"]:
        print("  Decision: ALLOWED")
        print(f"  Result: {result['result']}")

    else:
        print("  Decision: DENIED")
        print(f"  Reason: {result['reason']}")


# --------------------------------
# Audit log
# --------------------------------

print("\n======================================")
print("             Audit Log")
print("======================================")

for event in guard.audit_log.get_events():

    print(
        f"{event['timestamp']} | "
        f"{event['state']} | "
        f"{event['tool']} | "
        f"{event['decision']} | "
        f"{event['reason']}"
    )