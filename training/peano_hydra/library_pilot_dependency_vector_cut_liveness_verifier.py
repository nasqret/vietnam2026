"""Independent encoded-tree verifier for the bounded A2.3d cut-liveness pilot.

The producer works over kernel proof objects.  This verifier deliberately does
not import it and instead performs the scientific transformation over the
canonical JSON tagged arrays carried by ``peano-lab-v2`` artifacts.  Only after
the independent byte transformation has finished are the pinned artifact codec
and intuitionistic kernel loaded to check the retained inputs and the derived
closed proof.

The receipt is deliberately narrow.  It verifies one construction-specific
direct vector for ``odd_add_odd``.  It does not establish logical dependency
necessity, minimum cardinality, best-known status, publication, graph mutation,
authority, eligibility, or A2 completion.
"""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping, Sequence


VERIFICATION_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-cut-liveness-"
    "independent-verification-v1"
)
VERIFICATION_VERSION = 1
VERIFICATION_ID = (
    "independent-peano-hydra-l0-pilot-dependency-vector-cut-liveness-"
    "verification-v1"
)
VERIFICATION_STATUS = "passed"
VERIFICATION_ROOT_PREIMAGE_FORMAT = f"{VERIFICATION_FORMAT}-root-preimage-v1"

CANDIDATE_FORMAT = "peano-hydra-library-pilot-dependency-vector-cut-liveness-v1"
CANDIDATE_VERSION = 1
CANDIDATE_ID = "peano-hydra-l0-pilot-dependency-vector-cut-liveness-candidate-v1"
CANDIDATE_STATUS = (
    "candidate-only-bounded-one-root-proof-producing-cut-liveness-normalization"
)
CANDIDATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-cut-liveness-root-preimage-v1"
)

SCHEMA_FORMAT = "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema"
SCHEMA_ID = "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema-v1"
SCHEMA_RELATIVE = Path(
    "training/peano_hydra/"
    "library-pilot-dependency-vector-cut-liveness-schema-v1.json"
)
SCHEMA_SOURCE_BYTES = 12_566
SCHEMA_SOURCE_SHA256 = (
    "388190b4235b9892b38193714b0331a35b6c533c0605072c5d0663ad9cd9c0aa"
)
SCHEMA_SEMANTIC_SHA256 = (
    "9e8887072cc6051cf9cb9177609ab31aed35ca305a42c7d9c22d4ac339b6f5c5"
)
SCHEMA_CLAIM_BOUNDARY_SHA256 = (
    "0bcea142f7b5aa2199783d03ad51e19330a0deda505c561cb0082d2bc31a16de"
)

