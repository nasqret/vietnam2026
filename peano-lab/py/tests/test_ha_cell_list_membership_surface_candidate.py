"""Focused audit for the conservative K3C CellListValid/ListMember surfaces."""

from __future__ import annotations

import pytest

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.ha_cell_list_membership_surface_candidate import (
    cell_list_member,
    cell_list_valid,
)


FORBIDDEN = (
    "BetaAt(",
    "Cell(",
    "CellHistory(",
    "CellList(",
    "CellListValid(",
    "CellListLen(",
    "ListAt(",
    "ListMember(",
)


def test_k3c_surfaces_expand_to_alpha_stable_base_language_formulas() -> None:
    valid = cell_list_valid("z", tag="surface")
    member = cell_list_member("z", "a", tag="surface")
    valid_renamed = cell_list_valid("z", tag="surface_renamed")
    member_renamed = cell_list_member("z", "a", tag="surface_renamed")

    assert all(token not in valid and token not in member for token in FORBIDDEN)
    assert parse_formula(f"forall z. {valid}") == parse_formula(
        f"forall z. {valid_renamed}"
    )
    assert parse_formula(f"forall z a. {member}") == parse_formula(
        f"forall z a. {member_renamed}"
    )
    assert parse_formula_with_names(f"forall z. {valid}")[1] == ()
    assert parse_formula_with_names(f"forall z a. {member}")[1] == ()


def test_k3c_membership_allows_semantically_equal_code_and_value_arguments() -> None:
    source = cell_list_member("z", "z", tag="diagonal")
    formula, free = parse_formula_with_names(f"forall z. {source}")
    assert not free
    assert formula == parse_formula(f"forall z. {source}")


def test_k3c_surfaces_reject_compounds_reserved_tags_and_capture() -> None:
    with pytest.raises(ValueError):
        cell_list_valid("S z", tag="bad_compound")
    with pytest.raises(ValueError):
        cell_list_member("z", "a + b", tag="bad_compound")
    with pytest.raises(ValueError):
        cell_list_valid("z", tag="forall")
    with pytest.raises(ValueError):
        cell_list_valid("hclist_length_capture", tag="capture")
    with pytest.raises(ValueError):
        cell_list_member("hclist_member_index_capture", "a", tag="capture")


def test_k3c_surface_has_expected_existential_shape() -> None:
    valid = cell_list_valid("z", tag="shape")
    member = cell_list_member("z", "a", tag="shape")
    assert valid.startswith("exists hclist_length_shape. (")
    assert member.startswith("exists hclist_member_index_shape. (")
    assert "hclist_length_shape" in valid
    assert "hclist_member_index_shape" in member
