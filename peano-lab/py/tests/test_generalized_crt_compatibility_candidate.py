"""Original-kernel and adversarial audit of constructive noncoprime CRT."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, product
from math import gcd, lcm

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v24
from peano_lab.library import generalized_crt_compatibility_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "crt_mod_one_universal",
    "crt_coprime_divisor_pair",
    "crt_pairwise_compatible_prefix_empty",
    "crt_pairwise_compatible_prefix_drop_last",
    "crt_prefix_solution_implies_pairwise_compatible",
    "crt_pairwise_compatible_prefix_last",
    "crt_merge_compatible_prefix_drop_last",
    "generalized_binary_crt_merge_step",
    "crt_merge_compatible_prefix_solution_exists",
    "crt_positive_prefix_lcm_nonzero",
    "crt_prefix_zero_lcm_solution_unique",
    "crt_merge_compatible_prefix_canonical_exists_unique",
    "crt_balanced_bezout_scale",
    "crt_is_gcd_scale",
    "crt_is_gcd_coprime_factor_remove",
    "crt_product_witness",
    "crt_is_gcd_coprime_product",
    "crt_lcm_gcd_cofactor_product",
    "crt_gcd_scaled_coprime_component",
    "crt_gcd_monotone_under_divisibility",
    "crt_gcd_lcm_distributes_divisibility",
    "crt_merge_compatible_prefix_implies_pairwise_compatible",
    "crt_pairwise_compatible_dominating_last_solution",
    "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
)
EXPECTED_NAMES_SHA256 = "221fc9b2ca61c816f10bd6f8a1db48b053ff8676b8babece9d02a29dda9c5758"
EXPECTED_BODY_NODES = (
    20, 52, 32, 84, 89, 77, 66, 33, 125, 47, 38, 73,
    55, 131, 96, 4, 155, 59, 63, 79, 149, 26, 81, 84,
)
EXPECTED_ROOTS = {
    "crt_prefix_solution_implies_pairwise_compatible": "4b114040f7ff0a3e9e98279d8600d587741ebedcd598de06f2d899caad6fde1d",
    "crt_merge_compatible_prefix_solution_exists": "1e30822d43996807abe877aa76d88026a59c293dfe440ed00461e6a4eb17acc9",
    "crt_prefix_zero_lcm_solution_unique": "51282f3aa0c88577dd418755a7353937f00de77d97096e749e46b89390d9c4b9",
    "crt_merge_compatible_prefix_canonical_exists_unique": "9e3d68192e707b5953b2fd3c9e4716e9fe90317f63be49734bbed00e3492b927",
    "crt_is_gcd_scale": "abe947735d13b946283776bfb832f7f0e8dc17861fbd0850c5b7b51827d68f77",
    "crt_is_gcd_coprime_product": "e3b28cbcdf65cdad1e51c834812bf2efb8a45cb534bb8a5daa1e4245b4d0a347",
    "crt_gcd_lcm_distributes_divisibility": "0ac6861e424c4c961810fe6565850227601a3c79438256678a50f8df25a544dd",
    "crt_merge_compatible_prefix_implies_pairwise_compatible": "2088eb4d733f2d4bf8a84049d56d6f8fafc079a3b3fe76aa6d69665726fe0ea6",
    "crt_pairwise_compatible_dominating_last_solution": "97517c25a69447aa29949b2fc108933aea824e514eda2880c492c704094f5679",
    "crt_pairwise_compatible_dominating_last_canonical_exists_unique": "f249f7835eb127e8d5f15e74b3d4344d5d98503d8b01394d608bf2e677823fb0",
}
RELATIONS = (
    (candidate.crt_pairwise_compatible_prefix, ("r", "s", "b", "c", "l")),
    (candidate.crt_merge_compatible_prefix, ("r", "s", "b", "c", "l")),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_generalized_crt_compatibility_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v24.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def _row(name: str) -> TheoremSpec:
    return next(item for item in _rows() if item.name == name)


def _congruent(left: int, right: int, modulus: int) -> bool:
    return left == right if modulus == 0 else (left - right) % modulus == 0


def _compatible(moduli: tuple[int, ...], residues: tuple[int, ...]) -> bool:
    return all(
        _congruent(left_residue, right_residue, gcd(left_modulus, right_modulus))
        for (left_modulus, left_residue), (right_modulus, right_residue)
        in combinations(zip(moduli, residues), 2)
    )


def test_generalized_compatibility_tranche_is_new_ordered_closed_and_frozen() -> None:
    rows = _rows()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(rows) == 24
    assert sum(len(item.dependencies) for item in rows) == 90
    assert sum(len(item.script) for item in rows) == 1_097
    assert max(len(item.statement) for item in rows) == 15_458
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


def test_every_generalized_compatibility_body_passes_original_heyting_kernel() -> None:
    receipts = _receipts()
    assert tuple(item.name for item in receipts) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in receipts) == EXPECTED_BODY_NODES
    assert sum(item.proof_nodes for item in receipts) == 1_718
    assert max(item.proof_nodes for item in receipts) == 155
    assert max(item.proof_depth for item in receipts) == 48


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_major_noncoprime_crt_statement_roots_are_frozen(name: str, expected: str) -> None:
    assert sha256(_row(name).statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_forged_false_noncoprime_crt_conclusions_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_truncated_noncoprime_crt_bodies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_removed_noncoprime_crt_dependencies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_core() | {row.name: row for row in _rows()})


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_compatibility_relations_are_conservative_hygienic_and_alpha_invariant(
    builder, arguments: tuple[str, ...]
) -> None:
    left, left_names = parse_formula_with_names(builder(*arguments, tag="first"))
    right, right_names = parse_formula_with_names(builder(*arguments, tag="second"))
    assert left == right
    assert set(left_names) == set(right_names) == set(arguments)
    assert "CRT" not in builder(*arguments, tag="first")
    assert "GCD" not in builder(*arguments, tag="first")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_compatibility_relations_reject_untrusted_arguments(
    builder, arguments: tuple[str, ...], fragment: str
) -> None:
    with pytest.raises(candidate.GeneralizedCRTCompatibilityError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_compatibility_relations_reject_untrusted_tags(
    builder, arguments: tuple[str, ...], fragment: str
) -> None:
    with pytest.raises(candidate.GeneralizedCRTCompatibilityError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("gcomp_left_index_capture", "hag_divisor_capture"))
def test_compatibility_relations_reject_generated_binder_capture(
    builder, arguments: tuple[str, ...], fragment: str
) -> None:
    with pytest.raises(candidate.GeneralizedCRTCompatibilityError, match="capture"):
        builder(fragment, *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_compatibility_relations_reject_duplicate_arguments(
    builder, arguments: tuple[str, ...]
) -> None:
    with pytest.raises(candidate.GeneralizedCRTCompatibilityError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


@pytest.mark.parametrize(
    "name",
    (
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
    ),
)
def test_noncoprime_canonical_roots_have_actual_lcm_and_unique_bounded_solution(
    name: str,
) -> None:
    formula = _closed_formula(_row(name).statement)
    while isinstance(formula, Forall):
        formula = formula.body
    antecedents = 0
    while isinstance(formula, Imp):
        antecedents += 1
        formula = formula.right
    assert antecedents == (2 if name.startswith("crt_merge") else 5)
    assert isinstance(formula, Exists)
    assert isinstance(formula.body, Exists)
    assert isinstance(formula.body.body, And)
    assert isinstance(formula.body.body.right, Forall)


def test_full_arbitrary_pairwise_compatible_target_g011_remains_open() -> None:
    moduli, residues = (6, 10, 15), (1, 7, 7)
    assert _compatible(moduli, residues)
    assert any(gcd(left, right) != 1 for left, right in combinations(moduli, 2))
    assert moduli[-1] % moduli[0] != 0
    names = set(EXPECTED_NAMES)
    assert "crt_pairwise_compatible_prefix_canonical_exists_unique" not in names
    assert "crt_pairwise_compatible_prefix_implies_merge_compatible" not in names
    merge = _row("crt_merge_compatible_prefix_canonical_exists_unique")
    dominating = _row("crt_pairwise_compatible_dominating_last_canonical_exists_unique")
    assert "crt_merge_compatible_prefix_solution_exists" in merge.dependencies
    assert "crt_pairwise_compatible_dominating_last_solution" in dominating.dependencies


def test_lattice_distributivity_result_explicitly_requires_one_modulus_to_divide_other() -> None:
    formula = _closed_formula(_row("crt_gcd_lcm_distributes_divisibility").statement)
    for _ in range(7):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.left, Exists)


@pytest.mark.parametrize(
    ("moduli", "residues"),
    (
        ((2, 4, 8), (1, 3, 3)),
        ((6, 10, 30), (1, 7, 7)),
        ((4, 6, 12), (3, 5, 11)),
        ((3, 9, 18), (2, 8, 17)),
        ((5,), (48,)),
    ),
)
def test_bounded_examples_demonstrate_pairwise_compatible_dominating_last_crt(
    moduli: tuple[int, ...], residues: tuple[int, ...]
) -> None:
    assert all(modulus > 0 for modulus in moduli)
    assert _compatible(moduli, residues)
    assert all(moduli[-1] % modulus == 0 for modulus in moduli[:-1])
    assert all(_congruent(residues[-1], residue, modulus) for modulus, residue in zip(moduli, residues))
    modulus = lcm(*moduli)
    solutions = [
        value
        for value in range(modulus)
        if all(_congruent(value, residue, entry) for entry, residue in zip(moduli, residues))
    ]
    assert solutions == [residues[-1] % modulus]


@pytest.mark.parametrize(
    ("moduli", "residues"),
    (((2, 0), (1, 3)), ((0, 0), (7, 7)), ((4, 0), (2, 10))),
)
def test_dominating_last_solution_supports_zero_moduli_without_false_canonical_claim(
    moduli: tuple[int, ...], residues: tuple[int, ...]
) -> None:
    assert _compatible(moduli, residues)
    assert moduli[-1] == 0
    assert lcm(*moduli) == 0
    assert all(_congruent(residues[-1], residue, modulus) for modulus, residue in zip(moduli, residues))


@pytest.mark.parametrize(("moduli", "residues"), (((4, 6), (0, 1)), ((0, 0), (2, 3))))
def test_actual_incompatible_noncoprime_or_zero_systems_are_detected(
    moduli: tuple[int, ...], residues: tuple[int, ...]
) -> None:
    assert not _compatible(moduli, residues)


@pytest.mark.parametrize("scale", tuple(range(8)))
def test_bounded_gcd_scaling_examples_include_zero_scale(scale: int) -> None:
    for left, right in product(range(8), repeat=2):
        assert gcd(scale * left, scale * right) == scale * gcd(left, right)


@pytest.mark.parametrize("comparison", tuple(range(9)))
def test_bounded_divisible_lattice_distributivity_examples_include_zero(
    comparison: int,
) -> None:
    for left, quotient in product(range(8), repeat=2):
        right = left * quotient
        assert gcd(lcm(left, right), comparison) == lcm(
            gcd(left, comparison), gcd(right, comparison)
        )


@pytest.mark.parametrize("comparison", tuple(range(1, 9)))
def test_bounded_coprime_product_gcd_examples(comparison: int) -> None:
    for left, right in product(range(1, 9), repeat=2):
        if gcd(left, right) == 1:
            assert gcd(left * right, comparison) == gcd(left, comparison) * gcd(right, comparison)


def test_every_external_prerequisite_is_checked_in_immutable_alpha_v24() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for row in _rows()
        for dependency in row.dependencies
        if dependency not in local
    }
    assert external <= set(_core())
    assert {
        "generalized_binary_crt_sufficient", "crt_prefix_lcm_exists_unique",
        "crt_prefix_solution_canonical_remainder", "crt_canonical_prefix_solution_unique",
        "gcd_balanced_bezout_exists", "gauss_coprime_cancel", "gcd_lcm_product",
    } <= external
    assert all(editions_v24.ALPHA_EDITION.by_name[name].checked_use for name in external)
