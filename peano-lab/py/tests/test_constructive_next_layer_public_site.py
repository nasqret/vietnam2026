"""End-to-end static publication contract for the complete Alpha-v23 proof site.

These bounded integration checks inspect only source HTML, small JSON surfaces,
streamed catalog bytes, file metadata, and ``make -n`` output.  They never
decode, reconstruct, replay, or kernel-check historical proof bundles.
"""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / "deploy" / "proofs" / "index.html"
ATLAS = ROOT / "book" / "_static" / "constructive-grand-campaign"
HISTORIC = ROOT / "book" / "_static" / "constructive-frontier-explorer"
NEXT = ROOT / "book" / "_static" / "constructive-next-layer-explorer"
ADVANCED = ROOT / "book" / "_static" / "constructive-advanced-layer-explorer"
TRANSPORT = ROOT / "book" / "_static" / "constructive-transport-layer-explorer"
MILESTONE = ROOT / "book" / "_static" / "constructive-milestone-closure-explorer"
CATALOG = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v23.json"
CHANNELS = ROOT / "artifacts" / "peano-library" / "channels-v23.json"
METRICS = ROOT / "artifacts" / "peano-library" / "alpha" / "metrics-v23.json"

CURRENT_REVISION = "818da349674b"
STALE_V19_REVISION = "f1c3d3fba013"
CURRENT_ALPHA_IDENTITY = (
    "02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85"
)
NEXT_BUNDLE = "alpha-v20-next-layer-proof-bundle-v1.json"
NEXT_RECEIPT = "alpha-v20-next-layer-closure-receipt.md"
NEXT_BUNDLE_SHA256 = (
    "1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069"
)
ADVANCED_BUNDLE = "alpha-v21-advanced-layer-proof-bundle-v1.json"
ADVANCED_RECEIPT = "alpha-v21-advanced-layer-closure-receipt.md"
ADVANCED_BUNDLE_SHA256 = (
    "65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0"
)
TRANSPORT_BUNDLE = "alpha-v22-transport-layer-proof-bundle-v1.json"
TRANSPORT_RECEIPT = "alpha-v22-transport-layer-closure-receipt.md"
TRANSPORT_BUNDLE_SHA256 = (
    "95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938"
)
MILESTONE_BUNDLE = "alpha-v23-milestone-closure-proof-bundle-v1.json"
MILESTONE_RECEIPT = "alpha-v23-milestone-closure-receipt.md"
MILESTONE_BUNDLE_SHA256 = (
    "cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11"
)

