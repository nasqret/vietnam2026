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
ALPHA_V17_IDENTITY = "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4"
ALPHA_V18_IDENTITY = "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
ALPHA_V19_IDENTITY = "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7"
ALPHA_V18_CATALOG_SHA256 = "cfbaeaf5d89be609d09aa2b84c9d102297a45b7b6aeeea6efcd32b1b328e62b2"
ALPHA_V19_CATALOG_SHA256 = "f1c3d3fba013ca3a5b62a4103dd00bd5b7e39b1f785ed9023099704ad033004b"
ALPHA_ENROLLMENT_IDENTITY = "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
ALPHA_V19_ENROLLMENT_IDENTITY = "1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795"
QR_PROMOTION_NAMES_IDENTITY = "aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e"
SUPPLEMENT_PROMOTION_NAMES_IDENTITY = "21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7"
FLAGSHIP_PROMOTION_NAMES_IDENTITY = "5b6faad95b90a3b3f11e6aea929aefd3cdbf9b5a1f3563e57d8e48f15e9d59e6"
RESIDUAL_PROMOTION_NAMES_IDENTITY = "0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e"
FRONTIER_NEW_NAMES_IDENTITY = "07b9c92ab3ef80dc609681a9b588d21b0faeb69e87448c1420b78272a54aaed1"
SUPPLEMENT_BUNDLE_IDENTITY = "79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c"
RESIDUAL_BUNDLE_IDENTITY = "e69112c5e3b8c21bc452ad35838474f2af2e297152ff73fbdc62bfd935ffdebb"
FRONTIER_BUNDLE_IDENTITY = "cf7947a944d54e9eb956fb153702b29c953100ece6cf05743162759b0fba9b17"
ALPHA_V15_EVIDENCE_ROOT = "4d6cba8b48666d8d3cbea7acd2aa937e418a5bfa2e45bc6ebf5b53affd9a921e"
ALPHA_V16_EVIDENCE_ROOT = "142d73d908bd86f52af9b6a1d39a5e11679d1db4f463d3e6f17d5c483f283ee4"
ALPHA_V17_EVIDENCE_ROOT = "e631e3a9bfc680c3b84630db71903f817cb740c2cc830958b5dc7bcedaed19a1"
ALPHA_V18_EVIDENCE_ROOT = "def31d268c4fef3a3e598fa2447b9be92e9c54aae7ec9f227e6948c752ecb6f9"
ALPHA_V19_EVIDENCE_ROOT = "627f651198360aa95b8efd085b98f694d88c883434309f6050a819bc249c90c4"
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


@lru_cache(maxsize=None)
def alpha_catalog(version: str) -> dict[str, dict]:
    catalog = json.loads(
        (REPO / "artifacts" / "peano-library" / "alpha" / f"catalog-{version}.json").read_text(
            encoding="utf-8"
        )
    )
    return {theorem["name"]: theorem for theorem in catalog["theorems"]}


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

        conceptual = node.get("conceptual_refs", [])
        if not isinstance(conceptual, list) or len(set(conceptual)) != len(conceptual):
            raise ValueError(f"{node['id']} has invalid or repeated conceptual connections")
        for related in conceptual:
            if related not in by_id or related == node["id"]:
                raise ValueError(f"{node['id']} has a missing or self-referential conceptual connection")
            if related in dependencies:
                raise ValueError(f"{node['id']} conflates conceptual and proof dependencies")

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
            "open": 97,
            "existing_foundation": 6,
            "existing_anchor_extension": 3,
            "stable_closed": 1,
            "alpha_closed": 13,
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


def test_checked_milestones_bind_exact_actual_release_theorems() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    catalog = alpha_catalog(payload["meta"]["current_alpha_version"])
    expected = {
        "G012": ("linear_congruence_solvable_iff_gcd_divides", "alpha_closed", False),
        "G013": ("mod_eq_cancel_coprime", "stable_closed", True),
        "G026": ("infinitely_many_primes_one_mod_four", "alpha_closed", False),
        "G041": ("arbitrary_euler_criterion_complete", "alpha_closed", False),
        "G042": ("arbitrary_gauss_lemma_complete", "alpha_closed", False),
        "G061": (
            "prime_is_two_squares_iff_two_or_one_mod_four",
            "alpha_closed",
            False,
        ),
    }

    for identifier, (theorem_name, status, stable_member) in expected.items():
        node = nodes[identifier]
        evidence = node["evidence"]
        theorem = catalog[theorem_name]
        assert node["status"] == theorem["evidence_status"] == status
        assert evidence["theorem_name"] == theorem_name
        assert evidence["alpha_version"] == payload["meta"]["current_alpha_version"]
        assert evidence["release_status"] == theorem["evidence_status"]
        assert evidence["checked_use"] is theorem["checked_use"] is True
        assert evidence["stable_member"] is stable_member
        assert {"S09", "S10", "S14"} <= set(node["references"])
        if identifier in {"G012", "G026", "G061"}:
            assert evidence["theorem_statement_sha256"] == theorem["statement_sha256"]
            assert evidence["historical_alpha_v18_enrolled"] is False
            assert theorem_name not in alpha_catalog("v18")
            closure = theorem["empty_context_closure"]
            assert closure["bundle_campaign"] == "frontier"
            assert closure["certificate_sha256"] == FRONTIER_BUNDLE_IDENTITY

    assert "m>0" in nodes["G013"]["statement"]
    assert "~(m = 0)" in catalog["mod_eq_cancel_coprime"]["statement"]
    assert "Pow(a,h,A)" in nodes["G041"]["statement"]
    assert "Mod(A,p-1,p)" in nodes["G041"]["statement"]
    assert "x<p" not in nodes["G041"]["statement"]
    assert catalog["arbitrary_euler_criterion_complete"]["statement"].startswith(
        "forall p a n h A."
    )
    assert "b,c code [1,…,h]" in nodes["G042"]["statement"]
    assert "∃e." in nodes["G042"]["statement"]
    assert catalog["arbitrary_gauss_lemma_complete"]["statement"].startswith(
        "forall p h a b c."
    )


def test_valuation_interface_closes_all_exact_prime_specific_wrappers() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    catalog = alpha_catalog(payload["meta"]["current_alpha_version"])
    node = nodes["T09"]
    evidence = node["evidence"]
    formerly_unclosed = {
        "prime_power_valuation_exists",
        "prime_power_valuation_functional",
    }
    closed = formerly_unclosed | {
        "power_valuation_exact_cofactor",
        "prime_power_valuation_mul",
    }
    alternatives = {
        "power_valuation_exists",
        "power_valuation_functional",
    }

    assert node["status"] == evidence["release_status"] == "alpha_closed"
    assert set(evidence["theorem_names"]) == closed
    assert set(evidence["checked_theorem_names"]) == closed
    assert evidence["unchecked_theorem_names"] == []
    assert set(evidence["historical_alpha_v18_unchecked_theorem_names"]) == (
        formerly_unclosed
    )
    assert set(evidence["alternative_checked_theorem_names"]) == alternatives
    assert evidence["alpha_enrolled"] is True
    assert evidence["checked_use"] is True
    assert evidence["partial_checked_use"] is False
    assert evidence["stable_member"] is False
    for name in closed | alternatives:
        assert catalog[name]["evidence_status"] == "alpha_closed"
        assert catalog[name]["checked_use"] is True
    for name in formerly_unclosed:
        historical = alpha_catalog("v18")[name]
        assert historical["evidence_status"] == "body_checked"
        assert historical["checked_use"] is False
        closure = catalog[name]["empty_context_closure"]
        assert closure["bundle_campaign"] == "residual"
        assert closure["certificate_sha256"] == RESIDUAL_BUNDLE_IDENTITY


