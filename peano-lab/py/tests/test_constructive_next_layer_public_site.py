"""End-to-end static publication contract for the current sealed proof site.

These bounded integration checks inspect only source HTML, small JSON surfaces,
streamed catalog bytes, file metadata, and ``make -n`` output.  They never
decode, reconstruct, replay, or kernel-check historical proof bundles.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
HUB = ROOT / "deploy" / "proofs" / "index.html"
ATLAS = ROOT / "book" / "_static" / "constructive-gaussian-campaign"
HISTORIC = ROOT / "book" / "_static" / "constructive-frontier-explorer"
NEXT = ROOT / "book" / "_static" / "constructive-next-layer-explorer"
ADVANCED = ROOT / "book" / "_static" / "constructive-advanced-layer-explorer"
TRANSPORT = ROOT / "book" / "_static" / "constructive-transport-layer-explorer"
MILESTONE = ROOT / "book" / "_static" / "constructive-milestone-closure-explorer"
RESEARCH = ROOT / "book" / "_static" / "constructive-research-layer-explorer"
BREAKTHROUGH = ROOT / "book" / "_static" / "constructive-breakthrough-layer-explorer"
SECOND_WAVE = ROOT / "book/_static/constructive-second-wave-explorer-v30"
LOWER_LAYER = ROOT / "book/_static/constructive-lower-layer-explorer-v30"
PRIORITY_LAYER = ROOT / "book/_static/constructive-priority-layer-explorer-v30"
GAUSSIAN_FACTORIZATION = ROOT / "book/_static/constructive-gaussian-factorization-explorer"
CURRENT_ALPHA_VERSION = json.loads((ATLAS / "campaign.json").read_text(encoding="utf-8"))[
    "meta"
]["current_alpha_version"]
CATALOG = ROOT / "artifacts" / "peano-library" / "alpha" / f"catalog-{CURRENT_ALPHA_VERSION}.json"
CHANNELS = ROOT / "artifacts" / "peano-library" / f"channels-{CURRENT_ALPHA_VERSION}.json"
METRICS = ROOT / "artifacts" / "peano-library" / "alpha" / f"metrics-{CURRENT_ALPHA_VERSION}.json"
CURRENT_CHANNEL = json.loads(CHANNELS.read_text(encoding="utf-8"))["channels"]["alpha"]
CURRENT_REVISION = CURRENT_CHANNEL["artifact_sha256"][:12]
STALE_V19_REVISION = "f1c3d3fba013"
CURRENT_ALPHA_IDENTITY = CURRENT_CHANNEL["edition_identity_sha256"]
SEALED_FLAGSHIP_VERSION = "v25"
SEALED_FLAGSHIP_IDENTITY = "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
SECOND_WAVE_BUNDLE_SHA256 = "c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d"
SECOND_WAVE_ROUTES = {
    "integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer",
    "prime-count-chebyshev", "cornacchia", "cauchy-davenport",
}
LOWER_LAYER_ROUTES = {
    "arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers",
}
PRIORITY_LAYER_ROUTES = {
    "prime-valuation-support", "best-approximation", "totient-products",
    "squarefree-kernels", "exponent-lifting",
}
GAUSSIAN_FACTORIZATION_ROUTES = {"gaussian-factorization"}
# These immutable delivery manifests authorize research navigation, not Alpha
# membership.  Their own v30 provenance/revision survives later Alpha releases.
PUBLIC_RESEARCH_PARENT = {
    "alpha_checked_use_count": 3222,
    "alpha_version": "v30",
    "catalog_sha256": "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7",
    "stable_count": 432,
}
PUBLIC_RESEARCH_PACKAGES = (
    {
        "directory": "constructive-bottom-layer-publication",
        "base": "checkpoints",
        "schema": "peano-lab-public-bottom-layer-checkpoints-v1",
        "manifest": {"bytes": 81153, "sha256": "f800d3436d7b053a6ba233e2c1014d7a1b8e7eb613ba3d9c36902ca5ede623ab"},
        "checkpoint_digest": "fc592c0a4a0c385178528860634b18678e846327e9206b410cab043eb2ce7d48",
        "families": {"euler-units": 32, "prime-fields": 87, "mobius-values": 21, "signed-sums": 30},
        "count_key": "frontier_count",
    },
    {
        "directory": "constructive-lower-tier-publication",
        "base": "checkpoints/lower-tier",
        "schema": "peano-lab-public-lower-tier-checkpoints-v1",
        "manifest": {"bytes": 63621, "sha256": "a44222194449c465f9e89915ab07e1a93ad74f61e319d502745a1d4b7dbee152"},
        "checkpoint_digest": "fc8f85092b7a4ae03f3614e940c4ca4ab5cdf4da63710ea692cb10ca8be5bca9",
        "families": {"divisor-sums": 37, "signed-weighted-sums": 40, "prime-field-polynomials": 49},
        "count_key": "new_theorem_count",
    },
)
SECOND_WAVE_COMPLETIONS = {
    "T13": ("integer-linear-algebra", "rectangular_matrix_rank_exists_unique"),
    "G095": ("hensel-lifting", "integer_polynomial_prime_simple_root_lifts_all_positive_powers"),
    "G011": ("generalized-crt", "crt_pairwise_compatible_prefix_normalized_exists_unique"),
}
HISTORICAL_PARTIAL_EVIDENCE_SHA256 = {
    "T13": "fc99bbaa05e917570f1ee7e36ed365d8bed5bc656362ce5a7255fa0eebaa7c1b",
    "G095": "1b1b57bb84b49c6e4ecff1b3eec11426dec337cef0c674a7eb184ea15346326e",
    "G011": "f6f21bb21a20a4c464720e1c9df11d492faae71690c2c9bfaec425bf7787c5be",
}
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
RESEARCH_BUNDLE = "alpha-v24-research-layer-proof-bundle-v1.json"
RESEARCH_RECEIPT = "alpha-v24-research-layer-receipt.md"
RESEARCH_BUNDLE_SHA256 = (
    "627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9"
)
BREAKTHROUGH_BUNDLE = "alpha-v25-breakthrough-layer-proof-bundle-v1.json"
BREAKTHROUGH_RECEIPT = "alpha-v25-breakthrough-layer-receipt.md"
BREAKTHROUGH_BUNDLE_SHA256 = (
    "d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a"
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
RESEARCH_FAMILIES = {
    "matrix-determinant-minors": {
        "count": 17,
        "goal": "T13",
        "root": ("MN000D", "beta_signed_matrix_minor_exists"),
        "definition": ("ND0049", "SignedMatrixMinor"),
        "definition_count": 17,
    },
    "polynomial-hensel": {
        "count": 15,
        "goal": "G095",
        "root": ("HD000B", "beta_horner_derivative_exists_unique"),
        "definition": ("ND0051", "HornerDerivative"),
        "definition_count": 12,
    },
    "generalized-crt-fold": {
        "count": 27,
        "goal": "G011",
        "root": ("CR001B", "crt_pairwise_coprime_prefix_canonical_exists_unique"),
        "definition": ("ND0055", "CRTPrefixSolution"),
        "definition_count": 12,
    },
}
BREAKTHROUGH_FAMILIES = {
    "matrix-cofactor-expansion": {
        "count": 29,
        "goal": "T13",
        "root": ("CE001D", "signed_matrix_cofactor_family_and_fold_exists"),
        "definition": ("ND0064", "SignedFirstRowCofactorFold"),
        "definition_count": 19,
    },
    "polynomial-taylor-hensel": {
        "count": 19,
        "goal": "G095",
        "root": ("TH0013", "beta_horner_hensel_lift_exists"),
        "definition": ("ND0066", "HenselCorrection"),
        "definition_count": 16,
    },
    "generalized-crt-compatibility": {
        "count": 24,
        "goal": "G011",
        "root": ("GC000C", "crt_merge_compatible_prefix_canonical_exists_unique"),
        "definition": ("ND0068", "CRTMergeCompatiblePrefix"),
        "definition_count": 14,
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
    "MatrixSkipIndex": ("ND0046", "matrix-determinant-minors"),
    "MatrixMinorCell": ("ND0047", "matrix-determinant-minors"),
    "MatrixMinorPrefix": ("ND0048", "matrix-determinant-minors"),
    "SignedMatrixMinor": ("ND0049", "matrix-determinant-minors"),
    "HornerDerivativeTrace": ("ND0050", "polynomial-hensel"),
    "HornerDerivative": ("ND0051", "polynomial-hensel"),
    "HornerDerivativeOnly": ("ND0052", "polynomial-hensel"),
    "CRTPositiveModuliPrefix": ("ND0053", "generalized-crt-fold"),
    "CRTPairwiseCoprimePrefix": ("ND0054", "generalized-crt-fold"),
    "CRTPrefixSolution": ("ND0055", "generalized-crt-fold"),
    "CRTPrefixLCM": ("ND0056", "generalized-crt-fold"),
    "CRTCanonicalPrefixSolution": ("ND0057", "generalized-crt-fold"),
    "MatrixMinorFourCode": ("ND0058", "matrix-cofactor-expansion"),
    "SignedMinorRecord": ("ND0059", "matrix-cofactor-expansion"),
    "SignedCofactorMinorPrefix": ("ND0060", "matrix-cofactor-expansion"),
    "SignedAlternatingCofactorTerm": ("ND0061", "matrix-cofactor-expansion"),
    "SignedAlternatingProductPrefix": ("ND0062", "matrix-cofactor-expansion"),
    "SignedAlternatingCofactorFold": ("ND0063", "matrix-cofactor-expansion"),
    "SignedFirstRowCofactorFold": ("ND0064", "matrix-cofactor-expansion"),
    "HornerTaylorRemainder": ("ND0065", "polynomial-taylor-hensel"),
    "HenselCorrection": ("ND0066", "polynomial-taylor-hensel"),
    "CRTPairwiseCompatiblePrefix": ("ND0067", "generalized-crt-compatibility"),
    "CRTMergeCompatiblePrefix": ("ND0068", "generalized-crt-compatibility"),
}


GRAPH_CASES = (
    ("quadratic-reciprocity", ROOT / "book/_static/pa-proof-explorer/defined/graph.html"),
    ("bertrand-postulate", ROOT / "book/_static/bertrand-proof-explorer/defined/graph.html"),
    *(
        (slug, root / slug / "explorer/defined/graph.html")
        for root, slugs in (
            (HISTORIC, HISTORIC_ROUTES), (NEXT, NEXT_FAMILIES),
            (ADVANCED, ADVANCED_FAMILIES), (TRANSPORT, TRANSPORT_FAMILIES),
            (MILESTONE, MILESTONE_FAMILIES), (RESEARCH, RESEARCH_FAMILIES),
            (BREAKTHROUGH, BREAKTHROUGH_FAMILIES), (SECOND_WAVE, SECOND_WAVE_ROUTES),
            (LOWER_LAYER, LOWER_LAYER_ROUTES), (PRIORITY_LAYER, PRIORITY_LAYER_ROUTES),
            (GAUSSIAN_FACTORIZATION, GAUSSIAN_FACTORIZATION_ROUTES),
        )
        for slug in sorted(slugs)
    ),
)


class _Document(HTMLParser):
    """Capture real rendered anchors and the atlas's inert JSON snapshot."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._inside_snapshot = False
        self.snapshot: list[str] = []
        self.scripts: list[dict] = []
        self._script: dict | None = None

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attributes}
        if tag == "a":
            self.links.append(values)
        if tag == "script":
            self._script = {"attributes": values, "body": []}
            self.scripts.append(self._script)
        if tag == "script" and values.get("id") == "campaign-data":
            self._inside_snapshot = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._script = None
        if tag == "script" and self._inside_snapshot:
            self._inside_snapshot = False

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script["body"].append(data)
        if self._inside_snapshot:
            self.snapshot.append(data)


