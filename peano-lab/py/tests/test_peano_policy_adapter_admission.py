"""Focused tests for bounded final saved-adapter semantic admission."""

from __future__ import annotations

from contextlib import contextmanager
import copy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest


torch = pytest.importorskip("torch")


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.peano_policy.adapter_admission import (  # noqa: E402
    ADMISSION_FORMAT,
    AdapterAdmissionDependencies,
    AdapterAdmissionError,
    BaseReloadContract,
    admit_saved_adapter,
    canonical_tensor_population_fingerprint,
    capture_in_memory_policy,
    require_adapter_admission_for_prompt,
    restore_model_for_adapter_admission,
    select_admission_probes,
    validate_adapter_admission_evidence,
    validate_manifest_adapter_admission,
)
from training.peano_policy.contract import model_v1_environment  # noqa: E402
from training.peano_policy.data import tokenize_completion  # noqa: E402
from training.peano_policy.manifest import (  # noqa: E402
    artifact_directory_hash,
    sha256_json,
)
from training.peano_policy.prompt import ProofExample, render_prompt  # noqa: E402


REVISION = "a" * 40
ADAPTER_KEY = "base_model.model.layers.0.self_attn.q_proj.lora_A.weight"
ENVIRONMENT = model_v1_environment()


class _Tokenizer:
    eos_token_id = 31
    pad_token_id = 31
    padding_side = "right"
    special_tokens_map = {"eos_token": "<eos>", "pad_token": "<eos>"}

    def __init__(self, *, offset: int = 0) -> None:
        self.offset = offset

    def __len__(self) -> int:
        return 32

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        raw = text.encode("utf-8")
        return {
            "input_ids": [
                (sum(raw) + self.offset) % 29 + 1,
                (len(raw) + self.offset) % 29 + 1,
            ]
        }


def _example(index: int) -> ProofExample:
    prompt = render_prompt(
        goals=(f"⊢ {index} = {index}",),
        focus=0,
        environment=ENVIRONMENT,
    )
    return ProofExample(
        example_id=f"example-{index}",
        prompt=prompt,
        completion="refl</tactic>",
        environment_sha256=ENVIRONMENT.sha256,
    )


def _examples_and_features(
    start: int,
    count: int,
) -> tuple[tuple[ProofExample, ...], tuple[dict[str, list[int]], ...]]:
    examples = tuple(_example(index) for index in range(start, start + count))
    tokenizer = _Tokenizer()
    features = tuple(
        tokenize_completion(example, tokenizer, max_length=32)
        for example in examples
    )
    return examples, features


def _plan(*, count: int = 3):
    train_examples, train_features = _examples_and_features(0, 4)
    eval_examples, eval_features = _examples_and_features(10, 3)
    return select_admission_probes(
        admitted_train_examples=train_examples,
        admitted_train_features=train_features,
        admitted_evaluation_examples=eval_examples,
        admitted_evaluation_features=eval_features,
        max_length=32,
        selection_binding_sha256="b" * 64,
        count=count,
    )


class _Config:
    def __init__(self, record: dict[str, object]) -> None:
        self._record = copy.deepcopy(record)
        self._commit_hash = REVISION
        self.use_cache = True

    def to_dict(self) -> dict[str, object]:
        return copy.deepcopy(self._record)


class _Base(torch.nn.Module):
    def __init__(self, config_record: dict[str, object]) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.tensor(0.0), requires_grad=False)
        self.config = _Config(config_record)

    def forward(
        self,
        input_ids: Any,
        attention_mask: Any,
        logits_to_keep: Any,
    ) -> Any:
        del attention_mask
        selected = input_ids.index_select(1, logits_to_keep).float()
        vocab = torch.arange(32, device=input_ids.device, dtype=torch.float32)
        return SimpleNamespace(logits=-(selected.unsqueeze(-1) - vocab) ** 2 / 32.0)


