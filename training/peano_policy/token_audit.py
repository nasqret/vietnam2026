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
from typing import Any, Iterable, Mapping

from .budget import (
    enforce_token_budget,
    tokenize_split,
    tokenizer_identity_record,
)
from .config import ExperimentConfig, load_config
from .corpus_eligibility import verify_sealed_corpus_eligibility
from .curriculum import load_curriculum
from .data import dataset_manifest_path, load_examples, tokenize_completion
from .manifest import sha256_file, write_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_FORMAT = "peano-policy-token-audit"
LEGACY_REPORT_VERSION = 1
REPORT_VERSION = 2


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


def _load_pinned_tokenizer(config: ExperimentConfig) -> tuple[Any, str]:
    """Load the tokenizer and prove that its immutable revision resolved exactly."""

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
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer, resolved


def _legacy_tokenizer_record(
    config: ExperimentConfig,
    tokenizer: Any,
    resolved_revision: str,
) -> dict[str, object]:
    """Retain the exact report shape consumed by historical audit readers."""

    return {
        "model_id": config.model.model_id,
        "requested_revision": config.model.revision,
        "resolved_revision": resolved_revision,
        "class": type(tokenizer).__name__,
        "vocab_size": len(tokenizer),
    }


def _legacy_audit(
    config: ExperimentConfig,
    tokenizer: Any,
    resolved_revision: str,
) -> dict[str, object]:
    """Run the original uncapped/capped split audit without changing its report."""

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
        "v": LEGACY_REPORT_VERSION,
        "status": "passed",
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
            "max_length": config.data.max_length,
        },
        "tokenizer": _legacy_tokenizer_record(
            config, tokenizer, resolved_revision
        ),
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


