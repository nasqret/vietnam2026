"""Campaign3 Qwen recurrent LoRA training. Execute only on WMI/Helios SLURM."""
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
    if transformers.__version__ != "4.53.3" or peft.__version__ != "0.16.0":
        raise RuntimeError("Campaign3 requires Transformers4.53.3 and PEFT0.16.0")
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
def validate(model, rows, cfg, arm, pad):
    model.eval()
    policies = policy_grid(arm)
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
                if arm == "qwen_vanilla":
                    break
        if not taken or any(not bool(mask.all()) for mask in taken.values()):
            raise RuntimeError("A validation policy did not choose one exit per supervised target")
    records = [{"policy": a["policy"], "loss": a["ce"] / a["tokens"],
                "token_accuracy": a["correct"] / a["tokens"], "tokens": a["tokens"],
                "mean_recurrence": a["depth"] / a["tokens"], "mean_block_calls": a["blocks"] / a["tokens"]}
               for a in accum.values()]
    baseline = next(a["loss"] for a in records if a["policy"] == {"kind": "fixed", "depth": 1 if arm == "qwen_vanilla" else 4})
    eligible = [a for a in records if a["loss"] <= baseline + cfg["policy_loss_tolerance"]]
    selected = min(eligible, key=lambda a: (a["mean_block_calls"], a["loss"], policy_key(a["policy"])))
    return selected, records, time.monotonic() - started