LOGIC_MODE = "intuitionistic"
CERTIFICATE_REPRESENTATION = "peano-lab-v2"
EXPECTED_INDEX = 256
EXPECTED_NAME = "odd_add_odd"
INPUT_DEPENDENCIES = (
    "mul_add",
    "add_succ_left",
    "add_assoc",
    "add_comm",
)
DERIVED_DEPENDENCIES = ("mul_add", "add_comm")
INNER_FIRST_DEPENDENCIES = tuple(reversed(INPUT_DEPENDENCIES))
EXPECTED_INNER_FIRST_COUNTS = (2, 0, 0, 1)
EXPECTED_INNER_FIRST_OUTCOMES = (
    ("add_comm", "retained-used"),
    ("add_assoc", "deleted-vacuous"),
    ("add_succ_left", "deleted-vacuous"),
    ("mul_add", "retained-used"),
)
INPUT_VECTOR_LF_SHA256 = (
    "9bb59dbdeb07badb9f8ca9d0cc951b71f38dbf7c3edcb1b189d53efcba1708cc"
)
DERIVED_VECTOR_LF_SHA256 = (
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

REPLAY_ROOT = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
MANIFEST_RELATIVE = REPLAY_ROOT / "manifest.json"
MANIFEST_BYTES = 3_241_451
MANIFEST_SHA256 = (
    "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
)
MANIFEST_ROOT_SHA256 = (
    "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
)
REPLAY_ROOT_SHA256 = (
    "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
)
REPLAY_THEOREM_COUNT = 384
REPORT_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1-report.json")
REPORT_BYTES = 828
REPORT_SHA256 = (
    "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"
)

ROOT_ARTIFACT_RELATIVE = REPLAY_ROOT / (
    "certificates/0256-odd_add_odd-"
    "7ecd5c3f4ac81e800fc5d14b07758681b78f66a868d3d265a811c725aa6558c7.pl2"
)
ROOT_ARTIFACT_BYTES = 14_977
ROOT_ARTIFACT_SHA256 = (
    "7ecd5c3f4ac81e800fc5d14b07758681b78f66a868d3d265a811c725aa6558c7"
)
ROOT_SOURCE_FUEL = 2_432
ROOT_FORMULA_SHA256 = (
    "4d2aa6b4e387657e562641830dab2953890b5493d6e6858b6c36d73b06786c31"
)
ROOT_PROOF_SHA256 = (
    "0199da96fdf6834e9c1affbc343a62e312c497c9a9c014904bf8cdd8ce5f5f38"
)

DEPENDENCY_INPUTS = (
    {
        "artifact_bytes": 3_447,
        "artifact_path": (
            "certificates/0007-mul_add-"
            "aeabac97da97840a927c69265493c8a2355b711fa9fdc37b5c482b530b057cb7.pl2"
        ),
        "artifact_sha256": (
            "aeabac97da97840a927c69265493c8a2355b711fa9fdc37b5c482b530b057cb7"
        ),
        "formula_sha256": (
            "6c7d695dfd0c3b56e49507b7f510182794963f91ab9e5f1466dc40f145a7a0a5"
        ),
        "index": 7,
        "name": "mul_add",
        "proof_sha256": (
            "c32deba7cbdcfff28fe47fc2f2515cbb684f754c9b6b96860c8c89b02dfdf1ac"
        ),
    },
    {
        "artifact_bytes": 1_023,
        "artifact_path": (
            "certificates/0001-add_succ_left-"
            "09d9cd46daa969e93fdb83d9119f8c14fb226f11356acc69882759e270371983.pl2"
        ),
        "artifact_sha256": (
            "09d9cd46daa969e93fdb83d9119f8c14fb226f11356acc69882759e270371983"
        ),
        "formula_sha256": (
            "9c089dd32a335c2b820b4ea3c0902821860bcb80bbf5c306c0fdad15c8da1756"
        ),
        "index": 1,
        "name": "add_succ_left",
        "proof_sha256": (
            "769124fe14b55a54436635de5be893ee15ba997d5db435c159a3d00e611907d7"
        ),
    },
    {
        "artifact_bytes": 1_368,
        "artifact_path": (
            "certificates/0003-add_assoc-"
            "a239a7199c5294b1060e7f9a8244cd290036b5bc63f22ec767f68c9821026744.pl2"
        ),
        "artifact_sha256": (
            "a239a7199c5294b1060e7f9a8244cd290036b5bc63f22ec767f68c9821026744"
        ),
        "formula_sha256": (
            "4c7b9113d46e6c5646a169320d17464dcf78c0c97be26f4ef03a9d7f3afd3171"
        ),
        "index": 3,
        "name": "add_assoc",
        "proof_sha256": (
            "bc649ea7f7bb208ab963a2cc5137fc00b005d261a35d447a065dd094faa7399f"
        ),
    },
    {
        "artifact_bytes": 2_551,
        "artifact_path": (
            "certificates/0002-add_comm-"
            "e7094296018260b6c03fb3846c61bacc94e8d0f39739379326db409d99aeef9f.pl2"
        ),
        "artifact_sha256": (
            "e7094296018260b6c03fb3846c61bacc94e8d0f39739379326db409d99aeef9f"
        ),
        "formula_sha256": (
            "25b3cc29a1427896f1aa3935bc167b449d4501668be477e477180454ba292f94"
        ),
        "index": 2,
        "name": "add_comm",
        "proof_sha256": (
            "1d083e7da855b6e22c63dc081cd86cffa5beb4690f4298e6c804fe8717c4baaa"
        ),
    },
)

OUTPUT_ARTIFACT_BYTES = 11_958
OUTPUT_ARTIFACT_SHA256 = (
    "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22"
)
OUTPUT_PROOF_SHA256 = (
    "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4"
)
OUTPUT_FUEL = 1_936
OUTPUT_PROOF_NODES = 240
OUTPUT_PROOF_DEPTH = 30
OUTPUT_CUT_NODES = 5
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16

MAX_SCHEMA_BYTES = 262_144
MAX_DOCUMENT_BYTES = 1_048_576
MAX_ARTIFACT_BYTES = 65_536
MAX_JSON_DEPTH = 64
MAX_JSON_ITEMS = 100_000
MAX_PROOF_NODES = 10_000
MAX_PROOF_DEPTH = 128
MAX_TRANSFORM_VISITS = 50_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
PYCACHE_PREFIX = "/proc/peano-hydra-a23d-cut-liveness-disabled-pycache"

BROAD_FALSE_FIELDS = (
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
    "human_review_complete",
    "lineage_complete",
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

VERIFICATION_FALSE_FIELDS = (
    *BROAD_FALSE_FIELDS,
    "dependency_necessity_independently_verified",
    "execution_receipt_bound",
    "global_optimized_vector_audit_complete",
    "logical_minimality_independently_verified",
    "producer_semantics_independently_verified",
)

_CANDIDATE_TOP_LEVEL_FIELDS = frozenset(
    (
        *BROAD_FALSE_FIELDS,
        "aggregate",
        "algorithm",
        "bounded_one_root_protocol_executed",
        "format",
        "id",
        "implementation",
        "inputs",
        "logic_mode",
        "root_preimage",
        "root_sha256",
        "schema",
        "status",
        "theorem",
        "theorem_count",
        "theorem_record_root_sha256",
        "v",
    )
)
_CANDIDATE_THEOREM_FIELDS = frozenset(
    (
        *BROAD_FALSE_FIELDS,
        "bounded_one_root_cut_liveness_complete",
        "candidate_artifact",
        "closure_context",
        "derived_direct_vector",
        "index",
        "initial_direct_vector",
        "input_direct_cut_spine",
        "name",
        "normalization_steps_inner_first",
        "opaque_lemma_subtree_survival",
        "post_transform_idempotence",
        "proof_producing_cut_liveness_normalization_complete",
        "record_sha256",
        "statement",
    )
)
_CANDIDATE_ARTIFACT_FIELDS = frozenset(
    (
        "artifact_base64",
        "artifact_bytes",
        "artifact_sha256",
        "canonical_roundtrip_checked",
        "empty_context_kernel_checked",
        "formula_sha256",
        "fuel",
        "fuel_basis",
        "proof_term_sha256",
        "tree_metrics",
    )
)
_CANDIDATE_SPINE_FIELDS = frozenset(
    (
        "artifact_bytes",
        "artifact_path",
        "artifact_sha256",
        "declared_index",
        "dependency_index",
        "formula_sha256",
        "name",
        "opaque_lemma_bytes",
        "opaque_lemma_empty_context_kernel_checked",
        "opaque_lemma_proof_sha256",
        "proposition_formula_sha256",
        "root_conclusion_exact",
    )
)
_CANDIDATE_STEP_FIELDS = frozenset(
    (
        "bound_hypothesis_use_count",
        "declared_index",
        "dependency",
        "first_use_path",
        "input_body_proof_sha256",
        "intermediate_kernel_checked",
        "opaque_lemma_proof_sha256",
        "outcome",
        "output_proof_sha256",
        "processing_index",
        "surrounding_context_nearest_first",
    )
)
_VERIFICATION_TOP_LEVEL_FIELDS = frozenset(
    (
        *VERIFICATION_FALSE_FIELDS,
        "candidate_artifact_sha256",
        "candidate_root_sha256",
        "derived_artifact_byte_identical",
        "derived_direct_vector_independently_reproduced",
        "encoded_tagged_array_transform_independently_executed",
        "format",
        "id",
        "input_and_dependency_artifacts_independently_authenticated",
        "input_and_output_kernel_checked",
        "kernel_sources",
        "logic_mode",
        "producer_imported_by_verifier",
        "proof_liveness_transform_idempotent",
        "root_preimage",
        "root_sha256",
        "schema",
        "schema_claim_boundary_sha256",
        "status",
        "theorem",
        "v",
    )
)
_VERIFICATION_THEOREM_FIELDS = frozenset(
    (
        "candidate_artifact_sha256",
        "derived_direct_dependencies",
        "derived_direct_dependencies_lf_sha256",
        "index",
        "input_direct_cut_spine",
        "input_direct_cut_spine_lf_sha256",
        "name",
        "normalization_steps_inner_first",
        "output_fuel",
        "output_metrics",
        "output_proof_term_sha256",
        "record_sha256",
        "retained_transitive_closure",
        "retained_transitive_closure_lf_sha256",
    )
)

_KERNEL_SOURCE_FILES = (
    ("peano_lab/__init__.py", 257, "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a"),
    ("peano_lab/kernel/__init__.py", 263, "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84"),
    ("peano_lab/kernel/artifact_codec.py", 27_892, "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110"),
    ("peano_lab/kernel/checker.py", 10_738, "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19"),
    ("peano_lab/kernel/formulas.py", 10_950, "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"),
    ("peano_lab/kernel/proofs.py", 5_015, "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2"),
    ("peano_lab/kernel/terms.py", 9_133, "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"),
    ("peano_lab/kernel/subst.py", 5_165, "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3"),
)

_PRIVATE_KERNEL_ROOT = "_peano_hydra_a23d_verifier_kernel_runtime"
_PRIVATE_KERNEL_LOAD_ORDER = (
    ("peano_lab/__init__.py", _PRIVATE_KERNEL_ROOT, True),
    ("peano_lab/kernel/__init__.py", f"{_PRIVATE_KERNEL_ROOT}.kernel", True),
    ("peano_lab/kernel/terms.py", f"{_PRIVATE_KERNEL_ROOT}.kernel.terms", False),
    (
        "peano_lab/kernel/formulas.py",
        f"{_PRIVATE_KERNEL_ROOT}.kernel.formulas",
        False,
    ),
    ("peano_lab/kernel/proofs.py", f"{_PRIVATE_KERNEL_ROOT}.kernel.proofs", False),
    ("peano_lab/kernel/subst.py", f"{_PRIVATE_KERNEL_ROOT}.kernel.subst", False),
    (
        "peano_lab/kernel/artifact_codec.py",
        f"{_PRIVATE_KERNEL_ROOT}.kernel.artifact_codec",
        False,
    ),
    (
        "peano_lab/kernel/checker.py",
        f"{_PRIVATE_KERNEL_ROOT}.kernel.checker",
        False,
    ),
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class DependencyVectorCutLivenessVerificationError(ValueError):
    """The candidate, retained evidence, transform, or receipt is invalid."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value: str) -> object:
    raise ValueError(f"unsupported JSON number {value!r}")


def _parse_integer(value: str) -> int:
    parsed = int(value)
    if abs(parsed) > MAX_SAFE_JSON_INTEGER:
        raise ValueError("JSON integer exceeds the exact safe range")
    return parsed


def _validate_json(value: object, *, max_depth: int, max_items: int) -> None:
    pending: list[tuple[object, int]] = [(value, 1)]
    items = 0
    while pending:
        item, depth = pending.pop()
        items += 1
        if items > max_items:
            raise DependencyVectorCutLivenessVerificationError(
                "JSON value exceeds its item limit"
            )
        if depth > max_depth:
            raise DependencyVectorCutLivenessVerificationError(
                "JSON value exceeds its depth limit"
            )
        if item is None or type(item) in (bool, str):
            continue
        if type(item) is int:
            if abs(item) > MAX_SAFE_JSON_INTEGER:
                raise DependencyVectorCutLivenessVerificationError(
                    "JSON integer exceeds the exact safe range"
                )
            continue
        if type(item) is list:
            pending.extend((child, depth + 1) for child in item)
            continue
        if type(item) is dict:
            if not all(type(key) is str for key in item):
                raise DependencyVectorCutLivenessVerificationError(
                    "JSON object key is not text"
                )
            pending.extend((child, depth + 1) for child in item.values())
            continue
        raise DependencyVectorCutLivenessVerificationError(
            f"unsupported JSON value {type(item).__name__}"
        )


def _decode_json(raw: bytes, *, label: str, limit: int) -> object:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} is empty or exceeds its byte limit"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_int=_parse_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise DependencyVectorCutLivenessVerificationError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    _validate_json(value, max_depth=MAX_JSON_DEPTH, max_items=MAX_JSON_ITEMS)
    return value


def _compact_bytes(value: object) -> bytes:
    _validate_json(value, max_depth=MAX_JSON_DEPTH, max_items=MAX_JSON_ITEMS)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_verification_bytes(value: object) -> bytes:
    """Return the one canonical retained representation of a receipt."""

    validated = validate_dependency_vector_cut_liveness_verification(value)
    raw = (
        json.dumps(
            validated,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise DependencyVectorCutLivenessVerificationError(
            "verification receipt exceeds its byte limit"
        )
    return raw


def _canonical_document_bytes_unchecked(value: object) -> bytes:
    _validate_json(value, max_depth=MAX_JSON_DEPTH, max_items=MAX_JSON_ITEMS)
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256(_compact_bytes(value))


def _lf_sha256(names: Sequence[str]) -> str:
    return _sha256(("\n".join(names) + ("\n" if names else "")).encode("utf-8"))


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_regular_bytes(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise DependencyVectorCutLivenessVerificationError(
                    f"{label} ancestor is a symlink or non-directory"
                )
        metadata = absolute.lstat()
    except DependencyVectorCutLivenessVerificationError:
        raise
    except OSError as exc:
        raise DependencyVectorCutLivenessVerificationError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} is not a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise DependencyVectorCutLivenessVerificationError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise DependencyVectorCutLivenessVerificationError(
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
        path_after = absolute.lstat()
    except OSError as exc:
        raise DependencyVectorCutLivenessVerificationError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)
    identity = lambda item: (
        item.st_dev,
        item.st_ino,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )
    if (
        len(raw) > limit
        or not stat.S_ISREG(path_after.st_mode)
        or stat.S_ISLNK(path_after.st_mode)
        or identity(metadata) != identity(before)
        or identity(before) != identity(after)
        or identity(after) != identity(path_after)
    ):
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} changed during inspection"
        )
    return raw


def _repository_root(value: Path | None) -> Path:
    root = (
        Path(__file__).resolve().parents[2]
        if value is None
        else _lexical_absolute(value)
    )
    if not root.is_dir():
        raise DependencyVectorCutLivenessVerificationError(
            "repository root is not a directory"
        )
    return root


def _load_exact_json_file(
    path: Path,
    *,
    label: str,
    limit: int,
    expected_bytes: int,
    expected_sha256: str,
) -> dict[str, object]:
    raw = _safe_regular_bytes(path, label=label, limit=limit)
    if len(raw) != expected_bytes or _sha256(raw) != expected_sha256:
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} identity drifted"
        )
    value = _decode_json(raw, label=label, limit=limit)
    if type(value) is not dict or _canonical_document_bytes_unchecked(value) != raw:
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} is not canonical object JSON"
        )
    return value


def _load_schema(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    raw = _safe_regular_bytes(
        root / SCHEMA_RELATIVE, label="cut-liveness schema", limit=MAX_SCHEMA_BYTES
    )
    if len(raw) != SCHEMA_SOURCE_BYTES or _sha256(raw) != SCHEMA_SOURCE_SHA256:
        raise DependencyVectorCutLivenessVerificationError(
            "cut-liveness schema source identity drifted"
        )
    value = _decode_json(raw, label="cut-liveness schema", limit=MAX_SCHEMA_BYTES)
    if (
        type(value) is not dict
        or value.get("format") != SCHEMA_FORMAT
        or value.get("id") != SCHEMA_ID
        or value.get("v") != 1
        or value.get("logic_mode") != LOGIC_MODE
        or _sha256_json(value) != SCHEMA_SEMANTIC_SHA256
        or tuple(value.get("claim_boundary", {}).get("false_claims", ()))
        != BROAD_FALSE_FIELDS
        or value.get("fixed_inputs", {}).get("root", {}).get("name")
        != EXPECTED_NAME
        or tuple(
            value.get("fixed_inputs", {}).get("root", {}).get(
                "declared_dependencies", ()
            )
        )
        != INPUT_DEPENDENCIES
        or tuple(value.get("canonical_output", {}).get("derived_direct_dependencies", ()))
        != DERIVED_DEPENDENCIES
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "cut-liveness schema semantics drifted"
        )
    identity = {
        "artifact_bytes": len(raw),
        "artifact_sha256": _sha256(raw),
        "format": SCHEMA_FORMAT,
        "id": SCHEMA_ID,
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    return value, identity


def _load_manifest(root: Path) -> dict[str, object]:
    manifest = _load_exact_json_file(
        root / MANIFEST_RELATIVE,
        label="retained replay manifest",
        limit=4_000_000,
        expected_bytes=MANIFEST_BYTES,
        expected_sha256=MANIFEST_SHA256,
    )
    preimage = manifest.get("root_preimage")
    if (
        manifest.get("root_sha256") != MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != REPLAY_THEOREM_COUNT
        or manifest.get("logic_mode") != LOGIC_MODE
        or type(preimage) is not dict
        or _sha256_json(preimage) != MANIFEST_ROOT_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "retained replay manifest roots drifted"
        )
    rows = manifest.get("theorems")
    if type(rows) is not list or len(rows) != REPLAY_THEOREM_COUNT:
        raise DependencyVectorCutLivenessVerificationError(
            "retained replay theorem rows drifted"
        )
    return manifest


def _load_report(root: Path) -> dict[str, object]:
    report = _load_exact_json_file(
        root / REPORT_RELATIVE,
        label="retained replay report",
        limit=65_536,
        expected_bytes=REPORT_BYTES,
        expected_sha256=REPORT_SHA256,
    )
    if (
        report.get("v") != 1
        or report.get("format") != "peano-hydra-library-replay-verification"
        or report.get("status") != "passed"
        or report.get("logic_mode") != LOGIC_MODE
        or report.get("theorem_count") != REPLAY_THEOREM_COUNT
        or report.get("kernel_checked_count") != REPLAY_THEOREM_COUNT
        or report.get("manifest_root_sha256") != MANIFEST_ROOT_SHA256
        or report.get("replay_root_sha256") != REPLAY_ROOT_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "retained replay report semantics drifted"
        )
    return report


def _decode_tagged_artifact(raw: bytes, *, label: str) -> tuple[int, object, list[object]]:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} lacks one canonical terminal LF"
        )
    value = _decode_json(raw[:-1], label=label, limit=MAX_ARTIFACT_BYTES)
    if _compact_bytes(value) + b"\n" != raw:
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} is not a canonical tagged artifact"
        )
    if (
        type(value) is not list
        or len(value) != 4
        or value[0] != CERTIFICATE_REPRESENTATION
        or type(value[1]) is not int
        or value[1] < 1
        or type(value[2]) is not list
        or type(value[3]) is not list
    ):
        raise DependencyVectorCutLivenessVerificationError(
            f"{label} envelope is malformed"
        )
    return value[1], value[2], value[3]


# Proof child positions and the subset that introduce one proposition
# hypothesis for that child.  Formula and term children are intentionally
# opaque to this encoded-proof traversal.
_PROOF_LAYOUT: dict[str, tuple[int, tuple[int, ...], tuple[int, ...]]] = {
    "hyp": (2, (), ()),
    "imp_intro": (2, (1,), (1,)),
    "imp_elim": (3, (1, 2), ()),
    "cut": (5, (3, 4), (4,)),
    "and_intro": (3, (1, 2), ()),
    "and_elim_l": (2, (1,), ()),
    "and_elim_r": (2, (1,), ()),
    "or_intro_l": (2, (1,), ()),
    "or_intro_r": (2, (1,), ()),
    "or_elim": (4, (1, 2, 3), (2, 3)),
    "bot_elim": (2, (1,), ()),
    # ForallIntro introduces a term variable, not a proposition hypothesis.
    "forall_intro": (2, (1,), ()),
    "forall_elim": (3, (1,), ()),
    "exists_intro": (3, (2,), ()),
    "exists_elim": (3, (1, 2), (2,)),
    "eq_refl": (2, (), ()),
    "eq_sym": (2, (1,), ()),
    "eq_trans": (3, (1, 2), ()),
    "cong_s": (2, (1,), ()),
    "cong_add": (3, (1, 2), ()),
    "cong_mul": (3, (1, 2), ()),
    "eq_subst": (4, (2, 3), ()),
    "dne": (2, (), ()),
    "axiom": (2, (), ()),
    "ind": (4, (2, 3), ()),
}

_PROOF_PATH_NAMES: dict[str, tuple[str, dict[int, str]]] = {
    "hyp": ("Hyp", {}),
    "imp_intro": ("ImpIntro", {1: "body"}),
    "imp_elim": ("ImpElim", {1: "f", 2: "a"}),
    "cut": ("Cut", {3: "lemma", 4: "body"}),
    "and_intro": ("AndIntro", {1: "left", 2: "right"}),
    "and_elim_l": ("AndElimL", {1: "pair"}),
    "and_elim_r": ("AndElimR", {1: "pair"}),
    "or_intro_l": ("OrIntroL", {1: "proof"}),
    "or_intro_r": ("OrIntroR", {1: "proof"}),
    "or_elim": (
        "OrElim",
        {1: "disjunction", 2: "left_case", 3: "right_case"},
    ),
    "bot_elim": ("BotElim", {1: "absurdity"}),
    "forall_intro": ("ForallIntro", {1: "body"}),
    "forall_elim": ("ForallElim", {1: "p"}),
    "exists_intro": ("ExistsIntro", {2: "p"}),
    "exists_elim": ("ExistsElim", {1: "p", 2: "body"}),
    "eq_refl": ("EqRefl", {}),
    "eq_sym": ("EqSym", {1: "proof"}),
    "eq_trans": ("EqTrans", {1: "first", 2: "second"}),
    "cong_s": ("CongS", {1: "proof"}),
    "cong_add": ("CongAdd", {1: "left", 2: "right"}),
    "cong_mul": ("CongMul", {1: "left", 2: "right"}),
    "eq_subst": ("EqSubst", {2: "eq_proof", 3: "body_proof"}),
    "dne": ("DNE", {}),
    "axiom": ("Axiom", {}),
    "ind": ("Ind", {2: "base", 3: "step"}),
}


def _proof_layout(node: object) -> tuple[str, tuple[int, ...], tuple[int, ...]]:
    if type(node) is not list or not node or type(node[0]) is not str:
        raise DependencyVectorCutLivenessVerificationError(
            "encoded proof node is malformed"
        )
    tag = node[0]
    layout = _PROOF_LAYOUT.get(tag)
    if layout is None or len(node) != layout[0]:
        raise DependencyVectorCutLivenessVerificationError(
            f"encoded proof tag/arity is unsupported: {tag!r}"
        )
    if tag == "dne":
        raise DependencyVectorCutLivenessVerificationError(
            "intuitionistic proof contains DNE"
        )
    return tag, layout[1], layout[2]


def derive_tagged_proof_liveness(
    encoded_body: object,
    *,
    outer_hypothesis_count: int,
    max_visits: int = MAX_TRANSFORM_VISITS,
) -> tuple[int, ...]:
    """Count free references to each outer proposition slot.

    Slot zero is the newest outer hypothesis.  The traversal has an explicit
    binder table and is independent of the producer's proof-object visitor.
    """

    if (
        type(outer_hypothesis_count) is not int
        or outer_hypothesis_count < 0
        or type(max_visits) is not int
        or max_visits < 1
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "liveness traversal bounds are malformed"
        )
    counts = [0] * outer_hypothesis_count
    pending: list[tuple[object, int, int]] = [(encoded_body, 0, 1)]
    visits = 0
    while pending:
        node, binder_depth, proof_depth = pending.pop()
        visits += 1
        if visits > max_visits or proof_depth > MAX_PROOF_DEPTH:
            raise DependencyVectorCutLivenessVerificationError(
                "encoded liveness traversal exceeded its bound"
            )
        tag, children, binders = _proof_layout(node)
        if tag == "hyp":
            index = node[1]
            if type(index) is not int or index < 0:
                raise DependencyVectorCutLivenessVerificationError(
                    "encoded hypothesis index is malformed"
                )
            if index >= binder_depth:
                slot = index - binder_depth
                if slot >= outer_hypothesis_count:
                    raise DependencyVectorCutLivenessVerificationError(
                        "encoded proof references a hypothesis outside its context"
                    )
                counts[slot] += 1
            continue
        for position in reversed(children):
            pending.append(
                (
                    node[position],
                    binder_depth + (1 if position in binders else 0),
                    proof_depth + 1,
                )
            )
    return tuple(counts)


def _first_tagged_hypothesis_use_path(
    encoded_body: object,
    *,
    max_visits: int = MAX_TRANSFORM_VISITS,
) -> tuple[str, ...] | None:
    pending: list[tuple[object, int, tuple[str, ...], int]] = [
        (encoded_body, 0, (), 1)
    ]
    visits = 0
    while pending:
        node, binder_depth, path, proof_depth = pending.pop()
        visits += 1
        if visits > max_visits or proof_depth > MAX_PROOF_DEPTH:
            raise DependencyVectorCutLivenessVerificationError(
                "encoded first-use traversal exceeded its bound"
            )
        tag, children, binders = _proof_layout(node)
        if tag == "hyp":
            index = node[1]
            if type(index) is not int or index < 0:
                raise DependencyVectorCutLivenessVerificationError(
                    "encoded hypothesis index is malformed"
                )
            if index == binder_depth:
                return path + (f"Hyp[{index}]",)
            continue
        class_name, field_names = _PROOF_PATH_NAMES[tag]
        for position in reversed(children):
            field_name = field_names.get(position)
            if field_name is None:
                raise DependencyVectorCutLivenessVerificationError(
                    "encoded proof path table is incomplete"
                )
            pending.append(
                (
                    node[position],
                    binder_depth + (1 if position in binders else 0),
                    path + (f"{class_name}.{field_name}",),
                    proof_depth + 1,
                )
            )
    return None


def thin_tagged_proof_outer_context(
    encoded_body: object,
    *,
    outer_hypothesis_count: int,
    live_slots: Sequence[int],
    max_visits: int = MAX_TRANSFORM_VISITS,
) -> list[object]:
    """Capture-safely compact an encoded proof's outer hypothesis context."""

    if (
        type(outer_hypothesis_count) is not int
        or outer_hypothesis_count < 0
        or not isinstance(live_slots, Sequence)
        or isinstance(live_slots, (str, bytes, bytearray))
        or not all(type(slot) is int and 0 <= slot < outer_hypothesis_count for slot in live_slots)
        or len(set(live_slots)) != len(live_slots)
        or tuple(sorted(live_slots)) != tuple(live_slots)
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "outer-context thinning map is malformed"
        )
    mapping = {old: new for new, old in enumerate(live_slots)}
    visits = [0]

    def transform(node: object, binder_depth: int, proof_depth: int) -> list[object]:
        visits[0] += 1
        if visits[0] > max_visits or proof_depth > MAX_PROOF_DEPTH:
            raise DependencyVectorCutLivenessVerificationError(
                "encoded proof thinning exceeded its bound"
            )
        tag, children, binders = _proof_layout(node)
        if tag == "hyp":
            index = node[1]
            if type(index) is not int or index < 0:
                raise DependencyVectorCutLivenessVerificationError(
                    "encoded hypothesis index is malformed"
                )
            if index < binder_depth:
                return ["hyp", index]
            old_slot = index - binder_depth
            if old_slot >= outer_hypothesis_count:
                raise DependencyVectorCutLivenessVerificationError(
                    "encoded proof references a hypothesis outside its context"
                )
            if old_slot not in mapping:
                raise DependencyVectorCutLivenessVerificationError(
                    "attempted to delete a live outer hypothesis"
                )
            return ["hyp", binder_depth + mapping[old_slot]]
        result = deepcopy(node)
        for position in children:
            result[position] = transform(
                node[position],
                binder_depth + (1 if position in binders else 0),
                proof_depth + 1,
            )
        return result

    return transform(encoded_body, 0, 1)


def _proof_tree_metrics(encoded_proof: object) -> dict[str, int]:
    pending: list[tuple[object, int]] = [(encoded_proof, 1)]
    nodes = 0
    depth = 0
    cuts = 0
    while pending:
        node, current_depth = pending.pop()
        nodes += 1
        if nodes > MAX_PROOF_NODES or current_depth > MAX_PROOF_DEPTH:
            raise DependencyVectorCutLivenessVerificationError(
                "encoded proof metrics exceeded their bound"
            )
        tag, children, _binders = _proof_layout(node)
        depth = max(depth, current_depth)
        cuts += tag == "cut"
        pending.extend((node[position], current_depth + 1) for position in children)
    return {"cut_nodes": cuts, "proof_depth": depth, "proof_nodes": nodes}


def _manifest_rows(manifest: Mapping[str, object]) -> dict[str, dict[str, object]]:
    rows = manifest.get("theorems")
    if type(rows) is not list:
        raise DependencyVectorCutLivenessVerificationError(
            "retained manifest theorem rows are malformed"
        )
    result: dict[str, dict[str, object]] = {}
    for expected_index, row in enumerate(rows):
        if (
            type(row) is not dict
            or row.get("index") != expected_index
            or type(row.get("name")) is not str
            or row["name"] in result
        ):
            raise DependencyVectorCutLivenessVerificationError(
                "retained manifest theorem row identity drifted"
            )
        result[row["name"]] = row
    return result


def _transitive_closure(
    selected: Sequence[str], rows: Mapping[str, Mapping[str, object]]
) -> tuple[str, ...]:
    seen: set[str] = set()
    pending = list(selected)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = rows.get(name)
        if type(row) is not dict:
            raise DependencyVectorCutLivenessVerificationError(
                f"retained graph has no dependency {name!r}"
            )
        dependencies = row.get("declared_dependencies")
        if (
            type(dependencies) is not list
            or not all(type(item) is str and item for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise DependencyVectorCutLivenessVerificationError(
                "retained dependency vector is malformed"
            )
        seen.add(name)
        pending.extend(dependencies)
    if EXPECTED_NAME in seen:
        raise DependencyVectorCutLivenessVerificationError(
            "retained dependency closure contains its root"
        )
    return tuple(sorted(seen, key=lambda name: rows[name]["index"]))


def _load_and_authenticate_artifacts(
    root: Path, manifest: Mapping[str, object]
) -> dict[str, object]:
    rows = _manifest_rows(manifest)
    root_row = rows.get(EXPECTED_NAME)
    if (
        type(root_row) is not dict
        or root_row.get("index") != EXPECTED_INDEX
        or tuple(root_row.get("declared_dependencies", ())) != INPUT_DEPENDENCIES
        or root_row.get("formula_sha256") != ROOT_FORMULA_SHA256
        or root_row.get("proof_term_sha256") != ROOT_PROOF_SHA256
        or root_row.get("artifact", {}).get("sha256") != ROOT_ARTIFACT_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "retained root manifest row drifted"
        )
    root_raw = _safe_regular_bytes(
        root / ROOT_ARTIFACT_RELATIVE,
        label="retained root artifact",
        limit=MAX_ARTIFACT_BYTES,
    )
    if len(root_raw) != ROOT_ARTIFACT_BYTES or _sha256(root_raw) != ROOT_ARTIFACT_SHA256:
        raise DependencyVectorCutLivenessVerificationError(
            "retained root artifact identity drifted"
        )
    root_fuel, root_target, root_proof = _decode_tagged_artifact(
        root_raw, label="retained root artifact"
    )
    if (
        root_fuel != ROOT_SOURCE_FUEL
        or _sha256(_compact_bytes(root_target)) != ROOT_FORMULA_SHA256
        or _sha256(_compact_bytes(root_proof)) != ROOT_PROOF_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "retained root tagged identity drifted"
        )

    dependencies: dict[str, dict[str, object]] = {}
    for expected in DEPENDENCY_INPUTS:
        name = expected["name"]
        row = rows.get(name)
        if (
            type(row) is not dict
            or row.get("index") != expected["index"]
            or row.get("formula_sha256") != expected["formula_sha256"]
            or row.get("proof_term_sha256") != expected["proof_sha256"]
            or row.get("artifact", {}).get("path") != expected["artifact_path"]
            or row.get("artifact", {}).get("bytes") != expected["artifact_bytes"]
            or row.get("artifact", {}).get("sha256") != expected["artifact_sha256"]
        ):
            raise DependencyVectorCutLivenessVerificationError(
                f"retained dependency row drifted for {name!r}"
            )
        raw = _safe_regular_bytes(
            root / REPLAY_ROOT / expected["artifact_path"],
            label=f"retained dependency artifact {name}",
            limit=MAX_ARTIFACT_BYTES,
        )
        if len(raw) != expected["artifact_bytes"] or _sha256(raw) != expected["artifact_sha256"]:
            raise DependencyVectorCutLivenessVerificationError(
                f"retained dependency artifact drifted for {name!r}"
            )
        fuel, target, proof = _decode_tagged_artifact(
            raw, label=f"retained dependency artifact {name}"
        )
        if (
            _sha256(_compact_bytes(target)) != expected["formula_sha256"]
            or _sha256(_compact_bytes(proof)) != expected["proof_sha256"]
        ):
            raise DependencyVectorCutLivenessVerificationError(
                f"retained dependency tagged identity drifted for {name!r}"
            )
        dependencies[name] = {
            "fuel": fuel,
            "proof": proof,
            "raw": raw,
            "target": target,
        }
    return {
        "dependencies": dependencies,
        "manifest_rows": rows,
        "root_proof": root_proof,
        "root_raw": root_raw,
        "root_target": root_target,
    }


def _extract_outer_spine(
    proof: object,
    target: object,
    dependency_names: Sequence[str],
    dependencies: Mapping[str, Mapping[str, object]],
) -> object:
    cursor = proof
    for name in dependency_names:
        evidence = dependencies.get(name)
        if (
            type(cursor) is not list
            or len(cursor) != 5
            or cursor[0] != "cut"
            or type(evidence) is not dict
            or cursor[1] != evidence["target"]
            or cursor[2] != target
            or cursor[3] != evidence["proof"]
        ):
            raise DependencyVectorCutLivenessVerificationError(
                f"retained outer Cut spine drifted at {name!r}"
            )
        cursor = cursor[4]
    if (
        type(cursor) is list
        and len(cursor) == 5
        and cursor[0] == "cut"
        and cursor[2] == target
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "retained proof exposes an unexpected additional root Cut"
        )
    return cursor


def _rebuild_outer_spine(
    body: object,
    target: object,
    dependency_names: Sequence[str],
    dependencies: Mapping[str, Mapping[str, object]],
) -> list[object]:
    result = deepcopy(body)
    for name in reversed(tuple(dependency_names)):
        evidence = dependencies[name]
        result = [
            "cut",
            deepcopy(evidence["target"]),
            deepcopy(target),
            deepcopy(evidence["proof"]),
            result,
        ]
    return result


def _normalize_encoded_spine(
    proof: object,
    target: object,
    dependency_names: Sequence[str],
    dependencies: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    names = tuple(dependency_names)
    terminal = _extract_outer_spine(proof, target, names, dependencies)
    current = deepcopy(terminal)
    retained_inner_first: list[str] = []
    counts_inner_first: list[int] = []
    steps: list[dict[str, object]] = []
    closed_intermediates: list[list[object]] = []
    for processing_index, declared_index in enumerate(reversed(range(len(names)))):
        name = names[declared_index]
        context_size = declared_index + 1
        counts = derive_tagged_proof_liveness(
            current, outer_hypothesis_count=context_size
        )
        use_count = counts[0]
        first_path = _first_tagged_hypothesis_use_path(current)
        if bool(use_count) != (first_path is not None):
            raise DependencyVectorCutLivenessVerificationError(
                "encoded liveness count and first-use path disagree"
            )
        before_sha256 = _sha256(_compact_bytes(current))
        evidence = dependencies[name]
        if use_count:
            outcome = "retained-used"
            current = [
                "cut",
                deepcopy(evidence["target"]),
                deepcopy(target),
                deepcopy(evidence["proof"]),
                current,
            ]
            retained_inner_first.append(name)
        else:
            outcome = "deleted-vacuous"
            current = thin_tagged_proof_outer_context(
                current,
                outer_hypothesis_count=context_size,
                live_slots=tuple(range(1, context_size)),
            )
        counts_inner_first.append(use_count)
        steps.append(
            {
                "bound_hypothesis_use_count": use_count,
                "declared_index": declared_index,
                "dependency": name,
                "first_use_path": None if first_path is None else list(first_path),
                "input_body_proof_sha256": before_sha256,
                "intermediate_kernel_checked": True,
                "opaque_lemma_proof_sha256": _sha256(
                    _compact_bytes(evidence["proof"])
                ),
                "outcome": outcome,
                "output_proof_sha256": _sha256(_compact_bytes(current)),
                "processing_index": processing_index,
                "surrounding_context_nearest_first": list(
                    reversed(names[:declared_index])
                ),
            }
        )
        closed_intermediates.append(
            _rebuild_outer_spine(
                current, target, names[:declared_index], dependencies
            )
        )
    selected = tuple(reversed(retained_inner_first))
    return {
        "closed_intermediates": tuple(closed_intermediates),
        "counts_by_slot": tuple(counts_inner_first),
        "proof": current,
        "selected": selected,
        "steps": steps,
    }


def _authenticate_kernel_sources(
    root: Path,
) -> tuple[dict[str, object], dict[str, bytes]]:
    py_root = root / "peano-lab/py"
    records: list[dict[str, object]] = []
    source_bytes: dict[str, bytes] = {}
    for relative, expected_bytes, expected_sha256 in _KERNEL_SOURCE_FILES:
        raw = _safe_regular_bytes(
            py_root / relative,
            label=f"kernel source {relative}",
            limit=MAX_DOCUMENT_BYTES,
        )
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha256:
            raise DependencyVectorCutLivenessVerificationError(
                f"kernel source identity drifted for {relative!r}"
            )
        records.append(
            {"bytes": len(raw), "path": relative, "sha256": _sha256(raw)}
        )
        source_bytes[relative] = raw
    preimage = {
        "format": (
            "peano-hydra-a23d-cut-liveness-verifier-kernel-sources-preimage-v1"
        ),
        "records": records,
        "v": 1,
    }
    return (
        {
            "count": len(records),
            "load_mode": "authenticated-source-bytes-source_to_code-private-namespace",
            "preimage": preimage,
            "root_sha256": _sha256_json(preimage),
        },
        source_bytes,
    )


def _kernel_modules(root: Path) -> dict[str, object]:
    identities, source_bytes = _authenticate_kernel_sources(root)
    contaminated = sorted(
        name
        for name in sys.modules
        if name == _PRIVATE_KERNEL_ROOT or name.startswith(_PRIVATE_KERNEL_ROOT + ".")
    )
    if contaminated:
        raise DependencyVectorCutLivenessVerificationError(
            "private verifier kernel namespace was already populated"
        )
    loaded: list[str] = []
    modules: dict[str, object] = {}
    py_root = root / "peano-lab/py"
    try:
        for relative, module_name, is_package in _PRIVATE_KERNEL_LOAD_ORDER:
            path = py_root / relative
            loader = importlib.machinery.SourceFileLoader(module_name, str(path))
            specification = importlib.util.spec_from_loader(
                module_name, loader, is_package=is_package
            )
            if (
                specification is None
                or specification.loader is not loader
                or specification.origin != str(path)
            ):
                raise DependencyVectorCutLivenessVerificationError(
                    f"cannot construct private kernel loader for {relative!r}"
                )
            module = importlib.util.module_from_spec(specification)
            sys.modules[module_name] = module
            loaded.append(module_name)
            code = loader.source_to_code(source_bytes[relative], str(path))
            exec(code, module.__dict__)
            if (
                sys.modules.get(module_name) is not module
                or Path(str(module.__file__)).resolve() != path.resolve()
            ):
                raise DependencyVectorCutLivenessVerificationError(
                    f"private kernel module identity drifted for {relative!r}"
                )
            modules[module_name] = module
        observed = {
            name
            for name in sys.modules
            if name == _PRIVATE_KERNEL_ROOT
            or name.startswith(_PRIVATE_KERNEL_ROOT + ".")
        }
        expected = {row[1] for row in _PRIVATE_KERNEL_LOAD_ORDER}
        if observed != expected:
            raise DependencyVectorCutLivenessVerificationError(
                "private verifier kernel loaded an unexpected module closure"
            )
        return {
            "checker": modules[f"{_PRIVATE_KERNEL_ROOT}.kernel.checker"],
            "cleanup": tuple(reversed(loaded)),
            "codec": modules[f"{_PRIVATE_KERNEL_ROOT}.kernel.artifact_codec"],
            "identities": identities,
        }
    except BaseException:
        for name in reversed(loaded):
            sys.modules.pop(name, None)
        raise


def _kernel_check_artifacts(
    root: Path,
    evidence: Mapping[str, object],
    intermediate_raws: Sequence[bytes],
    output_raw: bytes,
) -> dict[str, object]:
    modules = _kernel_modules(root)
    codec = modules["codec"]
    checker = modules["checker"]
    try:
        decoded: dict[str, tuple[int, object, object]] = {}
        all_raw: list[tuple[str, bytes]] = [("root", evidence["root_raw"])]
        all_raw.extend(
            (name, item["raw"])
            for name, item in evidence["dependencies"].items()
        )
        all_raw.extend(
            (f"intermediate-{index}", raw)
            for index, raw in enumerate(intermediate_raws)
        )
        all_raw.append(("output", output_raw))
        for name, raw in all_raw:
            try:
                fuel, target, proof = codec.decode_artifact(
                    raw,
                    max_bytes=MAX_ARTIFACT_BYTES,
                    max_nodes=MAX_PROOF_NODES,
                    max_depth=MAX_PROOF_DEPTH,
                )
                roundtrip = codec.encode_artifact_bounded(
                    fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
                )
            except Exception as exc:
                raise DependencyVectorCutLivenessVerificationError(
                    f"kernel codec rejected {name!r} artifact"
                ) from exc
            if roundtrip != raw or not checker.check((), proof, target):
                raise DependencyVectorCutLivenessVerificationError(
                    f"{name!r} artifact failed canonical kernel replay"
                )
            decoded[name] = (fuel, target, proof)
        root_target = decoded["root"][1]
        root_cursor = decoded["root"][2]
        for name in INPUT_DEPENDENCIES:
            _fuel, target, proof = decoded[name]
            if (
                type(root_cursor).__name__ != "Cut"
                or codec.encode_formula(root_cursor.proposition)
                != codec.encode_formula(target)
                or codec.encode_formula(root_cursor.conclusion)
                != codec.encode_formula(root_target)
                or codec.encode_proof(root_cursor.lemma)
                != codec.encode_proof(proof)
            ):
                raise DependencyVectorCutLivenessVerificationError(
                    "decoded outer lemma or root conclusion differs from its pin"
                )
            root_cursor = root_cursor.body
        if type(root_cursor).__name__ == "Cut" and (
            codec.encode_formula(root_cursor.conclusion)
            == codec.encode_formula(root_target)
        ):
            raise DependencyVectorCutLivenessVerificationError(
                "decoded root exposes an unexpected additional direct Cut"
            )
        return modules["identities"]
    finally:
        for name in modules["cleanup"]:
            sys.modules.pop(name, None)


def _candidate_root(candidate: Mapping[str, object]) -> str:
    root = candidate.get("root_sha256")
    preimage = candidate.get("root_preimage")
    if (
        type(root) is not str
        or _SHA256_RE.fullmatch(root) is None
        or type(preimage) is not dict
        or set(preimage) != {"format", "payload", "v"}
        or preimage.get("format") != CANDIDATE_ROOT_PREIMAGE_FORMAT
        or preimage.get("v") != 1
        or _sha256_json(preimage) != root
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate document root is malformed"
        )
    detached = {
        key: deepcopy(value)
        for key, value in candidate.items()
        if key not in ("root_preimage", "root_sha256")
    }
    if preimage.get("payload") != detached:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate root preimage does not bind the candidate body"
        )
    return root


def _candidate_artifact_bytes(candidate: Mapping[str, object]) -> bytes:
    theorem = candidate.get("theorem")
    artifact = None if type(theorem) is not dict else theorem.get("candidate_artifact")
    encoded = None if type(artifact) is not dict else artifact.get("artifact_base64")
    if type(encoded) is not str:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate does not carry an embedded artifact"
        )
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate artifact base64 is malformed"
        ) from exc
    return raw


def _lf_receipt(names: Sequence[str]) -> dict[str, object]:
    values = tuple(names)
    raw = ("\n".join(values) + ("\n" if values else "")).encode("utf-8")
    return {
        "count": len(values),
        "dependencies": list(values),
        "lf_bytes": len(raw),
        "lf_sha256": _sha256(raw),
    }


def _require_candidate_claims(
    candidate: Mapping[str, object],
    derived: Mapping[str, object],
    schema_identity: Mapping[str, object],
) -> None:
    if (
        set(candidate) != _CANDIDATE_TOP_LEVEL_FIELDS
        or candidate.get("format") != CANDIDATE_FORMAT
        or candidate.get("id") != CANDIDATE_ID
        or candidate.get("v") != CANDIDATE_VERSION
        or candidate.get("logic_mode") != LOGIC_MODE
        or candidate.get("status") != CANDIDATE_STATUS
        or candidate.get("theorem_count") != 1
        or candidate.get("bounded_one_root_protocol_executed") is not True
        or candidate.get("schema") != schema_identity
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate envelope identity drifted"
        )
    if candidate.get("algorithm") != {
        "id": "binder-aware-inner-first-vacuous-direct-cut-elimination-v1",
        "opaque_direct_lemmas_transformed": False,
        "processing_order": "inner-first",
        "proof_producing": True,
        "scope": "exact-declared-root-direct-cut-spine-only",
    }:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate algorithm envelope drifted"
        )
    for field in BROAD_FALSE_FIELDS:
        if candidate.get(field) is not False:
            raise DependencyVectorCutLivenessVerificationError(
                f"candidate broad claim {field!r} is not false"
            )
    theorem = candidate.get("theorem")
    if type(theorem) is not dict:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate theorem record is missing"
        )
    if set(theorem) != _CANDIDATE_THEOREM_FIELDS:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate theorem field set drifted"
        )
    for field in BROAD_FALSE_FIELDS:
        if theorem.get(field) is not False:
            raise DependencyVectorCutLivenessVerificationError(
                f"candidate theorem claim {field!r} is not false"
            )
    evidence = derived["evidence"]
    expected_spine = []
    for declared_index, expected in enumerate(DEPENDENCY_INPUTS):
        name = expected["name"]
        proof = evidence["dependencies"][name]["proof"]
        expected_spine.append(
            {
                "artifact_bytes": expected["artifact_bytes"],
                "artifact_path": expected["artifact_path"],
                "artifact_sha256": expected["artifact_sha256"],
                "declared_index": declared_index,
                "dependency_index": expected["index"],
                "formula_sha256": expected["formula_sha256"],
                "name": name,
                "opaque_lemma_bytes": len(_compact_bytes(proof)),
                "opaque_lemma_empty_context_kernel_checked": True,
                "opaque_lemma_proof_sha256": expected["proof_sha256"],
                "proposition_formula_sha256": expected["formula_sha256"],
                "root_conclusion_exact": True,
            }
        )
    artifact = theorem.get("candidate_artifact")
    steps = theorem.get("normalization_steps_inner_first")
    input_vector = theorem.get("initial_direct_vector")
    derived_vector = theorem.get("derived_direct_vector")
    expected_metrics = derived["metrics"]
    if (
        theorem.get("index") != EXPECTED_INDEX
        or theorem.get("name") != EXPECTED_NAME
        or theorem.get("input_direct_cut_spine") != expected_spine
        or input_vector != _lf_receipt(INPUT_DEPENDENCIES)
        or derived_vector != _lf_receipt(DERIVED_DEPENDENCIES)
        or theorem.get("bounded_one_root_cut_liveness_complete") is not True
        or theorem.get("proof_producing_cut_liveness_normalization_complete")
        is not True
        or type(steps) is not list
        or len(steps) != len(EXPECTED_INNER_FIRST_OUTCOMES)
        or steps != derived["steps"]
        or any(type(row) is not dict or set(row) != _CANDIDATE_STEP_FIELDS for row in steps)
        or tuple(
            (row.get("dependency"), row.get("outcome"))
            for row in steps
            if type(row) is dict
        )
        != EXPECTED_INNER_FIRST_OUTCOMES
        or tuple(
            row.get("bound_hypothesis_use_count")
            for row in steps
            if type(row) is dict
        )
        != EXPECTED_INNER_FIRST_COUNTS
        or any(
            type(row) is not dict
            or row.get("processing_index") != processing_index
            or row.get("declared_index") != len(INPUT_DEPENDENCIES) - processing_index - 1
            or row.get("intermediate_kernel_checked") is not True
            for processing_index, row in enumerate(steps)
        )
        or type(artifact) is not dict
        or set(artifact) != _CANDIDATE_ARTIFACT_FIELDS
        or artifact.get("artifact_bytes") != OUTPUT_ARTIFACT_BYTES
        or artifact.get("artifact_sha256") != OUTPUT_ARTIFACT_SHA256
        or artifact.get("proof_term_sha256") != OUTPUT_PROOF_SHA256
        or artifact.get("fuel") != OUTPUT_FUEL
        or artifact.get("formula_sha256") != ROOT_FORMULA_SHA256
        or artifact.get("tree_metrics") != expected_metrics
        or artifact.get("canonical_roundtrip_checked") is not True
        or artifact.get("empty_context_kernel_checked") is not True
        or artifact.get("fuel_basis")
        != {
            "formula": "8 * intrinsic_proof_nodes + 16",
            "role": "deterministic-replay-envelope-metadata-not-a-comparison-axis-or-authority",
        }
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate theorem evidence differs from independent derivation"
        )
    expected_closure = _lf_receipt(EXPECTED_CLOSURE)
    closure = theorem.get("closure_context")
    expected_closure_context = {
        "basis": "retained-manifest-graph-descriptive-context-not-direct-vector-input",
        "derived_vector_closure": expected_closure,
        "dropped_direct_dependencies_remaining_reachable": [
            "add_succ_left",
            "add_assoc",
        ],
        "initial_vector_closure": expected_closure,
        "unchanged": True,
    }
    expected_idempotence = {
        "checked": True,
        "proof_term_sha256": OUTPUT_PROOF_SHA256,
        "retained_dependencies": list(DERIVED_DEPENDENCIES),
        "second_pass_outcomes_inner_first": [
            {"dependency": "add_comm", "outcome": "retained-used"},
            {"dependency": "mul_add", "outcome": "retained-used"},
        ],
    }
    expected_survival = [
        {
            "dependency": expected["name"],
            "direct_cut_retained": expected["name"] in DERIVED_DEPENDENCIES,
            "input_subtree_occurrences": before_count,
            "opaque_lemma_proof_sha256": expected["proof_sha256"],
            "output_subtree_occurrences": 1,
            "survives_elsewhere_after_root_cut_deletion": (
                expected["name"] not in DERIVED_DEPENDENCIES
            ),
        }
        for expected, before_count in zip(
            DEPENDENCY_INPUTS, (1, 2, 2, 1), strict=True
        )
    ]
    if (
        closure != expected_closure_context
        or theorem.get("statement")
        != {"formula_sha256": ROOT_FORMULA_SHA256, "target_preserved_exactly": True}
        or theorem.get("post_transform_idempotence") != expected_idempotence
        or theorem.get("opaque_lemma_subtree_survival") != expected_survival
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate closure or idempotence evidence drifted"
        )
    record_hash = theorem.get("record_sha256")
    if (
        type(record_hash) is not str
        or record_hash
        != _sha256_json(
            {key: value for key, value in theorem.items() if key != "record_sha256"}
        )
        or candidate.get("theorem_record_root_sha256") != record_hash
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate theorem record root drifted"
        )
    root_input = {
        "artifact_bytes": ROOT_ARTIFACT_BYTES,
        "artifact_path": ROOT_ARTIFACT_RELATIVE.relative_to(REPLAY_ROOT).as_posix(),
        "artifact_sha256": ROOT_ARTIFACT_SHA256,
        "formula_sha256": ROOT_FORMULA_SHA256,
        "fuel": ROOT_SOURCE_FUEL,
        "index": EXPECTED_INDEX,
        "name": EXPECTED_NAME,
        "proof_term_sha256": ROOT_PROOF_SHA256,
    }
    dependency_inputs = [
        {
            "artifact_bytes": row["artifact_bytes"],
            "artifact_path": row["artifact_path"],
            "artifact_sha256": row["artifact_sha256"],
            "formula_sha256": row["formula_sha256"],
            "index": row["index"],
            "name": row["name"],
            "proof_term_sha256": row["proof_sha256"],
        }
        for row in DEPENDENCY_INPUTS
    ]
    inputs = candidate.get("inputs")
    if (
        type(inputs) is not dict
        or inputs.get("root_artifact") != root_input
        or inputs.get("dependency_artifacts") != dependency_inputs
        or inputs.get("replay_manifest")
        != {
            "artifact_bytes": MANIFEST_BYTES,
            "artifact_path": MANIFEST_RELATIVE.as_posix(),
            "artifact_sha256": MANIFEST_SHA256,
            "manifest_root_sha256": MANIFEST_ROOT_SHA256,
            "replay_root_sha256": REPLAY_ROOT_SHA256,
        }
        or inputs.get("replay_report")
        != {
            "artifact_bytes": REPORT_BYTES,
            "artifact_path": REPORT_RELATIVE.as_posix(),
            "artifact_sha256": REPORT_SHA256,
        }
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate fixed-input receipt drifted"
        )
    if candidate.get("aggregate") != {
        "candidate_artifact_count": 1,
        "deleted_vacuous_root_cut_count": 2,
        "derived_direct_dependency_count": 2,
        "initial_direct_dependency_count": 4,
        "pilot_theorem_count": 1,
        "retained_used_root_cut_count": 2,
    }:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate aggregate drifted"
        )
    implementation = candidate.get("implementation")
    if type(implementation) is not dict or set(implementation) != {
        "source_count",
        "source_root_sha256",
        "sources",
    }:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate implementation receipt field set drifted"
        )
    sources = implementation.get("sources")
    if (
        type(sources) is not list
        or implementation.get("source_count") != len(sources)
        or not sources
        or any(
            type(row) is not dict
            or set(row) != {"bytes", "path", "sha256"}
            or type(row.get("bytes")) is not int
            or row["bytes"] < 1
            or type(row.get("path")) is not str
            or not row["path"]
            or type(row.get("sha256")) is not str
            or _SHA256_RE.fullmatch(row["sha256"]) is None
            for row in sources
        )
        or implementation.get("source_root_sha256")
        != _sha256_json(
            {
                "format": "peano-hydra-a23d-source-vector-v1",
                "sources": sources,
                "v": 1,
            }
        )
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "candidate implementation receipt is malformed"
        )


