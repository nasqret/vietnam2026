"""Acceptance gate for the retained Hydra A2.3a WMI pilot result.

This suite never rebuilds the optimizer candidate and never uses the network.
It pins the intentionally small retained evidence bundle, checks every receipt
binding, and replays only the independent kernel verifier in a fresh process.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

import pytest


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-hydra"
EVIDENCE_ROOT = ARTIFACT_ROOT / "a23a-wmi-pilot-219765"
CANDIDATE_PATH = (
    ARTIFACT_ROOT / "l0-optimizer-comparison-pilot-candidate-v1.json"
)
VERIFICATION_PATH = (
    ARTIFACT_ROOT
    / "l0-optimizer-comparison-pilot-independent-verification-v1.json"
)
SOURCE_STATE_PATH = EVIDENCE_ROOT / "inputs" / "producer-source-state.json"
GIT_RECEIPT_PATH = (
    EVIDENCE_ROOT / "inputs" / "producer-git-verification-receipt.json"
)
INFRASTRUCTURE_PATH = (
    EVIDENCE_ROOT / "inputs" / "wmi-infrastructure-manifest.json"
)
EXECUTION_PATH = EVIDENCE_ROOT / "runs" / "219765" / "execution-receipt.json"
COLLECTION_PATH = EVIDENCE_ROOT / "collections" / "job-219765.json"
VERIFIER_CLI = (
    ROOT / "scripts" / "verify_peano_hydra_library_optimizer_comparison_pilot.py"
)

JOB_ID = "219765"
COMMIT = "0f6ca3a0cf5998212e3a0ad508ba77e88a15a17d"
TREE = "9051b43aa3f7f75d37ce8d410b9c7a81ba472d94"
SNAPSHOT = "707398a7494482dbcc38c8438582688e01f88b395ab61e64be4a7d6396178824"
SOURCE_STATE_SEMANTIC_SHA256 = (
    "64ceb310fb0030ac0a1c040d5a15076a53ac1882dd17d725ea92e404f66d942b"
)

# Paths are relative to ``ARTIFACT_ROOT``.  Every retained byte is included;
# the optional root is the compact-JSON hash of that document's root preimage.
FILE_PINS = {
    "l0-optimizer-comparison-pilot-candidate-v1.json": (
        848_463,
        "3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b",
        "90a3d97a466dc7b1c9e6032b1b56b8ede3fcece8d56a4b39f2d4e5f34dbeb770",
    ),
    "l0-optimizer-comparison-pilot-independent-verification-v1.json": (
        18_327,
        "6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a",
        "e21290f654c1a30e0bdf79e796a8ca1da6ad3aa6a1cb1d8ba34d3d376de052dc",
    ),
    "a23a-wmi-pilot-219765/collections/job-219765.json": (
        8_707,
        "25e616fc9225ab59db6a089e8a53ed2d44915a54b42f073bcaaa020fc2ff609a",
        "52339b926ea8b9650787a3db138185e21144f6cdf83596d224ccc6b23435daf2",
    ),
    "a23a-wmi-pilot-219765/deposit.tsv": (
        438,
        "31a194c1469efd8f58d5c473fd28ae2675b7947d49212001ff0776a8bb01e14e",
        None,
    ),
    "a23a-wmi-pilot-219765/inputs/.peano-source-provenance.tsv": (
        68,
        "7862d7916c8b13ce26fe5540c6f901c22e6db55089aa9bfa1c2344d707129301",
        None,
    ),
    "a23a-wmi-pilot-219765/inputs/producer-git-verification-receipt.json": (
        28_400,
        "04158535ba4d920190f63e8a4cc48effcc33ccc162d8a7472265862149dc907e",
        "332fdc27d3a427d00bf7fa1ac4877c7c1fa73cf408413aedea179ae6846a7c6c",
    ),
    "a23a-wmi-pilot-219765/inputs/producer-source-state.json": (
        2_377,
        "3b6658ea8fae6c9430714781398232dd91a4d9c5edc756bd734a28cdb1734c82",
        "b8517b9d10868a3942cf5a42ceb8c61e34b317647ddac19da0a8cef998438029",
    ),
    "a23a-wmi-pilot-219765/inputs/wmi-infrastructure-manifest.json": (
        5_618,
        "5b4e740afa2af94a154185b9b7e8200f25c683b93f73e5aa92335f33e002d87b",
        "d0a299cd7b83c3584df36f7ae680613136f662c123768c871e8ba74806cf3a6b",
    ),
    "a23a-wmi-pilot-219765/logs/peano-hydra-a23a-219765.err": (
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        None,
    ),
    "a23a-wmi-pilot-219765/logs/peano-hydra-a23a-219765.out": (
        422,
        "88c0e3278fbf2a1b68f1e56db45595f5f47bbd12a55dc085d628ad681dec15b3",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/execution-receipt.json": (
        18_088,
        "779a971237f9ac5efe3a86dca5b5c4d74a6da56ab154b91e106f7fd1dac63a34",
        "7a597563c173cd0cb3d57ff42cd566a8531756e84bf8ba907e7c79ec7295dc0e",
    ),
    "a23a-wmi-pilot-219765/runs/219765/independent-verifier.stderr.log": (
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/independent-verifier.stdout.log": (
        144,
        "ea0b95150724f498b785f52ec7cfc870523005f3e80417007796335a07ab78c7",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/producer-0.stderr.log": (
        1_447,
        "6e0581b6b3a3f4b0ccd7bd102bb79825b641d7470ff15e8579e231caab5b51af",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/producer-0.stdout.log": (
        117,
        "6ea76700dc04a8d0e0a83b1d4a53b3afa5186ffe716d14d44d6b92303e6b7acd",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/producer-1.stderr.log": (
        1_447,
        "6e0581b6b3a3f4b0ccd7bd102bb79825b641d7470ff15e8579e231caab5b51af",
        None,
    ),
    "a23a-wmi-pilot-219765/runs/219765/producer-1.stdout.log": (
        117,
        "6ea76700dc04a8d0e0a83b1d4a53b3afa5186ffe716d14d44d6b92303e6b7acd",
        None,
    ),
    "a23a-wmi-pilot-219765/sacct.psv": (
        39,
        "26eec8cb84f436121c29698eef456e582055493f246697ff84a80615df935023",
        None,
    ),
    "a23a-wmi-pilot-219765/submission.tsv": (
        553,
        "053a0cf2fa7b4d0b5c688724e903cbe57c8d699f22c45fa0d580564060042602",
        None,
    ),
}

EVIDENCE_DIRECTORIES = {
    "collections",
    "inputs",
    "logs",
    "runs",
    "runs/219765",
}
AUTHORITY_FALSE_FIELDS = {
    "a2_complete",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_ready",
    "global_best_claim",
    "lineage_complete",
    "minimality_claim",
    "optimized_best_known",
    "optimized_vector_independently_audited",
    "producer_git_verified",
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
}
CANDIDATE_IDS = (
    "retained-replay",
    "a2.2-direct-cut-rebuild",
    "layered-closure",
)
COMPARISON_AXES = (
    "artifact_bytes",
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
)
REPRESENTATIVE_TIE_BREAK = (
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
    "artifact_bytes",
    "candidate_kind_order",
    "artifact_sha256",
    "candidate_id",
)
FRONTIER = ["a2.2-direct-cut-rebuild", "layered-closure"]
EXPECTED_THEOREMS = (
    (
        256,
        "odd_add_odd",
        (
            (14_977, 302, 32, 7),
            (13_640, 274, 31, 6),
            (12_709, 269, 37, 3),
        ),
    ),
    (
        376,
        "finite_bounded_injective_surjective",
        (
            (1_913_452, 42_463, 89, 1_266),
            (1_870_657, 41_341, 89, 1_235),
            (297_637, 8_355, 95, 20),
        ),
    ),
    (
        379,
        "beta_product_swap_last_invariant",
        (
            (391_540, 7_439, 67, 205),
            (386_189, 7_413, 67, 203),
            (118_018, 2_011, 79, 9),
        ),
    ),
)


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
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value, raw


def _assert_root(value: dict[str, object], expected: str) -> None:
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256", "theorems"}
    }
    preimage = {
        "format": f"{value['format']}-root-preimage",
        "payload": body,
        "v": value["v"],
    }
    assert value["root_preimage"] == preimage
    assert value["root_sha256"] == expected
    assert _compact_sha256(preimage) == expected


def _assert_theorem_record_root(
    document: dict[str, object], *, preimage_format: str
) -> None:
    identities = []
    for row in document["theorems"]:
        body = {key: item for key, item in row.items() if key != "record_sha256"}
        assert row["record_sha256"] == _compact_sha256(body)
        identities.append(
            {
                "index": row["index"],
                "name": row["name"],
                "record_sha256": row["record_sha256"],
            }
        )
    preimage = {
        "format": preimage_format,
        "records": identities,
        "v": document["v"],
    }
    assert document["theorem_records"] == {
        "count": len(identities),
        "preimage": preimage,
        "root_sha256": _compact_sha256(preimage),
    }


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


def _file_record(path: Path, *, retained_name: str | None = None) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.name if retained_name is None else retained_name,
        "sha256": _sha256(raw),
    }


def _dominates(left: dict[str, object], right: dict[str, object]) -> bool:
    left_metrics = left["metrics"]
    right_metrics = right["metrics"]
    return all(left_metrics[axis] <= right_metrics[axis] for axis in COMPARISON_AXES) and any(
        left_metrics[axis] < right_metrics[axis] for axis in COMPARISON_AXES
    )


def _pareto_frontier(artifacts: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        candidate
        for candidate in artifacts
        if not any(
            other is not candidate and _dominates(other, candidate)
            for other in artifacts
        )
    ]


def _representative(artifacts: list[dict[str, object]]) -> dict[str, object]:
    def key(artifact: dict[str, object]) -> tuple[object, ...]:
        metrics = artifact["metrics"]
        values = {**metrics, **artifact}
        return tuple(values[field] for field in REPRESENTATIVE_TIE_BREAK)

    return min(artifacts, key=key)


def test_retained_inventory_bytes_hashes_roots_and_no_duplicate_snapshot() -> None:
    expected_evidence_files = {
        relative.removeprefix("a23a-wmi-pilot-219765/")
        for relative in FILE_PINS
        if relative.startswith("a23a-wmi-pilot-219765/")
    }
    actual_evidence_files = {
        path.relative_to(EVIDENCE_ROOT).as_posix()
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_file()
    }
    actual_evidence_directories = {
        path.relative_to(EVIDENCE_ROOT).as_posix()
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_dir()
    }
    assert actual_evidence_files == expected_evidence_files
    assert actual_evidence_directories == EVIDENCE_DIRECTORIES
    assert not any(path.is_symlink() for path in EVIDENCE_ROOT.rglob("*"))

    retained_results = {
        path.name
        for path in ARTIFACT_ROOT.glob("l0-optimizer-comparison-pilot-*.json")
    }
    assert retained_results == {
        CANDIDATE_PATH.name,
        VERIFICATION_PATH.name,
    }

    for relative, (expected_bytes, expected_sha256, expected_root) in FILE_PINS.items():
        path = ARTIFACT_ROOT / relative
        raw = path.read_bytes()
        assert len(raw) == expected_bytes, relative
        assert _sha256(raw) == expected_sha256, relative
        if expected_root is not None:
            document, canonical_raw = _load_json(path)
            assert canonical_raw == raw
            _assert_root(document, expected_root)


def test_candidate_and_verifier_pin_metrics_frontiers_and_authority() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)

    _assert_theorem_record_root(
        candidate,
        preimage_format=(
            "peano-hydra-library-optimizer-comparison-pilot-records-preimage"
        ),
    )
    _assert_theorem_record_root(
        verification,
        preimage_format=(
            "peano-hydra-library-optimizer-comparison-pilot-verification-records-"
            "preimage"
        ),
    )

    assert (
        candidate["format"],
        candidate["id"],
        candidate["v"],
        candidate["status"],
        candidate["logic_mode"],
        candidate["theorem_count"],
    ) == (
        "peano-hydra-library-optimizer-comparison-pilot",
        "authoring-l0-optimizer-comparison-pilot-candidate-v1",
        1,
        "candidate",
        "intuitionistic",
        3,
    )
    assert candidate["producer_source_state"] == source_state
    assert candidate["producer_source_state_sha256"] == _compact_sha256(source_state)
    assert candidate["producer_source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert source_state["git_verified"] is False
    assert source_state["commit_sha1"] == COMMIT
    assert source_state["tree_sha1"] == TREE

    assert (
        verification["format"],
        verification["id"],
        verification["v"],
        verification["status"],
        verification["candidate_status"],
        verification["kernel_artifacts_verified"],
        verification["theorem_count"],
    ) == (
        "peano-hydra-library-optimizer-comparison-pilot-verification",
        "independent-a2.3a-optimizer-comparison-pilot-verification-v1",
        1,
        "passed",
        "candidate",
        True,
        3,
    )
    assert verification["candidate"] == {
        "artifact_bytes": len(candidate_raw),
        "artifact_sha256": _sha256(candidate_raw),
        "root_sha256": candidate["root_sha256"],
        "theorem_record_root_sha256": candidate["theorem_records"]["root_sha256"],
    }
    assert verification["producer_source_state"] == {
        "artifact_bytes": len(source_state_raw),
        "artifact_sha256": _sha256(source_state_raw),
        "root_sha256": source_state["root_sha256"],
        "semantic_sha256": _compact_sha256(source_state),
    }
    assert verification["producer_source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert verification["verifier"]["load_mode"] == (
        "direct-source-module-without-training-package-init"
    )
    assert verification["verifier"]["import_policy"] == (
        "stdlib-and-peano-kernel-only"
    )
    verifier_source = ROOT / verification["verifier"]["path"]
    assert _sha256(verifier_source.read_bytes()) == verification["verifier"]["sha256"]

    candidate_rows = candidate["theorems"]
    verification_rows = verification["theorems"]
    assert len(candidate_rows) == len(verification_rows) == 3
    for candidate_row, verification_row, expected in zip(
        candidate_rows, verification_rows, EXPECTED_THEOREMS, strict=True
    ):
        index, name, metric_rows = expected
        assert (candidate_row["index"], candidate_row["name"]) == (index, name)
        assert (verification_row["index"], verification_row["name"]) == (index, name)
        assert verification_row["candidate_record_sha256"] == candidate_row[
            "record_sha256"
        ]
        comparison = candidate_row["comparison"]
        assert comparison["axes_in_componentwise_order"] == list(COMPARISON_AXES)
        assert comparison["representative_tie_break"] == list(
            REPRESENTATIVE_TIE_BREAK
        )
        assert comparison["candidate_universe_ids_in_order"] == list(CANDIDATE_IDS)
        assert comparison["candidate_universe_complete"] is True
        assert comparison["nondominated_candidate_ids_in_input_order"] == FRONTIER
        assert comparison["representative_candidate_id"] == "layered-closure"
        assert verification_row["nondominated_candidate_ids_in_input_order"] == FRONTIER
        assert verification_row["representative_candidate_id"] == "layered-closure"
        assert len(candidate_row["artifacts"]) == len(verification_row["artifacts"]) == 3
        for order, (candidate_artifact, verified_artifact, metric_tuple) in enumerate(
            zip(
                candidate_row["artifacts"],
                verification_row["artifacts"],
                metric_rows,
                strict=True,
            )
        ):
            expected_metrics = dict(
                zip(
                    ("artifact_bytes", "proof_nodes", "proof_depth", "cut_nodes"),
                    metric_tuple,
                    strict=True,
                )
            )
            assert candidate_artifact["candidate_id"] == CANDIDATE_IDS[order]
            assert candidate_artifact["candidate_kind_order"] == order
            assert candidate_artifact["metrics"] == expected_metrics
            assert candidate_artifact["kernel_accepted"] is True
            assert verified_artifact["candidate_id"] == CANDIDATE_IDS[order]
            assert verified_artifact["candidate_kind_order"] == order
            assert verified_artifact["metrics"] == expected_metrics
            assert verified_artifact["artifact_sha256"] == candidate_artifact["artifact_sha256"]
            assert verified_artifact["kernel_accepted"] is True

        independently_nondominated = _pareto_frontier(candidate_row["artifacts"])
        assert [row["candidate_id"] for row in independently_nondominated] == FRONTIER
        assert _representative(independently_nondominated)["candidate_id"] == (
            "layered-closure"
        )

    assert candidate["aggregate"]["representative_counts"] == {
        "a2.2-direct-cut-rebuild": 0,
        "layered-closure": 3,
        "retained-replay": 0,
    }
    assert verification["aggregate"]["kernel_accepted_artifact_count"] == 9
    _assert_no_authority(candidate)
    _assert_no_authority(verification)
    assert len(verification_raw) == FILE_PINS[VERIFICATION_PATH.name][0]


def test_controlled_independent_verifier_reproduces_exact_receipt(
    tmp_path: Path,
) -> None:
    python = (
        sys.executable
        if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12)
        else shutil.which("python3.12")
    )
    if python is None:
        pytest.skip("controlled verifier requires CPython 3.12")
    probe = subprocess.run(
        [
            python,
            "-I",
            "-c",
            (
                "import platform,sys;"
                "print(platform.python_implementation(),sys.version_info[0],"
                "sys.version_info[1],int(sys.flags.safe_path),sep='|')"
            ),
        ],
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert probe.returncode == 0, probe.stderr or probe.stdout
    assert probe.stderr == ""
    assert probe.stdout == "CPython|3|12|1\n"
    output = tmp_path / "independent-verification.json"
    environment = {
        "HOME": str(tmp_path),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "2",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23a-disabled-pycache",
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
            "--candidate",
            str(CANDIDATE_PATH),
            "--producer-source-state",
            str(SOURCE_STATE_PATH),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stderr == ""
    assert "3 roots, 9 kernel-accepted artifacts" in completed.stdout
    assert output.read_bytes() == VERIFICATION_PATH.read_bytes()


def test_execution_collection_git_and_scheduler_cross_bindings() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)
    git_receipt, git_receipt_raw = _load_json(GIT_RECEIPT_PATH)
    infrastructure, infrastructure_raw = _load_json(INFRASTRUCTURE_PATH)
    execution, execution_raw = _load_json(EXECUTION_PATH)
    collection, _collection_raw = _load_json(COLLECTION_PATH)

    provenance_path = EVIDENCE_ROOT / "inputs" / ".peano-source-provenance.tsv"
    provenance_raw = provenance_path.read_bytes()
    provenance = provenance_raw.decode("ascii").removesuffix("\n").split("\t")
    assert provenance == [COMMIT, "false", "2026-08-10T00:51:24Z"]

    assert source_state["commit_sha1"] == git_receipt["commit_sha1"] == COMMIT
    assert source_state["tree_sha1"] == git_receipt["tree_sha1"] == TREE
    assert git_receipt["status"] == "passed"
    assert git_receipt["source_state_artifact_sha256"] == _sha256(source_state_raw)
    assert git_receipt["source_state_sha256"] == _compact_sha256(source_state)
    assert git_receipt["source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert git_receipt["generator"]["verified"] is True
    assert all(row["verified"] is True for row in git_receipt["source_files"])
    assert all(command["exit_code"] == 0 for command in git_receipt["commands"])
    verification_facts = git_receipt["verification"]
    for key in (
        "clean_after",
        "clean_before",
        "commit_stable",
        "diff_cached_quiet_after",
        "diff_cached_quiet_before",
        "diff_quiet_after",
        "diff_quiet_before",
        "generator_matches_head",
        "producer_files_match_head",
        "stage_zero_regular_blobs",
        "tree_stable",
    ):
        assert verification_facts[key] is True
    assert verification_facts["head_before"] == verification_facts["head_after"] == COMMIT
    assert verification_facts["tree_before"] == verification_facts["tree_after"] == TREE
    assert verification_facts["porcelain_before_bytes"] == 0
    assert verification_facts["porcelain_after_bytes"] == 0

    assert infrastructure["git_commit"] == COMMIT
    assert infrastructure["git_tree"] == TREE
    for row in infrastructure["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert _sha256(raw) == row["sha256"]

    assert execution["format"] == "peano-hydra-a23a-wmi-execution-receipt"
    assert execution["job_id"] == JOB_ID
    assert execution["status"] == "passed"
    assert execution["classification"] == (
        "two-producer-byte-identity-and-independent-verification"
    )
    assert execution["requested_resources"] == {
        "cpus_per_task": 1,
        "memory_mib": 4096,
        "nodes": 1,
        "ntasks": 1,
        "partition": "cpu_idle",
        "time_limit": "00:15:00",
        "time_limit_seconds": 900,
    }
    wmi_python = (
        "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
    )
    assert execution["runtime"] == {
        "dont_write_bytecode": True,
        "executable": wmi_python,
        "implementation": "CPython",
        "machine": "x86_64",
        "no_site": True,
        "pycache_prefix": "/proc/peano-hydra-a23a-disabled-pycache",
        "python_version": "3.12.12",
        "safe_path": True,
    }
    evidence = execution["evidence"]
    assert evidence["producer_byte_identical"] is True
    assert evidence["producer_hash_seeds"] == [0, 1]
    assert evidence["candidate"] == {
        "bytes": len(candidate_raw),
        "path": "candidate-hashseed-0.json",
        "root_sha256": candidate["root_sha256"],
        "sha256": _sha256(candidate_raw),
    }
    assert evidence["verifier"] == {
        "bytes": len(verification_raw),
        "hash_seed": 2,
        "path": "independent-verifier-receipt.json",
        "root_sha256": verification["root_sha256"],
        "sha256": _sha256(verification_raw),
        "status": "passed",
    }

    remote_root = (
        "/work/bnaskrecki/peano-lab-training/tmp/hydra-a23a-pilot/"
        f"{SNAPSHOT}"
    )
    remote_source_state = f"{remote_root}/inputs/producer-source-state.json"
    remote_run = f"{remote_root}/runs/{JOB_ID}"
    isolated_prefix = [wmi_python, "-B", "-P", "-s", "-S"]
    expected_processes = (
        (
            "producer-0",
            0,
            360,
            [
                *isolated_prefix,
                "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                "--producer-source-state",
                remote_source_state,
                "--output",
                f"{remote_run}/candidate-hashseed-0.json",
            ],
        ),
        (
            "producer-1",
            1,
            360,
            [
                *isolated_prefix,
                "scripts/build_peano_hydra_library_optimizer_comparison_pilot.py",
                "--producer-source-state",
                remote_source_state,
                "--output",
                f"{remote_run}/candidate-hashseed-1.json",
            ],
        ),
        (
            "independent-verifier",
            2,
            90,
            [
                *isolated_prefix,
                "scripts/verify_peano_hydra_library_optimizer_comparison_pilot.py",
                "--candidate",
                f"{remote_run}/candidate-hashseed-0.json",
                "--producer-source-state",
                remote_source_state,
                "--output",
                f"{remote_run}/independent-verifier-receipt.json",
            ],
        ),
    )
    run_root = EVIDENCE_ROOT / "runs" / JOB_ID
    for process, (role, seed, timeout, expected_argv) in zip(
        execution["processes"], expected_processes, strict=True
    ):
        assert process["role"] == role
        assert process["hash_seed"] == seed
        assert process["environment"] == {
            "HOME": "/nonexistent/peano-a23a-wmi",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": str(seed),
            "PYTHONNOUSERSITE": "1",
            "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23a-disabled-pycache",
            "TZ": "UTC",
        }
        assert process["returncode"] == 0
        assert process["timed_out"] is False
        assert process["output_limit_reached"] is False
        assert process["timeout_seconds"] == timeout
        assert process["argv"] == expected_argv
        assert process["stdout"] == _file_record(run_root / f"{role}.stdout.log")
        assert process["stderr"] == _file_record(run_root / f"{role}.stderr.log")

    source = execution["source"]
    assert source["git_commit"] == COMMIT
    assert source["git_tree"] == TREE
    assert source["snapshot_sha256"] == SNAPSHOT
    assert source["source_state"] == _file_record(SOURCE_STATE_PATH)
    assert source["git_receipt"] == _file_record(GIT_RECEIPT_PATH)
    assert source["infrastructure_manifest"] == _file_record(INFRASTRUCTURE_PATH)
    assert source["provenance"] == {
        "git_commit": COMMIT,
        "git_dirty": False,
        "sha256": _sha256(provenance_raw),
        "sync_timestamp": provenance[2],
    }

    submission_path = EVIDENCE_ROOT / "submission.tsv"
    submission_raw = submission_path.read_bytes()
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
    assert submission["provenance_sha256"] == _sha256(provenance_raw)

    deposit_path = EVIDENCE_ROOT / "deposit.tsv"
    deposit_raw = deposit_path.read_bytes()
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

    sacct_path = EVIDENCE_ROOT / "sacct.psv"
    sacct_raw = sacct_path.read_bytes()
    assert sacct_raw == b"219765|COMPLETED|0:0|0:0|60||4G|1|c2n1\n"
    accounting = collection["accounting"]
    assert accounting == {
        "allocated_cpus": 1,
        "derived_exit_code": "0:0",
        "elapsed_raw_seconds": 60,
        "exit_code": "0:0",
        "job_id": JOB_ID,
        "max_rss": "",
        "node_list": "c2n1",
        "raw_bytes": len(sacct_raw),
        "raw_sha256": _sha256(sacct_raw),
        "requested_memory": "4G",
        "state": "COMPLETED",
    }
    assert collection["format"] == "peano-hydra-a23a-wmi-collection-receipt"
    assert collection["job_id"] == JOB_ID
    assert collection["status"] == "passed"
    assert collection["classification"] == "completed-and-independently-verified"
    assert collection["execution_validation"] == {"status": "accepted"}
    assert collection["execution_receipt"] == {
        "bytes": len(execution_raw),
        "exists": True,
        "path": EXECUTION_PATH.name,
        "root_sha256": execution["root_sha256"],
        "sha256": _sha256(execution_raw),
    }
    scheduler_logs = collection["scheduler_logs"]
    assert scheduler_logs["rejections"] == {}
    assert scheduler_logs["stdout"] == {
        **_file_record(
            EVIDENCE_ROOT / "logs" / "peano-hydra-a23a-219765.out"
        ),
        "exists": True,
    }
    assert scheduler_logs["stderr"] == {
        **_file_record(
            EVIDENCE_ROOT / "logs" / "peano-hydra-a23a-219765.err"
        ),
        "exists": True,
    }
    sbatch = ROOT / "slurm" / "peano_wmi_hydra_a23a_pilot.sbatch"
    assert collection["submitted_sbatch"] == _file_record(sbatch)
    assert collection["submitted_sbatch"]["sha256"] == submission["sbatch_sha256"]

    _assert_no_authority(git_receipt)
    _assert_no_authority(execution)
    _assert_no_authority(collection)
