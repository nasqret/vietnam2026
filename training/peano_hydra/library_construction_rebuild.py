"""Candidate-only A2.2 rebuilds for three reduced direct dependency vectors.

The retained A2.1 audit found three exact tactic recipes that still compile
after one declared dependency is removed.  This module performs the distinct
next step: it reconstructs each recipe, closes it with canonical certificates
from the pinned replay pack, and asks the independent kernel to check the
result from the empty context against the original statement.

The resulting document is deliberately narrow.  It records three candidate
Cut-spine reductions and embeds their canonical certificates.  It does not
modify the theorem library or the 1,038-edge public graph, and it makes no
optimizer, Pareto, minimality, best-known, publication, freeze, training,
retrieval, or evaluation claim.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from peano_lab.engine.state import proof_resource_metrics
from peano_lab.kernel.artifact_codec import (
    decode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Cut, Proof
from peano_lab.library.candidate_validation import compile_candidate_body
from peano_lab.library.theorems import (
    THEOREMS,
    CheckedTheorem,
    TheoremSpec,
    _closed_formula,
    replay,
)

from .library_construction_rebuild_core import (
    ClosedCandidateCompilation,
    ConstructionRebuildCoreError,
    DependencyCertificate,
    compile_closed_candidate,
)
from .library_replay_pack import proof_tree_metrics


CONSTRUCTION_REBUILD_SCHEMA_FORMAT = (
    "peano-hydra-library-construction-rebuild-schema"
)
CONSTRUCTION_REBUILD_SCHEMA_VERSION = 1
CONSTRUCTION_REBUILD_SCHEMA_ID = "peano-hydra-library-construction-rebuild-v1"
CONSTRUCTION_REBUILD_SCHEMA_PATH = Path(__file__).with_name(
    "library-construction-rebuild-schema-v1.json"
)
CONSTRUCTION_REBUILD_SCHEMA_SHA256 = (
    "a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571"
)

CONSTRUCTION_REBUILD_FORMAT = "peano-hydra-library-construction-rebuild"
CONSTRUCTION_REBUILD_VERSION = 1
CONSTRUCTION_REBUILD_ID = "authoring-l0-construction-rebuild-candidate-v1"
CONSTRUCTION_REBUILD_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-construction-rebuild-root-preimage"
)
THEOREM_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-construction-rebuild-records-preimage"
)
STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
CERTIFICATE_REPRESENTATION = "peano-lab-v2"
SOURCE_CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"

MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 8_000_000
MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_ARTIFACT_BYTES = 8_000_000
MAX_JSON_DEPTH = 192
MAX_JSON_ITEMS = 2_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
THEOREM_COUNT = 3
RETAINED_DIRECT_EDGES = 25
CANDIDATE_DIRECT_EDGES = 22
RETAINED_PUBLIC_GRAPH_EDGES = 1_038

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_AUDIT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
)
_REPLAY_ROOT_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
_REPLAY_MANIFEST_RELATIVE = _REPLAY_ROOT_RELATIVE / "manifest.json"
_REPLAY_REPORT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)

AUDIT_ARTIFACT_SHA256 = (
    "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040"
)
AUDIT_ROOT_SHA256 = (
    "12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e"
)
AUDIT_THEOREM_RECORD_ROOT_SHA256 = (
    "8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784"
)
AUDIT_SCHEMA_ARTIFACT_SHA256 = (
    "ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff"
)
AUDIT_SCHEMA_SEMANTIC_SHA256 = (
    "54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4"
)
REPLAY_MANIFEST_ARTIFACT_SHA256 = (
    "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
)
REPLAY_MANIFEST_ROOT_SHA256 = (
    "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
)
REPLAY_ROOT_SHA256 = (
    "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
)
REPLAY_REPORT_ARTIFACT_SHA256 = (
    "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"
)
REPLAY_METRIC_SOURCE_RELATIVE = Path(
    "training/peano_hydra/library_replay_pack.py"
)
REPLAY_METRIC_SOURCE_SHA256 = (
    "8c5f3b44bed64bc3a49a7990d16a6f3c4a966b14c2bf4c732227041bc81506ee"
)
CORE_SOURCE_RELATIVE = Path(
    "training/peano_hydra/library_construction_rebuild_core.py"
)
CORE_SOURCE_SHA256 = (
    "98c2aa5b13b77a4f2e47c9d8663ff52c072e3cf61cac172dae523f30bfb25d10"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_EXPECTED = (
    {
        "index": 256,
        "name": "odd_add_odd",
        "omitted": "add_succ_left",
        "dependencies": ("mul_add", "add_assoc", "add_comm"),
        "closure_sha256": (
            "a4abec5d9eb955ed95f6eea761c96c3de0166b3df3c64fe8e898d8766ed5c5f2"
        ),
    },
    {
        "index": 376,
        "name": "finite_bounded_injective_surjective",
        "omitted": "beta_at_unique",
        "dependencies": (
            "finite_surjective_zero",
            "finite_contains_decidable",
            "finite_bounded_last_succ",
            "beta_prefix_swap_last_from_entries",
            "finite_swap_last_bounded",
            "finite_swap_last_injective",
            "finite_bounded_prefix_without_top",
            "finite_injective_prefix_succ",
            "finite_surjective_succ_from_prefix",
            "finite_swap_last_surjective_back",
            "finite_no_top_successor_gate",
            "le_succ",
            "le_refl",
            "lt_irrefl_expanded",
        ),
        "closure_sha256": (
            "a5b1ba200b4fe2f77c86a3b98e4870e05e178e0b21498f303b56a1ad61060363"
        ),
    },
    {
        "index": 379,
        "name": "beta_product_swap_last_invariant",
        "omitted": "le_refl",
        "dependencies": (
            "beta_product_replace_balance",
            "beta_product_succ_decompose",
            "beta_at_unique",
            "le_succ",
            "lt_irrefl_expanded",
        ),
        "closure_sha256": (
            "18c328d9374661586958db5e47441f49783a86d158afc0ac066d28f58c5bab37"
        ),
    },
)


class LibraryConstructionRebuildError(ValueError):
    """The A2.2 bundle, a pinned input, or a fresh rebuild is invalid."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _reject_float(value: str) -> object:
    raise ValueError(f"JSON floating-point number {value!r}")


