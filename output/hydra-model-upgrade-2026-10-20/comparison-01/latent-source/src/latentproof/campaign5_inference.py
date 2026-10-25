"""Separately reported bounded inference assistance and train-only encounters.

No model or checker import occurs at module import. Model calls receive only
current rendered goals and optional already-observed checker errors. Raw BPE
decisions, decoded actions, transformations, and submitted actions are separate
receipt fields. No gold action or reference prefix is supplied to inference.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import time

from .qwen_data import (compact_prompt, digest, group_sessions, object_digest,
                        require, require_slurm, tokenizer_identity, write_json)
from .qwen_eval import (PeanoRuntime, _suite_inputs, call_propose, check_prompt_binding,
                        checked_budgets, effective_generation_budget, rollout,
                        strict_generation, validate_provenance)

INTERVENTION_FORMAT = "latent-c5-inference-intervention-v1"
ENCOUNTER_FORMAT = "latent-c5-training-encounter-v1"


def checked_intervention(value):
    require(type(value) is dict and set(value) == {"format", "fresh_intro_names", "checker_feedback",
            "max_attempts_per_state", "max_feedback_bytes"} and value["format"] == INTERVENTION_FORMAT,
            "invalid explicit inference intervention")
    require(type(value["fresh_intro_names"]) is bool and type(value["checker_feedback"]) is bool
            and (value["fresh_intro_names"] or value["checker_feedback"]), "assisted condition must specify an intervention")
    require(type(value["max_attempts_per_state"]) is int and 1 <= value["max_attempts_per_state"] <= 4
            and (value["checker_feedback"] or value["max_attempts_per_state"] == 1), "unregistered retry budget")
    require(type(value["max_feedback_bytes"]) is int and 64 <= value["max_feedback_bytes"] <= 4096,
            "invalid finite feedback-context budget")
    return value


def fresh_intro_action(action, goals, *, enabled):
    """Rename only a colliding simple ``intro NAME`` using visible declarations.

    Canonical native goal text prints declarations as ``name : ...`` before ⊢.
    All open goals are considered conservatively. No formula/hypothesis choice,
    theorem, witness, or other tactic is repaired or substituted.
    """
    record = {"raw_action": action, "submitted_action": action, "transform": "identity", "renaming": {}}
    match = re.fullmatch(r"intro ([A-Za-z_][A-Za-z0-9_']*)", action)
    if not enabled or match is None:
        return record
    occupied = set()
    for goal in goals:
        require(type(goal) is str and "⊢" in goal, "fresh-name allocation requires canonical rendered goal text")
        context = goal.split("⊢", 1)[0]
        occupied.update(re.findall(r"(?:^|,\s*)([A-Za-z_][A-Za-z0-9_']*)\s*:", context))
    old = match.group(1)
    if old not in occupied:
        return record
    index = 0
    while "c5fresh" + str(index) in occupied:
        index += 1
    new = "c5fresh" + str(index)
    return {"raw_action": action, "submitted_action": "intro " + new,
            "transform": "visible-intro-collision-v1", "renaming": {old: new},
            "occupied_names": sorted(occupied)}


def feedback_prompt(goals, library_prefix_length, failures, max_bytes):
    base = compact_prompt(goals, library_prefix_length, focus=0)
    if not failures:
        return base
    # Include the most recent rejection only, with explicit JSON escaping.
    # The action is bounded by generation tokens; the message is byte-clipped.
    last = failures[-1]
    payload = {"submitted_action": last["submitted_action"], "error": str(last["error"])}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    while len(encoded) > max_bytes and payload["error"]:
        payload["error"] = payload["error"][:max(0, len(payload["error"]) - max(1, (len(encoded) - max_bytes) // 2))]
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > max_bytes:
        # A long rejected action is a digest, never an unmarked partial tactic.
        payload = {"submitted_action_sha256": hashlib.sha256(str(last["submitted_action"]).encode()).hexdigest(),
                   "error": "previous action rejected"}
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        if len(encoded) > max_bytes:
            encoded = b'{"error":"previous action rejected"}'
    require(len(encoded) <= max_bytes, "feedback byte budget exceeded")
    return base.removesuffix("Tactic:") + "Checker feedback: " + encoded.decode() + "\nReturn one different valid tactic.\nTactic:"


def assisted_rollout(task, propose, runtime, tokenizer, budgets, intervention, *,
                     expected_provenance, deadline_monotonic=None, budget_ceiling=None):
    """Single path, bounded retries at rejected states, no branch search or gold.

    max_actions bounds accepted path length. Every retry consumes the SAME
    decision-token budget and wall budget, and each native replay is accounted.
    This is an assisted proof metric, never intrinsic greedy pass@1.
    """
    require_slurm()
    budgets = checked_budgets(budgets, ceiling=budget_ceiling)
    intervention = checked_intervention(intervention)
    validate_provenance(expected_provenance)
    goals = runtime.initial_state(task)
    actions, transitions, receipts = [], [], []
    consumed, native_work, native_calls, retry_calls, transformations = 0, 0, 0, 0, 0
    result = {"id": task["id"], "session_id": task["session_id"], "task_family": task["task_family"],
        "stratum": task["stratum"], "formula": task["formula"], "environment_sha256": task["environment_sha256"],
        "task_sha256": object_digest(task), "budgets": budgets, "intervention": intervention,
        "intervention_sha256": object_digest(intervention), "status": "action_budget",
        "assisted_python_kernel_proof": False, "intrinsic_greedy_proof_success": None,
        "lean_acceptance": "not-performed", "reference_actions_used": 0,
        "search_branches": 1, "restarts": 0, "actions": actions, "steps": receipts, "native_result": None}
    terminal = False
    for index in range(budgets["max_actions"]):
        failures, accepted = [], False
        for attempt in range(intervention["max_attempts_per_state"]):
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                result["status"] = "not_attempted_deadline" if not receipts else "deadline"
                terminal = True
                break
            prompt = feedback_prompt(goals, task["library_prefix_length"], failures if intervention["checker_feedback"] else [],
                                     intervention["max_feedback_bytes"])
            limit, prompt_tokens = effective_generation_budget(prompt, tokenizer, budgets, consumed)
            if limit <= 0:
                result["status"] = "context_limit" if prompt_tokens >= budgets["max_context_tokens"] else "total_token_budget"
                terminal = True
                break
            raw = call_propose(propose, prompt, max_new_tokens=limit, deadline_monotonic=deadline_monotonic)
            check_prompt_binding(raw, prompt, tokenizer, limit, budgets["max_context_tokens"])
            parsed = strict_generation(raw, tokenizer, limit, expected_provenance=expected_provenance)
            consumed += parsed["decision_tokens"]
            retry_calls += int(attempt > 0)
            step = {"index": index + 1, "attempt": attempt + 1, "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt_tokens": prompt_tokens,
                "effective_max_new_tokens": limit, "generation": raw, "decoded": parsed,
                "raw_action": parsed["action"], "submitted_action": None, "valid_transition": False}
            receipts.append(step)
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                result["status"] = "deadline_after_model_call"
                terminal = True
                break
            if not parsed["valid_action"]:
                step["status"] = "malformed_or_truncated"
                failures.append({"submitted_action": None, "error": ",".join(parsed["rejection_reasons"])})
                continue
            transform = fresh_intro_action(parsed["action"], goals, enabled=intervention["fresh_intro_names"])
            step.update(transform)
            transformations += int(transform["transform"] != "identity")
            submitted = transform["submitted_action"]
            native = runtime.run_prefix(task, actions + [submitted], transitions)
            native_calls += 1
            native_work += len(actions) + 1
            step.update(status=native["status"], valid_transition=native["valid_transition"],
                native_error=native["native_error"], native_error_type=native["native_error_type"],
                trace_sha256=native.get("trace_sha256"))
            result["native_result"] = native["native_result"]
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                result.update(status="deadline_after_native_call", native_completion_outside_wall_budget=native["python_kernel_complete"])
                terminal = True
                break
            if not native["valid_transition"]:
                failures.append({"submitted_action": submitted, "error": native["native_error"]})
                continue
            actions.append(submitted)
            transitions, goals, accepted = native["transitions"], native["remaining_goals"], True
            if native["python_kernel_complete"]:
                result.update(status="proved", assisted_python_kernel_proof=True, proof_nodes=native["proof_nodes"])
                terminal = True
            elif native["status"] == "kernel_rejection":
                result["status"], terminal = "kernel_rejection", True
            else:
                require(goals, "open assisted proof has no goals")
            break
        if terminal:
            break
        if not accepted:
            result["status"] = "retry_budget"
            break
    result.update(model_calls=len(receipts), retry_model_calls=retry_calls,
        generated_decision_tokens=consumed, accepted_actions=len(actions),
        submitted_actions=native_calls, native_prefix_transitions_requested=native_work,
        fresh_name_transformations=transformations, remaining_goals=goals,
        wall_budget_limited="deadline" in result["status"] or any(row["generation"]["stop_reason"] == "wall_time_budget" for row in receipts))
    result["generation_cost"] = generation_cost(receipts)
    return result


def generation_cost(steps):
    total = {key: 0 for key in ("block_calls", "head_calls", "gate_calls", "decision_tokens")}
    for step in steps:
        raw = step["generation"]
        count = len(raw["decision_ids"])
        total["decision_tokens"] += count
        for key in ("block_calls", "head_calls", "gate_calls"):
            require(type(raw[key]) is list and len(raw[key]) == count
                    and all(type(number) is int and number >= 0 for number in raw[key]), "invalid per-decision inference cost")
            total[key] += sum(raw[key])
    return total


def evaluate_assisted_suite(prepared_dir, admission_path, peano_root, tokenizer, propose, provenance,
                            output_dir, budgets, intervention, *, split, expected_admission_sha256,
                            expected_preparation_sha256, expected_dataset_id, max_wall_seconds):
    """Evaluate the full frozen proof roster; no teacher-forced action metric."""
    require_slurm()
    require(split in {"dev", "test"}, "assisted evaluation requires explicit dev/test split")
    require(type(max_wall_seconds) in {int, float} and math.isfinite(max_wall_seconds) and max_wall_seconds > 0,
            "finite assisted-suite wall budget required")
    checked_intervention(intervention)
    budgets = checked_budgets(budgets, ceiling=budgets)
    manifest, selection, _, _, runtime, before = _suite_inputs(prepared_dir, admission_path, peano_root,
        tokenizer, provenance, split=split, expected_admission_sha256=expected_admission_sha256,
        expected_preparation_sha256=expected_preparation_sha256)
    require(manifest["dataset_id"] == expected_dataset_id, "assisted plan relabelled its corpus")
    before[str(Path(__file__).resolve())] = digest(__file__)
    output = Path(output_dir)
    require(not output.resolve().is_relative_to(Path(peano_root).resolve())
            and not output.resolve().is_relative_to(Path(prepared_dir).resolve()), "assisted output cannot modify inputs")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    counts = {"selected": len(selection["proof_tasks"]), "attempted": 0, "proved": 0, "wall_budget_limited": 0}
    total = {key: 0 for key in ("block_calls", "head_calls", "gate_calls", "decision_tokens")}
    with (output / "proofs.jsonl").open("x", encoding="utf-8") as stream:
        for task in selection["proof_tasks"]:
            result = assisted_rollout(task, propose, runtime, tokenizer, budgets, intervention,
                expected_provenance=provenance, deadline_monotonic=started + max_wall_seconds, budget_ceiling=budgets)
            stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            counts["attempted"] += int(result["model_calls"] > 0)
            counts["proved"] += int(result["assisted_python_kernel_proof"])
            counts["wall_budget_limited"] += int(result["wall_budget_limited"])
            for key in total:
                total[key] += result["generation_cost"][key]
    runtime.assert_unchanged()
    require(all(digest(path) == pin for path, pin in before.items()), "assisted evaluation inputs changed")
    summary = {"format": "latent-c5-assisted-suite-v1", "tier": "T4", "split": split,
        "status": "completed" if counts["wall_budget_limited"] == 0 else "budget_limited",
        "dataset_id": manifest["dataset_id"], "counts": counts, "generation_cost": total,
        "proof_task_ids": selection["proof_task_ids"], "provenance": provenance,
        "intervention": intervention, "intervention_sha256": object_digest(intervention),
        "budgets": budgets, "max_wall_seconds": max_wall_seconds, "elapsed_seconds": time.monotonic() - started,
        "proofs_sha256": digest(output / "proofs.jsonl"), "input_sha256_before_and_after": before,
        "reference_actions_used": 0, "intrinsic_greedy_metric": False, "test_used_for_selection": False,
        "scope": "shared deterministic name interface and bounded checker retries; complete original-target native acceptance required"}
    write_json(output / "summary.json", summary)
    return summary


def training_encounter(task, receipt, runtime, provenance):
    """Recheck exact accepted prefix before exporting a state for train recovery."""
    require(task["split"] == "train" and getattr(runtime, "training_rollout_collection", False),
            "encounter export accepts only explicitly admitted training rollouts")
    validate_provenance(provenance)
    require(receipt["id"] == task["id"] and receipt["task_sha256"] == object_digest(task)
            and receipt["reference_actions_used"] == 0, "encounter lost its admitted original target binding")
    accepted = receipt["actions"][:receipt["accepted_actions"]]
    transitions, goals = [], runtime.initial_state(task)
    for index in range(len(accepted)):
        native = runtime.run_prefix(task, accepted[:index + 1], transitions)
        require(native["valid_transition"], "saved accepted training prefix no longer replays")
        transitions, goals = native["transitions"], native["remaining_goals"]
    require(goals == receipt["remaining_goals"], "encounter state differs from replayed generated prefix")
    return {"format": ENCOUNTER_FORMAT, "session_id": task["session_id"], "split": "train",
        "structural_group": task["structural_group"], "formula": task["formula"],
        "environment_sha256": task["environment_sha256"], "accepted_prefix": accepted,
        "accepted_prefix_length": len(accepted), "encountered_state": goals,
        "generation_provenance": provenance, "task_sha256": object_digest(task),
        "rollout_receipt_sha256": object_digest(receipt), "stopped_status": receipt["status"],
        "solved": bool(receipt.get("autonomous_python_kernel_proof", receipt.get("assisted_python_kernel_proof", False))),
        "verification_native_calls": len(accepted),
        "verification_native_prefix_transitions_requested": len(accepted) * (len(accepted) + 1) // 2,
        "correction_label": None, "scope": "encounter only; no legal action is presumed to be a successful correction"}


def collect_training_rollouts(prepared_dir, admission_path, peano_root, tokenizer, propose, provenance,
                             output_dir, budgets, task_ids, *, expected_admission_sha256,
                             expected_preparation_sha256, expected_dataset_id, max_wall_seconds):
    """Collect intrinsic greedy training encounters from an explicit frozen ID list."""
    require_slurm()
    from .qwen_corpus import prepared_inputs, task_from_episode
    validate_provenance(provenance)
    require(type(max_wall_seconds) in {int, float} and math.isfinite(max_wall_seconds) and max_wall_seconds > 0,
            "finite training-rollout wall budget required")
    budgets = checked_budgets(budgets, ceiling=budgets)
    manifest, selection, rows, metadata, before = prepared_inputs(prepared_dir, split="train",
        expected_admission_sha256=expected_admission_sha256, expected_preparation_sha256=expected_preparation_sha256,
        expected_dataset_id=expected_dataset_id)
    require(selection is None and metadata is not None, "collection requires explicit structural training data")
    before[str(Path(__file__).resolve())] = digest(__file__)
    episodes = group_sessions(rows)
    require(type(task_ids) is list and task_ids and len(set(task_ids)) == len(task_ids)
            and all(key in episodes for key in task_ids), "collection roster is not a unique training-only ID list")
    require(digest(admission_path) == expected_admission_sha256, "collection admission differs from external pin")
    actual_tokenizer = tokenizer_identity(tokenizer)
    actual_tokenizer["file_bytes_verified"] = True
    require(actual_tokenizer == manifest["tokenizer"] and object_digest(actual_tokenizer) == provenance["tokenizer_identity_sha256"],
            "collection tokenizer differs from pinned data")
    runtime = PeanoRuntime(peano_root, admission_path, expected_admission_sha256=expected_admission_sha256,
                           split="train", training_rollout_collection=True)
    require(runtime.before == manifest["peano_source_files_sha256"], "collection checker differs from preparation")
    output = Path(output_dir)
    require(not output.resolve().is_relative_to(Path(peano_root).resolve())
            and not output.resolve().is_relative_to(Path(prepared_dir).resolve()), "collection output cannot modify inputs")
    output.mkdir(parents=True, exist_ok=False)
    started, recorded, skipped, solved, limited, verification_work = time.monotonic(), 0, [], 0, 0, 0
    with (output / "rollouts.jsonl").open("x", encoding="utf-8") as full, (output / "encounters.jsonl").open("x", encoding="utf-8") as encounters:
        for key in task_ids:
            if time.monotonic() >= started + max_wall_seconds:
                skipped.append(key)
                continue
            task = task_from_episode(episodes[key], metadata[key])
            require(task["split"] == "train", "foreign split entered collection")
            receipt = rollout(task, propose, runtime, tokenizer, budgets, expected_provenance=provenance,
                deadline_monotonic=started + max_wall_seconds, budget_ceiling=budgets)
            full.write(json.dumps(receipt, ensure_ascii=False, allow_nan=False) + "\n")
            full.flush()
            encounter = training_encounter(task, receipt, runtime, provenance)
            encounters.write(json.dumps(encounter, ensure_ascii=False, allow_nan=False) + "\n")
            encounters.flush()
            recorded += 1
            solved += int(encounter["solved"])
            limited += int(receipt["wall_budget_limited"])
            verification_work += encounter["verification_native_prefix_transitions_requested"]
    runtime.assert_unchanged()
    require(all(digest(path) == pin for path, pin in before.items()), "training collection inputs changed")
    summary = {"format": "latent-c5-training-rollouts-v1", "tier": "T4", "split": "train",
        "status": "completed" if not skipped and not limited else "budget_limited", "task_ids": task_ids,
        "recorded": recorded, "not_attempted": skipped, "solved": solved, "wall_budget_limited": limited,
        "verification_native_prefix_transitions_requested": verification_work,
        "generation_provenance": provenance, "budgets": budgets, "max_wall_seconds": max_wall_seconds,
        "elapsed_seconds": time.monotonic() - started, "encounters_sha256": digest(output / "encounters.jsonl"),
        "rollouts_sha256": digest(output / "rollouts.jsonl"), "input_sha256_before_and_after": before,
        "correction_labels_created": 0, "test_or_dev_parsed": False}
    write_json(output / "summary.json", summary)
    return summary
