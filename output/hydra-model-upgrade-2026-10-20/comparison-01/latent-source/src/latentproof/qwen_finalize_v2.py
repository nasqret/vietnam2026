"""Freeze both posttraining plans, then evaluate the locked best on dev/test.

Campaign5 v2 keeps the historical finalizer unchanged. It requires a complete
proof-selected checkpoint, explicit paired arms and primary policy rosters. All execution requires SLURM.
This orchestration module neither imports a model nor changes the architecture.
Each evaluator runs in a fresh process; its native per-policy deadline excludes
model loading and optional teacher-forced probes, as in qwen_eval_frozen.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from .qwen_corpus import prepared_inputs, sha256_value, validate_admission
from .qwen_data import decode, digest, object_digest, require, require_slurm, write_json
from .qwen_eval_frozen import (FORMAT as EVALUATION_FORMAT, PLAN_FORMAT,
    checked_plan, checkpoint_binding, evaluation_context_statistics,
    resolve_policies, source_inventory)
from .qwen_eval import PeanoRuntime

PROTOCOL_FORMAT = "latent-qwen-main-finalization-protocol-v2"
FORMAT = "latent-qwen-main-finalization-v2"
ARMS = ("qwen_vanilla", "qwen_fixed", "qwen_random", "qwen_adaptive")
SPLITS = ("dev", "test")
COMMON_BUDGETS = {"max_actions": 128, "max_new_tokens": 128,
    "max_total_decision_tokens": 16384, "max_context_tokens": 4096,
    "search_width": 1, "candidates_per_step": 1}


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def training_object_digest(value):
    """qwen_train's historical ASCII-escaped identity encoding, without torch."""
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def registered_policies():
    fixed = [{"label": "fixed" + str(depth), "policy": {"kind": "fixed", "depth": depth}}
             for depth in (1, 2, 4)]
    return {"qwen_vanilla": fixed[:1], "qwen_fixed": fixed,
            "qwen_random": fixed,
            "qwen_adaptive": fixed + [{"label": "learned050",
                "policy": {"kind": "learned", "quantile": 0.5}}]}


def checked_protocol(value):
    fields = {"format", "protocol_id", "campaign_id", "training_config_object_sha256",
        "data", "runs", "splits", "policies_by_arm", "budgets",
        "max_wall_seconds_per_policy", "teacher_forced", "micro_batch_size",
        "test_used_for_model_selection", "registered_arms"}
    require(type(value) is dict and set(value) == fields and value["format"] == PROTOCOL_FORMAT,
            "invalid exact finalization protocol schema")
    for name in ("protocol_id", "campaign_id"):
        require(type(value[name]) is str and re.fullmatch(r"[A-Za-z0-9_-]+", value[name]),
                "invalid protocol/campaign identifier")
    require(sha256_value(value["training_config_object_sha256"]), "missing registered training recipe")
    data = value["data"]
    require(type(data) is dict and set(data) == {"dataset_id", "preparation_sha256", "admission_sha256"}
            and type(data["dataset_id"]) is str and data["dataset_id"]
            and all(sha256_value(data[key]) for key in ("preparation_sha256", "admission_sha256")),
            "missing external corpus pins")
    require(value["splits"] == list(SPLITS) and value["test_used_for_model_selection"] is False,
            "both registered splits are required and test cannot select weights or policy")
    require(type(value["budgets"]) is dict
            and value["budgets"] == {**COMMON_BUDGETS, "max_context_tokens": value["budgets"].get("max_context_tokens")}
            and value["budgets"]["max_context_tokens"] in {4096, 6144}
            and all(type(item) is int for item in value["budgets"].values())
            and type(value["max_wall_seconds_per_policy"]) is int
            and 0 < value["max_wall_seconds_per_policy"] <= 14400,
            "v2 requires a registered 4096/6144 context, common action/token budgets and finite <=4h policy cap")
    require(type(value["teacher_forced"]) is bool and type(value["micro_batch_size"]) is int
            and value["micro_batch_size"] > 0, "explicit teacher-forced/probe batch settings required")
    require(type(value['registered_arms']) is list and value['registered_arms']
            and len(value['registered_arms']) == len(set(value['registered_arms']))
            and set(value['registered_arms']) <= set(ARMS)
            and set(value['policies_by_arm']) == set(value['registered_arms']),
            'explicit distinct registered arms and policy lists required')
    for arm, entries in value["policies_by_arm"].items():
        resolve_policies(entries, arm, {}, 4)  # Reject bool depths/quantiles and ambiguous policies.
    require(type(value["runs"]) is list and value["runs"], "empty registered training run roster")
    seen, pairs = set(), set()
    for entry in value["runs"]:
        require(type(entry) is dict and set(entry) == {"run_id", "arm", "seed"}
                and type(entry["run_id"]) is str and re.fullmatch(r"[A-Za-z0-9_-]+", entry["run_id"])
                and entry["run_id"] not in seen and entry["arm"] in value["registered_arms"]
                and type(entry["seed"]) is int and entry["seed"] >= 0
                and (entry["arm"], entry["seed"]) not in pairs, "invalid/duplicate registered run")
        seen.add(entry["run_id"])
        pairs.add((entry["arm"], entry["seed"]))
    seeds = {entry["seed"] for entry in value["runs"]}
    require(pairs == {(arm, seed) for arm in value["registered_arms"] for seed in seeds},
            "protocol must register every declared arm at each seed")
    return value


