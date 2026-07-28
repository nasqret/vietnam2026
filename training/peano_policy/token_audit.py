#!/usr/bin/env python3
"""Audit every selected policy row against the pinned tokenizer budget.

The one-example CUDA smoke proves that the accelerator stack works.  This
separate CPU-side gate proves that *all* rows selected by the training config
fit without truncating the prompt, environment, retrieved library, or target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .config import ExperimentConfig, load_config
from .data import load_examples, tokenize_completion
from .manifest import sha256_file, write_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_FORMAT = "peano-policy-token-audit"
REPORT_VERSION = 1


def _repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def _nearest_rank(sorted_values: list[int], numerator: int, denominator: int) -> int:
    if not sorted_values:
        raise ValueError("cannot summarize an empty token-length collection")
    index = ((len(sorted_values) - 1) * numerator + denominator - 1) // denominator
    return sorted_values[index]


def summarize_token_lengths(
    examples: Iterable[Any],
    tokenizer: Any,
    *,
    max_length: int,
) -> dict[str, int | float]:
    """Tokenize all examples and return a deterministic compact distribution."""

    lengths = [
        len(tokenize_completion(example, tokenizer, max_length=max_length)["input_ids"])
        for example in examples
    ]
    if not lengths:
        raise ValueError("token audit split is empty")
    lengths.sort()
    return {
        "rows": len(lengths),
        "minimum": lengths[0],
        "median": _nearest_rank(lengths, 1, 2),
        "p95": _nearest_rank(lengths, 95, 100),
        "p99": _nearest_rank(lengths, 99, 100),
        "maximum": lengths[-1],
        "mean": round(sum(lengths) / len(lengths), 3),
        "budget": max_length,
        "headroom": max_length - lengths[-1],
    }


def audit_config(config: ExperimentConfig) -> dict[str, object]:
    """Load the pinned tokenizer and validate the exact selected train/val rows."""

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=config.model.trust_remote_code,
    )
    resolved = tokenizer.init_kwargs.get("_commit_hash") or config.model.revision
    if resolved != config.model.revision:
        raise RuntimeError("resolved tokenizer snapshot differs from the pinned revision")
    if tokenizer.eos_token_id is None:
        raise RuntimeError("base tokenizer has no EOS token")

    train_path = _repo_path(config.data.train_path)
    eval_path = _repo_path(config.data.eval_path)
    train_examples = load_examples(
        train_path,
        max_samples=config.run.max_train_samples,
        seed=config.run.seed,
    )
    eval_examples = load_examples(
        eval_path,
        max_samples=config.run.max_eval_samples,
        seed=config.run.seed + 1,
    )
    return {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
            "max_length": config.data.max_length,
        },
        "tokenizer": {
            "model_id": config.model.model_id,
            "requested_revision": config.model.revision,
            "resolved_revision": resolved,
            "class": type(tokenizer).__name__,
            "vocab_size": len(tokenizer),
        },
        "inputs": {
            "train": {"path": config.data.train_path, "sha256": sha256_file(train_path)},
            "eval": {"path": config.data.eval_path, "sha256": sha256_file(eval_path)},
        },
        "splits": {
            "train": summarize_token_lengths(
                train_examples, tokenizer, max_length=config.data.max_length
            ),
            "eval": summarize_token_lengths(
                eval_examples, tokenizer, max_length=config.data.max_length
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit_config(load_config(args.config))
    if args.output is None:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        if args.output.exists():
            raise FileExistsError(f"refusing to replace token audit: {args.output}")
        write_manifest(args.output, report)
        print(json.dumps({"report": str(args.output)}, sort_keys=True))
    return 0


__all__ = [
    "REPORT_FORMAT",
    "REPORT_VERSION",
    "audit_config",
    "main",
    "summarize_token_lengths",
]


if __name__ == "__main__":
    raise SystemExit(main())
