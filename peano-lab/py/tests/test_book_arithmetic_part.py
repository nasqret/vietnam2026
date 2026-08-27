"""Contracts for the generated, interactive arithmetic Jupyter Book part."""

from __future__ import annotations

import collections
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit


REPO = Path(__file__).resolve().parents[3]
BOOK = REPO / "book"
ATLAS = BOOK / "arithmetic-library" / "theorem-atlas.md"
GUIDE = BOOK / "arithmetic-library" / "guided-tour.md"
K3B_CHAPTER = BOOK / "arithmetic-library" / "cell-history-and-lookup.md"
K3B_SITE = BOOK / "_static" / "pa-proof-explorer" / "k3b"
LIBRARY_EDITIONS = BOOK / "arithmetic-library" / "library-editions.md"
GRAND_CAMPAIGN_CHAPTER = BOOK / "arithmetic-library" / "grand-campaign-atlas.md"
NEXT_LAYER_CHAPTER = BOOK / "arithmetic-library" / "next-layer-campaign.md"
ADVANCED_LAYER_CHAPTER = BOOK / "arithmetic-library" / "advanced-layer-campaign.md"
TRANSPORT_LAYER_CHAPTER = BOOK / "arithmetic-library" / "transport-layer-campaign.md"
BERTRAND_CAMPAIGN = BOOK / "arithmetic-library" / "bertrand-campaign.md"
K3B_RECEIPT = (
    REPO
    / "artifacts"
    / "peano-library"
    / "ha-k3b-listat-full-closure-219217.json"
)
SNAPSHOT = REPO / "artifacts" / "peano-library" / "catalog-v1.json"
RESEARCH = REPO / "research" / "arithmetic-library" / "catalog.json"
GENERATOR = REPO / "scripts" / "build_arithmetic_book_atlas.py"
BOOK_GATE = REPO / "scripts" / "verify_book_commands.py"

DOMAIN_COUNTS = {
    "equality": 10,
    "addition": 12,
    "multiplication": 19,
    "order": 29,
    "divisibility": 20,
    "congruence": 58,
    "division": 13,
    "gcd_coprime": 45,
    "primes": 13,
    "factorization": 76,
    "quadratic_residues": 137,
}
PROOF_SNAPSHOT_COMMIT = "2037b87905817ada187e2477af22c57ff47fb512"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_current_definition_counts(definitions: dict) -> None:
    expected = {
        "definition_count": 290,
        "definition_edge_count": 406,
        "statement_usage_edge_count": 313,
        "declared_notation_edge_count": 213,
        "milestone_usage_edge_count": 526,
        "reviewed_definition_count": 198,
        "reviewed_definition_edge_count": 388,
        "compatible_reviewed_match_count": 201,
        "exact_name_reviewed_match_count": 196,
        "explicit_alias_reviewed_match_count": 5,
        "incompatible_reviewed_match_count": 2,
    }
    assert {key: definitions[key] for key in expected} == expected


def _assert_closed_matrix_and_algorithm_scopes(nodes: dict) -> None:
    for identifier in ("T13", "G101", "G102"):
        assert nodes[identifier]["status"] == "alpha_closed"
        assert nodes[identifier]["evidence"]["full_empty_context_closure"] is True
        assert nodes[identifier]["evidence"]["independent_lean_bundle_verified"] is True
        assert nodes[identifier]["evidence"]["stable_member"] is False
    matrix = nodes["T13"]["evidence"]
    for claim in ("full_arbitrary_determinant_proved", "full_arbitrary_signed_matrix_product_proved",
                  "full_rank_substrate_proved", "integer_column_span_zero_add_neg_proved"):
        assert matrix[claim] is True
    for claim in ("determinant_multiplicativity_proved", "lattice_index_formula_proved",
                  "independent_basis_theorem_proved", "normal_form_or_reduction_proved"):
        assert matrix[claim] is False
    euclidean = nodes["G101"]["evidence"]
    assert euclidean["terminal_state_identified_with_gcd_proved"] is True
    assert euclidean["formal_bit_length_unique_proved"] is True
    assert euclidean["formal_logarithmic_bound_proved"] is True
    binary = nodes["G102"]["evidence"]
    for claim in ("formal_complete_binary_execution_proved", "formal_execution_power_correct_proved",
                  "arbitrary_exponent_binary_digits_proved", "formal_logarithmic_bound_proved"):
        assert binary[claim] is True


def test_atlas_query_links_are_real_html_anchors_with_valid_destinations() -> None:
    campaign = _load(BOOK / "_static/constructive-grand-campaign/campaign.json")
    atlas = (BOOK / "_static/constructive-grand-campaign/index.html").read_text(encoding="utf-8")
    domains = re.search(r"var ATLAS_DOMAINS = \[(.*?)\n      \];", atlas, flags=re.S)
    assert domains is not None
    valid = {
        "goal": {row["id"] for row in campaign["nodes"]},
        "family": {row["id"] for row in campaign["families"]},
        "domain": set(re.findall(r'id: "(D[0-9]{2})"', domains.group(1))),
        "definition": set(campaign["definitions"]),
    }
    checked = 0
    for chapter in (GRAND_CAMPAIGN_CHAPTER, NEXT_LAYER_CHAPTER, TRANSPORT_LAYER_CHAPTER):
        source = chapter.read_text(encoding="utf-8")
        # MyST resolves a relative Markdown query as part of a file name.
        # Real HTML anchors preserve the query without suppressing warnings.
        assert not re.search(r"\]\(\.\./_static/[^)\s]*\?", source)
        for href in re.findall(r'<a\b[^>]*\bhref="([^"]*constructive-grand-campaign/[^"]*)"', source):
            destination = urlsplit(html.unescape(href))
            local = (chapter.parent / destination.path).resolve()
            assert local.is_relative_to(BOOK.resolve()) and local.is_file()
            query = parse_qs(destination.query, strict_parsing=True) if destination.query else {}
            if "view" in query:
                assert len(query["view"]) == len(query.get("focus", ())) == 1
                assert query["view"][0] in valid
                assert query["focus"][0] in valid[query["view"][0]]
            checked += 1
    assert checked >= 35


