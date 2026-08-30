from agentguard import AgentGuard


# ============================================================
# TOOLS
# ============================================================

def search_customer(customer_id):
    print(f"    [TOOL EXECUTED] search_customer({customer_id})")

    return {
        "customer_id": customer_id,
        "name": "John Smith",
        "status": "active",
    }


def get_invoice(invoice_id):
    print(f"    [TOOL EXECUTED] get_invoice({invoice_id})")

    return {
        "invoice_id": invoice_id,
        "amount": 600,
        "status": "eligible_for_refund",
    }


def issue_refund(invoice_id, amount):
    print(
        f"    [TOOL EXECUTED] "
        f"issue_refund(invoice_id={invoice_id}, amount=${amount})"
    )

    return {
        "invoice_id": invoice_id,
        "refunded": amount,
        "status": "refund_processed",
    }


def delete_customer(customer_id):
    print(
        f"    [TOOL EXECUTED] "
        f"delete_customer(customer_id={customer_id})"
    )

    return {
        "customer_id": customer_id,
        "status": "customer_deleted",
    }


TOOLS = {
    "search_customer": search_customer,
    "get_invoice": get_invoice,
    "issue_refund": issue_refund,
    "delete_customer": delete_customer,
}


# ============================================================
# AGENTGUARD POLICY
# ============================================================

POLICIES = {

    "discovery": {
        "allowed_tools": [
            "search_customer",
            "get_invoice",
        ]
    },

    "validation": {
        "allowed_tools": [
            "search_customer",
            "get_invoice",
        ]
    },

    "execution": {
        "allowed_tools": [
            "search_customer",
            "get_invoice",
            "issue_refund",
        ],

        "argument_rules": {

            "issue_refund": {

                "amount": {
                    "min": 1,
                    "max": 500,
                }

            }

        }

    }

}


guard = AgentGuard(POLICIES)


# ============================================================
# SIMPLE AUTONOMOUS AGENT
# ============================================================

class DemoAgent:

    def __init__(self, guard):

        self.guard = guard

        self.state = "discovery"

        self.context = {}

    def run(self, task):

        print("\n" + "=" * 70)
        print("                    AGENTGUARD")
        print("              Autonomous Agent Demo")
        print("=" * 70)

        print("\nUSER TASK")
        print("-" * 70)
        print(task)

        # ----------------------------------------------------
        # STEP 1 — DISCOVER
        # ----------------------------------------------------

        self.state = "discovery"

        self.request_tool(
            "get_invoice",
            {
                "invoice_id": "INV-001"
            }
        )

        # ----------------------------------------------------
        # STEP 2 — EXECUTION
        # ----------------------------------------------------

        self.state = "execution"

        refund_result = self.request_tool(
            "issue_refund",
            {
                "invoice_id": "INV-001",
                "amount": 600
            }
        )

        # ----------------------------------------------------
        # STEP 3 — REACT TO DENIAL
        # ----------------------------------------------------

        if refund_result["allowed"] is False:

            print("\n[AGENT]")
            print(
                "AgentGuard denied the refund."
            )

            print(
                "Agent adapts its plan instead of executing "
                "the blocked action."
            )

        # ----------------------------------------------------
        # STEP 4 — MALICIOUS / UNAUTHORISED ACTION
        # ----------------------------------------------------

        print("\n[AGENT]")
        print(
            "Agent attempts another action:"
        )

        self.request_tool(
            "delete_customer",
            {
                "customer_id": "12345"
            }
        )

        # ----------------------------------------------------
        # FINISHED
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("                    AUDIT LOG")
        print("=" * 70)

        for event in self.guard.audit_log.get_events():

            print(
                f"\n{event['decision']}"
                f" | state={event['state']}"
                f" | tool={event['tool']}"
            )

            print(
                f"  {event['reason']}"
            )

        print("\n" + "=" * 70)
        print("                    DEMO COMPLETE")
        print("=" * 70)

    # ========================================================
    # AGENT → AGENTGUARD → TOOL
    # ========================================================

    def request_tool(self, tool, arguments):

        print("\n" + "-" * 70)

        print("[AGENT]")
        print(
            f"Proposed action: {tool}"
        )

        print(
            f"Arguments: {arguments}"
        )

        print("\n[AGENTGUARD]")
        print("Evaluating authorization...")

        result = self.guard.call(
            state=self.state,
            tool=tool,
            function=TOOLS[tool],
            arguments=arguments,
        )

        if result["allowed"]:

            print("\n🟢 ALLOWED")

            print(
                "AgentGuard authorized the action."
            )

            print(
                "Tool executed: YES"
            )

            print(
                f"Tool result: {result.get('result')}"
            )

        else:

            print("\n🔴 DENIED")

            print(
                "AgentGuard blocked the action."
            )

            print(
                "Tool executed: NO"
            )

            print(
                f"Reason: {result['reason']}"
            )

        return result


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    agent = DemoAgent(guard)

    agent.run(
        "Customer 12345 wants a refund for invoice INV-001. "
        "Check the invoice and process the refund if appropriate."
    )