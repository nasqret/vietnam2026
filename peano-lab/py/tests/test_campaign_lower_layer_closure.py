"""No catalogue, cache, digest, or packaging shortcut supplies proof authority."""

from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from peano_lab.kernel.formulas import And, Bot
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import campaign_lower_layer_closure as closure
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, ProofBundleError, encode_proof_bundle,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]


def test_parent_is_an_exact_immutable_specification_not_a_new_edition():
    snapshot = closure.parent_snapshot()
    assert len(snapshot.specs) == closure.PARENT_COUNT == 2560
    assert sha256((ROOT / closure.PARENT_CATALOG).read_bytes()).hexdigest() == closure.PARENT_CATALOG_SHA256
    assert tuple(document.bytes for document in snapshot.documents) == tuple(sorted(document.bytes for document in snapshot.documents))
    assert all(document.path.startswith("research/arithmetic-library/artifacts/") for document in snapshot.documents)
    assert len({row.name for row in snapshot.specs}) == 2560
    assert len(snapshot.documents) == 17


def test_all_seventeen_parent_proof_provider_byte_pins_are_unchanged():
    assert closure.validate_parent_provider_bytes() == closure.parent_snapshot().documents


def test_complete_real_frontier_is_dependency_closed_and_topological():
    plan = closure.lower_layer_plan()
    assert plan.frontier_names == tuple(row.name for row in closure.lower_layer_specs())
    assert {"foundation_division_exists_unique", "prime_factor_lists_permutation_exists",
            "first_primes_double_exponential_bound"} <= set(plan.frontier_names)
    rows = {row.name: row for row in plan.rows}
    pending, visited = list(plan.root_names), set()
    while pending:
        name = pending.pop()
        if name not in visited:
            visited.add(name)
            pending.extend(rows[name].dependencies)
    assert visited == set(rows)
    assert set(plan.frontier_names) <= visited
    seen = set()
    for index, row in enumerate(plan.rows):
        assert row.node_id == index
        assert set(row.dependencies) <= seen
        seen.add(row.name)
    assert plan.dependency_edge_count == sum(len(row.dependencies) for row in plan.rows)
    assert plan.ordered_names_sha256 == sha256("\n".join(rows).encode()).hexdigest()
    assert all((ROOT / "research/arithmetic-library" / owner.rfc).is_file() for owner in closure.FACTORIES)


def test_metadata_planning_does_not_eagerly_import_alpha_editions():
    code = (
        "import sys; from peano_lab.library.campaign_lower_layer_closure import lower_layer_plan; "
        "lower_layer_plan(); assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules)"
    )
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "peano-lab/py"))
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=environment, check=True, timeout=45)


def test_runtime_parent_specs_need_no_catalogue_or_historical_provider_files(monkeypatch):
    specs = closure.parent_snapshot().specs
    expected = closure.lower_layer_plan()
    assert closure._specs_digest(specs) == closure.PARENT_SPECS_SHA256
    monkeypatch.setattr(closure, "parent_snapshot", lambda: pytest.fail("runtime read a catalogue or historical provider"))
    assert closure.lower_layer_plan(parent_specs=specs) == expected
    assert len(closure._table((), specs)) == 2560 + len(closure.lower_layer_specs())


def test_short_browser_module_path_imports_and_plans_without_a_catalogue(monkeypatch):
    module = ModuleType("peano_lab.library._lower_layer_browser_layout_test")
    module.__file__ = "/lab/peano_lab/library/campaign_lower_layer_closure.py"
    module.__package__ = "peano_lab.library"
    monkeypatch.setitem(sys.modules, module.__name__, module)
    source = (ROOT / "peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py").read_text()
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    assert module.ROOT == Path("/lab")
    supplied = closure.parent_snapshot().specs
    assert module.lower_layer_plan(parent_specs=supplied).frontier_names == closure.lower_layer_plan().frontier_names