def test_arithmetic_dashboard_tour_atlas_and_dependency_chapters_are_ordered() -> None:
    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    chapters = (
        "index",
        "library-editions",
        "grand-campaign-atlas",
        "next-layer-campaign",
        "advanced-layer-campaign",
        "transport-layer-campaign",
        "guided-tour",
        "theorem-atlas",
        "proof-explorer",
        "language-and-trust",
        "proof-sharing",
        "dependency-ladder",
        "divisibility-and-congruence",
        "gcd-and-bezout",
        "strict-ha-campaign",
        "cell-history-and-lookup",
        "primes-and-factorization",
        "quadratic-reciprocity",
        "source-audit",
        "using-the-library",
    )
    positions = [
        toc.index(f"- file: arithmetic-library/{chapter}") for chapter in chapters
    ]
    assert positions == sorted(positions)
    for chapter in chapters:
        source = BOOK / "arithmetic-library" / f"{chapter}.md"
        assert source.is_file()
        assert source.read_text(encoding="utf-8").startswith("# ")


def test_grand_campaign_book_chapter_connects_research_scales_honestly() -> None:
    chapter = html.unescape(GRAND_CAMPAIGN_CHAPTER.read_text(encoding="utf-8"))
    index = (BOOK / "arithmetic-library" / "index.md").read_text(encoding="utf-8")
    campaign = _load(
        BOOK / "_static" / "constructive-grand-campaign" / "campaign.json"
    )

    assert campaign["meta"]["goal_count"] == 120
    assert campaign["meta"]["tool_count"] == 16
    assert campaign["meta"]["anchor_count"] == 8
    assert len(campaign["families"]) == 12
    assert campaign["meta"]["current_alpha_version"] == "v27"
    assert campaign["meta"]["current_alpha_checked_use_count"] == 2560
    assert len(campaign["definitions"]) == 290
    assert sum(len(node["deps"]) for node in campaign["nodes"]) == 308

    for exact in (
        "**120 major mathematical goals**",
        "**16 reusable constructive tools**",
        "**8 established proof anchors**",
        "**290 pieces of mathematical vocabulary**",
        "**2,560 independently checked",
        "**8,196 checked proof dependencies**",
        "**406 definition-to-definition edges**",
        "**313 statement-lexical",
        "**213 separately typed, explicitly declared",
        "**526 milestone-to-notation edges**",
        "**198 genuinely shared conservative registry definitions**",
        "**388 reviewed dependency edges**",
        "**201 signature-compatible links**",
        "A research map is not a proof certificate",
        "future-facing entries remain planning vocabulary",
    ):
        assert exact in chapter

    for domain in ("D01", "D02", "D03", "D04", "D05"):
        assert f"?view=domain&focus={domain}" in chapter
    for family in ("F02", "F03", "F04", "F05", "F07", "F08"):
        assert f"?view=family&focus={family}" in chapter
    for goal in (
        "T12", "T13", "G012", "G023", "G024", "G025", "G026", "G043",
        "G045", "G047", "G048", "G061", "G063", "G065", "G071",
        "G077", "G078", "G101", "G102", "G107", "G120",
    ):
        assert f"?view=goal&focus={goal}" in chapter

    nodes = {node["id"]: node for node in campaign["nodes"]}
    for open_goal in ("G045", "G047", "G048", "G063", "G065", "G120", "G006", "G072", "G091"):
        assert nodes[open_goal]["status"] == "open"
    _assert_closed_matrix_and_algorithm_scopes(nodes)
    for closed_goal in ("T12", "G011", "G012", "G023", "G024", "G025", "G026", "G027", "G035",
                        "G043", "G051", "G061", "G071", "G077", "G078", "G095", "G107"):
        assert nodes[closed_goal]["status"] == "alpha_closed"

    assert "<grand-campaign-atlas>" in index
    assert "<next-layer-campaign>" in index
    assert "<advanced-layer-campaign>" in index
    assert "<transport-layer-campaign>" in index
    assert 'title="Interactive multiscale constructive number-theory research atlas"' in chapter


