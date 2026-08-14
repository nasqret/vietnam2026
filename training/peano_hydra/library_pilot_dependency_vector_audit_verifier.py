"""Independent verifier for the bounded Hydra A2.3b vector-audit result.

This module deliberately imports only the unchanged Peano kernel.  It does
not import the A2.3b producer, tactic engine, theorem library, layered
compiler, replay-pack implementation, or ``training.peano_hydra`` package
initializer.

The verifier independently authenticates, decodes, canonically re-encodes,
and kernel-checks six retained baseline artifacts: the three readable-route
baselines through the exact A2.2 embedded artifacts and the three layered
baselines through the exact A2.3a embedded artifacts.  The 44 negative route
rows are a different kind of evidence.  They represent 44 producer
``compile_candidate_body`` executions whose equal route-paired contents form
22 unique shared observation preimages.  This verifier can check their
structure, hashes, order, surfaces, and pairing, but it does not rerun tactics
and therefore does not independently verify those negative executions.
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
    "peano-hydra-library-pilot-dependency-vector-audit-verification"
)
VERIFICATION_VERSION = 1
VERIFICATION_ID = (
    "independent-a2.3b-pilot-dependency-vector-audit-verification-v1"
)
VERIFICATION_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-verification-"
    "root-preimage"
)
VERIFICATION_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-verification-"
    "records-preimage"
)

CANDIDATE_FORMAT = "peano-hydra-library-pilot-dependency-vector-audit"
CANDIDATE_VERSION = 1
CANDIDATE_ID = "authoring-l0-pilot-dependency-vector-audit-candidate-v1"
CANDIDATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-root-preimage"
)
CANDIDATE_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-records-preimage"
)
ATTEMPT_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-attempts-preimage"
)
ROUTE_RECEIPT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-route-preimage"
)
BASELINE_RECEIPT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-baseline-preimage"
)
PRODUCER_SOURCE_STATE_FORMAT = "peano-hydra-producer-source-state"
PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-producer-source-state-root-preimage"
)

READABLE_ROUTE = "readable-direct-closure"
LAYERED_ROUTE = "proposed-layered-closure-construction"
ROUTES = (READABLE_ROUTE, LAYERED_ROUTE)
LOGIC_MODE = "intuitionistic"
CANDIDATE_STATUS = "candidate"
VERIFICATION_STATUS = "passed"
PYCACHE_PREFIX = "/proc/peano-hydra-a23b-disabled-pycache"

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

EXPECTED_THEOREMS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
EXPECTED_DIRECT = {
    "odd_add_odd": ("mul_add", "add_assoc", "add_comm"),
    "finite_bounded_injective_surjective": (
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
    "beta_product_swap_last_invariant": (
        "beta_product_replace_balance",
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_succ",
        "lt_irrefl_expanded",
    ),
}
EXPECTED_CLOSURE_COUNTS = {
    "odd_add_odd": 5,
    "finite_bounded_injective_surjective": 119,
    "beta_product_swap_last_invariant": 31,
}
EXPECTED_ATTEMPT_COUNT = 44
EXPECTED_UNIQUE_SHARED_OBSERVATION_COUNT = 22
EXPECTED_BASELINE_ARTIFACT_COUNT = 6
RETAINED_PUBLIC_GRAPH_EDGES = 1_038

GLOBAL_FALSE_FIELDS = (
    "a2_complete",
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
    "theorem_admission_authority",
    "training_eligible",
)

VERIFICATION_FALSE_FIELDS = (
    *GLOBAL_FALSE_FIELDS,
    "bounded_three_root_vector_audit_complete",
    "negative_observations_independently_verified",
    "producer_git_verified",
    "producer_observations_execution_bound",
    "route_rejections_independently_verified",
)
VERIFICATION_RECEIPT_BODY_FIELDS = frozenset(
    {
        *VERIFICATION_FALSE_FIELDS,
        "aggregate",
        "candidate",
        "candidate_status",
        "format",
        "id",
        "kernel_baseline_artifacts_verified",
        "logic_mode",
        "producer_observations_structurally_verified",
        "producer_source_state",
        "producer_source_state_sha256",
        "status",
        "structural_receipts_verified",
        "theorem_count",
        "theorem_records",
        "v",
        "verifier",
    }
)
VERIFICATION_RECEIPT_FIELDS = frozenset(
    {*VERIFICATION_RECEIPT_BODY_FIELDS, "root_preimage", "root_sha256", "theorems"}
)

_CANDIDATE_ROOT_BODY_FIELDS = frozenset(
    {
        *GLOBAL_FALSE_FIELDS,
        "aggregate",
        "bounded_protocol_executed",
        "bounded_three_root_protocol_frozen",
        "bounded_three_root_vector_audit_complete",
        "format",
        "id",
        "implementation",
        "inputs",
        "logic_mode",
        "producer_git_verified",
        "producer_source_state",
        "producer_source_state_sha256",
        "schema",
        "single_omission_terminal_count",
        "status",
        "terminal_route_observations_complete",
        "theorem_count",
        "theorem_records",
        "v",
    }
)
_THEOREM_FIELDS = frozenset(
    {
        *GLOBAL_FALSE_FIELDS,
        "bounded_local_union",
        "bounded_protocol_executed",
        "bounded_three_root_vector_audit_complete",
        "index",
        "name",
        "record_sha256",
        "routes",
        "shared_body_consistency",
        "single_omission_attempt_count",
        "single_omission_kernel_accepted_count",
        "single_omission_rejected_count",
        "single_omission_terminal_count",
        "statement",
        "terminal_route_observations_complete",
    }
)
_ROUTE_FIELDS = frozenset(
    {
        "attempt_records",
        "attempts",
        "baseline",
        "route",
        "route_receipt_preimage",
        "route_receipt_sha256",
        "single_omission_kernel_accepted_count",
        "single_omission_rejected_count",
        "status",
    }
)
_BASELINE_FIELDS = frozenset(
    {"diagnostics", "preimage", "proof", "sha256", "status", "surface"}
)
_PROOF_RECEIPT_FIELDS = frozenset(
    {
        "formula_sha256",
        "kernel_accepted",
        "kernel_context",
        "logic_mode",
        "metrics",
        "proof_term_sha256",
    }
)
_SURFACE_FIELDS = frozenset(
    {
        "direct_dependencies",
        "direct_dependencies_lf_sha256",
        "direct_dependency_count",
        "surface_basis",
        "transitive_closure_count",
        "transitive_closure_dependencies_in_replay_order",
        "transitive_closure_lf_sha256",
    }
)
_REJECTED_ATTEMPT_FIELDS = frozenset(
    {
        "after_dependencies",
        "attempted_dependencies",
        "attempt_index",
        "baseline_formula_sha256",
        "baseline_root_body_certificate_sha256",
        "before_dependencies",
        "failure",
        "index",
        "layered_compiler_invoked",
        "name",
        "omitted_dependency",
        "outcome",
        "record_sha256",
        "route",
        "route_specific_assembly_reached",
        "script_sha256",
        "shared_root_body_observation_preimage",
        "shared_root_body_observation_sha256",
        "terminal_stage",
        "trial_surface",
    }
)
_VERIFICATION_THEOREM_FIELDS = frozenset(
    {
        "baseline_artifacts",
        "candidate_record_sha256",
        "index",
        "name",
        "producer_observation_route_record_count",
        "record_sha256",
        "unique_shared_root_body_observation_count",
    }
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_RELATIVE = Path(
    "training/peano_hydra/library-pilot-dependency-vector-audit-schema-v1.json"
)
_A21_RELATIVE = Path(
    "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
)
_A22_RELATIVE = Path(
    "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
)
_A23_RELATIVE = Path(
    "artifacts/peano-hydra/l0-optimizer-comparison-pilot-candidate-v1.json"
)
_A23_VERIFICATION_RELATIVE = Path(
    "artifacts/peano-hydra/"
    "l0-optimizer-comparison-pilot-independent-verification-v1.json"
)
_REPLAY_MANIFEST_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
_REPLAY_REPORT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)

PRODUCER_SOURCE_FILES = (
    (
        _SCHEMA_RELATIVE,
        21_875,
        "c4af0d2f850ad16fa7d4a3c086ad13356020a4ccb9a15e0d612babb8db690283",
    ),
    (
        Path("training/peano_hydra/library_pilot_dependency_vector_audit.py"),
        120_990,
        "3f2c9df051ce4271466b70bdf21ffd59d7ffc298905302d8b42946ca2c87804e",
    ),
    (
        Path("scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py"),
        24_509,
        "29f56547e6f228cf812df6c013670977de2088d2fccbb7da2fb64cda0ad7737a",
    ),
    (
        Path(
            "peano-lab/py/tests/"
            "test_peano_hydra_library_pilot_dependency_vector_audit.py"
        ),
        94_869,
        "6c3a0490b86ac2ae7aef3206c480fa14f6e15994106153788d79633fc3025d06",
    ),
)
SCHEMA_SEMANTIC_SHA256 = (
    "6782197c9925f5552aab030a11b996c157e2d06344a2d136d8babc1ee1fdc3df"
)
IMPLEMENTATION_SOURCE_ROOT_SHA256 = (
    "4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0"
)
CANDIDATE_BODY_COMPILER_SOURCE_SHA256 = (
    "b41e6587d32e27152e1358b3067c72b869357674548f05aa4ef5e86cf9bdc30a"
)

_FIXED_DOCUMENTS = {
    "a2.1_dependency_audit": (
        _A21_RELATIVE,
        "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040",
        "12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e",
        "8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784",
    ),
    "a2.2_construction_rebuild": (
        _A22_RELATIVE,
        "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182",
        "91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0",
        "42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5",
    ),
    "a2.3a_candidate": (
        _A23_RELATIVE,
        "3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b",
        "90a3d97a466dc7b1c9e6032b1b56b8ede3fcece8d56a4b39f2d4e5f34dbeb770",
        "4cfcbe22312ff2b92022189e65d3742bc096ba989dacaa82b2054e84282928e5",
    ),
    "a2.3a_verification": (
        _A23_VERIFICATION_RELATIVE,
        "6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a",
        "e21290f654c1a30e0bdf79e796a8ca1da6ad3aa6a1cb1d8ba34d3d376de052dc",
        "18f882717346477304285c9336d7b769ccf95cd1b58c32b65d335f3e8caa4188",
    ),
}
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

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA1_RE = re.compile(r"[0-9a-f]{40}")


class LibraryPilotDependencyVectorAuditVerificationError(ValueError):
    """The candidate, fixed evidence, or verification claim is invalid."""


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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "independent verifier runtime import boundary is contaminated"
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{path} exceeds the JSON depth limit"
        )
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{path} exceeds the safe integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{path} contains a Unicode surrogate"
            ) from exc
        return 1
    if type(value) not in (list, dict):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{path} contains a non-JSON value"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{path} contains a cycle"
        )
    branch = ancestors | {marker}
    count = 1
    iterator = enumerate(value) if type(value) is list else value.items()
    for key, item in iterator:
        if type(value) is dict and type(key) is not str:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{path} contains a non-string key"
            )
        count += _validate_json(
            item, path=f"{path}.{key}", depth=depth + 1, ancestors=branch
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot encode compact canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "compact canonical JSON exceeds its byte limit"
        )
    return raw


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256(_compact_json(value, limit=limit))


def canonical_verification_receipt_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return the sole retained canonical JSON representation."""

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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot encode canonical verification JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "canonical verification JSON exceeds its byte limit"
        )
    return raw


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
                raise LibraryPilotDependencyVectorAuditVerificationError(
                    f"{label} parent contains a link or non-directory component"
                )
        metadata = absolute.lstat()
    except LibraryPilotDependencyVectorAuditVerificationError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryPilotDependencyVectorAuditVerificationError(
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
        if len(raw) > limit or (
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
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{label} changed or exceeded its bound while read"
            )
        return raw
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot resolve repository_root"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def _require_fields(
    label: str, value: object, expected: frozenset[str] | set[str]
) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(expected):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} has the wrong fields"
        )
    return value


