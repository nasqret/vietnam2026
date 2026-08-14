"""Independent verifier for the bounded Hydra A2.3a comparison pilot.

This module deliberately does not import the producer, the layered compiler,
the tactic engine, or the replay-pack implementation.  It treats the producer
result as hostile data, obtains the nine certificate artifacts from their
three fixed transport surfaces, and asks only the unchanged Peano kernel to
check them against the original goals.

The verifier establishes a narrow mechanical fact: the exact three-by-three
candidate comparison was encoded, measured, ordered, and hashed as claimed.
It grants no dependency-vector, best-known, publication, review, training, or
A2-completion authority.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import fields
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping

from peano_lab.kernel.artifact_codec import (
    decode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Cut, Proof


VERIFICATION_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-verification"
)
VERIFICATION_VERSION = 1
VERIFICATION_ID = "independent-a2.3a-optimizer-comparison-pilot-verification-v1"
VERIFICATION_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-verification-root-preimage"
)
VERIFICATION_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-verification-records-preimage"
)

PILOT_FORMAT = "peano-hydra-library-optimizer-comparison-pilot"
PILOT_VERSION = 1
PILOT_ID = "authoring-l0-optimizer-comparison-pilot-candidate-v1"
PILOT_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-root-preimage"
)
PILOT_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-optimizer-comparison-pilot-records-preimage"
)
PRODUCER_SOURCE_STATE_FORMAT = "peano-hydra-producer-source-state"
PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-producer-source-state-root-preimage"
)

LOGIC_MODE = "intuitionistic"
CANDIDATE_STATUS = "candidate"
VERIFICATION_STATUS = "passed"
CERTIFICATE_REPRESENTATION = "peano-lab-v2"
MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_ARTIFACT_BYTES = 8_000_000
MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_JSON_DEPTH = 256
MAX_JSON_ITEMS = 4_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
MAX_PROOF_NODES = 1_000_000
MAX_PROOF_DEPTH = 512
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
PYCACHE_PREFIX = "/proc/peano-hydra-a23a-disabled-pycache"

EXPECTED_THEOREMS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
CANDIDATE_KINDS = (
    ("retained-replay", 0),
    ("a2.2-direct-cut-rebuild", 1),
    ("layered-closure", 2),
)
COMPARISON_AXES = (
    "artifact_bytes",
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
)
REPRESENTATIVE_TIE_BREAK = (
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
    "artifact_bytes",
    "candidate_kind_order",
    "artifact_sha256",
    "candidate_id",
)
SURFACE_BASES = {
    "retained-replay": "retained-manifest-literal-direct-cut-spine",
    "a2.2-direct-cut-rebuild": "a2.2-rebuilt-literal-direct-cut-spine",
    "layered-closure": (
        "modular-input-graph-not-literal-final-certificate-cut-spine"
    ),
}

_ROOT_BODY_FIELDS = {
    "a2_complete",
    "aggregate",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "format",
    "freeze_ready",
    "id",
    "inputs",
    "lineage_complete",
    "logic_mode",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "publication_ready",
    "publication_union_complete",
    "publication_union_verified",
    "producer_git_verified",
    "producer_source_state",
    "producer_source_state_sha256",
    "retrieval_eligible",
    "review_complete",
    "schema",
    "status",
    "theorem_count",
    "theorem_records",
    "training_eligible",
    "v",
}
_ROOT_FALSE_FIELDS = (
    "a2_complete",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_ready",
    "lineage_complete",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "publication_ready",
    "publication_union_complete",
    "publication_union_verified",
    "producer_git_verified",
    "retrieval_eligible",
    "review_complete",
    "training_eligible",
)
_THEOREM_FIELDS = {
    "a2_complete",
    "artifacts",
    "comparison",
    "dependency_vectors_complete",
    "index",
    "layered_bundle",
    "lineage_complete",
    "minimality_claim",
    "name",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "original",
    "public_graph_applied",
    "publication_union_complete",
    "publication_union_verified",
    "record_sha256",
    "review_complete",
}
_THEOREM_FALSE_FIELDS = (
    "a2_complete",
    "dependency_vectors_complete",
    "lineage_complete",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "public_graph_applied",
    "publication_union_complete",
    "publication_union_verified",
    "review_complete",
)
_ARTIFACT_COMMON_FIELDS = {
    "artifact_sha256",
    "candidate_id",
    "candidate_kind_order",
    "certificate_representation",
    "fuel",
    "formula_sha256",
    "kernel_accepted",
    "kernel_context",
    "logic_mode",
    "metrics",
    "proof_term_sha256",
    "source",
    "surface",
}
_SURFACE_FIELDS = {
    "direct_dependencies",
    "direct_dependencies_lf_sha256",
    "direct_dependency_count",
    "surface_basis",
    "transitive_closure_count",
    "transitive_closure_dependencies_in_replay_order",
    "transitive_closure_lf_sha256",
}
_COMPARISON_FIELDS = {
    "axes_in_componentwise_order",
    "candidate_universe_complete",
    "candidate_universe_ids_in_order",
    "claim",
    "global_best_claim",
    "minimality_claim",
    "nondominated_candidate_ids_in_input_order",
    "representative_candidate_id",
    "representative_tie_break",
}
_LAYERED_BUNDLE_FIELDS = {
    "body_sources",
    "compiler_result_type",
    "dependency_edge_count",
    "layer_count",
    "layers",
    "maximum_package_formula_depth",
    "node_count",
    "node_names_in_replay_order",
    "node_names_lf_sha256",
    "package_formula_occurrences",
}

VERIFICATION_FALSE_FIELDS = (
    "a2_complete",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_ready",
    "lineage_complete",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "producer_git_verified",
    "proof_authority",
    "publication_authority",
    "publication_ready",
    "publication_union_complete",
    "publication_union_verified",
    "retrieval_eligible",
    "review_complete",
    "theorem_admission_authority",
    "training_eligible",
)
VERIFICATION_RECEIPT_BODY_FIELDS = frozenset(
    {
        *VERIFICATION_FALSE_FIELDS,
        "aggregate",
        "candidate",
        "candidate_status",
        "format",
        "id",
        "kernel_artifacts_verified",
        "logic_mode",
        "producer_source_state",
        "producer_source_state_sha256",
        "status",
        "theorem_count",
        "theorem_records",
        "v",
        "verifier",
    }
)
VERIFICATION_RECEIPT_FIELDS = frozenset(
    {*VERIFICATION_RECEIPT_BODY_FIELDS, "root_preimage", "root_sha256", "theorems"}
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_RELATIVE = Path(
    "training/peano_hydra/library-optimizer-comparison-pilot-schema-v1.json"
)
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

# Frozen producer protocol sources.  These hashes are inputs to the verifier,
# not values copied from the candidate document under review.
PRODUCER_SOURCE_FILES = (
    (
        _SCHEMA_RELATIVE,
        26_493,
        "006d38ef781fc022b7b8929be35058038df02a0eee91eb2213128598c66a59ae",
    ),
    (
        Path("training/peano_hydra/library_optimizer_comparison_pilot.py"),
        81_389,
        "7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee",
    ),
    (
        Path("scripts/build_peano_hydra_library_optimizer_comparison_pilot.py"),
        9_092,
        "3acbd3ec0f190699d484ef0c800e4919c7cc8404fbbd50ba6daf90a5deb5d6ee",
    ),
    (
        Path(
            "peano-lab/py/tests/"
            "test_peano_hydra_library_optimizer_comparison_pilot.py"
        ),
        46_611,
        "d5ae3e830573c7a561462f5e0e91ef99bff42f6533986106cc65fc34f0e35dc9",
    ),
)
SCHEMA_SEMANTIC_SHA256 = (
    "07e5842c221fe84337e163ce5c858ab03dfbbc93d1477f5661edfdd6f8ba3978"
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
REBUILD_ARTIFACT_SHA256 = (
    "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182"
)
REBUILD_ROOT_SHA256 = (
    "91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0"
)
REBUILD_THEOREM_RECORD_ROOT_SHA256 = (
    "42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5"
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

_KERNEL_SOURCES = (
    (
        "peano_lab",
        Path("peano-lab/py/peano_lab/__init__.py"),
        "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a",
    ),
    (
        "peano_lab.kernel",
        Path("peano-lab/py/peano_lab/kernel/__init__.py"),
        "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    ),
    (
        "peano_lab.kernel.artifact_codec",
        Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        "peano_lab.kernel.checker",
        Path("peano-lab/py/peano_lab/kernel/checker.py"),
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        "peano_lab.kernel.formulas",
        Path("peano-lab/py/peano_lab/kernel/formulas.py"),
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        "peano_lab.kernel.proofs",
        Path("peano-lab/py/peano_lab/kernel/proofs.py"),
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
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

_PRODUCER_IMPLEMENTATION = (
    (
        "peano_lab.library.layered_replay",
        "peano-lab/py/peano_lab/library/layered_replay.py",
        "ad4421446336b7c8c0db9f12298a5aa66718dfeac76282ab91bf0db3ce00f4c4",
    ),
    (
        "peano_lab.kernel.checker",
        "peano-lab/py/peano_lab/kernel/checker.py",
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        "peano_lab.kernel.artifact_codec",
        "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        "training.peano_hydra.library_replay_pack",
        "training/peano_hydra/library_replay_pack.py",
        "8c5f3b44bed64bc3a49a7990d16a6f3c4a966b14c2bf4c732227041bc81506ee",
    ),
    (
        "peano_lab.kernel.proofs",
        "peano-lab/py/peano_lab/kernel/proofs.py",
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    ),
    (
        "peano_lab.kernel.formulas",
        "peano-lab/py/peano_lab/kernel/formulas.py",
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        "peano_lab.engine.state",
        "peano-lab/py/peano_lab/engine/state.py",
        "453904142273f14d01379c73c637be3476d035b093047587ff6990f1d572ac2f",
    ),
    (
        "peano_lab.kernel.terms",
        "peano-lab/py/peano_lab/kernel/terms.py",
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
    ),
    (
        "peano_lab.kernel.subst",
        "peano-lab/py/peano_lab/kernel/subst.py",
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    ),
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA1_RE = re.compile(r"[0-9a-f]{40}")


class LibraryOptimizerComparisonVerificationError(ValueError):
    """The candidate, a fixed input, or a verification claim is invalid."""


def _require_runtime_import_boundary() -> None:
    forbidden = sorted(
        name
        for name in sys.modules
        if name.startswith("peano_lab.engine")
        or name.startswith("peano_lab.library")
        or name.startswith("peano_lab.tactics")
        or name == "training.peano_hydra"
        or name.startswith("training.peano_hydra.")
    )
    if forbidden:
        raise LibraryOptimizerComparisonVerificationError(
            "independent verifier runtime import boundary is contaminated"
        )
    if (
        getattr(sys.flags, "safe_path", False) is not True
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.dont_write_bytecode is not True
        or sys.pycache_prefix != PYCACHE_PREFIX
        or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
        or os.environ.get("PYTHONPATH") not in (None, "")
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "independent verifier interpreter isolation policy differs"
        )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_float(value: str) -> object:
    raise ValueError(f"JSON floating-point number {value!r}")


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _validate_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> int:
    if depth > MAX_JSON_DEPTH:
        raise LibraryOptimizerComparisonVerificationError(
            f"{path} exceeds the JSON depth limit"
        )
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryOptimizerComparisonVerificationError(
                f"{path} exceeds the safe integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise LibraryOptimizerComparisonVerificationError(
                f"{path} contains a Unicode surrogate"
            ) from None
        return 1
    if type(value) not in (list, dict):
        raise LibraryOptimizerComparisonVerificationError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryOptimizerComparisonVerificationError(f"{path} contains a cycle")
    if len(value) > MAX_JSON_ITEMS:
        raise LibraryOptimizerComparisonVerificationError(
            f"{path} has too many items"
        )
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
                raise LibraryOptimizerComparisonVerificationError(
                    "JSON document has too many items"
                )
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryOptimizerComparisonVerificationError(
                f"{path} contains a non-string key"
            )
        count += _validate_json(
            key,
            path=f"{path}.<key>",
            depth=depth + 1,
            ancestors=descendants,
        )
        count += _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=descendants,
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryOptimizerComparisonVerificationError(
                "JSON document has too many items"
            )
    return count


def _compact_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> bytes:
    _validate_json(value)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LibraryOptimizerComparisonVerificationError(
            "cannot encode compact canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryOptimizerComparisonVerificationError(
            "compact canonical JSON exceeds its byte limit"
        )
    return raw


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256(_compact_json(value, limit=limit))


def canonical_verification_receipt_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Encode a candidate or verification receipt as canonical retained JSON."""

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
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LibraryOptimizerComparisonVerificationError(
            "cannot encode canonical verification JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryOptimizerComparisonVerificationError(
            "canonical verification JSON exceeds its byte limit"
        )
    return raw


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if len(raw) > limit:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} exceeds its byte limit"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} must be one JSON object"
        )
    _validate_json(value)
    return value


