"""Independent A2.3c replay of 22 shared A2.3b negative observations.

This module is intentionally implemented below the A2.3b producer boundary.
It reconstructs dependency-curried targets and tactic executions with the
registered ``replay_target`` / ``start`` / ``apply_tactic`` APIs.  It does not
import either A2.3b implementation module, and it does not invoke the A2.3b
candidate-body wrapper.  The retained A2.3b candidate is data: its 44
route-labelled rows are authenticated and joined two-to-one to 22 fresh body
replays.

Even a successful campaign proves only that the exact frozen scripts reject
the exact single-edge omissions under the shared Peano tactic engine.  It
does not independently execute either route-specific assembler and therefore
does not establish route rejection, logical necessity, minimality, vector
completeness, optimization, publication, admission, or A2 authority.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys
from typing import Callable, Mapping, Sequence

from peano_lab.engine.state import (
    ProofState,
    invariants_ok,
    proof_resource_metrics,
    start,
)
from peano_lab.engine.tactics import (
    TacticError,
    TacticLimit,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.artifact_codec import encode_formula, encode_proof
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Proof
from peano_lab.kernel.terms import Succ
from peano_lab.library.theorems import (
    THEOREMS,
    TheoremSpec,
    replay_target,
)


NEGATIVE_REPLAY_SCHEMA_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-schema"
)
NEGATIVE_REPLAY_SCHEMA_VERSION = 1
NEGATIVE_REPLAY_SCHEMA_ID = (
    "independent-a2.3c-pilot-dependency-vector-negative-replay-v1"
)
NEGATIVE_REPLAY_SCHEMA_PATH = Path(__file__).with_name(
    "library-pilot-dependency-vector-negative-replay-schema-v1.json"
)
NEGATIVE_REPLAY_SCHEMA_SOURCE_BYTES = 26_551
NEGATIVE_REPLAY_SCHEMA_SOURCE_SHA256 = (
    "be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4"
)
NEGATIVE_REPLAY_SCHEMA_SEMANTIC_SHA256 = (
    "a0d84c3168a9b779bfb5fdc483a2ec847e4cc34f85bcf8aee4c7351a6363ccb0"
)

NEGATIVE_REPLAY_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay"
)
NEGATIVE_REPLAY_VERSION = 1
NEGATIVE_REPLAY_ID = "independent-a2.3c-pilot-vector-negative-replay-v1"
NEGATIVE_REPLAY_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-root-preimage"
)
NEGATIVE_REPLAY_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-records-preimage"
)
NEGATIVE_REPLAY_TASKS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-tasks-preimage"
)
SOURCE_PROTOCOL_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-source-protocol"
)
SOURCE_PROTOCOL_ID = "source-only-a2.3c-negative-replay-protocol-v1"
SOURCE_PROTOCOL_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-negative-replay-source-"
    "protocol-root-preimage"
)

READABLE_ROUTE = "readable-direct-closure"
PROPOSED_LAYERED_ROUTE = "proposed-layered-closure-construction"
ROUTES = (READABLE_ROUTE, PROPOSED_LAYERED_ROUTE)
LOGIC_MODE = "intuitionistic"
EXPECTED_BASELINE_COUNT = 3
EXPECTED_OBSERVATION_COUNT = 22
EXPECTED_RETAINED_ROUTE_ROW_COUNT = 44
RETAINED_PUBLIC_GRAPH_EDGES = 1_038
EXPECTED_ROOTS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)

MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_SOURCE_BYTES = 16_000_000
MAX_JSON_DEPTH = 256
MAX_JSON_ITEMS = 4_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

IMPLEMENTATION_SOURCE_ROOT_SHA256 = (
    "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
)
EXPECTED_IMPLEMENTATION_SOURCE_COUNT = 39
QUALIFIED_CALLABLES = {
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
PYCACHE_PREFIX = "/proc/peano-hydra-a23c-disabled-pycache"
CONTROLLED_REPLAYER_MODULE_NAME = (
    "_peano_hydra_a23c_independent_negative_replayer"
)
CONTROLLED_REPLAYER_LOAD_MODE = (
    "authenticated-source-bytes-source_to_code-exec"
)
REPLAYER_RELATIVE_PATH = Path(
    "training/peano_hydra/library_pilot_dependency_vector_negative_replay.py"
)

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

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class LibraryPilotDependencyVectorNegativeReplayError(ValueError):
    """A2.3c input, execution, join, or result is invalid or unknown."""


@dataclass(frozen=True, slots=True)
class NegativeReplayTask:
    """One immutable reverse-order single-omission replay task."""

    theorem_index: int
    theorem_name: str
    attempt_index: int
    omitted_dependency: str
    full_dependencies: tuple[str, ...]
    trial_dependencies: tuple[str, ...]
    script: tuple[str, ...]
    expected_command_index: int
    expected_command: str
    expected_message: str

    def identity(self) -> dict[str, object]:
        return {
            "attempt_index": self.attempt_index,
            "expected_command": self.expected_command,
            "expected_command_index": self.expected_command_index,
            "expected_message": self.expected_message,
            "full_dependencies": list(self.full_dependencies),
            "omitted_dependency": self.omitted_dependency,
            "theorem_index": self.theorem_index,
            "theorem_name": self.theorem_name,
            "trial_dependencies": list(self.trial_dependencies),
        }


def current_negative_replay_runtime_identity() -> dict[str, object]:
    """Return the runtime fields that are pinned by the execution protocol."""

    return {
        "byteorder": sys.byteorder,
        "cache_tag": getattr(sys.implementation, "cache_tag", None),
        "implementation": sys.implementation.name,
        "int_max_str_digits": (
            sys.get_int_max_str_digits()
            if hasattr(sys, "get_int_max_str_digits")
            else None
        ),
        "major": sys.version_info.major,
        "micro": sys.version_info.micro,
        "minor": sys.version_info.minor,
        "optimize": sys.flags.optimize,
        "platform_prefix": platform.system().lower(),
        "safe_path": getattr(sys.flags, "safe_path", False),
    }


@dataclass(frozen=True, slots=True)
class NegativeReplayHooks:
    """Explicit lower-level seams used by production and synthetic tests.

    Production uses :data:`DEFAULT_NEGATIVE_REPLAY_HOOKS`.  Tests may replace
    a callable or exception type without monkeypatching module globals.  A
    completed production result records and verifies the default identities;
    a hook-substituted execution is synthetic and cannot validate as a result.
    """

    replay_target: Callable[[TheoremSpec], Formula]
    start: Callable[[Formula], object]
    apply_tactic: Callable[[object, str, str], object]
    checked_final: Callable[[object, Formula], Proof]
    proof_resource_metrics: Callable[[Proof], tuple[int, int, int, int, int]]
    proof_state_type: type[object]
    invariants_ok: Callable[[object], bool]
    encode_formula: Callable[[Formula], bytes]
    encode_proof: Callable[[Proof], bytes]
    tactic_error_type: type[BaseException]
    tactic_limit_type: type[BaseException]
    runtime_identity: Callable[[], Mapping[str, object]]
    baseline_runner: Callable[[TheoremSpec, "NegativeReplayHooks"], Mapping[str, object]] | None = None
    task_runner: Callable[[NegativeReplayTask, TheoremSpec, "NegativeReplayHooks"], Mapping[str, object]] | None = None


DEFAULT_NEGATIVE_REPLAY_HOOKS = NegativeReplayHooks(
    replay_target=replay_target,
    start=start,
    apply_tactic=apply_tactic,
    checked_final=checked_final,
    proof_resource_metrics=proof_resource_metrics,
    proof_state_type=ProofState,
    invariants_ok=invariants_ok,
    encode_formula=encode_formula,
    encode_proof=encode_proof,
    tactic_error_type=TacticError,
    tactic_limit_type=TacticLimit,
    runtime_identity=current_negative_replay_runtime_identity,
)


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
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{path} exceeds the JSON depth limit"
        )
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"{path} exceeds the JSON integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"{path} is not valid UTF-8 text"
            ) from exc
        return 1
    if type(value) not in (list, dict):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{path} contains a non-JSON value"
        )
    identity = id(value)
    if identity in ancestors:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{path} contains a cycle"
        )
    branch = ancestors | {identity}
    count = 1
    if type(value) is list:
        for index, item in enumerate(value):
            count += _validate_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=branch,
            )
            if count > MAX_JSON_ITEMS:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "JSON exceeds its item limit"
                )
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"{path} has a non-string object key"
            )
        count += 1 + _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=branch,
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryPilotDependencyVectorNegativeReplayError(
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
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "cannot encode compact canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "compact canonical JSON exceeds its byte limit"
        )
    return raw


def canonical_negative_replay_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return strict, pretty canonical A2.3c JSON with one terminal LF."""

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
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "cannot encode canonical negative-replay JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "canonical negative-replay JSON exceeds its byte limit"
        )
    return raw


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256(_compact_json(value, limit=limit))