def _require_false_fields(
    label: str, value: Mapping[str, object], names: tuple[str, ...]
) -> None:
    for name in names:
        if value.get(name) is not False:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{label} field {name!r} must remain false"
            )


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not one lowercase SHA-256 string"
        )
    return value


def _record_hash(row: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: value for key, value in row.items() if key != "record_sha256"}
    )


def _lf_hash(names: tuple[str, ...]) -> str:
    return _sha256(
        ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    )


def _single_omission_vectors(
    dependencies: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if (
        type(dependencies) is not tuple
        or not all(type(item) is str and item for item in dependencies)
        or len(set(dependencies)) != len(dependencies)
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "direct dependency vector is malformed"
        )
    return tuple(
        (dependencies[index], dependencies[:index] + dependencies[index + 1 :])
        for index in range(len(dependencies) - 1, -1, -1)
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} artifact hash drifted"
        )
    value = _decode_document(raw, label, limit=limit)
    if canonical_verification_receipt_bytes(value, limit=limit) != raw:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not canonical"
        )
    return raw, value


def _require_kernel_sources(root: Path) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    modules: dict[str, object] = {}
    for module_name, relative, expected_hash in _KERNEL_SOURCES:
        raw = _safe_file(
            root / relative,
            label=f"kernel source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256(raw) != expected_hash:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"kernel source {relative.as_posix()!r} drifted"
            )
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", None)
        if type(source) is not str:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"cannot identify kernel module {module_name!r}"
            )
        try:
            actual = Path(source).resolve(strict=True)
            expected = (root / relative).resolve(strict=True)
        except OSError as exc:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"cannot resolve kernel module {module_name!r}"
            ) from exc
        if actual != expected:
            raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "captured kernel callable or class identity drifted"
        )
    return identities


def _rows_by_name(
    document: Mapping[str, object], label: str, *, expected_count: int
) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list or len(rows) != expected_count:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"{label} theorem order is malformed"
            )
        previous = row["index"]
        result[row["name"]] = row
    return result


