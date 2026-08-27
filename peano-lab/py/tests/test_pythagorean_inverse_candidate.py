"""Kernel, hygiene, and exact-statement tests for the positive inverse."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd, isqrt

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.library import editions_v25
from peano_lab.library import pythagorean_inverse_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.coprime_square_factor_candidate import make_coprime_square_factor_candidate_theorems
from peano_lab.library.pythagorean_fermat_four_candidate import primitive_pythagorean
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "pythagorean_positive_add_strict",
    "pythagorean_leg_strictly_below_hypotenuse",
    "pythagorean_odd_ordered_difference_even",
    "pythagorean_half_sum_reassociation",
    "pythagorean_half_hypotenuse_reassociation",
    "pythagorean_half_product_is_square",
    "pythagorean_half_factors_coprime",
    "pythagorean_coprime_square_roots",
    "pythagorean_even_square_has_even_root",
    "pythagorean_odd_square_sum_opposite_roots",
    "pythagorean_half_roots_coordinates",
    "pythagorean_half_roots_even_leg",
    "pythagorean_positive_gap_orders_parameters",
    "pythagorean_positive_even_leg_parameters_nonzero",
    "pythagorean_odd_even_half_factors",
    "pythagorean_half_factors_extract_parameters",
    "pythagorean_primitive_odd_even_inverse",
    "pythagorean_positive_primitive_leg_swap",
    "pythagorean_positive_primitive_inverse",
    "pythagorean_ordered_gap_positive",
    "pythagorean_euclidean_parameters_positive_constructor",
    "pythagorean_positive_primitive_from_parameters",
    "pythagorean_positive_primitive_classification",
)
EXPECTED_PROOF_NODES = (31, 28, 53, 37, 15, 76, 53, 24, 25, 36, 30, 27, 19, 41, 77, 162, 60, 50, 140, 44, 187, 88, 32)
PINNED_ENDPOINTS = {
    "pythagorean_primitive_odd_even_inverse": "b926982a720ad0f6cba2184dbb851f072f4f5c69a152b7c0c5e40f448313646f",
    "pythagorean_positive_primitive_inverse": "52637d9c57c28d1875f272b93a815aa22ba1d05c066be0642d44721f1903ae85",
    "pythagorean_euclidean_parameters_positive_constructor": "687282a139b369f70e6ba31449ee22dde33e4028526c660bbb82ea3a2ca03aff",
    "pythagorean_positive_primitive_from_parameters": "61b4600ed933cf9ae7148ac1583be792fe36038479ae3f5b54d831fc29b93295",
    "pythagorean_positive_primitive_classification": "df3bd4829643a3900cee8f78fc7b4b242a0fb935f8e29e1b4d2b7e18bdac387f",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_pythagorean_inverse_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in (*editions_v25.ALPHA_SPECS, *make_coprime_square_factor_candidate_theorems(TheoremSpec))}


@lru_cache(maxsize=1)
def _all() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


def test_inverse_rows_are_closed_deterministic_dependency_ordered_and_additive() -> None:
    assert _rows() == candidate.make_pythagorean_inverse_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sum(len(row.dependencies) for row in _rows()) == 77
    assert sum(len(row.script) for row in _rows()) == 733
    available = set(_core())
    for row in _rows():
        parsed, free = parse_formula_with_names(row.statement)
        assert not free
        assert parsed == _closed_formula(row.statement)
        assert set(row.dependencies) <= available
        assert row.name not in editions_v25.ALPHA_EDITION.by_name
        assert not any("DNE" in command or "axiom" in command for command in row.script)
        available.add(row.name)


def test_every_inverse_body_is_accepted_by_the_original_kernel() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in receipts) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in receipts) == 1335
    assert all(receipt.proof_objects > 0 for receipt in receipts)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_strengthening_is_rejected(name: str) -> None:
    row = _all()[name]
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_certificate_is_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_missing_declared_dependency_is_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_all())


def test_endpoint_hashes_pin_both_orientations_and_every_positive_premise() -> None:
    assert {name: sha256(_all()[name].statement.encode()).hexdigest() for name in PINNED_ENDPOINTS} == PINNED_ENDPOINTS


def test_positive_definition_is_exact_not_the_zero_permitting_legacy_predicate() -> None:
    actual = candidate.positive_primitive_pythagorean("a", "b", "c", tag="audit")
    expected = (
        "~(a = 0) /\\ (~(b = 0) /\\ (~(c = 0) /\\ "
        f"({primitive_pythagorean('a', 'b', 'c', tag='independent')})))"
    )
    assert _closed_formula(f"forall a b c. {actual}") == _closed_formula(f"forall a b c. {expected}")
    assert _closed_formula(f"forall a b c. {actual}") != _closed_formula(
        f"forall a b c. {primitive_pythagorean('a', 'b', 'c', tag='legacy')}"
    )


def test_readable_relations_are_hygienic_first_order_expansions() -> None:
    for relation, arguments, quantifiers in (
        (candidate.positive_primitive_pythagorean, ("a", "b", "c"), "a b c"),
        (candidate.euclidean_parameter_witness, ("a", "b", "c", "m", "n"), "a b c m n"),
        (candidate.euclidean_parametrization, ("a", "b", "c"), "a b c"),
    ):
        first, free = parse_formula_with_names(f"forall {quantifiers}. ({relation(*arguments, tag='first')})")
        second, second_free = parse_formula_with_names(f"forall {quantifiers}. ({relation(*arguments, tag='second')})")
        assert not free and not second_free
        assert first == second
        assert isinstance(first, Forall)
        with pytest.raises(ValueError, match="capture"):
            relation("pi_gap_first", *arguments[1:], tag="first")
        with pytest.raises(ValueError):
            relation(*arguments, tag="injected. false")
        with pytest.raises(ValueError):
            relation("a + b", *arguments[1:], tag="first")


def test_classification_is_an_actual_equivalence_with_both_orientations() -> None:
    formula = _closed_formula(_all()["pythagorean_positive_primitive_classification"].statement)
    for _ in range(3):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, And)
    assert isinstance(formula.left, Imp) and isinstance(formula.right, Imp)
    assert formula.left.left == formula.right.right
    assert formula.left.right == formula.right.left
    target = formula.left.right
    for _ in range(2):
        assert isinstance(target, Exists)
        target = target.body
    for _ in range(5):
        assert isinstance(target, And)
        target = target.right
    assert isinstance(target, Or)
    assert isinstance(target.left, And) and isinstance(target.right, And)


@pytest.mark.parametrize("a,b,c", ((3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13), (8, 15, 17), (15, 8, 17), (20, 21, 29), (21, 20, 29), (33, 56, 65), (56, 33, 65)))
def test_small_examples_follow_the_constructed_half_factors(a: int, b: int, c: int) -> None:
    odd_leg, even_leg = (a, b) if a % 2 else (b, a)
    t = (c - odd_leg) // 2
    upper = odd_leg + t
    m, n = isqrt(upper), isqrt(t)
    assert a * a + b * b == c * c and gcd(a, b) == 1
    assert (c - odd_leg) == 2 * t and upper * t == (even_leg // 2) ** 2
    assert upper == m * m and t == n * n and gcd(upper, t) == 1
    assert m > n > 0 and gcd(m, n) == 1 and (m + n) % 2 == 1
    assert c == m * m + n * n and m * m == n * n + odd_leg and even_leg == 2 * m * n


def test_forward_and_inverse_numeric_sanity_cover_all_small_parameter_orientations() -> None:
    triples: set[tuple[int, int, int]] = set()
    for m in range(2, 25):
        for n in range(1, m):
            if gcd(m, n) != 1 or (m + n) % 2 == 0:
                continue
            odd_leg, even_leg, c = m * m - n * n, 2 * m * n, m * m + n * n
            assert gcd(odd_leg, even_leg) == 1 and min(odd_leg, even_leg, c) > 0
            for a, b in ((odd_leg, even_leg), (even_leg, odd_leg)):
                triples.add((a, b, c))
                assert a * a + b * b == c * c
            assert isqrt((c + odd_leg) // 2) == m
            assert isqrt((c - odd_leg) // 2) == n
    assert len(triples) > 200
    assert 0 * 0 + 1 * 1 == 1 * 1 and gcd(0, 1) == 1
    assert (0, 1, 1) not in triples and (1, 0, 1) not in triples
