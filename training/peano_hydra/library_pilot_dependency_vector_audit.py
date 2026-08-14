"""Bounded candidate-only A2.3b dependency-vector audit producer.

This module audits two deliberately distinct construction routes for exactly
three retained pilot roots.  The readable route closes a freshly replayed
candidate body with the selected direct certificates.  The proposed layered
route freshly regenerates the root modular body for every omitted vector,
recomputes the reachable graph with only that root vector changed, rebuilds
every modular-body/provenance row, and invokes the existing layered compiler.

An omission rejection is evidence only about the exact frozen route.  It is
not dependency necessity, minimality, best-known, optimizer, publication,
admission, or A2 authority.  Resource, internal, malformed, unsupported, and
typed-unknown outcomes abort the document instead of becoming rejections.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable, Mapping

from peano_lab.engine.proof_reduction import ProofReductionError
from peano_lab.engine.tactics import InvalidProof, TacticError
from peano_lab.kernel.artifact_codec import (
    decode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Proof
from peano_lab.library.candidate_validation import (
    CandidateBodyCompilation,
    CandidateBodyError,
    compile_candidate_body,
)
from peano_lab.library.layered_replay import (
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayLimits,
    LayeredReplayNode,
    compile_layered_replay,
)
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula

from .library_construction_rebuild_core import (
    ClosedCandidateCompilation,
    DependencyCertificate,
    compile_closed_candidate,
)
from .library_optimizer_comparison_pilot import recover_curried_modular_body
from .library_replay_pack import proof_tree_metrics


PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-schema"
)
PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_VERSION = 1
PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_ID = (
    "peano-hydra-library-pilot-dependency-vector-audit-v1"
)
PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_PATH = Path(__file__).with_name(
    "library-pilot-dependency-vector-audit-schema-v1.json"
)
PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_SHA256 = (
    "6782197c9925f5552aab030a11b996c157e2d06344a2d136d8babc1ee1fdc3df"
)

PILOT_DEPENDENCY_VECTOR_AUDIT_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit"
)
PILOT_DEPENDENCY_VECTOR_AUDIT_VERSION = 1
PILOT_DEPENDENCY_VECTOR_AUDIT_ID = (
    "authoring-l0-pilot-dependency-vector-audit-candidate-v1"
)
PILOT_DEPENDENCY_VECTOR_AUDIT_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-pilot-dependency-vector-audit-root-preimage"
)
THEOREM_RECORDS_PREIMAGE_FORMAT = (
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

READABLE_ROUTE = "readable-direct-closure"
PROPOSED_LAYERED_ROUTE = "proposed-layered-closure-construction"
STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
THEOREM_COUNT = 3
LIBRARY_THEOREM_COUNT = 384
EXPECTED_DIRECT_EDGE_COUNT = 22
EXPECTED_ATTEMPT_COUNT = 44
RETAINED_PUBLIC_GRAPH_EDGES = 1_038

MAX_SCHEMA_BYTES = 1_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_SOURCE_FILE_BYTES = 16_000_000
MAX_ARTIFACT_BYTES = 8_000_000
ARTIFACT_DECODE_MAX_NODES = 1_000_000
ARTIFACT_DECODE_MAX_DEPTH = 512
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
MAX_JSON_DEPTH = 256
MAX_JSON_ITEMS = 4_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

EXPECTED_ROOTS = (
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
QUALIFIED_CALLABLES = {
    "artifact_decode": "peano_lab.kernel.artifact_codec.decode_artifact",
    "artifact_encode": (
        "peano_lab.kernel.artifact_codec.encode_artifact_bounded"
    ),
    "candidate_body": (
        "peano_lab.library.candidate_validation.compile_candidate_body"
    ),
    "closed_readable": (
        "training.peano_hydra.library_construction_rebuild_core."
        "compile_closed_candidate"
    ),
    "formula_encode": "peano_lab.kernel.artifact_codec.encode_formula",
    "kernel": "peano_lab.kernel.checker.check",
    "layered": "peano_lab.library.layered_replay.compile_layered_replay",
    "modular_recovery": (
        "training.peano_hydra.library_optimizer_comparison_pilot."
        "recover_curried_modular_body"
    ),
    "proof_encode": "peano_lab.kernel.artifact_codec.encode_proof",
    "proof_metrics": (
        "training.peano_hydra.library_replay_pack.proof_tree_metrics"
    ),
}

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_A21_RELATIVE = Path("artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json")
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
_REPLAY_ROOT_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
_REPLAY_MANIFEST_RELATIVE = _REPLAY_ROOT_RELATIVE / "manifest.json"
_REPLAY_REPORT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)

_FIXED_INPUTS = {
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

_PINNED_IMPLEMENTATION = (
    (
        Path("peano-lab/py/peano_lab/__init__.py"),
        "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/__init__.py"),
        "1fbd27721e00e873b4b6839508b63889e6ba8a4a51165b11e042c05270d1308b",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/decide.py"),
        "07044458d92b68781d95091fabbe0fbc4a476c58f3821e0c806553e0813c2e0a",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/induction.py"),
        "4bb1db5f3b944e1f9a0ebe388ab76970aae055bf4d1171d896fbb0323172545f",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/norm_num.py"),
        "79d9ebe369348779aca6c7f12932a1204756a13d631ebd69f2612de082ab13b1",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/proof_reduction.py"),
        "deb17a5a0d5562f73248d6fbaa8db46b923c7bab07e491f37cb98e5e19a8251f",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/rewrite.py"),
        "05f0b5fe8d46910d9cc2b1604d96756aa68e42339ca90afc094d60bfce48aa5f",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/state.py"),
        "453904142273f14d01379c73c637be3476d035b093047587ff6990f1d572ac2f",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/tactics.py"),
        "fde9605bce6e14513260ffeb69eea8ae40a6ad7d44da3ff550fb3edf9b6396e4",
    ),
    (
        Path("peano-lab/py/peano_lab/engine/trace.py"),
        "d9a7b2aa789fefd8d0da8d6ce6b6ae37b925f92a3e611e0809b02cd5e9173df7",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/__init__.py"),
        "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/checker.py"),
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/formulas.py"),
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/proofs.py"),
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/subst.py"),
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    ),
    (
        Path("peano-lab/py/peano_lab/kernel/terms.py"),
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
    ),
    (
        Path("peano-lab/py/peano_lab/library/__init__.py"),
        "70035fa65aafe8bed7a7b1538b0f4fdbf895ca1d5ddeef3625b9fdb9fb4e77e5",
    ),
    (
        Path("peano-lab/py/peano_lab/library/candidate_validation.py"),
        "b41e6587d32e27152e1358b3067c72b869357674548f05aa4ef5e86cf9bdc30a",
    ),
    (
        Path("peano-lab/py/peano_lab/library/theorems.py"),
        "bfa6fad2c91a774b37c3ee458e9b59d679f7257a1ab4b2bef3f88bbccdb82a2f",
    ),
    (
        Path("peano-lab/py/peano_lab/library/parity.py"),
        "f39325d72c0f29969b6e01cfd92451fe29f911a485a628f2baa33c0319dcf2da",
    ),
    (
        Path("peano-lab/py/peano_lab/library/quadratic_residue_surface.py"),
        "ab7abd5b9fcf306035de6eb849ad65f8287e84e6cc00ad909aeed7e880915246",
    ),
    (
        Path("peano-lab/py/peano_lab/library/quadratic_residue_theorems.py"),
        "d08e6a29295be014c67ec52d8cf7b67cc4b7c99abe6dde3708c162beccc4126d",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_fold_surface.py"),
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_fold_theorems.py"),
        "e69c41198d25aa0cba3bbf8415344050b28ecb8d058c1cd8d98415e0db09178c",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_range_theorems.py"),
        "8ca4812b8059e76ec2faf4e4269d5192adee320df281b16dacfd5e7b9682833f",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_sum_theorems.py"),
        "0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_congruence_theorems.py"),
        "d82ad67620210cd81741bc8eb287569f9bf5124714ba50da65985c7d33a8ec68",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_bitcount_theorems.py"),
        "4704e64d968b6ff19d302ef404dac38a8510aff980fd41063dde0010d6390e6c",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_factorial_theorems.py"),
        "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709",
    ),
    (
        Path("peano-lab/py/peano_lab/library/power_congruence_theorems.py"),
        "f1b34a176f9c77d60ef7dd1908ec7e6163608f684451c992dbd9fb8dacf34423",
    ),
    (
        Path("peano-lab/py/peano_lab/library/qr_small_moduli.py"),
        "fb8dbbb75817e15f4e522e6d4ce20a0b4a13f4a836872ad6b8de6ed51c0d5530",
    ),
    (
        Path("peano-lab/py/peano_lab/library/power_algebra_theorems.py"),
        "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302",
    ),
    (
        Path("peano-lab/py/peano_lab/library/gauss_sign_bridge.py"),
        "2ea4ae59ea1d5120d93af74d7f4c1cff624c9ad3a0aeac36d3b8dd2901412b76",
    ),
    (
        Path("peano-lab/py/peano_lab/library/gauss_half_range.py"),
        "3653e994bc5862c686d21a9597e0aef19302eccdbcc3badffc260918b2a656d7",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_permutation_theorems.py"),
        "6265e4cf5938beadbf77182b7a5357a9435abd9948015a955539b451430420ce",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_product_permutation_theorems.py"),
        "a9d799a189d8061b1ee97f163172f95396a35819cfef791543407ee0a34aea5a",
    ),
    (
        Path("peano-lab/py/peano_lab/library/finite_product_reindex_support.py"),
        "7adf1f63c23e39ab1428061355cebb3caddd3bf51e909185ec22d83b6442fc7c",
    ),
    (
        Path("peano-lab/py/peano_lab/library/qr_bounded_units.py"),
        "1ca3673054052094c32cabfca6a59f7e801ccd51b1fd9fee780d52fecaa70562",
    ),
    (
        Path("peano-lab/py/peano_lab/library/qr_prime_units.py"),
        "ea611d606ed0b345e75e230c77ea9ec5ee5ce9a2b1d85ae400c2ac94819c11cd",
    ),
    (
        Path("peano-lab/py/peano_lab/library/layered_replay.py"),
        "ad4421446336b7c8c0db9f12298a5aa66718dfeac76282ab91bf0db3ce00f4c4",
    ),
    (
        Path("training/peano_hydra/library_construction_rebuild_core.py"),
        "98c2aa5b13b77a4f2e47c9d8663ff52c072e3cf61cac172dae523f30bfb25d10",
    ),
    (
        Path("training/peano_hydra/library_optimizer_comparison_pilot.py"),
        "7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee",
    ),
    (
        Path("training/peano_hydra/library_replay_pack.py"),
        "8c5f3b44bed64bc3a49a7990d16a6f3c4a966b14c2bf4c732227041bc81506ee",
    ),
)
IMPLEMENTATION_SOURCE_ROOT_SHA256 = (
    "4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0"
)
PRODUCER_SOURCE_FILES = (
    Path(
        "training/peano_hydra/"
        "library-pilot-dependency-vector-audit-schema-v1.json"
    ),
    Path("training/peano_hydra/library_pilot_dependency_vector_audit.py"),
    Path("scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py"),
    Path(
        "peano-lab/py/tests/"
        "test_peano_hydra_library_pilot_dependency_vector_audit.py"
    ),
)
PRODUCER_SOURCE_STATE_FORMAT = "peano-hydra-producer-source-state"
PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-producer-source-state-root-preimage"
)

PILOT_LAYERED_LIMITS = LayeredReplayLimits(
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

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA1_RE = re.compile(r"[0-9a-f]{40}")


class LibraryPilotDependencyVectorAuditError(ValueError):
    """The bounded A2.3b input, execution, or document is invalid/unknown."""


@dataclass(frozen=True, slots=True)
class _CandidateEvidence:
    target: Formula
    proof: Proof
    direct_dependencies: tuple[str, ...]
    closure: tuple[str, ...]
    diagnostics: Mapping[str, object]


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
        raise LibraryPilotDependencyVectorAuditError(
            f"{path} exceeds the JSON depth limit"
        )
    if value is None or type(value) is bool:
        return 1
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryPilotDependencyVectorAuditError(
                f"{path} exceeds the JSON integer domain"
            )
        return 1
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise LibraryPilotDependencyVectorAuditError(
                f"{path} is not valid UTF-8 text"
            ) from exc
        return 1
    if type(value) not in (list, dict):
        raise LibraryPilotDependencyVectorAuditError(
            f"{path} contains a non-JSON value"
        )
    identity = id(value)
    if identity in ancestors:
        raise LibraryPilotDependencyVectorAuditError(f"{path} contains a cycle")
    branch = ancestors | {identity}
    count = 1
    if type(value) is list:
        for index, item in enumerate(value):
            count += _validate_json(
                item, path=f"{path}[{index}]", depth=depth + 1, ancestors=branch
            )
            if count > MAX_JSON_ITEMS:
                raise LibraryPilotDependencyVectorAuditError(
                    "JSON exceeds its item limit"
                )
        return count
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryPilotDependencyVectorAuditError(
                f"{path} has a non-string object key"
            )
        count += 1 + _validate_json(
            item, path=f"{path}.{key}", depth=depth + 1, ancestors=branch
        )
        if count > MAX_JSON_ITEMS:
            raise LibraryPilotDependencyVectorAuditError(
                "JSON exceeds its item limit"
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
        raise LibraryPilotDependencyVectorAuditError(
            "cannot encode canonical JSON"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditError(
            "canonical JSON exceeds its byte limit"
        )
    return raw


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_DOCUMENT_BYTES) -> str:
    return _sha256_bytes(_compact_json(value, limit=limit))


def canonical_document_bytes(
    value: object, *, limit: int = MAX_DOCUMENT_BYTES
) -> bytes:
    """Return the sole canonical retained JSON representation."""

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
        raise LibraryPilotDependencyVectorAuditError(
            "cannot encode canonical document"
        ) from exc
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditError(
            "canonical document exceeds its byte limit"
        )
    return raw


def _decode_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if len(raw) > limit:
        raise LibraryPilotDependencyVectorAuditError(
            f"{label} exceeds its byte limit"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorAuditError(f"{label} must be one object")
    _validate_json(value)
    return value


def _read_regular_bytes(path: Path, *, label: str, limit: int) -> bytes:
    """Read a bounded regular file without following path-component links."""

    try:
        absolute = Path(os.path.abspath(path))
        current = Path(absolute.anchor)
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorAuditError(
                    f"{label} parent contains a link or non-directory component"
                )
        metadata = absolute.lstat()
    except LibraryPilotDependencyVectorAuditError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorAuditError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryPilotDependencyVectorAuditError(
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
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} exceeds its byte limit"
            )
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
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} changed while read"
            )
        return raw
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(f"cannot read {label}") from exc
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
        raise LibraryPilotDependencyVectorAuditError(
            "cannot resolve repository_root"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise LibraryPilotDependencyVectorAuditError(
            "repository_root must be a non-symlink directory"
        )
    return resolved


def pilot_dependency_vector_audit_schema() -> dict[str, object]:
    """Load, canonicalize, and authenticate the A2.3b protocol schema."""

    raw = _read_regular_bytes(
        PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_PATH,
        label="pilot dependency-vector audit schema",
        limit=MAX_SCHEMA_BYTES,
    )
    value = _decode_document(
        raw, "pilot dependency-vector audit schema", limit=MAX_SCHEMA_BYTES
    )
    if canonical_document_bytes(value, limit=MAX_SCHEMA_BYTES) != raw:
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit schema is not canonical"
        )
    if _sha256_json(value, limit=MAX_SCHEMA_BYTES) != (
        PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit schema digest drifted"
        )
    if (
        value.get("format") != PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_FORMAT
        or value.get("id") != PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_ID
        or value.get("v") != PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_VERSION
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit schema identity drifted"
        )
    return deepcopy(value)


def pilot_dependency_vector_audit_schema_identity() -> dict[str, object]:
    schema = pilot_dependency_vector_audit_schema()
    raw = canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "format": PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_FORMAT,
        "id": PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_ID,
        "sha256": PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_SHA256,
        "v": PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_VERSION,
    }


def _single_omission_vectors(
    dependencies: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if (
        type(dependencies) is not tuple
        or not all(type(item) is str and item for item in dependencies)
        or len(set(dependencies)) != len(dependencies)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "direct dependency vector is malformed"
        )
    return tuple(
        (
            dependencies[index],
            dependencies[:index] + dependencies[index + 1 :],
        )
        for index in range(len(dependencies) - 1, -1, -1)
    )


def _ordered_union(
    readable: tuple[str, ...], proposed: tuple[str, ...]
) -> tuple[str, ...]:
    for label, vector in (("readable", readable), ("proposed", proposed)):
        if (
            type(vector) is not tuple
            or not all(type(item) is str and item for item in vector)
            or len(set(vector)) != len(vector)
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} direct dependency vector is malformed"
            )
    return tuple(dict.fromkeys((*readable, *proposed)))


def _lf_sha256(values: tuple[str, ...]) -> str:
    return _sha256_bytes(
        ("\n".join(values) + ("\n" if values else "")).encode("utf-8")
    )


def _dependency_surface(
    dependencies: tuple[str, ...], closure: tuple[str, ...], *, basis: str
) -> dict[str, object]:
    if (
        type(basis) is not str
        or not basis
        or type(dependencies) is not tuple
        or type(closure) is not tuple
        or not all(type(item) is str and item for item in (*dependencies, *closure))
        or len(set(dependencies)) != len(dependencies)
        or len(set(closure)) != len(closure)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "dependency surface is malformed"
        )
    return {
        "direct_dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": _lf_sha256(dependencies),
        "direct_dependency_count": len(dependencies),
        "surface_basis": basis,
        "transitive_closure_count": len(closure),
        "transitive_closure_dependencies_in_replay_order": list(closure),
        "transitive_closure_lf_sha256": _lf_sha256(closure),
    }


def _route_preimage(
    *,
    route: str,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    attempts_root_sha256: str,
    baseline_receipt_sha256: str,
    formula_sha256: str,
    direct_dependencies_lf_sha256: str,
    baseline_closure_lf_sha256: str,
    root_body_certificate_sha256: str,
    producer_source_state_root_sha256: str,
    implementation_source_root_sha256: str,
    callable_limits_sha256: str,
) -> dict[str, object]:
    if route not in (READABLE_ROUTE, PROPOSED_LAYERED_ROUTE):
        raise LibraryPilotDependencyVectorAuditError("route is not registered")
    if (
        type(name) is not str
        or not name
        or type(index) is not int
        or index < 0
        or any(
            _SHA256_RE.fullmatch(value) is None
            for value in (
                attempts_root_sha256,
                baseline_receipt_sha256,
                formula_sha256,
                direct_dependencies_lf_sha256,
                baseline_closure_lf_sha256,
                root_body_certificate_sha256,
                producer_source_state_root_sha256,
                implementation_source_root_sha256,
                callable_limits_sha256,
            )
        )
    ):
        raise LibraryPilotDependencyVectorAuditError("route identity is malformed")
    _single_omission_vectors(dependencies)
    return {
        "attempts_root_sha256": attempts_root_sha256,
        "baseline_closure_lf_sha256": baseline_closure_lf_sha256,
        "baseline_receipt_sha256": baseline_receipt_sha256,
        "callable_limits_sha256": callable_limits_sha256,
        "dependencies": list(dependencies),
        "direct_dependencies_lf_sha256": direct_dependencies_lf_sha256,
        "format": ROUTE_RECEIPT_PREIMAGE_FORMAT,
        "formula_sha256": formula_sha256,
        "implementation_source_root_sha256": implementation_source_root_sha256,
        "index": index,
        "name": name,
        "producer_source_state_root_sha256": producer_source_state_root_sha256,
        "root_body_certificate_sha256": root_body_certificate_sha256,
        "route": route,
        "v": 1,
    }


def _classify_candidate_error(error: CandidateBodyError) -> dict[str, object]:
    """Admit only exact, structured deterministic route rejection evidence."""

    if type(error) is not CandidateBodyError:
        raise TypeError("error must be an exact CandidateBodyError")
    cause = error.__cause__
    allowed = False
    if error.kind == "exact-recipe-rejection" and error.phase == "command":
        allowed = (
            type(cause) is TacticError
            and type(error.command_index) is int
            and error.command_index >= 0
            and type(error.command) is str
            and bool(error.command)
        )
    elif error.kind == "exact-recipe-rejection" and error.phase == "finalization":
        if error.command_index is not None or error.command is not None:
            allowed = False
        elif type(cause) in (InvalidProof, ProofReductionError):
            allowed = True
        elif cause is None:
            message = str(error)
            allowed = bool(
                re.fullmatch(
                    r"candidate '[A-Za-z0-9_]+' (?:produced an incomplete "
                    r"dependency-curried proof|left a hole or metavariable "
                    r"during finalization)",
                    message,
                )
            )
    if not allowed:
        raise LibraryPilotDependencyVectorAuditError(
            "unknown candidate route outcome; aborting instead of recording "
            f"{error.kind!r}/{error.phase!r}"
        ) from error
    return {
        "failure": {
            "cause_type": None if cause is None else type(cause).__name__,
            "command": error.command,
            "command_index": error.command_index,
            "kind": error.kind,
            "phase": error.phase,
        },
        "outcome": "exact-route-rejected",
    }


def _classify_attempt_error(
    error: CandidateBodyError, *, script: tuple[str, ...]
) -> dict[str, object]:
    """Classify and bind command metadata to the exact frozen script."""

    if type(script) is not tuple or not all(type(item) is str for item in script):
        raise LibraryPilotDependencyVectorAuditError("attempt script is malformed")
    classification = _classify_candidate_error(error)
    if error.phase == "command" and (
        error.command_index is None
        or error.command_index >= len(script)
        or script[error.command_index] != error.command
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "unknown command rejection metadata; aborting attempt"
        ) from error
    return classification


def _require_layered_candidate(
    value: object, *, root_name: str, phase: str
) -> LayeredReplayCandidate:
    if type(value) is not LayeredReplayCandidate:
        raise LibraryPilotDependencyVectorAuditError(
            f"layered compiler returned unknown/unsupported result for "
            f"{root_name!r} during {phase}; aborting"
        )
    return value


def _implementation_rows() -> list[dict[str, str]]:
    return [
        {"path": relative.as_posix(), "sha256": digest}
        for relative, digest in _PINNED_IMPLEMENTATION
    ]


def _require_implementation(root: Path) -> None:
    rows = _implementation_rows()
    if _sha256_json(rows, limit=MAX_SCHEMA_BYTES) != (
        IMPLEMENTATION_SOURCE_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "implementation source root constant drifted"
        )
    schema = pilot_dependency_vector_audit_schema()
    if (
        schema.get("implementation_sources") != rows
        or schema.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or schema.get("artifact_decode_limits")
        != {
            "max_bytes": MAX_ARTIFACT_BYTES,
            "max_depth": ARTIFACT_DECODE_MAX_DEPTH,
            "max_nodes": ARTIFACT_DECODE_MAX_NODES,
        }
        or schema.get("artifact_encode_max_bytes") != MAX_ARTIFACT_BYTES
        or schema.get("fuel_policy")
        != {"multiplier": FUEL_MULTIPLIER, "offset": FUEL_OFFSET}
        or schema.get("expected_attempt_count") != EXPECTED_ATTEMPT_COUNT
        or schema.get("expected_roots")
        != [
            {"index": index, "name": name}
            for index, name in EXPECTED_ROOTS
        ]
        or schema.get("qualified_callables") != QUALIFIED_CALLABLES
        or schema.get("layered_replay_limits")
        != {
            field: getattr(PILOT_LAYERED_LIMITS, field)
            for field in PILOT_LAYERED_LIMITS.__dataclass_fields__
        }
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "schema implementation identity or layered limits drifted"
        )
    for relative, digest in _PINNED_IMPLEMENTATION:
        raw = _read_regular_bytes(
            root / relative,
            label=f"implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryPilotDependencyVectorAuditError(
                f"implementation source {relative.as_posix()!r} drifted"
            )
    callables = (
        (
            compile_candidate_body,
            "peano_lab.library.candidate_validation",
            "compile_candidate_body",
            Path("peano-lab/py/peano_lab/library/candidate_validation.py"),
        ),
        (
            compile_closed_candidate,
            "training.peano_hydra.library_construction_rebuild_core",
            "compile_closed_candidate",
            Path("training/peano_hydra/library_construction_rebuild_core.py"),
        ),
        (
            compile_layered_replay,
            "peano_lab.library.layered_replay",
            "compile_layered_replay",
            Path("peano-lab/py/peano_lab/library/layered_replay.py"),
        ),
        (
            check,
            "peano_lab.kernel.checker",
            "check",
            Path("peano-lab/py/peano_lab/kernel/checker.py"),
        ),
        (
            decode_artifact,
            "peano_lab.kernel.artifact_codec",
            "decode_artifact",
            Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        ),
        (
            encode_artifact_bounded,
            "peano_lab.kernel.artifact_codec",
            "encode_artifact_bounded",
            Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        ),
        (
            encode_formula,
            "peano_lab.kernel.artifact_codec",
            "encode_formula",
            Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        ),
        (
            encode_proof,
            "peano_lab.kernel.artifact_codec",
            "encode_proof",
            Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        ),
        (
            recover_curried_modular_body,
            "training.peano_hydra.library_optimizer_comparison_pilot",
            "recover_curried_modular_body",
            Path("training/peano_hydra/library_optimizer_comparison_pilot.py"),
        ),
        (
            proof_tree_metrics,
            "training.peano_hydra.library_replay_pack",
            "proof_tree_metrics",
            Path("training/peano_hydra/library_replay_pack.py"),
        ),
    )
    for value, module_name, qualified_name, relative in callables:
        if (
            getattr(value, "__module__", None) != module_name
            or getattr(value, "__qualname__", None) != qualified_name
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"qualified callable drifted for {module_name}.{qualified_name}"
            )
        module = importlib.import_module(module_name)
        if getattr(module, qualified_name, None) is not value:
            raise LibraryPilotDependencyVectorAuditError(
                f"callable alias drifted for {module_name}.{qualified_name}"
            )
        source = getattr(module, "__file__", None)
        if type(source) is not str:
            raise LibraryPilotDependencyVectorAuditError(
                f"cannot identify module {module_name!r}"
            )
        try:
            actual = Path(source).resolve(strict=True)
            expected = (root / relative).resolve(strict=True)
        except OSError as exc:
            raise LibraryPilotDependencyVectorAuditError(
                f"cannot resolve module {module_name!r}"
            ) from exc
        if actual != expected:
            raise LibraryPilotDependencyVectorAuditError(
                f"module origin drifted for {module_name!r}"
            )
    candidate_module = importlib.import_module(
        "peano_lab.library.candidate_validation"
    )
    tactics_module = importlib.import_module("peano_lab.engine.tactics")
    state_module = importlib.import_module("peano_lab.engine.state")
    core_module = importlib.import_module(
        "training.peano_hydra.library_construction_rebuild_core"
    )
    if (
        getattr(candidate_module, "apply_tactic", None)
        is not getattr(tactics_module, "apply_tactic", None)
        or getattr(candidate_module, "checked_final", None)
        is not getattr(tactics_module, "checked_final", None)
        or getattr(candidate_module, "proof_resource_metrics", None)
        is not getattr(state_module, "proof_resource_metrics", None)
        or getattr(core_module, "compile_candidate_body", None)
        is not compile_candidate_body
        or getattr(core_module, "check", None) is not check
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "critical imported callable alias drifted"
        )


def _validate_producer_source_state(
    value: object, *, root: Path
) -> dict[str, object]:
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
        raise LibraryPilotDependencyVectorAuditError(
            "producer source state has the wrong fields"
        )
    if (
        value.get("format") != PRODUCER_SOURCE_STATE_FORMAT
        or value.get("v") != 1
        or value.get("git_verified") is not False
        or type(value.get("commit_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(value["commit_sha1"]) is None
        or type(value.get("tree_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(value["tree_sha1"]) is None
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source-state identity is malformed"
        )
    files = value.get("files")
    if type(files) is not list or len(files) != len(PRODUCER_SOURCE_FILES):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source file list is malformed"
        )
    for expected, row in zip(PRODUCER_SOURCE_FILES, files, strict=True):
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise LibraryPilotDependencyVectorAuditError(
                "producer source file row is malformed"
            )
        if (
            row.get("path") != expected.as_posix()
            or type(row.get("bytes")) is not int
            or row["bytes"] <= 0
            or type(row.get("sha256")) is not str
            or _SHA256_RE.fullmatch(row["sha256"]) is None
        ):
            raise LibraryPilotDependencyVectorAuditError(
                "producer source file identity is malformed"
            )
        raw = _read_regular_bytes(
            root / expected,
            label=f"producer source {expected.as_posix()!r}",
            limit=MAX_SOURCE_FILE_BYTES,
        )
        if len(raw) != row["bytes"] or _sha256_bytes(raw) != row["sha256"]:
            raise LibraryPilotDependencyVectorAuditError(
                f"producer source {expected.as_posix()!r} differs from live bytes"
            )
    payload = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    expected_preimage = {
        "format": PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": 1,
    }
    if (
        value.get("root_preimage") != expected_preimage
        or value.get("root_sha256")
        != _sha256_json(expected_preimage, limit=MAX_SCHEMA_BYTES)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source-state root is malformed"
        )
    return deepcopy(value)


def _load_json_file(
    path: Path, *, label: str, expected_sha256: str, limit: int
) -> dict[str, object]:
    raw = _read_regular_bytes(path, label=label, limit=limit)
    if _sha256_bytes(raw) != expected_sha256:
        raise LibraryPilotDependencyVectorAuditError(f"{label} artifact drifted")
    value = _decode_document(raw, label, limit=limit)
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryPilotDependencyVectorAuditError(f"{label} is not canonical")
    return value


def _rows_by_name(
    document: Mapping[str, object], label: str, *, expected_count: int
) -> dict[str, dict[str, object]]:
    rows = document.get("theorems")
    if type(rows) is not list or len(rows) != expected_count:
        raise LibraryPilotDependencyVectorAuditError(
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
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} theorem order is malformed"
            )
        last_index = row["index"]
        result[row["name"]] = row
    return result


def _validate_live_theorem_transport(
    specs: tuple[TheoremSpec, ...],
    *,
    replay_rows: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    """Join every executed live theorem spec to the retained replay manifest."""

    if (
        type(specs) is not tuple
        or len(specs) != LIBRARY_THEOREM_COUNT
        or type(replay_rows) is not dict
        or len(replay_rows) != LIBRARY_THEOREM_COUNT
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "live theorem transport count/type drifted"
        )
    identities: list[dict[str, object]] = []
    seen: set[str] = set()
    for position, spec in enumerate(specs):
        if type(spec) is not TheoremSpec or type(spec.name) is not str:
            raise LibraryPilotDependencyVectorAuditError(
                f"live theorem spec type/name drifted at row {position}"
            )
        replay_row = replay_rows.get(spec.name)
        formula_sha256 = _sha256_bytes(
            encode_formula(_closed_formula(spec.statement))
        )
        statement_source_sha256 = _sha256_bytes(spec.statement.encode("utf-8"))
        script_sha256 = _lf_sha256(tuple(spec.script))
        if (
            spec.name in seen
            or type(replay_row) is not dict
            or type(replay_row.get("index")) is not int
            or replay_row.get("index") != position
            or replay_row.get("name") != spec.name
            or replay_row.get("statement_source") != spec.statement
            or replay_row.get("statement_source_sha256")
            != statement_source_sha256
            or type(replay_row.get("statement_canonical")) is not str
            or replay_row.get("statement_canonical_sha256")
            != _sha256_bytes(replay_row["statement_canonical"].encode("utf-8"))
            or tuple(replay_row.get("declared_dependencies", ()))
            != tuple(spec.dependencies)
            or type(replay_row.get("script")) is not list
            or tuple(replay_row["script"]) != tuple(spec.script)
            or replay_row.get("script_sha256") != script_sha256
            or replay_row.get("summary") != spec.summary
            or replay_row.get("formula_sha256") != formula_sha256
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"live theorem spec differs from retained replay row {position}"
            )
        seen.add(spec.name)
        identities.append(
            {
                "declared_dependencies": list(spec.dependencies),
                "formula_sha256": formula_sha256,
                "index": position,
                "name": spec.name,
                "script_sha256": script_sha256,
                "statement_canonical_sha256": replay_row[
                    "statement_canonical_sha256"
                ],
                "statement_source_sha256": statement_source_sha256,
                "summary_sha256": _sha256_bytes(spec.summary.encode("utf-8")),
            }
        )
    preimage = {
        "format": "peano-hydra-live-theorem-transport-preimage",
        "records": identities,
        "v": 1,
    }
    return {
        "count": LIBRARY_THEOREM_COUNT,
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "status": "exact-live-spec-to-retained-replay-transport",
    }


def _load_fixed_inputs(root: Path) -> dict[str, object]:
    _require_implementation(root)
    loaded: dict[str, dict[str, object]] = {}
    for label, (relative, digest, root_digest, records_digest) in (
        _FIXED_INPUTS.items()
    ):
        document = _load_json_file(
            root / relative,
            label=label,
            expected_sha256=digest,
            limit=MAX_DOCUMENT_BYTES,
        )
        if (
            document.get("root_sha256") != root_digest
            or document.get("theorem_count")
            != (384 if label == "a2.1_dependency_audit" else 3)
            or document.get("theorem_records", {}).get("root_sha256")
            != records_digest
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} retained identity drifted"
            )
        loaded[label] = document
    manifest = _load_json_file(
        root / _REPLAY_MANIFEST_RELATIVE,
        label="replay manifest",
        expected_sha256=REPLAY_MANIFEST_ARTIFACT_SHA256,
        limit=MAX_DOCUMENT_BYTES,
    )
    report = _load_json_file(
        root / _REPLAY_REPORT_RELATIVE,
        label="replay report",
        expected_sha256=REPLAY_REPORT_ARTIFACT_SHA256,
        limit=MAX_DOCUMENT_BYTES,
    )
    if (
        manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
        or manifest.get("theorem_count") != 384
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "replay manifest retained identity drifted"
        )
    a23 = loaded["a2.3a_candidate"]
    verification = loaded["a2.3a_verification"]
    if (
        verification.get("status") != "passed"
        or verification.get("candidate_status") != "candidate"
        or verification.get("kernel_artifacts_verified") is not True
        or verification.get("candidate", {}).get("artifact_sha256")
        != _FIXED_INPUTS["a2.3a_candidate"][1]
        or verification.get("candidate", {}).get("root_sha256")
        != a23.get("root_sha256")
        or verification.get("candidate", {}).get(
            "theorem_record_root_sha256"
        )
        != a23.get("theorem_records", {}).get("root_sha256")
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "A2.3a verification/candidate binding drifted"
        )
    a21_rows = _rows_by_name(
        loaded["a2.1_dependency_audit"], "A2.1", expected_count=384
    )
    a22_rows = _rows_by_name(
        loaded["a2.2_construction_rebuild"], "A2.2", expected_count=3
    )
    a23_rows = _rows_by_name(a23, "A2.3a", expected_count=3)
    verification_rows = _rows_by_name(
        verification, "A2.3a verification", expected_count=3
    )
    replay_rows = _rows_by_name(manifest, "replay manifest", expected_count=384)
    live_specs = tuple(THEOREMS)
    specs = {spec.name: spec for spec in live_specs}
    if len(specs) != LIBRARY_THEOREM_COUNT:
        raise LibraryPilotDependencyVectorAuditError("live theorem table drifted")
    theorem_transport = _validate_live_theorem_transport(
        live_specs, replay_rows=replay_rows
    )
    for index, name in EXPECTED_ROOTS:
        expected = EXPECTED_DIRECT[name]
        a21 = a21_rows[name]
        a22 = a22_rows[name]
        a23_row = a23_rows[name]
        verifier_row = verification_rows[name]
        replay_row = replay_rows[name]
        layered = next(
            (
                item
                for item in a23_row.get("artifacts", ())
                if type(item) is dict and item.get("candidate_id") == "layered-closure"
            ),
            None,
        )
        if (
            any(
                row.get("index") != index
                for row in (a21, a22, a23_row, verifier_row, replay_row)
            )
            or tuple(a21.get("readable", {}).get("dependencies", ())) != expected
            or tuple(a22.get("candidate_direct_dependencies", ())) != expected
            or type(layered) is not dict
            or tuple(layered.get("surface", {}).get("direct_dependencies", ()))
            != expected
            or layered.get("surface", {}).get("transitive_closure_count")
            != EXPECTED_CLOSURE_COUNTS[name]
            or a23_row.get("comparison", {}).get("representative_candidate_id")
            != "layered-closure"
            or a23_row.get("optimized_vector_independently_audited") is not False
            or specs.get(name) is None
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"fixed pilot join drifted for {name!r}"
            )
    return {
        **loaded,
        "a21_rows": a21_rows,
        "a22_rows": a22_rows,
        "a23_rows": a23_rows,
        "manifest": manifest,
        "replay_rows": replay_rows,
        "report": report,
        "specs": specs,
        "theorem_transport": theorem_transport,
        "verification_rows": verification_rows,
    }


def _transitive_closure(
    root_name: str,
    direct_dependencies: tuple[str, ...],
    *,
    replay_rows: Mapping[str, dict[str, object]],
    fixed_vectors: Mapping[str, tuple[str, ...]] | None = None,
) -> tuple[str, ...]:
    """Return replay-ordered closure with exactly one root-vector override."""

    if root_name not in replay_rows:
        raise LibraryPilotDependencyVectorAuditError("closure root is unknown")
    _single_omission_vectors(direct_dependencies)
    fixed = {} if fixed_vectors is None else dict(fixed_vectors)
    fixed[root_name] = direct_dependencies
    seen: set[str] = set()
    pending = list(direct_dependencies)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        row = replay_rows.get(name)
        if row is None:
            raise LibraryPilotDependencyVectorAuditError(
                f"closure contains unknown dependency {name!r}"
            )
        dependencies = fixed.get(name, tuple(row.get("declared_dependencies", ())))
        if (
            type(dependencies) is not tuple
            or not all(type(item) is str and item for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"retained dependency vector is malformed for {name!r}"
            )
        seen.add(name)
        pending.extend(dependencies)
    if root_name in seen:
        raise LibraryPilotDependencyVectorAuditError(
            "root-only override closure contains its root"
        )
    return tuple(sorted(seen, key=lambda name: replay_rows[name]["index"]))


def _decode_replay_certificate(
    name: str,
    *,
    root: Path,
    replay_rows: Mapping[str, dict[str, object]],
) -> DependencyCertificate:
    row = replay_rows.get(name)
    if type(row) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            f"replay certificate {name!r} is unknown"
        )
    artifact = row.get("artifact")
    if type(artifact) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            f"replay artifact metadata is malformed for {name!r}"
        )
    relative_text = artifact.get("path")
    if type(relative_text) is not str:
        raise LibraryPilotDependencyVectorAuditError(
            f"replay artifact path is malformed for {name!r}"
        )
    relative = Path(relative_text)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"replay artifact path is unsafe for {name!r}"
        )
    raw = _read_regular_bytes(
        root / _REPLAY_ROOT_RELATIVE / relative,
        label=f"replay certificate {name!r}",
        limit=MAX_ARTIFACT_BYTES,
    )
    if (
        type(artifact.get("bytes")) is not int
        or artifact["bytes"] != len(raw)
        or type(artifact.get("sha256")) is not str
        or _sha256_bytes(raw) != artifact["sha256"]
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"replay certificate identity drifted for {name!r}"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=ARTIFACT_DECODE_MAX_NODES,
            max_depth=ARTIFACT_DECODE_MAX_DEPTH,
        )
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot decode replay certificate {name!r}"
        ) from exc
    if (
        type(fuel) is not int
        or fuel != artifact.get("fuel")
        or _sha256_bytes(encode_formula(target)) != row.get("formula_sha256")
        or _sha256_bytes(encode_proof(proof)) != row.get("proof_term_sha256")
        or encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        != raw
        or not check((), proof, target)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"replay certificate failed exact kernel replay for {name!r}"
        )
    return DependencyCertificate(name=name, target=target, proof=proof)


def _decode_a22_certificate(
    name: str,
    *,
    a22_rows: Mapping[str, dict[str, object]],
    replay_rows: Mapping[str, dict[str, object]],
) -> DependencyCertificate:
    row = a22_rows.get(name)
    replay_row = replay_rows.get(name)
    if type(row) is not dict or type(replay_row) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2 modular certificate is missing for {name!r}"
        )
    artifact = row.get("rebuilt_certificate")
    encoded = None if type(artifact) is not dict else artifact.get("artifact_base64")
    if type(encoded) is not str:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2 artifact payload is malformed for {name!r}"
        )
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2 artifact base64 is malformed for {name!r}"
        ) from exc
    if (
        base64.b64encode(raw).decode("ascii") != encoded
        or len(raw) != artifact.get("artifact_bytes")
        or _sha256_bytes(raw) != artifact.get("artifact_sha256")
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2 artifact identity drifted for {name!r}"
        )
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=ARTIFACT_DECODE_MAX_NODES,
            max_depth=ARTIFACT_DECODE_MAX_DEPTH,
        )
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot decode A2.2 artifact for {name!r}"
        ) from exc
    if (
        fuel != artifact.get("fuel")
        or _sha256_bytes(encode_formula(target)) != replay_row.get("formula_sha256")
        or _sha256_bytes(encode_proof(proof)) != artifact.get("proof_term_sha256")
        or encode_artifact_bounded(
            fuel, target, proof, max_bytes=MAX_ARTIFACT_BYTES
        )
        != raw
        or not check((), proof, target)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2 artifact failed exact replay for {name!r}"
        )
    return DependencyCertificate(name=name, target=target, proof=proof)


def _candidate_body_receipt(
    body: CandidateBodyCompilation, *, dependencies: tuple[str, ...]
) -> dict[str, object]:
    if type(body) is not CandidateBodyCompilation or not check(
        (), body.certificate, body.target
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "fresh candidate body failed its dependency-curried kernel check"
        )
    receipt = body.receipt
    if receipt.dependency_count != len(dependencies):
        raise LibraryPilotDependencyVectorAuditError(
            "fresh candidate body dependency count drifted"
        )
    return {
        "certificate_sha256": _sha256_bytes(encode_proof(body.certificate)),
        "command_count": receipt.command_count,
        "dependency_count": receipt.dependency_count,
        "proof_depth": receipt.proof_depth,
        "proof_edges": receipt.proof_edges,
        "proof_nodes": receipt.proof_nodes,
        "proof_objects": receipt.proof_objects,
        "reused_objects": receipt.reused_objects,
        "target_formula_sha256": _sha256_bytes(encode_formula(body.target)),
    }


def _proof_receipt(target: Formula, proof: Proof) -> dict[str, object]:
    if not check((), proof, target):
        raise LibraryPilotDependencyVectorAuditError(
            "candidate proof failed the empty-context kernel check"
        )
    metrics = proof_tree_metrics(proof)
    return {
        "formula_sha256": _sha256_bytes(encode_formula(target)),
        "kernel_accepted": True,
        "kernel_context": "empty",
        "logic_mode": LOGIC_MODE,
        "metrics": metrics,
        "proof_term_sha256": _sha256_bytes(encode_proof(proof)),
    }


_STABLE_BODY_RECEIPT_FIELDS = [
    "certificate_representation",
    "certificate_sha256",
    "dependency_count",
    "kernel_accepted",
    "metrics.proof_depth",
    "metrics.proof_nodes",
    "target_formula_sha256",
]


def _accepted_a21_attempt(
    audit_row: Mapping[str, object], *, name: str
) -> dict[str, object] | None:
    recipe = audit_row.get("recipe_audit")
    attempts = None if type(recipe) is not dict else recipe.get("attempts")
    if type(attempts) is not list:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.1 attempt list is malformed for {name!r}"
        )
    accepted = [
        row
        for row in attempts
        if type(row) is dict and row.get("outcome") == "kernel-accepted"
    ]
    if not accepted:
        return None
    if len(accepted) != 1 or type(accepted[0].get("positive_receipt")) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.1 accepted omission is non-unique or malformed for {name!r}"
        )
    return accepted[0]


def _expected_modular_body_receipt(
    name: str,
    *,
    audit_row: Mapping[str, object],
    rebuild_row: Mapping[str, object] | None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Reconstruct the exact retained A2.1/A2.2 body-receipt route."""

    accepted_attempt = _accepted_a21_attempt(audit_row, name=name)
    readable_container = audit_row.get("readable")
    recipe = audit_row.get("recipe_audit")
    readable = (
        None
        if type(readable_container) is not dict
        else readable_container.get("proof")
    )
    initial = None if type(recipe) is not dict else recipe.get("positive_receipt")
    if type(readable) is not dict or type(initial) is not dict or readable != initial:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.1 initial readable body receipt drifted for {name!r}"
        )
    if rebuild_row is None:
        if accepted_attempt is not None:
            raise LibraryPilotDependencyVectorAuditError(
                f"accepted A2.1 omission lacks an A2.2 rebuild for {name!r}"
            )
        if (
            type(recipe) is not dict
            or tuple(recipe.get("initial_dependencies", ()))
            != tuple(audit_row.get("declared_dependencies", ()))
            or tuple(recipe.get("candidate_dependencies", ()))
            != tuple(audit_row.get("declared_dependencies", ()))
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"no-omission A2.1 vector drifted for {name!r}"
            )
        return initial, {
            "a2_1_initial_readable_receipt_sha256": readable["receipt_sha256"],
            "a2_1_recipe_audit_positive_receipt_sha256": initial[
                "receipt_sha256"
            ],
            "receipt_route": "no-accepted-omission-recipe-audit-fallback",
        }

    body = rebuild_row.get("body_receipt")
    accepted = (
        None
        if accepted_attempt is None
        else accepted_attempt.get("positive_receipt")
    )
    candidate_dependencies = tuple(
        rebuild_row.get("candidate_direct_dependencies", ())
    )
    retained_dependencies = tuple(
        rebuild_row.get("retained_direct_dependencies", ())
    )
    spine = rebuild_row.get("direct_cut_spine")
    omitted = None if type(spine) is not dict else spine.get(
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
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.2/last-accepted body receipt drifted for {name!r}"
        )
    return body, {
        "accepted_after_dependencies": list(candidate_dependencies),
        "accepted_omitted_dependency": omitted,
        "a2_1_initial_readable_receipt_sha256": readable["receipt_sha256"],
        "a2_1_last_accepted_receipt_sha256": accepted["receipt_sha256"],
        "a2_2_body_receipt_sha256": body["receipt_sha256"],
        "receipt_route": "a2.2-and-last-accepted-omission",
    }


