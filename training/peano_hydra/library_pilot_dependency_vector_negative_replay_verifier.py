"""Tactic-free structural verifier for the bounded Hydra A2.3c result.

This module deliberately imports only the Python standard library.  It never
imports or executes the A2.3c negative replayer, the Peano tactic engine, the
theorem library, the kernel, or ``training.peano_hydra`` package initializers.
It authenticates the frozen producer protocol and retained A2.3b evidence,
then independently checks canonical JSON, hashes, ordering, vectors, exact
registered commands and diagnostics, baseline receipts, and the 44-to-22
route-label join.

A passing receipt is structural evidence only.  This verifier does not bind a
WMI execution receipt, rerun a baseline, replay a negative task, or establish
tactic semantics, route rejection, necessity, minimality, vector completeness,
optimization, publication authority, theorem admission, or A2 completion.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping, Sequence


VERIFICATION_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "independent-verification"
)
VERIFICATION_VERSION = 1
VERIFICATION_ID = (
    "independent-a2.3c-pilot-vector-negative-replay-structural-"
    "verification-v1"
)
VERIFICATION_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "independent-verification-root-preimage"
)
VERIFICATION_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "independent-verification-records-preimage"
)
PROTOCOL_SOURCES_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "verified-protocol-sources-preimage"
)
RETAINED_EVIDENCE_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "verified-retained-evidence-preimage"
)

CANDIDATE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay"
)
CANDIDATE_VERSION = 1
CANDIDATE_ID = "independent-a2.3c-pilot-vector-negative-replay-v1"
CANDIDATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "root-preimage"
)
CANDIDATE_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "records-preimage"
)
RETAINED_JOIN_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-"
    "retained-route-join-preimage"
)

A23B_CANDIDATE_FORMAT = "peano-hydra-library-pilot-dependency-vector-audit"
A23B_CANDIDATE_ID = "authoring-l0-pilot-dependency-vector-audit-candidate-v1"
A23B_CANDIDATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-root-preimage"
)
A23B_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-records-preimage"
)
A23B_ATTEMPTS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-attempts-preimage"
)

SCHEMA_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-schema"
)
SCHEMA_ID = "independent-a2.3c-pilot-dependency-vector-negative-replay-v1"
SCHEMA_SEMANTIC_SHA256 = (
    "a0d84c3168a9b779bfb5fdc483a2ec847e4cc34f85bcf8aee4c7351a6363ccb0"
)
LOGIC_MODE = "intuitionistic"
READABLE_ROUTE = "readable-direct-closure"
LAYERED_ROUTE = "proposed-layered-closure-construction"
ROUTES = (READABLE_ROUTE, LAYERED_ROUTE)
EXPECTED_BASELINE_COUNT = 3
EXPECTED_OBSERVATION_COUNT = 22
EXPECTED_RETAINED_ROUTE_ROW_COUNT = 44
PYCACHE_PREFIX = "/proc/peano-hydra-a23c-disabled-pycache"

MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_SOURCE_BYTES = 16_000_000
MAX_JSON_DEPTH = 256
MAX_JSON_ITEMS = 4_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

GLOBAL_FALSE_FIELDS = (
    "a2_complete",
    "bounded_three_root_vector_audit_complete",
    "dependency_necessity_established",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_ready",
    "lineage_complete",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "proof_authority",
    "public_graph_applied",
    "publication_authority",
    "publication_ready",
    "publication_union_complete",
    "publication_union_verified",
    "retrieval_eligible",
    "review_complete",
    "route_rejections_independently_verified",
    "theorem_admission_authority",
    "training_eligible",
    "vector_optimizer_executed",
)
VERIFICATION_FALSE_FIELDS = (
    *GLOBAL_FALSE_FIELDS,
    "execution_receipt_bound",
    "kernel_baselines_independently_reexecuted",
    "negative_observations_independently_verified",
    "negative_replays_independently_reexecuted",
    "tactic_semantics_independently_verified",
)

PROTOCOL_SOURCE_FILES = (
    (
        "training/peano_hydra/"
        "library-pilot-dependency-vector-negative-replay-schema-v1.json",
        26_551,
        "be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4",
    ),
    (
        "training/peano_hydra/"
        "library_pilot_dependency_vector_negative_replay.py",
        91_304,
        "f5b5dd45c0ce4e2ed5587fd41b7ea206e92ee05526aebf7be96d80f5bb591aa4",
    ),
    (
        "scripts/"
        "verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py",
        49_259,
        "524ced1b5ca78040ddccc3030f2d5eee9f10c8bdf455ea96efb625595c72759b",
    ),
    (
        "peano-lab/py/tests/"
        "test_peano_hydra_library_pilot_dependency_vector_negative_replay.py",
        87_120,
        "dc5591dcc9d1e48028d1fbaf31971e65bc10c69377167b50317d4558596e6e82",
    ),
)

RETAINED_SOURCE_EVIDENCE_FILES = (
    (
        "a2.3b_producer_source_state",
        "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/inputs/"
        "producer-source-state.json",
        2_405,
        "ecf037e5d684a7472c2b02c917b5962e87daef02c688967f28b05afd85e339b0",
        "d92e9df55aea87241618fa026ee90730a4fc1b330b8d732030526afc5f501e09",
    ),
    (
        "a2.3b_producer_git_verification",
        "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/inputs/"
        "producer-git-verification-receipt.json",
        29_092,
        "384392a3a92a1e173576edb415f21f695729cdc71f81bf125afde65fce1041f6",
        "dfaf7d243881041729b8eb278e165046cb37099bcd0e582f2584edbc54c04ad5",
    ),
)

EXPECTED_THEOREMS = (
    {
        "dependencies": ("mul_add", "add_assoc", "add_comm"),
        "index": 256,
        "name": "odd_add_odd",
        "script_command_count": 10,
        "script_sha256": (
            "4d303cb1b7886cceba15a4d29f198ca16eff7aabca04ca577ae48d06878eed59"
        ),
        "statement_sha256": (
            "bd3780bb05fa5b37c137f073d0824b16479e754d20ae5a2088784b2161e92376"
        ),
    },
    {
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
        "index": 376,
        "name": "finite_bounded_injective_surjective",
        "script_command_count": 178,
        "script_sha256": (
            "6f501cc65ba7d78844c5dd6f42463be97c89b32c6dc2e19d40236a7618315533"
        ),
        "statement_sha256": (
            "9e0cad653da9de17ab7bbac3cb3bf49bc6d4a1304bda508669943b25fd247257"
        ),
    },
    {
        "dependencies": (
            "beta_product_replace_balance",
            "beta_product_succ_decompose",
            "beta_at_unique",
            "le_succ",
            "lt_irrefl_expanded",
        ),
        "index": 379,
        "name": "beta_product_swap_last_invariant",
        "script_command_count": 102,
        "script_sha256": (
            "b84a265093efa741e13cb8ac729dc53ce9baca8710dd51fac2b6c17534e373ed"
        ),
        "statement_sha256": (
            "a23f0b2f4451b4e423b9f15132ac02b6a035ce4d06f8eb95d744977109272465"
        ),
    },
)

# Ordered by root and then reverse declared dependency order.  Formula hashes
# are independently frozen encodings of the exact dependency-curried targets;
# this structural verifier never imports the formula encoder to recreate them.
EXPECTED_TASKS = (
    ("odd_add_odd", "add_comm", 9, "simp [mul_add, add_assoc, add_comm]", "705d6ba0ee903da62d1224f14e841e276ccf4fba417dea196f6b46bb3927bba3"),
    ("odd_add_odd", "add_assoc", 9, "simp [mul_add, add_assoc, add_comm]", "7c92297072fbe063986f1d05d413c4e80c467d09364035c0510013b701bf5837"),
    ("odd_add_odd", "mul_add", 9, "simp [mul_add, add_assoc, add_comm]", "920f6a9654a79e252d72c436107bfb954f5cd875160a079fa70cce3ff7004c04"),
    ("finite_bounded_injective_surjective", "lt_irrefl_expanded", 107, "specialize lt_irrefl_expanded n", "821604bc830ccc1df379c88d29b8490ec117e863f48acf9ccee00cc91c3fa33c"),
    ("finite_bounded_injective_surjective", "le_refl", 96, "specialize le_refl (S n)", "e1a70f2058f1098ecb8bb7839351d380603499e0c0ba432e26a6f77512a3e85a"),
    ("finite_bounded_injective_surjective", "le_succ", 91, "specialize le_succ (S j)", "fafd4370ff4385651365ba347629a505956b7bb65c53daad69377adf9b2a024a"),
    ("finite_bounded_injective_surjective", "finite_no_top_successor_gate", 162, "specialize finite_no_top_successor_gate b", "cba475b7f7c547eece7b87a6d7fa3a913ef563840beb2b6b8266a71ef2cd3945"),
    ("finite_bounded_injective_surjective", "finite_swap_last_surjective_back", 144, "specialize finite_swap_last_surjective_back b", "671713d9066c2d58332528f5258053da99fb1b0b70a87c51846d339d964d46c5"),
    ("finite_bounded_injective_surjective", "finite_surjective_succ_from_prefix", 135, "specialize finite_surjective_succ_from_prefix x2", "4f03d5a397a2f2a06eb3bebd32fd7d19a1e3ddb4178e9efbf6c4538e5c802310"),
    ("finite_bounded_injective_surjective", "finite_injective_prefix_succ", 121, "specialize finite_injective_prefix_succ x2", "f4d16a220238f8b7671b92e1c7dbddd0bc62ba3759346bcdc5041cd64b068bdc"),
    ("finite_bounded_injective_surjective", "finite_bounded_prefix_without_top", 112, "specialize finite_bounded_prefix_without_top x2", "ba9e3f137991ca533b9ef36ceb658e7b4b0358d465a64dc1c0a95ed5d5018648"),
    ("finite_bounded_injective_surjective", "finite_swap_last_injective", 68, "specialize finite_swap_last_injective b", "99b7b179764aa4162ec9d49c6dd1b5b6c5788592cd49d59e26735628f383e711"),
    ("finite_bounded_injective_surjective", "finite_swap_last_bounded", 49, "specialize finite_swap_last_bounded b", "43d7b3659c8518553497fe9891c25f53bf853edb831bd31e0c5268c88bba0a12"),
    ("finite_bounded_injective_surjective", "beta_prefix_swap_last_from_entries", 34, "specialize beta_prefix_swap_last_from_entries b", "f53e5c40335ffd050bd76f6cec700b019d6b791d971b83bf597f83380a67e81e"),
    ("finite_bounded_injective_surjective", "finite_bounded_last_succ", 24, "specialize finite_bounded_last_succ b", "26e49f464f0ba015e8ea7cb300bdbe5a9481fde9aaf2203336c3ae5a334324ac"),
    ("finite_bounded_injective_surjective", "finite_contains_decidable", 15, "specialize finite_contains_decidable b", "8cb4d5a12e24f756d582db5375239175ad31c9a0e1add9a5c8a2c91d12efee6c"),
    ("finite_bounded_injective_surjective", "finite_surjective_zero", 5, "specialize finite_surjective_zero b", "5fbb99570003a27ba760e62271f2fb32b68f2a72dab0ea9538ea016a33d8880b"),
    ("beta_product_swap_last_invariant", "lt_irrefl_expanded", 73, "specialize lt_irrefl_expanded n", "2e10655b56d75305ca08e9c009dcb75a1315ca1e2527714e0bf15702c395f1f0"),
    ("beta_product_swap_last_invariant", "le_succ", 67, "specialize le_succ (S j)", "f0919bdbac8e8209d9b203a67ffb19d9bfefe2e1cb0285716d18e2a6caaafb3c"),
    ("beta_product_swap_last_invariant", "beta_at_unique", 41, "specialize beta_at_unique b", "da25406be7b37e47ecd835454f34c039398a8ba2b9a8f61e9ec7c675fc7c2dd5"),
    ("beta_product_swap_last_invariant", "beta_product_succ_decompose", 19, "specialize beta_product_succ_decompose b", "97c5d9d7cd601553ad6c7224382318521592dbec3235826e7dec9723fa0ba4b1"),
    ("beta_product_swap_last_invariant", "beta_product_replace_balance", 79, "specialize beta_product_replace_balance n", "4a594b81b0ad10f29fcb5b8e22a4ed3623d2bd7906576abd554e207a3bbae0c9"),
)

EXPECTED_BASELINES = {
    "odd_add_odd": {
        "command_count": 10,
        "dependency_count": 3,
        "formula_sha256": "5f37f6bfbf8708439fe378bb2fd0581ec05c710a2b76d4eeab6e7b5153e13ba8",
        "proof_sha256": "420d70e0b87b981d44fba7da4fd11a514a3f164d441a0705c4dfa93a0161b29a",
        "proof_structure": {"depth": 31, "edges": 90, "nodes": 91, "objects": 81, "reused_objects": 10},
    },
    "finite_bounded_injective_surjective": {
        "command_count": 178,
        "dependency_count": 14,
        "formula_sha256": "c0fd73f8062ccfc63e55b64540cd8fb22d9817631b394ad9988a7fd010a319c8",
        "proof_sha256": "366ac9b8df3a524fa55bdafd95c8298783d93d6b981b39b02bb204f76de2dccf",
        "proof_structure": {"depth": 61, "edges": 351, "nodes": 352, "objects": 352, "reused_objects": 0},
    },
    "beta_product_swap_last_invariant": {
        "command_count": 102,
        "dependency_count": 5,
        "formula_sha256": "be5333944055091b534c7e7222dd45f97b40dba0e675c71f82cf6a6553b11c98",
        "proof_sha256": "a4c621ae3e27c54f60b48167d1d08200cc937937e0ba97461abe534f500c0f1d",
        "proof_structure": {"depth": 49, "edges": 131, "nodes": 132, "objects": 132, "reused_objects": 0},
    },
}

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class LibraryPilotDependencyVectorNegativeReplayVerificationError(ValueError):
    """The candidate, retained evidence, or structural receipt is invalid."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value: str) -> object:
    raise ValueError(f"unsupported JSON number {value!r}")


