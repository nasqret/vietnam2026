"""Focused native-body audit for the isolated Wilson terminal product bridge."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from peano_lab.library.gauss_magnitude_permutation_candidate import (
    make_gauss_magnitude_permutation_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name
from peano_lab.library.wilson_pair_order_induction_candidate import (
    make_wilson_pair_order_induction_candidate_theorems,
)
from peano_lab.library.wilson_pair_order_paired_iteration_candidate import (
    make_wilson_pair_order_paired_iteration_candidate_theorems,
)
from peano_lab.library.wilson_successor_lift_candidate import (
    make_wilson_successor_lift_candidate_theorems,
)
from peano_lab.library.wilson_terminal_product_candidate import (
    _range_two_prefix_term,
    make_wilson_terminal_product_candidate_theorems,
)


EXPECTED_NAMES = (
    "pair_order_terminal_state_magnitude_range",
    "pair_order_predecessor_range_two_successor_lift_aligned",
    "pair_order_terminal_successor_product_eq_range_two",
    "prime_wilson_terminal_product_package_exists",
)

EXPECTED_DEPENDENCIES = {
    "pair_order_terminal_state_magnitude_range": (
        "one_le_of_ne_zero",
        "le_of_succ_le_succ",
        "le_eq_or_lt",
    ),
    "pair_order_predecessor_range_two_successor_lift_aligned": (
        "beta_magnitude_predecessor_recode_bounded",
        "beta_magnitude_predecessor_recode_reflect",
        "beta_at_unique",
        "beta_range_entry_eq",
        "add_succ_left",
        "zero_add",
    ),
    "pair_order_terminal_successor_product_eq_range_two": (
        "beta_magnitude_predecessor_recode_bounded",
        "beta_magnitude_predecessor_recode_injective",
        "pair_order_predecessor_range_two_successor_lift_aligned",
        "beta_product_permutation_invariant",
    ),
    "prime_wilson_terminal_product_package_exists": (
        "prime_pair_order_paired_terminal_state_exists",
        "pair_order_state_terminal_coverage",
        "paired_pair_order_product_one_exists",
        "pair_order_terminal_state_magnitude_range",
        "beta_magnitude_predecessor_recode_exists",
        "beta_range_exists",
        "beta_product_exists",
        "pair_order_terminal_successor_product_eq_range_two",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "pair_order_terminal_state_magnitude_range": (
        "5f52b4d636387f32b55cf6876bfc7cd118ed59e55227895795f6af8af4c2932e"
    ),
    "pair_order_predecessor_range_two_successor_lift_aligned": (
        "6b7727cb499ba853fbb24fe6404fcffe9d26e7077b216e40317283d9daf66517"
    ),
    "pair_order_terminal_successor_product_eq_range_two": (
        "e01c4bdab6685c6ab5d2d116245379498cc12f6a2a209f939714941e5f7b6277"
    ),
    "prime_wilson_terminal_product_package_exists": (
        "ca86739c1e259749d12ff8d7eb70e9c4d7e416821f857ffa72aeeb7fce5c11aa"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "pair_order_terminal_state_magnitude_range": (3, 54, 80, 30, 80, 79, 0),
    "pair_order_predecessor_range_two_successor_lift_aligned": (
        6,
        86,
        152,
        42,
        152,
        151,
        0,
    ),
    "pair_order_terminal_successor_product_eq_range_two": (
        4,
        67,
        79,
        39,
        79,
        78,
        0,
    ),
    "prime_wilson_terminal_product_package_exists": (
        8,
        144,
        188,
        65,
        188,
        187,
        0,
    ),
}

_DEPENDENCY_FACTORIES = (
    make_gauss_magnitude_permutation_candidate_theorems,
    make_finite_product_reindex_candidate,
    make_wilson_pair_order_induction_candidate_theorems,
    make_wilson_pair_order_paired_iteration_candidate_theorems,
    make_wilson_successor_lift_candidate_theorems,
)

_BODY_CPU_LIMIT_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_terminal_product_candidate_theorems(TheoremSpec)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in _DEPENDENCY_FACTORIES:
        core.update((item.name, item) for item in factory(TheoremSpec))
    return core


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Wilson terminal body replay exceeded {seconds}s CPU")

    previous_handler = signal.signal(signal.SIGPROF, expired)
    previous_timer = signal.getitimer(signal.ITIMER_PROF)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_PROF, *previous_timer)


def test_wilson_terminal_product_contracts_are_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "wilson_terminal_product_candidate" not in registry_source


def test_wilson_terminal_product_expands_hygienically_to_native_pa() -> None:
    left = _range_two_prefix_term(
        "b", "c", "l", tag="terminal_audit_left", avoid=("b", "c", "l")
    )
    right = _range_two_prefix_term(
        "b", "c", "l", tag="terminal_audit_right", avoid=("b", "c", "l")
    )
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, helper_free_names = parse_formula_with_names(left)
    assert set(helper_free_names) == {"b", "c", "l"}

    forbidden_surface_tokens = (
        "AdjacentUnitPairs(",
        "Aligned(",
        "BetaAt(",
        "InversePrefix(",
        "MagnitudeRange(",
        "ModEq(",
        "PairOrderState(",
        "PairedInverseWitness(",
        "PredecessorRecode(",
        "Prime(",
        "Product(",
        "Range(",
        "SuccessorLift(",
        "%",
        "^",
        "<",
        "∣",
        "≡",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)
        assert all("DNE" not in command for command in item.script)


def test_wilson_terminal_product_bodies_kernel_check_within_cpu_limit() -> None:
    started = perf_counter()
    with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_explicit_dependency_core()
        )
    elapsed = perf_counter() - started

    observed = {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS

    print(
        "WILSON TERMINAL BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
