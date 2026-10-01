"""Small baseline transport/authority tests; no external solver required."""
import importlib.util
from pathlib import Path
import signal
import sys

import pytest


PATH = Path(__file__).with_name("sqrt2_power_automation_baseline.py")
spec = importlib.util.spec_from_file_location("sqrt2_baseline_tests_subject", PATH)
baseline = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = baseline
spec.loader.exec_module(baseline)


def record(text="", **updates):
    return {"reason": "exited", "returncode": 0, "output_truncated": False,
            "stdout": text, **updates}


def test_external_unsat_never_becomes_an_HA_or_campaign_proof():
    result = baseline.classify_z3(record("unsat\n(proof forged)\n"))
    assert result["status"] == "external_unsat_with_unchecked_proof"
    assert not result["proof_checked"] and not result["ha_checked"]
    assert result["solver_proofs_reconstructed"] == result["IR_obligations_closed"] == 0


@pytest.mark.parametrize("process", [None, record("sat\n"), record("unknown\n"),
    record("unsat\n"), record("unsat\n(proof forged)", returncode=1),
    record("unsat\n(proof forged)", reason="wall_limit"),
    record("unsat\n(proof forged)", output_truncated=True)])
def test_failed_or_missing_external_proof_is_unknown(process):
    assert baseline.classify_z3(process)["status"] == "unknown_or_no_proof"


def test_deadline_does_not_start_more_work(monkeypatch):
    monkeypatch.setattr(baseline, "runtime", lambda: pytest.fail("started expired job"))
    assert baseline.bounded(("/unavailable",), deadline=0, seconds=3) is None


def test_existing_supervisor_receives_exact_finite_limits_and_stdin(monkeypatch):
    seen = {}
    class Supervisor:
        ProcessLimits = baseline.runtime().ProcessLimits
        @staticmethod
        def run_bounded(command, **kwargs):
            seen.update(command=command, **kwargs)
            return "observed"
    monkeypatch.setattr(baseline, "runtime", lambda: Supervisor)
    monkeypatch.setattr(baseline.time, "monotonic", lambda: 10.0)
    assert baseline.bounded(("/solver", "-in"), deadline=12.9, seconds=5,
                            input_bytes=b"input") == "observed"
    assert seen["command"] == ("/solver", "-in") and seen["input_bytes"] == b"input"
    assert seen["limits"].wall_seconds == seen["limits"].cpu_seconds == 2


def test_native_worker_constructs_three_exact_empty_context_HA_proofs():
    value = baseline.native_worker()
    accepted = baseline.accept_native(record(baseline.canonical(value).decode()), baseline.source_pins())
    assert [row["formula"] for row in accepted["rows"]] == list(baseline.NATIVE_FORMULAS)
    assert [row["body_proof_nodes"] for row in accepted["rows"]] == [6, 10, 11]
    assert all(row["ha_checked"] and row["false_goal_rejected"] for row in accepted["rows"])
    assert accepted["IR_obligations_closed"] == accepted["model_proof_search_calls"] == 0


@pytest.mark.parametrize("mutation", ["formula", "classical", "check", "source", "certificate", "missing"])
def test_changed_native_evidence_is_rejected(mutation):
    value = baseline.native_worker()
    pins = baseline.source_pins()
    if mutation == "formula": value["rows"][0]["formula"] = "0 = 1"
    elif mutation == "classical": value["rows"][0]["classical"] = True
    elif mutation == "check": value["rows"][0]["ha_checked"] = False
    elif mutation == "source": value["source_pins"] = {}
    elif mutation == "certificate": value["rows"][0]["certificate"] = {"forged": True}
    else: value["rows"].pop()
    with pytest.raises(ValueError):
        baseline.accept_native(record(baseline.canonical(value).decode()), pins)


def test_native_nonzero_exit_never_counts_as_checked():
    assert baseline.accept_native(record("{}", returncode=1), {}) is None


def test_missing_solver_does_not_fall_back_to_installation(monkeypatch):
    monkeypatch.setattr(baseline.shutil, "which", lambda _name: None)
    monkeypatch.setattr(baseline, "bounded", lambda *args, **kwargs: None)
    tools = baseline.probe_tools(100)
    assert tools["vampire"]["status"] == tools["eprover"]["status"] == "unavailable_on_PATH"
    assert tools["z3"]["status"] == "unavailable_on_PATH"


def test_total_budget_uses_and_restores_real_alarm():
    previous = signal.getsignal(signal.SIGALRM)
    with baseline.total_budget(3):
        assert 0 < signal.getitimer(signal.ITIMER_REAL)[0] <= 3
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0
    assert signal.getsignal(signal.SIGALRM) == previous


def test_report_is_exclusive_and_cannot_replace_symlink(tmp_path):
    path = tmp_path / "report.json"
    baseline.write_report(path, {"first": True})
    original = path.read_bytes()
    with pytest.raises(ValueError): baseline.write_report(path, {"second": True})
    assert path.read_bytes() == original
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(ValueError): baseline.write_report(link, {})
