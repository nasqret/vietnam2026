"""Adversarial contracts for the bounded A2.3b vector-audit producer.

This file must stay synthetic and cheap.  It pins the three-root protocol and
exercises route/omission/transport helpers, but never rebuilds the retained
optimizer result or runs the real 44 proof attempts.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import training.peano_hydra.library_pilot_dependency_vector_audit as audit  # noqa: E402
from peano_lab.engine.proof_reduction import ProofReductionError  # noqa: E402
from peano_lab.engine.tactics import (  # noqa: E402
    InvalidProof,
    TacticError,
    TacticSyntaxError,
)
from peano_lab.library.candidate_validation import CandidateBodyError  # noqa: E402
from peano_lab.library.theorems import TheoremSpec  # noqa: E402


CLI_PATH = (
    ROOT / "scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py"
)
SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/library-pilot-dependency-vector-audit-schema-v1.json"
)
A21_PATH = ROOT / "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
A22_PATH = (
    ROOT / "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
)
A23_PATH = (
    ROOT / "artifacts/peano-hydra/l0-optimizer-comparison-pilot-candidate-v1.json"
)
A23_VERIFICATION_PATH = (
    ROOT
    / "artifacts/peano-hydra/"
    "l0-optimizer-comparison-pilot-independent-verification-v1.json"
)
REPLAY_MANIFEST_PATH = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
REPLAY_REPORT_PATH = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)

EXPECTED_ROOTS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
EXPECTED_DIRECT = {
    "odd_add_odd": (
        "mul_add",
        "add_assoc",
        "add_comm",
    ),
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
UPSTREAM_SHA256 = {
    A21_PATH: "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040",
    A22_PATH: "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182",
    A23_PATH: "3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b",
    A23_VERIFICATION_PATH: (
        "6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a"
    ),
    REPLAY_MANIFEST_PATH: (
        "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
    ),
    REPLAY_REPORT_PATH: (
        "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"
    ),
}
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

THEOREM_GENERATOR_SOURCE_ROWS = (
    (
        "peano-lab/py/peano_lab/library/parity.py",
        "f39325d72c0f29969b6e01cfd92451fe29f911a485a628f2baa33c0319dcf2da",
    ),
    (
        "peano-lab/py/peano_lab/library/quadratic_residue_surface.py",
        "ab7abd5b9fcf306035de6eb849ad65f8287e84e6cc00ad909aeed7e880915246",
    ),
    (
        "peano-lab/py/peano_lab/library/quadratic_residue_theorems.py",
        "d08e6a29295be014c67ec52d8cf7b67cc4b7c99abe6dde3708c162beccc4126d",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_fold_surface.py",
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_fold_theorems.py",
        "e69c41198d25aa0cba3bbf8415344050b28ecb8d058c1cd8d98415e0db09178c",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_range_theorems.py",
        "8ca4812b8059e76ec2faf4e4269d5192adee320df281b16dacfd5e7b9682833f",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_sum_theorems.py",
        "0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_congruence_theorems.py",
        "d82ad67620210cd81741bc8eb287569f9bf5124714ba50da65985c7d33a8ec68",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_bitcount_theorems.py",
        "4704e64d968b6ff19d302ef404dac38a8510aff980fd41063dde0010d6390e6c",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_factorial_theorems.py",
        "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709",
    ),
    (
        "peano-lab/py/peano_lab/library/power_congruence_theorems.py",
        "f1b34a176f9c77d60ef7dd1908ec7e6163608f684451c992dbd9fb8dacf34423",
    ),
    (
        "peano-lab/py/peano_lab/library/qr_small_moduli.py",
        "fb8dbbb75817e15f4e522e6d4ce20a0b4a13f4a836872ad6b8de6ed51c0d5530",
    ),
    (
        "peano-lab/py/peano_lab/library/power_algebra_theorems.py",
        "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302",
    ),
    (
        "peano-lab/py/peano_lab/library/gauss_sign_bridge.py",
        "2ea4ae59ea1d5120d93af74d7f4c1cff624c9ad3a0aeac36d3b8dd2901412b76",
    ),
    (
        "peano-lab/py/peano_lab/library/gauss_half_range.py",
        "3653e994bc5862c686d21a9597e0aef19302eccdbcc3badffc260918b2a656d7",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_permutation_theorems.py",
        "6265e4cf5938beadbf77182b7a5357a9435abd9948015a955539b451430420ce",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_product_permutation_theorems.py",
        "a9d799a189d8061b1ee97f163172f95396a35819cfef791543407ee0a34aea5a",
    ),
    (
        "peano-lab/py/peano_lab/library/finite_product_reindex_support.py",
        "7adf1f63c23e39ab1428061355cebb3caddd3bf51e909185ec22d83b6442fc7c",
    ),
    (
        "peano-lab/py/peano_lab/library/qr_bounded_units.py",
        "1ca3673054052094c32cabfca6a59f7e801ccd51b1fd9fee780d52fecaa70562",
    ),
    (
        "peano-lab/py/peano_lab/library/qr_prime_units.py",
        "ea611d606ed0b345e75e230c77ea9ec5ee5ce9a2b1d85ae400c2ac94819c11cd",
    ),
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_pilot_vector_audit_cli", CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _controlled_worker_environment(cli: object) -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONCASEOK",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONOPTIMIZE",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTHONWARNINGS",
    ):
        environment.pop(name, None)
    environment["PYTHONHASHSEED"] = "17"
    environment["PYTHONPYCACHEPREFIX"] = cli.DISABLED_PYCACHE_PREFIX
    return environment


def _cli_subprocess_source(body: str) -> str:
    return f"""
import importlib.util
from pathlib import Path
import sys

