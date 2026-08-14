"""Candidate-only A2 dependency observations for the retained PA library.

The builder reconstructs exactly the selected 384-theorem replay pack and
executes a deterministic reverse-order fixed-point leave-one-out audit of each
retained tactic recipe.  A dependency is removed only after the reduced
dependency-curried proof passes the independent Python kernel.  Conversely, a
failed omission is merely an observation about this exact tactic recipe; it is
not mathematical necessity, theorem-level minimality, or negative evidence.

This sidecar never changes the retained theorem certificates, metadata,
catalog, documentation, or public graph.  A row whose candidate construction
vector differs from its retained submitted construction is explicitly marked
as requiring a later certificate rebuild.  Every authority and eligibility
flag remains false.
"""

from __future__ import annotations

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

from peano_lab.engine.proof_reduction import ProofReductionError
from peano_lab.engine.tactics import InvalidProof, TacticError, TacticLimit
from peano_lab.kernel.artifact_codec import encode_formula, encode_proof
from peano_lab.kernel.checker import check
from peano_lab.library.candidate_validation import (
    CandidateBodyCompilation,
    CandidateBodyError,
    compile_candidate_body,
)
from peano_lab.library.theorems import THEOREMS, TheoremSpec


DEPENDENCY_AUDIT_SCHEMA_FORMAT = "peano-hydra-library-dependency-audit-schema"
DEPENDENCY_AUDIT_SCHEMA_VERSION = 1
DEPENDENCY_AUDIT_SCHEMA_ID = "peano-hydra-library-dependency-audit-v1"
DEPENDENCY_AUDIT_SCHEMA_PATH = Path(__file__).with_name(
    "library-dependency-audit-schema-v1.json"
)
# Semantic SHA-256 of the binding closed schema.  The transport hash is
# reported separately so whitespace can never masquerade as a semantic edit.
DEPENDENCY_AUDIT_SCHEMA_SHA256 = (
    "54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4"
)

DEPENDENCY_AUDIT_FORMAT = "peano-hydra-library-dependency-audit"
DEPENDENCY_AUDIT_VERSION = 1
DEPENDENCY_AUDIT_ID = "authoring-l0-dependency-audit-candidate-v1"
DEPENDENCY_AUDIT_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-dependency-audit-root-preimage"
)
THEOREM_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-dependency-theorem-records-preimage"
)
ATTEMPT_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-dependency-attempt-records-preimage"
)
RECIPE_AUDIT_PREIMAGE_FORMAT = (
    "peano-hydra-library-dependency-recipe-audit-preimage"
)
ROUTE_RECEIPT_PREIMAGE_FORMAT = (
    "peano-hydra-library-dependency-route-receipt-preimage"
)
ALGORITHM_ID = "peano-hydra-exact-recipe-loo-v1"
COMPILER_CALLABLE = (
    "peano_lab.library.candidate_validation.compile_candidate_body"
)
COMPILER_VERSION = 1
COMPILER_SOURCE_COUNT = 20
COMPILER_SOURCE_ROOT_SHA256 = (
    "66a9840096a8edab39b511384401c0cdd4066700983952246752ec3dafdc926c"
)

STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
THEOREM_COUNT = 384
DECLARED_DEPENDENCY_EDGES = 1_038

MAX_SCHEMA_BYTES = 1_000_000
MAX_AUDIT_BYTES = 16_000_000
MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_JSON_DEPTH = 192
MAX_JSON_ITEMS = 3_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
MAX_DEPENDENCIES_PER_THEOREM = 256
MAX_PASSES_PER_THEOREM = 257
MAX_ATTEMPTS = 4_000

REPOSITORY_COMMIT = "32803924d7def862ccf0b738cd1ed494a3165f7e"
REPOSITORY_TREE = "e945e4963ad53b1c07008fd8356980bdacc3bafe"
REPOSITORY_URL = "https://github.com/nasqret/vietnam2026"

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE_RELATIVE = Path("artifacts/peano-hydra/l0-documentation-candidate-v1")
_REPLAY_MANIFEST_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
_REPLAY_REPORT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)
_PREDECESSOR_RELATIVE = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json"
)