def _compile_readable_candidate(
    root_name: str,
    direct_dependencies: tuple[str, ...],
    *,
    specs: Mapping[str, TheoremSpec],
    replay_rows: Mapping[str, dict[str, object]],
    dependency_certificates: Mapping[str, DependencyCertificate],
    fixed_vectors: Mapping[str, tuple[str, ...]] | None = None,
) -> _CandidateEvidence:
    spec = specs.get(root_name)
    if type(spec) is not TheoremSpec:
        raise LibraryPilotDependencyVectorAuditError("readable root spec is missing")
    selected = replace(spec, dependencies=direct_dependencies)
    # This explicit call is the first, shared preassembly observation.  The
    # closing helper deliberately replays it again before installing Cuts.
    body = compile_candidate_body(selected, core=specs)
    body_receipt = _candidate_body_receipt(body, dependencies=direct_dependencies)
    carriers = {
        name: dependency_certificates[name] for name in direct_dependencies
    }
    try:
        closed = compile_closed_candidate(
            selected, core=specs, dependency_certificates=carriers
        )
    except CandidateBodyError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "second readable body replay diverged after the shared baseline; "
            "treating as unknown and aborting"
        ) from exc
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "readable direct closure failed internally; aborting as unknown"
        ) from exc
    if (
        type(closed) is not ClosedCandidateCompilation
        or closed.body.target != body.target
        or encode_proof(closed.body.certificate) != encode_proof(body.certificate)
        or not check((), closed.proof, closed.target)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "readable direct closure returned an unknown/mismatched candidate"
        )
    closure = _transitive_closure(
        root_name,
        direct_dependencies,
        replay_rows=replay_rows,
        fixed_vectors=fixed_vectors,
    )
    certificate_rows = [
        {
            "formula_sha256": _sha256_bytes(
                encode_formula(dependency_certificates[name].target)
            ),
            "name": name,
            "proof_term_sha256": _sha256_bytes(
                encode_proof(dependency_certificates[name].proof)
            ),
        }
        for name in direct_dependencies
    ]
    provenance_preimage = {
        "format": "peano-hydra-readable-direct-certificate-provenance-preimage",
        "records": certificate_rows,
        "v": 1,
    }
    return _CandidateEvidence(
        target=closed.target,
        proof=closed.proof,
        direct_dependencies=direct_dependencies,
        closure=closure,
        diagnostics={
            "assembly": "compile_candidate_body-then-compile_closed_candidate",
            "direct_certificate_count": len(certificate_rows),
            "direct_certificate_provenance_preimage": provenance_preimage,
            "direct_certificate_provenance_root_sha256": _sha256_json(
                provenance_preimage, limit=MAX_SCHEMA_BYTES
            ),
            "root_body_receipt": body_receipt,
        },
    )


