"""Exact v31 authority, source, transport and release-mutation regressions."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import check_alpha_v31_completed_lower as audit
import build_peano_library_channels_v31 as builder
import verify_peano_library_channels_v31 as verifier
from peano_lab.library.theorems import TheoremSpec


@pytest.fixture
def exact_row():
    source = "peano-lab/py/peano_lab/library/example_candidate.py"
    test = "peano-lab/py/tests/test_example_candidate.py"
    rfc = "research/arithmetic-library/example-rfc-v1.md"
    artifact = "research/arithmetic-library/artifacts/example-proof-bundle-v1.json"
    receipt = builder.relative(builder.DEFAULT_RECEIPT)
    documents = {path: {"path": path, "bytes": 11, "role": "test-only syntax fixture",
                        "sha256": sha256(path.encode()).hexdigest()}
                 for path in (source, test, rfc, artifact, receipt, audit.PARENT_PATH)}
    spec = TheoremSpec("example", "forall x. x = x", (), ("intro x", "refl"), "Reflexivity.")
    entry = SimpleNamespace(spec=spec, source_module=source, enrollment_origin=SimpleNamespace(value="ha"))
    item = SimpleNamespace(slug="example", artifact=artifact, artifact_sha256=documents[artifact]["sha256"],
                           rfc=rfc, modules=(SimpleNamespace(path=source),))
    family = {"slug": "example", "rows": [{"name": "example", "node_id": 0,
              "proof_nodes": 2, "proof_depth": 2, "proof_objects": 2, "proof_edges": 1, "reused_objects": 0}],
              "bundle": {"dependency_edges_including_packaging": 1, "nodes_including_packaging_root": 2,
                         "packaging_root_id": 1}}
    row = builder._frontier_row(entry, 3222, item, family, documents)
    return row, entry, item, family, documents


def test_exact_row_matches_independent_contract(exact_row):
    row, entry, item, family, documents = exact_row
    verifier._row(row, entry, 3222, family, item, documents)


@pytest.mark.parametrize("field,value", (
    ("statement", "forall x. x = 0"), ("name", "foreign"), ("summary", "Different statement."),
    ("script", ["sorry"]), ("script", ["DNE"]), ("dependencies", ["foreign"]),
    ("checked_use", False), ("checked_use", 1), ("body_checked", False), ("body_checked", 1),
    ("membership", "stable"), ("evidence_status", "body_checked"), ("enrollment_index", 3223),
    ("enrollment_index", True), ("enrollment_origin", "k3b"), ("provenance", ["stable"]),
    ("proof_tag", "UNREGISTERED"), ("frontier_campaign", "foreign"),
    ("statement_sha256", "0" * 64), ("script_sha256", "0" * 64), ("dependencies_sha256", "0" * 64),
    ("summary_sha256", "0" * 64), ("logical_spec_sha256", "0" * 64),
))
def test_exact_row_rejects_statement_script_membership_and_identity_mutations(exact_row, field, value):
    row, entry, item, family, documents = exact_row
    row[field] = value
    with pytest.raises(verifier.ReleaseError):
        verifier._row(row, entry, 3222, family, item, documents)


@pytest.mark.parametrize("field", ("checked_use", "statement", "empty_context_closure", "source", "evidence_links"))
def test_exact_row_requires_all_fields(exact_row, field):
    row, entry, item, family, documents = exact_row
    del row[field]
    with pytest.raises(verifier.ReleaseError):
        verifier._row(row, entry, 3222, family, item, documents)


@pytest.mark.parametrize("section,field,value", (
    ("empty_context_closure", "kernel_mode", "classical"),
    ("empty_context_closure", "status", "unchecked"),
    ("empty_context_closure", "bundle_node_id", 1),
    ("empty_context_closure", "bundle_node_id", False),
    ("empty_context_closure", "certificate_sha256", "0" * 64),
    ("empty_context_closure", "bundle_root_id", 0),
    ("empty_context_closure", "bundle_path", "../../outside.json"),
    ("empty_context_closure", "closure_kind", "trusted_receipt"),
    ("empty_context_closure", "node_statement_sha256", "0" * 64),
    ("empty_context_closure", "bundle_dependency_edge_count", True),
    ("alpha_v31_frontier_enrollment", "first_enrolled_version", "v30"),
    ("alpha_v31_frontier_enrollment", "bundle_node_id", 1),
    ("alpha_v31_frontier_enrollment", "source_sha256", "0" * 64),
    ("alpha_v31_frontier_enrollment", "test_sha256", "0" * 64),
    ("alpha_v31_frontier_enrollment", "rfc_sha256", "0" * 64),
    ("alpha_v31_frontier_enrollment", "body_receipt_sha256", "0" * 64),
    ("alpha_v31_frontier_enrollment", "parent_catalog_sha256", "0" * 64),
    ("body_receipt", "status", "accepted_by_hash"),
    ("body_receipt", "proof_nodes", 0), ("body_receipt", "dne_command_count", 1),
    ("source", "path", "unreviewed.py"), ("source", "sha256", "0" * 64),
))
def test_exact_row_rejects_closure_provenance_and_receipt_mutations(exact_row, section, field, value):
    row, entry, item, family, documents = exact_row
    row[section][field] = value
    with pytest.raises(verifier.ReleaseError):
        verifier._row(row, entry, 3222, family, item, documents)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "wrong_selector", "wrong_role", "wrong_digest", "extra"))
def test_evidence_links_remain_exact(exact_row, mutation):
    row, entry, item, family, documents = exact_row
    links = row["evidence_links"]
    if mutation == "missing":
        links.pop()
    elif mutation == "duplicate":
        links[1] = deepcopy(links[0])
    elif mutation == "extra":
        links.append(deepcopy(links[0]))
    else:
        key = {"wrong_selector": "selector", "wrong_role": "role", "wrong_digest": "document_sha256"}[mutation]
        links[3][key] = "wrong"
    with pytest.raises(verifier.ReleaseError):
        verifier._row(row, entry, 3222, family, item, documents)


def test_receipt_metadata_cannot_mint_live_proof_or_publication_authority():
    with pytest.raises(audit.AuditError, match="saved report"):
        audit.FreshProofAudit(object(), "0" * 64, {"success": True}, 1)
    with pytest.raises(verifier.ReleaseError, match="saved metadata"):
        verifier.LiveReleaseContext(object(), {"success": True}, {}, {}, {}, [])
    with pytest.raises(verifier.ReleaseError, match="fresh proof"):
        verifier.context_from_live_audit({"success": True})
    with pytest.raises(ValueError, match="saved proof"):
        builder.build_payloads({"success": True})


def test_publication_entrypoint_always_runs_actual_fresh_proof_gates(monkeypatch):
    calls = []
    value = object()
    monkeypatch.setattr(builder, "preflight_inputs", lambda: calls.append("preflight"))
    monkeypatch.setattr(audit, "verify_in_fresh_windows", lambda: calls.append("proofs") or value)
    monkeypatch.setattr(verifier, "context_from_live_audit", lambda received: calls.append(received) or "checked")
    assert verifier.verify_for_publication() == "checked"
    assert calls == ["preflight", "proofs", value]


@pytest.mark.parametrize("entrypoint", (builder.build_payloads, verifier.verify_for_publication))
def test_invalid_historical_metadata_stops_before_any_expensive_proof_job(monkeypatch, entrypoint):
    calls = []

    def invalid_metadata():
        calls.append("preflight")
        raise ValueError("historical input failed exact-byte preflight")

    monkeypatch.setattr(builder, "preflight_inputs", invalid_metadata)
    monkeypatch.setattr(audit, "verify_in_fresh_windows", lambda: calls.append("must not run"))
    with pytest.raises(ValueError, match="exact-byte preflight"):
        entrypoint()
    assert calls == ["preflight"]


def test_exact_archives_and_resolver_are_bound_to_live_proof_sources():
    historical = builder.historical_evidence
    assert "scripts/alpha_v31_historical_evidence.py" in audit.CONTROL_SOURCES
    assert set(historical.archive_paths()) <= set(audit.CONTROL_SOURCES)
    assert len(historical.archive_paths()) == 5
    assert "scripts/alpha_v31_historical_evidence.py" in builder.CONTROL_DOCUMENTS
    assert "scripts/test_alpha_v31_historical_evidence.py" in builder.CONTROL_DOCUMENTS


def _message(**changes):
    envelope = {"schema": audit.WORKER_SCHEMA, "kind": "novelty", "slug": "all",
                "nonce": "1" * 64, "binding_sha256": "2" * 64,
                "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
                "peak_rss_bytes": 12345, "report": {"test": "syntax-only"}}
    envelope.update(changes)
    return audit.canonical(envelope)


@pytest.mark.parametrize("changes", (
    {"schema": "old"}, {"kind": "family"}, {"slug": "foreign"}, {"nonce": "0" * 64},
    {"binding_sha256": "0" * 64}, {"extra": True}, {"peak_rss_bytes": True},
    {"peak_rss_bytes": 0}, {"peak_rss_bytes": 1536 * 1024 * 1024 + 1},
    {"limits": {"cpu": [171, 176], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024}},
    {"limits": {"cpu": [170, 175], "wall_seconds": 181, "max_rss_bytes": 1536 * 1024 * 1024}},
))
def test_worker_nonce_binding_scope_and_original_limits_fail_closed(monkeypatch, changes):
    monkeypatch.setattr(audit, "_validate_report", lambda *_args, **_kwargs: None)
    with pytest.raises(audit.AuditError):
        audit._validate_message(_message(**changes), kind="novelty", slug="all", nonce="1" * 64, binding="2" * 64)


@pytest.mark.parametrize("payload", (
    b"", b"{}", b'{"schema":1,"schema":2}\n', b'{"a":NaN}\n', b"[1,2]\n",
    b"x" * (128 * 1024 + 1), b"\xff", b'{"a": 1}\n',
))
def test_malformed_duplicate_or_oversized_worker_json_is_rejected(payload):
    with pytest.raises(audit.AuditError):
        audit._validate_message(payload, kind="novelty", slug="all", nonce="1" * 64, binding="2" * 64)


def test_original_proof_and_catalogue_limits_remain_unchanged():
    from peano_lab.library.proof_bundle import DEFAULT_BUNDLE_LIMITS
    import serve_lean_strands
    assert audit.CPU_LIMITS == (170, 175)
    assert audit.WALL_SECONDS == 180
    assert audit.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert builder.MAX_CATALOG_BYTES == serve_lean_strands.MAX_EXPLORER_CATALOG_BYTES == 64 * 1024 * 1024
    assert DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64_000_000
    assert DEFAULT_BUNDLE_LIMITS.max_nodes == 4096


def test_exact_promotion_inventory_is_nineteen_unique_families_and_574_rows():
    entries = audit.registry()
    assert len(entries) == 19 and sum(item.frontier_count for item in entries) == 574
    assert len({item.artifact for item in entries}) == 19
    assert len({name for item in entries for name in item.principal_roots}) == sum(len(item.principal_roots) for item in entries)
    assert "multiplicative" not in " ".join(name for item in entries for name in item.principal_roots)


def test_catalogue_writer_never_overwrites_an_existing_release(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    path = tmp_path / "already.json"
    path.write_bytes(b"historic")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        builder.check_or_write({path: b"new"}, check=False)
    assert path.read_bytes() == b"historic"


@pytest.mark.parametrize("payload", (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b"[]"))
def test_release_json_rejects_duplicate_fields_and_nonfinite_values(payload):
    with pytest.raises(ValueError):
        builder.strict_json(payload)


def test_logical_digest_detects_mutation_without_full_serialization():
    value = {"theorems": [{"name": "x", "statement": "forall x. x=x"}], "checked_use": True}
    expected = sha256(builder.compact(value).encode()).hexdigest()
    assert verifier._content_digest(value) == expected
    value["theorems"][0]["statement"] = "forall x. x=0"
    assert verifier._content_digest(value) != expected