cli_path = Path({str(CLI_PATH)!r})
spec = importlib.util.spec_from_file_location("_a23b_controlled_cli", cli_path)
if spec is None or spec.loader is None:
    raise SystemExit("cannot create CLI spec")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
{body}
"""


def _controlled_python_executable() -> str:
    for name in ("python3.12", "python3.11", "python3"):
        executable = shutil.which(name)
        if executable is None:
            continue
        probe = subprocess.run(
            [executable, "-P", "-c", "import sys; raise SystemExit(not sys.flags.safe_path)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if probe.returncode == 0:
            return executable
    pytest.skip("no Python interpreter with -P safe-path support is available")


def _rows(document: dict[str, object]) -> dict[str, dict[str, object]]:
    return {row["name"]: row for row in document["theorems"]}


def _producer_source_state() -> dict[str, object]:
    payload = {
        "commit_sha1": "1" * 40,
        "files": [
            {
                "bytes": len((ROOT / relative).read_bytes()),
                "path": relative.as_posix(),
                "sha256": _sha256((ROOT / relative).read_bytes()),
            }
            for relative in audit.PRODUCER_SOURCE_FILES
        ],
        "format": audit.PRODUCER_SOURCE_STATE_FORMAT,
        "git_verified": False,
        "tree_sha1": "2" * 40,
        "v": 1,
    }
    preimage = {
        "format": audit.PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": 1,
    }
    return {
        **payload,
        "root_preimage": preimage,
        "root_sha256": audit._sha256_json(preimage, limit=audit.MAX_SCHEMA_BYTES),
    }


def _reroot_source_state(value: dict[str, object]) -> None:
    payload = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    value["root_preimage"] = {
        "format": audit.PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": 1,
    }
    value["root_sha256"] = audit._sha256_json(
        value["root_preimage"], limit=audit.MAX_SCHEMA_BYTES
    )


def test_schema_fixes_three_roots_two_routes_and_exact_attempt_budget() -> None:
    raw = SCHEMA_PATH.read_bytes()
    schema = audit.pilot_dependency_vector_audit_schema()
    assert raw == audit.canonical_document_bytes(
        schema, limit=audit.MAX_SCHEMA_BYTES
    )
    assert tuple(audit.EXPECTED_ROOTS) == EXPECTED_ROOTS
    assert tuple(
        (row["index"], row["name"]) for row in schema["required_theorems"]
    ) == EXPECTED_ROOTS
    assert audit.READABLE_ROUTE != audit.PROPOSED_LAYERED_ROUTE
    assert schema["constants"]["route_count"] == 2
    assert schema["constants"]["direct_dependency_edges_per_route"] == 22
    assert schema["constants"]["attempt_count_per_route"] == 22
    assert schema["constants"]["attempt_count"] == 44
    assert audit.EXPECTED_ATTEMPT_COUNT == 44
    assert schema["algorithm"]["attempt_order"] == (
        "root-order-then-reverse-direct-vector-order"
    )


def test_schema_domain_separates_route_receipts_and_requires_root_regeneration() -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    algorithm = schema["algorithm"]
    assert set(algorithm["routes"]) == {
        audit.READABLE_ROUTE,
        audit.PROPOSED_LAYERED_ROUTE,
    }
    assert "distinct" in schema["claim_boundary"]["route_independence"]
    layered_contract = algorithm["layered_omission"]
    assert "regenerate" in layered_contract
    assert "root" in layered_contract
    assert "before" in layered_contract
    assert "compile_layered_replay" in layered_contract
    assert "cached" in layered_contract


def test_schema_discloses_shared_body_compiler_without_independent_corroboration() -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    boundary = " ".join(schema["claim_boundary"].values()).lower()
    algorithm = " ".join(
        value
        for value in schema["algorithm"].values()
        if type(value) is str
    ).lower()
    assert "shared" in boundary
    assert "compile_candidate_body" in boundary or "body compiler" in boundary
    assert "preassembly" in boundary or "root-body" in boundary
    assert "independent corroboration" in boundary
    assert "does not" in boundary or "not " in boundary
    assert "compile_candidate_body" in algorithm


def test_schema_pins_live_implementation_sources_callables_and_exact_limits() -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    sources = schema["implementation_sources"]
    assert tuple(
        (row["path"], row["sha256"]) for row in sources
    ) == tuple(
        (path.as_posix(), sha256)
        for path, sha256 in audit._PINNED_IMPLEMENTATION
    )
    for row in sources:
        assert _sha256((ROOT / row["path"]).read_bytes()) == row["sha256"]
    assert schema["implementation_source_root_sha256"] == (
        audit.IMPLEMENTATION_SOURCE_ROOT_SHA256
    )
    assert audit._sha256_json(sources) == audit.IMPLEMENTATION_SOURCE_ROOT_SHA256

    assert schema["qualified_callables"] == {
        "artifact_decode": (
            "peano_lab.kernel.artifact_codec.decode_artifact"
        ),
        "artifact_encode": (
            "peano_lab.kernel.artifact_codec.encode_artifact_bounded"
        ),
        "formula_encode": "peano_lab.kernel.artifact_codec.encode_formula",
        "proof_encode": "peano_lab.kernel.artifact_codec.encode_proof",
        "candidate_body": (
            "peano_lab.library.candidate_validation.compile_candidate_body"
        ),
        "closed_readable": (
            "training.peano_hydra.library_construction_rebuild_core."
            "compile_closed_candidate"
        ),
        "kernel": "peano_lab.kernel.checker.check",
        "layered": "peano_lab.library.layered_replay.compile_layered_replay",
        "modular_recovery": (
            "training.peano_hydra.library_optimizer_comparison_pilot."
            "recover_curried_modular_body"
        ),
        "proof_metrics": (
            "training.peano_hydra.library_replay_pack.proof_tree_metrics"
        ),
    }
    assert schema["layered_replay_limits"] == asdict(audit.PILOT_LAYERED_LIMITS)
    assert schema["artifact_decode_limits"] == {
        "max_bytes": audit.MAX_ARTIFACT_BYTES,
        "max_depth": 512,
        "max_nodes": 1_000_000,
    }
    assert schema["artifact_encode_max_bytes"] == audit.MAX_ARTIFACT_BYTES
    assert schema["fuel_policy"] == {"multiplier": 8, "offset": 16}

    callable_limits = audit._callable_limits_identity()["preimage"]
    for field in (
        "artifact_decode_limits",
        "artifact_encode_max_bytes",
        "fuel_policy",
        "layered_replay_limits",
        "qualified_callables",
    ):
        assert callable_limits[field] == schema[field]
    assert callable_limits["expected_roots"] == [
        {"index": index, "name": name} for index, name in EXPECTED_ROOTS
    ]
    assert callable_limits["expected_attempt_count"] == 44


def test_implementation_sources_are_exact_retained_compiler_union_without_duplicates() -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    a21 = json.loads(A21_PATH.read_bytes())
    retained = [
        (row["path"], row["sha256"])
        for row in a21["inputs"]["compiler"]["sources"]
    ]
    assert len(retained) == 20
    additions = (
        (
            "peano-lab/py/peano_lab/library/layered_replay.py",
            "ad4421446336b7c8c0db9f12298a5aa66718dfeac76282ab91bf0db3ce00f4c4",
        ),
        (
            "training/peano_hydra/library_construction_rebuild_core.py",
            "98c2aa5b13b77a4f2e47c9d8663ff52c072e3cf61cac172dae523f30bfb25d10",
        ),
        (
            "training/peano_hydra/library_optimizer_comparison_pilot.py",
            "7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee",
        ),
        (
            "training/peano_hydra/library_replay_pack.py",
            "8c5f3b44bed64bc3a49a7990d16a6f3c4a966b14c2bf4c732227041bc81506ee",
        ),
    )
    expected = [*retained, *THEOREM_GENERATOR_SOURCE_ROWS, *additions]

    actual = [
        (row["path"], row["sha256"])
        for row in schema["implementation_sources"]
    ]
    assert actual == expected
    assert len(actual) == len({path for path, _digest in actual}) == 44
    assert all(
        _sha256((ROOT / path).read_bytes()) == digest
        for path, digest in expected
    )

    initializer = "training/peano_hydra/__init__.py"
    if initializer not in {path for path, _digest in actual}:
        worker_contract = json.dumps(
            schema["controlled_worker_contract"], sort_keys=True
        ).lower()
        assert "bypass" in worker_contract
        assert "training/peano_hydra/__init__.py" in worker_contract


def test_schema_requires_exact_four_file_fresh_controlled_worker_source_state() -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    source = schema["producer_source_state_contract"]
    assert tuple(source["ordered_files"]) == tuple(
        path.as_posix() for path in audit.PRODUCER_SOURCE_FILES
    )
    assert source["git_verified"] is False
    assert source["format"] == audit.PRODUCER_SOURCE_STATE_FORMAT
    assert source["required_fields"] == [
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    ]
    assert "live bytes" in source["trust_boundary"]
    assert "unverified" in source["trust_boundary"]

    worker = schema["controlled_worker_contract"]
    assert worker["fresh_process"] is True
    assert worker["python_flags"] == ["-B", "-P", "-s", "-S"]
    assert worker["environment"]["PYTHONPATH"].startswith("unset")
    assert worker["environment"]["PYTHONOPTIMIZE"].startswith("absent")
    assert worker["environment"]["PYTHONCASEOK"] == "absent"
    assert worker["environment"]["PYTHONWARNINGS"] == "absent"
    assert "read-only" in worker["source_snapshot"]
    assert "clean-commit" in worker["source_snapshot"]
    assert "bypass" in worker["initializer_boundary"]
    assert "training/peano_hydra/__init__.py" in worker[
        "initializer_boundary"
    ]
    assert "read-only" in worker["working_directory"]
    assert "bounded canonical JSON" in worker["stdout"]
    assert "bounded" in worker["stderr"]
    assert set(worker["failure_policy"]) == {
        "malformed_or_oversized_output",
        "nonzero_exit",
        "resource_limit",
        "timeout",
    }
    assert all(
        "typed unknown" in policy
        for policy in worker["failure_policy"].values()
    )
    assert "later execution receipt" in worker["verification_boundary"]


def test_producer_source_state_accepts_only_exact_live_ordered_false_git_receipt() -> None:
    valid = _producer_source_state()
    assert audit._validate_producer_source_state(valid, root=ROOT) == valid

    mutations: list[dict[str, object]] = []

    extra = deepcopy(valid)
    extra["extra"] = False
    mutations.append(extra)

    reordered = deepcopy(valid)
    reordered["files"][0], reordered["files"][1] = (
        reordered["files"][1],
        reordered["files"][0],
    )
    _reroot_source_state(reordered)
    mutations.append(reordered)

    wrong_bytes = deepcopy(valid)
    wrong_bytes["files"][0]["bytes"] += 1
    _reroot_source_state(wrong_bytes)
    mutations.append(wrong_bytes)

    wrong_digest = deepcopy(valid)
    wrong_digest["files"][0]["sha256"] = "f" * 64
    _reroot_source_state(wrong_digest)
    mutations.append(wrong_digest)

    integer_digest = deepcopy(valid)
    integer_digest["files"][0]["sha256"] = 1
    _reroot_source_state(integer_digest)
    mutations.append(integer_digest)

    duplicate_row = deepcopy(valid)
    duplicate_row["files"][1] = deepcopy(duplicate_row["files"][0])
    _reroot_source_state(duplicate_row)
    mutations.append(duplicate_row)

    for field in ("commit_sha1", "tree_sha1"):
        non_hex = deepcopy(valid)
        non_hex[field] = "g" * 40
        _reroot_source_state(non_hex)
        mutations.append(non_hex)

        coercible_integer = deepcopy(valid)
        coercible_integer[field] = 1
        _reroot_source_state(coercible_integer)
        mutations.append(coercible_integer)

    asserted_git = deepcopy(valid)
    asserted_git["git_verified"] = True
    _reroot_source_state(asserted_git)
    mutations.append(asserted_git)

    wrong_root = deepcopy(valid)
    wrong_root["root_sha256"] = "e" * 64
    mutations.append(wrong_root)

    integer_root = deepcopy(valid)
    integer_root["root_sha256"] = int("1" * 64)
    mutations.append(integer_root)

    for forged in mutations:
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="source|file|field|identity|live|root|git",
        ):
            audit._validate_producer_source_state(forged, root=ROOT)


@pytest.mark.parametrize(
    "callable_name",
    (
        "compile_candidate_body",
        "compile_closed_candidate",
        "compile_layered_replay",
        "check",
        "decode_artifact",
        "encode_artifact_bounded",
        "encode_formula",
        "encode_proof",
        "proof_tree_metrics",
        "recover_curried_modular_body",
    ),
)
def test_implementation_callable_origin_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    callable_name: str,
) -> None:
    monkeypatch.setattr(audit, callable_name, lambda *_args, **_kwargs: None)
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="callable|identity|origin|drift",
    ):
        audit._require_implementation(ROOT)


@pytest.mark.parametrize(
    ("module_name", "attribute"),
    (
        ("peano_lab.library.candidate_validation", "apply_tactic"),
        ("peano_lab.library.candidate_validation", "checked_final"),
        ("peano_lab.library.candidate_validation", "proof_resource_metrics"),
        (
            "training.peano_hydra.library_construction_rebuild_core",
            "compile_candidate_body",
        ),
        ("training.peano_hydra.library_construction_rebuild_core", "check"),
    ),
)
def test_critical_imported_callable_alias_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    attribute: str,
) -> None:
    module = sys.modules[module_name]
    monkeypatch.setattr(module, attribute, lambda *_args, **_kwargs: None)
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="callable|alias|identity|drift",
    ):
        audit._require_implementation(ROOT)


def test_implementation_source_omission_reorder_or_digest_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = audit._PINNED_IMPLEMENTATION
    wrong_digest = list(original)
    path, _digest = wrong_digest[0]
    wrong_digest[0] = (path, "0" * 64)
    variants = (
        original[1:],
        (original[1], original[0], *original[2:]),
        tuple(wrong_digest),
    )
    for forged in variants:
        with monkeypatch.context() as patcher:
            patcher.setattr(audit, "_PINNED_IMPLEMENTATION", forged)
            with pytest.raises(
                audit.LibraryPilotDependencyVectorAuditError,
                match="source|root|identity|drift",
            ):
                audit._require_implementation(ROOT)


def test_one_field_layered_limit_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        audit,
        "PILOT_LAYERED_LIMITS",
        replace(
            audit.PILOT_LAYERED_LIMITS,
            max_candidate_proof_depth=(
                audit.PILOT_LAYERED_LIMITS.max_candidate_proof_depth + 1
            ),
        ),
    )
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="limits|identity|drift",
    ):
        audit._require_implementation(ROOT)


def test_codec_fuel_and_protocol_count_schema_mutations_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = audit.pilot_dependency_vector_audit_schema()
    mutations: list[dict[str, object]] = []
    for field in ("max_bytes", "max_nodes", "max_depth"):
        forged = deepcopy(schema)
        forged["artifact_decode_limits"][field] += 1
        mutations.append(forged)
    forged = deepcopy(schema)
    forged["artifact_encode_max_bytes"] += 1
    mutations.append(forged)
    for field in ("multiplier", "offset"):
        forged = deepcopy(schema)
        forged["fuel_policy"][field] += 1
        mutations.append(forged)
    forged = deepcopy(schema)
    forged["expected_attempt_count"] = 43
    mutations.append(forged)
    forged = deepcopy(schema)
    forged["expected_roots"] = list(reversed(forged["expected_roots"]))
    mutations.append(forged)
    forged = deepcopy(schema)
    forged["qualified_callables"]["kernel"] = "foreign.kernel.check"
    mutations.append(forged)

    for value in mutations:
        with monkeypatch.context() as patcher:
            patcher.setattr(
                audit, "pilot_dependency_vector_audit_schema", lambda: value
            )
            with pytest.raises(
                audit.LibraryPilotDependencyVectorAuditError,
                match="schema|limit|fuel|protocol|identity|drift",
            ):
                audit._require_implementation(ROOT)


def test_fixed_inputs_and_retained_surfaces_pin_exact_bytes() -> None:
    schema = json.loads(SCHEMA_PATH.read_bytes())
    fixed = schema["fixed_inputs"]
    fixed_by_path = {
        ROOT / row["artifact_path"]: row["artifact_sha256"]
        for row in fixed.values()
    }
    assert fixed_by_path == UPSTREAM_SHA256
    for path, expected in UPSTREAM_SHA256.items():
        assert _sha256(path.read_bytes()) == expected

    a21 = _rows(json.loads(A21_PATH.read_bytes()))
    a23 = _rows(json.loads(A23_PATH.read_bytes()))
    readable_total = 0
    layered_total = 0
    for index, name in EXPECTED_ROOTS:
        assert a21[name]["index"] == a23[name]["index"] == index
        readable = tuple(a21[name]["readable"]["dependencies"])
        assert readable == EXPECTED_DIRECT[name]
        readable_total += len(readable)

        assert a23[name]["comparison"]["representative_candidate_id"] == (
            "layered-closure"
        )
        layered = next(
            row
            for row in a23[name]["artifacts"]
            if row["candidate_id"] == "layered-closure"
        )
        surface = layered["surface"]
        optimized = tuple(surface["direct_dependencies"])
        assert optimized == EXPECTED_DIRECT[name]
        assert surface["direct_dependency_count"] == len(optimized)
        assert surface["transitive_closure_count"] == EXPECTED_CLOSURE_COUNTS[name]
        closure = tuple(
            surface["transitive_closure_dependencies_in_replay_order"]
        )
        assert closure != optimized
        assert surface["transitive_closure_lf_sha256"] == _sha256(
            ("\n".join(closure) + "\n").encode("utf-8")
        )
        assert tuple(a23[name]["layered_bundle"]["node_names_in_replay_order"]) == (
            *closure,
            name,
        )
        assert a23[name]["layered_bundle"]["node_names_lf_sha256"] == _sha256(
            ("\n".join((*closure, name)) + "\n").encode("utf-8")
        )
        body_sources = a23[name]["layered_bundle"]["body_sources"]
        assert tuple(source["name"] for source in body_sources) == (*closure, name)
        assert body_sources[-1]["kind"] == "a2.2-direct-cut-rebuild"
        assert tuple(body_sources[-1]["dependencies"]) == optimized
        assert all(
            source["kind"] == "retained-replay"
            for source in body_sources[:-1]
        )
        assert not (
            {pilot_name for _pilot_index, pilot_name in EXPECTED_ROOTS} - {name}
        ).intersection(closure)
        layered_total += len(optimized)

    assert (readable_total, layered_total) == (22, 22)


def test_all_384_live_theorem_specs_exactly_join_retained_transport() -> None:
    manifest = json.loads(REPLAY_MANIFEST_PATH.read_bytes())
    rows = manifest["theorems"]
    assert len(rows) == len(audit.THEOREMS) == 384
    for index, (spec, row) in enumerate(zip(audit.THEOREMS, rows, strict=True)):
        assert type(spec) is TheoremSpec
        assert row["index"] == index
        assert row["name"] == spec.name
        assert row["statement_source"] == spec.statement
        assert row["statement_source_sha256"] == _sha256(
            spec.statement.encode("utf-8")
        )
        assert row["formula_sha256"] == _sha256(
            audit.encode_formula(audit._closed_formula(spec.statement))
        )
        assert tuple(row["declared_dependencies"]) == spec.dependencies
        assert tuple(row["script"]) == spec.script
        assert row["script_sha256"] == audit._lf_sha256(spec.script)
        assert row["summary"] == spec.summary


def test_live_theorem_transport_join_is_type_order_and_field_mutation_closed() -> None:
    manifest = json.loads(REPLAY_MANIFEST_PATH.read_bytes())
    specs = tuple(audit.THEOREMS)
    replay_rows = _rows(manifest)
    receipt = audit._validate_live_theorem_transport(
        specs, replay_rows=replay_rows
    )
    assert receipt["count"] == 384
    assert receipt["status"] == "exact-live-spec-to-retained-replay-transport"
    assert len(receipt["preimage"]["records"]) == 384
    assert receipt["root_sha256"] == audit._sha256_json(receipt["preimage"])

    def reject(
        changed_specs: object = specs,
        changed_rows: object = replay_rows,
    ) -> None:
        with pytest.raises(audit.LibraryPilotDependencyVectorAuditError):
            audit._validate_live_theorem_transport(
                changed_specs, replay_rows=changed_rows
            )

    reject(list(specs), replay_rows)
    reject(specs[:-1], replay_rows)
    foreign = list(specs)
    foreign[0] = SimpleNamespace(**asdict(specs[0]))
    reject(tuple(foreign), replay_rows)

    reordered = list(specs)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    reject(tuple(reordered), replay_rows)
    for field, value in (
        ("name", specs[1].name),
        ("statement", specs[1].statement),
        ("dependencies", (*specs[0].dependencies, "unexpected_dependency")),
        ("script", (*specs[0].script, "simp")),
        ("summary", specs[0].summary + " drift"),
    ):
        changed = list(specs)
        changed[0] = replace(specs[0], **{field: value})
        reject(tuple(changed), replay_rows)

    first_name = specs[0].name
    for field, value in (
        ("index", True),
        ("name", specs[1].name),
        ("statement_source", specs[1].statement),
        ("statement_source_sha256", "0" * 64),
        ("statement_canonical", "drifted canonical statement"),
        ("statement_canonical_sha256", "1" * 64),
        ("declared_dependencies", ["unexpected_dependency"]),
        ("script", [*specs[0].script, "simp"]),
        ("script_sha256", "2" * 64),
        ("summary", specs[0].summary + " drift"),
        ("formula_sha256", "3" * 64),
    ):
        changed_rows = deepcopy(replay_rows)
        changed_rows[first_name][field] = value
        reject(specs, changed_rows)

    coherent_statement_drift = deepcopy(replay_rows)
    coherent_statement_drift[first_name]["statement_source"] = specs[1].statement
    coherent_statement_drift[first_name]["statement_source_sha256"] = _sha256(
        specs[1].statement.encode("utf-8")
    )
    coherent_statement_drift[first_name]["formula_sha256"] = _sha256(
        audit.encode_formula(audit._closed_formula(specs[1].statement))
    )
    reject(specs, coherent_statement_drift)

    coherent_script_drift = deepcopy(replay_rows)
    changed_script = [*specs[0].script, "simp"]
    coherent_script_drift[first_name]["script"] = changed_script
    coherent_script_drift[first_name]["script_sha256"] = audit._lf_sha256(
        tuple(changed_script)
    )
    reject(specs, coherent_script_drift)

    missing = deepcopy(replay_rows)
    missing.pop(first_name)
    missing["unexpected_theorem"] = deepcopy(next(iter(replay_rows.values())))
    reject(specs, missing)


def test_route_preimages_and_ordered_local_union_are_domain_separated() -> None:
    readable = ("a", "b", "d")
    optimized = ("b", "c", "a", "e")
    assert audit._ordered_union(readable, optimized) == (
        "a",
        "b",
        "d",
        "c",
        "e",
    )
    common = {
        "name": "fixture",
        "index": 7,
        "dependencies": readable,
        "attempts_root_sha256": "1" * 64,
        "baseline_receipt_sha256": "2" * 64,
        "formula_sha256": "3" * 64,
        "direct_dependencies_lf_sha256": "4" * 64,
        "baseline_closure_lf_sha256": "5" * 64,
        "root_body_certificate_sha256": "6" * 64,
        "producer_source_state_root_sha256": "7" * 64,
        "implementation_source_root_sha256": "8" * 64,
        "callable_limits_sha256": "9" * 64,
    }
    first = audit._route_preimage(route=audit.READABLE_ROUTE, **common)
    second = audit._route_preimage(
        route=audit.PROPOSED_LAYERED_ROUTE, **common
    )
    assert first != second
    assert first["route"] == audit.READABLE_ROUTE
    assert second["route"] == audit.PROPOSED_LAYERED_ROUTE
    assert {
        "attempts_root_sha256",
        "baseline_closure_lf_sha256",
        "baseline_receipt_sha256",
        "callable_limits_sha256",
        "dependencies",
        "direct_dependencies_lf_sha256",
        "formula_sha256",
        "implementation_source_root_sha256",
        "index",
        "name",
        "producer_source_state_root_sha256",
        "root_body_certificate_sha256",
        "route",
    }.issubset(first)
    assert audit._sha256_json(first) != audit._sha256_json(second)


def test_single_omission_vectors_are_complete_full_vector_and_reverse_ordered() -> None:
    dependencies = ("a", "b", "c")
    attempts = audit._single_omission_vectors(dependencies)
    assert attempts == (
        ("c", ("a", "b")),
        ("b", ("a", "c")),
        ("a", ("b", "c")),
    )
    assert all(len(candidate) == len(dependencies) - 1 for _, candidate in attempts)
    assert {omitted for omitted, _candidate in attempts} == set(dependencies)

    all_attempts = [
        (name, omitted, candidate)
        for _index, name in EXPECTED_ROOTS
        for omitted, candidate in audit._single_omission_vectors(
            EXPECTED_DIRECT[name]
        )
    ]
    assert len(all_attempts) == 22
    assert len(all_attempts) * 2 == audit.EXPECTED_ATTEMPT_COUNT == 44


def test_only_exact_recipe_rejection_is_recordable_and_unknown_aborts() -> None:
    try:
        try:
            raise TacticError("synthetic ordinary tactic rejection")
        except TacticError as cause:
            raise CandidateBodyError(
                "synthetic exact rejection",
                phase="command",
                kind="exact-recipe-rejection",
                command_index=0,
                command="refl",
            ) from cause
    except CandidateBodyError as error:
        exact = error
    classification = audit._classify_candidate_error(exact)
    assert classification["outcome"] == "exact-route-rejected"
    assert classification["failure"]["kind"] == "exact-recipe-rejection"

    cause_less = CandidateBodyError(
        "unproven exact label",
        phase="command",
        kind="exact-recipe-rejection",
        command_index=0,
        command="refl",
    )
    for unknown in (
        cause_less,
        CandidateBodyError(
            "synthetic resource exhaustion",
            phase="finalization",
            kind="resource-limit",
        ),
        CandidateBodyError(
            "synthetic internal failure",
            phase="finalization",
            kind="internal",
        ),
        CandidateBodyError(
            "synthetic malformed source",
            phase="finalization",
            kind="malformed-source",
        ),
    ):
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="unknown|abort|resource|internal|malformed",
        ):
            audit._classify_candidate_error(unknown)


def test_command_rejection_requires_exact_tactic_error_cause_type() -> None:
    class ForeignTacticError(TacticError):
        pass

    for cause in (
        TacticSyntaxError("synthetic syntax error"),
        ForeignTacticError("synthetic foreign tactic error"),
    ):
        error = CandidateBodyError(
            "candidate 'fixture' failed at command 0: 'refl'",
            phase="command",
            kind="exact-recipe-rejection",
            command_index=0,
            command="refl",
        )
        error.__cause__ = cause
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="unknown|abort|cause|command",
        ):
            audit._classify_candidate_error(error)


@pytest.mark.parametrize(
    ("command_index", "command"),
    (
        (None, "refl"),
        (-1, "refl"),
        (False, "refl"),
        (0, None),
        (0, ""),
        (0, False),
    ),
)
def test_command_rejection_requires_exact_nonempty_command_metadata(
    command_index: object,
    command: object,
) -> None:
    error = CandidateBodyError(
        "synthetic command rejection",
        phase="command",
        kind="exact-recipe-rejection",
        command_index=command_index,
        command=command,
    )
    try:
        raise TacticError("synthetic ordinary tactic rejection")
    except TacticError as cause:
        error.__cause__ = cause

    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="metadata|command|unknown|abort",
    ):
        audit._classify_candidate_error(error)


@pytest.mark.parametrize(
    ("command_index", "command"),
    ((0, None), (None, "refl"), (0, "refl"), (False, None)),
)
def test_finalization_rejection_requires_null_command_metadata(
    command_index: object,
    command: object,
) -> None:
    error = CandidateBodyError(
        "synthetic theorem produced an incomplete dependency-curried proof",
        phase="finalization",
        kind="exact-recipe-rejection",
        command_index=command_index,
        command=command,
    )
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="metadata|command|unknown|abort",
    ):
        audit._classify_candidate_error(error)


def test_valid_finalization_rejection_records_explicit_null_command_metadata() -> None:
    error = CandidateBodyError(
        "candidate 'fixture' produced an incomplete dependency-curried proof",
        phase="finalization",
        kind="exact-recipe-rejection",
    )
    classified = audit._classify_candidate_error(error)
    assert classified["failure"]["phase"] == "finalization"
    assert classified["failure"]["command_index"] is None
    assert classified["failure"]["command"] is None


def test_finalization_rejection_allows_only_exact_causes_or_exact_compiler_paths() -> None:
    for cause in (
        InvalidProof("synthetic invalid proof"),
        ProofReductionError("synthetic invalid reduction"),
    ):
        error = CandidateBodyError(
            "candidate 'fixture' failed exact finalization",
            phase="finalization",
            kind="exact-recipe-rejection",
        )
        error.__cause__ = cause
        assert audit._classify_candidate_error(error)["outcome"] == (
            "exact-route-rejected"
        )

    class ForeignInvalidProof(InvalidProof):
        pass

    subclass_error = CandidateBodyError(
        "candidate 'fixture' failed foreign finalization",
        phase="finalization",
        kind="exact-recipe-rejection",
    )
    subclass_error.__cause__ = ForeignInvalidProof("foreign")
    malformed_cause_less = (
        "forged incomplete dependency-curried proof somewhere",
        (
            "candidate 'fixture' produced an incomplete dependency-curried proof "
            "after an unclassified error"
        ),
        "forged left a hole or metavariable during finalization somewhere",
    )
    for unknown in (
        subclass_error,
        *(
            CandidateBodyError(
                message,
                phase="finalization",
                kind="exact-recipe-rejection",
            )
            for message in malformed_cause_less
        ),
    ):
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="unknown|abort|cause|finalization",
        ):
            audit._classify_candidate_error(unknown)


def test_attempt_layer_binds_command_rejection_to_exact_frozen_script() -> None:
    error = CandidateBodyError(
        "synthetic exact command rejection",
        phase="command",
        kind="exact-recipe-rejection",
        command_index=1,
        command="exact needed",
    )
    try:
        raise TacticError("synthetic ordinary tactic rejection")
    except TacticError as cause:
        error.__cause__ = cause

    classified = audit._classify_attempt_error(
        error, script=("intro n", "exact needed")
    )
    assert classified["failure"]["command_index"] == 1
    assert classified["failure"]["command"] == "exact needed"

    for script in (
        ("intro n",),
        ("intro n", "exact another"),
        ("exact needed", "intro n"),
    ):
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="command|script|unknown|abort",
        ):
            audit._classify_attempt_error(error, script=script)


def test_shared_preassembly_rejection_keeps_full_after_vector_and_trial_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencies = ("needed",)
    script = ("refl",)
    baseline_evidence = audit._CandidateEvidence(
        target=object(),
        proof=object(),
        direct_dependencies=dependencies,
        closure=("baseline-closure",),
        diagnostics={"root_body_receipt": {"certificate_sha256": "a" * 64}},
    )

    def compile_vector(vector: tuple[str, ...]) -> object:
        if vector == dependencies:
            return baseline_evidence
        error = CandidateBodyError(
            "candidate 'fixture' failed at command 0: 'refl'",
            phase="command",
            kind="exact-recipe-rejection",
            command_index=0,
            command="refl",
        )
        error.__cause__ = TacticError("synthetic shared rejection")
        raise error

    def closure_for(vector: tuple[str, ...]) -> tuple[str, ...]:
        return ("baseline-closure",) if vector else ("trial-closure",)

    def baseline_receipt(
        *, route: str, evidence: object, basis: str, **_kwargs: object
    ) -> dict[str, object]:
        assert evidence is baseline_evidence
        surface = audit._dependency_surface(
            dependencies, ("baseline-closure",), basis=basis
        )
        return {
            "diagnostics": {
                "root_body_receipt": {"certificate_sha256": "a" * 64}
            },
            "proof": {"formula_sha256": "b" * 64},
            "sha256": (
                "c" * 64 if route == audit.READABLE_ROUTE else "d" * 64
            ),
            "surface": surface,
        }

    monkeypatch.setattr(audit, "_baseline_receipt", baseline_receipt)
    monkeypatch.setattr(
        audit,
        "_callable_limits_identity",
        lambda: {"sha256": "e" * 64},
    )
    common = {
        "name": "fixture",
        "index": 7,
        "dependencies": dependencies,
        "script": script,
        "producer_source_state_root_sha256": "f" * 64,
        "compile_vector": compile_vector,
        "closure_for_vector": closure_for,
    }
    readable = audit._audit_readable_route(**common)
    layered = audit._audit_layered_route(**common)
    readable_row = readable["attempts"][0]
    layered_row = layered["attempts"][0]

    for row, route in (
        (readable_row, audit.READABLE_ROUTE),
        (layered_row, audit.PROPOSED_LAYERED_ROUTE),
    ):
        assert row["name"] == "fixture"
        assert row["index"] == 7
        assert row["route"] == route
        assert row["before_dependencies"] == ["needed"]
        assert row["attempted_dependencies"] == []
        assert row["after_dependencies"] == ["needed"]
        assert "surface" not in row
        assert row["trial_surface"]["direct_dependencies"] == []
        assert row["trial_surface"][
            "transitive_closure_dependencies_in_replay_order"
        ] == ["trial-closure"]
        assert row["terminal_stage"] == "root-body-regeneration"
        assert row["layered_compiler_invoked"] is False
        assert row["route_specific_assembly_reached"] is False
        assert row["baseline_formula_sha256"] == "b" * 64
        assert row["baseline_root_body_certificate_sha256"] == "a" * 64
        assert row["script_sha256"] == audit._lf_sha256(script)
        assert row["record_sha256"] == audit._attempt_record_hash(row)

    assert readable_row["shared_root_body_observation_sha256"] == (
        layered_row["shared_root_body_observation_sha256"]
    )
    assert readable["route_receipt_sha256"] != layered["route_receipt_sha256"]


def test_positive_layered_attempt_retains_body_provenance_and_artifact_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencies = ("omitted",)
    baseline = audit._CandidateEvidence(
        target=object(),
        proof=object(),
        direct_dependencies=dependencies,
        closure=("baseline-node",),
        diagnostics={"root_body_receipt": {"certificate_sha256": "1" * 64}},
    )
    trial_diagnostics = {
        "artifact_bytes": 123,
        "artifact_sha256": "2" * 64,
        "modular_body_provenance_root_sha256": "3" * 64,
        "root_body_receipt": {
            "certificate_sha256": "4" * 64,
            "target_formula_sha256": "5" * 64,
        },
    }
    trial = audit._CandidateEvidence(
        target=object(),
        proof=object(),
        direct_dependencies=(),
        closure=("trial-node",),
        diagnostics=trial_diagnostics,
    )

    def compile_vector(vector: tuple[str, ...]) -> object:
        return baseline if vector == dependencies else trial

    def closure_for(vector: tuple[str, ...]) -> tuple[str, ...]:
        return ("baseline-node",) if vector else ("trial-node",)

    def baseline_receipt(*, basis: str, **_kwargs: object) -> dict[str, object]:
        return {
            "diagnostics": {
                "root_body_receipt": {"certificate_sha256": "1" * 64}
            },
            "proof": {"formula_sha256": "6" * 64},
            "sha256": "7" * 64,
            "surface": audit._dependency_surface(
                dependencies, ("baseline-node",), basis=basis
            ),
        }

    monkeypatch.setattr(audit, "_baseline_receipt", baseline_receipt)
    monkeypatch.setattr(
        audit,
        "_proof_receipt",
        lambda _target, _proof: {
            "formula_sha256": "6" * 64,
            "kernel_accepted": True,
            "proof_term_sha256": "8" * 64,
        },
    )
    monkeypatch.setattr(
        audit,
        "_callable_limits_identity",
        lambda: {"sha256": "9" * 64},
    )

    result = audit._audit_layered_route(
        name="fixture",
        index=7,
        dependencies=dependencies,
        script=("refl",),
        producer_source_state_root_sha256="a" * 64,
        compile_vector=compile_vector,
        closure_for_vector=closure_for,
    )
    row = result["attempts"][0]
    assert row["outcome"] == "kernel-accepted"
    assert row["name"] == "fixture"
    assert row["index"] == 7
    assert row["baseline_formula_sha256"] == "6" * 64
    assert row["baseline_root_body_certificate_sha256"] == "1" * 64
    assert row["script_sha256"] == audit._lf_sha256(("refl",))
    assert row["attempted_dependencies"] == []
    assert row["after_dependencies"] == []
    assert row["trial_surface"][
        "transitive_closure_dependencies_in_replay_order"
    ] == ["trial-node"]
    assert row["diagnostics"] == trial_diagnostics
    assert row["diagnostics"]["root_body_receipt"][
        "certificate_sha256"
    ] == "4" * 64
    assert row["diagnostics"][
        "modular_body_provenance_root_sha256"
    ] == "3" * 64
    assert row["diagnostics"]["artifact_sha256"] == "2" * 64
    assert row["diagnostics"]["artifact_bytes"] == 123
    assert row["terminal_stage"] == "kernel-check"
    assert row["layered_compiler_invoked"] is True
    assert row["record_sha256"] == audit._attempt_record_hash(row)


def test_cross_route_shared_body_consistency_rejects_any_outcome_or_receipt_drift() -> None:
    baseline_body = {"certificate_sha256": "1" * 64, "dependency_count": 2}
    successful_body = {"certificate_sha256": "2" * 64, "dependency_count": 1}
    attempts = [
        {
            "attempt_index": 0,
            "attempted_dependencies": ["a"],
            "omitted_dependency": "b",
            "outcome": "exact-route-rejected",
            "shared_root_body_observation_sha256": "3" * 64,
        },
        {
            "attempt_index": 1,
            "attempted_dependencies": ["b"],
            "diagnostics": {"root_body_receipt": successful_body},
            "omitted_dependency": "a",
            "outcome": "kernel-accepted",
        },
    ]
    readable = {
        "attempts": deepcopy(attempts),
        "baseline": {"diagnostics": {"root_body_receipt": baseline_body}},
    }
    layered = deepcopy(readable)
    receipt = audit._validate_cross_route_shared_body_consistency(
        readable, layered
    )
    assert receipt["status"] == "shared-root-body-consistent"
    assert receipt["paired_attempt_count"] == 2

    mutations: list[dict[str, object]] = []
    changed = deepcopy(layered)
    changed["baseline"]["diagnostics"]["root_body_receipt"][
        "certificate_sha256"
    ] = "4" * 64
    mutations.append(changed)
    changed = deepcopy(layered)
    changed["attempts"][0]["outcome"] = "kernel-accepted"
    changed["attempts"][0]["diagnostics"] = {
        "root_body_receipt": successful_body
    }
    mutations.append(changed)
    changed = deepcopy(layered)
    changed["attempts"][0]["shared_root_body_observation_sha256"] = "5" * 64
    mutations.append(changed)
    changed = deepcopy(layered)
    changed["attempts"][1]["diagnostics"]["root_body_receipt"][
        "certificate_sha256"
    ] = "6" * 64
    mutations.append(changed)
    changed = deepcopy(layered)
    changed["attempts"][1]["attempted_dependencies"] = []
    mutations.append(changed)

    for forged in mutations:
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="cross-route|shared|baseline|outcome|replay|diverged",
        ):
            audit._validate_cross_route_shared_body_consistency(
                readable, forged
            )


@pytest.mark.parametrize("value", (None, object(), False, {}))
def test_layered_none_or_wrong_type_is_unknown_and_aborts(value: object) -> None:
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="unknown|layered|candidate|abort",
    ):
        audit._require_layered_candidate(
            value,
            root_name="synthetic-root",
            phase="single-dependency-omission",
        )


def test_layered_omission_regenerates_trial_root_before_closure_and_compile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_name = "fixture_root"
    dependency_name = "fixture_dependency"
    baseline_root_body = object()
    regenerated_root_body = object()
    retained_dependency_body = object()
    compiled_proof = object()
    events: list[tuple[str, object]] = []
    root_spec = TheoremSpec(
        root_name,
        "forall n. n = n",
        (dependency_name, "omitted_dependency"),
        ("intro n", "refl"),
        "Synthetic root.",
    )
    specs = {root_name: root_spec}
    replay_rows = {
        dependency_name: {"index": 0},
        root_name: {"index": 1},
    }
    trial = (dependency_name,)

    def compile_body(spec: TheoremSpec, *, core: object) -> object:
        events.append(("compile-root-body", spec.dependencies))
        assert spec is not root_spec
        assert spec.dependencies == trial
        assert core is specs
        return SimpleNamespace(certificate=regenerated_root_body)

    def body_receipt(body: object, *, dependencies: tuple[str, ...]) -> dict[str, object]:
        events.append(("root-body-receipt", dependencies))
        assert body.certificate is regenerated_root_body
        return {"certificate_sha256": "a" * 64}

    def closure(
        supplied_root: str,
        dependencies: tuple[str, ...],
        *,
        replay_rows: object,
        fixed_vectors: object,
    ) -> tuple[str, ...]:
        events.append(("root-only-closure", dependencies))
        assert supplied_root == root_name
        assert dependencies == trial
        assert fixed_vectors == {}
        return (dependency_name,)

    def recover(
        name: str, **_kwargs: object
    ) -> tuple[object, tuple[str, ...], object, dict[str, object]]:
        events.append(("recover-node", name))
        assert name == dependency_name
        return object(), (), retained_dependency_body, {
            "body_certificate_sha256": "b" * 64,
            "dependencies": [],
            "index": 0,
            "name": name,
        }

    def layered(bundle: object, target: object, *, limits: object) -> object:
        events.append(("compile-layered-replay", bundle))
        assert limits is audit.PILOT_LAYERED_LIMITS
        assert bundle.root == 1
        assert len(bundle.nodes) == 2
        dependency_node, root_node = bundle.nodes
        assert dependency_node.body is retained_dependency_body
        assert root_node.body is regenerated_root_body
        assert root_node.body is not baseline_root_body
        assert root_node.dependencies == (0,)
        return SimpleNamespace(
            target=target,
            certificate=compiled_proof,
            layers=((0,), (1,)),
            maximum_package_formula_depth=1,
            package_formula_occurrences=1,
            proof_depth=1,
            proof_nodes=1,
        )

    def kernel(_context: object, proof: object, _target: object) -> bool:
        events.append(("kernel-check", proof))
        return True

    def encode_artifact(
        fuel: int,
        _target: object,
        proof: object,
        *,
        max_bytes: int,
    ) -> bytes:
        events.append(("encode-artifact", proof))
        assert fuel == 24
        assert max_bytes == audit.MAX_ARTIFACT_BYTES
        return b"synthetic-layered-artifact"

    def decode_artifact(
        raw: bytes, **_kwargs: object
    ) -> tuple[int, object, object]:
        events.append(("decode-artifact", raw))
        assert raw == b"synthetic-layered-artifact"
        target = next(
            item[1].nodes[1].target
            for item in events
            if item[0] == "compile-layered-replay"
        )
        return 24, target, compiled_proof

    monkeypatch.setattr(audit, "compile_candidate_body", compile_body)
    monkeypatch.setattr(audit, "_candidate_body_receipt", body_receipt)
    monkeypatch.setattr(audit, "_transitive_closure", closure)
    monkeypatch.setattr(audit, "_recover_selected_modular_body", recover)
    monkeypatch.setattr(audit, "compile_layered_replay", layered)
    monkeypatch.setattr(audit, "_require_layered_candidate", lambda value, **_kwargs: value)
    monkeypatch.setattr(audit, "check", kernel)
    monkeypatch.setattr(
        audit,
        "proof_tree_metrics",
        lambda _proof: {"cut_nodes": 0, "proof_depth": 1, "proof_nodes": 1},
    )
    monkeypatch.setattr(audit, "encode_formula", lambda _formula: b"formula")
    monkeypatch.setattr(audit, "encode_proof", lambda _proof: b"proof")
    monkeypatch.setattr(audit, "encode_artifact_bounded", encode_artifact)
    monkeypatch.setattr(audit, "decode_artifact", decode_artifact)

    evidence = audit._compile_layered_candidate(
        root_name,
        trial,
        root=ROOT,
        a21_rows={},
        replay_rows=replay_rows,
        specs=specs,
    )

    names = [name for name, _payload in events]
    assert names.index("compile-root-body") < names.index("root-only-closure")
    assert names.index("root-only-closure") < names.index("recover-node")
    assert names.index("recover-node") < names.index("compile-layered-replay")
    assert names.index("compile-layered-replay") < names.index("kernel-check")
    assert names.index("kernel-check") < names.index("encode-artifact")
    assert names.index("encode-artifact") < names.index("decode-artifact")
    assert names.count("encode-artifact") == 2
    assert names.count("kernel-check") == 2
    assert evidence.direct_dependencies == trial
    assert evidence.closure == (dependency_name,)
    assert evidence.proof is compiled_proof
    assert evidence.diagnostics["root_body_receipt"][
        "certificate_sha256"
    ] == "a" * 64


def test_readable_success_return_keeps_only_readable_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_name = "fixture_root"
    dependency = "fixture_dependency"
    spec = TheoremSpec(
        root_name,
        "forall n. n = n",
        (dependency,),
        ("intro n", "refl"),
        "Synthetic readable root.",
    )
    specs = {root_name: spec}
    body = SimpleNamespace(target=object(), certificate=object())
    closed = audit.ClosedCandidateCompilation(
        body=body,
        target=object(),
        proof=object(),
    )
    carrier = SimpleNamespace(target=object(), proof=object())
    events: list[str] = []

    def compile_body(selected: TheoremSpec, *, core: object) -> object:
        events.append("compile-body")
        assert selected.dependencies == (dependency,)
        assert core is specs
        return body

    def compile_closed(
        selected: TheoremSpec, **_kwargs: object
    ) -> object:
        events.append("compile-closed")
        assert selected.dependencies == (dependency,)
        return closed

    def closure(
        supplied_root: str,
        dependencies: tuple[str, ...],
        **_kwargs: object,
    ) -> tuple[str, ...]:
        events.append("closure")
        assert supplied_root == root_name
        assert dependencies == (dependency,)
        return (dependency,)

    monkeypatch.setattr(audit, "compile_candidate_body", compile_body)
    monkeypatch.setattr(
        audit,
        "_candidate_body_receipt",
        lambda *_args, **_kwargs: {"certificate_sha256": "1" * 64},
    )
    monkeypatch.setattr(audit, "compile_closed_candidate", compile_closed)
    monkeypatch.setattr(audit, "check", lambda *_args: True)
    monkeypatch.setattr(audit, "encode_formula", lambda _formula: b"formula")
    monkeypatch.setattr(audit, "encode_proof", lambda _proof: b"proof")
    monkeypatch.setattr(audit, "_transitive_closure", closure)

    evidence = audit._compile_readable_candidate(
        root_name,
        (dependency,),
        specs=specs,
        replay_rows={root_name: {"index": 1}, dependency: {"index": 0}},
        dependency_certificates={dependency: carrier},
        fixed_vectors={},
    )
    assert events == ["compile-body", "compile-closed", "closure"]
    assert evidence.target is closed.target
    assert evidence.proof is closed.proof
    assert evidence.direct_dependencies == (dependency,)
    assert evidence.closure == (dependency,)
    assert evidence.diagnostics["root_body_receipt"][
        "certificate_sha256"
    ] == "1" * 64
    assert "modular_body_identity_preimage" not in evidence.diagnostics


def test_full_vector_layered_baseline_parity_is_exact_and_mutation_closed() -> None:
    row = _rows(json.loads(A23_PATH.read_bytes()))["odd_add_odd"]
    layered = next(
        item
        for item in row["artifacts"]
        if item["candidate_id"] == "layered-closure"
    )
    bundle = row["layered_bundle"]
    surface = layered["surface"]
    identities = [
        {
            "body_certificate_sha256": source["body_certificate_sha256"],
            "dependencies": source["dependencies"],
            "index": source["index"],
            "name": source["name"],
        }
        for source in bundle["body_sources"]
    ]
    identity_preimage = {
        "format": "peano-hydra-layered-modular-body-identities-preimage",
        "records": identities,
        "v": 1,
    }
    provenance_preimage = {
        "format": "peano-hydra-layered-modular-body-provenance-preimage",
        "records": [
            {
                "body_certificate_sha256": identity[
                    "body_certificate_sha256"
                ],
                "name": identity["name"],
                "source": "fresh-a2.3b-recovery",
            }
            for identity in identities
        ],
        "v": 1,
    }
    diagnostics = {
        "artifact_bytes": layered["metrics"]["artifact_bytes"],
        "artifact_sha256": layered["artifact_sha256"],
        "candidate_formula_sha256": layered["formula_sha256"],
        "candidate_metrics": layered["metrics"],
        "candidate_proof_term_sha256": layered["proof_term_sha256"],
        "compiler_result_type": bundle["compiler_result_type"],
        "dependency_edge_count": bundle["dependency_edge_count"],
        "fuel": layered["fuel"],
        "layer_count": bundle["layer_count"],
        "layers": bundle["layers"],
        "maximum_package_formula_depth": bundle[
            "maximum_package_formula_depth"
        ],
        "modular_body_identity_preimage": identity_preimage,
        "modular_body_identity_root_sha256": audit._sha256_json(
            identity_preimage
        ),
        "modular_body_provenance_preimage": provenance_preimage,
        "modular_body_provenance_root_sha256": audit._sha256_json(
            provenance_preimage
        ),
        "node_count": bundle["node_count"],
        "node_names_in_replay_order": bundle["node_names_in_replay_order"],
        "node_names_lf_sha256": bundle["node_names_lf_sha256"],
        "package_formula_occurrences": bundle["package_formula_occurrences"],
    }
    evidence = audit._CandidateEvidence(
        target=object(),
        proof=object(),
        direct_dependencies=tuple(surface["direct_dependencies"]),
        closure=tuple(
            surface["transitive_closure_dependencies_in_replay_order"]
        ),
        diagnostics=diagnostics,
    )
    receipt = audit._validate_layered_baseline_parity(evidence, a23_row=row)
    assert receipt["status"] == (
        "exact-candidate-and-stable-body-identity-parity-with-distinct-provenance"
    )
    assert receipt["a2_3a_layered_artifact_sha256"] == layered[
        "artifact_sha256"
    ]
    assert receipt["retained_body_sources_root_sha256"] == audit._sha256_json(
        receipt["a2_3a_body_sources_preimage"]
    )
    assert receipt["fresh_body_provenance_root_sha256"] == audit._sha256_json(
        provenance_preimage
    )
    assert receipt["stable_body_identity_fields"] == [
        "body_certificate_sha256",
        "dependencies",
        "index",
        "name",
    ]
    assert receipt["stable_body_identity_root_sha256"] == audit._sha256_json(
        identity_preimage
    )
    assert receipt["fresh_body_provenance_root_sha256"] != receipt[
        "retained_body_sources_root_sha256"
    ]

    mutations: list[audit._CandidateEvidence] = []
    for field, value in (
        ("artifact_sha256", "0" * 64),
        ("artifact_bytes", diagnostics["artifact_bytes"] + 1),
        ("candidate_formula_sha256", "0" * 64),
        ("candidate_metrics", {}),
        ("candidate_proof_term_sha256", "0" * 64),
        ("compiler_result_type", "foreign"),
        ("dependency_edge_count", diagnostics["dependency_edge_count"] + 1),
        ("fuel", diagnostics["fuel"] + 1),
        ("layer_count", diagnostics["layer_count"] + 1),
        ("layers", []),
        (
            "maximum_package_formula_depth",
            diagnostics["maximum_package_formula_depth"] + 1,
        ),
        ("node_names_in_replay_order", []),
        ("node_names_lf_sha256", "0" * 64),
        ("node_count", diagnostics["node_count"] + 1),
        (
            "package_formula_occurrences",
            diagnostics["package_formula_occurrences"] + 1,
        ),
        ("modular_body_identity_root_sha256", "0" * 64),
        ("modular_body_provenance_root_sha256", "not-a-sha256"),
        ("modular_body_identity_preimage", {}),
        ("modular_body_provenance_preimage", {}),
    ):
        changed = deepcopy(diagnostics)
        changed[field] = value
        mutations.append(
            audit._CandidateEvidence(
                target=evidence.target,
                proof=evidence.proof,
                direct_dependencies=evidence.direct_dependencies,
                closure=evidence.closure,
                diagnostics=changed,
            )
        )
    mutations.extend(
        (
            audit._CandidateEvidence(
                target=evidence.target,
                proof=evidence.proof,
                direct_dependencies=evidence.direct_dependencies[:-1],
                closure=evidence.closure,
                diagnostics=diagnostics,
            ),
            audit._CandidateEvidence(
                target=evidence.target,
                proof=evidence.proof,
                direct_dependencies=evidence.direct_dependencies,
                closure=evidence.closure[:-1],
                diagnostics=diagnostics,
            ),
        )
    )
    for forged in mutations:
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="baseline|A2.3a|construction|differs",
        ):
            audit._validate_layered_baseline_parity(forged, a23_row=row)

    retained_forgery = deepcopy(row)
    retained_forgery["layered_bundle"]["body_sources"][0][
        "body_certificate_sha256"
    ] = "0" * 64
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="baseline|A2.3a|construction|differs|identity",
    ):
        audit._validate_layered_baseline_parity(
            evidence, a23_row=retained_forgery
        )


def test_selected_nonroot_rebuild_uses_a22_override_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "selected_rebuild"
    dependency = "dependency"
    omitted = "omitted"
    initial_receipt = {
        "certificate_sha256": "9" * 64,
        "receipt_sha256": "a" * 64,
    }
    expected_receipt = {
        "certificate_sha256": "2" * 64,
        "receipt_sha256": "3" * 64,
    }
    a21_rows = {
        name: {
            "declared_dependencies": [dependency, omitted],
            "readable": {"proof": initial_receipt},
            "recipe_audit": {
                "attempts": [
                    {
                        "after_dependencies": [dependency],
                        "before_dependencies": [dependency, omitted],
                        "omitted_dependency": omitted,
                        "outcome": "kernel-accepted",
                        "positive_receipt": expected_receipt,
                    }
                ],
                "positive_receipt": initial_receipt,
            },
            "record_sha256": "1" * 64,
        }
    }
    a22_rows = {
        name: {
            "body_receipt": expected_receipt,
            "candidate_direct_dependencies": [dependency],
            "direct_cut_spine": {"omitted_direct_dependency": omitted},
            "record_sha256": "b" * 64,
            "retained_direct_dependencies": [dependency, omitted],
            "rebuilt_certificate": {
                "artifact_sha256": "4" * 64,
                "proof_term_sha256": "5" * 64,
            },
        }
    }
    replay_rows = {
        name: {"formula_sha256": "6" * 64, "index": 7},
        dependency: {"proof_term_sha256": "8" * 64},
    }
    specs = {
        dependency: TheoremSpec(
            dependency,
            "forall n. n = n",
            (),
            ("intro n", "refl"),
            "Synthetic dependency.",
        )
    }
    certificate = SimpleNamespace(target=object(), proof=object())
    recovered = SimpleNamespace(target=object(), body=object())
    calls: list[str] = []
    monkeypatch.setattr(
        audit,
        "_decode_a22_certificate",
        lambda *_args, **_kwargs: (calls.append("a2.2") or certificate),
    )
    monkeypatch.setattr(
        audit,
        "_decode_replay_certificate",
        lambda *_args, **_kwargs: (calls.append("retained") or certificate),
    )
    monkeypatch.setattr(audit, "_closed_formula", lambda _statement: object())

    def recover(**kwargs: object) -> object:
        calls.append("recover")
        assert kwargs["dependencies"] == (dependency,)
        assert kwargs["expected_body_receipt"] == expected_receipt
        return recovered

    monkeypatch.setattr(audit, "recover_curried_modular_body", recover)
    target, dependencies, body, provenance = audit._recover_selected_modular_body(
        name,
        root=ROOT,
        a21_rows=a21_rows,
        a22_rows=a22_rows,
        replay_rows=replay_rows,
        specs=specs,
    )
    assert calls == ["a2.2", "recover"]
    assert target is recovered.target
    assert dependencies == (dependency,)
    assert body is recovered.body
    assert provenance["kind"] == "a2.2-direct-cut-rebuild"
    assert provenance["receipt_route"] == "a2.2-and-last-accepted-omission"
    assert provenance["accepted_omitted_dependency"] == omitted
    assert provenance["a2_2_record_sha256"] == "b" * 64
    assert provenance["artifact_sha256"] == "4" * 64
    assert provenance["proof_term_sha256"] == "5" * 64


def test_direct_surface_and_transitive_closure_cannot_alias() -> None:
    surface = audit._dependency_surface(
        ("direct",),
        ("prior", "direct"),
        basis="synthetic-route",
    )
    assert surface["direct_dependencies"] == ["direct"]
    assert surface["direct_dependency_count"] == 1
    assert surface["direct_dependencies_lf_sha256"] == _sha256(b"direct\n")
    assert surface["transitive_closure_dependencies_in_replay_order"] == [
        "prior",
        "direct",
    ]
    assert surface["transitive_closure_count"] == 2
    assert surface["transitive_closure_lf_sha256"] == _sha256(
        b"prior\ndirect\n"
    )
    assert surface["direct_dependencies_lf_sha256"] != surface[
        "transitive_closure_lf_sha256"
    ]


def test_closure_applies_exactly_one_root_override_and_keeps_nonroot_a22_vectors() -> None:
    replay_rows = {
        "retained_leaf": {"declared_dependencies": [], "index": 0},
        "fixed_leaf": {"declared_dependencies": [], "index": 1},
        "child": {
            "declared_dependencies": ["retained_leaf"],
            "index": 2,
        },
        "wrong_root_dependency": {"declared_dependencies": [], "index": 3},
        "root": {
            "declared_dependencies": ["wrong_root_dependency"],
            "index": 4,
        },
    }
    fixed_vectors = {
        "child": ("fixed_leaf",),
        "root": ("wrong_root_dependency",),
    }
    assert audit._transitive_closure(
        "root",
        ("child",),
        replay_rows=replay_rows,
        fixed_vectors=fixed_vectors,
    ) == ("fixed_leaf", "child")

    cycle = dict(fixed_vectors)
    cycle["child"] = ("root",)
    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="root|closure",
    ):
        audit._transitive_closure(
            "root",
            ("child",),
            replay_rows=replay_rows,
            fixed_vectors=cycle,
        )


def test_schema_keeps_every_global_authority_and_completeness_flag_false() -> None:
    constants = audit.pilot_dependency_vector_audit_schema()["constants"]
    for field in GLOBAL_FALSE_FIELDS:
        assert constants[field] is False, field
    assert constants["status"] == "candidate"
    assert constants["bounded_three_root_vector_audit_complete"] is False
    assert constants["bounded_three_root_protocol_frozen"] is True


def test_terminal_result_requires_all_44_rejected_and_keeps_vector_complete_false() -> None:
    assert audit._require_complete_attempt_aggregate(
        total_attempts=44,
        total_rejected=44,
        total_accepted=0,
    ) == {
        "bounded_protocol_executed": True,
        "bounded_three_root_vector_audit_complete": False,
        "single_omission_terminal_count": 44,
        "terminal_route_observations_complete": True,
    }
    for attempts, rejected, accepted in (
        (43, 43, 0),
        (44, 43, 1),
        (44, 44, 1),
        (44, 43, 0),
        (44, 0, 44),
        (-1, 44, 0),
        (True, 44, 0),
        (44, True, 0),
        (44, 44, False),
    ):
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="incomplete|accepted|unknown|terminal|refusing",
        ):
            audit._require_complete_attempt_aggregate(
                total_attempts=attempts,
                total_rejected=rejected,
                total_accepted=accepted,
            )


def test_module_exposes_no_public_authority_or_publication_entry_point() -> None:
    exported = tuple(
        getattr(
            audit,
            "__all__",
            tuple(name for name in vars(audit) if not name.startswith("_")),
        )
    )
    forbidden = ("admit", "publish", "freeze", "best", "minimal")
    assert not [
        name
        for name in exported
        if any(token in name.lower() for token in forbidden)
    ]


def test_no_retained_a23b_result_exists_and_historical_inputs_are_not_rewritten() -> None:
    assert not list(
        (ROOT / "artifacts/peano-hydra").glob(
            "l0-pilot-dependency-vector-audit-*.json"
        )
    )
    for path, expected in UPSTREAM_SHA256.items():
        assert _sha256(path.read_bytes()) == expected


def test_cli_never_adopts_a_preimported_producer_as_authenticated() -> None:
    assert sys.modules[audit.__name__] is audit
    cli = _load_cli()
    assert not hasattr(cli, "_existing_producer")
    assert cli.LibraryPilotDependencyVectorAuditError is not (
        audit.LibraryPilotDependencyVectorAuditError
    )
    assert cli._loaded_producer is None
    with pytest.raises(cli.LibraryPilotDependencyVectorAuditError):
        cli.build_candidate_pilot_dependency_vector_audit()


def test_cli_authenticates_exact_44_source_vector_without_importing_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    before_modules = set(sys.modules)
    reads: list[Path] = []
    original = cli._read_regular

    def tracked(path: Path, *, label: str, limit: int) -> bytes:
        reads.append(path)
        return original(path, label=label, limit=limit)

    monkeypatch.setattr(cli, "_read_regular", tracked)
    schema = cli._authenticate_schema_and_sources()
    expected = [
        cli.SCHEMA_PATH,
        *(
            cli.ROOT / row["path"]
            for row in schema["implementation_sources"]
        ),
    ]
    assert reads == expected
    assert len(expected) == 45
    assert len(schema["implementation_sources"]) == 44
    assert schema["implementation_source_root_sha256"] == (
        cli.IMPLEMENTATION_SOURCE_ROOT_SHA256
    )
    introduced = set(sys.modules) - before_modules
    assert not {
        name
        for name in introduced
        if name == "peano_lab"
        or name.startswith("peano_lab.")
        or name == "training"
        or name.startswith("training.")
    }


def test_cli_implementation_byte_drift_aborts_before_any_import() -> None:
    body = f"""
