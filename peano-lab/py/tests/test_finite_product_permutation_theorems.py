"""Independent admission audit for beta-coded finite-product permutations."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256

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
from peano_lab.library.finite_product_permutation_theorems import (
    make_finite_product_permutation_theorems,
)
from peano_lab.library.theorems import (
    FINITE_PRODUCT_PERMUTATION_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These are exact receipts from
# genuinely cold isolated replays.
EXPECTED = {
    "beta_prefix_replace_reflect": (1_735, 62, 1_011, 1_065, 55, 48),
    "beta_product_replace_balance": (4_780, 66, 1_552, 1_607, 56, 130),
    "beta_product_swap_last_invariant": (7_439, 67, 1_685, 1_745, 61, 205),
}

EXPECTED_DEPENDENCIES = {
    "beta_prefix_replace_reflect": (
        "eq_decidable",
        "beta_at_exists",
        "beta_at_unique",
    ),
    "beta_product_replace_balance": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_lt_succ_eq_or_lt",
        "beta_product_succ_decompose",
        "beta_product_transport_prefix",
        "beta_product_functional",
        "beta_at_unique",
        "mul_assoc",
        "mul_comm",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "beta_product_swap_last_invariant": (
        "beta_product_replace_balance",
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "beta_prefix_replace_reflect": (
        "c0496b2821ca285b28e61cca5e594a4c0e18065b7793f66db39293a81a96d158"
    ),
    "beta_product_replace_balance": (
        "7ea5a5b5d4b956523749fa76765d8e3db95f775cce76f3f4e1c254e831f4ed99"
    ),
    "beta_product_swap_last_invariant": (
        "a23f0b2f4451b4e423b9f15132ac02b6a035ce4d06f8eb95d744977109272465"
    ),
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
    specs = make_finite_product_permutation_theorems(TheoremSpec)
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


def test_product_permutation_replays_twice_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_product_permutation_contracts_are_exact_closed_expanded_pa() -> None:
    specs = make_finite_product_permutation_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert {name: item.dependencies for name, item in table.items()} == (
        EXPECTED_DEPENDENCIES
    )
    assert {
        name: sha256(item.statement.encode()).hexdigest()
        for name, item in table.items()
    } == EXPECTED_STATEMENT_SHA256
    for item in specs:
        assert _closed_formula(item.statement) == parse_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(
            token not in item.statement
            for token in ("BetaAt(", "Product(", "Permutation(", "%", "^", "∣")
        )


def test_product_permutation_has_stable_registry_bindings_and_lookup() -> None:
    specs = make_finite_product_permutation_theorems(TheoremSpec)
    assert FINITE_PRODUCT_PERMUTATION_THEOREMS == specs
    for spec in FINITE_PRODUCT_PERMUTATION_THEOREMS:
        assert get(spec.name) is spec
        assert replay(spec.name).formula == _closed_formula(spec.statement)


def test_swap_last_certificate_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("beta_product_swap_last_invariant")
    statement = next(
        item.statement
        for item in specs
        if item.name == "beta_product_swap_last_invariant"
    )
    assert statement.endswith("p = q")
    mutated_contract = parse_formula(statement.removesuffix("p = q") + "q = p")
    assert not check((), theorem.certificate, mutated_contract)

    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, theorem.formula)
