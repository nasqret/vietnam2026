"""Bounded fail-closed mutation audit for fully checked additive Alpha v25."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

import build_peano_library_channels_v25 as builder
import verify_peano_library_channels_v25 as verifier
from peano_lab.library import editions_v25 as v25


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog, parent=parent)
    # Exactly one unchanged-kernel plus independently compiled Lean run.
    checked = builder._checked_bundle()
    return parent["theorems"], catalog["theorems"], documents, checked


def _rows(release):
    parent, current, documents, checked = release
    return parent, list(current), documents, checked


def _copy_row(rows, index: int):
    rows[index] = deepcopy(rows[index])
    return rows[index]


def _frontier(rows):
    return _copy_row(rows, builder.EXPECTED_PARENT_COUNT)


def _inherited_qr(release):
    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = deepcopy(release[2][path])
    return path, {path: record}, {"evidence_documents": [deepcopy(record)]}


def test_exact_immutable_dependency_closed_additive_release_is_accepted(release) -> None:
    parent, rows, documents, checked = release
    verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    "seal",
    (
        "EXPECTED_PARENT_ALPHA_SHA256", "EXPECTED_PARENT_METRICS_SHA256",
        "EXPECTED_PARENT_GRAPH_SHA256", "EXPECTED_PARENT_CHANNELS_SHA256",
    ),
)
def test_every_immutable_v24_parent_artifact_is_authenticated(monkeypatch, seal: str) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    monkeypatch.setattr(builder, seal, "0" * 64)
    with pytest.raises(ValueError, match="sealed Alpha-v24 parent artifact changed"):
        builder._validate_parent(parent)


@pytest.mark.parametrize("path", tuple(builder.CONTROL_DOCUMENTS))
def test_every_actual_proof_and_reviewed_definition_control_digest_is_authenticated(
    release, path: str
) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    item = next(row for row in catalog["evidence_documents"] if row["path"] == path)
    item["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="actual-proof control document"):
        verifier._documents(catalog)


@pytest.mark.parametrize("path", (builder.DEFINITION_REGISTRY, builder.DEFINITION_GRAPH_SOURCE))
def test_reviewed_definition_dag_sources_are_not_optional(release, path: str) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    catalog["evidence_documents"] = [
        item for item in catalog["evidence_documents"] if item["path"] != path
    ]
    with pytest.raises(ValueError, match="actual-proof control document"):
        verifier._documents(catalog)


def test_all_492_immutable_v24_evidence_bindings_are_preserved(release) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    assert len(parent["evidence_documents"]) == 492
    verifier._verify_inherited_evidence_documents(release[2], parent)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("sha256", "0" * 64), ("bytes", 17_229_310),
        ("role", "invented authority"),
        ("path", "book/_static/pa-proof-explorer/api/current-corpus.json"),
    ),
)
def test_inherited_qr_metadata_mutation_fails_before_reading_corpus(
    release, monkeypatch, field: str, forged: object
) -> None:
    path, documents, parent = _inherited_qr(release)
    documents[path][field] = forged
    monkeypatch.setattr(Path, "read_bytes", lambda _path: pytest.fail("read immutable corpus"))
    with pytest.raises(ValueError, match="immutable Alpha-v24 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize(
    ("field", "forged"),
    (("sha256", "0" * 64), ("bytes", 17_229_310), ("bytes", True)),
)
def test_synchronized_parent_and_current_qr_forgery_cannot_replace_pins(
    release, field: str, forged: object
) -> None:
    path, documents, parent = _inherited_qr(release)
    documents[path][field] = forged
    parent["evidence_documents"][0][field] = forged
    with pytest.raises(ValueError, match="quadratic-reciprocity corpus catalog binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "inventory"))
def test_inherited_qr_binding_must_exist_exactly_once(release, mutation: str) -> None:
    _path, documents, parent = _inherited_qr(release)
    if mutation == "missing":
        parent["evidence_documents"] = []
    elif mutation == "duplicate":
        parent["evidence_documents"].append(deepcopy(parent["evidence_documents"][0]))
    else:
        parent["evidence_documents"] = None
    with pytest.raises(ValueError, match="quadratic-reciprocity|Alpha-v24 evidence-document"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("field", ("sha256", "bytes", "role"))
def test_other_historical_evidence_bindings_are_preserved_without_hashing_files(
    release, monkeypatch, field: str
) -> None:
    _path, documents, parent = _inherited_qr(release)
    old = {
        "path": "research/arithmetic-library/historical-review.md",
        "bytes": 9, "sha256": "a" * 64, "role": "immutable historical source",
    }
    documents[old["path"]] = deepcopy(old)
    parent["evidence_documents"].insert(0, deepcopy(old))
    documents[old["path"]][field] = 10 if field == "bytes" else "forged"
    monkeypatch.setattr(Path, "read_bytes", lambda _path: pytest.fail("hashed unrelated file"))
    with pytest.raises(ValueError, match="immutable Alpha-v24 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("kind", ("missing", "short", "same_length"))
def test_frozen_qr_bytes_fail_closed_without_writing_immutable_file(
    release, monkeypatch, kind: str
) -> None:
    path, documents, parent = _inherited_qr(release)
    if kind == "missing":
        def missing(_path):
            raise OSError("missing immutable corpus")
        monkeypatch.setattr(Path, "read_bytes", missing)
        message = "corpus evidence is unavailable"
    else:
        forged = b"forged corpus"
        if kind == "same_length":
            monkeypatch.setattr(builder, "EXPECTED_IMMUTABLE_QR_CORPUS_BYTES", len(forged))
            documents[path]["bytes"] = len(forged)
            parent["evidence_documents"][0]["bytes"] = len(forged)
        monkeypatch.setattr(Path, "read_bytes", lambda _path: forged)
        message = "corpus evidence bytes changed"
    with pytest.raises(ValueError, match=message):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("index", (0, 431, 432, 1775, 1829, 1889, 1948, 1949, 2007))
def test_any_immutable_historical_v24_row_mutation_is_rejected(release, index: int) -> None:
    parent, rows, documents, checked = _rows(release)
    _copy_row(rows, index)["summary"] = "forged historical theorem"
    with pytest.raises(ValueError, match="immutable Alpha-v24 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("missing", (True, False))
def test_missing_or_extra_frontier_is_rejected(release, missing: bool) -> None:
    parent, rows, documents, checked = _rows(release)
    if missing:
        rows.pop()
    else:
        rows.append(rows[-1])
    with pytest.raises(ValueError, match="2,008-row parent or additive frontier"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("name", verifier.FRONTIER_ROOT_NAMES)
def test_missing_exact_major_constructive_root_is_rejected(release, name: str) -> None:
    parent, rows, documents, checked = _rows(release)
    index = next(index for index, row in enumerate(rows) if row["name"] == name)
    _copy_row(rows, index)["name"] = f"forged_{name}"
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("frontier_campaign", "invented"), ("statement", "forall n. n = 0"),
        ("statement_sha256", "0" * 64), ("summary", "forged content"),
        ("summary_sha256", "0" * 64), ("dependencies", ["bertrand_strict"]),
        ("dependencies_sha256", "0" * 64), ("script", ["DNE"]),
        ("script_sha256", "0" * 64), ("checked_use", False), ("checked_use", 1),
        ("body_checked", False), ("body_checked", 1), ("evidence_status", "body_checked"),
        ("membership", "stable"), ("enrollment_index", 999999),
        ("enrollment_origin", "stable"), ("provenance", ["stable"]),
        ("proof_tag", "forged"), ("logical_spec_sha256", "0" * 64),
    ),
)
def test_frontier_source_bound_field_mutations_are_rejected(
    release, field: str, forged: object
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)[field] = forged
    with pytest.raises(ValueError, match=f"source-bound field '{field}'"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("field", ("sha256", "kind", "path"))
def test_frontier_source_authority_mutation_is_rejected(release, field: str) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["source"][field] = "forged"
    with pytest.raises(ValueError, match="source-bound field 'source'"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("mutation", ("missing", "extra"))
def test_frontier_unknown_or_missing_authority_is_rejected(release, mutation: str) -> None:
    parent, rows, documents, checked = _rows(release)
    row = _frontier(rows)
    if mutation == "missing":
        row.pop("summary_sha256")
    else:
        row["invented_authority"] = True
    with pytest.raises(ValueError, match="exact immutable field set"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("command_count", -1), ("dependency_count", -1), ("dne_command_count", 1),
        ("name", "forged"), ("proof_nodes", 0), ("proof_depth", 0),
        ("proof_objects", 0), ("proof_edges", -1), ("reused_objects", -1),
        ("status", "unchecked"),
    ),
)
def test_actual_kernel_body_receipt_forgery_is_rejected(
    release, field: str, forged: object
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["body_receipt"][field] = forged
    with pytest.raises(ValueError, match="original-kernel body receipt"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1), ("bundle_campaign", "invented"),
        ("bundle_sha256", "0" * 64), ("campaign", "invented"),
        ("parent_catalog_sha256", "0" * 64), ("source_sha256", "0" * 64),
        ("test_sha256", "0" * 64), ("rfc_sha256", "0" * 64),
        ("body_receipt_sha256", "0" * 64),
    ),
)
def test_frontier_proof_enrollment_forgery_is_rejected(
    release, field: str, forged: object
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["alpha_v25_frontier_enrollment"][field] = forged
    with pytest.raises(ValueError, match="source/proof enrollment"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1), ("bundle_campaign", "invented"),
        ("bundle_node_count", 0), ("bundle_dependency_edge_count", 0),
        ("bundle_path", "/tmp/forged.json"), ("bundle_root_id", -1),
        ("certificate_sha256", "0" * 64), ("certificate_representation", "unchecked"),
        ("closure_kind", "metadata_only"), ("digest_kind", "statement-sha256"),
        ("kernel_mode", "classical"), ("node_statement_sha256", "0" * 64),
        ("body_proof_nodes", 0), ("body_proof_depth", -1), ("status", "unchecked"),
    ),
)
def test_actual_checked_proof_binding_forgery_is_rejected(
    release, field: str, forged: object
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["empty_context_closure"][field] = forged
    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("index", range(6))
def test_any_missing_source_or_proof_link_is_rejected(release, index: int) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"].pop(index)
    with pytest.raises(ValueError, match="source/test/RFC/proof/parent link"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("index", range(6))
def test_any_evidence_document_digest_forgery_is_rejected(release, index: int) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"][index]["document_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence-document digest"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("field", ("kind", "role", "selector"))
def test_evidence_link_authority_mutation_is_rejected(release, field: str) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"][0][field] = "forged"
    with pytest.raises(ValueError, match="evidence-link authority or order"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("mutation", ("duplicate", "reorder", "selector"))
def test_evidence_link_topology_or_proof_selector_mutations_fail_closed(
    release, mutation: str
) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    if mutation == "duplicate":
        links.append(deepcopy(links[0]))
        message = "duplicated a source/proof evidence link"
    elif mutation == "reorder":
        links[0], links[1] = links[1], links[0]
        message = "evidence-link authority or order"
    else:
        next(item for item in links if item["path"] == builder.CLOSURE_ARTIFACT)[
            "selector"
        ] = "nodes[id=-1]"
        message = "exact proof-node selector"
    with pytest.raises(ValueError, match=message):
        verifier._verify_rows(rows, parent, documents, checked)


def test_missing_actual_checked_proof_bundle_is_rejected(release) -> None:
    parent, rows, documents, _checked = release
    with pytest.raises(ValueError, match="independently checked breakthrough-layer proof bundle"):
        verifier._verify_rows(rows, parent, documents, ())


def test_missing_exact_checked_proof_position_is_rejected(release) -> None:
    parent, rows, documents, checked = release
    bundle, receipt, positions = checked
    missing = dict(positions)
    missing.pop(v25.FRONTIER_NEW_NAMES[0])
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, (bundle, receipt, missing))


@pytest.mark.parametrize("forbidden", sorted(verifier.FORBIDDEN_UNPROVED_CLAIMS))
def test_open_matrix_hensel_and_generalized_crt_goals_cannot_be_claimed(
    forbidden: str,
) -> None:
    names = set(v25.FRONTIER_NEW_NAMES)
    names.add(forbidden)
    with pytest.raises(ValueError, match="unproved ambitious boundary"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize("missing", verifier.FRONTIER_ROOT_NAMES)
def test_a_real_major_breakthrough_boundary_cannot_be_removed(missing: str) -> None:
    names = set(v25.FRONTIER_NEW_NAMES)
    names.remove(missing)
    with pytest.raises(ValueError, match="constructive boundary root"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize(
    ("name", "digest"), verifier.INDEPENDENT_BREAKTHROUGH_STATEMENT_SHA256.items()
)
def test_major_breakthrough_formulas_have_independently_pinned_digests(
    name: str, digest: str
) -> None:
    assert sha256(v25.ALPHA_EDITION.by_name[name].spec.statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", verifier.INDEPENDENT_BREAKTHROUGH_STATEMENT_SHA256)
def test_independent_major_statement_digest_forgery_is_rejected(monkeypatch, name: str) -> None:
    monkeypatch.setitem(verifier.INDEPENDENT_BREAKTHROUGH_STATEMENT_SHA256, name, "0" * 64)
    with pytest.raises(ValueError, match="independently pinned breakthrough statement"):
        verifier._verify_truthful_boundaries(set(v25.FRONTIER_NEW_NAMES))


@pytest.mark.parametrize("scope", ("promotion", "proof_bundle"))
@pytest.mark.parametrize("forged", (False, None, 1, "true"))
def test_real_independently_compiled_lean_acceptance_cannot_be_forged(
    release, scope: str, forged: object
) -> None:
    promotion = deepcopy(builder._promotion_payload(release[3]))
    proof = promotion["proof_bundle"]
    (promotion if scope == "promotion" else proof)["independent_lean_bundle_verified"] = forged
    with pytest.raises(ValueError, match="independently compiled Lean proof-bundle verification"):
        verifier._verify_independent_lean_evidence(promotion, proof)


def test_current_release_counts_and_open_boundaries_are_exact() -> None:
    assert v25.EXPECTED_ALPHA_V25_COUNT == 2_080
    assert len(v25.STABLE_SPECS) == 432
    assert verifier.EXPECTED_CAMPAIGNS == {
        "matrix_cofactor_expansion": 29,
        "polynomial_taylor_hensel": 19,
        "generalized_crt_compatibility": 24,
    }
    assert not verifier.FORBIDDEN_UNPROVED_CLAIMS.intersection(v25.FRONTIER_NEW_NAMES)
