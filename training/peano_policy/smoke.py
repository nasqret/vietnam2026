#!/usr/bin/env python3
"""One real accelerator forward/backward and LoRA save/reload preflight."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import tempfile
import time
from typing import Any

from .adapter_admission import (
    AdmissionProbePlan,
    BaseReloadContract,
    admit_loaded_policy,
    canonical_peft_adapter_state,
    capture_in_memory_policy,
    select_admission_probes,
)
from .budget import (
    enforce_token_budget,
    tokenize_split,
    tokenizer_identity_record,
)
from .config import ExperimentConfig, load_config
from .corpus_eligibility import verify_sealed_corpus_eligibility
from .curriculum import load_curriculum
from .data import IGNORE_INDEX, load_examples, tokenize_completion
from .manifest import (
    ADAPTER_SUBDIR,
    TOKENIZER_SUBDIR,
    artifact_directory_hash,
    require_safetensors_adapter,
    sha256_json,
    verify_artifact_directory,
    write_manifest,
)
from .objective import (
    CompletionOnlyTrainerMixin,
    completion_objective_record,
    completion_projection,
    indexed_completion_cross_entropy,
    require_indexed_logits_support,
    single_process_trainer_runtime_record,
)
from .runtime import runtime_identity, slurm_job_identity


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9._-]{1,64}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CUSTOM_CLIP_MAX_NORM = 1.0
_TRAINER_BUILTIN_CLIP_MAX_NORM = 0.0
_ADAM_BETAS = (0.9, 0.999)
_ADAM_EPSILON = 1e-8


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


@dataclass(frozen=True, slots=True)
class SmokeExampleSelection:
    """One selected row and every extremal role it witnesses."""

    example: Any
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SmokeAdmissionPlan:
    """Bounded train/validation probes and their auditable selection source."""

    plan: AdmissionProbePlan
    selection: dict[str, object]
    tokenized_evaluation: dict[str, object]


def _parse_cuda_capability(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]{1,2})\.([0-9]{1,2})", value)
    if match is None:
        raise argparse.ArgumentTypeError("expected CUDA capability MAJOR.MINOR")
    return int(match.group(1)), int(match.group(2))


def _safe_token(value: str) -> str:
    if _SAFE_TOKEN_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("expected one safe ASCII token")
    return value


def _record_sha256(
    record: dict[str, object],
    key: str,
    label: str,
) -> str:
    value = record.get(key)
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise RuntimeError(f"{label} has no canonical SHA-256 identity")
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


def _extend_active_prompt_to_length(
    torch: Any,
    batch: dict[str, Any],
    *,
    target_length: int,
    pad_token_id: int,
) -> dict[str, Any]:
    """Insert attended masked tokens before the supervised completion suffix.

    Zero-attention right padding is not a backend-independent memory envelope:
    an unpadding attention implementation may discard it.  These inserted pad
    token ids are instead ordinary attended prompt tokens whose labels remain
    masked.  The completion suffix and its supervised-token count are exactly
    preserved while active sequence length reaches the audited maximum.
    """

    required = {"input_ids", "attention_mask", "labels"}
    if set(batch) != required:
        raise RuntimeError("memory-envelope batch has unexpected tensor fields")
    if type(target_length) is not int or target_length < 2:
        raise RuntimeError("memory-envelope target length is invalid")
    if type(pad_token_id) is not int or pad_token_id < 0:
        raise RuntimeError("memory-envelope tokenizer has no valid pad token")
    tensors = [batch[name] for name in sorted(required)]
    if any(
        not torch.is_tensor(value)
        or value.ndim != 2
        or value.dtype != torch.long
        for value in tensors
    ):
        raise RuntimeError("memory-envelope batch tensors are malformed")
    shapes = {tuple(value.shape) for value in tensors}
    if len(shapes) != 1:
        raise RuntimeError("memory-envelope batch tensor shapes differ")
    rows, current_length = tensors[0].shape
    if rows != 1 or current_length > target_length:
        raise RuntimeError("memory-envelope cannot extend the selected batch")
    if not bool(batch["attention_mask"].eq(1).all().detach().cpu()):
        raise RuntimeError("memory-envelope source row is not fully attended")
    completion_projection(batch["labels"], batch["attention_mask"])
    supervised = batch["labels"][0].ne(IGNORE_INDEX)
    first_supervised = int(
        supervised.nonzero(as_tuple=False)[0].detach().cpu().item()
    )
    inserted = target_length - current_length
    if inserted == 0:
        return dict(batch)
    fill = {
        "input_ids": pad_token_id,
        "attention_mask": 1,
        "labels": IGNORE_INDEX,
    }
    return {
        name: torch.cat(
            (
                value[:, :first_supervised],
                torch.full(
                    (rows, inserted),
                    fill[name],
                    dtype=value.dtype,
                    device=value.device,
                ),
                value[:, first_supervised:],
            ),
            dim=1,
        )
        for name, value in batch.items()
    }


def _add_combined_memory_envelope(
    torch: Any,
    selections: tuple[SmokeExampleSelection, ...],
    natural_batches: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    probe_records: list[dict[str, object]],
    *,
    sequence_maximum: int,
    supervision_maximum: int,
    pad_token_id: int,
) -> dict[str, object]:
    """Exercise the componentwise memory envelope of the selected curriculum.

    Every selected row has sequence and completion lengths bounded by the two
    audited maxima.  If no natural row attains both, extend the longest
    completion's prompt with attended label-masked tokens until it reaches the
    longest sequence.  This valid batch's active attention and indexed-head
    tensor dimensions jointly dominate every row without spending a redundant
    third optimizer step.  The natural batch remains available for tokenizer
    round-trip evidence.
    """

    if type(sequence_maximum) is not int or sequence_maximum < 2:
        raise RuntimeError("curriculum sequence maximum is invalid")
    if type(supervision_maximum) is not int or supervision_maximum < 1:
        raise RuntimeError("curriculum supervision maximum is invalid")
    if not (
        len(selections) == len(natural_batches) == len(batches) == len(probe_records)
    ):
        raise RuntimeError("memory-envelope natural probe populations differ")

    existing = [
        index
        for index, probe in enumerate(probe_records)
        if probe.get("sequence_tokens") == sequence_maximum
        and probe.get("supervised_tokens") == supervision_maximum
    ]
    if existing:
        probe = probe_records[existing[0]]
        roles = probe.get("roles")
        if type(roles) is not list:
            raise RuntimeError("memory-envelope probe roles are malformed")
        roles.append("combined_memory_envelope")
        probe["construction"] = "natural-row"
        return probe

    completion_indices = [
        index
        for index, selection in enumerate(selections)
        if "longest_completion" in selection.roles
    ]
    if len(completion_indices) != 1:
        raise RuntimeError("memory-envelope needs one longest completion row")
    source_index = completion_indices[0]
    source = selections[source_index].example
    envelope = _extend_active_prompt_to_length(
        torch,
        natural_batches[source_index],
        target_length=sequence_maximum,
        pad_token_id=pad_token_id,
    )
    projection = completion_projection(
        envelope["labels"], envelope["attention_mask"]
    )
    supervised_tokens = int(projection.supervised_tokens.detach().cpu())
    projected_positions = int(projection.positions.numel())
    if (
        int(envelope["input_ids"].shape[1]) != sequence_maximum
        or int(envelope["attention_mask"].sum().detach().cpu())
        != sequence_maximum
        or supervised_tokens != supervision_maximum
        or projected_positions != supervision_maximum
    ):
        raise RuntimeError("combined memory-envelope dimensions are not maximal")
    source_length = int(natural_batches[source_index]["input_ids"].shape[1])
    batches[source_index] = envelope
    probe = {
        "id": source.example_id,
        "source_example_id": source.example_id,
        "roles": [*selections[source_index].roles, "combined_memory_envelope"],
        "construction": "attended-masked-prompt-extension-to-longest-sequence",
        "inserted_prompt_tokens": sequence_maximum - source_length,
        "sequence_tokens": sequence_maximum,
        "attended_tokens": sequence_maximum,
        "supervised_tokens": supervised_tokens,
        "projected_positions": projected_positions,
    }
    probe_records[source_index] = probe
    return probe


def _smoke_examples(
    config: ExperimentConfig,
    tokenizer: Any,
) -> tuple[
    tuple[SmokeExampleSelection, ...],
    dict[str, object] | None,
    dict[str, object] | None,
]:
    """Choose the legacy row or both memory-relevant v3 extrema.

    Transformer activation cost is driven primarily by full sequence length,
    while the indexed language-model head is driven by supervised completion
    length.  A sound preflight therefore exercises both extrema, deduplicating
    the common case where one row witnesses both.
    """

    train_path = _repo_path(config.data.train_path)
    curriculum = config.curriculum
    if curriculum is None:
        examples = load_examples(
            train_path,
            max_samples=1,
            seed=config.run.seed,
        )
        if len(examples) != 1:
            raise RuntimeError(
                "training smoke could not select exactly one checked row"
            )
        return (
            (SmokeExampleSelection(examples[0], ("deterministic_single_row",)),),
            None,
            None,
        )

    if config.run.max_train_samples is not None:
        raise RuntimeError("model-v3 curriculum forbids train-row subsampling")
    loaded = load_curriculum(
        train_path,
        seed=str(curriculum.selection_seed),
        synthetic_row_ceiling=curriculum.synthetic_row_ceiling,
    )
    _, token_record = tokenize_split(
        loaded.examples,
        tokenizer,
        role="train",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity_record(
            tokenizer,
            model_id=config.model.model_id,
            revision=config.model.revision,
        ),
        retain_encodings=False,
    )
    enforce_token_budget(
        token_record,
        max_total_tokens=curriculum.max_train_tokens,
        max_sum_squared_tokens=curriculum.max_train_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )
    sequence = token_record.get("sequence")
    supervision = token_record.get("supervision")
    if (
        type(sequence) is not dict
        or type(sequence.get("longest_example_id")) is not str
        or type(supervision) is not dict
        or type(supervision.get("longest_example_id")) is not str
    ):
        raise RuntimeError("token audit did not identify both extremal training rows")

    by_id = {example.example_id: example for example in loaded.examples}
    if len(by_id) != len(loaded.examples):
        raise RuntimeError("selected curriculum repeats an example id")
    roles_by_id: dict[str, list[str]] = {}
    ordered_ids: list[str] = []
    for role, example_id in (
        ("longest_sequence", sequence["longest_example_id"]),
        ("longest_completion", supervision["longest_example_id"]),
    ):
        if example_id not in by_id:
            raise RuntimeError(f"{role} training row is absent")
        if example_id not in roles_by_id:
            roles_by_id[example_id] = []
            ordered_ids.append(example_id)
        roles_by_id[example_id].append(role)
    selections = tuple(
        SmokeExampleSelection(by_id[example_id], tuple(roles_by_id[example_id]))
        for example_id in ordered_ids
    )
    return selections, loaded.attestation, token_record


def _smoke_admission_plan(
    config: ExperimentConfig,
    tokenizer: Any,
    selections: tuple[SmokeExampleSelection, ...],
    *,
    corpus_eligibility: dict[str, object],
    curriculum_attestation: dict[str, object],
    tokenized_train: dict[str, object],
) -> SmokeAdmissionPlan:
    """Select two or three natural admitted rows without retaining all tokens.

    The existing natural training extrema are already deterministic outputs of
    the reviewed curriculum.  Add the lexicographically first example from the
    exact capped validation population, then let the shared stratified selector
    canonically order those two or three candidates.  Only these bounded rows
    retain token arrays; the complete validation split is still token-audited
    with ``retain_encodings=False`` before any model is loaded.
    """

    curriculum = config.curriculum
    if curriculum is None:
        raise RuntimeError("legacy smoke has no model-v3 adapter-admission plan")
    if not 1 <= len(selections) <= 2:
        raise RuntimeError("adapter admission needs one or two training extrema")
    train_examples = tuple(selection.example for selection in selections)
    if len({example.example_id for example in train_examples}) != len(train_examples):
        raise RuntimeError("adapter-admission training extrema are not unique")

    evaluation = tuple(
        load_examples(
            _repo_path(config.data.eval_path),
            max_samples=config.run.max_eval_samples,
            seed=config.run.seed + 1,
        )
    )
    if not evaluation:
        raise RuntimeError("adapter admission needs a non-empty validation split")
    tokenizer_identity = tokenizer_identity_record(
        tokenizer,
        model_id=config.model.model_id,
        revision=config.model.revision,
    )
    _, evaluation_record = tokenize_split(
        evaluation,
        tokenizer,
        role="eval",
        max_length=config.data.max_length,
        tokenizer_identity=tokenizer_identity,
        retain_encodings=False,
    )
    enforce_token_budget(
        evaluation_record,
        max_total_tokens=curriculum.max_eval_tokens,
        max_sum_squared_tokens=curriculum.max_eval_squared_tokens,
        max_supervised_tokens=config.generation.max_new_tokens,
    )

    validation_example = min(evaluation, key=lambda example: example.example_id)
    train_features = tuple(
        tokenize_completion(example, tokenizer, max_length=config.data.max_length)
        for example in train_examples
    )
    validation_feature = tokenize_completion(
        validation_example,
        tokenizer,
        max_length=config.data.max_length,
    )
    binding_core: dict[str, object] = {
        "format": "peano-policy-smoke-admission-selection",
        "v": 1,
        "sealed_corpus_eligibility_sha256": _record_sha256(
            corpus_eligibility,
            "eligibility_sha256",
            "sealed corpus eligibility",
        ),
        "curriculum_sha256": _record_sha256(
            curriculum_attestation,
            "curriculum_sha256",
            "curriculum attestation",
        ),
        "tokenized_train_sha256": _record_sha256(
            tokenized_train,
            "record_sha256",
            "tokenized training split",
        ),
        "tokenized_evaluation_sha256": _record_sha256(
            evaluation_record,
            "record_sha256",
            "tokenized evaluation split",
        ),
        "train_candidate_policy": "natural-memory-extrema-v1",
        "train_candidate_ids": [example.example_id for example in train_examples],
        "validation_candidate_policy": "lexicographically-first-example-id-v1",
        "validation_candidate_id": validation_example.example_id,
    }
    binding = {
        **binding_core,
        "selection_binding_sha256": sha256_json(binding_core),
    }
    plan = select_admission_probes(
        admitted_train_examples=train_examples,
        admitted_train_features=train_features,
        admitted_evaluation_examples=(validation_example,),
        admitted_evaluation_features=(validation_feature,),
        max_length=config.data.max_length,
        selection_binding_sha256=binding["selection_binding_sha256"],
        count=len(train_examples) + 1,
    )
    return SmokeAdmissionPlan(plan, binding, evaluation_record)


def _verified_corpus_record(config: ExperimentConfig) -> dict[str, object] | None:
    curriculum = config.curriculum
    if curriculum is None:
        return None
    eligibility = verify_sealed_corpus_eligibility(
        _repo_path(curriculum.corpus_seal_path),
        configured_train_path=_repo_path(config.data.train_path),
        configured_eval_path=_repo_path(config.data.eval_path),
        historical_source_commit=curriculum.corpus_source_commit,
        historical_prepare_job_id=curriculum.corpus_prepare_job_id,
        sealed_content_sha256=curriculum.corpus_content_sha256,
    )
    return eligibility.record


def _require_source_evidence_agrees(
    eligibility: object,
    curriculum: object,
    token_record: object,
) -> None:
    """Close the eligibility/load TOCTOU gap before any model is loaded."""

    if type(eligibility) is not dict or type(curriculum) is not dict:
        raise RuntimeError("curriculum smoke source evidence is malformed")
    if type(token_record) is not dict:
        raise RuntimeError("curriculum smoke token evidence is malformed")
    inputs = eligibility.get("inputs")
    source = curriculum.get("source")
    selected = curriculum.get("selected")
    if type(inputs) is not dict or type(source) is not dict or type(selected) is not dict:
        raise RuntimeError("curriculum smoke source evidence is incomplete")
    for eligibility_name, curriculum_name in (
        ("train", "train"),
        ("manifest", "manifest"),
    ):
        eligible = inputs.get(eligibility_name)
        loaded = source.get(curriculum_name)
        if type(eligible) is not dict or type(loaded) is not dict:
            raise RuntimeError("curriculum smoke source identity is malformed")
        fields = ("bytes", "sha256") + (
            ("rows",) if eligibility_name == "train" else ()
        )
        if any(eligible.get(field) != loaded.get(field) for field in fields):
            raise RuntimeError(
                f"loaded curriculum {curriculum_name} differs from sealed eligibility"
            )
    if (
        type(selected.get("rows")) is not int
        or selected.get("rows") != token_record.get("rows")
    ):
        raise RuntimeError("tokenized curriculum row count differs from its selection")


def _indexed_loss(model: Any, batch: dict[str, Any]) -> tuple[Any, Any, Any]:
    projection = completion_projection(batch["labels"], batch["attention_mask"])
    outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        logits_to_keep=projection.positions,
    )
    loss = indexed_completion_cross_entropy(outputs.logits, projection)
    return loss, outputs, projection


def _trainer_schedule(config: ExperimentConfig, *, train_rows: int) -> dict[str, int]:
    """Reproduce Transformers 4.53.3's finite-dataloader step arithmetic."""

    if type(train_rows) is not int or train_rows < 1:
        raise RuntimeError("training schedule needs a positive curriculum row count")
    batches = math.ceil(train_rows / config.trainer.per_device_train_batch_size)
    updates_per_epoch = max(
        math.ceil(batches / config.trainer.gradient_accumulation_steps),
        1,
    )
    total_steps = (
        config.trainer.max_steps
        if config.trainer.max_steps > 0
        else math.ceil(config.trainer.epochs * updates_per_epoch)
    )
    warmup_steps = math.ceil(total_steps * config.trainer.warmup_ratio)
    if total_steps < 1 or warmup_steps >= total_steps:
        raise RuntimeError("training schedule has no post-warmup optimizer step")
    return {
        "train_rows": train_rows,
        "dataloader_batches": batches,
        "updates_per_epoch": updates_per_epoch,
        "total_steps": total_steps,
        "warmup_steps": warmup_steps,
    }