def _document(path: Path) -> _Document:
    result = _Document()
    result.feed(path.read_text(encoding="utf-8"))
    return result


def _pinned_publication_bytes(path: Path, expected: dict) -> bytes:
    """Authenticate small delivery metadata/landing pages, never proof bodies."""
    size = expected["bytes"]
    assert type(size) is int and size > 0
    assert not path.is_symlink() and path.is_file(), path
    assert path.stat().st_size == size, path
    with path.open("rb") as source:
        payload = source.read(size + 1)
    assert len(payload) == size and sha256(payload).hexdigest() == expected["sha256"], path
    return payload


def _assert_research_publication_inventory(package: dict, manifest: dict, inventory: dict) -> None:
    """Keep a public delivery record distinct from its non-admitting evidence."""
    for value in (manifest, inventory):
        assert value["publication_scope"] == "public_research_checkpoint"
        assert value["checkpoint_digest"] == package["checkpoint_digest"]
        assert value["navigation_revision"] == PUBLIC_RESEARCH_PARENT["catalog_sha256"][:12]
    assert manifest["schema"] == package["schema"] + "-manifest"
    assert manifest["file_count_excluding_manifest"] == len(manifest["files"])
    assert inventory["schema"] == package["schema"]
    assert inventory["public_base_path"] == f"/proofs/{package['base']}/"
    assert inventory["parent"] == PUBLIC_RESEARCH_PARENT
    assert inventory["delivery_metadata_only"] is True
    for flag in ("alpha_admission_performed", "stable_admission_performed",
                 "on_demand_alpha_lean_service_exposes_frontier"):
        assert inventory[flag] is False, flag
    for count in ("alpha_checked_use_node_count", "stable_admitted_node_count"):
        assert type(inventory[count]) is int and inventory[count] == 0, count
    assert inventory["families"] == package["families"]
    assert inventory["new_theorem_count"] == sum(package["families"].values())
    rows = inventory["checkpoints"]
    assert Counter(row["slug"] for row in rows) == Counter(package["families"].keys())
    for row in rows:
        assert row[package["count_key"]] == package["families"][row["slug"]]
        assert row["membership"] == "local_non_admitting_checkpoint"
        for flag in ("admitted_to_alpha", "alpha_checked_use", "stable_member"):
            assert row[flag] is False, (row["slug"], flag)
        # Inspect the pinned historical declarations; this test performs no
        # proof replay and grants no authority from a saved success receipt.
        assert row["bundle"]["original_ha_checked"] is True
        assert row["bundle"]["independent_lean_checked"] is True


