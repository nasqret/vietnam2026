"""Bounded semantic admission for one final saved model-v3 adapter.

This module separates final-model admission into two phases.  First,
``capture_in_memory_policy`` reduces the trained in-memory policy to compact
hashes over two or three deterministic probes and the canonical PEFT adapter
state.  The caller can then release Trainer, optimizer, and model objects.
Second, ``admit_saved_adapter`` freshly loads the closed tokenizer, pinned base
snapshot, and saved PEFT safetensors and requires byte-exact semantic agreement
with the compact snapshot.

Probe candidates come only from the already admitted curriculum train and
validation examples supplied by the caller.  Frozen theorem-discovery goals
and held-out proof success are deliberately outside this check: admission asks
whether the artifact is the policy that was trained, not whether it solves a
benchmark.

Torch, Transformers, PEFT, and safetensors are imported lazily.  This keeps
manifest validators and documentation tooling framework-light.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
import gc
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

from .data import IGNORE_INDEX, tokenize_completion
from .manifest import (
    ADAPTER_SUBDIR,
    TOKENIZER_SUBDIR,
    require_safetensors_adapter,
    sha256_json,
    verify_artifact_directory,
)
from .objective import (
    completion_projection,
    indexed_completion_cross_entropy,
    require_indexed_logits_support,
)
from .prompt import PEANO_PROMPT_V3, ProofExample


ADMISSION_FORMAT = "peano-policy-final-adapter-admission"
ADMISSION_VERSION = 1
PROBE_SELECTION_METHOD = "sha256-stratified-admitted-train-validation-v1"
PROBE_MINIMUM = 2
PROBE_MAXIMUM = 3
TENSOR_POPULATION_FORMAT = "peano-policy-canonical-peft-tensor-population"
TENSOR_POPULATION_VERSION = 1
TENSOR_POPULATION_HASH_FORMAT = (
    "sha256-canonical-json-sorted-name-dtype-shape-content-sha256-records-v1"
)
PROJECTED_LOGITS_HASH_FORMAT = (
    "sha256-dtype-shape-header-newline-contiguous-raw-tensor-bytes-v1"
)
OUTPUT_SET_HASH_FORMAT = (
    "sha256-canonical-json-probe-sha256-loss-hex-projected-logits-records-v1"
)
HASH_CANONICALIZATION = "utf8-json-sort-keys-no-whitespace-v1"
ADAPTER_NAME = "default"

_HEX = frozenset("0123456789abcdef")
_FEATURE_KEYS = {"input_ids", "attention_mask", "labels"}
_PROBE_RECORD_KEYS = {
    "source",
    "example_id",
    "example_sha256",
    "feature_sha256",
    "candidate_sha256",
    "rank_sha256",
}


class AdapterAdmissionError(ValueError):
    """A saved adapter cannot be identified with the final trained policy."""


def _sha256(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise AdapterAdmissionError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise AdapterAdmissionError(f"{label} must be a positive integer")
    return value


def _exact_mapping(
    value: object,
    keys: set[str],
    label: str,
) -> Mapping[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise AdapterAdmissionError(f"{label} has a malformed exact schema")
    return value


def _text(value: object, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or "\n" in value
        or "\r" in value
    ):
        raise AdapterAdmissionError(f"{label} must be non-empty one-line text")
    return value


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class BaseReloadContract:
    """Exact base-model identity and loader settings for the fresh reload."""

    model_id: str
    revision: str
    config_sha256: str
    dtype: str = "bfloat16"
    attention: str = "sdpa"
    trust_remote_code: bool = False

    def __post_init__(self) -> None:
        _text(self.model_id, "base model id")
        if (
            len(self.revision) != 40
            or any(character not in _HEX for character in self.revision)
        ):
            raise AdapterAdmissionError(
                "base revision must be one immutable lowercase 40-hex commit"
            )
        _sha256(self.config_sha256, "base configuration hash")
        if self.dtype != "bfloat16":
            raise AdapterAdmissionError("adapter admission is pinned to bfloat16")
        if self.attention != "sdpa":
            raise AdapterAdmissionError("adapter admission is pinned to SDPA")
        if self.trust_remote_code is not False:
            raise AdapterAdmissionError("adapter admission forbids remote code")

    def record(self) -> dict[str, object]:
        return {
            "id": self.model_id,
            "requested_revision": self.revision,
            "resolved_snapshot_hash": self.revision,
            "config_sha256": self.config_sha256,
            "dtype": self.dtype,
            "attention": self.attention,
            "trust_remote_code": False,
        }

    @property
    def sha256(self) -> str:
        return sha256_json(self.record())


@dataclass(frozen=True, slots=True)
class ProbeFeature:
    """One unpadded, completion-supervised feature admitted for training/eval."""

    input_ids: tuple[int, ...]
    attention_mask: tuple[int, ...]
    labels: tuple[int, ...]

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Sequence[int]],
        *,
        max_length: int,
    ) -> "ProbeFeature":
        if not isinstance(value, Mapping) or set(value) != _FEATURE_KEYS:
            raise AdapterAdmissionError("probe feature has unexpected fields")
        if type(max_length) is not int or max_length < 2:
            raise AdapterAdmissionError("probe max_length must be at least two")
        converted: dict[str, tuple[int, ...]] = {}
        for name in ("input_ids", "attention_mask", "labels"):
            raw = value[name]
            if type(raw) not in {list, tuple}:
                raise AdapterAdmissionError(f"probe {name} must be a list or tuple")
            items = tuple(raw)
            if any(type(item) is not int for item in items):
                raise AdapterAdmissionError(
                    f"probe {name} must contain only non-boolean integers"
                )
            converted[name] = items
        lengths = {len(items) for items in converted.values()}
        if len(lengths) != 1:
            raise AdapterAdmissionError("probe feature fields have different lengths")
        length = lengths.pop()
        if length < 2 or length > max_length:
            raise AdapterAdmissionError("probe feature length is outside its bound")
        input_ids = converted["input_ids"]
        attention_mask = converted["attention_mask"]
        labels = converted["labels"]
        if any(token < 0 for token in input_ids):
            raise AdapterAdmissionError("probe input ids must be non-negative")
        if any(mask != 1 for mask in attention_mask):
            raise AdapterAdmissionError(
                "admission probes must be unpadded admitted examples"
            )
        supervised = tuple(label != IGNORE_INDEX for label in labels)
        if supervised[0] or not any(supervised):
            raise AdapterAdmissionError(
                "probe labels need a masked prompt and supervised completion"
            )
        first = supervised.index(True)
        if any(supervised[:first]) or not all(supervised[first:]):
            raise AdapterAdmissionError(
                "probe supervision must be one contiguous completion suffix"
            )
        if any(label < 0 for label in labels[first:]):
            raise AdapterAdmissionError("supervised probe labels must be token ids")
        if any(labels[index] != input_ids[index] for index in range(first, length)):
            raise AdapterAdmissionError(
                "supervised probe labels must equal their completion input ids"
            )
        return cls(input_ids, attention_mask, labels)

    def record(self) -> dict[str, list[int]]:
        return {
            "input_ids": list(self.input_ids),
            "attention_mask": list(self.attention_mask),
            "labels": list(self.labels),
        }

    @property
    def sha256(self) -> str:
        return sha256_json(self.record())


@dataclass(frozen=True, slots=True)
class AdmissionProbe:
    """Selected example plus its exact already-admitted token feature."""

    source: str
    example: ProofExample
    feature: ProbeFeature
    example_sha256: str
    candidate_sha256: str
    rank_sha256: str

    def compact_record(self) -> dict[str, object]:
        return {
            "source": self.source,
            "example_id": self.example.example_id,
            "example_sha256": self.example_sha256,
            "feature_sha256": self.feature.sha256,
            "candidate_sha256": self.candidate_sha256,
            "rank_sha256": self.rank_sha256,
        }


@dataclass(frozen=True, slots=True)
class AdmissionProbePlan:
    """Order-independent, hash-bound probes from the admitted curriculum."""

    max_length: int
    selection_binding_sha256: str
    candidate_population_sha256: str
    candidate_count: int
    train_candidate_count: int
    validation_candidate_count: int
    probes: tuple[AdmissionProbe, ...]

    @property
    def compact_records(self) -> tuple[dict[str, object], ...]:
        return tuple(probe.compact_record() for probe in self.probes)

    @property
    def probe_set_sha256(self) -> str:
        return sha256_json(list(self.compact_records))


@dataclass(frozen=True, slots=True)
class TensorPopulationFingerprint:
    """Compact identity of every canonical PEFT tensor and raw value byte."""

    tensor_count: int
    names_sha256: str
    population_sha256: str

    def record(self) -> dict[str, object]:
        return {
            "format": TENSOR_POPULATION_FORMAT,
            "v": TENSOR_POPULATION_VERSION,
            "tensor_count": self.tensor_count,
            "names_sha256": self.names_sha256,
            "population_sha256": self.population_sha256,
            "population_hash_format": TENSOR_POPULATION_HASH_FORMAT,
        }


@dataclass(frozen=True, slots=True)
class TensorValueFingerprint:
    """Raw-byte identity for one finite projected-logit tensor."""

    dtype: str
    shape: tuple[int, ...]
    sha256: str

    def record(self) -> dict[str, object]:
        return {
            "dtype": self.dtype,
            "shape": list(self.shape),
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ProbeOutputFingerprint:
    """Exact finite indexed loss/logit identity for one admission probe."""

    probe_sha256: str
    loss_hex: str
    projected_logits: TensorValueFingerprint

    def record(self) -> dict[str, object]:
        return {
            "probe_sha256": self.probe_sha256,
            "loss_hex": self.loss_hex,
            "projected_logits": self.projected_logits.record(),
        }


@dataclass(frozen=True, slots=True)
class InMemoryPolicySnapshot:
    """Compact final-policy state safe to retain after releasing the model."""

    base_contract_sha256: str
    probe_set_sha256: str
    tokenizer_identity_sha256: str
    adapter_population: TensorPopulationFingerprint
    outputs: tuple[ProbeOutputFingerprint, ...]

    @property
    def outputs_sha256(self) -> str:
        return sha256_json([output.record() for output in self.outputs])


@dataclass(frozen=True, slots=True)
class AdapterAdmissionDependencies:
    """Lazy heavy dependencies; injectable for bounded integration tests."""

    torch: Any
    AutoModelForCausalLM: Any
    AutoTokenizer: Any
    PeftModel: Any
    get_peft_model_state_dict: Callable[..., Mapping[str, Any]]
    safe_open: Callable[..., AbstractContextManager[Any]]


def _example_sha256(example: ProofExample) -> str:
    return sha256_json(
        {
            "example_id": example.example_id,
            "prompt_sha256": _text_sha256(example.prompt),
            "completion_sha256": _text_sha256(example.completion),
            "environment_sha256": example.environment_sha256,
        }
    )


def _candidate_probe(
    *,
    source: str,
    example: ProofExample,
    feature: Mapping[str, Sequence[int]],
    max_length: int,
    selection_binding_sha256: str,
) -> AdmissionProbe:
    if type(example) is not ProofExample:
        raise AdapterAdmissionError("probe candidates must be ProofExample values")
    normalized = ProbeFeature.from_mapping(feature, max_length=max_length)
    example_digest = _example_sha256(example)
    candidate_digest = sha256_json(
        {
            "source": source,
            "example_sha256": example_digest,
            "feature_sha256": normalized.sha256,
        }
    )
    rank_digest = sha256_json(
        {
            "method": PROBE_SELECTION_METHOD,
            "selection_binding_sha256": selection_binding_sha256,
            "candidate_sha256": candidate_digest,
        }
    )
    return AdmissionProbe(
        source=source,
        example=example,
        feature=normalized,
        example_sha256=example_digest,
        candidate_sha256=candidate_digest,
        rank_sha256=rank_digest,
    )


def select_admission_probes(
    *,
    admitted_train_examples: Sequence[ProofExample],
    admitted_train_features: Sequence[Mapping[str, Sequence[int]]],
    admitted_evaluation_examples: Sequence[ProofExample],
    admitted_evaluation_features: Sequence[Mapping[str, Sequence[int]]],
    max_length: int,
    selection_binding_sha256: str,
    count: int = PROBE_MAXIMUM,
) -> AdmissionProbePlan:
    """Choose two or three deterministic probes from admitted model-v3 data.

    The two argument pairs must be the post-selection train and validation
    examples/features used by Trainer.  No API accepts held-out theorem goals.
    Selection is stable under input reordering and includes at least one probe
    from each admitted split.
    """

    _sha256(selection_binding_sha256, "probe selection binding")
    if type(count) is not int or not PROBE_MINIMUM <= count <= PROBE_MAXIMUM:
        raise AdapterAdmissionError("admission probe count must be two or three")
    if type(max_length) is not int or max_length < 2:
        raise AdapterAdmissionError("admission probe max_length is invalid")
    pairs = (
        ("train", admitted_train_examples, admitted_train_features),
        (
            "validation",
            admitted_evaluation_examples,
            admitted_evaluation_features,
        ),
    )
    candidates: list[AdmissionProbe] = []
    counts: dict[str, int] = {}
    seen_example_ids: set[str] = set()
    for source, examples, features in pairs:
        if len(examples) != len(features):
            raise AdapterAdmissionError(
                f"admitted {source} examples/features have different lengths"
            )
        if not examples:
            raise AdapterAdmissionError(
                "final admission requires non-empty train and validation data"
            )
        counts[source] = len(examples)
        for example, feature in zip(examples, features, strict=True):
            if example.example_id in seen_example_ids:
                raise AdapterAdmissionError(
                    "admitted probe population contains a duplicate example id"
                )
            seen_example_ids.add(example.example_id)
            candidates.append(
                _candidate_probe(
                    source=source,
                    example=example,
                    feature=feature,
                    max_length=max_length,
                    selection_binding_sha256=selection_binding_sha256,
                )
            )
    if len(candidates) < count:
        raise AdapterAdmissionError("admitted population is smaller than probe count")
    if len({candidate.candidate_sha256 for candidate in candidates}) != len(candidates):
        raise AdapterAdmissionError("admitted population contains duplicate candidates")

    ordered = sorted(
        candidates,
        key=lambda candidate: (
            candidate.rank_sha256,
            candidate.candidate_sha256,
        ),
    )
    selected = [
        min(
            (candidate for candidate in candidates if candidate.source == source),
            key=lambda candidate: (
                candidate.rank_sha256,
                candidate.candidate_sha256,
            ),
        )
        for source in ("train", "validation")
    ]
    selected_digests = {candidate.candidate_sha256 for candidate in selected}
    for candidate in ordered:
        if len(selected) == count:
            break
        if candidate.candidate_sha256 not in selected_digests:
            selected.append(candidate)
            selected_digests.add(candidate.candidate_sha256)
    selected.sort(key=lambda candidate: (candidate.rank_sha256, candidate.candidate_sha256))

    population_records = sorted(
        (
            {
                "source": candidate.source,
                "example_id": candidate.example.example_id,
                "candidate_sha256": candidate.candidate_sha256,
                "rank_sha256": candidate.rank_sha256,
            }
            for candidate in candidates
        ),
        key=lambda record: (record["candidate_sha256"], record["source"]),
    )
    return AdmissionProbePlan(
        max_length=max_length,
        selection_binding_sha256=selection_binding_sha256,
        candidate_population_sha256=sha256_json(population_records),
        candidate_count=len(candidates),
        train_candidate_count=counts["train"],
        validation_candidate_count=counts["validation"],
        probes=tuple(selected),
    )


def _tensor_raw_sha256(torch: Any, tensor: Any) -> str:
    raw = tensor.detach().contiguous().view(torch.uint8).cpu().numpy()
    return hashlib.sha256(raw).hexdigest()


def canonical_tensor_population_fingerprint(
    state: Mapping[str, Any],
    *,
    torch_module: Any | None = None,
) -> TensorPopulationFingerprint:
    """Hash an already canonical PEFT state mapping without renaming keys."""

    if torch_module is None:
        import torch as torch_module

    if not isinstance(state, Mapping) or not state:
        raise AdapterAdmissionError("canonical PEFT state must be non-empty")
    records: list[dict[str, object]] = []
    names: list[str] = []
    for name in sorted(state):
        if type(name) is not str or not name or "\n" in name or "\r" in name:
            raise AdapterAdmissionError(
                "canonical PEFT state names must be unique non-empty one-line text"
            )
        tensor = state[name]
        if not torch_module.is_tensor(tensor):
            raise AdapterAdmissionError(f"canonical PEFT value {name!r} is not a tensor")
        if getattr(tensor, "layout", None) != torch_module.strided:
            raise AdapterAdmissionError(
                f"canonical PEFT tensor {name!r} is not strided"
            )
        if not bool(torch_module.isfinite(tensor.detach()).all().cpu()):
            raise AdapterAdmissionError(
                f"canonical PEFT tensor {name!r} contains a non-finite value"
            )
        names.append(name)
        records.append(
            {
                "name": name,
                "dtype": str(tensor.dtype),
                "shape": list(tensor.shape),
                "content_sha256": _tensor_raw_sha256(torch_module, tensor),
            }
        )
    return TensorPopulationFingerprint(
        tensor_count=len(records),
        names_sha256=sha256_json(names),
        population_sha256=sha256_json(records),
    )


def _tensor_value_fingerprint(torch: Any, tensor: Any) -> TensorValueFingerprint:
    if not torch.is_tensor(tensor) or tensor.ndim != 3:
        raise AdapterAdmissionError("policy projected logits must be a rank-3 tensor")
    if not bool(torch.isfinite(tensor.detach()).all().cpu()):
        raise AdapterAdmissionError("policy projected logits contain non-finite values")
    header = json.dumps(
        {"dtype": str(tensor.dtype), "shape": list(tensor.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\n")
    digest.update(tensor.detach().contiguous().view(torch.uint8).cpu().numpy())
    return TensorValueFingerprint(
        dtype=str(tensor.dtype),
        shape=tuple(tensor.shape),
        sha256=digest.hexdigest(),
    )


def _tokenizer_identity(tokenizer: Any, contract: BaseReloadContract) -> dict[str, object]:
    eos = getattr(tokenizer, "eos_token_id", None)
    pad = getattr(tokenizer, "pad_token_id", None)
    if (
        type(eos) is not int
        or eos < 0
        or type(pad) is not int
        or pad < 0
        or getattr(tokenizer, "padding_side", None) != "right"
    ):
        raise AdapterAdmissionError(
            "admission tokenizer needs non-negative EOS/pad ids and right padding"
        )
    try:
        size = len(tokenizer)
    except (TypeError, ValueError) as exc:
        raise AdapterAdmissionError("admission tokenizer has no finite vocabulary") from exc
    if type(size) is not int or size < 1:
        raise AdapterAdmissionError("admission tokenizer has no finite vocabulary")
    record = {
        "class": type(tokenizer).__name__,
        "commit": contract.revision,
        "special_tokens": getattr(tokenizer, "special_tokens_map", None),
        "vocab_size": size,
    }
    try:
        sha256_json(record)
    except (TypeError, ValueError) as exc:
        raise AdapterAdmissionError("tokenizer identity is not canonical JSON") from exc
    return record


def _verify_probe_encodings(
    tokenizer: Any,
    plan: AdmissionProbePlan,
) -> None:
    for probe in plan.probes:
        encoded = tokenize_completion(
            probe.example,
            tokenizer,
            max_length=plan.max_length,
        )
        if ProbeFeature.from_mapping(
            encoded,
            max_length=plan.max_length,
        ) != probe.feature:
            raise AdapterAdmissionError(
                f"tokenizer changed admission probe {probe.example.example_id!r}"
            )


def _model_device(model: Any) -> Any:
    try:
        return next(model.parameters()).device
    except (AttributeError, StopIteration, TypeError) as exc:
        raise AdapterAdmissionError("policy model has no parameter device") from exc


def _evaluate_probe(
    model: Any,
    probe: AdmissionProbe,
    *,
    torch: Any,
    device: Any,
) -> ProbeOutputFingerprint:
    feature = probe.feature
    batch = {
        "input_ids": torch.tensor([feature.input_ids], dtype=torch.long, device=device),
        "attention_mask": torch.tensor(
            [feature.attention_mask], dtype=torch.long, device=device
        ),
        "labels": torch.tensor([feature.labels], dtype=torch.long, device=device),
    }
    projection = completion_projection(batch["labels"], batch["attention_mask"])
    with torch.inference_mode():
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            logits_to_keep=projection.positions,
        )
        logits = (
            outputs.get("logits")
            if isinstance(outputs, Mapping)
            else getattr(outputs, "logits", None)
        )
        if logits is None:
            raise AdapterAdmissionError("policy model returned no projected logits")
        loss = indexed_completion_cross_entropy(logits, projection)
    loss_value = float(loss.detach().float().cpu())
    if not math.isfinite(loss_value):
        raise AdapterAdmissionError("policy admission loss is non-finite")
    return ProbeOutputFingerprint(
        probe_sha256=probe.candidate_sha256,
        loss_hex=loss_value.hex(),
        projected_logits=_tensor_value_fingerprint(torch, logits),
    )


def _evaluate_plan(
    model: Any,
    plan: AdmissionProbePlan,
    *,
    torch: Any,
    device: Any | None,
) -> tuple[ProbeOutputFingerprint, ...]:
    model.eval()
    if getattr(model, "training", None) is not False:
        raise AdapterAdmissionError("policy model did not enter evaluation mode")
    resolved_device = _model_device(model) if device is None else device
    return tuple(
        _evaluate_probe(
            model,
            probe,
            torch=torch,
            device=resolved_device,
        )
        for probe in plan.probes
    )


def canonical_peft_adapter_state(
    model: Any,
    *,
    get_peft_model_state_dict: Callable[..., Mapping[str, Any]] | None = None,
) -> Mapping[str, Any]:
    """Return PEFT 0.16's save-format state for exactly the default adapter.

    ``save_embedding_layers=False`` is intentional for the pinned LoRA policy:
    embeddings are neither resized nor adapter targets.  PEFT removes the
    ``.default`` name segment in this public function before safetensors save,
    so its keys are the canonical persisted names.
    """

    if get_peft_model_state_dict is None:
        from peft import get_peft_model_state_dict

    configs = getattr(model, "peft_config", None)
    if not isinstance(configs, Mapping) or set(configs) != {ADAPTER_NAME}:
        raise AdapterAdmissionError(
            "admission requires exactly one PEFT adapter named 'default'"
        )
    state = get_peft_model_state_dict(
        model,
        adapter_name=ADAPTER_NAME,
        save_embedding_layers=False,
    )
    if not isinstance(state, Mapping):
        raise AdapterAdmissionError("PEFT returned a malformed canonical state")
    return state


def capture_in_memory_policy(
    *,
    model: Any,
    tokenizer: Any,
    plan: AdmissionProbePlan,
    base_contract: BaseReloadContract,
    canonical_adapter_state: Mapping[str, Any] | None = None,
    get_peft_model_state_dict: Callable[..., Mapping[str, Any]] | None = None,
    torch_module: Any | None = None,
    device: Any | None = None,
) -> InMemoryPolicySnapshot:
    """Capture compact final-policy fingerprints before releasing Trainer."""

    if torch_module is None:
        import torch as torch_module

    _validate_probe_plan(plan)
    _verify_probe_encodings(tokenizer, plan)
    tokenizer_digest = sha256_json(_tokenizer_identity(tokenizer, base_contract))
    state = (
        canonical_adapter_state
        if canonical_adapter_state is not None
        else canonical_peft_adapter_state(
            model,
            get_peft_model_state_dict=get_peft_model_state_dict,
        )
    )
    population = canonical_tensor_population_fingerprint(
        state,
        torch_module=torch_module,
    )
    outputs = _evaluate_plan(
        model,
        plan,
        torch=torch_module,
        device=device,
    )
    return InMemoryPolicySnapshot(
        base_contract_sha256=base_contract.sha256,
        probe_set_sha256=plan.probe_set_sha256,
        tokenizer_identity_sha256=tokenizer_digest,
        adapter_population=population,
        outputs=outputs,
    )


def _artifact_digest(
    expected: Mapping[str, Any],
    path: str,
    label: str,
) -> str:
    files = expected.get("files")
    if type(files) is not dict:
        raise AdapterAdmissionError(f"{label} artifact record is malformed")
    return _sha256(files.get(path), f"{label} artifact {path} hash")


def _admission_evidence(
    *,
    plan: AdmissionProbePlan,
    snapshot: InMemoryPolicySnapshot,
    base_contract: BaseReloadContract,
    adapter_artifacts: Mapping[str, Any],
    tokenizer_artifacts: Mapping[str, Any],
    fresh_outputs: tuple[ProbeOutputFingerprint, ...],
    differs_from_base_count: int,
    device: str,
) -> dict[str, object]:
    adapter_digest = _sha256(adapter_artifacts.get("sha256"), "adapter hash")
    tokenizer_digest = _sha256(tokenizer_artifacts.get("sha256"), "tokenizer hash")
    evidence: dict[str, object] = {
        "format": ADMISSION_FORMAT,
        "v": ADMISSION_VERSION,
        "status": "passed",
        "base_model": base_contract.record(),
        "artifacts": {
            "adapter_sha256": adapter_digest,
            "adapter_config_sha256": _artifact_digest(
                adapter_artifacts,
                f"{ADAPTER_SUBDIR}/adapter_config.json",
                "adapter",
            ),
            "adapter_safetensors_sha256": _artifact_digest(
                adapter_artifacts,
                f"{ADAPTER_SUBDIR}/adapter_model.safetensors",
                "adapter",
            ),
            "tokenizer_sha256": tokenizer_digest,
        },
        "probes": {
            "selection_method": PROBE_SELECTION_METHOD,
            "selection_binding_sha256": plan.selection_binding_sha256,
            "candidate_population_sha256": plan.candidate_population_sha256,
            "candidate_count": plan.candidate_count,
            "train_candidate_count": plan.train_candidate_count,
            "validation_candidate_count": plan.validation_candidate_count,
            "count": len(plan.probes),
            "set_sha256": plan.probe_set_sha256,
            "records": list(plan.compact_records),
            "original_outputs_sha256": snapshot.outputs_sha256,
            "fresh_outputs_sha256": sha256_json(
                [output.record() for output in fresh_outputs]
            ),
        },
        "adapter_tensors": snapshot.adapter_population.record(),
        "reload": {
            "base_model_loads": 1,
            "adapter_loads": 1,
            "tokenizer_loads": 1,
            "adapter_safetensor_reads": 1,
            "adapter_name": ADAPTER_NAME,
            "device": device,
        },
        "checks": {
            "tokenizer_encoding_count": len(plan.probes),
            "exact_reload_count": len(fresh_outputs),
            "differs_from_base_count": differs_from_base_count,
        },
        "hash_contract": {
            "algorithm": "sha256",
            "canonicalization": HASH_CANONICALIZATION,
            "tensor_population": TENSOR_POPULATION_HASH_FORMAT,
            "projected_logits": PROJECTED_LOGITS_HASH_FORMAT,
            "output_set": OUTPUT_SET_HASH_FORMAT,
        },
    }
    evidence["content_sha256"] = sha256_json(evidence)
    validate_adapter_admission_evidence(evidence)
    return evidence


def admit_loaded_policy(
    *,
    reloaded_model: Any,
    reloaded_tokenizer: Any,
    saved_adapter_state: Mapping[str, Any],
    reloaded_adapter_state: Mapping[str, Any],
    plan: AdmissionProbePlan,
    snapshot: InMemoryPolicySnapshot,
    base_contract: BaseReloadContract,
    adapter_artifacts: Mapping[str, Any],
    tokenizer_artifacts: Mapping[str, Any],
    torch_module: Any | None = None,
    device: Any | None = None,
    device_label: str = "cuda:0",
) -> dict[str, object]:
    """Compare freshly loaded objects with a compact pre-release snapshot."""

    if torch_module is None:
        import torch as torch_module

    _validate_probe_plan(plan)
    if snapshot.base_contract_sha256 != base_contract.sha256:
        raise AdapterAdmissionError("snapshot names a different base contract")
    if snapshot.probe_set_sha256 != plan.probe_set_sha256:
        raise AdapterAdmissionError("snapshot names a different admission probe set")
    if len(snapshot.outputs) != len(plan.probes):
        raise AdapterAdmissionError("snapshot has the wrong number of probe outputs")
    _verify_probe_encodings(reloaded_tokenizer, plan)
    fresh_tokenizer_digest = sha256_json(
        _tokenizer_identity(reloaded_tokenizer, base_contract)
    )
    if fresh_tokenizer_digest != snapshot.tokenizer_identity_sha256:
        raise AdapterAdmissionError("closed tokenizer identity changed after save")

    saved_population = canonical_tensor_population_fingerprint(
        saved_adapter_state,
        torch_module=torch_module,
    )
    fresh_population = canonical_tensor_population_fingerprint(
        reloaded_adapter_state,
        torch_module=torch_module,
    )
    if saved_population != snapshot.adapter_population:
        raise AdapterAdmissionError(
            "saved safetensors differ from the final in-memory PEFT state"
        )
    if fresh_population != saved_population:
        raise AdapterAdmissionError(
            "fresh PEFT model did not populate the exact saved adapter tensors"
        )

    fresh_outputs = _evaluate_plan(
        reloaded_model,
        plan,
        torch=torch_module,
        device=device,
    )
    for reference, fresh in zip(snapshot.outputs, fresh_outputs, strict=True):
        if fresh != reference:
            raise AdapterAdmissionError(
                "fresh adapter changed indexed loss or projected logits"
            )

    disable_adapter = getattr(reloaded_model, "disable_adapter", None)
    if not callable(disable_adapter):
        raise AdapterAdmissionError("fresh PEFT model cannot disable its adapter")
    context = disable_adapter()
    if not isinstance(context, AbstractContextManager):
        raise AdapterAdmissionError("PEFT disable_adapter did not return a context")
    with context:
        base_outputs = _evaluate_plan(
            reloaded_model,
            plan,
            torch=torch_module,
            device=device,
        )
    differs = sum(
        fresh.projected_logits != base.projected_logits
        for fresh, base in zip(fresh_outputs, base_outputs, strict=True)
    )
    if differs < 1:
        raise AdapterAdmissionError(
            "fresh adapter is indistinguishable from disabled base on all probes"
        )
    return _admission_evidence(
        plan=plan,
        snapshot=snapshot,
        base_contract=base_contract,
        adapter_artifacts=adapter_artifacts,
        tokenizer_artifacts=tokenizer_artifacts,
        fresh_outputs=fresh_outputs,
        differs_from_base_count=differs,
        device=_text(device_label, "admission device"),
    )


def _heavy_dependencies() -> AdapterAdmissionDependencies:
    import torch
    from peft import PeftModel, get_peft_model_state_dict
    from safetensors import safe_open
    from transformers import AutoModelForCausalLM, AutoTokenizer

    return AdapterAdmissionDependencies(
        torch=torch,
        AutoModelForCausalLM=AutoModelForCausalLM,
        AutoTokenizer=AutoTokenizer,
        PeftModel=PeftModel,
        get_peft_model_state_dict=get_peft_model_state_dict,
        safe_open=safe_open,
    )


def _read_saved_adapter_state(
    path: Path,
    *,
    dependencies: AdapterAdmissionDependencies,
) -> dict[str, Any]:
    try:
        with dependencies.safe_open(
            str(path),
            framework="pt",
            device="cpu",
        ) as handle:
            names = tuple(sorted(handle.keys()))
            if not names:
                raise AdapterAdmissionError("saved adapter safetensors is empty")
            return {name: handle.get_tensor(name) for name in names}
    except AdapterAdmissionError:
        raise
    except Exception as exc:
        raise AdapterAdmissionError(
            f"cannot read saved adapter safetensors: {exc}"
        ) from exc


def admit_saved_adapter(
    *,
    output_dir: Path,
    adapter_artifacts: Mapping[str, Any],
    tokenizer_artifacts: Mapping[str, Any],
    plan: AdmissionProbePlan,
    snapshot: InMemoryPolicySnapshot,
    base_contract: BaseReloadContract,
    device: str = "cuda:0",
    dependencies: AdapterAdmissionDependencies | None = None,
) -> dict[str, object]:
    """Fresh-load and admit the actual closed final adapter/tokenizer trees.

    The API intentionally receives only the compact snapshot, never the
    original model or Trainer.  Callers should delete those objects and clear
    CUDA memory before entering this phase.  All loader-visible artifacts are
    hash-checked both before and after the fresh semantic run.
    """

    root = Path(output_dir)
    _validate_probe_plan(plan)
    if snapshot.base_contract_sha256 != base_contract.sha256:
        raise AdapterAdmissionError("saved-adapter reload uses a different base")
    require_safetensors_adapter(adapter_artifacts)
    adapter_dir = verify_artifact_directory(
        root,
        adapter_artifacts,
        ADAPTER_SUBDIR,
        require_protected=True,
    )
    tokenizer_dir = verify_artifact_directory(
        root,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=True,
    )
    deps = dependencies or _heavy_dependencies()
    torch = deps.torch
    saved_state = _read_saved_adapter_state(
        adapter_dir / "adapter_model.safetensors",
        dependencies=deps,
    )

    gc.collect()
    if device.startswith("cuda") and bool(torch.cuda.is_available()):
        torch.cuda.empty_cache()

    tokenizer = None
    base = None
    reloaded = None
    try:
        tokenizer = deps.AutoTokenizer.from_pretrained(
            tokenizer_dir,
            use_fast=True,
            trust_remote_code=False,
            local_files_only=True,
        )
        base = deps.AutoModelForCausalLM.from_pretrained(
            base_contract.model_id,
            revision=base_contract.revision,
            torch_dtype=torch.bfloat16,
            attn_implementation=base_contract.attention,
            trust_remote_code=False,
            use_safetensors=True,
            local_files_only=True,
        )
        resolved = (
            getattr(getattr(base, "config", None), "_commit_hash", None)
            or base_contract.revision
        )
        if resolved != base_contract.revision:
            raise AdapterAdmissionError(
                "fresh base model resolved to a different immutable revision"
            )
        config = getattr(base, "config", None)
        if config is None or not callable(getattr(config, "to_dict", None)):
            raise AdapterAdmissionError("fresh base model has no configuration")
        if sha256_json(config.to_dict()) != base_contract.config_sha256:
            raise AdapterAdmissionError("fresh base configuration changed")
        require_indexed_logits_support(base)
        config.use_cache = False
        reloaded = deps.PeftModel.from_pretrained(
            base,
            adapter_dir,
            adapter_name=ADAPTER_NAME,
            is_trainable=False,
            autocast_adapter_dtype=True,
            low_cpu_mem_usage=False,
            local_files_only=True,
        ).to(device)
        fresh_state = canonical_peft_adapter_state(
            reloaded,
            get_peft_model_state_dict=deps.get_peft_model_state_dict,
        )
        evidence = admit_loaded_policy(
            reloaded_model=reloaded,
            reloaded_tokenizer=tokenizer,
            saved_adapter_state=saved_state,
            reloaded_adapter_state=fresh_state,
            plan=plan,
            snapshot=snapshot,
            base_contract=base_contract,
            adapter_artifacts=adapter_artifacts,
            tokenizer_artifacts=tokenizer_artifacts,
            torch_module=torch,
            device=device,
            device_label=device,
        )
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
        return evidence
    finally:
        del reloaded, base, tokenizer, saved_state
        gc.collect()
        if device.startswith("cuda") and bool(torch.cuda.is_available()):
            torch.cuda.empty_cache()


def _validate_probe_plan(plan: AdmissionProbePlan) -> None:
    if type(plan) is not AdmissionProbePlan:
        raise AdapterAdmissionError("admission probe plan has the wrong type")
    _sha256(plan.selection_binding_sha256, "probe selection binding")
    _sha256(plan.candidate_population_sha256, "candidate population hash")
    if type(plan.max_length) is not int or plan.max_length < 2:
        raise AdapterAdmissionError("probe plan max_length is invalid")
    count = len(plan.probes)
    if not PROBE_MINIMUM <= count <= PROBE_MAXIMUM:
        raise AdapterAdmissionError("probe plan must contain two or three probes")
    if (
        type(plan.candidate_count) is not int
        or type(plan.train_candidate_count) is not int
        or type(plan.validation_candidate_count) is not int
        or plan.train_candidate_count < 1
        or plan.validation_candidate_count < 1
        or plan.candidate_count
        != plan.train_candidate_count + plan.validation_candidate_count
        or plan.candidate_count < count
    ):
        raise AdapterAdmissionError("probe plan candidate counts are inconsistent")
    if {probe.source for probe in plan.probes} != {"train", "validation"}:
        raise AdapterAdmissionError("probe plan must represent train and validation")
    if len({probe.candidate_sha256 for probe in plan.probes}) != count:
        raise AdapterAdmissionError("probe plan contains duplicate probes")
    if tuple(plan.probes) != tuple(
        sorted(
            plan.probes,
            key=lambda probe: (probe.rank_sha256, probe.candidate_sha256),
        )
    ):
        raise AdapterAdmissionError("probe plan is not in canonical rank order")
    for probe in plan.probes:
        _sha256(probe.example_sha256, "probe example hash")
        _sha256(probe.candidate_sha256, "probe candidate hash")
        _sha256(probe.rank_sha256, "probe rank hash")
        if probe.example_sha256 != _example_sha256(probe.example):
            raise AdapterAdmissionError("probe example content changed after selection")
        expected_candidate = sha256_json(
            {
                "source": probe.source,
                "example_sha256": probe.example_sha256,
                "feature_sha256": probe.feature.sha256,
            }
        )
        expected_rank = sha256_json(
            {
                "method": PROBE_SELECTION_METHOD,
                "selection_binding_sha256": plan.selection_binding_sha256,
                "candidate_sha256": expected_candidate,
            }
        )
        if (
            probe.candidate_sha256 != expected_candidate
            or probe.rank_sha256 != expected_rank
        ):
            raise AdapterAdmissionError("probe selection hash chain is inconsistent")


def validate_adapter_admission_evidence(
    value: object,
) -> dict[str, object]:
    """Validate the exact compact JSON schema and all internal count/hash joins."""

    root_keys = {
        "format",
        "v",
        "status",
        "base_model",
        "artifacts",
        "probes",
        "adapter_tensors",
        "reload",
        "checks",
        "hash_contract",
        "content_sha256",
    }
    root = _exact_mapping(value, root_keys, "adapter admission evidence")
    if (
        root.get("format") != ADMISSION_FORMAT
        or root.get("v") != ADMISSION_VERSION
        or root.get("status") != "passed"
    ):
        raise AdapterAdmissionError("adapter admission header is invalid")
    base = _exact_mapping(
        root["base_model"],
        {
            "id",
            "requested_revision",
            "resolved_snapshot_hash",
            "config_sha256",
            "dtype",
            "attention",
            "trust_remote_code",
        },
        "admitted base model",
    )
    contract = BaseReloadContract(
        model_id=_text(base["id"], "admitted base model id"),
        revision=_text(base["requested_revision"], "admitted base revision"),
        config_sha256=_sha256(base["config_sha256"], "admitted base config hash"),
        dtype=base["dtype"],
        attention=base["attention"],
        trust_remote_code=base["trust_remote_code"],
    )
    if dict(base) != contract.record():
        raise AdapterAdmissionError("admitted base record is not canonical")

    artifacts = _exact_mapping(
        root["artifacts"],
        {
            "adapter_sha256",
            "adapter_config_sha256",
            "adapter_safetensors_sha256",
            "tokenizer_sha256",
        },
        "admission artifact hashes",
    )
    for key, digest in artifacts.items():
        _sha256(digest, f"admission {key}")

    probes = _exact_mapping(
        root["probes"],
        {
            "selection_method",
            "selection_binding_sha256",
            "candidate_population_sha256",
            "candidate_count",
            "train_candidate_count",
            "validation_candidate_count",
            "count",
            "set_sha256",
            "records",
            "original_outputs_sha256",
            "fresh_outputs_sha256",
        },
        "admission probes",
    )
    if probes["selection_method"] != PROBE_SELECTION_METHOD:
        raise AdapterAdmissionError("admission probe selection method changed")
    for key in (
        "selection_binding_sha256",
        "candidate_population_sha256",
        "set_sha256",
        "original_outputs_sha256",
        "fresh_outputs_sha256",
    ):
        _sha256(probes[key], f"admission probe {key}")
    count = _positive_int(probes["count"], "admission probe count")
    if not PROBE_MINIMUM <= count <= PROBE_MAXIMUM:
        raise AdapterAdmissionError("admission evidence must bind two or three probes")
    candidate_count = _positive_int(
        probes["candidate_count"], "admission candidate count"
    )
    train_count = _positive_int(
        probes["train_candidate_count"], "admission train candidate count"
    )
    validation_count = _positive_int(
        probes["validation_candidate_count"],
        "admission validation candidate count",
    )
    if candidate_count != train_count + validation_count or candidate_count < count:
        raise AdapterAdmissionError("admission candidate counts are inconsistent")
    records = probes["records"]
    if type(records) is not list or len(records) != count:
        raise AdapterAdmissionError("admission probe records have the wrong length")
    sources: set[str] = set()
    candidate_digests: set[str] = set()
    for record_value in records:
        record = _exact_mapping(
            record_value,
            _PROBE_RECORD_KEYS,
            "admission probe record",
        )
        source = record["source"]
        if source not in {"train", "validation"}:
            raise AdapterAdmissionError("admission probe source is invalid")
        sources.add(source)
        _text(record["example_id"], "admission probe example id")
        for key in (
            "example_sha256",
            "feature_sha256",
            "candidate_sha256",
            "rank_sha256",
        ):
            _sha256(record[key], f"admission probe {key}")
        expected_candidate = sha256_json(
            {
                "source": source,
                "example_sha256": record["example_sha256"],
                "feature_sha256": record["feature_sha256"],
            }
        )
        expected_rank = sha256_json(
            {
                "method": PROBE_SELECTION_METHOD,
                "selection_binding_sha256": probes[
                    "selection_binding_sha256"
                ],
                "candidate_sha256": expected_candidate,
            }
        )
        if (
            record["candidate_sha256"] != expected_candidate
            or record["rank_sha256"] != expected_rank
        ):
            raise AdapterAdmissionError(
                "admission probe record hash chain is inconsistent"
            )
        candidate_digests.add(record["candidate_sha256"])
    if sources != {"train", "validation"} or len(candidate_digests) != count:
        raise AdapterAdmissionError("admission probe records are not stratified/unique")
    if sha256_json(records) != probes["set_sha256"]:
        raise AdapterAdmissionError("admission probe-set hash is inconsistent")
    if records != sorted(
        records,
        key=lambda record: (record["rank_sha256"], record["candidate_sha256"]),
    ):
        raise AdapterAdmissionError("admission probes are not in canonical rank order")
    if probes["original_outputs_sha256"] != probes["fresh_outputs_sha256"]:
        raise AdapterAdmissionError("admission output hashes do not match")

    tensors = _exact_mapping(
        root["adapter_tensors"],
        {
            "format",
            "v",
            "tensor_count",
            "names_sha256",
            "population_sha256",
            "population_hash_format",
        },
        "admission tensor population",
    )
    if (
        tensors["format"] != TENSOR_POPULATION_FORMAT
        or tensors["v"] != TENSOR_POPULATION_VERSION
        or tensors["population_hash_format"] != TENSOR_POPULATION_HASH_FORMAT
    ):
        raise AdapterAdmissionError("admission tensor population contract changed")
    _positive_int(tensors["tensor_count"], "admission adapter tensor count")
    _sha256(tensors["names_sha256"], "admission adapter names hash")
    _sha256(tensors["population_sha256"], "admission adapter population hash")

    reload = _exact_mapping(
        root["reload"],
        {
            "base_model_loads",
            "adapter_loads",
            "tokenizer_loads",
            "adapter_safetensor_reads",
            "adapter_name",
            "device",
        },
        "admission reload counts",
    )
    if any(
        reload[key] != 1
        for key in (
            "base_model_loads",
            "adapter_loads",
            "tokenizer_loads",
            "adapter_safetensor_reads",
        )
    ) or reload["adapter_name"] != ADAPTER_NAME:
        raise AdapterAdmissionError("admission did not perform exactly one fresh reload")
    _text(reload["device"], "admission reload device")

    checks = _exact_mapping(
        root["checks"],
        {
            "tokenizer_encoding_count",
            "exact_reload_count",
            "differs_from_base_count",
        },
        "admission checks",
    )
    if (
        checks["tokenizer_encoding_count"] != count
        or checks["exact_reload_count"] != count
        or type(checks["differs_from_base_count"]) is not int
        or not 1 <= checks["differs_from_base_count"] <= count
    ):
        raise AdapterAdmissionError("admission check counts are inconsistent")

    hashes = _exact_mapping(
        root["hash_contract"],
        {
            "algorithm",
            "canonicalization",
            "tensor_population",
            "projected_logits",
            "output_set",
        },
        "admission hash contract",
    )
    if dict(hashes) != {
        "algorithm": "sha256",
        "canonicalization": HASH_CANONICALIZATION,
        "tensor_population": TENSOR_POPULATION_HASH_FORMAT,
        "projected_logits": PROJECTED_LOGITS_HASH_FORMAT,
        "output_set": OUTPUT_SET_HASH_FORMAT,
    }:
        raise AdapterAdmissionError("admission hash contract changed")
    content = _sha256(root["content_sha256"], "adapter admission content hash")
    without_content = dict(root)
    del without_content["content_sha256"]
    if sha256_json(without_content) != content:
        raise AdapterAdmissionError("adapter admission content hash is inconsistent")
    # A final allow_nan=False serialization check also rejects unexpected
    # framework objects nested inside an otherwise schema-valid record.
    try:
        json.dumps(root, allow_nan=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise AdapterAdmissionError("adapter admission is not strict JSON") from exc
    return dict(root)


def validate_manifest_adapter_admission(
    manifest: object,
) -> dict[str, object]:
    """Join saved-policy admission to every independent manifest authority.

    The semantic evidence is intentionally useful on its own, but deployment
    must additionally prove that it names the *same* base snapshot, final
    artifact trees, run identity, CUDA device, and completed-training artifact
    hashes as the enclosing manifest.
    """

    if type(manifest) is not dict or manifest.get("prompt_version") != PEANO_PROMPT_V3:
        raise AdapterAdmissionError(
            "adapter admission applies only to an exact model-v3 manifest"
        )
    evidence = validate_adapter_admission_evidence(
        manifest.get("adapter_admission")
    )
    base = manifest.get("base_model")
    runtime = manifest.get("runtime")
    adapter = manifest.get("adapter")
    tokenizer = manifest.get("tokenizer")
    inputs = manifest.get("inputs")
    completed = manifest.get("training_evidence")
    if not all(
        type(value) is dict
        for value in (base, runtime, adapter, tokenizer, inputs, completed)
    ):
        raise AdapterAdmissionError(
            "model-v3 manifest lacks an adapter-admission join authority"
        )
    trainer_runtime = runtime.get("trainer")
    tokenizer_artifacts = tokenizer.get("artifacts")
    run_identity = inputs.get("run_identity")
    completed_artifacts = completed.get("artifacts")
    if not all(
        type(value) is dict
        for value in (
            trainer_runtime,
            tokenizer_artifacts,
            run_identity,
            completed_artifacts,
        )
    ):
        raise AdapterAdmissionError(
            "model-v3 manifest has malformed adapter-admission authorities"
        )

    expected_base = {
        "id": base.get("id"),
        "requested_revision": base.get("requested_revision"),
        "resolved_snapshot_hash": base.get("resolved_snapshot_hash"),
        "config_sha256": base.get("config_sha256"),
        "dtype": runtime.get("dtype"),
        "attention": runtime.get("attention"),
        "trust_remote_code": False,
    }
    admitted_artifacts = evidence["artifacts"]
    adapter_files = adapter.get("files")
    if (
        evidence.get("base_model") != expected_base
        or evidence["reload"].get("device") != "cuda:0"
        or trainer_runtime.get("device") != {"type": "cuda", "index": 0}
        or evidence["probes"].get("selection_binding_sha256")
        != run_identity.get("sha256")
        or type(adapter_files) is not dict
        or admitted_artifacts.get("adapter_sha256") != adapter.get("sha256")
        or admitted_artifacts.get("adapter_config_sha256")
        != adapter_files.get(f"{ADAPTER_SUBDIR}/adapter_config.json")
        or admitted_artifacts.get("adapter_safetensors_sha256")
        != adapter_files.get(f"{ADAPTER_SUBDIR}/adapter_model.safetensors")
        or admitted_artifacts.get("tokenizer_sha256")
        != tokenizer_artifacts.get("sha256")
        or completed_artifacts
        != {
            "adapter_sha256": adapter.get("sha256"),
            "tokenizer_sha256": tokenizer_artifacts.get("sha256"),
        }
    ):
        raise AdapterAdmissionError(
            "adapter admission differs from its enclosing model-v3 manifest"
        )
    return evidence


def require_adapter_admission_for_prompt(
    manifest: object,
) -> dict[str, object] | None:
    """Gate model-v3 deployment while preserving legacy v1/v2 adapters."""

    if type(manifest) is dict and manifest.get("prompt_version") == PEANO_PROMPT_V3:
        return validate_manifest_adapter_admission(manifest)
    return None


__all__ = [
    "ADMISSION_FORMAT",
    "ADMISSION_VERSION",
    "AdapterAdmissionDependencies",
    "AdapterAdmissionError",
    "AdmissionProbePlan",
    "BaseReloadContract",
    "InMemoryPolicySnapshot",
    "admit_loaded_policy",
    "admit_saved_adapter",
    "canonical_peft_adapter_state",
    "canonical_tensor_population_fingerprint",
    "capture_in_memory_policy",
    "require_adapter_admission_for_prompt",
    "select_admission_probes",
    "validate_adapter_admission_evidence",
    "validate_manifest_adapter_admission",
]
