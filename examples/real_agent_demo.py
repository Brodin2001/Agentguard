from agentguard import AgentGuard


# ============================================================
# REAL TOOLS
# ============================================================

def get_invoice(invoice_id):
    print(f"    [REAL TOOL] get_invoice('{invoice_id}')")

    return {
        "invoice_id": invoice_id,
        "amount": 600,
        "status": "eligible_for_refund",
    }


def issue_refund(invoice_id, amount):
    print(
        f"    [REAL TOOL] issue_refund("
        f"invoice_id='{invoice_id}', amount=${amount})"
    )

    return {
        "invoice_id": invoice_id,
        "refunded": amount,
        "status": "refund_processed",
    }


def search_customer(customer_id):
    print(
        f"    [REAL TOOL] search_customer("
        f"customer_id='{customer_id}')"
    )

    return {
        "customer_id": customer_id,
        "name": "John Smith",
        "status": "active",
    }


def delete_customer(customer_id):
    print(
        f"    [REAL TOOL] delete_customer("
        f"customer_id='{customer_id}')"
    )

    return {
        "customer_id": customer_id,
        "status": "customer_deleted",
    }


TOOLS = {
    "get_invoice": get_invoice,
    "issue_refund": issue_refund,
    "search_customer": search_customer,
    "delete_customer": delete_customer,
}


# ============================================================
# AGENTGUARD POLICY
# ============================================================

POLICIES = {

    "discovery": {
        "allowed_tools": [
            "get_invoice",
            "search_customer",
        ],
    },

    "execution": {
        "allowed_tools": [
            "get_invoice",
            "search_customer",
            "issue_refund",
        ],

        "argument_rules": {

            "issue_refund": {

                "amount": {
                    "min": 1,
                    "max": 500,
                }

            }

        },
    },
}


guard = AgentGuard(POLICIES)


# ============================================================
# AGENT
# ============================================================

class Agent:

    def __init__(self, guard, tools):

        self.guard = guard
        self.tools = tools

        self.state = "discovery"
        self.context = {}

    # --------------------------------------------------------
    # REQUEST TOOL
    # --------------------------------------------------------

    def request_tool(self, tool, arguments):

        print()
        print("-" * 70)

        print("[AGENT]")
        print(f"Proposed action: {tool}")
        print(f"Arguments: {arguments}")

        print()
        print("[AGENTGUARD]")
        print("Evaluating authorization...")

        result = self.guard.call(
            state=self.state,
            tool=tool,
            function=self.tools[tool],
            arguments=arguments,
        )

        if result["allowed"]:

            print()
            print("🟢 ALLOWED")
            print("AgentGuard authorized the action.")
            print("Tool executed: YES")
            print(
                f"Tool result: {result['result']}"
            )

        else:

            print()
            print("🔴 DENIED")
            print("AgentGuard blocked the action.")
            print("Tool executed: NO")
            print(
                f"Reason: {result['reason']}"
            )

        return result

    # --------------------------------------------------------
    # AGENT REASONING
    # --------------------------------------------------------

    def run(self, task):

        print()
        print("=" * 70)
        print("                    AGENTGUARD")
        print("              Agent Execution Demo")
        print("=" * 70)

        print()
        print("USER TASK")
        print("-" * 70)
        print(task)

        print()
        print("Running agent...")

        # ====================================================
        # AGENT DECIDES TO INSPECT INVOICE
        # ====================================================

        print()
        print("[AGENT]")
        print(
            "I need to inspect the invoice before deciding "
            "what action to take."
        )

        self.state = "discovery"

        invoice_result = self.request_tool(
            tool="get_invoice",
            arguments={
                "invoice_id": "INV-001",
            },
        )

        if not invoice_result["allowed"]:

            print()
            print(
                "[AGENT] Unable to inspect invoice."
            )

            return

        invoice = invoice_result["result"]

        self.context["invoice"] = invoice

        # ====================================================
        # AGENT DECIDES WHAT TO DO WITH RESULT
        # ====================================================

        print()
        print("[AGENT]")

        if invoice["status"] == "eligible_for_refund":

            print(
                f"The invoice is eligible for a "
                f"${invoice['amount']} refund."
            )

            print(
                "I will propose issuing the refund."
            )

        else:

            print(
                "The invoice is not eligible for a refund."
            )

            return

        # ====================================================
        # EXECUTION STATE
        # ====================================================

        self.state = "execution"

        refund_result = self.request_tool(
            tool="issue_refund",
            arguments={
                "invoice_id": invoice["invoice_id"],
                "amount": invoice["amount"],
            },
        )

        # ====================================================
        # AGENT RECEIVES DENIAL
        # ====================================================

        if not refund_result["allowed"]:

            print()
            print("[AGENT]")
            print(
                "AgentGuard rejected the proposed action."
            )

            print(
                "The authorization result has been "
                "returned to the agent."
            )

            print(
                "The agent changes its plan."
            )

            print()
            print(
                "[AGENT] I will not retry the same "
                "blocked action."
            )

            print(
                "[AGENT] I will instead inspect the "
                "customer record."
            )

            # =================================================
            # ALTERNATIVE ACTION
            # =================================================

            customer_result = self.request_tool(
                tool="search_customer",
                arguments={
                    "customer_id": "12345",
                },
            )

            if customer_result["allowed"]:

                print()
                print("[AGENT]")
                print(
                    "Customer record successfully retrieved."
                )

                self.context["customer"] = (
                    customer_result["result"]
                )

        # ====================================================
        # MALICIOUS / UNAUTHORIZED ACTION
        # ====================================================

        print()
        print("[AGENT]")
        print(
            "I will now test another available tool."
        )

        self.request_tool(
            tool="delete_customer",
            arguments={
                "customer_id": "12345",
            },
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    agent = Agent(
        guard=guard,
        tools=TOOLS,
    )

    agent.run(
        "Customer 12345 wants a refund for invoice INV-001. "
        "Check the invoice and process the refund if appropriate."
    )

    # ========================================================
    # AUDIT LOG
    # ========================================================

    print()
    print("=" * 70)
    print("                    AUDIT LOG")
    print("=" * 70)

    for event in guard.audit_log.get_events():

        print()
        print(
            f"{event['decision']} | "
            f"state={event['state']} | "
            f"tool={event['tool']}"
        )

        print(
            f"  {event['reason']}"
        )

    print()
    print("=" * 70)
    print("                    DEMO COMPLETE")
    print("=" * 70)