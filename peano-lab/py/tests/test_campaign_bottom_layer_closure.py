"""Exact non-admitting closure, hostile proof data, and original HA checks."""

from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import AndIntro, EqRefl, Hyp, ImpIntro
from peano_lab.kernel.terms import Zero
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library import campaign_lower_layer_closure as historical
from peano_lab.library.proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, ProofBundle,
    check_proof_bundle, decode_proof_bundle, encode_proof_bundle,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]


def spec(name="bottom_test_zero", statement="0 = 0", dependencies=(), script=("refl",)):
    return TheoremSpec(name, statement, dependencies, script, "Test-only ordinary HA theorem.")


@pytest.fixture
def tiny_parent(monkeypatch):
    parent = (
        spec("bottom_parent_zero"),
        spec("bottom_parent_one", "1 = 1"),
    )
    snapshot = closure.ParentSnapshot(parent, ())
    monkeypatch.setattr(closure, "parent_snapshot", lambda: snapshot)
    return parent


def build(frontier):
    return closure.assemble_bottom_layer_bundle(frontier, report=lambda message: None)


def test_real_v30_parent_and_all_twenty_provider_pins():
    parent = closure.parent_snapshot()
    assert len(parent.specs) == 3222
    assert len(parent.documents) == 20
    assert closure.PARENT_CATALOG_BYTES == 66_503_303
    assert len({row.name for row in parent.specs}) == 3222
    assert closure.validate_parent_provider_bytes() == parent.documents
    assert any(item.path.endswith("alpha-v30-gaussian-factorization-proof-bundle-v1.json")
               for item in parent.documents)


def test_original_resource_policies_are_reused_without_changes():
    for name in ("MAX_BATCH_ROWS", "MAX_BATCH_PROOF_NODES", "MAX_BATCH_PROOF_OBJECTS"):
        assert getattr(closure, name) == getattr(historical, name)
    assert closure.DEFAULT_LAYERED_REPLAY_LIMITS is historical.DEFAULT_LAYERED_REPLAY_LIMITS
    assert closure.DEFAULT_BUNDLE_LIMITS is DEFAULT_BUNDLE_LIMITS


def test_import_and_planning_never_import_an_edition_or_admit_a_row():
    program = (
        "import sys; from peano_lab.library.campaign_bottom_layer_closure import bottom_layer_plan; "
        "from peano_lab.library.theorems import TheoremSpec; "
        "bottom_layer_plan((TheoremSpec('bottom_import_probe','0=0',(),('refl',),'probe'),)); "
        "assert not any(n.startswith(('peano_lab.library.editions','peano_lab.library.alpha_enrollment')) "
        "for n in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", program], cwd=ROOT,
                   env=dict(os.environ, PYTHONPATH=str(ROOT / "peano-lab/py")),
                   check=True, timeout=45)


@pytest.mark.parametrize("frontier", [None, [], (), "bad", (None,), (True,)])
def test_invalid_frontier_rejected_before_parent_file_read(monkeypatch, frontier):
    monkeypatch.setattr(closure, "parent_snapshot", lambda: pytest.fail("invalid input read parent"))
    with pytest.raises(closure.BottomLayerClosureError):
        closure.bottom_layer_plan(frontier)


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("name", "two words"), ("name", "../outside"),
    ("name", True), ("statement", 1), ("summary", None),
    ("dependencies", []), ("dependencies", (True,)),
    ("dependencies", ("duplicate", "duplicate")), ("script", []),
    ("script", ()), ("script", (None,)), ("script", ("",)),
    ("script", ("use secret",)), ("script", ("admit",)),
    ("script", ("sorry",)), ("script", ("DNE",)),
])
def test_malformed_spec_rejected_before_parent_read(monkeypatch, field, value):
    monkeypatch.setattr(closure, "parent_snapshot", lambda: pytest.fail("invalid row read parent"))
    with pytest.raises(closure.BottomLayerClosureError):
        closure.bottom_layer_plan((replace(spec(), **{field: value}),))


