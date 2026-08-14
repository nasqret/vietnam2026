"""Tactic-free one-root comparison of four retained proof constructions.

This A2.3e aggregator authenticates the retained A2.3a comparison and its
independent kernel receipt together with the retained A2.3d Cut-liveness result
and its independent reconstruction receipt.  It then compares exactly four
``odd_add_odd`` artifacts.  It does not rebuild a proof, execute tactics, search
for another construction, or publish a dependency vector.

The only new positive claim is scoped: the construction-derived direct vector
``[mul_add, add_comm]`` was independently reproduced upstream and is included
in an exact four-candidate Pareto comparison.  Nothing here establishes a
global optimum, best-known status, theorem-level necessity, minimality, A2
completion, publication, or authority.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Mapping, Sequence


VERSION = 1
FORMAT = "peano-hydra-library-pilot-optimized-construction-comparison-v1"
DOCUMENT_ID = (
    "peano-hydra-l0-pilot-optimized-construction-comparison-candidate-v1"
)
ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-optimized-construction-comparison-"
    "root-preimage-v1"
)
THEOREM_RECORD_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-optimized-construction-comparison-"
    "theorem-record-preimage-v1"
)
STATUS = "candidate-only-fixed-one-root-four-candidate-comparison"
LOGIC_MODE = "intuitionistic"

SCHEMA_FORMAT = (
    "peano-hydra-library-pilot-optimized-construction-comparison-schema"
)
SCHEMA_ID = (
    "peano-hydra-library-pilot-optimized-construction-comparison-schema-v1"
)
SCHEMA_BYTES = 9_702
SCHEMA_SHA256 = (
    "f927f2c0590a82495498230a7b6c159e63c8670162540fdd5283f86cccb35d54"
)
SCHEMA_SEMANTIC_SHA256 = (
    "fb820a246a38211cd0250ae2ea0fb4cc70dee08b6151a2974c4226f3b38e92f9"
)

MAX_SCHEMA_BYTES = 131_072
MAX_INPUT_BYTES = 1_048_576
MAX_DOCUMENT_BYTES = 1_048_576
MAX_JSON_NODES = 250_000
MAX_JSON_DEPTH = 96
MAX_SAFE_INTEGER = (1 << 53) - 1

EXPECTED_INDEX = 256
EXPECTED_NAME = "odd_add_odd"
EXPECTED_FORMULA_SHA256 = (
    "4d2aa6b4e387657e562641830dab2953890b5493d6e6858b6c36d73b06786c31"
)
EXPECTED_VECTOR = ("mul_add", "add_comm")
EXPECTED_VECTOR_LF_SHA256 = (
    "ca9176e5c542ed28309d630ef0cb06e69f4edad391a3505e498207b83ac830c4"
)
EXPECTED_CLOSURE = (
    "zero_add",
    "add_succ_left",
    "add_comm",
    "add_assoc",
    "mul_add",
)
EXPECTED_CLOSURE_LF_SHA256 = (
    "a4abec5d9eb955ed95f6eea761c96c3de0166b3df3c64fe8e898d8766ed5c5f2"
)
COMPARISON_AXES = (
    "artifact_bytes",
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
)
CANDIDATE_IDS = (
    "retained-replay",
    "a2.2-direct-cut-rebuild",
    "layered-closure",
    "cut-liveness",
)
EXPECTED_FRONTIER = ("layered-closure", "cut-liveness")
EXPECTED_REPRESENTATIVE = "cut-liveness"
REPRESENTATIVE_TIE_BREAK = (
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
    "artifact_bytes",
    "candidate_kind_order",
    "artifact_sha256",
    "candidate_id",
)

FALSE_CLAIMS = (
    "a2_complete",
    "authority_granted",
    "best_known",
    "bounded_three_root_vector_audit_complete",
    "dependency_minimality_established",
    "dependency_necessity_established",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_complete",
    "global_comparison_complete",
    "global_optimized_vector_audit_complete",
    "human_review_complete",
    "kernel_artifacts_reexecuted",
    "lineage_complete",
    "logical_minimality_independently_verified",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "producer_git_verified",
    "public_graph_applied",
    "publication_applied",
    "publication_union_complete",
    "publication_union_verified",
    "research_evaluation_eligible",
    "retrieval_eligible",
    "route_rejections_independently_verified",
    "training_eligible",
)

_MODULE_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = Path(__file__).with_name(
    "library-pilot-optimized-construction-comparison-schema-v1.json"
)


class LibraryPilotOptimizedConstructionComparisonError(ValueError):
    """An input, comparison, canonical document, or claim is invalid."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"duplicate JSON key {key!r}"
            )
        result[key] = value
    return result