def test_next_layer_book_chapter_matches_exact_checked_release_and_open_boundary() -> None:
    chapter = NEXT_LAYER_CHAPTER.read_text(encoding="utf-8")
    campaign = _load(
        BOOK / "_static" / "constructive-grand-campaign" / "campaign.json"
    )
    definitions = _load(
        BOOK / "_static" / "constructive-grand-campaign" / "definitions.json"
    )
    catalog = _load(REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v20.json")

    assert catalog["theorem_count"] == 1776
    assert catalog["checked_use_count"] == 1776
    assert catalog["edge_count"] == 5882
    assert catalog["evidence_counts"] == {"alpha_closed": 1344, "stable_closed": 432}
    assert catalog["frontier_v20_campaign_counts"] == {
        "polynomial_horner": 7,
        "matrix_dot_product": 10,
        "bertrand_prime": 13,
        "continued_fraction": 9,
    }
    _assert_current_definition_counts(definitions)

    for exact in (
        "**39 new independently checked theorems**",
        "**1,776 checked-use entries**",
        "**5,882 actual theorem",
        "T13 is not closed",
        "milestone remained\nexplicitly **open**",
        "**132 mathematical definitions**",
        "**71 definition-to-definition prerequisites**",
        "**311 actual lexical theorem-to-notation uses**",
        "**31 explicitly declared typed references**",
        "**79 conservative\nfirst-order definitions**",
        "**123 exact reviewed prerequisite edges**",
        "**40 signature-compatible blueprint definitions**",
        "**590 complete proof bodies**",
        "independently compiled Lean proof",
        "1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069",
        "8f86225cc560d7b59ff665e58594ac6249c12dbb5cdfe47ae2708a0e497c86ce",
    ):
        assert exact in chapter

    for name, identifier in (
        ("Horner", "ND0002"),
        ("MatrixAt", "ND0003"),
        ("DotProduct", "ND0004"),
        ("SignedDet2", "ND0005"),
        ("BertrandWindow", "ND0006"),
        ("PowerValuationOne", "ND0007"),
        ("BertrandChain", "ND0008"),
        ("ContinuedFraction", "ND0011"),
    ):
        assert name in chapter
        assert f"`{identifier}`" in chapter

    for name, tag in (
        ("beta_horner_eval_exists", "PH0002"),
        ("beta_dot_product_exists_unique", "MD0006"),
        ("central_binom_prime_divisor_multiplicity_one_exists", "BP0007"),
        ("iterated_bertrand_prime_chain_exists", "BP000D"),
        ("continued_fraction_positive_exists", "CF0009"),
    ):
        assert f"`{name}`" in chapter
        assert f"/tag/{tag}.html" in chapter

    assert campaign["ambitious_boundaries"]["alpha_v20_edition"]["theorem_count"] == 1776
    assert campaign["ambitious_boundaries"]["next_layer_evidence_transition"][
        "independent_lean_bundle_verified"
    ] is True


def test_advanced_layer_book_chapter_binds_exact_v21_proofs_definitions_and_open_goals() -> None:
    chapter = ADVANCED_LAYER_CHAPTER.read_text(encoding="utf-8")
    campaign = _load(BOOK / "_static/constructive-grand-campaign/campaign.json")
    definitions = _load(BOOK / "_static/constructive-grand-campaign/definitions.json")
    catalog = _load(REPO / "artifacts/peano-library/alpha/catalog-v21.json")

    assert catalog["theorem_count"] == catalog["checked_use_count"] == 1830
    assert (catalog["edge_count"], catalog["layer_count"]) == (5986, 53)
    assert catalog["evidence_counts"] == {
        "alpha_closed": 1398,
        "stable_closed": 432,
    }
    assert catalog["frontier_v21_campaign_counts"] == {
        "matrix_coded_product": 23,
        "euclidean_complexity": 15,
        "binary_modular_exponentiation": 16,
    }
    promotion = catalog["alpha_v21_advanced_layer_promotion"]
    bundle = promotion["proof_bundle"]
    assert promotion["independent_lean_bundle_verified"] is True
    assert bundle["independent_lean_bundle_verified"] is True
    assert (
        bundle["node_count"],
        bundle["dependency_edges"],
        bundle["body_proof_nodes"],
        bundle["artifact_bytes"],
        len(bundle["root_names"]),
    ) == (209, 491, 10304, 1005317, 27)

    for exact in (
        "**54 new independently\nchecked constructive theorems**",
        "**1,830\nchecked-use entries**",
        "**5,986 checked theorem dependencies**",
        "**432 unchanged Stable theorems**",
        "**1,398\nAlpha-only theorems**",
        "**33 independently available components**",
        "T13 remains open",
        "**G101 is completely closed**",
        "**G102 is completely closed**",
        "**132 blueprint vocabulary entries**",
        "**71\nblueprint definition dependencies**",
        "**79 independently\nexpansion-audited definitions**",
        "**123 reviewed definition prerequisite\nedges**",
        "**40 signature-compatible blueprint definitions**",
        "**36 exact-name matches**",
        "**four explicitly reviewed\naliases**",
        "**209 independently checked\nproof bodies**",
        "**491 proof-dependency edges**",
        "**10,304 structural\nbody-proof nodes**",
        "steps <= 3 * BitLen(e) + 2",
        "1,005,317",
        "65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0",
        "84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1",
        "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98",
        "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6",
        "9d217af3e7f77f8beb436f627a44f1a29cda54bb08a4e666899803aa97ccb91b",
    ):
        assert exact in chapter

    for name, tag, route in (
        ("beta_matrix_product_exists", "MC000B", "matrix-coded-products"),
        ("beta_signed_matrix_product_exists", "MC000E", "matrix-coded-products"),
        ("signed_matrix_three_full_determinant_exists", "MC0016", "matrix-coded-products"),
        ("euclidean_two_step_halving", "EC0006", "euclidean-complexity"),
        ("euclidean_gcd_execution_linear_bound", "EC000F", "euclidean-complexity"),
        (
            "binary_modular_exponentiation_result_exists_unique",
            "BX0010",
            "binary-modular-exponentiation",
        ),
    ):
        assert f"`{name}` (`{tag}`)" in chapter
        assert f"/{route}/explorer/defined/tag/{tag}.html" in chapter
        assert (
            BOOK
            / "_static/constructive-advanced-layer-explorer"
            / route
            / "explorer/defined/tag"
            / f"{tag}.html"
        ).is_file()

    by_id = {item["id"]: item for item in definitions["reviewed_definitions"]}
    for identifier in (f"ND{index:04d}" for index in range(12, 28)):
        definition = by_id[identifier]
        assert f"`{identifier}`" in chapter
        assert f"`{definition['name']}`" in chapter
    assert len([item for item in by_id if "ND0012" <= item <= "ND0027"]) == 16

    nodes = {node["id"]: node for node in campaign["nodes"]}
    _assert_closed_matrix_and_algorithm_scopes(nodes)

    for goal in ("T13", "G101", "G102", "G051", "G095", "G027", "G035", "G107"):
        assert goal in chapter


def test_transport_layer_book_chapter_binds_exact_v22_proofs_definitions_and_honest_gaps() -> None:
    chapter = TRANSPORT_LAYER_CHAPTER.read_text(encoding="utf-8")
    campaign = _load(BOOK / "_static/constructive-grand-campaign/campaign.json")
    definitions = _load(BOOK / "_static/constructive-grand-campaign/definitions.json")
    catalog = _load(REPO / "artifacts/peano-library/alpha/catalog-v22.json")

    assert catalog["theorem_count"] == catalog["checked_use_count"] == 1890
    assert (catalog["edge_count"], catalog["layer_count"]) == (6128, 53)
    assert catalog["evidence_counts"] == {
        "alpha_closed": 1458,
        "stable_closed": 432,
    }
    assert catalog["frontier_v22_campaign_counts"] == {
        "binary_length": 21,
        "euclidean_gcd_transport": 20,
        "binary_modular_execution": 19,
    }
    assert catalog["parent_alpha_v21"]["theorem_count"] == 1830
    promotion = catalog["alpha_v22_transport_layer_promotion"]
    bundle = promotion["proof_bundle"]
    assert promotion["independent_lean_bundle_verified"] is True
    assert bundle["independent_lean_bundle_verified"] is True
    assert (
        bundle["node_count"],
        bundle["dependency_edges"],
        bundle["body_proof_nodes"],
        bundle["artifact_bytes"],
        bundle["bundle_root_id"],
        len(bundle["root_names"]),
    ) == (240, 597, 11848, 1099541, 239, 17)
    artifact = REPO / bundle["artifact_path"]
    artifact_bytes = artifact.read_bytes()
    assert len(artifact_bytes) == 1099541
    assert hashlib.sha256(artifact_bytes).hexdigest() == (
        "95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938"
    )

    for exact in (
        "**Alpha v22**",
        "**1,830-theorem Alpha-v21",
        "**60 new independently checked theorems**",
        "**1,890 enrolled theorems**",
        "**432 unchanged",
        "**1,458 Alpha-only**",
        "**6,128 exact proof-dependency edges**",
        "**53 dependency-first layers**",
        "**141 blueprint terms**",
        "**88 definition-to-definition prerequisites**",
        "**311 lexical statement",
        "**41 separately declared notation references**",
        "**352 total",
        "**89 reviewed conservative",
        "**142 exact reviewed definition edges**",
        "**50 compatible",
        "**57 exact\nnames**",
        "**four explicitly reviewed",
        "**239 real theorem",
        "**597 exact proof edges**",
        "**11,848 structural proof nodes**",
        "**1,099,541 bytes**",
        "**240 proof bodies**",
        "k <= 2*BitLen(b)+1",
        "G101",
        "G102",
        "T13",
        "95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938",
        "fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22",
        "431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea",
        "2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db",
    ):
        assert exact in chapter

    for name in (
        "binary_length_exists",
        "binary_length_functional",
        "binary_length_exists_unique",
        "binary_length_power_exact",
        "euclidean_trace_prefix_gcd_invariant",
        "euclidean_execution_terminal_identified",
        "euclidean_anchored_execution_linear_bound",
        "binary_execution_prefix_exists",
        "binary_modular_execution_exists",
        "binary_modular_execution_power_correct",
        "binary_modular_execution_horner_exists",
        "binary_modular_execution_result_exists_unique",
    ):
        assert name in chapter

    _assert_current_definition_counts(definitions)
    by_id = {item["id"]: item for item in definitions["reviewed_definitions"]}
    for identifier in (f"ND{index:04d}" for index in range(28, 38)):
        definition = by_id[identifier]
        assert f"`{identifier}`" in chapter
        assert f"`{definition['name']}`" in chapter
    assert by_id["ND0030"]["dependencies"] == ["PowTwo", "Le", "Lt"]
    assert by_id["ND0033"]["dependencies"] == [
        "ContinuedFractionTrace",
        "EuclideanStateAt",
        "IsGCD",
    ]

    nodes = {node["id"]: node for node in campaign["nodes"]}
    _assert_closed_matrix_and_algorithm_scopes(nodes)


def test_alpha_k3b_book_chapter_and_sparse_graph_match_the_sealed_receipt() -> None:
    chapter = K3B_CHAPTER.read_text(encoding="utf-8")
    site = (K3B_SITE / "index.html").read_text(encoding="utf-8")
    css = (K3B_SITE / "assets" / "k3b.css").read_text(encoding="utf-8")
    javascript = (K3B_SITE / "assets" / "k3b.js").read_text(encoding="utf-8")
    receipt_bytes = K3B_RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)

    assert hashlib.sha256(receipt_bytes).hexdigest() == (
        "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8"
    )
    assert len(receipt_bytes) == 10_550
    assert receipt["status"] == "passed"
    assert receipt["passes"] == 2
    assert receipt["deterministic_across_passes"] is True
    assert receipt["provenance"] == {
        "local_commit": "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
        "local_dirty": False,
        "payload_sha256": (
            "78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835"
        ),
    }
    assert all(row["dne_objects"] == 0 for row in receipt["results"].values())

    for exact in (
        "WMI job **219217**",
        "**Alpha-only**",
        "**closed checked**",
        "legacy evidence spelling\n`closed_checked_candidate`",
        "432-theorem Stable checked-use registry",
        "95,253",
        "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8",
        "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
        "78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835",
        "make ha-k3b-list-lookup-check",
    ):
        assert exact in chapter
    for name in receipt["selected_theorems"]:
        assert f"`{name}`" in chapter

    match = re.search(
        r'<script id="k3b-graph-data" type="application/json">\s*(\{.*?\})\s*</script>',
        site,
        flags=re.DOTALL,
    )
    assert match is not None
    graph = json.loads(match.group(1))
    assert graph["schema"] == "peano-k3b-book-graph-v2"
    assert graph["orientation"] == "dependency_to_dependent"
    assert graph["default_focus"] == "cell_list_extensional"
    assert graph["receipt"] == {
        "artifact": "ha-k3b-listat-full-closure-219217.json",
        "artifact_commit": "51f6e081a4aa1223bcdff7ff3ff0a662de8f9b08",
        "artifact_sha256": (
            "c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8"
        ),
        "job_id": "219217",
        "source_commit": "cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e",
    }

    nodes = graph["nodes"]
    by_id = {node["id"]: node for node in nodes}
    assert len(by_id) == len(nodes) == 41
    assert collections.Counter(node["kind"] for node in nodes) == {
        "definition": 7,
        "stable": 12,
        "alpha": 22,
    }
    assert collections.Counter(node["release"] for node in nodes) == {
        "presentation": 7,
        "stable": 12,
        "alpha_only": 22,
    }
    assert collections.Counter(node["evidence"] for node in nodes) == {
        "conservative_definition": 7,
        "closed_checked": 34,
    }
    assert all("status" not in node for node in nodes)
    assert all(not node["id"].startswith(("PA", "PD")) for node in nodes)
    assert all("tag" not in node for node in nodes)

    edge_keys = [(edge["source"], edge["target"], edge["kind"]) for edge in graph["edges"]]
    assert len(edge_keys) == len(set(edge_keys))
    assert {edge["kind"] for edge in graph["edges"]} == {"proof", "notation"}
    assert all(edge["source"] in by_id and edge["target"] in by_id for edge in graph["edges"])

    for name in receipt["selected_theorems"]:
        node = by_id[name]
        closed = receipt["results"][name]
        assert node["release"] == "alpha_only"
        assert node["evidence"] == "closed_checked"
        assert node["metrics"] == {
            "nodes": closed["proof_nodes"],
            "depth": closed["proof_depth"],
            "objects": closed["proof_objects"],
            "edges": closed["proof_edges"],
            "reused": closed["reused_objects"],
            "cuts": closed["cuts"],
        }
        proof_dependencies = [
            edge["source"]
            for edge in graph["edges"]
            if edge["kind"] == "proof" and edge["target"] == name
        ]
        assert proof_dependencies == closed["direct_dependencies"]
        source = REPO / node["source_path"]
        audit = REPO / node["test_path"]
        assert source.is_file() and audit.is_file()
        assert node["source_line"] <= len(source.read_text(encoding="utf-8").splitlines())
        assert node["test_line"] <= len(audit.read_text(encoding="utf-8").splitlines())

    for node in nodes:
        if node["kind"] == "stable":
            assert (K3B_SITE / node["href"]).resolve().is_file()
        elif node["href"].startswith("../../../arithmetic-library/"):
            fragment = node["href"].split("#", 1)[1]
            assert f'id="{fragment}"' in chapter

    local_assets = re.findall(
        r'<(?:link|script)\b[^>]*(?:href|src)="([^"]+)"', site
    )
    assert local_assets == ["assets/k3b.css", "assets/k3b.js"]
    assert all((K3B_SITE / relative).is_file() for relative in local_assets)
    assert "https://" not in site
    assert "http://" not in site
    assert "fetch(" not in javascript
    assert "innerHTML" not in javascript
    assert "immediateIds" in javascript
    assert 'viewControl.value === "all"' in javascript
    assert 'edgeControl.value === "none"' in javascript
    assert "body.k3b-site .k3b-node-definition polygon" in css
    assert "body.k3b-site .k3b-node-alpha rect" in css
    assert "body.k3b-site .k3b-node-stable rect" in css
    assert 'var order = { definition: 0, stable: 1, alpha: 2 }' in javascript
    assert 'appendPair(metrics, "Release", node.release)' in javascript
    assert 'appendPair(metrics, "Evidence", node.evidence)' in javascript
    assert "prefers-reduced-motion" in css

    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    assert toc.index("- file: arithmetic-library/strict-ha-campaign") < toc.index(
        "- file: arithmetic-library/cell-history-and-lookup"
    ) < toc.index("- file: arithmetic-library/primes-and-factorization")
    assert toc.index("- file: arithmetic-library/index") < toc.index(
        "- file: arithmetic-library/library-editions"
    ) < toc.index("- file: arithmetic-library/guided-tour")
    assert "<cell-history-and-lookup>" in (
        BOOK / "arithmetic-library" / "index.md"
    ).read_text(encoding="utf-8")
    assert "<cell-history-and-lookup>" in (
        BOOK / "arithmetic-library" / "strict-ha-campaign.md"
    ).read_text(encoding="utf-8")


