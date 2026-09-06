import unittest

from agentguard import AgentGuard


class TestAgentGuard(unittest.TestCase):

    def setUp(self):
        self.executed = False

        def search(query):
            self.executed = True
            return f"Results for {query}"

        def issue_refund(customer_id, amount):
            self.executed = True
            return f"Refunded ${amount}"

        self.search = search
        self.issue_refund = issue_refund

        self.guard = AgentGuard({
            "research": {
                "allowed_tools": [
                    "search"
                ]
            },
            "execution": {
                "allowed_tools": [
                    "search",
                    "issue_refund"
                ],
                "argument_rules": {
                    "issue_refund": {
                        "amount": {
                            "max": 500,
                            "min": 1
                        }
                    }
                }
            }
        })

    def test_allowed_tool_executes(self):
        result = self.guard.call(
            state="research",
            tool="search",
            function=self.search,
            arguments={"query": "customers"}
        )

        self.assertTrue(result["allowed"])
        self.assertTrue(result["executed"])
        self.assertTrue(self.executed)

    def test_allowed_execution_returns_function_result(self):
        result = self.guard.call(
            state="research",
            tool="search",
            function=self.search,
            arguments={"query": "customers"}
        )

        self.assertEqual(result["result"], "Results for customers")

    def test_blocked_tool_does_not_execute(self):
        result = self.guard.call(
            state="research",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": 100
            }
        )

        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertFalse(self.executed)

    def test_unknown_state_is_denied(self):
        result = self.guard.call(
            state="unknown",
            tool="search",
            function=self.search,
            arguments={"query": "customers"}
        )

        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertFalse(self.executed)
        self.assertIn("Unknown agent state", result["reason"])

    def test_allowed_argument_executes(self):
        result = self.guard.call(
            state="execution",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": 100
            }
        )

        self.assertTrue(result["allowed"])
        self.assertTrue(result["executed"])
        self.assertTrue(self.executed)

    def test_amount_above_maximum_is_blocked(self):
        result = self.guard.call(
            state="execution",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": 5000
            }
        )

        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertFalse(self.executed)

    def test_amount_below_minimum_is_blocked(self):
        result = self.guard.call(
            state="execution",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": 0
            }
        )

        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertFalse(self.executed)

    def test_invalid_argument_type_is_denied(self):
        result = self.guard.call(
            state="execution",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": "500"
            }
        )

        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertFalse(self.executed)
        self.assertIn("invalid type", result["reason"])

    def test_tool_execution_error_is_returned_and_logged(self):
        def failing_tool():
            self.executed = True
            raise RuntimeError("simulated failure")

        result = self.guard.call(
            state="execution",
            tool="search",
            function=failing_tool,
            arguments={}
        )

        self.assertTrue(self.executed)
        self.assertTrue(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertEqual(result["error"], "simulated failure")
        self.assertEqual(
            self.guard.audit_log.get_events()[-1]["decision"],
            "ERROR"
        )

    def test_every_decision_is_logged(self):
        self.guard.call(
            state="research",
            tool="search",
            function=self.search,
            arguments={"query": "customers"}
        )

        self.guard.call(
            state="research",
            tool="issue_refund",
            function=self.issue_refund,
            arguments={
                "customer_id": "123",
                "amount": 100
            }
        )

        events = self.guard.audit_log.get_events()

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["decision"], "ALLOWED")
        self.assertEqual(events[1]["decision"], "DENIED")


if __name__ == "__main__":
    unittest.main()
