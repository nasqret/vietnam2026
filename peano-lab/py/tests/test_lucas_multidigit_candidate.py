"""Focused constructive audit of coherent arbitrary-length Lucas digit traces."""

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
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.lucas_block_digit_candidate import (
    make_lucas_block_digit_candidate_theorems,
)
from peano_lab.library.lucas_multidigit_candidate import (
    LUCAS_CHOOSE_PREFIX_EMPTY,
    LUCAS_CHOOSE_PREFIX_EXISTS,
    LUCAS_CHOOSE_PREFIX_POINT,
    LUCAS_CHOOSE_PREFIX_EXTEND,
    LUCAS_DIGIT_CHAIN_EMPTY,
    LUCAS_DIGIT_CHAIN_EMPTY_EXISTS,
    LUCAS_DIGIT_CHAIN_EXISTS,
    LUCAS_DIGIT_CHAIN_EXTEND,
    LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS,
    LUCAS_DIGIT_CHAIN_INITIAL_VALUE,
    LUCAS_DIGIT_CHAIN_STEP_EXISTS,
    LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD,
    LUCAS_MULTIDIGIT_CONGRUENCE,
    LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP,
    LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND,
    LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO,
    LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT,
    LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP,
    LUCAS_TERMINATING_MULTIDIGIT_THEOREM,
    LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS,
    LUCAS_THEOREM,
    LUCAS_THEOREM_FOR_LENGTH,
    LUCAS_PRIME_DIGIT_CHAIN_EXISTS,
    make_lucas_multidigit_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive, _specs_by_name


EXPECTED_NAMES = (
    LUCAS_DIGIT_CHAIN_INITIAL_CODE_EXISTS,
    LUCAS_DIGIT_CHAIN_EMPTY,
    LUCAS_DIGIT_CHAIN_EMPTY_EXISTS,
    LUCAS_DIGIT_CHAIN_EXTEND,
    LUCAS_DIGIT_CHAIN_EXISTS,
    LUCAS_PRIME_DIGIT_CHAIN_EXISTS,
    LUCAS_DIGIT_CHAIN_INITIAL_VALUE,
    LUCAS_DIGIT_CHAIN_STEP_EXISTS,
    LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD,
    LUCAS_CHOOSE_PREFIX_EMPTY,
    LUCAS_CHOOSE_PREFIX_EXTEND,
    LUCAS_CHOOSE_PREFIX_EXISTS,
    LUCAS_CHOOSE_PREFIX_POINT,
    LUCAS_MULTIDIGIT_CONGRUENCE_FROM_ONE_STEP,
    LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP,
    LUCAS_PRIME_DIGIT_NONZERO_QUOTIENT_STRICT,
    LUCAS_PRIME_DIGIT_CHAIN_NONZERO_INDEX_BOUND,
    LUCAS_PRIME_DIGIT_CHAIN_TERMINAL_ZERO,
    LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS,
    LUCAS_MULTIDIGIT_CONGRUENCE,
    LUCAS_TERMINATING_MULTIDIGIT_THEOREM,
    LUCAS_THEOREM_FOR_LENGTH,
    LUCAS_THEOREM,
)

EXPECTED_FLAGSHIP_STATEMENTS = {
    LUCAS_DIGIT_CHAIN_EXISTS: (
        1_566,
        "1761ba49ed540370bfed36630364865f9adc49d5f549be0bebf1f71a5ba5b082",
    ),
    LUCAS_MODULAR_BACKWARD_PRODUCT_FOLD: (
        3_709,
        "53e3a474d9672635e77fc1b9dc4d50d66d9bb3f487f27fd2a3e77268d50977a9",
    ),
    LUCAS_TERMINATING_PRIME_DIGIT_CHAIN_EXISTS: (
        2_401,
        "e7519d8f5c7600546594ca5db83677d7bc01ab26d960fdb928e2707286df8e45",
    ),
    LUCAS_MULTIDIGIT_CONGRUENCE: (
        29_483,
        "e2f9f557280fd3a7142f86b9a66faadf243a65f8d9d5ba5e599de06f75e2fbb7",
    ),
    LUCAS_TERMINATING_MULTIDIGIT_THEOREM: (
        29_917,
        "89c221df26cc91d9a6de17522d2abf137bb1c11601fddf3fe212ab19b6c4b395",
    ),
    LUCAS_THEOREM_FOR_LENGTH: (
        38_521,
        "855e865592946ebe0bd8f0856edb73bc521c2db254a730ccc3e4851384d21ebb",
    ),
    LUCAS_THEOREM: (
        38_430,
        "396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564",
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_lucas_multidigit_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


@lru_cache(maxsize=1)
def _external_core() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in make_lucas_block_digit_candidate_theorems(TheoremSpec)
        if item.name == "lucas_one_step_division_congruence"
    }


def _core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _alpha_core() | _external_core() | {item.name: item for item in _rows()[:index]}


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str):
    row = next(item for item in _rows() if item.name == name)
    target = _closed_formula(row.statement)
    core = _core(name)
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
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        pending.extend(
            child
            for field in fields(current)
            if isinstance((child := getattr(current, field.name)), Proof)
        )


def test_multidigit_candidates_are_native_closed_isolated_and_ordered() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    stable = _specs_by_name()
    observed: set[str] = set()
    for row in rows:
        assert row.name not in stable
        assert row.name not in _alpha_core()
        assert set(row.dependencies) <= set(_alpha_core()) | set(_external_core()) | observed
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(token not in row.statement for token in ("BetaAt(", "Digit(", "Chain(", "^"))
        observed.add(row.name)


def test_multidigit_bodies_independently_replay_with_bounded_receipts() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_alpha_core() | _external_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(item.proof_nodes for item in receipts) <= 600
    assert max(item.proof_depth for item in receipts) <= 120


@pytest.mark.parametrize("name", tuple(EXPECTED_FLAGSHIP_STATEMENTS))
def test_multidigit_flagship_formulas_have_exact_frozen_hashes(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    assert (len(row.statement), sha256(row.statement.encode()).hexdigest()) == (
        EXPECTED_FLAGSHIP_STATEMENTS[name]
    )


def test_full_lucas_root_is_unconditional_and_uses_checked_prime_block() -> None:
    final = next(item for item in _rows() if item.name == LUCAS_THEOREM)
    unconditional = next(
        item for item in _rows() if item.name == LUCAS_TERMINATING_MULTIDIGIT_THEOREM
    )
    assert final.statement.startswith("forall p n k C.")
    assert unconditional.dependencies == (
        "lucas_one_step_division_congruence",
        LUCAS_TERMINATING_MULTIDIGIT_THEOREM_FROM_ONE_STEP,
    )
    assert tuple(_external_core()) == ("lucas_one_step_division_congruence",)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_multidigit_body_is_constructive_and_rejects_false_target(name: str) -> None:
    proof, target = _body(name)
    assert check((), proof, target)
    assert all(type(node) is not DNE for node in _walk(proof))
    row = next(item for item in _rows() if item.name == name)
    mutation = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutation,), core=_core(name))