original = cli._read_regular
target = cli.ROOT / {audit._PINNED_IMPLEMENTATION[0][0].as_posix()!r}
def corrupt(path, *, label, limit):
    raw = original(path, label=label, limit=limit)
    return raw + b"\\n" if path == target else raw
cli._read_regular = corrupt
try:
    cli._authenticate_schema_and_sources()
except cli.LibraryPilotDependencyVectorAuditError:
    pass
else:
    raise SystemExit("corrupt implementation source was accepted")
forbidden = [
    name for name in sys.modules
    if name == "peano_lab" or name.startswith("peano_lab.")
    or name == "training" or name.startswith("training.")
]
if forbidden:
    raise SystemExit("preflight imported code: " + repr(forbidden))
print("preimport-byte-drift-rejected")
"""
    cli = _load_cli()
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "preimport-byte-drift-rejected"


def test_cli_reads_exact_four_file_source_state_before_producer_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    state = _producer_source_state()
    state_path = tmp_path / "source-state.json"
    state_path.write_bytes(audit.canonical_document_bytes(state))
    loaded, producer_raw = cli._read_producer_source_state(state_path)
    assert loaded == state
    assert producer_raw == (
        ROOT / audit.PRODUCER_SOURCE_FILES[1]
    ).read_bytes()
    assert tuple(row["path"] for row in loaded["files"]) == tuple(
        path.as_posix() for path in audit.PRODUCER_SOURCE_FILES
    )

    events: list[str] = []
    monkeypatch.setattr(cli, "_require_controlled_worker", lambda: events.append("worker"))
    monkeypatch.setattr(
        cli,
        "_authenticate_schema_and_sources",
        lambda: events.append("implementation-preflight"),
    )
    monkeypatch.setattr(
        cli,
        "_read_producer_source_state",
        lambda _path: (_ for _ in ()).throw(
            cli.LibraryPilotDependencyVectorAuditError("four-file drift")
        ),
    )
    monkeypatch.setattr(
        cli,
        "_load_producer_after_preflight",
        lambda _raw: events.append("producer-executed"),
    )
    with pytest.raises(cli.LibraryPilotDependencyVectorAuditError):
        cli._controlled_load(state_path)
    assert events == ["worker", "implementation-preflight"]


def test_cli_controlled_loader_uses_minimal_stub_and_exact_environment(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    state_path = tmp_path / "source-state.json"
    state_path.write_bytes(
        audit.canonical_document_bytes(_producer_source_state())
    )
    allowed = {
        "training.peano_hydra.library_construction_rebuild_core",
        "training.peano_hydra.library_optimizer_comparison_pilot",
        "training.peano_hydra.library_pilot_dependency_vector_audit",
        "training.peano_hydra.library_replay_pack",
    }
    body = f"""