def _decode_document(raw: bytes, *, label: str, limit: int) -> dict[str, object]:
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorNegativeReplayError(
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
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} must be one JSON object"
        )
    _validate_json(value)
    return value


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
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    f"{label} ancestor is a link or non-directory"
                )
        metadata = absolute.lstat()
    except LibraryPilotDependencyVectorNegativeReplayError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryPilotDependencyVectorNegativeReplayError(
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
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)
    identity = lambda value: (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    if len(raw) > limit or identity(before) != identity(after):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} changed or exceeded its bound while read"
        )
    return raw


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository_root must be pathlib.Path or None")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "cannot resolve repository root"
        ) from exc
    if not resolved.is_dir():
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "repository root is not a directory"
        )
    return resolved


def pilot_dependency_vector_negative_replay_schema(
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Load and authenticate the immutable A2.3c preregistration schema."""

    root = _repository_root(repository_root)
    path = root / "training/peano_hydra/library-pilot-dependency-vector-negative-replay-schema-v1.json"
    raw = _safe_regular_bytes(path, label="A2.3c schema", limit=MAX_SCHEMA_BYTES)
    if (
        len(raw) != NEGATIVE_REPLAY_SCHEMA_SOURCE_BYTES
        or _sha256(raw) != NEGATIVE_REPLAY_SCHEMA_SOURCE_SHA256
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "A2.3c schema source identity drifted"
        )
    value = _decode_document(raw, label="A2.3c schema", limit=MAX_SCHEMA_BYTES)
    if (
        canonical_negative_replay_bytes(value, limit=MAX_SCHEMA_BYTES) != raw
        or _sha256_json(value, limit=MAX_SCHEMA_BYTES)
        != NEGATIVE_REPLAY_SCHEMA_SEMANTIC_SHA256
        or value.get("format") != NEGATIVE_REPLAY_SCHEMA_FORMAT
        or value.get("v") != NEGATIVE_REPLAY_SCHEMA_VERSION
        or value.get("id") != NEGATIVE_REPLAY_SCHEMA_ID
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "A2.3c schema canonical or semantic identity drifted"
        )
    return value


def pilot_dependency_vector_negative_replay_schema_identity(
    repository_root: Path | None = None,
) -> dict[str, object]:
    schema = pilot_dependency_vector_negative_replay_schema(repository_root)
    raw = canonical_negative_replay_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256(raw),
        "bytes": len(raw),
        "id": schema["id"],
        "semantic_sha256": _sha256_json(schema, limit=MAX_SCHEMA_BYTES),
        "v": schema["v"],
    }


def _script_sha256(script: tuple[str, ...]) -> str:
    return _sha256(("\n".join(script) + "\n").encode("utf-8"))


def _split_command(command: str) -> tuple[str, str]:
    if type(command) is not str:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "script command is not text"
        )
    pieces = command.strip().split(maxsplit=1)
    if not pieces:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "script command is blank"
        )
    return pieces[0], pieces[1] if len(pieces) == 2 else ""


def single_omission_replay_tasks(
    theorem_name: str,
    theorem_index: int,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    registrations: Sequence[Mapping[str, object]],
) -> tuple[NegativeReplayTask, ...]:
    """Purely derive and validate the registered reverse-order task vector."""

    if (
        type(theorem_name) is not str
        or not theorem_name
        or type(theorem_index) is not int
        or theorem_index < 0
        or type(dependencies) is not tuple
        or not dependencies
        or not all(type(item) is str and item for item in dependencies)
        or len(set(dependencies)) != len(dependencies)
        or type(script) is not tuple
        or not script
        or not all(type(item) is str and item for item in script)
        or not isinstance(registrations, Sequence)
        or isinstance(registrations, (str, bytes, bytearray))
        or len(registrations) != len(dependencies)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "single-omission task inputs are malformed"
        )
    tasks: list[NegativeReplayTask] = []
    for attempt_index, omitted in enumerate(reversed(dependencies)):
        registration = registrations[attempt_index]
        if type(registration) is not dict or set(registration) != {
            "attempt_index",
            "expected_command",
            "expected_command_index",
            "expected_message",
            "omitted_dependency",
        }:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay task registration is malformed"
            )
        command_index = registration.get("expected_command_index")
        command = registration.get("expected_command")
        message = registration.get("expected_message")
        if (
            registration.get("attempt_index") != attempt_index
            or registration.get("omitted_dependency") != omitted
            or type(command_index) is not int
            or not 0 <= command_index < len(script)
            or type(command) is not str
            or command != script[command_index]
            or type(message) is not str
            or message != f"unknown hypothesis {omitted!r}."
            or re.search(rf"(?<![A-Za-z0-9_]){re.escape(omitted)}(?![A-Za-z0-9_])", command)
            is None
            or omitted not in message
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"negative-replay task registration drifted for {omitted!r}"
            )
        trial = tuple(item for item in dependencies if item != omitted)
        if len(trial) != len(dependencies) - 1:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "single-omission vector did not remove exactly one name"
            )
        tasks.append(
            NegativeReplayTask(
                theorem_index=theorem_index,
                theorem_name=theorem_name,
                attempt_index=attempt_index,
                omitted_dependency=omitted,
                full_dependencies=dependencies,
                trial_dependencies=trial,
                script=script,
                expected_command_index=command_index,
                expected_command=command,
                expected_message=message,
            )
        )
    return tuple(tasks)


def _registered_specs_and_tasks(
    schema: Mapping[str, object],
) -> tuple[tuple[TheoremSpec, ...], tuple[NegativeReplayTask, ...]]:
    rows = schema.get("required_theorems")
    if type(rows) is not list or len(rows) != EXPECTED_BASELINE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "registered theorem vector is malformed"
        )
    live = tuple(THEOREMS)
    if len(live) != 384 or not all(type(item) is TheoremSpec for item in live):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "live theorem table identity drifted"
        )
    specs: list[TheoremSpec] = []
    tasks: list[NegativeReplayTask] = []
    for expected_root, row in zip(EXPECTED_ROOTS, rows, strict=True):
        if type(row) is not dict or set(row) != {
            "dependencies",
            "index",
            "name",
            "script_command_count",
            "script_sha256",
            "statement_sha256",
            "tasks",
        }:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "registered theorem row is malformed"
            )
        index = row.get("index")
        name = row.get("name")
        if (index, name) != expected_root:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "registered theorem order drifted"
            )
        if type(index) is not int or not 0 <= index < len(live):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "registered theorem index is malformed"
            )
        live_spec = live[index]
        dependencies = tuple(row.get("dependencies", ()))
        script = tuple(live_spec.script)
        if (
            type(name) is not str
            or live_spec.name != name
            or not dependencies
            or len(set(dependencies)) != len(dependencies)
            or row.get("script_command_count") != len(script)
            or row.get("script_sha256") != _script_sha256(script)
            or row.get("statement_sha256")
            != _sha256(live_spec.statement.encode("utf-8"))
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"live registered theorem drifted at index {index}"
            )
        # The registered A2.3b pilot vector is deliberately reconstructed as
        # a fresh TheoremSpec.  It is a pinned upstream vector and need not be
        # identical to the current public row's pedagogical dependency list.
        spec = replace(live_spec, dependencies=dependencies)
        specs.append(spec)
        registered = row.get("tasks")
        if type(registered) is not list:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "registered task vector is malformed"
            )
        tasks.extend(
            single_omission_replay_tasks(
                name,
                index,
                dependencies,
                script,
                registered,
            )
        )
    if len(tasks) != EXPECTED_OBSERVATION_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "registered negative-replay task count drifted"
        )
    return tuple(specs), tuple(tasks)


def _false_claims() -> dict[str, bool]:
    return {field: False for field in GLOBAL_FALSE_FIELDS}


def pilot_dependency_vector_negative_replay_source_protocol(
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Describe the frozen source protocol without executing a proof campaign."""

    schema = pilot_dependency_vector_negative_replay_schema(repository_root)
    _, tasks = _registered_specs_and_tasks(schema)
    task_preimage = {
        "format": NEGATIVE_REPLAY_TASKS_PREIMAGE_FORMAT,
        "tasks": [task.identity() for task in tasks],
        "v": 1,
    }
    body: dict[str, object] = {
        **_false_claims(),
        "campaign_executed": False,
        "expected_baseline_count": EXPECTED_BASELINE_COUNT,
        "expected_independent_observation_count": EXPECTED_OBSERVATION_COUNT,
        "expected_retained_route_row_count": EXPECTED_RETAINED_ROUTE_ROW_COUNT,
        "format": SOURCE_PROTOCOL_FORMAT,
        "id": SOURCE_PROTOCOL_ID,
        "implementation_sources_authenticated": False,
        "independence": deepcopy(schema["independence_contract"]),
        "logic_mode": LOGIC_MODE,
        "negative_observations_independently_verified": False,
        "predecessor_inputs_authenticated": False,
        "result_exists": False,
        "schema": pilot_dependency_vector_negative_replay_schema_identity(
            repository_root
        ),
        "source_protocol_frozen": True,
        "status": "source-only-no-campaign",
        "task_preimage": task_preimage,
        "task_root_sha256": _sha256_json(task_preimage, limit=MAX_SCHEMA_BYTES),
        "v": 1,
    }
    preimage = {
        "format": SOURCE_PROTOCOL_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage, limit=MAX_SCHEMA_BYTES),
    }


