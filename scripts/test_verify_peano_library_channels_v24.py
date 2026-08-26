"""Bounded fail-closed mutation audit for the additive Alpha-v24 release."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

import build_peano_library_channels_v24 as builder
import verify_peano_library_channels_v24 as verifier
from peano_lab.library import editions_v24 as v24


@pytest.fixture(scope="module")
def release():
    parent = verifier._load(builder.PARENT_ALPHA)
    catalog = verifier._load(builder.DEFAULT_ALPHA)
    documents = verifier._documents(catalog, parent=parent)
    # Exactly one original-kernel + independently compiled Lean run is shared
    # by the whole mutation suite; do not duplicate complete historical rows.
    checked = builder._checked_bundle()
    return parent["theorems"], catalog["theorems"], documents, checked


def _rows(release):
    parent, actual, documents, checked = release
    return parent, list(actual), documents, checked


def _copy_row(rows, index: int):
    rows[index] = deepcopy(rows[index])
    return rows[index]


def _frontier(rows):
    return _copy_row(rows, builder.EXPECTED_PARENT_COUNT)


def _inherited_qr_evidence(release):
    path = builder._repository_path(builder.IMMUTABLE_QR_CORPUS)
    record = deepcopy(release[2][path])
    return path, {path: record}, {"evidence_documents": [deepcopy(record)]}


def test_exact_immutable_dependency_closed_additive_release_is_accepted(release) -> None:
    parent, rows, documents, checked = release
    verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    "seal",
    (
        "EXPECTED_PARENT_ALPHA_SHA256",
        "EXPECTED_PARENT_METRICS_SHA256",
        "EXPECTED_PARENT_GRAPH_SHA256",
        "EXPECTED_PARENT_CHANNELS_SHA256",
    ),
)
def test_each_frozen_v23_parent_artifact_digest_is_independently_authenticated(
    monkeypatch: pytest.MonkeyPatch, seal: str
) -> None:
    parent = verifier._load(builder.PARENT_ALPHA)
    monkeypatch.setattr(builder, seal, "0" * 64)

    with pytest.raises(ValueError, match="sealed Alpha-v23 parent artifact changed"):
        builder._validate_parent(parent)


@pytest.mark.parametrize(
    "path",
    (
        builder.ADMISSION_TEST,
        builder.CLOSURE_TEST,
        builder.CLOSURE_MODULE,
        builder.CLOSURE_ARTIFACT,
        builder.CLOSURE_RECEIPT,
        builder.ADMISSION_RFC,
    ),
)
def test_every_actual_research_control_document_digest_is_authenticated(
    release, path: str
) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    row = next(item for item in catalog["evidence_documents"] if item["path"] == path)
    row["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="actual-proof control document"):
        verifier._documents(catalog)


def test_missing_frozen_v23_parent_evidence_document_fails_closed(release) -> None:
    catalog = deepcopy(verifier._load(builder.DEFAULT_ALPHA))
    parent = builder._repository_path(builder.PARENT_ALPHA)
    catalog["evidence_documents"] = [
        item for item in catalog["evidence_documents"] if item["path"] != parent
    ]

    with pytest.raises(ValueError, match="immutable sealed Alpha-v23 parent"):
        verifier._documents(catalog)


def test_exact_inherited_qr_catalog_record_and_frozen_bytes_are_authenticated(
    release,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)

    assert documents[path]["bytes"] == 17_229_311
    assert documents[path]["sha256"] == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )
    verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("sha256", "0" * 64),
        ("bytes", 17_229_310),
        ("role", "invented historical proof authority"),
        ("path", "book/_static/pa-proof-explorer/api/current-corpus.json"),
    ),
)
def test_inherited_qr_catalog_mutation_fails_before_any_corpus_read(
    release,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    forged: object,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)
    documents[path][field] = forged
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda _path: pytest.fail("a changed historical binding read immutable corpus bytes"),
    )

    with pytest.raises(ValueError, match="immutable Alpha-v23 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


def test_missing_inherited_qr_document_is_rejected_before_disk_access(
    release,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)
    documents.pop(path)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda _path: pytest.fail("a missing historical binding read immutable corpus bytes"),
    )

    with pytest.raises(ValueError, match="immutable Alpha-v23 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize(
    ("field", "forged"),
    (("sha256", "0" * 64), ("bytes", 17_229_310), ("bytes", True)),
)
def test_synchronized_parent_and_current_qr_forgery_cannot_replace_frozen_pins(
    release,
    field: str,
    forged: object,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)
    documents[path][field] = forged
    parent["evidence_documents"][0][field] = forged

    with pytest.raises(ValueError, match="quadratic-reciprocity corpus catalog binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "inventory"))
def test_parent_qr_binding_must_exist_exactly_once(
    release,
    mutation: str,
) -> None:
    _path, documents, parent = _inherited_qr_evidence(release)
    if mutation == "missing":
        parent["evidence_documents"] = []
    elif mutation == "duplicate":
        parent["evidence_documents"].append(
            deepcopy(parent["evidence_documents"][0])
        )
    else:
        parent["evidence_documents"] = None

    with pytest.raises(ValueError, match="quadratic-reciprocity|Alpha-v23 evidence-document"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("field", ("sha256", "bytes", "role"))
def test_every_historical_evidence_binding_is_preserved_without_hashing_all_files(
    release,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)
    historical_path = "research/arithmetic-library/historical-review.md"
    historical = {
        "path": historical_path,
        "bytes": 9,
        "sha256": "a" * 64,
        "role": "reviewed immutable historical source",
    }
    documents[historical_path] = deepcopy(historical)
    parent["evidence_documents"].insert(0, deepcopy(historical))
    documents[historical_path][field] = 10 if field == "bytes" else "forged"
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda _path: pytest.fail("historical metadata validation hashed repository files"),
    )

    with pytest.raises(ValueError, match="immutable Alpha-v23 evidence-document binding"):
        verifier._verify_inherited_evidence_documents(documents, parent)
    assert path in documents


def test_missing_frozen_qr_corpus_bytes_fail_closed_without_modifying_file(
    release,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _path, documents, parent = _inherited_qr_evidence(release)

    def unavailable(path: Path) -> bytes:
        assert path == builder.IMMUTABLE_QR_CORPUS
        raise OSError("immutable corpus disappeared")

    monkeypatch.setattr(Path, "read_bytes", unavailable)

    with pytest.raises(ValueError, match="quadratic-reciprocity corpus evidence is unavailable"):
        verifier._verify_inherited_evidence_documents(documents, parent)


def test_changed_frozen_qr_corpus_byte_length_fails_closed_without_file_write(
    release,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _path, documents, parent = _inherited_qr_evidence(release)
    monkeypatch.setattr(Path, "read_bytes", lambda _path: b"forged corpus")

    with pytest.raises(ValueError, match="quadratic-reciprocity corpus evidence bytes changed"):
        verifier._verify_inherited_evidence_documents(documents, parent)


def test_same_length_forged_qr_corpus_bytes_fail_exact_sha256(
    release,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, documents, parent = _inherited_qr_evidence(release)
    forged = b"forged corpus"
    monkeypatch.setattr(builder, "EXPECTED_IMMUTABLE_QR_CORPUS_BYTES", len(forged))
    documents[path]["bytes"] = len(forged)
    parent["evidence_documents"][0]["bytes"] = len(forged)
    monkeypatch.setattr(Path, "read_bytes", lambda _path: forged)

    with pytest.raises(ValueError, match="quadratic-reciprocity corpus evidence bytes changed"):
        verifier._verify_inherited_evidence_documents(documents, parent)


@pytest.mark.parametrize("index", (0, 431, 432, 1_775, 1_829, 1_889, 1_890, 1_948))
def test_any_historical_v23_stable_or_alpha_row_mutation_is_rejected(
    release, index: int
) -> None:
    parent, rows, documents, checked = _rows(release)
    _copy_row(rows, index)["summary"] = "forged immutable historical theorem"

    with pytest.raises(ValueError, match="immutable Alpha-v23 parent row"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_historical_parent_row_reordering_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    rows[0], rows[1] = rows[1], rows[0]

    with pytest.raises(ValueError, match="immutable theorem order"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("missing", (True, False))
def test_missing_or_extra_unreviewed_additive_frontier_is_rejected(
    release, missing: bool
) -> None:
    parent, rows, documents, checked = _rows(release)
    if missing:
        rows.pop()
    else:
        rows.append(rows[-1])

    with pytest.raises(ValueError, match="1,949-row parent or additive frontier"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("name", verifier.FRONTIER_ROOT_NAMES)
def test_missing_exact_major_constructive_root_is_rejected(release, name: str) -> None:
    parent, rows, documents, checked = _rows(release)
    index = next(position for position, row in enumerate(rows) if row["name"] == name)
    _copy_row(rows, index)["name"] = f"forged_{name}"

    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("name", "honest", "forged"),
    (
        (
            "beta_signed_matrix_minor_exists",
            "forall pb pc nb nc q r d.",
            "forall pb pc nb nc q r d z.",
        ),
        (
            "beta_horner_derivative_exists_unique",
            "forall b c t l. exists n z.",
            "forall b c t l. exists n.",
        ),
        (
            "crt_prefix_lcm_exists_unique",
            "forall b c l. exists x.",
            "forall b c l. exists y.",
        ),
        (
            "crt_pairwise_coprime_prefix_canonical_exists_unique",
            "forall r s b c l.",
            "forall r s b c l z.",
        ),
    ),
)
def test_exact_matrix_polynomial_and_finite_crt_statement_tampering_is_rejected(
    release,
    name: str,
    honest: str,
    forged: str,
) -> None:
    parent, rows, documents, checked = _rows(release)
    index = next(position for position, row in enumerate(rows) if row["name"] == name)
    row = _copy_row(rows, index)
    assert row["statement"].count(honest) == 1
    row["statement"] = row["statement"].replace(honest, forged)

    with pytest.raises(ValueError, match="source-bound field 'statement'"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_forward_additive_frontier_reordering_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    index = builder.EXPECTED_PARENT_COUNT
    rows[index], rows[index + 1] = rows[index + 1], rows[index]

    with pytest.raises(ValueError, match="exact additive order"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("frontier_campaign", "invented"),
        ("statement", "forall n. n = 0"),
        ("statement_sha256", "0" * 64),
        ("summary", "forged mathematical content"),
        ("summary_sha256", "0" * 64),
        ("dependencies", ["bertrand_strict"]),
        ("dependencies_sha256", "0" * 64),
        ("script", ["DNE"]),
        ("script_sha256", "0" * 64),
        ("checked_use", False),
        ("checked_use", 1),
        ("body_checked", False),
        ("body_checked", 1),
        ("evidence_status", "body_checked"),
        ("membership", "stable"),
        ("enrollment_index", 1_000_000),
        ("enrollment_origin", "stable"),
        ("provenance", ["stable"]),
        ("proof_tag", "forged"),
        ("logical_spec_sha256", "0" * 64),
    ),
)
def test_frontier_source_bound_field_mutations_are_rejected(
    release, field: str, forged
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
        row["unreviewed_authority"] = True

    with pytest.raises(ValueError, match="exact immutable field set"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("command_count", -1),
        ("dependency_count", -1),
        ("dne_command_count", 1),
        ("name", "invented"),
        ("proof_nodes", 0),
        ("proof_depth", 0),
        ("proof_objects", 0),
        ("proof_edges", -1),
        ("reused_objects", -1),
        ("status", "unchecked"),
    ),
)
def test_frontier_actual_kernel_body_receipt_mutations_are_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["body_receipt"][field] = forged

    with pytest.raises(ValueError, match="original-kernel body receipt"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1),
        ("bundle_campaign", "invented"),
        ("bundle_sha256", "0" * 64),
        ("campaign", "invented"),
        ("parent_catalog_sha256", "0" * 64),
        ("source_sha256", "0" * 64),
        ("test_sha256", "0" * 64),
        ("rfc_sha256", "0" * 64),
        ("body_receipt_sha256", "0" * 64),
    ),
)
def test_frontier_source_and_proof_enrollment_forgery_is_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["alpha_v24_frontier_enrollment"][field] = forged

    with pytest.raises(ValueError, match="source/proof enrollment"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("bundle_node_id", -1),
        ("bundle_campaign", "invented"),
        ("bundle_node_count", 0),
        ("bundle_dependency_edge_count", 0),
        ("bundle_path", "/tmp/forged.json"),
        ("bundle_root_id", -1),
        ("certificate_sha256", "0" * 64),
        ("certificate_representation", "unchecked"),
        ("closure_kind", "metadata_only"),
        ("digest_kind", "statement-sha256"),
        ("kernel_mode", "classical"),
        ("node_statement_sha256", "0" * 64),
        ("body_proof_nodes", 0),
        ("body_proof_depth", -1),
        ("status", "unchecked"),
    ),
)
def test_frontier_actual_checked_proof_binding_mutations_are_rejected(
    release, field: str, forged
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["empty_context_closure"][field] = forged

    with pytest.raises(ValueError, match="actual checked proof binding"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("index", range(6))
def test_any_missing_independent_source_or_proof_link_is_rejected(
    release, index: int
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"].pop(index)

    with pytest.raises(ValueError, match="source/test/RFC/proof/parent link"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_duplicate_evidence_link_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    links.append(deepcopy(links[0]))

    with pytest.raises(ValueError, match="duplicated a source/proof evidence link"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("index", range(6))
def test_any_frontier_evidence_document_digest_forgery_is_rejected(
    release, index: int
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"][index]["document_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="evidence-document digest"):
        verifier._verify_rows(rows, parent, documents, checked)


@pytest.mark.parametrize("field", ("kind", "role", "selector"))
def test_document_evidence_link_authority_mutation_is_rejected(
    release, field: str
) -> None:
    parent, rows, documents, checked = _rows(release)
    _frontier(rows)["evidence_links"][0][field] = "forged"

    with pytest.raises(ValueError, match="evidence-link authority or order"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_evidence_link_reordering_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    links[0], links[1] = links[1], links[0]

    with pytest.raises(ValueError, match="evidence-link authority or order"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_frontier_proof_node_selector_forgery_is_rejected(release) -> None:
    parent, rows, documents, checked = _rows(release)
    links = _frontier(rows)["evidence_links"]
    next(item for item in links if item["path"] == builder.CLOSURE_ARTIFACT)[
        "selector"
    ] = "nodes[id=-1]"

    with pytest.raises(ValueError, match="exact proof-node selector"):
        verifier._verify_rows(rows, parent, documents, checked)


def test_missing_independently_checked_proof_bundle_is_rejected(release) -> None:
    parent, rows, documents, _checked = release

    with pytest.raises(ValueError, match="independently checked research-layer proof bundle"):
        verifier._verify_rows(rows, parent, documents, ())


def test_missing_exact_checked_proof_position_is_rejected(release) -> None:
    parent, rows, documents, checked = release
    bundle, receipt, positions = checked
    missing = dict(positions)
    missing.pop(v24.FRONTIER_NEW_NAMES[0])

    with pytest.raises(ValueError, match="no independently checked proof node"):
        verifier._verify_rows(rows, parent, documents, (bundle, receipt, missing))


@pytest.mark.parametrize("forbidden", sorted(verifier.FORBIDDEN_UNPROVED_CLAIMS))
def test_genuinely_open_matrix_and_other_blueprint_goals_cannot_be_claimed(
    forbidden: str,
) -> None:
    names = set(v24.FRONTIER_NEW_NAMES)
    names.add(forbidden)

    with pytest.raises(ValueError, match="unproved ambitious boundary"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize("missing", verifier.FRONTIER_ROOT_NAMES)
def test_a_real_major_campaign_boundary_cannot_be_removed(missing: str) -> None:
    names = set(v24.FRONTIER_NEW_NAMES)
    names.remove(missing)

    with pytest.raises(ValueError, match="constructive boundary root"):
        verifier._verify_truthful_boundaries(names)


@pytest.mark.parametrize(
    ("name", "digest"), verifier.INDEPENDENT_RESEARCH_STATEMENT_SHA256.items()
)
def test_major_research_formulas_have_independently_pinned_exact_digests(
    name: str, digest: str
) -> None:
    source = v24.ALPHA_EDITION.by_name[name].spec.statement

    assert sha256(source.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", verifier.INDEPENDENT_RESEARCH_STATEMENT_SHA256)
def test_independent_major_statement_digest_forgery_is_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setitem(verifier.INDEPENDENT_RESEARCH_STATEMENT_SHA256, name, "0" * 64)

    with pytest.raises(ValueError, match="independently pinned research statement"):
        verifier._verify_truthful_boundaries(set(v24.FRONTIER_NEW_NAMES))


@pytest.mark.parametrize("scope", ("promotion", "proof_bundle"))
@pytest.mark.parametrize("forged", (False, None, 1, "true"))
def test_missing_real_independent_lean_acceptance_is_rejected(
    release, scope: str, forged
) -> None:
    promotion = deepcopy(builder._promotion_payload(release[3]))
    target = promotion if scope == "promotion" else promotion["proof_bundle"]
    target["independent_lean_bundle_verified"] = forged

    with pytest.raises(ValueError, match="independently compiled Lean"):
        verifier._verify_independent_lean_evidence(promotion, promotion["proof_bundle"])


def test_actual_independent_lean_acceptance_is_preserved_in_both_scopes(release) -> None:
    promotion = builder._promotion_payload(release[3])

    verifier._verify_independent_lean_evidence(promotion, promotion["proof_bundle"])


@pytest.mark.parametrize(
    ("status", "output"),
    (
        (1, "ACCEPT\tnodes=0\troot=0\n"),
        (0, "REJECT\tforged mathematical proof\n"),
        (0, "ACCEPT\tnodes=0\troot=0\n"),
    ),
)
def test_actual_compiled_lean_rejection_cannot_be_masked_by_boolean_claims(
    release,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    output: str,
) -> None:
    monkeypatch.setattr(
        builder.subprocess,
        "run",
        lambda *_arguments, **_options: SimpleNamespace(
            returncode=status, stdout=output
        ),
    )

    with pytest.raises(ValueError, match="independently compiled Lean verifier rejected"):
        builder._checked_bundle()


def test_missing_independent_compiled_lean_executable_fails_closed(
    release,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*_arguments, **_options):
        raise OSError("compiled Lean verifier is missing")

    monkeypatch.setattr(builder.subprocess, "run", unavailable)

    with pytest.raises(ValueError, match="independently compiled Lean proof verifier is unavailable"):
        builder._checked_bundle()


@pytest.mark.parametrize(
    "family",
    (
        "matrix_determinant_minors",
        "polynomial_hensel",
        "generalized_crt_fold",
    ),
)
def test_every_reviewed_campaign_is_genuinely_nonempty(family: str) -> None:
    assert verifier.EXPECTED_CAMPAIGNS[family] > 0