def test_pascal_and_legendre_milestones_bind_exact_new_checked_theorems() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    catalog = alpha_catalog(payload["meta"]["current_alpha_version"])
    expected = {
        "G031": {
            "choose_exists",
            "choose_functional",
            "beta_pascal_table_successor_cell_recurrence",
        },
        "G032": {"prime_factorial_valuation_eq_legendre_sum"},
    }

    for identifier, expected_names in expected.items():
        node = nodes[identifier]
        evidence = node["evidence"]
        names = set(evidence.get("theorem_names", [evidence.get("theorem_name")]))
        assert names == expected_names
        assert node["status"] == evidence["release_status"] == "alpha_closed"
        assert evidence["alpha_enrolled"] is True
        assert evidence["checked_use"] is True
        assert evidence["stable_member"] is False
        assert "S14" in node["references"]
        for name in names:
            assert catalog[name]["evidence_status"] == "alpha_closed"
            assert catalog[name]["checked_use"] is True

    assert "FactorialValuation(p,n,e)" in nodes["G032"]["statement"]
    assert "LegendreSum(p,n,s)" in nodes["G032"]["statement"]
    assert "T09" not in nodes["G032"]["deps"]
    assert nodes["G032"]["conceptual_refs"] == ["T09"]


def test_finite_generalized_crt_is_not_confused_with_checked_binary_crt() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    catalog = alpha_catalog(payload["meta"]["current_alpha_version"])
    finite = nodes["G011"]
    evidence = finite["evidence"]

    assert finite["status"] == "open"
    assert evidence["available_scope"] == "two congruences"
    assert "arbitrary compatible finite lists" in evidence["target_scope"]
    assert evidence["finite_list_constructor_proved"] is False
    assert evidence["checked_use"] is False
    assert evidence["partial_release_status"] == "stable_closed"
    assert evidence["partial_checked_use"] is True
    for name in evidence["partial_theorem_names"]:
        assert catalog[name]["evidence_status"] == "stable_closed"
        assert catalog[name]["checked_use"] is True


def test_unbuilt_polynomial_and_matrix_tools_are_honest_blockers() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    for identifier in ("T12", "T13"):
        node = nodes[identifier]
        evidence = node["evidence"]
        assert node["kind"] == "tool"
        assert node["status"] == "open"
        assert evidence == {
            "implementation": "unbuilt",
            "alpha_enrolled": False,
            "checked_use": False,
            "stable_member": False,
        }

    assert "T12" in nodes["G095"]["deps"]
    assert "T13" not in nodes["A06"]["deps"]
    assert "T13" not in nodes["A08"]["deps"]


def test_conceptual_connections_do_not_become_false_proof_dependencies() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    policy = payload["dependency_policy"]

    assert "actual construction prerequisites" in policy["deps"].lower()
    assert "do not create arrows" in policy["conceptual_refs"]
    assert nodes["A06"]["deps"] == ["T08", "T11", "T15"]
    assert nodes["A06"]["conceptual_refs"] == ["A05"]
    assert nodes["A06"]["evidence"]["first_admission"] == "v13"
    assert nodes["A05"]["evidence"]["first_admission"] == "v15"
    assert nodes["A07"]["deps"] == ["T04", "T11", "G031"]
    assert nodes["A07"]["conceptual_refs"] == ["A04", "T09"]
    assert nodes["A07"]["evidence"]["first_admission"] == "v13"
    assert nodes["A04"]["evidence"]["first_admission"] == "v14"
    assert "T09" not in nodes["A01"]["deps"]
    assert "T09" not in nodes["G041"]["deps"]
    assert nodes["G026"]["deps"] == ["A03", "T08"]
    assert nodes["G026"]["conceptual_refs"] == ["G025"]
    assert nodes["G026"]["evidence"]["three_mod_four_infinitude_required"] is False
    assert nodes["G025"]["status"] == "open"


def test_closed_milestones_do_not_depend_on_unavailable_constructions() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    unchecked = {
        "open",
        "body_checked",
        "pending_layered_closure",
        "existing_anchor_closure",
        "existing_anchor_extension",
    }

    for node in nodes.values():
        if node["status"] not in {"stable_closed", "alpha_closed"}:
            continue
        frontier = list(node["deps"])
        visited: set[str] = set()
        while frontier:
            identifier = frontier.pop()
            if identifier in visited:
                continue
            visited.add(identifier)
            prerequisite = nodes[identifier]
            assert prerequisite["status"] not in unchecked, (
                f"checked {node['id']} cannot require "
                f"{identifier} ({prerequisite['status']})"
            )
            frontier.extend(prerequisite["deps"])