module, state = cli._controlled_load(Path({str(state_path)!r}))
forbidden = sorted(
    name for name in sys.modules
    if name.startswith("training.peano_hydra.") and name not in {allowed!r}
)
package = sys.modules.get("training.peano_hydra")
if forbidden or package is None or hasattr(package, "__file__"):
    raise SystemExit("initializer boundary failed: " + repr(forbidden))
if Path(module.__file__).resolve() != cli.PRODUCER_PATH.resolve():
    raise SystemExit("producer origin drifted")
if len(module._PINNED_IMPLEMENTATION) != 44:
    raise SystemExit("implementation vector count drifted")
print("controlled-minimal-stub-load-ok")
"""
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "controlled-minimal-stub-load-ok"


def test_cli_rejects_preloaded_peano_lab_before_executing_producer() -> None:
    body = '''
import types
local_error = cli.LibraryPilotDependencyVectorAuditError
sys.modules["peano_lab"] = types.ModuleType("peano_lab")
producer_raw = b"""\
class LibraryPilotDependencyVectorAuditError(ValueError):
    pass
def _require_implementation(root):
    return None
"""
try:
    cli._load_producer_after_preflight(producer_raw)
except local_error:
    pass
else:
    raise SystemExit("preloaded peano_lab was accepted")
if cli._loaded_producer is not None:
    raise SystemExit("failed contamination check authenticated a producer")
if cli.LibraryPilotDependencyVectorAuditError is not local_error:
    raise SystemExit("CLI error class was replaced")
if any(name == "training" or name.startswith("training.") for name in sys.modules):
    raise SystemExit("contamination failure installed training stubs")
print("preloaded-peano-lab-rejected")
'''
    cli = _load_cli()
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "preloaded-peano-lab-rejected"


def test_cli_implementation_validation_failure_is_atomic_and_local() -> None:
    body = '''
local_error = cli.LibraryPilotDependencyVectorAuditError
producer_raw = b"""\
class LibraryPilotDependencyVectorAuditError(ValueError):
    pass
