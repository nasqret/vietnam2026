"""Exact constructive audit of the one-digit Lucas/Kummer boundary."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import comb

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.lucas_digit_candidate import (
    LUCAS_BASE_P_DIGIT_FUNCTIONAL,
    LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE,
    LUCAS_BASE_P_DIGIT_PREFIX_EXISTS,
    LUCAS_BASE_P_DIGIT_PREFIX_POINT,
    LUCAS_BASE_P_DIGIT_TOTAL,
    LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION,
    LUCAS_BASE_P_TWO_DIGIT_TOTAL,
    LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES,
    LUCAS_CHOOSE_PRIME_DIVISOR_BOUND,
    LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES,
    LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES,
    LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES,
    LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS,
    LUCAS_PRIME_BASE_DIGIT_TOTAL,
    LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL,
    LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE,
    LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE,
    LUCAS_PRIME_ROW_SPARSE_COMPLETE,
    LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE,
    make_lucas_digit_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES,
    LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE,
    LUCAS_CHOOSE_PRIME_DIVISOR_BOUND,
    LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES,
    LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES,
    LUCAS_BASE_P_DIGIT_TOTAL,
    LUCAS_PRIME_BASE_DIGIT_TOTAL,
    LUCAS_BASE_P_DIGIT_FUNCTIONAL,
    LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE,
    LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES,
    LUCAS_BASE_P_DIGIT_PREFIX_EXISTS,
    LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS,
    LUCAS_BASE_P_DIGIT_PREFIX_POINT,
    LUCAS_BASE_P_TWO_DIGIT_TOTAL,
    LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL,
    LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION,
    LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE,
    LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE,
    LUCAS_PRIME_ROW_SPARSE_COMPLETE,
)

EXPECTED_STATEMENTS = {
    LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES: (
        8_848, "979a0d1d2e7bb1944318ed9db078c52bb2a23df21398d4ba22b83c31b92179dc"
    ),
    LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE: (
        8_450, "78827a3b8078769874d47ec33599ae70c9ade5b2d941ac40246da48f9116c41b"
    ),
    LUCAS_CHOOSE_PRIME_DIVISOR_BOUND: (
        8_735, "036809b0c7f5ca8a171462d4100c4340b99e42c43c2a323fb2bd1bc5ee569699"
    ),
    LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES: (
        8_968, "f2a21464f86d511c8d99ac535cb4029fa135d2bd3b6374493fdffbd347dd0f50"
    ),
    LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES: (
        8_990, "9a74ff6b08f258fd917297aa5bc1f2f04d419554b0f5896e5f7ea363a8c61d30"
    ),
    LUCAS_BASE_P_DIGIT_TOTAL: (
        126, "6685bc27979b311bddc2e6bf7e8b191dc1e16542193597c8d53ac45acaf176fe"
    ),
    LUCAS_PRIME_BASE_DIGIT_TOTAL: (
        398, "089da6d48aba1e3302f183dd62a10a2f68f38d722bcaf5a018b0e3c09f6ce95d"
    ),
    LUCAS_BASE_P_DIGIT_FUNCTIONAL: (
        234, "fea6557056a8c8bd1747489531b2a794f61cf303001a560d8d889d78c37c9fb4"
    ),
    LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE: (
        193, "dbd1150433374b9322261598e7ea585c5f43cd00c04b5c109d5cbb1ef7e8833b"
    ),
    LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES: (
        278, "6cdd9024b8eaa32e34721d770a94d73fad56bb1a4afa39b8dd1f31893ce6a538"
    ),
    LUCAS_BASE_P_DIGIT_PREFIX_EXISTS: (
        1_432, "3a060a4e4a2c89b9801d3ea6a052171e1de8923e48da1dd1d43abf2dbab6070a"
    ),
    LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS: (
        1_674, "2c5e3f6a3d59ee8dc2a189d1a8ca4a94be9d07daa229c94bdbdee506fdcae6f8"
    ),
    LUCAS_BASE_P_DIGIT_PREFIX_POINT: (
        2_065, "4217c5f9ca75041c820053c41665d23687ad3a48f588cd7e05abfa719d8f1ff0"
    ),
    LUCAS_BASE_P_TWO_DIGIT_TOTAL: (
        237, "41c769ba481935c92351620c4cbdff5f4f5f3f15fa9f4bc6bc878450f4c47900"
    ),
    LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL: (
        497, "18e43f99a7500b235e1da5ae63632f350d67c28b6ccc57b3a957f490d548989c"
    ),
    LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION: (
        249, "c81452d56a730c9291f6bcb1f8e4eb39f45e8aead52c465c9ac54249e440ed2d"
    ),
    LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE: (
        8_205, "737b4cb1da1a11db8a42ed424fa0ef051d548da1e5fa0e0d10d60de1c230b21a"
    ),
    LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE: (
        8_366, "9eabfb948d4101973cd645ad0c140c611173cb777d02e3907dfaa6d032cf5d6f"
    ),
    LUCAS_PRIME_ROW_SPARSE_COMPLETE: (
        25_017, "f0804ab6b8a14d05793a9d026a4ffe360d205f67312476099e22e02a7b3c5e8c"
    ),
}

EXPECTED_DEPENDENCIES = {
    LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES: (
        "choose_prime_divides_between",
    ),
    LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE: (
        "choose_prime_divides_between", "le_refl",
    ),
    LUCAS_CHOOSE_PRIME_DIVISOR_BOUND: (
        "factorial_exists", "choose_factorial_bridge", "multiple_mul_left",
        "factorial_prime_le_of_divides",
    ),
    LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES: (
        LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES,
        LUCAS_CHOOSE_PRIME_DIVISOR_BOUND,
    ),
    LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES: (
        LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES, "lt_not_le", "le_or_lt",
    ),
    LUCAS_BASE_P_DIGIT_TOTAL: ("division_remainder_exists",),
    LUCAS_PRIME_BASE_DIGIT_TOTAL: (
        "prime_nonzero", LUCAS_BASE_P_DIGIT_TOTAL,
    ),
    LUCAS_BASE_P_DIGIT_FUNCTIONAL: ("division_remainder_unique",),
    LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE: (
        "division_remainder_unique", "zero_add",
    ),
    LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES: (
        "zero_remainder_implies_multiple",
        "eq_decidable",
        "nonzero_remainder_not_multiple",
    ),
    LUCAS_BASE_P_DIGIT_PREFIX_EXISTS: ("beta_division_prefix_exists",),
    LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS: (
        "prime_nonzero", LUCAS_BASE_P_DIGIT_PREFIX_EXISTS,
    ),
    LUCAS_BASE_P_DIGIT_PREFIX_POINT: ("beta_at_unique",),
    LUCAS_BASE_P_TWO_DIGIT_TOTAL: (LUCAS_BASE_P_DIGIT_TOTAL,),
    LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL: (
        "prime_nonzero", LUCAS_BASE_P_TWO_DIGIT_TOTAL,
    ),
    LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION: (
        "mul_add", "mul_assoc", "add_assoc",
    ),
    LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE: ("choose_zero",),
    LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE: ("choose_self",),
    LUCAS_PRIME_ROW_SPARSE_COMPLETE: (
        LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE,
        LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE,
        LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE,
    ),
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_RECEIPTS = {
    LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES: (1, 21, 43, 27, 43, 42, 0),
    LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE: (2, 22, 48, 28, 48, 47, 0),
    LUCAS_CHOOSE_PRIME_DIVISOR_BOUND: (4, 49, 57, 32, 57, 56, 0),
    LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES: (2, 31, 69, 27, 69, 68, 0),
    LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES: (3, 37, 61, 27, 61, 60, 0),
    LUCAS_BASE_P_DIGIT_TOTAL: (1, 7, 15, 10, 15, 14, 0),
    LUCAS_PRIME_BASE_DIGIT_TOTAL: (2, 11, 25, 16, 25, 24, 0),
    LUCAS_BASE_P_DIGIT_FUNCTIONAL: (1, 21, 58, 34, 58, 57, 0),
    LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE: (2, 18, 57, 31, 57, 56, 0),
    LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES: (3, 29, 76, 33, 76, 75, 0),
    LUCAS_BASE_P_DIGIT_PREFIX_EXISTS: (1, 11, 25, 16, 25, 24, 0),
    LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS: (2, 15, 35, 22, 35, 34, 0),
    LUCAS_BASE_P_DIGIT_PREFIX_POINT: (1, 43, 57, 31, 57, 56, 0),
    LUCAS_BASE_P_TWO_DIGIT_TOTAL: (1, 24, 27, 14, 27, 26, 0),
    LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL: (2, 11, 25, 16, 25, 24, 0),
    LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION: (3, 25, 55, 31, 55, 54, 0),
    LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE: (1, 7, 15, 10, 15, 14, 0),
    LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE: (1, 7, 15, 10, 15, 14, 0),
    LUCAS_PRIME_ROW_SPARSE_COMPLETE: (3, 33, 67, 32, 67, 66, 0),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_lucas_digit_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


def _core_before(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _alpha_core() | {row.name: row for row in _rows()[:index]}


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str):
    row = next(item for item in _rows() if item.name == name)
    core = _core_before(name)
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(core[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(
            child
            for field in fields(node)
            if isinstance((child := getattr(node, field.name)), Proof)
        )


def test_lucas_digit_factory_is_exact_topological_and_isolated() -> None:
    rows = _rows()
    assert make_lucas_digit_candidate_theorems(TheoremSpec) == rows
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {row.name: row.dependencies for row in rows} == EXPECTED_DEPENDENCIES
    assert all(row.name not in _alpha_core() for row in rows)
    assert all(row.name not in _specs_by_name() for row in rows)
    observed: set[str] = set()
    for row in rows:
        assert set(row.dependencies) <= set(_alpha_core()) | observed
        observed.add(row.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_lucas_digit_statement_is_pinned_closed_and_first_order(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    assert (len(row.statement), sha256(row.statement.encode()).hexdigest()) == (
        EXPECTED_STATEMENTS[name]
    )
    formula, free_names = parse_formula_with_names(row.statement)
    assert not free_names
    assert formula == _closed_formula(row.statement)
    assert all(
        token not in row.statement
        for token in ("Prime(", "Choose(", "Divides(", "Lucas(", "^", "%", "↔")
    )


def test_lucas_digit_all_proof_bodies_have_exact_bounded_receipts() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_alpha_core())
    assert {
        row.name: (
            row.dependency_count, row.command_count, row.proof_nodes,
            row.proof_depth, row.proof_objects, row.proof_edges,
            row.reused_objects,
        )
        for row in receipts
    } == EXPECTED_RECEIPTS
    assert max(row.proof_nodes for row in receipts) == 76
    assert max(row.proof_depth for row in receipts) == 34


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_lucas_digit_kernel_proof_is_constructive_and_mutation_safe(
    name: str,
) -> None:
    body, target = _body(name)
    assert check((), body, target)
    assert all(type(node) is not DNE for node in _walk(body))
    row = next(item for item in _rows() if item.name == name)
    mutated = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core_before(name))


@pytest.mark.parametrize(
    ("name", "dependency"),
    tuple(
        (name, dependency)
        for name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_every_lucas_digit_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    row = next(item for item in _rows() if item.name == name)
    shortened = replace(
        row,
        dependencies=tuple(item for item in row.dependencies if item != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_core_before(name))


@pytest.mark.parametrize("prime_modulus", (2, 3, 5, 7, 11, 13, 17))
def test_all_one_digit_carries_match_prime_binomial_divisibility(
    prime_modulus: int,
) -> None:
    for left in range(prime_modulus):
        for right in range(prime_modulus):
            coefficient = comb(left + right, left)
            carries = left + right >= prime_modulus
            assert (coefficient % prime_modulus == 0) is carries
            assert (coefficient % prime_modulus != 0) is (not carries)


@pytest.mark.parametrize("prime_modulus", (2, 3, 5, 7, 11, 13, 17, 19))
def test_all_prime_row_interior_coefficients_are_divisible(
    prime_modulus: int,
) -> None:
    assert all(
        comb(prime_modulus, index) % prime_modulus == 0
        for index in range(1, prime_modulus)
    )


def test_prime_premise_and_digit_bounds_are_mathematically_essential() -> None:
    assert comb(4, 2) % 4 != 0
    assert comb(6, 3) % 6 != 0
    # Outside the one-digit contract, a carry at the units position need
    # not be detected by comparing the entire sum against the modulus.
    assert comb(2 + 5, 2) % 5 != 0


@pytest.mark.parametrize("base", (2, 3, 4, 5, 7, 9, 11, 13, 17, 19))
def test_base_digit_totality_functionality_and_zero_divisibility_examples(
    base: int,
) -> None:
    for value in range(0, 4 * base * base + 1):
        quotient, digit = divmod(value, base)
        assert value == base * quotient + digit
        assert 0 <= digit < base
        assert (digit == 0) is (value % base == 0)
        assert all(
            (other_quotient, other_digit) == (quotient, digit)
            for other_quotient in range(value // base + 2)
            for other_digit in range(base)
            if value == base * other_quotient + other_digit
        )


@pytest.mark.parametrize("base", (2, 3, 5, 7, 11, 13, 17, 19))
def test_small_values_are_their_own_unique_base_digits(base: int) -> None:
    for value in range(base):
        quotient, digit = divmod(value, base)
        assert quotient == 0
        assert digit == value


@pytest.mark.parametrize("base", (2, 3, 5, 7, 11))
def test_finite_source_prefix_has_aligned_quotient_and_digit_prefixes(
    base: int,
) -> None:
    source = tuple(index * index + 3 * index + 7 for index in range(24))
    quotients = tuple(value // base for value in source)
    digits = tuple(value % base for value in source)

    assert len(source) == len(quotients) == len(digits)
    for index, value in enumerate(source):
        assert value == base * quotients[index] + digits[index]
        assert digits[index] < base
        assert (digits[index] == 0) is (value % base == 0)


@pytest.mark.parametrize("base", (2, 3, 5, 7, 11, 13, 17, 19))
def test_prime_pascal_row_is_sparse_modulo_its_prime_base(base: int) -> None:
    residues = tuple(comb(base, index) % base for index in range(base + 1))
    assert residues == (1,) + (0,) * (base - 1) + (1,)


@pytest.mark.parametrize("base", (2, 3, 4, 5, 7, 11, 13, 17))
def test_two_successive_base_digits_are_coherent_and_reconstruct_the_input(
    base: int,
) -> None:
    for value in range(3 * base * base + base + 1):
        first_quotient, first_digit = divmod(value, base)
        second_quotient, second_digit = divmod(first_quotient, base)

        assert value == base * first_quotient + first_digit
        assert first_quotient == base * second_quotient + second_digit
        assert first_digit < base
        assert second_digit < base
        assert value == (base * base) * second_quotient + (
            base * second_digit + first_digit
        )