def _published_research_hub_routes() -> dict[str, str]:
    routes = {}
    for package in PUBLIC_RESEARCH_PACKAGES:
        directory = ROOT / "book/_static" / package["directory"]
        manifest = json.loads(_pinned_publication_bytes(directory / "manifest.json", package["manifest"]))
        inventory = json.loads(_pinned_publication_bytes(directory / "checkpoints.json", manifest["files"]["checkpoints.json"]))
        _assert_research_publication_inventory(package, manifest, inventory)
        historical = inventory["historical_local_inventory"]
        assert historical["path"] == "receipts/local-checkpoints.json"
        assert manifest["files"][historical["path"]] == {
            "bytes": historical["bytes"], "sha256": historical["sha256"],
        }
        local = json.loads(_pinned_publication_bytes(directory / historical["path"], historical))
        assert local["published"] is False
        for key in ("checkpoint_digest", "parent", "checkpoints"):
            assert local[key] == inventory[key]
        for slug in ("", *package["families"]):
            page = f"{slug}/index.html" if slug else "index.html"
            _pinned_publication_bytes(directory / page, manifest["files"][page])
            route = f"{package['base']}/{slug}" if slug else package["base"]
            assert route not in routes
            routes[route] = inventory["navigation_revision"]
    assert len(routes) == 9  # Seven research families and two separate indexes.
    return routes


def _assert_public_hub_routes(document: _Document, alpha_routes: set[str], research_routes: dict[str, str]) -> None:
    assert not alpha_routes.intersection(research_routes)
    assert "grand-campaign" not in alpha_routes | research_routes.keys()
    expected = {route: CURRENT_REVISION for route in alpha_routes | {"grand-campaign"}}
    expected.update(research_routes)
    actual = []
    for item in document.links:
        if "primary-action" not in item.get("class", "").split():
            continue
        href = item["href"]
        route = urlsplit(href).path.removesuffix("/")
        assert route in expected, href
        # Exact relative URLs reject foreign origins, query duplicates,
        # fragments and path aliases as well as incorrect edition revisions.
        assert href == f"{route}/?v={expected[route]}", href
        actual.append(route)
    assert Counter(actual) == Counter(expected.keys())


def _assert_actual_inline_graph_contract(document: _Document, expected: dict, label: str) -> None:
    data = [
        row for row in document.scripts
        if row["attributes"].get("id") == "pa-defined-graph-data"
    ]
    assert len(data) == 1, label
    assert data[0]["attributes"].get("type", "").lower() in {
        "", "text/javascript", "application/javascript",
    }, label
    javascript = [
        {"source": "".join(row["body"]), "filename": f"{label}:script-{index}"}
        for index, row in enumerate(document.scripts)
        if "".join(row["body"]).strip()
        and row["attributes"].get("type", "").lower() not in {
            "application/json", "application/ld+json",
        }
    ]
    result = subprocess.run(
        ["node", "--max-old-space-size=128", "-e", r"""
const fs = require('node:fs'), vm = require('node:vm');
const scripts = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const script of scripts) new vm.Script(script.source, {filename: script.filename});
process.stdout.write(String(scripts.length));
"""],
        input=json.dumps(javascript), check=True, text=True, capture_output=True, timeout=30,
    )
    assert int(result.stdout) == len(javascript) >= 1, label
    assignment = re.fullmatch(
        r"\s*window\.PA_DEFINED_GRAPH\s*=\s*(\{.*\})\s*;\s*",
        "".join(data[0]["body"]), re.DOTALL,
    )
    assert assignment is not None, label
    assert json.loads(assignment.group(1)) == expected, label


