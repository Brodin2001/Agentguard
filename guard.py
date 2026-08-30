from .audit import AuditLog


class AgentGuard:
    """
    AgentGuard controls whether an AI agent is allowed to execute
    a tool based on the current agent state and tool arguments.
    """

    def __init__(self, policies):
        self.policies = policies
        self.audit_log = AuditLog()

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

                if value > rules["max"]:

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

                if value < rules["min"]:

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
