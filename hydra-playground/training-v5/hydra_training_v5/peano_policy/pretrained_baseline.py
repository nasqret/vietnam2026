"""Immutable authority and loader for the model-v3 pretrained-base baseline.

The baseline deliberately does not have an independent prompt or benchmark
configuration.  A *completed* model-v3 adapter artifact is its comparison
authority: that final manifest pins the base-model revision, the closed saved
tokenizer, the complete 247-theorem prompt environment, and the held-out
contract.  The adapter weights are verified as part of that immutable
authority but are never attached to the model loaded here.

This module imports no model framework at import time.  Torch and Transformers
are loaded only after all model-free authority checks have passed.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Mapping

from .adapter_admission import validate_manifest_adapter_admission
from .contract import (
    MODEL_V3_LIBRARY_SIZE,
    attested_training_environment,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v3_environment,
)
from .manifest import (
    ADAPTER_SUBDIR,
    MANIFEST_VERSION,
    TOKENIZER_SUBDIR,
    require_safetensors_adapter,
    sha256_json,
    verify_artifact_directory,
)
from .prompt import PEANO_PROMPT_V3, prompt_contract_sha256
from .training_evidence import validate_completed_training_evidence


BASELINE_FORMAT = "peano-policy-pretrained-base-comparison-authority"
BASELINE_VERSION = 1
BASELINE_POLICY_KIND = "peano-policy-pretrained-base-v1"
EXPECTED_BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
EXPECTED_BASE_MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
EXPECTED_V3_ENVIRONMENT_SHA256 = (
    "72372974368a4a2b66cba42fa48baae47e24bf811a8b2dd030027ea3b7f16363"
)


def _sha256(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _snapshot_hash(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be one pinned lowercase Git snapshot")
    return value


def _artifact_summary(value: object, label: str, root: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"root", "sha256", "files"}:
        raise ValueError(f"{label} artifact identity is malformed")
    if value.get("root") != root:
        raise ValueError(f"{label} artifact identity names the wrong directory")
    files = value.get("files")
    if type(files) is not dict or not files:
        raise ValueError(f"{label} artifact identity has no closed file set")
    return {
        "root": root,
        "sha256": _sha256(value.get("sha256"), f"{label} artifact hash"),
    }


def validate_comparison_manifest(manifest: object) -> object:
    """Return the exact full model-v3 environment or reject the authority.

    A ``training-manifest.json`` is published only after training, evaluation,
    adapter saving, tokenizer saving, and final input/source rechecks.  The
    metrics checks below additionally prevent a zero-step or partial manifest
    from being used as the scientific comparison anchor.
    """

    if type(manifest) is not dict or manifest.get("v") != MANIFEST_VERSION:
        raise ValueError("comparison authority is not a supported training manifest")
    validate_completed_training_evidence(manifest)
    validate_manifest_adapter_admission(manifest)
    environment = attested_training_environment(manifest)
    expected_environment = model_v3_environment()
    if (
        environment != expected_environment
        or environment.prompt_version != PEANO_PROMPT_V3
        or environment.library_prefix_length != MODEL_V3_LIBRARY_SIZE
        or environment.library_full_length != MODEL_V3_LIBRARY_SIZE
        or environment.sha256 != EXPECTED_V3_ENVIRONMENT_SHA256
        or manifest.get("prompt_version") != PEANO_PROMPT_V3
        or manifest.get("prompt_contract_sha256")
        != prompt_contract_sha256(PEANO_PROMPT_V3)
    ):
        raise ValueError(
            "pretrained baseline requires the exact full 247-theorem model-v3 authority"
        )

    inputs = manifest.get("inputs")
    attestation = (
        inputs.get("dataset_attestation") if type(inputs) is dict else None
    )
    if (
        type(attestation) is not dict
        or attestation.get("held_out_contract")
        != held_out_contract_record(PEANO_PROMPT_V3)
        or attestation.get("held_out_contract_sha256")
        != held_out_contract_sha256(PEANO_PROMPT_V3)
        or attestation.get("inference_environment")
        != environment_record(expected_environment)
    ):
        raise ValueError("comparison manifest does not bind the frozen v3 benchmark")

    base = manifest.get("base_model")
    tokenizer = manifest.get("tokenizer")
    adapter = manifest.get("adapter")
    if type(base) is not dict or type(tokenizer) is not dict or type(adapter) is not dict:
        raise ValueError("comparison manifest lacks base, tokenizer, or adapter identity")
    revision = _snapshot_hash(
        base.get("resolved_snapshot_hash"), "resolved base-model revision"
    )
    if (
        base.get("id") != EXPECTED_BASE_MODEL_ID
        or revision != EXPECTED_BASE_MODEL_REVISION
        or base.get("requested_revision") != revision
        or tokenizer.get("resolved_snapshot_hash") != revision
    ):
        raise ValueError("comparison model and tokenizer are not the pinned Qwen snapshot")
    _sha256(base.get("config_sha256"), "base-model configuration hash")
    _sha256(tokenizer.get("identity_sha256"), "tokenizer identity hash")
    _artifact_summary(adapter, "adapter", ADAPTER_SUBDIR)
    _artifact_summary(tokenizer.get("artifacts"), "tokenizer", TOKENIZER_SUBDIR)
    require_safetensors_adapter(adapter)

    runtime = manifest.get("runtime")
    generation = manifest.get("generation")
    if (
        type(runtime) is not dict
        or runtime.get("dtype") != "bfloat16"
        or runtime.get("attention") != "sdpa"
        or type(generation) is not dict
        or type(generation.get("temperature")) not in {int, float}
        or generation.get("temperature") != 1.0
        or type(generation.get("top_p")) not in {int, float}
        or generation.get("top_p") != 1.0
    ):
        raise ValueError("comparison manifest has a different model/decoder runtime")

    metrics = manifest.get("metrics")
    expected_steps = (
        metrics.get("expected_optimizer_steps") if type(metrics) is dict else None
    )
    actual_steps = (
        metrics.get("actual_optimizer_steps") if type(metrics) is dict else None
    )
    if (
        type(expected_steps) is not int
        or expected_steps < 1
        or type(actual_steps) is not int
        or actual_steps != expected_steps
    ):
        raise ValueError(
            "comparison authority is not a completed positive-step model-v3 run"
        )
    return environment


def comparison_authority_record(
    adapter_dir: Path,
    manifest: Mapping[str, object],
    *,
    manifest_sha256: str,
) -> dict[str, object]:
    """Verify the two closed trees and return a compact comparison binding."""

    environment = validate_comparison_manifest(manifest)
    manifest_digest = _sha256(manifest_sha256, "training manifest hash")
    adapter = manifest["adapter"]
    tokenizer = manifest["tokenizer"]
    if type(adapter) is not dict or type(tokenizer) is not dict:
        raise RuntimeError("validated comparison artifact identity was lost")
    tokenizer_artifacts = tokenizer["artifacts"]
    if type(tokenizer_artifacts) is not dict:
        raise RuntimeError("validated tokenizer artifact identity was lost")
    require_safetensors_adapter(adapter)
    verify_artifact_directory(
        adapter_dir,
        adapter,
        ADAPTER_SUBDIR,
        require_protected=True,
    )
    verify_artifact_directory(
        adapter_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=True,
    )
    run = manifest.get("run")
    run_name = run.get("name") if type(run) is dict else None
    if type(run_name) is not str or not run_name:
        raise ValueError("comparison manifest has no stable run name")
    base = manifest["base_model"]
    if type(base) is not dict:
        raise RuntimeError("validated base-model identity was lost")
    runtime = manifest["runtime"]
    if type(runtime) is not dict:
        raise RuntimeError("validated model runtime identity was lost")
    return {
        "format": BASELINE_FORMAT,
        "v": BASELINE_VERSION,
        "training_manifest_sha256": manifest_digest,
        "comparison_run_name": run_name,
        "base_model": {
            "id": base["id"],
            "revision": base["resolved_snapshot_hash"],
            "config_sha256": base["config_sha256"],
        },
        "model_runtime": {
            "dtype": runtime["dtype"],
            "attention": runtime["attention"],
        },
        "adapter": _artifact_summary(adapter, "adapter", ADAPTER_SUBDIR),
        "tokenizer": _artifact_summary(
            tokenizer_artifacts,
            "tokenizer",
            TOKENIZER_SUBDIR,
        ),
        "prompt_version": PEANO_PROMPT_V3,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V3),
        "environment": environment_record(environment),
        "held_out_contract": held_out_contract_record(PEANO_PROMPT_V3),
        "held_out_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
    }


def load_pretrained_base(
    adapter_dir: Path,
    manifest: Mapping[str, object],
    *,
    seed: int,
) -> tuple[Any, Any]:
    """Load only the pinned base weights and the comparison tokenizer.

    The closed adapter directory is verified but never passed to a loader.
    In particular, this function neither imports PEFT nor calls
    ``PeftModel.from_pretrained``.
    """

    if type(seed) is not int:
        raise TypeError("baseline seed must be an integer")
    validate_comparison_manifest(manifest)
    base = manifest["base_model"]
    tokenizer_record = manifest["tokenizer"]
    adapter_record = manifest["adapter"]
    if (
        type(base) is not dict
        or type(tokenizer_record) is not dict
        or type(adapter_record) is not dict
    ):
        raise RuntimeError("validated model artifact identity was lost")
    tokenizer_artifacts = tokenizer_record["artifacts"]
    if type(tokenizer_artifacts) is not dict:
        raise RuntimeError("validated tokenizer artifact identity was lost")
    require_safetensors_adapter(adapter_record)
    # Verifying the unused adapter is intentional: it is part of the immutable
    # comparison authority whose manifest identifies the trained treatment.
    verify_artifact_directory(
        adapter_dir,
        adapter_record,
        ADAPTER_SUBDIR,
        require_protected=True,
    )
    tokenizer_dir = verify_artifact_directory(
        adapter_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=True,
    )

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    set_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        use_fast=True,
        trust_remote_code=False,
    )
    revision = base["resolved_snapshot_hash"]
    tokenizer_identity = {
        "class": type(tokenizer).__name__,
        "commit": revision,
        "special_tokens": tokenizer.special_tokens_map,
        "vocab_size": len(tokenizer),
    }
    if (
        tokenizer.eos_token_id is None
        or tokenizer.pad_token_id is None
        or tokenizer.padding_side != "right"
        or sha256_json(tokenizer_identity) != tokenizer_record["identity_sha256"]
    ):
        raise RuntimeError("closed comparison tokenizer identity did not reproduce")

    model = AutoModelForCausalLM.from_pretrained(
        base["id"],
        revision=revision,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
        trust_remote_code=False,
        use_safetensors=True,
    )
    model_commit = getattr(model.config, "_commit_hash", None) or revision
    if (
        model_commit != revision
        or sha256_json(model.config.to_dict()) != base["config_sha256"]
    ):
        raise RuntimeError("loaded base model differs from the comparison snapshot")
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
    # Direct callers receive a model only if the authority trees still match
    # after the potentially long tokenizer/base load interval.
    verify_artifact_directory(
        adapter_dir,
        adapter_record,
        ADAPTER_SUBDIR,
        require_protected=True,
    )
    verify_artifact_directory(
        adapter_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=True,
    )
    return model, tokenizer


__all__ = [
    "BASELINE_FORMAT",
    "BASELINE_POLICY_KIND",
    "BASELINE_VERSION",
    "EXPECTED_BASE_MODEL_ID",
    "EXPECTED_BASE_MODEL_REVISION",
    "EXPECTED_V3_ENVIRONMENT_SHA256",
    "comparison_authority_record",
    "load_pretrained_base",
    "validate_comparison_manifest",
]
