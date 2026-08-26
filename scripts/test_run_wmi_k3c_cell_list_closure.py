"""Structural, CLI, and tiny-closure tests for the K3C WMI harness."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))


def _load_runner():
    path = REPOSITORY_ROOT / "scripts" / "run_wmi_k3c_cell_list_closure.py"
    spec = importlib.util.spec_from_file_location(
        "run_wmi_k3c_cell_list_closure_under_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = _load_runner()
SBATCH = (
    REPOSITORY_ROOT / "slurm" / "peano_wmi_k3c_cell_list_closure.sbatch"
)

EXPECTED_TARGET_NAMES = (
    "cell_list_valid_nil",
    "cell_list_valid_cell_intro",
    "cell_list_valid_cases",
    "cell_list_valid_cell_elim",
    "list_at_implies_cell_list_valid",
    "list_member_implies_cell_list_valid",
    "list_member_nil_false",
    "list_member_cell_intro_head",
    "list_member_cell_intro_tail",
    "list_member_cell_elim",
    "list_member_cell_iff",
    "list_member_pointwise_transport",
    "list_at_exists_unique",
    "cell_list_nonempty_iff_head_exists",
    "cell_list_code_eq_lookup_values",
    "cell_list_code_eq_iff_pointwise",
    "cell_list_decompose_unique",
)
EXPECTED_PARENT = {
    "alpha_v2_checked_use_count": 570,
    "alpha_v2_edge_count": 2_674,
    "alpha_v2_enrollment_sha256": (
        "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
    ),
    "alpha_v2_identity_sha256": (
        "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
    ),
    "alpha_v2_layer_count": 45,
    "alpha_v2_theorem_count": 902,
}
EXPECTED_TINY_RECEIPT = {
    "cell_list_valid_nil": {
        "cuts": 3,
        "dependency_closure_count": 4,
        "dependency_closure_sha256": (
            "d713aac83614e8f3589ff9432b19f7c7e24a3a9970b3fa1a9e7016b1145792a7"
        ),
        "direct_dependencies": ["cell_history_nil"],
        "dne_objects": 0,
        "proof_dag_sha256": (
            "4e0ca50959a77dc71f1d7de3f285d9b9b3326e5b5fac4902deff1d6c242bf45c"
        ),
        "proof_depth": 19,
        "proof_edges": 159,
        "proof_nodes": 160,
        "proof_objects": 160,
        "reused_objects": 0,
        "script_commands": 4,
        "script_sha256": (
            "7b0e529d46614f8b47fd5fc29e4acf3684cc6c3fdc6bb3744bb1d7c2894e5635"
        ),
        "statement_characters": 3_185,
        "statement_sha256": (
            "5ec6b2e7ef6f193917b42834c4b0c51cfde4af18da2975e43f574ee0379458ec"
        ),
    }
}


def _set_valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "PEANO_K3C_LOCAL_COMMIT": "1" * 40,
        "PEANO_K3C_LOCAL_DIRTY": "false",
        "PEANO_K3C_PAYLOAD_SHA256": "2" * 64,
        "PEANO_K3C_REQUESTED_PARTITION": "cpu_idle",
        "PEANO_K3C_REQUESTED_NODES": "1",
        "PEANO_K3C_REQUESTED_NTASKS": "1",
        "PEANO_K3C_REQUESTED_CPUS_PER_TASK": "1",
        "PEANO_K3C_REQUESTED_MEMORY_MIB": "32768",
        "PEANO_K3C_REQUESTED_TIME_LIMIT": "04:00:00",
        "PEANO_K3C_REQUESTED_TIME_LIMIT_SECONDS": "14400",
        "PYTHONHASHSEED": "20260809",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_parent_target_surfaces_and_local_dependency_graph_are_exact() -> None:
    assert RUNNER.FORMAT == "peano-k3c-cell-list-cold-closure-v1"
    assert RUNNER.EXPECTED_PASSES == 2
    assert RUNNER.TARGET_NAMES == EXPECTED_TARGET_NAMES
    assert RUNNER._parent_receipt() == EXPECTED_PARENT

    local = RUNNER._local_specs()
    public = RUNNER._public_specs()
    assert tuple(local) == EXPECTED_TARGET_NAMES
    assert not (set(local) & set(public))
    assert sum(len(item.dependencies) for item in local.values()) == 33
    assert RUNNER._target_graph_sha256(tuple(local.values())) == (
        "b1dd6e67e085817c41a4608c12b176c7bdeab7e785d4e9a35592626f5a53fb1c"
    )
    assert RUNNER._target_surface_sha256(tuple(local.values())) == (
        "448b1e07315f2d9e8430f049fa89760223b2e838ff203daeeda87410ed76a338"
    )

    available = set(public)
    for name, item in local.items():
        assert all(dependency in available for dependency in item.dependencies)
        available.add(name)
    closure = RUNNER._dependency_closure(EXPECTED_TARGET_NAMES, local, public)
    assert len(closure) == 151
    assert sha256("\n".join(closure).encode()).hexdigest() == (
        "02052e2c4b95eaade2c6f2a8f3dbdbaf2250341236ffd74d0027da5db1f1d9a2"
    )


def test_cli_lists_and_selects_only_the_frozen_canonical_order(capsys) -> None:
    assert RUNNER.main(["--list-theorems"]) == 0
    assert tuple(capsys.readouterr().out.splitlines()) == EXPECTED_TARGET_NAMES

    requested = (EXPECTED_TARGET_NAMES[-1], EXPECTED_TARGET_NAMES[0])
    assert RUNNER._selected(requested) == (
        EXPECTED_TARGET_NAMES[0],
        EXPECTED_TARGET_NAMES[-1],
    )
    assert RUNNER._selected(None) == EXPECTED_TARGET_NAMES
    with pytest.raises(RUNNER.ClosureError, match="duplicate"):
        RUNNER._selected((EXPECTED_TARGET_NAMES[0],) * 2)
    with pytest.raises(SystemExit):
        RUNNER._arguments(["--theorem", "not_a_k3c_theorem"])
    with pytest.raises(RUNNER.ClosureError, match="exactly two"):
        RUNNER.main(["--passes", "1", "--report", "unused.json"])


def test_requested_resources_and_provenance_are_exact(monkeypatch) -> None:
    _set_valid_environment(monkeypatch)
    assert RUNNER._resources() == RUNNER.EXPECTED_RESOURCES
    assert RUNNER._provenance() == {
        "local_commit": "1" * 40,
        "local_dirty": False,
        "payload_sha256": "2" * 64,
    }

    monkeypatch.setenv("PEANO_K3C_REQUESTED_MEMORY_MIB", "65536")
    with pytest.raises(RUNNER.ClosureError, match="resource profile mismatch"):
        RUNNER._resources()
    monkeypatch.setenv("PEANO_K3C_PAYLOAD_SHA256", "not-a-sha")
    with pytest.raises(RUNNER.ClosureError, match="PAYLOAD_SHA256"):
        RUNNER._provenance()


def test_sbatch_profile_selection_and_non_submission_are_frozen() -> None:
    text = SBATCH.read_text(encoding="utf-8")
    lines = set(text.splitlines())
    assert {
        "#SBATCH --partition=cpu_idle",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --mem=32768M",
        "#SBATCH --time=04:00:00",
    } <= lines
    assert "arguments=(--passes 2)" in text
    assert "export PYTHONHASHSEED=20260809" in text
    assert "scripts/run_wmi_k3c_cell_list_closure.py" in text
    assert "PEANO_K3C_PAYLOAD_SHA256" in text
    assert "PEANO_K3C_LOCAL_COMMIT" in text
    assert "SLURM_MEM_PER_NODE" in text
    assert all(name in text for name in EXPECTED_TARGET_NAMES)
    assert "\nsbatch " not in text
    assert "\nsrun " not in text
    subprocess.run(["bash", "-n", str(SBATCH)], check=True)


def test_two_tiny_passes_use_distinct_fresh_processes_and_match_exactly(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _set_valid_environment(monkeypatch)
    selected = EXPECTED_TARGET_NAMES[0]
    report = tmp_path / "success" / "receipt.json"
    assert RUNNER.main(["--theorem", selected, "--report", str(report)]) == 0
    receipt = json.loads(report.read_text(encoding="utf-8"))
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["parent"] == EXPECTED_PARENT
    assert receipt["selected_theorems"] == [selected]
    assert receipt["results"] == EXPECTED_TINY_RECEIPT
    assert receipt["results"][selected]["dne_objects"] == 0
    passes = receipt["cold_passes"]
    payloads = [item["worker_payload"] for item in passes]
    assert [item["pass_index"] for item in payloads] == [1, 2]
    assert payloads[0]["receipt"] == payloads[1]["receipt"]
    assert payloads[0]["receipt"]["results"] == EXPECTED_TINY_RECEIPT
    worker_pids = [item["process"]["pid"] for item in payloads]
    assert len(set(worker_pids)) == 2
    assert os.getpid() not in worker_pids
    assert all(
        item["process"]["parent_pid"] == os.getpid() for item in payloads
    )
    assert len(
        {item["process"]["process_nonce"] for item in payloads}
    ) == 2
    assert all(
        len(item["worker_payload_sha256"]) == 64 for item in passes
    )
    assert all(
        sha256(
            RUNNER._canonical_json_bytes(item["worker_payload"])
        ).hexdigest()
        == item["worker_payload_sha256"]
        for item in passes
    )
    assert report.read_bytes().endswith(b"\n")
    assert tuple(report.parent.glob(f".{report.name}.pass-*.json")) == ()


def test_second_pass_failure_or_nondeterminism_leaves_no_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _set_valid_environment(monkeypatch)
    selected = EXPECTED_TARGET_NAMES[0]
    report = tmp_path / "failed.json"
    real_subprocess_run = RUNNER.subprocess.run
    worker_calls = 0

    def failed_worker(command, **kwargs):
        nonlocal worker_calls
        worker_calls += 1
        assert "--worker-report" in command
        assert "--worker-parent-pid" in command
        if worker_calls == 1:
            return real_subprocess_run(command, **kwargs)
        return subprocess.CompletedProcess(command, 9, "", "synthetic failure")

    monkeypatch.setattr(RUNNER.subprocess, "run", failed_worker)
    with pytest.raises(RUNNER.ClosureError, match="exit 9"):
        RUNNER.main(["--theorem", selected, "--report", str(report)])
    assert worker_calls == 2
    assert not report.exists()
    assert tuple(tmp_path.glob(f".{report.name}.pass-*.json")) == ()

    monkeypatch.setattr(RUNNER.subprocess, "run", real_subprocess_run)
    parent = RUNNER._parent_receipt()
    provenance = RUNNER._provenance()
    resources = RUNNER._resources()
    common = RUNNER._deterministic_receipt(
        (selected,), parent, provenance, resources, EXPECTED_TINY_RECEIPT
    )

    mismatch = tmp_path / "nondeterministic.json"

    def fake_pass(index: int, receipt: dict[str, object], pid: int):
        return {
            "worker_payload": {
                "format": RUNNER.WORKER_FORMAT,
                "pass_index": index,
                "process": {
                    "parent_pid": os.getpid(),
                    "pid": pid,
                    "process_nonce": f"{index:032x}",
                },
                "receipt": receipt,
                "schema_version": 1,
                "status": "passed",
            },
            "worker_payload_sha256": f"{index:064x}",
        }

    def nondeterministic_worker(index, _selected, _report, _expected):
        receipt = json.loads(json.dumps(common))
        if index == 2:
            receipt["results"][selected]["cuts"] = 4
        return fake_pass(index, receipt, os.getpid() + index)

    monkeypatch.setattr(RUNNER, "_run_worker", nondeterministic_worker)
    with pytest.raises(RUNNER.ClosureError, match="nondeterministic"):
        RUNNER.main(["--theorem", selected, "--report", str(mismatch)])
    assert not mismatch.exists()

    reused = tmp_path / "reused-process.json"

    def reused_process(index, _selected, _report, _expected):
        return fake_pass(index, common, os.getpid() + 1)

    monkeypatch.setattr(RUNNER, "_run_worker", reused_process)
    with pytest.raises(RUNNER.ClosureError, match="distinct fresh processes"):
        RUNNER.main(["--theorem", selected, "--report", str(reused)])
    assert not reused.exists()