def source_boundary():
    """Protect the immutable release when present, otherwise the package tree."""
    source = Path(__file__).resolve()
    return next((parent for parent in source.parents if (parent / "release-manifest.json").is_file()),
                source.parent)


def verify_inputs(before, sources):
    require(all(Path(path).is_file() and digest(path) == pin for path, pin in before.items()),
            "finalization input changed after freezing")
    require(source_inventory() == sources, "evaluation source package changed after freezing")


def selected_proof_binding(run, receipt, selection, roster, before, peano_root, admission_path):
    """Recompute the selection evidence and compare the two actual weight maps.

    This reads local trusted tensor checkpoints on CPU inside SLURM. No model is
    constructed and no generation is rerun. A matching hash alone would not
    establish that best.pt and the evaluated snapshot contain identical weights.
    """
    from .campaign5_training import proof_candidate
    import torch
    step = selection['checkpoint_step']
    cfg, identity = receipt['config'], receipt['identity']
    policy = cfg['campaign5']['selection_policies'][identity['arm']]
    require(selection['halting_policy'] == selection['registered_selection_policy'] == policy,
            'selected checkpoint policy differs from registered proof policy')
    directory = run / f'validation-proof-step-{step}'
    summary_path, proofs_path = directory/'summary.json', directory/'proofs.jsonl'
    snapshot_path = run/f'evaluation-step-{step}.pt'
    require(all(path.is_file() for path in (summary_path, proofs_path, snapshot_path)),
            'selected checkpoint lacks its actual development proof evidence')
    for path in (summary_path, proofs_path, snapshot_path):
        before[str(path)] = digest(path)
    report = decode(summary_path.read_text(encoding='utf-8'))
    provenance = report.get('provenance', {})
    require(provenance.get('run_id') == run.name
            and provenance.get('checkpoint_sha256') == before[str(snapshot_path)]
            and provenance.get('source_inventory_sha256') == training_object_digest(identity['sources_sha256'])
            and provenance.get('tokenizer_identity_sha256') == receipt['data_manifest']['tokenizer_identity_sha256'],
            'selected proof evidence has different snapshot/source/tokenizer provenance')
    tasks = roster['proof_tasks'][:cfg['proof_tasks']]
    require(report.get('proof_task_ids') == [task['id'] for task in tasks],
            'selected proof report differs from the frozen online development prefix')
    projected = {**roster, 'proof_tasks': tasks, 'proof_task_ids': [task['id'] for task in tasks],
                 'proof_tasks_count': len(tasks)}
    contract = report.get('evaluation_contract', {})
    expected_budgets = {'max_actions': cfg['proof_max_actions'], 'max_new_tokens': cfg['max_new_tokens'],
        'max_total_decision_tokens': cfg['proof_max_actions']*cfg['max_new_tokens'],
        'max_context_tokens': cfg['max_sequence_length'], 'candidates_per_step': 1, 'search_width': 1}
    require(all(contract.get(key) == cfg['data_contract'][key] for key in ('dataset_id', 'preparation_sha256', 'admission_sha256'))
            and contract.get('split') == 'dev'
            and contract.get('selection_object_sha256') == object_digest(projected)
            and contract.get('ordered_roster_sha256') == object_digest({key: projected[key] for key in ('generation_ids', 'proof_task_ids')})
            and contract.get('authority_inventory_sha256') == object_digest(receipt['data_manifest']['authorities'])
            and contract.get('task_metadata_sha256') == receipt['data_manifest']['task_metadata']['dev']['sha256']
            and contract.get('budgets') == contract.get('budget_ceiling') == expected_budgets
            and contract.get('wall_seconds_ceiling') == cfg['generation_seconds_per_event'],
            'selected proof evidence differs from the frozen corpus/roster/budget contract')
    runtime = PeanoRuntime(peano_root, admission_path,
        expected_admission_sha256=cfg['data_contract']['admission_sha256'], split='dev')
    candidate = proof_candidate(report, proofs_path, policy=policy,
        validation_loss=selection['best_validation_loss'], step=step, frozen_tasks=tasks,
        success_label=runtime.success_label)
    runtime.assert_unchanged()
    before.update({str(runtime.root/name): pin for name, pin in runtime.before.items()})
    require(candidate is not None and candidate == selection.get('proof_selection'),
            'selected proof rank differs from recomputed original evidence')
    selected = torch.load(run/'best.pt', map_location='cpu', weights_only=True)
    evaluated = torch.load(snapshot_path, map_location='cpu', weights_only=True)
    require(selected.get('identity') == evaluated.get('identity') == identity
            and selected.get('step') == evaluated.get('step') == step
            and selected.get('policy') == evaluated.get('policy') == policy
            and selected.get('val_loss') == selection['best_validation_loss']
            and selected.get('selection') == candidate,
            'best and evaluated tensor checkpoints have different selection identities')
    left, right = selected['trainable'], evaluated['trainable']
    require(set(left) == set(right) and bool(left), 'selected tensor name inventory changed')
    require(all(torch.is_tensor(left[key]) and torch.is_tensor(right[key])
                and left[key].dtype == right[key].dtype and left[key].shape == right[key].shape
                and torch.equal(left[key], right[key]) for key in left),
            'selected best weights differ from the proof-evaluated snapshot')
    return {'proof_summary_sha256': before[str(summary_path)], 'proofs_sha256': before[str(proofs_path)],
            'evaluation_snapshot_sha256': before[str(snapshot_path)], 'trainable_tensors': len(left),
            'exact_tensor_equality': True, 'generation_replayed': False}


