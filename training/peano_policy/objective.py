"""Exact completion-only causal-LM loss with indexed logit projection.

The dataset masks prompt tokens with ``IGNORE_INDEX`` and supervises one
contiguous completion suffix (including EOS).  A causal model logit at position
``i`` predicts the label at position ``i + 1``.  Consequently, we can ask a
supporting model to materialize only the union of positions that predict a
supervised token, without changing either the loss or its gradients.

This module deliberately imports no training framework at import time.  The
small Trainer mixin below is combined with the pinned Transformers ``Trainer``
inside :mod:`training.peano_policy.train`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import inspect
from typing import Any

from .data import IGNORE_INDEX


OBJECTIVE_FORMAT = "peano-completion-only-indexed-logits"
OBJECTIVE_VERSION = 1
TRAINER_RUNTIME_FORMAT = "peano-completion-only-trainer-runtime"
TRAINER_RUNTIME_VERSION = 1


class CompletionObjectiveError(ValueError):
    """The batch or model cannot implement the pinned training objective."""


def single_process_trainer_runtime_record(
    trainer: object,
    *,
    expected_gradient_accumulation_steps: int,
) -> dict[str, object]:
    """Fail closed around Trainer/Accelerator's exact single-GPU contract.

    Transformers 4.53.3 manually chunks its dataloader into accumulation
    windows and calls ``Accelerator.backward`` for each microbatch.  Our loss
    is already divided by the whole window's supervised-token count, so an
    Accelerator gradient-accumulation divisor other than one would silently
    scale it a second time.  Environment-selected distributed plugins are
    likewise outside the reviewed one-process objective.
    """

    if (
        type(expected_gradient_accumulation_steps) is not int
        or expected_gradient_accumulation_steps < 1
    ):
        raise CompletionObjectiveError(
            "expected Trainer gradient accumulation must be a positive integer"
        )
    args = getattr(trainer, "args", None)
    accelerator = getattr(trainer, "accelerator", None)
    if args is None or accelerator is None:
        raise CompletionObjectiveError("Trainer runtime is not initialized")
    configured_steps = getattr(args, "gradient_accumulation_steps", None)
    backward_divisor = getattr(accelerator, "gradient_accumulation_steps", None)
    num_processes = getattr(accelerator, "num_processes", None)
    visible_gpus = getattr(args, "n_gpu", None)
    distributed_type = getattr(accelerator, "distributed_type", None)
    distributed_name = getattr(distributed_type, "name", None)
    distributed_value = getattr(distributed_type, "value", None)
    accelerator_device = getattr(accelerator, "device", None)
    trainer_device = getattr(args, "device", None)
    mixed_precision = getattr(accelerator, "mixed_precision", None)
    accelerator_state = getattr(accelerator, "state", None)
    dynamo_plugin = getattr(accelerator_state, "dynamo_plugin", None)
    dynamo_backend = getattr(dynamo_plugin, "backend", None)
    dynamo_name = getattr(dynamo_backend, "name", None)
    dynamo_value = getattr(dynamo_backend, "value", None)
    plugins = {
        "deepspeed": getattr(trainer, "is_deepspeed_enabled", None),
        "fsdp": getattr(trainer, "is_fsdp_enabled", None),
        "tensor_parallel": getattr(trainer, "is_tp_enabled", None),
    }
    if (
        type(configured_steps) is not int
        or configured_steps != expected_gradient_accumulation_steps
    ):
        raise CompletionObjectiveError(
            "Trainer gradient accumulation differs from the reviewed configuration"
        )
    if type(backward_divisor) is not int or backward_divisor != 1:
        raise CompletionObjectiveError(
            "Accelerator.backward must not divide the manually accumulated loss"
        )
    if (
        type(num_processes) is not int
        or num_processes != 1
        or type(visible_gpus) is not int
        or visible_gpus != 1
    ):
        raise CompletionObjectiveError(
            "completion training requires exactly one process and one visible GPU"
        )
    if distributed_name != "NO" or distributed_value != "NO":
        raise CompletionObjectiveError(
            "completion training requires Accelerate DistributedType.NO"
        )
    normalized_device_indices: list[int] = []
    for label, device in (
        ("Trainer", trainer_device),
        ("Accelerator", accelerator_device),
    ):
        if getattr(device, "type", None) != "cuda":
            raise CompletionObjectiveError(
                f"{label} device must be CUDA for completion training"
            )
        index = getattr(device, "index", None)
        if index is None:
            index = 0
        if type(index) is not int or index != 0:
            raise CompletionObjectiveError(
                f"{label} CUDA device index must resolve to zero"
            )
        normalized_device_indices.append(index)
    if normalized_device_indices[0] != normalized_device_indices[1]:
        raise CompletionObjectiveError(
            "Trainer and Accelerator CUDA devices do not agree"
        )
    if mixed_precision != "bf16":
        raise CompletionObjectiveError(
            "Accelerator mixed precision must be bf16"
        )
    try:
        from accelerate.utils import DynamoBackend
    except ImportError:
        # Lightweight unit tests deliberately run without the heavy training
        # stack.  Production reaches this helper only after Trainer has already
        # imported Accelerate, where the identity check below is mandatory.
        if (
            type(dynamo_backend).__name__ != "DynamoBackend"
            or dynamo_name != "NO"
            or dynamo_value != "NO"
        ):
            raise CompletionObjectiveError(
                "Accelerator Dynamo backend must be DynamoBackend.NO"
            )
    else:
        if dynamo_backend is not DynamoBackend.NO:
            raise CompletionObjectiveError(
                "Accelerator Dynamo backend must be DynamoBackend.NO"
            )
    if any(value is not False for value in plugins.values()):
        raise CompletionObjectiveError(
            "completion training forbids DeepSpeed, FSDP, and tensor parallelism"
        )
    return {
        "format": TRAINER_RUNTIME_FORMAT,
        "v": TRAINER_RUNTIME_VERSION,
        "num_processes": 1,
        "visible_gpus": 1,
        "device": {"type": "cuda", "index": 0},
        "mixed_precision": "bf16",
        "distributed_type": {"name": "NO", "value": "NO"},
        "dynamo_backend": {"name": "NO", "value": "NO"},
        "plugins": plugins,
        "manual_trainer_accumulation": True,
        "configured_trainer_gradient_accumulation_steps": configured_steps,
        "accelerator_backward_divisor": 1,
    }


@dataclass(frozen=True, slots=True)
class CompletionProjection:
    """The minimal logit positions and their aligned next-token targets."""

    positions: Any
    targets: Any
    supervised_tokens: Any


def completion_objective_record() -> dict[str, object]:
    """Return the canonical identity embedded in run and artifact manifests."""

    return {
        "format": OBJECTIVE_FORMAT,
        "v": OBJECTIVE_VERSION,
        "task": "causal-next-token-completion-sft",
        "supervision": "contiguous-completion-suffix-including-eos",
        "ignore_index": IGNORE_INDEX,
        "causal_shift": 1,
        "projection": {
            "model_argument": "logits_to_keep",
            "positions": "union-of-nonignored-shifted-label-positions",
        },
        "loss": {
            "function": "cross_entropy",
            "logits_dtype": "float32",
            "reduction": "summed-token-loss/num-items-in-batch",
        },
    }


def require_indexed_logits_support(model: object) -> None:
    """Fail closed unless ``forward`` explicitly accepts ``logits_to_keep``.

    Merely accepting arbitrary ``**kwargs`` is not enough: a model could ignore
    the projection request and silently materialize full-sequence logits.
    """

    forward = getattr(model, "forward", None)
    if not callable(forward):
        raise CompletionObjectiveError("model has no callable forward method")
    try:
        parameter = inspect.signature(forward).parameters.get("logits_to_keep")
    except (TypeError, ValueError) as exc:
        raise CompletionObjectiveError(
            "cannot verify model support for indexed logits"
        ) from exc
    if parameter is None or parameter.kind not in {
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    }:
        raise CompletionObjectiveError(
            "model.forward must explicitly accept the logits_to_keep keyword"
        )


def _truth(value: Any) -> bool:
    """Convert a scalar tensor predicate to bool at a validation boundary."""

    return bool(value.detach().item())


def _validate_completion_suffix(labels: Any, attention_mask: Any) -> None:
    """Check the exact right-padded ``prompt + completion`` batch contract."""

    import torch

    if not torch.is_tensor(labels) or not torch.is_tensor(attention_mask):
        raise CompletionObjectiveError("labels and attention_mask must be tensors")
    if labels.ndim != 2 or attention_mask.ndim != 2:
        raise CompletionObjectiveError("labels and attention_mask must be rank 2")
    if labels.shape != attention_mask.shape:
        raise CompletionObjectiveError("labels and attention_mask shapes differ")
    if labels.shape[0] == 0 or labels.shape[1] < 2:
        raise CompletionObjectiveError("each batch row needs prompt and completion tokens")
    if labels.dtype != torch.long:
        raise CompletionObjectiveError("labels must have torch.long dtype")
    if labels.device != attention_mask.device:
        raise CompletionObjectiveError("labels and attention_mask must share a device")
    if not _truth((attention_mask.eq(0) | attention_mask.eq(1)).all()):
        raise CompletionObjectiveError("attention_mask must contain only 0 or 1")

    active = attention_mask.eq(1)
    if not _truth(active[:, 0].all()):
        raise CompletionObjectiveError("only right padding is supported")
    seen_padding = active.logical_not().cumsum(dim=1).gt(0)
    if _truth((active & seen_padding).any()):
        raise CompletionObjectiveError("attention_mask is not right padded")

    supervised = labels.ne(IGNORE_INDEX)
    if _truth((supervised & active.logical_not()).any()):
        raise CompletionObjectiveError("padding positions must use IGNORE_INDEX")
    if _truth(supervised[:, 0].any()):
        raise CompletionObjectiveError("each row must contain a masked prompt token")
    if not _truth(supervised.any(dim=1).all()):
        raise CompletionObjectiveError("each row needs a supervised completion suffix")
    seen_supervision = supervised.cumsum(dim=1).gt(0)
    if _truth((active & seen_supervision & supervised.logical_not()).any()):
        raise CompletionObjectiveError(
            "supervised labels must be one contiguous suffix of attended tokens"
        )
    if _truth(labels[supervised].lt(0).any()):
        raise CompletionObjectiveError(
            "supervised labels must be non-negative token ids"
        )


def completion_projection(labels: Any, attention_mask: Any) -> CompletionProjection:
    """Build exact indexed-logit positions after the one-token causal shift.

    The returned position tensor indexes the model's sequence dimension.  The
    target tensor has the same batch/position dimensions as the logits the
    model must return; cells unused by a shorter row retain ``IGNORE_INDEX``.
    """

    _validate_completion_suffix(labels, attention_mask)
    shifted_targets = labels[:, 1:].contiguous()
    positions = (
        shifted_targets.ne(IGNORE_INDEX)
        .any(dim=0)
        .nonzero(as_tuple=False)
        .flatten()
    )
    targets = shifted_targets.index_select(1, positions).contiguous()
    supervised_tokens = targets.ne(IGNORE_INDEX).sum()
    if positions.numel() == 0 or not _truth(supervised_tokens.gt(0)):
        raise CompletionObjectiveError("batch has no supervised causal targets")
    return CompletionProjection(positions, targets, supervised_tokens)


def indexed_completion_cross_entropy(
    logits: Any,
    projection: CompletionProjection,
    *,
    num_items_in_batch: Any | None = None,
) -> Any:
    """Compute the pinned FP32 token loss from projected logits.

    ``num_items_in_batch`` is the total number of supervised tokens across the
    current gradient-accumulation window when supplied by Transformers.  Thus
    summing the independently backpropagated microbatch losses produces the
    same gradient as one concatenated batch with token-mean reduction.
    """

    import torch
    import torch.nn.functional as functional

    if not torch.is_tensor(logits) or logits.ndim != 3:
        raise CompletionObjectiveError("projected logits must be a rank-3 tensor")
    targets = projection.targets
    if not torch.is_tensor(targets) or tuple(logits.shape[:2]) != tuple(targets.shape):
        raise CompletionObjectiveError("projected logits and targets shapes differ")
    if logits.shape[2] <= 0:
        raise CompletionObjectiveError("projected logits have an empty vocabulary")

    targets = targets.to(device=logits.device)
    supervised = targets.ne(IGNORE_INDEX)
    if not _truth(supervised.any()):
        raise CompletionObjectiveError("projected targets contain no supervision")
    if _truth(targets[supervised].lt(0).any()) or _truth(
        targets[supervised].ge(logits.shape[2]).any()
    ):
        raise CompletionObjectiveError("supervised token id is outside the vocabulary")

    numerator = functional.cross_entropy(
        logits.float().reshape(-1, logits.shape[2]),
        targets.reshape(-1),
        ignore_index=IGNORE_INDEX,
        reduction="sum",
    )
    local_items = supervised.sum()
    if num_items_in_batch is None:
        denominator = local_items
    elif torch.is_tensor(num_items_in_batch):
        if num_items_in_batch.numel() != 1:
            raise CompletionObjectiveError("num_items_in_batch must be scalar")
        denominator = num_items_in_batch.to(device=logits.device).reshape(())
    else:
        if type(num_items_in_batch) not in {int, float}:
            raise CompletionObjectiveError("num_items_in_batch must be numeric")
        denominator = torch.tensor(num_items_in_batch, device=logits.device)
    denominator = denominator.to(dtype=numerator.dtype)
    if not _truth(torch.isfinite(denominator)) or not _truth(denominator.gt(0)):
        raise CompletionObjectiveError("num_items_in_batch must be finite and positive")
    if _truth(denominator.lt(local_items.to(denominator.device))):
        raise CompletionObjectiveError(
            "num_items_in_batch is smaller than this microbatch's supervision"
        )
    return numerator / denominator


class CompletionOnlyTrainerMixin:
    """Transformers Trainer override for the exact indexed-logit objective."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if (
            getattr(self.args, "n_gpu", 1) > 1
            and getattr(self.accelerator, "num_processes", 1) == 1
        ):
            raise CompletionObjectiveError(
                "torch.nn.DataParallel is unsupported for indexed logit positions"
            )
        # In Transformers 4.53 this flag also asks Trainer to count non-ignored
        # labels across an entire gradient-accumulation window.  compute_loss
        # consumes that count itself and never forwards it to the model.
        self.model_accepts_loss_kwargs = True

    def compute_loss(
        self,
        model: Any,
        inputs: Mapping[str, Any],
        return_outputs: bool = False,
        num_items_in_batch: Any | None = None,
    ) -> Any:
        if (
            getattr(model, "training", False) is True
            and num_items_in_batch is None
        ):
            raise CompletionObjectiveError(
                "completion training requires num_items_in_batch from Trainer"
            )
        if "labels" not in inputs or "attention_mask" not in inputs:
            raise CompletionObjectiveError(
                "completion objective requires labels and attention_mask"
            )
        if "logits_to_keep" in inputs:
            raise CompletionObjectiveError(
                "logits_to_keep is owned by the completion objective"
            )
        projection = completion_projection(inputs["labels"], inputs["attention_mask"])
        model_inputs = {key: value for key, value in inputs.items() if key != "labels"}
        outputs = model(**model_inputs, logits_to_keep=projection.positions)
        logits = (
            outputs.get("logits")
            if isinstance(outputs, Mapping)
            else getattr(outputs, "logits", None)
        )
        if logits is None:
            raise CompletionObjectiveError("model did not return projected logits")
        loss = indexed_completion_cross_entropy(
            logits,
            projection,
            num_items_in_batch=num_items_in_batch,
        )
        if (
            getattr(self.args, "average_tokens_across_devices", False)
            and num_items_in_batch is not None
        ):
            loss = loss * self.accelerator.num_processes
        return (loss, outputs) if return_outputs else loss
