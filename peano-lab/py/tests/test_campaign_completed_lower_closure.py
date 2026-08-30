"""Independent exact-inventory and hostile-proof tests for the v31 providers.

Saved checkpoints are authoring references only. The positive proof test below
checks actual frozen bytes with the original HA kernel; no mocked acceptance.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import sys

import pytest

from peano_lab.kernel import checker as kernel_checker
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import campaign_completed_lower_closure as c
from peano_lab.library import editions_v30 as parent
from peano_lab.library.proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, ProofBundleError, decode_proof_bundle,
)
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SMALL = "dirichlet-signed-units"
EXPECTED_INVENTORY = (
    ("euler-units", 32, 210, 568, 12452),
    ("prime-fields", 87, 228, 611, 12012),
    ("mobius-values", 21, 237, 675, 15134),
    ("signed-sums", 30, 214, 571, 13724),
    ("divisor-sums", 37, 315, 875, 20685),
    ("signed-weighted-sums", 40, 227, 584, 13692),
    ("prime-field-polynomials", 49, 202, 519, 11889),
    ("divisor-involutions", 12, 140, 355, 7711),
    ("mobius-divisor-cancellation", 28, 377, 1081, 27012),
    ("rectangular-sums", 32, 217, 551, 12534),
    ("polynomial-products", 53, 210, 503, 11604),
    ("finite-support", 8, 170, 397, 8697),
    ("dirichlet-convolution", 40, 270, 712, 18180),
    ("dirichlet-fubini", 32, 347, 971, 25115),
    ("dirichlet-units", 25, 282, 760, 18734),
    ("mobius-inversion", 8, 531, 1579, 40028),
    ("dirichlet-signed-units", 9, 71, 146, 4704),
    ("dirichlet-triangular", 10, 219, 541, 12776),
    ("dirichlet-inverses", 21, 401, 1150, 29441),
)
TRUSTED_SOURCE_SHA256 = {
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/library/layered_replay.py": "7c8b14b95ab76fe10f265a10271fd58f779fab3b7524c8f9002884b753b2badf",
    "peano-lab/py/peano_lab/library/formula_dag.py": "3dfd0ad9ec3270cb2cd40948b62f223ba9e5f7284152c823405d8002b7a1a45f",
    "peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py": "68af15379776c0cb36125c1d2f24e7c87b98880a7caad24725453937b864ac3e",
    "peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py": "d7b31c8511d4439e1a2075cba718b2cba0fd7ea42a07c2ffb41d55dd7e75542c",
    "peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py": "e4d6f74feabf16ac342c9bfb875a39d060f5b97039866ae3a0a5fea99db84477",
    "peano-lab/py/peano_lab/library/editions_v30.py": "88499fde8ae5b19be5fea2d2d88d3ab56c0a27901abdbf6f005c16a0c1c1328f",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v30.py": "ca61a5efa17c8624c29ad3388c97743947a81f648e7f1aeeef848833cd484bac",
}
REGISTRIES = (
    "constructive_bottom_layer_checkpoints", "constructive_lower_tier_checkpoints",
    "constructive_lower_continuation_checkpoints", "constructive_dirichlet_checkpoints",
    "constructive_dirichlet_inverse_checkpoints",
)


@lru_cache(maxsize=1)
def registered():
    directory = str(ROOT / "scripts")
    if directory not in sys.path:
        sys.path.insert(0, directory)
    return {item.slug: item for module in REGISTRIES
            for item in import_module(module).CHECKPOINTS}


@pytest.fixture(scope="module")
def small_syntax():
    family = c.completed_lower_family(SMALL)
    payload = c.read_completed_lower_bundle_bytes(SMALL, ROOT / family.artifact)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    return bundle, target


def test_exact_nineteen_families_and_five_completed_generations():
    assert tuple((f.slug, f.count, f.node_count, f.bundle_edges, f.body_nodes)
                 for f in c.FAMILIES) == EXPECTED_INVENTORY
    assert len(c.FACTORIES) == 35 and len(c.FAMILY_BY_NAME) == 574
    assert tuple(sum(f.count for f in c.FAMILIES if f.generation == n)
                 for n in (170, 126, 125, 113, 40)) == (170, 126, 125, 113, 40)
    assert sum(f.edge_count for f in c.FAMILIES) == 1660
    assert sum(f.command_count for f in c.FAMILIES) == 26004
    assert c._metadata_digest() == "07c04a017f2a19e2250b6b9a013b247cc94586ce90ab818bc75a7e20e1ea7737"


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_independent_frozen_registry_pins_and_ownership(family):
    old = registered()[family.slug]
    assert (old.frontier_count, old.frontier_specs_sha256, old.artifact,
            old.artifact_bytes, old.artifact_sha256, old.principal_roots) == (
        family.count, family.specs_sha256, family.artifact,
        family.artifact_bytes, family.artifact_sha256, family.principal_roots,
    )
    assert family.modules == tuple(pin.module for pin in old.modules)
    for pin in old.modules:
        owner = c.FACTORY_BY_MODULE[pin.module]
        assert (owner.factory, owner.source, owner.source_sha256) == (pin.factory, pin.path, pin.sha256)
    rows = tuple(row for row in c.completed_lower_specs() if row.name in family.owned_names)
    assert tuple(row.name for row in rows) == family.owned_names
    assert c._specs_digest(rows) == old.frontier_specs_sha256


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda f: f.module)
def test_every_mathematical_source_is_byte_exact_and_bounded(owner):
    path = ROOT / owner.source
    raw = c._read_pinned(path, owner.source_bytes, owner.source_sha256, maximum=c.MAX_SOURCE_BYTES)
    assert sha256(raw).hexdigest() == owner.source_sha256
    assert len(raw) == owner.source_bytes <= 2 * 1024 * 1024


@pytest.mark.parametrize("path,digest", TRUSTED_SOURCE_SHA256.items())
def test_original_kernel_limits_and_historical_providers_unchanged(path, digest):
    assert sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_actual_complete_cone_has_no_missing_or_recounted_support(family):
    plan = c.completed_lower_plan(family.slug, parent_specs=parent.ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == family.theorem_count
    assert plan.owned_names == family.owned_names
    assert tuple(row.name for row in plan.rows if row.is_owned) == family.owned_names
    assert len(plan.positions) == len(plan.rows)
    assert plan.root_names == family.root_names
    assert set(plan.root_names) <= set(plan.owned_names)
    assert plan.dependency_edge_count == family.dependency_edges
    assert plan.ordered_names_sha256 == family.ordered_cone_names_sha256
    assert plan.frontier_specs_sha256 == family.complete_non_alpha_specs_sha256
    seen = set()
    for row, spec in zip(plan.rows, plan.specs, strict=True):
        assert row.node_id == len(seen)
        assert row.name == spec.name and row.dependencies == spec.dependencies
        assert set(row.dependencies) <= seen
        assert row.statement_sha256 == sha256(spec.statement.encode()).hexdigest()
        assert row.is_owned == (row.name in family.owned_names)
        assert row.campaign == (c.FAMILY_BY_NAME[row.name].slug if row.name in c.FAMILY_BY_NAME else None)
        seen.add(row.name)
    pending, reachable = list(plan.root_names), set()
    specs = {row.name: row for row in plan.specs}
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(specs[name].dependencies)
    assert reachable == seen
    with pytest.raises(TypeError):
        plan.positions["invented"] = 0


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_each_actual_artifact_has_its_independent_frozen_bytes(family):
    raw = c.read_completed_lower_bundle_bytes(family.slug, ROOT / family.artifact)
    old = registered()[family.slug]
    assert len(raw) == old.artifact_bytes
    assert sha256(raw).hexdigest() == old.artifact_sha256


@pytest.mark.parametrize("slug", ("", "missing", "DIRICHLET-SIGNED-UNITS", "../dirichlet-signed-units", None, 1, True, (SMALL,)))
def test_unknown_or_malformed_family_is_rejected_before_files(monkeypatch, slug):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid selection opened a file"))
    with pytest.raises(c.CompletedLowerClosureError):
        c.completed_lower_family(slug)


@pytest.mark.parametrize("mutation", ("count", "order", "statement", "summary", "script", "name", "dependency", "list", "object", "duplicate"))
def test_every_supplied_parent_field_is_exact(mutation):
    rows = parent.ALPHA_CHECKED_SPECS
    if mutation == "count":
        altered = rows[:-1]
    elif mutation == "order":
        altered = rows[1:] + rows[:1]
    elif mutation == "list":
        altered = list(rows)
    elif mutation == "object":
        altered = (object(),) + rows[1:]
    elif mutation == "duplicate":
        altered = rows[:1] + rows[:1] + rows[2:]
    else:
        changes = {"statement": "0 = 1", "summary": "altered", "script": ("refl",),
                   "name": "altered", "dependency": ("invented",)}
        key = "dependencies" if mutation == "dependency" else mutation
        altered = (replace(rows[0], **{key: changes[mutation]}),) + rows[1:]
    with pytest.raises(c.CompletedLowerClosureError):
        c._parent_specs(altered)


@pytest.mark.parametrize("field,value", (
    ("artifact_bytes", 0), ("artifact_bytes", True), ("artifact_bytes", 64_000_001),
    ("artifact_sha256", ""), ("artifact_sha256", "0" * 64), ("artifact", "../escape.json"),
    ("count", 0), ("specs_sha256", "0" * 64), ("names_sha256", "0" * 64),
    ("node_count", 0), ("dependency_edges", 0), ("body_nodes", 0),
    ("owned_names", ()), ("principal_roots", ()), ("root_names", ()),
    ("modules", ()), ("generation", 0), ("edge_count", 1),
    ("complete_non_alpha_specs_sha256", "0" * 64),
))
def test_every_family_metadata_change_fails_before_source_or_proof_use(monkeypatch, field, value):
    changed = (replace(c.FAMILIES[0], **{field: value}),) + c.FAMILIES[1:]
    monkeypatch.setattr(c, "FAMILIES", changed)
    monkeypatch.setattr(c, "COMPLETED_LOWER_FAMILIES", changed)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("bad metadata opened a source"))
    with pytest.raises(c.CompletedLowerClosureError):
        c.validate_completed_lower_metadata()


@pytest.mark.parametrize("field,value", (
    ("module", "../escape"), ("factory", "other"), ("rfc", "../bad-rfc-v1.md"),
    ("source_bytes", 0), ("source_bytes", 2 * 1024 * 1024 + 1),
    ("source_sha256", "0" * 64), ("specs_sha256", "0" * 64), ("count", 1),
))
def test_every_factory_metadata_change_is_rejected(monkeypatch, field, value):
    monkeypatch.setattr(c, "FACTORIES", (replace(c.FACTORIES[0], **{field: value}),) + c.FACTORIES[1:])
    with pytest.raises(c.CompletedLowerClosureError):
        c.validate_completed_lower_metadata()


@pytest.mark.parametrize("mutation", ("count", "name", "statement", "dependencies", "script", "summary", "order", "type"))
def test_poisoned_factory_cannot_reuse_old_source_hash_as_authority(monkeypatch, mutation):
    owner = c.FACTORIES[0]
    module = import_module("peano_lab.library." + owner.module)
    original = getattr(module, owner.factory)
    rows = tuple(original(__import__("peano_lab.library.theorems", fromlist=["TheoremSpec"]).TheoremSpec))
    if mutation == "count":
        changed = rows[:-1]
    elif mutation == "order":
        changed = tuple(reversed(rows))
    elif mutation == "type":
        changed = (object(),) + rows[1:]
    else:
        values = {"name": "invented", "statement": "0 = 1", "dependencies": ("invented",),
                  "script": ("refl",), "summary": "altered"}
        changed = (replace(rows[0], **{mutation: values[mutation]}),) + rows[1:]
    c.clear_completed_lower_metadata_cache()
    monkeypatch.setattr(module, owner.factory, lambda _spec: changed)
    try:
        with pytest.raises(c.CompletedLowerClosureError):
            c.completed_lower_specs()
    finally:
        c.clear_completed_lower_metadata_cache()


@pytest.mark.parametrize("mutation", ("missing", "directory", "symlink", "truncate", "append", "same_size_poison"))
def test_invalid_proof_file_fails_before_decoding(tmp_path, mutation):
    family = c.completed_lower_family(SMALL)
    raw = (ROOT / family.artifact).read_bytes()
    path = tmp_path / "proof.json"
    if mutation == "directory":
        path.mkdir()
    elif mutation == "symlink":
        path.symlink_to(ROOT / family.artifact)
    elif mutation == "truncate":
        path.write_bytes(raw[:-1])
    elif mutation == "append":
        path.write_bytes(raw + b" ")
    elif mutation == "same_size_poison":
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    with pytest.raises(c.CompletedLowerClosureError):
        c.read_completed_lower_bundle_bytes(SMALL, path)


def test_bounded_reader_never_calls_unbounded_read(monkeypatch):
    family = c.completed_lower_family(SMALL)
    original = Path.open
    calls = []
    class Reader:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def read(self, size=-1):
            calls.append(size)
            assert size == family.artifact_bytes + 1
            return self.handle.read(size)
    monkeypatch.setattr(Path, "open", lambda path, *args, **kwargs: Reader(original(path, *args, **kwargs)))
    raw = c.read_completed_lower_bundle_bytes(SMALL, ROOT / family.artifact)
    assert calls == [family.artifact_bytes + 1] and len(raw) == family.artifact_bytes


@pytest.mark.parametrize("size", (0, -1, True, 64_000_001, 1.0))
def test_invalid_size_never_opens_file(monkeypatch, size):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid bound opened a file"))
    with pytest.raises(c.CompletedLowerClosureError):
        c._read_pinned(Path("missing"), size, "a" * 64, maximum=64_000_000)


def test_frozen_metadata_and_explicit_parent_need_no_catalog_or_artifact(monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as old
    monkeypatch.setattr(old, "parent_snapshot", lambda: pytest.fail("runtime read a catalogue"))
    monkeypatch.setattr(c, "read_completed_lower_bundle_bytes", lambda *_a, **_k: pytest.fail("plan loaded proof bytes"))
    plan = c.completed_lower_plan(SMALL, parent_specs=parent.ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == 70 and len(plan.owned_names) == 9


def test_real_small_bundle_checks_every_actual_body_in_original_empty_context(small_syntax, monkeypatch):
    bundle, target = small_syntax
    original = kernel_checker.check
    calls = []
    def observed(context, proof, conclusion):
        calls.append((context, proof, conclusion))
        return original(context, proof, conclusion)
    monkeypatch.setattr(kernel_checker, "check", observed)
    receipt = c.check_completed_lower_proof_bundle(SMALL, bundle, target, parent_specs=parent.ALPHA_CHECKED_SPECS)
    assert receipt.kernel_calls == receipt.node_count == len(calls) == 71
    assert receipt.total_body_nodes == 4704 and receipt.dependency_edges == 146
    assert all(context == () for context, _, _ in calls)
    assert all(proof is node.body for (_, proof, _), node in zip(calls, bundle.nodes, strict=True))


@pytest.mark.parametrize("mutation", (
    "missing_node", "duplicate_node", "reverse_nodes", "root", "boolean_root",
    "target", "node_target", "node_id", "boolean_node_id", "remove_dependency",
    "poison_dependency", "reverse_dependencies", "boolean_dependency",
    "packaging_target", "packaging_body", "packaging_dependencies",
    "tuple_type", "node_type",
))
def test_exact_graph_target_order_and_packaging_fail_before_kernel(small_syntax, monkeypatch, mutation):
    bundle, target = small_syntax
    nodes = list(bundle.nodes)
    selected = next(i for i, node in enumerate(nodes[:-1]) if len(node.dependencies) >= 2)
    if mutation == "missing_node":
        changed = replace(bundle, nodes=tuple(nodes[:-1]))
    elif mutation == "duplicate_node":
        changed = replace(bundle, nodes=tuple(nodes) + (nodes[0],))
    elif mutation == "reverse_nodes":
        changed = replace(bundle, nodes=tuple(reversed(nodes)))
    elif mutation in {"root", "boolean_root"}:
        changed = replace(bundle, root=0 if mutation == "root" else True)
    elif mutation == "target":
        changed, target = bundle, Bot()
    elif mutation == "tuple_type":
        changed = replace(bundle, nodes=nodes)
    else:
        if mutation == "node_target":
            nodes[selected] = replace(nodes[selected], target=Bot())
        elif mutation == "node_id":
            nodes[selected] = replace(nodes[selected], node_id=999)
        elif mutation == "boolean_node_id":
            nodes[0] = replace(nodes[0], node_id=False)
        elif mutation == "remove_dependency":
            nodes[selected] = replace(nodes[selected], dependencies=nodes[selected].dependencies[:-1])
        elif mutation == "poison_dependency":
            nodes[selected] = replace(nodes[selected], dependencies=(999,) + nodes[selected].dependencies[1:])
        elif mutation == "reverse_dependencies":
            nodes[selected] = replace(nodes[selected], dependencies=tuple(reversed(nodes[selected].dependencies)))
        elif mutation == "boolean_dependency":
            i = next(i for i, node in enumerate(nodes[:-1]) if 0 in node.dependencies)
            nodes[i] = replace(nodes[i], dependencies=tuple(False if d == 0 else d for d in nodes[i].dependencies))
        elif mutation == "packaging_target":
            nodes[-1] = replace(nodes[-1], target=Bot())
        elif mutation == "packaging_body":
            nodes[-1] = replace(nodes[-1], body=Hyp(0))
        elif mutation == "packaging_dependencies":
            nodes[-1] = replace(nodes[-1], dependencies=nodes[-1].dependencies[:-1])
        elif mutation == "node_type":
            nodes[0] = object()
        changed = replace(bundle, nodes=tuple(nodes))
    monkeypatch.setattr(c, "check_proof_bundle", lambda *_a, **_k: pytest.fail("bad graph reached proof checker"))
    with pytest.raises(c.CompletedLowerClosureError):
        c.check_completed_lower_proof_bundle(SMALL, changed, target, parent_specs=parent.ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("which", ("inherited", "owned", "open_own", "DNE"))
def test_false_or_open_bodies_reach_and_fail_original_kernel(small_syntax, which):
    bundle, target = small_syntax
    plan = c.completed_lower_plan(SMALL, parent_specs=parent.ALPHA_CHECKED_SPECS)
    position = next(row.node_id for row in plan.rows if row.is_owned) if which != "inherited" else 0
    body = Hyp(0)
    if which == "DNE":
        from peano_lab.kernel.proofs import DNE
        body = DNE(Bot())
    nodes = list(bundle.nodes)
    nodes[position] = replace(nodes[position], body=body)
    with pytest.raises((ProofBundleError, c.CompletedLowerClosureError)):
        c.check_completed_lower_proof_bundle(SMALL, replace(bundle, nodes=tuple(nodes)), target,
                                            parent_specs=parent.ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("field,value", (
    ("kernel_calls", 0), ("node_count", 1), ("root", 0),
    ("dependency_edges", 0), ("total_body_nodes", 0), ("topological_order", ()),
    ("target", Bot()),
))
def test_real_checker_receipt_cannot_hide_skipped_nodes_or_wrong_target(small_syntax, monkeypatch, field, value):
    bundle, target = small_syntax
    original = c.check_proof_bundle
    def corrupted_receipt(*args, **kwargs):
        actual = original(*args, **kwargs)
        return replace(actual, **{field: value})
    monkeypatch.setattr(c, "check_proof_bundle", corrupted_receipt)
    with pytest.raises(c.CompletedLowerClosureError):
        c.check_completed_lower_proof_bundle(SMALL, bundle, target, parent_specs=parent.ALPHA_CHECKED_SPECS)


def test_original_resource_limits_are_used_without_a_provider_override():
    from peano_lab.library import proof_bundle
    from peano_lab.library import layered_replay
    from peano_lab.library import editions_v31
    assert c.DEFAULT_BUNDLE_LIMITS is proof_bundle.DEFAULT_BUNDLE_LIMITS
    assert editions_v31.DEFAULT_LAYERED_REPLAY_LIMITS is layered_replay.DEFAULT_LAYERED_REPLAY_LIMITS
    assert DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64_000_000
    assert DEFAULT_BUNDLE_LIMITS.max_nodes == 4096
    assert DEFAULT_BUNDLE_LIMITS.max_total_body_nodes == 5_000_000
    assert c.MAX_SOURCE_BYTES == 2 * 1024 * 1024