def _safe_file(path: Path, *, label: str, limit: int) -> bytes:
    try:
        absolute = Path(os.path.abspath(path))
        current = Path(absolute.anchor)
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryOptimizerComparisonVerificationError(
                    f"{label} parent contains a link or non-directory component"
                )
        metadata = absolute.lstat()
    except LibraryOptimizerComparisonVerificationError:
        raise
    except OSError as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryOptimizerComparisonVerificationError(
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
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if len(raw) > limit:
            raise LibraryOptimizerComparisonVerificationError(
                f"{label} exceeds its byte limit"
            )
        if identity_before != identity_after:
            raise LibraryOptimizerComparisonVerificationError(
                f"{label} changed while read"
            )
        return raw
    except OSError as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"cannot read {label}"
        ) from exc
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
        raise LibraryOptimizerComparisonVerificationError(
            "cannot resolve repository_root"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise LibraryOptimizerComparisonVerificationError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def _require_fields(label: str, value: object, expected: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} has the wrong fields"
        )
    return value


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not one lowercase SHA-256 string"
        )
    return value


def _require_false_fields(
    label: str, value: Mapping[str, object], names: tuple[str, ...]
) -> None:
    for name in names:
        if value.get(name) is not False:
            raise LibraryOptimizerComparisonVerificationError(
                f"{label} field {name!r} must remain false"
            )


def _load_canonical_json(
    path: Path,
    *,
    label: str,
    limit: int,
    expected_sha256: str,
) -> tuple[bytes, dict[str, object]]:
    raw = _safe_file(path, label=label, limit=limit)
    if _sha256(raw) != expected_sha256:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} artifact hash drifted"
        )
    value = _decode_document(raw, label, limit=limit)
    if canonical_verification_receipt_bytes(value, limit=limit) != raw:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not canonical"
        )
    return raw, value