def _validate_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> int:
    if depth > MAX_JSON_DEPTH:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "JSON exceeds its depth limit"
        )
    if value is None or type(value) in (str, bool):
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"{path} integer exceeds the safe JSON domain"
            )
        return 1
    if type(value) not in (list, dict):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{path} contains an unsupported JSON value"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{path} contains a JSON cycle"
        )
    branch = ancestors | {marker}
    count = 1
    if type(value) is list:
        iterator = ((f"{path}[{index}]", item) for index, item in enumerate(value))
    else:
        iterator = []
        for key, item in value.items():
            if type(key) is not str:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    f"{path} has a non-string object key"
                )
            iterator.append((f"{path}.{key}", item))
    for child_path, item in iterator:
        count += _validate_json(
            item, path=child_path, depth=depth + 1, ancestors=branch
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "JSON exceeds its item limit"
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
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "cannot encode compact canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "compact canonical JSON exceeds its byte limit"
        )
    return raw


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256(_compact_json(value, limit=limit))


def canonical_negative_replay_verification_receipt_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return strict pretty canonical JSON with exactly one terminal LF."""

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
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "cannot encode canonical structural-verification JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "canonical structural-verification JSON exceeds its byte limit"
        )
    return raw


def _decode_document(raw: bytes, *, label: str, limit: int) -> dict[str, object]:
    if type(raw) is not bytes or len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} exceeds its byte limit"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} must be one object"
        )
    _validate_json(value)
    return value


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository_root must be pathlib.Path or None")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "cannot resolve repository root"
        ) from exc
    if not resolved.is_dir():
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "repository root is not a directory"
        )
    return resolved


def _safe_file(path: Path, *, label: str, limit: int) -> bytes:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    f"{label} ancestor is a link or non-directory"
                )
        metadata = absolute.lstat()
    except LibraryPilotDependencyVectorNegativeReplayVerificationError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
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
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
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
        or not stat.S_ISREG(before.st_mode)
        or identity(before) != identity(after)
        or identity(after) != identity(path_after)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} changed or exceeded its bound while read"
        )
    return raw


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _require_fields(label: str, value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} has unregistered fields"
        )
    return value


def _require_false_fields(label: str, value: Mapping[str, object], fields: Sequence[str]) -> None:
    if any(value.get(field) is not False for field in fields):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} asserted a forbidden claim"
        )


def _rooted_document(label: str, value: Mapping[str, object], root_format: str) -> None:
    preimage = {
        "format": root_format,
        "payload": {
            key: item
            for key, item in value.items()
            if key not in {"root_preimage", "root_sha256"}
        },
        "v": 1,
    }
    if value.get("root_preimage") != preimage or value.get("root_sha256") != _sha256_json(preimage):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} document root drifted"
        )


def _records_bundle(records: Sequence[Mapping[str, object]], *, kind: str) -> dict[str, object]:
    identities = []
    for index, record in enumerate(records):
        digest = record.get("record_sha256") if type(record) is dict else None
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"{kind} record identity is malformed"
            )
        identities.append({"index": index, "record_sha256": digest})
    preimage = {
        "format": CANDIDATE_RECORDS_PREIMAGE_FORMAT,
        "kind": kind,
        "records": identities,
        "v": 1,
    }
    return {"count": len(records), "preimage": preimage, "root_sha256": _sha256_json(preimage)}


def _lf_sha256(values: Sequence[str]) -> str:
    return _sha256(("\n".join(values) + "\n").encode("utf-8"))


def _authenticate_protocol_sources(
    root: Path,
) -> tuple[dict[str, object], dict[str, object], bytes]:
    rows: list[dict[str, object]] = []
    decoded: dict[str, dict[str, object]] = {}
    replayer_raw = b""
    for relative, expected_bytes, expected_sha256 in PROTOCOL_SOURCE_FILES:
        raw = _safe_file(
            root / relative,
            label=f"frozen A2.3c protocol source {relative!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha256:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"frozen A2.3c protocol source {relative!r} drifted"
            )
        rows.append(
            {"bytes": expected_bytes, "path": relative, "sha256": expected_sha256}
        )
        if relative.endswith("schema-v1.json"):
            schema = _decode_document(raw, label="frozen A2.3c schema", limit=MAX_SCHEMA_BYTES)
            if (
                canonical_negative_replay_verification_receipt_bytes(
                    schema, limit=MAX_SCHEMA_BYTES
                )
                != raw
                or schema.get("format") != SCHEMA_FORMAT
                or schema.get("id") != SCHEMA_ID
                or schema.get("v") != 1
                or _sha256_json(schema, limit=MAX_SCHEMA_BYTES)
                != SCHEMA_SEMANTIC_SHA256
            ):
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "frozen A2.3c schema semantics drifted"
                )
            decoded["schema"] = schema
        elif relative == PROTOCOL_SOURCE_FILES[1][0]:
            replayer_raw = raw
    if set(decoded) != {"schema"} or not replayer_raw:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "frozen A2.3c protocol source vector is incomplete"
        )
    tree = ast.parse(replayer_raw.decode("utf-8"), filename=PROTOCOL_SOURCE_FILES[1][0])
    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    forbidden_imports = (
        "training.peano_hydra.library_pilot_dependency_vector_audit",
        "training.peano_hydra.library_pilot_dependency_vector_audit_verifier",
        "peano_lab.library.candidate_validation",
    )
    if (
        any(
            name == prefix or name.startswith(prefix + ".")
            for name in imports
            for prefix in forbidden_imports
        )
        or "compile_candidate_body" in calls
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "frozen A2.3c producer source crosses its independence boundary"
        )
    preimage = {
        "format": PROTOCOL_SOURCES_PREIMAGE_FORMAT,
        "sources": rows,
        "v": 1,
    }
    receipt = {
        "count": len(rows),
        "independence_source_scan": (
            "no-a2.3b-wrapper-import-or-compile-candidate-body-call"
        ),
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage, limit=MAX_SCHEMA_BYTES),
    }
    return receipt, decoded["schema"], replayer_raw


def _safe_relative(value: object, *, label: str) -> Path:
    if type(value) is not str:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} path is malformed"
        )
    path = Path(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} path is unsafe"
        )
    return path


def _load_exact_json(
    root: Path,
    *,
    label: str,
    identity: Mapping[str, object],
) -> tuple[dict[str, object], bytes]:
    relative = _safe_relative(identity.get("path"), label=label)
    expected_bytes = identity.get("bytes")
    expected_sha = identity.get("artifact_sha256")
    if (
        type(expected_bytes) is not int
        or not 0 <= expected_bytes <= MAX_DOCUMENT_BYTES
        or type(expected_sha) is not str
        or _SHA256_RE.fullmatch(expected_sha) is None
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} identity is malformed"
        )
    raw = _safe_file(root / relative, label=label, limit=MAX_DOCUMENT_BYTES)
    if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} exact artifact identity drifted"
        )
    value = _decode_document(raw, label=label, limit=MAX_DOCUMENT_BYTES)
    if canonical_negative_replay_verification_receipt_bytes(value) != raw:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} is not canonical"
        )
    for field in ("root_sha256", "replay_root_sha256"):
        if field in identity and value.get(field) != identity[field]:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"{label} {field} drifted"
            )
    if "theorem_records_root_sha256" in identity and (
        type(value.get("theorem_records")) is not dict
        or value["theorem_records"].get("root_sha256")
        != identity["theorem_records_root_sha256"]
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            f"{label} theorem-record root drifted"
        )
    return value, raw


def _authenticate_retained_evidence(
    root: Path, schema: Mapping[str, object]
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    fixed = schema.get("fixed_inputs")
    expected_labels = {
        "a2.3b_candidate",
        "a2.3b_collection",
        "a2.3b_execution",
        "a2.3b_verification",
        "replay_manifest",
        "replay_report",
    }
    if type(fixed) is not dict or set(fixed) != expected_labels:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c fixed predecessor vector drifted"
        )
    values: dict[str, dict[str, object]] = {}
    evidence_rows: list[dict[str, object]] = []
    for label in sorted(expected_labels):
        identity = fixed[label]
        if type(identity) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"fixed predecessor {label!r} identity is malformed"
            )
        value, _raw = _load_exact_json(root, label=label, identity=identity)
        values[label] = value
        evidence_rows.append(
            {
                "artifact_sha256": identity["artifact_sha256"],
                "bytes": identity["bytes"],
                "label": label,
                "path": identity["path"],
            }
        )

    for label, relative, size, digest, root_digest in RETAINED_SOURCE_EVIDENCE_FILES:
        identity = {
            "artifact_sha256": digest,
            "bytes": size,
            "path": relative,
            "root_sha256": root_digest,
        }
        value, _raw = _load_exact_json(root, label=label, identity=identity)
        values[label] = value
        evidence_rows.append(
            {
                "artifact_sha256": digest,
                "bytes": size,
                "label": label,
                "path": relative,
            }
        )

    candidate = values["a2.3b_candidate"]
    verification = values["a2.3b_verification"]
    execution = values["a2.3b_execution"]
    collection = values["a2.3b_collection"]
    source_state = values["a2.3b_producer_source_state"]
    git_receipt = values["a2.3b_producer_git_verification"]
    manifest = values["replay_manifest"]
    report = values["replay_report"]
    source_semantic = _sha256_json(source_state, limit=MAX_SCHEMA_BYTES)
    source_identity = verification.get("producer_source_state")
    candidate_replay = candidate.get("inputs", {}).get("replay", {})
    if (
        candidate.get("root_sha256")
        != fixed["a2.3b_candidate"].get("root_sha256")
        or verification.get("root_sha256")
        != fixed["a2.3b_verification"].get("root_sha256")
        or verification.get("candidate", {}).get("artifact_sha256")
        != fixed["a2.3b_candidate"].get("artifact_sha256")
        or verification.get("candidate", {}).get("root_sha256")
        != candidate.get("root_sha256")
        or verification.get("status") != "passed"
        or verification.get("negative_observations_independently_verified") is not False
        or verification.get("route_rejections_independently_verified") is not False
        or execution.get("status") != "passed"
        or collection.get("status") != "passed"
        or source_state != candidate.get("producer_source_state")
        or candidate.get("producer_source_state_sha256") != source_semantic
        or type(source_identity) is not dict
        or source_identity
        != {
            "artifact_bytes": RETAINED_SOURCE_EVIDENCE_FILES[0][2],
            "artifact_sha256": RETAINED_SOURCE_EVIDENCE_FILES[0][3],
            "root_sha256": RETAINED_SOURCE_EVIDENCE_FILES[0][4],
            "semantic_sha256": source_semantic,
        }
        or git_receipt.get("status") != "passed"
        or git_receipt.get("source_state_artifact_sha256")
        != RETAINED_SOURCE_EVIDENCE_FILES[0][3]
        or git_receipt.get("source_state_root_sha256")
        != RETAINED_SOURCE_EVIDENCE_FILES[0][4]
        or git_receipt.get("source_state_sha256") != source_semantic
        or git_receipt.get("commit_sha1") != source_state.get("commit_sha1")
        or git_receipt.get("tree_sha1") != source_state.get("tree_sha1")
        or manifest.get("theorem_count") != 384
        or report.get("theorem_count") != 384
        or report.get("status") != "passed"
        or candidate_replay.get("manifest_artifact_sha256")
        != fixed["replay_manifest"].get("artifact_sha256")
        or candidate_replay.get("manifest_root_sha256")
        != fixed["replay_manifest"].get("root_sha256")
        or candidate_replay.get("replay_report_artifact_sha256")
        != fixed["replay_report"].get("artifact_sha256")
        or candidate_replay.get("replay_root_sha256")
        != fixed["replay_manifest"].get("replay_root_sha256")
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "retained predecessor evidence cross-binding drifted"
        )
    preimage = {
        "evidence": evidence_rows,
        "format": RETAINED_EVIDENCE_PREIMAGE_FORMAT,
        "v": 1,
    }
    receipt = {
        "count": len(evidence_rows),
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "status": "exact-retained-predecessors-and-source-evidence-authenticated",
    }
    return values, receipt


def _registered_tasks(
    schema: Mapping[str, object], manifest: Mapping[str, object]
) -> tuple[dict[str, object], ...]:
    schema_rows = schema.get("required_theorems")
    manifest_rows = manifest.get("theorems")
    if (
        type(schema_rows) is not list
        or len(schema_rows) != EXPECTED_BASELINE_COUNT
        or type(manifest_rows) is not list
        or len(manifest_rows) != 384
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "registered theorem inputs drifted"
        )
    manifest_by_name: dict[str, dict[str, object]] = {}
    for row in manifest_rows:
        if type(row) is not dict or type(row.get("name")) is not str:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "replay manifest theorem row is malformed"
            )
        if row["name"] in manifest_by_name:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "replay manifest theorem name is duplicated"
            )
        manifest_by_name[row["name"]] = row
    constants_by_key = {
        (name, omitted): (command_index, command, target_sha)
        for name, omitted, command_index, command, target_sha in EXPECTED_TASKS
    }
    tasks: list[dict[str, object]] = []
    for expected, schema_row in zip(EXPECTED_THEOREMS, schema_rows, strict=True):
        if type(schema_row) is not dict or set(schema_row) != {
            "dependencies",
            "index",
            "name",
            "script_command_count",
            "script_sha256",
            "statement_sha256",
            "tasks",
        }:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "registered theorem schema row is malformed"
            )
        expected_schema = {
            **expected,
            "dependencies": list(expected["dependencies"]),
        }
        for field in (
            "dependencies",
            "index",
            "name",
            "script_command_count",
            "script_sha256",
            "statement_sha256",
        ):
            if schema_row.get(field) != expected_schema[field]:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    f"registered theorem {expected['name']!r} drifted"
                )
        manifest_row = manifest_by_name.get(expected["name"])
        script = manifest_row.get("script") if type(manifest_row) is dict else None
        if (
            type(script) is not list
            or not all(type(command) is str and command for command in script)
            or manifest_row.get("index") != expected["index"]
            or len(script) != expected["script_command_count"]
            or _lf_sha256(script) != expected["script_sha256"]
            or manifest_row.get("statement_source_sha256")
            != expected["statement_sha256"]
        ):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"exact replay script {expected['name']!r} drifted"
            )
        registrations = schema_row.get("tasks")
        dependencies = expected["dependencies"]
        if type(registrations) is not list or len(registrations) != len(dependencies):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "registered negative task vector is malformed"
            )
        for attempt_index, (omitted, registration) in enumerate(
            zip(reversed(dependencies), registrations, strict=True)
        ):
            constant = constants_by_key.get((expected["name"], omitted))
            if constant is None or type(registration) is not dict:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "registered negative task constant is absent"
                )
            command_index, command, target_sha = constant
            message = f"unknown hypothesis {omitted!r}."
            if registration != {
                "attempt_index": attempt_index,
                "expected_command": command,
                "expected_command_index": command_index,
                "expected_message": message,
                "omitted_dependency": omitted,
            } or script[command_index] != command:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    f"registered negative task {(expected['name'], omitted)!r} drifted"
                )
            trial = tuple(item for item in dependencies if item != omitted)
            tasks.append(
                {
                    "attempt_index": attempt_index,
                    "command": command,
                    "command_index": command_index,
                    "full_dependencies": list(dependencies),
                    "message": message,
                    "name": expected["name"],
                    "omitted_dependency": omitted,
                    "script_sha256": expected["script_sha256"],
                    "target_formula_sha256": target_sha,
                    "theorem_index": expected["index"],
                    "trial_dependencies": list(trial),
                }
            )
    if (
        len(tasks) != EXPECTED_OBSERVATION_COUNT
        or len({(row["name"], row["omitted_dependency"]) for row in tasks})
        != EXPECTED_OBSERVATION_COUNT
        or tuple((row["name"], row["omitted_dependency"]) for row in tasks)
        != tuple((row[0], row[1]) for row in EXPECTED_TASKS)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "registered 22-task order or uniqueness drifted"
        )
    return tuple(tasks)


def _validate_retained_a23b_candidate(
    candidate: Mapping[str, object], tasks: Sequence[Mapping[str, object]]
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str], dict[str, object]]]:
    if (
        candidate.get("format") != A23B_CANDIDATE_FORMAT
        or candidate.get("id") != A23B_CANDIDATE_ID
        or candidate.get("v") != 1
        or candidate.get("status") != "candidate"
        or candidate.get("logic_mode") != LOGIC_MODE
        or candidate.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or candidate.get("single_omission_terminal_count")
        != EXPECTED_RETAINED_ROUTE_ROW_COUNT
        or candidate.get("terminal_route_observations_complete") is not True
        or candidate.get("bounded_three_root_vector_audit_complete") is not False
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "retained A2.3b candidate identity or claim boundary drifted"
        )
    for field in GLOBAL_FALSE_FIELDS:
        if field in candidate and candidate[field] is not False:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained A2.3b candidate asserted a forbidden claim"
            )
    a23b_preimage = {
        "format": A23B_CANDIDATE_ROOT_PREIMAGE_FORMAT,
        "payload": {
            key: item
            for key, item in candidate.items()
            if key not in {"root_preimage", "root_sha256", "theorems"}
        },
        "v": 1,
    }
    if (
        candidate.get("root_preimage") != a23b_preimage
        or candidate.get("root_sha256") != _sha256_json(a23b_preimage)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "retained A2.3b candidate document root drifted"
        )
    theorem_rows = candidate.get("theorems")
    if type(theorem_rows) is not list or len(theorem_rows) != EXPECTED_BASELINE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "retained A2.3b theorem vector drifted"
        )
    task_by_key = {
        (task["name"], task["omitted_dependency"]): task for task in tasks
    }
    baseline_expectations: dict[str, dict[str, object]] = {}
    retained: dict[tuple[str, str], dict[str, object]] = {}
    theorem_identities: list[dict[str, object]] = []
    total_rows = 0
    for theorem, expected in zip(theorem_rows, EXPECTED_THEOREMS, strict=True):
        if (
            type(theorem) is not dict
            or theorem.get("index") != expected["index"]
            or theorem.get("name") != expected["name"]
            or theorem.get("single_omission_attempt_count")
            != 2 * len(expected["dependencies"])
            or theorem.get("single_omission_rejected_count")
            != 2 * len(expected["dependencies"])
            or theorem.get("single_omission_kernel_accepted_count") != 0
            or theorem.get("single_omission_terminal_count")
            != 2 * len(expected["dependencies"])
            or theorem.get("terminal_route_observations_complete") is not True
            or theorem.get("bounded_three_root_vector_audit_complete") is not False
        ):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"retained A2.3b theorem {expected['name']!r} drifted"
            )
        for field in GLOBAL_FALSE_FIELDS:
            if field in theorem and theorem[field] is not False:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b theorem asserted a forbidden claim"
                )
        routes = theorem.get("routes")
        if type(routes) is not list or len(routes) != 2:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained A2.3b route vector drifted"
            )
        route_attempts: list[list[dict[str, object]]] = []
        baseline_receipts: list[dict[str, object]] = []
        for route_name, route in zip(ROUTES, routes, strict=True):
            if (
                type(route) is not dict
                or route.get("route") != route_name
                or route.get("status") != "bounded-route-audit-complete"
                or route.get("single_omission_kernel_accepted_count") != 0
                or route.get("single_omission_rejected_count")
                != len(expected["dependencies"])
            ):
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b route receipt drifted"
                )
            attempts = route.get("attempts")
            if type(attempts) is not list or len(attempts) != len(expected["dependencies"]):
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b attempt vector drifted"
                )
            identities = [
                {
                    "attempt_index": index,
                    "omitted_dependency": row.get("omitted_dependency"),
                    "record_sha256": row.get("record_sha256"),
                }
                for index, row in enumerate(attempts)
                if type(row) is dict
            ]
            attempts_preimage = {
                "format": A23B_ATTEMPTS_PREIMAGE_FORMAT,
                "name": expected["name"],
                "records": identities,
                "route": route_name,
                "v": 1,
            }
            if route.get("attempt_records") != {
                "count": len(attempts),
                "preimage": attempts_preimage,
                "root_sha256": _sha256_json(attempts_preimage),
            }:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b attempt-record root drifted"
                )
            route_preimage = route.get("route_receipt_preimage")
            if (
                type(route_preimage) is not dict
                or route_preimage.get("attempts_root_sha256")
                != route["attempt_records"]["root_sha256"]
                or route_preimage.get("index") != expected["index"]
                or route_preimage.get("name") != expected["name"]
                or route_preimage.get("route") != route_name
                or route_preimage.get("dependencies")
                != list(expected["dependencies"])
                or route.get("route_receipt_sha256") != _sha256_json(route_preimage)
            ):
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b route root drifted"
                )
            baseline = route.get("baseline")
            receipt = (
                baseline.get("diagnostics", {}).get("root_body_receipt")
                if type(baseline) is dict
                else None
            )
            if type(receipt) is not dict:
                raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                    "retained A2.3b baseline receipt is malformed"
                )
            baseline_receipts.append(receipt)
            route_attempts.append(attempts)
        if baseline_receipts[0] != baseline_receipts[1]:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained A2.3b routes disagree on their shared baseline"
            )
        receipt = baseline_receipts[0]
        expected_baseline = EXPECTED_BASELINES[expected["name"]]
        if set(receipt) != {
            "certificate_sha256",
            "command_count",
            "dependency_count",
            "proof_depth",
            "proof_edges",
            "proof_nodes",
            "proof_objects",
            "reused_objects",
            "target_formula_sha256",
        } or {
            "command_count": receipt.get("command_count"),
            "dependency_count": receipt.get("dependency_count"),
            "formula_sha256": receipt.get("target_formula_sha256"),
            "proof_sha256": receipt.get("certificate_sha256"),
            "proof_structure": {
                "depth": receipt.get("proof_depth"),
                "edges": receipt.get("proof_edges"),
                "nodes": receipt.get("proof_nodes"),
                "objects": receipt.get("proof_objects"),
                "reused_objects": receipt.get("reused_objects"),
            },
        } != expected_baseline:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained A2.3b full-vector baseline identity drifted"
            )
        baseline_expectations[expected["name"]] = deepcopy(expected_baseline)
        for attempt_index, pair in enumerate(
            zip(route_attempts[0], route_attempts[1], strict=True)
        ):
            omitted = tuple(reversed(expected["dependencies"]))[attempt_index]
            task = task_by_key[(expected["name"], omitted)]
            expected_failure = {
                "cause_type": "TacticError",
                "command": task["command"],
                "command_index": task["command_index"],
                "kind": "exact-recipe-rejection",
                "phase": "command",
            }
            pair_rows: list[dict[str, object]] = []
            shared_digest: str | None = None
            for route_name, row in zip(ROUTES, pair, strict=True):
                if type(row) is not dict:
                    raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                        "retained A2.3b attempt is malformed"
                    )
                shared = row.get("shared_root_body_observation_preimage")
                digest = row.get("shared_root_body_observation_sha256")
                if (
                    row.get("attempt_index") != attempt_index
                    or row.get("route") != route_name
                    or row.get("index") != expected["index"]
                    or row.get("name") != expected["name"]
                    or row.get("omitted_dependency") != omitted
                    or row.get("before_dependencies")
                    != list(expected["dependencies"])
                    or row.get("after_dependencies")
                    != list(expected["dependencies"])
                    or row.get("attempted_dependencies")
                    != task["trial_dependencies"]
                    or row.get("failure") != expected_failure
                    or row.get("outcome") != "exact-route-rejected"
                    or row.get("terminal_stage") != "root-body-regeneration"
                    or row.get("route_specific_assembly_reached") is not False
                    or row.get("layered_compiler_invoked") is not False
                    or row.get("script_sha256") != task["script_sha256"]
                    or type(shared) is not dict
                    or shared
                    != {
                        "candidate_body_compiler_source_sha256": (
                            "b41e6587d32e27152e1358b3067c72b869357674548f05aa4ef5e86cf9bdc30a"
                        ),
                        "dependencies": task["trial_dependencies"],
                        "failure": expected_failure,
                        "format": "peano-hydra-shared-root-body-observation-preimage",
                        "index": expected["index"],
                        "name": expected["name"],
                        "v": 1,
                    }
                    or digest != _sha256_json(shared, limit=MAX_SCHEMA_BYTES)
                    or row.get("record_sha256") != _record_hash(row)
                ):
                    raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                        "retained A2.3b route observation semantics drifted"
                    )
                if shared_digest is None:
                    shared_digest = digest
                elif shared_digest != digest:
                    raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                        "retained A2.3b route pair does not share one observation"
                    )
                pair_rows.append(
                    {"record_sha256": row["record_sha256"], "route": route_name}
                )
                total_rows += 1
            retained[(expected["name"], omitted)] = {
                "records": pair_rows,
                "shared_sha256": shared_digest,
            }
        if theorem.get("record_sha256") != _record_hash(theorem):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained A2.3b theorem record hash drifted"
            )
        theorem_identities.append(
            {
                "index": expected["index"],
                "name": expected["name"],
                "record_sha256": theorem["record_sha256"],
            }
        )
    theorem_preimage = {
        "format": A23B_RECORDS_PREIMAGE_FORMAT,
        "records": theorem_identities,
        "v": 1,
    }
    if candidate.get("theorem_records") != {
        "count": EXPECTED_BASELINE_COUNT,
        "preimage": theorem_preimage,
        "root_sha256": _sha256_json(theorem_preimage),
    } or total_rows != EXPECTED_RETAINED_ROUTE_ROW_COUNT or len(retained) != EXPECTED_OBSERVATION_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "retained A2.3b 44-to-22 evidence is incomplete"
        )
    return baseline_expectations, retained


def _expected_callable_receipt(schema: Mapping[str, object]) -> dict[str, object]:
    qualified = schema.get("qualified_callables")
    expected_qualified = {
        "apply_tactic": "peano_lab.engine.tactics.apply_tactic",
        "checked_final": "peano_lab.engine.tactics.checked_final",
        "formula_encode": "peano_lab.kernel.artifact_codec.encode_formula",
        "proof_encode": "peano_lab.kernel.artifact_codec.encode_proof",
        "proof_metrics": "peano_lab.engine.state.proof_resource_metrics",
        "proof_state_invariants": "peano_lab.engine.state.invariants_ok",
        "proof_state_type": "peano_lab.engine.state.ProofState",
        "replay_target": "peano_lab.library.theorems.replay_target",
        "start": "peano_lab.engine.state.start",
    }
    if qualified != expected_qualified:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "registered callable identity vector drifted"
        )
    sources = {
        "apply_tactic": "peano-lab/py/peano_lab/engine/tactics.py",
        "checked_final": "peano-lab/py/peano_lab/engine/tactics.py",
        "formula_encode": "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "proof_encode": "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "proof_metrics": "peano-lab/py/peano_lab/engine/state.py",
        "proof_state_invariants": "peano-lab/py/peano_lab/engine/state.py",
        "proof_state_type": "peano-lab/py/peano_lab/engine/state.py",
        "replay_target": "peano-lab/py/peano_lab/library/theorems.py",
        "start": "peano-lab/py/peano_lab/engine/state.py",
    }
    return {
        "callables": [
            {"qualified_name": name, "source_path": sources[label]}
            for label, name in expected_qualified.items()
        ],
        "qualified_callables": deepcopy(expected_qualified),
        "status": "exact-callable-identities-authenticated",
    }


def _validate_producer_environment(
    environment: object,
    *,
    root: Path,
    schema: Mapping[str, object],
) -> None:
    fields = {
        "callables",
        "fixed_input_count",
        "implementation_source_count",
        "implementation_source_root_sha256",
        "preimage",
        "replayer",
        "root_sha256",
        "runtime",
        "status",
    }
    value = _require_fields("A2.3c producer environment", environment, fields)
    callables = _expected_callable_receipt(schema)
    replayer_relative = PROTOCOL_SOURCE_FILES[1][0]
    replayer = {
        "bytes": PROTOCOL_SOURCE_FILES[1][1],
        "load_mode": "authenticated-source-bytes-source_to_code-exec",
        "module_name": "_peano_hydra_a23c_independent_negative_replayer",
        "path": replayer_relative,
        "pycache_prefix": "/proc/peano-hydra-a23c-disabled-pycache",
        "sha256": PROTOCOL_SOURCE_FILES[1][2],
        "source_loader": "importlib.machinery.SourceFileLoader",
    }
    schema_identity = {
        "artifact_sha256": PROTOCOL_SOURCE_FILES[0][2],
        "bytes": PROTOCOL_SOURCE_FILES[0][1],
        "id": SCHEMA_ID,
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    preimage = {
        "callables": callables,
        "fixed_inputs": deepcopy(schema["fixed_inputs"]),
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "environment-preimage"
        ),
        "implementation_source_root_sha256": (
            "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
        ),
        "runtime": deepcopy(schema["runtime_binding"]),
        "replayer": replayer,
        "schema": schema_identity,
        "v": 1,
    }
    if value != {
        "callables": callables,
        "fixed_input_count": 6,
        "implementation_source_count": 39,
        "implementation_source_root_sha256": (
            "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
        ),
        "preimage": preimage,
        "replayer": replayer,
        "root_sha256": _sha256_json(preimage),
        "runtime": deepcopy(schema["runtime_binding"]),
        "status": "all-execution-bindings-authenticated",
    }:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c producer environment receipt drifted"
        )


def _expected_observation(task: Mapping[str, object]) -> dict[str, object]:
    failure = {
        "cause_type": "TacticError",
        "command": task["command"],
        "command_index": task["command_index"],
        "diagnostic": (
            f"candidate {task['name']!r} failed at command "
            f"{task['command_index']}: {task['command']!r}: {task['message']}"
        ),
        "kind": "exact-recipe-rejection",
        "message": task["message"],
        "message_source": "fresh-a2.3c-lower-level-replay",
        "omitted_dependency": task["omitted_dependency"],
        "phase": "command",
        "retained_message_available": False,
    }
    body: dict[str, object] = {
        "attempt_index": task["attempt_index"],
        "failure": failure,
        "full_dependencies": task["full_dependencies"],
        "name": task["name"],
        "omitted_dependency": task["omitted_dependency"],
        "outcome": "exact-shared-root-body-rejected",
        "prefix_command_count": task["command_index"],
        "target_formula_sha256": task["target_formula_sha256"],
        "theorem_index": task["theorem_index"],
        "trial_dependencies": task["trial_dependencies"],
    }
    body["record_sha256"] = _record_hash(body)
    return body


def _expected_retained_join(
    observations: Sequence[Mapping[str, object]],
    retained: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    joins: list[dict[str, object]] = []
    for observation in observations:
        key = (observation["name"], observation["omitted_dependency"])
        pair = retained.get(key)
        if type(pair) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "retained route pair is absent"
            )
        joins.append(
            {
                "attempt_index": observation["attempt_index"],
                "fresh_observation_record_sha256": observation["record_sha256"],
                "name": observation["name"],
                "omitted_dependency": observation["omitted_dependency"],
                "retained_message_available": False,
                "retained_route_records": deepcopy(pair["records"]),
                "retained_shared_observation_sha256": pair["shared_sha256"],
                "route_row_count": 2,
                "theorem_index": observation["theorem_index"],
            }
        )
    preimage = {
        "format": RETAINED_JOIN_PREIMAGE_FORMAT,
        "joins": joins,
        "v": 1,
    }
    return {
        "fresh_observation_count": len(joins),
        "joins": joins,
        "preimage": preimage,
        "retained_route_row_count": 2 * len(joins),
        "root_sha256": _sha256_json(preimage),
        "route_rows_per_observation": 2,
        "status": "exact-44-route-rows-joined-two-to-one",
    }


def _validate_candidate_structure(
    candidate: object,
    *,
    candidate_raw: bytes | None,
    root: Path,
    schema: Mapping[str, object],
    fixed: Mapping[str, Mapping[str, object]],
    tasks: Sequence[Mapping[str, object]],
    baselines_expected: Mapping[str, Mapping[str, object]],
    retained: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    fields = {
        *GLOBAL_FALSE_FIELDS,
        "aggregate",
        "baseline_records",
        "baselines",
        "campaign_executed",
        "environment",
        "format",
        "id",
        "independence",
        "logic_mode",
        "negative_observation_records",
        "negative_observations",
        "negative_observations_independently_verified",
        "predecessors",
        "result_exists",
        "retained_route_join",
        "root_preimage",
        "root_sha256",
        "schema",
        "status",
        "theorem_count",
        "theorem_records",
        "theorems",
        "v",
    }
    value = _require_fields("A2.3c negative-replay result", candidate, fields)
    _require_false_fields("A2.3c negative-replay result", value, GLOBAL_FALSE_FIELDS)
    canonical = canonical_negative_replay_verification_receipt_bytes(value)
    if candidate_raw is None:
        candidate_raw = canonical
    elif type(candidate_raw) is not bytes or candidate_raw != canonical:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c candidate transport is not canonical"
        )
    aggregate = {
        "full_vector_baseline_count": EXPECTED_BASELINE_COUNT,
        "independent_shared_observation_count": EXPECTED_OBSERVATION_COUNT,
        "retained_route_row_count": EXPECTED_RETAINED_ROUTE_ROW_COUNT,
        "route_rows_per_shared_observation": 2,
        "theorem_count": EXPECTED_BASELINE_COUNT,
    }
    schema_identity = {
        "artifact_sha256": PROTOCOL_SOURCE_FILES[0][2],
        "bytes": PROTOCOL_SOURCE_FILES[0][1],
        "id": SCHEMA_ID,
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    if (
        value.get("format") != CANDIDATE_FORMAT
        or value.get("id") != CANDIDATE_ID
        or value.get("v") != CANDIDATE_VERSION
        or value.get("status") != "passed"
        or value.get("logic_mode") != LOGIC_MODE
        or value.get("campaign_executed") is not True
        or value.get("result_exists") is not True
        or value.get("negative_observations_independently_verified") is not True
        or value.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or value.get("aggregate") != aggregate
        or value.get("schema") != schema_identity
        or value.get("predecessors") != schema.get("fixed_inputs")
        or value.get("independence") != schema.get("independence_contract")
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c negative-replay aggregate or immutable binding drifted"
        )
    _validate_producer_environment(value.get("environment"), root=root, schema=schema)
    baselines = value.get("baseline_records")
    observations = value.get("negative_observation_records")
    theorems = value.get("theorems")
    if (
        type(baselines) is not list
        or len(baselines) != EXPECTED_BASELINE_COUNT
        or type(observations) is not list
        or len(observations) != EXPECTED_OBSERVATION_COUNT
        or type(theorems) is not list
        or len(theorems) != EXPECTED_BASELINE_COUNT
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c negative-replay record counts drifted"
        )
    for baseline, expected in zip(baselines, EXPECTED_THEOREMS, strict=True):
        fields = {
            "command_count",
            "dependencies",
            "dependency_count",
            "formula_sha256",
            "name",
            "proof_sha256",
            "proof_structure",
            "record_sha256",
            "script_sha256",
            "status",
            "theorem_index",
        }
        row = _require_fields("A2.3c full-vector baseline", baseline, fields)
        expected_baseline = baselines_expected[expected["name"]]
        expected_body = {
            "command_count": expected_baseline["command_count"],
            "dependencies": list(expected["dependencies"]),
            "dependency_count": expected_baseline["dependency_count"],
            "formula_sha256": expected_baseline["formula_sha256"],
            "name": expected["name"],
            "proof_sha256": expected_baseline["proof_sha256"],
            "proof_structure": expected_baseline["proof_structure"],
            "script_sha256": expected["script_sha256"],
            "status": "full-vector-baseline-kernel-accepted",
            "theorem_index": expected["index"],
        }
        if (
            {key: item for key, item in row.items() if key != "record_sha256"}
            != expected_body
            or row.get("record_sha256") != _record_hash(row)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "A2.3c full-vector baseline structure drifted"
            )
    expected_observations = [_expected_observation(task) for task in tasks]
    if observations != expected_observations:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c 22-observation structure, order, or exact diagnostic drifted"
        )
    offset = 0
    for theorem, baseline, expected in zip(
        theorems, baselines, EXPECTED_THEOREMS, strict=True
    ):
        count = len(expected["dependencies"])
        selected = observations[offset : offset + count]
        offset += count
        theorem_fields = {
            *GLOBAL_FALSE_FIELDS,
            "baseline",
            "index",
            "name",
            "negative_observation_count",
            "negative_observations",
            "negative_observations_independently_verified",
            "record_sha256",
        }
        row = _require_fields("A2.3c theorem result", theorem, theorem_fields)
        _require_false_fields("A2.3c theorem result", row, GLOBAL_FALSE_FIELDS)
        expected_body = {
            **{field: False for field in GLOBAL_FALSE_FIELDS},
            "baseline": baseline,
            "index": expected["index"],
            "name": expected["name"],
            "negative_observation_count": count,
            "negative_observations": selected,
            "negative_observations_independently_verified": True,
        }
        if (
            {key: item for key, item in row.items() if key != "record_sha256"}
            != expected_body
            or row.get("record_sha256") != _record_hash(row)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "A2.3c theorem partition or claim boundary drifted"
            )
    if offset != EXPECTED_OBSERVATION_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c theorem partition is incomplete"
        )
    for bundle, records, kind in (
        (value.get("baselines"), baselines, "full-vector-baselines"),
        (
            value.get("negative_observations"),
            observations,
            "independent-shared-root-body-negative-replays",
        ),
        (value.get("theorem_records"), theorems, "theorems"),
    ):
        if bundle != _records_bundle(records, kind=kind):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                f"A2.3c {kind} record root drifted"
            )
    expected_join = _expected_retained_join(observations, retained)
    if value.get("retained_route_join") != expected_join:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c exact 44-to-22 retained-route join drifted"
        )
    _rooted_document("A2.3c negative-replay result", value, CANDIDATE_ROOT_PREIMAGE_FORMAT)
    return {
        "artifact_bytes": len(candidate_raw),
        "artifact_sha256": _sha256(candidate_raw),
        "baseline_records_root_sha256": value["baselines"]["root_sha256"],
        "negative_observation_records_root_sha256": value["negative_observations"]["root_sha256"],
        "retained_route_join_root_sha256": expected_join["root_sha256"],
        "root_sha256": value["root_sha256"],
        "theorem_records_root_sha256": value["theorem_records"]["root_sha256"],
    }


def _verification_record_bundle(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    identities = [
        {
            "index": record["index"],
            "name": record["name"],
            "record_sha256": record["record_sha256"],
        }
        for record in records
    ]
    preimage = {
        "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": 1,
    }
    return {"count": len(records), "preimage": preimage, "root_sha256": _sha256_json(preimage)}


def _theorem_verification_rows(candidate: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for theorem, expected in zip(candidate["theorems"], EXPECTED_THEOREMS, strict=True):
        observation_identities = [
            {
                "attempt_index": observation["attempt_index"],
                "omitted_dependency": observation["omitted_dependency"],
                "record_sha256": observation["record_sha256"],
            }
            for observation in theorem["negative_observations"]
        ]
        observation_preimage = {
            "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
            "kind": "theorem-negative-observations",
            "name": expected["name"],
            "records": observation_identities,
            "v": 1,
        }
        body: dict[str, object] = {
            **{field: False for field in VERIFICATION_FALSE_FIELDS},
            "baseline_record_sha256": theorem["baseline"]["record_sha256"],
            "index": expected["index"],
            "name": expected["name"],
            "negative_observation_count": len(observation_identities),
            "negative_observation_records_root_sha256": _sha256_json(observation_preimage),
            "retained_route_pair_count": len(observation_identities),
            "structural_result_verified": True,
        }
        body["record_sha256"] = _record_hash(body)
        rows.append(body)
    return rows


def _verifier_identity(root: Path) -> dict[str, object]:
    path = root / "training/peano_hydra/library_pilot_dependency_vector_negative_replay_verifier.py"
    raw = _safe_file(path, label="A2.3c structural verifier source", limit=MAX_SOURCE_BYTES)
    if Path(__file__).resolve(strict=True) != path.resolve(strict=True):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verifier source path drifted"
        )
    return {
        "bytecode_write_disabled": sys.dont_write_bytecode,
        "import_policy": "python-standard-library-only-no-peano-or-training-import",
        "load_mode": "authenticated-source-bytes-source_to_code-exec",
        "module_name": __name__,
        "path": path.relative_to(root).as_posix(),
        "pycache_prefix": PYCACHE_PREFIX,
        "sha256": _sha256(raw),
        "source_bytes": len(raw),
        "tactic_free": True,
    }


VERIFICATION_RECEIPT_BODY_FIELDS = frozenset(
    {
        *VERIFICATION_FALSE_FIELDS,
        "aggregate",
        "candidate",
        "candidate_negative_observations_structurally_verified",
        "candidate_status",
        "format",
        "id",
        "logic_mode",
        "predecessor_evidence_authenticated",
        "producer_environment_structurally_verified",
        "producer_independence_source_verified",
        "protocol_sources",
        "retained_evidence",
        "source_protocol_authenticated",
        "status",
        "structural_receipts_verified",
        "structural_result_verified",
        "theorem_count",
        "theorem_records",
        "theorems",
        "v",
        "verifier",
    }
)
VERIFICATION_RECEIPT_FIELDS = frozenset(
    {*VERIFICATION_RECEIPT_BODY_FIELDS, "root_preimage", "root_sha256"}
)


def _require_runtime_import_boundary() -> None:
    forbidden_modules = sorted(
        name
        for name in sys.modules
        if name == "training"
        or name.startswith("training.")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
    )
    forbidden_environment = (
        "PYTHONCASEOK",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONOPTIMIZE",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTHONWARNINGS",
    )
    if forbidden_modules:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verifier import boundary is contaminated"
        )
    if (
        getattr(sys.flags, "safe_path", False) is not True
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.flags.optimize != 0
        or sys.dont_write_bytecode is not True
        or sys.pycache_prefix != PYCACHE_PREFIX
        or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
        or any(name in os.environ for name in forbidden_environment)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verifier interpreter isolation policy differs"
        )
    try:
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "cannot inspect disabled verifier pycache prefix"
        ) from exc
    else:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "disabled verifier pycache prefix unexpectedly exists"
        )


def _construct_verification_receipt(
    candidate: object,
    *,
    candidate_raw: bytes | None,
    repository_root: Path | None,
    require_runtime_boundary: bool,
) -> dict[str, object]:
    if require_runtime_boundary:
        _require_runtime_import_boundary()
    root = _repository_root(repository_root)
    protocol_sources, schema, _replayer_raw = _authenticate_protocol_sources(root)
    fixed, retained_evidence = _authenticate_retained_evidence(root, schema)
    tasks = _registered_tasks(schema, fixed["replay_manifest"])
    baselines_expected, retained = _validate_retained_a23b_candidate(
        fixed["a2.3b_candidate"], tasks
    )
    candidate_identity = _validate_candidate_structure(
        candidate,
        candidate_raw=candidate_raw,
        root=root,
        schema=schema,
        fixed=fixed,
        tasks=tasks,
        baselines_expected=baselines_expected,
        retained=retained,
    )
    assert type(candidate) is dict
    theorem_rows = _theorem_verification_rows(candidate)
    theorem_records = _verification_record_bundle(theorem_rows)
    body: dict[str, object] = {
        **{field: False for field in VERIFICATION_FALSE_FIELDS},
        "aggregate": {
            "full_vector_baseline_count": EXPECTED_BASELINE_COUNT,
            "negative_observation_count": EXPECTED_OBSERVATION_COUNT,
            "retained_route_pair_count": EXPECTED_OBSERVATION_COUNT,
            "retained_route_row_count": EXPECTED_RETAINED_ROUTE_ROW_COUNT,
            "theorem_count": EXPECTED_BASELINE_COUNT,
        },
        "candidate": candidate_identity,
        "candidate_negative_observations_structurally_verified": True,
        "candidate_status": "passed",
        "format": VERIFICATION_FORMAT,
        "id": VERIFICATION_ID,
        "logic_mode": LOGIC_MODE,
        "predecessor_evidence_authenticated": True,
        "producer_environment_structurally_verified": True,
        "producer_independence_source_verified": True,
        "protocol_sources": protocol_sources,
        "retained_evidence": retained_evidence,
        "source_protocol_authenticated": True,
        "status": "passed",
        "structural_receipts_verified": True,
        "structural_result_verified": True,
        "theorem_count": EXPECTED_BASELINE_COUNT,
        "theorem_records": theorem_records,
        "theorems": theorem_rows,
        "v": VERIFICATION_VERSION,
        "verifier": _verifier_identity(root),
    }
    if set(body) != VERIFICATION_RECEIPT_BODY_FIELDS:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "internal structural verification body field vector drifted"
        )
    preimage = {
        "format": VERIFICATION_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": VERIFICATION_VERSION,
    }
    receipt = {**body, "root_preimage": preimage, "root_sha256": _sha256_json(preimage)}
    canonical_negative_replay_verification_receipt_bytes(receipt)
    return receipt


def verify_pilot_dependency_vector_negative_replay_result(
    candidate: object,
    *,
    candidate_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Return a tactic-free structural receipt for one completed result."""

    return _construct_verification_receipt(
        candidate,
        candidate_raw=candidate_raw,
        repository_root=repository_root,
        require_runtime_boundary=True,
    )


