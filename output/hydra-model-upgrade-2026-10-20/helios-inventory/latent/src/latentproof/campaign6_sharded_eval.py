"""Campaign 6 frozen, resumable per-target evaluation. SLURM execution only.

Candidate destination: src/latentproof/campaign6_sharded_eval.py. This adapter
reuses the original model loader, strict BPE receipt checks, rollout, and native
constructive checker. It changes scheduling and accounting, not inference.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gc
import json
import math
import os
from pathlib import Path
import re
import time
from types import SimpleNamespace

from .qwen_data import (IntegrityError, decode, digest, group_sessions, load_pinned_tokenizer,
                       object_digest, require, require_slurm)
from .qwen_corpus import prepared_inputs, sha256_value, task_from_episode
from .qwen_eval import (PeanoRuntime, _suite_inputs, checked_budgets,
                       check_prompt_binding, compact_prompt, rollout,
                       strict_generation)
from .qwen_eval_frozen import (checkpoint_binding, load_frozen_checkpoint,
                               resolve_policies, source_inventory)

FORMAT = "latent-c6-sharded-evaluation-v1"
PROTOCOL_FORMAT = "latent-c6-sharded-protocol-v1"
ARMS = ("qwen_vanilla", "qwen_fixed", "qwen_random", "qwen_adaptive")


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    """A chunk is one file; each finished task atomically replaces that file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read_json(path):
    return decode(Path(path).read_text(encoding="utf-8"))


def identifier(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9_-]+", value) is not None


def checked_protocol(value):
    fields = {"format", "campaign_id", "training_protocol_sha256", "budgets",
              "max_wall_seconds_per_task", "chunk_size", "worker_count",
              "infrastructure_attempt_limit", "splits", "policies_by_arm",
              "primary_policy_by_arm", "test_used_for_model_selection", "evaluation_scopes"}
    require(type(value) is dict and set(value) == fields
            and value["format"] == PROTOCOL_FORMAT and identifier(value["campaign_id"]),
            "invalid exact Campaign 6 evaluation protocol")
    require(sha256_value(value["training_protocol_sha256"])
            and value["test_used_for_model_selection"] is False,
            "immutable training protocol required; no test-based selection")
    require(value["splits"] == ["dev", "test"], "complete paired dev and test required")
    scopes = value["evaluation_scopes"]
    require(type(scopes) is list and scopes and len(scopes) == len(set(scopes))
            and set(scopes) <= {"dev", "test-diagnostic", "test-complement", "test-fresh"},
            "explicit distinct evaluation scopes required")
    require(not ({"test-complement", "test-fresh"} <= set(scopes)),
            "complement and strict-fresh overlap: register only one as a cell scope")
    checked_budgets(value["budgets"], ceiling=value["budgets"])
    require(type(value["max_wall_seconds_per_task"]) is int
            and 1 <= value["max_wall_seconds_per_task"] <= 3600,
            "each target requires one common finite wall budget")
    for name, maximum in (("chunk_size", 64), ("worker_count", 64),
                          ("infrastructure_attempt_limit", 3)):
        require(type(value[name]) is int and 1 <= value[name] <= maximum,
                "invalid bounded " + name)
    registered_arms = set(value["policies_by_arm"])
    require(registered_arms and registered_arms <= set(ARMS)
            and "qwen_vanilla" in registered_arms
            and set(value["primary_policy_by_arm"]) == registered_arms,
            "explicit registered arms require policies and a vanilla baseline")
    for arm in registered_arms:
        entries = value["policies_by_arm"][arm]
        # Explicit policies only: never silently recover a policy from weights.
        require(all(type(entry) is dict and type(entry.get("policy")) is dict
                    for entry in entries), "policies must be explicit")
        resolved = resolve_policies(entries, arm, {}, 4)
        require(value["primary_policy_by_arm"][arm] in {entry["label"] for entry in resolved},
                "primary policy missing from registered sweep")
    expected = {"qwen_vanilla": {"kind": "fixed", "depth": 1},
                "qwen_fixed": {"kind": "fixed", "depth": 2},
                "qwen_random": {"kind": "fixed", "depth": 2},
                "qwen_adaptive": {"kind": "learned", "quantile": 0.5}}
    for arm in registered_arms:
        policy = next(entry["policy"] for entry in value["policies_by_arm"][arm]
                      if entry["label"] == value["primary_policy_by_arm"][arm])
        require(policy == expected[arm], "primary policy must match the C5 preregistration")
    return value


def cells(plan):
    """Primary before exploratory, test before dev; neither order selects models."""
    result = []
    protocol = plan["protocol"]
    for primary in (True, False):
        for split in protocol["evaluation_scopes"]:
            for run in plan["runs"]:
                for entry in protocol["policies_by_arm"][run["arm"]]:
                    is_primary = entry["label"] == protocol["primary_policy_by_arm"][run["arm"]]
                    if is_primary != primary:
                        continue
                    result.append({"id": run["run_id"] + "--" + split + "--" + entry["label"],
                        "run_id": run["run_id"], "arm": run["arm"], "seed": run["seed"],
                        "split": split, "label": entry["label"], "policy": entry["policy"],
                        "primary": primary})
    return result


def chunks(plan):
    index = 0
    size = plan["protocol"]["chunk_size"]
    for cell in cells(plan):
        count = len(plan["rosters"][cell["split"]]["proof_tasks"])
        for offset in range(0, count, size):
            yield {"index": index, "cell": cell, "offset": offset,
                   "stop": min(offset + size, count),
                   "owner": index % plan["protocol"]["worker_count"]}
            index += 1


