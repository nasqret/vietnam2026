"""Synthetic metadata, origin-worker and inference spies; no actual proofs/models.

The metadata/source/receipt readers, shared deadline, retained unknown prefix
and immutable acceptance arithmetic are exercised without external actions.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from training.peano_hydra import frontier_saved_benchmark_run as run
from training.peano_hydra import frontier_benchmark_run as original
from training.peano_hydra.frontier_benchmark_protocol import BenchmarkReference
from test_peano_hydra_origin_bridge import bundle, mock_worker, authenticate  # noqa: F401
from test_peano_hydra_frontier_benchmark_evaluation import _synthetic_reports
from test_peano_hydra_helios_runtime import central_directories, _environment, GPU_PATHS  # noqa: F401


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if type(value) is bytes else run.canonical(value) + b"\n"
    path.write_bytes(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def test_existing_acceptance_functions_are_reused_without_new_thresholds():
    assert run.acceptance_protocol is original.acceptance_protocol
    assert run._decision is original._decision
    assert run.LIMITS == original.LIMITS
    assert run.acceptance_protocol()["minimum_net_additional_primary_proofs_at_16_calls"] == 4
    assert run._decision(*_synthetic_reports())["status"] == "pilot-gate-met"
    assert run._decision(*_synthetic_reports(gain16=3))["status"] == "pilot-gate-not-met"
    assert run._decision(*_synthetic_reports(gain8=-1))["status"] == "pilot-gate-not-met"


def test_draft_and_wrong_raw_pin_fail_before_touching_origins(tmp_path, monkeypatch):
    descriptor = save(tmp_path / "draft.json", run.request_template())
    monkeypatch.setattr(run, "_read", lambda *_a, **_k: pytest.fail("draft touched package inputs"))
    with pytest.raises(ValueError, match="still a draft"):
        run.check_request(Path(descriptor["path"]), descriptor["sha256"])
    with pytest.raises(ValueError, match="raw SHA differs"):
        run.check_request(Path(descriptor["path"]), "0" * 64)


def test_absent_or_unaccepted_benchmark_blocks_before_origin_receipts(tmp_path, monkeypatch):
    record = run.request_template()
    record["status"] = "ready-for-explicit-resource-approval"
    record["request_sha256"] = run.digest({k: v for k, v in record.items() if k != "request_sha256"})
    descriptor = save(tmp_path / "request.json", record)
    monkeypatch.setattr(run, "_origin", lambda *_a: pytest.fail("unreviewed request touched origin"))
    with pytest.raises(ValueError, match="human/reference review is pending"):
        run.check_request(Path(descriptor["path"]), descriptor["sha256"])
    for key in ("benchmark_manifest", "benchmark_audit", "benchmark_review"):
        record[key] = {"path": run.PACKAGE + "/" + key + ".json", "bytes": 1, "sha256": "a" * 64}
    record["request_sha256"] = run.digest({k: v for k, v in record.items() if k != "request_sha256"})
    descriptor = save(tmp_path / "request.json", record)
    monkeypatch.setattr(run, "_read", lambda *_a, **_k: {})
    monkeypatch.setattr(run, "_training_benchmark_join", lambda _record: None)
    def pending(_self): raise ValueError("pending genuine Lean4.31 and two full cold passes")
    monkeypatch.setattr(BenchmarkReference, "load", pending)
    with pytest.raises(ValueError, match="pending genuine"):
        run.check_request(Path(descriptor["path"]), descriptor["sha256"])


@pytest.mark.parametrize("changed", ["benchmark_manifest", "benchmark_audit"])
def test_replacement_benchmark_cannot_be_accepted_after_the_actual_training(tmp_path, monkeypatch, changed):
    record = run.request_template()
    record["status"] = "ready-for-explicit-resource-approval"
    for key in ("benchmark_manifest", "benchmark_audit", "benchmark_review"):
        record[key] = {"path": run.PACKAGE + "/" + key + ".json", "bytes": 10, "sha256": "a" * 64}
    record["completed_training"]["resource_request"] = {
        "path": run.PACKAGE + "/completed-training-request.json", "bytes": 10,
        "sha256": run.TRAINING_EVIDENCE_PINS["resource_request"]}
    original_training = {"run_id": run.TRAINING_RUN_ID, "source_commit": run.TRAINING_SOURCE_COMMIT,
        "payloads": {path: {"bytes": 10, "sha256": "a" * 64} for path in run.TRAINING_BENCHMARK_INPUTS.values()}}
    reads = []
    def read(descriptor, **_kwargs):
        reads.append(descriptor["path"])
        assert descriptor == record["completed_training"]["resource_request"]
        return deepcopy(original_training)
    monkeypatch.setattr(run, "_read", read)
    run._training_benchmark_join(record)
    record[changed]["sha256"] = "b" * 64
    record["request_sha256"] = run.digest({k: v for k, v in record.items() if k != "request_sha256"})
    descriptor = save(tmp_path / "replacement-request.json", record)
    monkeypatch.setattr(run, "_origin", lambda *_a: pytest.fail("replacement cohort reached an origin"))
    monkeypatch.setattr(BenchmarkReference, "load", lambda _s: pytest.fail("replacement reached expensive review traversal"))
    with pytest.raises(ValueError, match="pretraining-approved selection"):
        run.check_request(Path(descriptor["path"]), descriptor["sha256"])
    assert set(reads) == {record["completed_training"]["resource_request"]["path"]}


def test_local_origin_metadata_never_opens_weights_but_remote_load_still_requires_them(bundle, mock_worker, monkeypatch):
    handle = authenticate(bundle)  # explicitly synthetic original-validator child
    root = bundle.execution
    monkeypatch.setattr(run, "ROOT", root)
    monkeypatch.setattr(run, "REMOTE_PARENT", bundle.adapter_root.parent)
    artifacts = deepcopy(run.launch.REMOTE_ARTIFACTS)
    artifacts[run.evaluation.ROLES[0]] = {"relative_directory": bundle.adapter_root.name,
                                         "adapter_manifest_sha256": bundle.request.adapter_manifest_sha256}
    monkeypatch.setattr(run.launch, "REMOTE_ARTIFACTS", artifacts)
    archive = root / run.ORIGIN_ARCHIVES[run.evaluation.ROLES[0]]
    shutil.copytree(bundle.root, archive)
    def descriptor(name, raw):
        value = save(root / run.PACKAGE / name, raw)
        value["path"] = (run.PACKAGE + "/" + name)
        return value
    record = {"identity": bundle.request.to_dict(), "source_root": archive.relative_to(root).as_posix(),
        "source_manifest": descriptor("source.json", bundle.request.source_manifest.read_bytes()),
        "adapter_manifest": descriptor("adapter-manifest.json", bundle.request.adapter_manifest.read_bytes()),
        "receipt": descriptor("origin-receipt.json", handle.receipt_bytes)}
    actual_fingerprint = run.bridge._Tree.fingerprint
    opened_artifacts = []
    def fingerprint(tree, name, **kwargs):
        if tree.root == bundle.adapter_root: opened_artifacts.append(name)
        return actual_fingerprint(tree, name, **kwargs)
    monkeypatch.setattr(run.bridge._Tree, "fingerprint", fingerprint)
    ref, adapter = run._origin(record, run.evaluation.ROLES[0])
    assert opened_artifacts == [] and adapter == bundle.adapter
    # Metadata admission is not a weaker replacement for byte authentication.
    (bundle.adapter_root / "adapter/adapter_model.safetensors").unlink()
    with pytest.raises(ValueError, match="artifact inventory changed"):
        ref.load()


def test_current_runtime_profile_does_not_relabel_historical_jobs(central_directories):
    from training.peano_hydra.helios_runtime import reviewed_runtime_library_paths
    env = _environment("train")
    env["PEANO_JOB_SCRIPT"] = run.launch.JOBS["evaluate"]
    env["PEANO_HYDRA_PROFILE"] = run.PROFILE
    assert reviewed_runtime_library_paths(env) == GPU_PATHS
    for wrong in (None, "peano-hydra-frontier-v1", "peano-hydra-frontier-training-v1"):
        env["PEANO_HYDRA_PROFILE"] = wrong
        with pytest.raises(ValueError, match="evaluation-only job"):
            reviewed_runtime_library_paths(env)


@pytest.fixture
def execution(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(run, "ROOT", root)
    checked = SimpleNamespace(path=root / "request.json", raw_sha256="b" * 64,
        record={"caller_sources": {}}, baseline=SimpleNamespace(receipt_sha256="c" * 64),
        candidate=SimpleNamespace(receipt_sha256="d" * 64, request=SimpleNamespace(
            adapter_manifest_sha256=run.launch.REMOTE_ARTIFACTS["new-frontier"]["adapter_manifest_sha256"])))
    reservation = {"status": "job-verified", "stage": "evaluate", "job_id": "42001", "jobs": {"evaluate": "42001"},
        "approval_sha256": "e" * 64, "request_file_sha256": "f" * 64,
        "evaluation_request_sha256": checked.raw_sha256, "source_commit": "a" * 40, "allocation_performed": False}
    approval = {"request_file_sha256": "f" * 64}
    resource = {"payloads": {run.launch.INPUTS["evaluation_request"]: {"sha256": checked.raw_sha256}},
                "source_files": {}, "source_commit": "a" * 40}
    monkeypatch.setattr(run.launch, "validate_metadata", lambda _sha: (deepcopy(approval), deepcopy(resource)))
    monkeypatch.setattr(run.launch, "check_job_reservation", lambda *_args: deepcopy(reservation))
    monkeypatch.setattr(run, "check_request", lambda *_args: checked)
    plans = {cohort: SimpleNamespace(proposal={"cohort": cohort}) for cohort in run.COHORTS}
    binds, calls, clock = [], [], [0.0]
    def bind(_checked):
        binds.append(_checked)
        return plans
    monkeypatch.setattr(run, "_bind", bind)
    monkeypatch.setattr(run, "_authorization", lambda plan: {"synthetic_only": plan.proposal["cohort"]})
    monkeypatch.setattr(run.time, "monotonic", lambda: clock[0])
    def infer(plan, **kwargs):
        calls.append(plan.proposal["cohort"])
        kwargs["reservation_check"](kwargs["authorization"])
        clock[0] += 6.0
        return {"synthetic_only": "NOT MODEL OUTPUT OR PROOF EVIDENCE", "cohort": plan.proposal["cohort"]}
    monkeypatch.setattr(run.evaluation, "execute_evaluation", infer)
    return SimpleNamespace(root=root, checked=checked, output=root / run.launch.EVALUATION_OUTPUT,
        binds=binds, calls=calls, clock=clock, reservation=reservation, approval=approval, resource=resource)


def test_no_artifact_binding_or_output_without_separate_approval(execution, monkeypatch):
    def reject(_pin): raise ValueError("separate evaluation approval absent")
    monkeypatch.setattr(run.launch, "validate_metadata", reject)
    with pytest.raises(ValueError, match="approval absent"):
        run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
                    approval_sha256="e" * 64, output=execution.output)
    assert not execution.binds and not execution.calls and not execution.output.exists()


def test_spent_training_job_cannot_be_adopted_for_evaluation(execution, monkeypatch):
    wrong = dict(execution.reservation, job_id=run.TRAINING_JOB_ID, jobs={"evaluate": run.TRAINING_JOB_ID})
    monkeypatch.setattr(run.launch, "check_job_reservation", lambda *_args: wrong)
    with pytest.raises(ValueError, match="spent training"):
        run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
                    approval_sha256="e" * 64, output=execution.output)
    assert not execution.binds and not execution.calls and not execution.output.exists()


def test_shared_deadline_does_not_reset_for_second_cohort(execution):
    with pytest.raises(ValueError, match="shared evaluation deadline"):
        run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
                    approval_sha256="e" * 64, output=execution.output, stop_after_seconds=5)
    assert execution.calls == [run.COHORTS[0]]
    status = json.loads((execution.output / "execution-status.json").read_bytes())
    assert status["uncompleted_outcomes"] == "unknown" and status["automatic_retry"] is status["resume"] is False
    assert (execution.output / (run.COHORTS[0] + ".json")).is_file()
    assert not (execution.output / "run.json").exists()


def test_setup_exhaustion_stops_before_artifact_binding(execution):
    execution.clock[0] = 6.0
    with pytest.raises(ValueError, match="shared evaluation deadline"):
        run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
                    approval_sha256="e" * 64, output=execution.output, stop_after_seconds=5, started=0.0)
    assert execution.binds == execution.calls == []


def test_two_complete_reports_require_independent_replay_before_decision(execution, monkeypatch):
    manifest = run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
        approval_sha256="e" * 64, output=execution.output, stop_after_seconds=30)
    assert execution.calls == list(run.COHORTS)
    assert manifest["status"] == "complete-pending-independent-replay"
    assert manifest["positive_proof_independent_verification_complete"] is False
    assert "decision" not in manifest
    with pytest.raises(ValueError, match="fresh"):
        run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
                    approval_sha256="e" * 64, output=execution.output, stop_after_seconds=30)


def test_saved_reservation_is_evaluation_only_and_independent_of_training_source(execution):
    record = {"reservation": execution.reservation, "resource_approval_file_sha256": "e" * 64,
              "resource_request_file_sha256": "f" * 64}
    run._saved_reservation(execution.checked, record, execution.approval, execution.resource)
    assert execution.resource["source_commit"] != run.TRAINING_SOURCE_COMMIT
    record["reservation"] = dict(execution.reservation, jobs={"train": run.TRAINING_JOB_ID, "evaluate": "42001"})
    with pytest.raises(ValueError, match="inventory"):
        run._saved_reservation(execution.checked, record, execution.approval, execution.resource)


def test_offline_verifier_authenticates_both_reports_before_any_fresh_replay(execution, monkeypatch):
    reports, proofs = _synthetic_reports()
    def infer(plan, **kwargs):
        kwargs["reservation_check"](kwargs["authorization"])
        execution.clock[0] += 1
        return deepcopy(reports[plan.proposal["cohort"]])
    monkeypatch.setattr(run.evaluation, "execute_evaluation", infer)
    run.execute(execution.checked, approval_path=execution.root / run.launch.APPROVAL,
        approval_sha256="e" * 64, output=execution.output, stop_after_seconds=30)
    manifest = execution.output / "run.json"
    pin = hashlib.sha256(manifest.read_bytes()).hexdigest()
    monkeypatch.setattr(run, "caller_sources", lambda: {})
    checks = []
    def verify(plan, result, *, expected_authorization_sha256, replay):
        cohort = plan.proposal["cohort"]
        assert result == reports[cohort]
        assert expected_authorization_sha256 == run.digest(run._authorization(plan))
        checks.append((cohort, replay))
        return deepcopy(proofs[cohort])
    monkeypatch.setattr(run.evaluation, "verify_result", verify)
    result = run.verify_run(execution.checked, execution.output, pin)
    assert checks == [(c, False) for c in run.COHORTS] + [(c, True) for c in run.COHORTS]
    assert result["status"] == "passed" and result["decision"]["status"] == "pilot-gate-met"
    assert result["decision"]["self_training_authorized"] is False
    checks.clear()
    target = execution.output / (run.COHORTS[1] + ".json")
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="artifact changed"):
        run.verify_run(execution.checked, execution.output, pin)
    assert checks == [(run.COHORTS[0], False)]  # zero positive-proof replay after any byte mismatch