def test_existing_anchors_gain_only_exact_reviewed_dependency_closed_authority() -> None:
    anchors = {
        node["id"]: node
        for node in campaign()["nodes"]
        if node["kind"] == "anchor"
    }
    assert anchors["A01"]["status"] == "alpha_closed"
    reciprocity = anchors["A01"]["evidence"]
    assert reciprocity["alpha_version"] == "v19"
    assert reciprocity["release_status"] == "alpha_closed"
    assert reciprocity["checked_use"] is True
    assert reciprocity["stable_member"] is False
    assert reciprocity["alpha_identity_sha256"] == ALPHA_V19_IDENTITY
    assert reciprocity["historical_alpha_v15"] == {
        "release_status": "pending_layered_closure",
        "checked_use": False,
        "identity_sha256": ALPHA_V15_IDENTITY,
    }
    assert reciprocity["historical_alpha_v16"] == {
        "release_status": "alpha_closed",
        "checked_use": True,
        "identity_sha256": ALPHA_V16_IDENTITY,
    }
    assert reciprocity["historical_alpha_v17"] == {
        "release_status": "alpha_closed",
        "checked_use": True,
        "identity_sha256": ALPHA_V17_IDENTITY,
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
    supplementary = anchors["A03"]
    assert supplementary["status"] == "alpha_closed"
    evidence = supplementary["evidence"]
    assert evidence["first_admission"] == "v15"
    assert evidence["alpha_version"] == "v19"
    assert evidence["release_status"] == "alpha_closed"
    assert evidence["checked_use"] is True
    assert evidence["stable_member"] is False
    assert evidence["full_empty_context_closure"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert evidence["theorem_names"] == [
        "quadratic_supplement_minus_one_complete",
        "quadratic_supplement_two_complete",
    ]
    assert evidence["historical_alpha_v16"] == {
        "release_status": "body_checked",
        "checked_use": False,
        "identity_sha256": ALPHA_V16_IDENTITY,
    }
    assert evidence["historical_alpha_v17"] == {
        "release_status": "alpha_closed",
        "checked_use": True,
        "identity_sha256": ALPHA_V17_IDENTITY,
    }
    assert evidence["alpha_identity_sha256"] == ALPHA_V19_IDENTITY
    assert evidence["promoted_dependency_count"] == 31
    assert evidence["dependency_theorem_count"] == 437
    assert evidence["bundle_nodes"] == 438
    assert evidence["bundle_dependencies"] == 1_429
    assert evidence["bundle_body_proof_nodes"] == 33_173
    assert evidence["bundle_bytes"] == 1_732_249
    assert evidence["bundle_sha256"] == SUPPLEMENT_BUNDLE_IDENTITY
    assert evidence["promoted_names_sha256"] == SUPPLEMENT_PROMOTION_NAMES_IDENTITY
    actual_bundle = (
        REPO
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / "supplementary-laws-proof-bundle-v1.json"
    ).read_bytes()
    assert len(actual_bundle) == evidence["bundle_bytes"]
    assert sha256(actual_bundle).hexdigest() == evidence["bundle_sha256"]
    bundle = json.loads(actual_bundle)
    assert bundle[0] == "peano-lab-bundle-v1"
    assert bundle[1] == 437
    assert len(bundle[3]) == 438

    assert {
        anchor["id"]
        for anchor in anchors.values()
        if anchor["status"] in {"stable_closed", "alpha_closed"}
    } == {f"A{index:02d}" for index in range(1, 9)}
    exact = {
        "A02": ("bertrand_strict", 544, 1_917, 241),
        "A04": ("kummer_binomial_carry_bit_count", 281, 779, 73),
        "A05": (
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
            517,
            1_599,
            89,
        ),
        "A06": ("four_square_lagrange", 390, 1_187, 196),
        "A07": ("lucas_theorem", 213, 617, 74),
    }
    catalog = alpha_catalog("v19")
    for identifier, (name, node_count, edges, promoted) in exact.items():
        anchor = anchors[identifier]
        proof = anchor["evidence"]
        assert anchor["status"] == "alpha_closed"
        assert proof["alpha_version"] == "v19"
        assert proof["release_status"] == "alpha_closed"
        assert proof["checked_use"] is True
        assert proof["stable_member"] is False
        assert proof["full_empty_context_closure"] is True
        assert proof["independent_lean_bundle_verified"] is True
        assert proof["bundle_nodes"] == node_count
        assert proof["bundle_dependencies"] == edges
        assert proof["promoted_dependency_count"] == promoted
        assert proof["historical_alpha_v17"] == {
            "release_status": "body_checked",
            "checked_use": False,
            "identity_sha256": ALPHA_V17_IDENTITY,
        }
        assert catalog[name]["evidence_status"] == "alpha_closed"
        assert catalog[name]["checked_use"] is True
        assert alpha_catalog("v17")[name]["evidence_status"] == "body_checked"
        assert "S14" in anchor["references"]

    assert anchors["A04"]["evidence"]["root_node_ids"] == [277, 279]
    assert anchors["A04"]["evidence"]["synthetic_root_node_id"] == 280
    assert anchors["A04"]["evidence"]["ordinary_root_proof_nodes"] == [23_564, 24_170]
    bertrand = anchors["A02"]["evidence"]
    assert (
        bertrand["ordinary_proof_nodes"],
        bertrand["ordinary_proof_objects"],
        bertrand["ordinary_proof_depth"],
        bertrand["ordinary_proof_envelope_depth"],
        bertrand["interned_body_proof_objects"],
    ) == (201_285, 45_254, 235, 244, 31_694)
    forward = anchors["A08"]
    evidence = forward["evidence"]
    assert forward["status"] == "alpha_closed"
    assert evidence["alpha_version"] == "v19"
    assert evidence["release_status"] == "alpha_closed"
    assert evidence["alpha_enrolled"] is True
    assert evidence["checked_use"] is True
    assert evidence["stable_member"] is False
    assert evidence["new_theorem_count"] == 44
    assert evidence["historical_alpha_v18_enrolled"] is False
    assert evidence["inverse_parametrization_complete"] is False
    assert evidence["fermat_four_descent_complete"] is False
    assert evidence["theorem_names"] == [
        "pythagorean_primitive_euclidean_from_order",
        "pythagorean_primitive_normal_form",
    ]
    for name in evidence["theorem_names"]:
        assert name not in alpha_catalog("v18")
        assert catalog[name]["evidence_status"] == "alpha_closed"
        assert catalog[name]["checked_use"] is True
        closure = catalog[name]["empty_context_closure"]
        assert closure["bundle_campaign"] == "frontier"
        assert closure["certificate_sha256"] == FRONTIER_BUNDLE_IDENTITY
    assert evidence["theorem_statement_sha256"] == catalog[
        "pythagorean_primitive_euclidean_from_order"
    ]["statement_sha256"]
    assert evidence["normal_form_statement_sha256"] == catalog[
        "pythagorean_primitive_normal_form"
    ]["statement_sha256"]


@pytest.mark.parametrize(
    ("identifier", "source", "campaign_label", "roots"),
    (
        ("A02", "S21", "bertrand", ("bertrand_strict",)),
        (
            "A04",
            "S19",
            "kummer",
            ("kummer_binomial_carry_bit_count", "kummer_carry_free_iff_not_divides"),
        ),
        (
            "A05",
            "S25",
            "two_square",
            ("two_square_iff_zero_or_even_three_mod_four_prime_valuations",),
        ),
        ("A06", "S23", "four_square", ("four_square_lagrange",)),
        ("A07", "S17", "lucas", ("lucas_theorem",)),
    ),
)
def test_every_new_checked_anchor_binds_exact_frozen_bundle_and_catalog_nodes(
    identifier: str,
    source: str,
    campaign_label: str,
    roots: tuple[str, ...],
) -> None:
    payload = campaign()
    anchor = next(node for node in payload["nodes"] if node["id"] == identifier)
    evidence = anchor["evidence"]
    reference = next(item for item in payload["sources"] if item["id"] == source)
    artifact = REPO / reference["path"]
    digest = sha256()
    with artifact.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            digest.update(chunk)

    assert artifact.stat().st_size == evidence["bundle_bytes"]
    assert digest.hexdigest() == evidence["bundle_sha256"]
    catalog = alpha_catalog("v18")
    for name in roots:
        closure = catalog[name]["empty_context_closure"]
        assert closure["bundle_campaign"] == campaign_label
        assert closure["bundle_path"] == reference["path"]
        assert closure["certificate_sha256"] == evidence["bundle_sha256"]
        assert closure["bundle_node_count"] == evidence["bundle_nodes"]
        assert closure["bundle_dependency_edge_count"] == evidence["bundle_dependencies"]


def test_current_v19_release_preserves_v15_v16_v17_v18_evidence_and_stable() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    ancestor = boundaries["alpha_v15_edition"]
    historical = boundaries["alpha_v16_edition"]
    supplementary_parent = boundaries["alpha_v17_edition"]
    parent = boundaries["alpha_v18_edition"]
    current = boundaries["alpha_v19_edition"]
    transition = boundaries["quadratic_reciprocity_evidence_transition"]
    supplementary = boundaries["supplementary_laws_evidence_transition"]
    flagship = boundaries["flagship_evidence_transition"]
    residual = boundaries["residual_evidence_transition"]
    frontier = boundaries["frontier_evidence_transition"]

    assert payload["meta"]["current_alpha_version"] == "v19"
    assert payload["meta"]["historical_alpha_versions"] == [
        "v15", "v16", "v17", "v18"
    ]
    assert payload["meta"]["current_alpha_checked_use_count"] == 1_737
    assert boundaries["stable_edition"] == {
        "theorem_count": 432,
        "checked_use_count": 432,
        "changed_by_campaign": False,
    }

    assert ancestor["role"] == "immutable_historical_ancestor"
    assert (
        ancestor["theorem_count"],
        ancestor["stable_closed_count"],
        ancestor["alpha_closed_count"],
        ancestor["body_checked_count"],
        ancestor["pending_layered_closure_count"],
        ancestor["checked_use_count"],
    ) == (1_673, 432, 138, 1_102, 1, 570)
    assert ancestor["identity_sha256"] == ALPHA_V15_IDENTITY
    assert ancestor["evidence_root_sha256"] == ALPHA_V15_EVIDENCE_ROOT
    assert ancestor["changed_by_campaign"] is False

    assert historical["role"] == "immutable_historical_ancestor"
    assert (
        historical["theorem_count"],
        historical["stable_closed_count"],
        historical["alpha_closed_count"],
        historical["body_checked_count"],
        historical["pending_layered_closure_count"],
        historical["checked_use_count"],
    ) == (1_673, 432, 453, 788, 0, 885)
    assert historical["checked_use_promotion_count"] == 315
    assert historical["dependency_edge_count"] == 5_615
    assert historical["checked_dependency_edge_count"] == 2_641
    assert historical["layer_count"] == 53
    assert historical["identity_sha256"] == ALPHA_V16_IDENTITY
    assert historical["evidence_root_sha256"] == ALPHA_V16_EVIDENCE_ROOT
    assert historical["promoted_names_sha256"] == QR_PROMOTION_NAMES_IDENTITY
    assert historical["stable_unchanged"] is True
    assert historical["historical_v15_unchanged"] is True
    assert historical["promoted_origin"] == "quadratic_reciprocity_only"
    assert historical["changed_by_campaign"] is False

    assert supplementary_parent["role"] == "immutable_historical_ancestor"
    assert (
        supplementary_parent["theorem_count"],
        supplementary_parent["stable_closed_count"],
        supplementary_parent["alpha_closed_count"],
        supplementary_parent["body_checked_count"],
        supplementary_parent["pending_layered_closure_count"],
        supplementary_parent["checked_use_count"],
    ) == (1_673, 432, 484, 757, 0, 916)
    assert supplementary_parent["checked_use_promotion_count"] == 31
    assert supplementary_parent["dependency_edge_count"] == 5_615
    assert supplementary_parent["checked_dependency_edge_count"] == 2_743
    assert supplementary_parent["layer_count"] == 53
    assert supplementary_parent["identity_sha256"] == ALPHA_V17_IDENTITY
    assert supplementary_parent["evidence_root_sha256"] == ALPHA_V17_EVIDENCE_ROOT
    assert supplementary_parent["promoted_names_sha256"] == (
        SUPPLEMENT_PROMOTION_NAMES_IDENTITY
    )
    assert supplementary_parent["stable_unchanged"] is True
    assert supplementary_parent["historical_v15_unchanged"] is True
    assert supplementary_parent["historical_v16_unchanged"] is True
    assert supplementary_parent["promoted_origin"] == "quadratic_supplementary_laws_only"
    assert supplementary_parent["changed_by_campaign"] is False

    assert parent["role"] == "immutable_historical_parent"
    assert (
        parent["theorem_count"],
        parent["stable_closed_count"],
        parent["alpha_closed_count"],
        parent["body_checked_count"],
        parent["pending_layered_closure_count"],
        parent["checked_use_count"],
    ) == (1_673, 432, 1_157, 84, 0, 1_589)
    assert parent["checked_use_promotion_count"] == 673
    assert parent["dependency_edge_count"] == 5_615
    assert parent["checked_dependency_edge_count"] == 5_366
    assert parent["layer_count"] == 53
    assert parent["identity_sha256"] == ALPHA_V18_IDENTITY
    assert parent["catalog_sha256"] == ALPHA_V18_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v18.json").read_bytes()
    ).hexdigest() == ALPHA_V18_CATALOG_SHA256
    assert parent["evidence_root_sha256"] == ALPHA_V18_EVIDENCE_ROOT
    assert parent["promoted_names_sha256"] == FLAGSHIP_PROMOTION_NAMES_IDENTITY
    assert parent["stable_unchanged"] is True
    assert parent["historical_v15_unchanged"] is True
    assert parent["historical_v16_unchanged"] is True
    assert parent["historical_v17_unchanged"] is True
    assert parent["promoted_origin"] == "five_independently_checked_flagship_bundles_only"
    assert parent["changed_by_campaign"] is False

    assert current["role"] == "current_immutable_release"
    assert (
        current["theorem_count"],
        current["stable_closed_count"],
        current["alpha_closed_count"],
        current["body_checked_count"],
        current["pending_layered_closure_count"],
        current["checked_use_count"],
    ) == (1_737, 432, 1_305, 0, 0, 1_737)
    assert current["checked_use_promotion_count"] == 148
    assert current["legacy_body_promotion_count"] == 84
    assert current["new_theorem_count"] == 64
    assert current["dependency_edge_count"] == 5_779
    assert current["checked_dependency_edge_count"] == 5_779
    assert current["layer_count"] == 53
    assert current["identity_sha256"] == ALPHA_V19_IDENTITY
    assert current["catalog_sha256"] == ALPHA_V19_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v19.json").read_bytes()
    ).hexdigest() == ALPHA_V19_CATALOG_SHA256
    assert current["evidence_root_sha256"] == ALPHA_V19_EVIDENCE_ROOT
    assert current["residual_promoted_names_sha256"] == (
        RESIDUAL_PROMOTION_NAMES_IDENTITY
    )
    assert current["frontier_new_names_sha256"] == FRONTIER_NEW_NAMES_IDENTITY
    assert current["stable_unchanged"] is True
    assert current["historical_v15_unchanged"] is True
    assert current["historical_v16_unchanged"] is True
    assert current["historical_v17_unchanged"] is True
    assert current["historical_v18_unchanged"] is True
    assert current["promoted_origin"] == (
        "complete_legacy_residual_closure_and_exact_new_constructive_frontier"
    )
    assert ancestor["enrollment_sha256"] == historical["enrollment_sha256"]
    assert historical["enrollment_sha256"] == supplementary_parent["enrollment_sha256"]
    assert supplementary_parent["enrollment_sha256"] == parent["enrollment_sha256"]
    assert parent["enrollment_sha256"] == ALPHA_ENROLLMENT_IDENTITY
    assert current["parent_enrollment_sha256"] == ALPHA_ENROLLMENT_IDENTITY
    assert current["enrollment_sha256"] == ALPHA_V19_ENROLLMENT_IDENTITY
    assert current["enrollment_sha256"] != parent["enrollment_sha256"]

    assert transition["historical_v15"] == {
        "stable_closed": 241,
        "alpha_closed": 1,
        "body_checked": 314,
        "pending_layered_closure": 1,
    }
    assert transition["historical_v16"] == {
        "stable_closed": 241,
        "alpha_closed": 316,
        "body_checked": 0,
        "pending_layered_closure": 0,
    }
    assert transition["historical_v17"] == transition["historical_v16"]
    assert transition["current_v18"] == transition["historical_v16"]
    assert transition["current_v19"] == transition["historical_v16"]
    assert transition["promoted_body_checked_count"] == 314
    assert transition["promoted_pending_root_count"] == 1
    assert transition["unrelated_body_roots_promoted"] == 0
    assert transition["bundle_node_count"] == 557
    assert transition["dependency_edge_count"] == 1_787

    assert supplementary["theorem_node_count"] == 437
    assert supplementary["bundle_node_count"] == 438
    assert supplementary["dependency_edge_count"] == 1_429
    assert supplementary["body_proof_nodes"] == 33_173
    assert supplementary["bundle_bytes"] == 1_732_249
    assert supplementary["bundle_sha256"] == SUPPLEMENT_BUNDLE_IDENTITY
    assert supplementary["historical_v16"] == {
        "stable_closed": 226,
        "alpha_closed": 180,
        "body_checked": 31,
    }
    assert supplementary["historical_v17"] == {
        "stable_closed": 226,
        "alpha_closed": 211,
        "body_checked": 0,
    }
    assert supplementary["current_v18"] == supplementary["historical_v17"]
    assert supplementary["current_v19"] == supplementary["historical_v17"]
    assert supplementary["promoted_body_checked_count"] == 31
    assert supplementary["older_support_rows"] == 3
    assert supplementary["supplementary_campaign_rows"] == 28
    assert supplementary["root_names"] == [
        "quadratic_supplement_minus_one_complete",
        "quadratic_supplement_two_complete",
    ]
    assert supplementary["independent_lean_bundle_verified"] is True
    assert supplementary["unrelated_body_roots_promoted"] == 0

    assert flagship["historical_v17"] == {
        "stable_closed": 432,
        "alpha_closed": 484,
        "body_checked": 757,
        "checked_use": 916,
    }
    assert flagship["current_v18"] == {
        "stable_closed": 432,
        "alpha_closed": 1_157,
        "body_checked": 84,
        "checked_use": 1_589,
    }
    assert flagship["current_v19"] == {
        "stable_closed": 432,
        "alpha_closed": 1_305,
        "body_checked": 0,
        "checked_use": 1_737,
    }
    assert flagship["joint_dependency_theorem_count"] == 1_113
    assert flagship["promoted_body_checked_count"] == 673
    assert flagship["promoted_names_sha256"] == FLAGSHIP_PROMOTION_NAMES_IDENTITY
    assert flagship["campaign_order"] == [
        "lucas",
        "kummer",
        "bertrand",
        "four_square",
        "two_square",
    ]
    assert flagship["promotion_owner_counts"] == {
        "lucas": 74,
        "kummer": 73,
        "bertrand": 241,
        "four_square": 196,
        "two_square": 89,
    }
    assert flagship["independent_lean_bundles_verified"] is True
    assert flagship["stable_unchanged"] is True
    assert flagship["historical_v17_unchanged"] is True

    assert residual["historical_v18"] == flagship["current_v18"]
    assert residual["current_v19_legacy"] == {
        "stable_closed": 432,
        "alpha_closed": 1_241,
        "body_checked": 0,
        "checked_use": 1_673,
    }
    assert residual["promoted_body_checked_count"] == 84
    assert residual["bundle_node_count"] == 475
    assert residual["dependency_edge_count"] == 1_452
    assert residual["body_proof_nodes"] == 38_688
    assert residual["bundle_bytes"] == 4_176_537
    assert residual["bundle_sha256"] == RESIDUAL_BUNDLE_IDENTITY
    assert residual["promoted_names_sha256"] == RESIDUAL_PROMOTION_NAMES_IDENTITY
    assert residual["historical_v18_unchanged"] is True

    assert frontier["parent_v18_theorem_count"] == 1_673
    assert frontier["new_theorem_count"] == 64
    assert frontier["current_v19_theorem_count"] == 1_737
    assert frontier["campaign_order"] == [
        "pythagorean", "prime_two_square", "linear_congruence", "primes_one_mod_four"
    ]
    assert frontier["new_theorem_counts"] == {
        "pythagorean": 44,
        "prime_two_square": 1,
        "linear_congruence": 9,
        "primes_one_mod_four": 10,
    }
    assert frontier["root_names"] == [
        "pythagorean_primitive_euclidean_from_order",
        "pythagorean_primitive_normal_form",
        "prime_is_two_squares_iff_two_or_one_mod_four",
        "linear_congruence_solvable_iff_gcd_divides",
        "infinitely_many_primes_one_mod_four",
    ]
    assert frontier["new_names_sha256"] == FRONTIER_NEW_NAMES_IDENTITY
    assert frontier["theorem_node_count"] == 544
    assert frontier["bundle_node_count"] == 545
    assert frontier["synthetic_root_count"] == 1
    assert frontier["maximal_root_count"] == 17
    assert frontier["dependency_edge_count"] == 1_650
    assert frontier["body_proof_nodes"] == 34_020
    assert frontier["bundle_bytes"] == 1_617_207
    assert frontier["bundle_sha256"] == FRONTIER_BUNDLE_IDENTITY
    assert frontier["historical_v18_unchanged"] is True