def _require_implementation(root):
    raise LibraryPilotDependencyVectorAuditError("synthetic implementation drift")
"""
try:
    cli._load_producer_after_preflight(producer_raw)
except local_error:
    pass
else:
    raise SystemExit("implementation validation failure was accepted")
if cli._loaded_producer is not None:
    raise SystemExit("failed implementation authenticated a producer")
if cli.LibraryPilotDependencyVectorAuditError is not local_error:
    raise SystemExit("CLI error class was replaced")
if any(
    name == "training" or name.startswith("training.")
    or name == "peano_lab" or name.startswith("peano_lab.")
    for name in sys.modules
):
    raise SystemExit("failed implementation left provisional modules")
for wrapper, arguments in (
    (cli.build_candidate_pilot_dependency_vector_audit, ()),
    (cli.canonical_document_bytes, (dict(),)),
):
    try:
        wrapper(*arguments)
    except local_error:
        pass
    else:
        raise SystemExit("wrapper used an unauthenticated producer")
print("implementation-failure-atomic")
'''
    cli = _load_cli()
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "implementation-failure-atomic"


def test_cli_source_state_validation_failure_rolls_back_loaded_producer(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    state_path = tmp_path / "source-state.json"
    state_path.write_bytes(
        audit.canonical_document_bytes(_producer_source_state())
    )
    body = f"""
