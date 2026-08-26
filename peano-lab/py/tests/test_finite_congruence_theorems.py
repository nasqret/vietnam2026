"""Independent admission audit for finite-fold congruence transport."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.finite_congruence_theorems import (
    make_finite_congruence_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references
EXPECTED = {
    "beta_product_pointwise_mod_congruent": (4_129, 64, 1_198, 1_254, 57),
    "beta_sum_pointwise_mod_congruent": (2_994, 64, 1_079, 1_124, 46),
}


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _fresh_replayer():
    specs = make_finite_congruence_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            target = Imp(_closed_formula(core[dependency].statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)

        body = certificate
        for _ in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = replay(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, run


def _rows() -> tuple[tuple[str, int, int, int, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused))
    return tuple(rows)


def test_finite_congruence_tranche_replays_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_finite_congruence_contracts_are_closed_expanded_pa_formulas() -> None:
    specs = make_finite_congruence_theorems(TheoremSpec)
    assert tuple(spec.name for spec in specs) == tuple(EXPECTED)
    for spec in specs:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < 4_000
        assert all(
            token not in spec.statement
            for token in (
                "BetaAt(",
                "Product(",
                "Sum(",
                "ModEq(",
                "%",
                "^",
                "∣",
            )
        )


def test_product_transport_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("beta_product_pointwise_mod_congruent")
    statement = next(
        spec.statement
        for spec in specs
        if spec.name == "beta_product_pointwise_mod_congruent"
    )
    marker = "= q + m * fc_v_pv"
    assert statement.count(marker) == 1
    inconsistent = parse_formula(statement.replace(marker, "= S q + m * fc_v_pv"))
    assert not check((), theorem.certificate, inconsistent)

    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, theorem.formula)