def freeze_plans(args):
    """Validate metadata and CPU checkpoint tensors; freeze BOTH evaluation plans."""
    require_slurm()
    require(args.cluster in {"wmi", "helios"}, "unregistered execution cluster")
    require(sha256_value(args.protocol_sha256) and digest(args.protocol) == args.protocol_sha256,
            "finalization protocol differs from its external pin")
    protocol = checked_protocol(decode(Path(args.protocol).read_text(encoding="utf-8")))
    run, data, out = Path(args.run).resolve(), Path(args.data).resolve(), Path(args.out).resolve()
    for path in (run, data, Path(args.model).resolve(), Path(args.peano_root).resolve()):
        require(path.is_dir(), "missing explicit run/data/model/Peano directory")
    require(not out.exists() and all(not out.is_relative_to(path) for path in
        (run, data, Path(args.model).resolve(), Path(args.peano_root).resolve(), source_boundary())),
        "finalization output must be new and outside all inputs and source release")
    status_path = run / "status.json"
    status_pin = digest(status_path)
    training_status = decode(status_path.read_text(encoding="utf-8"))
    expected = {name + "_sha256": digest(run / file) for name, file in
        (("receipt", "receipt.json"), ("selection", "selection.json"), ("checkpoint", "best.pt"))}
    receipt, selection, checkpoint, before = checkpoint_binding(run, expected)
    cfg, identity = receipt["config"], receipt["identity"]
    registered = {"run_id": run.name, "arm": identity["arm"], "seed": identity["seed"]}
    require(registered in protocol["runs"] and type(identity["seed"]) is int,
            "training run/arm/seed not in the preregistered main roster")
    require(cfg["campaign_id"] == protocol["campaign_id"]
            and training_object_digest(cfg) == protocol["training_config_object_sha256"]
            and identity["config_sha256"] == protocol["training_config_object_sha256"],
            "completed run differs from the registered main training recipe")
    require(selection["selected_using"] == "development-only" and selection["test_labels_read"] is False,
            "posttraining comparison requires development-only checkpoint selection")
    require(type(cfg["steps"]) is int and cfg["steps"] > 0
            and training_status.get("state") == "completed"
            and type(training_status.get("step")) is int and training_status["step"] == cfg["steps"]
            and type(training_status.get("max_steps")) is int and training_status["max_steps"] == cfg["steps"]
            and all(training_status.get(key) == registered[key] for key in ("run_id", "arm", "seed"))
            and training_status.get("campaign_id") == protocol["campaign_id"]
            and training_status.get("smoke") is False
            and selection["checkpoint_step"] <= cfg["steps"],
            "only a completed, nonsmoke matched-update trainer can enter finalization")
    require(cfg.get("data_contract") == {**protocol["data"], "development_split": "dev"}
            and cfg.get("max_sequence_length") == protocol["budgets"]["max_context_tokens"]
            and cfg.get("max_new_tokens") == COMMON_BUDGETS["max_new_tokens"]
            and cfg.get("max_recurrence") == 4, "training data/context/recurrence condition changed")
    require(cfg.get('campaign5', {}).get('checkpoint_selection') == 'proof_success'
            and selection.get('checkpoint_selection_criterion') == 'proof_success'
            and selection.get('proof_selection', {}).get('complete') is True
            and selection.get('registered_selection_policy') == cfg['campaign5']['selection_policies'][identity['arm']]
            and set(cfg['arms']) == set(protocol['registered_arms']),
            'v2 requires an eligible proof-selected checkpoint and exact registered arms')
    admission_path, preparation_path = data / "admission.json", data / "preparation.json"
    require(digest(admission_path) == protocol["data"]["admission_sha256"]
            and digest(preparation_path) == protocol["data"]["preparation_sha256"], "registered data bytes differ")
    admission = decode(admission_path.read_text(encoding="utf-8"))
    validate_admission(admission, expected_admission_sha256=protocol["data"]["admission_sha256"])
    require(admission.get("dataset_id") == protocol["data"]["dataset_id"], "admission dataset was relabelled")
    before.update({str(Path(args.protocol).resolve()): args.protocol_sha256,
                   str(status_path): status_pin, str(admission_path): protocol["data"]["admission_sha256"],
                   str(Path(__file__).resolve()): digest(__file__)})
    sources = source_inventory()
    policies = resolve_policies(protocol["policies_by_arm"][identity["arm"]],
        identity["arm"], selection["halting_policy"], cfg["max_recurrence"])
    plans, rosters = {}, {}
    proof_binding = None
    for split in SPLITS:
        manifest, roster, rows, _, observed = prepared_inputs(data, split=split,
            expected_dataset_id=protocol["data"]["dataset_id"],
            expected_admission_sha256=protocol["data"]["admission_sha256"],
            expected_preparation_sha256=protocol["data"]["preparation_sha256"])
        require(manifest == receipt["data_manifest"]
                and manifest.get('max_length') == protocol['budgets']['max_context_tokens'],
                "evaluation corpus/context differs from actual training manifest")
        if split == "dev":
            require(receipt["validation_selection"] == {key: roster[key] for key in ("validation_ids", "generation_ids")},
                    "development selection differs from the trainer's selection")
            require(receipt.get('campaign5', {}).get('proof_selection_roster') == roster['proof_task_ids'][:cfg['proof_tasks']]
                    and receipt['campaign5']['proof_selection_roster_sha256'] == training_object_digest(roster['proof_task_ids'][:cfg['proof_tasks']]),
                    'online proof roster is not the frozen development prefix')
            proof_binding = selected_proof_binding(run, receipt, selection, roster, before, args.peano_root, admission_path)
        context = evaluation_context_statistics(manifest, rows, roster, split,
            protocol['budgets']['max_context_tokens'], teacher_forced=protocol["teacher_forced"])
        before.update(observed)
        rosters[split] = {key: roster[key] for key in ("validation_ids", "generation_ids", "proof_task_ids")}
        rosters[split].update(selection_object_sha256=object_digest(roster),
            ordered_roster_sha256=object_digest({key: roster[key] for key in ("generation_ids", "proof_task_ids")}),
            context_statistics=context)
        plans[split] = checked_plan({"format": PLAN_FORMAT,
            "comparison_id": protocol["protocol_id"] + "-" + run.name + "-" + split,
            "purpose": "posttraining-frozen-checkpoint", "checkpoint": expected,
            "data": {**protocol["data"], "split": split}, "policies": policies,
            "budgets": dict(protocol["budgets"]), "max_wall_seconds_per_policy": protocol["max_wall_seconds_per_policy"],
            "micro_batch_size": protocol["micro_batch_size"], "teacher_forced": protocol["teacher_forced"],
            "training_protocol_sha256": args.protocol_sha256})
        del rows
    verify_inputs(before, sources)
    out.mkdir(parents=True, exist_ok=False)
    (out / "plans").mkdir()
    plan_files = {}
    for split in SPLITS:
        path = out / "plans" / (split + ".json")
        write_json(path, plans[split])
        plan_files[split] = {"path": str(path), "sha256": digest(path)}
        before[str(path)] = plan_files[split]["sha256"]
    freeze = {"format": FORMAT, "state": "plans-frozen", "created_at": now(),
        "job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster,
        "run": str(run), "run_id": run.name, "campaign_id": cfg["campaign_id"],
        "arm": identity["arm"], "seed": identity["seed"], "training_step": training_status["step"],
        "checkpoint_step": selection["checkpoint_step"], "checkpoint_path": str(checkpoint),
        "checkpoint_role": "original-selected-best", "original": expected,
        "original_identity_sha256": selection["identity_sha256"],
        "original_selected_policy": selection["halting_policy"],
        "protocol_sha256": args.protocol_sha256, "protocol": protocol,
        "plans": plan_files, "rosters": rosters, "policies": policies,
        "input_sha256_before_and_after": before, "evaluation_sources_sha256": sources,
        "both_plans_frozen_before_any_evaluation": True, "test_used_for_model_selection": False,
        "model_imported_by_finalizer": False, "optimizer_constructed": False}
    freeze['selected_proof_binding'] = proof_binding
    write_json(out / "freeze.json", freeze)
    verify_inputs(before, sources)
    return freeze


