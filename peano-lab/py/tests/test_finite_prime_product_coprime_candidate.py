"""Focused static and body audit for generic prime-product coprimality."""

from __future__ import annotations

import signal
from contextlib import contextmanager

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.finite_prime_product_coprime_candidate import (
    make_finite_prime_product_coprime_candidate_theorems,
    positive_below_prime_prefix,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = ("prime_positive_bounded_product_coprime",)

EXPECTED_DEPENDENCIES = {
    "prime_positive_bounded_product_coprime": (
        "divisor_le_nonzero",
        "lt_not_le",
        "prime_not_divides_coprime",
        "coprime_symm",
        "beta_product_pointwise_coprime",
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "prime_positive_bounded_product_coprime": (5, 51, 64, 31, 64, 63, 0),
}

_BODY_PREFLIGHT_SECONDS = 10


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_prime_product_coprime_candidate_theorems(TheoremSpec)


def _body_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update(
        (spec.name, spec)
        for spec in make_fermat_residue_product_candidate_theorems(TheoremSpec)
    )
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


def test_prime_product_coprime_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()
    assert second == first
    assert tuple(spec.name for spec in first) == EXPECTED_NAMES
    assert {spec.name: spec.dependencies for spec in first} == EXPECTED_DEPENDENCIES
    assert all(spec.name not in _specs_by_name() for spec in first)


def test_prime_product_coprime_expands_hygienically_to_native_pa() -> None:
    left = positive_below_prime_prefix("b", "c", "l", "p", tag="audit_left")
    right = positive_below_prime_prefix("b", "c", "l", "p", tag="audit_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"b", "c", "l", "p"}

    forbidden = (
        "PositiveBelowPrimePrefix(",
        "PointwiseCoprime(",
        "Prime(",
        "BetaAt(",
        "Product(",
        "Coprime(",
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


def test_prime_product_coprime_body_kernel_checks_before_deadline() -> None:
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