def chunk_path(output, chunk):
    return Path(output) / "chunks" / chunk["cell"]["id"] / f"{chunk['offset']:05d}.json"


def chunk_tasks(plan, chunk):
    return plan["rosters"][chunk["cell"]["split"]]["proof_tasks"][chunk["offset"]:chunk["stop"]]


def new_chunk(plan_sha256, chunk):
    return {"format": FORMAT, "plan_sha256": plan_sha256, "chunk": chunk, "records": []}


def check_chunk(value, plan, plan_sha256, chunk):
    require(type(value) is dict and value.get("format") == FORMAT
            and value.get("plan_sha256") == plan_sha256 and value.get("chunk") == chunk,
            "resume chunk belongs to a different plan or shard")
    tasks = {task["id"]: task for task in chunk_tasks(plan, chunk)}
    observed = set()
    for record in value["records"]:
        key = record["task_id"]
        require(key in tasks and key not in observed
                and record["task_sha256"] == object_digest(tasks[key]),
                "chunk task is duplicate, foreign, or changed")
        require(type(record["attempts"]) is int and 1 <= record["attempts"]
                <= plan["protocol"]["infrastructure_attempt_limit"], "bad attempt accounting")
        require(record["state"] in {"evaluated", "infrastructure-error"}, "bad task state")
        require(record["cell"] == chunk["cell"], "task policy/checkpoint cell changed")
        if record["state"] == "evaluated":
            proof = record["proof"]
            require(proof["id"] == key and proof["task_sha256"] == object_digest(tasks[key])
                    and proof["budgets"] == plan["protocol"]["budgets"]
                    and proof["reference_actions_used"] == 0 and proof["search_branches"] == 1
                    and proof["restarts"] == 0, "saved rollout identity/budget drift")
        observed.add(key)
    return value


def terminal(record, protocol):
    return record is not None and (record["state"] == "evaluated"
        or record["attempts"] >= protocol["infrastructure_attempt_limit"])


def acquire_claim(output, chunk):
    """Nonblocking shared-filesystem claim, automatically released on death."""
    directory = Path(output) / "claims"
    directory.mkdir(parents=True, exist_ok=True)
    stream = (directory / f"{chunk['index']:06d}.lock").open("a")
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        return None
    return stream


def checked_selection_schedule(schedule, cfg):
    expected = cfg["campaign5"]["proof_eval_steps"]
    require(schedule["format"] == "latent-c6-selection-schedule-assessment-v1"
            and schedule["registered_steps"] == expected
            and schedule["attained_step"] == cfg["steps"]
            and [row["step"] for row in schedule["milestones"]] == expected
            and all(type(row["eligible"]) is bool for row in schedule["milestones"])
            and schedule["selection_schedule_complete"] is all(row["eligible"] for row in schedule["milestones"]),
            "invalid C6 selection opportunity assessment")
    return schedule["selection_schedule_complete"]


def freeze(args):
    """CPU SLURM: independently bind selection evidence before any C6 inference."""
    require_slurm()
    from .qwen_finalize_v2 import checked_protocol as checked_training_protocol
    require(digest(args.protocol) == args.protocol_sha256, "C6 protocol hash changed")
    protocol = checked_protocol(read_json(args.protocol))
    require(digest(args.training_protocol) == protocol["training_protocol_sha256"],
            "C5 registered training/finalization protocol changed")
    training = checked_training_protocol(read_json(args.training_protocol))
    require(set(training["registered_arms"]) == set(protocol["policies_by_arm"])
            and protocol["budgets"] == training["budgets"],
            "C6 keeps registered training action/token/context budgets and exact arms")
    require(not args.out.exists(), "freeze output must be new")
    for source in (args.runs_root, args.data, args.model, args.peano_root):
        require(not args.out.resolve().is_relative_to(source.resolve()),
                "freeze output cannot lie within an input directory")
    args.out.mkdir(parents=True)
    inventories = source_inventory()
    rosters, inputs, runs = {}, {}, []
    original_rosters = {}
    for split in protocol["splits"]:
        _, roster, rows, metadata, before = prepared_inputs(args.data, split=split,
            expected_dataset_id=training["data"]["dataset_id"],
            expected_admission_sha256=training["data"]["admission_sha256"],
            expected_preparation_sha256=training["data"]["preparation_sha256"])
        original_rosters[split] = roster
        if split == "dev":
            rosters["dev"] = roster
        else:
            rosters["test-diagnostic"] = roster
            episodes = group_sessions(rows)
            original_ids = set(roster["proof_task_ids"])
            by_id = {row["id"]: row for row in rows}
            action_sessions = {by_id[key]["session_id"] for key in roster["generation_ids"]}
            # Freeze by stable ID only, without looking at target formulas or
            # successes. Original corpus admission verifies structural split.
            complement = [task_from_episode(episodes[key], metadata[key])
                          for key in sorted(episodes) if key not in original_ids]
            fresh = [task for task in complement if task["id"] not in action_sessions]
            for name, tasks in (("test-complement", complement), ("test-fresh", fresh)):
                rosters[name] = {**roster, "proof_tasks": tasks,
                    "proof_task_ids": [task["id"] for task in tasks],
                    "proof_tasks_count": len(tasks), "generation_ids": [], "generation_rows": 0,
                    "scope": name, "original_selection_object_sha256": object_digest(roster),
                    "prior_action_evaluation_session_ids": sorted(action_sessions & {task["id"] for task in tasks}),
                    "selection_rule": "sorted original test session IDs minus C5 proof-task IDs"
                        + (" minus all C5 generation-row session IDs" if name == "test-fresh" else ""),
                    "selection_independent_of_outcomes": True}
        inputs.update(before)
    # Runs can be pending here. Freeze identities, corpus, policies and budgets
    # now; bind each completed trainer later with the unchanged strict binder.
    for registered in training["runs"]:
        runs.append(registered)
    inputs.update({str(args.protocol.resolve()): args.protocol_sha256,
                   str(args.training_protocol.resolve()): protocol["training_protocol_sha256"]})
    require(source_inventory() == inventories and all(digest(path) == pin for path, pin in inputs.items()),
            "source or corpus changed while freezing")
    require(all(rosters[scope]["proof_tasks"] for scope in protocol["evaluation_scopes"]),
            "cannot register an empty evaluation scope")
    plan = {"format": FORMAT, "protocol": protocol, "protocol_sha256": args.protocol_sha256,
        "training_protocol": training, "runs": runs,
        "rosters": {scope: rosters[scope] for scope in protocol["evaluation_scopes"]},
        "original_rosters": original_rosters,
        "test_complement_audit": rosters["test-complement"],
        "evaluation_sources_sha256": inventories, "input_sha256_before_and_after": inputs,
        "created_at": now(), "cluster": args.cluster, "job_id": os.environ["SLURM_JOB_ID"],
        "tier": "T4", "native_lean_acceptance": "not-performed"}
    atomic_json(args.out / "plan.json", plan)
    atomic_json(args.out / "freeze-receipt.json", {"format": FORMAT, "state": "frozen",
        "plan_sha256": digest(args.out / "plan.json"), "run_count": len(runs),
        "cell_count": len(cells(plan)), "chunk_count": sum(1 for _ in chunks(plan)),
        "test_used_for_model_selection": False, "checkpoint_binding_deferred": True,
        "roster_counts": {scope: len(rosters[scope]["proof_tasks"]) for scope in protocol["evaluation_scopes"]},
        "strict_fresh_count": len(rosters["test-fresh"]["proof_tasks"]),
        "complement_count": len(rosters["test-complement"]["proof_tasks"]),
        "complement_prior_action_sessions": len(rosters["test-complement"]["prior_action_evaluation_session_ids"])})
    return plan


