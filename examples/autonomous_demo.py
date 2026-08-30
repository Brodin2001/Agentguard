from agentguard import AgentGuard


# ============================================================
# TOOLS
# ============================================================

def search_customer(customer_id):
    print(f"    [REAL TOOL] search_customer(customer_id={customer_id})")

    return {
        "customer_id": customer_id,
        "name": "John Smith",
        "status": "active",
    }


def get_invoice(invoice_id):
    print(f"    [REAL TOOL] get_invoice(invoice_id={invoice_id})")

    return {
        "invoice_id": invoice_id,
        "amount": 600,
        "status": "eligible_for_refund",
    }


def issue_refund(invoice_id, amount):
    print(
        f"    [REAL TOOL] "
        f"issue_refund(invoice_id={invoice_id}, amount=${amount})"
    )

    return {
        "invoice_id": invoice_id,
        "refunded": amount,
        "status": "refund_processed",
    }


def delete_customer(customer_id):
    print(
        f"    [REAL TOOL] "
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


# ============================================================
# AGENTGUARD
# ============================================================

guard = AgentGuard(POLICIES)


# ============================================================
# AUTONOMOUS DEMO AGENT
# ============================================================

class DemoAgent:

    def __init__(self, guard):

        self.guard = guard
        self.state = "discovery"
        self.context = {}
        self.denied_actions = []
        self.action_count = 0

    # ========================================================
    # MAIN AGENT LOOP
    # ========================================================

    def run(self, task):

        print("\n" + "=" * 70)
        print("                    AGENTGUARD")
        print("              Autonomous Agent Demo")
        print("=" * 70)

        print("\nUSER TASK")
        print("-" * 70)
        print(task)

        print("\nRunning agent...")

        # ----------------------------------------------------
        # ACTION 1 — DISCOVERY
        # ----------------------------------------------------

        self.state = "discovery"

        action = self.decide_next_action()

        result = self.request_tool(
            action["tool"],
            action["arguments"]
        )

        if result["allowed"]:
            self.context["invoice"] = result["result"]

        # ----------------------------------------------------
        # ACTION 2 — EXECUTION
        # ----------------------------------------------------

        self.state = "execution"

        action = self.decide_next_action()

        result = self.request_tool(
            action["tool"],
            action["arguments"]
        )

        # ----------------------------------------------------
        # ACTION 3 — ADAPT AFTER DENIAL
        # ----------------------------------------------------

        if not result["allowed"]:

            print("\n[AGENT]")
            print("AgentGuard rejected the proposed action.")

            print(
                "The agent received the authorization result "
                "and changed its plan."
            )

            action = self.decide_next_action()

            self.request_tool(
                action["tool"],
                action["arguments"]
            )

        # ----------------------------------------------------
        # AUDIT LOG
        # ----------------------------------------------------

        self.print_audit_log()

    # ========================================================
    # AGENT DECISION MAKER
    # ========================================================

    def decide_next_action(self):

        # ----------------------------------------------------
        # DISCOVERY
        # ----------------------------------------------------

        if self.state == "discovery":

            if "invoice" not in self.context:

                print("\n[AGENT]")
                print(
                    "I need to inspect the invoice before "
                    "deciding what to do."
                )

                return {
                    "tool": "get_invoice",
                    "arguments": {
                        "invoice_id": "INV-001"
                    }
                }

        # ----------------------------------------------------
        # EXECUTION
        # ----------------------------------------------------

        if self.state == "execution":

            invoice = self.context.get("invoice")

            if invoice:

                # --------------------------------------------
                # IMPORTANT:
                # If the refund has already been denied,
                # the agent MUST NOT retry the same action.
                # --------------------------------------------

                refund_was_denied = any(
                    denied["tool"] == "issue_refund"
                    for denied in self.denied_actions
                )

                if refund_was_denied:

                    print("\n[AGENT]")
                    print(
                        "The refund request was denied."
                    )

                    print(
                        "I will not retry the same blocked action."
                    )

                    print(
                        "I will instead look up the customer "
                        "record."
                    )

                    return {
                        "tool": "search_customer",
                        "arguments": {
                            "customer_id": "12345"
                        }
                    }

                # --------------------------------------------
                # First refund attempt
                # --------------------------------------------

                amount = invoice["amount"]

                print("\n[AGENT]")
                print(
                    f"The invoice is eligible for a "
                    f"${amount} refund."
                )

                print(
                    "I will propose issuing the refund."
                )

                return {
                    "tool": "issue_refund",
                    "arguments": {
                        "invoice_id": invoice["invoice_id"],
                        "amount": amount
                    }
                }

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        print("\n[AGENT]")
        print(
            "I will attempt another action."
        )

        return {
            "tool": "delete_customer",
            "arguments": {
                "customer_id": "12345"
            }
        }

    # ========================================================
    # AGENT → AGENTGUARD → TOOL
    # ========================================================

    def request_tool(self, tool, arguments):

        self.action_count += 1

        print("\n" + "-" * 70)

        print(
            f"ACTION {self.action_count}"
        )

        print("\n[AGENT]")

        print(
            f"Proposed action: {tool}"
        )

        print(
            f"Arguments: {arguments}"
        )

        print("\n[AGENTGUARD]")
        print(
            "Evaluating authorization..."
        )

        result = self.guard.call(
            state=self.state,
            tool=tool,
            function=TOOLS[tool],
            arguments=arguments,
        )

        # ----------------------------------------------------
        # ALLOWED
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DENIED
        # ----------------------------------------------------

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

            # -----------------------------------------------
            # Pass denial information back to the agent.
            # -----------------------------------------------

            self.denied_actions.append({
                "tool": tool,
                "reason": result["reason"],
            })

        return result

    # ========================================================
    # AUDIT LOG
    # ========================================================

    def print_audit_log(self):

        print("\n" + "=" * 70)
        print("                    AUDIT LOG")
        print("=" * 70)

        events = self.guard.audit_log.get_events()

        for event in events:

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


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    agent = DemoAgent(guard)

    agent.run(
        "Customer 12345 wants a refund for invoice INV-001. "
        "Check the invoice and process the refund if appropriate."
    )