def _load_fixed_inputs(root: Path) -> dict[str, object]:
    schema_raw, schema = _load_canonical_json(
        root / _SCHEMA_RELATIVE,
        label="A2.3b producer schema",
        limit=MAX_SCHEMA_BYTES,
        expected_sha256=PRODUCER_SOURCE_FILES[0][2],
    )
    if (
        _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != SCHEMA_SEMANTIC_SHA256
        or schema.get("format")
        != "peano-hydra-library-pilot-dependency-vector-audit-schema"
        or schema.get("id")
        != "peano-hydra-library-pilot-dependency-vector-audit-v1"
        or schema.get("v") != 1
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b producer schema semantic identity drifted"
        )
    for relative, size, digest in PRODUCER_SOURCE_FILES:
        raw = _safe_file(
            root / relative,
            label=f"A2.3b producer source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != size or _sha256(raw) != digest:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"A2.3b producer source {relative.as_posix()!r} drifted"
            )
    implementation_rows = schema.get("implementation_sources")
    if (
        type(implementation_rows) is not list
        or len(implementation_rows) != 44
        or schema.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or _sha256_json(implementation_rows, limit=MAX_SCHEMA_BYTES)
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b implementation source vector drifted"
        )
    seen: set[str] = set()
    for row in implementation_rows:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "A2.3b implementation source row is malformed"
            )
        path_text = row.get("path")
        digest = row.get("sha256")
        if (
            type(path_text) is not str
            or path_text in seen
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "A2.3b implementation source identity is malformed"
            )
        relative = Path(path_text)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
            or relative.as_posix() != path_text
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "A2.3b implementation source path is unsafe"
            )
        seen.add(path_text)
        raw = _safe_file(
            root / relative,
            label=f"A2.3b implementation source {path_text!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256(raw) != digest:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"A2.3b implementation source {path_text!r} drifted"
            )

    loaded: dict[str, dict[str, object]] = {}
    for label, (relative, artifact_sha, root_sha, records_sha) in (
        _FIXED_DOCUMENTS.items()
    ):
        _raw, document = _load_canonical_json(
            root / relative,
            label=f"fixed {label}",
            limit=MAX_DOCUMENT_BYTES,
            expected_sha256=artifact_sha,
        )
        theorem_count = 384 if label == "a2.1_dependency_audit" else 3
        if (
            document.get("root_sha256") != root_sha
            or document.get("theorem_count") != theorem_count
            or type(document.get("theorem_records")) is not dict
            or document["theorem_records"].get("root_sha256") != records_sha
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"fixed {label} semantic root drifted"
            )
        loaded[label] = document

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
        manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != 384
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "fixed replay manifest semantic root drifted"
        )
    a23 = loaded["a2.3a_candidate"]
    a23_verification = loaded["a2.3a_verification"]
    if (
        a23_verification.get("status") != "passed"
        or a23_verification.get("candidate_status") != "candidate"
        or a23_verification.get("kernel_artifacts_verified") is not True
        or a23_verification.get("candidate", {}).get("artifact_sha256")
        != _FIXED_DOCUMENTS["a2.3a_candidate"][1]
        or a23_verification.get("candidate", {}).get("root_sha256")
        != a23.get("root_sha256")
        or a23_verification.get("candidate", {}).get(
            "theorem_record_root_sha256"
        )
        != a23.get("theorem_records", {}).get("root_sha256")
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "fixed A2.3a candidate/verification join drifted"
        )

    a21_rows = _rows_by_name(
        loaded["a2.1_dependency_audit"], "A2.1", expected_count=384
    )
    a22_rows = _rows_by_name(
        loaded["a2.2_construction_rebuild"], "A2.2", expected_count=3
    )
    a23_rows = _rows_by_name(a23, "A2.3a", expected_count=3)
    replay_rows = _rows_by_name(manifest, "replay manifest", expected_count=384)
    if tuple((row["index"], row["name"]) for row in a22_rows.values()) != (
        EXPECTED_THEOREMS
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "fixed A2.2 theorem set drifted"
        )
    return {
        **loaded,
        "a21_rows": a21_rows,
        "a22_rows": a22_rows,
        "a23_rows": a23_rows,
        "implementation_rows": deepcopy(implementation_rows),
        "kernel_sources": _require_kernel_sources(root),
        "manifest": manifest,
        "replay_rows": replay_rows,
        "schema": schema,
        "schema_artifact_sha256": _sha256(schema_raw),
    }


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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer source-state identity is malformed"
        )
    source_rows = state.get("files")
    if type(source_rows) is not list or len(source_rows) != len(
        PRODUCER_SOURCE_FILES
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer source-state file vector differs"
        )
    for row, (relative, size, digest) in zip(
        source_rows, PRODUCER_SOURCE_FILES, strict=True
    ):
        if type(row) is not dict or row != {
            "bytes": size,
            "path": relative.as_posix(),
            "sha256": digest,
        }:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "producer source state does not bind the four frozen sources"
            )
        raw = _safe_file(
            root / relative,
            label=f"producer source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != size or _sha256(raw) != digest:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"live producer source {relative.as_posix()!r} drifted"
            )
    payload = {
        key: item
        for key, item in state.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": 1,
    }
    if (
        state.get("root_preimage") != preimage
        or state.get("root_sha256")
        != _sha256_json(preimage, limit=MAX_SCHEMA_BYTES)
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer source-state root is malformed"
        )
    return deepcopy(state)


def _decode_base64(value: object, *, label: str) -> bytes:
    maximum = 4 * ((MAX_ARTIFACT_BYTES + 2) // 3)
    if type(value) is not str or not value or len(value) > maximum:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not bounded base64"
        )
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not canonical base64"
        ) from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not canonical base64"
        )
    return raw


def _proof_tree_metrics(proof: Proof) -> dict[str, int]:
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
            raise LibraryPilotDependencyVectorAuditVerificationError(
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
    expected_artifact_sha256: str,
    expected_fuel: int,
    expected_formula_sha256: str,
    expected_proof_sha256: str,
) -> tuple[Formula, dict[str, object]]:
    if type(raw) is not bytes or not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} is not bounded artifact bytes"
        )
    if _sha256(raw) != expected_artifact_sha256:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
        formula_sha = _sha256(encode_formula(target))
        proof_sha = _sha256(encode_proof(proof))
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"cannot canonically decode {label}"
        ) from exc
    if (
        canonical != raw
        or type(fuel) is not int
        or fuel != expected_fuel
        or formula_sha != expected_formula_sha256
        or proof_sha != expected_proof_sha256
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{label} canonical identity differs"
        )
    try:
        accepted = check((), proof, target)
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"kernel checking {label} failed closed"
        ) from exc
    if accepted is not True:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"kernel rejected {label} from the empty context"
        )
    metrics = _proof_tree_metrics(proof)
    metrics["artifact_bytes"] = len(raw)
    return target, {
        "artifact_sha256": expected_artifact_sha256,
        "formula_sha256": formula_sha,
        "fuel": fuel,
        "kernel_accepted": True,
        "kernel_context": "empty",
        "metrics": metrics,
        "proof_term_sha256": proof_sha,
    }


def _closure(
    root_name: str,
    direct_dependencies: tuple[str, ...],
    *,
    replay_rows: Mapping[str, dict[str, object]],
    fixed_vectors: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if root_name not in replay_rows:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"unknown closure root {root_name!r}"
        )
    _single_omission_vectors(direct_dependencies)
    overrides = dict(fixed_vectors)
    overrides[root_name] = direct_dependencies
    pending = list(direct_dependencies)
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = replay_rows.get(name)
        if row is None:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"closure contains unknown theorem {name!r}"
            )
        dependencies = overrides.get(
            name, tuple(row.get("declared_dependencies", ()))
        )
        if (
            type(dependencies) is not tuple
            or not all(type(item) is str and item for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"dependency vector for {name!r} is malformed"
            )
        seen.add(name)
        pending.extend(dependencies)
    if root_name in seen:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"closure for {root_name!r} contains its root"
        )
    return tuple(sorted(seen, key=lambda name: replay_rows[name]["index"]))


def _surface(
    dependencies: tuple[str, ...], closure: tuple[str, ...], *, basis: str
) -> dict[str, object]:
    return {
        "direct_dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": _lf_hash(dependencies),
        "direct_dependency_count": len(dependencies),
        "surface_basis": basis,
        "transitive_closure_count": len(closure),
        "transitive_closure_dependencies_in_replay_order": list(closure),
        "transitive_closure_lf_sha256": _lf_hash(closure),
    }


def _expected_root_body_receipt(
    rebuild_row: Mapping[str, object], replay_row: Mapping[str, object]
) -> dict[str, object]:
    body = rebuild_row.get("body_receipt")
    metrics = None if type(body) is not dict else body.get("metrics")
    script = replay_row.get("script")
    if (
        type(body) is not dict
        or type(metrics) is not dict
        or type(script) is not list
        or body.get("kernel_accepted") is not True
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "fixed A2.2 root-body receipt is malformed"
        )
    return {
        "certificate_sha256": body["certificate_sha256"],
        "command_count": len(script),
        "dependency_count": body["dependency_count"],
        "proof_depth": metrics["proof_depth"],
        "proof_edges": metrics["proof_edges"],
        "proof_nodes": metrics["proof_nodes"],
        "proof_objects": metrics["proof_objects"],
        "reused_objects": metrics["reused_objects"],
        "target_formula_sha256": body["target_formula_sha256"],
    }


def _baseline_artifact_observations(
    *,
    name: str,
    a22_row: Mapping[str, object],
    a23_row: Mapping[str, object],
    replay_row: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    rebuild = a22_row.get("rebuilt_certificate")
    if type(rebuild) is not dict:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fixed A2.2 artifact for {name!r} is malformed"
        )
    readable_raw = _decode_base64(
        rebuild.get("artifact_base64"), label=f"A2.2 artifact for {name!r}"
    )
    if (
        len(readable_raw) != rebuild.get("artifact_bytes")
        or rebuild.get("formula_sha256") != replay_row.get("formula_sha256")
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fixed A2.2 artifact metadata for {name!r} differs"
        )
    _readable_target, readable = _inspect_artifact(
        readable_raw,
        label=f"{name}:readable-baseline",
        expected_artifact_sha256=rebuild["artifact_sha256"],
        expected_fuel=rebuild["fuel"],
        expected_formula_sha256=replay_row["formula_sha256"],
        expected_proof_sha256=rebuild["proof_term_sha256"],
    )
    layered = next(
        (
            row
            for row in a23_row.get("artifacts", ())
            if type(row) is dict and row.get("candidate_id") == "layered-closure"
        ),
        None,
    )
    if type(layered) is not dict:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fixed A2.3a layered artifact for {name!r} is malformed"
        )
    layered_raw = _decode_base64(
        layered.get("artifact_base64"),
        label=f"A2.3a layered artifact for {name!r}",
    )
    _layered_target, layered_observation = _inspect_artifact(
        layered_raw,
        label=f"{name}:layered-baseline",
        expected_artifact_sha256=layered["artifact_sha256"],
        expected_fuel=layered["fuel"],
        expected_formula_sha256=replay_row["formula_sha256"],
        expected_proof_sha256=layered["proof_term_sha256"],
    )
    return {
        READABLE_ROUTE: readable,
        LAYERED_ROUTE: layered_observation,
    }


