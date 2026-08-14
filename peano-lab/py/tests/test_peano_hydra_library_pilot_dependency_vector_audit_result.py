"""Acceptance gate for the retained Hydra A2.3b WMI vector audit.

The producer campaign is deliberately not replayed here.  This gate pins the
complete small retained bundle, reconstructs its structural receipts, and
replays only the corrected independent six-baseline verifier in isolation.
The 44 negative route rows remain producer observations, not independently
reproduced negative proofs.
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
EVIDENCE_ROOT = ARTIFACT_ROOT / "a23b-wmi-vector-audit-220220"
RESULT_ROOT = EVIDENCE_ROOT / "results"
CANDIDATE_PATH = (
    RESULT_ROOT / "l0-pilot-dependency-vector-audit-candidate-v1.json"
)
VERIFICATION_PATH = (
    RESULT_ROOT
    / "l0-pilot-dependency-vector-audit-independent-verification-v1.json"
)
SOURCE_STATE_PATH = EVIDENCE_ROOT / "inputs" / "producer-source-state.json"
GIT_RECEIPT_PATH = (
    EVIDENCE_ROOT / "inputs" / "producer-git-verification-receipt.json"
)
INFRASTRUCTURE_PATH = (
    EVIDENCE_ROOT / "inputs" / "wmi-infrastructure-manifest.json"
)
EXECUTION_PATH = EVIDENCE_ROOT / "runs" / "220220" / "execution-receipt.json"
COLLECTION_PATH = EVIDENCE_ROOT / "collections" / "job-220220.json"
VERIFIER_CLI = (
    ROOT / "scripts/verify_peano_hydra_library_pilot_dependency_vector_audit.py"
)

JOB_ID = "220220"
COMMIT = "720021aec7afff0463ef8dd1180db2702b415301"
TREE = "03383d9b3c5850edfeb8f3401d55116fa4cdd5a2"
SNAPSHOT = "64266e107ee03fe6833af74f7a8d4d5b645886c064f361acd49e416f72c99ae4"
SOURCE_STATE_SEMANTIC_SHA256 = (
    "68657f636ae520af7b3d5b30fdfddfb2911906cbb475694b0b6d7cf4e6319f12"
)
INVENTORY_SHA256 = (
    "e9eec4b239d3f9b870695b51ace1ee8f5667071e52b3d30378ebb056d839476f"
)
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Paths are relative to EVIDENCE_ROOT.  Every retained byte is pinned.  The
# optional third value is the compact-JSON root-preimage digest.
FILE_PINS = {
    "collections/job-220220.json": (
        8_841,
        "d1602e23f7736482b039c3d32537fa012d91302f42d62f75ccab9c11583542a9",
        "9f58b68b2fe811cfa82a25395e53b08c01cdd145b57f234d2cde0ca287cf42e5",
    ),
    "deposit.tsv": (
        438,
        "237ecbc732319b8215faba419fe1fe1692bafbaee907f624c6c205fcc1b18bac",
        None,
    ),
    "inputs/.peano-source-provenance.tsv": (
        68,
        "262147bd951e408cc365455835fed638720bbc9d9152416e6e38eb3e97fa1f35",
        None,
    ),
    "inputs/producer-git-verification-receipt.json": (
        29_092,
        "384392a3a92a1e173576edb415f21f695729cdc71f81bf125afde65fce1041f6",
        "dfaf7d243881041729b8eb278e165046cb37099bcd0e582f2584edbc54c04ad5",
    ),
    "inputs/producer-source-state.json": (
        2_405,
        "ecf037e5d684a7472c2b02c917b5962e87daef02c688967f28b05afd85e339b0",
        "d92e9df55aea87241618fa026ee90730a4fc1b330b8d732030526afc5f501e09",
    ),
    "inputs/wmi-infrastructure-manifest.json": (
        5_714,
        "30b5cd45275d41998fa8398aa710e09d85aba4bea4b050acefdab3992fe90e56",
        "e7fe18588f9b96834681410b881d6aba15645e24bed3521adc9eb45456e320cf",
    ),
    "logs/peano-hydra-a23b-220220.err": (0, EMPTY_SHA256, None),
    "logs/peano-hydra-a23b-220220.out": (
        436,
        "ce56187c8999ea6686c492745d952135bd4067275da002871e2a54f92af4adeb",
        None,
    ),
    "results/l0-pilot-dependency-vector-audit-candidate-v1.json": (
        3_160_729,
        "4f4965508b63d852697c94fe0e7707759b39c5cf456ec2db8aa5a5afe719f2ad",
        "21f4c7a06dd8b1abf01d8eddd8c1942733f0955141ba682d53229078e15d5e85",
    ),
    "results/l0-pilot-dependency-vector-audit-independent-verification-v1.json": (
        16_925,
        "50c207c4de0cabe8a50518da4d20e83925f0e1df29ffd78df05e249ea18d4396",
        "ef0dfac8552789bb4dc0e6694a1704c63a8781a93a1f0d9117c6e5c6babcfbd1",
    ),
    "runs/220220/execution-receipt.json": (
        19_990,
        "dc3cb3d4dc7dae5f842358b1649f131d019742ebeb732d4cad6e92c827b4f318",
        "c010a79955e93b29651557977001f6f6abff7cd63ba7f1fa1b9deb2a5bc3c08b",
    ),
    "runs/220220/independent-verifier.stderr.log": (0, EMPTY_SHA256, None),
    "runs/220220/independent-verifier.stdout.log": (
        199,
        "362508ab461c6ac98795ff1d3faf92fd75881717c417007e8ea527f2b244e31c",
        None,
    ),
    "runs/220220/producer-0.stderr.log": (
        1_482,
        "f49a01eb78638447a5208e98fd550168657f2de3b593a6d0345893b65c83cbce",
        None,
    ),
    "runs/220220/producer-0.stdout.log": (
        128,
        "079f450d7a1c0f042eb8b651b4f9df9f323f87f2684cc3ad7988290af24aecb4",
        None,
    ),
    "runs/220220/producer-1.stderr.log": (
        1_482,
        "f49a01eb78638447a5208e98fd550168657f2de3b593a6d0345893b65c83cbce",
        None,
    ),
    "runs/220220/producer-1.stdout.log": (
        128,
        "079f450d7a1c0f042eb8b651b4f9df9f323f87f2684cc3ad7988290af24aecb4",
        None,
    ),
    "sacct.psv": (
        40,
        "7b98add5fc05e4b3bf1d338136639a971e5b4e1cf244485ff972685b14cff053",
        None,
    ),
    "submission.tsv": (
        553,
        "854c06b97bb43ec33f5679b83394a7762308d989ca9757b820329efbabecb6f2",
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
    "runs/220220",
}
GLOBAL_FALSE_FIELDS = {
    "a2_complete",
    "dependency_vectors_complete",
    "evaluation_eligible",
    "freeze_ready",
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
ROUTES = (
    "readable-direct-closure",
    "proposed-layered-closure-construction",
)
EXPECTED_THEOREMS = (
    (
        256,
        "odd_add_odd",
        ("mul_add", "add_assoc", "add_comm"),
        (
            (
                "8064d28bd99adbaa1cde42c7ebd0f94880b345c889d6afc18e4b607749310ecc",
                13_640,
                2_208,
                6,
                31,
                274,
            ),
            (
                "3fe6ba0a5ab6ca95a159ddb2d8fa44fd674a0eab4376069b3cc2db9f6c3c2962",
                12_709,
                2_168,
                3,
                37,
                269,
            ),
        ),
    ),
    (
        376,
        "finite_bounded_injective_surjective",
        (
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
        (
            (
                "623865d90504af44cddca3d76ac4f009be8aa289e80d2785b72b121a52954504",
                1_870_657,
                330_744,
                1_235,
                89,
                41_341,
            ),
            (
                "af1410f83a9ab66080a80311d9262341f4cbd4b136a64e889b94c7f12fc342e1",
                297_637,
                66_856,
                20,
                95,
                8_355,
            ),
        ),
    ),
    (
        379,
        "beta_product_swap_last_invariant",
        (
            "beta_product_replace_balance",
            "beta_product_succ_decompose",
            "beta_at_unique",
            "le_succ",
            "lt_irrefl_expanded",
        ),
        (
            (
                "507940a3e456122fadb3b43d34891a70c91baa87615be80c1fca059e9ebd82df",
                386_189,
                59_320,
                203,
                67,
                7_413,
            ),
            (
                "fc08873008eea245be7b8b2961e1a00bf659c25dd257785d2e2345ff29fde9a1",
                118_018,
                16_104,
                9,
                79,
                2_011,
            ),
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


def _lf_sha256(values: Iterable[str]) -> str:
    return _sha256("".join(f"{value}\n" for value in values).encode("utf-8"))


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


def _assert_theorem_records(document: dict[str, object], format_: str) -> None:
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
    preimage = {"format": format_, "records": identities, "v": document["v"]}
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
        if key in GLOBAL_FALSE_FIELDS:
            assert item is False, f"forbidden authority field {key!r} is not false"


def _file_record(path: Path, *, retained_name: str | None = None) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.name if retained_name is None else retained_name,
        "sha256": _sha256(raw),
    }


def test_exact_closed_inventory_has_no_snapshot_duplicate_or_symlink() -> None:
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
    assert len(actual_files) == 19
    assert sum(path.stat().st_size for path in actual_files.values()) == 3_248_650
    assert not any(path.is_symlink() for path in EVIDENCE_ROOT.rglob("*"))
    assert all(
        path.is_file() and stat.S_IMODE(path.stat().st_mode) == 0o644
        for path in actual_files.values()
    )

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

    # Results live only inside the closed job bundle.  The second producer's
    # byte-identical candidate and the deposited full source snapshot/archive
    # were intentionally not retained as redundant evidence.
    assert list(ARTIFACT_ROOT.glob("l0-pilot-dependency-vector-audit-*.json")) == []
    assert list(ARTIFACT_ROOT.rglob(CANDIDATE_PATH.name)) == [CANDIDATE_PATH]
    assert list(ARTIFACT_ROOT.rglob(VERIFICATION_PATH.name)) == [VERIFICATION_PATH]
    assert not list(EVIDENCE_ROOT.rglob("candidate-hashseed-*.json"))
    assert not list(EVIDENCE_ROOT.rglob("independent-verifier-receipt.json"))
    assert not (EVIDENCE_ROOT / "source").exists()
    assert not any(path.name == SNAPSHOT for path in EVIDENCE_ROOT.rglob("*"))
    assert not any(
        path.name.endswith((".tar", ".tar.gz", ".tgz", ".zip"))
        for path in EVIDENCE_ROOT.rglob("*")
    )


def test_candidate_and_verifier_preserve_the_44_route_22_shared_boundary() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)

    _assert_theorem_records(
        candidate,
        "peano-hydra-library-pilot-dependency-vector-audit-records-preimage",
    )
    _assert_theorem_records(
        verification,
        "peano-hydra-library-pilot-dependency-vector-audit-verification-"
        "records-preimage",
    )
    assert candidate["theorem_records"]["root_sha256"] == (
        "6a90eee2d8a306e41b944735940044b142cf1c4f02441133c25c94111e11d336"
    )
    assert verification["theorem_records"]["root_sha256"] == (
        "87bef2a0d30c789424a15bb257e1bc743f74f4bfa27fb899ab59a44f4d522585"
    )

    assert (
        candidate["format"],
        candidate["id"],
        candidate["v"],
        candidate["status"],
        candidate["logic_mode"],
        candidate["theorem_count"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-audit",
        "authoring-l0-pilot-dependency-vector-audit-candidate-v1",
        1,
        "candidate",
        "intuitionistic",
        3,
    )
    assert candidate["aggregate"] == {
        "bounded_local_union_edges": 22,
        "kernel_accepted_baseline_count": 6,
        "pilot_theorem_count": 3,
        "retained_public_graph_edges": 1038,
        "route_count": 2,
        "single_omission_attempt_count": 44,
        "single_omission_kernel_accepted_count": 0,
        "single_omission_rejected_count": 44,
        "single_omission_terminal_count": 44,
    }
    assert candidate["bounded_protocol_executed"] is True
    assert candidate["bounded_three_root_protocol_frozen"] is True
    assert candidate["terminal_route_observations_complete"] is True
    assert candidate["single_omission_terminal_count"] == 44
    assert candidate["bounded_three_root_vector_audit_complete"] is False
    assert candidate["producer_source_state"] == source_state
    assert candidate["producer_source_state_sha256"] == _compact_sha256(source_state)
    assert candidate["producer_source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert source_state["git_verified"] is False
    assert (source_state["commit_sha1"], source_state["tree_sha1"]) == (COMMIT, TREE)

    schema_path = (
        ROOT
        / "training/peano_hydra/library-pilot-dependency-vector-audit-schema-v1.json"
    )
    schema, schema_raw = _load_json(schema_path)
    assert candidate["schema"] == {
        "artifact_sha256": _sha256(schema_raw),
        "format": schema["format"],
        "id": schema["id"],
        "sha256": _compact_sha256(schema),
        "v": schema["v"],
    }
    implementation = candidate["implementation"]
    assert implementation["source_root_sha256"] == (
        "4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0"
    )
    for row in implementation["sources"]:
        assert _sha256((ROOT / row["path"]).read_bytes()) == row["sha256"]
    callable_identity = implementation["callable_limits_identity"]
    assert callable_identity["sha256"] == _compact_sha256(callable_identity["preimage"])
    assert callable_identity["preimage"]["expected_attempt_count"] == 44
    transport = implementation["live_theorem_transport"]
    assert transport["count"] == 384
    assert transport["root_sha256"] == _compact_sha256(transport["preimage"])

    for key, binding in candidate["inputs"].items():
        if key == "replay":
            manifest_path = ROOT / binding["manifest_artifact_path"]
            report_path = ROOT / binding["replay_report_artifact_path"]
            manifest, manifest_raw = _load_json(manifest_path)
            report, report_raw = _load_json(report_path)
            assert _sha256(manifest_raw) == binding["manifest_artifact_sha256"]
            assert manifest["root_sha256"] == binding["manifest_root_sha256"]
            assert _sha256(report_raw) == binding["replay_report_artifact_sha256"]
            assert report["replay_root_sha256"] == binding["replay_root_sha256"]
            continue
        input_path = ROOT / binding["artifact_path"]
        input_document, input_raw = _load_json(input_path)
        assert _sha256(input_raw) == binding["artifact_sha256"]
        assert input_document["root_sha256"] == binding["root_sha256"]
        assert input_document["theorem_records"]["root_sha256"] == binding[
            "theorem_record_root_sha256"
        ]

    assert (
        verification["format"],
        verification["id"],
        verification["v"],
        verification["status"],
        verification["candidate_status"],
        verification["logic_mode"],
        verification["theorem_count"],
    ) == (
        "peano-hydra-library-pilot-dependency-vector-audit-verification",
        "independent-a2.3b-pilot-dependency-vector-audit-verification-v1",
        1,
        "passed",
        "candidate",
        "intuitionistic",
        3,
    )
    assert verification["aggregate"] == {
        "baseline_artifact_count": 6,
        "kernel_accepted_baseline_artifact_count": 6,
        "pilot_theorem_count": 3,
        "producer_observation_route_record_count": 44,
        "unique_shared_root_body_observation_count": 22,
    }
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
    assert verification["kernel_baseline_artifacts_verified"] is True
    assert verification["producer_observations_structurally_verified"] is True
    assert verification["structural_receipts_verified"] is True
    for field in (
        "bounded_three_root_vector_audit_complete",
        "negative_observations_independently_verified",
        "producer_git_verified",
        "producer_observations_execution_bound",
        "route_rejections_independently_verified",
    ):
        assert verification[field] is False
    verifier = verification["verifier"]
    assert verifier["load_mode"] == "direct-source-module-without-training-package-init"
    assert verifier["import_policy"] == "stdlib-and-peano-kernel-only"
    assert verifier["pycache_prefix"] == "/proc/peano-hydra-a23b-disabled-pycache"
    assert _sha256((ROOT / verifier["path"]).read_bytes()) == verifier["sha256"]
    for row in verifier["kernel_sources"]:
        assert _sha256((ROOT / row["path"]).read_bytes()) == row["sha256"]

    route_record_count = 0
    all_shared_observations: set[str] = set()
    for candidate_row, verified_row, expected in zip(
        candidate["theorems"],
        verification["theorems"],
        EXPECTED_THEOREMS,
        strict=True,
    ):
        index, name, dependencies_tuple, baseline_expectations = expected
        dependencies = list(dependencies_tuple)
        assert (candidate_row["index"], candidate_row["name"]) == (index, name)
        assert (verified_row["index"], verified_row["name"]) == (index, name)
        assert verified_row["candidate_record_sha256"] == candidate_row["record_sha256"]
        local_union = candidate_row["bounded_local_union"]
        assert local_union["dependencies"] == dependencies
        assert local_union["dependency_count"] == len(dependencies)
        assert local_union["root_sha256"] == _compact_sha256(
            local_union["preimage"]
        )
        assert local_union["preimage"]["readable_dependencies"] == dependencies
        assert local_union["preimage"]["proposed_layered_dependencies"] == dependencies
        assert local_union["scope"] == (
            "bounded-pilot-root-only-not-publication-verified"
        )

        theorem_attempt_count = 2 * len(dependencies)
        assert candidate_row["bounded_protocol_executed"] is True
        assert candidate_row["terminal_route_observations_complete"] is True
        assert candidate_row["bounded_three_root_vector_audit_complete"] is False
        assert candidate_row["single_omission_attempt_count"] == theorem_attempt_count
        assert candidate_row["single_omission_rejected_count"] == theorem_attempt_count
        assert candidate_row["single_omission_kernel_accepted_count"] == 0
        assert candidate_row["single_omission_terminal_count"] == theorem_attempt_count
        assert (
            verified_row["producer_observation_route_record_count"]
            == theorem_attempt_count
        )
        assert verified_row["unique_shared_root_body_observation_count"] == len(
            dependencies
        )

        assert [row["route"] for row in candidate_row["routes"]] == list(ROUTES)
        paired_attempts = []
        baseline_root_receipt = None
        for route_index, (route_row, verified_baseline, baseline_expected) in enumerate(
            zip(
                candidate_row["routes"],
                verified_row["baseline_artifacts"],
                baseline_expectations,
                strict=True,
            )
        ):
            route = ROUTES[route_index]
            artifact_sha, artifact_bytes, fuel, cuts, depth, nodes = baseline_expected
            assert route_row["status"] == "bounded-route-audit-complete"
            assert route_row["route_receipt_sha256"] == _compact_sha256(
                route_row["route_receipt_preimage"]
            )
            baseline = route_row["baseline"]
            assert baseline["status"] == "kernel-accepted-baseline"
            assert baseline["sha256"] == _compact_sha256(baseline["preimage"])
            assert baseline["preimage"] == {
                "diagnostics": baseline["diagnostics"],
                "format": (
                    "peano-hydra-library-pilot-dependency-vector-audit-"
                    "baseline-preimage"
                ),
                "index": index,
                "name": name,
                "proof": baseline["proof"],
                "route": route,
                "surface": baseline["surface"],
                "v": 1,
            }
            assert baseline["proof"]["kernel_accepted"] is True
            assert baseline["proof"]["kernel_context"] == "empty"
            assert baseline["proof"]["logic_mode"] == "intuitionistic"
            assert baseline["proof"]["formula_sha256"] == candidate_row["statement"][
                "formula_sha256"
            ]
            assert baseline["proof"]["metrics"] == {
                "cut_nodes": cuts,
                "proof_depth": depth,
                "proof_nodes": nodes,
            }
            surface = baseline["surface"]
            assert surface["direct_dependencies"] == dependencies
            assert surface["direct_dependency_count"] == len(dependencies)
            assert surface["direct_dependencies_lf_sha256"] == _lf_sha256(dependencies)
            assert surface["transitive_closure_lf_sha256"] == _lf_sha256(
                surface["transitive_closure_dependencies_in_replay_order"]
            )

            root_body_receipt = baseline["diagnostics"]["root_body_receipt"]
            if baseline_root_receipt is None:
                baseline_root_receipt = root_body_receipt
            else:
                assert root_body_receipt == baseline_root_receipt
            assert (
                route_row["route_receipt_preimage"]["baseline_receipt_sha256"]
                == baseline["sha256"]
            )
            assert route_row["route_receipt_preimage"][
                "producer_source_state_root_sha256"
            ] == source_state["root_sha256"]

            assert verified_baseline["route"] == route
            assert verified_baseline["source"] == (
                "fixed-a2.2-embedded-artifact"
                if route_index == 0
                else "fixed-a2.3a-embedded-artifact"
            )
            assert verified_baseline["artifact_sha256"] == artifact_sha
            assert verified_baseline["fuel"] == fuel
            assert verified_baseline["metrics"] == {
                "artifact_bytes": artifact_bytes,
                "cut_nodes": cuts,
                "proof_depth": depth,
                "proof_nodes": nodes,
            }
            assert verified_baseline["kernel_accepted"] is True
            assert verified_baseline["formula_sha256"] == baseline["proof"][
                "formula_sha256"
            ]
            assert verified_baseline["proof_term_sha256"] == baseline["proof"][
                "proof_term_sha256"
            ]

            attempts = route_row["attempts"]
            assert len(attempts) == len(dependencies)
            assert [row["omitted_dependency"] for row in attempts] == list(
                reversed(dependencies)
            )
            identities = []
            for attempt_index, attempt in enumerate(attempts):
                omitted = dependencies[-1 - attempt_index]
                attempted = [item for item in dependencies if item != omitted]
                assert attempt["attempt_index"] == attempt_index
                assert attempt["omitted_dependency"] == omitted
                assert attempt["attempted_dependencies"] == attempted
                assert attempt["before_dependencies"] == dependencies
                assert attempt["after_dependencies"] == dependencies
                assert attempt["route"] == route
                assert attempt["outcome"] == "exact-route-rejected"
                assert attempt["terminal_stage"] == "root-body-regeneration"
                assert attempt["route_specific_assembly_reached"] is False
                assert attempt["layered_compiler_invoked"] is False
                assert attempt["failure"]["kind"] == "exact-recipe-rejection"
                assert attempt["failure"]["phase"] == "command"
                assert attempt["failure"]["cause_type"] == "TacticError"
                assert attempt["baseline_formula_sha256"] == baseline["proof"][
                    "formula_sha256"
                ]
                assert attempt["baseline_root_body_certificate_sha256"] == (
                    root_body_receipt["certificate_sha256"]
                )
                trial = attempt["trial_surface"]
                assert trial["direct_dependencies"] == attempted
                assert trial["direct_dependency_count"] == len(attempted)
                assert trial["direct_dependencies_lf_sha256"] == _lf_sha256(attempted)
                assert trial["transitive_closure_lf_sha256"] == _lf_sha256(
                    trial["transitive_closure_dependencies_in_replay_order"]
                )
                shared_preimage = attempt["shared_root_body_observation_preimage"]
                assert shared_preimage["dependencies"] == attempted
                assert shared_preimage["failure"] == attempt["failure"]
                assert attempt[
                    "shared_root_body_observation_sha256"
                ] == _compact_sha256(shared_preimage)
                body = {
                    key: item for key, item in attempt.items() if key != "record_sha256"
                }
                assert attempt["record_sha256"] == _compact_sha256(body)
                identities.append(
                    {
                        "attempt_index": attempt_index,
                        "omitted_dependency": omitted,
                        "record_sha256": attempt["record_sha256"],
                    }
                )
            attempt_preimage = {
                "format": (
                    "peano-hydra-library-pilot-dependency-vector-audit-"
                    "attempts-preimage"
                ),
                "name": name,
                "records": identities,
                "route": route,
                "v": 1,
            }
            assert route_row["attempt_records"] == {
                "count": len(attempts),
                "preimage": attempt_preimage,
                "root_sha256": _compact_sha256(attempt_preimage),
            }
            paired_attempts.append(attempts)

        readable_attempts, layered_attempts = paired_attempts
        theorem_shared: set[str] = set()
        for readable, layered in zip(readable_attempts, layered_attempts, strict=True):
            for key in (
                "attempt_index",
                "omitted_dependency",
                "attempted_dependencies",
                "failure",
                "shared_root_body_observation_preimage",
                "shared_root_body_observation_sha256",
            ):
                assert readable[key] == layered[key]
            theorem_shared.add(readable["shared_root_body_observation_sha256"])
        assert len(theorem_shared) == len(dependencies)
        assert not all_shared_observations.intersection(theorem_shared)
        all_shared_observations.update(theorem_shared)
        shared_preimage = {
            "format": "peano-hydra-cross-route-shared-baseline-body-preimage",
            "root_body_receipt": baseline_root_receipt,
            "v": 1,
        }
        assert candidate_row["shared_body_consistency"] == {
            "baseline_root_body_receipt_sha256": _compact_sha256(shared_preimage),
            "paired_attempt_count": len(dependencies),
            "status": "shared-root-body-consistent",
        }
        route_record_count += theorem_attempt_count

    assert route_record_count == 44
    assert len(all_shared_observations) == 22
    assert len(verification_raw) == FILE_PINS[
        "results/l0-pilot-dependency-vector-audit-independent-verification-v1.json"
    ][0]
    _assert_no_authority(candidate)
    _assert_no_authority(verification)


def test_corrected_independent_verifier_replays_byte_identically(
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
        "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23b-disabled-pycache",
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
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stderr == ""
    assert "6 kernel-accepted baseline artifacts" in completed.stdout
    assert "44 routed producer observations/22 shared inputs" in completed.stdout
    assert output.read_bytes() == VERIFICATION_PATH.read_bytes()
    replayed, _ = _load_json(output)
    assert replayed["negative_observations_independently_verified"] is False
    assert replayed["route_rejections_independently_verified"] is False
    assert replayed["producer_observations_execution_bound"] is False


def test_source_git_infrastructure_and_wmi_receipts_cross_bind_every_log() -> None:
    candidate, candidate_raw = _load_json(CANDIDATE_PATH)
    verification, verification_raw = _load_json(VERIFICATION_PATH)
    source_state, source_state_raw = _load_json(SOURCE_STATE_PATH)
    git_receipt, git_receipt_raw = _load_json(GIT_RECEIPT_PATH)
    infrastructure, infrastructure_raw = _load_json(INFRASTRUCTURE_PATH)
    execution, execution_raw = _load_json(EXECUTION_PATH)
    collection, _collection_raw = _load_json(COLLECTION_PATH)

    assert source_state["files"]
    for row in source_state["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert _sha256(raw) == row["sha256"]
    assert source_state["root_sha256"] == (
        "d92e9df55aea87241618fa026ee90730a4fc1b330b8d732030526afc5f501e09"
    )

    provenance_path = EVIDENCE_ROOT / "inputs" / ".peano-source-provenance.tsv"
    provenance_raw = provenance_path.read_bytes()
    provenance = provenance_raw.decode("ascii").removesuffix("\n").split("\t")
    assert provenance == [COMMIT, "false", "2026-08-14T03:45:32Z"]

    assert git_receipt["format"] == "peano-hydra-a23b-producer-git-verification-receipt"
    assert git_receipt["status"] == "passed"
    assert git_receipt["commit_sha1"] == source_state["commit_sha1"] == COMMIT
    assert git_receipt["tree_sha1"] == source_state["tree_sha1"] == TREE
    assert git_receipt["source_state_artifact_sha256"] == _sha256(source_state_raw)
    assert git_receipt["source_state_root_sha256"] == source_state["root_sha256"]
    assert git_receipt["source_state_sha256"] == _compact_sha256(source_state)
    assert git_receipt["source_state_sha256"] == SOURCE_STATE_SEMANTIC_SHA256
    assert len(git_receipt["commands"]) == 22
    assert all(command["exit_code"] == 0 for command in git_receipt["commands"])
    assert all(command["stderr_bytes"] == 0 for command in git_receipt["commands"])
    assert all(
        command["stderr_sha256"] == EMPTY_SHA256
        for command in git_receipt["commands"]
    )
    source_rows = {row["path"]: row for row in source_state["files"]}
    assert len(git_receipt["source_files"]) == len(source_rows) == 4
    for row in git_receipt["source_files"]:
        source_row = source_rows[row["path"]]
        assert row["mode"] == "100644"
        assert row["verified"] is True
        assert row["bytes"] == source_row["bytes"]
        assert row["live_sha256"] == row["committed_sha256"] == source_row["sha256"]
    generator = git_receipt["generator"]
    generator_raw = (ROOT / generator["path"]).read_bytes()
    assert generator["verified"] is True
    assert generator["mode"] == "100644"
    assert generator["bytes"] == len(generator_raw)
    assert generator["live_sha256"] == generator["committed_sha256"] == _sha256(
        generator_raw
    )
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
    assert (
        verification_facts["head_before"]
        == verification_facts["head_after"]
        == COMMIT
    )
    assert (
        verification_facts["tree_before"]
        == verification_facts["tree_after"]
        == TREE
    )
    assert verification_facts["porcelain_before_bytes"] == 0
    assert verification_facts["porcelain_after_bytes"] == 0
    assert verification_facts["porcelain_before_sha256"] == EMPTY_SHA256
    assert verification_facts["porcelain_after_sha256"] == EMPTY_SHA256

    assert infrastructure["format"] == "peano-hydra-a23b-wmi-infrastructure-manifest"
    assert infrastructure["git_commit"] == COMMIT
    assert infrastructure["git_tree"] == TREE
    assert len(infrastructure["files"]) == 11
    for row in infrastructure["files"]:
        path = ROOT / row["path"]
        raw = path.read_bytes()
        assert len(raw) == row["bytes"]
        assert _sha256(raw) == row["sha256"]
        expected_mode = "100755" if os.access(path, os.X_OK) else "100644"
        assert row["mode"] == expected_mode

    assert execution["format"] == "peano-hydra-a23b-wmi-execution-receipt"
    assert execution["job_id"] == JOB_ID
    assert execution["status"] == "passed"
    assert execution["error"] is None
    assert execution["classification"] == (
        "two-producer-byte-identity-and-independent-baseline-verification"
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
    wmi_python = "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
    assert execution["runtime"] == {
        "dont_write_bytecode": True,
        "executable": wmi_python,
        "implementation": "CPython",
        "machine": "x86_64",
        "no_site": True,
        "optimize": 0,
        "pycache_prefix": "/proc/peano-hydra-a23b-disabled-pycache",
        "python_version": "3.12.12",
        "safe_path": True,
        "user_site_disabled": True,
    }
    evidence = execution["evidence"]
    assert evidence["producer_byte_identical"] is True
    assert evidence["producer_hash_seeds"] == [0, 1]
    assert evidence["candidate"] == {
        "baseline_artifact_count": 6,
        "bytes": len(candidate_raw),
        "negative_observations_independently_verified": False,
        "path": "candidate-hashseed-0.json",
        "producer_observations_execution_bound": True,
        "root_sha256": candidate["root_sha256"],
        "route_negative_record_count": 44,
        "sha256": _sha256(candidate_raw),
        "unique_shared_root_body_observation_count": 22,
    }
    assert evidence["evidence_boundary"] == {
        "independently_verified_baseline_count": 6,
        "kernel_baseline_artifacts_verified": True,
        "negative_observations_independently_verified": False,
        "producer_negative_route_record_count": 44,
        "producer_observations_execution_bound": True,
        "producer_observations_structurally_verified": True,
        "route_rejections_independently_verified": False,
        "structural_receipts_verified": True,
        "unique_shared_root_body_observation_count": 22,
    }
    assert evidence["verifier"] == {
        "bytes": len(verification_raw),
        "hash_seed": 2,
        "path": "independent-verifier-receipt.json",
        "root_sha256": verification["root_sha256"],
        "sha256": _sha256(verification_raw),
        "status": "passed",
    }
    # The WMI wrapper binds the producer observations to this execution, while
    # the independent receipt correctly makes no such standalone claim.
    assert (
        evidence["evidence_boundary"]["producer_observations_execution_bound"]
        is True
    )
    assert verification["producer_observations_execution_bound"] is False
    assert verification["negative_observations_independently_verified"] is False
    assert verification["route_rejections_independently_verified"] is False

    remote_root = (
        "/work/bnaskrecki/peano-lab-training/tmp/hydra-a23b-vector-audit/"
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
            116_851,
            [
                *isolated_prefix,
                "scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py",
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
            116_091,
            [
                *isolated_prefix,
                "scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py",
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
            3_579,
            [
                *isolated_prefix,
                "scripts/verify_peano_hydra_library_pilot_dependency_vector_audit.py",
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
    for process, (role, seed, timeout, duration, expected_argv) in zip(
        execution["processes"], expected_processes, strict=True
    ):
        assert process["role"] == role
        assert process["hash_seed"] == seed
        assert process["duration_seconds_millis"] == duration
        assert process["environment"] == {
            "HOME": "/nonexistent/peano-a23b-wmi",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": str(seed),
            "PYTHONNOUSERSITE": "1",
            "PYTHONPYCACHEPREFIX": "/proc/peano-hydra-a23b-disabled-pycache",
            "TZ": "UTC",
        }
        assert process["returncode"] == 0
        assert process["timed_out"] is False
        assert process["output_limit_reached"] is False
        assert process["timeout_seconds"] == timeout
        assert process["argv"] == expected_argv
        assert process["stdout"] == _file_record(run_root / f"{role}.stdout.log")
        assert process["stderr"] == _file_record(run_root / f"{role}.stderr.log")

    assert (run_root / "producer-0.stdout.log").read_bytes() == (
        run_root / "producer-1.stdout.log"
    ).read_bytes()
    assert (run_root / "producer-0.stderr.log").read_bytes() == (
        run_root / "producer-1.stderr.log"
    ).read_bytes()
    assert (run_root / "independent-verifier.stderr.log").read_bytes() == b""
    assert (run_root / "independent-verifier.stdout.log").read_text(
        encoding="utf-8"
    ) == (
        "independent A2.3b verification: 3 roots, 6 kernel-accepted baseline "
        "artifacts, 44 routed producer observations/22 shared inputs, root "
        f"{verification['root_sha256']}\n"
    )

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
        "cpus_per_task": int(submission_values[11]),
        "git_commit": submission_values[3],
        "git_receipt_sha256": submission_values[6],
        "git_tree": submission_values[4],
        "infrastructure_sha256": submission_values[7],
        "job_id": submission_values[1],
        "memory_mib": int(submission_values[13]),
        "ntasks": int(submission_values[12]),
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
    assert deposit["archive_bytes"] == 278_735_872
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
    assert sacct_raw == b"220220|COMPLETED|0:0|0:0|237||4G|1|c3n1\n"
    assert collection["accounting"] == {
        "allocated_cpus": 1,
        "derived_exit_code": "0:0",
        "elapsed_raw_seconds": 237,
        "exit_code": "0:0",
        "job_id": JOB_ID,
        "max_rss": "",
        "node_list": "c3n1",
        "raw_bytes": len(sacct_raw),
        "raw_sha256": _sha256(sacct_raw),
        "requested_memory": "4G",
        "state": "COMPLETED",
    }
    assert collection["format"] == "peano-hydra-a23b-wmi-collection-receipt"
    assert collection["job_id"] == JOB_ID
    assert collection["status"] == "passed"
    assert collection["classification"] == (
        "completed-dual-producer-and-independent-baselines-verified"
    )
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
    scheduler_stdout = EVIDENCE_ROOT / "logs" / "peano-hydra-a23b-220220.out"
    scheduler_stderr = EVIDENCE_ROOT / "logs" / "peano-hydra-a23b-220220.err"
    assert scheduler_logs["stdout"] == {
        **_file_record(scheduler_stdout),
        "exists": True,
    }
    assert scheduler_logs["stderr"] == {
        **_file_record(scheduler_stderr),
        "exists": True,
    }
    assert scheduler_stderr.read_bytes() == b""
    scheduler_text = scheduler_stdout.read_text(encoding="utf-8")
    assert (
        f"status=passed receipt={remote_run}/execution-receipt.json"
        in scheduler_text
    )
    assert _sha256(execution_raw) in scheduler_text
    sbatch = ROOT / "slurm" / "peano_wmi_hydra_a23b_vector_audit.sbatch"
    assert collection["submitted_sbatch"] == _file_record(sbatch)
    assert collection["submitted_sbatch"]["sha256"] == submission["sbatch_sha256"]

    _assert_no_authority(git_receipt)
    _assert_no_authority(execution)
    _assert_no_authority(collection)
