"""Bounded structural/evidence audit for the strict-HA grand campaign atlas."""

from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest


REPO = Path(__file__).resolve().parents[3]
CAMPAIGN = REPO / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
EXPLORER = CAMPAIGN.parent / "index.html"
BLUEPRINT = REPO / "PLAN" / "14_constructive_number_theory_grand_campaign.md"
ARITHMETIC_INDEX = REPO / "research" / "arithmetic-library" / "README.md"

EXPECTED_FAMILIES = tuple(f"F{index:02d}" for index in range(1, 13))
EXPECTED_TOOLS = {f"T{index:02d}" for index in range(1, 17)}
EXPECTED_ANCHORS = {f"A{index:02d}" for index in range(1, 9)}
EXPECTED_GOALS = {f"G{index:03d}" for index in range(1, 121)}
ALPHA_V15_IDENTITY = "2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66"
ALPHA_V16_IDENTITY = "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10"
ALPHA_ENROLLMENT_IDENTITY = "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
QR_PROMOTION_NAMES_IDENTITY = "aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e"
ALPHA_V15_EVIDENCE_ROOT = "4d6cba8b48666d8d3cbea7acd2aa937e418a5bfa2e45bc6ebf5b53affd9a921e"
ALPHA_V16_EVIDENCE_ROOT = "142d73d908bd86f52af9b6a1d39a5e11679d1db4f463d3e6f17d5c483f283ee4"
HONEST_STATUSES = {
    "available",
    "stable_closed",
    "alpha_closed",
    "pending_layered_closure",
    "body_checked",
    "existing_foundation",
    "existing_anchor_closure",
    "existing_anchor_extension",
    "open",
}


@lru_cache(maxsize=1)
def campaign() -> dict:
    return json.loads(CAMPAIGN.read_text(encoding="utf-8"))


