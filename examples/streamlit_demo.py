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

def get_invoice(invoice_id):
    return {
        "invoice_id": invoice_id,
        "amount": 600,
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


# ============================================================
# AGENTGUARD POLICY
# ============================================================

POLICIES = {
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
                },
            },
        },
    },
}


TOOLS = {
    "get_invoice": get_invoice,
    "issue_refund": issue_refund,
    "delete_customer": delete_customer,
}


# ============================================================
# SESSION STATE
# ============================================================

if "guard" not in st.session_state:
    st.session_state.guard = AgentGuard(POLICIES)

if "events" not in st.session_state:
    st.session_state.events = []

if "running" not in st.session_state:
    st.session_state.running = False

guard = st.session_state.guard


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .subtitle {
        font-size: 18px;
        color: #777;
        margin-bottom: 25px;
    }

    .step {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #ddd;
        background: #fafafa;
        margin-bottom: 12px;
    }

    .agent {
        border-left: 5px solid #777;
    }

    .guard {
        border-left: 5px solid #444;
    }

    .allowed {
        border-left: 5px solid #2e7d32;
        background: #f1f8f2;
    }

    .denied {
        border-left: 5px solid #c62828;
        background: #fff4f4;
    }

    .tool {
        border-left: 5px solid #1565c0;
        background: #f3f7fc;
    }

    .status {
        font-size: 24px;
        font-weight: 700;
    }

    .small {
        color: #777;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🛡️ AgentGuard Playground</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Runtime authorization for AI-agent tool calls'
    '</div>',
    unsafe_allow_html=True,
)

