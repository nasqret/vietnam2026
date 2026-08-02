"""Fail-closed evidence for admitting a completed model-v3 training run.

This module is deliberately framework-light.  It validates ordinary Python
records and imports neither Torch nor Transformers.  The training runner is
responsible for observing gradients at the real pre-optimizer boundary; the
small accumulator below makes those observations sequential and stable before
they are summarized in the final immutable manifest.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import math
import os
from pathlib import Path
import stat
from typing import Any

from .manifest import sha256_json
from .objective import TRAINER_RUNTIME_FORMAT, TRAINER_RUNTIME_VERSION
from .prompt import PEANO_PROMPT_V3


TRAINING_EVIDENCE_FORMAT = "peano-policy-completed-training-evidence"
TRAINING_EVIDENCE_VERSION = 1
FINITE_GRADIENT_AUDIT_FORMAT = "peano-policy-finite-gradient-audit"
FINITE_GRADIENT_AUDIT_VERSION = 1
OPTIMIZER_LOG_FORMAT = "peano-policy-optimizer-log-history"
OPTIMIZER_LOG_VERSION = 1
HASH_ALGORITHM = "sha256"
HASH_CANONICALIZATION = "utf8-json-sort-keys-no-whitespace-v1"
EVALUATION_LOSS_SEMANTICS = "mean-of-per-example-completion-token-means"
TRAINING_LOSS_SEMANTICS = "mean-of-optimizer-window-completion-token-means"
TRAINER_ARGUMENTS_FORMAT = "peano-policy-reviewed-trainer-arguments"
TRAINER_ARGUMENTS_VERSION = 2
CUSTOM_GRADIENT_CLIP_MAX_NORM = 1.0
OPTIMIZER_STEPS_HASH_PAYLOAD_FORMAT = (
    "json-list-of-consecutive-integers-one-through-final-step-v1"
)
PARAMETER_NAMES_HASH_PAYLOAD_FORMAT = (
    "json-list-of-sorted-unique-trainable-parameter-names-v1"
)
GRADIENT_NORMS_HASH_PAYLOAD_FORMAT = (
    "json-list-of-step-and-pre-clip-global-norm-records-v1"
)
OPTIMIZER_LOG_HASH_PAYLOAD_FORMAT = (
    "json-list-of-exact-finite-trainer-log-history-records-v1"
)
METRICS_HASH_PAYLOAD_FORMAT = "json-object-with-finite-train-and-eval-metrics-v1"
ADAPTER_UPDATE_FORMAT = "peano-policy-adapter-update-audit"
ADAPTER_UPDATE_VERSION = 1
TENSOR_POPULATION_FINGERPRINT_FORMAT = (
    "sha256-canonical-json-sorted-name-dtype-shape-content-sha256-records-v1"
)
_MAX_MANIFEST_BYTES = 16 * 1024 * 1024

_HEX = frozenset("0123456789abcdef")
_ROOT_KEYS = {
    "format",
    "v",
    "status",
    "steps",
    "runtime",
    "trainer_arguments",
    "gradients",
    "adapter_update",
    "logging",
    "metrics",
    "artifacts",
    "hash_contract",
    "content_sha256",
}
_STEP_KEYS = {
    "expected_optimizer_steps",
    "top_level_actual_optimizer_steps",
    "train_result_global_step",
    "trainer_state_global_step",
    "trainer_state_max_steps",
}
_RUNTIME_KEYS = {
    "format",
    "v",
    "num_processes",
    "visible_gpus",
    "device",
    "mixed_precision",
    "distributed_type",
    "dynamo_backend",
    "plugins",
    "manual_trainer_accumulation",
    "configured_trainer_gradient_accumulation_steps",
    "accelerator_backward_divisor",
}
_GRADIENT_KEYS = {
    "format",
    "v",
    "expected_optimizer_boundaries",
    "observed_optimizer_boundaries",
    "raw_finite_optimizer_boundaries",
    "post_clip_finite_optimizer_boundaries",
    "first_optimizer_step",
    "last_optimizer_step",
    "optimizer_steps_sha256",
    "optimizer_steps_hash_payload_format",
    "trainable_parameter_tensors",
    "trainable_parameter_names_sha256",
    "trainable_parameter_names_hash_payload_format",
    "custom_gradient_clip_max_norm",
    "records",
    "records_sha256",
    "records_hash_payload_format",
}
_GRADIENT_RECORD_KEYS = {"step", "pre_clip_global_norm"}
_LOGGING_KEYS = {
    "format",
    "v",
    "logging_steps",
    "records",
    "records_sha256",
    "records_hash_payload_format",
}
_METRIC_KEYS = {
    "train",
    "eval",
    "training_loss_semantics",
    "evaluation_loss_semantics",
    "records_sha256",
    "records_hash_payload_format",
    "top_level_metrics_sha256",
}
_ARTIFACT_KEYS = {"adapter_sha256", "tokenizer_sha256"}
_ADAPTER_UPDATE_KEYS = {
    "format",
    "v",
    "trainable_parameter_tensors",
    "trainable_parameter_names",
    "trainable_parameter_names_sha256",
    "trainable_parameter_names_hash_payload_format",
    "tensor_population_fingerprint_format",
    "initial_tensor_population_sha256",
    "final_tensor_population_sha256",
    "changed_parameter_tensors",
    "changed_parameter_names",
    "changed_parameter_names_sha256",
    "changed_parameter_names_hash_payload_format",
    "final_finite_parameter_tensors",
}
_TRAINER_ARGUMENT_KEYS = {
    "format",
    "v",
    "built_in_max_grad_norm",
    "custom_gradient_clip_max_norm",
    "custom_gradient_clip_error_if_nonfinite",
    "gradient_boundary",
    "bf16",
    "bf16_full_eval",
    "save_strategy",
    "eval_strategy",
    "logging_nan_inf_filter",
    "logging_steps",
    "per_device_train_batch_size",
    "per_device_eval_batch_size",
    "gradient_accumulation_steps",
}


class TrainingEvidenceError(ValueError):
    """A claimed completed-training record is missing or inconsistent."""


def _mapping(value: object, keys: set[str], label: str) -> Mapping[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise TrainingEvidenceError(f"{label} has a malformed exact schema")
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise TrainingEvidenceError(f"{label} must be a positive integer")
    return value


def _sha256(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise TrainingEvidenceError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _finite_number(value: object, label: str) -> int | float:
    if type(value) not in {int, float}:
        raise TrainingEvidenceError(f"{label} must be a finite non-boolean number")
    try:
        finite = math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        finite = False
    if not finite:
        raise TrainingEvidenceError(f"{label} must be a finite non-boolean number")
    return value


def _finite_float(value: object, label: str) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise TrainingEvidenceError(f"{label} must be one finite JSON float")
    return value


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TrainingEvidenceError(f"duplicate training-manifest key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise TrainingEvidenceError(
        f"training manifest contains forbidden non-finite constant {value}"
    )


def _file_identity(
    value: os.stat_result,
) -> tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_strict_training_manifest(path: Path) -> dict[str, object]:
    """Read one stable regular-file snapshot with strict finite JSON syntax."""

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise TrainingEvidenceError(f"cannot open training manifest: {exc}") from None
    chunks: list[bytes] = []
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > _MAX_MANIFEST_BYTES
        ):
            raise TrainingEvidenceError(
                "training manifest must be one bounded regular file"
            )
        remaining = _MAX_MANIFEST_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    if (
        len(payload) > _MAX_MANIFEST_BYTES
        or len(payload) != before.st_size
        or _file_identity(before) != _file_identity(after)
    ):
        raise TrainingEvidenceError("training manifest changed while it was read")
    try:
        path_after = path.lstat()
    except OSError as exc:
        raise TrainingEvidenceError(
            f"cannot recheck training manifest snapshot: {exc}"
        ) from None
    if path_after.st_nlink != 1 or _file_identity(path_after) != _file_identity(after):
        raise TrainingEvidenceError("training manifest path changed while it was read")
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TrainingEvidenceError(f"invalid training-manifest JSON: {exc}") from None
    if type(value) is not dict:
        raise TrainingEvidenceError("training manifest root must be one JSON object")
    return value


def _canonical_parameter_names(names: Iterable[str]) -> tuple[str, ...]:
    values = tuple(names)
    if (
        not values
        or any(type(name) is not str or not name for name in values)
        or len(set(values)) != len(values)
    ):
        raise TrainingEvidenceError(
            "trainable parameter names must be unique non-empty strings"
        )
    return tuple(sorted(values))


def _optimizer_steps_sha256(optimizer_steps: int) -> str:
    return sha256_json(list(range(1, optimizer_steps + 1)))


class FiniteGradientAudit:
    """Accumulate one already-checked finite-gradient observation per step.

    The caller must inspect the live gradient tensors and pass exactly the
    names which both have a gradient and have passed its finite-value check.
    Missing, extra, duplicate, reordered, or skipped boundary observations are
    rejected immediately.  No tensor or framework object is retained.
    """

    def __init__(
        self,
        *,
        expected_optimizer_steps: int,
        trainable_parameter_names: Iterable[str],
    ) -> None:
        self._expected_steps = _positive_int(
            expected_optimizer_steps, "expected optimizer boundaries"
        )
        self._names = _canonical_parameter_names(trainable_parameter_names)
        self._names_sha256 = sha256_json(list(self._names))
        self._observed_steps: list[int] = []
        self._records: list[dict[str, object]] = []

    def observe_pre_optimizer_step(
        self,
        *,
        trainer_state_global_step: int,
        raw_finite_gradient_parameter_names: Iterable[str],
        pre_clip_global_norm: float,
        post_clip_finite_gradient_parameter_names: Iterable[str],
    ) -> None:
        """Record the next boundary after live gradient finiteness checks.

        Transformers invokes ``on_pre_optimizer_step`` before incrementing
        ``TrainerState.global_step``.  Therefore the optimizer boundary being
        observed is exactly ``trainer_state_global_step + 1``.
        """

        if type(trainer_state_global_step) is not int or trainer_state_global_step < 0:
            raise TrainingEvidenceError(
                "pre-optimizer Trainer global step must be a non-negative integer"
            )
        step = trainer_state_global_step + 1
        expected_next = len(self._observed_steps) + 1
        if step != expected_next or step > self._expected_steps:
            raise TrainingEvidenceError(
                "finite-gradient observations must cover optimizer steps "
                "exactly once in order"
            )
        raw_names = _canonical_parameter_names(
            raw_finite_gradient_parameter_names
        )
        post_clip_names = _canonical_parameter_names(
            post_clip_finite_gradient_parameter_names
        )
        if raw_names != self._names or post_clip_names != self._names:
            raise TrainingEvidenceError(
                "raw and post-clip finite gradients must cover the stable "
                "trainable population"
            )
        norm = _finite_float(pre_clip_global_norm, "pre-clip global gradient norm")
        if norm < 0.0:
            raise TrainingEvidenceError(
                "pre-clip global gradient norm must be non-negative"
            )
        self._observed_steps.append(step)
        self._records.append({"step": step, "pre_clip_global_norm": norm})

    def record(self) -> dict[str, object]:
        """Finalize only after every expected optimizer boundary was observed."""

        if self._observed_steps != list(range(1, self._expected_steps + 1)):
            raise TrainingEvidenceError(
                "finite-gradient audit is incomplete at training finalization"
            )
        return {
            "format": FINITE_GRADIENT_AUDIT_FORMAT,
            "v": FINITE_GRADIENT_AUDIT_VERSION,
            "expected_optimizer_boundaries": self._expected_steps,
            "observed_optimizer_boundaries": self._expected_steps,
            "raw_finite_optimizer_boundaries": self._expected_steps,
            "post_clip_finite_optimizer_boundaries": self._expected_steps,
            "first_optimizer_step": 1,
            "last_optimizer_step": self._expected_steps,
            "optimizer_steps_sha256": sha256_json(self._observed_steps),
            "optimizer_steps_hash_payload_format": (
                OPTIMIZER_STEPS_HASH_PAYLOAD_FORMAT
            ),
            "trainable_parameter_tensors": len(self._names),
            "trainable_parameter_names_sha256": self._names_sha256,
            "trainable_parameter_names_hash_payload_format": (
                PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
            ),
            "custom_gradient_clip_max_norm": CUSTOM_GRADIENT_CLIP_MAX_NORM,
            "records": list(self._records),
            "records_sha256": sha256_json(self._records),
            "records_hash_payload_format": GRADIENT_NORMS_HASH_PAYLOAD_FORMAT,
        }


def _validate_runtime(value: object) -> dict[str, object]:
    runtime = _mapping(value, _RUNTIME_KEYS, "Trainer runtime contract")
    if (
        runtime.get("format") != TRAINER_RUNTIME_FORMAT
        or type(runtime.get("v")) is not int
        or runtime.get("v") != TRAINER_RUNTIME_VERSION
        or runtime.get("num_processes") != 1
        or type(runtime.get("num_processes")) is not int
        or runtime.get("visible_gpus") != 1
        or type(runtime.get("visible_gpus")) is not int
        or runtime.get("device") != {"type": "cuda", "index": 0}
        or runtime.get("mixed_precision") != "bf16"
        or runtime.get("distributed_type") != {"name": "NO", "value": "NO"}
        or runtime.get("dynamo_backend") != {"name": "NO", "value": "NO"}
        or runtime.get("plugins")
        != {"deepspeed": False, "fsdp": False, "tensor_parallel": False}
        or runtime.get("manual_trainer_accumulation") is not True
        or runtime.get("accelerator_backward_divisor") != 1
        or type(runtime.get("accelerator_backward_divisor")) is not int
    ):
        raise TrainingEvidenceError(
            "completed evidence has an unreviewed Trainer/Accelerator runtime"
        )
    _positive_int(
        runtime.get("configured_trainer_gradient_accumulation_steps"),
        "configured Trainer gradient accumulation",
    )
    return dict(runtime)


def _validate_trainer_arguments(value: object) -> dict[str, object]:
    arguments = _mapping(
        value, _TRAINER_ARGUMENT_KEYS, "reviewed Trainer arguments"
    )
    if (
        arguments.get("format") != TRAINER_ARGUMENTS_FORMAT
        or type(arguments.get("v")) is not int
        or arguments.get("v") != TRAINER_ARGUMENTS_VERSION
        or type(arguments.get("built_in_max_grad_norm")) is not float
        or arguments.get("built_in_max_grad_norm") != 0.0
        or type(arguments.get("custom_gradient_clip_max_norm")) is not float
        or arguments.get("custom_gradient_clip_max_norm")
        != CUSTOM_GRADIENT_CLIP_MAX_NORM
        or arguments.get("custom_gradient_clip_error_if_nonfinite") is not True
        or arguments.get("gradient_boundary")
        != "on_pre_optimizer_step-with-transformers-clipping-disabled"
        or arguments.get("bf16") is not True
        or arguments.get("bf16_full_eval") is not False
        or arguments.get("save_strategy") != "no"
        or arguments.get("eval_strategy") != "no"
        or arguments.get("logging_nan_inf_filter") is not False
        or type(arguments.get("per_device_train_batch_size")) is not int
        or arguments.get("per_device_train_batch_size") != 1
        or type(arguments.get("per_device_eval_batch_size")) is not int
        or arguments.get("per_device_eval_batch_size") != 1
    ):
        raise TrainingEvidenceError(
            "completed evidence has unreviewed Trainer clipping/save/eval arguments"
        )
    _positive_int(arguments.get("logging_steps"), "Trainer logging interval")
    _positive_int(
        arguments.get("gradient_accumulation_steps"),
        "Trainer gradient accumulation",
    )
    return dict(arguments)


def reviewed_trainer_arguments_record(trainer: object) -> dict[str, object]:
    """Inspect and return the exact Trainer/custom-clipping contract."""

    args = getattr(trainer, "args", None)
    if args is None:
        raise TrainingEvidenceError("Trainer arguments are not initialized")

    def strategy(name: str) -> object:
        value = getattr(args, name, None)
        return getattr(value, "value", value)

    observed = {
        "format": TRAINER_ARGUMENTS_FORMAT,
        "v": TRAINER_ARGUMENTS_VERSION,
        "built_in_max_grad_norm": getattr(args, "max_grad_norm", None),
        "custom_gradient_clip_max_norm": CUSTOM_GRADIENT_CLIP_MAX_NORM,
        "custom_gradient_clip_error_if_nonfinite": True,
        "gradient_boundary": (
            "on_pre_optimizer_step-with-transformers-clipping-disabled"
        ),
        "bf16": getattr(args, "bf16", None),
        "bf16_full_eval": getattr(args, "bf16_full_eval", None),
        "save_strategy": strategy("save_strategy"),
        "eval_strategy": strategy("eval_strategy"),
        "logging_nan_inf_filter": getattr(
            args, "logging_nan_inf_filter", None
        ),
        "logging_steps": getattr(args, "logging_steps", None),
        "per_device_train_batch_size": getattr(
            args, "per_device_train_batch_size", None
        ),
        "per_device_eval_batch_size": getattr(
            args, "per_device_eval_batch_size", None
        ),
        "gradient_accumulation_steps": getattr(
            args, "gradient_accumulation_steps", None
        ),
    }
    return _validate_trainer_arguments(observed)


def _validate_gradients(value: object, optimizer_steps: int) -> dict[str, object]:
    gradients = _mapping(value, _GRADIENT_KEYS, "finite-gradient audit")
    if (
        gradients.get("format") != FINITE_GRADIENT_AUDIT_FORMAT
        or type(gradients.get("v")) is not int
        or gradients.get("v") != FINITE_GRADIENT_AUDIT_VERSION
    ):
        raise TrainingEvidenceError("finite-gradient audit format is unsupported")
    counts = (
        gradients.get("expected_optimizer_boundaries"),
        gradients.get("observed_optimizer_boundaries"),
        gradients.get("raw_finite_optimizer_boundaries"),
        gradients.get("post_clip_finite_optimizer_boundaries"),
        gradients.get("last_optimizer_step"),
    )
    if any(type(count) is not int or count != optimizer_steps for count in counts):
        raise TrainingEvidenceError(
            "finite-gradient audit does not cover every optimizer boundary"
        )
    if (
        type(gradients.get("first_optimizer_step")) is not int
        or gradients.get("first_optimizer_step") != 1
        or gradients.get("optimizer_steps_sha256")
        != _optimizer_steps_sha256(optimizer_steps)
        or gradients.get("optimizer_steps_hash_payload_format")
        != OPTIMIZER_STEPS_HASH_PAYLOAD_FORMAT
    ):
        raise TrainingEvidenceError(
            "finite-gradient optimizer-step sequence is incomplete or reordered"
        )
    _positive_int(
        gradients.get("trainable_parameter_tensors"),
        "trainable parameter tensor count",
    )
    _sha256(
        gradients.get("trainable_parameter_names_sha256"),
        "trainable parameter name hash",
    )
    if (
        gradients.get("trainable_parameter_names_hash_payload_format")
        != PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
        or type(gradients.get("custom_gradient_clip_max_norm")) is not float
        or gradients.get("custom_gradient_clip_max_norm")
        != CUSTOM_GRADIENT_CLIP_MAX_NORM
    ):
        raise TrainingEvidenceError(
            "finite-gradient audit has a different population or clip contract"
        )
    records = gradients.get("records")
    if type(records) is not list:
        raise TrainingEvidenceError("gradient norm records must be one JSON list")
    canonical_records: list[dict[str, object]] = []
    for index, value_record in enumerate(records):
        record = _mapping(
            value_record, _GRADIENT_RECORD_KEYS, f"gradient norm record {index}"
        )
        norm = _finite_float(
            record.get("pre_clip_global_norm"), "pre-clip global gradient norm"
        )
        if norm < 0.0:
            raise TrainingEvidenceError(
                "pre-clip global gradient norm must be non-negative"
            )
        canonical_records.append(
            {
                "step": _positive_int(record.get("step"), "gradient norm step"),
                "pre_clip_global_norm": norm,
            }
        )
    if [record["step"] for record in canonical_records] != list(
        range(1, optimizer_steps + 1)
    ):
        raise TrainingEvidenceError(
            "gradient norm records must cover every optimizer boundary in order"
        )
    if (
        gradients.get("records_sha256") != sha256_json(canonical_records)
        or gradients.get("records_hash_payload_format")
        != GRADIENT_NORMS_HASH_PAYLOAD_FORMAT
    ):
        raise TrainingEvidenceError("gradient norm record hash is stale or forged")
    return dict(gradients)


def adapter_update_audit_record(
    *,
    trainable_parameter_names: Iterable[str],
    initial_tensor_population_sha256: str,
    final_tensor_population_sha256: str,
    changed_parameter_names: Iterable[str],
    final_finite_parameter_names: Iterable[str],
) -> dict[str, object]:
    """Build a compact proof that training changed a finite adapter population."""

    trainable = _canonical_parameter_names(trainable_parameter_names)
    changed = _canonical_parameter_names(changed_parameter_names)
    final_finite = _canonical_parameter_names(final_finite_parameter_names)
    if not set(changed).issubset(trainable):
        raise TrainingEvidenceError(
            "changed adapter tensors are not a subset of the trainable population"
        )
    if final_finite != trainable:
        raise TrainingEvidenceError(
            "final finite tensors do not cover the trainable population"
        )
    initial = _sha256(
        initial_tensor_population_sha256, "initial tensor-population fingerprint"
    )
    final = _sha256(
        final_tensor_population_sha256, "final tensor-population fingerprint"
    )
    if initial == final:
        raise TrainingEvidenceError("training did not change the adapter population")
    return {
        "format": ADAPTER_UPDATE_FORMAT,
        "v": ADAPTER_UPDATE_VERSION,
        "trainable_parameter_tensors": len(trainable),
        "trainable_parameter_names": list(trainable),
        "trainable_parameter_names_sha256": sha256_json(list(trainable)),
        "trainable_parameter_names_hash_payload_format": (
            PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
        ),
        "tensor_population_fingerprint_format": (
            TENSOR_POPULATION_FINGERPRINT_FORMAT
        ),
        "initial_tensor_population_sha256": initial,
        "final_tensor_population_sha256": final,
        "changed_parameter_tensors": len(changed),
        "changed_parameter_names": list(changed),
        "changed_parameter_names_sha256": sha256_json(list(changed)),
        "changed_parameter_names_hash_payload_format": (
            PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
        ),
        "final_finite_parameter_tensors": len(final_finite),
    }


def _validate_adapter_update(
    value: object,
    *,
    gradients: Mapping[str, object],
) -> dict[str, object]:
    update = _mapping(value, _ADAPTER_UPDATE_KEYS, "adapter-update audit")
    if (
        update.get("format") != ADAPTER_UPDATE_FORMAT
        or type(update.get("v")) is not int
        or update.get("v") != ADAPTER_UPDATE_VERSION
        or update.get("trainable_parameter_names_hash_payload_format")
        != PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
        or update.get("changed_parameter_names_hash_payload_format")
        != PARAMETER_NAMES_HASH_PAYLOAD_FORMAT
        or update.get("tensor_population_fingerprint_format")
        != TENSOR_POPULATION_FINGERPRINT_FORMAT
    ):
        raise TrainingEvidenceError("adapter-update audit format is unsupported")
    trainable_raw = update.get("trainable_parameter_names")
    changed_raw = update.get("changed_parameter_names")
    if type(trainable_raw) is not list or type(changed_raw) is not list:
        raise TrainingEvidenceError("adapter-update parameter names must be JSON lists")
    trainable = _canonical_parameter_names(trainable_raw)
    changed = _canonical_parameter_names(changed_raw)
    if list(trainable) != trainable_raw or list(changed) != changed_raw:
        raise TrainingEvidenceError("adapter-update parameter names are not canonical")
    population = _positive_int(
        update.get("trainable_parameter_tensors"),
        "adapter trainable parameter tensor count",
    )
    changed_count = _positive_int(
        update.get("changed_parameter_tensors"),
        "changed adapter parameter tensor count",
    )
    if (
        population != len(trainable)
        or changed_count != len(changed)
        or changed_count > population
        or not set(changed).issubset(trainable)
        or type(update.get("final_finite_parameter_tensors")) is not int
        or update.get("final_finite_parameter_tensors") != population
    ):
        raise TrainingEvidenceError(
            "adapter update does not bind a changed, wholly finite population"
        )
    names_hash = sha256_json(list(trainable))
    if (
        update.get("trainable_parameter_names_sha256") != names_hash
        or update.get("changed_parameter_names_sha256")
        != sha256_json(list(changed))
        or gradients.get("trainable_parameter_tensors") != population
        or gradients.get("trainable_parameter_names_sha256") != names_hash
    ):
        raise TrainingEvidenceError(
            "adapter-update population differs from finite-gradient evidence"
        )
    initial = _sha256(
        update.get("initial_tensor_population_sha256"),
        "initial tensor-population fingerprint",
    )
    final = _sha256(
        update.get("final_tensor_population_sha256"),
        "final tensor-population fingerprint",
    )
    if initial == final:
        raise TrainingEvidenceError("training did not change the adapter population")
    return dict(update)


def _canonical_history_record(
    value: object,
    *,
    index: int,
) -> dict[str, int | float]:
    if not isinstance(value, Mapping) or not value:
        raise TrainingEvidenceError(
            f"Trainer log history record {index} is not one non-empty record"
        )
    result: dict[str, int | float] = {}
    for key, metric in value.items():
        if type(key) is not str or not key:
            raise TrainingEvidenceError(
                f"Trainer log history record {index} has an invalid key"
            )
        result[key] = _finite_number(
            metric, f"Trainer log history record {index} field {key}"
        )
    _positive_int(result.get("step"), f"Trainer log history record {index} step")
    return result


def _history_kind(record: Mapping[str, object], index: int) -> str:
    present = tuple(
        key for key in ("loss", "train_loss", "eval_loss") if key in record
    )
    if len(present) != 1:
        raise TrainingEvidenceError(
            f"Trainer log history record {index} has an ambiguous category"
        )
    kind = present[0]
    if kind == "loss":
        if "learning_rate" not in record:
            raise TrainingEvidenceError(
                f"periodic Trainer log history record {index} lacks learning_rate"
            )
        # Transformers 4.53.3 adds grad_norm only when its local value is not
        # None.  With reviewed max_grad_norm=0, it remains None and the key is
        # omitted; custom raw/preclip evidence lives in the gradient audit.
        if "grad_norm" in record:
            raise TrainingEvidenceError(
                f"periodic Trainer log history record {index} unexpectedly "
                "claims built-in gradient clipping"
            )
    return kind


def _validate_history_shape(
    records: list[dict[str, int | float]],
    *,
    optimizer_steps: int,
    logging_steps: int,
    train_metrics: Mapping[str, int | float],
    evaluation_metrics: Mapping[str, int | float],
) -> None:
    interval = _positive_int(logging_steps, "configured logging steps")
    if optimizer_steps % interval != 0:
        raise TrainingEvidenceError(
            "completed optimizer schedule must end on a configured logging boundary"
        )
    periodic_steps = list(range(interval, optimizer_steps + 1, interval))
    if len(records) != len(periodic_steps) + 2:
        raise TrainingEvidenceError(
            "Trainer history must contain periodic logs then one train and one eval summary"
        )
    kinds = [_history_kind(record, index) for index, record in enumerate(records)]
    if kinds != ["loss"] * len(periodic_steps) + ["train_loss", "eval_loss"]:
        raise TrainingEvidenceError(
            "Trainer history categories are missing, duplicated, or out of order"
        )
    if [record["step"] for record in records[: len(periodic_steps)]] != periodic_steps:
        raise TrainingEvidenceError(
            "periodic optimizer logs must occur exactly once at every logging step"
        )
    train_summary = dict(records[-2])
    eval_summary = dict(records[-1])
    if train_summary.pop("step") != optimizer_steps:
        raise TrainingEvidenceError("final training summary has the wrong step")
    if eval_summary.pop("step") != optimizer_steps:
        raise TrainingEvidenceError("final evaluation summary has the wrong step")
    if train_summary != dict(train_metrics):
        raise TrainingEvidenceError(
            "Trainer history training summary differs from top-level train metrics"
        )
    if eval_summary != dict(evaluation_metrics):
        raise TrainingEvidenceError(
            "Trainer history evaluation summary differs from top-level eval metrics"
        )


def _normalized_trainer_history(
    log_history: Sequence[Mapping[str, object]],
    *,
    optimizer_steps: int,
    logging_steps: int,
    train_metrics: Mapping[str, int | float],
    evaluation_metrics: Mapping[str, int | float],
) -> list[dict[str, int | float]]:
    if isinstance(log_history, (str, bytes)) or not isinstance(
        log_history, Sequence
    ):
        raise TrainingEvidenceError("Trainer log history must be one sequence")
    records = [
        _canonical_history_record(raw, index=index)
        for index, raw in enumerate(log_history)
    ]
    _validate_history_shape(
        records,
        optimizer_steps=optimizer_steps,
        logging_steps=logging_steps,
        train_metrics=train_metrics,
        evaluation_metrics=evaluation_metrics,
    )
    return records


def _validate_logging(
    value: object,
    optimizer_steps: int,
    *,
    train_metrics: Mapping[str, int | float],
    evaluation_metrics: Mapping[str, int | float],
) -> dict[str, object]:
    logging = _mapping(value, _LOGGING_KEYS, "optimizer logging evidence")
    if (
        logging.get("format") != OPTIMIZER_LOG_FORMAT
        or type(logging.get("v")) is not int
        or logging.get("v") != OPTIMIZER_LOG_VERSION
    ):
        raise TrainingEvidenceError("optimizer logging evidence format is unsupported")
    interval = _positive_int(logging.get("logging_steps"), "configured logging steps")
    records = logging.get("records")
    if type(records) is not list:
        raise TrainingEvidenceError("optimizer logging records must be one JSON list")
    canonical = [
        _canonical_history_record(record, index=index)
        for index, record in enumerate(records)
    ]
    _validate_history_shape(
        canonical,
        optimizer_steps=optimizer_steps,
        logging_steps=interval,
        train_metrics=train_metrics,
        evaluation_metrics=evaluation_metrics,
    )
    if (
        logging.get("records_sha256") != sha256_json(canonical)
        or logging.get("records_hash_payload_format")
        != OPTIMIZER_LOG_HASH_PAYLOAD_FORMAT
    ):
        raise TrainingEvidenceError("optimizer logging record hash is stale or forged")
    return {
        "format": OPTIMIZER_LOG_FORMAT,
        "v": OPTIMIZER_LOG_VERSION,
        "logging_steps": interval,
        "records": canonical,
        "records_sha256": logging["records_sha256"],
        "records_hash_payload_format": OPTIMIZER_LOG_HASH_PAYLOAD_FORMAT,
    }


def _finite_metrics(value: object, required: str, label: str) -> dict[str, int | float]:
    if type(value) is not dict or required not in value or not value:
        raise TrainingEvidenceError(f"{label} lacks required finite {required}")
    result: dict[str, int | float] = {}
    for key, metric in value.items():
        if type(key) is not str or not key:
            raise TrainingEvidenceError(f"{label} has an invalid metric name")
        result[key] = _finite_number(metric, f"{label} {key}")
    return result


def _validate_top_level_metrics(
    value: object,
    *,
    optimizer_steps: int,
) -> tuple[dict[str, object], dict[str, int | float], dict[str, int | float]]:
    if type(value) is not dict:
        raise TrainingEvidenceError("training manifest has no top-level metrics record")
    train = _finite_metrics(value.get("train"), "train_loss", "training metrics")
    evaluation = _finite_metrics(value.get("eval"), "eval_loss", "evaluation metrics")
    if (
        type(value.get("expected_optimizer_steps")) is not int
        or value.get("expected_optimizer_steps") != optimizer_steps
        or type(value.get("actual_optimizer_steps")) is not int
        or value.get("actual_optimizer_steps") != optimizer_steps
    ):
        raise TrainingEvidenceError(
            "top-level optimizer-step metrics differ from completed evidence"
        )
    # Every additional scalar is part of the claimed experiment record.  Keep
    # the schema forward-compatible while forbidding strings, bools, and JSON's
    # non-standard NaN/Infinity values.
    for key, metric in value.items():
        if key in {"train", "eval"}:
            continue
        if type(key) is not str or not key:
            raise TrainingEvidenceError("top-level metrics has an invalid key")
        _finite_number(metric, f"top-level metric {key}")
    return dict(value), train, evaluation


def _artifact_hashes(manifest: Mapping[str, object]) -> tuple[object, object]:
    adapter = manifest.get("adapter")
    tokenizer = manifest.get("tokenizer")
    adapter_hash = adapter.get("sha256") if type(adapter) is dict else None
    tokenizer_artifacts = (
        tokenizer.get("artifacts") if type(tokenizer) is dict else None
    )
    tokenizer_hash = (
        tokenizer_artifacts.get("sha256")
        if type(tokenizer_artifacts) is dict
        else None
    )
    return adapter_hash, tokenizer_hash


def completed_training_evidence_record(
    *,
    top_level_metrics: Mapping[str, object],
    train_result_global_step: int,
    trainer_state_global_step: int,
    trainer_state_max_steps: int,
    trainer_runtime: Mapping[str, object],
    trainer_arguments: Mapping[str, object],
    finite_gradient_audit: Mapping[str, object],
    adapter_update: Mapping[str, object],
    logging_steps: int,
    log_history: Sequence[Mapping[str, object]],
    adapter_sha256: str,
    tokenizer_sha256: str,
) -> dict[str, object]:
    """Build the one canonical completed-training record for publication."""

    expected = _positive_int(
        top_level_metrics.get("expected_optimizer_steps"),
        "expected optimizer steps",
    )
    actual = _positive_int(
        top_level_metrics.get("actual_optimizer_steps"),
        "actual optimizer steps",
    )
    result_step = _positive_int(
        train_result_global_step, "train result global step"
    )
    state_step = _positive_int(
        trainer_state_global_step, "Trainer state global step"
    )
    maximum = _positive_int(trainer_state_max_steps, "Trainer state maximum steps")
    if len({expected, actual, result_step, state_step, maximum}) != 1:
        raise TrainingEvidenceError(
            "expected, actual, train-result, state, and maximum optimizer steps "
            "must agree"
        )
    runtime = _validate_runtime(dict(trainer_runtime))
    reviewed_arguments = _validate_trainer_arguments(dict(trainer_arguments))
    if (
        reviewed_arguments.get("gradient_accumulation_steps")
        != runtime.get("configured_trainer_gradient_accumulation_steps")
        or reviewed_arguments.get("logging_steps") != logging_steps
    ):
        raise TrainingEvidenceError(
            "observed Trainer arguments differ from runtime/logging evidence"
        )
    gradients = _validate_gradients(dict(finite_gradient_audit), expected)
    update = _validate_adapter_update(dict(adapter_update), gradients=gradients)
    if (
        gradients.get("custom_gradient_clip_max_norm")
        != reviewed_arguments.get("custom_gradient_clip_max_norm")
    ):
        raise TrainingEvidenceError(
            "gradient audit and Trainer arguments bind different clipping"
        )
    top_metrics, train, evaluation = _validate_top_level_metrics(
        dict(top_level_metrics), optimizer_steps=expected
    )
    records = _normalized_trainer_history(
        log_history,
        optimizer_steps=expected,
        logging_steps=logging_steps,
        train_metrics=train,
        evaluation_metrics=evaluation,
    )
    evidence: dict[str, object] = {
        "format": TRAINING_EVIDENCE_FORMAT,
        "v": TRAINING_EVIDENCE_VERSION,
        "status": "completed",
        "steps": {
            "expected_optimizer_steps": expected,
            "top_level_actual_optimizer_steps": actual,
            "train_result_global_step": result_step,
            "trainer_state_global_step": state_step,
            "trainer_state_max_steps": maximum,
        },
        "runtime": runtime,
        "trainer_arguments": reviewed_arguments,
        "gradients": gradients,
        "adapter_update": update,
        "logging": {
            "format": OPTIMIZER_LOG_FORMAT,
            "v": OPTIMIZER_LOG_VERSION,
            "logging_steps": _positive_int(
                logging_steps, "configured logging steps"
            ),
            "records": records,
            "records_sha256": sha256_json(records),
            "records_hash_payload_format": OPTIMIZER_LOG_HASH_PAYLOAD_FORMAT,
        },
        "metrics": {
            "train": train,
            "eval": evaluation,
            "training_loss_semantics": TRAINING_LOSS_SEMANTICS,
            "evaluation_loss_semantics": EVALUATION_LOSS_SEMANTICS,
            "records_sha256": sha256_json(
                {"train": train, "eval": evaluation}
            ),
            "records_hash_payload_format": METRICS_HASH_PAYLOAD_FORMAT,
            "top_level_metrics_sha256": sha256_json(top_metrics),
        },
        "artifacts": {
            "adapter_sha256": _sha256(adapter_sha256, "adapter artifact hash"),
            "tokenizer_sha256": _sha256(
                tokenizer_sha256, "tokenizer artifact hash"
            ),
        },
        "hash_contract": {
            "algorithm": HASH_ALGORITHM,
            "canonicalization": HASH_CANONICALIZATION,
        },
    }
    evidence["content_sha256"] = sha256_json(evidence)
    return evidence


def validate_completed_training_evidence(
    manifest: object,
) -> dict[str, object]:
    """Return canonical evidence or reject a partial/forged v3 checkpoint."""

    if type(manifest) is not dict or manifest.get("prompt_version") != PEANO_PROMPT_V3:
        raise TrainingEvidenceError(
            "completed-training evidence applies only to an exact model-v3 manifest"
        )
    evidence = _mapping(
        manifest.get("training_evidence"), _ROOT_KEYS, "completed-training evidence"
    )
    if (
        evidence.get("format") != TRAINING_EVIDENCE_FORMAT
        or type(evidence.get("v")) is not int
        or evidence.get("v") != TRAINING_EVIDENCE_VERSION
        or evidence.get("status") != "completed"
    ):
        raise TrainingEvidenceError(
            "model-v3 training evidence is not an exact completed record"
        )
    if evidence.get("hash_contract") != {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
    }:
        raise TrainingEvidenceError("completed-training hash contract is unsupported")
    unsigned = dict(evidence)
    claimed_content_hash = unsigned.pop("content_sha256")
    try:
        actual_content_hash = sha256_json(unsigned)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TrainingEvidenceError(
            f"completed-training evidence is not canonical finite JSON: {exc}"
        ) from None
    if claimed_content_hash != actual_content_hash:
        raise TrainingEvidenceError("completed-training evidence hash is stale or forged")
    _sha256(claimed_content_hash, "completed-training evidence hash")

    steps = _mapping(evidence.get("steps"), _STEP_KEYS, "optimizer-step evidence")
    step_values = tuple(
        _positive_int(steps.get(key), key.replace("_", " "))
        for key in (
            "expected_optimizer_steps",
            "top_level_actual_optimizer_steps",
            "train_result_global_step",
            "trainer_state_global_step",
            "trainer_state_max_steps",
        )
    )
    if len(set(step_values)) != 1:
        raise TrainingEvidenceError(
            "expected, actual, train-result, state, and maximum optimizer steps "
            "must agree"
        )
    optimizer_steps = step_values[0]

    runtime = _validate_runtime(evidence.get("runtime"))
    reviewed_arguments = _validate_trainer_arguments(
        evidence.get("trainer_arguments")
    )
    top_runtime = manifest.get("runtime")
    if (
        type(top_runtime) is not dict
        or top_runtime.get("trainer") != runtime
        or top_runtime.get("trainer_arguments") != reviewed_arguments
    ):
        raise TrainingEvidenceError(
            "completed evidence differs from the manifest Trainer runtime/arguments"
        )
    if reviewed_arguments.get(
        "gradient_accumulation_steps"
    ) != runtime.get("configured_trainer_gradient_accumulation_steps"):
        raise TrainingEvidenceError(
            "observed Trainer accumulation differs from runtime evidence"
        )
    gradients = _validate_gradients(evidence.get("gradients"), optimizer_steps)
    update = _validate_adapter_update(
        evidence.get("adapter_update"), gradients=gradients
    )
    if (
        gradients.get("custom_gradient_clip_max_norm")
        != reviewed_arguments.get("custom_gradient_clip_max_norm")
    ):
        raise TrainingEvidenceError(
            "gradient audit and Trainer arguments bind different clipping"
        )
    top_metrics, train, evaluation = _validate_top_level_metrics(
        manifest.get("metrics"), optimizer_steps=optimizer_steps
    )
    logging = _validate_logging(
        evidence.get("logging"),
        optimizer_steps,
        train_metrics=train,
        evaluation_metrics=evaluation,
    )
    if reviewed_arguments.get("logging_steps") != logging.get("logging_steps"):
        raise TrainingEvidenceError(
            "observed Trainer logging interval differs from logging evidence"
        )
    metrics = _mapping(evidence.get("metrics"), _METRIC_KEYS, "metrics evidence")
    if (
        metrics.get("train") != train
        or metrics.get("eval") != evaluation
        or metrics.get("training_loss_semantics")
        != TRAINING_LOSS_SEMANTICS
        or metrics.get("evaluation_loss_semantics")
        != EVALUATION_LOSS_SEMANTICS
        or metrics.get("records_sha256")
        != sha256_json({"train": train, "eval": evaluation})
        or metrics.get("records_hash_payload_format")
        != METRICS_HASH_PAYLOAD_FORMAT
        or metrics.get("top_level_metrics_sha256") != sha256_json(top_metrics)
    ):
        raise TrainingEvidenceError(
            "completed evidence differs from finite top-level train/eval metrics"
        )

    artifacts = _mapping(
        evidence.get("artifacts"), _ARTIFACT_KEYS, "artifact evidence"
    )
    adapter_hash = _sha256(
        artifacts.get("adapter_sha256"), "evidence adapter artifact hash"
    )
    tokenizer_hash = _sha256(
        artifacts.get("tokenizer_sha256"), "evidence tokenizer artifact hash"
    )
    manifest_adapter_hash, manifest_tokenizer_hash = _artifact_hashes(manifest)
    if manifest_adapter_hash is not None and manifest_adapter_hash != adapter_hash:
        raise TrainingEvidenceError(
            "completed evidence differs from the manifest adapter hash"
        )
    if manifest_tokenizer_hash is not None and manifest_tokenizer_hash != tokenizer_hash:
        raise TrainingEvidenceError(
            "completed evidence differs from the manifest tokenizer hash"
        )

    # A present audited schedule is another independent statement of the exact
    # optimizer count.  Older manifests may not have this optional preflight.
    inputs = manifest.get("inputs")
    schedule = inputs.get("schedule_preflight") if type(inputs) is dict else None
    if schedule is not None and (
        type(schedule) is not dict
        or type(schedule.get("expected_optimizer_steps")) is not int
        or schedule.get("expected_optimizer_steps") != optimizer_steps
    ):
        raise TrainingEvidenceError(
            "completed evidence differs from the audited optimizer schedule"
        )

    return {
        "format": TRAINING_EVIDENCE_FORMAT,
        "v": TRAINING_EVIDENCE_VERSION,
        "status": "completed",
        "steps": dict(steps),
        "runtime": runtime,
        "trainer_arguments": reviewed_arguments,
        "gradients": gradients,
        "adapter_update": update,
        "logging": logging,
        "metrics": dict(metrics),
        "artifacts": dict(artifacts),
        "hash_contract": dict(evidence["hash_contract"]),
        "content_sha256": claimed_content_hash,
    }


def require_completed_training_evidence_for_prompt(
    manifest: object,
) -> dict[str, object] | None:
    """Gate only model-v3; preserve legacy v1/v2 adapter admission."""

    if type(manifest) is dict and manifest.get("prompt_version") == PEANO_PROMPT_V3:
        return validate_completed_training_evidence(manifest)
    return None


__all__ = [
    "ADAPTER_UPDATE_FORMAT",
    "ADAPTER_UPDATE_VERSION",
    "FINITE_GRADIENT_AUDIT_FORMAT",
    "FINITE_GRADIENT_AUDIT_VERSION",
    "FiniteGradientAudit",
    "CUSTOM_GRADIENT_CLIP_MAX_NORM",
    "GRADIENT_NORMS_HASH_PAYLOAD_FORMAT",
    "HASH_ALGORITHM",
    "HASH_CANONICALIZATION",
    "EVALUATION_LOSS_SEMANTICS",
    "OPTIMIZER_LOG_FORMAT",
    "OPTIMIZER_LOG_HASH_PAYLOAD_FORMAT",
    "OPTIMIZER_LOG_VERSION",
    "OPTIMIZER_STEPS_HASH_PAYLOAD_FORMAT",
    "PARAMETER_NAMES_HASH_PAYLOAD_FORMAT",
    "TRAINER_ARGUMENTS_FORMAT",
    "TRAINER_ARGUMENTS_VERSION",
    "TRAINING_LOSS_SEMANTICS",
    "TENSOR_POPULATION_FINGERPRINT_FORMAT",
    "TRAINING_EVIDENCE_FORMAT",
    "TRAINING_EVIDENCE_VERSION",
    "TrainingEvidenceError",
    "adapter_update_audit_record",
    "completed_training_evidence_record",
    "read_strict_training_manifest",
    "require_completed_training_evidence_for_prompt",
    "reviewed_trainer_arguments_record",
    "validate_completed_training_evidence",
]
