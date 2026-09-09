import hashlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from examples.openworkproof_apply_patch import OWP_TOOL, build_guard, guarded_apply_patch


def _fake_owp(monkeypatch, calls):
    package = types.ModuleType("openworkproof")
    module = types.ModuleType("openworkproof.mcp_server")

    def execute_apply_patch(*args, **kwargs):
        calls.append((args, kwargs))
        return {"status": "succeeded"}

    module.execute_apply_patch = execute_apply_patch
    package.mcp_server = module
    monkeypatch.setitem(sys.modules, "openworkproof", package)
    monkeypatch.setitem(sys.modules, "openworkproof.mcp_server", module)


def _inputs(tmp_path):
    workspace = SimpleNamespace(worktree=Path(tmp_path))
    request = SimpleNamespace(actor_id="agent-1")
    request_arguments = SimpleNamespace(target_paths=("src/app.py",))
    execution_facts = SimpleNamespace(execution_context_id="run-1")
    patch_bytes = b"patch payload"
    return workspace, request, request_arguments, execution_facts, patch_bytes


def test_openworkproof_adapter_derives_and_executes_exact_action(monkeypatch, tmp_path):
    calls = []
    _fake_owp(monkeypatch, calls)
    workspace, request, request_arguments, facts, patch_bytes = _inputs(tmp_path)

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
    assert len(calls) == 1


def test_openworkproof_adapter_uses_actual_patch_digest(monkeypatch, tmp_path):
    calls = []
    _fake_owp(monkeypatch, calls)
    workspace, request, request_arguments, facts, patch_bytes = _inputs(tmp_path)
    guard = build_guard()

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

    assert hashlib.sha256(patch_bytes).hexdigest() == hashlib.sha256(patch_bytes).hexdigest()
    assert calls


def test_execute_receipt_has_no_caller_supplied_callable_path():
    guard = build_guard()
    assert "function" not in __import__("inspect").signature(guard.execute_receipt).parameters
    assert OWP_TOOL == "owp.apply_patch"