def test_alpha_and_stable_book_page_records_the_canonical_channel_contract() -> None:
    source = LIBRARY_EDITIONS.read_text(encoding="utf-8")
    bertrand = BERTRAND_CAMPAIGN.read_text(encoding="utf-8")
    index = (BOOK / "arithmetic-library" / "index.md").read_text(encoding="utf-8")
    artifacts = (REPO / "artifacts" / "README.md").read_text(encoding="utf-8")
    normalized_artifacts = " ".join(artifacts.split())
    proof_explorer = (
        BOOK / "arithmetic-library" / "proof-explorer.md"
    ).read_text(encoding="utf-8")
    normalized_proof_explorer = " ".join(proof_explorer.split())

    for exact in (
        "# Alpha and Stable library editions",
        "**885** theorems",
        "**902** theorems",
        "**923** theorems",
        "**965** theorems",
        "**972** theorems",
        "**993** theorems",
        "**1,017** theorems",
        "**1,055** theorems",
        "**1,076** theorems",
        "**1,085** theorems",
        "**1,123** theorems",
        "**1,303** theorems",
        "**1,543** theorems",
        "**1,556** theorems",
        "**1,673** theorems",
        "**1,737** theorems",
        "**1,776** theorems",
        "**1,830** theorems",
        "**1,890** theorems",
        "**570** theorems",
        "**885** theorems",
        "**916** theorems",
        "**1,589** theorems",
        "**2,641** edges / **45** layers",
        "**2,730** edges / **45** layers",
        "**2,891** edges / **45** layers",
        "**2,912** edges / **45** layers",
        "**3,072** edges / **45** layers",
        "**3,224** edges / **45** layers",
        "**3,276** edges / **45** layers",
        "**3,306** edges / **45** layers",
        "**3,482** edges / **45** layers",
        "**4,302** edges / **45** layers",
        "**5,615** edges / **53** layers",
        "**5,779** edges / **53** layers",
        "**5,882** edges / **53** layers",
        "**5,986** edges / **53** layers",
        "**6,128** edges / **53** layers",
        "432 Stable plus 453 Alpha-only rows",
        "432 Stable plus 491 Alpha-only rows",
        "432 Stable plus 533 Alpha-only rows",
        "432 Stable plus 540 Alpha-only rows",
        "432 Stable plus 561 Alpha-only rows",
        "432 Stable plus 585 Alpha-only rows",
        "432 Stable plus 623 Alpha-only rows",
        "432 Stable plus 644 Alpha-only rows",
        "432 Stable plus 653 Alpha-only rows",
        "432 Stable plus 691 Alpha-only rows",
        "432 Stable plus 871 Alpha-only rows",
        "314 `body_checked`",
        "352 `body_checked`",
        "394 `body_checked`",
        "401 `body_checked`",
        "446 `body_checked`",
        "484 `body_checked`",
        "505 `body_checked`",
        "514 `body_checked`",
        "552 `body_checked`",
        "732 `body_checked`",
        "one `pending_layered_closure`",
        'edition("alpha").checked_specs',
        "from peano_lab.library.editions_v27 import edition, entry, replay",
        "# 2560",
        'entry("cell_list_extensional", edition="alpha")',
        'replay("signed_decode_nonnegative_constructor", edition="alpha")',
        'entry("quadratic_reciprocity_combined", edition="alpha")',
        'entry("linear_congruence_solvable_iff_gcd_divides", edition="alpha")',
        'entry("prime_is_two_squares_iff_two_or_one_mod_four", edition="alpha")',
        'entry("infinitely_many_primes_one_mod_four", edition="alpha")',
        'entry("beta_horner_eval_exists", edition="alpha")',
        'entry("beta_dot_product_exists_unique", edition="alpha")',
        'entry("central_binom_prime_divisor_multiplicity_one_exists", edition="alpha")',
        'entry("iterated_bertrand_prime_chain_exists", edition="alpha")',
        'entry("continued_fraction_positive_exists", edition="alpha")',
        'entry("beta_matrix_product_exists", edition="alpha")',
        'entry("beta_signed_matrix_product_exists", edition="alpha")',
        'entry("signed_matrix_three_full_determinant_exists", edition="alpha")',
        'entry("euclidean_two_step_halving", edition="alpha")',
        'entry("euclidean_gcd_execution_linear_bound", edition="alpha")',
        'entry("binary_modular_exponentiation_result_exists_unique", edition="alpha")',
        'entry("binary_length_exists_unique", edition="alpha")',
        'entry("euclidean_execution_terminal_identified", edition="alpha")',
        'entry("euclidean_anchored_execution_linear_bound", edition="alpha")',
        'entry("binary_modular_execution_power_correct", edition="alpha")',
        'entry("binary_modular_execution_result_exists_unique", edition="alpha")',
        "95,253 proof nodes",
        "artifacts/peano-library/alpha/catalog-v1.json",
        "artifacts/peano-library/channels.json",
        "artifacts/peano-library/channels-v3.json",
        "artifacts/peano-library/channels-v4.json",
        "artifacts/peano-library/channels-v5.json",
        "artifacts/peano-library/channels-v7.json",
        "artifacts/peano-library/alpha/catalog-v8.json",
        "artifacts/peano-library/alpha/metrics-v8.json",
        "artifacts/peano-library/alpha/dependency-graph-v8.mmd",
        "artifacts/peano-library/channels-v8.json",
        "artifacts/peano-library/alpha/catalog-v9.json",
        "artifacts/peano-library/alpha/metrics-v9.json",
        "artifacts/peano-library/alpha/dependency-graph-v9.mmd",
        "artifacts/peano-library/channels-v9.json",
        "artifacts/peano-library/alpha/catalog-v10.json",
        "artifacts/peano-library/alpha/metrics-v10.json",
        "artifacts/peano-library/alpha/dependency-graph-v10.mmd",
        "artifacts/peano-library/channels-v10.json",
        "artifacts/peano-library/alpha/catalog-v11.json",
        "artifacts/peano-library/alpha/metrics-v11.json",
        "artifacts/peano-library/alpha/dependency-graph-v11.mmd",
        "artifacts/peano-library/channels-v11.json",
        "artifacts/peano-library/alpha/catalog-v12.json",
        "artifacts/peano-library/alpha/metrics-v12.json",
        "artifacts/peano-library/alpha/dependency-graph-v12.mmd",
        "artifacts/peano-library/channels-v12.json",
        "artifacts/peano-library/channels-v16.json",
        "artifacts/peano-library/channels-v17.json",
        "artifacts/peano-library/channels-v18.json",
        "artifacts/peano-library/channels-v19.json",
        "artifacts/peano-library/channels-v20.json",
        "artifacts/peano-library/channels-v21.json",
        "artifacts/peano-library/channels-v22.json",
        "3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10",
        "db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4",
        "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66",
        "1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795",
        "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7",
        "627f651198360aa95b8efd085b98f694d88c883434309f6050a819bc249c90c4",
        "947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c",
        "ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b",
        "fd76c648de26cd8a451244441fac8f423fb4fec8e7feac1c789404dafcda1563",
        "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98",
        "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6",
        "9d217af3e7f77f8beb436f627a44f1a29cda54bb08a4e666899803aa97ccb91b",
        "84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1",
        "431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea",
        "2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db",
        "897ac1893550881538cf74274d0d48e15450125776f31be4edc10de0b1d05ef6",
        "fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22",
        "95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938",
        "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c",
        "9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff",
        "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2",
        "2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123",
        "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f",
        "b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80",
        "762d1310c41ed92da066701cf7529551324b09f7b501c5a29c530f443afeb998",
        "4c87c40b5a260d67b5582447cfabb7e3ce62e80303aa4f4d33b1b952995ec356",
        "108593843459a69d81c333305a50b5368294c3c722437f425b92c942391fe9be",
        "edfb0eacecbd9419b1b303098915e28e45643379b65ab7d807ffcd4d7bd4b3e7",
        "61f33ba9e49219ff4a199d082722d9582ac6d87f825851173ac7fdb6931bb52d",
        "1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab",
        "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f",
        "1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d",
        "6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46",
        "01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013",
        "a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a",
        "f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e",
        "446f6c9d07c3f9e22fa0fbb41a46c95d27804a088d708b13aea0ddd7159c45dd",
        "fdac645cbc070b5a1cdfe71b19e98afe095a183d4cfa0ad4256fa42857ca736c",
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36",
        "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3",
        "4a1f4302b0a4ede3bf5123ec021b4f2f5f98c2a7e22eadc6f13a446422ad9450",
        "2f0be30e7de93bcf89235700c419f46656cb638be85ca153154684845e8dabdb",
        "b82b567e59cabeda6f90fdfedaceb628ca2e7c4b7423be643b8f22865e7599bd",
        "ecce457947650ae7ddf2a638d8b1f2c8757daea6a95ea9c927ebaef3995d4ccd",
        "cf5d550d5a3aa4af1debf9268eca578c30ca408058dcdeb35892bc705287214e",
        "6c314d36cd7bb1e6cb5b213fec9bf9e04ab118e84121830b00c885ede2abac2a",
        "c72d6e1234aa6521b0c524720cd64912f7e9b0bc58f31b6964bbb1a99c5a071d",
        "7676fc944b695d02a3aec05b428c012933258cb6cd9b465599318e690e0f6df4",
        "c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370",
        "90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813",
        "ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008",
        "dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d",
        "74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda",
        "7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65",
        "03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9",
        "77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34",
        "46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3",
        "63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de",
        "fdee73e6ea045c90afb7c024e8a209fbea8b03189538611c93678e4fa923aa76",
        "644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2",
        "d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c",
        "92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300",
        "c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1",
        "039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f",
        "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b",
        "bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061",
        "362da94c3c5e788f296f315b86b5d63534c1567ce00911dbb27227a66ab50e28",
        "726c6134461dace943f909a0073ca0a6cae95a54ff306f8aeefeb3d9a5151926",
        "de8a6a57b828c2b3893c6fb31f2611d5180f8de4d1002a21a681739616b761b5",
        "7ad0c942a2239532696f5d99ee1dc985e13302cf73b4637497b879871d05752c",
        "ee9494f8dfb9e4070a2ce3d2d740b312d147948dcd296ac0da7ed059c9944e50",
        "df0e5cb8402483360f8381c76c7ce6ed6c70245df45556107c40652d00beb0da",
        "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109",
        "64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4",
        "583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8",
        "0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982",
        "RFC HA-R6-BERTRAND-CB-1",
        "Primorial foundation RFC",
        "Primorial membership RFC",
        "Primorial interval-split RFC",
        "Bertrand campaign chapter",
        "direct neighborhood",
    ):
        assert exact in source
    for exact in (
        "<library-editions>",
        "<strong>2,560</strong><span>Alpha v27 theorems</span>",
        "<strong>2,560</strong><span>Alpha checked-use rows</span>",
        "<strong>2,128</strong><span>Alpha-only rows</span>",
        "2,560 theorems, 8,196 direct edges",
        "1,303 theorems, 4,302 direct",
        "732 `body_checked`",
        "dependency-closed B6 support and B5--BP02 completion chain",
    ):
        assert exact in index
    assert "241 Stable prerequisites" in normalized_proof_explorer
    assert "316 Alpha-only specifications" in normalized_proof_explorer
    assert "748" in normalized_proof_explorer
    for exact in (
        "## Current Alpha v12 layer",
        "| Alpha v12 specifications | 1,303 |",
        "| `FactorialVal` rows | 7 |",
        "8 + 5 + 5 + 3",
        "3 + 5 + 4 + 2 + 5 + 3 + 2",
        "24 + 14",
        "10 + 11",
        "## Alpha v6 threshold, finite-sum, and bridge layer",
        "## Alpha v7 recurrence, equality, and $H/J$ layer",
        "## Alpha v8 recurrence-defined Choose and central lower bound",
        "## Alpha v9 Primorial foundation and membership",
        "## Alpha v10 Primorial interval splitting",
        "## Alpha v11 B4 capstone and B5 prime support",
        "## Alpha v12 complete Bertrand proof",
        "B3 Choose/CentralBinom [Alpha v8 body evidence]",
        (
            "B4 Primorial [Alpha v11 body evidence; bound closed; "
            "depends on B3]"
        ),
        "eight-row threshold tranche",
        "five-row finite Legendre-sum interface",
        "does **not** yet prove",
        "relational-power bridge",
        "`05cb3ff`",
        "`f35b8ed`",
        "`4df44c9`",
        "`85625d6`",
        "`bb24543`",
        "`2f41a97`",
        "`5b9433a`",
        "`b2035ce`",
        "`5b189f0`",
        "`70c5b16`",
        "`de58034`",
        "`985a773`",
        "`158d87c`",
        "`00e8361`",
        "`874e81e`",
        "`d1cbe16`",
        "`8ea03f2`",
        "`d1ad971`",
        "`d46e513`--`74dc219`",
        "prime_factorial_valuation_eq_legendre_sum",
        "four_pow_lt_mul_central_binom",
        "RFC HA-R6-BERTRAND-CB-1",
        "c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89",
        "4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5",
        "1a9bac74069a495d6ce17b906f46821731d6fad4e97d07e7272cf57da72593ab",
        "`dfb2673`",
        "`b0bc5de`",
        "`c45d68a`",
        "`5eef9a5`--`7539b44`",
        "`56ecb02`",
        "make peano-library-alpha-v12-check",
        "complete Bertrand proof explorer",
        "BT0127",
    ):
        assert exact in bertrand
    for exact in (
        "## Peano Alpha v7 — Bertrand recurrence, equality, and transport",
        "[`peano-library/channels-v7.json`](peano-library/channels-v7.json)",
        "1,017 theorem specifications, 3,072 declared direct edges",
        "aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c",
        "prime_factorial_valuation_eq_legendre_sum",
        "make peano-library-alpha-v7-check",
    ):
        assert exact in artifacts
    assert "all twenty-four additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v8 — Choose and central-binomial lower bound",
        "[`peano-library/channels-v8.json`](peano-library/channels-v8.json)",
        "1,055 theorem specifications, 3,224 declared direct edges",
        "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2",
        "four_pow_lt_mul_central_binom",
        "RFC HA-R6-BERTRAND-CB-1",
        "make peano-library-alpha-v8-check",
    ):
        assert exact in artifacts
    assert "all thirty-eight additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v12 — complete Bertrand proof",
        "[`peano-library/channels-v12.json`](peano-library/channels-v12.json)",
        "1,303 theorem specifications, 4,302 declared direct edges",
        "f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b",
        "bertrand_closed_upper",
        "bertrand_strict",
        "make peano-library-alpha-v12-check",
    ):
        assert exact in artifacts
    assert "all 180 additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v9 — Primorial foundation and membership",
        "[`peano-library/channels-v9.json`](peano-library/channels-v9.json)",
        "1,076 theorem specifications, 3,276 declared direct edges",
        "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f",
        "primorial_le_four_pow",
        "Primorial foundation RFC",
        "Primorial membership RFC",
        "make peano-library-alpha-v9-check",
    ):
        assert exact in artifacts
    assert "all twenty-one additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v10 — Primorial interval splitting",
        "[`peano-library/channels-v10.json`](peano-library/channels-v10.json)",
        "1,085 theorem specifications, 3,306 declared direct edges",
        "c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f",
        "Primorial interval-split RFC",
        "make peano-library-alpha-v10-check",
    ):
        assert exact in artifacts
    assert "all nine additions fail closed" in normalized_artifacts
    for exact in (
        "## Peano Alpha v11 — Primorial capstone and B5 support",
        "[`peano-library/channels-v11.json`](peano-library/channels-v11.json)",
        "1,123 theorem specifications, 3,482 declared direct edges",
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36",
        "primorial_le_four_pow",
        "make peano-library-alpha-v11-check",
    ):
        assert exact in artifacts
    assert "all thirty-eight additions fail closed" in normalized_artifacts