def test_quadratic_reciprocity_goal_uses_current_exact_anchor_evidence() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    goal = nodes["G043"]

    assert goal["status"] == "alpha_closed"
    assert goal["evidence"] == {
        "anchor": "A01",
        "alpha_version": "v19",
        "anchor_release_status": "alpha_closed",
        "full_empty_context_closure": True,
        "independent_lean_bundle_verified": True,
        "checked_use": True,
        "stable_member": False,
        "historical_alpha_v15_release_status": "pending_layered_closure",
        "historical_alpha_v16_release_status": "alpha_closed",
        "historical_alpha_v17_release_status": "alpha_closed",
    }


@pytest.mark.parametrize(
    ("identifier", "anchor", "name", "campaign_label"),
    (
        ("G033", "A07", "lucas_theorem", "lucas"),
        ("G034", "A04", "kummer_binomial_carry_bit_count", "kummer"),
        (
            "G062",
            "A05",
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
            "two_square",
        ),
        ("G064", "A06", "four_square_lagrange", "four_square"),
    ),
)
def test_exact_new_flagship_milestones_bind_actual_checked_roots(
    identifier: str,
    anchor: str,
    name: str,
    campaign_label: str,
) -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    goal = nodes[identifier]
    proof = goal["evidence"]
    theorem = alpha_catalog("v19")[name]

    assert goal["status"] == "alpha_closed"
    assert proof["anchor"] == anchor
    assert proof["alpha_version"] == "v19"
    assert proof["theorem_name"] == name
    assert proof["anchor_release_status"] == "alpha_closed"
    assert proof["bundle_campaign"] == campaign_label
    assert proof["checked_use"] is theorem["checked_use"] is True
    assert proof["stable_member"] is False
    assert proof["historical_alpha_v17_release_status"] == "body_checked"
    assert theorem["evidence_status"] == "alpha_closed"
    assert alpha_catalog("v17")[name]["checked_use"] is False