def test_free_object_variable_does_not_become_a_closed_target(tiny_parent):
    with pytest.raises(ValueError):
        closure.bottom_layer_plan((spec(statement="x = x"),))


@pytest.mark.parametrize("frontier", [
    (spec("bottom_parent_zero"),),
    (spec(), spec()),
    (spec(dependencies=("not_a_theorem",)),),
    (spec(dependencies=("bottom_later",)), spec("bottom_later")),
    (spec(dependencies=("bottom_test_zero",)),),
    (spec("cycle_a", dependencies=("cycle_b",)), spec("cycle_b", dependencies=("cycle_a",))),
])
def test_shadowed_unknown_forward_or_cyclic_premises_rejected(tiny_parent, frontier):
    with pytest.raises(closure.BottomLayerClosureError):
        closure.bottom_layer_plan(frontier)


def test_maximal_roots_cover_every_new_theorem_and_only_real_ancestors(tiny_parent):
    rows = (
        spec("bottom_first", dependencies=("bottom_parent_zero",), script=("exact bottom_parent_zero",)),
        spec("bottom_second", dependencies=("bottom_first",), script=("exact bottom_first",)),
        spec("bottom_independent", "2 = 2"),
    )
    plan = closure.bottom_layer_plan(rows)
    assert tuple(row.name for row in plan.rows) == (
        "bottom_parent_zero", "bottom_first", "bottom_second", "bottom_independent",
    )
    assert plan.root_names == ("bottom_second", "bottom_independent")
    assert plan.frontier_names == tuple(row.name for row in rows)
    assert plan.dependency_edge_count == 2
    assert [row.is_frontier for row in plan.rows] == [False, True, True, True]
    assert plan.frontier_specs_sha256 == historical._specs_digest(rows)
    assert plan.ordered_names_sha256 == sha256(
        b"bottom_parent_zero\nbottom_first\nbottom_second\nbottom_independent"
    ).hexdigest()


def test_complete_checkpoint_and_ordinary_empty_context_certificate(tiny_parent):
    rows = (spec(dependencies=("bottom_parent_zero",), script=("exact bottom_parent_zero",)),)
    result = build(rows)
    assert result.receipt.node_count == result.receipt.kernel_calls == 3
    assert result.receipt.dependency_edges == 2
    assert result.origins[0][1:] == ("parent_script", None)
    assert result.origins[1][1:] == ("new_script", None)
    assert check_proof_bundle(result.bundle, result.target) == result.receipt
    theorem = closure.replay_bottom_layer_theorem(rows, rows[0].name, result.bundle, result.target)
    assert theorem.formula == _closed_formula("0 = 0")
    assert check((), theorem.certificate, theorem.formula)


def test_unproved_parent_cannot_be_laundered_through_a_valid_conditional_body(monkeypatch):
    bad_parent = spec("bottom_false_parent", "0 = 1", script=("refl",))
    monkeypatch.setattr(closure, "parent_snapshot", lambda: closure.ParentSnapshot((bad_parent,), ()))
    rows = (spec(statement="0 = 1", dependencies=(bad_parent.name,), script=("exact bottom_false_parent",)),)
    with pytest.raises(ValueError):
        build(rows)


@pytest.mark.parametrize("mutation", ["conclusion", "missing_premise", "wrong_body", "wrong_script"])
def test_false_or_incomplete_new_proof_is_rejected(tiny_parent, mutation):
    row = spec(dependencies=("bottom_parent_zero",), script=("exact bottom_parent_zero",))
    if mutation == "conclusion":
        row = replace(row, statement="0 = 1")
    elif mutation == "missing_premise":
        row = replace(row, dependencies=())
    elif mutation == "wrong_body":
        row = replace(row, script=("intro impossible",))
    else:
        row = replace(row, script=("exact bottom_parent_one",))
    with pytest.raises(ValueError):
        build((row,))


