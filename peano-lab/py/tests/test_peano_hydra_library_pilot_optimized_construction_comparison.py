from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCHEMA = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-optimized-construction-comparison-schema-v1.json"
)
PRODUCER = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_optimized_construction_comparison.py"
)
VERIFIER = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_optimized_construction_comparison_verifier.py"
)
BUILD_CLI = (
    ROOT
    / "scripts/build_peano_hydra_library_pilot_optimized_construction_comparison.py"
)
VERIFY_CLI = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_optimized_construction_comparison.py"
)
PYTHON312 = Path("/opt/homebrew/bin/python3.12")

EXPECTED_IDENTITIES = {
    SCHEMA: (
        9_702,
        "f927f2c0590a82495498230a7b6c159e63c8670162540fdd5283f86cccb35d54",
    ),
    PRODUCER: (
        33_466,
        "b7242039928552c1a38b23ac555d8998caa74bf4e9c7d68830cc53a8001acfd4",
    ),
    VERIFIER: (
        35_352,
        "552be2d82cda8d4b0c8c5131196e45b1904b249b2c648ddbce71b13bd11d565c",
    ),
    BUILD_CLI: (
        11_136,
        "0e4d228eeb4f53458226cc5e20d8dfd2249719e271021aa8fc299286f339aa0f",
    ),
    VERIFY_CLI: (
        11_633,
        "c3627ce6e22b493766c72f4f5eae1085f60240487303480f8271d00d5bd8c765",
    ),
}

FALSE_CLAIMS = {
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
    "global_optimized_vector_audit_complete",
    "human_review_complete",
    "kernel_artifacts_reexecuted",
    "lineage_complete",
    "logical_minimality_independently_verified",
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
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _compact(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def producer_module():
    return _load_module("_a23e_test_producer", PRODUCER)


@pytest.fixture(scope="module")
def verifier_module():
    return _load_module("_a23e_test_verifier", VERIFIER)


@pytest.fixture(scope="module")
def candidate(producer_module):
    return producer_module.build_pilot_optimized_construction_comparison(ROOT)


def _controlled_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONHASHSEED": "0",
    }


def _run_cli(path: Path, *args: object) -> subprocess.CompletedProcess[bytes]:
    assert PYTHON312.is_file()
    return subprocess.run(
        [
            os.fspath(PYTHON312),
            "-B",
            "-P",
            "-s",
            "-S",
            os.fspath(path),
            *(os.fspath(arg) for arg in args),
        ],
        cwd=ROOT,
        env=_controlled_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )


def _reroot_candidate(value: dict[str, object]) -> None:
    payload = {
        key: deepcopy(item)
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": (
            "peano-hydra-library-pilot-optimized-construction-comparison-"
            "root-preimage-v1"
        ),
        "payload": payload,
        "v": 1,
    }
    value["root_preimage"] = preimage
    value["root_sha256"] = _sha256(_compact(preimage))


def _reroot_receipt(value: dict[str, object]) -> None:
    payload = {
        key: deepcopy(item)
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": (
            "peano-hydra-library-pilot-optimized-construction-comparison-"
            "independent-verification-v1-root-preimage-v1"
        ),
        "payload": payload,
        "v": 1,
    }
    value["root_preimage"] = preimage
    value["root_sha256"] = _sha256(_compact(preimage))


def test_frozen_source_identities_and_modes() -> None:
    for path, (size, digest) in EXPECTED_IDENTITIES.items():
        raw = path.read_bytes()
        assert len(raw) == size
        assert _sha256(raw) == digest
    assert BUILD_CLI.stat().st_mode & 0o777 == 0o755
    assert VERIFY_CLI.stat().st_mode & 0o777 == 0o755
    for path in (SCHEMA, PRODUCER, VERIFIER):
        assert path.stat().st_mode & 0o777 == 0o644


