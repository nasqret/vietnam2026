"""Bounded, resumable campaign-2 trainer and live records. SLURM GPU only."""
from __future__ import annotations
import argparse
from dataclasses import asdict, replace
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
from torch.nn import functional as F

from .adaptive import AdaptiveRecurrentLM, distribution_features, policy_grid, policy_key, select_policy
from .campaign_data import BOS_EOS, VOCAB_SIZE, ExampleStream, batch, digest, evaluation_subset, load_rows
from .model import ModelConfig, StandardTransformerLM, unique_parameter_count


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, obj):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def make_model(cfg, arm):
    architecture = ModelConfig(vocab_size=VOCAB_SIZE, width=cfg["width"], heads=cfg["heads"],
        mlp_width=cfg["mlp_width"], prelude_layers=1, core_layers=2, coda_layers=1,
        reference_recurrence=cfg["fixed_recurrence"], max_sequence_length=cfg["max_sequence_length"])
    if arm.startswith("recurrent_"):
        model = AdaptiveRecurrentLM(architecture, cfg["min_recurrence"], cfg["max_recurrence"])
        if arm != "recurrent_adaptive":
            for parameter in model.halt_gate.parameters():
                parameter.requires_grad_(False)
        return model
    if arm == "vanilla_pre":
        return StandardTransformerLM(replace(architecture, mlp_width=1622), 4, "pre", initialization_depth=10)
    if arm == "vanilla_sandwich":
        return StandardTransformerLM(replace(architecture, mlp_width=1621), 4, "sandwich", initialization_depth=10)
    if arm == "vanilla_deep":
        return StandardTransformerLM(architecture, 10, "sandwich", initialization_depth=10)
    raise ValueError("unknown arm")


def cross_entropy(logits, labels):
    return F.cross_entropy(logits.float().reshape(-1, logits.shape[-1]), labels.reshape(-1), ignore_index=-100)


@torch.inference_mode()
def validate(model, rows, cfg, native, policies_override=None):
    """Teacher-forced sweep. Counts depth decisions, NOT measured saved FLOPs."""
    model.eval()
    recurrent = isinstance(model, AdaptiveRecurrentLM)
    policies = policies_override if policies_override is not None else (policy_grid(native) if recurrent else [{"kind": "vanilla"}])
    accum = {policy_key(p): {"policy": p, "ce": 0.0, "correct": 0, "tokens": 0,
                            "depth": 0.0, "blocks": 0.0} for p in policies}
    for start in range(0, len(rows), cfg["micro_batch_size"]):
        tokens, labels = batch(rows[start:start+cfg["micro_batch_size"]], "cuda")
        mask = labels != -100
        count = int(mask.sum())
        chosen = {policy_key(p): torch.zeros_like(mask) for p in policies}
        survival = torch.ones_like(labels, dtype=torch.float)
        previous = None
        with torch.autocast("cuda", dtype=torch.bfloat16):
            probes = model.depth_logits(tokens) if recurrent else [(1, model(tokens)["logits"])]
            for depth, logits in probes:
                entropy, kl, logp = distribution_features(logits, previous)
                previous = logp
                ce = F.cross_entropy(logits.float().reshape(-1, logits.shape[-1]), labels.reshape(-1),
                                     ignore_index=-100, reduction="none").reshape_as(labels)
                correct = logits.argmax(-1) == labels
                if recurrent and model.min_depth <= depth < model.max_depth and native:
                    survival *= 1 - model.hazard(entropy, kl, depth)
                for policy in policies:
                    kind, key = policy["kind"], policy_key(policy)
                    stop = torch.zeros_like(mask)
                    if kind == "vanilla":
                        stop = torch.ones_like(mask)
                    elif kind == "fixed":
                        if depth == policy["depth"]:
                            stop = torch.ones_like(mask)
                    elif depth >= model.min_depth:
                        if depth == model.max_depth:
                            stop = torch.ones_like(mask)
                        elif kind == "learned":
                            stop = (1 - survival) >= policy["quantile"]
                        elif kind == "entropy":
                            stop = entropy <= policy["entropy"]
                        elif kind == "kl":
                            stop = kl <= policy["kl"]
                        elif kind == "entropy_kl":
                            stop = (entropy <= policy["entropy"]) & (kl <= policy["kl"])
                    take = stop & mask & ~chosen[key]
                    chosen[key] |= take
                    n = int(take.sum())
                    entry = accum[key]
                    entry["ce"] += float(ce[take].sum())
                    entry["correct"] += int(correct[take].sum())
                    entry["tokens"] += n
                    entry["depth"] += n * depth if recurrent else 0
                    block_calls = (model.block_evaluations(depth) if kind == "fixed" else
                                   model.cfg.prelude_layers + depth * (model.cfg.core_layers + model.cfg.coda_layers)) if recurrent else len(model.layers)
                    entry["blocks"] += n * block_calls
        if any(int(x.sum()) != count for x in chosen.values()):
            raise RuntimeError("policy did not choose exactly one output per supervised position")
    records = []
    for entry in accum.values():
        n = entry["tokens"]
        records.append({"policy": entry["policy"], "loss": entry["ce"] / n,
                        "token_accuracy": entry["correct"] / n, "tokens": n,
                        "mean_recurrence": entry["depth"] / n if recurrent else None,
                        "mean_block_calls": entry["blocks"] / n})
    selected = select_policy(records, cfg["policy_loss_tolerance"]) if recurrent and policies_override is None else policies[0]
    summary = next(x for x in records if x["policy"] == selected)
    return summary, records


