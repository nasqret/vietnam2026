"""Bounded fail-closed mutation audit for fully checked additive Alpha v29."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

import build_peano_library_channels_v29 as builder
import verify_peano_library_channels_v29 as verifier
from peano_lab.library import editions_v29 as v29


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
def test_every_immutable_v28_parent_artifact_is_authenticated(monkeypatch, seal: str) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    monkeypatch.setattr(builder, seal, "0" * 64)
    with pytest.raises(ValueError, match="sealed Alpha-v28 parent artifact changed"):
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


def test_all_647_immutable_v28_evidence_bindings_are_preserved(release) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    assert len(parent["evidence_documents"]) == 647
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
    with pytest.raises(ValueError, match="immutable Alpha-v28 evidence-document binding"):
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
    with pytest.raises(ValueError, match="quadratic-reciprocity|Alpha-v28 evidence-document"):
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
    with pytest.raises(ValueError, match="immutable Alpha-v28 evidence-document binding"):
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


@pytest.mark.parametrize("index", (0, 431, 432, 1775, 1829, 1889, 1948, 1949, 2007, 2008, 2079, 2080, 2137, 2138, 2359, 2479, 2559))
def test_any_immutable_historical_v28_row_mutation_is_rejected(release, index: int) -> None:
    parent, rows, documents, checked = _rows(release)
    _copy_row(rows, index)["summary"] = "forged historical theorem"
    with pytest.raises(ValueError, match="immutable Alpha-v28 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("field,value", (
    ("enrollment_index", False), ("checked_use", 1), ("body_checked", 1),
))
def test_historical_rows_preserve_json_types_not_python_boolean_aliases(
    release, field: str, value: object
) -> None:
    parent, rows, documents, checked = _rows(release)
    row = _copy_row(rows, 0)
    assert row[field] == value and type(row[field]) is not type(value)
    row[field] = value
    with pytest.raises(ValueError, match="immutable Alpha-v28 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_historical_documents_preserve_nested_zero_and_boolean_types(release, monkeypatch) -> None:
    _path, documents, parent = _inherited_qr(release)
    record = {
        "path": "research/arithmetic-library/historical-diagnostic.md",
        "bytes": 7, "sha256": "a" * 64, "role": "historical review",
        "diagnostic": {"missing": 0, "checked": True},
    }
    parent["evidence_documents"].insert(0, deepcopy(record))
    documents[record["path"]] = deepcopy(record)
    documents[record["path"]]["diagnostic"]["missing"] = False
    monkeypatch.setattr(Path, "read_bytes", lambda _path: pytest.fail("read before type check"))
    with pytest.raises(ValueError, match="immutable Alpha-v28 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("missing", (True, False))
def test_missing_or_extra_frontier_is_rejected(release, missing: bool) -> None:
    parent, rows, documents, checked = _rows(release)
    if missing:
        rows.pop()
    else:
        rows.append(rows[-1])
    with pytest.raises(ValueError, match="2,764-row parent or additive frontier"):
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
        ("dne_command_count", False),
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
    _frontier(rows)["alpha_v29_frontier_enrollment"][field] = forged
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
    with pytest.raises(ValueError, match="independently checked priority-layer proof bundle"):
        verifier._verify_rows(rows, parent, documents, ())


def test_missing_exact_checked_proof_position_is_rejected(release) -> None:
    parent, rows, documents, checked = release
    bundle, receipt, positions = checked
    missing = dict(positions)
    missing.pop(v29.FRONTIER_NEW_NAMES[0])
    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, (bundle, receipt, missing))


@pytest.mark.parametrize("forbidden", sorted(verifier.FORBIDDEN_UNPROVED_CLAIMS))
def test_still_open_lattice_and_analytic_goals_cannot_be_claimed(
    forbidden: str,
) -> None:
    names = set(v29.FRONTIER_NEW_NAMES)
    names.add(forbidden)
    with pytest.raises(ValueError, match="unproved ambitious boundary"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize("missing", verifier.FRONTIER_ROOT_NAMES)
def test_a_real_major_priority_layer_boundary_cannot_be_removed(missing: str) -> None:
    names = set(v29.FRONTIER_NEW_NAMES)
    names.remove(missing)
    with pytest.raises(ValueError, match="constructive boundary root"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize(
    ("name", "digest"), verifier.INDEPENDENT_PRIORITY_LAYER_STATEMENT_SHA256.items()
)
def test_major_priority_layer_formulas_have_independently_pinned_digests(
    name: str, digest: str
) -> None:
    assert sha256(v29.ALPHA_EDITION.by_name[name].spec.statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", verifier.INDEPENDENT_PRIORITY_LAYER_STATEMENT_SHA256)
def test_independent_major_statement_digest_forgery_is_rejected(monkeypatch, name: str) -> None:
    monkeypatch.setitem(verifier.INDEPENDENT_PRIORITY_LAYER_STATEMENT_SHA256, name, "0" * 64)
    with pytest.raises(ValueError, match="independently pinned priority-layer statement"):
        verifier._verify_truthful_boundaries(set(v29.FRONTIER_NEW_NAMES))


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
    from peano_lab.library.alpha_enrollment_v29 import FRONTIER_V29_EXPECTED_COUNT
    assert v29.EXPECTED_ALPHA_V29_COUNT == 2_764 + FRONTIER_V29_EXPECTED_COUNT
    assert FRONTIER_V29_EXPECTED_COUNT > 0
    assert len(v29.STABLE_SPECS) == 432
    assert set(verifier.EXPECTED_CAMPAIGNS) == {
        "prime_valuation_support", "continued_fraction_approximation", "euler_totient", "squarefree_perfect_power", "odd_prime_lte",
    }
    assert sum(verifier.EXPECTED_CAMPAIGNS.values()) == FRONTIER_V29_EXPECTED_COUNT
    assert not verifier.FORBIDDEN_UNPROVED_CLAIMS.intersection(v29.FRONTIER_NEW_NAMES)


def test_exact_unconditional_priority_layer_endpoints_are_accepted() -> None:
    specs = {name: entry.spec for name, entry in v29.ALPHA_EDITION.by_name.items()}
    verifier._verify_unconditional_endpoints(specs)


@pytest.mark.parametrize(
    "name,old,new",
    (
        ("continued_fraction_convergent_best_approximation", "forall a b s i u v.", "exists a b s i u v."),
        ("continued_fraction_convergent_best_approximation", "BestApproximationSecondKind(a,b,u,v)", "BestApproximationSecondKind(b,a,u,v)"),
        ("continued_fraction_convergent_best_approximation_signed", "Convergent(s,i,u,v) -> ", ""),
        ("totient_euler_product_formula", "~(n = 0) -> ", ""),
        ("totient_euler_product_formula", "exists f g l t.", "forall f g l t."),
        ("totient_euler_product_formula", "Phi(n,t)", "Phi(n,n)"),
        ("positive_squarefree_kernel_and_power_profile", "~(n = 0) -> ", ""),
        ("positive_squarefree_kernel_and_power_profile", "u = r", "u = u"),
        ("positive_squarefree_kernel_and_power_profile", "v = s", "v = v"),
        ("positive_squarefree_kernel_and_power_profile", "forall u v.", "exists u v."),
        ("positive_squarefree_kernel_and_power_profile", "PowerProfile(n,w)", "PowerProfile(r,w)"),
        ("odd_prime_lifting_the_exponent", "Prime(p) -> ", ""),
        ("odd_prime_lifting_the_exponent", "Lt(2,p) -> ", ""),
        ("odd_prime_lifting_the_exponent", "Lt(y,x) -> ", ""),
        ("odd_prime_lifting_the_exponent", "~(y=0) -> ", ""),
        ("odd_prime_lifting_the_exponent", "~(n=0) -> ", ""),
        ("odd_prime_lifting_the_exponent", "Dvd(p,d) -> ", ""),
        ("odd_prime_lifting_the_exponent", "~Dvd(p,x*y) -> ", ""),
        ("odd_prime_lifting_the_exponent", "exists X Y D.", "forall X Y D."),
        ("odd_prime_lifting_the_exponent", "LiftedPowerDifference(p,x,y,n,a+b,X,Y,D)", "LiftedPowerDifference(p,x,y,n,a,X,Y,D)"),
        ("odd_prime_lifting_the_exponent_value", "Pow(x,n,X) -> ", ""),
        ("odd_prime_lifting_the_exponent_value", "X=Y+D -> ", ""),
        ("odd_prime_lifting_the_exponent_value", "PowerValuation(p,D,a+b)", "PowerValuation(p,D,a)"),
    ),
)
def test_independent_endpoint_ast_rejects_false_or_weakened_claims(name, old, new):
    from peano_lab.kernel.formulas import pretty_formula

    specs = {name: entry.spec for name, entry in v29.ALPHA_EDITION.by_name.items()}
    original = specs[name]
    surface = verifier.INDEPENDENT_EXACT_ENDPOINTS[name]
    changed = surface.replace(old, new)
    assert changed != surface
    statement = pretty_formula(verifier._endpoint_formula(changed), [])
    specs[name] = replace(original, statement=statement)
    with pytest.raises(ValueError, match="exact unconditional endpoint"):
        verifier._verify_unconditional_endpoints(specs)


@pytest.mark.parametrize("name", tuple(verifier.INDEPENDENT_EXACT_ENDPOINTS))
def test_supplied_witness_or_false_extra_premise_is_rejected_independently(name):
    specs = {name: entry.spec for name, entry in v29.ALPHA_EDITION.by_name.items()}
    original = specs[name]
    specs[name] = replace(original, statement=f"(0 = 1) -> ({original.statement})")
    with pytest.raises(ValueError, match="exact unconditional endpoint"):
        verifier._verify_unconditional_endpoints(specs)


@pytest.mark.parametrize(
    "path",
    (
        builder.EXPLORER_BUILDER,
        builder.EXPLORER_RENDERER, builder.EXPLORER_TEST,
        builder.LOCAL_DISPLAY_ADAPTER, builder.LOCAL_DISPLAY_TEST,
        builder.CHANNEL_EXPORTER, builder.CHANNEL_VERIFIER, builder.CHANNEL_VERIFIER_TEST,
        builder.CAMPAIGN_EXTENSION, builder.HISTORICAL_PRESENTATION_SUCCESSOR,
        builder.HISTORICAL_PRESENTATION_TEST, *builder.HISTORICAL_ATLAS_INPUTS,
    ),
)
def test_priority_layer_notation_and_publication_controls_are_mandatory(release, path: str) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    catalog["evidence_documents"] = [
        item for item in catalog["evidence_documents"] if item["path"] != path
    ]
    with pytest.raises(ValueError, match="actual-proof control document"):
        verifier._documents(catalog)


@pytest.mark.parametrize(
    "actual,expected",
    (
        (True, 1), (False, 0), (1, True), (0, False),
        ({"kernel_calls": True}, {"kernel_calls": 1}),
        ([{"dne_command_count": False}], [{"dne_command_count": 0}]),
    ),
)
def test_numeric_evidence_cannot_be_replaced_with_boolean_aliases(actual, expected) -> None:
    assert not verifier._exact_json(actual, expected)


def test_nested_exact_evidence_comparison_accepts_only_matching_types() -> None:
    evidence = {"checked_use": True, "calls": 1, "nested": [{"dne": 0}], "optional": None}
    assert verifier._exact_json(deepcopy(evidence), evidence)


@pytest.mark.parametrize(
    "payload,reason",
    (
        ('{"checked_use":false,"checked_use":true}', "duplicate JSON field"),
        ('{"nested":{"proof_nodes":0,"proof_nodes":1}}', "duplicate JSON field"),
        ('{"proof_nodes":NaN}', "non-finite JSON"),
        ('{"proof_nodes":Infinity}', "non-finite JSON"),
        ('[]', "JSON object"),
    ),
)
def test_ambiguous_or_nonfinite_release_json_is_rejected(tmp_path, payload, reason) -> None:
    source = tmp_path / "untrusted-catalog.json"
    source.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match=reason):
        verifier._load(source)


@pytest.mark.parametrize("reject", (False, True))
def test_principal_runtime_gate_releases_each_large_certificate(
    monkeypatch, capsys, reject: bool
) -> None:
    from types import SimpleNamespace
    events = []
    class Replay:
        def __call__(self, name, *, edition):
            events.append(("replay", name, edition))
            return SimpleNamespace(certificate=name, formula=f"target:{name}")
        def cache_clear(self):
            events.append(("release",))
    def checked(context, certificate, formula):
        assert context == () and formula == f"target:{certificate}"
        events.append(("kernel", certificate))
        return not reject
    monkeypatch.setattr(verifier, "FRONTIER_ROOT_NAMES", ("first", "second"))
    monkeypatch.setattr(verifier.v29, "replay", Replay())
    monkeypatch.setattr(verifier, "check", checked)
    monkeypatch.setattr(verifier.gc, "collect", lambda: events.append(("collect",)))
    if reject:
        with pytest.raises(ValueError, match="kernel rejected exact new campaign root"):
            verifier._verify_principal_roots()
        names = ("first",)
    else:
        verifier._verify_principal_roots()
        names = ("first", "second")
    assert events == [
        event for name in names
        for event in (
            ("replay", name, "alpha"), ("kernel", name), ("release",), ("collect",)
        )
    ]
    assert capsys.readouterr().out.splitlines() == [
        line for name in names
        for line in (
            (f"checking Alpha-v29 principal root: {name}",)
            if reject else (
                f"checking Alpha-v29 principal root: {name}",
                f"accepted Alpha-v29 principal root: {name}",
            )
        )
    ]

def test_frozen_formula_compactor_is_inherited_not_rebound(release) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    record = next(item for item in parent["evidence_documents"]
                  if item["path"] == builder.FORMULA_COMPACTOR)
    assert builder.FORMULA_COMPACTOR not in builder.CONTROL_DOCUMENTS
    assert release[2][builder.FORMULA_COMPACTOR] == record
    payload = (builder.ROOT / builder.FORMULA_COMPACTOR).read_bytes()
    assert len(payload) == record["bytes"]
    assert sha256(payload).hexdigest() == record["sha256"]


def test_inherited_formula_compactor_record_cannot_be_removed(release) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    catalog["evidence_documents"] = [
        record for record in catalog["evidence_documents"]
        if record["path"] != builder.FORMULA_COMPACTOR
    ]
    with pytest.raises(ValueError, match="immutable Alpha-v28 evidence-document binding"):
        verifier._documents(catalog)


def test_every_historical_provider_is_authenticated_even_if_unused(monkeypatch) -> None:
    from peano_lab.library import campaign_priority_layer_closure as closure
    parent = verifier._load(builder.PARENT_ALPHA)
    calls = []
    original = closure.validate_parent_provider_bytes
    def validate():
        calls.append("all")
        return original()
    monkeypatch.setattr(closure, "validate_parent_provider_bytes", validate)
    builder._validate_parent(parent)
    assert calls == ["all"]
    assert len(original()) == 18


def test_removed_historical_provider_inventory_is_not_tolerated(monkeypatch) -> None:
    from peano_lab.library import campaign_priority_layer_closure as closure
    parent = verifier._load(builder.PARENT_ALPHA)
    monkeypatch.setattr(closure, "validate_parent_provider_bytes", lambda: tuple(range(17)))
    with pytest.raises(ValueError, match="eighteen immutable Alpha-v28 proof providers"):
        builder._validate_parent(parent)


def test_current_release_cannot_remove_an_inherited_evidence_record() -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    parent["evidence_documents"].pop()
    with pytest.raises(ValueError, match="immutable Alpha-v28 document inventory"):
        builder._validate_parent(parent)


@pytest.mark.parametrize("path", tuple(builder.HISTORICAL_ATLAS_INPUTS))
def test_historical_atlas_parent_is_literal_pinned_evidence(monkeypatch, path) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    monkeypatch.setitem(builder.HISTORICAL_ATLAS_INPUTS, path, "0" * 64)
    with pytest.raises(ValueError, match="immutable Alpha-v28 atlas input changed"):
        builder._validate_parent(parent)


@pytest.mark.parametrize("mutation", ("extra_authority", "missing_field", "numeric_boolean"))
def test_exact_topology_record_cannot_invent_or_change_authority(release, mutation: str) -> None:
    metrics = verifier._load(builder.DEFAULT_ALPHA_METRICS)
    topology = metrics["dependency_graph"]
    if mutation == "extra_authority":
        topology["unproved_goal_closed"] = True
    elif mutation == "missing_field":
        topology.pop("transitive_reduction_preserves_reachability")
    else:
        topology["transitive_reduction_preserves_reachability"] = 1
    with pytest.raises(ValueError, match="independently derived checked-DAG topology"):
        verifier._verify_topology(release[1], metrics)
