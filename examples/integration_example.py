"""Run with: python examples/integration_example.py"""

from agentguard import AgentGuard


# This represents an existing Python tool in your application.
def send_email(to, subject, body, attachment_count=0):
    print(f"[REAL TOOL] Sending email to {to}: {subject}")
    return "Email sent"


def delete_account(account_id):
    print(f"[REAL TOOL] Deleting account {account_id}")
    return "Account deleted"


guard = AgentGuard({
    "support": {
        "allowed_tools": ["send_email"],
        "argument_rules": {
            "send_email": {"attachment_count": {"max": 3}},
        },
    },
})


def request(label, tool, function, arguments):
    print(f"\n{label}")
    result = guard.call(
        state="support",
        tool=tool,
        function=function,
        arguments=arguments,
    )
    print(f"Decision: {'ALLOWED' if result['allowed'] else 'DENIED'}")
    print(f"Function executed: {'YES' if result['executed'] else 'NO'}")
    print(f"Reason: {result['reason']}")
    if result.get("executed"):
        print(f"Result: {result['result']}")


request(
    "1. Allowed: send_email executes.",
    "send_email",
    send_email,
    {"to": "customer@example.com", "subject": "Update", "body": "Done."},
)
request(
    "2. Unauthorized: delete_account does NOT execute.",
    "delete_account",
    delete_account,
    {"account_id": "acct_123"},
)
request(
    "3. Argument violation: send_email does NOT execute with too many attachments.",
    "send_email",
    send_email,
    {
        "to": "customer@example.com",
        "subject": "Documents",
        "body": "Attached files.",
        "attachment_count": 10,
    },
)

print("\nAudit log:")
for event in guard.audit_log.get_events():
    print(f"{event['decision']} | {event['tool']} | {event['reason']}")