@torch.inference_mode()
def generate_one(model, row, policy, cfg):
    sequence = [BOS_EOS] + list(row["prompt"].encode("utf-8"))
    generated, decisions, depths, blocks = [], [], [], []
    stopped = False
    stop_reason = "context_limit" if cfg["max_sequence_length"] - len(sequence) < cfg["max_new_tokens"] else "token_budget"
    for _ in range(min(cfg["max_new_tokens"], cfg["max_sequence_length"] - len(sequence))):
        tokens = torch.tensor([sequence], device="cuda", dtype=torch.long)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            if isinstance(model, AdaptiveRecurrentLM):
                logits, depth, calls = model.next_logits(tokens, policy)
            else:
                logits, depth, calls = model(tokens)["logits"][:, -1], 0, len(model.layers)
        token = int(logits.argmax(-1))
        decisions.append(token)
        depths.append(depth)
        blocks.append(calls)
        if token == BOS_EOS:
            stopped = True
            stop_reason = "eos"
            break
        if token >= 256:
            # PAD is not silently repaired into a valid tactic.
            generated.append(token)
            stop_reason = "invalid_special_token"
            break
        generated.append(token)
        sequence.append(token)
    try:
        prediction = bytes(generated).decode("utf-8", errors="strict")
        valid_encoding = True
    except (UnicodeDecodeError, ValueError):
        prediction, valid_encoding = None, False
    return {"id": row["id"], "session_id": row["session_id"], "task_family": row.get("task_family"),
            "prediction": prediction, "expected": row["completion"], "generated_ids": generated,
            "decision_ids": decisions, "stop_reason": stop_reason,
            "eos": stopped, "valid_encoding": valid_encoding,
            "exact_match": stopped and valid_encoding and prediction == row["completion"],
            "recurrence_depths": depths, "block_calls": blocks, "policy": policy}


