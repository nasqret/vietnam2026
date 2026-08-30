"""Current-source eligibility for one historically replayed corpus seal.

This module deliberately creates no signature and no new proof attestation.
The caller must obtain three historical trust anchors from an authenticated
channel outside the seal itself:

* the clean source commit used by the preparation job;
* the decimal preparation job id; and
* the seal ``content_sha256``.

Reading those values out of ``seal.json`` and passing them back here provides
integrity checking but no external authentication.  Given real anchors,
:func:`verify_sealed_corpus_eligibility` first performs the complete immutable
seal verification, then checks that the configured loader paths name exactly
that seal's training and validation files.  Finally it compares the current
builder/kernel/compiler inventory with the inventory embedded in the sealed
dataset manifest.  That last check hashes source files but intentionally does
not replay any proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from collections.abc import Mapping, Sequence

from . import attest, corpus_seal
from .contract import (
    MODEL_V3_LIBRARY_SIZE,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v3_prefix_library,
)
from .prompt import (
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    PromptEnvironment,
    prompt_contract_sha256,
    prompt_manifest_record,
)
from peano_lab.batch import MODEL_V1_COMMANDS


ELIGIBILITY_FORMAT = "peano-policy-v3-sealed-corpus-eligibility"
ELIGIBILITY_VERSION = 1

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MAX_JSON_BYTES = 64 * 1024 * 1024


class CorpusEligibilityError(ValueError):
    """A sealed corpus cannot safely be reused by the current source."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _decode_json(raw: bytes, *, location: str) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise CorpusEligibilityError(f"{location}: invalid JSON: {exc}") from exc
    if type(value) is not dict:
        raise CorpusEligibilityError(f"{location}: expected one JSON object")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise CorpusEligibilityError(f"{label}: expected one lowercase SHA-256")
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise CorpusEligibilityError(f"{label}: expected a JSON object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if type(value) is not list:
        raise CorpusEligibilityError(f"{label}: expected a JSON array")
    return value


def _absolute_lexical_path(
    value: str | os.PathLike[str],
    label: str,
) -> Path:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise CorpusEligibilityError(f"{label}: path is not filesystem text") from exc
    if (
        type(raw) is not str
        or not raw
        or any(ord(character) < 32 or ord(character) == 127 for character in raw)
    ):
        raise CorpusEligibilityError(
            f"{label}: path must be non-empty control-free text"
        )
    path = Path(raw)
    if ".." in path.parts:
        raise CorpusEligibilityError(f"{label}: parent traversal is forbidden")
    return path if path.is_absolute() else Path.cwd() / path


def _file_table(seal: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    records = _sequence(seal.get("files"), "seal file inventory")
    result: dict[str, Mapping[str, object]] = {}
    for index, value in enumerate(records, 1):
        record = _mapping(value, f"seal file inventory record {index}")
        if set(record) != {"path", "bytes", "sha256"}:
            raise CorpusEligibilityError(
                f"seal file inventory record {index}: fields are not canonical"
            )
        relative = record.get("path")
        size = record.get("bytes")
        if type(relative) is not str or not relative or relative in result:
            raise CorpusEligibilityError("seal file inventory path is invalid or repeated")
        if type(size) is not int or size < 0:
            raise CorpusEligibilityError(f"sealed {relative}: invalid byte count")
        _sha256(record.get("sha256"), f"sealed {relative} hash")
        result[relative] = record
    return result


def _read_bound_json(
    path: Path,
    record: Mapping[str, object],
    *,
    label: str,
) -> tuple[dict[str, object], bytes]:
    expected_size = record.get("bytes")
    expected_sha256 = _sha256(record.get("sha256"), f"{label} sealed hash")
    if type(expected_size) is not int or expected_size < 0:
        raise CorpusEligibilityError(f"{label}: sealed byte count is malformed")
    if expected_size > _MAX_JSON_BYTES:
        raise CorpusEligibilityError(
            f"{label}: exceeds the {_MAX_JSON_BYTES}-byte JSON safety limit"
        )

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CorpusEligibilityError(f"{label}: cannot open sealed file: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CorpusEligibilityError(f"{label}: sealed path is not a regular file")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read(_MAX_JSON_BYTES + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise CorpusEligibilityError(f"{label}: cannot read sealed file: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    if len(raw) > _MAX_JSON_BYTES:
        raise CorpusEligibilityError(
            f"{label}: exceeds the {_MAX_JSON_BYTES}-byte JSON safety limit"
        )
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise CorpusEligibilityError(f"{label}: changed while it was read")
    if len(raw) != expected_size:
        raise CorpusEligibilityError(f"{label}: byte count differs from the verified seal")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise CorpusEligibilityError(f"{label}: hash differs from the verified seal")
    return _decode_json(raw, location=label), raw


def _require_exact_loader_paths(
    seal_root: Path,
    configured_train_path: str | os.PathLike[str],
    configured_eval_path: str | os.PathLike[str],
) -> tuple[Path, Path, Path]:
    train = _absolute_lexical_path(configured_train_path, "configured train path")
    evaluation = _absolute_lexical_path(configured_eval_path, "configured eval path")
    expected_train = seal_root / "data" / "train.jsonl"
    expected_eval = seal_root / "data" / "val.jsonl"
    if train != expected_train:
        raise CorpusEligibilityError(
            "configured train path must be exactly seal/data/train.jsonl"
        )
    if evaluation != expected_eval:
        raise CorpusEligibilityError(
            "configured eval path must be exactly seal/data/val.jsonl"
        )
    return train, evaluation, seal_root / "data" / "manifest.json"


def _current_inference_environment(
    historical_prefix_sha256: str,
    historical_full_library_sha256: str,
) -> dict[str, object]:
    """Project the current source authority without replaying certificates.

    The prefix and full-library digests come from the externally anchored
    historical replay and remain separate even at the full inference prefix.
    ``model_v3_prefix_library`` validates the current source/catalog projection
    but, unlike ``model_v3_environment``, does not reconstruct proof terms.
    Exact compiler-inventory matching makes reuse of the historical digests
    sound for this compatibility gate.
    """

    library = model_v3_prefix_library(MODEL_V3_LIBRARY_SIZE)
    environment = PromptEnvironment(
        False,
        CapabilityIdentity(
            label="model-v3",
            allowed_commands=tuple(sorted(MODEL_V1_COMMANDS)),
            allowed_theorems=tuple(record.name for record in library),
        ),
        prompt_version=PEANO_PROMPT_V3,
        library=library,
        library_identity_sha256=historical_prefix_sha256,
        library_prefix_length=MODEL_V3_LIBRARY_SIZE,
        library_full_length=MODEL_V3_LIBRARY_SIZE,
        library_full_identity_sha256=historical_full_library_sha256,
    )
    return environment_record(environment)


def eligibility_record_sha256(record: Mapping[str, object]) -> str:
    """Return the digest of an eligibility record's self-excluding core."""

    if not isinstance(record, Mapping):
        raise CorpusEligibilityError("eligibility record must be a mapping")
    core = dict(record)
    claimed = core.pop("eligibility_sha256", None)
    _sha256(claimed, "eligibility record digest")
    return _sha256_json(core)


def canonical_eligibility_json(record: Mapping[str, object]) -> str:
    """Validate and render one eligibility record as canonical JSON plus LF."""

    claimed = record.get("eligibility_sha256")
    if eligibility_record_sha256(record) != claimed:
        raise CorpusEligibilityError("eligibility record digest mismatch")
    return _canonical_json(record) + "\n"


@dataclass(frozen=True, slots=True)
class SealedCorpusEligibility:
    """An immutable reuse record plus the exact bound historical report."""

    record_json: str
    dataset_attestation_json: str

    def __post_init__(self) -> None:
        if type(self.record_json) is not str:
            raise CorpusEligibilityError("eligibility record JSON must be text")
        record = _decode_json(
            self.record_json.encode("utf-8"),
            location="eligibility record",
        )
        if (
            record.get("format") != ELIGIBILITY_FORMAT
            or record.get("version") != ELIGIBILITY_VERSION
        ):
            raise CorpusEligibilityError(
                "eligibility record has the wrong format/version"
            )
        if canonical_eligibility_json(record) != self.record_json:
            raise CorpusEligibilityError("eligibility record is not canonical JSON")
        if type(self.dataset_attestation_json) is not str:
            raise CorpusEligibilityError("dataset attestation JSON must be text")
        attestation = _decode_json(
            self.dataset_attestation_json.encode("utf-8"),
            location="bound dataset attestation",
        )
        identity = _mapping(
            record.get("historical_attestation"),
            "eligibility historical attestation identity",
        )
        expected_sha256 = _sha256(
            identity.get("sha256"), "eligibility historical attestation hash"
        )
        if (
            hashlib.sha256(self.dataset_attestation_json.encode("utf-8")).hexdigest()
            != expected_sha256
        ):
            raise CorpusEligibilityError(
                "dataset attestation JSON differs from the bound sealed report"
            )
        if (
            attestation.get("format") != identity.get("format")
            or attestation.get("v") != identity.get("version")
            or attestation.get("independent_replay")
            != identity.get("independent_replay")
            or attestation.get("held_out_contamination")
            != identity.get("held_out_contamination")
            or attestation.get("manifest_sha256")
            != identity.get("manifest_sha256")
            or attestation.get("dataset_sha256")
            != identity.get("dataset_sha256")
        ):
            raise CorpusEligibilityError(
                "dataset attestation JSON differs from its eligibility identity"
            )

    @property
    def record(self) -> dict[str, object]:
        """Return a detached JSON-compatible copy of the immutable record."""

        return _decode_json(
            self.record_json.encode("utf-8"),
            location="eligibility record",
        )

    @property
    def dataset_attestation(self) -> dict[str, object]:
        """Return a detached copy of the exact hash-bound replay report."""

        return _decode_json(
            self.dataset_attestation_json.encode("utf-8"),
            location="bound dataset attestation",
        )

    @property
    def sha256(self) -> str:
        value = self.record.get("eligibility_sha256")
        if type(value) is not str:  # guarded by ``__post_init__``
            raise RuntimeError("eligibility record has no digest")
        return value


def _validate_historical_attestation(
    attestation_record: Mapping[str, object],
    *,
    report_sha256: str,
    seal_dataset: Mapping[str, object],
    compiler: Mapping[str, object],
    current_prompt: Mapping[str, object],
    current_prompt_sha256: str,
    current_held_out: Mapping[str, object],
    current_held_out_sha256: str,
    current_environment: Mapping[str, object],
) -> dict[str, object]:
    if (
        attestation_record.get("format") != "peano-policy-dataset-attestation"
        or attestation_record.get("v") != 2
        or attestation_record.get("prompt_version") != PEANO_PROMPT_V3
        or attestation_record.get("independent_replay") is not True
        or attestation_record.get("held_out_contamination") != 0
    ):
        raise CorpusEligibilityError(
            "historical report is not an independent uncontaminated model-v3 replay"
        )

    manifest_sha256 = _sha256(
        seal_dataset.get("manifest_sha256"), "sealed dataset manifest hash"
    )
    dataset_sha256 = _sha256(
        seal_dataset.get("dataset_sha256"), "sealed dataset aggregate hash"
    )
    if (
        attestation_record.get("manifest_sha256") != manifest_sha256
        or attestation_record.get("dataset_sha256") != dataset_sha256
    ):
        raise CorpusEligibilityError(
            "historical attestation names a different sealed dataset"
        )
    if attestation_record.get("compiler") != compiler:
        raise CorpusEligibilityError(
            "historical attestation compiler identity differs from the compatible manifest"
        )
    if (
        attestation_record.get("prompt_contract") != current_prompt
        or attestation_record.get("prompt_contract_sha256")
        != current_prompt_sha256
        or seal_dataset.get("prompt_contract_sha256") != current_prompt_sha256
    ):
        raise CorpusEligibilityError(
            "historical dataset uses a different current prompt contract"
        )
    if (
        attestation_record.get("held_out_contract") != current_held_out
        or attestation_record.get("held_out_contract_sha256")
        != current_held_out_sha256
        or seal_dataset.get("held_out_contract_sha256") != current_held_out_sha256
    ):
        raise CorpusEligibilityError(
            "historical dataset uses a different current held-out contract"
        )

    library_snapshot_sha256 = _sha256(
        seal_dataset.get("library_snapshot_sha256"),
        "sealed library snapshot hash",
    )
    if (
        attestation_record.get("library_snapshot_sha256")
        != library_snapshot_sha256
        or current_environment.get("library_identity_sha256")
        != library_snapshot_sha256
        or attestation_record.get("inference_environment") != current_environment
    ):
        raise CorpusEligibilityError(
            "historical dataset uses a different current model-v3 inference authority"
        )
    if (
        attestation_record.get("training_environments_sha256")
        != seal_dataset.get("training_environments_sha256")
        or attestation_record.get("authority_schedule")
        != seal_dataset.get("authority_schedule")
    ):
        raise CorpusEligibilityError(
            "historical curriculum identity differs from the sealed dataset"
        )

    attestor = _mapping(
        attestation_record.get("attestor"), "historical attestor identity"
    )
    return {
        "sealed_path": "reports/dataset-attestation.json",
        "sha256": report_sha256,
        "format": "peano-policy-dataset-attestation",
        "version": 2,
        "independent_replay": True,
        "held_out_contamination": 0,
        "attestor_sha256": _sha256_json(attestor),
        "manifest_sha256": manifest_sha256,
        "dataset_sha256": dataset_sha256,
    }


def verify_sealed_corpus_eligibility(
    seal: str | os.PathLike[str],
    *,
    configured_train_path: str | os.PathLike[str],
    configured_eval_path: str | os.PathLike[str],
    historical_source_commit: str,
    historical_prepare_job_id: str,
    sealed_content_sha256: str,
) -> SealedCorpusEligibility:
    """Authorize immutable corpus reuse by the current compatible source.

    ``historical_source_commit``, ``historical_prepare_job_id``, and
    ``sealed_content_sha256`` are mandatory external trust anchors.  They must
    not be populated by first reading the untrusted seal being checked.
    ``configured_train_path`` and ``configured_eval_path`` are the exact paths
    the eventual loader will use; aliases and paths outside this seal fail.
    """

    expected_content_sha256 = _sha256(
        sealed_content_sha256, "externally trusted seal content hash"
    )
    try:
        verified_seal = corpus_seal.verify_seal(
            seal,
            source_commit=historical_source_commit,
            prepare_job_id=historical_prepare_job_id,
        )
    except (CorpusEligibilityError, corpus_seal.CorpusSealError) as exc:
        raise CorpusEligibilityError(f"sealed corpus verification failed: {exc}") from exc

    actual_content_sha256 = _sha256(
        verified_seal.get("content_sha256"), "verified seal content hash"
    )
    if actual_content_sha256 != expected_content_sha256:
        raise CorpusEligibilityError(
            "verified seal differs from the externally trusted content hash"
        )

    seal_root = _absolute_lexical_path(seal, "sealed corpus")
    train_path, eval_path, manifest_path = _require_exact_loader_paths(
        seal_root,
        configured_train_path,
        configured_eval_path,
    )
    files = _file_table(verified_seal)
    required = {
        "data/train.jsonl",
        "data/val.jsonl",
        "data/manifest.json",
        "reports/dataset-attestation.json",
    }
    if not required <= set(files):
        raise CorpusEligibilityError("verified seal lacks an eligibility artifact")

    dataset_manifest, _ = _read_bound_json(
        manifest_path,
        files["data/manifest.json"],
        label="sealed dataset manifest",
    )
    try:
        compiler = attest._verify_compiler(dataset_manifest)
    except attest.DatasetAttestationError as exc:
        raise CorpusEligibilityError(
            f"current compiler is incompatible with sealed dataset: {exc}"
        ) from exc

    historical_attestation, historical_attestation_raw = _read_bound_json(
        seal_root / "reports" / "dataset-attestation.json",
        files["reports/dataset-attestation.json"],
        label="sealed historical dataset attestation",
    )
    seal_dataset = _mapping(verified_seal.get("dataset"), "seal dataset identity")
    seal_source = _mapping(verified_seal.get("source"), "seal source identity")
    seal_reports = _mapping(verified_seal.get("reports"), "seal report identities")
    attestation_identity = _mapping(
        seal_reports.get("dataset_attestation"),
        "seal dataset attestation identity",
    )
    attestation_sha256 = _sha256(
        attestation_identity.get("sha256"),
        "seal dataset attestation hash",
    )
    if attestation_sha256 != files["reports/dataset-attestation.json"].get("sha256"):
        raise CorpusEligibilityError(
            "seal report identity differs from its closed file inventory"
        )

    current_prompt = prompt_manifest_record(PEANO_PROMPT_V3)
    current_prompt_sha256 = prompt_contract_sha256(PEANO_PROMPT_V3)
    current_held_out = held_out_contract_record(PEANO_PROMPT_V3)
    current_held_out_sha256 = held_out_contract_sha256(PEANO_PROMPT_V3)
    historical_prefix_sha256 = _sha256(
        seal_dataset.get("library_snapshot_sha256"),
        "sealed library snapshot hash",
    )
    sealed_historical_environment = _mapping(
        historical_attestation.get("inference_environment"),
        "historical inference environment",
    )
    historical_full_library_sha256 = _sha256(
        sealed_historical_environment.get("library_full_identity_sha256"),
        "historical full-library identity hash",
    )
    authority_schedule = _mapping(
        seal_dataset.get("authority_schedule"), "sealed authority schedule"
    )
    if (
        authority_schedule.get("full_library_sha256")
        != historical_full_library_sha256
    ):
        raise CorpusEligibilityError(
            "historical full-library identity differs from the authority schedule"
        )
    current_environment = _current_inference_environment(
        historical_prefix_sha256,
        historical_full_library_sha256,
    )
    historical_identity = _validate_historical_attestation(
        historical_attestation,
        report_sha256=attestation_sha256,
        seal_dataset=seal_dataset,
        compiler=compiler,
        current_prompt=current_prompt,
        current_prompt_sha256=current_prompt_sha256,
        current_held_out=current_held_out,
        current_held_out_sha256=current_held_out_sha256,
        current_environment=current_environment,
    )

    split_identities = _mapping(seal_dataset.get("splits"), "sealed split identities")
    input_records: dict[str, object] = {}
    for role, sealed_name, configured_path, split_name in (
        ("train", "data/train.jsonl", train_path, "train"),
        ("eval", "data/val.jsonl", eval_path, "val"),
    ):
        file_record = files[sealed_name]
        split = _mapping(
            split_identities.get(split_name), f"sealed {split_name} split identity"
        )
        split_sha256 = _sha256(split.get("sha256"), f"sealed {split_name} split hash")
        if split_sha256 != file_record.get("sha256"):
            raise CorpusEligibilityError(
                f"sealed {split_name} identity differs from its file inventory"
            )
        rows = split.get("rows")
        if type(rows) is not int or rows < 1:
            raise CorpusEligibilityError(f"sealed {split_name} row count is invalid")
        input_records[role] = {
            "configured_path": str(configured_path),
            "sealed_path": sealed_name,
            "bytes": file_record["bytes"],
            "rows": rows,
            "sha256": split_sha256,
        }

    manifest_record = files["data/manifest.json"]
    manifest_sha256 = _sha256(
        manifest_record.get("sha256"), "sealed manifest file hash"
    )
    if manifest_sha256 != seal_dataset.get("manifest_sha256"):
        raise CorpusEligibilityError(
            "sealed dataset identity differs from its manifest file"
        )
    input_records["manifest"] = {
        "configured_path": str(manifest_path),
        "sealed_path": "data/manifest.json",
        "bytes": manifest_record["bytes"],
        "sha256": manifest_sha256,
    }

    source_commit = seal_source.get("git_commit")
    prepare_job_id = seal_source.get("prepare_job_id")
    if (
        source_commit != historical_source_commit
        or prepare_job_id != historical_prepare_job_id
    ):
        raise CorpusEligibilityError("verified seal did not preserve its trust anchors")

    core: dict[str, object] = {
        "format": ELIGIBILITY_FORMAT,
        "version": ELIGIBILITY_VERSION,
        "seal": {
            "root": str(seal_root),
            "format": verified_seal.get("format"),
            "version": verified_seal.get("version"),
            "content_sha256": actual_content_sha256,
            "files_sha256": _sha256(
                verified_seal.get("files_sha256"), "seal file inventory hash"
            ),
            "historical_source_commit": source_commit,
            "historical_prepare_job_id": prepare_job_id,
        },
        "historical_attestation": historical_identity,
        "inputs": input_records,
        "current_compatibility": {
            "compiler": {
                "status": "exact-source-inventory-match",
                "sealed_runtime": compiler["runtime"],
                "sources_sha256": compiler["sources_sha256"],
                "source_count": compiler["source_count"],
            },
            "prompt_contract": {
                "version": PEANO_PROMPT_V3,
                "record": current_prompt,
                "sha256": current_prompt_sha256,
            },
            "held_out_contract": {
                "record": current_held_out,
                "sha256": current_held_out_sha256,
            },
            "inference_environment": current_environment,
        },
    }
    record = {**core, "eligibility_sha256": _sha256_json(core)}
    return SealedCorpusEligibility(
        canonical_eligibility_json(record),
        historical_attestation_raw.decode("utf-8"),
    )


__all__ = [
    "ELIGIBILITY_FORMAT",
    "ELIGIBILITY_VERSION",
    "CorpusEligibilityError",
    "SealedCorpusEligibility",
    "canonical_eligibility_json",
    "eligibility_record_sha256",
    "verify_sealed_corpus_eligibility",
]
