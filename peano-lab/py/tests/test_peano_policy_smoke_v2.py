"""Focused CPU tests for fail-closed model-v3 accelerator smoke evidence."""

from __future__ import annotations

from enum import Enum
import inspect
from pathlib import Path
from types import SimpleNamespace
import math
import sys

import pytest


torch = pytest.importorskip("torch")


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy import smoke  # noqa: E402
from training.peano_policy.contract import model_v1_environment  # noqa: E402
from training.peano_policy.manifest import sha256_json  # noqa: E402
from training.peano_policy.prompt import ProofExample, render_prompt  # noqa: E402


class _IdentityTokenizer:
    eos_token_id = 1
    pad_token_id = 1

    def __len__(self) -> int:
        return 17


class _AdmissionTokenizer:
    eos_token_id = 31
    pad_token_id = 31
    padding_side = "right"
    special_tokens_map = {"eos_token": "<eos>", "pad_token": "<eos>"}

    def __len__(self) -> int:
        return 32

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        raw = text.encode("utf-8")
        return {"input_ids": [sum(raw) % 29 + 1, len(raw) % 29 + 1]}


def _schedule_config(
    *,
    epochs: float = 1.0,
    max_steps: int = -1,
    batch_size: int = 1,
    accumulation: int = 32,
    warmup_ratio: float = 0.05,
) -> SimpleNamespace:
    return SimpleNamespace(
        trainer=SimpleNamespace(
            epochs=epochs,
            max_steps=max_steps,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=accumulation,
            warmup_ratio=warmup_ratio,
        )
    )


def test_trainer_schedule_matches_finite_dataloader_ceiling_arithmetic() -> None:
    record = smoke._trainer_schedule(
        _schedule_config(),
        train_rows=20_782,
    )

    assert record == {
        "train_rows": 20_782,
        "dataloader_batches": 20_782,
        "updates_per_epoch": 650,
        "total_steps": 650,
        "warmup_steps": 33,
    }


def test_trainer_schedule_honors_max_steps_and_rejects_no_post_warmup_step() -> None:
    assert smoke._trainer_schedule(
        _schedule_config(max_steps=17, batch_size=4, accumulation=2),
        train_rows=21,
    )["total_steps"] == 17
    with pytest.raises(RuntimeError, match="no post-warmup"):
        smoke._trainer_schedule(
            _schedule_config(max_steps=1, warmup_ratio=1.0),
            train_rows=1,
        )


def test_gradient_gate_requires_every_trainable_parameter() -> None:
    left = torch.nn.Parameter(torch.tensor([3.0, 4.0]))
    right = torch.nn.Parameter(torch.tensor([1.0]))
    left.grad = torch.tensor([3.0, 4.0])

    with pytest.raises(RuntimeError, match="no gradient for 1"):
        smoke._require_and_clip_gradients(
            torch,
            [("left", left), ("right", right)],
        )


def test_gradient_gate_rejects_nonfinite_values_and_clips_like_trainer() -> None:
    parameter = torch.nn.Parameter(torch.tensor([0.0, 0.0]))
    parameter.grad = torch.tensor([float("inf"), 0.0])
    with pytest.raises(RuntimeError, match="non-finite gradient"):
        smoke._require_and_clip_gradients(torch, [("weight", parameter)])

    parameter.grad = torch.tensor([3.0, 4.0])
    record = smoke._require_and_clip_gradients(torch, [("weight", parameter)])
    assert record == {
        "parameters_with_grad": 1,
        "norm_before_clip": 5.0,
        "max_norm": 1.0,
        "clipped": True,
    }
    assert torch.linalg.vector_norm(parameter.grad).item() == pytest.approx(1.0)


def test_finite_gradient_audit_binds_every_trainable_tensor() -> None:
    left = torch.nn.Parameter(torch.tensor([1.0]))
    right = torch.nn.Parameter(torch.tensor([2.0]))
    left.grad = torch.tensor([0.0])
    right.grad = torch.tensor([3.0])

    record = smoke._require_finite_gradients(
        torch,
        [("right", right), ("left", left)],
    )

    assert record["parameters_with_finite_grad"] == 2
    assert isinstance(record["parameter_names_sha256"], str)
    assert len(record["parameter_names_sha256"]) == 64
    right.grad = torch.tensor([float("nan")])
    with pytest.raises(RuntimeError, match="non-finite gradient for 1"):
        smoke._require_finite_gradients(
            torch,
            [("right", right), ("left", left)],
        )