def _require_kernel_sources(root: Path) -> list[dict[str, object]]:
    identities: list[dict[str, object]] = []
    modules: dict[str, object] = {}
    for module_name, relative, expected_hash in _KERNEL_SOURCES:
        raw = _safe_file(
            root / relative,
            label=f"kernel source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256(raw) != expected_hash:
            raise LibraryOptimizerComparisonVerificationError(
                f"kernel source {relative.as_posix()!r} drifted"
            )
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", None)
        if type(source) is not str:
            raise LibraryOptimizerComparisonVerificationError(
                f"cannot identify kernel module {module_name!r}"
            )
        try:
            actual = Path(source).resolve(strict=True)
            wanted = (root / relative).resolve(strict=True)
        except OSError as exc:
            raise LibraryOptimizerComparisonVerificationError(
                f"cannot resolve kernel module {module_name!r}"
            ) from exc
        if actual != wanted:
            raise LibraryOptimizerComparisonVerificationError(
                f"kernel module {module_name!r} origin drifted"
            )
        modules[module_name] = module
        identities.append(
            {
                "module": module_name,
                "path": relative.as_posix(),
                "sha256": expected_hash,
            }
        )
    codec = modules["peano_lab.kernel.artifact_codec"]
    checker = modules["peano_lab.kernel.checker"]
    formulas = modules["peano_lab.kernel.formulas"]
    proofs = modules["peano_lab.kernel.proofs"]
    if (
        getattr(codec, "decode_artifact", None) is not decode_artifact
        or getattr(codec, "encode_artifact_bounded", None)
        is not encode_artifact_bounded
        or getattr(codec, "encode_formula", None) is not encode_formula
        or getattr(codec, "encode_proof", None) is not encode_proof
        or getattr(checker, "check", None) is not check
        or getattr(formulas, "Formula", None) is not Formula
        or getattr(proofs, "Proof", None) is not Proof
        or getattr(proofs, "Cut", None) is not Cut
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "captured kernel callable or class identity drifted"
        )
    return identities


def _load_fixed_inputs(root: Path) -> dict[str, object]:
    schema_raw, schema = _load_canonical_json(
        root / _SCHEMA_RELATIVE,
        label="A2.3a producer schema",
        limit=MAX_SCHEMA_BYTES,
        expected_sha256=PRODUCER_SOURCE_FILES[0][2],
    )
    if (
        _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != SCHEMA_SEMANTIC_SHA256
        or schema.get("format")
        != "peano-hydra-library-optimizer-comparison-pilot-schema"
        or schema.get("id")
        != "peano-hydra-library-optimizer-comparison-pilot-v1"
        or schema.get("v") != 1
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "A2.3a producer schema semantic identity drifted"
        )
    for relative, size, expected_hash in PRODUCER_SOURCE_FILES:
        raw = _safe_file(
            root / relative,
            label=f"producer source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != size or _sha256(raw) != expected_hash:
            raise LibraryOptimizerComparisonVerificationError(
                f"producer source {relative.as_posix()!r} drifted"
            )
    _audit_raw, audit = _load_canonical_json(
        root / _AUDIT_RELATIVE,
        label="fixed A2.1 dependency audit",
        limit=MAX_DOCUMENT_BYTES,
        expected_sha256=AUDIT_ARTIFACT_SHA256,
    )
    _rebuild_raw, rebuild = _load_canonical_json(
        root / _REBUILD_RELATIVE,
        label="fixed A2.2 construction rebuild",
        limit=MAX_DOCUMENT_BYTES,
        expected_sha256=REBUILD_ARTIFACT_SHA256,
    )
    _manifest_raw, manifest = _load_canonical_json(
        root / _REPLAY_MANIFEST_RELATIVE,
        label="fixed replay manifest",
        limit=MAX_DOCUMENT_BYTES,
        expected_sha256=REPLAY_MANIFEST_ARTIFACT_SHA256,
    )
    _load_canonical_json(
        root / _REPLAY_REPORT_RELATIVE,
        label="fixed replay report",
        limit=MAX_DOCUMENT_BYTES,
        expected_sha256=REPLAY_REPORT_ARTIFACT_SHA256,
    )
    if (
        audit.get("root_sha256") != AUDIT_ROOT_SHA256
        or not isinstance(audit.get("theorem_records"), dict)
        or audit["theorem_records"].get("root_sha256")
        != AUDIT_THEOREM_RECORD_ROOT_SHA256
        or rebuild.get("root_sha256") != REBUILD_ROOT_SHA256
        or not isinstance(rebuild.get("theorem_records"), dict)
        or rebuild["theorem_records"].get("root_sha256")
        != REBUILD_THEOREM_RECORD_ROOT_SHA256
        or manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "one fixed upstream semantic root drifted"
        )
    return {
        "audit": audit,
        "kernel_sources": _require_kernel_sources(root),
        "manifest": manifest,
        "rebuild": rebuild,
        "schema": schema,
        "schema_artifact_sha256": _sha256(schema_raw),
    }


def _rows_by_name(
    document: Mapping[str, object], label: str, *, expected_count: int | None = None
) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list or (expected_count is not None and len(rows) != expected_count):
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} theorem rows are malformed"
        )
    result: dict[str, dict[str, object]] = {}
    previous = -1
    for row in rows:
        if (
            type(row) is not dict
            or type(row.get("index")) is not int
            or row["index"] <= previous
            or type(row.get("name")) is not str
            or row["name"] in result
        ):
            raise LibraryOptimizerComparisonVerificationError(
                f"{label} theorem order is malformed"
            )
        previous = row["index"]
        result[row["name"]] = row
    return result