st.write(
    "Watch an autonomous agent plan and execute a task while "
    "AgentGuard controls which tools it is actually allowed to use."
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Demo Scenario")

scenario = st.sidebar.selectbox(
    "Choose scenario",
    [
        "Unsafe refund",
        "Safe refund",
    ],
)

st.sidebar.divider()

st.sidebar.subheader("AgentGuard policy")

st.sidebar.write(
    "AgentGuard evaluates every tool request before execution."
)

st.sidebar.markdown(
    """
    **Discovery**
    
    ✓ `get_invoice`

    **Execution**

    ✓ `get_invoice`  
    ✓ `issue_refund`  
    ✕ `delete_customer`

    **Refund limit**

    Maximum: **$500**
    """
)

if st.sidebar.button("Reset Demo"):
    st.session_state.guard = AgentGuard(POLICIES)
    st.session_state.events = []
    st.session_state.running = False
    st.rerun()


# ============================================================
# SCENARIO DESCRIPTION
# ============================================================

if scenario == "Unsafe refund":

    customer_id = "12345"
    invoice_id = "INV-001"
    invoice_amount = 600

    task = (
        "Customer 12345 wants a refund for invoice INV-001. "
        "Check the invoice and process the refund if appropriate."
    )

else:

    customer_id = "12345"
    invoice_id = "INV-002"
    invoice_amount = 100

    task = (
        "Customer 12345 wants a refund for invoice INV-002. "
        "Check the invoice and process the refund if appropriate."
    )


# ============================================================
# USER TASK
# ============================================================

st.header("🎯 User Task")

st.info(task)


# ============================================================
# RUN AGENT
# ============================================================

if st.button(
    "▶ Run Autonomous Agent",
    type="primary",
    use_container_width=True,
):

    # Reset previous run
    st.session_state.guard = AgentGuard(POLICIES)
    st.session_state.events = []

    guard = st.session_state.guard

    st.session_state.running = True

    # --------------------------------------------------------
    # ACTION 1 — GET INVOICE
    # --------------------------------------------------------

    action_1 = {
        "agent": "Agent",
        "state": "discovery",
        "tool": "get_invoice",
        "arguments": {
            "invoice_id": invoice_id,
        },
    }

    result_1 = guard.call(
        state="discovery",
        tool="get_invoice",
        function=get_invoice,
        arguments={
            "invoice_id": invoice_id,
        },
    )

    st.session_state.events.append(
        {
            "action": action_1,
            "result": result_1,
        }
    )

    # --------------------------------------------------------
    # ACTION 2 — REFUND
    # --------------------------------------------------------

    action_2 = {
        "agent": "Agent",
        "state": "execution",
        "tool": "issue_refund",
        "arguments": {
            "invoice_id": invoice_id,
            "amount": invoice_amount,
        },
    }

    result_2 = guard.call(
        state="execution",
        tool="issue_refund",
        function=issue_refund,
        arguments={
            "invoice_id": invoice_id,
            "amount": invoice_amount,
        },
    )

    st.session_state.events.append(
        {
            "action": action_2,
            "result": result_2,
        }
    )

    # --------------------------------------------------------
    # ACTION 3 — UNSAFE FALLBACK
    # --------------------------------------------------------

    action_3 = {
        "agent": "Agent",
        "state": "execution",
        "tool": "delete_customer",
        "arguments": {
            "customer_id": customer_id,
        },
    }

    result_3 = guard.call(
        state="execution",
        tool="delete_customer",
        function=delete_customer,
        arguments={
            "customer_id": customer_id,
        },
    )

    st.session_state.events.append(
        {
            "action": action_3,
            "result": result_3,
        }
    )

    st.session_state.running = False

    st.rerun()


# ============================================================
# AUTONOMOUS EXECUTION TIMELINE
# ============================================================

if st.session_state.events:

    st.divider()

    st.header("🤖 Autonomous Agent Execution")

    for index, event in enumerate(
        st.session_state.events,
        start=1,
    ):

        action = event["action"]
        result = event["result"]

        tool = action["tool"]
        state = action["state"]
        arguments = action["arguments"]

        # ----------------------------------------------------
        # AGENT
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="step agent">

            <b>🤖 AGENT — Action {index}</b>

            <br><br>

            Agent proposes:

            <br>

            <code>{tool}</code>

            <br><br>

            State: <code>{state}</code>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.code(
            f"{tool}({arguments})",
            language="python",
        )

        # ----------------------------------------------------
        # AGENTGUARD
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="step guard">

            <b>🛡️ AGENTGUARD</b>

            <br><br>

            Evaluating authorization...

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # DECISION
        # ----------------------------------------------------

        if result["allowed"]:

            st.markdown(
                f"""
                <div class="step allowed">

                <div class="status">🟢 ALLOWED</div>

                <br>

                <b>Tool:</b> <code>{tool}</code>

                <br>

                <b>State:</b> <code>{state}</code>

                <br>

                <b>Tool executed:</b> YES

                <br><br>

                AgentGuard authorized the action.

                </div>
                """,
                unsafe_allow_html=True,
            )

            if result.get("result") is not None:

                st.markdown(
                    '<div class="step tool">'
                    '<b>🔧 TOOL EXECUTED</b>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.json(result["result"])

        else:

            st.markdown(
                f"""
                <div class="step denied">

                <div class="status">🔴 DENIED</div>

                <br>

                <b>Tool:</b> <code>{tool}</code>

                <br>

                <b>State:</b> <code>{state}</code>

                <br>

                <b>Tool executed:</b> NO

                <br><br>

                <b>Reason:</b>

                <br>

                {result["reason"]}

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.warning(
                "🚫 AgentGuard stopped the tool call before "
                "the underlying function could execute."
            )

        # ----------------------------------------------------
        # ADAPTATION
        # ----------------------------------------------------

        if (
            not result["allowed"]
            and tool == "issue_refund"
        ):

            st.markdown(
                """
                <div class="step agent">

                <b>🤖 AGENT ADAPTS</b>

                <br><br>

                AgentGuard denied the refund.

                <br><br>

                The agent receives the denial and can
                reconsider its plan rather than executing
                the blocked action.

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# AUDIT LOG
# ============================================================

st.divider()

st.header("📋 Audit Log")

events = guard.audit_log.get_events()

if events:

    for event in reversed(events):

        decision = event["decision"]

        if decision == "ALLOWED":
            icon = "🟢"
        elif decision == "DENIED":
            icon = "🔴"
        else:
            icon = "🟡"

        st.markdown(
            f"""
            <div class="step">

            {icon} <b>{decision}</b>

            &nbsp;&nbsp;

            State: <code>{event["state"]}</code>

            &nbsp;&nbsp;

            Tool: <code>{event["tool"]}</code>

            <br><br>

            {event["reason"]}

            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.info(
        "No tool calls have been attempted yet."
    )


# ============================================================
# DEVELOPER INTEGRATION
# ============================================================

st.divider()

st.header("👨‍💻 What the Developer Gets")

st.write(
    "The developer does not need to rebuild their agent. "
    "AgentGuard is placed at the tool execution boundary."
)

st.code(
    '''from agentguard import AgentGuard

guard = AgentGuard(policies)

result = guard.call(
    state=agent_state,
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "invoice_id": invoice_id,
        "amount": amount,
    },
)''',
    language="python",
)

st.caption(
    "The model proposes. AgentGuard authorizes. "
    "The tool executes only when permitted."
)

st.caption("AgentGuard v0.1")