def _recover_selected_modular_body(
    name: str,
    *,
    root: Path,
    a21_rows: Mapping[str, dict[str, object]],
    a22_rows: Mapping[str, dict[str, object]],
    replay_rows: Mapping[str, dict[str, object]],
    specs: Mapping[str, TheoremSpec],
) -> tuple[Formula, tuple[str, ...], Proof, dict[str, object]]:
    replay_row = replay_rows[name]
    rebuild_row = a22_rows.get(name)
    if rebuild_row is None:
        certificate = _decode_replay_certificate(
            name, root=root, replay_rows=replay_rows
        )
        dependencies = tuple(replay_row.get("declared_dependencies", ()))
        artifact_sha256 = replay_row["artifact"]["sha256"]
        proof_term_sha256 = replay_row["proof_term_sha256"]
        kind = "retained-replay"
    else:
        certificate = _decode_a22_certificate(
            name, a22_rows=a22_rows, replay_rows=replay_rows
        )
        dependencies = tuple(rebuild_row.get("candidate_direct_dependencies", ()))
        artifact_sha256 = rebuild_row["rebuilt_certificate"]["artifact_sha256"]
        proof_term_sha256 = rebuild_row["rebuilt_certificate"][
            "proof_term_sha256"
        ]
        kind = "a2.2-direct-cut-rebuild"
    if not all(type(item) is str for item in dependencies):
        raise LibraryPilotDependencyVectorAuditError(
            f"retained modular vector is malformed for {name!r}"
        )
    audit_row = a21_rows.get(name)
    if type(audit_row) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            f"A2.1 body audit row is missing for {name!r}"
        )
    expected_receipt, receipt_source = _expected_modular_body_receipt(
        name, audit_row=audit_row, rebuild_row=rebuild_row
    )
    dependency_targets = {
        dependency: _closed_formula(specs[dependency].statement)
        for dependency in dependencies
    }
    dependency_hashes = {
        dependency: replay_rows[dependency]["proof_term_sha256"]
        for dependency in dependencies
    }
    recovered = recover_curried_modular_body(
        name=name,
        target=certificate.target,
        proof=certificate.proof,
        dependencies=dependencies,
        dependency_targets=dependency_targets,
        dependency_proof_sha256=dependency_hashes,
        expected_body_receipt=expected_receipt,
    )
    provenance = {
        **receipt_source,
        "a2_1_record_sha256": audit_row["record_sha256"],
        "artifact_sha256": artifact_sha256,
        "body_certificate_sha256": expected_receipt["certificate_sha256"],
        "dependencies": list(dependencies),
        "formula_sha256": replay_row["formula_sha256"],
        "index": replay_row["index"],
        "kind": kind,
        "name": name,
        "proof_term_sha256": proof_term_sha256,
        "identity_metrics_comparable": False,
        "source_identity_metrics_transportable": False,
        "stable_receipt_fields_compared": list(_STABLE_BODY_RECEIPT_FIELDS),
    }
    if rebuild_row is not None:
        provenance["a2_2_record_sha256"] = rebuild_row["record_sha256"]
    return recovered.target, dependencies, recovered.body, provenance