FLAGSHIP_ROUTES = ("quadratic-reciprocity", "bertrand-postulate")
HISTORIC_ROUTES = (
    "supplementary-laws",
    "kummer",
    "two-squares",
    "four-squares",
    "lucas",
    "pythagorean-fermat-four",
)
NEXT_FAMILIES = {
    "polynomial-horner": {
        "count": 7,
        "domain": "D04",
        "family": "F10",
        "roots": {"T12": ("PH0002", "beta_horner_eval_exists")},
        "definition": ("ND0002", "Horner"),
    },
    "matrix-dot-product": {
        "count": 10,
        "domain": "D05",
        "family": "F12",
        "roots": {"T13": ("MD0006", "beta_dot_product_exists_unique")},
        "definition": ("ND0004", "DotProduct"),
    },
    "bertrand-prime-chains": {
        "count": 13,
        "domain": "D02",
        "family": "F03",
        "roots": {
            "G023": (
                "BP0007",
                "central_binom_prime_divisor_multiplicity_one_exists",
            ),
            "G024": ("BP000D", "iterated_bertrand_prime_chain_exists"),
        },
        "definition": ("ND0008", "BertrandChain"),
    },
    "continued-fractions": {
        "count": 9,
        "domain": "D03",
        "family": "F08",
        "roots": {"G071": ("CF0009", "continued_fraction_positive_exists")},
        "definition": ("ND0011", "ContinuedFraction"),
    },
}
ADVANCED_FAMILIES = {
    "matrix-coded-products": {
        "count": 23,
        "goal": "T13",
        "root": ("MC000E", "beta_signed_matrix_product_exists"),
        "definition": ("ND0017", "SignedMatrixProduct"),
    },
    "euclidean-complexity": {
        "count": 15,
        "goal": "G101",
        "root": ("EC000F", "euclidean_gcd_execution_linear_bound"),
        "definition": ("ND0020", "EuclideanExecution"),
    },
    "binary-modular-exponentiation": {
        "count": 16,
        "goal": "G102",
        "root": ("BX0010", "binary_modular_exponentiation_result_exists_unique"),
        "definition": ("ND0027", "BinaryModularPower"),
    },
}
TRANSPORT_FAMILIES = {
    "binary-length": {
        "count": 21,
        "goal": "G102",
        "root": ("BL0014", "binary_length_exists_unique"),
        "definition": ("ND0030", "BitLen"),
    },
    "euclidean-gcd-transport": {
        "count": 20,
        "goal": "G101",
        "root": ("GT0010", "euclidean_execution_terminal_identified"),
        "definition": ("ND0033", "EuclideanAnchoredExecution"),
    },
    "binary-modular-execution": {
        "count": 19,
        "goal": "G102",
        "root": ("BE0013", "binary_modular_execution_result_exists_unique"),
        "definition": ("ND0036", "BinaryModularExecution"),
    },
}
MILESTONE_FAMILIES = {
    "euclidean-logarithmic-bound": {
        "count": 17,
        "goal": "G101",
        "root": ("EL0010", "euclidean_gcd_execution_logarithmic_bound"),
        "definition": ("ND0039", "EuclideanLogarithmicExecution"),
        "definition_count": 19,
        "proof_edge_count": 48,
    },
    "binary-digit-extraction": {
        "count": 24,
        "goal": "G102",
        "root": ("BD0018", "binary_modular_execution_logarithmic_bound"),
        "definition": ("ND0041", "BinaryCanonicalExponentDigitCode"),
        "definition_count": 25,
        "proof_edge_count": 63,
    },
    "primes-three-mod-four": {
        "count": 18,
        "goal": "G025",
        "root": ("TF0012", "infinitely_many_primes_three_mod_four"),
        "definition": ("ND0044", "PrimeThreeModFourDivisor"),
        "definition_count": 11,
        "proof_edge_count": 46,
    },
}
REVIEWED_NEXT_DEFINITIONS = {
    "Horner": ("ND0002", "polynomial-horner"),
    "MatrixAt": ("ND0003", "matrix-dot-product"),
    "DotProduct": ("ND0004", "matrix-dot-product"),
    "SignedDet2": ("ND0005", "matrix-dot-product"),
    "BertrandWindow": ("ND0006", "bertrand-prime-chains"),
    "PowerValuationOne": ("ND0007", "bertrand-prime-chains"),
    "BertrandChain": ("ND0008", "bertrand-prime-chains"),
    "ContinuedFraction": ("ND0011", "continued-fractions"),
    "ListCell": ("ND0009", "continued-fractions"),
    "ContinuedFractionTrace": ("ND0010", "continued-fractions"),
    "MatrixAffineSlice": ("ND0012", "matrix-coded-products"),
    "MatrixProductCell": ("ND0013", "matrix-coded-products"),
    "MatrixProductPrefix": ("ND0014", "matrix-coded-products"),
    "MatrixPointwiseAdd": ("ND0015", "matrix-coded-products"),
    "SignedDotProduct": ("ND0016", "matrix-coded-products"),
    "SignedMatrixProduct": ("ND0017", "matrix-coded-products"),
    "EuclideanDivision": ("ND0018", "euclidean-complexity"),
    "EuclideanHalving": ("ND0019", "euclidean-complexity"),
    "EuclideanExecution": ("ND0020", "euclidean-complexity"),
    "BinaryModulus": ("ND0021", "binary-modular-exponentiation"),
    "BinaryExponentSplit": ("ND0022", "binary-modular-exponentiation"),
    "CanonicalModularResidue": ("ND0023", "binary-modular-exponentiation"),
    "BinaryDoubledPower": ("ND0024", "binary-modular-exponentiation"),
    "BinaryOddPower": ("ND0025", "binary-modular-exponentiation"),
    "BinaryModularStep": ("ND0026", "binary-modular-exponentiation"),
    "BinaryModularPower": ("ND0027", "binary-modular-exponentiation"),
    "PowTwo": ("ND0028", "binary-length"),
    "BinaryDigit": ("ND0029", "binary-length"),
    "BitLen": ("ND0030", "binary-length"),
    "EuclideanCommonDivisor": ("ND0031", "euclidean-gcd-transport"),
    "EuclideanStateAt": ("ND0032", "euclidean-gcd-transport"),
    "EuclideanAnchoredExecution": ("ND0033", "euclidean-gcd-transport"),
    "BinaryDigitPrefix": ("ND0034", "binary-modular-execution"),
    "BinaryExecutionTrace": ("ND0035", "binary-modular-execution"),
    "BinaryModularExecution": ("ND0036", "binary-modular-execution"),
    "BinaryExecutionPowerInvariant": ("ND0037", "binary-modular-execution"),
    "EuclideanBoundedTrace": ("ND0038", "euclidean-logarithmic-bound"),
    "EuclideanLogarithmicExecution": ("ND0039", "euclidean-logarithmic-bound"),
    "BinaryExponentDigitCode": ("ND0040", "binary-digit-extraction"),
    "BinaryCanonicalExponentDigitCode": ("ND0041", "binary-digit-extraction"),
    "BinaryCompleteModularExecution": ("ND0042", "binary-digit-extraction"),
    "BinaryExecutionOperationCount": ("ND0043", "binary-digit-extraction"),
    "PrimeThreeModFourDivisor": ("ND0044", "primes-three-mod-four"),
    "EuclidThreeNumber": ("ND0045", "primes-three-mod-four"),
}


