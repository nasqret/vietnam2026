"""Lightweight verifier for the sealed full K3B ListAt WMI receipt.

This audit pins the exact JSON artifact and reconstructs theorem metadata only.
It never parses tactics, replays a theorem, builds a certificate, or invokes
the kernel checker.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.library.ha_cell_bounds_candidate import (  # noqa: E402
    make_ha_cell_bounds_candidate_theorems,
)
from peano_lab.library.ha_cell_functional_candidate import (  # noqa: E402
    make_ha_cell_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_history_candidate import (  # noqa: E402
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (  # noqa: E402
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (  # noqa: E402
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_extensional_candidate import (  # noqa: E402
    make_ha_cell_list_extensional_candidate_theorems,
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
from peano_lab.library.ha_cell_list_lookup_domain_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_domain_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_exists_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_exists_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_external_bound_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_external_bound_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_functional_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_head_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_head_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_history_independent_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_history_independent_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_succ_candidate import (  # noqa: E402
    make_ha_cell_list_lookup_succ_candidate_theorems,
)
from peano_lab.library.ha_pair_cell_seed_candidate import (  # noqa: E402
    make_ha_pair_cell_seed_candidate_theorems,
)
from peano_lab.library.ha_pair_injective_candidate import (  # noqa: E402
    make_ha_pair_injective_candidate_theorems,
)
from peano_lab.library.ha_pair_shell_candidate import (  # noqa: E402
    make_ha_pair_shell_candidate_theorems,
)
from peano_lab.library.theorems import _specs_by_name  # noqa: E402


ARTIFACT_PATH = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-library"
    / "ha-k3b-listat-full-closure-219217.json"
)
ARTIFACT_BYTES = 10_550
ARTIFACT_SHA256 = (
    "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8"
)
EXPECTED_PROVENANCE = {
    "local_commit": "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
    "local_dirty": False,
    "payload_sha256": (
        "78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835"
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
TARGET_NAMES = (
    "cell_history_nil",
    "cell_history_extend",
    "cell_history_succ_elim",
    "cell_history_extend_preserves_prefix",
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "cell_list_length_functional",
    "cell_list_length_le_code",
    "cell_list_length_total",
    "list_at_domain",
    "list_at_head_iff",
    "list_at_succ_iff",
    "list_at_external_bound",
    "list_at_exists",
    "list_at_functional",
    "list_at_history_independent",
    "cell_list_extensional",
)
TOP_LEVEL_KEYS = {
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
RESULT_KEYS = {
    "cuts",
    "dependency_closure_count",
    "dependency_closure_sha256",
    "direct_dependencies",
    "dne_objects",
    "proof_dag_sha256",
    "proof_depth",
    "proof_edges",
    "proof_nodes",
    "proof_objects",
    "reused_objects",
    "statement_characters",
    "statement_sha256",
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
MAX_PROOF_NODES = 500_000
MAX_PROOF_OBJECTS = 100_000
MAX_PROOF_DEPTH = 256


@dataclass(frozen=True)
class _SurfaceSpec:
    name: str
    statement: str
    dependencies: tuple[str, ...]
    script: tuple[str, ...]
    summary: str


Factory = Callable[[type[_SurfaceSpec]], tuple[_SurfaceSpec, ...]]
SUPPORT_FACTORIES: tuple[Factory, ...] = (
    make_ha_pair_cell_seed_candidate_theorems,
    make_ha_pair_shell_candidate_theorems,
    make_ha_pair_injective_candidate_theorems,
    make_ha_cell_functional_candidate_theorems,
    make_ha_cell_bounds_candidate_theorems,
)
TARGET_FACTORIES: tuple[Factory, ...] = (
    make_ha_cell_history_candidate_theorems,
    make_ha_cell_history_prefix_preservation_candidate_theorems,
    make_ha_cell_list_equations_candidate_theorems,
    make_ha_cell_list_length_functional_candidate_theorems,
    make_ha_cell_list_length_bound_candidate_theorems,
    make_ha_cell_list_length_total_candidate_theorems,
    make_ha_cell_list_lookup_domain_candidate_theorems,
    make_ha_cell_list_lookup_head_candidate_theorems,
    make_ha_cell_list_lookup_succ_candidate_theorems,
    make_ha_cell_list_lookup_external_bound_candidate_theorems,
    make_ha_cell_list_lookup_exists_candidate_theorems,
    make_ha_cell_list_lookup_functional_candidate_theorems,
    make_ha_cell_list_lookup_history_independent_candidate_theorems,
    make_ha_cell_list_extensional_candidate_theorems,
)


def _private_surfaces() -> tuple[dict[str, _SurfaceSpec], tuple[str, ...]]:
    table: dict[str, _SurfaceSpec] = {}
    targets: list[str] = []
    for factory in SUPPORT_FACTORIES + TARGET_FACTORIES:
        rows = factory(_SurfaceSpec)
        assert type(rows) is tuple
        for item in rows:
            assert type(item) is _SurfaceSpec
            assert item.name not in table
            table[item.name] = item
            if factory in TARGET_FACTORIES:
                targets.append(item.name)
    return table, tuple(targets)


def _dependency_closure(
    name: str,
    available: dict[str, object],
) -> tuple[str, ...]:
    complete: set[str] = set()
    active: set[str] = set()

    def visit(current: str) -> None:
        if current in complete:
            return
        assert current not in active
        item = available.get(current)
        assert item is not None
        active.add(current)
        for dependency in item.dependencies:
            visit(dependency)
        active.remove(current)
        complete.add(current)

    visit(name)
    return tuple(sorted(complete))


def test_full_lookup_wmi_receipt_is_exact_surface_bound_and_constructive() -> None:
    encoded = ARTIFACT_PATH.read_bytes()
    assert len(encoded) == ARTIFACT_BYTES
    assert sha256(encoded).hexdigest() == ARTIFACT_SHA256
    assert encoded.endswith(b"\n")

    receipt = json.loads(encoded)
    canonical = (
        json.dumps(
            receipt,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")
    assert encoded == canonical

    assert set(receipt) == TOP_LEVEL_KEYS
    assert receipt["format"] == "peano-k3b-cell-history-cold-closure-v3"
    assert receipt["schema_version"] == 1
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["environment"] == EXPECTED_ENVIRONMENT
    assert receipt["provenance"] == EXPECTED_PROVENANCE
    assert receipt["requested_resources"] == EXPECTED_RESOURCES
    assert tuple(receipt["selected_theorems"]) == TARGET_NAMES
    assert set(receipt["results"]) == set(TARGET_NAMES)
    assert len(receipt["results"]) == len(TARGET_NAMES) == 17

    private, target_order = _private_surfaces()
    assert target_order == TARGET_NAMES
    public = dict(_specs_by_name())
    assert not (set(public) & set(private))
    available: dict[str, object] = dict(public)
    available.update(private)

    for name in TARGET_NAMES:
        surface = private[name]
        result = receipt["results"][name]
        assert set(result) == RESULT_KEYS
        assert result["direct_dependencies"] == list(surface.dependencies)
        assert result["statement_characters"] == len(surface.statement)
        assert result["statement_sha256"] == sha256(
            surface.statement.encode("utf-8")
        ).hexdigest()

        closure = _dependency_closure(name, available)
        assert result["dependency_closure_count"] == len(closure)
        assert result["dependency_closure_sha256"] == sha256(
            "\n".join(closure).encode("utf-8")
        ).hexdigest()

        assert result["dne_objects"] == 0
        assert SHA256_PATTERN.fullmatch(result["statement_sha256"])
        assert SHA256_PATTERN.fullmatch(result["dependency_closure_sha256"])
        assert SHA256_PATTERN.fullmatch(result["proof_dag_sha256"])
        assert 0 < result["statement_characters"]
        assert 0 < result["proof_nodes"] <= MAX_PROOF_NODES
        assert 0 < result["proof_objects"] <= MAX_PROOF_OBJECTS
        assert 0 < result["proof_depth"] <= MAX_PROOF_DEPTH
        assert 0 <= result["cuts"] <= result["proof_objects"]
        assert 0 <= result["reused_objects"]
        assert result["proof_objects"] <= result["proof_nodes"]
        assert result["proof_edges"] == (
            result["proof_objects"] + result["reused_objects"] - 1
        )
        assert result["dependency_closure_count"] >= (
            len(result["direct_dependencies"]) + 1
        )