def _require_and_clip_gradients(
    torch: Any,
    named_parameters: list[tuple[str, Any]],
    *,
    max_norm: float = _CUSTOM_CLIP_MAX_NORM,
) -> dict[str, object]:
    """Require every trainable parameter's finite gradient, then clip as Trainer."""

    _require_finite_gradients(torch, named_parameters)
    parameters = [parameter for _, parameter in named_parameters]
    try:
        norm = torch.nn.utils.clip_grad_norm_(
            parameters,
            max_norm=max_norm,
            error_if_nonfinite=True,
        )
    except RuntimeError as exc:
        raise RuntimeError("LoRA smoke produced a non-finite gradient") from exc
    norm_value = float(norm.detach().float().cpu())
    if not math.isfinite(norm_value):
        raise RuntimeError("LoRA smoke produced a non-finite gradient norm")
    return {
        "parameters_with_grad": len(parameters),
        "norm_before_clip": norm_value,
        "max_norm": max_norm,
        "clipped": norm_value > max_norm,
    }


def _require_finite_gradients(
    torch: Any,
    named_parameters: list[tuple[str, Any]],
) -> dict[str, object]:
    """Fail closed unless every named trainable tensor has a finite gradient."""

    if not named_parameters:
        raise RuntimeError("LoRA smoke has no trainable parameter population")
    missing = [name for name, parameter in named_parameters if parameter.grad is None]
    if missing:
        preview = ", ".join(missing[:5])
        raise RuntimeError(
            f"LoRA smoke produced no gradient for {len(missing)} trainable "
            f"parameters: {preview}"
        )
    nonfinite = [
        name
        for name, parameter in named_parameters
        if not bool(torch.isfinite(parameter.grad).all().detach().cpu())
    ]
    if nonfinite:
        preview = ", ".join(nonfinite[:5])
        raise RuntimeError(
            f"LoRA smoke produced a non-finite gradient for {len(nonfinite)} "
            f"trainable parameters: {preview}"
        )
    names = sorted(name for name, _ in named_parameters)
    return {
        "parameters_with_finite_grad": len(named_parameters),
        "parameter_names_sha256": hashlib.sha256(
            json.dumps(names, separators=(",", ":"), ensure_ascii=True).encode(
                "ascii"
            )
        ).hexdigest(),
    }


