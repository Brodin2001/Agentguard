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

## OpenWorkProof v1.4.0 integration experiment

The first external integration experiment targets OpenWorkProof's internal `owp.apply_patch` execution path at the pinned **v1.4.0** commit:

```text
OpenWorkProof: 14e967501ac164ba966c635a90b819c8bd60c2fb
AgentGuard:    integration/openworkproof-v1.4.0
```

OpenWorkProof's protected path is:

```text
dispatch_protected_agent_action()
  -> execute_apply_patch()
  -> patch handler
```

The AgentGuard adapter is intentionally placed **immediately before `execute_apply_patch(...)`**. It authorizes a candidate action containing the operation, declared target paths, patch digest/size, workspace target, agent identity and runtime identity. The receipt is then consumed immediately before entering the OWP executor.

```text
candidate action
      |
      v
AgentGuard.issue_receipt()
      |
      v
AgentGuard.execute_receipt()   <-- AgentGuard execution boundary
      |
      v
OpenWorkProof.execute_apply_patch()
      |
      v
OWP patch handler / filesystem mutation
```

OpenWorkProof's own authorization and validation remain intact. The experiment records which layer rejects each adversarial case; an OWP rejection is not counted as an AgentGuard catch.

### Setup

Use separate disposable checkouts and pin both sides before testing:

```bash
# AgentGuard
 git clone https://github.com/Brodin2001/Agentguard.git
 cd Agentguard
 git checkout integration/openworkproof-v1.4.0
 python -m pip install -e ".[tests]"

# In a separate directory: OpenWorkProof
 git clone https://github.com/dengyier/OpenWorkProof.git
 cd OpenWorkProof
 git checkout 14e967501ac164ba966c635a90b819c8bd60c2fb
 python -m pip install -e .
```

Then use `examples/openworkproof_apply_patch.py` as the adapter skeleton. The real OWP `execute_apply_patch(...)` call should be supplied as the `execute_owp` closure.

### Initial attack matrix

The combined experiment should distinguish:

1. unchanged authorized patch — expected execution;
2. changed patch digest/content — expected rejection;
3. changed target path — expected rejection;
4. changed workspace target — expected rejection;
5. changed agent identity — expected rejection;
6. changed runtime identity — expected rejection;
7. receipt replay — expected rejection;
8. expired receipt — expected rejection;
9. policy change after issuance — expected rejection;
10. direct/alternate execution path — test separately and label it as outside AgentGuard's explicit protected path if it bypasses the adapter.

For each case record: the authorized action, mutation attempted, whether AgentGuard was reached, AgentGuard's decision, whether OpenWorkProof rejected it, whether the patch handler ran, and repository state before/after.

The adapter is an integration experiment, not a claim that AgentGuard controls arbitrary same-process execution outside the protected path.

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
- OpenWorkProof v1.4.0 action-bound `owp.apply_patch` experiment

LangChain example:

```bash
python examples/langchain_agent.py
```

LangGraph example:

```bash
python examples/langgraph_agent.py
```

OpenWorkProof adapter example:

```bash
python examples/openworkproof_apply_patch.py
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
pytest -q tests/test_guard.py tests/test_receipts.py tests/test_openworkproof_adapter.py
```

The receipt tests deliberately attack the authorization boundary with altered arguments, substituted targets, identity changes, replay, expiry, policy changes, and receipt tampering. The OpenWorkProof adapter tests separately verify exact-action mutation and replay rejection at the AgentGuard layer.

## Examples

- `examples/quickstart.py` — smallest working example
- `examples/attack_demo.py` — attempts unauthorized and unsafe actions
- `examples/langchain_agent.py` — LangChain integration
- `examples/langgraph_agent.py` — LangGraph integration
- `examples/developer_integration.py` — integration-oriented example
- `examples/openworkproof_apply_patch.py` — OpenWorkProof v1.4.0 adapter skeleton

## Important limitation

AgentGuard protects execution paths that are explicitly routed through `guard.call()` or `guard.execute_receipt()` (or an integration that provides equivalent enforcement). Direct calls to the underlying Python function bypass AgentGuard.

The v0.2 receipt experiment is designed to test whether binding authorization to the exact candidate action materially improves the execution boundary. It is not presented as a complete security boundary against arbitrary code with equivalent process privileges.

This project is being validated with developers building real AI-agent systems. The goal is evidence: real workflows, real integrations, real bypass attempts, and ultimately willingness to keep using and pay for the solution.
