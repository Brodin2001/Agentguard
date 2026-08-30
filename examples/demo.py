from agentguard import AgentGuard


# ============================================================
# REAL PYTHON TOOLS
# ============================================================

def search(query):
    print(f"    [REAL TOOL EXECUTED] search('{query}')")
    return f"Search results for '{query}'"


def issue_refund(customer_id, amount):
    print(
        f"    [REAL TOOL EXECUTED] "
        f"issue_refund(customer_id='{customer_id}', amount=${amount})"
    )
    return f"Refunded ${amount} to customer {customer_id}"


def send_email(to, subject, body):
    print(
        f"    [REAL TOOL EXECUTED] "
        f"send_email(to='{to}')"
    )
    return f"Email sent to {to}"


def delete_customer(customer_id):
    print(
        f"    [REAL TOOL EXECUTED] "
        f"delete_customer(customer_id='{customer_id}')"
    )
    return f"Customer {customer_id} deleted"


# ============================================================
# AGENTGUARD POLICY
# ============================================================

policies = {
    "research": {
        "allowed_tools": [
            "search"
        ],

        "argument_rules": {}
    },

    "execution": {
        "allowed_tools": [
            "search",
            "send_email",
            "issue_refund"
        ],

        "argument_rules": {
            "issue_refund": {
                "amount": {
                    "max": 500
                }
            }
        }
    }
}


guard = AgentGuard(policies)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_section(title):
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def print_result(result):
    decision = "ALLOWED" if result["allowed"] else "DENIED"

    print(f"    Decision: {decision}")

    if result["allowed"]:
        print("    Tool executed: YES")
        print(f"    Result: {result['result']}")
    else:
        print("    Tool executed: NO")
        print(f"    Reason: {result['reason']}")


# ============================================================
# DEMO
# ============================================================

print()
print("=" * 64)
print("                    AGENTGUARD v0.1")
print("=" * 64)
print()
print("Runtime authorization for AI-agent tool calls.")
print()
print("The agent can REQUEST a tool.")
print("AgentGuard decides whether that tool can EXECUTE.")
print()


# ============================================================
# TEST 1 — LEGITIMATE RESEARCH
# ============================================================

print_section("1. LEGITIMATE RESEARCH ACTION")

print()
print("Agent state: research")
print("Agent request: search('customer complaints')")
print()

result = guard.call(
    state="research",
    tool="search",
    function=search,
    arguments={
        "query": "customer complaints"
    }
)

print_result(result)


# ============================================================
# TEST 2 — UNAUTHORIZED TOOL
# ============================================================

print_section("2. UNAUTHORIZED TOOL ATTEMPT")

print()
print("Agent state: research")
print("Agent request: issue_refund(customer=123, amount=$100)")
print()

result = guard.call(
    state="research",
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "customer_id": "123",
        "amount": 100
    }
)

print_result(result)


# ============================================================
# TEST 3 — EXCESSIVE ARGUMENT
# ============================================================

print_section("3. EXCESSIVE ARGUMENT ATTEMPT")

print()
print("Agent state: execution")
print("Agent request: issue_refund(customer=123, amount=$5000)")
print()

result = guard.call(
    state="execution",
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "customer_id": "123",
        "amount": 5000
    }
)

print_result(result)


# ============================================================
# TEST 4 — AUTHORIZED EXECUTION
# ============================================================

print_section("4. AUTHORIZED EXECUTION")

print()
print("Agent state: execution")
print("Agent request: issue_refund(customer=123, amount=$100)")
print()

result = guard.call(
    state="execution",
    tool="issue_refund",
    function=issue_refund,
    arguments={
        "customer_id": "123",
        "amount": 100
    }
)

print_result(result)


# ============================================================
# AUDIT LOG
# ============================================================

print_section("5. AUDIT LOG")

print()

for event in guard.audit_log.get_events():
    print(
        f"{event['decision']:7} | "
        f"{event['state']:9} | "
        f"{event['tool']:15} | "
        f"{event['reason']}"
    )


print()
print("=" * 64)
print("                         DEMO COMPLETE")
print("=" * 64)
print()