def _compile_layered_candidate(
    root_name: str,
    direct_dependencies: tuple[str, ...],
    *,
    root: Path,
    a21_rows: Mapping[str, dict[str, object]],
    a22_rows: Mapping[str, dict[str, object]] | None = None,
    replay_rows: Mapping[str, dict[str, object]],
    specs: Mapping[str, TheoremSpec],
) -> _CandidateEvidence:
    """Freshly regenerate the root before any closure/layered assembly."""

    spec = specs.get(root_name)
    if type(spec) is not TheoremSpec:
        raise LibraryPilotDependencyVectorAuditError("layered root spec is missing")
    selected = replace(spec, dependencies=direct_dependencies)
    # Required ordering: no baseline/root-body cache exists, and this global
    # callable runs before closure calculation or compile_layered_replay.
    root_body = compile_candidate_body(selected, core=specs)
    root_body_receipt = _candidate_body_receipt(
        root_body, dependencies=direct_dependencies
    )
    selected_a22 = {} if a22_rows is None else dict(a22_rows)
    fixed_vectors = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in selected_a22.items()
    }
    closure = _transitive_closure(
        root_name,
        direct_dependencies,
        replay_rows=replay_rows,
        fixed_vectors=fixed_vectors,
    )
    node_names = tuple(
        sorted((*closure, root_name), key=lambda item: replay_rows[item]["index"])
    )
    positions = {name: position for position, name in enumerate(node_names)}
    nodes: list[LayeredReplayNode] = []
    provenance: list[dict[str, object]] = []
    root_target = _closed_formula(spec.statement)
    for name in node_names:
        if name == root_name:
            target = root_target
            dependencies = direct_dependencies
            body = root_body.certificate
            source = {
                "body_certificate_sha256": root_body_receipt[
                    "certificate_sha256"
                ],
                "dependencies": list(dependencies),
                "formula_sha256": _sha256_bytes(encode_formula(target)),
                "index": replay_rows[name]["index"],
                "kind": "fresh-root-candidate-body",
                "name": name,
                "root_body_receipt": root_body_receipt,
            }
        else:
            try:
                target, dependencies, body, source = _recover_selected_modular_body(
                    name,
                    root=root,
                    a21_rows=a21_rows,
                    a22_rows=selected_a22,
                    replay_rows=replay_rows,
                    specs=specs,
                )
            except CandidateBodyError as exc:
                raise LibraryPilotDependencyVectorAuditError(
                    "unchanged modular-body recovery rejected unexpectedly; "
                    "aborting as unknown"
                ) from exc
        if any(dependency not in positions for dependency in dependencies):
            raise LibraryPilotDependencyVectorAuditError(
                f"layered closure omits a direct dependency of {name!r}"
            )
        nodes.append(
            LayeredReplayNode(
                positions[name],
                target,
                tuple(positions[dependency] for dependency in dependencies),
                body,
            )
        )
        provenance.append(source)
    compilation = _require_layered_candidate(
        compile_layered_replay(
            LayeredReplayBundle(tuple(nodes), positions[root_name]),
            root_target,
            limits=PILOT_LAYERED_LIMITS,
        ),
        root_name=root_name,
        phase="layered-compile",
    )
    if compilation.target != root_target or not check(
        (), compilation.certificate, root_target
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"layered candidate for {root_name!r} failed kernel-check; aborting"
        )
    tree = proof_tree_metrics(compilation.certificate)
    if (
        type(tree) is not dict
        or type(tree.get("proof_nodes")) is not int
        or type(tree.get("proof_depth")) is not int
        or type(tree.get("cut_nodes")) is not int
        or tree["proof_nodes"] != compilation.proof_nodes
        or tree["proof_depth"] != compilation.proof_depth
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "layered compiler proof metrics differ from independent traversal"
        )
    fuel = FUEL_MULTIPLIER * tree["proof_nodes"] + FUEL_OFFSET
    raw = encode_artifact_bounded(
        fuel,
        root_target,
        compilation.certificate,
        max_bytes=MAX_ARTIFACT_BYTES,
    )
    try:
        decoded_fuel, decoded_target, decoded_proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=ARTIFACT_DECODE_MAX_NODES,
            max_depth=ARTIFACT_DECODE_MAX_DEPTH,
        )
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "fresh layered artifact decode is unknown; aborting"
        ) from exc
    if (
        decoded_fuel != fuel
        or decoded_target != root_target
        or encode_proof(decoded_proof) != encode_proof(compilation.certificate)
        or encode_artifact_bounded(
            decoded_fuel,
            decoded_target,
            decoded_proof,
            max_bytes=MAX_ARTIFACT_BYTES,
        )
        != raw
        or not check((), decoded_proof, root_target)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "fresh layered artifact round trip failed; aborting as unknown"
        )
    provenance_preimage = {
        "format": "peano-hydra-layered-modular-provenance-preimage",
        "records": provenance,
        "v": 1,
    }
    body_identities = [
        {
            "body_certificate_sha256": row["body_certificate_sha256"],
            "dependencies": row["dependencies"],
            "index": row["index"],
            "name": row["name"],
        }
        for row in provenance
    ]
    body_identity_preimage = {
        "format": "peano-hydra-layered-modular-body-identities-preimage",
        "records": body_identities,
        "v": 1,
    }
    candidate_metrics = {
        "artifact_bytes": len(raw),
        "cut_nodes": tree["cut_nodes"],
        "proof_depth": tree["proof_depth"],
        "proof_nodes": tree["proof_nodes"],
    }
    return _CandidateEvidence(
        target=root_target,
        proof=decoded_proof,
        direct_dependencies=direct_dependencies,
        closure=closure,
        diagnostics={
            "artifact_bytes": len(raw),
            "artifact_sha256": _sha256_bytes(raw),
            "assembly": (
                "fresh-root-then-single-root-vector-override-with-fixed-a2.2-"
                "nonroot-vectors-then-layered-replay"
            ),
            "compiler_result_type": "LayeredReplayCandidate",
            "candidate_formula_sha256": _sha256_bytes(
                encode_formula(root_target)
            ),
            "candidate_metrics": candidate_metrics,
            "candidate_proof_term_sha256": _sha256_bytes(
                encode_proof(decoded_proof)
            ),
            "dependency_edge_count": sum(
                len(node.dependencies) for node in nodes
            ),
            "fuel": fuel,
            "fresh_body_sources": deepcopy(provenance),
            "layer_count": len(compilation.layers),
            "layers": [list(layer) for layer in compilation.layers],
            "modular_body_count": len(provenance),
            "modular_body_identity_preimage": body_identity_preimage,
            "modular_body_identity_root_sha256": _sha256_json(
                body_identity_preimage
            ),
            "modular_body_provenance_preimage": provenance_preimage,
            "modular_body_provenance_root_sha256": _sha256_json(
                provenance_preimage
            ),
            "maximum_package_formula_depth": (
                compilation.maximum_package_formula_depth
            ),
            "node_count": len(nodes),
            "node_names_in_replay_order": list(node_names),
            "node_names_lf_sha256": _lf_sha256(node_names),
            "package_formula_occurrences": (
                compilation.package_formula_occurrences
            ),
            "root_body_receipt": root_body_receipt,
        },
    )