@pytest.mark.parametrize("mutation", ("count", "order", "statement", "script", "summary", "name", "type"))
def test_supplied_runtime_parent_is_exact_and_fail_closed(mutation):
    specs = closure.parent_snapshot().specs
    if mutation == "count":
        changed = specs[:-1]
    elif mutation == "order":
        changed = tuple(reversed(specs))
    elif mutation == "type":
        changed = list(specs)
    else:
        value = {"statement": "0 = 1", "script": ("refl",), "summary": "unbound source", "name": "forged"}[mutation]
        changed = (replace(specs[0], **{mutation: value}),) + specs[1:]
        if changed == specs:
            changed = (replace(specs[0], script=("intro unused",)),) + specs[1:]
    with pytest.raises(closure.LowerLayerError):
        closure._parent_specs(changed)


def test_authoring_limits_are_the_existing_policy_not_relaxed_limits():
    source = ast.parse((ROOT / "peano-lab/py/peano_lab/library/frontier_promotion.py").read_text())
    assignments = {
        target.id: ast.literal_eval(node.value)
        for node in source.body if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert closure.MAX_BATCH_ROWS == assignments["MAX_FRONTIER_CLOSURE_MICROBATCH"] == 16
    assert closure.MAX_BATCH_PROOF_NODES == assignments["MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES"] == 125000
    assert closure.MAX_BATCH_PROOF_OBJECTS == assignments["MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS"] == 25000


@pytest.mark.parametrize("selection", (("unknown",), ("foundations", "foundations"), ["foundations"], (True,)))
def test_unknown_or_ambiguous_campaign_selection_is_rejected(selection):
    with pytest.raises(closure.LowerLayerError):
        closure.selected_factories(selection)


@pytest.mark.parametrize("batch_size", (0, -1, True, 1.5, 17))
def test_invalid_batch_is_rejected_before_any_replay(batch_size):
    with pytest.raises(closure.LowerLayerError, match="1..16"):
        closure.assemble_lower_layer_proof_bundle(batch_size=batch_size)


@pytest.fixture
def tiny_inventory(monkeypatch):
    """Small *real* HA bodies exercise the same closed-bundle authority path."""
    parent = TheoremSpec("base", "0 = 0", (), ("refl",), "Reflexivity.")
    candidates = [
        TheoremSpec("left", "0 = 0", ("base",), ("exact base",), "Actual prerequisite."),
        TheoremSpec("right", "forall n. n = n", (), ("intro n", "refl"), "Universal reflexivity."),
    ]
    closure.lower_layer_specs.cache_clear()
    closure.lower_layer_plan.cache_clear()
    monkeypatch.setattr(closure, "parent_snapshot", lambda: closure.ParentSnapshot((parent,), ()))
    monkeypatch.setattr(closure, "FACTORIES", (closure.LowerLayerFactory("tiny", "tiny", "factory", "tiny.md"),))
    monkeypatch.setattr(closure, "import_module", lambda *args, **kwargs: SimpleNamespace(factory=lambda spec: tuple(candidates)))
    yield parent, candidates
    closure.lower_layer_specs.cache_clear()
    closure.lower_layer_plan.cache_clear()


def test_every_body_and_every_maximal_root_reaches_the_original_kernel(tiny_inventory):
    result = closure.assemble_lower_layer_proof_bundle(report=lambda message: None)
    assert result.receipt.kernel_calls == result.receipt.node_count == 4
    assert result.receipt.dependency_edges == 3
    assert isinstance(result.target, And)
    assert result.bundle.nodes[-1].dependencies == (1, 2)
    assert result.origins == (("base", "parent_script", None), ("left", "new_script", None), ("right", "new_script", None))


@pytest.mark.parametrize("mutation", ("root", "target", "edge", "packaging", "body", "inventory"))
def test_changed_targets_edges_bodies_and_synthetic_roots_are_rejected(tiny_inventory, mutation):
    result = closure.assemble_lower_layer_proof_bundle(report=lambda message: None)
    nodes = list(result.bundle.nodes)
    if mutation == "root":
        bundle = replace(result.bundle, root=0)
    else:
        if mutation == "target":
            nodes[1] = replace(nodes[1], target=Bot())
        elif mutation == "edge":
            nodes[1] = replace(nodes[1], dependencies=())
        elif mutation == "packaging":
            nodes[-1] = replace(nodes[-1], body=Hyp(0))
        elif mutation == "body":
            nodes[0] = replace(nodes[0], body=Hyp(0))
        else:
            nodes.pop(1)
        bundle = replace(result.bundle, nodes=tuple(nodes))
    with pytest.raises((closure.LowerLayerError, ProofBundleError)):
        closure.check_lower_layer_proof_bundle(bundle, result.target)


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "forward", "duplicate_edge", "implicit", "empty"))
def test_specification_changes_cannot_hide_a_missing_proof(tiny_inventory, mutation):
    parent, rows = tiny_inventory
    if mutation == "duplicate":
        rows[0] = replace(rows[0], name=parent.name)
    elif mutation == "missing":
        rows[0] = replace(rows[0], dependencies=("nonexistent",))
    elif mutation == "forward":
        rows[0] = replace(rows[0], dependencies=("right",))
    elif mutation == "duplicate_edge":
        rows[0] = replace(rows[0], dependencies=("base", "base"))
    elif mutation == "implicit":
        rows[0] = replace(rows[0], script=("use unverified",))
    else:
        rows[0] = replace(rows[0], script=())
    with pytest.raises(closure.LowerLayerError):
        closure.lower_layer_plan()


