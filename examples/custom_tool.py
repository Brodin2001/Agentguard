from agentguard import AgentGuard


# --------------------------------
# DEVELOPER-DEFINED TOOLS
# --------------------------------

def send_email(to, subject, body):
    print("\n[REAL TOOL EXECUTED]")
    print(f"Sending email to: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")

    return f"Email sent to {to}"


def lookup_weather(city):
    print("\n[REAL TOOL EXECUTED]")
    print(f"Looking up weather for: {city}")

    return f"Sunny, 22°C in {city}"


# --------------------------------
# AGENTGUARD POLICY
# --------------------------------

policies = {
    "research": {
        "allowed_tools": [
            "search"
        ]
    },

    "execution": {
        "allowed_tools": [
            "send_email",
            "lookup_weather"
        ]
    }
}


guard = AgentGuard(policies)


# --------------------------------
# DEMO HEADER
# --------------------------------

print("\n========================================")
print("      AgentGuard Custom Tool Demo")
print("========================================")


# --------------------------------
# TEST 1
# Unauthorized email during research
# --------------------------------

print("\n=== TEST 1: UNAUTHORIZED TOOL ===")

result = guard.call(
    state="research",
    tool="send_email",
    function=send_email,
    arguments={
        "to": "customer@example.com",
        "subject": "Important update",
        "body": "Your request has been processed."
    }
)

print(result)


# --------------------------------
# TEST 2
# Authorized email during execution
# --------------------------------

print("\n=== TEST 2: AUTHORIZED TOOL ===")

result = guard.call(
    state="execution",
    tool="send_email",
    function=send_email,
    arguments={
        "to": "customer@example.com",
        "subject": "Important update",
        "body": "Your request has been processed."
    }
)

print(result)


# --------------------------------
# TEST 3
# New developer-defined tool
# --------------------------------

print("\n=== TEST 3: NEW CUSTOM TOOL ===")

result = guard.call(
    state="execution",
    tool="lookup_weather",
    function=lookup_weather,
    arguments={
        "city": "Sydney"
    }
)

print(result)


# --------------------------------
# TEST 4
# Same tool, unauthorized state
# --------------------------------

print("\n=== TEST 4: STATE RESTRICTION ===")

result = guard.call(
    state="research",
    tool="lookup_weather",
    function=lookup_weather,
    arguments={
        "city": "Sydney"
    }
)

print(result)


# --------------------------------
# AUDIT LOG
# --------------------------------

print("\n=== AUDIT LOG ===")

for event in guard.audit_log.get_events():
    print(
        f"{event['decision']} | "
        f"{event['state']} | "
        f"{event['tool']} | "
        f"{event['reason']}"
    )