def verify_expected_tactic_rejection(
    error: BaseException,
    *,
    task: NegativeReplayTask,
    hooks: NegativeReplayHooks = DEFAULT_NEGATIVE_REPLAY_HOOKS,
) -> dict[str, object]:
    """Purely require the exact preregistered fresh ``TacticError`` diagnostic.

    A2.3b retained the command tuple but not exception text.  The exact raw
    message and wrapper diagnostic returned here are therefore fresh A2.3c
    replay evidence, not a comparison against a retained message.
    """

    if type(task) is not NegativeReplayTask or type(hooks) is not NegativeReplayHooks:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay rejection contract is malformed"
        )
    if not (
        isinstance(hooks.tactic_error_type, type)
        and issubclass(hooks.tactic_error_type, BaseException)
        and isinstance(hooks.tactic_limit_type, type)
        and issubclass(hooks.tactic_limit_type, BaseException)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay exception hooks are malformed"
        )
    if isinstance(error, hooks.tactic_limit_type):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "resource-limit outcome is unknown, not negative evidence"
        ) from error
    if type(error) is not hooks.tactic_error_type:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "only an exact TacticError is registered negative evidence"
        ) from error
    message = str(error)
    if (
        task.omitted_dependency not in task.expected_command
        or task.omitted_dependency not in task.expected_message
        or message != task.expected_message
        or task.omitted_dependency not in message
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "fresh tactic rejection diagnostic drifted"
        ) from error
    diagnostic = (
        f"candidate {task.theorem_name!r} failed at command "
        f"{task.expected_command_index}: {task.expected_command!r}: {message}"
    )
    expected_diagnostic = (
        f"candidate {task.theorem_name!r} failed at command "
        f"{task.expected_command_index}: {task.expected_command!r}: "
        f"{task.expected_message}"
    )
    if diagnostic != expected_diagnostic or task.omitted_dependency not in diagnostic:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "fresh wrapper diagnostic drifted"
        ) from error
    return {
        "cause_type": hooks.tactic_error_type.__name__,
        "command": task.expected_command,
        "command_index": task.expected_command_index,
        "diagnostic": diagnostic,
        "kind": "exact-recipe-rejection",
        "message": message,
        "message_source": "fresh-a2.3c-lower-level-replay",
        "omitted_dependency": task.omitted_dependency,
        "phase": "command",
        "retained_message_available": False,
    }


def _require_initial_state(
    state: object,
    target: Formula,
    *,
    hooks: NegativeReplayHooks,
    label: str,
) -> None:
    try:
        valid = hooks.invariants_ok(state)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} state invariant check failed internally"
        ) from exc
    if (
        type(state) is not hooks.proof_state_type
        or getattr(state, "target", None) != target
        or getattr(state, "history", None) != ()
        or valid is not True
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} returned a malformed or target-drifted initial state"
        )


def _require_state_transition(
    before: object,
    after: object,
    target: Formula,
    *,
    tactic: str,
    args: str,
    hooks: NegativeReplayHooks,
    label: str,
) -> None:
    try:
        before_valid = hooks.invariants_ok(before)
        after_valid = hooks.invariants_ok(after)
        before_history = getattr(before, "history", None)
        after_history = getattr(after, "history", None)
        step = (
            after_history[-1]
            if type(after_history) is tuple and after_history
            else None
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} state transition check failed internally"
        ) from exc
    if (
        type(before) is not hooks.proof_state_type
        or type(after) is not hooks.proof_state_type
        or getattr(before, "target", None) != target
        or getattr(after, "target", None) != target
        or before_valid is not True
        or after_valid is not True
        or type(before_history) is not tuple
        or type(after_history) is not tuple
        or len(after_history) != len(before_history) + 1
        or after_history[:-1] != before_history
        or step is None
        or getattr(step, "state_before", None) is not before
        or getattr(step, "tactic", None) != tactic
        or getattr(step, "args", None) != args
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} returned a malformed, discontinuous, or target-drifted state"
        )


def _require_current_state(
    state: object,
    target: Formula,
    *,
    hooks: NegativeReplayHooks,
    label: str,
) -> None:
    try:
        valid = hooks.invariants_ok(state)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} state invariant check failed internally"
        ) from exc
    if (
        type(state) is not hooks.proof_state_type
        or getattr(state, "target", None) != target
        or type(getattr(state, "history", None)) is not tuple
        or valid is not True
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} carries a malformed or target-drifted state"
        )


