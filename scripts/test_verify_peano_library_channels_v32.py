"""Independent v32 row, provenance, catalogue and channel regressions.

The syntax fixture reads the actual frozen mathematical sources and inert
artifact bodies.  The large fixture combines the actual immutable v31 parent
and actual v32 entries for *private metadata-contract tests only*.  Its plain
report is conspicuously not a FreshProofAudit, never enters a release writer,
and is explicitly rejected by every public authority boundary.  No HA or Lean
acceptance is mocked, and no saved report can authorize admission.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, replace
import gc
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import random
import resource
import signal
import sys
import time
from types import SimpleNamespace

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import build_peano_library_channels_v32 as builder
import verify_peano_library_channels_v32 as verifier
import check_alpha_v32_research as audit
from peano_lab.library import campaign_research_v32_closure as research
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_INVENTORY = (
    ("multiplicative-convolution", 90, 462, 1371, 35945),
    ("polynomial-division-prerequisites", 85, 293, 740, 17412),
)
RESEARCH_PRESENTATIONS = (
    ("book/_static/constructive-g009-explorer/multiplicative-convolution/api/checkpoint.json",
     17455, "d55e7cb2071c77bd0a305d56591c6e59c46afc610f4db8020deeb10e6fbf8d6c"),
    ("book/_static/constructive-polynomial-division-explorer/polynomial-division-prerequisites/api/checkpoint.json",
     12722, "87e9e6d3e1467a263ee2cc6fcb5044c440f1f563511db93ffafa7b7a70c0f10e"),
)
SHARED_TEST = "peano-lab/py/tests/test_dirichlet_multiplicative_closure_candidate.py"
SHARED_MODULES = ("dirichlet_multiplicative_support_candidate", "dirichlet_multiplicative_candidate")
OUTPUT_NAMES = ("DEFAULT_ALPHA", "DEFAULT_DELTA", "DEFAULT_METRICS", "DEFAULT_GRAPH",
                "DEFAULT_CHANNELS", "DEFAULT_RECEIPT")
ROW_FIELDS = (
    "body_checked", "body_receipt", "checked_use", "dependencies", "dependencies_sha256",
    "empty_context_closure", "enrollment_index", "enrollment_origin", "evidence_links", "evidence_status",
    "frontier_campaign", "logical_spec_sha256", "membership", "name", "proof_tag", "provenance",
    "script", "script_sha256", "source", "statement", "statement_sha256", "summary", "summary_sha256",
    "alpha_v32_frontier_enrollment",
)


def _bad(value):
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return value + " [changed]"
    if type(value) is list:
        return ["unreviewed"]
    if type(value) is dict:
        return {"unreviewed": True}
    return "unreviewed"


def _changed(value, path, replacement=None, *, explicit=False):
    """Copy only the changed path, not the immutable 3796-row parent."""
    if not path:
        return replacement if explicit else _bad(value)
    key, *tail = path
    result = list(value) if type(value) is list else dict(value)
    result[key] = _changed(value[key], tail, replacement, explicit=explicit)
    return result


def _files_fingerprint(paths):
    return tuple((str(path), len(raw), builder.digest(raw)) for path in sorted(set(paths))
                 for raw in (builder.read_bytes(path),))


@dataclass(frozen=True, repr=False)
class SyntaxMetadataOnly:
    entries: tuple
    items: tuple
    families: dict
    documents: dict
    report: dict
    fingerprint: tuple


@pytest.fixture(scope="module")
def syntax_metadata_only():
    """Real source/body syntax and historical observations, never live proof."""
    from peano_lab.engine.state import proof_identity_metrics, proof_metrics
    from peano_lab.library.proof_bundle import DEFAULT_BUNDLE_LIMITS, decode_formula, decode_proof

    owners = research.validate_research_source_bytes()
    specs = research.research_specs()
    items = audit.registry()
    by_name = {spec.name: spec for spec in specs}
    entries = []
    for owner in owners:
        factory_rows = tuple(getattr(import_module("peano_lab.library." + owner.module), owner.factory)(TheoremSpec))
        assert len(factory_rows) == owner.count
        entries.extend(SimpleNamespace(spec=spec, source_module=owner.source,
                                       enrollment_origin=SimpleNamespace(value="ha"))
                       for spec in factory_rows)
    assert tuple(entry.spec for entry in entries) == specs
    paths = {ROOT / owner.source for owner in owners} | {ROOT / owner.test for owner in owners}
    paths |= {ROOT / item.rfc for item in items} | {ROOT / item.artifact for item in items}
    paths |= {builder.PARENT_ALPHA, *(ROOT / row[0] for row in RESEARCH_PRESENTATIONS)}
    paths |= {ROOT / path for path in builder.CONTROL_DOCUMENTS}
    before = _files_fingerprint(paths)
    families = {}
    for item, sealed, presentation_pin in zip(items, research.FAMILIES, RESEARCH_PRESENTATIONS, strict=True):
        raw = research.read_research_bundle_bytes(item.slug, ROOT / item.artifact)
        encoded = json.loads(raw)
        assert type(encoded) is list and len(encoded) == 4 and encoded[0] == "peano-lab-bundle-v1"
        assert encoded[1] == sealed.node_count - 1 and len(encoded[3]) == sealed.node_count
        presentation_raw = builder.read_bytes(ROOT / presentation_pin[0])
        assert (len(presentation_raw), builder.digest(presentation_raw)) == presentation_pin[1:]
        historical = builder.strict_json(presentation_raw)
        assert historical["stored_receipt_is_proof_authority"] is False
        assert historical["alpha_admission_performed"] is historical["stable_admission_performed"] is False
        assert tuple(historical["checkpoint"]["owned_names"]) == sealed.owned_names
        assert historical["checkpoint"]["bundle"]["sha256"] == item.artifact_sha256
        rows = []
        start = sealed.theorem_count - sealed.count
        for offset, name in enumerate(sealed.owned_names):
            node_id = start + offset
            node = encoded[3][node_id]
            assert type(node) is list and len(node) == 4 and type(node[0]) is int and node[0] > 0
            assert decode_formula(node[1], _depth=DEFAULT_BUNDLE_LIMITS.max_formula_depth) == _closed_formula(by_name[name].statement)
            body = decode_proof(node[3], _depth=DEFAULT_BUNDLE_LIMITS.max_body_depth)
            nodes, depth = proof_metrics(body)
            objects, edges, reused = proof_identity_metrics(body)
            rows.append({"name": name, "node_id": node_id, "statement_sha256": builder.digest(by_name[name].statement),
                         "proof_nodes": nodes, "proof_depth": depth, "proof_objects": objects,
                         "proof_edges": edges, "reused_objects": reused})
            del body
        assert tuple(row["name"] for row in historical["principal_roots"]) == item.principal_roots
        # These booleans are historical observations, not fresh checks.  The
        # enclosing SyntaxMetadataOnly object is rejected at every public gate.
        families[item.slug] = {
            "slug": item.slug, "new_theorem_count": item.frontier_count,
            "specs_sha256": item.frontier_specs_sha256,
            "owned_node_ids": {row["name"]: row["node_id"] for row in rows}, "rows": rows,
            "bundle": {"path": item.artifact, "bytes": item.artifact_bytes, "sha256": item.artifact_sha256,
                       "nodes_including_packaging_root": sealed.node_count,
                       "dependency_edges_including_packaging": sealed.bundle_edges,
                       "body_proof_nodes": sealed.body_nodes, "packaging_root_id": sealed.node_count - 1,
                       "kernel_calls": sealed.node_count,
                       "original_ha_checked": historical["checkpoint"]["bundle"]["original_ha_checked"],
                       "independent_lean_checked": historical["checkpoint"]["bundle"]["independent_lean_checked"]},
            "principal_roots": historical["principal_roots"],
        }
        del encoded, raw
        gc.collect()
    report = {"test_scope": "NON-AUTHORIZING actual-syntax/historical-observation metadata projection",
              "families": list(families.values()), "ordinary_principal_count": 12}
    documents = {builder.relative(path): builder._document(path, "test-only real byte identity, not admission")
                 for path in paths}
    receipt = builder.relative(builder.DEFAULT_RECEIPT)
    documents[receipt] = builder._document(builder.DEFAULT_RECEIPT, "non-authorizing formatter input",
                                         payload=builder.pretty(report))
    assert _files_fingerprint(paths) == before
    yield SyntaxMetadataOnly(tuple(entries), items, families, documents, report, before)
    assert _files_fingerprint(paths) == before


@pytest.fixture
def exact_row(syntax_metadata_only):
    entry = syntax_metadata_only.entries[0]
    item = syntax_metadata_only.items[0]
    family = syntax_metadata_only.families[item.slug]
    docs = syntax_metadata_only.documents
    return builder._frontier_row(entry, 3796, item, family, docs), entry, item, family, docs


def _check_row(data, row=None):
    original, entry, item, family, docs = data
    verifier._row(original if row is None else row, entry, 3796, family, item, docs)


def test_exact_scope_parent_pins_and_original_limits():
    assert tuple((f.slug, f.count, f.node_count, f.bundle_edges, f.body_nodes) for f in research.FAMILIES) == EXPECTED_INVENTORY
    assert len(research.FACTORIES) == 13 and len(research.FRONTIER_NEW_NAMES) == 175
    assert audit.EXPECTED_JOB_COUNT == 15 and tuple(len(item.principal_roots) for item in audit.registry()) == (6, 6)
    assert (audit.CPU_LIMITS, audit.WALL_SECONDS, audit.MAX_RSS_BYTES) == ((170, 175), 180, 1536 * 1024 * 1024)
    assert builder.MAX_CATALOG_BYTES == builder.codec.MAX_CATALOG_BYTES == 64 * 1024 * 1024
    assert builder.EXPECTED_PARENT_PINS["catalog"][1] == "6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab"
    assert builder.STABLE_SHA256 == "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"


@pytest.mark.parametrize("module", SHARED_MODULES)
def test_shared_g009_test_provenance_is_literal(module, syntax_metadata_only):
    owner = research.FACTORY_BY_MODULE[module]
    assert owner.test == audit.module_test_path(module) == SHARED_TEST
    entry = next(entry for entry in syntax_metadata_only.entries if entry.source_module == owner.source)
    index = 3796 + syntax_metadata_only.entries.index(entry)
    item = syntax_metadata_only.items[0]
    family, docs = syntax_metadata_only.families[item.slug], syntax_metadata_only.documents
    row = builder._frontier_row(entry, index, item, family, docs)
    verifier._row(row, entry, index, family, item, docs)
    assert row["evidence_links"][1]["path"] == SHARED_TEST
    assert row["alpha_v32_frontier_enrollment"]["test_sha256"] == builder.digest(builder.read_bytes(ROOT / SHARED_TEST))
    assert "test_" + module + ".py" != Path(SHARED_TEST).name


@pytest.mark.parametrize("owner", research.FACTORIES, ids=lambda owner: owner.module)
def test_every_real_factory_row_matches_the_independent_format_contract(owner, syntax_metadata_only):
    item = next(item for item in syntax_metadata_only.items if item.slug == owner.campaign)
    family, docs = syntax_metadata_only.families[item.slug], syntax_metadata_only.documents
    count = 0
    for index, entry in enumerate(syntax_metadata_only.entries, 3796):
        if entry.source_module == owner.source:
            row = builder._frontier_row(entry, index, item, family, docs)
            assert set(row) == set(ROW_FIELDS)
            verifier._row(row, entry, index, family, item, docs)
            assert row["statement"] == entry.spec.statement and row["script"] == list(entry.spec.script)
            assert row["evidence_links"][1]["path"] == owner.test
            count += 1
    assert count == owner.count


@pytest.mark.parametrize("field", ROW_FIELDS)
def test_each_new_row_field_is_exact(exact_row, field):
    row = _changed(exact_row[0], (field,))
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, row)


@pytest.mark.parametrize("field", ROW_FIELDS)
def test_each_new_row_field_is_required(exact_row, field):
    row = dict(exact_row[0])
    del row[field]
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, row)


def test_new_row_extra_field_is_rejected(exact_row):
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, {**exact_row[0], "unreviewed_authority": True})


ROW_NESTED_PATHS = (
    *( ("source", field) for field in ("kind", "path", "sha256") ),
    *( ("body_receipt", field) for field in (
        "name", "command_count", "dependency_count", "dne_command_count", "status",
        "proof_nodes", "proof_depth", "proof_objects", "proof_edges", "reused_objects") ),
    *( ("empty_context_closure", field) for field in (
        "body_proof_depth", "body_proof_nodes", "bundle_campaign", "bundle_dependency_edge_count",
        "bundle_node_count", "bundle_node_id", "bundle_path", "bundle_root_id", "certificate_representation",
        "certificate_sha256", "closure_kind", "digest_kind", "kernel_mode", "node_statement_sha256", "status") ),
    *( ("alpha_v32_frontier_enrollment", field) for field in (
        "first_enrolled_version", "campaign", "parent_catalog_sha256", "source_sha256", "test_sha256",
        "rfc_sha256", "body_receipt_sha256", "bundle_campaign", "bundle_node_id", "bundle_sha256") ),
)


@pytest.mark.parametrize("path", ROW_NESTED_PATHS, ids=lambda path: "/".join(path))
def test_every_body_closure_and_first_admission_field_is_exact(exact_row, path):
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, _changed(exact_row[0], path))


@pytest.mark.parametrize("index", range(6))
@pytest.mark.parametrize("field", ("path", "document_sha256", "kind", "role", "selector"))
def test_every_evidence_link_field_is_exact(exact_row, index, field):
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, _changed(exact_row[0], ("evidence_links", index, field)))


@pytest.mark.parametrize("mutation", ("missing", "extra", "reordered", "duplicate"))
def test_evidence_links_are_an_exact_ordered_six_tuple(exact_row, mutation):
    row = dict(exact_row[0])
    links = list(row["evidence_links"])
    if mutation == "missing":
        links.pop()
    elif mutation == "extra":
        links.append(links[0])
    elif mutation == "reordered":
        links.reverse()
    else:
        links[1] = links[0]
    row["evidence_links"] = links
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, row)


@pytest.mark.parametrize("path,value", (
    (("checked_use",), 1), (("body_checked",), 1), (("enrollment_index",), 3796.0),
    (("body_receipt", "dne_command_count"), False),
    (("empty_context_closure", "bundle_node_id"), 371.0),
    (("alpha_v32_frontier_enrollment", "first_enrolled_version"), "v31"),
    (("empty_context_closure", "kernel_mode"), "classical"),
    (("empty_context_closure", "closure_kind"), "trusted_receipt"),
    (("membership",), "stable"), (("script",), ["sorry"]), (("script",), ["DNE"]),
))
def test_row_json_types_and_no_admission_shortcuts(exact_row, path, value):
    with pytest.raises(verifier.ReleaseError):
        _check_row(exact_row, _changed(exact_row[0], path, value, explicit=True))


def test_non_authorizing_actual_metadata_cannot_enter_any_public_gate(syntax_metadata_only):
    assert type(syntax_metadata_only) is not audit.FreshProofAudit
    assert "schema" not in syntax_metadata_only.report
    for value in (syntax_metadata_only, syntax_metadata_only.report,
                  builder.pretty(syntax_metadata_only.report), SimpleNamespace(report=syntax_metadata_only.report)):
        with pytest.raises(ValueError):
            builder.build_payloads(value)
        with pytest.raises(verifier.ReleaseError):
            verifier.verify_candidate_payloads({}, value)
        with pytest.raises(verifier.ReleaseError):
            verifier.context_from_live_audit(value)
        with pytest.raises(verifier.ReleaseError):
            verifier.LiveReleaseContext(object(), value, {}, {}, {}, ())


@pytest.mark.parametrize("value", ({}, {"passed": True}, b'{"passed":true}', object(), None))
def test_saved_reports_never_construct_live_authority(value):
    with pytest.raises(audit.AuditError, match="saved report"):
        audit.FreshProofAudit(value, "0" * 64, {"passed": True}, 1)
    with pytest.raises(verifier.ReleaseError, match="saved metadata"):
        verifier.LiveReleaseContext(value, {"passed": True}, {}, {}, {}, ())


@pytest.mark.parametrize("kind", ("uninitialized", "foreign_token", "subclass", "duck"))
def test_foreign_and_uninitialized_invocations_fail_before_any_source_or_proof_work(monkeypatch, kind):
    calls = []
    class ForeignAudit(audit.FreshProofAudit):
        def require_unchanged(self):
            calls.append("foreign override must not run")
    if kind == "duck":
        value = SimpleNamespace(report={"passed": True}, require_unchanged=lambda: calls.append("duck"))
    else:
        value = object.__new__(ForeignAudit if kind == "subclass" else audit.FreshProofAudit)
        if kind == "foreign_token":
            value._token = object()
    def forbidden(*_args, **_kwargs):
        calls.append("source or proof gate unexpectedly reached")
        raise AssertionError(calls[-1])
    monkeypatch.setattr(audit, "source_binding", forbidden)
    monkeypatch.setattr(audit, "verify_in_fresh_windows", forbidden)
    for entrypoint, args in ((builder.build_payloads, (value,)),
                            (verifier.verify_candidate_payloads, ({}, value)),
                            (verifier.context_from_live_audit, (value,))):
        with pytest.raises((ValueError, audit.AuditError, AttributeError)):
            entrypoint(*args)
    assert calls == []


def test_a_foreign_live_context_token_cannot_read_files_or_claim_success(monkeypatch):
    value = object.__new__(verifier.LiveReleaseContext)
    value._token = object()
    monkeypatch.setattr(builder, "read_bytes", lambda *_args: pytest.fail("foreign capability reached a file read"))
    with pytest.raises(verifier.ReleaseError, match="no live"):
        value.require_unchanged()


@pytest.mark.parametrize("entrypoint", (builder.build_payloads, verifier.verify_for_publication))
@pytest.mark.parametrize("failure", ("preflight", "actual_proof"))
def test_entrypoints_fail_before_acceptance_when_either_real_gate_fails(monkeypatch, entrypoint, failure):
    calls = []
    def preflight():
        calls.append("preflight")
        if failure == "preflight":
            raise ValueError("deliberate preflight rejection")
    def actual_proof():
        calls.append("actual_proof")
        raise audit.AuditError("deliberate proof failure; no acceptance substituted")
    monkeypatch.setattr(builder, "preflight_inputs", preflight)
    monkeypatch.setattr(audit, "verify_in_fresh_windows", actual_proof)
    with pytest.raises((ValueError, audit.AuditError), match="deliberate"):
        entrypoint()
    assert calls == (["preflight"] if failure == "preflight" else ["preflight", "actual_proof"])


@pytest.mark.parametrize("entrypoint", (builder.main, verifier.main))
@pytest.mark.parametrize("args", (("--receipt", "stored.json"), ("--skip-proof",), ("--trust-report",), ("--family", "one")))
def test_public_cli_has_no_saved_receipt_or_partial_acceptance_mode(entrypoint, args):
    with pytest.raises(SystemExit) as caught:
        entrypoint(list(args))
    assert caught.value.code == 2


def _source_tree(module):
    return ast.parse(builder.read_bytes(Path(module.__file__)).decode())


def _function(module, name):
    return next(node for node in _source_tree(module).body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)


def _call_names(node):
    return [ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)]


def test_source_order_keeps_preinstall_independent_verification_and_postinstall_capability():
    calls = [ast.unparse(node) for node in _function(builder, "main").body]
    def position(needle):
        return next(index for index, source in enumerate(calls) if needle in source)
    assert position("build_payloads()") < position("verify_candidate_payloads(payloads, audit)")
    assert position("verify_candidate_payloads(payloads, audit)") < position("check_or_write(payloads")
    assert position("check_or_write(payloads") < position("context_from_live_audit(audit)")
    assert position("context_from_live_audit(audit)") < position("context.require_unchanged()")
    assert "LiveReleaseContext" not in _call_names(_function(verifier, "verify_candidate_payloads"))
    context = ast.unparse(_function(verifier, "context_from_live_audit"))
    assert "edition.replay('zero_add', edition='stable')" in context
    assert "check((), result.certificate, result.formula)" in context
    assert context.count("audit.require_unchanged()") >= 2


def test_live_context_rechecks_exact_bytes_and_in_process_metadata():
    source = ast.unparse(_function(verifier, "LiveReleaseContext"))
    assert "type(self) is LiveReleaseContext" in source and "self._token is _LIVE_RELEASE" in source
    assert "self._audit.require_unchanged()" in source and "builder.read_bytes(path)" in source
    assert "len(contents) == length" in source and "builder.digest(contents) == expected" in source
    assert "_content_digest(self._catalog)" in source and "_content_digest(self._channels)" in source
    assert "self._audit.report['families']" in source


def test_controls_bind_this_regression_and_preserve_parent_evidence_archives():
    assert builder.relative(Path(__file__)) in builder.CONTROL_DOCUMENTS
    assert set(builder.CONTROL_DOCUMENTS) >= {
        "scripts/build_peano_library_channels_v32.py", "scripts/verify_peano_library_channels_v32.py",
        "scripts/peano_catalog_shards_v32.py", "scripts/check_alpha_v32_research.py"}
    assert set(builder.historical_evidence.archive_paths()) <= set(audit.CONTROL_SOURCES)
    for module in (builder, verifier):
        source = builder.read_bytes(Path(module.__file__)).decode()
        assert "module_test_path" in source
        assert "test_" + "{pin.module}" not in source


@pytest.mark.parametrize("payload", (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b"[]", b"null", b"\xff"))
def test_release_json_has_exact_object_and_finite_unique_fields(payload):
    with pytest.raises((ValueError, UnicodeError)):
        builder.strict_json(payload)


@pytest.mark.parametrize("value", ({"s": "Zażółć λ", "flag": True, "n": 1}, ["α", None, False, {"x": 0}], {}))
def test_streaming_digest_equals_original_canonical_bytes(value):
    assert verifier._content_digest(value) == sha256(builder.compact(value).encode()).hexdigest()
    assert not verifier._same({"x": True}, {"x": 1})
    assert not verifier._same({"x": 1}, {"x": 1.0})


@pytest.mark.parametrize("include_origin", (False, True))
@pytest.mark.parametrize("size", (0, 1, 2, 17, 64))
def test_independent_streaming_ordered_roots_preserve_unicode_and_separator_bytes(include_origin, size):
    rng = random.Random(0x32)
    atoms = ("", "plain", "Zażółć", "λ∀∃", "\x00", "\x1c", "\x1d", "\x1e", "\x1f", "a\nb", "🙂", "e\u0301")
    def fragment():
        return "".join(rng.choice(atoms) for _ in range(rng.randrange(5)))
    entries = tuple(SimpleNamespace(
        spec=TheoremSpec(fragment(), fragment(), tuple(fragment() for _ in range(rng.randrange(4))),
                         tuple(fragment() for _ in range(rng.randrange(4))), "unused summary"),
        enrollment_origin=SimpleNamespace(value=fragment())) for _ in range(size))
    expected = builder.base._ordered_root(entries, include_origin=include_origin)
    assert builder._ordered_root(entries, include_origin=include_origin) == expected
    assert verifier._ordered_root(entries, include_origin=include_origin) == expected
    assert verifier._ordered_root is not builder._ordered_root


@pytest.fixture
def six_payloads():
    return {getattr(builder, name): ("transport only: " + name + "\n").encode() for name in OUTPUT_NAMES}


def test_candidate_byte_adapter_copies_mapping_and_returns_exact_immutable_bytes(six_payloads):
    retained = dict(six_payloads)
    adapter = verifier._ReleaseArtifacts(six_payloads)
    for path, original in retained.items():
        six_payloads[path] = b"changed input mapping"
        assert adapter.read(path) is original
    assert adapter._payloads == retained


@pytest.mark.parametrize("mutation", ("missing", "extra", "relative_key", "list", "empty", "text", "bytearray", "memoryview"))
def test_candidate_byte_adapter_rejects_incomplete_or_mutable_payloads(six_payloads, mutation):
    path = builder.DEFAULT_ALPHA
    if mutation == "missing":
        del six_payloads[path]
    elif mutation == "extra":
        six_payloads[ROOT / "unreviewed.json"] = b"x"
    elif mutation == "relative_key":
        six_payloads[Path("catalog-v32.json")] = six_payloads.pop(path)
    elif mutation == "list":
        six_payloads = list(six_payloads.items())
    else:
        six_payloads[path] = {"empty": b"", "text": "x", "bytearray": bytearray(b"x"),
                              "memoryview": memoryview(b"x")}[mutation]
    with pytest.raises(verifier.ReleaseError):
        verifier._ReleaseArtifacts(six_payloads)


def test_original_64_mib_candidate_ceiling_is_enforced(six_payloads):
    six_payloads[builder.DEFAULT_ALPHA] = b"x" * (64 * 1024 * 1024 + 1)
    with pytest.raises(verifier.ReleaseError):
        verifier._ReleaseArtifacts(six_payloads)
    with pytest.raises(ValueError, match="document limit"):
        builder.check_or_write(six_payloads, check=False)


@pytest.fixture
def dedicated_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    for name in OUTPUT_NAMES:
        monkeypatch.setattr(builder, name, tmp_path / (name.lower() + ".json"))
    return {getattr(builder, name): ("transport only " + name).encode() for name in OUTPUT_NAMES}


def test_exclusive_writer_only_creates_its_six_dedicated_transport_outputs(dedicated_outputs):
    builder.check_or_write(dedicated_outputs, check=False)
    assert {path: path.read_bytes() for path in dedicated_outputs} == dedicated_outputs
    builder.check_or_write(dedicated_outputs, check=True)


@pytest.mark.parametrize("index", range(6))
def test_any_existing_output_stops_all_writes(dedicated_outputs, index):
    paths = list(dedicated_outputs)
    paths[index].write_bytes(b"immutable predecessor")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        builder.check_or_write(dedicated_outputs, check=False)
    assert paths[index].read_bytes() == b"immutable predecessor"
    assert not any(path.exists() for path in paths if path != paths[index])


@pytest.mark.parametrize("mutation", ("missing", "extra", "empty", "text", "bytearray", "dangling_symlink"))
def test_writer_rejects_wrong_inventory_or_unsafe_output_without_partial_writes(dedicated_outputs, mutation, tmp_path):
    outputs = dict(dedicated_outputs)
    first = next(iter(outputs))
    if mutation == "missing":
        del outputs[first]
    elif mutation == "extra":
        outputs[tmp_path / "outside.json"] = b"x"
    elif mutation == "dangling_symlink":
        first.symlink_to(tmp_path / "uncreated.json")
    else:
        outputs[first] = {"empty": b"", "text": "x", "bytearray": bytearray(b"x")}[mutation]
    with pytest.raises(ValueError):
        builder.check_or_write(outputs, check=False)
    assert not any(path.exists() for path in dedicated_outputs)


def test_check_mode_is_read_only_and_detects_one_changed_byte(dedicated_outputs):
    builder.check_or_write(dedicated_outputs, check=False)
    path = next(iter(dedicated_outputs))
    path.write_bytes(dedicated_outputs[path] + b"x")
    before = {item: item.read_bytes() for item in dedicated_outputs}
    with pytest.raises(ValueError, match="stale"):
        builder.check_or_write(dedicated_outputs, check=True)
    assert {item: item.read_bytes() for item in dedicated_outputs} == before


# The remaining tests intentionally import the actual current runtime.  Run
# them in separately scheduled original-bound windows, never a synthetic
# edition replacement.  The projection remains a plain non-authorizing value.
@dataclass(frozen=True, repr=False)
class MetadataProjectionOnly:
    catalog: dict
    metrics: dict
    channels: dict
    parent: dict
    families: dict
    evidence: SyntaxMetadataOnly
    documents: dict
    artifacts: object
    manifest_hash: str


@pytest.fixture(scope="module")
def current_runtime_metadata_only():
    """Match release allocation order: runtime syntax precedes inert bodies."""
    from peano_lab.library import editions_v31 as parent_edition
    from peano_lab.library import editions_v32 as edition
    edition.require_research_seal()
    assert edition.STABLE_EDITION is parent_edition.STABLE_EDITION
    assert all(new is old for new, old in zip(edition.ALPHA_ENTRIES[:3796], parent_edition.ALPHA_ENTRIES, strict=True))
    gc.collect()
    return edition


@pytest.mark.parametrize("include_origin", (False, True))
def test_actual_3971_ordered_roots_match_original_algorithm(current_runtime_metadata_only, include_origin):
    edition = current_runtime_metadata_only
    expected = builder.base._ordered_root(edition.ALPHA_ENTRIES, include_origin=include_origin)
    assert builder._ordered_root(edition.ALPHA_ENTRIES, include_origin=include_origin) == expected
    assert verifier._ordered_root(edition.ALPHA_ENTRIES, include_origin=include_origin) == expected
    if include_origin:
        assert expected == "911df25bac9987e73d3313c90bdd0602e9e7e6f3f4af00c81701d35b14268cb5"


@pytest.fixture(scope="module")
def metadata_projection_only(current_runtime_metadata_only, syntax_metadata_only):
    edition = current_runtime_metadata_only
    gc.collect()
    parent = builder._load_parent()
    parent_metrics = builder.strict_json(builder.read_bytes(builder.PARENT_METRICS))
    parent_channels = builder.strict_json(builder.read_bytes(builder.PARENT_CHANNELS))
    evidence = syntax_metadata_only
    documents = {record["path"]: record for record in parent["evidence_documents"]}
    def add(path, role, raw=None):
        record = builder._document(ROOT / path, role, payload=raw)
        if path in documents:
            assert (documents[path]["bytes"], documents[path]["sha256"]) == (record["bytes"], record["sha256"])
        else:
            documents[path] = record
    for path, role in builder.CONTROL_DOCUMENTS.items():
        add(path, role)
    for label, (path, _) in builder.EXPECTED_PARENT_PINS.items():
        add(builder.relative(path), "Exact immutable Alpha-v31 parent release component: " + label + ".")
    receipt = builder.pretty(evidence.report)
    add(builder.relative(builder.DEFAULT_RECEIPT),
        "Fresh original-HA, same-byte compiled-Lean and twelve ordinary-principal release audit.", receipt)
    for item in evidence.items:
        add(item.artifact, "Complete actual constructive proof data; original research artifact unchanged.")
        add(item.rfc, "Exact reviewed constructive mathematical contract for " + item.slug + ".")
        for pin in item.modules:
            add(pin.path, "Exact constructive proof factory first admitted to Alpha v32.")
            add(audit.module_test_path(pin.module), "Independent exact statement, proof and hostile-input regression audit.")
    item_by_name = {name: item for item in evidence.items for name in research.FAMILY_BY_SLUG[item.slug].owned_names}
    rows = list(parent["theorems"])
    for index, entry in enumerate(edition.ALPHA_ENTRIES[3796:], 3796):
        item = item_by_name[entry.spec.name]
        rows.append(builder._frontier_row(entry, index, item, evidence.families[item.slug], documents))
    topology, graph = builder._topology(rows, parent_metrics)
    promotion = builder._promotion(evidence.report, evidence.families)
    origins = Counter(parent["enrollment_origin_counts"])
    origins["ha"] += 175
    catalog = {**parent, "schema": builder.SCHEMA, "theorem_count": 3971, "checked_use_count": 3971,
        "stable_count": 432, "alpha_only_count": 3539, "edge_count": edition.EXPECTED_ALPHA_V32_EDGE_COUNT,
        "layer_count": edition.EXPECTED_ALPHA_V32_LAYER_COUNT, "edition_identity_sha256": edition.ALPHA_V32_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": builder._ordered_root(edition.ALPHA_ENTRIES, include_origin=True),
        "ordered_spec_root_sha256": builder._ordered_root(edition.ALPHA_ENTRIES, include_origin=False),
        "membership_root_sha256": builder.base._membership_root(rows), "evidence_root_sha256": builder.base._evidence_root(rows),
        "enrollment_origin_counts": dict(sorted(origins.items())), "evidence_counts": {"alpha_closed": 3539, "stable_closed": 432},
        "membership_counts": {"alpha_only": 3539, "stable": 432},
        "canonical_order": [*parent["canonical_order"], *(f"Constructive Alpha-v32 {slug} ({count})" for slug, count in audit.EXPECTED_INVENTORY)],
        "evidence_documents": [documents[path] for path in sorted(documents)],
        "frontier_v32_campaign_counts": dict(audit.EXPECTED_INVENTORY),
        "frontier_v32_ordered_names_sha256": builder.digest("\n".join(edition.FRONTIER_NEW_NAMES)),
        "parent_alpha_v31": builder._parent_binding(), "alpha_v32_research_promotion": promotion, "theorems": rows}
    manifest, delta = builder.codec.encode_catalog({key: value for key, value in catalog.items() if key != "theorems"}, rows[3222:])
    metrics = builder._metrics(catalog, parent_metrics, topology, graph, manifest, promotion)
    metrics_bytes = builder.pretty(metrics)
    channels = builder._channels(catalog, parent_channels, manifest, delta, metrics_bytes, graph)
    artifacts = verifier._ReleaseArtifacts({builder.DEFAULT_ALPHA: manifest, builder.DEFAULT_DELTA: delta,
        builder.DEFAULT_METRICS: metrics_bytes, builder.DEFAULT_GRAPH: graph,
        builder.DEFAULT_CHANNELS: builder.pretty(channels), builder.DEFAULT_RECEIPT: receipt})
    assert type(evidence) is not audit.FreshProofAudit
    gc.collect()
    yield MetadataProjectionOnly(catalog, metrics, channels, parent, evidence.families,
                                 evidence, documents, artifacts, builder.digest(manifest))
    assert all(row is old for row, old in zip(rows[:3796], parent["theorems"], strict=True))


def _metadata_check(value, *, catalog=None, metrics=None, channels=None, artifacts=None):
    # Reclaim only unreachable temporary Python objects.  No proof or formula
    # cache, kernel limit, validator, catalogue row, or source is modified.
    gc.collect()
    return verifier._verify_metadata(value.catalog if catalog is None else catalog,
        value.metrics if metrics is None else metrics, value.channels if channels is None else channels,
        value.parent, value.families, value.evidence, value.manifest_hash,
        value.artifacts if artifacts is None else artifacts)


def test_actual_runtime_and_parent_projection_is_metadata_only(metadata_projection_only):
    value = metadata_projection_only
    assert len(value.catalog["theorems"]) == 3971 and len(value.parent["theorems"]) == 3796
    assert len(value.parent["evidence_documents"]) == 879
    assert len(value.catalog["theorems"][3796:]) == 175
    _metadata_check(value)
    docs = verifier._documents(value.catalog, value.parent, value.evidence, value.artifacts)
    rows, families = verifier._verify_rows(value.catalog, value.parent, value.evidence, docs)
    assert rows is value.catalog["theorems"] and families == value.families
    assert all(row is old for row, old in zip(rows[:3796], value.parent["theorems"], strict=True))
    assert value.channels["channels"]["stable"] == builder.strict_json(builder.read_bytes(builder.PARENT_CHANNELS))["channels"]["stable"]
    assert value.catalog["alpha_v32_research_promotion"]["open_named_targets"] == ["G091"]
    assert value.catalog["alpha_v32_research_promotion"]["all_parent_admissions_freshly_replayed_here"] is False
    with pytest.raises(verifier.ReleaseError, match="stored receipts"):
        verifier.verify_candidate_payloads(value.artifacts._payloads, value.evidence)


PARENT_METADATA_FIELDS = tuple(builder.strict_json(builder.read_bytes(builder.PARENT_ALPHA))["metadata"])
CATALOG_METADATA_FIELDS = tuple(key for key in PARENT_METADATA_FIELDS if key != "evidence_documents") + (
    "frontier_v32_campaign_counts", "frontier_v32_ordered_names_sha256", "parent_alpha_v31", "alpha_v32_research_promotion")
PARENT_METRICS_FIELDS = tuple(builder.strict_json(builder.read_bytes(builder.PARENT_METRICS)))
METRICS_FIELDS = PARENT_METRICS_FIELDS + ("parent_alpha_v31", "alpha_v32_research_promotion", "frontier_v32_campaign_counts", "frontier_v32_ordered_names_sha256")
PARENT_ALPHA_CHANNEL_FIELDS = tuple(builder.strict_json(builder.read_bytes(builder.PARENT_CHANNELS))["channels"]["alpha"])
ALPHA_CHANNEL_FIELDS = PARENT_ALPHA_CHANNEL_FIELDS + ("alpha_v32_frontier_new_count", "frontier_v32_campaign_counts", "parent_alpha_v31_sha256")


@pytest.mark.parametrize("field", CATALOG_METADATA_FIELDS)
def test_every_actual_catalogue_metadata_field_is_exact(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, catalog=_changed(metadata_projection_only.catalog, (field,)))


@pytest.mark.parametrize("field", METRICS_FIELDS)
def test_every_actual_metrics_field_is_exact(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, metrics=_changed(metadata_projection_only.metrics, (field,)))


@pytest.mark.parametrize("field", ALPHA_CHANNEL_FIELDS)
def test_every_actual_alpha_channel_field_is_exact(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, channels=_changed(metadata_projection_only.channels, ("channels", "alpha", field)))


@pytest.mark.parametrize("field", ("schema", "channels", "default_channel", "policy", "parent_channels_v31", "channel_pointer_root_sha256"))
def test_every_current_channel_envelope_field_is_exact(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, channels=_changed(metadata_projection_only.channels, (field,)))


PROMOTION_FIELDS = ("status", "parent_theorem_count", "frontier_new_count", "checked_use_before", "checked_use_after",
    "campaign_counts", "frontier_ordered_names_sha256", "proof_bundle_count", "proof_bundles", "independent_lean_bundle_verified",
    "ordinary_principal_count", "remaining_body_checked_count", "receipt_path", "receipt_sha256", "completed_named_targets",
    "open_named_targets", "freshly_checked_new_theorems", "inherited_checked_theorems", "all_parent_admissions_freshly_replayed_here",
    "historical_evidence_archives")


@pytest.mark.parametrize("field", PROMOTION_FIELDS)
def test_every_promotion_scope_field_is_exact(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, catalog=_changed(metadata_projection_only.catalog, ("alpha_v32_research_promotion", field)))


@pytest.mark.parametrize("where", ("catalog", "metrics", "channels", "alpha"))
@pytest.mark.parametrize("attack", ("extra", "missing"))
def test_no_new_or_missing_release_metadata_fields(metadata_projection_only, where, attack):
    value = metadata_projection_only
    original = value.channels if where == "alpha" else getattr(value, where)
    target = dict(original["channels"]["alpha"] if where == "alpha" else original)
    if attack == "extra":
        target["unreviewed_authority"] = True
    else:
        del target["schema" if where != "alpha" else "artifact_path"]
    changed = _changed(original, ("channels", "alpha"), target, explicit=True) if where == "alpha" else target
    with pytest.raises((verifier.ReleaseError, KeyError)):
        _metadata_check(value, **{"channels" if where == "alpha" else where: changed})


@pytest.mark.parametrize("component", ("catalog", "catalog_delta", "metrics", "dependency_graph"))
@pytest.mark.parametrize("field", ("path", "sha256"))
def test_channels_bind_all_four_exact_component_bytes(metadata_projection_only, component, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, channels=_changed(metadata_projection_only.channels,
            ("channels", "alpha", "artifacts", component, field)))


@pytest.mark.parametrize("field", ("artifact_path", "artifact_sha256", "theorem_count", "ordered_enrollment_root_sha256"))
def test_default_stable_pointer_cannot_be_rewritten(metadata_projection_only, field):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, channels=_changed(metadata_projection_only.channels, ("channels", "stable", field)))


@pytest.mark.parametrize("path,value", (
    (("checked_closure_metrics", "metric_bearing_theorem_count"), 3971.0),
    (("checked_closure_metrics", "missing_empty_context_metric_count"), False),
    (("checked_closure_metrics", "certificate_digest_kinds", "self-contained-proof-bundle-sha256"), 0),
    (("checked_closure_metrics", "campaign_v32_bundle_accounting", "new_checked_theorem_count"), 755),
    (("promotion_gates", "full_alpha_empty_context_compilation", "checked"), 3971.0),
    (("promotion_gates", "full_alpha_empty_context_compilation", "missing"), False),
    (("promotion_gates", "complete_constructive_alpha_v32_research", "independent_lean_bundle_verified"), 1),
    (("promotion_gates", "complete_constructive_alpha_v32_research", "ordinary_principal_count"), 11),
    (("promotion_gates", "source_integrity", "source_bound_theorem_count"), 3796),
))
def test_actual_metric_types_full_coverage_and_no_support_doublecount(metadata_projection_only, path, value):
    with pytest.raises(verifier.ReleaseError):
        _metadata_check(metadata_projection_only, metrics=_changed(metadata_projection_only.metrics, path, value, explicit=True))


@pytest.mark.parametrize("field", ROW_FIELDS)
def test_one_parent_row_field_change_is_rejected_before_new_family_checks(metadata_projection_only, field):
    value = metadata_projection_only
    # The first inherited v31 admission has the matching historical field name.
    old = value.catalog["theorems"][3222]
    target = field.replace("alpha_v32_frontier_enrollment", "alpha_v31_frontier_enrollment")
    assert target in old
    catalog = _changed(value.catalog, ("theorems", 3222, target))
    with pytest.raises(verifier.ReleaseError, match="historical theorem"):
        verifier._verify_rows(catalog, value.parent, value.evidence, value.documents)


@pytest.mark.parametrize("attack", (
    "family_missing", "family_duplicate", "family_reordered", "family_tuple", "foreign_family",
    "principal_missing", "principal_duplicate", "principal_reordered", "principal_foreign",
    "principal_wrong_node", "principal_wrong_statement", "principal_unchecked", "principal_boolean_nodes",
    "owned_missing", "owned_foreign", "owned_wrong_id",
))
def test_actual_family_and_twelve_principal_inventory_is_exact(metadata_projection_only, attack):
    value = metadata_projection_only
    report = deepcopy(value.evidence.report)
    families = report["families"]
    principals = families[0]["principal_roots"]
    if attack == "family_missing":
        families.pop()
    elif attack == "family_duplicate":
        families.append(deepcopy(families[0]))
    elif attack == "family_reordered":
        families.reverse()
    elif attack == "family_tuple":
        report["families"] = tuple(families)
    elif attack == "foreign_family":
        families[0]["slug"] = "unreviewed"
    elif attack == "principal_missing":
        principals.pop()
    elif attack == "principal_duplicate":
        principals[1] = deepcopy(principals[0])
    elif attack == "principal_reordered":
        principals.reverse()
    elif attack == "principal_foreign":
        principals[0]["name"] = "zero_add"
    elif attack.startswith("principal_"):
        key, changed = {
            "principal_wrong_node": ("node_id", 0), "principal_wrong_statement": ("statement_sha256", "0" * 64),
            "principal_unchecked": ("complete_ordinary_ha_checked", False), "principal_boolean_nodes": ("ordinary_certificate_nodes", True),
        }[attack]
        principals[0][key] = changed
    else:
        owned = families[0]["owned_node_ids"]
        first = next(iter(owned))
        if attack == "owned_missing":
            del owned[first]
        elif attack == "owned_foreign":
            owned["zero_add"] = 0
        else:
            owned[first] = 0
    with pytest.raises((verifier.ReleaseError, audit.AuditError)):
        verifier._verify_rows(value.catalog, value.parent, replace(value.evidence, report=report), value.documents)


@pytest.mark.parametrize("count", (0, 11, 13, True, 12.0))
def test_twelve_actual_principals_cannot_be_recounted_or_retyped(metadata_projection_only, count):
    value = metadata_projection_only
    evidence = replace(value.evidence, report={**value.evidence.report, "ordinary_principal_count": count})
    with pytest.raises(verifier.ReleaseError, match="principal"):
        verifier._verify_rows(value.catalog, value.parent, evidence, value.documents)
    with pytest.raises(verifier.ReleaseError, match="principal"):
        _metadata_check(replace(value, evidence=evidence))


@pytest.mark.parametrize("attack", ("missing", "extra", "duplicate", "foreign_role", "foreign_sha", "wrong_size", "boolean_size", "extra_field", "changed_receipt"))
def test_actual_document_inventory_and_receipt_are_non_substitutable(metadata_projection_only, attack):
    value = metadata_projection_only
    catalog = dict(value.catalog)
    records = list(catalog["evidence_documents"])
    path = builder.relative(Path(__file__))
    index = next(i for i, row in enumerate(records) if row["path"] == path)
    if attack == "missing":
        records.pop(index)
    elif attack == "extra":
        records.append({"path": "unreviewed.txt", "bytes": 1, "sha256": "0" * 64, "role": "unreviewed"})
    elif attack == "duplicate":
        records.append(records[index])
    else:
        records[index] = dict(records[index])
        field, changed = {"foreign_role": ("role", "trusted receipt"), "foreign_sha": ("sha256", "0" * 64),
            "wrong_size": ("bytes", records[index]["bytes"] + 1), "boolean_size": ("bytes", True),
            "extra_field": ("accepted", True), "changed_receipt": ("role", records[index]["role"])}[attack]
        records[index][field] = changed
    catalog["evidence_documents"] = records
    artifacts = value.artifacts
    if attack == "changed_receipt":
        payloads = dict(artifacts._payloads)
        payloads[builder.DEFAULT_RECEIPT] += b" "
        artifacts = verifier._ReleaseArtifacts(payloads)
    with pytest.raises(ValueError):
        verifier._documents(catalog, value.parent, value.evidence, artifacts)


class _BoundedSelection:
    def __init__(self, start, count, expected, phase):
        self.start, self.count, self.expected, self.phase = start, count, expected, phase
        self.ids, self.results = (), []

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        eligible = [item for item in items if self.phase == "all" or
                    ("current_runtime_metadata_only" in item.fixturenames) == (self.phase == "metadata")]
        selected = eligible[self.start:] if self.count is None else eligible[self.start:self.start + self.count]
        dropped = [item for item in items if item not in selected]
        items[:] = selected
        if dropped:
            config.hook.pytest_deselected(items=dropped)
        self.ids = tuple(item.nodeid for item in items)
        if not self.ids or len(self.ids) != len(set(self.ids)) or self.expected is not None and len(self.ids) != self.expected:
            raise pytest.UsageError("the exact bounded case inventory changed")

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.failed or report.skipped:
            self.results.append((report.nodeid, report.when, report.outcome, hasattr(report, "wasxfail")))


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    parser.add_argument("--expect", type=int)
    parser.add_argument("--phase", choices=("all", "syntax", "metadata"), default="all")
    args, pytest_args = parser.parse_known_args(argv)
    if args.start < 0 or args.count is not None and args.count <= 0:
        parser.error("invalid bounded case window")
    plugin = _BoundedSelection(args.start, args.count, args.expect, args.phase)
    status = int(pytest.main([str(Path(__file__)), *(pytest_args or ["-q"])], plugins=[plugin]))
    elapsed = time.monotonic() - _STARTED
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    if "--collect-only" not in pytest_args:
        calls = {name for name, when, outcome, xfail in plugin.results if when == "call" and outcome == "passed" and not xfail}
        if status == 0 and (calls != set(plugin.ids) or any(outcome != "passed" or xfail for _, _, outcome, xfail in plugin.results)):
            status = 1
    if elapsed > 180 or rss > 1536 * 1024 * 1024 or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175):
        status = 1
    print(json.dumps({"status": status, "selected_unique_cases": len(plugin.ids),
        "node_ids_sha256": sha256("\n".join(sorted(plugin.ids)).encode()).hexdigest(),
        "seconds": elapsed, "cpu_seconds": usage.ru_utime + usage.ru_stime,
        "peak_rss_bytes": rss, "cpu_limits": [170, 175], "wall_alarm_seconds": 180}, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(_main())
