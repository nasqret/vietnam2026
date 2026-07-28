#!/usr/bin/env python3
"""BF16 LoRA completion SFT for a Qwen3 Peano next-tactic policy.

Heavy dependencies are imported only inside ``train``.  Importing this module
is therefore safe in documentation tools and lightweight unit tests.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import random
from typing import Any

from .attest import attest_dataset
from .config import ExperimentConfig, load_config
from .data import (
    IGNORE_INDEX,
    dataset_manifest_path,
    load_examples,
    tokenize_completion,
)
from .manifest import (
    ADAPTER_SUBDIR,
    MANIFEST_VERSION,
    TOKENIZER_SUBDIR,
    artifact_directory_hash,
    sha256_file,
    sha256_json,
    source_hash,
    write_manifest,
)
from .prompt import PEANO_PROMPT_VERSION, prompt_manifest_record
from .runtime import deployment_identity, runtime_identity, slurm_job_identity


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(__file__).resolve().parent
RUN_IDENTITY_VERSION = 1


def _repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


@dataclass(frozen=True, slots=True)
class ResumeDecision:
    trainer_value: str | bool
    checkpoint: str | None
    checkpoint_sha256: str | None
    global_step: int | None


def _run_identity(
    config: ExperimentConfig,
    *,
    train_path: Path,
    eval_path: Path,
    dataset_attestation: dict[str, object],
    deployment: dict[str, object],
) -> dict[str, Any]:
    """Identity that every checkpoint in an output directory must share."""

    train_manifest = dataset_manifest_path(train_path)
    eval_manifest = dataset_manifest_path(eval_path)
    return {
        "v": RUN_IDENTITY_VERSION,
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
            "resolved": {
                "run": asdict(config.run),
                "model": asdict(config.model),
                "data": asdict(config.data),
                "lora": asdict(config.lora),
                "trainer": asdict(config.trainer),
                "generation": asdict(config.generation),
            },
        },
        "model": {
            "id": config.model.model_id,
            "revision": config.model.revision,
        },
        "prompt_version": PEANO_PROMPT_VERSION,
        "prompt_contract_sha256": sha256_json(prompt_manifest_record()),
        "inputs": {
            "train": sha256_file(train_path),
            "eval": sha256_file(eval_path),
            "train_manifest": sha256_file(train_manifest),
            "eval_manifest": sha256_file(eval_manifest),
            "dataset_attestation": dataset_attestation,
        },
        "source": source_hash(SOURCE_ROOT),
        "deployment": deployment,
    }


def _ensure_run_identity(output_dir: Path, identity: dict[str, Any]) -> tuple[Path, str]:
    path = output_dir / "run-identity.json"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot validate existing run identity: {exc}") from None
        if existing != identity:
            raise ValueError(
                "output directory belongs to a different training identity"
            )
    else:
        write_manifest(path, identity)
    return path, sha256_file(path)


def _checkpoint_step(path: Path) -> int:
    state_path = path / "trainer_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read checkpoint trainer state {state_path}: {exc}") from None
    step = state.get("global_step") if isinstance(state, dict) else None
    if type(step) is not int or step < 0:
        raise ValueError(f"checkpoint has no valid global_step: {state_path}")
    return step


def _resume_decision(
    output_dir: Path,
    requested: str,
    get_last_checkpoint: Any,
    *,
    run_identity_sha256: str,
) -> ResumeDecision:
    if requested == "never":
        return ResumeDecision(False, None, None, None)
    candidate = (
        get_last_checkpoint(str(output_dir))
        if requested == "auto" and output_dir.is_dir()
        else requested
    )
    if not candidate:
        return ResumeDecision(False, None, None, None)
    checkpoint = _repo_path(str(candidate)).resolve()
    if not checkpoint.is_dir():
        raise FileNotFoundError(f"checkpoint does not exist: {checkpoint}")
    checkpoint_identity = checkpoint.parent / "run-identity.json"
    if (
        not checkpoint_identity.is_file()
        or sha256_file(checkpoint_identity) != run_identity_sha256
    ):
        raise ValueError(
            "checkpoint training identity does not match the requested run"
        )
    checkpoint_artifacts = source_hash(checkpoint)
    return ResumeDecision(
        str(checkpoint),
        str(checkpoint),
        str(checkpoint_artifacts["sha256"]),
        _checkpoint_step(checkpoint),
    )


def _set_seeds(seed: int, torch: Any, transformers_set_seed: Any) -> None:
    if os.environ.get("PYTHONHASHSEED") != str(seed):
        raise RuntimeError(
            f"launch training with PYTHONHASHSEED={seed}; setting it after "
            "interpreter startup is ineffective"
        )
    random.seed(seed)
    try:
        import numpy
    except ImportError:
        numpy = None
    if numpy is not None:
        numpy.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    transformers_set_seed(seed)


class _CompletionCollator:
    """Right-pad ids/masks while preserving the completion-only label mask."""

    def __init__(self, torch: Any, pad_token_id: int) -> None:
        self._torch = torch
        self._pad_token_id = pad_token_id

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        width = max(len(feature["input_ids"]) for feature in features)

        def padded(name: str, fill: int) -> list[list[int]]:
            return [
                feature[name] + [fill] * (width - len(feature[name]))
                for feature in features
            ]

        return {
            "input_ids": self._torch.tensor(
                padded("input_ids", self._pad_token_id), dtype=self._torch.long
            ),
            "attention_mask": self._torch.tensor(
                padded("attention_mask", 0), dtype=self._torch.long
            ),
            "labels": self._torch.tensor(
                padded("labels", IGNORE_INDEX), dtype=self._torch.long
            ),
        }


def train(config: ExperimentConfig, *, resume_override: str | None = None) -> Path:
    """Run one adapter experiment and return its provenance manifest path."""

    output_dir = _repo_path(config.run.output_dir)
    train_path = _repo_path(config.data.train_path)
    eval_path = _repo_path(config.data.eval_path)
    deployment = deployment_identity()
    dataset_attestation = attest_dataset(train_path, eval_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_identity = _run_identity(
        config,
        train_path=train_path,
        eval_path=eval_path,
        dataset_attestation=dataset_attestation,
        deployment=deployment,
    )
    run_identity_path, run_identity_sha256 = _ensure_run_identity(
        output_dir, run_identity
    )

    # Kept lazy so static/data tooling never initializes CUDA or imports torch.
    import torch
    from peft import LoraConfig as PeftLoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        set_seed,
    )
    from transformers.trainer_utils import get_last_checkpoint

    _set_seeds(config.run.seed, torch, set_seed)

    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=config.model.trust_remote_code,
    )
    if tokenizer.eos_token_id is None:
        raise RuntimeError("base tokenizer has no EOS token")
    tokenizer_commit = (
        tokenizer.init_kwargs.get("_commit_hash") or config.model.revision
    )
    if tokenizer_commit != config.model.revision:
        raise RuntimeError(
            "resolved tokenizer snapshot differs from the pinned model revision"
        )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        torch_dtype=torch.bfloat16,
        attn_implementation=config.model.attn_implementation,
        trust_remote_code=config.model.trust_remote_code,
    )
    model_commit = getattr(model.config, "_commit_hash", None) or config.model.revision
    if model_commit != config.model.revision:
        raise RuntimeError(
            "resolved model snapshot differs from the pinned model revision"
        )
    model_config = model.config.to_dict()
    model.config.use_cache = False
    if config.trainer.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
    model = get_peft_model(
        model,
        PeftLoraConfig(
            r=config.lora.rank,
            lora_alpha=config.lora.alpha,
            lora_dropout=config.lora.dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(config.lora.target_modules),
        ),
    )

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
    if not train_examples:
        raise ValueError("the replay-validated training split is empty")
    train_dataset = [
        tokenize_completion(example, tokenizer, max_length=config.data.max_length)
        for example in train_examples
    ]
    eval_dataset = [
        tokenize_completion(example, tokenizer, max_length=config.data.max_length)
        for example in eval_examples
    ]

    arguments = TrainingArguments(
        output_dir=str(output_dir),
        overwrite_output_dir=False,
        num_train_epochs=config.trainer.epochs,
        max_steps=config.trainer.max_steps,
        per_device_train_batch_size=config.trainer.per_device_train_batch_size,
        per_device_eval_batch_size=config.trainer.per_device_eval_batch_size,
        gradient_accumulation_steps=config.trainer.gradient_accumulation_steps,
        learning_rate=config.trainer.learning_rate,
        weight_decay=config.trainer.weight_decay,
        warmup_ratio=config.trainer.warmup_ratio,
        lr_scheduler_type="cosine",
        optim="adamw_torch_fused",
        bf16=True,
        bf16_full_eval=bool(eval_examples),
        tf32=True,
        gradient_checkpointing=config.trainer.gradient_checkpointing,
        logging_steps=config.trainer.logging_steps,
        eval_strategy="steps" if eval_examples else "no",
        eval_steps=config.trainer.eval_steps,
        save_strategy="steps",
        save_steps=config.trainer.save_steps,
        save_total_limit=config.trainer.save_total_limit,
        report_to=[],
        seed=config.run.seed,
        data_seed=config.run.seed,
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset or None,
        data_collator=_CompletionCollator(torch, tokenizer.pad_token_id),
    )
    resume_requested = resume_override or config.run.resume
    resume = _resume_decision(
        output_dir,
        resume_requested,
        get_last_checkpoint,
        run_identity_sha256=run_identity_sha256,
    )
    train_result = trainer.train(resume_from_checkpoint=resume.trainer_value)
    eval_metrics = trainer.evaluate() if eval_examples else {}
    adapter_output = output_dir / ADAPTER_SUBDIR
    tokenizer_output = output_dir / TOKENIZER_SUBDIR
    trainer.save_model(str(adapter_output))
    tokenizer.save_pretrained(str(tokenizer_output))

    # A sync while a job is running must not let imported old code masquerade as
    # newly hashed source.  Recheck every identity-bearing input before the
    # final manifest is published.
    current_source = source_hash(SOURCE_ROOT)
    if current_source != run_identity["source"]:
        raise RuntimeError("training source changed while the run was active")
    if deployment_identity() != deployment:
        raise RuntimeError("source deployment changed while the run was active")
    if (
        sha256_file(config.path) != run_identity["config"]["sha256"]
        or sha256_file(train_path) != run_identity["inputs"]["train"]
        or sha256_file(eval_path) != run_identity["inputs"]["eval"]
        or sha256_file(dataset_manifest_path(train_path))
        != run_identity["inputs"]["train_manifest"]
        or sha256_file(dataset_manifest_path(eval_path))
        != run_identity["inputs"]["eval_manifest"]
    ):
        raise RuntimeError("training configuration or dataset changed during the run")

    tokenizer_identity = {
        "class": type(tokenizer).__name__,
        "commit": tokenizer_commit,
        "special_tokens": tokenizer.special_tokens_map,
        "vocab_size": len(tokenizer),
    }
    adapter_artifacts = artifact_directory_hash(output_dir, ADAPTER_SUBDIR)
    tokenizer_artifacts = artifact_directory_hash(output_dir, TOKENIZER_SUBDIR)
    manifest = {
        "v": MANIFEST_VERSION,
        "prompt_version": PEANO_PROMPT_VERSION,
        "prompt_contract_sha256": sha256_json(prompt_manifest_record()),
        "run": asdict(config.run),
        "generation": asdict(config.generation),
        "base_model": {
            "id": config.model.model_id,
            "requested_revision": config.model.revision,
            "resolved_snapshot_hash": model_commit,
            "config_sha256": sha256_json(model_config),
        },
        "tokenizer": {
            "resolved_snapshot_hash": tokenizer_commit,
            "identity_sha256": sha256_json(tokenizer_identity),
            "artifacts": tokenizer_artifacts,
        },
        "adapter": adapter_artifacts,
        "inputs": {
            "dataset_attestation": dataset_attestation,
            "train_data": {"path": config.data.train_path, "sha256": sha256_file(train_path)},
            "eval_data": {"path": config.data.eval_path, "sha256": sha256_file(eval_path)},
            "train_dataset_manifest": {
                "path": str(dataset_manifest_path(train_path)),
                "sha256": sha256_file(dataset_manifest_path(train_path)),
            },
            "eval_dataset_manifest": {
                "path": str(dataset_manifest_path(eval_path)),
                "sha256": sha256_file(dataset_manifest_path(eval_path)),
            },
            "config": {"path": str(config.path), "sha256": sha256_file(config.path)},
            "run_identity": {
                "path": str(run_identity_path),
                "sha256": run_identity_sha256,
            },
            "source": current_source,
            "deployment": deployment,
        },
        "runtime": {
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "peft": __import__("peft").__version__,
            "accelerate": __import__("accelerate").__version__,
            "dtype": config.model.dtype,
            "attention": config.model.attn_implementation,
            "resume": asdict(resume),
            "environment": runtime_identity(torch),
            "job": slurm_job_identity(),
        },
        "metrics": {
            "train": train_result.metrics,
            "eval": eval_metrics,
            "train_examples": len(train_examples),
            "eval_examples": len(eval_examples),
        },
    }
    manifest_path = output_dir / "training-manifest.json"
    write_manifest(manifest_path, manifest)
    return manifest_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--resume-from-checkpoint",
        metavar="AUTO|NEVER|PATH",
        help="override [run].resume; AUTO discovers the latest checkpoint",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    override = args.resume_from_checkpoint
    if override is not None:
        override = {"AUTO": "auto", "NEVER": "never"}.get(override.upper(), override)
    path = train(load_config(args.config), resume_override=override)
    print(json.dumps({"manifest": str(path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