def test_supplementary_goal_uses_exact_new_checked_anchor_evidence() -> None:
    payload = campaign()
    nodes = {node["id"]: node for node in payload["nodes"]}
    goal = nodes["G044"]
    anchor = nodes["A03"]
    catalog = alpha_catalog("v19")

    assert goal["status"] == anchor["status"] == "alpha_closed"
    assert goal["evidence"] == {
        "anchor": "A03",
        "alpha_version": "v19",
        "anchor_release_status": "alpha_closed",
        "theorem_names": [
            "quadratic_supplement_minus_one_complete",
            "quadratic_supplement_two_complete",
        ],
        "full_empty_context_closure": True,
        "independent_lean_bundle_verified": True,
        "checked_use": True,
        "stable_member": False,
        "promoted_dependency_count": 31,
        "bundle_sha256": SUPPLEMENT_BUNDLE_IDENTITY,
        "historical_alpha_v16_release_status": "body_checked",
        "historical_alpha_v17_release_status": "alpha_closed",
    }
    assert goal["evidence"]["theorem_names"] == anchor["evidence"]["theorem_names"]
    for name in goal["evidence"]["theorem_names"]:
        assert catalog[name]["evidence_status"] == "alpha_closed"
        assert catalog[name]["checked_use"] is True
        assert alpha_catalog("v16")[name]["evidence_status"] == "body_checked"
        assert alpha_catalog("v16")[name]["checked_use"] is False


