"""Admission checks for the native QR-0 parity and modulo-four ladder."""

from __future__ import annotations

from dataclasses import fields

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import MAX_USE_CERTIFICATE_NODES, MAX_USE_PROOF_DEPTH
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.theorems import PARITY_THEOREMS, _specs_by_name, replay


EXPECTED_NAMES = (
    "parity_cases",
    "even_odd_exclusive_pointwise",
    "even_not_odd",
    "odd_not_even",
    "successor_odd_of_even",
    "successor_even_of_odd",
    "even_add_even",
    "even_add_odd",
    "odd_add_even",
    "odd_add_odd",
    "even_mul_left",
    "mul_double_right",
    "even_mul_right",
    "odd_mul_odd",
    "odd_half_unique",
    "odd_half_exists_unique",
    "four_mul_eq_double_double",
    "odd_mod4_cases",
    "mod4_one_three_exclusive_pointwise",
    "mod4_one_is_odd",
    "mod4_three_is_odd",
    "prime_ne_two_is_odd",
)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _cold_rows() -> tuple[tuple[str, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for spec in PARITY_THEOREMS:
        theorem = replay(spec.name)
        assert check((), theorem.certificate, theorem.formula)
        nodes, depth = proof_metrics(theorem.certificate)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_parity_ladder_replays_deterministically_and_within_live_limits() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert tuple(spec.name for spec in PARITY_THEOREMS) == EXPECTED_NAMES
    assert second == first
    assert max(nodes for _, nodes, _ in first) == 953
    assert max(depth for _, _, depth in first) == 59
    assert all(nodes <= MAX_USE_CERTIFICATE_NODES for _, nodes, _ in first)
    assert all(depth <= MAX_USE_PROOF_DEPTH for _, _, depth in first)


def test_parity_contracts_are_closed_native_formula_expansions() -> None:
    for spec in PARITY_THEOREMS:
        formula = parse_formula(spec.statement)
        assert replay(spec.name).formula == formula
        assert all(
            token not in spec.statement
            for token in ("Even", "Odd", "Prime", "%", "^", "∣")
        )


def test_parity_and_mod4_certificates_reject_nearby_false_mutations() -> None:
    parity = replay("parity_cases")
    bad_parity = parse_formula(
        "forall n. exists k. n = 2 * k \\/ n = 2 * k + 2"
    )
    assert not check((), parity.certificate, bad_parity)

    mod4 = replay("odd_mod4_cases")
    bad_mod4 = parse_formula(
        "forall n. (exists h. n = 2 * h + 1) -> "
        "(exists a. n = 4 * a + 1) \\/ exists b. n = 4 * b + 2"
    )
    assert not check((), mod4.certificate, bad_mod4)

