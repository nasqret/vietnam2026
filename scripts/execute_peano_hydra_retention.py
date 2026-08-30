#!/usr/bin/env python3
"""Bind the pilot's real inputs, preflight tokens, or enter one reserved stage.

CPU modes do not allocate resources or load model weights. Execution has no
path overrides: its exact scientific request and completed candidate pin come
from the held-job ledger. Authorization below records that existing authority;
it is not a new user approval or an origin/proof attestation.
"""
from __future__ import annotations

import argparse
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
from training.peano_hydra import retention_launch as gate, retention_training as training

INPUT_SCHEMA = "peano-hydra-retention-pilot-inputs-v1"
PREFLIGHT_SCHEMA = "peano-hydra-retention-pilot-preflight-v1"
STAGE_SCHEMA = "peano-hydra-retention-pilot-stage-request-v1"
CONFIG = "training/peano_hydra/configs/qwen3_1_7b_retention_pilot.toml"
require, canonical, digest = training.require, training.canonical, training.digest


def read_pinned(path, sha, maximum=training.MAX_METADATA):
    return training._record(Path(path), sha, maximum)


def descriptor(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}, "exact input descriptor required")
    name = bridge._relative(value["path"])
    require(name.startswith(gate.PACKAGE + "/") and name not in (gate.REQUEST, gate.APPROVAL)
            and type(value["bytes"]) is int and 0 < value["bytes"] <= training.MAX_METADATA,
            "scientific descriptor escaped the bounded pilot inputs")
    record, raw = read_pinned(ROOT / name, value["sha256"])
    require(len(raw) == value["bytes"], "scientific descriptor byte count changed")
    return record


def load_inputs(path, expected_sha):
    require(bridge._absolute(Path(path)) == ROOT / gate.PACKAGE / "inputs.json", "fixed pilot input path required")
    record, _ = read_pinned(path, expected_sha)
    require(type(record) is dict and set(record) == {"schema", "profile", "run_id", "training_input", "locations"}
            and record["schema"] == INPUT_SCHEMA and record["profile"] == gate.PROFILE
            and record["run_id"] == gate.RUN_ID and type(record["locations"]) is dict
            and set(record["locations"]) == {"local", "helios"}, "pilot input identity/locations changed")
    matches = [where for where in record["locations"].values() if type(where) is dict
               and where.get("directory") == str(ROOT / gate.PACKAGE / "preparation")]
    require(len(matches) == 1, "this source root has no unique declared physical input binding")
    where = matches[0]
    require(where.get("config_path") == str(ROOT / CONFIG)
            and where.get("evaluation_plan_path") == str(ROOT / gate.PACKAGE / "evaluation-plan.json"),
            "configuration or preregistered evaluation moved outside the fixed inputs")
    return training.input_reference(record["training_input"], where)


def preflight_record(plan):
    tokens = training.token_preflight(plan)
    return {"schema": PREFLIGHT_SCHEMA, "profile": gate.PROFILE, "run_id": gate.RUN_ID,
            "training_plan": plan.to_dict(), "token_preflight": tokens,
            "model_weights_loaded": False, "gpu_allocated": False, "training_authorized": False}