def test_strict_pre_optimizer_clip_records_raw_and_postclip_gradients() -> None:
    parameter = torch.nn.Parameter(torch.tensor([0.0, 0.0]))
    parameter.grad = torch.tensor([3.0, 4.0])

    record = smoke._strict_pre_optimizer_clip_evidence(
        torch, [("weight", parameter)]
    )

    assert record["hook"] == "on_pre_optimizer_step"
    assert record["raw"]["parameters_with_finite_grad"] == 1
    clip = record["custom_pre_optimizer_clip"]
    assert clip["max_norm"] == 1.0
    assert clip["error_if_nonfinite"] is True
    assert clip["norm_before_clip"] == 5.0
    assert clip["clipped"] is True
    assert clip["postclip"] == record["raw"]
    assert torch.linalg.vector_norm(parameter.grad).item() == pytest.approx(1.0)


def test_adapter_change_gate_rejects_noop_and_binds_parameter_population() -> None:
    left = torch.nn.Parameter(torch.tensor([1.0]))
    right = torch.nn.Parameter(torch.tensor([2.0]))
    named = [("left", left), ("right", right)]
    before = smoke._parameter_snapshot(named)

    with pytest.raises(RuntimeError, match="did not change"):
        smoke._changed_parameter_names(torch, before, named)
    right.data.add_(1.0)
    assert smoke._changed_parameter_names(torch, before, named) == ["right"]
    with pytest.raises(RuntimeError, match="population changed"):
        smoke._changed_parameter_names(torch, before, [("left", left)])


def test_projected_logit_fingerprint_binds_shape_dtype_and_every_byte() -> None:
    value = torch.tensor([[[1.0, 2.0], [3.0, 4.0]]], dtype=torch.float32)
    first = smoke._tensor_fingerprint(torch, value)
    assert first == smoke._tensor_fingerprint(torch, value.clone())

    changed = value.clone()
    changed[0, 1, 1] += 1.0
    assert smoke._tensor_fingerprint(torch, changed)["sha256"] != first["sha256"]
    assert smoke._tensor_fingerprint(torch, value.reshape(1, 1, 4))["sha256"] != (
        first["sha256"]
    )
    assert smoke._tensor_fingerprint(torch, value.double())["sha256"] != first["sha256"]


def _completion_batch(
    *, sequence_tokens: int, supervised_tokens: int
) -> dict[str, torch.Tensor]:
    prompt_tokens = sequence_tokens - supervised_tokens
    return {
        "input_ids": torch.arange(sequence_tokens, dtype=torch.long).unsqueeze(0),
        "attention_mask": torch.ones((1, sequence_tokens), dtype=torch.long),
        "labels": torch.tensor(
            [[-100] * prompt_tokens + list(range(supervised_tokens))],
            dtype=torch.long,
        ),
    }