def _run_baseline(
    spec: TheoremSpec,
    hooks: NegativeReplayHooks = DEFAULT_NEGATIVE_REPLAY_HOOKS,
) -> dict[str, object]:
    """Run one fresh full-vector baseline through the pinned lower-level APIs."""

    if type(spec) is not TheoremSpec or type(hooks) is not NegativeReplayHooks:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "baseline driver input is malformed"
        )
    try:
        target = hooks.replay_target(spec)
        state = hooks.start(target)
        _require_initial_state(state, target, hooks=hooks, label="baseline start")
        for dependency in spec.dependencies:
            before = state
            state = hooks.apply_tactic(before, "intro", dependency)
            _require_state_transition(
                before,
                state,
                target,
                tactic="intro",
                args=dependency,
                hooks=hooks,
                label="baseline dependency introduction",
            )
        for command in spec.script:
            tactic, args = _split_command(command)
            before = state
            state = hooks.apply_tactic(before, tactic, args)
            _require_state_transition(
                before,
                state,
                target,
                tactic=tactic,
                args=args,
                hooks=hooks,
                label="baseline script command",
            )
        _require_current_state(state, target, hooks=hooks, label="baseline final")
        proof = hooks.checked_final(state, target)
        metrics = hooks.proof_resource_metrics(proof)
        formula_bytes = hooks.encode_formula(target)
        proof_bytes = hooks.encode_proof(proof)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"full-vector baseline is unknown for {spec.name!r}"
        ) from exc
    if (
        not isinstance(target, Formula)
        or not isinstance(proof, Proof)
        or type(metrics) is not tuple
        or len(metrics) != 5
        or not all(type(item) is int and item >= 0 for item in metrics)
        or type(formula_bytes) is not bytes
        or type(proof_bytes) is not bytes
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"full-vector baseline returned unsupported evidence for {spec.name!r}"
        )
    nodes, depth, objects, edges, reused = metrics
    return {
        "command_count": len(spec.script),
        "dependencies": list(spec.dependencies),
        "dependency_count": len(spec.dependencies),
        "formula_sha256": _sha256(formula_bytes),
        "name": spec.name,
        "proof_sha256": _sha256(proof_bytes),
        "proof_structure": {
            "depth": depth,
            "edges": edges,
            "nodes": nodes,
            "objects": objects,
            "reused_objects": reused,
        },
        "script_sha256": _script_sha256(tuple(spec.script)),
        "status": "full-vector-baseline-kernel-accepted",
    }


