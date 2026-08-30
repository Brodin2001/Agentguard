# AgentGuard

AgentGuard is a runtime authorization layer between an AI agent and its Python tools.

Your agent can request a tool. Your policy decides whether that tool is allowed to execute. If a call is denied, AgentGuard does not call the underlying function.

```text
Agent requests tool
        |
   AgentGuard
   /        \
ALLOW       DENY
  |           |
Tool runs  Tool blocked
```

This is an early validation MVP for developers building Python AI agents.

## Install

From this repository:

```bash
python -m pip install -e .
```

## Quickstart

```bash
python examples/quickstart.py
```

The quickstart shows an allowed function call, an unauthorized tool blocked before execution, and an unsafe argument blocked before execution.

## Connect your LangChain agent

AgentGuard can sit between a LangChain agent and the Python tools it is allowed to execute.

```python
from langchain.agents import create_agent
from langchain.tools import tool

from agentguard import AgentGuard


def send_email(to: str, subject: str, body: str) -> str:
    return "Email sent"


guard = AgentGuard({
    "support": {
        "allowed_tools": ["send_email"]
    }
})


@tool("send_email")
def guarded_send_email(to: str, subject: str, body: str) -> str:
    """Send a customer email."""

    result = guard.call(
        state="support",
        tool="send_email",
        function=send_email,
        arguments={
            "to": to,
            "subject": subject,
            "body": body
        },
    )

    return result.get(
        "result",
        f"BLOCKED: {result['reason']}"
    )


agent = create_agent(
    model,
    tools=[guarded_send_email]
)
```

A denied request returns `BLOCKED: ...` to the agent and never calls the underlying function.

Run the included API-key-free LangChain demo:

```bash
python examples/langchain_agent.py
```

## Connect an existing Python tool

Your existing function stays unchanged. Pass it to `guard.call()` instead of calling it directly.

```python
from agentguard import AgentGuard


def send_email(to, subject, body):
    print(f"[REAL TOOL] Sending email to {to}")
    return "Email sent"


guard = AgentGuard({
    "support": {
        "allowed_tools": ["send_email"],
    },
})


result = guard.call(
    state="support",
    tool="send_email",
    function=send_email,
    arguments={
        "to": "customer@example.com",
        "subject": "Update",
        "body": "Your request is complete.",
    },
)
```

For an allowed request:

```python
{
    "allowed": True,
    "state": "support",
    "tool": "send_email",
    "reason": "Tool and arguments are permitted.",
    "executed": True,
    "result": "Email sent",
}
```

For a denied request, `allowed` and `executed` are both `False`; the function was not run.

## Argument limits

Use `min` and `max` policies to constrain arguments before execution:

```python
guard = AgentGuard({
    "payments": {
        "allowed_tools": ["refund"],
        "argument_rules": {
            "refund": {
                "amount": {
                    "min": 1,
                    "max": 500
                }
            }
        }
    }
})
```

A request for:

```python
refund(amount=5000)
```

is denied before the function executes.

## Audit log

Every authorization decision is available in memory:

```python
events = guard.audit_log.get_events()

for event in events:
    print(event)
```

Each event records the timestamp, agent state, tool, decision, and reason.

## Run the demo

See AgentGuard allow legitimate actions and block unauthorized or unsafe requests:

```bash
python examples/demo.py
```

Run the tests:

```bash
pytest -q
```

## Current MVP

AgentGuard currently provides:

* Tool authorization by agent state
* Argument limits
* Fail-closed behavior for unknown states
* Tool execution only after authorization
* In-memory audit logging
* LangChain/LangGraph examples

This is an early validation MVP and is **not intended to be a production security system yet**.

## Feedback

AgentGuard is being built to solve a simple problem:

**How do you stop an AI agent from executing a tool it shouldn't be allowed to execute?**

If you're building AI agents, I'd like to know:

* Would you use something like this?
* Where would you put it in your agent architecture?
* What's missing before you'd try it?
* What would make this useful in production?

**Try it and tell me what you'd change.**