def _validate_producer_source_state(
    value: object, *, root: Path
) -> dict[str, object]:
    state = _require_fields(
        "producer source state",
        value,
        {
            "commit_sha1",
            "files",
            "format",
            "git_verified",
            "root_preimage",
            "root_sha256",
            "tree_sha1",
            "v",
        },
    )
    if (
        state.get("format") != PRODUCER_SOURCE_STATE_FORMAT
        or state.get("v") != 1
        or state.get("git_verified") is not False
        or type(state.get("commit_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(state["commit_sha1"]) is None
        or type(state.get("tree_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(state["tree_sha1"]) is None
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "producer source state identity is malformed"
        )
    source_rows = state.get("files")
    if type(source_rows) is not list or len(source_rows) != len(PRODUCER_SOURCE_FILES):
        raise LibraryOptimizerComparisonVerificationError(
            "producer source state has the wrong file list"
        )
    for row, (relative, size, digest) in zip(
        source_rows, PRODUCER_SOURCE_FILES, strict=True
    ):
        if type(row) is not dict or row != {
            "bytes": size,
            "path": relative.as_posix(),
            "sha256": digest,
        }:
            raise LibraryOptimizerComparisonVerificationError(
                "producer source state does not bind the four frozen sources"
            )
        raw = _safe_file(
            root / relative,
            label=f"producer source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != size or _sha256(raw) != digest:
            raise LibraryOptimizerComparisonVerificationError(
                f"live producer source {relative.as_posix()!r} drifted"
            )
    body = {
        key: item
        for key, item in state.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    if (
        state.get("root_preimage") != preimage
        or state.get("root_sha256")
        != _sha256_json(preimage, limit=MAX_SCHEMA_BYTES)
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "producer source state root is malformed"
        )
    return deepcopy(state)


def _proof_tree_metrics(proof: Proof) -> dict[str, int]:
    """Count structural proof occurrences without the producer's metrics code."""

    if not isinstance(proof, Proof):
        raise TypeError("proof must be one kernel Proof")
    node_count = 0
    cut_count = 0
    maximum_depth = 0
    pending: list[tuple[Proof, int]] = [(proof, 1)]
    while pending:
        node, depth = pending.pop()
        node_count += 1
        if node_count > MAX_PROOF_NODES or depth > MAX_PROOF_DEPTH:
            raise LibraryOptimizerComparisonVerificationError(
                "proof exceeds independent structural limits"
            )
        maximum_depth = max(maximum_depth, depth)
        if type(node) is Cut:
            cut_count += 1
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, Proof):
                pending.append((child, depth + 1))
    return {
        "artifact_bytes": 0,
        "cut_nodes": cut_count,
        "proof_depth": maximum_depth,
        "proof_nodes": node_count,
    }


def _inspect_artifact(
    raw: bytes,
    *,
    label: str,
    expected_artifact_sha256: str | None = None,
    expected_fuel: int | None = None,
    expected_formula_sha256: str | None = None,
    expected_proof_sha256: str | None = None,
) -> tuple[Formula, dict[str, object]]:
    if type(raw) is not bytes or not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not bounded artifact bytes"
        )
    digest = _sha256(raw)
    if expected_artifact_sha256 is not None and digest != expected_artifact_sha256:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} artifact hash differs"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=MAX_PROOF_NODES,
            max_depth=MAX_PROOF_DEPTH,
        )
        canonical = encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        formula_digest = _sha256(encode_formula(target))
        proof_digest = _sha256(encode_proof(proof))
    except Exception as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"cannot canonically decode {label}"
        ) from exc
    if canonical != raw:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not the canonical artifact encoding"
        )
    if type(fuel) is not int or fuel <= 0:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} has non-positive fuel"
        )
    if expected_fuel is not None and fuel != expected_fuel:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} fuel differs"
        )
    if expected_formula_sha256 is not None and formula_digest != expected_formula_sha256:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} formula hash differs"
        )
    if expected_proof_sha256 is not None and proof_digest != expected_proof_sha256:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} proof hash differs"
        )
    try:
        accepted = check((), proof, target)
    except Exception as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"kernel checking {label} failed closed"
        ) from exc
    if accepted is not True:
        raise LibraryOptimizerComparisonVerificationError(
            f"kernel rejected {label} from the empty context"
        )
    metrics = _proof_tree_metrics(proof)
    metrics["artifact_bytes"] = len(raw)
    return target, {
        "artifact_sha256": digest,
        "formula_sha256": formula_digest,
        "fuel": fuel,
        "kernel_accepted": True,
        "kernel_context": "empty",
        "metrics": metrics,
        "proof_term_sha256": proof_digest,
    }


def _comparison_record(candidate: Mapping[str, object]) -> tuple[str, int, str, dict[str, int]]:
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
        or type(metrics.get("artifact_bytes")) is not int
        or metrics["artifact_bytes"] <= 0
        or type(metrics.get("proof_nodes")) is not int
        or metrics["proof_nodes"] <= 0
        or type(metrics.get("proof_depth")) is not int
        or metrics["proof_depth"] <= 0
        or type(metrics.get("cut_nodes")) is not int
        or metrics["cut_nodes"] < 0
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "candidate comparison record is malformed"
        )
    return candidate_id, kind_order, digest, metrics


