"""Independent admission audit for the isolated relational-factorial tranche."""

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
from peano_lab.library.finite_factorial_theorems import (
    FACTORIAL_EXISTS,
    FACTORIAL_FUNCTIONAL,
    FACTORIAL_SUCCESSOR_DECOMPOSE,
    FACTORIAL_ZERO,
    factorial_relation,
    make_finite_factorial_theorems,
)
from peano_lab.library.theorems import (
    FINITE_FACTORIAL_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These values are the
# deterministic admission receipts from two genuinely cold isolated replays.
EXPECTED = {
    "factorial_exists": (59_841, 88, 4_907, 5_147, 241, 1_795),
    "factorial_functional": (2_704, 63, 1_110, 1_149, 40, 71),
    "factorial_zero": (1_223, 61, 794, 830, 37, 32),
    "factorial_succ_decompose": (2_594, 63, 891, 934, 44, 74),
}

EXPECTED_DEPENDENCIES = {
    "factorial_exists": ("beta_range_exists", "beta_product_exists"),
    "factorial_functional": (
        "beta_range_transport_entry",
        "beta_product_transport_prefix",
        "beta_product_functional",
    ),
    "factorial_zero": ("beta_product_zero",),
    "factorial_succ_decompose": (
        "beta_product_succ_decompose",
        "beta_range_entry_eq",
        "le_refl",
        "le_succ",
        "add_succ_left",
        "zero_add",
    ),
}

PUBLIC_STATEMENTS = {
    "factorial_exists": FACTORIAL_EXISTS,
    "factorial_functional": FACTORIAL_FUNCTIONAL,
    "factorial_zero": FACTORIAL_ZERO,
    "factorial_succ_decompose": FACTORIAL_SUCCESSOR_DECOMPOSE,
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
    specs = make_finite_factorial_theorems(TheoremSpec)
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


def _rows() -> tuple[tuple[str, int, int, int, int, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused, cuts))
    return tuple(rows)


def test_factorial_tranche_replays_twice_deterministically_and_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_factorial_contracts_are_exact_closed_expanded_pa_surfaces() -> None:
    specs = make_finite_factorial_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert {name: spec.dependencies for name, spec in table.items()} == (
        EXPECTED_DEPENDENCIES
    )
    for name, statement in PUBLIC_STATEMENTS.items():
        spec = table[name]
        assert spec.statement == statement
        assert _closed_formula(statement) == parse_formula(statement)
        assert all(
            token not in statement
            for token in (
                "BetaAt(",
                "Factorial(",
                "Product(",
                "Range(",
                "%",
                "^",
                "∣",
            )
        )

    sample = factorial_relation("n", "z", tag="surface")
    assert "1 + ff_i_surface_range" in sample
    assert "one" not in sample


def test_factorial_registry_bindings_and_public_replay_are_exact() -> None:
    expected = make_finite_factorial_theorems(TheoremSpec)

    assert FINITE_FACTORIAL_THEOREMS == expected
    for public, rebuilt in zip(FINITE_FACTORIAL_THEOREMS, expected, strict=True):
        assert public == rebuilt
        assert get(public.name) is public
        theorem = replay(public.name)
        assert theorem.formula == parse_formula(public.statement)
        assert check((), theorem.certificate, theorem.formula)


def test_factorial_successor_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("factorial_succ_decompose")
    statement = next(
        spec.statement
        for spec in specs
        if spec.name == "factorial_succ_decompose"
    )
    marker = "z = r * S n"
    assert statement.count(marker) == 1
    inconsistent = parse_formula(statement.replace(marker, "z = S (r * S n)"))
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
