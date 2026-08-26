"""Keep Hydra's single product roadmap synchronized with checked public evidence.

The compact campaign/definition snapshots, sealed channel, and current-edition
source constants are enough to authenticate documentation counts. Loading the
large full Alpha catalog into another Python object graph here would add
needless peak memory; no release version is hardcoded.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[3]
ROADMAP = ROOT / "docs" / "HYDRA_PRODUCT_ROADMAP.md"
HYDRA_PLAN = ROOT / "PLAN" / "11_peano_hydra.md"
LAB_PLAN = ROOT / "PLAN" / "09_peano_lab.md"
GRAND_PLAN = ROOT / "PLAN" / "14_constructive_number_theory_grand_campaign.md"
PLAN_INDEX = ROOT / "PLAN.md"
ARCHIVED_PLANS = (
    "10_arithmetic_library.md",
    "11_quadratic_reciprocity.md",
    "12_ha_number_theory_campaign.md",
    "13_constructive_number_theory_frontier.md",
)
HYDRA_DESIGN = ROOT / "docs" / "PEANO_HYDRA_DESIGN.md"
CAMPAIGN = ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
DEFINITIONS = (
    ROOT / "book" / "_static" / "constructive-grand-campaign" / "definitions.json"
)
LEAN_DOCS = (
    "BUILD.md",
    "DEPLOY.md",
    "LEAN_CERTIFIED_PRESENTATION.md",
    "LEAN_LIVE_INTEGRATION.md",
    "LEAN_LIVE_PROOF_COVERAGE.md",
    "LEAN_PROOF_STRANDS.md",
    "LEAN_SELECTOR_UI.md",
    "PUBLIC_LEAN_SERVICE.md",
)
HISTORICAL_MODEL_DOCS = (
    "PEANO_TRAINING.md",
    "PEANO_LLM.md",
    "PEANO_PRETRAINED_BASELINE.md",
    "PEANO_TRAINING_DASHBOARD.md",
)
MODEL_BOOK_CHAPTERS = (
    "peano-hydra.md",
    "training-a-peano-policy.md",
)
PRODUCT_NAVIGATION = tuple(
    dict.fromkeys(
        (
            *LEAN_DOCS,
            *HISTORICAL_MODEL_DOCS,
            "PEANO_LAB_DESIGN.md",
            "PEANO_HYDRA_DESIGN.md",
            "HYDRA_POST_TRAINING.md",
        )
    )
)


@pytest.fixture(scope="module")
def documentation() -> dict[str, str]:
    return {
        "roadmap": ROADMAP.read_text(encoding="utf-8"),
        "hydra_plan": HYDRA_PLAN.read_text(encoding="utf-8"),
        "lab_plan": LAB_PLAN.read_text(encoding="utf-8"),
        "grand_plan": GRAND_PLAN.read_text(encoding="utf-8"),
        "plan_index": PLAN_INDEX.read_text(encoding="utf-8"),
        "design": HYDRA_DESIGN.read_text(encoding="utf-8"),
    }


@pytest.fixture(scope="module")
def public_evidence() -> dict[str, object]:
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    definitions = json.loads(DEFINITIONS.read_text(encoding="utf-8"))
    version = campaign["meta"]["current_alpha_version"]
    assert isinstance(version, str) and re.fullmatch(r"v[1-9][0-9]{0,3}", version)
    edition_source = (
        ROOT
        / "peano-lab"
        / "py"
        / "peano_lab"
        / "library"
        / f"editions_{version}.py"
    )
    channel_path = ROOT / "artifacts" / "peano-library" / f"channels-{version}.json"
    channels = json.loads(channel_path.read_text(encoding="utf-8"))
    alpha = channels["channels"]["alpha"]
    stable = channels["channels"]["stable"]
    constant_prefix = f"EXPECTED_ALPHA_{version.upper()}_"
    constants: dict[str, int] = {}
    tree = ast.parse(edition_source.read_text(encoding="utf-8"))
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name) or not target.id.startswith(constant_prefix):
            continue
        if isinstance(statement.value, ast.Constant) and type(statement.value.value) is int:
            constants[target.id.removeprefix(constant_prefix)] = statement.value.value
    assert alpha["theorem_count"] == constants["COUNT"]
    assert stable["theorem_count"] == 432
    return {
        "campaign": campaign,
        "definitions": definitions,
        "version": version,
        "next_version": f"v{int(version[1:]) + 1}",
        "alpha": alpha,
        "stable": stable,
        "constants": constants,
        "nodes": {node["id"]: node for node in campaign["nodes"]},
    }


@pytest.fixture(scope="module")
def browser_evidence(public_evidence: dict[str, object]) -> dict[str, int]:
    static = ROOT / "book" / "_static"
    manifests = tuple(sorted(static.glob("constructive-*-explorer/manifest.json")))
    assert manifests, "the current release has no generated constructive browsers"

    campaign_families = 0
    campaign_theorems = 0
    checked_alpha_pages = 0
    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert manifest["alpha_edition_version"] == public_evidence["version"]
        families = manifest["families"]
        campaign_families += len(families)
        for family in families:
            theorem_count = family.get("theorem_count", family.get("node_count"))
            alpha_count = family.get("alpha_checked_use_node_count", theorem_count)
            assert type(theorem_count) is int and theorem_count > 0
            assert type(alpha_count) is int and 0 <= alpha_count <= theorem_count
            campaign_theorems += theorem_count
            checked_alpha_pages += alpha_count

    flagship_roots = (
        static / "pa-proof-explorer",
        static / "bertrand-proof-explorer",
    )
    flagship_pages = 0
    for root in flagship_roots:
        for edition in (root, root / "defined"):
            assert (edition / "graph.html").is_file()
            flagship_pages += sum(path.is_file() for path in (edition / "tag").glob("*.html"))

    family_count = campaign_families + len(flagship_roots)
    graph_count = campaign_families + 2 * len(flagship_roots)
    staged_page_count = graph_count + 2 * campaign_theorems + flagship_pages
    return {
        "families": family_count,
        "graphs": graph_count,
        "eligible_pages": staged_page_count,
        "checked_alpha_pages": checked_alpha_pages,
    }


def test_current_epoch_counts_match_compact_campaign_and_release_constants(
    documentation: dict[str, str], public_evidence: dict[str, object]
) -> None:
    campaign = public_evidence["campaign"]
    constants = public_evidence["constants"]
    version = public_evidence["version"]
    theorem_count = constants["COUNT"]
    assert theorem_count == campaign["meta"]["current_alpha_checked_use_count"]
    assert constants["CHECKED_USE_COUNT"] == theorem_count

    for document in ("roadmap", "hydra_plan", "lab_plan"):
        text = documentation[document]
        assert f"Alpha {version}" in text
        assert f"{theorem_count:,}" in text
        assert f"{constants['EDGE_COUNT']:,}" in text
        assert f"{constants['LAYER_COUNT']}" in text
        assert "432" in text


def test_only_reviewed_definition_graph_has_mathematical_authority(
    documentation: dict[str, str], public_evidence: dict[str, object]
) -> None:
    definitions = public_evidence["definitions"]
    roadmap = documentation["roadmap"]
    assert definitions["authority_policy"]["blueprint_definitions"].startswith(
        "research vocabulary only"
    )
    assert f"{definitions['reviewed_definition_count']} definitions" in roadmap
    assert f"{definitions['reviewed_definition_edge_count']} definition-dependency" in roadmap
    assert f"{definitions['definition_count']} names" in roadmap
    assert f"{definitions['definition_edge_count']} conceptual edges" in roadmap
    assert f"{definitions['milestone_usage_edge_count']} references" in roadmap
    assert "exactly two mathematical graphs that can grow" in roadmap
    assert "not parallel mathematical" in roadmap


def test_milestone_graph_is_planning_only_and_uses_real_prerequisite_counts(
    documentation: dict[str, str], public_evidence: dict[str, object]
) -> None:
    campaign = public_evidence["campaign"]
    vertex_count = len(campaign["nodes"])
    edge_count = sum(len(node["deps"]) for node in campaign["nodes"])
    roadmap = documentation["roadmap"]
    assert vertex_count == campaign["meta"]["node_count"]
    assert f"{vertex_count} vertices" in roadmap
    assert f"{edge_count} planning edges" in roadmap
    assert "Research scheduling only; open nodes are not proved theorems" in roadmap


def test_mixed_edge_types_never_grant_theorem_proof_authority(
    documentation: dict[str, str]
) -> None:
    roadmap = documentation["roadmap"]
    assert "`proof_dependency`: actual theorem-proof prerequisite" in roadmap
    assert "`uses_definition`: statement/presentation notation reference" in roadmap
    assert (
        "`definition_uses_definition`: conservative-abbreviation prerequisite"
        in roadmap
    )
    assert "Only `proof_dependency` contributes to theorem reachability" in roadmap


def test_alpha_access_is_explicit_and_does_not_widen_historical_authority(
    documentation: dict[str, str], public_evidence: dict[str, object]
) -> None:
    roadmap = documentation["roadmap"]
    constants = public_evidence["constants"]
    version = public_evidence["version"]
    assert "unchanged 432-theorem Stable default" in roadmap
    assert f"`hydra-alpha-{version}-` digest-bound authority" in roadmap
    assert "historical\n247-theorem authority" in roadmap
    assert f"{constants['COUNT'] - 432:,} theorems" in roadmap
    assert "Unknown editions, changed digests, nonmembers, unchecked rows" in roadmap
    assert f"Prospective Alpha-{public_evidence['next_version']} candidate" in roadmap
    assert "separately sealed release" in roadmap
    identity = public_evidence["alpha"]["edition_identity_sha256"]
    assert len(identity) == 64
    assert f"hydra-alpha-{version}-{identity}" in roadmap
    assert "A shortened digest or version name by itself does not grant Alpha access" in roadmap


@pytest.mark.parametrize("identifier", ("T13", "G095", "G011"))
def test_checked_research_components_never_close_their_stronger_milestones(
    identifier: str,
    documentation: dict[str, str],
    public_evidence: dict[str, object],
) -> None:
    node = public_evidence["nodes"][identifier]
    assert node["status"] == "open"
    assert node["evidence"]["checked_use"] is False
    assert node["evidence"]["partial_component_checked_use"] is True
    new_count = node["evidence"]["new_checked_theorem_count"]
    assert type(new_count) is int and new_count > 0
    assert f"**{identifier}**" in documentation["roadmap"]
    assert "remain **OPEN**" in documentation["roadmap"]
    assert f"{new_count}" in documentation["roadmap"]


def test_grand_campaign_reconciles_current_partial_mathematical_evidence(
    documentation: dict[str, str], public_evidence: dict[str, object]
) -> None:
    blueprint = documentation["grand_plan"]
    nodes = public_evidence["nodes"]
    version = public_evidence["version"]
    previous_version = f"v{int(version[1:]) - 1}"
    assert f"current Alpha-{version} catalog resolves" in blueprint
    assert f"current Alpha-{previous_version} catalog resolves" not in blueprint
    assert f"{nodes['T13']['evidence']['partial_checked_theorem_count']} checked components" in blueprint
    assert "formal-derivative" in blueprint
    assert "pairwise-coprime finite-list CRT" in blueprint
    assert "G011 remains open" in blueprint


def test_historical_teaching_stubs_and_no_training_rule_are_explicitly_superseded(
    documentation: dict[str, str]
) -> None:
    lab = documentation["lab_plan"]
    assert "M7's early statement-only" in lab
    assert "superseded by independently compiled production" in lab
    assert "never offers a stub as a verified Lean Live proof" in lab
    assert "M9 itself was data + protocol only" in lab
    assert "later reviewed M19 milestone" in lab
    assert "**No training in this repo**" not in lab


def test_completed_quadratic_reciprocity_is_not_falsely_listed_as_future_work(
    documentation: dict[str, str]
) -> None:
    plan = documentation["hydra_plan"]
    assert "Quadratic reciprocity is not future library growth" in plan
    assert "historical Alpha v16" in plan
    assert "## Quadratic-reciprocity expansion track" not in plan
    assert "Current 247-theorem library identified" not in plan


def test_experimental_gates_are_not_confused_with_implemented_product(
    documentation: dict[str, str]
) -> None:
    roadmap = documentation["roadmap"]
    plan = documentation["hydra_plan"]
    assert "**H0 is not complete. H1 is not complete. No H5 claim is available. No" in roadmap
    assert "language-model advantage has been demonstrated.**" in roadmap
    assert "**H0 is not complete:**" in plan
    assert "**H1 is not complete:**" in plan
    assert "**No H5 claim is available:**" in plan
    assert "## Current executable product baseline" in plan
    assert "publication-grade matched-compute result" in plan


def test_optimization_discovery_and_post_training_share_one_verified_epoch(
    documentation: dict[str, str]
) -> None:
    roadmap = documentation["roadmap"]
    assert "## Proof optimization contract" in roadmap
    assert "## Proof-discovery contract" in roadmap
    assert "## Post-training contract" in roadmap
    assert "**Supervised transitions:**" in roadmap
    assert "**Preference pairs:**" in roadmap
    assert "**Discovery labels:**" in roadmap
    assert "fewer expanded proof-search states" in roadmap
    assert "exact public command tuple as a deterministic final tie-breaker" in roadmap
    assert "not a proof of global tactic-decision\noptimality" in roadmap
    assert "`exact_source_statement_sha256_only`" in roadmap
    assert "`semantic_novelty_claim: false`" in roadmap
    for filename in (
        "epoch.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl", "manifest.json"
    ):
        assert f"_deploy/hydra/{filename}" in roadmap
    assert "teacher-oracle labels represent a previously unknown mathematical theorem" in (
        " ".join(roadmap.split())
    )
    assert "until its ordinary\ndependency-closed Alpha-admission procedure succeeds" in roadmap
    assert "100,000 positive transitions from 20,000" in roadmap


def test_one_ordered_engineering_milestone_replaces_competing_roadmaps(
    documentation: dict[str, str]
) -> None:
    roadmap = documentation["roadmap"]
    assert roadmap.count("## The one next engineering milestone") == 1
    assert "`make hydra-check`" in roadmap
    assert "`make hydra-prepare`" in roadmap
    assert "HYDRA_PRODUCT_ROADMAP.md" in documentation["hydra_plan"]
    assert "HYDRA_PRODUCT_ROADMAP.md" in documentation["lab_plan"]
    assert "HYDRA_PRODUCT_ROADMAP.md" in documentation["design"]
    assert "## Current product state and single active next step" in documentation[
        "plan_index"
    ]
    assert "13_constructive_number_theory_frontier.md" in documentation["plan_index"]
    assert "14_constructive_number_theory_grand_campaign.md" in documentation[
        "plan_index"
    ]
    assert "## Active Peano Lab milestone" not in documentation["plan_index"]


def test_documented_hydra_entry_points_are_real_bounded_local_make_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^hydra-check:\s*$", makefile, flags=re.MULTILINE)
    assert re.search(r"^hydra-prepare:\s*$", makefile, flags=re.MULTILINE)
    assert (ROOT / "scripts" / "prepare_peano_hydra.py").is_file()
    start = makefile.index("hydra-check:")
    next_target = re.search(r"\n[a-z][a-z0-9_-]*:", makefile[start:])
    assert next_target is not None
    check_stanza = makefile[start : start + next_target.start()]
    start = makefile.index("hydra-prepare:")
    next_target = re.search(r"\n[a-z][a-z0-9_-]*:", makefile[start:])
    assert next_target is not None
    prepare_stanza = makefile[start : start + next_target.start()]
    assert "scripts/prepare_peano_hydra.py --check" in check_stanza
    assert '"_deploy/hydra"' in prepare_stanza
    for unsafe in ("ssh ", "rsync ", "git push", "deploy-proofs"):
        assert unsafe not in check_stanza
        assert unsafe not in prepare_stanza


@pytest.mark.parametrize("filename", ARCHIVED_PLANS)
def test_superseded_plan_ledgers_clearly_identify_current_checked_authority(
    filename: str,
    public_evidence: dict[str, object],
) -> None:
    plan = (ROOT / "PLAN" / filename).read_text(encoding="utf-8")
    preface = plan[:2_100]
    assert "Historical" in preface
    assert f"Alpha {public_evidence['version']}" in preface
    assert f"{public_evidence['constants']['COUNT']:,}" in preface
    assert "HYDRA_PRODUCT_ROADMAP.md" in preface
    assert "14_constructive_number_theory_grand_campaign.md" in preface


def test_old_dated_release_rows_are_labeled_as_historical_not_current() -> None:
    plan = (ROOT / "PLAN" / "12_ha_number_theory_campaign.md").read_text(
        encoding="utf-8"
    )
    for version in range(2, 13):
        assert f"Alpha v{version} (historical checkpoint)" in plan
        assert f"Alpha v{version} (current)" not in plan


def test_every_public_campaign_and_alpha_exact_page_uses_the_same_proof_action(
    documentation: dict[str, str],
    browser_evidence: dict[str, int],
) -> None:
    selector = (ROOT / "docs" / "LEAN_SELECTOR_UI.md").read_text(encoding="utf-8")
    hosting = (ROOT / "docs" / "PUBLIC_LEAN_SERVICE.md").read_text(encoding="utf-8")
    for guide in (selector, hosting, documentation["roadmap"]):
        assert f"{browser_evidence['families']:,}" in guide
        assert f"{browser_evidence['graphs']:,}" in guide
        assert f"{browser_evidence['eligible_pages']:,}" in guide
        assert f"{browser_evidence['checked_alpha_pages']:,}" in guide
    assert "Checked-use authority: Alpha vN; independently verified" in selector
    assert "Alpha evidence: alpha_closed" in selector
    assert "merely `body_checked` receipt never" in selector


@pytest.mark.parametrize("filename", LEAN_DOCS)
def test_every_current_lean_guide_uses_the_same_checked_release_and_product_roadmap(
    filename: str,
    public_evidence: dict[str, object],
) -> None:
    guide = (ROOT / "docs" / filename).read_text(encoding="utf-8")
    version = public_evidence["version"]
    constants = public_evidence["constants"]
    assert "HYDRA_PRODUCT_ROADMAP.md" in guide
    assert f"Alpha {version}" in guide or f"Alpha-{version}" in guide
    assert f"{constants['COUNT']:,}" in guide
    assert f"{constants['EDGE_COUNT']:,}" in guide
    for historical in range(1, int(version[1:])):
        assert re.search(
            r"\b(?:current|currently)\s+(?:immutable\s+|sealed\s+)?"
            rf"(?:\*\*)?Alpha[ -]v{historical}\b",
            guide,
            flags=re.IGNORECASE,
        ) is None


def test_public_browser_docs_have_one_same_origin_deployment_path() -> None:
    selector = (ROOT / "docs" / "LEAN_SELECTOR_UI.md").read_text(encoding="utf-8")
    hosting = (ROOT / "docs" / "PUBLIC_LEAN_SERVICE.md").read_text(encoding="utf-8")
    assert "only\nsupported production route is the exact same-origin" in selector
    assert "cross-origin HTTPS proof services are rejected" in selector
    assert "or explicitly configured HTTPS proof-service origin" not in selector
    assert "external HTTPS proof-service origin is not a supported" in hosting


def test_public_lean_python_restart_remains_operator_controlled() -> None:
    guide = (ROOT / "docs" / "PUBLIC_LEAN_SERVICE.md").read_text(encoding="utf-8")
    assert "does not automatically reload upgraded Python" in guide
    assert "make lean-public-stop\nmake lean-public-start\nmake lean-public-status" in guide
    assert "`make lean-browser`" in guide
    assert "its owning terminal" in guide
    assert "interrupt an active public SSH tunnel" in guide
    assert "does not deploy content" in guide


@pytest.mark.parametrize("filename", HISTORICAL_MODEL_DOCS)
def test_historical_model_guides_keep_247_authority_distinct_from_current_alpha(
    filename: str,
    public_evidence: dict[str, object],
) -> None:
    guide = (ROOT / "docs" / filename).read_text(encoding="utf-8")
    introduction = guide[:2_000]
    assert "247-theorem" in introduction
    assert f"Alpha {public_evidence['version']}" in introduction
    assert f"{public_evidence['constants']['COUNT']:,}" in introduction
    assert "432-theorem Stable" in introduction
    assert "HYDRA_PRODUCT_ROADMAP.md" in introduction
    assert "HYDRA_POST_TRAINING.md" in introduction


def test_binding_peano_design_no_longer_limits_current_alpha_exports_to_v16(
    public_evidence: dict[str, object],
) -> None:
    design = (ROOT / "docs" / "PEANO_LAB_DESIGN.md").read_text(encoding="utf-8")
    constants = public_evidence["constants"]
    assert f"{constants['COUNT']:,}" in design
    assert f"{constants['EDGE_COUNT']:,}" in design
    assert "HYDRA_PRODUCT_ROADMAP.md" in design
    assert f"currently Alpha {public_evidence['version']}" in design
    assert "first\n   acquired that authority in historical Alpha v16" in design
    assert "only to closed theorems admitted by immutable Alpha v16" not in design


@pytest.mark.parametrize("filename", MODEL_BOOK_CHAPTERS)
def test_public_model_chapters_use_current_epoch_without_rewriting_old_receipts(
    filename: str,
    public_evidence: dict[str, object],
) -> None:
    chapter = (ROOT / "book" / "peano" / filename).read_text(encoding="utf-8")
    constants = public_evidence["constants"]
    assert f"Alpha {public_evidence['version']}" in chapter
    assert f"{constants['COUNT']:,}" in chapter
    assert f"{constants['EDGE_COUNT']:,}" in chapter
    assert "432-theorem Stable" in chapter
    assert "247-theorem" in chapter
    assert "HYDRA_PRODUCT_ROADMAP.md" in chapter
    assert "HYDRA_POST_TRAINING.md" in chapter
    assert "The current 384-theorem library" not in chapter


def test_public_theorem_ladder_distinguishes_current_release_from_early_history(
    public_evidence: dict[str, object],
) -> None:
    chapter = (ROOT / "book" / "peano" / "ladder.md").read_text(encoding="utf-8")
    introduction = chapter[:2_100]
    constants = public_evidence["constants"]
    assert f"Alpha {public_evidence['version']}" in introduction
    assert f"{constants['COUNT']:,}" in introduction
    assert f"{constants['EDGE_COUNT']:,}" in introduction
    assert "432-theorem Stable default" in introduction
    assert "closed in historical Alpha v16" in introduction
    assert "historical local candidate runtime" in introduction
    assert "HYDRA_PRODUCT_ROADMAP.md" in introduction
    assert "current local candidate runtime contains 384" not in chapter


def test_catalog_scaleout_preserves_explicit_checked_authority_and_bounds(
    documentation: dict[str, str],
) -> None:
    roadmap = documentation["roadmap"]
    operations = (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(
        encoding="utf-8"
    )
    implementation = (ROOT / "scripts" / "prepare_peano_hydra.py").read_text(
        encoding="utf-8"
    )
    for guide in (roadmap, operations):
        assert "--catalog-limit 32" in guide
        assert "--catalog-theorem crt_product_witness" in guide
        assert "**33" in guide
        assert "**279 verified" in guide
        assert "**2 " in guide
        for flag in ("--catalog-limit", "--catalog-theorem"):
            assert flag in guide
            assert flag in implementation
    assert "**512 additional theorem routes**" in roadmap
    assert "32-decision ceiling" in roadmap
    assert "freshly" in roadmap or "independently rechecks" in roadmap
    assert "a\nworking pilot, not a large-corpus claim" in roadmap
    assert '"duplicate_transitions_removed": curriculum.duplicate_transitions_removed' in implementation


def test_whole_catalog_guides_report_real_census_and_fail_closed_memory_bounds(
    documentation: dict[str, str],
) -> None:
    source_path = ROOT / "scripts" / "prepare_peano_hydra.py"
    source = source_path.read_text(encoding="utf-8")
    constants = {
        target.id: statement.value.value
        for statement in ast.parse(source).body
        if isinstance(statement, ast.Assign)
        and isinstance(statement.value, ast.Constant)
        and type(statement.value.value) is int
        for target in statement.targets
        if isinstance(target, ast.Name)
    }

    assert constants["MAX_ADDITIONAL_CATALOG_THEOREMS"] == 512
    assert constants["MAX_CATALOG_ROUTE_DECISIONS"] == 32
    assert constants["MAX_CATALOG_TOTAL_TACTICS"] == 8_192
    assert constants["MAX_CATALOG_STATEMENT_BYTES"] == 4_096
    assert constants["MAX_CATALOG_DEPENDENCY_CLOSURE_TACTICS"] == 256
    assert constants["MAX_CATALOG_DEPENDENCY_CLOSURE_STATEMENT_BYTES"] == 8_192
    assert '"automatic_prerequisite_membership": "stable_only"' in source

    guides = (
        documentation["roadmap"],
        (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(encoding="utf-8"),
        (ROOT / "training" / "peano_hydra" / "README.md").read_text(
            encoding="utf-8"
        ),
    )
    for guide in guides:
        compact = " ".join(guide.split())
        for value in (
            "978",
            "723 Alpha-only",
            "255 Stable",
            "818",
            "564 Alpha-only",
            "254 Stable",
            "460",
            "260 Alpha-only",
            "200 Stable",
        ):
            assert value in compact
        for value in (
            "512",
            "256",
            "4,096",
            "8,192",
            "512 KiB",
            "24 MiB",
            "Stable-only",
            "--catalog-all",
            "--catalog-limit 192",
            "--catalog-max-decisions 16",
            "192",
            "91 Alpha-only",
            "1,798",
            "40",
        ):
            assert value in compact
        assert "279" in compact and "33" in compact


def test_alpha_handoff_quarantines_canonical_heldouts_from_train_and_development(
    documentation: dict[str, str],
) -> None:
    guides = (
        documentation["roadmap"],
        (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(encoding="utf-8"),
        (ROOT / "training" / "peano_hydra" / "README.md").read_text(
            encoding="utf-8"
        ),
    )
    for guide in guides:
        compact = " ".join(guide.split())
        assert "triangular_product_even_hydra_candidate" in compact
        assert "consecutive_product_even" in compact
        assert "both training and development" in compact
        assert "261" in compact
        assert "5" in compact
        assert "1,773" in compact
        assert "12 clean development" in compact
        assert "222 bounded optimizer steps" in compact
        assert "13 quarantined" in compact
        assert "train.jsonl" in compact and "dev.jsonl" in compact
        assert "prompt" in compact
        assert "planned/not-run" in compact
        assert "--execute" in compact

    operations = guides[1]
    for goal in (
        "closed_arithmetic_seven",
        "existential_subtraction_two",
        "double_right_zero",
        "consecutive_product_even",
    ):
        assert goal in operations
    assert "`quarantine.jsonl`" in operations
    assert "no proof\nstatement, tactic, trace, prompt, or completion" in operations
    assert "16-transition default pilot" in operations
    assert "research_claim_eligible: false" in operations
    assert "sealed_benchmark: false" in operations


def test_symbolic_evaluation_is_real_but_never_a_language_model_result(
    documentation: dict[str, str],
) -> None:
    guides = (
        documentation["roadmap"],
        (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(encoding="utf-8"),
        (ROOT / "training" / "peano_hydra" / "README.md").read_text(
            encoding="utf-8"
        ),
    )
    for guide in guides:
        compact = " ".join(guide.split())
        assert "make hydra-eval-control" in compact
        assert "--check --symbolic-controls" in compact
        assert "3 of 4" in compact
        for value in ("98", "29", "10"):
            assert value in compact
        assert "unknown" in compact
        assert "zero theorem imports" in compact
        assert "zero model calls" in compact


def test_alpha_training_make_targets_keep_gpu_execution_explicit_and_separate() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    targets = (
        "hydra-scale",
        "hydra-posttrain-prepare",
        "hydra-posttrain-preflight",
        "hydra-eval-plan",
        "hydra-eval-control",
        "hydra-posttrain-ready",
        "hydra-posttrain-execute",
    )

    def stanza(name: str) -> tuple[str, str]:
        target = re.search(
            rf"^{re.escape(name)}:(?P<dependencies>[^\n]*)$",
            makefile,
            flags=re.MULTILINE,
        )
        assert target is not None, name
        remainder = makefile[target.end() :]
        next_target = re.search(r"^[A-Za-z][A-Za-z0-9_-]*:", remainder, re.MULTILINE)
        body = remainder if next_target is None else remainder[: next_target.start()]
        return target.group("dependencies"), body

    for target in targets:
        assert re.search(
            rf'^\s*@echo "\s+make {re.escape(target)}\b',
            makefile,
            flags=re.MULTILINE,
        ), target
        stanza(target)

    dependencies, ready = stanza("hydra-posttrain-ready")
    assert "hydra-scale" in dependencies.split()
    assert "prepare_peano_hydra_posttrain.py" in ready
    assert "training.peano_hydra.posttrain" in ready
    assert "--preflight" in ready
    assert "eval_peano_hydra_posttrain.py" in ready
    assert "--check" in ready
    assert "--symbolic-controls" in ready

    _, control = stanza("hydra-eval-control")
    assert "--check --symbolic-controls" in control

    for target in targets[:-1]:
        _, body = stanza(target)
        assert "--execute" not in body, target
        assert "hydra-posttrain-execute" not in body, target
        for unsafe in ("ssh ", "rsync ", "git push", "deploy-proofs"):
            assert unsafe not in body, (target, unsafe)

    _, execute = stanza("hydra-posttrain-execute")
    assert "--execute" in execute
    assert "--preparation-dir" in execute


def test_optional_helios_training_chain_is_clean_offline_and_dependency_guarded(
    documentation: dict[str, str],
) -> None:
    prepare_path = ROOT / "slurm" / "peano_hydra_alpha_prepare.sbatch"
    train_path = ROOT / "slurm" / "peano_hydra_alpha_train.sbatch"
    evaluate_path = ROOT / "slurm" / "peano_hydra_alpha_evaluate.sbatch"
    prepare = prepare_path.read_text(encoding="utf-8")
    train = train_path.read_text(encoding="utf-8")
    evaluate = evaluate_path.read_text(encoding="utf-8")
    common = (ROOT / "scripts" / "helios_common.sh").read_text(encoding="utf-8")
    submit = (ROOT / "scripts" / "helios_submit_job.sh").read_text(encoding="utf-8")

    assert "#SBATCH --account=plgccaiautore2026-cpu" in prepare
    assert "#SBATCH --time=00:30:00" in prepare
    assert "--execute" not in prepare
    for source in (train, evaluate):
        assert "#SBATCH --account=plgccaiautore2026-gpu-gh200" in source
        assert "#SBATCH --gres=gpu:1" in source
    assert "#SBATCH --time=02:00:00" in train
    assert "#SBATCH --time=01:00:00" in evaluate
    assert "--execute --preparation-dir" in train
    assert "--execute-models --trained-adapter" in evaluate
    for source in (prepare, train, evaluate):
        assert "requires an explicitly clean committed source" in source
        assert "HF_HUB_OFFLINE=1" in source
        assert "TRANSFORMERS_OFFLINE=1" in source

    assert "peano_helios_expected_predecessor" in common
    assert "slurm/peano_hydra_alpha_prepare.sbatch" in common
    assert "slurm/peano_hydra_alpha_train.sbatch" in common
    assert "slurm/peano_hydra_alpha_evaluate.sbatch" in common
    assert "training and evaluation submissions require --afterok JOB_ID" in submit
    assert "--submit --confirm" in submit

    for guide in (
        documentation["roadmap"],
        (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(encoding="utf-8"),
        (ROOT / "training" / "peano_hydra" / "README.md").read_text(
            encoding="utf-8"
        ),
    ):
        compact = " ".join(guide.split())
        for path in (prepare_path, train_path, evaluate_path):
            assert path.relative_to(ROOT).as_posix() in compact
        assert "--afterok" in compact
        assert "--submit" in compact and "--confirm" in compact


def test_recorded_routes_normalize_only_engine_metavariables_after_exact_match(
    documentation: dict[str, str],
) -> None:
    source_path = ROOT / "training" / "peano_hydra" / "development.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    expression = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_METAVARIABLE"
            for target in node.targets
        )
    )
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_normalize_metavariables"
    )
    module = ast.Module(body=[expression, function], type_ignores=[])
    namespace: dict[str, object] = {"re": re}
    exec(compile(ast.fix_missing_locations(module), str(source_path), "exec"), namespace)
    normalize = namespace["_normalize_metavariables"]

    original = ("?t91 + x = ?t4", "?t4 = ?t91", "?u7 = ?t91x")
    assert normalize(original) == ("?t1 + x = ?t2", "?t2 = ?t1", "?u7 = ?t91x")
    assert normalize(("?t8 = ?t8",)) != normalize(("?t8 = ?t9",))
    assert normalize(tuple(reversed(original[:2]))) != normalize(original[:2])
    assert source.index("exact = self._source.propose(") < source.index(
        "return self._normalized.get("
    )
    assert "return self._source.policy_environment" in source

    operations = (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(
        encoding="utf-8"
    )
    for guide in (documentation["roadmap"], operations):
        assert "`?tN`" in guide
        assert "ordered goal tuple" in guide
        assert "novelty claim" in guide
        assert "goal order" in guide


def test_identical_transition_deduplication_preserves_complete_authority(
    documentation: dict[str, str],
) -> None:
    source_path = ROOT / "training" / "peano_hydra" / "curriculum.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_verified_curriculum"
    )
    key = next(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "key"
            for target in node.targets
        )
    )
    assert isinstance(key, ast.Tuple)
    fields = tuple(
        item.slice.value
        for item in key.elts
        if isinstance(item, ast.Subscript)
        and isinstance(item.value, ast.Name)
        and item.value.id == "row"
        and isinstance(item.slice, ast.Constant)
    )
    assert fields == (
        "epoch_sha256",
        "lineage_sha256",
        "state_sha256",
        "action",
        "environment_sha256",
    )
    checked_conflicts = {
        node.slice.value
        for node in ast.walk(function)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "earlier"
        and isinstance(node.slice, ast.Constant)
    }
    assert {
        "goals_before", "goals_after", "focus", "prompt", "completion"
    } <= checked_conflicts
    assert '"duplicate_transitions_removed": self.duplicate_transitions_removed' in source

    operations = (ROOT / "docs" / "HYDRA_POST_TRAINING.md").read_text(
        encoding="utf-8"
    )
    for guide in (documentation["roadmap"], operations):
        for field in (*fields, "duplicate_transitions_removed"):
            assert field in guide
        assert "deterministically" in guide
        assert "focus" in guide


def test_public_hydra_chapter_explains_existing_qr_and_real_preparation_outputs() -> None:
    chapter = (ROOT / "book" / "peano" / "peano-hydra.md").read_text(
        encoding="utf-8"
    )
    assert "## Reciprocity is existing proof evidence, not a new discovery" in chapter
    assert "independently closed in Alpha v16" in chapter
    assert "make hydra-check" in chapter
    assert "make hydra-prepare" in chapter
    for filename in (
        "epoch.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl", "manifest.json"
    ):
        assert f"_deploy/hydra/{filename}" in chapter
    assert "not-yet-completed H0.3 protocol" in chapter
    assert "do not claim semantic mathematical novelty" in chapter or (
        "without\nclaiming semantic mathematical novelty" in chapter
    )
    assert "eight to ten weeks" not in chapter


def test_every_local_roadmap_document_link_resolves(
    documentation: dict[str, str]
) -> None:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", documentation["roadmap"]):
        assert "://" not in target
        path = (ROADMAP.parent / target.split("#", 1)[0]).resolve()
        assert path.is_relative_to(ROOT)
        assert path.is_file(), f"broken Hydra roadmap link: {target}"


ALPHA_MODEL_RUN = (
    ROOT / "artifacts" / "peano-hydra" / "alpha-v25-posttrain-2026-08-26"
)


def _run_receipt(filename: str) -> dict[str, object]:
    return json.loads((ALPHA_MODEL_RUN / filename).read_text(encoding="utf-8"))


def _file_sha256(filename: str) -> str:
    return hashlib.sha256((ALPHA_MODEL_RUN / filename).read_bytes()).hexdigest()


def test_archived_alpha_model_evidence_has_a_complete_checksum_inventory() -> None:
    entries = {}
    for line in (ALPHA_MODEL_RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        assert filename not in entries
        assert Path(filename).name == filename
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        assert _file_sha256(filename) == digest
        entries[filename] = digest
    assert set(entries) == {
        path.name for path in ALPHA_MODEL_RUN.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    }


def test_archived_alpha_model_evidence_preserves_exact_executed_bytes() -> None:
    assert _file_sha256("training-manifest.json") == (
        "766b94e1645096840f79499b3b45465c7c29133d2583456e85567bdf5cc2b45f"
    )
    assert _file_sha256("matched-evaluation.json") == (
        "87085bd544e7121cb1eb41255208c036e74139a4c2c459a69f20b141d60f2689"
    )
    assert _file_sha256("symbolic-control.json") == (
        "80798392a002fdb7c0bae4abf9f68ad6e2e6d7817bc2b394f342f9fe74a899cb"
    )
    model = _run_receipt("training-manifest.json")
    preparation = _run_receipt("preparation-manifest.json")
    assert _file_sha256("preparation-manifest.json") == model[
        "preparation_manifest_sha256"
    ]
    assert _file_sha256("preparation-config.toml") == preparation["files"][
        "config.toml"
    ]["sha256"]
    assert _file_sha256("source-manifest.json") == preparation["source"][
        "manifest_sha256"
    ]
    assert _file_sha256("source-provenance.tsv") == model["job"]["deployment"][
        "source_sync"
    ]["sha256"]
    for filename in ("matched-evaluation.json", "symbolic-control.json"):
        report = _run_receipt(filename)
        digest = report.pop("evaluation_sha256")
        canonical = json.dumps(
            report, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == digest


def test_archived_alpha_model_scores_do_not_claim_a_symbolic_advantage() -> None:
    report = _run_receipt("matched-evaluation.json")
    model = _run_receipt("training-manifest.json")
    control = _run_receipt("symbolic-control.json")
    metrics = report["comparison"]["model_metrics"]
    assert report["comparison"]["status"] == "executed"
    assert metrics["pretrained_kernel_checked_proofs"] == 0
    assert metrics["trained_kernel_checked_proofs"] == 3
    assert metrics["pretrained_model_generate_calls"] == 4
    assert metrics["trained_model_generate_calls"] == 22
    assert metrics["research_claim_eligible"] is False
    assert report["theorem_authority"]["allowed_theorems"] == []
    assert control["symbolic_controls"]["kernel_checked_proofs"] == 3
    assert all(row["model_calls"] == 0 for row in control["symbolic_controls"]["goals"])
    assert control["comparison"]["status"] == "unmeasured"
    assert control["comparison"]["model_metrics"] is None
    assert model["model_trained"] is True
    assert model["research_claim_eligible"] is False
    assert model["sealed_benchmark"] is False
    assert model["alpha_admitted"] is False
    assert model["metrics"]["actual_optimizer_steps"] == 222
    assert model["metrics"]["expected_optimizer_steps"] == 222
    assert model["metrics"]["training_rows"] == 1773
    assert model["metrics"]["development_rows"] == 12
    audit = model["finite_gradient_audit"]
    assert audit["observed_optimizer_boundaries"] == 222
    assert audit["raw_finite_optimizer_boundaries"] == 222
    assert audit["post_clip_finite_optimizer_boundaries"] == 222
    assert len(audit["records"]) == 222
    assert model["adapter_update"]["changed_parameter_tensors"] == 392
    assert model["adapter_update"]["trainable_parameter_tensors"] == 392
    lanes = report["comparison"]["lanes"]
    assert sum(row["generation"]["malformed_sequences_rejected"]
               for row in lanes["pretrained"]["goals"]) == 16
    assert sum(row["generation"]["candidate_lines_returned"]
               for row in lanes["pretrained"]["goals"]) == 0
    assert sum(row["generation"]["candidate_lines_returned"]
               for row in lanes["trained"]["goals"]) == 88
    assert lanes["trained"]["goals"][-1]["status"] == "limit"


def test_archived_alpha_model_replay_receipt_binds_original_proofs() -> None:
    report = _run_receipt("matched-evaluation.json")
    replay = _run_receipt("independent-replay.json")
    assert replay["status"] == "passed"
    assert replay["cuda_initialized"] is False
    assert replay["report_file_sha256"] == _file_sha256("matched-evaluation.json")
    assert replay["adapter_manifest_sha256"] == _file_sha256("training-manifest.json")
    assert replay["evaluation_sha256"] == report["evaluation_sha256"]
    assert replay["metrics"] == report["comparison"]["model_metrics"]
    proofs = [row for row in report["comparison"]["lanes"]["trained"]["goals"]
              if row["status"] == "proof"]
    assert [row["proof_nodes"] for row in proofs] == [98, 29, 21]
    for row, receipt in zip(proofs, replay["independently_replayed_proofs"], strict=True):
        assert receipt["goal"] == row["goal"]
        assert receipt["lane"] == "trained"
        assert receipt["commands"] == row["evidence"]["search"]["commands"]
        assert receipt["proof_nodes"] == row["proof_nodes"]
        assert row["kernel_checked"] is True


def test_archived_next_curriculum_is_isolated_and_not_a_trained_model() -> None:
    original = _run_receipt("preparation-manifest.json")
    source = _run_receipt("next-source-manifest.json")
    preparation = _run_receipt("next-preparation-manifest.json")
    preflight = _run_receipt("next-preflight.json")
    assert "run_id" not in original
    assert preparation["run_id"] == preflight["run_id"] == "catalog-460"
    assert preparation["epoch_sha256"] == original["epoch_sha256"]
    assert preparation["source"]["independently_replayed_catalog_routes"] == 460
    assert preparation["source"]["manifest_sha256"] == _file_sha256(
        "next-source-manifest.json"
    )
    assert preparation["files"]["config.toml"]["sha256"] == _file_sha256(
        "next-preparation-config.toml"
    )
    assert source["transition_count"] == 7154
    assert source["duplicate_transitions_removed"] == 90
    assert preparation["files"]["train.jsonl"]["rows"] == 7129
    assert preparation["files"]["dev.jsonl"]["rows"] == 12
    assert preparation["files"]["dev.jsonl"] == original["files"]["dev.jsonl"]
    assert preflight["quarantined_rows"] == 13
    assert preflight["expected_optimizer_steps"] == 892
    assert preflight["cuda_initialized"] is False
    assert preflight["model_trained"] is False
    assert preparation["model_trained"] is False
    target = preparation["training"]["adapter_output_dir"]
    assert target == preflight["adapter_output_dir"]
    assert target.endswith("-catalog-460")
    assert target != original["training"]["adapter_output_dir"]


def test_archived_cluster_chain_records_only_owned_completed_jobs() -> None:
    model = _run_receipt("training-manifest.json")
    with (ALPHA_MODEL_RUN / "submissions.tsv").open(encoding="utf-8") as stream:
        ledger = {row["job_id"]: row for row in csv.DictReader(stream, delimiter="\t")}
    assert set(ledger) == {"21279542", "21279955", "21279969", "21280018"}
    assert ledger["21279969"]["dependency_job_id"] == "21279955"
    assert ledger["21280018"]["dependency_job_id"] == "21279969"
    assert ledger["21279969"] == model["job"]["submission"]
    assert all(row["git_commit"] == "a4ed24815925adffd45a5fe40423c2df2cf0a665"
               and row["git_dirty"] == "false" for row in ledger.values())
    with (ALPHA_MODEL_RUN / "scheduler-accounting.psv").open(encoding="utf-8") as stream:
        accounting = list(csv.DictReader(stream, delimiter="|"))
    assert {row["JobIDRaw"] for row in accounting if "." not in row["JobIDRaw"]} == set(ledger)
    assert all(row["State"] == "COMPLETED" and row["ExitCode"] == "0:0"
               for row in accounting)


def test_completed_model_run_and_next_milestone_are_consistent_across_guides() -> None:
    sources = (
        ROADMAP, HYDRA_PLAN, PLAN_INDEX, ROOT / "README.md",
        ROOT / "docs" / "HYDRA_POST_TRAINING.md",
        ROOT / "training" / "peano_hydra" / "README.md",
        ROOT / "book" / "peano" / "peano-hydra.md",
        ALPHA_MODEL_RUN / "README.md",
    )
    for source in sources:
        content = source.read_text(encoding="utf-8")
        compact = " ".join(content.split())
        for value in ("222", "0/4", "3/4", "460", "7,129", "H0", "H1"):
            assert value in compact, (source, value)
        assert "symbolic" in compact and "lineage-clean" in compact
        assert "prepared, not trained" in compact.replace("**", "") or (
            source == HYDRA_PLAN and "no second model training" in compact
        )
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = (source.parent / target.split("#", 1)[0]).resolve()
            assert path.is_relative_to(ROOT)
            assert path.exists(), f"broken completed-run link in {source}: {target}"


@pytest.mark.parametrize("filename", PRODUCT_NAVIGATION)
def test_all_linked_hydra_model_and_lean_guides_have_valid_local_destinations(
    filename: str,
) -> None:
    source = ROOT / "docs" / filename
    text = source.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith(("#", "mailto:")):
            continue
        path = (source.parent / target.split("#", 1)[0]).resolve()
        assert path.is_relative_to(ROOT)
        assert path.exists(), f"broken product documentation link in {filename}: {target}"
