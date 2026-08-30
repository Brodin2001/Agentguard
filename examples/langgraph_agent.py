from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from agentguard import AgentGuard


class AgentState(TypedDict):
    state: str
    tool: str
    amount: int
    result: str


def refund_customer(amount: int) -> str:
    return f"Refunded ${amount}"


guard = AgentGuard(
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

app = graph.compile()


print("\n--- AgentGuard + LangGraph Demo ---\n")

print("Test 1: Safe refund")
result = app.invoke({
    "state": "normal",
    "tool": "refund_customer",
    "amount": 50,
    "result": ""
})

print(result["result"])


print("\nTest 2: Excessive refund")
result = app.invoke({
    "state": "normal",
    "tool": "refund_customer",
    "amount": 500,
    "result": ""
})

print(result["result"])


print("\nAudit log:")
for event in guard.audit_log.get_events():
    print(event)