def test_attended_prompt_extension_attains_both_memory_extrema() -> None:
    selections = (
        smoke.SmokeExampleSelection(
            SimpleNamespace(example_id="sequence"), ("longest_sequence",)
        ),
        smoke.SmokeExampleSelection(
            SimpleNamespace(example_id="completion"), ("longest_completion",)
        ),
    )
    natural = [
        _completion_batch(sequence_tokens=8, supervised_tokens=2),
        _completion_batch(sequence_tokens=6, supervised_tokens=3),
    ]
    batches = list(natural)
    probes: list[dict[str, object]] = [
        {
            "id": "sequence",
            "roles": ["longest_sequence"],
            "sequence_tokens": 8,
            "attended_tokens": 8,
            "supervised_tokens": 2,
            "projected_positions": 2,
        },
        {
            "id": "completion",
            "roles": ["longest_completion"],
            "sequence_tokens": 6,
            "attended_tokens": 6,
            "supervised_tokens": 3,
            "projected_positions": 3,
        },
    ]

    envelope_record = smoke._add_combined_memory_envelope(
        torch,
        selections,
        natural,
        batches,
        probes,
        sequence_maximum=8,
        supervision_maximum=3,
        pad_token_id=99,
    )

    assert len(batches) == 2
    assert len(probes) == 2
    assert probes[-1] == {
        "id": "completion",
        "source_example_id": "completion",
        "roles": ["longest_completion", "combined_memory_envelope"],
        "construction": "attended-masked-prompt-extension-to-longest-sequence",
        "inserted_prompt_tokens": 2,
        "sequence_tokens": 8,
        "attended_tokens": 8,
        "supervised_tokens": 3,
        "projected_positions": 3,
    }
    assert envelope_record is probes[-1]
    assert natural[-1]["input_ids"].shape[1] == 6
    envelope = batches[-1]
    assert envelope["input_ids"].tolist()[0] == [0, 1, 2, 99, 99, 3, 4, 5]
    assert envelope["attention_mask"].tolist()[0] == [1] * 8
    assert envelope["labels"].tolist()[0] == [
        -100,
        -100,
        -100,
        -100,
        -100,
        0,
        1,
        2,
    ]
    projection = smoke.completion_projection(
        envelope["labels"], envelope["attention_mask"]
    )
    assert int(projection.supervised_tokens) == 3
    assert projection.positions.numel() == 3


def test_natural_combined_extremum_is_reused_without_duplicate_probe() -> None:
    selections = (
        smoke.SmokeExampleSelection(
            SimpleNamespace(example_id="both"),
            ("longest_sequence", "longest_completion"),
        ),
    )
    natural = [_completion_batch(sequence_tokens=8, supervised_tokens=3)]
    batches = list(natural)
    probes: list[dict[str, object]] = [
        {
            "id": "both",
            "roles": ["longest_sequence", "longest_completion"],
            "sequence_tokens": 8,
            "attended_tokens": 8,
            "supervised_tokens": 3,
            "projected_positions": 3,
        }
    ]

    envelope_record = smoke._add_combined_memory_envelope(
        torch,
        selections,
        natural,
        batches,
        probes,
        sequence_maximum=8,
        supervision_maximum=3,
        pad_token_id=99,
    )

    assert len(batches) == 1
    assert probes[0]["roles"] == [
        "longest_sequence",
        "longest_completion",
        "combined_memory_envelope",
    ]
    assert probes[0]["construction"] == "natural-row"
    assert envelope_record is probes[0]


def test_scheduler_warmup_advance_reaches_peak_without_changing_parameter() -> None:
    parameter = torch.nn.Parameter(torch.tensor([5.0]))
    optimizer = torch.optim.AdamW([parameter], lr=0.2)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda step: min(step / 3, 1.0),
    )

    initial, peak = smoke._advance_scheduler_to_peak(
        optimizer,
        scheduler,
        warmup_steps=3,
        expected_learning_rate=0.2,
    )

    assert initial == [0.0]
    assert peak == [0.2]
    assert parameter.item() == 5.0


def test_exact_reload_gate_rejects_any_loss_or_logit_change() -> None:
    fingerprint = {"dtype": "torch.bfloat16", "shape": [1, 2, 3], "sha256": "a" * 64}
    reference = {"loss": 1.25, "projected_logits": fingerprint}
    smoke._require_exact_reload(
        reference,
        loss=1.25,
        projected_logits=dict(fingerprint),
    )
    with pytest.raises(RuntimeError, match="projected logits"):
        smoke._require_exact_reload(
            reference,
            loss=1.25,
            projected_logits={**fingerprint, "sha256": "b" * 64},
        )
    with pytest.raises(RuntimeError, match="changed loss"):
        smoke._require_exact_reload(
            reference,
            loss=1.2500001,
            projected_logits=dict(fingerprint),
        )


def _trainer_probe_config() -> SimpleNamespace:
    return SimpleNamespace(
        run=SimpleNamespace(seed=31),
        trainer=SimpleNamespace(
            learning_rate=0.1,
            weight_decay=0.01,
            gradient_checkpointing=True,
        ),
    )


