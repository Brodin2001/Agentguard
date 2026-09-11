import hashlib
import inspect
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from examples.openworkproof_apply_patch import (
    OWP_TOOL,
    build_guard,
    guarded_apply_patch,
)


def _fake_owp(monkeypatch, calls):
    def fake_execute_apply_patch(
        ledger_path,
        *,
        evidence_root,
        context,
        request,
        request_arguments,
        execution_facts,
        sidecar_private_key,
        patch_bytes,
        candidate_workspace,
        handler,
        clock,
    ):
        calls.append(
            (
                ledger_path,
                {
                    "evidence_root": evidence_root,
                    "context": context,
                    "request": request,
                    "request_arguments": request_arguments,
                    "execution_facts": execution_facts,
                    "sidecar_private_key": sidecar_private_key,
                    "patch_bytes": patch_bytes,
                    "candidate_workspace": candidate_workspace,
                    "handler": handler,
                    "clock": clock,
                },
            )
        )

        return {"status": "succeeded"}

    fake_openworkproof = ModuleType("openworkproof")
    fake_mcp_server = ModuleType("openworkproof.mcp_server")

    fake_openworkproof.__path__ = []
    fake_mcp_server.execute_apply_patch = fake_execute_apply_patch
    fake_openworkproof.mcp_server = fake_mcp_server

    monkeypatch.setitem(
        sys.modules,
        "openworkproof",
        fake_openworkproof,
    )
    monkeypatch.setitem(
        sys.modules,
        "openworkproof.mcp_server",
        fake_mcp_server,
    )


def _inputs(tmp_path):
    workspace = SimpleNamespace(
        worktree=tmp_path,
    )

    request = SimpleNamespace(
        actor_id="agent-1",
    )

    request_arguments = SimpleNamespace(
        target_paths=("src/app.py",),
    )

    facts = SimpleNamespace(
        execution_context_id="run-1",
    )

    patch_bytes = b"test patch"

    return (
        workspace,
        request,
        request_arguments,
        facts,
        patch_bytes,
    )


def test_openworkproof_adapter_executes_real_owp_path(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    result = guarded_apply_patch(
        guard=build_guard(),
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert result["allowed"] is True
    assert result["executed"] is True
    assert result["result"] == {"status": "succeeded"}

    assert len(calls) == 1
    assert calls[0][1]["request"].actor_id == "agent-1"
    assert calls[0][1]["request_arguments"].target_paths == (
        "src/app.py",
    )
    assert (
        calls[0][1]["execution_facts"].execution_context_id
        == "run-1"
    )


def test_openworkproof_adapter_binds_actual_patch_digest(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    guard = build_guard()
    issued = []

    original_issue_receipt = guard.issue_receipt

    def capture_issue_receipt(*args, **kwargs):
        issued.append(kwargs.copy())
        return original_issue_receipt(*args, **kwargs)

    monkeypatch.setattr(
        guard,
        "issue_receipt",
        capture_issue_receipt,
    )

    guarded_apply_patch(
        guard=guard,
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert len(issued) == 1
    assert issued[0]["tool"] == OWP_TOOL
    assert issued[0]["arguments"]["target_paths"] == ["src/app.py"]

    assert (
        issued[0]["arguments"]["patch_digest"]
        == hashlib.sha256(patch_bytes).hexdigest()
    )

    assert (
        issued[0]["arguments"]["patch_size_bytes"]
        == len(patch_bytes)
    )

    assert issued[0]["target"] == str(Path(tmp_path).resolve())
    assert issued[0]["agent_id"] == "agent-1"
    assert issued[0]["runtime_id"] == "run-1"

    assert calls[0][1]["patch_bytes"] == patch_bytes

    assert calls[0][1]["candidate_workspace"] is not workspace
    assert (
        calls[0][1]["candidate_workspace"].worktree
        == workspace.worktree
    )

    assert calls[0][1]["request"] is not request
    assert calls[0][1]["request"].actor_id == request.actor_id

    assert calls[0][1]["execution_facts"] is not facts
    assert (
        calls[0][1]["execution_facts"].execution_context_id
        == facts.execution_context_id
    )


def test_openworkproof_adapter_snapshots_request_arguments(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    guard = build_guard()

    original_issue_receipt = guard.issue_receipt

    def issue_then_mutate(*args, **kwargs):
        receipt = original_issue_receipt(*args, **kwargs)
        request_arguments.target_paths = ("evil.py",)
        return receipt

    monkeypatch.setattr(
        guard,
        "issue_receipt",
        issue_then_mutate,
    )

    guarded_apply_patch(
        guard=guard,
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert request_arguments.target_paths == ("evil.py",)

    assert calls[0][1]["request_arguments"] is not request_arguments
    assert calls[0][1]["request_arguments"].target_paths == (
        "src/app.py",
    )


def test_openworkproof_adapter_snapshots_workspace(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    guard = build_guard()

    original_issue_receipt = guard.issue_receipt

    def issue_then_mutate(*args, **kwargs):
        receipt = original_issue_receipt(*args, **kwargs)
        workspace.worktree = Path(r"C:\evil-workspace")
        return receipt

    monkeypatch.setattr(
        guard,
        "issue_receipt",
        issue_then_mutate,
    )

    guarded_apply_patch(
        guard=guard,
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert workspace.worktree == Path(r"C:\evil-workspace")

    assert calls[0][1]["candidate_workspace"] is not workspace
    assert calls[0][1]["candidate_workspace"].worktree == tmp_path


def test_openworkproof_adapter_snapshots_agent_identity(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    guard = build_guard()

    original_issue_receipt = guard.issue_receipt

    def issue_then_mutate(*args, **kwargs):
        receipt = original_issue_receipt(*args, **kwargs)
        request.actor_id = "evil-agent"
        return receipt

    monkeypatch.setattr(
        guard,
        "issue_receipt",
        issue_then_mutate,
    )

    result = guarded_apply_patch(
        guard=guard,
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert result["allowed"] is True
    assert request.actor_id == "evil-agent"
    assert calls[0][1]["request"] is not request
    assert calls[0][1]["request"].actor_id == "agent-1"


def test_openworkproof_adapter_snapshots_runtime_identity(
    monkeypatch,
    tmp_path,
):
    calls = []
    _fake_owp(monkeypatch, calls)

    workspace, request, request_arguments, facts, patch_bytes = _inputs(
        tmp_path
    )

    guard = build_guard()

    original_issue_receipt = guard.issue_receipt

    def issue_then_mutate(*args, **kwargs):
        receipt = original_issue_receipt(*args, **kwargs)
        facts.execution_context_id = "evil-run"
        return receipt

    monkeypatch.setattr(
        guard,
        "issue_receipt",
        issue_then_mutate,
    )

    result = guarded_apply_patch(
        guard=guard,
        ledger_path=tmp_path / "ledger.json",
        evidence_root=tmp_path / "evidence",
        context=SimpleNamespace(),
        request=request,
        request_arguments=request_arguments,
        execution_facts=facts,
        sidecar_private_key=object(),
        patch_bytes=patch_bytes,
        candidate_workspace=workspace,
        handler=lambda command: command,
        clock=lambda: SimpleNamespace(),
    )

    assert result["allowed"] is True
    assert facts.execution_context_id == "evil-run"

    assert calls[0][1]["execution_facts"] is not facts
    assert (
        calls[0][1]["execution_facts"].execution_context_id
        == "run-1"
    )


def test_execute_receipt_has_no_caller_supplied_callable_path():
    guard = build_guard()

    assert "function" not in inspect.signature(
        guard.execute_receipt
    ).parameters

    assert OWP_TOOL == "owp.apply_patch"
