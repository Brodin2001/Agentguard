from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agentguard import AgentGuard


class AgentState(TypedDict):
    state: str
    tool: str
    amount: int
    result: str


def refund_customer(amount: int) -> str:
    return f"Refunded ${amount}"


def build_graph(guard):
    def execute_tool(state: AgentState):
        decision = guard.call(
            state=state["state"],
            tool=state["tool"],
            function=refund_customer,
            arguments={
                "amount": state["amount"]
            }
        )

        if decision["allowed"]:
            return {
                "result": decision["result"]
            }

        return {
            "result": f"BLOCKED: {decision['reason']}"
        }

    graph = StateGraph(AgentState)

    graph.add_node("execute_tool", execute_tool)

    graph.add_edge(START, "execute_tool")
    graph.add_edge("execute_tool", END)

    return graph.compile()


def create_guard():
    return AgentGuard(
        policies={
            "normal": {
                "allowed_tools": ["refund_customer"],
                "argument_rules": {
                    "refund_customer": {
                        "amount": {
                            "max": 100
                        }
                    }
                }
            }
        }
    )


def test_langgraph_allows_valid_tool_call():
    guard = create_guard()
    app = build_graph(guard)

    result = app.invoke({
        "state": "normal",
        "tool": "refund_customer",
        "amount": 50,
        "result": ""
    })

    assert result["result"] == "Refunded $50"

    events = guard.audit_log.get_events()

    assert events[-1]["decision"] == "ALLOWED"


def test_langgraph_blocks_invalid_tool_call():
    guard = create_guard()
    app = build_graph(guard)

    result = app.invoke({
        "state": "normal",
        "tool": "refund_customer",
        "amount": 500,
        "result": ""
    })

    assert result["result"].startswith("BLOCKED:")

    events = guard.audit_log.get_events()

    assert events[-1]["decision"] == "DENIED"