def _validate_layered_baseline_parity(
    evidence: _CandidateEvidence, *, a23_row: Mapping[str, object]
) -> dict[str, object]:
    """Bind a fresh full-vector baseline to the retained A2.3a construction."""

    if type(evidence) is not _CandidateEvidence or type(a23_row) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            "layered baseline parity input is malformed"
        )
    layered = next(
        (
            row
            for row in a23_row.get("artifacts", ())
            if type(row) is dict and row.get("candidate_id") == "layered-closure"
        ),
        None,
    )
    bundle = a23_row.get("layered_bundle")
    diagnostics = evidence.diagnostics
    if type(layered) is not dict or type(bundle) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            "retained A2.3a layered baseline is malformed"
        )
    retained_sources = bundle.get("body_sources")
    if type(retained_sources) is not list:
        raise LibraryPilotDependencyVectorAuditError(
            "retained A2.3a body sources are malformed"
        )
    retained_identities = [
        {
            "body_certificate_sha256": row["body_certificate_sha256"],
            "dependencies": row["dependencies"],
            "index": row["index"],
            "name": row["name"],
        }
        for row in retained_sources
        if type(row) is dict
    ]
    retained_identity_preimage = {
        "format": "peano-hydra-layered-modular-body-identities-preimage",
        "records": retained_identities,
        "v": 1,
    }
    retained_sources_preimage = {
        "format": "peano-hydra-a2.3a-layered-body-sources-preimage",
        "records": retained_sources,
        "v": 1,
    }
    surface = layered.get("surface")
    metrics = layered.get("metrics")
    fresh_identity_preimage = diagnostics.get("modular_body_identity_preimage")
    fresh_provenance_preimage = diagnostics.get(
        "modular_body_provenance_preimage"
    )
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
                (
                    []
                    if type(fresh_identity_preimage) is not dict
                    else fresh_identity_preimage.get("records", [])
                ),
                retained_identities,
            )
        ],
        "stable_fields": stable_fields,
        "v": 1,
    }
    if (
        type(surface) is not dict
        or type(metrics) is not dict
        or type(fresh_identity_preimage) is not dict
        or type(fresh_provenance_preimage) is not dict
        or fresh_identity_preimage.get("records") != retained_identities
        or len(retained_identities) != len(retained_sources)
        or diagnostics.get("modular_body_identity_root_sha256")
        != _sha256_json(fresh_identity_preimage)
        or diagnostics.get("modular_body_provenance_root_sha256")
        != _sha256_json(fresh_provenance_preimage)
        or diagnostics.get("artifact_sha256") != layered.get("artifact_sha256")
        or diagnostics.get("artifact_bytes") != layered.get("metrics", {}).get(
            "artifact_bytes"
        )
        or diagnostics.get("candidate_formula_sha256")
        != layered.get("formula_sha256")
        or diagnostics.get("candidate_proof_term_sha256")
        != layered.get("proof_term_sha256")
        or diagnostics.get("candidate_metrics") != metrics
        or diagnostics.get("fuel") != layered.get("fuel")
        or diagnostics.get("compiler_result_type")
        != bundle.get("compiler_result_type")
        or diagnostics.get("layer_count") != bundle.get("layer_count")
        or diagnostics.get("node_names_in_replay_order")
        != bundle.get("node_names_in_replay_order")
        or diagnostics.get("node_names_lf_sha256")
        != bundle.get("node_names_lf_sha256")
        or diagnostics.get("layers") != bundle.get("layers")
        or diagnostics.get("node_count") != bundle.get("node_count")
        or diagnostics.get("dependency_edge_count")
        != bundle.get("dependency_edge_count")
        or diagnostics.get("maximum_package_formula_depth")
        != bundle.get("maximum_package_formula_depth")
        or diagnostics.get("package_formula_occurrences")
        != bundle.get("package_formula_occurrences")
        or diagnostics.get("modular_body_identity_root_sha256")
        != _sha256_json(retained_identity_preimage)
        or tuple(evidence.direct_dependencies)
        != tuple(surface.get("direct_dependencies", ()))
        or tuple(evidence.closure)
        != tuple(
            surface.get("transitive_closure_dependencies_in_replay_order", ())
        )
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "fresh layered baseline differs from exact retained A2.3a construction"
        )
    return {
        "a2_3a_body_sources_preimage": retained_sources_preimage,
        "a2_3a_body_sources_root_sha256": _sha256_json(
            retained_sources_preimage
        ),
        "a2_3a_candidate_record_sha256": a23_row["record_sha256"],
        "a2_3a_layered_artifact_sha256": layered["artifact_sha256"],
        "fresh_body_provenance_root_sha256": diagnostics[
            "modular_body_provenance_root_sha256"
        ],
        "retained_body_sources_root_sha256": _sha256_json(
            retained_sources_preimage
        ),
        "stable_body_identity_fields": stable_fields,
        "stable_body_identity_join_preimage": stable_join_preimage,
        "stable_body_identity_join_root_sha256": _sha256_json(
            stable_join_preimage
        ),
        "stable_body_identity_root_sha256": diagnostics[
            "modular_body_identity_root_sha256"
        ],
        "status": (
            "exact-candidate-and-stable-body-identity-parity-with-distinct-"
            "provenance"
        ),
    }