class _TinyPolicy(torch.nn.Module):
    def __init__(
        self,
        value: float,
        *,
        semantic_offset: float = 0.0,
        adapter_effect: bool = True,
    ) -> None:
        super().__init__()
        self.adapter = torch.nn.Parameter(torch.tensor([[value]], dtype=torch.float32))
        self.peft_config = {"default": object()}
        self._disabled = False
        self.semantic_offset = semantic_offset
        self.adapter_effect = adapter_effect

    def forward(
        self,
        input_ids: Any,
        attention_mask: Any,
        logits_to_keep: Any,
    ) -> Any:
        del attention_mask
        selected = input_ids.index_select(1, logits_to_keep).float()
        vocab = torch.arange(32, device=input_ids.device, dtype=torch.float32)
        logits = -(selected.unsqueeze(-1) - vocab) ** 2 / 32.0
        effect = torch.arange(32, device=input_ids.device, dtype=torch.float32) / 97.0
        if self.adapter_effect and not self._disabled:
            logits = logits + (self.adapter.flatten()[0] + self.semantic_offset) * effect
        return SimpleNamespace(logits=logits)

    @contextmanager
    def disable_adapter(self):
        previous = self._disabled
        self._disabled = True
        try:
            yield
        finally:
            self._disabled = previous


class _SafeHandle:
    def __init__(self, state: dict[str, torch.Tensor]) -> None:
        self.state = state

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback
        return False

    def keys(self):
        return self.state.keys()

    def get_tensor(self, name: str) -> torch.Tensor:
        return self.state[name].detach().clone()


class _FakeStack:
    def __init__(
        self,
        *,
        saved_value: float = 0.5,
        loaded_value: float | None = None,
        tokenizer_offset: int = 0,
        semantic_offset: float = 0.0,
        adapter_effect: bool = True,
    ) -> None:
        self.config_record = {"architectures": ["TinyCausalLM"], "vocab_size": 32}
        self.saved_value = saved_value
        self.loaded_value = saved_value if loaded_value is None else loaded_value
        self.tokenizer_offset = tokenizer_offset
        self.semantic_offset = semantic_offset
        self.adapter_effect = adapter_effect
        self.model_calls: list[tuple[object, dict[str, object]]] = []
        self.tokenizer_calls: list[tuple[object, dict[str, object]]] = []
        self.peft_calls: list[tuple[object, dict[str, object]]] = []
        self.state_calls: list[dict[str, object]] = []
        self.safe_calls: list[tuple[object, dict[str, object]]] = []

    def dependencies(self) -> AdapterAdmissionDependencies:
        owner = self

        class AutoModel:
            @classmethod
            def from_pretrained(cls, source, **kwargs):
                owner.model_calls.append((source, kwargs))
                return _Base(owner.config_record)

        class AutoTokenizer:
            @classmethod
            def from_pretrained(cls, source, **kwargs):
                owner.tokenizer_calls.append((source, kwargs))
                return _Tokenizer(offset=owner.tokenizer_offset)

        class PeftModel:
            @classmethod
            def from_pretrained(cls, base, source, **kwargs):
                del base
                owner.peft_calls.append((source, kwargs))
                return _TinyPolicy(
                    owner.loaded_value,
                    semantic_offset=owner.semantic_offset,
                    adapter_effect=owner.adapter_effect,
                )

        def get_state(model, **kwargs):
            owner.state_calls.append(kwargs)
            return {ADAPTER_KEY: model.adapter}

        def safe_open(path, **kwargs):
            owner.safe_calls.append((path, kwargs))
            return _SafeHandle(
                {ADAPTER_KEY: torch.tensor([[owner.saved_value]], dtype=torch.float32)}
            )

        return AdapterAdmissionDependencies(
            torch=torch,
            AutoModelForCausalLM=AutoModel,
            AutoTokenizer=AutoTokenizer,
            PeftModel=PeftModel,
            get_peft_model_state_dict=get_state,
            safe_open=safe_open,
        )


def _artifacts(tmp_path: Path, *, unsafe_adapter: bool = False):
    adapter = tmp_path / "adapter"
    tokenizer = tmp_path / "tokenizer"
    adapter.mkdir()
    tokenizer.mkdir()
    (adapter / "adapter_config.json").write_text(
        json.dumps({"peft_type": "LORA"}), encoding="utf-8"
    )
    (adapter / "adapter_model.safetensors").write_bytes(b"test-safe-state")
    if unsafe_adapter:
        (adapter / "adapter_model.bin").write_bytes(b"pickle")
    (tokenizer / "tokenizer.json").write_text("{}", encoding="utf-8")
    for path in (adapter, tokenizer):
        for payload in path.iterdir():
            payload.chmod(0o444)
        path.chmod(0o555)
    return (
        artifact_directory_hash(
            tmp_path, "adapter", require_protected=True
        ),
        artifact_directory_hash(
            tmp_path, "tokenizer", require_protected=True
        ),
    )


