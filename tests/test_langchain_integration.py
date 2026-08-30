import unittest

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from agentguard import AgentGuard


class FakeToolCallingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class TestLangChainIntegration(unittest.TestCase):
    def test_agent_tool_requests_are_guarded_before_execution(self):
        executed = []

        def send_email(to, attachment_count=0):
            executed.append(("send_email", to))
            return "Email sent"

        def delete_account(account_id):
            executed.append(("delete_account", account_id))
            return "Account deleted"

        guard = AgentGuard({
            "support": {
                "allowed_tools": ["send_email"],
                "argument_rules": {
                    "send_email": {"attachment_count": {"max": 3}},
                },
            },
        })

        @tool("send_email")
        def guarded_send_email(to: str, attachment_count: int = 0) -> str:
            """Send a customer email."""
            result = guard.call(
                state="support",
                tool="send_email",
                function=send_email,
                arguments={"to": to, "attachment_count": attachment_count},
            )
            return result.get("result", f"BLOCKED: {result['reason']}")

        @tool("delete_account")
        def guarded_delete_account(account_id: str) -> str:
            """Delete a customer account."""
            result = guard.call(
                state="support",
                tool="delete_account",
                function=delete_account,
                arguments={"account_id": account_id},
            )
            return result.get("result", f"BLOCKED: {result['reason']}")

        model = FakeToolCallingModel(responses=[
            AIMessage(content="", tool_calls=[{
                "name": "send_email",
                "args": {"to": "customer@example.com"},
                "id": "allowed",
            }]),
            AIMessage(content="", tool_calls=[{
                "name": "delete_account",
                "args": {"account_id": "acct_123"},
                "id": "denied_tool",
            }]),
            AIMessage(content="", tool_calls=[{
                "name": "send_email",
                "args": {"to": "customer@example.com", "attachment_count": 10},
                "id": "denied_argument",
            }]),
            AIMessage(content="Done."),
        ])

        agent = create_agent(model, tools=[guarded_send_email, guarded_delete_account])
        agent.invoke({"messages": [{"role": "user", "content": "Run tools."}]})

        self.assertEqual(executed, [("send_email", "customer@example.com")])
        self.assertEqual(
            [event["decision"] for event in guard.audit_log.get_events()],
            ["ALLOWED", "DENIED", "DENIED"],
        )


if __name__ == "__main__":
    unittest.main()