def _raw_input_identity(path: Path, *, display_path: str) -> dict[str, object]:
    """Bind one regular input's exact bytes without retaining its contents."""

    if not path.is_file():
        raise FileNotFoundError(f"token audit input does not exist: {path}")
    return {
        "path": display_path,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _curriculum_inputs(
    train_path: Path,
    eval_path: Path,
    config: ExperimentConfig,
) -> dict[str, dict[str, object]]:
    train_manifest = dataset_manifest_path(train_path)
    eval_manifest = dataset_manifest_path(eval_path)
    return {
        "train": _raw_input_identity(
            train_path, display_path=config.data.train_path
        ),
        "eval": _raw_input_identity(eval_path, display_path=config.data.eval_path),
        "train_manifest": _raw_input_identity(
            train_manifest, display_path=str(train_manifest)
        ),
        "eval_manifest": _raw_input_identity(
            eval_manifest, display_path=str(eval_manifest)
        ),
    }


def _summary_from_token_record(
    record: Mapping[str, object], *, max_length: int
) -> dict[str, int | float]:
    """Project the exact budget record onto the historical compact summary."""

    sequence = record["sequence"]
    if not isinstance(sequence, Mapping):  # produced by ``tokenize_split``
        raise RuntimeError("tokenized split record lacks sequence evidence")
    maximum = int(sequence["maximum"])
    return {
        "rows": int(record["rows"]),
        "minimum": int(sequence["minimum"]),
        "median": int(sequence["median"]),
        "p95": int(sequence["p95"]),
        "p99": int(sequence["p99"]),
        "maximum": maximum,
        "mean": float(sequence["mean"]),
        "budget": max_length,
        "headroom": max_length - maximum,
    }


def _require_curriculum_source_matches_inputs(
    attestation: Mapping[str, object],
    inputs: Mapping[str, Mapping[str, object]],
) -> None:
    """Prevent selected examples from floating away from reported raw bytes."""

    source = attestation.get("source")
    if not isinstance(source, Mapping):
        raise RuntimeError("curriculum attestation lacks source evidence")
    expected = {
        "train": inputs["train"],
        "manifest": inputs["train_manifest"],
    }
    for label, identity in expected.items():
        claimed = source.get(label)
        if not isinstance(claimed, Mapping) or any(
            claimed.get(key) != identity[key] for key in ("bytes", "sha256")
        ):
            raise RuntimeError(
                f"curriculum {label} source differs from the audited raw input"
            )


def _curriculum_audit(
    config: ExperimentConfig,
    tokenizer: Any,
    tokenizer_identity: Mapping[str, object],
) -> dict[str, object]:
    """Audit the exact selected model-v3 curriculum and capped evaluation view."""

    curriculum_config = config.curriculum
    if curriculum_config is None:  # guarded by the caller
        raise RuntimeError("curriculum audit requires a curriculum configuration")
    if config.run.max_train_samples is not None:
        raise ValueError("model-v3 curriculum forbids train-row subsampling")
    train_path = _repo_path(config.data.train_path)
    eval_path = _repo_path(config.data.eval_path)
    eligibility = verify_sealed_corpus_eligibility(
        _repo_path(curriculum_config.corpus_seal_path),
        configured_train_path=train_path,
        configured_eval_path=eval_path,
        historical_source_commit=curriculum_config.corpus_source_commit,
        historical_prepare_job_id=curriculum_config.corpus_prepare_job_id,
        sealed_content_sha256=curriculum_config.corpus_content_sha256,
    )
    before = _curriculum_inputs(train_path, eval_path, config)

    # Loading the complete train split is deliberate: selection is whole-session
    # and must first validate every source row.  The legacy sample cap therefore
    # has no authority over model-v3 training selection.
    curriculum = load_curriculum(
        train_path,
        seed=str(curriculum_config.selection_seed),
        synthetic_row_ceiling=curriculum_config.synthetic_row_ceiling,
    )
    eval_examples = load_examples(
        eval_path,
        max_samples=config.run.max_eval_samples,
        seed=config.run.seed + 1,
    )
    _, train_record = tokenize_split(
        curriculum.examples,
        tokenizer,
        role="train",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
        retain_encodings=False,
    )
    _, eval_record = tokenize_split(
        eval_examples,
        tokenizer,
        role="eval",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
        retain_encodings=False,
    )
    enforce_token_budget(
        train_record,
        max_total_tokens=curriculum_config.max_train_tokens,
        max_sum_squared_tokens=curriculum_config.max_train_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )
    enforce_token_budget(
        eval_record,
        max_total_tokens=curriculum_config.max_eval_tokens,
        max_sum_squared_tokens=curriculum_config.max_eval_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )

    after = _curriculum_inputs(train_path, eval_path, config)
    if before != after:
        raise RuntimeError("dataset bytes changed during the token audit")
    curriculum_attestation = curriculum.attestation
    _require_curriculum_source_matches_inputs(curriculum_attestation, after)

    return {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
            "max_length": config.data.max_length,
        },
        "tokenizer": dict(tokenizer_identity),
        "inputs": after,
        "sealed_corpus_eligibility": eligibility.record,
        "sealed_dataset_attestation": eligibility.dataset_attestation,
        "curriculum": curriculum_attestation,
        "compute_gates": {
            "max_train_tokens": curriculum_config.max_train_tokens,
            "max_eval_tokens": curriculum_config.max_eval_tokens,
            "max_train_squared_tokens": curriculum_config.max_train_squared_tokens,
            "max_eval_squared_tokens": curriculum_config.max_eval_squared_tokens,
            "max_supervised_tokens": config.generation.max_new_tokens,
        },
        # Keep these compact projections for the existing report-v1 and sealed
        # corpus readers.  The adjacent records bind every exact token id.
        "splits": {
            "train": _summary_from_token_record(
                train_record, max_length=config.data.max_length
            ),
            "eval": _summary_from_token_record(
                eval_record, max_length=config.data.max_length
            ),
        },
        "tokenized_splits": {
            "train": train_record,
            "eval": eval_record,
        },
    }


def audit_config(config: ExperimentConfig) -> dict[str, object]:
    """Load the pinned tokenizer and validate the exact selected train/val rows."""

    tokenizer, resolved_revision = _load_pinned_tokenizer(config)
    if config.curriculum is None:
        return _legacy_audit(config, tokenizer, resolved_revision)
    tokenizer_identity = tokenizer_identity_record(
        tokenizer,
        model_id=config.model.model_id,
        revision=resolved_revision,
    )
    return _curriculum_audit(config, tokenizer, tokenizer_identity)


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
    "LEGACY_REPORT_VERSION",
    "REPORT_FORMAT",
    "REPORT_VERSION",
    "audit_config",
    "main",
    "summarize_token_lengths",
]


if __name__ == "__main__":
    raise SystemExit(main())
