"""New research rows retain exact old proof support without new admissions."""

from dataclasses import replace
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_lower_tier_support as support
from peano_lab.kernel.checker import check
from peano_lab.library.theorems import TheoremSpec


def spec(name, statement="0=0", dependencies=(), script=("refl",)):
    return TheoremSpec(name, statement, dependencies, script, "Test-only support syntax.")


@pytest.fixture
def tiny_inventory(monkeypatch):
    parent = (spec("parent_zero"), spec("parent_unused", "1=1"))
    old = (
        spec("old_first", dependencies=("parent_zero",), script=("exact parent_zero",)),
        spec("old_second", dependencies=("old_first",), script=("exact old_first",)),
        spec("old_unused", "2=2"),
    )
    monkeypatch.setattr(support.closure, "parent_snapshot",
                        lambda: support.closure.ParentSnapshot(parent, ()))
    monkeypatch.setattr(support, "previous_rows", lambda: old)
    return parent, old


def test_only_genuine_ancestors_are_selected_and_counted_by_role(tiny_inventory):
    rows = (
        spec("new_append", dependencies=("old_second",), script=("exact old_second",)),
        spec("new_mask", dependencies=("new_append",), script=("exact new_append",)),
        spec("new_other", "3=3"),
        spec("new_final", dependencies=("new_mask",), script=("exact new_mask",)),
    )
    selection = support.select_support(rows, ("new_mask", "new_final"))
    assert tuple(row.name for row in selection.owned) == ("new_mask", "new_final")
    assert tuple(row.name for row in selection.frontier) == (
        "old_first", "old_second", "new_append", "new_mask", "new_final",
    )
    assert selection.published_support == ("old_first", "old_second")
    assert selection.current_support == ("new_append",)
    assert selection.plan.root_names == ("new_final",)
    assert [selection.role(row.name) for row in selection.plan.rows] == [
        "inherited_alpha_v30", "inherited_published_non_admitted_checkpoint",
        "inherited_published_non_admitted_checkpoint", "new_cross_track_support",
        "new_owned_theorem", "new_owned_theorem",
    ]
    with pytest.raises(support.LowerTierSupportError):
        selection.role("old_unused")


@pytest.mark.parametrize("names", [None, [], (), (1,), ("new", "new"),
                                    ("old_first",), ("absent",), ("new_two", "new")])
def test_bad_ownership_rejected_before_any_historical_read(monkeypatch, names):
    monkeypatch.setattr(support, "previous_rows", lambda: pytest.fail("invalid ownership read history"))
    with pytest.raises(support.LowerTierSupportError):
        support.select_support((spec("new"), spec("new_two")), names)


@pytest.mark.parametrize("bad", [
    spec("old_first"), spec("parent_zero"), spec("unrelated", dependencies=("absent",)),
    spec("unrelated", dependencies=("unrelated",)),
])
def test_shadowed_or_bad_unused_rows_are_not_hidden_by_selection(tiny_inventory, bad):
    with pytest.raises(support.closure.BottomLayerClosureError):
        support.select_support((spec("new"), bad), ("new",))


def test_old_checkpoint_body_is_closed_in_the_actual_original_ha_proof(tiny_inventory):
    rows = (spec("new", dependencies=("old_second",), script=("exact old_second",)),)
    selection = support.select_support(rows, ("new",))
    closed = support.closure.assemble_bottom_layer_bundle(selection.frontier, report=lambda _: None)
    assert closed.receipt.node_count == closed.receipt.kernel_calls == 5
    theorem = support.closure.replay_bottom_layer_theorem(
        selection.frontier, "new", closed.bundle, closed.target,
    )
    assert check((), theorem.certificate, theorem.formula)


def test_false_inherited_checkpoint_cannot_become_an_assumed_oracle(tiny_inventory, monkeypatch):
    _, old = tiny_inventory
    bad = replace(old[1], statement="0=1", script=("refl",))
    monkeypatch.setattr(support, "previous_rows", lambda: (old[0], bad, old[2]))
    rows = (spec("new", "0=1", ("old_second",), ("exact old_second",)),)
    selection = support.select_support(rows, ("new",))
    with pytest.raises(ValueError):
        support.closure.assemble_bottom_layer_bundle(selection.frontier, report=lambda _: None)


def test_novelty_compares_alpha_equivalent_asts_and_all_three_roles(tiny_inventory):
    rows = (spec("renamed_parent"), spec("renamed_old", "2 = 2"),
            spec("alpha_a", "forall x. x=x", script=("intro x", "refl")),
            spec("alpha_b", "∀long_name. long_name=long_name", script=("intro x", "refl")))
    assert set(support.statement_duplicates(rows)) == {
        ("renamed_parent", "parent_zero"), ("renamed_parent", "old_first"),
        ("renamed_parent", "old_second"), ("renamed_old", "old_unused"),
        ("alpha_b", "alpha_a"),
    }


def test_novelty_does_not_expand_large_double_and_add_numeral_trees(tiny_inventory):
    number = 2 ** 120 + 12345
    rows = (spec("big_a", f"{number}={number}"),
            spec("big_b", f"({number}) = ({number})"),
            spec("different", f"{number + 1}={number + 1}"))
    assert support.statement_duplicates(rows) == (("big_b", "big_a"),)


def test_real_170_sources_and_ordered_specifications_are_authenticated():
    rows = support.previous_rows()
    assert len(rows) == len({row.name for row in rows}) == 170
    assert len(support.previous_seed_paths()) == 4
    assert support.closure.PARENT_COUNT == 3222
