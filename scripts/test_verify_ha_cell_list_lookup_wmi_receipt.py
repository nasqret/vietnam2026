"""Lightweight verifier for the sealed K3B lookup-prefix WMI receipt.

This audit reads the frozen JSON artifact and reconstructs only the private
candidate surface.  It does not parse tactics, replay public theorems, or build
any certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (  # noqa: E402
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)


ARTIFACT_PATH = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-library"
    / "ha-k3b-listat-prefix-closure-219209.json"
)
ARTIFACT_BYTES = 1_333
ARTIFACT_SHA256 = (
    "0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560"
)
TARGET_NAME = "cell_history_extend_preserves_prefix"
EXPECTED_PROVENANCE = {
    "local_commit": "94cf88912bf368d43a3201abc91c69ddeb442a56",
    "local_dirty": False,
    "payload_sha256": (
        "b288d4641680f48c1b145251209bedeb5b82d7ffab40b356a1a2497fef041c74"
    ),
}
EXPECTED_ENVIRONMENT = {
    "python_executable": (
        "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
    ),
    "python_implementation": "CPython",
    "python_version": "3.12.12",
    "pythonhashseed": "20260804",
}
EXPECTED_RESOURCES = {
    "cpus_per_task": 1,
    "memory_mib": 32_768,
    "nodes": 1,
    "ntasks": 1,
    "partition": "cpu_idle",
    "time_limit": "04:00:00",
    "time_limit_seconds": 14_400,
}
EXPECTED_RESULT = {
    "cuts": 241,
    "dependency_closure_count": 104,
    "dependency_closure_sha256": (
        "110e39250834964ec050e5778f09af31fdeb02a6e7e9198c1afa5c9c1393f0ae"
    ),
    "direct_dependencies": [
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
        "zero_le",
        "succ_le_succ",
        "le_refl",
    ],
    "dne_objects": 0,
    "proof_dag_sha256": (
        "7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498"
    ),
    "proof_depth": 81,
    "proof_edges": 4_896,
    "proof_nodes": 29_369,
    "proof_objects": 4_668,
    "reused_objects": 229,
    "statement_characters": 3_799,
    "statement_sha256": (
        "3191deb1ef7c06755622ef9f277b3d5d1e358edac5437e5e337c9f29c6e395b2"
    ),
}


@dataclass(frozen=True)
class _SurfaceSpec:
    name: str
    statement: str
    dependencies: tuple[str, ...]
    script: tuple[str, ...]
    summary: str


def test_lookup_prefix_wmi_receipt_is_exact_and_surface_bound() -> None:
    encoded = ARTIFACT_PATH.read_bytes()
    assert len(encoded) == ARTIFACT_BYTES
    assert sha256(encoded).hexdigest() == ARTIFACT_SHA256
    assert encoded.endswith(b"\n")
    receipt = json.loads(encoded)

    assert set(receipt) == {
        "deterministic_across_passes",
        "environment",
        "format",
        "passes",
        "provenance",
        "requested_resources",
        "results",
        "schema_version",
        "selected_theorems",
        "status",
    }
    assert receipt["format"] == "peano-k3b-cell-history-cold-closure-v2"
    assert receipt["schema_version"] == 1
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["environment"] == EXPECTED_ENVIRONMENT
    assert receipt["provenance"] == EXPECTED_PROVENANCE
    assert receipt["requested_resources"] == EXPECTED_RESOURCES
    assert receipt["selected_theorems"] == [TARGET_NAME]
    assert receipt["results"] == {TARGET_NAME: EXPECTED_RESULT}

    (surface,) = make_ha_cell_history_prefix_preservation_candidate_theorems(
        _SurfaceSpec
    )
    assert surface.name == TARGET_NAME
    assert list(surface.dependencies) == EXPECTED_RESULT["direct_dependencies"]
    assert len(surface.statement) == EXPECTED_RESULT["statement_characters"]
    assert sha256(surface.statement.encode()).hexdigest() == (
        EXPECTED_RESULT["statement_sha256"]
    )

    assert EXPECTED_RESULT["dne_objects"] == 0
    assert EXPECTED_RESULT["proof_nodes"] <= 500_000
    assert EXPECTED_RESULT["proof_objects"] <= 100_000
    assert EXPECTED_RESULT["proof_depth"] <= 256
