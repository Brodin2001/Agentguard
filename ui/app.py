import streamlit as st

from agentguard import AgentGuard


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AgentGuard Playground",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# DEMO TOOLS
# ============================================================

def search_customer(customer_id):
    return {
        "customer_id": customer_id,
        "name": "John Smith",
        "status": "active",
    }


def get_invoice(invoice_id):
    return {
        "invoice_id": invoice_id,
        "amount": 250,
        "status": "eligible_for_refund",
    }


def issue_refund(invoice_id, amount):
    return {
        "invoice_id": invoice_id,
        "refunded": amount,
        "status": "refund_processed",
    }


def delete_customer(customer_id):
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
# POLICIES
# ============================================================

POLICIES = {
    "discovery": {
        "allowed_tools": [
            "search_customer",
            "get_invoice",
        ],
    },

    "validation": {
        "allowed_tools": [
            "search_customer",
            "get_invoice",
        ],
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
                    "min": 0,
                    "max": 500,
                },
            },
        },
    },
}


# ============================================================
# AGENTGUARD
# ============================================================

if "guard" not in st.session_state:
    st.session_state.guard = AgentGuard(POLICIES)

guard = st.session_state.guard


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ AgentGuard Playground")

st.subheader(
    "Runtime authorization for AI-agent tool calls"
)

st.write(
    "The model proposes an action. "
    "AgentGuard decides whether it is authorized. "
    "The tool only executes if permission is granted."
)

st.divider()


# ============================================================
# SIDEBAR — AGENT WORKFLOW
# ============================================================

st.sidebar.title("🤖 Agent Workflow")

state = st.sidebar.selectbox(
    "Current agent state",
    list(POLICIES.keys()),
)

st.sidebar.divider()

st.sidebar.subheader("Allowed tools")

allowed_tools = POLICIES[state]["allowed_tools"]

for tool_name in allowed_tools:
    st.sidebar.success(tool_name)

st.sidebar.subheader("Blocked tools")

for tool_name in TOOLS:
    if tool_name not in allowed_tools:
        st.sidebar.error(tool_name)


# ============================================================
# MAIN LAYOUT
# ============================================================

left, right = st.columns(2)


# ============================================================
# AGENT REQUEST
# ============================================================

with left:

    st.header("🤖 Agent Tool Request")

    st.write(
        f"Current state: **{state}**"
    )

    tool = st.selectbox(
        "Tool requested by agent",
        list(TOOLS.keys()),
    )

    arguments = {}

    if tool == "search_customer":

        customer_id = st.text_input(
            "Customer ID",
            value="123",
        )

        arguments = {
            "customer_id": customer_id
        }

    elif tool == "get_invoice":

        invoice_id = st.text_input(
            "Invoice ID",
            value="INV-001",
        )

        arguments = {
            "invoice_id": invoice_id
        }

    elif tool == "issue_refund":

        invoice_id = st.text_input(
            "Invoice ID",
            value="INV-001",
        )

        amount = st.number_input(
            "Refund amount ($)",
            min_value=0.0,
            value=100.0,
            step=50.0,
        )

        arguments = {
            "invoice_id": invoice_id,
            "amount": amount,
        }

    elif tool == "delete_customer":

        customer_id = st.text_input(
            "Customer ID",
            value="123",
        )

        arguments = {
            "customer_id": customer_id
        }

    st.subheader("Request Preview")

    st.code(
        f"State: {state}\n"
        f"Tool: {tool}\n"
        f"Arguments: {arguments}",
        language="python",
    )


# ============================================================
# AGENTGUARD DECISION
# ============================================================

with right:

    st.header("🛡️ AgentGuard")

    st.write(
        "AgentGuard sits between the agent and the tool."
    )

    st.divider()

    if st.button(
        "▶ Execute Tool Request",
        type="primary",
        width="stretch",
    ):

        result = guard.call(
            state=state,
            tool=tool,
            function=TOOLS[tool],
            arguments=arguments,
        )

        st.subheader("Decision")

        if result["allowed"]:

            st.success("🟢 ALLOWED")

            st.write(
                f"**Tool:** `{tool}`"
            )

            st.write(
                f"**State:** `{state}`"
            )

            st.write(
                "**Tool executed:** YES"
            )

            st.divider()

            if result.get("executed"):

                st.success(
                    "✓ Python function executed successfully."
                )

                st.subheader("Tool Result")

                st.json(
                    result.get("result")
                )

        else:

            st.error("🔴 DENIED")

            st.write(
                f"**Tool:** `{tool}`"
            )

            st.write(
                f"**State:** `{state}`"
            )

            st.write(
                "**Tool executed:** NO"
            )

            st.divider()

            st.write("**Reason:**")

            st.warning(
                result["reason"]
            )

            st.info(
                "AgentGuard prevented the tool from executing."
            )


# ============================================================
# AUDIT LOG
# ============================================================

st.divider()

st.header("📋 Audit Log")

events = guard.audit_log.get_events()

if events:

    st.dataframe(
        events,
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "No tool requests have been attempted yet."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AgentGuard v0.1 — The model proposes. "
    "AgentGuard authorizes. "
    "The tool executes only when permitted."
)