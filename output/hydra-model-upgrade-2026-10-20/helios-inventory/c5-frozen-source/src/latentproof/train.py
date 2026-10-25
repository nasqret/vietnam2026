"""Run the pre-registered tiny comparison ONLY in a SLURM allocation.

Not the Huginn recipe. Completion loss, shared data schedule, FP32, one GPU.
Save all predictions and send parsed certificates to the pinned Lean verifier.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import time

import torch
from torch.nn import functional as F

from .data import ALPHABET, EOS_ID, examples, encode, compile_prediction, reference_valid
from .model import ModelConfig, RecurrentLM, StandardTransformerLM, sample_recurrence, unique_parameter_count
from .peano import canonical_bytes, CHECKER_COMMIT


def atomic_json(path, obj):
    p = Path(path)
    temp = p.with_suffix(p.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2) + "\n")
    temp.replace(p)


def batch(rows, device):
    seqs = [encode(x.prompt + x.completion) for x in rows]
    width = max(map(len, seqs))
    tokens = torch.zeros((len(rows), width), dtype=torch.long, device=device)
    labels = torch.full((len(rows), width - 1), -100, dtype=torch.long, device=device)
    for i, (row, seq) in enumerate(zip(rows, seqs)):
        tokens[i, :len(seq)] = torch.tensor(seq, device=device)
        start = len(row.prompt) - 1
        labels[i, start:len(seq)-1] = torch.tensor(seq[start+1:], device=device)
    return tokens, labels


def logits(model, tokens, r=None, k=None, deterministic=False):
    if isinstance(model, RecurrentLM):
        state = torch.zeros((*tokens.shape, model.cfg.width), device=tokens.device) if deterministic else None
        return model(tokens, recurrence=r, backprop_depth=k, initial_state=state)["logits"]
    return model(tokens)["logits"]


@torch.inference_mode()
def generate(model, rows, r, max_new_tokens, device):
    prompts = [encode(row.prompt) for row in rows]
    capacity = max(map(len, prompts)) + max_new_tokens
    seq = torch.zeros((len(rows), capacity), dtype=torch.long, device=device)
    lengths = torch.tensor([len(p) for p in prompts], device=device)
    finished = torch.zeros(len(rows), dtype=torch.bool, device=device)
    for i, p in enumerate(prompts):
        seq[i, :len(p)] = torch.tensor(p, device=device)
    for _ in range(max_new_tokens):
        upto = int(lengths.max())
        scores = logits(model, seq[:, :upto], r, deterministic=True)
        next_ids = scores[torch.arange(len(rows), device=device), lengths-1].argmax(-1)
        active = ~finished
        seq[torch.arange(len(rows), device=device)[active], lengths[active]] = next_ids[active]
        lengths += active.long()
        finished |= next_ids == EOS_ID
        if bool(finished.all()):
            break
    return ["".join(ALPHABET[x] for x in seq[i, len(p):int(lengths[i])].tolist())
            for i, p in enumerate(prompts)]


def evaluate(model, dataset, r, cfg, out, verifier, device):
    model.eval()
    records, summaries = [], []
    prediction_log = out / f"predictions-r{r}.jsonl"
    prediction_log.write_text("")
    proof_dir = out / "certificates"
    proof_dir.mkdir(exist_ok=True)
    for split, rows in dataset.items():
        if split == "train":
            continue
        torch.cuda.synchronize()
        start = time.perf_counter()
        predictions = generate(model, rows, r, cfg["max_new_tokens"], device)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        atomic_json(out / f"raw-predictions-{split}-r{r}.json", [
            {**asdict(row), "prediction": prediction} for row, prediction in zip(rows, predictions)])
        accepted = diagnostic = parsed = 0
        for row, prediction in zip(rows, predictions):
            rec = {**asdict(row), "theorem_id": row.theorem_id, "prediction": prediction,
                   "expected": row.completion, "reference_valid": reference_valid(row, prediction),
                   "lean_accepted": False}
            diagnostic += rec["reference_valid"]
            try:
                art = compile_prediction(row, prediction)
                payload = canonical_bytes(art)
                path = proof_dir / f"{split}-{row.a}-{row.b}-r{r}.json"
                path.write_bytes(payload)
                result = subprocess.run([str(verifier), str(path)], capture_output=True, text=True, timeout=15)
                if result.returncode not in (0, 1, 2):
                    raise RuntimeError(f"verifier infrastructure failure {result.returncode}: {result.stderr}")
                rec.update(certificate=str(path.relative_to(out)), certificate_sha256=hashlib.sha256(payload).hexdigest(),
                           verifier_exit=result.returncode, verifier_output=(result.stdout + result.stderr).strip(),
                           lean_accepted=result.returncode == 0)
                parsed += 1
                accepted += rec["lean_accepted"]
            except ValueError as exc:
                rec["parse_error"] = str(exc)
            except (subprocess.TimeoutExpired, RuntimeError) as exc:
                rec["infrastructure_error"] = str(exc)
                with prediction_log.open("a") as stream:
                    stream.write(json.dumps(rec) + "\n")
                raise
            with prediction_log.open("a") as stream:
                stream.write(json.dumps(rec) + "\n")
            if rec["reference_valid"] != rec["lean_accepted"]:
                raise RuntimeError(f"Independent diagnostic/checker disagreement: {rec}")
            records.append(rec)
        summaries.append({"split": split, "n": len(rows), "lean_accepted": accepted,
                          "parsed": parsed, "acceptance_rate": accepted/len(rows),
                          "generation_seconds": elapsed, "diagnostic_valid": diagnostic})
    return summaries


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Experimental execution requires Helios/WMI SLURM")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/pilot.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    assert torch.cuda.is_available(), "This pilot requests a GPU"
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    device = torch.device("cuda")
    dataset = examples()
    base = ModelConfig(vocab_size=len(ALPHABET), width=cfg["width"], heads=cfg["heads"],
                       mlp_width=cfg["mlp_width"], prelude_layers=cfg["prelude_layers"],
                       core_layers=cfg["core_layers"], coda_layers=cfg["coda_layers"],
                       reference_recurrence=cfg["reference_recurrence"], max_sequence_length=64)
    # Adapter contributes 2*w*w parameters. Compensate using baseline MLP width
    # with integer rounding, report the exact residual mismatch below.
    stored_depth = base.prelude_layers + base.core_layers + base.coda_layers
    matched_mlp = base.mlp_width + round((2 * base.width) / (3 * stored_depth))
    specs = [("recurrent", base, None),
             ("standard_parameter", replace(base, mlp_width=matched_mlp), stored_depth),
             ("standard_depth", base, base.prelude_layers + base.reference_recurrence * base.core_layers + base.coda_layers)]
    report = {"schema": 1, "config": cfg, "model_config": asdict(base), "job_id": os.environ["SLURM_JOB_ID"],
              "hostname": os.uname().nodename, "torch": torch.__version__, "device": torch.cuda.get_device_name(),
              "checker_commit": CHECKER_COMMIT, "split_sizes": {k: len(v) for k,v in dataset.items()},
              "status": "running", "runs": [], "tier": "T4", "scope": "closed-addition certificate canary"}
    atomic_json(args.out / "summary.json", report)
    for seed in cfg["seeds"]:
        for name, model_cfg, depth in specs:
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            model = (RecurrentLM(model_cfg) if depth is None else
                     StandardTransformerLM(model_cfg, depth, norm_style="sandwich",
                                           initialization_depth=base.prelude_layers + base.reference_recurrence * base.core_layers + base.coda_layers)).to(device)
            opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"], weight_decay=0.01)
            rng = random.Random(seed + 17)
            recurrence_rng = torch.Generator().manual_seed(seed + 37)
            dest = args.out / f"{name}-seed{seed}"
            dest.mkdir()
            history, hist, capped, tokens_seen = [], Counter(), 0, 0
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            start = time.perf_counter()
            model.train()
            for step in range(cfg["steps"]):
                rows = [rng.choice(dataset["train"]) for _ in range(cfg["batch_size"])]
                x, y = batch(rows, device)
                r = None
                if name == "recurrent":
                    raw = sample_recurrence(cfg["recurrence_rate_mean"], generator=recurrence_rng)
                    r = min(raw, cfg["recurrence_cap"])
                    capped += raw > r
                    hist[r] += 1
                opt.zero_grad(set_to_none=True)
                scores = logits(model, x, r, cfg["backprop_depth"])
                loss = F.cross_entropy(scores[:, :-1].reshape(-1, len(ALPHABET)), y.reshape(-1))
                if not bool(torch.isfinite(loss)):
                    raise RuntimeError("nonfinite loss")
                loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
                opt.step()
                tokens_seen += int((y != -100).sum())
                if step % 100 == 0 or step == cfg["steps"] - 1:
                    history.append({"step":step+1,"completion_loss":float(loss),"grad_norm":float(grad_norm)})
            torch.cuda.synchronize()
            duration = time.perf_counter() - start
            run = {"name":name,"seed":seed,"parameters":unique_parameter_count(model),
                   "model_config":asdict(model_cfg),"standard_layers":depth,"norm_style":"sandwich",
                   "training_seconds":duration,"target_tokens_seen":tokens_seen,"recurrence_histogram":dict(hist),
                   "capped_draws":capped,"peak_gpu_bytes":torch.cuda.max_memory_allocated(),"history":history,"evaluations":[]}
            torch.save({"model":model.state_dict(),"model_config":asdict(model_cfg),"seed":seed,"name":name,
                        "layers":depth,"train_config":cfg}, dest / "model.pt")
            for r in (cfg["evaluation_recurrences"] if name == "recurrent" else [None]):
                metrics = evaluate(model, dataset, r, cfg, dest, args.verifier.resolve(), device)
                run["evaluations"].append({"recurrence":r,"block_evaluations":model.block_evaluations(r) if r else depth,"splits":metrics})
            atomic_json(dest / "metrics.json", run)
            report["runs"].append(run)
            atomic_json(args.out / "summary.json", report)
            print(json.dumps({"completed":name,"seed":seed,"training_seconds":duration,"evaluations":run["evaluations"]}), flush=True)
            del opt, model
            torch.cuda.empty_cache()
    report["status"] = "completed"
    atomic_json(args.out / "summary.json", report)


if __name__ == "__main__":
    main()