def _strict_pre_optimizer_clip_evidence(
    torch: Any,
    named_parameters: list[tuple[str, Any]],
) -> dict[str, object]:
    """Audit raw gradients, clip strictly, then audit the clipped population."""

    raw = _require_finite_gradients(torch, named_parameters)
    clip = _require_and_clip_gradients(
        torch,
        named_parameters,
        max_norm=_CUSTOM_CLIP_MAX_NORM,
    )
    postclip = _require_finite_gradients(torch, named_parameters)
    if raw != postclip:
        raise RuntimeError("LoRA gradient population changed during clipping")
    return {
        "hook": "on_pre_optimizer_step",
        "raw": raw,
        "custom_pre_optimizer_clip": {
            "max_norm": clip["max_norm"],
            "error_if_nonfinite": True,
            "norm_before_clip": clip["norm_before_clip"],
            "clipped": clip["clipped"],
            "postclip": postclip,
        },
    }


def _parameter_snapshot(
    named_parameters: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Copy trainable tensors to CPU outside the measured CUDA interval."""

    return {
        name: parameter.detach().cpu().clone()
        for name, parameter in named_parameters
    }


def _changed_parameter_names(
    torch: Any,
    before: dict[str, Any],
    named_parameters: list[tuple[str, Any]],
) -> list[str]:
    """Return adapter tensors changed by the representative optimizer steps."""

    if set(before) != {name for name, _ in named_parameters}:
        raise RuntimeError("trainable parameter population changed during smoke")
    changed = [
        name
        for name, parameter in named_parameters
        if not torch.equal(before[name], parameter.detach().cpu())
    ]
    if not changed:
        raise RuntimeError("LoRA optimizer smoke did not change any adapter parameter")
    return changed


def _tensor_fingerprint(torch: Any, tensor: Any) -> dict[str, object]:
    """Hash every raw projected-logit byte for semantic reload comparison."""

    value = tensor.detach().contiguous().view(torch.uint8).cpu()
    header = json.dumps(
        {"dtype": str(tensor.dtype), "shape": list(tensor.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\n")
    digest.update(value.numpy())
    return {
        "dtype": str(tensor.dtype),
        "shape": list(tensor.shape),
        "sha256": digest.hexdigest(),
    }


def _advance_scheduler_to_peak(
    optimizer: Any,
    scheduler: Any,
    *,
    warmup_steps: int,
    expected_learning_rate: float,
) -> tuple[list[float], list[float]]:
    """Exercise real warmup transitions without changing adapter parameters."""

    initial_lrs = [float(group["lr"]) for group in optimizer.param_groups]
    optimizer.zero_grad(set_to_none=True)
    for _ in range(warmup_steps):
        optimizer.step()
        scheduler.step()
    peak_lrs = [float(group["lr"]) for group in optimizer.param_groups]
    if any(
        not math.isclose(
            value,
            expected_learning_rate,
            rel_tol=1e-12,
            abs_tol=0.0,
        )
        for value in peak_lrs
    ):
        raise RuntimeError("cosine scheduler did not reach the configured peak LR")
    return initial_lrs, peak_lrs


def _require_exact_reload(
    reference: object,
    *,
    loss: float,
    projected_logits: dict[str, object],
) -> None:
    """Fail closed unless a reloaded adapter is semantically byte-identical."""

    if type(reference) is not dict:
        raise RuntimeError("smoke lost its pre-save semantic reference")
    if projected_logits != reference.get("projected_logits"):
        raise RuntimeError("reloaded adapter changed projected logits after save")
    if loss != reference.get("loss"):
        raise RuntimeError("reloaded adapter changed loss after save")


def _trainer_probe_feature(torch: Any, batch: dict[str, Any]) -> dict[str, list[int]]:
    """Copy one already-validated device batch into Trainer dataset form."""

    if set(batch) != {"input_ids", "attention_mask", "labels"}:
        raise RuntimeError("Trainer integration batch has unexpected tensor fields")
    feature: dict[str, list[int]] = {}
    shapes: set[tuple[int, ...]] = set()
    for name in ("input_ids", "attention_mask", "labels"):
        value = batch[name]
        if (
            not torch.is_tensor(value)
            or value.dtype != torch.long
            or value.ndim != 2
            or value.shape[0] != 1
        ):
            raise RuntimeError("Trainer integration batch tensors are malformed")
        shapes.add(tuple(value.shape))
        feature[name] = value.detach().cpu().tolist()[0]
    if len(shapes) != 1:
        raise RuntimeError("Trainer integration batch tensor shapes differ")
    return feature


def _trainer_probe_arguments(config: ExperimentConfig, output_dir: Path) -> dict[str, object]:
    """Return the bounded one-step subset of production TrainingArguments.

    The manual smoke already checks the full configured scheduler and gradient
    accumulation arithmetic.  This probe is deliberately one microbatch and
    one non-warmup optimizer step: its purpose is to exercise Trainer's actual
    data, objective, backward, clipping, fused-AdamW, and evaluation lifecycle
    without multiplying the 32k-token memory envelope by the production
    accumulation count.
    """

    return {
        "output_dir": str(output_dir),
        "overwrite_output_dir": False,
        "do_train": True,
        "do_eval": True,
        "num_train_epochs": 1.0,
        "max_steps": 1,
        "per_device_train_batch_size": 1,
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": 1,
        "learning_rate": config.trainer.learning_rate,
        "weight_decay": config.trainer.weight_decay,
        "warmup_ratio": 0.0,
        "warmup_steps": 0,
        "lr_scheduler_type": "cosine",
        "optim": "adamw_torch_fused",
        "adam_beta1": _ADAM_BETAS[0],
        "adam_beta2": _ADAM_BETAS[1],
        "adam_epsilon": _ADAM_EPSILON,
        "bf16": True,
        # Keep PEFT's FP32 adapter population unchanged across the explicit
        # evaluation pass.  Transformers' full-eval flag casts the live model.
        "bf16_full_eval": False,
        "tf32": True,
        "gradient_checkpointing": config.trainer.gradient_checkpointing,
        "gradient_checkpointing_kwargs": {"use_reentrant": False},
        # Trainer clips before on_pre_optimizer_step and hard-codes
        # error_if_nonfinite=False.  Disable that path; our callback below
        # performs the strict, auditable clip at the same optimizer boundary.
        "max_grad_norm": _TRAINER_BUILTIN_CLIP_MAX_NORM,
        "logging_strategy": "no",
        "logging_nan_inf_filter": False,
        "eval_strategy": "no",
        "save_strategy": "no",
        "report_to": [],
        "seed": config.run.seed,
        "data_seed": config.run.seed,
        "dataloader_num_workers": 0,
        "remove_unused_columns": False,
        "prediction_loss_only": True,
        "label_names": ["labels"],
        "average_tokens_across_devices": True,
        "disable_tqdm": True,
    }


def _finite_trainer_metric(value: object, label: str) -> float:
    """Normalize one Trainer metric without permitting booleans or NaNs."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"Trainer integration {label} is not numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"Trainer integration {label} is non-finite")
    return result