def test_schema_is_strict_and_scoped(producer_module) -> None:
    schema = producer_module.optimized_construction_comparison_schema()
    identity = producer_module.optimized_construction_comparison_schema_identity()
    assert identity["artifact_sha256"] == EXPECTED_IDENTITIES[SCHEMA][1]
    assert schema["expected_theorem"]["name"] == "odd_add_odd"
    assert schema["expected_theorem"]["index"] == 256
    assert schema["expected_comparison"] == {
        "candidate_count": 4,
        "nondominated_candidate_ids_in_input_order": [
            "layered-closure",
            "cut-liveness",
        ],
        "representative_candidate_id": "cut-liveness",
    }
    assert set(schema["claim_boundary"]["false_claims"]) == FALSE_CLAIMS
    assert schema["controlled_runtime"]["minor"] == 12


def test_candidate_reconstructs_exact_four_candidate_universe(candidate) -> None:
    assert candidate["root_sha256"] == (
        "054a1f78ca16647f5a6b003570b20791295a4b5e9f7b127de170f4e6e1e7de03"
    )
    theorem = candidate["theorem"]
    assert [row["candidate_id"] for row in theorem["candidates"]] == [
        "retained-replay",
        "a2.2-direct-cut-rebuild",
        "layered-closure",
        "cut-liveness",
    ]
    assert [row["metrics"] for row in theorem["candidates"]] == [
        {
            "artifact_bytes": 14_977,
            "cut_nodes": 7,
            "proof_depth": 32,
            "proof_nodes": 302,
        },
        {
            "artifact_bytes": 13_640,
            "cut_nodes": 6,
            "proof_depth": 31,
            "proof_nodes": 274,
        },
        {
            "artifact_bytes": 12_709,
            "cut_nodes": 3,
            "proof_depth": 37,
            "proof_nodes": 269,
        },
        {
            "artifact_bytes": 11_958,
            "cut_nodes": 5,
            "proof_depth": 30,
            "proof_nodes": 240,
        },
    ]


def test_candidate_frontier_and_representative_are_exact(candidate) -> None:
    comparison = candidate["theorem"]["comparison"]
    assert comparison["nondominated_candidate_ids_in_input_order"] == [
        "layered-closure",
        "cut-liveness",
    ]
    assert comparison["representative_candidate_id"] == "cut-liveness"
    assert comparison["global_best_claim"] is False
    assert comparison["minimality_claim"] is False
    assert candidate["theorem"]["fixed_set_deltas_for_cut_liveness"] == [
        {
            "against_candidate_id": "retained-replay",
            "artifact_bytes_delta": -3019,
            "cut_nodes_delta": -2,
            "proof_depth_delta": -2,
            "proof_nodes_delta": -62,
        },
        {
            "against_candidate_id": "a2.2-direct-cut-rebuild",
            "artifact_bytes_delta": -1682,
            "cut_nodes_delta": -1,
            "proof_depth_delta": -1,
            "proof_nodes_delta": -34,
        },
        {
            "against_candidate_id": "layered-closure",
            "artifact_bytes_delta": -751,
            "cut_nodes_delta": 2,
            "proof_depth_delta": -7,
            "proof_nodes_delta": -29,
        },
    ]


def test_candidate_scoped_vector_and_false_claims(candidate) -> None:
    vector = candidate["theorem"]["construction_direct_vector"]
    assert vector == {
        "dependencies": ["mul_add", "add_comm"],
        "independently_reproduced": True,
        "lf_sha256": (
            "ca9176e5c542ed28309d630ef0cb06e69f4edad391a3505e498207b83ac830c4"
        ),
        "source_candidate_id": "cut-liveness",
        "theorem_scoped_audit_complete": True,
    }
    assert candidate["theorem_scoped_construction_vector_audit_complete"] is True
    assert candidate["optimized_vector_independently_audited"] is False
    assert candidate["optimized_best_known"] is False
    for name in FALSE_CLAIMS:
        assert candidate[name] is False


