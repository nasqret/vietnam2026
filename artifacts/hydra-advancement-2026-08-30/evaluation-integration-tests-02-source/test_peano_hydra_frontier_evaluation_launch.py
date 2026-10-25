"""Synthetic temporary metadata/approvals/scheduler only; never human evidence.

These fixtures do not execute native proofs, read models, contact SSH, or
submit jobs. They exercise the actual byte closure and single-use budget.
"""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[3]
HELPER = ROOT / "training/peano_hydra/frontier_evaluation_launch.py"


@pytest.fixture
def gate(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("_evaluation_only_test_gate", HELPER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    scratch = tmp_path / "scratch"
    root = scratch / m.REMOTE_PARENT / m.REMOTE_CHILD
    root.mkdir(parents=True)
    monkeypatch.setattr(m, "ROOT", root)
    monkeypatch.setattr(m.safe, "ROOT", root)
    monkeypatch.setenv("SCRATCH", str(scratch))
    monkeypatch.setenv("USER", "synthetic")
    for name in tuple(os.environ):
        if name.startswith(("SLURM_", "SBATCH_", "PEANO_JOB_", "PEANO_HYDRA_")):
            monkeypatch.delenv(name, raising=False)
    def put(name, value):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = value if type(value) is bytes else m.canonical(value) + b"\n"
        path.write_bytes(raw)
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    def seal(value, key):
        value[key] = m.digest({k: v for k, v in value.items() if k != key})
        return value
    commit = "a" * 40
    put(".peano-source-provenance.tsv", (commit + "\tfalse\t2026-08-30T00:00:00Z\n").encode())
    sources = {name: put(name, (ROOT / name).read_bytes() if name.endswith("requirements-helios.lock")
                       else ("# SYNTHETIC SOURCE NOT EXECUTED: " + name + "\n").encode())
               for name in sorted(m.REQUIRED_SOURCES | {"peano-lab/py/synthetic.py"})}
    payloads = {}
    def payload(name, value):
        identity = put(name, value)
        payloads[name] = identity
        return dict(path=name, **identity)
    p = m.PACKAGE + "/review"
    readiness = seal({"status": "human-reviewed-reference-ready", "reviewed_by_human": True,
        "synthetic_only": "NOT HUMAN ACCEPTANCE OR REFERENCE EVIDENCE",
        "epoch_sha256": m.preserved.PINS["epoch_sha256"],
        "lean": {"version": "4.31.0", "toolchain_pin": "leanprover/lean4:v4.31.0"},
        "semantic_checks": {"status": "passed", "semantic_formula_count": 1000, "theorem_count": 400,
            "decision_claim": False, "all_in_scope_results_agree": True, "false_acceptance_count": 0,
            "unresolved_semantics_count": 0, "required_mutations_rejected": True, "kernel_import_boundary_passed": True,
            "original_goal_tests_passed": True, "transactional_history_tests_passed": True},
        "cold_library": {"scope": "full", "epoch_target_count": 2764, "fresh_workers": True,
            "passes": [{"pass_number": i, "checked_count": 2764, "failed_count": 0,
                        "unknown_count": 0, "root_sha256": "f" * 64} for i in (1, 2)]},
        "independent_verification": {"status": "passed", "fresh_reference_recheck": True,
                                      "both_full_cold_passes_rechecked": True}}, "readiness_sha256")
    ready_d = payload(p + "/readiness.json", readiness)
    review = seal({"decision": "accept", "synthetic_only": "NOT HUMAN ACCEPTANCE",
        "human_assertion": {"provided_by_human": True, "identity_attested": False},
        "reference_readiness": dict(ready_d, path="readiness.json")}, "review_sha256")
    review_d = payload(p + "/review.json", review)
    evaluation = {"schema": m.EVALUATION_SCHEMA, "status": "ready-for-explicit-resource-approval",
        "profile": m.PROFILE, "run_id": m.RUN_ID, "gpu_execution_authorized": False,
        "sealed_benchmark": False, "research_claim_eligible": False, "existing_remote_artifacts": m.REMOTE_ARTIFACTS,
        "benchmark_review": review_d,
        **{k: payload(p + "/" + k + ".json", {"synthetic_only": k})
           for k in ("benchmark_manifest", "benchmark_audit", "acceptance_protocol")}}
    seal(evaluation, "request_sha256")
    eval_d = payload(m.INPUTS["evaluation_request"], evaluation)
    request = m.request_template()
    request.update(status="ready-for-explicit-resource-approval", source_commit=commit, source_files=sources,
                   payloads=payloads, payloads_sha256=m.digest(payloads))
    request["semantic_admission"] = {"schema": "peano-hydra-frontier-evaluation-cpu-admission-v1", "status": "passed",
        "evaluation_request_sha256": eval_d["sha256"], "source_files_sha256": m.digest(sources),
        "payloads_sha256": m.digest(payloads), "benchmark_review_sha256": review_d["sha256"],
        "reference_readiness_sha256": ready_d["sha256"], "checker_python": [3, 11, 0],
        "summary": {"status": "completed-origin-metadata-checked-not-executed", "request_file_sha256": eval_d["sha256"],
            "candidate_adapter_manifest_sha256": m.REMOTE_ARTIFACTS["new-frontier"]["adapter_manifest_sha256"],
            "training_job_id": "21438102", "model_weights_loaded": False,
            "existing_remote_artifact_bytes_checked": False, "remote_artifact_recheck_required_before_inference": True}}
    value = SimpleNamespace(module=m, root=root, request=request, commit=commit, calls=[], scheduled={}, released=[],
        snapshot_overrides={}, running=False, fail_submit=False, put=put, payload=payload,
        review=review, readiness=readiness, evaluation=evaluation, seal=seal)
    def resign():
        request["payloads_sha256"] = m.digest(payloads)
        item = put(m.REQUEST, request)
        value.approval = {"schema": m.APPROVAL_SCHEMA, "profile": m.PROFILE, "run_id": m.RUN_ID,
            "approved": True, "approval_reference": "SYNTHETIC TEST ONLY; NOT USER APPROVAL",
            "request_file_sha256": item["sha256"]}
        value.sha = put(m.APPROVAL, value.approval)["sha256"]
    value.resign = resign
    resign()
    def scheduler(argv, environment=None):
        assert environment is None
        value.calls.append(list(argv))
        if argv[0] == "squeue":
            return "".join(f"{job}|{root}|{m.JOB_NAMES[stage]}|PENDING\n" for stage, job in value.scheduled.items())
        if argv[0] == "sacct":
            return "".join(f"{job}|{m.JOB_NAMES[stage]}|{root}|\n" for stage, job in value.scheduled.items())
        if argv[0] == "sbatch":
            identity = m._identity(value.approval, request, value.sha)
            state = m.load_ledger(identity)
            assert state["gpu_seconds"] == 1800 and state["phase"] == "reserve"
            if value.fail_submit: raise ValueError("synthetic ambiguous scheduler response")
            value.scheduled["evaluate"] = "42001"
            return "42001\n"
        if argv[:4] == ["scontrol", "-o", "show", "job"]:
            fields = {"JobId": "42001", "JobName": m.JOB_NAMES["evaluate"], "WorkDir": str(root),
                "JobState": "RUNNING" if value.running else "PENDING", "Reason": "None" if value.running else "JobHeldUser",
                "Priority": "1" if value.running else "0", "Dependency": "(null)", "Requeue": "0", "Account": m.ACCOUNT,
                "Partition": m.PARTITION, "TimeLimit": m.WALL["evaluate"], "NumNodes": "1", "NumCPUs": "8",
                "ReqTRES": "billing=1,cpu=8,mem=64G,node=1,gres/gpu=1"}
            fields.update(value.snapshot_overrides)
            return " ".join(k + "=" + v for k, v in fields.items()) + "\n"
        if argv[:2] == ["scontrol", "release"]:
            assert m.load_ledger(m._identity(value.approval, request, value.sha))["phase"] == "release-authorized"
            value.released.append(argv[-1])
            return ""
        pytest.fail("unexpected external operation " + repr(argv))
    monkeypatch.setattr(m, "run", scheduler)
    return value


def test_new_gate_is_python39_syntax_and_shells_parse():
    ast.parse(HELPER.read_text(), feature_version=(3, 9))
    for name in ("scripts/helios_hydra_frontier_evaluation.sh", "scripts/run_peano_hydra_frontier_evaluation.sh",
                 "slurm/peano_hydra_frontier_evaluation.sbatch"):
        subprocess.run(["bash", "-n", str(ROOT / name)], check=True)


def test_login_byte_gate_does_not_import_the_newer_semantic_engine(gate, monkeypatch):
    m = gate.module
    monkeypatch.setattr(m.sys, "version_info", (3, 9, 25))
    assert m.validate_metadata(gate.sha)[1] == gate.request
    with pytest.raises(ValueError, match="Python>=3.11"):
        m.semantic_check(gate.request)
    assert not gate.calls


@pytest.mark.parametrize("field,value", [
    ("semantic_admission", None), ("training_authorized", True), ("self_training_authorized", True),
    ("resume", True), ("automatic_retry", True), ("maximum_aggregate_gpu_seconds", 7200),
    ("profile", "peano-hydra-frontier-training-v1"), ("status", "draft-missing-prerequisites"),
])
def test_incomplete_or_changed_scope_rejects_before_scheduler(gate, field, value):
    gate.request[field] = value
    gate.resign()
    with pytest.raises(ValueError): gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert not gate.calls and not (gate.root / gate.module.LEDGER).exists()


def test_missing_approval_and_untracked_payload_fail_before_scheduler(gate):
    with pytest.raises(ValueError): gate.module.validate_metadata("0" * 64)
    gate.put(gate.module.PACKAGE + "/unapproved.json", b"unapproved\n")
    with pytest.raises(ValueError, match="closed input"): gate.module.validate_metadata(gate.sha)
    assert not gate.calls


def test_source_bound_cpu_admission_cannot_be_reused_for_changed_inputs(gate):
    gate.request["semantic_admission"]["payloads_sha256"] = "b" * 64
    gate.resign()
    with pytest.raises(ValueError, match="local semantic check"): gate.module.validate_metadata(gate.sha)


def test_single_evaluation_budget_is_charged_before_submit_and_not_refunded(gate):
    result = gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert result["jobs"] == {"evaluate": "42001"} and result["reserved_gpu_seconds"] == 1800
    assert gate.released == ["42001"]
    submitted = [call for call in gate.calls if call[0] == "sbatch"]
    assert len(submitted) == 1 and "--hold" in submitted[0] and "--time=00:30:00" in submitted[0]
    assert "--signal=B:USR1@180" in submitted[0] and "--no-requeue" in submitted[0]
    assert not any(v.startswith("--dependency=") for v in submitted[0])
    before = list(gate.calls)
    with pytest.raises(ValueError, match="already opened/charged"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.calls == before


def test_ambiguous_response_stays_charged_without_retry_or_release(gate):
    gate.fail_submit = True
    with pytest.raises(ValueError, match="ambiguous"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    state = gate.module.load_ledger(gate.module._identity(gate.approval, gate.request, gate.sha))
    assert state["gpu_seconds"] == 1800 and not state["jobs"] and not gate.released
    with pytest.raises(ValueError, match="already opened/charged"):
        gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)


@pytest.mark.parametrize("field,value", [("TimeLimit", "02:00:00"), ("NumCPUs", "16"), ("Requeue", "1"),
    ("Dependency", "afterok:21438102"), ("ReqTRES", "cpu=8,mem=64G,node=1,gres/gpu=2")])
def test_changed_controller_keeps_the_only_job_held(gate, field, value):
    gate.snapshot_overrides[field] = value
    with pytest.raises(ValueError): gate.module.launch(gate.sha, submit=True, expected_commit=gate.commit)
    assert gate.scheduled == {"evaluate": "42001"} and not gate.released


def test_exact_scheduled_job_rejects_training_and_restarts(gate, monkeypatch):
    m = gate.module
    m.launch(gate.sha, submit=True, expected_commit=gate.commit)
    gate.running = True
    monkeypatch.setenv("SLURM_JOB_ID", "42001")
    monkeypatch.setenv("SLURM_SUBMIT_DIR", str(gate.root))
    monkeypatch.setenv("PEANO_JOB_SCRIPT", m.JOBS["evaluate"])
    monkeypatch.setenv("PEANO_HYDRA_PROFILE", m.PROFILE)
    assert m.check_job_reservation(gate.sha, "evaluate")["jobs"] == {"evaluate": "42001"}
    with pytest.raises(ValueError): m.check_job_reservation(gate.sha, "train")
    monkeypatch.setenv("SLURM_RESTART_COUNT", "1")
    with pytest.raises(ValueError, match="restart"): m.check_job_reservation(gate.sha, "evaluate")


def test_absent_real_approval_stops_wrapper_before_ssh(tmp_path):
    marker = tmp_path / "ssh-contacted"
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    ssh = fakebin / "ssh"
    ssh.write_text("#!/bin/sh\n: > '" + str(marker) + "'\nexit 97\n")
    ssh.chmod(0o700)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SLURM_", "SBATCH_"))}
    env["PATH"] = str(fakebin) + os.pathsep + os.environ["PATH"]
    result = subprocess.run(["bash", str(ROOT / "scripts/helios_hydra_frontier_evaluation.sh"),
                             "--approval-sha256", "0" * 64, "--test-only"],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and not marker.exists()


def test_draft_has_no_approval_semantics_or_training_reservation(gate):
    draft = gate.module.request_template()
    assert draft["source_commit"] is draft["semantic_admission"] is None
    assert draft["source_files"] == draft["payloads"] == {}
    assert draft["training_authorized"] is draft["gpu_execution_authorized"] is False
    assert list(draft["reservations"]) == ["evaluate"]
    with pytest.raises(ValueError, match="draft"): gate.module.validate_request(draft)
    draft["existing_remote_artifacts"]["new-frontier"]["adapter_manifest_sha256"] = "0" * 64
    draft["evaluation"]["fixed_search"]["max_depth"] = 500
    assert gate.module.REMOTE_ARTIFACTS["new-frontier"]["adapter_manifest_sha256"] != "0" * 64
    assert gate.module.EVALUATION["fixed_search"]["max_depth"] == 16
