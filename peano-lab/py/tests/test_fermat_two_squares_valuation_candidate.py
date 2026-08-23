"""Focused, dependency-curried audit of constructive two-square valuation bridges."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from itertools import product
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names, pretty_formula
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12, theorems as theorem_registry
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_valuation_candidate import (
    PRIME_POWER_VALUATION_SQUARE_EVEN,
    PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
    PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
    PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
    THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
    THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT,
    THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
    TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
    TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,
    TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM,
    TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO,
    TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR,
    TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS,
    make_fermat_two_squares_valuation_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS,
    TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO,
    PRIME_POWER_VALUATION_SQUARE_EVEN,
    TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,
    TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
    TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM,
    TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,
    THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT,
    PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
    PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
    THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
    PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
    THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN,
)

EXPECTED_DEPENDENCIES = {
    TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS: ("mul_eq_zero",),
    TWO_SQUARE_NORM_ZERO_IFF_COORDINATES_ZERO: (
        "add_eq_zero_left",
        "add_eq_zero_right",
        TWO_SQUARE_SELF_SQUARE_ZERO_REFLECTS,
    ),
    PRIME_POWER_VALUATION_SQUARE_EVEN: ("prime_power_valuation_mul",),
    TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY: ("mul_shuffle_four", "mul_add"),
    TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR: (
        TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,
    ),
    TWO_SQUARE_COMMON_SQUARED_FACTOR_DIVIDES_NORM: (
        TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
    ),
    TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR: (
        "every_natural_square_is_sum_of_two_squares",
        "two_square_representation_multiplicatively_closed",
    ),
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR: (
        "three_mod_four_prime_divides_two_square_norm_divides_both",
        TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
    ),
    THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT: (
        THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,
    ),
    PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT: (
        "power_valuation_exists",
        PRIME_POWER_VALUATION_SQUARE_EVEN,
        "mul_ne_zero",
        "prime_power_valuation_mul",
    ),
    PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS: (
        PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
        "add_shuffle_middle",
    ),
    THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS: (
        "power_valuation_nonzero_exponent_divides_base",
        THREE_MOD_FOUR_PRIME_NONZERO_TWO_SQUARE_NORM_EXTRACTS_NONZERO_QUOTIENT,
    ),
    PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES: (
        "prime_two_le",
        "succ_le_mul_of_two_le_right",
        "prime_nonzero",
        "one_le_of_ne_zero",
        "mul_le_mul_left",
        "mul_one",
        "le_trans",
        "mul_assoc",
        "mul_comm",
    ),
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED: (
        "le_zero",
        "eq_decidable",
        THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
        PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
        "le_trans",
        "le_of_succ_le_succ",
        "power_valuation_exists",
        "prime_nonzero",
        "power_valuation_value_eq_transport",
        PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
    ),
    THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN: (
        "le_refl",
        THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
    ),
    THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN: (
        "power_valuation_value_eq_transport",
        THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
    ),
}

EXTERNAL_NAMES = (
    "two_square_representation_multiplicatively_closed",
    "every_natural_square_is_sum_of_two_squares",
    "three_mod_four_prime_divides_two_square_norm_divides_both",
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_valuation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


@lru_cache(maxsize=1)
def _external_candidate_core() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in make_fermat_two_squares_classification_candidate_theorems(
            TheoremSpec
        )
        if item.name in EXTERNAL_NAMES
    }


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return (
        _alpha_core()
        | _external_candidate_core()
        | {item.name: item for item in _rows()[:index]}
    )


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str):
    row = next(item for item in _rows() if item.name == name)
    core = _row_core(name)
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(core[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        try:
            state = apply_tactic(state, tactic, arguments)
        except Exception as error:
            current = state.current()
            goal = (
                "<none>"
                if current is None
                else pretty_formula(current.target, list(current.variables))
            )
            raise type(error)(
                f"{row.name}: `{command}` at `{goal}`: {error}"
            ) from error
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


def _valuation(base: int, value: int) -> int:
    assert base >= 2
    assert value > 0
    exponent = 0
    while value % base == 0:
        value //= base
        exponent += 1
    return exponent


def test_two_square_valuation_candidates_are_isolated_and_dependency_ordered() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {row.name: row.dependencies for row in rows} == EXPECTED_DEPENDENCIES

    stable = _specs_by_name()
    alpha = _alpha_core()
    external = _external_candidate_core()
    assert set(external) == set(EXTERNAL_NAMES)
    assert all(name not in alpha and name not in stable for name in external)

    seen: set[str] = set()
    for row in rows:
        assert row.name not in alpha
        assert row.name not in stable
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(
            name in alpha or name in external or name in seen
            for name in row.dependencies
        )
        seen.add(row.name)

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "fermat_two_squares_valuation_candidate" not in registry_source


def test_two_square_valuation_contracts_are_closed_native_first_order_formulas() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in (
                "Prime(",
                "PowerVal(",
                "TwoSquare(",
                "FourThree(",
                "Even(",
                "abs(",
                "^",
                " - ",
            )
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_two_square_valuation_candidate_bodies_kernel_check_constructively(
    name: str,
) -> None:
    proof, target = _body(name)
    nodes, depth = proof_metrics(proof)
    objects, edges, reused = proof_identity_metrics(proof)

    assert check((), proof, target)
    assert nodes <= 300
    assert depth <= 90
    assert objects <= nodes
    assert edges >= objects - 1
    assert reused >= 0
    assert not any(type(node) is DNE for node in _walk(proof))


@pytest.mark.parametrize(
    ("name", "dependency"),
    (
        (PRIME_POWER_VALUATION_SQUARE_EVEN, "prime_power_valuation_mul"),
        (TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY, "mul_shuffle_four"),
        (
            TWO_SQUARE_COMMON_DIVISOR_EXTRACTS_SQUARED_FACTOR,
            TWO_SQUARE_COMMON_FACTOR_NORM_IDENTITY,
        ),
        (
            TWO_SQUARE_REPRESENTATION_PRESERVED_BY_SQUARE_FACTOR,
            "two_square_representation_multiplicatively_closed",
        ),
        (
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_EXTRACTS_SQUARED_FACTOR,
            "three_mod_four_prime_divides_two_square_norm_divides_both",
        ),
        (
            PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
            PRIME_POWER_VALUATION_SQUARE_EVEN,
        ),
        (
            PRIME_POWER_VALUATION_SQUARE_FACTOR_PRESERVES_EVENNESS,
            PRIME_POWER_VALUATION_SQUARE_FACTOR_SHIFT,
        ),
        (
            THREE_MOD_FOUR_PRIME_NONZERO_NORM_POSITIVE_VALUATION_EXTRACTS,
            "power_valuation_nonzero_exponent_divides_base",
        ),
        (
            PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
            "succ_le_mul_of_two_le_right",
        ),
        (
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN_BOUNDED,
            PRIME_SQUARE_TIMES_NONZERO_STRICTLY_INCREASES,
        ),
        (
            THREE_MOD_FOUR_PRIME_REPRESENTED_NONZERO_VALUATION_EVEN,
            THREE_MOD_FOUR_PRIME_TWO_SQUARE_NORM_VALUATION_EVEN,
        ),
    ),
)
def test_two_square_valuation_essential_dependencies_are_live(
    name: str, dependency: str
) -> None:
    row = next(item for item in _rows() if item.name == name)
    mutation = replace(
        row,
        dependencies=tuple(value for value in row.dependencies if value != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutation,), core=_row_core(name))


def test_two_square_zero_boundary_and_common_factor_oracles() -> None:
    for a, b in product(range(15), repeat=2):
        assert (a * a + b * b == 0) == (a == 0 and b == 0)

    for p, u, v in product(range(8), repeat=3):
        a, b = p * u, p * v
        assert a * a + b * b == p * p * (u * u + v * v)


def test_square_valuation_doubling_and_evenness_shift_oracles() -> None:
    for p in (2, 3, 5, 7, 11):
        for z, n in product(range(1, 36), repeat=2):
            factor = _valuation(p, z)
            quotient = _valuation(p, n)
            assert _valuation(p, z * z) == factor + factor
            assert _valuation(p, z * z * n) == factor + factor + quotient
            if quotient % 2 == 0:
                assert _valuation(p, z * z * n) % 2 == 0


def test_three_mod_four_prime_extracts_square_from_nonzero_norm_oracle() -> None:
    observed = 0
    for p in (3, 7, 11, 19):
        for a, b in product(range(1, 50), repeat=2):
            norm = a * a + b * b
            if norm % p:
                continue
            assert a % p == 0
            assert b % p == 0
            quotient = (a // p) ** 2 + (b // p) ** 2
            assert quotient > 0
            assert norm == p * p * quotient
            assert _valuation(p, norm) % 2 == 0
            observed += 1

    assert observed > 0


def test_two_square_valuation_scripts_avoid_hidden_or_classical_automation() -> None:
    commands = tuple(command for row in _rows() for command in row.script)
    assert "apply prime_power_valuation_mul" in commands
    assert "apply add_shuffle_middle" in commands
    assert all(not command.startswith(("auto", "ring", "use ")) for command in commands)
    assert all("DNE" not in command and "sorry" not in command for command in commands)


def test_two_square_valuation_rfc_preserves_evidence_and_zero_boundaries() -> None:
    repository = Path(__file__).resolve().parents[3]
    rfc = (
        repository
        / "research"
        / "arithmetic-library"
        / "fermat-two-squares-valuation-rfc-v1.md"
    ).read_text(encoding="utf-8")

    for name in EXPECTED_NAMES:
        assert f"`{name}`" in rfc
    assert "zero has no asserted prime valuation" in rfc
    assert "not the full all-integer iff classification" in rfc
    assert "not Alpha or Stable admission" in rfc