def test_candidate_canonical_roundtrip_and_deep_validation(
    producer_module, candidate
) -> None:
    raw = producer_module.canonical_document_bytes(candidate)
    assert len(raw) == 14_953
    assert raw.endswith(b"\n")
    producer_module.validate_pilot_optimized_construction_comparison(
        candidate, repository_root=ROOT
    )


def test_independent_verifier_recomputes_comparison(
    producer_module, verifier_module, candidate
) -> None:
    candidate_raw = producer_module.canonical_document_bytes(candidate)
    receipt = verifier_module.verify_pilot_optimized_construction_comparison(
        candidate,
        candidate_raw=candidate_raw,
        repository_root=ROOT,
    )
    assert receipt["root_sha256"] == (
        "d62c417f1eb5cf8597c7ee8492e2b3610fdfd834c0f9ef474f110d2f9d963c8c"
    )
    assert receipt["comparison_independently_recomputed"] is True
    assert receipt["candidate_structure_independently_verified"] is True
    assert receipt["theorem_scoped_construction_vector_audit_complete"] is True
    assert receipt["optimized_vector_independently_audited"] is False
    assert receipt["verifier_boundary"] == {
        "imports_producer": False,
        "imports_tactics_or_kernel": False,
        "reexecutes_kernel_artifacts": False,
        "shared_inputs": (
            "exact retained A2.3a/A2.3d candidate-and-verifier bytes"
        ),
    }
    verifier_module.validate_comparison_verification_receipt(
        receipt,
        candidate=candidate,
        candidate_raw=candidate_raw,
        repository_root=ROOT,
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("optimized_best_known",), True),
        (("optimized_vector_independently_audited",), True),
        (("theorem", "construction_direct_vector", "dependencies"), ["mul_add"]),
        (("theorem", "candidates", 3, "metrics", "proof_nodes"), 239),
        (
            (
                "theorem",
                "comparison",
                "nondominated_candidate_ids_in_input_order",
            ),
            ["cut-liveness"],
        ),
        (("theorem", "comparison", "representative_candidate_id"), "layered-closure"),
    ],
)
def test_fully_rerooted_candidate_forgery_is_rejected(
    producer_module, verifier_module, candidate, path, value
) -> None:
    forged = deepcopy(candidate)
    cursor = forged
    for component in path[:-1]:
        cursor = cursor[component]
    cursor[path[-1]] = value
    _reroot_candidate(forged)
    with pytest.raises(Exception, match="exact reconstruction|differs"):
        producer_module.validate_pilot_optimized_construction_comparison(
            forged, repository_root=ROOT
        )
    with pytest.raises(Exception, match="exact reconstruction|differs"):
        verifier_module.verify_pilot_optimized_construction_comparison(
            forged, repository_root=ROOT
        )


def test_fully_rerooted_verifier_overclaim_is_rejected(
    producer_module, verifier_module, candidate
) -> None:
    raw = producer_module.canonical_document_bytes(candidate)
    receipt = verifier_module.verify_pilot_optimized_construction_comparison(
        candidate, candidate_raw=raw, repository_root=ROOT
    )
    forged = deepcopy(receipt)
    forged["best_known"] = True
    _reroot_receipt(forged)
    with pytest.raises(Exception, match="exact reconstruction|differs"):
        verifier_module.validate_comparison_verification_receipt(
            forged,
            candidate=candidate,
            candidate_raw=raw,
            repository_root=ROOT,
        )


def test_componentwise_frontier_rejects_duplicate_identity(producer_module) -> None:
    rows = (
        {
            "artifact_sha256": "a" * 64,
            "candidate_id": "same",
            "candidate_kind_order": 0,
            "metrics": {
                "artifact_bytes": 10,
                "proof_nodes": 10,
                "proof_depth": 10,
                "cut_nodes": 1,
            },
        },
        {
            "artifact_sha256": "b" * 64,
            "candidate_id": "same",
            "candidate_kind_order": 1,
            "metrics": {
                "artifact_bytes": 9,
                "proof_nodes": 9,
                "proof_depth": 9,
                "cut_nodes": 1,
            },
        },
    )
    with pytest.raises(Exception, match="unique"):
        producer_module.componentwise_nondominated(rows)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":1.0}',
        b'{"x":NaN}',
        b'\xff',
        b'[]',
    ],
)
def test_strict_loader_rejects_noncanonical_json(
    producer_module, tmp_path: Path, raw: bytes
) -> None:
    path = tmp_path / "candidate.json"
    path.write_bytes(raw)
    with pytest.raises(Exception):
        producer_module.load_pilot_optimized_construction_comparison(
            path, repository_root=ROOT
        )


