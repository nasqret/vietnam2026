#!/usr/bin/env python3
"""Publish historical Alpha-v25 breakthroughs under current Alpha-v28 authority.

All displayed formulas, scripts, dependencies, definition DAGs and closure
receipts retain their immutable v25 first-admission catalog, its v24 parent,
and the independently compiled-Lean-verified original-kernel bundle.  The
current v28 release must preserve those exact rows and checked-use authority.
The stronger milestones T13, G095 and G011 are now closed by separate v27
second-wave proofs; these v25 chapters retain their original partial scope.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import sys
from types import FunctionType, MappingProxyType
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

import build_constructive_next_layer_explorer as original  # noqa: E402
import build_constructive_research_layer_explorer as research  # noqa: E402
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
    ADVANCED_LAYER_REGISTRIES,
)
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME,
    BREAKTHROUGH_LAYER_REGISTRIES,
)
from constructive_frontier_exact_explorer import (  # noqa: E402
    render_exact_index,
    render_exact_theorem,
)
from constructive_milestone_closure_definitions import (  # noqa: E402
    MILESTONE_CLOSURE_DEFINITIONS_BY_NAME,
    MILESTONE_CLOSURE_REGISTRIES,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS_BY_NAME,
    NEXT_LAYER_REGISTRIES,
)
from constructive_proof_explorer_template import (  # noqa: E402
    render_canonical_family_landing,
)
from constructive_research_layer_definitions import (  # noqa: E402
    RESEARCH_LAYER_DEFINITIONS_BY_NAME as HISTORICAL_RESEARCH_DEFINITIONS_BY_NAME,
    RESEARCH_LAYER_REGISTRIES as HISTORICAL_RESEARCH_REGISTRIES,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_REGISTRIES,
)
from peano_lab.library import editions_v24 as v24  # noqa: E402
from peano_lab.library import editions_v25 as v25  # noqa: E402
from peano_lab.library import editions_v28 as current_alpha  # noqa: E402
from peano_lab.library.alpha_enrollment_v25 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V25_EXPECTED_COUNT,
    FRONTIER_V25_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V24_COUNT,
    FrontierV25Campaign,
    alpha_v25_enrollment,
)
from peano_lab.library.campaign_breakthrough_layer_closure import (  # noqa: E402
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT,
)
from peano_lab.library.defined_syntax import DefinitionSpec  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "constructive-breakthrough-layer-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v25.json"
PARENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v28.json"
CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v28.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_STABLE_COUNT = 432
# Historical branch notation stays fixed; the complete current atlas is
# independently reconstructed and authenticated by _audit_current_atlas.
EXPECTED_REVIEWED_DEFINITION_COUNT = 120
EXPECTED_BUNDLE_PATH = (
    "research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json"
)
SCHEMA = "peano-lab-constructive-breakthrough-layer-explorer-v1"
STATUS = (
    "Alpha v28 checked-use · first admitted v25 · "
    "independently kernel and Lean verified; not Stable"
)
ASSET_SOURCES = original.ASSET_SOURCES
PINNED_ASSETS = original.PINNED_ASSETS
_digest = original._digest
_json = original._json
_e = original._e
_versioned = original._versioned
_file_digest = original._file_digest
_asset = original._asset
_LocalDefinedParser = original._LocalDefinedParser

# Reuse the already-audited definition-record implementation without modifying
# its historical module globals: the cloned function has THIS isolated namespace.
RESEARCH_LAYER_DEFINITIONS_BY_NAME = MappingProxyType({
    **HISTORICAL_RESEARCH_DEFINITIONS_BY_NAME,
    **BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME,
})
RESEARCH_LAYER_REGISTRIES = HISTORICAL_RESEARCH_REGISTRIES + BREAKTHROUGH_LAYER_REGISTRIES


class BreakthroughLayerExplorerError(ValueError):
    """A theorem, definition, receipt, or historical/current scope boundary changed."""


# The cloned audited helpers reference their original exception's global name.
ResearchLayerExplorerError = BreakthroughLayerExplorerError


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV25Campaign
    prefix: str
    title: str
    kicker: str
    description: str
    formula: str
    domain: str
    family_id: str
    milestones: tuple[str, ...]
    roots: tuple[str, ...]
    definitions: tuple[str, ...]
    caveat: str


FAMILIES = (
    Family(
        slug="matrix-cofactor-expansion",
        campaign=FrontierV25Campaign.MATRIX_COFACTOR_EXPANSION,
        prefix="CE",
        title="Complete signed cofactor families and alternating Laplace folds",
        kicker="Every genuine first-row minor · arbitrary alternating sums · T13 partial",
        description=(
            "Twenty-nine independently checked constructive theorems simultaneously "
            "encode every genuine signed first-row cofactor minor, prove exact "
            "parity-adjusted finite Laplace folds and establish uniqueness in every "
            "unrestricted finite dimension."
        ),
        formula="∀M,q. ∃ family. ∀j<S(q). family[j]=SignedMinor(M,0,j)",
        domain="D05",
        family_id="F12",
        milestones=("T13",),
        roots=(
            "matrix_minor_four_code_components_injective",
            "signed_cofactor_minor_family_exists",
            "signed_cofactor_minor_family_entry_projects_minor",
            "signed_alternating_product_prefix_exact_term",
            "signed_alternating_cofactor_fold_exists",
            "signed_alternating_cofactor_fold_functional",
            "signed_alternating_cofactor_fold_exists_unique",
            "signed_first_row_cofactor_fold_exists",
            "signed_matrix_cofactor_family_and_fold_exists",
        ),
        definitions=(
            "SignedFirstRowCofactorFold", "SignedAlternatingCofactorFold",
            "SignedAlternatingProductPrefix", "SignedAlternatingCofactorTerm",
            "SignedCofactorMinorPrefix", "SignedMinorRecord", "MatrixMinorFourCode",
            "SignedMatrixMinor", "MatrixMinorPrefix", "MatrixMinorCell",
            "MatrixSkipIndex", "MatrixAffineSlice", "Sum", "Even", "Odd", "Beta", "Lt",
        ),
        caveat=(
            "Historical partial components only: this chapter proves genuine signed "
            "first-row minors and unique alternating folds, with supplied cofactor "
            "values. T13 is now closed in the separate Alpha-v27 integer-linear-algebra "
            "branch with actual arbitrary determinant data, rank, and integer "
            "column spans; lattice index and normal forms are not claimed."
        ),
    ),
    Family(
        slug="polynomial-taylor-hensel",
        campaign=FrontierV25Campaign.POLYNOMIAL_TAYLOR_HENSEL,
        prefix="TH",
        title="Constructive Taylor remainders and one-step Hensel lifting",
        kicker="Exact quadratic Taylor witness · bounded inverse correction · G095 partial",
        description=(
            "Nineteen independently checked constructive theorems prove exact "
            "witnessed quadratic Taylor remainders for arbitrary beta-coded "
            "polynomials, unique bounded modular correction digits and a genuine "
            "one-step simple-root divisibility lift."
        ),
        formula="f(a)=m·q ∧ gcd(f′(a),p)=1 ⇒ ∃t<p. p·m ∣ f(a+m·t)",
        domain="D04",
        family_id="F10",
        milestones=("G095",),
        roots=(
            "beta_horner_eval_mod_congruence",
            "beta_horner_derivative_mod_congruence",
            "beta_horner_taylor_remainder_exists",
            "hensel_correction_exists_unique",
            "horner_derivative_coprime_bounded_inverse",
            "beta_horner_taylor_square_congruence",
            "beta_horner_hensel_lift_divisibility",
            "beta_horner_hensel_lift_exists",
        ),
        definitions=(
            "HornerTaylorRemainder", "HenselCorrection", "HornerDerivative",
            "HornerDerivativeTrace", "Horner", "Coprime", "IsGCD", "ModEq",
            "Dvd", "Prime", "Beta", "Lt", "Pow",
        ),
        caveat=(
            "Historical partial components only: this chapter proves exact natural "
            "polynomial Taylor remainders, bounded corrections, and one-step "
            "divisibility lifts. G095 is now closed in the separate Alpha-v27 "
            "hensel-lifting branch for integer polynomials, unrestricted input "
            "roots, unique canonical representatives, and every positive prime power."
        ),
    ),
    Family(
        slug="generalized-crt-compatibility",
        campaign=FrontierV25Campaign.GENERALIZED_CRT_COMPATIBILITY,
        prefix="GC",
        title="Noncoprime constructive CRT compatibility and canonical solutions",
        kicker="Exact successive-LCM compatibility · genuine noncoprime lists · G011 partial",
        description=(
            "Twenty-four independently checked constructive theorems solve "
            "arbitrary positive noncoprime finite systems satisfying their exact "
            "successive-LCM/gcd compatibility invariant and also establish the "
            "genuinely pairwise-compatible dominating-last case."
        ),
        formula="MergeCompatible(aᵢ,mᵢ) ⇒ ∃!x<lcm(mᵢ). ∀i. x≡aᵢ (mod mᵢ)",
        domain="D01",
        family_id="F02",
        milestones=("G011",),
        roots=(
            "crt_prefix_solution_implies_pairwise_compatible",
            "crt_merge_compatible_prefix_solution_exists",
            "crt_prefix_zero_lcm_solution_unique",
            "crt_is_gcd_scale",
            "crt_lcm_gcd_cofactor_product",
            "crt_gcd_lcm_distributes_divisibility",
            "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
            "crt_merge_compatible_prefix_canonical_exists_unique",
        ),
        definitions=(
            "CRTMergeCompatiblePrefix", "CRTPairwiseCompatiblePrefix",
            "CRTCanonicalPrefixSolution", "CRTPrefixLCM", "CRTPrefixSolution",
            "CRTPositiveModuliPrefix", "CRTPairwiseCoprimePrefix", "Coprime",
            "IsGCD", "Dvd", "ModEq", "Beta", "Lt", "Le",
        ),
        caveat=(
            "Historical partial components only: this chapter proves canonical "
            "solutions under successive-merge compatibility and in the "
            "pairwise-compatible dominating-last case. G011 is now closed in the "
            "separate Alpha-v27 generalized-crt branch for arbitrary "
            "pairwise-compatible finite lists, including noncoprime moduli."
        ),
    ),
)


@lru_cache(maxsize=1)
def _definition_specs() -> dict[str, DefinitionSpec]:
    definitions = dict(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
    if (
        len(definitions) != EXPECTED_REVIEWED_DEFINITION_COUNT
        or len({item.stable_id for item in definitions.values()})
        != EXPECTED_REVIEWED_DEFINITION_COUNT
        or definitions.get("Mod4Three") is None
        or definitions["Mod4Three"].stable_id != "PD0012"
    ):
        raise BreakthroughLayerExplorerError("the historical reviewed Alpha-v25 registry changed")
    for definition in definitions.values():
        required = definition.conceptual_dependencies
        if (
            len(required) != len(set(required))
            or definition.name in required
            or not set(required) <= set(definitions)
        ):
            raise BreakthroughLayerExplorerError(
                f"reviewed definition {definition.name!r} has an invalid dependency"
            )
    return definitions


def _definition_closure(names: Sequence[str]) -> tuple[DefinitionSpec, ...]:
    available = _definition_specs()
    ordered: list[DefinitionSpec] = []
    active: set[str] = set()
    complete: set[str] = set()

    def visit(name: str) -> None:
        if name in complete:
            return
        if name in active:
            raise BreakthroughLayerExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise BreakthroughLayerExplorerError(f"unknown constructive definition {name!r}")
        active.add(name)
        for dependency in definition.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        complete.add(name)
        ordered.append(definition)

    for name in names:
        visit(name)
    return tuple(ordered)


def _validate_theorem(
    row: Mapping[str, Any],
    *,
    spec: Any,
    campaign: FrontierV25Campaign,
    source: str,
    bundle: Mapping[str, Any],
) -> None:
    if (
        row.get("name") != spec.name
        or row.get("statement") != spec.statement
        or row.get("dependencies") != list(spec.dependencies)
        or row.get("script") != list(spec.script)
        or row.get("summary") != spec.summary
        or row.get("frontier_campaign") != campaign.value
        or row.get("statement_sha256") != _digest(spec.statement)
        or row.get("script_sha256") != _digest("\n".join(spec.script) + "\n")
        or row.get("checked_use") is not True
        or row.get("evidence_status") != "alpha_closed"
        or row.get("membership") != "alpha_only"
        or not isinstance(row.get("source"), dict)
        or row["source"].get("path") != source
    ):
        raise BreakthroughLayerExplorerError(f"exact checked Alpha-v25 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v25_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "breakthrough_layer"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "breakthrough_layer"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise BreakthroughLayerExplorerError(
            f"theorem lacks its independently dependency-closed kernel proof: {spec.name}"
        )


def _load_inputs() -> dict[str, Any]:
    """Authenticate v25 admission and the separately completed v27 milestones."""

    if (
        v25.EXPECTED_ALPHA_V25_COUNT <= PARENT_ALPHA_V24_COUNT
        or FRONTIER_V25_EXPECTED_COUNT <= 0
        or EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT <= 0
    ):
        raise BreakthroughLayerExplorerError("the Alpha-v25 breakthrough release is not sealed")
    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    current_raw_catalog = CURRENT_CATALOG.read_bytes()
    current_catalog = json.loads(current_raw_catalog)
    channels = json.loads(CHANNELS.read_bytes())
    parent_channels_raw = CHANNELS.with_name("channels-v27.json").read_bytes()
    parent_channels = json.loads(parent_channels_raw)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v25"
        or catalog.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or catalog.get("checked_use_count") != v25.EXPECTED_ALPHA_V25_CHECKED_USE_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v25.ALPHA_V25_ENROLLMENT_SHA256
        or catalog.get("frontier_v25_campaign_counts") != expected_counts
        or catalog.get("frontier_v25_ordered_names_sha256")
        != FRONTIER_V25_EXPECTED_NAMES_SHA256
    ):
        raise BreakthroughLayerExplorerError("the sealed fully checked Alpha-v25 catalog changed")
    channel = channels.get("channels", {}).get("alpha", {})
    original._audit_current_parent(current_catalog, channels, error_type=BreakthroughLayerExplorerError)
    current_parent = current_catalog.get("parent_alpha_v25", {})
    if (
        channels.get("schema") != "peano-library-channels-v28"
        or channels.get("default_channel") != "stable"
        or channels.get("parent_channels_v27", {}).get("path")
        != "artifacts/peano-library/channels-v27.json"
        or channels.get("parent_channels_v27", {}).get("sha256")
        != _digest(parent_channels_raw)
        or channels.get("channels", {}).get("stable")
        != parent_channels.get("channels", {}).get("stable")
        or channel.get("artifact_path") != "artifacts/peano-library/alpha/catalog-v28.json"
        or channel.get("artifact_sha256") != _digest(current_raw_catalog)
        or channel.get("parent_alpha_v25_sha256") != _digest(raw_catalog)
        or channel.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V28_COUNT
        or channel.get("checked_use_count") != current_alpha.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT
        or channel.get("edition_identity_sha256") != current_alpha.ALPHA_V28_IDENTITY_SHA256
        or channel.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V28_ENROLLMENT_SHA256
        or current_catalog.get("schema") != "peano-library-alpha-snapshot-v28"
        or current_catalog.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V28_COUNT
        or current_catalog.get("checked_use_count")
        != current_alpha.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT
        or current_catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or current_catalog.get("edition_identity_sha256")
        != current_alpha.ALPHA_V28_IDENTITY_SHA256
        or current_catalog.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V28_ENROLLMENT_SHA256
        or not isinstance(current_parent, dict)
        or current_parent.get("schema") != "peano-library-alpha-snapshot-v25"
        or current_parent.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or current_parent.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or current_parent.get("ordered_enrollment_root_sha256")
        != v25.ALPHA_V25_ENROLLMENT_SHA256
        or not isinstance(current_parent.get("artifacts"), dict)
        or current_parent.get("artifacts", {}).get("catalog") != {
            "path": "artifacts/peano-library/alpha/catalog-v25.json",
            "sha256": _digest(raw_catalog),
        }
        or not isinstance(current_catalog.get("theorems"), list)
        or len(current_catalog["theorems"]) != current_alpha.EXPECTED_ALPHA_V28_COUNT
        or current_catalog["theorems"][:v25.EXPECTED_ALPHA_V25_COUNT]
        != catalog.get("theorems")
        or tuple(current_alpha.ALPHA_ENTRIES[:v25.EXPECTED_ALPHA_V25_COUNT])
        != v25.ALPHA_ENTRIES
        or any(
            newer is not historical
            for newer, historical in zip(current_alpha.ALPHA_ENTRIES, v25.ALPHA_ENTRIES)
        )
    ):
        raise BreakthroughLayerExplorerError(
            "the current Alpha-v28 channel changed its sealed historical Alpha-v25 admission"
        )
    parent = catalog.get("parent_alpha_v24")
    if (
        not isinstance(parent, dict)
        or parent.get("schema") != "peano-library-alpha-snapshot-v24"
        or parent.get("theorem_count") != PARENT_ALPHA_V24_COUNT
        or parent.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or not isinstance(parent.get("artifacts"), dict)
        or not isinstance(parent["artifacts"].get("catalog"), dict)
        or parent["artifacts"]["catalog"].get("sha256") != _file_digest(PARENT_CATALOG)
    ):
        raise BreakthroughLayerExplorerError("Alpha-v25 lost its exact immutable Alpha-v24 parent")
    promotion = catalog.get("alpha_v25_breakthrough_layer_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V25_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("parent_theorem_count") != PARENT_ALPHA_V24_COUNT
        or promotion.get("independent_lean_bundle_verified") is not True
    ):
        raise BreakthroughLayerExplorerError(
            "Alpha-v25 lacks complete independently original-kernel- and Lean-verified admission"
        )
    bundle = promotion.get("proof_bundle")
    if (
        not isinstance(bundle, dict)
        or bundle.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle.get("node_count") != EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V25_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT - FRONTIER_V25_EXPECTED_COUNT - 1
        or bundle.get("independent_lean_bundle_verified") is not True
    ):
        raise BreakthroughLayerExplorerError("Alpha-v25 lacks its exact independently Lean-verified proof")
    artifact = (REPO / EXPECTED_BUNDLE_PATH).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise BreakthroughLayerExplorerError("the sealed Alpha-v25 breakthrough proof-bundle bytes changed")

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != v25.EXPECTED_ALPHA_V25_COUNT:
        raise BreakthroughLayerExplorerError("Alpha-v25 lacks its complete checked theorem inventory")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise BreakthroughLayerExplorerError("malformed Alpha-v25 theorem row")
        if row["name"] in by_name:
            raise BreakthroughLayerExplorerError(f"duplicate Alpha-v25 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_bytes())
    graph = json.loads(GLOBAL_DEFINITIONS.read_bytes())
    original._audit_current_atlas(campaign, graph, error_type=BreakthroughLayerExplorerError)
    blueprint = campaign.get("definitions")
    if not isinstance(blueprint, dict):
        raise BreakthroughLayerExplorerError("the global atlas has no exact named definition registry")
    goals = {item["id"]: item for item in campaign.get("nodes", ())}
    for goal in original.SECOND_WAVE_COMPLETIONS:
        original._audit_second_wave_milestone(
            goal, goals.get(goal), current_catalog, error_type=BreakthroughLayerExplorerError
        )

    enrollment = alpha_v25_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V25_EXPECTED_COUNT:
        raise BreakthroughLayerExplorerError("Alpha-v25 enrollment changed its checked additions")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise BreakthroughLayerExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
        _validate_theorem(
            row, spec=spec, campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name], bundle=bundle,
        )
    return {
        "catalog": current_catalog,
        "first_admission_catalog": catalog,
        "channels": channels,
        "catalog_sha256": _digest(current_raw_catalog),
        "first_admission_catalog_sha256": _digest(raw_catalog),
        "revision": _digest(current_raw_catalog)[:12],
        "bundle": bundle,
        "by_name": by_name,
        "campaign": campaign,
        "blueprint": blueprint,
        "global_graph": graph,
        "milestones": goals,
        "enrollment": enrollment,
    }


_definition_records = FunctionType(
    research._definition_records.__code__, globals(), "_definition_records",
    research._definition_records.__defaults__, research._definition_records.__closure__,
)


def _factory_name(campaign: FrontierV25Campaign) -> str:
    return {
        FrontierV25Campaign.MATRIX_COFACTOR_EXPANSION: (
            "make_matrix_cofactor_expansion_candidate_theorems"
        ),
        FrontierV25Campaign.POLYNOMIAL_TAYLOR_HENSEL: (
            "make_polynomial_taylor_hensel_candidate_theorems"
        ),
        FrontierV25Campaign.GENERALIZED_CRT_COMPATIBILITY: (
            "make_generalized_crt_compatibility_candidate_theorems"
        ),
    }[campaign]


_inherited_family_corpus = FunctionType(
    research._family_corpus.__code__, globals(), "_inherited_family_corpus",
    research._family_corpus.__defaults__, research._family_corpus.__closure__,
)


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    corpus = _inherited_family_corpus(family, inputs)
    corpus["alpha_edition_version"] = "v28"
    corpus["alpha_first_enrolled_version"] = "v25"
    for node in corpus["nodes"]:
        node["alpha_edition_version"] = "v28"
        node["alpha_first_enrolled_version"] = "v25"
    return corpus


def _graph_payload(family: Family, corpus: Mapping[str, Any], *, revision: str) -> dict[str, Any]:
    graph = original._graph_payload(family, corpus, revision=revision)
    graph["schema"] = f"{SCHEMA}-graph"
    graph["alpha_edition_version"] = "v28"
    graph["alpha_first_enrolled_version"] = "v25"
    graph.update(original._completed_milestone_metadata(family.milestones[-1]))
    graph["milestone_caveat"] = family.caveat
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            node["alpha_edition_version"] = "v28"
            node["alpha_first_enrolled_version"] = "v25"
    return graph


def _retarget(document: bytes, family: Family, *, include_caveat: bool = False) -> bytes:
    # Keep the exact audited historical QR templates while upgrading the
    # current checked use and immutable first-admission metadata of v25 rows.
    text = research._retarget(document, family, include_caveat=include_caveat).decode("utf-8")
    text = text.replace("first admitted v24", "first admitted v25")
    text = text.replace("FIRST ADMITTED v24", "FIRST ADMITTED v25")
    text = text.replace("First admission</dt><dd>Alpha v24", "First admission</dt><dd>Alpha v25")
    text = text.replace("Alpha v24", "Alpha v25")
    text = text.replace("ALPHA v24", "ALPHA v25")
    text = text.replace("Alpha-v24", "Alpha-v25")
    old_count = research.EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
    count = EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT
    text = text.replace(f"{old_count}-node bundle", f"{count}-node bundle")
    text = text.replace(f"all {old_count} exact bundle nodes", f"all {count} exact bundle nodes")
    text = text.replace(f" / {old_count}</dd>", f" / {count}</dd>")
    return text.encode("utf-8")


def _top_index(
    corpora: Sequence[tuple[Family, Mapping[str, Any]]], *, revision: str
) -> bytes:
    entries = "".join(
        f'<article class="proof-card"><h2><a href="{_versioned(family.slug + "/", revision)}">'
        f"{_e(family.title)}</a></h2><p>{_e(family.description)}</p>"
        f"<p>{corpus['node_count']} independently kernel- and Lean-verified theorems · "
        f"{corpus['definition_count']} conservative definitions · "
        f"{family.milestones[-1]} now closed in its separate second-wave branch</p>"
        f'<p class="pd-callout">{_e(family.caveat)}</p></article>'
        for family, corpus in corpora
    )
    body = f"""<main class="proof-home proof-library-home"><header class="proof-hero">
 <p class="eyebrow">ALPHA v28 · HISTORICAL v25 INDEPENDENTLY VERIFIED CONSTRUCTIVE BREAKTHROUGHS</p>
 <h1>Complete cofactor families, genuine Hensel lifts, and noncoprime CRT</h1>
 <p>Independently original-kernel- and Lean-verified historical advances, linked to the separate second-wave proofs that now complete their broader milestones.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Complete number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>Each displayed theorem first admitted in historical Alpha v25 retains current Alpha-v28 checked-use authority. These old components retain their partial scope; the separate second-wave branches now close T13, G095 and G011. Stable remains an unchanged separate edition.</p></main>"""
    return original._document(
        FAMILIES[0], title="Three Constructive Number-Theory Breakthroughs",
        body=body, prefix="", defined=False,
    )


def _trim_html_trailing_whitespace(document: bytes) -> bytes:
    """Keep inherited optional template slots free of commit-breaking spaces."""

    return b"\n".join(line.rstrip(b" \t") for line in document.split(b"\n"))


def build_files() -> dict[str, bytes]:
    """Build canonical QR-style surfaces after exact independent v25 verification."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise BreakthroughLayerExplorerError(f"reviewed shared explorer asset changed: {name}")
        files[f"assets/{name}"] = payload

    built: list[tuple[Family, Mapping[str, Any]]] = []
    for family in FAMILIES:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        prefix = family.slug
        files[f"{prefix}/index.html"] = render_canonical_family_landing(
            family, corpus, revision=revision,
            current_alpha_version="v28", first_admitted_version="v25",
            bundle_node_count=EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT,
        )
        files[f"{prefix}/api/corpus.json"] = _json(corpus)
        files[f"{prefix}/explorer/index.html"] = _retarget(
            original._inject_atlas_navigation(
                render_exact_index(
                    family, corpus, corpus["tags"], corpus["layers"],
                    stylesheet_href=_asset("exact-explorer.css", "../../"),
                    script_href=_asset("exact-explorer.js", "../../"),
                    html_revision=revision,
                ), family, prefix="../../", revision=revision,
            ), family,
        )
        files[f"{prefix}/explorer/defined/index.html"] = _retarget(
            original._defined_index(family, corpus, revision=revision), family
        )
        files[f"{prefix}/explorer/defined/graph.html"] = _retarget(
            original._defined_graph(family, corpus, graph, revision=revision), family
        )
        files[f"{prefix}/explorer/defined/api/graph.json"] = _json(graph)
        for node in corpus["nodes"]:
            tag = corpus["tags"][node["name"]]
            files[f"{prefix}/explorer/tag/{tag}.html"] = _retarget(
                original._inject_atlas_navigation(
                    render_exact_theorem(
                        family, corpus, node, corpus["tags"], corpus["layers"],
                        stylesheet_href=_asset("exact-explorer.css", "../../../"),
                        script_href=_asset("exact-explorer.js", "../../../"),
                        html_revision=revision,
                    ), family, prefix="../../../", revision=revision,
                    goal=node["campaign_milestone"],
                ), family,
            )
            files[f"{prefix}/explorer/defined/tag/{tag}.html"] = _retarget(
                original._defined_theorem(family, corpus, node, revision=revision),
                family, include_caveat=True,
            )
        for definition in corpus["definitions"]:
            files[f"{prefix}/explorer/defined/definition/{definition['id']}.html"] = (
                _retarget(
                    original._defined_definition(family, corpus, definition, revision=revision),
                    family,
                )
            )
        built.append((family, corpus))
    files["index.html"] = _top_index(built, revision=revision)
    original._link_second_wave_completions(files, FAMILIES, revision=revision)
    files = {
        name: _trim_html_trailing_whitespace(payload) if name.endswith(".html") else payload
        for name, payload in files.items()
    }
    inventory = [
        {"path": name, "bytes": len(payload), "sha256": _digest(payload)}
        for name, payload in sorted(files.items())
    ]
    manifest = {
        "schema": f"{SCHEMA}-manifest",
        "alpha_edition_version": "v28",
        "alpha_first_enrolled_version": "v25",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["first_admission_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["catalog"]["edition_identity_sha256"],
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT,
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "alpha_edition_version": "v28",
                "alpha_first_enrolled_version": "v25",
                "domain": family.domain,
                "family": family.family_id,
                "milestones": list(family.milestones),
                **original._completed_milestone_metadata(family.milestones[-1]),
                "theorem_count": corpus["node_count"],
                "definition_count": corpus["definition_count"],
                "root_tags": {name: corpus["tags"][name] for name in family.roots},
            }
            for family, corpus in built
        ],
        "file_count": len(inventory),
        "inventory_sha256": _digest(_json(inventory)),
        "files": inventory,
    }
    files["manifest.json"] = _json(manifest)
    return files


_write = research._write
_check = research._check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    try:
        files = build_files()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"constructive breakthrough-layer explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive breakthrough-layer explorer is stale", file=sys.stderr)
            return 1
        print(
            f"constructive breakthrough-layer explorer: {len(files)} files, "
            f"{FRONTIER_V25_EXPECTED_COUNT} checked theorems"
        )
        return 0
    _write(options.output, files)
    print(
        f"constructive breakthrough-layer explorer: wrote {len(files)} files, "
        f"{FRONTIER_V25_EXPECTED_COUNT} checked theorems"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