class _Document(HTMLParser):
    """Capture real rendered anchors and the atlas's inert JSON snapshot."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._inside_snapshot = False
        self.snapshot: list[str] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attributes}
        if tag == "a":
            self.links.append(values)
        if tag == "script" and values.get("id") == "campaign-data":
            self._inside_snapshot = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._inside_snapshot:
            self._inside_snapshot = False

    def handle_data(self, data: str) -> None:
        if self._inside_snapshot:
            self.snapshot.append(data)


def _document(path: Path) -> _Document:
    result = _Document()
    result.feed(path.read_text(encoding="utf-8"))
    return result


@lru_cache(maxsize=1)
def _catalog_digest() -> str:
    """Stream the 25 MiB catalog; never parse it or touch a proof bundle."""

    digest = sha256()
    with CATALOG.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _channels() -> dict:
    return json.loads(CHANNELS.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _campaign() -> dict:
    return json.loads((ATLAS / "campaign.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _global_definitions() -> dict:
    return json.loads((ATLAS / "definitions.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _manifest() -> dict:
    return json.loads((NEXT / "manifest.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _transport_manifest() -> dict:
    return json.loads((TRANSPORT / "manifest.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _milestone_manifest() -> dict:
    return json.loads((MILESTONE / "manifest.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _corpus(slug: str) -> dict:
    return json.loads((NEXT / slug / "api" / "corpus.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _staging_dry_run(target: str) -> str:
    return subprocess.run(
        ["make", "-n", target],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _revision(href: str) -> str | None:
    return parse_qs(urlsplit(href).query).get("v", [None])[0]


def test_current_alpha_and_immutable_stable_are_bound_to_actual_catalog_bytes() -> None:
    channels = _channels()
    alpha = channels["channels"]["alpha"]
    stable = channels["channels"]["stable"]
    digest = _catalog_digest()

    assert digest == alpha["artifact_sha256"]
    assert digest[:12] == CURRENT_REVISION
    assert alpha["artifact_path"] == "artifacts/peano-library/alpha/catalog-v23.json"
    assert alpha["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert alpha["theorem_count"] == alpha["checked_use_count"] == 1_949
    assert alpha["evidence_counts"] == {"alpha_closed": 1_517, "stable_closed": 432}
    assert alpha["alpha_v23_frontier_new_count"] == 59
    assert alpha["frontier_v23_campaign_counts"] == {
        "binary_digit_extraction": 24,
        "euclidean_logarithmic_bound": 17,
        "primes_three_mod_four": 18,
    }
    assert stable["theorem_count"] == stable["checked_use_count"] == 432
    assert channels["default_channel"] == "stable"


def test_public_hub_publishes_exactly_twenty_one_independently_versioned_family_routes() -> None:
    document = _document(HUB)
    links = [
        item
        for item in document.links
        if "primary-action" in item.get("class", "").split()
    ]
    family_links = {
        urlsplit(item["href"]).path.strip("/"): item
        for item in links
        if urlsplit(item["href"]).path.strip("/") != "grand-campaign"
    }
    assert set(family_links) == (
        set(FLAGSHIP_ROUTES)
        | set(HISTORIC_ROUTES)
        | set(NEXT_FAMILIES)
        | set(ADVANCED_FAMILIES)
        | set(TRANSPORT_FAMILIES)
        | set(MILESTONE_FAMILIES)
    )
    assert len(family_links) == 21
    assert all(_revision(item["href"]) == CURRENT_REVISION for item in family_links.values())

    atlas = next(
        item for item in links if urlsplit(item["href"]).path.strip("/") == "grand-campaign"
    )
    assert _revision(atlas["href"]) == CURRENT_REVISION


def test_public_hub_truthfully_identifies_v23_and_contains_no_stale_current_revision() -> None:
    source = HUB.read_text(encoding="utf-8")

    assert "Immutable Alpha v23" in source
    assert "All 1,949 theorems have checked-use authority" in source
    assert "432-theorem Stable edition remains unchanged" in source
    assert "Nineteen constructive proof campaigns" in source
    assert "152 structured first-order definitions" in source
    assert "97 reviewed conservative definitions" in source
    for milestone in ("G025", "G101", "G102"):
        assert f"Closed milestone {milestone}" in source
    assert "Immutable Alpha v19 independently closes" not in source
    assert "All 1,737 theorems have checked-use authority" not in source
    assert f"?v={STALE_V19_REVISION}" not in source
    assert f"&amp;v={STALE_V19_REVISION}" not in source
    assert f'href="assets/proofs.css?v={CURRENT_REVISION}"' in source


def test_grand_atlas_embeds_the_exact_current_snapshot_without_rewriting_history() -> None:
    document = _document(ATLAS / "index.html")
    snapshot = json.loads("".join(document.snapshot))
    assert snapshot == _campaign()
    assert snapshot["meta"]["current_alpha_version"] == "v23"
    assert snapshot["meta"]["current_alpha_checked_use_count"] == 1_949
    assert "v19" in snapshot["meta"]["historical_alpha_versions"]
    assert "v20" in snapshot["meta"]["historical_alpha_versions"]
    assert "v21" in snapshot["meta"]["historical_alpha_versions"]
    assert "v22" in snapshot["meta"]["historical_alpha_versions"]

    boundaries = snapshot["ambitious_boundaries"]
    current = boundaries["alpha_v23_edition"]
    historic = boundaries["alpha_v22_edition"]
    assert current["role"] == "current_immutable_release"
    assert current["theorem_count"] == current["checked_use_count"] == 1_949
    assert current["stable_closed_count"] == 432
    assert current["catalog_sha256"] == _catalog_digest()
    assert historic["role"] == "immutable_historical_parent"
    assert historic["theorem_count"] == 1_890


def test_grand_atlas_closes_three_exact_milestones_but_keeps_t13_genuinely_open() -> None:
    nodes = {node["id"]: node for node in _campaign()["nodes"]}
    expected = {
        "T12": "beta_horner_eval_exists",
        "G023": "central_binom_prime_divisor_multiplicity_one_exists",
        "G024": "iterated_bertrand_prime_chain_exists",
        "G071": "continued_fraction_positive_exists",
    }
    for milestone, root in expected.items():
        node = nodes[milestone]
        evidence = node["evidence"]
        assert node["status"] == "alpha_closed"
        assert evidence["alpha_version"] == "v20"
        assert evidence["checked_use"] is True
        assert evidence["full_empty_context_closure"] is True
        assert evidence["theorem_name"] == root
        assert evidence["bundle_nodes"] == 590
        assert evidence["bundle_sha256"] == NEXT_BUNDLE_SHA256
        assert evidence["independent_lean_bundle_verified"] is True

    partial = nodes["T13"]
    evidence = partial["evidence"]
    assert partial["status"] == "open"
    assert evidence["implementation"] == "independently_closed_partial"
    assert evidence["checked_use"] is False
    assert evidence["partial_component_checked_use"] is True
    assert evidence["alpha_version"] == "v21"
    assert evidence["partial_checked_theorem_count"] == 33
    assert evidence["new_checked_theorem_count"] == 23
    assert evidence["partial_theorem_name"] == "beta_signed_matrix_product_exists"
    assert evidence["independent_lean_bundle_verified"] is True
    assert evidence["full_arbitrary_signed_matrix_proved"] is True
    assert evidence["full_arbitrary_signed_matrix_product_proved"] is True
    assert evidence["full_arbitrary_determinant_proved"] is False
    assert evidence["full_lattice_substrate_proved"] is False
    assert "T13 milestone remains OPEN" in (
        NEXT / "matrix-dot-product" / "index.html"
    ).read_text(encoding="utf-8")
    for identifier, expected_count, expected_edges, expected_name in (
        ("G101", 17, 48, "euclidean_gcd_execution_logarithmic_bound"),
        ("G102", 24, 63, "binary_modular_execution_logarithmic_bound"),
        ("G025", 18, 46, "infinitely_many_primes_three_mod_four"),
    ):
        node = nodes[identifier]
        closed_evidence = node["evidence"]
        assert node["status"] == "alpha_closed"
        assert closed_evidence["implementation"] == "independently_closed"
        assert closed_evidence["checked_use"] is True
        assert closed_evidence["stable_member"] is False
        assert closed_evidence["full_empty_context_closure"] is True
        assert closed_evidence["alpha_version"] == "v23"
        assert closed_evidence["new_theorem_count"] == expected_count
        assert closed_evidence["dependency_edge_count"] == expected_edges
        assert closed_evidence["theorem_name"] == expected_name
        assert closed_evidence["bundle_nodes"] == 617
        assert closed_evidence["bundle_dependencies"] == 1_871
        assert closed_evidence["bundle_sha256"] == MILESTONE_BUNDLE_SHA256
        assert closed_evidence["independent_lean_bundle_verified"] is True
    assert nodes["G101"]["evidence"]["terminal_state_identified_with_gcd_proved"] is True
    assert nodes["G101"]["evidence"]["formal_logarithmic_bound_proved"] is True
    assert nodes["G101"]["evidence"]["stronger_two_times_bit_length_bound_proved"] is True
    assert nodes["G102"]["evidence"]["formal_complete_binary_execution_proved"] is True
    assert nodes["G102"]["evidence"]["arbitrary_exponent_binary_digits_proved"] is True
    assert nodes["G102"]["evidence"]["formal_logarithmic_bound_proved"] is True
    assert nodes["G025"]["evidence"]["strict_unbounded_prime_witness_proved"] is True


def test_global_definition_dag_is_downloadable_layered_and_genuinely_reviewed() -> None:
    document = _document(ATLAS / "index.html")
    link = next(item for item in document.links if "data-definition-dag-download" in item)
    assert link["href"] == "./definitions.json"

    graph = _global_definitions()
    rows = {item["name"]: item for item in graph["definitions"]}
    assert graph["schema"] == "constructive-number-theory-definition-dag-v1"
    assert graph["definition_count"] == len(rows) == len(_campaign()["definitions"])
    assert graph["definition_count"] == 152
    assert graph["definition_edge_count"] == 108
    assert graph["statement_usage_edge_count"] == 311
    assert graph["declared_notation_edge_count"] == 55
    assert graph["milestone_usage_edge_count"] == 366
    assert graph["reviewed_definition_count"] == 97
    assert graph["reviewed_definition_edge_count"] == 159
    assert graph["compatible_reviewed_match_count"] == 61
    assert graph["definition_edge_count"] == len(graph["definition_edges"])
    assert graph["topological_layer_count"] == len(graph["layers"]) == 6
    assert graph["reviewed_definition_count"] == len(graph["reviewed_definitions"])
    assert graph["compatible_reviewed_match_count"] == len(
        graph["compatible_reviewed_matches"]
    )

    order = {name: position for position, name in enumerate(graph["topological_order"])}
    assert set(order) == set(rows)
    for edge in graph["definition_edges"]:
        assert edge["kind"] == "definition_uses_definition"
        assert order[edge["target"]] < order[edge["source"]]
        assert edge["target"] in rows[edge["source"]]["dependencies"]

    for name, (identifier, route) in REVIEWED_NEXT_DEFINITIONS.items():
        match = rows[name]["reviewed_match"]
        assert match is not None
        assert match["reviewed_id"] == identifier
        assert match["reviewed_name"] == name
        assert match["route"] == route
        assert match["blueprint_expansion_is_kernel_checked"] is False

    assert rows["Beta"]["reviewed_match"]["reviewed_id"] == "PD0013"
    assert rows["Sum"]["reviewed_match"] is None
    assert rows["Sum"]["reviewed_incompatibility"]["reason"] == "incompatible-arity"


def test_atlas_definition_links_resolve_new_families_both_locally_and_when_deployed() -> None:
    source = (ATLAS / "index.html").read_text(encoding="utf-8")
    function = source.split("function explorerBase(route)", maxsplit=1)[1].split(
        "\n      function ", maxsplit=1
    )[0]
    assert 'if (deployed) return "../" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-next-layer-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-advanced-layer-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-transport-layer-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-milestone-closure-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-frontier-explorer/" + route + "/explorer/defined/";' in function
    for slug in (
        *NEXT_FAMILIES,
        *ADVANCED_FAMILIES,
        *TRANSPORT_FAMILIES,
        *MILESTONE_FAMILIES,
    ):
        assert f'"{slug}"' in function


def test_next_layer_manifest_publishes_all_families_with_current_kernel_and_lean_evidence() -> None:
    manifest = _manifest()
    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == "v23"
    assert manifest["alpha_first_enrolled_version"] == "v20"
    assert manifest["proof_bundle_sha256"] == NEXT_BUNDLE_SHA256
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 39
    assert manifest["stable_count"] == 0
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["file_count"] + 1 == sum(path.is_file() for path in NEXT.rglob("*"))
    assert {family["slug"]: family["theorem_count"] for family in manifest["families"]} == {
        slug: family["count"] for slug, family in NEXT_FAMILIES.items()
    }


@pytest.mark.parametrize("slug", tuple(NEXT_FAMILIES))
def test_each_new_family_exposes_real_checked_corpus_graph_and_exact_root_pages(slug: str) -> None:
    expected = NEXT_FAMILIES[slug]
    corpus = _corpus(slug)
    family = next(item for item in _manifest()["families"] if item["slug"] == slug)
    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_edition_version"] == "v23"
    assert corpus["alpha_first_enrolled_version"] == "v20"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == NEXT_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_domain_id"] == expected["domain"]
    assert corpus["campaign_family_id"] == expected["family"]
    assert corpus["path_policy"] == "proof_dependency_edges_only"
    assert all(
        node["alpha_edition_version"] == "v23" and node["alpha_first_enrolled_version"] == "v20"
        for node in corpus["nodes"]
    )
    assert all(node["checked_use"] and node["independent_lean_bundle_verified"] for node in corpus["nodes"])

    graph = json.loads(
        (NEXT / slug / "explorer" / "defined" / "api" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    assert graph["alpha_edition_version"] == "v23"
    assert graph["alpha_first_enrolled_version"] == "v20"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True

    for milestone, (tag, name) in expected["roots"].items():
        assert family["root_tags"][name] == tag
        assert any(node["id"] == tag and node["name"] == name for node in corpus["nodes"])
        exact = NEXT / slug / "explorer" / "tag" / f"{tag}.html"
        defined = NEXT / slug / "explorer" / "defined" / "tag" / f"{tag}.html"
        assert exact.is_file() and defined.is_file()
        page = defined.read_text(encoding="utf-8")
        assert name in page
        assert "Alpha v23 checked-use" in page
        assert "first admitted v20" in page
        assert "compiled verifier accepted all 590 exact bundle nodes" in page
        assert NEXT_BUNDLE_SHA256 in page
        assert f"?v={STALE_V19_REVISION}" not in page

        links = {
            item["data-campaign-link"]: item
            for item in _document(defined).links
            if "data-campaign-link" in item
        }
        assert set(links) >= {"global", "domain", "family", "goal"}
        for item in links.values():
            assert _revision(item["href"]) == CURRENT_REVISION
        assert parse_qs(urlsplit(links["domain"]["href"]).query)["focus"] == [
            expected["domain"]
        ]
        assert parse_qs(urlsplit(links["family"]["href"]).query)["focus"] == [
            expected["family"]
        ]
        assert parse_qs(urlsplit(links["goal"]["href"]).query)["focus"] == [milestone]


@pytest.mark.parametrize("slug", tuple(NEXT_FAMILIES))
def test_new_family_definition_pages_link_exactly_into_global_atlas(slug: str) -> None:
    identifier, name = NEXT_FAMILIES[slug]["definition"]
    corpus = _corpus(slug)
    record = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert record["name"] == record["global_definition"] == name
    assert record["exact_ast_verified"] is True
    assert record["kernel_signature_unchanged"] is True

    page = NEXT / slug / "explorer" / "defined" / "definition" / f"{identifier}.html"
    links = [
        item
        for item in _document(page).links
        if item.get("data-campaign-link") == "definition"
    ]
    assert len(links) == 1
    query = parse_qs(urlsplit(links[0]["href"]).query)
    assert query == {"view": ["definition"], "focus": [name], "v": [CURRENT_REVISION]}


@pytest.mark.parametrize("slug", HISTORIC_ROUTES)
def test_historic_checked_families_report_current_v23_without_rewriting_provenance(
    slug: str,
) -> None:
    corpus = json.loads((HISTORIC / slug / "api" / "corpus.json").read_text(encoding="utf-8"))
    assert corpus["alpha_edition_version"] == "v23"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    for node in corpus["nodes"]:
        if node.get("alpha_checked_use"):
            assert node["alpha_edition_version"] == "v23"
            assert "Alpha v19 checked-use" not in node["status"]


def test_bertrand_flagship_reports_current_v23_authority() -> None:
    root = ROOT / "book" / "_static" / "bertrand-proof-explorer" / "defined"
    landing = (ROOT / "deploy" / "proofs" / "bertrand-postulate.html").read_text(
        encoding="utf-8"
    )
    assert "Alpha v23 independently verified proof" in landing
    assert "Alpha v19 independently verified proof" not in landing
    assert "historical Alpha-v12 enrollment remains unchanged" in landing
    for filename in ("manifest.json", "api/graph.json"):
        record = json.loads((root / filename).read_text(encoding="utf-8"))
        assert record["alpha_edition_version"] == "v23"
        assert record["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY


def test_public_hub_and_release_metrics_preserve_historical_590_node_certificate_and_receipt() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{NEXT_BUNDLE}" in links
    assert f"artifacts/{NEXT_RECEIPT}" in links

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    evidence = metrics["alpha_v20_next_layer_promotion"]["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / NEXT_RECEIPT
    assert artifact.name == NEXT_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 14_775_673
    assert evidence["artifact_sha256"] == NEXT_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 590
    assert evidence["dependency_edges"] == 2_045
    assert evidence["frontier_count"] == 39
    assert evidence["inherited_dependency_count"] == 550
    assert receipt.is_file()
    assert NEXT_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


def test_current_release_preserves_its_historical_209_node_kernel_and_lean_certificate() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{ADVANCED_BUNDLE}" in links
    assert f"artifacts/{ADVANCED_RECEIPT}" in links
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    promotion = metrics["alpha_v21_advanced_layer_promotion"]
    evidence = promotion["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / ADVANCED_RECEIPT
    assert artifact.name == ADVANCED_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 1_005_317
    assert evidence["artifact_sha256"] == ADVANCED_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 209
    assert evidence["dependency_edges"] == 491
    assert evidence["body_proof_nodes"] == 10_304
    assert evidence["frontier_count"] == 54
    assert evidence["inherited_dependency_count"] == 154
    assert promotion["independent_lean_bundle_verified"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert ADVANCED_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


def test_current_release_preserves_its_historical_240_node_kernel_and_lean_certificate() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{TRANSPORT_BUNDLE}" in links
    assert f"artifacts/{TRANSPORT_RECEIPT}" in links

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    promotion = metrics["alpha_v22_transport_layer_promotion"]
    evidence = promotion["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / TRANSPORT_RECEIPT
    assert artifact.name == TRANSPORT_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 1_099_541
    assert evidence["artifact_sha256"] == TRANSPORT_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 240
    assert evidence["dependency_edges"] == 597
    assert evidence["body_proof_nodes"] == 11_848
    assert evidence["frontier_count"] == 60
    assert evidence["inherited_dependency_count"] == 179
    assert promotion["independent_lean_bundle_verified"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert TRANSPORT_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


def test_current_release_publishes_its_actual_617_node_kernel_and_lean_certificate() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{MILESTONE_BUNDLE}" in links
    assert f"artifacts/{MILESTONE_RECEIPT}" in links

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    promotion = metrics["alpha_v23_milestone_closure_promotion"]
    evidence = promotion["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / MILESTONE_RECEIPT
    assert artifact.name == MILESTONE_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 2_518_315
    assert evidence["artifact_sha256"] == MILESTONE_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 617
    assert evidence["dependency_edges"] == 1_871
    assert evidence["body_proof_nodes"] == 39_161
    assert evidence["frontier_count"] == 59
    assert evidence["inherited_dependency_count"] == 557
    assert promotion["independent_lean_bundle_verified"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert MILESTONE_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


@pytest.mark.parametrize("slug", tuple(ADVANCED_FAMILIES))
def test_advanced_families_preserve_provenance_and_report_their_current_goal_status(
    slug: str,
) -> None:
    expected = ADVANCED_FAMILIES[slug]
    corpus = json.loads((ADVANCED / slug / "api/corpus.json").read_text(encoding="utf-8"))
    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["alpha_edition_version"] == "v23"
    assert corpus["alpha_first_enrolled_version"] == "v21"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == ADVANCED_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    expected_status = "open" if expected["goal"] == "T13" else "alpha_closed"
    assert corpus["milestone_status"] == expected_status
    assert corpus["milestone_checked_use"] is (expected["goal"] != "T13")
    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = ADVANCED / slug / "explorer/tag" / f"{tag}.html"
    defined = ADVANCED / slug / "explorer/defined/tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert "Alpha v23 checked-use" in page
    assert "first admitted v21" in page
    assert ADVANCED_BUNDLE_SHA256 in page
    assert "209" in page
    identifier, definition = expected["definition"]
    row = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert row["name"] == row["global_definition"] == definition
    assert row["exact_ast_verified"] is True
    assert (ADVANCED / slug / "explorer/defined/definition" / f"{identifier}.html").is_file()


def test_transport_manifest_publishes_exact_current_and_first_admission_authority() -> None:
    manifest = _transport_manifest()
    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == "v23"
    assert manifest["alpha_first_enrolled_version"] == "v22"
    assert manifest["proof_bundle_sha256"] == TRANSPORT_BUNDLE_SHA256
    assert manifest["proof_bundle_node_count"] == 240
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 60
    assert manifest["stable_count"] == 0
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["file_count"] + 1 == sum(path.is_file() for path in TRANSPORT.rglob("*"))
    assert {family["slug"]: family["theorem_count"] for family in manifest["families"]} == {
        slug: family["count"] for slug, family in TRANSPORT_FAMILIES.items()
    }


@pytest.mark.parametrize("slug", tuple(TRANSPORT_FAMILIES))
def test_transport_families_publish_checked_roots_and_real_definition_dag_links(
    slug: str,
) -> None:
    expected = TRANSPORT_FAMILIES[slug]
    corpus = json.loads((TRANSPORT / slug / "api/corpus.json").read_text(encoding="utf-8"))
    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_edition_version"] == "v23"
    assert corpus["alpha_first_enrolled_version"] == "v22"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == TRANSPORT_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    assert all(
        node["alpha_edition_version"] == "v23"
        and node["alpha_first_enrolled_version"] == "v22"
        for node in corpus["nodes"]
    )

    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = TRANSPORT / slug / "explorer/tag" / f"{tag}.html"
    defined = TRANSPORT / slug / "explorer/defined/tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert "Alpha v23 checked-use" in page
    assert "first admitted v22" in page
    assert "compiled verifier accepted all 240 exact bundle nodes" in page
    assert TRANSPORT_BUNDLE_SHA256 in page

    graph = json.loads(
        (TRANSPORT / slug / "explorer/defined/api/graph.json").read_text(encoding="utf-8")
    )
    assert graph["alpha_edition_version"] == "v23"
    assert graph["alpha_first_enrolled_version"] == "v22"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    assert all(
        node["alpha_edition_version"] == "v23"
        and node["alpha_first_enrolled_version"] == "v22"
        for node in graph["nodes"]
        if node.get("kind") == "theorem"
    )

    identifier, definition = expected["definition"]
    row = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert row["name"] == row["global_definition"] == definition
    assert row["exact_ast_verified"] is True
    definition_page = (
        TRANSPORT / slug / "explorer/defined/definition" / f"{identifier}.html"
    )
    assert definition_page.is_file()
    atlas_links = [
        item
        for item in _document(definition_page).links
        if item.get("data-campaign-link") == "definition"
    ]
    assert len(atlas_links) == 1
    assert parse_qs(urlsplit(atlas_links[0]["href"]).query) == {
        "view": ["definition"],
        "focus": [definition],
        "v": [CURRENT_REVISION],
    }


def test_milestone_manifest_publishes_three_fully_closed_independent_campaigns() -> None:
    manifest = _milestone_manifest()
    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == "v23"
    assert manifest["alpha_first_enrolled_version"] == "v23"
    assert manifest["proof_bundle_sha256"] == MILESTONE_BUNDLE_SHA256
    assert manifest["proof_bundle_node_count"] == 617
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 59
    assert manifest["stable_count"] == 0
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["file_count"] + 1 == sum(path.is_file() for path in MILESTONE.rglob("*"))
    assert {family["slug"]: family["theorem_count"] for family in manifest["families"]} == {
        slug: family["count"] for slug, family in MILESTONE_FAMILIES.items()
    }


@pytest.mark.parametrize("slug", tuple(MILESTONE_FAMILIES))
def test_complete_milestone_families_publish_actual_checked_roots_and_definition_dags(
    slug: str,
) -> None:
    expected = MILESTONE_FAMILIES[slug]
    corpus = json.loads((MILESTONE / slug / "api/corpus.json").read_text(encoding="utf-8"))
    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_edition_version"] == corpus["alpha_first_enrolled_version"] == "v23"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == MILESTONE_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    assert len(corpus["definitions"]) == expected["definition_count"]

    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = MILESTONE / slug / "explorer/tag" / f"{tag}.html"
    defined = MILESTONE / slug / "explorer/defined/tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert "Alpha v23 checked-use" in page
    assert "first admitted v23" in page
    assert "compiled verifier accepted all 617 exact bundle nodes" in page
    assert MILESTONE_BUNDLE_SHA256 in page

    graph = json.loads(
        (MILESTONE / slug / "explorer/defined/api/graph.json").read_text(encoding="utf-8")
    )
    assert graph["alpha_edition_version"] == graph["alpha_first_enrolled_version"] == "v23"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    assert all(
        node["alpha_edition_version"] == node["alpha_first_enrolled_version"] == "v23"
        for node in graph["nodes"]
        if node.get("kind") == "theorem"
    )

    identifier, definition = expected["definition"]
    row = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert row["name"] == row["global_definition"] == definition
    assert row["exact_ast_verified"] is True
    assert row["kernel_signature_unchanged"] is True
    definition_page = MILESTONE / slug / "explorer/defined/definition" / f"{identifier}.html"
    assert definition_page.is_file()
    atlas_links = [
        item
        for item in _document(definition_page).links
        if item.get("data-campaign-link") == "definition"
    ]
    assert len(atlas_links) == 1
    assert parse_qs(urlsplit(atlas_links[0]["href"]).query) == {
        "view": ["definition"],
        "focus": [definition],
        "v": [CURRENT_REVISION],
    }


def test_stage_proofs_exposes_all_twenty_one_routes_and_all_exact_additive_artifacts() -> None:
    output = _staging_dry_run("stage-proofs")
    assert "python3 scripts/build_constructive_next_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_advanced_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_transport_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_milestone_closure_explorer.py" in output
    assert "scripts/sync_constructive_grand_campaign.py --check" in output
    assert "book/_static/constructive-grand-campaign/" in output
    assert '"_deploy/proofs/grand-campaign/"' in output

    for slug in FLAGSHIP_ROUTES:
        assert f'"_deploy/proofs/{slug}/explorer/' in output
    for slug in HISTORIC_ROUTES:
        assert f"book/_static/constructive-frontier-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in NEXT_FAMILIES:
        assert f"book/_static/constructive-next-layer-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in ADVANCED_FAMILIES:
        assert f"book/_static/constructive-advanced-layer-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in TRANSPORT_FAMILIES:
        assert f"book/_static/constructive-transport-layer-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in MILESTONE_FAMILIES:
        assert f"book/_static/constructive-milestone-closure-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for filename in (
        NEXT_BUNDLE,
        NEXT_RECEIPT,
        ADVANCED_BUNDLE,
        ADVANCED_RECEIPT,
        TRANSPORT_BUNDLE,
        TRANSPORT_RECEIPT,
        MILESTONE_BUNDLE,
        MILESTONE_RECEIPT,
    ):
        assert f'"_deploy/proofs/artifacts/{filename}"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_stage_peano_includes_all_frozen_v20_through_v23_bundles_without_deployment() -> None:
    output = _staging_dry_run("stage-peano")
    assert f"research/arithmetic-library/artifacts/{NEXT_BUNDLE}" in output
    assert f"/proof-artifacts/{NEXT_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{ADVANCED_BUNDLE}" in output
    assert f"/proof-artifacts/{ADVANCED_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{TRANSPORT_BUNDLE}" in output
    assert f"/proof-artifacts/{TRANSPORT_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{MILESTONE_BUNDLE}" in output
    assert f"/proof-artifacts/{MILESTONE_BUNDLE}" in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output
