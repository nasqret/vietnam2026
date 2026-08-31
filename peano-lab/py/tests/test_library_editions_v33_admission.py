"""Artifact-free membership and real ordinary-proof v33 admission regressions."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace

import resource
import signal
import time

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library import alpha_enrollment_v33 as a
from peano_lab.library import campaign_research_v33_closure as c
from peano_lab.library import editions_v32 as parent
from peano_lab.library import editions_v33 as current
from peano_lab.library.editions_v5 import _enrollment_identity, _identity, _make_edition
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SMALL = "polynomial-euclidean-division"
PRINCIPAL = "polynomial_diagonal_left_prefix_transport"
EXPECTED_PRINCIPALS = {
    "prime_field_polynomial_division_execution_functional": "b14ad2149cd34386887dcac50cb06b7df7014500b1ab918fac7967976b6042fe",
    "prime_field_polynomial_division_execution_exists_unique": "0ac4c1f5ca519e7db039365ff2a703f8772e22e58376d4c55a3f7777e08565fc",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent": "fbefa6c478ac7028d2c60d742799660f05d010578ce4ed30b0f72f6f0af237d6",
    "prime_field_polynomial_convolution_both_left_paddings_exists": "b79ee5e0362c752f6b0189437e25cacc49e7060037adf8837f3105db832f8ffd",
    "prime_field_polynomial_equivalent_implies_left_pad": "e9b137b8b2e2d502cb4f5405a4cb90a0abcbb50de9a0df45ff51d5127761a25c",
    "prime_field_polynomial_add_equivalent_congruent": "847a60b511d446febdc15c56231f1368a7993172939945b7b99ab297cb65c4fb",
    "prime_field_polynomial_subtract_equivalent_congruent": "b073daede7886ec70b68c11665fc2f70154db2696cd613e542d1e22900e5f2a3",
    "prime_field_polynomial_convolution_equivalent_congruent": "d984fe3c378d4d4b02941d6f3a126324a2c7c26bf47f4d8ee7c37b2e55404446",
}


@pytest.fixture(scope="module")
def actual_small():
    current.set_research_bundle_source(SMALL, None)
    bundle, receipt, positions = current.checked_research_bundle(SMALL)
    assert receipt.kernel_calls == receipt.node_count == 377
    proof = current.replay(PRINCIPAL, edition="alpha")
    assert proof.spec == current.ALPHA_EDITION.by_name[PRINCIPAL].spec
    assert proof.formula == _closed_formula(proof.spec.statement)
    assert check((), proof.certificate, proof.formula)
    yield bundle, receipt, positions, proof
    current.set_research_bundle_source(SMALL, None)


def test_all_parent_entries_and_every_stable_object_are_preserved():
    assert len(parent.ALPHA_ENTRIES) == 3971
    assert current.ALPHA_ENTRIES[:3971] == parent.ALPHA_ENTRIES
    assert all(new is old for new, old in zip(current.ALPHA_ENTRIES, parent.ALPHA_ENTRIES))
    assert current.STABLE_EDITION is parent.STABLE_EDITION
    assert current.STABLE_ENTRIES is parent.STABLE_ENTRIES
    assert current.STABLE_SPECS is parent.STABLE_SPECS
    assert current.STABLE_RELEASE_ORDER is parent.STABLE_RELEASE_ORDER
    assert len(current.STABLE_SPECS) == 432
    assert a.alpha_v33_enrollment().parent_entries is parent.ALPHA_ENTRIES


def test_actual_complete_edition_has_exact_count_graph_and_identity():
    assert len(current.ALPHA_ENTRIES) == len(current.ALPHA_CHECKED_SPECS) == 4092
    assert len(current.FRONTIER_NEW_NAMES) == 121
    assert current.ALPHA_EDITION.edge_count == 13212
    assert current.ALPHA_EDITION.layer_count == 53
    assert current.ALPHA_V33_ENROLLMENT_SHA256 == "0d4101bfee06dfff5a49ee8cfaf955a2c81a43ac622623e27890d6fe541eeaa0"
    assert current.ALPHA_V33_IDENTITY_SHA256 == "9e66890600db5f787230fb5e48e18ce08026750ba4a9d3fa7b0b1e30f6e39a3d"
    assert current.ALPHA_CHECKED_SPECS == current.ALPHA_SPECS
    assert Counter(item.evidence for item in current.ALPHA_ENTRIES) == {
        current.EvidenceStatus.STABLE_CLOSED: 432, current.EvidenceStatus.ALPHA_CLOSED: 3660,
    }


def test_exact_frontier_ownership_and_every_dependency_is_earlier():
    e = a.alpha_v33_enrollment()
    assert len(e.frontier_specs) == 121
    assert sum(len(row.dependencies) for row in e.frontier_specs) == 461
    assert sum(len(row.script) for row in e.frontier_specs) == 9068
    assert Counter(e.campaign_by_name.values()) == a.EXPECTED_CAMPAIGN_COUNTS
    assert tuple(row.name for row in e.frontier_specs) == c.FRONTIER_NEW_NAMES
    assert len(set(c.FRONTIER_NEW_NAMES)) == 121
    assert c._specs_digest(e.frontier_specs) == "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
    seen = {item.spec.name for item in parent.ALPHA_ENTRIES}
    for row in e.frontier_specs:
        assert row.name not in seen and set(row.dependencies) <= seen
        assert current.ALPHA_EDITION.by_name[row.name].spec is row
        seen.add(row.name)
    assert len(seen) == 4092


@pytest.mark.parametrize("name,digest", EXPECTED_PRINCIPALS.items())
def test_every_principal_is_the_independently_pinned_exact_statement(name, digest):
    entry = current.ALPHA_EDITION.by_name[name]
    assert entry.checked_use
    assert sha256(entry.spec.statement.encode()).hexdigest() == digest
    assert a.ROOT_STATEMENT_SHA256[name] == digest


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda f: f.module)
def test_all_factory_source_test_and_rfc_provenance_is_preserved(owner):
    e = a.alpha_v33_enrollment()
    names = tuple(name for name in current.FRONTIER_NEW_NAMES if e.source_by_name[name] == owner.source)
    assert len(names) == owner.count == a.EXPECTED_FACTORY_COUNTS[owner.module]
    assert a.EXPECTED_FACTORY_SOURCE_SHA256[owner.module] == owner.source_sha256
    for name in names:
        assert e.test_by_name[name] == owner.test
        assert e.rfc_by_name[name] == "research/arithmetic-library/" + owner.rfc
        assert e.campaign_by_name[name].value == owner.campaign
        assert current.ALPHA_EDITION.by_name[name].source_module == owner.source


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_browser_paths_and_case_insensitive_lookup_are_exact(family):
    assert current.RESEARCH_ARTIFACT_FILENAMES[family.slug] == Path(family.artifact).name
    assert current.PYODIDE_RESEARCH_BUNDLE_PATHS[family.slug] == (
        "/lab/proof-artifacts/" + Path(family.artifact).name
    )
    name = family.owned_names[0]
    assert current.entry(" " + name.upper() + " ", edition=" AlPhA ") is current.ALPHA_EDITION.by_name[name]
    assert current.entry(name) is None


def test_new_rows_do_not_leak_to_stable_even_when_proof_sources_are_available():
    for name in current.FRONTIER_NEW_NAMES:
        assert current.entry(name, edition="stable") is None
    with pytest.raises(current.EditionV33ReplayError, match="unknown stable"):
        current.replay(PRINCIPAL, edition="stable")


@pytest.mark.parametrize("seed", range(8))
def test_streamed_identity_is_exact_old_serialization_including_escaping(seed):
    rng = random.Random(seed)
    samples = tuple(replace(
        rng.choice(current.ALPHA_ENTRIES), source_module='path/quote"\\line\nλ/' + str(i),
        spec=replace(rng.choice(current.ALPHA_SPECS),
                     summary="μ\tline\n" + chr(0x1c) + '"\\' + str(i)),
    ) for i in range(rng.randrange(0, 10)))
    assert current._stream_identity(current.EditionName.ALPHA, samples) == _identity(current.EditionName.ALPHA, samples)
    assert current._stream_enrollment_identity(samples) == _enrollment_identity(samples)


def test_streamed_edition_uses_identical_original_topology_and_entry_objects():
    entries = parent.ALPHA_ENTRIES[:20]
    streamed = current._make_streamed_edition(current.EditionName.ALPHA, entries)
    old = _make_edition(current.EditionName.ALPHA, entries)
    assert streamed == old and streamed.entries is entries
    assert all(streamed.by_name[name] is old.by_name[name] for name in old.by_name)


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_ALPHA_V33_COUNT", 0), ("EXPECTED_ALPHA_V33_COUNT", 4093),
    ("EXPECTED_ALPHA_V33_CHECKED_USE_COUNT", 0), ("EXPECTED_ALPHA_V33_FRONTIER_COUNT", 0),
    ("EXPECTED_ALPHA_V33_IDENTITY_SHA256", ""), ("EXPECTED_ALPHA_V33_ENROLLMENT_SHA256", "0" * 64),
))
def test_unsealed_edition_metadata_cannot_advertise_alpha_but_stable_is_lazy(monkeypatch, field, value):
    monkeypatch.setattr(current, field, value)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("metadata opened a file"))
    with pytest.raises(current.EditionV33ReplayError):
        current.require_research_seal()
    with pytest.raises(current.EditionV33ReplayError):
        current.edition("alpha")
    assert current.edition() is parent.STABLE_EDITION
    assert current.entry("zero_add") is parent.entry("zero_add")


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_RESEARCH_FAMILY_COUNT", 0),
    ("EXPECTED_RESEARCH_FACTORY_COUNT", 0),
    ("EXPECTED_RESEARCH_COUNT", 0),
    ("EXPECTED_RESEARCH_EDGE_COUNT", 0),
    ("EXPECTED_RESEARCH_COMMAND_COUNT", 0),
    ("EXPECTED_RESEARCH_NAMES_SHA256", "0" * 64),
    ("EXPECTED_RESEARCH_METADATA_SHA256", "0" * 64),
))
def test_unsealed_provider_metadata_blocks_alpha_without_loading_a_plan(monkeypatch, field, value):
    monkeypatch.setattr(c, field, value)
    monkeypatch.setattr(c, "research_plan", lambda *_a, **_k: pytest.fail("metadata loaded a plan"))
    monkeypatch.setattr(c, "read_research_bundle_bytes", lambda *_a, **_k: pytest.fail("metadata read an artifact"))
    with pytest.raises(current.EditionV33ReplayError):
        current.require_research_seal()
    assert current.edition() is parent.STABLE_EDITION


def test_seal_and_lookup_are_artifact_free_not_proof_authority(monkeypatch):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("lookup opened a file"))
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("lookup read a file"))
    monkeypatch.setattr(c, "research_plan", lambda *_a, **_k: pytest.fail("lookup loaded a plan"))
    monkeypatch.setattr(current, "_checked_research_bundle", lambda *_a: pytest.fail("lookup invoked proof provider"))
    assert current.require_research_seal() is None
    assert current.entry(PRINCIPAL, edition="alpha").spec.name == PRINCIPAL
    assert current.entry("zero_add") is parent.entry("zero_add")


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES", 0),
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256", "0" * 64),
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES", 0),
))
def test_current_alpha_preserves_parent_metadata_eligibility_without_artifact_reads(monkeypatch, field, value):
    from peano_lab.library import campaign_gaussian_factorization_closure as gaussian
    monkeypatch.setattr(gaussian, field, value)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("parent seal opened a file"))
    monkeypatch.setattr(current, "checked_research_bundle", lambda *_a: pytest.fail("parent seal loaded proof"))
    with pytest.raises(current.EditionV33ReplayError, match="parent is not sealed"):
        current.require_research_seal()
    with pytest.raises(current.EditionV33ReplayError, match="parent is not sealed"):
        current.entry(PRINCIPAL, edition="alpha")
    assert current.edition() is parent.STABLE_EDITION
    assert current.entry("zero_add") is parent.entry("zero_add")


def test_real_stable_replay_delegates_without_touching_new_providers(monkeypatch):
    current.replay.cache_clear()
    calls = []
    original = parent.replay
    def recorded(name, *, edition):
        calls.append((name, edition))
        return original(name, edition=edition)
    monkeypatch.setattr(parent, "replay", recorded)
    monkeypatch.setattr(current, "checked_research_bundle", lambda *_: pytest.fail("Stable opened new proof"))
    checked = current.replay("zero_add", edition="stable")
    assert check((), checked.certificate, checked.formula)
    assert calls == [("zero_add", current.EditionName.STABLE)]
    current.replay.cache_clear()


def test_actual_complete_bundle_and_real_ordinary_certificate(actual_small):
    bundle, receipt, positions, proof = actual_small
    assert receipt.kernel_calls == len(bundle.nodes) == 377 and len(positions) == 376
    assert receipt.total_body_nodes == 30527 and receipt.dependency_edges == 1071
    from peano_lab.engine.state import proof_metrics
    assert proof.proof_nodes == proof_metrics(proof.certificate)[0]
    assert proof.proof_nodes > 1
    assert proof.formula == bundle.nodes[positions[PRINCIPAL]].target
    assert check((), proof.certificate, proof.formula)
    with pytest.raises(TypeError):
        positions["invented"] = 0


def test_source_change_clears_checked_bundles_and_materialized_certificates(actual_small, tmp_path):
    current.checked_research_bundle(SMALL)
    current.replay(PRINCIPAL, edition="alpha")
    assert current._checked_research_bundle.cache_info().currsize == 1
    assert current.replay.cache_info().currsize == 1
    current.set_research_bundle_source(SMALL, tmp_path / "missing.json")
    try:
        assert current._checked_research_bundle.cache_info().currsize == 0
        assert current.replay.cache_info().currsize == 0
        with pytest.raises(current.EditionV33ReplayError):
            current.replay(PRINCIPAL, edition="alpha")
    finally:
        current.set_research_bundle_source(SMALL, None)


@pytest.mark.parametrize("slug", ("missing", "", None, 0, True, [SMALL]))
def test_invalid_family_source_setter_does_not_mutate_state(slug):
    before = dict(current._bundle_sources)
    with pytest.raises(current.EditionV33ReplayError):
        current.set_research_bundle_source(slug, "irrelevant")
    assert current._bundle_sources == before


@pytest.mark.parametrize("source", (0, True, object(), b"proof.json", []))
def test_invalid_source_type_cannot_invalidate_or_redirect_a_valid_provider(source):
    before = dict(current._bundle_sources)
    with pytest.raises(current.EditionV33ReplayError):
        current.set_research_bundle_source(SMALL, source)
    assert current._bundle_sources == before


@pytest.mark.parametrize("mutation", ("missing", "directory", "symlink", "truncate", "append", "poison"))
def test_changed_artifact_is_rejected_before_decode_kernel_or_parent_fallback(monkeypatch, tmp_path, mutation):
    family = c.research_family(SMALL)
    path = tmp_path / "changed.json"
    raw = (ROOT / family.artifact).read_bytes()
    if mutation == "directory":
        path.mkdir()
    elif mutation == "symlink":
        path.symlink_to(ROOT / family.artifact)
    elif mutation == "truncate":
        path.write_bytes(raw[:-1])
    elif mutation == "append":
        path.write_bytes(raw + b" ")
    elif mutation == "poison":
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    monkeypatch.setattr(current, "decode_proof_bundle", lambda *_: pytest.fail("bad artifact was decoded"))
    monkeypatch.setattr(parent, "replay", lambda *_a, **_k: pytest.fail("bad new proof fell back to parent"))
    current.set_research_bundle_source(SMALL, path)
    try:
        with pytest.raises(current.EditionV33ReplayError):
            current.replay(PRINCIPAL, edition="alpha")
    finally:
        current.set_research_bundle_source(SMALL, None)


def test_short_browser_layout_resolves_only_the_explicit_proof_mount(monkeypatch):
    monkeypatch.setattr(current, "__file__", "/lab/peano_lab/library/editions_v33.py")
    monkeypatch.setattr(Path, "is_file", lambda *_: False)
    assert current._default_research_bundle_source(SMALL) == Path(
        "/lab/proof-artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json"
    )


def test_provider_and_ordinary_runtime_do_not_need_any_catalogue(actual_small, monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as old
    from peano_lab.library import campaign_gaussian_factorization_closure as gaussian
    from peano_lab.library import campaign_lower_layer_closure as lower
    for module in (old, gaussian, lower):
        monkeypatch.setattr(module, "parent_snapshot", lambda: pytest.fail("runtime loaded a repository catalogue"))
    current.set_research_bundle_source(SMALL, None)
    checked = current.replay(PRINCIPAL, edition="alpha")
    assert check((), checked.certificate, checked.formula)


@pytest.mark.parametrize("mutation", ("none", "node_id", "target", "dependencies", "body", "missing_node", "root"))
def test_interning_is_untrusted_and_cannot_omit_or_rewire_proof_data(actual_small, monkeypatch, mutation):
    original = current.intern_layered_replay_bodies
    def altered(*args, **kwargs):
        result = original(*args, **kwargs)
        if mutation == "none":
            return None
        if mutation == "missing_node":
            return replace(result, nodes=result.nodes[:-1])
        if mutation == "root":
            return replace(result, root=0)
        nodes = list(result.nodes)
        position = next(i for i, node in enumerate(nodes) if node.dependencies)
        node = nodes[position]
        changes = {"node_id": {"node_id": 9999}, "target": {"target": Bot()},
                   "dependencies": {"dependencies": ()}, "body": {"body": Hyp(0)}}[mutation]
        nodes[position] = replace(node, **changes)
        return replace(result, nodes=tuple(nodes))
    monkeypatch.setattr(current, "intern_layered_replay_bodies", altered)
    current.replay.cache_clear()
    with pytest.raises((current.EditionV33ReplayError, ValueError)):
        current.replay(PRINCIPAL, edition="alpha")


@pytest.mark.parametrize("mutation", ("none", "open_hypothesis", "other_formula", "changed_target"))
def test_untrusted_materializer_never_substitutes_an_open_or_other_certificate(actual_small, monkeypatch, mutation):
    _, _, _, actual = actual_small
    if mutation == "none":
        forged = None
    elif mutation == "changed_target":
        forged = SimpleNamespace(target=Bot(), certificate=actual.certificate, proof_nodes=actual.proof_nodes)
    else:
        forged = SimpleNamespace(target=actual.formula, proof_nodes=1,
                                 certificate=Hyp(0) if mutation == "open_hypothesis" else EqRefl(Zero()))
    monkeypatch.setattr(current, "compile_gaussian_factorization_replay", lambda *_a, **_k: forged)
    current.replay.cache_clear()
    with pytest.raises(current.EditionV33ReplayError):
        current.replay(PRINCIPAL, edition="alpha")


def test_original_empty_context_recheck_is_mandatory(actual_small, monkeypatch):
    current.replay.cache_clear()
    original = current.check
    calls = []
    def observed(context, proof, target):
        calls.append((context, target))
        return original(context, proof, target)
    monkeypatch.setattr(current, "check", observed)
    actual = current.replay(PRINCIPAL, edition="alpha")
    assert calls and calls[-1] == ((), actual.formula)
    assert all(context == () for context, _ in calls)


def test_original_checker_rejection_is_never_replaced_by_receipts(actual_small, monkeypatch):
    monkeypatch.setattr(current, "check", lambda *_a, **_k: False)
    current.replay.cache_clear()
    with pytest.raises(current.EditionV33ReplayError):
        current.replay(PRINCIPAL, edition="alpha")


def test_proof_caches_are_single_family_and_single_certificate():
    assert current._checked_research_bundle.cache_info().maxsize == 1
    assert current.replay.cache_info().maxsize == 1


def test_cold_installed_runtime_is_artifact_free_and_imports_no_authoring_scripts():
    program = r"""
import resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(170,175))
signal.alarm(180)
from pathlib import Path
import builtins,sys
original_open=Path.open
original_import=builtins.__import__
def guarded_open(path,*args,**kwargs):
    if "catalog" in path.name or "proof-bundle" in path.name:
        raise AssertionError("cold runtime opened an artifact/catalogue")
    return original_open(path,*args,**kwargs)
def guarded_import(name,*args,**kwargs):
    if name=="scripts" or name.startswith("scripts.") or name.startswith("constructive_"):
        raise AssertionError("cold runtime imported authoring scripts")
    return original_import(name,*args,**kwargs)
Path.open=guarded_open
builtins.__import__=guarded_import
from peano_lab.library import editions_v33 as v
v.require_research_seal()
assert len(v.ALPHA_CHECKED_SPECS)==4092 and len(v.STABLE_SPECS)==432
assert not any(name=="scripts" or name.startswith("scripts.") for name in sys.modules)
assert v._checked_research_bundle.cache_info().currsize==0
assert v.replay.cache_info().currsize==0
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform!="darwin":
    peak*=1024
assert peak<=1536*1024*1024
print("artifact-free installed v33 PASS")
"""
    result = subprocess.run([sys.executable, "-c", program], cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH=str(ROOT / "peano-lab/py"),
                                     PYTHONMALLOC="pymalloc", PYTHONDONTWRITEBYTECODE="1"),
                            text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "artifact-free installed v33 PASS"


def test_streaming_encoders_are_the_exact_original_functions_not_reimplementations():
    assert current._stream_identity is parent._stream_identity
    assert current._stream_enrollment_identity is parent._stream_enrollment_identity
    assert current._make_streamed_edition is parent._make_streamed_edition


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_ALPHA_V32_COUNT", 0),
    ("EXPECTED_ALPHA_V32_FRONTIER_COUNT", 0),
    ("EXPECTED_ALPHA_V32_IDENTITY_SHA256", "0" * 64),
    ("EXPECTED_ALPHA_V32_ENROLLMENT_SHA256", "0" * 64),
))
def test_v32_parent_metadata_guard_is_retained_before_any_v33_lookup(monkeypatch, field, value):
    monkeypatch.setattr(parent, field, value)
    monkeypatch.setattr(current, "checked_research_bundle",
                        lambda *_a, **_k: pytest.fail("bad parent reached the new proof provider"))
    with pytest.raises(current.EditionV33ReplayError, match="parent"):
        current.edition("alpha")
    assert current.edition("stable") is parent.STABLE_EDITION


def test_all_eight_canonical_sources_use_the_new_shared_test_without_old_loaders():
    enrollment = a.alpha_v33_enrollment()
    for owner in c.FACTORIES:
        assert owner.test == "peano-lab/py/tests/test_campaign_research_v33_closure.py"
        assert (ROOT / owner.test).is_file()
        for name, source in enrollment.source_by_name.items():
            if source == owner.source:
                assert enrollment.test_by_name[name] == owner.test
    assert not any(name in sys.modules for name in (
        "working_equivalence_support", "working_euclidean_support", "working_euclidean_extension_support"))


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