def test_trainer_probe_arguments_are_one_step_and_io_free(tmp_path: Path) -> None:
    arguments = smoke._trainer_probe_arguments(
        _trainer_probe_config(), tmp_path / "trainer"
    )

    assert arguments["max_steps"] == 1
    assert arguments["do_train"] is True
    assert arguments["do_eval"] is True
    assert arguments["gradient_accumulation_steps"] == 1
    assert arguments["gradient_checkpointing_kwargs"] == {"use_reentrant": False}
    assert arguments["warmup_steps"] == 0
    assert arguments["optim"] == "adamw_torch_fused"
    assert arguments["adam_beta1"] == 0.9
    assert arguments["adam_beta2"] == 0.999
    assert arguments["adam_epsilon"] == 1e-8
    assert arguments["max_grad_norm"] == 0.0
    assert arguments["save_strategy"] == "no"
    assert arguments["eval_strategy"] == "no"
    assert arguments["logging_strategy"] == "no"
    assert arguments["logging_nan_inf_filter"] is False
    assert arguments["average_tokens_across_devices"] is True


def test_actual_completion_trainer_lifecycle_probe_updates_and_evaluates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    try:
        from accelerate.utils import DynamoBackend
    except ImportError:
        # Mirror the production boundary: exact enum identity is available in
        # the training environment, while lightweight CI may omit Accelerate.
        class DynamoBackend(Enum):
            NO = "NO"

    class TinyIndexedModel(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.logit_vector = torch.nn.Parameter(torch.zeros(8))

        def forward(
            self,
            *,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor,
            logits_to_keep: torch.Tensor,
        ) -> dict[str, torch.Tensor]:
            assert input_ids.shape == attention_mask.shape
            logits = self.logit_vector.reshape(1, 1, -1).expand(
                input_ids.shape[0], logits_to_keep.numel(), -1
            )
            return {"logits": logits}

    class FakeTrainingArguments:
        observed: dict[str, object] | None = None

        def __init__(self, **kwargs: object) -> None:
            type(self).observed = dict(kwargs)
            self.__dict__.update(kwargs)
            self.n_gpu = 1
            self.device = SimpleNamespace(type="cuda", index=0)

    class FakeTrainerCallback:
        pass

    class FakeTrainer:
        def __init__(
            self,
            *,
            model: torch.nn.Module,
            args: object,
            train_dataset: list[dict[str, list[int]]],
            eval_dataset: list[dict[str, list[int]]],
            data_collator: object,
            callbacks: list[object],
        ) -> None:
            self.model = model
            self.model._original_forward = self.model.forward

            def prepared_forward(*args, **kwargs):
                outputs = self.model._original_forward(*args, **kwargs)
                return {"logits": outputs["logits"].double()}

            prepared_forward.__wrapped__ = self.model._original_forward
            self.model.forward = prepared_forward
            self.args = args
            self.train_dataset = train_dataset
            self.eval_dataset = eval_dataset
            self.data_collator = data_collator
            self.callbacks = callbacks
            self.accelerator = SimpleNamespace(
                num_processes=1,
                gradient_accumulation_steps=1,
                distributed_type=SimpleNamespace(name="NO", value="NO"),
                device=SimpleNamespace(type="cuda", index=0),
                mixed_precision="bf16",
                state=SimpleNamespace(
                    dynamo_plugin=SimpleNamespace(backend=DynamoBackend.NO)
                ),
                unwrap_model=self._unwrap_model,
            )
            self.is_deepspeed_enabled = False
            self.is_fsdp_enabled = False
            self.is_tp_enabled = False
            self.state = SimpleNamespace(global_step=0)

        @staticmethod
        def _unwrap_model(
            model,
            *,
            keep_fp32_wrapper: bool,
            keep_torch_compile: bool,
        ):
            assert keep_fp32_wrapper is False
            assert keep_torch_compile is False
            model.forward = model.__dict__.pop("_original_forward")
            return model

        def train(self) -> SimpleNamespace:
            self.model.train()
            inputs = self.data_collator(self.train_dataset)
            supervised = inputs["labels"].ne(-100).sum()
            loss = self.compute_loss(
                self.model,
                inputs,
                num_items_in_batch=supervised,
            )
            loss.backward()
            if self.args.max_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(
                    list(self.model.parameters()), self.args.max_grad_norm
                )
            control = SimpleNamespace()
            for callback in self.callbacks:
                callback.on_pre_optimizer_step(
                    self.args, self.state, control, model=self.model
                )
            optimizer = torch.optim.SGD(
                self.model.parameters(), lr=self.args.learning_rate
            )
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            self.state.global_step = 1
            return SimpleNamespace(
                global_step=1,
                training_loss=float(loss.detach()),
            )

        def evaluate(self) -> dict[str, float]:
            self.model.eval()
            inputs = self.data_collator(self.eval_dataset)
            with torch.no_grad():
                loss = self.compute_loss(self.model, inputs)
            return {"eval_loss": float(loss)}

    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", lambda: None)
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda: 123)
    monkeypatch.setattr(torch.cuda, "max_memory_reserved", lambda: 150)

    model = TinyIndexedModel()
    batch = _completion_batch(sequence_tokens=5, supervised_tokens=2)
    record = smoke._trainer_integration_probe(
        _trainer_probe_config(),
        model,
        batch,
        {
            "id": "combined",
            "roles": ["combined_memory_envelope"],
            "construction": "natural-row",
            "sequence_tokens": 5,
            "attended_tokens": 5,
            "supervised_tokens": 2,
            "projected_positions": 2,
        },
        list(model.named_parameters()),
        pad_token_id=7,
        torch=torch,
        Trainer=FakeTrainer,
        TrainerCallback=FakeTrainerCallback,
        TrainingArguments=FakeTrainingArguments,
    )

    assert record["format"] == "peano-completion-only-trainer-integration"
    assert "_original_forward" not in model.__dict__
    restored_outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        logits_to_keep=torch.tensor([3], dtype=torch.long),
    )
    assert restored_outputs["logits"].dtype == torch.float32
    assert record["train_global_step"] == 1
    assert math.isfinite(record["training_loss"])
    assert math.isfinite(record["evaluation_loss"])
    assert record["batch"] == {
        "role": "componentwise-maximal-memory-envelope",
        "probe_id": "combined",
        "construction": "natural-row",
        "sequence_tokens": 5,
        "attended_tokens": 5,
        "supervised_tokens": 2,
        "projected_positions": 2,
    }
    assert record["arguments"]["trainer_builtin_clip"] == "disabled"
    assert record["arguments"]["trainer_builtin_max_grad_norm"] == 0.0
    assert record["arguments"]["custom_pre_optimizer_clip"] == 1.0
    assert record["arguments"]["custom_pre_optimizer_error_if_nonfinite"] is True
    assert record["gradients"]["hook"] == "on_pre_optimizer_step"
    assert record["gradients"]["raw"]["parameters_with_finite_grad"] == 1
    clip = record["gradients"]["custom_pre_optimizer_clip"]
    assert clip["max_norm"] == 1.0
    assert clip["error_if_nonfinite"] is True
    assert math.isfinite(clip["norm_before_clip"])
    assert clip["postclip"] == record["gradients"]["raw"]
    assert record["runtime"]["accelerator_backward_divisor"] == 1
    assert record["runtime"]["configured_trainer_gradient_accumulation_steps"] == 1
    assert record["runtime"]["device"] == {"type": "cuda", "index": 0}
    assert record["runtime"]["mixed_precision"] == "bf16"
    assert record["runtime"]["dynamo_backend"] == {
        "name": "NO",
        "value": "NO",
    }
    assert record["adapter_update"]["changed_parameter_tensors"] == 1
    assert record["train_runtime"]["peak_cuda_allocated_bytes"] == 123
    assert record["evaluation_runtime"]["peak_cuda_reserved_bytes"] == 150
    assert FakeTrainingArguments.observed is not None
    assert FakeTrainingArguments.observed["save_strategy"] == "no"
    assert FakeTrainingArguments.observed["eval_strategy"] == "no"
    assert FakeTrainingArguments.observed["max_grad_norm"] == 0.0
    assert FakeTrainingArguments.observed["gradient_checkpointing_kwargs"] == {
        "use_reentrant": False
    }


