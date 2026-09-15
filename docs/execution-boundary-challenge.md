# Execution-Boundary Challenge

## The question

When an AI agent is allowed to perform a consequential action, what guarantees that the action that actually executes is still the action that was authorized?

This is a technical experiment, not a claim that existing agent frameworks are insecure.

## A minimal test

Take an existing agent workflow that has a permission, approval, allowlist, or policy step before a consequential tool call.

Record one concrete action at the authorization point, for example:

```text
operation = send_email
target = customer@example.com
arguments = {subject: "Invoice", body: "..."}
identity = agent-1
```

Then, before the underlying callable executes, deliberately test whether changing one of these values is detected:

- tool / capability
- arguments
- target / resource
- agent identity
- runtime identity / execution context
- authorization state
- expiry / freshness
- execution capability

The expected security property is simple:

> If the action reaching the executor is materially different from the action that was authorized, the execution should be rejected.

## Why this is worth testing

Human approval, OAuth, RBAC, MCP permissions, framework middleware, and application-level checks can all be useful controls. This experiment asks a narrower question: does the control remain bound to the concrete action at the point where the side effect occurs?

Different architectures may answer this in different ways. A system that already guarantees the property does not need another layer merely because this repository exists.

## Try it against your own architecture

The most useful result is not a compliment or a theoretical opinion. It is a reproducible test result from a real tool path.

If your framework or application already handles this, document how.

If it does not, try the mutation against a non-production test environment and document what happens.

## AgentGuard

AgentGuard is one implementation experiment: a local Python runtime authorization layer that can bind a short-lived authorization receipt to the executable capability and action context, then verify that binding immediately before execution.

Repository: https://github.com/Brodin2001/Agentguard

AgentGuard is an early-adopter MVP, not a production security certification. Its documented trust boundary is the explicitly protected execution path; arbitrary same-process code with equivalent privileges can bypass a library-level control by taking an unguarded execution path.

## What would falsify the idea?

This project should be considered unnecessary for a workflow if the existing architecture already provides the required execution-time guarantee with acceptable integration cost.

That is useful evidence, not a failure of the experiment.
