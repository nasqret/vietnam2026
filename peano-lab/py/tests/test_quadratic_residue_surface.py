"""Syntax, hygiene, and input-budget contract for the QR campaign surface."""

from __future__ import annotations

import pytest

import driver

from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.library.quadratic_residue_surface import (
    SURFACE_FORMULAS,
    bounded_quadratic_residue,
    congruent_mod,
    quadratic_residue,
)


def test_every_qr_campaign_formula_is_closed_and_round_trips() -> None:
    for source in SURFACE_FORMULAS.values():
        formula, free_names = parse_formula_with_names(source)
        assert free_names == ()
        rendered = pretty_formula(formula, [])
        reparsed, reparsed_free_names = parse_formula_with_names(rendered)
        assert reparsed_free_names == ()
        assert reparsed == formula


def test_qr_endpoint_has_large_input_budget_margin() -> None:
    lengths = {name: len(source) for name, source in SURFACE_FORMULAS.items()}
    assert lengths == {
        "mod_eq_decidable_nonzero": 185,
        "quadratic_residue_bounded_equiv": 694,
        "quadratic_residue_search_up_to": 471,
        "quadratic_residue_bounded_decidable_nonzero": 401,
        "quadratic_residue_decidable_nonzero": 309,
        "quadratic_reciprocity_same_case": 980,
        "quadratic_reciprocity_opposite_case": 988,
        "quadratic_reciprocity_combined": 1_520,
    }
    assert max(lengths.values()) < driver.MAX_INPUT // 2


def test_surface_expands_every_expository_predicate_name() -> None:
    forbidden = ("CongMod", "Odd", "Prime", "QRes", "Residue")
    for source in SURFACE_FORMULAS.values():
        assert not any(name in source for name in forbidden)


@pytest.mark.parametrize(
    "bad_identifier",
    ("", "p + 1", "forall", "exists", "S", "0", "x) -> false"),
)
def test_surface_rejects_non_identifier_interpolation(bad_identifier: str) -> None:
    with pytest.raises(ValueError, match="Peano identifier"):
        quadratic_residue(bad_identifier, "a", tag="test")


def test_surface_rejects_generated_binder_capture() -> None:
    with pytest.raises(ValueError, match="captures"):
        quadratic_residue("qr_x_test", "a", tag="test")


def test_surface_examples_remain_open_only_in_declared_arguments() -> None:
    examples = (
        congruent_mod("p", "a", "b", tag="example"),
        quadratic_residue("p", "a", tag="example"),
        bounded_quadratic_residue("p", "a", tag="example"),
    )
    expected = (("a", "p", "b"), ("p", "a"), ("p", "a"))
    for source, free_names in zip(examples, expected, strict=True):
        _, actual = parse_formula_with_names(source)
        assert actual == free_names