TERMINAL_STAGES = (
    "root-body-regeneration",
    "direct-closure",
    "closure-recompute",
    "modular-recovery",
    "layered-compile",
    "kernel-check",
)


def _callable_limits_identity() -> dict[str, object]:
    schema = pilot_dependency_vector_audit_schema()
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


def _baseline_receipt(
    *,
    route: str,
    name: str,
    index: int,
    evidence: _CandidateEvidence,
    basis: str,
) -> dict[str, object]:
    proof = _proof_receipt(evidence.target, evidence.proof)
    surface = _dependency_surface(
        evidence.direct_dependencies, evidence.closure, basis=basis
    )
    diagnostics = deepcopy(dict(evidence.diagnostics))
    preimage = {
        "diagnostics": diagnostics,
        "format": BASELINE_RECEIPT_PREIMAGE_FORMAT,
        "index": index,
        "name": name,
        "proof": proof,
        "route": route,
        "surface": surface,
        "v": 1,
    }
    return {
        "diagnostics": diagnostics,
        "preimage": preimage,
        "proof": proof,
        "sha256": _sha256_json(preimage),
        "status": "kernel-accepted-baseline",
        "surface": surface,
    }


def _attempt_record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _shared_root_body_observation(
    *,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    classification: Mapping[str, object],
) -> tuple[dict[str, object], str]:
    preimage = {
        "candidate_body_compiler_source_sha256": (
            "b41e6587d32e27152e1358b3067c72b869357674548f05aa4ef5e86cf9bdc30a"
        ),
        "dependencies": list(dependencies),
        "failure": classification["failure"],
        "format": "peano-hydra-shared-root-body-observation-preimage",
        "index": index,
        "name": name,
        "v": 1,
    }
    return preimage, _sha256_json(preimage, limit=MAX_SCHEMA_BYTES)


