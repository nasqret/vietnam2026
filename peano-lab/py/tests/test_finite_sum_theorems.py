"""Isolated admission checks for the native beta-coded Sum tranche."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.state import start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.finite_fold_surface import (
    BETA_SUM_EXISTS,
    BETA_SUM_FUNCTIONAL,
)
from peano_lab.library.finite_sum_theorems import make_finite_sum_theorems
from peano_lab.library.theorems import (
    CheckedTheorem,
    FINITE_SUM_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


SUM_THEOREMS = make_finite_sum_theorems(TheoremSpec)
SUM_TABLE = {spec.name: spec for spec in SUM_THEOREMS}

EXPECTED_METRICS = (
    ("beta_prefix_sum_trace_exists", 29_985, 85),
    ("beta_sum_exists", 30_491, 86),
    ("beta_sum_trace_functional", 1_382, 60),
    ("beta_sum_functional", 1_439, 61),
    ("beta_sum_exists_unique", 31_979, 87),
    ("beta_sum_zero", 1_171, 60),
    ("beta_sum_succ_decompose", 1_257, 62),
)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@lru_cache(maxsize=None)
def _replay_sum(name: str) -> CheckedTheorem:
    spec = SUM_TABLE[name]
    formula = _closed_formula(spec.statement)
    target = formula
    for dependency in reversed(spec.dependencies):
        dependency_statement = (
            SUM_TABLE[dependency].statement
            if dependency in SUM_TABLE
            else replay(dependency).spec.statement
        )
        target = Imp(_closed_formula(dependency_statement), target)

    state = start(target)
    for dependency in spec.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in spec.script:
        tactic, args = _primitive(command)
        state = apply_tactic(state, tactic, args)
    certificate = checked_final(state, target)

    body = certificate
    for _dependency in spec.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    for dependency in reversed(spec.dependencies):
        checked_dependency = (
            _replay_sum(dependency)
            if dependency in SUM_TABLE
            else replay(dependency)
        )
        body = Cut(
            checked_dependency.formula,
            formula,
            checked_dependency.certificate,
            body,
        )

    assert check((), body, formula)
    return CheckedTheorem(spec, formula, body, proof_metrics(body)[0])


def _cold_rows() -> tuple[tuple[str, int, int], ...]:
    _replay_sum.cache_clear()
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for spec in SUM_THEOREMS:
        theorem = _replay_sum(spec.name)
        assert check((), theorem.certificate, theorem.formula)
        nodes, depth = proof_metrics(theorem.certificate)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_sum_tranche_replays_deterministically_and_constructively() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert first == EXPECTED_METRICS
    assert second == first
    assert all(nodes <= MAX_USE_CERTIFICATE_NODES for _, nodes, _ in first)
    assert all(depth <= MAX_USE_PROOF_DEPTH for _, _, depth in first)


def test_sum_public_contracts_are_exact_expanded_surface_formulas() -> None:
    assert tuple(SUM_TABLE) == tuple(name for name, _, _ in EXPECTED_METRICS)
    assert SUM_TABLE["beta_sum_exists"].statement == BETA_SUM_EXISTS
    assert SUM_TABLE["beta_sum_functional"].statement == BETA_SUM_FUNCTIONAL
    for spec in SUM_THEOREMS:
        assert _replay_sum(spec.name).formula == parse_formula(spec.statement)
        assert all(token not in spec.statement for token in ("Sum", "%", "^", "∣"))


def test_sum_tranche_has_stable_registry_bindings_and_lookup() -> None:
    assert FINITE_SUM_THEOREMS == SUM_THEOREMS
    for spec in FINITE_SUM_THEOREMS:
        assert get(spec.name) is spec
        assert replay(spec.name).formula == _replay_sum(spec.name).formula


def test_sum_certificate_rejects_an_inconsistent_nearby_contract() -> None:
    theorem = _replay_sum("beta_sum_zero")
    statement = SUM_TABLE["beta_sum_zero"].statement
    assert statement.endswith("n = 0")
    inconsistent = parse_formula(statement.removesuffix("n = 0") + "n = 1")
    assert not check((), theorem.certificate, inconsistent)
