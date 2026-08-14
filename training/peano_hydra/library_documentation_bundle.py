"""Deterministic H1.1b documentation for one retained replay-pack selection.

The documents built here are a candidate reading surface, never proof
authority.  Selection comes only from the exact retained replay manifest.  A
fresh zip against source-hash-verified :class:`TheoremSpec` values from that
pinned snapshot prevents accidental substitution, and every conservative
defined-syntax compaction is checked by the pinned exact-AST compactor before
it is serialized.
"""

from __future__ import annotations

import ast
from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping
import warnings

SCHEMA_FORMAT = "peano-hydra-library-documentation-bundle-schema"
SCHEMA_VERSION = 1
SCHEMA_ID = "peano-hydra-library-documentation-bundle-v1"
SCHEMA_PATH = Path(__file__).with_name(
    "library-documentation-bundle-schema-v1.json"
)
# Patched after the closed schema is finalized.  This is the semantic digest
# of compact canonical JSON; the schema identity also exposes the exact-file
# digest of the retained two-space document.
SCHEMA_SHA256 = "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d"

EXPLICIT_FORMAT = "peano-hydra-library-documentation-explicit"
DEFINED_FORMAT = "peano-hydra-library-documentation-defined"
ISOLATION_FORMAT = "peano-hydra-library-documentation-isolation-receipt"
MANIFEST_FORMAT = "peano-hydra-library-documentation-manifest"
EXPLICIT_ID = "authoring-l0-documentation-explicit-candidate-v1"
DEFINED_ID = "authoring-l0-documentation-defined-candidate-v1"
ISOLATION_ID = "authoring-l0-documentation-isolation-candidate-v1"
MANIFEST_ID = "authoring-l0-documentation-candidate-v1"

STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
SOURCE_COMMIT = "32803924d7def862ccf0b738cd1ed494a3165f7e"
SOURCE_TREE = "e945e4963ad53b1c07008fd8356980bdacc3bafe"
REPOSITORY_URL = "https://github.com/nasqret/vietnam2026"

REPLAY_MANIFEST_ARTIFACT_SHA256 = (
    "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
)
REPLAY_MANIFEST_ROOT_SHA256 = (
    "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
)
REPLAY_ROOT_SHA256 = (
    "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
)
CATALOG_ARTIFACT_SHA256 = (
    "326ffe660da6e34a3aa12e0aa13096078a0bf20c45c440049aaf5d5bed1f1be7"
)
CATALOG_SEMANTIC_SHA256 = (
    "f5c7318229ea76b372d7f09250241ba7bb98b3829a8853e85ad2d8528b710a51"
)
CATALOG_ORDERED_ROOT_SHA256 = (
    "73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b"
)
CATALOG_SOURCE_ROOT_SHA256 = (
    "6fefaa2bdc92e477ce20444122ea1c752420e7efc1706a664777cb887128a3be"
)
DEFINED_SYNTAX_SOURCE_SHA256 = (
    "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903"
)
DEFINED_COMPACTOR_SOURCE_SHA256 = (
    "0e08246b93743f9efb8ad8c054a1e4361914570c6d3f56ed62092992a5551f55"
)
FORMULAS_SOURCE_SHA256 = (
    "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"
)
TERMS_SOURCE_SHA256 = (
    "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"
)

SCHEMA_FILE = "schema.json"
EXPLICIT_FILE = "explicit.json"
DEFINED_FILE = "defined.json"
ISOLATION_FILE = "isolation-receipt.json"
MANIFEST_FILE = "manifest.json"
DOCUMENT_FILES = (
    SCHEMA_FILE,
    EXPLICIT_FILE,
    DEFINED_FILE,
    ISOLATION_FILE,
    MANIFEST_FILE,
)
MANIFEST_MEMBER_FILES = DOCUMENT_FILES[:-1]

MAX_SCHEMA_BYTES = 1_000_000
MAX_EXPLICIT_BYTES = 8_000_000
MAX_DEFINED_BYTES = 16_000_000
MAX_ISOLATION_BYTES = 1_000_000
MAX_MANIFEST_BYTES = 1_000_000
MAX_REPLAY_MANIFEST_BYTES = 8_000_000
MAX_REPLAY_CATALOG_BYTES = 4_000_000
MAX_SOURCE_FILE_BYTES = 8_000_000
MAX_DOCUMENT_BYTES = MAX_DEFINED_BYTES
MAX_JSON_DEPTH = 192
MAX_JSON_ITEMS = 3_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

EXPECTED = {
    "changed_local_propositions": 624,
    "changed_statements": 321,
    "declared_dependency_edges": 1038,
    "defined_local_characters": 25733,
    "defined_statement_characters": 29098,
    "definition_count": 40,
    "definition_occurrences": 2027,
    "dependency_depth_maximum": 21,
    "dependency_level_count": 22,
    "expanded_local_characters": 148105,
    "expanded_statement_characters": 224948,
    "explicitly_referenced_dependency_edges": 1035,
    "foundation_count": 55,
    "implicit_dependency_edges": 3,
    "local_proposition_count": 950,
    "reference_occurrences": 3989,
    "tactic_head_count": 20,
    "tactic_line_count": 13862,
    "tactic_text_characters": 399210,
    "terminal_count": 100,
    "theorem_count": 384,
}

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_DIRECTORY = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
_REPLAY_MANIFEST_PATH = _REPLAY_DIRECTORY / MANIFEST_FILE
_REPLAY_CATALOG_PATH = _REPLAY_DIRECTORY / "catalog.json"
_DEFINED_SYNTAX_PATH = Path("peano-lab/py/peano_lab/library/defined_syntax.py")
_DEFINED_COMPACTOR_PATH = Path("peano-lab/py/peano_lab/library/defined_edition.py")
_FORMULAS_PATH = Path("peano-lab/py/peano_lab/kernel/formulas.py")
_TERMS_PATH = Path("peano-lab/py/peano_lab/kernel/terms.py")

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_THEOREM_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,127}")
_IDENTIFIER_RE = r"[A-Za-z_][A-Za-z0-9_']*"
_PA_AXIOMS = {f"PA{number}" for number in range(1, 7)}
_THEOREM_SPEC_FIELDS = (
    "name",
    "statement",
    "dependencies",
    "script",
    "summary",
)
_DISALLOWED_THEOREM_FIELDS = frozenset(
    {"closure", "dependents", "href", "scope", "tag"}
)

# qr_small_moduli.py uses five finite factories.  These are the complete,
# reviewed output-name sets for the pinned source bytes; no open-ended string
# interpolation is accepted as a locator.
_GENERATED_SMALL_MODULI = {
    "lt__cases": ("lt_five_cases", "lt_seven_cases"),
    "bounded_square_mod_classify": (
        "bounded_square_mod3_classify",
        "bounded_square_mod5_classify",
        "bounded_square_mod7_classify",
    ),
    "qres_mod_": (
        "qres_mod3_zero",
        "qres_mod3_one",
        "qres_mod5_zero",
        "qres_mod5_one",
        "qres_mod5_four",
        "qres_mod7_zero",
        "qres_mod7_one",
        "qres_mod7_two",
        "qres_mod7_four",
    ),
    "qres_mod_canonical_iff": (
        "qres_mod3_canonical_iff",
        "qres_mod5_canonical_iff",
        "qres_mod7_canonical_iff",
    ),
    "not_qres_mod_": (
        "not_qres_mod3_two",
        "not_qres_mod5_two",
        "not_qres_mod5_three",
        "not_qres_mod7_three",
        "not_qres_mod7_five",
        "not_qres_mod7_six",
    ),
}


