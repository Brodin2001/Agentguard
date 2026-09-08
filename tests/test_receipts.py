import unittest
from dataclasses import replace

from agentguard import AgentGuard


class TestAuthorizationReceipts(unittest.TestCase):
    def setUp(self):
        self.executed = []
        self.policies = {
            "execution": {
                "allowed_tools": ["refund"],
                "argument_rules": {
                    "refund": {"amount": {"min": 1, "max": 500}}
                },
            }
        }
        self.guard = AgentGuard(self.policies)

    def refund(self, customer_id, amount):
        self.executed.append((customer_id, amount))
        return f"Refunded ${amount}"

    def issue(self, amount=100, target="customer-123"):
        return self.guard.issue_receipt(
            state="execution",
            tool="refund",
            arguments={"customer_id": target, "amount": amount},
            target=target,
            agent_id="agent-1",
            runtime_id="run-1",
            ttl_seconds=30,
        )

    def test_exact_action_executes_once(self):
        receipt = self.issue()
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertTrue(result["allowed"])
        self.assertTrue(result["executed"])
        self.assertEqual(self.executed, [("customer-123", 100)])

    def test_changed_argument_is_blocked(self):
        receipt = self.issue(amount=100)
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 400},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertIn("Arguments do not match", result["reason"])
        self.assertEqual(self.executed, [])

    def test_changed_target_is_blocked(self):
        receipt = self.issue(target="customer-123")
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-999",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertIn("Target does not match", result["reason"])
        self.assertEqual(self.executed, [])

    def test_changed_identity_is_blocked(self):
        receipt = self.issue()
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="different-agent",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertFalse(result["executed"])
        self.assertIn("Agent identity", result["reason"])

    def test_replay_is_blocked(self):
        receipt = self.issue()
        first = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        second = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertTrue(first["executed"])
        self.assertFalse(second["allowed"])
        self.assertFalse(second["executed"])
        self.assertIn("already been consumed", second["reason"])
        self.assertEqual(len(self.executed), 1)

    def test_expired_receipt_is_blocked(self):
        receipt = self.guard.receipts.issue(
            state="execution",
            tool="refund",
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
            ttl_seconds=1,
        )
        authority = self.guard.receipts
        authority._clock = lambda: receipt.expires_at
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertIn("expired", result["reason"])
        self.assertEqual(self.executed, [])

    def test_policy_change_invalidates_receipt(self):
        receipt = self.issue()
        self.policies["execution"]["argument_rules"]["refund"]["amount"]["max"] = 50
        result = self.guard.execute_receipt(
            receipt,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-123",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertIn("policy is stale", result["reason"])
        self.assertEqual(self.executed, [])

    def test_tampered_receipt_is_blocked(self):
        receipt = self.issue()
        tampered = replace(receipt, target="customer-999")
        result = self.guard.execute_receipt(
            tampered,
            self.refund,
            arguments={"customer_id": "customer-123", "amount": 100},
            target="customer-999",
            agent_id="agent-1",
            runtime_id="run-1",
        )
        self.assertFalse(result["allowed"])
        self.assertIn("integrity check failed", result["reason"])
        self.assertEqual(self.executed, [])

    def test_denied_action_cannot_issue_receipt(self):
        with self.assertRaises(PermissionError):
            self.guard.issue_receipt(
                state="execution",
                tool="delete_database",
                arguments={},
            )


if __name__ == "__main__":
    unittest.main()
