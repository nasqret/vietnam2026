"""Syntax, compatibility, and size contracts for β-coded finite folds."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import driver

from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.library.finite_fold_surface import (
    SURFACE_FORMULAS,
    all_bits,
    beta_at,
    bit_count,
    power_relation,
    product_relation,
    product_successor_relation,
    range_relation,
    repeat_relation,
    sum_relation,
)


ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "research" / "arithmetic-library" / "catalog.json"


def test_every_finite_fold_formula_is_closed_and_round_trips() -> None:
    for source in SURFACE_FORMULAS.values():
        formula, free_names = parse_formula_with_names(source)
        assert free_names == ()
        rendered = pretty_formula(formula, [])
        reparsed, reparsed_free_names = parse_formula_with_names(rendered)
        assert reparsed_free_names == ()
        assert reparsed == formula


def test_finite_fold_endpoints_fit_the_interactive_input_budget() -> None:
    lengths = {name: len(source) for name, source in SURFACE_FORMULAS.items()}
    assert lengths == {
        "beta_sum_exists": 1_020,
        "beta_sum_functional": 2_023,
        "bit_count_bounded": 1_630,
        "bit_count_exists": 1_907,
        "bit_count_functional": 3_213,
        "range_exists": 263,
        "repeat_exists": 245,
        "power_exists": 1_813,
        "power_functional": 3_611,
        "power_zero": 1_823,
        "power_successor_decompose": 3_642,
    }
    assert max(lengths.values()) <= 3_650
    assert max(lengths.values()) < driver.MAX_INPUT


def test_beta_at_and_product_match_the_checked_catalog_conventions() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    conventions = catalog["expanded_predicate_conventions"]
    comparisons = (
        (
            conventions["beta_at(b,c,i,x)"],
            beta_at("b", "c", "i", "x", tag="compat"),
        ),
        (
            conventions["product(b,c,l,n)"],
            product_relation("b", "c", "l", "n", tag="compat"),
        ),
    )
    for expected_source, actual_source in comparisons:
        expected, expected_names = parse_formula_with_names(expected_source)
        actual, actual_names = parse_formula_with_names(actual_source)
        assert actual_names == expected_names
        assert actual == expected


def test_range_parenthesizes_the_compound_decoded_value() -> None:
    expected_source = (
        "forall b c a l i. (exists h. h + S i = l) -> "
        "((exists h. h + S (a + i) = S ((S i) * c)) /\\ "
        "exists q. b = q * S ((S i) * c) + (a + i))"
    )
    actual_source = (
        "forall b c a l. " + range_relation("b", "c", "a", "l", tag="parentheses")
    )
    expected, expected_names = parse_formula_with_names(expected_source)
    actual, actual_names = parse_formula_with_names(actual_source)
    assert expected_names == actual_names == ()
    assert actual == expected


def test_product_successor_relation_assembles_only_the_audited_compound_length() -> None:
    source = product_successor_relation("b", "c", "n", "p", tag="successor")
    _, free_names = parse_formula_with_names(source)
    assert set(free_names) == {"b", "c", "n", "p"}
    assert "S ((S (S n))" in source
    assert " = S n)" in source

    with pytest.raises(ValueError, match="Peano identifier"):
        product_successor_relation("b", "c", "n + 1", "p", tag="successor")


def test_finite_fold_surface_expands_all_expository_names() -> None:
    forbidden = ("AllBits", "BetaAt", "BitCount", "Pow", "Product", "Range", "Repeat", "Sum")
    for source in SURFACE_FORMULAS.values():
        assert not any(name in source for name in forbidden)


@pytest.mark.parametrize(
    "bad_identifier",
    ("", "i + 1", "forall", "exists", "S", "0", "x) -> false"),
)
def test_finite_fold_surface_rejects_term_interpolation(bad_identifier: str) -> None:
    with pytest.raises(ValueError, match="Peano identifier"):
        sum_relation(bad_identifier, "c", "l", "n", tag="test")


def test_finite_fold_surface_rejects_generated_binder_capture() -> None:
    with pytest.raises(ValueError, match="captures"):
        sum_relation("ff_u_test", "c", "l", "n", tag="test")


def test_relation_helpers_are_open_only_in_their_arguments() -> None:
    examples = (
        (sum_relation("b", "c", "l", "n", tag="open"), {"b", "c", "l", "n"}),
        (
            product_successor_relation("b", "c", "l", "n", tag="open"),
            {"b", "c", "l", "n"},
        ),
        (all_bits("b", "c", "l", tag="open"), {"b", "c", "l"}),
        (bit_count("b", "c", "l", "n", tag="open"), {"b", "c", "l", "n"}),
        (range_relation("b", "c", "a", "l", tag="open"), {"b", "c", "a", "l"}),
        (repeat_relation("b", "c", "a", "l", tag="open"), {"b", "c", "a", "l"}),
        (power_relation("a", "e", "n", tag="open"), {"a", "e", "n"}),
    )
    for source, expected_names in examples:
        _, actual_names = parse_formula_with_names(source)
        assert set(actual_names) == expected_names
