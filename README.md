# AgentGuard

AgentGuard is a lightweight runtime authorization layer for AI agent tool calls.

Its core model is **action-bound authorization**: for consequential actions, authorization can be bound to the exact tool, arguments, target, agent identity, runtime identity, executable capability, and current policy state immediately before execution.

> **Early-adopter MVP. Not a production security system or a guarantee against arbitrary code with equivalent process privileges.**

## Install

```bash
git clone https://github.com/Brodin2001/Agentguard.git
cd Agentguard
python -m pip install -e .
```

The core package has no mandatory framework dependencies.

Optional integrations:

```bash
python -m pip install -e ".[langchain]"
python -m pip install -e ".[langgraph]"
```

## Basic authorization

```python
from agentguard import AgentGuard


def send_email(to, subject):
    return f"Email sent to {to}: {subject}"


guard = AgentGuard({
    "support": {
        "allowed_tools": ["send_email"]
    }
})

result = guard.call(
    state="support",
    tool="send_email",
    function=send_email,
    arguments={
        "to": "customer@example.com",
        "subject": "Your request is complete",
    },
)
```

## Action-bound authorization

For consequential actions, bind the executable capability first, issue a short-lived receipt for the exact candidate action, then execute the receipt immediately before the side effect:

```python
from agentguard import AgentGuard


def refund(customer_id, amount):
    return f"Refunded ${amount}"


guard = AgentGuard({
    "execution": {
        "allowed_tools": ["refund"],
        "argument_rules": {
            "refund": {
                "amount": {"min": 1, "max": 500}
            }
        },
    }
})

guard.bind_tool("refund", refund)

arguments = {"customer_id": "customer-123", "amount": 100}

receipt = guard.issue_receipt(
    state="execution",
    tool="refund",
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
    ttl_seconds=30,
)

result = guard.execute_receipt(
    receipt,
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)
```

The receipt is bound to the executable capability and exact authorized action. Execution fails closed if there is a mismatch in:

- arguments
- target
- agent identity
- runtime identity
- executable capability
- policy state
- receipt integrity
- expiry
- replay

The receipt MAC is intended to make the receipt tamper-evident within the AgentGuard process. It does not prevent arbitrary Python code with equivalent process privileges from bypassing the library entirely.

## Policies

Authorize tools by agent state:

```python
policies = {
    "support": {
        "allowed_tools": ["send_email"]
    }
}
```

Constrain numeric arguments with `min` and `max`:

```python
policies = {
    "payments": {
        "allowed_tools": ["refund"],
        "argument_rules": {
            "refund": {
                "amount": {
                    "min": 1,
                    "max": 500,
                }
            }
        },
    }
}
```

Unknown states fail closed. A denied request returns `allowed=False` and `executed=False`, and the underlying function is not called.

## Integrations

AgentGuard includes examples and tests for:

- Plain Python tools
- LangChain
- LangGraph

LangChain:

```bash
python examples/langchain_agent.py
```

LangGraph:

```bash
python examples/langgraph_agent.py
```

The integrations keep enforcement at the tool-execution boundary rather than replacing the agent framework.

## Audit log

Authorization decisions are recorded in an in-memory audit log:

```python
for event in guard.audit_log.get_events():
    print(event)
```

## Testing

```bash
python -m pip install -e ".[tests]"
pytest -q
```

The test suite includes receipt attacks covering argument mutation, target mutation, identity changes, replay, expiry, policy changes, receipt tampering, and executable-capability substitution.

## Early-adopter testing

AgentGuard is currently being validated with developers building real tool-using AI agents.

The highest-value test is not a demo tool. It is one consequential action in an existing workflow — for example an MCP write, database mutation, calendar/email action, repository change, deployment, or other side effect.

The question we are testing is:

> **The agent got approval. Did the exact action that was authorized actually become the action that executed?**

If you have a consequential agent execution path, the most useful feedback is to connect one real path, deliberately attempt to mutate the authorized action, and report whether AgentGuard blocks the mismatch.

## Important limitation

AgentGuard protects execution paths that are explicitly routed through `guard.call()` or `guard.execute_receipt()` (or an integration providing equivalent enforcement). Direct calls to the underlying Python function bypass AgentGuard.

This project is an early-adopter validation MVP. The goal is evidence from real workflows, real integrations, real bypass attempts, continued use, and ultimately willingness to pay.