def check_stage_request(path, expected_sha):
    request, _ = read_pinned(path, expected_sha)
    fields = {"schema", "profile", "run_id", "stage", "inputs", "preflight", "training_plan_sha256",
              "evaluation_plan_sha256", "initialization", "output", "candidate_manifest_binding",
              "automatic_retry", "resume"}
    require(type(request) is dict and set(request) == fields and request["schema"] == STAGE_SCHEMA
            and request["profile"] == gate.PROFILE and request["run_id"] == gate.RUN_ID
            and request["stage"] in gate.STAGES and request["initialization"] == training.INITIALIZATION
            and request["automatic_retry"] is False and request["resume"] is False,
            "scientific stage request changed exact pilot scope")
    stage = request["stage"]
    require(bridge._absolute(Path(path)) == ROOT / gate.PACKAGE / (stage + "-request.json")
            and request["output"] == gate.OUTPUTS[stage]
            and request["candidate_manifest_binding"] == (None if stage == "train" else
                "completed-retention-train-manifest-from-reservation"), "scientific stage/output/candidate binding changed")
    descriptor(request["inputs"])
    inputs = load_inputs(ROOT / request["inputs"]["path"], request["inputs"]["sha256"])
    preflight = descriptor(request["preflight"])
    require(set(preflight) == {"schema", "profile", "run_id", "training_plan", "token_preflight",
                              "model_weights_loaded", "gpu_allocated", "training_authorized"}
            and preflight["schema"] == PREFLIGHT_SCHEMA and preflight["profile"] == gate.PROFILE
            and preflight["run_id"] == gate.RUN_ID
            and all(preflight[key] is False for key in ("model_weights_loaded", "gpu_allocated", "training_authorized")),
            "preflight claims differ from the exact CPU-only record")
    plan = training.bind_training(inputs)
    require(preflight["training_plan"] == plan.to_dict()
            and request["training_plan_sha256"] == plan.to_dict()["training_plan_sha256"]
            and request["evaluation_plan_sha256"] == inputs.evaluation_plan_sha256,
            "actual inputs/source/evaluation differ from the token-preflight plan")
    tokens = preflight["token_preflight"]
    training._validate_token_record(plan, tokens, tokens["token_preflight_sha256"])
    return request, plan, tokens


def training_authorization(plan, tokens, observed):
    bound = plan.to_dict()
    record = {"schema": training.AUTHORIZATION_SCHEMA,
        "training_plan_sha256": bound["training_plan_sha256"],
        "token_preflight_sha256": tokens["token_preflight_sha256"],
        "resource_approval_sha256": observed["approval_sha256"],
        "resource_request_sha256": observed["resource_request_sha256"],
        "model_training_authorized": True, "initialization": training.INITIALIZATION,
        "max_wall_seconds": 7200, "gpu_count": 1,
        **{key: bound[key] for key in ("training_rows", "development_rows", "expected_optimizer_steps")},
        "automatic_retry": False, "resume": False}
    return training.validate_training_authorization(plan, record, expected_authorization_sha256=digest(record))


def evaluation_authorization(plan):
    from training.peano_hydra import retention_evaluation as evaluation
    bound = plan.to_dict()
    record = {"schema": evaluation.AUTHORIZATION_SCHEMA, "authorization_id": "retention-pilot-v1-evaluation",
        "plan_sha256": bound["plan_sha256"],
        "execution_binding_sha256": bound["execution_binding"]["execution_binding_sha256"],
        "model_inference_authorized": True, "gpu_count": 1, "max_wall_seconds": 3300,
        "max_model_calls": 3072, "max_goal_records": 256, "external_hard_wall_limit_required": True,
        "training_authorized": False, "upload_authorized": False, "new_allocation_authorized": False,
        "automatic_retry": False, "resume": False, "historical_checkpoint_reuse_allowed": False}
    return evaluation.validate_execution_authorization(plan, record, expected_authorization_sha256=digest(record))


def immutable_observation(record):
    return {key: value for key, value in record.items()
            if key not in ("allocation_elapsed_seconds", "allocation_remaining_seconds")}


def output_protections(inputs, extra=()):
    return (*inputs.protected_paths(), *(ROOT / name for name in ("training", "scripts", "slurm", "peano-lab", ".git")), *extra)


def result_parents(stage):
    """Create only the fixed result ancestors, with no symlink traversal."""
    paths = [ROOT / "results", ROOT / "results/peano-hydra"]
    if stage == "evaluate": paths.append(ROOT / "results/peano-hydra/evaluations")
    for path in paths:
        parent = files.directory(path.parent)
        try:
            try: os.mkdir(path.name, 0o700, dir_fd=parent)
            except FileExistsError: pass
            os.fsync(parent)
        finally: os.close(parent)
        os.close(files.directory(path))


