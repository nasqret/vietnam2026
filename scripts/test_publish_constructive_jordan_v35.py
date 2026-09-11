"""The bounded handoff rejects observations before any fork or write."""
import ast
from pathlib import Path
from types import SimpleNamespace
import pytest

import publish_constructive_jordan_v35 as publish


@pytest.mark.parametrize("value", [{}, {"source_binding_sha256": "a"*64},
    SimpleNamespace(require_unchanged=lambda: None), "saved-receipt.json"])
def test_post_audit_cannot_start_from_saved_or_lookalike_authority(value, monkeypatch):
    import os
    def forbidden(): pytest.fail("foreign authority reached fork")
    monkeypatch.setattr(os, "fork", forbidden)
    with pytest.raises(ValueError, match="actual proof audit"):
        publish._bounded_post_audit(value, SimpleNamespace())


def test_actual_capability_is_inherited_not_deserialized_or_reconstructed():
    tree = ast.parse(Path(publish.__file__).read_text())
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    handoff = ast.unparse(functions["_bounded_post_audit"])
    complete = ast.unparse(functions["_complete_from_live_audit"])
    installed = ast.unparse(functions["_publish_installed_from_live_audit"])
    assert "_complete_from_live_audit(audit, args)" in handoff
    assert "type(audit) is not checking.FreshProofAudit" in handoff
    assert handoff.count("audit.require_unchanged()") == 2
    assert "resource.setrlimit(resource.RLIMIT_CPU, checking.CPU_LIMITS)" in handoff
    assert "os.WNOHANG" in handoff and "os.killpg" in handoff
    assert "builder.build_payloads(audit)" in complete
    assert "context_from_live_audit(audit)" in installed
    assert "process.ISOLATE_PHASE_GROUP = False" in handoff
    assert "signal.ITIMER_VIRTUAL" in handoff
    assert not any(token in handoff+complete for token in ("pickle", "importlib.reload", "FreshProofAudit("))


def test_main_still_runs_all_fresh_gates_before_the_fork():
    tree = ast.parse(Path(publish.__file__).read_text())
    main = ast.unparse(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"))
    assert main.index("builder.preflight_inputs()") < main.index("audit_module.verify_in_fresh_windows()") < main.index("_bounded_post_audit(audit, args)")