def _contract(stack: _FakeStack) -> BaseReloadContract:
    return BaseReloadContract(
        model_id="test/Tiny-Causal-LM",
        revision=REVISION,
        config_sha256=sha256_json(stack.config_record),
    )


def _snapshot(stack: _FakeStack, plan=None, *, adapter_effect: bool = True):
    selected = _plan() if plan is None else plan
    contract = _contract(stack)
    model = _TinyPolicy(0.5, adapter_effect=adapter_effect)
    snapshot = capture_in_memory_policy(
        model=model,
        tokenizer=_Tokenizer(),
        plan=selected,
        base_contract=contract,
        canonical_adapter_state={ADAPTER_KEY: model.adapter},
        torch_module=torch,
        device="cpu",
    )
    return selected, contract, snapshot


def _admit(tmp_path: Path, stack: _FakeStack, *, adapter_effect: bool = True):
    plan, contract, snapshot = _snapshot(
        stack,
        adapter_effect=adapter_effect,
    )
    adapter, tokenizer = _artifacts(tmp_path)
    evidence = admit_saved_adapter(
        output_dir=tmp_path,
        adapter_artifacts=adapter,
        tokenizer_artifacts=tokenizer,
        plan=plan,
        snapshot=snapshot,
        base_contract=contract,
        device="cpu",
        dependencies=stack.dependencies(),
    )
    return evidence, plan, snapshot


def _manifest_for_admission(evidence: dict[str, object]) -> dict[str, object]:
    evidence = copy.deepcopy(evidence)
    # The fake semantic stack runs on CPU; the production manifest contract is
    # deliberately pinned to the reviewed single-GPU cuda:0 runtime.
    evidence["reload"]["device"] = "cuda:0"
    evidence.pop("content_sha256")
    evidence["content_sha256"] = sha256_json(evidence)
    admitted_base = evidence["base_model"]
    artifacts = evidence["artifacts"]
    probes = evidence["probes"]
    return {
        "prompt_version": 3,
        "base_model": {
            key: admitted_base[key]
            for key in (
                "id",
                "requested_revision",
                "resolved_snapshot_hash",
                "config_sha256",
            )
        },
        "runtime": {
            "dtype": admitted_base["dtype"],
            "attention": admitted_base["attention"],
            "trainer": {"device": {"type": "cuda", "index": 0}},
        },
        "adapter": {
            "root": "adapter",
            "sha256": artifacts["adapter_sha256"],
            "files": {
                "adapter/adapter_config.json": artifacts[
                    "adapter_config_sha256"
                ],
                "adapter/adapter_model.safetensors": artifacts[
                    "adapter_safetensors_sha256"
                ],
            },
        },
        "tokenizer": {
            "artifacts": {
                "root": "tokenizer",
                "sha256": artifacts["tokenizer_sha256"],
                "files": {"tokenizer/tokenizer.json": "0" * 64},
            }
        },
        "inputs": {
            "run_identity": {
                "sha256": probes["selection_binding_sha256"],
            }
        },
        "training_evidence": {
            "artifacts": {
                "adapter_sha256": artifacts["adapter_sha256"],
                "tokenizer_sha256": artifacts["tokenizer_sha256"],
            }
        },
        "adapter_admission": evidence,
    }