def test_versioned_campaign_sources_distinguish_current_and_historical_channels() -> None:
    sources = {source["id"]: source for source in campaign()["sources"]}

    assert sources["S01"]["path"] == "artifacts/peano-library/channels-v15.json"
    assert "v15" in sources["S01"]["label"]
    assert sources["S09"]["path"] == "artifacts/peano-library/channels-v16.json"
    assert "v16" in sources["S09"]["label"]
    assert "historical" in sources["S09"]["label"].lower()
    assert sources["S10"]["path"] == "artifacts/peano-library/channels-v17.json"
    assert "v17" in sources["S10"]["label"]
    assert "historical" in sources["S10"]["label"].lower()
    assert sources["S14"]["path"] == "artifacts/peano-library/channels-v19.json"
    assert "v19" in sources["S14"]["label"]
    assert "current" in sources["S14"]["label"].lower()
    assert sources["S26"]["path"] == "artifacts/peano-library/channels-v18.json"
    assert "v18" in sources["S26"]["label"]
    assert "historical" in sources["S26"]["label"].lower()
    assert sources["S11"]["path"] == (
        "research/arithmetic-library/supplementary-laws-closure-receipt.md"
    )
    assert sources["S12"]["path"] == (
        "research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json"
    )
    assert sources["S13"]["path"] == (
        "research/arithmetic-library/alpha-v17-supplementary-laws-promotion-rfc-v1.md"
    )
    assert sources["S15"]["path"] == (
        "research/arithmetic-library/alpha-v18-flagship-promotion-rfc-v1.md"
    )
    assert sources["S27"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json"
    )
    assert sources["S28"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json"
    )
    assert sources["S29"]["path"] == (
        "research/arithmetic-library/alpha-v19-constructive-campaign-rfc-v1.md"
    )
    for identifier, expected_size, expected_digest in (
        ("S27", 4_176_537, RESIDUAL_BUNDLE_IDENTITY),
        ("S28", 1_617_207, FRONTIER_BUNDLE_IDENTITY),
    ):
        artifact = REPO / sources[identifier]["path"]
        assert artifact.stat().st_size == expected_size
        assert sha256(artifact.read_bytes()).hexdigest() == expected_digest
    assert (REPO / sources["S29"]["path"]).is_file()
    for receipt, bundle, stem in (
        ("S16", "S17", "lucas"),
        ("S18", "S19", "kummer"),
        ("S20", "S21", "bertrand"),
        ("S22", "S23", "four-square"),
        ("S24", "S25", "two-square"),
    ):
        assert sources[receipt]["path"] == (
            f"research/arithmetic-library/{stem}-complete-closure-receipt.md"
        )
        assert sources[bundle]["path"] == (
            f"research/arithmetic-library/artifacts/{stem}-proof-bundle-v1.json"
        )
        assert (REPO / sources[receipt]["path"]).is_file()
        assert (REPO / sources[bundle]["path"]).is_file()
    assert {"S01", "S09", "S10", "S14"} <= set(
        next(node for node in campaign()["nodes"] if node["id"] == "A01")[
            "references"
        ]
    )
    assert {"S09", "S10", "S11", "S12", "S14"} <= set(
        next(node for node in campaign()["nodes"] if node["id"] == "A03")[
            "references"
        ]
    )


def test_campaign_release_evidence_matches_all_five_immutable_channel_artifacts() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    versions = {
        version: json.loads(
            (REPO / "artifacts" / "peano-library" / f"channels-{version}.json").read_text(
                encoding="utf-8"
            )
        )
        for version in ("v15", "v16", "v17", "v18", "v19")
    }
    historical_channels = versions["v15"]

    for version, channels in versions.items():
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

    assert versions["v16"]["parent_channels_v15"]["path"] == (
        "artifacts/peano-library/channels-v15.json"
    )
    assert versions["v17"]["parent_channels_v16"]["path"] == (
        "artifacts/peano-library/channels-v16.json"
    )
    assert versions["v18"]["parent_channels_v17"]["path"] == (
        "artifacts/peano-library/channels-v17.json"
    )
    assert versions["v19"]["parent_channels_v18"]["path"] == (
        "artifacts/peano-library/channels-v18.json"
    )
    alpha_v19 = versions["v19"]["channels"]["alpha"]
    assert alpha_v19["alpha_v19_residual_promoted_count"] == 84
    assert alpha_v19["alpha_v19_frontier_new_count"] == 64
    assert alpha_v19["frontier_v19_campaign_counts"] == {
        "linear_congruence": 9,
        "prime_two_square": 1,
        "primes_one_mod_four": 10,
        "pythagorean": 44,
    }


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
        "Alpha v19", "1,737", "1,305", "5,779", "148", "64", "97", "23",
        "475", "1,452", "38,688", "545", "1,650", "34,020",
        "Alpha v18", "1,157", "84", "1,589", "673", "1,113", "544", "1,917",
        "201,285", "45,254", "31,694",
        "Alpha v17", "1,673", "484", "757", "916", "31", "438", "1,429",
        "Alpha v16", "453", "788", "885", "315",
        "Alpha v15", "138", "1,102", "570",
        "pending_layered_closure", "body_checked",
    ):
        assert value in document
    assert ALPHA_V16_IDENTITY in document
    assert ALPHA_V17_IDENTITY in document
    assert ALPHA_V18_IDENTITY in document
    assert ALPHA_V19_IDENTITY in document
    assert ALPHA_V18_CATALOG_SHA256 in document
    assert ALPHA_V19_CATALOG_SHA256 in document
    assert ALPHA_V16_EVIDENCE_ROOT in document
    assert ALPHA_V17_EVIDENCE_ROOT in document
    assert ALPHA_V18_EVIDENCE_ROOT in document
    assert ALPHA_V19_EVIDENCE_ROOT in document
    assert FLAGSHIP_PROMOTION_NAMES_IDENTITY in document
    assert RESIDUAL_PROMOTION_NAMES_IDENTITY in document
    assert FRONTIER_NEW_NAMES_IDENTITY in document
    assert ALPHA_ENROLLMENT_IDENTITY in document
    assert ALPHA_V19_ENROLLMENT_IDENTITY in document
    assert SUPPLEMENT_BUNDLE_IDENTITY in document
    assert RESIDUAL_BUNDLE_IDENTITY in document
    assert FRONTIER_BUNDLE_IDENTITY in document


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


ATLAS_DOMAIN_FAMILIES = {
    "D01": ("F01", "F02", "F04"),
    "D02": ("F03", "F05", "F09"),
    "D03": ("F06", "F07", "F08"),
    "D04": ("F10", "F11"),
    "D05": ("F12",),
}

EXPECTED_CROSS_DOMAIN_PROOF_EDGES = {
    ("D01", "D02"): 27,
    ("D01", "D03"): 15,
    ("D01", "D04"): 19,
    ("D01", "D05"): 4,
    ("D02", "D03"): 9,
    ("D02", "D04"): 3,
    ("D03", "D02"): 1,
    ("D03", "D04"): 3,
    ("D03", "D05"): 2,
    ("D04", "D01"): 4,
    ("D04", "D02"): 4,
    ("D04", "D03"): 6,
    ("D04", "D05"): 6,
    ("D05", "D02"): 2,
    ("D05", "D03"): 3,
    ("D05", "D04"): 2,
}