def _componentwise_nondominated(
    candidates: tuple[Mapping[str, object], ...]
) -> tuple[str, ...]:
    parsed = tuple(_comparison_record(candidate) for candidate in candidates)
    if (
        not parsed
        or len({item[0] for item in parsed}) != len(parsed)
        or len({item[1] for item in parsed}) != len(parsed)
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "comparison universe is empty or non-unique"
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


def _select_representative(candidates: tuple[Mapping[str, object], ...]) -> str:
    parsed = tuple(_comparison_record(candidate) for candidate in candidates)
    if not parsed:
        raise LibraryOptimizerComparisonVerificationError(
            "frontier cannot be empty"
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


def _closure(
    root_name: str,
    *,
    replay_rows: Mapping[str, dict[str, object]],
    overrides: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if root_name not in replay_rows:
        raise LibraryOptimizerComparisonVerificationError(
            f"unknown closure root {root_name!r}"
        )
    root_row = replay_rows[root_name]
    pending = list(
        overrides.get(root_name, tuple(root_row.get("declared_dependencies", ())))
    )
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = replay_rows.get(name)
        if row is None:
            raise LibraryOptimizerComparisonVerificationError(
                f"closure contains unknown theorem {name!r}"
            )
        dependencies = overrides.get(name, tuple(row.get("declared_dependencies", ())))
        if (
            type(dependencies) is not tuple
            or not all(type(item) is str and item for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise LibraryOptimizerComparisonVerificationError(
                f"dependency vector for {name!r} is malformed"
            )
        seen.add(name)
        pending.extend(dependencies)
    if root_name in seen:
        raise LibraryOptimizerComparisonVerificationError(
            f"closure for {root_name!r} contains its root"
        )
    return tuple(sorted(seen, key=lambda name: replay_rows[name]["index"]))


def _lf_hash(names: tuple[str, ...]) -> str:
    return _sha256(
        ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    )


def _verify_surface(
    value: object,
    *,
    candidate_id: str,
    dependencies: tuple[str, ...],
    closure: tuple[str, ...],
) -> None:
    surface = _require_fields("dependency surface", value, _SURFACE_FIELDS)
    expected = {
        "direct_dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": _lf_hash(dependencies),
        "direct_dependency_count": len(dependencies),
        "surface_basis": SURFACE_BASES[candidate_id],
        "transitive_closure_count": len(closure),
        "transitive_closure_dependencies_in_replay_order": list(closure),
        "transitive_closure_lf_sha256": _lf_hash(closure),
    }
    if surface != expected:
        raise LibraryOptimizerComparisonVerificationError(
            f"dependency surface for {candidate_id!r} differs"
        )


def _decode_base64(value: object, *, label: str) -> bytes:
    if type(value) is not str or len(value) > 4 * ((MAX_ARTIFACT_BYTES + 2) // 3):
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not bounded base64"
        )
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not canonical base64"
        ) from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} is not canonical base64"
        )
    return raw


def _safe_replay_artifact(root: Path, relative: object) -> bytes:
    if type(relative) is not str:
        raise LibraryOptimizerComparisonVerificationError(
            "retained artifact path is not a string"
        )
    parsed = Path(relative)
    if (
        parsed.is_absolute()
        or parsed.parts[:1] != ("certificates",)
        or ".." in parsed.parts
        or parsed.as_posix() != relative
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "retained artifact path is unsafe"
        )
    return _safe_file(
        root / _REPLAY_ROOT_RELATIVE / parsed,
        label=f"retained replay artifact {relative!r}",
        limit=MAX_ARTIFACT_BYTES,
    )


def _expected_layers(
    node_names: tuple[str, ...],
    *,
    replay_rows: Mapping[str, dict[str, object]],
    overrides: Mapping[str, tuple[str, ...]],
) -> tuple[tuple[int, ...], ...]:
    positions = {name: index for index, name in enumerate(node_names)}
    depths: dict[int, int] = {}
    for name in node_names:
        node_id = positions[name]
        dependencies = overrides.get(
            name, tuple(replay_rows[name].get("declared_dependencies", ()))
        )
        try:
            dependency_ids = tuple(positions[item] for item in dependencies)
        except KeyError as exc:
            raise LibraryOptimizerComparisonVerificationError(
                "layered bundle omits one dependency"
            ) from exc
        if any(item >= node_id for item in dependency_ids):
            raise LibraryOptimizerComparisonVerificationError(
                "layered dependency is not earlier in replay order"
            )
        depths[node_id] = (
            0 if not dependency_ids else 1 + max(depths[item] for item in dependency_ids)
        )
    grouped: list[list[int]] = [
        [] for _ in range(1 + max(depths.values(), default=0))
    ]
    for node_id in sorted(depths):
        grouped[depths[node_id]].append(node_id)
    return tuple(tuple(layer) for layer in grouped)


def _verify_layered_bundle(
    value: object,
    *,
    root_name: str,
    layered_closure: tuple[str, ...],
    replay_rows: Mapping[str, dict[str, object]],
    overrides: Mapping[str, tuple[str, ...]],
) -> None:
    bundle = _require_fields("layered bundle", value, _LAYERED_BUNDLE_FIELDS)
    node_names = tuple(
        sorted(
            (*layered_closure, root_name),
            key=lambda name: replay_rows[name]["index"],
        )
    )
    layers = _expected_layers(
        node_names, replay_rows=replay_rows, overrides=overrides
    )
    expected_edges = sum(
        len(overrides.get(name, tuple(replay_rows[name]["declared_dependencies"])))
        for name in node_names
    )
    if (
        bundle.get("compiler_result_type") != "LayeredReplayCandidate"
        or bundle.get("node_count") != len(node_names)
        or bundle.get("node_names_in_replay_order") != list(node_names)
        or bundle.get("node_names_lf_sha256") != _lf_hash(node_names)
        or bundle.get("dependency_edge_count") != expected_edges
        or bundle.get("layer_count") != len(layers)
        or bundle.get("layers") != [list(layer) for layer in layers]
        or type(bundle.get("maximum_package_formula_depth")) is not int
        or bundle["maximum_package_formula_depth"] <= 0
        or type(bundle.get("package_formula_occurrences")) is not int
        or bundle["package_formula_occurrences"] <= 0
    ):
        raise LibraryOptimizerComparisonVerificationError(
            f"layered diagnostics for {root_name!r} differ"
        )
    body_sources = bundle.get("body_sources")
    if type(body_sources) is not list or len(body_sources) != len(node_names):
        raise LibraryOptimizerComparisonVerificationError(
            "layered body-source list differs"
        )
    for name, source in zip(node_names, body_sources, strict=True):
        expected_dependencies = overrides.get(
            name, tuple(replay_rows[name]["declared_dependencies"])
        )
        if (
            type(source) is not dict
            or source.get("name") != name
            or source.get("index") != replay_rows[name]["index"]
            or source.get("dependencies") != list(expected_dependencies)
            or type(source.get("body_certificate_sha256")) is not str
            or _SHA256_RE.fullmatch(source["body_certificate_sha256"]) is None
            or source.get("identity_metrics_comparable") is not False
            or source.get("source_identity_metrics_transportable") is not False
        ):
            raise LibraryOptimizerComparisonVerificationError(
                f"layered body-source row for {name!r} differs"
            )


def _verify_root_inputs(value: object, *, schema: Mapping[str, object]) -> None:
    inputs = _require_fields(
        "pilot inputs",
        value,
        {
            "construction_rebuild",
            "dependency_audit",
            "implementation",
            "layered_replay_limits",
            "replay_pack",
        },
    )
    expected_audit = {
        "artifact_path": _AUDIT_RELATIVE.as_posix(),
        "artifact_sha256": AUDIT_ARTIFACT_SHA256,
        "root_sha256": AUDIT_ROOT_SHA256,
        "theorem_record_root_sha256": AUDIT_THEOREM_RECORD_ROOT_SHA256,
    }
    expected_rebuild = {
        "artifact_path": _REBUILD_RELATIVE.as_posix(),
        "artifact_sha256": REBUILD_ARTIFACT_SHA256,
        "root_sha256": REBUILD_ROOT_SHA256,
        "theorem_record_root_sha256": REBUILD_THEOREM_RECORD_ROOT_SHA256,
    }
    expected_replay = {
        "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
        "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
        "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
    }
    expected_implementation = [
        {"module": module, "path": path, "sha256": digest}
        for module, path, digest in _PRODUCER_IMPLEMENTATION
    ]
    limits = schema.get("limits")
    if type(limits) is not dict or type(limits.get("layered_replay")) is not dict:
        raise LibraryOptimizerComparisonVerificationError(
            "fixed schema has no layered limits"
        )
    if (
        inputs.get("dependency_audit") != expected_audit
        or inputs.get("construction_rebuild") != expected_rebuild
        or inputs.get("replay_pack") != expected_replay
        or inputs.get("implementation") != expected_implementation
        or inputs.get("layered_replay_limits") != limits["layered_replay"]
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "pilot fixed-input identity differs"
        )


def _verify_artifact_row(
    artifact: object,
    *,
    candidate_id: str,
    kind_order: int,
    raw: bytes,
    expected_artifact_sha256: str,
    expected_fuel: int | None,
    expected_formula_sha256: str,
    expected_proof_sha256: str | None,
    expected_source: dict[str, object],
    dependencies: tuple[str, ...],
    closure: tuple[str, ...],
    label: str,
) -> tuple[Formula, dict[str, object]]:
    expected_fields = set(_ARTIFACT_COMMON_FIELDS)
    if candidate_id == "layered-closure":
        expected_fields.add("artifact_base64")
    row = _require_fields(label, artifact, expected_fields)
    if (
        row.get("candidate_id") != candidate_id
        or row.get("candidate_kind_order") != kind_order
        or row.get("certificate_representation") != CERTIFICATE_REPRESENTATION
        or row.get("logic_mode") != LOGIC_MODE
        or row.get("kernel_accepted") is not True
        or row.get("kernel_context") != "empty"
        or row.get("source") != expected_source
    ):
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} metadata differs"
        )
    _verify_surface(
        row.get("surface"),
        candidate_id=candidate_id,
        dependencies=dependencies,
        closure=closure,
    )
    target, independently_observed = _inspect_artifact(
        raw,
        label=label,
        expected_artifact_sha256=expected_artifact_sha256,
        expected_fuel=expected_fuel,
        expected_formula_sha256=expected_formula_sha256,
        expected_proof_sha256=expected_proof_sha256,
    )
    recorded_observation = {
        "artifact_sha256": row.get("artifact_sha256"),
        "formula_sha256": row.get("formula_sha256"),
        "fuel": row.get("fuel"),
        "kernel_accepted": row.get("kernel_accepted"),
        "kernel_context": row.get("kernel_context"),
        "metrics": row.get("metrics"),
        "proof_term_sha256": row.get("proof_term_sha256"),
    }
    if recorded_observation != independently_observed:
        raise LibraryOptimizerComparisonVerificationError(
            f"{label} independent observation differs from its record"
        )
    return target, {
        "artifact_sha256": independently_observed["artifact_sha256"],
        "candidate_id": candidate_id,
        "candidate_kind_order": kind_order,
        "formula_sha256": independently_observed["formula_sha256"],
        "fuel": independently_observed["fuel"],
        "kernel_accepted": True,
        "kernel_context": "empty",
        "metrics": independently_observed["metrics"],
        "proof_term_sha256": independently_observed["proof_term_sha256"],
    }


