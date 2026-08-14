"""Acceptance gate for the retained Hydra A2.3c WMI negative replay.

This suite never repeats the expensive tactic campaign.  It pins the closed
retained bundle, validates the 3/22/44 result boundary, replays the independent
tactic-free structural verifier, and reconstructs the WMI receipt bindings.
"""

from __future__ import annotations

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
EVIDENCE_ROOT = ARTIFACT_ROOT / "a23c-wmi-negative-replay-220227"
RESULT_ROOT = EVIDENCE_ROOT / "results"
CANDIDATE_PATH = (
    RESULT_ROOT / "l0-pilot-dependency-vector-negative-replay-candidate-v1.json"
)
VERIFICATION_PATH = (
    RESULT_ROOT
    / "l0-pilot-dependency-vector-negative-replay-independent-verification-v1.json"
)
SOURCE_STATE_PATH = EVIDENCE_ROOT / "inputs" / "replayer-source-state.json"
GIT_RECEIPT_PATH = (
    EVIDENCE_ROOT / "inputs" / "replayer-git-verification-receipt.json"
)
INFRASTRUCTURE_PATH = (
    EVIDENCE_ROOT / "inputs" / "wmi-infrastructure-manifest.json"
)
EXECUTION_PATH = EVIDENCE_ROOT / "runs" / "220227" / "execution-receipt.json"
COLLECTION_PATH = EVIDENCE_ROOT / "collections" / "job-220227.json"
VERIFIER_CLI = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py"
)

