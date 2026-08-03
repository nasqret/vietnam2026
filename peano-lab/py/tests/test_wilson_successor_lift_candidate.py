"""Focused static and body audit for the isolated Wilson successor lift."""

from __future__ import annotations

import signal
from contextlib import contextmanager

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_residue_map_candidate import (
    make_fermat_residue_map_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name
from peano_lab.library.wilson_pair_order_paired_iteration_candidate import (
    make_wilson_pair_order_paired_iteration_candidate_theorems,
)
from peano_lab.library.wilson_pair_product_candidate import (
    make_wilson_pair_product_candidate_theorems,
)
from peano_lab.library.wilson_successor_lift_candidate import (
    make_wilson_successor_lift_candidate_theorems,
    successor_lift_prefix,
)


EXPECTED_NAMES = (
    "pair_order_successor_lift_exists",
    "paired_successor_lift_adjacent_units",
    "paired_pair_order_factor_code_exists",
    "paired_pair_order_product_one_exists",
)

EXPECTED_DEPENDENCIES = {
    "pair_order_successor_lift_exists": ("beta_successor_lift_exists",),
    "paired_successor_lift_adjacent_units": (
        "pair_index_left_below_double",
        "pair_index_right_below_double",
        "beta_at_unique",
    ),
    "paired_pair_order_factor_code_exists": (
        "pair_order_successor_lift_exists",
        "paired_successor_lift_adjacent_units",
    ),
    "paired_pair_order_product_one_exists": (
        "paired_pair_order_factor_code_exists",
        "beta_product_exists",
        "beta_adjacent_unit_pairs_product_one",
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "pair_order_successor_lift_exists": (1, 7, 17, 11, 17, 16, 0),
    "paired_successor_lift_adjacent_units": (3, 106, 124, 38, 124, 123, 0),
    "paired_pair_order_factor_code_exists": (2, 35, 41, 31, 41, 40, 0),
    "paired_pair_order_product_one_exists": (3, 52, 65, 32, 65, 64, 0),
}

_BODY_PREFLIGHT_SECONDS = 10


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_successor_lift_candidate_theorems(TheoremSpec)


def _body_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    support = (
        make_fermat_residue_map_candidate_theorems(TheoremSpec)
        + make_wilson_pair_order_paired_iteration_candidate_theorems(TheoremSpec)
        + make_wilson_pair_product_candidate_theorems(TheoremSpec)
    )
    core.update((spec.name, spec) for spec in support)
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"candidate body preflight exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_wilson_successor_lift_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert all(spec.name not in _specs_by_name() for spec in first)


def test_wilson_successor_lift_expands_hygienically_to_native_pa() -> None:
    left = successor_lift_prefix("b", "c", "f", "g", "l", tag="audit_left")
    right = successor_lift_prefix("b", "c", "f", "g", "l", tag="audit_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"b", "c", "f", "g", "l"}

    forbidden = (
        "SuccessorLift(",
        "AdjacentUnitPairs(",
        "PairOrderState(",
        "BetaAt(",
        "Product(",
        "ModEq(",
        "<",
        "%",
        "^",
        "∣",
    )
    for spec in _candidate_specs():
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert formula == parse_formula(spec.statement) == _closed_formula(spec.statement)
        assert len(spec.statement) < 8_192
        assert all(token not in spec.statement for token in forbidden)
        assert all("DNE" not in command for command in spec.script)


def test_wilson_successor_lift_bodies_kernel_check_before_deadline() -> None:
    with _body_deadline(_BODY_PREFLIGHT_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_body_core())
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

