"""
AgentGuard Developer Integration Demo

This demonstrates the intended integration pattern:

AI Agent
    ↓
Tool Request
    ↓
AgentGuard
    ↓
ALLOW / DENY
    ↓
Real Tool
"""

from agentguard import AgentGuard


# =========================================================
# 1. YOUR EXISTING AGENT TOOLS
# =========================================================

def search_customer(customer_id):
    print(
        f"[REAL TOOL] Searching customer {customer_id}"
    )

    return {
        "customer_id": customer_id,
        "name": "John Smith",
        "status": "active"
    }


def get_invoice(invoice_id):
    print(
        f"[REAL TOOL] Looking up invoice {invoice_id}"
    )

    return {
        "invoice_id": invoice_id,
        "amount": 250,
        "status": "eligible_for_refund"
    }


def issue_refund(invoice_id, amount):
    print(
        f"[REAL TOOL] REFUND EXECUTED "
        f"invoice={invoice_id}, amount=${amount}"
    )

    return {
        "invoice_id": invoice_id,
        "refunded": amount,
        "status": "refund_processed"
    }


def delete_customer(customer_id):
    print(
        f"[REAL TOOL] DELETE CUSTOMER EXECUTED "
        f"customer={customer_id}"
    )

    return {
        "customer_id": customer_id,
        "status": "deleted"
    }


# =========================================================
# 2. AGENTGUARD POLICY
# =========================================================

POLICIES = {

    "research": {

        "allowed_tools": [
            "search_customer",
            "get_invoice"
        ]
    },

    "execution": {

        "allowed_tools": [
            "search_customer",
            "get_invoice",
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


# =========================================================
# 3. CREATE AGENTGUARD
# =========================================================

guard = AgentGuard(POLICIES)


# =========================================================
# 4. AGENT TOOL REGISTRY
# =========================================================

TOOLS = {

    "search_customer": search_customer,

    "get_invoice": get_invoice,

    "issue_refund": issue_refund,

    "delete_customer": delete_customer
}


# =========================================================
# 5. SIMULATED AGENT TOOL CALL
# =========================================================

def agent_request(
    state,
    tool,
    arguments
):

    print("\n" + "=" * 60)

    print("AGENT TOOL REQUEST")

    print("=" * 60)

    print(f"State:     {state}")
    print(f"Tool:      {tool}")
    print(f"Arguments: {arguments}")

    print("\nSending request through AgentGuard...")

    result = guard.call(
        state=state,
        tool=tool,
        function=TOOLS[tool],
        arguments=arguments
    )

    print("\nAGENTGUARD RESULT")

    print(f"Allowed:   {result['allowed']}")

    if result["allowed"]:

        print("Executed:  YES")
        print(f"Result:    {result['result']}")

    else:

        print("Executed:  NO")
        print(f"Reason:    {result['reason']}")

    return result


# =========================================================
# 6. DEMO
# =========================================================

print()
print("=" * 60)
print("              AGENTGUARD")
print("       Developer Integration Demo")
print("=" * 60)


# ---------------------------------------------------------
# TEST 1
# Legitimate research
# ---------------------------------------------------------

agent_request(
    state="research",
    tool="search_customer",
    arguments={
        "customer_id": "123"
    }
)


# ---------------------------------------------------------
# TEST 2
# Agent tries dangerous tool during research
# ---------------------------------------------------------

agent_request(
    state="research",
    tool="delete_customer",
    arguments={
        "customer_id": "123"
    }
)


# ---------------------------------------------------------
# TEST 3
# Agent attempts excessive refund
# ---------------------------------------------------------

agent_request(
    state="execution",
    tool="issue_refund",
    arguments={
        "invoice_id": "INV-001",
        "amount": 5000
    }
)


# ---------------------------------------------------------
# TEST 4
# Legitimate refund
# ---------------------------------------------------------

agent_request(
    state="execution",
    tool="issue_refund",
    arguments={
        "invoice_id": "INV-001",
        "amount": 100
    }
)


# =========================================================
# AUDIT LOG
# =========================================================

print("\n" + "=" * 60)

print("                    AUDIT LOG")

print("=" * 60)

for event in guard.audit_log.get_events():

    print(
        f"{event['decision']:7} | "
        f"{event['state']:10} | "
        f"{event['tool']:20} | "
        f"{event['reason']}"
    )

print("\nDemo complete.")