JOB_ID = "220227"
COMMIT = "a1830b8d019baaec72d1d2b3cc8046c72d22a336"
TREE = "2bed15ee16c4c6b3360f4d6a711246e9020cfd9c"
SNAPSHOT = "b8e30114001162ef4a189d702f55844bda4f401abd452d7e212f2aeecdfc3719"
SOURCE_STATE_SEMANTIC_SHA256 = (
    "d4f67373b2f284ff29d70596944844bdcb1c4a014ca992d808a031ac135b13af"
)
INVENTORY_SHA256 = (
    "05d80cae1648769a377d3d5fc429f0edac0f484bd526b2607e236930baf282d0"
)
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Paths are relative to EVIDENCE_ROOT.  The optional third value is the
# compact-JSON digest of the document's root preimage.
FILE_PINS = {
    "collections/job-220227.json": (
        8_967,
        "2f187bde83cdd2bba97cacb0af0a6dcc4c204e6d0eb224ff5732e2433ed6266d",
        "17421fa3ebdf15020acc2bafad9ce100641d3403b2ce938a9c0b02fc42286814",
    ),
    "deposit.tsv": (
        438,
        "a8bbfb3a8ca30c13f2af2200cea20daf929c9c0d8831af4172d1258986321127",
        None,
    ),
    "inputs/.peano-source-provenance.tsv": (
        68,
        "cba0c0d750421fd223686f8d76a169cbd9e5b21a680abc7cb250845d36ed277f",
        None,
    ),
    "inputs/replayer-git-verification-receipt.json": (
        29_334,
        "42ebb8a353b205916a167de74bf3adc8412f9e16ad2bae8dab9213a7a37b8b8d",
        "85825e1ac8a9e7255fc64afd305bee99d93dac44382dd64e1723483388eeb7b7",
    ),
    "inputs/replayer-source-state.json": (
        2_500,
        "4fbcb219cf746da206fb07b99f6149922b761fff551fafd0b28f557bc53bf0b0",
        "832372c5838b2cf3230f5d305ba6b4c9350d165e3c68debe1667f7fa6653722b",
    ),
    "inputs/wmi-infrastructure-manifest.json": (
        5_858,
        "2057bc1ab33e2cd863062bc370bb16b6d8f7022592b7ca73be5b05850282ecce",
        "5fb4363d47b5d0bc55ab68186f158087c3750e0a512361acf9c2d711e0f41f43",
    ),
    "logs/peano-hydra-a23c-negative-replay-220227.err": (
        0,
        EMPTY_SHA256,
        None,
    ),
    "logs/peano-hydra-a23c-negative-replay-220227.out": (
        442,
        "f4dbd3768cd6072fd2bb2199cf9d66a68b19ab648e089105ed6375075db7d2c6",
        None,
    ),
    "results/l0-pilot-dependency-vector-negative-replay-candidate-v1.json": (
        322_779,
        "46989ea781e1f66b585c5e0817fdf4e76ba24ff34feec71e9cea2162289f2dba",
        "f17e8c4a2b8080401376ab04f96d771b466946b87b816cb99be54299cbd6a02f",
    ),
    "results/l0-pilot-dependency-vector-negative-replay-independent-verification-v1.json": (
        27_484,
        "48884600840c37044e099683b832659aec1fb22e4068637ad7212c104fe10293",
        "364d4ee4099856c44ee1633439f2e5b1c57ae24cc90d9178cdf7445008504733",
    ),
    "runs/220227/execution-receipt.json": (
        20_492,
        "f5c051493fac987a4010043b2bc0b5ef85a8cf37976aff36b331a3c57c93c5b1",
        "60513353afa2539f82568ae4360d98192584920af4bfd530d930e97e94efacdf",
    ),
    "runs/220227/independent-verifier.stderr.log": (0, EMPTY_SHA256, None),
    "runs/220227/independent-verifier.stdout.log": (
        212,
        "4ce13eea5c6e7b0905058adb02e6b5d82f57dfbe290ac3a806a52b2314b23f61",
        None,
    ),
    "runs/220227/replayer-0.stderr.log": (0, EMPTY_SHA256, None),
    "runs/220227/replayer-1.stderr.log": (0, EMPTY_SHA256, None),
    "sacct.psv": (
        39,
        "6868582d10fc542676c33d154ab047c3b2aea0bc3a91f2a95ae1e28f0980857f",
        None,
    ),
    "submission.tsv": (
        553,
        "06e827b20889971371ae4efe67c00ea514729a345c35a4606ca63f84d6e005a2",
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
    "runs/220227",
}
AUTHORITY_FALSE_FIELDS = {
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
}
EXPECTED_THEOREMS = (
    (256, "odd_add_odd", 3),
    (376, "finite_bounded_injective_surjective", 14),
    (379, "beta_product_swap_last_invariant", 5),
)
ROUTES = {
    "readable-direct-closure",
    "proposed-layered-closure-construction",
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
    preimage = {
        "format": f"{value['format']}-root-preimage",
        "payload": body,
        "v": value["v"],
    }
    assert value["root_preimage"] == preimage
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


def _assert_hashed_records(records: list[dict[str, object]]) -> None:
    for row in records:
        body = {key: item for key, item in row.items() if key != "record_sha256"}
        assert row["record_sha256"] == _compact_sha256(body)


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
    assert sum(path.stat().st_size for path in actual_files.values()) == 419_166
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

    assert list(ARTIFACT_ROOT.glob("l0-pilot-dependency-vector-negative-replay-*.json")) == []
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
        for token in ("ledger", "pointer")
    )


def test_result_preserves_the_3_baseline_22_observation_44_route_boundary() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, _ = _load_json(VERIFICATION_PATH)

    assert (
        candidate["format"],
        candidate["id"],
        candidate["v"],
        candidate["status"],
        candidate["logic_mode"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-negative-replay",
        "independent-a2.3c-pilot-vector-negative-replay-v1",
        1,
        "passed",
        "intuitionistic",
    )
    assert candidate["aggregate"] == {
        "full_vector_baseline_count": 3,
        "independent_shared_observation_count": 22,
        "retained_route_row_count": 44,
        "route_rows_per_shared_observation": 2,
        "theorem_count": 3,
    }
    assert candidate["campaign_executed"] is True
    assert candidate["result_exists"] is True
    assert candidate["negative_observations_independently_verified"] is True
    assert candidate["route_rejections_independently_verified"] is False
    assert candidate["independence"] == {
        "a2.3b_producer_imported": False,
        "a2.3b_verifier_imported": False,
        "compile_candidate_body_called": False,
        "fresh_process_required": True,
        "independent_wrapper_implementation": True,
        "lower_level_call_sequence": [
            "replay_target",
            "start",
            "apply_tactic:intro",
            "apply_tactic:script-command",
            "ProofState/invariants_ok:after-every-success",
            "checked_final:baseline-only",
        ],
        "route_specific_assemblers_called": False,
        "shared_engine_with_a2.3b": True,
        "shared_intuitionistic_kernel": True,
    }

    baselines = candidate["baseline_records"]
    observations = candidate["negative_observation_records"]
    joins = candidate["retained_route_join"]["joins"]
    assert len(baselines) == 3
    assert len({row["record_sha256"] for row in baselines}) == 3
    assert len({row["proof_sha256"] for row in baselines}) == 3
    assert len(observations) == len(joins) == 22
    _assert_hashed_records(baselines)
    _assert_hashed_records(observations)
    _assert_hashed_records(candidate["theorems"])
    assert candidate["baselines"]["count"] == 3
    assert candidate["baselines"]["root_sha256"] == _compact_sha256(
        candidate["baselines"]["preimage"]
    )
    assert candidate["negative_observations"]["count"] == 22
    assert candidate["negative_observations"]["root_sha256"] == _compact_sha256(
        candidate["negative_observations"]["preimage"]
    )
    route_join = candidate["retained_route_join"]
    assert route_join["fresh_observation_count"] == 22
    assert route_join["retained_route_row_count"] == 44
    assert route_join["route_rows_per_observation"] == 2
    assert route_join["status"] == "exact-44-route-rows-joined-two-to-one"
    assert route_join["root_sha256"] == _compact_sha256(route_join["preimage"])

    observation_by_key = {
        (row["theorem_index"], row["attempt_index"]): row for row in observations
    }
    assert len(observation_by_key) == 22
    retained_route_hashes: set[str] = set()
    for join in joins:
        key = (join["theorem_index"], join["attempt_index"])
        observation = observation_by_key[key]
        assert join["fresh_observation_record_sha256"] == observation["record_sha256"]
        assert join["name"] == observation["name"]
        assert join["omitted_dependency"] == observation["omitted_dependency"]
        assert join["retained_message_available"] is False
        assert join["route_row_count"] == 2
        assert {row["route"] for row in join["retained_route_records"]} == ROUTES
        retained_route_hashes.update(
            row["record_sha256"] for row in join["retained_route_records"]
        )
        failure = observation["failure"]
        assert observation["outcome"] == "exact-shared-root-body-rejected"
        assert failure["kind"] == "exact-recipe-rejection"
        assert failure["cause_type"] == "TacticError"
        assert failure["message_source"] == "fresh-a2.3c-lower-level-replay"
        assert failure["retained_message_available"] is False
    assert len(retained_route_hashes) == 44

    offset = 0
    for theorem, baseline, expected in zip(
        candidate["theorems"], baselines, EXPECTED_THEOREMS, strict=True
    ):
        index, name, count = expected
        assert (theorem["index"], theorem["name"], theorem["negative_observation_count"]) == expected
        assert (baseline["theorem_index"], baseline["name"], baseline["dependency_count"]) == expected
        assert theorem["baseline"] == baseline
        assert theorem["negative_observations"] == observations[offset : offset + count]
        assert baseline["status"] == "full-vector-baseline-kernel-accepted"
        assert theorem["negative_observations_independently_verified"] is True
        assert theorem["route_rejections_independently_verified"] is False
        offset += count
    assert offset == 22

    assert (
        verification["format"],
        verification["id"],
        verification["status"],
        verification["candidate_status"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-negative-replay-independent-verification",
        "independent-a2.3c-pilot-vector-negative-replay-structural-verification-v1",
        "passed",
        "passed",
    )
    assert verification["aggregate"] == {
        "full_vector_baseline_count": 3,
        "negative_observation_count": 22,
        "retained_route_pair_count": 22,
        "retained_route_row_count": 44,
        "theorem_count": 3,
    }
    assert verification["candidate"] == {
        "artifact_bytes": len(candidate_raw),
        "artifact_sha256": _sha256(candidate_raw),
        "baseline_records_root_sha256": candidate["baselines"]["root_sha256"],
        "negative_observation_records_root_sha256": candidate["negative_observations"]["root_sha256"],
        "retained_route_join_root_sha256": route_join["root_sha256"],
        "root_sha256": candidate["root_sha256"],
        "theorem_records_root_sha256": candidate["theorem_records"]["root_sha256"],
    }
    assert verification["candidate_negative_observations_structurally_verified"] is True
    assert verification["predecessor_evidence_authenticated"] is True
    assert verification["source_protocol_authenticated"] is True
    assert verification["structural_receipts_verified"] is True
    assert verification["structural_result_verified"] is True
    for field in (
        "execution_receipt_bound",
        "kernel_baselines_independently_reexecuted",
        "negative_observations_independently_verified",
        "negative_replays_independently_reexecuted",
        "route_rejections_independently_verified",
        "tactic_semantics_independently_verified",
    ):
        assert verification[field] is False
    _assert_hashed_records(verification["theorems"])
    assert [
        (row["index"], row["name"], row["negative_observation_count"])
        for row in verification["theorems"]
    ] == list(EXPECTED_THEOREMS)
    protocol_sources = verification["protocol_sources"]
    assert protocol_sources["count"] == 4
    assert protocol_sources["root_sha256"] == _compact_sha256(
        protocol_sources["preimage"]
    )
    for row in protocol_sources["preimage"]["sources"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])
    retained_evidence = verification["retained_evidence"]
    assert retained_evidence["count"] == 8
    assert retained_evidence["root_sha256"] == _compact_sha256(
        retained_evidence["preimage"]
    )
    for row in retained_evidence["preimage"]["evidence"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["artifact_sha256"])
    verifier = verification["verifier"]
    verifier_raw = (ROOT / verifier["path"]).read_bytes()
    assert verifier["tactic_free"] is True
    assert verifier["import_policy"] == "python-standard-library-only-no-peano-or-training-import"
    assert (len(verifier_raw), _sha256(verifier_raw)) == (
        verifier["source_bytes"],
        verifier["sha256"],
    )
    _assert_no_authority(candidate)
    _assert_no_authority(verification)


def test_tactic_free_structural_verifier_replays_byte_identically(
    tmp_path: Path,
) -> None:
    python = (
        sys.executable
        if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12)
        else shutil.which("python3.12")
    )
    if python is None:
        pytest.skip("controlled verifier requires CPython 3.12")
    output = tmp_path / "independent-verification.json"
    environment = {
        "HOME": str(tmp_path),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "2",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23c-disabled-pycache",
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
            "--output",
            str(output),
            "--repository-root",
            str(ROOT),
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stderr == ""
    assert "3 baselines, 22 negative records, 44 retained route labels" in completed.stdout
    assert "no tactic replay or execution binding" in completed.stdout
    assert output.read_bytes() == VERIFICATION_PATH.read_bytes()
    replayed, _ = _load_json(output)
    assert replayed["negative_replays_independently_reexecuted"] is False
    assert replayed["execution_receipt_bound"] is False
    assert replayed["tactic_semantics_independently_verified"] is False


def test_source_and_wmi_receipts_cross_bind_normalized_duplicate_outputs() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)
    git_receipt, git_receipt_raw = _load_json(GIT_RECEIPT_PATH)
    infrastructure, infrastructure_raw = _load_json(INFRASTRUCTURE_PATH)
    execution, execution_raw = _load_json(EXECUTION_PATH)
    collection, _ = _load_json(COLLECTION_PATH)

    assert (source_state["commit_sha1"], source_state["tree_sha1"]) == (COMMIT, TREE)
    assert source_state["git_verified"] is False
    assert _compact_sha256(source_state) == SOURCE_STATE_SEMANTIC_SHA256
    for row in source_state["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])

    provenance = (
        EVIDENCE_ROOT / "inputs" / ".peano-source-provenance.tsv"
    ).read_text(encoding="ascii").removesuffix("\n").split("\t")
    assert provenance == [COMMIT, "false", "2026-08-14T07:39:16Z"]
    assert git_receipt["format"] == "peano-hydra-a23c-replayer-git-verification-receipt"
    assert git_receipt["status"] == "passed"
    assert (git_receipt["commit_sha1"], git_receipt["tree_sha1"]) == (COMMIT, TREE)
    assert git_receipt["source_state_artifact_sha256"] == _sha256(source_state_raw)
    assert git_receipt["source_state_root_sha256"] == source_state["root_sha256"]
    assert git_receipt["source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert len(git_receipt["commands"]) == 22
    assert all(row["exit_code"] == 0 for row in git_receipt["commands"])
    assert all(row["stderr_sha256"] == EMPTY_SHA256 for row in git_receipt["commands"])
    source_rows = {row["path"]: row for row in source_state["files"]}
    assert len(source_rows) == len(git_receipt["source_files"]) == 4
    for row in git_receipt["source_files"]:
        source_row = source_rows[row["path"]]
        assert row["verified"] is True
        assert row["mode"] == "100644"
        assert row["bytes"] == source_row["bytes"]
        assert row["live_sha256"] == row["committed_sha256"] == source_row["sha256"]

    assert infrastructure["format"] == "peano-hydra-a23c-wmi-infrastructure-manifest"
    assert (infrastructure["git_commit"], infrastructure["git_tree"]) == (COMMIT, TREE)
    assert len(infrastructure["files"]) == 11
    for row in infrastructure["files"]:
        path = ROOT / row["path"]
        raw = path.read_bytes()
        assert (len(raw), _sha256(raw)) == (row["bytes"], row["sha256"])
        assert row["mode"] == ("100755" if os.access(path, os.X_OK) else "100644")

    assert execution["format"] == "peano-hydra-a23c-negative-replay-wmi-execution-receipt"
    assert execution["job_id"] == JOB_ID
    assert execution["status"] == "passed"
    assert execution["error"] is None
    assert execution["classification"] == (
        "two-replayer-byte-identity-and-independent-structural-verification"
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
        "pycache_prefix": "/proc/peano-hydra-a23c-disabled-pycache",
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
    assert evidence["replayer_byte_identical"] is True
    assert evidence["replayer_hash_seeds"] == [0, 1]
    assert evidence["evidence_boundary"] == {
        "full_vector_baseline_record_count": 3,
        "independent_negative_observation_count": 22,
        "independent_wrapper_implementation": True,
        "negative_observations_independently_verified": True,
        "replayer_observations_execution_bound": True,
        "retained_route_row_count": 44,
        "route_rejections_independently_verified": False,
        "shared_engine_with_a2.3b": True,
        "structural_receipts_verified": True,
        "tactic_semantics_independently_verified_by_verifier": False,
    }
    assert evidence["candidate"] == {
        "baseline_record_count": 3,
        "bytes": len(candidate_raw),
        "independent_negative_observation_count": 22,
        "negative_observations_independently_verified": True,
        "path": CANDIDATE_PATH.name,
        "replayer_observations_execution_bound": True,
        "replayer_source_state_root_sha256": source_state["root_sha256"],
        "retained_route_row_count": 44,
        "root_sha256": candidate["root_sha256"],
        "sha256": _sha256(candidate_raw),
    }
    assert evidence["verifier"] == {
        "bytes": len(verification_raw),
        "hash_seed": 2,
        "path": VERIFICATION_PATH.name,
        "root_sha256": verification["root_sha256"],
        "sha256": _sha256(verification_raw),
        "status": "passed",
    }

    processes = execution["processes"]
    assert [row["role"] for row in processes] == [
        "replayer-0",
        "replayer-1",
        "independent-verifier",
    ]
    assert [row["hash_seed"] for row in processes] == [0, 1, 2]
    assert all(row["returncode"] == 0 for row in processes)
    assert all(row["timed_out"] is False for row in processes)
    assert all(row["output_limit_reached"] is False for row in processes)
    remote_root = (
        "/work/bnaskrecki/peano-lab-training/tmp/hydra-a23c-negative-replay/"
        f"{SNAPSHOT}"
    )
    remote_run = f"{remote_root}/runs/{JOB_ID}"
    isolated_prefix = [wmi_python, "-B", "-P", "-s", "-S"]
    expected_processes = (
        (
            0,
            360,
            [
                *isolated_prefix,
                "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py",
                "--execute",
                "--confirm",
                "PEANO-HYDRA-A23C-NEGATIVE-REPLAY",
                "--hash-seed",
                "0",
                "--output",
                f"{remote_run}/{CANDIDATE_PATH.name}",
            ],
        ),
        (
            1,
            360,
            [
                *isolated_prefix,
                "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py",
                "--execute",
                "--confirm",
                "PEANO-HYDRA-A23C-NEGATIVE-REPLAY",
                "--hash-seed",
                "1",
                "--output",
                f"{remote_run}/l0-pilot-dependency-vector-negative-replay-candidate-v1-hashseed-1.json",
            ],
        ),
        (
            2,
            90,
            [
                *isolated_prefix,
                "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py",
                "--candidate",
                f"{remote_run}/{CANDIDATE_PATH.name}",
                "--output",
                f"{remote_run}/{VERIFICATION_PATH.name}",
                "--repository-root",
                f"{remote_root}/source",
            ],
        ),
    )
    for process, (seed, timeout, argv) in zip(
        processes, expected_processes, strict=True
    ):
        assert process["argv"] == argv
        assert process["timeout_seconds"] == timeout
        assert process["environment"] == {
            "HOME": "/nonexistent/peano-a23c-wmi",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": str(seed),
            "PYTHONNOUSERSITE": "1",
            "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23c-disabled-pycache",
            "TZ": "UTC",
        }

    # Four large logical files (two candidate outputs and their two stdout
    # mirrors) normalize to the sole retained candidate.  Only their empty
    # stderr logs are retained separately.
    candidate_identity = {
        "bytes": len(candidate_raw),
        "sha256": _sha256(candidate_raw),
    }
    normalized: list[tuple[str, dict[str, object]]] = []
    for process in processes[:2]:
        output_index = process["argv"].index("--output") + 1
        normalized.append((Path(process["argv"][output_index]).name, candidate_identity))
        normalized.append((process["stdout"]["path"], process["stdout"]))
        assert process["stdout"]["bytes"] == candidate_identity["bytes"]
        assert process["stdout"]["sha256"] == candidate_identity["sha256"]
        stderr_path = EVIDENCE_ROOT / "runs" / JOB_ID / process["stderr"]["path"]
        assert process["stderr"] == _record(stderr_path)
    assert len(normalized) == 4
    assert [name for name, _ in normalized] == [
        CANDIDATE_PATH.name,
        "replayer-0.stdout.log",
        "l0-pilot-dependency-vector-negative-replay-candidate-v1-hashseed-1.json",
        "replayer-1.stdout.log",
    ]
    assert not any(
        (EVIDENCE_ROOT / "runs" / JOB_ID / name).exists()
        for name in ("replayer-0.stdout.log", "replayer-1.stdout.log")
    )
    assert not any(EVIDENCE_ROOT.rglob("*hashseed-1.json"))

    verifier_process = processes[2]
    verifier_log_root = EVIDENCE_ROOT / "runs" / JOB_ID
    assert verifier_process["stdout"] == _record(
        verifier_log_root / "independent-verifier.stdout.log"
    )
    assert verifier_process["stderr"] == _record(
        verifier_log_root / "independent-verifier.stderr.log"
    )
    assert (verifier_log_root / "independent-verifier.stdout.log").read_text(
        encoding="utf-8"
    ) == (
        "independent A2.3c structural verification: 3 baselines, "
        "22 negative records, 44 retained route labels; no tactic replay or "
        "execution binding; root "
        "364d4ee4099856c44ee1633439f2e5b1c57ae24cc90d9178cdf7445008504733\n"
    )

    assert collection["format"] == "peano-hydra-a23c-negative-replay-wmi-collection-receipt"
    assert collection["job_id"] == JOB_ID
    assert collection["status"] == "passed"
    assert collection["classification"] == (
        "completed-dual-replayer-and-independent-structural-verification"
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
        "elapsed_raw_seconds": 89,
        "exit_code": "0:0",
        "job_id": JOB_ID,
        "max_rss": "",
        "node_list": "c3n1",
        "raw_bytes": 39,
        "raw_sha256": FILE_PINS["sacct.psv"][1],
        "requested_memory": "4G",
        "state": "COMPLETED",
    }
    assert collection["scheduler_logs"]["stderr"] == {
        **_record(EVIDENCE_ROOT / "logs" / "peano-hydra-a23c-negative-replay-220227.err"),
        "exists": True,
    }
    assert collection["scheduler_logs"]["stdout"] == {
        **_record(EVIDENCE_ROOT / "logs" / "peano-hydra-a23c-negative-replay-220227.out"),
        "exists": True,
    }
    submission_raw = (EVIDENCE_ROOT / "submission.tsv").read_bytes()
    submission_values = submission_raw.decode("ascii").removesuffix("\n").split("\t")
    assert len(submission_values) == 16
    assert submission_values[11:15] == ["1", "1", "4096", "00:15:00"]
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
    assert submission["provenance_sha256"] == source["provenance"]["sha256"]

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
    assert deposit["archive_bytes"] == 282_733_056
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

    sacct_raw = (EVIDENCE_ROOT / "sacct.psv").read_bytes()
    assert sacct_raw == b"220227|COMPLETED|0:0|0:0|89||4G|1|c3n1\n"
    assert collection["submitted_sbatch"] == {
        "bytes": 5_055,
        "path": "peano_wmi_hydra_a23c_negative_replay.sbatch",
        "sha256": "f2b2cd1879147d5dbf234a5dc7cd49aefd92152a0cd1b02bf67c02d6feb4fc29",
    }
    sbatch_raw = (
        ROOT / "slurm" / "peano_wmi_hydra_a23c_negative_replay.sbatch"
    ).read_bytes()
    assert (len(sbatch_raw), _sha256(sbatch_raw)) == (
        collection["submitted_sbatch"]["bytes"],
        collection["submitted_sbatch"]["sha256"],
    )
    _assert_no_authority(execution)
    _assert_no_authority(collection)
    _assert_no_authority(git_receipt)
