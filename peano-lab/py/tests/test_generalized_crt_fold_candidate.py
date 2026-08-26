"""Original-kernel and adversarial audit of the constructive finite CRT fold."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
from math import gcd, lcm, prod

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v23
from peano_lab.library import generalized_crt_fold_candidate as candidate
from peano_lab.library.bertrand_primorial_choose_interval_candidate import (
    _pairwise_coprime_prefix_term,
)
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "crt_positive_moduli_prefix_empty",
    "crt_positive_moduli_prefix_drop_last",
    "crt_positive_moduli_prefix_last_nonzero",
    "crt_pairwise_coprime_prefix_drop_last",
    "crt_prefix_solution_empty",
    "crt_prefix_solution_drop_last",
    "crt_prefix_solution_last",
    "crt_prefix_solution_successor_intro",
    "crt_pairwise_coprime_prefix_last",
    "crt_positive_moduli_prefix_product_nonzero",
    "crt_prefix_product_common_multiple",
    "crt_pairwise_coprime_prefix_product_is_lcm",
    "crt_prefix_lcm_unique",
    "crt_prefix_lcm_empty",
    "crt_prefix_lcm_successor_intro",
    "crt_prefix_lcm_exists_unique",
    "crt_pairwise_coprime_prefix_lcm_exists_unique",
    "crt_pairwise_coprime_prefix_product_coprime_last",
    "crt_pairwise_coprime_prefix_solution_exists",
    "crt_prefix_solutions_pointwise_congruent",
    "crt_prefix_solution_transport_common_multiple",
    "crt_prefix_ordered_solutions_gap_multiple",
    "crt_prefix_solutions_congruent_lcm",
    "crt_prefix_solution_class_iff_lcm",
    "crt_prefix_solution_canonical_remainder",
    "crt_canonical_prefix_solution_unique",
    "crt_pairwise_coprime_prefix_canonical_exists_unique",
)
EXPECTED_NAMES_SHA256 = "1d18c793f8521e3b08ec2ea1c2e8e5d9e4e824c58b5366a00415316af6f6b240"
EXPECTED_BODY_NODES = (
    20, 35, 27, 61, 25, 43, 35, 85, 66, 80, 41, 57, 49, 22,
    108, 81, 99, 71, 169, 88, 90, 58, 101, 101, 63, 101, 84,
)
EXPECTED_ROOTS = {
    "crt_prefix_lcm_exists_unique": "09fa610c42ac069677f4fb90f00c6e0780d2b1de843380599e725a9cf19e1175",
    "crt_pairwise_coprime_prefix_solution_exists": "6e61d9a848010dc5857fdacbc8efc3973e160a997a421a17100a867e1c501e68",
    "crt_prefix_solutions_congruent_lcm": "0a5243850c7ffde41b00fb3680cf48610aa2f9e285e33f40e19c59c282814fea",
    "crt_prefix_solution_class_iff_lcm": "a943495e7c8817cf917f4cc282502ad316a2a3ce9892c5d6bb3ba2ab0fbd6488",
    "crt_canonical_prefix_solution_unique": "3631285d003a8cedeb954757d88ea8043cc2f79acb657e582b27018a0f0f003c",
    "crt_pairwise_coprime_prefix_canonical_exists_unique": "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f",
}
RELATIONS = (
    (candidate.crt_positive_moduli_prefix, ("b", "c", "l")),
    (candidate.crt_pairwise_coprime_prefix, ("b", "c", "l")),
    (candidate.crt_prefix_solution, ("r", "s", "b", "c", "l", "x")),
    (candidate.crt_prefix_lcm, ("b", "c", "l", "M")),
    (candidate.crt_canonical_prefix_solution, ("r", "s", "b", "c", "l", "x", "M")),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_generalized_crt_fold_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v23.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(item for item in _rows() if item.name == name)


def test_finite_crt_tranche_is_new_closed_ordered_and_exactly_frozen() -> None:
    rows = _rows()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(rows) == 27
    assert sum(len(item.dependencies) for item in rows) == 83
    assert sum(len(item.script) for item in rows) == 1_106
    assert max(len(item.statement) for item in rows) == 9_122
    available = set(_core())
    for item in rows:
        assert item.name not in available
        assert set(item.dependencies) <= available
        assert _closed_formula(item.statement)
        assert all(
            "DNE" not in command
            and command not in {"sorry", "admit"}
            and not command.startswith("use ")
            for command in item.script
        )
        available.add(item.name)


def test_every_finite_crt_body_passes_the_unchanged_intuitionistic_kernel() -> None:
    receipts = _receipts()
    assert tuple(item.name for item in receipts) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in receipts) == EXPECTED_BODY_NODES
    assert sum(item.proof_nodes for item in receipts) == 1_860
    assert max(item.proof_nodes for item in receipts) == 169
    assert max(item.proof_depth for item in receipts) == 55


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_actual_major_finite_crt_statement_roots_are_frozen(name: str, expected: str) -> None:
    assert sha256(_row(name).statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_forged_false_finite_crt_conclusions_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_truncated_finite_crt_proof_bodies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_removed_major_finite_crt_dependencies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_finite_crt_relations_are_conservative_hygienic_and_tag_independent(
    builder, arguments: tuple[str, ...]
) -> None:
    left, left_names = parse_formula_with_names(builder(*arguments, tag="first"))
    right, right_names = parse_formula_with_names(builder(*arguments, tag="second"))
    assert left == right
    assert set(left_names) == set(right_names) == set(arguments)
    assert "CRT" not in builder(*arguments, tag="first")
    assert "LCM" not in builder(*arguments, tag="first")


def test_pairwise_coprime_relation_reuses_exact_existing_checked_theorem_formula() -> None:
    actual, actual_names = parse_formula_with_names(
        candidate.crt_pairwise_coprime_prefix("b", "c", "l", tag="candidate")
    )
    existing, existing_names = parse_formula_with_names(
        _pairwise_coprime_prefix_term("b", "c", "l", tag="historical", variables=("b", "c", "l"))
    )
    assert actual == existing
    assert set(actual_names) == set(existing_names) == {"b", "c", "l"}


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_finite_crt_relations_reject_untrusted_arguments(builder, arguments, fragment: str) -> None:
    with pytest.raises(candidate.GeneralizedCRTFoldError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_finite_crt_relations_reject_untrusted_binder_tags(builder, arguments, fragment: str) -> None:
    with pytest.raises(candidate.GeneralizedCRTFoldError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_finite_crt_relations_reject_generated_binder_capture(builder, arguments) -> None:
    with pytest.raises(candidate.GeneralizedCRTFoldError, match="captures"):
        builder("gcrt_positive_index_capture", *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_finite_crt_relations_reject_duplicate_free_arguments(builder, arguments) -> None:
    with pytest.raises(candidate.GeneralizedCRTFoldError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


def test_full_finite_coprime_root_has_actual_prefix_guards_lcm_and_unique_bounded_solution() -> None:
    formula = _closed_formula(_row("crt_pairwise_coprime_prefix_canonical_exists_unique").statement)
    for _ in range(5):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.right, Imp)
    result = formula.right.right
    assert isinstance(result, Exists)
    assert isinstance(result.body, Exists)
    assert isinstance(result.body.body, And)
    assert isinstance(result.body.body.right, Forall)


def test_general_list_lcm_is_unconditional_even_for_noncoprime_and_zero_moduli() -> None:
    formula = _closed_formula(_row("crt_prefix_lcm_exists_unique").statement)
    for _ in range(3):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Exists)
    assert isinstance(formula.body, And)
    assert isinstance(formula.body.right, Forall)


@pytest.mark.parametrize(
    ("moduli", "residues"),
    (
        ((), ()),
        ((1,), (87,)),
        ((2, 3), (1, 2)),
        ((3, 5, 7), (2, 3, 4)),
        ((4, 9, 25), (3, 8, 17)),
        ((5, 7, 8, 9), (4, 6, 7, 8)),
    ),
)
def test_bounded_host_examples_demonstrate_actual_canonical_finite_coprime_crt(
    moduli: tuple[int, ...], residues: tuple[int, ...]
) -> None:
    assert all(modulus > 0 for modulus in moduli)
    assert all(gcd(left, right) == 1 for left, right in combinations(moduli, 2))
    product = prod(moduli)
    assert product == lcm(*moduli) if moduli else product == 1
    solutions = [value for value in range(product) if all(value % m == a % m for m, a in zip(moduli, residues))]
    assert len(solutions) == 1
    assert 0 <= solutions[0] < product


@pytest.mark.parametrize("moduli", ((6, 10), (4, 6, 15), (0, 4, 6), (0, 0), ()))
def test_all_modulus_lcm_exists_without_pairwise_coprimality(moduli: tuple[int, ...]) -> None:
    result = lcm(*moduli) if moduli else 1
    assert all(result % modulus == 0 for modulus in moduli if modulus)
    if any(modulus == 0 for modulus in moduli):
        assert result == 0


def test_noncoprime_pairwise_compatible_goal_g011_is_not_falsely_claimed_closed() -> None:
    moduli = (6, 10, 15)
    residues = (1, 7, 7)
    assert all(
        (left_residue - right_residue) % gcd(left_modulus, right_modulus) == 0
        for (left_modulus, left_residue), (right_modulus, right_residue)
        in combinations(zip(moduli, residues), 2)
    )
    assert not all(gcd(left, right) == 1 for left, right in combinations(moduli, 2))
    final = _row("crt_pairwise_coprime_prefix_canonical_exists_unique")
    assert "crt_pairwise_coprime_prefix_solution_exists" in final.dependencies
    assert all("pairwise_compatible_prefix_canonical_exists_unique" not in row.name for row in _rows())


def test_all_external_prerequisites_are_checked_in_immutable_alpha_v23() -> None:
    local = set(EXPECTED_NAMES)
    external = {dependency for row in _rows() for dependency in row.dependencies if dependency not in local}
    assert external <= set(_core())
    assert {
        "binary_crt_fold_step", "beta_product_exists_unique", "beta_factor_divides_product",
        "beta_pairwise_coprime_product_divides_common_multiple", "lcm_exists_relational",
        "canonical_remainder_exists", "mod_eq_bounded_unique",
    } <= external
    assert all(editions_v23.ALPHA_EDITION.by_name[name].checked_use for name in external)