def _selection_config() -> SimpleNamespace:
    return SimpleNamespace(
        data=SimpleNamespace(
            train_path="data/peano-policy-v3/train.jsonl",
            eval_path="data/peano-policy-v3/val.jsonl",
            max_length=99,
        ),
        run=SimpleNamespace(
            seed=7,
            max_train_samples=None,
            max_eval_samples=17,
        ),
        curriculum=SimpleNamespace(
            selection_seed=11,
            synthetic_row_ceiling=50,
            max_train_tokens=1_000,
            max_train_squared_tokens=10_000,
            max_eval_tokens=1_000,
            max_eval_squared_tokens=10_000,
        ),
        generation=SimpleNamespace(max_new_tokens=100),
        model=SimpleNamespace(model_id="model", revision="a" * 40),
    )


@pytest.mark.parametrize(
    ("sequence_id", "completion_id", "expected"),
    [
        (
            "seq",
            "completion",
            [("seq", ("longest_sequence",)), ("completion", ("longest_completion",))],
        ),
        (
            "seq",
            "seq",
            [("seq", ("longest_sequence", "longest_completion"))],
        ),
    ],
)
def test_curriculum_smoke_selects_both_extrema_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
    sequence_id: str,
    completion_id: str,
    expected: list[tuple[str, tuple[str, ...]]],
) -> None:
    examples = (
        SimpleNamespace(example_id="seq"),
        SimpleNamespace(example_id="completion"),
        SimpleNamespace(example_id="other"),
    )
    token_record = {
        "rows": 3,
        "sequence": {"maximum": 90, "longest_example_id": sequence_id},
        "supervision": {"maximum": 20, "longest_example_id": completion_id},
    }
    monkeypatch.setattr(
        smoke,
        "load_curriculum",
        lambda *_args, **_kwargs: SimpleNamespace(
            examples=examples,
            attestation={"curriculum_sha256": "b" * 64},
        ),
    )
    monkeypatch.setattr(
        smoke,
        "tokenize_split",
        lambda *_args, **_kwargs: ([], token_record),
    )
    monkeypatch.setattr(smoke, "enforce_token_budget", lambda *_args, **_kwargs: None)

    selected, attestation, observed = smoke._smoke_examples(
        _selection_config(),
        _IdentityTokenizer(),
    )

    assert [(item.example.example_id, item.roles) for item in selected] == expected
    assert attestation == {"curriculum_sha256": "b" * 64}
    assert observed is token_record


