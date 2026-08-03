"""Independent admission audit for the beta-coded Gauss half-range."""

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
from peano_lab.library.gauss_half_range import make_gauss_half_range_theorems
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
    "beta_range_injective": (1_338, 61, 766, 803, 38),
    "beta_half_range_entry_bounds": (1_585, 61, 850, 895, 46),
    "beta_half_range_mod_eq_value": (2_603, 62, 941, 988, 48),
    "beta_half_range_mod_injective": (4_001, 63, 1_052, 1_101, 50),
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
    specs = make_gauss_half_range_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            dependency_spec = local.get(dependency) or core[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

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
            checked_dependency = (
                run(dependency) if dependency in local else replay(dependency)
            )
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


def test_gauss_half_range_replays_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_gauss_half_range_contracts_are_closed_expanded_native_pa() -> None:
    specs = make_gauss_half_range_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert max((len(spec.statement), spec.name) for spec in specs) == (
        747,
        "beta_range_injective",
    )
    bounds = table["beta_half_range_entry_bounds"].statement
    assert "p = 2 * h + 1" in bounds
    assert "~(x = 0)" in bounds
    assert bounds.endswith("gh_lt_half_value + S x = p))")
    assert table["beta_half_range_mod_eq_value"].statement.endswith("-> x = y")
    assert table["beta_half_range_mod_injective"].statement.endswith("-> i = j")

    for spec in specs:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < 8_192
        assert all(
            token not in spec.statement
            for token in (
                "Range(",
                "BetaAt(",
                "ModEq(",
                "<",
                "%",
                "^",
                "∣",
            )
        )


def test_gauss_half_range_rejects_false_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    table = {spec.name: spec for spec in specs}

    injective = run("beta_range_injective")
    injective_statement = table["beta_range_injective"].statement
    assert injective_statement.endswith("-> i = j")
    false_injective = parse_formula(
        injective_statement.removesuffix("i = j") + "i = 0"
    )
    assert not check((), injective.certificate, false_injective)

    bounds = run("beta_half_range_entry_bounds")
    bounds_statement = table["beta_half_range_entry_bounds"].statement
    assert bounds_statement.count("p = 2 * h + 1") == 1
    false_bounds = parse_formula(
        bounds_statement.replace("p = 2 * h + 1", "p = 2 * h")
    )
    assert not check((), bounds.certificate, false_bounds)

    capstone = run("beta_half_range_mod_injective")
    assert type(capstone.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        capstone.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, capstone.formula)

