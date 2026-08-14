"""Focused contracts for the result-independent Hydra A2.3b verifier.

These tests never run the 44-attempt producer campaign.  Compact synthetic
kernel artifacts exercise the codec/checker boundary; fixed retained inputs
exercise only the six baseline transports that the independent verifier will
later join to a producer result.
"""

from __future__ import annotations

import ast
import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PY_ROOT = ROOT / "peano-lab" / "py"
for path in (str(ROOT), str(PY_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from peano_lab.kernel.artifact_codec import (  # noqa: E402
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import Cut, EqRefl, Hyp  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
import training.peano_hydra.library_pilot_dependency_vector_audit_verifier as verifier  # noqa: E402


MODULE_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_audit_verifier.py"
)
CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_audit.py"
)
ISOLATED_PYTHON = shutil.which("python3.12") or shutil.which("python3.11")
FORBIDDEN_IMPORT_PREFIXES = (
    "peano_lab.engine",
    "peano_lab.library",
    "peano_lab.tactics",
    "training.peano_hydra",
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _isolated_environment() -> dict[str, str]:
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
    environment["PYTHONPYCACHEPREFIX"] = verifier.PYCACHE_PREFIX
    return environment


def _isolated_argv(*arguments: str) -> list[str]:
    if ISOLATED_PYTHON is None:
        pytest.skip("no CPython with -P safe-path support is available")
    return [ISOLATED_PYTHON, "-B", "-P", "-s", "-S", *arguments]


def _artifact(*, cut: bool = False, valid: bool = True, fuel: int = 40):
    zero = Zero()
    target = Eq(zero, zero if valid else Succ(zero))
    proposition = Eq(zero, zero)
    proof = (
        Cut(proposition, proposition, EqRefl(zero), Hyp(0))
        if cut
        else EqRefl(zero)
    )
    raw = encode_artifact_bounded(fuel, target, proof, max_bytes=10_000)
    return raw, target, proof


def _producer_source_state() -> dict[str, object]:
    payload = {
        "commit_sha1": "1" * 40,
        "files": [
            {"bytes": size, "path": path.as_posix(), "sha256": digest}
            for path, size, digest in verifier.PRODUCER_SOURCE_FILES
        ],
        "format": verifier.PRODUCER_SOURCE_STATE_FORMAT,
        "git_verified": False,
        "tree_sha1": "2" * 40,
        "v": 1,
    }
    preimage = {
        "format": verifier.PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": payload,
        "v": 1,
    }
    return {
        **payload,
        "root_preimage": preimage,
        "root_sha256": verifier._sha256_json(
            preimage, limit=verifier.MAX_SCHEMA_BYTES
        ),
    }


def test_public_surface_and_receipt_claim_split_are_narrow() -> None:
    assert set(verifier.__all__) == {
        "LibraryPilotDependencyVectorAuditVerificationError",
        "VERIFICATION_FALSE_FIELDS",
        "VERIFICATION_RECEIPT_BODY_FIELDS",
        "VERIFICATION_RECEIPT_FIELDS",
        "canonical_verification_receipt_bytes",
        "load_and_verify_pilot_dependency_vector_audit",
        "validate_pilot_dependency_vector_audit_verification_receipt",
        "verify_pilot_dependency_vector_audit",
    }
    assert not any(
        fragment in name
        for name in verifier.__all__
        for fragment in ("compile", "build", "publish", "admit", "minimal")
    )
    assert {
        "bounded_three_root_vector_audit_complete",
        "negative_observations_independently_verified",
        "producer_git_verified",
        "producer_observations_execution_bound",
        "route_rejections_independently_verified",
    }.issubset(verifier.VERIFICATION_FALSE_FIELDS)
    assert {
        "kernel_baseline_artifacts_verified",
        "producer_observations_structurally_verified",
        "structural_receipts_verified",
    }.issubset(verifier.VERIFICATION_RECEIPT_BODY_FIELDS)


def test_static_import_policy_is_stdlib_and_kernel_only() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(
        name.startswith(prefix)
        for name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )
    peano_imports = [name for name in imported if name.startswith("peano_lab")]
    assert peano_imports
    assert all(name.startswith("peano_lab.kernel") for name in peano_imports)


def test_cli_exact_loader_has_no_default_verification_or_write() -> None:
    completed = subprocess.run(
        _isolated_argv(str(CLI_PATH)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "no verification or retained write" in completed.stdout
    incomplete = subprocess.run(
        _isolated_argv(str(CLI_PATH), "--candidate", "missing.json"),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert incomplete.returncode == 2


def test_cli_loader_keeps_forbidden_modules_absent() -> None:
    code = r'''
import importlib.util
import sys
spec = importlib.util.spec_from_file_location("_a23b_cli_test", sys.argv[1])
if spec is None or spec.loader is None:
    raise SystemExit("no CLI spec")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
forbidden = [
    name for name in sys.modules
    if name.startswith("peano_lab.engine")
    or name.startswith("peano_lab.library")
    or name.startswith("peano_lab.tactics")
    or name == "training" or name.startswith("training.")
]
if forbidden:
    raise SystemExit(repr(sorted(forbidden)))
if module._CACHE_PREFLIGHTED is not True or module._KERNEL_PREFLIGHTED is not True:
    raise SystemExit("preflight not retained")
'''
    completed = subprocess.run(
        _isolated_argv("-c", code, str(CLI_PATH)),
        cwd=ROOT,
        env=_isolated_environment(),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_frozen_sources_inputs_and_six_baseline_artifacts_kernel_check() -> None:
    fixed = verifier._load_fixed_inputs(ROOT)
    assert len(fixed["implementation_rows"]) == 44
    assert len(fixed["kernel_sources"]) == 8
    assert len(fixed["replay_rows"]) == 384
    accepted = []
    for _index, name in verifier.EXPECTED_THEOREMS:
        observations = verifier._baseline_artifact_observations(
            name=name,
            a22_row=fixed["a22_rows"][name],
            a23_row=fixed["a23_rows"][name],
            replay_row=fixed["replay_rows"][name],
        )
        assert tuple(observations) == verifier.ROUTES
        accepted.extend(
            observation["kernel_accepted"]
            for observation in observations.values()
        )
    assert accepted == [True] * 6


def test_unknown_job_220218_mismatch_diagnostic_goldens_reconstruct() -> None:
    """Regress mismatch diagnostics; grant no result/execution authority."""

    goldens = {
        "odd_add_odd": {
            "baseline": (
                "f5f47017f83000f11e9d172809bef8a24a8129788a5846834d87dea3503f5861"
            ),
            "identity": (
                "2b94fa7bfc83bbc35831a6c7e93d3847731130aa3cc6aaf4a13d904e672dcd64"
            ),
            "provenance": (
                "17a2a8f785a2d8bd53e8f0126b20fa6121589d2ae2129d8f1dd952becce7fb79"
            ),
            "source_count": 6,
        },
        "finite_bounded_injective_surjective": {
            "baseline": (
                "1a26e5387c603a5486d2a5997a1f00a502d7998820fc0ea75a455d5267d58f78"
            ),
            "identity": (
                "cbd44b126bdee88f9129676a7592bed8b37a4c25ead091ea049faf2bb9c129a7"
            ),
            "provenance": (
                "b6ff38ab7e5262acefdf7a2aa69c0a38d7828c53edb2268831c0ab8642f6a750"
            ),
            "source_count": 120,
        },
        "beta_product_swap_last_invariant": {
            "baseline": (
                "09baf29e9dd471d30d23854aed3e0337fb0d82dbb73e6c9aec1c84507eff281a"
            ),
            "identity": (
                "2ba58aca941891764257b2ff86175c00f8a5cf546e0448143c52e1fa0cc85501"
            ),
            "provenance": (
                "1daa8ea8d13a1fb2af2e988455dc7a3a466ba5e65e18e30f9f59cd1060bc8fd6"
            ),
            "source_count": 32,
        },
    }
    fixed = verifier._load_fixed_inputs(ROOT)
    layered_vectors = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in fixed["a22_rows"].items()
    }
    for index, name in verifier.EXPECTED_THEOREMS:
        dependencies = verifier.EXPECTED_DIRECT[name]
        closure = verifier._closure(
            name,
            dependencies,
            replay_rows=fixed["replay_rows"],
            fixed_vectors=layered_vectors,
        )
        diagnostics = verifier._expected_layered_diagnostics(
            name=name,
            dependencies=dependencies,
            closure=closure,
            root_body_receipt=verifier._expected_root_body_receipt(
                fixed["a22_rows"][name], fixed["replay_rows"][name]
            ),
            a21_rows=fixed["a21_rows"],
            a22_rows=fixed["a22_rows"],
            a23_row=fixed["a23_rows"][name],
            replay_rows=fixed["replay_rows"],
        )
        observation = verifier._baseline_artifact_observations(
            name=name,
            a22_row=fixed["a22_rows"][name],
            a23_row=fixed["a23_rows"][name],
            replay_row=fixed["replay_rows"][name],
        )[verifier.LAYERED_ROUTE]
        proof = verifier._proof_receipt_from_observation(observation)
        surface = verifier._surface(
            dependencies,
            closure,
            basis=(
                "proposed-layered-root-input-graph-not-final-cut-spine"
            ),
        )
        baseline_preimage = {
            "diagnostics": diagnostics,
            "format": verifier.BASELINE_RECEIPT_PREIMAGE_FORMAT,
            "index": index,
            "name": name,
            "proof": proof,
            "route": verifier.LAYERED_ROUTE,
            "surface": surface,
            "v": 1,
        }
        assert {
            "baseline": verifier._sha256_json(baseline_preimage),
            "identity": diagnostics["modular_body_identity_root_sha256"],
            "provenance": diagnostics[
                "modular_body_provenance_root_sha256"
            ],
            "source_count": len(diagnostics["fresh_body_sources"]),
        } == goldens[name]
        first_source = diagnostics["fresh_body_sources"][0]
        assert "a2_1_record_sha256" in first_source
        assert "formula_sha256" in first_source


def test_producer_source_state_binds_exact_four_files_and_false_git() -> None:
    state = _producer_source_state()
    assert verifier._validate_producer_source_state(state, root=ROOT) == state
    for mutate in (
        lambda value: value.__setitem__("git_verified", True),
        lambda value: value["files"].reverse(),
        lambda value: value["files"][0].__setitem__("sha256", "0" * 64),
        lambda value: value.__setitem__("root_sha256", "0" * 64),
    ):
        changed = deepcopy(state)
        mutate(changed)
        with pytest.raises(
            verifier.LibraryPilotDependencyVectorAuditVerificationError
        ):
            verifier._validate_producer_source_state(changed, root=ROOT)


def test_independent_artifact_inspector_checks_codec_kernel_and_metrics() -> None:
    raw, target, proof = _artifact(cut=True, fuel=77)
    decoded, observation = verifier._inspect_artifact(
        raw,
        label="synthetic-cut",
        expected_artifact_sha256=_sha(raw),
        expected_fuel=77,
        expected_formula_sha256=_sha(encode_formula(target)),
        expected_proof_sha256=_sha(encode_proof(proof)),
    )
    assert decoded == target
    assert observation["kernel_accepted"] is True
    assert observation["kernel_context"] == "empty"
    assert observation["metrics"] == {
        "artifact_bytes": len(raw),
        "cut_nodes": 1,
        "proof_depth": 2,
        "proof_nodes": 3,
    }
    mutations = (
        {"expected_artifact_sha256": "0" * 64},
        {"expected_fuel": 78},
        {"expected_formula_sha256": "1" * 64},
        {"expected_proof_sha256": "2" * 64},
    )
    baseline = {
        "expected_artifact_sha256": _sha(raw),
        "expected_fuel": 77,
        "expected_formula_sha256": _sha(encode_formula(target)),
        "expected_proof_sha256": _sha(encode_proof(proof)),
    }
    for mutation in mutations:
        arguments = {**baseline, **mutation}
        with pytest.raises(
            verifier.LibraryPilotDependencyVectorAuditVerificationError
        ):
            verifier._inspect_artifact(raw, label="mutated", **arguments)
    invalid, invalid_target, invalid_proof = _artifact(valid=False)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorAuditVerificationError,
        match="kernel rejected",
    ):
        verifier._inspect_artifact(
            invalid,
            label="kernel-invalid",
            expected_artifact_sha256=_sha(invalid),
            expected_fuel=40,
            expected_formula_sha256=_sha(encode_formula(invalid_target)),
            expected_proof_sha256=_sha(encode_proof(invalid_proof)),
        )


def test_reverse_single_omission_order_is_exactly_22_inputs() -> None:
    assert verifier._single_omission_vectors(("a", "b", "c")) == (
        ("c", ("a", "b")),
        ("b", ("a", "c")),
        ("a", ("b", "c")),
    )
    unique = sum(
        len(verifier._single_omission_vectors(verifier.EXPECTED_DIRECT[name]))
        for _index, name in verifier.EXPECTED_THEOREMS
    )
    assert unique == verifier.EXPECTED_UNIQUE_SHARED_OBSERVATION_COUNT == 22
    assert 2 * unique == verifier.EXPECTED_ATTEMPT_COUNT == 44


def test_rejection_classification_is_type_literal_and_script_bound() -> None:
    script = ("intro n", "refl")
    command = {
        "cause_type": "TacticError",
        "command": "refl",
        "command_index": 1,
        "kind": "exact-recipe-rejection",
        "phase": "command",
    }
    assert verifier._verify_failure(command, script=script) == command
    finalization = {
        "cause_type": "InvalidProof",
        "command": None,
        "command_index": None,
        "kind": "exact-recipe-rejection",
        "phase": "finalization",
    }
    assert verifier._verify_failure(finalization, script=script) == finalization
    for mutation in (
        lambda value: value.__setitem__("cause_type", "TacticSyntaxError"),
        lambda value: value.__setitem__("command_index", True),
        lambda value: value.__setitem__("command", "intro n"),
        lambda value: value.__setitem__("kind", "resource-limit"),
    ):
        changed = deepcopy(command)
        mutation(changed)
        with pytest.raises(
            verifier.LibraryPilotDependencyVectorAuditVerificationError
        ):
            verifier._verify_failure(changed, script=script)


def _synthetic_attempt(route: str) -> dict[str, object]:
    full = ("a", "b")
    trial = ("a",)
    failure = {
        "cause_type": None,
        "command": None,
        "command_index": None,
        "kind": "exact-recipe-rejection",
        "phase": "finalization",
    }
    shared = {
        "candidate_body_compiler_source_sha256": (
            verifier.CANDIDATE_BODY_COMPILER_SOURCE_SHA256
        ),
        "dependencies": list(trial),
        "failure": failure,
        "format": "peano-hydra-shared-root-body-observation-preimage",
        "index": 7,
        "name": "fixture",
        "v": 1,
    }
    basis = (
        "readable-literal-direct-cut-closure"
        if route == verifier.READABLE_ROUTE
        else "proposed-layered-root-input-graph-not-final-cut-spine"
    )
    row = {
        "after_dependencies": list(full),
        "attempted_dependencies": list(trial),
        "attempt_index": 0,
        "baseline_formula_sha256": "1" * 64,
        "baseline_root_body_certificate_sha256": "2" * 64,
        "before_dependencies": list(full),
        "failure": failure,
        "index": 7,
        "layered_compiler_invoked": False,
        "name": "fixture",
        "omitted_dependency": "b",
        "outcome": "exact-route-rejected",
        "route": route,
        "route_specific_assembly_reached": False,
        "script_sha256": verifier._lf_hash(("refl",)),
        "shared_root_body_observation_preimage": shared,
        "shared_root_body_observation_sha256": verifier._sha256_json(
            shared, limit=verifier.MAX_SCHEMA_BYTES
        ),
        "terminal_stage": "root-body-regeneration",
        "trial_surface": verifier._surface(trial, ("a",), basis=basis),
    }
    row["record_sha256"] = verifier._record_hash(row)
    return row


def test_attempt_records_are_44_route_records_not_22_independent_rejections() -> None:
    readable = _synthetic_attempt(verifier.READABLE_ROUTE)
    layered = _synthetic_attempt(verifier.LAYERED_ROUTE)
    verified_readable = verifier._verify_attempt(
        readable,
        route=verifier.READABLE_ROUTE,
        name="fixture",
        index=7,
        attempt_index=0,
        omitted_dependency="b",
        candidate_dependencies=("a",),
        full_dependencies=("a", "b"),
        script=("refl",),
        closure=("a",),
        baseline_formula_sha256="1" * 64,
        baseline_root_body_sha256="2" * 64,
    )
    verified_layered = verifier._verify_attempt(
        layered,
        route=verifier.LAYERED_ROUTE,
        name="fixture",
        index=7,
        attempt_index=0,
        omitted_dependency="b",
        candidate_dependencies=("a",),
        full_dependencies=("a", "b"),
        script=("refl",),
        closure=("a",),
        baseline_formula_sha256="1" * 64,
        baseline_root_body_sha256="2" * 64,
    )
    baseline_body = {"certificate_sha256": "2" * 64}
    preimage = {
        "format": "peano-hydra-cross-route-shared-baseline-body-preimage",
        "root_body_receipt": baseline_body,
        "v": 1,
    }
    recorded = {
        "baseline_root_body_receipt_sha256": verifier._sha256_json(preimage),
        "paired_attempt_count": 1,
        "status": "shared-root-body-consistent",
    }
    _receipt, unique = verifier._verify_shared_route_pairing(
        [verified_readable],
        [verified_layered],
        baseline_root_body_receipt=baseline_body,
        recorded=recorded,
    )
    assert len(unique) == 1
    assert verified_readable["record_sha256"] != verified_layered["record_sha256"]
    changed = deepcopy(layered)
    changed["shared_root_body_observation_sha256"] = "9" * 64
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorAuditVerificationError
    ):
        verifier._verify_shared_route_pairing(
            [readable],
            [changed],
            baseline_root_body_receipt=baseline_body,
            recorded=recorded,
        )


def test_strict_json_base64_and_canonical_transport_fail_closed() -> None:
    for raw in (b'{"x":1,"x":2}\n', b'{"x":1.0}\n', b'{"x":NaN}\n'):
        with pytest.raises(
            verifier.LibraryPilotDependencyVectorAuditVerificationError
        ):
            verifier._decode_document(raw, "fixture", limit=100)
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorAuditVerificationError
    ):
        verifier.canonical_verification_receipt_bytes(cyclic)
    raw, _target, _proof = _artifact()
    encoded = base64.b64encode(raw).decode("ascii")
    assert verifier._decode_base64(encoded, label="fixture") == raw
    with pytest.raises(
        verifier.LibraryPilotDependencyVectorAuditVerificationError
    ):
        verifier._decode_base64(encoded + "\n", label="fixture")


def test_no_a23b_candidate_or_verification_result_is_retained() -> None:
    artifact_root = ROOT / "artifacts/peano-hydra"
    assert not list(
        artifact_root.glob("l0-pilot-dependency-vector-audit-*.json")
    )