def evaluator_command(args, split, freeze):
    spec = freeze["plans"][split]
    return [sys.executable, "-B", "-m", "latentproof.qwen_eval_frozen",
        "--plan", spec["path"], "--plan-sha256", spec["sha256"],
        "--training-protocol", str(Path(args.protocol).resolve()),
        "--run", str(Path(args.run).resolve()), "--model", str(Path(args.model).resolve()),
        "--data", str(Path(args.data).resolve()), "--peano-root", str(Path(args.peano_root).resolve()),
        "--out", str(Path(args.out).resolve() / split), "--cluster", args.cluster]


def run_evaluator(command, stdout_path, stderr_path):
    """Fresh interpreter releases model memory; forward worker stop signals."""
    with Path(stdout_path).open("x") as stdout, Path(stderr_path).open("x") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        previous = {}
        def stop(signum, frame):
            if process.poll() is None:
                process.terminate()
            raise InterruptedError("finalizer received signal " + str(signum))
        try:
            for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
                previous[sig] = signal.signal(sig, stop)
            return process.wait()
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def checked_result(directory, split, freeze):
    """Bind the subprocess result to its frozen plan, weights, roster and budget."""
    summary_path = Path(directory) / "summary.json"
    result = decode(summary_path.read_text(encoding="utf-8"))
    checkpoint = result.get("checkpoint", {})
    require(result.get("format") == EVALUATION_FORMAT and result.get("status") in {"completed", "budget_limited"}
            and result.get("purpose") == "posttraining-frozen-checkpoint"
            and result.get("evaluation_plan_sha256") == freeze["plans"][split]["sha256"]
            and result.get("data") == {**freeze["protocol"]["data"], "split": split}
            and result.get("test_used_for_model_selection") is False and result.get("optimizer_constructed") is False,
            "evaluator did not return a complete receipt for the registered split/plan")
    require(checkpoint.get("checkpoint_role") == "original-selected-best"
            and checkpoint.get("checkpoint_step") == freeze["checkpoint_step"]
            and checkpoint.get("original_identity_sha256") == freeze["original_identity_sha256"]
            and checkpoint.get("actual_checkpoint_rehashed_after_restore") is True
            and all(checkpoint.get(key) == pin for key, pin in freeze["original"].items()),
            "evaluator used different selected-best provenance")
    policies = result.get("policies")
    require(type(policies) is list and [{"label": row.get("label"), "policy": row.get("policy")} for row in policies] == freeze["policies"],
            "evaluated policies differ from the preregistered ordered policy roster")
    for record in policies:
        native_path = Path(directory) / record["label"] / "summary.json"
        require(record["native_summary_path"] == record["label"] + "/summary.json"
                and (Path(directory) / record["native_summary_path"]).resolve() == native_path.resolve()
                and digest(native_path) == record["native_summary_sha256"], "native policy receipt missing or changed")
        native = decode(native_path.read_text(encoding="utf-8"))
        contract = native["evaluation_contract"]
        require(native["status"] == record["status"] and record["status"] in {"completed", "budget_limited"}
                and contract == record["evaluation_contract"]
                and contract["split"] == split
                and all(contract[key] == value for key, value in freeze["protocol"]["data"].items())
                and contract["budgets"] == freeze["protocol"]["budgets"]
                and contract["max_wall_seconds"] == freeze["protocol"]["max_wall_seconds_per_policy"]
                and all(native[key] == record[key] == freeze["rosters"][split][key] for key in ("generation_ids", "proof_task_ids"))
                and contract["ordered_roster_sha256"] == freeze["rosters"][split]["ordered_roster_sha256"]
                and contract["selection_object_sha256"] == freeze["rosters"][split]["selection_object_sha256"]
                and native["provenance"]["checkpoint_sha256"] == freeze["original"]["checkpoint_sha256"]
                and native["provenance"]["policy"] == record["policy"],
                "native policy receipt changed its selected targets, budget or checkpoint")
    require(result["status"] == ("completed" if all(row["status"] == "completed" for row in policies) else "budget_limited"),
            "evaluator aggregate deadline status differs from policy receipts")
    return {"split": split, "status": result["status"], "summary_path": str(summary_path.resolve()),
        "summary_sha256": digest(summary_path), "evaluation_plan_sha256": freeze["plans"][split]["sha256"],
        "checkpoint_step": freeze["checkpoint_step"], "checkpoint_sha256": freeze["original"]["checkpoint_sha256"],
        "policies": policies, "elapsed_seconds": result["elapsed_seconds"]}