def validate_pilot_dependency_vector_negative_replay_verification_receipt(
    value: object,
    *,
    candidate: object,
    candidate_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Deep-validate and exactly reconstruct one structural receipt.

    Reconstruction remains tactic-free: neither this function nor the receipt
    builder executes a baseline or negative replay.
    """

    receipt = _require_fields(
        "A2.3c structural verification receipt",
        value,
        set(VERIFICATION_RECEIPT_FIELDS),
    )
    _validate_json(receipt)
    _require_false_fields(
        "A2.3c structural verification receipt", receipt, VERIFICATION_FALSE_FIELDS
    )
    if (
        receipt.get("format") != VERIFICATION_FORMAT
        or receipt.get("id") != VERIFICATION_ID
        or receipt.get("v") != VERIFICATION_VERSION
        or receipt.get("status") != "passed"
        or receipt.get("candidate_status") != "passed"
        or receipt.get("logic_mode") != LOGIC_MODE
        or receipt.get("structural_result_verified") is not True
        or receipt.get("structural_receipts_verified") is not True
        or receipt.get("candidate_negative_observations_structurally_verified")
        is not True
        or receipt.get("source_protocol_authenticated") is not True
        or receipt.get("predecessor_evidence_authenticated") is not True
        or receipt.get("producer_environment_structurally_verified") is not True
        or receipt.get("producer_independence_source_verified") is not True
        or receipt.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or receipt.get("aggregate")
        != {
            "full_vector_baseline_count": EXPECTED_BASELINE_COUNT,
            "negative_observation_count": EXPECTED_OBSERVATION_COUNT,
            "retained_route_pair_count": EXPECTED_OBSERVATION_COUNT,
            "retained_route_row_count": EXPECTED_RETAINED_ROUTE_ROW_COUNT,
            "theorem_count": EXPECTED_BASELINE_COUNT,
        }
    ):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verification receipt identity drifted"
        )
    theorem_rows = receipt.get("theorems")
    if type(theorem_rows) is not list or len(theorem_rows) != EXPECTED_BASELINE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verification theorem vector drifted"
        )
    theorem_fields = {
        *VERIFICATION_FALSE_FIELDS,
        "baseline_record_sha256",
        "index",
        "name",
        "negative_observation_count",
        "negative_observation_records_root_sha256",
        "record_sha256",
        "retained_route_pair_count",
        "structural_result_verified",
    }
    for row, expected in zip(theorem_rows, EXPECTED_THEOREMS, strict=True):
        theorem = _require_fields(
            "A2.3c structural verification theorem", row, theorem_fields
        )
        _require_false_fields(
            "A2.3c structural verification theorem",
            theorem,
            VERIFICATION_FALSE_FIELDS,
        )
        if (
            theorem.get("index") != expected["index"]
            or theorem.get("name") != expected["name"]
            or theorem.get("negative_observation_count")
            != len(expected["dependencies"])
            or theorem.get("retained_route_pair_count")
            != len(expected["dependencies"])
            or theorem.get("structural_result_verified") is not True
            or theorem.get("record_sha256") != _record_hash(theorem)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
                "A2.3c structural verification theorem receipt drifted"
            )
    if receipt.get("theorem_records") != _verification_record_bundle(theorem_rows):
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verification theorem root drifted"
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
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural verification document root drifted"
        )
    expected = _construct_verification_receipt(
        candidate,
        candidate_raw=candidate_raw,
        repository_root=repository_root,
        require_runtime_boundary=True,
    )
    if receipt != expected:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c structural receipt differs from exact tactic-free reconstruction"
        )
    return deepcopy(receipt)


def load_and_verify_pilot_dependency_vector_negative_replay_result(
    candidate_path: Path,
    *,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Strict-load one canonical A2.3c result and return its receipt."""

    raw = _safe_file(
        candidate_path,
        label="A2.3c negative-replay candidate",
        limit=MAX_DOCUMENT_BYTES,
    )
    candidate = _decode_document(
        raw, label="A2.3c negative-replay candidate", limit=MAX_DOCUMENT_BYTES
    )
    if canonical_negative_replay_verification_receipt_bytes(candidate) != raw:
        raise LibraryPilotDependencyVectorNegativeReplayVerificationError(
            "A2.3c negative-replay candidate is not canonical"
        )
    return verify_pilot_dependency_vector_negative_replay_result(
        candidate, candidate_raw=raw, repository_root=repository_root
    )


__all__ = [
    "LibraryPilotDependencyVectorNegativeReplayVerificationError",
    "PYCACHE_PREFIX",
    "VERIFICATION_FALSE_FIELDS",
    "VERIFICATION_FORMAT",
    "VERIFICATION_ID",
    "VERIFICATION_RECEIPT_BODY_FIELDS",
    "VERIFICATION_RECEIPT_FIELDS",
    "VERIFICATION_VERSION",
    "canonical_negative_replay_verification_receipt_bytes",
    "load_and_verify_pilot_dependency_vector_negative_replay_result",
    "validate_pilot_dependency_vector_negative_replay_verification_receipt",
    "verify_pilot_dependency_vector_negative_replay_result",
]
