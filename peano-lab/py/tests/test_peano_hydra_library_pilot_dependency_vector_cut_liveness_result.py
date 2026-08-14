"""Acceptance gate for the retained Hydra A2.3d Cut-liveness result.

This suite does not rerun the producer campaign.  It pins the closed retained
bundle, checks the one-root proof-producing transformation and narrow claim
boundary, re-executes the independent verifier, and reconstructs the WMI
source, process, scheduler, and normalized-output bindings.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Iterable

import pytest


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-hydra"
EVIDENCE_ROOT = ARTIFACT_ROOT / "a23d-wmi-cut-liveness-220246"
RESULT_ROOT = EVIDENCE_ROOT / "results"
CANDIDATE_PATH = (
    RESULT_ROOT / "l0-pilot-dependency-vector-cut-liveness-candidate-v1.json"
)
VERIFICATION_PATH = (
    RESULT_ROOT
    / "l0-pilot-dependency-vector-cut-liveness-independent-verification-v1.json"
)
SOURCE_STATE_PATH = EVIDENCE_ROOT / "inputs" / "cut-liveness-source-state.json"
GIT_RECEIPT_PATH = (
    EVIDENCE_ROOT / "inputs" / "cut-liveness-git-verification-receipt.json"
)
INFRASTRUCTURE_PATH = (
    EVIDENCE_ROOT / "inputs" / "wmi-infrastructure-manifest.json"
)
EXECUTION_PATH = EVIDENCE_ROOT / "runs" / "220246" / "execution-receipt.json"
COLLECTION_PATH = EVIDENCE_ROOT / "collections" / "job-220246.json"
VERIFIER_CLI = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
)

JOB_ID = "220246"
COMMIT = "25228180c956456145eba64601e829103731e903"
TREE = "528ca1d3c0e697048479acdd690b54a9d13fa469"
SNAPSHOT = "52480a731e184565a0f6627d62d6b034d9c4f2a66fa5e508335def68998c9a7d"
INVENTORY_SHA256 = (
    "db3914f58b1ab4019fbe447c6454a261ec9a32e74b7a25772e0483bfbad2ac81"
)
SOURCE_STATE_SEMANTIC_SHA256 = (
    "72f2219542c2d43d05597e1381f89cfda292399267f905129cf16f7346938e2f"
)
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
CANDIDATE_SHA256 = (
    "a9077a7b272930477b93c48baef8b14fe0e443627c52177efa863ed0c18375e0"
)
CANDIDATE_ROOT = (
    "fd0497da5ea0c12ecb14fa168637ea6d54006ce9b9295010e879df37f5dcd835"
)
VERIFICATION_SHA256 = (
    "8f6531d3a0544a6d308ebd0abf7e41ed2436984758e76e66797ff1023e0a2821"
)
VERIFICATION_ROOT = (
    "b3c253674f488eeed1e5a14e4be6632b0fe6ed946cf611ee0b3fde66f79acad7"
)
OUTPUT_ARTIFACT_SHA256 = (
    "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22"
)
OUTPUT_PROOF_SHA256 = (
    "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4"
)

# Paths are relative to EVIDENCE_ROOT.  The optional third value is the
# compact-JSON digest of the document's root preimage.
FILE_PINS = {
    "collections/job-220246.json": (
        8_942,
        "1f8907520cc2e7508a841719f43111538245a6c640de042b422213da0dc5de3a",
        "fe9d57683008f8b61768a133d8ba453d2819e337c31fd1afe4ee397a7b880fb1",
    ),
    "deposit.tsv": (
        438,
        "babb2d65872be482980982ad075096f1aa00c6f331d727e4095811f36343ada5",
        None,
    ),
    "inputs/.peano-source-provenance.tsv": (
        68,
        "85d75a9c229d40a0597543513e78600d6c15986a0392b164d16446988f6eb934",
        None,
    ),
    "inputs/cut-liveness-git-verification-receipt.json": (
        35_158,
        "3a207d46b9142ca951705cac066221e1d2b6b54005d542b9275b4585360e6876",
        "3194cbf1ff2041fe448ac4c3781356c8e28d79acd43c22dbd4b5c597e2beb7da",
    ),
    "inputs/cut-liveness-source-state.json": (
        3_372,
        "1e0315e75364721408799db01db3b7f39896d84c26b83c50bcd103994533a421",
        "7db294f75a67cd6252c2831dd8ae11ba5ba0d185a736328031e0724602b38363",
    ),
    "inputs/wmi-infrastructure-manifest.json": (
        5_790,
        "afcf38c94167814123950b47aa38cb97d8564c89adf2ecc976a320a7525a585f",
        "09a05076bc8e57174790575d59e41a0b4c0090602f8305465e84339b172fc01e",
    ),
    "logs/peano-hydra-a23d-cut-liveness-220246.err": (
        0,
        EMPTY_SHA256,
        None,
    ),
    "logs/peano-hydra-a23d-cut-liveness-220246.out": (
        436,
        "80766110261d32502c4bbde4e413fb4ad6e8921bb82d102b4290b4bb2637ff17",
        None,
    ),
    "results/l0-pilot-dependency-vector-cut-liveness-candidate-v1.json": (
        74_579,
        CANDIDATE_SHA256,
        CANDIDATE_ROOT,
    ),
    (
        "results/l0-pilot-dependency-vector-cut-liveness-"
        "independent-verification-v1.json"
    ): (12_737, VERIFICATION_SHA256, VERIFICATION_ROOT),
    "runs/220246/execution-receipt.json": (
        19_383,
        "46922d976e00925a62bef9792bdeaa50c6e6800d9d034c132fae6b952be35bc7",
        "28e660ea1b9f455c2cbb9022b045fc9ef57922c0bf007d413de2ca106d31ead1",
    ),
    "runs/220246/independent-verifier.stderr.log": (0, EMPTY_SHA256, None),
    "runs/220246/independent-verifier.stdout.log": (
        12_737,
        VERIFICATION_SHA256,
        None,
    ),
    "runs/220246/producer-0.stderr.log": (0, EMPTY_SHA256, None),
    "runs/220246/producer-1.stderr.log": (0, EMPTY_SHA256, None),
    "sacct.psv": (
        38,
        "837de6c66a82ed5396480f190d6a873b9881721acd24a28fbcf5734d2276fe17",
        None,
    ),
    "submission.tsv": (
        553,
        "64d9fde87f4e0b299d998110b0f4f375edc1d0dab1f81021f6f3b2da2f4ff80b",
        None,
    ),
}

EVIDENCE_DIRECTORIES = {
    ".",
    "collections",
    "inputs",
    "logs",
    "results",
    "runs",
    "runs/220246",
}
AUTHORITY_FALSE_FIELDS = {
    "a2_complete",
    "authority_granted",
    "best_known",
    "bounded_three_root_vector_audit_complete",
    "dependency_minimality_established",
    "dependency_necessity_established",
    "dependency_necessity_independently_verified",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_complete",
    "freeze_ready",
    "global_comparison_complete",
    "global_optimized_vector_audit_complete",
    "human_review_complete",
    "lineage_complete",
    "logical_minimality_independently_verified",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "proof_authority",
    "producer_git_verified",
    "producer_semantics_independently_verified",
    "public_graph_applied",
    "publication_applied",
    "publication_authority",
    "publication_ready",
    "publication_union_complete",
    "publication_union_verified",
    "research_evaluation_eligible",
    "retrieval_eligible",
    "review_complete",
    "route_rejections_independently_verified",
    "theorem_admission_authority",
    "training_eligible",
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _compact_sha256(value: object) -> str:
    return _sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        assert key not in value, f"duplicate JSON key: {key!r}"
        value[key] = item
    return value


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
    canonical = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value, raw


def _assert_root(value: dict[str, object], expected: str) -> None:
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = value["root_preimage"]
    assert type(preimage) is dict
    assert preimage["payload"] == body
    assert preimage["v"] == value["v"]
    assert value["root_sha256"] == expected == _compact_sha256(preimage)


def _walk(value: object) -> Iterable[tuple[str, object]]:
    if type(value) is dict:
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif type(value) is list:
        for item in value:
            yield from _walk(item)


def _assert_no_authority(value: object) -> None:
    for key, item in _walk(value):
        if key in AUTHORITY_FALSE_FIELDS:
            assert item is False, f"forbidden authority field {key!r} is not false"


def _record(path: Path, retained_name: str | None = None) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.name if retained_name is None else retained_name,
        "sha256": _sha256(raw),
    }


def test_exact_closed_inventory_has_no_duplicate_snapshot_or_symlink() -> None:
    actual_files = {
        path.relative_to(EVIDENCE_ROOT).as_posix(): path
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_file()
    }
    actual_directories = {"."} | {
        path.relative_to(EVIDENCE_ROOT).as_posix()
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_dir()
    }
    assert set(actual_files) == set(FILE_PINS)
    assert actual_directories == EVIDENCE_DIRECTORIES
    assert len(actual_files) == 17
    assert sum(path.stat().st_size for path in actual_files.values()) == 174_231
    assert not any(path.is_symlink() for path in EVIDENCE_ROOT.rglob("*"))
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o644
        for path in actual_files.values()
    )
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o755
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_dir()
    )
    assert stat.S_IMODE(EVIDENCE_ROOT.stat().st_mode) == 0o755

    inventory = b"".join(
        (
            f"{_sha256(actual_files[relative].read_bytes())}\t"
            f"{actual_files[relative].stat().st_size}\t{relative}\n"
        ).encode("ascii")
        for relative in sorted(actual_files)
    )
    assert _sha256(inventory) == INVENTORY_SHA256

    for relative, (expected_bytes, expected_sha256, expected_root) in FILE_PINS.items():
        path = actual_files[relative]
        raw = path.read_bytes()
        assert len(raw) == expected_bytes, relative
        assert _sha256(raw) == expected_sha256, relative
        if expected_root is not None:
            document, canonical_raw = _load_json(path)
            assert canonical_raw == raw
            _assert_root(document, expected_root)

    assert list(
        ARTIFACT_ROOT.glob("l0-pilot-dependency-vector-cut-liveness-*.json")
    ) == []
    assert list(ARTIFACT_ROOT.rglob(CANDIDATE_PATH.name)) == [CANDIDATE_PATH]
    assert list(ARTIFACT_ROOT.rglob(VERIFICATION_PATH.name)) == [VERIFICATION_PATH]
    assert not (EVIDENCE_ROOT / "source").exists()
    assert not any(path.name == SNAPSHOT for path in EVIDENCE_ROOT.rglob("*"))
    assert not any(
        path.name.endswith((".tar", ".tar.gz", ".tgz", ".zip"))
        for path in EVIDENCE_ROOT.rglob("*")
    )
    assert not any(
        token in path.name.lower()
        for path in EVIDENCE_ROOT.rglob("*")
        for token in ("ledger", "pointer", "run-2")
    )
    assert not any(path.name.startswith("producer-") and path.suffix == ".stdout.log"
                   for path in EVIDENCE_ROOT.rglob("*"))


def test_result_binds_one_root_cut_liveness_without_broad_claims() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)

    assert (
        candidate["format"],
        candidate["id"],
        candidate["v"],
        candidate["status"],
        candidate["logic_mode"],
        candidate["theorem_count"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-cut-liveness-v1",
        "peano-hydra-l0-pilot-dependency-vector-cut-liveness-candidate-v1",
        1,
        "candidate-only-bounded-one-root-proof-producing-cut-liveness-normalization",
        "intuitionistic",
        1,
    )
    assert len(candidate_raw) == 74_579
    assert _sha256(candidate_raw) == CANDIDATE_SHA256
    assert candidate["root_sha256"] == CANDIDATE_ROOT
    assert candidate["bounded_one_root_protocol_executed"] is True
    assert candidate["aggregate"] == {
        "candidate_artifact_count": 1,
        "deleted_vacuous_root_cut_count": 2,
        "derived_direct_dependency_count": 2,
        "initial_direct_dependency_count": 4,
        "pilot_theorem_count": 1,
        "retained_used_root_cut_count": 2,
    }

    theorem = candidate["theorem"]
    assert (theorem["index"], theorem["name"]) == (256, "odd_add_odd")
    assert theorem["bounded_one_root_cut_liveness_complete"] is True
    assert theorem["proof_producing_cut_liveness_normalization_complete"] is True
    assert theorem["initial_direct_vector"] == {
        "count": 4,
        "dependencies": ["mul_add", "add_succ_left", "add_assoc", "add_comm"],
        "lf_bytes": 41,
        "lf_sha256": (
            "9bb59dbdeb07badb9f8ca9d0cc951b71f38dbf7c3edcb1b189d53efcba1708cc"
        ),
    }
    assert theorem["derived_direct_vector"] == {
        "count": 2,
        "dependencies": ["mul_add", "add_comm"],
        "lf_bytes": 17,
        "lf_sha256": (
            "ca9176e5c542ed28309d630ef0cb06e69f4edad391a3505e498207b83ac830c4"
        ),
    }
    closure = theorem["closure_context"]
    expected_closure = [
        "zero_add",
        "add_succ_left",
        "add_comm",
        "add_assoc",
        "mul_add",
    ]
    assert closure["unchanged"] is True
    assert closure["dropped_direct_dependencies_remaining_reachable"] == [
        "add_succ_left",
        "add_assoc",
    ]
    assert closure["initial_vector_closure"]["dependencies"] == expected_closure
    assert closure["derived_vector_closure"]["dependencies"] == expected_closure
    assert closure["derived_vector_closure"]["lf_sha256"] == (
        "a4abec5d9eb955ed95f6eea761c96c3de0166b3df3c64fe8e898d8766ed5c5f2"
    )

    steps = theorem["normalization_steps_inner_first"]
    assert [
        (row["dependency"], row["bound_hypothesis_use_count"], row["outcome"])
        for row in steps
    ] == [
        ("add_comm", 2, "retained-used"),
        ("add_assoc", 0, "deleted-vacuous"),
        ("add_succ_left", 0, "deleted-vacuous"),
        ("mul_add", 1, "retained-used"),
    ]
    assert all(row["intermediate_kernel_checked"] is True for row in steps)
    assert [row["processing_index"] for row in steps] == [0, 1, 2, 3]
    artifact = theorem["candidate_artifact"]
    artifact_raw = base64.b64decode(artifact["artifact_base64"], validate=True)
    assert (len(artifact_raw), _sha256(artifact_raw)) == (
        11_958,
        OUTPUT_ARTIFACT_SHA256,
    )
    assert artifact["artifact_sha256"] == OUTPUT_ARTIFACT_SHA256
    assert artifact["proof_term_sha256"] == OUTPUT_PROOF_SHA256
    assert artifact["formula_sha256"] == (
        "4d2aa6b4e387657e562641830dab2953890b5493d6e6858b6c36d73b06786c31"
    )
    assert artifact["fuel"] == 1_936
    assert artifact["tree_metrics"] == {
        "cut_nodes": 5,
        "proof_depth": 30,
        "proof_nodes": 240,
    }
    assert artifact["empty_context_kernel_checked"] is True
    assert artifact["canonical_roundtrip_checked"] is True
    assert theorem["post_transform_idempotence"] == {
        "checked": True,
        "proof_term_sha256": OUTPUT_PROOF_SHA256,
        "retained_dependencies": ["mul_add", "add_comm"],
        "second_pass_outcomes_inner_first": [
            {"dependency": "add_comm", "outcome": "retained-used"},
            {"dependency": "mul_add", "outcome": "retained-used"},
        ],
    }
    theorem_body = {
        key: item for key, item in theorem.items() if key != "record_sha256"
    }
    assert theorem["record_sha256"] == _compact_sha256(theorem_body)
    assert candidate["theorem_record_root_sha256"] == theorem["record_sha256"]

    assert (
        verification["format"],
        verification["id"],
        verification["v"],
        verification["status"],
        verification["logic_mode"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-cut-liveness-"
        "independent-verification-v1",
        "independent-peano-hydra-l0-pilot-dependency-vector-cut-liveness-"
        "verification-v1",
        1,
        "passed",
        "intuitionistic",
    )
    assert len(verification_raw) == 12_737
    assert _sha256(verification_raw) == VERIFICATION_SHA256
    assert verification["root_sha256"] == VERIFICATION_ROOT
    assert verification["candidate_artifact_sha256"] == CANDIDATE_SHA256
    assert verification["candidate_root_sha256"] == CANDIDATE_ROOT
    for field in (
        "derived_artifact_byte_identical",
        "derived_direct_vector_independently_reproduced",
        "encoded_tagged_array_transform_independently_executed",
        "input_and_dependency_artifacts_independently_authenticated",
        "input_and_output_kernel_checked",
        "proof_liveness_transform_idempotent",
    ):
        assert verification[field] is True
    assert verification["execution_receipt_bound"] is False
    assert verification["producer_imported_by_verifier"] is False
    assert verification["producer_semantics_independently_verified"] is False

    verified = verification["theorem"]
    assert verified["index"] == 256
    assert verified["name"] == "odd_add_odd"
    assert verified["input_direct_cut_spine"] == [
        "mul_add",
        "add_succ_left",
        "add_assoc",
        "add_comm",
    ]
    assert verified["derived_direct_dependencies"] == ["mul_add", "add_comm"]
    assert verified["candidate_artifact_sha256"] == OUTPUT_ARTIFACT_SHA256
    assert verified["output_proof_term_sha256"] == OUTPUT_PROOF_SHA256
    assert verified["output_fuel"] == 1_936
    assert verified["output_metrics"] == {
        "cut_nodes": 5,
        "proof_depth": 30,
        "proof_nodes": 240,
    }
    verified_body = {
        key: item for key, item in verified.items() if key != "record_sha256"
    }
    assert verified["record_sha256"] == _compact_sha256(verified_body)

    kernel_sources = verification["kernel_sources"]
    assert kernel_sources["count"] == 8
    assert kernel_sources["root_sha256"] == _compact_sha256(
        kernel_sources["preimage"]
    )
    for row in kernel_sources["preimage"]["records"]:
        raw = (ROOT / "peano-lab" / "py" / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])
    for row in candidate["implementation"]["sources"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])

    _assert_no_authority(candidate)
    _assert_no_authority(verification)


def test_independent_verifier_replays_byte_identically(tmp_path: Path) -> None:
    python = (
        sys.executable
        if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12)
        else shutil.which("python3.12")
    )
    if python is None:
        pytest.skip("controlled verifier requires CPython 3.12")
    environment = {
        "HOME": str(tmp_path),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "31337",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23d-disabled-pycache",
        "TZ": "UTC",
    }
    completed = subprocess.run(
        [
            python,
            "-B",
            "-P",
            "-s",
            "-S",
            str(VERIFIER_CLI),
            "--verify",
            str(CANDIDATE_PATH),
            "--repository-root",
            str(ROOT),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", errors="replace"
    )
    assert completed.stderr == b""
    assert completed.stdout == VERIFICATION_PATH.read_bytes()
    replayed = json.loads(completed.stdout)
    assert replayed["derived_direct_vector_independently_reproduced"] is True
    assert replayed["input_and_output_kernel_checked"] is True
    assert replayed["execution_receipt_bound"] is False
    assert replayed["optimized_vector_independently_audited"] is False


def test_source_and_wmi_receipts_cross_bind_normalized_outputs() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)
    git_receipt, git_receipt_raw = _load_json(GIT_RECEIPT_PATH)
    infrastructure, infrastructure_raw = _load_json(INFRASTRUCTURE_PATH)
    execution, execution_raw = _load_json(EXECUTION_PATH)
    collection, _ = _load_json(COLLECTION_PATH)

    assert (source_state["commit_sha1"], source_state["tree_sha1"]) == (
        COMMIT,
        TREE,
    )
    assert source_state["git_verified"] is False
    assert _compact_sha256(source_state) == SOURCE_STATE_SEMANTIC_SHA256
    for row in source_state["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])

    provenance = (
        EVIDENCE_ROOT / "inputs" / ".peano-source-provenance.tsv"
    ).read_text(encoding="ascii").removesuffix("\n").split("\t")
    assert provenance == [COMMIT, "false", "2026-08-14T11:15:08Z"]
    assert git_receipt["status"] == "passed"
    assert (git_receipt["commit_sha1"], git_receipt["tree_sha1"]) == (
        COMMIT,
        TREE,
    )
    assert git_receipt["source_state_artifact_sha256"] == _sha256(
        source_state_raw
    )
    assert git_receipt["source_state_root_sha256"] == source_state["root_sha256"]
    assert git_receipt["source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert len(git_receipt["commands"]) == 26
    assert all(row["exit_code"] == 0 for row in git_receipt["commands"])
    assert all(
        row["stderr_sha256"] == EMPTY_SHA256 for row in git_receipt["commands"]
    )
    source_rows = {row["path"]: row for row in source_state["files"]}
    assert len(source_rows) == len(git_receipt["source_files"]) == 6
    for row in git_receipt["source_files"]:
        source_row = source_rows[row["path"]]
        assert row["verified"] is True
        assert row["bytes"] == source_row["bytes"]
        assert row["live_sha256"] == row["committed_sha256"] == source_row["sha256"]

    assert infrastructure["git_commit"] == COMMIT
    assert infrastructure["git_tree"] == TREE
    assert len(infrastructure["files"]) == 11
    for row in infrastructure["files"]:
        path = ROOT / row["path"]
        raw = path.read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])
        assert row["mode"] == ("100755" if os.access(path, os.X_OK) else "100644")

    assert execution["job_id"] == JOB_ID
    assert execution["status"] == "passed"
    assert execution["error"] is None
    assert execution["classification"] == (
        "two-producer-byte-identity-and-independent-cut-liveness-verification"
    )
    wmi_python = "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
    assert execution["requested_resources"] == {
        "cpus_per_task": 1,
        "memory_mib": 4096,
        "nodes": 1,
        "ntasks": 1,
        "partition": "cpu_idle",
        "time_limit": "00:15:00",
        "time_limit_seconds": 900,
    }
    assert execution["runtime"] == {
        "dont_write_bytecode": True,
        "executable": wmi_python,
        "implementation": "CPython",
        "machine": "x86_64",
        "no_site": True,
        "optimize": 0,
        "pycache_prefix": "/proc/peano-hydra-a23d-disabled-pycache",
        "python_version": "3.12.12",
        "safe_path": True,
        "user_site_disabled": True,
    }
    source = execution["source"]
    assert (source["git_commit"], source["git_tree"], source["snapshot_sha256"]) == (
        COMMIT,
        TREE,
        SNAPSHOT,
    )
    assert source["source_state"] == _record(SOURCE_STATE_PATH)
    assert source["git_receipt"] == _record(GIT_RECEIPT_PATH)
    assert source["infrastructure_manifest"] == _record(INFRASTRUCTURE_PATH)
    assert source["provenance"] == {
        "git_commit": COMMIT,
        "git_dirty": False,
        "sha256": FILE_PINS["inputs/.peano-source-provenance.tsv"][1],
        "sync_timestamp": provenance[2],
    }

    evidence = execution["evidence"]
    assert evidence["producer_byte_identical"] is True
    assert evidence["producer_hash_seeds"] == [0, 0]
    assert evidence["producer_run_count"] == 2
    assert evidence["evidence_boundary"] == {
        "bounded_one_root_cut_liveness_execution_complete": True,
        "construction_direct_vector_execution_bound": True,
        "dependency_necessity_established": False,
        "derived_direct_vector_independently_reproduced": True,
        "global_comparison_complete": False,
        "logical_minimality_established": False,
        "optimized_best_known": False,
        "optimized_vector_independently_audited": False,
        "public_graph_applied": False,
        "publication_applied": False,
        "route_rejections_independently_verified": False,
        "shared_kernel_with_producer": True,
    }
    assert evidence["candidate"] == {
        "artifact_bytes": len(candidate_raw),
        "artifact_sha256": _sha256(candidate_raw),
        "derived_direct_dependencies": ["mul_add", "add_comm"],
        "execution_bound": True,
        "path": CANDIDATE_PATH.name,
        "root_sha256": candidate["root_sha256"],
        "source_state_root_sha256": source_state["root_sha256"],
        "theorem_index": 256,
        "theorem_name": "odd_add_odd",
    }
    assert evidence["verifier"] == {
        "artifact_bytes": len(verification_raw),
        "artifact_sha256": _sha256(verification_raw),
        "hash_seed": 0,
        "path": VERIFICATION_PATH.name,
        "root_sha256": verification["root_sha256"],
        "status": "passed",
    }

    processes = execution["processes"]
    assert [row["role"] for row in processes] == [
        "producer-0",
        "producer-1",
        "independent-verifier",
    ]
    assert [row["hash_seed"] for row in processes] == [0, 0, 0]
    assert all(row["returncode"] == 0 for row in processes)
    assert all(row["timed_out"] is False for row in processes)
    assert all(row["output_limit_reached"] is False for row in processes)
    assert [row["timeout_seconds"] for row in processes] == [60, 60, 90]
    assert all(row["duration_seconds_millis"] >= 0 for row in processes)
    for process in processes:
        assert process["environment"] == {
            "HOME": "/nonexistent/peano-a23d-wmi",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23d-disabled-pycache",
            "TZ": "UTC",
        }

    candidate_identity = {"bytes": len(candidate_raw), "sha256": _sha256(candidate_raw)}
    for process in processes[:2]:
        assert process["stdout"] == {
            **candidate_identity,
            "path": f"{process['role']}.stdout.log",
        }
        stderr = EVIDENCE_ROOT / "runs" / JOB_ID / process["stderr"]["path"]
        assert process["stderr"] == _record(stderr)
    assert not any(EVIDENCE_ROOT.rglob("producer-*.stdout.log"))
    assert not any(EVIDENCE_ROOT.rglob("*run-2.json"))
    assert not any(
        path.name == CANDIDATE_PATH.name
        for path in (EVIDENCE_ROOT / "runs").rglob("*")
    )

    verifier_process = processes[2]
    verifier_logs = EVIDENCE_ROOT / "runs" / JOB_ID
    assert verifier_process["stdout"] == _record(
        verifier_logs / "independent-verifier.stdout.log"
    )
    assert verifier_process["stderr"] == _record(
        verifier_logs / "independent-verifier.stderr.log"
    )
    assert (verifier_logs / "independent-verifier.stdout.log").read_bytes() == (
        verification_raw
    )

    assert collection["job_id"] == JOB_ID
    assert collection["status"] == "passed"
    assert collection["classification"] == (
        "completed-dual-producer-and-independent-cut-liveness-verification"
    )
    assert collection["execution_validation"] == {"status": "accepted"}
    assert collection["scheduler_logs"]["rejections"] == {}
    assert collection["execution_receipt"] == {
        **_record(EXECUTION_PATH),
        "exists": True,
        "root_sha256": execution["root_sha256"],
    }
    assert collection["accounting"] == {
        "allocated_cpus": 1,
        "derived_exit_code": "0:0",
        "elapsed_raw_seconds": 3,
        "exit_code": "0:0",
        "job_id": JOB_ID,
        "max_rss": "",
        "node_list": "c3n1",
        "raw_bytes": 38,
        "raw_sha256": FILE_PINS["sacct.psv"][1],
        "requested_memory": "4G",
        "state": "COMPLETED",
    }
    for stream, suffix in (("stdout", "out"), ("stderr", "err")):
        path = (
            EVIDENCE_ROOT
            / "logs"
            / f"peano-hydra-a23d-cut-liveness-220246.{suffix}"
        )
        assert collection["scheduler_logs"][stream] == {
            **_record(path),
            "exists": True,
        }

    submission_raw = (EVIDENCE_ROOT / "submission.tsv").read_bytes()
    submission_values = submission_raw.decode("ascii").removesuffix("\n").split("\t")
    assert len(submission_values) == 16
    submission = {
        "artifact_bytes": len(submission_raw),
        "artifact_sha256": _sha256(submission_raw),
        "cpus_per_task": 1,
        "git_commit": submission_values[3],
        "git_receipt_sha256": submission_values[6],
        "git_tree": submission_values[4],
        "infrastructure_sha256": submission_values[7],
        "job_id": submission_values[1],
        "memory_mib": 4096,
        "ntasks": 1,
        "partition": submission_values[10],
        "provenance_sha256": submission_values[8],
        "sbatch_sha256": submission_values[15],
        "snapshot_sha256": submission_values[2],
        "source_state_sha256": submission_values[5],
        "submission_timestamp": submission_values[0],
        "sync_timestamp": submission_values[9],
        "time_limit": submission_values[14],
    }
    assert collection["submission"] == submission
    assert (
        submission["job_id"],
        submission["snapshot_sha256"],
        submission["git_commit"],
        submission["git_tree"],
    ) == (JOB_ID, SNAPSHOT, COMMIT, TREE)
    assert submission["source_state_sha256"] == _sha256(source_state_raw)
    assert submission["git_receipt_sha256"] == _sha256(git_receipt_raw)
    assert submission["infrastructure_sha256"] == _sha256(infrastructure_raw)

    deposit_raw = (EVIDENCE_ROOT / "deposit.tsv").read_bytes()
    deposit_values = deposit_raw.decode("ascii").removesuffix("\n").split("\t")
    assert len(deposit_values) == 9
    deposit = {
        "archive_bytes": int(deposit_values[1]),
        "artifact_bytes": len(deposit_raw),
        "artifact_sha256": _sha256(deposit_raw),
        "git_commit": deposit_values[2],
        "git_receipt_sha256": deposit_values[5],
        "git_tree": deposit_values[3],
        "infrastructure_sha256": deposit_values[6],
        "provenance_sha256": deposit_values[7],
        "snapshot_sha256": deposit_values[0],
        "source_state_sha256": deposit_values[4],
        "sync_timestamp": deposit_values[8],
    }
    assert collection["source_deposit"] == deposit
    assert deposit["archive_bytes"] == 283_796_480
    for key in (
        "git_commit",
        "git_receipt_sha256",
        "git_tree",
        "infrastructure_sha256",
        "provenance_sha256",
        "snapshot_sha256",
        "source_state_sha256",
        "sync_timestamp",
    ):
        assert deposit[key] == submission[key]

    assert (EVIDENCE_ROOT / "sacct.psv").read_bytes() == (
        b"220246|COMPLETED|0:0|0:0|3||4G|1|c3n1\n"
    )
    assert collection["submitted_sbatch"] == {
        "bytes": 5_057,
        "path": "peano_wmi_hydra_a23d_cut_liveness.sbatch",
        "sha256": (
            "de5463e13d626cd0e7c34c1ce96e0e3e7b5aaf5e6304453f794ac41f06c629d9"
        ),
    }
    sbatch_raw = (ROOT / "slurm" / collection["submitted_sbatch"]["path"]).read_bytes()
    assert (len(sbatch_raw), _sha256(sbatch_raw)) == (
        collection["submitted_sbatch"]["bytes"],
        collection["submitted_sbatch"]["sha256"],
    )
    assert len(execution_raw) == FILE_PINS["runs/220246/execution-receipt.json"][0]
    _assert_no_authority(git_receipt)
    _assert_no_authority(execution)
    _assert_no_authority(collection)
