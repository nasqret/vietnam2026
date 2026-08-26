"""Bounded kernel audit of canonical prime-factor pairing predecessors."""

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
from peano_lab.library.fermat_two_squares_pairing_candidate import (
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
    ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED,
    ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT,
    BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
    DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
    DISTINCT_PRIME_POWER_VALUATION_ZERO,
    EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL,
    EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
    EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR,
    NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
    POSITIVE_DOUBLE_AT_LEAST_TWO,
    PAIRING_DOUBLE_EQUALS_TWO_MUL,
    PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY,
    PRIME_MOD_FOUR_GOOD_OR_THREE,
    PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
    POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
    SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
    THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED,
    TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
    make_fermat_two_squares_pairing_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_valuation_candidate import (
    make_fermat_two_squares_valuation_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_candidate import (
    make_fermat_two_squares_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_factor_fold_candidate import (
    make_fermat_two_squares_factor_fold_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY,
    DISTINCT_PRIME_POWER_VALUATION_ZERO,
    POSITIVE_DOUBLE_AT_LEAST_TWO,
    EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
    PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
    BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
    EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR,
    PAIRING_DOUBLE_EQUALS_TWO_MUL,
    EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL,
    DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
    SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
    THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED,
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
    ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT,
    PRIME_MOD_FOUR_GOOD_OR_THREE,
    ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED,
    POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
    NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
    TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
)

EXPECTED_DEPENDENCIES = {
    PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY: ("prime_divisor_eq_one_or_self",),
    DISTINCT_PRIME_POWER_VALUATION_ZERO: (
        "eq_decidable",
        "power_valuation_nonzero_exponent_divides_base",
        PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY,
    ),
    POSITIVE_DOUBLE_AT_LEAST_TWO: (
        "nonzero_is_succ",
        "add_succ_left",
        "add_assoc",
        "add_comm",
    ),
    EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR: (
        "prime_divisor_power_valuation_nonzero",
        POSITIVE_DOUBLE_AT_LEAST_TWO,
        "power_valuation_power_divides",
        "power_divides_exponent_antitone",
        "pow_two",
    ),
    PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR: (
        "prime_nonzero",
        "mul_left_cancel_nonzero",
        "mul_comm",
        "mul_assoc",
    ),
    BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST: (
        "beta_prime_divisor_product_member",
        "beta_sorted_factor_le_last",
        "le_antisymm",
    ),
    EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR: (
        "beta_product_succ_decompose",
        "beta_at_unique",
        "mul_comm",
        EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
        PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
        "all_prime_succ_elim_prefix",
        "sorted_succ_elim_prefix",
        "sorted_succ_elim_last",
        BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
    ),
    PAIRING_DOUBLE_EQUALS_TWO_MUL: ("mul_succ_left", "one_mul"),
    EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL: (
        PAIRING_DOUBLE_EQUALS_TWO_MUL,
        "even_sum_parity_cases",
        "even_not_odd",
    ),
    DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX: (
        DISTINCT_PRIME_POWER_VALUATION_ZERO,
        "prime_nonzero",
        "prime_power_valuation_mul",
    ),
    SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR: (
        "prime_power_valuation_square_factor_shift",
        EVEN_DOUBLE_SUM_REFLECTS_EVEN_TAIL,
    ),
    THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED: (
        "sum_two_squares_not_four_mod_three",
    ),
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME: (
        THREE_MOD_FOUR_NUMBER_NOT_EQUAL_REPRESENTED,
        "power_valuation_exists",
        DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
    ),
    ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR: (
        "power_valuation_exists",
        "power_valuation_value_eq_transport",
        "mul_comm",
        SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
    ),
    ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT: (
        "power_valuation_value_eq_transport",
    ),
    PRIME_MOD_FOUR_GOOD_OR_THREE: ("prime_mod_four_trichotomy",),
    ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED: (
        "le_zero",
        "eq_decidable",
        "prime_divisor_exists",
        PRIME_MOD_FOUR_GOOD_OR_THREE,
        "prime_two_or_one_mod_four_is_sum_of_two_squares",
        ALL_BAD_PRIME_EVEN_VALUATION_VALUE_EQ_TRANSPORT,
        ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
        "mul_comm",
        "proper_factor_lt",
        "le_trans",
        "le_of_succ_le_succ",
        "two_square_representation_multiplicatively_closed",
        "power_valuation_exists",
        EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
        "prime_nonzero",
        ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
        "prime_square_times_nonzero_strictly_increases",
        "two_square_representation_preserved_by_square_factor",
    ),
    POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE: (
        "le_refl",
        ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED,
    ),
    NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS: (
        "three_mod_four_prime_represented_nonzero_valuation_even",
        POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
    ),
    TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS: (
        "eq_decidable",
        NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_pairing_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


@lru_cache(maxsize=1)
def _external_candidate_core() -> dict[str, TheoremSpec]:
    valuation_names = {
        "prime_power_valuation_square_factor_shift",
        "prime_square_times_nonzero_strictly_increases",
        "two_square_representation_preserved_by_square_factor",
        "three_mod_four_prime_represented_nonzero_valuation_even",
    }
    result = {
        item.name: item
        for item in make_fermat_two_squares_valuation_candidate_theorems(TheoremSpec)
        if item.name in valuation_names
    }
    result.update(
        (item.name, item)
        for item in make_fermat_two_squares_candidate_theorems(TheoremSpec)
        if item.name == "sum_two_squares_not_four_mod_three"
    )
    result.update(
        (item.name, item)
        for item in make_fermat_two_squares_classification_candidate_theorems(
            TheoremSpec
        )
        if item.name
        in ("prime_mod_four_trichotomy", "two_square_representation_multiplicatively_closed")
    )
    result.update(
        (item.name, item)
        for item in make_fermat_two_squares_factor_fold_candidate_theorems(TheoremSpec)
        if item.name == "prime_two_or_one_mod_four_is_sum_of_two_squares"
    )
    return result


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
    result = 0
    while value % base == 0:
        result += 1
        value //= base
    return result


def test_pairing_candidates_are_isolated_and_dependency_ordered() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {row.name: row.dependencies for row in rows} == EXPECTED_DEPENDENCIES

    alpha = _alpha_core()
    stable = _specs_by_name()
    external = _external_candidate_core()
    assert set(external) == {
        "prime_power_valuation_square_factor_shift",
        "prime_square_times_nonzero_strictly_increases",
        "two_square_representation_preserved_by_square_factor",
        "three_mod_four_prime_represented_nonzero_valuation_even",
        "sum_two_squares_not_four_mod_three",
        "prime_mod_four_trichotomy",
        "two_square_representation_multiplicatively_closed",
        "prime_two_or_one_mod_four_is_sum_of_two_squares",
    }
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
    assert "fermat_two_squares_pairing_candidate" not in registry_source


def test_pairing_contracts_are_closed_native_first_order_formulas() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in (
                "Prime(",
                "PowerVal(",
                "PowDiv(",
                "BetaAt(",
                "Product(",
                "Sorted(",
                "^",
                " - ",
            )
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_pairing_bodies_are_kernel_checked_and_constructive(name: str) -> None:
    proof, target = _body(name)
    nodes, depth = proof_metrics(proof)
    objects, edges, reused = proof_identity_metrics(proof)
    assert check((), proof, target)
    assert nodes <= 400
    assert depth <= 90
    assert objects <= nodes
    assert edges >= objects - 1
    assert reused >= 0
    assert not any(type(node) is DNE for node in _walk(proof))


@pytest.mark.parametrize(
    ("name", "dependency"),
    (
        (DISTINCT_PRIME_POWER_VALUATION_ZERO, PRIME_DIVISOR_OF_PRIME_FORCES_EQUALITY),
        (EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR, "pow_two"),
        (
            PRIME_SQUARE_DIVISIBILITY_FORCES_SUFFIX_PRIME_DIVISOR,
            "mul_left_cancel_nonzero",
        ),
        (
            BETA_SORTED_PRIME_PREFIX_DIVISOR_EQUALS_BOUNDED_LAST,
            "beta_prime_divisor_product_member",
        ),
        (
            EVEN_VALUATION_SORTED_TERMINAL_PRIME_HAS_EQUAL_PREDECESSOR,
            EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
        ),
        (
            DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
            DISTINCT_PRIME_POWER_VALUATION_ZERO,
        ),
        (
            SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
            "prime_power_valuation_square_factor_shift",
        ),
        (
            ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_REPRESENTED_PRIME,
            DISTINCT_PRIME_FACTOR_EVEN_VALUATION_REFLECTS_PREFIX,
        ),
        (
            ALL_BAD_PRIME_EVEN_VALUATIONS_STRIP_SQUARE_FACTOR,
            SQUARE_FACTOR_EVEN_VALUATION_REFLECTS_COFACTOR,
        ),
        (
            ALL_BAD_PRIME_EVEN_TWO_SQUARE_SUFFICIENCY_BOUNDED,
            EVEN_POSITIVE_PRIME_VALUATION_HAS_SQUARE_DIVISOR,
        ),
        (
            NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
            POSITIVE_NUMBER_WITH_EVEN_BAD_PRIME_VALUATIONS_IS_TWO_SQUARE,
        ),
        (
            TWO_SQUARE_IFF_ZERO_OR_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
            NONZERO_TWO_SQUARE_IFF_EVEN_THREE_MOD_FOUR_PRIME_VALUATIONS,
        ),
    ),
)
def test_pairing_essential_dependencies_are_live(name: str, dependency: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    mutation = replace(
        row,
        dependencies=tuple(value for value in row.dependencies if value != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutation,), core=_row_core(name))


def test_prime_valuation_pairing_predecessors_match_small_number_oracles() -> None:
    for p, q in product((2, 3, 5, 7, 11, 13), repeat=2):
        if p != q:
            assert _valuation(p, q) == 0

    observed = 0
    for p in (2, 3, 5, 7):
        for n in range(1, 300):
            exponent = _valuation(p, n)
            if n % p == 0 and exponent % 2 == 0:
                assert n % (p * p) == 0
                prefix = n // p
                assert prefix % p == 0
                observed += 1
    assert observed > 0


def test_pairing_rfc_honestly_documents_the_complete_candidate_classification() -> None:
    repository = Path(__file__).resolve().parents[3]
    document = (
        repository
        / "research"
        / "arithmetic-library"
        / "fermat-two-squares-pairing-rfc-v1.md"
    ).read_text(encoding="utf-8")
    for name in EXPECTED_NAMES:
        assert f"`{name}`" in document
    assert "not Alpha or Stable admission" in document
    assert "complete two-square iff criterion" in document
    assert "zero has no asserted prime valuation" in document
