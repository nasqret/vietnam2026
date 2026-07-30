"""Independent admission audit for exact beta-product reindex invariance."""

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
from peano_lab.library.finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from peano_lab.library.finite_product_reindex_support import (
    make_finite_product_reindex_support_theorems,
)
from peano_lab.library.theorems import (
    FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These are exact receipts from
# genuinely cold isolated replays whose support and candidate dependencies are
# independently closed with self-contained Cut nodes.
EXPECTED = {
    "beta_product_reindex_fixed_last": (2_488, 63, 869, 909, 41, 69),
    "beta_product_permutation_invariant": (
        124_847,
        96,
        8_400,
        8_727,
        328,
        3_674,
    ),
}

EXPECTED_DEPENDENCIES = {
    "beta_product_reindex_fixed_last": (
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_refl",
    ),
    "beta_product_permutation_invariant": (
        "finite_bounded_injective_surjective",
        "finite_lt_succ_eq_or_lt",
        "finite_fixed_last_prefix_bounded",
        "finite_injective_prefix_succ",
        "beta_prefix_swap_last_from_entries",
        "finite_swap_last_bounded",
        "finite_swap_last_injective",
        "beta_product_swap_last_invariant",
        "beta_product_zero",
        "beta_product_exists",
        "beta_at_exists",
        "beta_at_unique",
        "beta_reindex_alignment_swap_last",
        "beta_product_reindex_fixed_last",
        "le_refl",
        "le_succ",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "beta_product_reindex_fixed_last": (
        "6f1f4125af0a0bae54d1095ecb40a05f6d4ab609178613385c9a5b77f410e051"
    ),
    "beta_product_permutation_invariant": (
        "cde158e9d22685010c99290d6c139ce33e9feb5770fdc7f897fbf876d1ef98f2"
    ),
}

EXPECTED_STATEMENT_LENGTH = {
    "beta_product_reindex_fixed_last": 5_231,
    "beta_product_permutation_invariant": 6_798,
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
    support_specs = make_finite_product_reindex_support_theorems(TheoremSpec)
    candidate_specs = make_finite_product_reindex_candidate(TheoremSpec)
    local = {spec.name: spec for spec in support_specs + candidate_specs}
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

    return candidate_specs, support_specs, run


def _rows() -> tuple[tuple[str, int, int, int, int, int, int], ...]:
    # Both caches are deliberately emptied for every chain.  In particular,
    # the second pass cannot inherit public dependency certificates from the
    # first one.
    replay.cache_clear()
    _specs_by_name.cache_clear()
    candidate_specs, _, run = _fresh_replayer()
    rows = []
    for spec in candidate_specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused, cuts))
    return tuple(rows)


def test_product_reindex_replays_twice_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_product_reindex_contracts_are_exact_closed_expanded_native_pa() -> None:
    specs = make_finite_product_reindex_candidate(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert {name: item.dependencies for name, item in table.items()} == (
        EXPECTED_DEPENDENCIES
    )
    assert {
        name: sha256(item.statement.encode()).hexdigest()
        for name, item in table.items()
    } == EXPECTED_STATEMENT_SHA256
    assert {name: len(item.statement) for name, item in table.items()} == (
        EXPECTED_STATEMENT_LENGTH
    )

    # Every authoring relation has already disappeared from the exact input
    # contract, and every name is quantified before the parser/kernel boundary.
    for item in specs:
        assert _closed_formula(item.statement) == parse_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(
            token not in item.statement
            for token in (
                "AlignedPrefix(",
                "BetaAt(",
                "BoundedPrefix(",
                "InjectivePrefix(",
                "Permutation(",
                "Product(",
                "SurjectivePrefix(",
                "%",
                "^",
                "∣",
            )
        )


def test_product_reindex_authoring_is_deterministic_and_support_is_public() -> None:
    first = make_finite_product_reindex_candidate(TheoremSpec)
    second = make_finite_product_reindex_candidate(TheoremSpec)
    assert second == first

    support = make_finite_product_reindex_support_theorems(TheoremSpec)
    assert FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS == support
    for spec in FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS:
        assert get(spec.name) is spec
        assert replay(spec.name).formula == _closed_formula(spec.statement)


def test_product_reindex_rejects_false_contract_and_first_cut_mutation() -> None:
    specs, _, run = _fresh_replayer()
    table = {spec.name: spec for spec in specs}

    for name in EXPECTED:
        theorem = run(name)
        statement = table[name].statement
        assert statement.endswith("p = q")
        false_contract = parse_formula(
            statement.removesuffix("p = q") + "p = S q"
        )
        assert not check((), theorem.certificate, false_contract)

    capstone = run("beta_product_permutation_invariant")
    assert type(capstone.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_first_cut = replace(
        capstone.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_first_cut, capstone.formula)