def _trainer_integration_probe(
    config: ExperimentConfig,
    model: Any,
    batch: dict[str, Any],
    envelope_probe: dict[str, object],
    named_trainable: list[tuple[str, Any]],
    *,
    pad_token_id: int,
    torch: Any,
    Trainer: Any,
    TrainerCallback: Any,
    TrainingArguments: Any,
) -> dict[str, object]:
    """Run one real CompletionOnlyTrainer step and one explicit evaluation.

    Callers must release the manual optimizer and scheduler first.  This helper
    owns the only optimizer state that exists during its lifetime.
    """

    # Import lazily to use the exact collator exercised by the training runner
    # without making lightweight smoke-module imports depend on train.py.
    from .train import _CompletionCollator

    if type(pad_token_id) is not int or pad_token_id < 0:
        raise RuntimeError("Trainer integration tokenizer has no valid pad token")
    feature = _trainer_probe_feature(torch, batch)
    projection = completion_projection(batch["labels"], batch["attention_mask"])
    sequence_tokens = int(batch["input_ids"].shape[1])
    attended_tokens = int(batch["attention_mask"].sum().detach().cpu())
    supervised_tokens = int(projection.supervised_tokens.detach().cpu())
    projected_positions = int(projection.positions.numel())
    probe_id = envelope_probe.get("id")
    construction = envelope_probe.get("construction")
    if (
        type(probe_id) is not str
        or not probe_id
        or construction
        not in {
            "natural-row",
            "attended-masked-prompt-extension-to-longest-sequence",
        }
        or "combined_memory_envelope" not in envelope_probe.get("roles", [])
        or envelope_probe.get("sequence_tokens") != sequence_tokens
        or envelope_probe.get("attended_tokens") != attended_tokens
        or envelope_probe.get("supervised_tokens") != supervised_tokens
        or envelope_probe.get("projected_positions") != projected_positions
        or attended_tokens != sequence_tokens
        or supervised_tokens != projected_positions
    ):
        raise RuntimeError("Trainer integration batch is not the memory envelope")

    gradient_events: list[dict[str, object]] = []

    class GradientAuditCallback(TrainerCallback):
        """Own strict clipping at Trainer's pre-optimizer gradient boundary."""

        def on_pre_optimizer_step(
            self,
            args: Any,
            state: Any,
            control: Any,
            **kwargs: Any,
        ) -> Any:
            gradient_events.append(
                _strict_pre_optimizer_clip_evidence(torch, named_trainable)
            )
            return control

    class CompletionOnlyTrainer(CompletionOnlyTrainerMixin, Trainer):
        """The same indexed completion Trainer composition used in train.py."""

    before = _parameter_snapshot(named_trainable)
    scratch = REPOSITORY_ROOT / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="peano-trainer-integration-", dir=scratch
    ) as raw:
        arguments = TrainingArguments(
            **_trainer_probe_arguments(config, Path(raw))
        )
        trainer = CompletionOnlyTrainer(
            model=model,
            args=arguments,
            train_dataset=[feature],
            eval_dataset=[feature],
            data_collator=_CompletionCollator(torch, pad_token_id),
            callbacks=[GradientAuditCallback()],
        )
        trainer_runtime = single_process_trainer_runtime_record(
            trainer,
            expected_gradient_accumulation_steps=1,
        )

        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        train_started = time.perf_counter()
        train_result = trainer.train()
        torch.cuda.synchronize()
        train_seconds = time.perf_counter() - train_started
        train_peak_allocated = int(torch.cuda.max_memory_allocated())
        train_peak_reserved = int(torch.cuda.max_memory_reserved())

        global_step = getattr(train_result, "global_step", None)
        state_step = getattr(getattr(trainer, "state", None), "global_step", None)
        if global_step != 1 or state_step != 1:
            raise RuntimeError(
                "Trainer integration did not perform exactly one optimizer step"
            )
        if len(gradient_events) != 1:
            raise RuntimeError(
                "Trainer integration did not expose exactly one pre-optimizer gradient event"
            )
        training_loss = _finite_trainer_metric(
            getattr(train_result, "training_loss", None), "training loss"
        )
        changed_names = _changed_parameter_names(torch, before, named_trainable)

        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        eval_started = time.perf_counter()
        eval_metrics = trainer.evaluate()
        torch.cuda.synchronize()
        eval_seconds = time.perf_counter() - eval_started
        eval_peak_allocated = int(torch.cuda.max_memory_allocated())
        eval_peak_reserved = int(torch.cuda.max_memory_reserved())
        if type(eval_metrics) is not dict:
            raise RuntimeError("Trainer integration evaluation returned no metrics")
        evaluation_loss = _finite_trainer_metric(
            eval_metrics.get("eval_loss"), "evaluation loss"
        )

        del trainer, arguments, train_result, eval_metrics

    del before
    gc.collect()
    torch.cuda.empty_cache()
    return {
        "format": "peano-completion-only-trainer-integration",
        "v": 1,
        "trainer": "CompletionOnlyTrainerMixin+transformers.Trainer",
        "train_global_step": 1,
        "training_loss": training_loss,
        "evaluation_loss": evaluation_loss,
        "batch": {
            "role": "componentwise-maximal-memory-envelope",
            "probe_id": probe_id,
            "construction": construction,
            "sequence_tokens": sequence_tokens,
            "attended_tokens": attended_tokens,
            "supervised_tokens": supervised_tokens,
            "projected_positions": projected_positions,
        },
        "arguments": {
            "max_steps": 1,
            "per_device_train_batch_size": 1,
            "per_device_eval_batch_size": 1,
            "gradient_accumulation_steps": 1,
            "learning_rate": config.trainer.learning_rate,
            "weight_decay": config.trainer.weight_decay,
            "bf16": True,
            "tf32": True,
            "gradient_checkpointing": config.trainer.gradient_checkpointing,
            "gradient_checkpointing_kwargs": {"use_reentrant": False},
            "warmup_steps": 0,
            "optimizer": "adamw_torch_fused",
            "adam_beta1": _ADAM_BETAS[0],
            "adam_beta2": _ADAM_BETAS[1],
            "adam_epsilon": _ADAM_EPSILON,
            "trainer_builtin_clip": "disabled",
            "trainer_builtin_max_grad_norm": _TRAINER_BUILTIN_CLIP_MAX_NORM,
            "custom_pre_optimizer_clip": _CUSTOM_CLIP_MAX_NORM,
            "custom_pre_optimizer_error_if_nonfinite": True,
            "average_tokens_across_devices": True,
            "logging_nan_inf_filter": False,
            "save_strategy": "no",
            "eval_strategy": "no",
        },
        "gradients": gradient_events[0],
        "runtime": trainer_runtime,
        "adapter_update": {
            "changed_parameter_tensors": len(changed_names),
            "changed_parameter_names_sha256": hashlib.sha256(
                json.dumps(
                    sorted(changed_names), separators=(",", ":"), ensure_ascii=True
                ).encode("ascii")
            ).hexdigest(),
        },
        "train_runtime": {
            "seconds": round(train_seconds, 6),
            "peak_cuda_allocated_bytes": train_peak_allocated,
            "peak_cuda_reserved_bytes": train_peak_reserved,
        },
        "evaluation_runtime": {
            "seconds": round(eval_seconds, 6),
            "peak_cuda_allocated_bytes": eval_peak_allocated,
            "peak_cuda_reserved_bytes": eval_peak_reserved,
        },
    }