def _reject_float(value: str) -> object:
    raise LibraryPilotOptimizedConstructionComparisonError(
        f"floating-point JSON value {value!r} is forbidden"
    )


def _reject_constant(value: str) -> object:
    raise LibraryPilotOptimizedConstructionComparisonError(
        f"non-finite JSON value {value!r} is forbidden"
    )


def _validate_json(value: object, *, depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [MAX_JSON_NODES]
    budget[0] -= 1
    if budget[0] < 0 or depth > MAX_JSON_DEPTH:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "JSON structure exceeds its registered bound"
        )
    if value is None or type(value) in (bool, str):
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            raise LibraryPilotOptimizedConstructionComparisonError(
                "JSON integer exceeds the exact safe domain"
            )
        return
    if type(value) is list:
        for item in value:
            _validate_json(item, depth=depth + 1, budget=budget)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise LibraryPilotOptimizedConstructionComparisonError(
                    "JSON object key is not a string"
                )
            _validate_json(item, depth=depth + 1, budget=budget)
        return
    raise LibraryPilotOptimizedConstructionComparisonError(
        f"unsupported JSON value type {type(value).__name__}"
    )


def _compact_bytes(value: object) -> bytes:
    _validate_json(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_document_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return canonical retained JSON with one terminal newline."""

    if type(limit) is not int or limit <= 0:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "canonical byte limit must be a positive exact integer"
        )
    raw = _compact_bytes(value) + b"\n"
    if len(raw) > limit:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "canonical document exceeds its byte bound"
        )
    return raw


def _decode_object(raw: bytes, *, label: str) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} is not UTF-8"
        ) from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except LibraryPilotOptimizedConstructionComparisonError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} is not strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} must be one JSON object"
        )
    _validate_json(value)
    return value


def _lexical_absolute(path: Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = Path.cwd() / value
    return Path(os.path.abspath(os.fspath(value)))


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _require_directory_chain(path: Path, *, label: str) -> None:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotOptimizedConstructionComparisonError(
                    f"{label} contains a symlink or non-directory"
                )
    except LibraryPilotOptimizedConstructionComparisonError:
        raise
    except OSError as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"cannot inspect {label}"
        ) from exc


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label=f"{label} ancestors")
    try:
        inspected = absolute.lstat()
    except OSError as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _stat_identity(inspected) != _stat_identity(before)
        ):
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"{label} is not the inspected bounded regular file"
            )
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        path_after = absolute.lstat()
        if (
            len(raw) > limit
            or _stat_identity(before) != _stat_identity(after)
            or stat.S_ISLNK(path_after.st_mode)
            or not stat.S_ISREG(path_after.st_mode)
            or _stat_identity(after) != _stat_identity(path_after)
        ):
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"{label} changed or exceeded its bound while read"
            )
        return raw
    except OSError as exc:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)


def _repository_root(value: Path | None) -> Path:
    root = _MODULE_ROOT if value is None else _lexical_absolute(value)
    _require_directory_chain(root, label="repository root")
    return root


def optimized_construction_comparison_schema() -> dict[str, object]:
    """Load and authenticate the immutable A2.3e comparison schema."""

    raw = _read_regular(_SCHEMA_PATH, label="comparison schema", limit=MAX_SCHEMA_BYTES)
    if len(raw) != SCHEMA_BYTES or _sha256(raw) != SCHEMA_SHA256:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "comparison schema source identity drifted"
        )
    value = _decode_object(raw, label="comparison schema")
    if (
        value.get("v") != VERSION
        or value.get("format") != SCHEMA_FORMAT
        or value.get("id") != SCHEMA_ID
        or value.get("logic_mode") != LOGIC_MODE
        or _sha256(_compact_bytes(value)) != SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "comparison schema semantic identity drifted"
        )
    return deepcopy(value)


def optimized_construction_comparison_schema_identity() -> dict[str, object]:
    value = optimized_construction_comparison_schema()
    return {
        "artifact_bytes": SCHEMA_BYTES,
        "artifact_sha256": SCHEMA_SHA256,
        "format": value["format"],
        "id": value["id"],
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": value["v"],
    }


def _require_false(value: Mapping[str, object], names: Sequence[str], *, label: str) -> None:
    for name in names:
        if name in value and value[name] is not False:
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"{label} overclaims {name!r}"
            )


def _find_theorem(value: Mapping[str, object], *, label: str) -> dict[str, object]:
    rows = value.get("theorems")
    if type(rows) is not list:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} theorem rows are malformed"
        )
    matches = [
        row
        for row in rows
        if type(row) is dict
        and row.get("index") == EXPECTED_INDEX
        and row.get("name") == EXPECTED_NAME
    ]
    if len(matches) != 1:
        raise LibraryPilotOptimizedConstructionComparisonError(
            f"{label} does not contain the exact pilot theorem once"
        )
    return matches[0]


def _candidate_tuple(row: Mapping[str, object]) -> tuple[str, int, str, dict[str, int]]:
    candidate_id = row.get("candidate_id")
    order = row.get("candidate_kind_order")
    digest = row.get("artifact_sha256")
    metrics = row.get("metrics")
    if (
        type(candidate_id) is not str
        or type(order) is not int
        or type(digest) is not str
        or len(digest) != 64
        or type(metrics) is not dict
        or set(metrics) != set(COMPARISON_AXES)
        or any(type(metrics.get(key)) is not int for key in COMPARISON_AXES)
        or any(metrics[key] <= 0 for key in COMPARISON_AXES[:-1])
        or metrics["cut_nodes"] < 0
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "candidate comparison row is malformed"
        )
    return candidate_id, order, digest, metrics


def componentwise_nondominated(
    candidates: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    """Return nondominated IDs in the registered input order."""

    if not candidates:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "candidate universe must be non-empty"
        )
    parsed = tuple(_candidate_tuple(row) for row in candidates)
    if len({row[0] for row in parsed}) != len(parsed) or len(
        {row[1] for row in parsed}
    ) != len(parsed):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "candidate IDs and kind orders must be unique"
        )
    result: list[str] = []
    for index, (candidate_id, _order, _digest, metrics) in enumerate(parsed):
        dominated = False
        for other_index, (_other_id, _other_order, _other_digest, other) in enumerate(parsed):
            if index == other_index:
                continue
            if all(other[axis] <= metrics[axis] for axis in COMPARISON_AXES) and any(
                other[axis] < metrics[axis] for axis in COMPARISON_AXES
            ):
                dominated = True
                break
        if not dominated:
            result.append(candidate_id)
    return tuple(result)


def select_fixed_set_representative(
    candidates: Sequence[Mapping[str, object]],
) -> str:
    """Select the deterministic fixed-set representative; never a global best."""

    parsed = tuple(_candidate_tuple(row) for row in candidates)
    if not parsed:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "frontier must be non-empty"
        )
    return min(
        parsed,
        key=lambda row: (
            row[3]["proof_nodes"],
            row[3]["proof_depth"],
            row[3]["cut_nodes"],
            row[3]["artifact_bytes"],
            row[1],
            row[2],
            row[0],
        ),
    )[0]


def _load_fixed_inputs(root: Path) -> tuple[dict[str, object], ...]:
    schema = optimized_construction_comparison_schema()
    pins = schema.get("fixed_inputs")
    if type(pins) is not list or len(pins) != 4:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "schema fixed input vector is malformed"
        )
    results: list[dict[str, object]] = []
    for pin in pins:
        if type(pin) is not dict or set(pin) != {
            "artifact_bytes",
            "artifact_sha256",
            "label",
            "path",
            "root_sha256",
        }:
            raise LibraryPilotOptimizedConstructionComparisonError(
                "schema fixed input row is malformed"
            )
        relative = Path(str(pin["path"]))
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise LibraryPilotOptimizedConstructionComparisonError(
                "schema fixed input path is unsafe"
            )
        raw = _read_regular(
            root / relative,
            label=str(pin["label"]),
            limit=MAX_INPUT_BYTES,
        )
        if len(raw) != pin["artifact_bytes"] or _sha256(raw) != pin["artifact_sha256"]:
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"fixed input {pin['label']!r} identity drifted"
            )
        value = _decode_object(raw, label=str(pin["label"]))
        preimage = value.get("root_preimage")
        if (
            type(preimage) is not dict
            or _sha256(_compact_bytes(preimage)) != pin["root_sha256"]
            or value.get("root_sha256") != pin["root_sha256"]
        ):
            raise LibraryPilotOptimizedConstructionComparisonError(
                f"fixed input {pin['label']!r} root differs"
            )
        results.append(value)
    return tuple(results)


def _derive_candidates(inputs: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    schema = optimized_construction_comparison_schema()
    expected = schema["expected_theorem"]
    expected_rows = expected["candidates"]
    a23a_candidate, a23a_verifier, a23d_candidate, a23d_verifier = inputs

    if (
        a23a_verifier.get("status") != "passed"
        or a23a_verifier.get("kernel_artifacts_verified") is not True
        or a23a_verifier.get("candidate", {}).get("artifact_sha256")
        != schema["fixed_inputs"][0]["artifact_sha256"]
        or a23a_verifier.get("candidate", {}).get("root_sha256")
        != schema["fixed_inputs"][0]["root_sha256"]
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3a verification receipt is not the registered passed receipt"
        )
    _require_false(
        a23a_verifier,
        (
            "a2_complete",
            "dependency_vectors_complete",
            "minimality_claim",
            "optimized_best_known",
            "optimized_vector_independently_audited",
            "publication_union_complete",
            "publication_union_verified",
        ),
        label="A2.3a verifier",
    )
    a23a_row = _find_theorem(a23a_candidate, label="A2.3a candidate")
    a23a_verified_row = _find_theorem(a23a_verifier, label="A2.3a verifier")
    if a23a_verified_row.get("candidate_record_sha256") != a23a_row.get("record_sha256"):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3a theorem candidate/verifier join differs"
        )
    candidate_artifacts = a23a_row.get("artifacts")
    verified_artifacts = a23a_verified_row.get("artifacts")
    if (
        type(candidate_artifacts) is not list
        or type(verified_artifacts) is not list
        or len(candidate_artifacts) != 3
        or len(verified_artifacts) != 3
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3a odd candidate universe differs"
        )

    derived: list[dict[str, object]] = []
    for position in range(3):
        source = candidate_artifacts[position]
        verified = verified_artifacts[position]
        expected_row = expected_rows[position]
        if type(source) is not dict or type(verified) is not dict:
            raise LibraryPilotOptimizedConstructionComparisonError(
                "A2.3a artifact row is malformed"
            )
        row = {
            "artifact_sha256": source.get("artifact_sha256"),
            "candidate_id": source.get("candidate_id"),
            "candidate_kind_order": source.get("candidate_kind_order"),
            "direct_dependencies": source.get("surface", {}).get("direct_dependencies"),
            "direct_dependencies_lf_sha256": source.get("surface", {}).get(
                "direct_dependencies_lf_sha256"
            ),
            "fuel": source.get("fuel"),
            "metrics": source.get("metrics"),
            "proof_term_sha256": source.get("proof_term_sha256"),
            "surface_basis": source.get("surface", {}).get("surface_basis"),
        }
        verified_projection = {
            "artifact_sha256": verified.get("artifact_sha256"),
            "candidate_id": verified.get("candidate_id"),
            "candidate_kind_order": verified.get("candidate_kind_order"),
            "fuel": verified.get("fuel"),
            "metrics": verified.get("metrics"),
            "proof_term_sha256": verified.get("proof_term_sha256"),
        }
        if any(row[key] != verified_projection[key] for key in verified_projection):
            raise LibraryPilotOptimizedConstructionComparisonError(
                "A2.3a artifact identity differs from independent observation"
            )
        if row != expected_row:
            raise LibraryPilotOptimizedConstructionComparisonError(
                "A2.3a artifact differs from the preregistered candidate row"
            )
        derived.append(deepcopy(row))

    theorem = a23d_candidate.get("theorem")
    receipt_theorem = a23d_verifier.get("theorem")
    if type(theorem) is not dict or type(receipt_theorem) is not dict:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d theorem receipt is malformed"
        )
    if (
        a23d_verifier.get("status") != "passed"
        or a23d_verifier.get("candidate_artifact_sha256")
        != schema["fixed_inputs"][2]["artifact_sha256"]
        or a23d_verifier.get("candidate_root_sha256")
        != schema["fixed_inputs"][2]["root_sha256"]
        or a23d_verifier.get("derived_artifact_byte_identical") is not True
        or a23d_verifier.get("derived_direct_vector_independently_reproduced") is not True
        or a23d_verifier.get("encoded_tagged_array_transform_independently_executed")
        is not True
        or a23d_verifier.get("input_and_output_kernel_checked") is not True
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d independent receipt is not the registered passed reconstruction"
        )
    _require_false(
        a23d_verifier,
        (
            "a2_complete",
            "best_known",
            "dependency_minimality_established",
            "dependency_necessity_established",
            "dependency_vectors_complete",
            "global_comparison_complete",
            "global_optimized_vector_audit_complete",
            "logical_minimality_independently_verified",
            "optimized_best_known",
            "optimized_vector_independently_audited",
            "publication_union_complete",
            "publication_union_verified",
            "route_rejections_independently_verified",
        ),
        label="A2.3d verifier",
    )
    artifact = theorem.get("candidate_artifact")
    if type(artifact) is not dict:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d candidate artifact is malformed"
        )
    row = {
        "artifact_sha256": artifact.get("artifact_sha256"),
        "candidate_id": "cut-liveness",
        "candidate_kind_order": 3,
        "direct_dependencies": theorem.get("derived_direct_vector", {}).get(
            "dependencies"
        ),
        "direct_dependencies_lf_sha256": theorem.get("derived_direct_vector", {}).get(
            "lf_sha256"
        ),
        "fuel": artifact.get("fuel"),
        "metrics": {
            "artifact_bytes": artifact.get("artifact_bytes"),
            **artifact.get("tree_metrics", {}),
        },
        "proof_term_sha256": artifact.get("proof_term_sha256"),
        "surface_basis": "a2.3d-transformed-literal-direct-cut-spine",
    }
    receipt_projection = {
        "artifact_sha256": receipt_theorem.get("candidate_artifact_sha256"),
        "direct_dependencies": receipt_theorem.get("derived_direct_dependencies"),
        "direct_dependencies_lf_sha256": receipt_theorem.get(
            "derived_direct_dependencies_lf_sha256"
        ),
        "fuel": receipt_theorem.get("output_fuel"),
        "metrics": {
            "artifact_bytes": artifact.get("artifact_bytes"),
            **receipt_theorem.get("output_metrics", {}),
        },
        "proof_term_sha256": receipt_theorem.get("output_proof_term_sha256"),
    }
    if any(row[key] != receipt_projection[key] for key in receipt_projection):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d candidate differs from independent reconstruction"
        )
    if row != expected_rows[3]:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d artifact differs from the preregistered candidate row"
        )
    if (
        theorem.get("index") != EXPECTED_INDEX
        or theorem.get("name") != EXPECTED_NAME
        or artifact.get("formula_sha256") != EXPECTED_FORMULA_SHA256
        or receipt_theorem.get("retained_transitive_closure") != list(EXPECTED_CLOSURE)
        or receipt_theorem.get("retained_transitive_closure_lf_sha256")
        != EXPECTED_CLOSURE_LF_SHA256
    ):
        raise LibraryPilotOptimizedConstructionComparisonError(
            "A2.3d theorem identity or closure differs"
        )
    derived.append(deepcopy(row))
    if tuple(item["candidate_id"] for item in derived) != CANDIDATE_IDS:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "fixed candidate order differs"
        )
    return derived


def _record_sha256(value: Mapping[str, object]) -> str:
    return _sha256(
        _compact_bytes(
            {
                "format": THEOREM_RECORD_PREIMAGE_FORMAT,
                "payload": value,
                "v": VERSION,
            }
        )
    )


def _expected_document(root: Path) -> dict[str, object]:
    schema = optimized_construction_comparison_schema()
    inputs = _load_fixed_inputs(root)
    candidates = _derive_candidates(inputs)
    frontier = componentwise_nondominated(candidates)
    frontier_rows = [row for row in candidates if row["candidate_id"] in frontier]
    representative = select_fixed_set_representative(frontier_rows)
    if frontier != EXPECTED_FRONTIER or representative != EXPECTED_REPRESENTATIVE:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "fixed comparison result differs from preregistration"
        )
    cut_liveness = candidates[3]
    deltas = []
    for other in candidates[:3]:
        deltas.append(
            {
                "against_candidate_id": other["candidate_id"],
                "artifact_bytes_delta": cut_liveness["metrics"]["artifact_bytes"]
                - other["metrics"]["artifact_bytes"],
                "cut_nodes_delta": cut_liveness["metrics"]["cut_nodes"]
                - other["metrics"]["cut_nodes"],
                "proof_depth_delta": cut_liveness["metrics"]["proof_depth"]
                - other["metrics"]["proof_depth"],
                "proof_nodes_delta": cut_liveness["metrics"]["proof_nodes"]
                - other["metrics"]["proof_nodes"],
            }
        )
    theorem: dict[str, object] = {
        "candidates": candidates,
        "comparison": {
            "axes_in_componentwise_order": list(COMPARISON_AXES),
            "candidate_universe_complete_for_fixed_scope": True,
            "candidate_universe_ids_in_order": list(CANDIDATE_IDS),
            "claim": "bounded-one-root-four-candidate-fixed-set-only",
            "fixed_set_pareto_frontier_computed": True,
            "fixed_set_representative_selected": True,
            "global_best_claim": False,
            "minimality_claim": False,
            "nondominated_candidate_ids_in_input_order": list(frontier),
            "representative_candidate_id": representative,
            "representative_tie_break": list(REPRESENTATIVE_TIE_BREAK),
        },
        "construction_direct_vector": {
            "dependencies": list(EXPECTED_VECTOR),
            "independently_reproduced": True,
            "lf_sha256": EXPECTED_VECTOR_LF_SHA256,
            "source_candidate_id": "cut-liveness",
            "theorem_scoped_audit_complete": True,
        },
        "fixed_set_deltas_for_cut_liveness": deltas,
        "formula_sha256": EXPECTED_FORMULA_SHA256,
        "index": EXPECTED_INDEX,
        "name": EXPECTED_NAME,
        "transitive_closure": {
            "dependencies_in_replay_order": list(EXPECTED_CLOSURE),
            "lf_sha256": EXPECTED_CLOSURE_LF_SHA256,
        },
    }
    theorem["record_sha256"] = _record_sha256(theorem)
    input_rows = []
    for pin in schema["fixed_inputs"]:
        input_rows.append(deepcopy(pin))
    payload: dict[str, object] = {
        **{name: False for name in FALSE_CLAIMS},
        "aggregate": {
            "candidate_count": 4,
            "construction_direct_dependency_count": 2,
            "nondominated_candidate_count": 2,
            "pilot_theorem_count": 1,
        },
        "construction_direct_vector_independently_reproduced": True,
        "fixed_one_root_candidate_universe_authenticated": True,
        "fixed_set_pareto_frontier_computed": True,
        "fixed_set_representative_selected": True,
        "format": FORMAT,
        "id": DOCUMENT_ID,
        "inputs": input_rows,
        "logic_mode": LOGIC_MODE,
        "schema": optimized_construction_comparison_schema_identity(),
        "status": STATUS,
        "theorem": theorem,
        "theorem_count": 1,
        "theorem_scoped_construction_vector_audit_complete": True,
        "upstream_independent_kernel_receipts_authenticated": True,
        "v": VERSION,
    }
    preimage = {
        "format": ROOT_PREIMAGE_FORMAT,
        "payload": deepcopy(payload),
        "v": VERSION,
    }
    result = {
        **payload,
        "root_preimage": preimage,
        "root_sha256": _sha256(_compact_bytes(preimage)),
    }
    if canonical_document_bytes(result) != canonical_document_bytes(result):
        raise AssertionError("canonical encoding is not deterministic")
    return result


def build_pilot_optimized_construction_comparison(
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Build the exact tactic-free A2.3e fixed-set comparison document."""

    root = _repository_root(repository_root)
    return deepcopy(_expected_document(root))


def validate_pilot_optimized_construction_comparison(
    value: object, *, repository_root: Path | None = None
) -> None:
    """Deeply validate a document against exact authenticated predecessor bytes."""

    if type(value) is not dict:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "comparison document must be one exact object"
        )
    _validate_json(value)
    expected = _expected_document(_repository_root(repository_root))
    if value != expected:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "comparison document differs from exact reconstruction"
        )


def load_pilot_optimized_construction_comparison(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one canonical, bounded comparison document and validate it deeply."""

    raw = _read_regular(path, label="comparison document", limit=MAX_DOCUMENT_BYTES)
    value = _decode_object(raw, label="comparison document")
    if canonical_document_bytes(value) != raw:
        raise LibraryPilotOptimizedConstructionComparisonError(
            "comparison document is not canonical"
        )
    validate_pilot_optimized_construction_comparison(
        value, repository_root=repository_root
    )
    return value


__all__ = [
    "FORMAT",
    "DOCUMENT_ID",
    "LibraryPilotOptimizedConstructionComparisonError",
    "build_pilot_optimized_construction_comparison",
    "canonical_document_bytes",
    "componentwise_nondominated",
    "load_pilot_optimized_construction_comparison",
    "optimized_construction_comparison_schema",
    "optimized_construction_comparison_schema_identity",
    "select_fixed_set_representative",
    "validate_pilot_optimized_construction_comparison",
]
