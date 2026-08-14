"""Acceptance gate for the retained Hydra A2.3e fixed-set comparison.

The retained result is deliberately small and tactic-free: one canonical
comparison candidate and one separately authored stdlib verifier receipt.
This gate pins those bytes, reproduces both documents, and preserves the
strict one-root/four-candidate claim boundary.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-hydra"
BUNDLE_ROOT = ARTIFACT_ROOT / "a23e-local-fixed-comparison-7e0c24e"
RESULT_ROOT = BUNDLE_ROOT / "results"
CANDIDATE_PATH = (
    RESULT_ROOT
    / "l0-pilot-optimized-construction-comparison-candidate-v1.json"
)
VERIFICATION_PATH = (
    RESULT_ROOT
    / (
        "l0-pilot-optimized-construction-comparison-"
        "independent-verification-v1.json"
    )
)
PRODUCER_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_optimized_construction_comparison.py"
)
VERIFIER_PATH = (
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
PYTHON312 = (
    Path(sys.executable)
    if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12)
    else Path("/opt/homebrew/bin/python3.12")
)

CANDIDATE_BYTES = 14_953
CANDIDATE_SHA256 = (
    "213107ea9d940f3cbd998e3deb22bdae3e6a1a9aaa4ab945bfbea9899e25cd08"
)
CANDIDATE_ROOT = (
    "054a1f78ca16647f5a6b003570b20791295a4b5e9f7b127de170f4e6e1e7de03"
)
VERIFICATION_BYTES = 11_247
VERIFICATION_SHA256 = (
    "1c1075c469550c5aef4e4500819a548ade66ca5166a811bc0dc391c6fecd23bb"
)
VERIFICATION_ROOT = (
    "d62c417f1eb5cf8597c7ee8492e2b3610fdfd834c0f9ef474f110d2f9d963c8c"
)
INVENTORY_SHA256 = (
    "b70e6c34c7954551cd21a812ef12a21668718261a31e8c0f255487eff54b37ad"
)

FILE_PINS = {
    (
        "results/"
        "l0-pilot-optimized-construction-comparison-candidate-v1.json"
    ): (CANDIDATE_BYTES, CANDIDATE_SHA256, CANDIDATE_ROOT),
    (
        "results/l0-pilot-optimized-construction-comparison-"
        "independent-verification-v1.json"
    ): (VERIFICATION_BYTES, VERIFICATION_SHA256, VERIFICATION_ROOT),
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
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result, f"duplicate JSON key: {key!r}"
        result[key] = value
    return result


def _reject_float(value: str) -> object:
    raise AssertionError(f"floating-point JSON number is forbidden: {value}")


def _load_json(path: Path) -> tuple[dict[str, object], bytes]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_strict_object,
        parse_float=_reject_float,
        parse_constant=_reject_float,
    )
    assert type(value) is dict
    assert raw == _compact(value) + b"\n"
    return value, raw


def _assert_root(value: dict[str, object], expected: str) -> None:
    payload = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = value["root_preimage"]
    assert type(preimage) is dict
    assert preimage["payload"] == payload
    assert preimage["v"] == value["v"]
    assert value["root_sha256"] == expected == _sha256(_compact(preimage))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def producer_module():
    return _load_module("_a23e_result_producer", PRODUCER_PATH)


@pytest.fixture(scope="module")
def verifier_module():
    return _load_module("_a23e_result_verifier", VERIFIER_PATH)


def _controlled_run(path: Path, *args: object) -> subprocess.CompletedProcess[bytes]:
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
        env={
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONHASHSEED": "0",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )


def test_retained_bundle_is_closed_canonical_and_exact() -> None:
    assert BUNDLE_ROOT.is_dir() and not BUNDLE_ROOT.is_symlink()
    assert RESULT_ROOT.is_dir() and not RESULT_ROOT.is_symlink()
    assert stat.S_IMODE(BUNDLE_ROOT.stat().st_mode) == 0o755
    assert stat.S_IMODE(RESULT_ROOT.stat().st_mode) == 0o755

    nodes = sorted(BUNDLE_ROOT.rglob("*"))
    files = [path for path in nodes if path.is_file()]
    directories = [path for path in nodes if path.is_dir()]
    assert directories == [RESULT_ROOT]
    assert all(not path.is_symlink() for path in nodes)
    assert {
        path.relative_to(BUNDLE_ROOT).as_posix()
        for path in files
    } == set(FILE_PINS)

    inventory = bytearray()
    for relative in sorted(FILE_PINS):
        path = BUNDLE_ROOT / relative
        raw = path.read_bytes()
        size, digest, root = FILE_PINS[relative]
        assert len(raw) == size
        assert _sha256(raw) == digest
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
        value, canonical = _load_json(path)
        assert canonical == raw
        _assert_root(value, root)
        inventory.extend(f"{digest}\t{size}\t{relative}\n".encode("utf-8"))
    assert sum(size for size, _digest, _root in FILE_PINS.values()) == 26_200
    assert _sha256(bytes(inventory)) == INVENTORY_SHA256

    assert list(
        ARTIFACT_ROOT.glob(
            "l0-pilot-optimized-construction-comparison-*.json"
        )
    ) == []
    assert sorted(
        ARTIFACT_ROOT.rglob(
            "l0-pilot-optimized-construction-comparison-*.json"
        )
    ) == [CANDIDATE_PATH, VERIFICATION_PATH]


def test_retained_result_has_exact_fixed_scope_and_false_claims() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    receipt, _receipt_raw = _load_json(VERIFICATION_PATH)

    assert candidate["status"] == (
        "candidate-only-fixed-one-root-four-candidate-comparison"
    )
    assert candidate["aggregate"] == {
        "candidate_count": 4,
        "construction_direct_dependency_count": 2,
        "nondominated_candidate_count": 2,
        "pilot_theorem_count": 1,
    }
    theorem = candidate["theorem"]
    assert theorem["name"] == "odd_add_odd"
    assert theorem["index"] == 256
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
    comparison = theorem["comparison"]
    assert comparison["nondominated_candidate_ids_in_input_order"] == [
        "layered-closure",
        "cut-liveness",
    ]
    assert comparison["representative_candidate_id"] == "cut-liveness"
    assert comparison["global_best_claim"] is False
    assert comparison["minimality_claim"] is False
    vector = theorem["construction_direct_vector"]
    assert vector["dependencies"] == ["mul_add", "add_comm"]
    assert vector["independently_reproduced"] is True
    assert vector["theorem_scoped_audit_complete"] is True
    for field in FALSE_CLAIMS:
        assert candidate[field] is False

    assert receipt["status"] == "passed"
    assert receipt["candidate"] == {
        "artifact_bytes": CANDIDATE_BYTES,
        "artifact_sha256": CANDIDATE_SHA256,
        "root_sha256": CANDIDATE_ROOT,
        "theorem_record_sha256": theorem["record_sha256"],
    }
    assert receipt["candidate_structure_independently_verified"] is True
    assert receipt["comparison_independently_recomputed"] is True
    assert receipt["construction_direct_vector_independently_reproduced"] is True
    assert receipt["execution_receipt_bound"] is False
    assert receipt["producer_imported_by_verifier"] is False
    assert receipt["producer_semantics_independently_verified"] is False
    assert receipt["verifier_boundary"] == {
        "imports_producer": False,
        "imports_tactics_or_kernel": False,
        "reexecutes_kernel_artifacts": False,
        "shared_inputs": (
            "exact retained A2.3a/A2.3d candidate-and-verifier bytes"
        ),
    }
    for field in FALSE_CLAIMS:
        assert receipt[field] is False
    assert _sha256(candidate_raw) == CANDIDATE_SHA256


def test_frozen_modules_reproduce_retained_bytes(
    producer_module, verifier_module
) -> None:
    retained_candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    retained_receipt, receipt_raw = _load_json(VERIFICATION_PATH)

    candidate = producer_module.build_pilot_optimized_construction_comparison(ROOT)
    producer_module.validate_pilot_optimized_construction_comparison(
        candidate, repository_root=ROOT
    )
    rebuilt_candidate_raw = producer_module.canonical_document_bytes(candidate)
    assert candidate == retained_candidate
    assert rebuilt_candidate_raw == candidate_raw

    receipt = verifier_module.verify_pilot_optimized_construction_comparison(
        candidate,
        candidate_raw=rebuilt_candidate_raw,
        repository_root=ROOT,
    )
    verifier_module.validate_comparison_verification_receipt(
        receipt,
        candidate=candidate,
        candidate_raw=rebuilt_candidate_raw,
        repository_root=ROOT,
    )
    rebuilt_receipt_raw = verifier_module.canonical_verification_receipt_bytes(
        receipt
    )
    assert receipt == retained_receipt
    assert rebuilt_receipt_raw == receipt_raw


def test_controlled_cli_replays_are_byte_identical(
    tmp_path: Path,
) -> None:
    candidates = [tmp_path / f"candidate-{seed}.json" for seed in (0, 1)]
    receipts = [tmp_path / f"receipt-{seed}.json" for seed in (0, 1)]
    for candidate in candidates:
        run = _controlled_run(
            BUILD_CLI,
            "--build",
            "--confirm",
            "PEANO-HYDRA-A23E-FIXED-COMPARISON",
            "--repository-root",
            ROOT,
            "--output",
            candidate,
        )
        assert run.returncode == 0, run.stderr.decode("utf-8", "replace")
        assert run.stdout == b""
        assert run.stderr == b""
        assert candidate.read_bytes() == CANDIDATE_PATH.read_bytes()

    for candidate, receipt in zip(candidates, receipts, strict=True):
        run = _controlled_run(
            VERIFY_CLI,
            "--verify",
            candidate,
            "--confirm",
            "PEANO-HYDRA-A23E-VERIFY-COMPARISON",
            "--repository-root",
            ROOT,
            "--output",
            receipt,
        )
        assert run.returncode == 0, run.stderr.decode("utf-8", "replace")
        assert run.stdout == b""
        assert run.stderr == b""
        assert receipt.read_bytes() == VERIFICATION_PATH.read_bytes()

    assert candidates[0].read_bytes() == candidates[1].read_bytes()
    assert receipts[0].read_bytes() == receipts[1].read_bytes()