def test_curriculum_extremum_must_exist_in_selected_population(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        smoke,
        "load_curriculum",
        lambda *_args, **_kwargs: SimpleNamespace(
            examples=(SimpleNamespace(example_id="present"),),
            attestation={},
        ),
    )
    monkeypatch.setattr(
        smoke,
        "tokenize_split",
        lambda *_args, **_kwargs: (
            [],
            {
                "rows": 1,
                "sequence": {"maximum": 5, "longest_example_id": "missing"},
                "supervision": {"maximum": 2, "longest_example_id": "present"},
            },
        ),
    )
    monkeypatch.setattr(smoke, "enforce_token_budget", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="longest_sequence training row is absent"):
        smoke._smoke_examples(_selection_config(), _IdentityTokenizer())


def _admission_example(example_id: str, numeral: int) -> ProofExample:
    environment = model_v1_environment()
    return ProofExample(
        example_id=example_id,
        prompt=render_prompt(
            goals=(f"⊢ {numeral} = {numeral}",),
            focus=0,
            environment=environment,
        ),
        completion="refl</tactic>",
        environment_sha256=environment.sha256,
    )


@pytest.mark.parametrize("train_count", [1, 2])
def test_smoke_admission_plan_is_bounded_stratified_and_source_bound(
    monkeypatch: pytest.MonkeyPatch,
    train_count: int,
) -> None:
    training = tuple(
        _admission_example(f"train-{index}", index)
        for index in range(train_count)
    )
    validation = (
        _admission_example("validation-z", 12),
        _admission_example("validation-a", 10),
        _admission_example("validation-m", 11),
    )
    monkeypatch.setattr(smoke, "load_examples", lambda *_args, **_kwargs: validation)

    result = smoke._smoke_admission_plan(
        _selection_config(),
        _AdmissionTokenizer(),
        tuple(
            smoke.SmokeExampleSelection(example, ("longest_sequence",))
            for example in training
        ),
        corpus_eligibility={"eligibility_sha256": "a" * 64},
        curriculum_attestation={"curriculum_sha256": "b" * 64},
        tokenized_train={"record_sha256": "c" * 64},
    )

    assert len(result.plan.probes) == train_count + 1
    assert result.plan.train_candidate_count == train_count
    assert result.plan.validation_candidate_count == 1
    assert {probe.source for probe in result.plan.probes} == {
        "train",
        "validation",
    }
    assert {
        probe.example.example_id
        for probe in result.plan.probes
        if probe.source == "validation"
    } == {"validation-a"}
    assert result.plan.selection_binding_sha256 == result.selection[
        "selection_binding_sha256"
    ]
    core = dict(result.selection)
    claimed = core.pop("selection_binding_sha256")
    assert sha256_json(core) == claimed
    assert result.selection["tokenized_evaluation_sha256"] == (
        result.tokenized_evaluation["record_sha256"]
    )
    assert result.tokenized_evaluation["rows"] == 3


