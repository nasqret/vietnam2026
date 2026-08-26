"""Exact constructive audit of arbitrarily large primes ``1 modulo 4``."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd, isqrt

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, parse_formula_with_names
from peano_lab.library import editions_v18 as v18
from peano_lab.library import primes_one_mod_four_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "doubled_square_plus_one_nonzero",
    "doubled_square_plus_one_nonunit",
    "doubled_square_plus_one_has_prime_divisor",
    "doubled_square_plus_one_not_divisible_by_two",
    "three_mod_four_prime_cannot_divide_doubled_square_plus_one",
    "prime_divisor_of_doubled_square_plus_one_is_one_mod_four",
    "bounded_common_multiple_contains_bounded_prime",
    "common_multiple_prime_cannot_divide_doubled_square_plus_one",
    "doubled_square_prime_divisor_exceeds_common_multiple_bound",
    "infinitely_many_primes_one_mod_four",
)

EXPECTED_PROOF_NODES = (19, 35, 27, 18, 33, 35, 42, 42, 33, 41)
EXPECTED_PROOF_DEPTHS = (9, 14, 14, 11, 18, 16, 20, 21, 20, 17)
EXPECTED_COMMAND_COUNTS = (6, 27, 11, 13, 29, 25, 32, 36, 25, 26)
EXPECTED_ROOT_STATEMENT_SHA256 = (
    "eb4e068b6bb3a271118a6e6aaea03ddd9d0fc10317f38bc4697b0a46dd9ac1be"
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "80d387e5567f93e1a56014555257e14193f42b3de56da6bae354d55fc792220c"
)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_primes_one_mod_four_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v18.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_ten_exact_candidates_are_ordered_closed_and_not_alpha_enrolled() -> None:
    actual = rows()

    assert len(actual) == 10
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert actual == candidate.make_primes_one_mod_four_candidate_theorems(TheoremSpec)
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert sum(map(len, (item.dependencies for item in actual))) == 27
    assert sum(map(len, (item.script for item in actual))) == 230

    prior: set[str] = set()
    for item in actual:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert set(item.dependencies).issubset(set(core()) | prior)
        assert item.name not in v18.ALPHA_EDITION.by_name
        assert not any("DNE" in command or command.startswith("use ") for command in item.script)
        prior.add(item.name)


def test_all_actual_dependency_curried_proofs_pass_the_original_kernel() -> None:
    actual = receipts()

    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert tuple(item.command_count for item in actual) == EXPECTED_COMMAND_COUNTS
    assert all(item.proof_nodes == item.proof_objects for item in actual)
    assert max(item.proof_nodes for item in actual) == 42
    assert max(item.proof_depth for item in actual) == 21
    assert sum(item.proof_nodes for item in actual) == 325


def test_exact_root_has_genuine_prime_strict_bound_and_one_mod_four_witnesses() -> None:
    endpoint = rows()[-1]

    assert endpoint.name == candidate.INFINITELY_MANY_PRIMES_ONE_MOD_FOUR
    assert endpoint.dependencies == (
        "bounded_common_multiple_exists",
        "doubled_square_plus_one_has_prime_divisor",
        "prime_divisor_of_doubled_square_plus_one_is_one_mod_four",
        "doubled_square_prime_divisor_exceeds_common_multiple_bound",
    )
    assert sha256(endpoint.statement.encode()).hexdigest() == (
        EXPECTED_ROOT_STATEMENT_SHA256
    )
    assert "gap + S B = p" in endpoint.statement
    assert "p) = 4 * pomf_one_result + 1" in endpoint.statement
    assert "p = 1" in endpoint.statement

    formula = _closed_formula(endpoint.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Exists)
    assert isinstance(formula.body.body, And)
    primality = formula.body.body.left
    bounds = formula.body.body.right
    assert isinstance(primality, And)
    assert isinstance(bounds, And)
    assert isinstance(bounds.left, Exists)
    assert isinstance(bounds.right, Exists)


def test_only_preexisting_checked_theorems_are_used_as_external_authority() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in rows()
        for dependency in item.dependencies
        if dependency not in local
    }

    assert external == {
        "add_comm",
        "bounded_common_multiple_exists",
        "divides_remainder",
        "divisor_one",
        "even_odd_exclusive_pointwise",
        "le_or_lt",
        "mul_assoc",
        "mul_eq_zero",
        "mul_one",
        "multiple_mul_left",
        "multiple_mul_right",
        "nonzero_is_succ",
        "prime_divisor_exists",
        "prime_mod_four_trichotomy",
        "prime_nonzero",
        "three_mod_four_prime_divides_two_square_norm_divides_both",
    }
    assert all(v18.ALPHA_EDITION.by_name[name].checked_use for name in external)
    assert "infinitely_many_primes_three_mod_four" not in external
    assert "prime_is_two_squares_iff_two_or_one_mod_four" not in external


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_candidate_conclusions_are_independently_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    available = core() | {item.name: item for item in rows()}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_candidate_scripts_cannot_become_proof_evidence(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])
    available = core() | {item.name: item for item in rows()}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize(
    "name",
    tuple(
        name
        for name in EXPECTED_NAMES
        if name != "doubled_square_plus_one_nonzero"
    ),
)
def test_missing_declared_dependency_fails_closed(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    available = core() | {item.name: item for item in rows()}

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize("bound", (0, 1, 2, 4, 6, 10, 12, 16))
def test_numerical_euclid_witnesses_illustrate_the_checked_construction(
    bound: int,
) -> None:
    common = 1
    for value in range(1, bound + 1):
        common = common // gcd(common, value) * value
    norm = (2 * common) * (2 * common) + 1
    divisor = next(
        (value for value in range(2, isqrt(norm) + 1) if norm % value == 0),
        norm,
    )

    assert norm % divisor == 0
    assert all(divisor % value for value in range(2, isqrt(divisor) + 1))
    assert divisor > bound
    assert divisor % 4 == 1