@torch.inference_mode()
def generate_action(model, tokenizer, prompt, policy, cfg, *, max_new_tokens=None):
    sequence = tokenizer.encode(prompt, add_special_tokens=False)
    limit = min(cfg["max_new_tokens"] if max_new_tokens is None else max_new_tokens,
                cfg["max_sequence_length"] - len(sequence))
    decisions, depths, blocks = [], [], []
    reason = "context_limit" if len(sequence) + (cfg["max_new_tokens"] if max_new_tokens is None else max_new_tokens) > cfg["max_sequence_length"] else "token_budget"
    special_ids = set(tokenizer.all_special_ids)
    started = time.monotonic()
    for _ in range(max(0, limit)):
        tokens = torch.tensor([sequence], dtype=torch.long, device="cuda")
        with torch.autocast("cuda", dtype=torch.bfloat16):
            output = model.next_logits(input_ids=tokens, policy=policy)
        token = int(output["logits"].argmax(-1).item())
        decisions.append(token)
        depths.append(int(output["depth"]))
        blocks.append(int(output["block_calls"]))
        if token == tokenizer.eos_token_id:
            reason = "eos"
            break
        if token in special_ids:
            reason = "invalid_special_token"
            break
        sequence.append(token)
    return {"decision_ids": decisions, "stop_reason": reason, "eos": reason == "eos",
            "recurrence_depths": depths, "block_calls": blocks,
            "policy": policy, "seconds": time.monotonic() - started,
            "provenance": {"model_tokenizer": "Qwen3-pinned-BPE", "max_new_tokens": max_new_tokens or cfg["max_new_tokens"],
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
        raise SystemExit("All campaign3 execution requires WMI/Helios SLURM")
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
              "notes": ["Qwen BPE and compact proof-state condition; compare within campaign3.",
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
        if inventory["model.safetensors"] != cfg["base_weights_sha256"]:
            raise ValueError("Base weight identity differs from pinned snapshot")
        from .qwen_data import load_tokenized, deterministic_evaluation_ids
        train = load_tokenized(args.data / "train.jsonl")
        val_all = load_tokenized(args.data / "val.jsonl")
        data_manifest = json.loads((args.data / "manifest.json").read_text())
        dataset_hashes = {name: digest(args.data / name) for name in ("manifest.json", "train.jsonl", "val.jsonl")}
        for split in ("train", "val"):
            if data_manifest["splits"][split]["output_sha256"] != dataset_hashes[split + ".jsonl"]:
                raise ValueError("Prepared data changed")
        selection = deterministic_evaluation_ids(val_all, validation_rows=cfg["validation_rows"], generation_rows=cfg["generation_rows"])
        by_id = {r["id"]: r for r in val_all}
        val = [by_id[i] for i in selection["validation_ids"]]
        gen_rows = [by_id[i] for i in selection["generation_ids"]]
        tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, trust_remote_code=False)
        pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        model = make_model(cfg, args.model, args.arm)
        trainable = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(trainable, lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"], betas=(.9, .95))
        stream, depth_rng = ExampleStream(train, args.seed), random.Random(args.seed + 8071)
        sources = {str(p): digest(p) for p in sorted(Path("src/latentproof").glob("*.py"))}
        identity = {"arm": args.arm, "seed": args.seed, "config_sha256": object_digest(cfg),
                    "data": dataset_hashes, "base": inventory, "sources_sha256": sources,
                    "transformers": transformers.__version__, "peft": peft.__version__,
                    "torch": torch.__version__, "cuda": torch.version.cuda,
                    "device": torch.cuda.get_device_name(0)}
        receipt = {"identity": identity, "config": cfg, "created_at": now(),
                   "parameters": sum(p.numel() for p in model.parameters()),
                   "trainable_parameters": sum(p.numel() for p in trainable),
                   "trainable_names": [name for name, p in model.named_parameters() if p.requires_grad],
                   "training_rows": len(train), "validation_selection": selection,
                   "python": platform.python_version(), "platform": platform.platform(),
                   "data_manifest": data_manifest}
        status.update(parameters=receipt["parameters"], trainable_parameters=receipt["trainable_parameters"],
                      device=identity["device"], state="running")
        start_step, best_loss, elapsed_before = 0, math.inf, 0.
        tokens_seen, examples_seen, training_seconds = 0, 0, 0.
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
                "examples_seen": examples_seen, "training_seconds": training_seconds, "best": best})

        for step in range(start_step + 1, cfg["steps"] + 1):
            if elapsed_before + time.monotonic() - beginning >= cfg["train_seconds_limit"]:
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
                group["lr"] = lr
            mean_loss, mean_depth = 0., 0.
            q_mass = torch.zeros(cfg["max_recurrence"], device="cuda")
            depth_loss = torch.zeros_like(q_mass)
            for offset in range(0, len(rows), cfg["micro_batch_size"]):
                inputs = collate(rows[offset:offset + cfg["micro_batch_size"]], pad)
                weight = int((inputs["labels"][:, 1:] != -100).sum()) / n_targets
                ponder = cfg["ponder_cost"] * min(1., max(0., (step - cfg["ponder_start_step"]) / cfg["ponder_warmup_steps"]))
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    result = model.supervised_loss(**inputs, mode="adaptive" if args.arm == "qwen_adaptive" else "fixed",
                        recurrence=recurrence, auxiliary_weight=cfg["auxiliary_weight"], ponder_cost=ponder)
                    loss = result["loss"] * weight
                if not bool(torch.isfinite(loss)):
                    raise FloatingPointError("Nonfinite training loss")
                loss.backward()
                mean_loss += float(result["prediction_loss"].detach()) * weight
                mean_depth += float(result["mean_recurrence"].detach()) * weight
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
            metrics.update(train_loss=mean_loss, train_mean_recurrence=mean_depth, elapsed_seconds=elapsed,
                           training_seconds=training_seconds, train_tokens=tokens_seen, training_examples=examples_seen,
                           tokens_per_second=tokens_seen / max(.001, training_seconds), learning_rate=lr,
                           grad_norm=float(grad_norm), gpu_memory_gb=torch.cuda.max_memory_allocated() / 1024**3,
                           optimizer_steps=step)
            if args.arm == "qwen_adaptive":
                metrics.update(halting_mass=q_mass.tolist(), depth_prediction_loss=depth_loss.tolist(), gate_grad_norm=gate_norm)
            at_limit = elapsed >= cfg["train_seconds_limit"] or stopped[0] or (args.stop_after_step is not None and step >= args.stop_after_step)
            final = step == cfg["steps"] or at_limit
            extra = {}
            if step == 1 or step % cfg["eval_every"] == 0 or final:
                summary, sweep, duration = validate(model, val, cfg, args.arm, pad)
                metrics.update(val_loss=summary["loss"], val_accuracy=summary["token_accuracy"],
                    val_tokens=summary["tokens"], mean_recurrence=summary["mean_recurrence"],
                    mean_block_calls=summary["mean_block_calls"], validation_seconds=duration)
                status.update(selected_policy=summary["policy"], policy_sweep=sweep, validation_step=step)
                extra.update(validation=True, selected_policy=summary["policy"], policy_sweep=sweep)
                if summary["loss"] < best_loss:
                    best_loss = summary["loss"]
                    best = {"identity": identity, "step": step, "trainable": trainable_state(model),
                            "val_loss": best_loss, "policy": summary["policy"]}
                    save_torch(args.out / "best.pt", best)
                if step % cfg["generation_every"] == 0 or final:
                    model.eval()
                    from .qwen_eval import strict_generation
                    records = []
                    generation_started = time.monotonic()
                    for row in gen_rows:
                        raw = generate_action(model, tokenizer, row["prompt"], summary["policy"], cfg)
                        decoded = strict_generation(raw, tokenizer, max_new_tokens=cfg["max_new_tokens"])
                        records.append({**raw, **decoded, "id": row["id"], "session_id": row["session_id"],
                            "expected": row["completion"], "exact_match": decoded.get("valid", False) and decoded.get("text") == row["completion"]})
                    atomic_json(args.out / f"validation-predictions-{step}.json", records)
                    all_depths = [d for record in records for d in record["recurrence_depths"]]
                    metrics.update(gen_exact_match=sum(bool(r["exact_match"]) for r in records) / len(records),
                        generation_examples=len(records), generation_seconds=time.monotonic() - generation_started,
                        generation_mean_recurrence=sum(all_depths) / len(all_depths) if all_depths else None)
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
            raise RuntimeError("Budget exhausted before one validated checkpoint")
        # If elapsed budget crossed between iterations, preserve latest attained update.
        save(status["step"])
        atomic_json(args.out / "selection.json", {"schema_version": 1, "state": "locked", "selected_using": "validation-only",
            "identity_sha256": object_digest(identity), "checkpoint_step": best["step"], "halting_policy": best["policy"],
            "best_validation_loss": best_loss, "checkpoint": "best.pt", "checkpoint_sha256": digest(args.out / "best.pt"),
            "last_checkpoint_sha256": digest(checkpoint), "test_labels_read": False, "locked_at": now()})
        status.update(state="completed" if status["step"] == cfg["steps"] else "budget_limited",
                      updated_at=now(), test_state="pending-frozen-held-out-evaluation")
        atomic_json(args.out / "status.json", status)
    except BaseException as error:
        status.update(state="failed", updated_at=now(), error=f"{type(error).__name__}: {error}")
        atomic_json(args.out / ("resume-failure.json" if resuming else "status.json"), status)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