def test_smoke_admission_plan_rejects_missing_source_digests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    train = _admission_example("train", 0)
    validation = _admission_example("validation", 1)
    monkeypatch.setattr(smoke, "load_examples", lambda *_args, **_kwargs: [validation])

    with pytest.raises(RuntimeError, match="sealed corpus eligibility"):
        smoke._smoke_admission_plan(
            _selection_config(),
            _AdmissionTokenizer(),
            (smoke.SmokeExampleSelection(train, ("longest_sequence",)),),
            corpus_eligibility={},
            curriculum_attestation={"curriculum_sha256": "b" * 64},
            tokenized_train={"record_sha256": "c" * 64},
        )


class _SafeTensorHandle:
    def __init__(self, tensors: dict[str, torch.Tensor]) -> None:
        self.tensors = tensors

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback
        return False

    def keys(self):
        return self.tensors.keys()

    def get_tensor(self, name: str) -> torch.Tensor:
        return self.tensors[name]


def test_saved_adapter_reader_uses_exact_cpu_safetensors_and_detaches_values(
    tmp_path: Path,
) -> None:
    source = {
        "z": torch.tensor([3.0]),
        "a": torch.tensor([1.0, 2.0]),
    }
    calls: list[tuple[str, dict[str, object]]] = []

    def safe_open(path: str, **kwargs: object) -> _SafeTensorHandle:
        calls.append((path, dict(kwargs)))
        return _SafeTensorHandle(source)

    observed = smoke._read_adapter_safetensors(
        tmp_path / "adapter",
        safe_open=safe_open,
    )
    source["a"].add_(10.0)

    assert list(observed) == ["a", "z"]
    assert observed["a"].tolist() == [1.0, 2.0]
    assert calls == [
        (
            str(tmp_path / "adapter" / "adapter_model.safetensors"),
            {"framework": "pt", "device": "cpu"},
        )
    ]


def test_saved_adapter_reader_rejects_an_empty_safetensors_population(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError, match="safetensors is empty"):
        smoke._read_adapter_safetensors(
            tmp_path / "adapter",
            safe_open=lambda *_args, **_kwargs: _SafeTensorHandle({}),
        )


def _matching_source_evidence() -> tuple[
    dict[str, object], dict[str, object], dict[str, object]
]:
    train = {"bytes": 123, "rows": 17, "sha256": "a" * 64}
    manifest = {"bytes": 456, "sha256": "b" * 64}
    return (
        {"inputs": {"train": dict(train), "manifest": dict(manifest)}},
        {
            "source": {"train": dict(train), "manifest": dict(manifest)},
            "selected": {"rows": 11},
        },
        {"rows": 11},
    )