@pytest.mark.parametrize("mutation", [
    "missing_node", "extra_node", "reordered_nodes", "wrong_root", "wrong_id",
    "wrong_target", "wrong_premise", "omitted_premise", "body", "package_body",
    "package_target", "package_premises", "external_target",
])
def test_exact_bundle_mutations_fail_closed(tiny_parent, mutation):
    rows = (spec(dependencies=("bottom_parent_zero",), script=("exact bottom_parent_zero",)),)
    result = build(rows)
    nodes, root, target = list(result.bundle.nodes), result.bundle.root, result.target
    false = _closed_formula("0 = 1")
    if mutation == "missing_node":
        nodes.pop()
    elif mutation == "extra_node":
        nodes.append(nodes[-1])
    elif mutation == "reordered_nodes":
        nodes[0], nodes[1] = nodes[1], nodes[0]
    elif mutation == "wrong_root":
        root = 0
    elif mutation == "wrong_id":
        nodes[1] = replace(nodes[1], node_id=5)
    elif mutation == "wrong_target":
        nodes[1] = replace(nodes[1], target=false)
    elif mutation == "wrong_premise":
        nodes[1] = replace(nodes[1], dependencies=(1,))
    elif mutation == "omitted_premise":
        nodes[1] = replace(nodes[1], dependencies=())
    elif mutation == "body":
        nodes[0] = replace(nodes[0], body=Hyp(0))
    elif mutation == "package_body":
        nodes[-1] = replace(nodes[-1], body=Hyp(0))
    elif mutation == "package_target":
        nodes[-1] = replace(nodes[-1], target=false)
    elif mutation == "package_premises":
        nodes[-1] = replace(nodes[-1], dependencies=(0,))
    else:
        target = false
    with pytest.raises(ValueError):
        closure.check_bottom_layer_bundle(rows, ProofBundle(tuple(nodes), root), target)


@pytest.mark.parametrize("batch", [0, -1, 17, True, "1", None])
def test_invalid_batch_rejected_before_any_source_or_proof_read(monkeypatch, batch):
    monkeypatch.setattr(closure, "parent_snapshot", lambda: pytest.fail("invalid batch read source"))
    with pytest.raises(closure.BottomLayerClosureError):
        closure.assemble_bottom_layer_bundle((spec(),), batch_size=batch)


@pytest.mark.parametrize("seeds", [None, [], "file", (True,), ("same", "./same")])
def test_malformed_or_duplicate_seed_paths_rejected_before_source_read(monkeypatch, seeds):
    monkeypatch.setattr(closure, "parent_snapshot", lambda: pytest.fail("invalid seed selection read source"))
    with pytest.raises(closure.BottomLayerClosureError):
        closure.assemble_bottom_layer_bundle((spec(),), seed_bundles=seeds)


def test_checked_seed_is_reused_only_after_all_nodes_pass(tiny_parent, tmp_path, monkeypatch):
    rows = (spec(dependencies=("bottom_parent_zero",), script=("exact bottom_parent_zero",)),)
    initial = build(rows)
    seed = tmp_path / "checked-seed.json"
    seed.write_text(encode_proof_bundle(initial.bundle, initial.target))
    calls = []
    original = closure.check_proof_bundle

    def observed(bundle, target):
        result = original(bundle, target)
        calls.append(result.kernel_calls)
        return result

    monkeypatch.setattr(closure, "check_proof_bundle", observed)
    monkeypatch.setattr(closure, "_reconstruct_body", lambda *_: pytest.fail("exact seed body was rebuilt"))
    actual = closure.assemble_bottom_layer_bundle(rows, seed_bundles=(seed,), report=lambda _: None)
    assert calls == [3, 3]
    assert actual.bundle == initial.bundle
    assert all(source == str(seed) for _, source, _ in actual.origins)


