#!/usr/bin/env python3
"""One real accelerator forward/backward and LoRA save/reload preflight."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import tempfile
from typing import Any

from .config import ExperimentConfig, load_config
from .data import load_examples, tokenize_completion
from .manifest import (
    ADAPTER_SUBDIR,
    TOKENIZER_SUBDIR,
    artifact_directory_hash,
    require_safetensors_adapter,
    verify_artifact_directory,
    write_manifest,
)
from .runtime import runtime_identity, slurm_job_identity


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9._-]{1,64}")


@dataclass(frozen=True, slots=True)
class SmokePlatformContract:
    """Small site contract checked before an expensive model smoke."""

    expected_machine: str = "aarch64"
    minimum_cuda_capability: tuple[int, int] | None = None
    report_format: str = "peano-policy-gh200-smoke"

    def __post_init__(self) -> None:
        if _SAFE_TOKEN_RE.fullmatch(self.expected_machine) is None:
            raise ValueError("expected machine must be one safe token")
        if _SAFE_TOKEN_RE.fullmatch(self.report_format) is None:
            raise ValueError("report format must be one safe token")
        capability = self.minimum_cuda_capability
        if capability is not None and (
            type(capability) is not tuple
            or len(capability) != 2
            or any(type(value) is not int or value < 0 or value > 99 for value in capability)
        ):
            raise ValueError("minimum CUDA capability must be a nonnegative pair")


DEFAULT_PLATFORM_CONTRACT = SmokePlatformContract()


def _parse_cuda_capability(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]{1,2})\.([0-9]{1,2})", value)
    if match is None:
        raise argparse.ArgumentTypeError("expected CUDA capability MAJOR.MINOR")
    return int(match.group(1)), int(match.group(2))


def _safe_token(value: str) -> str:
    if _SAFE_TOKEN_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("expected one safe ASCII token")
    return value


def _verify_machine(contract: SmokePlatformContract) -> None:
    machine = platform.machine()
    if machine != contract.expected_machine:
        raise RuntimeError(
            f"preflight requires machine {contract.expected_machine}, got {machine}"
        )


def _verify_accelerator(torch: Any, contract: SmokePlatformContract) -> None:
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("the allocated accelerator does not support CUDA BF16")
    minimum = contract.minimum_cuda_capability
    if minimum is not None:
        actual = tuple(torch.cuda.get_device_capability(0))
        if actual < minimum:
            raise RuntimeError(
                f"preflight requires CUDA capability {minimum[0]}.{minimum[1]}, "
                f"got {actual[0]}.{actual[1]}"
            )


def _platform_contract_record(
    contract: SmokePlatformContract,
) -> dict[str, object] | None:
    if contract == DEFAULT_PLATFORM_CONTRACT:
        return None
    minimum = contract.minimum_cuda_capability
    return {
        "expected_machine": contract.expected_machine,
        "minimum_cuda_capability": (
            None if minimum is None else [minimum[0], minimum[1]]
        ),
        "report_format": contract.report_format,
    }


def _repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def _resolved_commit(value: object, requested: str, label: str) -> str:
    commit = value or requested
    if commit != requested:
        raise RuntimeError(f"{label} resolved to a different model commit")
    return str(commit)


def _one_batch(example: Any, tokenizer: Any, torch: Any, max_length: int) -> dict[str, Any]:
    encoded = tokenize_completion(example, tokenizer, max_length=max_length)
    return {
        name: torch.tensor([values], dtype=torch.long, device="cuda")
        for name, values in encoded.items()
    }


def run_smoke(
    config: ExperimentConfig,
    *,
    platform_contract: SmokePlatformContract = DEFAULT_PLATFORM_CONTRACT,
) -> dict[str, object]:
    """Exercise the exact tokenizer, model, LoRA, optimizer, and reload stack."""

    _verify_machine(platform_contract)
    expected_hash_seed = str(config.run.seed)
    if os.environ.get("PYTHONHASHSEED") != expected_hash_seed:
        raise RuntimeError(f"launch the smoke with PYTHONHASHSEED={expected_hash_seed}")

    import torch
    from peft import LoraConfig as PeftLoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    _verify_accelerator(torch, platform_contract)
    random.seed(config.run.seed)
    torch.manual_seed(config.run.seed)
    torch.cuda.manual_seed_all(config.run.seed)
    set_seed(config.run.seed)

    tokenizer = AutoTokenizer.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        use_fast=True,
        trust_remote_code=False,
    )
    tokenizer_commit = _resolved_commit(
        tokenizer.init_kwargs.get("_commit_hash"),
        config.model.revision,
        "tokenizer",
    )
    if tokenizer.eos_token_id is None:
        raise RuntimeError("base tokenizer has no EOS token")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    examples = load_examples(
        _repo_path(config.data.train_path),
        max_samples=1,
        seed=config.run.seed,
    )
    if len(examples) != 1:
        raise RuntimeError("training smoke could not select exactly one checked row")
    prompt_ids = tokenizer(examples[0].prompt, add_special_tokens=False)["input_ids"]

    model = AutoModelForCausalLM.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        torch_dtype=torch.bfloat16,
        attn_implementation=config.model.attn_implementation,
        trust_remote_code=False,
        use_safetensors=True,
    )
    model_commit = _resolved_commit(
        getattr(model.config, "_commit_hash", None),
        config.model.revision,
        "model",
    )
    model.config.use_cache = False
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
    ).to("cuda")
    batch = _one_batch(examples[0], tokenizer, torch, config.data.max_length)
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not trainable:
        raise RuntimeError("LoRA smoke produced no trainable parameters")
    trainable_parameters = sum(parameter.numel() for parameter in trainable)
    optimizer = torch.optim.AdamW(trainable, lr=config.trainer.learning_rate)
    model.train()
    loss = model(**batch).loss
    if loss is None or not math.isfinite(float(loss.detach().float().cpu())):
        raise RuntimeError("LoRA smoke produced a non-finite training loss")
    loss.backward()
    gradients = [parameter.grad for parameter in trainable if parameter.grad is not None]
    if not gradients or any(not torch.isfinite(gradient).all() for gradient in gradients):
        raise RuntimeError("LoRA smoke produced missing or non-finite gradients")
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    training_loss = float(loss.detach().float().cpu())

    scratch = REPOSITORY_ROOT / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="peano-lora-smoke-", dir=scratch) as raw:
        root = Path(raw)
        adapter_dir = root / ADAPTER_SUBDIR
        tokenizer_dir = root / TOKENIZER_SUBDIR
        model.save_pretrained(adapter_dir, safe_serialization=True)
        tokenizer.save_pretrained(tokenizer_dir)
        adapter_artifacts = artifact_directory_hash(root, ADAPTER_SUBDIR)
        tokenizer_artifacts = artifact_directory_hash(root, TOKENIZER_SUBDIR)
        require_safetensors_adapter(adapter_artifacts)
        verify_artifact_directory(root, adapter_artifacts, ADAPTER_SUBDIR)
        verify_artifact_directory(root, tokenizer_artifacts, TOKENIZER_SUBDIR)

        del optimizer, model, trainable, gradients, loss
        gc.collect()
        torch.cuda.empty_cache()

        reloaded_tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, use_fast=True)
        if (
            reloaded_tokenizer(examples[0].prompt, add_special_tokens=False)["input_ids"]
            != prompt_ids
        ):
            raise RuntimeError("saved tokenizer changed the repository prompt encoding")
        base = AutoModelForCausalLM.from_pretrained(
            config.model.model_id,
            revision=config.model.revision,
            torch_dtype=torch.bfloat16,
            attn_implementation=config.model.attn_implementation,
            trust_remote_code=False,
            use_safetensors=True,
        )
        reloaded = PeftModel.from_pretrained(base, adapter_dir).to("cuda")
        reloaded.eval()
        with torch.inference_mode():
            reload_loss = reloaded(**batch).loss
        if reload_loss is None or not math.isfinite(
            float(reload_loss.detach().float().cpu())
        ):
            raise RuntimeError("reloaded LoRA adapter produced a non-finite loss")
        reloaded_loss = float(reload_loss.detach().float().cpu())

    report: dict[str, object] = {
        "format": platform_contract.report_format,
        "v": 1,
        "status": "passed",
        "model": {
            "id": config.model.model_id,
            "requested_revision": config.model.revision,
            "model_commit": model_commit,
            "tokenizer_commit": tokenizer_commit,
        },
        "example": {
            "id": examples[0].example_id,
            "sequence_tokens": int(batch["input_ids"].shape[1]),
        },
        "lora": {
            "rank": config.lora.rank,
            "target_modules": list(config.lora.target_modules),
            "trainable_parameters": trainable_parameters,
            "adapter_artifacts": adapter_artifacts,
            "tokenizer_artifacts": tokenizer_artifacts,
        },
        "loss": {"training": training_loss, "reloaded": reloaded_loss},
        "runtime": runtime_identity(torch),
        "job": slurm_job_identity(),
    }
    contract_record = _platform_contract_record(platform_contract)
    if contract_record is not None:
        report["platform_contract"] = contract_record
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expected-machine",
        type=_safe_token,
        default=DEFAULT_PLATFORM_CONTRACT.expected_machine,
    )
    parser.add_argument("--minimum-cuda-capability", type=_parse_cuda_capability)
    parser.add_argument(
        "--report-format",
        type=_safe_token,
        default=DEFAULT_PLATFORM_CONTRACT.report_format,
    )
    args = parser.parse_args(argv)
    contract = SmokePlatformContract(
        expected_machine=args.expected_machine,
        minimum_cuda_capability=args.minimum_cuda_capability,
        report_format=args.report_format,
    )
    report = run_smoke(load_config(args.config), platform_contract=contract)
    if args.output is None:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        if args.output.exists():
            raise FileExistsError(f"refusing to replace smoke report: {args.output}")
        write_manifest(args.output, report)
        print(json.dumps({"report": str(args.output)}, sort_keys=True))
    return 0


__all__ = [
    "DEFAULT_PLATFORM_CONTRACT",
    "SmokePlatformContract",
    "_platform_contract_record",
    "main",
    "run_smoke",
]


if __name__ == "__main__":
    raise SystemExit(main())
