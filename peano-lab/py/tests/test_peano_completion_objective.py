"""Focused equivalence and fail-closed tests for the Peano SFT objective."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


torch = pytest.importorskip("torch")
functional = pytest.importorskip("torch.nn.functional")


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.peano_policy.data import IGNORE_INDEX
from training.peano_policy.objective import (
    OBJECTIVE_FORMAT,
    CompletionObjectiveError,
    CompletionOnlyTrainerMixin,
    completion_objective_record,
    completion_projection,
    indexed_completion_cross_entropy,
    require_indexed_logits_support,
    single_process_trainer_runtime_record,
)
import training.peano_policy.train as training_run


def _full_completion_loss(
    hidden: torch.Tensor,
    weight: torch.Tensor,
    labels: torch.Tensor,
    *,
    denominator: int | None = None,
) -> torch.Tensor:
    """Reference full-sequence causal loss, independent of objective.py."""

    logits = hidden @ weight.transpose(0, 1)
    targets = labels[:, 1:].contiguous()
    numerator = functional.cross_entropy(
        logits[:, :-1, :].float().reshape(-1, logits.shape[-1]),
        targets.reshape(-1),
        ignore_index=IGNORE_INDEX,
        reduction="sum",
    )
    items = targets.ne(IGNORE_INDEX).sum() if denominator is None else denominator
    return numerator / items


def _indexed_completion_loss(
    hidden: torch.Tensor,
    weight: torch.Tensor,
    labels: torch.Tensor,
    attention_mask: torch.Tensor,
    *,
    denominator: int | None = None,
) -> torch.Tensor:
    projection = completion_projection(labels, attention_mask)
    selected = hidden.index_select(1, projection.positions)
    logits = selected @ weight.transpose(0, 1)
    return indexed_completion_cross_entropy(
        logits,
        projection,
        num_items_in_batch=denominator,
    )


def test_objective_identity_is_canonical_and_fresh() -> None:
    first = completion_objective_record()
    second = completion_objective_record()
    assert first == second
    assert first is not second
    assert first == {
        "format": OBJECTIVE_FORMAT,
        "v": 1,
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
    first["projection"]["positions"] = "mutated"  # type: ignore[index]
    assert completion_objective_record() == second


def test_projection_applies_the_causal_shift_in_the_correct_direction() -> None:
    labels = torch.tensor(
        [[IGNORE_INDEX, IGNORE_INDEX, 10, 11, 12]], dtype=torch.long
    )
    attention_mask = torch.ones_like(labels)
    projection = completion_projection(labels, attention_mask)

    # Logit 1 predicts label 2 (the first completion token).  Keeping 2, 3, 4
    # would be the classic off-by-one error and would even include a useless
    # final logit with no next-token target.
    assert projection.positions.tolist() == [1, 2, 3]
    assert projection.targets.tolist() == [[10, 11, 12]]
    assert projection.supervised_tokens.item() == 3


def test_projection_unions_noncontiguous_positions_in_a_right_padded_batch() -> None:
    labels = torch.tensor(
        [
            [
                IGNORE_INDEX, IGNORE_INDEX, 5, 6,
                IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX,
            ],
            [
                IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX,
                IGNORE_INDEX, IGNORE_INDEX, 7, 8,
            ],
        ],
        dtype=torch.long,
    )
    attention_mask = torch.tensor(
        [
            [1, 1, 1, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ],
        dtype=torch.long,
    )
    projection = completion_projection(labels, attention_mask)

    assert projection.positions.tolist() == [1, 2, 5, 6]
    assert projection.targets.tolist() == [
        [5, 6, IGNORE_INDEX, IGNORE_INDEX],
        [IGNORE_INDEX, IGNORE_INDEX, 7, 8],
    ]
    assert projection.supervised_tokens.item() == 4


@pytest.mark.parametrize(
    ("labels", "attention_mask"),
    [
        ([3, 4], [1, 1]),
        ([IGNORE_INDEX, IGNORE_INDEX], [1, 1]),
        ([IGNORE_INDEX, 3, IGNORE_INDEX, 4], [1, 1, 1, 1]),
        ([IGNORE_INDEX, 3, 4], [1, 1, 0]),
        ([IGNORE_INDEX, IGNORE_INDEX, 4], [1, 0, 1]),
        ([IGNORE_INDEX, -5], [1, 1]),
    ],
)
def test_projection_rejects_malformed_completion_suffixes(
    labels: list[int], attention_mask: list[int]
) -> None:
    with pytest.raises(CompletionObjectiveError):
        completion_projection(
            torch.tensor([labels], dtype=torch.long),
            torch.tensor([attention_mask], dtype=torch.long),
        )


def test_projection_rejects_shape_and_dtype_mismatches() -> None:
    with pytest.raises(CompletionObjectiveError, match="shapes differ"):
        completion_projection(
            torch.tensor([[IGNORE_INDEX, 2]], dtype=torch.long),
            torch.tensor([[1, 1, 0]], dtype=torch.long),
        )
    with pytest.raises(CompletionObjectiveError, match="torch.long"):
        completion_projection(
            torch.tensor([[IGNORE_INDEX, 2]], dtype=torch.int32),
            torch.tensor([[1, 1]], dtype=torch.long),
        )


def test_indexed_loss_and_gradients_equal_full_sequence_reference() -> None:
    torch.manual_seed(19)
    labels = torch.tensor(
        [
            [IGNORE_INDEX, IGNORE_INDEX, 2, 4, IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX],
            [IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX, 1, 3, 5],
        ],
        dtype=torch.long,
    )
    attention_mask = torch.tensor(
        [[1, 1, 1, 1, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1]],
        dtype=torch.long,
    )
    base_hidden = torch.randn(2, 7, 9)
    base_weight = torch.randn(11, 9)
    full_hidden = base_hidden.clone().requires_grad_()
    full_weight = base_weight.clone().requires_grad_()
    indexed_hidden = base_hidden.clone().requires_grad_()
    indexed_weight = base_weight.clone().requires_grad_()

    full_loss = _full_completion_loss(full_hidden, full_weight, labels)
    indexed_loss = _indexed_completion_loss(
        indexed_hidden, indexed_weight, labels, attention_mask
    )
    full_loss.backward()
    indexed_loss.backward()

    torch.testing.assert_close(indexed_loss, full_loss, rtol=1e-6, atol=1e-7)
    torch.testing.assert_close(
        indexed_hidden.grad, full_hidden.grad, rtol=1e-6, atol=1e-7
    )
    torch.testing.assert_close(
        indexed_weight.grad, full_weight.grad, rtol=1e-6, atol=1e-7
    )
    assert indexed_loss.dtype == torch.float32


def test_unequal_microbatches_use_one_accumulation_window_denominator() -> None:
    torch.manual_seed(23)
    label_batches = [
        torch.tensor([[IGNORE_INDEX, IGNORE_INDEX, 2]], dtype=torch.long),
        torch.tensor(
            [[IGNORE_INDEX, 1, 3, 4, 5], [IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX, 6, 7]],
            dtype=torch.long,
        ),
    ]
    mask_batches = [torch.ones_like(labels) for labels in label_batches]
    base_hidden = [torch.randn(*labels.shape, 8) for labels in label_batches]
    base_weight = torch.randn(10, 8)
    full_hidden = [value.clone().requires_grad_() for value in base_hidden]
    indexed_hidden = [value.clone().requires_grad_() for value in base_hidden]
    full_weight = base_weight.clone().requires_grad_()
    indexed_weight = base_weight.clone().requires_grad_()
    total_items = sum(
        labels[:, 1:].ne(IGNORE_INDEX).sum().item() for labels in label_batches
    )
    assert total_items == 7

    full_losses = [
        _full_completion_loss(
            hidden,
            full_weight,
            labels,
            denominator=total_items,
        )
        for hidden, labels in zip(full_hidden, label_batches, strict=True)
    ]
    indexed_losses = [
        _indexed_completion_loss(
            hidden,
            indexed_weight,
            labels,
            mask,
            denominator=total_items,
        )
        for hidden, labels, mask in zip(
            indexed_hidden, label_batches, mask_batches, strict=True
        )
    ]
    for loss in full_losses:
        loss.backward()
    for loss in indexed_losses:
        loss.backward()

    torch.testing.assert_close(
        sum(indexed_losses), sum(full_losses), rtol=1e-6, atol=1e-7
    )
    torch.testing.assert_close(
        indexed_weight.grad, full_weight.grad, rtol=1e-6, atol=1e-7
    )
    for actual, expected in zip(indexed_hidden, full_hidden, strict=True):
        torch.testing.assert_close(
            actual.grad, expected.grad, rtol=1e-6, atol=1e-7
        )


def test_model_support_check_requires_an_explicit_keyword() -> None:
    class Supported:
        def forward(self, input_ids: object, logits_to_keep: object = 0) -> None:
            pass

    class KwargsOnly:
        def forward(self, input_ids: object, **kwargs: object) -> None:
            pass

    class PositionalOnly:
        def forward(self, logits_to_keep: object, /) -> None:
            pass

    require_indexed_logits_support(Supported())
    for model in (KwargsOnly(), PositionalOnly(), object()):
        with pytest.raises(CompletionObjectiveError):
            require_indexed_logits_support(model)


def test_trainer_mixin_owns_projection_and_does_not_forward_labels() -> None:
    class BaseTrainer:
        def __init__(self) -> None:
            self.args = SimpleNamespace(average_tokens_across_devices=False)
            self.accelerator = SimpleNamespace(num_processes=1)
            self.model_accepts_loss_kwargs = False

    class CompletionTrainer(CompletionOnlyTrainerMixin, BaseTrainer):
        pass

    class IndexedModel:
        def __init__(self, weight: torch.Tensor) -> None:
            self.weight = weight
            self.positions: list[int] | None = None

        def __call__(
            self,
            *,
            features: torch.Tensor,
            attention_mask: torch.Tensor,
            logits_to_keep: torch.Tensor,
        ) -> dict[str, torch.Tensor]:
            assert attention_mask.ndim == 2
            self.positions = logits_to_keep.tolist()
            selected = features.index_select(1, logits_to_keep)
            return {"logits": selected @ self.weight.transpose(0, 1)}

    torch.manual_seed(29)
    trainer = CompletionTrainer()
    assert trainer.model_accepts_loss_kwargs is True
    labels = torch.tensor(
        [[IGNORE_INDEX, IGNORE_INDEX, 2, 3]], dtype=torch.long
    )
    attention_mask = torch.ones_like(labels)
    features = torch.randn(1, 4, 6)
    weight = torch.randn(7, 6)
    model = IndexedModel(weight)
    loss, outputs = trainer.compute_loss(
        model,
        {
            "features": features,
            "attention_mask": attention_mask,
            "labels": labels,
        },
        return_outputs=True,
        num_items_in_batch=torch.tensor(2),
    )

    expected = _full_completion_loss(features, weight, labels, denominator=2)
    torch.testing.assert_close(loss, expected, rtol=1e-6, atol=1e-7)
    assert model.positions == [1, 2]
    assert outputs["logits"].shape == (1, 2, 7)


def test_trainer_mixin_requires_window_denominator_only_during_training() -> None:
    class BaseTrainer:
        def __init__(self) -> None:
            self.args = SimpleNamespace(average_tokens_across_devices=False)
            self.accelerator = SimpleNamespace(num_processes=1)

    class CompletionTrainer(CompletionOnlyTrainerMixin, BaseTrainer):
        pass

    class IndexedModel(torch.nn.Module):
        def forward(
            self,
            *,
            features: torch.Tensor,
            attention_mask: torch.Tensor,
            logits_to_keep: torch.Tensor,
        ) -> dict[str, torch.Tensor]:
            del attention_mask
            selected = features.index_select(1, logits_to_keep)
            return {"logits": selected}

    trainer = CompletionTrainer()
    model = IndexedModel()
    inputs = {
        "features": torch.tensor(
            [[[0.1, 0.2, 0.3], [0.3, 0.2, 0.1], [0.2, 0.3, 0.1]]]
        ),
        "attention_mask": torch.ones((1, 3), dtype=torch.long),
        "labels": torch.tensor([[IGNORE_INDEX, 1, 2]], dtype=torch.long),
    }

    model.train()
    with pytest.raises(
        CompletionObjectiveError,
        match="requires num_items_in_batch from Trainer",
    ):
        trainer.compute_loss(model, inputs)

    model.eval()
    loss = trainer.compute_loss(model, inputs)
    assert torch.isfinite(loss)


def test_trainer_mixin_rejects_single_process_data_parallel() -> None:
    class BaseTrainer:
        def __init__(self) -> None:
            self.args = SimpleNamespace(
                average_tokens_across_devices=True,
                n_gpu=2,
            )
            self.accelerator = SimpleNamespace(num_processes=1)

    class CompletionTrainer(CompletionOnlyTrainerMixin, BaseTrainer):
        pass

    with pytest.raises(CompletionObjectiveError, match="DataParallel"):
        CompletionTrainer()


class DynamoBackend(Enum):
    NO = "NO"
    INDUCTOR = "INDUCTOR"


def _single_gpu_trainer_runtime(*, accumulation: int = 32) -> SimpleNamespace:
    return SimpleNamespace(
        args=SimpleNamespace(
            n_gpu=1,
            gradient_accumulation_steps=accumulation,
            device=SimpleNamespace(type="cuda", index=0),
        ),
        accelerator=SimpleNamespace(
            num_processes=1,
            gradient_accumulation_steps=1,
            distributed_type=SimpleNamespace(name="NO", value="NO"),
            device=SimpleNamespace(type="cuda", index=0),
            mixed_precision="bf16",
            state=SimpleNamespace(
                dynamo_plugin=SimpleNamespace(backend=DynamoBackend.NO)
            ),
        ),
        is_deepspeed_enabled=False,
        is_fsdp_enabled=False,
        is_tp_enabled=False,
    )


def test_single_process_trainer_runtime_binds_manual_accumulation() -> None:
    record = single_process_trainer_runtime_record(
        _single_gpu_trainer_runtime(),
        expected_gradient_accumulation_steps=32,
    )

    assert record == {
        "format": "peano-completion-only-trainer-runtime",
        "v": 1,
        "num_processes": 1,
        "visible_gpus": 1,
        "device": {"type": "cuda", "index": 0},
        "mixed_precision": "bf16",
        "distributed_type": {"name": "NO", "value": "NO"},
        "dynamo_backend": {"name": "NO", "value": "NO"},
        "plugins": {
            "deepspeed": False,
            "fsdp": False,
            "tensor_parallel": False,
        },
        "manual_trainer_accumulation": True,
        "configured_trainer_gradient_accumulation_steps": 32,
        "accelerator_backward_divisor": 1,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda trainer: setattr(
                trainer.accelerator, "gradient_accumulation_steps", 32
            ),
            "must not divide",
        ),
        (
            lambda trainer: setattr(trainer.accelerator, "num_processes", 2),
            "exactly one process",
        ),
        (
            lambda trainer: setattr(trainer.args, "n_gpu", 2),
            "exactly one process",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator,
                "distributed_type",
                SimpleNamespace(name="MULTI_GPU", value="MULTI_GPU"),
            ),
            "DistributedType.NO",
        ),
        (
            lambda trainer: setattr(
                trainer.args, "device", SimpleNamespace(type="cpu", index=None)
            ),
            "Trainer device must be CUDA",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator,
                "device",
                SimpleNamespace(type="cpu", index=None),
            ),
            "Accelerator device must be CUDA",
        ),
        (
            lambda trainer: setattr(
                trainer.args,
                "device",
                SimpleNamespace(type="cuda", index=1),
            ),
            "Trainer CUDA device index",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator,
                "device",
                SimpleNamespace(type="cuda", index=1),
            ),
            "Accelerator CUDA device index",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator, "mixed_precision", "fp16"
            ),
            "mixed precision must be bf16",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator, "mixed_precision", "no"
            ),
            "mixed precision must be bf16",
        ),
        (
            lambda trainer: setattr(
                trainer.accelerator.state.dynamo_plugin,
                "backend",
                DynamoBackend.INDUCTOR,
            ),
            "DynamoBackend.NO",
        ),
        (
            lambda trainer: setattr(trainer, "is_deepspeed_enabled", True),
            "forbids DeepSpeed",
        ),
        (
            lambda trainer: setattr(trainer, "is_fsdp_enabled", True),
            "forbids DeepSpeed",
        ),
        (
            lambda trainer: setattr(trainer, "is_tp_enabled", True),
            "forbids DeepSpeed",
        ),
    ],
)
def test_single_process_trainer_runtime_rejects_unreviewed_accelerate_state(
    mutation: object,
    message: str,
) -> None:
    trainer = _single_gpu_trainer_runtime()
    assert callable(mutation)
    mutation(trainer)
    with pytest.raises(CompletionObjectiveError, match=message):
        single_process_trainer_runtime_record(
            trainer,
            expected_gradient_accumulation_steps=32,
        )


def test_single_process_trainer_runtime_rejects_configured_accumulation_drift() -> None:
    with pytest.raises(CompletionObjectiveError, match="reviewed configuration"):
        single_process_trainer_runtime_record(
            _single_gpu_trainer_runtime(accumulation=16),
            expected_gradient_accumulation_steps=32,
        )


def test_train_runner_binds_the_same_objective_to_both_manifests() -> None:
    source = (REPO_ROOT / "training" / "peano_policy" / "train.py").read_text(
        encoding="utf-8"
    )
    assert training_run.RUN_IDENTITY_VERSION == 5
    assert '"objective": completion_objective_record()' in source
    assert '"objective": run_identity["objective"]' in source
    assert "trainer = CompletionOnlyTrainer(" in source
    assert "require_indexed_logits_support(model)" in source
    assert "average_tokens_across_devices=True" in source
    assert "do_train=True" in source
    assert "do_eval=bool(eval_examples)" in source
    assert "bf16_full_eval=False" in source
    assert 'gradient_checkpointing_kwargs={"use_reentrant": False}' in source
    assert "max_grad_norm=(0.0 if schedule_preflight is not None else 1.0)" in source
    assert "adam_beta1=0.9" in source
    assert "adam_beta2=0.999" in source
    assert "adam_epsilon=1e-8" in source
    assert "logging_nan_inf_filter=False" in source
    assert 'eval_strategy="no"' in source
    assert 'save_strategy="no"' in source
    assert 'save_strategy="steps"' not in source
    assert "single_process_trainer_runtime_record(" in source
