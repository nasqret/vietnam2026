"""The production sync gate keeps checked proofs and notation in separate DAGs."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sync_constructive_grand_campaign as synchronization  # noqa: E402


CAMPAIGN = ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
@pytest.fixture(scope="module")
def evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    campaign = json.loads(CAMPAIGN.read_bytes())
    # Build directly from the current source of truth: ongoing Alpha work may
    # legitimately change blueprint vocabulary before snapshots are refreshed.
    definitions = synchronization.build_definition_graph(campaign)
    version = campaign["meta"]["current_alpha_version"]
    catalog_path = ROOT / "artifacts" / "peano-library" / "alpha" / f"catalog-{version}.json"
    catalog_bytes = catalog_path.read_bytes()
    catalog = json.loads(catalog_bytes)
    return campaign, definitions, catalog, sha256(catalog_bytes).hexdigest()


def _audit(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    *,
    campaign: dict[str, Any] | None = None,
    definitions: dict[str, Any] | None = None,
    catalog: dict[str, Any] | None = None,
    digest: str | None = None,
) -> synchronization.CampaignDagAudit:
    original_campaign, original_definitions, original_catalog, original_digest = evidence
    return synchronization.validate_campaign_dags(
        original_campaign if campaign is None else campaign,
        definition_graph=original_definitions if definitions is None else definitions,
        catalog=original_catalog if catalog is None else catalog,
        catalog_sha256=original_digest if digest is None else digest,
    )


def _catalog_row(
    catalog: dict[str, Any],
    index: int,
    **updates: object,
) -> dict[str, Any]:
    """Copy one metadata row only; never duplicate the 28 MiB sealed catalog."""

    changed = dict(catalog)
    rows = list(catalog["theorems"])
    rows[index] = {**rows[index], **updates}
    changed["theorems"] = rows
    return changed


def _milestone(
    campaign: dict[str, Any],
    index: int,
    **updates: object,
) -> dict[str, Any]:
    changed = dict(campaign)
    rows = list(campaign["nodes"])
    rows[index] = {**rows[index], **updates}
    changed["nodes"] = rows
    return changed


def _graph_row(
    graph: dict[str, Any],
    field: str,
    index: int,
    **updates: object,
) -> dict[str, Any]:
    changed = dict(graph)
    rows = list(graph[field])
    rows[index] = {**rows[index], **updates}
    changed[field] = rows
    return changed


def test_current_alpha_exposes_one_theorem_dag_and_distinct_definition_dags(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    result = _audit(evidence)
    campaign, definitions, catalog, digest = evidence

    assert result.alpha_version == campaign["meta"]["current_alpha_version"]
    assert result.catalog_sha256 == digest
    assert result.theorem_count == len(catalog["theorems"]) >= 2_008
    assert result.theorem_edge_count == sum(len(row["dependencies"]) for row in catalog["theorems"])
    assert result.milestone_count == len(campaign["nodes"]) >= 144
    assert result.milestone_proof_edge_count == sum(len(row["deps"]) for row in campaign["nodes"])
    assert result.definition_count == len(definitions["definitions"]) >= 164
    assert result.definition_edge_count == sum(
        len(row["dependencies"]) for row in definitions["definitions"]
    )
    assert result.reviewed_definition_count == len(definitions["reviewed_definitions"]) >= 109
    assert result.reviewed_definition_edge_count == sum(
        len(row["dependencies"]) for row in definitions["reviewed_definitions"]
    )
    assert (
        result.milestone_usage_edge_count,
        result.statement_usage_edge_count,
        result.declared_notation_edge_count,
    ) == (
        definitions["milestone_usage_edge_count"],
        definitions["statement_usage_edge_count"],
        definitions["declared_notation_edge_count"],
    )
    assert result.theorem_dag_sha256 == synchronization._digest(
        [
            {"name": row["name"], "dependencies": row["dependencies"]}
            for row in catalog["theorems"]
        ]
    )
    assert result.milestone_dag_sha256 == synchronization._digest(
        [
            {"id": row["id"], "deps": row["deps"], "layer": row["layer"]}
            for row in campaign["nodes"]
        ]
    )
    assert result.definition_dag_sha256 == synchronization._digest(
        [
            {"name": row["name"], "dependencies": row["dependencies"]}
            for row in definitions["definitions"]
        ]
    )
    assert result.reviewed_definition_dag_sha256 == synchronization._digest(
        [
            {"id": row["id"], "name": row["name"], "dependencies": row["dependencies"]}
            for row in definitions["reviewed_definitions"]
        ]
    )
    assert len(
        {
            result.theorem_dag_sha256,
            result.milestone_dag_sha256,
            result.definition_dag_sha256,
            result.reviewed_definition_dag_sha256,
        }
    ) == 4
    with pytest.raises(FrozenInstanceError):
        result.theorem_count = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("index", "updates", "message"),
    (
        (1, {"name": "zero_add"}, "duplicated"),
        (2, {"dependencies": ["zero_add", "zero_add"]}, "repeats a proof dependency"),
        (2, {"dependencies": ["UnknownTheorem"]}, "missing, forward, or circular"),
        (0, {"dependencies": ["add_comm"]}, "missing, forward, or circular"),
        (2, {"dependencies": ["add_comm"]}, "missing, forward, or circular"),
        (2, {"checked_use": False}, "unchecked theorem"),
        (2, {"body_checked": False}, "unchecked theorem"),
        (2, {"empty_context_closure": {"status": "unchecked"}}, "empty-context closure"),
        (2, {"membership": "stable", "evidence_status": "alpha_closed"}, "conflates Stable"),
        (2, {"statement_sha256": "unchecked"}, "statement_sha256"),
        (2, {"statement": "forall n. n = S n"}, "changed its sealed statement"),
        (2, {"script": ["admit"]}, "changed its sealed proof script"),
        (2, {"script": []}, "no exact proof script"),
        (2, {"enrollment_index": 1}, "immutable enrollment order"),
    ),
)
def test_checked_theorem_dag_rejects_unsound_or_non_topological_catalog_rows(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    index: int,
    updates: dict[str, object],
    message: str,
) -> None:
    catalog = _catalog_row(evidence[2], index, **updates)

    with pytest.raises(synchronization.CampaignDagError, match=message):
        _audit(evidence, catalog=catalog)


@pytest.mark.parametrize(
    ("updates", "message"),
    (
        ({"schema": "peano-library-alpha-snapshot-v23"}, "invalid or stale schema"),
        ({"channel": "stable"}, "Alpha channel"),
        ({"theorem_count": 2_007}, "checked-theorem counts"),
        ({"checked_use_count": 2_007}, "checked-theorem counts"),
        ({"edge_count": 6_422}, "proof-edge count"),
    ),
)
def test_checked_theorem_dag_rejects_stale_catalog_inventory(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    updates: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(synchronization.CampaignDagError, match=message):
        _audit(evidence, catalog={**evidence[2], **updates})


def test_current_alpha_catalog_is_bound_to_its_immutable_public_release(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    with pytest.raises(synchronization.CampaignDagError, match="immutable sealed digest"):
        _audit(evidence, digest="0" * 64)


@pytest.mark.parametrize(
    ("index", "updates", "message"),
    (
        (1, {"id": "T01"}, "duplicated"),
        (0, {"kind": "unknown"}, "invalid kind"),
        (0, {"id": "G001"}, "wrong namespace"),
        (0, {"status": "unchecked_placeholder"}, "unreviewed status"),
        (0, {"title": "   "}, "real title"),
        (0, {"layer": 99}, "unknown layer"),
        (3, {"deps": ["T01", "T01"]}, "repeats a proof edge"),
        (2, {"deps": ["T999"]}, "missing proof prerequisite"),
        (0, {"deps": ["T01"]}, "reversed, circular"),
        (2, {"conceptual_refs": ["T999"]}, "missing, repeated"),
        (2, {"conceptual_refs": ["T01", "T01"]}, "missing, repeated"),
    ),
)
def test_milestone_proof_dag_rejects_broken_dependencies_and_fake_evidence(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    index: int,
    updates: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(synchronization.CampaignDagError, match=message):
        _audit(evidence, campaign=_milestone(evidence[0], index, **updates))


def test_conceptual_links_never_become_milestone_proof_prerequisites(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    campaign = evidence[0]
    index = next(index for index, row in enumerate(campaign["nodes"]) if row["deps"])
    changed = _milestone(campaign, index, conceptual_refs=[campaign["nodes"][index]["deps"][0]])

    with pytest.raises(synchronization.CampaignDagError, match="conflates a conceptual link"):
        _audit(evidence, campaign=changed)


def test_closed_milestones_cannot_lose_their_independent_checked_theorem_authority(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    campaign = evidence[0]
    index = next(index for index, row in enumerate(campaign["nodes"]) if row["status"] == "alpha_closed")
    changed = _milestone(
        campaign,
        index,
        evidence={**campaign["nodes"][index]["evidence"], "checked_use": False},
    )

    with pytest.raises(synchronization.CampaignDagError, match="no checked theorem authority"):
        _audit(evidence, campaign=changed)


def test_stable_milestones_cannot_borrow_alpha_only_theorem_membership(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    campaign = evidence[0]
    index = next(index for index, row in enumerate(campaign["nodes"]) if row["status"] == "stable_closed")
    alpha_only = next(row["name"] for row in evidence[2]["theorems"] if row["membership"] == "alpha_only")
    changed = _milestone(
        campaign,
        index,
        evidence={**campaign["nodes"][index]["evidence"], "theorem_name": alpha_only},
    )

    with pytest.raises(synchronization.CampaignDagError, match="non-Stable theorem as Stable"):
        _audit(evidence, campaign=changed)


@pytest.mark.parametrize(
    ("updates", "message"),
    (
        ({"checked_use": True}, "falsely claims checked closure"),
        ({"partial_theorem_name": "missing_theorem"}, "lacks its checked partial theorem"),
        ({"partial_theorem_name": None}, "lacks its checked partial theorem"),
    ),
)
def test_partial_checked_components_never_close_open_research_milestones(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    updates: dict[str, object],
    message: str,
) -> None:
    campaign = evidence[0]
    index = next(index for index, row in enumerate(campaign["nodes"]) if row["id"] == "T13")
    changed = _milestone(
        campaign,
        index,
        status="open",
        evidence={**campaign["nodes"][index]["historical_partial_evidence"], **updates},
    )

    with pytest.raises(synchronization.CampaignDagError, match=message):
        _audit(evidence, campaign=changed)


def test_milestone_evidence_cannot_cite_or_duplicate_unavailable_theorems(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    campaign = evidence[0]
    index = next(index for index, row in enumerate(campaign["nodes"]) if row["id"] == "T09")
    references = campaign["nodes"][index]["evidence"]["theorem_names"]
    changed = _milestone(
        campaign,
        index,
        evidence={**campaign["nodes"][index]["evidence"], "theorem_names": [*references, references[0]]},
    )

    with pytest.raises(synchronization.CampaignDagError, match="repeated or unavailable"):
        _audit(evidence, campaign=changed)


@pytest.mark.parametrize("field", ("node_count", "goal_count", "tool_count", "anchor_count"))
def test_milestone_inventory_metadata_is_audited_before_publication(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    field: str,
) -> None:
    campaign = {**evidence[0], "meta": {**evidence[0]["meta"], field: 0}}

    with pytest.raises(synchronization.CampaignDagError, match="count disagrees"):
        _audit(evidence, campaign=campaign)


def test_campaign_families_cannot_silently_lose_a_goal_browser_route(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    families = list(evidence[0]["families"])
    families[0] = {**families[0], "goal_ids": families[0]["goal_ids"][1:]}

    with pytest.raises(synchronization.CampaignDagError, match="stale goal membership"):
        _audit(evidence, campaign={**evidence[0], "families": families})


@pytest.mark.parametrize(
    ("field", "index", "updates", "message"),
    (
        ("definitions", 1, {"name": "ArithmeticProgression"}, "duplicated"),
        ("definitions", 0, {"dependencies": ["MissingDefinition"]}, "missing, forward"),
        ("definitions", 0, {"topological_layer": 1}, "changed its DAG layer"),
        ("definitions", 0, {"expansion": "forged"}, "campaign expansion"),
        ("definitions", 0, {"expansion_sha256": "0" * 64}, "expansion SHA-256"),
        (
            "reviewed_definitions",
            0,
            {"dependencies": ["MissingReviewedDefinition"]},
            "missing, forward",
        ),
        ("reviewed_definitions", 0, {"topological_layer": 1}, "changed its DAG layer"),
        ("reviewed_definitions", 0, {"expansion_sha256": "unchecked"}, "expansion SHA-256"),
        (
            "reviewed_definitions",
            1,
            {"id": "ND0001"},
            "identifier .* is reused",
        ),
        (
            "definition_edges",
            0,
            {"kind": "proof_dependency"},
            "definition_uses_definition category",
        ),
        (
            "definition_edges",
            0,
            {"target": "T01"},
            "definition_uses_definition category",
        ),
        (
            "milestone_usage_edges",
            0,
            {"kind": "proof_dependency"},
            "masquerade as a theorem proof edge",
        ),
        (
            "milestone_usage_edges",
            0,
            {"source": "At"},
            "wrong graph namespaces",
        ),
        (
            "milestone_usage_edges",
            0,
            {"target": "T01"},
            "wrong graph namespaces",
        ),
    ),
)
def test_notation_dags_can_never_be_conflated_with_theorem_proof_edges(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    field: str,
    index: int,
    updates: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(synchronization.CampaignDagError, match=message):
        _audit(evidence, definitions=_graph_row(evidence[1], field, index, **updates))


@pytest.mark.parametrize(
    "field",
    (
        "definition_count",
        "reviewed_definition_count",
        "definition_edge_count",
        "reviewed_definition_edge_count",
        "statement_usage_edge_count",
        "declared_notation_edge_count",
        "milestone_usage_edge_count",
    ),
)
def test_definition_and_notation_edge_censuses_fail_closed(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    field: str,
) -> None:
    graph = {**evidence[1], field: evidence[1][field] + 1}

    with pytest.raises(synchronization.CampaignDagError, match="disagree"):
        _audit(evidence, definitions=graph)


def test_definitions_cannot_be_replayed_against_a_different_campaign_snapshot(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    graph = {**evidence[1], "campaign_snapshot_sha256": "0" * 64}

    with pytest.raises(synchronization.CampaignDagError, match="different campaign"):
        _audit(evidence, definitions=graph)


def test_duplicate_notation_arrows_are_rejected_even_with_forged_matching_counts(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
) -> None:
    edge = evidence[1]["milestone_usage_edges"][0]
    graph = {
        **evidence[1],
        "milestone_usage_edges": [*evidence[1]["milestone_usage_edges"], edge],
        "milestone_usage_edge_count": evidence[1]["milestone_usage_edge_count"] + 1,
        "statement_usage_edge_count": evidence[1]["statement_usage_edge_count"] + 1,
    }

    with pytest.raises(synchronization.CampaignDagError, match="duplicate edge"):
        _audit(evidence, definitions=graph)


@pytest.mark.parametrize(
    ("payload", "maximum", "message"),
    (
        (b'{"safe":1,"safe":2}', 1024, "repeats JSON field"),
        (b'{"safe":NaN}', 1024, "non-finite JSON constant"),
        (b'{"safe":Infinity}', 1024, "non-finite JSON constant"),
        (b"[]", 1024, "one exact JSON object"),
        (b'{"safe":true}', 4, "safe bounded artifact size"),
    ),
)
def test_product_artifact_loader_rejects_ambiguous_or_unbounded_json(
    tmp_path: Path,
    payload: bytes,
    maximum: int,
    message: str,
) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_bytes(payload)

    with pytest.raises(synchronization.CampaignDagError, match=message):
        synchronization._load_document(artifact, maximum=maximum, context="test evidence")


def test_product_artifact_loader_never_follows_a_symbolic_evidence_source(
    tmp_path: Path,
) -> None:
    original = tmp_path / "actual.json"
    original.write_text('{"safe":true}', encoding="utf-8")
    redirected = tmp_path / "redirected.json"
    redirected.symlink_to(original)

    with pytest.raises(synchronization.CampaignDagError, match="ordinary repository artifact"):
        synchronization._load_document(redirected, maximum=1024, context="test evidence")


def test_json_sync_gate_exposes_exact_machine_readable_dag_identities(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign, definitions, _catalog, _digest = evidence
    _isolate_current_campaign(
        campaign,
        definitions,
        monkeypatch=monkeypatch,
        tmp_path=tmp_path,
    )
    monkeypatch.setattr(sys, "argv", ["sync_constructive_grand_campaign.py", "--check", "--json"])

    assert synchronization.main() == 0
    assert json.loads(capsys.readouterr().out) == asdict(_audit(evidence))


def _isolate_current_campaign(
    campaign: dict[str, Any],
    definitions: dict[str, Any],
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    campaign_path = tmp_path / "campaign.json"
    definition_path = tmp_path / "definitions.json"
    explorer_path = tmp_path / "index.html"
    campaign_path.write_text(json.dumps(campaign, ensure_ascii=False), encoding="utf-8")
    definition_path.write_text(
        json.dumps(definitions, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    snapshot = json.dumps(campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    explorer_path.write_text(
        "<!doctype html>" + synchronization.OPENING + snapshot + synchronization.CLOSING,
        encoding="utf-8",
    )
    monkeypatch.setattr(synchronization, "CAMPAIGN", campaign_path)
    monkeypatch.setattr(synchronization, "EXPLORER", explorer_path)
    monkeypatch.setattr(synchronization, "DEFINITION_GRAPH", definition_path)


def test_standard_sync_gate_reports_both_independent_product_dags(
    evidence: tuple[dict[str, Any], dict[str, Any], dict[str, Any], str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign, definitions, _catalog, _digest = evidence
    _isolate_current_campaign(
        campaign,
        definitions,
        monkeypatch=monkeypatch,
        tmp_path=tmp_path,
    )
    monkeypatch.setattr(sys, "argv", ["sync_constructive_grand_campaign.py", "--check"])

    assert synchronization.main() == 0
    output = capsys.readouterr().out
    audit = _audit(evidence)
    assert "definition DAG verified" in output
    assert (
        f"checked-theorem DAG verified ({audit.theorem_count:,} theorems, "
        f"{audit.theorem_edge_count:,} proof edges)"
    ) in output
    assert (
        f"milestone DAG verified ({audit.milestone_count:,} nodes, "
        f"{audit.milestone_proof_edge_count:,} proof edges)"
    ) in output
