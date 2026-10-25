#!/usr/bin/env python3
"""Train the deadline Peano policy on one local Apple-Silicon GPU.

This runner is deliberately separate from the preregistered WMI experiment.
It trains a small, useful pilot quickly without changing the sealed 1.7B
configuration or acceptance manifest.  The model is an *untrusted* tactic
policy: its eventual output is useful only through Peano Lab's kernel-guided
search and independent checker.

Heavy ML packages are imported only after every path and dataset preflight.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for _root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from training.peano_policy.contract import (  # noqa: E402
    environment_record,
    model_v2_environment,
)
from training.peano_policy.data import (  # noqa: E402
    IGNORE_INDEX,
    load_dataset_manifest,
    load_examples,
    tokenize_completion,
)
from training.peano_policy.manifest import (  # noqa: E402
    artifact_directory_hash,
    require_safetensors_adapter,
    sha256_file,
    sha256_json,
    write_manifest,
)
from training.peano_policy.prompt import PromptError  # noqa: E402


FORMAT = "peano-local-mps-pilot"
VERSION = 1
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
DEFAULT_SNAPSHOT = Path(
    "/Users/bnaskrecki/.cache/huggingface/hub/"
    "models--Qwen--Qwen3-0.6B/snapshots/"
    f"{MODEL_REVISION}"
)
DEFAULT_TRAIN = REPOSITORY_ROOT / "data/peano-policy-v2-local-pilot/train.jsonl"
DEFAULT_VAL = REPOSITORY_ROOT / "data/peano-policy-v2-local-pilot/val.jsonl"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT / "results/peano-policy/qwen3-0.6b-local-pilot"
)
ADAPTER_SUBDIR = "adapter"
TOKENIZER_SUBDIR = "tokenizer"
MANIFEST_NAME = "local-pilot-manifest.json"
TARGET_MODULES = (
    "q_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)


@dataclass(frozen=True, slots=True)
class PilotConfig:
    seed: int
    max_steps: int
    max_wall_minutes: float
    max_length: int
    gradient_accumulation_steps: int
    learning_rate: float
    warmup_steps: int
    rank: int
    alpha: int
    dropout: float
    max_train_examples: int
    max_val_examples: int
    logging_steps: int
    gradient_checkpointing: bool
    device: str


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--val", type=Path, default=DEFAULT_VAL)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--max-wall-minutes", type=float, default=145.0)
    # Model-v2 prompts include the checked public-library snapshot.  A token
    # audit of this exact 10k-row curriculum found a minimum of 820 tokens, so
    # 512 would accept no row.  1024 is the smallest honest fixed window.
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--max-train-examples", type=int, default=4096)
    parser.add_argument("--max-val-examples", type=int, default=256)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--device", choices=("mps", "cpu"), default="mps")
    return parser


def _positive_int(name: str, value: int) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _validate_args(args: argparse.Namespace) -> PilotConfig:
    for name in (
        "max_steps",
        "max_length",
        "gradient_accumulation_steps",
        "warmup_steps",
        "rank",
        "alpha",
        "max_train_examples",
        "max_val_examples",
        "logging_steps",
    ):
        value = getattr(args, name)
        if name == "warmup_steps":
            if type(value) is not int or value < 0:
                raise ValueError("warmup_steps must be a non-negative integer")
        else:
            _positive_int(name, value)
    if args.max_length < 128 or args.max_length > 2048:
        raise ValueError("max_length must lie between 128 and 2048")
    if type(args.seed) is not int or args.seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not math.isfinite(args.max_wall_minutes) or args.max_wall_minutes <= 0:
        raise ValueError("max_wall_minutes must be positive and finite")
    if not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
        raise ValueError("learning_rate must be positive and finite")
    if not math.isfinite(args.dropout) or not 0 <= args.dropout < 1:
        raise ValueError("dropout must lie in [0, 1)")
    return PilotConfig(
        seed=args.seed,
        max_steps=args.max_steps,
        max_wall_minutes=args.max_wall_minutes,
        max_length=args.max_length,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        rank=args.rank,
        alpha=args.alpha,
        dropout=args.dropout,
        max_train_examples=args.max_train_examples,
        max_val_examples=args.max_val_examples,
        logging_steps=args.logging_steps,
        gradient_checkpointing=args.gradient_checkpointing,
        device=args.device,
    )


def _plain_input(path: Path, *, label: str) -> Path:
    absolute = path.expanduser().absolute()
    if absolute.is_symlink() or not absolute.is_file():
        raise FileNotFoundError(f"{label} must be one plain file: {absolute}")
    return absolute


def _fresh_output(path: Path) -> Path:
    absolute = path.expanduser().absolute()
    allowed = (REPOSITORY_ROOT / "results").resolve(strict=False)
    resolved = absolute.resolve(strict=False)
    if not resolved.is_relative_to(allowed):
        raise ValueError(f"output must live below {allowed}")
    if os.path.lexists(absolute):
        raise FileExistsError(
            f"refusing to reuse local-pilot output directory: {absolute}"
        )
    return absolute


def snapshot_identity(snapshot: Path) -> dict[str, object]:
    """Hash the exact logical files of one immutable HF snapshot.

    Hugging Face snapshots normally contain relative symlinks into the sibling
    ``blobs`` directory.  We reject all other links and bind both link text and
    resolved bytes, so a cache mutation cannot silently change the base model.
    """

    lexical = snapshot.expanduser().absolute()
    if lexical.is_symlink() or not lexical.is_dir():
        raise ValueError("base snapshot must be one plain directory")
    if lexical.name != MODEL_REVISION:
        raise ValueError("base snapshot path does not name the pinned revision")
    model_cache = lexical.parents[1].resolve(strict=True)
    entries: dict[str, dict[str, object]] = {}
    for item in sorted(lexical.iterdir(), key=lambda value: value.name):
        if item.name.startswith(".") or "/" in item.name:
            raise ValueError(f"unsafe base snapshot entry: {item.name!r}")
        link: str | None = None
        if item.is_symlink():
            link = os.readlink(item)
            if os.path.isabs(link):
                raise ValueError(f"absolute base snapshot symlink: {item.name}")
        resolved = item.resolve(strict=True)
        if not resolved.is_relative_to(model_cache):
            raise ValueError(f"base snapshot entry escapes model cache: {item.name}")
        if not resolved.is_file():
            raise ValueError(f"base snapshot entry is not a file: {item.name}")
        stat = resolved.stat()
        entries[item.name] = {
            "link": link,
            "bytes": stat.st_size,
            "sha256": sha256_file(resolved),
        }
    required = {"config.json", "model.safetensors", "tokenizer.json"}
    if not required <= set(entries):
        raise ValueError("base snapshot is incomplete")
    return {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "path": str(lexical),
        "files": entries,
        "sha256": sha256_json(entries),
        "bytes": sum(int(record["bytes"]) for record in entries.values()),
    }


def _validate_dataset(train_path: Path, val_path: Path) -> dict[str, object]:
    train_manifest = train_path.parent / "manifest.json"
    val_manifest = val_path.parent / "manifest.json"
    if train_manifest != val_manifest:
        raise ValueError("train and validation splits need one shared manifest")
    manifest_path = _plain_input(train_manifest, label="dataset manifest")
    manifest = load_dataset_manifest(manifest_path)
    expected_environment = environment_record(model_v2_environment())
    environments = manifest.get("environments")
    if type(environments) is not list or len(environments) != 1:
        raise ValueError("local pilot requires exactly one checked environment")
    environment = environments[0]
    if type(environment) is not dict:
        raise ValueError("dataset environment is malformed")
    observed = {key: environment.get(key) for key in expected_environment}
    if observed != expected_environment:
        raise ValueError("dataset is not the exact model-v2 Peano environment")
    return {
        "train": {"path": str(train_path), "sha256": sha256_file(train_path)},
        "val": {"path": str(val_path), "sha256": sha256_file(val_path)},
        "builder_manifest": {
            "path": str(manifest_path),
            "sha256": sha256_file(manifest_path),
        },
        "environment": expected_environment,
        "builder_summary": {
            "source": manifest.get("source"),
            "replay": manifest.get("replay"),
            "splits": manifest.get("splits"),
        },
    }


def _source_identity() -> dict[str, object]:
    paths = (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "training/peano_policy/data.py",
        REPOSITORY_ROOT / "training/peano_policy/prompt.py",
        REPOSITORY_ROOT / "training/peano_policy/contract.py",
        REPOSITORY_ROOT / "training/peano_policy/manifest.py",
    )
    files = {
        str(path.relative_to(REPOSITORY_ROOT)): sha256_file(path)
        for path in paths
    }
    return {"files": files, "sha256": sha256_json(files)}


def _tokenize_fitting(
    examples: Iterable[Any], tokenizer: Any, *, max_length: int
) -> tuple[list[dict[str, list[int]]], int]:
    rows: list[dict[str, list[int]]] = []
    skipped = 0
    for example in examples:
        try:
            rows.append(tokenize_completion(example, tokenizer, max_length=max_length))
        except PromptError as exc:
            if "does not fit max_length" not in str(exc):
                raise
            skipped += 1
    return rows, skipped


def _batch_one(torch: Any, row: dict[str, list[int]], device: str) -> dict[str, Any]:
    return {
        key: torch.tensor([value], dtype=torch.long, device=device)
        for key, value in row.items()
    }


def _learning_rate_scale(step: int, config: PilotConfig) -> float:
    if step < config.warmup_steps:
        return float(step + 1) / max(1, config.warmup_steps)
    progress = (step - config.warmup_steps) / max(
        1, config.max_steps - config.warmup_steps
    )
    return 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))


def _evaluate_loss(
    model: Any,
    rows: list[dict[str, list[int]]],
    *,
    torch: Any,
    device: str,
    deadline: float,
) -> tuple[float | None, int]:
    model.eval()
    losses: list[float] = []
    with torch.inference_mode():
        for row in rows:
            if time.monotonic() >= deadline:
                break
            loss = model(**_batch_one(torch, row, device)).loss
            losses.append(float(loss.detach().cpu()))
    model.train()
    return (sum(losses) / len(losses) if losses else None), len(losses)


def train(args: argparse.Namespace) -> Path:
    config = _validate_args(args)
    train_path = _plain_input(args.train, label="training split")
    val_path = _plain_input(args.val, label="validation split")
    output = _fresh_output(args.output)
    snapshot_before = snapshot_identity(args.snapshot)
    dataset_identity = _validate_dataset(train_path, val_path)
    source_before = _source_identity()

    # Heavy imports and device initialization happen only after static gates.
    import torch
    import transformers
    import peft
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if config.device == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable; run outside the restricted sandbox")
    random.seed(config.seed)
    torch.manual_seed(config.seed)
    if config.device == "mps":
        torch.mps.manual_seed(config.seed)

    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    deadline = started + config.max_wall_minutes * 60.0
    snapshot_path = Path(str(snapshot_before["path"]))
    tokenizer = AutoTokenizer.from_pretrained(
        str(snapshot_path), use_fast=True, local_files_only=True
    )
    if tokenizer.eos_token_id is None:
        raise RuntimeError("base tokenizer has no EOS token")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    train_examples = load_examples(
        train_path, max_samples=config.max_train_examples, seed=config.seed
    )
    val_examples = load_examples(
        val_path, max_samples=config.max_val_examples, seed=config.seed + 1
    )
    train_rows, train_skipped = _tokenize_fitting(
        train_examples, tokenizer, max_length=config.max_length
    )
    val_rows, val_skipped = _tokenize_fitting(
        val_examples, tokenizer, max_length=config.max_length
    )
    if len(train_rows) < config.gradient_accumulation_steps:
        raise ValueError("too few training rows fit the local context window")

    # Do not allocate the 0.6B model until the complete replay-builder/data and
    # tokenizer-context gates have passed.
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot_path),
        dtype=torch.float16,
        attn_implementation="sdpa",
        trust_remote_code=False,
        use_safetensors=True,
        local_files_only=True,
    )
    model.config.use_cache = False
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
    model = get_peft_model(
        model,
        LoraConfig(
            r=config.rank,
            lora_alpha=config.alpha,
            lora_dropout=config.dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(TARGET_MODULES),
        ),
    )
    model.to(config.device)
    model.train()

    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=config.learning_rate, weight_decay=0.01)
    optimizer.zero_grad(set_to_none=True)
    order = list(range(len(train_rows)))
    rng = random.Random(config.seed)
    rng.shuffle(order)
    cursor = 0
    completed_steps = 0
    observed_losses: list[float] = []
    stop_reason = "max_steps"

    print(
        json.dumps(
            {
                "event": "training_start",
                "device": config.device,
                "train_rows": len(train_rows),
                "val_rows": len(val_rows),
                "max_steps": config.max_steps,
                "deadline_minutes": config.max_wall_minutes,
                "trainable_parameters": sum(p.numel() for p in trainable),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    while completed_steps < config.max_steps:
        if time.monotonic() >= deadline:
            stop_reason = "wall_time"
            break
        accumulated = 0.0
        microbatches = 0
        for _ in range(config.gradient_accumulation_steps):
            if time.monotonic() >= deadline:
                break
            if cursor == len(order):
                rng.shuffle(order)
                cursor = 0
            row = train_rows[order[cursor]]
            cursor += 1
            loss = model(**_batch_one(torch, row, config.device)).loss
            if not bool(torch.isfinite(loss).item()):
                raise RuntimeError("training produced a non-finite loss")
            (loss / config.gradient_accumulation_steps).backward()
            accumulated += float(loss.detach().cpu())
            microbatches += 1
        if microbatches != config.gradient_accumulation_steps:
            optimizer.zero_grad(set_to_none=True)
            stop_reason = "wall_time"
            break
        scale = _learning_rate_scale(completed_steps, config)
        for group in optimizer.param_groups:
            group["lr"] = config.learning_rate * scale
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        completed_steps += 1
        step_loss = accumulated / microbatches
        observed_losses.append(step_loss)
        if config.device == "mps":
            torch.mps.synchronize()
        if completed_steps == 1 or completed_steps % config.logging_steps == 0:
            print(
                json.dumps(
                    {
                        "event": "training_progress",
                        "step": completed_steps,
                        "loss": step_loss,
                        "learning_rate": optimizer.param_groups[0]["lr"],
                        "elapsed_seconds": round(time.monotonic() - started, 1),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if completed_steps < 1:
        raise RuntimeError("deadline elapsed before one complete optimizer step")

    validation_loss, validation_rows = _evaluate_loss(
        model,
        val_rows,
        torch=torch,
        device=config.device,
        deadline=deadline,
    )
    output.mkdir(parents=True)
    adapter_dir = output / ADAPTER_SUBDIR
    tokenizer_dir = output / TOKENIZER_SUBDIR
    model.save_pretrained(adapter_dir, safe_serialization=True)
    tokenizer.save_pretrained(tokenizer_dir)

    snapshot_after = snapshot_identity(snapshot_path)
    if snapshot_after != snapshot_before:
        raise RuntimeError("base snapshot changed while local training was active")
    source_after = _source_identity()
    if source_after != source_before:
        raise RuntimeError("local trainer source changed while training was active")
    if (
        sha256_file(train_path) != dataset_identity["train"]["sha256"]
        or sha256_file(val_path) != dataset_identity["val"]["sha256"]
        or sha256_file(train_path.parent / "manifest.json")
        != dataset_identity["builder_manifest"]["sha256"]
    ):
        raise RuntimeError("dataset changed while local training was active")

    adapter_artifacts = artifact_directory_hash(output, ADAPTER_SUBDIR)
    tokenizer_artifacts = artifact_directory_hash(output, TOKENIZER_SUBDIR)
    require_safetensors_adapter(adapter_artifacts)
    elapsed = time.monotonic() - started
    manifest = {
        "format": FORMAT,
        "v": VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "complete",
        "warning": (
            "Untrusted next-tactic policy; publish proofs only after Peano Lab "
            "kernel replay against the original theorem."
        ),
        "run": {
            "name": "qwen3-0.6b-local-pilot",
            "started_at": started_wall.replace(microsecond=0).isoformat(),
            "elapsed_seconds": elapsed,
            "stop_reason": stop_reason,
            "config": asdict(config),
            "completed_optimizer_steps": completed_steps,
            "completed_microbatches": (
                completed_steps * config.gradient_accumulation_steps
            ),
        },
        "base_model": snapshot_before,
        "dataset": dataset_identity,
        "source": source_before,
        "runtime": {
            "python": sys.version,
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "peft": peft.__version__,
            "device": config.device,
            "dtype": "float16",
            "attention": "sdpa",
        },
        "lora": {
            "rank": config.rank,
            "alpha": config.alpha,
            "dropout": config.dropout,
            "target_modules": list(TARGET_MODULES),
            "trainable_parameters": sum(p.numel() for p in trainable),
        },
        "data_selection": {
            "train_loaded": len(train_examples),
            "train_tokenized": len(train_rows),
            "train_overlength_skipped": train_skipped,
            "val_loaded": len(val_examples),
            "val_tokenized": len(val_rows),
            "val_overlength_skipped": val_skipped,
        },
        "metrics": {
            "last_train_loss": observed_losses[-1],
            "mean_train_loss": sum(observed_losses) / len(observed_losses),
            "validation_loss": validation_loss,
            "validation_rows": validation_rows,
        },
        "adapter": adapter_artifacts,
        "tokenizer": tokenizer_artifacts,
    }
    manifest_path = output / MANIFEST_NAME
    write_manifest(manifest_path, manifest)
    print(
        json.dumps(
            {
                "event": "training_complete",
                "manifest": str(manifest_path),
                "steps": completed_steps,
                "stop_reason": stop_reason,
                "elapsed_seconds": round(elapsed, 1),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return manifest_path


def main() -> int:
    manifest = train(_parser().parse_args())
    print(json.dumps({"manifest": str(manifest)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