def _attempt_records_bundle(
    route: str, name: str, records: list[dict[str, object]]
) -> dict[str, object]:
    identities = [
        {
            "attempt_index": row["attempt_index"],
            "omitted_dependency": row["omitted_dependency"],
            "record_sha256": row["record_sha256"],
        }
        for row in records
    ]
    preimage = {
        "format": ATTEMPT_RECORDS_PREIMAGE_FORMAT,
        "name": name,
        "records": identities,
        "route": route,
        "v": 1,
    }
    return {
        "count": len(records),
        "preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def _audit_route(
    *,
    route: str,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    producer_source_state_root_sha256: str,
    compile_vector: Callable[[tuple[str, ...]], _CandidateEvidence],
    closure_for_vector: Callable[[tuple[str, ...]], tuple[str, ...]],
    baseline_validator: Callable[
        [_CandidateEvidence], Mapping[str, object]
    ]
    | None = None,
) -> dict[str, object]:
    if route not in (READABLE_ROUTE, PROPOSED_LAYERED_ROUTE):
        raise LibraryPilotDependencyVectorAuditError("route is not registered")
    try:
        baseline_evidence = compile_vector(dependencies)
    except Exception as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"{route} baseline did not kernel-pass for {name!r}; aborting"
        ) from exc
    if (
        type(baseline_evidence) is not _CandidateEvidence
        or baseline_evidence.direct_dependencies != dependencies
        or baseline_evidence.closure != closure_for_vector(dependencies)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            f"{route} baseline surface drifted for {name!r}"
        )
    if baseline_validator is not None:
        parity = baseline_validator(baseline_evidence)
        if type(parity) is not dict:
            raise LibraryPilotDependencyVectorAuditError(
                f"{route} baseline parity receipt is malformed"
            )
        baseline_evidence = _CandidateEvidence(
            target=baseline_evidence.target,
            proof=baseline_evidence.proof,
            direct_dependencies=baseline_evidence.direct_dependencies,
            closure=baseline_evidence.closure,
            diagnostics={
                **dict(baseline_evidence.diagnostics),
                "retained_baseline_parity": deepcopy(parity),
            },
        )
    basis = (
        "readable-literal-direct-cut-closure"
        if route == READABLE_ROUTE
        else "proposed-layered-root-input-graph-not-final-cut-spine"
    )
    baseline = _baseline_receipt(
        route=route,
        name=name,
        index=index,
        evidence=baseline_evidence,
        basis=basis,
    )
    script_sha256 = _sha256_bytes(
        ("\n".join(script) + ("\n" if script else "")).encode("utf-8")
    )
    baseline_formula_sha256 = baseline["proof"]["formula_sha256"]
    baseline_root_body_sha256 = baseline["diagnostics"]["root_body_receipt"][
        "certificate_sha256"
    ]
    records: list[dict[str, object]] = []
    for attempt_index, (omitted, candidate) in enumerate(
        _single_omission_vectors(dependencies)
    ):
        try:
            evidence = compile_vector(candidate)
        except CandidateBodyError as exc:
            classification = _classify_attempt_error(exc, script=script)
            # The deterministic surface is recomputed only after the fresh
            # root-body attempt.  No route-specific assembler ran.
            closure = closure_for_vector(candidate)
            shared_preimage, shared_digest = _shared_root_body_observation(
                name=name,
                index=index,
                dependencies=candidate,
                classification=classification,
            )
            row: dict[str, object] = {
                "after_dependencies": list(dependencies),
                "attempted_dependencies": list(candidate),
                "attempt_index": attempt_index,
                "baseline_formula_sha256": baseline_formula_sha256,
                "baseline_root_body_certificate_sha256": (
                    baseline_root_body_sha256
                ),
                "before_dependencies": list(dependencies),
                "failure": classification["failure"],
                "index": index,
                "layered_compiler_invoked": False,
                "name": name,
                "omitted_dependency": omitted,
                "outcome": "exact-route-rejected",
                "route": route,
                "route_specific_assembly_reached": False,
                "script_sha256": script_sha256,
                "shared_root_body_observation_preimage": shared_preimage,
                "shared_root_body_observation_sha256": shared_digest,
                "trial_surface": _dependency_surface(
                    candidate, closure, basis=basis
                ),
                "terminal_stage": "root-body-regeneration",
            }
        except LibraryPilotDependencyVectorAuditError:
            raise
        except Exception as exc:
            raise LibraryPilotDependencyVectorAuditError(
                f"{route} omission produced an unknown internal outcome for "
                f"{name!r}; aborting"
            ) from exc
        else:
            if (
                type(evidence) is not _CandidateEvidence
                or evidence.direct_dependencies != candidate
                or evidence.closure != closure_for_vector(candidate)
            ):
                raise LibraryPilotDependencyVectorAuditError(
                    f"{route} omission surface drifted for {name!r}"
                )
            row = {
                "after_dependencies": list(candidate),
                "attempted_dependencies": list(candidate),
                "attempt_index": attempt_index,
                "baseline_formula_sha256": baseline_formula_sha256,
                "baseline_root_body_certificate_sha256": (
                    baseline_root_body_sha256
                ),
                "before_dependencies": list(dependencies),
                "diagnostics": deepcopy(dict(evidence.diagnostics)),
                "failure": None,
                "index": index,
                "layered_compiler_invoked": route == PROPOSED_LAYERED_ROUTE,
                "name": name,
                "omitted_dependency": omitted,
                "outcome": "kernel-accepted",
                "proof": _proof_receipt(evidence.target, evidence.proof),
                "route": route,
                "route_specific_assembly_reached": True,
                "script_sha256": script_sha256,
                "shared_root_body_observation_preimage": None,
                "shared_root_body_observation_sha256": None,
                "trial_surface": _dependency_surface(
                    candidate, evidence.closure, basis=basis
                ),
                "terminal_stage": "kernel-check",
            }
        if row["terminal_stage"] not in TERMINAL_STAGES:
            raise LibraryPilotDependencyVectorAuditError(
                "attempt terminal stage is not registered"
            )
        row["record_sha256"] = _attempt_record_hash(row)
        records.append(row)
    attempts = _attempt_records_bundle(route, name, records)
    root_body = baseline["diagnostics"].get("root_body_receipt")
    if type(root_body) is not dict or type(
        root_body.get("certificate_sha256")
    ) is not str:
        raise LibraryPilotDependencyVectorAuditError(
            "baseline root-body receipt is malformed"
        )
    callable_limits = _callable_limits_identity()
    route_preimage = _route_preimage(
        route=route,
        name=name,
        index=index,
        dependencies=dependencies,
        attempts_root_sha256=attempts["root_sha256"],
        baseline_receipt_sha256=baseline["sha256"],
        formula_sha256=baseline["proof"]["formula_sha256"],
        direct_dependencies_lf_sha256=baseline["surface"][
            "direct_dependencies_lf_sha256"
        ],
        baseline_closure_lf_sha256=baseline["surface"][
            "transitive_closure_lf_sha256"
        ],
        root_body_certificate_sha256=root_body["certificate_sha256"],
        producer_source_state_root_sha256=producer_source_state_root_sha256,
        implementation_source_root_sha256=IMPLEMENTATION_SOURCE_ROOT_SHA256,
        callable_limits_sha256=callable_limits["sha256"],
    )
    return {
        "attempt_records": attempts,
        "attempts": records,
        "baseline": baseline,
        "route": route,
        "route_receipt_preimage": route_preimage,
        "route_receipt_sha256": _sha256_json(route_preimage),
        "single_omission_kernel_accepted_count": sum(
            row["outcome"] == "kernel-accepted" for row in records
        ),
        "single_omission_rejected_count": sum(
            row["outcome"] == "exact-route-rejected" for row in records
        ),
        "status": "bounded-route-audit-complete",
    }


def _audit_readable_route(
    *,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    producer_source_state_root_sha256: str,
    compile_vector: Callable[[tuple[str, ...]], _CandidateEvidence],
    closure_for_vector: Callable[[tuple[str, ...]], tuple[str, ...]],
    baseline_validator: Callable[
        [_CandidateEvidence], Mapping[str, object]
    ]
    | None = None,
) -> dict[str, object]:
    return _audit_route(
        route=READABLE_ROUTE,
        name=name,
        index=index,
        dependencies=dependencies,
        script=script,
        producer_source_state_root_sha256=producer_source_state_root_sha256,
        compile_vector=compile_vector,
        closure_for_vector=closure_for_vector,
        baseline_validator=baseline_validator,
    )


def _audit_layered_route(
    *,
    name: str,
    index: int,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    producer_source_state_root_sha256: str,
    compile_vector: Callable[[tuple[str, ...]], _CandidateEvidence],
    closure_for_vector: Callable[[tuple[str, ...]], tuple[str, ...]],
    baseline_validator: Callable[
        [_CandidateEvidence], Mapping[str, object]
    ]
    | None = None,
) -> dict[str, object]:
    return _audit_route(
        route=PROPOSED_LAYERED_ROUTE,
        name=name,
        index=index,
        dependencies=dependencies,
        script=script,
        producer_source_state_root_sha256=producer_source_state_root_sha256,
        compile_vector=compile_vector,
        closure_for_vector=closure_for_vector,
        baseline_validator=baseline_validator,
    )


def _validate_cross_route_shared_body_consistency(
    readable_route: Mapping[str, object], layered_route: Mapping[str, object]
) -> dict[str, object]:
    """Require deterministic shared root-body replay across both assemblers."""

    try:
        readable_baseline_body = readable_route["baseline"]["diagnostics"][  # type: ignore[index]
            "root_body_receipt"
        ]
        layered_baseline_body = layered_route["baseline"]["diagnostics"][  # type: ignore[index]
            "root_body_receipt"
        ]
        readable_attempts = readable_route["attempts"]
        layered_attempts = layered_route["attempts"]
    except (KeyError, TypeError) as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "cross-route shared body evidence is malformed"
        ) from exc
    if (
        type(readable_baseline_body) is not dict
        or type(layered_baseline_body) is not dict
        or readable_baseline_body != layered_baseline_body
        or type(readable_attempts) is not list
        or type(layered_attempts) is not list
        or len(readable_attempts) != len(layered_attempts)
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "cross-route baseline root-body replay diverged"
        )
    for readable, layered in zip(
        readable_attempts, layered_attempts, strict=True
    ):
        if (
            type(readable) is not dict
            or type(layered) is not dict
            or readable.get("attempt_index") != layered.get("attempt_index")
            or readable.get("omitted_dependency")
            != layered.get("omitted_dependency")
            or readable.get("attempted_dependencies")
            != layered.get("attempted_dependencies")
            or readable.get("outcome") != layered.get("outcome")
        ):
            raise LibraryPilotDependencyVectorAuditError(
                "cross-route shared body outcome diverged; aborting as unknown"
            )
        if readable["outcome"] == "exact-route-rejected":
            if (
                type(readable.get("shared_root_body_observation_sha256"))
                is not str
                or readable["shared_root_body_observation_sha256"]
                != layered.get("shared_root_body_observation_sha256")
            ):
                raise LibraryPilotDependencyVectorAuditError(
                    "cross-route shared root-body rejection digest diverged"
                )
        elif readable["outcome"] == "kernel-accepted":
            readable_body = readable.get("diagnostics", {}).get(  # type: ignore[union-attr]
                "root_body_receipt"
            )
            layered_body = layered.get("diagnostics", {}).get(  # type: ignore[union-attr]
                "root_body_receipt"
            )
            if (
                type(readable_body) is not dict
                or type(layered_body) is not dict
                or readable_body != layered_body
            ):
                raise LibraryPilotDependencyVectorAuditError(
                    "cross-route accepted root-body replay diverged"
                )
        else:
            raise LibraryPilotDependencyVectorAuditError(
                "cross-route shared body outcome is unknown"
            )
    baseline_preimage = {
        "format": "peano-hydra-cross-route-shared-baseline-body-preimage",
        "root_body_receipt": readable_baseline_body,
        "v": 1,
    }
    return {
        "baseline_root_body_receipt_sha256": _sha256_json(baseline_preimage),
        "paired_attempt_count": len(readable_attempts),
        "status": "shared-root-body-consistent",
    }


_GLOBAL_FALSE_FIELDS = (
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


def _false_claims() -> dict[str, bool]:
    return {field: False for field in _GLOBAL_FALSE_FIELDS}


def _require_complete_attempt_aggregate(
    *, total_attempts: int, total_rejected: int, total_accepted: int
) -> dict[str, object]:
    """Fail closed unless every bounded attempt terminated as an exact rejection.

    This is execution completeness for the frozen protocol, not dependency-vector
    completeness, minimality, necessity, or optimizer evidence.
    """

    if (
        type(total_attempts) is not int
        or type(total_rejected) is not int
        or type(total_accepted) is not int
        or min(total_attempts, total_rejected, total_accepted) < 0
        or total_attempts != EXPECTED_ATTEMPT_COUNT
        or total_rejected != EXPECTED_ATTEMPT_COUNT
        or total_accepted != 0
        or total_rejected + total_accepted != total_attempts
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "bounded protocol is incomplete or produced an accepted/unknown "
            "omission; refusing a terminal result"
        )
    return {
        "bounded_protocol_executed": True,
        "bounded_three_root_vector_audit_complete": False,
        "single_omission_terminal_count": EXPECTED_ATTEMPT_COUNT,
        "terminal_route_observations_complete": True,
    }


def _record_hash(value: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: item for key, item in value.items() if key != "record_sha256"}
    )