def _verify_comparison(
    value: object, *, artifacts: tuple[Mapping[str, object], ...]
) -> tuple[tuple[str, ...], str]:
    comparison = _require_fields("pilot comparison", value, _COMPARISON_FIELDS)
    if tuple(
        (artifact.get("candidate_id"), artifact.get("candidate_kind_order"))
        for artifact in artifacts
    ) != CANDIDATE_KINDS:
        raise LibraryOptimizerComparisonVerificationError(
            "candidate universe order differs"
        )
    frontier = _componentwise_nondominated(artifacts)
    frontier_set = set(frontier)
    frontier_candidates = tuple(
        artifact
        for artifact in artifacts
        if artifact.get("candidate_id") in frontier_set
    )
    representative = _select_representative(frontier_candidates)
    expected = {
        "axes_in_componentwise_order": list(COMPARISON_AXES),
        "candidate_universe_complete": True,
        "candidate_universe_ids_in_order": [item[0] for item in CANDIDATE_KINDS],
        "claim": "bounded-three-candidate-pilot-only",
        "global_best_claim": False,
        "minimality_claim": False,
        "nondominated_candidate_ids_in_input_order": list(frontier),
        "representative_candidate_id": representative,
        "representative_tie_break": list(REPRESENTATIVE_TIE_BREAK),
    }
    if comparison != expected:
        raise LibraryOptimizerComparisonVerificationError(
            "pilot comparison differs from independent recomputation"
        )
    return frontier, representative


def _record_hash(row: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: value for key, value in row.items() if key != "record_sha256"}
    )