local_error = cli.LibraryPilotDependencyVectorAuditError
original_read = cli._read_producer_source_state
def forged_read(path):
    state, producer_raw = original_read(path)
    state["git_verified"] = True
    return state, producer_raw
cli._read_producer_source_state = forged_read
try:
    cli._controlled_load(Path({str(state_path)!r}))
except local_error:
    pass
else:
    raise SystemExit("invalid source state was accepted")
if cli._loaded_producer is not None:
    raise SystemExit("source-state failure authenticated a producer")
if cli.LibraryPilotDependencyVectorAuditError is not local_error:
    raise SystemExit("CLI error class was replaced")
if any(name == "training" or name.startswith("training.") for name in sys.modules):
    raise SystemExit("source-state failure left provisional training modules")
for wrapper, arguments in (
    (cli.build_candidate_pilot_dependency_vector_audit, ()),
    (cli.canonical_document_bytes, (dict(),)),
):
    try:
        wrapper(*arguments)
    except local_error:
        pass
    else:
        raise SystemExit("wrapper used a rolled-back producer")
print("source-state-failure-atomic")
"""
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "source-state-failure-atomic"


def test_cli_controlled_worker_rejects_present_even_empty_injection_env() -> None:
    body = """
import os
cli._require_controlled_worker()
for name in (
    "PYTHONCASEOK",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTHONOPTIMIZE",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "PYTHONUSERBASE",
    "PYTHONWARNINGS",
):
    os.environ[name] = ""
    try:
        cli._require_controlled_worker()
    except cli.LibraryPilotDependencyVectorAuditError:
        pass
    else:
        raise SystemExit("empty injection variable accepted: " + name)
    del os.environ[name]