def _expected_inputs() -> dict[str, object]:
    result: dict[str, object] = {
        label: {
            "artifact_path": relative.as_posix(),
            "artifact_sha256": artifact_sha,
            "root_sha256": root_sha,
            "theorem_record_root_sha256": records_sha,
        }
        for label, (relative, artifact_sha, root_sha, records_sha) in (
            _FIXED_DOCUMENTS.items()
        )
    }
    result["replay"] = {
        "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
        "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
        "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
    }
    return result


def _expected_live_theorem_transport(
    replay_rows: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    if len(replay_rows) != 384:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "replay theorem transport count differs"
        )
    records: list[dict[str, object]] = []
    for position, row in enumerate(replay_rows.values()):
        if row.get("index") != position:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "replay theorem transport order differs"
            )
        dependencies = row.get("declared_dependencies")
        script = row.get("script")
        summary = row.get("summary")
        if (
            type(dependencies) is not list
            or not all(type(item) is str for item in dependencies)
            or type(script) is not list
            or not all(type(item) is str for item in script)
            or type(summary) is not str
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "replay theorem transport row is malformed"
            )
        records.append(
            {
                "declared_dependencies": dependencies,
                "formula_sha256": row["formula_sha256"],
                "index": position,
                "name": row["name"],
                "script_sha256": _lf_hash(tuple(script)),
                "statement_canonical_sha256": row[
                    "statement_canonical_sha256"
                ],
                "statement_source_sha256": row["statement_source_sha256"],
                "summary_sha256": _sha256(summary.encode("utf-8")),
            }
        )
    preimage = {
        "format": "peano-hydra-live-theorem-transport-preimage",
        "records": records,
        "v": 1,
    }
    return {
        "count": 384,
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "status": "exact-live-spec-to-retained-replay-transport",
    }


def _expected_callable_limits_identity(
    schema: Mapping[str, object],
) -> dict[str, object]:
    preimage = {
        "artifact_decode_limits": schema["artifact_decode_limits"],
        "artifact_encode_max_bytes": schema["artifact_encode_max_bytes"],
        "expected_attempt_count": schema["expected_attempt_count"],
        "expected_roots": schema["expected_roots"],
        "format": "peano-hydra-pilot-vector-audit-callable-limits-preimage",
        "fuel_policy": schema["fuel_policy"],
        "implementation_source_root_sha256": IMPLEMENTATION_SOURCE_ROOT_SHA256,
        "layered_replay_limits": schema["layered_replay_limits"],
        "qualified_callables": schema["qualified_callables"],
        "v": 1,
    }
    return {"preimage": preimage, "sha256": _sha256_json(preimage)}


def _verify_implementation(
    value: object,
    *,
    schema: Mapping[str, object],
    implementation_rows: list[dict[str, object]],
    replay_rows: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    implementation = _require_fields(
        "candidate implementation",
        value,
        {
            "callable_limits_identity",
            "live_theorem_transport",
            "source_root_sha256",
            "sources",
        },
    )
    expected_callable = _expected_callable_limits_identity(schema)
    expected_transport = _expected_live_theorem_transport(replay_rows)
    if implementation != {
        "callable_limits_identity": expected_callable,
        "live_theorem_transport": expected_transport,
        "source_root_sha256": IMPLEMENTATION_SOURCE_ROOT_SHA256,
        "sources": implementation_rows,
    }:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate implementation identity differs"
        )
    return expected_callable


def _proof_receipt_from_observation(
    observation: Mapping[str, object]
) -> dict[str, object]:
    metrics = observation.get("metrics")
    if type(metrics) is not dict or set(metrics) != {
        "artifact_bytes",
        "cut_nodes",
        "proof_depth",
        "proof_nodes",
    }:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "independent baseline metrics are malformed"
        )
    return {
        "formula_sha256": observation["formula_sha256"],
        "kernel_accepted": True,
        "kernel_context": "empty",
        "logic_mode": LOGIC_MODE,
        "metrics": {
            "cut_nodes": metrics["cut_nodes"],
            "proof_depth": metrics["proof_depth"],
            "proof_nodes": metrics["proof_nodes"],
        },
        "proof_term_sha256": observation["proof_term_sha256"],
    }


def _expected_readable_diagnostics(
    *,
    dependencies: tuple[str, ...],
    replay_rows: Mapping[str, dict[str, object]],
    root_body_receipt: Mapping[str, object],
) -> dict[str, object]:
    certificate_rows = [
        {
            "formula_sha256": replay_rows[name]["formula_sha256"],
            "name": name,
            "proof_term_sha256": replay_rows[name]["proof_term_sha256"],
        }
        for name in dependencies
    ]
    preimage = {
        "format": "peano-hydra-readable-direct-certificate-provenance-preimage",
        "records": certificate_rows,
        "v": 1,
    }
    return {
        "assembly": "compile_candidate_body-then-compile_closed_candidate",
        "direct_certificate_count": len(certificate_rows),
        "direct_certificate_provenance_preimage": preimage,
        "direct_certificate_provenance_root_sha256": _sha256_json(
            preimage, limit=MAX_SCHEMA_BYTES
        ),
        "root_body_receipt": deepcopy(dict(root_body_receipt)),
    }


def _expected_layered_diagnostics(
    *,
    name: str,
    dependencies: tuple[str, ...],
    closure: tuple[str, ...],
    root_body_receipt: Mapping[str, object],
    a23_row: Mapping[str, object],
) -> dict[str, object]:
    layered = next(
        (
            row
            for row in a23_row.get("artifacts", ())
            if type(row) is dict and row.get("candidate_id") == "layered-closure"
        ),
        None,
    )
    bundle = a23_row.get("layered_bundle")
    if type(layered) is not dict or type(bundle) is not dict:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fixed A2.3a layered evidence for {name!r} is malformed"
        )
    retained_sources = bundle.get("body_sources")
    node_names = tuple(bundle.get("node_names_in_replay_order", ()))
    if (
        type(retained_sources) is not list
        or len(retained_sources) != len(node_names)
        or node_names != (*closure, name)
        or not retained_sources
        or retained_sources[-1].get("name") != name
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fixed A2.3a body-source transport for {name!r} differs"
        )
    root_source = {
        "body_certificate_sha256": root_body_receipt["certificate_sha256"],
        "dependencies": list(dependencies),
        "formula_sha256": layered["formula_sha256"],
        "index": a23_row["index"],
        "kind": "fresh-root-candidate-body",
        "name": name,
        "root_body_receipt": deepcopy(dict(root_body_receipt)),
    }
    fresh_sources = [*deepcopy(retained_sources[:-1]), root_source]
    identities = [
        {
            "body_certificate_sha256": source["body_certificate_sha256"],
            "dependencies": source["dependencies"],
            "index": source["index"],
            "name": source["name"],
        }
        for source in fresh_sources
    ]
    retained_identities = [
        {
            "body_certificate_sha256": source["body_certificate_sha256"],
            "dependencies": source["dependencies"],
            "index": source["index"],
            "name": source["name"],
        }
        for source in retained_sources
    ]
    if identities != retained_identities:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"fresh/retained stable body identities for {name!r} differ"
        )
    identity_preimage = {
        "format": "peano-hydra-layered-modular-body-identities-preimage",
        "records": identities,
        "v": 1,
    }
    provenance_preimage = {
        "format": "peano-hydra-layered-modular-provenance-preimage",
        "records": fresh_sources,
        "v": 1,
    }
    retained_sources_preimage = {
        "format": "peano-hydra-a2.3a-layered-body-sources-preimage",
        "records": retained_sources,
        "v": 1,
    }
    stable_fields = [
        "body_certificate_sha256",
        "dependencies",
        "index",
        "name",
    ]
    stable_join_preimage = {
        "format": "peano-hydra-fresh-retained-stable-body-identity-join-preimage",
        "records": [
            {"fresh": fresh, "retained": retained}
            for fresh, retained in zip(
                identities, retained_identities, strict=True
            )
        ],
        "stable_fields": stable_fields,
        "v": 1,
    }
    provenance_root = _sha256_json(provenance_preimage)
    identity_root = _sha256_json(identity_preimage)
    retained_sources_root = _sha256_json(retained_sources_preimage)
    parity = {
        "a2_3a_body_sources_preimage": retained_sources_preimage,
        "a2_3a_body_sources_root_sha256": retained_sources_root,
        "a2_3a_candidate_record_sha256": a23_row["record_sha256"],
        "a2_3a_layered_artifact_sha256": layered["artifact_sha256"],
        "fresh_body_provenance_root_sha256": provenance_root,
        "retained_body_sources_root_sha256": retained_sources_root,
        "stable_body_identity_fields": stable_fields,
        "stable_body_identity_join_preimage": stable_join_preimage,
        "stable_body_identity_join_root_sha256": _sha256_json(
            stable_join_preimage
        ),
        "stable_body_identity_root_sha256": identity_root,
        "status": (
            "exact-candidate-and-stable-body-identity-parity-with-distinct-"
            "provenance"
        ),
    }
    return {
        "artifact_bytes": layered["metrics"]["artifact_bytes"],
        "artifact_sha256": layered["artifact_sha256"],
        "assembly": (
            "fresh-root-then-single-root-vector-override-with-fixed-a2.2-"
            "nonroot-vectors-then-layered-replay"
        ),
        "candidate_formula_sha256": layered["formula_sha256"],
        "candidate_metrics": layered["metrics"],
        "candidate_proof_term_sha256": layered["proof_term_sha256"],
        "compiler_result_type": bundle["compiler_result_type"],
        "dependency_edge_count": bundle["dependency_edge_count"],
        "fresh_body_sources": fresh_sources,
        "fuel": layered["fuel"],
        "layer_count": bundle["layer_count"],
        "layers": bundle["layers"],
        "maximum_package_formula_depth": bundle[
            "maximum_package_formula_depth"
        ],
        "modular_body_count": len(fresh_sources),
        "modular_body_identity_preimage": identity_preimage,
        "modular_body_identity_root_sha256": identity_root,
        "modular_body_provenance_preimage": provenance_preimage,
        "modular_body_provenance_root_sha256": provenance_root,
        "node_count": bundle["node_count"],
        "node_names_in_replay_order": bundle["node_names_in_replay_order"],
        "node_names_lf_sha256": bundle["node_names_lf_sha256"],
        "package_formula_occurrences": bundle[
            "package_formula_occurrences"
        ],
        "retained_baseline_parity": parity,
        "root_body_receipt": deepcopy(dict(root_body_receipt)),
    }


