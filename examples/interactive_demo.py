from agentguard import AgentGuard


# --------------------------------
# Example tools
# --------------------------------

def search(query):
    print(f"\n[TOOL EXECUTED] search('{query}')")
    return f"Search results for '{query}'"


def issue_refund(customer_id, amount):
    print(
        f"\n[TOOL EXECUTED] issue_refund("
        f"customer_id='{customer_id}', amount=${amount})"
    )
    return f"Refunded ${amount} to customer {customer_id}"


def delete_customer(customer_id):
    print(
        f"\n[TOOL EXECUTED] delete_customer("
        f"customer_id='{customer_id}')"
    )
    return f"Customer {customer_id} deleted"


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
                    "min": 1,
                    "max": 500
                }
            }
        }
    }
}


guard = AgentGuard(policies)


# --------------------------------
# Available tools
# --------------------------------

tools = {
    "1": ("search", search),
    "2": ("issue_refund", issue_refund),
    "3": ("delete_customer", delete_customer),
}


# --------------------------------
# Main interactive loop
# --------------------------------

print("\n========================================")
print("       AgentGuard Interactive Demo")
print("========================================")

print("\nThis demo lets you test AgentGuard's")
print("runtime tool authorization yourself.")

print("\nAvailable states:")
print("1. research")
print("2. execution")


while True:

    print("\n----------------------------------------")

    state_choice = input(
        "\nChoose state (1/2) or 'q' to quit: "
    ).strip().lower()

    if state_choice == "q":
        break

    if state_choice == "1":
        state = "research"

    elif state_choice == "2":
        state = "execution"

    else:
        print("Invalid state.")
        continue

    print(f"\nCurrent state: {state}")

    print("\nAvailable tools:")

    for number, (name, _) in tools.items():
        print(f"{number}. {name}")

    tool_choice = input(
        "\nChoose a tool (1/2/3): "
    ).strip()

    if tool_choice not in tools:
        print("Invalid tool.")
        continue

    tool_name, function = tools[tool_choice]

    # --------------------------------
    # Collect arguments
    # --------------------------------

    if tool_name == "search":

        query = input(
            "Search query: "
        )

        arguments = {
            "query": query
        }

    elif tool_name == "issue_refund":

        customer_id = input(
            "Customer ID: "
        )

        amount_input = input(
            "Refund amount: $"
        )

        try:
            amount = float(amount_input)
        except ValueError:
            print("Invalid amount.")
            continue

        arguments = {
            "customer_id": customer_id,
            "amount": amount
        }

    elif tool_name == "delete_customer":

        customer_id = input(
            "Customer ID: "
        )

        arguments = {
            "customer_id": customer_id
        }

    # --------------------------------
    # AgentGuard enforcement
    # --------------------------------

    print("\n[AGENT REQUEST]")
    print(f"State: {state}")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")

    result = guard.call(
        state=state,
        tool=tool_name,
        function=function,
        arguments=arguments
    )

    print("\n[AGENTGUARD DECISION]")

    if result["allowed"]:

        print("Decision: ALLOWED")
        print("Tool executed: YES")
        print(f"Result: {result['result']}")

    else:

        print("Decision: DENIED")
        print("Tool executed: NO")
        print(f"Reason: {result['reason']}")


# --------------------------------
# Audit log
# --------------------------------

print("\n========================================")
print("             Audit Log")
print("========================================")

events = guard.audit_log.get_events()

if not events:

    print("No tool requests were made.")

else:

    for event in events:

        print(
            f"{event['decision']} | "
            f"{event['state']} | "
            f"{event['tool']} | "
            f"{event['reason']}"
        )

print("\nDemo complete.")