@lru_cache(maxsize=1)
def _catalog_digest() -> str:
    """Stream the current catalog; never parse it or touch a proof bundle."""

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
def _research_manifest() -> dict:
    return json.loads((RESEARCH / "manifest.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _breakthrough_manifest() -> dict:
    return json.loads((BREAKTHROUGH / "manifest.json").read_text(encoding="utf-8"))


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


def _assert_separate_second_wave_completion(record: dict, goal: str) -> None:
    """A historical partial chapter links to a distinct, completed v27 proof."""

    route, theorem = SECOND_WAVE_COMPLETIONS[goal]
    assert record["milestone_status"] == "alpha_closed"
    assert record["milestone_checked_use"] is True
    assert "milestone_partial_checked_use" not in record
    assert record["milestone_full_proof_slug"] == route
    assert record["milestone_full_theorem_name"] == theorem
    assert record["milestone_caveat"].startswith("Historical partial components only:")
    assert theorem not in {node["name"] for node in record["nodes"]}


def test_current_alpha_and_immutable_stable_are_bound_to_actual_catalog_bytes() -> None:
    channels = _channels()
    alpha = channels["channels"]["alpha"]
    stable = channels["channels"]["stable"]
    digest = _catalog_digest()

    assert CURRENT_ALPHA_VERSION == "v30"
    assert digest == "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
    assert CURRENT_ALPHA_IDENTITY == "8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9"
    assert digest == alpha["artifact_sha256"]
    assert digest[:12] == CURRENT_REVISION
    assert alpha["artifact_path"] == (
        f"artifacts/peano-library/alpha/catalog-{CURRENT_ALPHA_VERSION}.json"
    )
    assert alpha["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    current = _campaign()["ambitious_boundaries"][f"alpha_{CURRENT_ALPHA_VERSION}_edition"]
    assert alpha["theorem_count"] == alpha["checked_use_count"] == current["theorem_count"]
    assert alpha["evidence_counts"] == {
        "alpha_closed": current["alpha_closed_count"],
        "stable_closed": current["stable_closed_count"],
    }
    assert alpha[f"alpha_{CURRENT_ALPHA_VERSION}_frontier_new_count"] == current[
        "new_theorem_count"
    ]
    current_counts = alpha[f"frontier_{CURRENT_ALPHA_VERSION}_campaign_counts"]
    assert sum(current_counts.values()) == current["new_theorem_count"]
    assert current["theorem_count"] == 3222
    assert current["new_theorem_count"] == 180
    assert current["dependency_edge_count"] == current["checked_dependency_edge_count"] == 10588
    assert current["layer_count"] == 53
    assert current_counts == {
        "gaussian_factorization": 180,
    }
    historical_campaign_counts = {
        "v24": {
            "generalized_crt_fold": 27,
            "matrix_determinant_minors": 17,
            "polynomial_hensel": 15,
        },
        "v25": {
            "generalized_crt_compatibility": 24,
            "matrix_cofactor_expansion": 29,
            "polynomial_taylor_hensel": 19,
        },
    }
    for version, expected in historical_campaign_counts.items():
        historical = json.loads((ROOT / f"artifacts/peano-library/channels-{version}.json").read_bytes())
        historic_alpha = historical["channels"]["alpha"]
        assert historic_alpha[f"frontier_{version}_campaign_counts"] == expected
        assert historic_alpha[f"alpha_{version}_frontier_new_count"] == sum(expected.values())
        assert historical["channels"]["stable"] == stable
    assert stable["theorem_count"] == stable["checked_use_count"] == 432
    assert channels["default_channel"] == "stable"


@pytest.mark.parametrize("slug,path", GRAPH_CASES, ids=[row[0] for row in GRAPH_CASES])
def test_actual_inline_graph_javascript_compiles_and_equals_its_published_api(slug: str, path: Path) -> None:
    assert len(GRAPH_CASES) == len({row[0] for row in GRAPH_CASES}) == 44
    assert path.is_file(), slug
    graph = json.loads((path.parent / "api/graph.json").read_bytes())
    _assert_actual_inline_graph_contract(_document(path), graph, path.relative_to(ROOT).as_posix())


@pytest.mark.parametrize("mutation", (
    "raw_anchor", "summary_relabel", "broken_overlay", "missing_data", "duplicate_data",
))
def test_inline_graph_contract_rejects_html_injection_data_drift_and_invalid_scripts(mutation: str) -> None:
    expected = {"nodes": [{"summary": "Historical Alpha-v21 evidence"}], "edges": []}
    block = f'<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={json.dumps(expected)};</script>'
    source = '<main><p>Proof graph</p></main>' + block
    if mutation == "raw_anchor":
        source = source.replace("Alpha-v21", 'Alpha-v21 <a data-current-milestone="T13">Full</a>')
    elif mutation == "summary_relabel":
        source = source.replace("Alpha-v21", "Alpha-v22")
    elif mutation == "broken_overlay":
        source += '<script>const broken = ;</script>'
    elif mutation == "missing_data":
        source = source.replace(block, "")
    else:
        source += block
    document = _Document()
    document.feed(source)
    with pytest.raises((AssertionError, subprocess.CalledProcessError, json.JSONDecodeError)):
        _assert_actual_inline_graph_contract(document, expected, mutation)


def test_public_hub_publishes_every_current_independently_versioned_family_route() -> None:
    known_routes = (
        set(FLAGSHIP_ROUTES)
        | set(HISTORIC_ROUTES)
        | set(NEXT_FAMILIES)
        | set(ADVANCED_FAMILIES)
        | set(TRANSPORT_FAMILIES)
        | set(MILESTONE_FAMILIES)
        | set(RESEARCH_FAMILIES)
        | set(BREAKTHROUGH_FAMILIES)
        | SECOND_WAVE_ROUTES
        | LOWER_LAYER_ROUTES
        | PRIORITY_LAYER_ROUTES
        | GAUSSIAN_FACTORIZATION_ROUTES
    )
    manifest_routes = set()
    for package in (
        HISTORIC, NEXT, ADVANCED, TRANSPORT, MILESTONE, RESEARCH, BREAKTHROUGH,
        SECOND_WAVE, LOWER_LAYER, PRIORITY_LAYER, GAUSSIAN_FACTORIZATION,
    ):
        manifest = json.loads((package / "manifest.json").read_bytes())
        assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
        assert manifest.get("catalog_sha256", manifest.get("alpha_catalog_sha256")) == _catalog_digest()
        family_routes = [family["slug"] for family in manifest["families"]]
        assert len(family_routes) == len(set(family_routes))
        assert not manifest_routes.intersection(family_routes)
        manifest_routes.update(family_routes)
    assert known_routes == set(FLAGSHIP_ROUTES) | manifest_routes
    assert len(known_routes) == 44
    _assert_public_hub_routes(_document(HUB), known_routes, _published_research_hub_routes())


@pytest.mark.parametrize("mutation", (
    "missing_alpha", "duplicate_alpha", "missing_research", "duplicate_research",
    "missing_index", "duplicate_atlas", "local_only", "misclassified_alpha",
    "wrong_revision", "external_origin", "duplicate_revision", "fragment",
))
def test_public_hub_route_inventory_rejects_unregistered_or_ambiguous_actions(mutation: str) -> None:
    # A small syntax-only hub fixture exercises the same exact route checker;
    # it is not a substitute for the real manifest/pin checks above.
    alpha = {"quadratic-reciprocity"}
    research = {"checkpoints": "ac7111ec14ff", "checkpoints/euler-units": "ac7111ec14ff"}
    hrefs = [f"{route}/?v={revision}" for route, revision in {
        **{route: CURRENT_REVISION for route in alpha | {"grand-campaign"}}, **research,
    }.items()]
    target = {
        "missing_alpha": "quadratic-reciprocity", "duplicate_alpha": "quadratic-reciprocity",
        "missing_research": "checkpoints/euler-units", "duplicate_research": "checkpoints/euler-units",
        "missing_index": "checkpoints", "duplicate_atlas": "grand-campaign",
    }.get(mutation, "checkpoints/euler-units")
    original = next(href for href in hrefs if urlsplit(href).path == target + "/")
    if mutation.startswith("missing_"):
        hrefs.remove(original)
    elif mutation.startswith("duplicate_") and mutation != "duplicate_revision":
        hrefs.append(original)
    elif mutation == "local_only":
        hrefs.append(f"checkpoints/dirichlet-inverses/?v={CURRENT_REVISION}")
    elif mutation == "misclassified_alpha":
        research["quadratic-reciprocity"] = CURRENT_REVISION
    else:
        replacement = {
            "wrong_revision": original.replace("ac7111ec14ff", "000000000000"),
            "external_origin": "https://example.invalid/" + original,
            "duplicate_revision": original + "&v=ac7111ec14ff",
            "fragment": original + "#unchecked",
        }[mutation]
        hrefs[hrefs.index(original)] = replacement
    document = _Document()
    document.feed("".join(f'<a class="primary-action" href="{href}">Open</a>' for href in hrefs))
    with pytest.raises(AssertionError):
        _assert_public_hub_routes(document, alpha, research)


@pytest.mark.parametrize("package", PUBLIC_RESEARCH_PACKAGES, ids=lambda row: row["directory"])
@pytest.mark.parametrize("mutation", (
    "local_scope", "wrong_base", "wrong_parent", "extra_family", "missing_family",
    "duplicate_checkpoint", "wrong_count", "alpha_admission", "stable_admission",
    "service_exposure", "checked_use_count", "checkpoint_admission",
))
def test_public_research_hub_inventory_rejects_scope_count_and_authority_drift(package: dict, mutation: str) -> None:
    directory = ROOT / "book/_static" / package["directory"]
    manifest = json.loads(_pinned_publication_bytes(directory / "manifest.json", package["manifest"]))
    inventory = json.loads(_pinned_publication_bytes(directory / "checkpoints.json", manifest["files"]["checkpoints.json"]))
    if mutation == "local_scope":
        inventory["publication_scope"] = "local_non_admitting_checkpoint"
    elif mutation == "wrong_base":
        inventory["public_base_path"] = "/book/_static/local-only/"
    elif mutation == "wrong_parent":
        inventory["parent"]["catalog_sha256"] = "0" * 64
    elif mutation == "extra_family":
        inventory["families"]["dirichlet-inverses"] = 21
    elif mutation == "missing_family":
        inventory["families"].pop(next(iter(inventory["families"])))
    elif mutation == "duplicate_checkpoint":
        inventory["checkpoints"].append(inventory["checkpoints"][0])
    elif mutation == "wrong_count":
        inventory["checkpoints"][0][package["count_key"]] += 1
    elif mutation == "checkpoint_admission":
        inventory["checkpoints"][0]["admitted_to_alpha"] = True
    else:
        key, value = {
            "alpha_admission": ("alpha_admission_performed", True),
            "stable_admission": ("stable_admission_performed", True),
            "service_exposure": ("on_demand_alpha_lean_service_exposes_frontier", True),
            "checked_use_count": ("alpha_checked_use_node_count", 1),
        }[mutation]
        inventory[key] = value
    # This separately tests semantic rejection even before considering that a
    # changed inventory could not match the pinned delivery manifest.
    with pytest.raises(AssertionError):
        _assert_research_publication_inventory(package, manifest, inventory)


@pytest.mark.parametrize("member", ("manifest.json", "checkpoints.json", "index.html"))
def test_public_research_hub_requires_literal_pinned_delivery_bytes(tmp_path: Path, member: str) -> None:
    package = PUBLIC_RESEARCH_PACKAGES[0]
    directory = ROOT / "book/_static" / package["directory"]
    manifest = json.loads(_pinned_publication_bytes(directory / "manifest.json", package["manifest"]))
    expected = package["manifest"] if member == "manifest.json" else manifest["files"][member]
    payload = _pinned_publication_bytes(directory / member, expected)
    altered = tmp_path / member
    altered.write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
    with pytest.raises(AssertionError):
        _pinned_publication_bytes(altered, expected)


def test_public_hub_truthfully_identifies_the_current_sealed_release() -> None:
    source = HUB.read_text(encoding="utf-8")
    current = _campaign()["ambitious_boundaries"][f"alpha_{CURRENT_ALPHA_VERSION}_edition"]
    definitions = _global_definitions()

    assert f"Immutable Alpha {CURRENT_ALPHA_VERSION}" in source
    assert f"All {current['theorem_count']:,} theorems have checked-use authority" in source
    assert "432 unchanged Stable theorems" in source
    assert "constructive proof campaigns" in source
    assert f"{definitions['definition_count']} structured first-order definitions" in source
    assert f"{definitions['reviewed_definition_count']} reviewed conservative definitions" in source
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
    assert snapshot["meta"]["current_alpha_version"] == CURRENT_ALPHA_VERSION
    assert snapshot["meta"]["current_alpha_checked_use_count"] == CURRENT_CHANNEL["checked_use_count"]
    assert "v19" in snapshot["meta"]["historical_alpha_versions"]
    assert "v20" in snapshot["meta"]["historical_alpha_versions"]
    assert "v21" in snapshot["meta"]["historical_alpha_versions"]
    assert "v22" in snapshot["meta"]["historical_alpha_versions"]
    assert "v23" in snapshot["meta"]["historical_alpha_versions"]
    assert "v24" in snapshot["meta"]["historical_alpha_versions"]
    assert "v25" in snapshot["meta"]["historical_alpha_versions"]
    assert "v26" in snapshot["meta"]["historical_alpha_versions"]
    assert "v27" in snapshot["meta"]["historical_alpha_versions"]
    assert "v28" in snapshot["meta"]["historical_alpha_versions"]
    assert "v29" in snapshot["meta"]["historical_alpha_versions"]
    assert Counter(node["status"] for node in snapshot["nodes"] if node["kind"] == "goal") == {
        "open": 78, "alpha_closed": 41, "stable_closed": 1,
    }
    assert sum(len(node["deps"]) for node in snapshot["nodes"]) == 313

    boundaries = snapshot["ambitious_boundaries"]
    current = boundaries[f"alpha_{CURRENT_ALPHA_VERSION}_edition"]
    historic = boundaries["alpha_v23_edition"]
    assert current["role"] == "current_immutable_release"
    assert current["theorem_count"] == current["checked_use_count"] == CURRENT_CHANNEL["theorem_count"]
    assert current["stable_closed_count"] == 432
    assert current["catalog_sha256"] == _catalog_digest()
    assert historic["role"] in {"immutable_historical_parent", "immutable_historical_ancestor"}
    assert historic["theorem_count"] == 1_949
    parent = boundaries["alpha_v24_edition"]
    assert parent["role"] in {"immutable_historical_parent", "immutable_historical_ancestor"}
    assert parent["theorem_count"] == parent["checked_use_count"] == 2_008
    for version, count in (("v27", 2560), ("v28", 2764), ("v29", 3042)):
        historical_parent = boundaries[f"alpha_{version}_edition"]
        assert historical_parent["role"] == "historical_immutable_release"
        assert historical_parent["theorem_count"] == historical_parent["checked_use_count"] == count


def test_grand_atlas_preserves_historical_closures_and_honest_open_boundaries() -> None:
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
    evidence = partial["historical_partial_evidence"]
    assert partial["status"] == "alpha_closed"
    assert evidence["implementation"] == "independently_closed_partial"
    assert evidence["checked_use"] is False
    assert evidence["partial_component_checked_use"] is True
    assert evidence["alpha_version"] == "v25"
    assert evidence["partial_checked_theorem_count"] >= 50
    assert evidence["new_checked_theorem_count"] >= 17
    assert evidence["partial_theorem_name"] == "signed_matrix_cofactor_family_and_fold_exists"
    assert evidence["independent_lean_bundle_verified"] is True
    assert evidence["full_arbitrary_signed_matrix_proved"] is True
    assert evidence["full_arbitrary_signed_matrix_product_proved"] is True
    assert evidence["full_arbitrary_determinant_proved"] is False
    assert evidence["full_lattice_substrate_proved"] is False
    matrix_page = (NEXT / "matrix-dot-product" / "index.html").read_text(encoding="utf-8")
    assert "T13 milestone remains OPEN" not in matrix_page
    assert "Historical partial components only" in matrix_page
    assert "Full T13 proof · Alpha v27" in matrix_page
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
    for identifier, theorem, theorem_count in (
        ("T13", "signed_matrix_cofactor_family_and_fold_exists", 29),
        ("G095", "beta_horner_hensel_lift_exists", 19),
        ("G011", "crt_merge_compatible_prefix_canonical_exists_unique", 24),
    ):
        node = nodes[identifier]
        partial_evidence = node["historical_partial_evidence"]
        assert node["status"] == "alpha_closed"
        assert partial_evidence["checked_use"] is False
        assert partial_evidence["partial_component_checked_use"] is True
        assert partial_evidence["partial_theorem_name"] == theorem
        assert partial_evidence["new_checked_theorem_count"] == theorem_count
        assert partial_evidence["alpha_version"] == "v25"
        assert partial_evidence["bundle_nodes"] == 302
        assert partial_evidence["bundle_sha256"] == BREAKTHROUGH_BUNDLE_SHA256
        historical_bytes = (json.dumps(
            partial_evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n").encode("utf-8")
        assert sha256(historical_bytes).hexdigest() == HISTORICAL_PARTIAL_EVIDENCE_SHA256[identifier]

        complete = node["evidence"]
        route, root = SECOND_WAVE_COMPLETIONS[identifier]
        assert complete["implementation"] == "independently_closed"
        assert complete["alpha_version"] == "v27"
        assert complete["checked_use"] is True
        assert complete["alpha_enrolled"] is True
        assert complete["stable_member"] is False
        assert complete["full_empty_context_closure"] is True
        assert complete["independent_lean_bundle_verified"] is True
        assert complete["theorem_name"] == root
        assert complete["route"] == route + "/"
        assert complete["bundle_nodes"] == 1224
        assert complete["bundle_dependencies"] == 3999
        assert complete["bundle_sha256"] == SECOND_WAVE_BUNDLE_SHA256
        assert "partial_component_checked_use" not in complete
        assert "partial_theorem_name" not in complete
        assert complete["theorem_name"] != partial_evidence["partial_theorem_name"]

    matrix = nodes["T13"]["evidence"]
    for flag in (
        "full_arbitrary_determinant_proved", "full_rank_substrate_proved",
        "full_lattice_substrate_proved", "positive_absolute_determinant_data_proved",
        "nonzero_determinant_implies_full_rank_proved", "integer_column_span_zero_add_neg_proved",
    ):
        assert matrix[flag] is True
    for flag in (
        "lattice_index_formula_proved", "normal_form_or_reduction_proved",
        "independent_basis_theorem_proved", "determinant_multiplicativity_proved",
    ):
        assert matrix[flag] is False
    for flag in (
        "full_simple_root_hensel_lift_proved", "signed_integer_polynomials_proved",
        "unrestricted_input_canonical_prime_power_lift_proved", "arbitrary_prime_power_iteration_proved",
        "derivative_nonzero_implies_unit_proved", "lifted_root_uniqueness_proved",
    ):
        assert nodes["G095"]["evidence"][flag] is True
    for flag in (
        "full_generalized_crt_proved", "arbitrary_pairwise_compatibility_implies_merge_compatibility_proved",
        "general_compatible_non_coprime_fold_proved", "normalized_unique_solution_proved",
        "zero_moduli_and_empty_list_included",
    ):
        assert nodes["G011"]["evidence"][flag] is True


def test_global_definition_dag_is_downloadable_layered_and_genuinely_reviewed() -> None:
    document = _document(ATLAS / "index.html")
    link = next(item for item in document.links if "data-definition-dag-download" in item)
    assert link["href"] == "./definitions.json"

    graph = _global_definitions()
    rows = {item["name"]: item for item in graph["definitions"]}
    assert graph["schema"] == "constructive-number-theory-definition-dag-v1"
    assert graph["definition_count"] == len(rows) == len(_campaign()["definitions"])
    assert graph["definition_count"] == 370
    assert graph["definition_edge_count"] == sum(len(row["dependencies"]) for row in rows.values()) == 576
    assert graph["statement_usage_edge_count"] == 320
    assert graph["declared_notation_edge_count"] == 246
    assert graph["milestone_usage_edge_count"] == (
        graph["statement_usage_edge_count"] + graph["declared_notation_edge_count"]
    )
    assert graph["milestone_usage_edge_count"] == 566
    assert graph["reviewed_definition_count"] == 284
    assert graph["reviewed_definition_edge_count"] == sum(
        len(row["dependencies"]) for row in graph["reviewed_definitions"]
    ) == 560
    assert graph["compatible_reviewed_match_count"] == 287
    assert graph["exact_name_reviewed_match_count"] == 282
    assert graph["explicit_alias_reviewed_match_count"] == 5
    assert graph["incompatible_reviewed_match_count"] == 2
    assert graph["definition_edge_count"] == len(graph["definition_edges"])
    assert graph["topological_layer_count"] == len(graph["layers"]) >= 7
    assert graph["topological_layer_count"] == 13
    assert graph["topological_layer_count"] == max(
        row["topological_layer"] for row in rows.values()
    ) + 1
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
    assert rows["Prod"]["reviewed_match"] is None
    assert rows["Prod"]["reviewed_incompatibility"]["reason"] == "incompatible-arity"
    assert rows["BetaSum"]["reviewed_match"]["reviewed_id"] == "PD0015"
    assert rows["BetaSum"]["reviewed_match"]["reviewed_name"] == "Sum"
    assert rows["BetaSum"]["reviewed_match"]["reviewed_argument_blueprint_positions"] == [
        0, 1, 2, 3
    ]


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
    assert 'return "../constructive-research-layer-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-breakthrough-layer-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-second-wave-explorer-v30/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-lower-layer-explorer-v30/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-priority-layer-explorer-v30/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-gaussian-factorization-explorer/" + route + "/explorer/defined/";' in function
    assert 'return "../constructive-frontier-explorer/" + route + "/explorer/defined/";' in function
    for slug in (
        *NEXT_FAMILIES,
        *ADVANCED_FAMILIES,
        *TRANSPORT_FAMILIES,
        *MILESTONE_FAMILIES,
        *RESEARCH_FAMILIES,
        *BREAKTHROUGH_FAMILIES,
        *SECOND_WAVE_ROUTES,
        *LOWER_LAYER_ROUTES,
        *PRIORITY_LAYER_ROUTES,
        *GAUSSIAN_FACTORIZATION_ROUTES,
    ):
        assert f'"{slug}"' in function


def test_next_layer_manifest_publishes_all_families_with_current_kernel_and_lean_evidence() -> None:
    manifest = _manifest()
    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v20"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == NEXT_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_domain_id"] == expected["domain"]
    assert corpus["campaign_family_id"] == expected["family"]
    assert corpus["path_policy"] == "proof_dependency_edges_only"
    assert all(
        node["alpha_edition_version"] == CURRENT_ALPHA_VERSION
        and node["alpha_first_enrolled_version"] == "v20"
        for node in corpus["nodes"]
    )
    assert all(node["checked_use"] and node["independent_lean_bundle_verified"] for node in corpus["nodes"])

    graph = json.loads(
        (NEXT / slug / "explorer" / "defined" / "api" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    assert graph["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
        assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
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
def test_historic_checked_families_report_the_current_release_without_rewriting_provenance(
    slug: str,
) -> None:
    corpus = json.loads((HISTORIC / slug / "api" / "corpus.json").read_text(encoding="utf-8"))
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    for node in corpus["nodes"]:
        if node.get("alpha_checked_use"):
            assert node["alpha_edition_version"] == CURRENT_ALPHA_VERSION
            assert "Alpha v19 checked-use" not in node["status"]


def test_bertrand_flagship_reports_current_checked_release_authority() -> None:
    root = ROOT / "book" / "_static" / "bertrand-proof-explorer" / "defined"
    landing = (ROOT / "deploy" / "proofs" / "bertrand-postulate.html").read_text(
        encoding="utf-8"
    )
    assert f"Alpha {CURRENT_ALPHA_VERSION} independently verified proof" in landing
    assert "Alpha v19 independently verified proof" not in landing
    assert "historical Alpha-v12 enrollment remains unchanged" in landing
    for filename in ("manifest.json", "api/graph.json"):
        record = json.loads((root / filename).read_text(encoding="utf-8"))
        assert record["alpha_edition_version"] == SEALED_FLAGSHIP_VERSION
        assert record["alpha_edition_identity_sha256"] == SEALED_FLAGSHIP_IDENTITY


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
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v21"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == ADVANCED_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    if expected["goal"] == "T13":
        _assert_separate_second_wave_completion(corpus, "T13")
        assert "lattice index and normal forms are outside that scope" in corpus["milestone_caveat"]
    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = ADVANCED / slug / "explorer/tag" / f"{tag}.html"
    defined = ADVANCED / slug / "explorer/defined/tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
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
    assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v22"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == TRANSPORT_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    assert corpus["milestone_status"] == "alpha_closed"
    assert corpus["milestone_checked_use"] is True
    assert all(
        node["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
    assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
    assert "first admitted v22" in page
    assert "compiled verifier accepted all 240 exact bundle nodes" in page
    assert TRANSPORT_BUNDLE_SHA256 in page

    graph = json.loads(
        (TRANSPORT / slug / "explorer/defined/api/graph.json").read_text(encoding="utf-8")
    )
    assert graph["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert graph["alpha_first_enrolled_version"] == "v22"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    assert all(
        node["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
    assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
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
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v23"
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
    assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
    assert "first admitted v23" in page
    assert "compiled verifier accepted all 617 exact bundle nodes" in page
    assert MILESTONE_BUNDLE_SHA256 in page

    graph = json.loads(
        (MILESTONE / slug / "explorer/defined/api/graph.json").read_text(encoding="utf-8")
    )
    assert graph["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert graph["alpha_first_enrolled_version"] == "v23"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    assert all(
        node["alpha_edition_version"] == CURRENT_ALPHA_VERSION
        and node["alpha_first_enrolled_version"] == "v23"
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


def test_research_manifest_preserves_exact_checked_authority_and_first_admission() -> None:
    manifest = _research_manifest()
    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert manifest["alpha_first_enrolled_version"] == "v24"
    assert manifest["proof_bundle_sha256"] == RESEARCH_BUNDLE_SHA256
    assert manifest["proof_bundle_node_count"] == 203
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 59
    assert manifest["stable_count"] == 0
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["file_count"] + 1 == sum(path.is_file() for path in RESEARCH.rglob("*"))
    assert {family["slug"]: family["theorem_count"] for family in manifest["families"]} == {
        slug: family["count"] for slug, family in RESEARCH_FAMILIES.items()
    }


@pytest.mark.parametrize("slug", tuple(RESEARCH_FAMILIES))
def test_research_families_keep_historical_components_separate_from_completed_milestones(slug: str) -> None:
    expected = RESEARCH_FAMILIES[slug]
    corpus = json.loads((RESEARCH / slug / "api" / "corpus.json").read_bytes())
    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v24"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == RESEARCH_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    _assert_separate_second_wave_completion(corpus, expected["goal"])
    assert len(corpus["definitions"]) == expected["definition_count"]
    assert corpus["path_policy"] == "proof_dependency_edges_only"

    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = RESEARCH / slug / "explorer" / "tag" / f"{tag}.html"
    defined = RESEARCH / slug / "explorer" / "defined" / "tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
    assert "first admitted v24" in page
    assert "compiled verifier accepted all 203 exact bundle nodes" in page
    assert RESEARCH_BUNDLE_SHA256 in page
    assert f"{expected['goal']} remains OPEN" not in page
    assert f"Full {expected['goal']} proof · Alpha v27" in page

    graph = json.loads(
        (RESEARCH / slug / "explorer" / "defined" / "api" / "graph.json").read_bytes()
    )
    assert graph["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert graph["alpha_first_enrolled_version"] == "v24"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    _assert_separate_second_wave_completion(graph, expected["goal"])
    assert graph["path_policy"] == "proof_dependency_edges_only"

    identifier, definition = expected["definition"]
    record = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert record["name"] == record["global_definition"] == definition
    assert record["exact_ast_verified"] is True
    assert record["kernel_signature_unchanged"] is True
    definition_page = RESEARCH / slug / "explorer" / "defined" / "definition" / f"{identifier}.html"
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


def test_current_release_preserves_its_historical_203_node_research_certificate() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{RESEARCH_BUNDLE}" in links
    assert f"artifacts/{RESEARCH_RECEIPT}" in links

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    promotion = metrics["alpha_v24_research_layer_promotion"]
    evidence = promotion["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / RESEARCH_RECEIPT
    assert artifact.name == RESEARCH_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 738_923
    assert evidence["artifact_sha256"] == RESEARCH_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 203
    assert evidence["dependency_edges"] == 502
    assert evidence["frontier_count"] == 59
    assert evidence["inherited_dependency_count"] == 143
    assert promotion["independent_lean_bundle_verified"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert RESEARCH_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


def test_breakthrough_manifest_binds_all_current_checked_frontiers_to_the_sealed_release() -> None:
    manifest = _breakthrough_manifest()

    assert manifest["catalog_sha256"] == _catalog_digest()
    assert manifest["html_revision"] == CURRENT_REVISION
    assert manifest["edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert manifest["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert manifest["alpha_first_enrolled_version"] == "v25"
    assert manifest["proof_bundle_sha256"] == BREAKTHROUGH_BUNDLE_SHA256
    assert manifest["proof_bundle_node_count"] == 302
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 72
    assert manifest["stable_count"] == 0
    assert manifest["independent_lean_bundle_verified"] is True
    assert manifest["file_count"] + 1 == sum(path.is_file() for path in BREAKTHROUGH.rglob("*"))
    assert {family["slug"]: family["theorem_count"] for family in manifest["families"]} == {
        slug: family["count"] for slug, family in BREAKTHROUGH_FAMILIES.items()
    }


@pytest.mark.parametrize("slug", tuple(BREAKTHROUGH_FAMILIES))
def test_breakthrough_families_publish_old_roots_and_separate_actual_milestone_closures(
    slug: str,
) -> None:
    expected = BREAKTHROUGH_FAMILIES[slug]
    corpus = json.loads((BREAKTHROUGH / slug / "api" / "corpus.json").read_bytes())

    assert corpus["family_slug"] == slug
    assert corpus["node_count"] == corpus["alpha_checked_use_node_count"] == expected["count"]
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert corpus["alpha_first_enrolled_version"] == "v25"
    assert corpus["alpha_edition_identity_sha256"] == CURRENT_ALPHA_IDENTITY
    assert corpus["alpha_catalog_sha256"] == _catalog_digest()
    assert corpus["alpha_proof_bundle_sha256"] == BREAKTHROUGH_BUNDLE_SHA256
    assert corpus["independent_lean_bundle_verified"] is True
    assert corpus["campaign_goal_id"] == expected["goal"]
    _assert_separate_second_wave_completion(corpus, expected["goal"])
    assert len(corpus["definitions"]) == expected["definition_count"]
    assert corpus["path_policy"] == "proof_dependency_edges_only"

    tag, name = expected["root"]
    assert corpus["tags"][name] == tag
    assert name in corpus["root_names"]
    exact = BREAKTHROUGH / slug / "explorer" / "tag" / f"{tag}.html"
    defined = BREAKTHROUGH / slug / "explorer" / "defined" / "tag" / f"{tag}.html"
    assert exact.is_file() and defined.is_file()
    page = defined.read_text(encoding="utf-8")
    assert name in page
    assert f"Alpha {CURRENT_ALPHA_VERSION} checked-use" in page
    assert "first admitted v25" in page
    assert "compiled verifier accepted all 302 exact bundle nodes" in page
    assert BREAKTHROUGH_BUNDLE_SHA256 in page
    assert f"{expected['goal']} remains OPEN" not in page
    assert f"Full {expected['goal']} proof · Alpha v27" in page

    graph = json.loads(
        (BREAKTHROUGH / slug / "explorer" / "defined" / "api" / "graph.json").read_bytes()
    )
    assert graph["alpha_edition_version"] == CURRENT_ALPHA_VERSION
    assert graph["alpha_first_enrolled_version"] == "v25"
    assert graph["alpha_checked_use_node_count"] == expected["count"]
    assert graph["stable_admitted_node_count"] == 0
    assert graph["independent_lean_bundle_verified"] is True
    _assert_separate_second_wave_completion(graph, expected["goal"])
    assert graph["path_policy"] == "proof_dependency_edges_only"

    identifier, definition = expected["definition"]
    record = next(item for item in corpus["definitions"] if item["id"] == identifier)
    assert record["name"] == record["global_definition"] == definition
    assert record["exact_ast_verified"] is True
    assert record["kernel_signature_unchanged"] is True
    definition_page = (
        BREAKTHROUGH / slug / "explorer" / "defined" / "definition" / f"{identifier}.html"
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


def test_current_release_publishes_its_checked_302_node_breakthrough_certificate() -> None:
    links = {item["href"] for item in _document(HUB).links if "href" in item}
    assert f"artifacts/{BREAKTHROUGH_BUNDLE}" in links
    assert f"artifacts/{BREAKTHROUGH_RECEIPT}" in links

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    promotion = metrics["alpha_v25_breakthrough_layer_promotion"]
    evidence = promotion["proof_bundle"]
    artifact = ROOT / evidence["artifact_path"]
    receipt = ROOT / "research" / "arithmetic-library" / BREAKTHROUGH_RECEIPT
    assert artifact.name == BREAKTHROUGH_BUNDLE
    assert artifact.stat().st_size == evidence["artifact_bytes"] == 1_041_166
    assert evidence["artifact_sha256"] == BREAKTHROUGH_BUNDLE_SHA256
    assert evidence["node_count"] == evidence["kernel_calls"] == 302
    assert evidence["dependency_edges"] == 820
    assert evidence["frontier_count"] == 72
    assert evidence["inherited_dependency_count"] == 229
    assert promotion["independent_lean_bundle_verified"] is True
    assert evidence["independent_lean_bundle_verified"] is True
    assert BREAKTHROUGH_BUNDLE_SHA256 in receipt.read_text(encoding="utf-8")


def test_stage_proofs_exposes_all_current_routes_and_exact_additive_artifacts() -> None:
    output = _staging_dry_run("stage-proofs")
    assert "python3 scripts/build_constructive_next_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_advanced_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_transport_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_milestone_closure_explorer.py" in output
    assert "python3 scripts/build_constructive_research_layer_explorer.py" in output
    assert "python3 scripts/build_constructive_breakthrough_layer_explorer.py" in output
    assert "python3 scripts/upgrade_constructive_priority_layer_publication_v30.py" in output
    assert "python3 scripts/build_constructive_gaussian_factorization_explorer.py" in output
    assert "scripts/extend_constructive_gaussian_factorization_campaign.py" in output
    assert "book/_static/constructive-gaussian-campaign/" in output
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
    for slug in RESEARCH_FAMILIES:
        assert f"book/_static/constructive-research-layer-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in BREAKTHROUGH_FAMILIES:
        assert f"book/_static/constructive-breakthrough-layer-explorer/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in SECOND_WAVE_ROUTES:
        assert f"book/_static/constructive-second-wave-explorer-v30/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in LOWER_LAYER_ROUTES:
        assert f"book/_static/constructive-lower-layer-explorer-v30/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in PRIORITY_LAYER_ROUTES:
        assert f"book/_static/constructive-priority-layer-explorer-v30/{slug}/" in output
        assert f'"_deploy/proofs/{slug}/"' in output
    for slug in GAUSSIAN_FACTORIZATION_ROUTES:
        assert f"book/_static/constructive-gaussian-factorization-explorer/{slug}/" in output
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
        RESEARCH_BUNDLE,
        RESEARCH_RECEIPT,
        BREAKTHROUGH_BUNDLE,
        BREAKTHROUGH_RECEIPT,
        "alpha-v26-first-wave-proof-bundle-v1.json",
        "alpha-v26-first-wave-receipt.md",
        "alpha-v27-second-wave-proof-bundle-v1.json",
        "alpha-v27-second-wave-receipt.md",
        "alpha-v28-lower-layer-proof-bundle-v1.json",
        "alpha-v28-lower-layer-receipt.md",
        "alpha-v29-priority-layer-proof-bundle-v1.json",
        "alpha-v29-priority-layer-receipt.md",
        "alpha-v30-gaussian-factorization-proof-bundle-v1.json",
        "alpha-v30-gaussian-factorization-receipt.md",
    ):
        assert f'"_deploy/proofs/artifacts/{filename}"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output


def test_stage_peano_includes_all_frozen_v20_through_v30_bundles_without_deployment() -> None:
    output = _staging_dry_run("stage-peano")
    assert f"research/arithmetic-library/artifacts/{NEXT_BUNDLE}" in output
    assert f"/proof-artifacts/{NEXT_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{ADVANCED_BUNDLE}" in output
    assert f"/proof-artifacts/{ADVANCED_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{TRANSPORT_BUNDLE}" in output
    assert f"/proof-artifacts/{TRANSPORT_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{MILESTONE_BUNDLE}" in output
    assert f"/proof-artifacts/{MILESTONE_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{RESEARCH_BUNDLE}" in output
    assert f"/proof-artifacts/{RESEARCH_BUNDLE}" in output
    assert f"research/arithmetic-library/artifacts/{BREAKTHROUGH_BUNDLE}" in output
    assert f"/proof-artifacts/{BREAKTHROUGH_BUNDLE}" in output
    for bundle in (
        "alpha-v26-first-wave-proof-bundle-v1.json",
        "alpha-v27-second-wave-proof-bundle-v1.json",
        "alpha-v28-lower-layer-proof-bundle-v1.json",
        "alpha-v29-priority-layer-proof-bundle-v1.json",
        "alpha-v30-gaussian-factorization-proof-bundle-v1.json",
    ):
        assert f"research/arithmetic-library/artifacts/{bundle}" in output
        assert f"/proof-artifacts/{bundle}" in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output