def _verify_baseline(
    value: object,
    *,
    route: str,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    closure: tuple[str, ...],
    diagnostics: Mapping[str, object],
    observation: Mapping[str, object],
) -> dict[str, object]:
    baseline = _require_fields("route baseline", value, _BASELINE_FIELDS)
    basis = (
        "readable-literal-direct-cut-closure"
        if route == READABLE_ROUTE
        else "proposed-layered-root-input-graph-not-final-cut-spine"
    )
    expected_surface = _surface(dependencies, closure, basis=basis)
    expected_proof = _proof_receipt_from_observation(observation)
    expected_preimage = {
        "diagnostics": diagnostics,
        "format": BASELINE_RECEIPT_PREIMAGE_FORMAT,
        "index": index,
        "name": name,
        "proof": expected_proof,
        "route": route,
        "surface": expected_surface,
        "v": 1,
    }
    expected = {
        "diagnostics": diagnostics,
        "preimage": expected_preimage,
        "proof": expected_proof,
        "sha256": _sha256_json(expected_preimage),
        "status": "kernel-accepted-baseline",
        "surface": expected_surface,
    }
    if baseline != expected:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{route} baseline receipt for {name!r} differs from independently "
            "checked upstream artifact"
        )
    return expected


def _verify_failure(value: object, *, script: tuple[str, ...]) -> dict[str, object]:
    failure = _require_fields(
        "producer rejection classification",
        value,
        {"cause_type", "command", "command_index", "kind", "phase"},
    )
    if failure.get("kind") != "exact-recipe-rejection":
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer rejection kind differs"
        )
    phase = failure.get("phase")
    if phase == "command":
        command_index = failure.get("command_index")
        command = failure.get("command")
        if (
            failure.get("cause_type") != "TacticError"
            or type(command_index) is not int
            or command_index < 0
            or command_index >= len(script)
            or type(command) is not str
            or not command
            or script[command_index] != command
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "producer command rejection is not bound to the frozen script"
            )
    elif phase == "finalization":
        if (
            failure.get("command") is not None
            or failure.get("command_index") is not None
            or failure.get("cause_type")
            not in (None, "InvalidProof", "ProofReductionError")
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "producer finalization rejection classification differs"
            )
    else:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer rejection phase is not allowlisted"
        )
    return deepcopy(failure)


def _verify_attempt(
    value: object,
    *,
    route: str,
    name: str,
    index: int,
    attempt_index: int,
    omitted_dependency: str,
    candidate_dependencies: tuple[str, ...],
    full_dependencies: tuple[str, ...],
    script: tuple[str, ...],
    closure: tuple[str, ...],
    baseline_formula_sha256: str,
    baseline_root_body_sha256: str,
) -> dict[str, object]:
    attempt = _require_fields(
        f"{route} attempt {attempt_index}", value, _REJECTED_ATTEMPT_FIELDS
    )
    failure = _verify_failure(attempt.get("failure"), script=script)
    shared_preimage = {
        "candidate_body_compiler_source_sha256": (
            CANDIDATE_BODY_COMPILER_SOURCE_SHA256
        ),
        "dependencies": list(candidate_dependencies),
        "failure": failure,
        "format": "peano-hydra-shared-root-body-observation-preimage",
        "index": index,
        "name": name,
        "v": 1,
    }
    basis = (
        "readable-literal-direct-cut-closure"
        if route == READABLE_ROUTE
        else "proposed-layered-root-input-graph-not-final-cut-spine"
    )
    expected = {
        "after_dependencies": list(full_dependencies),
        "attempted_dependencies": list(candidate_dependencies),
        "attempt_index": attempt_index,
        "baseline_formula_sha256": baseline_formula_sha256,
        "baseline_root_body_certificate_sha256": baseline_root_body_sha256,
        "before_dependencies": list(full_dependencies),
        "failure": failure,
        "index": index,
        "layered_compiler_invoked": False,
        "name": name,
        "omitted_dependency": omitted_dependency,
        "outcome": "exact-route-rejected",
        "route": route,
        "route_specific_assembly_reached": False,
        "script_sha256": _lf_hash(script),
        "shared_root_body_observation_preimage": shared_preimage,
        "shared_root_body_observation_sha256": _sha256_json(
            shared_preimage, limit=MAX_SCHEMA_BYTES
        ),
        "terminal_stage": "root-body-regeneration",
        "trial_surface": _surface(candidate_dependencies, closure, basis=basis),
    }
    expected["record_sha256"] = _record_hash(expected)
    if attempt != expected:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{route} attempt {attempt_index} for {name!r} differs"
        )
    return expected