def _validate_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> int:
    if depth > MAX_JSON_DEPTH:
        raise LibraryConstructionRebuildError(f"{path} exceeds the JSON depth limit")
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryConstructionRebuildError(
                f"{path} exceeds the JSON integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise LibraryConstructionRebuildError(
                f"{path} contains a Unicode surrogate"
            ) from None
        return 1
    if type(value) not in (list, dict):
        raise LibraryConstructionRebuildError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryConstructionRebuildError(f"{path} contains a cycle")
    if len(value) > MAX_JSON_ITEMS:
        raise LibraryConstructionRebuildError(f"{path} has too many items")
    descendants = ancestors | {marker}
    count = 1
    if type(value) is list:
        for index, item in enumerate(value):
            count += _validate_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=descendants,
            )
            if count > MAX_JSON_ITEMS:
                raise LibraryConstructionRebuildError(
                    "JSON document has too many items"
                )
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryConstructionRebuildError(f"{path} has a non-string key")
        count += _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=descendants,
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryConstructionRebuildError("JSON document has too many items")
    return count


def _compact_bytes(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> bytes:
    _validate_json(value)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryConstructionRebuildError(
            f"value is not canonical JSON: {exc}"
        ) from None
    if type(limit) is not int or limit < 1 or len(raw) > limit:
        raise LibraryConstructionRebuildError(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Encode one canonical retained JSON document."""

    _validate_json(value)
    try:
        raw = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryConstructionRebuildError(
            f"value is not canonical JSON: {exc}"
        ) from None
    if type(limit) is not int or limit < 1 or len(raw) > limit:
        raise LibraryConstructionRebuildError(
            f"canonical document exceeds the {limit}-byte limit"
        )
    return raw


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256_bytes(_compact_bytes(value, limit=limit))


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryConstructionRebuildError(f"{label} exceeds its byte limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise LibraryConstructionRebuildError(
            f"{label} is not strict JSON: {exc}"
        ) from None
    if type(value) is not dict:
        raise LibraryConstructionRebuildError(f"{label} must be one JSON object")
    _validate_json(value)
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryConstructionRebuildError(
            f"{label} is not canonical document JSON"
        )
    return value


def _safe_file(path: Path, *, label: str, limit: int) -> bytes:
    if not isinstance(path, Path):
        raise TypeError(f"{label} path must be pathlib.Path")
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryConstructionRebuildError(
                    f"{label} parent contains a link or non-directory component"
                )
    except LibraryConstructionRebuildError:
        raise
    except OSError as exc:
        raise LibraryConstructionRebuildError(
            f"cannot inspect {label} parent"
        ) from exc
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryConstructionRebuildError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryConstructionRebuildError(
                f"{label} must be a bounded regular file"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1_048_576, limit + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise LibraryConstructionRebuildError(
                    f"{label} exceeds its byte limit"
                )
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise LibraryConstructionRebuildError(f"{label} changed while read")
        return b"".join(chunks)
    except OSError as exc:
        raise LibraryConstructionRebuildError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository_root must be pathlib.Path or None")
    try:
        metadata = root.lstat()
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise LibraryConstructionRebuildError("cannot resolve repository_root") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise LibraryConstructionRebuildError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def construction_rebuild_schema() -> dict[str, object]:
    """Load and validate the binding A2.2 schema."""

    raw = _safe_file(
        CONSTRUCTION_REBUILD_SCHEMA_PATH,
        label="construction-rebuild schema",
        limit=MAX_SCHEMA_BYTES,
    )
    value = _decode_document(raw, "construction-rebuild schema", limit=MAX_SCHEMA_BYTES)
    if _sha256_json(value, limit=MAX_SCHEMA_BYTES) != CONSTRUCTION_REBUILD_SCHEMA_SHA256:
        raise LibraryConstructionRebuildError(
            "construction-rebuild schema semantic digest drifted"
        )
    if (
        value.get("format") != CONSTRUCTION_REBUILD_SCHEMA_FORMAT
        or value.get("id") != CONSTRUCTION_REBUILD_SCHEMA_ID
        or value.get("v") != CONSTRUCTION_REBUILD_SCHEMA_VERSION
    ):
        raise LibraryConstructionRebuildError(
            "construction-rebuild schema identity drifted"
        )
    return deepcopy(value)


def construction_rebuild_schema_identity() -> dict[str, object]:
    schema = construction_rebuild_schema()
    raw = canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "format": CONSTRUCTION_REBUILD_SCHEMA_FORMAT,
        "id": CONSTRUCTION_REBUILD_SCHEMA_ID,
        "sha256": CONSTRUCTION_REBUILD_SCHEMA_SHA256,
        "v": CONSTRUCTION_REBUILD_SCHEMA_VERSION,
    }


def _require_module_origin(module_name: str, expected: Path) -> object:
    module = importlib.import_module(module_name)
    source = getattr(module, "__file__", None)
    if type(source) is not str:
        raise LibraryConstructionRebuildError(
            f"cannot identify module {module_name!r}"
        )
    try:
        actual = Path(source).resolve(strict=True)
        wanted = expected.resolve(strict=True)
    except OSError as exc:
        raise LibraryConstructionRebuildError(
            f"cannot resolve module {module_name!r}"
        ) from exc
    if actual != wanted:
        raise LibraryConstructionRebuildError(
            f"module {module_name!r} origin drifted"
        )
    return module


def _load_fixed_inputs(
    root: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, TheoremSpec], dict[str, object]]:
    audit_raw = _safe_file(
        root / _AUDIT_RELATIVE, label="A2.1 audit", limit=MAX_DOCUMENT_BYTES
    )
    if _sha256_bytes(audit_raw) != AUDIT_ARTIFACT_SHA256:
        raise LibraryConstructionRebuildError("A2.1 audit artifact drifted")
    audit = _decode_document(audit_raw, "A2.1 audit", limit=MAX_DOCUMENT_BYTES)
    if (
        audit.get("root_sha256") != AUDIT_ROOT_SHA256
        or audit.get("theorem_records", {}).get("root_sha256")
        != AUDIT_THEOREM_RECORD_ROOT_SHA256
        or audit.get("schema", {}).get("artifact_sha256")
        != AUDIT_SCHEMA_ARTIFACT_SHA256
        or audit.get("schema", {}).get("sha256")
        != AUDIT_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryConstructionRebuildError("A2.1 audit identity drifted")

    manifest_raw = _safe_file(
        root / _REPLAY_MANIFEST_RELATIVE,
        label="replay manifest",
        limit=MAX_DOCUMENT_BYTES,
    )
    if _sha256_bytes(manifest_raw) != REPLAY_MANIFEST_ARTIFACT_SHA256:
        raise LibraryConstructionRebuildError("replay manifest artifact drifted")
    manifest = _decode_document(
        manifest_raw, "replay manifest", limit=MAX_DOCUMENT_BYTES
    )
    if (
        manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != 384
    ):
        raise LibraryConstructionRebuildError("replay manifest identity drifted")
    report_raw = _safe_file(
        root / _REPLAY_REPORT_RELATIVE,
        label="replay report",
        limit=MAX_DOCUMENT_BYTES,
    )
    if _sha256_bytes(report_raw) != REPLAY_REPORT_ARTIFACT_SHA256:
        raise LibraryConstructionRebuildError("replay report artifact drifted")

    compiler = audit.get("inputs", {}).get("compiler")
    if type(compiler) is not dict or type(compiler.get("sources")) is not list:
        raise LibraryConstructionRebuildError("A2.1 compiler identity is malformed")
    for source in compiler["sources"]:
        if type(source) is not dict:
            raise LibraryConstructionRebuildError("compiler source is malformed")
        relative, digest = source.get("path"), source.get("sha256")
        if type(relative) is not str or _SHA256_RE.fullmatch(str(digest)) is None:
            raise LibraryConstructionRebuildError("compiler source identity is malformed")
        raw = _safe_file(
            root / relative,
            label=f"compiler source {relative!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryConstructionRebuildError(
                f"compiler source {relative!r} drifted"
            )
    core_raw = _safe_file(
        root / CORE_SOURCE_RELATIVE,
        label="construction-rebuild core",
        limit=MAX_SOURCE_FILE_BYTES,
    )
    if _sha256_bytes(core_raw) != CORE_SOURCE_SHA256:
        raise LibraryConstructionRebuildError("construction-rebuild core drifted")
    replay_metric_raw = _safe_file(
        root / REPLAY_METRIC_SOURCE_RELATIVE,
        label="replay tree-metric source",
        limit=MAX_SOURCE_FILE_BYTES,
    )
    if _sha256_bytes(replay_metric_raw) != REPLAY_METRIC_SOURCE_SHA256:
        raise LibraryConstructionRebuildError("replay tree-metric source drifted")

    core_module = _require_module_origin(
        "training.peano_hydra.library_construction_rebuild_core",
        root / CORE_SOURCE_RELATIVE,
    )
    candidate_module = _require_module_origin(
        "peano_lab.library.candidate_validation",
        root / "peano-lab/py/peano_lab/library/candidate_validation.py",
    )
    theorem_module = _require_module_origin(
        "peano_lab.library.theorems",
        root / "peano-lab/py/peano_lab/library/theorems.py",
    )
    checker_module = _require_module_origin(
        "peano_lab.kernel.checker",
        root / "peano-lab/py/peano_lab/kernel/checker.py",
    )
    codec_module = _require_module_origin(
        "peano_lab.kernel.artifact_codec",
        root / "peano-lab/py/peano_lab/kernel/artifact_codec.py",
    )
    replay_module = _require_module_origin(
        "training.peano_hydra.library_replay_pack",
        root / "training/peano_hydra/library_replay_pack.py",
    )
    state_module = _require_module_origin(
        "peano_lab.engine.state",
        root / "peano-lab/py/peano_lab/engine/state.py",
    )
    if (
        getattr(core_module, "compile_closed_candidate", None)
        is not compile_closed_candidate
        or getattr(core_module, "ClosedCandidateCompilation", None)
        is not ClosedCandidateCompilation
        or getattr(core_module, "ConstructionRebuildCoreError", None)
        is not ConstructionRebuildCoreError
        or getattr(core_module, "DependencyCertificate", None)
        is not DependencyCertificate
        or getattr(core_module, "check", None) is not check
        or getattr(core_module, "compile_candidate_body", None)
        is not compile_candidate_body
        or getattr(core_module, "_closed_formula", None) is not _closed_formula
        or getattr(candidate_module, "compile_candidate_body", None)
        is not compile_candidate_body
        or getattr(theorem_module, "THEOREMS", None) is not THEOREMS
        or getattr(theorem_module, "TheoremSpec", None) is not TheoremSpec
        or getattr(theorem_module, "CheckedTheorem", None) is not CheckedTheorem
        or getattr(theorem_module, "_closed_formula", None) is not _closed_formula
        or getattr(theorem_module, "replay", None) is not replay
        or getattr(checker_module, "check", None) is not check
        or getattr(codec_module, "decode_artifact", None) is not decode_artifact
        or getattr(codec_module, "encode_artifact_bounded", None)
        is not encode_artifact_bounded
        or getattr(codec_module, "encode_formula", None) is not encode_formula
        or getattr(codec_module, "encode_proof", None) is not encode_proof
        or getattr(replay_module, "proof_tree_metrics", None)
        is not proof_tree_metrics
        or getattr(state_module, "proof_resource_metrics", None)
        is not proof_resource_metrics
    ):
        raise LibraryConstructionRebuildError("rebuild runtime callable drifted")

    specs: dict[str, TheoremSpec] = {}
    for spec in THEOREMS:
        if type(spec) is not TheoremSpec or spec.name in specs:
            raise LibraryConstructionRebuildError("theorem source table is malformed")
        specs[spec.name] = spec
    if len(specs) != 384:
        raise LibraryConstructionRebuildError("theorem source count drifted")
    return audit, manifest, specs, deepcopy(compiler)


def _rows_by_name(document: Mapping[str, object], label: str) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list:
        raise LibraryConstructionRebuildError(f"{label} theorem rows are malformed")
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if type(row) is not dict or type(row.get("name")) is not str:
            raise LibraryConstructionRebuildError(f"{label} theorem row is malformed")
        if row["name"] in result:
            raise LibraryConstructionRebuildError(
                f"{label} has duplicate theorem {row['name']!r}"
            )
        result[row["name"]] = row
    return result


def _decode_packed_certificate(
    root: Path,
    row: Mapping[str, object],
    *,
    expected_target: Formula,
) -> DependencyCertificate:
    name = row.get("name")
    artifact = row.get("artifact")
    if type(name) is not str or type(artifact) is not dict:
        raise LibraryConstructionRebuildError("replay theorem artifact is malformed")
    relative = artifact.get("path")
    if (
        type(relative) is not str
        or Path(relative).is_absolute()
        or Path(relative).parts[:1] != ("certificates",)
        or ".." in Path(relative).parts
    ):
        raise LibraryConstructionRebuildError("replay artifact path is unsafe")
    raw = _safe_file(
        root / _REPLAY_ROOT_RELATIVE / relative,
        label=f"replay certificate {name!r}",
        limit=MAX_ARTIFACT_BYTES,
    )
    if (
        len(raw) != artifact.get("bytes")
        or _sha256_bytes(raw) != artifact.get("sha256")
    ):
        raise LibraryConstructionRebuildError(
            f"replay certificate {name!r} identity drifted"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=1_000_000,
            max_depth=512,
        )
    except Exception as exc:
        raise LibraryConstructionRebuildError(
            f"replay certificate {name!r} cannot be decoded"
        ) from exc
    if (
        fuel != artifact.get("fuel")
        or target != expected_target
        or _sha256_bytes(encode_formula(target)) != row.get("formula_sha256")
        or _sha256_bytes(encode_proof(proof)) != row.get("proof_term_sha256")
        or encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        != raw
        or not check((), proof, expected_target)
    ):
        raise LibraryConstructionRebuildError(
            f"replay certificate {name!r} failed exact empty-context replay"
        )
    return DependencyCertificate(name=name, target=target, proof=proof)


def _source_certificate(
    name: str,
    *,
    packed: DependencyCertificate,
    replay_row: Mapping[str, object],
) -> DependencyCertificate:
    """Recover the pinned source-stage proof DAG and bind it to packed bytes."""

    try:
        checked = replay(name)
    except Exception as exc:
        raise LibraryConstructionRebuildError(
            f"cannot replay source certificate {name!r}"
        ) from exc
    if (
        type(checked) is not CheckedTheorem
        or checked.spec.name != name
        or checked.formula != packed.target
        or encode_proof(checked.certificate) != encode_proof(packed.proof)
        or _sha256_bytes(repr(checked.certificate).encode("utf-8"))
        != replay_row.get("construction_metrics", {}).get(
            "source_certificate_sha256"
        )
        or not check((), checked.certificate, checked.formula)
    ):
        raise LibraryConstructionRebuildError(
            f"source certificate {name!r} differs from the retained pack"
        )
    return DependencyCertificate(
        name=name, target=checked.formula, proof=checked.certificate
    )


def _resource_metrics(proof: Proof) -> dict[str, int]:
    nodes, depth, objects, edges, reused = proof_resource_metrics(proof)
    tree = proof_tree_metrics(proof)
    if tree["proof_nodes"] != nodes or tree["proof_depth"] != depth:
        raise LibraryConstructionRebuildError("proof metric implementations disagree")
    return {
        "cut_nodes": tree["cut_nodes"],
        "distinct_proof_objects": objects,
        "proof_depth": depth,
        "proof_edges": edges,
        "proof_nodes": nodes,
        "reused_proof_references": reused,
    }


def _body_receipt(compilation: ClosedCandidateCompilation) -> dict[str, object]:
    if not check((), compilation.body.certificate, compilation.body.target):
        raise LibraryConstructionRebuildError(
            "fresh dependency-curried body failed independent kernel check"
        )
    receipt = compilation.body.receipt
    result: dict[str, object] = {
        "certificate_representation": "peano-lab-v2-encoded-proof",
        "certificate_sha256": _sha256_bytes(
            encode_proof(compilation.body.certificate)
        ),
        "dependency_count": receipt.dependency_count,
        "kernel_accepted": True,
        "metrics": {
            "proof_depth": receipt.proof_depth,
            "proof_edges": receipt.proof_edges,
            "proof_nodes": receipt.proof_nodes,
            "proof_objects": receipt.proof_objects,
            "reused_objects": receipt.reused_objects,
        },
        "target_formula_sha256": _sha256_bytes(encode_formula(compilation.body.target)),
    }
    result["receipt_sha256"] = _sha256_json(result)
    return result


def _transitive_closure(
    dependencies: tuple[str, ...],
    *,
    replay_rows: Mapping[str, dict[str, object]],
) -> list[str]:
    seen: set[str] = set()
    pending = list(dependencies)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = replay_rows.get(name)
        if row is None or type(row.get("declared_dependencies")) is not list:
            raise LibraryConstructionRebuildError(
                f"cannot compute retained closure through {name!r}"
            )
        seen.add(name)
        pending.extend(row["declared_dependencies"])
    return sorted(seen, key=lambda name: replay_rows[name]["index"])


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _build_candidate_construction_rebuild(root: Path) -> dict[str, object]:
    audit, manifest, specs, compiler_identity = _load_fixed_inputs(root)
    audit_rows = _rows_by_name(audit, "A2.1 audit")
    replay_rows = _rows_by_name(manifest, "replay manifest")
    certificate_cache: dict[str, DependencyCertificate] = {}
    result_rows: list[dict[str, object]] = []

    for expected in _EXPECTED:
        name = expected["name"]
        index = expected["index"]
        omitted = expected["omitted"]
        dependencies = expected["dependencies"]
        if (
            type(name) is not str
            or type(index) is not int
            or type(omitted) is not str
            or type(dependencies) is not tuple
        ):
            raise LibraryConstructionRebuildError("internal expected row is malformed")
        audit_row = audit_rows.get(name)
        replay_row = replay_rows.get(name)
        spec = specs.get(name)
        if audit_row is None or replay_row is None or type(spec) is not TheoremSpec:
            raise LibraryConstructionRebuildError(f"missing source theorem {name!r}")
        current = tuple(replay_row.get("declared_dependencies", ()))
        if (
            audit_row.get("index") != index
            or replay_row.get("index") != index
            or tuple(audit_row.get("declared_dependencies", ())) != current
            or tuple(audit_row.get("candidate_publication_union", ()))
            != dependencies
            or audit_row.get("requires_certificate_rebuild") is not True
            or tuple(spec.dependencies) != current
            or spec.statement != replay_row.get("statement_source")
            or list(spec.script) != replay_row.get("script")
            or audit_row.get("statement", {}).get("source_sha256")
            != replay_row.get("statement_source_sha256")
            or audit_row.get("statement", {}).get("formula_sha256")
            != replay_row.get("formula_sha256")
            or audit_row.get("script", {}).get("script_sha256")
            != replay_row.get("script_sha256")
            or audit_row.get("script", {}).get("command_count") != len(spec.script)
            or omitted not in current
            or tuple(item for item in current if item != omitted) != dependencies
        ):
            raise LibraryConstructionRebuildError(
                f"source/A2.1/replay join drifted for {name!r}"
            )

        positive_attempts = [
            attempt
            for attempt in audit_row.get("recipe_audit", {}).get("attempts", [])
            if type(attempt) is dict
            and attempt.get("outcome") == "kernel-accepted"
            and attempt.get("omitted_dependency") == omitted
        ]
        if len(positive_attempts) != 1:
            raise LibraryConstructionRebuildError(
                f"A2.1 omission evidence drifted for {name!r}"
            )
        positive_attempt = positive_attempts[0]
        if tuple(positive_attempt.get("after_dependencies", ())) != dependencies:
            raise LibraryConstructionRebuildError(
                f"A2.1 reduced vector drifted for {name!r}"
            )

        reduced = replace(spec, dependencies=dependencies)
        carriers: dict[str, DependencyCertificate] = {}
        import_receipts: list[dict[str, object]] = []
        for dependency in dependencies:
            dependency_row = replay_rows.get(dependency)
            dependency_spec = specs.get(dependency)
            if dependency_row is None or type(dependency_spec) is not TheoremSpec:
                raise LibraryConstructionRebuildError(
                    f"missing dependency source {dependency!r}"
                )
            if dependency not in certificate_cache:
                packed_dependency = _decode_packed_certificate(
                    root,
                    dependency_row,
                    expected_target=_closed_formula(dependency_spec.statement),
                )
                certificate_cache[dependency] = _source_certificate(
                    dependency,
                    packed=packed_dependency,
                    replay_row=dependency_row,
                )
            carriers[dependency] = certificate_cache[dependency]
            import_receipts.append(
                {
                    "artifact_sha256": dependency_row["artifact"]["sha256"],
                    "formula_sha256": dependency_row["formula_sha256"],
                    "index": dependency_row["index"],
                    "name": dependency,
                    "proof_term_sha256": dependency_row["proof_term_sha256"],
                }
            )
        try:
            compilation = compile_closed_candidate(
                reduced,
                core=specs,
                dependency_certificates=carriers,
            )
        except ConstructionRebuildCoreError as exc:
            raise LibraryConstructionRebuildError(
                f"fresh construction failed for {name!r}: {exc}"
            ) from exc
        body_receipt = _body_receipt(compilation)
        if body_receipt != positive_attempt.get("positive_receipt"):
            raise LibraryConstructionRebuildError(
                f"fresh dependency-curried body differs from A2.1 for {name!r}"
            )
        target, proof = compilation.target, compilation.proof
        if _sha256_bytes(encode_formula(target)) != replay_row.get("formula_sha256"):
            raise LibraryConstructionRebuildError(
                f"rebuilt original target drifted for {name!r}"
            )
        metrics = _resource_metrics(proof)
        fuel = FUEL_MULTIPLIER * metrics["proof_nodes"] + FUEL_OFFSET
        artifact = encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        decoded_fuel, decoded_target, decoded_proof = decode_artifact(
            artifact,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=1_000_000,
            max_depth=512,
        )
        if (
            decoded_fuel != fuel
            or decoded_target != target
            or encode_proof(decoded_proof) != encode_proof(proof)
            or not check((), decoded_proof, target)
        ):
            raise LibraryConstructionRebuildError(
                f"encoded construction failed fresh replay for {name!r}"
            )

        # Also replay the exact predecessor certificate being compared.
        submitted_packed = _decode_packed_certificate(
            root, replay_row, expected_target=_closed_formula(spec.statement)
        )
        submitted = _source_certificate(
            name, packed=submitted_packed, replay_row=replay_row
        )
        submitted_metrics = replay_row.get("construction_metrics")
        if (
            type(submitted_metrics) is not dict
            or proof_tree_metrics(submitted_packed.proof)
            != replay_row.get("packed_tree_metrics")
            or _resource_metrics(submitted.proof)
            != {
                key: submitted_metrics[key]
                for key in (
                    "cut_nodes",
                    "distinct_proof_objects",
                    "proof_depth",
                    "proof_edges",
                    "proof_nodes",
                    "reused_proof_references",
                )
            }
        ):
            raise LibraryConstructionRebuildError(
                f"submitted metrics drifted for {name!r}"
            )

        closure = _transitive_closure(dependencies, replay_rows=replay_rows)
        closure_lf_sha256 = _sha256_bytes(
            ("\n".join(closure) + "\n").encode("utf-8")
        )
        if omitted not in closure or closure_lf_sha256 != expected["closure_sha256"]:
            raise LibraryConstructionRebuildError(
                f"transitive-closure receipt drifted for {name!r}"
            )
        encoded_b64 = base64.b64encode(artifact).decode("ascii")
        if base64.b64decode(encoded_b64, validate=True) != artifact:
            raise LibraryConstructionRebuildError("artifact base64 round trip failed")

        compared_keys = (
            "artifact_bytes",
            "cut_nodes",
            "proof_depth",
            "proof_nodes",
        )
        submitted_values = {
            "artifact_bytes": replay_row["artifact"]["bytes"],
            **{
                key: replay_row["packed_tree_metrics"][key]
                for key in compared_keys
                if key != "artifact_bytes"
            },
        }
        rebuilt_values = {
            "artifact_bytes": len(artifact),
            **{
                key: metrics[key]
                for key in compared_keys
                if key != "artifact_bytes"
            },
        }
        row: dict[str, object] = {
            "a2_complete": False,
            "a2_1": {
                "accepted_omission_attempt_record_sha256": positive_attempt[
                    "record_sha256"
                ],
                "audit_record_sha256": audit_row["record_sha256"],
                "requires_certificate_rebuild_before": True,
                "route_receipt_sha256": audit_row["submitted_construction"][
                    "leave_one_out"
                ]["sha256"],
            },
            "body_receipt": body_receipt,
            "candidate_direct_dependencies": list(dependencies),
            "comparison": {
                "claim": "descriptive-predecessor-delta-only",
                "delta_rebuilt_minus_submitted": {
                    key: rebuilt_values[key] - submitted_values[key]
                    for key in compared_keys
                },
                "rebuilt": rebuilt_values,
                "submitted": submitted_values,
                "metric_basis": "canonical-artifact-and-intrinsic-proof-tree-only",
            },
            "construction_rebuild_complete": True,
            "dependency_vectors_complete": False,
            "direct_cut_spine": {
                "dependencies": list(dependencies),
                "dependency_artifacts": import_receipts,
                "omitted_direct_dependency": omitted,
                "relation": "selected-direct-cuts-only",
            },
            "index": index,
            "lineage_complete": False,
            "minimality_claim": False,
            "name": name,
            "optimized_best_known": False,
            "optimized_vector_independently_audited": False,
            "original": {
                "formula_sha256": replay_row["formula_sha256"],
                "script": list(spec.script),
                "script_sha256": replay_row["script_sha256"],
                "statement_source": spec.statement,
                "statement_source_sha256": replay_row[
                    "statement_source_sha256"
                ],
            },
            "public_graph_applied": False,
            "publication_union_complete": False,
            "publication_union_verified": False,
            "rebuilt_certificate": {
                "artifact_base64": encoded_b64,
                "artifact_bytes": len(artifact),
                "artifact_sha256": _sha256_bytes(artifact),
                "certificate_representation": CERTIFICATE_REPRESENTATION,
                "fuel": fuel,
                "formula_sha256": _sha256_bytes(encode_formula(target)),
                "kernel_accepted": True,
                "kernel_context": "empty",
                "logic_mode": LOGIC_MODE,
                "construction_metrics": metrics,
                "construction_metrics_basis": (
                    "non-comparable-schedule-dependent-python-object-alias-observation"
                ),
                "identity_metrics_comparable": False,
                "identity_metrics_claim": (
                    "observation-only-schedule-and-assembly-dependent"
                ),
                "packed_tree_metrics": {
                    key: metrics[key]
                    for key in ("cut_nodes", "proof_depth", "proof_nodes")
                },
                "proof_term_sha256": _sha256_bytes(encode_proof(proof)),
                "source_certificate_representation": (
                    SOURCE_CERTIFICATE_REPRESENTATION
                ),
                "source_certificate_sha256": _sha256_bytes(
                    repr(proof).encode("utf-8")
                ),
            },
            "retained_direct_dependencies": list(current),
            "review_complete": False,
            "submitted_certificate": {
                "artifact_bytes": replay_row["artifact"]["bytes"],
                "artifact_sha256": replay_row["artifact"]["sha256"],
                "construction_metrics": deepcopy(submitted_metrics),
                "construction_metrics_basis": (
                    "non-comparable-retained-source-python-object-alias-observation"
                ),
                "identity_metrics_comparable": False,
                "proof_term_sha256": replay_row["proof_term_sha256"],
            },
            "transitive_closure": {
                "dependency_count": len(closure),
                "dependencies_in_replay_order": closure,
                "lf_sha256": closure_lf_sha256,
                "omitted_direct_dependency": omitted,
                "omitted_name_still_reachable": True,
                "source_graph": "retained-1038-edge-replay-manifest",
            },
        }
        row["record_sha256"] = _record_hash(row)
        result_rows.append(row)

    identities = [
        {"index": row["index"], "name": row["name"], "record_sha256": row["record_sha256"]}
        for row in result_rows
    ]
    records_preimage = {
        "format": THEOREM_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": 1,
    }
    theorem_records = {
        "count": len(result_rows),
        "preimage": records_preimage,
        "root_sha256": _sha256_json(records_preimage),
    }
    aggregate = {
        "artifact_bytes_delta_total": sum(
            row["comparison"]["delta_rebuilt_minus_submitted"]["artifact_bytes"]
            for row in result_rows
        ),
        "candidate_direct_dependency_edges_across_three_rebuilds": (
            CANDIDATE_DIRECT_EDGES
        ),
        "cut_nodes_delta_total": sum(
            row["comparison"]["delta_rebuilt_minus_submitted"]["cut_nodes"]
            for row in result_rows
        ),
        "direct_edges_removed_in_candidate_rebuilds": 3,
        "proof_nodes_delta_total": sum(
            row["comparison"]["delta_rebuilt_minus_submitted"]["proof_nodes"]
            for row in result_rows
        ),
        "rebuilt_theorem_count": THEOREM_COUNT,
        "retained_direct_dependency_edges_across_three_rebuilds": (
            RETAINED_DIRECT_EDGES
        ),
        "retained_public_graph_edges": RETAINED_PUBLIC_GRAPH_EDGES,
        "transitively_reachable_omitted_names": 3,
    }
    inputs = {
        "compiler": compiler_identity,
        "construction_core": {
            "callable": (
                "training.peano_hydra.library_construction_rebuild_core."
                "compile_closed_candidate"
            ),
            "path": CORE_SOURCE_RELATIVE.as_posix(),
            "sha256": CORE_SOURCE_SHA256,
            "v": 1,
        },
        "dependency_audit": {
            "artifact_path": _AUDIT_RELATIVE.as_posix(),
            "artifact_sha256": AUDIT_ARTIFACT_SHA256,
            "root_sha256": AUDIT_ROOT_SHA256,
            "schema_artifact_sha256": AUDIT_SCHEMA_ARTIFACT_SHA256,
            "schema_semantic_sha256": AUDIT_SCHEMA_SEMANTIC_SHA256,
            "theorem_record_root_sha256": AUDIT_THEOREM_RECORD_ROOT_SHA256,
        },
        "replay_pack": {
            "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
            "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
            "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
            "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
            "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
            "replay_root_sha256": REPLAY_ROOT_SHA256,
        },
        "replay_tree_metric_source": {
            "callable": (
                "training.peano_hydra.library_replay_pack.proof_tree_metrics"
            ),
            "path": REPLAY_METRIC_SOURCE_RELATIVE.as_posix(),
            "sha256": REPLAY_METRIC_SOURCE_SHA256,
        },
    }
    body = {
        "a2_complete": False,
        "aggregate": aggregate,
        "dependency_vectors_complete": False,
        "evaluation_eligible": False,
        "format": CONSTRUCTION_REBUILD_FORMAT,
        "freeze_ready": False,
        "id": CONSTRUCTION_REBUILD_ID,
        "inputs": inputs,
        "logic_mode": LOGIC_MODE,
        "lineage_complete": False,
        "minimality_claim": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "publication_ready": False,
        "publication_union_complete": False,
        "publication_union_verified": False,
        "retrieval_eligible": False,
        "review_complete": False,
        "schema": construction_rebuild_schema_identity(),
        "status": STATUS,
        "theorem_count": THEOREM_COUNT,
        "theorem_records": theorem_records,
        "training_eligible": False,
        "v": CONSTRUCTION_REBUILD_VERSION,
    }
    root_preimage = {
        "format": CONSTRUCTION_REBUILD_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": CONSTRUCTION_REBUILD_VERSION,
    }
    return {
        **body,
        "root_preimage": root_preimage,
        "root_sha256": _sha256_json(root_preimage),
        "theorems": result_rows,
    }


def build_candidate_construction_rebuild(
    *, repository_root: Path | None = None
) -> dict[str, object]:
    """Freshly rebuild and empty-context-check the exact three A2.2 rows."""

    construction_rebuild_schema()
    root = _repository_root(repository_root)
    result = _build_candidate_construction_rebuild(root)
    canonical_document_bytes(result)
    return deepcopy(result)


def validate_construction_rebuild(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate by full reconstruction from the exact pinned source inputs."""

    construction_rebuild_schema()
    if type(value) is not dict:
        raise LibraryConstructionRebuildError(
            "construction rebuild must be one object"
        )
    _validate_json(value)
    expected = _build_candidate_construction_rebuild(
        _repository_root(repository_root)
    )
    if value != expected:
        raise LibraryConstructionRebuildError(
            "construction rebuild differs from exact fixed-source reconstruction"
        )
    return _decode_document(
        canonical_document_bytes(expected),
        "validated construction rebuild",
        limit=MAX_DOCUMENT_BYTES,
    )


def load_construction_rebuild(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one bounded canonical sidecar and fully reconstruct its evidence."""

    raw = _safe_file(
        path, label="construction rebuild", limit=MAX_DOCUMENT_BYTES
    )
    value = _decode_document(
        raw, "construction rebuild", limit=MAX_DOCUMENT_BYTES
    )
    return validate_construction_rebuild(value, repository_root=repository_root)


__all__ = [
    "CONSTRUCTION_REBUILD_SCHEMA_FORMAT",
    "CONSTRUCTION_REBUILD_SCHEMA_ID",
    "CONSTRUCTION_REBUILD_SCHEMA_PATH",
    "CONSTRUCTION_REBUILD_SCHEMA_SHA256",
    "CONSTRUCTION_REBUILD_SCHEMA_VERSION",
    "LibraryConstructionRebuildError",
    "build_candidate_construction_rebuild",
    "canonical_document_bytes",
    "construction_rebuild_schema",
    "construction_rebuild_schema_identity",
    "load_construction_rebuild",
    "validate_construction_rebuild",
]