def _save_smoke_artifacts(
    model: Any,
    tokenizer: Any,
    root: Path,
    *,
    require_protected: bool = False,
) -> tuple[Path, Path, dict[str, object], dict[str, object]]:
    """Save and close-hash the exact loader-visible adapter/tokenizer trees."""

    adapter_dir = root / ADAPTER_SUBDIR
    tokenizer_dir = root / TOKENIZER_SUBDIR
    model.save_pretrained(adapter_dir, safe_serialization=True)
    tokenizer.save_pretrained(tokenizer_dir)
    if require_protected:
        for directory in (adapter_dir, tokenizer_dir):
            for current, child_directories, files in os.walk(
                directory,
                topdown=False,
                followlinks=False,
            ):
                current_path = Path(current)
                for name in files:
                    os.chmod(
                        current_path / name,
                        0o444,
                        follow_symlinks=False,
                    )
                for name in child_directories:
                    os.chmod(
                        current_path / name,
                        0o555,
                        follow_symlinks=False,
                    )
                os.chmod(current_path, 0o555, follow_symlinks=False)
    adapter_artifacts = artifact_directory_hash(
        root,
        ADAPTER_SUBDIR,
        require_protected=require_protected,
    )
    tokenizer_artifacts = artifact_directory_hash(
        root,
        TOKENIZER_SUBDIR,
        require_protected=require_protected,
    )
    require_safetensors_adapter(adapter_artifacts)
    verify_artifact_directory(
        root,
        adapter_artifacts,
        ADAPTER_SUBDIR,
        require_protected=require_protected,
    )
    verify_artifact_directory(
        root,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=require_protected,
    )
    return adapter_dir, tokenizer_dir, adapter_artifacts, tokenizer_artifacts


def _read_adapter_safetensors(
    adapter_dir: Path,
    *,
    safe_open: Any,
) -> dict[str, Any]:
    """Read every actual persisted adapter tensor through safetensors only."""

    path = adapter_dir / "adapter_model.safetensors"
    try:
        with safe_open(str(path), framework="pt", device="cpu") as handle:
            names = tuple(sorted(handle.keys()))
            if not names:
                raise RuntimeError("saved smoke adapter safetensors is empty")
            return {
                name: handle.get_tensor(name).detach().clone()
                for name in names
            }
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"cannot read saved smoke adapter safetensors: {exc}"
        ) from exc


