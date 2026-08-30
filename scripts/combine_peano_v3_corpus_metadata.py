#!/usr/bin/env python3
"""Validate and combine the two model-v3 corpus metadata populations.

The theorem-ladder generator emits one session for each declaration under its
strict predecessor prefix.  The balanced generator emits one synthetic
population under the complete library prefix.  This command is the narrow
join between those generators and ``build_peano_policy_dataset.py``: it
rejects mixed or incomplete authorities, canonicalizes record order and JSON,
then transactionally publishes one metadata JSONL file and a compact manifest.

No proof certificate is trusted or replayed here.  The dataset builder remains
responsible for replaying every referenced trace against this metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from export_traces import publish_text_artifact_set  # noqa: E402


FORMAT = "peano-v3-combined-corpus-metadata"
VERSION = 1
EXPECTED_LIBRARY_SIZE = 247
LIBRARY_TRAJECTORY = "catalog-predecessor-prefix-v1"
SYNTHETIC_LANE = "synthetic-root-balanced"
COMBINATION_ORDER = "library-index-then-synthetic-ordinal-v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CombinationError(ValueError):
    """Input metadata does not describe the exact model-v3 curriculum."""


@dataclass(frozen=True, slots=True)
class CombinationResult:
    """Paths and summary for one transactionally published combination."""

    metadata_path: Path
    manifest_path: Path
    manifest: dict[str, object]


@dataclass(frozen=True, slots=True)
class _LocatedRecord:
    value: dict[str, object]
    path: Path
    line: int

    @property
    def location(self) -> str:
        return f"{self.path}:{self.line}"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_jsonl(path: Path) -> tuple[tuple[_LocatedRecord, ...], bytes]:
    if not path.is_file():
        raise CombinationError(f"{path}: metadata is not a regular file")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CombinationError(f"{path}: metadata is not valid UTF-8") from exc
    except OSError as exc:
        raise CombinationError(f"{path}: cannot read metadata: {exc}") from exc
    if not raw:
        raise CombinationError(f"{path}: metadata is empty")
    if not raw.endswith(b"\n"):
        raise CombinationError(f"{path}: incomplete JSONL (missing final newline)")

    records: list[_LocatedRecord] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line:
            raise CombinationError(
                f"{path}:{line_number}: blank JSONL records are forbidden"
            )
        try:
            value = json.loads(
                line,
                object_pairs_hook=_object_from_pairs,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise CombinationError(
                f"{path}:{line_number}: invalid JSON: {exc}"
            ) from exc
        if type(value) is not dict:
            raise CombinationError(
                f"{path}:{line_number}: each JSONL record must be an object"
            )
        records.append(_LocatedRecord(value, path, line_number))
    return tuple(records), raw


def _safe_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value.strip())
        and not any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
            for character in value
        )
    )


def _text(record: _LocatedRecord, field: str) -> str:
    value = record.value.get(field)
    if not _safe_text(value):
        raise CombinationError(
            f"{record.location}: {field} must be non-empty control-free text"
        )
    return value  # type: ignore[return-value]


def _integer(record: _LocatedRecord, field: str) -> int:
    value = record.value.get(field)
    if type(value) is not int:
        raise CombinationError(f"{record.location}: {field} must be an integer")
    return value


def _sha256(record: _LocatedRecord, field: str) -> str:
    value = record.value.get(field)
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise CombinationError(
            f"{record.location}: {field} must be a lowercase SHA-256"
        )
    return value


def _validate_common(record: _LocatedRecord) -> tuple[str, str, str]:
    session = _text(record, "session")
    statement = _text(record, "statement")
    full_identity = _sha256(record, "library_full_identity_sha256")
    _sha256(record, "library_identity_sha256")
    _sha256(record, "environment_sha256")
    if _integer(record, "library_size") != EXPECTED_LIBRARY_SIZE:
        raise CombinationError(
            f"{record.location}: library_size must be {EXPECTED_LIBRARY_SIZE}"
        )
    prefix = _integer(record, "library_prefix_length")
    if not 0 <= prefix <= EXPECTED_LIBRARY_SIZE:
        raise CombinationError(
            f"{record.location}: library_prefix_length is outside 0.."
            f"{EXPECTED_LIBRARY_SIZE}"
        )
    if record.value.get("surface") != "model-v3":
        raise CombinationError(f"{record.location}: surface must be 'model-v3'")
    if record.value.get("classical") is not False:
        raise CombinationError(f"{record.location}: classical must be false")
    if type(record.value.get("capabilities")) is not dict:
        raise CombinationError(f"{record.location}: capabilities must be an object")
    return session, statement, full_identity


def _validate_library(
    records: Sequence[_LocatedRecord],
) -> tuple[_LocatedRecord, ...]:
    if len(records) != EXPECTED_LIBRARY_SIZE:
        raise CombinationError(
            "library metadata must contain exactly "
            f"{EXPECTED_LIBRARY_SIZE} predecessor-prefix records"
        )
    by_index: dict[int, _LocatedRecord] = {}
    target_names: set[str] = set()
    for record in records:
        if record.value.get("trajectory") != LIBRARY_TRAJECTORY:
            raise CombinationError(
                f"{record.location}: library trajectory must be "
                f"{LIBRARY_TRAJECTORY!r}"
            )
        index = _integer(record, "library_target_index")
        if index in by_index:
            raise CombinationError(
                f"{record.location}: duplicate library target index {index}"
            )
        if not 0 <= index < EXPECTED_LIBRARY_SIZE:
            raise CombinationError(
                f"{record.location}: library target index is outside 0.."
                f"{EXPECTED_LIBRARY_SIZE - 1}"
            )
        prefix = _integer(record, "library_prefix_length")
        if prefix != index:
            raise CombinationError(
                f"{record.location}: theorem {index} must use prefix {index}, "
                f"not {prefix}"
            )
        target = _text(record, "library_target_name")
        if record.value.get("theorem") != target:
            raise CombinationError(
                f"{record.location}: theorem and library_target_name differ"
            )
        if target in target_names:
            raise CombinationError(
                f"{record.location}: duplicate library target {target!r}"
            )
        by_index[index] = record
        target_names.add(target)

    expected = set(range(EXPECTED_LIBRARY_SIZE))
    if set(by_index) != expected:
        missing = sorted(expected.difference(by_index))
        extra = sorted(set(by_index).difference(expected))
        raise CombinationError(
            f"library prefix coverage is not exactly 0..{EXPECTED_LIBRARY_SIZE - 1}; "
            f"missing={missing}, extra={extra}"
        )
    return tuple(by_index[index] for index in range(EXPECTED_LIBRARY_SIZE))


def _validate_synthetic(
    records: Sequence[_LocatedRecord],
) -> tuple[tuple[_LocatedRecord, ...], dict[str, str]]:
    if not records:
        raise CombinationError("synthetic metadata population is empty")
    by_ordinal: dict[int, _LocatedRecord] = {}
    seeds: set[str] = set()
    environments: set[str] = set()
    prefix_identities: set[str] = set()
    roots: set[str] = set()
    for record in records:
        if record.value.get("lane") != SYNTHETIC_LANE:
            raise CombinationError(
                f"{record.location}: synthetic lane must be {SYNTHETIC_LANE!r}"
            )
        if _integer(record, "library_prefix_length") != EXPECTED_LIBRARY_SIZE:
            raise CombinationError(
                f"{record.location}: synthetic records must use the full "
                f"{EXPECTED_LIBRARY_SIZE}-theorem prefix"
            )
        if (
            "library_target_index" in record.value
            or "library_target_name" in record.value
        ):
            raise CombinationError(
                f"{record.location}: synthetic record claims a library target"
            )
        ordinal = _integer(record, "ordinal")
        if ordinal < 1:
            raise CombinationError(
                f"{record.location}: synthetic ordinal must be positive"
            )
        if ordinal in by_ordinal:
            raise CombinationError(
                f"{record.location}: duplicate synthetic ordinal {ordinal}"
            )
        root = _text(record, "root")
        if root in roots:
            raise CombinationError(
                f"{record.location}: duplicate synthetic target root {root!r}"
            )
        by_ordinal[ordinal] = record
        roots.add(root)
        seeds.add(_text(record, "seed"))
        environments.add(_sha256(record, "environment_sha256"))
        prefix_identities.add(_sha256(record, "library_identity_sha256"))

    expected_ordinals = set(range(1, len(records) + 1))
    if set(by_ordinal) != expected_ordinals:
        raise CombinationError(
            "synthetic population ordinals must be exactly 1.."
            f"{len(records)}"
        )
    if len(seeds) != 1 or len(environments) != 1 or len(prefix_identities) != 1:
        raise CombinationError(
            "synthetic metadata must describe exactly one full-prefix population"
        )
    identity = {
        "seed": next(iter(seeds)),
        "environment_sha256": next(iter(environments)),
        "library_identity_sha256": next(iter(prefix_identities)),
    }
    return (
        tuple(by_ordinal[index] for index in range(1, len(records) + 1)),
        identity,
    )


def _paths_alias(paths: Sequence[Path]) -> bool:
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            try:
                if left.resolve(strict=False) == right.resolve(strict=False):
                    return True
            except (OSError, RuntimeError):
                pass
            try:
                if os.path.samefile(left, right):
                    return True
            except OSError:
                pass
    return False


def _artifact(path: Path, raw: bytes) -> dict[str, object]:
    return {
        "path": path.name,
        "bytes": len(raw),
        "sha256": _sha256_bytes(raw),
    }


def combine_metadata(
    library_metadata: str | os.PathLike[str],
    synthetic_metadata: str | os.PathLike[str],
    output: str | os.PathLike[str],
    manifest: str | os.PathLike[str],
) -> CombinationResult:
    """Validate, canonicalize, and transactionally publish both populations."""

    library_path = Path(library_metadata)
    synthetic_path = Path(synthetic_metadata)
    output_path = Path(output)
    manifest_path = Path(manifest)
    if _paths_alias(
        (library_path, synthetic_path, output_path, manifest_path)
    ):
        raise CombinationError("input and output artifact paths must be distinct")

    library_records, library_raw = _load_jsonl(library_path)
    synthetic_records, synthetic_raw = _load_jsonl(synthetic_path)
    library = _validate_library(library_records)
    synthetic, synthetic_identity = _validate_synthetic(synthetic_records)

    sessions: dict[str, str] = {}
    targets: dict[str, str] = {}
    full_identities: set[str] = set()
    for record in (*library, *synthetic):
        session, statement, full_identity = _validate_common(record)
        if session in sessions:
            raise CombinationError(
                f"{record.location}: duplicate session {session!r}; first at "
                f"{sessions[session]}"
            )
        if statement in targets:
            raise CombinationError(
                f"{record.location}: duplicate target statement; first at "
                f"{targets[statement]}"
            )
        sessions[session] = record.location
        targets[statement] = record.location
        full_identities.add(full_identity)
    if len(full_identities) != 1:
        raise CombinationError(
            "all metadata records must bind one common full-library identity"
        )
    full_identity = next(iter(full_identities))

    ordered = (*library, *synthetic)
    metadata_text = "".join(
        _canonical_json(record.value) + "\n" for record in ordered
    )
    metadata_bytes = metadata_text.encode("utf-8")
    combined_sha256 = _sha256_bytes(metadata_bytes)
    fingerprint_payload = {
        "combination_order": COMBINATION_ORDER,
        "full_library_identity_sha256": full_identity,
        "library_input_sha256": _sha256_bytes(library_raw),
        "synthetic_input_sha256": _sha256_bytes(synthetic_raw),
        "combined_metadata_sha256": combined_sha256,
    }
    run_fingerprint = _sha256_bytes(
        _canonical_json(fingerprint_payload).encode("utf-8")
    )
    summary: dict[str, object] = {
        "format": FORMAT,
        "version": VERSION,
        "run_fingerprint": run_fingerprint,
        "combination_order": COMBINATION_ORDER,
        "library": {
            "full_identity_sha256": full_identity,
            "size": EXPECTED_LIBRARY_SIZE,
            "trajectory": LIBRARY_TRAJECTORY,
            "prefix_coverage": [0, EXPECTED_LIBRARY_SIZE - 1],
        },
        "synthetic_population": {
            "lane": SYNTHETIC_LANE,
            "library_prefix_length": EXPECTED_LIBRARY_SIZE,
            **synthetic_identity,
        },
        "inputs": {
            "library_metadata": _artifact(library_path, library_raw),
            "synthetic_metadata": _artifact(synthetic_path, synthetic_raw),
        },
        "artifact": {
            "metadata": {
                "path": output_path.name,
                "bytes": len(metadata_bytes),
                "sha256": combined_sha256,
            }
        },
        "counts": {
            "sessions": len(ordered),
            "unique_sessions": len(sessions),
            "unique_target_statements": len(targets),
            "library_sessions": len(library),
            "synthetic_sessions": len(synthetic),
            "synthetic_populations": 1,
        },
    }
    manifest_text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    try:
        publish_text_artifact_set(
            (
                (output_path, metadata_text),
                (manifest_path, manifest_text),
            )
        )
    except ValueError as exc:
        raise CombinationError(
            str(exc).replace("export artifact", "combined metadata artifact")
        ) from exc
    return CombinationResult(output_path, manifest_path, summary)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-metadata", required=True)
    parser.add_argument("--synthetic-metadata", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = combine_metadata(
            args.library_metadata,
            args.synthetic_metadata,
            args.output,
            args.manifest,
        )
    except (CombinationError, OSError) as exc:
        print(f"metadata combination failed: {exc}", file=sys.stderr)
        return 2
    counts = result.manifest["counts"]
    assert isinstance(counts, Mapping)
    print(
        f"combined {counts['library_sessions']} library + "
        f"{counts['synthetic_sessions']} synthetic sessions; "
        f"manifest: {result.manifest_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main tests
    raise SystemExit(main())


__all__ = [
    "COMBINATION_ORDER",
    "CombinationError",
    "CombinationResult",
    "EXPECTED_LIBRARY_SIZE",
    "FORMAT",
    "LIBRARY_TRAJECTORY",
    "SYNTHETIC_LANE",
    "combine_metadata",
    "main",
]