def test_loader_rejects_symlink(producer_module, candidate, tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_bytes(producer_module.canonical_document_bytes(candidate))
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(Exception, match="non-symlink regular file"):
        producer_module.load_pilot_optimized_construction_comparison(
            link, repository_root=ROOT
        )


def test_verifier_source_has_independent_stdlib_boundary() -> None:
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.startswith("training") for name in imports)
    assert not any(name.startswith("peano_lab") for name in imports)
    source = VERIFIER.read_text(encoding="utf-8")
    assert "compile_candidate_body" not in source
    assert "library_pilot_optimized_construction_comparison import" not in source


def test_cli_pins_match_live_sources() -> None:
    build_source = BUILD_CLI.read_text(encoding="utf-8")
    verify_source = VERIFY_CLI.read_text(encoding="utf-8")
    assert "PRODUCER_BYTES = 33_466" in build_source
    assert "VERIFIER_BYTES = 35_352" in verify_source
    assert EXPECTED_IDENTITIES[PRODUCER][1] in build_source
    assert EXPECTED_IDENTITIES[VERIFIER][1] in verify_source


def test_build_cli_default_is_source_only_and_no_write() -> None:
    result = _run_cli(BUILD_CLI)
    assert result.returncode == 0, result.stderr.decode()
    value = json.loads(result.stdout)
    assert value["default_action"] == "describe-only-no-write"
    assert value["campaign_executed"] is False
    assert value["result_retained"] is False


def test_build_and_verify_cli_roundtrip_create_only(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    receipt_path = tmp_path / "receipt.json"
    built = _run_cli(
        BUILD_CLI,
        "--build",
        "--confirm",
        "PEANO-HYDRA-A23E-FIXED-COMPARISON",
        "--output",
        candidate_path,
    )
    assert built.returncode == 0, built.stderr.decode()
    assert built.stdout == b""
    assert len(candidate_path.read_bytes()) == 14_953
    verified = _run_cli(
        VERIFY_CLI,
        "--verify",
        candidate_path,
        "--confirm",
        "PEANO-HYDRA-A23E-VERIFY-COMPARISON",
        "--output",
        receipt_path,
    )
    assert verified.returncode == 0, verified.stderr.decode()
    assert verified.stdout == b""
    assert len(receipt_path.read_bytes()) == 11_247
    overwrite = _run_cli(
        BUILD_CLI,
        "--build",
        "--confirm",
        "PEANO-HYDRA-A23E-FIXED-COMPARISON",
        "--output",
        candidate_path,
    )
    assert overwrite.returncode == 2
    assert candidate_path.read_bytes() != b""


def test_cli_rejects_stray_confirmation_and_injection_env() -> None:
    stray = _run_cli(BUILD_CLI, "--confirm", "anything")
    assert stray.returncode == 2
    env = _controlled_env()
    env["PYTHONPATH"] = ""
    result = subprocess.run(
        [
            os.fspath(PYTHON312),
            "-B",
            "-P",
            "-s",
            "-S",
            os.fspath(BUILD_CLI),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    assert result.returncode == 2
    assert b"must be absent" in result.stderr


def test_no_retained_a23e_result_exists() -> None:
    assert not list(
        (ROOT / "artifacts/peano-hydra").glob(
            "l0-pilot-optimized-construction-comparison-*.json"
        )
    )
    assert not list(
        (ROOT / "artifacts/peano-hydra").glob(
            "a23e-wmi-optimized-construction-comparison-*"
        )
    )