def test_module_import_is_framework_light() -> None:
    script = f"""
import builtins, sys
sys.path.insert(0, {str(REPO_ROOT)!r})
real = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.', 1)[0] in {{'torch', 'transformers', 'peft', 'safetensors'}}:
        raise AssertionError(name)
    return real(name, *args, **kwargs)
builtins.__import__ = guarded
import training.peano_policy.adapter_admission
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_probe_selection_is_order_independent_stratified_and_hash_bound() -> None:
    train_examples, train_features = _examples_and_features(0, 4)
    eval_examples, eval_features = _examples_and_features(10, 3)

    first = select_admission_probes(
        admitted_train_examples=train_examples,
        admitted_train_features=train_features,
        admitted_evaluation_examples=eval_examples,
        admitted_evaluation_features=eval_features,
        max_length=32,
        selection_binding_sha256="b" * 64,
    )
    second = select_admission_probes(
        admitted_train_examples=tuple(reversed(train_examples)),
        admitted_train_features=tuple(reversed(train_features)),
        admitted_evaluation_examples=tuple(reversed(eval_examples)),
        admitted_evaluation_features=tuple(reversed(eval_features)),
        max_length=32,
        selection_binding_sha256="b" * 64,
    )

    assert first.compact_records == second.compact_records
    assert first.candidate_population_sha256 == second.candidate_population_sha256
    assert len(first.probes) == 3
    assert {probe.source for probe in first.probes} == {"train", "validation"}


def test_population_hash_changes_when_an_unselected_candidate_changes() -> None:
    train_examples, train_features = _examples_and_features(0, 8)
    eval_examples, eval_features = _examples_and_features(20, 8)
    first = select_admission_probes(
        admitted_train_examples=train_examples,
        admitted_train_features=train_features,
        admitted_evaluation_examples=eval_examples,
        admitted_evaluation_features=eval_features,
        max_length=32,
        selection_binding_sha256="c" * 64,
    )
    selected_ids = {probe.example.example_id for probe in first.probes}
    changed = [copy.deepcopy(feature) for feature in train_features]
    index = next(
        position
        for position, example in enumerate(train_examples)
        if example.example_id not in selected_ids
    )
    changed[index]["input_ids"][-1] += 1
    changed[index]["labels"][-1] += 1
    second = select_admission_probes(
        admitted_train_examples=train_examples,
        admitted_train_features=changed,
        admitted_evaluation_examples=eval_examples,
        admitted_evaluation_features=eval_features,
        max_length=32,
        selection_binding_sha256="c" * 64,
    )
    assert first.candidate_population_sha256 != second.candidate_population_sha256


@pytest.mark.parametrize("count", [0, 1, 4, True])
def test_probe_count_is_bounded(count: object) -> None:
    train_examples, train_features = _examples_and_features(0, 2)
    eval_examples, eval_features = _examples_and_features(10, 2)
    with pytest.raises(AdapterAdmissionError, match="two or three"):
        select_admission_probes(
            admitted_train_examples=train_examples,
            admitted_train_features=train_features,
            admitted_evaluation_examples=eval_examples,
            admitted_evaluation_features=eval_features,
            max_length=32,
            selection_binding_sha256="b" * 64,
            count=count,  # type: ignore[arg-type]
        )


def test_probe_feature_requires_exact_completion_supervision() -> None:
    train_examples, train_features = _examples_and_features(0, 2)
    eval_examples, eval_features = _examples_and_features(10, 2)
    broken = [copy.deepcopy(feature) for feature in train_features]
    broken[0]["labels"][-1] += 1
    with pytest.raises(AdapterAdmissionError, match="must equal"):
        select_admission_probes(
            admitted_train_examples=train_examples,
            admitted_train_features=broken,
            admitted_evaluation_examples=eval_examples,
            admitted_evaluation_features=eval_features,
            max_length=32,
            selection_binding_sha256="b" * 64,
        )


def test_tensor_population_is_order_independent_and_value_exact() -> None:
    left = {
        "z": torch.tensor([[1.0]], dtype=torch.float32),
        "a": torch.tensor([2.0], dtype=torch.float32),
    }
    right = {"a": left["a"].clone(), "z": left["z"].clone()}
    changed = {"a": left["a"].clone(), "z": torch.tensor([[1.5]])}
    assert canonical_tensor_population_fingerprint(
        left, torch_module=torch
    ) == canonical_tensor_population_fingerprint(right, torch_module=torch)
    assert canonical_tensor_population_fingerprint(
        left, torch_module=torch
    ) != canonical_tensor_population_fingerprint(changed, torch_module=torch)


def test_tensor_population_rejects_nonfinite_or_nontensor_values() -> None:
    with pytest.raises(AdapterAdmissionError, match="non-finite"):
        canonical_tensor_population_fingerprint(
            {"a": torch.tensor([float("nan")])}, torch_module=torch
        )
    with pytest.raises(AdapterAdmissionError, match="not a tensor"):
        canonical_tensor_population_fingerprint({"a": [1.0]}, torch_module=torch)


def test_trainer_forward_wrapper_is_removed_before_adapter_admission() -> None:
    model = _TinyPolicy(0.5)
    original_forward = model.forward

    def prepared_forward(*args, **kwargs):
        return original_forward(*args, **kwargs)

    prepared_forward.__wrapped__ = original_forward  # type: ignore[attr-defined]
    model._original_forward = original_forward
    model.forward = prepared_forward  # type: ignore[method-assign]
    calls: list[tuple[bool, bool]] = []

    class Accelerator:
        @staticmethod
        def unwrap_model(
            prepared,
            *,
            keep_fp32_wrapper: bool,
            keep_torch_compile: bool,
        ):
            calls.append((keep_fp32_wrapper, keep_torch_compile))
            restored = prepared.__dict__.pop("_original_forward")
            prepared.forward = restored
            return prepared

    trainer = SimpleNamespace(model=model, accelerator=Accelerator())
    restored = restore_model_for_adapter_admission(trainer=trainer, model=model)

    assert restored is model
    assert calls == [(False, False)]
    assert "_original_forward" not in model.__dict__
    assert model.forward.__func__ is original_forward.__func__


def test_adapter_snapshot_rejects_retained_accelerate_forward_wrapper() -> None:
    stack = _FakeStack()
    plan = _plan()
    model = _TinyPolicy(0.5)
    model._original_forward = model.forward

    with pytest.raises(AdapterAdmissionError, match="retains an Accelerate"):
        capture_in_memory_policy(
            model=model,
            tokenizer=_Tokenizer(),
            plan=plan,
            base_contract=_contract(stack),
            canonical_adapter_state={ADAPTER_KEY: model.adapter},
            torch_module=torch,
            device="cpu",
        )


def test_trainer_forward_restoration_fails_if_wrapper_survives() -> None:
    model = _TinyPolicy(0.5)
    model._original_forward = model.forward
    trainer = SimpleNamespace(
        model=model,
        accelerator=SimpleNamespace(unwrap_model=lambda prepared, **kwargs: prepared),
    )

    with pytest.raises(AdapterAdmissionError, match="retained"):
        restore_model_for_adapter_admission(trainer=trainer, model=model)


def test_fresh_saved_adapter_admission_passes_and_is_compact(tmp_path: Path) -> None:
    stack = _FakeStack()
    evidence, plan, snapshot = _admit(tmp_path, stack)

    assert evidence["format"] == ADMISSION_FORMAT
    assert evidence["status"] == "passed"
    assert evidence["checks"] == {
        "tokenizer_encoding_count": len(plan.probes),
        "exact_reload_count": len(plan.probes),
        "differs_from_base_count": len(plan.probes),
    }
    assert evidence["probes"]["original_outputs_sha256"] == snapshot.outputs_sha256
    assert len(stack.model_calls) == 1
    assert len(stack.tokenizer_calls) == 1
    assert len(stack.peft_calls) == 1
    assert len(stack.safe_calls) == 1
    assert stack.model_calls[0][1]["revision"] == REVISION
    assert stack.model_calls[0][1]["use_safetensors"] is True
    assert stack.model_calls[0][1]["local_files_only"] is True
    assert stack.peft_calls[0][1]["is_trainable"] is False
    assert stack.state_calls == [
        {"adapter_name": "default", "save_embedding_layers": False}
    ]
    assert validate_adapter_admission_evidence(evidence) == evidence
    assert len(json.dumps(evidence, allow_nan=False)) < 8_000


def test_manifest_gate_joins_every_adapter_admission_authority(
    tmp_path: Path,
) -> None:
    evidence, _, _ = _admit(tmp_path, _FakeStack())
    manifest = _manifest_for_admission(evidence)

    admitted = manifest["adapter_admission"]
    assert validate_manifest_adapter_admission(manifest) == admitted
    assert require_adapter_admission_for_prompt(manifest) == admitted
    assert require_adapter_admission_for_prompt({"prompt_version": 2}) is None


@pytest.mark.parametrize(
    "mutation",
    (
        lambda manifest: manifest["base_model"].__setitem__(
            "config_sha256", "f" * 64
        ),
        lambda manifest: manifest["runtime"]["trainer"].__setitem__(
            "device", {"type": "cpu", "index": None}
        ),
        lambda manifest: manifest["inputs"]["run_identity"].__setitem__(
            "sha256", "e" * 64
        ),
        lambda manifest: manifest["adapter"].__setitem__("sha256", "d" * 64),
        lambda manifest: manifest["tokenizer"]["artifacts"].__setitem__(
            "sha256", "c" * 64
        ),
        lambda manifest: manifest["training_evidence"]["artifacts"].__setitem__(
            "adapter_sha256", "a" * 64
        ),
    ),
)
def test_manifest_gate_rejects_cross_authority_mismatch(
    tmp_path: Path,
    mutation,
) -> None:
    evidence, _, _ = _admit(tmp_path, _FakeStack())
    manifest = _manifest_for_admission(evidence)
    mutation(manifest)
    with pytest.raises(AdapterAdmissionError, match="enclosing"):
        validate_manifest_adapter_admission(manifest)


@pytest.mark.parametrize(
    ("stack", "match"),
    [
        (_FakeStack(saved_value=0.75), "saved safetensors differ"),
        (_FakeStack(loaded_value=0.75), "did not populate"),
        (_FakeStack(semantic_offset=0.25), "changed indexed loss"),
        (_FakeStack(tokenizer_offset=1), "tokenizer changed"),
    ],
)
def test_each_reload_identity_mismatch_fails_closed(
    tmp_path: Path,
    stack: _FakeStack,
    match: str,
) -> None:
    plan, contract, snapshot = _snapshot(_FakeStack())
    adapter, tokenizer = _artifacts(tmp_path)
    with pytest.raises(AdapterAdmissionError, match=match):
        admit_saved_adapter(
            output_dir=tmp_path,
            adapter_artifacts=adapter,
            tokenizer_artifacts=tokenizer,
            plan=plan,
            snapshot=snapshot,
            base_contract=contract,
            device="cpu",
            dependencies=stack.dependencies(),
        )


def test_adapter_must_differ_from_disabled_base(tmp_path: Path) -> None:
    stack = _FakeStack(adapter_effect=False)
    plan, contract, snapshot = _snapshot(stack, adapter_effect=False)
    adapter, tokenizer = _artifacts(tmp_path)
    with pytest.raises(AdapterAdmissionError, match="indistinguishable"):
        admit_saved_adapter(
            output_dir=tmp_path,
            adapter_artifacts=adapter,
            tokenizer_artifacts=tokenizer,
            plan=plan,
            snapshot=snapshot,
            base_contract=contract,
            device="cpu",
            dependencies=stack.dependencies(),
        )


def test_unsafe_or_mutated_artifact_is_rejected_before_loading(tmp_path: Path) -> None:
    stack = _FakeStack()
    plan, contract, snapshot = _snapshot(stack)
    adapter, tokenizer = _artifacts(tmp_path, unsafe_adapter=True)
    with pytest.raises(ValueError, match="pickle-compatible"):
        admit_saved_adapter(
            output_dir=tmp_path,
            adapter_artifacts=adapter,
            tokenizer_artifacts=tokenizer,
            plan=plan,
            snapshot=snapshot,
            base_contract=contract,
            device="cpu",
            dependencies=stack.dependencies(),
        )
    assert not stack.model_calls


def test_unprotected_final_artifact_is_rejected_before_loading(
    tmp_path: Path,
) -> None:
    stack = _FakeStack()
    plan, contract, snapshot = _snapshot(stack)
    adapter, tokenizer = _artifacts(tmp_path)
    adapter_directory = tmp_path / "adapter"
    adapter_directory.chmod(0o755)
    try:
        with pytest.raises(ValueError, match="not protected as 0555"):
            admit_saved_adapter(
                output_dir=tmp_path,
                adapter_artifacts=adapter,
                tokenizer_artifacts=tokenizer,
                plan=plan,
                snapshot=snapshot,
                base_contract=contract,
                device="cpu",
                dependencies=stack.dependencies(),
            )
    finally:
        adapter_directory.chmod(0o555)
    assert not stack.model_calls


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"unknown": 1}),
        lambda value: value["checks"].update({"exact_reload_count": 1}),
        lambda value: value["probes"].update(
            {"fresh_outputs_sha256": "f" * 64}
        ),
        lambda value: value["probes"]["records"][0].update(
            {"candidate_sha256": "e" * 64}
        ),
        lambda value: value["reload"].update({"base_model_loads": 2}),
        lambda value: value["adapter_tensors"].update({"tensor_count": 0}),
    ],
)
def test_admission_evidence_mutations_fail_strict_validation(
    tmp_path: Path,
    mutate,
) -> None:
    evidence, _, _ = _admit(tmp_path, _FakeStack())
    broken = copy.deepcopy(evidence)
    mutate(broken)
    if set(broken) == set(evidence):
        without_content = dict(broken)
        del without_content["content_sha256"]
        broken["content_sha256"] = sha256_json(without_content)
    with pytest.raises(AdapterAdmissionError):
        validate_adapter_admission_evidence(broken)