@pytest.mark.parametrize("mutation", ("digest", "bytes", "target", "forged_body", "none"))
def test_historical_reuse_is_only_an_optimization_not_authority(tiny_inventory, monkeypatch, tmp_path, mutation):
    parent, _ = tiny_inventory
    target = _closed_formula(parent.statement)
    body = closure._reconstruct_body(parent, {parent.name: parent})
    node = BundleNode(0, target, (), body)
    if mutation == "target":
        node = replace(node, target=Bot())
    elif mutation == "forged_body":
        node = replace(node, body=Hyp(0))
    provider = ProofBundle((node,), 0)
    payload = encode_proof_bundle(provider, provider.nodes[-1].target).encode()
    path = tmp_path / "provider.json"
    path.write_bytes(payload)
    document = closure.ParentDocument(path.name, len(payload) + (mutation == "bytes"),
                                      "0" * 64 if mutation == "digest" else sha256(payload).hexdigest())
    monkeypatch.setattr(closure, "ROOT", tmp_path)
    monkeypatch.setattr(closure, "parent_snapshot", lambda: closure.ParentSnapshot((parent,), (document,)))
    if mutation in {"digest", "bytes", "forged_body"}:
        with pytest.raises((closure.LowerLayerError, ProofBundleError)):
            closure.assemble_lower_layer_proof_bundle(report=lambda message: None)
    else:
        result = closure.assemble_lower_layer_proof_bundle(report=lambda message: None)
        assert result.receipt.kernel_calls == 4
        assert result.origins[0][1] == ("parent_script" if mutation == "target" else path.name)