def dependency_order(nodes: list[dict]) -> list[str]:
    """Reject missing, repeated, same-layer, reversed, or circular edges."""

    by_id = {node["id"]: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("campaign has repeated theorem/tool/anchor identifiers")

    outgoing: dict[str, list[str]] = {identifier: [] for identifier in by_id}
    indegree = {identifier: 0 for identifier in by_id}

    for node in nodes:
        dependencies = node["deps"]
        if len(set(dependencies)) != len(dependencies):
            raise ValueError(f"{node['id']} has repeated prerequisites")
        for dependency in dependencies:
            if dependency not in by_id:
                raise ValueError(f"{node['id']} depends on missing {dependency}")
            if by_id[dependency]["layer"] >= node["layer"]:
                raise ValueError(
                    f"{dependency} -> {node['id']} does not strictly advance layers"
                )
            outgoing[dependency].append(node["id"])
            indegree[node["id"]] += 1

    ready = deque(sorted(identifier for identifier, degree in indegree.items() if not degree))
    ordered: list[str] = []
    while ready:
        identifier = ready.popleft()
        ordered.append(identifier)
        for dependent in outgoing[identifier]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    if len(ordered) != len(nodes):
        raise ValueError("campaign contains a circular dependency")
    return ordered


class ScriptParser(HTMLParser):
    """Extract exact inline scripts without confusing JSON with executable JS."""

    def __init__(self) -> None:
        super().__init__()
        self.current: dict[str, str] | None = None
        self.fragments: list[str] = []
        self.scripts: list[tuple[dict[str, str], str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.current = {key: value or "" for key, value in attrs}
            self.fragments = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.fragments.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.current is not None:
            self.scripts.append((self.current, "".join(self.fragments)))
            self.current = None
            self.fragments = []


def test_campaign_schema_and_exact_144_vertex_inventory() -> None:
    payload = campaign()
    assert payload["schema"] == "constructive-grand-campaign-v1"
    assert len(payload["nodes"]) == 144
    assert len(payload["families"]) == 12

    by_kind = {
        kind: {node["id"] for node in payload["nodes"] if node["kind"] == kind}
        for kind in ("tool", "anchor", "goal")
    }
    assert by_kind["tool"] == EXPECTED_TOOLS
    assert by_kind["anchor"] == EXPECTED_ANCHORS
    assert by_kind["goal"] == EXPECTED_GOALS


def test_all_twelve_mathematical_families_have_ten_goals() -> None:
    payload = campaign()
    assert tuple(family["id"] for family in payload["families"]) == EXPECTED_FAMILIES

    counts = Counter(
        node["family"] for node in payload["nodes"] if node["kind"] == "goal"
    )
    assert counts == Counter({family: 10 for family in EXPECTED_FAMILIES})

    for family_index, family in enumerate(EXPECTED_FAMILIES):
        expected = {
            f"G{goal_index:03d}"
            for goal_index in range(family_index * 10 + 1, family_index * 10 + 11)
        }
        actual = {
            node["id"]
            for node in payload["nodes"]
            if node["kind"] == "goal" and node["family"] == family
        }
        assert actual == expected


def test_dependency_graph_is_closed_and_strictly_layered() -> None:
    payload = campaign()
    order = dependency_order(payload["nodes"])
    assert len(order) == 144

    declared_levels = [layer["number"] for layer in payload["layers"]]
    assert len(declared_levels) == 13
    assert sorted(declared_levels) == list(range(13))

    positions = {identifier: index for index, identifier in enumerate(order)}
    for node in payload["nodes"]:
        assert all(positions[dependency] < positions[node["id"]] for dependency in node["deps"])

    levels = {node["layer"] for node in payload["nodes"]}
    assert levels == set(range(13))
    assert sum(len(node["deps"]) for node in payload["nodes"]) == 303


def test_goal_status_and_layer_census_remain_honest_and_exact() -> None:
    payload = campaign()
    goals = [node for node in payload["nodes"] if node["kind"] == "goal"]
    statuses = Counter(node["status"] for node in goals)
    assert statuses == Counter(
        {
            "open": 102,
            "existing_foundation": 8,
            "existing_anchor_closure": 5,
            "existing_anchor_extension": 4,
            "alpha_closed": 1,
        }
    )

    layer_vertices = Counter(node["layer"] for node in payload["nodes"])
    assert [layer_vertices[level] for level in range(13)] == [
        3, 4, 5, 8, 8, 13, 11, 17, 21, 16, 18, 11, 9
    ]
    layer_goals = Counter(node["layer"] for node in goals)
    assert [layer_goals[level] for level in range(13)] == [
        0, 0, 1, 4, 6, 9, 9, 16, 21, 16, 18, 11, 9
    ]


def test_every_goal_records_real_statement_rationale_and_evidence_status() -> None:
    payload = campaign()
    family_ids = {family["id"] for family in payload["families"]}

    for node in payload["nodes"]:
        assert isinstance(node["title"], str) and node["title"].strip()
        assert isinstance(node["statement"], str) and len(node["statement"].strip()) >= 12
        assert isinstance(node["why"], str) and node["why"].strip()
        assert node["status"] in HONEST_STATUSES
        assert isinstance(node["layer"], int) and 0 <= node["layer"] <= 12
        if node["kind"] == "goal":
            assert node["family"] in family_ids
            assert node.get("difficulty")


def test_existing_anchors_gain_only_the_exact_reviewed_qr_release_authority() -> None:
    anchors = {
        node["id"]: node
        for node in campaign()["nodes"]
        if node["kind"] == "anchor"
    }
    assert anchors["A01"]["status"] == "alpha_closed"
    reciprocity = anchors["A01"]["evidence"]
    assert reciprocity["alpha_version"] == "v16"
    assert reciprocity["release_status"] == "alpha_closed"
    assert reciprocity["checked_use"] is True
    assert reciprocity["stable_member"] is False
    assert reciprocity["alpha_identity_sha256"] == ALPHA_V16_IDENTITY
    assert reciprocity["historical_alpha_v15"] == {
        "release_status": "pending_layered_closure",
        "checked_use": False,
        "identity_sha256": ALPHA_V15_IDENTITY,
    }
    assert reciprocity["full_empty_context_closure"] is True
    assert reciprocity["independent_lean_bundle_verified"] is True
    assert reciprocity["ordinary_proof_nodes"] == 54_870
    assert reciprocity["ordinary_proof_objects"] == 35_052
    assert reciprocity["ordinary_proof_depth"] == 129
    assert reciprocity["bundle_nodes"] == 557
    assert reciprocity["bundle_dependencies"] == 1_787
    assert reciprocity["bundle_sha256"] == (
        "3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c"
    )
    artifact = (
        REPO
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / "quadratic-reciprocity-proof-bundle-v1.json"
    )
    assert sha256(artifact.read_bytes()).hexdigest() == reciprocity["bundle_sha256"]
    assert reciprocity["release_upgraded_by_focused_certificate"] is False
    assert reciprocity["reviewed_dependency_closed_promotion"] is True
    assert anchors["A02"]["status"] == "body_checked"
    assert all(
        anchors[f"A{index:02d}"]["status"] == "body_checked"
        for index in range(3, 9)
    )
    assert {
        anchor["id"]
        for anchor in anchors.values()
        if anchor["status"] in {"stable_closed", "alpha_closed"}
    } == {"A01"}
    assert all(
        anchors[f"A{index:02d}"]["evidence"]["alpha_version"] == "v16"
        and anchors[f"A{index:02d}"]["evidence"]["checked_use"] is False
        for index in range(2, 8)
    )
    assert anchors["A08"]["evidence"]["alpha_enrolled"] is False


def test_current_v16_release_preserves_immutable_v15_evidence_and_stable() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    historical = boundaries["alpha_v15_edition"]
    current = boundaries["alpha_v16_edition"]
    transition = boundaries["quadratic_reciprocity_evidence_transition"]

    assert payload["meta"]["current_alpha_version"] == "v16"
    assert payload["meta"]["historical_alpha_versions"] == ["v15"]
    assert payload["meta"]["current_alpha_checked_use_count"] == 885
    assert boundaries["stable_edition"] == {
        "theorem_count": 432,
        "checked_use_count": 432,
        "changed_by_campaign": False,
    }

    assert historical["role"] == "immutable_historical_parent"
    assert (
        historical["theorem_count"],
        historical["stable_closed_count"],
        historical["alpha_closed_count"],
        historical["body_checked_count"],
        historical["pending_layered_closure_count"],
        historical["checked_use_count"],
    ) == (1_673, 432, 138, 1_102, 1, 570)
    assert historical["identity_sha256"] == ALPHA_V15_IDENTITY
    assert historical["evidence_root_sha256"] == ALPHA_V15_EVIDENCE_ROOT
    assert historical["changed_by_campaign"] is False

    assert current["role"] == "current_immutable_release"
    assert (
        current["theorem_count"],
        current["stable_closed_count"],
        current["alpha_closed_count"],
        current["body_checked_count"],
        current["pending_layered_closure_count"],
        current["checked_use_count"],
    ) == (1_673, 432, 453, 788, 0, 885)
    assert current["checked_use_promotion_count"] == 315
    assert current["dependency_edge_count"] == 5_615
    assert current["checked_dependency_edge_count"] == 2_641
    assert current["layer_count"] == 53
    assert current["identity_sha256"] == ALPHA_V16_IDENTITY
    assert current["evidence_root_sha256"] == ALPHA_V16_EVIDENCE_ROOT
    assert current["promoted_names_sha256"] == QR_PROMOTION_NAMES_IDENTITY
    assert current["stable_unchanged"] is True
    assert current["historical_v15_unchanged"] is True
    assert current["promoted_origin"] == "quadratic_reciprocity_only"
    assert historical["enrollment_sha256"] == current["enrollment_sha256"]
    assert current["enrollment_sha256"] == ALPHA_ENROLLMENT_IDENTITY

    assert transition["historical_v15"] == {
        "stable_closed": 241,
        "alpha_closed": 1,
        "body_checked": 314,
        "pending_layered_closure": 1,
    }
    assert transition["current_v16"] == {
        "stable_closed": 241,
        "alpha_closed": 316,
        "body_checked": 0,
        "pending_layered_closure": 0,
    }
    assert transition["promoted_body_checked_count"] == 314
    assert transition["promoted_pending_root_count"] == 1
    assert transition["unrelated_body_roots_promoted"] == 0
    assert transition["bundle_node_count"] == 557
    assert transition["dependency_edge_count"] == 1_787


def test_quadratic_reciprocity_goal_uses_current_exact_anchor_evidence() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    goal = nodes["G043"]

    assert goal["status"] == "alpha_closed"
    assert goal["evidence"] == {
        "anchor": "A01",
        "alpha_version": "v16",
        "anchor_release_status": "alpha_closed",
        "full_empty_context_closure": True,
        "independent_lean_bundle_verified": True,
        "checked_use": True,
        "stable_member": False,
        "historical_alpha_v15_release_status": "pending_layered_closure",
    }
    for identifier in ("G033", "G034", "G044", "G062", "G064"):
        assert nodes[identifier]["status"] == "existing_anchor_closure"
        assert nodes[identifier]["evidence"]["checked_use"] is False


def test_versioned_campaign_sources_distinguish_current_and_historical_channels() -> None:
    sources = {source["id"]: source for source in campaign()["sources"]}

    assert sources["S01"]["path"] == "artifacts/peano-library/channels-v15.json"
    assert "v15" in sources["S01"]["label"]
    assert sources["S09"]["path"] == "artifacts/peano-library/channels-v16.json"
    assert "v16" in sources["S09"]["label"]
    assert {"S01", "S09"} <= set(
        next(node for node in campaign()["nodes"] if node["id"] == "A01")[
            "references"
        ]
    )


def test_campaign_release_evidence_matches_both_immutable_channel_artifacts() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    historical_channels = json.loads(
        (REPO / "artifacts" / "peano-library" / "channels-v15.json").read_text(
            encoding="utf-8"
        )
    )
    current_channels = json.loads(
        (REPO / "artifacts" / "peano-library" / "channels-v16.json").read_text(
            encoding="utf-8"
        )
    )

    for version, channels in (("v15", historical_channels), ("v16", current_channels)):
        declared = boundaries[f"alpha_{version}_edition"]
        alpha = channels["channels"]["alpha"]
        assert alpha["theorem_count"] == declared["theorem_count"]
        assert alpha["checked_use_count"] == declared["checked_use_count"]
        assert alpha["edition_identity_sha256"] == declared["identity_sha256"]
        assert alpha["evidence_root_sha256"] == declared["evidence_root_sha256"]
        assert alpha["ordered_enrollment_root_sha256"] == declared["enrollment_sha256"]
        assert alpha["evidence_counts"].get("stable_closed", 0) == declared[
            "stable_closed_count"
        ]
        assert alpha["evidence_counts"].get("alpha_closed", 0) == declared[
            "alpha_closed_count"
        ]
        assert alpha["evidence_counts"].get("body_checked", 0) == declared[
            "body_checked_count"
        ]
        assert alpha["evidence_counts"].get("pending_layered_closure", 0) == declared[
            "pending_layered_closure_count"
        ]
        assert channels["channels"]["stable"] == historical_channels["channels"]["stable"]

    assert current_channels["parent_channels_v15"]["path"] == (
        "artifacts/peano-library/channels-v15.json"
    )


def test_strict_heyting_signature_and_conservative_definitions_are_explicit() -> None:
    language = campaign()["language"]
    signature = {str(symbol).replace("×", "*") for symbol in language["base_signature"]}
    assert signature == {"0", "S", "+", "*", "="}
    assert "intuitionistic" in language["logic"].lower()
    definitions = campaign()["definitions"]
    assert "Prime" in definitions
    assert "PowerValuation" in definitions


def test_blueprint_has_exactly_one_contract_for_every_goal_and_twelve_families() -> None:
    document = BLUEPRINT.read_text(encoding="utf-8")
    ids = re.findall(r"^\d+\. \*\*(G\d{3})\b", document, flags=re.MULTILINE)
    assert len(ids) == 120
    assert set(ids) == EXPECTED_GOALS

    families = re.findall(r"^### (F\d{2})\.", document, flags=re.MULTILINE)
    assert tuple(families) == EXPECTED_FAMILIES
    for value in (
        "Alpha v16", "1,673", "453", "788", "885", "315",
        "Alpha v15", "138", "1,102", "570",
        "pending_layered_closure", "body_checked",
    ):
        assert value in document
    assert ALPHA_V16_IDENTITY in document
    assert ALPHA_V16_EVIDENCE_ROOT in document
    assert ALPHA_ENROLLMENT_IDENTITY in document


def test_phase_split_mermaid_overview_is_a_genuine_dag() -> None:
    document = BLUEPRINT.read_text(encoding="utf-8")
    diagrams = re.findall(r"```mermaid\n(.*?)\n```", document, flags=re.DOTALL)
    assert len(diagrams) == 1

    edges = re.findall(
        r"^\s*([A-Z][A-Z0-9]*)\s*(?:\[[^\]]*\])?\s*-->\s*([A-Z][A-Z0-9]*)",
        diagrams[0],
        flags=re.MULTILINE,
    )
    assert len(edges) >= 25

    vertices = {vertex for edge in edges for vertex in edge}
    indegree = {vertex: 0 for vertex in vertices}
    outgoing = {vertex: [] for vertex in vertices}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1

    ready = deque(sorted(vertex for vertex in vertices if indegree[vertex] == 0))
    visited: list[str] = []
    while ready:
        vertex = ready.popleft()
        visited.append(vertex)
        for target in outgoing[vertex]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)

    assert len(visited) == len(vertices)
    assert {"F05A", "F05B", "F09A", "F09B", "F12A", "F12B"} <= vertices


def test_high_prestige_prime_distribution_summits_are_numbered() -> None:
    by_id = {node["id"]: node for node in campaign()["nodes"]}
    assert "zsigmondy" in by_id["G028"]["title"].lower()
    assert "prime number" in by_id["G029"]["title"].lower()
    assert "dirichlet" in by_id["G030"]["title"].lower()


def test_mathematical_exception_domains_and_nonvacuity_are_preserved() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    definitions = payload["definitions"]

    zsigmondy = nodes["G028"]["statement"]
    assert all(part in zsigmondy for part in ("n=2", "a+b=2^j", "a=2", "b=1", "n=6"))
    assert "LogBracket" in nodes["G029"]["statement"]
    assert "q>0" in nodes["G030"]["statement"]
    assert "Coprime(a,q)" in nodes["G030"]["statement"]
    assert "0<m≤N" in nodes["G007"]["statement"]
    assert "0<n≤N" in nodes["G007"]["statement"]
    assert "∀N>0" in nodes["G009"]["statement"]
    assert "0<n≤N" in definitions["Convolution"]["expansion"]

    davenport = nodes["G057"]["statement"]
    assert "invariant-factor" in davenport
    assert "n1∣n2∣" in davenport
    assert "p-group" in davenport and "rank≤2" in davenport

    triple = definitions["PrimitiveTriple"]["expansion"]
    assert "Dvd(2,b)" not in triple
    pythagorean = nodes["G077"]["statement"]
    assert "a=m²-k² ∧ b=2*m*k" in pythagorean
    assert "a=2*m*k ∧ b=m²-k²" in pythagorean

    assert "p=2 ∧ GNorm(z,2)" in nodes["G083"]["statement"]
    assert "p=3 ∧ ENorm(z,3)" in nodes["G086"]["statement"]
    cyclotomic = nodes["G089"]["statement"]
    assert all(part in cyclotomic for part in ("m=1→u=0", "∀p k.", "u=p", "u=1"))

    hilbert = definitions["HilbertProduct"]["expansion"]
    assert "DUPLICATE-FREE" in hilbert and "EXACTLY ONCE" in hilbert
    assert "HilbertBit(a,b,v,s_v)" in hilbert

    polygon = nodes["G098"]["statement"]
    assert "f=X^v*g" in polygon
    assert "ONLY NONZERO coefficients" in polygon
    assert "NEGATIVE" in polygon
    assert "horizontal-length multiplicity" in polygon
    assert "COUPLED source precision" in nodes["G100"]["statement"]


def test_elliptic_boundaries_and_algorithm_complexity_are_not_overclaimed() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    for identifier in ("G111", "G113", "G114", "G119"):
        assert "p>3" in nodes[identifier]["statement"]

    for identifier in ("G117", "G118", "G120"):
        assert "THREE witnessed distinct rational roots" in nodes[identifier]["statement"]

    recurrence = nodes["G119"]["statement"]
    assert "∀r≥1" in recurrence
    assert "At(T,0,2)" in recurrence
    assert "At(T,1,a)" in recurrence
    assert "j+2≤r" in recurrence

    for identifier in ("G105", "G114"):
        assert "Execution(" in nodes[identifier]["statement"]
        assert "polynomial" not in nodes[identifier]["statement"].lower()
        assert "separate" in nodes[identifier]["why"].lower()
    assert "do not compute" in nodes["G120"]["why"].lower()


def test_cross_family_summits_retain_required_transitive_prerequisites() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}

    @lru_cache(maxsize=None)
    def predecessors(identifier: str) -> frozenset[str]:
        direct = frozenset(nodes[identifier]["deps"])
        return direct.union(
            *(predecessors(dependency) for dependency in direct)
        )

    expected = {
        "G028": {"G088"},
        "G030": {"G029", "G088"},
        "G047": {"G085"},
        "G048": {"G082"},
        "G067": {"G066"},
        "G069": {"G066", "G095", "G068"},
        "G078": {"G077", "G061"},
        "G079": {"G084", "G085"},
        "G090": {"G088", "G089"},
        "G114": {"G111", "G113"},
        "G120": {"G117", "G118"},
    }
    for summit, prerequisites in expected.items():
        assert prerequisites <= predecessors(summit)


def test_blueprint_distinguishes_priority_from_topological_execution() -> None:
    blueprint = BLUEPRINT.read_text(encoding="utf-8")
    assert "Thirteen proof-engineering layers" in blueprint
    assert "strictly increasing layers `0,...,12`" in blueprint
    assert "| **Total** | **144** | **120** |" in blueprint
    assert "canonical invariant-factor decomposition" in blueprint
    assert "negatives of the" in blueprint
    assert "canonical duplicate-free" in blueprint
    assert "not a theorem about every genus-one lattice" in blueprint
    assert "prime/two-square" in blueprint


def test_interactive_viewer_embeds_the_exact_portable_campaign_snapshot() -> None:
    parser = ScriptParser()
    parser.feed(EXPLORER.read_text(encoding="utf-8"))
    snapshots = [
        content
        for attributes, content in parser.scripts
        if attributes.get("id") == "campaign-data"
        and attributes.get("type") == "application/json"
    ]
    assert len(snapshots) == 1
    assert json.loads(snapshots[0]) == campaign()

    executable = [
        content
        for attributes, content in parser.scripts
        if attributes.get("type") != "application/json"
    ]
    assert len(executable) == 1
    assert 'window.location.protocol === "file:"' in executable[0]
    assert 'fetch("./campaign.json"' in executable[0]
    assert 'setAttribute("viewBox"' in executable[0]
    assert not re.search(r"\.href\s*=", executable[0])
    assert "Independently proved; sealed release promotion pending" in executable[0]


def test_interactive_campaign_snapshot_sync_is_reproducible() -> None:
    updater = REPO / "scripts" / "sync_constructive_grand_campaign.py"
    result = subprocess.run(
        ["python3", str(updater), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "snapshot verified" in result.stdout


def test_interactive_viewer_javascript_parses_without_external_dependencies() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed on this workstation")

    parser = ScriptParser()
    parser.feed(EXPLORER.read_text(encoding="utf-8"))
    executable = next(
        content
        for attributes, content in parser.scripts
        if attributes.get("type") != "application/json"
    )
    completed = subprocess.run(
        [node, "-e", "new Function(process.argv[1]);", executable],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_arithmetic_library_index_exposes_blueprint_dataset_and_explorer() -> None:
    index = ARITHMETIC_INDEX.read_text(encoding="utf-8")
    assert "14_constructive_number_theory_grand_campaign.md" in index
    assert "constructive-grand-campaign/campaign.json" in index
    assert "constructive-grand-campaign/index.html" in index


@pytest.mark.parametrize("mutation", ["missing", "same-layer", "duplicate"])
def test_invalid_dependency_graph_mutations_fail_closed(mutation: str) -> None:
    nodes = [dict(node, deps=list(node["deps"])) for node in campaign()["nodes"]]
    target = next(node for node in nodes if node["kind"] == "goal" and node["deps"])
    by_id = {node["id"]: node for node in nodes}

    if mutation == "missing":
        target["deps"][0] = "MISSING"
    elif mutation == "same-layer":
        by_id[target["deps"][0]]["layer"] = target["layer"]
    else:
        target["deps"].append(target["deps"][0])

    with pytest.raises(ValueError):
        dependency_order(nodes)
