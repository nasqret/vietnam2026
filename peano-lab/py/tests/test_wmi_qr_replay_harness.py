"""Cheap, no-network regressions for the WMI QR replay transport."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


REPO = Path(__file__).resolve().parents[3]
RUNNER = REPO / "scripts" / "run_qr_wmi_replay.py"
SUBMIT = REPO / "scripts" / "submit_wmi_qr_replay.sh"
SLURM = REPO / "slurm" / "peano_wmi_qr_replay.sbatch"
CLOSURE = REPO / "peano-lab" / "py" / "tests" / (
    "test_quadratic_reciprocity_closure.py"
)
LAYERED_WMI = REPO / "peano-lab" / "py" / "tests" / (
    "test_quadratic_reciprocity_layered_wmi.py"
)

FINAL_SELECTORS = (
    "test_quadratic_reciprocity_candidate.py::"
    "test_quadratic_reciprocity_factory_is_exact_ordered_and_isolated",
    "test_quadratic_reciprocity_candidate.py::"
    "test_quadratic_reciprocity_contracts_are_closed_native_pa",
    "test_quadratic_reciprocity_candidate.py::"
    "test_quadratic_reciprocity_scripts_are_constructive_and_explicit",
    "test_quadratic_reciprocity_candidate.py::"
    "test_quadratic_reciprocity_bodies_kernel_check_within_laptop_limit",
    "test_quadratic_reciprocity_closure.py::"
    "test_quadratic_reciprocity_closure_manifest_is_exact_deterministic_and_source_isolated",
    "test_quadratic_reciprocity_closure.py::"
    "test_quadratic_reciprocity_closure_graph_is_exact_acyclic_and_closed_over_dependencies",
)

RECURSIVE_DIAGNOSTIC_SELECTORS = (
    "test_quadratic_reciprocity_closure.py::"
    "test_quadratic_reciprocity_full_recursive_cut_closure_replays_twice_deterministically",
    "test_quadratic_reciprocity_closure.py::"
    "test_quadratic_reciprocity_full_closure_rejects_false_contract_and_every_direct_dependency_cut_mutation",
    "test_quadratic_reciprocity_closure.py::"
    "test_quadratic_reciprocity_full_closure_meets_current_use_capacity_policy",
)

LAYERED_SELECTORS = (
    "test_quadratic_reciprocity_layered_experiment.py::"
    "test_blueprint_uses_exact_shared_557_node_45_layer_qr_stack",
    "test_quadratic_reciprocity_layered_experiment.py::"
    "test_blueprint_provenance_hashes_are_not_bodies_or_authority",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_wmi_contract_is_exact_static_and_unregistered",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_actual_targets_dummy_body_scaffold_metrics_are_pinned",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_exact_topology_distinct_target_scaffold_kernel_checks",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_builds_each_dependency_curried_body_once_per_cold_pass",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_full_certificate_kernel_checks_twice_deterministically",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_false_target_layer_package_and_body_mutations_fail_closed",
    "test_quadratic_reciprocity_layered_wmi.py::"
    "test_qr_layered_certificate_meets_current_use_capacity_policy",
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("_test_qr_wmi_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(*command: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=REPO,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_final_qr_suite_is_an_exact_nonempty_literal_subset_of_full() -> None:
    runner = _load_runner()
    selected = runner._selected_tests(
        runner.TEST_SUITES["quadratic-reciprocity-final"]
    )
    full = runner._selected_tests(runner.TEST_SUITES["full"])

    assert selected == FINAL_SELECTORS
    assert len(selected) == len(set(selected)) == 6
    assert all(selector in full for selector in selected)
    assert all(tests for tests in runner.TEST_SUITES.values())
    for selector in selected:
        source, _separator, name = selector.partition("::")
        assert source and name
        path = runner.TEST_ROOT / source
        assert path.is_file()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert name in definitions


def test_layered_and_recursive_diagnostic_suites_are_exact_and_separated() -> None:
    runner = _load_runner()
    layered = runner._selected_tests(
        runner.TEST_SUITES["quadratic-reciprocity-layered"]
    )
    diagnostic = runner._selected_tests(
        runner.TEST_SUITES["quadratic-reciprocity-recursive-diagnostic"]
    )
    full = runner._selected_tests(runner.TEST_SUITES["full"])

    assert layered == LAYERED_SELECTORS
    assert diagnostic == RECURSIVE_DIAGNOSTIC_SELECTORS
    assert len(layered) == len(set(layered)) == 9
    assert len(diagnostic) == len(set(diagnostic)) == 3
    assert len(full) == 136
    assert all(selector in full for selector in layered)
    assert all(selector not in full for selector in diagnostic)

    for selector in layered + diagnostic:
        source, _separator, name = selector.partition("::")
        path = runner.TEST_ROOT / source
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert name in definitions


def test_static_qr_suites_cannot_trigger_recursive_metadata_discovery(
    monkeypatch,
) -> None:
    namespace = runpy.run_path(str(CLOSURE))
    hook = namespace["wmi_receipt_metadata"]
    assert callable(hook)
    hook.__globals__["_static_wmi_receipt_metadata"] = lambda: {
        "static_manifest": True
    }

    def forbidden_discovery():
        raise AssertionError("recursive QR discovery escaped its diagnostic suite")

    hook.__globals__["_discovery_runs"] = forbidden_discovery
    for suite in ("full", "quadratic-reciprocity-final"):
        monkeypatch.setenv("PEANO_QR_SUITE", suite)
        assert hook() == {
            "static_manifest": True,
            "recursive_discovery_executed": False,
            "recursive_discovery_status": "not_selected",
        }

    class _UncachedDiscovery:
        class _Info:
            currsize = 0

        def cache_info(self):
            return self._Info()

        def __call__(self):
            raise AssertionError("recursive diagnostic discovery was retried")

    monkeypatch.setenv(
        "PEANO_QR_SUITE", "quadratic-reciprocity-recursive-diagnostic"
    )
    hook.__globals__["_discovery_runs"] = _UncachedDiscovery()
    assert hook() == {
        "static_manifest": True,
        "recursive_discovery_executed": False,
        "recursive_discovery_status": "failed_before_receipt_cache",
    }


def test_failed_layered_metadata_reports_partial_state_without_retry(
    monkeypatch,
) -> None:
    namespace = runpy.run_path(str(LAYERED_WMI))
    hook = namespace["wmi_receipt_metadata"]
    assert callable(hook)
    hook.__globals__["_static_wmi_receipt_metadata"] = lambda: {
        "static_blueprint": True
    }
    partial = {
        "status": "failed",
        "phase": "pass_1_compile",
        "error": "AssertionError: compiler sentinel",
        "passes": [
            {
                "pass_index": 1,
                "phase": "compile",
                "body_build_seconds": 12.5,
                "compile_seconds": 3.0,
                "kernel_check_seconds": None,
            }
        ],
    }
    hook.__globals__["_partial_discovery_snapshot"] = lambda: partial

    class _UncachedDiscovery:
        class _Info:
            currsize = 0

        def cache_info(self):
            return self._Info()

        def __call__(self):
            raise AssertionError("layered QR discovery was retried")

    hook.__globals__["_discovery_runs"] = _UncachedDiscovery()
    monkeypatch.setenv("PEANO_QR_SUITE", "quadratic-reciprocity-layered")

    assert hook() == {
        "static_blueprint": True,
        "discovery_receipt_cached": False,
        "discovery_status": "failed_before_receipt_cache",
        "passes": [],
        "mutation_audit_cached": False,
        "mutation_audit": None,
        "partial_discovery": partial,
    }


def test_layered_partial_receipt_survives_synthetic_kernel_rejection() -> None:
    namespace = runpy.run_path(str(LAYERED_WMI))
    cold = namespace["_cold_layered_admission"]
    assert callable(cold)
    zero = namespace["Zero"]()
    body_receipt = namespace["_BodyReceipt"](
        body_count=557,
        script_command_count=0,
        proof_occurrences=557,
        proof_objects=557,
        maximum_proof_depth=1,
        body_sha256="synthetic-body-receipt",
    )

    def synthetic_bodies(blueprint):
        return (
            {name: namespace["EqRefl"](zero) for name in blueprint.names},
            body_receipt,
        )

    cold.__globals__["_build_dependency_curried_bodies"] = synthetic_bodies
    cold.__globals__["check"] = lambda *_args: False
    cold.__globals__["_reset_partial_discovery_receipt"]()
    try:
        cold(1)
    except AssertionError as exc:
        assert "unchanged kernel rejected" in str(exc)
    else:
        raise AssertionError("synthetic kernel rejection unexpectedly passed")

    partial = cold.__globals__["_partial_discovery_snapshot"]()
    json.dumps(partial, allow_nan=False, sort_keys=True)
    assert partial["status"] == "failed"
    assert partial["phase"] == "pass_1_kernel_check"
    assert "unchanged kernel rejected" in partial["error"]
    assert len(partial["passes"]) == 1
    row = partial["passes"][0]
    assert row["status"] == "failed"
    assert row["phase"] == "kernel_check"
    assert row["body"] == {
        "body_count": 557,
        "script_command_count": 0,
        "proof_occurrences": 557,
        "proof_objects": 557,
        "maximum_proof_depth": 1,
        "body_sha256": "synthetic-body-receipt",
    }
    assert row["body_build_seconds"] >= 0
    assert row["compile_seconds"] >= 0
    assert row["kernel_check_seconds"] >= 0
    assert row["compilation"]["layer_count"] == 45
    assert row["kernel_accepted"] is False


def test_runner_lists_only_the_final_allowlist_and_rejects_unknown_suites() -> None:
    listed = _run(
        sys.executable,
        str(RUNNER),
        "--suite",
        "quadratic-reciprocity-final",
        "--list",
    )
    assert listed.returncode == 0, listed.stderr
    assert tuple(listed.stdout.splitlines()) == FINAL_SELECTORS

    for suite, expected in (
        ("quadratic-reciprocity-layered", LAYERED_SELECTORS),
        (
            "quadratic-reciprocity-recursive-diagnostic",
            RECURSIVE_DIAGNOSTIC_SELECTORS,
        ),
    ):
        listed = _run(
            sys.executable,
            str(RUNNER),
            "--suite",
            suite,
            "--list",
        )
        assert listed.returncode == 0, listed.stderr
        assert tuple(listed.stdout.splitlines()) == expected

    rejected = _run(sys.executable, str(RUNNER), "--suite", "qr-final-typo", "--list")
    assert rejected.returncode == 2
    assert "invalid choice" in rejected.stderr


def _install_receipt_environment(monkeypatch) -> None:
    values = {
        "PEANO_QR_LOCAL_COMMIT": "1" * 40,
        "PEANO_QR_LOCAL_DIRTY": "true",
        "PEANO_QR_REQUESTED_CPUS_PER_TASK": "1",
        "PEANO_QR_REQUESTED_MEMORY_MIB": "32768",
        "PEANO_QR_REQUESTED_NODES": "1",
        "PEANO_QR_REQUESTED_NTASKS": "1",
        "PEANO_QR_REQUESTED_PARTITION": "cpu_idle",
        "PEANO_QR_REQUESTED_TIME_LIMIT": "04:00:00",
        "PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS": "14400",
        "PEANO_QR_SNAPSHOT_SHA256": "2" * 64,
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_runner_preserves_json_metadata_after_a_selected_test_fails(
    tmp_path: Path, monkeypatch
) -> None:
    runner = _load_runner()
    source = tmp_path / "test_failure_with_metadata.py"
    source.write_text(
        "def test_failure():\n"
        "    raise AssertionError('original failure sentinel')\n\n"
        "def wmi_receipt_metadata():\n"
        "    return {'closure': {'proof_nodes': 600001}}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "TEST_ROOT", tmp_path)
    _install_receipt_environment(monkeypatch)

    payload = runner._run(((source.name, ("test_failure",)),), "unit-failure")

    assert payload["status"] == "failed"
    assert payload["source_metadata"] == {
        source.name: {"closure": {"proof_nodes": 600001}}
    }
    assert len(payload["tests"]) == 1
    assert payload["tests"][0]["status"] == "failed"
    assert "original failure sentinel" in payload["tests"][0]["error"]
    assert "original failure sentinel" in payload["tests"][0]["traceback"]


def test_runner_records_a_second_failure_when_failure_metadata_is_invalid(
    tmp_path: Path, monkeypatch
) -> None:
    runner = _load_runner()
    source = tmp_path / "test_failure_with_broken_metadata.py"
    source.write_text(
        "def test_failure():\n"
        "    raise AssertionError('original failure sentinel')\n\n"
        "def wmi_receipt_metadata():\n"
        "    raise RuntimeError('metadata failure sentinel')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "TEST_ROOT", tmp_path)
    _install_receipt_environment(monkeypatch)

    payload = runner._run(((source.name, ("test_failure",)),), "unit-failure")

    assert payload["status"] == "failed"
    assert payload["source_metadata"] == {}
    assert len(payload["tests"]) == 2
    original, metadata = payload["tests"]
    assert original["status"] == metadata["status"] == "failed"
    assert original["name"] == f"{source.name}::test_failure"
    assert "original failure sentinel" in original["traceback"]
    assert metadata["name"] == f"{source.name}::wmi_receipt_metadata"
    assert "metadata failure sentinel" in metadata["traceback"]


def test_submit_and_slurm_scripts_preserve_the_final_suite_boundaries() -> None:
    submit = SUBMIT.read_text(encoding="utf-8")
    slurm = SLURM.read_text(encoding="utf-8")

    syntax = _run("bash", "-n", str(SUBMIT), str(SLURM))
    assert syntax.returncode == 0, syntax.stderr

    help_result = _run("bash", str(SUBMIT), "--help")
    assert help_result.returncode == 0
    assert "quadratic-reciprocity-final" in help_result.stderr
    assert "quadratic-reciprocity-layered" in help_result.stderr
    assert "quadratic-reciprocity-recursive-diagnostic" in help_result.stderr

    rejected = _run("bash", str(SUBMIT), "--suite", "qr-final-typo")
    assert rejected.returncode == 2
    assert "unknown QR replay suite: qr-final-typo" in rejected.stderr

    assert "peano-lab/py/peano_lab" in submit
    assert "peano-lab/py/tests" in submit
    assert "--exclude='.DS_Store'" in submit
    assert "--exclude='peano-lab/py/peano_lab/library/" not in submit
    assert submit.count("quadratic-reciprocity-final") >= 4
    assert submit.count("quadratic-reciprocity-layered") >= 4
    assert submit.count("quadratic-reciprocity-recursive-diagnostic") >= 4
    assert slurm.count("quadratic-reciprocity-final") >= 2
    assert slurm.count("quadratic-reciprocity-layered") >= 2
    assert slurm.count("quadratic-reciprocity-recursive-diagnostic") >= 2
    high_profile_suites = (
        "full|fermat-endpoints|quadratic-reciprocity-final|"
        "quadratic-reciprocity-layered|"
        "quadratic-reciprocity-recursive-diagnostic)"
    )
    assert high_profile_suites in submit
    assert high_profile_suites in slurm
    for assignment in (
        "resource_memory_mib=32768",
        "resource_time_limit=04:00:00",
        "resource_time_limit_seconds=14400",
    ):
        assert assignment in submit
    for guard in (
        '"$PEANO_QR_REQUESTED_MEMORY_MIB" = 32768',
        '"$PEANO_QR_REQUESTED_TIME_LIMIT" = 04:00:00',
        '"$PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS" = 14400',
    ):
        assert guard in slurm
    for source in (
        "quadratic_reciprocity_candidate.py",
        "gauss_eisenstein_data_candidate.py",
    ):
        assert (REPO / "peano-lab" / "py" / "peano_lab" / "library" / source).is_file()
    assert (
        REPO / "peano-lab" / "py" / "tests" / "test_quadratic_reciprocity_closure.py"
    ).is_file()
    assert (
        REPO
        / "peano-lab"
        / "py"
        / "tests"
        / "test_quadratic_reciprocity_layered_wmi.py"
    ).is_file()
