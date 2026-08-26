"""Independent admission audit for finite-product reindex support rungs."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.finite_product_reindex_support import (
    aligned_prefix,
    aligned_successor_prefix,
    make_finite_product_reindex_support_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These are exact receipts from
# genuinely cold isolated replays, including closed dependency certificates.
EXPECTED = {
    "finite_fixed_last_prefix_bounded": (409, 24, 294, 301, 8, 16),
    "beta_reindex_alignment_swap_last": (3_057, 63, 1_212, 1_267, 56, 80),
}

EXPECTED_DEPENDENCIES = {
    "finite_fixed_last_prefix_bounded": (
        "finite_bounded_prefix_without_top",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "beta_reindex_alignment_swap_last": (
        "beta_prefix_swap_last_reflect",
        "beta_at_unique",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "finite_fixed_last_prefix_bounded": (
        "b6cfeb72c9bf4606284b57cd6480de28449533d780ed3dfb506d64cb6b90d2d5"
    ),
    "beta_reindex_alignment_swap_last": (
        "3feb5dbe3cc3478b0098ff68d63d8eefd7d9264d0c9ee98db997fd1bbf4d8e7a"
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
    specs = make_finite_product_reindex_support_theorems(TheoremSpec)
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


def test_reindex_support_replays_twice_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_reindex_support_contracts_are_exact_closed_expanded_pa() -> None:
    specs = make_finite_product_reindex_support_theorems(TheoremSpec)
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
            for token in (
                "AlignedPrefix(",
                "BetaAt(",
                "BoundedPrefix(",
                "InjectivePrefix(",
                "Permutation(",
                "Product(",
                "%",
                "^",
                "∣",
            )
        )


def test_alignment_helpers_are_hygienic_alpha_stable_and_audited() -> None:
    prefix = aligned_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="audit_prefix"
    )
    successor = aligned_successor_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="audit_successor"
    )
    for source in (prefix, successor):
        _, free_names = parse_formula_with_names(source)
        assert set(free_names) == {"r", "s", "b", "c", "z", "d", "n"}

    assert "= n" in prefix
    assert "= S n" in successor
    alpha_prefix = aligned_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="alpha_prefix"
    )
    alpha_successor = aligned_successor_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="alpha_successor"
    )
    assert parse_formula(prefix) == parse_formula(alpha_prefix)
    assert parse_formula(successor) == parse_formula(alpha_successor)

    with pytest.raises(ValueError, match="Peano identifier"):
        aligned_prefix(
            "r", "s", "b", "c", "z", "d", "n + 1", tag="bad_length"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        aligned_prefix(
            "fpr_i_capture",
            "s",
            "b",
            "c",
            "z",
            "d",
            "n",
            tag="capture",
        )


def test_reindex_support_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    table = {spec.name: spec for spec in specs}

    bounded = run("finite_fixed_last_prefix_bounded")
    bounded_statement = table["finite_fixed_last_prefix_bounded"].statement
    bounded_marker = (
        "fp_gap_fixed_last_bounded_prefix_value + S "
        "fp_value_fixed_last_bounded_prefix = n"
    )
    assert bounded_statement.count(bounded_marker) == 1
    bounded_mutation = parse_formula(
        bounded_statement.replace(bounded_marker, bounded_marker + " + 0")
    )
    assert not check((), bounded.certificate, bounded_mutation)

    aligned = run("beta_reindex_alignment_swap_last")
    aligned_statement = table["beta_reindex_alignment_swap_last"].statement
    aligned_marker = (
        "exists ff_q_align_swap_new_target. w = "
        "ff_q_align_swap_new_target"
    )
    assert aligned_statement.count(aligned_marker) == 1
    aligned_mutation = parse_formula(
        aligned_statement.replace(
            aligned_marker,
            "exists ff_q_align_swap_new_target. z = "
            "ff_q_align_swap_new_target",
        )
    )
    assert not check((), aligned.certificate, aligned_mutation)

    assert type(aligned.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        aligned.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, aligned.formula)
