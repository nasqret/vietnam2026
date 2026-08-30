"""Preregister and run one explicitly approved frontier pilot comparison.

This module cannot create human reviews, allocate a GPU, resume checkpoints,
or turn a public candidate into an independently owned final test. The
resource approval pins the complete pretraining request. Its only deferred
binding is the final adapter from the exact successful training job; that
adapter must pass the preserved-source origin validator before inference.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import uuid

from training.peano_hydra import corrective_workflow as files
from training.peano_hydra import origin_bridge as bridge
from training.peano_hydra import scaling_admission as admission
from training.peano_hydra import scaling_evaluation as evaluation
from training.peano_hydra import scaling_experiment as experiment

ROOT = Path(__file__).absolute().parents[2]
SCHEMA = "peano-hydra-frontier-benchmark-evaluation-request-v1"
RUN_SCHEMA = "peano-hydra-frontier-benchmark-run-v1"
PROTOCOL_SCHEMA = "peano-hydra-frontier-preregistered-acceptance-v1"
DECISION_SCHEMA = "peano-hydra-frontier-pilot-decision-v1"
PACKAGE = "_deploy/hydra-frontier-v1"
COHORTS = ("frontier-heldout-candidate32", "frontier-regression32")
MAX_METADATA = 4 * 1024**2
BASELINE_SHA = "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c"
ADAPTER_OUTPUT = "results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-v1/manifest.json"
LIVE_INPUTS = {
    "candidate_readiness": PACKAGE + "/admitted/candidate-readiness.json",
    "lineage_review": PACKAGE + "/admitted/lineage-review.json",
    "training_admission": PACKAGE + "/admitted/training-admission.json",
    "preparation_manifest": PACKAGE + "/admitted/preparation/manifest.json",
    "preparation_preflight": PACKAGE + "/admitted/preflight.json",
    "token_preflight": PACKAGE + "/token-preflight.json",
}
LIMITS = {"cohorts": 2, "goals_per_cohort": 32, "reserved_goals_not_scored": 32,
          "goal_records": 256, "model_calls": 3072, "wall_seconds": 1800,
          "gpus": 1, "automatic_retry": False, "resume": False}
require, canonical, digest = bridge._require, bridge._canonical, bridge._digest


def acceptance_protocol():
    """Operational pilot thresholds, not statistical or publication claims."""
    body = {
        "schema": PROTOCOL_SCHEMA, "status": "preregistered-before-training",
        "primary_cohort": COHORTS[0], "regression_cohort": COHORTS[1],
        "budgets": [8, 16], "primary_budget": 16,
        "minimum_net_additional_primary_proofs_at_16_calls": 4,
        "maximum_net_primary_proof_loss_at_8_calls": 0,
        "maximum_regression_losses_at_either_budget": 0,
        "maximum_new_to_old_calls_per_proof_ratio_at_16_calls": 1.25,
        "zero_baseline_proofs_cost_rule": "ratio undefined; report totals and retain fixed per-goal call caps",
        "all_256_outcomes_required": True,
        "all_positive_proofs_require_fresh_independent_native_replay": True,
        "incomplete_outcomes": "inconclusive; never count unknown as a failed proof",
        "proof_cost": "report calls, tactic decisions, native proof nodes and wall time; common proofs paired",
        "selection": "final completed epoch only; no best-of-checkpoint or seed selection",
        "primary_budget_reason": "28 of 32 authored teachers use 9 to 13 actions; eight calls is a constrained diagnostic, not a proof-length lower bound",
        "reserve_goals": "all32 excluded from every training phase and not scored by this pilot",
        "self_training": {
            "automatic_start": False, "requires_pilot_gate_met": True,
            "allowed_source": "reviewed TRAIN families only",
            "acceptance": "complete original-goal proof freshly replayed by the native checker",
            "exclude": "all benchmark primary/reserved families, DEV, TEST, partial and failed traces",
            "requires_new_lineage_admission_token_preflight_and_resource_approval": True,
            "conditional_scale_targets": {"proof_roots": 20000, "verified_transitions": 100000},
            "scale_is_not_authorized_by_this_protocol": True,
        },
        "scope": "declared-project-exposure candidate pilot; eight templates share one authored component",
        "independent_final_test_ownership_claimed": False, "sealed_benchmark": False,
        "unknown_base_pretraining_exposure": True, "research_claim_eligible": False,
        "training_authorized": False, "gpu_execution_authorized": False,
    }
    return {**body, "protocol_sha256": digest(body)}


def _path(name):
    relative = bridge._relative(name)
    require(relative.startswith(PACKAGE + "/"), "evaluation input must stay in its closed pilot package")
    return ROOT / relative


def _descriptor(record, *, maximum=MAX_METADATA):
    bridge._keys(record, {"path", "bytes", "sha256"}, "externally anchored file")
    bridge._integer(record["bytes"], maximum, "input bytes", 1)
    bridge._hash(record["sha256"], "raw file SHA")
    return _path(record["path"])


def _read(record, *, maximum=MAX_METADATA):
    path = _descriptor(record, maximum=maximum)
    raw = bridge._read(path, maximum)
    require(len(raw) == record["bytes"] and hashlib.sha256(raw).hexdigest() == record["sha256"],
            "externally anchored package file changed: " + record["path"])
    return bridge._decode(raw, maximum, record["path"])


def _origin(record):
    bridge._keys(record, {"identity", "source_root", "source_manifest", "adapter_manifest", "receipt"},
                 "baseline origin reference")
    source_root = _path(record["source_root"])
    require(record["source_root"] == PACKAGE + "/old-origin-source", "baseline needs its preserved source archive")
    source_manifest, adapter = _descriptor(record["source_manifest"]), _descriptor(record["adapter_manifest"])
    _read(record["source_manifest"])
    _read(record["adapter_manifest"])
    identity = record["identity"]
    require(identity["source_manifest_sha256"] == record["source_manifest"]["sha256"]
            and identity["adapter_manifest_sha256"] == record["adapter_manifest"]["sha256"] == BASELINE_SHA,
            "saved corrected origin or adapter was substituted")
    request = bridge._request(identity, {"source_root": str(source_root), "source_manifest": str(source_manifest),
                                        "adapter_manifest": str(adapter)})
    _read(record["receipt"], maximum=bridge.MAX_RECEIPT_BYTES)
    ref = evaluation.OriginReference(request, _descriptor(record["receipt"], maximum=bridge.MAX_RECEIPT_BYTES),
                                     record["receipt"]["sha256"])
    ref.load()
    return ref


@dataclass(frozen=True, slots=True)
class CheckedRequest:
    path: Path
    raw_sha256: str
    _json: str
    benchmark: object
    baseline: evaluation.OriginReference

    @property
    def record(self): return json.loads(self._json)

    def summary(self):
        return {"schema": SCHEMA, "status": "pretraining-inputs-checked-not-executed",
                "request_file_sha256": self.raw_sha256, "limits": dict(LIMITS),
                "candidate_adapter_binding": "deferred-until-exact-approved-training-completes",
                "human_identity_attested": False, "model_weights_loaded": False,
                "training_authorized": False, "gpu_execution_authorized": False,
                "independent_final_test_ownership_claimed": False}


def check_request(path, expected_raw_sha256):
    """CPU byte/metadata checks; a draft, absent review or absent preflight fails."""
    path = bridge._absolute(Path(path))
    bridge._hash(expected_raw_sha256, "external raw evaluation request SHA")
    raw = bridge._read(path, MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_raw_sha256, "evaluation request raw SHA differs")
    record = bridge._decode(raw, MAX_METADATA, "evaluation request")
    bridge._keys(record, {"schema", "status", "profile", "run_id", "benchmark_manifest", "benchmark_audit",
        "benchmark_review", "cohorts", "admitted_inputs", "baseline", "candidate", "acceptance_protocol",
        "limits", "gpu_execution_authorized", "sealed_benchmark", "research_claim_eligible", "request_sha256"},
        "evaluation request")
    require(record["schema"] == SCHEMA and record["status"] == "ready-for-explicit-resource-approval"
            and record["profile"] == "peano-hydra-frontier-v1" and record["run_id"] == "frontier-v1",
            "evaluation request is still a draft; human/reference review and admitted preflight are required")
    require(record["request_sha256"] == digest({k: v for k, v in record.items() if k != "request_sha256"})
            and record["limits"] == LIMITS
            and all(record[k] is False for k in ("gpu_execution_authorized", "sealed_benchmark", "research_claim_eligible")),
            "evaluation request changed its exact limits or claims")
    # Review is checked before touching old weights or the large source archives.
    from training.peano_hydra.frontier_benchmark_protocol import BenchmarkReference
    descriptors = [record[k] for k in ("benchmark_manifest", "benchmark_audit", "benchmark_review")]
    require(all(type(d) is dict for d in descriptors), "external benchmark human/reference review is pending")
    for descriptor in descriptors: _read(descriptor)
    benchmark = BenchmarkReference(*[value for desc in descriptors for value in (_descriptor(desc), desc["sha256"])])
    checked_benchmark = benchmark.load()
    require(_read(record["acceptance_protocol"]) == acceptance_protocol(), "preregistered pilot criteria changed")
    inputs = record["admitted_inputs"]
    bridge._keys(inputs, set(LIVE_INPUTS), "admitted pilot inputs")
    for key, expected in LIVE_INPUTS.items():
        require(inputs[key]["path"] == expected, "live admitted input location changed")
    data = {key: _read(value) for key, value in inputs.items()}
    identity = admission.admission_identity(ROOT / PACKAGE / "admitted/source")
    require(identity["candidate_readiness_sha256"] == inputs["candidate_readiness"]["sha256"]
            and identity["admission_file_sha256"] == inputs["training_admission"]["sha256"]
            and identity["review_sha256"] == data["lineage_review"]["review_sha256"],
            "exact accepted training admission is missing or changed")
    prepared = data["preparation_manifest"]
    require(prepared["curriculum_identity"]["review_admission"] == identity
            and prepared["source"]["manifest_sha256"] == identity["source_manifest_sha256"]
            and prepared["epoch_sha256"] == checked_benchmark["epoch_sha256"]
            and identity["source_manifest_sha256"] in checked_benchmark["audited_file_sha256"],
            "benchmark audit, admitted preparation and current native source do not join")
    preflight, tokens = data["preparation_preflight"], data["token_preflight"]
    require(preflight.get("schema") == "peano-hydra-posttrain-preflight-v2"
            and preflight.get("model_trained") is False and preflight.get("cuda_initialized") is False
            and preflight.get("preparation_manifest_sha256") == inputs["preparation_manifest"]["sha256"]
            and preflight.get("run_id") == "frontier-v1" and preflight.get("epoch_sha256") == prepared["epoch_sha256"]
            and preflight.get("training_rows") == 12772 and preflight.get("development_rows") == 2096
            and preflight.get("quarantined_rows") == 0 and preflight.get("expected_optimizer_steps") == 1597,
            "saved production preflight does not join the exact CPU-checked pilot preparation")
    require(tokens.get("schema") == "peano-hydra-frontier-production-token-preflight-v1"
            and tokens.get("status") == "passed" and tokens.get("model_weights_loaded") is False
            and tokens.get("preparation_manifest_sha256") == inputs["preparation_manifest"]["sha256"]
            and tokens.get("configured_max_length") == 4096,
            "production token preflight must cover this exact admitted preparation")
    candidate = record["candidate"]
    bridge._keys(candidate, {"source_root", "source_manifest", "source_commit", "preparation_relative_path",
                             "preparation_manifest", "adapter_manifest_path"}, "deferred candidate origin")
    require(candidate["source_root"] == PACKAGE + "/candidate-origin-source"
            and candidate["preparation_relative_path"] == str(Path(LIVE_INPUTS["preparation_manifest"]).parent)
            and candidate["adapter_manifest_path"] == ADAPTER_OUTPUT
            and re.fullmatch(r"[0-9a-f]{40}", candidate["source_commit"]) is not None,
            "candidate must be the exact fresh run with a separate preserved source archive")
    source = _read(candidate["source_manifest"])
    require(source["schema"] == bridge.SOURCE_SCHEMA and source["git_commit"] == candidate["source_commit"],
            "candidate origin has no real pinned source commit")
    with bridge._Tree(_path(candidate["source_root"])) as tree:
        bridge._check_sources(tree, source)
    require(candidate["preparation_manifest"]["path"] == candidate["source_root"] + "/"
            + candidate["preparation_relative_path"] + "/manifest.json"
            and candidate["preparation_manifest"]["sha256"] == inputs["preparation_manifest"]["sha256"]
            and _read(candidate["preparation_manifest"]) == prepared,
            "archived preparation differs from the exact live training input")
    archived_identity = admission.admission_identity(_path(candidate["source_root"]) / prepared["source"]["directory"])
    require(archived_identity == identity, "preserved training admission differs from live admission")
    baseline = _origin(record["baseline"])
    old_prepared, _ = evaluation._read(baseline.request.preparation_directory / "manifest.json",
                                      baseline.request.preparation_manifest_sha256)
    require(old_prepared["source"]["manifest_sha256"] in checked_benchmark["audited_file_sha256"],
            "benchmark audit does not cover the saved corrected training source")
    bridge._keys(record["cohorts"], set(COHORTS), "fixed two-cohort request")
    ready = data["candidate_readiness"]
    expected_context = {
        "benchmark_manifest_sha256": record["benchmark_manifest"]["sha256"],
        "benchmark_audit_sha256": record["benchmark_audit"]["sha256"],
        "benchmark_review_sha256": record["benchmark_review"]["sha256"],
        "heldout_goals_sha256": checked_benchmark["heldout_goals_sha256"],
        "candidate_readiness_sha256": inputs["candidate_readiness"]["sha256"],
    }
    pilot = experiment.build_pilot_plan(run_id="frontier-" + ready["profile"] + "-v1", profile=ready["profile"],
        source_manifest_sha256=identity["source_manifest_sha256"], shard_manifest_sha256=ready["shard_manifest_sha256"],
        lineage_proposal_sha256=identity["proposal_sha256"], epoch_sha256=prepared["epoch_sha256"],
        authority_sha256=digest(prepared["authority"]), baseline_adapter_manifest_sha256=BASELINE_SHA,
        split_rows={k: ready["split_rows"][k] for k in ("train", "dev", "quarantine")})
    for cohort in COHORTS:
        plan = experiment.validate_evaluation_plan(_read(record["cohorts"][cohort]))
        require(plan["schema"] == experiment.BENCHMARK_EVALUATION_SCHEMA and plan["cohort"] == cohort
                and plan["benchmark_context"] == expected_context
                and plan["epoch_sha256"] == prepared["epoch_sha256"]
                and plan["authority_sha256"] == digest(prepared["authority"])
                and plan["baseline_adapter_manifest_sha256"] == BASELINE_SHA
                and plan["lineage_proposal_sha256"] == identity["proposal_sha256"]
                and plan["source_files_sha256"] == identity["bindings"]["execution_source_files_sha256"]
                and plan["candidate_training_plan_sha256"] == pilot["plan_sha256"],
                "factorial plan does not join the exact training and benchmark review")
        if cohort == COHORTS[0]:
            require(plan["goals"] == checked_benchmark["primary_goals"], "primary candidate goals changed")
    require(bridge._read(path, MAX_METADATA) == raw, "request changed during checking")
    return CheckedRequest(path, expected_raw_sha256, canonical(record).decode(), benchmark, baseline)


def _candidate_request(checked, adapter_sha256):
    record = checked.record["candidate"]
    return bridge.OriginRequest(_path(record["source_root"]), _descriptor(record["source_manifest"]),
        record["source_manifest"]["sha256"], record["source_commit"],
        _descriptor(record["preparation_manifest"]).parent, record["preparation_manifest"]["sha256"],
        ROOT / record["adapter_manifest_path"], adapter_sha256, evaluation.AUTHORITY_PRIMITIVE_PROFILE)


def _bind(checked, candidate):
    return {cohort: evaluation.bind_evaluation(_descriptor(checked.record["cohorts"][cohort]),
        expected_evaluation_plan_sha256=checked.record["cohorts"][cohort]["sha256"],
        baseline=checked.baseline, candidate=candidate, benchmark_reference=checked.benchmark) for cohort in COHORTS}


def _authorization(plan):
    # A deterministic narrowing of a verified one-use resource approval. This
    # value is never used until the real launcher's exact job gate succeeds.
    return {"schema": evaluation.AUTHORIZATION_SCHEMA, "authorization_id": "frontier-v1-" + plan.proposal["cohort"],
        "plan_sha256": plan.to_dict()["plan_sha256"],
        "execution_binding_sha256": plan.to_dict()["execution_binding"]["execution_binding_sha256"],
        "model_inference_authorized": True, "gpu_count": 1, "max_wall_seconds": LIMITS["wall_seconds"],
        "max_model_calls": plan.proposal["max_model_calls_total"], "max_goal_records": len(plan.proposal["ordered_slots"]),
        "external_hard_wall_limit_required": True, "training_authorized": False, "upload_authorized": False,
        "new_allocation_authorized": False, "automatic_retry": False, "resume": False,
        "historical_checkpoint_reuse_allowed": False}


def _check_trained_job(checked, adapter, reservation, resource):
    """Join the deferred final artifact to this exact approved predecessor."""
    from training.peano_hydra import frontier_pilot_launch as launch
    job = adapter.get("job", {})
    submission, deployment = job.get("submission", {}), job.get("deployment", {})
    job_script, synced = deployment.get("job_script", {}), deployment.get("source_sync", {})
    expected_script = launch.JOBS["train"]
    expected_script_sha = resource["source_files"][expected_script]["sha256"]
    expected_commit = checked.record["candidate"]["source_commit"]
    require(adapter.get("run_id") == "frontier-v1" and adapter.get("model_trained") is True
            and adapter.get("preparation_manifest_sha256") == checked.record["admitted_inputs"]["preparation_manifest"]["sha256"]
            and job.get("scheduler") == "slurm" and job.get("job_id") == reservation["jobs"]["train"]
            and submission.get("job_id") == reservation["jobs"]["train"]
            and submission.get("script") == expected_script and submission.get("script_sha256") == expected_script_sha
            and submission.get("git_commit") == expected_commit and submission.get("git_dirty") == "false"
            and job_script == {"path": expected_script, "sha256": expected_script_sha, "status": "declared"}
            and synced.get("git_commit") == expected_commit and synced.get("git_dirty") is False,
            "candidate adapter is not the final artifact of the exact approved training predecessor")


def _check_saved_reservation(checked, run, approval, resource):
    reservation = run["reservation"]
    bridge._keys(reservation, {"status", "stage", "job_id", "jobs", "approval_sha256", "request_file_sha256",
                               "evaluation_request_sha256", "source_commit", "allocation_performed"}, "saved reservation")
    bridge._keys(reservation["jobs"], {"train", "evaluate"}, "saved job chain")
    require(all(type(v) is str and re.fullmatch(r"[1-9][0-9]{0,15}", v) for v in reservation["jobs"].values())
            and len(set(reservation["jobs"].values())) == 2
            and reservation["status"] == "job-verified" and reservation["stage"] == "evaluate"
            and reservation["job_id"] == reservation["jobs"]["evaluate"]
            and reservation["approval_sha256"] == run["resource_approval_file_sha256"]
            and reservation["request_file_sha256"] == run["resource_request_file_sha256"] == approval["request_file_sha256"]
            and reservation["evaluation_request_sha256"] == checked.raw_sha256
            and reservation["source_commit"] == resource["source_commit"] == checked.record["candidate"]["source_commit"]
            and reservation["allocation_performed"] is False,
            "saved reservation does not join this exact approved request and two-job chain")
    return reservation


def _fresh_directory(path):
    path = files.guard_output(path)
    fd = files.directory(path.parent)
    try:
        os.mkdir(path.name, mode=0o700, dir_fd=fd)
        os.fsync(fd)
    finally: os.close(fd)
    return path


def _output_record(root, path):
    raw = bridge._read(path, evaluation.MAX_REPORT_BYTES)
    return {"path": path.relative_to(root).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_report(path, value):
    """Fresh atomic report within the evaluator's existing 48 MiB cap.

    The general corrective metadata publisher deliberately keeps its 4 MiB
    bound; a complete factorial report uses its own already declared bound.
    """
    raw = canonical(value) + b"\n"
    require(len(raw) <= evaluation.MAX_REPORT_BYTES, "evaluation report exceeds its retained-byte cap")
    path = files.guard_output(Path(path))
    parent = files.directory(path.parent)
    temporary = ".frontier-report-" + uuid.uuid4().hex
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # link() is atomic and never replaces an existing file.
        os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)


def _run_file(root, descriptor, maximum):
    bridge._keys(descriptor, {"path", "bytes", "sha256"}, "saved run artifact")
    name = bridge._relative(descriptor["path"])
    bridge._integer(descriptor["bytes"], maximum, "saved artifact bytes", 1)
    bridge._hash(descriptor["sha256"], "saved artifact raw SHA")
    path = root / name
    raw = bridge._read(path, maximum)
    require(len(raw) == descriptor["bytes"] and hashlib.sha256(raw).hexdigest() == descriptor["sha256"],
            "saved run artifact changed")
    return path, bridge._decode(raw, maximum, "saved run artifact")


def execute(checked, *, approval_path, approval_sha256, output, stop_after_seconds=1500,
            started=None, stop_requested=None):
    """One scheduled evaluation; the shared deadline includes setup and both cohorts."""
    from training.peano_hydra import frontier_pilot_launch as launch
    started = time.monotonic() if started is None else started
    require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
            and 0 < stop_after_seconds <= LIMITS["wall_seconds"], "invalid shared evaluation soft deadline")
    require(bridge._absolute(Path(approval_path)) == ROOT / launch.APPROVAL, "resource approval location changed")
    approval, resource = launch.validate_metadata(approval_sha256)
    reservation = launch.check_job_reservation(approval_sha256, "evaluate")
    require(resource["payloads"][launch.INPUTS["evaluation_request"]]["sha256"] == checked.raw_sha256
            and reservation["evaluation_request_sha256"] == checked.raw_sha256
            and resource["source_commit"] == checked.record["candidate"]["source_commit"],
            "approved exact job does not authorize this evaluation request")
    require(Path(output).absolute() == ROOT / launch.outputs(reservation["jobs"])["evaluation"],
            "output must belong to the exact approved evaluation job")
    # Parent creation is confined to the fixed results path after approval.
    fd = files.directory(ROOT)
    try:
        for part in ("results", "peano-hydra", "evaluations"):
            try: os.mkdir(part, 0o700, dir_fd=fd)
            except FileExistsError: pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
    finally: os.close(fd)
    out = _fresh_directory(Path(output))
    completed = {}
    def stopping():
        return time.monotonic() - started >= stop_after_seconds or (stop_requested is not None and stop_requested())
    def boundary():
        require(not stopping(), "shared evaluation deadline/stop reached; unstarted outcomes remain unknown")
    try:
        boundary()
        fresh = check_request(checked.path, checked.raw_sha256)
        require(fresh.record == checked.record, "evaluation input changed after reservation")
        adapter_path = ROOT / ADAPTER_OUTPUT
        adapter_raw = bridge._read(adapter_path, MAX_METADATA)
        adapter_sha = hashlib.sha256(adapter_raw).hexdigest()
        require(adapter_sha != BASELINE_SHA, "new candidate must not overwrite or substitute the saved adapter")
        _check_trained_job(checked, bridge._decode(adapter_raw, MAX_METADATA, "candidate adapter"), reservation, resource)
        boundary()
        origin = bridge.authenticate_origin(_candidate_request(checked, adapter_sha), python=Path(sys.executable),
                                             runtime_library_paths=files.runtime_libraries())
        boundary()
        origin_dir = _fresh_directory(out / "origin")
        receipt_path = origin_dir / "receipt.json"
        files.write_new(receipt_path, origin.receipt_bytes, raw=True)
        candidate = evaluation.OriginReference(origin.request, receipt_path, origin.receipt_sha256)
        plans = _bind(checked, candidate)
        for cohort, plan in plans.items():
            boundary()
            authorization = _authorization(plan)
            def reservation_check(assertion):
                require(assertion == authorization, "narrowed evaluation authorization changed")
                current = launch.check_job_reservation(approval_sha256, "evaluate")
                require(current == reservation, "approved job identity changed between cohorts")
                boundary()
            result = evaluation.execute_evaluation(plan, authorization=authorization,
                expected_authorization_sha256=digest(authorization), checkpoint_directory=out / (cohort + "-checkpoint"),
                reservation_check=reservation_check, stop_requested=stopping)
            target = out / (cohort + ".json")
            write_report(target, result)
            completed[cohort] = _output_record(out, target)
        record = {"schema": RUN_SCHEMA, "status": "complete-pending-independent-replay",
            "request_file_sha256": checked.raw_sha256, "resource_approval_file_sha256": approval_sha256,
            "resource_request_file_sha256": approval["request_file_sha256"], "reservation": reservation,
            "candidate_adapter_manifest_sha256": adapter_sha,
            "candidate_origin_receipt": _output_record(out, receipt_path), "reports": completed,
            "shared_soft_deadline_seconds": stop_after_seconds, "wall_seconds": time.monotonic() - started,
            "limits": dict(LIMITS), "positive_proof_independent_verification_complete": False,
            "research_claim_eligible": False, "sealed_benchmark": False}
        record["run_sha256"] = digest(record)
        files.write_new(out / "run.json", record)
        return record
    except BaseException as error:
        # Never retry, resume, erase the prefix, or fabricate remaining rows.
        status = {"schema": RUN_SCHEMA, "status": "interrupted-or-failed-prefix-retained",
            "request_file_sha256": checked.raw_sha256, "completed_cohorts": list(completed),
            "error_type": type(error).__name__, "error": " ".join(str(error).split())[:2048],
            "uncompleted_outcomes": "unknown", "automatic_retry": False, "resume": False,
            "research_claim_eligible": False}
        files.write_new(out / "execution-status.json", status)
        raise


def _decision(reports, verifications):
    """Derive the preregistered gate only from the freshly verified paired reports."""
    require(set(reports) == set(verifications) == set(COHORTS), "both complete cohorts are required")
    outcomes, checks = {}, {}
    for cohort in COHORTS:
        result, proof_check = reports[cohort], verifications[cohort]
        require(proof_check["status"] == "passed" and proof_check["verification_complete"] is True
                and proof_check["proof_replay_performed"] is True
                and proof_check["evaluation_sha256"] == result["evaluation_sha256"],
                "pilot decisions require fresh native replay of every complete report")
        plan = result["plan"]["evaluation_plan"]
        metric = result["metrics"]
        require(plan["cohort"] == cohort and metric["all_records_present"] is True
                and metric["explicit_unknown_records"] == 0, "unknown outcomes make the pilot inconclusive")
        outcomes[cohort] = {(r["role"], r["max_model_calls"], r["goal"]): row
                           for r, row in zip(plan["ordered_slots"], result["rows"], strict=True)}
        checks[cohort] = {item["max_model_calls"]: item for item in metric["matched_comparisons"]}
    primary = checks[COHORTS[0]]
    gains8 = len(primary[8]["reported_gains"]) - len(primary[8]["reported_losses"])
    gains16 = len(primary[16]["reported_gains"]) - len(primary[16]["reported_losses"])
    regression_losses = {budget: len(checks[COHORTS[1]][budget]["reported_losses"]) for budget in (8, 16)}
    costs = {}
    for role in evaluation.ROLES:
        rows = [row for (who, budget, _), row in outcomes[COHORTS[0]].items() if who == role and budget == 16]
        count, calls = sum(r["kernel_checked"] for r in rows), sum(r["model_generate_calls"] for r in rows)
        costs[role] = {"proofs": count, "model_calls": calls, "calls_per_proof": calls / count if count else None}
    old, new = (costs[role]["calls_per_proof"] for role in evaluation.ROLES)
    cost_ok = old is None or new is not None and new <= 1.25 * old
    criteria = {"primary_net_gain_at_16_calls": gains16 >= 4, "no_net_primary_loss_at_8_calls": gains8 >= 0,
                "no_regression_goal_losses": all(n == 0 for n in regression_losses.values()), "cost_ratio": cost_ok}
    body = {"schema": DECISION_SCHEMA, "status": "pilot-gate-met" if all(criteria.values()) else "pilot-gate-not-met",
        "protocol_sha256": acceptance_protocol()["protocol_sha256"], "criteria": criteria,
        "primary_net_gains": {"8": gains8, "16": gains16}, "regression_losses": regression_losses,
        "primary_16_call_cost": costs,
        "verification_sha256": {k: digest(v) for k, v in verifications.items()},
        "self_training_authorized": False, "scaling_authorized": False,
        "next_step": "separate TRAIN-only native admission/preflight/resource review" if all(criteria.values())
                     else "inspect failures; preserve benchmark exclusions; no automatic retry or scale-up",
        "research_claim_eligible": False, "sealed_benchmark": False}
    return {**body, "decision_sha256": digest(body)}


def verify_run(checked, directory, expected_run_sha256):
    """Offline verification; never load model frameworks or submit jobs."""
    evaluation.paired._model_free()
    directory = bridge._absolute(Path(directory))
    bridge._hash(expected_run_sha256, "external raw run manifest SHA")
    raw = bridge._read(directory / "run.json", MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_run_sha256, "saved run raw SHA differs")
    run = bridge._decode(raw, MAX_METADATA, "saved run")
    bridge._keys(run, {"schema", "status", "request_file_sha256", "resource_approval_file_sha256",
        "resource_request_file_sha256", "reservation", "candidate_adapter_manifest_sha256", "candidate_origin_receipt",
        "reports", "shared_soft_deadline_seconds", "wall_seconds", "limits", "positive_proof_independent_verification_complete",
        "research_claim_eligible", "sealed_benchmark", "run_sha256"}, "saved run manifest")
    require(run["schema"] == RUN_SCHEMA and run["status"] == "complete-pending-independent-replay"
            and run["request_file_sha256"] == checked.raw_sha256 and run["limits"] == LIMITS
            and run["run_sha256"] == digest({k: v for k, v in run.items() if k != "run_sha256"}),
            "saved run changed its request, completion or resource limits")
    require(all(run[k] is False for k in ("positive_proof_independent_verification_complete", "research_claim_eligible", "sealed_benchmark"))
            and all(type(run[k]) in (int, float) and math.isfinite(run[k]) and 0 < run[k] <= LIMITS["wall_seconds"]
                    for k in ("wall_seconds", "shared_soft_deadline_seconds")), "saved run changed its time bounds or claims")
    from training.peano_hydra import frontier_pilot_launch as launch
    approval, resource = launch.validate_metadata(run["resource_approval_file_sha256"])
    require(resource["payloads"][launch.INPUTS["evaluation_request"]]["sha256"] == checked.raw_sha256,
            "saved approval does not pin this evaluation request")
    reservation = _check_saved_reservation(checked, run, approval, resource)
    adapter_raw = bridge._read(ROOT / ADAPTER_OUTPUT, MAX_METADATA)
    require(hashlib.sha256(adapter_raw).hexdigest() == run["candidate_adapter_manifest_sha256"],
            "saved candidate adapter changed")
    _check_trained_job(checked, bridge._decode(adapter_raw, MAX_METADATA, "candidate adapter"), reservation, resource)
    bridge._keys(run["reports"], set(COHORTS), "saved cohort inventory")
    receipt_path, _ = _run_file(directory, run["candidate_origin_receipt"], bridge.MAX_RECEIPT_BYTES)
    candidate = evaluation.OriginReference(_candidate_request(checked, run["candidate_adapter_manifest_sha256"]),
        receipt_path, run["candidate_origin_receipt"]["sha256"])
    plans = _bind(checked, candidate)
    reports, verifications = {}, {}
    # Authenticate all report metadata before starting even one native replay.
    for cohort in COHORTS:
        _, reports[cohort] = _run_file(directory, run["reports"][cohort], evaluation.MAX_REPORT_BYTES)
        evaluation.verify_result(plans[cohort], reports[cohort],
            expected_authorization_sha256=digest(_authorization(plans[cohort])), replay=False)
    for cohort in COHORTS:
        verifications[cohort] = evaluation.verify_result(plans[cohort], reports[cohort],
            expected_authorization_sha256=digest(_authorization(plans[cohort])), replay=True)
    require(bridge._read(directory / "run.json", MAX_METADATA) == raw, "run manifest changed during native verification")
    return {"schema": "peano-hydra-frontier-pilot-independent-verification-v1", "status": "passed",
        "run_file_sha256": expected_run_sha256, "request_file_sha256": checked.raw_sha256,
        "cohorts": verifications, "decision": _decision(reports, verifications),
        "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
        "research_claim_eligible": False, "sealed_benchmark": False}