def _load_base_model(
    config: ExperimentConfig,
    torch: Any,
    AutoModelForCausalLM: Any,
    *,
    indexed_logits: bool,
    local_files_only: bool = False,
) -> Any:
    """Load every initial/reload branch under one pinned safe contract."""

    model = AutoModelForCausalLM.from_pretrained(
        config.model.model_id,
        revision=config.model.revision,
        torch_dtype=torch.bfloat16,
        attn_implementation=config.model.attn_implementation,
        trust_remote_code=False,
        use_safetensors=True,
        local_files_only=local_files_only,
    )
    if indexed_logits:
        require_indexed_logits_support(model)
    return model


def _load_lora_model(
    config: ExperimentConfig,
    torch: Any,
    AutoModelForCausalLM: Any,
    PeftLoraConfig: Any,
    get_peft_model: Any,
    *,
    curriculum_v2: bool,
) -> tuple[Any, str, str]:
    """Load the pinned base and install the exact configured LoRA adapter."""

    model = _load_base_model(
        config,
        torch,
        AutoModelForCausalLM,
        indexed_logits=curriculum_v2,
    )
    model_commit = _resolved_commit(
        getattr(model.config, "_commit_hash", None),
        config.model.revision,
        "model",
    )
    if not callable(getattr(model.config, "to_dict", None)):
        raise RuntimeError("base model has no canonical configuration")
    # This is the pristine pinned base configuration.  Capture it before the
    # runtime-only cache mutation so a fresh loader can be checked exactly.
    base_config_sha256 = sha256_json(model.config.to_dict())
    model.config.use_cache = False
    if curriculum_v2 and config.trainer.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
        if not getattr(model, "is_gradient_checkpointing", False):
            raise RuntimeError("model did not enable gradient checkpointing")
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
    return model, model_commit, base_config_sha256