def execute_stage(stage, approval_sha, stopped):
    # This mandatory live check precedes scientific binding and framework load.
    observed_at = time.monotonic()
    observed = gate.check_job_reservation(approval_sha, stage)
    stage_input = observed["scientific_input"]
    descriptor(stage_input)
    request, plan, tokens = check_stage_request(ROOT / stage_input["path"], stage_input["sha256"])
    require(request["stage"] == stage, "reserved scientific input belongs to another stage")
    authorization = None
    fixed = json.loads(canonical(immutable_observation(observed)))
    def reservation_check(assertion):
        require(authorization is not None and assertion == authorization,
                "caller changed the exact derived scientific authorization")
        actual = gate.check_job_reservation(approval_sha, stage)
        require(immutable_observation(actual) == fixed, "reserved source/input/model identity changed")
        return actual
    result_parents(stage)
    if stage == "train":
        require(observed["model_manifest"] is None, "fresh training cannot adopt an ancestor adapter")
        authorization = training_authorization(plan, tokens, observed)
        target = training.execute(plan, authorization=authorization, expected_authorization_sha256=digest(authorization),
            reservation_check=reservation_check, stop_requested=stopped, progress=training.Progress(), stop_after_seconds=6900)
        raw = bridge._read(target, training.MAX_METADATA)
        return {"status": "training-complete", "manifest": str(target), "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "job_id": observed["job_id"]}
    from training.peano_hydra import retention_evaluation as evaluation, frontier_benchmark_run as reports
    model_pin = observed["model_manifest"]
    require(type(model_pin) is dict and set(model_pin) == {"bytes", "sha256"}, "actual completed model pin required")
    model_path = ROOT / gate.MODEL_OUTPUT / "manifest.json"
    _, model_raw = read_pinned(model_path, model_pin["sha256"])
    require(len(model_raw) == model_pin["bytes"], "reserved completed model size changed")
    candidate = training.TrainingArtifactReference(model_path, model_pin["sha256"], plan.inputs)
    bound = evaluation.bind_evaluation(plan.inputs.evaluation_plan_path,
        expected_evaluation_plan_sha256=plan.inputs.evaluation_plan_sha256, baseline=plan.inputs.baseline, candidate=candidate)
    authorization = evaluation_authorization(bound)
    reservation_check(authorization)
    out = ROOT / gate.EVALUATION_OUTPUT
    evaluation._guard_output(out, bound)
    reports._fresh_directory(out)
    files.write_new(out / "execution-binding.json", {"schema": "peano-hydra-retention-evaluation-caller-v1",
        "scientific_input": stage_input, "reservation": observed, "authorization": authorization,
        "authorization_sha256": digest(authorization), "model_manifest": model_pin,
        "automatic_retry": False, "resume": False})
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
                "independent_proof_verification_performed": False}
    except BaseException as error:
        files.write_new(out / "execution-status.json", {"schema": "peano-hydra-retention-evaluation-interruption-v1",
            "status": "incomplete-output-retained", "error_type": type(error).__name__,
            "error": " ".join(str(error).split())[:2048], "automatic_retry": False, "resume": False,
            "authorization_sha256": digest(authorization), "complete_comparison_claimed": False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--stage", choices=gate.STAGES)
    modes.add_argument("--check-inputs", action="store_true")
    modes.add_argument("--token-preflight", action="store_true")
    modes.add_argument("--check-request", type=Path)
    modes.add_argument("--verify-checkpoint", type=Path)
    parser.add_argument("--approval-sha256")
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--expected-inputs-sha256")
    parser.add_argument("--expected-request-sha256")
    parser.add_argument("--model-manifest", type=Path)
    parser.add_argument("--expected-model-manifest-sha256")
    parser.add_argument("--expected-authorization-sha256")
    parser.add_argument("--expected-checkpoint-head-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    try:
        if args.stage:
            require(args.approval_sha256 is not None and all(getattr(args, key) is None for key in
                ("inputs", "expected_inputs_sha256", "expected_request_sha256", "model_manifest",
                 "expected_model_manifest_sha256", "expected_authorization_sha256", "expected_checkpoint_head_sha256", "output")),
                "execution only accepts its stage and externally pinned resource approval")
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1): signal.signal(sig, stop)
            result = execute_stage(args.stage, args.approval_sha256, lambda: stopped)
        else:
            require(args.approval_sha256 is None and not os.environ.get("SLURM_JOB_ID"),
                    "CPU check/preflight/independent verification cannot enter a scheduled GPU allocation")
            if args.check_request:
                require(args.expected_request_sha256 is not None, "external stage request pin required")
                preview, _ = read_pinned(args.check_request, args.expected_request_sha256)
                descriptor(preview["inputs"])
                inputs = load_inputs(ROOT / preview["inputs"]["path"], preview["inputs"]["sha256"])
                if args.output is not None:
                    files.guard_output(args.output, protected=output_protections(inputs))
                request, plan, tokens = check_stage_request(args.check_request, args.expected_request_sha256)
                result = {"status": "scientific-inputs-verified", "stage": request["stage"],
                    "training_plan_sha256": plan.to_dict()["training_plan_sha256"],
                    "token_preflight_sha256": tokens["token_preflight_sha256"], "model_loaded": False}
            else:
                require(args.inputs is not None and args.expected_inputs_sha256 is not None,
                        "explicit input path and external raw pin required")
                inputs = load_inputs(args.inputs, args.expected_inputs_sha256)
                extra = ()
                if args.verify_checkpoint:
                    require(all(getattr(args, key) is not None for key in ("model_manifest", "expected_model_manifest_sha256",
                        "expected_authorization_sha256", "expected_checkpoint_head_sha256", "output")),
                        "independent verification requires exact candidate, checkpoint HEAD and authorization pins plus fresh output")
                    extra = (args.model_manifest.parent, args.verify_checkpoint)
                if args.output is not None:
                    files.guard_output(args.output, protected=output_protections(inputs, extra))
                if args.verify_checkpoint:
                    from training.peano_hydra import retention_evaluation as evaluation
                    head = args.verify_checkpoint / "HEAD.json"
                    _, before = read_pinned(head, args.expected_checkpoint_head_sha256)
                    candidate = training.TrainingArtifactReference(args.model_manifest, args.expected_model_manifest_sha256, inputs)
                    bound = evaluation.bind_evaluation(inputs.evaluation_plan_path,
                        expected_evaluation_plan_sha256=inputs.evaluation_plan_sha256, baseline=inputs.baseline, candidate=candidate)
                    result = evaluation.verify_checkpoint(bound, args.verify_checkpoint,
                        expected_authorization_sha256=args.expected_authorization_sha256, replay=True)
                    require(bridge._read(head, training.MAX_METADATA) == before, "checkpoint HEAD changed during independent verification")
                else:
                    plan = training.bind_training(inputs)
                    result = preflight_record(plan) if args.token_preflight else plan.to_dict()
            if args.output is not None:
                protected = output_protections(inputs, (args.model_manifest.parent, args.verify_checkpoint) if args.verify_checkpoint else ())
                files.publish_metadata(args.output, result, protected=protected)
        # Large plans/replay evidence are published to the explicitly fresh file.
        print(json.dumps(result if args.stage or args.output is None else {"status": "written", "output": str(args.output),
            "sha256": hashlib.sha256(bridge._read(args.output, training.MAX_METADATA)).hexdigest()}, sort_keys=True), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, RecursionError) as error:
        print("retention-pilot: " + " ".join(str(error).split())[:3000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