def _build_candidate_pilot_dependency_vector_audit(
    root: Path, *, producer_source_state: Mapping[str, object]
) -> dict[str, object]:
    producer = _validate_producer_source_state(producer_source_state, root=root)
    fixed = _load_fixed_inputs(root)
    a21_rows = fixed["a21_rows"]
    a22_rows = fixed["a22_rows"]
    a23_rows = fixed["a23_rows"]
    replay_rows = fixed["replay_rows"]
    specs = fixed["specs"]
    readable_fixed_vectors = {
        name: tuple(row["readable"]["dependencies"])
        for name, row in a21_rows.items()
    }
    layered_fixed_vectors = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in a22_rows.items()
    }
    certificate_cache: dict[str, DependencyCertificate] = {}
    result_rows: list[dict[str, object]] = []
    total_attempts = 0
    total_rejected = 0
    total_accepted = 0
    producer_root = producer["root_sha256"]

    for index, name in EXPECTED_ROOTS:
        spec = specs[name]
        readable_dependencies = tuple(a21_rows[name]["readable"]["dependencies"])
        layered_artifact = next(
            row
            for row in a23_rows[name]["artifacts"]
            if row["candidate_id"] == "layered-closure"
        )
        proposed_dependencies = tuple(
            layered_artifact["surface"]["direct_dependencies"]
        )
        if (
            readable_dependencies != EXPECTED_DIRECT[name]
            or proposed_dependencies != EXPECTED_DIRECT[name]
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"pilot vector drifted for {name!r}"
            )
        for dependency in _ordered_union(
            readable_dependencies, proposed_dependencies
        ):
            if dependency not in certificate_cache:
                certificate_cache[dependency] = _decode_replay_certificate(
                    dependency, root=root, replay_rows=replay_rows
                )

        def readable_compile(
            vector: tuple[str, ...], *, _name: str = name
        ) -> _CandidateEvidence:
            return _compile_readable_candidate(
                _name,
                vector,
                specs=specs,
                replay_rows=replay_rows,
                dependency_certificates=certificate_cache,
                fixed_vectors=readable_fixed_vectors,
            )

        def readable_closure(
            vector: tuple[str, ...], *, _name: str = name
        ) -> tuple[str, ...]:
            return _transitive_closure(
                _name,
                vector,
                replay_rows=replay_rows,
                fixed_vectors=readable_fixed_vectors,
            )

        def layered_compile(
            vector: tuple[str, ...], *, _name: str = name
        ) -> _CandidateEvidence:
            return _compile_layered_candidate(
                _name,
                vector,
                root=root,
                a21_rows=a21_rows,
                a22_rows=a22_rows,
                replay_rows=replay_rows,
                specs=specs,
            )

        def layered_closure(
            vector: tuple[str, ...], *, _name: str = name
        ) -> tuple[str, ...]:
            return _transitive_closure(
                _name,
                vector,
                replay_rows=replay_rows,
                fixed_vectors=layered_fixed_vectors,
            )

        readable_route = _audit_readable_route(
            name=name,
            index=index,
            dependencies=readable_dependencies,
            script=spec.script,
            producer_source_state_root_sha256=producer_root,
            compile_vector=readable_compile,
            closure_for_vector=readable_closure,
        )
        layered_route = _audit_layered_route(
            name=name,
            index=index,
            dependencies=proposed_dependencies,
            script=spec.script,
            producer_source_state_root_sha256=producer_root,
            compile_vector=layered_compile,
            closure_for_vector=layered_closure,
            baseline_validator=lambda evidence, _row=a23_rows[name]: (
                _validate_layered_baseline_parity(evidence, a23_row=_row)
            ),
        )
        expected_closure = tuple(
            layered_artifact["surface"][
                "transitive_closure_dependencies_in_replay_order"
            ]
        )
        if tuple(
            layered_route["baseline"]["surface"][
                "transitive_closure_dependencies_in_replay_order"
            ]
        ) != expected_closure:
            raise LibraryPilotDependencyVectorAuditError(
                f"layered baseline closure drifted for {name!r}"
            )
        readable_formula = readable_route["baseline"]["proof"][
            "formula_sha256"
        ]
        layered_formula = layered_route["baseline"]["proof"][
            "formula_sha256"
        ]
        if (
            readable_formula != replay_rows[name]["formula_sha256"]
            or layered_formula != replay_rows[name]["formula_sha256"]
            or readable_formula != layered_formula
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"cross-route baseline formula drifted for {name!r}"
            )
        shared_body_consistency = _validate_cross_route_shared_body_consistency(
            readable_route, layered_route
        )
        attempts = len(readable_route["attempts"]) + len(
            layered_route["attempts"]
        )
        rejected = (
            readable_route["single_omission_rejected_count"]
            + layered_route["single_omission_rejected_count"]
        )
        accepted = (
            readable_route["single_omission_kernel_accepted_count"]
            + layered_route["single_omission_kernel_accepted_count"]
        )
        total_attempts += attempts
        total_rejected += rejected
        total_accepted += accepted
        local_union = _ordered_union(
            readable_dependencies, proposed_dependencies
        )
        local_union_preimage = {
            "format": "peano-hydra-bounded-local-dependency-union-preimage",
            "index": index,
            "name": name,
            "proposed_layered_dependencies": list(proposed_dependencies),
            "readable_dependencies": list(readable_dependencies),
            "union": list(local_union),
            "v": 1,
        }
        row: dict[str, object] = {
            **_false_claims(),
            "bounded_local_union": {
                "dependencies": list(local_union),
                "dependency_count": len(local_union),
                "preimage": local_union_preimage,
                "root_sha256": _sha256_json(local_union_preimage),
                "scope": "bounded-pilot-root-only-not-publication-verified",
            },
            "bounded_protocol_executed": True,
            "bounded_three_root_vector_audit_complete": False,
            "index": index,
            "name": name,
            "routes": [readable_route, layered_route],
            "shared_body_consistency": shared_body_consistency,
            "single_omission_attempt_count": attempts,
            "single_omission_kernel_accepted_count": accepted,
            "single_omission_rejected_count": rejected,
            "single_omission_terminal_count": rejected,
            "terminal_route_observations_complete": accepted == 0
            and rejected == attempts,
            "statement": {
                "formula_sha256": replay_rows[name]["formula_sha256"],
                "statement_canonical_sha256": replay_rows[name][
                    "statement_canonical_sha256"
                ],
                "statement_source_sha256": replay_rows[name][
                    "statement_source_sha256"
                ],
            },
        }
        row["record_sha256"] = _record_hash(row)
        result_rows.append(row)

    completion = _require_complete_attempt_aggregate(
        total_attempts=total_attempts,
        total_rejected=total_rejected,
        total_accepted=total_accepted,
    )
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
        "count": THEOREM_COUNT,
        "preimage": records_preimage,
        "root_sha256": _sha256_json(records_preimage),
    }
    callable_limits = _callable_limits_identity()
    input_rows = {
        label: {
            "artifact_path": relative.as_posix(),
            "artifact_sha256": artifact_sha,
            "root_sha256": root_sha,
            "theorem_record_root_sha256": records_sha,
        }
        for label, (
            relative,
            artifact_sha,
            root_sha,
            records_sha,
        ) in _FIXED_INPUTS.items()
    }
    input_rows["replay"] = {
        "manifest_artifact_path": _REPLAY_MANIFEST_RELATIVE.as_posix(),
        "manifest_artifact_sha256": REPLAY_MANIFEST_ARTIFACT_SHA256,
        "manifest_root_sha256": REPLAY_MANIFEST_ROOT_SHA256,
        "replay_report_artifact_path": _REPLAY_REPORT_RELATIVE.as_posix(),
        "replay_report_artifact_sha256": REPLAY_REPORT_ARTIFACT_SHA256,
        "replay_root_sha256": REPLAY_ROOT_SHA256,
    }
    body: dict[str, object] = {
        **_false_claims(),
        "aggregate": {
            "bounded_local_union_edges": sum(
                row["bounded_local_union"]["dependency_count"]
                for row in result_rows
            ),
            "kernel_accepted_baseline_count": THEOREM_COUNT * 2,
            "pilot_theorem_count": THEOREM_COUNT,
            "retained_public_graph_edges": RETAINED_PUBLIC_GRAPH_EDGES,
            "route_count": 2,
            "single_omission_attempt_count": total_attempts,
            "single_omission_kernel_accepted_count": total_accepted,
            "single_omission_rejected_count": total_rejected,
            "single_omission_terminal_count": total_rejected,
        },
        "bounded_three_root_protocol_frozen": True,
        **completion,
        "format": PILOT_DEPENDENCY_VECTOR_AUDIT_FORMAT,
        "id": PILOT_DEPENDENCY_VECTOR_AUDIT_ID,
        "implementation": {
            "callable_limits_identity": callable_limits,
            "live_theorem_transport": fixed["theorem_transport"],
            "source_root_sha256": IMPLEMENTATION_SOURCE_ROOT_SHA256,
            "sources": _implementation_rows(),
        },
        "inputs": input_rows,
        "logic_mode": LOGIC_MODE,
        "producer_git_verified": False,
        "producer_source_state": producer,
        "producer_source_state_sha256": _sha256_json(
            producer, limit=MAX_SCHEMA_BYTES
        ),
        "schema": pilot_dependency_vector_audit_schema_identity(),
        "status": STATUS,
        "theorem_count": THEOREM_COUNT,
        "theorem_records": theorem_records,
        "v": PILOT_DEPENDENCY_VECTOR_AUDIT_VERSION,
    }
    root_preimage = {
        "format": PILOT_DEPENDENCY_VECTOR_AUDIT_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": PILOT_DEPENDENCY_VECTOR_AUDIT_VERSION,
    }
    return {
        **body,
        "root_preimage": root_preimage,
        "root_sha256": _sha256_json(root_preimage),
        "theorems": result_rows,
    }


def build_candidate_pilot_dependency_vector_audit(
    *,
    producer_source_state: Mapping[str, object],
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Build the exact bounded candidate protocol; unknown outcomes abort."""

    pilot_dependency_vector_audit_schema()
    result = _build_candidate_pilot_dependency_vector_audit(
        _repository_root(repository_root),
        producer_source_state=producer_source_state,
    )
    canonical_document_bytes(result)
    return deepcopy(result)


def validate_candidate_pilot_dependency_vector_audit(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate by exact reconstruction from pinned inputs and source state."""

    pilot_dependency_vector_audit_schema()
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit must be one object"
        )
    _validate_json(value)
    producer = value.get("producer_source_state")
    if type(producer) is not dict:
        raise LibraryPilotDependencyVectorAuditError(
            "audit differs from fixed-source reconstruction: missing source state"
        )
    expected = _build_candidate_pilot_dependency_vector_audit(
        _repository_root(repository_root), producer_source_state=producer
    )
    if value != expected:
        raise LibraryPilotDependencyVectorAuditError(
            "audit differs from exact fixed-source reconstruction"
        )
    return _decode_document(
        canonical_document_bytes(expected),
        "validated pilot dependency-vector audit",
        limit=MAX_DOCUMENT_BYTES,
    )


def load_candidate_pilot_dependency_vector_audit(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one canonical audit and reconstruct all 44 route attempts."""

    raw = _read_regular_bytes(
        path, label="pilot dependency-vector audit", limit=MAX_DOCUMENT_BYTES
    )
    value = _decode_document(
        raw, "pilot dependency-vector audit", limit=MAX_DOCUMENT_BYTES
    )
    if canonical_document_bytes(value) != raw:
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit is not canonical"
        )
    return validate_candidate_pilot_dependency_vector_audit(
        value, repository_root=repository_root
    )


__all__ = [
    "EXPECTED_ATTEMPT_COUNT",
    "EXPECTED_ROOTS",
    "LibraryPilotDependencyVectorAuditError",
    "PILOT_DEPENDENCY_VECTOR_AUDIT_FORMAT",
    "PILOT_DEPENDENCY_VECTOR_AUDIT_ID",
    "PILOT_DEPENDENCY_VECTOR_AUDIT_ROOT_PREIMAGE_FORMAT",
    "PROPOSED_LAYERED_ROUTE",
    "READABLE_ROUTE",
    "build_candidate_pilot_dependency_vector_audit",
    "canonical_document_bytes",
    "load_candidate_pilot_dependency_vector_audit",
    "pilot_dependency_vector_audit_schema",
    "pilot_dependency_vector_audit_schema_identity",
    "validate_candidate_pilot_dependency_vector_audit",
]
