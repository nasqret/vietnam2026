#!/usr/bin/env python3
"""Run the heavy quadratic-reciprocity replay gates without pytest.

WMI's reviewed central Python does not ship pytest.  The selected admission
tests are plain functions with assertions; several hygiene checks use only
``pytest.raises``.  This runner supplies that tiny context-manager surface,
executes an explicit allowlist, and emits a machine-readable receipt.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import resource
from runpy import run_path
import sys
import time
import traceback
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "peano-lab" / "py" / "tests"
SNAPSHOT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
POSITIVE_INTEGER_PATTERN = re.compile(r"^[1-9][0-9]*$")
PARTITION_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
TIME_LIMIT_PATTERN = re.compile(r"^(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$")

TESTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "test_euler_scaled_inverse_candidate.py",
        (
            "test_euler_scaled_inverse_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_euler_scaled_inverse_helpers_are_hygienic_alpha_native_and_audited",
            "test_euler_scaled_inverse_graph_is_exact_core_bounded_and_source_isolated",
            "test_euler_scaled_inverse_body_preflight_then_replays_twice_with_full_cut_closure",
            "test_euler_scaled_inverse_rejects_false_contract_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_finite_omission_candidate.py",
        (
            "test_finite_omission_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_finite_omission_helpers_are_hygienic_alpha_native_and_witnesses_audited",
            "test_finite_omission_graph_is_exact_core_bounded_and_source_isolated",
            "test_finite_omission_stack_replays_twice_profiles_full_cut_closure",
            "test_finite_omission_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_gauss_signed_half_candidate.py",
        (
            "test_gauss_signed_half_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_gauss_signed_half_helpers_are_hygienic_alpha_native_and_witnesses_audited",
            "test_gauss_signed_half_graph_is_exact_core_bounded_and_source_isolated",
            "test_gauss_signed_half_stack_replays_twice_profiles_full_cut_closure",
            "test_gauss_signed_half_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_gauss_signed_prefix_candidate.py",
        (
            "test_gauss_signed_prefix_contracts_and_bodies_are_exact_native_pa",
            "test_gauss_signed_prefix_helpers_are_hygienic_alpha_native_and_semantic",
            "test_gauss_signed_prefix_graph_is_exact_core_bounded_and_isolated",
            "test_gauss_signed_prefix_stack_replays_twice_profiles_full_cut_closure",
            "test_gauss_signed_prefix_rejects_contract_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_gauss_magnitude_permutation_candidate.py",
        (
            "test_gauss_magnitude_contracts_and_bodies_are_exact_native_pa",
            "test_gauss_magnitude_helpers_are_hygienic_alpha_native_and_semantic",
            "test_gauss_magnitude_graph_is_exact_core_bounded_and_source_isolated",
            "test_gauss_magnitude_stack_replays_twice_profiles_full_cut_closure",
            "test_gauss_magnitude_rejects_contract_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_gauss_sign_factor_recode_candidate.py",
        (
            "test_gauss_sign_factor_recode_contracts_and_bodies_are_exact_native_pa",
            "test_gauss_sign_factor_recode_surface_is_hygienic_alpha_equal_and_semantic",
            "test_gauss_sign_factor_recode_graph_is_ordered_bounded_and_source_isolated",
            "test_gauss_sign_factor_recode_stack_replays_twice_profiles_full_cut_closure",
            "test_gauss_sign_factor_recode_rejects_false_contracts_and_direct_cut_mutations",
        ),
    ),
    (
        "test_wilson_pair_product_candidate.py",
        (
            "test_wilson_pair_product_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_wilson_pair_product_helpers_are_exact_hygienic_alpha_equal_and_guard_normalization",
            "test_wilson_pair_product_graph_is_exact_core_bounded_and_source_isolated",
            "test_wilson_pair_product_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_pair_product_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_pair_order_candidate.py",
        (
            "test_wilson_pair_order_contracts_and_bodies_are_exact_native_pa",
            "test_wilson_pair_order_helpers_are_hygienic_alpha_equal_and_compound_safe",
            "test_wilson_pair_order_graph_is_ordered_core_bounded_and_source_isolated",
            "test_wilson_pair_order_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_pair_order_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_pair_order_induction_candidate.py",
        (
            "test_wilson_pair_order_induction_contracts_and_bodies_are_exact_native_pa",
            "test_wilson_pair_order_induction_state_is_hygienic_alpha_equal_and_bounded",
            "test_wilson_pair_order_induction_graph_is_ordered_bounded_and_isolated",
            "test_wilson_pair_order_induction_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_pair_order_induction_rejects_false_contracts_and_direct_cut_mutations",
        ),
    ),
    (
        "test_wilson_pair_order_iteration_candidate.py",
        (
            "test_wilson_pair_order_iteration_contracts_and_bodies_are_exact_native_pa",
            "test_wilson_pair_order_iteration_state_is_hygienic_alpha_equal_and_semantic",
            "test_wilson_pair_order_iteration_graph_is_ordered_bounded_and_source_isolated",
            "test_wilson_pair_order_iteration_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_pair_order_iteration_rejects_false_contracts_and_direct_cut_mutations",
        ),
    ),
    (
        "test_wilson_inverse_orbit_candidate.py",
        (
            "test_wilson_orbit_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_wilson_orbit_helpers_are_exact_hygienic_and_alpha_equal",
            "test_wilson_orbit_graph_is_exact_core_bounded_and_source_isolated",
            "test_wilson_orbit_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_orbit_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_inverse_endpoints_candidate.py",
        (
            "test_wilson_endpoint_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_wilson_endpoint_helpers_are_exact_hygienic_and_alpha_equal",
            "test_wilson_endpoint_graph_is_exact_core_bounded_and_source_isolated",
            "test_wilson_endpoint_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_endpoint_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_inverse_involution_candidate.py",
        (
            "test_wilson_involution_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_wilson_involution_helpers_are_exact_hygienic_and_shared_alpha_equal",
            "test_wilson_involution_graph_is_exact_core_bounded_and_source_isolated",
            "test_wilson_involution_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_involution_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_inverse_prefix_candidate.py",
        (
            "test_wilson_inverse_contracts_are_exact_deterministic_closed_expanded_pa",
            "test_wilson_inverse_helpers_are_exact_hygienic_and_shared_alpha_equal",
            "test_wilson_inverse_dependency_graph_is_exact_core_bounded_and_isolated",
            "test_wilson_inverse_stack_replays_twice_profiles_full_cut_closure",
            "test_wilson_inverse_stack_rejects_false_contracts_and_every_direct_cut_mutation",
        ),
    ),
    (
        "test_wilson_square_one_candidate.py",
        (
            "test_wilson_square_one_contract_is_exact_deterministic_closed_expanded_pa",
            "test_wilson_square_one_helpers_are_exact_alpha_stable_and_fail_closed",
            "test_wilson_square_one_dependency_boundary_is_exact_core_and_isolated",
            "test_wilson_square_one_replays_twice_profiles_full_cut_closure",
            "test_wilson_square_one_rejects_contract_and_every_dependency_cut_mutation",
        ),
    ),
    (
        "test_fermat_endpoints_candidate.py",
        (
            "test_fermat_endpoint_contracts_are_deterministic_closed_expanded_pa",
            "test_fermat_endpoint_helpers_are_exact_alpha_stable_and_fail_closed",
            "test_fermat_endpoint_dependency_boundary_is_exact_acyclic_and_isolated",
            "test_fermat_endpoints_replay_twice_profile_and_check_cut_spines",
            "test_fermat_endpoints_reject_contract_and_dependency_cut_mutations",
        ),
    ),
    (
        "test_fermat_residue_reindex_candidate.py",
        (
            "test_fermat_residue_reindex_contracts_are_deterministic_closed_expanded_pa",
            "test_fermat_residue_reindex_helpers_are_exact_alpha_stable_and_fail_closed",
            "test_fermat_residue_reindex_dependency_boundary_is_exact_and_isolated",
            "test_fermat_residue_reindex_replays_twice_profiles_constructively",
            "test_fermat_residue_reindex_rejects_contract_and_cut_mutations",
        ),
    ),
    (
        "test_fermat_product_balance_candidate.py",
        (
            "test_fermat_product_balance_contract_is_deterministic_closed_expanded_pa",
            "test_fermat_product_balance_helpers_are_alpha_stable_and_fail_closed",
            "test_fermat_product_balance_dependency_boundary_is_exact_and_isolated",
            "test_fermat_product_balance_replays_twice_profiles_constructively",
            "test_fermat_product_balance_rejects_contract_and_cut_mutations",
        ),
    ),
    (
        "test_fermat_scale_product_candidate.py",
        (
            "test_fermat_scale_contract_is_deterministic_closed_expanded_pa",
            "test_fermat_scale_helpers_are_hygienic_expanded_and_fail_closed",
            "test_fermat_scale_replays_twice_profiles_and_rejects_mutations",
        ),
    ),
    (
        "test_fermat_residue_map_candidate.py",
        (
            "test_fermat_map_contracts_are_deterministic_closed_expanded_pa",
            "test_fermat_map_helpers_are_hygienic_expanded_and_fail_closed",
            "test_fermat_map_replays_twice_profiles_and_rejects_mutations",
        ),
    ),
    (
        "test_fermat_residue_product_candidate.py",
        (
            "test_fermat_candidate_contracts_are_deterministic_closed_expanded_pa",
            "test_fermat_candidate_helpers_are_hygienic_and_expanded",
            "test_fermat_candidate_replays_twice_profiles_and_rejects_mutations",
        ),
    ),
    (
        "test_finite_product_reindex_support.py",
        (
            "test_reindex_support_replays_twice_deterministically_constructively",
            "test_reindex_support_contracts_are_exact_closed_expanded_pa",
            "test_alignment_helpers_are_hygienic_alpha_stable_and_audited",
            "test_reindex_support_rejects_contract_and_cut_mutations",
        ),
    ),
    (
        "test_finite_product_reindex_theorems.py",
        (
            "test_product_reindex_replays_twice_deterministically_constructively",
            "test_product_reindex_contracts_are_exact_closed_expanded_native_pa",
            "test_product_reindex_authoring_is_deterministic_and_support_is_public",
            "test_product_reindex_rejects_false_contract_and_first_cut_mutation",
        ),
    ),
    (
        "test_qr_bounded_units.py",
        (
            "test_bounded_units_replay_twice_with_exact_receipts",
            "test_bounded_unit_contracts_are_exact_closed_expanded_native_pa",
            "test_bounded_unit_surface_helpers_are_exact_and_hygienic",
            "test_bounded_inverse_rejects_false_contract_and_cut_mutations",
        ),
    ),
    (
        "test_quadratic_reciprocity_candidate.py",
        (
            "test_quadratic_reciprocity_factory_is_exact_ordered_and_isolated",
            "test_quadratic_reciprocity_contracts_are_closed_native_pa",
            "test_quadratic_reciprocity_scripts_are_constructive_and_explicit",
            "test_quadratic_reciprocity_bodies_kernel_check_within_laptop_limit",
        ),
    ),
    (
        "test_quadratic_reciprocity_closure.py",
        (
            "test_quadratic_reciprocity_closure_manifest_is_exact_deterministic_and_source_isolated",
            "test_quadratic_reciprocity_closure_graph_is_exact_acyclic_and_closed_over_dependencies",
        ),
    ),
    (
        "test_quadratic_reciprocity_layered_experiment.py",
        (
            "test_blueprint_uses_exact_shared_557_node_45_layer_qr_stack",
            "test_blueprint_provenance_hashes_are_not_bodies_or_authority",
        ),
    ),
    (
        "test_quadratic_reciprocity_layered_wmi.py",
        (
            "test_qr_layered_wmi_contract_is_exact_static_and_unregistered",
            "test_qr_layered_actual_targets_dummy_body_scaffold_metrics_are_pinned",
            "test_qr_layered_exact_topology_distinct_target_scaffold_kernel_checks",
            "test_qr_layered_builds_each_dependency_curried_body_once_per_cold_pass",
            "test_qr_layered_full_certificate_kernel_checks_twice_deterministically",
            "test_qr_layered_false_target_layer_package_and_body_mutations_fail_closed",
            "test_qr_layered_certificate_meets_current_use_capacity_policy",
        ),
    ),
    (
        "test_certificate_capacity_profile.py",
        (
            "test_capacity_profile_distinguishes_occurrences_from_objects",
            "test_capacity_profile_rejects_unknown_theorem",
        ),
    ),
    (
        "test_ladder.py",
        (
            "test_full_binding_ladder_and_helpers_have_stable_acyclic_order",
            "test_every_script_replays_and_final_certificate_checks_original_statement",
            "test_core_capstone_is_the_required_zero_product_theorem",
            "test_mutating_a_capstone_arithmetic_leaf_is_rejected",
            "test_multi_dependency_cut_does_not_capture_inserted_internal_hypotheses",
            "test_implication_beta_normalization_avoids_proposition_capture",
            "test_implication_beta_normalization_shifts_terms_below_forall",
            "test_lookup_is_casefolded_but_unknown_names_do_not_fabricate_entries",
        ),
    ),
)

RECURSIVE_DIAGNOSTIC_TESTS: tuple[
    tuple[str, tuple[str, ...]], ...
] = (
    (
        "test_quadratic_reciprocity_closure.py",
        (
            "test_quadratic_reciprocity_full_recursive_cut_closure_replays_twice_deterministically",
            "test_quadratic_reciprocity_full_closure_rejects_false_contract_and_every_direct_dependency_cut_mutation",
            "test_quadratic_reciprocity_full_closure_meets_current_use_capacity_policy",
        ),
    ),
)

TEST_SUITES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "full": TESTS,
    "euler-scaled-inverse": tuple(
        item
        for item in TESTS
        if item[0] == "test_euler_scaled_inverse_candidate.py"
    ),
    "fermat-reindex": tuple(
        item for item in TESTS if item[0] == "test_fermat_residue_reindex_candidate.py"
    ),
    "fermat-balance": tuple(
        item for item in TESTS if item[0] == "test_fermat_product_balance_candidate.py"
    ),
    "fermat-endpoints": tuple(
        item for item in TESTS if item[0] == "test_fermat_endpoints_candidate.py"
    ),
    "wilson-square-one": tuple(
        item for item in TESTS if item[0] == "test_wilson_square_one_candidate.py"
    ),
    "wilson-inverse-prefix": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_inverse_prefix_candidate.py"
    ),
    "wilson-inverse-involution": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_inverse_involution_candidate.py"
    ),
    "wilson-inverse-endpoints": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_inverse_endpoints_candidate.py"
    ),
    "wilson-inverse-orbit": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_inverse_orbit_candidate.py"
    ),
    "wilson-pair-product": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_pair_product_candidate.py"
    ),
    "wilson-pair-order": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_pair_order_candidate.py"
    ),
    "wilson-pair-order-induction": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_pair_order_induction_candidate.py"
    ),
    "wilson-pair-order-iteration": tuple(
        item
        for item in TESTS
        if item[0] == "test_wilson_pair_order_iteration_candidate.py"
    ),
    "gauss-signed-half": tuple(
        item
        for item in TESTS
        if item[0] == "test_gauss_signed_half_candidate.py"
    ),
    "gauss-signed-prefix": tuple(
        item
        for item in TESTS
        if item[0] == "test_gauss_signed_prefix_candidate.py"
    ),
    "gauss-magnitude-permutation": tuple(
        item
        for item in TESTS
        if item[0] == "test_gauss_magnitude_permutation_candidate.py"
    ),
    "gauss-sign-factor-recode": tuple(
        item
        for item in TESTS
        if item[0] == "test_gauss_sign_factor_recode_candidate.py"
    ),
    "finite-omission": tuple(
        item
        for item in TESTS
        if item[0] == "test_finite_omission_candidate.py"
    ),
    "quadratic-reciprocity-final": tuple(
        item
        for item in TESTS
        if item[0]
        in {
            "test_quadratic_reciprocity_candidate.py",
            "test_quadratic_reciprocity_closure.py",
        }
    ),
    "quadratic-reciprocity-layered": tuple(
        item
        for item in TESTS
        if item[0]
        in {
            "test_quadratic_reciprocity_layered_experiment.py",
            "test_quadratic_reciprocity_layered_wmi.py",
        }
    ),
    "quadratic-reciprocity-recursive-diagnostic": RECURSIVE_DIAGNOSTIC_TESTS,
}
if any(not tests for tests in TEST_SUITES.values()):
    raise RuntimeError("every WMI QR replay suite must select at least one test file")


class _Raises:
    def __init__(self, expected: type[BaseException], match: str | None) -> None:
        self.expected = expected
        self.match = match

    def __enter__(self) -> "_Raises":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        _traceback: object,
    ) -> bool:
        if exc_type is None:
            raise AssertionError(f"expected {self.expected.__name__} was not raised")
        if not issubclass(exc_type, self.expected):
            return False
        if self.match is not None and (
            exc is None or re.search(self.match, str(exc)) is None
        ):
            raise AssertionError(
                f"exception {exc!r} did not match {self.match!r}"
            )
        return True


def _install_pytest_raises_stub() -> None:
    if "pytest" in sys.modules:
        return
    module = ModuleType("pytest")

    def raises(
        expected: type[BaseException], *, match: str | None = None
    ) -> _Raises:
        return _Raises(expected, match)

    module.raises = raises  # type: ignore[attr-defined]
    sys.modules["pytest"] = module


def _identity(name: str, pattern: re.Pattern[str]) -> str:
    value = os.environ.get(name, "")
    if pattern.fullmatch(value) is None:
        raise RuntimeError(f"missing or malformed {name}")
    return value


def _selected_tests(
    tests: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[str, ...]:
    return tuple(f"{source}::{name}" for source, names in tests for name in names)


def _requested_resources() -> dict[str, Any]:
    return {
        "cpus_per_task": int(
            _identity("PEANO_QR_REQUESTED_CPUS_PER_TASK", POSITIVE_INTEGER_PATTERN)
        ),
        "memory_mib": int(
            _identity("PEANO_QR_REQUESTED_MEMORY_MIB", POSITIVE_INTEGER_PATTERN)
        ),
        "nodes": int(
            _identity("PEANO_QR_REQUESTED_NODES", POSITIVE_INTEGER_PATTERN)
        ),
        "ntasks": int(
            _identity("PEANO_QR_REQUESTED_NTASKS", POSITIVE_INTEGER_PATTERN)
        ),
        "partition": _identity(
            "PEANO_QR_REQUESTED_PARTITION", PARTITION_PATTERN
        ),
        "time_limit": _identity(
            "PEANO_QR_REQUESTED_TIME_LIMIT", TIME_LIMIT_PATTERN
        ),
        "time_limit_seconds": int(
            _identity(
                "PEANO_QR_REQUESTED_TIME_LIMIT_SECONDS", POSITIVE_INTEGER_PATTERN
            )
        ),
    }


def _receipt_metadata(
    source: str, namespace: dict[str, Any]
) -> dict[str, Any] | None:
    """Read an optional, JSON-only discovery receipt from a test module."""

    hook = namespace.get("wmi_receipt_metadata")
    if hook is None:
        return None
    if not callable(hook):
        raise RuntimeError(f"{source} wmi_receipt_metadata is not callable")
    payload = hook()
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) for key in payload
    ):
        raise RuntimeError(
            f"{source} wmi_receipt_metadata must return a string-keyed dictionary"
        )
    try:
        encoded = json.dumps(
            payload, allow_nan=False, ensure_ascii=False, sort_keys=True
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"{source} wmi_receipt_metadata is not strict JSON: {exc}"
        ) from exc
    normalized = json.loads(encoded)
    assert isinstance(normalized, dict)
    return normalized


def _run(
    tests: tuple[tuple[str, tuple[str, ...]], ...],
    suite: str,
) -> dict[str, Any]:
    _install_pytest_raises_stub()
    rows: list[dict[str, Any]] = []
    source_metadata: dict[str, dict[str, Any]] = {}
    suite_started = time.perf_counter()
    for source, names in tests:
        namespace = run_path(str(TEST_ROOT / source))
        for name in names:
            test = namespace.get(name)
            if not callable(test):
                raise RuntimeError(f"missing selected test {source}::{name}")
            started = time.perf_counter()
            print(f"WMI START {source}::{name}", flush=True)
            try:
                test()
            except BaseException as exc:  # Preserve a complete audit receipt.
                elapsed = time.perf_counter() - started
                rows.append(
                    {
                        "duration_seconds": elapsed,
                        "error": f"{type(exc).__name__}: {exc}",
                        "name": f"{source}::{name}",
                        "status": "failed",
                        "traceback": traceback.format_exc(),
                    }
                )
                print(f"WMI FAIL  {source}::{name} ({elapsed:.3f}s)", flush=True)
                # Capacity-policy failure is an expected fail-closed outcome
                # for discovery runs. Preserve any metrics already cached by
                # the source module before returning the original failure.
                hook_name = f"{source}::wmi_receipt_metadata"
                metadata_started = time.perf_counter()
                try:
                    metadata = _receipt_metadata(source, namespace)
                except BaseException as metadata_exc:
                    metadata_elapsed = time.perf_counter() - metadata_started
                    rows.append(
                        {
                            "duration_seconds": metadata_elapsed,
                            "error": (
                                f"{type(metadata_exc).__name__}: {metadata_exc}"
                            ),
                            "name": hook_name,
                            "status": "failed",
                            "traceback": traceback.format_exc(),
                        }
                    )
                    print(
                        f"WMI FAIL  {hook_name} ({metadata_elapsed:.3f}s)",
                        flush=True,
                    )
                else:
                    if metadata is not None:
                        source_metadata[source] = metadata
                        print(f"WMI META  {source}", flush=True)
                return _report(
                    rows, source_metadata, suite_started, "failed", suite
                )
            elapsed = time.perf_counter() - started
            rows.append(
                {
                    "duration_seconds": elapsed,
                    "error": None,
                    "name": f"{source}::{name}",
                    "status": "passed",
                    "traceback": None,
                }
            )
            print(f"WMI PASS  {source}::{name} ({elapsed:.3f}s)", flush=True)
        hook_name = f"{source}::wmi_receipt_metadata"
        started = time.perf_counter()
        try:
            metadata = _receipt_metadata(source, namespace)
        except BaseException as exc:
            elapsed = time.perf_counter() - started
            rows.append(
                {
                    "duration_seconds": elapsed,
                    "error": f"{type(exc).__name__}: {exc}",
                    "name": hook_name,
                    "status": "failed",
                    "traceback": traceback.format_exc(),
                }
            )
            print(f"WMI FAIL  {hook_name} ({elapsed:.3f}s)", flush=True)
            return _report(rows, source_metadata, suite_started, "failed", suite)
        if metadata is not None:
            source_metadata[source] = metadata
            print(f"WMI META  {source}", flush=True)
    return _report(rows, source_metadata, suite_started, "passed", suite)


def _report(
    rows: list[dict[str, Any]],
    source_metadata: dict[str, dict[str, Any]],
    suite_started: float,
    status: str,
    suite: str,
) -> dict[str, Any]:
    return {
        "duration_seconds": time.perf_counter() - suite_started,
        "format": "peano-qr-wmi-replay",
        "host": platform.node(),
        "local_commit": _identity("PEANO_QR_LOCAL_COMMIT", COMMIT_PATTERN),
        "local_dirty": os.environ.get("PEANO_QR_LOCAL_DIRTY") == "true",
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "requested_resources": _requested_resources(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "snapshot_sha256": _identity("PEANO_QR_SNAPSHOT_SHA256", SNAPSHOT_PATTERN),
        "source_metadata": source_metadata,
        "status": status,
        "suite": suite,
        "tests": rows,
        "version": 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--suite", choices=tuple(TEST_SUITES), default="full")
    args = parser.parse_args()
    if args.list:
        print("\n".join(_selected_tests(TEST_SUITES[args.suite])))
        return 0
    if args.report is None:
        parser.error("--report is required unless --list is used")
    payload = _run(TEST_SUITES[args.suite], args.suite)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