print("empty-injection-env-rejected")
"""
    cli = _load_cli()
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "empty-injection-env-rejected"


def test_cli_controlled_worker_rejects_optimized_interpreter() -> None:
    body = """
try:
    cli._require_controlled_worker()
except cli.LibraryPilotDependencyVectorAuditError:
    print("optimized-worker-rejected")
else:
    raise SystemExit("optimized worker was accepted")
"""
    cli = _load_cli()
    completed = subprocess.run(
        [
            _controlled_python_executable(),
            "-O",
            "-B",
            "-P",
            "-s",
            "-S",
            "-c",
            _cli_subprocess_source(body),
        ],
        cwd=ROOT,
        env=_controlled_worker_environment(cli),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "optimized-worker-rejected"


def test_cli_publish_is_create_only_atomic_regular_and_exact(tmp_path: Path) -> None:
    cli = _load_cli()
    destination = tmp_path / "audit.json"
    raw = b'{"fixture":true}\n'
    cli._publish(destination, raw)
    metadata = destination.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not stat.S_ISLNK(metadata.st_mode)
    assert destination.read_bytes() == raw
    cli._read_exact(destination, raw)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorAuditError,
        match="already exists",
    ):
        cli._publish(destination, b"replacement\n")
    assert destination.read_bytes() == raw

    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorAuditError,
        match="link|parent|directory",
    ):
        cli._publish(linked_parent / "forbidden.json", raw)
    assert not (actual_parent / "forbidden.json").exists()


def test_cli_has_no_default_build_or_write(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = _load_cli()
    builds: list[object] = []
    writes: list[object] = []
    monkeypatch.setattr(
        cli,
        "build_candidate_pilot_dependency_vector_audit",
        lambda **_kwargs: builds.append("build"),
    )
    monkeypatch.setattr(cli, "_publish", lambda *_args: writes.append("publish"))
    monkeypatch.setattr(cli, "_read_exact", lambda *_args: writes.append("read"))
    monkeypatch.setattr(sys, "argv", [str(CLI_PATH)])

    cli.main()

    assert builds == []
    assert writes == []
    assert "no build or retained write requested" in capsys.readouterr().out


def test_loader_schema_and_cli_reject_symlink_and_fifo_without_blocking(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    actual = tmp_path / "actual.json"
    actual.write_bytes(b"{}\n")
    linked = tmp_path / "linked.json"
    try:
        linked.symlink_to(actual)
    except OSError:
        pytest.skip("symlinks are unavailable")
    with pytest.raises(audit.LibraryPilotDependencyVectorAuditError):
        audit.load_candidate_pilot_dependency_vector_audit(linked)
    with pytest.raises(cli.LibraryPilotDependencyVectorAuditError):
        cli._read_exact(linked, b"{}\n")

    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir()
    (actual_parent / "audit.json").write_bytes(b"{}\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(audit.LibraryPilotDependencyVectorAuditError):
        audit._read_regular_bytes(
            linked_parent / "audit.json",
            label="pilot dependency-vector audit",
            limit=audit.MAX_DOCUMENT_BYTES,
        )
    with pytest.raises(cli.LibraryPilotDependencyVectorAuditError):
        cli._read_exact(linked_parent / "audit.json", b"{}\n")

    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        return
    fifo = tmp_path / "fifo.json"
    os.mkfifo(fifo)
    with pytest.raises(audit.LibraryPilotDependencyVectorAuditError, match="regular"):
        audit.load_candidate_pilot_dependency_vector_audit(fifo)
    with pytest.raises(cli.LibraryPilotDependencyVectorAuditError):
        cli._read_exact(fifo, b"{}\n")


def test_json_and_retained_artifact_paths_fail_closed_on_ambiguity() -> None:
    for raw in (
        b'{"duplicate":1,"duplicate":2}\n',
        b'{"not_finite":NaN}\n',
        b'{"not_finite":Infinity}\n',
    ):
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="duplicate|JSON|constant|decode|invalid",
        ):
            audit._decode_document(raw, "synthetic", limit=1_024)

    for value in (
        None,
        False,
        "",
        ".",
        "../escape.json",
        "/absolute/escape.json",
        "nested/../escape.json",
    ):
        replay_rows = {
            "fixture": {
                "artifact": {
                    "bytes": 1,
                    "path": value,
                    "sha256": "0" * 64,
                }
            }
        }
        with pytest.raises(
            audit.LibraryPilotDependencyVectorAuditError,
            match="path|unsafe|malformed",
        ):
            audit._decode_replay_certificate(
                "fixture", root=ROOT, replay_rows=replay_rows
            )


def test_semantically_equal_noncanonical_schema_bytes_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = json.loads(SCHEMA_PATH.read_bytes())
    compact = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert compact != audit.canonical_document_bytes(
        value, limit=audit.MAX_SCHEMA_BYTES
    )
    original = audit._read_regular_bytes

    def substitute(path: Path, *, label: str, limit: int) -> bytes:
        if path == audit.PILOT_DEPENDENCY_VECTOR_AUDIT_SCHEMA_PATH:
            return compact
        return original(path, label=label, limit=limit)

    monkeypatch.setattr(audit, "_read_regular_bytes", substitute)
    with pytest.raises(audit.LibraryPilotDependencyVectorAuditError, match="canonical"):
        audit.pilot_dependency_vector_audit_schema()


def test_fully_rerooted_global_flag_forgery_fails_exact_reconstruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = {
        "optimized_vector_independently_audited": False,
        "producer_source_state": {},
        "root_preimage": {
            "format": audit.PILOT_DEPENDENCY_VECTOR_AUDIT_ROOT_PREIMAGE_FORMAT,
            "payload": {"optimized_vector_independently_audited": False},
            "v": 1,
        },
        "root_sha256": "0" * 64,
    }
    baseline["root_sha256"] = audit._sha256_json(baseline["root_preimage"])
    forged = deepcopy(baseline)
    forged["optimized_vector_independently_audited"] = True
    forged["root_preimage"]["payload"][
        "optimized_vector_independently_audited"
    ] = True
    forged["root_sha256"] = audit._sha256_json(forged["root_preimage"])
    monkeypatch.setattr(audit, "pilot_dependency_vector_audit_schema", lambda: {})
    monkeypatch.setattr(
        audit,
        "_build_candidate_pilot_dependency_vector_audit",
        lambda _root, *, producer_source_state: deepcopy(baseline),
    )
    monkeypatch.setattr(audit, "_repository_root", lambda _root: ROOT)

    with pytest.raises(
        audit.LibraryPilotDependencyVectorAuditError,
        match="fixed-source reconstruction|differs",
    ):
        audit.validate_candidate_pilot_dependency_vector_audit(
            forged, repository_root=ROOT
        )
