"""Bounded candidate-only A2.3a optimizer/comparison pilot.

The pilot compares exactly three already-delimited constructions for exactly
three theorem roots: the retained replay artifact, the A2.2 direct-``Cut``
rebuild, and a closure-only construction made by the existing production
``layered_replay`` compiler.  It does not replay tactic scripts or introduce a
new factorer.

Every artifact in the comparison is decoded, canonically re-encoded, and
checked by the unchanged intuitionistic kernel from the empty context against
the original target.  Nondominance is relative only to this three-element
pilot universe.  Nothing in this module admits a theorem, changes a dependency
graph, or grants review, publication, freeze, training, retrieval, evaluation,
minimality, best-known, optimized-vector, or A2 authority.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

from peano_lab.engine.state import proof_identity_metrics
from peano_lab.kernel.artifact_codec import (
    decode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import Cut, ImpIntro, Proof
from peano_lab.kernel.subst import shift_formula, subst_formula
from peano_lab.kernel.terms import Term
from peano_lab.library.layered_replay import (
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayLimits,
    LayeredReplayNode,
    compile_layered_replay,
)

from .library_replay_pack import proof_tree_metrics


OPTIMIZER_COMPARISON_PILOT_SCHEMA_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-schema"
)
OPTIMIZER_COMPARISON_PILOT_SCHEMA_VERSION = 1
OPTIMIZER_COMPARISON_PILOT_SCHEMA_ID = (
    "peano-hydra-library-optimizer-comparison-pilot-v1"
)
OPTIMIZER_COMPARISON_PILOT_SCHEMA_PATH = Path(__file__).with_name(
    "library-optimizer-comparison-pilot-schema-v1.json"
)
# This pin is intentionally updated only after schema review.
OPTIMIZER_COMPARISON_PILOT_SCHEMA_SHA256 = (
    "07e5842c221fe84337e163ce5c858ab03dfbbc93d1477f5661edfdd6f8ba3978"
)

OPTIMIZER_COMPARISON_PILOT_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot"
)
OPTIMIZER_COMPARISON_PILOT_VERSION = 1
OPTIMIZER_COMPARISON_PILOT_ID = (
    "authoring-l0-optimizer-comparison-pilot-candidate-v1"
)
OPTIMIZER_COMPARISON_PILOT_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-root-preimage"
)
THEOREM_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-records-preimage"
)
STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
CERTIFICATE_REPRESENTATION = "peano-lab-v2"

MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_ARTIFACT_BYTES = 8_000_000
MAX_JSON_DEPTH = 256
MAX_JSON_ITEMS = 4_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
THEOREM_COUNT = 3
RETAINED_PUBLIC_GRAPH_EDGES = 1_038
PILOT_BODY_UNION_COUNT = 127
PILOT_BODY_UNION_DIRECT_EDGES = 328
PILOT_BODY_UNION_PROOF_NODES = 7_365
PILOT_BODY_MAX_PROOF_NODES = 373
PILOT_BUNDLE_NODE_COUNTS = {
    "odd_add_odd": 6,
    "finite_bounded_injective_surjective": 120,
    "beta_product_swap_last_invariant": 32,
}

_REGISTERED_LAYERED_LIMITS = LayeredReplayLimits(
    max_nodes=4_096,
    max_dependencies_per_node=256,
    max_dependency_edges=65_536,
    max_formula_occurrences_per_target=100_000,
    max_total_formula_occurrences=500_000,
    max_formula_depth=256,
    max_body_occurrences=500_000,
    max_body_objects=100_000,
    max_body_depth=256,
    max_body_annotation_occurrences=500_000,
    max_body_envelope_depth=256,
    max_total_body_occurrences=5_000_000,
    max_total_body_objects=500_000,
    max_total_body_annotation_occurrences=5_000_000,
    max_package_formula_occurrences=500_000,
    max_package_formula_depth=256,
    max_candidate_proof_occurrences=500_000,
    max_candidate_proof_objects=100_000,
    max_candidate_proof_depth=256,
    max_candidate_annotation_occurrences=5_000_000,
    max_candidate_envelope_depth=256,
)
PILOT_LAYERED_LIMITS = _REGISTERED_LAYERED_LIMITS

COMPARISON_AXES = (
    "artifact_bytes",
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
)
CANDIDATE_KINDS = (
    ("retained-replay", 0),
    ("a2.2-direct-cut-rebuild", 1),
    ("layered-closure", 2),
)
SURFACE_BASES = {
    "retained-replay": "retained-manifest-literal-direct-cut-spine",
    "a2.2-direct-cut-rebuild": "a2.2-rebuilt-literal-direct-cut-spine",
    "layered-closure": (
        "modular-input-graph-not-literal-final-certificate-cut-spine"
    ),
}

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_AUDIT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
)
_REBUILD_RELATIVE = Path(
    "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
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
REBUILD_ARTIFACT_SHA256 = (
    "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182"
)
REBUILD_ROOT_SHA256 = (
    "91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0"
)
REBUILD_THEOREM_RECORD_ROOT_SHA256 = (
    "42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5"
)
REBUILD_SCHEMA_ARTIFACT_SHA256 = (
    "d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f"
)
REBUILD_SCHEMA_SEMANTIC_SHA256 = (
    "a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571"
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

_PINNED_IMPLEMENTATION = (
    (
        "peano_lab.library.layered_replay",
        Path("peano-lab/py/peano_lab/library/layered_replay.py"),
        "ad4421446336b7c8c0db9f12298a5aa66718dfeac76282ab91bf0db3ce00f4c4",
    ),
    (
        "peano_lab.kernel.checker",
        Path("peano-lab/py/peano_lab/kernel/checker.py"),
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        "peano_lab.kernel.artifact_codec",
        Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        "training.peano_hydra.library_replay_pack",
        Path("training/peano_hydra/library_replay_pack.py"),
        "8c5f3b44bed64bc3a49a7990d16a6f3c4a966b14c2bf4c732227041bc81506ee",
    ),
    (
        "peano_lab.kernel.proofs",
        Path("peano-lab/py/peano_lab/kernel/proofs.py"),
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    ),
    (
        "peano_lab.kernel.formulas",
        Path("peano-lab/py/peano_lab/kernel/formulas.py"),
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        "peano_lab.engine.state",
        Path("peano-lab/py/peano_lab/engine/state.py"),
        "453904142273f14d01379c73c637be3476d035b093047587ff6990f1d572ac2f",
    ),
    (
        "peano_lab.kernel.terms",
        Path("peano-lab/py/peano_lab/kernel/terms.py"),
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
    ),
    (
        "peano_lab.kernel.subst",
        Path("peano-lab/py/peano_lab/kernel/subst.py"),
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    ),
)

_EXPECTED = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA1_RE = re.compile(r"[0-9a-f]{40}")
PRODUCER_SOURCE_STATE_FORMAT = "peano-hydra-producer-source-state"
PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-producer-source-state-root-preimage"
)
PRODUCER_SOURCE_FILES = (
    Path("training/peano_hydra/library-optimizer-comparison-pilot-schema-v1.json"),
    Path("training/peano_hydra/library_optimizer_comparison_pilot.py"),
    Path("scripts/build_peano_hydra_library_optimizer_comparison_pilot.py"),
    Path("peano-lab/py/tests/test_peano_hydra_library_optimizer_comparison_pilot.py"),
)


class LibraryOptimizerComparisonPilotError(ValueError):
    """A pilot input, modular body, comparison, or artifact is invalid."""


@dataclass(frozen=True, slots=True)
class RecoveredModularBody:
    """One checked dependency-curried body recovered from a closed artifact."""

    target: Formula
    dependencies: tuple[str, ...]
    curried_target: Formula
    body: Proof
    receipt: dict[str, object]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


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
        raise LibraryOptimizerComparisonPilotError(
            f"{path} exceeds the JSON depth limit"
        )
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryOptimizerComparisonPilotError(
                f"{path} exceeds the JSON integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise LibraryOptimizerComparisonPilotError(
                f"{path} contains a Unicode surrogate"
            ) from None
        return 1
    if type(value) not in (list, dict):
        raise LibraryOptimizerComparisonPilotError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryOptimizerComparisonPilotError(f"{path} contains a cycle")
    if len(value) > MAX_JSON_ITEMS:
        raise LibraryOptimizerComparisonPilotError(f"{path} has too many items")
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
                raise LibraryOptimizerComparisonPilotError(
                    "JSON document has too many items"
                )
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryOptimizerComparisonPilotError(
                f"{path} contains a non-string key"
            )
        _validate_json(
            key, path=f"{path}.<key>", depth=depth + 1, ancestors=descendants
        )
        count += _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=descendants,
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryOptimizerComparisonPilotError(
                "JSON document has too many items"
            )
    return count


def _compact_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> bytes:
    _validate_json(value)
    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LibraryOptimizerComparisonPilotError(
            "cannot encode canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryOptimizerComparisonPilotError(
            "canonical JSON exceeds its byte limit"
        )
    return raw


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256_bytes(_compact_json(value, limit=limit))


def canonical_document_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return the one canonical retained JSON representation."""

    _validate_json(value)
    try:
        raw = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LibraryOptimizerComparisonPilotError(
            "cannot encode canonical document"
        ) from exc
    if len(raw) > limit:
        raise LibraryOptimizerComparisonPilotError(
            "canonical document exceeds its byte limit"
        )
    return raw


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if len(raw) > limit:
        raise LibraryOptimizerComparisonPilotError(f"{label} exceeds its byte limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryOptimizerComparisonPilotError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryOptimizerComparisonPilotError(f"{label} must be one object")
    _validate_json(value)
    return value


def _safe_file(path: Path, *, label: str, limit: int) -> bytes:
    try:
        absolute = Path(os.path.abspath(path))
        current = Path(absolute.anchor)
        for component in absolute.parent.parts[1:]:
            current = current / component
            parent_metadata = current.lstat()
            if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(
                parent_metadata.st_mode
            ):
                raise LibraryOptimizerComparisonPilotError(
                    f"{label} parent contains a link or non-directory component"
                )
        metadata = path.lstat()
    except OSError as exc:
        raise LibraryOptimizerComparisonPilotError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryOptimizerComparisonPilotError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryOptimizerComparisonPilotError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryOptimizerComparisonPilotError(
                f"{label} is not a bounded regular file"
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
        if len(raw) > limit:
            raise LibraryOptimizerComparisonPilotError(f"{label} exceeds its byte limit")
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
            raise LibraryOptimizerComparisonPilotError(f"{label} changed while read")
        return raw
    except OSError as exc:
        raise LibraryOptimizerComparisonPilotError(f"cannot read {label}") from exc
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
        raise LibraryOptimizerComparisonPilotError(
            "cannot resolve repository_root"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise LibraryOptimizerComparisonPilotError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def _validate_producer_source_state(
    value: object, *, root: Path
) -> dict[str, object]:
    """Validate the explicit protocol-commit source state against live bytes.

    Git ancestry/tree/cleanliness is deliberately not asserted here.  The
    later successor receipt owns that domain-separated check, so this state
    must carry ``git_verified = false``.
    """

    if type(value) is not dict or set(value) != {
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    }:
        raise LibraryOptimizerComparisonPilotError(
            "producer source state has the wrong fields"
        )
    if (
        value.get("format") != PRODUCER_SOURCE_STATE_FORMAT
        or value.get("v") != 1
        or value.get("git_verified") is not False
        or _GIT_SHA1_RE.fullmatch(str(value.get("commit_sha1"))) is None
        or _GIT_SHA1_RE.fullmatch(str(value.get("tree_sha1"))) is None
    ):
        raise LibraryOptimizerComparisonPilotError(
            "producer source state identity is malformed"
        )
    files = value.get("files")
    if type(files) is not list or len(files) != len(PRODUCER_SOURCE_FILES):
        raise LibraryOptimizerComparisonPilotError(
            "producer source file list is malformed"
        )
    for expected, row in zip(PRODUCER_SOURCE_FILES, files, strict=True):
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise LibraryOptimizerComparisonPilotError(
                "producer source file row is malformed"
            )
        if (
            row.get("path") != expected.as_posix()
            or type(row.get("bytes")) is not int
            or row["bytes"] <= 0
            or type(row.get("sha256")) is not str
            or _SHA256_RE.fullmatch(row["sha256"]) is None
        ):
            raise LibraryOptimizerComparisonPilotError(
                "producer source file identity is malformed"
            )
        raw = _safe_file(
            root / expected,
            label=f"producer source {expected.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != row["bytes"] or _sha256_bytes(raw) != row["sha256"]:
            raise LibraryOptimizerComparisonPilotError(
                f"producer source {expected.as_posix()!r} differs from live bytes"
            )
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    expected_preimage = {
        "format": PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    if value.get("root_preimage") != expected_preimage or value.get(
        "root_sha256"
    ) != _sha256_json(expected_preimage, limit=MAX_SCHEMA_BYTES):
        raise LibraryOptimizerComparisonPilotError(
            "producer source-state root is malformed"
        )
    return deepcopy(value)


def optimizer_comparison_pilot_schema() -> dict[str, object]:
    """Load and validate the candidate-only A2.3a pilot schema."""

    raw = _safe_file(
        OPTIMIZER_COMPARISON_PILOT_SCHEMA_PATH,
        label="optimizer/comparison pilot schema",
        limit=MAX_SCHEMA_BYTES,
    )
    value = _decode_document(
        raw, "optimizer/comparison pilot schema", limit=MAX_SCHEMA_BYTES
    )
    if canonical_document_bytes(value, limit=MAX_SCHEMA_BYTES) != raw:
        raise LibraryOptimizerComparisonPilotError(
            "optimizer/comparison pilot schema is not canonical"
        )
    if (
        _sha256_json(value, limit=MAX_SCHEMA_BYTES)
        != OPTIMIZER_COMPARISON_PILOT_SCHEMA_SHA256
    ):
        raise LibraryOptimizerComparisonPilotError(
            "optimizer/comparison pilot schema semantic digest drifted"
        )
    if (
        value.get("format") != OPTIMIZER_COMPARISON_PILOT_SCHEMA_FORMAT
        or value.get("id") != OPTIMIZER_COMPARISON_PILOT_SCHEMA_ID
        or value.get("v") != OPTIMIZER_COMPARISON_PILOT_SCHEMA_VERSION
    ):
        raise LibraryOptimizerComparisonPilotError(
            "optimizer/comparison pilot schema identity drifted"
        )
    return deepcopy(value)


def optimizer_comparison_pilot_schema_identity() -> dict[str, object]:
    schema = optimizer_comparison_pilot_schema()
    raw = canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "format": OPTIMIZER_COMPARISON_PILOT_SCHEMA_FORMAT,
        "id": OPTIMIZER_COMPARISON_PILOT_SCHEMA_ID,
        "sha256": OPTIMIZER_COMPARISON_PILOT_SCHEMA_SHA256,
        "v": OPTIMIZER_COMPARISON_PILOT_SCHEMA_VERSION,
    }


def _require_module_origin(module_name: str, expected: Path) -> object:
    module = importlib.import_module(module_name)
    source = getattr(module, "__file__", None)
    if type(source) is not str:
        raise LibraryOptimizerComparisonPilotError(
            f"cannot identify module {module_name!r}"
        )
    try:
        actual = Path(source).resolve(strict=True)
        wanted = expected.resolve(strict=True)
    except OSError as exc:
        raise LibraryOptimizerComparisonPilotError(
            f"cannot resolve module {module_name!r}"
        ) from exc
    if actual != wanted:
        raise LibraryOptimizerComparisonPilotError(
            f"module {module_name!r} origin drifted"
        )
    return module


def _require_implementation(root: Path) -> None:
    if (
        type(PILOT_LAYERED_LIMITS) is not LayeredReplayLimits
        or PILOT_LAYERED_LIMITS != _REGISTERED_LAYERED_LIMITS
    ):
        raise LibraryOptimizerComparisonPilotError(
            "layered replay resource limit drifted"
        )
    modules: dict[str, object] = {}
    for module_name, relative, digest in _PINNED_IMPLEMENTATION:
        raw = _safe_file(
            root / relative,
            label=f"implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryOptimizerComparisonPilotError(
                f"implementation source {relative.as_posix()!r} drifted"
            )
        modules[module_name] = _require_module_origin(module_name, root / relative)

    layered = modules["peano_lab.library.layered_replay"]
    checker = modules["peano_lab.kernel.checker"]
    codec = modules["peano_lab.kernel.artifact_codec"]
    replay_metrics = modules["training.peano_hydra.library_replay_pack"]
    proofs = modules["peano_lab.kernel.proofs"]
    formulas = modules["peano_lab.kernel.formulas"]
    state = modules["peano_lab.engine.state"]
    terms = modules["peano_lab.kernel.terms"]
    subst = modules["peano_lab.kernel.subst"]
    if (
        getattr(layered, "LayeredReplayBundle", None) is not LayeredReplayBundle
        or getattr(layered, "LayeredReplayCandidate", None)
        is not LayeredReplayCandidate
        or getattr(layered, "LayeredReplayLimits", None) is not LayeredReplayLimits
        or getattr(layered, "LayeredReplayNode", None) is not LayeredReplayNode
        or getattr(layered, "compile_layered_replay", None)
        is not compile_layered_replay
        or getattr(checker, "check", None) is not check
        or getattr(codec, "decode_artifact", None) is not decode_artifact
        or getattr(codec, "encode_artifact_bounded", None)
        is not encode_artifact_bounded
        or getattr(codec, "encode_formula", None) is not encode_formula
        or getattr(codec, "encode_proof", None) is not encode_proof
        or getattr(replay_metrics, "proof_tree_metrics", None)
        is not proof_tree_metrics
        or getattr(proofs, "Cut", None) is not Cut
        or getattr(proofs, "ImpIntro", None) is not ImpIntro
        or getattr(proofs, "Proof", None) is not Proof
        or getattr(formulas, "Formula", None) is not Formula
        or getattr(formulas, "Imp", None) is not Imp
        or getattr(state, "proof_identity_metrics", None)
        is not proof_identity_metrics
        or getattr(layered, "proof_identity_metrics", None)
        is not proof_identity_metrics
        or getattr(terms, "Term", None) is not Term
        or getattr(subst, "shift_formula", None) is not shift_formula
        or getattr(subst, "subst_formula", None) is not subst_formula
        or getattr(checker, "shift_formula", None) is not shift_formula
        or getattr(checker, "subst_formula", None) is not subst_formula
    ):
        raise LibraryOptimizerComparisonPilotError(
            "optimizer/comparison runtime callable drifted"
        )


def _rows_by_name(
    document: Mapping[str, object], label: str, *, expected_count: int
) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list or len(rows) != expected_count:
        raise LibraryOptimizerComparisonPilotError(
            f"{label} theorem rows are malformed"
        )
    result: dict[str, dict[str, object]] = {}
    last_index = -1
    for row in rows:
        if (
            type(row) is not dict
            or type(row.get("name")) is not str
            or type(row.get("index")) is not int
            or row["index"] <= last_index
            or row["name"] in result
        ):
            raise LibraryOptimizerComparisonPilotError(
                f"{label} theorem order is malformed"
            )
        last_index = row["index"]
        result[row["name"]] = row
    return result


def _load_fixed_inputs(
    root: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    _require_implementation(root)
    audit_raw = _safe_file(root / _AUDIT_RELATIVE, label="A2.1 audit", limit=8_000_000)
    rebuild_raw = _safe_file(
        root / _REBUILD_RELATIVE, label="A2.2 construction rebuild", limit=8_000_000
    )
    manifest_raw = _safe_file(
        root / _REPLAY_MANIFEST_RELATIVE,
        label="replay manifest",
        limit=8_000_000,
    )
    report_raw = _safe_file(
        root / _REPLAY_REPORT_RELATIVE, label="replay report", limit=8_000_000
    )
    if _sha256_bytes(audit_raw) != AUDIT_ARTIFACT_SHA256:
        raise LibraryOptimizerComparisonPilotError("A2.1 audit artifact drifted")
    if _sha256_bytes(rebuild_raw) != REBUILD_ARTIFACT_SHA256:
        raise LibraryOptimizerComparisonPilotError("A2.2 rebuild artifact drifted")
    if _sha256_bytes(manifest_raw) != REPLAY_MANIFEST_ARTIFACT_SHA256:
        raise LibraryOptimizerComparisonPilotError("replay manifest artifact drifted")
    if _sha256_bytes(report_raw) != REPLAY_REPORT_ARTIFACT_SHA256:
        raise LibraryOptimizerComparisonPilotError("replay report artifact drifted")

    audit = _decode_document(audit_raw, "A2.1 audit", limit=8_000_000)
    rebuild = _decode_document(rebuild_raw, "A2.2 rebuild", limit=8_000_000)
    manifest = _decode_document(manifest_raw, "replay manifest", limit=8_000_000)
    if (
        audit.get("root_sha256") != AUDIT_ROOT_SHA256
        or audit.get("theorem_count") != 384
        or audit.get("theorem_records", {}).get("root_sha256")
        != AUDIT_THEOREM_RECORD_ROOT_SHA256
        or audit.get("schema", {}).get("artifact_sha256")
        != AUDIT_SCHEMA_ARTIFACT_SHA256
        or audit.get("schema", {}).get("sha256")
        != AUDIT_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryOptimizerComparisonPilotError("A2.1 audit identity drifted")
    if (
        rebuild.get("root_sha256") != REBUILD_ROOT_SHA256
        or rebuild.get("theorem_count") != THEOREM_COUNT
        or rebuild.get("theorem_records", {}).get("root_sha256")
        != REBUILD_THEOREM_RECORD_ROOT_SHA256
        or rebuild.get("schema", {}).get("artifact_sha256")
        != REBUILD_SCHEMA_ARTIFACT_SHA256
        or rebuild.get("schema", {}).get("sha256")
        != REBUILD_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryOptimizerComparisonPilotError("A2.2 rebuild identity drifted")
    if (
        manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != 384
    ):
        raise LibraryOptimizerComparisonPilotError("replay manifest identity drifted")

    kernel_identity = manifest.get("kernel_identity")
    if type(kernel_identity) is not dict or type(kernel_identity.get("sources")) is not list:
        raise LibraryOptimizerComparisonPilotError(
            "replay kernel source identity is malformed"
        )
    kernel_sources = kernel_identity["sources"]
    if kernel_identity.get("source_root_sha256") != _sha256_json(
        kernel_sources, limit=MAX_SCHEMA_BYTES
    ):
        raise LibraryOptimizerComparisonPilotError(
            "replay kernel source root drifted"
        )
    for source in kernel_sources:
        if type(source) is not dict:
            raise LibraryOptimizerComparisonPilotError(
                "replay kernel source row is malformed"
            )
        relative = source.get("path")
        digest = source.get("sha256")
        if (
            type(relative) is not str
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or _SHA256_RE.fullmatch(str(digest)) is None
        ):
            raise LibraryOptimizerComparisonPilotError(
                "replay kernel source identity is malformed"
            )
        raw = _safe_file(
            root / relative,
            label=f"replay kernel source {relative!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryOptimizerComparisonPilotError(
                f"replay kernel source {relative!r} drifted"
            )

    compiler = audit.get("inputs", {}).get("compiler")
    if type(compiler) is not dict or type(compiler.get("sources")) is not list:
        raise LibraryOptimizerComparisonPilotError(
            "A2.1 compiler source identity is malformed"
        )
    pinned_sources: list[Mapping[str, object]] = list(compiler["sources"])
    construction_core = rebuild.get("inputs", {}).get("construction_core")
    replay_metric_source = rebuild.get("inputs", {}).get(
        "replay_tree_metric_source"
    )
    if type(construction_core) is not dict or type(replay_metric_source) is not dict:
        raise LibraryOptimizerComparisonPilotError(
            "A2.2 compiler source identity is malformed"
        )
    pinned_sources.extend((construction_core, replay_metric_source))
    for source in pinned_sources:
        relative = source.get("path")
        digest = source.get("sha256")
        if (
            type(relative) is not str
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or _SHA256_RE.fullmatch(str(digest)) is None
        ):
            raise LibraryOptimizerComparisonPilotError(
                "upstream compiler source identity is malformed"
            )
        raw = _safe_file(
            root / relative,
            label=f"upstream compiler source {relative!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryOptimizerComparisonPilotError(
                f"upstream compiler source {relative!r} drifted"
            )
    audit_rows = _rows_by_name(audit, "A2.1 audit", expected_count=384)
    rebuild_rows = _rows_by_name(
        rebuild, "A2.2 construction rebuild", expected_count=THEOREM_COUNT
    )
    replay_rows = _rows_by_name(manifest, "replay manifest", expected_count=384)
    if tuple((row["index"], row["name"]) for row in rebuild["theorems"]) != _EXPECTED:
        raise LibraryOptimizerComparisonPilotError("A2.2 pilot roots drifted")
    return audit, rebuild, manifest, audit_rows, rebuild_rows, replay_rows


def _stable_body_receipt(
    *, dependencies: tuple[str, ...], target: Formula, body: Proof
) -> dict[str, object]:
    tree = proof_tree_metrics(body)
    return {
        "certificate_representation": "peano-lab-v2-encoded-proof",
        "certificate_sha256": _sha256_bytes(encode_proof(body)),
        "dependency_count": len(dependencies),
        "kernel_accepted": True,
        "proof_depth": tree["proof_depth"],
        "proof_nodes": tree["proof_nodes"],
        "target_formula_sha256": _sha256_bytes(encode_formula(target)),
    }


def _validate_expected_body_receipt(
    expected: Mapping[str, object], actual: Mapping[str, object]
) -> None:
    if type(expected) is not dict or set(expected) != {
        "certificate_representation",
        "certificate_sha256",
        "dependency_count",
        "kernel_accepted",
        "metrics",
        "receipt_sha256",
        "target_formula_sha256",
    }:
        raise LibraryOptimizerComparisonPilotError("body receipt must be one object")
    if _sha256_json({k: v for k, v in expected.items() if k != "receipt_sha256"}) != expected.get(
        "receipt_sha256"
    ):
        raise LibraryOptimizerComparisonPilotError("body receipt hash drifted")
    metrics = expected.get("metrics")
    if type(metrics) is not dict or set(metrics) != {
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "proof_objects",
        "reused_objects",
    }:
        raise LibraryOptimizerComparisonPilotError("body receipt metrics are malformed")
    if (
        expected.get("certificate_representation")
        != "peano-lab-v2-encoded-proof"
        or type(expected.get("certificate_sha256")) is not str
        or _SHA256_RE.fullmatch(expected["certificate_sha256"]) is None
        or type(expected.get("target_formula_sha256")) is not str
        or _SHA256_RE.fullmatch(expected["target_formula_sha256"]) is None
        or type(expected.get("receipt_sha256")) is not str
        or _SHA256_RE.fullmatch(expected["receipt_sha256"]) is None
        or type(expected.get("dependency_count")) is not int
        or expected["dependency_count"] < 0
        or expected.get("kernel_accepted") is not True
        or any(type(metrics.get(key)) is not int for key in metrics)
        or metrics["proof_nodes"] <= 0
        or metrics["proof_depth"] <= 0
        or metrics["proof_objects"] <= 0
        or metrics["proof_edges"] < 0
        or metrics["reused_objects"] < 0
        or metrics["proof_objects"] > metrics["proof_nodes"]
        or metrics["proof_edges"] < metrics["proof_objects"] - 1
        or metrics["reused_objects"]
        != metrics["proof_edges"] - (metrics["proof_objects"] - 1)
    ):
        raise LibraryOptimizerComparisonPilotError("body receipt domain is malformed")
    for key in (
        "certificate_representation",
        "certificate_sha256",
        "dependency_count",
        "kernel_accepted",
        "target_formula_sha256",
    ):
        if expected.get(key) != actual[key]:
            raise LibraryOptimizerComparisonPilotError(
                f"recovered body differs from its pinned {key} receipt"
            )
    if (
        metrics.get("proof_nodes") != actual["proof_nodes"]
        or metrics.get("proof_depth") != actual["proof_depth"]
    ):
        raise LibraryOptimizerComparisonPilotError(
            "recovered body differs from its stable tree metrics"
        )


def recover_curried_modular_body(
    *,
    name: str,
    target: Formula,
    proof: Proof,
    dependencies: tuple[str, ...],
    dependency_targets: Mapping[str, Formula],
    dependency_proof_sha256: Mapping[str, str],
    expected_body_receipt: Mapping[str, object],
) -> RecoveredModularBody:
    """Verify/peel an exact outer direct-Cut spine and re-curry its body."""

    if type(name) is not str or not name:
        raise LibraryOptimizerComparisonPilotError("modular body name is malformed")
    if not isinstance(target, Formula) or not isinstance(proof, Proof):
        raise LibraryOptimizerComparisonPilotError("modular body syntax is malformed")
    if (
        type(dependencies) is not tuple
        or not all(type(item) is str and item for item in dependencies)
        or len(set(dependencies)) != len(dependencies)
    ):
        raise LibraryOptimizerComparisonPilotError(
            "modular body dependencies are malformed"
        )
    if set(dependency_targets) != set(dependencies) or set(
        dependency_proof_sha256
    ) != set(dependencies):
        raise LibraryOptimizerComparisonPilotError(
            "direct dependency evidence differs from the exact vector"
        )
    if not check((), proof, target):
        raise LibraryOptimizerComparisonPilotError(
            f"closed artifact for {name!r} failed the empty-context kernel check"
        )

    cursor = proof
    for dependency in dependencies:
        expected_target = dependency_targets[dependency]
        expected_sha256 = dependency_proof_sha256[dependency]
        if not isinstance(expected_target, Formula):
            raise LibraryOptimizerComparisonPilotError(
                f"direct dependency target is malformed for {dependency!r}"
            )
        if type(cursor) is not Cut:
            raise LibraryOptimizerComparisonPilotError(
                f"direct Cut spine is missing at dependency {dependency!r}"
            )
        if cursor.proposition != expected_target:
            raise LibraryOptimizerComparisonPilotError(
                f"direct Cut proposition drifted at dependency {dependency!r}"
            )
        if cursor.conclusion != target:
            raise LibraryOptimizerComparisonPilotError(
                f"direct Cut conclusion drifted at dependency {dependency!r}"
            )
        if (
            _SHA256_RE.fullmatch(str(expected_sha256)) is None
            or _sha256_bytes(encode_proof(cursor.lemma)) != expected_sha256
        ):
            raise LibraryOptimizerComparisonPilotError(
                f"direct Cut lemma hash drifted at dependency {dependency!r}"
            )
        if not check((), cursor.lemma, expected_target):
            raise LibraryOptimizerComparisonPilotError(
                f"direct Cut lemma failed the kernel at dependency {dependency!r}"
            )
        cursor = cursor.body

    curried_target = target
    curried_body = cursor
    for dependency in reversed(dependencies):
        curried_target = Imp(dependency_targets[dependency], curried_target)
        curried_body = ImpIntro(curried_body)
    if not check((), curried_body, curried_target):
        raise LibraryOptimizerComparisonPilotError(
            f"recovered body for {name!r} failed dependency-curried check"
        )
    receipt = _stable_body_receipt(
        dependencies=dependencies, target=curried_target, body=curried_body
    )
    _validate_expected_body_receipt(expected_body_receipt, receipt)
    return RecoveredModularBody(
        target=target,
        dependencies=dependencies,
        curried_target=curried_target,
        body=curried_body,
        # The exact source receipt is preserved, including its explicitly
        # non-transportable Python alias metrics.  Only the stable subset was
        # compared above because decoding intentionally erases object sharing.
        receipt=deepcopy(dict(expected_body_receipt)),
    )


def _comparison_record(candidate: Mapping[str, object]) -> tuple[str, int, str, dict[str, int]]:
    if type(candidate) is not dict:
        raise LibraryOptimizerComparisonPilotError("candidate must be one exact object")
    candidate_id = candidate.get("candidate_id")
    kind_order = candidate.get("candidate_kind_order")
    digest = candidate.get("artifact_sha256")
    metrics = candidate.get("metrics")
    if (
        type(candidate_id) is not str
        or not candidate_id
        or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", candidate_id) is None
        or type(kind_order) is not int
        or kind_order < 0
        or type(digest) is not str
        or _SHA256_RE.fullmatch(digest) is None
        or type(metrics) is not dict
        or set(metrics) != set(COMPARISON_AXES)
        or type(metrics["artifact_bytes"]) is not int
        or metrics["artifact_bytes"] <= 0
        or type(metrics["proof_nodes"]) is not int
        or metrics["proof_nodes"] <= 0
        or type(metrics["proof_depth"]) is not int
        or metrics["proof_depth"] <= 0
        or type(metrics["cut_nodes"]) is not int
        or metrics["cut_nodes"] < 0
    ):
        raise LibraryOptimizerComparisonPilotError("candidate comparison record is malformed")
    return candidate_id, kind_order, str(digest), metrics


def componentwise_nondominated(
    candidates: tuple[Mapping[str, object], ...]
) -> tuple[str, ...]:
    """Return input-ordered IDs not dominated on the four registered axes."""

    if type(candidates) is not tuple or not candidates:
        raise LibraryOptimizerComparisonPilotError(
            "comparison candidates must be a non-empty tuple"
        )
    parsed = tuple(_comparison_record(candidate) for candidate in candidates)
    ids = [item[0] for item in parsed]
    orders = [item[1] for item in parsed]
    if len(set(ids)) != len(ids) or len(set(orders)) != len(orders):
        raise LibraryOptimizerComparisonPilotError(
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


def select_pilot_representative(
    candidates: tuple[Mapping[str, object], ...]
) -> str:
    """Select the preregistered deterministic pilot representative."""

    if type(candidates) is not tuple or not candidates:
        raise LibraryOptimizerComparisonPilotError(
            "comparison candidates must be a non-empty tuple"
        )
    parsed = tuple(_comparison_record(candidate) for candidate in candidates)
    if (
        len({item[0] for item in parsed}) != len(parsed)
        or len({item[1] for item in parsed}) != len(parsed)
    ):
        raise LibraryOptimizerComparisonPilotError(
            "candidate IDs and kind orders must be unique"
        )
    return min(
        parsed,
        key=lambda item: (
            item[3]["proof_nodes"],
            item[3]["proof_depth"],
            item[3]["cut_nodes"],
            item[3]["artifact_bytes"],
            item[1],
            item[2],
            item[0],
        ),
    )[0]


def _decode_replay_artifact(
    root: Path, row: Mapping[str, object]
) -> tuple[bytes, int, Formula, Proof]:
    artifact = row.get("artifact")
    name = row.get("name")
    if type(artifact) is not dict or type(name) is not str:
        raise LibraryOptimizerComparisonPilotError("replay artifact row is malformed")
    relative = artifact.get("path")
    if (
        type(relative) is not str
        or Path(relative).is_absolute()
        or Path(relative).parts[:1] != ("certificates",)
        or ".." in Path(relative).parts
    ):
        raise LibraryOptimizerComparisonPilotError("replay artifact path is unsafe")
    raw = _safe_file(
        root / _REPLAY_ROOT_RELATIVE / relative,
        label=f"replay certificate {name!r}",
        limit=MAX_ARTIFACT_BYTES,
    )
    if len(raw) != artifact.get("bytes") or _sha256_bytes(raw) != artifact.get("sha256"):
        raise LibraryOptimizerComparisonPilotError(
            f"replay certificate {name!r} identity drifted"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw, max_bytes=MAX_ARTIFACT_BYTES, max_nodes=1_000_000, max_depth=512
        )
    except Exception as exc:
        raise LibraryOptimizerComparisonPilotError(
            f"cannot decode replay certificate {name!r}"
        ) from exc
    if (
        fuel != artifact.get("fuel")
        or _sha256_bytes(encode_formula(target)) != row.get("formula_sha256")
        or _sha256_bytes(encode_proof(proof)) != row.get("proof_term_sha256")
        or encode_artifact_bounded(fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES) != raw
        or proof_tree_metrics(proof) != row.get("packed_tree_metrics")
        or not check((), proof, target)
    ):
        raise LibraryOptimizerComparisonPilotError(
            f"replay certificate {name!r} failed exact replay"
        )
    return raw, fuel, target, proof


def _decode_rebuild_artifact(
    row: Mapping[str, object], *, replay_row: Mapping[str, object]
) -> tuple[bytes, int, Formula, Proof]:
    artifact = row.get("rebuilt_certificate")
    name = row.get("name")
    if type(artifact) is not dict or type(name) is not str:
        raise LibraryOptimizerComparisonPilotError("A2.2 artifact row is malformed")
    encoded = artifact.get("artifact_base64")
    if type(encoded) is not str:
        raise LibraryOptimizerComparisonPilotError("A2.2 artifact payload is malformed")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise LibraryOptimizerComparisonPilotError("A2.2 artifact base64 is malformed") from exc
    if (
        base64.b64encode(raw).decode("ascii") != encoded
        or len(raw) != artifact.get("artifact_bytes")
        or _sha256_bytes(raw) != artifact.get("artifact_sha256")
    ):
        raise LibraryOptimizerComparisonPilotError("A2.2 artifact identity drifted")
    try:
        fuel, target, proof = decode_artifact(
            raw, max_bytes=MAX_ARTIFACT_BYTES, max_nodes=1_000_000, max_depth=512
        )
    except Exception as exc:
        raise LibraryOptimizerComparisonPilotError("cannot decode A2.2 artifact") from exc
    if (
        fuel != artifact.get("fuel")
        or _sha256_bytes(encode_formula(target)) != replay_row.get("formula_sha256")
        or _sha256_bytes(encode_proof(proof)) != artifact.get("proof_term_sha256")
        or encode_artifact_bounded(fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES) != raw
        or proof_tree_metrics(proof) != artifact.get("packed_tree_metrics")
        or not check((), proof, target)
    ):
        raise LibraryOptimizerComparisonPilotError("A2.2 artifact failed exact replay")
    return raw, fuel, target, proof


def _closure(
    root_name: str,
    *,
    replay_rows: Mapping[str, dict[str, object]],
    overrides: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    seen: set[str] = set()
    pending = list(overrides.get(root_name, tuple(replay_rows[root_name]["declared_dependencies"])))
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = replay_rows.get(name)
        if row is None:
            raise LibraryOptimizerComparisonPilotError(
                f"dependency closure has unknown theorem {name!r}"
            )
        dependencies = overrides.get(name, tuple(row.get("declared_dependencies", ())))
        if (
            type(dependencies) is not tuple
            or not all(type(item) is str for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise LibraryOptimizerComparisonPilotError("dependency vector is malformed")
        seen.add(name)
        pending.extend(dependencies)
    if root_name in seen:
        raise LibraryOptimizerComparisonPilotError("dependency closure contains its root")
    return tuple(sorted(seen, key=lambda name: replay_rows[name]["index"]))


def _surface(
    dependencies: tuple[str, ...],
    closure: tuple[str, ...],
    *,
    surface_basis: str,
) -> dict[str, object]:
    if surface_basis not in SURFACE_BASES.values():
        raise LibraryOptimizerComparisonPilotError(
            "dependency surface basis is not registered"
        )
    return {
        "direct_dependency_count": len(dependencies),
        "direct_dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": _sha256_bytes(
            ("\n".join(dependencies) + ("\n" if dependencies else "")).encode("utf-8")
        ),
        "surface_basis": surface_basis,
        "transitive_closure_count": len(closure),
        "transitive_closure_dependencies_in_replay_order": list(closure),
        "transitive_closure_lf_sha256": _sha256_bytes(
            ("\n".join(closure) + ("\n" if closure else "")).encode("utf-8")
        ),
    }


def _accepted_attempt(audit_row: Mapping[str, object]) -> dict[str, object] | None:
    attempts = audit_row.get("recipe_audit", {}).get("attempts")
    if type(attempts) is not list:
        raise LibraryOptimizerComparisonPilotError("A2.1 attempt list is malformed")
    accepted = [
        attempt
        for attempt in attempts
        if type(attempt) is dict and attempt.get("outcome") == "kernel-accepted"
    ]
    if not accepted:
        return None
    if len(accepted) != 1:
        raise LibraryOptimizerComparisonPilotError(
            "A2.1 row has a non-unique accepted omission attempt"
        )
    attempt = accepted[0]
    receipt = attempt.get("positive_receipt")
    if type(receipt) is not dict:
        raise LibraryOptimizerComparisonPilotError("accepted A2.1 attempt has no receipt")
    return attempt


def _expected_body_receipt(
    name: str,
    *,
    audit_row: Mapping[str, object],
    rebuild_row: Mapping[str, object] | None,
) -> tuple[dict[str, object], dict[str, object]]:
    accepted_attempt = _accepted_attempt(audit_row)
    readable = audit_row.get("readable", {}).get("proof")
    initial = audit_row.get("recipe_audit", {}).get("positive_receipt")
    if type(readable) is not dict or type(initial) is not dict or readable != initial:
        raise LibraryOptimizerComparisonPilotError(
            f"A2.1 initial readable proof receipt drifted for {name!r}"
        )
    if rebuild_row is not None:
        body = rebuild_row.get("body_receipt")
        accepted = (
            None
            if accepted_attempt is None
            else accepted_attempt.get("positive_receipt")
        )
        candidate_dependencies = tuple(
            rebuild_row.get("candidate_direct_dependencies", ())
        )
        retained_dependencies = tuple(rebuild_row.get("retained_direct_dependencies", ()))
        omitted = rebuild_row.get("direct_cut_spine", {}).get(
            "omitted_direct_dependency"
        )
        if (
            type(body) is not dict
            or type(accepted) is not dict
            or body != accepted
            or tuple(audit_row.get("declared_dependencies", ()))
            != retained_dependencies
            or tuple(accepted_attempt.get("before_dependencies", ()))
            != retained_dependencies
            or tuple(accepted_attempt.get("after_dependencies", ()))
            != candidate_dependencies
            or accepted_attempt.get("omitted_dependency") != omitted
            or tuple(
                dependency
                for dependency in retained_dependencies
                if dependency != omitted
            )
            != candidate_dependencies
        ):
            raise LibraryOptimizerComparisonPilotError(
                f"A2.2/last accepted body receipt drifted for {name!r}"
            )
        return body, {
            "accepted_after_dependencies": list(candidate_dependencies),
            "accepted_omitted_dependency": omitted,
            "a2_1_initial_readable_receipt_sha256": readable["receipt_sha256"],
            "a2_1_last_accepted_receipt_sha256": accepted["receipt_sha256"],
            "a2_2_body_receipt_sha256": body["receipt_sha256"],
            "receipt_route": "a2.2-and-last-accepted-omission",
        }
    if accepted_attempt is not None:
        raise LibraryOptimizerComparisonPilotError(
            f"accepted omission lacks an A2.2 rebuild for {name!r}"
        )
    recipe = audit_row.get("recipe_audit")
    if (
        type(recipe) is not dict
        or tuple(recipe.get("initial_dependencies", ()))
        != tuple(audit_row.get("declared_dependencies", ()))
        or tuple(recipe.get("candidate_dependencies", ()))
        != tuple(audit_row.get("declared_dependencies", ()))
    ):
        raise LibraryOptimizerComparisonPilotError(
            f"no-omission A2.1 vector drifted for {name!r}"
        )
    return initial, {
        "a2_1_initial_readable_receipt_sha256": readable["receipt_sha256"],
        "a2_1_recipe_audit_positive_receipt_sha256": initial["receipt_sha256"],
        "receipt_route": "no-accepted-omission-recipe-audit-fallback",
    }


def _recover_node(
    name: str,
    *,
    root: Path,
    audit_rows: Mapping[str, dict[str, object]],
    rebuild_rows: Mapping[str, dict[str, object]],
    replay_rows: Mapping[str, dict[str, object]],
    recovered_targets: Mapping[str, Formula],
) -> tuple[RecoveredModularBody, dict[str, object]]:
    replay_row = replay_rows[name]
    rebuild_row = rebuild_rows.get(name)
    if rebuild_row is None:
        _raw, _fuel, target, proof = _decode_replay_artifact(root, replay_row)
        dependencies = tuple(replay_row.get("declared_dependencies", ()))
        source = {
            "artifact_sha256": replay_row["artifact"]["sha256"],
            "kind": "retained-replay",
            "proof_term_sha256": replay_row["proof_term_sha256"],
        }
    else:
        _raw, _fuel, target, proof = _decode_rebuild_artifact(
            rebuild_row, replay_row=replay_row
        )
        dependencies = tuple(rebuild_row.get("candidate_direct_dependencies", ()))
        source = {
            "artifact_sha256": rebuild_row["rebuilt_certificate"]["artifact_sha256"],
            "kind": "a2.2-direct-cut-rebuild",
            "proof_term_sha256": rebuild_row["rebuilt_certificate"]["proof_term_sha256"],
        }
    if not all(type(item) is str for item in dependencies):
        raise LibraryOptimizerComparisonPilotError("node dependency vector is malformed")

    dependency_targets: dict[str, Formula] = {}
    dependency_hashes: dict[str, str] = {}
    for dependency in dependencies:
        dependency_row = replay_rows.get(dependency)
        dep_target = recovered_targets.get(dependency)
        if dependency_row is None or dep_target is None:
            raise LibraryOptimizerComparisonPilotError(
                f"dependency {dependency!r} was not recovered earlier in replay order"
            )
        dependency_targets[dependency] = dep_target
        dependency_hashes[dependency] = dependency_row["proof_term_sha256"]
    expected_receipt, receipt_source = _expected_body_receipt(
        name,
        audit_row=audit_rows[name],
        rebuild_row=rebuild_row,
    )
    recovered = recover_curried_modular_body(
        name=name,
        target=target,
        proof=proof,
        dependencies=dependencies,
        dependency_targets=dependency_targets,
        dependency_proof_sha256=dependency_hashes,
        expected_body_receipt=expected_receipt,
    )
    return recovered, {
        **source,
        **receipt_source,
        "identity_metrics_comparable": False,
        "source_identity_metrics_transportable": False,
        "stable_receipt_fields_compared": [
            "certificate_representation",
            "certificate_sha256",
            "dependency_count",
            "kernel_accepted",
            "metrics.proof_depth",
            "metrics.proof_nodes",
            "target_formula_sha256",
        ],
    }


def _artifact_metrics(raw: bytes, proof: Proof) -> dict[str, int]:
    tree = proof_tree_metrics(proof)
    return {
        "artifact_bytes": len(raw),
        "cut_nodes": tree["cut_nodes"],
        "proof_depth": tree["proof_depth"],
        "proof_nodes": tree["proof_nodes"],
    }


def _candidate_comparison(
    *, candidate_id: str, kind_order: int, raw: bytes, proof: Proof
) -> dict[str, object]:
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "candidate_id": candidate_id,
        "candidate_kind_order": kind_order,
        "metrics": _artifact_metrics(raw, proof),
    }


def _build_layered_candidate(
    root_name: str,
    *,
    root: Path,
    audit_rows: Mapping[str, dict[str, object]],
    rebuild_rows: Mapping[str, dict[str, object]],
    replay_rows: Mapping[str, dict[str, object]],
    _shared_body_cache: dict[
        str, tuple[RecoveredModularBody, dict[str, object]]
    ] | None = None,
) -> tuple[bytes, int, Formula, Proof, dict[str, object], tuple[str, ...], tuple[str, ...]]:
    body_cache = {} if _shared_body_cache is None else _shared_body_cache
    overrides = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in rebuild_rows.items()
    }
    closure = _closure(root_name, replay_rows=replay_rows, overrides=overrides)
    node_names = tuple(
        sorted((*closure, root_name), key=lambda name: replay_rows[name]["index"])
    )
    positions = {name: index for index, name in enumerate(node_names)}
    nodes: list[LayeredReplayNode] = []
    body_sources: list[dict[str, object]] = []
    target: Formula | None = None
    for name in node_names:
        cached = body_cache.get(name)
        if cached is None:
            recovered, source = _recover_node(
                name,
                root=root,
                audit_rows=audit_rows,
                rebuild_rows=rebuild_rows,
                replay_rows=replay_rows,
                recovered_targets={
                    dependency: carrier.target
                    for dependency, (carrier, _source) in body_cache.items()
                },
            )
            body_cache[name] = (recovered, source)
        else:
            recovered, source = cached
        dependencies = tuple(
            positions[dependency] for dependency in recovered.dependencies
        )
        nodes.append(
            LayeredReplayNode(
                positions[name], recovered.target, dependencies, recovered.body
            )
        )
        body_sources.append(
            {
                "body_certificate_sha256": recovered.receipt["certificate_sha256"],
                "dependencies": list(recovered.dependencies),
                "index": replay_rows[name]["index"],
                "name": name,
                **source,
            }
        )
        if name == root_name:
            target = recovered.target
    if target is None:
        raise LibraryOptimizerComparisonPilotError("layered root target is missing")
    bundle = LayeredReplayBundle(tuple(nodes), positions[root_name])
    compilation = compile_layered_replay(
        bundle, target, limits=PILOT_LAYERED_LIMITS
    )
    if type(compilation) is not LayeredReplayCandidate:
        raise LibraryOptimizerComparisonPilotError(
            f"layered compiler returned typed unknown for {root_name!r}"
        )
    if not check((), compilation.certificate, target):
        raise LibraryOptimizerComparisonPilotError(
            f"layered certificate for {root_name!r} failed empty-context check"
        )
    tree = proof_tree_metrics(compilation.certificate)
    if (
        tree["proof_nodes"] != compilation.proof_nodes
        or tree["proof_depth"] != compilation.proof_depth
    ):
        raise LibraryOptimizerComparisonPilotError("layered compiler metrics drifted")
    fuel = FUEL_MULTIPLIER * tree["proof_nodes"] + FUEL_OFFSET
    raw = encode_artifact_bounded(
        fuel, target, compilation.certificate, max_bytes=MAX_ARTIFACT_BYTES
    )
    decoded_fuel, decoded_target, decoded_proof = decode_artifact(
        raw, max_bytes=MAX_ARTIFACT_BYTES, max_nodes=1_000_000, max_depth=512
    )
    if (
        decoded_fuel != fuel
        or decoded_target != target
        or encode_proof(decoded_proof) != encode_proof(compilation.certificate)
        or encode_artifact_bounded(
            decoded_fuel, decoded_target, decoded_proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        != raw
        or not check((), decoded_proof, target)
    ):
        raise LibraryOptimizerComparisonPilotError(
            f"layered artifact for {root_name!r} failed encode/decode replay"
        )
    diagnostics = {
        "body_sources": body_sources,
        "compiler_result_type": "LayeredReplayCandidate",
        "dependency_edge_count": sum(len(node.dependencies) for node in nodes),
        "layer_count": len(compilation.layers),
        "layers": [list(layer) for layer in compilation.layers],
        "maximum_package_formula_depth": compilation.maximum_package_formula_depth,
        "node_count": len(nodes),
        "node_names_in_replay_order": list(node_names),
        "node_names_lf_sha256": _sha256_bytes(
            ("\n".join(node_names) + "\n").encode("utf-8")
        ),
        "package_formula_occurrences": compilation.package_formula_occurrences,
    }
    return (
        raw,
        fuel,
        target,
        decoded_proof,
        diagnostics,
        closure,
        overrides[root_name],
    )


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _build_candidate_optimizer_comparison_pilot(
    root: Path, *, producer_source_state: Mapping[str, object]
) -> dict[str, object]:
    producer = _validate_producer_source_state(producer_source_state, root=root)
    (
        audit,
        rebuild,
        manifest,
        audit_rows,
        rebuild_rows,
        replay_rows,
    ) = _load_fixed_inputs(root)
    result_rows: list[dict[str, object]] = []
    aggregate_frontier_members = 0
    representative_counts = {candidate_id: 0 for candidate_id, _ in CANDIDATE_KINDS}
    body_cache: dict[str, tuple[RecoveredModularBody, dict[str, object]]] = {}

    for index, name in _EXPECTED:
        replay_row = replay_rows[name]
        rebuild_row = rebuild_rows[name]
        audit_row = audit_rows[name]
        if (
            replay_row.get("index") != index
            or rebuild_row.get("index") != index
            or audit_row.get("index") != index
            or replay_row.get("formula_sha256")
            != rebuild_row.get("original", {}).get("formula_sha256")
            or audit_row.get("record_sha256")
            != rebuild_row.get("a2_1", {}).get("audit_record_sha256")
        ):
            raise LibraryOptimizerComparisonPilotError(
                f"A2.1/A2.2/replay join drifted for {name!r}"
            )

        retained_raw, retained_fuel, target, retained_proof = _decode_replay_artifact(
            root, replay_row
        )
        retained_comparison = _candidate_comparison(
            candidate_id="retained-replay",
            kind_order=0,
            raw=retained_raw,
            proof=retained_proof,
        )
        del retained_proof
        rebuild_raw, rebuild_fuel, rebuild_target, rebuild_proof = _decode_rebuild_artifact(
            rebuild_row, replay_row=replay_row
        )
        if rebuild_target != target:
            raise LibraryOptimizerComparisonPilotError(
                f"candidate targets differ for {name!r}"
            )
        rebuild_comparison = _candidate_comparison(
            candidate_id="a2.2-direct-cut-rebuild",
            kind_order=1,
            raw=rebuild_raw,
            proof=rebuild_proof,
        )
        del rebuild_proof
        (
            layered_raw,
            layered_fuel,
            layered_target,
            layered_proof,
            layered_diagnostics,
            layered_closure,
            layered_direct,
        ) = _build_layered_candidate(
            name,
            root=root,
            audit_rows=audit_rows,
            rebuild_rows=rebuild_rows,
            replay_rows=replay_rows,
            _shared_body_cache=body_cache,
        )
        if layered_target != target:
            raise LibraryOptimizerComparisonPilotError(
                f"layered target differs for {name!r}"
            )
        if layered_diagnostics["node_count"] != PILOT_BUNDLE_NODE_COUNTS[name]:
            raise LibraryOptimizerComparisonPilotError(
                f"layered bundle size drifted for {name!r}"
            )
        layered_comparison = _candidate_comparison(
            candidate_id="layered-closure",
            kind_order=2,
            raw=layered_raw,
            proof=layered_proof,
        )
        layered_proof_sha256 = _sha256_bytes(encode_proof(layered_proof))
        del layered_proof

        retained_direct = tuple(replay_row["declared_dependencies"])
        rebuild_direct = tuple(rebuild_row["candidate_direct_dependencies"])
        retained_closure = _closure(name, replay_rows=replay_rows, overrides={})
        rebuild_closure = _closure(
            name, replay_rows=replay_rows, overrides={name: rebuild_direct}
        )
        recorded_rebuild_closure = tuple(
            rebuild_row["transitive_closure"]["dependencies_in_replay_order"]
        )
        if rebuild_closure != recorded_rebuild_closure:
            raise LibraryOptimizerComparisonPilotError(
                f"A2.2 closure differs from exact reconstruction for {name!r}"
            )

        comparison_candidates = (
            retained_comparison,
            rebuild_comparison,
            layered_comparison,
        )
        if tuple(
            (item["candidate_id"], item["candidate_kind_order"])
            for item in comparison_candidates
        ) != CANDIDATE_KINDS:
            raise LibraryOptimizerComparisonPilotError("candidate universe order drifted")
        frontier = componentwise_nondominated(comparison_candidates)
        frontier_set = set(frontier)
        frontier_candidates = tuple(
            candidate
            for candidate in comparison_candidates
            if candidate["candidate_id"] in frontier_set
        )
        representative = select_pilot_representative(frontier_candidates)
        if representative not in frontier_set:
            raise LibraryOptimizerComparisonPilotError(
                "pilot representative is not on the computed frontier"
            )
        aggregate_frontier_members += len(frontier)
        representative_counts[representative] += 1

        artifacts = [
            {
                **comparison_candidates[0],
                "certificate_representation": CERTIFICATE_REPRESENTATION,
                "fuel": retained_fuel,
                "formula_sha256": replay_row["formula_sha256"],
                "kernel_accepted": True,
                "kernel_context": "empty",
                "logic_mode": LOGIC_MODE,
                "proof_term_sha256": replay_row["proof_term_sha256"],
                "source": {
                    "artifact_path": replay_row["artifact"]["path"],
                    "manifest_record_index": replay_row["index"],
                    "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
                },
                "surface": _surface(
                    retained_direct,
                    retained_closure,
                    surface_basis=SURFACE_BASES["retained-replay"],
                ),
            },
            {
                **comparison_candidates[1],
                "certificate_representation": CERTIFICATE_REPRESENTATION,
                "fuel": rebuild_fuel,
                "formula_sha256": replay_row["formula_sha256"],
                "kernel_accepted": True,
                "kernel_context": "empty",
                "logic_mode": LOGIC_MODE,
                "proof_term_sha256": rebuild_row["rebuilt_certificate"][
                    "proof_term_sha256"
                ],
                "source": {
                    "construction_rebuild_record_sha256": rebuild_row["record_sha256"],
                    "construction_rebuild_root_sha256": REBUILD_ROOT_SHA256,
                },
                "surface": _surface(
                    rebuild_direct,
                    rebuild_closure,
                    surface_basis=SURFACE_BASES["a2.2-direct-cut-rebuild"],
                ),
            },
            {
                **comparison_candidates[2],
                "artifact_base64": base64.b64encode(layered_raw).decode("ascii"),
                "certificate_representation": CERTIFICATE_REPRESENTATION,
                "fuel": layered_fuel,
                "formula_sha256": _sha256_bytes(encode_formula(layered_target)),
                "kernel_accepted": True,
                "kernel_context": "empty",
                "logic_mode": LOGIC_MODE,
                "proof_term_sha256": layered_proof_sha256,
                "source": {
                    "compiler_callable": (
                        "peano_lab.library.layered_replay.compile_layered_replay"
                    ),
                    "compiler_source_sha256": _PINNED_IMPLEMENTATION[0][2],
                },
                "surface": _surface(
                    layered_direct,
                    layered_closure,
                    surface_basis=SURFACE_BASES["layered-closure"],
                ),
            },
        ]
        if base64.b64decode(artifacts[2]["artifact_base64"], validate=True) != layered_raw:
            raise LibraryOptimizerComparisonPilotError("layered base64 round trip failed")

        row: dict[str, object] = {
            "a2_complete": False,
            "artifacts": artifacts,
            "comparison": {
                "axes_in_componentwise_order": list(COMPARISON_AXES),
                "candidate_universe_complete": True,
                "candidate_universe_ids_in_order": [item[0] for item in CANDIDATE_KINDS],
                "claim": "bounded-three-candidate-pilot-only",
                "global_best_claim": False,
                "minimality_claim": False,
                "nondominated_candidate_ids_in_input_order": list(frontier),
                "representative_candidate_id": representative,
                "representative_tie_break": [
                    "proof_nodes",
                    "proof_depth",
                    "cut_nodes",
                    "artifact_bytes",
                    "candidate_kind_order",
                    "artifact_sha256",
                    "candidate_id",
                ],
            },
            "dependency_vectors_complete": False,
            "index": index,
            "layered_bundle": layered_diagnostics,
            "lineage_complete": False,
            "minimality_claim": False,
            "name": name,
            "optimized_best_known": False,
            "optimized_vector_independently_audited": False,
            "original": {
                "formula_sha256": replay_row["formula_sha256"],
                "statement_canonical_sha256": replay_row[
                    "statement_canonical_sha256"
                ],
                "statement_source_sha256": replay_row["statement_source_sha256"],
            },
            "public_graph_applied": False,
            "publication_union_complete": False,
            "publication_union_verified": False,
            "review_complete": False,
        }
        row["record_sha256"] = _record_hash(row)
        result_rows.append(row)

    cached_body_proof_nodes = sum(
        carrier.receipt["metrics"]["proof_nodes"]
        for carrier, _source in body_cache.values()
    )
    cached_body_edges = sum(
        len(carrier.dependencies) for carrier, _source in body_cache.values()
    )
    cached_body_maximum = max(
        carrier.receipt["metrics"]["proof_nodes"]
        for carrier, _source in body_cache.values()
    )
    if (
        len(body_cache) != PILOT_BODY_UNION_COUNT
        or cached_body_edges != PILOT_BODY_UNION_DIRECT_EDGES
        or cached_body_proof_nodes != PILOT_BODY_UNION_PROOF_NODES
        or cached_body_maximum != PILOT_BODY_MAX_PROOF_NODES
    ):
        raise LibraryOptimizerComparisonPilotError(
            "three-root recovered-body union bound drifted"
        )
    body_cache.clear()

    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
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
    body = {
        "a2_complete": False,
        "aggregate": {
            "candidate_artifact_count": THEOREM_COUNT * len(CANDIDATE_KINDS),
            "candidate_count_per_theorem": len(CANDIDATE_KINDS),
            "cached_modular_body_count": PILOT_BODY_UNION_COUNT,
            "cached_modular_body_direct_edges": PILOT_BODY_UNION_DIRECT_EDGES,
            "cached_modular_body_maximum_proof_nodes": PILOT_BODY_MAX_PROOF_NODES,
            "cached_modular_body_proof_nodes": PILOT_BODY_UNION_PROOF_NODES,
            "nondominated_members_total": aggregate_frontier_members,
            "pilot_theorem_count": THEOREM_COUNT,
            "representative_counts": representative_counts,
            "retained_public_graph_edges": RETAINED_PUBLIC_GRAPH_EDGES,
        },
        "dependency_vectors_complete": False,
        "evaluation_eligible": False,
        "format": OPTIMIZER_COMPARISON_PILOT_FORMAT,
        "freeze_ready": False,
        "id": OPTIMIZER_COMPARISON_PILOT_ID,
        "inputs": {
            "construction_rebuild": {
                "artifact_path": _REBUILD_RELATIVE.as_posix(),
                "artifact_sha256": REBUILD_ARTIFACT_SHA256,
                "root_sha256": REBUILD_ROOT_SHA256,
                "theorem_record_root_sha256": REBUILD_THEOREM_RECORD_ROOT_SHA256,
            },
            "dependency_audit": {
                "artifact_path": _AUDIT_RELATIVE.as_posix(),
                "artifact_sha256": AUDIT_ARTIFACT_SHA256,
                "root_sha256": AUDIT_ROOT_SHA256,
                "theorem_record_root_sha256": AUDIT_THEOREM_RECORD_ROOT_SHA256,
            },
            "implementation": [
                {
                    "module": module,
                    "path": relative.as_posix(),
                    "sha256": digest,
                }
                for module, relative, digest in _PINNED_IMPLEMENTATION
            ],
            "layered_replay_limits": {
                field: getattr(PILOT_LAYERED_LIMITS, field)
                for field in PILOT_LAYERED_LIMITS.__dataclass_fields__
            },
            "replay_pack": {
                "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
                "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
                "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
                "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
                "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
                "replay_root_sha256": REPLAY_ROOT_SHA256,
            },
        },
        "lineage_complete": False,
        "logic_mode": LOGIC_MODE,
        "minimality_claim": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "publication_ready": False,
        "publication_union_complete": False,
        "publication_union_verified": False,
        "producer_git_verified": False,
        "producer_source_state": producer,
        "producer_source_state_sha256": _sha256_json(
            producer, limit=MAX_SCHEMA_BYTES
        ),
        "retrieval_eligible": False,
        "review_complete": False,
        "schema": optimizer_comparison_pilot_schema_identity(),
        "status": STATUS,
        "theorem_count": THEOREM_COUNT,
        "theorem_records": theorem_records,
        "training_eligible": False,
        "v": OPTIMIZER_COMPARISON_PILOT_VERSION,
    }
    root_preimage = {
        "format": OPTIMIZER_COMPARISON_PILOT_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": OPTIMIZER_COMPARISON_PILOT_VERSION,
    }
    result = {
        **body,
        "root_preimage": root_preimage,
        "root_sha256": _sha256_json(root_preimage),
        "theorems": result_rows,
    }
    # Keep the three exact upstream documents live through all source joins;
    # no claim is derived from an unpinned or lazily substituted input.
    if not (audit and rebuild and manifest):
        raise LibraryOptimizerComparisonPilotError("fixed input unexpectedly empty")
    return result


def build_candidate_optimizer_comparison_pilot(
    *,
    producer_source_state: Mapping[str, object],
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Build and kernel-check the exact bounded three-root A2.3a pilot."""

    optimizer_comparison_pilot_schema()
    root = _repository_root(repository_root)
    result = _build_candidate_optimizer_comparison_pilot(
        root, producer_source_state=producer_source_state
    )
    canonical_document_bytes(result)
    return deepcopy(result)


def validate_optimizer_comparison_pilot(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate a pilot by exact reconstruction from all pinned inputs."""

    optimizer_comparison_pilot_schema()
    if type(value) is not dict:
        raise LibraryOptimizerComparisonPilotError("pilot must be one object")
    _validate_json(value)
    embedded_producer = value.get("producer_source_state")
    if type(embedded_producer) is not dict:
        raise LibraryOptimizerComparisonPilotError(
            "pilot has no typed producer source state"
        )
    expected = _build_candidate_optimizer_comparison_pilot(
        _repository_root(repository_root),
        producer_source_state=embedded_producer,
    )
    if value != expected:
        raise LibraryOptimizerComparisonPilotError(
            "pilot differs from exact fixed-source reconstruction"
        )
    return _decode_document(
        canonical_document_bytes(expected), "validated pilot", limit=MAX_DOCUMENT_BYTES
    )


def load_optimizer_comparison_pilot(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one bounded canonical pilot and reconstruct every result."""

    raw = _safe_file(path, label="optimizer/comparison pilot", limit=MAX_DOCUMENT_BYTES)
    value = _decode_document(raw, "optimizer/comparison pilot", limit=MAX_DOCUMENT_BYTES)
    if canonical_document_bytes(value) != raw:
        raise LibraryOptimizerComparisonPilotError("pilot JSON is not canonical")
    return validate_optimizer_comparison_pilot(value, repository_root=repository_root)


__all__ = [
    "LibraryOptimizerComparisonPilotError",
    "RecoveredModularBody",
    "build_candidate_optimizer_comparison_pilot",
    "canonical_document_bytes",
    "componentwise_nondominated",
    "load_optimizer_comparison_pilot",
    "optimizer_comparison_pilot_schema",
    "optimizer_comparison_pilot_schema_identity",
    "recover_curried_modular_body",
    "select_pilot_representative",
    "validate_optimizer_comparison_pilot",
]