def test_multiscale_domains_partition_all_families_and_count_real_proof_edges() -> None:
    payload = campaign()
    family_domains = {
        family: domain
        for domain, families in ATLAS_DOMAIN_FAMILIES.items()
        for family in families
    }
    assert set(family_domains) == set(EXPECTED_FAMILIES)

    def domain(node: dict) -> str:
        if node.get("family"):
            return family_domains[node["family"]]
        return {"T12": "D04", "T13": "D05"}.get(node["id"], "D01")

    nodes = {node["id"]: node for node in payload["nodes"]}
    actual = Counter(
        (domain(nodes[dependency]), domain(node))
        for node in nodes.values()
        for dependency in node["deps"]
        if domain(nodes[dependency]) != domain(node)
    )
    assert dict(actual) == EXPECTED_CROSS_DOMAIN_PROOF_EDGES
    assert sum(actual.values()) == 110
    assert len(actual) == 16

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert 'var ATLAS_DOMAINS = [' in explorer
    for identifier in ATLAS_DOMAIN_FAMILIES:
        assert f'id: "{identifier}"' in explorer
    assert '"data-dependency-weight": edge.count' in explorer
    assert "underlying 144-node proof graph is acyclic" in explorer


def test_blueprint_definition_dag_is_separate_acyclic_and_lexically_exact() -> None:
    payload = campaign()
    definitions = payload["definitions"]
    assert len(definitions) == 107

    def references(source: str, *, exclude: str | None = None) -> set[str]:
        return {
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", source)
            if token in definitions and token != exclude
        }

    notation_edges = {
        name: references(definition["expansion"], exclude=name)
        for name, definition in definitions.items()
    }
    statement_edges = {
        node["id"]: references(node["statement"])
        for node in payload["nodes"]
    }
    assert sum(map(len, notation_edges.values())) == 32
    assert sum(map(len, statement_edges.values())) == 312
    assert notation_edges["PowerValuation"] == {"Val"}
    assert notation_edges["Val"] == {"Prime", "Dvd"}
    assert notation_edges["Prime"] == {"Dvd"}
    assert {"Prime", "Rep2"} <= statement_edges["G061"]

    pending = {name: set(dependencies) for name, dependencies in notation_edges.items()}
    ordered = []
    while pending:
        ready = sorted(name for name, dependencies in pending.items() if not dependencies)
        assert ready, f"Cyclic blueprint notation: {pending}"
        for name in ready:
            ordered.append(name)
            del pending[name]
        for dependencies in pending.values():
            dependencies.difference_update(ready)
    assert len(ordered) == 107

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert "Blueprint vocabulary only" in explorer
    assert "Lexical notation links are not proof premises" in explorer
    assert "Lexical notation prerequisites — not proof premises" in explorer
    assert "compiled conservative kernel definition" in explorer
    assert "state.definitionDependencies" in explorer
    assert "state.definitionUsers" in explorer


def test_ready_frontier_never_treats_unverified_foundations_as_checked() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    checked = {"available", "stable_closed", "alpha_closed"}
    frontier = {"open", "existing_anchor_extension", "existing_anchor_closure"}
    ready = {
        node["id"]
        for node in nodes.values()
        if node["status"] in frontier
        and all(nodes[dependency]["status"] in checked for dependency in node["deps"])
    }
    assert ready == {"T12", "T13", "G023", "G024", "G035", "G071", "G101", "G102"}
    assert nodes["G002"]["status"] == "existing_foundation"
    assert nodes["G025"]["status"] == "open"
    assert nodes["G077"]["status"] == "existing_anchor_extension"
    assert nodes["G077"]["evidence"]["inverse_direction_already_proved"] is False

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert "Ready to investigate — not proved" in explorer
    assert "existing unverified foundations" in explorer.lower()
    assert "Existing anchor only — this extension remains unproved" in explorer


def test_checked_definition_cross_links_resolve_to_actual_explorer_pages() -> None:
    expected = {
        "Coprime": ("quadratic-reciprocity", "PD0005"),
        "DivRem": ("quadratic-reciprocity", "PD0007"),
        "Dvd": ("quadratic-reciprocity", "PD0003"),
        "FactorialValuation": ("bertrand-postulate", "PD0048"),
        "Le": ("quadratic-reciprocity", "PD0001"),
        "LegendreSum": ("bertrand-postulate", "PD0050"),
        "Lt": ("quadratic-reciprocity", "PD0002"),
        "Pow": ("quadratic-reciprocity", "PD0020"),
        "PowerValuation": ("bertrand-postulate", "PD0046"),
        "Prime": ("quadratic-reciprocity", "PD0004"),
        "Sum": ("quadratic-reciprocity", "PD0015"),
    }
    explorer = EXPLORER.read_text(encoding="utf-8")
    for name, (route, identifier) in expected.items():
        assert f'{name}: {{ id: "{identifier}", route: "{route}" }}' in explorer
        root = "pa-proof-explorer" if route == "quadratic-reciprocity" else "bertrand-proof-explorer"
        assert (REPO / "book" / "_static" / root / "defined" / "definition" / f"{identifier}.html").is_file()
    assert len(expected) == 11


