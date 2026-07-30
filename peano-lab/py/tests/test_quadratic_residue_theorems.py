"""Admission checks for the constructive native QR entrance gates."""

from __future__ import annotations

from dataclasses import fields

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import MAX_USE_CERTIFICATE_NODES, MAX_USE_PROOF_DEPTH
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.quadratic_residue_surface import (
    MOD_EQ_DECIDABLE_NONZERO,
    QUADRATIC_RESIDUE_BOUNDED_DECIDABLE_NONZERO,
    QUADRATIC_RESIDUE_BOUNDED_EQUIV,
    QUADRATIC_RESIDUE_DECIDABLE_NONZERO,
    QUADRATIC_RESIDUE_SEARCH_UP_TO,
)
from peano_lab.library.theorems import (
    QUADRATIC_RESIDUE_THEOREMS,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "mod_eq_decidable_from_remainders",
    "mod_eq_decidable_nonzero",
    "quadratic_residue_search_up_to",
    "quadratic_residue_bounded_decidable_nonzero",
    "quadratic_residue_bounded_equiv",
    "quadratic_residue_decidable_nonzero",
)

PUBLIC_STATEMENTS = {
    "mod_eq_decidable_nonzero": MOD_EQ_DECIDABLE_NONZERO,
    "quadratic_residue_search_up_to": QUADRATIC_RESIDUE_SEARCH_UP_TO,
    "quadratic_residue_bounded_decidable_nonzero": (
        QUADRATIC_RESIDUE_BOUNDED_DECIDABLE_NONZERO
    ),
    "quadratic_residue_bounded_equiv": QUADRATIC_RESIDUE_BOUNDED_EQUIV,
    "quadratic_residue_decidable_nonzero": QUADRATIC_RESIDUE_DECIDABLE_NONZERO,
}


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
    for spec in QUADRATIC_RESIDUE_THEOREMS:
        theorem = replay(spec.name)
        assert check((), theorem.certificate, theorem.formula)
        nodes, depth = proof_metrics(theorem.certificate)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_quadratic_residue_gates_replay_deterministically_and_constructively() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert tuple(spec.name for spec in QUADRATIC_RESIDUE_THEOREMS) == EXPECTED_NAMES
    assert second == first
    assert max(nodes for _, nodes, _ in first) == 4_737
    assert max(depth for _, _, depth in first) == 71
    assert all(nodes <= MAX_USE_CERTIFICATE_NODES for _, nodes, _ in first)
    assert all(depth <= MAX_USE_PROOF_DEPTH for _, _, depth in first)


def test_public_gate_contracts_are_the_exact_hygienic_surface_formulas() -> None:
    specs = {spec.name: spec for spec in QUADRATIC_RESIDUE_THEOREMS}
    for name, statement in PUBLIC_STATEMENTS.items():
        assert specs[name].statement == statement
        assert replay(name).formula == parse_formula(statement)
        assert all(
            token not in statement
            for token in ("QRes", "ModEq", "Prime", "%", "^", "∣")
        )


def test_decision_certificate_rejects_an_inconsistent_nearby_contract() -> None:
    theorem = replay("mod_eq_decidable_nonzero")
    inconsistent = parse_formula(
        "forall p a b. ~(p = 0) -> "
        "(exists u v. a + p * u = b + p * v) /\\ "
        "~(exists u v. a + p * u = b + p * v)"
    )
    assert not check((), theorem.certificate, inconsistent)