def bind(args):
    """CPU SLURM, after a trainer completes: bind the frozen registered run."""
    from .qwen_finalize_v2 import freeze_plans, verify_inputs
    plan = load_plan(args)
    require(any(run["run_id"] == args.run_id for run in plan["runs"]), "unregistered run")
    parent = args.bindings / args.run_id
    parent.mkdir(parents=True, exist_ok=True)
    ready = parent / "binding.json"
    if ready.exists():
        return load_binding(args, plan, args.run_id)
    # The lock also protects simultaneous dependent workers attempting binding.
    with (parent / "binding.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if ready.exists():
            return load_binding(args, plan, args.run_id)
        # The trainer writes this assessment just after its completed status.
        # Wait for the assessment before creating irreversible binding output.
        is_new_training = plan["training_protocol"]["campaign_id"].startswith("qwen-c6-")
        schedule_path = args.runs_root / args.run_id / "selection-schedule.json"
        if is_new_training:
            require(schedule_path.is_file(), "trainer selection assessment is not ready")
        directory, result = None, None
        for attempt in range(1, 4):
            candidate = parent / ("validated" if attempt == 1 else "validated-attempt" + str(attempt))
            if (candidate / "freeze.json").is_file():
                restored = read_json(candidate / "freeze.json")
                require(restored["run_id"] == args.run_id
                        and restored["protocol_sha256"] == plan["protocol"]["training_protocol_sha256"],
                        "partial binding belongs to a different run/protocol")
                verify_inputs(restored["input_sha256_before_and_after"], restored["evaluation_sources_sha256"])
                directory, result = candidate, restored
                break
            if not candidate.exists():
                directory = candidate
                result = freeze_plans(SimpleNamespace(protocol=args.training_protocol,
                    protocol_sha256=plan["protocol"]["training_protocol_sha256"],
                    run=args.runs_root / args.run_id, data=args.data, out=directory,
                    model=args.model, peano_root=args.peano_root, cluster=args.cluster))
                break
        require(result is not None, "three interrupted binding attempts exhausted; evidence retained")
        registered = next(run for run in plan["runs"] if run["run_id"] == args.run_id)
        producer = read_json(args.runs_root / args.run_id / "receipt.json")
        cfg = producer["config"]
        binding = {**registered, "format": FORMAT, "plan_sha256": args.plan_sha256,
            "state": "bound", "checkpoint": result["original"], "checkpoint_step": result["checkpoint_step"],
            "original_identity_sha256": result["original_identity_sha256"],
            "tokenizer_identity_sha256": producer["data_manifest"]["tokenizer_identity_sha256"],
            "selection_binding_relative": directory.name,
            "selection_binding_sha256": digest(directory / "freeze.json"),
            "selected_proof_binding": result["selected_proof_binding"],
            "architecture_counts": {"prelude_layers": cfg["prelude_layers"],
                "core_layers": cfg["core_layers"],
                "coda_layers": 28 - cfg["prelude_layers"] - cfg["core_layers"],
                "max_recurrence": cfg["max_recurrence"]}}
        if is_new_training:
            schedule = read_json(schedule_path)
            checked_selection_schedule(schedule, cfg)
            binding.update(selection_schedule_sha256=digest(schedule_path),
                selection_schedule_complete=schedule["selection_schedule_complete"],
                primary_comparison_eligible=schedule["selection_schedule_complete"],
                selection_schedule_scope="Pinned worker assessment; milestone evidence was checked by campaign6_recovery")
        else:
            binding.update(selection_schedule_sha256=None, selection_schedule_complete=None,
                primary_comparison_eligible=True,
                selection_schedule_scope="Historical C5 diagnostic checkpoint under its original selection contract")
        atomic_json(ready, binding)
        return binding


def load_binding(args, plan, run_id):
    parent = args.bindings / run_id
    value = read_json(parent / "binding.json")
    registered = next(run for run in plan["runs"] if run["run_id"] == run_id)
    require(value["selection_binding_relative"] in {"validated", "validated-attempt2", "validated-attempt3"},
            "foreign binding receipt path")
    receipt_path = parent / value["selection_binding_relative"] / "freeze.json"
    require(value["format"] == FORMAT and value["plan_sha256"] == args.plan_sha256
            and all(value[key] == registered[key] for key in ("run_id", "arm", "seed"))
            and digest(receipt_path) == value["selection_binding_sha256"],
            "checkpoint binding differs from frozen plan/run")
    receipt = read_json(receipt_path)
    require(receipt["original"] == value["checkpoint"]
            and receipt["protocol_sha256"] == plan["protocol"]["training_protocol_sha256"]
            and receipt["selected_proof_binding"]["exact_tensor_equality"] is True,
            "checkpoint binder receipt changed")
    producer, selection, _, _ = checkpoint_binding(args.runs_root / run_id, value["checkpoint"])
    cfg = producer["config"]
    require(value["checkpoint_step"] == receipt["checkpoint_step"] == selection["checkpoint_step"]
            and value["original_identity_sha256"] == receipt["original_identity_sha256"] == selection["identity_sha256"]
            and value["selected_proof_binding"] == receipt["selected_proof_binding"]
            and value["tokenizer_identity_sha256"] == producer["data_manifest"]["tokenizer_identity_sha256"],
            "binding checkpoint/selection/tokenizer metadata differs from pinned receipts")
    require(value["architecture_counts"] == {"prelude_layers": cfg["prelude_layers"],
        "core_layers": cfg["core_layers"], "coda_layers": 28 - cfg["prelude_layers"] - cfg["core_layers"],
        "max_recurrence": cfg["max_recurrence"]}, "checkpoint architecture call accounting changed")
    if plan["training_protocol"]["campaign_id"].startswith("qwen-c6-"):
        schedule_path = args.runs_root / run_id / "selection-schedule.json"
        require(sha256_value(value.get("selection_schedule_sha256"))
                and digest(schedule_path) == value["selection_schedule_sha256"],
                "selection opportunity assessment changed")
        complete = checked_selection_schedule(read_json(schedule_path), cfg)
        require(value["selection_schedule_complete"] is complete
                and value["primary_comparison_eligible"] is complete,
                "binding falsely changed selection opportunity eligibility")
    else:
        require(value["selection_schedule_sha256"] is None and value["selection_schedule_complete"] is None
                and value["primary_comparison_eligible"] is True,
                "historical diagnostic selection contract changed")
    return value


def load_plan(args):
    require_slurm()
    require(digest(args.plan) == args.plan_sha256, "frozen C6 evaluation plan changed")
    plan = read_json(args.plan)
    require(plan["format"] == FORMAT, "foreign C6 plan format")
    checked_protocol(plan["protocol"])
    require(source_inventory() == plan["evaluation_sources_sha256"],
            "source inventory differs from frozen evaluation source")
    require(digest(args.training_protocol) == plan["protocol"]["training_protocol_sha256"],
            "training protocol bytes differ")
    return plan


def write_worker_status(args, state, **extra):
    atomic_json(args.out / f"worker-{args.worker_index:02d}.json", {
        "format": FORMAT, "plan_sha256": args.plan_sha256, "worker_index": args.worker_index,
        "job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster,
        "updated_at": now(), "state": state, **extra})


def worker(args):
    """GPU SLURM worker. Repeat this command to resume exactly its frozen shard.

    Interruptions lose at most one in-flight target. An evaluated target,
    including a per-task timeout, is never rerun. Infrastructure errors have
    finitely many attempts and never masquerade as model failures.
    """
    plan = load_plan(args)
    protocol = plan["protocol"]
    require(type(args.worker_index) is int and 0 <= args.worker_index < protocol["worker_count"],
            "worker outside the frozen finite roster")
    for source in (args.runs_root, args.data, args.model, args.peano_root):
        require(not args.out.resolve().is_relative_to(source.resolve()),
                "worker output cannot lie within an input directory")
    args.out.mkdir(parents=True, exist_ok=True)
    # Advisory interprocess lock is released automatically after process death.
    # Launch at most one live process per (plan, worker_index).
    with (args.out / f"worker-{args.worker_index:02d}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return worker_locked(args, plan)


def worker_locked(args, plan):
    from .qwen_train import generate_action
    import torch
    protocol = plan["protocol"]
    started = time.monotonic()
    require(type(args.worker_seconds) is int and args.worker_seconds
            > protocol["max_wall_seconds_per_task"] + 300, "worker allocation too short")
    deadline = started + args.worker_seconds
    inventory = plan["evaluation_sources_sha256"]
    # All workers see the same ordered finite queue. A short nonblocking flock
    # claims each chunk, so an idle worker can help another shard and a killed
    # worker leaves no stale ownership. Worker index identifies status only.
    assigned = list(chunks(plan))
    write_worker_status(args, "running", chunks_assigned=len(assigned))
    # Preserve primary/test priority. Reload at cell-run boundaries; do not
    # regroup all cells by run and let a slow sweep delay other primary arms.
    current_run, model, tokenizer, checkpoint, model_inputs = None, None, None, None, None
    split_cache = {}
    counts = Counter()
    for chunk in assigned:
        if not (args.bindings / chunk["cell"]["run_id"] / "binding.json").exists():
            counts["unbound_run_chunks"] += 1
            continue
        claim = acquire_claim(args.out, chunk)
        if claim is None:
            counts["busy_chunks"] += 1
            continue
        path = chunk_path(args.out, chunk)
        saved = check_chunk(read_json(path), plan, args.plan_sha256, chunk) if path.exists() else new_chunk(args.plan_sha256, chunk)
        records = {item["task_id"]: item for item in saved["records"]}
        tasks = chunk_tasks(plan, chunk)
        pending = [task for task in tasks if not terminal(records.get(task["id"]), protocol)]
        if not pending:
            counts["chunks_already_terminal"] += 1
            claim.close()
            continue
        if time.monotonic() + protocol["max_wall_seconds_per_task"] + 180 >= deadline:
            claim.close()
            write_worker_status(args, "resumable-allocation-boundary", counts=dict(counts))
            return {"state": "resumable-allocation-boundary", "counts": dict(counts)}
        cell = chunk["cell"]
        run = load_binding(args, plan, cell["run_id"])
        if current_run != run["run_id"]:
            if model is not None:
                del model
                gc.collect()
                torch.cuda.empty_cache()
            model, checkpoint, model_inputs = load_frozen_checkpoint(args.runs_root / run["run_id"], args.model, run["checkpoint"])
            require(checkpoint["checkpoint_step"] == run["checkpoint_step"]
                    and checkpoint["arm"] == run["arm"] and checkpoint["seed"] == run["seed"],
                    "model restore identity differs from frozen run")
            tokenizer, _ = load_pinned_tokenizer(args.model)
            current_run, split_cache = run["run_id"], {}
        provenance = {"run_id": run["run_id"], "checkpoint_sha256": run["checkpoint"]["checkpoint_sha256"],
            "tokenizer_identity_sha256": checkpoint["original_training_data_manifest"]["tokenizer_identity_sha256"],
            "source_inventory_sha256": object_digest(inventory), "policy": cell["policy"],
            "model_vocab_size": model.causal_lm.config.vocab_size,
            "checkpoint_step": run["checkpoint_step"], "evaluation_plan_sha256": args.plan_sha256}
        base_split = "dev" if cell["split"] == "dev" else "test"
        if base_split not in split_cache:
            data = plan["training_protocol"]["data"]
            manifest, roster, _, episodes, runtime, before = _suite_inputs(args.data, args.data / "admission.json",
                args.peano_root, tokenizer, provenance, split=base_split,
                expected_admission_sha256=data["admission_sha256"],
                expected_preparation_sha256=data["preparation_sha256"])
            require(roster == plan["original_rosters"][base_split], "frozen source task roster changed")
            split_cache[base_split] = (episodes, runtime, before)
        episodes, runtime, before = split_cache[base_split]
        cfg = {**checkpoint["original_config"], "max_new_tokens": protocol["budgets"]["max_new_tokens"],
               "max_sequence_length": protocol["budgets"]["max_context_tokens"]}
        def propose(prompt, *, max_new_tokens, deadline_monotonic=None):
            return generate_action(model, tokenizer, prompt, cell["policy"], cfg,
                max_new_tokens=max_new_tokens, deadline=deadline_monotonic, provenance=provenance)
        for task in pending:
            if time.monotonic() + protocol["max_wall_seconds_per_task"] + 120 >= deadline:
                claim.close()
                write_worker_status(args, "resumable-allocation-boundary", counts=dict(counts))
                return {"state": "resumable-allocation-boundary", "counts": dict(counts)}
            prior = records.get(task["id"])
            record = {"task_id": task["id"], "task_sha256": object_digest(task), "cell": cell,
                "attempts": (prior["attempts"] if prior else 0) + 1,
                "previous_infrastructure_errors": ([] if prior is None else
                    prior.get("previous_infrastructure_errors", []) + [prior["error"]]),
                "job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster,
                "device": torch.cuda.get_device_name(0), "started_at": now(),
                "max_wall_seconds_per_task": protocol["max_wall_seconds_per_task"],
                "checkpoint": run["checkpoint"], "generation_provenance": provenance}
            task_started = time.monotonic()
            # Reserve this attempt durably before any model/native work. If
            # killed, the next lock owner sees an interrupted attempt, so even
            # hard process deaths consume the registered finite retry budget.
            record.update(state="infrastructure-error", error={"type": "InterruptedAttempt",
                "message": "Attempt reserved; no terminal receipt was committed"})
            records[task["id"]] = record
            saved["records"] = [records[item["id"]] for item in tasks if item["id"] in records]
            atomic_json(path, saved)
            try:
                # Gold replay is infrastructure validation, outside the target
                # inference clock; its actions never enter the model callback.
                runtime.verify_reference(episodes[task["session_id"]])
                inference_started = time.monotonic()
                proof = rollout(task, propose, runtime, tokenizer, protocol["budgets"],
                    expected_provenance=provenance, budget_ceiling=protocol["budgets"],
                    deadline_monotonic=inference_started + protocol["max_wall_seconds_per_task"])
                record.update(state="evaluated", proof=proof,
                    inference_seconds=time.monotonic() - inference_started)
                record.pop("error", None)
            except IntegrityError:
                # Hash, authority, BPE, or source contradictions are fatal.
                # They must never become a tolerated individual model failure.
                raise
            except Exception as exc:
                record.update(state="infrastructure-error",
                    error={"type": type(exc).__name__, "message": str(exc)})
                torch.cuda.empty_cache()
            record.update(elapsed_seconds=time.monotonic() - task_started, finished_at=now())
            records[task["id"]] = record
            saved["records"] = [records[item["id"]] for item in tasks if item["id"] in records]
            atomic_json(path, saved)
            counts[record["state"]] += 1
            write_worker_status(args, "running", cell=cell, task_id=task["id"], counts=dict(counts))
        runtime.assert_unchanged()
        require(all(digest(name) == pin for name, pin in {**before, **model_inputs}.items())
                and source_inventory() == inventory, "evaluation inputs changed during chunk")
        claim.close()
    write_worker_status(args, "pass-completed", counts=dict(counts), elapsed_seconds=time.monotonic() - started)
    return {"state": "pass-completed", "counts": dict(counts)}


def replay_record(record, task, runtime, tokenizer, plan, *, architecture=None):
    """Replay saved raw actions without invoking a model or trusting its verdict.

    This is native replay by the same admitted checker, not an independently
    implemented proof checker, and it does not regenerate model decisions.
    """
    proof, provenance = record["proof"], record["generation_provenance"]
    require(record["max_wall_seconds_per_task"] == plan["protocol"]["max_wall_seconds_per_task"],
            "task time budget changed")
    budgets = plan["protocol"]["budgets"]
    architecture = architecture or {"prelude_layers": 8, "core_layers": 12,
                                    "coda_layers": 8, "max_recurrence": 4}
    require(proof["model_calls"] == len(proof["steps"]) <= budgets["max_actions"]
            and proof["submitted_actions"] == len(proof["actions"])
            and len(proof["actions"]) <= len(proof["steps"]), "saved rollout counts changed")
    goals = runtime.initial_state(task)
    actions, transitions, tokens, native_work = [], [], 0, 0
    last_native = None
    for index, step in enumerate(proof["steps"]):
        prompt = compact_prompt(goals, task["library_prefix_length"], focus=0)
        available = min(budgets["max_new_tokens"], budgets["max_context_tokens"]
            - len(tokenizer.encode(prompt, add_special_tokens=False)),
            budgets["max_total_decision_tokens"] - tokens)
        require(available > 0 and step["index"] == index + 1 and step["prompt"] == prompt
                and step["effective_max_new_tokens"] == available, "saved trajectory prompt/budget drift")
        raw = step["generation"]
        check_prompt_binding(raw, prompt, tokenizer, available, budgets["max_context_tokens"])
        parsed = strict_generation(raw, tokenizer, available, expected_provenance=provenance)
        require(parsed == step["decoded"], "stored BPE parsing verdict differs from recomputation")
        for name in ("block_calls", "head_calls", "gate_calls", "readouts", "recurrence_depths"):
            require(type(raw[name]) is list and len(raw[name]) == len(raw["decision_ids"])
                    and all(type(value) is int and value >= 0 for value in raw[name]),
                    "generation cost receipt has inconsistent length/type")
        for position, depth in enumerate(raw["recurrence_depths"]):
            kind = provenance["policy"]["kind"]
            require(1 <= depth <= architecture["max_recurrence"]
                    and (kind != "fixed" or depth == provenance["policy"]["depth"]),
                    "recorded token depth differs from the registered policy")
            readouts = 1 if kind == "fixed" else depth
            blocks = architecture["prelude_layers"] + depth * architecture["core_layers"] + readouts * architecture["coda_layers"]
            gates = min(depth, architecture["max_recurrence"] - 1) if kind == "learned" else 0
            require(raw["block_calls"][position] == blocks
                    and raw["head_calls"][position] == raw["readouts"][position] == readouts
                    and raw["gate_calls"][position] == gates,
                    "recorded token cost differs from original architecture and policy")
        tokens += parsed["decision_tokens"]
        if index >= len(proof["actions"]):
            require(index == len(proof["steps"]) - 1
                    and (not parsed["valid_action"] or proof["status"] == "deadline_after_model_call"),
                    "valid generated action silently omitted")
            continue
        require(parsed["valid_action"] and proof["actions"][index] == parsed["action"],
                "native actions differ from raw decoded generation")
        actions.append(parsed["action"])
        native = runtime.run_prefix(task, actions, transitions)
        native_work += len(actions)
        require(all(step.get(key) == native.get(key) for key in
                    ("status", "valid_transition", "native_error", "native_error_type", "trace_sha256")),
                "native replay differs from saved transition")
        last_native = native
        # Deadline-after-native stores the native result, but deliberately does
        # not update accepted transitions or goals and does not count success.
        if proof["status"] == "deadline_after_native_call" and index == len(proof["steps"]) - 1:
            require(proof["native_completion_outside_wall_budget"] == native["python_kernel_complete"],
                    "late native success flag changed")
            continue
        if native["valid_transition"]:
            transitions, goals = native["transitions"], native["remaining_goals"]
        else:
            require(index == len(proof["steps"]) - 1, "trajectory continued after native failure")
    require(tokens == proof["generated_decision_tokens"] <= budgets["max_total_decision_tokens"]
            and native_work == proof["native_prefix_transitions_requested"]
            and len(transitions) == proof["accepted_actions"] and goals == proof["remaining_goals"],
            "trajectory token/action/native-work accounting mismatch")
    saved_native = proof["native_result"]
    if last_native is None:
        require(saved_native is None, "saved native certificate has no submitted actions")
    elif last_native["native_result"] is None:
        require(saved_native is None, "native resource/request error fabricated a certificate")
    else:
        fresh_native = last_native["native_result"]
        # Ignore runtime timing metadata if a future native wrapper adds it;
        # bind all semantic certificate fields and the complete native trace.
        semantic = ("status", "classical", "theorem", "environment_sha256", "kernel_checked",
            "trace", "goals", "tactics_requested", "tactics_applied", "failed_tactics",
            "failed_step", "proof_nodes", "error", "error_type")
        require(type(saved_native) is dict and all(saved_native.get(key) == fresh_native.get(key)
                    for key in semantic), "saved final native certificate differs from fresh replay")
    limited = "deadline" in proof["status"] or any(
        step["generation"]["stop_reason"] == "wall_time_budget" for step in proof["steps"])
    require(type(proof["wall_budget_limited"]) is bool and proof["wall_budget_limited"] is limited,
            "saved per-task deadline classification changed")
    proved = bool(last_native and last_native["python_kernel_complete"]
                  and proof["status"] == "proved" and not proof["wall_budget_limited"])
    if last_native and last_native["python_kernel_complete"] and not limited:
        require(proof["status"] == "proved", "native proof was relabelled as an ordinary failure")
    require(proof["autonomous_python_kernel_proof"] is proved
            and (not proved or not goals), "saved proof success differs from native replay")
    return {"native_replayed": True, "proved": proved, "native_prefixes": len(actions),
            "tokens": tokens, "scope": "same pinned constructive checker; no model regeneration or Lean"}


def aggregate(args):
    """CPU SLURM: full-roster progress and native replay; never select a winner."""
    plan = load_plan(args)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    tokenizer, tokenizer_info = load_pinned_tokenizer(args.model)
    data = plan["training_protocol"]["data"]
    runtimes = {split: PeanoRuntime(args.peano_root, args.data / "admission.json",
        expected_admission_sha256=data["admission_sha256"], split=split)
        for split in plan["protocol"]["splits"]}
    for split in plan["protocol"]["splits"]:
        manifest, selection, _, _, _ = prepared_inputs(args.data, split=split,
            expected_dataset_id=data["dataset_id"], expected_admission_sha256=data["admission_sha256"],
            expected_preparation_sha256=data["preparation_sha256"])
        require(selection == plan["original_rosters"][split], "aggregate source corpus changed")
        require(tokenizer_info == manifest["tokenizer"], "aggregate tokenizer differs from prepared corpus")
    records_by_cell = {cell["id"]: {} for cell in cells(plan)}
    chunk_hashes = {}
    for chunk in chunks(plan):
        path = chunk_path(args.results, chunk)
        if not path.exists():
            continue
        pin = digest(path)
        saved = check_chunk(read_json(path), plan, args.plan_sha256, chunk)
        require(digest(path) == pin, "chunk changed while reading; rerun aggregate")
        chunk_hashes[str(path)] = pin
        records_by_cell[chunk["cell"]["id"]].update({r["task_id"]: r for r in saved["records"]})
    rows = []
    for cell in cells(plan):
        tasks = plan["rosters"][cell["split"]]["proof_tasks"]
        counts = Counter(selected=len(tasks))
        strata, families, outcomes, costs = {}, {}, {}, Counter()
        run = (load_binding(args, plan, cell["run_id"])
            if (args.bindings / cell["run_id"] / "binding.json").exists() else None)
        for task in tasks:
            key = task["id"]
            record = records_by_cell[cell["id"]].get(key)
            group = task["stratum"]
            bucket = strata.setdefault(group, Counter())
            family = families.setdefault(task["task_family"], Counter())
            bucket["selected"] += 1
            family["selected"] += 1
            if record is None:
                counts["missing"] += 1
                bucket["missing"] += 1
                family["missing"] += 1
                outcomes[key] = None
                continue
            require(run is not None, "result exists for a run without its validated checkpoint binding")
            require(record["checkpoint"] == run["checkpoint"], "result checkpoint bytes changed")
            if record["state"] == "infrastructure-error":
                counts["infrastructure_errors"] += 1
                bucket["infrastructure_errors"] += 1
                family["infrastructure_errors"] += 1
                outcomes[key] = None
                continue
            provenance = record["generation_provenance"]
            require(provenance["evaluation_plan_sha256"] == args.plan_sha256
                    and provenance["checkpoint_sha256"] == run["checkpoint"]["checkpoint_sha256"]
                    and provenance["run_id"] == run["run_id"]
                    and provenance["checkpoint_step"] == run["checkpoint_step"]
                    and provenance["tokenizer_identity_sha256"] == run["tokenizer_identity_sha256"]
                    and provenance["policy"] == cell["policy"]
                    and provenance["source_inventory_sha256"] == object_digest(plan["evaluation_sources_sha256"]),
                    "generation provenance differs from frozen cell")
            require(type(record["inference_seconds"]) in {int, float}
                    and math.isfinite(record["inference_seconds"]) and record["inference_seconds"] >= 0,
                    "invalid measured inference duration")
            replay = replay_record(record, task, runtimes["dev" if cell["split"] == "dev" else "test"], tokenizer, plan,
                architecture=run["architecture_counts"])
            proof = record["proof"]
            counts["evaluated"] += 1
            counts["attempted"] += int(proof["model_calls"] > 0)
            counts["solved"] += int(replay["proved"])
            counts["per_task_wall_limited"] += int(proof["wall_budget_limited"])
            counts["status:" + proof["status"]] += 1
            bucket["evaluated"] += 1
            bucket["solved"] += int(replay["proved"])
            bucket["wall_limited"] += int(proof["wall_budget_limited"])
            family["evaluated"] += 1
            family["attempted"] += int(proof["model_calls"] > 0)
            family["solved"] += int(replay["proved"])
            family["wall_limited"] += int(proof["wall_budget_limited"])
            outcomes[key] = replay["proved"]
            costs["inference_seconds"] += record["inference_seconds"]
            costs["decision_tokens"] += replay["tokens"]
            costs["model_calls"] += proof["model_calls"]
            for step in proof["steps"]:
                generated = step["generation"]
                for name in ("block_calls", "head_calls", "gate_calls", "readouts"):
                    costs[name] += sum(generated[name])
        complete = counts["evaluated"] == counts["selected"]
        rows.append({**cell, "suite_id": cell["id"], "checkpoint_step": None if run is None else run["checkpoint_step"],
            "counts": dict(counts), "status": "complete" if complete else "incomplete",
            "selected": counts["selected"], "attempted": counts["attempted"],
            "completed": counts["evaluated"] - counts["per_task_wall_limited"],
            "solved": counts["solved"], "wall_limited": counts["per_task_wall_limited"],
            "missing": counts["missing"], "infrastructure_errors": counts["infrastructure_errors"],
            "selection_schedule_complete": None if run is None else run["selection_schedule_complete"],
            "primary_comparison_eligible": False if run is None else run["primary_comparison_eligible"],
            "checkpoint_sha256": None if run is None else run["checkpoint"]["checkpoint_sha256"],
            "roster_sha256": object_digest(tasks), "budgets_sha256": object_digest(plan["protocol"]["budgets"]),
            "source_manifest_sha256": object_digest(plan["evaluation_sources_sha256"]),
            "complete_roster": complete, "yield_all_selected": counts["solved"] / counts["selected"],
            "strata": {key: dict(value) for key, value in strata.items()}, "costs": dict(costs),
            "families": {key: dict(value) for key, value in families.items()},
            "outcomes": outcomes, "missing_is_not_model_failure": True})
    # Paired outcomes only when BOTH full rosters are present. No conditional
    # attempted-subset accuracy or rank on the incomplete table is emitted.
    pairs = []
    for split in plan["protocol"]["evaluation_scopes"]:
        for seed in sorted({run["seed"] for run in plan["runs"]}):
            group = [row for row in rows if row["primary"] and row["split"] == split and row["seed"] == seed]
            baseline = next(row for row in group if row["arm"] == "qwen_vanilla")
            for row in group:
                if row is baseline:
                    continue
                ready = (row["complete_roster"] and baseline["complete_roster"]
                    and row["primary_comparison_eligible"] and baseline["primary_comparison_eligible"])
                pair = {"split": split, "seed": seed, "baseline": baseline["id"], "candidate": row["id"], "complete": ready,
                    "paired": ready, "left": baseline["id"], "right": row["id"],
                    "selected": row["selected"],
                    "full_rosters_present": row["complete_roster"] and baseline["complete_roster"],
                    "equal_selection_opportunity": row["primary_comparison_eligible"] and baseline["primary_comparison_eligible"],
                    "primary_comparison_eligible": row["primary_comparison_eligible"] and baseline["primary_comparison_eligible"]}
                if ready:
                    table = Counter()
                    for key, value in baseline["outcomes"].items():
                        table[("baseline_" + str(int(value))) + "_candidate_" + str(int(row["outcomes"][key]))] += 1
                    pair["paired_task_contingency"] = dict(table)
                    pair.update(both_solved=table["baseline_1_candidate_1"],
                        left_only=table["baseline_1_candidate_0"], right_only=table["baseline_0_candidate_1"],
                        neither_solved=table["baseline_0_candidate_0"])
                    pair["difference_all_selected"] = row["yield_all_selected"] - baseline["yield_all_selected"]
                pairs.append(pair)
    for runtime in runtimes.values():
        runtime.assert_unchanged()
    summary = {"format": FORMAT, "plan_sha256": args.plan_sha256, "tier": "T4",
        "state": "complete" if all(row["complete_roster"] for row in rows) else "incomplete",
        "created_at": now(), "generated_at": now(), "job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster,
        "cells": rows, "evaluations": rows, "paired_primary": pairs, "comparisons": pairs,
        "chunk_sha256": chunk_hashes,
        "native_replay_performed": True, "independent_checker_implementation": False,
        "model_generation_replayed": False, "test_used_for_model_selection": False,
        "scope": "Frozen C5 selected Qwen adapters, registered constructive corpus, per-target budgets; no general HA claim",
        "coverage_semantics": "Every frozen task remains in its denominator. Missing/infrastructure rows are unresolved; per-task timeouts are registered model-budget outcomes.",
        "cost_semantics": "Inference wall time and emitted-token block/head/gate/readout counts; block counts are not FLOPs or total experiment cost."}
    atomic_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("freeze", "bind", "worker", "aggregate"):
        sub = subs.add_parser(name)
        for field in ("training-protocol", "runs-root", "data", "model", "peano-root", "out"):
            sub.add_argument("--" + field, type=Path, required=True)
        sub.add_argument("--cluster", choices=("helios", "wmi"), required=True)
        if name == "freeze":
            sub.add_argument("--protocol", type=Path, required=True)
            sub.add_argument("--protocol-sha256", required=True)
        else:
            sub.add_argument("--plan", type=Path, required=True)
            sub.add_argument("--plan-sha256", required=True)
            sub.add_argument("--bindings", type=Path, required=True)
        if name == "bind":
            sub.add_argument("--run-id", required=True)
        if name == "worker":
            sub.add_argument("--worker-index", type=int, required=True)
            sub.add_argument("--worker-seconds", type=int, required=True)
        if name == "aggregate":
            sub.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    require_slurm()
    result = globals()[args.command](args)
    print(json.dumps({"command": args.command, "state": result.get("state", "frozen")}), flush=True)


if __name__ == "__main__":
    main()