BUNDLE_SCHEMA_ARTIFACT_SHA256 = (
    "a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c"
)
BUNDLE_SCHEMA_SEMANTIC_SHA256 = (
    "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d"
)
BUNDLE_EXPLICIT_ARTIFACT_SHA256 = (
    "f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936"
)
BUNDLE_EXPLICIT_ROOT_SHA256 = (
    "b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da"
)
BUNDLE_EXPLICIT_ORDERED_RECORD_ROOT_SHA256 = (
    "6e3c28746ae72dcb0ab820378c7dc59e982c3c9d7b832fc8b8faf0940b7f20a0"
)
BUNDLE_MANIFEST_ARTIFACT_SHA256 = (
    "5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf"
)
BUNDLE_MANIFEST_ROOT_SHA256 = (
    "8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4"
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
REPLAY_CATALOG_ARTIFACT_SHA256 = (
    "326ffe660da6e34a3aa12e0aa13096078a0bf20c45c440049aaf5d5bed1f1be7"
)
REPLAY_CATALOG_ORDERED_ROOT_SHA256 = (
    "73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b"
)

PREDECESSOR_ARTIFACT_SHA256 = (
    "dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d"
)
PREDECESSOR_ROOT_SHA256 = (
    "e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e"
)
PREDECESSOR_THEOREM_RECORD_ROOT_SHA256 = (
    "22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMPILER_SOURCES = (
    ("peano-lab/py/peano_lab/__init__.py", "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a"),
    ("peano-lab/py/peano_lab/engine/__init__.py", "1fbd27721e00e873b4b6839508b63889e6ba8a4a51165b11e042c05270d1308b"),
    ("peano-lab/py/peano_lab/engine/decide.py", "07044458d92b68781d95091fabbe0fbc4a476c58f3821e0c806553e0813c2e0a"),
    ("peano-lab/py/peano_lab/engine/induction.py", "4bb1db5f3b944e1f9a0ebe388ab76970aae055bf4d1171d896fbb0323172545f"),
    ("peano-lab/py/peano_lab/engine/norm_num.py", "79d9ebe369348779aca6c7f12932a1204756a13d631ebd69f2612de082ab13b1"),
    ("peano-lab/py/peano_lab/engine/proof_reduction.py", "deb17a5a0d5562f73248d6fbaa8db46b923c7bab07e491f37cb98e5e19a8251f"),
    ("peano-lab/py/peano_lab/engine/rewrite.py", "05f0b5fe8d46910d9cc2b1604d96756aa68e42339ca90afc094d60bfce48aa5f"),
    ("peano-lab/py/peano_lab/engine/state.py", "453904142273f14d01379c73c637be3476d035b093047587ff6990f1d572ac2f"),
    ("peano-lab/py/peano_lab/engine/tactics.py", "fde9605bce6e14513260ffeb69eea8ae40a6ad7d44da3ff550fb3edf9b6396e4"),
    ("peano-lab/py/peano_lab/engine/trace.py", "d9a7b2aa789fefd8d0da8d6ce6b6ae37b925f92a3e611e0809b02cd5e9173df7"),
    ("peano-lab/py/peano_lab/kernel/__init__.py", "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84"),
    ("peano-lab/py/peano_lab/kernel/artifact_codec.py", "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110"),
    ("peano-lab/py/peano_lab/kernel/checker.py", "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19"),
    ("peano-lab/py/peano_lab/kernel/formulas.py", "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"),
    ("peano-lab/py/peano_lab/kernel/proofs.py", "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2"),
    ("peano-lab/py/peano_lab/kernel/subst.py", "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3"),
    ("peano-lab/py/peano_lab/kernel/terms.py", "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"),
    ("peano-lab/py/peano_lab/library/__init__.py", "70035fa65aafe8bed7a7b1538b0f4fdbf895ca1d5ddeef3625b9fdb9fb4e77e5"),
    ("peano-lab/py/peano_lab/library/candidate_validation.py", "b41e6587d32e27152e1358b3067c72b869357674548f05aa4ef5e86cf9bdc30a"),
    ("peano-lab/py/peano_lab/library/theorems.py", "bfa6fad2c91a774b37c3ee458e9b59d679f7257a1ab4b2bef3f88bbccdb82a2f"),
)


class LibraryDependencyAuditError(ValueError):
    """The candidate audit, its inputs, or an exact replay is invalid."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


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
        raise LibraryDependencyAuditError(f"{path} exceeds the JSON depth limit")
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryDependencyAuditError(f"{path} exceeds the JSON integer domain")
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise LibraryDependencyAuditError(
                f"{path} contains a Unicode surrogate"
            ) from None
        return 1
    if type(value) not in (list, dict):
        raise LibraryDependencyAuditError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryDependencyAuditError(f"{path} contains a cycle")
    if len(value) > MAX_JSON_ITEMS:
        raise LibraryDependencyAuditError(f"{path} has too many items")
    next_ancestors = ancestors | {marker}
    count = 1
    if type(value) is list:
        for index, item in enumerate(value):
            count += _validate_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=next_ancestors,
            )
            if count > MAX_JSON_ITEMS:
                raise LibraryDependencyAuditError("JSON document has too many items")
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryDependencyAuditError(f"{path} has a non-string key")
        count += _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=next_ancestors,
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryDependencyAuditError("JSON document has too many items")
    return count


def _compact_bytes(value: object, *, limit: int = MAX_AUDIT_BYTES) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive integer")
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
        raise LibraryDependencyAuditError(f"value is not canonical JSON: {exc}") from None
    if len(raw) > limit:
        raise LibraryDependencyAuditError(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_AUDIT_BYTES
) -> bytes:
    """Encode one exact retained document with sorted keys and one final LF."""

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
        raise LibraryDependencyAuditError(f"value is not canonical JSON: {exc}") from None
    if type(limit) is not int or limit < 1:
        raise TypeError("canonical document limit must be a positive integer")
    if len(raw) > limit:
        raise LibraryDependencyAuditError(
            f"canonical document exceeds the {limit}-byte limit"
        )
    return raw


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_AUDIT_BYTES) -> str:
    return _sha256_bytes(_compact_bytes(value, limit=limit))


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryDependencyAuditError(f"{label} must be a lowercase SHA-256")
    return value


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if type(raw) is not bytes or len(raw) > limit:
        raise LibraryDependencyAuditError(f"{label} exceeds its byte limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise LibraryDependencyAuditError(f"{label} is not strict JSON: {exc}") from None
    if type(value) is not dict:
        raise LibraryDependencyAuditError(f"{label} must be one JSON object")
    _validate_json(value)
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryDependencyAuditError(f"{label} is not canonical document JSON")
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
                raise LibraryDependencyAuditError(
                    f"{label} parent contains a link or non-directory component"
                )
    except LibraryDependencyAuditError:
        raise
    except OSError as exc:
        raise LibraryDependencyAuditError(
            f"cannot inspect {label} parent"
        ) from exc
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryDependencyAuditError(f"cannot open {label}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            raise LibraryDependencyAuditError(
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
                raise LibraryDependencyAuditError(f"{label} exceeds its byte limit")
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ) != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        ):
            raise LibraryDependencyAuditError(f"{label} changed while being read")
        return b"".join(chunks)
    except OSError as exc:
        raise LibraryDependencyAuditError(f"cannot read {label}") from exc
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
        raise LibraryDependencyAuditError("cannot resolve repository_root") from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise LibraryDependencyAuditError("repository_root must be a non-symlink directory")
    return resolved


def dependency_audit_schema() -> dict[str, object]:
    """Load and validate the binding A2.1 schema artifact."""

    raw = _safe_file(
        DEPENDENCY_AUDIT_SCHEMA_PATH,
        label="dependency-audit schema",
        limit=MAX_SCHEMA_BYTES,
    )
    value = _decode_document(raw, "dependency-audit schema", limit=MAX_SCHEMA_BYTES)
    semantic = _sha256_json(value, limit=MAX_SCHEMA_BYTES)
    if semantic != DEPENDENCY_AUDIT_SCHEMA_SHA256:
        raise LibraryDependencyAuditError("dependency-audit schema semantic digest drifted")
    if (
        value.get("format") != DEPENDENCY_AUDIT_SCHEMA_FORMAT
        or value.get("id") != DEPENDENCY_AUDIT_SCHEMA_ID
        or value.get("v") != DEPENDENCY_AUDIT_SCHEMA_VERSION
    ):
        raise LibraryDependencyAuditError("dependency-audit schema identity drifted")
    expected_compiler = {
        "callable": COMPILER_CALLABLE,
        "source_count": COMPILER_SOURCE_COUNT,
        "source_root_sha256": COMPILER_SOURCE_ROOT_SHA256,
        "v": COMPILER_VERSION,
    }
    if value.get("fixed_inputs", {}).get("dependency_compiler") != expected_compiler:
        raise LibraryDependencyAuditError(
            "dependency-audit schema compiler identity drifted"
        )
    return deepcopy(value)


def dependency_audit_schema_identity() -> dict[str, object]:
    """Return the exact schema transport and semantic identities."""

    schema = dependency_audit_schema()
    raw = canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "format": DEPENDENCY_AUDIT_SCHEMA_FORMAT,
        "id": DEPENDENCY_AUDIT_SCHEMA_ID,
        "sha256": DEPENDENCY_AUDIT_SCHEMA_SHA256,
        "v": DEPENDENCY_AUDIT_SCHEMA_VERSION,
    }


def _compiler_identity(root: Path) -> dict[str, object]:
    if len(_COMPILER_SOURCES) != COMPILER_SOURCE_COUNT:
        raise LibraryDependencyAuditError("compiler source count drifted")
    sources: list[dict[str, object]] = []
    for relative, digest in _COMPILER_SOURCES:
        raw = _safe_file(
            root / relative,
            label=f"compiler source {relative!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryDependencyAuditError(f"compiler source {relative!r} drifted")
        sources.append({"path": relative, "sha256": digest})
    source_root = _sha256_json(
        {
            "format": "peano-hydra-library-dependency-compiler-source-root-preimage",
            "sources": sources,
            "v": 1,
        }
    )
    if source_root != COMPILER_SOURCE_ROOT_SHA256:
        raise LibraryDependencyAuditError("compiler source root drifted")
    return {
        "callable": COMPILER_CALLABLE,
        "source_root_sha256": source_root,
        "sources": sources,
        "v": COMPILER_VERSION,
    }


def _require_module_origin(module_name: str, expected: Path) -> object:
    module = importlib.import_module(module_name)
    source = getattr(module, "__file__", None)
    if type(source) is not str:
        raise LibraryDependencyAuditError(f"cannot identify module {module_name!r}")
    try:
        actual = Path(source).resolve(strict=True)
        wanted = expected.resolve(strict=True)
    except OSError as exc:
        raise LibraryDependencyAuditError(
            f"cannot resolve module {module_name!r}"
        ) from exc
    if actual != wanted:
        raise LibraryDependencyAuditError(f"module {module_name!r} origin drifted")
    return module


def _repository_identity() -> dict[str, object]:
    return {
        "commit": REPOSITORY_COMMIT,
        "source": "retained-replay-pack-snapshot",
        "tree": REPOSITORY_TREE,
        "url": REPOSITORY_URL,
    }


def _documentation_identity() -> dict[str, object]:
    return {
        "artifact_path": _BUNDLE_RELATIVE.as_posix(),
        "explicit_artifact_sha256": BUNDLE_EXPLICIT_ARTIFACT_SHA256,
        "explicit_ordered_record_root_sha256": (
            BUNDLE_EXPLICIT_ORDERED_RECORD_ROOT_SHA256
        ),
        "explicit_root_sha256": BUNDLE_EXPLICIT_ROOT_SHA256,
        "manifest_artifact_sha256": BUNDLE_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": BUNDLE_MANIFEST_ROOT_SHA256,
        "schema_artifact_sha256": BUNDLE_SCHEMA_ARTIFACT_SHA256,
        "schema_semantic_sha256": BUNDLE_SCHEMA_SEMANTIC_SHA256,
    }


def _replay_identity() -> dict[str, object]:
    return {
        "catalog_artifact_sha256": REPLAY_CATALOG_ARTIFACT_SHA256,
        "catalog_ordered_root_sha256": REPLAY_CATALOG_ORDERED_ROOT_SHA256,
        "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
        "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
        "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
    }


def _predecessor_identity() -> dict[str, object]:
    return {
        "artifact_path": _PREDECESSOR_RELATIVE.as_posix(),
        "artifact_sha256": PREDECESSOR_ARTIFACT_SHA256,
        "root_sha256": PREDECESSOR_ROOT_SHA256,
        "theorem_record_root_sha256": PREDECESSOR_THEOREM_RECORD_ROOT_SHA256,
    }


def _load_inputs(
    root: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], Mapping[str, TheoremSpec], dict[str, object]]:
    compiler = _compiler_identity(root)
    candidate_module = _require_module_origin(
        "peano_lab.library.candidate_validation",
        root / "peano-lab/py/peano_lab/library/candidate_validation.py",
    )
    theorem_module = _require_module_origin(
        "peano_lab.library.theorems",
        root / "peano-lab/py/peano_lab/library/theorems.py",
    )
    if (
        getattr(candidate_module, "compile_candidate_body", None)
        is not compile_candidate_body
        or getattr(candidate_module, "CandidateBodyCompilation", None)
        is not CandidateBodyCompilation
        or getattr(candidate_module, "CandidateBodyError", None)
        is not CandidateBodyError
        or getattr(theorem_module, "THEOREMS", None) is not THEOREMS
        or getattr(theorem_module, "TheoremSpec", None) is not TheoremSpec
    ):
        raise LibraryDependencyAuditError("compiler callable identity drifted")
    tactics_module = _require_module_origin(
        "peano_lab.engine.tactics",
        root / "peano-lab/py/peano_lab/engine/tactics.py",
    )
    reduction_module = _require_module_origin(
        "peano_lab.engine.proof_reduction",
        root / "peano-lab/py/peano_lab/engine/proof_reduction.py",
    )
    codec_module = _require_module_origin(
        "peano_lab.kernel.artifact_codec",
        root / "peano-lab/py/peano_lab/kernel/artifact_codec.py",
    )
    checker_module = _require_module_origin(
        "peano_lab.kernel.checker",
        root / "peano-lab/py/peano_lab/kernel/checker.py",
    )
    if (
        getattr(tactics_module, "InvalidProof", None) is not InvalidProof
        or getattr(tactics_module, "TacticError", None) is not TacticError
        or getattr(tactics_module, "TacticLimit", None) is not TacticLimit
        or getattr(reduction_module, "ProofReductionError", None)
        is not ProofReductionError
        or getattr(codec_module, "encode_formula", None) is not encode_formula
        or getattr(codec_module, "encode_proof", None) is not encode_proof
        or getattr(checker_module, "check", None) is not check
    ):
        raise LibraryDependencyAuditError("compiler runtime callable identity drifted")

    bundle_module = _require_module_origin(
        "training.peano_hydra.library_documentation_bundle",
        root / "training/peano_hydra/library_documentation_bundle.py",
    )
    try:
        bundle = bundle_module.load_documentation_bundle(
            root / _BUNDLE_RELATIVE, repository_root=root
        )
    except bundle_module.LibraryDocumentationBundleError as exc:
        raise LibraryDependencyAuditError(
            f"selected documentation bundle is invalid: {exc}"
        ) from None
    pinned_bundle_members = (
        ("schema.json", BUNDLE_SCHEMA_ARTIFACT_SHA256, MAX_SCHEMA_BYTES),
        ("explicit.json", BUNDLE_EXPLICIT_ARTIFACT_SHA256, 16_000_000),
        ("manifest.json", BUNDLE_MANIFEST_ARTIFACT_SHA256, 1_000_000),
    )
    for filename, digest, limit in pinned_bundle_members:
        raw = _safe_file(
            root / _BUNDLE_RELATIVE / filename,
            label=f"selected documentation {filename!r}",
            limit=limit,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryDependencyAuditError(
                f"selected documentation {filename!r} bytes drifted"
            )
        decoded = _decode_document(
            raw,
            f"selected documentation {filename!r}",
            limit=limit,
        )
        if bundle.get(filename) != decoded:
            raise LibraryDependencyAuditError(
                f"selected documentation {filename!r} loader join drifted"
            )
    explicit = bundle.get("explicit.json")
    bundle_manifest = bundle.get("manifest.json")
    bundle_schema = bundle.get("schema.json")
    if (
        type(explicit) is not dict
        or type(bundle_manifest) is not dict
        or type(bundle_schema) is not dict
        or explicit.get("root_sha256") != BUNDLE_EXPLICIT_ROOT_SHA256
        or explicit.get("theorem_count") != THEOREM_COUNT
        or explicit.get("dependency_receipt", {}).get(
            "ordered_record_root_sha256"
        )
        != BUNDLE_EXPLICIT_ORDERED_RECORD_ROOT_SHA256
        or bundle_manifest.get("root_sha256") != BUNDLE_MANIFEST_ROOT_SHA256
        or _sha256_json(bundle_schema, limit=MAX_SCHEMA_BYTES)
        != BUNDLE_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryDependencyAuditError("selected documentation identities drifted")

    replay_raw = _safe_file(
        root / _REPLAY_MANIFEST_RELATIVE,
        label="retained replay manifest",
        limit=8_000_000,
    )
    if _sha256_bytes(replay_raw) != REPLAY_MANIFEST_ARTIFACT_SHA256:
        raise LibraryDependencyAuditError("retained replay manifest bytes drifted")
    replay_manifest = _decode_document(
        replay_raw, "retained replay manifest", limit=8_000_000
    )
    if (
        replay_manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or replay_manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or replay_manifest.get("theorem_count") != THEOREM_COUNT
        or replay_manifest.get("source_catalog", {}).get("artifact_sha256")
        != REPLAY_CATALOG_ARTIFACT_SHA256
        or replay_manifest.get("source_catalog", {}).get("ordered_root_sha256")
        != REPLAY_CATALOG_ORDERED_ROOT_SHA256
    ):
        raise LibraryDependencyAuditError("retained replay manifest identity drifted")

    report_raw = _safe_file(
        root / _REPLAY_REPORT_RELATIVE,
        label="retained replay report",
        limit=1_000_000,
    )
    if _sha256_bytes(report_raw) != REPLAY_REPORT_ARTIFACT_SHA256:
        raise LibraryDependencyAuditError("retained replay report bytes drifted")
    report = _decode_document(report_raw, "retained replay report", limit=1_000_000)
    if report != {
        "artifact_bytes_total": replay_manifest["aggregate"]["artifact_bytes_total"],
        "format": "peano-hydra-library-replay-verification",
        "kernel_checked_count": THEOREM_COUNT,
        "logic_mode": LOGIC_MODE,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
        "status": "passed",
        "theorem_count": THEOREM_COUNT,
        "v": 1,
        "worker_isolation": {
            "forbidden_import_prefixes": [
                "peano_lab.library",
                "peano_lab.engine",
                "peano_lab.ui",
                "training",
                "torch",
                "transformers",
            ],
            "forbidden_modules_loaded": [],
            "format": "peano-hydra-replay-worker-isolation",
            "fresh_repo_pycache": True,
            "guard": "meta-path-reject",
            "python_isolated_mode": True,
            "python_no_site": True,
            "v": 1,
        },
    }:
        raise LibraryDependencyAuditError("retained replay report identity drifted")

    predecessor_raw = _safe_file(
        root / _PREDECESSOR_RELATIVE,
        label="predecessor metadata v2",
        limit=16_000_000,
    )
    if _sha256_bytes(predecessor_raw) != PREDECESSOR_ARTIFACT_SHA256:
        raise LibraryDependencyAuditError("predecessor metadata bytes drifted")
    predecessor = _decode_document(
        predecessor_raw, "predecessor metadata v2", limit=16_000_000
    )
    if (
        predecessor.get("root_sha256") != PREDECESSOR_ROOT_SHA256
        or predecessor.get("theorem_count") != THEOREM_COUNT
        or predecessor.get("theorem_records", {}).get("root_sha256")
        != PREDECESSOR_THEOREM_RECORD_ROOT_SHA256
        or predecessor.get("status") != STATUS
        or any(
            predecessor.get(field) is not False
            for field in (
                "evaluation_eligible",
                "freeze_ready",
                "retrieval_eligible",
                "training_eligible",
            )
        )
    ):
        raise LibraryDependencyAuditError("predecessor metadata identity drifted")

    explicit_rows = explicit.get("theorems")
    replay_rows = replay_manifest.get("theorems")
    if (
        type(explicit_rows) is not list
        or type(replay_rows) is not list
        or len(explicit_rows) != THEOREM_COUNT
        or len(replay_rows) != THEOREM_COUNT
        or len(THEOREMS) != THEOREM_COUNT
    ):
        raise LibraryDependencyAuditError("selected theorem count drifted")
    table: dict[str, TheoremSpec] = {}
    edge_count = 0
    for index, (spec, explicit_row, replay_row) in enumerate(
        zip(THEOREMS, explicit_rows, replay_rows, strict=True)
    ):
        if type(spec) is not TheoremSpec or type(explicit_row) is not dict or type(replay_row) is not dict:
            raise LibraryDependencyAuditError("selected theorem row type drifted")
        script = tuple(line["text"] for line in explicit_row["command_lines"])
        if (
            explicit_row.get("index") != index
            or replay_row.get("index") != index
            or spec.name != explicit_row.get("name")
            or spec.name != replay_row.get("name")
            or spec.statement != explicit_row.get("statement_source")
            or spec.statement != replay_row.get("statement_source")
            or list(spec.dependencies) != explicit_row.get("declared_dependencies")
            or list(spec.dependencies) != replay_row.get("declared_dependencies")
            or spec.script != script
            or list(spec.script) != replay_row.get("script")
            or spec.summary != explicit_row.get("summary")
            or spec.summary != replay_row.get("summary")
            or explicit_row.get("formula_sha256") != replay_row.get("formula_sha256")
            or explicit_row.get("script_sha256") != replay_row.get("script_sha256")
        ):
            raise LibraryDependencyAuditError(
                f"selected theorem join drifted at index {index}"
            )
        if spec.name in table:
            raise LibraryDependencyAuditError("selected theorem names are duplicated")
        if len(spec.dependencies) > MAX_DEPENDENCIES_PER_THEOREM:
            raise LibraryDependencyAuditError(
                f"theorem {spec.name!r} exceeds the dependency limit"
            )
        if len(set(spec.dependencies)) != len(spec.dependencies):
            raise LibraryDependencyAuditError(
                f"theorem {spec.name!r} has duplicate dependencies"
            )
        if any(dependency not in table for dependency in spec.dependencies):
            raise LibraryDependencyAuditError(
                f"theorem {spec.name!r} has a non-prior dependency"
            )
        table[spec.name] = spec
        edge_count += len(spec.dependencies)
    if edge_count != DECLARED_DEPENDENCY_EDGES:
        raise LibraryDependencyAuditError("selected dependency edge count drifted")
    return explicit_rows, replay_rows, table, {
        "compiler": compiler,
        "documentation_bundle": _documentation_identity(),
        "predecessor_metadata": _predecessor_identity(),
        "replay_pack": _replay_identity(),
        "repository": _repository_identity(),
    }


def _body_receipt(compilation: CandidateBodyCompilation) -> dict[str, object]:
    if type(compilation) is not CandidateBodyCompilation:
        raise LibraryDependencyAuditError("body compiler returned a foreign carrier")
    if not check((), compilation.certificate, compilation.target):
        raise LibraryDependencyAuditError(
            "independent kernel rejected a dependency-curried body"
        )
    metrics = compilation.receipt
    receipt: dict[str, object] = {
        "certificate_representation": "peano-lab-v2-encoded-proof",
        "certificate_sha256": _sha256_bytes(encode_proof(compilation.certificate)),
        "dependency_count": metrics.dependency_count,
        "kernel_accepted": True,
        "metrics": {
            "proof_depth": metrics.proof_depth,
            "proof_edges": metrics.proof_edges,
            "proof_nodes": metrics.proof_nodes,
            "proof_objects": metrics.proof_objects,
            "reused_objects": metrics.reused_objects,
        },
        "target_formula_sha256": _sha256_bytes(encode_formula(compilation.target)),
    }
    receipt["receipt_sha256"] = _sha256_json(receipt)
    return receipt


def _deterministic_failure(error: CandidateBodyError) -> dict[str, object]:
    kind = getattr(error, "kind", None)
    phase = getattr(error, "phase", None)
    if kind == "resource-limit":
        raise LibraryDependencyAuditError(
            "leave-one-out replay reached a resource limit; result is unknown"
        ) from error
    if kind != "exact-recipe-rejection" or phase not in (
        "command",
        "finalization",
    ):
        raise LibraryDependencyAuditError(
            "leave-one-out replay failed internally; result is unknown"
        ) from error
    cause = error.__cause__
    expected_cause = (
        phase == "command"
        and isinstance(cause, TacticError)
        and not isinstance(cause, TacticLimit)
    ) or (
        phase == "finalization"
        and (
            cause is None
            or isinstance(cause, (InvalidProof, ProofReductionError))
        )
    )
    if not expected_cause:
        raise LibraryDependencyAuditError(
            "leave-one-out rejection classification is malformed; result is unknown"
        ) from error
    command_index = getattr(error, "command_index", None)
    command = getattr(error, "command", None)
    if phase == "command" and (
        type(command_index) is not int
        or command_index < 0
        or type(command) is not str
    ):
        raise LibraryDependencyAuditError("candidate-body failure metadata is malformed")
    if phase == "finalization" and (
        command_index is not None or command is not None
    ):
        raise LibraryDependencyAuditError("candidate-body failure metadata is malformed")
    return {
        "command_index": command_index,
        "command_sha256": (
            _sha256_bytes(command.encode("utf-8")) if type(command) is str else None
        ),
        "kind": "exact-recipe-rejection",
        "message_sha256": _sha256_bytes(str(error).encode("utf-8")),
        "phase": phase,
    }


def _algorithm_identity() -> dict[str, object]:
    return {
        "direction": "reverse-declaration-order",
        "fixed_point": "complete-pass-until-no-removal",
        "id": ALGORITHM_ID,
        "unknown_policy": "block-document",
        "v": 1,
    }


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _audit_spec(
    spec: TheoremSpec,
    *,
    core: Mapping[str, TheoremSpec],
) -> dict[str, object]:
    """Audit one exact recipe; retained only through the fixed 384-row builder."""

    if type(spec) is not TheoremSpec:
        raise LibraryDependencyAuditError("audit needs an exact TheoremSpec")
    if len(spec.dependencies) > MAX_DEPENDENCIES_PER_THEOREM:
        raise LibraryDependencyAuditError("theorem exceeds the dependency limit")
    try:
        positive = _body_receipt(compile_candidate_body(spec, core=core))
    except CandidateBodyError as exc:
        if getattr(exc, "kind", None) == "resource-limit":
            raise LibraryDependencyAuditError(
                f"original recipe for {spec.name!r} reached a resource limit; "
                "result is unknown"
            ) from exc
        if getattr(exc, "kind", None) != "exact-recipe-rejection":
            raise LibraryDependencyAuditError(
                f"original recipe for {spec.name!r} failed internally; "
                "result is unknown"
            ) from exc
        raise LibraryDependencyAuditError(
            f"original recipe for {spec.name!r} did not compile"
        ) from exc

    working = list(spec.dependencies)
    attempts: list[dict[str, object]] = []
    pass_index = 0
    while True:
        if pass_index >= MAX_PASSES_PER_THEOREM:
            raise LibraryDependencyAuditError("dependency audit exceeded its pass limit")
        removed = False
        for dependency in reversed(tuple(working)):
            before = list(working)
            candidate = list(working)
            candidate.remove(dependency)
            altered = replace(spec, dependencies=tuple(candidate))
            failure: dict[str, object] | None = None
            reduced_receipt: dict[str, object] | None = None
            try:
                reduced_receipt = _body_receipt(
                    compile_candidate_body(altered, core=core)
                )
            except CandidateBodyError as exc:
                failure = _deterministic_failure(exc)
            if reduced_receipt is not None:
                working = candidate
                removed = True
                outcome = "kernel-accepted"
                after = list(working)
            else:
                outcome = "exact-recipe-rejected"
                after = before
            attempt: dict[str, object] = {
                "after_dependencies": after,
                "attempt_index": len(attempts),
                "before_dependencies": before,
                "failure": failure,
                "omitted_dependency": dependency,
                "outcome": outcome,
                "pass_index": pass_index,
                "positive_receipt": reduced_receipt,
            }
            attempt["record_sha256"] = _record_hash(attempt)
            attempts.append(attempt)
            if len(attempts) > MAX_ATTEMPTS:
                raise LibraryDependencyAuditError(
                    "dependency audit exceeded its attempt limit"
                )
        pass_index += 1
        if not removed:
            break

    attempt_identities = [
        {
            "attempt_index": attempt["attempt_index"],
            "record_sha256": attempt["record_sha256"],
        }
        for attempt in attempts
    ]
    attempt_preimage = {
        "format": ATTEMPT_RECORDS_PREIMAGE_FORMAT,
        "records": attempt_identities,
        "v": 1,
    }
    attempt_records = {
        "count": len(attempts),
        "preimage": attempt_preimage,
        "root_sha256": _sha256_json(attempt_preimage),
    }
    receipt_preimage = {
        "algorithm": _algorithm_identity(),
        "attempt_root_sha256": attempt_records["root_sha256"],
        "candidate_dependencies": list(working),
        "format": RECIPE_AUDIT_PREIMAGE_FORMAT,
        "initial_dependencies": list(spec.dependencies),
        "positive_receipt_sha256": positive["receipt_sha256"],
        "v": 1,
    }
    return {
        "algorithm": _algorithm_identity(),
        "attempt_records": attempt_records,
        "attempts": attempts,
        "candidate_dependencies": list(working),
        "complete": True,
        "initial_dependencies": list(spec.dependencies),
        "positive_receipt": positive,
        "receipt_preimage": receipt_preimage,
        "receipt_sha256": _sha256_json(receipt_preimage),
    }


def _route_receipt(
    recipe_audit: Mapping[str, object], *, route: str
) -> dict[str, object]:
    dependencies = deepcopy(recipe_audit["candidate_dependencies"])
    preimage = {
        "dependencies": dependencies,
        "format": ROUTE_RECEIPT_PREIMAGE_FORMAT,
        "recipe_audit_sha256": recipe_audit["receipt_sha256"],
        "route": route,
        "v": 1,
    }
    return {
        "dependencies": dependencies,
        "preimage": preimage,
        "route": route,
        "sha256": _sha256_json(preimage),
        "status": "fixed-point-exact-recipe-observation",
    }


def _theorem_row(
    index: int,
    spec: TheoremSpec,
    explicit: Mapping[str, object],
    replay: Mapping[str, object],
    recipe_audit: dict[str, object],
) -> dict[str, object]:
    candidate_dependencies = list(recipe_audit["candidate_dependencies"])
    rebuild = candidate_dependencies != list(spec.dependencies)
    readable_receipt = _route_receipt(recipe_audit, route="readable-proof")
    construction_receipt = _route_receipt(
        recipe_audit, route="submitted-construction-candidate"
    )
    union = list(
        dict.fromkeys(
            (*readable_receipt["dependencies"], *construction_receipt["dependencies"])
        )
    )
    row: dict[str, object] = {
        "candidate_publication_union": union,
        "declared_dependencies": list(spec.dependencies),
        "explicit_record_sha256": explicit["record_sha256"],
        "index": index,
        "minimality_claim": False,
        "name": spec.name,
        "optimized_best_known": False,
        "readable": {
            "dependencies": list(readable_receipt["dependencies"]),
            "leave_one_out": readable_receipt,
            "proof": deepcopy(recipe_audit["positive_receipt"]),
            "status": "candidate-fixed-point-exact-recipe",
        },
        "recipe_audit": recipe_audit,
        "replay_artifact_sha256": replay["artifact"]["sha256"],
        "requires_certificate_rebuild": rebuild,
        "script": {
            "command_count": len(spec.script),
            "script_sha256": replay["script_sha256"],
        },
        "statement": {
            "formula_sha256": replay["formula_sha256"],
            "source_sha256": replay["statement_source_sha256"],
        },
        "submitted_construction": {
            "best_known": False,
            "candidate_dependencies": list(construction_receipt["dependencies"]),
            "current_certificate": {
                "artifact_sha256": replay["artifact"]["sha256"],
                "proof_term_sha256": replay["proof_term_sha256"],
                "replay_status": "kernel-accepted-retained-report",
            },
            "current_dependencies": list(spec.dependencies),
            "leave_one_out": construction_receipt,
            "recipe_relation": "same-theorem-spec-as-readable",
            "requires_certificate_rebuild": rebuild,
            "status": "submitted-not-best-known",
        },
    }
    row["record_sha256"] = _record_hash(row)
    return row


def _build_candidate_dependency_audit(root: Path) -> dict[str, object]:
    explicit_rows, replay_rows, table, inputs = _load_inputs(root)
    theorem_rows: list[dict[str, object]] = []
    accepted = 0
    rejected = 0
    candidate_edges = 0
    rebuilds = 0
    for index, (spec, explicit, replay) in enumerate(
        zip(THEOREMS, explicit_rows, replay_rows, strict=True)
    ):
        recipe = _audit_spec(spec, core=table)
        row = _theorem_row(index, spec, explicit, replay, recipe)
        theorem_rows.append(row)
        accepted += sum(
            attempt["outcome"] == "kernel-accepted"
            for attempt in recipe["attempts"]
        )
        rejected += sum(
            attempt["outcome"] == "exact-recipe-rejected"
            for attempt in recipe["attempts"]
        )
        candidate_edges += len(row["candidate_publication_union"])
        rebuilds += row["requires_certificate_rebuild"] is True

    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
        for row in theorem_rows
    ]
    record_preimage = {
        "format": THEOREM_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": 1,
    }
    theorem_records = {
        "count": THEOREM_COUNT,
        "preimage": record_preimage,
        "root_sha256": _sha256_json(record_preimage),
    }
    body = {
        "aggregate": {
            "accepted_omission_observations": accepted,
            "candidate_dependency_edges": candidate_edges,
            "declared_dependency_edges": DECLARED_DEPENDENCY_EDGES,
            "exact_recipe_rejection_observations": rejected,
            "requires_certificate_rebuild_count": rebuilds,
            "theorem_count": THEOREM_COUNT,
            "unknown_observations": 0,
        },
        "evaluation_eligible": False,
        "format": DEPENDENCY_AUDIT_FORMAT,
        "freeze_ready": False,
        "id": DEPENDENCY_AUDIT_ID,
        "inputs": inputs,
        "logic_mode": LOGIC_MODE,
        "minimality_claim": False,
        "optimized_best_known": False,
        "publication_ready": False,
        "retrieval_eligible": False,
        "schema": dependency_audit_schema_identity(),
        "status": STATUS,
        "theorem_count": THEOREM_COUNT,
        "theorem_records": theorem_records,
        "training_eligible": False,
        "v": DEPENDENCY_AUDIT_VERSION,
    }
    payload = {
        "body": body,
        "theorem_record_root_sha256": theorem_records["root_sha256"],
    }
    root_preimage = {
        "format": DEPENDENCY_AUDIT_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": DEPENDENCY_AUDIT_VERSION,
    }
    return {
        **body,
        "root_preimage": root_preimage,
        "root_sha256": _sha256_json(root_preimage),
        "theorems": theorem_rows,
    }


def build_candidate_dependency_audit(
    *, repository_root: Path | None = None
) -> dict[str, object]:
    """Build the exact candidate audit afresh from fixed selected inputs."""

    dependency_audit_schema()
    root = _repository_root(repository_root)
    result = _build_candidate_dependency_audit(root)
    canonical_document_bytes(result)
    return deepcopy(result)


def validate_dependency_audit(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate one audit by exact reconstruction from fixed source inputs."""

    dependency_audit_schema()
    if type(value) is not dict:
        raise LibraryDependencyAuditError("dependency audit must be one object")
    _validate_json(value)
    root = _repository_root(repository_root)
    expected = _build_candidate_dependency_audit(root)
    if value != expected:
        raise LibraryDependencyAuditError(
            "dependency audit differs from exact fixed-source reconstruction"
        )
    return _decode_document(
        canonical_document_bytes(expected),
        "validated dependency audit",
        limit=MAX_AUDIT_BYTES,
    )


def load_dependency_audit(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one bounded canonical file and fully reconstruct its evidence."""

    raw = _safe_file(path, label="dependency audit", limit=MAX_AUDIT_BYTES)
    value = _decode_document(raw, "dependency audit", limit=MAX_AUDIT_BYTES)
    return validate_dependency_audit(value, repository_root=repository_root)


__all__ = [
    "DEPENDENCY_AUDIT_SCHEMA_FORMAT",
    "DEPENDENCY_AUDIT_SCHEMA_ID",
    "DEPENDENCY_AUDIT_SCHEMA_PATH",
    "DEPENDENCY_AUDIT_SCHEMA_SHA256",
    "DEPENDENCY_AUDIT_SCHEMA_VERSION",
    "LibraryDependencyAuditError",
    "build_candidate_dependency_audit",
    "canonical_document_bytes",
    "dependency_audit_schema",
    "dependency_audit_schema_identity",
    "load_dependency_audit",
    "validate_dependency_audit",
]
