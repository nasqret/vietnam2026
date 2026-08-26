"""Bounded independent audit of constructive quaternion multiplier descent."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library import four_square_descent_candidate as descent
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_factor_fold_candidate import (
    make_fermat_two_squares_factor_fold_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_pairing_candidate import (
    make_fermat_two_squares_pairing_candidate_theorems,
)
from peano_lab.library.four_square_euler_candidate import (
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_candidate import (
    make_four_square_lagrange_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    descent.FOUR_SQUARE_DESCENT_NONZERO_SQUARE,
    descent.FOUR_SQUARE_DESCENT_PRODUCT_REASSOCIATE,
    descent.FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM,
    descent.FOUR_SQUARE_DESCENT_SQUARE_FACTOR_CANCEL,
    descent.FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT,
    descent.FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT,
    descent.FOUR_SQUARE_DESCENT_STRICT_STEP_FROM_CENTERED_QUATERNION,
    descent.FOUR_SQUARE_DESCENT_MODULAR_SEED_MULTIPLIER_NONZERO,
    descent.FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED,
    descent.FOUR_SQUARE_DESCENT_PRIME_FROM_STRICT_STEP,
    descent.FOUR_SQUARE_DESCENT_PRIME_FROM_MODULAR_SEED_AND_STEP,
    descent.FOUR_SQUARE_DESCENT_THREE_MOD_FOUR_PRIMES_FROM_SEED_AND_STEP,
    descent.FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT,
    descent.FOUR_SQUARE_DESCENT_REMAINDER_COMPLEMENT_EXISTS,
    descent.FOUR_SQUARE_DESCENT_CENTERED_SIGNED_REMAINDER_EXISTS,
    descent.FOUR_SQUARE_DESCENT_CENTERED_FOUR_REMAINDERS_EXIST,
    descent.FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER,
    descent.FOUR_SQUARE_DESCENT_MATCHING_PARITY_SUM_EVEN,
    descent.FOUR_SQUARE_DESCENT_MATCHING_PARITY_ABSOLUTE_EVEN,
    descent.FOUR_SQUARE_DESCENT_DOUBLE_PAIR_IDENTITY,
    descent.FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_PAIRED_HALVING,
    descent.FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING,
    descent.FOUR_SQUARE_DESCENT_ODD_CENTERED_MAGNITUDE_HALF_BOUND,
    descent.FOUR_SQUARE_DESCENT_ADD_LE_ADD,
    descent.FOUR_SQUARE_DESCENT_DOUBLE_SQUARE_FOUR_SUM,
    descent.FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT,
    descent.FOUR_SQUARE_DESCENT_ODD_CENTERED_NORM_STRICT,
    descent.FOUR_SQUARE_DESCENT_ZERO_NORM_COORDINATES,
    descent.FOUR_SQUARE_DESCENT_ZERO_CENTERED_REMAINDER_DIVIDES,
    descent.FOUR_SQUARE_DESCENT_NONUNIT_PROPER_FACTOR_NOT_PRIME,
    descent.FOUR_SQUARE_DESCENT_DIVISIBLE_COORDINATES_PRIME_FACTOR,
    descent.FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO,
    descent.FOUR_SQUARE_DESCENT_ODD_CENTERED_STRICT_STEP,
)

PINNED_ENDPOINTS = {
    descent.FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT:
        "81d988b1cd0dbd5c7532707f9ef48b75fb8192190037ae04406c758e55fbe379",
    descent.FOUR_SQUARE_DESCENT_STRICT_STEP_FROM_CENTERED_QUATERNION:
        "360a0d489f5acec54775453e7d9e94d1af030ae3648be5ae1a74609f6e95811c",
    descent.FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED:
        "6929fe9263c7da1673c64be0f5043992de4774210433736a77a4db85b826b54c",
    descent.FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT:
        "9ce8baabf8926783a666e0e3a7bc81d45eaa5eadec5fb4d3b6ed0a7308443673",
    descent.FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO:
        "76e8b2a148cb36d2e456ec59810f93fe0f73d9c34d69ad7de3b8982de30cae9f",
    descent.FOUR_SQUARE_DESCENT_ODD_CENTERED_STRICT_STEP:
        "75e1a1097d08b24c1168513ed20472ff9d9141bb1ef856aee652b3d00114ce4b",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return descent.make_four_square_descent_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _base_core() -> dict[str, TheoremSpec]:
    result = {row.name: row for row in editions_v12.ALPHA_SPECS}
    factories = (
        make_fermat_two_squares_classification_candidate_theorems,
        make_fermat_two_squares_factor_fold_candidate_theorems,
        make_fermat_two_squares_pairing_candidate_theorems,
        make_four_square_identity_candidate_theorems,
        make_four_square_euler_candidate_theorems,
        make_four_square_lagrange_candidate_theorems,
    )
    for factory in factories:
        result.update({row.name: row for row in factory(TheoremSpec)})
    return result


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _base_core() | {row.name: row for row in _rows()[:index]}


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str) -> tuple[Proof, object]:
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


def test_descent_candidates_are_deterministic_closed_and_registry_isolated() -> None:
    rows = _rows()
    assert rows == descent.make_four_square_descent_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES

    alpha = {row.name for row in editions_v12.ALPHA_SPECS}
    stable = _specs_by_name()
    seen: set[str] = set()
    for row in rows:
        assert row.name not in alpha
        assert row.name not in stable
        assert set(row.dependencies) <= set(_base_core()) | seen
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in ("Prime(", "FourSquare(", "Centered(", " - ", "^")
        )
        assert all(
            not command.startswith(("ring", "omega", "auto"))
            for command in row.script
        )
        seen.add(row.name)

    assert {
        row.name: sha256(row.statement.encode("utf-8")).hexdigest()
        for row in rows
        if row.name in PINNED_ENDPOINTS
    } == PINNED_ENDPOINTS


def test_descent_bodies_are_independently_kernel_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_base_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) <= 380
    assert max(receipt.proof_depth for receipt in receipts) <= 55


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_descent_bodies_are_constructive_and_reject_false_targets(name: str) -> None:
    proof, target = _body(name)
    assert check((), proof, target)
    assert all(type(node) is not DNE for node in _walk(proof))
    row = next(item for item in _rows() if item.name == name)
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_row_core(name))


def test_universal_endpoint_retains_both_real_missing_hypotheses() -> None:
    row = next(
        item
        for item in _rows()
        if item.name
        == descent.FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT
    )
    formula = _closed_formula(row.statement)
    assert type(formula) is Imp
    assert type(formula.left) is Forall
    assert type(formula.right) is Imp
    assert type(formula.right.left) is Forall
    assert type(formula.right.right) is Forall
    assert "4 * fsd_seed_residue_universal + 3" in row.statement
    assert "fsd_gap_universal + S fsd_smaller_universal" in row.statement


@pytest.mark.parametrize(
    ("prime_value", "coordinates"),
    (
        (3, (2, 1, 1, 0)),
        (7, (3, 2, 1, 0)),
        (11, (4, 2, 1, 1)),
        (19, (5, 3, 2, 0)),
    ),
)
def test_even_multiplier_quaternion_quotient_has_actual_integral_coordinates(
    prime_value: int, coordinates: tuple[int, int, int, int]
) -> None:
    a, b, c, d = coordinates
    assert a * a + b * b + c * c + d * d == 2 * prime_value

    e, f, g, h = a % 2, (-b) % 2, (-c) % 2, (-d) % 2
    second_norm = e * e + f * f + g * g + h * h
    assert second_norm == 2
    positive = (
        a * e,
        a * f + b * e + c * h,
        a * g + c * e + d * f,
        a * h + b * g + d * e,
    )
    negative = (b * f + c * g + d * h, d * g, b * h, c * f)
    magnitudes = tuple(abs(left - right) for left, right in zip(positive, negative))
    assert all(value % 2 == 0 for value in magnitudes)
    quotient = tuple(value // 2 for value in magnitudes)
    assert sum(value * value for value in quotient) == prime_value


@pytest.mark.parametrize("modulus", tuple(range(1, 16)))
def test_centered_signed_remainder_is_constructively_bounded(modulus: int) -> None:
    for value in range(4 * modulus + 1):
        remainder = value % modulus
        complement = modulus - remainder
        magnitude = min(remainder, complement)
        assert magnitude + magnitude <= modulus
        assert (
            (value - magnitude) % modulus == 0
            or (value + magnitude) % modulus == 0
        )


@pytest.mark.parametrize(
    ("prime_value", "multiplier", "coordinates", "expected_quotient"),
    (
        (5, 3, (1, 1, 2, 3), 1),
        (7, 5, (0, 1, 3, 5), 1),
        (11, 5, (1, 1, 2, 7), 2),
        (11, 7, (0, 4, 5, 6), 2),
        (13, 9, (3, 6, 6, 6), 4),
        (13, 11, (3, 6, 7, 7), 6),
    ),
)
def test_proper_odd_prime_multiplier_centered_quotient_is_strictly_positive(
    prime_value: int,
    multiplier: int,
    coordinates: tuple[int, int, int, int],
    expected_quotient: int,
) -> None:
    assert 1 < multiplier < prime_value
    assert multiplier % 2 == 1
    assert sum(value * value for value in coordinates) == prime_value * multiplier
    centered = tuple(
        min(value % multiplier, multiplier - (value % multiplier))
        for value in coordinates
    )
    centered_norm = sum(value * value for value in centered)
    assert centered_norm == multiplier * expected_quotient
    assert 0 < expected_quotient < multiplier


def test_descent_rfc_preserves_the_exact_two_open_obligations() -> None:
    repository = Path(__file__).resolve().parents[3]
    text = (
        repository / "research/arithmetic-library/four-square-descent-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "four_square_descent_quaternion_quotient" in text
    assert "four_square_descent_bounded_centered_quotient_nonzero" in text
    assert "four_square_descent_odd_centered_strict_step" in text
    assert "four_square_lagrange_from_modular_seeds_and_strict_descent" in text
    assert "does not prove universal Lagrange unconditionally" in text
    assert "No Alpha or Stable admission" in text
