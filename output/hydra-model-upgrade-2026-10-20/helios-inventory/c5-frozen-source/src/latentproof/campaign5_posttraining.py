"""Freeze and dispatch bounded C5 assisted-dev and train-only collection plans.

Requires a completed registered run and its proof-selected best checkpoint.
Both inference plans are frozen before either fresh subprocess starts. Test
metadata and arbitrary protocol-supplied commands are never read or executed.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from .qwen_corpus import (METADATA_REQUIRED, contained_path, prepared_inputs,
    sha256_value, validate_admission, validate_preparation)
from .qwen_data import decode, digest, object_digest, require, require_slurm, write_json
from .qwen_eval_frozen import checkpoint_binding, resolve_policies, source_inventory
from .campaign5_inference import checked_intervention
from .campaign5_inference_runner import FORMAT as PLAN_FORMAT, checked_plan
from .qwen_finalize_v2 import (atomic_json, selected_proof_binding, source_boundary,
    training_object_digest, verify_inputs)

FORMAT = "latent-c5-posttraining-v1"
PROTOCOL_FORMAT = "latent-c5-posttraining-protocol-v1"
ROSTER_RULE = "sha256-protocol-session-v1"
PHASES = ("assisted-dev", "training-rollouts")
ARMS = {"qwen_vanilla", "qwen_fixed", "qwen_random", "qwen_adaptive"}
COMMON_BUDGETS = {"max_actions": 128, "max_new_tokens": 128,
    "max_total_decision_tokens": 16384, "max_context_tokens": 4096,
    "search_width": 1, "candidates_per_step": 1}


def now():
    return datetime.now(timezone.utc).isoformat()


def ordered_training_ids(protocol_id, session_ids, count=32):
    """Hash-sort eligible prepared train IDs without inspecting model outcomes."""
    require(type(protocol_id) is str and protocol_id and type(count) is int and count > 0,
            "invalid deterministic roster namespace/count")
    require(type(session_ids) is list and all(type(key) is str and key for key in session_ids)
            and len(session_ids) == len(set(session_ids)) and len(session_ids) >= count,
            "training roster requires enough distinct admitted/prepared session IDs")
    return sorted(session_ids, key=lambda key: (
        hashlib.sha256((protocol_id + "\0" + key).encode("utf-8")).hexdigest(), key))[:count]


def checked_ids(ids, count, label):
    require(type(ids) is list and all(type(key) is str and key for key in ids)
            and len(ids) == count and len(set(ids)) == count, "invalid exact " + label + " roster")


def checked_protocol(value):
    fields = {"format", "protocol_id", "campaign_id", "training_config_object_sha256",
        "data", "runs", "registered_arms", "primary_policies", "budgets", "assisted_dev",
        "training_rollouts", "process_overhead_seconds", "test_used_for_model_selection"}
    require(type(value) is dict and set(value) == fields and value["format"] == PROTOCOL_FORMAT,
            "invalid exact posttraining protocol schema")
    for key in ("protocol_id", "campaign_id"):
        require(type(value[key]) is str and re.fullmatch(r"[A-Za-z0-9_-]+", value[key]),
                "invalid posttraining identifier")
    require(sha256_value(value["training_config_object_sha256"]), "missing registered training recipe")
    data = value["data"]
    require(type(data) is dict and set(data) == {"dataset_id", "preparation_sha256", "admission_sha256"}
            and type(data["dataset_id"]) is str and data["dataset_id"]
            and all(sha256_value(data[key]) for key in ("preparation_sha256", "admission_sha256")),
            "missing external corpus pins")
    arms = value["registered_arms"]
    require(type(arms) is list and arms and all(type(arm) is str for arm in arms)
            and len(arms) == len(set(arms)) and set(arms) <= ARMS
            and type(value["primary_policies"]) is dict and set(value["primary_policies"]) == set(arms),
            "explicit distinct registered arms and primary policies required")
    for arm, policy in value["primary_policies"].items():
        resolve_policies([{"label": "primary", "policy": policy}], arm, {}, 4)
    require(type(value["runs"]) is list and value["runs"], "empty registered run roster")
    names, pairs = set(), set()
    for entry in value["runs"]:
        require(type(entry) is dict and set(entry) == {"run_id", "arm", "seed"}
                and type(entry["run_id"]) is str and re.fullmatch(r"[A-Za-z0-9_-]+", entry["run_id"])
                and entry["run_id"] not in names and entry["arm"] in arms
                and type(entry["seed"]) is int and entry["seed"] >= 0
                and (entry["arm"], entry["seed"]) not in pairs, "invalid/duplicate registered run")
        names.add(entry["run_id"])
        pairs.add((entry["arm"], entry["seed"]))
    require(pairs == {(arm, seed) for arm in arms for seed in {item["seed"] for item in value["runs"]}},
            "every registered seed must have the same arms")
    require(type(value["budgets"]) is dict
            and value["budgets"] == {**COMMON_BUDGETS, "max_context_tokens": value["budgets"].get("max_context_tokens")}
            and value["budgets"].get("max_context_tokens") in {4096, 6144}
            and all(type(item) is int for item in value["budgets"].values()),
            "common 128-action/128-token budgets with explicit 4096 or 6144 context required")
    dev = value["assisted_dev"]
    require(type(dev) is dict and set(dev) == {"split", "task_ids", "max_wall_seconds", "intervention"}
            and dev["split"] == "dev" and type(dev["max_wall_seconds"]) is int
            and 0 < dev["max_wall_seconds"] <= 7200, "invalid bounded assisted-dev phase")
    checked_ids(dev["task_ids"], 128, "development")
    checked_intervention(dev["intervention"])
    require(dev["intervention"]["fresh_intro_names"] is True
            and dev["intervention"]["checker_feedback"] is True
            and dev["intervention"]["max_attempts_per_state"] == 2,
            "all arms require the same fresh-name interface and one checker-feedback retry")
    train = value["training_rollouts"]
    require(type(train) is dict and set(train) == {"split", "task_ids", "max_wall_seconds", "roster_rule"}
            and train["split"] == "train" and train["roster_rule"] == ROSTER_RULE
            and type(train["max_wall_seconds"]) is int and 0 < train["max_wall_seconds"] <= 1800,
            "invalid bounded train-only collection phase")
    checked_ids(train["task_ids"], 32, "training")
    require(not set(train["task_ids"]) & set(dev["task_ids"]), "development/training task IDs overlap")
    require(type(value["process_overhead_seconds"]) is int and 30 <= value["process_overhead_seconds"] <= 900
            and value["test_used_for_model_selection"] is False,
            "finite explicit startup allowance required; test selection is prohibited")
    return value


def training_metadata_ids(data, manifest, admission, before):
    """Read the pinned train sidecar only; collector later verifies full episodes."""
    spec = manifest["task_metadata"]["train"]
    require(spec.get("source_sha256") == admission["task_metadata"]["train"]["sha256"],
            "prepared train sidecar is not bound to admitted train metadata")
    path = contained_path(data, spec["path"])
    require(sha256_value(spec.get("sha256")) and digest(path) == spec["sha256"]
            and type(spec.get("sessions")) is int and spec["sessions"] > 0,
            "prepared training metadata changed")
    ids = []
    with path.open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n") and raw != b"\n", "invalid train metadata JSONL framing")
            row = decode(raw)
            require(type(row) is dict and METADATA_REQUIRED <= set(row) and row["split"] == "train"
                    and type(row["session_id"]) is str and row["session_id"]
                    and type(row["structural_group"]) is str and row["structural_group"],
                    "foreign/invalid train metadata record")
            ids.append(row["session_id"])
    require(len(ids) == len(set(ids)) == spec["sessions"] == manifest["splits"]["train"]["retained_sessions"]
            and digest(path) == spec["sha256"], "train metadata count/identity changed")
    before[str(path)] = spec["sha256"]
    return ids


def freeze_plans(args):
    require_slurm()
    require(args.cluster in {"wmi", "helios"}, "unregistered execution cluster")
    require(sha256_value(args.protocol_sha256) and digest(args.protocol) == args.protocol_sha256,
            "posttraining protocol differs from its external pin")
    protocol = checked_protocol(decode(Path(args.protocol).read_text(encoding="utf-8")))
    run, data, out = Path(args.run).resolve(), Path(args.data).resolve(), Path(args.out).resolve()
    inputs = (run, data, Path(args.model).resolve(), Path(args.peano_root).resolve())
    require(all(path.is_dir() for path in inputs), "missing explicit run/data/model/Peano directory")
    require(not out.exists() and all(not out.is_relative_to(path) for path in (*inputs, source_boundary())),
            "posttraining output must be new and outside all inputs and the source release")
    status_path = run / "status.json"
    status_pin = digest(status_path)
    status = decode(status_path.read_text(encoding="utf-8"))
    pins = {name + "_sha256": digest(run / file) for name, file in
        (("receipt", "receipt.json"), ("selection", "selection.json"), ("checkpoint", "best.pt"))}
    receipt, selection, checkpoint, before = checkpoint_binding(run, pins)
    cfg, identity = receipt["config"], receipt["identity"]
    registered = {"run_id": run.name, "arm": identity["arm"], "seed": identity["seed"]}
    require(registered in protocol["runs"] and type(identity["seed"]) is int
            and set(cfg["arms"]) == set(protocol["registered_arms"]), "run/arm/seed differs from registered roster")
    require(cfg["campaign_id"] == protocol["campaign_id"]
            and training_object_digest(cfg) == identity["config_sha256"] == protocol["training_config_object_sha256"]
            and cfg.get("data_contract") == {**protocol["data"], "development_split": "dev"},
            "completed training recipe/corpus differs from protocol")
    require(type(cfg["steps"]) is int and cfg["steps"] > 0 and status.get("state") == "completed"
            and type(status.get("step")) is int and status["step"] == cfg["steps"]
            and type(status.get("max_steps")) is int and status["max_steps"] == cfg["steps"]
            and all(status.get(key) == registered[key] for key in registered)
            and status.get("campaign_id") == protocol["campaign_id"] and status.get("smoke") is False,
            "posttraining requires the completed nonsmoke registered update count")
    require(selection["selected_using"] == "development-only" and selection["test_labels_read"] is False
            and selection["checkpoint_step"] <= cfg["steps"]
            and cfg.get("campaign5", {}).get("checkpoint_selection") == "proof_success"
            and selection.get("checkpoint_selection_criterion") == "proof_success"
            and selection.get("proof_selection", {}).get("complete") is True,
            "posttraining requires a complete development-only proof-selected best")
    policy = resolve_policies([{"label": "primary", "policy": protocol["primary_policies"][identity["arm"]]}],
        identity["arm"], selection["halting_policy"], cfg["max_recurrence"])[0]["policy"]
    require(policy == selection["halting_policy"] == selection.get("registered_selection_policy")
            == cfg["campaign5"]["selection_policies"][identity["arm"]],
            "posttraining primary policy differs from the preregistered selection policy")
    admission_path, preparation_path = data / "admission.json", data / "preparation.json"
    require(digest(admission_path) == protocol["data"]["admission_sha256"]
            and digest(preparation_path) == protocol["data"]["preparation_sha256"], "registered data bytes differ")
    admission = decode(admission_path.read_text(encoding="utf-8"))
    validate_admission(admission, expected_admission_sha256=protocol["data"]["admission_sha256"])
    require(admission.get("dataset_id") == protocol["data"]["dataset_id"], "admission dataset was relabelled")
    before.update({str(Path(args.protocol).resolve()): args.protocol_sha256, str(status_path): status_pin,
        str(admission_path): protocol["data"]["admission_sha256"],
        str(preparation_path): protocol["data"]["preparation_sha256"], str(Path(__file__).resolve()): digest(__file__)})
    sources = source_inventory()
    manifest, roster, rows, _, observed = prepared_inputs(data, split="dev",
        expected_dataset_id=protocol["data"]["dataset_id"],
        expected_admission_sha256=protocol["data"]["admission_sha256"],
        expected_preparation_sha256=protocol["data"]["preparation_sha256"])
    del rows
    validate_preparation(manifest, expected_admission_sha256=protocol["data"]["admission_sha256"])
    require(type(cfg.get("max_sequence_length")) is int and type(manifest.get("max_length")) is int
            and protocol["budgets"]["max_context_tokens"] == cfg["max_sequence_length"] == manifest["max_length"],
            "protocol/training/preparation context budgets differ")
    require(manifest == receipt["data_manifest"] and roster["proof_task_ids"] == protocol["assisted_dev"]["task_ids"],
            "assisted dev must use the exact complete frozen 128-task prepared roster")
    require(receipt["validation_selection"] == {key: roster[key] for key in ("validation_ids", "generation_ids")}
            and receipt.get("campaign5", {}).get("proof_selection_roster") == roster["proof_task_ids"][:cfg["proof_tasks"]]
            and receipt["campaign5"]["proof_selection_roster_sha256"]
                == training_object_digest(roster["proof_task_ids"][:cfg["proof_tasks"]]),
            "training proof monitor differs from the frozen dev prefix")
    before.update(observed)
    proof_binding = selected_proof_binding(run, receipt, selection, roster, before, args.peano_root, admission_path)
    all_train_ids = training_metadata_ids(data, manifest, admission, before)
    require(protocol["training_rollouts"]["task_ids"] == ordered_training_ids(protocol["protocol_id"], all_train_ids),
            "train collection roster differs from the preregistered hash order")
    common = {"format": PLAN_FORMAT, "checkpoint": pins, "policy": policy,
        "budgets": dict(protocol["budgets"]), "training_protocol_sha256": args.protocol_sha256,
        "evaluation_source_inventory_sha256": object_digest(sources), "test_used_for_model_selection": False}
    plans = {
        "assisted-dev": checked_plan({**common, "comparison_id": protocol["protocol_id"] + "-" + run.name + "-assisted-dev",
            "mode": "assisted-evaluation", "data": {**protocol["data"], "split": "dev"},
            "max_wall_seconds": protocol["assisted_dev"]["max_wall_seconds"],
            "intervention": protocol["assisted_dev"]["intervention"], "task_ids": None}),
        "training-rollouts": checked_plan({**common, "comparison_id": protocol["protocol_id"] + "-" + run.name + "-training-rollouts",
            "mode": "training-rollouts", "data": {**protocol["data"], "split": "train"},
            "max_wall_seconds": protocol["training_rollouts"]["max_wall_seconds"],
            "intervention": None, "task_ids": protocol["training_rollouts"]["task_ids"]})}
    verify_inputs(before, sources)
    out.mkdir(parents=True, exist_ok=False)
    (out / "plans").mkdir()
    files = {}
    for phase in PHASES:
        path = out / "plans" / (phase + ".json")
        write_json(path, plans[phase])
        files[phase] = {"path": str(path), "sha256": digest(path), "plan": plans[phase]}
        before[str(path)] = files[phase]["sha256"]
    frozen = {"format": FORMAT, "state": "plans-frozen", "tier": "T4", "created_at": now(),
        "job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster, "run": str(run), "run_id": run.name,
        "campaign_id": cfg["campaign_id"], "arm": identity["arm"], "seed": identity["seed"],
        "training_step": status["step"], "checkpoint_step": selection["checkpoint_step"],
        "checkpoint_path": str(checkpoint), "checkpoint_role": "original-selected-best", "checkpoint": pins,
        "original_identity_sha256": selection["identity_sha256"], "selected_proof_binding": proof_binding,
        "primary_policy": policy, "protocol": protocol, "protocol_sha256": args.protocol_sha256,
        "plans": files, "input_sha256_before_and_after": before, "evaluation_source_inventory": sources,
        "prepared_manifest_sha256": protocol["data"]["preparation_sha256"],
        "tokenizer_identity_sha256": manifest["tokenizer_identity_sha256"],
        "rosters": {"assisted-dev": roster["proof_task_ids"], "training-rollouts": protocol["training_rollouts"]["task_ids"]},
        "both_plans_frozen_before_any_evaluation": True, "test_split_parsed": False,
        "model_constructed_by_dispatcher": False, "optimizer_constructed": False, "correction_labels_created": 0}
    write_json(out / "freeze.json", frozen)
    verify_inputs(before, sources)
    return frozen


def evaluator_command(args, phase, frozen):
    require(phase in PHASES, "unregistered posttraining phase")
    spec = frozen["plans"][phase]
    return [sys.executable, "-B", "-m", "latentproof.campaign5_inference_runner",
        "--plan", spec["path"], "--plan-sha256", spec["sha256"],
        "--training-protocol", str(Path(args.protocol).resolve()), "--run", str(Path(args.run).resolve()),
        "--data", str(Path(args.data).resolve()), "--model", str(Path(args.model).resolve()),
        "--peano-root", str(Path(args.peano_root).resolve()), "--out", str(Path(args.out).resolve() / phase),
        "--cluster", args.cluster]


def run_process(command, stdout, stderr, timeout_seconds):
    """Own one fresh process group; bound loading plus suite and clean children."""
    started, timed_out, interrupted = time.monotonic(), False, []
    require(type(timeout_seconds) is int and timeout_seconds > 0, "finite child timeout required")
    with Path(stdout).open("x") as out, Path(stderr).open("x") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        def send_group(signum):
            try:
                os.killpg(process.pid, signum)
            except ProcessLookupError:
                pass
        def interrupted_handler(signum, frame):
            interrupted.append(signum)
            send_group(signal.SIGTERM)
        signals = (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1)
        previous = {item: signal.signal(item, interrupted_handler) for item in signals}
        try:
            deadline = started + timeout_seconds
            while process.poll() is None:
                if interrupted:
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                try:
                    process.wait(timeout=min(1., remaining))
                except subprocess.TimeoutExpired:
                    pass
        finally:
            # This process group is ours; clean descendants even if the parent
            # evaluator exited early. Never signal any other Slurm job.
            send_group(signal.SIGTERM)
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                send_group(signal.SIGKILL)
                process.wait(timeout=10)
            send_group(signal.SIGKILL)
            for item, handler in previous.items():
                signal.signal(item, handler)
    return {"returncode": process.returncode, "timed_out": timed_out,
        "interrupted_signal": interrupted[0] if interrupted else None,
        "elapsed_seconds": time.monotonic() - started, "timeout_seconds": timeout_seconds,
        "process_group_cleaned": True}


def checked_result(args, phase, frozen):
    output = Path(args.out).resolve() / phase
    result_path, receipt_path = output / "summary.json", output / "runner-receipt.json"
    require(result_path.is_file() and receipt_path.is_file(), "evaluator did not create complete result receipts")
    result, receipt = decode(result_path.read_text()), decode(receipt_path.read_text())
    spec, plan = frozen["plans"][phase], frozen["plans"][phase]["plan"]
    require(receipt.get("format") == PLAN_FORMAT and receipt.get("plan_sha256") == spec["sha256"]
            and receipt.get("plan") == plan and receipt.get("summary_sha256") == digest(result_path)
            and receipt.get("evaluation_source_inventory") == frozen["evaluation_source_inventory"]
            and receipt.get("cluster") == args.cluster and receipt.get("state") == result.get("status")
            and result.get("status") in {"completed", "budget_limited"}, "child receipt/plan/result binding changed")
    checkpoint = receipt.get("checkpoint", {})
    require(all(checkpoint.get(key) == pin for key, pin in frozen["checkpoint"].items())
            and checkpoint.get("original_run_id") == frozen["run_id"]
            and checkpoint.get("arm") == frozen["arm"] and checkpoint.get("seed") == frozen["seed"]
            and checkpoint.get("checkpoint_step") == frozen["checkpoint_step"]
            and checkpoint.get("original_identity_sha256") == frozen["original_identity_sha256"]
            and checkpoint.get("checkpoint_role") == "original-selected-best"
            and checkpoint.get("actual_checkpoint_rehashed_after_restore") is True
            and checkpoint.get("optimizer_constructed") is False, "child did not load the frozen selected checkpoint")
    provenance = receipt.get("generation_provenance", {})
    require(provenance.get("policy") == frozen["primary_policy"]
            and provenance.get("checkpoint_sha256") == frozen["checkpoint"]["checkpoint_sha256"]
            and provenance.get("checkpoint_step") == frozen["checkpoint_step"]
            and provenance.get("checkpoint_role") == "original-selected-best"
            and provenance.get("original_identity_sha256") == frozen["original_identity_sha256"]
            and provenance.get("source_inventory_sha256") == object_digest(frozen["evaluation_source_inventory"])
            and provenance.get("tokenizer_identity_sha256") == frozen["tokenizer_identity_sha256"]
            and provenance.get("run_id") == output.name,
            "child generation provenance differs from frozen primary policy/checkpoint/source")
    require(result.get("budgets") == plan["budgets"] and result.get("max_wall_seconds") == plan["max_wall_seconds"]
            and result.get("split") == plan["data"]["split"], "child inference budget/split changed")
    observed = result.get("input_sha256_before_and_after", {})
    require(type(observed) is dict and observed
            and observed.get(str(Path(args.data).resolve() / "preparation.json")) == frozen["prepared_manifest_sha256"]
            and all(Path(path).is_file() and digest(path) == pin for path, pin in observed.items()),
            "child corpus/source inventory differs from actual immutable files")
    if phase == "assisted-dev":
        require(result.get("format") == "latent-c5-assisted-suite-v1"
                and result.get("dataset_id") == plan["data"]["dataset_id"]
                and result.get("proof_task_ids") == frozen["rosters"][phase]
                and result.get("provenance") == provenance and result.get("intervention") == plan["intervention"]
                and result.get("intervention_sha256") == object_digest(plan["intervention"])
                and result.get("reference_actions_used") == 0 and result.get("intrinsic_greedy_metric") is False
                and result.get("test_used_for_selection") is False, "assisted result changed its registered intervention/roster")
        path = output / "proofs.jsonl"
        require(digest(path) == result.get("proofs_sha256"), "assisted proof receipts changed")
        rows = [decode(raw) for raw in path.read_bytes().splitlines()]
        require([row.get("id") for row in rows] == frozen["rosters"][phase], "assisted raw roster changed")
        counts = {"selected": len(rows), "attempted": sum(row["model_calls"] > 0 for row in rows),
            "proved": sum(row["assisted_python_kernel_proof"] is True for row in rows),
            "wall_budget_limited": sum(row["wall_budget_limited"] is True for row in rows)}
        require(result.get("counts") == counts, "assisted summary counts differ from raw receipts")
        metrics = counts
        artifacts = {"proofs_sha256": digest(path)}
    else:
        require(result.get("format") == "latent-c5-training-rollouts-v1"
                and result.get("task_ids") == frozen["rosters"][phase]
                and result.get("generation_provenance") == provenance
                and result.get("correction_labels_created") == 0 and result.get("test_or_dev_parsed") is False,
                "training collection changed its registered scope/roster")
        rollouts, encounters = output / "rollouts.jsonl", output / "encounters.jsonl"
        require(digest(rollouts) == result.get("rollouts_sha256")
                and digest(encounters) == result.get("encounters_sha256"), "train collector raw artifacts changed")
        rows = [decode(raw) for raw in rollouts.read_bytes().splitlines()]
        states = [decode(raw) for raw in encounters.read_bytes().splitlines()]
        require(type(result.get("recorded")) is int and len(rows) == len(states) == result["recorded"]
                and [row.get("id") for row in rows] == [row.get("session_id") for row in states]
                == frozen["rosters"][phase][:len(rows)]
                and result.get("not_attempted") == frozen["rosters"][phase][len(rows):]
                and all(row.get("split") == "train" and row.get("generation_provenance") == provenance
                        and row.get("correction_label") is None for row in states)
                and result.get("solved") == sum(row["solved"] is True for row in states)
                and result.get("wall_budget_limited") == sum(row["wall_budget_limited"] is True for row in rows),
                "train raw receipts/counts differ from the deterministic train roster")
        metrics = {key: result[key] for key in ("recorded", "solved", "wall_budget_limited")}
        artifacts = {"rollouts_sha256": digest(rollouts), "encounters_sha256": digest(encounters)}
    expected_status = "budget_limited" if metrics["wall_budget_limited"] or (phase == "training-rollouts" and result["not_attempted"]) else "completed"
    require(result["status"] == expected_status, "child completion status hides incomplete coverage")
    return {"state": result["status"], "summary_sha256": digest(result_path),
        "runner_receipt_sha256": digest(receipt_path), "metrics": metrics, **artifacts,
        "scope": "bound evaluator receipts; independent native/generation audit remains separate"}


def dispatch(args, *, runner=run_process):
    frozen = freeze_plans(args)
    out = Path(args.out).resolve()
    frozen_pin = digest(out / "freeze.json")
    before = {**frozen["input_sha256_before_and_after"], str(out / "freeze.json"): frozen_pin}
    state = {"format": FORMAT, "tier": "T4", "run_id": out.name, "original_run_id": frozen["run_id"],
        "campaign_id": frozen["campaign_id"], "arm": frozen["arm"], "seed": frozen["seed"],
        "role": "posttraining-assisted-and-collection", "state": "plans-frozen", "updated_at": now(),
        "checkpoint_step": frozen["checkpoint_step"], "checkpoint_sha256": frozen["checkpoint"]["checkpoint_sha256"],
        "protocol_sha256": args.protocol_sha256, "freeze_sha256": frozen_pin,
        "phases": {phase: {"state": "not-started"} for phase in PHASES},
        "both_plans_frozen_before_any_evaluation": True, "test_split_parsed": False,
        "correction_labels_created": 0, "automatic_budget_renewal": False}
    atomic_json(out / "status.json", state)
    try:
        for phase in PHASES:
            verify_inputs(before, frozen["evaluation_source_inventory"])
            state.update(state="running", active_phase=phase, updated_at=now())
            state["phases"][phase] = {"state": "running", "started_at": now()}
            atomic_json(out / "status.json", state)
            command = evaluator_command(args, phase, frozen)
            timeout = frozen["plans"][phase]["plan"]["max_wall_seconds"] + frozen["protocol"]["process_overhead_seconds"]
            process = runner(command, out / (phase + ".stdout"), out / (phase + ".stderr"), timeout)
            verify_inputs(before, frozen["evaluation_source_inventory"])
            if process["interrupted_signal"] is not None:
                result = {"state": "interrupted", "summary_valid": False}
            elif process["timed_out"]:
                result = {"state": "timed-out", "summary_valid": False}
            elif process["returncode"] != 0:
                result = {"state": "failed", "summary_valid": False}
            else:
                result = checked_result(args, phase, frozen)
            state["phases"][phase].update(**result, process=process, finished_at=now())
            atomic_json(out / (phase + "-result.json"), state["phases"][phase])
            atomic_json(out / "status.json", state)
            if result["state"] == "interrupted":
                break
        states = [item["state"] for item in state["phases"].values()]
        state["state"] = ("interrupted" if "interrupted" in states else
            "failed" if any(value in {"failed", "timed-out", "not-started"} for value in states) else
            "budget_limited" if "budget_limited" in states else "completed")
    except BaseException as error:
        state["state"] = "infrastructure-abort"
        state["error"] = {"type": type(error).__name__, "message": str(error)[:2048]}
        active = state.get("active_phase")
        if active and state["phases"][active]["state"] == "running":
            state["phases"][active].update(state="infrastructure-abort", summary_valid=False, finished_at=now())
        raise
    finally:
        state.update(updated_at=now(), active_phase=None)
        atomic_json(out / "status.json", state)
        atomic_json(out / "summary.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("protocol", "run", "data", "model", "peano-root", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    args = parser.parse_args()
    result = dispatch(args)
    raise SystemExit(0 if result["state"] in {"completed", "budget_limited"} else 1)


if __name__ == "__main__":
    main()