def test_generated_atlas_is_byte_current() -> None:
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_atlas_embeds_every_checked_statement_script_receipt_and_edge() -> None:
    snapshot = _load(SNAPSHOT)
    source = ATLAS.read_text(encoding="utf-8")
    cards = re.findall(
        r'<article class="pa-theorem-card" id="theorem-[^"]+".*?</article>',
        source,
        flags=re.DOTALL,
    )
    by_name: dict[str, str] = {}
    for card in cards:
        match = re.search(r'data-name="([^"]+)"', card)
        assert match is not None
        assert match.group(1) not in by_name
        by_name[match.group(1)] = card

    theorems = snapshot["theorems"]
    assert len(theorems) == snapshot["theorem_count"] == 432
    assert len(by_name) == 432
    assert sum(len(theorem["dependencies"]) for theorem in theorems) == 1_185

    for theorem in theorems:
        card = by_name[theorem["name"]]
        recipe = [f"pa prove {theorem['statement']}"]
        recipe.extend(f"use {name}" for name in theorem["dependencies"])
        recipe.extend(theorem["script"])
        recipe.append("qed")
        assert html.escape(theorem["statement"], quote=True) in card
        assert html.escape("\n".join(recipe), quote=True) in card
        assert theorem["certificate_sha256"] in card
        assert f"<dd>{theorem['proof_nodes']:,}</dd>" in card
        assert f"<dd>{theorem['distinct_proof_objects']:,}</dd>" in card
        assert f"<dd>{theorem['reused_proof_references']:,}</dd>" in card
        assert f"<dd>{theorem['proof_depth']}</dd>" in card
        assert f"<dd>{theorem['cut_nodes']:,}</dd>" in card
        for dependency in theorem["dependencies"]:
            assert f'href="#theorem-{dependency}"' in card

    assert source.count('data-status="blocked_by_language"') == 1
    assert "Bézout identity with integer coefficients" in source
    assert "This card deliberately contains no native proof script" in source