def finalize(args, *, runner=None):
    """Callable worker entry point; only tests inject an inert evaluator runner."""
    require_slurm()
    freeze = freeze_plans(args)
    out, started = Path(args.out).resolve(), time.monotonic()
    before = dict(freeze["input_sha256_before_and_after"])
    before[str(out / "freeze.json")] = digest(out / "freeze.json")
    runner = run_evaluator if runner is None else runner
    state = {"format": FORMAT, "run_id": out.name, "role": "posttraining-finalization",
        "campaign_id": freeze["campaign_id"], "source_run_id": freeze["run_id"],
        "arm": freeze["arm"], "seed": freeze["seed"], "cluster": args.cluster,
        "job_id": os.environ["SLURM_JOB_ID"], "state": "finalizing", "started_at": now(),
        "checkpoint_role": "original-selected-best", "checkpoint_step": freeze["checkpoint_step"],
        "checkpoint_sha256": freeze["original"]["checkpoint_sha256"],
        "training_step": freeze["training_step"], "protocol_sha256": args.protocol_sha256,
        "freeze_sha256": digest(out / "freeze.json"), "plans": freeze["plans"], "evaluations": []}
    atomic_json(out / "status.json", state)
    try:
        for split in SPLITS:
            verify_inputs(before, freeze["evaluation_sources_sha256"])
            command = evaluator_command(args, split, freeze)
            state.update(active_split=split, updated_at=now(), command=command)
            atomic_json(out / "status.json", state)
            code = runner(command, out / (split + ".stdout.log"), out / (split + ".stderr.log"))
            require(type(code) is int and code == 0, "frozen " + split + " evaluator failed with exit code " + str(code))
            verify_inputs(before, freeze["evaluation_sources_sha256"])
            result = checked_result(out / split, split, freeze)
            state["evaluations"].append(result)
            before[result["summary_path"]] = result["summary_sha256"]
            atomic_json(out / "status.json", state)
        verify_inputs(before, freeze["evaluation_sources_sha256"])
        summary = {**state, "state": "evaluated",
            "status": "completed" if all(row["status"] == "completed" for row in state["evaluations"]) else "budget_limited",
            "execution_complete": True, "tier": "T4", "finished_at": now(),
            "elapsed_seconds": time.monotonic() - started, "both_plans_frozen_before_any_evaluation": True,
            "test_used_for_model_selection": False, "optimizer_constructed": False,
            "input_sha256_before_and_after": before,
            "scope": "Locked development-selected best; all preregistered policies reported separately on dev and test. Evaluation completion is distinct from proof success and deadline coverage."}
        summary.pop("command", None)
        summary.pop("active_split", None)
        write_json(out / "summary.json", summary)
        atomic_json(out / "status.json", summary)
        return summary
    except BaseException as exc:
        state.update(state="failed", error_type=type(exc).__name__, error=str(exc),
            updated_at=now(), elapsed_seconds=time.monotonic() - started, execution_complete=False)
        atomic_json(out / "FAILED.json", state)
        atomic_json(out / "status.json", state)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("protocol", "run", "model", "data", "peano-root", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    args = parser.parse_args()
    result = finalize(args)
    print(json.dumps({"status": result["status"], "execution_complete": True,
                     "summary": str(args.out.resolve() / "summary.json")}), flush=True)


if __name__ == "__main__":
    main()