def _verify_route(
    value: object,
    *,
    route: str,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    fixed_vectors: Mapping[str, tuple[str, ...]],
    replay_rows: Mapping[str, dict[str, object]],
    diagnostics: Mapping[str, object],
    observation: Mapping[str, object],
    producer_source_state_root_sha256: str,
    callable_limits_sha256: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    record = _require_fields(f"{route} route", value, _ROUTE_FIELDS)
    baseline_closure = _closure(
        name,
        dependencies,
        replay_rows=replay_rows,
        fixed_vectors=fixed_vectors,
    )
    baseline = _verify_baseline(
        record.get("baseline"),
        route=route,
        name=name,
        index=index,
        dependencies=dependencies,
        closure=baseline_closure,
        diagnostics=diagnostics,
        observation=observation,
    )
    attempts = record.get("attempts")
    omission_vectors = _single_omission_vectors(dependencies)
    if type(attempts) is not list or len(attempts) != len(omission_vectors):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{route} attempt vector for {name!r} differs"
        )
    verified_attempts: list[dict[str, object]] = []
    for attempt_index, ((omitted, candidate), attempt) in enumerate(
        zip(omission_vectors, attempts, strict=True)
    ):
        closure = _closure(
            name,
            candidate,
            replay_rows=replay_rows,
            fixed_vectors=fixed_vectors,
        )
        verified_attempts.append(
            _verify_attempt(
                attempt,
                route=route,
                name=name,
                index=index,
                attempt_index=attempt_index,
                omitted_dependency=omitted,
                candidate_dependencies=candidate,
                full_dependencies=dependencies,
                script=script,
                closure=closure,
                baseline_formula_sha256=baseline["proof"]["formula_sha256"],
                baseline_root_body_sha256=baseline["diagnostics"][
                    "root_body_receipt"
                ]["certificate_sha256"],
            )
        )
    identities = [
        {
            "attempt_index": attempt["attempt_index"],
            "omitted_dependency": attempt["omitted_dependency"],
            "record_sha256": attempt["record_sha256"],
        }
        for attempt in verified_attempts
    ]
    attempts_preimage = {
        "format": ATTEMPT_RECORDS_PREIMAGE_FORMAT,
        "name": name,
        "records": identities,
        "route": route,
        "v": 1,
    }
    attempts_bundle = {
        "count": len(verified_attempts),
        "preimage": attempts_preimage,
        "root_sha256": _sha256_json(attempts_preimage),
    }
    if record.get("attempt_records") != attempts_bundle:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{route} attempt-record root for {name!r} differs"
        )
    route_preimage = {
        "attempts_root_sha256": attempts_bundle["root_sha256"],
        "baseline_closure_lf_sha256": baseline["surface"][
            "transitive_closure_lf_sha256"
        ],
        "baseline_receipt_sha256": baseline["sha256"],
        "callable_limits_sha256": callable_limits_sha256,
        "dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": baseline["surface"][
            "direct_dependencies_lf_sha256"
        ],
        "format": ROUTE_RECEIPT_PREIMAGE_FORMAT,
        "formula_sha256": baseline["proof"]["formula_sha256"],
        "implementation_source_root_sha256": (
            IMPLEMENTATION_SOURCE_ROOT_SHA256
        ),
        "index": index,
        "name": name,
        "producer_source_state_root_sha256": (
            producer_source_state_root_sha256
        ),
        "root_body_certificate_sha256": baseline["diagnostics"][
            "root_body_receipt"
        ]["certificate_sha256"],
        "route": route,
        "v": 1,
    }
    expected = {
        "attempt_records": attempts_bundle,
        "attempts": verified_attempts,
        "baseline": baseline,
        "route": route,
        "route_receipt_preimage": route_preimage,
        "route_receipt_sha256": _sha256_json(route_preimage),
        "single_omission_kernel_accepted_count": 0,
        "single_omission_rejected_count": len(verified_attempts),
        "status": "bounded-route-audit-complete",
    }
    if record != expected:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            f"{route} receipt for {name!r} differs"
        )
    return expected, verified_attempts


def _verify_shared_route_pairing(
    readable: list[dict[str, object]],
    layered: list[dict[str, object]],
    *,
    baseline_root_body_receipt: Mapping[str, object],
    recorded: object,
) -> tuple[dict[str, object], set[str]]:
    if len(readable) != len(layered):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cross-route attempt counts differ"
        )
    unique: set[str] = set()
    for first, second in zip(readable, layered, strict=True):
        if (
            first["attempt_index"] != second["attempt_index"]
            or first["omitted_dependency"] != second["omitted_dependency"]
            or first["attempted_dependencies"]
            != second["attempted_dependencies"]
            or first["failure"] != second["failure"]
            or first["shared_root_body_observation_preimage"]
            != second["shared_root_body_observation_preimage"]
            or first["shared_root_body_observation_sha256"]
            != second["shared_root_body_observation_sha256"]
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "cross-route shared root-body observation pairing differs"
            )
        unique.add(first["shared_root_body_observation_sha256"])
    baseline_preimage = {
        "format": "peano-hydra-cross-route-shared-baseline-body-preimage",
        "root_body_receipt": baseline_root_body_receipt,
        "v": 1,
    }
    expected = {
        "baseline_root_body_receipt_sha256": _sha256_json(
            baseline_preimage
        ),
        "paired_attempt_count": len(readable),
        "status": "shared-root-body-consistent",
    }
    if recorded != expected or len(unique) != len(readable):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cross-route shared-body consistency receipt differs"
        )
    return expected, unique


