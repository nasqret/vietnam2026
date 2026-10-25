"""Exact exposed DEV comparison, separate from the held-out benchmark pilot.

Reuses original OriginReference, bind_evaluation, execute_evaluation and
verify_result without weakening their validation. This diagnostic cannot earn
pilot acceptance or self-training readiness. No train/model upload/retry API.
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
from hydra_training_v5.peano_hydra import frontier_benchmark_run as report_files
from hydra_training_v5.peano_hydra import frontier_diagnostic_launch as launch
from hydra_training_v5.peano_hydra import origin_bridge as bridge
from hydra_training_v5.peano_hydra import scaling_admission as admission
from hydra_training_v5.peano_hydra import scaling_evaluation as evaluation
from hydra_training_v5.peano_hydra import scaling_experiment as experiment

ROOT = Path(__file__).absolute().parents[2]
PACKAGE, PROFILE, RUN_ID = launch.PACKAGE, launch.PROFILE, launch.RUN_ID
SCHEMA = launch.EVALUATION_SCHEMA
RUN_SCHEMA = "peano-hydra-frontier-dev-diagnostic-run-v1"
VERIFY_SCHEMA = "peano-hydra-frontier-dev-diagnostic-verification-v1"
LIMITS, MAX_METADATA = dict(launch.EVALUATION), 4 * 1024**2
require, canonical, digest = bridge._require, bridge._canonical, bridge._digest
write_report, _run_file = report_files.write_report, report_files._run_file
_fresh_directory, _output_record = report_files._fresh_directory, report_files._output_record
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
REMOTE_PARENT = Path(launch.REMOTE_PROJECT)
CLAIMS = {"gpu_execution_authorized": False, "sealed_benchmark": False, "research_claim_eligible": False,
          "pilot_acceptance_eligible": False, "benchmark_acceptance_eligible": False,
          "self_training_readiness_eligible": False, "heldout_or_reserved_goals_scored": False}
CALLER_SOURCES = frozenset((
    "training/peano_hydra/frontier_diagnostic_run.py",
    "training/peano_hydra/frontier_diagnostic_launch.py",
    "scripts/eval_peano_hydra_frontier_diagnostic.py",
    "scripts/prepare_peano_hydra_frontier_diagnostic_launch.py",
    "scripts/run_peano_hydra_frontier_diagnostic.sh",
    "scripts/helios_hydra_frontier_diagnostic.sh",
    "slurm/peano_hydra_frontier_diagnostic.sbatch",
    "training/peano_hydra/helios_runtime.py",
))
REQUEST_FIELDS = frozenset((
    "schema", "status", "profile", "run_id", "evaluation_plan", "baseline", "candidate",
    "completed_training", "existing_remote_artifacts", "existing_read_only_sources", "caller_sources",
    "limits", "request_sha256", *CLAIMS,
))


def request_template():
    """Nonauthorizing draft; missing original receipt identities remain null."""
    body = {"schema": SCHEMA, "status": "draft-pending-original-origin-receipts",
        "profile": PROFILE, "run_id": RUN_ID, "evaluation_plan": None, "baseline": None, "candidate": None,
        "completed_training": {key: None for key in TRAINING_EVIDENCE_PINS},
        "existing_remote_artifacts": launch.REMOTE_ARTIFACTS,
        "existing_read_only_sources": launch.EXTERNAL_SOURCES,
        "caller_sources": {}, "limits": dict(LIMITS), "request_sha256": None, **CLAIMS}
    return json.loads(canonical(body))


def _path(name):
    relative = bridge._relative(name)
    require(relative.startswith(PACKAGE + "/"), "diagnostic metadata must stay in its closed input package")
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


def guard_output(path, *, extra=()):
    return files.guard_output(path, protected=launch.output_protections(extra=extra))


def _plan(descriptor):
    require(type(descriptor) is dict
            and {k: descriptor.get(k) for k in ("bytes", "sha256")}
            == {k: launch.DEV_PLAN[k] for k in ("bytes", "sha256")},
            "only the exact preregistered exposed DEV plan is eligible; no held-out or reserve replacement")
    plan = experiment.validate_evaluation_plan(_read(descriptor))
    require(plan["schema"] == experiment.EVALUATION_SCHEMA and plan["cohort"] == LIMITS["cohort"]
            and plan["plan_sha256"] == launch.DEV_PLAN["plan_sha256"]
            and plan["roles"] == list(evaluation.ROLES) and plan["budgets"] == [8, 16]
            and len(plan["goals"]) == 32 and len(plan["ordered_slots"]) == 128
            and plan["max_model_calls_total"] == 1536,
            "the diagnostic cannot expand or relabel the frozen DEV factorial plan")
    return plan


def _origin(record, role):
    """Validate an anchored completed-origin receipt without opening weights.

    This deliberately does not return an AuthenticatedOrigin or assert current
    artifact-byte validation. OriginReference.load() must run on the existing
    server artifacts before bind_evaluation/inference and offline verification.
    """
    bridge._keys(record, {"identity", "source_locations", "source_manifest", "adapter_manifest", "receipt"},
                 "completed origin reference")
    require(record["source_locations"] == launch.EXTERNAL_SOURCES[role],
            "origin needs its exact declared read-only external source locations")
    source = _read(record["source_manifest"], maximum=bridge.MAX_BUNDLE_MANIFEST_BYTES)
    adapter = _read(record["adapter_manifest"])
    receipt = _read(record["receipt"], maximum=bridge.MAX_RECEIPT_BYTES)
    pinned = launch.REMOTE_ARTIFACTS[role]
    identity = record["identity"]
    require(identity["source_manifest_sha256"] == record["source_manifest"]["sha256"]
            and identity["adapter_manifest_sha256"] == record["adapter_manifest"]["sha256"]
            == pinned["adapter_manifest_sha256"], "saved origin or final adapter was substituted")
    source_pin = launch.EXTERNAL_SOURCES[role]
    require(identity["source_commit"] == source_pin["source_commit"]
            and identity["source_manifest_sha256"] == source_pin["source_manifest_sha256"],
            "the original preserved source identity was replaced")
    location = "remote" if ROOT == Path(launch.REMOTE_PROJECT) / launch.REMOTE_CHILD else "local"
    require(not os.environ.get("SLURM_JOB_ID") or location == "remote",
            "a scheduled diagnostic must use its fixed remote source locations")
    source_root = bridge._absolute(Path(source_pin[location]))
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


def _admitted_plan(record, candidate, adapter, plan):
    """Join the exact DEV bytes to the original preparation and accepted lineage."""
    request = candidate.request
    with bridge._Tree(request.source_root) as tree:
        prep_relative = request.to_dict()["preparation_relative_path"] + "/manifest.json"
        raw = tree.read(prep_relative, MAX_METADATA)
        require(hashlib.sha256(raw).hexdigest() == request.preparation_manifest_sha256 == TRAINING_PREPARATION_SHA,
                "candidate preparation identity changed")
        prepared = bridge._decode(raw, MAX_METADATA, "original candidate preparation")
        source_relative = bridge._relative(prepared["source"]["directory"])
        source_raw = tree.read(source_relative + "/manifest.json", MAX_METADATA)
        require(hashlib.sha256(source_raw).hexdigest() == prepared["source"]["manifest_sha256"],
                "original candidate native source manifest changed")
        source = bridge._decode(source_raw, MAX_METADATA, "original candidate source")
        ready_relative = (Path(source_relative).parent / "candidate-readiness.json").as_posix()
        ready_raw = tree.read(ready_relative, MAX_METADATA)
        ready = bridge._decode(ready_raw, MAX_METADATA, "original candidate readiness")
        admitted = admission.admission_identity(request.source_root / source_relative)
        identity = prepared["curriculum_identity"]
        require(identity == adapter["curriculum_identity"]
                and identity["review_admission"] == admitted
                and identity["source_schema"] == admission.SOURCE_SCHEMA
                and identity["projection_policy"] == admission.PROJECTION_POLICY
                and source["schema"] == admission.SOURCE_SCHEMA
                and admitted["candidate_readiness_sha256"] == hashlib.sha256(ready_raw).hexdigest(),
                "diagnostic candidate lost its original accepted admission")
        require(ready["files"]["evaluation-plan.json"]
                == {k: record["evaluation_plan"][k] for k in ("bytes", "sha256")}
                and plan["epoch_sha256"] == prepared["epoch_sha256"] == admitted["bindings"]["epoch_sha256"]
                and plan["authority_sha256"] == digest(prepared["authority"]) == admitted["bindings"]["authority_sha256"]
                and plan["lineage_proposal_sha256"] == admitted["proposal_sha256"]
                and plan["source_files_sha256"] == digest(ready["source_files"])
                == admitted["bindings"]["execution_source_files_sha256"],
                "DEV selection, native epoch, authority or admitted source changed")
        routes = {item["name"]: item for item in source["composition"]["plan"]["routes"] if item["split"] == "dev"}
        for goal in plan["goals"]:
            require(goal["name"] in routes and goal == {k: routes[goal["name"]][k] for k in goal}
                    and goal["name"] in prepared["splits"]["dev"]["theorems"]
                    and goal["lineage_sha256"] not in prepared["splits"]["train"]["lineages"],
                    "diagnostic goal is not its original reviewed DEV route")
        tree.assert_unchanged()


@dataclass(frozen=True, slots=True)
class CheckedRequest:
    path: Path
    raw_sha256: str
    _json: str
    baseline: evaluation.OriginReference
    candidate: evaluation.OriginReference

    @property
    def record(self): return json.loads(self._json)

    def summary(self):
        return {"schema": SCHEMA, "status": "completed-origin-metadata-checked-not-executed",
            "request_file_sha256": self.raw_sha256, "limits": dict(LIMITS),
            "candidate_adapter_manifest_sha256": self.candidate.request.adapter_manifest_sha256,
            "training_job_id": TRAINING_JOB_ID, "model_weights_loaded": False,
            "existing_remote_artifact_bytes_checked": False,
            "external_source_and_preparation_bytes_checked": True,
            "remote_artifact_recheck_required_before_inference": True,
            "external_sources_or_model_weights_in_transfer_payload": False,
            "training_authorized": False, "self_training_authorized": False,
            "human_identity_attested": False, "independent_final_test_ownership_claimed": False, **CLAIMS}


def check_request(path, expected_raw_sha256):
    """Original receipt/source/data metadata checks; never opens binary model files."""
    path = bridge._absolute(Path(path))
    bridge._hash(expected_raw_sha256, "external raw diagnostic request SHA")
    raw = bridge._read(path, MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_raw_sha256, "diagnostic request raw SHA differs")
    record = bridge._decode(raw, MAX_METADATA, "diagnostic-only request")
    bridge._keys(record, set(REQUEST_FIELDS), "diagnostic-only request")
    require(record["schema"] == SCHEMA and record["status"] == "ready-for-explicit-resource-approval"
            and record["profile"] == PROFILE and record["run_id"] == RUN_ID,
            "diagnostic request is still a draft; both original origin receipts are required")
    require(record["request_sha256"] == digest({k: v for k, v in record.items() if k != "request_sha256"})
            and record["limits"] == LIMITS and record["existing_remote_artifacts"] == launch.REMOTE_ARTIFACTS
            and record["existing_read_only_sources"] == launch.EXTERNAL_SOURCES
            and all(record[k] is False for k in CLAIMS),
            "diagnostic request changed its exact resources, external origins or claims")
    plan = _plan(record["evaluation_plan"])
    require(record["caller_sources"] == caller_sources(), "diagnostic caller sources changed or are unpinned")
    require(type(record["baseline"]) is dict and type(record["candidate"]) is dict,
            "both original origin receipts remain required")
    baseline, _ = _origin(record["baseline"], evaluation.ROLES[0])
    candidate, adapter = _origin(record["candidate"], evaluation.ROLES[1])
    _completed_training(record["completed_training"], adapter, candidate)
    _admitted_plan(record, candidate, adapter, plan)
    require(bridge._read(path, MAX_METADATA) == raw and record["caller_sources"] == caller_sources()
            and _plan(record["evaluation_plan"]) == plan, "diagnostic inputs changed during admission")
    return CheckedRequest(path, expected_raw_sha256, canonical(record).decode(), baseline, candidate)


def _bind(checked):
    """Original full artifact rehash and DEV binding; no benchmark reference."""
    descriptor = checked.record["evaluation_plan"]
    return evaluation.bind_evaluation(_descriptor(descriptor), expected_evaluation_plan_sha256=descriptor["sha256"],
        baseline=checked.baseline, candidate=checked.candidate)


def _authorization(plan):
    """Deterministic narrowing AFTER resource approval and exact scheduler gate."""
    return {"schema": evaluation.AUTHORIZATION_SCHEMA, "authorization_id": RUN_ID,
        "plan_sha256": plan.to_dict()["plan_sha256"],
        "execution_binding_sha256": plan.to_dict()["execution_binding"]["execution_binding_sha256"],
        "model_inference_authorized": True, "gpu_count": 1, "max_wall_seconds": 720,
        "max_model_calls": plan.proposal["max_model_calls_total"],
        "max_goal_records": len(plan.proposal["ordered_slots"]), "external_hard_wall_limit_required": True,
        "training_authorized": False, "upload_authorized": False, "new_allocation_authorized": False,
        "automatic_retry": False, "resume": False, "historical_checkpoint_reuse_allowed": False}


def _resource_join(checked, resource):
    require(resource["payloads"][launch.INPUTS["evaluation_request"]]["sha256"] == checked.raw_sha256
            and resource["existing_read_only_sources"] == launch.EXTERNAL_SOURCES
            and all(resource["source_files"].get(k) == v for k, v in checked.record["caller_sources"].items()),
            "resource request does not pin this exact diagnostic request/caller/source location")


def _reservation_identity(record):
    return {k: v for k, v in record.items() if k != "allocation_elapsed_seconds"}


def execute(checked, *, approval_path, approval_sha256, output, stop_after_seconds=720,
            started=None, stop_requested=None, progress=None):
    """One approved fresh diagnostic, with allocation-wide (not inference-only) deadline."""
    started = time.monotonic() if started is None else started
    require(type(started) in (int, float) and math.isfinite(started) and started <= time.monotonic(),
            "invalid monotonic process start")
    require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
            and 0 < stop_after_seconds <= 720, "invalid whole-allocation soft deadline")
    require(stop_requested is None or callable(stop_requested), "invalid stop hook")
    require(bridge._absolute(Path(approval_path)) == ROOT / launch.APPROVAL, "resource approval location changed")
    progress = progress or evaluation.cp.Progress()
    progress.emit("diagnostic-reservation-validation-start")
    approval, resource = launch.validate_metadata(approval_sha256)
    before_reservation = time.monotonic()
    reservation = launch.check_job_reservation(approval_sha256, "evaluate")
    elapsed = reservation.get("allocation_elapsed_seconds")
    require(type(elapsed) is int and 0 <= elapsed < 900, "scheduler elapsed allocation time is required")
    # Scheduler elapsed time is whole seconds. Count the fractional second
    # conservatively, and anchor before the metadata roundtrip (never later).
    allocation_started = min(started, before_reservation - elapsed - 1.0)
    _resource_join(checked, resource)
    require(reservation["evaluation_request_sha256"] == checked.raw_sha256
            and set(reservation["jobs"]) == {"evaluate"} and reservation["job_id"] != TRAINING_JOB_ID,
            "diagnostic needs its fresh independent reservation, never the spent training job")
    require(Path(output).absolute() == ROOT / launch.outputs(reservation["jobs"])["evaluation"],
            "output must belong to the exact approved diagnostic job")
    progress.emit("diagnostic-reservation-validation-complete")
    def stopping():
        return (time.monotonic() - allocation_started >= stop_after_seconds
                or (stop_requested is not None and stop_requested()))
    def boundary():
        require(not stopping(), "whole-allocation diagnostic deadline/stop reached; unstarted outcomes remain unknown")
    boundary()
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
    try:
        boundary()
        progress.emit("diagnostic-input-revalidation-start")
        fresh = check_request(checked.path, checked.raw_sha256)
        require(fresh.record == checked.record, "diagnostic input changed after reservation")
        progress.emit("diagnostic-input-revalidation-complete")
        boundary()
        progress.emit("diagnostic-origin-binding-start")
        plan = _bind(fresh)
        progress.emit("diagnostic-origin-binding-complete")
        boundary()
        authorization = _authorization(plan)
        def reservation_check(assertion):
            require(assertion == authorization, "narrowed diagnostic authorization changed")
            current = launch.check_job_reservation(approval_sha256, "evaluate")
            require(_reservation_identity(current) == _reservation_identity(reservation),
                    "approved job identity changed before model loading")
            require(type(current.get("allocation_elapsed_seconds")) is int
                    and current["allocation_elapsed_seconds"] + 1 < stop_after_seconds,
                    "scheduler reports the diagnostic allocation deadline reached")
            boundary()
        result = evaluation.execute_evaluation(plan, authorization=authorization,
            expected_authorization_sha256=digest(authorization), checkpoint_directory=out / "checkpoint",
            reservation_check=reservation_check, stop_requested=stopping, progress=progress)
        target = out / "diagnostic.json"
        write_report(target, result)
        record = {"schema": RUN_SCHEMA, "status": "complete-pending-independent-replay",
            "request_file_sha256": checked.raw_sha256, "resource_approval_file_sha256": approval_sha256,
            "resource_request_file_sha256": approval["request_file_sha256"], "reservation": reservation,
            "candidate_adapter_manifest_sha256": checked.candidate.request.adapter_manifest_sha256,
            "origin_receipt_sha256": {role: ref.receipt_sha256 for role, ref in zip(evaluation.ROLES,
                (checked.baseline, checked.candidate), strict=True)}, "report": _output_record(out, target),
            "caller_sources": checked.record["caller_sources"], "whole_allocation_soft_deadline_seconds": stop_after_seconds,
            "observed_wall_seconds": time.monotonic() - allocation_started, "limits": dict(LIMITS),
            "soft_stop_boundary": "before model loads and between goals; scheduler hard limit remains 900 seconds",
            "positive_proof_independent_verification_complete": False, "claim_boundary": evaluation.CLAIM, **CLAIMS}
        record["run_sha256"] = digest(record)
        files.write_new(out / "run.json", record)
        return record
    except BaseException as error:
        files.write_new(out / "execution-status.json", {"schema": RUN_SCHEMA,
            "status": "interrupted-or-failed-prefix-retained", "request_file_sha256": checked.raw_sha256,
            "error_type": type(error).__name__, "error": " ".join(str(error).split())[:2048],
            "uncompleted_outcomes": "unknown", "automatic_retry": False, "resume": False, **CLAIMS})
        raise


def _saved_reservation(checked, record, approval, resource):
    reservation = record["reservation"]
    bridge._keys(reservation, {"status", "stage", "job_id", "jobs", "approval_sha256", "request_file_sha256",
        "evaluation_request_sha256", "source_commit", "allocation_performed", "allocation_elapsed_seconds"},
        "saved diagnostic reservation")
    bridge._keys(reservation["jobs"], {"evaluate"}, "diagnostic job inventory")
    require(type(reservation["job_id"]) is str and re.fullmatch(r"[1-9][0-9]{0,19}", reservation["job_id"])
            and reservation["job_id"] == reservation["jobs"]["evaluate"] != TRAINING_JOB_ID
            and reservation["status"] == "job-verified" and reservation["stage"] == "evaluate"
            and reservation["approval_sha256"] == record["resource_approval_file_sha256"]
            and reservation["request_file_sha256"] == record["resource_request_file_sha256"] == approval["request_file_sha256"]
            and reservation["evaluation_request_sha256"] == checked.raw_sha256
            and reservation["source_commit"] == resource["source_commit"] and reservation["allocation_performed"] is False
            and type(reservation["allocation_elapsed_seconds"]) is int and 0 <= reservation["allocation_elapsed_seconds"] < 720,
            "saved reservation does not join this independently approved diagnostic job")


def verify_run(checked, directory, expected_run_sha256):
    """Original fresh positive-proof replay; diagnostic summary only, no pilot decision."""
    evaluation.paired._model_free()
    directory = bridge._absolute(Path(directory))
    bridge._hash(expected_run_sha256, "external raw run manifest SHA")
    raw = bridge._read(directory / "run.json", MAX_METADATA)
    require(hashlib.sha256(raw).hexdigest() == expected_run_sha256, "saved diagnostic run raw SHA differs")
    record = bridge._decode(raw, MAX_METADATA, "saved diagnostic run")
    fields = {"schema", "status", "request_file_sha256", "resource_approval_file_sha256", "resource_request_file_sha256",
        "reservation", "candidate_adapter_manifest_sha256", "origin_receipt_sha256", "report", "caller_sources",
        "whole_allocation_soft_deadline_seconds", "observed_wall_seconds", "limits", "soft_stop_boundary",
        "positive_proof_independent_verification_complete", "claim_boundary", "run_sha256", *CLAIMS}
    bridge._keys(record, fields, "saved diagnostic run manifest")
    require(record["schema"] == RUN_SCHEMA and record["status"] == "complete-pending-independent-replay"
            and record["request_file_sha256"] == checked.raw_sha256 and record["limits"] == LIMITS
            and record["caller_sources"] == checked.record["caller_sources"] == caller_sources()
            and record["run_sha256"] == digest({k: v for k, v in record.items() if k != "run_sha256"})
            and record["candidate_adapter_manifest_sha256"] == checked.candidate.request.adapter_manifest_sha256
            and record["origin_receipt_sha256"] == {role: ref.receipt_sha256 for role, ref in zip(evaluation.ROLES,
                (checked.baseline, checked.candidate), strict=True)}, "saved diagnostic identity changed")
    require(all(record[k] is False for k in (*CLAIMS, "positive_proof_independent_verification_complete"))
            and record["claim_boundary"] == evaluation.CLAIM
            and record["soft_stop_boundary"] == "before model loads and between goals; scheduler hard limit remains 900 seconds"
            and type(record["observed_wall_seconds"]) in (int, float) and math.isfinite(record["observed_wall_seconds"])
            and 0 < record["observed_wall_seconds"] <= 900
            and type(record["whole_allocation_soft_deadline_seconds"]) in (int, float)
            and math.isfinite(record["whole_allocation_soft_deadline_seconds"])
            and 0 < record["whole_allocation_soft_deadline_seconds"] <= 720,
            "saved diagnostic changed its allocation bounds or claim boundary")
    require(check_request(checked.path, checked.raw_sha256).record == checked.record, "diagnostic admission changed")
    approval, resource = launch.validate_metadata(record["resource_approval_file_sha256"])
    _resource_join(checked, resource)
    _saved_reservation(checked, record, approval, resource)
    plan = _bind(checked)
    _, report = _run_file(directory, record["report"], evaluation.MAX_REPORT_BYTES)
    authorization_sha = digest(_authorization(plan))
    evaluation.verify_result(plan, report, expected_authorization_sha256=authorization_sha, replay=False)
    verification = evaluation.verify_result(plan, report, expected_authorization_sha256=authorization_sha, replay=True)
    require(bridge._read(directory / "run.json", MAX_METADATA) == raw, "run changed during native verification")
    return {"schema": VERIFY_SCHEMA, "status": "diagnostic-proofs-independently-replayed",
        "run_file_sha256": expected_run_sha256, "request_file_sha256": checked.raw_sha256,
        "verification": verification, "metrics": report["metrics"], "model_outputs_regenerated": False,
        "historical_gpu_inference_attested": False, "claim_boundary": evaluation.CLAIM, **CLAIMS}