def test_bad_unused_seed_body_cannot_hide_behind_a_valid_selected_root(tiny_parent, tmp_path):
    rows = (spec(),)
    correct, false = _closed_formula("0=0"), _closed_formula("0=1")
    target = And(correct, false)
    seed = ProofBundle((
        BundleNode(0, correct, (), EqRefl(Zero())),
        BundleNode(1, false, (), EqRefl(Zero())),
        BundleNode(2, target, (0, 1), ImpIntro(ImpIntro(AndIntro(Hyp(1), Hyp(0))))),
    ), 2)
    path = tmp_path / "bad-extra-seed.json"
    path.write_text(encode_proof_bundle(seed, target))
    with pytest.raises(ValueError):
        closure.assemble_bottom_layer_bundle(rows, seed_bundles=(path,), report=lambda _: None)


def test_all_parent_pins_checked_even_when_seed_supplies_every_body(tiny_parent, tmp_path, monkeypatch):
    rows = (spec(),)
    result = build(rows)
    seed = tmp_path / "complete-seed.json"
    seed.write_text(encode_proof_bundle(result.bundle, result.target))

    def poisoned_provider():
        raise closure.BottomLayerClosureError("unused immutable provider was changed")

    monkeypatch.setattr(closure, "validate_parent_provider_bytes", poisoned_provider)
    with pytest.raises(closure.BottomLayerClosureError, match="unused immutable"):
        closure.assemble_bottom_layer_bundle(rows, seed_bundles=(seed,), report=lambda _: None)


def test_seed_with_same_target_but_different_ordered_premises_is_not_reused(tiny_parent, tmp_path):
    rows = (spec(dependencies=("bottom_parent_zero", "bottom_parent_one")),)
    seed = ProofBundle((
        BundleNode(0, _closed_formula("0=0"), (), EqRefl(Zero())),
        BundleNode(1, _closed_formula("1=1"), (), historical._reconstruct_body(tiny_parent[1], {})),
        BundleNode(2, _closed_formula("0=0"), (1, 0), ImpIntro(ImpIntro(EqRefl(Zero())))),
    ), 2)
    target = _closed_formula("0=0")
    assert check_proof_bundle(seed, target).kernel_calls == 3
    path = tmp_path / "different-premises.json"
    path.write_text(encode_proof_bundle(seed, target))
    result = closure.assemble_bottom_layer_bundle(rows, seed_bundles=(path,), report=lambda _: None)
    assert result.origins[-1][1:] == ("new_script", None)


@pytest.mark.parametrize("mutation", ["missing", "size", "bytes", "symlink"])
def test_bounded_pinned_read_rejects_wrong_sources(tmp_path, mutation):
    source = tmp_path / "provider.json"
    expected = b"proof-data"
    if mutation != "missing":
        source.write_bytes(expected if mutation in ("size", "symlink") else b"Proof-data")
    if mutation == "symlink":
        link = tmp_path / "alias.json"
        link.symlink_to(source)
        source = link
    size = len(expected) + (mutation == "size")
    with pytest.raises(closure.BottomLayerClosureError):
        closure._read_pinned(source, size, sha256(expected).hexdigest())


def test_export_is_checked_deterministic_and_never_overwrites(tiny_parent, tmp_path, monkeypatch):
    rows = (spec(),)
    destination = tmp_path / "new" / "proof.json"
    result = closure.export_bottom_layer_bundle(rows, destination)
    raw = destination.read_text()
    decoded, target = decode_proof_bundle(raw)
    assert raw == encode_proof_bundle(result.bundle, result.target)
    assert check_proof_bundle(decoded, target) == result.receipt
    monkeypatch.setattr(closure, "assemble_bottom_layer_bundle", lambda *_args, **_kwargs: pytest.fail("overwrite rebuilt proof"))
    with pytest.raises(closure.BottomLayerClosureError, match="never overwrites"):
        closure.export_bottom_layer_bundle(rows, destination)
    assert destination.read_text() == raw


def test_unknown_named_replay_rejected(tiny_parent):
    rows = (spec(),)
    result = build(rows)
    with pytest.raises(closure.BottomLayerClosureError, match="unknown"):
        closure.replay_bottom_layer_theorem(rows, "nonexistent", result.bundle, result.target)
