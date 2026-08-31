"""Independent exact-inventory and hostile-proof tests for the v33 provider.

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

import resource
import signal
import time

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

from peano_lab.kernel import checker as kernel_checker
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import campaign_research_v33_closure as c
from peano_lab.library.proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, ProofBundleError, decode_proof_bundle,
)
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SMALL = "polynomial-euclidean-division"
EXPECTED_INVENTORY = (("polynomial-euclidean-division", 121, 377, 1071, 30527),)
TRUSTED_SOURCE_SHA256 = {
    "peano-lab/py/peano_lab/library/editions_v32.py": "69707c34aed369163cc0cce95db7e6078302fe639df75210176e9b53ab719785",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v32.py": "81003d179548d50417ef093e1e7c6fc1006ec72ff06f39d1e0a47e56335172c6",
    "peano-lab/py/peano_lab/library/campaign_research_v32_closure.py": "cdbc803669fc35c0d8b91e06f5f79d1470ffc2355e041fc12c205ec21dfb3ea0",
    "peano-lab/py/peano_lab/library/editions_v31.py": "24fedcd8a492578f9a1e32bdd984693bd8e27216105000f719188a3a38200870",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v31.py": "7106c15b7196ca70d4bd62a4708696bd38e9b4eee07a127844c2d8398cd6e81b",
    "peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py": "9aec583406e6b890fdd626cb60ecf8de4271581e20e86e1aa8499a4b1701dab3",
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
CANONICAL_SOURCE_PINS = (
    ("prime_field_polynomial_convolution_triangular_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_convolution_triangular_candidate.py", 8, 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("prime_field_polynomial_representation_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_representation_candidate.py", 30, 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("prime_field_polynomial_division_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_division_candidate.py", 25, 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("prime_field_polynomial_distributivity_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_distributivity_candidate.py", 18, 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("prime_field_polynomial_division_uniqueness_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_division_uniqueness_candidate.py", 9, 23258, "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15"),
    ("prime_field_polynomial_convolution_padding_candidate", "research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_convolution_padding_candidate.py", 23, 39740, "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007"),
    ("prime_field_polynomial_equivalence_candidate", "research/arithmetic-library/working/prime-field-equivalence-v1/prime_field_polynomial_equivalence_candidate.py", 5, 10469, "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373"),
    ("prime_field_polynomial_convolution_congruence_candidate", "research/arithmetic-library/working/prime-field-equivalence-v1/prime_field_polynomial_convolution_congruence_candidate.py", 3, 8183, "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70"),
)


def _parent():
    # Deliberately lazy: pure source/registration checks need no Alpha import.
    from peano_lab.library import editions_v32
    return editions_v32


@pytest.fixture(scope="module")
def small_syntax():
    family = c.research_family(SMALL)
    payload = c.read_research_bundle_bytes(SMALL, ROOT / family.artifact)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    return bundle, target


def test_exact_one_family_and_eight_canonical_factories():
    assert tuple((f.slug, f.count, f.node_count, f.bundle_edges, f.body_nodes)
                 for f in c.FAMILIES) == EXPECTED_INVENTORY
    assert len(c.FACTORIES) == 8 and len(c.FAMILY_BY_NAME) == 121
    assert sum(f.edge_count for f in c.FAMILIES) == 461
    assert sum(f.command_count for f in c.FAMILIES) == 9068
    assert c._metadata_digest() == "ea9a09d907d3010a8f32e3efc54c1d2c171b074a87a140953c06f626071fdce6"


def test_canonical_registration_matches_frozen_sources_without_loading_old_aliases():
    family = c.FAMILIES[0]
    assert family.specs_sha256 == "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
    assert (family.artifact_bytes, family.artifact_sha256) == (
        2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf")
    assert family.research_checkpoint_slug == "working-polynomial-equivalence121"
    assert family.modules == tuple(row[0] for row in CANONICAL_SOURCE_PINS)
    for module, original, count, size, digest in CANONICAL_SOURCE_PINS:
        owner = c.FACTORY_BY_MODULE[module]
        old = (ROOT / original).read_bytes()
        canonical = (ROOT / owner.source).read_bytes()
        assert old == canonical and (len(old), sha256(old).hexdigest()) == (size, digest)
        assert owner.count == count and owner.source_bytes == size and owner.source_sha256 == digest
        assert owner.factory == "make_" + module + "_theorems"
        assert owner.test == "peano-lab/py/tests/test_campaign_research_v33_closure.py"
    rows = c.research_specs()
    assert tuple(row.name for row in rows) == family.owned_names and len(rows) == 121
    assert c._specs_digest(rows) == family.specs_sha256
    assert not any(name in sys.modules for name in (
        "working_equivalence_support", "working_euclidean_support", "working_euclidean_extension_support"))


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
    plan = c.research_plan(family.slug, parent_specs=_parent().ALPHA_CHECKED_SPECS)
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


def test_actual_artifact_is_the_exact_preserved_121_working_bytes():
    family = c.FAMILIES[0]
    raw = c.read_research_bundle_bytes(family.slug, ROOT / family.artifact)
    archived = (ROOT / "research/arithmetic-library/working/prime-field-equivalence-v1/artifacts/working-equivalence-proof-bundle-v1.json").read_bytes()
    assert raw == archived
    assert len(raw) == 2449379
    assert sha256(raw).hexdigest() == "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf"


@pytest.mark.parametrize("slug", ("", "missing", "POLYNOMIAL-EUCLIDEAN-DIVISION", "../polynomial-euclidean-division", None, 1, True, (SMALL,)))
def test_unknown_or_malformed_family_is_rejected_before_files(monkeypatch, slug):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid selection opened a file"))
    with pytest.raises(c.ResearchClosureError):
        c.research_family(slug)


@pytest.mark.parametrize("mutation", ("count", "order", "statement", "summary", "script", "name", "dependency", "list", "object", "duplicate"))
def test_every_supplied_parent_field_is_exact(mutation):
    rows = _parent().ALPHA_CHECKED_SPECS
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
    with pytest.raises(c.ResearchClosureError):
        c._parent_specs(altered)


@pytest.mark.parametrize("field,value", (
    ("artifact_bytes", 0), ("artifact_bytes", True), ("artifact_bytes", 64_000_001),
    ("artifact_sha256", ""), ("artifact_sha256", "0" * 64), ("artifact", "../escape.json"),
    ("count", 0), ("specs_sha256", "0" * 64), ("names_sha256", "0" * 64),
    ("node_count", 0), ("dependency_edges", 0), ("body_nodes", 0),
    ("owned_names", ()), ("principal_roots", ()), ("root_names", ()),
    ("modules", ()), ("research_checkpoint_slug", "not-the-old-slug"), ("edge_count", 1),
    ("complete_non_alpha_specs_sha256", "0" * 64),
))
def test_every_family_metadata_change_fails_before_source_or_proof_use(monkeypatch, field, value):
    changed = (replace(c.FAMILIES[0], **{field: value}),) + c.FAMILIES[1:]
    monkeypatch.setattr(c, "FAMILIES", changed)
    monkeypatch.setattr(c, "RESEARCH_FAMILIES", changed)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("bad metadata opened a source"))
    with pytest.raises(c.ResearchClosureError):
        c.validate_research_metadata()


@pytest.mark.parametrize("field,value", (
    ("module", "../escape"), ("factory", "other"), ("rfc", "../bad-rfc-v1.md"),
    ("source_bytes", 0), ("source_bytes", 2 * 1024 * 1024 + 1),
    ("source_sha256", "0" * 64), ("specs_sha256", "0" * 64), ("count", 1),
    ("test_filename", "../escape.py"), ("test_filename", "test_invented.py"),
))
def test_every_factory_metadata_change_is_rejected(monkeypatch, field, value):
    monkeypatch.setattr(c, "FACTORIES", (replace(c.FACTORIES[0], **{field: value}),) + c.FACTORIES[1:])
    with pytest.raises(c.ResearchClosureError):
        c.validate_research_metadata()


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
    c.clear_research_metadata_cache()
    def poisoned(_spec):
        return changed
    poisoned.__module__ = module.__name__
    monkeypatch.setattr(module, owner.factory, poisoned)
    try:
        with pytest.raises(c.ResearchClosureError):
            c.research_specs()
    finally:
        c.clear_research_metadata_cache()


@pytest.mark.parametrize("mutation", ("missing", "directory", "symlink", "truncate", "append", "same_size_poison"))
def test_invalid_proof_file_fails_before_decoding(tmp_path, mutation):
    family = c.research_family(SMALL)
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
    with pytest.raises(c.ResearchClosureError):
        c.read_research_bundle_bytes(SMALL, path)


def test_bounded_reader_never_calls_unbounded_read(monkeypatch):
    family = c.research_family(SMALL)
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
    raw = c.read_research_bundle_bytes(SMALL, ROOT / family.artifact)
    assert calls == [family.artifact_bytes + 1] and len(raw) == family.artifact_bytes


@pytest.mark.parametrize("size", (0, -1, True, 64_000_001, 1.0))
def test_invalid_size_never_opens_file(monkeypatch, size):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid bound opened a file"))
    with pytest.raises(c.ResearchClosureError):
        c._read_pinned(Path("missing"), size, "a" * 64, maximum=64_000_000)


def test_frozen_metadata_and_explicit_parent_need_no_catalog_or_artifact(monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as old
    monkeypatch.setattr(old, "parent_snapshot", lambda: pytest.fail("runtime read a catalogue"))
    monkeypatch.setattr(c, "read_research_bundle_bytes", lambda *_a, **_k: pytest.fail("plan loaded proof bytes"))
    plan = c.research_plan(SMALL, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == 376 and len(plan.owned_names) == 121


def test_real_complete_bundle_checks_every_actual_body_in_original_empty_context(small_syntax, monkeypatch):
    bundle, target = small_syntax
    original = kernel_checker.check
    calls = []
    def observed(context, proof, conclusion):
        calls.append((context, proof, conclusion))
        return original(context, proof, conclusion)
    monkeypatch.setattr(kernel_checker, "check", observed)
    receipt = c.check_research_proof_bundle(SMALL, bundle, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    assert receipt.kernel_calls == receipt.node_count == len(calls) == 377
    assert receipt.total_body_nodes == 30527 and receipt.dependency_edges == 1071
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
    with pytest.raises(c.ResearchClosureError):
        c.check_research_proof_bundle(SMALL, changed, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("which", ("inherited", "owned", "open_own", "DNE"))
def test_false_or_open_bodies_reach_and_fail_original_kernel(small_syntax, which):
    bundle, target = small_syntax
    plan = c.research_plan(SMALL, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    position = next(row.node_id for row in plan.rows if row.is_owned) if which != "inherited" else 0
    body = Hyp(0)
    if which == "DNE":
        from peano_lab.kernel.proofs import DNE
        body = DNE(Bot())
    nodes = list(bundle.nodes)
    nodes[position] = replace(nodes[position], body=body)
    with pytest.raises((ProofBundleError, c.ResearchClosureError)):
        c.check_research_proof_bundle(SMALL, replace(bundle, nodes=tuple(nodes)), target,
                                            parent_specs=_parent().ALPHA_CHECKED_SPECS)


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
    with pytest.raises(c.ResearchClosureError):
        c.check_research_proof_bundle(SMALL, bundle, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)


def test_original_resource_limits_are_used_without_a_provider_override():
    from peano_lab.library import proof_bundle
    from peano_lab.library import layered_replay
    from peano_lab.library import editions_v33
    assert c.DEFAULT_BUNDLE_LIMITS is proof_bundle.DEFAULT_BUNDLE_LIMITS
    assert editions_v33.DEFAULT_LAYERED_REPLAY_LIMITS is layered_replay.DEFAULT_LAYERED_REPLAY_LIMITS
    assert DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64_000_000
    assert DEFAULT_BUNDLE_LIMITS.max_nodes == 4096
    assert DEFAULT_BUNDLE_LIMITS.max_total_body_nodes == 5_000_000
    assert c.MAX_SOURCE_BYTES == 2 * 1024 * 1024


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda item: item.module)
def test_even_an_unused_source_pin_is_checked_before_cached_specs(monkeypatch, owner):
    original = c._read_pinned
    calls = []
    def reject_one(path, *args, **kwargs):
        calls.append(path)
        if path.name == owner.module + ".py":
            raise c.ResearchClosureError("intentional changed unused source")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(c, "_read_pinned", reject_one)
    with pytest.raises(c.ResearchClosureError, match="changed unused source"):
        c.research_specs()
    assert any(path.name == owner.module + ".py" for path in calls)


def _main(argv=None):
    """Run only the selected actual tests in one original bounded window."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("a case window must be positive and bounded")

    class Window:
        def __init__(self):
            self.selected = []
            self.passed = set()
            self.bad = []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested case window is unavailable")
            if not chosen:
                raise ValueError("an empty bounded case selection is not a pass")
            selected = {item.nodeid for item in chosen}
            rejected = [item for item in items if item.nodeid not in selected]
            config.hook.pytest_deselected(items=rejected)
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS ceiling was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
                      "collect_only": args.collect_only, "pytest_exit_code": int(status),
                      "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED,
                      "peak_rss_bytes": peak, "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                      "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())

