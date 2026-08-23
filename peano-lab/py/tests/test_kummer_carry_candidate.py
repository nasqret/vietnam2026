"""Bounded, fail-closed audit for the constructive general Kummer endpoint.

Every proof checked here is dependency-curried. Alpha-v12 specifications and
the preceding Kummer valuation tranche are hypotheses, not trusted facts or
empty-context certificates.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
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
from peano_lab.library.kummer_carry_candidate import (
    ADD_QUOTIENT_CARRY_CHOICE,
    ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS,
    ADD_QUOTIENT_CARRY_PREFIX_EXISTS,
    ADD_QUOTIENT_CARRY_PREFIX_EXTEND,
    ADD_QUOTIENT_CARRY_PREFIX_RESTRICT,
    BETA_SUM_ADD_CARRY_EXACT,
    KUMMER_BINOMIAL_CARRY_BIT_COUNT,
    KUMMER_CARRY_FREE_IFF_NOT_DIVIDES,
    PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES,
    _add_carry_prefix,
    make_kummer_carry_candidate_theorems,
    make_kummer_carry_corollary_candidate_theorems,
)
from peano_lab.library.kummer_valuation_candidate import (
    BINOMIAL_LEGENDRE_VALUATION_BALANCE,
    DIVISION_ADD_QUOTIENT_BIT,
    make_kummer_valuation_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    ADD_QUOTIENT_CARRY_CHOICE,
    ADD_QUOTIENT_CARRY_PREFIX_EXTEND,
    ADD_QUOTIENT_CARRY_PREFIX_EXISTS,
    ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS,
    ADD_QUOTIENT_CARRY_PREFIX_RESTRICT,
    BETA_SUM_ADD_CARRY_EXACT,
    KUMMER_BINOMIAL_CARRY_BIT_COUNT,
)

EXPECTED_DEPENDENCIES = {
    ADD_QUOTIENT_CARRY_CHOICE: ("pow_functional", DIVISION_ADD_QUOTIENT_BIT),
    ADD_QUOTIENT_CARRY_PREFIX_EXTEND: (
        "beta_prefix_extend", "finite_lt_succ_eq_or_lt",
    ),
    ADD_QUOTIENT_CARRY_PREFIX_EXISTS: (
        "add_eq_zero_right", "succ_ne_zero", "le_succ", "le_refl",
        ADD_QUOTIENT_CARRY_CHOICE, ADD_QUOTIENT_CARRY_PREFIX_EXTEND,
    ),
    ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS: (),
    ADD_QUOTIENT_CARRY_PREFIX_RESTRICT: ("le_succ",),
    BETA_SUM_ADD_CARRY_EXACT: (
        "beta_sum_zero", "beta_sum_succ_decompose", "bit_count_zero",
        "bit_count_succ_decompose", "beta_at_unique", "le_refl",
        ADD_QUOTIENT_CARRY_PREFIX_RESTRICT, "add_assoc", "add_comm",
        "add_shuffle_middle",
    ),
    KUMMER_BINOMIAL_CARRY_BIT_COUNT: (
        "prime_legendre_sum_exists", BINOMIAL_LEGENDRE_VALUATION_BALANCE,
        "legendre_sum_extended_prefix_exists", "add_comm",
        ADD_QUOTIENT_CARRY_PREFIX_EXISTS, ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS,
        "bit_count_exists", BETA_SUM_ADD_CARRY_EXACT, "add_left_cancel",
    ),
}

EXPECTED_ARTIFACTS = {
    ADD_QUOTIENT_CARRY_CHOICE: (
        12_265, "f39e3a371da4c77acd0d86714471b379fd5c64d3ca2d5dd744cc6d3be36e04dd",
    ),
    ADD_QUOTIENT_CARRY_PREFIX_EXTEND: (
        3_596, "edb51fb89fb374db513d256119406d63d64fc59f806ad0c41eb33d56cac636a8",
    ),
    ADD_QUOTIENT_CARRY_PREFIX_EXISTS: (
        13_085, "27370fc43a46e90f0283406075c004cc3d93f8a29fb0d3bc547a4f5df4f140a7",
    ),
    ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS: (
        2_055, "c18399a0b22f4b06bbcb74763cdeb87530953dda0fd95aa1479370c9f54a1f80",
    ),
    ADD_QUOTIENT_CARRY_PREFIX_RESTRICT: (
        3_036, "87d588e2d5dd609a47c22ae1d7c06196f47f2497f176963c048a7773a76c6086",
    ),
    BETA_SUM_ADD_CARRY_EXACT: (
        9_029, "9e48ec840c9d3883cf61a11d93b0e2bf9f8721a58d97db92ab27ab3485be02ac",
    ),
    KUMMER_BINOMIAL_CARRY_BIT_COUNT: (
        32_858, "f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f",
    ),
}

EXPECTED_BODIES = {
    ADD_QUOTIENT_CARRY_CHOICE: (2, 105, 159, 40, 159, 158, 0),
    ADD_QUOTIENT_CARRY_PREFIX_EXTEND: (2, 85, 131, 44, 131, 130, 0),
    ADD_QUOTIENT_CARRY_PREFIX_EXISTS: (6, 94, 110, 40, 110, 109, 0),
    ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS: (0, 34, 42, 24, 42, 41, 0),
    ADD_QUOTIENT_CARRY_PREFIX_RESTRICT: (1, 18, 30, 22, 30, 29, 0),
    BETA_SUM_ADD_CARRY_EXACT: (10, 228, 640, 78, 635, 639, 5),
    KUMMER_BINOMIAL_CARRY_BIT_COUNT: (9, 157, 268, 65, 268, 267, 0),
}

EXPECTED_COROLLARY_DEPENDENCIES = {
    PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES: (
        "prime_divisor_power_valuation_nonzero",
        "power_valuation_nonzero_exponent_divides_base",
        "eq_decidable",
    ),
    KUMMER_CARRY_FREE_IFF_NOT_DIVIDES: (
        "choose_positive", "add_comm", PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES,
        KUMMER_BINOMIAL_CARRY_BIT_COUNT, "bit_count_functional",
    ),
}

EXPECTED_COROLLARY_BODIES = {
    PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES: (3, 31, 67, 27, 67, 66, 0),
    KUMMER_CARRY_FREE_IFF_NOT_DIVIDES: (5, 95, 194, 50, 188, 193, 6),
}

LIVE_EDGES = tuple(
    (name, dependency)
    for name, dependencies in EXPECTED_DEPENDENCIES.items()
    for dependency in dependencies
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_kummer_carry_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _corollary_rows() -> tuple[TheoremSpec, ...]:
    return make_kummer_carry_corollary_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support() -> dict[str, TheoremSpec]:
    alpha = {item.name: item for item in editions_v12.ALPHA_SPECS}
    valuation = {
        item.name: item for item in make_kummer_valuation_candidate_theorems(TheoremSpec)
    }
    assert not set(alpha) & set(valuation)
    return alpha | valuation


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _support() | {item.name: item for item in _rows()[:index]}


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


@lru_cache(maxsize=len(EXPECTED_COROLLARY_BODIES))
def _corollary_body(name: str) -> tuple[Proof, Formula]:
    rows = _corollary_rows()
    index = tuple(EXPECTED_COROLLARY_DEPENDENCIES).index(name)
    item = rows[index]
    core = _support() | {row.name: row for row in _rows()} | {
        row.name: row for row in rows[:index]
    }
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
    result = 0
    while value % base == 0:
        result += 1
        value //= base
    return result


def _digit_carries(base: int, left: int, right: int) -> tuple[int, ...]:
    carries: list[int] = []
    previous = 0
    while left or right:
        left, left_digit = divmod(left, base)
        right, right_digit = divmod(right, base)
        previous = int(left_digit + right_digit + previous >= base)
        carries.append(previous)
    return tuple(carries)


def test_kummer_carry_static_contract_and_isolation() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert len(LIVE_EDGES) == 30

    alpha = {item.name for item in editions_v12.ALPHA_SPECS}
    stable = set(_specs_by_name())
    support = _support()
    seen: set[str] = set()
    for item in rows:
        assert item.dependencies == EXPECTED_DEPENDENCIES[item.name]
        assert item.name not in alpha
        assert item.name not in stable
        assert item.name not in support
        assert all(dependency in support or dependency in seen for dependency in item.dependencies)
        assert _closed_formula(item.statement)
        seen.add(item.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kummer_carry_artifacts_are_frozen(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    assert (
        len(item.statement), sha256(item.statement.encode()).hexdigest()
    ) == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kummer_carry_bodies_are_constructive_and_bounded(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    body, target = _body(name)
    assert check((), body, target)
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert nodes <= 650
    assert depth <= 80
    assert not any(type(node) is DNE for node in _walk(body))
    assert (
        len(item.dependencies), len(item.script), nodes, depth, objects, edges, reused
    ) == EXPECTED_BODIES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_kummer_carry_every_dependency_is_live(name: str, dependency: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    shortened = replace(
        item,
        dependencies=tuple(entry for entry in item.dependencies if entry != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kummer_carry_false_targets_are_rejected(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_kummer_carry_prefix_rejects_captured_generated_binders() -> None:
    with pytest.raises(ValueError, match="captures"):
        _add_carry_prefix(
            "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
            tag="capture", variables=("kmc_index_capture",),
        )


def test_kummer_carry_corollary_contract_and_isolation() -> None:
    rows = _corollary_rows()
    assert tuple(row.name for row in rows) == tuple(EXPECTED_COROLLARY_DEPENDENCIES)
    assert tuple(EXPECTED_COROLLARY_BODIES) == tuple(EXPECTED_COROLLARY_DEPENDENCIES)
    alpha = {row.name for row in editions_v12.ALPHA_SPECS}
    stable = set(_specs_by_name())
    for item in rows:
        assert item.dependencies == EXPECTED_COROLLARY_DEPENDENCIES[item.name]
        assert item.name not in alpha
        assert item.name not in stable
        assert _closed_formula(item.statement)


@pytest.mark.parametrize("name", tuple(EXPECTED_COROLLARY_BODIES))
def test_kummer_carry_corollary_bodies_are_constructive_and_bounded(name: str) -> None:
    item = next(row for row in _corollary_rows() if row.name == name)
    body, target = _corollary_body(name)
    assert check((), body, target)
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert nodes <= 200
    assert depth <= 50
    assert not any(type(node) is DNE for node in _walk(body))
    assert (
        len(item.dependencies), len(item.script), nodes, depth, objects, edges, reused
    ) == EXPECTED_COROLLARY_BODIES[name]


@pytest.mark.parametrize("name", tuple(EXPECTED_COROLLARY_BODIES))
def test_kummer_carry_corollary_false_targets_are_rejected(name: str) -> None:
    rows = _corollary_rows()
    index = tuple(EXPECTED_COROLLARY_DEPENDENCIES).index(name)
    core = _support() | {row.name: row for row in _rows()} | {
        row.name: row for row in rows[:index]
    }
    mutated = replace(rows[index], statement=f"({rows[index].statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=core)


@pytest.mark.parametrize(
    ("base", "left", "right", "expected"),
    (
        (2, 3, 7, (1, 1, 1)),
        (2, 8, 5, (0, 0, 0, 0)),
        (3, 5, 7, (1, 1)),
        (5, 2, 4, (1,)),
        (5, 6, 2, (0, 0)),
        (5, 12, 8, (1, 0)),
        (7, 0, 19, (0, 0)),
    ),
)
def test_kummer_carry_exact_independent_examples(
    base: int,
    left: int,
    right: int,
    expected: tuple[int, ...],
) -> None:
    carries = _digit_carries(base, left, right)
    assert carries == expected
    assert _valuation(base, comb(left + right, left)) == sum(carries)
    assert (sum(carries) == 0) == (comb(left + right, left) % base != 0)
