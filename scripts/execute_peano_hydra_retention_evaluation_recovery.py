#!/usr/bin/env python3
"""Evaluate the unchanged saved retention adapter under a fresh one-use gate.

Admission and input checks are CPU metadata operations. The separately typed
historical admission preserves the actual producer's source and training plan;
it does not claim that the producer's broken artifact-loading call succeeded.
Only --evaluate can load weights, after the new live reservation is checked.
No mode trains, allocates, resumes, retries or adopts an old checkpoint.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).absolute().parents[1]
sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]
from training.peano_hydra import corrective_workflow as files, origin_bridge as bridge
from training.peano_hydra import retention_evaluation as evaluation, retention_training as training
from training.peano_hydra import retention_evaluation_recovery_launch as gate
from training.peano_hydra import retention_saved_artifact as saved

INPUT_SCHEMA = "peano-hydra-retention-evaluation-recovery-inputs-v1"
PREFLIGHT_SCHEMA = "peano-hydra-retention-evaluation-recovery-input-check-v1"
STAGE_SCHEMA = "peano-hydra-retention-evaluation-recovery-stage-request-v1"
OUTPUT = "results/peano-hydra/evaluations/retention-evaluation-recovery-v1"
REMOTE_ROOT = Path("/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-evaluation-recovery-v1")
PRODUCER_COMMIT = "4aeae795c8cb5bfc622c9943359b5b38446089b9"
TRAINING_JOB_ID = "21456251"
FAILED_EVALUATION_JOB_ID = "21457058"
MODEL_MANIFEST = {"bytes": 191597, "sha256": "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"}
EVALUATION_PLAN = {"path": gate.PACKAGE + "/evaluation-plan.json", "bytes": 110574,
    "sha256": "7dd90249324b82846f6cbae6e157c5fef09e22e0b058b73822f11aae1b95f635"}
FALSE_CLAIMS = {"model_weights_loaded": False, "gpu_allocated": False,
                "training_authorized": False, "native_proof_replay_performed": False}
require, canonical, digest = training.require, training.canonical, training.digest


def read_pinned(path, sha, maximum=training.MAX_METADATA):
    return training._record(Path(path), sha, maximum)


def descriptor(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}, "exact scientific descriptor required")
    name = bridge._relative(value["path"])
    require(name.startswith(gate.PACKAGE + "/")
            and name not in (gate.PACKAGE + "/resource-request.json", gate.PACKAGE + "/approval.json")
            and type(value["bytes"]) is int and 0 < value["bytes"] <= training.MAX_METADATA,
            "scientific descriptor escaped the bounded recovery package")
    record, raw = read_pinned(ROOT / name, value["sha256"])
    require(len(raw) == value["bytes"], "scientific descriptor byte count changed")
    return record


@dataclass(frozen=True)
class Inputs:
    path: Path
    raw_sha256: str
    candidate: saved.PreservedRetentionArtifactReference
    _record_json: str

    def to_dict(self):
        return json.loads(self._record_json)

    def protected_paths(self):
        return (*self.candidate.protected_paths(), self.path.parent)


def load_inputs(path, expected_sha, *, draft=False):
    require(type(draft) is bool, "draft selection must be explicit")
    path = bridge._absolute(Path(path))
    name = "admission-request.json" if draft else "inputs.json"
    require(path == ROOT / gate.PACKAGE / name, "fixed recovery input path required")
    record, _ = read_pinned(path, expected_sha)
    require(type(record) is dict and set(record) == {"schema", "profile", "run_id", "candidate_reference", "locations", "evaluation_plan"}
            and record["schema"] == INPUT_SCHEMA and record["profile"] == gate.PROFILE
            and record["run_id"] == gate.RUN_ID and type(record["locations"]) is dict
            and set(record["locations"]) == {"local", "helios"}
            and record["evaluation_plan"] == EVALUATION_PLAN,
            "recovery input identity, location inventory or original DEV proposal changed")
    descriptor(record["evaluation_plan"])
    where = "helios" if ROOT == REMOTE_ROOT else "local"
    references = {key: saved.reference(record["candidate_reference"], value)
                  for key, value in record["locations"].items()}
    require(all(type(ref) is saved.PreservedRetentionArtifactReference for ref in references.values()),
            "recovery needs the separately typed preserved producer reference")
    for ref in references.values():
        require(ref.to_dict() == record["candidate_reference"]
                and ref.manifest_sha256 == MODEL_MANIFEST["sha256"]
                and ref.inputs.evaluation_plan_sha256 == EVALUATION_PLAN["sha256"],
                "preserved candidate or preregistered proposal identity changed")
        require((ref.admission_receipt_sha256 is None and ref.admission_receipt_path is None) if draft else
                (ref.admission_receipt_sha256 is not None and ref.admission_receipt_path is not None),
                "only authentication accepts a nullable draft admission")
    candidate = references[where]
    if not draft:
        matches = [key for key, ref in references.items()
                   if ref.admission_receipt_path == ROOT / gate.PACKAGE / "admission.json"]
        require(matches == [where], "this source root has no unique declared physical admission binding")
    _, model_raw = read_pinned(candidate.manifest_path, MODEL_MANIFEST["sha256"])
    require(len(model_raw) == MODEL_MANIFEST["bytes"], "actual saved training manifest size changed")
    return Inputs(path, expected_sha, candidate, canonical(record).decode())


def bind_inputs(inputs):
    require(type(inputs) is Inputs and inputs.candidate.admission_receipt_sha256 is not None,
            "actual completed historical admission is required before evaluation binding")
    bound = evaluation.bind_evaluation(ROOT / EVALUATION_PLAN["path"],
        expected_evaluation_plan_sha256=EVALUATION_PLAN["sha256"],
        baseline=inputs.candidate.inputs.baseline, candidate=inputs.candidate)
    current, _ = read_pinned(inputs.path, inputs.raw_sha256)
    require(current == inputs.to_dict(), "recovery input changed during scientific binding")
    descriptor(EVALUATION_PLAN)
    return bound


def preflight_record(inputs, bound):
    return {"schema": PREFLIGHT_SCHEMA, "profile": gate.PROFILE, "run_id": gate.RUN_ID,
        "inputs_sha256": inputs.raw_sha256, "candidate_reference": inputs.candidate.to_dict(),
        "model_manifest": MODEL_MANIFEST, "evaluation_plan": EVALUATION_PLAN,
        "bound_evaluation_plan": bound.to_dict(), **FALSE_CLAIMS}


def check_stage_request(path, expected_sha):
    request, _ = read_pinned(path, expected_sha)
    fields = {"schema", "profile", "run_id", "stage", "inputs", "preflight", "evaluation_plan_sha256",
        "bound_evaluation_plan_sha256", "model_manifest", "producer_source_commit", "training_job_id",
        "failed_evaluation_job_id", "output", "training_authorized", "automatic_retry", "resume",
        "historical_checkpoint_reuse_allowed"}
    require(type(request) is dict and set(request) == fields and request["schema"] == STAGE_SCHEMA
            and request["profile"] == gate.PROFILE and request["run_id"] == gate.RUN_ID
            and request["stage"] == "evaluate" and request["output"] == OUTPUT
            and request["model_manifest"] == MODEL_MANIFEST
            and request["evaluation_plan_sha256"] == EVALUATION_PLAN["sha256"]
            and request["producer_source_commit"] == PRODUCER_COMMIT
            and request["training_job_id"] == TRAINING_JOB_ID
            and request["failed_evaluation_job_id"] == FAILED_EVALUATION_JOB_ID
            and all(request[key] is False for key in ("training_authorized", "automatic_retry", "resume", "historical_checkpoint_reuse_allowed")),
            "scientific request changed the saved model or exact evaluation-only scope")
    require(bridge._absolute(Path(path)) == ROOT / gate.PACKAGE / "evaluate-request.json",
            "fixed evaluation-only scientific request path required")
    descriptor(request["inputs"])
    inputs = load_inputs(ROOT / request["inputs"]["path"], request["inputs"]["sha256"])
    preflight = descriptor(request["preflight"])
    bound = bind_inputs(inputs)
    require(preflight == preflight_record(inputs, bound)
            and request["bound_evaluation_plan_sha256"] == bound.to_dict()["plan_sha256"],
            "actual source, model, admission or DEV plan differs from the CPU preflight")
    return request, inputs, bound


def evaluation_authorization(bound):
    plan = bound.to_dict()
    record = {"schema": evaluation.AUTHORIZATION_SCHEMA,
        "authorization_id": "retention-evaluation-recovery-v1-evaluation",
        "plan_sha256": plan["plan_sha256"],
        "execution_binding_sha256": plan["execution_binding"]["execution_binding_sha256"],
        "model_inference_authorized": True, "gpu_count": 1, "max_wall_seconds": 3300,
        "max_model_calls": 3072, "max_goal_records": 256, "external_hard_wall_limit_required": True,
        "training_authorized": False, "upload_authorized": False, "new_allocation_authorized": False,
        "automatic_retry": False, "resume": False, "historical_checkpoint_reuse_allowed": False}
    return evaluation.validate_execution_authorization(bound, record, expected_authorization_sha256=digest(record))


def immutable_observation(record):
    return {key: value for key, value in record.items()
            if key not in ("allocation_elapsed_seconds", "allocation_remaining_seconds")}


def output_protections(inputs, extra=()):
    return (*inputs.protected_paths(), *(ROOT / name for name in ("training", "scripts", "slurm", "peano-lab", ".git", gate.PACKAGE)), *extra)


def result_parents():
    for name in ("results", "results/peano-hydra", "results/peano-hydra/evaluations"):
        path = ROOT / name
        parent = files.directory(path.parent)
        try:
            try: os.mkdir(path.name, 0o700, dir_fd=parent)
            except FileExistsError: pass
            os.fsync(parent)
        finally:
            os.close(parent)
        os.close(files.directory(path))


def execute(approval_sha, stopped):
    # Time spent in the first gate and every later binding consumes the same
    # allocation. Never start a new 3300-second clock after loading metadata.
    observed_at = time.monotonic()
    observed = gate.check_job_reservation(approval_sha, "evaluate")
    stage_input = observed["scientific_input"]
    descriptor(stage_input)
    request, inputs, bound = check_stage_request(ROOT / stage_input["path"], stage_input["sha256"])
    require(observed["model_manifest"] == MODEL_MANIFEST
            and observed["producer_source_commit"] == PRODUCER_COMMIT
            and observed["training_job_id"] == TRAINING_JOB_ID
            and observed["failed_evaluation_job_id"] == FAILED_EVALUATION_JOB_ID,
            "reserved historical producer, model or spent-job evidence changed")
    authorization = evaluation_authorization(bound)
    fixed = json.loads(canonical(immutable_observation(observed)))
    def reservation_check(assertion):
        require(assertion == authorization, "caller changed the exact derived scientific authorization")
        actual = gate.check_job_reservation(approval_sha, "evaluate")
        require(immutable_observation(actual) == fixed, "reserved source/input/model identity changed")
        return actual
    reservation_check(authorization)
    from training.peano_hydra import frontier_benchmark_run as reports
    result_parents()
    out = ROOT / OUTPUT
    files.guard_output(out, protected=output_protections(inputs))
    evaluation._guard_output(out, bound)
    reports._fresh_directory(out)
    files.write_new(out / "execution-binding.json", {
        "schema": "peano-hydra-retention-evaluation-recovery-caller-v1",
        "scientific_input": stage_input, "reservation": observed, "authorization": authorization,
        "authorization_sha256": digest(authorization), "model_manifest": MODEL_MANIFEST,
        "candidate_reference": inputs.candidate.to_dict(), "preflight": request["preflight"],
        "automatic_retry": False, "resume": False, "historical_checkpoint_reuse_allowed": False,
        "training_authorized": False})
    progress = evaluation.cp.Progress(lambda event: print(canonical(event).decode(), flush=True))
    try:
        result = evaluation.execute_evaluation(bound, authorization=authorization,
            expected_authorization_sha256=digest(authorization), checkpoint_directory=out / "checkpoint",
            reservation_check=reservation_check,
            allocation_deadline=observed_at + 3300 - observed["allocation_elapsed_seconds"] - 1.0,
            progress=progress, stop_requested=stopped)
        reports.write_report(out / "evaluation.json", result)
        return {"status": "evaluation-complete", "directory": str(out), "job_id": observed["job_id"],
            "authorization_sha256": digest(authorization), "metrics": result["metrics"],
            "independent_proof_verification_performed": False, "training_performed": False}
    except BaseException as error:
        files.write_new(out / "execution-status.json", {
            "schema": "peano-hydra-retention-evaluation-recovery-interruption-v1",
            "status": "incomplete-output-retained", "error_type": type(error).__name__,
            "error": " ".join(str(error).split())[:2048], "automatic_retry": False, "resume": False,
            "authorization_sha256": digest(authorization), "complete_comparison_claimed": False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--evaluate", action="store_true")
    modes.add_argument("--authenticate-admission", action="store_true")
    modes.add_argument("--check-inputs", action="store_true")
    modes.add_argument("--check-request", type=Path)
    modes.add_argument("--verify-checkpoint", type=Path)
    parser.add_argument("--approval-sha256")
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--expected-inputs-sha256")
    parser.add_argument("--expected-request-sha256")
    parser.add_argument("--expected-authorization-sha256")
    parser.add_argument("--expected-checkpoint-head-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    try:
        if args.evaluate:
            require(args.approval_sha256 is not None and all(getattr(args, key) is None for key in
                ("inputs", "expected_inputs_sha256", "expected_request_sha256",
                 "expected_authorization_sha256", "expected_checkpoint_head_sha256", "output")),
                "execution accepts only its externally pinned new resource approval")
            training._sha(args.approval_sha256, "resource approval")
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1): signal.signal(sig, stop)
            result = execute(args.approval_sha256, lambda: stopped)
        else:
            require(args.approval_sha256 is None and not os.environ.get("SLURM_JOB_ID") and args.output is not None,
                    "CPU admission/check/verification requires fresh output outside a scheduled GPU allocation")
            require(not {"torch", "transformers", "peft"} & set(sys.modules), "CPU checks cannot inherit model frameworks")
            if args.check_request:
                require(args.expected_request_sha256 is not None and all(getattr(args, key) is None for key in
                    ("inputs", "expected_inputs_sha256", "expected_authorization_sha256", "expected_checkpoint_head_sha256")),
                    "request checking needs only its external raw request pin and fresh output")
                preview, _ = read_pinned(args.check_request, args.expected_request_sha256)
                descriptor(preview["inputs"])
                inputs = load_inputs(ROOT / preview["inputs"]["path"], preview["inputs"]["sha256"])
                files.guard_output(args.output, protected=output_protections(inputs))
                _, inputs, bound = check_stage_request(args.check_request, args.expected_request_sha256)
                result = preflight_record(inputs, bound)
            else:
                require(args.inputs is not None and args.expected_inputs_sha256 is not None
                        and args.expected_request_sha256 is None, "explicit input path and external raw pin required")
                require(args.verify_checkpoint is not None or
                        (args.expected_authorization_sha256 is None and args.expected_checkpoint_head_sha256 is None),
                        "checkpoint pins are only accepted by independent verification")
                inputs = load_inputs(args.inputs, args.expected_inputs_sha256, draft=args.authenticate_admission)
                extra = (args.verify_checkpoint,) if args.verify_checkpoint else ()
                files.guard_output(args.output, protected=output_protections(inputs, extra))
                if args.authenticate_admission:
                    result = saved.authenticate_admission(inputs.candidate, args.output)
                    current, _ = read_pinned(inputs.path, inputs.raw_sha256)
                    require(current == inputs.to_dict(), "draft input changed during admission")
                elif args.verify_checkpoint:
                    require(args.expected_authorization_sha256 is not None and args.expected_checkpoint_head_sha256 is not None,
                            "independent verification requires external authorization and actual checkpoint HEAD pins")
                    head = args.verify_checkpoint / "HEAD.json"
                    _, before = read_pinned(head, args.expected_checkpoint_head_sha256)
                    bound = bind_inputs(inputs)
                    result = evaluation.verify_checkpoint(bound, args.verify_checkpoint,
                        expected_authorization_sha256=args.expected_authorization_sha256, replay=True)
                    require(bridge._read(head, training.MAX_METADATA) == before,
                            "checkpoint HEAD changed during independent verification")
                else:
                    result = preflight_record(inputs, bind_inputs(inputs))
            require(not {"torch", "transformers", "peft"} & set(sys.modules), "CPU operation imported model frameworks")
            if not args.authenticate_admission:
                files.publish_metadata(args.output, result,
                    protected=output_protections(inputs, (args.verify_checkpoint,) if args.verify_checkpoint else ()))
                result = {"status": "written", "output": str(args.output),
                    "sha256": hashlib.sha256(bridge._read(args.output, training.MAX_METADATA)).hexdigest()}
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, RecursionError) as error:
        print("retention-evaluation-recovery: " + " ".join(str(error).split())[:3000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
