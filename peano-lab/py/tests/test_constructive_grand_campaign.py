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
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
CAMPAIGN = REPO / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
EXPLORER = CAMPAIGN.parent / "index.html"
BLUEPRINT = REPO / "PLAN" / "14_constructive_number_theory_grand_campaign.md"
ARITHMETIC_INDEX = REPO / "research" / "arithmetic-library" / "README.md"
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

EXPECTED_FAMILIES = tuple(f"F{index:02d}" for index in range(1, 13))
EXPECTED_TOOLS = {f"T{index:02d}" for index in range(1, 17)}
EXPECTED_ANCHORS = {f"A{index:02d}" for index in range(1, 9)}
EXPECTED_GOALS = {f"G{index:03d}" for index in range(1, 121)}
ALPHA_V15_IDENTITY = "2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66"
ALPHA_V16_IDENTITY = "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10"
ALPHA_V17_IDENTITY = "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4"
ALPHA_V18_IDENTITY = "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
ALPHA_V19_IDENTITY = "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7"
ALPHA_V20_IDENTITY = "ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b"
ALPHA_V21_IDENTITY = "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6"
ALPHA_V22_IDENTITY = "2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db"
ALPHA_V23_IDENTITY = "02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85"
ALPHA_V24_IDENTITY = "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
ALPHA_V25_IDENTITY = "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
ALPHA_V26_IDENTITY = "8573945e4bdfe0a8d9414b499828ced67eff3b886e5adde50a0fcff81cfbdc19"
ALPHA_V18_CATALOG_SHA256 = "cfbaeaf5d89be609d09aa2b84c9d102297a45b7b6aeeea6efcd32b1b328e62b2"
ALPHA_V19_CATALOG_SHA256 = "f1c3d3fba013ca3a5b62a4103dd00bd5b7e39b1f785ed9023099704ad033004b"
ALPHA_V20_CATALOG_SHA256 = "8f86225cc560d7b59ff665e58594ac6249c12dbb5cdfe47ae2708a0e497c86ce"
ALPHA_V21_CATALOG_SHA256 = "84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1"
ALPHA_V22_CATALOG_SHA256 = "fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22"
ALPHA_V23_CATALOG_SHA256 = "818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2"
ALPHA_V24_CATALOG_SHA256 = "94ac4d193cbfe8c2ec04e54024221bc2c3a534c0ae014d381663b86174b3dcc1"
ALPHA_V25_CATALOG_SHA256 = "75fa146ac19bf6aa5f799265b6fc031b725c1e1b2e044854da91b31898d5876e"
ALPHA_V26_CATALOG_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
ALPHA_ENROLLMENT_IDENTITY = "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
ALPHA_V19_ENROLLMENT_IDENTITY = "1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795"
ALPHA_V20_ENROLLMENT_IDENTITY = "947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c"
ALPHA_V21_ENROLLMENT_IDENTITY = "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98"
ALPHA_V22_ENROLLMENT_IDENTITY = "431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea"
ALPHA_V23_ENROLLMENT_IDENTITY = "f5d94af7a11c642d7076a195e2e795e7b84c61a6de1a6b074708669b2dac1648"
ALPHA_V24_ENROLLMENT_IDENTITY = "7463b938ffb87fe85eea6cd0e40c10ac73c799087ca1c408a070fcbe2687d4e1"
ALPHA_V25_ENROLLMENT_IDENTITY = "f724872707cdcf401f35cb69680e1bbec86d626c4bf56e6d41f01a3724e2be81"
ALPHA_V26_ENROLLMENT_IDENTITY = "cdf2cd0adfef8f1becd6f1f62d4d1d5d7a1891838e16b52a4d1cdaca98c496f2"
FIRST_WAVE_NEW_NAMES_IDENTITY = "226cc91137521e0484dc6c3dcf90d2138e67acc79bf53798d84fb0deaf5973de"
FIRST_WAVE_BUNDLE_IDENTITY = "59afca707b33b68df907c941683e335492f7de12ee3888219339c5dfce8ec4fc"
QR_PROMOTION_NAMES_IDENTITY = "aba2d7a192b6f1c11fbafbed1001bf592ca9ed8f5bee7ac3f1de863dd870a80e"
SUPPLEMENT_PROMOTION_NAMES_IDENTITY = "21e141da58e3262e250285ef9d43d78a5911d065e3746a824faea82642f7c8c7"
FLAGSHIP_PROMOTION_NAMES_IDENTITY = "5b6faad95b90a3b3f11e6aea929aefd3cdbf9b5a1f3563e57d8e48f15e9d59e6"
RESIDUAL_PROMOTION_NAMES_IDENTITY = "0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e"
FRONTIER_NEW_NAMES_IDENTITY = "07b9c92ab3ef80dc609681a9b588d21b0faeb69e87448c1420b78272a54aaed1"
NEXT_LAYER_NEW_NAMES_IDENTITY = "6a9564cc3e55245161d7c13b81e25005e287232dd44deb303133e3a8e3ae2eba"
ADVANCED_LAYER_NEW_NAMES_IDENTITY = "cbf76fb45efbae79a2b1cd2c7fc3cf806a6f8ebc593a5fceee6f5bea7cd734f5"
TRANSPORT_LAYER_NEW_NAMES_IDENTITY = "c2d9a2840111e6b79a8716eb1a9a0c02345a771bcf60d42c96e6a7c3283e6713"
MILESTONE_CLOSURE_NEW_NAMES_IDENTITY = "7d24a436a735a83e20faf2a1378193560f9ea4fb4ae5c7f03e5fc812b39d69db"
RESEARCH_LAYER_NEW_NAMES_IDENTITY = "e88ec1f9a1242c339565305bd7a866a0ec1e95a069f537af1712abf364433947"
SUPPLEMENT_BUNDLE_IDENTITY = "79fc4717dbe570bf836cca5ec699492ff3995700ec25336a20d03cc57261054c"
RESIDUAL_BUNDLE_IDENTITY = "e69112c5e3b8c21bc452ad35838474f2af2e297152ff73fbdc62bfd935ffdebb"
FRONTIER_BUNDLE_IDENTITY = "cf7947a944d54e9eb956fb153702b29c953100ece6cf05743162759b0fba9b17"
NEXT_LAYER_BUNDLE_IDENTITY = "1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069"
ADVANCED_LAYER_BUNDLE_IDENTITY = "65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0"
TRANSPORT_LAYER_BUNDLE_IDENTITY = "95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938"
MILESTONE_CLOSURE_BUNDLE_IDENTITY = "cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11"
RESEARCH_LAYER_BUNDLE_IDENTITY = "627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9"
BREAKTHROUGH_LAYER_BUNDLE_IDENTITY = (
    "d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a"
)
ALPHA_V15_EVIDENCE_ROOT = "4d6cba8b48666d8d3cbea7acd2aa937e418a5bfa2e45bc6ebf5b53affd9a921e"
ALPHA_V16_EVIDENCE_ROOT = "142d73d908bd86f52af9b6a1d39a5e11679d1db4f463d3e6f17d5c483f283ee4"
ALPHA_V17_EVIDENCE_ROOT = "e631e3a9bfc680c3b84630db71903f817cb740c2cc830958b5dc7bcedaed19a1"
ALPHA_V18_EVIDENCE_ROOT = "def31d268c4fef3a3e598fa2447b9be92e9c54aae7ec9f227e6948c752ecb6f9"
ALPHA_V19_EVIDENCE_ROOT = "627f651198360aa95b8efd085b98f694d88c883434309f6050a819bc249c90c4"
ALPHA_V20_EVIDENCE_ROOT = "fd76c648de26cd8a451244441fac8f423fb4fec8e7feac1c789404dafcda1563"
ALPHA_V21_EVIDENCE_ROOT = "9d217af3e7f77f8beb436f627a44f1a29cda54bb08a4e666899803aa97ccb91b"
ALPHA_V22_EVIDENCE_ROOT = "897ac1893550881538cf74274d0d48e15450125776f31be4edc10de0b1d05ef6"
ALPHA_V23_EVIDENCE_ROOT = "e9c00544bdad559342da3ed5a0d1e26ef1576a0eecd9f580ec1fc98a2eb941cf"
ALPHA_V24_EVIDENCE_ROOT = "2516501a609a5bd46114a53e20bbdd7c9f79bc801f7d3148be38dcd48f4ce3e0"
ALPHA_V25_EVIDENCE_ROOT = "193ee636570fa9f7b69344dbebc6c7e53de8bebda01bcb86687f01a50ec19674"
ALPHA_V26_EVIDENCE_ROOT = "fa9773708ab4eacfc981707e2cecb615dd46714df7c242008a5946821b8e4c52"
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
    assert sum(len(node["deps"]) for node in payload["nodes"]) == 309