def test_research_domains_and_runtime_names_match_the_atlas_contract() -> None:
    snapshot_names = {
        theorem["name"] for theorem in _load(SNAPSHOT)["theorems"]
    }
    rows = _load(RESEARCH)["lemmas"]
    checked_names: set[str] = set()
    counts: collections.Counter[str] = collections.Counter()
    for row in rows:
        if row["status"] == "blocked_by_language":
            continue
        peano = row["peano"]
        name = peano.get("existing_name") or row["id"]
        assert name not in checked_names
        checked_names.add(name)
        counts[row["domain"]] += 1
    assert checked_names == snapshot_names
    assert dict(counts) == DOMAIN_COUNTS


def test_interaction_assets_are_local_progressive_and_auto_discovered_once() -> None:
    config = (BOOK / "_config.yml").read_text(encoding="utf-8")
    css = (BOOK / "_static" / "arithmetic-book.css").read_text(encoding="utf-8")
    js = (BOOK / "_static" / "arithmetic-book.js").read_text(encoding="utf-8")
    # Jupyter Book 1.x auto-discovers the local _static tree. Repeating these
    # Sphinx keys would load the same assets twice, but the files themselves
    # are a required, versioned part of the Book.
    assert "html_static_path" not in config
    assert "html_css_files" not in config
    assert "html_js_files" not in config
    assert (BOOK / "_static" / "arithmetic-book.css").is_file()
    assert (BOOK / "_static" / "arithmetic-book.js").is_file()
    assert (BOOK / "_static" / "pa-proof-explorer" / "assets" / "explorer.css").is_file()
    assert (BOOK / "_static" / "pa-proof-explorer" / "assets" / "explorer.js").is_file()
    assert "fetch(" not in js
    assert "innerHTML" not in js
    assert "prefers-reduced-motion" in css
    assert "@media print" in css
    atlas = ATLAS.read_text(encoding="utf-8")
    assert "```{raw} html\n<div class=\"pa-atlas\"" in atlas
    assert "</div>\n```\n\n## How to use this atlas" in atlas
    assert "data-pa-search" in atlas
    assert "data-pa-lab-command" not in atlas
    assert "Stable repository theorem; hosted-runtime deployment is a separate channel" in atlas
    assert "# The Stable theorem atlas" in atlas
    assert f"github.com/nasqret/vietnam2026/blob/{PROOF_SNAPSHOT_COMMIT}/" in atlas
    assert "github.com/nasqret/vietnam2026/blob/peano-lab/" not in atlas
    assert "data-pa-learning-route" in GUIDE.read_text(encoding="utf-8")
    for line in GUIDE.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("<"):
            assert "$" not in line, f"raw HTML contains unrendered TeX: {line}"
    assert "http://" not in css + js
    assert "https://" not in css + js


def test_guided_tour_sessions_replay_through_the_real_peano_driver() -> None:
    result = subprocess.run(
        [sys.executable, str(BOOK_GATE), str(GUIDE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all commands replay cleanly" in result.stdout
    assert "2 session blocks" in result.stdout


def test_arithmetic_narrative_does_not_reintroduce_the_pre_fta_blocker() -> None:
    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in (BOOK / "arithmetic-library").glob("*.md")
        if path.name != "theorem-atlas.md"
    }
    joined = "\n".join(texts.values())
    assert "native FTA is not yet proved" not in joined
    assert "The library does not yet have greatest-prime descent" not in joined
    assert "planned and expressible" not in joined
    assert "guided-tour" in (BOOK / "intro.md").read_text(encoding="utf-8")
    assert "theorem-atlas" in (BOOK / "peano" / "index.md").read_text(
        encoding="utf-8"
    )