@torch.inference_mode()
def evaluate_generation(model, rows, policy, cfg, out, step):
    model.eval()
    # Warm the same kernels on a validation record; timings exclude this pass.
    generate_one(model, rows[0], policy, {**cfg, "max_new_tokens": 2})
    torch.cuda.synchronize()
    start = time.monotonic()
    records = [generate_one(model, row, policy, cfg) for row in rows]
    torch.cuda.synchronize()
    elapsed = time.monotonic() - start
    atomic_json(out / f"validation-predictions-{step}.json", records)
    decisions = [r for row in records for r in row["recurrence_depths"]]
    return {"gen_exact_match": sum(x["exact_match"] for x in records) / len(records),
            "generation_examples": len(records), "generation_seconds": elapsed,
            "generation_tokens_per_second": len(decisions) / elapsed,
            "generation_mean_recurrence": sum(decisions) / len(decisions) if isinstance(model, AdaptiveRecurrentLM) else None,
            "generation_eos_rate": sum(x["eos"] for x in records) / len(records)}


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Run on Helios/WMI SLURM only")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--cluster", choices=("wmi", "helios"), required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--stop-after-step", type=int, help="Checkpointed interruption for remote resume validation")
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if args.arm not in cfg["arms"]:
        raise ValueError("unregistered arm")
    if args.smoke:
        cfg.update(steps=4, effective_batch_size=4, eval_every=4, log_every=1,
                   checkpoint_every=4, generation_every=4, validation_rows=4,
                   generation_rows=2, max_new_tokens=8, train_seconds_limit=600)
    args.out.mkdir(parents=True, exist_ok=True)
    checkpoint = args.out / "last.pt"
    resuming, resume_validated = checkpoint.exists(), False
    status = {"run_id": args.out.name, "campaign_id": cfg["campaign_id"], "arm": args.arm,
              "seed": args.seed, "cluster": args.cluster, "job_id": os.environ["SLURM_JOB_ID"],
              "array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID"),
              "array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID"),
              "state": "initializing", "step": 0, "max_steps": cfg["steps"], "updated_at": now(),
              "metrics": {"proof_acceptance": None, "tactic_validity": None}, "history": [],
              "notes": ["Teacher-forced token accuracy and generated-action exact match are not proof acceptance.",
                        "Policy sweep counts are projected depth/block calls; generation timing measures actual execution."],
              "smoke": args.smoke}
    if not resuming:
        atomic_json(args.out / "status.json", status)
    stopped = [False]
    signal.signal(signal.SIGTERM, lambda *_: stopped.__setitem__(0, True))
    signal.signal(signal.SIGUSR1, lambda *_: stopped.__setitem__(0, True))
    try:
        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("CUDA/bf16 unavailable")
        torch.set_num_threads(min(4, int(os.environ.get("SLURM_CPUS_PER_TASK", 4))))
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
        admission = json.loads((args.data / "admission.json").read_text())
        if admission["status"] != "admitted-python-replay":
            raise ValueError("data did not pass admission")
        train_hash, val_hash = digest(args.data / "train.jsonl"), digest(args.data / "val.jsonl")
        if any(admission["splits"][name]["output_sha256"] != value for name, value in (("train", train_hash), ("val", val_hash))):
            raise ValueError("admitted dataset bytes changed")
        train = load_rows(args.data / "train.jsonl", cfg["max_sequence_length"])
        val = load_rows(args.data / "val.jsonl", cfg["max_sequence_length"])
        val = evaluation_subset(val, cfg["validation_rows"], "campaign2-validation-v1")
        stream, depth_rng = ExampleStream(train, args.seed), random.Random(args.seed + 8071)
        model = make_model(cfg, args.arm).cuda()
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                                     lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"], betas=(0.9, 0.95))
        config_sha = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        source_hashes = {str(p): digest(p) for p in sorted(Path("src/latentproof").glob("*.py"))}
        identity = {"arm": args.arm, "seed": args.seed, "config_sha256": config_sha,
                    "train_sha256": train_hash, "val_sha256": val_hash,
                    "admission_sha256": digest(args.data / "admission.json"), "sources_sha256": source_hashes,
                    "evaluation_schema": "campaign2-validation-policy-v1", "torch": torch.__version__,
                    "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(0)}
        receipt = {"config": cfg, "config_sha256": config_sha, "architecture": asdict(model.cfg),
                   "sources_sha256": source_hashes, "admission_sha256": digest(args.data / "admission.json"),
                   "train_sha256": train_hash, "val_sha256": val_hash,
                   "torch": torch.__version__, "cuda": torch.version.cuda, "python": platform.python_version(),
                   "device": torch.cuda.get_device_name(0), "platform": platform.platform(),
                   "parameters": unique_parameter_count(model),
                   "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
                   "training_rows": len(train), "validation_rows": len(val), "created_at": now()}
        receipt["identity"] = identity
        if not resuming:
            atomic_json(args.out / "receipt.json", receipt)
        status.update(parameters=receipt["parameters"], device=receipt["device"], state="running")
        start_step, elapsed_before, examples_seen, tokens_seen, best_loss = 0, 0., 0, 0, math.inf
        training_seconds, input_tokens_seen = 0., 0
        if resuming:
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            if saved.get("identity") != identity:
                raise ValueError("resume source/config/data mismatch")
            # last.pt is the committed transaction boundary. Later validation,
            # prediction and best-checkpoint files belong to an abandoned tail.
            restored_best = saved["best_checkpoint"]
            if (restored_best["identity"] != identity or type(restored_best["step"]) is not int
                or type(saved["step"]) is not int or not 1 <= restored_best["step"] <= saved["step"] <= cfg["steps"]
                or not math.isfinite(restored_best["val_loss"])):
                raise ValueError("invalid best checkpoint in resume transaction")
            all_lines = (args.out / "metrics.jsonl").read_text().splitlines() if (args.out / "metrics.jsonl").exists() else []
            history_steps = [json.loads(line)["step"] for line in all_lines]
            if any(type(s) is not int or s < 1 for s in history_steps) or any(a >= b for a, b in zip(history_steps, history_steps[1:])):
                raise ValueError("history steps are not strictly increasing integers")
            resume_validated = True
            archive = args.out / ("abandoned-tail-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            archive.mkdir()
            for name in ("status.json", "selection.json", "best.pt"):
                existing = args.out / name
                if existing.exists():
                    existing.replace(archive / name)
            torch.save(restored_best, args.out / "best.pt")
            if (args.out / "metrics.jsonl").exists():
                (archive / "metrics-original.jsonl").write_text("\n".join(all_lines) + "\n")
                active_lines = [line for line in all_lines if json.loads(line)["step"] <= saved["step"]]
                history_temporary = args.out / "metrics.jsonl.tmp"
                history_temporary.write_text("\n".join(active_lines) + "\n")
                history_temporary.replace(args.out / "metrics.jsonl")
            for prediction in args.out.glob("validation-predictions-*.json"):
                if int(prediction.stem.rsplit("-", 1)[1]) > saved["step"]:
                    prediction.replace(archive / prediction.name)
            model.load_state_dict(saved["model"])
            optimizer.load_state_dict(saved["optimizer"])
            stream.load_state_dict(saved["stream"])
            depth_rng.setstate(saved["depth_rng"])
            torch.set_rng_state(saved["torch_rng"])
            torch.cuda.set_rng_state_all(saved["cuda_rng"])
            start_step, elapsed_before = saved["step"], saved["elapsed_seconds"]
            examples_seen, tokens_seen, best_loss = saved["examples_seen"], saved["tokens_seen"], saved["best_loss"]
            training_seconds, input_tokens_seen = saved["training_seconds"], saved["input_tokens_seen"]
            status["step"] = start_step
            if (args.out / "metrics.jsonl").exists():
                status["history"] = [json.loads(x) for x in (args.out / "metrics.jsonl").read_text().splitlines()][-300:]
                for point in status["history"]:
                    controls = {"step", "updated_at", "validation", "generation", "policy_sweep", "selected_policy"}
                    status["metrics"].update({k: v for k, v in point.items() if k not in controls})
                    if "selected_policy" in point:
                        status["selected_policy"] = point["selected_policy"]
                        status["policy_sweep"] = point["policy_sweep"]
                    if point.get("validation"):
                        status["validation_step"] = point["step"]
                    if point.get("generation"):
                        status["generation_step"] = point["step"]
            best_loss = restored_best["val_loss"]
        beginning = time.monotonic()
        last_log = beginning
        last_log_tokens = tokens_seen
        native = args.arm == "recurrent_adaptive"

        def save(step):
            temporary = args.out / "last.pt.tmp"
            best_checkpoint = torch.load(args.out / "best.pt", map_location="cpu", weights_only=False)
            torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(), "step": step,
                        "identity": identity,
                        "stream": stream.state_dict(), "depth_rng": depth_rng.getstate(), "torch_rng": torch.get_rng_state(),
                        "cuda_rng": torch.cuda.get_rng_state_all(), "elapsed_seconds": elapsed_before + time.monotonic() - beginning,
                        "examples_seen": examples_seen, "tokens_seen": tokens_seen, "best_loss": best_loss,
                        "training_seconds": training_seconds, "input_tokens_seen": input_tokens_seen,
                        "best_checkpoint": best_checkpoint}, temporary)
            temporary.replace(checkpoint)

        end_step = start_step if elapsed_before >= cfg["train_seconds_limit"] else cfg["steps"]
        for step in range(start_step + 1, end_step + 1):
            training_started = time.monotonic()
            model.train()
            optimizer.zero_grad(set_to_none=True)
            selected_rows = stream.take(cfg["effective_batch_size"])
            supervision = sum(len(row["completion"].encode("utf-8")) + 1 for row in selected_rows)
            recurrence = depth_rng.randint(cfg["min_recurrence"], cfg["max_recurrence"]) if args.arm == "recurrent_random" else cfg["fixed_recurrence"]
            learning_rate = cfg["learning_rate"] * min(1., step / cfg["warmup_steps"])
            if step > cfg["warmup_steps"]:
                fraction = (step - cfg["warmup_steps"]) / max(1, cfg["steps"] - cfg["warmup_steps"])
                learning_rate = cfg["minimum_learning_rate"] + .5 * (cfg["learning_rate"] - cfg["minimum_learning_rate"]) * (1 + math.cos(math.pi * fraction))
            for group in optimizer.param_groups:
                group["lr"] = learning_rate
            mean_loss, mean_depth = 0., 0.
            q_mass = torch.zeros(cfg["max_recurrence"] - cfg["min_recurrence"] + 1, device="cuda")
            depth_ce = torch.zeros_like(q_mass)
            for offset in range(0, len(selected_rows), cfg["micro_batch_size"]):
                tokens, labels = batch(selected_rows[offset:offset+cfg["micro_batch_size"]], "cuda")
                weight = int((labels != -100).sum()) / supervision
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    if native:
                        result = model.adaptive_loss(tokens, labels,
                            ponder_cost=cfg["ponder_cost"] * min(1., step / cfg["ponder_warmup_steps"]),
                            auxiliary_weight=cfg["auxiliary_weight"])
                        loss, prediction_loss, depth = result["loss"], result["prediction_loss"], float(result["mean_recurrence"].detach())
                        q_mass += result["weights"].detach()[labels != -100].mean(0) * weight
                        depth_ce += result["depth_ce"].detach()[labels != -100].mean(0) * weight
                    else:
                        output = model(tokens, recurrence) if isinstance(model, AdaptiveRecurrentLM) else model(tokens)
                        loss = prediction_loss = cross_entropy(output["logits"], labels)
                        depth = recurrence if isinstance(model, AdaptiveRecurrentLM) else 0
                    loss = loss * weight
                if not bool(torch.isfinite(loss)):
                    raise FloatingPointError("nonfinite loss")
                loss.backward()
                mean_loss += float(prediction_loss.detach()) * weight
                mean_depth += depth * weight
            gate_grad_norm = float(torch.linalg.vector_norm(torch.stack([p.grad.norm() for p in model.halt_gate.parameters() if p.grad is not None]))) if native else None
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"], error_if_nonfinite=True)
            optimizer.step()
            torch.cuda.synchronize()
            training_seconds += time.monotonic() - training_started
            examples_seen += len(selected_rows)
            tokens_seen += supervision
            input_tokens_seen += sum(len(row["tokens"]) - 1 for row in selected_rows)
            status["step"] = step
            elapsed = elapsed_before + time.monotonic() - beginning
            metrics = status["metrics"]
            metrics.update(train_loss=mean_loss, train_mean_recurrence=mean_depth if isinstance(model, AdaptiveRecurrentLM) else None,
                           elapsed_seconds=elapsed, train_tokens=tokens_seen, training_examples=examples_seen,
                           learning_rate=learning_rate, grad_norm=float(grad_norm),
                           gpu_memory_gb=torch.cuda.max_memory_allocated() / 1024**3,
                           training_seconds=training_seconds, input_tokens=input_tokens_seen,
                           training_only_tokens_per_second=tokens_seen / max(.001, training_seconds),
                           optimizer_steps=step)
            if native:
                metrics.update(halting_mass=q_mass.tolist(), depth_prediction_loss=depth_ce.tolist(),
                               gate_grad_norm=gate_grad_norm)
            at_limit = elapsed >= cfg["train_seconds_limit"] or stopped[0] or (args.stop_after_step is not None and step >= args.stop_after_step)
            final_step = step == cfg["steps"] or at_limit
            extra = {}
            if step % cfg["eval_every"] == 0 or step == 1 or final_step:
                summary, sweep = validate(model, val, cfg, native)
                metrics.update(val_loss=summary["loss"], val_accuracy=summary["token_accuracy"],
                               mean_recurrence=summary["mean_recurrence"], val_tokens=summary["tokens"],
                               mean_block_calls=summary["mean_block_calls"])
                status["selected_policy"] = summary["policy"]
                status["policy_sweep"] = sweep
                status["validation_step"] = step
                extra.update(policy_sweep=sweep, selected_policy=summary["policy"], validation=True)
                if summary["loss"] < best_loss:
                    best_loss = summary["loss"]
                    best_temporary = args.out / "best.pt.tmp"
                    torch.save({"model": model.state_dict(), "step": step, "policy": summary["policy"],
                                "val_loss": best_loss, "config_sha256": config_sha, "identity": identity}, best_temporary)
                    best_temporary.replace(args.out / "best.pt")
                if step % cfg["generation_every"] == 0 or final_step:
                    gen_rows = evaluation_subset(val, cfg["generation_rows"], "campaign2-generate-v1")
                    metrics.update(evaluate_generation(model, gen_rows, summary["policy"], cfg, args.out, step))
                    status["generation_step"] = step
                    extra["generation"] = True
            if step % cfg["log_every"] == 0 or extra or final_step:
                timestamp = time.monotonic()
                metrics["tokens_per_second"] = (tokens_seen - last_log_tokens) / max(.001, timestamp - last_log)
                last_log, last_log_tokens = timestamp, tokens_seen
                point = {**metrics, **extra, "step": step, "updated_at": now()}
                if not extra.get("validation"):
                    for key in ("val_loss", "val_accuracy", "mean_recurrence", "val_tokens", "mean_block_calls"):
                        point.pop(key, None)
                if not extra.get("generation"):
                    for key in list(point):
                        if key == "gen_exact_match" or key.startswith("generation_"):
                            point.pop(key, None)
                with (args.out / "metrics.jsonl").open("a") as f:
                    f.write(json.dumps(point, allow_nan=False) + "\n")
                status["history"] = (status["history"] + [point])[-300:]
                status.update(updated_at=now())
                atomic_json(args.out / "status.json", status)
                print(json.dumps({"step": step, "train_loss": mean_loss, "val_loss": metrics.get("val_loss"),
                                  "elapsed_seconds": elapsed}), flush=True)
            if step % cfg["checkpoint_every"] == 0 or final_step:
                save(step)
            if at_limit:
                break
        # Lock selection on validation only. Test evaluation is a separate job.
        selected_checkpoint = torch.load(args.out / "best.pt", map_location="cpu", weights_only=False)
        atomic_json(args.out / "selection.json", {"schema_version": 1, "state": "locked",
            "selected_using": "validation-only", "config_sha256": config_sha, "best_validation_loss": best_loss,
            "checkpoint_step": selected_checkpoint["step"], "halting_policy": selected_checkpoint["policy"],
            "checkpoint": "best.pt", "checkpoint_sha256": digest(args.out / "best.pt"),
            "final_checkpoint_sha256": digest(checkpoint), "test_labels_read": False, "locked_at": now()})
        status.update(state="completed" if status["step"] == cfg["steps"] else "budget_limited",
                      updated_at=now(), test_state="pending-separate-frozen-evaluation")
        atomic_json(args.out / "status.json", status)
    except BaseException as error:
        status.update(state="failed", updated_at=now(), error=f"{type(error).__name__}: {error}")
        atomic_json(args.out / ("resume-failure.json" if resuming and not resume_validated else "status.json"), status)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
