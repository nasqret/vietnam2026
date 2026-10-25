"""Run a pinned assisted evaluation or train-only rollout plan on SLURM."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from .qwen_data import digest, load_pinned_tokenizer, object_digest, require, require_slurm, write_json
from .qwen_corpus import sha256_value
from .qwen_eval import checked_budgets
from .qwen_eval_frozen import load_frozen_checkpoint, resolve_policies, source_inventory
from .campaign5_inference import checked_intervention, collect_training_rollouts, evaluate_assisted_suite

FORMAT = "latent-c5-inference-plan-v1"


def checked_plan(value):
    fields = {"format", "comparison_id", "mode", "checkpoint", "data", "policy", "budgets",
              "max_wall_seconds", "intervention", "task_ids", "training_protocol_sha256",
              "evaluation_source_inventory_sha256", "test_used_for_model_selection"}
    require(type(value) is dict and set(value) == fields and value["format"] == FORMAT,
            "invalid exact Campaign 5 inference plan")
    require(type(value["comparison_id"]) is str and value["comparison_id"]
            and value["mode"] in {"assisted-evaluation", "training-rollouts"}, "invalid inference plan identity/mode")
    data = value["data"]
    require(type(data) is dict and set(data) == {"dataset_id", "split", "preparation_sha256", "admission_sha256"}
            and type(data["dataset_id"]) is str and data["dataset_id"]
            and all(sha256_value(data[key]) for key in ("preparation_sha256", "admission_sha256")),
            "invalid explicit inference corpus pins")
    require(sha256_value(value["training_protocol_sha256"]) and sha256_value(value["evaluation_source_inventory_sha256"])
            and value["test_used_for_model_selection"] is False, "inference plan lacks immutable protocol/source pins")
    checked_budgets(value["budgets"], ceiling=value["budgets"])
    require(type(value["max_wall_seconds"]) is int and 0 < value["max_wall_seconds"] <= 86400,
            "finite bounded inference wall budget required")
    if value["mode"] == "assisted-evaluation":
        require(data["split"] in {"dev", "test"} and value["task_ids"] is None,
                "assisted evaluation requires the complete frozen dev/test roster")
        checked_intervention(value["intervention"])
    else:
        ids = value["task_ids"]
        require(data["split"] == "train" and value["intervention"] is None
                and type(ids) is list and ids and all(type(key) is str and key for key in ids)
                and len(ids) == len(set(ids)), "training collection requires unique train IDs and intrinsic inference")
    return value


def run(args):
    require_slurm()
    require(digest(args.plan) == args.plan_sha256, "inference plan differs from its external pin")
    plan = checked_plan(json.loads(args.plan.read_text()))
    require(digest(args.training_protocol) == plan["training_protocol_sha256"], "registered training/inference protocol changed")
    inventory = source_inventory()
    require(object_digest(inventory) == plan["evaluation_source_inventory_sha256"], "frozen evaluation source inventory changed")
    require(not args.out.exists(), "inference output must be a new directory")
    for source in (args.run, args.data, args.model, args.peano_root):
        require(not args.out.resolve().is_relative_to(source.resolve()), "output cannot be inside any input directory")
    from .qwen_train import generate_action, atomic_json, now
    model, checkpoint, before = load_frozen_checkpoint(args.run, args.model, plan["checkpoint"])
    tokenizer, _ = load_pinned_tokenizer(args.model)
    policy = resolve_policies([{"label": "registered", "policy": plan["policy"]}], checkpoint["arm"],
        checkpoint["original_selected_policy"], checkpoint["original_config"]["max_recurrence"])[0]["policy"]
    cfg = {**checkpoint["original_config"], "max_new_tokens": plan["budgets"]["max_new_tokens"],
           "max_sequence_length": plan["budgets"]["max_context_tokens"]}
    from .qwen_data import tokenizer_identity
    identity = tokenizer_identity(tokenizer)
    identity["file_bytes_verified"] = True
    provenance = {"run_id": args.out.name, "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "tokenizer_identity_sha256": object_digest(identity), "source_inventory_sha256": object_digest(inventory),
        "policy": policy, "model_vocab_size": model.causal_lm.config.vocab_size,
        "checkpoint_role": "original-selected-best", "checkpoint_step": checkpoint["checkpoint_step"],
        "original_identity_sha256": checkpoint["original_identity_sha256"]}
    def propose(prompt, *, max_new_tokens, deadline_monotonic=None):
        return generate_action(model, tokenizer, prompt, policy, cfg, max_new_tokens=max_new_tokens,
                               deadline=deadline_monotonic, provenance=provenance)
    common = dict(expected_admission_sha256=plan["data"]["admission_sha256"],
        expected_preparation_sha256=plan["data"]["preparation_sha256"],
        expected_dataset_id=plan["data"]["dataset_id"], max_wall_seconds=plan["max_wall_seconds"])
    started = time.monotonic()
    if plan["mode"] == "assisted-evaluation":
        summary = evaluate_assisted_suite(args.data, args.data / "admission.json", args.peano_root,
            tokenizer, propose, provenance, args.out, plan["budgets"], plan["intervention"],
            split=plan["data"]["split"], **common)
    else:
        summary = collect_training_rollouts(args.data, args.data / "admission.json", args.peano_root,
            tokenizer, propose, provenance, args.out, plan["budgets"], plan["task_ids"],
            **common)
    require(all(digest(path) == pin for path, pin in before.items()) and source_inventory() == inventory
            and digest(args.plan) == args.plan_sha256 and digest(args.training_protocol) == plan["training_protocol_sha256"],
            "inference plan, checkpoint or source changed during execution")
    write_json(args.out / "runner-receipt.json", {"format": FORMAT, "state": summary["status"],
        "plan_sha256": args.plan_sha256, "plan": plan, "checkpoint": checkpoint,
        "generation_provenance": provenance, "evaluation_source_inventory": inventory,
        "cluster": args.cluster, "elapsed_seconds": time.monotonic() - started,
        "summary_sha256": digest(args.out / "summary.json"), "completed_at": now()})
    atomic_json(args.out / "status.json", {"run_id": args.out.name, "campaign_id": plan["comparison_id"],
        "state": summary["status"], "mode": plan["mode"], "split": plan["data"]["split"],
        "arm": checkpoint["arm"], "seed": checkpoint["seed"], "updated_at": now(),
        "checkpoint_step": checkpoint["checkpoint_step"], "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "metrics": summary.get("counts", {key: summary[key] for key in ("recorded", "solved") if key in summary}),
        "intrinsic_greedy_metric": plan["mode"] == "training-rollouts"})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "training-protocol", "run", "data", "model", "peano-root", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
