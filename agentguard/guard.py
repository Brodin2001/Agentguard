from .audit import AuditLog
from .receipt import AuthorizationReceipt, ReceiptAuthority


class AgentGuard:
    """
    AgentGuard controls whether an AI agent is allowed to execute
    a tool based on the current agent state and tool arguments.
    """

    def __init__(self, policies):
        self.policies = policies
        self.audit_log = AuditLog()
        self.receipts = ReceiptAuthority(lambda: self.policies)

    def authorize(self, state, tool, arguments=None):
        """
        Decide whether a tool request is permitted.

        This method NEVER executes the tool.
        """

        if arguments is None:
            arguments = {}

        # Fail closed if the state is unknown.
        if state not in self.policies:
            reason = f"Unknown agent state: {state}"

            self.audit_log.record({
                "state": state,
                "tool": tool,
                "decision": "DENIED",
                "reason": reason
            })

            return {
                "allowed": False,
                "state": state,
                "tool": tool,
                "reason": reason,
                "executed": False,
            }

        state_policy = self.policies[state]

        allowed_tools = state_policy.get(
            "allowed_tools",
            []
        )

        # -------------------------------------------------
        # TOOL AUTHORIZATION
        # -------------------------------------------------

        if tool not in allowed_tools:

            reason = (
                "Tool is not permitted "
                "in the current state."
            )

            self.audit_log.record({
                "state": state,
                "tool": tool,
                "decision": "DENIED",
                "reason": reason
            })

            return {
                "allowed": False,
                "state": state,
                "tool": tool,
                "reason": reason,
                "executed": False,
            }

        # -------------------------------------------------
        # ARGUMENT VALIDATION
        # -------------------------------------------------

        argument_rules = state_policy.get(
            "argument_rules",
            {}
        )

        tool_rules = argument_rules.get(
            tool,
            {}
        )

        for argument_name, rules in tool_rules.items():

            if argument_name not in arguments:
                continue

            value = arguments[argument_name]

            # Maximum
            if "max" in rules:

                try:
                    exceeds_max = value > rules["max"]
                except TypeError:
                    reason = (
                        f"Argument '{argument_name}' has an invalid "
                        "type for the configured maximum rule."
                    )

                    self.audit_log.record({
                        "state": state,
                        "tool": tool,
                        "decision": "DENIED",
                        "reason": reason
                    })

                    return {
                        "allowed": False,
                        "state": state,
                        "tool": tool,
                        "reason": reason,
                        "executed": False,
                    }

                if exceeds_max:

                    reason = (
                        f"Argument '{argument_name}' "
                        f"exceeds maximum allowed "
                        f"value of {rules['max']}."
                    )

                    self.audit_log.record({
                        "state": state,
                        "tool": tool,
                        "decision": "DENIED",
                        "reason": reason
                    })

                    return {
                        "allowed": False,
                        "state": state,
                        "tool": tool,
                        "reason": reason,
                        "executed": False,
                    }

            # Minimum
            if "min" in rules:

                try:
                    below_min = value < rules["min"]
                except TypeError:
                    reason = (
                        f"Argument '{argument_name}' has an invalid "
                        "type for the configured minimum rule."
                    )

                    self.audit_log.record({
                        "state": state,
                        "tool": tool,
                        "decision": "DENIED",
                        "reason": reason
                    })

                    return {
                        "allowed": False,
                        "state": state,
                        "tool": tool,
                        "reason": reason,
                        "executed": False,
                    }

                if below_min:

                    reason = (
                        f"Argument '{argument_name}' "
                        f"is below minimum allowed "
                        f"value of {rules['min']}."
                    )

                    self.audit_log.record({
                        "state": state,
                        "tool": tool,
                        "decision": "DENIED",
                        "reason": reason
                    })

                    return {
                        "allowed": False,
                        "state": state,
                        "tool": tool,
                        "reason": reason,
                        "executed": False,
                    }

        # -------------------------------------------------
        # ALLOWED
        # -------------------------------------------------

        reason = "Tool and arguments are permitted."

        self.audit_log.record({
            "state": state,
            "tool": tool,
            "decision": "ALLOWED",
            "reason": reason
        })

        return {
            "allowed": True,
            "state": state,
            "tool": tool,
            "reason": reason,
            "executed": False,
        }

    def call(
        self,
        state,
        tool,
        function,
        arguments=None
    ):
        """
        Authorize a tool and execute it only if permitted.

        This is the primary integration point for developers.
        """

        if arguments is None:
            arguments = {}

        decision = self.authorize(
            state=state,
            tool=tool,
            arguments=arguments
        )

        # IMPORTANT:
        # The function is never called when denied.
        if not decision["allowed"]:
            return decision

        try:

            result = function(**arguments)

        except Exception as error:

            reason = (
                f"Tool execution failed: {error}"
            )

            self.audit_log.record({
                "state": state,
                "tool": tool,
                "decision": "ERROR",
                "reason": reason
            })

            return {
                **decision,
                "executed": False,
                "error": str(error)
            }

        return {
            **decision,
            "executed": True,
            "result": result
        }

    def issue_receipt(
        self,
        state,
        tool,
        arguments=None,
        target=None,
        agent_id=None,
        runtime_id=None,
        ttl_seconds=30.0,
    ):
        """Authorize one exact action and issue a short-lived receipt."""
        if arguments is None:
            arguments = {}

        decision = self.authorize(
            state=state,
            tool=tool,
            arguments=arguments,
        )
        if not decision["allowed"]:
            raise PermissionError(decision["reason"])

        return self.receipts.issue(
            tool=tool,
            arguments=arguments,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
            ttl_seconds=ttl_seconds,
        )

    def execute_receipt(
        self,
        receipt: AuthorizationReceipt,
        function,
        arguments=None,
        target=None,
        agent_id=None,
        runtime_id=None,
    ):
        """Verify and consume a receipt immediately before tool execution.

        This protects the execution path that explicitly uses this adapter.
        It does not prevent arbitrary code in the same process from calling
        the underlying function through a different route.
        """
        if arguments is None:
            arguments = {}

        allowed, reason = self.receipts.verify_and_consume(
            receipt=receipt,
            tool=receipt.tool,
            arguments=arguments,
            target=target,
            agent_id=agent_id,
            runtime_id=runtime_id,
        )

        if not allowed:
            self.audit_log.record({
                "tool": receipt.tool,
                "decision": "DENIED",
                "reason": reason,
                "receipt_id": receipt.decision_id,
            })
            return {
                "allowed": False,
                "executed": False,
                "reason": reason,
                "receipt_id": receipt.decision_id,
            }

        try:
            result = function(**arguments)
        except Exception as error:
            reason = f"Tool execution failed: {error}"
            self.audit_log.record({
                "tool": receipt.tool,
                "decision": "ERROR",
                "reason": reason,
                "receipt_id": receipt.decision_id,
            })
            return {
                "allowed": True,
                "executed": False,
                "error": str(error),
                "receipt_id": receipt.decision_id,
            }

        self.audit_log.record({
            "tool": receipt.tool,
            "decision": "EXECUTED",
            "reason": reason,
            "receipt_id": receipt.decision_id,
        })
        return {
            "allowed": True,
            "executed": True,
            "result": result,
            "receipt_id": receipt.decision_id,
        }
