"""Constructive/adversarial audit of infinitely many primes ``3 modulo 4``."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd, isqrt

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, parse_formula_with_names
from peano_lab.library import editions_v22 as v22
from peano_lab.library import primes_three_mod_four_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_factor_fold_candidate import (
    make_fermat_two_squares_factor_fold_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "beta_two_square_prefix_drop_last",
    "beta_two_square_prefix_last_represented",
    "beta_two_square_represented_factor_product",
    "beta_all_prime_entry_is_prime",
    "beta_admissible_prime_factor_product_is_two_square",
    "positive_number_with_admissible_prime_divisors_is_two_square",
    "three_mod_four_progression_nonzero",
    "three_mod_four_progression_nonunit",
    "three_mod_four_progression_not_two_square",
    "three_mod_four_good_prime_exclusive",
    "three_mod_four_prime_divisor_decidable",
    "three_mod_four_prime_divisor_bounded_search",
    "three_mod_four_prime_divisor_exists",
    "euclid_three_number_successor_balance",
    "euclid_three_progression_prime_exists",
    "euclid_three_common_multiple_exclusion",
    "euclid_three_prime_divisor_exceeds_bound",
    "infinitely_many_primes_three_mod_four",
)

EXPECTED_PROOF_NODES = (
    32,
    24,
    106,
    42,
    40,
    76,
    21,
    23,
    19,
    23,
    46,
    92,
    66,
    59,
    10,
    44,
    38,
    42,
)

EXPECTED_PROOF_DEPTHS = (
    21,
    16,
    26,
    21,
    21,
    27,
    11,
    11,
    12,
    14,
    14,
    25,
    26,
    16,
    7,
    23,
    22,
    20,
)

EXPECTED_STATEMENT_ROOTS = {
    "positive_number_with_admissible_prime_divisors_is_two_square": (
        "4f1877c55982623acfdc8c10d6244f00d0c97073e3701854c9f1243ce665fce1"
    ),
    "three_mod_four_prime_divisor_decidable": (
        "78cb480295bfbb6ab051a5a9836219a4aac959dd2b55c78768e920587c1f622d"
    ),
    "three_mod_four_prime_divisor_bounded_search": (
        "bf745c28ef1dc187532e538fa2635704f72cdbf80c86d02547d2bf8f01d0025e"
    ),
    "three_mod_four_prime_divisor_exists": (
        "6b5d6bcf3910d533b85b9e7e3f020da54ae1910114b1a8f83f0c39e4d3056985"
    ),
    "euclid_three_progression_prime_exists": (
        "a2bcbb4684372da3274ff4f55ff36ae47a7f6cd0b642965ee9a49eec95d4cc3c"
    ),
    "euclid_three_prime_divisor_exceeds_bound": (
        "34d1c3326204e6a72fa4a7115a8d500217275f498293ec78eb417ecab0b858af"
    ),
    "infinitely_many_primes_three_mod_four": (
        "3ddac628b2e37925ee3d7a4bd56319de5e173e9065cce6437cab775cc646620b"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_primes_three_mod_four_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v22.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def _available() -> dict[str, TheoremSpec]:
    return core() | {item.name: item for item in rows()}


def test_eighteen_progression_candidates_are_closed_fresh_and_dag_ordered() -> None:
    actual = rows()

    assert len(actual) == 18
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert actual == candidate.make_primes_three_mod_four_candidate_theorems(
        TheoremSpec
    )
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        "ba74af7579f0e73c4041f0dc58bab86a15f08435ac08f8568cc35417bc37f4b9"
    )
    assert sum(len(item.dependencies) for item in actual) == 46
    assert sum(len(item.script) for item in actual) == 467

    available = set(core())
    for item in actual:
        parsed, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert parsed == _closed_formula(item.statement)
        assert set(item.dependencies) <= available
        assert item.name not in v22.ALPHA_EDITION.by_name
        assert not any(
            command in {"sorry", "admit"}
            or "DNE" in command
            or command.startswith("use ")
            for command in item.script
        )
        available.add(item.name)


def test_all_progression_bodies_reach_the_original_intuitionistic_kernel() -> None:
    actual = receipts()

    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(item.proof_nodes for item in actual) == 803
    assert sum(item.proof_objects for item in actual) == 793
    assert max(item.proof_nodes for item in actual) == 106
    assert max(item.proof_depth for item in actual) == 27


def test_factor_fold_foundations_are_reused_exactly_not_redefined() -> None:
    historical = {
        item.name: item
        for item in make_fermat_two_squares_factor_fold_candidate_theorems(
            TheoremSpec
        )
    }

    assert candidate.FACTOR_FOLD_FOUNDATION_NAMES == EXPECTED_NAMES[:6]
    assert tuple(rows()[:6]) == tuple(
        historical[name] for name in candidate.FACTOR_FOLD_FOUNDATION_NAMES
    )
    assert all(name not in core() for name in candidate.FACTOR_FOLD_FOUNDATION_NAMES)


@pytest.mark.parametrize(("name", "expected"), EXPECTED_STATEMENT_ROOTS.items())
def test_major_progression_statement_roots_are_exact(name: str, expected: str) -> None:
    row = next(item for item in rows() if item.name == name)

    assert sha256(row.statement.encode()).hexdigest() == expected


def test_final_endpoint_has_actual_prime_strict_order_and_three_class() -> None:
    endpoint = rows()[-1]

    assert endpoint.name == candidate.INFINITELY_MANY_PRIMES_THREE_MOD_FOUR
    assert endpoint.dependencies == (
        "bounded_common_multiple_exists",
        "nonzero_is_succ",
        "euclid_three_progression_prime_exists",
        "euclid_three_prime_divisor_exceeds_bound",
    )
    assert "gap + S B = p" in endpoint.statement
    assert "(p) = 4 * ff_residue_ptmf_prime + 3" in endpoint.statement
    assert "p = 1" in endpoint.statement

    parsed = _closed_formula(endpoint.statement)
    assert isinstance(parsed, Forall)
    assert isinstance(parsed.body, Exists)
    assert isinstance(parsed.body.body, And)
    assert isinstance(parsed.body.body.left, And)
    assert isinstance(parsed.body.body.right, And)
    assert isinstance(parsed.body.body.right.left, Exists)
    assert isinstance(parsed.body.body.right.right, Exists)


def test_only_checked_alpha_v22_dependencies_supply_external_authority() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in rows()
        for dependency in item.dependencies
        if dependency not in local
    }

    assert external == {
        "beta_at_unique",
        "beta_factor_divides_product",
        "beta_product_succ_decompose",
        "beta_product_zero",
        "bounded_common_multiple_contains_bounded_prime",
        "bounded_common_multiple_exists",
        "divides_remainder",
        "divisor_le_nonzero",
        "divisor_one",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "le_or_lt",
        "le_refl",
        "le_succ",
        "le_zero",
        "mul_one",
        "multiple_mul_left",
        "nonzero_is_succ",
        "prime_divides_decidable",
        "prime_factorization_existence",
        "prime_mod_four_good_or_three",
        "prime_nonzero",
        "prime_two_or_one_mod_four_is_sum_of_two_squares",
        "three_mod_four_number_not_equal_represented",
        "two_square_representation_multiplicatively_closed",
    }
    assert all(v22.ALPHA_EDITION.by_name[name].checked_use for name in external)
    assert "infinitely_many_primes_one_mod_four" not in external
    assert "infinitely_many_primes_three_mod_four" not in external


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_progression_candidate_conclusions_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_progression_proof_bodies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize(
    "name",
    tuple(name for name in EXPECTED_NAMES if name not in {
        "three_mod_four_progression_nonzero",
        "three_mod_four_progression_nonunit",
        "euclid_three_number_successor_balance",
    }),
)
def test_missing_progression_dependency_fails_closed(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, dependencies=original.dependencies[:-1])

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("gap + S B = p", "gap + B = p"),
        ("4 * ff_residue_ptmf_prime + 3", "4 * ff_residue_ptmf_prime + 1"),
    ),
)
def test_tampered_exact_progression_endpoint_is_rejected(old: str, new: str) -> None:
    original = rows()[-1]
    assert original.statement.count(old) == 1
    forged = replace(original, statement=original.statement.replace(old, new))

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=_available())


@pytest.mark.parametrize(
    ("surface", "arguments", "free"),
    (
        (candidate.three_mod_four_relation, ("n",), {"n"}),
        (candidate.three_mod_four_prime_divisor, ("n", "p"), {"n", "p"}),
        (candidate.euclid_three_number, ("c", "n"), {"c", "n"}),
    ),
)
def test_progression_surfaces_are_conservative_and_hygienic(
    surface, arguments, free
) -> None:
    expanded = surface(*arguments, tag="safe")
    parsed, free_names = parse_formula_with_names(expanded)

    assert parsed is not None
    assert set(free_names) == free
    assert not any(name in expanded for name in ("Prime(", "Mod(", "Dvd("))

    with pytest.raises(candidate.PrimesThreeModFourError):
        surface("n + 1", *arguments[1:], tag="safe")
    with pytest.raises(candidate.PrimesThreeModFourError):
        surface(*arguments, tag="safe) -> false")


@pytest.mark.parametrize(
    ("surface", "arguments"),
    (
        (candidate.three_mod_four_relation, ("ff_residue_ptmf_safe",)),
        (
            candidate.three_mod_four_prime_divisor,
            ("ff_residue_ptmf_safe_residue", "p"),
        ),
        (
            candidate.three_mod_four_prime_divisor,
            ("ff_quotient_ptmf_safe_divides", "p"),
        ),
        (candidate.euclid_three_number, ("ff_predecessor_ptmf_safe", "n")),
    ),
)
def test_generated_progression_binders_cannot_capture_arguments(
    surface, arguments
) -> None:
    with pytest.raises(candidate.PrimesThreeModFourError, match="captures"):
        surface(*arguments, tag="safe")


@pytest.mark.parametrize("bound", (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20))
def test_concrete_euclid_construction_returns_a_strict_progression_prime(
    bound: int,
) -> None:
    common = 1
    for value in range(1, bound + 1):
        common = common // gcd(common, value) * value

    predecessor = common - 1
    euclid = 4 * predecessor + 3
    remaining = euclid
    factor = 2
    while factor * factor <= remaining:
        if remaining % factor:
            factor += 1
        elif factor % 4 == 3:
            witness = factor
            break
        else:
            remaining //= factor
    else:
        witness = remaining

    assert euclid + 1 == 4 * common
    assert euclid == 4 * common - 1
    assert euclid % witness == 0
    assert all(witness % factor for factor in range(2, isqrt(witness) + 1))
    assert witness > bound
    assert witness % 4 == 3


def test_every_small_three_progression_value_has_a_three_progression_prime() -> None:
    for value in range(3, 1024, 4):
        witness = next(
            divisor
            for divisor in range(3, value + 1, 4)
            if value % divisor == 0
            and all(divisor % factor for factor in range(2, isqrt(divisor) + 1))
        )

        assert value % witness == 0
        assert witness % 4 == 3
