"""Evaluate a hash-pinned selected checkpoint on a new or retained frozen roster.

Candidate destination: latentproof.qwen_eval_frozen. SLURM only. No optimizer is
constructed and no training state is resumed. Architecture and adapter settings
come from the ORIGINAL run receipt, never the new training/evaluation recipe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

from .qwen_data import (ADMISSION_SHA256, decode, digest, load_pinned_tokenizer,
                       object_digest, require, require_slurm, write_json)
from .qwen_corpus import prepared_inputs, sha256_value
from .qwen_eval import checked_budgets, evaluate_suite

PLAN_FORMAT = "latent-qwen-frozen-evaluation-plan-v1"
FORMAT = "latent-qwen-frozen-checkpoint-evaluation-v1"


def source_inventory():
    root = Path(__file__).resolve().parent
    return {path.name: digest(path) for path in sorted(root.glob("*.py"))}


def checkpoint_binding(run_dir, expected):
    """Validate JSON provenance and actual file hashes before loading weights."""
    run_dir = Path(run_dir).resolve()
    require(type(expected) is dict and set(expected) == {"receipt_sha256", "selection_sha256", "checkpoint_sha256"}
            and all(sha256_value(value) for value in expected.values()), "missing external original-checkpoint pins")
    paths = {"receipt_sha256": run_dir / "receipt.json", "selection_sha256": run_dir / "selection.json"}
    require(all(digest(path) == expected[key] for key, path in paths.items()), "original receipt/selection differs from evaluation plan")
    receipt = decode(paths["receipt_sha256"].read_text(encoding="utf-8"))
    selection = decode(paths["selection_sha256"].read_text(encoding="utf-8"))
    # Preserve qwen_train's historical ensure_ascii=True identity encoding while
    # keeping this provenance-only function free of torch/model imports.
    def training_object_digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    require(selection.get("state") == "locked" and selection.get("selected_using") in {"validation-only", "development-only"}
            and selection.get("test_labels_read") is False and selection.get("checkpoint") == "best.pt",
            "only the original locked selected-best checkpoint is eligible")
    require(training_object_digest(receipt["identity"]) == selection["identity_sha256"]
            and training_object_digest(receipt["config"]) == receipt["identity"]["config_sha256"], "original run/config identity changed")
    require(type(selection.get("checkpoint_step")) is int and selection["checkpoint_step"] > 0,
            "invalid original selected checkpoint step")
    path = run_dir / "best.pt"
    require(digest(path) == expected["checkpoint_sha256"] == selection["checkpoint_sha256"], "actual selected checkpoint hash differs")
    paths["checkpoint_sha256"] = path
    return receipt, selection, path, {str(path): expected[key] for key, path in paths.items()}


def checked_plan(plan):
    require(type(plan) is dict and plan.get("format") == PLAN_FORMAT
            and type(plan.get("comparison_id")) is str and plan["comparison_id"], "invalid frozen evaluation plan")
    require(plan.get("purpose") in {"pretraining-frozen-checkpoint", "posttraining-frozen-checkpoint"}, "unregistered comparison purpose")
    data = plan.get("data", {})
    require(set(data) == {"dataset_id", "split", "preparation_sha256", "admission_sha256"}
            and type(data["dataset_id"]) is str and data["dataset_id"]
            and data["split"] in {"val", "dev", "test"}
            and sha256_value(data["preparation_sha256"]) and sha256_value(data["admission_sha256"]), "invalid evaluation corpus pins")
    require(type(plan.get("policies")) is list and plan["policies"], "empty inference-policy roster")
    require(type(plan.get("max_wall_seconds_per_policy")) in {int, float}
            and math.isfinite(plan["max_wall_seconds_per_policy"]) and plan["max_wall_seconds_per_policy"] > 0,
            "missing finite per-policy wall budget")
    require(type(plan.get("micro_batch_size")) is int and plan["micro_batch_size"] > 0, "invalid evaluation microbatch")
    require(type(plan.get("teacher_forced")) is bool, "teacher-forced evaluation must be explicitly enabled/disabled")
    require(type(plan.get("budgets")) is dict, "explicit common finite inference budgets are required")
    checked_budgets(plan["budgets"], ceiling=plan["budgets"])
    if data["split"] == "test":
        require(sha256_value(plan.get("training_protocol_sha256")), "test evaluation requires the already frozen training-protocol digest")
    return plan


def resolve_policies(entries, arm, original_policy, max_recurrence):
    """Never substitute an untrained gate or apply recurrence to vanilla."""
    resolved, labels = [], set()
    for entry in entries:
        require(type(entry) is dict and set(entry) == {"label", "policy"}
                and type(entry["label"]) is str and entry["label"]
                and all(char.isalnum() or char in "-_" for char in entry["label"])
                and entry["label"] not in labels, "invalid/duplicate policy label")
        labels.add(entry["label"])
        policy = dict(original_policy) if entry["policy"] == "original-selected" else entry["policy"]
        require(type(policy) is dict, "inference policy must be explicit or original-selected")
        kind = policy.get("kind")
        if kind == "fixed":
            require(set(policy) == {"kind", "depth"} and type(policy["depth"]) is int
                    and policy["depth"] in {1, 2, 4} and policy["depth"] <= max_recurrence, "unregistered fixed depth")
        elif kind == "learned":
            require(arm == "qwen_adaptive" and set(policy) == {"kind", "quantile"}
                    and type(policy["quantile"]) in {int, float} and 0 < policy["quantile"] <= 1,
                    "learned policy requires a trained adaptive gate")
        elif entry["policy"] == "original-selected" and kind in {"entropy", "kl"}:
            key = "entropy" if kind == "entropy" else "kl"
            require(set(policy) == {"kind", key} and type(policy[key]) in {int, float}
                    and math.isfinite(policy[key]) and policy[key] >= 0,
                    "invalid original selected confidence policy")
        else:
            require(False, "new comparison policies must be fixed 1/2/4 or learned; original selected policy is preserved exactly")
        require(arm != "qwen_vanilla" or policy == {"kind": "fixed", "depth": 1},
                "vanilla is evaluated at trained r1; untrained recurrence is a separate experiment")
        resolved.append({"label": entry["label"], "policy": policy})
    return resolved


def evaluation_context_statistics(manifest, rows, selection, split, max_context_tokens, *, teacher_forced):
    require(type(max_context_tokens) is int and max_context_tokens > 1 and type(teacher_forced) is bool,
            "invalid declared evaluation context")
    require(rows and selection["validation_ids"], "missing evaluation context audit rows")
    by_id = {row["id"]: row for row in rows}
    actual = max(len(row["input_ids"]) for row in rows)
    declared = manifest["splits"][split]["max_retained_sequence_tokens"]
    require(type(declared) is int and actual == declared, "evaluation manifest context maximum differs from actual rows")
    selected = max(len(by_id[key]["input_ids"]) for key in selection["validation_ids"])
    if teacher_forced:
        require(selected <= max_context_tokens, "selected teacher-forced rows exceed the registered evaluation context")
    return {"prepared_split_max_retained_sequence_tokens": actual,
            "selected_teacher_forced_max_sequence_tokens": selected,
            "selected_teacher_forced_rows": len(selection["validation_ids"]),
            "registered_max_context_tokens": max_context_tokens, "teacher_forced_enabled": teacher_forced}


def load_frozen_checkpoint(run_dir, model_path, expected):
    require_slurm()
    import torch
    from .qwen_train import make_model, model_inventory, restore_trainable
    receipt, selection, checkpoint, before = checkpoint_binding(run_dir, expected)
    cfg, original = receipt["config"], receipt["identity"]
    actual_base = model_inventory(model_path)
    require(actual_base == cfg["base_files_sha256"] == original["base"], "base snapshot differs from original training recipe")
    recurrent = [checksum for path, checksum in original["sources_sha256"].items() if Path(path).name == "qwen_recurrent.py"]
    require(len(recurrent) == 1 and recurrent[0] == digest(Path(__file__).with_name("qwen_recurrent.py")),
            "recurrent architecture code differs from the checkpoint's original recipe; no partial compatibility fallback")
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "CUDA/bfloat16 unavailable")
    model = make_model(cfg, model_path, original["arm"])
    expected_names = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    require(expected_names == receipt["trainable_names"], "original trainable parameter names/order differ")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
    require(saved["identity"] == original and saved["step"] == selection["checkpoint_step"]
            and saved["policy"] == selection["halting_policy"] and saved["val_loss"] == selection["best_validation_loss"],
            "loaded weights do not have the original selected-best identity/step/policy/loss")
    require(set(saved["trainable"]) == set(expected_names), "checkpoint parameter set changed")
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            require(saved["trainable"][name].shape == parameter.shape
                    and saved["trainable"][name].dtype == parameter.dtype,
                    "checkpoint parameter shape/dtype differs from original architecture")
    restore_trainable(model, saved["trainable"])
    del saved
    model.eval()
    require(model_inventory(model_path) == actual_base and all(digest(path) == checksum for path, checksum in before.items()),
            "base/checkpoint/provenance changed during restore")
    binding = {"original_run_id": Path(run_dir).name, "original_campaign_id": cfg["campaign_id"],
        "arm": original["arm"], "seed": original["seed"], "checkpoint_step": selection["checkpoint_step"],
        "checkpoint_path": str(checkpoint.resolve()), "checkpoint_role": "original-selected-best",
        "checkpoint_sha256": digest(checkpoint), "actual_checkpoint_rehashed_after_restore": True,
        "receipt_sha256": expected["receipt_sha256"], "selection_sha256": expected["selection_sha256"],
        "original_selected_policy": selection["halting_policy"], "original_selection_criterion": selection["selected_using"],
        "original_identity": original, "original_config": cfg, "original_identity_sha256": selection["identity_sha256"],
        "original_training_data_manifest": receipt["data_manifest"], "original_source_inventory_sha256": object_digest(original["sources_sha256"]),
        "recurrent_architecture_sha256": recurrent[0], "trainable_names": expected_names,
        "base_inventory_sha256": actual_base, "optimizer_constructed": False}
    return model, binding, before


def evaluate_frozen(args):
    require_slurm()
    require(digest(args.plan) == args.plan_sha256, "evaluation plan changed from externally registered hash")
    plan = checked_plan(decode(args.plan.read_text(encoding="utf-8")))
    plan_bytes = {str(args.plan.resolve()): args.plan_sha256}
    data = plan["data"]
    if data["split"] == "test":
        require(args.training_protocol is not None and digest(args.training_protocol) == plan["training_protocol_sha256"],
                "held-out evaluation requires the actual previously frozen training protocol file")
        plan_bytes[str(args.training_protocol.resolve())] = plan["training_protocol_sha256"]
    manifest, selection, rows, metadata, before = prepared_inputs(args.data, split=data["split"],
        expected_admission_sha256=data["admission_sha256"], expected_preparation_sha256=data["preparation_sha256"],
        expected_dataset_id=None if data["admission_sha256"] == ADMISSION_SHA256 else data["dataset_id"])
    require(selection is not None, "frozen evaluation cannot use the training split")
    require(data["dataset_id"] == manifest.get("dataset_id", "campaign2-admitted-compact-state"), "evaluation cannot relabel the corpus")
    context_statistics = evaluation_context_statistics(manifest, rows, selection, data["split"],
        plan["budgets"]["max_context_tokens"], teacher_forced=plan["teacher_forced"])
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    sources = source_inventory()
    model, checkpoint, restored_inputs = load_frozen_checkpoint(args.run, args.model, plan["checkpoint"])
    tokenizer, tokenizer_info = load_pinned_tokenizer(args.model)
    require(tokenizer_info == manifest["tokenizer"], "evaluation tokenizer differs from prepared corpus")
    policies = resolve_policies(plan["policies"], checkpoint["arm"], checkpoint["original_selected_policy"], checkpoint["original_config"]["max_recurrence"])
    from .qwen_train import generate_action, evaluate_policy_grid
    from .qwen_train import atomic_json, now
    import torch
    eval_cfg = {**checkpoint["original_config"], "micro_batch_size": plan["micro_batch_size"],
                "max_new_tokens": plan["budgets"]["max_new_tokens"], "max_sequence_length": plan["budgets"]["max_context_tokens"]}
    provenance_inputs = {**before, **plan_bytes, **restored_inputs}
    write_json(args.out / "evaluation-receipt.json", {"format": FORMAT, "state": "running", "tier": "T4",
        "slurm_job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster, "plan": plan,
        "evaluation_plan_sha256": args.plan_sha256, "checkpoint": checkpoint, "resolved_policies": policies,
        "context_statistics": context_statistics,
        "evaluation_source_inventory": sources, "evaluation_source_inventory_sha256": object_digest(sources),
        "device": torch.cuda.get_device_name(0), "input_sha256_before": provenance_inputs,
        "test_policy": "frozen protocol and policies; no model/checkpoint selection from this evaluation"})
    status = {"run_id": args.out.name, "campaign_id": plan["comparison_id"], "role": "previous-checkpoint-baseline" if plan["purpose"] == "pretraining-frozen-checkpoint" else "new-checkpoint-comparison",
        "arm": checkpoint["arm"], "seed": checkpoint["seed"], "cluster": args.cluster, "job_id": os.environ["SLURM_JOB_ID"],
        "state": "evaluating", "step": 0, "max_steps": 0, "checkpoint_step": checkpoint["checkpoint_step"],
        "checkpoint_sha256": checkpoint["checkpoint_sha256"], "checkpoint_role": checkpoint["checkpoint_role"],
        "original_run_id": checkpoint["original_run_id"], "original_campaign_id": checkpoint["original_campaign_id"],
        "original_selected_policy": checkpoint["original_selected_policy"], "updated_at": now(), "history": [],
        "metrics": {"proof_acceptance": None, "tactic_validity": None, "gen_exact_match": None},
        "notes": ["Frozen selected checkpoint evaluation; no optimizer or training updates.", "Selected target denominators include deadline-unattempted targets."]}
    atomic_json(args.out / "status.json", status)
    records = []
    by_id = {row["id"]: row for row in rows}
    for entry in policies:
        label, policy = entry["label"], entry["policy"]
        policy_started = time.monotonic()
        teacher_forced = None
        if plan["teacher_forced"]:
            teacher_forced, teacher_seconds = evaluate_policy_grid(model, [by_id[key] for key in selection["validation_ids"]],
                eval_cfg, [policy], tokenizer.pad_token_id)
        else:
            teacher_seconds = 0.
        provenance = {"run_id": checkpoint["original_run_id"], "checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "tokenizer_identity_sha256": manifest["tokenizer_identity_sha256"], "source_inventory_sha256": object_digest(sources),
            "policy": policy, "model_vocab_size": model.causal_lm.config.vocab_size,
            "checkpoint_step": checkpoint["checkpoint_step"], "checkpoint_role": "original-selected-best",
            "evaluation_plan_sha256": args.plan_sha256, "original_identity_sha256": checkpoint["original_identity_sha256"]}
        def propose(prompt, *, max_new_tokens, deadline_monotonic=None):
            return generate_action(model, tokenizer, prompt, policy, eval_cfg, max_new_tokens=max_new_tokens,
                                   deadline=deadline_monotonic, provenance=provenance)
        native = evaluate_suite(args.data, args.data / "admission.json", args.peano_root, tokenizer, propose, provenance,
            args.out / label, budgets=plan["budgets"], max_wall_seconds=plan["max_wall_seconds_per_policy"],
            extra_input_hashes=provenance_inputs, split=data["split"], expected_admission_sha256=data["admission_sha256"],
            expected_preparation_sha256=data["preparation_sha256"], budget_ceiling=plan["budgets"],
            wall_seconds_ceiling=plan["max_wall_seconds_per_policy"], selection_usage="frozen-checkpoint-comparison")
        record = {"label": label, "policy": policy, "checkpoint_step": checkpoint["checkpoint_step"],
            "teacher_forced": teacher_forced, "teacher_forced_seconds": teacher_seconds,
            "native_summary_path": label + "/summary.json", "native_summary_sha256": digest(args.out / label / "summary.json"),
            "status": native["status"], "action_counts": native["action_counts"], "proof_counts": native["proof_counts"],
            "action_rates_all_selected": native["action_rates_all_selected"], "proof_success_rate_all_selected": native["proof_success_rate_all_selected"],
            "evaluation_contract": native["evaluation_contract"], "generation_ids": native["generation_ids"], "proof_task_ids": native["proof_task_ids"],
            "stratified_results": native.get("stratified_results", []), "elapsed_seconds": time.monotonic() - policy_started}
        records.append(record)
        write_json(args.out / (label + "-result.json"), record)
        ac, pc = native["action_counts"], native["proof_counts"]
        status.update(state="evaluating", updated_at=now(), selected_policy=policy, evaluated_policy_label=label,
            evaluation_contract=native["evaluation_contract"], stratified_results=native.get("stratified_results", []),
            generation_step=checkpoint["checkpoint_step"], frozen_policy_results=records,
            metrics={"proof_acceptance": native["proof_success_rate_all_selected"],
                     "tactic_validity": native["action_rates_all_selected"]["valid_transition"],
                     "gen_exact_match": native["action_rates_all_selected"]["exact_match"],
                     "generation_examples": ac.get("attempted", 0), "generation_total": ac["selected"],
                     "proof_attempted": pc.get("attempted", 0), "proof_total": pc["selected"],
                     "evaluation_complete": native["status"] == "completed", "elapsed_seconds": time.monotonic() - started})
        atomic_json(args.out / "status.json", status)
    require(all(digest(path) == checksum for path, checksum in provenance_inputs.items()) and source_inventory() == sources,
            "frozen evaluation inputs or implementation changed")
    summary = {"format": FORMAT, "status": "completed" if all(row["status"] == "completed" for row in records) else "budget_limited",
        "tier": "T4", "comparison_id": plan["comparison_id"], "purpose": plan["purpose"],
        "slurm_job_id": os.environ["SLURM_JOB_ID"], "cluster": args.cluster, "data": data,
        "evaluation_plan_sha256": args.plan_sha256, "checkpoint": checkpoint,
        "context_statistics": context_statistics,
        "evaluation_source_inventory_sha256": object_digest(sources), "policies": records,
        "input_sha256_before_and_after": provenance_inputs, "elapsed_seconds": time.monotonic() - started,
        "test_used_for_model_selection": False, "optimizer_constructed": False,
        "comparison_scope": "matched frozen rosters/budgets required across runs; action transition validity is not autonomous proof success"}
    write_json(args.out / "summary.json", summary)
    status.update(state="evaluated", evaluation_outcome=summary["status"], updated_at=now(),
                  completion_scope="Evaluation receipt complete; proof success and deadline coverage are separate metrics")
    atomic_json(args.out / "status.json", status)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "run", "model", "data", "peano-root", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--training-protocol", type=Path)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    args = parser.parse_args()
    require_slurm()
    require(not args.out.exists(), "evaluation output already exists; do not overwrite a prior evaluation")
    for source in (args.run, args.model, args.data, args.peano_root):
        require(not args.out.resolve().is_relative_to(source.resolve()), "evaluation output must be separate from frozen inputs")
    try:
        evaluate_frozen(args)
    except Exception as exc:
        if args.out.exists() and not (args.out / "summary.json").exists():
            write_json(args.out / "FAILED.json", {"format": FORMAT, "status": "infrastructure-abort", "summary_valid": False,
                       "error_type": type(exc).__name__, "error": str(exc), "slurm_job_id": os.environ["SLURM_JOB_ID"]})
            status_path = args.out / "status.json"
            if status_path.exists():
                from .qwen_train import atomic_json, now
                status = decode(status_path.read_text(encoding="utf-8"))
                status.update(state="failed", updated_at=now(), error=f"{type(exc).__name__}: {exc}")
                atomic_json(status_path, status)
        raise


if __name__ == "__main__":
    main()
