"""Model-free development evaluation must retain bounded, exact evidence."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from training.peano_hydra import frontier  # noqa: E402


@pytest.mark.parametrize("field,value", [
    ("wall_seconds", 0), ("wall_seconds", 31), ("cpu_seconds", 26),
    ("rss_bytes", 64 * 1024**2), ("rss_bytes", 3 * 1024**3),
    ("max_depth", 17), ("max_states", 257), ("max_proposals", True),
])
def test_worker_limits_fail_closed(field, value):
    with pytest.raises(frontier.DevelopmentEvaluationError):
        replace(frontier.WorkerLimits(), **{field: value})


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'{'])
def test_evidence_parser_is_strict(raw):
    with pytest.raises(frontier.DevelopmentEvaluationError):
        frontier.decode(raw)


def test_bounded_exact_publication_never_overwrites(tmp_path):
    target = tmp_path / "receipt.json"
    descriptor = frontier.write_once(target, {"status": "unknown", "model_calls": 0})
    assert frontier.read_record(target)["status"] == "unknown"
    assert descriptor["bytes"] == target.stat().st_size
    with pytest.raises(FileExistsError):
        frontier.write_once(target, {"status": "proved"})
    with pytest.raises(frontier.DevelopmentEvaluationError):
        frontier.read_record(target, limit=3)
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(OSError):
        frontier.read_record(link)


def test_bad_worker_schema_is_rejected_before_resource_mutation(monkeypatch):
    monkeypatch.setattr(frontier, "_guard", lambda limits: pytest.fail("unexpected resource change"))
    with pytest.raises(frontier.DevelopmentEvaluationError, match="fields"):
        frontier.worker({"schema": "anything"})


def test_incomplete_run_cannot_publish_complete_metrics():
    with pytest.raises(frontier.DevelopmentEvaluationError, match="incomplete"):
        frontier.summarize({"reserved_worker_runs": 2}, [])


def test_timeout_kills_only_owned_worker_and_never_claims_proof(monkeypatch):
    calls = []
    class Process:
        returncode = None
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))
        def communicate(self, *args, **kwargs):
            if self.returncode is None:
                raise subprocess.TimeoutExpired("owned-worker", 1)
        def kill(self):
            self.returncode = -9
            calls.append("killed")
    monkeypatch.setattr(frontier.subprocess, "Popen", Process)
    request = {"limits": frontier.WorkerLimits().to_dict(), "goal": {"id": "a"},
               "lane": "closure", "profile_sha256": "a" * 64,
               "epoch_sha256": "b" * 64, "source_files_sha256": "c" * 64, "environment": {}}
    result = frontier.run_isolated(request)
    assert calls[-1] == "killed"
    assert result["status"] == "unknown"
    assert result["reason"] == "wall_limit"
    assert result["kernel_checked"] is False
    assert result["evidence"] is None
    assert result["resources"]["worker_cpu_seconds"] is None
    assert result["resources"]["peak_rss_bytes"] is None
    assert result["model_calls"] == result["solver_calls"] == 0


def test_default_cli_is_plan_only_and_worker_output_is_bounded():
    source = (ROOT / "scripts/eval_peano_hydra_development.py").read_text()
    assert 'action="store_true"' in source
    assert 'if args.run else plan' in source
    assert '2 * 1024 * 1024 + 1' in source
    assert '--execute-models' not in source
    assert 'ssh ' not in source


def test_cli_rejects_output_without_explicit_execution(tmp_path):
    output = tmp_path / "must-not-exist"
    result = subprocess.run([sys.executable, str(frontier.SCRIPT), "--output-dir", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert not output.exists()


def test_corrupted_report_claim_is_rejected_before_replay(tmp_path):
    report = {"schema": frontier.SCHEMA, "status": "completed", "development_only": True,
              "sealed_benchmark": True, "research_claim_eligible": True,
              "model_comparison_performed": False}
    report["report_sha256"] = frontier.digest(report)
    frontier.write_once(tmp_path / "report.json", report)
    with pytest.raises(frontier.DevelopmentEvaluationError, match="claim boundary"):
        frontier.verify_run(tmp_path)


def test_missing_worker_resources_are_not_reported_as_measured_zero():
    plan = {"reserved_worker_runs": 2, "benchmark": {"goals": [{"id": "a", "cohort": "expanded"}]}}
    rows = [{"goal": {"id": "a"}, "lane": lane, "kernel_checked": False, "evidence": None,
             "resources": {"parent_wall_seconds": 5.0, "peak_rss_bytes": None,
                           "worker_cpu_seconds": None}}
            for lane in frontier.LANES]
    metrics = frontier.summarize(plan, rows)
    for lane in frontier.LANES:
        assert metrics[lane]["max_recorded_peak_rss_bytes"] is None
        assert metrics[lane]["recorded_worker_cpu_seconds"] is None
        assert metrics[lane]["unavailable_worker_resource_rows"] == 1
        assert metrics[lane]["cohorts"]["expanded"] == {"goals": 1, "proved": 0, "unknown": 1}


def test_real_worker_search_and_independent_replay_need_no_model():
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.protocol import development_profile
    from training.peano_hydra.runner import policy_environment
    epoch = freeze_epoch()
    plan = {"limits": frontier.WorkerLimits().to_dict(), "profile": development_profile(),
            "benchmark": {"epoch_sha256": epoch.epoch_sha256}, "source": frontier.source_identity(),
            "environment": policy_environment(frontier.execution_capabilities())}
    goal = {"id": "worker-reflexivity-control", "source": "0 = 0", "canonical": "0 = 0"}
    result = frontier.run_isolated(frontier._request(plan, goal, "closure"))
    assert result["kernel_checked"] is True, json.dumps(result, indent=2)
    assert result["model_calls"] == result["solver_calls"] == 0
    assert result["action_records"]
    assert result["resources"]["peak_rss_bytes"] <= plan["limits"]["rss_bytes"]
    replay = frontier.run_isolated(frontier._request(plan, goal, "closure", saved=result))
    assert replay["kernel_checked"] is True, json.dumps(replay, indent=2)
    assert replay["reason"] == "independently_replayed"
    damaged = json.loads(json.dumps(result))
    damaged["evidence"]["replay"]["proof_nodes"] += 1
    rejected = frontier.run_isolated(frontier._request(plan, goal, "closure", saved=damaged))
    assert rejected["kernel_checked"] is False
    assert rejected["status"] == "unknown"
    assert any(message in rejected["diagnostic"] for message in (
        "fresh kernel replay differs", "symbolic successful replay changed",
    ))


@pytest.mark.parametrize("field", ["worker_cpu_seconds", "peak_rss_bytes", "parent_wall_seconds"])
def test_resealed_negative_resource_measurements_are_rejected(field):
    resources = {"parent_wall_seconds": 0.2, "worker_wall_seconds": 0.1,
                 "worker_cpu_seconds": 0.1, "peak_rss_bytes": 1024,
                 "cpu_instructions": None, "energy_joules": None}
    resources[field] = -1
    with pytest.raises(frontier.DevelopmentEvaluationError, match="invalid measured"):
        frontier.validate_resources({"evidence": {}, "resources": resources}, frontier.WorkerLimits())


def test_complete_archival_pipeline_and_resealed_lane_rejection(tmp_path, monkeypatch):
    from training.peano_hydra import benchmark
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.protocol import development_profile
    epoch = freeze_epoch()
    # Small independent engineering fixture, never the measured 68-goal set.
    fixture = {"epoch_sha256": epoch.epoch_sha256,
               "goals": [{"id": "archive-reflexivity-control", "source": "0 = 0",
                          "canonical": "0 = 0", "cohort": "expanded"}]}
    fixture["manifest_sha256"] = frontier.digest(fixture)
    monkeypatch.setattr(benchmark, "build_development_benchmark", lambda unused: fixture)
    plan = frontier.build_plan()
    directory = tmp_path / "run"
    report = frontier.execute_plan(plan, directory)
    assert report["metrics"]["closure"]["cohorts"]["expanded"]["proved"] == 1
    verified = frontier.verify_run(directory)
    assert verified["independently_replayed_proofs"] == 2
    assert verified["deterministically_verified_policy_rows"] == 2
    row_path = directory / "row-000.json"
    row = frontier.read_record(row_path)
    row["config"]["induction"] = True
    raw = frontier.canonical(row) + b"\n"
    row_path.write_bytes(raw)
    report["rows"][0]["bytes"] = len(raw)
    report["rows"][0]["sha256"] = frontier.hashlib.sha256(raw).hexdigest()
    report.pop("report_sha256")
    report["report_sha256"] = frontier.digest(report)
    (directory / "report.json").write_bytes(frontier.canonical(report) + b"\n")
    with pytest.raises(frontier.DevelopmentEvaluationError, match="component configuration"):
        frontier.verify_run(directory)


def test_new_development_guides_and_make_targets_are_connected():
    import re
    for name in ("HYDRA_DEVELOPMENT_EVALUATION.md", "HYDRA_DEVELOPMENT_PROTOCOL.md"):
        source = ROOT / "docs" / name
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" not in target:
                assert (source.parent / target.split("#", 1)[0]).resolve().is_file()
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target, switch in (("hydra-dev-plan", "--plan"), ("hydra-dev-evaluate", "--run"),
                           ("hydra-dev-verify", "--verify")):
        match = re.search(rf"^{target}:\n((?:\t[^\n]*\n)+)", makefile, re.MULTILINE)
        assert match and switch in match.group(1)
        assert "--execute-models" not in match.group(1)
        assert "ssh " not in match.group(1)
