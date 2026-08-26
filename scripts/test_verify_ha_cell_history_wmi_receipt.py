"""Lightweight verifier for the sealed K3B CellHistory WMI receipt.

This audit reads one frozen JSON artifact and reconstructs only the private
theorem *surfaces*.  It never parses or executes a tactic script, replays a
public theorem, builds a certificate, or performs recursive cold closure.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.library.ha_cell_history_candidate import (  # noqa: E402
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (  # noqa: E402
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_bound_candidate import (  # noqa: E402
    make_ha_cell_list_length_bound_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_functional_candidate import (  # noqa: E402
    make_ha_cell_list_length_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_total_candidate import (  # noqa: E402
    make_ha_cell_list_length_total_candidate_theorems,
)


ARTIFACT_PATH = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-library"
    / "ha-k3b-cell-history-closure-219203.json"
)
ARTIFACT_BYTES = 5_371
ARTIFACT_SHA256 = (
    "6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c"
)

TARGET_NAMES = (
    "cell_history_nil",
    "cell_history_extend",
    "cell_history_succ_elim",
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "cell_list_length_functional",
    "cell_list_length_le_code",
    "cell_list_length_total",
)

EXPECTED_PROVENANCE = {
    "local_commit": "0b33b6675481a93d0e330987b22d9ef91564a0a0",
    "local_dirty": False,
    "payload_sha256": (
        "edf77bff5cf824cbfd549179f8cef2a18ac65904d473ce3bbd2bd5e5f1c95620"
    ),
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
EXPECTED_ENVIRONMENT = {
    "python_executable": (
        "/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python"
    ),
    "python_implementation": "CPython",
    "python_version": "3.12.12",
    "pythonhashseed": "20260804",
}

# These are the exact empty-context proof receipts produced by both cold WMI
# passes.  Keeping every field here makes metric or dependency drift visible
# even when the artifact's whole-file seal is deliberately updated later.
EXPECTED_RESULTS = {
    "cell_history_nil": {
        "cuts": 2,
        "dependency_closure_count": 3,
        "dependency_closure_sha256": (
            "7d8b7043771bbd2985b5b3ddf5d5b8c0b9107935f4e67c8f04785b41adc9c082"
        ),
        "direct_dependencies": ["add_eq_zero_right", "succ_ne_zero"],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8"
        ),
        "proof_depth": 18,
        "proof_edges": 154,
        "proof_nodes": 155,
        "proof_objects": 155,
        "reused_objects": 0,
        "statement_characters": 1_468,
        "statement_sha256": (
            "18568ecbb4bcc3f923c504be74f4933a2b4f79e5d21751a1791715449374de37"
        ),
    },
    "cell_history_extend": {
        "cuts": 241,
        "dependency_closure_count": 104,
        "dependency_closure_sha256": (
            "edaf4867a4020c7f126ededec296002e58a6d74a7ba2c18d34a6d8f269c93a42"
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
            "370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78"
        ),
        "proof_depth": 81,
        "proof_edges": 4_879,
        "proof_nodes": 29_352,
        "proof_objects": 4_651,
        "reused_objects": 229,
        "statement_characters": 3_153,
        "statement_sha256": (
            "50e26cefb18371aed02b5c926757bbfc22a007a51b995aafd3675c9a960bf407"
        ),
    },
    "cell_history_succ_elim": {
        "cuts": 27,
        "dependency_closure_count": 19,
        "dependency_closure_sha256": (
            "12d3154a380cdcbdbfd7b624fecc3251f165dc2bc84e4c997147874de1af3540"
        ),
        "direct_dependencies": ["beta_at_unique", "le_refl", "le_succ"],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c"
        ),
        "proof_depth": 60,
        "proof_edges": 810,
        "proof_nodes": 1_245,
        "proof_objects": 772,
        "reused_objects": 39,
        "statement_characters": 3_365,
        "statement_sha256": (
            "2f44b8405bb60e1571452cdae993c024c80cb079be6ded25edd58716888ecdee"
        ),
    },
    "cell_list_zero_iff_nil": {
        "cuts": 26,
        "dependency_closure_count": 20,
        "dependency_closure_sha256": (
            "6f19bddab05bd3991e969c97e802f9efa67e035b9293463e4cb3e6483d28b751"
        ),
        "direct_dependencies": ["beta_at_unique", "cell_history_nil"],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73"
        ),
        "proof_depth": 60,
        "proof_edges": 916,
        "proof_nodes": 1_309,
        "proof_objects": 880,
        "reused_objects": 37,
        "statement_characters": 4_332,
        "statement_sha256": (
            "bef9e900318713718a2e981eb04de28fb21e4641ff4f80c2a98b1dc41af2db29"
        ),
    },
    "cell_list_succ_iff_cell": {
        "cuts": 246,
        "dependency_closure_count": 106,
        "dependency_closure_sha256": (
            "6cc5a371435d61ab8f6ca937793afc2e50681360939ced004941670405199738"
        ),
        "direct_dependencies": ["cell_history_succ_elim", "cell_history_extend"],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699"
        ),
        "proof_depth": 83,
        "proof_edges": 4_992,
        "proof_nodes": 30_648,
        "proof_objects": 4_761,
        "reused_objects": 232,
        "statement_characters": 8_954,
        "statement_sha256": (
            "bb678323c7061f561ce69bb0357bf93ece948acf763503eec4763934cf50b23c"
        ),
    },
    "cell_list_length_functional": {
        "cuts": 299,
        "dependency_closure_count": 126,
        "dependency_closure_sha256": (
            "ff1067d392da4f760916ad688c25a6f27c94a9c9a71f09886869205ad57e823c"
        ),
        "direct_dependencies": [
            "cell_list_zero_iff_nil",
            "cell_list_succ_iff_cell",
            "nil_not_cell",
            "cell_tail_functional",
            "zero_or_succ",
        ],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c"
        ),
        "proof_depth": 85,
        "proof_edges": 5_976,
        "proof_nodes": 34_732,
        "proof_objects": 5_700,
        "reused_objects": 277,
        "statement_characters": 5_517,
        "statement_sha256": (
            "e08563402824e2af98ac5fcd56065b173da4713dd33ab96ec16fb6fc5346b8e3"
        ),
    },
    "cell_list_length_le_code": {
        "cuts": 257,
        "dependency_closure_count": 110,
        "dependency_closure_sha256": (
            "065b64ce37889bd5d9e972abf059768120f0cf48b42009e9ce26cd6e97c78ceb"
        ),
        "direct_dependencies": [
            "cell_list_succ_iff_cell",
            "cell_tail_lt_code",
            "zero_le",
            "succ_le_succ",
            "le_trans",
        ],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9"
        ),
        "proof_depth": 84,
        "proof_edges": 5_129,
        "proof_nodes": 31_002,
        "proof_objects": 4_891,
        "reused_objects": 239,
        "statement_characters": 2_754,
        "statement_sha256": (
            "48af1df5e7ca96895308b04b48ed154ed33399424d19a38b7cb18841ac12a08a"
        ),
    },
    "cell_list_length_total": {
        "cuts": 246,
        "dependency_closure_count": 107,
        "dependency_closure_sha256": (
            "2ca3bf882b176ea331014e6f21701bfabae733510dc75ddbb36b3a6ebe5fe376"
        ),
        "direct_dependencies": [
            "cell_history_nil",
            "cell_constructor",
            "cell_history_extend",
        ],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17"
        ),
        "proof_depth": 84,
        "proof_edges": 5_078,
        "proof_nodes": 29_569,
        "proof_objects": 4_848,
        "reused_objects": 231,
        "statement_characters": 2_219,
        "statement_sha256": (
            "8e6cea3fc40ffe051e4e3eb8af5b698e087c0f3d798fcfc628a107db1b09d765"
        ),
    },
}

# Current ordinary-tactic live-certificate ceilings.  The receipt is evidence
# that all eight closed results fit these limits, not permission to raise them.
MAX_PROOF_NODES = 500_000
MAX_PROOF_OBJECTS = 100_000
MAX_PROOF_DEPTH = 256


@dataclass(frozen=True)
class _SurfaceSpec:
    """The three theorem fields needed for a no-replay source comparison."""

    name: str
    statement: str
    dependencies: tuple[str, ...]


def _capture_surface(
    name: str,
    statement: str,
    dependencies: tuple[str, ...],
    _script: tuple[str, ...],
    _summary: str,
) -> _SurfaceSpec:
    return _SurfaceSpec(name, statement, dependencies)


Factory = Callable[[Callable[..., _SurfaceSpec]], tuple[_SurfaceSpec, ...]]
FACTORIES: tuple[Factory, ...] = (
    make_ha_cell_history_candidate_theorems,
    make_ha_cell_list_equations_candidate_theorems,
    make_ha_cell_list_length_functional_candidate_theorems,
    make_ha_cell_list_length_bound_candidate_theorems,
    make_ha_cell_list_length_total_candidate_theorems,
)


def _current_surfaces() -> tuple[_SurfaceSpec, ...]:
    return tuple(
        item
        for factory in FACTORIES
        for item in factory(_capture_surface)
    )


def test_sealed_k3b_cell_history_wmi_receipt_is_exact_and_current() -> None:
    raw = ARTIFACT_PATH.read_bytes()
    assert len(raw) == ARTIFACT_BYTES
    assert sha256(raw).hexdigest() == ARTIFACT_SHA256
    assert raw.endswith(b"\n")

    receipt = json.loads(raw)
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
    assert receipt["format"] == "peano-k3b-cell-history-cold-closure-v1"
    assert receipt["schema_version"] == 1
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["environment"] == EXPECTED_ENVIRONMENT
    assert receipt["provenance"] == EXPECTED_PROVENANCE
    assert receipt["requested_resources"] == EXPECTED_RESOURCES
    assert tuple(receipt["selected_theorems"]) == TARGET_NAMES
    assert receipt["results"] == EXPECTED_RESULTS

    surfaces = _current_surfaces()
    assert tuple(item.name for item in surfaces) == TARGET_NAMES
    for item in surfaces:
        closed = receipt["results"][item.name]
        assert len(item.statement) == closed["statement_characters"]
        assert sha256(item.statement.encode("utf-8")).hexdigest() == closed[
            "statement_sha256"
        ]
        assert list(item.dependencies) == closed["direct_dependencies"]

    for name in TARGET_NAMES:
        closed = receipt["results"][name]
        assert closed["dne_objects"] == 0
        assert 0 < closed["proof_nodes"] <= MAX_PROOF_NODES
        assert 0 < closed["proof_objects"] <= MAX_PROOF_OBJECTS
        assert 0 < closed["proof_depth"] <= MAX_PROOF_DEPTH
        assert closed["proof_objects"] <= closed["proof_nodes"]
        assert closed["proof_edges"] == (
            closed["proof_objects"] + closed["reused_objects"] - 1
        )
        assert closed["cuts"] <= closed["proof_objects"]
        assert closed["dependency_closure_count"] >= (
            len(closed["direct_dependencies"]) + 1
        )
