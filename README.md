# AgentGuard

AgentGuard is a lightweight runtime authorization layer for AI agent tool calls.

It evaluates a requested tool call against an explicit policy before the underlying function runs. The v0.2 experiment adds **action-bound authorization receipts**: a short-lived receipt binds authorization to the exact tool, arguments, target, runtime identity, and policy state before the protected execution path runs.

> **Early validation MVP / research experiment. Not a production security system.**

## Install

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

## Action-bound authorization receipts

For consequential actions, the v0.2 experiment lets you authorize an exact candidate action first, then require a receipt immediately before execution:

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
    refund,
    arguments=arguments,
    target="customer-123",
    agent_id="agent-1",
    runtime_id="run-1",
)
```

The receipt is bound to the exact action and policy state. The protected execution path rejects:

- changed arguments
- changed target
- changed agent or runtime identity
- expired receipts
- replayed receipts
- tampered receipts
- receipts issued under a changed policy

The receipt MAC is intended to make the receipt tamper-evident **within the AgentGuard process**. It does not make arbitrary Python code in the same process unable to call an underlying function through another route.

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

LangChain example:

```bash
python examples/langchain_agent.py
```

LangGraph example:

```bash
python examples/langgraph_agent.py
```

## Audit log

Authorization decisions are recorded in an in-memory audit log:

```python
for event in guard.audit_log.get_events():
    print(event)
```

## Testing

```bash
python -m pip install -e ".[tests]"
pytest -q tests/test_guard.py tests/test_receipts.py
```

The receipt tests deliberately attack the authorization boundary with altered arguments, substituted targets, identity changes, replay, expiry, policy changes, and receipt tampering.

## Examples

- `examples/quickstart.py` — smallest working example
- `examples/attack_demo.py` — attempts unauthorized and unsafe actions
- `examples/langchain_agent.py` — LangChain integration
- `examples/langgraph_agent.py` — LangGraph integration
- `examples/developer_integration.py` — integration-oriented example

## Important limitation

AgentGuard protects execution paths that are explicitly routed through `guard.call()` or `guard.execute_receipt()` (or an integration that provides equivalent enforcement). Direct calls to the underlying Python function bypass AgentGuard.

The v0.2 receipt experiment is designed to test whether binding authorization to the exact candidate action materially improves the execution boundary. It is not presented as a complete security boundary against arbitrary code with equivalent process privileges.

This project is being validated with developers building real AI-agent systems. The goal is evidence: real workflows, real integrations, real bypass attempts, and ultimately willingness to keep using and pay for the solution.
