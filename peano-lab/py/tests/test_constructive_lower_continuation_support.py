"""Support syntax cannot relabel either inherited proof generation as new."""

from dataclasses import replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_lower_continuation_support as support
import constructive_lower_tier_checkpoints as lower
import constructive_lower_tier_support as previous
from peano_lab.library import campaign_bottom_layer_closure as closure


@pytest.fixture(scope="module")
def inherited():
    return next(row for row in lower.all_new_rows() if row.name == "signed_divisor_sum_exists_unique")


def _syntactic_child(row, name="support_test_child"):
    # Deliberately a restatement for a syntax-selection/duplicate rejection
    # test. It is neither a mathematical contribution nor a checked proof.
    return replace(row, name=name, dependencies=(row.name,), script=("exact " + row.name,))


def test_both_prior_generations_are_exact_and_not_counted_as_new():
    rows = support.previous_rows()
    assert len(rows) == 296
    assert rows == (*previous.previous_rows(), *lower.all_new_rows())
    assert len({row.name for row in rows}) == len(rows)


def test_actual_cone_preserves_four_separate_inventory_roles(inherited):
    child = _syntactic_child(inherited)
    parent = _syntactic_child(child, "support_test_root")
    selected = support.select_support((child, parent), (parent.name,))
    assert selected.owned == (parent,)
    assert selected.current_support == (child.name,)
    assert inherited.name in selected.lower_support
    assert selected.bottom_support
    assert selected.role(parent.name) == "new_owned_theorem"
    assert selected.role(child.name) == "new_cross_track_support"
    assert selected.role(inherited.name) == "inherited_published_lower_tier_checkpoint"
    assert selected.role(selected.bottom_support[0]) == "inherited_published_bottom_layer_checkpoint"
    alpha = set(row.name for row in selected.plan.rows) - {row.name for row in selected.frontier}
    assert alpha and selected.role(next(iter(alpha))) == "inherited_alpha_v30"
    assert selected.published_support == selected.bottom_support + selected.lower_support
    assert set(selected.plan.root_names) <= {parent.name}
    with pytest.raises(support.SupportError):
        selected.role("no_such_proof")


@pytest.mark.parametrize("bad_names", ((), [], ("no_such_proof",), (1,), ("signed_divisor_sum_exists_unique",)))
def test_owned_rows_must_be_current_and_nonempty(inherited, bad_names):
    child = _syntactic_child(inherited)
    with pytest.raises((ValueError, TypeError)):
        support.select_support((child,), bad_names)


def test_duplicate_owned_names_rejected(inherited):
    child = _syntactic_child(inherited)
    with pytest.raises(ValueError):
        support.select_support((child,), (child.name, child.name))


@pytest.mark.parametrize("mutation", ("unknown", "forward", "cycle", "shadow_lower", "shadow_bottom"))
def test_hidden_invalid_inventory_rejected_even_when_not_in_owned_cone(inherited, mutation):
    child = _syntactic_child(inherited)
    other = replace(child, name="unused_bad_proof", dependencies=("unknown_proof",))
    if mutation == "forward":
        other = replace(other, dependencies=("later_proof",))
        rows = (child, other, replace(child, name="later_proof"))
    elif mutation == "cycle":
        rows = (child, replace(other, dependencies=(other.name,)))
    elif mutation == "shadow_lower":
        rows = (child, replace(other, name=inherited.name))
    elif mutation == "shadow_bottom":
        rows = (child, replace(other, name=previous.previous_rows()[0].name))
    else:
        rows = (child, other)
    with pytest.raises(ValueError):
        support.select_support(rows, (child.name,))


def test_exact_ast_duplicate_comparison_includes_prior_126_and_current_rows(inherited):
    first = _syntactic_child(inherited, "duplicate_one")
    second = replace(first, name="duplicate_two", statement="  " + inherited.statement + "  ")
    duplicates = support.statement_duplicates((first, second))
    assert (first.name, inherited.name) in duplicates
    assert (second.name, inherited.name) in duplicates
    assert (second.name, first.name) in duplicates
    assert all(left in {first.name, second.name} for left, _ in duplicates)


def test_real_seven_seed_paths_are_byte_authenticated():
    paths = support.previous_seed_paths()
    assert len(paths) == 7
    assert len(set(paths)) == 7
    assert paths[:4] == previous.previous_seed_paths()
    for path, checkpoint in zip(paths[4:], lower.CHECKPOINTS, strict=True):
        assert path == ROOT / checkpoint.artifact
        closure._read_pinned(path, checkpoint.artifact_bytes, checkpoint.artifact_sha256)


def test_changed_prior_source_or_ordered_specs_are_not_accepted(inherited, monkeypatch):
    def reject(*_):
        raise lower.CheckpointError("prior proof source changed")
    monkeypatch.setattr(lower, "load_rows", reject)
    with pytest.raises(lower.CheckpointError, match="source changed"):
        support.select_support((_syntactic_child(inherited),), ("support_test_child",))
    with pytest.raises(lower.CheckpointError):
        support.previous_rows()
