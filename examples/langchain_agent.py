"""Run with: python examples/langchain_agent.py

This uses a local fake LangChain model so no API key or external service is needed.
Replace DemoModel with your configured LangChain chat model in a real agent.
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from agentguard import AgentGuard


# Existing application functions. AgentGuard leaves these functions unchanged.
def send_email(to: str, subject: str, body: str, attachment_count: int = 0) -> str:
    print(f"[REAL TOOL EXECUTED] Sending email to {to}: {subject}")
    return "Email sent"


def delete_account(account_id: str) -> str:
    print(f"[REAL TOOL EXECUTED] Deleting account {account_id}")
    return "Account deleted"


guard = AgentGuard({
    "support": {
        "allowed_tools": ["send_email"],
        "argument_rules": {
            "send_email": {"attachment_count": {"max": 3}},
        },
    },
})


# These are the LangChain tools supplied to the agent. Each wrapper sends the
# model's requested arguments through AgentGuard before calling the real tool.
@tool("send_email")
def guarded_send_email(
    to: str, subject: str, body: str, attachment_count: int = 0
) -> str:
    """Send a customer email."""
    print("[AGENT REQUEST] send_email")
    decision = guard.call(
        state="support",
        tool="send_email",
        function=send_email,
        arguments={
            "to": to,
            "subject": subject,
            "body": body,
            "attachment_count": attachment_count,
        },
    )
    print(f"[AGENTGUARD] {'ALLOWED' if decision['allowed'] else 'DENIED'}")
    return decision.get("result", f"BLOCKED: {decision['reason']}")


@tool("delete_account")
def guarded_delete_account(account_id: str) -> str:
    """Delete a customer account."""
    print("[AGENT REQUEST] delete_account")
    decision = guard.call(
        state="support",
        tool="delete_account",
        function=delete_account,
        arguments={"account_id": account_id},
    )
    print(f"[AGENTGUARD] {'ALLOWED' if decision['allowed'] else 'DENIED'}")
    return decision.get("result", f"BLOCKED: {decision['reason']}")


class DemoModel(FakeMessagesListChatModel):
    """A local model that makes three tool requests for this demonstration."""

    def bind_tools(self, tools, **kwargs):
        return self


model = DemoModel(responses=[
    AIMessage(content="", tool_calls=[{
        "name": "send_email",
        "args": {"to": "customer@example.com", "subject": "Update", "body": "Done."},
        "id": "call_allowed",
    }]),
    AIMessage(content="", tool_calls=[{
        "name": "delete_account",
        "args": {"account_id": "acct_123"},
        "id": "call_denied_tool",
    }]),
    AIMessage(content="", tool_calls=[{
        "name": "send_email",
        "args": {
            "to": "customer@example.com",
            "subject": "Attachments",
            "body": "Please see attached.",
            "attachment_count": 10,
        },
        "id": "call_denied_argument",
    }]),
    AIMessage(content="Agent run complete."),
])

agent = create_agent(model, tools=[guarded_send_email, guarded_delete_account])
agent.invoke({"messages": [{"role": "user", "content": "Process the support requests."}]})

print("\nAudit log:")
for event in guard.audit_log.get_events():
    print(f"{event['decision']} | {event['tool']} | {event['reason']}")
