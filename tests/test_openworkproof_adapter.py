from examples.openworkproof_apply_patch import build_guard, guarded_apply_patch


def _action():
    return {
        "operation": "owp.apply_patch",
        "target_paths": ["src/demo.py"],
        "patch_digest": "a" * 64,
        "patch_size_bytes": 10,
    }


def test_openworkproof_adapter_allows_exact_action():
    calls = []
    result = guarded_apply_patch(
        guard=build_guard(),
        action_arguments=_action(),
        workspace_target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
        execute_owp=lambda: calls.append("executed") or "patched",
    )

    assert result["allowed"] is True
    assert result["executed"] is True
    assert calls == ["executed"]


def test_openworkproof_adapter_receipt_cannot_be_reused_for_changed_action():
    guard = build_guard()
    action = _action()
    receipt = guard.issue_receipt(
        state="patch",
        tool="owp.apply_patch",
        arguments=action,
        target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
    )

    changed = {**action, "target_paths": ["src/other.py"]}
    calls = []
    result = guard.execute_receipt(
        receipt,
        lambda **_: calls.append("executed"),
        arguments=changed,
        target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
    )

    assert result["allowed"] is False
    assert result["executed"] is False
    assert calls == []


def test_openworkproof_adapter_receipt_cannot_be_replayed():
    guard = build_guard()
    action = _action()
    receipt = guard.issue_receipt(
        state="patch",
        tool="owp.apply_patch",
        arguments=action,
        target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
    )
    calls = []

    first = guard.execute_receipt(
        receipt,
        lambda **_: calls.append("first"),
        arguments=action,
        target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
    )
    second = guard.execute_receipt(
        receipt,
        lambda **_: calls.append("second"),
        arguments=action,
        target="workspace-1",
        agent_id="agent-1",
        runtime_id="run-1",
    )

    assert first["executed"] is True
    assert second["allowed"] is False
    assert second["executed"] is False
    assert calls == ["first"]
