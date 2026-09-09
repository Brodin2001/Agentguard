from .audit import AuditLog
from .receipt import AuthorizationReceipt, ReceiptAuthority
import secrets
from typing import Any, Callable


class AgentGuard:
    """Runtime authorization for AI-agent tool calls."""

    def __init__(self, policies):
        self.policies = policies
        self.audit_log = AuditLog()
        self.receipts = ReceiptAuthority(lambda: self.policies)
        self._capabilities: dict[str, tuple[str, Callable[..., Any]]] = {}
        self._tool_capabilities: dict[str, str] = {}

    def bind_tool(self, tool: str, function: Callable[..., Any]) -> str:
        """Register an exact executable capability for a tool."""
        capability_id = secrets.token_urlsafe(18)
        self._capabilities[capability_id] = (tool, function)
        self._tool_capabilities[tool] = capability_id
        return capability_id

    def _capability_for_tool(self, tool: str):
        capability_id = self._tool_capabilities.get(tool)
        if capability_id is None:
            return None
        return capability_id, self._capabilities[capability_id][1]

    def authorize(self, state, tool, arguments=None):
        """Decide whether a tool request is permitted without executing it."""
        if arguments is None:
            arguments = {}
        if state not in self.policies:
            reason = f"Unknown agent state: {state}"
            self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
            return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}

        state_policy = self.policies[state]
        if tool not in state_policy.get("allowed_tools", []):
            reason = "Tool is not permitted in the current state."
            self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
            return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}

        tool_rules = state_policy.get("argument_rules", {}).get(tool, {})
        for argument_name, rules in tool_rules.items():
            if argument_name not in arguments:
                continue
            value = arguments[argument_name]
            if "max" in rules:
                try:
                    exceeds_max = value > rules["max"]
                except TypeError:
                    reason = f"Argument '{argument_name}' has an invalid type for the configured maximum rule."
                    self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
                    return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}
                if exceeds_max:
                    reason = f"Argument '{argument_name}' exceeds maximum allowed value of {rules['max']}."
                    self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
                    return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}
            if "min" in rules:
                try:
                    below_min = value < rules["min"]
                except TypeError:
                    reason = f"Argument '{argument_name}' has an invalid type for the configured minimum rule."
                    self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
                    return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}
                if below_min:
                    reason = f"Argument '{argument_name}' is below minimum allowed value of {rules['min']}."
                    self.audit_log.record({"state": state, "tool": tool, "decision": "DENIED", "reason": reason})
                    return {"allowed": False, "state": state, "tool": tool, "reason": reason, "executed": False}

        reason = "Tool and arguments are permitted."
        self.audit_log.record({"state": state, "tool": tool, "decision": "ALLOWED", "reason": reason})
        return {"allowed": True, "state": state, "tool": tool, "reason": reason, "executed": False}

    def call(self, state, tool, function, arguments=None):
        """Authorize and execute a registered tool capability."""
        if arguments is None:
            arguments = {}
        bound = self._capability_for_tool(tool)
        if bound is None:
            self.bind_tool(tool, function)
            bound = self._capability_for_tool(tool)
        capability_id, registered = bound
        if registered is not function:
            return {"allowed": False, "executed": False, "reason": "Callable does not match the bound tool capability."}
        decision = self.authorize(state, tool, arguments)
        if not decision["allowed"]:
            return decision
        try:
            result = registered(**arguments)
        except Exception as error:
            reason = f"Tool execution failed: {error}"
            self.audit_log.record({"state": state, "tool": tool, "decision": "ERROR", "reason": reason})
            return {**decision, "executed": False, "error": str(error)}
        return {**decision, "executed": True, "result": result}

    def issue_receipt(
        self, state, tool, arguments=None, target=None,
        agent_id=None, runtime_id=None, ttl_seconds=30.0,
        capability_id=None,
    ):
        """Authorize one exact action for a bound executable capability."""
        if arguments is None:
            arguments = {}
        if capability_id is None:
            bound = self._capability_for_tool(tool)
            if bound is None:
                raise ValueError(f"Tool '{tool}' has no bound executable capability.")
            capability_id, _ = bound
        else:
            capability = self._capabilities.get(capability_id)
            if capability is None or capability[0] != tool:
                raise ValueError("Capability does not match the requested tool.")
        decision = self.authorize(state, tool, arguments)
        if not decision["allowed"]:
            raise PermissionError(decision["reason"])
        return self.receipts.issue(
            state=state,
            tool=tool,
            capability_id=capability_id,
            arguments=arguments,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
            ttl_seconds=ttl_seconds,
        )

    def execute_receipt(
        self, receipt: AuthorizationReceipt, arguments=None,
        target=None, agent_id=None, runtime_id=None,
    ):
        """Verify, consume, resolve, and execute the exact bound capability."""
        if arguments is None:
            arguments = {}
        capability = self._capabilities.get(receipt.capability_id)
        if capability is None:
            reason = "Authorized executable capability is no longer registered."
            self.audit_log.record({"state": receipt.state, "tool": receipt.tool, "decision": "DENIED", "reason": reason, "receipt_id": receipt.decision_id})
            return {"allowed": False, "executed": False, "reason": reason, "receipt_id": receipt.decision_id}
        bound_tool, function = capability
        if bound_tool != receipt.tool:
            reason = "Executable capability is bound to a different tool."
            self.audit_log.record({"state": receipt.state, "tool": receipt.tool, "decision": "DENIED", "reason": reason, "receipt_id": receipt.decision_id})
            return {"allowed": False, "executed": False, "reason": reason, "receipt_id": receipt.decision_id}

        allowed, reason = self.receipts.verify_and_consume(
            receipt=receipt,
            tool=bound_tool,
            capability_id=receipt.capability_id,
            arguments=arguments,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
        )
        if not allowed:
            self.audit_log.record({"state": receipt.state, "tool": receipt.tool, "decision": "DENIED", "reason": reason, "receipt_id": receipt.decision_id})
            return {"allowed": False, "executed": False, "reason": reason, "receipt_id": receipt.decision_id}

        try:
            result = function(**arguments)
        except Exception as error:
            reason = f"Tool execution failed: {error}"
            self.audit_log.record({"state": receipt.state, "tool": receipt.tool, "decision": "ERROR", "reason": reason, "receipt_id": receipt.decision_id})
            return {"allowed": True, "executed": False, "error": str(error), "receipt_id": receipt.decision_id}

        self.audit_log.record({"state": receipt.state, "tool": receipt.tool, "decision": "EXECUTED", "reason": reason, "receipt_id": receipt.decision_id})
        return {"allowed": True, "executed": True, "result": result, "receipt_id": receipt.decision_id}
