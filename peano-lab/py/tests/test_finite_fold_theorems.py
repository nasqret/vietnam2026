"""Admission checks for the first checked Repeat/Pow finite-fold tranche."""

from __future__ import annotations

from dataclasses import fields

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import MAX_USE_CERTIFICATE_NODES, MAX_USE_PROOF_DEPTH
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.finite_fold_surface import (
    POWER_EXISTS,
    POWER_FUNCTIONAL,
    POWER_SUCCESSOR_DECOMPOSE,
    POWER_ZERO,
    REPEAT_EXISTS,
    power_relation,
)
from peano_lab.library.theorems import (
    FINITE_FOLD_THEOREMS,
    _specs_by_name,
    replay,
)


EXPECTED_METRICS = (
    ("beta_repeat_empty", 42, 16),
    ("beta_repeat_succ_extend", 29_224, 81),
    ("beta_repeat_exists", 29_322, 83),
    ("beta_repeat_entry_eq", 1_144, 60),
    ("beta_repeat_transport_entry", 1_191, 61),
    ("pow_exists", 59_836, 88),
    ("pow_zero", 1_224, 61),
    ("pow_functional", 2_705, 63),
    ("pow_successor_decompose", 2_541, 63),
)

PUBLIC_STATEMENTS = {
    "beta_repeat_exists": REPEAT_EXISTS,
    "pow_exists": POWER_EXISTS,
    "pow_zero": POWER_ZERO,
    "pow_functional": POWER_FUNCTIONAL,
    "pow_successor_decompose": POWER_SUCCESSOR_DECOMPOSE,
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
    for spec in FINITE_FOLD_THEOREMS:
        theorem = replay(spec.name)
        assert check((), theorem.certificate, theorem.formula)
        nodes, depth = proof_metrics(theorem.certificate)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_finite_fold_tranche_replays_deterministically_and_constructively() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert first == EXPECTED_METRICS
    assert second == first
    assert all(nodes <= MAX_USE_CERTIFICATE_NODES for _, nodes, _ in first)
    assert all(depth <= MAX_USE_PROOF_DEPTH for _, _, depth in first)


def test_public_contracts_are_the_exact_hygienic_surface_formulas() -> None:
    specs = {spec.name: spec for spec in FINITE_FOLD_THEOREMS}
    assert tuple(specs) == tuple(name for name, _, _ in EXPECTED_METRICS)
    for name, statement in PUBLIC_STATEMENTS.items():
        assert specs[name].statement == statement
        assert replay(name).formula == parse_formula(statement)
        assert all(token not in statement for token in ("Pow", "Repeat", "%", "^", "∣"))


def test_power_certificate_rejects_an_inconsistent_nearby_contract() -> None:
    theorem = replay("pow_zero")
    relation = power_relation("a", "e", "n", tag="mutation")
    inconsistent = parse_formula(
        f"forall a e n. e = 0 -> ({relation}) -> n = 0"
    )
    assert not check((), theorem.certificate, inconsistent)