def _run_negative_task(
    task: NegativeReplayTask,
    spec: TheoremSpec,
    hooks: NegativeReplayHooks = DEFAULT_NEGATIVE_REPLAY_HOOKS,
) -> dict[str, object]:
    """Replay a successful prefix and require the exact registered failure."""

    if (
        type(task) is not NegativeReplayTask
        or type(spec) is not TheoremSpec
        or type(hooks) is not NegativeReplayHooks
        or spec.name != task.theorem_name
        or tuple(spec.script) != task.script
        or tuple(spec.dependencies) != task.full_dependencies
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative task driver input is malformed"
        )
    trial_spec = replace(spec, dependencies=task.trial_dependencies)
    try:
        target = hooks.replay_target(trial_spec)
        state = hooks.start(target)
        _require_initial_state(
            state, target, hooks=hooks, label="negative replay start"
        )
        for dependency in task.trial_dependencies:
            before = state
            state = hooks.apply_tactic(before, "intro", dependency)
            _require_state_transition(
                before,
                state,
                target,
                tactic="intro",
                args=dependency,
                hooks=hooks,
                label="negative replay dependency introduction",
            )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"negative replay setup is unknown for {task.theorem_name!r}"
        ) from exc
    for command_index, command in enumerate(task.script):
        if command_index > task.expected_command_index:
            break
        tactic, args = _split_command(command)
        try:
            next_state = hooks.apply_tactic(state, tactic, args)
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            if command_index != task.expected_command_index:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "negative replay failed before its registered command"
                ) from exc
            _require_current_state(
                state,
                target,
                hooks=hooks,
                label="negative replay registered failure",
            )
            failure = verify_expected_tactic_rejection(
                exc, task=task, hooks=hooks
            )
            target_bytes = hooks.encode_formula(target)
            if type(target_bytes) is not bytes:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "negative replay target encoder returned unsupported evidence"
                )
            body: dict[str, object] = {
                "attempt_index": task.attempt_index,
                "failure": failure,
                "full_dependencies": list(task.full_dependencies),
                "name": task.theorem_name,
                "omitted_dependency": task.omitted_dependency,
                "outcome": "exact-shared-root-body-rejected",
                "prefix_command_count": task.expected_command_index,
                "target_formula_sha256": _sha256(target_bytes),
                "theorem_index": task.theorem_index,
                "trial_dependencies": list(task.trial_dependencies),
            }
            body["record_sha256"] = _sha256_json(body, limit=MAX_SCHEMA_BYTES)
            return body
        else:
            _require_state_transition(
                state,
                next_state,
                target,
                tactic=tactic,
                args=args,
                hooks=hooks,
                label="negative replay successful prefix command",
            )
            state = next_state
            if command_index == task.expected_command_index:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "single-omission script accepted its registered failure command"
                )
    raise LibraryPilotDependencyVectorNegativeReplayError(
        "negative replay did not reach its registered failure command"
    )


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def join_retained_route_rows(
    candidate: Mapping[str, object],
    observations: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Purely join 22 fresh observations to exactly 44 retained route rows."""

    if type(candidate) is not dict or not isinstance(observations, Sequence):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "retained-row join inputs are malformed"
        )
    if (
        candidate.get("format")
        != "peano-hydra-library-pilot-dependency-vector-audit"
        or candidate.get("v") != 1
        or candidate.get("id")
        != "authoring-l0-pilot-dependency-vector-audit-candidate-v1"
        or candidate.get("status") != "candidate"
        or candidate.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or candidate.get("root_sha256")
        != "21f4c7a06dd8b1abf01d8eddd8c1942733f0955141ba682d53229078e15d5e85"
        or candidate.get("theorem_records", {}).get("root_sha256")
        != "6a90eee2d8a306e41b944735940044b142cf1c4f02441133c25c94111e11d336"
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "retained A2.3b candidate identity drifted"
        )
    if len(observations) != EXPECTED_OBSERVATION_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "fresh negative observation count drifted"
        )
    fresh: dict[tuple[str, str], dict[str, object]] = {}
    fresh_order: list[tuple[str, str]] = []
    for raw in observations:
        if type(raw) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "fresh negative observation is malformed"
            )
        name = raw.get("name")
        omitted = raw.get("omitted_dependency")
        key = (name, omitted)
        failure = raw.get("failure")
        if (
            type(name) is not str
            or type(omitted) is not str
            or key in fresh
            or raw.get("outcome") != "exact-shared-root-body-rejected"
            or type(raw.get("attempt_index")) is not int
            or type(raw.get("theorem_index")) is not int
            or type(raw.get("full_dependencies")) is not list
            or type(raw.get("trial_dependencies")) is not list
            or type(failure) is not dict
            or failure.get("cause_type") != "TacticError"
            or failure.get("kind") != "exact-recipe-rejection"
            or failure.get("phase") != "command"
            or failure.get("omitted_dependency") != omitted
            or failure.get("message") != f"unknown hypothesis {omitted!r}."
            or raw.get("record_sha256") != _record_hash(raw)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "fresh negative observation contract drifted"
            )
        fresh[key] = raw
        fresh_order.append(key)
    theorem_rows = candidate.get("theorems")
    if type(theorem_rows) is not list or len(theorem_rows) != EXPECTED_BASELINE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "retained theorem rows are malformed"
        )
    joins: list[dict[str, object]] = []
    route_row_count = 0
    seen_fresh: set[tuple[str, str]] = set()
    for theorem in theorem_rows:
        if type(theorem) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained theorem row is malformed"
            )
        name = theorem.get("name")
        index = theorem.get("index")
        routes = theorem.get("routes")
        if (
            type(name) is not str
            or type(index) is not int
            or type(routes) is not list
            or len(routes) != len(ROUTES)
            or [row.get("route") for row in routes if type(row) is dict]
            != list(ROUTES)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained theorem route vector drifted"
            )
        route_attempts: list[list[dict[str, object]]] = []
        for route_name, route in zip(ROUTES, routes, strict=True):
            attempts = route.get("attempts")
            if (
                route.get("route") != route_name
                or route.get("status") != "bounded-route-audit-complete"
                or type(attempts) is not list
            ):
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "retained route receipt drifted"
                )
            route_attempts.append(attempts)
        if len(route_attempts[0]) != len(route_attempts[1]):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained route attempt counts differ"
            )
        for attempt_index, pair in enumerate(
            zip(route_attempts[0], route_attempts[1], strict=True)
        ):
            left, right = pair
            if type(left) is not dict or type(right) is not dict:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "retained route attempt is malformed"
                )
            omitted = left.get("omitted_dependency")
            key = (name, omitted)
            observation = fresh.get(key)
            if observation is None or key in seen_fresh:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "retained route row has no unique fresh observation"
                )
            expected_failure = {
                "cause_type": "TacticError",
                "command": observation["failure"]["command"],
                "command_index": observation["failure"]["command_index"],
                "kind": "exact-recipe-rejection",
                "phase": "command",
            }
            shared_digest: str | None = None
            retained_records: list[dict[str, str]] = []
            for route_name, row in zip(ROUTES, (left, right), strict=True):
                shared = row.get("shared_root_body_observation_preimage")
                digest = row.get("shared_root_body_observation_sha256")
                if (
                    row.get("route") != route_name
                    or row.get("name") != name
                    or row.get("index") != index
                    or row.get("attempt_index") != attempt_index
                    or row.get("attempt_index") != observation["attempt_index"]
                    or row.get("omitted_dependency") != omitted
                    or omitted != observation["omitted_dependency"]
                    or row.get("before_dependencies")
                    != observation["full_dependencies"]
                    or row.get("after_dependencies")
                    != observation["full_dependencies"]
                    or row.get("attempted_dependencies")
                    != observation["trial_dependencies"]
                    or row.get("failure") != expected_failure
                    or row.get("outcome") != "exact-route-rejected"
                    or row.get("terminal_stage") != "root-body-regeneration"
                    or row.get("route_specific_assembly_reached") is not False
                    or row.get("layered_compiler_invoked") is not False
                    or type(shared) is not dict
                    or shared.get("dependencies")
                    != observation["trial_dependencies"]
                    or shared.get("failure") != expected_failure
                    or shared.get("index") != index
                    or shared.get("name") != name
                    or digest != _sha256_json(shared, limit=MAX_SCHEMA_BYTES)
                    or type(digest) is not str
                    or _SHA256_RE.fullmatch(digest) is None
                    or row.get("record_sha256") != _record_hash(row)
                ):
                    raise LibraryPilotDependencyVectorNegativeReplayError(
                        "retained route row does not match fresh observation"
                    )
                if shared_digest is None:
                    shared_digest = digest
                elif shared_digest != digest:
                    raise LibraryPilotDependencyVectorNegativeReplayError(
                        "retained routes do not share one observation preimage"
                    )
                retained_records.append(
                    {"record_sha256": row["record_sha256"], "route": route_name}
                )
                route_row_count += 1
            seen_fresh.add(key)
            joins.append(
                {
                    "attempt_index": attempt_index,
                    "fresh_observation_record_sha256": observation["record_sha256"],
                    "name": name,
                    "omitted_dependency": omitted,
                    "retained_message_available": False,
                    "retained_route_records": retained_records,
                    "retained_shared_observation_sha256": shared_digest,
                    "route_row_count": 2,
                    "theorem_index": index,
                }
            )
    if (
        route_row_count != EXPECTED_RETAINED_ROUTE_ROW_COUNT
        or len(joins) != EXPECTED_OBSERVATION_COUNT
        or seen_fresh != set(fresh)
        or fresh_order
        != [(row["name"], row["omitted_dependency"]) for row in joins]
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "retained 44-to-22 route join is incomplete"
        )
    preimage = {
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "retained-route-join-preimage"
        ),
        "joins": joins,
        "v": 1,
    }
    return {
        "fresh_observation_count": len(joins),
        "joins": joins,
        "preimage": preimage,
        "retained_route_row_count": route_row_count,
        "root_sha256": _sha256_json(preimage),
        "route_rows_per_observation": 2,
        "status": "exact-44-route-rows-joined-two-to-one",
    }


def _safe_relative(value: object, *, label: str) -> Path:
    if type(value) is not str:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} path is malformed"
        )
    path = Path(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            f"{label} path is unsafe"
        )
    return path


def _authenticate_implementation_sources(
    root: Path, schema: Mapping[str, object]
) -> list[dict[str, str]]:
    rows = schema.get("implementation_sources")
    if type(rows) is not list or len(rows) != EXPECTED_IMPLEMENTATION_SOURCE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "implementation source vector count drifted"
        )
    if (
        schema.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or _sha256_json(rows, limit=MAX_SCHEMA_BYTES)
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "implementation source vector root drifted"
        )
    authenticated: list[dict[str, str]] = []
    seen: set[Path] = set()
    for row in rows:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "implementation source row is malformed"
            )
        relative = _safe_relative(row.get("path"), label="implementation source")
        digest = row.get("sha256")
        if (
            relative in seen
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "implementation source identity is duplicated or malformed"
            )
        raw = _safe_regular_bytes(
            root / relative,
            label=f"implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if _sha256(raw) != digest:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"implementation source {relative.as_posix()!r} drifted"
            )
        seen.add(relative)
        authenticated.append({"path": relative.as_posix(), "sha256": digest})
    return authenticated


def _authenticate_fixed_inputs(
    root: Path, schema: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    registered = schema.get("fixed_inputs")
    expected_labels = {
        "a2.3b_candidate",
        "a2.3b_collection",
        "a2.3b_execution",
        "a2.3b_verification",
        "replay_manifest",
        "replay_report",
    }
    if type(registered) is not dict or set(registered) != expected_labels:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "fixed predecessor input vector drifted"
        )
    loaded: dict[str, dict[str, object]] = {}
    for label in sorted(expected_labels):
        identity = registered[label]
        if type(identity) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"fixed input identity {label!r} is malformed"
            )
        relative = _safe_relative(identity.get("path"), label=label)
        expected_bytes = identity.get("bytes")
        expected_sha = identity.get("artifact_sha256")
        if (
            type(expected_bytes) is not int
            or not 0 <= expected_bytes <= MAX_DOCUMENT_BYTES
            or type(expected_sha) is not str
            or _SHA256_RE.fullmatch(expected_sha) is None
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"fixed input identity {label!r} drifted"
            )
        raw = _safe_regular_bytes(
            root / relative, label=f"fixed input {label!r}", limit=MAX_DOCUMENT_BYTES
        )
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"fixed input {label!r} artifact identity drifted"
            )
        value = _decode_document(raw, label=f"fixed input {label!r}", limit=MAX_DOCUMENT_BYTES)
        if canonical_negative_replay_bytes(value) != raw:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"fixed input {label!r} is noncanonical"
            )
        for field in ("root_sha256", "replay_root_sha256"):
            if field in identity and value.get(field) != identity[field]:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    f"fixed input {label!r} {field} drifted"
                )
        if "theorem_records_root_sha256" in identity and (
            value.get("theorem_records", {}).get("root_sha256")
            != identity["theorem_records_root_sha256"]
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"fixed input {label!r} theorem-record root drifted"
            )
        loaded[label] = value
    candidate = loaded["a2.3b_candidate"]
    verification = loaded["a2.3b_verification"]
    execution = loaded["a2.3b_execution"]
    collection = loaded["a2.3b_collection"]
    manifest = loaded["replay_manifest"]
    report = loaded["replay_report"]
    replay_input = candidate.get("inputs", {}).get("replay", {})
    if (
        candidate.get("status") != "candidate"
        or candidate.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or verification.get("status") != "passed"
        or verification.get("candidate_status") != "candidate"
        or verification.get("negative_observations_independently_verified")
        is not False
        or verification.get("route_rejections_independently_verified") is not False
        or execution.get("status") != "passed"
        or collection.get("status") != "passed"
        or manifest.get("theorem_count") != 384
        or report.get("theorem_count") != 384
        or report.get("status") != "passed"
        or replay_input.get("manifest_artifact_sha256")
        != registered["replay_manifest"]["artifact_sha256"]
        or replay_input.get("manifest_root_sha256")
        != registered["replay_manifest"]["root_sha256"]
        or replay_input.get("replay_report_artifact_sha256")
        != registered["replay_report"]["artifact_sha256"]
        or replay_input.get("replay_root_sha256")
        != registered["replay_manifest"]["replay_root_sha256"]
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "fixed predecessor cross-binding drifted"
        )
    return loaded


def _retained_baseline_expectations(
    candidate: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    rows = candidate.get("theorems")
    if type(rows) is not list or len(rows) != EXPECTED_BASELINE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "retained baseline theorem vector is malformed"
        )
    result: dict[str, dict[str, object]] = {}
    for row, (index, name) in zip(rows, EXPECTED_ROOTS, strict=True):
        if (
            type(row) is not dict
            or row.get("index") != index
            or row.get("name") != name
            or type(row.get("routes")) is not list
            or len(row["routes"]) != 2
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained baseline theorem order drifted"
            )
        receipts: list[dict[str, object]] = []
        for route, route_name in zip(row["routes"], ROUTES, strict=True):
            receipt = (
                route.get("baseline", {})
                .get("diagnostics", {})
                .get("root_body_receipt")
            )
            if route.get("route") != route_name or type(receipt) is not dict:
                raise LibraryPilotDependencyVectorNegativeReplayError(
                    "retained root-body baseline receipt is malformed"
                )
            receipts.append(receipt)
        if receipts[0] != receipts[1]:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained routes disagree on their shared root-body baseline"
            )
        receipt = receipts[0]
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
        }:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "retained root-body baseline fields drifted"
            )
        result[name] = {
            "command_count": receipt["command_count"],
            "dependency_count": receipt["dependency_count"],
            "formula_sha256": receipt["target_formula_sha256"],
            "proof_sha256": receipt["certificate_sha256"],
            "proof_structure": {
                "depth": receipt["proof_depth"],
                "edges": receipt["proof_edges"],
                "nodes": receipt["proof_nodes"],
                "objects": receipt["proof_objects"],
                "reused_objects": receipt["reused_objects"],
            },
        }
    return result


def _require_production_hooks(
    root: Path,
    schema: Mapping[str, object],
    hooks: NegativeReplayHooks,
) -> dict[str, object]:
    if hooks is not DEFAULT_NEGATIVE_REPLAY_HOOKS:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "a production campaign requires the exact registered hook set"
        )
    if schema.get("qualified_callables") != QUALIFIED_CALLABLES:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "qualified callable registration drifted"
        )
    callables: dict[str, object] = {
        "apply_tactic": hooks.apply_tactic,
        "checked_final": hooks.checked_final,
        "formula_encode": hooks.encode_formula,
        "proof_encode": hooks.encode_proof,
        "proof_metrics": hooks.proof_resource_metrics,
        "proof_state_invariants": hooks.invariants_ok,
        "proof_state_type": hooks.proof_state_type,
        "replay_target": hooks.replay_target,
        "start": hooks.start,
    }
    implementation_paths = {
        row["path"] for row in schema["implementation_sources"]
    }
    receipts: list[dict[str, str]] = []
    for label, qualified in QUALIFIED_CALLABLES.items():
        value = callables[label]
        module_name, _, qualname = qualified.rpartition(".")
        if (
            getattr(value, "__module__", None) != module_name
            or getattr(value, "__qualname__", None) != qualname
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"qualified callable {qualified!r} drifted"
            )
        module = importlib.import_module(module_name)
        if getattr(module, qualname, None) is not value:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"callable alias {qualified!r} drifted"
            )
        source = getattr(module, "__file__", None)
        if type(source) is not str:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"callable module {module_name!r} has no source"
            )
        try:
            relative = Path(source).resolve(strict=True).relative_to(root)
        except (OSError, ValueError) as exc:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"callable module origin {module_name!r} escaped the repository"
            ) from exc
        if relative.as_posix() not in implementation_paths:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"callable source {relative.as_posix()!r} is not pinned"
            )
        receipts.append(
            {
                "qualified_name": qualified,
                "source_path": relative.as_posix(),
            }
        )
    return {
        "callables": receipts,
        "qualified_callables": deepcopy(QUALIFIED_CALLABLES),
        "status": "exact-callable-identities-authenticated",
    }


def _controlled_replayer_identity(root: Path) -> dict[str, object]:
    raw = _safe_regular_bytes(
        root / REPLAYER_RELATIVE_PATH,
        label="A2.3c replayer source",
        limit=MAX_SOURCE_BYTES,
    )
    return {
        "bytes": len(raw),
        "load_mode": CONTROLLED_REPLAYER_LOAD_MODE,
        "module_name": CONTROLLED_REPLAYER_MODULE_NAME,
        "path": REPLAYER_RELATIVE_PATH.as_posix(),
        "pycache_prefix": PYCACHE_PREFIX,
        "sha256": _sha256(raw),
        "source_loader": "importlib.machinery.SourceFileLoader",
    }


def _require_replayer_identity(
    root: Path, value: Mapping[str, object] | None, *, controlled: bool
) -> dict[str, object]:
    expected = _controlled_replayer_identity(root)
    if value is None:
        if controlled:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "production replay requires an authenticated loader identity"
            )
        return {
            **expected,
            "load_mode": "direct-source-authentication-no-execution-claim",
            "module_name": __name__,
        }
    if type(value) is not dict or set(value) != set(expected):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "authenticated replayer identity is malformed"
        )
    if controlled:
        wanted = expected
    else:
        wanted = {
            **expected,
            "load_mode": value.get("load_mode"),
            "module_name": value.get("module_name"),
        }
    if (
        value != wanted
        or type(value.get("module_name")) is not str
        or not value["module_name"]
        or type(value.get("load_mode")) is not str
        or not value["load_mode"]
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "authenticated replayer source identity drifted"
        )
    return deepcopy(value)


def authenticate_negative_replay_environment(
    repository_root: Path | None = None,
    *,
    hooks: NegativeReplayHooks = DEFAULT_NEGATIVE_REPLAY_HOOKS,
    replayer_identity: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Authenticate all source, predecessor, callable, and runtime bindings."""

    root = _repository_root(repository_root)
    schema = pilot_dependency_vector_negative_replay_schema(root)
    forbidden = sorted(
        name
        for name in sys.modules
        if name
        in {
            "peano_lab.library.candidate_validation",
            "training.peano_hydra.library_pilot_dependency_vector_audit",
            "training.peano_hydra.library_pilot_dependency_vector_audit_verifier",
        }
    )
    if forbidden:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay process is contaminated by a forbidden wrapper"
        )
    sources = _authenticate_implementation_sources(root, schema)
    callables = _require_production_hooks(root, schema, hooks)
    fixed = _authenticate_fixed_inputs(root, schema)
    replayer = _require_replayer_identity(
        root,
        replayer_identity,
        controlled=hooks is DEFAULT_NEGATIVE_REPLAY_HOOKS,
    )
    runtime = dict(hooks.runtime_identity())
    if runtime != schema.get("runtime_binding"):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay runtime identity drifted"
        )
    preimage = {
        "callables": callables,
        "fixed_inputs": deepcopy(schema["fixed_inputs"]),
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "environment-preimage"
        ),
        "implementation_source_root_sha256": (
            IMPLEMENTATION_SOURCE_ROOT_SHA256
        ),
        "runtime": runtime,
        "replayer": replayer,
        "schema": pilot_dependency_vector_negative_replay_schema_identity(root),
        "v": 1,
    }
    # Keep decoded predecessors private while exposing their authenticated
    # bytes through the immutable schema identities and one environment root.
    return {
        "callables": callables,
        "fixed_input_count": len(fixed),
        "implementation_source_count": len(sources),
        "implementation_source_root_sha256": (
            IMPLEMENTATION_SOURCE_ROOT_SHA256
        ),
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "runtime": runtime,
        "replayer": replayer,
        "status": "all-execution-bindings-authenticated",
    }


