# AgentGuard

A lightweight authorization layer for AI agents and tool execution.

## What it does

AgentGuard sits between an AI agent and the tools it wants to execute.

Instead of allowing the model to directly decide whether an action happens, AgentGuard evaluates the requested tool call against an explicit policy.

AI Agent
↓
Tool Request
↓
AgentGuard
↓
Allow / Deny
↓
Tool Execution

## Why

AI agents are increasingly being given access to real tools such as:

- APIs
- databases
- email
- CRMs
- files
- external services

Prompt instructions and framework guardrails can influence model behaviour, but they should not be the final security boundary.

AgentGuard experiments with putting deterministic authorization outside the model's control.

## Current MVP

The current MVP focuses on:

- Tool authorization
- Explicit policies
- Allow/deny decisions
- Audit logging
- Python-based agent/tool workflows

This project is currently being validated with AI-agent developers.

## Example

An agent requests:

send_email(to="customer@example.com")

AgentGuard evaluates the request against the configured policy.

If permitted:

ALLOW

If not permitted:

DENY

The goal is to make this type of authorization easier than developers writing their own permission logic for every agent.

## Status

Early MVP / validation stage.

The project is actively being tested with developers building real AI-agent systems.

Feedback, criticism and practical use cases are welcome.

## Getting Started

Clone the repository:

git clone https://github.com/Brodin2001/Agentguard.git

cd Agentguard

The project is currently experimental and intended for evaluation rather than production security use.

## Feedback

If you're building agents with real tool access and have experience with permissions, guardrails, human approval or tool authorization, I'd especially like to hear how you're handling that problem today.