def verify_pilot_dependency_vector_audit(
    candidate: object,
    *,
    producer_source_state: object,
    candidate_raw: bytes | None = None,
    producer_source_state_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Verify one canonical A2.3b result under the honest split boundary."""

    _require_runtime_import_boundary()
    root = _repository_root(repository_root)
    fixed = _load_fixed_inputs(root)
    if type(candidate) is not dict:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "pilot dependency-vector audit candidate must be one object"
        )
    _validate_json(candidate)
    canonical_candidate = canonical_verification_receipt_bytes(candidate)
    if candidate_raw is None:
        candidate_raw = canonical_candidate
    elif type(candidate_raw) is not bytes or candidate_raw != canonical_candidate:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate transport bytes are not canonical"
        )

    source_state = _validate_producer_source_state(
        producer_source_state, root=root
    )
    canonical_source_state = canonical_verification_receipt_bytes(
        source_state, limit=MAX_SCHEMA_BYTES
    )
    if producer_source_state_raw is None:
        producer_source_state_raw = canonical_source_state
    elif (
        type(producer_source_state_raw) is not bytes
        or producer_source_state_raw != canonical_source_state
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "producer source-state transport bytes are not canonical"
        )

    document = _require_fields(
        "A2.3b candidate root",
        candidate,
        {
            *_CANDIDATE_ROOT_BODY_FIELDS,
            "root_preimage",
            "root_sha256",
            "theorems",
        },
    )
    _require_false_fields("A2.3b candidate root", document, GLOBAL_FALSE_FIELDS)
    if (
        document.get("format") != CANDIDATE_FORMAT
        or document.get("id") != CANDIDATE_ID
        or document.get("v") != CANDIDATE_VERSION
        or document.get("logic_mode") != LOGIC_MODE
        or document.get("status") != CANDIDATE_STATUS
        or document.get("theorem_count") != len(EXPECTED_THEOREMS)
        or document.get("producer_git_verified") is not False
        or document.get("bounded_three_root_protocol_frozen") is not True
        or document.get("bounded_protocol_executed") is not True
        or document.get("bounded_three_root_vector_audit_complete") is not False
        or document.get("single_omission_terminal_count")
        != EXPECTED_ATTEMPT_COUNT
        or document.get("terminal_route_observations_complete") is not True
        or document.get("producer_source_state") != source_state
        or document.get("producer_source_state_sha256")
        != _sha256_json(source_state, limit=MAX_SCHEMA_BYTES)
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b candidate root identity or claim boundary differs"
        )
    expected_schema_identity = {
        "artifact_sha256": PRODUCER_SOURCE_FILES[0][2],
        "format": (
            "peano-hydra-library-pilot-dependency-vector-audit-schema"
        ),
        "id": "peano-hydra-library-pilot-dependency-vector-audit-v1",
        "sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    if document.get("schema") != expected_schema_identity:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b candidate schema identity differs"
        )
    if document.get("inputs") != _expected_inputs():
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b candidate fixed-input identity differs"
        )
    callable_limits = _verify_implementation(
        document.get("implementation"),
        schema=fixed["schema"],
        implementation_rows=fixed["implementation_rows"],
        replay_rows=fixed["replay_rows"],
    )

    a21_rows = fixed["a21_rows"]
    a22_rows = fixed["a22_rows"]
    a23_rows = fixed["a23_rows"]
    replay_rows = fixed["replay_rows"]
    readable_fixed_vectors = {
        name: tuple(row["readable"]["dependencies"])
        for name, row in a21_rows.items()
    }
    layered_fixed_vectors = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in a22_rows.items()
    }
    result_rows = document.get("theorems")
    if type(result_rows) is not list or len(result_rows) != len(
        EXPECTED_THEOREMS
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b candidate theorem list differs"
        )

    verification_rows: list[dict[str, object]] = []
    candidate_record_identities: list[dict[str, object]] = []
    verification_record_identities: list[dict[str, object]] = []
    all_shared_observations: set[str] = set()
    route_record_count = 0

    for (index, name), row in zip(
        EXPECTED_THEOREMS, result_rows, strict=True
    ):
        theorem = _require_fields(
            f"A2.3b theorem {name!r}", row, _THEOREM_FIELDS
        )
        _require_false_fields(
            f"A2.3b theorem {name!r}", theorem, GLOBAL_FALSE_FIELDS
        )
        if theorem.get("index") != index or theorem.get("name") != name:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "A2.3b theorem identity/order differs"
            )
        replay_row = replay_rows.get(name)
        a21_row = a21_rows.get(name)
        a22_row = a22_rows.get(name)
        a23_row = a23_rows.get(name)
        if not all(
            type(item) is dict
            for item in (replay_row, a21_row, a22_row, a23_row)
        ) or any(
            item.get("index") != index
            for item in (replay_row, a21_row, a22_row, a23_row)
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"fixed theorem evidence join for {name!r} differs"
            )
        dependencies = EXPECTED_DIRECT[name]
        layered_artifact = next(
            (
                artifact
                for artifact in a23_row.get("artifacts", ())
                if type(artifact) is dict
                and artifact.get("candidate_id") == "layered-closure"
            ),
            None,
        )
        if (
            tuple(a21_row.get("readable", {}).get("dependencies", ()))
            != dependencies
            or tuple(a22_row.get("candidate_direct_dependencies", ()))
            != dependencies
            or type(layered_artifact) is not dict
            or tuple(
                layered_artifact.get("surface", {}).get(
                    "direct_dependencies", ()
                )
            )
            != dependencies
            or layered_artifact.get("surface", {}).get(
                "transitive_closure_count"
            )
            != EXPECTED_CLOSURE_COUNTS[name]
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"fixed dependency-vector join for {name!r} differs"
            )
        script_value = replay_row.get("script")
        if type(script_value) is not list or not all(
            type(item) is str for item in script_value
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"fixed script for {name!r} is malformed"
            )
        script = tuple(script_value)
        expected_statement = {
            "formula_sha256": replay_row["formula_sha256"],
            "statement_canonical_sha256": replay_row[
                "statement_canonical_sha256"
            ],
            "statement_source_sha256": replay_row["statement_source_sha256"],
        }
        if theorem.get("statement") != expected_statement:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"statement identity for {name!r} differs"
            )
        expected_union_preimage = {
            "format": "peano-hydra-bounded-local-dependency-union-preimage",
            "index": index,
            "name": name,
            "proposed_layered_dependencies": list(dependencies),
            "readable_dependencies": list(dependencies),
            "union": list(dependencies),
            "v": 1,
        }
        expected_union = {
            "dependencies": list(dependencies),
            "dependency_count": len(dependencies),
            "preimage": expected_union_preimage,
            "root_sha256": _sha256_json(expected_union_preimage),
            "scope": "bounded-pilot-root-only-not-publication-verified",
        }
        if theorem.get("bounded_local_union") != expected_union:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"bounded local union for {name!r} differs"
            )

        observations = _baseline_artifact_observations(
            name=name,
            a22_row=a22_row,
            a23_row=a23_row,
            replay_row=replay_row,
        )
        root_body_receipt = _expected_root_body_receipt(a22_row, replay_row)
        readable_closure = _closure(
            name,
            dependencies,
            replay_rows=replay_rows,
            fixed_vectors=readable_fixed_vectors,
        )
        layered_closure = _closure(
            name,
            dependencies,
            replay_rows=replay_rows,
            fixed_vectors=layered_fixed_vectors,
        )
        expected_a23_closure = tuple(
            layered_artifact["surface"][
                "transitive_closure_dependencies_in_replay_order"
            ]
        )
        if layered_closure != expected_a23_closure:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"independent layered closure for {name!r} differs"
            )
        diagnostics = {
            READABLE_ROUTE: _expected_readable_diagnostics(
                dependencies=dependencies,
                replay_rows=replay_rows,
                root_body_receipt=root_body_receipt,
            ),
            LAYERED_ROUTE: _expected_layered_diagnostics(
                name=name,
                dependencies=dependencies,
                closure=layered_closure,
                root_body_receipt=root_body_receipt,
                a23_row=a23_row,
            ),
        }
        route_rows = theorem.get("routes")
        if type(route_rows) is not list or len(route_rows) != 2:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"route list for {name!r} differs"
            )
        verified_routes: dict[str, dict[str, object]] = {}
        verified_attempts: dict[str, list[dict[str, object]]] = {}
        for route, route_row in zip(ROUTES, route_rows, strict=True):
            fixed_vectors = (
                readable_fixed_vectors
                if route == READABLE_ROUTE
                else layered_fixed_vectors
            )
            verified_route, attempts = _verify_route(
                route_row,
                route=route,
                name=name,
                index=index,
                dependencies=dependencies,
                script=script,
                fixed_vectors=fixed_vectors,
                replay_rows=replay_rows,
                diagnostics=diagnostics[route],
                observation=observations[route],
                producer_source_state_root_sha256=source_state["root_sha256"],
                callable_limits_sha256=callable_limits["sha256"],
            )
            verified_routes[route] = verified_route
            verified_attempts[route] = attempts
        _shared_receipt, theorem_shared = _verify_shared_route_pairing(
            verified_attempts[READABLE_ROUTE],
            verified_attempts[LAYERED_ROUTE],
            baseline_root_body_receipt=root_body_receipt,
            recorded=theorem.get("shared_body_consistency"),
        )
        theorem_route_count = 2 * len(dependencies)
        if (
            theorem.get("bounded_protocol_executed") is not True
            or theorem.get("bounded_three_root_vector_audit_complete") is not False
            or theorem.get("single_omission_attempt_count")
            != theorem_route_count
            or theorem.get("single_omission_kernel_accepted_count") != 0
            or theorem.get("single_omission_rejected_count")
            != theorem_route_count
            or theorem.get("single_omission_terminal_count")
            != theorem_route_count
            or theorem.get("terminal_route_observations_complete") is not True
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"bounded attempt aggregate for {name!r} differs"
            )
        candidate_record_sha = _record_hash(theorem)
        if theorem.get("record_sha256") != candidate_record_sha:
            raise LibraryPilotDependencyVectorAuditVerificationError(
                f"candidate theorem record hash for {name!r} differs"
            )
        candidate_record_identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": candidate_record_sha,
            }
        )
        baseline_rows = []
        for route, source in (
            (READABLE_ROUTE, "fixed-a2.2-embedded-artifact"),
            (LAYERED_ROUTE, "fixed-a2.3a-embedded-artifact"),
        ):
            baseline_rows.append(
                {"route": route, "source": source, **observations[route]}
            )
        verification_row: dict[str, object] = {
            "baseline_artifacts": baseline_rows,
            "candidate_record_sha256": candidate_record_sha,
            "index": index,
            "name": name,
            "producer_observation_route_record_count": theorem_route_count,
            "unique_shared_root_body_observation_count": len(theorem_shared),
        }
        verification_row["record_sha256"] = _record_hash(verification_row)
        if set(verification_row) != set(_VERIFICATION_THEOREM_FIELDS):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "internal verification theorem field contract drifted"
            )
        verification_rows.append(verification_row)
        verification_record_identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": verification_row["record_sha256"],
            }
        )
        if all_shared_observations.intersection(theorem_shared):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "shared root-body observation digest is duplicated across roots"
            )
        all_shared_observations.update(theorem_shared)
        route_record_count += theorem_route_count

    candidate_records_preimage = {
        "format": CANDIDATE_RECORDS_PREIMAGE_FORMAT,
        "records": candidate_record_identities,
        "v": 1,
    }
    candidate_records = {
        "count": len(EXPECTED_THEOREMS),
        "preimage": candidate_records_preimage,
        "root_sha256": _sha256_json(candidate_records_preimage),
    }
    if document.get("theorem_records") != candidate_records:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate theorem-record root differs"
        )
    candidate_body = {key: document[key] for key in _CANDIDATE_ROOT_BODY_FIELDS}
    candidate_root_preimage = {
        "format": CANDIDATE_ROOT_PREIMAGE_FORMAT,
        "payload": candidate_body,
        "v": CANDIDATE_VERSION,
    }
    candidate_root_sha = _sha256_json(candidate_root_preimage)
    if (
        document.get("root_preimage") != candidate_root_preimage
        or document.get("root_sha256") != candidate_root_sha
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate document root differs"
        )
    expected_aggregate = {
        "bounded_local_union_edges": 22,
        "kernel_accepted_baseline_count": 6,
        "pilot_theorem_count": 3,
        "retained_public_graph_edges": RETAINED_PUBLIC_GRAPH_EDGES,
        "route_count": 2,
        "single_omission_attempt_count": EXPECTED_ATTEMPT_COUNT,
        "single_omission_kernel_accepted_count": 0,
        "single_omission_rejected_count": EXPECTED_ATTEMPT_COUNT,
        "single_omission_terminal_count": EXPECTED_ATTEMPT_COUNT,
    }
    if document.get("aggregate") != expected_aggregate:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate aggregate differs from independent recomputation"
        )
    if (
        route_record_count != EXPECTED_ATTEMPT_COUNT
        or len(all_shared_observations)
        != EXPECTED_UNIQUE_SHARED_OBSERVATION_COUNT
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "candidate 44-route/22-shared observation boundary differs"
        )

    verification_records_preimage = {
        "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": verification_record_identities,
        "v": VERIFICATION_VERSION,
    }
    verification_records = {
        "count": len(verification_rows),
        "preimage": verification_records_preimage,
        "root_sha256": _sha256_json(verification_records_preimage),
    }
    verifier_relative = Path(
        "training/peano_hydra/"
        "library_pilot_dependency_vector_audit_verifier.py"
    )
    verifier_raw = _safe_file(
        root / verifier_relative,
        label="independent A2.3b verifier source",
        limit=MAX_SOURCE_FILE_BYTES,
    )
    false_claims = {field: False for field in VERIFICATION_FALSE_FIELDS}
    receipt_body: dict[str, object] = {
        **false_claims,
        "aggregate": {
            "baseline_artifact_count": EXPECTED_BASELINE_ARTIFACT_COUNT,
            "kernel_accepted_baseline_artifact_count": (
                EXPECTED_BASELINE_ARTIFACT_COUNT
            ),
            "pilot_theorem_count": len(EXPECTED_THEOREMS),
            "producer_observation_route_record_count": route_record_count,
            "unique_shared_root_body_observation_count": len(
                all_shared_observations
            ),
        },
        "candidate": {
            "artifact_bytes": len(candidate_raw),
            "artifact_sha256": _sha256(candidate_raw),
            "root_sha256": candidate_root_sha,
            "theorem_record_root_sha256": candidate_records[
                "root_sha256"
            ],
        },
        "candidate_status": CANDIDATE_STATUS,
        "format": VERIFICATION_FORMAT,
        "id": VERIFICATION_ID,
        "kernel_baseline_artifacts_verified": True,
        "logic_mode": LOGIC_MODE,
        "producer_observations_structurally_verified": True,
        "producer_source_state": {
            "artifact_bytes": len(producer_source_state_raw),
            "artifact_sha256": _sha256(producer_source_state_raw),
            "root_sha256": source_state["root_sha256"],
            "semantic_sha256": _sha256_json(
                source_state, limit=MAX_SCHEMA_BYTES
            ),
        },
        "producer_source_state_sha256": document[
            "producer_source_state_sha256"
        ],
        "status": VERIFICATION_STATUS,
        "structural_receipts_verified": True,
        "theorem_count": len(verification_rows),
        "theorem_records": verification_records,
        "v": VERIFICATION_VERSION,
        "verifier": {
            "bytecode_write_disabled": True,
            "import_policy": "stdlib-and-peano-kernel-only",
            "kernel_sources": fixed["kernel_sources"],
            "load_mode": "direct-source-module-without-training-package-init",
            "path": verifier_relative.as_posix(),
            "pycache_prefix": PYCACHE_PREFIX,
            "safe_path": True,
            "sha256": _sha256(verifier_raw),
            "site_import_disabled": True,
            "source_loader_preflight": (
                "pathfinder-sourcefileloader-exact-origin"
            ),
            "stdlib_precedes_peano_root": True,
            "user_site_disabled": True,
        },
    }
    if set(receipt_body) != set(VERIFICATION_RECEIPT_BODY_FIELDS):
        raise LibraryPilotDependencyVectorAuditVerificationError(
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


def validate_pilot_dependency_vector_audit_verification_receipt(
    value: object,
    *,
    candidate: object,
    producer_source_state: object,
    candidate_raw: bytes | None = None,
    producer_source_state_raw: bytes | None = None,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Deep-validate a receipt and reconstruct it through the kernel path."""

    receipt = _require_fields(
        "independent A2.3b verification receipt",
        value,
        VERIFICATION_RECEIPT_FIELDS,
    )
    _require_false_fields(
        "independent A2.3b verification receipt",
        receipt,
        VERIFICATION_FALSE_FIELDS,
    )
    if (
        receipt.get("format") != VERIFICATION_FORMAT
        or receipt.get("id") != VERIFICATION_ID
        or receipt.get("v") != VERIFICATION_VERSION
        or receipt.get("status") != VERIFICATION_STATUS
        or receipt.get("candidate_status") != CANDIDATE_STATUS
        or receipt.get("logic_mode") != LOGIC_MODE
        or receipt.get("kernel_baseline_artifacts_verified") is not True
        or receipt.get("producer_observations_structurally_verified") is not True
        or receipt.get("structural_receipts_verified") is not True
        or receipt.get("theorem_count") != len(EXPECTED_THEOREMS)
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "independent A2.3b verification receipt identity differs"
        )
    rows = receipt.get("theorems")
    if type(rows) is not list or len(rows) != len(EXPECTED_THEOREMS):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "independent verification theorem rows differ"
        )
    identities: list[dict[str, object]] = []
    for (index, name), row in zip(EXPECTED_THEOREMS, rows, strict=True):
        theorem = _require_fields(
            f"independent verification theorem {name!r}",
            row,
            _VERIFICATION_THEOREM_FIELDS,
        )
        if (
            theorem.get("index") != index
            or theorem.get("name") != name
            or theorem.get("record_sha256") != _record_hash(theorem)
        ):
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "independent verification theorem record differs"
            )
        identities.append(
            {
                "index": index,
                "name": name,
                "record_sha256": theorem["record_sha256"],
            }
        )
    records_preimage = {
        "format": VERIFICATION_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": VERIFICATION_VERSION,
    }
    expected_records = {
        "count": len(rows),
        "preimage": records_preimage,
        "root_sha256": _sha256_json(records_preimage),
    }
    if receipt.get("theorem_records") != expected_records:
        raise LibraryPilotDependencyVectorAuditVerificationError(
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
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "independent verification document root differs"
        )
    expected = verify_pilot_dependency_vector_audit(
        candidate,
        producer_source_state=producer_source_state,
        candidate_raw=candidate_raw,
        producer_source_state_raw=producer_source_state_raw,
        repository_root=repository_root,
    )
    if receipt != expected:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "verification receipt differs from exact independent reconstruction"
        )
    return deepcopy(receipt)


