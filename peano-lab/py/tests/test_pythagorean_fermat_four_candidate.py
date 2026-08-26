"""Exact first-order audit of constructive Pythagorean/Fermat-four foundations."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd, isqrt
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v13
from peano_lab.library import pythagorean_fermat_four_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "pythagorean_double_product",
    "pythagorean_euclidean_identity",
    "pythagorean_euclidean_constructor",
    "pythagorean_leg_swap",
    "pythagorean_euclidean_swapped_constructor",
    "pythagorean_euclidean_even_leg",
    "pythagorean_euclidean_even_leg_not_odd",
    "pythagorean_difference_witness_unique",
    "pythagorean_square_gap_from_order",
    "pythagorean_euclidean_from_order",
    "pythagorean_hypotenuse_nonzero",
    "pythagorean_coprime_swap",
    "pythagorean_primitive_leg_swap",
    "fermat_four_counterexample_is_pythagorean",
    "fermat_four_bounded_descent",
    "fermat_four_no_square_from_descent",
    "fermat_four_no_fourth_from_descent",
)

PINNED_ENDPOINTS = {
    "pythagorean_euclidean_identity": (
        "6a18ef67200f67f9ad0e4024538c8ca8aaa34775cc350234683bfb3292192efa"
    ),
    "pythagorean_euclidean_from_order": (
        "3ecb9f3cf3c72a2eb9cd6482d4b4fc69b15e4f1a6729eeac3b9555cab602c76d"
    ),
    "pythagorean_primitive_leg_swap": (
        "a4dd23c784f994d86cbb5fe79f755643919b39a9ad38d3abcb12804f2744c44a"
    ),
    "fermat_four_bounded_descent": (
        "7cf226bab6834b88816acc8fcd7aeeb48dd07f4c15372d56a311fbafc0b83180"
    ),
    "fermat_four_no_square_from_descent": (
        "a76b3502e5b6c1cc2b78505cc264fd479d22e4c751bb6c615b380deea1b4db46"
    ),
    "fermat_four_no_fourth_from_descent": (
        "a7cb2e3e1a5ebe93e07f839eae7b45bfd4ba5f59b324fbc51e9b1c5b4d5d19a5"
    ),
}

EXPECTED_PROOF_NODES = (20, 33, 13, 10, 17, 4, 22, 25, 22, 14, 22, 15, 26, 12, 63, 31, 40)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_pythagorean_fermat_four_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v13.ALPHA_SPECS}


def test_pythagorean_frontier_is_closed_deterministic_and_release_isolated() -> None:
    rows = _rows()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows == candidate.make_pythagorean_fermat_four_candidate_theorems(
        TheoremSpec
    )
    seen: set[str] = set()
    public = _specs_by_name()
    for item in rows:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert set(item.dependencies) <= set(_core()) | seen
        assert item.name not in public
        assert item.name not in editions_v13.ALPHA_EDITION.by_name
        assert all("DNE" not in command for command in item.script)
        seen.add(item.name)


def test_all_pythagorean_and_conditional_descent_bodies_replay_in_actual_kernel() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in receipts) == EXPECTED_PROOF_NODES
    assert max(receipt.proof_nodes for receipt in receipts) == 63
    assert all(receipt.proof_objects > 0 for receipt in receipts)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_pythagorean_or_descent_conclusions_are_rejected(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    corrupted = replace(item, statement=f"({item.statement}) /\\ false")
    available = _core() | {row.name: row for row in _rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=available)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_pythagorean_or_descent_scripts_are_rejected(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    corrupted = replace(item, script=item.script[:-1])
    available = _core() | {row.name: row for row in _rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=available)


def test_pythagorean_endpoint_statements_remain_pinned() -> None:
    by_name = {row.name: row for row in _rows()}
    assert {
        name: sha256(by_name[name].statement.encode("utf-8")).hexdigest()
        for name in PINNED_ENDPOINTS
    } == PINNED_ENDPOINTS


def test_primitive_relation_expands_without_a_trusted_gcd_predicate() -> None:
    relation = candidate.primitive_pythagorean("x", "y", "z", tag="audit")
    assert "x" in relation and "y" in relation and "z" in relation
    assert "pff_divisor_audit" in relation
    assert "pff_left_audit" in relation
    assert "pff_right_audit" in relation
    assert "gcd" not in relation.lower()
    _, free = parse_formula_with_names(f"forall x y z. ({relation})")
    assert not free


def test_fermat_descent_endpoint_retains_its_exact_unproved_premise() -> None:
    by_name = {row.name: row for row in _rows()}
    expected = _closed_formula(candidate.fermat_four_strict_descent(tag="bounded"))
    for name in (
        candidate.FERMAT_FOUR_NO_SQUARE_FROM_DESCENT,
        candidate.FERMAT_FOUR_NO_FOURTH_FROM_DESCENT,
    ):
        parsed = _closed_formula(by_name[name].statement)
        assert isinstance(parsed, Imp)
        assert parsed.antecedent == expected
        assert isinstance(parsed.consequent, Forall)
        assert "pff_smaller_hypotenuse_bounded" in by_name[name].statement
        assert "pff_gap_bounded + S pff_smaller_hypotenuse_bounded" in (
            by_name[name].statement
        )


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    (
        (2, 1, (3, 4, 5)),
        (3, 2, (5, 12, 13)),
        (4, 1, (15, 8, 17)),
        (4, 3, (7, 24, 25)),
        (5, 2, (21, 20, 29)),
        (5, 4, (9, 40, 41)),
        (6, 1, (35, 12, 37)),
    ),
)
def test_euclidean_examples_have_exact_primitive_constructive_witnesses(
    first: int, second: int, expected: tuple[int, int, int],
) -> None:
    difference = first * first - second * second
    doubled = 2 * first * second
    hypotenuse = first * first + second * second
    assert (difference, doubled, hypotenuse) == expected
    assert difference * difference + doubled * doubled == hypotenuse * hypotenuse
    assert gcd(first, second) == 1
    assert (first - second) % 2 == 1
    assert gcd(difference, doubled) == 1


@pytest.mark.parametrize("first", range(1, 13))
def test_bounded_fourth_power_examples_exhibit_no_false_counterexample(
    first: int,
) -> None:
    for second in range(1, 13):
        value = first**4 + second**4
        root = isqrt(value)
        assert root * root != value


def test_pythagorean_rfc_preserves_exact_missing_classification_boundary() -> None:
    repository = Path(__file__).resolve().parents[3]
    document = (
        repository / "research/arithmetic-library/pythagorean-fermat-four-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "17" in document
    assert "pythagorean_euclidean_from_order" in document
    assert "fermat_four_no_fourth_from_descent" in document
    assert "strict descent premise remains unproved" in document
    assert "No full primitive classification" in document
    assert "No unconditional Fermat exponent-four theorem" in document