@pytest.mark.parametrize("base", (2, 3, 4, 5, 7, 11, 13))
@pytest.mark.parametrize("length", (0, 1, 2, 3, 7, 12))
def test_successive_digit_chains_are_coherent_for_arbitrary_finite_lengths(
    base: int,
    length: int,
) -> None:
    for original in (0, 1, base - 1, base, base * base + 3, 317):
        quotients = [original]
        digits: list[int] = []
        for _ in range(length):
            quotient, digit = divmod(quotients[-1], base)
            quotients.append(quotient)
            digits.append(digit)
        assert len(quotients) == length + 1
        assert len(digits) == length
        assert quotients[0] == original
        assert all(
            quotients[index] == base * quotients[index + 1] + digits[index]
            and digits[index] < base
            for index in range(length)
        )


@pytest.mark.parametrize("prime_modulus", (2, 3, 5, 7, 11, 13))
def test_complete_lucas_digit_product_matches_binomial_examples(
    prime_modulus: int,
) -> None:
    for upper in range(55):
        for lower in range(62):
            left = comb(upper, lower) if lower <= upper else 0
            quotient_upper = upper
            quotient_lower = lower
            digit_product = 1
            while quotient_upper or quotient_lower:
                quotient_upper, upper_digit = divmod(quotient_upper, prime_modulus)
                quotient_lower, lower_digit = divmod(quotient_lower, prime_modulus)
                digit_product *= (
                    comb(upper_digit, lower_digit)
                    if lower_digit <= upper_digit
                    else 0
                )
            assert left % prime_modulus == digit_product % prime_modulus