def _records_bundle(
    records: Sequence[Mapping[str, object]], *, kind: str
) -> dict[str, object]:
    identities: list[dict[str, object]] = []
    for index, record in enumerate(records):
        if type(record) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"{kind} record is malformed"
            )
        digest = record.get("record_sha256")
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                f"{kind} record identity is malformed"
            )
        identities.append({"index": index, "record_sha256": digest})
    preimage = {
        "format": NEGATIVE_REPLAY_RECORDS_PREIMAGE_FORMAT,
        "kind": kind,
        "records": identities,
        "v": 1,
    }
    return {
        "count": len(records),
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def build_pilot_dependency_vector_negative_replay(
    repository_root: Path | None = None,
    *,
    hooks: NegativeReplayHooks = DEFAULT_NEGATIVE_REPLAY_HOOKS,
    replayer_identity: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Execute the real bounded A2.3c campaign and return its result.

    This function has no output side effect.  Production rejects substituted
    hooks; focused synthetic tests exercise :func:`_run_baseline`,
    :func:`_run_negative_task`, and :func:`join_retained_route_rows` directly.
    """

    root = _repository_root(repository_root)
    schema = pilot_dependency_vector_negative_replay_schema(root)
    environment = authenticate_negative_replay_environment(
        root,
        hooks=hooks,
        replayer_identity=replayer_identity,
    )
    fixed = _authenticate_fixed_inputs(root, schema)
    retained_baselines = _retained_baseline_expectations(
        fixed["a2.3b_candidate"]
    )
    specs, tasks = _registered_specs_and_tasks(schema)
    specs_by_name = {spec.name: spec for spec in specs}
    baselines: list[dict[str, object]] = []
    for index, spec in zip((item[0] for item in EXPECTED_ROOTS), specs, strict=True):
        runner = hooks.baseline_runner or _run_baseline
        raw = runner(spec, hooks)
        if type(raw) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "baseline runner returned unsupported evidence"
            )
        expected_baseline = retained_baselines[spec.name]
        if any(raw.get(field) != expected_baseline[field] for field in expected_baseline):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "independent baseline does not match the retained root-body identity"
            )
        record = {**deepcopy(raw), "theorem_index": index}
        record["record_sha256"] = _record_hash(record)
        baselines.append(record)
    observations: list[dict[str, object]] = []
    for task in tasks:
        runner = hooks.task_runner or _run_negative_task
        raw = runner(task, specs_by_name[task.theorem_name], hooks)
        if type(raw) is not dict or raw.get("record_sha256") != _record_hash(raw):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative task runner returned unsupported evidence"
            )
        observations.append(deepcopy(raw))
    join = join_retained_route_rows(fixed["a2.3b_candidate"], observations)
    theorem_records: list[dict[str, object]] = []
    for (index, name), baseline in zip(EXPECTED_ROOTS, baselines, strict=True):
        selected = [row for row in observations if row["name"] == name]
        record: dict[str, object] = {
            **_false_claims(),
            "baseline": baseline,
            "index": index,
            "name": name,
            "negative_observation_count": len(selected),
            "negative_observations": selected,
            "negative_observations_independently_verified": True,
            "route_rejections_independently_verified": False,
        }
        record["record_sha256"] = _record_hash(record)
        theorem_records.append(record)
    baseline_bundle = _records_bundle(baselines, kind="full-vector-baselines")
    observation_bundle = _records_bundle(
        observations, kind="independent-shared-root-body-negative-replays"
    )
    theorem_bundle = _records_bundle(theorem_records, kind="theorems")
    body: dict[str, object] = {
        **_false_claims(),
        "aggregate": {
            "full_vector_baseline_count": len(baselines),
            "independent_shared_observation_count": len(observations),
            "retained_route_row_count": join["retained_route_row_count"],
            "route_rows_per_shared_observation": 2,
            "theorem_count": len(theorem_records),
        },
        "baseline_records": baselines,
        "baselines": baseline_bundle,
        "campaign_executed": True,
        "environment": environment,
        "format": NEGATIVE_REPLAY_FORMAT,
        "id": NEGATIVE_REPLAY_ID,
        "independence": deepcopy(schema["independence_contract"]),
        "logic_mode": LOGIC_MODE,
        "negative_observation_records": observations,
        "negative_observations": observation_bundle,
        "negative_observations_independently_verified": True,
        "predecessors": deepcopy(schema["fixed_inputs"]),
        "result_exists": True,
        "retained_route_join": join,
        "route_rejections_independently_verified": False,
        "schema": pilot_dependency_vector_negative_replay_schema_identity(root),
        "status": "passed",
        "theorem_count": len(theorem_records),
        "theorem_records": theorem_bundle,
        "theorems": theorem_records,
        "v": NEGATIVE_REPLAY_VERSION,
    }
    preimage = {
        "format": NEGATIVE_REPLAY_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    result = {
        **body,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }
    return validate_pilot_dependency_vector_negative_replay(result)


def validate_pilot_dependency_vector_negative_replay(
    value: object,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Deeply validate a completed A2.3c result without rerunning tactics."""

    if type(value) is not dict:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay result must be one object"
        )
    expected_fields = {
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
        "route_rejections_independently_verified",
        "schema",
        "status",
        "theorem_count",
        "theorem_records",
        "theorems",
        "v",
    }
    if set(value) != expected_fields:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay result has unregistered fields"
        )
    if any(value.get(field) is not False for field in GLOBAL_FALSE_FIELDS):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay result asserted a forbidden claim"
        )
    root = _repository_root(repository_root)
    schema = pilot_dependency_vector_negative_replay_schema(root)
    fixed = _authenticate_fixed_inputs(root, schema)
    retained_baselines = _retained_baseline_expectations(
        fixed["a2.3b_candidate"]
    )
    specs, tasks = _registered_specs_and_tasks(schema)
    aggregate = value.get("aggregate")
    baselines = value.get("baseline_records")
    observations = value.get("negative_observation_records")
    theorems = value.get("theorems")
    if (
        value.get("format") != NEGATIVE_REPLAY_FORMAT
        or value.get("v") != NEGATIVE_REPLAY_VERSION
        or value.get("id") != NEGATIVE_REPLAY_ID
        or value.get("status") != "passed"
        or value.get("logic_mode") != LOGIC_MODE
        or value.get("campaign_executed") is not True
        or value.get("result_exists") is not True
        or value.get("negative_observations_independently_verified") is not True
        or value.get("route_rejections_independently_verified") is not False
        or value.get("theorem_count") != EXPECTED_BASELINE_COUNT
        or type(aggregate) is not dict
        or aggregate
        != {
            "full_vector_baseline_count": EXPECTED_BASELINE_COUNT,
            "independent_shared_observation_count": EXPECTED_OBSERVATION_COUNT,
            "retained_route_row_count": EXPECTED_RETAINED_ROUTE_ROW_COUNT,
            "route_rows_per_shared_observation": 2,
            "theorem_count": EXPECTED_BASELINE_COUNT,
        }
        or type(baselines) is not list
        or len(baselines) != EXPECTED_BASELINE_COUNT
        or type(observations) is not list
        or len(observations) != EXPECTED_OBSERVATION_COUNT
        or type(theorems) is not list
        or len(theorems) != EXPECTED_BASELINE_COUNT
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay result aggregate drifted"
        )

    if (
        value.get("schema")
        != pilot_dependency_vector_negative_replay_schema_identity(root)
        or value.get("predecessors") != schema.get("fixed_inputs")
        or value.get("independence") != schema.get("independence_contract")
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay immutable input binding drifted"
        )
    environment = value.get("environment")
    expected_callable_sources = {
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
    expected_callable_receipt = {
        "callables": [
            {
                "qualified_name": qualified,
                "source_path": expected_callable_sources[label],
            }
            for label, qualified in QUALIFIED_CALLABLES.items()
        ],
        "qualified_callables": deepcopy(QUALIFIED_CALLABLES),
        "status": "exact-callable-identities-authenticated",
    }
    if type(environment) is not dict or set(environment) != {
        "callables",
        "fixed_input_count",
        "implementation_source_count",
        "implementation_source_root_sha256",
        "preimage",
        "replayer",
        "root_sha256",
        "runtime",
        "status",
    }:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay environment receipt is malformed"
        )
    expected_environment_preimage = {
        "callables": expected_callable_receipt,
        "fixed_inputs": deepcopy(schema["fixed_inputs"]),
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "environment-preimage"
        ),
        "implementation_source_root_sha256": IMPLEMENTATION_SOURCE_ROOT_SHA256,
        "runtime": deepcopy(schema["runtime_binding"]),
        "replayer": _controlled_replayer_identity(root),
        "schema": pilot_dependency_vector_negative_replay_schema_identity(root),
        "v": 1,
    }
    if (
        environment.get("callables") != expected_callable_receipt
        or environment.get("fixed_input_count") != 6
        or environment.get("implementation_source_count")
        != EXPECTED_IMPLEMENTATION_SOURCE_COUNT
        or environment.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or environment.get("runtime") != schema.get("runtime_binding")
        or environment.get("replayer") != _controlled_replayer_identity(root)
        or environment.get("status")
        != "all-execution-bindings-authenticated"
        or environment.get("preimage") != expected_environment_preimage
        or environment.get("root_sha256")
        != _sha256_json(expected_environment_preimage)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay environment binding drifted"
        )

    expected_tasks = list(tasks)
    for baseline, (index, name), spec in zip(
        baselines, EXPECTED_ROOTS, specs, strict=True
    ):
        if type(baseline) is not dict or set(baseline) != {
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
        }:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay baseline record is malformed"
            )
        metrics = baseline.get("proof_structure")
        if (
            baseline.get("name") != name
            or baseline.get("theorem_index") != index
            or baseline.get("dependencies") != list(spec.dependencies)
            or baseline.get("dependency_count") != len(spec.dependencies)
            or baseline.get("command_count") != len(spec.script)
            or baseline.get("script_sha256") != _script_sha256(tuple(spec.script))
            or baseline.get("status")
            != "full-vector-baseline-kernel-accepted"
            or baseline.get("formula_sha256")
            != retained_baselines[name]["formula_sha256"]
            or baseline.get("proof_sha256")
            != retained_baselines[name]["proof_sha256"]
            or type(metrics) is not dict
            or set(metrics) != {"depth", "edges", "nodes", "objects", "reused_objects"}
            or metrics != retained_baselines[name]["proof_structure"]
            or baseline.get("record_sha256") != _record_hash(baseline)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay baseline semantics drifted"
            )

    specs_by_name = {spec.name: spec for spec in specs}
    for observation, task in zip(observations, expected_tasks, strict=True):
        if type(observation) is not dict or set(observation) != {
            "attempt_index",
            "failure",
            "full_dependencies",
            "name",
            "omitted_dependency",
            "outcome",
            "prefix_command_count",
            "record_sha256",
            "target_formula_sha256",
            "theorem_index",
            "trial_dependencies",
        }:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay observation record is malformed"
            )
        expected_failure = {
            "cause_type": "TacticError",
            "command": task.expected_command,
            "command_index": task.expected_command_index,
            "diagnostic": (
                f"candidate {task.theorem_name!r} failed at command "
                f"{task.expected_command_index}: {task.expected_command!r}: "
                f"{task.expected_message}"
            ),
            "kind": "exact-recipe-rejection",
            "message": task.expected_message,
            "message_source": "fresh-a2.3c-lower-level-replay",
            "omitted_dependency": task.omitted_dependency,
            "phase": "command",
            "retained_message_available": False,
        }
        try:
            trial_spec = replace(
                specs_by_name[task.theorem_name],
                dependencies=task.trial_dependencies,
            )
            expected_target = DEFAULT_NEGATIVE_REPLAY_HOOKS.replay_target(
                trial_spec
            )
            expected_target_bytes = (
                DEFAULT_NEGATIVE_REPLAY_HOOKS.encode_formula(expected_target)
            )
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "cannot reconstruct registered negative-replay target"
            ) from exc
        if type(expected_target_bytes) is not bytes:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "registered negative-replay target encoding is unsupported"
            )
        if (
            observation.get("attempt_index") != task.attempt_index
            or observation.get("theorem_index") != task.theorem_index
            or observation.get("name") != task.theorem_name
            or observation.get("omitted_dependency") != task.omitted_dependency
            or observation.get("full_dependencies") != list(task.full_dependencies)
            or observation.get("trial_dependencies") != list(task.trial_dependencies)
            or observation.get("prefix_command_count")
            != task.expected_command_index
            or observation.get("failure") != expected_failure
            or observation.get("outcome")
            != "exact-shared-root-body-rejected"
            or observation.get("target_formula_sha256")
            != _sha256(expected_target_bytes)
            or observation.get("record_sha256") != _record_hash(observation)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay observation semantics drifted"
            )

    offset = 0
    for theorem, baseline, (index, name), spec in zip(
        theorems, baselines, EXPECTED_ROOTS, specs, strict=True
    ):
        count = len(spec.dependencies)
        selected = observations[offset : offset + count]
        offset += count
        expected_theorem_fields = {
            *GLOBAL_FALSE_FIELDS,
            "baseline",
            "index",
            "name",
            "negative_observation_count",
            "negative_observations",
            "negative_observations_independently_verified",
            "record_sha256",
        }
        if (
            type(theorem) is not dict
            or set(theorem) != expected_theorem_fields
            or any(theorem.get(field) is not False for field in GLOBAL_FALSE_FIELDS)
            or theorem.get("index") != index
            or theorem.get("name") != name
            or theorem.get("baseline") != baseline
            or theorem.get("negative_observation_count") != count
            or theorem.get("negative_observations") != selected
            or theorem.get("negative_observations_independently_verified")
            is not True
            or theorem.get("record_sha256") != _record_hash(theorem)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay theorem partition drifted"
            )
    if offset != EXPECTED_OBSERVATION_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay theorem partition is incomplete"
        )

    for bundle, collection, kind in (
        (value.get("baselines"), baselines, "full-vector-baselines"),
        (
            value.get("negative_observations"),
            observations,
            "independent-shared-root-body-negative-replays",
        ),
        (value.get("theorem_records"), theorems, "theorems"),
    ):
        expected_bundle = _records_bundle(collection, kind=kind)
        if bundle != expected_bundle:
            raise LibraryPilotDependencyVectorNegativeReplayError(
                "negative-replay record bundle drifted"
            )
    expected_join = join_retained_route_rows(
        fixed["a2.3b_candidate"], observations
    )
    if value.get("retained_route_join") != expected_join:
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay retained-route join drifted"
        )
    root_preimage = {
        "format": NEGATIVE_REPLAY_ROOT_PREIMAGE_FORMAT,
        "payload": {
            key: item
            for key, item in value.items()
            if key not in {"root_preimage", "root_sha256"}
        },
        "v": 1,
    }
    if (
        value.get("root_preimage") != root_preimage
        or value.get("root_sha256") != _sha256_json(root_preimage)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayError(
            "negative-replay document root drifted"
        )
    canonical_negative_replay_bytes(value)
    return deepcopy(value)


__all__ = [
    "DEFAULT_NEGATIVE_REPLAY_HOOKS",
    "LibraryPilotDependencyVectorNegativeReplayError",
    "NEGATIVE_REPLAY_FORMAT",
    "NEGATIVE_REPLAY_ID",
    "NEGATIVE_REPLAY_SCHEMA_FORMAT",
    "NEGATIVE_REPLAY_SCHEMA_ID",
    "NEGATIVE_REPLAY_SCHEMA_VERSION",
    "NEGATIVE_REPLAY_VERSION",
    "NegativeReplayHooks",
    "NegativeReplayTask",
    "authenticate_negative_replay_environment",
    "build_pilot_dependency_vector_negative_replay",
    "canonical_negative_replay_bytes",
    "current_negative_replay_runtime_identity",
    "join_retained_route_rows",
    "pilot_dependency_vector_negative_replay_schema",
    "pilot_dependency_vector_negative_replay_schema_identity",
    "pilot_dependency_vector_negative_replay_source_protocol",
    "single_omission_replay_tasks",
    "validate_pilot_dependency_vector_negative_replay",
    "verify_expected_tactic_rejection",
]