def load_and_verify_pilot_dependency_vector_audit(
    candidate_path: Path,
    producer_source_state_path: Path,
    *,
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Strict-load a candidate/source-state pair and return its receipt."""

    candidate_raw = _safe_file(
        candidate_path,
        label="A2.3b pilot dependency-vector audit candidate",
        limit=MAX_DOCUMENT_BYTES,
    )
    candidate = _decode_document(
        candidate_raw,
        "A2.3b pilot dependency-vector audit candidate",
        limit=MAX_DOCUMENT_BYTES,
    )
    if canonical_verification_receipt_bytes(candidate) != candidate_raw:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b candidate is not canonical"
        )
    source_raw = _safe_file(
        producer_source_state_path,
        label="A2.3b producer source state",
        limit=MAX_SCHEMA_BYTES,
    )
    source_state = _decode_document(
        source_raw, "A2.3b producer source state", limit=MAX_SCHEMA_BYTES
    )
    if (
        canonical_verification_receipt_bytes(
            source_state, limit=MAX_SCHEMA_BYTES
        )
        != source_raw
    ):
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "A2.3b producer source state is not canonical"
        )
    return verify_pilot_dependency_vector_audit(
        candidate,
        producer_source_state=source_state,
        candidate_raw=candidate_raw,
        producer_source_state_raw=source_raw,
        repository_root=repository_root,
    )


__all__ = [
    "LibraryPilotDependencyVectorAuditVerificationError",
    "VERIFICATION_FALSE_FIELDS",
    "VERIFICATION_RECEIPT_BODY_FIELDS",
    "VERIFICATION_RECEIPT_FIELDS",
    "canonical_verification_receipt_bytes",
    "load_and_verify_pilot_dependency_vector_audit",
    "validate_pilot_dependency_vector_audit_verification_receipt",
    "verify_pilot_dependency_vector_audit",
]