@pytest.mark.parametrize("dependency_ids", ((0, 1), (1, 0), (0,)))
def test_body_reuse_matches_every_ordered_dependency_target(tiny_inventory, monkeypatch, tmp_path, dependency_ids):
    a = TheoremSpec("first", "0 = 0", (), ("refl",), "First premise.")
    b = TheoremSpec("second", "1 = 1", (), ("refl",), "Different second premise.")
    parent = TheoremSpec("base", "2 = 2", (a.name, b.name), ("refl",), "Distinct target.")
    tiny_inventory[1][0] = replace(tiny_inventory[1][0], statement=parent.statement)
    table = {row.name: row for row in (a, b, parent)}
    nodes = tuple(BundleNode(index, _closed_formula(row.statement), dependencies,
                             closure._reconstruct_body(row, table))
                  for index, (row, dependencies) in enumerate(((a, ()), (b, ()), (parent, dependency_ids))))
    package_target, package_body = closure._packaging_root(tuple(node.target for node in nodes))
    provider = ProofBundle(nodes + (BundleNode(3, package_target, (0, 1, 2), package_body),), 3)
    payload = encode_proof_bundle(provider, package_target).encode()
    path = tmp_path / "provider.json"
    path.write_bytes(payload)
    document = closure.ParentDocument(path.name, len(payload), sha256(payload).hexdigest())
    monkeypatch.setattr(closure, "ROOT", tmp_path)
    monkeypatch.setattr(closure, "parent_snapshot", lambda: closure.ParentSnapshot((a, b, parent), (document,)))
    result = closure.assemble_lower_layer_proof_bundle(report=lambda message: None)
    assert result.receipt.kernel_calls == 6
    assert result.origins[2][1] == (path.name if dependency_ids == (0, 1) else "parent_script")


def test_empty_packaging_is_not_a_theorem():
    with pytest.raises(closure.LowerLayerError, match="empty"):
        closure._packaging_root(())


def test_unsealed_metadata_cannot_trigger_checked_use_or_a_file_read(monkeypatch):
    monkeypatch.setattr(closure, "EXPECTED_LOWER_LAYER_BUNDLE_BYTES", 0)
    monkeypatch.setattr(Path, "read_bytes", lambda _path: pytest.fail("unsealed checked use read a file"))
    with pytest.raises(closure.LowerLayerError, match="not sealed"):
        closure.checked_lower_layer_proof_bundle()


def test_unused_parent_provider_byte_mutation_still_rejects(tiny_inventory,monkeypatch,tmp_path):
    parent,_=tiny_inventory
    path=tmp_path/"unused-provider.json"
    path.write_bytes(b"changed historical bytes")
    document=closure.ParentDocument(path.name,1,"0"*64)
    monkeypatch.setattr(closure,"ROOT",tmp_path)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),(document,)))
    with pytest.raises(closure.LowerLayerError,match="historical proof bytes changed"):
        closure.validate_parent_provider_bytes()


def test_final_sealed_bundle_has_every_real_body_and_exact_resource_receipt():
    bundle, receipt = closure.checked_lower_layer_proof_bundle()
    plan = closure.lower_layer_plan()
    assert len(plan.frontier_names) == closure.EXPECTED_LOWER_LAYER_FRONTIER_COUNT == 204
    assert len(plan.rows) == closure.EXPECTED_LOWER_LAYER_THEOREM_COUNT == 861
    assert len(plan.root_names) == closure.EXPECTED_LOWER_LAYER_ROOT_COUNT == 36
    assert receipt.kernel_calls == receipt.node_count == closure.EXPECTED_LOWER_LAYER_BUNDLE_NODE_COUNT == 862
    assert receipt.dependency_edges == closure.EXPECTED_LOWER_LAYER_BUNDLE_EDGE_COUNT == 3090
    assert receipt.total_body_nodes == closure.EXPECTED_LOWER_LAYER_BUNDLE_BODY_PROOF_NODES == 230464
    assert bundle.root == closure.EXPECTED_LOWER_LAYER_THEOREM_COUNT == 861
    artifact = ROOT / "research/arithmetic-library/artifacts" / closure.LOWER_LAYER_ARTIFACT_FILENAME
    assert artifact.stat().st_size == closure.EXPECTED_LOWER_LAYER_BUNDLE_BYTES == 18977050
    assert sha256(artifact.read_bytes()).hexdigest() == closure.EXPECTED_LOWER_LAYER_BUNDLE_SHA256 == "e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1"
    assert plan.ordered_names_sha256 == closure.EXPECTED_LOWER_LAYER_ORDERED_NAMES_SHA256 == "d9900807b562cb3f6b5e40b398b4cc26e4ad0714dc5e7cc00263ada62ee73a15"
    assert all(bundle.nodes[row.node_id].target == _closed_formula(closure._table(())[row.name].statement) for row in plan.rows)