def verify_optimizer_comparison_pilot(
    candidate: object,
    *,
    producer_source_state: object,
    candidate_raw: bytes | None = None,
    producer_source_state_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Independently verify one canonical A2.3a candidate and return a receipt.

    ``candidate_raw`` is required when the caller needs the receipt to bind the
    exact transport bytes.  Omitting it is useful only for already-decoded,
    compact unit fixtures; the value is canonically encoded before hashing.
    """

    _require_runtime_import_boundary()
    root = _repository_root(repository_root)
    fixed = _load_fixed_inputs(root)
    if type(candidate) is not dict:
        raise LibraryOptimizerComparisonVerificationError(
            "optimizer/comparison candidate must be one object"
        )
    _validate_json(candidate)
    canonical_candidate = canonical_verification_receipt_bytes(candidate)
    if candidate_raw is None:
        candidate_raw = canonical_candidate
    elif type(candidate_raw) is not bytes or candidate_raw != canonical_candidate:
        raise LibraryOptimizerComparisonVerificationError(
            "candidate transport bytes are not canonical"
        )

    source_state = _validate_producer_source_state(producer_source_state, root=root)
    canonical_source_state = canonical_verification_receipt_bytes(
        source_state, limit=MAX_SCHEMA_BYTES
    )
    if producer_source_state_raw is None:
        producer_source_state_raw = canonical_source_state
    elif (
        type(producer_source_state_raw) is not bytes
        or producer_source_state_raw != canonical_source_state
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "producer source-state transport bytes are not canonical"
        )
    expected_root_fields = _ROOT_BODY_FIELDS | {
        "root_preimage",
        "root_sha256",
        "theorems",
    }
    document = _require_fields("pilot root", candidate, expected_root_fields)
    _require_false_fields("pilot root", document, _ROOT_FALSE_FIELDS)
    if (
        document.get("format") != PILOT_FORMAT
        or document.get("id") != PILOT_ID
        or document.get("v") != PILOT_VERSION
        or document.get("logic_mode") != LOGIC_MODE
        or document.get("status") != CANDIDATE_STATUS
        or document.get("theorem_count") != len(EXPECTED_THEOREMS)
        or document.get("producer_source_state") != source_state
        or document.get("producer_source_state_sha256")
        != _sha256_json(source_state, limit=MAX_SCHEMA_BYTES)
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "pilot root identity or source-state binding differs"
        )
    schema_identity = document.get("schema")
    expected_schema_identity = {
        "artifact_sha256": PRODUCER_SOURCE_FILES[0][2],
        "format": "peano-hydra-library-optimizer-comparison-pilot-schema",
        "id": "peano-hydra-library-optimizer-comparison-pilot-v1",
        "sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    if schema_identity != expected_schema_identity:
        raise LibraryOptimizerComparisonVerificationError(
            "pilot schema identity differs"
        )
    _verify_root_inputs(document.get("inputs"), schema=fixed["schema"])

    audit_rows = _rows_by_name(fixed["audit"], "A2.1", expected_count=384)
    rebuild_rows = _rows_by_name(fixed["rebuild"], "A2.2", expected_count=3)
    replay_rows = _rows_by_name(fixed["manifest"], "replay manifest", expected_count=384)
    overrides = {
        name: tuple(row.get("candidate_direct_dependencies", ()))
        for name, row in rebuild_rows.items()
    }
    if tuple((row["index"], row["name"]) for row in rebuild_rows.values()) != EXPECTED_THEOREMS:
        raise LibraryOptimizerComparisonVerificationError(
            "fixed A2.2 theorem set differs"
        )

    result_rows = document.get("theorems")
    if type(result_rows) is not list or len(result_rows) != len(EXPECTED_THEOREMS):
        raise LibraryOptimizerComparisonVerificationError(
            "pilot theorem list differs"
        )
    verification_rows: list[dict[str, object]] = []
    record_identities: list[dict[str, object]] = []
    candidate_record_identities: list[dict[str, object]] = []
    frontier_total = 0
    representative_counts = {candidate_id: 0 for candidate_id, _ in CANDIDATE_KINDS}

    for expected, row in zip(EXPECTED_THEOREMS, result_rows, strict=True):
        index, name = expected
        theorem = _require_fields(f"pilot theorem {name!r}", row, _THEOREM_FIELDS)
        _require_false_fields(f"pilot theorem {name!r}", theorem, _THEOREM_FALSE_FIELDS)
        if theorem.get("index") != index or theorem.get("name") != name:
            raise LibraryOptimizerComparisonVerificationError(
                "pilot theorem identity/order differs"
            )
        replay_row = replay_rows[name]
        rebuild_row = rebuild_rows[name]
        audit_row = audit_rows[name]
        if (
            replay_row.get("index") != index
            or rebuild_row.get("index") != index
            or audit_row.get("index") != index
            or audit_row.get("record_sha256")
            != rebuild_row.get("a2_1", {}).get("audit_record_sha256")
        ):
            raise LibraryOptimizerComparisonVerificationError(
                f"fixed evidence join for {name!r} differs"
            )
        original = theorem.get("original")
        expected_original = {
            "formula_sha256": replay_row["formula_sha256"],
            "statement_canonical_sha256": replay_row["statement_canonical_sha256"],
            "statement_source_sha256": replay_row["statement_source_sha256"],
        }
        if original != expected_original:
            raise LibraryOptimizerComparisonVerificationError(
                f"original theorem identity for {name!r} differs"
            )

        retained_direct = tuple(replay_row["declared_dependencies"])
        reduced_direct = tuple(rebuild_row["candidate_direct_dependencies"])
        retained_closure = _closure(name, replay_rows=replay_rows, overrides={})
        rebuild_closure = _closure(
            name, replay_rows=replay_rows, overrides={name: reduced_direct}
        )
        layered_closure = _closure(
            name, replay_rows=replay_rows, overrides=overrides
        )
        _verify_layered_bundle(
            theorem.get("layered_bundle"),
            root_name=name,
            layered_closure=layered_closure,
            replay_rows=replay_rows,
            overrides=overrides,
        )

        artifact_rows = theorem.get("artifacts")
        if type(artifact_rows) is not list or len(artifact_rows) != 3:
            raise LibraryOptimizerComparisonVerificationError(
                f"artifact universe for {name!r} differs"
            )
        retained_metadata = replay_row["artifact"]
        retained_raw = _safe_replay_artifact(root, retained_metadata["path"])
        rebuild_metadata = rebuild_row["rebuilt_certificate"]
        rebuild_raw = _decode_base64(
            rebuild_metadata.get("artifact_base64"),
            label=f"A2.2 artifact for {name!r}",
        )
        layered_raw = _decode_base64(
            artifact_rows[2].get("artifact_base64")
            if type(artifact_rows[2]) is dict
            else None,
            label=f"layered artifact for {name!r}",
        )
        raw_artifacts = (retained_raw, rebuild_raw, layered_raw)
        expected_hashes = (
            retained_metadata["sha256"],
            rebuild_metadata["artifact_sha256"],
            _sha256(layered_raw),
        )
        expected_fuels = (
            retained_metadata["fuel"],
            rebuild_metadata["fuel"],
            None,
        )
        expected_proof_hashes = (
            replay_row["proof_term_sha256"],
            rebuild_metadata["proof_term_sha256"],
            None,
        )
        expected_sources = (
            {
                "artifact_path": retained_metadata["path"],
                "manifest_record_index": index,
                "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
            },
            {
                "construction_rebuild_record_sha256": rebuild_row["record_sha256"],
                "construction_rebuild_root_sha256": REBUILD_ROOT_SHA256,
            },
            {
                "compiler_callable": (
                    "peano_lab.library.layered_replay.compile_layered_replay"
                ),
                "compiler_source_sha256": _PRODUCER_IMPLEMENTATION[0][2],
            },
        )
        dependency_vectors = (retained_direct, reduced_direct, reduced_direct)
        closures = (retained_closure, rebuild_closure, layered_closure)
        observations: list[dict[str, object]] = []
        targets: list[Formula] = []
        for position, ((candidate_id, kind_order), artifact, raw) in enumerate(
            zip(CANDIDATE_KINDS, artifact_rows, raw_artifacts, strict=True)
        ):
            target, observation = _verify_artifact_row(
                artifact,
                candidate_id=candidate_id,
                kind_order=kind_order,
                raw=raw,
                expected_artifact_sha256=expected_hashes[position],
                expected_fuel=expected_fuels[position],
                expected_formula_sha256=replay_row["formula_sha256"],
                expected_proof_sha256=expected_proof_hashes[position],
                expected_source=expected_sources[position],
                dependencies=dependency_vectors[position],
                closure=closures[position],
                label=f"{name}:{candidate_id}",
            )
            targets.append(target)
            observations.append(observation)
        if not (targets[0] == targets[1] == targets[2]):
            raise LibraryOptimizerComparisonVerificationError(
                f"candidate formulas for {name!r} differ"
            )
        if observations[2]["fuel"] != (
            FUEL_MULTIPLIER * observations[2]["metrics"]["proof_nodes"] + FUEL_OFFSET
        ):
            raise LibraryOptimizerComparisonVerificationError(
                f"layered fuel contract for {name!r} differs"
            )
        frontier, representative = _verify_comparison(
            theorem.get("comparison"), artifacts=tuple(observations)
        )
        frontier_total += len(frontier)
        representative_counts[representative] += 1

        candidate_record_hash = _record_hash(theorem)
        if theorem.get("record_sha256") != candidate_record_hash:
            raise LibraryOptimizerComparisonVerificationError(
                f"candidate theorem record hash for {name!r} differs"
            )
        candidate_record_identities.append(
            {"index": index, "name": name, "record_sha256": candidate_record_hash}
        )
        verification_row: dict[str, object] = {
            "artifacts": observations,
            "candidate_record_sha256": candidate_record_hash,
            "index": index,
            "name": name,
            "nondominated_candidate_ids_in_input_order": list(frontier),
            "representative_candidate_id": representative,
        }
        verification_row["record_sha256"] = _record_hash(verification_row)
        verification_rows.append(verification_row)
        record_identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": verification_row["record_sha256"],
            }
        )

    candidate_records_preimage = {
        "format": PILOT_RECORDS_PREIMAGE_FORMAT,
        "records": candidate_record_identities,
        "v": 1,
    }
    candidate_records_root = _sha256_json(candidate_records_preimage)
    expected_candidate_records = {
        "count": len(EXPECTED_THEOREMS),
        "preimage": candidate_records_preimage,
        "root_sha256": candidate_records_root,
    }
    if document.get("theorem_records") != expected_candidate_records:
        raise LibraryOptimizerComparisonVerificationError(
            "candidate theorem-record root differs"
        )
    body = {key: document[key] for key in _ROOT_BODY_FIELDS}
    candidate_root_preimage = {
        "format": PILOT_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": PILOT_VERSION,
    }
    candidate_root_sha = _sha256_json(candidate_root_preimage)
    if (
        document.get("root_preimage") != candidate_root_preimage
        or document.get("root_sha256") != candidate_root_sha
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "candidate document root differs"
        )

    expected_aggregate = {
        "candidate_artifact_count": 9,
        "candidate_count_per_theorem": 3,
        "cached_modular_body_count": 127,
        "cached_modular_body_direct_edges": 328,
        "cached_modular_body_maximum_proof_nodes": 373,
        "cached_modular_body_proof_nodes": 7_365,
        "nondominated_members_total": frontier_total,
        "pilot_theorem_count": 3,
        "representative_counts": representative_counts,
        "retained_public_graph_edges": 1_038,
    }
    if document.get("aggregate") != expected_aggregate:
        raise LibraryOptimizerComparisonVerificationError(
            "candidate aggregate differs from independent recomputation"
        )

    verification_records_preimage = {
        "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": record_identities,
        "v": VERIFICATION_VERSION,
    }
    verification_records = {
        "count": len(verification_rows),
        "preimage": verification_records_preimage,
        "root_sha256": _sha256_json(verification_records_preimage),
    }
    verifier_source_relative = Path(
        "training/peano_hydra/library_optimizer_comparison_verifier.py"
    )
    verifier_raw = _safe_file(
        root / verifier_source_relative,
        label="independent verifier source",
        limit=MAX_SOURCE_FILE_BYTES,
    )
    receipt_body = {
        "a2_complete": False,
        "aggregate": {
            "candidate_artifact_count": 9,
            "kernel_accepted_artifact_count": 9,
            "nondominated_members_total": frontier_total,
            "pilot_theorem_count": 3,
            "representative_counts": representative_counts,
        },
        "candidate": {
            "artifact_bytes": len(candidate_raw),
            "artifact_sha256": _sha256(candidate_raw),
            "root_sha256": candidate_root_sha,
            "theorem_record_root_sha256": candidate_records_root,
        },
        "candidate_status": CANDIDATE_STATUS,
        "dependency_vectors_complete": False,
        "evaluation_eligible": False,
        "format": VERIFICATION_FORMAT,
        "freeze_ready": False,
        "id": VERIFICATION_ID,
        "kernel_artifacts_verified": True,
        "lineage_complete": False,
        "logic_mode": LOGIC_MODE,
        "minimality_claim": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "producer_git_verified": False,
        "producer_source_state": {
            "artifact_bytes": len(producer_source_state_raw),
            "artifact_sha256": _sha256(producer_source_state_raw),
            "root_sha256": source_state["root_sha256"],
            "semantic_sha256": _sha256_json(
                source_state, limit=MAX_SCHEMA_BYTES
            ),
        },
        "producer_source_state_sha256": document["producer_source_state_sha256"],
        "proof_authority": False,
        "publication_authority": False,
        "publication_ready": False,
        "publication_union_complete": False,
        "publication_union_verified": False,
        "retrieval_eligible": False,
        "review_complete": False,
        "status": VERIFICATION_STATUS,
        "theorem_admission_authority": False,
        "theorem_count": len(verification_rows),
        "theorem_records": verification_records,
        "training_eligible": False,
        "v": VERIFICATION_VERSION,
        "verifier": {
            "bytecode_write_disabled": True,
            "import_policy": "stdlib-and-peano-kernel-only",
            "kernel_sources": fixed["kernel_sources"],
            "load_mode": "direct-source-module-without-training-package-init",
            "path": verifier_source_relative.as_posix(),
            "pycache_prefix": PYCACHE_PREFIX,
            "safe_path": True,
            "sha256": _sha256(verifier_raw),
            "site_import_disabled": True,
            "source_loader_preflight": "pathfinder-sourcefileloader-exact-origin",
            "stdlib_precedes_peano_root": True,
            "user_site_disabled": True,
        },
    }
    if set(receipt_body) != set(VERIFICATION_RECEIPT_BODY_FIELDS):
        raise LibraryOptimizerComparisonVerificationError(
            "internal verification receipt field contract drifted"
        )
    receipt_preimage = {
        "format": VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": receipt_body,
        "v": VERIFICATION_VERSION,
    }
    receipt = {
        **receipt_body,
        "root_preimage": receipt_preimage,
        "root_sha256": _sha256_json(receipt_preimage),
        "theorems": verification_rows,
    }
    canonical_verification_receipt_bytes(receipt)
    return receipt


def validate_optimizer_comparison_verification_receipt(
    value: object,
    *,
    candidate: object,
    producer_source_state: object,
    candidate_raw: bytes | None = None,
    producer_source_state_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Deep-validate a receipt by its own roots and exact kernel reconstruction."""

    receipt = _require_fields(
        "independent verification receipt", value, set(VERIFICATION_RECEIPT_FIELDS)
    )
    _require_false_fields(
        "independent verification receipt", receipt, VERIFICATION_FALSE_FIELDS
    )
    if (
        receipt.get("format") != VERIFICATION_FORMAT
        or receipt.get("id") != VERIFICATION_ID
        or receipt.get("v") != VERIFICATION_VERSION
        or receipt.get("status") != VERIFICATION_STATUS
        or receipt.get("candidate_status") != CANDIDATE_STATUS
        or receipt.get("logic_mode") != LOGIC_MODE
        or receipt.get("kernel_artifacts_verified") is not True
        or receipt.get("theorem_count") != len(EXPECTED_THEOREMS)
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "independent verification receipt identity differs"
        )
    rows = receipt.get("theorems")
    if type(rows) is not list or len(rows) != len(EXPECTED_THEOREMS):
        raise LibraryOptimizerComparisonVerificationError(
            "independent verification theorem rows differ"
        )
    record_identities: list[dict[str, object]] = []
    for (expected_index, expected_name), row in zip(
        EXPECTED_THEOREMS, rows, strict=True
    ):
        if (
            type(row) is not dict
            or set(row)
            != {
                "artifacts",
                "candidate_record_sha256",
                "index",
                "name",
                "nondominated_candidate_ids_in_input_order",
                "record_sha256",
                "representative_candidate_id",
            }
            or row.get("index") != expected_index
            or row.get("name") != expected_name
            or row.get("record_sha256") != _record_hash(row)
        ):
            raise LibraryOptimizerComparisonVerificationError(
                "independent verification theorem record differs"
            )
        record_identities.append(
            {
                "index": expected_index,
                "name": expected_name,
                "record_sha256": row["record_sha256"],
            }
        )
    records_preimage = {
        "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": record_identities,
        "v": VERIFICATION_VERSION,
    }
    expected_records = {
        "count": len(rows),
        "preimage": records_preimage,
        "root_sha256": _sha256_json(records_preimage),
    }
    if receipt.get("theorem_records") != expected_records:
        raise LibraryOptimizerComparisonVerificationError(
            "independent verification theorem-record root differs"
        )
    body = {key: receipt[key] for key in VERIFICATION_RECEIPT_BODY_FIELDS}
    preimage = {
        "format": VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": VERIFICATION_VERSION,
    }
    if (
        receipt.get("root_preimage") != preimage
        or receipt.get("root_sha256") != _sha256_json(preimage)
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "independent verification document root differs"
        )
    expected = verify_optimizer_comparison_pilot(
        candidate,
        producer_source_state=producer_source_state,
        candidate_raw=candidate_raw,
        producer_source_state_raw=producer_source_state_raw,
        repository_root=repository_root,
    )
    if receipt != expected:
        raise LibraryOptimizerComparisonVerificationError(
            "verification receipt differs from exact independent reconstruction"
        )
    return deepcopy(receipt)


def load_and_verify_optimizer_comparison_pilot(
    candidate_path: Path,
    producer_source_state_path: Path,
    *,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Strict-load a candidate plus explicit source state and verify all nine artifacts."""

    candidate_raw = _safe_file(
        candidate_path,
        label="optimizer/comparison candidate",
        limit=MAX_DOCUMENT_BYTES,
    )
    candidate = _decode_document(
        candidate_raw, "optimizer/comparison candidate", limit=MAX_DOCUMENT_BYTES
    )
    if canonical_verification_receipt_bytes(candidate) != candidate_raw:
        raise LibraryOptimizerComparisonVerificationError(
            "optimizer/comparison candidate is not canonical"
        )
    source_raw = _safe_file(
        producer_source_state_path,
        label="producer source state",
        limit=MAX_SCHEMA_BYTES,
    )
    source_state = _decode_document(
        source_raw, "producer source state", limit=MAX_SCHEMA_BYTES
    )
    if (
        canonical_verification_receipt_bytes(
            source_state, limit=MAX_SCHEMA_BYTES
        )
        != source_raw
    ):
        raise LibraryOptimizerComparisonVerificationError(
            "producer source state is not canonical"
        )
    return verify_optimizer_comparison_pilot(
        candidate,
        producer_source_state=source_state,
        candidate_raw=candidate_raw,
        producer_source_state_raw=source_raw,
        repository_root=repository_root,
    )


__all__ = [
    "LibraryOptimizerComparisonVerificationError",
    "canonical_verification_receipt_bytes",
    "load_and_verify_optimizer_comparison_pilot",
    "validate_optimizer_comparison_verification_receipt",
    "verify_optimizer_comparison_pilot",
    "VERIFICATION_FALSE_FIELDS",
    "VERIFICATION_RECEIPT_BODY_FIELDS",
    "VERIFICATION_RECEIPT_FIELDS",
]
