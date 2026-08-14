"""One-root proof-producing direct-Cut liveness normalization.

This untrusted A2.3d producer consumes only the exact retained replay pack.  It
does not import the living theorem registry, tactics, or any A2.1--A2.3
producer.  For ``odd_add_odd`` it authenticates the declared four-Cut outer
spine, then processes those Cuts inner-first.  A Cut is deleted only when its
bound proposition hypothesis has no binder-aware occurrence in the current
body; all remaining free proposition-hypothesis indices are lowered by one.

Every opaque lemma, intermediate proof, and final artifact is checked by the
unchanged intuitionistic kernel.  This establishes only a deterministic
vacuous-root-Cut normal form and its direct vector.  It establishes no
mathematical necessity, global minimality, best-known status, publication, or
authority.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass, fields, replace
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Mapping

from peano_lab.kernel.artifact_codec import (
    ArtifactDecodeError,
    ArtifactLimitError,
    decode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import (
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    Cut,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
    Proof,
)


CUT_LIVENESS_VERSION = 1
CUT_LIVENESS_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-cut-liveness-v1"
)
CUT_LIVENESS_ID = (
    "peano-hydra-l0-pilot-dependency-vector-cut-liveness-candidate-v1"
)
CUT_LIVENESS_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-cut-liveness-"
    "root-preimage-v1"
)
STATUS = "candidate-only-bounded-one-root-proof-producing-cut-liveness-normalization"
LOGIC_MODE = "intuitionistic"
ALGORITHM_ID = "binder-aware-inner-first-vacuous-direct-cut-elimination-v1"

EXPECTED_ROOT_INDEX = 256
EXPECTED_ROOT_NAME = "odd_add_odd"
EXPECTED_DECLARED_DEPENDENCIES = (
    "mul_add",
    "add_succ_left",
    "add_assoc",
    "add_comm",
)
EXPECTED_DERIVED_DEPENDENCIES = ("mul_add", "add_comm")
EXPECTED_INNER_FIRST_OUTCOMES = (
    ("add_comm", "retained-used"),
    ("add_assoc", "deleted-vacuous"),
    ("add_succ_left", "deleted-vacuous"),
    ("mul_add", "retained-used"),
)
EXPECTED_INITIAL_VECTOR_LF_SHA256 = (
    "9bb59dbdeb07badb9f8ca9d0cc951b71f38dbf7c3edcb1b189d53efcba1708cc"
)
EXPECTED_DERIVED_VECTOR_LF_SHA256 = (
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

EXPECTED_CANDIDATE_FUEL = 1936
EXPECTED_CANDIDATE_ARTIFACT_BYTES = 11_958
EXPECTED_CANDIDATE_ARTIFACT_SHA256 = (
    "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22"
)
EXPECTED_CANDIDATE_PROOF_SHA256 = (
    "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4"
)
EXPECTED_CANDIDATE_PROOF_NODES = 240
EXPECTED_CANDIDATE_PROOF_DEPTH = 30
EXPECTED_CANDIDATE_CUT_NODES = 5

MAX_SCHEMA_BYTES = 262_144
MAX_MANIFEST_BYTES = 4_000_000
MAX_REPORT_BYTES = 65_536
MAX_ARTIFACT_BYTES = 65_536
MAX_DOCUMENT_BYTES = 1_048_576
MAX_PROOF_NODES = 10_000
MAX_PROOF_DEPTH = 128
MAX_DEPENDENCIES = 4
MAX_TRANSFORM_VISITS = 50_000
MAX_JSON_NODES = 100_000
MAX_JSON_DEPTH = 64

SCHEMA_SOURCE_BYTES = 12_566
SCHEMA_SOURCE_SHA256 = (
    "388190b4235b9892b38193714b0331a35b6c533c0605072c5d0663ad9cd9c0aa"
)
SCHEMA_SEMANTIC_SHA256 = (
    "9e8887072cc6051cf9cb9177609ab31aed35ca305a42c7d9c22d4ac339b6f5c5"
)

_MODULE_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = Path(__file__).with_name(
    "library-pilot-dependency-vector-cut-liveness-schema-v1.json"
)
_REPLAY_ROOT_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
_MANIFEST_RELATIVE = _REPLAY_ROOT_RELATIVE / "manifest.json"
_REPORT_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1-report.json")

_MANIFEST_BYTES = 3_241_451
_MANIFEST_SHA256 = "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
_MANIFEST_ROOT_SHA256 = "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
_REPLAY_ROOT_SHA256 = "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
_REPORT_BYTES = 828
_REPORT_SHA256 = "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"

_ROOT_PIN = {
    "artifact_bytes": 14_977,
    "artifact_path": (
        "certificates/0256-odd_add_odd-"
        "7ecd5c3f4ac81e800fc5d14b07758681b78f66a868d3d265a811c725aa6558c7.pl2"
    ),
    "artifact_sha256": "7ecd5c3f4ac81e800fc5d14b07758681b78f66a868d3d265a811c725aa6558c7",
    "formula_sha256": "4d2aa6b4e387657e562641830dab2953890b5493d6e6858b6c36d73b06786c31",
    "fuel": 2432,
    "index": 256,
    "name": "odd_add_odd",
    "proof_term_sha256": "0199da96fdf6834e9c1affbc343a62e312c497c9a9c014904bf8cdd8ce5f5f38",
}

_DEPENDENCY_PINS = (
    {
        "artifact_bytes": 3447,
        "artifact_path": "certificates/0007-mul_add-aeabac97da97840a927c69265493c8a2355b711fa9fdc37b5c482b530b057cb7.pl2",
        "artifact_sha256": "aeabac97da97840a927c69265493c8a2355b711fa9fdc37b5c482b530b057cb7",
        "formula_sha256": "6c7d695dfd0c3b56e49507b7f510182794963f91ab9e5f1466dc40f145a7a0a5",
        "fuel": 632,
        "index": 7,
        "name": "mul_add",
        "proof_term_sha256": "c32deba7cbdcfff28fe47fc2f2515cbb684f754c9b6b96860c8c89b02dfdf1ac",
    },
    {
        "artifact_bytes": 1023,
        "artifact_path": "certificates/0001-add_succ_left-09d9cd46daa969e93fdb83d9119f8c14fb226f11356acc69882759e270371983.pl2",
        "artifact_sha256": "09d9cd46daa969e93fdb83d9119f8c14fb226f11356acc69882759e270371983",
        "formula_sha256": "9c089dd32a335c2b820b4ea3c0902821860bcb80bbf5c306c0fdad15c8da1756",
        "fuel": 232,
        "index": 1,
        "name": "add_succ_left",
        "proof_term_sha256": "769124fe14b55a54436635de5be893ee15ba997d5db435c159a3d00e611907d7",
    },
    {
        "artifact_bytes": 1368,
        "artifact_path": "certificates/0003-add_assoc-a239a7199c5294b1060e7f9a8244cd290036b5bc63f22ec767f68c9821026744.pl2",
        "artifact_sha256": "a239a7199c5294b1060e7f9a8244cd290036b5bc63f22ec767f68c9821026744",
        "formula_sha256": "4c7b9113d46e6c5646a169320d17464dcf78c0c97be26f4ef03a9d7f3afd3171",
        "fuel": 280,
        "index": 3,
        "name": "add_assoc",
        "proof_term_sha256": "bc649ea7f7bb208ab963a2cc5137fc00b005d261a35d447a065dd094faa7399f",
    },
    {
        "artifact_bytes": 2551,
        "artifact_path": "certificates/0002-add_comm-e7094296018260b6c03fb3846c61bacc94e8d0f39739379326db409d99aeef9f.pl2",
        "artifact_sha256": "e7094296018260b6c03fb3846c61bacc94e8d0f39739379326db409d99aeef9f",
        "formula_sha256": "25b3cc29a1427896f1aa3935bc167b449d4501668be477e477180454ba292f94",
        "fuel": 600,
        "index": 2,
        "name": "add_comm",
        "proof_term_sha256": "1d083e7da855b6e22c63dc081cd86cffa5beb4690f4298e6c804fe8717c4baaa",
    },
)

_KERNEL_SOURCE_PINS = (
    ("peano-lab/py/peano_lab/__init__.py", 257, "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a"),
    ("peano-lab/py/peano_lab/kernel/__init__.py", 263, "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84"),
    ("peano-lab/py/peano_lab/kernel/artifact_codec.py", 27_892, "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110"),
    ("peano-lab/py/peano_lab/kernel/checker.py", 10_738, "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19"),
    ("peano-lab/py/peano_lab/kernel/formulas.py", 10_950, "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"),
    ("peano-lab/py/peano_lab/kernel/proofs.py", 5_015, "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2"),
    ("peano-lab/py/peano_lab/kernel/subst.py", 5_165, "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3"),
    ("peano-lab/py/peano_lab/kernel/terms.py", 9_133, "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"),
)

_FALSE_CLAIMS = (
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

_PROOF_TYPES = (
    Hyp,
    ImpIntro,
    ImpElim,
    Cut,
    AndIntro,
    AndElimL,
    AndElimR,
    OrIntroL,
    OrIntroR,
    OrElim,
    BotElim,
    ForallIntro,
    ForallElim,
    ExistsIntro,
    ExistsElim,
    EqRefl,
    EqSym,
    EqTrans,
    CongS,
    CongAdd,
    CongMul,
    EqSubst,
    DNE,
    Axiom,
    Ind,
)

_PROPOSITION_BINDING_FIELDS = frozenset(
    {
        (ImpIntro, "body"),
        (Cut, "body"),
        (OrElim, "left_case"),
        (OrElim, "right_case"),
        (ExistsElim, "body"),
    }
)


class LibraryPilotDependencyVectorCutLivenessError(ValueError):
    """The fixed input, transform, result, or resource boundary is invalid."""


@dataclass(frozen=True, slots=True)
class _ArtifactCarrier:
    name: str
    index: int
    path: str
    raw: bytes
    fuel: int
    target: Formula
    proof: Proof
    artifact_sha256: str
    formula_sha256: str
    proof_term_sha256: str


@dataclass(frozen=True, slots=True)
class _DirectSpineNormalization:
    proof: Proof
    retained_dependencies: tuple[str, ...]
    input_spine: tuple[dict[str, object], ...]
    steps: tuple[dict[str, object], ...]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _compact_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_bytes(value))


def canonical_document_bytes(value: object) -> bytes:
    """Return strict, pretty canonical JSON with one terminal LF."""

    _validate_json(value)
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
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness document exceeds its byte limit"
        )
    return raw


def _validate_json(value: object) -> None:
    pending: list[tuple[object, int]] = [(value, 1)]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "JSON value exceeds its structural limit"
            )
        if current is None or type(current) in (bool, int, str):
            continue
        if type(current) is list:
            pending.extend((item, depth + 1) for item in current)
            continue
        if type(current) is dict:
            if not all(type(key) is str for key in current):
                raise LibraryPilotDependencyVectorCutLivenessError(
                    "JSON object keys must be exact strings"
                )
            pending.extend((item, depth + 1) for item in current.values())
            continue
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"unsupported JSON value {type(current).__name__}"
        )


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value: str) -> object:
    raise ValueError(f"unsupported JSON number {value!r}")


def _decode_object(raw: bytes, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_number,
            parse_float=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, RecursionError) as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"{label} must be one object"
        )
    _validate_json(value)
    return value


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _require_directory_chain(path: Path, *, label: str) -> None:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorCutLivenessError(
                    f"{label} contains a symlink or non-directory"
                )
    except LibraryPilotDependencyVectorCutLivenessError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot inspect {label}"
        ) from exc


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_regular_bytes(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label=f"{label} ancestors")
    try:
        inspected = absolute.lstat()
    except OSError as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _stat_identity(inspected) != _stat_identity(before)
        ):
            raise LibraryPilotDependencyVectorCutLivenessError(
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
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"{label} changed or exceeded its bound while read"
            )
        return raw
    except OSError as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)


def _safe_relative(value: object, *, label: str) -> Path:
    if type(value) is not str:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"{label} path is malformed"
        )
    relative = Path(value)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"{label} path is unsafe"
        )
    return relative


def _repository_root(value: Path | None) -> Path:
    root = _MODULE_ROOT if value is None else _lexical_absolute(value)
    _require_directory_chain(root, label="repository root")
    return root


def cut_liveness_schema() -> dict[str, object]:
    """Load and authenticate the immutable A2.3d preregistration schema."""

    raw = _read_regular_bytes(
        _SCHEMA_PATH, label="cut-liveness schema", limit=MAX_SCHEMA_BYTES
    )
    if len(raw) != SCHEMA_SOURCE_BYTES or _sha256_bytes(raw) != SCHEMA_SOURCE_SHA256:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness schema source identity drifted"
        )
    value = _decode_object(raw, label="cut-liveness schema")
    if (
        value.get("v") != CUT_LIVENESS_VERSION
        or value.get("format")
        != "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema"
        or value.get("id")
        != "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema-v1"
        or value.get("logic_mode") != LOGIC_MODE
        or _sha256_bytes(_compact_bytes(value)) != SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness schema semantic identity drifted"
        )
    return deepcopy(value)


def cut_liveness_schema_identity() -> dict[str, object]:
    value = cut_liveness_schema()
    return {
        "artifact_bytes": SCHEMA_SOURCE_BYTES,
        "artifact_sha256": SCHEMA_SOURCE_SHA256,
        "format": value["format"],
        "id": value["id"],
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": value["v"],
    }


def _proof_children(proof: Proof) -> tuple[tuple[str, Proof, bool], ...]:
    if type(proof) not in _PROOF_TYPES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"unsupported exact proof constructor {type(proof).__name__}"
        )
    result: list[tuple[str, Proof, bool]] = []
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            if type(child) not in _PROOF_TYPES:
                raise LibraryPilotDependencyVectorCutLivenessError(
                    f"unsupported exact proof constructor {type(child).__name__}"
                )
            result.append(
                (
                    item.name,
                    child,
                    (type(proof), item.name) in _PROPOSITION_BINDING_FIELDS,
                )
            )
    return tuple(result)


def _validate_cutoff(cutoff: int) -> None:
    if type(cutoff) is not int or cutoff < 0:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "hypothesis cutoff must be a non-negative exact integer"
        )


def _count_hypothesis_uses(proof: Proof, cutoff: int = 0) -> int:
    """Count structural uses of one proposition slot under all kernel binders."""

    _validate_cutoff(cutoff)
    if type(proof) not in _PROOF_TYPES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "hypothesis-use traversal needs an exact kernel proof"
        )
    pending: list[tuple[Proof, int]] = [(proof, cutoff)]
    visits = 0
    uses = 0
    while pending:
        current, current_cutoff = pending.pop()
        visits += 1
        if visits > MAX_TRANSFORM_VISITS:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "hypothesis-use traversal exceeded its visit limit"
            )
        if type(current) is Hyp:
            if type(current.i) is not int or current.i < 0:
                raise LibraryPilotDependencyVectorCutLivenessError(
                    "proof contains a malformed Hyp index"
                )
            if current.i == current_cutoff:
                uses += 1
            continue
        children = _proof_children(current)
        pending.extend(
            (child, current_cutoff + (1 if binds else 0))
            for _name, child, binds in reversed(children)
        )
    return uses


def _first_hypothesis_use_path(proof: Proof, cutoff: int = 0) -> tuple[str, ...] | None:
    _validate_cutoff(cutoff)
    pending: list[tuple[Proof, int, tuple[str, ...]]] = [(proof, cutoff, ())]
    visits = 0
    while pending:
        current, current_cutoff, path = pending.pop()
        visits += 1
        if visits > MAX_TRANSFORM_VISITS:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "hypothesis-path traversal exceeded its visit limit"
            )
        if type(current) is Hyp:
            if current.i == current_cutoff:
                return path + (f"Hyp[{current.i}]",)
            continue
        children = _proof_children(current)
        pending.extend(
            (
                child,
                current_cutoff + (1 if binds else 0),
                path + (f"{type(current).__name__}.{name}",),
            )
            for name, child, binds in reversed(children)
        )
    return None


def _drop_vacuous_hypothesis(proof: Proof, cutoff: int = 0) -> Proof:
    """Delete one unused proposition slot without entering term-variable scope."""

    _validate_cutoff(cutoff)
    if _count_hypothesis_uses(proof, cutoff) != 0:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cannot drop a proposition hypothesis that is used"
        )
    visits = 0

    def lower(current: Proof, current_cutoff: int) -> Proof:
        nonlocal visits
        visits += 1
        if visits > MAX_TRANSFORM_VISITS:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "hypothesis-lowering traversal exceeded its visit limit"
            )
        if type(current) is Hyp:
            if type(current.i) is not int or current.i < 0:
                raise LibraryPilotDependencyVectorCutLivenessError(
                    "proof contains a malformed Hyp index"
                )
            if current.i == current_cutoff:
                raise LibraryPilotDependencyVectorCutLivenessError(
                    "vacuity preflight disagreed with hypothesis lowering"
                )
            return Hyp(current.i - 1) if current.i > current_cutoff else current
        changes: dict[str, Proof] = {}
        for name, child, binds in _proof_children(current):
            changed = lower(child, current_cutoff + (1 if binds else 0))
            if changed is not child:
                changes[name] = changed
        return replace(current, **changes) if changes else current

    try:
        return lower(proof, cutoff)
    except RecursionError as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "hypothesis lowering exceeded the host recursion limit"
        ) from exc


def _proof_tree_metrics(proof: Proof) -> dict[str, int]:
    if type(proof) not in _PROOF_TYPES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "proof metrics need an exact kernel proof"
        )
    pending: list[tuple[Proof, int]] = [(proof, 1)]
    nodes = 0
    maximum_depth = 0
    cut_nodes = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        maximum_depth = max(maximum_depth, depth)
        cut_nodes += type(current) is Cut
        if nodes > MAX_PROOF_NODES or depth > MAX_PROOF_DEPTH:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "proof exceeds the registered node/depth limit"
            )
        pending.extend(
            (child, depth + 1)
            for _name, child, _binds in reversed(_proof_children(current))
        )
    return {
        "cut_nodes": cut_nodes,
        "proof_depth": maximum_depth,
        "proof_nodes": nodes,
    }


def _normalize_direct_spine(
    proof: Proof,
    target: Formula,
    dependencies: tuple[tuple[str, Formula, Proof], ...],
) -> _DirectSpineNormalization:
    """Authenticate, peel, and normalize one exact declared outer Cut spine."""

    if type(dependencies) is not tuple or not 1 <= len(dependencies) <= MAX_DEPENDENCIES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "direct spine dependencies must be one bounded exact tuple"
        )
    names: list[str] = []
    peeled: list[tuple[str, Formula, Proof]] = []
    input_rows: list[dict[str, object]] = []
    current = proof
    for declared_index, entry in enumerate(dependencies):
        if (
            type(entry) is not tuple
            or len(entry) != 3
            or type(entry[0]) is not str
            or not isinstance(entry[1], Formula)
            or type(entry[2]) not in _PROOF_TYPES
        ):
            raise LibraryPilotDependencyVectorCutLivenessError(
                "direct dependency carrier is malformed"
            )
        name, proposition, opaque_lemma = entry
        if name in names:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "direct dependency names must be unique"
            )
        names.append(name)
        if type(current) is not Cut:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "retained proof does not expose the exact declared outer Cut spine"
            )
        cut_lemma_bytes = encode_proof(current.lemma)
        opaque_lemma_bytes = encode_proof(opaque_lemma)
        if (
            current.proposition != proposition
            or current.conclusion != target
            or current.lemma != opaque_lemma
            or cut_lemma_bytes != opaque_lemma_bytes
            or not check((), current.lemma, proposition)
            or not check((), opaque_lemma, proposition)
        ):
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"outer Cut carrier differs from opaque dependency {name!r}"
            )
        input_rows.append(
            {
                "declared_index": declared_index,
                "name": name,
                "opaque_lemma_bytes": len(opaque_lemma_bytes),
                "opaque_lemma_empty_context_kernel_checked": True,
                "opaque_lemma_proof_sha256": _sha256_bytes(opaque_lemma_bytes),
                "proposition_formula_sha256": _sha256_bytes(
                    encode_formula(proposition)
                ),
                "root_conclusion_exact": True,
            }
        )
        peeled.append((name, proposition, opaque_lemma))
        current = current.body
    if type(current) is Cut and current.conclusion == target:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained proof exposes an unexpected additional root Cut"
        )
    propositions = tuple(item[1] for item in peeled)
    if not check(tuple(reversed(propositions)), current, target):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "peeled body failed under the exact declared dependency context"
        )

    retained_inner_first: list[str] = []
    step_rows: list[dict[str, object]] = []
    for processing_index, declared_index in enumerate(
        reversed(range(len(peeled)))
    ):
        name, proposition, opaque_lemma = peeled[declared_index]
        before_sha = _sha256_bytes(encode_proof(current))
        use_count = _count_hypothesis_uses(current)
        first_path = _first_hypothesis_use_path(current)
        if bool(use_count) != (first_path is not None):
            raise LibraryPilotDependencyVectorCutLivenessError(
                "hypothesis count and first-use path disagree"
            )
        if use_count:
            outcome = "retained-used"
            current = Cut(proposition, target, opaque_lemma, current)
            retained_inner_first.append(name)
        else:
            outcome = "deleted-vacuous"
            current = _drop_vacuous_hypothesis(current)
        surrounding_context = tuple(reversed(propositions[:declared_index]))
        if not check(surrounding_context, current, target):
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"intermediate proof failed after processing {name!r}"
            )
        step_rows.append(
            {
                "bound_hypothesis_use_count": use_count,
                "declared_index": declared_index,
                "dependency": name,
                "first_use_path": None if first_path is None else list(first_path),
                "input_body_proof_sha256": before_sha,
                "intermediate_kernel_checked": True,
                "opaque_lemma_proof_sha256": _sha256_bytes(
                    encode_proof(opaque_lemma)
                ),
                "outcome": outcome,
                "output_proof_sha256": _sha256_bytes(encode_proof(current)),
                "processing_index": processing_index,
                "surrounding_context_nearest_first": list(
                    reversed(names[:declared_index])
                ),
            }
        )
    retained = tuple(reversed(retained_inner_first))
    if not check((), current, target):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "normalized proof failed empty-context checking"
        )
    return _DirectSpineNormalization(
        proof=current,
        retained_dependencies=retained,
        input_spine=tuple(input_rows),
        steps=tuple(step_rows),
    )


def _lf_receipt(names: tuple[str, ...]) -> dict[str, object]:
    if type(names) is not tuple or not all(type(name) is str for name in names):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "LF receipt needs an exact name tuple"
        )
    raw = ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    return {
        "count": len(names),
        "dependencies": list(names),
        "lf_bytes": len(raw),
        "lf_sha256": _sha256_bytes(raw),
    }


def _false_claims() -> dict[str, bool]:
    return {name: False for name in _FALSE_CLAIMS}


def _manifest_rows(document: Mapping[str, object]) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list or len(rows) != 384:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "replay manifest theorem rows differ"
        )
    table: dict[str, dict[str, object]] = {}
    indexes: set[int] = set()
    for row in rows:
        if type(row) is not dict:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "replay theorem row is malformed"
            )
        name = row.get("name")
        index = row.get("index")
        if (
            type(name) is not str
            or type(index) is not int
            or name in table
            or index in indexes
        ):
            raise LibraryPilotDependencyVectorCutLivenessError(
                "replay theorem names/indexes are malformed or duplicate"
            )
        table[name] = row
        indexes.add(index)
    return table


def _require_row_pin(row: Mapping[str, object], pin: Mapping[str, object]) -> None:
    artifact = row.get("artifact")
    if type(artifact) is not dict:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"replay artifact row for {pin['name']!r} is malformed"
        )
    observed = {
        "artifact_bytes": artifact.get("bytes"),
        "artifact_path": artifact.get("path"),
        "artifact_sha256": artifact.get("sha256"),
        "formula_sha256": row.get("formula_sha256"),
        "fuel": artifact.get("fuel"),
        "index": row.get("index"),
        "name": row.get("name"),
        "proof_term_sha256": row.get("proof_term_sha256"),
    }
    if observed != dict(pin):
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"retained replay row drifted for {pin['name']!r}"
        )


def _load_carrier(
    root: Path,
    row: Mapping[str, object],
    pin: Mapping[str, object],
) -> _ArtifactCarrier:
    _require_row_pin(row, pin)
    relative = _safe_relative(pin["artifact_path"], label=str(pin["name"]))
    path = root / _REPLAY_ROOT_RELATIVE / relative
    raw = _read_regular_bytes(
        path, label=f"{pin['name']} replay artifact", limit=MAX_ARTIFACT_BYTES
    )
    if len(raw) != pin["artifact_bytes"] or _sha256_bytes(raw) != pin["artifact_sha256"]:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"retained replay artifact drifted for {pin['name']!r}"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=MAX_PROOF_NODES,
            max_depth=MAX_PROOF_DEPTH,
        )
    except (ArtifactDecodeError, ArtifactLimitError, TypeError, ValueError) as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"cannot decode retained artifact {pin['name']!r}"
        ) from exc
    formula_sha = _sha256_bytes(encode_formula(target))
    proof_sha = _sha256_bytes(encode_proof(proof))
    if (
        fuel != pin["fuel"]
        or formula_sha != pin["formula_sha256"]
        or proof_sha != pin["proof_term_sha256"]
        or encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        != raw
        or not check((), proof, target)
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            f"retained artifact {pin['name']!r} failed exact replay"
        )
    _proof_tree_metrics(proof)
    return _ArtifactCarrier(
        name=str(pin["name"]),
        index=int(pin["index"]),
        path=str(pin["artifact_path"]),
        raw=raw,
        fuel=fuel,
        target=target,
        proof=proof,
        artifact_sha256=str(pin["artifact_sha256"]),
        formula_sha256=formula_sha,
        proof_term_sha256=proof_sha,
    )


def _load_fixed_inputs(
    root: Path,
) -> tuple[
    dict[str, object],
    dict[str, dict[str, object]],
    _ArtifactCarrier,
    tuple[_ArtifactCarrier, ...],
]:
    manifest_raw = _read_regular_bytes(
        root / _MANIFEST_RELATIVE,
        label="retained replay manifest",
        limit=MAX_MANIFEST_BYTES,
    )
    if len(manifest_raw) != _MANIFEST_BYTES or _sha256_bytes(manifest_raw) != _MANIFEST_SHA256:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained replay manifest identity drifted"
        )
    manifest = _decode_object(manifest_raw, label="retained replay manifest")
    if (
        manifest.get("theorem_count") != 384
        or manifest.get("logic_mode") != LOGIC_MODE
        or manifest.get("root_sha256") != _MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != _REPLAY_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained replay manifest roots or mode drifted"
        )
    report_raw = _read_regular_bytes(
        root / _REPORT_RELATIVE,
        label="retained replay report",
        limit=MAX_REPORT_BYTES,
    )
    if len(report_raw) != _REPORT_BYTES or _sha256_bytes(report_raw) != _REPORT_SHA256:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained replay report identity drifted"
        )
    report = _decode_object(report_raw, label="retained replay report")
    if (
        report.get("kernel_checked_count") != 384
        or report.get("theorem_count") != 384
        or report.get("logic_mode") != LOGIC_MODE
        or report.get("manifest_root_sha256") != _MANIFEST_ROOT_SHA256
        or report.get("replay_root_sha256") != _REPLAY_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained replay report differs from the manifest"
        )
    rows = _manifest_rows(manifest)
    root_row = rows.get(EXPECTED_ROOT_NAME)
    if root_row is None:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained replay root is missing"
        )
    if tuple(root_row.get("declared_dependencies", ())) != EXPECTED_DECLARED_DEPENDENCIES:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained root declared dependency vector drifted"
        )
    root_carrier = _load_carrier(root, root_row, _ROOT_PIN)
    dependencies: list[_ArtifactCarrier] = []
    for pin in _DEPENDENCY_PINS:
        row = rows.get(str(pin["name"]))
        if row is None:
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"retained dependency {pin['name']!r} is missing"
            )
        dependencies.append(_load_carrier(root, row, pin))
    return manifest, rows, root_carrier, tuple(dependencies)


def _transitive_closure(
    direct: tuple[str, ...], rows: Mapping[str, Mapping[str, object]]
) -> tuple[str, ...]:
    seen: set[str] = set()
    pending = list(direct)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = rows.get(name)
        if row is None:
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"closure contains unknown theorem {name!r}"
            )
        dependencies = row.get("declared_dependencies")
        if (
            type(dependencies) is not list
            or not all(type(item) is str for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"closure dependency vector is malformed for {name!r}"
            )
        seen.add(name)
        pending.extend(dependencies)
    return tuple(sorted(seen, key=lambda name: int(rows[name]["index"])))


def _subtree_hash_counts(
    proof: Proof, wanted: Mapping[str, str]
) -> dict[str, int]:
    counts = {name: 0 for name in wanted}
    pending = [proof]
    visits = 0
    while pending:
        current = pending.pop()
        visits += 1
        if visits > MAX_TRANSFORM_VISITS:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "subtree scan exceeded its visit limit"
            )
        digest = _sha256_bytes(encode_proof(current))
        for name, expected in wanted.items():
            if digest == expected:
                counts[name] += 1
        pending.extend(
            child for _name, child, _binds in reversed(_proof_children(current))
        )
    return counts


def _implementation_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, expected_bytes, expected_sha in _KERNEL_SOURCE_PINS:
        raw = _read_regular_bytes(
            _MODULE_ROOT / relative,
            label=f"implementation source {relative}",
            limit=MAX_DOCUMENT_BYTES,
        )
        if len(raw) != expected_bytes or _sha256_bytes(raw) != expected_sha:
            raise LibraryPilotDependencyVectorCutLivenessError(
                f"implementation source drifted: {relative}"
            )
        rows.append(
            {
                "bytes": expected_bytes,
                "path": relative,
                "sha256": expected_sha,
            }
        )
    module_raw = _read_regular_bytes(
        Path(__file__), label="cut-liveness producer source", limit=MAX_DOCUMENT_BYTES
    )
    rows.append(
        {
            "bytes": len(module_raw),
            "path": "training/peano_hydra/library_pilot_dependency_vector_cut_liveness.py",
            "sha256": _sha256_bytes(module_raw),
        }
    )
    return rows


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _build_candidate_dependency_vector_cut_liveness(root: Path) -> dict[str, object]:
    manifest, rows, root_carrier, dependency_carriers = _load_fixed_inputs(root)
    dependency_tuple = tuple(
        (carrier.name, carrier.target, carrier.proof)
        for carrier in dependency_carriers
    )
    normalization = _normalize_direct_spine(
        root_carrier.proof, root_carrier.target, dependency_tuple
    )
    outcomes = tuple(
        (str(step["dependency"]), str(step["outcome"]))
        for step in normalization.steps
    )
    if (
        normalization.retained_dependencies != EXPECTED_DERIVED_DEPENDENCIES
        or outcomes != EXPECTED_INNER_FIRST_OUTCOMES
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness normalization outcome drifted"
        )

    initial_vector = _lf_receipt(EXPECTED_DECLARED_DEPENDENCIES)
    derived_vector = _lf_receipt(normalization.retained_dependencies)
    if (
        initial_vector["lf_sha256"] != EXPECTED_INITIAL_VECTOR_LF_SHA256
        or derived_vector["lf_sha256"] != EXPECTED_DERIVED_VECTOR_LF_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "direct-vector LF identity drifted"
        )
    initial_closure = _transitive_closure(EXPECTED_DECLARED_DEPENDENCIES, rows)
    derived_closure = _transitive_closure(
        normalization.retained_dependencies, rows
    )
    initial_closure_receipt = _lf_receipt(initial_closure)
    derived_closure_receipt = _lf_receipt(derived_closure)
    if (
        initial_closure != EXPECTED_CLOSURE
        or derived_closure != EXPECTED_CLOSURE
        or initial_closure_receipt["lf_sha256"] != EXPECTED_CLOSURE_LF_SHA256
        or derived_closure_receipt["lf_sha256"] != EXPECTED_CLOSURE_LF_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "retained-graph descriptive closure drifted"
        )

    proof = normalization.proof
    proof_bytes = encode_proof(proof)
    proof_sha = _sha256_bytes(proof_bytes)
    metrics = _proof_tree_metrics(proof)
    fuel = 8 * metrics["proof_nodes"] + 16
    candidate_raw = encode_artifact_bounded(
        fuel, root_carrier.target, proof, max_bytes=MAX_ARTIFACT_BYTES
    )
    if (
        proof_sha != EXPECTED_CANDIDATE_PROOF_SHA256
        or metrics
        != {
            "cut_nodes": EXPECTED_CANDIDATE_CUT_NODES,
            "proof_depth": EXPECTED_CANDIDATE_PROOF_DEPTH,
            "proof_nodes": EXPECTED_CANDIDATE_PROOF_NODES,
        }
        or fuel != EXPECTED_CANDIDATE_FUEL
        or len(candidate_raw) != EXPECTED_CANDIDATE_ARTIFACT_BYTES
        or _sha256_bytes(candidate_raw) != EXPECTED_CANDIDATE_ARTIFACT_SHA256
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "canonical cut-liveness candidate identity drifted"
        )
    try:
        decoded_fuel, decoded_target, decoded_proof = decode_artifact(
            candidate_raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=MAX_PROOF_NODES,
            max_depth=MAX_PROOF_DEPTH,
        )
    except (ArtifactDecodeError, ArtifactLimitError, TypeError, ValueError) as exc:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cannot decode the canonical cut-liveness candidate"
        ) from exc
    if (
        decoded_fuel != fuel
        or decoded_target != root_carrier.target
        or encode_proof(decoded_proof) != proof_bytes
        or not check((), decoded_proof, decoded_target)
        or encode_artifact_bounded(
            decoded_fuel,
            decoded_target,
            decoded_proof,
            max_bytes=MAX_ARTIFACT_BYTES,
        )
        != candidate_raw
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "canonical candidate failed decode/re-encode replay"
        )

    derived_by_name = {
        carrier.name: carrier for carrier in dependency_carriers
    }
    second = _normalize_direct_spine(
        proof,
        root_carrier.target,
        tuple(
            (name, derived_by_name[name].target, derived_by_name[name].proof)
            for name in normalization.retained_dependencies
        ),
    )
    if (
        second.proof != proof
        or encode_proof(second.proof) != proof_bytes
        or second.retained_dependencies != normalization.retained_dependencies
        or any(step["outcome"] != "retained-used" for step in second.steps)
    ):
        raise LibraryPilotDependencyVectorCutLivenessError(
            "post-transform idempotence check failed"
        )

    opaque_hashes = {
        carrier.name: carrier.proof_term_sha256
        for carrier in dependency_carriers
    }
    before_counts = _subtree_hash_counts(root_carrier.proof, opaque_hashes)
    after_counts = _subtree_hash_counts(proof, opaque_hashes)
    if before_counts != {
        "mul_add": 1,
        "add_succ_left": 2,
        "add_assoc": 2,
        "add_comm": 1,
    } or after_counts != {
        "mul_add": 1,
        "add_succ_left": 1,
        "add_assoc": 1,
        "add_comm": 1,
    }:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "opaque lemma subtree survival counts drifted"
        )
    subtree_rows = [
        {
            "dependency": carrier.name,
            "direct_cut_retained": carrier.name
            in normalization.retained_dependencies,
            "input_subtree_occurrences": before_counts[carrier.name],
            "opaque_lemma_proof_sha256": carrier.proof_term_sha256,
            "output_subtree_occurrences": after_counts[carrier.name],
            "survives_elsewhere_after_root_cut_deletion": (
                carrier.name not in normalization.retained_dependencies
                and after_counts[carrier.name] > 0
            ),
        }
        for carrier in dependency_carriers
    ]

    input_spine = []
    for structural, carrier in zip(
        normalization.input_spine, dependency_carriers, strict=True
    ):
        if structural["opaque_lemma_proof_sha256"] != carrier.proof_term_sha256:
            raise LibraryPilotDependencyVectorCutLivenessError(
                "structural spine lemma hash differs from retained artifact"
            )
        input_spine.append(
            {
                **structural,
                "artifact_bytes": len(carrier.raw),
                "artifact_path": carrier.path,
                "artifact_sha256": carrier.artifact_sha256,
                "dependency_index": carrier.index,
                "formula_sha256": carrier.formula_sha256,
            }
        )

    theorem: dict[str, object] = {
        **_false_claims(),
        "bounded_one_root_cut_liveness_complete": True,
        "candidate_artifact": {
            "artifact_base64": base64.b64encode(candidate_raw).decode("ascii"),
            "artifact_bytes": len(candidate_raw),
            "artifact_sha256": _sha256_bytes(candidate_raw),
            "canonical_roundtrip_checked": True,
            "empty_context_kernel_checked": True,
            "formula_sha256": root_carrier.formula_sha256,
            "fuel": fuel,
            "fuel_basis": {
                "formula": "8 * intrinsic_proof_nodes + 16",
                "role": "deterministic-replay-envelope-metadata-not-a-comparison-axis-or-authority",
            },
            "proof_term_sha256": proof_sha,
            "tree_metrics": metrics,
        },
        "closure_context": {
            "basis": "retained-manifest-graph-descriptive-context-not-direct-vector-input",
            "derived_vector_closure": derived_closure_receipt,
            "dropped_direct_dependencies_remaining_reachable": [
                name
                for name in EXPECTED_DECLARED_DEPENDENCIES
                if name not in normalization.retained_dependencies
                and name in derived_closure
            ],
            "initial_vector_closure": initial_closure_receipt,
            "unchanged": initial_closure == derived_closure,
        },
        "derived_direct_vector": derived_vector,
        "index": EXPECTED_ROOT_INDEX,
        "initial_direct_vector": initial_vector,
        "input_direct_cut_spine": input_spine,
        "name": EXPECTED_ROOT_NAME,
        "normalization_steps_inner_first": [
            dict(step) for step in normalization.steps
        ],
        "opaque_lemma_subtree_survival": subtree_rows,
        "post_transform_idempotence": {
            "checked": True,
            "proof_term_sha256": proof_sha,
            "retained_dependencies": list(second.retained_dependencies),
            "second_pass_outcomes_inner_first": [
                {
                    "dependency": step["dependency"],
                    "outcome": step["outcome"],
                }
                for step in second.steps
            ],
        },
        "proof_producing_cut_liveness_normalization_complete": True,
        "statement": {
            "formula_sha256": root_carrier.formula_sha256,
            "target_preserved_exactly": True,
        },
    }
    theorem["record_sha256"] = _record_hash(theorem)

    implementation_rows = _implementation_rows()
    body: dict[str, object] = {
        **_false_claims(),
        "aggregate": {
            "candidate_artifact_count": 1,
            "deleted_vacuous_root_cut_count": 2,
            "derived_direct_dependency_count": 2,
            "initial_direct_dependency_count": 4,
            "pilot_theorem_count": 1,
            "retained_used_root_cut_count": 2,
        },
        "algorithm": {
            "id": ALGORITHM_ID,
            "opaque_direct_lemmas_transformed": False,
            "processing_order": "inner-first",
            "proof_producing": True,
            "scope": "exact-declared-root-direct-cut-spine-only",
        },
        "bounded_one_root_protocol_executed": True,
        "format": CUT_LIVENESS_FORMAT,
        "id": CUT_LIVENESS_ID,
        "implementation": {
            "source_count": len(implementation_rows),
            "source_root_sha256": _sha256_json(
                {"format": "peano-hydra-a23d-source-vector-v1", "sources": implementation_rows, "v": 1}
            ),
            "sources": implementation_rows,
        },
        "inputs": {
            "dependency_artifacts": [
                {
                    "artifact_bytes": len(carrier.raw),
                    "artifact_path": carrier.path,
                    "artifact_sha256": carrier.artifact_sha256,
                    "formula_sha256": carrier.formula_sha256,
                    "index": carrier.index,
                    "name": carrier.name,
                    "proof_term_sha256": carrier.proof_term_sha256,
                }
                for carrier in dependency_carriers
            ],
            "replay_manifest": {
                "artifact_bytes": _MANIFEST_BYTES,
                "artifact_path": _MANIFEST_RELATIVE.as_posix(),
                "artifact_sha256": _MANIFEST_SHA256,
                "manifest_root_sha256": manifest["root_sha256"],
                "replay_root_sha256": manifest["replay_root_sha256"],
            },
            "replay_report": {
                "artifact_bytes": _REPORT_BYTES,
                "artifact_path": _REPORT_RELATIVE.as_posix(),
                "artifact_sha256": _REPORT_SHA256,
            },
            "root_artifact": {
                "artifact_bytes": len(root_carrier.raw),
                "artifact_path": root_carrier.path,
                "artifact_sha256": root_carrier.artifact_sha256,
                "formula_sha256": root_carrier.formula_sha256,
                "fuel": root_carrier.fuel,
                "index": root_carrier.index,
                "name": root_carrier.name,
                "proof_term_sha256": root_carrier.proof_term_sha256,
            },
        },
        "logic_mode": LOGIC_MODE,
        "schema": cut_liveness_schema_identity(),
        "status": STATUS,
        "theorem": theorem,
        "theorem_count": 1,
        "theorem_record_root_sha256": theorem["record_sha256"],
        "v": CUT_LIVENESS_VERSION,
    }
    root_preimage = {
        "format": CUT_LIVENESS_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": CUT_LIVENESS_VERSION,
    }
    result = {
        **body,
        "root_preimage": root_preimage,
        "root_sha256": _sha256_json(root_preimage),
    }
    canonical_document_bytes(result)
    return result


def build_candidate_dependency_vector_cut_liveness(
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Build the exact one-root candidate; any unknown or drift aborts."""

    cut_liveness_schema()
    return deepcopy(
        _build_candidate_dependency_vector_cut_liveness(
            _repository_root(repository_root)
        )
    )