def test_goal_status_and_layer_census_remain_honest_and_exact() -> None:
    payload = campaign()
    goals = [node for node in payload["nodes"] if node["kind"] == "goal"]
    statuses = Counter(node["status"] for node in goals)
    assert statuses == Counter(
        {
            "open": 83,
            "stable_closed": 1,
            "alpha_closed": 36,
        }
    )

    layer_vertices = Counter(node["layer"] for node in payload["nodes"])
    assert [layer_vertices[level] for level in range(13)] == [
        3, 4, 5, 8, 8, 12, 12, 17, 21, 16, 18, 11, 9
    ]
    layer_goals = Counter(node["layer"] for node in goals)
    assert [layer_goals[level] for level in range(13)] == [
        0, 0, 1, 4, 6, 8, 10, 16, 21, 16, 18, 11, 9
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
        # The immutable v20 parent prefix preserves v19 evidence verbatim.
        assert evidence["alpha_version"] == "v19"
        assert theorem == alpha_catalog("v19")[theorem_name]
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
    evidence = finite["historical_partial_evidence"]

    assert finite["status"] == "alpha_closed"
    assert finite["evidence"]["full_generalized_crt_proved"] is True
    assert finite["evidence"]["zero_moduli_and_empty_list_included"] is True
    assert "non-coprime" in evidence["available_scope"]
    assert "predecessor-LCM merge compatibility" in evidence["available_scope"]
    assert "zero-inclusive" in evidence["available_scope"]
    assert "non-coprime" in evidence["target_scope"]
    assert evidence["alpha_version"] == "v25"
    assert evidence["finite_list_constructor_proved"] is True
    assert evidence["pairwise_coprime_finite_list_constructor_proved"] is True
    assert evidence["arbitrary_modulus_list_lcm_exists_unique_proved"] is True
    assert evidence["merge_compatible_non_coprime_fold_proved"] is True
    assert evidence["zero_inclusive_merge_compatible_fold_proved"] is True
    assert evidence["pairwise_compatible_dominating_last_canonical_proved"] is True
    assert evidence["arbitrary_pairwise_compatibility_implies_merge_compatibility_proved"] is False
    assert evidence["general_compatible_non_coprime_fold_proved"] is False
    assert evidence["full_generalized_crt_proved"] is False
    assert evidence["checked_use"] is False
    assert evidence["partial_release_status"] == "alpha_closed"
    assert evidence["partial_checked_use"] is True
    assert evidence["partial_component_checked_use"] is True
    assert evidence["bundle_sha256"] == BREAKTHROUGH_LAYER_BUNDLE_IDENTITY
    assert evidence["bundle_node_id"] == 288
    for name in evidence["partial_theorem_names"]:
        expected = (
            "stable_closed"
            if name in {"binary_crt", "generalized_binary_crt_solvable_iff"}
            else "alpha_closed"
        )
        assert catalog[name]["evidence_status"] == expected
        assert catalog[name]["checked_use"] is True


def test_polynomial_and_matrix_tools_preserve_honest_evidence_boundaries() -> None:
    nodes = {node["id"]: node for node in campaign()["nodes"]}
    catalog = alpha_catalog("v20")
    polynomial = nodes["T12"]
    horner = polynomial["evidence"]

    assert polynomial["kind"] == "tool"
    assert polynomial["status"] == horner["release_status"] == "alpha_closed"
    assert polynomial["statement"] == "∀b c x ell. ∃z. Horner(b,c,x,ell,z)."
    assert polynomial["definition_refs"] == ["Horner", "Beta"]
    assert horner["alpha_version"] == "v20"
    assert horner["theorem_name"] == "beta_horner_eval_exists"
    assert horner["new_theorem_count"] == 7
    assert horner["alpha_enrolled"] is True
    assert horner["checked_use"] is True
    assert horner["stable_member"] is False
    assert horner["arbitrary_presented_ring_totality_claimed"] is False
    assert horner["formal_differentiation_claimed"] is False
    assert catalog[horner["theorem_name"]]["statement_sha256"] == (
        horner["theorem_statement_sha256"]
    )

    matrix = nodes["T13"]
    partial = matrix["historical_partial_evidence"]
    assert matrix["kind"] == "tool"
    assert matrix["status"] == "alpha_closed"
    assert matrix["evidence"]["full_arbitrary_determinant_proved"] is True
    assert matrix["evidence"]["full_rank_substrate_proved"] is True
    assert matrix["evidence"]["lattice_index_formula_proved"] is False
    assert set(campaign()["definitions"]) >= {
        "MatrixAt", "DotProduct", "SignedDet2", "MatrixAffineSlice",
        "MatrixProductCell", "MatrixProductPrefix", "MatrixPointwiseAdd",
        "SignedDotProduct", "SignedMatrixProduct", "MatrixSkipIndex",
        "MatrixMinorCell", "MatrixMinorPrefix", "SignedMatrixMinor",
        "MatrixMinorFourCode", "SignedMinorRecord", "SignedCofactorMinorPrefix",
        "SignedAlternatingCofactorTerm", "SignedAlternatingProductPrefix",
        "SignedAlternatingCofactorFold", "SignedFirstRowCofactorFold",
        "BetaSum", "Even", "Odd",
    }
    assert {"SignedRecursiveDeterminant", "RectangularMatrixRank", "IntegerColumnSpan",
            "PositiveDeterminantMatrixData"} <= set(matrix["definition_refs"])
    assert partial["implementation"] == "independently_closed_partial"
    assert partial["alpha_version"] == "v25"
    assert partial["alpha_enrolled"] is True
    assert partial["checked_use"] is False
    assert partial["partial_component_checked_use"] is True
    assert partial["stable_member"] is False
    assert partial["partial_checked_theorem_count"] == 79
    assert partial["new_checked_theorem_count"] == 29
    assert partial["partial_theorem_name"] == "signed_matrix_cofactor_family_and_fold_exists"
    assert partial["full_arbitrary_signed_matrix_proved"] is True
    assert partial["full_arbitrary_signed_matrix_product_proved"] is True
    assert partial["full_arbitrary_signed_minor_proved"] is True
    assert partial["signed_four_by_four_determinant_proved"] is True
    assert partial["complete_first_row_signed_minor_family_proved"] is True
    assert partial["arbitrary_signed_alternating_cofactor_fold_proved"] is True
    assert partial["full_arbitrary_determinant_proved"] is False
    assert partial["full_lattice_substrate_proved"] is False
    current_catalog = alpha_catalog("v25")
    assert current_catalog[partial["partial_theorem_name"]]["checked_use"] is True
    assert current_catalog[partial["partial_theorem_name"]]["statement_sha256"] == (
        partial["partial_theorem_statement_sha256"]
    )
    assert partial["bundle_sha256"] == BREAKTHROUGH_LAYER_BUNDLE_IDENTITY

    hensel = nodes["G095"]
    foundation = hensel["historical_partial_evidence"]
    assert hensel["status"] == "alpha_closed"
    assert hensel["evidence"]["full_simple_root_hensel_lift_proved"] is True
    assert hensel["evidence"]["arbitrary_prime_power_iteration_proved"] is True
    assert foundation["alpha_version"] == "v25"
    assert foundation["partial_theorem_name"] == "beta_horner_hensel_lift_exists"
    assert foundation["formal_derivative_exists_unique_proved"] is True
    assert foundation["taylor_divisibility_proved"] is True
    assert foundation["modular_inverse_root_correction_proved"] is True
    assert foundation["one_step_hensel_lift_proved"] is True
    assert foundation["full_simple_root_hensel_lift_proved"] is False
    assert foundation["checked_use"] is False
    assert foundation["partial_component_checked_use"] is True
    assert foundation["bundle_sha256"] == BREAKTHROUGH_LAYER_BUNDLE_IDENTITY

    assert "T12" in nodes["G095"]["deps"]
    assert "T13" not in nodes["A06"]["deps"]
    assert "T13" not in nodes["A08"]["deps"]


@pytest.mark.parametrize(
    ("identifier", "theorem_name", "statement_digest", "count", "node_id"),
    (
        (
            "T12",
            "beta_horner_eval_exists",
            "bd1fa1601bd14a7dd6e769eb49bb646326d12f9a26d206c89eea1c7de54ac7d3",
            7,
            551,
        ),
        (
            "G023",
            "central_binom_prime_divisor_multiplicity_one_exists",
            "d0899600b713e85d0cb20997ada171ce02b6a6e8316364ed4ab603389724f5a8",
            7,
            573,
        ),
        (
            "G024",
            "iterated_bertrand_prime_chain_exists",
            "02c52d46368ec2320c8d316b41d37ef7c1dbb5de32dbd15247325a17382650d2",
            6,
            579,
        ),
        (
            "G071",
            "continued_fraction_positive_exists",
            "d3b12766820bb64d9b1437e0ef96a9068c84d6d3176e066fe70f5a4f2d9e087d",
            9,
            588,
        ),
    ),
)
def test_v20_checked_milestones_bind_exact_original_kernel_bundle_nodes(
    identifier: str,
    theorem_name: str,
    statement_digest: str,
    count: int,
    node_id: int,
) -> None:
    node = next(item for item in campaign()["nodes"] if item["id"] == identifier)
    evidence = node["evidence"]
    theorem = alpha_catalog("v20")[theorem_name]
    closure = theorem["empty_context_closure"]

    assert theorem_name not in alpha_catalog("v19")
    assert node["status"] == theorem["evidence_status"] == "alpha_closed"
    assert evidence["alpha_version"] == "v20"
    assert evidence["theorem_name"] == theorem_name
    assert evidence["theorem_statement_sha256"] == (
        theorem["statement_sha256"]
    ) == statement_digest
    assert evidence["release_status"] == "alpha_closed"
    assert evidence["alpha_enrolled"] is True
    assert evidence["checked_use"] is theorem["checked_use"] is True
    assert evidence["stable_member"] is False
    assert evidence["full_empty_context_closure"] is True
    assert evidence["new_theorem_count"] == count
    assert evidence["bundle_node_id"] == closure["bundle_node_id"] == node_id
    assert evidence["bundle_nodes"] == closure["bundle_node_count"] == 590
    assert evidence["bundle_dependencies"] == (
        closure["bundle_dependency_edge_count"]
    ) == 2_045
    assert evidence["bundle_sha256"] == (
        closure["certificate_sha256"]
    ) == NEXT_LAYER_BUNDLE_IDENTITY
    assert closure["bundle_campaign"] == "next_layer"
    assert set(node["references"]) == {"S30", "S31", "S32", "S33"}


@pytest.mark.parametrize(
    (
        "identifier",
        "theorem_name",
        "statement_digest",
        "count",
        "dependency_count",
        "body_nodes",
        "node_id",
        "route",
        "tag",
    ),
    (
        (
            "G101",
            "euclidean_gcd_execution_logarithmic_bound",
            "decf1f8be3a9dcaf2e8bdf7bebd59e46d08e9f91fee375ca325c6b53847c8d6e",
            17,
            48,
            719,
            572,
            "euclidean-logarithmic-bound",
            "EL0010",
        ),
        (
            "G102",
            "binary_modular_execution_logarithmic_bound",
            "3ac6949afecc26acc6e5fb9d8d9041be9a9f2b8120dcbc918b8e771a7a1bd27d",
            24,
            63,
            1_229,
            597,
            "binary-digit-extraction",
            "BD0018",
        ),
        (
            "G025",
            "infinitely_many_primes_three_mod_four",
            "3ddac628b2e37925ee3d7a4bd56319de5e173e9065cce6437cab775cc646620b",
            18,
            46,
            803,
            615,
            "primes-three-mod-four",
            "TF0012",
        ),
    ),
)
def test_v23_completed_milestones_bind_exact_original_kernel_objects_and_atlas_roots(
    identifier: str,
    theorem_name: str,
    statement_digest: str,
    count: int,
    dependency_count: int,
    body_nodes: int,
    node_id: int,
    route: str,
    tag: str,
) -> None:
    node = next(item for item in campaign()["nodes"] if item["id"] == identifier)
    evidence = node["evidence"]
    theorem = alpha_catalog("v23")[theorem_name]
    closure = theorem["empty_context_closure"]

    assert theorem_name not in alpha_catalog("v22")
    assert node["status"] == theorem["evidence_status"] == "alpha_closed"
    assert evidence["implementation"] == "independently_closed"
    assert evidence["alpha_version"] == "v23"
    assert evidence["theorem_name"] == theorem_name
    assert evidence["theorem_statement_sha256"] == (
        theorem["statement_sha256"]
    ) == closure["node_statement_sha256"] == statement_digest
    assert evidence["release_status"] == "alpha_closed"
    assert evidence["alpha_enrolled"] is True
    assert evidence["checked_use"] is theorem["checked_use"] is True
    assert evidence["stable_member"] is False
    assert evidence["full_empty_context_closure"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert evidence["new_theorem_count"] == count
    assert evidence["dependency_edge_count"] == dependency_count
    assert evidence["body_proof_nodes"] == body_nodes
    assert evidence["bundle_node_id"] == closure["bundle_node_id"] == node_id
    assert evidence["bundle_nodes"] == closure["bundle_node_count"] == 617
    assert evidence["bundle_dependencies"] == (
        closure["bundle_dependency_edge_count"]
    ) == 1_871
    assert evidence["bundle_sha256"] == (
        closure["certificate_sha256"]
    ) == MILESTONE_CLOSURE_BUNDLE_IDENTITY
    assert closure["bundle_campaign"] == "milestone_closure"
    assert closure["bundle_root_id"] == 616
    assert closure["kernel_mode"] == "intuitionistic"
    assert closure["closure_kind"] == "dependency_closed_bundle_node"
    assert closure["status"] == "checked"
    assert {"S42", "S43", "S44", "S45"} <= set(node["references"])

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert re.search(
        rf'{identifier}: \{{ route: "{re.escape(route)}", '
        rf'label: "[^"]+", tag: "{tag}" \}}',
        explorer,
    )
    family = (
        REPO / "book" / "_static" / "constructive-milestone-closure-explorer" / route
    )
    assert (family / "index.html").is_file()
    assert (family / "explorer" / "defined" / "tag" / f"{tag}.html").is_file()
    corpus = json.loads((family / "api" / "corpus.json").read_text(encoding="utf-8"))
    assert corpus["campaign_goal_id"] == identifier
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    assert theorem_name in corpus["root_names"]
    assert corpus["node_count"] == count
    # These immutable readers were already refreshed to v30. Their first
    # admission is still v23; the older v28 planning atlas is not their
    # current-edition catalog authority.
    assert corpus["alpha_edition_version"] == "v30"
    assert corpus["alpha_first_enrolled_version"] == "v23"
    catalog_digest = sha256()
    with (REPO / "artifacts/peano-library/alpha/catalog-v30.json").open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            catalog_digest.update(chunk)
    assert corpus["alpha_catalog_sha256"] == catalog_digest.hexdigest() == (
        "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
    )
    assert corpus["alpha_edition_identity_sha256"] == (
        "8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9"
    )
    current_theorem = alpha_catalog("v30")[theorem_name]
    assert current_theorem["statement_sha256"] == statement_digest
    assert current_theorem["empty_context_closure"]["certificate_sha256"] == MILESTONE_CLOSURE_BUNDLE_IDENTITY
    assert corpus["alpha_proof_bundle_sha256"] == MILESTONE_CLOSURE_BUNDLE_IDENTITY


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
    assert nodes["G025"]["status"] == "alpha_closed"
    assert nodes["G025"]["evidence"]["one_mod_four_infinitude_required"] is False


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


def test_current_v28_release_preserves_v15_through_v27_evidence_and_stable() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    ancestor = boundaries["alpha_v15_edition"]
    historical = boundaries["alpha_v16_edition"]
    supplementary_parent = boundaries["alpha_v17_edition"]
    parent = boundaries["alpha_v18_edition"]
    current = boundaries["alpha_v19_edition"]
    latest = boundaries["alpha_v20_edition"]
    advanced = boundaries["alpha_v21_edition"]
    transport = boundaries["alpha_v22_edition"]
    milestone = boundaries["alpha_v23_edition"]
    research = boundaries["alpha_v24_edition"]
    breakthrough = boundaries["alpha_v25_edition"]
    completed = boundaries["alpha_v26_edition"]
    transition = boundaries["quadratic_reciprocity_evidence_transition"]
    supplementary = boundaries["supplementary_laws_evidence_transition"]
    flagship = boundaries["flagship_evidence_transition"]
    residual = boundaries["residual_evidence_transition"]
    frontier = boundaries["frontier_evidence_transition"]
    next_layer = boundaries["next_layer_evidence_transition"]
    advanced_layer = boundaries["advanced_layer_evidence_transition"]
    transport_layer = boundaries["transport_layer_evidence_transition"]
    milestone_layer = boundaries["milestone_closure_evidence_transition"]
    research_layer = boundaries["research_layer_evidence_transition"]
    breakthrough_layer = boundaries["breakthrough_layer_evidence_transition"]
    first_wave = boundaries["first_wave_evidence_transition"]

    assert payload["meta"]["current_alpha_version"] == "v28"
    assert payload["meta"]["historical_alpha_versions"] == [
        "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24", "v25", "v26", "v27"
    ]
    assert payload["meta"]["current_alpha_checked_use_count"] == 2_764
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

    assert parent["role"] == "immutable_historical_ancestor"
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

    assert current["role"] == "immutable_historical_ancestor"
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
    assert current["changed_by_campaign"] is False
    assert ancestor["enrollment_sha256"] == historical["enrollment_sha256"]
    assert historical["enrollment_sha256"] == supplementary_parent["enrollment_sha256"]
    assert supplementary_parent["enrollment_sha256"] == parent["enrollment_sha256"]
    assert parent["enrollment_sha256"] == ALPHA_ENROLLMENT_IDENTITY
    assert current["parent_enrollment_sha256"] == ALPHA_ENROLLMENT_IDENTITY
    assert current["enrollment_sha256"] == ALPHA_V19_ENROLLMENT_IDENTITY
    assert current["enrollment_sha256"] != parent["enrollment_sha256"]

    assert latest["role"] == "immutable_historical_parent"
    assert (
        latest["theorem_count"],
        latest["stable_closed_count"],
        latest["alpha_closed_count"],
        latest["body_checked_count"],
        latest["pending_layered_closure_count"],
        latest["checked_use_count"],
    ) == (1_776, 432, 1_344, 0, 0, 1_776)
    assert latest["checked_use_promotion_count"] == 39
    assert latest["new_theorem_count"] == 39
    assert latest["dependency_edge_count"] == 5_882
    assert latest["checked_dependency_edge_count"] == 5_882
    assert latest["layer_count"] == 53
    assert latest["identity_sha256"] == ALPHA_V20_IDENTITY
    assert latest["catalog_sha256"] == ALPHA_V20_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v20.json").read_bytes()
    ).hexdigest() == ALPHA_V20_CATALOG_SHA256
    assert latest["evidence_root_sha256"] == ALPHA_V20_EVIDENCE_ROOT
    assert latest["frontier_new_names_sha256"] == NEXT_LAYER_NEW_NAMES_IDENTITY
    assert latest["parent_enrollment_sha256"] == ALPHA_V19_ENROLLMENT_IDENTITY
    assert latest["enrollment_sha256"] == ALPHA_V20_ENROLLMENT_IDENTITY
    assert latest["enrollment_sha256"] != current["enrollment_sha256"]
    assert latest["stable_unchanged"] is True
    assert latest["historical_v15_unchanged"] is True
    assert latest["historical_v16_unchanged"] is True
    assert latest["historical_v17_unchanged"] is True
    assert latest["historical_v18_unchanged"] is True
    assert latest["historical_v19_unchanged"] is True
    assert latest["promoted_origin"] == (
        "independently_checked_four_campaign_next_constructive_layer"
    )

    assert advanced["role"] == "immutable_historical_parent"
    assert (
        advanced["theorem_count"],
        advanced["stable_closed_count"],
        advanced["alpha_closed_count"],
        advanced["body_checked_count"],
        advanced["pending_layered_closure_count"],
        advanced["checked_use_count"],
    ) == (1_830, 432, 1_398, 0, 0, 1_830)
    assert advanced["checked_use_promotion_count"] == 54
    assert advanced["new_theorem_count"] == 54
    assert advanced["dependency_edge_count"] == 5_986
    assert advanced["checked_dependency_edge_count"] == 5_986
    assert advanced["layer_count"] == 53
    assert advanced["identity_sha256"] == ALPHA_V21_IDENTITY
    assert advanced["catalog_sha256"] == ALPHA_V21_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v21.json").read_bytes()
    ).hexdigest() == ALPHA_V21_CATALOG_SHA256
    assert advanced["evidence_root_sha256"] == ALPHA_V21_EVIDENCE_ROOT
    assert advanced["frontier_new_names_sha256"] == ADVANCED_LAYER_NEW_NAMES_IDENTITY
    assert advanced["parent_enrollment_sha256"] == ALPHA_V20_ENROLLMENT_IDENTITY
    assert advanced["enrollment_sha256"] == ALPHA_V21_ENROLLMENT_IDENTITY
    assert advanced["enrollment_sha256"] != latest["enrollment_sha256"]
    assert advanced["stable_unchanged"] is True
    assert all(advanced[f"historical_v{version}_unchanged"] for version in range(15, 21))
    assert advanced["independent_lean_bundle_verified"] is True
    assert advanced["promoted_origin"] == (
        "independently_kernel_and_lean_checked_three_campaign_advanced_constructive_layer"
    )

    assert transport["role"] == "immutable_historical_parent"
    assert (
        transport["theorem_count"],
        transport["stable_closed_count"],
        transport["alpha_closed_count"],
        transport["body_checked_count"],
        transport["pending_layered_closure_count"],
        transport["checked_use_count"],
    ) == (1_890, 432, 1_458, 0, 0, 1_890)
    assert transport["checked_use_promotion_count"] == 60
    assert transport["new_theorem_count"] == 60
    assert transport["dependency_edge_count"] == 6_128
    assert transport["checked_dependency_edge_count"] == 6_128
    assert transport["layer_count"] == 53
    assert transport["identity_sha256"] == ALPHA_V22_IDENTITY
    assert transport["catalog_sha256"] == ALPHA_V22_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v22.json").read_bytes()
    ).hexdigest() == ALPHA_V22_CATALOG_SHA256
    assert transport["evidence_root_sha256"] == ALPHA_V22_EVIDENCE_ROOT
    assert transport["frontier_new_names_sha256"] == TRANSPORT_LAYER_NEW_NAMES_IDENTITY
    assert transport["parent_enrollment_sha256"] == ALPHA_V21_ENROLLMENT_IDENTITY
    assert transport["enrollment_sha256"] == ALPHA_V22_ENROLLMENT_IDENTITY
    assert transport["enrollment_sha256"] != advanced["enrollment_sha256"]
    assert transport["stable_unchanged"] is True
    assert all(transport[f"historical_v{version}_unchanged"] for version in range(15, 22))
    assert transport["independent_lean_bundle_verified"] is True
    assert transport["promoted_origin"] == (
        "independently_kernel_and_lean_checked_binary_length_euclidean_gcd_and_binary_execution_transport"
    )

    assert milestone["role"] == "immutable_historical_ancestor"
    assert (
        milestone["theorem_count"],
        milestone["stable_closed_count"],
        milestone["alpha_closed_count"],
        milestone["body_checked_count"],
        milestone["pending_layered_closure_count"],
        milestone["checked_use_count"],
    ) == (1_949, 432, 1_517, 0, 0, 1_949)
    assert milestone["checked_use_promotion_count"] == 59
    assert milestone["new_theorem_count"] == 59
    assert milestone["dependency_edge_count"] == 6_285
    assert milestone["checked_dependency_edge_count"] == 6_285
    assert milestone["layer_count"] == 53
    assert milestone["identity_sha256"] == ALPHA_V23_IDENTITY
    assert milestone["catalog_sha256"] == ALPHA_V23_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v23.json").read_bytes()
    ).hexdigest() == ALPHA_V23_CATALOG_SHA256
    assert milestone["evidence_root_sha256"] == ALPHA_V23_EVIDENCE_ROOT
    assert milestone["frontier_new_names_sha256"] == MILESTONE_CLOSURE_NEW_NAMES_IDENTITY
    assert milestone["parent_enrollment_sha256"] == ALPHA_V22_ENROLLMENT_IDENTITY
    assert milestone["enrollment_sha256"] == ALPHA_V23_ENROLLMENT_IDENTITY
    assert milestone["enrollment_sha256"] != transport["enrollment_sha256"]
    assert milestone["stable_unchanged"] is True
    assert all(milestone[f"historical_v{version}_unchanged"] for version in range(15, 23))
    assert milestone["independent_lean_bundle_verified"] is True
    assert milestone["promoted_origin"] == (
        "independently_kernel_and_lean_checked_full_euclidean_logarithmic_"
        "binary_execution_and_three_mod_four_prime_milestones"
    )

    assert research["role"] == "immutable_historical_ancestor"
    assert (
        research["theorem_count"],
        research["stable_closed_count"],
        research["alpha_closed_count"],
        research["body_checked_count"],
        research["pending_layered_closure_count"],
        research["checked_use_count"],
    ) == (2_008, 432, 1_576, 0, 0, 2_008)
    assert research["checked_use_promotion_count"] == 59
    assert research["new_theorem_count"] == 59
    assert research["dependency_edge_count"] == 6_423
    assert research["checked_dependency_edge_count"] == 6_423
    assert research["layer_count"] == 53
    assert research["identity_sha256"] == ALPHA_V24_IDENTITY
    assert research["catalog_sha256"] == ALPHA_V24_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v24.json").read_bytes()
    ).hexdigest() == ALPHA_V24_CATALOG_SHA256
    assert research["evidence_root_sha256"] == ALPHA_V24_EVIDENCE_ROOT
    assert research["frontier_new_names_sha256"] == RESEARCH_LAYER_NEW_NAMES_IDENTITY
    assert research["parent_enrollment_sha256"] == ALPHA_V23_ENROLLMENT_IDENTITY
    assert research["enrollment_sha256"] == ALPHA_V24_ENROLLMENT_IDENTITY
    assert research["stable_unchanged"] is True
    assert all(research[f"historical_v{version}_unchanged"] for version in range(15, 24))
    assert research["independent_lean_bundle_verified"] is True
    assert research["promoted_origin"] == (
        "independently_kernel_and_lean_checked_arbitrary_matrix_minors_"
        "formal_polynomial_derivatives_and_finite_coprime_crt"
    )

    assert breakthrough["role"] == "immutable_historical_parent"
    assert (
        breakthrough["theorem_count"],
        breakthrough["stable_closed_count"],
        breakthrough["alpha_closed_count"],
        breakthrough["body_checked_count"],
        breakthrough["pending_layered_closure_count"],
        breakthrough["checked_use_count"],
    ) == (2_080, 432, 1_648, 0, 0, 2_080)
    assert breakthrough["checked_use_promotion_count"] == 72
    assert breakthrough["new_theorem_count"] == 72
    assert breakthrough["dependency_edge_count"] == 6_633
    assert breakthrough["checked_dependency_edge_count"] == 6_633
    assert breakthrough["layer_count"] == 53
    assert breakthrough["identity_sha256"] == ALPHA_V25_IDENTITY
    assert breakthrough["catalog_sha256"] == ALPHA_V25_CATALOG_SHA256
    assert sha256(
        (REPO / "artifacts/peano-library/alpha/catalog-v25.json").read_bytes()
    ).hexdigest() == ALPHA_V25_CATALOG_SHA256
    assert breakthrough["evidence_root_sha256"] == ALPHA_V25_EVIDENCE_ROOT
    assert breakthrough["frontier_new_names_sha256"] == (
        "28e37959781f86e7dc22e242963a9e7a4d834110d18e80f0c2a691547833c265"
    )
    assert breakthrough["parent_enrollment_sha256"] == ALPHA_V24_ENROLLMENT_IDENTITY
    assert breakthrough["enrollment_sha256"] == ALPHA_V25_ENROLLMENT_IDENTITY
    assert breakthrough["stable_unchanged"] is True
    assert all(breakthrough[f"historical_v{version}_unchanged"] for version in range(15, 25))
    assert breakthrough["independent_lean_bundle_verified"] is True

    assert completed["role"] == "historical_immutable_release"
    assert (
        completed["theorem_count"], completed["stable_closed_count"],
        completed["alpha_closed_count"], completed["body_checked_count"],
        completed["pending_layered_closure_count"], completed["checked_use_count"],
    ) == (2_138, 432, 1_706, 0, 0, 2_138)
    assert completed["checked_use_promotion_count"] == completed["new_theorem_count"] == 58
    assert completed["dependency_edge_count"] == completed["checked_dependency_edge_count"] == 6_851
    assert completed["layer_count"] == 53
    assert completed["identity_sha256"] == ALPHA_V26_IDENTITY
    assert completed["catalog_sha256"] == ALPHA_V26_CATALOG_SHA256
    assert sha256((REPO / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()).hexdigest() == ALPHA_V26_CATALOG_SHA256
    assert completed["evidence_root_sha256"] == ALPHA_V26_EVIDENCE_ROOT
    assert completed["frontier_new_names_sha256"] == FIRST_WAVE_NEW_NAMES_IDENTITY
    assert completed["parent_enrollment_sha256"] == ALPHA_V25_ENROLLMENT_IDENTITY
    assert completed["enrollment_sha256"] == ALPHA_V26_ENROLLMENT_IDENTITY
    assert completed["stable_unchanged"] is True
    assert all(completed[f"historical_v{version}_unchanged"] for version in range(15, 26))
    assert completed["independent_lean_bundle_verified"] is True

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

    assert next_layer["parent_v19_theorem_count"] == 1_737
    assert next_layer["new_theorem_count"] == 39
    assert next_layer["current_v20_theorem_count"] == 1_776
    assert next_layer["campaign_order"] == [
        "polynomial_horner",
        "matrix_dot_product",
        "bertrand_prime",
        "continued_fraction",
    ]
    assert next_layer["new_theorem_counts"] == {
        "polynomial_horner": 7,
        "matrix_dot_product": 10,
        "bertrand_prime": 13,
        "continued_fraction": 9,
    }
    assert {
        "beta_horner_eval_exists_unique",
        "beta_dot_product_exists_unique",
        "central_binom_prime_divisor_multiplicity_one_exists",
        "iterated_bertrand_prime_chain_exists",
        "continued_fraction_positive_exists",
    } <= set(next_layer["root_names"])
    assert next_layer["new_names_sha256"] == NEXT_LAYER_NEW_NAMES_IDENTITY
    assert next_layer["theorem_node_count"] == 589
    assert next_layer["bundle_node_count"] == 590
    assert next_layer["synthetic_root_count"] == 1
    assert next_layer["maximal_root_count"] == 12
    assert next_layer["dependency_edge_count"] == 2_045
    assert next_layer["body_proof_nodes"] == 190_533
    assert next_layer["bundle_bytes"] == 14_775_673
    assert next_layer["bundle_sha256"] == NEXT_LAYER_BUNDLE_IDENTITY
    assert next_layer["original_kernel_call_count"] == 590
    assert next_layer["stable_unchanged"] is True
    assert next_layer["historical_v19_unchanged"] is True

    assert advanced_layer["parent_v20_theorem_count"] == 1_776
    assert advanced_layer["new_theorem_count"] == 54
    assert advanced_layer["current_v21_theorem_count"] == 1_830
    assert advanced_layer["campaign_order"] == [
        "matrix_coded_product", "euclidean_complexity", "binary_modular_exponentiation"
    ]
    assert advanced_layer["new_theorem_counts"] == {
        "matrix_coded_product": 23,
        "euclidean_complexity": 15,
        "binary_modular_exponentiation": 16,
    }
    assert {
        "beta_signed_matrix_product_exists",
        "euclidean_two_step_halving",
        "euclidean_gcd_execution_linear_bound",
        "binary_modular_exponentiation_result_exists_unique",
    } <= set(advanced_layer["root_names"])
    assert advanced_layer["new_names_sha256"] == ADVANCED_LAYER_NEW_NAMES_IDENTITY
    assert advanced_layer["theorem_node_count"] == 208
    assert advanced_layer["bundle_node_count"] == 209
    assert advanced_layer["synthetic_root_count"] == 1
    assert advanced_layer["maximal_root_count"] == 27
    assert advanced_layer["dependency_edge_count"] == 491
    assert advanced_layer["body_proof_nodes"] == 10_304
    assert advanced_layer["bundle_bytes"] == 1_005_317
    assert advanced_layer["bundle_sha256"] == ADVANCED_LAYER_BUNDLE_IDENTITY
    assert advanced_layer["original_kernel_call_count"] == 209
    assert advanced_layer["independent_lean_bundle_verified"] is True
    assert advanced_layer["stable_unchanged"] is True
    assert advanced_layer["historical_v20_unchanged"] is True

    assert transport_layer["parent_v21_theorem_count"] == 1_830
    assert transport_layer["new_theorem_count"] == 60
    assert transport_layer["current_v22_theorem_count"] == 1_890
    assert transport_layer["campaign_order"] == [
        "binary_length", "euclidean_gcd_transport", "binary_modular_execution"
    ]
    assert transport_layer["new_theorem_counts"] == {
        "binary_length": 21,
        "euclidean_gcd_transport": 20,
        "binary_modular_execution": 19,
    }
    assert {
        "binary_length_exists_unique",
        "euclidean_anchored_execution_linear_bound",
        "binary_modular_execution_result_exists_unique",
    } <= set(transport_layer["root_names"])
    assert transport_layer["new_names_sha256"] == TRANSPORT_LAYER_NEW_NAMES_IDENTITY
    assert transport_layer["theorem_node_count"] == 239
    assert transport_layer["bundle_node_count"] == 240
    assert transport_layer["synthetic_root_count"] == 1
    assert transport_layer["maximal_root_count"] == 17
    assert transport_layer["dependency_edge_count"] == 597
    assert transport_layer["body_proof_nodes"] == 11_848
    assert transport_layer["bundle_bytes"] == 1_099_541
    assert transport_layer["bundle_sha256"] == TRANSPORT_LAYER_BUNDLE_IDENTITY
    assert transport_layer["original_kernel_call_count"] == 240
    assert transport_layer["independent_lean_bundle_verified"] is True
    assert transport_layer["stable_unchanged"] is True
    assert transport_layer["historical_v21_unchanged"] is True

    assert milestone_layer["parent_v22_theorem_count"] == 1_890
    assert milestone_layer["new_theorem_count"] == 59
    assert milestone_layer["current_v23_theorem_count"] == 1_949
    assert milestone_layer["campaign_order"] == [
        "euclidean_logarithmic_bound",
        "binary_digit_extraction",
        "primes_three_mod_four",
    ]
    assert milestone_layer["new_theorem_counts"] == {
        "euclidean_logarithmic_bound": 17,
        "binary_digit_extraction": 24,
        "primes_three_mod_four": 18,
    }
    assert milestone_layer["root_names"] == [
        "euclidean_gcd_execution_logarithmic_exists",
        "binary_digit_prefix_recode",
        "binary_exponent_digit_prefix_value_functional",
        "binary_canonical_exponent_length_functional",
        "binary_digit_operation_count_functional",
        "binary_modular_exponent_coded_execution_exists_unique",
        "binary_modular_execution_logarithmic_bound",
        "three_mod_four_progression_nonunit",
        "infinitely_many_primes_three_mod_four",
    ]
    assert milestone_layer["new_names_sha256"] == MILESTONE_CLOSURE_NEW_NAMES_IDENTITY
    assert milestone_layer["theorem_node_count"] == 616
    assert milestone_layer["bundle_node_count"] == 617
    assert milestone_layer["synthetic_root_count"] == 1
    assert milestone_layer["maximal_root_count"] == 9
    assert milestone_layer["dependency_edge_count"] == 1_871
    assert milestone_layer["body_proof_nodes"] == 39_161
    assert milestone_layer["bundle_bytes"] == 2_518_315
    assert milestone_layer["bundle_sha256"] == MILESTONE_CLOSURE_BUNDLE_IDENTITY
    assert milestone_layer["original_kernel_call_count"] == 617
    assert milestone_layer["independent_lean_bundle_verified"] is True
    assert milestone_layer["stable_unchanged"] is True
    assert milestone_layer["historical_v22_unchanged"] is True

    assert research_layer["parent_v23_theorem_count"] == 1_949
    assert research_layer["new_theorem_count"] == 59
    assert research_layer["current_v24_theorem_count"] == 2_008
    assert research_layer["campaign_order"] == [
        "matrix_determinant_minors", "polynomial_hensel", "generalized_crt_fold"
    ]
    assert research_layer["new_theorem_counts"] == {
        "matrix_determinant_minors": 17,
        "polynomial_hensel": 15,
        "generalized_crt_fold": 27,
    }
    assert research_layer["new_names_sha256"] == RESEARCH_LAYER_NEW_NAMES_IDENTITY
    assert research_layer["theorem_node_count"] == 202
    assert research_layer["bundle_node_count"] == 203
    assert research_layer["synthetic_root_count"] == 1
    assert research_layer["maximal_root_count"] == 18
    assert research_layer["theorem_dependency_edge_count"] == 484
    assert research_layer["dependency_edge_count"] == 502
    assert research_layer["body_proof_nodes"] == 11_065
    assert research_layer["bundle_bytes"] == 738_923
    assert research_layer["bundle_sha256"] == RESEARCH_LAYER_BUNDLE_IDENTITY
    assert research_layer["original_kernel_call_count"] == 203
    assert research_layer["independent_lean_bundle_verified"] is True
    assert research_layer["stable_unchanged"] is True
    assert research_layer["historical_v23_unchanged"] is True
    assert research_layer["full_matrix_lattice_milestone_closed"] is False
    assert research_layer["full_simple_hensel_milestone_closed"] is False
    assert research_layer["full_non_coprime_crt_milestone_closed"] is False

    assert breakthrough_layer["parent_v24_theorem_count"] == 2_008
    assert breakthrough_layer["new_theorem_count"] == 72
    assert breakthrough_layer["current_v25_theorem_count"] == 2_080
    assert breakthrough_layer["campaign_order"] == [
        "matrix_cofactor_expansion",
        "polynomial_taylor_hensel",
        "generalized_crt_compatibility",
    ]
    assert breakthrough_layer["new_theorem_counts"] == {
        "matrix_cofactor_expansion": 29,
        "polynomial_taylor_hensel": 19,
        "generalized_crt_compatibility": 24,
    }
    assert breakthrough_layer["theorem_node_count"] == 301
    assert breakthrough_layer["bundle_node_count"] == 302
    assert breakthrough_layer["synthetic_root_count"] == 1
    assert breakthrough_layer["maximal_root_count"] == 29
    assert breakthrough_layer["theorem_dependency_edge_count"] == 791
    assert breakthrough_layer["dependency_edge_count"] == 820
    assert breakthrough_layer["body_proof_nodes"] == 16_947
    assert breakthrough_layer["bundle_bytes"] == 1_041_166
    assert breakthrough_layer["bundle_sha256"] == BREAKTHROUGH_LAYER_BUNDLE_IDENTITY
    assert breakthrough_layer["original_kernel_call_count"] == 302
    assert breakthrough_layer["independent_lean_bundle_verified"] is True
    assert breakthrough_layer["stable_unchanged"] is True
    assert breakthrough_layer["historical_v24_unchanged"] is True
    assert breakthrough_layer["full_matrix_lattice_milestone_closed"] is False
    assert breakthrough_layer["full_simple_hensel_milestone_closed"] is False
    assert breakthrough_layer["full_non_coprime_crt_milestone_closed"] is False

    assert first_wave["parent_v25_theorem_count"] == 2_080
    assert first_wave["new_theorem_count"] == 58
    assert first_wave["current_v26_theorem_count"] == 2_138
    assert first_wave["campaign_order"] == ["coprime_square_factor", "pythagorean_inverse", "fermat_four_descent"]
    assert first_wave["new_theorem_counts"] == {"coprime_square_factor": 9, "pythagorean_inverse": 23, "fermat_four_descent": 26}
    assert first_wave["theorem_node_count"] == 215
    assert first_wave["bundle_node_count"] == 216
    assert first_wave["synthetic_root_count"] == 1
    assert first_wave["maximal_root_count"] == 4
    assert first_wave["theorem_dependency_edge_count"] == 554
    assert first_wave["dependency_edge_count"] == 558
    assert first_wave["body_proof_nodes"] == 10_397
    assert first_wave["bundle_bytes"] == 364_186
    assert first_wave["bundle_sha256"] == FIRST_WAVE_BUNDLE_IDENTITY
    assert first_wave["original_kernel_call_count"] == 216
    assert first_wave["independent_lean_bundle_verified"] is True
    assert first_wave["stable_unchanged"] is True
    assert first_wave["historical_v25_unchanged"] is True


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
    assert "historical" in sources["S14"]["label"].lower()
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
    assert sources["S30"]["path"] == "artifacts/peano-library/channels-v20.json"
    assert "v20" in sources["S30"]["label"]
    assert "historical" in sources["S30"]["label"].lower()
    assert sources["S31"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json"
    )
    assert sources["S32"]["path"] == (
        "research/arithmetic-library/alpha-v20-next-layer-closure-receipt.md"
    )
    assert sources["S33"]["path"] == (
        "research/arithmetic-library/alpha-v20-next-layer-rfc-v1.md"
    )
    assert sources["S34"]["path"] == "artifacts/peano-library/channels-v21.json"
    assert "historical" in sources["S34"]["label"].lower()
    assert sources["S35"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json"
    )
    assert sources["S36"]["path"] == (
        "research/arithmetic-library/alpha-v21-advanced-layer-closure-receipt.md"
    )
    assert sources["S37"]["path"] == (
        "research/arithmetic-library/alpha-v21-advanced-layer-rfc-v1.md"
    )
    assert sources["S38"]["path"] == "artifacts/peano-library/channels-v22.json"
    assert "historical" in sources["S38"]["label"].lower()
    assert sources["S39"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json"
    )
    assert sources["S40"]["path"] == (
        "research/arithmetic-library/alpha-v22-transport-layer-closure-receipt.md"
    )
    assert sources["S41"]["path"] == (
        "research/arithmetic-library/alpha-v22-transport-layer-rfc-v1.md"
    )
    assert sources["S42"]["path"] == "artifacts/peano-library/channels-v23.json"
    assert "historical" in sources["S42"]["label"].lower()
    assert sources["S43"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json"
    )
    assert sources["S44"]["path"] == (
        "research/arithmetic-library/alpha-v23-milestone-closure-receipt.md"
    )
    assert sources["S45"]["path"] == (
        "research/arithmetic-library/alpha-v23-milestone-closure-rfc-v1.md"
    )
    assert sources["S46"]["path"] == "artifacts/peano-library/channels-v24.json"
    assert "historical" in sources["S46"]["label"].lower()
    assert sources["S47"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json"
    )
    assert sources["S48"]["path"] == (
        "research/arithmetic-library/alpha-v24-research-layer-receipt.md"
    )
    assert sources["S49"]["path"] == (
        "research/arithmetic-library/alpha-v24-research-layer-rfc-v1.md"
    )
    assert sources["S50"]["path"] == "artifacts/peano-library/channels-v25.json"
    assert "historical" in sources["S50"]["label"].lower()
    assert sources["S51"]["path"] == (
        "research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json"
    )
    assert sources["S52"]["path"] == (
        "research/arithmetic-library/alpha-v25-breakthrough-layer-receipt.md"
    )
    assert sources["S53"]["path"] == (
        "research/arithmetic-library/alpha-v25-breakthrough-layer-rfc-v1.md"
    )
    assert sources["S54"]["path"] == "artifacts/peano-library/channels-v26.json"
    assert "historical" in sources["S54"]["label"].lower()
    assert sources["S55"]["path"] == "research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json"
    assert sources["S56"]["path"] == "research/arithmetic-library/alpha-v26-first-wave-receipt.md"
    assert sources["S57"]["path"] == "research/arithmetic-library/alpha-v26-first-wave-rfc-v1.md"
    assert sources["S58"]["path"] == "artifacts/peano-library/channels-v27.json"
    assert "current" in sources["S58"]["label"].lower()
    assert sources["S59"]["path"] == "research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json"
    assert sources["S60"]["path"] == "research/arithmetic-library/alpha-v27-second-wave-receipt.md"
    assert sources["S61"]["path"] == "research/arithmetic-library/alpha-v27-second-wave-rfc-v1.md"
    assert all((REPO / sources[name]["path"]).is_file() for name in ("S58", "S59", "S60", "S61"))
    for identifier, expected_size, expected_digest in (
        ("S27", 4_176_537, RESIDUAL_BUNDLE_IDENTITY),
        ("S28", 1_617_207, FRONTIER_BUNDLE_IDENTITY),
        ("S31", 14_775_673, NEXT_LAYER_BUNDLE_IDENTITY),
        ("S35", 1_005_317, ADVANCED_LAYER_BUNDLE_IDENTITY),
        ("S39", 1_099_541, TRANSPORT_LAYER_BUNDLE_IDENTITY),
        ("S43", 2_518_315, MILESTONE_CLOSURE_BUNDLE_IDENTITY),
        ("S47", 738_923, RESEARCH_LAYER_BUNDLE_IDENTITY),
        ("S51", 1_041_166, BREAKTHROUGH_LAYER_BUNDLE_IDENTITY),
        ("S55", 364_186, FIRST_WAVE_BUNDLE_IDENTITY),
    ):
        artifact = REPO / sources[identifier]["path"]
        assert artifact.stat().st_size == expected_size
        assert sha256(artifact.read_bytes()).hexdigest() == expected_digest
    assert (REPO / sources["S29"]["path"]).is_file()
    assert (REPO / sources["S32"]["path"]).is_file()
    assert (REPO / sources["S33"]["path"]).is_file()
    assert (REPO / sources["S36"]["path"]).is_file()
    assert (REPO / sources["S37"]["path"]).is_file()
    assert (REPO / sources["S40"]["path"]).is_file()
    assert (REPO / sources["S41"]["path"]).is_file()
    assert (REPO / sources["S44"]["path"]).is_file()
    assert (REPO / sources["S45"]["path"]).is_file()
    assert (REPO / sources["S48"]["path"]).is_file()
    assert (REPO / sources["S49"]["path"]).is_file()
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


def test_campaign_release_evidence_matches_all_fourteen_immutable_channel_artifacts() -> None:
    payload = campaign()
    boundaries = payload["ambitious_boundaries"]
    versions = {
        version: json.loads(
            (REPO / "artifacts" / "peano-library" / f"channels-{version}.json").read_text(
                encoding="utf-8"
            )
        )
        for version in (
            "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24", "v25", "v26", "v27", "v28"
        )
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
    assert versions["v20"]["parent_channels_v19"]["path"] == (
        "artifacts/peano-library/channels-v19.json"
    )
    assert versions["v21"]["parent_channels_v20"]["path"] == (
        "artifacts/peano-library/channels-v20.json"
    )
    assert versions["v22"]["parent_channels_v21"]["path"] == (
        "artifacts/peano-library/channels-v21.json"
    )
    assert versions["v23"]["parent_channels_v22"]["path"] == (
        "artifacts/peano-library/channels-v22.json"
    )
    assert versions["v24"]["parent_channels_v23"]["path"] == (
        "artifacts/peano-library/channels-v23.json"
    )
    assert versions["v25"]["parent_channels_v24"]["path"] == (
        "artifacts/peano-library/channels-v24.json"
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
    alpha_v20 = versions["v20"]["channels"]["alpha"]
    assert alpha_v20["alpha_v20_frontier_new_count"] == 39
    assert alpha_v20["parent_alpha_v19_sha256"] == ALPHA_V19_CATALOG_SHA256
    assert alpha_v20["frontier_v20_campaign_counts"] == {
        "polynomial_horner": 7,
        "matrix_dot_product": 10,
        "bertrand_prime": 13,
        "continued_fraction": 9,
    }
    alpha_v21 = versions["v21"]["channels"]["alpha"]
    assert alpha_v21["alpha_v21_frontier_new_count"] == 54
    assert alpha_v21["parent_alpha_v20_sha256"] == ALPHA_V20_CATALOG_SHA256
    assert alpha_v21["frontier_v21_campaign_counts"] == {
        "matrix_coded_product": 23,
        "euclidean_complexity": 15,
        "binary_modular_exponentiation": 16,
    }
    alpha_v22 = versions["v22"]["channels"]["alpha"]
    assert alpha_v22["alpha_v22_frontier_new_count"] == 60
    assert alpha_v22["parent_alpha_v21_sha256"] == ALPHA_V21_CATALOG_SHA256
    assert alpha_v22["frontier_v22_campaign_counts"] == {
        "binary_length": 21,
        "euclidean_gcd_transport": 20,
        "binary_modular_execution": 19,
    }
    alpha_v23 = versions["v23"]["channels"]["alpha"]
    assert alpha_v23["alpha_v23_frontier_new_count"] == 59
    assert alpha_v23["parent_alpha_v22_sha256"] == ALPHA_V22_CATALOG_SHA256
    assert alpha_v23["frontier_v23_campaign_counts"] == {
        "euclidean_logarithmic_bound": 17,
        "binary_digit_extraction": 24,
        "primes_three_mod_four": 18,
    }
    alpha_v24 = versions["v24"]["channels"]["alpha"]
    assert alpha_v24["alpha_v24_frontier_new_count"] == 59
    assert alpha_v24["parent_alpha_v23_sha256"] == ALPHA_V23_CATALOG_SHA256
    assert alpha_v24["frontier_v24_campaign_counts"] == {
        "matrix_determinant_minors": 17,
        "polynomial_hensel": 15,
        "generalized_crt_fold": 27,
    }
    alpha_v25 = versions["v25"]["channels"]["alpha"]
    assert alpha_v25["alpha_v25_frontier_new_count"] == 72
    assert alpha_v25["parent_alpha_v24_sha256"] == ALPHA_V24_CATALOG_SHA256
    assert alpha_v25["frontier_v25_campaign_counts"] == {
        "matrix_cofactor_expansion": 29,
        "polynomial_taylor_hensel": 19,
        "generalized_crt_compatibility": 24,
    }
    alpha_v26 = versions["v26"]["channels"]["alpha"]
    assert alpha_v26["alpha_v26_frontier_new_count"] == 58
    assert alpha_v26["parent_alpha_v25_sha256"] == ALPHA_V25_CATALOG_SHA256
    assert alpha_v26["frontier_v26_campaign_counts"] == {
        "coprime_square_factor": 9, "pythagorean_inverse": 23, "fermat_four_descent": 26,
    }


@pytest.mark.parametrize("identifier,name,digest,count,node_id", (
    ("T13", "rectangular_matrix_rank_exists_unique", "677f945b5341792d5b2281cc8948922456c461c1aeeec880c452199df7d178f1", 182, 896),
    ("G011", "crt_pairwise_compatible_prefix_normalized_exists_unique", "f333d811cf04309d630382e2c049885d0de6e2cf4f26a218faf0e6039b002587", 24, 1041),
    ("G095", "integer_polynomial_prime_simple_root_lifts_all_positive_powers", "158b28822061f364d34a4badf84986d5f02301b58c555b1e67ec758c786709e8", 40, 1022),
    ("G035", "multinomial_kummer_carry_valuation", "f69d92599b4eaa9e893e3a4c0e8ab998234bbce6223fbbde949433c1ee7c8266", 19, 1063),
    ("G027", "prime_count_chebyshev_bounds", "38a80957c2e9e9545cf57e1a036768d506a64edd891be2d0125ffd499fab7428", 55, 1114),
    ("G051", "prime_cauchy_davenport_sumset_bound", "634e3a5403ad025cef1e894dc2b9c3401691bb84bb57c2b70cb3aba185b806fb", 72, 1221),
    ("G107", "cornacchia_prime_two_squares_complete", "becd01e6f073d37e512d385ffbc5e4e929ea3113f9d900fcc189718fc83eefc7", 30, 1150),
))
def test_second_wave_closed_milestones_bind_actual_full_theorem_roots(identifier, name, digest, count, node_id):
    payload = campaign()
    node = next(row for row in payload["nodes"] if row["id"] == identifier)
    evidence = node["evidence"]
    row = alpha_catalog("v27")[name]
    assert node["status"] == "alpha_closed"
    assert evidence["alpha_version"] == "v27"
    assert evidence["theorem_name"] == name
    assert evidence["theorem_statement_sha256"] == row["statement_sha256"]
    if digest is not None:
        assert row["statement_sha256"] == digest
    assert evidence["new_theorem_count"] == count
    assert evidence["bundle_node_id"] == row["empty_context_closure"]["bundle_node_id"] == node_id
    assert evidence["bundle_nodes"] == 1224 and evidence["bundle_dependencies"] == 3999
    assert evidence["bundle_sha256"] == "c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d"
    assert evidence["full_empty_context_closure"] is evidence["independent_lean_bundle_verified"] is evidence["checked_use"] is True
    assert evidence["stable_member"] is False
    assert {"S58", "S59", "S60", "S61"} <= set(node["references"])
    page = REPO / "book/_static/constructive-second-wave-explorer-v28" / evidence["route"] / "explorer/defined/tag" / (evidence["proof_tag"] + ".html")
    assert page.is_file() and name.encode() in page.read_bytes()


def test_historical_second_wave_release_is_preserved_and_does_not_close_broader_roadmap():
    payload = campaign()
    current = payload["ambitious_boundaries"]["alpha_v27_edition"]
    assert current["role"] == "historical_immutable_release"
    assert current["theorem_count"] == current["checked_use_count"] == 2560
    assert current["stable_closed_count"] == 432 and current["alpha_closed_count"] == 2128
    assert current["dependency_edge_count"] == current["checked_dependency_edge_count"] == 8196
    assert current["identity_sha256"] == "5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05"
    assert current["enrollment_sha256"] == "20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e"
    assert current["parent_enrollment_sha256"] == ALPHA_V26_ENROLLMENT_IDENTITY
    transition = payload["ambitious_boundaries"]["second_wave_evidence_transition"]
    assert transition["new_theorem_count"] == 422
    assert set(transition["named_targets_complete"]) == {"T13", "G011", "G095", "G035", "G027", "G051", "G107"}
    assert transition["broader_roadmap_bullets_automatically_closed"] is False
    nodes = {node["id"]: node for node in payload["nodes"]}
    assert all(nodes[name]["status"] == "open" for name in ("G039", "G052", "G082", "G085", "G109", "G115"))
    assert all(nodes[name]["status"] == "alpha_closed" for name in ("G081", "G084"))


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
    normalized_document = re.sub(r"\s+", " ", document)
    ids = re.findall(r"^\d+\. \*\*(G\d{3})\b", document, flags=re.MULTILINE)
    assert len(ids) == 120
    assert set(ids) == EXPECTED_GOALS

    families = re.findall(r"^### (F\d{2})\.", document, flags=re.MULTILINE)
    assert tuple(families) == EXPECTED_FAMILIES
    for value in (
        "Alpha v26", "2,138", "1,706", "6,851", "216", "558", "10,397",
        "189 blueprint", "131 hygienically", "231 reviewed", "99 compatible",
        "Alpha v25", "2,080", "1,648", "6,633", "302", "820", "16,947",
        "179 blueprint", "120 hygienically", "214 reviewed", "88 compatible",
        "83 exact names",
        "Alpha v24", "2,008", "1,576", "6,423", "203", "502", "11,065",
        "738,923", "164 blueprint", "109 hygienically", "186 reviewed",
        "73 compatible", "69 exact names",
        "Alpha v23", "1,949", "1,517", "6,285", "59", "617", "1,871", "39,161",
        "2,518,315", "Alpha v22", "1,890", "1,458", "6,128", "60", "240",
        "597", "11,848", "Alpha v21", "1,830", "1,398", "5,986", "54", "209",
        "491", "10,304", "152 blueprint", "97 hygienically", "159 reviewed",
        "61 compatible",
        "Alpha v20", "1,776", "1,344", "5,882", "39", "590", "2,045", "190,533",
        "Alpha v19", "1,737", "1,305", "5,779", "64",
        "**92 genuinely open research", "**28 existing/revisited constructive",
        "475", "1,452", "38,688", "545", "1,650", "34,020",
        "Alpha v18", "1,157", "84", "1,589", "673", "1,113", "544", "1,917",
        "201,285", "45,254", "31,694",
        "Alpha v17", "1,673", "484", "757", "916", "31", "438", "1,429",
        "Alpha v16", "453", "788", "885", "315",
        "Alpha v15", "138", "1,102", "570",
        "pending_layered_closure", "body_checked",
    ):
        assert value in normalized_document
    assert ALPHA_V16_IDENTITY in document
    assert ALPHA_V17_IDENTITY in document
    assert ALPHA_V18_IDENTITY in document
    assert ALPHA_V19_IDENTITY in document
    assert ALPHA_V20_IDENTITY in document
    assert ALPHA_V21_IDENTITY in document
    assert ALPHA_V22_IDENTITY in document
    assert ALPHA_V23_IDENTITY in document
    assert ALPHA_V24_IDENTITY in document
    assert ALPHA_V18_CATALOG_SHA256 in document
    assert ALPHA_V19_CATALOG_SHA256 in document
    assert ALPHA_V20_CATALOG_SHA256 in document
    assert ALPHA_V21_CATALOG_SHA256 in document
    assert ALPHA_V22_CATALOG_SHA256 in document
    assert ALPHA_V23_CATALOG_SHA256 in document
    assert ALPHA_V24_CATALOG_SHA256 in document
    assert ALPHA_V16_EVIDENCE_ROOT in document
    assert ALPHA_V17_EVIDENCE_ROOT in document
    assert ALPHA_V18_EVIDENCE_ROOT in document
    assert ALPHA_V19_EVIDENCE_ROOT in document
    assert ALPHA_V20_EVIDENCE_ROOT in document
    assert ALPHA_V21_EVIDENCE_ROOT in document
    assert ALPHA_V22_EVIDENCE_ROOT in document
    assert ALPHA_V23_EVIDENCE_ROOT in document
    assert ALPHA_V24_EVIDENCE_ROOT in document
    assert FLAGSHIP_PROMOTION_NAMES_IDENTITY in document
    assert RESIDUAL_PROMOTION_NAMES_IDENTITY in document
    assert FRONTIER_NEW_NAMES_IDENTITY in document
    assert NEXT_LAYER_NEW_NAMES_IDENTITY in document
    assert ADVANCED_LAYER_NEW_NAMES_IDENTITY in document
    assert TRANSPORT_LAYER_NEW_NAMES_IDENTITY in document
    assert RESEARCH_LAYER_NEW_NAMES_IDENTITY in document
    assert MILESTONE_CLOSURE_NEW_NAMES_IDENTITY in document
    assert ALPHA_ENROLLMENT_IDENTITY in document
    assert ALPHA_V19_ENROLLMENT_IDENTITY in document
    assert ALPHA_V20_ENROLLMENT_IDENTITY in document
    assert ALPHA_V21_ENROLLMENT_IDENTITY in document
    assert ALPHA_V22_ENROLLMENT_IDENTITY in document
    assert ALPHA_V23_ENROLLMENT_IDENTITY in document
    assert SUPPLEMENT_BUNDLE_IDENTITY in document
    assert RESIDUAL_BUNDLE_IDENTITY in document
    assert FRONTIER_BUNDLE_IDENTITY in document
    assert NEXT_LAYER_BUNDLE_IDENTITY in document
    assert ADVANCED_LAYER_BUNDLE_IDENTITY in document
    assert TRANSPORT_LAYER_BUNDLE_IDENTITY in document
    assert MILESTONE_CLOSURE_BUNDLE_IDENTITY in document


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
    assert pythagorean == "∀a b c. PrimitiveTriple(a,b,c) ↔ EuclidParametrization(a,b,c)."
    parametrization = definitions["EuclidParametrization"]["expansion"]
    assert "m*m=n*n+a" in parametrization.replace(" ", "")
    assert "m*m=n*n+b" in parametrization.replace(" ", "")
    assert "2*(m*n)" in parametrization.replace(" ", "")

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
        "G077": {"A08", "T07"},
        "G078": {"G077", "T07", "T15"},
        "G079": {"G084", "G085"},
        "G090": {"G088", "G089"},
        "G114": {"G111", "G113"},
        "G120": {"G117", "G118"},
    }
    for summit, prerequisites in expected.items():
        assert prerequisites <= predecessors(summit)
    assert nodes["G077"]["conceptual_refs"] == ["G005", "G062"]
    assert nodes["G078"]["conceptual_refs"] == ["G061"]
    assert "G005" not in nodes["G077"]["deps"]
    assert "G061" not in nodes["G078"]["deps"]


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
    ("D01", "D02"): 30,
    ("D01", "D03"): 20,
    ("D01", "D04"): 22,
    ("D01", "D05"): 4,
    ("D02", "D03"): 9,
    ("D02", "D04"): 3,
    ("D03", "D02"): 1,
    ("D03", "D04"): 1,
    ("D03", "D05"): 2,
    ("D04", "D01"): 4,
    ("D04", "D02"): 4,
    ("D04", "D03"): 5,
    ("D04", "D05"): 6,
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
    assert sum(actual.values()) == 116
    assert len(actual) == 15

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert 'var ATLAS_DOMAINS = [' in explorer
    for identifier in ATLAS_DOMAIN_FAMILIES:
        assert f'id: "{identifier}"' in explorer
    assert '"data-dependency-weight": edge.count' in explorer
    assert "underlying 144-node proof graph is acyclic" in explorer


def test_blueprint_definition_dag_is_separate_acyclic_and_lexically_exact() -> None:
    payload = campaign()
    definitions = payload["definitions"]
    artifact = json.loads(
        (CAMPAIGN.parent / "definitions.json").read_text(encoding="utf-8")
    )
    assert len(definitions) == artifact["definition_count"] == 323
    assert artifact["reviewed_definition_count"] == 233
    assert artifact["reviewed_definition_edge_count"] == 441
    assert artifact["compatible_reviewed_match_count"] == 236
    assert artifact["exact_name_reviewed_match_count"] == 231
    assert artifact["explicit_alias_reviewed_match_count"] == 5
    assert artifact["incompatible_reviewed_match_count"] == 2

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
    assert sum(map(len, notation_edges.values())) == (
        artifact["definition_edge_count"]
    ) == 459
    assert sum(map(len, statement_edges.values())) == (
        artifact["statement_usage_edge_count"]
    ) == 317
    assert artifact["declared_notation_edge_count"] == 231
    assert artifact["milestone_usage_edge_count"] == 548
    assert notation_edges["PowerValuation"] == {"Val"}
    assert notation_edges["Val"] == {"Prime", "Dvd"}
    assert notation_edges["Prime"] == {"Dvd"}
    assert notation_edges["BertrandWindow"] == {"Lt", "Prime"}
    assert notation_edges["BertrandChain"] == {"BertrandWindow", "Beta", "Lt"}
    assert notation_edges["PowerValuationOne"] == {"PowerValuation"}
    assert notation_edges["Horner"] == {"Beta", "Lt"}
    assert notation_edges["HornerDerivativeTrace"] == {"Beta", "Lt"}
    assert notation_edges["HornerDerivative"] == {
        "HornerDerivativeTrace", "Beta", "Horner"
    }
    assert notation_edges["HornerDerivativeOnly"] == {"HornerDerivative"}
    assert notation_edges["MatrixAt"] == {"Beta"}
    assert notation_edges["MatrixSkipIndex"] == {"Lt", "Le"}
    assert notation_edges["MatrixMinorCell"] == {"MatrixSkipIndex", "Beta"}
    assert notation_edges["MatrixMinorPrefix"] == {
        "Lt", "MatrixMinorCell", "Beta"
    }
    assert notation_edges["SignedMatrixMinor"] == {"MatrixMinorPrefix"}
    assert notation_edges["CRTPositiveModuliPrefix"] == {"Lt", "Beta"}
    assert notation_edges["CRTPairwiseCoprimePrefix"] == {
        "Lt", "Beta", "Coprime"
    }
    assert notation_edges["CRTPrefixSolution"] == {"Lt", "Beta"}
    assert notation_edges["CRTPrefixLCM"] == {"Lt", "Beta", "Dvd"}
    assert notation_edges["CRTCanonicalPrefixSolution"] == {
        "CRTPrefixLCM", "Lt", "CRTPrefixSolution"
    }
    assert notation_edges["Even"] == set()
    assert notation_edges["Odd"] == set()
    assert notation_edges["ModEq"] == set()
    assert notation_edges["BetaSum"] == {"Beta", "Lt"}
    assert notation_edges["SignedMinorRecord"] == {
        "MatrixMinorFourCode", "SignedMatrixMinor"
    }
    assert notation_edges["SignedCofactorMinorPrefix"] == {
        "Beta", "Lt", "SignedMinorRecord"
    }
    assert notation_edges["SignedAlternatingCofactorTerm"] == {"Even", "Odd"}
    assert notation_edges["SignedAlternatingProductPrefix"] == {
        "Beta", "Lt", "SignedAlternatingCofactorTerm"
    }
    assert notation_edges["SignedAlternatingCofactorFold"] == {
        "SignedAlternatingProductPrefix", "BetaSum"
    }
    assert notation_edges["SignedFirstRowCofactorFold"] == {
        "MatrixAffineSlice", "SignedAlternatingCofactorFold"
    }
    assert notation_edges["HornerTaylorRemainder"] == {"HornerDerivative", "Horner"}
    assert notation_edges["HenselCorrection"] == {"Lt", "ModEq"}
    assert notation_edges["CRTPairwiseCompatiblePrefix"] == {
        "Lt", "Beta", "Gcd", "ModEq"
    }
    assert notation_edges["CRTMergeCompatiblePrefix"] == {
        "Lt", "CRTPrefixLCM", "CRTPrefixSolution", "Beta", "Gcd", "ModEq"
    }
    assert notation_edges["DotProduct"] == {"Beta", "Lt"}
    assert notation_edges["SignedDet2"] == set()
    assert notation_edges["MatrixAffineSlice"] == {"Beta", "Lt"}
    assert notation_edges["MatrixProductCell"] == {"MatrixAffineSlice", "DotProduct"}
    assert notation_edges["MatrixProductPrefix"] == {"MatrixProductCell", "Beta", "Lt"}
    assert notation_edges["MatrixPointwiseAdd"] == {"Beta", "Lt"}
    assert notation_edges["SignedDotProduct"] == {"DotProduct"}
    assert notation_edges["SignedMatrixProduct"] == {"MatrixProductPrefix", "MatrixPointwiseAdd"}
    assert notation_edges["ContinuedFractionTrace"] == {"Beta", "Lt", "ListCell"}
    assert notation_edges["EuclideanExecution"] == {"ContinuedFractionTrace", "Gcd"}
    assert notation_edges["BinaryModularPower"] == {"Pow", "CanonicalModularResidue"}
    assert notation_edges["PowTwo"] == {"Pow"}
    assert notation_edges["BinaryDigit"] == {"BinaryExponentSplit"}
    assert notation_edges["BitLen"] == {"PowTwo"}
    assert notation_edges["EuclideanCommonDivisor"] == {"Dvd"}
    assert notation_edges["EuclideanStateAt"] == {"Beta"}
    assert notation_edges["EuclideanAnchoredExecution"] == {
        "ContinuedFractionTrace", "EuclideanStateAt", "Gcd"
    }
    assert notation_edges["BinaryDigitPrefix"] == {"Beta", "Lt"}
    assert notation_edges["BinaryExecutionTrace"] == {
        "Beta", "Lt", "BinaryModularStep"
    }
    assert notation_edges["BinaryModularExecution"] == {
        "BinaryExecutionTrace", "Beta"
    }
    assert notation_edges["BinaryExecutionPowerInvariant"] == {
        "Horner", "BinaryModularPower"
    }
    assert notation_edges["Mod4Three"] == set()
    assert notation_edges["AllBits"] == {"Beta", "Lt"}
    assert notation_edges["BitCount"] == {"AllBits"}
    assert notation_edges["EuclideanBoundedTrace"] == {
        "ContinuedFractionTrace", "Le"
    }
    assert notation_edges["EuclideanLogarithmicExecution"] == {
        "BitLen", "EuclideanAnchoredExecution", "Le"
    }
    assert notation_edges["BinaryExponentDigitCode"] == {
        "BinaryDigitPrefix", "Horner"
    }
    assert notation_edges["BinaryCanonicalExponentDigitCode"] == {
        "BinaryExponentDigitCode", "BitLen"
    }
    assert notation_edges["BinaryCompleteModularExecution"] == {
        "BinaryCanonicalExponentDigitCode",
        "BinaryModularExecution",
        "BinaryModularPower",
    }
    assert notation_edges["BinaryExecutionOperationCount"] == {"BitCount"}
    assert notation_edges["PrimeThreeModFourDivisor"] == {
        "Dvd", "Mod4Three", "Prime"
    }
    assert notation_edges["EuclidThreeNumber"] == {"Mod4Three"}
    assert {"Prime", "Rep2"} <= statement_edges["G061"]
    assert statement_edges["T12"] == {"Horner"}

    declared = {node["id"]: set(node.get("definition_refs", [])) for node in payload["nodes"]}
    assert declared["T12"] == {"Horner", "Beta"}
    from build_constructive_second_wave_explorer import FAMILIES, _family_definitions
    for family in FAMILIES:
        assert declared[family.milestones[-1]] == {
            item.name if item.name != "Sum" else "BetaSum"
            for item in _family_definitions(family)
        }
    assert declared["G023"] == {"BertrandWindow", "PowerValuationOne"}
    assert declared["G024"] == {"BertrandChain", "BertrandWindow"}
    assert declared["G071"] == {"ContinuedFraction", "Beta"}
    assert declared["G025"] == {
        "Prime", "Mod4Three", "Dvd", "PrimeThreeModFourDivisor", "EuclidThreeNumber"
    }
    assert declared["G101"] == {
        "EuclideanDivision", "EuclideanHalving", "EuclideanExecution",
        "ContinuedFractionTrace", "EuclideanCommonDivisor", "EuclideanStateAt",
        "EuclideanAnchoredExecution", "EuclideanBoundedTrace",
        "EuclideanLogarithmicExecution", "PowTwo", "BitLen", "Le",
    }
    assert declared["G102"] == {
        "BinaryModulus", "BinaryExponentSplit", "CanonicalModularResidue",
        "BinaryDoubledPower", "BinaryOddPower", "BinaryModularStep",
        "BinaryModularPower", "PowTwo", "BinaryDigit", "BitLen",
        "BinaryDigitPrefix", "BinaryExecutionTrace", "BinaryModularExecution",
        "BinaryExecutionPowerInvariant", "AllBits", "BitCount",
        "BinaryExponentDigitCode", "BinaryCanonicalExponentDigitCode",
        "BinaryCompleteModularExecution", "BinaryExecutionOperationCount", "Execution",
    }

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
    assert len(ordered) == len(definitions)

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert "Blueprint vocabulary only" in explorer
    assert "notation links are separate from proof premises" in explorer
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
    assert ready == {
        "G006", "G007", "G010", "G036", "G039", "G045", "G052", "G068",
        "G072", "G082", "G085", "G087", "G091", "G093", "G109", "G115",
    }
    blueprint = BLUEPRINT.read_text(encoding="utf-8")
    scheduled = re.findall(
        r"^\| (\d+) \| (T\d{2}|G\d{3}) \|",
        blueprint,
        flags=re.MULTILINE,
    )
    assert scheduled == [
        ("3", "T13"),
        ("6", "G051"),
        ("6", "G095"),
        ("8", "G027"),
        ("8", "G035"),
        ("9", "G107"),
    ]
    historical_ready = {identifier for _layer, identifier in scheduled}
    assert historical_ready.isdisjoint(ready)
    assert all(nodes[identifier]["status"] == "alpha_closed" for identifier in historical_ready)
    assert all(int(layer) == nodes[identifier]["layer"] for layer, identifier in scheduled)
    assert {"T12", "G023", "G024", "G025", "G071", "G101", "G102"}.isdisjoint(ready)
    assert nodes["T13"]["historical_partial_evidence"]["partial_component_checked_use"] is True
    assert nodes["T13"]["historical_partial_evidence"]["checked_use"] is False
    assert nodes["T13"]["evidence"]["checked_use"] is True
    assert nodes["G002"]["status"] == "alpha_closed"
    assert nodes["G002"]["historical_foundation_classification"] == "existing_foundation"
    assert all(
        nodes[identifier]["status"] == "alpha_closed"
        for identifier in ("G025", "G101", "G102")
    )
    assert nodes["G077"]["status"] == "alpha_closed"
    assert nodes["G077"]["evidence"]["checked_use"] is True
    assert nodes["G078"]["status"] == "alpha_closed"
    assert nodes["G078"]["evidence"]["checked_use"] is True

    explorer = EXPLORER.read_text(encoding="utf-8")
    assert "Ready to investigate — not proved" in explorer
    assert "existing unverified foundations" in explorer.lower()
    assert "Existing anchor only — this extension remains unproved" in explorer


def test_checked_definition_cross_links_resolve_to_actual_explorer_pages() -> None:
    expected = {
        "AllBits": ("quadratic-reciprocity", "PD0016"),
        "Beta": ("quadratic-reciprocity", "PD0013"),
        "Binom": ("bertrand-postulate", "PD0041"),
        "BitCount": ("quadratic-reciprocity", "PD0017"),
        "Coprime": ("quadratic-reciprocity", "PD0005"),
        "DivRem": ("quadratic-reciprocity", "PD0007"),
        "Dvd": ("quadratic-reciprocity", "PD0003"),
        "Fact": ("quadratic-reciprocity", "PD0023"),
        "FactorialValuation": ("bertrand-postulate", "PD0048"),
        "Gcd": ("quadratic-reciprocity", "PD0006"),
        "Le": ("quadratic-reciprocity", "PD0001"),
        "LegendreSum": ("bertrand-postulate", "PD0050"),
        "Lt": ("quadratic-reciprocity", "PD0002"),
        "Mod4Three": ("quadratic-reciprocity", "PD0012"),
        "Pow": ("quadratic-reciprocity", "PD0020"),
        "PowerValuation": ("bertrand-postulate", "PD0046"),
        "Prime": ("quadratic-reciprocity", "PD0004"),
        "Horner": ("polynomial-horner", "ND0002"),
        "MatrixAt": ("matrix-dot-product", "ND0003"),
        "DotProduct": ("matrix-dot-product", "ND0004"),
        "SignedDet2": ("matrix-dot-product", "ND0005"),
        "BertrandWindow": ("bertrand-prime-chains", "ND0006"),
        "PowerValuationOne": ("bertrand-prime-chains", "ND0007"),
        "BertrandChain": ("bertrand-prime-chains", "ND0008"),
        "ListCell": ("continued-fractions", "ND0009"),
        "ContinuedFractionTrace": ("continued-fractions", "ND0010"),
        "ContinuedFraction": ("continued-fractions", "ND0011"),
        "MatrixAffineSlice": ("matrix-coded-products", "ND0012"),
        "MatrixProductCell": ("matrix-coded-products", "ND0013"),
        "MatrixProductPrefix": ("matrix-coded-products", "ND0014"),
        "MatrixPointwiseAdd": ("matrix-coded-products", "ND0015"),
        "SignedDotProduct": ("matrix-coded-products", "ND0016"),
        "SignedMatrixProduct": ("matrix-coded-products", "ND0017"),
        "EuclideanDivision": ("euclidean-complexity", "ND0018"),
        "EuclideanHalving": ("euclidean-complexity", "ND0019"),
        "EuclideanExecution": ("euclidean-complexity", "ND0020"),
        "BinaryModulus": ("binary-modular-exponentiation", "ND0021"),
        "BinaryExponentSplit": ("binary-modular-exponentiation", "ND0022"),
        "CanonicalModularResidue": ("binary-modular-exponentiation", "ND0023"),
        "BinaryDoubledPower": ("binary-modular-exponentiation", "ND0024"),
        "BinaryOddPower": ("binary-modular-exponentiation", "ND0025"),
        "BinaryModularStep": ("binary-modular-exponentiation", "ND0026"),
        "BinaryModularPower": ("binary-modular-exponentiation", "ND0027"),
        "PowTwo": ("binary-length", "ND0028"),
        "BinaryDigit": ("binary-length", "ND0029"),
        "BitLen": ("binary-length", "ND0030"),
        "EuclideanCommonDivisor": ("euclidean-gcd-transport", "ND0031"),
        "EuclideanStateAt": ("euclidean-gcd-transport", "ND0032"),
        "EuclideanAnchoredExecution": ("euclidean-gcd-transport", "ND0033"),
        "BinaryDigitPrefix": ("binary-modular-execution", "ND0034"),
        "BinaryExecutionTrace": ("binary-modular-execution", "ND0035"),
        "BinaryModularExecution": ("binary-modular-execution", "ND0036"),
        "BinaryExecutionPowerInvariant": ("binary-modular-execution", "ND0037"),
        "EuclideanBoundedTrace": ("euclidean-logarithmic-bound", "ND0038"),
        "EuclideanLogarithmicExecution": ("euclidean-logarithmic-bound", "ND0039"),
        "BinaryExponentDigitCode": ("binary-digit-extraction", "ND0040"),
        "BinaryCanonicalExponentDigitCode": ("binary-digit-extraction", "ND0041"),
        "BinaryCompleteModularExecution": ("binary-digit-extraction", "ND0042"),
        "BinaryExecutionOperationCount": ("binary-digit-extraction", "ND0043"),
        "PrimeThreeModFourDivisor": ("primes-three-mod-four", "ND0044"),
        "EuclidThreeNumber": ("primes-three-mod-four", "ND0045"),
        "MatrixSkipIndex": ("matrix-determinant-minors", "ND0046"),
        "MatrixMinorCell": ("matrix-determinant-minors", "ND0047"),
        "MatrixMinorPrefix": ("matrix-determinant-minors", "ND0048"),
        "SignedMatrixMinor": ("matrix-determinant-minors", "ND0049"),
        "HornerDerivativeTrace": ("polynomial-hensel", "ND0050"),
        "HornerDerivative": ("polynomial-hensel", "ND0051"),
        "HornerDerivativeOnly": ("polynomial-hensel", "ND0052"),
        "CRTPositiveModuliPrefix": ("generalized-crt-fold", "ND0053"),
        "CRTPairwiseCoprimePrefix": ("generalized-crt-fold", "ND0054"),
        "CRTPrefixSolution": ("generalized-crt-fold", "ND0055"),
        "CRTPrefixLCM": ("generalized-crt-fold", "ND0056"),
        "CRTCanonicalPrefixSolution": ("generalized-crt-fold", "ND0057"),
        "Even": ("quadratic-reciprocity", "PD0009"),
        "Odd": ("quadratic-reciprocity", "PD0010"),
        "ModEq": ("quadratic-reciprocity", "PD0008"),
        "BetaSum": ("quadratic-reciprocity", "PD0015"),
        "MatrixMinorFourCode": ("matrix-cofactor-expansion", "ND0058"),
        "SignedMinorRecord": ("matrix-cofactor-expansion", "ND0059"),
        "SignedCofactorMinorPrefix": ("matrix-cofactor-expansion", "ND0060"),
        "SignedAlternatingCofactorTerm": ("matrix-cofactor-expansion", "ND0061"),
        "SignedAlternatingProductPrefix": ("matrix-cofactor-expansion", "ND0062"),
        "SignedAlternatingCofactorFold": ("matrix-cofactor-expansion", "ND0063"),
        "SignedFirstRowCofactorFold": ("matrix-cofactor-expansion", "ND0064"),
        "HornerTaylorRemainder": ("polynomial-taylor-hensel", "ND0065"),
        "HenselCorrection": ("polynomial-taylor-hensel", "ND0066"),
        "CRTPairwiseCompatiblePrefix": ("generalized-crt-compatibility", "ND0067"),
        "CRTMergeCompatiblePrefix": ("generalized-crt-compatibility", "ND0068"),
        "Pythagorean": ("pythagorean-fermat-four", "CF0011"),
        "PrimitivePythagorean": ("pythagorean-fermat-four", "CF0013"),
        "FermatFourCounterexample": ("pythagorean-fermat-four", "CF0014"),
        "FermatFourStrictDescent": ("pythagorean-fermat-four", "CF0015"),
        "OppositeParity": ("pythagorean-fermat-four", "CF0016"),
        "PrimitiveTriple": ("pythagorean-fermat-four", "ND0069"),
        "EuclidParameters": ("pythagorean-fermat-four", "ND0070"),
        "PrimitiveFermatFourCounterexample": ("pythagorean-fermat-four", "ND0071"),
        "SmallerFermatFourCounterexample": ("pythagorean-fermat-four", "ND0072"),
        "TrivialFermatFourSolution": ("pythagorean-fermat-four", "ND0073"),
        "EuclidParametrization": ("pythagorean-fermat-four", "ND0074"),
    }
    # Preserve all 99 earlier hand-pinned aliases, then independently derive
    # the newly exposed canonical names from the actual reviewed registries.
    assert len(expected) == 99
    from constructive_lower_layer_definition_graph import DEFAULT_REGISTRIES, REVIEWED_BLUEPRINT_ALIASES

    blueprint_definitions = campaign()["definitions"]
    for route, group in DEFAULT_REGISTRIES:
        for definition in group:
            item = blueprint_definitions.get(definition.name)
            if item and len(item["parameters"]) == len(definition.parameters):
                value = (route, definition.stable_id)
                if definition.name in expected:
                    if expected[definition.name] != value:
                        assert definition.name in REVIEWED_BLUEPRINT_ALIASES
                    continue
                expected[definition.name] = value
    artifact = json.loads(
        (CAMPAIGN.parent / "definitions.json").read_text(encoding="utf-8")
    )
    matches = {
        row["blueprint_name"]: row
        for row in artifact["compatible_reviewed_matches"]
    }
    explorer = EXPLORER.read_text(encoding="utf-8")
    for name, (route, identifier) in expected.items():
        assert matches[name]["reviewed_id"] == identifier
        assert matches[name]["route"] == route
        route = artifact.get("definition_page_overrides", {}).get(identifier, {}).get("route", route)
        assert f'{name}: {{ id: "{identifier}", route: "{route}"' in explorer
        assert len(matches[name]["reviewed_parameters"]) == len(
            campaign()["definitions"][name]["parameters"]
        )
        if route == "quadratic-reciprocity":
            destination = (
                REPO / "book" / "_static" / "pa-proof-explorer"
                / "defined" / "definition" / f"{identifier}.html"
            )
        elif route == "bertrand-postulate":
            destination = (
                REPO / "book" / "_static" / "bertrand-proof-explorer"
                / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "matrix-coded-products", "euclidean-complexity", "binary-modular-exponentiation"
        }:
            destination = (
                REPO / "book" / "_static" / "constructive-advanced-layer-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "binary-length", "euclidean-gcd-transport", "binary-modular-execution"
        }:
            destination = (
                REPO / "book" / "_static" / "constructive-transport-layer-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "euclidean-logarithmic-bound", "binary-digit-extraction", "primes-three-mod-four"
        }:
            destination = (
                REPO / "book" / "_static" / "constructive-milestone-closure-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold"
        }:
            destination = (
                REPO / "book" / "_static" / "constructive-research-layer-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "matrix-cofactor-expansion",
            "polynomial-taylor-hensel",
            "generalized-crt-compatibility",
        }:
            destination = (
                REPO / "book" / "_static" / "constructive-breakthrough-layer-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        elif route in {
            "integer-linear-algebra", "hensel-lifting", "generalized-crt",
            "multinomial-kummer", "prime-count-chebyshev", "cornacchia", "cauchy-davenport",
        }:
            destination = (
                REPO / "book/_static/constructive-second-wave-explorer-v28"
                / route / "explorer/defined/definition" / f"{identifier}.html"
            )
        elif route in {"arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers"}:
            destination = (
                REPO / "book/_static/constructive-lower-layer-explorer"
                / route / "explorer/defined/definition" / f"{identifier}.html"
            )
        elif route == "pythagorean-fermat-four":
            destination = (
                REPO / "book/_static/constructive-frontier-explorer"
                / route / "explorer/defined/definition" / f"{identifier}.html"
            )
        else:
            destination = (
                REPO / "book" / "_static" / "constructive-next-layer-explorer"
                / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
            )
        assert destination.is_file()
    assert len(expected) == 236
    assert set(matches) == set(expected)
    assert matches["Gcd"]["reviewed_argument_blueprint_positions"] == [2, 0, 1]
    assert {row["blueprint_name"] for row in artifact["incompatible_reviewed_matches"]} == {
        "Prod",
        "Sum",
    }
    assert "var INCOMPATIBLE_DEFINITIONS = {" in explorer
    assert "No checked-definition evidence is conferred" in explorer


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
    if (["[data-family]", "[data-layer]", "[data-evidence-filter]", "[data-definition-domain]", "[data-definition-trust]", "[data-definition-layer]"].includes(selector)) {
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

atlasModes.find(button => button.attributes["data-atlas-view"] === "definitions").click();
atlasButton("[data-definition-grid]", "data-definition-name", "Sum").click();
const sumDetail = item("[data-definition-detail]").children.map(child => child.textContent);
const sumLinks = descendants(item("[data-definition-detail]"), child => child.name === "a").map(child => child.attributes.href);
atlasButton("[data-definition-grid]", "data-definition-name", "Prod").click();
const productDetail = item("[data-definition-detail]").children.map(child => child.textContent);
const productLinks = descendants(item("[data-definition-detail]"), child => child.name === "a").map(child => child.attributes.href);
atlasButton("[data-definition-grid]", "data-definition-name", "Gcd").click();
const gcdDetail = item("[data-definition-detail]").children.map(child => child.textContent);
const gcdLinks = descendants(item("[data-definition-detail]"), child => child.name === "a").map(child => child.attributes.href);
const nextLayerDefinitions = {};
for (const name of ["Horner", "MatrixAt", "DotProduct", "SignedDet2", "BertrandWindow", "PowerValuationOne", "BertrandChain", "ContinuedFraction"]) {
  atlasButton("[data-definition-grid]", "data-definition-name", name).click();
  nextLayerDefinitions[name] = descendants(item("[data-definition-detail]"), child => child.name === "a")
    .map(child => child.attributes.href);
}

const layerControl = item("[data-definition-layer]");
layerControl.value = "4";
for (const callback of layerControl.listeners.change || []) callback({});
const fourthLayerNames = item("[data-definition-grid]").children
  .map(child => child.attributes["data-definition-name"]);
layerControl.value = "all";
const trustControl = item("[data-definition-trust]");
trustControl.value = "incompatible";
for (const callback of trustControl.listeners.change || []) callback({});
const incompatibleNames = item("[data-definition-grid]").children
  .map(child => child.attributes["data-definition-name"])
  .sort();

process.stdout.write(JSON.stringify({
  initialFamily, overviewDomainCount, domainGraphWeights, domainGoalCount, familyGoalCount,
  selectedGoal, goalProofLinks, goalUrl, primeDetail, primeLinks, definitionUrl,
  afterBack, frontierCards, frontierCount, notationCount, qrNavigation,
  sumDetail, sumLinks, productDetail, productLinks, gcdDetail, gcdLinks,
  fourthLayerNames, incompatibleNames, nextLayerDefinitions
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
    nodes = {row["id"]: row for row in campaign()["nodes"]}
    checked_statuses = {"available", "stable_closed", "alpha_closed"}
    open_statuses = {"open", "existing_anchor_extension", "existing_anchor_closure"}
    expected_frontier = {
        row["id"]
        for row in nodes.values()
        if row["status"] in open_statuses
        and all(
            nodes[dependency]["status"] in checked_statuses
            for dependency in row["deps"]
        )
    }
    assert expected_frontier <= set(actual["frontierCards"])
    assert actual["frontierCount"].startswith(f"{len(expected_frontier)} ready")
    assert {"T12", "G023", "G024", "G071"}.isdisjoint(expected_frontier)
    artifact = json.loads(
        (CAMPAIGN.parent / "definitions.json").read_text(encoding="utf-8")
    )
    assert f'{artifact["definition_count"]} blueprint terms' in actual["notationCount"]
    assert f'{artifact["definition_edge_count"]} lexical expansion edges' in actual["notationCount"]
    assert f'{artifact["statement_usage_edge_count"]} lexical statement-use edges' in actual["notationCount"]
    assert f'{artifact["declared_notation_edge_count"]} explicitly declared notation links' in actual["notationCount"]
    assert f'{artifact["topological_layer_count"]} dependency layers' in actual["notationCount"]
    assert (
        f'{artifact["compatible_reviewed_match_count"]} '
        "signature-compatible checked-registry matches"
    ) in actual["notationCount"]
    assert "2 incompatible reviewed signatures" in actual["notationCount"]
    assert any("incompatible arity (3 versus 4)" in text for text in actual["sumDetail"])
    assert any("No checked-definition evidence is conferred" in text for text in actual["sumDetail"])
    assert actual["sumLinks"] == []
    assert any("Product(b, c, l, z)" in text for text in actual["productDetail"])
    assert actual["productLinks"] == []
    assert any("reviewed argument positions in the blueprint are [2, 0, 1]" in text for text in actual["gcdDetail"])
    assert actual["gcdLinks"] == [expected_qr_prefix + "definition/PD0006.html"]
    deployed = "/proofs/grand-campaign/" in location
    shared = {
        "Horner": ("polynomial-horner", "ND0002"),
        "MatrixAt": ("matrix-dot-product", "ND0003"),
        "DotProduct": ("matrix-dot-product", "ND0004"),
        "SignedDet2": ("matrix-dot-product", "ND0005"),
        "BertrandWindow": ("bertrand-prime-chains", "ND0006"),
        "PowerValuationOne": ("bertrand-prime-chains", "ND0007"),
        "BertrandChain": ("bertrand-prime-chains", "ND0008"),
        "ContinuedFraction": ("continued-fractions", "ND0011"),
    }
    for name, (route, identifier) in shared.items():
        prefix = (
            f"../{route}/explorer/defined/"
            if deployed else
            f"../constructive-next-layer-explorer/{route}/explorer/defined/"
        )
        assert actual["nextLayerDefinitions"][name] == [
            prefix + f"definition/{identifier}.html"
        ]
    graph_rows = {row["name"]: row for row in artifact["definitions"]}
    assert actual["fourthLayerNames"]
    assert all(
        graph_rows[name]["topological_layer"] == 4
        for name in actual["fourthLayerNames"]
    )
    assert actual["incompatibleNames"] == ["Prod", "Sum"]

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