class LibraryDocumentationBundleError(ValueError):
    """The candidate documentation bundle or a pinned input is malformed."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryDocumentationBundleError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise LibraryDocumentationBundleError(f"forbidden JSON constant {value!r}")


def _reject_float(value: str) -> object:
    raise LibraryDocumentationBundleError(
        f"floating-point JSON value {value!r} is forbidden"
    )


def _validate_json_value(
    value: object,
    *,
    depth: int = 0,
    active: set[int] | None = None,
    counter: list[int] | None = None,
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise LibraryDocumentationBundleError("JSON exceeds the nesting limit")
    if active is None:
        active = set()
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_JSON_ITEMS:
        raise LibraryDocumentationBundleError("JSON exceeds the item limit")
    if value is None or type(value) in (bool, str):
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_JSON_INTEGER:
            raise LibraryDocumentationBundleError(
                "JSON integer exceeds the safe domain"
            )
        return
    if type(value) not in (list, dict):
        raise LibraryDocumentationBundleError("value is outside strict JSON")
    identity = id(value)
    if identity in active:
        raise LibraryDocumentationBundleError("cyclic JSON value is forbidden")
    active.add(identity)
    try:
        if type(value) is dict:
            if not all(type(key) is str for key in value):
                raise LibraryDocumentationBundleError(
                    "JSON object keys must be text"
                )
            values = value.values()
        else:
            values = value
        for item in values:
            _validate_json_value(
                item,
                depth=depth + 1,
                active=active,
                counter=counter,
            )
    finally:
        active.remove(identity)


def _canonical_json_bytes(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json_value(value)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryDocumentationBundleError(
            f"value is not canonical JSON: {exc}"
        ) from None
    if len(raw) > limit:
        raise LibraryDocumentationBundleError(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return the unique retained UTF-8 representation of a JSON value."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json_value(value)
    try:
        raw = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryDocumentationBundleError(
            f"value is not canonical JSON: {exc}"
        ) from None
    if len(raw) > limit:
        raise LibraryDocumentationBundleError(
            f"canonical JSON document exceeds the {limit}-byte limit"
        )
    return raw


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256_bytes(_canonical_json_bytes(value, limit=limit))


def _decode_json(raw: bytes, label: str) -> object:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except LibraryDocumentationBundleError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryDocumentationBundleError(
            f"{label} is not strict JSON: {exc}"
        ) from None


def _decode_canonical_document(
    raw: bytes, label: str, *, limit: int
) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryDocumentationBundleError(f"{label} must be bounded exact bytes")
    value = _decode_json(raw, label)
    if type(value) is not dict:
        raise LibraryDocumentationBundleError(f"{label} must be one JSON object")
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryDocumentationBundleError(
            f"{label} is not a canonical JSON document"
        )
    return value


def _detached_object(value: object, label: str) -> dict[str, object]:
    decoded = _decode_json(_canonical_json_bytes(value), label)
    if type(decoded) is not dict:
        raise LibraryDocumentationBundleError(f"{label} must be one JSON object")
    return decoded


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository root must be a pathlib.Path")
    try:
        metadata = root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryDocumentationBundleError(
                "repository root must be a non-symlink directory"
            )
        return root.resolve(strict=True)
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            "cannot resolve repository root"
        ) from exc


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("file limit must be a positive exact integer")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryDocumentationBundleError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size < 1 or before.st_size > limit:
            raise LibraryDocumentationBundleError(
                f"{label} must be a bounded nonempty regular file"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
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
            raise LibraryDocumentationBundleError(f"{label} changed while read")
    except OSError as exc:
        raise LibraryDocumentationBundleError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)
    if len(raw) != before.st_size:
        raise LibraryDocumentationBundleError(f"{label} changed size while read")
    return raw


def documentation_bundle_schema() -> dict[str, object]:
    """Load and verify the closed binding schema shipped beside this module."""

    raw = _read_bounded_regular_file(
        SCHEMA_PATH, label="documentation-bundle schema", limit=MAX_SCHEMA_BYTES
    )
    schema = _decode_canonical_document(
        raw, "documentation-bundle schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        schema.get("format") != SCHEMA_FORMAT
        or schema.get("id") != SCHEMA_ID
        or schema.get("v") != SCHEMA_VERSION
    ):
        raise LibraryDocumentationBundleError(
            "documentation-bundle schema identity drifted"
        )
    if _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != SCHEMA_SHA256:
        raise LibraryDocumentationBundleError(
            "documentation-bundle schema digest drifted"
        )
    return _detached_object(schema, "documentation-bundle schema")


def documentation_bundle_schema_identity() -> dict[str, object]:
    """Return semantic and exact-file identities of the binding schema."""

    schema = documentation_bundle_schema()
    return {
        "artifact_sha256": _sha256_bytes(
            canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
        ),
        "format": SCHEMA_FORMAT,
        "id": SCHEMA_ID,
        "sha256": SCHEMA_SHA256,
        "v": SCHEMA_VERSION,
    }


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryDocumentationBundleError(
            f"{label} must be one lowercase SHA-256"
        )
    return value


def _require_exact_file_hash(
    root: Path, relative: Path, expected: str, *, limit: int
) -> bytes:
    raw = _read_bounded_regular_file(
        root / relative, label=f"pinned source {relative.as_posix()!r}", limit=limit
    )
    if _sha256_bytes(raw) != expected:
        raise LibraryDocumentationBundleError(
            f"pinned source {relative.as_posix()!r} drifted"
        )
    return raw


def _require_import_origin(
    label: str, value: object, *, root: Path, relative: Path
) -> None:
    source = getattr(value, "__file__", None)
    if source is None:
        try:
            source = inspect.getsourcefile(value)
        except (TypeError, OSError):
            source = None
    if type(source) is not str:
        raise LibraryDocumentationBundleError(f"cannot identify import origin for {label}")
    try:
        actual = Path(source).resolve(strict=True)
        expected = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            f"cannot resolve import origin for {label}"
        ) from exc
    if actual != expected:
        raise LibraryDocumentationBundleError(
            f"import origin for {label} is outside the pinned repository root"
        )


def _loaded_registry_semantic_sha256(
    *,
    registry_id: str,
    version: int,
    definitions: tuple[object, ...],
    adjacent_definitions: tuple[object, ...],
) -> str:
    def record(definition: object) -> dict[str, object]:
        return {
            "stable_id": definition.stable_id,
            "name": definition.name,
            "parameters": definition.parameters,
            "template_source": definition.template_source,
            "summary": definition.summary,
            "category": definition.category,
            "priority": definition.priority,
            "conceptual_dependencies": definition.conceptual_dependencies,
        }

    payload = json.dumps(
        {
            "registry_id": registry_id,
            "version": version,
            "definitions": [record(item) for item in definitions],
            "adjacent_definitions": [record(item) for item in adjacent_definitions],
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _repository_identity() -> dict[str, object]:
    return {
        "commit": SOURCE_COMMIT,
        "source": "retained-replay-pack-snapshot",
        "tree": SOURCE_TREE,
        "url": REPOSITORY_URL,
    }


def _replay_identity() -> dict[str, object]:
    return {
        "artifact_path": _REPLAY_MANIFEST_PATH.as_posix(),
        "artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
    }


def _catalog_identity() -> dict[str, object]:
    return {
        "artifact_path": _REPLAY_CATALOG_PATH.as_posix(),
        "artifact_sha256": CATALOG_ARTIFACT_SHA256,
        "catalog_sha256": CATALOG_SEMANTIC_SHA256,
        "ordered_root_sha256": CATALOG_ORDERED_ROOT_SHA256,
        "schema": "peano-library-snapshot-v3",
        "source_root_sha256": CATALOG_SOURCE_ROOT_SHA256,
        "theorem_count": EXPECTED["theorem_count"],
    }


def _runtime_dependencies() -> list[dict[str, object]]:
    return [
        {"path": _TERMS_PATH.as_posix(), "sha256": TERMS_SOURCE_SHA256},
        {"path": _FORMULAS_PATH.as_posix(), "sha256": FORMULAS_SOURCE_SHA256},
    ]


def _registry_identity() -> dict[str, object]:
    return {
        "id": "peano-lab.defined-predicates",
        "parser_registry_definition_count": 43,
        "parser_registry_semantic_sha256": (
            "924c8bc220f23ce772b72991b8234c3499be7698dc086d90509d39760a1ed0fe"
        ),
        "path": _DEFINED_SYNTAX_PATH.as_posix(),
        "serialized_definition_count": EXPECTED["definition_count"],
        "source_sha256": DEFINED_SYNTAX_SOURCE_SHA256,
        "v": 2,
    }


def _compactor_identity() -> dict[str, object]:
    return {
        "callable": "peano_lab.library.defined_edition.compact_theorem_spec",
        "path": _DEFINED_COMPACTOR_PATH.as_posix(),
        "runtime_dependencies": _runtime_dependencies(),
        "source_sha256": DEFINED_COMPACTOR_SOURCE_SHA256,
    }


def _eligibility() -> dict[str, object]:
    return {
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": LOGIC_MODE,
        "retrieval_eligible": False,
        "status": STATUS,
        "training_eligible": False,
    }


def _record_sha256(record: Mapping[str, object]) -> str:
    if "record_sha256" not in record:
        raise LibraryDocumentationBundleError("record lacks its hash field")
    preimage = {key: value for key, value in record.items() if key != "record_sha256"}
    return _sha256_json(preimage)


def _add_record_hash(record: dict[str, object]) -> dict[str, object]:
    if "record_sha256" in record:
        raise LibraryDocumentationBundleError("record hash field is duplicated")
    result = {**record, "record_sha256": "0" * 64}
    result["record_sha256"] = _record_sha256(result)
    return result


def _ordered_record_identities(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "index": record["index"],
            "name": record["name"],
            "record_sha256": record["record_sha256"],
        }
        for record in records
    ]


def _ordered_record_root(records: list[dict[str, object]]) -> str:
    triples = [
        [record["index"], record["name"], record["record_sha256"]]
        for record in records
    ]
    return _sha256_json(triples)


def _rooted_document(
    body: dict[str, object], *, root_format: str, payload: dict[str, object]
) -> dict[str, object]:
    preimage = {"format": root_format, "payload": payload, "v": SCHEMA_VERSION}
    return {**body, "root_preimage": preimage, "root_sha256": _sha256_json(preimage)}


def _finite_source_locators(
    source_rows: object,
    *,
    root: Path,
    theorem_names: set[str],
) -> dict[str, dict[str, object]]:
    if type(source_rows) is not list:
        raise LibraryDocumentationBundleError(
            "pinned catalog theorem_sources is malformed"
        )
    result: dict[str, dict[str, object]] = {}
    literal_payloads: dict[
        str, tuple[str, str, tuple[str, ...], tuple[str, ...], str] | None
    ] = {}
    for source_row in source_rows:
        if type(source_row) is not dict or set(source_row) != {"path", "sha256"}:
            raise LibraryDocumentationBundleError(
                "pinned catalog theorem source row is malformed"
            )
        relative_value = source_row["path"]
        expected_sha = _require_sha256(
            "pinned catalog theorem source hash", source_row["sha256"]
        )
        if type(relative_value) is not str or not relative_value:
            raise LibraryDocumentationBundleError(
                "pinned catalog theorem source path is malformed"
            )
        relative = Path(relative_value)
        if relative.is_absolute() or ".." in relative.parts:
            raise LibraryDocumentationBundleError(
                "pinned catalog theorem source path escapes the repository"
            )
        raw = _require_exact_file_hash(
            root, relative, expected_sha, limit=MAX_SOURCE_FILE_BYTES
        )
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(raw.decode("utf-8"), filename=relative_value)
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise LibraryDocumentationBundleError(
                f"pinned theorem source {relative_value!r} is not valid Python"
            ) from exc
        calls = sorted(
            (node for node in ast.walk(tree) if isinstance(node, ast.Call)),
            key=lambda node: (node.lineno, node.col_offset),
        )
        for node in calls:
            if not isinstance(node.func, ast.Name) or node.func.id not in {
                "TheoremSpec",
                "spec",
            }:
                continue
            name_node: ast.expr | None = node.args[0] if node.args else None
            if name_node is None:
                name_node = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "name"),
                    None,
                )
            kind = "declaration"
            if isinstance(name_node, ast.Constant) and isinstance(name_node.value, str):
                names = (name_node.value,)
                fields: dict[str, object] = {}
                for field_index, field in enumerate(_THEOREM_SPEC_FIELDS):
                    field_node: ast.expr | None = (
                        node.args[field_index]
                        if field_index < len(node.args)
                        else next(
                            (
                                keyword.value
                                for keyword in node.keywords
                                if keyword.arg == field
                            ),
                            None,
                        )
                    )
                    if field_node is None:
                        break
                    try:
                        fields[field] = ast.literal_eval(field_node)
                    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                        break
                literal_payload: tuple[
                    str, str, tuple[str, ...], tuple[str, ...], str
                ] | None = None
                if set(fields) == set(_THEOREM_SPEC_FIELDS):
                    candidate = (
                        fields["name"],
                        fields["statement"],
                        fields["dependencies"],
                        fields["script"],
                        fields["summary"],
                    )
                    if (
                        type(candidate[0]) is str
                        and type(candidate[1]) is str
                        and type(candidate[2]) is tuple
                        and all(type(item) is str for item in candidate[2])
                        and type(candidate[3]) is tuple
                        and all(type(item) is str for item in candidate[3])
                        and type(candidate[4]) is str
                    ):
                        literal_payload = candidate
            else:
                fragments = "".join(
                    item.value
                    for item in getattr(name_node, "values", ())
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
                if (
                    relative.name == "qr_small_moduli.py"
                    and isinstance(name_node, ast.JoinedStr)
                    and fragments in _GENERATED_SMALL_MODULI
                ):
                    names = _GENERATED_SMALL_MODULI[fragments]
                    kind = "generated-factory"
                    literal_payload = None
                else:
                    raise LibraryDocumentationBundleError(
                        f"TheoremSpec at {relative_value}:{node.lineno} has no "
                        "reviewed literal or finite generated name"
                    )
            for name in names:
                if name not in theorem_names:
                    continue
                if name in result:
                    # Pinned compatibility blocks repeat a few literal
                    # declarations.  They may share one canonical locator
                    # only when the complete literal theorem payloads agree;
                    # a repeated name with different mathematics fails closed.
                    if (
                        literal_payload is None
                        or literal_payloads[name] is None
                        or literal_payload != literal_payloads[name]
                    ):
                        raise LibraryDocumentationBundleError(
                            f"theorem {name!r} has conflicting pinned source declarations"
                        )
                    continue
                result[name] = {
                    "file_sha256": expected_sha,
                    "kind": kind,
                    "line": node.lineno,
                    "path": relative_value,
                }
                literal_payloads[name] = literal_payload
    if set(result) != theorem_names:
        missing = sorted(theorem_names - set(result))
        raise LibraryDocumentationBundleError(
            f"pinned source locators differ from selection: {missing[:3]!r}"
        )
    return result


def _validate_catalog(
    catalog: dict[str, object], manifest: dict[str, object]
) -> list[dict[str, object]]:
    expected_fields = {
        "certificate_policy",
        "certificate_representation",
        "ordered_root_sha256",
        "schema",
        "theorem_count",
        "theorem_source_root_sha256",
        "theorem_sources",
        "theorems",
    }
    if set(catalog) != expected_fields:
        raise LibraryDocumentationBundleError(
            "pinned catalog has missing or additional fields"
        )
    if (
        catalog.get("schema") != "peano-library-snapshot-v3"
        or catalog.get("theorem_count") != EXPECTED["theorem_count"]
        or catalog.get("ordered_root_sha256") != CATALOG_ORDERED_ROOT_SHA256
        or catalog.get("theorem_source_root_sha256") != CATALOG_SOURCE_ROOT_SHA256
    ):
        raise LibraryDocumentationBundleError("pinned catalog identity drifted")
    rows = catalog.get("theorems")
    manifest_rows = manifest.get("theorems")
    if (
        type(rows) is not list
        or type(manifest_rows) is not list
        or len(rows) != EXPECTED["theorem_count"]
        or len(manifest_rows) != len(rows)
    ):
        raise LibraryDocumentationBundleError("pinned catalog theorem rows drifted")
    for index, (catalog_row, replay_row) in enumerate(
        zip(rows, manifest_rows, strict=True)
    ):
        if type(catalog_row) is not dict or type(replay_row) is not dict:
            raise LibraryDocumentationBundleError("pinned theorem row is malformed")
        expected = {
            "dependencies": replay_row.get("declared_dependencies"),
            "index": index,
            "layer": replay_row.get("layer"),
            "name": replay_row.get("name"),
            "script": replay_row.get("script"),
            "script_sha256": replay_row.get("script_sha256"),
            "statement": replay_row.get("statement_source"),
            "statement_sha256": replay_row.get("statement_source_sha256"),
            "summary": replay_row.get("summary"),
        }
        if any(catalog_row.get(key) != value for key, value in expected.items()):
            raise LibraryDocumentationBundleError(
                f"pinned catalog/replay join drifted at row {index}"
            )
    return [_detached_object(row, "pinned catalog theorem") for row in rows]


def _load_inputs(root: Path) -> tuple[
    dict[str, object],
    dict[str, object],
    list[object],
    dict[str, dict[str, object]],
    tuple[object, ...],
    object,
]:
    manifest_raw = _read_bounded_regular_file(
        root / _REPLAY_MANIFEST_PATH,
        label="retained replay-pack manifest",
        limit=MAX_REPLAY_MANIFEST_BYTES,
    )
    if _sha256_bytes(manifest_raw) != REPLAY_MANIFEST_ARTIFACT_SHA256:
        raise LibraryDocumentationBundleError(
            "retained replay-pack manifest artifact drifted"
        )
    manifest_value = _decode_canonical_document(
        manifest_raw,
        "retained replay-pack manifest",
        limit=MAX_REPLAY_MANIFEST_BYTES,
    )

    # Verify the exact parser/checker source receipts embedded in the already
    # pinned manifest before importing the validator or theorem registry.
    kernel_identity = manifest_value.get("kernel_identity")
    kernel_sources = (
        kernel_identity.get("sources") if type(kernel_identity) is dict else None
    )
    if type(kernel_sources) is not list:
        raise LibraryDocumentationBundleError(
            "retained replay-pack kernel source receipts are malformed"
        )
    for source in kernel_sources:
        if type(source) is not dict or set(source) != {"path", "sha256"}:
            raise LibraryDocumentationBundleError(
                "retained replay-pack kernel source receipt is malformed"
            )
        relative = source["path"]
        expected_sha = _require_sha256("kernel source hash", source["sha256"])
        if type(relative) is not str:
            raise LibraryDocumentationBundleError("kernel source path is malformed")
        _require_exact_file_hash(
            root, Path(relative), expected_sha, limit=MAX_SOURCE_FILE_BYTES
        )

    try:
        import training.peano_hydra.library_replay_pack as replay_pack_module
        from training.peano_hydra.library_replay_pack import (
            LibraryReplayPackError,
            validate_replay_pack_manifest,
        )

        _require_import_origin(
            "replay-pack validator",
            replay_pack_module,
            root=root,
            relative=Path("training/peano_hydra/library_replay_pack.py"),
        )

        manifest = validate_replay_pack_manifest(manifest_value)
    except (LibraryReplayPackError, ImportError) as exc:
        raise LibraryDocumentationBundleError(
            f"retained replay-pack manifest is invalid: {exc}"
        ) from None
    manifest_catalog_identity = dict(_catalog_identity())
    manifest_catalog_identity["artifact_path"] = "catalog.json"
    if (
        manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != EXPECTED["theorem_count"]
        or manifest.get("source_catalog") != manifest_catalog_identity
    ):
        raise LibraryDocumentationBundleError(
            "retained replay-pack manifest pins drifted"
        )

    catalog_raw = _read_bounded_regular_file(
        root / _REPLAY_CATALOG_PATH,
        label="retained replay-pack catalog",
        limit=MAX_REPLAY_CATALOG_BYTES,
    )
    if _sha256_bytes(catalog_raw) != CATALOG_ARTIFACT_SHA256:
        raise LibraryDocumentationBundleError(
            "retained replay-pack catalog artifact drifted"
        )
    catalog = _decode_canonical_document(
        catalog_raw,
        "retained replay-pack catalog",
        limit=MAX_REPLAY_CATALOG_BYTES,
    )
    catalog_rows = _validate_catalog(catalog, manifest)

    replay_rows = manifest["theorems"]
    theorem_names = {row["name"] for row in replay_rows}
    locators = _finite_source_locators(
        catalog["theorem_sources"], root=root, theorem_names=theorem_names
    )

    for relative, expected in (
        (_DEFINED_SYNTAX_PATH, DEFINED_SYNTAX_SOURCE_SHA256),
        (_DEFINED_COMPACTOR_PATH, DEFINED_COMPACTOR_SOURCE_SHA256),
        (_FORMULAS_PATH, FORMULAS_SOURCE_SHA256),
        (_TERMS_PATH, TERMS_SOURCE_SHA256),
    ):
        _require_exact_file_hash(root, relative, expected, limit=MAX_SOURCE_FILE_BYTES)

    try:
        import peano_lab.kernel.formulas as formulas_module
        import peano_lab.kernel.terms as terms_module
        import peano_lab.library.defined_edition as defined_edition_module
        import peano_lab.library.defined_syntax as defined_syntax_module
        import peano_lab.library.theorems as theorems_module
        from peano_lab.library.defined_edition import compact_theorem_spec
        from peano_lab.library.defined_syntax import (
            ADJACENT_DEFINITIONS,
            ALL_DEFINITIONS,
            DEFINITIONS,
            DEFINED_SYNTAX_REGISTRY_ID,
            DEFINED_SYNTAX_REGISTRY_SHA256,
            DEFINED_SYNTAX_VERSION,
        )
        from peano_lab.library.theorems import THEOREMS, TheoremSpec
    except ImportError as exc:
        raise LibraryDocumentationBundleError(
            f"cannot import pinned theorem documentation inputs: {exc}"
        ) from None
    for label, imported, relative in (
        ("kernel formulas", formulas_module, _FORMULAS_PATH),
        ("kernel terms", terms_module, _TERMS_PATH),
        ("defined compactor module", defined_edition_module, _DEFINED_COMPACTOR_PATH),
        ("defined registry module", defined_syntax_module, _DEFINED_SYNTAX_PATH),
        (
            "theorem registry module",
            theorems_module,
            Path("peano-lab/py/peano_lab/library/theorems.py"),
        ),
        ("defined compactor callable", compact_theorem_spec, _DEFINED_COMPACTOR_PATH),
        ("TheoremSpec class", TheoremSpec, Path("peano-lab/py/peano_lab/library/theorems.py")),
        ("DefinitionSpec class", type(DEFINITIONS[0]), _DEFINED_SYNTAX_PATH),
    ):
        _require_import_origin(label, imported, root=root, relative=relative)
    loaded_registry_sha = _loaded_registry_semantic_sha256(
        registry_id=DEFINED_SYNTAX_REGISTRY_ID,
        version=DEFINED_SYNTAX_VERSION,
        definitions=tuple(DEFINITIONS),
        adjacent_definitions=tuple(ADJACENT_DEFINITIONS),
    )
    if (
        DEFINED_SYNTAX_REGISTRY_ID != _registry_identity()["id"]
        or DEFINED_SYNTAX_REGISTRY_SHA256
        != _registry_identity()["parser_registry_semantic_sha256"]
        or DEFINED_SYNTAX_VERSION != _registry_identity()["v"]
        or len(DEFINITIONS) != EXPECTED["definition_count"]
        or len(ALL_DEFINITIONS) != 43
        or len(ADJACENT_DEFINITIONS) != 3
        or loaded_registry_sha != _registry_identity()["parser_registry_semantic_sha256"]
    ):
        raise LibraryDocumentationBundleError("defined-syntax registry drifted")
    if len(THEOREMS) != EXPECTED["theorem_count"]:
        raise LibraryDocumentationBundleError("live TheoremSpec count drifted")

    specs: list[object] = []
    for index, (replay_row, catalog_row, spec) in enumerate(
        zip(replay_rows, catalog_rows, THEOREMS, strict=True)
    ):
        if type(spec) is not TheoremSpec:
            raise LibraryDocumentationBundleError(
                f"live theorem row {index} is not an exact TheoremSpec"
            )
        expected = (
            replay_row["name"],
            replay_row["statement_source"],
            tuple(replay_row["declared_dependencies"]),
            tuple(replay_row["script"]),
            replay_row["summary"],
        )
        actual = (
            spec.name,
            spec.statement,
            spec.dependencies,
            spec.script,
            spec.summary,
        )
        if actual != expected:
            raise LibraryDocumentationBundleError(
                f"live TheoremSpec differs from retained row {index}"
            )
        if catalog_row["name"] != spec.name:
            raise LibraryDocumentationBundleError(
                f"catalog join differs from TheoremSpec row {index}"
            )
        specs.append(spec)
    return manifest, catalog, specs, locators, tuple(DEFINITIONS), compact_theorem_spec


def _command_spans(
    command: str, declared_dependencies: set[str]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    match = re.match(rf"\s*({_IDENTIFIER_RE})", command)
    if match is None:
        raise LibraryDocumentationBundleError(
            f"cannot parse tactic command {command!r}"
        )
    tactic_name = match.group(1)
    tactic_span = {
        "end": match.end(1),
        "name": tactic_name,
        "start": match.start(1),
    }
    argument_start = match.end()
    arguments = command[argument_start:]
    spans: list[tuple[int, int]] = []
    if tactic_name in {"apply", "exact", "cases"}:
        found = re.fullmatch(rf"\s*({_IDENTIFIER_RE})\s*", arguments)
        if found is not None:
            spans.append(
                (
                    argument_start + found.start(1),
                    argument_start + found.end(1),
                )
            )
    elif tactic_name in {"specialize", "forall_elim"}:
        found = re.match(rf"\s*({_IDENTIFIER_RE})(?:\s|$)", arguments)
        if found is not None:
            spans.append(
                (
                    argument_start + found.start(1),
                    argument_start + found.end(1),
                )
            )
    elif tactic_name == "rewrite":
        found = re.match(
            rf"\s*(?:(?:<-|←)\s*)?({_IDENTIFIER_RE})(?:\s|$)", arguments
        )
        if found is not None:
            spans.append(
                (
                    argument_start + found.start(1),
                    argument_start + found.end(1),
                )
            )
    elif tactic_name == "simp":
        stripped = arguments.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            offset = argument_start + arguments.index("[") + 1
            body = stripped[1:-1]
            spans.extend(
                (offset + found.start(), offset + found.end())
                for found in re.finditer(_IDENTIFIER_RE, body)
            )
    elif tactic_name == "use":
        found = re.match(rf"\s*({_IDENTIFIER_RE})(?:\s|$)", arguments)
        if found is not None:
            spans.append(
                (
                    argument_start + found.start(1),
                    argument_start + found.end(1),
                )
            )

    references: list[dict[str, object]] = []
    last_end = -1
    for start, end in sorted(spans):
        if start < last_end or not (0 <= start < end <= len(command)):
            raise LibraryDocumentationBundleError(
                f"overlapping or invalid command span in {command!r}"
            )
        last_end = end
        name = command[start:end]
        if name in declared_dependencies:
            kind = "theorem"
        elif name in _PA_AXIOMS:
            kind = "axiom"
        else:
            continue
        references.append({"end": end, "kind": kind, "name": name, "start": start})
    return tactic_span, references


def _dependency_depths(replay_rows: list[dict[str, object]]) -> dict[str, int]:
    depths: dict[str, int] = {}
    for index, row in enumerate(replay_rows):
        name = row["name"]
        dependencies = row["declared_dependencies"]
        if (
            type(name) is not str
            or _THEOREM_NAME_RE.fullmatch(name) is None
            or type(dependencies) is not list
            or any(dependency not in depths for dependency in dependencies)
        ):
            raise LibraryDocumentationBundleError(
                f"retained dependency order is not topological at row {index}"
            )
        depths[name] = (
            0 if not dependencies else max(depths[dependency] for dependency in dependencies) + 1
        )
    return depths


def _build_explicit_document(
    manifest: dict[str, object], locators: dict[str, dict[str, object]]
) -> dict[str, object]:
    replay_rows = manifest["theorems"]
    depths = _dependency_depths(replay_rows)
    selected_names = [row["name"] for row in replay_rows]
    selected = set(selected_names)
    dependency_pairs: list[list[str]] = []
    node_pairs: list[list[object]] = []
    theorem_reference_pairs: set[tuple[str, str]] = set()
    tactic_heads: set[str] = set()
    theorem_reference_occurrences = 0
    tactic_line_count = 0
    tactic_text_characters = 0
    records: list[dict[str, object]] = []

    dependent_names: set[str] = set()
    for index, row in enumerate(replay_rows):
        name = row["name"]
        dependencies = row["declared_dependencies"]
        if len(dependencies) != len(set(dependencies)) or any(
            dependency not in selected for dependency in dependencies
        ):
            raise LibraryDocumentationBundleError(
                f"declared dependencies are malformed for {name!r}"
            )
        node_pairs.append([name, dependencies])
        for dependency in dependencies:
            dependency_pairs.append([dependency, name])
            dependent_names.add(dependency)

        command_lines: list[dict[str, object]] = []
        for command_index, command in enumerate(row["script"]):
            tactic, references = _command_spans(command, set(dependencies))
            tactic_heads.add(tactic["name"])
            tactic_line_count += 1
            tactic_text_characters += len(command)
            for reference in references:
                if reference["kind"] == "theorem":
                    theorem_reference_occurrences += 1
                    theorem_reference_pairs.add((reference["name"], name))
            command_lines.append(
                {
                    "index": command_index,
                    "line": command_index + 1,
                    "references": references,
                    "sha256": _sha256_bytes(command.encode("utf-8")),
                    "tactic": tactic,
                    "text": command,
                }
            )
        record = _add_record_hash(
            {
                "catalog_layer": row["layer"],
                "command_lines": command_lines,
                "declared_dependencies": dependencies,
                "dependency_depth": depths[name],
                "formula_sha256": row["formula_sha256"],
                "index": index,
                "minimality_claim": False,
                "name": name,
                "script_sha256": row["script_sha256"],
                "source": locators[name],
                "statement_canonical": row["statement_canonical"],
                "statement_canonical_sha256": row["statement_canonical_sha256"],
                "statement_source": row["statement_source"],
                "statement_source_sha256": row["statement_source_sha256"],
                "summary": row["summary"],
                "summary_sha256": _sha256_bytes(row["summary"].encode("utf-8")),
            }
        )
        records.append(record)

    dependency_edges = {(dependency, dependent) for dependency, dependent in dependency_pairs}
    if len(dependency_edges) != len(dependency_pairs):
        raise LibraryDocumentationBundleError("declared dependency edge is duplicated")
    implicit_edges = dependency_edges - theorem_reference_pairs
    aggregate = {
        "declared_dependency_edges": len(dependency_pairs),
        "dependency_depth_maximum": max(depths.values()),
        "dependency_level_count": len(set(depths.values())),
        "explicitly_referenced_dependency_edges": len(theorem_reference_pairs),
        "foundation_count": sum(not row["declared_dependencies"] for row in replay_rows),
        "implicit_dependency_edges": len(implicit_edges),
        "reference_occurrences": theorem_reference_occurrences,
        "tactic_head_count": len(tactic_heads),
        "tactic_heads": sorted(tactic_heads),
        "tactic_line_count": tactic_line_count,
        "tactic_text_characters": tactic_text_characters,
        "terminal_count": len(selected - dependent_names),
        "theorem_count": len(records),
    }
    expected_subset = {
        key: EXPECTED[key]
        for key in (
            "declared_dependency_edges",
            "dependency_depth_maximum",
            "dependency_level_count",
            "explicitly_referenced_dependency_edges",
            "foundation_count",
            "implicit_dependency_edges",
            "reference_occurrences",
            "tactic_head_count",
            "tactic_line_count",
            "tactic_text_characters",
            "terminal_count",
            "theorem_count",
        )
    }
    if {key: aggregate[key] for key in expected_subset} != expected_subset:
        raise LibraryDocumentationBundleError(
            "explicit documentation aggregate differs from the pinned contract"
        )
    dependency_receipt = {
        "edge_root_sha256": _sha256_json(dependency_pairs),
        "node_root_sha256": _sha256_json(node_pairs),
        "orientation": "dependency-to-dependent",
        "ordered_record_root_sha256": _ordered_record_root(records),
    }
    identity = _eligibility()
    body = {
        "aggregate": aggregate,
        "dependency_receipt": dependency_receipt,
        "evaluation_eligible": identity["evaluation_eligible"],
        "format": EXPLICIT_FORMAT,
        "freeze_ready": identity["freeze_ready"],
        "id": EXPLICIT_ID,
        "logic_mode": identity["logic_mode"],
        "replay_pack": _replay_identity(),
        "repository": _repository_identity(),
        "retrieval_eligible": identity["retrieval_eligible"],
        "source_catalog": _catalog_identity(),
        "status": identity["status"],
        "theorem_count": len(records),
        "theorems": records,
        "training_eligible": identity["training_eligible"],
        "v": SCHEMA_VERSION,
    }
    payload = {
        key: value for key, value in body.items() if key != "theorems"
    } | {"ordered_records": _ordered_record_identities(records)}
    return _rooted_document(
        body,
        root_format="peano-hydra-library-documentation-explicit-root-preimage",
        payload=payload,
    )


def _definition_source_line(source_text: str, name: str) -> int:
    needle = f'name="{name}"'
    matches = [
        number
        for number, line in enumerate(source_text.splitlines(), 1)
        if needle in line
    ]
    if len(matches) != 1:
        raise LibraryDocumentationBundleError(
            f"definition {name!r} has no unique pinned source line"
        )
    return matches[0]


def _definition_use_json(use: object) -> dict[str, object]:
    definition_id = getattr(use, "definition_id", None)
    name = getattr(use, "name", None)
    occurrences = getattr(use, "occurrences", None)
    if (
        type(definition_id) is not str
        or type(name) is not str
        or type(occurrences) is not int
        or occurrences < 1
    ):
        raise LibraryDocumentationBundleError("definition-use receipt is malformed")
    return {
        "definition": definition_id,
        "name": name,
        "occurrences": occurrences,
    }


def _part_json(part: object) -> dict[str, object]:
    kind = getattr(part, "kind", None)
    text = getattr(part, "text", None)
    definition_id = getattr(part, "definition_id", None)
    if type(text) is not str or not text:
        raise LibraryDocumentationBundleError("defined surface part is malformed")
    if kind == "text" and definition_id is None:
        return {"kind": "text", "text": text}
    if kind == "definition" and type(definition_id) is str:
        return {"definition": definition_id, "kind": "definition", "text": text}
    raise LibraryDocumentationBundleError("defined surface part is malformed")


def _receipt_json(receipt: object) -> dict[str, object]:
    exact = getattr(receipt, "exact_ast_equivalence", None)
    if exact is not True:
        raise LibraryDocumentationBundleError(
            "defined compaction lacks exact AST equivalence"
        )
    result = {
        "canonical_expansion_sha256": getattr(
            receipt, "canonical_expansion_sha256", None
        ),
        "defined_characters": getattr(receipt, "defined_characters", None),
        "defined_source_sha256": getattr(receipt, "defined_source_sha256", None),
        "definition_uses": [
            _definition_use_json(use)
            for use in getattr(receipt, "definition_uses", ())
        ],
        "exact_ast_equivalence": True,
        "expanded_characters": getattr(receipt, "expanded_characters", None),
        "expanded_source_sha256": getattr(receipt, "expanded_source_sha256", None),
        "free_names": list(getattr(receipt, "free_names", ())),
    }
    for key in (
        "canonical_expansion_sha256",
        "defined_source_sha256",
        "expanded_source_sha256",
    ):
        _require_sha256(f"defined receipt {key}", result[key])
    for key in ("defined_characters", "expanded_characters"):
        if type(result[key]) is not int or result[key] < 0:
            raise LibraryDocumentationBundleError(
                f"defined receipt {key} is malformed"
            )
    if not all(type(name) is str for name in result["free_names"]):
        raise LibraryDocumentationBundleError(
            "defined receipt free-name list is malformed"
        )
    return result


def _formula_compaction_json(compaction: object) -> dict[str, object]:
    expanded = getattr(compaction, "expanded_source", None)
    defined = getattr(compaction, "defined_source", None)
    if not all(type(value) is str and value for value in (expanded, defined)):
        raise LibraryDocumentationBundleError("formula compaction source is malformed")
    parts = [_part_json(part) for part in getattr(compaction, "parts", ())]
    if not parts or "".join(part["text"] for part in parts) != defined:
        raise LibraryDocumentationBundleError(
            "formula compaction parts differ from defined source"
        )
    receipt = _receipt_json(getattr(compaction, "receipt", None))
    if (
        receipt["expanded_source_sha256"]
        != _sha256_bytes(expanded.encode("utf-8"))
        or receipt["defined_source_sha256"]
        != _sha256_bytes(defined.encode("utf-8"))
        or receipt["expanded_characters"] != len(expanded)
        or receipt["defined_characters"] != len(defined)
    ):
        raise LibraryDocumentationBundleError(
            "formula compaction receipt differs from its exact sources"
        )
    return {
        "defined_source": defined,
        "expanded_source": expanded,
        "parts": parts,
        "receipt": receipt,
    }


def _build_definition_records(
    root: Path, definitions: tuple[object, ...]
) -> list[dict[str, object]]:
    source_raw = _require_exact_file_hash(
        root,
        _DEFINED_SYNTAX_PATH,
        DEFINED_SYNTAX_SOURCE_SHA256,
        limit=MAX_SOURCE_FILE_BYTES,
    )
    try:
        source_text = source_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LibraryDocumentationBundleError(
            "defined-syntax source is not UTF-8"
        ) from exc
    ids_by_name = {
        getattr(definition, "name", None): getattr(definition, "stable_id", None)
        for definition in definitions
    }
    seen: set[str] = set()
    records: list[dict[str, object]] = []
    for index, definition in enumerate(definitions):
        definition_id = getattr(definition, "stable_id", None)
        name = getattr(definition, "name", None)
        parameters = tuple(getattr(definition, "parameters", ()))
        conceptual_names = tuple(
            getattr(definition, "conceptual_dependencies", ())
        )
        if (
            type(definition_id) is not str
            or re.fullmatch(r"PD[0-9A-Y]{4}", definition_id) is None
            or type(name) is not str
            or not parameters
            or not all(type(parameter) is str for parameter in parameters)
        ):
            raise LibraryDocumentationBundleError(
                f"defined-syntax record {index} is malformed"
            )
        conceptual_dependencies = [ids_by_name[item] for item in conceptual_names]
        if any(
            type(item) is not str or item not in seen
            for item in conceptual_dependencies
        ):
            raise LibraryDocumentationBundleError(
                f"definition {name!r} has a nonpreceding conceptual dependency"
            )
        expansion = getattr(definition, "template_source", None)
        summary = getattr(definition, "summary", None)
        category = getattr(definition, "category", None)
        priority = getattr(definition, "priority", None)
        if not all(
            type(value) is str and value
            for value in (expansion, summary, category, priority)
        ):
            raise LibraryDocumentationBundleError(
                f"definition {name!r} metadata is malformed"
            )
        records.append(
            _add_record_hash(
                {
                    "category": category,
                    "conceptual_dependencies": conceptual_dependencies,
                    "expansion": expansion,
                    "expansion_sha256": _sha256_bytes(expansion.encode("utf-8")),
                    "id": definition_id,
                    "index": index,
                    "name": name,
                    "parameters": list(parameters),
                    "priority": priority,
                    "source": {
                        "file_sha256": DEFINED_SYNTAX_SOURCE_SHA256,
                        "line": _definition_source_line(source_text, name),
                        "path": _DEFINED_SYNTAX_PATH.as_posix(),
                    },
                    "summary": summary,
                }
            )
        )
        seen.add(definition_id)
    if len(records) != EXPECTED["definition_count"]:
        raise LibraryDocumentationBundleError("definition record count drifted")
    return records


def _build_defined_document(
    *,
    root: Path,
    specs: list[object],
    definitions: tuple[object, ...],
    compact_theorem_spec: object,
    explicit: dict[str, object],
) -> dict[str, object]:
    if not callable(compact_theorem_spec):
        raise LibraryDocumentationBundleError("defined compactor is not callable")
    definition_records = _build_definition_records(root, definitions)
    serialized_definition_ids = {record["id"] for record in definition_records}
    explicit_records = explicit["theorems"]
    records: list[dict[str, object]] = []
    changed_statements = 0
    local_count = 0
    changed_locals = 0
    expanded_statement_characters = 0
    defined_statement_characters = 0
    expanded_local_characters = 0
    defined_local_characters = 0
    total_uses: Counter[str] = Counter()

    for index, (spec, explicit_record) in enumerate(
        zip(specs, explicit_records, strict=True)
    ):
        try:
            compacted = compact_theorem_spec(spec, scope="public")
        except (TypeError, ValueError, RecursionError) as exc:
            raise LibraryDocumentationBundleError(
                f"defined compaction failed for row {index}: {exc}"
            ) from None
        if getattr(getattr(compacted, "expanded_spec", None), "name", None) != spec.name:
            raise LibraryDocumentationBundleError(
                f"defined compaction name drifted at row {index}"
            )
        statement = _formula_compaction_json(compacted.statement)
        changed_statements += bool(statement["receipt"]["definition_uses"])
        expanded_statement_characters += len(statement["expanded_source"])
        defined_statement_characters += len(statement["defined_source"])

        script: list[dict[str, object]] = []
        for line_index, tactic in enumerate(compacted.tactics):
            expanded_command = tactic.expanded_command
            defined_command = tactic.defined_command
            parts = [_part_json(part) for part in tactic.parts]
            if "".join(part["text"] for part in parts) != defined_command:
                raise LibraryDocumentationBundleError(
                    f"defined command parts drifted at row {index}, line {line_index + 1}"
                )
            proposition = (
                None
                if tactic.proposition is None
                else _formula_compaction_json(tactic.proposition)
            )
            if proposition is not None:
                local_count += 1
                changed_locals += bool(proposition["receipt"]["definition_uses"])
                expanded_local_characters += len(proposition["expanded_source"])
                defined_local_characters += len(proposition["defined_source"])
            script.append(
                {
                    "defined_command": defined_command,
                    "defined_command_sha256": _sha256_bytes(
                        defined_command.encode("utf-8")
                    ),
                    "expanded_command": expanded_command,
                    "expanded_command_sha256": _sha256_bytes(
                        expanded_command.encode("utf-8")
                    ),
                    "index": line_index,
                    "line": tactic.line_number,
                    "local_name": tactic.local_name,
                    "parts": parts,
                    "proposition": proposition,
                    "tactic": tactic.tactic,
                }
            )
        uses = [_definition_use_json(use) for use in compacted.definition_uses]
        nested_uses = list(statement["receipt"]["definition_uses"])
        nested_uses.extend(
            use
            for tactic_row in script
            if tactic_row["proposition"] is not None
            for use in tactic_row["proposition"]["receipt"]["definition_uses"]
        )
        if any(
            use["definition"] not in serialized_definition_ids
            for use in [*uses, *nested_uses]
        ):
            raise LibraryDocumentationBundleError(
                f"defined theorem {spec.name!r} uses an unserialized definition"
            )
        total_uses.update({item["name"]: item["occurrences"] for item in uses})
        records.append(
            _add_record_hash(
                {
                    "definition_uses": uses,
                    "explicit_record_sha256": explicit_record["record_sha256"],
                    "index": index,
                    "minimality_claim": False,
                    "name": spec.name,
                    "script": script,
                    "statement": statement,
                }
            )
        )

    aggregate = {
        "changed_local_propositions": changed_locals,
        "changed_statements": changed_statements,
        "defined_local_characters": defined_local_characters,
        "defined_statement_characters": defined_statement_characters,
        "definition_count": len(definition_records),
        "definition_occurrences": sum(total_uses.values()),
        "expanded_local_characters": expanded_local_characters,
        "expanded_statement_characters": expanded_statement_characters,
        "local_proposition_count": local_count,
        "ordered_record_root_sha256": _ordered_record_root(records),
        "theorem_count": len(records),
    }
    expected_subset = {
        key: EXPECTED[key]
        for key in (
            "changed_local_propositions",
            "changed_statements",
            "defined_local_characters",
            "defined_statement_characters",
            "definition_count",
            "definition_occurrences",
            "expanded_local_characters",
            "expanded_statement_characters",
            "local_proposition_count",
            "theorem_count",
        )
    }
    if {key: aggregate[key] for key in expected_subset} != expected_subset:
        raise LibraryDocumentationBundleError(
            "defined documentation aggregate differs from the pinned contract"
        )
    definitions_root = _sha256_json(
        [
            [record["index"], record["id"], record["record_sha256"]]
            for record in definition_records
        ]
    )
    identity = _eligibility()
    body = {
        "aggregate": aggregate,
        "compactor": _compactor_identity(),
        "definitions": definition_records,
        "evaluation_eligible": identity["evaluation_eligible"],
        "explicit_root_sha256": explicit["root_sha256"],
        "format": DEFINED_FORMAT,
        "freeze_ready": identity["freeze_ready"],
        "id": DEFINED_ID,
        "logic_mode": identity["logic_mode"],
        "registry": _registry_identity(),
        "replay_pack": _replay_identity(),
        "retrieval_eligible": identity["retrieval_eligible"],
        "status": identity["status"],
        "theorem_count": len(records),
        "theorems": records,
        "training_eligible": identity["training_eligible"],
        "v": SCHEMA_VERSION,
    }
    payload = {
        key: value
        for key, value in body.items()
        if key not in {"definitions", "theorems"}
    } | {
        "definitions_root_sha256": definitions_root,
        "ordered_records": _ordered_record_identities(records),
    }
    return _rooted_document(
        body,
        root_format="peano-hydra-library-documentation-defined-root-preimage",
        payload=payload,
    )


def _count_disallowed_fields(value: object) -> int:
    if type(value) is list:
        return sum(_count_disallowed_fields(item) for item in value)
    if type(value) is not dict:
        return 0
    return sum(key in _DISALLOWED_THEOREM_FIELDS for key in value) + sum(
        _count_disallowed_fields(item) for item in value.values()
    )


def _build_isolation_receipt(
    *,
    manifest: dict[str, object],
    explicit: dict[str, object],
    defined: dict[str, object],
) -> dict[str, object]:
    selected_names = [row["name"] for row in manifest["theorems"]]
    explicit_names = [row["name"] for row in explicit["theorems"]]
    defined_names = [row["name"] for row in defined["theorems"]]
    selected = set(selected_names)
    explicit_set = set(explicit_names)
    defined_set = set(defined_names)
    outside_edges = sum(
        dependency not in selected
        for row in explicit["theorems"]
        for dependency in row["declared_dependencies"]
    )
    disallowed = _count_disallowed_fields(explicit["theorems"]) + _count_disallowed_fields(
        defined["theorems"]
    )
    duplicate_names = (
        len(explicit_names)
        - len(explicit_set)
        + len(defined_names)
        - len(defined_set)
    )
    counts = {
        "definition_records": len(defined["definitions"]),
        "defined_records": len(defined_names),
        "disallowed_fields": disallowed,
        "duplicate_names": duplicate_names,
        "explicit_records": len(explicit_names),
        "foreign_defined_names": len(defined_set - selected),
        "foreign_explicit_names": len(explicit_set - selected),
        "missing_defined_names": len(selected - defined_set),
        "missing_explicit_names": len(selected - explicit_set),
        "outside_dependency_edges": outside_edges,
        "selected_names": len(selected_names),
    }
    expected_counts = {
        "definition_records": EXPECTED["definition_count"],
        "defined_records": EXPECTED["theorem_count"],
        "disallowed_fields": 0,
        "duplicate_names": 0,
        "explicit_records": EXPECTED["theorem_count"],
        "foreign_defined_names": 0,
        "foreign_explicit_names": 0,
        "missing_defined_names": 0,
        "missing_explicit_names": 0,
        "outside_dependency_edges": 0,
        "selected_names": EXPECTED["theorem_count"],
    }
    checks = {
        "declared_edges_internal": outside_edges == 0,
        "exact_member_names": explicit_set == selected == defined_set,
        "exact_selected_order": selected_names
        == [row["name"] for row in manifest["theorems"]],
        "explicit_defined_order": explicit_names == defined_names == selected_names,
        "no_disallowed_fields": disallowed == 0,
        "no_duplicate_names": duplicate_names == 0,
        "no_foreign_names": not (explicit_set - selected or defined_set - selected),
    }
    if counts != expected_counts or not all(checks.values()):
        raise LibraryDocumentationBundleError(
            "candidate documentation selection is not isolated"
        )
    roots = {
        "defined_document_root_sha256": defined["root_sha256"],
        "defined_ordered_record_root_sha256": defined["aggregate"][
            "ordered_record_root_sha256"
        ],
        "dependency_edge_root_sha256": explicit["dependency_receipt"][
            "edge_root_sha256"
        ],
        "dependency_node_root_sha256": explicit["dependency_receipt"][
            "node_root_sha256"
        ],
        "explicit_document_root_sha256": explicit["root_sha256"],
        "explicit_ordered_record_root_sha256": explicit["dependency_receipt"][
            "ordered_record_root_sha256"
        ],
        "selected_name_root_sha256": _sha256_json(selected_names),
    }
    identity = _eligibility()
    body = {
        "checks": checks,
        "counts": counts,
        "evaluation_eligible": identity["evaluation_eligible"],
        "format": ISOLATION_FORMAT,
        "freeze_ready": identity["freeze_ready"],
        "id": ISOLATION_ID,
        "logic_mode": identity["logic_mode"],
        "retrieval_eligible": identity["retrieval_eligible"],
        "roots": roots,
        "status": identity["status"],
        "training_eligible": identity["training_eligible"],
        "v": SCHEMA_VERSION,
    }
    return _rooted_document(
        body,
        root_format="peano-hydra-library-documentation-isolation-root-preimage",
        payload=dict(body),
    )


def _document_limit(filename: str) -> int:
    limits = {
        SCHEMA_FILE: MAX_SCHEMA_BYTES,
        EXPLICIT_FILE: MAX_EXPLICIT_BYTES,
        DEFINED_FILE: MAX_DEFINED_BYTES,
        ISOLATION_FILE: MAX_ISOLATION_BYTES,
        MANIFEST_FILE: MAX_MANIFEST_BYTES,
    }
    try:
        return limits[filename]
    except KeyError:
        raise LibraryDocumentationBundleError(
            f"unknown documentation member {filename!r}"
        ) from None


def _build_manifest(
    *,
    schema: dict[str, object],
    explicit: dict[str, object],
    defined: dict[str, object],
    isolation: dict[str, object],
) -> dict[str, object]:
    members = {
        SCHEMA_FILE: schema,
        EXPLICIT_FILE: explicit,
        DEFINED_FILE: defined,
        ISOLATION_FILE: isolation,
    }
    files = []
    for filename in MANIFEST_MEMBER_FILES:
        raw = canonical_document_bytes(
            members[filename], limit=_document_limit(filename)
        )
        files.append(
            {"bytes": len(raw), "name": filename, "sha256": _sha256_bytes(raw)}
        )
    identity = _eligibility()
    aggregate = {
        "declared_dependency_edges": explicit["aggregate"][
            "declared_dependency_edges"
        ],
        "definition_count": defined["aggregate"]["definition_count"],
        "theorem_count": explicit["theorem_count"],
    }
    source_bindings = {
        "compactor": _compactor_identity(),
        "registry": _registry_identity(),
        "replay_catalog": _catalog_identity(),
        "replay_manifest": _replay_identity(),
        "repository": _repository_identity(),
    }
    body = {
        "aggregate": aggregate,
        "evaluation_eligible": identity["evaluation_eligible"],
        "files": files,
        "format": MANIFEST_FORMAT,
        "freeze_ready": identity["freeze_ready"],
        "id": MANIFEST_ID,
        "logic_mode": identity["logic_mode"],
        "retrieval_eligible": identity["retrieval_eligible"],
        "schema": documentation_bundle_schema_identity(),
        "source_bindings": source_bindings,
        "status": identity["status"],
        "training_eligible": identity["training_eligible"],
        "v": SCHEMA_VERSION,
    }
    return _rooted_document(
        body,
        root_format="peano-hydra-library-documentation-manifest-root-preimage",
        payload=dict(body),
    )


def _build_candidate_documentation_bundle(
    *, repository_root: Path | None
) -> dict[str, dict[str, object]]:
    root = _repository_root(repository_root)
    schema = documentation_bundle_schema()
    manifest, _catalog, specs, locators, definitions, compactor = _load_inputs(root)
    explicit = _build_explicit_document(manifest, locators)
    defined = _build_defined_document(
        root=root,
        specs=specs,
        definitions=definitions,
        compact_theorem_spec=compactor,
        explicit=explicit,
    )
    isolation = _build_isolation_receipt(
        manifest=manifest, explicit=explicit, defined=defined
    )
    bundle_manifest = _build_manifest(
        schema=schema, explicit=explicit, defined=defined, isolation=isolation
    )
    return {
        SCHEMA_FILE: schema,
        EXPLICIT_FILE: explicit,
        DEFINED_FILE: defined,
        ISOLATION_FILE: isolation,
        MANIFEST_FILE: bundle_manifest,
    }


def _validate_against_expected(
    value: object, *, repository_root: Path | None
) -> dict[str, dict[str, object]]:
    if type(value) is not dict or set(value) != set(DOCUMENT_FILES):
        raise LibraryDocumentationBundleError(
            "documentation bundle must map the exact five member names"
        )
    supplied: dict[str, dict[str, object]] = {}
    for filename in DOCUMENT_FILES:
        document = value[filename]
        if type(document) is not dict:
            raise LibraryDocumentationBundleError(
                f"documentation member {filename!r} must be one object"
            )
        raw = canonical_document_bytes(document, limit=_document_limit(filename))
        supplied[filename] = _decode_canonical_document(
            raw, f"documentation member {filename!r}", limit=_document_limit(filename)
        )
    expected = _build_candidate_documentation_bundle(
        repository_root=repository_root
    )
    for filename in DOCUMENT_FILES:
        supplied_raw = canonical_document_bytes(
            supplied[filename], limit=_document_limit(filename)
        )
        expected_raw = canonical_document_bytes(
            expected[filename], limit=_document_limit(filename)
        )
        if supplied_raw != expected_raw:
            raise LibraryDocumentationBundleError(
                f"documentation member {filename!r} differs from pinned reconstruction"
            )
    return supplied


def build_candidate_documentation_bundle(
    *, repository_root: Path | None = None
) -> dict[str, dict[str, object]]:
    """Build the exact tagless candidate documentation bundle in memory."""

    built = _build_candidate_documentation_bundle(repository_root=repository_root)
    # Detach every return value so callers cannot observe builder object sharing.
    return {
        filename: _detached_object(document, f"built {filename}")
        for filename, document in built.items()
    }


def validate_documentation_bundle(
    value: object, *, repository_root: Path | None = None
) -> dict[str, dict[str, object]]:
    """Validate all roots, shapes, fixed inputs, and exact reconstructed bytes."""

    return _validate_against_expected(value, repository_root=repository_root)


def _exact_directory(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("documentation directory must be a pathlib.Path")
    try:
        metadata = path.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryDocumentationBundleError(
                "documentation directory must be a non-symlink directory"
            )
        resolved = path.resolve(strict=True)
        entries: dict[str, bool] = {}
        with os.scandir(resolved) as iterator:
            for entry in iterator:
                if entry.name in entries or len(entries) >= len(DOCUMENT_FILES):
                    raise LibraryDocumentationBundleError(
                        "documentation directory has duplicate or extra members"
                    )
                entries[entry.name] = entry.is_file(follow_symlinks=False)
    except LibraryDocumentationBundleError:
        raise
    except OSError as exc:
        raise LibraryDocumentationBundleError(
            "cannot inspect documentation directory"
        ) from exc
    if set(entries) != set(DOCUMENT_FILES) or not all(entries.values()):
        raise LibraryDocumentationBundleError(
            "documentation directory differs from the exact five-member layout"
        )
    return resolved


def load_documentation_bundle(
    directory: Path, *, repository_root: Path | None = None
) -> dict[str, dict[str, object]]:
    """Load and validate one exact bounded, no-follow five-file directory."""

    root = _exact_directory(directory)
    documents: dict[str, dict[str, object]] = {}
    for filename in DOCUMENT_FILES:
        raw = _read_bounded_regular_file(
            root / filename,
            label=f"documentation member {filename!r}",
            limit=_document_limit(filename),
        )
        documents[filename] = _decode_canonical_document(
            raw,
            f"documentation member {filename!r}",
            limit=_document_limit(filename),
        )
    return validate_documentation_bundle(
        documents, repository_root=repository_root
    )


__all__ = [
    "LibraryDocumentationBundleError",
    "documentation_bundle_schema",
    "documentation_bundle_schema_identity",
    "canonical_document_bytes",
    "build_candidate_documentation_bundle",
    "validate_documentation_bundle",
    "load_documentation_bundle",
]
