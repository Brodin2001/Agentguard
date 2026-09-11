# AgentGuard

**Action-bound runtime authorization for AI agent tool calls.**

AgentGuard is a lightweight Python authorization layer designed to sit at the execution boundary between an AI agent and consequential tools.

Its core model is simple:

> **Authorization should remain bound to the exact action that executes.**

For consequential actions, AgentGuard can issue a short-lived authorization receipt bound to the exact tool, arguments, target, agent identity, runtime identity, executable capability, and policy state. The protected execution path verifies that binding immediately before the side effect.

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

For consequential actions, bind the executable capability, issue a short-lived receipt for the exact candidate action, then consume that receipt immediately before execution:

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

Execution fails closed if the receipt no longer matches the action or policy, including:

- changed arguments
- changed target
- changed agent identity
- changed runtime identity
- substituted executable capability
- expired receipt
- replayed receipt
- tampered receipt
- stale policy

The receipt MAC is intended to make the receipt tamper-evident within the AgentGuard process. It does not prevent arbitrary same-process code with equivalent privileges from calling an underlying function through another route.

## Integrations

AgentGuard includes examples for:

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

The receipt tests deliberately attack the authorization boundary with altered arguments, substituted targets, identity changes, replay, expiry, policy changes, receipt tampering, and executable-capability substitution.

## Independent security validation

AgentGuard's action-bound execution model has been independently adversarially retested against an OpenWorkProof integration.

The independent retest ran **39/39 cases successfully**, including argument, target, agent-identity, runtime-identity, capability-substitution, replay, expiry, policy-staleness, and legitimate-execution cases. Two previously identified High-severity findings (AG-CORE-01 and AG-OWP-01) were independently verified as remediated.

This is validation evidence, not a security certification or claim of complete protection.

## Examples

- `examples/quickstart.py` — smallest working example
- `examples/attack_demo.py` — attempts unauthorized and unsafe actions
- `examples/langchain_agent.py` — LangChain integration
- `examples/langgraph_agent.py` — LangGraph integration
- `examples/developer_integration.py` — integration-oriented example

## Important limitation

AgentGuard protects execution paths that are explicitly routed through `guard.call()` or `guard.execute_receipt()` (or an integration providing equivalent enforcement). Direct calls to the underlying Python function bypass AgentGuard.

The project is being validated with developers building real AI-agent systems. The objective is evidence from real workflows and consequential actions: installs, integrations, bypass attempts, continued use, and ultimately willingness to pay.
