"""Qwen recurrent LoRA training with pinned corpora; WMI/Helios SLURM only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import signal
import time
import traceback

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
import transformers
import peft
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

from .campaign_data import ExampleStream, digest
from .qwen_recurrent import QwenRecurrentLM


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def model_inventory(path):
    names = ("config.json", "generation_config.json", "tokenizer_config.json", "tokenizer.json",
             "vocab.json", "merges.txt", "model.safetensors")
    return {name: digest(Path(path) / name) for name in names}


def make_model(cfg, path, arm, device="cuda"):
    torch.use_deterministic_algorithms(bool(cfg.get("deterministic_algorithms", True)))
    if transformers.__version__ != "4.53.3" or peft.__version__ != "0.16.0":
        raise RuntimeError("Qwen recurrence requires Transformers4.53.3 and PEFT0.16.0")
    base = AutoModelForCausalLM.from_pretrained(str(path), local_files_only=True,
        torch_dtype=torch.bfloat16, attn_implementation="sdpa", trust_remote_code=False)
    base.config.use_cache = False
    adapted = get_peft_model(base, LoraConfig(r=cfg["lora_rank"], lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"], target_modules=cfg["lora_targets"],
        bias="none", task_type="CAUSAL_LM"))
    model = QwenRecurrentLM(adapted, prelude_layers=cfg["prelude_layers"],
        core_layers=cfg["core_layers"], max_recurrence=cfg["max_recurrence"],
        checkpoint_layers=True, head_chunk_size=cfg["head_chunk_size"],
        extra_pass_scale=cfg["extra_pass_scale"], max_extra_pass_scale=cfg["max_extra_pass_scale"],
        train_gate=arm == "qwen_adaptive", train_damping=arm != "qwen_vanilla")
    return model.to(device)


def collate(rows, pad, device="cuda"):
    length = max(len(row["input_ids"]) for row in rows)
    tokens = torch.full((len(rows), length), pad, dtype=torch.long, device=device)
    labels = torch.full_like(tokens, -100)
    mask = torch.zeros_like(tokens)
    for i, row in enumerate(rows):
        n = len(row["input_ids"])
        tokens[i, :n] = torch.tensor(row["input_ids"], dtype=torch.long, device=device)
        labels[i, :n] = torch.tensor(row["labels"], dtype=torch.long, device=device)
        mask[i, :n] = 1
    positions = (mask.cumsum(-1) - 1).masked_fill(mask == 0, 0)
    return {"input_ids": tokens, "labels": labels, "attention_mask": mask, "position_ids": positions}


def policy_grid(arm):
    if arm == "qwen_vanilla":
        return [{"kind": "fixed", "depth": 1}]
    policies = [{"kind": "fixed", "depth": r} for r in (1, 2, 4)]
    if arm == "qwen_adaptive":
        policies += [{"kind": "learned", "quantile": q} for q in (.25, .5, .75, .9)]
    else:
        policies += [{"kind": "entropy", "entropy": x} for x in (.05, .15, .3)]
        policies += [{"kind": "kl", "kl": x} for x in (.001, .01)]
    return policies


def policy_key(policy):
    return json.dumps(policy, sort_keys=True)


@torch.inference_mode()
def evaluate_policy_grid(model, rows, cfg, policies, pad):
    """Score explicit policies without selecting one or touching test/train state.

    Block counts describe each policy's inference path. The all-depth validation
    probe itself executes extra coda/readouts; elapsed time is measured separately.
    """
    model.eval()
    if not rows or not policies or len({policy_key(p) for p in policies}) != len(policies):
        raise ValueError("Policy evaluation requires nonempty data and distinct explicit policies")
    stop_depth = max(p["depth"] for p in policies) if all(p["kind"] == "fixed" for p in policies) else cfg["max_recurrence"]
    accum = {policy_key(p): {"policy": p, "ce": 0., "correct": 0, "tokens": 0,
                            "depth": 0., "blocks": 0.} for p in policies}
    started = time.monotonic()
    for start in range(0, len(rows), cfg["micro_batch_size"]):
        inputs = collate(rows[start:start + cfg["micro_batch_size"]], pad)
        taken, survival = {}, None
        with torch.autocast("cuda", dtype=torch.bfloat16):
            for probe in model.iter_supervised(**inputs):
                depth, ce, correct = probe["depth"], probe["ce"], probe["correct"]
                if survival is None:
                    survival = torch.ones_like(ce, dtype=torch.float32)
                    taken = {policy_key(p): torch.zeros_like(ce, dtype=torch.bool) for p in policies}
                if probe.get("hazard") is not None:
                    survival = survival * (1 - probe["hazard"])
                for policy in policies:
                    kind, key = policy["kind"], policy_key(policy)
                    if kind == "fixed":
                        stop = torch.full_like(ce, depth == policy["depth"], dtype=torch.bool)
                    elif depth == cfg["max_recurrence"]:
                        stop = torch.ones_like(ce, dtype=torch.bool)
                    elif kind == "learned":
                        stop = 1 - survival >= policy["quantile"]
                    elif kind == "entropy":
                        stop = probe["entropy"] <= policy["entropy"]
                    else:
                        # First pass has no preceding distribution.
                        stop = (probe["kl"] <= policy["kl"]) if depth > 1 else torch.zeros_like(ce, dtype=torch.bool)
                    take = stop & ~taken[key]
                    taken[key] |= take
                    n = int(take.sum())
                    entry = accum[key]
                    entry["ce"] += float(ce[take].sum())
                    entry["correct"] += int(correct[take].sum())
                    entry["tokens"] += n
                    entry["depth"] += depth * n
                    calls = cfg["prelude_layers"] + depth * cfg["core_layers"] + (28 - cfg["prelude_layers"] - cfg["core_layers"]) * (1 if kind == "fixed" else depth)
                    entry["blocks"] += n * calls
                if depth == stop_depth:
                    break
        if not taken or any(not bool(mask.all()) for mask in taken.values()):
            raise RuntimeError("A validation policy did not choose one exit per supervised target")
    records = [{"policy": a["policy"], "loss": a["ce"] / a["tokens"],
                "token_accuracy": a["correct"] / a["tokens"], "tokens": a["tokens"],
                "mean_recurrence": a["depth"] / a["tokens"], "mean_block_calls": a["blocks"] / a["tokens"],
                "cost_scope": "projected policy inference block calls per supervised token; validation probes execute additional readouts"}
               for a in accum.values()]
    return records, time.monotonic() - started


def validate(model, rows, cfg, arm, pad):
    if cfg.get("campaign5") is not None:
        # The proof-selection policy is preregistered, never chosen from this
        # checkpoint's token loss or test outcomes.
        policy = cfg["campaign5"]["selection_policies"][arm]
        records, duration = evaluate_policy_grid(model, rows, cfg, [policy], pad)
        return records[0], records, duration
    records, duration = evaluate_policy_grid(model, rows, cfg, policy_grid(arm), pad)
    baseline = next(a["loss"] for a in records if a["policy"] == {"kind": "fixed", "depth": 1 if arm == "qwen_vanilla" else 4})
    eligible = [a for a in records if a["loss"] <= baseline + cfg["policy_loss_tolerance"]]
    selected = min(eligible, key=lambda a: (a["mean_block_calls"], a["loss"], policy_key(a["policy"])))
    return selected, records, duration


@torch.inference_mode()
def generate_action(model, tokenizer, prompt, policy, cfg, *, max_new_tokens=None, deadline=None, provenance=None):
    sequence = tokenizer.encode(prompt, add_special_tokens=False)
    prompt_length = len(sequence)
    limit = min(cfg["max_new_tokens"] if max_new_tokens is None else max_new_tokens,
                cfg["max_sequence_length"] - len(sequence))
    decisions, depths, blocks, heads, gates, readouts = [], [], [], [], [], []
    reason = "context_limit" if len(sequence) + (cfg["max_new_tokens"] if max_new_tokens is None else max_new_tokens) > cfg["max_sequence_length"] else "token_budget"
    special_ids = set(tokenizer.all_special_ids)
    started = time.monotonic()
    for _ in range(max(0, limit)):
        if deadline is not None and time.monotonic() >= deadline:
            reason = "wall_time_budget"
            break
        tokens = torch.tensor([sequence], dtype=torch.long, device="cuda")
        with torch.autocast("cuda", dtype=torch.bfloat16):
            output = model.next_logits(input_ids=tokens, policy=policy)
        token = int(output["logits"].argmax(-1).item())
        decisions.append(token)
        depths.append(int(output["depth"]))
        blocks.append(int(output["block_calls"]))
        heads.append(int(output["head_calls"]))
        gates.append(int(output["gate_calls"]))
        readouts.append(int(output["readouts"]))
        if token == tokenizer.eos_token_id:
            reason = "eos"
            break
        if token in special_ids or token >= len(tokenizer):
            reason = "invalid_special_token"
            break
        sequence.append(token)
    return {"format": "latent-qwen-bpe-generation-v1", "model_vocab_size": model.causal_lm.config.vocab_size, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt_tokens": prompt_length, "max_context_tokens": cfg["max_sequence_length"], "max_new_tokens": max_new_tokens if max_new_tokens is not None else cfg["max_new_tokens"], "decision_ids": decisions, "stop_reason": reason, "eos": reason == "eos",
            "recurrence_depths": depths, "block_calls": blocks, "head_calls": heads, "gate_calls": gates, "readouts": readouts,
            "policy": policy, "seconds": time.monotonic() - started,
            "provenance": provenance if provenance is not None else {"model_tokenizer": "Qwen3-pinned-BPE", "max_new_tokens": max_new_tokens or cfg["max_new_tokens"],
                           "max_sequence_length": cfg["max_sequence_length"], "use_cache": False}}


def trainable_state(model):
    # Store only adapters and learned recurrence parameters. Frozen base weights
    # are bound by their independent immutable inventory, never recopied per run.
    return {name: p.detach().cpu().clone() for name, p in model.named_parameters() if p.requires_grad}


def restore_trainable(model, state):
    expected = {name: p for name, p in model.named_parameters() if p.requires_grad}
    if expected.keys() != state.keys():
        raise ValueError("Trainable checkpoint parameter names differ")
    with torch.no_grad():
        for name, parameter in expected.items():
            if parameter.shape != state[name].shape:
                raise ValueError("Trainable checkpoint shape differs")
            parameter.copy_(state[name].to(parameter.device))


def save_torch(path, value):
    temporary = Path(str(path) + ".tmp")
    torch.save(value, temporary)
    temporary.replace(path)


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("All Qwen campaign execution requires WMI/Helios SLURM")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    parser.add_argument("--peano-root", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--stop-after-step", type=int)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if args.arm not in cfg["arms"]:
        raise ValueError("Unregistered comparison arm")
    from .campaign5_training import checked_options, stage_at, optimizer_groups, proof_candidate, candidate_is_better, graceful_stop, BalancedExampleStream
    campaign5 = checked_options(cfg, args.arm)
    if args.smoke and campaign5 is not None:
        raise ValueError("Campaign 5 uses an explicit preregistered tiny recipe, not the legacy smoke override")
    if args.smoke:
        cfg.update(steps=2, effective_batch_size=2, micro_batch_size=1, eval_every=2,
                   log_every=1, checkpoint_every=2, generation_every=2, validation_rows=2,
                   generation_rows=2, proof_tasks=1, proof_max_actions=2, max_new_tokens=8,
                   train_seconds_limit=900, evaluation_seconds_limit=120)
    args.out.mkdir(parents=True, exist_ok=True)
    status = {"run_id": args.out.name, "campaign_id": cfg["campaign_id"], "arm": args.arm,
              "seed": args.seed, "cluster": args.cluster, "job_id": os.environ["SLURM_JOB_ID"],
              "state": "initializing", "step": 0, "max_steps": cfg["steps"], "updated_at": now(),
              "metrics": {"proof_acceptance": None, "tactic_validity": None}, "history": [],
              "notes": [f"Qwen BPE and compact proof-state condition; compare within {cfg['campaign_id']}.",
                        "Development validation and Python-kernel proof checks; no native Lean result."],
              "smoke": args.smoke}
    checkpoint = args.out / "last.pt"
    resuming = checkpoint.exists()
    if not resuming:
        atomic_json(args.out / "status.json", status)
    stopped = [False]
    signal.signal(signal.SIGTERM, lambda *_: stopped.__setitem__(0, True))
    signal.signal(signal.SIGUSR1, lambda *_: stopped.__setitem__(0, True))
    try:
        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("CUDA/bfloat16 unavailable")
        torch.set_num_threads(min(4, int(os.environ.get("SLURM_CPUS_PER_TASK", 4))))
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
        inventory = model_inventory(args.model)
        if inventory != cfg["base_files_sha256"]:
            raise ValueError("Base weight identity differs from pinned snapshot")
        from .qwen_data import load_tokenized, deterministic_evaluation_ids, tokenizer_identity, ADMISSION_SHA256
        data_contract = cfg.get("data_contract")
        if data_contract is None:
            development_split, admission_sha256, preparation_sha256 = "val", ADMISSION_SHA256, None
            data_manifest = json.loads((args.data / "preparation.json").read_text())
            if data_manifest["source_admission_sha256"] != ADMISSION_SHA256 or data_manifest["test"]["parsed"]:
                raise ValueError("Unadmitted source or test exposure")
            train = load_tokenized(args.data / "train.jsonl", data_manifest, "train")
            val_all = load_tokenized(args.data / "val.jsonl", data_manifest, "val")
            dataset_hashes = {name: digest(args.data / name) for name in ("preparation.json", "train.jsonl", "val.jsonl", "selection.json")}
            if dataset_hashes["selection.json"] != data_manifest["selection_sha256"]:
                raise ValueError("Frozen validation selection changed")
            for split in ("train", "val"):
                if data_manifest["splits"][split]["output_sha256"] != dataset_hashes[split + ".jsonl"]:
                    raise ValueError("Prepared data changed")
            selection = deterministic_evaluation_ids(val_all, validation_rows=cfg["validation_rows"], generation_rows=cfg["generation_rows"])
        else:
            from .qwen_corpus import prepared_inputs
            if set(data_contract) != {"dataset_id", "preparation_sha256", "admission_sha256", "development_split"} or data_contract["development_split"] != "dev":
                raise ValueError("New training requires an explicit pinned train/dev corpus contract")
            development_split, admission_sha256, preparation_sha256 = "dev", data_contract["admission_sha256"], data_contract["preparation_sha256"]
            data_args = {"expected_admission_sha256": admission_sha256, "expected_preparation_sha256": preparation_sha256,
                         "expected_dataset_id": data_contract["dataset_id"]}
            data_manifest, _, train, _, train_hashes = prepared_inputs(args.data, split="train", **data_args)
            dev_manifest, frozen_selection, val_all, _, dev_hashes = prepared_inputs(args.data, split="dev", **data_args)
            if dev_manifest != data_manifest:
                raise ValueError("Prepared manifest changed between train/dev reads")
            dataset_hashes = {str(Path(path).relative_to(args.data.resolve())): checksum for path, checksum in {**train_hashes, **dev_hashes}.items()}
            selection = {"validation_ids": frozen_selection["validation_ids"], "generation_ids": frozen_selection["generation_ids"]}
            if args.smoke:
                # Explicit infrastructure-only subset, never a reported corpus evaluation.
                selection = {key: value[:cfg["validation_rows"] if key == "validation_ids" else cfg["generation_rows"]] for key, value in selection.items()}
            elif (len(selection["validation_ids"]) != cfg["validation_rows"]
                  or len(selection["generation_ids"]) != cfg["generation_rows"]
                  or (len(frozen_selection["proof_tasks"]) != cfg["proof_tasks"] if campaign5 is None else len(frozen_selection["proof_tasks"]) < cfg["proof_tasks"])):
                raise ValueError("Training config disagrees with the frozen development roster")
        from .qwen_corpus import validate_training_context
        validate_training_context(data_manifest, {"train": train, development_split: val_all}, cfg["max_sequence_length"])
        if not args.smoke and max(data_manifest["splits"][split]["max_supervised_tokens_including_eos"] for split in ("train", development_split)) > cfg["max_new_tokens"]:
            raise ValueError("Generation token budget cannot cover admitted train/development reference actions plus EOS")
        by_id = {r["id"]: r for r in val_all}
        val = [by_id[i] for i in selection["validation_ids"]]
        gen_rows = [by_id[i] for i in selection["generation_ids"]]
        tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, trust_remote_code=False)
        if tokenizer_identity(tokenizer, args.model) != data_manifest["tokenizer"]:
            raise ValueError("Live tokenizer differs from prepared data")
        pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        model = make_model(cfg, args.model, args.arm)
        trainable = [p for p in model.parameters() if p.requires_grad]
        groups = trainable if campaign5 is None else optimizer_groups(model, campaign5, cfg["learning_rate"])
        optimizer = torch.optim.AdamW(groups, lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"], betas=(.9, .95))
        balanced_sampling = campaign5 is not None and campaign5.get("sampling", {"kind": "permutation"})["kind"] == "family_phase_balanced"
        stream = BalancedExampleStream(train, args.seed) if balanced_sampling else ExampleStream(train, args.seed)
        depth_rng = random.Random(args.seed + 8071)
        sources = {str(p): digest(p) for p in sorted(Path("src/latentproof").glob("*.py"))}
        identity = {"arm": args.arm, "seed": args.seed, "config_sha256": object_digest(cfg),
                    "data": dataset_hashes, "base": inventory, "sources_sha256": sources,
                    "transformers": transformers.__version__, "peft": peft.__version__,
                    "torch": str(torch.__version__), "cuda": torch.version.cuda,
                    "device": torch.cuda.get_device_name(0), "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                    "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}
        receipt = {"identity": identity, "config": cfg, "created_at": now(),
                   "parameters": sum(p.numel() for p in model.parameters()),
                   "trainable_parameters": sum(p.numel() for p in trainable),
                   "trainable_names": [name for name, p in model.named_parameters() if p.requires_grad],
                   "training_rows": len(train), "validation_selection": selection,
                   "python": platform.python_version(), "platform": platform.platform(),
                   "data_manifest": data_manifest}
        if campaign5 is not None:
            receipt["campaign5"] = {"controls": campaign5,
                "initialization": "fresh-pinned-base-LoRA; only exact same-identity resume is supported",
                "training_cost_scope": "measured training wall time plus logical forward calls; backward recomputation excluded from call counts",
                "proof_selection_roster": frozen_selection["proof_task_ids"][:cfg["proof_tasks"]],
                "proof_selection_roster_sha256": object_digest(frozen_selection["proof_task_ids"][:cfg["proof_tasks"]]),
                "proof_roster_selection": "ordered prefix of pinned preparation development roster",
                "sampling": stream.summary() if balanced_sampling else {"kind": "permutation"},
                "optimizer_groups": [{"name": group["name"], "lr_multiplier": group["lr_multiplier"],
                    "parameters": sum(parameter.numel() for parameter in group["params"])} for group in optimizer.param_groups]}
        status.update(parameters=receipt["parameters"], trainable_parameters=receipt["trainable_parameters"],
                      device=identity["device"], state="running")
        start_step, best_loss, elapsed_before = 0, math.inf, 0.
        tokens_seen, examples_seen, training_seconds, evaluation_seconds = 0, 0, 0., 0.
        training_forward = {key: 0 for key in ("block_calls", "head_calls", "gate_calls", "microbatches", "sequence_tokens", "padded_sequence_tokens", "padded_token_block_calls")}
        best = None
        if resuming:
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            if saved["identity"] != identity:
                raise ValueError("Resume source/data/config/device identity mismatch")
            restore_trainable(model, saved["trainable"])
            optimizer.load_state_dict(saved["optimizer"])
            stream.load_state_dict(saved["stream"])
            depth_rng.setstate(saved["depth_rng"])
            torch.set_rng_state(saved["torch_rng"])
            torch.cuda.set_rng_state_all(saved["cuda_rng"])
            start_step, elapsed_before = saved["step"], saved["elapsed_seconds"]
            tokens_seen, examples_seen, training_seconds = saved["tokens_seen"], saved["examples_seen"], saved["training_seconds"]
            evaluation_seconds = saved["evaluation_seconds"]
            if campaign5 is not None:
                training_forward = saved["training_forward"]
            best = saved["best"]
            best_loss = best["val_loss"] if best else math.inf
            archive = args.out / ("abandoned-tail-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            archive.mkdir()
            for name in ("status.json", "selection.json", "best.pt", "metrics.jsonl"):
                if (args.out / name).exists():
                    (args.out / name).replace(archive / name)
            lines = (archive / "metrics.jsonl").read_text().splitlines() if (archive / "metrics.jsonl").exists() else []
            retained = [json.loads(line) for line in lines if json.loads(line)["step"] <= start_step]
            if any(a["step"] >= b["step"] for a, b in zip(retained, retained[1:])):
                raise ValueError("Nonmonotone committed history")
            (args.out / "metrics.jsonl").write_text("".join(json.dumps(point) + "\n" for point in retained))
            status["history"] = retained[-300:]
            for point in retained:
                status["metrics"].update({k: v for k, v in point.items() if k not in {"step", "updated_at", "validation", "generation", "proof_validation", "tactic_validation", "policy_sweep", "selected_policy"}})
                if point.get("validation"):
                    status.update(selected_policy=point["selected_policy"], policy_sweep=point["policy_sweep"], validation_step=point["step"])
            if best:
                save_torch(args.out / "best.pt", best)
            status["step"] = start_step
        else:
            atomic_json(args.out / "receipt.json", receipt)
        beginning = time.monotonic()

        def save(step):
            save_torch(checkpoint, {"identity": identity, "step": step, "trainable": trainable_state(model),
                "optimizer": optimizer.state_dict(), "stream": stream.state_dict(), "depth_rng": depth_rng.getstate(),
                "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all(),
                "elapsed_seconds": elapsed_before + time.monotonic() - beginning, "tokens_seen": tokens_seen,
                "examples_seen": examples_seen, "training_seconds": training_seconds, "evaluation_seconds": evaluation_seconds, "best": best,
                **({"training_forward": training_forward} if campaign5 is not None else {})})

        def spent_training_budget():
            return training_seconds if campaign5 is not None and campaign5["training_budget_scope"] == "training" else elapsed_before + time.monotonic() - beginning

        for step in range(start_step + 1, cfg["steps"] + 1):
            if spent_training_budget() >= cfg["train_seconds_limit"]:
                break
            started = time.monotonic()
            model.train()
            optimizer.zero_grad(set_to_none=True)
            rows = stream.take(cfg["effective_batch_size"])
            n_targets = sum(sum(label != -100 for label in row["labels"][1:]) for row in rows)
            recurrence = 1 if args.arm == "qwen_vanilla" else depth_rng.choice(cfg["depth_choices"]) if args.arm == "qwen_random" else cfg["fixed_recurrence"]
            lr = cfg["learning_rate"] * min(1., step / cfg["warmup_steps"])
            if step > cfg["warmup_steps"]:
                ratio = (step - cfg["warmup_steps"]) / max(1, cfg["steps"] - cfg["warmup_steps"])
                lr = cfg["minimum_learning_rate"] + .5 * (cfg["learning_rate"] - cfg["minimum_learning_rate"]) * (1 + math.cos(math.pi * ratio))
            for group in optimizer.param_groups:
                group["lr"] = lr * group.get("lr_multiplier", 1.)
            stage = stage_at(campaign5, args.arm, step)
            mean_loss, mean_depth, mean_objective, mean_auxiliary = 0., 0., 0., 0.
            q_mass = torch.zeros(cfg["max_recurrence"], device="cuda")
            depth_loss = torch.zeros_like(q_mass)
            for offset in range(0, len(rows), cfg["micro_batch_size"]):
                inputs = collate(rows[offset:offset + cfg["micro_batch_size"]], pad)
                weight = int((inputs["labels"][:, 1:] != -100).sum()) / n_targets
                ponder = cfg["ponder_cost"] * min(1., max(0., (step - cfg["ponder_start_step"]) / cfg["ponder_warmup_steps"]))
                if campaign5 is not None:
                    # A nonzero gate penalty starts only after the ungated stage.
                    gate_start = max(cfg["ponder_start_step"], campaign5["adaptive_warmup_steps"])
                    ponder = cfg["ponder_cost"] * min(1., max(0., (step - gate_start) / cfg["ponder_warmup_steps"])) if stage["gate_enabled"] else 0.
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    result = model.supervised_loss(**inputs, mode=stage["mode"],
                        recurrence=recurrence, auxiliary_weight=cfg["auxiliary_weight"], ponder_cost=ponder)
                    loss = result["loss"] * weight
                if not bool(torch.isfinite(loss)):
                    raise FloatingPointError("Nonfinite training loss")
                loss.backward()
                mean_loss += float(result["prediction_loss"].detach()) * weight
                mean_objective += float(result["loss"].detach()) * weight
                mean_auxiliary += float(result["auxiliary_loss"].detach()) * weight
                mean_depth += float(result["mean_recurrence"].detach()) * weight
                if campaign5 is not None:
                    for field in ("block_calls", "head_calls", "gate_calls"):
                        training_forward[field] += result[field]
                    training_forward["microbatches"] += 1
                    training_forward["sequence_tokens"] += int(inputs["attention_mask"].sum())
                    training_forward["padded_sequence_tokens"] += inputs["input_ids"].numel()
                    training_forward["padded_token_block_calls"] += inputs["input_ids"].numel() * result["block_calls"]
                if args.arm == "qwen_adaptive":
                    q_mass += result["halting_mass"].detach() * weight
                    depth_loss += result["depth_prediction_loss"].detach() * weight
            gate_grad = [p.grad.norm() for name, p in model.named_parameters() if "halt_gate" in name and p.grad is not None]
            gate_norm = float(torch.linalg.vector_norm(torch.stack(gate_grad))) if gate_grad else None
            grad_norm = torch.nn.utils.clip_grad_norm_(trainable, cfg["grad_clip"], error_if_nonfinite=True)
            optimizer.step()
            torch.cuda.synchronize()
            training_seconds += time.monotonic() - started
            examples_seen += len(rows)
            tokens_seen += n_targets
            status["step"] = step
            elapsed = elapsed_before + time.monotonic() - beginning
            metrics = status["metrics"]
            metrics.update(train_loss=mean_loss, train_objective_loss=mean_objective, train_auxiliary_loss=mean_auxiliary, ponder_coefficient=ponder, train_mean_recurrence=mean_depth, elapsed_seconds=elapsed,
                           training_seconds=training_seconds, train_tokens=tokens_seen, training_examples=examples_seen,
                           tokens_per_second=tokens_seen / max(.001, training_seconds), learning_rate=lr,
                           grad_norm=float(grad_norm), gpu_memory_gb=torch.cuda.max_memory_allocated() / 1024**3,
                           optimizer_steps=step)
            if campaign5 is not None:
                metrics.update(training_stage=stage["name"], gate_training_enabled=stage["gate_enabled"],
                    train_executed_recurrence=cfg["max_recurrence"] if stage["mode"] != "fixed" else recurrence,
                    training_forward_cost=dict(training_forward),
                    optimizer_learning_rates={group["name"]: group["lr"] for group in optimizer.param_groups},
                    training_budget_scope=campaign5["training_budget_scope"],
                    selection_criterion=campaign5["checkpoint_selection"])
                if balanced_sampling:
                    metrics["sampling"] = stream.summary()
            if args.arm != "qwen_vanilla":
                metrics["damping_scales"] = model.damping_scales.detach().tolist()
            if args.arm == "qwen_adaptive":
                metrics.update(halting_mass=q_mass.tolist(), depth_prediction_loss=depth_loss.tolist(), gate_grad_norm=gate_norm)
            at_limit = spent_training_budget() >= cfg["train_seconds_limit"] or stopped[0] or (args.stop_after_step is not None and step >= args.stop_after_step)
            final = step == cfg["steps"] or at_limit
            proof_milestone = (step % cfg["generation_every"] == 0 or final) if campaign5 is None else step in campaign5["proof_eval_steps"]
            extra = {}
            stopping = graceful_stop(campaign5, stop_requested=stopped[0], at_budget_limit=at_limit, step=step, total_steps=cfg["steps"])
            if stopping:
                save(step)
                extra.update(checkpoint_saved_before_shutdown=True,
                    evaluation_skipped="external-stop-or-training-budget; latest trainable/optimizer/RNG state saved")
            if not stopping and (step == 1 or step % cfg["eval_every"] == 0 or final or proof_milestone):
                summary, sweep, duration = validate(model, val, cfg, args.arm, pad)
                metrics.update(val_loss=summary["loss"], val_accuracy=summary["token_accuracy"],
                    val_tokens=summary["tokens"], mean_recurrence=summary["mean_recurrence"],
                    mean_block_calls=summary["mean_block_calls"], validation_seconds=duration)
                status.update(selected_policy=summary["policy"], policy_sweep=sweep, validation_step=step)
                extra.update(validation=True, selected_policy=summary["policy"], policy_sweep=sweep)
                if (campaign5 is None or campaign5["checkpoint_selection"] == "loss") and summary["loss"] < best_loss:
                    best_loss = summary["loss"]
                    best = {"identity": identity, "step": step, "trainable": trainable_state(model),
                            "val_loss": best_loss, "policy": summary["policy"]}
                    save_torch(args.out / "best.pt", best)
                if proof_milestone and evaluation_seconds < cfg["evaluation_seconds_limit"]:
                    model.eval()
                    from .qwen_eval import strict_generation
                    evaluation_snapshot = args.out / f"evaluation-step-{step}.pt"
                    save_torch(evaluation_snapshot, {"identity": identity, "step": step, "trainable": trainable_state(model), "policy": summary["policy"]})
                    provenance = {"run_id": args.out.name, "checkpoint_sha256": digest(evaluation_snapshot),
                        "tokenizer_identity_sha256": data_manifest["tokenizer_identity_sha256"],
                        "source_inventory_sha256": object_digest(sources), "policy": summary["policy"],
                        "model_vocab_size": model.causal_lm.config.vocab_size}
                    if campaign5 is not None:
                        provenance.update(checkpoint_step=step, checkpoint_role="current-evaluation-snapshot")
                    generation_started = time.monotonic()
                    deadline = generation_started + min(cfg["generation_seconds_per_event"], cfg["evaluation_seconds_limit"] - evaluation_seconds)
                    generation_counts = {"decisions": 0, "depths": 0, "blocks": 0, "heads": 0, "gates": 0}
                    def propose(prompt, *, max_new_tokens, deadline_monotonic=None):
                        raw = generate_action(model, tokenizer, prompt, summary["policy"], cfg,
                                               max_new_tokens=max_new_tokens, deadline=min(deadline, deadline_monotonic) if deadline_monotonic is not None else deadline, provenance=provenance)
                        generation_counts["decisions"] += len(raw["decision_ids"])
                        for key, field in (("depths", "recurrence_depths"), ("blocks", "block_calls"), ("heads", "head_calls"), ("gates", "gate_calls")):
                            generation_counts[key] += sum(raw[field])
                        return raw
                    if args.smoke:
                        records = []
                        for row in gen_rows:
                            if time.monotonic() >= deadline:
                                break
                            raw = propose(row["prompt"], max_new_tokens=cfg["max_new_tokens"])
                            decoded = strict_generation(raw, tokenizer, max_new_tokens=cfg["max_new_tokens"], expected_provenance=provenance)
                            records.append({**raw, **decoded, "id": row["id"], "expected": row["completion"],
                                "exact_match": decoded["valid_action"] and decoded["action"] == row["completion"]})
                        atomic_json(args.out / f"validation-predictions-{step}.json", records)
                        metrics.update(gen_exact_match=sum(bool(r["exact_match"]) for r in records) / len(gen_rows),
                                       generation_examples=len(records), generation_total=len(gen_rows))
                    else:
                        if args.peano_root is None:
                            raise ValueError("Native constructive evaluator is required for Qwen proof evaluation")
                        from .qwen_eval import evaluate_suite
                        report = evaluate_suite(args.data, args.data / "admission.json", args.peano_root, tokenizer,
                            propose, provenance, args.out / f"validation-proof-step-{step}",
                            budgets={"max_actions": cfg["proof_max_actions"], "max_new_tokens": cfg["max_new_tokens"],
                                "max_total_decision_tokens": cfg["max_new_tokens"] * cfg["proof_max_actions"],
                                "max_context_tokens": cfg["max_sequence_length"], "candidates_per_step": 1, "search_width": 1},
                            max_wall_seconds=max(.001, deadline-time.monotonic()), split=development_split,
                            expected_admission_sha256=admission_sha256, expected_preparation_sha256=preparation_sha256,
                            budget_ceiling=None if data_contract is None else {"max_actions": cfg["proof_max_actions"], "max_new_tokens": cfg["max_new_tokens"],
                                "max_total_decision_tokens": cfg["max_new_tokens"] * cfg["proof_max_actions"],
                                "max_context_tokens": cfg["max_sequence_length"], "candidates_per_step": 1, "search_width": 1},
                            wall_seconds_ceiling=3600 if data_contract is None else cfg["generation_seconds_per_event"],
                            proof_task_limit=cfg["proof_tasks"] if campaign5 is not None else None)
                        action_counts, proof_counts = report["action_counts"], report["proof_counts"]
                        status.update(stratified_results=report.get("stratified_results", []),
                                      evaluation_contract=report.get("evaluation_contract"),
                                      checkpoint_step=step, checkpoint_sha256=provenance["checkpoint_sha256"],
                                      checkpoint_role="current-evaluation-snapshot", generation_step=step)
                        generation_total, proof_total = len(report["generation_ids"]), len(report["proof_task_ids"])
                        metrics.update(gen_exact_match=action_counts.get("exact_match", 0) / generation_total if action_counts.get("attempted", 0) else None,
                            tactic_validity=action_counts.get("valid_transition", 0) / generation_total if action_counts.get("attempted", 0) else None,
                            proof_acceptance=proof_counts.get("autonomous_python_kernel_proof", 0) / proof_total if proof_counts.get("attempted", 0) else None,
                            generation_examples=action_counts.get("attempted", 0), generation_total=generation_total,
                            proof_attempted=proof_counts.get("attempted", 0), proof_total=proof_total,
                            evaluation_complete=report["status"] == "completed")
                        extra.update(tactic_validation=True, proof_validation=True)
                        if campaign5 is not None:
                            # evaluate_suite has loaded and hash-checked this
                            # exact native module from the admitted Peano root.
                            from peano_lab.ui.prove import surface_success_trace_tactic
                            candidate = proof_candidate(report, args.out / f"validation-proof-step-{step}" / "proofs.jsonl",
                                policy=summary["policy"], validation_loss=summary["loss"], step=step,
                                frozen_tasks=frozen_selection["proof_tasks"][:cfg["proof_tasks"]],
                                success_label=surface_success_trace_tactic)
                            extra["proof_selection_candidate"] = candidate
                            extra["proof_selection_eligible"] = candidate is not None
                            if campaign5["checkpoint_selection"] == "proof_success" and candidate_is_better(candidate, None if best is None else best["selection"]):
                                best_loss = summary["loss"]
                                best = {"identity": identity, "step": step, "trainable": trainable_state(model),
                                    "val_loss": best_loss, "policy": summary["policy"], "selection": candidate}
                                save_torch(args.out / "best.pt", best)
                                status.update(best_checkpoint_step=step, best_proof_selection=candidate)
                    duration = time.monotonic() - generation_started
                    evaluation_seconds += duration
                    denominator = generation_counts["decisions"]
                    metrics.update(generation_seconds=duration, cumulative_evaluation_seconds=evaluation_seconds,
                        generation_decisions=denominator,
                        generation_mean_recurrence=generation_counts["depths"] / denominator if denominator else None,
                        generation_mean_block_calls=generation_counts["blocks"] / denominator if denominator else None,
                        generation_head_calls=generation_counts["heads"], generation_gate_calls=generation_counts["gates"])
                    status["generation_step"] = step
                    extra["generation"] = True
            if step % cfg["log_every"] == 0 or extra or final:
                point = {**metrics, **extra, "step": step, "updated_at": now()}
                if not extra.get("validation"):
                    for key in ("val_loss", "val_accuracy", "val_tokens", "mean_recurrence", "mean_block_calls", "validation_seconds"):
                        point.pop(key, None)
                if not extra.get("generation"):
                    for key in list(point):
                        if key == "gen_exact_match" or key.startswith("generation_"):
                            point.pop(key, None)
                with (args.out / "metrics.jsonl").open("a") as f:
                    f.write(json.dumps(point, allow_nan=False) + "\n")
                status["history"] = (status["history"] + [point])[-300:]
                status["updated_at"] = now()
                atomic_json(args.out / "status.json", status)
                print(json.dumps({"step": step, "train_loss": mean_loss, "val_loss": metrics.get("val_loss"), "elapsed_seconds": elapsed}), flush=True)
            if step % cfg["checkpoint_every"] == 0 or final:
                save(step)
            if at_limit:
                break
        if best is None:
            if campaign5 is not None:
                save(status["step"])
                status.update(state="budget_limited", updated_at=now(), checkpoint_selection_pending=True,
                    completion_scope="Latest training checkpoint saved; no eligible development checkpoint yet",
                    test_state="not-eligible-no-development-selected-checkpoint")
                atomic_json(args.out / "status.json", status)
                return
            raise RuntimeError("Budget exhausted before one validated checkpoint")
        # If elapsed budget crossed between iterations, preserve latest attained update.
        save(status["step"])
        atomic_json(args.out / "selection.json", {"schema_version": 1, "state": "locked", "selected_using": "validation-only" if data_contract is None else "development-only",
            "identity_sha256": object_digest(identity), "checkpoint_step": best["step"], "halting_policy": best["policy"],
            "best_validation_loss": best_loss, "checkpoint": "best.pt", "checkpoint_sha256": digest(args.out / "best.pt"),
            "last_checkpoint_sha256": digest(checkpoint), "test_labels_read": False, "locked_at": now(),
            **({"checkpoint_selection_criterion": campaign5["checkpoint_selection"],
                "proof_selection": best.get("selection"), "registered_selection_policy": campaign5["selection_policies"][args.arm]}
               if campaign5 is not None else {})})
        status.update(state="completed" if status["step"] == cfg["steps"] else "budget_limited",
                      completion_scope="Requested updates completed" if status["step"] == cfg["steps"] else "Partial updates; compare at matched updates or measured compute",
                      updated_at=now(), test_state="pending-frozen-held-out-evaluation")
        atomic_json(args.out / "status.json", status)
    except BaseException as error:
        status.update(state="failed", updated_at=now(), error=f"{type(error).__name__}: {error}")
        atomic_json(args.out / ("resume-failure.json" if resuming else "status.json"), status)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
