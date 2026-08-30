from agentguard import AgentGuard


# ============================================================
# REAL TOOL FUNCTIONS
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


def delete_customer(customer_id):
    print(
        f"    [REAL TOOL] delete_customer("
        f"customer_id='{customer_id}')"
    )

    return {
        "customer_id": customer_id,
        "status": "customer_deleted",
    }


# ============================================================
# AGENTGUARD POLICY
# ============================================================

policies = {

    "discovery": {
        "allowed_tools": [
            "get_invoice",
        ],
    },

    "execution": {
        "allowed_tools": [
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

        },

    },

}


# ============================================================
# AGENTGUARD
# ============================================================

guard = AgentGuard(policies)


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = {

    "get_invoice": get_invoice,

    "issue_refund": issue_refund,

    "delete_customer": delete_customer,

}


# ============================================================
# AGENT
# ============================================================

class DemoAgent:

    def __init__(self, guard, tools):

        self.guard = guard
        self.tools = tools

        self.state = "discovery"

        self.context = {}

        self.denied_actions = []

    # ========================================================
    # TOOL REQUEST
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
        print(
            "Evaluating authorization..."
        )

        result = self.guard.call(

            state=self.state,

            tool=tool,

            function=self.tools[tool],

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
                f"Tool result: {result['result']}"
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

            self.denied_actions.append({

                "tool": tool,

                "arguments": arguments,

                "reason": result["reason"],

            })

        return result

    # ========================================================
    # SIMULATED AGENT REASONING
    #
    # This is deliberately isolated so that we can replace
    # it with a real LLM without changing AgentGuard.
    # ========================================================

    def decide_next_action(self):

        # ----------------------------------------------------
        # DISCOVERY
        # ----------------------------------------------------

        if self.state == "discovery":

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

                amount = invoice["amount"]

                # --------------------------------------------
                # If refund was already denied, the agent
                # receives that information and changes plan.
                # --------------------------------------------

                refund_denied = any(

                    denial["tool"] == "issue_refund"

                    for denial in self.denied_actions

                )

                if refund_denied:

                    print("\n[AGENT]")

                    print(
                        "The refund action was denied."
                    )

                    print(
                        "I will not retry the blocked action."
                    )

                    print(
                        "I will instead inspect the customer "
                        "record."
                    )

                    return {

                        "tool": "delete_customer",

                        "arguments": {
                            "customer_id": "12345"
                        }

                    }

                # --------------------------------------------
                # First execution attempt
                # --------------------------------------------

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

                        "invoice_id":
                            invoice["invoice_id"],

                        "amount":
                            amount,

                    }

                }

        return None

    # ========================================================
    # RUN
    # ========================================================

    def run(self, task):

        print("\n" + "=" * 70)

        print(
            "                    AGENTGUARD"
        )

        print(
            "              Agent Execution Demo"
        )

        print("=" * 70)

        print("\nUSER TASK")

        print("-" * 70)

        print(task)

        print("\nRunning agent...")

        # ----------------------------------------------------
        # DISCOVERY
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
        # EXECUTION
        # ----------------------------------------------------

        self.state = "execution"

        action = self.decide_next_action()

        result = self.request_tool(

            action["tool"],

            action["arguments"]

        )

        # ----------------------------------------------------
        # AGENT RECEIVES DENIAL
        # ----------------------------------------------------

        if not result["allowed"]:

            print("\n[AGENT]")

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

            # -----------------------------------------------
            # Ask the agent for its next action.
            # -----------------------------------------------

            action = self.decide_next_action()

            if action:

                self.request_tool(

                    action["tool"],

                    action["arguments"]

                )

        # ----------------------------------------------------
        # AUDIT LOG
        # ----------------------------------------------------

        print("\n" + "=" * 70)

        print(
            "                    AUDIT LOG"
        )

        print("=" * 70)

        for event in self.guard.audit_log.get_events():

            print()

            print(

                f"{event['decision']} | "
                f"state={event['state']} | "
                f"tool={event['tool']}"

            )

            print(

                f"  {event['reason']}"

            )

        print("\n" + "=" * 70)

        print(
            "                    DEMO COMPLETE"
        )

        print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    agent = DemoAgent(

        guard=guard,

        tools=TOOLS,

    )

    agent.run(

        "Customer 12345 wants a refund for "
        "invoice INV-001."

    )