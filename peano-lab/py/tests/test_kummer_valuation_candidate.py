"""Fail-closed audit for the first general-Kummer constructive tranche.

These tests check dependency-curried intuitionistic bodies only.  Alpha-v12
statements are supplied as explicit hypotheses; their membership is never
treated as an empty-context certificate or checked-use authorization.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from math import comb

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.kummer_valuation_candidate import (
    BINOMIAL_LEGENDRE_VALUATION_BALANCE,
    CHOOSE_FACTORIAL_VALUATION_BALANCE,
    CHOOSE_LEGENDRE_VALUATION_BALANCE,
    DIVISION_ADD_QUOTIENT_BIT,
    DIVISION_ADD_QUOTIENT_LOWER,
    DIVISION_ADD_QUOTIENT_UPPER,
    make_kummer_valuation_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    DIVISION_ADD_QUOTIENT_BIT,
    DIVISION_ADD_QUOTIENT_LOWER,
    DIVISION_ADD_QUOTIENT_UPPER,
    CHOOSE_FACTORIAL_VALUATION_BALANCE,
    CHOOSE_LEGENDRE_VALUATION_BALANCE,
    BINOMIAL_LEGENDRE_VALUATION_BALANCE,
)

EXPECTED_DEPENDENCIES = {
    DIVISION_ADD_QUOTIENT_BIT: (
        "le_or_lt",
        "le_eq_or_lt",
        "lt_not_le",
        "zero_le",
        "one_le_of_ne_zero",
        "add_shuffle_middle",
        "mul_add",
        "add_assoc",
        "add_comm",
        "add_lt_add",
        "add_lt_cancel_left",
        "division_remainder_unique",
    ),
    DIVISION_ADD_QUOTIENT_LOWER: (
        DIVISION_ADD_QUOTIENT_BIT,
        "le_refl",
        "le_succ",
    ),
    DIVISION_ADD_QUOTIENT_UPPER: (
        DIVISION_ADD_QUOTIENT_BIT,
        "le_refl",
        "le_succ",
    ),
    CHOOSE_FACTORIAL_VALUATION_BALANCE: (
        "add_comm",
        "choose_positive",
        "factorial_nonzero",
        "choose_factorial_bridge",
        "power_valuation_exists",
        "power_valuation_value_eq_transport",
        "prime_power_valuation_mul",
        "mul_ne_zero",
    ),
    CHOOSE_LEGENDRE_VALUATION_BALANCE: (
        "factorial_valuation_exists",
        "prime_factorial_valuation_eq_legendre_sum",
        CHOOSE_FACTORIAL_VALUATION_BALANCE,
    ),
    BINOMIAL_LEGENDRE_VALUATION_BALANCE: (
        CHOOSE_LEGENDRE_VALUATION_BALANCE,
    ),
}

EXPECTED_BODIES = {
    DIVISION_ADD_QUOTIENT_BIT: (12, 138, 242, 40, 240, 241, 2),
    DIVISION_ADD_QUOTIENT_LOWER: (3, 36, 46, 29, 46, 45, 0),
    DIVISION_ADD_QUOTIENT_UPPER: (3, 36, 46, 29, 46, 45, 0),
    CHOOSE_FACTORIAL_VALUATION_BALANCE: (8, 123, 169, 46, 167, 168, 2),
    CHOOSE_LEGENDRE_VALUATION_BALANCE: (3, 84, 96, 41, 96, 95, 0),
    BINOMIAL_LEGENDRE_VALUATION_BALANCE: (1, 31, 66, 41, 66, 65, 0),
}

LIVE_EDGES = tuple(
    (name, dependency)
    for name, dependencies in EXPECTED_DEPENDENCIES.items()
    for dependency in dependencies
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_kummer_valuation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _alpha_core() | {item.name: item for item in _rows()[:index]}


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str) -> tuple[Proof, Formula]:
    item = next(row for row in _rows() if row.name == name)
    core = _row_core(name)
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(core[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
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
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )


def _valuation(base: int, value: int) -> int:
    assert base >= 2
    assert value > 0
    exponent = 0
    while value % base == 0:
        exponent += 1
        value //= base
    return exponent


def _legendre(base: int, value: int) -> int:
    assert base >= 2
    result = 0
    while value:
        value //= base
        result += value
    return result


def _carry_count(base: int, left: int, right: int) -> int:
    assert base >= 2
    result = 0
    carry = 0
    while left or right:
        left, left_digit = divmod(left, base)
        right, right_digit = divmod(right, base)
        carry = int(left_digit + right_digit + carry >= base)
        result += carry
    return result


def test_kummer_valuation_static_contract_and_isolation() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert len(LIVE_EDGES) == 30

    alpha = _alpha_core()
    stable = _specs_by_name()
    seen: set[str] = set()
    for item in rows:
        assert item.dependencies == EXPECTED_DEPENDENCIES[item.name]
        assert item.name not in alpha
        assert item.name not in stable
        assert not (set(item.dependencies) & (set(EXPECTED_NAMES) - seen))
        assert all(dependency in alpha or dependency in seen for dependency in item.dependencies)
        assert _closed_formula(item.statement)
        seen.add(item.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kummer_valuation_bodies_are_checked_and_resource_bounded(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    body, target = _body(name)
    assert check((), body, target)
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert nodes <= 250
    assert depth <= 50
    assert not any(type(node) is DNE for node in _walk(body))
    assert actual == EXPECTED_BODIES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_kummer_valuation_every_dependency_is_live(name: str, dependency: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    shortened = replace(
        item,
        dependencies=tuple(entry for entry in item.dependencies if entry != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kummer_valuation_false_targets_are_rejected(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_kummer_valuation_genuine_mutations_have_counterexamples() -> None:
    # A carry is possible even when the inputs and their quotients differ.
    assert divmod(2, 5) == (0, 2)
    assert divmod(4, 5) == (0, 4)
    assert divmod(2 + 4, 5) == (1, 1)

    # A carry is not mandatory: strengthening the lower bound would be false.
    assert divmod(6, 5) == (1, 1)
    assert divmod(2, 5) == (0, 2)
    assert divmod(6 + 2, 5) == (1, 3)

    # The prime premise is essential; the analogous composite-base claim fails.
    assert comb(2 + 2, 2) == 6
    assert _valuation(4, 6) == 0
    assert _legendre(4, 4) - _legendre(4, 2) - _legendre(4, 2) == 1


@pytest.mark.parametrize("base", (2, 3, 5, 7, 11, 13))
def test_kummer_valuation_matches_independent_digit_examples(base: int) -> None:
    for left in range(25):
        for right in range(25):
            value = comb(left + right, left)
            exponent = _valuation(base, value)
            total = _legendre(base, left + right)
            left_sum = _legendre(base, left)
            right_sum = _legendre(base, right)
            assert total == left_sum + right_sum + exponent
            assert exponent == _carry_count(base, left, right)

            divisor = base
            while divisor <= left + right:
                left_quotient, _ = divmod(left, divisor)
                right_quotient, _ = divmod(right, divisor)
                total_quotient, _ = divmod(left + right, divisor)
                assert total_quotient in (
                    left_quotient + right_quotient,
                    left_quotient + right_quotient + 1,
                )
                divisor *= base

