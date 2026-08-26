"""Bounded constructive audit of quaternion Euler cancellation candidates."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from itertools import product

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
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.four_square_euler_candidate import (
    FOUR_SQUARE_EULER_ALL_MIXED_CANCEL,
    FOUR_SQUARE_EULER_ADD_PERMUTE_NINE,
    FOUR_SQUARE_EULER_ADD_PERMUTE_SIX,
    FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN,
    FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE,
    FOUR_SQUARE_EULER_ADD_SWAP_LAST,
    FOUR_SQUARE_EULER_BALANCE_AGGREGATE,
    FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
    FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE,
    FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE,
    FOUR_SQUARE_EULER_CROSS_DECOMPOSITION,
    FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION,
    FOUR_SQUARE_EULER_CROSS_SWAP,
    FOUR_SQUARE_EULER_DIAGONAL_BLOCK,
    FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
    FOUR_SQUARE_EULER_DIAGONAL_REGROUP,
    FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
    FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
    FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL,
    FOUR_SQUARE_EULER_GLOBAL_COMPENSATION,
    FOUR_SQUARE_EULER_LEFT_DECOMPOSITION,
    FOUR_SQUARE_EULER_MIXED_AB,
    FOUR_SQUARE_EULER_MIXED_AC,
    FOUR_SQUARE_EULER_MIXED_AD,
    FOUR_SQUARE_EULER_MIXED_BC,
    FOUR_SQUARE_EULER_MIXED_BD,
    FOUR_SQUARE_EULER_MIXED_CD,
    FOUR_SQUARE_EULER_MIXED_DECOMPOSITION,
    FOUR_SQUARE_EULER_QUATERNION,
    FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL,
    FOUR_SQUARE_EULER_REPRESENTATIONS_CLOSED_UNDER_MULTIPLICATION,
    FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION,
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    FOUR_SQUARE_EULER_CROSS_SWAP,
    FOUR_SQUARE_EULER_MIXED_AB,
    FOUR_SQUARE_EULER_MIXED_AC,
    FOUR_SQUARE_EULER_MIXED_AD,
    FOUR_SQUARE_EULER_MIXED_BC,
    FOUR_SQUARE_EULER_MIXED_BD,
    FOUR_SQUARE_EULER_MIXED_CD,
    FOUR_SQUARE_EULER_ALL_MIXED_CANCEL,
    FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
    FOUR_SQUARE_EULER_BALANCE_AGGREGATE,
    FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
    FOUR_SQUARE_EULER_DIAGONAL_BLOCK,
    FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
    FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL,
    FOUR_SQUARE_EULER_ADD_PERMUTE_SIX,
    FOUR_SQUARE_EULER_ADD_PERMUTE_NINE,
    FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE,
    FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN,
    FOUR_SQUARE_EULER_ADD_SWAP_LAST,
    FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION,
    FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION,
    FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
    FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE,
    FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE,
    FOUR_SQUARE_EULER_DIAGONAL_REGROUP,
    FOUR_SQUARE_EULER_LEFT_DECOMPOSITION,
    FOUR_SQUARE_EULER_CROSS_DECOMPOSITION,
    FOUR_SQUARE_EULER_MIXED_DECOMPOSITION,
    FOUR_SQUARE_EULER_GLOBAL_COMPENSATION,
    FOUR_SQUARE_EULER_QUATERNION,
    FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL,
    FOUR_SQUARE_EULER_REPRESENTATIONS_CLOSED_UNDER_MULTIPLICATION,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_euler_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _base_core() -> dict[str, TheoremSpec]:
    core = {item.name: item for item in editions_v12.ALPHA_SPECS}
    core |= {
        item.name: item
        for item in make_fermat_two_squares_classification_candidate_theorems(
            TheoremSpec
        )
    }
    core |= {
        item.name: item
        for item in make_four_square_identity_candidate_theorems(TheoremSpec)
    }
    return core


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _base_core() | {item.name: item for item in _rows()[:index]}


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


def test_euler_candidates_are_isolated_first_order_and_topological() -> None:
    rows = _rows()
    assert rows == make_four_square_euler_candidate_theorems(TheoremSpec)
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    stable = _specs_by_name()
    alpha = {item.name for item in editions_v12.ALPHA_SPECS}
    observed: set[str] = set()
    for row in rows:
        assert row.name not in stable
        assert row.name not in alpha
        assert set(row.dependencies) <= set(_base_core()) | observed
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in ("Quaternion(", "FourSquare(", " - ", "^", "abs(")
        )
        assert all(not command.startswith(("ring", "omega", "auto")) for command in row.script)
        observed.add(row.name)


def test_euler_candidate_bodies_are_bounded_and_independently_replayed() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_base_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(item.proof_nodes for item in receipts) <= 1200
    assert max(item.proof_depth for item in receipts) <= 140


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_euler_body_is_constructive_and_rejects_false_conclusion(name: str) -> None:
    proof, target = _body(name)
    assert check((), proof, target)
    assert all(type(node) is not DNE for node in _walk(proof))
    row = next(item for item in _rows() if item.name == name)
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_row_core(name))


@pytest.mark.parametrize("coordinates", tuple(product(range(3), repeat=4)))
def test_crossed_products_cancel_for_every_small_coordinate_pair(
    coordinates: tuple[int, int, int, int],
) -> None:
    a, b, c, d = coordinates
    assert (a * b) * (c * d) == (a * d) * (c * b)


@pytest.mark.parametrize("left", ((0, 0, 0, 0), (1, 2, 3, 4), (7, 1, 9, 5)))
@pytest.mark.parametrize("right", ((0, 0, 0, 0), (1, 2, 3, 4), (2, 5, 7, 11)))
def test_hamilton_cross_compensation_matches_full_euler_identity(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> None:
    a, b, c, d = left
    e, f, g, h = right
    positive = (a * e, a * f + b * e + c * h, a * g + c * e + d * f, a * h + b * g + d * e)
    negative = (b * f + c * g + d * h, d * g, b * h, c * f)
    magnitudes = tuple(abs(p - n) for p, n in zip(positive, negative, strict=True))
    norm = sum(value * value for value in left) * sum(value * value for value in right)
    cross = sum(p * n + n * p for p, n in zip(positive, negative, strict=True))
    balanced = sum(p * p + n * n for p, n in zip(positive, negative, strict=True))

    assert norm + cross == balanced
    assert norm == sum(value * value for value in magnitudes)