def _false_claims() -> dict[str, bool]:
    return {field: False for field in VERIFICATION_FALSE_FIELDS}


def verify_dependency_vector_cut_liveness(
    candidate: Mapping[str, object], repository_root: Path | None = None
) -> dict[str, object]:
    """Independently reproduce and kernel-check the exact A2.3d candidate."""

    if type(candidate) is not dict:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate must be one exact object"
        )
    root = _repository_root(repository_root)
    schema, schema_identity = _load_schema(root)
    manifest = _load_manifest(root)
    _load_report(root)
    evidence = _load_and_authenticate_artifacts(root, manifest)
    normalized = _normalize_encoded_spine(
        evidence["root_proof"],
        evidence["root_target"],
        INPUT_DEPENDENCIES,
        evidence["dependencies"],
    )
    counts = normalized["counts_by_slot"]
    inner_first_counts = tuple(counts)
    if (
        normalized["selected"] != DERIVED_DEPENDENCIES
        or inner_first_counts != EXPECTED_INNER_FIRST_COUNTS
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "independent liveness result differs from the registered result"
        )
    metrics = _proof_tree_metrics(normalized["proof"])
    fuel = FUEL_MULTIPLIER * metrics["proof_nodes"] + FUEL_OFFSET
    output_value = [
        CERTIFICATE_REPRESENTATION,
        fuel,
        deepcopy(evidence["root_target"]),
        normalized["proof"],
    ]
    output_raw = _compact_bytes(output_value) + b"\n"
    if (
        metrics
        != {
            "cut_nodes": OUTPUT_CUT_NODES,
            "proof_depth": OUTPUT_PROOF_DEPTH,
            "proof_nodes": OUTPUT_PROOF_NODES,
        }
        or fuel != OUTPUT_FUEL
        or len(output_raw) != OUTPUT_ARTIFACT_BYTES
        or _sha256(output_raw) != OUTPUT_ARTIFACT_SHA256
        or _sha256(_compact_bytes(normalized["proof"])) != OUTPUT_PROOF_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "independent transformed artifact identity drifted"
        )
    second = _normalize_encoded_spine(
        normalized["proof"],
        evidence["root_target"],
        DERIVED_DEPENDENCIES,
        evidence["dependencies"],
    )
    if (
        second["selected"] != DERIVED_DEPENDENCIES
        or second["proof"] != normalized["proof"]
        or tuple(second["counts_by_slot"]) != (2, 1)
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "independent cut-liveness transform is not idempotent"
        )
    rows = evidence["manifest_rows"]
    closure = _transitive_closure(DERIVED_DEPENDENCIES, rows)
    if (
        _lf_sha256(INPUT_DEPENDENCIES) != INPUT_VECTOR_LF_SHA256
        or _lf_sha256(DERIVED_DEPENDENCIES) != DERIVED_VECTOR_LF_SHA256
        or closure != EXPECTED_CLOSURE
        or _lf_sha256(closure) != EXPECTED_CLOSURE_LF_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "independent vector or retained closure identity drifted"
        )
    intermediate_raws: list[bytes] = []
    for intermediate_proof in normalized["closed_intermediates"]:
        intermediate_metrics = _proof_tree_metrics(intermediate_proof)
        intermediate_fuel = (
            FUEL_MULTIPLIER * intermediate_metrics["proof_nodes"] + FUEL_OFFSET
        )
        intermediate_raw = _compact_bytes(
            [
                CERTIFICATE_REPRESENTATION,
                intermediate_fuel,
                deepcopy(evidence["root_target"]),
                intermediate_proof,
            ]
        ) + b"\n"
        if len(intermediate_raw) > MAX_ARTIFACT_BYTES:
            raise DependencyVectorCutLivenessVerificationError(
                "independent intermediate artifact exceeds its byte bound"
            )
        intermediate_raws.append(intermediate_raw)
    if intermediate_raws[-1] != output_raw:
        raise DependencyVectorCutLivenessVerificationError(
            "final independent intermediate differs from the canonical output"
        )
    kernel_sources = _kernel_check_artifacts(
        root, evidence, intermediate_raws, output_raw
    )
    candidate_raw = _canonical_document_bytes_unchecked(candidate)
    if len(candidate_raw) > MAX_DOCUMENT_BYTES:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate document exceeds its byte limit"
        )
    candidate_root = _candidate_root(candidate)
    embedded = _candidate_artifact_bytes(candidate)
    if embedded != output_raw:
        raise DependencyVectorCutLivenessVerificationError(
            "candidate artifact bytes differ from independent output"
        )
    derived = {
        "evidence": evidence,
        "metrics": metrics,
        "steps": normalized["steps"],
    }
    _require_candidate_claims(candidate, derived, schema_identity)
    steps = [
        {
            "dependency": name,
            "hypothesis_occurrences": count,
            "outcome": outcome,
        }
        for (name, outcome), count in zip(
            EXPECTED_INNER_FIRST_OUTCOMES,
            EXPECTED_INNER_FIRST_COUNTS,
            strict=True,
        )
    ]
    theorem: dict[str, object] = {
        "candidate_artifact_sha256": OUTPUT_ARTIFACT_SHA256,
        "derived_direct_dependencies": list(DERIVED_DEPENDENCIES),
        "derived_direct_dependencies_lf_sha256": DERIVED_VECTOR_LF_SHA256,
        "index": EXPECTED_INDEX,
        "input_direct_cut_spine": list(INPUT_DEPENDENCIES),
        "input_direct_cut_spine_lf_sha256": INPUT_VECTOR_LF_SHA256,
        "name": EXPECTED_NAME,
        "normalization_steps_inner_first": steps,
        "output_fuel": OUTPUT_FUEL,
        "output_metrics": metrics,
        "output_proof_term_sha256": OUTPUT_PROOF_SHA256,
        "retained_transitive_closure": list(closure),
        "retained_transitive_closure_lf_sha256": EXPECTED_CLOSURE_LF_SHA256,
    }
    theorem["record_sha256"] = _sha256_json(theorem)
    body: dict[str, object] = {
        **_false_claims(),
        "candidate_artifact_sha256": _sha256(candidate_raw),
        "candidate_root_sha256": candidate_root,
        "derived_artifact_byte_identical": True,
        "derived_direct_vector_independently_reproduced": True,
        "encoded_tagged_array_transform_independently_executed": True,
        "format": VERIFICATION_FORMAT,
        "id": VERIFICATION_ID,
        "input_and_dependency_artifacts_independently_authenticated": True,
        "input_and_output_kernel_checked": True,
        "kernel_sources": kernel_sources,
        "logic_mode": LOGIC_MODE,
        "producer_imported_by_verifier": False,
        "proof_liveness_transform_idempotent": True,
        "schema": schema_identity,
        "schema_claim_boundary_sha256": _sha256_json(schema["claim_boundary"]),
        "status": VERIFICATION_STATUS,
        "theorem": theorem,
        "v": VERIFICATION_VERSION,
    }
    preimage = {
        "format": VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    result = {
        **body,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }
    return validate_dependency_vector_cut_liveness_verification(result)


def validate_dependency_vector_cut_liveness_verification(
    value: object,
) -> dict[str, object]:
    """Validate one detached independent verification receipt."""

    if type(value) is not dict:
        raise DependencyVectorCutLivenessVerificationError(
            "verification receipt must be one exact object"
        )
    _validate_json(value, max_depth=MAX_JSON_DEPTH, max_items=MAX_JSON_ITEMS)
    if set(value) != _VERIFICATION_TOP_LEVEL_FIELDS:
        raise DependencyVectorCutLivenessVerificationError(
            "verification receipt field set drifted"
        )
    for field in VERIFICATION_FALSE_FIELDS:
        if value.get(field) is not False:
            raise DependencyVectorCutLivenessVerificationError(
                f"verification broad claim {field!r} is not false"
            )
    required_true = (
        "derived_artifact_byte_identical",
        "derived_direct_vector_independently_reproduced",
        "encoded_tagged_array_transform_independently_executed",
        "input_and_dependency_artifacts_independently_authenticated",
        "input_and_output_kernel_checked",
        "proof_liveness_transform_idempotent",
    )
    if (
        value.get("format") != VERIFICATION_FORMAT
        or value.get("id") != VERIFICATION_ID
        or value.get("v") != VERIFICATION_VERSION
        or value.get("status") != VERIFICATION_STATUS
        or value.get("logic_mode") != LOGIC_MODE
        or value.get("producer_imported_by_verifier") is not False
        or any(value.get(field) is not True for field in required_true)
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "verification receipt envelope drifted"
        )
    theorem = value.get("theorem")
    if (
        type(theorem) is not dict
        or set(theorem) != _VERIFICATION_THEOREM_FIELDS
        or theorem.get("index") != EXPECTED_INDEX
        or theorem.get("name") != EXPECTED_NAME
        or tuple(theorem.get("input_direct_cut_spine", ())) != INPUT_DEPENDENCIES
        or tuple(theorem.get("derived_direct_dependencies", ()))
        != DERIVED_DEPENDENCIES
        or theorem.get("input_direct_cut_spine_lf_sha256")
        != INPUT_VECTOR_LF_SHA256
        or theorem.get("derived_direct_dependencies_lf_sha256")
        != DERIVED_VECTOR_LF_SHA256
        or theorem.get("retained_transitive_closure") != list(EXPECTED_CLOSURE)
        or theorem.get("retained_transitive_closure_lf_sha256")
        != EXPECTED_CLOSURE_LF_SHA256
        or theorem.get("normalization_steps_inner_first")
        != [
            {
                "dependency": name,
                "hypothesis_occurrences": count,
                "outcome": outcome,
            }
            for (name, outcome), count in zip(
                EXPECTED_INNER_FIRST_OUTCOMES,
                EXPECTED_INNER_FIRST_COUNTS,
                strict=True,
            )
        ]
        or theorem.get("candidate_artifact_sha256") != OUTPUT_ARTIFACT_SHA256
        or theorem.get("output_proof_term_sha256") != OUTPUT_PROOF_SHA256
        or theorem.get("output_fuel") != OUTPUT_FUEL
        or theorem.get("output_metrics")
        != {
            "cut_nodes": OUTPUT_CUT_NODES,
            "proof_depth": OUTPUT_PROOF_DEPTH,
            "proof_nodes": OUTPUT_PROOF_NODES,
        }
        or theorem.get("record_sha256")
        != _sha256_json(
            {key: item for key, item in theorem.items() if key != "record_sha256"}
        )
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "verification theorem receipt drifted"
        )
    candidate_root = value.get("candidate_root_sha256")
    candidate_sha = value.get("candidate_artifact_sha256")
    kernel_sources = value.get("kernel_sources")
    if (
        type(candidate_root) is not str
        or _SHA256_RE.fullmatch(candidate_root) is None
        or type(candidate_sha) is not str
        or _SHA256_RE.fullmatch(candidate_sha) is None
        or type(kernel_sources) is not dict
        or set(kernel_sources) != {"count", "load_mode", "preimage", "root_sha256"}
        or kernel_sources.get("count") != len(_KERNEL_SOURCE_FILES)
        or kernel_sources.get("load_mode")
        != "authenticated-source-bytes-source_to_code-private-namespace"
        or kernel_sources.get("root_sha256")
        != _sha256_json(kernel_sources.get("preimage"))
        or value.get("schema")
        != {
            "artifact_bytes": SCHEMA_SOURCE_BYTES,
            "artifact_sha256": SCHEMA_SOURCE_SHA256,
            "format": SCHEMA_FORMAT,
            "id": SCHEMA_ID,
            "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
            "v": 1,
        }
        or value.get("schema_claim_boundary_sha256")
        != SCHEMA_CLAIM_BOUNDARY_SHA256
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "verification source or candidate identities drifted"
        )
    kernel_preimage = kernel_sources["preimage"]
    expected_kernel_records = [
        {"bytes": byte_count, "path": path, "sha256": digest}
        for path, byte_count, digest in _KERNEL_SOURCE_FILES
    ]
    if kernel_preimage != {
        "format": "peano-hydra-a23d-cut-liveness-verifier-kernel-sources-preimage-v1",
        "records": expected_kernel_records,
        "v": 1,
    }:
        raise DependencyVectorCutLivenessVerificationError(
            "verification kernel source vector drifted"
        )
    root = value.get("root_sha256")
    preimage = value.get("root_preimage")
    detached = {
        key: deepcopy(item)
        for key, item in value.items()
        if key not in ("root_preimage", "root_sha256")
    }
    if (
        type(root) is not str
        or _SHA256_RE.fullmatch(root) is None
        or type(preimage) is not dict
        or preimage
        != {
            "format": VERIFICATION_ROOT_PREIMAGE_FORMAT,
            "payload": detached,
            "v": 1,
        }
        or _sha256_json(preimage) != root
    ):
        raise DependencyVectorCutLivenessVerificationError(
            "verification document root drifted"
        )
    return deepcopy(value)


def load_dependency_vector_cut_liveness_verification(
    path: Path,
) -> dict[str, object]:
    """Safely load one canonical independent verification receipt."""

    raw = _safe_regular_bytes(
        path, label="cut-liveness verification", limit=MAX_DOCUMENT_BYTES
    )
    value = _decode_json(
        raw, label="cut-liveness verification", limit=MAX_DOCUMENT_BYTES
    )
    validated = validate_dependency_vector_cut_liveness_verification(value)
    if canonical_verification_bytes(validated) != raw:
        raise DependencyVectorCutLivenessVerificationError(
            "cut-liveness verification is not canonical"
        )
    return validated


__all__ = [
    "DependencyVectorCutLivenessVerificationError",
    "canonical_verification_bytes",
    "derive_tagged_proof_liveness",
    "load_dependency_vector_cut_liveness_verification",
    "thin_tagged_proof_outer_context",
    "validate_dependency_vector_cut_liveness_verification",
    "verify_dependency_vector_cut_liveness",
]
