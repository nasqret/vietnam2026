"""Exact-kernel audit of constructive primitive Pythagorean parametrization."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.library import editions_v15
from peano_lab.library import pythagorean_primitive_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.pythagorean_fermat_four_candidate import (
    make_pythagorean_fermat_four_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "pythagorean_parameter_even_square",
    "pythagorean_parameter_odd_square",
    "pythagorean_even_odd_square_gap_odd",
    "pythagorean_odd_even_square_gap_odd",
    "pythagorean_opposite_parity_square_gap_odd",
    "pythagorean_opposite_parity_hypotenuse_odd",
    "pythagorean_odd_coordinate_coprime_two",
    "pythagorean_parameter_divisor_divides_square",
    "pythagorean_square_gap_coprime_first_parameter",
    "pythagorean_square_gap_coprime_second_parameter",
    "pythagorean_square_gap_coprime_parameter_product",
    "pythagorean_primitive_euclidean_legs",
    "pythagorean_primitive_euclidean_constructor",
    "pythagorean_primitive_euclidean_from_order",
    "pythagorean_primitive_euclidean_swapped_constructor",
    "pythagorean_primitive_hypotenuse_coprime_first_leg",
    "pythagorean_primitive_hypotenuse_coprime_second_leg",
    "pythagorean_primitive_pairwise_coprime",
    "pythagorean_primitive_legs_not_both_even",
    "pythagorean_odd_square_pair_two_mod_four",
    "pythagorean_two_mod_four_not_square",
    "pythagorean_triple_legs_not_both_odd",
    "pythagorean_coordinate_parity_choice",
    "pythagorean_primitive_legs_opposite_parity",
    "pythagorean_odd_square_has_odd_root",
    "pythagorean_primitive_hypotenuse_odd",
    "pythagorean_primitive_normal_form",
)

EXPECTED_PROOF_NODES = (
    14,
    16,
    46,
    46,
    45,
    63,
    29,
    19,
    49,
    47,
    57,
    35,
    43,
    24,
    41,
    51,
    35,
    22,
    34,
    90,
    159,
    24,
    16,
    47,
    29,
    27,
    54,
)

PINNED_ENDPOINTS = {
    "pythagorean_opposite_parity_square_gap_odd": (
        "3f58197d5cfb212aff32cc367b850ae4d22a771c440b39f054f3608005b06791"
    ),
    "pythagorean_primitive_euclidean_legs": (
        "71a97881469eda3e051098a29e9500853a914422f11eaf4d5859b1bca0971693"
    ),
    "pythagorean_primitive_euclidean_constructor": (
        "d4304edcb6d60187a8b782afd978a8c16e33d7dbec31058c129f60cccc3e0a4f"
    ),
    "pythagorean_primitive_euclidean_from_order": (
        "7b71efd8961214c09eacc96a84603d56f5658d850a3f31256df3e00255a48e90"
    ),
    "pythagorean_primitive_euclidean_swapped_constructor": (
        "ff13caf4f8e1c20e73a2f2aa7ec6d6b2c24ef3aaccb9d95a50288a1bdd103900"
    ),
    "pythagorean_primitive_pairwise_coprime": (
        "21c752b66064560f0f856c8c535e575fb153e886b90cca727fe9a2bfff15e086"
    ),
    "pythagorean_triple_legs_not_both_odd": (
        "5ca8c96a9784f740a19c4765afd05829cc5e17dbc6da81e4c5edf3364e015ca8"
    ),
    "pythagorean_primitive_legs_opposite_parity": (
        "d6c2c8b838e32f362b87c59d2b41822ef4464a58a88eb13ffdf7a153d63b83e4"
    ),
    "pythagorean_primitive_hypotenuse_odd": (
        "7c3f0d5c228cb548a2e2af26fc753f853c80911b6adefdc1803a1b077a747ac9"
    ),
    "pythagorean_primitive_normal_form": (
        "0e58024c289803991f5b0536889cea380c59940c3b351eebe2e57298db872bac"
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_pythagorean_primitive_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {
        **{item.name: item for item in editions_v15.ALPHA_SPECS},
        **{
            item.name: item
            for item in make_pythagorean_fermat_four_candidate_theorems(TheoremSpec)
        },
    }


def test_primitive_frontier_is_closed_deterministic_and_release_isolated() -> None:
    rows = _rows()
    assert len(rows) == 27
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows == candidate.make_pythagorean_primitive_candidate_theorems(
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
        assert item.name not in editions_v15.ALPHA_EDITION.by_name
        assert all("DNE" not in command for command in item.script)
        seen.add(item.name)


def test_all_primitive_euclidean_bodies_replay_in_actual_independent_kernel() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in receipts) == EXPECTED_PROOF_NODES
    assert max(receipt.proof_nodes for receipt in receipts) == 159
    assert all(receipt.proof_objects > 0 for receipt in receipts)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_primitive_conclusions_are_rejected_by_the_kernel(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    corrupted = replace(item, statement=f"({item.statement}) /\\ false")
    available = _core() | {row.name: row for row in _rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=available)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_primitive_scripts_are_rejected_by_the_kernel(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    corrupted = replace(item, script=item.script[:-1])
    available = _core() | {row.name: row for row in _rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=available)


@pytest.mark.parametrize(
    "name",
    (
        "pythagorean_primitive_euclidean_legs",
        "pythagorean_primitive_euclidean_constructor",
        "pythagorean_primitive_euclidean_from_order",
        "pythagorean_primitive_pairwise_coprime",
        "pythagorean_primitive_legs_opposite_parity",
        "pythagorean_primitive_hypotenuse_odd",
        "pythagorean_primitive_normal_form",
    ),
)
def test_removing_declared_primitive_dependencies_fails_closed(name: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    corrupted = replace(item, dependencies=item.dependencies[:-1])
    available = _core() | {row.name: row for row in _rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=available)


def test_primitive_endpoint_statements_remain_exactly_pinned() -> None:
    by_name = {row.name: row for row in _rows()}
    assert {
        name: sha256(by_name[name].statement.encode("utf-8")).hexdigest()
        for name in PINNED_ENDPOINTS
    } == PINNED_ENDPOINTS


def test_opposite_parity_is_an_exact_first_order_witnessed_disjunction() -> None:
    relation = candidate.opposite_parity("m", "n", tag="audit")
    assert "pp_even_audit_first_even" in relation
    assert "pp_odd_audit_second_odd" in relation
    assert "pp_odd_audit_first_odd" in relation
    assert "pp_even_audit_second_even" in relation
    assert "parity" not in relation.lower()
    assert "gcd" not in relation.lower()
    parsed, free = parse_formula_with_names(f"forall m n. ({relation})")
    assert not free
    assert isinstance(parsed, Forall)
    assert isinstance(parsed.body, Forall)
    assert isinstance(parsed.body.body, Or)
    assert isinstance(parsed.body.body.left, And)
    assert isinstance(parsed.body.body.right, And)


def test_forward_constructor_has_only_order_coprimality_and_parity_premises() -> None:
    item = next(
        row
        for row in _rows()
        if row.name == candidate.PYTHAGOREAN_PRIMITIVE_EUCLIDEAN_FROM_ORDER
    )
    formula = _closed_formula(item.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Forall)
    order = formula.body.body
    assert isinstance(order, Imp)
    assert isinstance(order.antecedent, Exists)
    coprimality = order.consequent
    assert isinstance(coprimality, Imp)
    assert isinstance(coprimality.antecedent, Forall)
    parity = coprimality.consequent
    assert isinstance(parity, Imp)
    assert isinstance(parity.antecedent, Or)
    assert isinstance(parity.consequent, Exists)
    assert isinstance(parity.consequent.body, And)
    assert "descent" not in item.statement
    assert "inverse" not in item.statement


def test_unconditional_normal_form_preserves_exact_primitive_premise() -> None:
    item = next(
        row for row in _rows() if row.name == candidate.PYTHAGOREAN_PRIMITIVE_NORMAL_FORM
    )
    formula = _closed_formula(item.statement)
    for _ in range(3):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.antecedent, And)
    assert isinstance(formula.consequent, And)
    assert isinstance(formula.consequent.left, Or)
    assert isinstance(formula.consequent.right, And)
    assert isinstance(formula.consequent.right.left, Exists)
    assert "pff_divisor" in item.statement
    assert "pp_odd_normal_hypotenuse" in item.statement


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    (
        (1, 0, (1, 0, 1)),
        (2, 1, (3, 4, 5)),
        (3, 2, (5, 12, 13)),
        (4, 1, (15, 8, 17)),
        (4, 3, (7, 24, 25)),
        (5, 2, (21, 20, 29)),
        (5, 4, (9, 40, 41)),
        (6, 1, (35, 12, 37)),
        (8, 5, (39, 80, 89)),
    ),
)
def test_primitive_euclidean_examples_satisfy_all_constructive_conclusions(
    first: int, second: int, expected: tuple[int, int, int],
) -> None:
    difference = first * first - second * second
    doubled = 2 * first * second
    hypotenuse = first * first + second * second

    assert (difference, doubled, hypotenuse) == expected
    assert difference * difference + doubled * doubled == hypotenuse * hypotenuse
    assert gcd(first, second) == 1
    assert (first - second) % 2 == 1
    assert difference % 2 == 1
    assert doubled % 2 == 0
    assert hypotenuse % 2 == 1
    assert gcd(difference, doubled) == 1
    assert gcd(difference, hypotenuse) == 1
    assert gcd(doubled, hypotenuse) == 1


@pytest.mark.parametrize(
    ("first", "second"),
    ((3, 1), (4, 2), (5, 1), (6, 3), (8, 4), (9, 3)),
)
def test_missing_parameter_hypotheses_do_not_create_fake_primitive_claims(
    first: int, second: int,
) -> None:
    difference = first * first - second * second
    doubled = 2 * first * second
    assert gcd(first, second) != 1 or (first - second) % 2 == 0
    assert gcd(difference, doubled) != 1


def test_all_bounded_primitive_triples_satisfy_proved_normal_form() -> None:
    for first in range(41):
        for second in range(41):
            for hypotenuse in range(41):
                if first * first + second * second != hypotenuse * hypotenuse:
                    continue
                if gcd(first, second) != 1:
                    continue
                assert (first - second) % 2 == 1
                assert hypotenuse % 2 == 1
                assert gcd(first, hypotenuse) == 1
                assert gcd(second, hypotenuse) == 1


def test_primitive_rfc_reports_exact_proof_and_remaining_inverse_boundary() -> None:
    repository = Path(__file__).resolve().parents[3]
    document = (
        repository / "research/arithmetic-library/pythagorean-primitive-rfc-v1.md"
    ).read_text(encoding="utf-8")

    assert "27" in document
    assert "159" in document
    assert "pythagorean_primitive_euclidean_from_order" in document
    assert "pythagorean_primitive_legs_opposite_parity" in document
    assert "pythagorean_primitive_hypotenuse_odd" in document
    assert "pythagorean_primitive_normal_form" in document
    assert "inverse parametrization remains unproved" in document
    assert "Fermat strict-descent premise remains unproved" in document
    assert "No Alpha/Stable enrollment" in document