def _legacy_model_smoke(
    config: ExperimentConfig,
    tokenizer: Any,
    selection: SmokeExampleSelection,
    torch: Any,
    AutoModelForCausalLM: Any,
    AutoTokenizer: Any,
    PeftLoraConfig: Any,
    PeftModel: Any,
    get_peft_model: Any,
) -> dict[str, object]:
    """Retain the historical v1 one-row behavior and evidence shape."""

    example = selection.example
    prompt_ids = tokenizer(example.prompt, add_special_tokens=False)["input_ids"]
    model, model_commit, _ = _load_lora_model(
        config,
        torch,
        AutoModelForCausalLM,
        PeftLoraConfig,
        get_peft_model,
        curriculum_v2=False,
    )
    batch = _one_batch(example, tokenizer, torch, config.data.max_length)
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
        adapter_dir, tokenizer_dir, adapter_artifacts, tokenizer_artifacts = (
            _save_smoke_artifacts(model, tokenizer, root)
        )
        del optimizer, model, trainable, gradients, loss
        gc.collect()
        torch.cuda.empty_cache()

        reloaded_tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_dir, use_fast=True
        )
        if (
            reloaded_tokenizer(example.prompt, add_special_tokens=False)["input_ids"]
            != prompt_ids
        ):
            raise RuntimeError("saved tokenizer changed the repository prompt encoding")
        base = _load_base_model(
            config,
            torch,
            AutoModelForCausalLM,
            indexed_logits=False,
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

    return {
        "model_commit": model_commit,
        "example": example,
        "batch": batch,
        "trainable_parameters": trainable_parameters,
        "adapter_artifacts": adapter_artifacts,
        "tokenizer_artifacts": tokenizer_artifacts,
        "training_loss": training_loss,
        "reloaded_loss": reloaded_loss,
    }


def _curriculum_model_smoke(
    config: ExperimentConfig,
    tokenizer: Any,
    selections: tuple[SmokeExampleSelection, ...],
    token_record: dict[str, object],
    admission_plan: AdmissionProbePlan,
    torch: Any,
    AutoModelForCausalLM: Any,
    AutoTokenizer: Any,
    PeftLoraConfig: Any,
    PeftModel: Any,
    get_peft_model: Any,
    get_peft_model_state_dict: Any,
    safe_open: Any,
    Trainer: Any,
    TrainerCallback: Any,
    TrainingArguments: Any,
    get_scheduler: Any,
) -> dict[str, object]:
    """Run fail-closed v2 probes for both indexed-objective extrema."""

    if not selections:
        raise RuntimeError("curriculum smoke selected no extremal rows")
    sequence = token_record.get("sequence")
    supervision = token_record.get("supervision")
    if type(sequence) is not dict or type(supervision) is not dict:
        raise RuntimeError("curriculum token evidence lacks extrema")

    model, model_commit, base_config_sha256 = _load_lora_model(
        config,
        torch,
        AutoModelForCausalLM,
        PeftLoraConfig,
        get_peft_model,
        curriculum_v2=True,
    )
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    natural_batches: list[dict[str, Any]] = []
    probe_records: list[dict[str, object]] = []
    for selection in selections:
        batch = _one_batch(
            selection.example, tokenizer, torch, config.data.max_length
        )
        projection = completion_projection(batch["labels"], batch["attention_mask"])
        sequence_tokens = int(batch["input_ids"].shape[1])
        attended_tokens = int(batch["attention_mask"].sum().detach().cpu())
        supervised_tokens = int(projection.supervised_tokens.detach().cpu())
        projected_positions = int(projection.positions.numel())
        if (
            "longest_sequence" in selection.roles
            and sequence_tokens != sequence.get("maximum")
        ):
            raise RuntimeError("sequence smoke row is not the attested longest row")
        if (
            "longest_completion" in selection.roles
            and supervised_tokens != supervision.get("maximum")
        ):
            raise RuntimeError(
                "completion smoke row is not the attested longest completion"
            )
        if projected_positions != supervised_tokens:
            raise RuntimeError("single-row indexed projection lost supervision")
        if attended_tokens != sequence_tokens:
            raise RuntimeError("natural smoke row is not fully attended")
        natural_batches.append(batch)
        probe_records.append(
            {
                "id": selection.example.example_id,
                "roles": list(selection.roles),
                "sequence_tokens": sequence_tokens,
                "attended_tokens": attended_tokens,
                "supervised_tokens": supervised_tokens,
                "projected_positions": projected_positions,
            }
        )
    batches = list(natural_batches)
    memory_envelope = _add_combined_memory_envelope(
        torch,
        selections,
        natural_batches,
        batches,
        probe_records,
        sequence_maximum=sequence.get("maximum"),
        supervision_maximum=supervision.get("maximum"),
        pad_token_id=tokenizer.pad_token_id,
    )

    named_trainable = [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]
    if not named_trainable:
        raise RuntimeError("LoRA smoke produced no trainable parameters")
    trainable_parameters = sum(
        parameter.numel() for _, parameter in named_trainable
    )
    trainer_shell = Trainer.__new__(Trainer)
    decay_names = set(trainer_shell.get_decay_parameter_names(model))
    decay_parameters = [
        parameter
        for name, parameter in named_trainable
        if name in decay_names
    ]
    no_decay_parameters = [
        parameter
        for name, parameter in named_trainable
        if name not in decay_names
    ]
    decay_parameter_tensors = len(decay_parameters)
    no_decay_parameter_tensors = len(no_decay_parameters)
    optimizer = torch.optim.AdamW(
        [
            {
                "params": decay_parameters,
                "weight_decay": config.trainer.weight_decay,
            },
            {"params": no_decay_parameters, "weight_decay": 0.0},
        ],
        lr=config.trainer.learning_rate,
        betas=_ADAM_BETAS,
        eps=_ADAM_EPSILON,
        fused=True,
    )
    schedule = _trainer_schedule(config, train_rows=int(token_record["rows"]))
    if schedule["warmup_steps"] + len(batches) > schedule["total_steps"]:
        raise RuntimeError("training schedule is too short for all smoke probes")
    scheduler = get_scheduler(
        "cosine",
        optimizer=optimizer,
        num_warmup_steps=schedule["warmup_steps"],
        num_training_steps=schedule["total_steps"],
    )
    # Position the costly probes at the first nonzero peak-LR steps.  The
    # no-gradient optimizer calls exercise the exact scheduler API while the
    # parameter snapshot below proves the subsequent real steps change LoRA.
    initial_lrs, peak_lrs = _advance_scheduler_to_peak(
        optimizer,
        scheduler,
        warmup_steps=schedule["warmup_steps"],
        expected_learning_rate=config.trainer.learning_rate,
    )

    before = _parameter_snapshot(named_trainable)
    step_seconds = 0.0
    peak_allocated = 0
    peak_reserved = 0
    for batch, probe in zip(batches, probe_records, strict=True):
        model.train()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.perf_counter()
        learning_rate = float(optimizer.param_groups[0]["lr"])
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            loss, outputs, projection = _indexed_loss(model, batch)
        loss_value = float(loss.detach().float().cpu())
        if not math.isfinite(loss_value):
            raise RuntimeError("LoRA smoke produced a non-finite training loss")
        loss.backward()
        gradient_record = _require_and_clip_gradients(torch, named_trainable)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        seconds = time.perf_counter() - started
        allocated = int(torch.cuda.max_memory_allocated())
        reserved = int(torch.cuda.max_memory_reserved())
        step_seconds += seconds
        peak_allocated = max(peak_allocated, allocated)
        peak_reserved = max(peak_reserved, reserved)
        probe["training"] = {
            "loss": loss_value,
            "learning_rate": learning_rate,
            "seconds": round(seconds, 6),
            "peak_cuda_allocated_bytes": allocated,
            "peak_cuda_reserved_bytes": reserved,
            "gradients": gradient_record,
        }
        del loss, outputs, projection

    changed_names = _changed_parameter_names(torch, before, named_trainable)
    changed_names_sha256 = hashlib.sha256(
        json.dumps(
            sorted(changed_names), separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    ).hexdigest()
    del before

    # The manual probe above establishes the full configured schedule and
    # extremal memory behavior.  Release its optimizer state before creating
    # Trainer's optimizer: at 32k tokens these two states must never coexist.
    del optimizer, scheduler, decay_parameters, no_decay_parameters
    gc.collect()
    torch.cuda.empty_cache()
    try:
        envelope_index = next(
            index
            for index, probe in enumerate(probe_records)
            if probe is memory_envelope
        )
    except StopIteration as exc:  # pragma: no cover - guarded by construction
        raise RuntimeError("memory-envelope probe is absent") from exc
    trainer_integration = _trainer_integration_probe(
        config,
        model,
        batches[envelope_index],
        memory_envelope,
        named_trainable,
        pad_token_id=tokenizer.pad_token_id,
        torch=torch,
        Trainer=Trainer,
        TrainerCallback=TrainerCallback,
        TrainingArguments=TrainingArguments,
    )

    model.eval()
    pre_save_use_cache = model.config.use_cache
    if type(pre_save_use_cache) is not bool:
        raise RuntimeError("pre-save model use_cache setting is not Boolean")
    with torch.inference_mode():
        for batch, probe in zip(batches, probe_records, strict=True):
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                loss, outputs, projection = _indexed_loss(model, batch)
            loss_value = float(loss.detach().float().cpu())
            if not math.isfinite(loss_value):
                raise RuntimeError("post-step LoRA smoke loss is non-finite")
            probe["post_step_eval"] = {
                "loss": loss_value,
                "projected_logits": _tensor_fingerprint(torch, outputs.logits),
            }
            del loss, outputs, projection

    base_reload_contract = BaseReloadContract(
        model_id=config.model.model_id,
        revision=model_commit,
        config_sha256=base_config_sha256,
        dtype=config.model.dtype,
        attention=config.model.attn_implementation,
        trust_remote_code=config.model.trust_remote_code,
    )
    in_memory_policy = capture_in_memory_policy(
        model=model,
        tokenizer=tokenizer,
        plan=admission_plan,
        base_contract=base_reload_contract,
        get_peft_model_state_dict=get_peft_model_state_dict,
        torch_module=torch,
        device="cuda:0",
    )

    scratch = REPOSITORY_ROOT / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="peano-lora-smoke-", dir=scratch) as raw:
        root = Path(raw)
        adapter_dir, tokenizer_dir, adapter_artifacts, tokenizer_artifacts = (
            _save_smoke_artifacts(
                model,
                tokenizer,
                root,
                require_protected=True,
            )
        )
        del model, named_trainable
        gc.collect()
        torch.cuda.empty_cache()

        reloaded_tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_dir,
            use_fast=True,
            trust_remote_code=False,
            local_files_only=True,
        )
        for selection, batch in zip(selections, natural_batches, strict=True):
            encoded = tokenize_completion(
                selection.example,
                reloaded_tokenizer,
                max_length=config.data.max_length,
            )
            expected = {
                name: values.detach().cpu().tolist()[0]
                for name, values in batch.items()
            }
            if encoded != expected:
                raise RuntimeError("saved tokenizer changed a complete smoke encoding")

        base = _load_base_model(
            config,
            torch,
            AutoModelForCausalLM,
            indexed_logits=True,
            local_files_only=True,
        )
        fresh_model_commit = _resolved_commit(
            getattr(base.config, "_commit_hash", None),
            config.model.revision,
            "fresh model",
        )
        if fresh_model_commit != model_commit:
            raise RuntimeError("fresh base model changed the pinned model commit")
        if not callable(getattr(base.config, "to_dict", None)):
            raise RuntimeError("fresh base model has no canonical configuration")
        if sha256_json(base.config.to_dict()) != base_config_sha256:
            raise RuntimeError("fresh base model changed its pristine configuration")
        base.config.use_cache = pre_save_use_cache
        reloaded = PeftModel.from_pretrained(
            base,
            adapter_dir,
            adapter_name="default",
            is_trainable=False,
            autocast_adapter_dtype=True,
            low_cpu_mem_usage=False,
            local_files_only=True,
        ).to("cuda")
        reloaded.config.use_cache = pre_save_use_cache
        if (
            base.config.use_cache != pre_save_use_cache
            or reloaded.config.use_cache != pre_save_use_cache
        ):
            raise RuntimeError("reloaded model changed the pre-save use_cache setting")
        reloaded.eval()
        saved_adapter_state = _read_adapter_safetensors(
            adapter_dir,
            safe_open=safe_open,
        )
        reloaded_adapter_state = canonical_peft_adapter_state(
            reloaded,
            get_peft_model_state_dict=get_peft_model_state_dict,
        )
        adapter_admission = admit_loaded_policy(
            reloaded_model=reloaded,
            reloaded_tokenizer=reloaded_tokenizer,
            saved_adapter_state=saved_adapter_state,
            reloaded_adapter_state=reloaded_adapter_state,
            plan=admission_plan,
            snapshot=in_memory_policy,
            base_contract=base_reload_contract,
            adapter_artifacts=adapter_artifacts,
            tokenizer_artifacts=tokenizer_artifacts,
            torch_module=torch,
            device="cuda:0",
            device_label="cuda:0",
        )
        del saved_adapter_state, reloaded_adapter_state
        with torch.inference_mode():
            for batch, probe in zip(batches, probe_records, strict=True):
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    loss, outputs, projection = _indexed_loss(reloaded, batch)
                loss_value = float(loss.detach().float().cpu())
                fingerprint = _tensor_fingerprint(torch, outputs.logits)
                reference = probe["post_step_eval"]
                _require_exact_reload(
                    reference,
                    loss=loss_value,
                    projected_logits=fingerprint,
                )
                probe["reloaded_eval"] = {
                    "loss": loss_value,
                    "projected_logits": fingerprint,
                    "exact_match": True,
                }
                del loss, outputs, projection
        verify_artifact_directory(
            root,
            adapter_artifacts,
            ADAPTER_SUBDIR,
            require_protected=True,
        )
        verify_artifact_directory(
            root,
            tokenizer_artifacts,
            TOKENIZER_SUBDIR,
            require_protected=True,
        )

    primary = probe_records[0]
    primary_training = primary.get("training")
    primary_reloaded = primary.get("reloaded_eval")
    if type(primary_training) is not dict or type(primary_reloaded) is not dict:
        raise RuntimeError("primary smoke evidence is incomplete")
    return {
        "model_commit": model_commit,
        "example": selections[0].example,
        "batch": batches[0],
        "trainable_parameters": trainable_parameters,
        "adapter_artifacts": adapter_artifacts,
        "tokenizer_artifacts": tokenizer_artifacts,
        "training_loss": primary_training["loss"],
        "reloaded_loss": primary_reloaded["loss"],
        "probes": probe_records,
        "step": {
            "seconds": round(step_seconds, 6),
            "peak_cuda_allocated_bytes": peak_allocated,
            "peak_cuda_reserved_bytes": peak_reserved,
            "gradient_checkpointing": config.trainer.gradient_checkpointing,
            "use_cache": pre_save_use_cache,
            "optimizer": "adamw_torch_fused",
            "gradient_clip_max_norm": _CUSTOM_CLIP_MAX_NORM,
            "tf32": True,
            "probe_count": len(probe_records),
            "memory_envelope": {
                "probe_id": memory_envelope["id"],
                "construction": memory_envelope["construction"],
                "sequence_tokens": memory_envelope["sequence_tokens"],
                "attended_tokens": memory_envelope["attended_tokens"],
                "supervised_tokens": memory_envelope["supervised_tokens"],
                "dominance": (
                    "componentwise-maxima-over-tokenized-selected-curriculum"
                ),
            },
        },
        "optimizer": {
            "name": "adamw_torch_fused",
            "betas": list(_ADAM_BETAS),
            "epsilon": _ADAM_EPSILON,
            "learning_rate": config.trainer.learning_rate,
            "weight_decay": config.trainer.weight_decay,
            "decay_parameter_tensors": decay_parameter_tensors,
            "no_decay_parameter_tensors": no_decay_parameter_tensors,
        },
        "scheduler": {
            "name": "cosine",
            **schedule,
            "initial_learning_rates": initial_lrs,
            "probe_start_learning_rates": peak_lrs,
            "warmup_advance": "optimizer-and-scheduler-steps-with-no-gradients",
        },
        "adapter_update": {
            "changed_parameter_tensors": len(changed_names),
            "changed_parameter_names_sha256": changed_names_sha256,
        },
        "adapter_admission": adapter_admission,
        "trainer_integration": trainer_integration,
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

    eligibility_record = _verified_corpus_record(config)

    import torch
    from peft import (
        LoraConfig as PeftLoraConfig,
        PeftModel,
        get_peft_model,
        get_peft_model_state_dict,
    )
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainerCallback,
        TrainingArguments,
        get_scheduler,
        set_seed,
    )

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

    selections, curriculum_record, token_record = _smoke_examples(config, tokenizer)
    curriculum_v2 = config.curriculum is not None
    smoke_admission: SmokeAdmissionPlan | None = None
    if curriculum_v2:
        if token_record is None or curriculum_record is None or eligibility_record is None:
            raise RuntimeError("curriculum smoke lacks sealed source evidence")
        _require_source_evidence_agrees(
            eligibility_record,
            curriculum_record,
            token_record,
        )
        smoke_admission = _smoke_admission_plan(
            config,
            tokenizer,
            selections,
            corpus_eligibility=eligibility_record,
            curriculum_attestation=curriculum_record,
            tokenized_train=token_record,
        )
        from safetensors import safe_open

        evidence = _curriculum_model_smoke(
            config,
            tokenizer,
            selections,
            token_record,
            smoke_admission.plan,
            torch,
            AutoModelForCausalLM,
            AutoTokenizer,
            PeftLoraConfig,
            PeftModel,
            get_peft_model,
            get_peft_model_state_dict,
            safe_open,
            Trainer,
            TrainerCallback,
            TrainingArguments,
            get_scheduler,
        )
    else:
        if len(selections) != 1:
            raise RuntimeError("legacy smoke selected more than one row")
        evidence = _legacy_model_smoke(
            config,
            tokenizer,
            selections[0],
            torch,
            AutoModelForCausalLM,
            AutoTokenizer,
            PeftLoraConfig,
            PeftModel,
            get_peft_model,
        )

    example = evidence["example"]
    batch = evidence["batch"]
    report: dict[str, object] = {
        "format": platform_contract.report_format,
        "v": 2 if curriculum_v2 else 1,
        "status": "passed",
        "model": {
            "id": config.model.model_id,
            "requested_revision": config.model.revision,
            "model_commit": evidence["model_commit"],
            "tokenizer_commit": tokenizer_commit,
        },
        "example": {
            "id": example.example_id,
            "sequence_tokens": int(batch["input_ids"].shape[1]),
        },
        "lora": {
            "rank": config.lora.rank,
            "target_modules": list(config.lora.target_modules),
            "trainable_parameters": evidence["trainable_parameters"],
            "adapter_artifacts": evidence["adapter_artifacts"],
            "tokenizer_artifacts": evidence["tokenizer_artifacts"],
        },
        "loss": {
            "training": evidence["training_loss"],
            "reloaded": evidence["reloaded_loss"],
        },
        "runtime": runtime_identity(torch),
        "job": slurm_job_identity(),
    }
    if curriculum_v2:
        if smoke_admission is None:
            raise RuntimeError("curriculum smoke lost its adapter-admission plan")
        report["example"]["selection"] = "longest-reviewed-curriculum-row"
        report["lora"].update(
            {
                "alpha": config.lora.alpha,
                "dropout": config.lora.dropout,
                "adapter_update": evidence["adapter_update"],
            }
        )
        report["objective"] = completion_objective_record()
        report["step"] = evidence["step"]
        report["optimizer"] = evidence["optimizer"]
        report["scheduler"] = evidence["scheduler"]
        report["trainer_integration"] = evidence["trainer_integration"]
        report["adapter_admission"] = evidence["adapter_admission"]
        report["adapter_admission_selection"] = smoke_admission.selection
        report["smoke_probes"] = evidence["probes"]
        report["corpus_eligibility"] = eligibility_record
        report["curriculum"] = curriculum_record
        report["tokenized_train"] = token_record
        report["tokenized_evaluation"] = smoke_admission.tokenized_evaluation
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
