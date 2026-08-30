"""Strict, source-bound loading for the model-v3 training curriculum.

The dataset builder and :mod:`training.peano_policy.data` remain the authority
for positive SFT rows.  This module adds one deliberately narrow operation:
load the complete ``train.jsonl`` artifact, adapt every validated row to the
model-v3 selector, and bind the resulting selection to the exact split and
manifest bytes from which it was derived.

No row is rewritten or normalized.  Builder JSON must already use the exact
encoding emitted by ``build_peano_policy_dataset.py``; otherwise loading fails.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from .data import (
    MAX_DATASET_LINE_BYTES,
    _decode_json,
    dataset_manifest_path,
    load_examples,
)
from .manifest import sha256_file
from .prompt import ProofExample, PromptError
from .selection import (
    MODEL_V3_SELECTION_CONTRACT,
    MODEL_V3_SYNTHETIC_ROW_CEILING,
    SELECTION_ALGORITHM,
    SELECTION_FORMAT,
    SELECTION_VERSION,
    CurriculumSelectionContract,
    canonical_selection_json,
    row_from_validated_record,
    select_curriculum,
)


CURRICULUM_FORMAT = "peano-policy-v3-curriculum"
CURRICULUM_VERSION = 1
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class CurriculumLoadError(ValueError):
    """A loaded curriculum or its immutable attestation is inconsistent."""


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise CurriculumLoadError(
            f"curriculum evidence is not canonical JSON: {exc}"
        ) from exc


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def curriculum_record_sha256(record: Mapping[str, object]) -> str:
    """Recompute the self-excluding digest of a curriculum attestation."""

    if not isinstance(record, Mapping):
        raise CurriculumLoadError("curriculum record must be a mapping")
    core = dict(record)
    claimed = core.pop("curriculum_sha256", None)
    if type(claimed) is not str or _SHA256_RE.fullmatch(claimed) is None:
        raise CurriculumLoadError("curriculum record has no valid digest")
    return _sha256_json(core)


def canonical_curriculum_json(record: Mapping[str, object]) -> str:
    """Validate and serialize one curriculum record as canonical JSONL."""

    claimed = record.get("curriculum_sha256")
    if curriculum_record_sha256(record) != claimed:
        raise CurriculumLoadError("curriculum record digest mismatch")
    return _canonical_json_bytes(record).decode("utf-8") + "\n"


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise CurriculumLoadError(f"{label} must be lowercase SHA-256")
    return value


def _example_record(example: ProofExample) -> dict[str, str]:
    return {
        "example_id": example.example_id,
        "prompt": example.prompt,
        "completion": example.completion,
        "environment_sha256": example.environment_sha256,
    }


def _validate_attestation(
    record: object,
    examples: tuple[ProofExample, ...],
) -> None:
    if type(record) is not dict or set(record) != {
        "format",
        "v",
        "source",
        "selection",
        "selected",
        "curriculum_sha256",
    }:
        raise CurriculumLoadError("malformed curriculum record")
    if (
        record.get("format") != CURRICULUM_FORMAT
        or type(record.get("v")) is not int
        or record.get("v") != CURRICULUM_VERSION
    ):
        raise CurriculumLoadError("unsupported curriculum format/version")
    source = record.get("source")
    selection = record.get("selection")
    selected = record.get("selected")
    if (
        type(source) is not dict
        or type(selection) is not dict
        or type(selected) is not dict
    ):
        raise CurriculumLoadError(
            "curriculum record lacks source, selection, or selected evidence"
        )
    if set(source) != {"train", "manifest"}:
        raise CurriculumLoadError("malformed curriculum source evidence")
    train = source.get("train")
    manifest = source.get("manifest")
    if (
        type(train) is not dict
        or set(train) != {"name", "bytes", "rows", "sha256"}
        or train.get("name") != "train.jsonl"
        or type(train.get("bytes")) is not int
        or train["bytes"] < 0
        or type(train.get("rows")) is not int
        or train["rows"] < 1
    ):
        raise CurriculumLoadError("malformed source train evidence")
    if (
        type(manifest) is not dict
        or set(manifest) != {"name", "bytes", "sha256"}
        or manifest.get("name") != "manifest.json"
        or type(manifest.get("bytes")) is not int
        or manifest["bytes"] < 1
    ):
        raise CurriculumLoadError("malformed source manifest evidence")
    _require_sha256("source train digest", train.get("sha256"))
    _require_sha256("source manifest digest", manifest.get("sha256"))

    # The nested selector record has its own self-digest.  Re-rendering it is
    # also a closed structural check; the outer digest then binds it to source
    # bytes instead of allowing the same selector digest to float between
    # nominally equivalent artifacts.
    canonical_selection_json(selection)
    if (
        selection.get("format") != SELECTION_FORMAT
        or type(selection.get("v")) is not int
        or selection.get("v") != SELECTION_VERSION
        or selection.get("algorithm") != SELECTION_ALGORITHM
    ):
        raise CurriculumLoadError("incompatible nested selection identity")
    selection_source = selection.get("source")
    selection_selected = selection.get("selected")
    if type(selection_source) is not dict or type(selection_selected) is not dict:
        raise CurriculumLoadError("malformed nested selection evidence")
    if (
        type(selection_source.get("rows")) is not int
        or selection_source.get("rows") != train["rows"]
        or type(selection_selected.get("rows")) is not int
    ):
        raise CurriculumLoadError(
            "selection row evidence is malformed or differs from the source"
        )

    if set(selected) != {
        "rows",
        "ordered_example_ids_sha256",
        "ordered_examples_sha256",
        "selection_sha256",
    }:
        raise CurriculumLoadError("malformed selected-example evidence")
    if type(selected.get("rows")) is not int or selected["rows"] < 1:
        raise CurriculumLoadError("selected row count must be a positive integer")
    if type(examples) is not tuple or not examples:
        raise CurriculumLoadError("curriculum examples must be a non-empty tuple")
    if any(not isinstance(example, ProofExample) for example in examples):
        raise CurriculumLoadError("curriculum contains a non-ProofExample value")
    example_ids = [example.example_id for example in examples]
    example_evidence = [_example_record(example) for example in examples]
    if len(set(example_ids)) != len(example_ids):
        raise CurriculumLoadError("curriculum repeats an example id")
    if (
        selected.get("rows") != len(examples)
        or selection_selected.get("rows") != len(examples)
        or selection_selected.get("example_ids_sha256")
        != _sha256_json(sorted(example_ids))
        or selected.get("ordered_example_ids_sha256")
        != _sha256_json(example_ids)
        or selected.get("ordered_examples_sha256")
        != _sha256_json(example_evidence)
        or selected.get("selection_sha256")
        != selection.get("selection_sha256")
    ):
        raise CurriculumLoadError(
            "selected examples differ from their immutable attestation"
        )
    _require_sha256(
        "selected selection digest", selected.get("selection_sha256")
    )
    if curriculum_record_sha256(record) != record.get("curriculum_sha256"):
        raise CurriculumLoadError("curriculum record digest mismatch")


@dataclass(frozen=True, slots=True)
class LoadedCurriculum:
    """Selected examples paired with their immutable source attestation."""

    examples: tuple[ProofExample, ...]
    attestation_json: str

    def __post_init__(self) -> None:
        try:
            decoded = json.loads(self.attestation_json)
        except (TypeError, json.JSONDecodeError, RecursionError) as exc:
            raise CurriculumLoadError(
                f"curriculum attestation is invalid JSON: {exc}"
            ) from exc
        _validate_attestation(decoded, self.examples)
        if canonical_curriculum_json(decoded) != self.attestation_json:
            raise CurriculumLoadError(
                "curriculum attestation is not canonical JSON"
            )

    @property
    def attestation(self) -> dict[str, object]:
        """Return a detached copy of the immutable canonical record."""

        decoded = json.loads(self.attestation_json)
        if type(decoded) is not dict:  # guarded by ``__post_init__``
            raise RuntimeError("curriculum attestation changed after validation")
        return decoded

    @property
    def sha256(self) -> str:
        value = self.attestation.get("curriculum_sha256")
        if type(value) is not str:  # guarded by ``__post_init__``
            raise RuntimeError("curriculum attestation has no digest")
        return value

    @property
    def selection_sha256(self) -> str:
        selection = self.attestation.get("selection")
        if type(selection) is not dict:  # guarded by ``__post_init__``
            raise RuntimeError("curriculum attestation has no selection")
        value = selection.get("selection_sha256")
        if type(value) is not str:  # guarded by ``__post_init__``
            raise RuntimeError("selection attestation has no digest")
        return value


def _read_bytes(path: Path, *, label: str) -> bytes:
    if not path.is_file():
        raise PromptError(f"missing {label} {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PromptError(f"cannot read {label} {path}: {exc}") from exc


def _canonical_manifest(raw: bytes, path: Path) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PromptError(f"{path}: manifest is not valid UTF-8") from exc
    decoded = _decode_json(text, location=str(path))
    if type(decoded) is not dict:
        raise PromptError(f"{path}: manifest must be an object")
    expected = (
        json.dumps(decoded, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    if raw != expected:
        raise PromptError(f"{path}: manifest is not canonical builder JSON")
    return decoded


def _canonical_train_records(raw: bytes, path: Path) -> tuple[dict[str, object], ...]:
    records: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(raw.splitlines(keepends=True), 1):
        if len(raw_line) > MAX_DATASET_LINE_BYTES:
            raise PromptError(
                f"{path}:{line_number}: row exceeds the "
                f"{MAX_DATASET_LINE_BYTES}-byte limit"
            )
        if not raw_line.endswith(b"\n"):
            raise PromptError(f"{path}: split must be complete JSONL")
        if raw_line == b"\n":
            raise PromptError(f"{path}:{line_number}: blank JSONL record")
        try:
            text = raw_line[:-1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PromptError(
                f"{path}:{line_number}: split is not valid UTF-8"
            ) from exc
        decoded = _decode_json(text, location=f"{path}:{line_number}")
        if type(decoded) is not dict:
            raise PromptError(f"{path}:{line_number}: row must be an object")
        expected = (
            json.dumps(
                decoded,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        metadata = decoded.get("metadata")
        metadata_is_canonical = type(metadata) is dict and tuple(metadata) == tuple(
            sorted(metadata)
        )
        if raw_line != expected or not metadata_is_canonical:
            raise PromptError(
                f"{path}:{line_number}: row is not canonical builder JSON"
            )
        records.append(decoded)
    if not records:
        raise PromptError(f"{path}: model-v3 training split is empty")
    return tuple(records)


def load_curriculum(
    train_path: Path,
    *,
    seed: str,
    synthetic_row_ceiling: int = MODEL_V3_SYNTHETIC_ROW_CEILING,
    contract: CurriculumSelectionContract = MODEL_V3_SELECTION_CONTRACT,
) -> LoadedCurriculum:
    """Load and select the complete, manifest-authorized model-v3 train split.

    The adjacent ``manifest.json`` is mandatory.  ``max_samples`` is
    intentionally absent: every row is structurally validated before the
    whole-session selector is allowed to drop any synthetic session.
    """

    if not isinstance(train_path, Path):
        raise TypeError("train_path must be a pathlib.Path")
    if train_path.name != "train.jsonl":
        raise PromptError("model-v3 curriculum source must be named train.jsonl")
    manifest_path = dataset_manifest_path(train_path)
    train_raw = _read_bytes(train_path, label="training split")
    manifest_raw = _read_bytes(manifest_path, label="dataset manifest")
    train_sha256 = _sha256(train_raw)
    manifest_sha256 = _sha256(manifest_raw)
    manifest = _canonical_manifest(manifest_raw, manifest_path)

    # This call is the shared authority for the manifest environment table,
    # split hash/count, replay counters, and every ``example_from_record``
    # structural check.  It must see the same byte snapshot used below.
    validated = load_examples(
        train_path,
        seed=0,
        manifest_path=manifest_path,
    )
    try:
        unchanged = (
            sha256_file(train_path) == train_sha256
            and sha256_file(manifest_path) == manifest_sha256
        )
    except OSError as exc:
        raise PromptError(f"dataset changed while loading: {exc}") from exc
    if not unchanged:
        raise PromptError("dataset changed while loading the curriculum")

    records = _canonical_train_records(train_raw, train_path)
    examples_by_id: dict[str, ProofExample] = {}
    for example in validated:
        if example.example_id in examples_by_id:
            raise PromptError(
                f"{train_path}: duplicate example id {example.example_id!r}"
            )
        examples_by_id[example.example_id] = example
    if len(examples_by_id) != len(records):
        raise PromptError(
            f"{train_path}: validated row population changed while loading"
        )

    rows = []
    for line_number, record in enumerate(records, 1):
        example_id = f"{record.get('session')}:{record.get('step')}"
        example = examples_by_id.pop(example_id, None)
        if example is None:
            raise PromptError(
                f"{train_path}:{line_number}: row lacks its validated example"
            )
        rows.append(row_from_validated_record(example, record))
    if examples_by_id:
        raise PromptError(f"{train_path}: validated examples lack builder rows")

    split_table = manifest.get("splits")
    if type(split_table) is not dict or type(split_table.get("train")) is not dict:
        raise PromptError(f"{manifest_path}: missing train split provenance")
    train_manifest = split_table["train"]
    if (
        train_manifest.get("sha256") != train_sha256
        or train_manifest.get("rows") != len(records)
    ):
        raise PromptError(
            f"{manifest_path}: captured train split differs from its provenance"
        )

    selection = select_curriculum(
        rows,
        seed=seed,
        synthetic_row_ceiling=synthetic_row_ceiling,
        contract=contract,
    )
    examples = selection.examples
    core: dict[str, object] = {
        "format": CURRICULUM_FORMAT,
        "v": CURRICULUM_VERSION,
        "source": {
            "train": {
                "name": train_path.name,
                "bytes": len(train_raw),
                "rows": len(records),
                "sha256": train_sha256,
            },
            "manifest": {
                "name": manifest_path.name,
                "bytes": len(manifest_raw),
                "sha256": manifest_sha256,
            },
        },
        "selection": selection.record,
        "selected": {
            "rows": len(examples),
            "ordered_example_ids_sha256": _sha256_json(
                [example.example_id for example in examples]
            ),
            "ordered_examples_sha256": _sha256_json(
                [_example_record(example) for example in examples]
            ),
            "selection_sha256": selection.sha256,
        },
    }
    record = {**core, "curriculum_sha256": _sha256_json(core)}
    return LoadedCurriculum(
        examples=examples,
        attestation_json=canonical_curriculum_json(record),
    )


__all__ = [
    "CURRICULUM_FORMAT",
    "CURRICULUM_VERSION",
    "CurriculumLoadError",
    "LoadedCurriculum",
    "canonical_curriculum_json",
    "curriculum_record_sha256",
    "load_curriculum",
]