def test_source_evidence_gate_accepts_identical_loaded_and_sealed_inputs() -> None:
    eligibility, curriculum, token_record = _matching_source_evidence()

    smoke._require_source_evidence_agrees(eligibility, curriculum, token_record)


@pytest.mark.parametrize(
    ("section", "field"),
    [("train", "sha256"), ("train", "rows"), ("manifest", "bytes")],
)
def test_source_evidence_gate_rejects_changed_loaded_input(
    section: str,
    field: str,
) -> None:
    eligibility, curriculum, token_record = _matching_source_evidence()
    loaded = curriculum["source"][section]  # type: ignore[index]
    loaded[field] = "c" * 64 if field == "sha256" else 999  # type: ignore[index]

    with pytest.raises(RuntimeError, match=f"{section} differs"):
        smoke._require_source_evidence_agrees(eligibility, curriculum, token_record)


def test_source_evidence_gate_rejects_tokenized_selection_row_mismatch() -> None:
    eligibility, curriculum, token_record = _matching_source_evidence()
    token_record["rows"] = 10

    with pytest.raises(RuntimeError, match="row count differs"):
        smoke._require_source_evidence_agrees(eligibility, curriculum, token_record)


def test_v2_source_contains_exact_reload_and_two_probe_fail_closed_checks() -> None:
    source = (REPOSITORY_ROOT / "training" / "peano_policy" / "smoke.py").read_text(
        encoding="utf-8"
    )
    assert "_require_exact_reload(" in source
    assert '"longest_sequence"' in source
    assert '"longest_completion"' in source
    assert "_require_and_clip_gradients(torch, named_trainable)" in source
    assert "_strict_pre_optimizer_clip_evidence(torch, named_trainable)" in source
    assert "_changed_parameter_names(torch, before, named_trainable)" in source
    assert "base.config.use_cache = pre_save_use_cache" in source
    assert "reloaded.config.use_cache = pre_save_use_cache" in source
    manual_release = source.index(
        "del optimizer, scheduler, decay_parameters, no_decay_parameters"
    )
    trainer_construction = source.index(
        "trainer_integration = _trainer_integration_probe("
    )
    assert manual_release < trainer_construction
    assert "batches[envelope_index]" in source
    assert "class CompletionOnlyTrainer(CompletionOnlyTrainerMixin, Trainer)" in source
    assert "train_result = trainer.train()" in source
    assert "eval_metrics = trainer.evaluate()" in source
    assert "restore_model_for_adapter_admission(trainer=trainer, model=model)" in source


def test_v2_saved_adapter_admission_reuses_one_strict_fresh_base_reload() -> None:
    function_source = inspect.getsource(smoke._curriculum_model_smoke)
    loader_source = inspect.getsource(smoke._load_lora_model)
    report_source = inspect.getsource(smoke.run_smoke)

    assert "capture_in_memory_policy(" in function_source
    assert "canonical_peft_adapter_state(" in function_source
    assert "admit_loaded_policy(" in function_source
    assert "_read_adapter_safetensors(" in function_source
    assert "local_files_only=True" in function_source
    assert function_source.count("_load_base_model(") == 1
    assert 'adapter_name="default"' in function_source
    assert "is_trainable=False" in function_source
    assert "autocast_adapter_dtype=True" in function_source
    assert "low_cpu_mem_usage=False" in function_source
    assert "_save_smoke_artifacts(" in function_source
    assert function_source.count("require_protected=True") == 3
    assert (
        function_source.index("sha256_json(base.config.to_dict())")
        < function_source.index("base.config.use_cache = pre_save_use_cache")
    )
    assert (
        loader_source.index("base_config_sha256 = sha256_json(model.config.to_dict())")
        < loader_source.index("model.config.use_cache = False")
    )
    assert 'report["adapter_admission"] = evidence["adapter_admission"]' in (
        report_source
    )
    assert 'report["adapter_admission_selection"]' in report_source
    assert 'report["tokenized_evaluation"]' in report_source
