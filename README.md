# AgentGuard

AgentGuard is a lightweight runtime authorization layer between an AI agent and its Python tools.

It evaluates a requested tool call against an explicit policy before the underlying function runs. If the request is denied, the function is not called.

```text
Agent requests tool
        |
   AgentGuard
   /        \
ALLOW       DENY
  |           |
Tool runs  Tool blocked
```

> Early validation MVP. Not a production security system.

## Install

Clone the repository and install the package:

```bash
git clone https://github.com/Brodin2001/Agentguard.git
cd Agentguard
python -m pip install -e .
```

The core package has no mandatory framework dependencies.

For integrations:

```bash
python -m pip install -e ".[langchain]"
python -m pip install -e ".[langgraph]"
```

## Quickstart

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

print(result)
```

Run the included quickstart:

```bash
python examples/quickstart.py
```

It demonstrates an allowed call and denied calls for unauthorized tools and unsafe arguments.

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

AgentGuard currently includes examples and tests for:

- Plain Python tools
- LangChain
- LangGraph

LangChain example:

```bash
python examples/langchain_agent.py
```

LangGraph example:

```bash
python examples/langgraph_agent.py
```

The integrations keep AgentGuard at the tool-execution boundary rather than replacing the agent framework.

## Audit log

Authorization decisions are recorded in an in-memory audit log:

```python
for event in guard.audit_log.get_events():
    print(event)
```

Events include the timestamp, state, tool, decision, and reason.

## Testing

Install the test dependency:

```bash
python -m pip install -e ".[tests]"
```

Run the test suite:

```bash
pytest -q
```

The repository includes core authorization tests plus LangChain and LangGraph integration tests.

## Examples

- `examples/quickstart.py` — smallest working example
- `examples/attack_demo.py` — attempts unauthorized and unsafe actions
- `examples/langchain_agent.py` — LangChain integration
- `examples/langgraph_agent.py` — LangGraph integration
- `examples/developer_integration.py` — integration-oriented example

## Important limitation

AgentGuard protects calls that are routed through `guard.call()` or otherwise explicitly wrapped by the integration. Direct calls to the underlying Python function bypass AgentGuard.

This project is currently being validated with developers building real AI-agent systems. The goal of the current MVP is to determine whether deterministic tool authorization solves a meaningful problem in real workflows.

If you build tool-using agents, the most useful feedback is practical: what you protected, where AgentGuard fit into your architecture, what failed, and whether you would keep using it.