def validate_dependency_vector_cut_liveness(
    value: object,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Validate a candidate by exact reconstruction from pinned inputs."""

    if type(value) is not dict:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness candidate must be one object"
        )
    _validate_json(value)
    expected = _build_candidate_dependency_vector_cut_liveness(
        _repository_root(repository_root)
    )
    if value != expected:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness candidate differs from exact reconstruction"
        )
    return _decode_object(
        canonical_document_bytes(expected), label="validated cut-liveness candidate"
    )


def load_dependency_vector_cut_liveness(
    path: Path,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Load one canonical candidate and reconstruct the exact transformation."""

    raw = _read_regular_bytes(
        path, label="cut-liveness candidate", limit=MAX_DOCUMENT_BYTES
    )
    value = _decode_object(raw, label="cut-liveness candidate")
    if canonical_document_bytes(value) != raw:
        raise LibraryPilotDependencyVectorCutLivenessError(
            "cut-liveness candidate is not canonical"
        )
    return validate_dependency_vector_cut_liveness(
        value, repository_root=repository_root
    )


__all__ = [
    "ALGORITHM_ID",
    "CUT_LIVENESS_FORMAT",
    "CUT_LIVENESS_ID",
    "CUT_LIVENESS_ROOT_PREIMAGE_FORMAT",
    "CUT_LIVENESS_VERSION",
    "EXPECTED_DECLARED_DEPENDENCIES",
    "EXPECTED_DERIVED_DEPENDENCIES",
    "EXPECTED_ROOT_INDEX",
    "EXPECTED_ROOT_NAME",
    "LibraryPilotDependencyVectorCutLivenessError",
    "build_candidate_dependency_vector_cut_liveness",
    "canonical_document_bytes",
    "cut_liveness_schema",
    "cut_liveness_schema_identity",
    "load_dependency_vector_cut_liveness",
    "validate_dependency_vector_cut_liveness",
]
