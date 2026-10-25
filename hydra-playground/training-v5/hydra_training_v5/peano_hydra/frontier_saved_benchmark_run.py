"""The unchanged frontier comparison for two already completed training origins.

This separate request cannot retrain, use the spent training ledger, mint a
human review, or turn diagnostic DEV loss into benchmark acceptance. Local
checking reads preserved metadata/source/data, never adapter weights. Exact
artifact byte rechecking occurs through the existing origin bridge on the
server before any model framework is imported.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

from hydra_training_v5.peano_hydra import corrective_workflow as files
from hydra_training_v5.peano_hydra import frontier_benchmark_run as original
from hydra_training_v5.peano_hydra import frontier_evaluation_launch as launch
from hydra_training_v5.peano_hydra import origin_bridge as bridge
from hydra_training_v5.peano_hydra import scaling_admission as admission
from hydra_training_v5.peano_hydra import scaling_evaluation as evaluation
from hydra_training_v5.peano_hydra import scaling_experiment as experiment

ROOT = Path(__file__).absolute().parents[2]
PACKAGE, PROFILE, RUN_ID = launch.PACKAGE, launch.PROFILE, launch.RUN_ID
SCHEMA = launch.EVALUATION_SCHEMA
RUN_SCHEMA = "peano-hydra-frontier-saved-benchmark-run-v1"
COHORTS, LIMITS, MAX_METADATA = original.COHORTS, dict(original.LIMITS), original.MAX_METADATA
require, canonical, digest = bridge._require, bridge._canonical, bridge._digest
acceptance_protocol, _decision = original.acceptance_protocol, original._decision
write_report, _run_file = original.write_report, original._run_file
_fresh_directory, _output_record = original._fresh_directory, original._output_record

TRAINING_RUN_ID = "frontier-training-v1"
TRAINING_JOB_ID = "21438102"
TRAINING_SOURCE_COMMIT = "b08a6b1303d73217f6cc23800ae15e50b17db792"
TRAINING_PREPARATION_SHA = "729b97bf8418cb227d0ef1b1ba350fde5da537e46da4ad55774d8b4ca73517d3"
TRAINING_PACKAGE = "_deploy/hydra-frontier-training-v1"
TRAINING_EVIDENCE_PINS = {
    "resource_request": "02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb",
    "resource_approval": "9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd",
    "launch_receipt": "4515907b8f3c7adf361ce645cba564fb2149baba0b7013bfc883c38e0ab78fb0",
    "terminal_observation": "3b85a4ceb82e3bc816b795efbe296cd31d114363cd11299cb31d73c3c0828cae",
}
TRAINING_BENCHMARK_INPUTS = {
    "benchmark_manifest": TRAINING_PACKAGE + "/benchmark-evidence/benchmark-candidates-build-02/manifest.json",
    "benchmark_audit": TRAINING_PACKAGE + "/benchmark-evidence/benchmark-exposure-audit-01.json",
}
REMOTE_PARENT = Path("/net/scratch/hscra/plgrid/plgnasqret") / launch.REMOTE_PARENT
ORIGIN_ARCHIVES = {"saved-corrected": PACKAGE + "/old-origin-source",
                   "new-frontier": PACKAGE + "/candidate-origin-source"}
ADMITTED_BASE = ORIGIN_ARCHIVES["new-frontier"] + "/" + TRAINING_PACKAGE
ADMITTED_INPUTS = {
    "candidate_readiness": ADMITTED_BASE + "/admitted/candidate-readiness.json",
    "lineage_review": ADMITTED_BASE + "/admitted/lineage-review.json",
    "training_admission": ADMITTED_BASE + "/admitted/training-admission.json",
    "preparation_manifest": ADMITTED_BASE + "/admitted/preparation/manifest.json",
    "preparation_preflight": ADMITTED_BASE + "/admitted/preflight.json",
    "token_preflight": ADMITTED_BASE + "/token-preflight.json",
}
# Existing scaling_evaluation source fingerprints remain unchanged. These
# new caller files have a separate explicit binding, also covered by the new
# resource request's complete frozen execution inventory.
CALLER_SOURCES = frozenset((
    "training/peano_hydra/frontier_saved_benchmark_run.py",
    "training/peano_hydra/frontier_evaluation_launch.py",
    "scripts/eval_peano_hydra_frontier_saved_benchmark.py",
    "scripts/prepare_peano_hydra_frontier_evaluation_launch.py",
    "scripts/run_peano_hydra_frontier_evaluation.sh",
    "scripts/helios_hydra_frontier_evaluation.sh",
    "slurm/peano_hydra_frontier_evaluation.sbatch",
    "training/peano_hydra/helios_runtime.py",
))
REQUEST_FIELDS = frozenset((
    "schema", "status", "profile", "run_id", "benchmark_manifest", "benchmark_audit", "benchmark_review",
    "cohorts", "admitted_inputs", "baseline", "candidate", "completed_training", "acceptance_protocol",
    "existing_remote_artifacts", "caller_sources", "limits", "gpu_execution_authorized", "sealed_benchmark",
    "research_claim_eligible", "request_sha256",
))


def request_template():
    """Only a draft. Missing external review/receipt identities stay null."""
    body = {"schema": SCHEMA, "status": "draft-pending-human-reference-review",
        "profile": PROFILE, "run_id": RUN_ID, "benchmark_manifest": None, "benchmark_audit": None,
        "benchmark_review": None, "cohorts": {key: None for key in COHORTS},
        "admitted_inputs": {key: None for key in ADMITTED_INPUTS}, "baseline": None, "candidate": None,
        "completed_training": {key: None for key in TRAINING_EVIDENCE_PINS}, "acceptance_protocol": None,
        "existing_remote_artifacts": launch.REMOTE_ARTIFACTS, "caller_sources": {}, "limits": dict(LIMITS),
        "gpu_execution_authorized": False, "sealed_benchmark": False, "research_claim_eligible": False,
        "request_sha256": None}
    return json.loads(canonical(body))


def _path(name):
    relative = bridge._relative(name)
    require(relative.startswith(PACKAGE + "/"), "evaluation input must stay in its closed evaluation-only package")
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


def caller_sources():
    return {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name in sorted(CALLER_SOURCES) for raw in (bridge._read(ROOT / name, bridge.MAX_PYTHON_BYTES),)}


def _training_benchmark_join(record):
    """A later accepted review cannot silently replace the pretraining cohort."""
    descriptor = record["completed_training"]["resource_request"]
    require(descriptor["sha256"] == TRAINING_EVIDENCE_PINS["resource_request"],
            "benchmark selection requires the exact original approved training request")
    training = _read(descriptor)
    require(training["source_commit"] == TRAINING_SOURCE_COMMIT and training["run_id"] == TRAINING_RUN_ID,
            "benchmark selection changed its completed training origin")
    for key, original_path in TRAINING_BENCHMARK_INPUTS.items():
        require({k: record[key][k] for k in ("bytes", "sha256")} == training["payloads"].get(original_path),
                "benchmark manifest/audit differs from the exact pretraining-approved selection: " + key)


def _origin(record, role):
    """Validate an anchored completed-origin receipt without opening weights.

    This deliberately does not return an AuthenticatedOrigin or assert current
    artifact-byte validation. OriginReference.load() must run on the existing
    server artifacts before bind_evaluation/inference and offline verification.
    """
    bridge._keys(record, {"identity", "source_root", "source_manifest", "adapter_manifest", "receipt"},
                 "completed origin reference")
    require(record["source_root"] == ORIGIN_ARCHIVES[role], "origin needs its separate preserved source archive")
    source = _read(record["source_manifest"], maximum=bridge.MAX_BUNDLE_MANIFEST_BYTES)
    adapter = _read(record["adapter_manifest"])
    receipt = _read(record["receipt"], maximum=bridge.MAX_RECEIPT_BYTES)
    pinned = launch.REMOTE_ARTIFACTS[role]
    identity = record["identity"]
    require(identity["source_manifest_sha256"] == record["source_manifest"]["sha256"]
            and identity["adapter_manifest_sha256"] == record["adapter_manifest"]["sha256"]
            == pinned["adapter_manifest_sha256"], "saved origin or final adapter was substituted")
    source_root = _path(record["source_root"])
    request = bridge._request(identity, {"source_root": str(source_root),
        "source_manifest": str(_descriptor(record["source_manifest"], maximum=bridge.MAX_BUNDLE_MANIFEST_BYTES)),
        "adapter_manifest": str(REMOTE_PARENT / pinned["relative_directory"] / "manifest.json")})
    bridge._source_record(source)
    require(source["git_commit"] == request.source_commit, "preserved origin source commit differs")
    with bridge._Tree(source_root) as tree, bridge._Tree(ROOT) as support_tree:
        bridge._check_sources(tree, source)
        # Anchored receipt metadata can be reviewed locally; only native data
        # and sources are freshly hashed here. Adapter files are NOT opened.
        prepared_raw = tree.read(identity["preparation_relative_path"] + "/manifest.json", MAX_METADATA)
        require(hashlib.sha256(prepared_raw).hexdigest() == request.preparation_manifest_sha256,
                "original preparation manifest changed")
        prepared = bridge._decode(prepared_raw, MAX_METADATA, "original preparation")
        inputs = receipt["inputs"]
        require(inputs["preparation"]["manifest"] == {"bytes": len(prepared_raw), "sha256": request.preparation_manifest_sha256}
                and inputs["adapter_manifest"] == {k: record["adapter_manifest"][k] for k in ("bytes", "sha256")},
                "origin receipt does not join current preparation/adapter metadata")
        for name, descriptor in inputs["preparation"]["files"].items():
            relative = bridge._relative(identity["preparation_relative_path"] + "/" + name)
            actual, _ = tree.fingerprint(relative, maximum=bridge.MAX_DATA_BYTES)
            require(bridge._small_identity(actual) == descriptor, "original prepared data changed")
        require(inputs["source"]["directory"] == prepared["source"]["directory"], "original native source directory changed")
        for name, descriptor in inputs["source"]["files"].items():
            relative = bridge._relative(inputs["source"]["directory"] + "/" + name)
            actual, _ = tree.fingerprint(relative, maximum=bridge.MAX_DATA_BYTES)
            require(bridge._small_identity(actual) == descriptor, "original native source changed")
        for kind in ("adapter", "tokenizer"):
            artifacts = inputs["artifacts"][kind]
            require(artifacts["identity"] == adapter[kind]
                    and {k: v["sha256"] for k, v in artifacts["files"].items()} == adapter[kind]["files"],
                    "anchored artifact metadata differs from the original manifest")
        bridge._validate_receipt(receipt, request, source, inputs, adapter, bridge._support(support_tree))
        tree.assert_unchanged()
        support_tree.assert_unchanged()
    return evaluation.OriginReference(request, _descriptor(record["receipt"], maximum=bridge.MAX_RECEIPT_BYTES),
                                      record["receipt"]["sha256"]), adapter


def _completed_training(record, adapter, candidate):
    bridge._keys(record, set(TRAINING_EVIDENCE_PINS), "completed training evidence")
    evidence = {}
    for key, pin in TRAINING_EVIDENCE_PINS.items():
        require(record[key]["sha256"] == pin, "completed training evidence was substituted: " + key)
        evidence[key] = _read(record[key])
    request, approval = evidence["resource_request"], evidence["resource_approval"]
    require(request["profile"] == "peano-hydra-frontier-training-v1" and request["run_id"] == TRAINING_RUN_ID
            and approval["approved"] is True and approval["request_file_sha256"] == TRAINING_EVIDENCE_PINS["resource_request"]
            and request["source_commit"] == TRAINING_SOURCE_COMMIT, "the original training approval/source join differs")
    job, deployment = adapter["job"], adapter["deployment"]
    script = "slurm/peano_hydra_frontier_training.sbatch"
    script_sha = request["source_files"][script]["sha256"]
    require(candidate.request.source_commit == TRAINING_SOURCE_COMMIT
            and candidate.request.preparation_manifest_sha256 == TRAINING_PREPARATION_SHA
            and candidate.request.to_dict()["preparation_relative_path"] == TRAINING_PACKAGE + "/admitted/preparation"
            and adapter["run_id"] == TRAINING_RUN_ID and adapter["model_trained"] is True
            and adapter["model"] == launch.MODEL and adapter["preparation_manifest_sha256"] == TRAINING_PREPARATION_SHA
            and job["scheduler"] == "slurm" and job["job_id"] == TRAINING_JOB_ID
            and job["submission"]["job_id"] == TRAINING_JOB_ID and job["submission"]["script"] == script
            and job["submission"]["script_sha256"] == script_sha
            and job["submission"]["git_commit"] == TRAINING_SOURCE_COMMIT and job["submission"]["git_dirty"] == "false"
            and deployment["job_script"] == {"path": script, "sha256": script_sha, "status": "declared"}
            and deployment["source_sync"]["git_commit"] == TRAINING_SOURCE_COMMIT
            and deployment["source_sync"]["git_dirty"] is False,
            "candidate is not the final artifact of completed training job21438102")
    metrics = adapter["metrics"]
    require(metrics["actual_optimizer_steps"] == metrics["expected_optimizer_steps"] == 1597
            and metrics["training_rows"] == 12772 and metrics["development_rows"] == 2096
            and metrics["train"]["epoch"] == 1.0, "candidate training did not complete its exact epoch")
    observation = evidence["terminal_observation"]["observation"]
    accounting = observation["scheduler"]["accounting"]
    rows = [row.split("|") for row in accounting["stdout"].splitlines()]
    top = [row for row in rows if row[0] == TRAINING_JOB_ID]
    require(accounting["returncode"] == 0 and accounting["reason"] == "exited"
            and len(top) == 1 and len(top[0]) == 16 and top[0][2:4] == ["COMPLETED", "0:0"]
            and top[0][5:8] == ["120", "8", "64G"]
            and observation["manifest"]["captured_sha256"] == candidate.request.adapter_manifest_sha256,
            "the separately retained terminal accounting does not show successful training")


def _admitted_and_plans(record, candidate, baseline, benchmark):
    inputs = record["admitted_inputs"]
    bridge._keys(inputs, set(ADMITTED_INPUTS), "completed training admission inputs")
    for key, path in ADMITTED_INPUTS.items():
        require(inputs[key]["path"] == path, "admission must retain its original archived relative path")
    data = {key: _read(value) for key, value in inputs.items()}
    prepared, ready = data["preparation_manifest"], data["candidate_readiness"]
    source = candidate.request.source_root / bridge._relative(prepared["source"]["directory"])
    admitted = admission.admission_identity(source)
    require(admitted["candidate_readiness_sha256"] == inputs["candidate_readiness"]["sha256"]
            and admitted["admission_file_sha256"] == inputs["training_admission"]["sha256"]
            and admitted["review_sha256"] == data["lineage_review"]["review_sha256"]
            and prepared["curriculum_identity"]["review_admission"] == admitted
            and prepared["epoch_sha256"] == benchmark["epoch_sha256"]
            and prepared["source"]["manifest_sha256"] == admitted["source_manifest_sha256"],
            "completed training does not join the actual accepted lineage/preparation/benchmark")
    require(inputs["preparation_manifest"]["sha256"] == candidate.request.preparation_manifest_sha256
            == TRAINING_PREPARATION_SHA, "candidate preparation was substituted")
    preflight, tokens = data["preparation_preflight"], data["token_preflight"]
    require(preflight.get("schema") == "peano-hydra-posttrain-preflight-v2"
            and preflight.get("run_id") == TRAINING_RUN_ID and preflight.get("model_trained") is False
            and preflight.get("cuda_initialized") is False
            and preflight.get("preparation_manifest_sha256") == TRAINING_PREPARATION_SHA
            and preflight.get("training_rows") == 12772 and preflight.get("development_rows") == 2096
            and preflight.get("quarantined_rows") == 0 and preflight.get("expected_optimizer_steps") == 1597,
            "the original production preflight is absent or differs")
    require(tokens.get("schema") == "peano-hydra-frontier-production-token-preflight-v1"
            and tokens.get("status") == "passed" and tokens.get("model_weights_loaded") is False
            and tokens.get("cuda_used") is False and tokens.get("model_trained") is False
            and tokens.get("preparation_manifest_sha256") == TRAINING_PREPARATION_SHA
            and tokens.get("configured_max_length") == 4096, "the original production token preflight is absent or differs")
    old_raw = bridge._read(baseline.request.preparation_directory / "manifest.json", MAX_METADATA)
    require(hashlib.sha256(old_raw).hexdigest() == baseline.request.preparation_manifest_sha256,
            "saved baseline preparation changed")
    old_prepared = bridge._decode(old_raw, MAX_METADATA, "old preparation")
    require(admitted["source_manifest_sha256"] in benchmark["audited_file_sha256"]
            and old_prepared["source"]["manifest_sha256"] in benchmark["audited_file_sha256"],
            "benchmark exposure review omits an actual completed training source")
    bridge._keys(record["cohorts"], set(COHORTS), "fixed cohort plans")
    context = {"benchmark_manifest_sha256": benchmark["manifest_file_sha256"],
        "benchmark_audit_sha256": benchmark["audit_file_sha256"], "benchmark_review_sha256": benchmark["review_file_sha256"],
        "heldout_goals_sha256": benchmark["heldout_goals_sha256"],
        "candidate_readiness_sha256": inputs["candidate_readiness"]["sha256"]}
    pilot = experiment.build_pilot_plan(run_id="frontier-" + ready["profile"] + "-v1", profile=ready["profile"],
        source_manifest_sha256=admitted["source_manifest_sha256"], shard_manifest_sha256=ready["shard_manifest_sha256"],
        lineage_proposal_sha256=admitted["proposal_sha256"], epoch_sha256=prepared["epoch_sha256"],
        authority_sha256=digest(prepared["authority"]), baseline_adapter_manifest_sha256=baseline.request.adapter_manifest_sha256,
        split_rows={k: ready["split_rows"][k] for k in ("train", "dev", "quarantine")})
    for cohort, descriptor in record["cohorts"].items():
        plan = experiment.validate_evaluation_plan(_read(descriptor))
        require(plan["schema"] == experiment.BENCHMARK_EVALUATION_SCHEMA and plan["cohort"] == cohort
                and len(plan["goals"]) == 32 and len(plan["ordered_slots"]) == 128 and plan["max_model_calls_total"] == 1536
                and plan["benchmark_context"] == context and plan["epoch_sha256"] == prepared["epoch_sha256"]
                and plan["authority_sha256"] == digest(prepared["authority"])
                and plan["lineage_proposal_sha256"] == admitted["proposal_sha256"]
                and plan["source_files_sha256"] == admitted["bindings"]["execution_source_files_sha256"]
                and plan["candidate_training_plan_sha256"] == pilot["plan_sha256"]
                and plan["baseline_adapter_manifest_sha256"] == baseline.request.adapter_manifest_sha256,
                "preregistered cohort, admission or fixed comparison budget changed")
        if cohort == COHORTS[0]:
            require(plan["goals"] == benchmark["primary_goals"], "the primary goals were reselected after training")


@dataclass(frozen=True, slots=True)
class CheckedRequest:
    path: Path
    raw_sha256: str
    _json: str
    benchmark: object
    baseline: evaluation.OriginReference
    candidate: evaluation.OriginReference

    @property
    def record(self): return json.loads(self._json)

    def summary(self):
        return {"schema": SCHEMA, "status": "completed-origin-metadata-checked-not-executed",
            "request_file_sha256": self.raw_sha256, "limits": dict(LIMITS),
            "candidate_adapter_manifest_sha256": self.candidate.request.adapter_manifest_sha256,
            "training_job_id": TRAINING_JOB_ID, "model_weights_loaded": False,
            "existing_remote_artifact_bytes_checked": False, "remote_artifact_recheck_required_before_inference": True,
            "training_authorized": False, "gpu_execution_authorized": False, "self_training_authorized": False,
            "human_identity_attested": False, "independent_final_test_ownership_claimed": False}


def check_request(path, expected_raw_sha256):
    """Pure metadata/source/data admission; never opens binary model artifacts."""
    path = bridge._absolute(Path(path))
    bridge._hash(expected_raw_sha256, "external raw evaluation request SHA")
    raw = bridge._read(path, MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_raw_sha256, "evaluation request raw SHA differs")
    record = bridge._decode(raw, MAX_METADATA, "evaluation-only request")
    bridge._keys(record, set(REQUEST_FIELDS), "evaluation-only request")
    require(record["schema"] == SCHEMA and record["status"] == "ready-for-explicit-resource-approval"
            and record["profile"] == PROFILE and record["run_id"] == RUN_ID,
            "evaluation request is still a draft; actual benchmark/reference review is required")
    require(record["request_sha256"] == digest({k: v for k, v in record.items() if k != "request_sha256"})
            and record["limits"] == LIMITS and record["existing_remote_artifacts"] == launch.REMOTE_ARTIFACTS
            and all(record[k] is False for k in ("gpu_execution_authorized", "sealed_benchmark", "research_claim_eligible")),
            "evaluation request changed its exact limits, origins or claims")
    from hydra_training_v5.peano_hydra.frontier_benchmark_protocol import BenchmarkReference
    descriptors = [record[k] for k in ("benchmark_manifest", "benchmark_audit", "benchmark_review")]
    require(all(type(d) is dict for d in descriptors), "external benchmark human/reference review is pending")
    _training_benchmark_join(record)
    for descriptor in descriptors: _read(descriptor)
    benchmark = BenchmarkReference(*[v for desc in descriptors for v in (_descriptor(desc), desc["sha256"])])
    benchmark_record = benchmark.load()
    require(_read(record["acceptance_protocol"]) == acceptance_protocol(), "the original preregistered criteria changed")
    require(record["caller_sources"] == caller_sources(), "new evaluation caller sources changed or are unpinned")
    baseline, _ = _origin(record["baseline"], evaluation.ROLES[0])
    candidate, adapter = _origin(record["candidate"], evaluation.ROLES[1])
    _completed_training(record["completed_training"], adapter, candidate)
    _admitted_and_plans(record, candidate, baseline, benchmark_record)
    require(bridge._read(path, MAX_METADATA) == raw and record["caller_sources"] == caller_sources()
            and benchmark.load() == benchmark_record, "evaluation inputs changed during admission")
    return CheckedRequest(path, expected_raw_sha256, canonical(record).decode(), benchmark, baseline, candidate)


def _bind(checked):
    # This is the FIRST current-artifact byte check. It is mandatory before
    # frameworks, and uses the original bridge without changing its semantics.
    return {cohort: evaluation.bind_evaluation(_descriptor(checked.record["cohorts"][cohort]),
        expected_evaluation_plan_sha256=checked.record["cohorts"][cohort]["sha256"],
        baseline=checked.baseline, candidate=checked.candidate, benchmark_reference=checked.benchmark)
        for cohort in COHORTS}


def _authorization(plan):
    # Only a deterministic narrowing used AFTER the exact new job gate.
    return dict(original._authorization(plan), authorization_id=RUN_ID + "-" + plan.proposal["cohort"])


def _resource_join(checked, resource):
    require(resource["payloads"][launch.INPUTS["evaluation_request"]]["sha256"] == checked.raw_sha256
            and all(resource["source_files"].get(k) == v for k, v in checked.record["caller_sources"].items()),
            "resource request does not pin this exact evaluation request/caller source")


def execute(checked, *, approval_path, approval_sha256, output, stop_after_seconds=1500,
            started=None, stop_requested=None):
    """One fresh scheduled comparison; a shared deadline covers both cohorts."""
    started = time.monotonic() if started is None else started
    require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
            and 0 < stop_after_seconds <= LIMITS["wall_seconds"], "invalid shared evaluation soft deadline")
    require(bridge._absolute(Path(approval_path)) == ROOT / launch.APPROVAL, "resource approval location changed")
    approval, resource = launch.validate_metadata(approval_sha256)
    reservation = launch.check_job_reservation(approval_sha256, "evaluate")
    _resource_join(checked, resource)
    require(reservation["evaluation_request_sha256"] == checked.raw_sha256
            and set(reservation["jobs"]) == {"evaluate"} and reservation["job_id"] != TRAINING_JOB_ID,
            "evaluation must use a fresh independent reservation, never the spent training job")
    require(Path(output).absolute() == ROOT / launch.outputs(reservation["jobs"])["evaluation"],
            "output must belong to the exact approved evaluation job")
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
        boundary()
        plans = _bind(fresh)
        for cohort, plan in plans.items():
            boundary()
            authorization = _authorization(plan)
            def reservation_check(assertion):
                require(assertion == authorization, "narrowed evaluation authorization changed")
                require(launch.check_job_reservation(approval_sha256, "evaluate") == reservation,
                        "approved job identity changed between cohorts")
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
            "candidate_adapter_manifest_sha256": checked.candidate.request.adapter_manifest_sha256,
            "origin_receipt_sha256": {role: ref.receipt_sha256 for role, ref in zip(evaluation.ROLES,
                (checked.baseline, checked.candidate), strict=True)}, "reports": completed,
            "caller_sources": checked.record["caller_sources"],
            "shared_soft_deadline_seconds": stop_after_seconds, "wall_seconds": time.monotonic() - started,
            "limits": dict(LIMITS), "positive_proof_independent_verification_complete": False,
            "research_claim_eligible": False, "sealed_benchmark": False}
        record["run_sha256"] = digest(record)
        files.write_new(out / "run.json", record)
        return record
    except BaseException as error:
        files.write_new(out / "execution-status.json", {"schema": RUN_SCHEMA,
            "status": "interrupted-or-failed-prefix-retained", "request_file_sha256": checked.raw_sha256,
            "completed_cohorts": list(completed), "error_type": type(error).__name__,
            "error": " ".join(str(error).split())[:2048], "uncompleted_outcomes": "unknown",
            "automatic_retry": False, "resume": False, "research_claim_eligible": False})
        raise


def _saved_reservation(checked, record, approval, resource):
    reservation = record["reservation"]
    bridge._keys(reservation, {"status", "stage", "job_id", "jobs", "approval_sha256", "request_file_sha256",
                               "evaluation_request_sha256", "source_commit", "allocation_performed"}, "saved reservation")
    bridge._keys(reservation["jobs"], {"evaluate"}, "evaluation-only job inventory")
    require(type(reservation["job_id"]) is str and re.fullmatch(r"[1-9][0-9]{0,19}", reservation["job_id"])
            and reservation["job_id"] == reservation["jobs"]["evaluate"] != TRAINING_JOB_ID
            and reservation["status"] == "job-verified" and reservation["stage"] == "evaluate"
            and reservation["approval_sha256"] == record["resource_approval_file_sha256"]
            and reservation["request_file_sha256"] == record["resource_request_file_sha256"] == approval["request_file_sha256"]
            and reservation["evaluation_request_sha256"] == checked.raw_sha256
            and reservation["source_commit"] == resource["source_commit"] and reservation["allocation_performed"] is False,
            "saved reservation does not join this independently approved evaluation-only job")


def verify_run(checked, directory, expected_run_sha256):
    """Offline positive-proof replay; same preregistered acceptance arithmetic."""
    evaluation.paired._model_free()
    directory = bridge._absolute(Path(directory))
    bridge._hash(expected_run_sha256, "external raw run manifest SHA")
    raw = bridge._read(directory / "run.json", MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_run_sha256, "saved run raw SHA differs")
    record = bridge._decode(raw, MAX_METADATA, "saved evaluation-only run")
    bridge._keys(record, {"schema", "status", "request_file_sha256", "resource_approval_file_sha256",
        "resource_request_file_sha256", "reservation", "candidate_adapter_manifest_sha256", "origin_receipt_sha256",
        "reports", "caller_sources", "shared_soft_deadline_seconds", "wall_seconds", "limits",
        "positive_proof_independent_verification_complete", "research_claim_eligible", "sealed_benchmark", "run_sha256"},
        "saved evaluation-only run manifest")
    require(record["schema"] == RUN_SCHEMA and record["status"] == "complete-pending-independent-replay"
            and record["request_file_sha256"] == checked.raw_sha256 and record["limits"] == LIMITS
            and record["caller_sources"] == checked.record["caller_sources"] == caller_sources()
            and record["run_sha256"] == digest({k: v for k, v in record.items() if k != "run_sha256"})
            and record["candidate_adapter_manifest_sha256"] == checked.candidate.request.adapter_manifest_sha256
            and record["origin_receipt_sha256"] == {role: ref.receipt_sha256 for role, ref in zip(evaluation.ROLES,
                (checked.baseline, checked.candidate), strict=True)}, "saved request, callers or completed origins changed")
    require(all(record[k] is False for k in ("positive_proof_independent_verification_complete", "research_claim_eligible", "sealed_benchmark"))
            and all(type(record[k]) in (int, float) and math.isfinite(record[k]) and 0 < record[k] <= LIMITS["wall_seconds"]
                    for k in ("wall_seconds", "shared_soft_deadline_seconds")), "saved run changed its time bounds or claims")
    require(check_request(checked.path, checked.raw_sha256).record == checked.record, "evaluation admission changed")
    approval, resource = launch.validate_metadata(record["resource_approval_file_sha256"])
    _resource_join(checked, resource)
    _saved_reservation(checked, record, approval, resource)
    bridge._keys(record["reports"], set(COHORTS), "saved cohort inventory")
    plans = _bind(checked)
    reports, verifications = {}, {}
    for cohort in COHORTS:
        _, reports[cohort] = _run_file(directory, record["reports"][cohort], evaluation.MAX_REPORT_BYTES)
        evaluation.verify_result(plans[cohort], reports[cohort],
            expected_authorization_sha256=digest(_authorization(plans[cohort])), replay=False)
    for cohort in COHORTS:
        verifications[cohort] = evaluation.verify_result(plans[cohort], reports[cohort],
            expected_authorization_sha256=digest(_authorization(plans[cohort])), replay=True)
    require(bridge._read(directory / "run.json", MAX_METADATA) == raw, "run changed during native verification")
    return {"schema": "peano-hydra-frontier-pilot-independent-verification-v1", "status": "passed",
        "run_file_sha256": expected_run_sha256, "request_file_sha256": checked.raw_sha256,
        "cohorts": verifications, "decision": _decision(reports, verifications),
        "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
        "research_claim_eligible": False, "sealed_benchmark": False}