@pytest.mark.parametrize(
    ("location", "initial_family", "expected_qr_prefix"),
    (
        (
            "file:///proofs/grand-campaign/index.html?view=family&focus=F05&v=atlas-test",
            "F05",
            "../quadratic-reciprocity/explorer/defined/",
        ),
        (
            "file:///book/_static/constructive-grand-campaign/index.html?view=goal&focus=A02",
            "F03",
            "../pa-proof-explorer/defined/",
        ),
    ),
)
def test_multiscale_atlas_navigates_real_browser_interactions(
    location: str,
    initial_family: str,
    expected_qr_prefix: str,
) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed on this workstation")

    harness = (
        f"const campaignPath = {json.dumps(str(CAMPAIGN))};\n"
        f"const explorerPath = {json.dumps(str(EXPLORER))};\n"
        f"const initialLocation = {json.dumps(location)};\n"
        + r"""
const fs = require("fs");
const payload = fs.readFileSync(campaignPath, "utf8");
const source = fs.readFileSync(explorerPath, "utf8");
const executable = source.match(/<script>\s*([\s\S]*?)\s*<\/script>/)[1];
const allElements = [];

class Element {
  constructor(name) {
    this.name = name;
    this.attributes = {};
    this.children = [];
    this.listeners = {};
    this.style = {};
    this.hidden = false;
    this.textContent = "";
    this.value = "";
    this.scrollLeft = 0;
    this.scrollTop = 0;
    this.clientWidth = 1200;
    this.clientHeight = 760;
    this.classList = {add() {}, remove() {}, contains() { return false; }};
    allElements.push(this);
  }
  get firstChild() { return this.children[0] || null; }
  get childNodes() { return this.children; }
  get options() { return this.children; }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  getAttribute(key) { return this.attributes[key] || null; }
  removeAttribute(key) { delete this.attributes[key]; }
  appendChild(child) { child.parentElement = this; this.children.push(child); return child; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); return child; }
  remove(index) { this.children.splice(index, 1); }
  addEventListener(event, callback) { (this.listeners[event] ||= []).push(callback); }
  scrollIntoView() {}
  click() { for (const callback of this.listeners.click || []) callback({preventDefault() {}}); }
}

const selectors = new Map();
function item(selector) {
  if (!selectors.has(selector)) {
    const name = selector.includes("controls") ? "form" : selector.includes("graph") ? "svg" : "div";
    const value = new Element(name);
    if (["[data-family]", "[data-layer]", "[data-evidence-filter]", "[data-definition-domain]", "[data-definition-trust]"].includes(selector)) {
      value.value = "all";
      value.appendChild(new Element("option"));
    }
    if (selector === "[data-edges]") value.value = "focused";
    selectors.set(selector, value);
  }
  return selectors.get(selector);
}

const atlasModes = ["overview", "frontier", "definitions"].map(mode => {
  const button = new Element("button");
  button.setAttribute("data-atlas-view", mode);
  return button;
});

global.document = {
  title: "",
  createElement(name) { return new Element(name); },
  createElementNS(_namespace, name) { return new Element(name); },
  createTextNode(value) { return {textContent: String(value)}; },
  getElementById(identifier) { return identifier === "campaign-data" ? {textContent: payload} : null; },
  querySelector(selector) { return item(selector); },
  querySelectorAll(selector) {
    if (selector === "[data-atlas-view]") return atlasModes;
    if (selector === "[data-family-id]") return allElements.filter(entry => entry.attributes["data-family-id"]);
    return [];
  }
};

const locationState = new URL(initialLocation);
global.window = {
  location: locationState,
  listeners: {},
  addEventListener(name, callback) { this.listeners[name] = callback; }
};
global.history = {
  pushState(_state, _title, target) {
    const next = new URL(target, locationState);
    locationState.pathname = next.pathname;
    locationState.search = next.search;
    locationState.hash = next.hash;
  },
  replaceState(_state, _title, target) { this.pushState(_state, _title, target); }
};

new Function(executable)();

function descendants(parent, predicate) {
  const result = [];
  for (const child of parent.children || []) {
    if (predicate(child)) result.push(child);
    result.push(...descendants(child, predicate));
  }
  return result;
}
function atlasButton(parentSelector, attribute, value) {
  const match = descendants(item(parentSelector), child => child.attributes && child.attributes[attribute] === value)[0];
  if (!match) throw new Error("Missing " + attribute + "=" + value + " in " + parentSelector);
  return match;
}

const initialFamily = item("[data-family]").value;
const overviewDomainCount = item("[data-domain-grid]").children.length;
const domainGraphWeights = descendants(item("[data-domain-graph]"), child => child.attributes && child.attributes["data-dependency-weight"])
  .map(child => ({source: child.attributes["data-domain-source"], target: child.attributes["data-domain-target"], count: Number(child.attributes["data-dependency-weight"])}));

atlasButton("[data-domain-grid]", "data-domain-id", "D02").click();
const domainGoalCount = item("[data-scope-goals]").children.length;
atlasButton("[data-scope-families]", "data-family-id", "F05").click();
const familyGoalCount = item("[data-scope-goals]").children.length;
atlasButton("[data-scope-goals]", "data-atlas-node", "G043").click();
const selectedGoal = item("[data-node-id]").textContent;
const goalProofLinks = item("[data-node-proof-links]").children.map(child => child.attributes.href);
const goalUrl = locationState.toString();

const prime = descendants(item("[data-node-notation]"), child => child.textContent === "Prime")[0];
if (prime) prime.click();
else atlasButton("[data-definition-grid]", "data-definition-name", "Prime").click();
const primeDetail = item("[data-definition-detail]").children.map(child => child.textContent);
const primeLinks = descendants(item("[data-definition-detail]"), child => child.name === "a").map(child => child.attributes.href);
const definitionUrl = locationState.toString();

item("[data-atlas-back]").click();
const afterBack = item("[data-node-id]").textContent;
atlasModes.find(button => button.attributes["data-atlas-view"] === "frontier").click();
const frontierCards = item("[data-frontier-grid]").children
  .filter(child => child.attributes && child.attributes["data-atlas-node"])
  .map(child => child.attributes["data-atlas-node"]);
const frontierCount = item("[data-frontier-count]").textContent;
const notationCount = item("[data-definition-count]").textContent;
const qrNavigation = item("[data-proof-quadratic]").attributes.href;

process.stdout.write(JSON.stringify({
  initialFamily, overviewDomainCount, domainGraphWeights, domainGoalCount, familyGoalCount,
  selectedGoal, goalProofLinks, goalUrl, primeDetail, primeLinks, definitionUrl,
  afterBack, frontierCards, frontierCount, notationCount, qrNavigation
}));
"""
    )
    result = subprocess.run(
        [node, "-e", harness],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)

    assert actual["initialFamily"] == initial_family
    assert actual["overviewDomainCount"] == 5
    assert actual["domainGoalCount"] == 30
    assert actual["familyGoalCount"] == 10
    assert actual["selectedGoal"].startswith("G043")
    assert actual["afterBack"].startswith("G043")
    assert "view=goal" in actual["goalUrl"] and "focus=G043" in actual["goalUrl"]
    assert "view=definition" in actual["definitionUrl"] and "focus=Prime" in actual["definitionUrl"]
    assert any("Prime(p)" in value for value in actual["primeDetail"])
    assert actual["primeLinks"] == [expected_qr_prefix + "definition/PD0004.html"]
    assert actual["qrNavigation"] == expected_qr_prefix + "index.html"
    assert any(link.startswith(expected_qr_prefix) for link in actual["goalProofLinks"])
    assert {"T12", "T13", "G023", "G024", "G035", "G071", "G101", "G102"} <= set(actual["frontierCards"])
    assert actual["frontierCount"].startswith("8 ready")
    assert "107 blueprint terms" in actual["notationCount"]
    assert "32 lexical expansion edges" in actual["notationCount"]
    assert "312 lexical statement-use edges" in actual["notationCount"]
    assert "11 checked-registry matches" in actual["notationCount"]

    weights = {
        (edge["source"], edge["target"]): edge["count"]
        for edge in actual["domainGraphWeights"]
    }
    assert weights == EXPECTED_CROSS_DOMAIN_PROOF_EDGES


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
    assert "conceptual_refs" in executable[0]
    assert "Unimplemented constructive substrate" in executable[0]


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


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "same-layer",
        "duplicate",
        "conceptual-missing",
        "conceptual-duplicate",
        "conceptual-proof-overlap",
    ],
)
def test_invalid_dependency_graph_mutations_fail_closed(mutation: str) -> None:
    nodes = [
        dict(
            node,
            deps=list(node["deps"]),
            **(
                {"conceptual_refs": list(node["conceptual_refs"])}
                if "conceptual_refs" in node
                else {}
            ),
        )
        for node in campaign()["nodes"]
    ]
    if mutation.startswith("conceptual-"):
        target = next(node for node in nodes if node.get("conceptual_refs"))
    else:
        target = next(node for node in nodes if node["kind"] == "goal" and node["deps"])
    by_id = {node["id"]: node for node in nodes}

    if mutation == "missing":
        target["deps"][0] = "MISSING"
    elif mutation == "same-layer":
        by_id[target["deps"][0]]["layer"] = target["layer"]
    elif mutation == "duplicate":
        target["deps"].append(target["deps"][0])
    elif mutation == "conceptual-missing":
        target["conceptual_refs"][0] = "MISSING"
    elif mutation == "conceptual-duplicate":
        target["conceptual_refs"].append(target["conceptual_refs"][0])
    else:
        target["conceptual_refs"][0] = target["deps"][0]

    with pytest.raises(ValueError):
        dependency_order(nodes)
