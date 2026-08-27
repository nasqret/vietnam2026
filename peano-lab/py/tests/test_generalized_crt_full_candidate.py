"""Original-HA body replay and adversarial audit of unrestricted finite CRT.

Small integer computations below are regression examples, not proof evidence.
Every formal row is checked separately against the unchanged original kernel.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd, lcm

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.library import editions_v26
from peano_lab.library import generalized_crt_full_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.generalized_crt_compatibility_candidate import (
    crt_merge_compatible_prefix, crt_pairwise_compatible_prefix,
)
from peano_lab.library.generalized_crt_fold_candidate import (
    crt_canonical_prefix_solution, crt_positive_moduli_prefix,
    crt_prefix_lcm, crt_prefix_solution,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "crt_gcd_zero_right_value",
    "crt_gcd_nonzero_left",
    "crt_gcd_nonzero_right",
    "crt_gcd_coprime_cofactors",
    "crt_gcd_lcm_distributes_scaled_coprime",
    "crt_gcd_lcm_distributes_nonzero",
    "crt_gcd_lcm_distributes_zero_left",
    "crt_gcd_lcm_distributes_zero_comparison",
    "crt_gcd_lcm_distributes",
    "crt_prefix_gcd_congruences_drop_last",
    "crt_prefix_gcd_congruences_lcm",
    "crt_pairwise_compatible_prefix_induces_gcd_congruences",
    "crt_pairwise_compatible_prefix_implies_merge_compatible",
    "crt_pairwise_compatible_prefix_solution_exists",
    "crt_pairwise_compatible_prefix_canonical_exists_unique",
    "crt_canonical_prefix_solution_implies_normalized",
    "crt_normalized_prefix_solution_unique",
    "crt_prefix_solution_normalized_exists",
    "crt_pairwise_compatible_prefix_normalized_exists_unique",
    "crt_pairwise_compatible_prefix_solvable_iff",
    "crt_pairwise_compatible_prefix_merge_iff",
    "crt_normalized_prefix_solution_class_iff_lcm",
    "crt_normalized_zero_lcm_all_solutions_unique",
    "crt_positive_normalized_prefix_iff_canonical",
)
EXPECTED_NAMES_SHA256 = "e22d05834c251753c184f3153dc86eb5c73c736993cdd01ed6776c4e81194a81"
EXPECTED_BODY_NODES = (
    23, 25, 41, 42, 351, 174, 48, 91, 79, 43, 232, 89,
    105, 53, 56, 30, 175, 49, 57, 62, 56, 63, 69, 91,
)
EXPECTED_STATEMENTS = {
    "crt_gcd_lcm_distributes": "50a7f6d6073fce97824cccfd6af82f692b2840298b8b8e73067d051f33f64233",
    "crt_prefix_gcd_congruences_lcm": "6ca30daf96706a4f4f193a1e305703edf35008320aedb0b742ad07a5c64af48a",
    "crt_pairwise_compatible_prefix_implies_merge_compatible": "d582dfb54082a0620f6476a37dc52d9e759bb4d86631708aa890249d5af8d98c",
    "crt_pairwise_compatible_prefix_solution_exists": "48a05bffa7e68939a732d71d5cb72ac423b78e014dbfada69a78fcfcf2bd667a",
    "crt_pairwise_compatible_prefix_canonical_exists_unique": "ac5e941743de53a1954904f99231acf74a38f59c15ed7887d3896cf3b8fe65b8",
    "crt_normalized_prefix_solution_unique": "5180816ac65acca0c53e4071a21e5c3f05f0f37e094bab304ac39106cf01f5ca",
    "crt_pairwise_compatible_prefix_normalized_exists_unique": "f333d811cf04309d630382e2c049885d0de6e2cf4f26a218faf0e6039b002587",
    "crt_pairwise_compatible_prefix_solvable_iff": "bbaf5b097637ebfb6178b95ff37f6fed77776532c4058ece4f2f79a94e65ba64",
    "crt_pairwise_compatible_prefix_merge_iff": "149a47d55ab4e0d114425fdf4e5a24372b1bec6703c8edfb778bda26a0965385",
    "crt_normalized_prefix_solution_class_iff_lcm": "7b40cc8a8d70540961d430bb2bcded5b85339c88aa4a56eea04fa36be938aa65",
    "crt_normalized_zero_lcm_all_solutions_unique": "5e8527d6bb0ace3d9edfb731527e3f285afa15a9f470352f68d2caa01e8b66f0",
    "crt_positive_normalized_prefix_iff_canonical": "c386db27791b4089d54b406464fdc41045866f7ee86c540fdc030a9ae2f9d16e",
}
RELATIONS = (
    (candidate.crt_prefix_gcd_congruences, ("b", "c", "l", "n", "u", "v")),
    (candidate.crt_normalized_prefix_solution, ("r", "s", "b", "c", "l", "x", "M")),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_generalized_crt_full_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in editions_v26.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _all() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


@lru_cache(maxsize=1)
def _receipts():
    # Each invocation builds and checks exactly one dependency-curried body;
    # no recursive full-library replay or unbounded proof bundle is attempted.
    return tuple(replay_candidate_bodies((row,), core=_all())[0] for row in _rows())


def test_full_crt_inventory_is_closed_additive_dependency_ordered_and_deterministic() -> None:
    assert _rows() == candidate.make_generalized_crt_full_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(_rows()) == 24
    assert sum(len(row.dependencies) for row in _rows()) == 72
    assert sum(len(row.script) for row in _rows()) == 1_099
    assert max(len(row.statement) for row in _rows()) == 24_030
    available = set(_core())
    for row in _rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        formula, free = parse_formula_with_names(row.statement)
        assert not free and formula == _closed_formula(row.statement)
        assert all(
            not any(fragment in command for fragment in ("DNE", "sorry", "admit", "oracle", "axiom"))
            and not command.startswith("use ")
            for command in row.script
        )
        available.add(row.name)


def test_all_bodies_pass_the_original_heyting_kernel_in_bounded_microbatches() -> None:
    assert tuple(receipt.name for receipt in _receipts()) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in _receipts()) == EXPECTED_BODY_NODES
    assert sum(receipt.proof_nodes for receipt in _receipts()) == 2_104
    assert max(receipt.proof_depth for receipt in _receipts()) == 62
    assert max(receipt.proof_nodes for receipt in _receipts()) == 351


@pytest.mark.parametrize(("name", "digest"), EXPECTED_STATEMENTS.items())
def test_major_endpoint_statement_hashes_are_pinned(name: str, digest: str) -> None:
    assert sha256(_all()[name].statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_conclusions_are_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_original_proof_bodies_are_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all())


@pytest.mark.parametrize("name", tuple(name for name in EXPECTED_NAMES if name != "crt_canonical_prefix_solution_implies_normalized"))
def test_removed_dependencies_are_rejected(name: str) -> None:
    row = _all()[name]
    assert row.dependencies
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_all())


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_new_definitions_are_hygienic_alpha_invariant_expansions(builder, arguments) -> None:
    first, names = parse_formula_with_names(builder(*arguments, tag="first"))
    second, other_names = parse_formula_with_names(builder(*arguments, tag="second"))
    assert first == second
    assert set(names) == set(other_names) == set(arguments)
    assert all(token not in builder(*arguments, tag="audit") for token in ("CRT", "IsGCD", "IsLCM", "ModEq"))


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_new_definitions_reject_untrusted_arguments(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_new_definitions_reject_untrusted_tags(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("gfull_index_capture", "ec_gcd_common_capture", "hscale_common_capture", "gcomp_left_index_capture", "hag_divisor_capture"))
def test_new_definitions_reject_generated_binder_capture(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError, match="capture"):
        builder(fragment, *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_new_definitions_reject_duplicate_arguments(builder, arguments) -> None:
    with pytest.raises(ValueError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


def test_gcd_lcm_distributivity_has_no_divisibility_coprimality_or_positivity_premise() -> None:
    formula = _closed_formula(_all()["crt_gcd_lcm_distributes"].statement)
    for _ in range(7):
        assert isinstance(formula, Forall)
        formula = formula.body
    premises = []
    while isinstance(formula, Imp):
        premises.append(formula.left)
        formula = formula.right
    assert len(premises) == 4  # The input LCM and three input GCD relations only.
    assert all(isinstance(premise, And) for premise in premises)
    assert isinstance(formula, And)


def test_the_arbitrary_prefix_lifting_proof_really_uses_natural_induction() -> None:
    row = _all()["crt_prefix_gcd_congruences_lcm"]
    assert "induction l" in row.script
    assert "crt_gcd_lcm_distributes" in row.dependencies
    assert "crt_prefix_lcm_successor_intro" in row.dependencies
    assert "mod_eq_lcm_merge" in row.dependencies


def test_unrestricted_merge_endpoint_has_only_actual_pairwise_compatibility() -> None:
    expected = (
        "forall r s b c l. "
        f"({crt_pairwise_compatible_prefix('r', 's', 'b', 'c', 'l', tag='audit_source')}) -> "
        f"({crt_merge_compatible_prefix('r', 's', 'b', 'c', 'l', tag='audit_result')})"
    )
    assert _closed_formula(_all()["crt_pairwise_compatible_prefix_implies_merge_compatible"].statement) == _closed_formula(expected)


def test_full_zero_inclusive_root_has_one_pairwise_premise_and_actual_unique_witnesses() -> None:
    expected = (
        "forall r s b c l. "
        f"({crt_pairwise_compatible_prefix('r', 's', 'b', 'c', 'l', tag='audit_pairs')}) -> exists x M. "
        f"(({candidate.crt_normalized_prefix_solution('r', 's', 'b', 'c', 'l', 'x', 'M', tag='audit_chosen')}) /\\ "
        f"forall y. ({candidate.crt_normalized_prefix_solution('r', 's', 'b', 'c', 'l', 'y', 'M', tag='audit_compared')}) -> y = x)"
    )
    actual = _closed_formula(_all()["crt_pairwise_compatible_prefix_normalized_exists_unique"].statement)
    assert actual == _closed_formula(expected)
    for _ in range(5):
        assert isinstance(actual, Forall)
        actual = actual.body
    assert isinstance(actual, Imp) and isinstance(actual.right, Exists)
    assert isinstance(actual.right.body, Exists) and isinstance(actual.right.body.body, And)
    assert isinstance(actual.right.body.body.right, Forall)


def test_positive_canonical_root_preserves_the_historical_strict_definition() -> None:
    expected = (
        "forall r s b c l. "
        f"({crt_positive_moduli_prefix('b', 'c', 'l', tag='audit_positive')}) -> "
        f"({crt_pairwise_compatible_prefix('r', 's', 'b', 'c', 'l', tag='audit_pairs')}) -> exists x M. "
        f"(({crt_canonical_prefix_solution('r', 's', 'b', 'c', 'l', 'x', 'M', tag='audit_chosen')}) /\\ "
        f"forall y. ({crt_canonical_prefix_solution('r', 's', 'b', 'c', 'l', 'y', 'M', tag='audit_compared')}) -> y = x)"
    )
    assert _closed_formula(_all()["crt_pairwise_compatible_prefix_canonical_exists_unique"].statement) == _closed_formula(expected)


def test_normalization_does_not_discard_solution_or_lcm_at_zero() -> None:
    expected = (
        f"({crt_prefix_lcm('b', 'c', 'l', 'M', tag='audit_lcm')}) /\\ "
        f"((M = 0 \\/ (exists h. h + S x = M)) /\\ "
        f"({crt_prefix_solution('r', 's', 'b', 'c', 'l', 'x', tag='audit_solution')}))"
    )
    actual = candidate.crt_normalized_prefix_solution("r", "s", "b", "c", "l", "x", "M", tag="audit")
    assert _closed_formula(f"forall r s b c l x M. {actual}") == _closed_formula(f"forall r s b c l x M. {expected}")
    parsed = _closed_formula(f"forall r s b c l x M. {actual}")
    for _ in range(7):
        parsed = parsed.body
    assert isinstance(parsed, And) and isinstance(parsed.right, And)
    assert isinstance(parsed.right.left, Or)
    assert isinstance(parsed.right.right, Forall)


@pytest.mark.parametrize("name", ("crt_pairwise_compatible_prefix_solvable_iff", "crt_pairwise_compatible_prefix_merge_iff"))
def test_both_compatibility_characterizations_are_exact_equivalences(name: str) -> None:
    formula = _closed_formula(_all()[name].statement)
    for _ in range(5):
        formula = formula.body
    assert isinstance(formula, And)
    assert isinstance(formula.left, Imp) and isinstance(formula.right, Imp)
    assert formula.left.left == formula.right.right
    assert formula.left.right == formula.right.left


def _congruent(modulus: int, left: int, right: int) -> bool:
    return left == right if modulus == 0 else (left - right) % modulus == 0


def _compatible(moduli: tuple[int, ...], residues: tuple[int, ...]) -> bool:
    return all(_congruent(gcd(a, b), x, y) for a, x in zip(moduli, residues) for b, y in zip(moduli, residues))


def _solution(moduli: tuple[int, ...], residues: tuple[int, ...], value: int) -> bool:
    return all(_congruent(modulus, value, residue) for modulus, residue in zip(moduli, residues))


@pytest.mark.parametrize(("moduli", "residues", "expected", "period"), (
    ((), (), 0, 1),
    ((6, 10, 15), (1, 7, 7), 7, 30),
    ((6, 10, 15, 21), (5, 7, 2, 2), 107, 210),
    ((4, 6), (3, 5), 11, 12),
    ((6, 6), (1, 7), 1, 6),
    ((1, 1, 1), (17, 33, 8), 0, 1),
    ((0, 6), (7, 1), 7, 0),
    ((6, 0), (1, 7), 7, 0),
    ((0, 0), (7, 7), 7, 0),
    ((0, 4, 6, 10), (47, 3, 5, 7), 47, 0),
))
def test_zero_empty_repeated_and_nondominating_small_examples(moduli, residues, expected, period) -> None:
    assert _compatible(moduli, residues)
    assert lcm(*moduli) == period
    assert _solution(moduli, residues, expected)
    assert period == 0 or expected < period
    for value in range(max(expected + 15, period * 2 + 5)):
        assert _solution(moduli, residues, value) == _congruent(period, value, expected)
        if _solution(moduli, residues, value) and (period == 0 or value < period):
            assert value == expected


def test_unrestricted_gcd_lcm_identity_on_all_small_zero_inclusive_inputs() -> None:
    for a, b, n in product(range(9), repeat=3):
        assert gcd(lcm(a, b), n) == lcm(gcd(a, n), gcd(b, n))


def test_compatibility_is_exact_for_all_small_lists_including_zero_moduli() -> None:
    for length in range(4):
        for moduli in product(range(4), repeat=length):
            period = lcm(*moduli)
            for residues in product(range(4), repeat=length):
                candidates = range(period) if period else (residues[moduli.index(0)],)
                normalized = [value for value in candidates if _solution(moduli, residues, value)]
                assert bool(normalized) == _compatible(moduli, residues)
                assert len(normalized) <= 1


def test_old_dominating_last_special_case_does_not_cover_the_new_example() -> None:
    moduli, residues = (6, 10, 15), (1, 7, 7)
    assert _compatible(moduli, residues)
    assert not all(moduli[-1] % modulus == 0 for modulus in moduli[:-1])
    assert not all(gcd(a, b) == 1 for a, b in zip(moduli, moduli[1:]))
