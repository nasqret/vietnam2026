#!/usr/bin/env python3
"""Publish historical Alpha-v24 families under current sealed Alpha-v30 authority.

Each displayed theorem is a fully dependency-closed original-kernel proof that
was independently verified by the compiled Lean checker. The historical
partial components remain unchanged; separate v27 second-wave proofs now
close T13, G095, and G011 and are linked without upgrading these old proofs.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

import build_constructive_next_layer_explorer as original  # noqa: E402
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
    ADVANCED_LAYER_REGISTRIES,
)
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
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
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    RESEARCH_LAYER_DEFINITIONS_BY_NAME,
    RESEARCH_LAYER_REGISTRIES,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_REGISTRIES,
)
from peano_lab.library import editions_v23 as v23  # noqa: E402
from peano_lab.library import editions_v24 as v24  # noqa: E402
from peano_lab.library import editions_v25 as v25  # noqa: E402
from peano_lab.library import editions_v30 as current_alpha  # noqa: E402
from peano_lab.library.alpha_enrollment_v24 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V24_EXPECTED_COUNT,
    FRONTIER_V24_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V23_COUNT,
    FrontierV24Campaign,
    alpha_v24_enrollment,
)
from peano_lab.library.campaign_research_layer_closure import (  # noqa: E402
    EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
)
from peano_lab.library.campaign_breakthrough_layer_closure import (  # noqa: E402
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256,
    breakthrough_layer_plan,
)
from peano_lab.library.defined_syntax import DefinitionSpec  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "constructive-research-layer-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
PARENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v23.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v30.json"
CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v30.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-gaussian-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_STABLE_COUNT = 432
# These branches retain their reviewed v25 notation; the complete current
# additive atlas is independently authenticated by _audit_current_atlas.
EXPECTED_REVIEWED_DEFINITION_COUNT = 120
EXPECTED_BUNDLE_PATH = (
    "research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json"
)
SCHEMA = "peano-lab-constructive-research-layer-explorer-v1"
STATUS = (
    "Alpha v30 checked-use · first admitted v24 · "
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


class ResearchLayerExplorerError(ValueError):
    """A proof, reviewed definition, or historical/current evidence boundary changed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV24Campaign
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
        slug="matrix-determinant-minors",
        campaign=FrontierV24Campaign.MATRIX_DETERMINANT_MINORS,
        prefix="MN",
        title="Constructive signed matrix minors and determinants",
        kicker="Arbitrary signed cofactor minors · exact 4×4 determinants · T13 partial",
        description=(
            "Seventeen independently checked constructive theorems delete arbitrary "
            "rows and columns from genuinely signed beta-coded matrices of every "
            "finite dimension and construct exact signed four-by-four determinants."
        ),
        formula="∀M,q,r,d. r,d<S(q) ⇒ ∃N. SignedMinor(M,S(q),r,d,N,q)",
        domain="D05",
        family_id="F12",
        milestones=("T13",),
        roots=(
            "matrix_skip_index_avoids_removed",
            "beta_matrix_minor_cell_functional",
            "signed_matrix_four_cofactor_expansion_exists",
            "signed_matrix_four_full_determinant_exists",
            "signed_matrix_four_full_determinant_functional",
            "beta_matrix_minor_exists",
            "beta_signed_matrix_minor_exists",
        ),
        definitions=(
            "SignedMatrixMinor", "MatrixMinorPrefix", "MatrixMinorCell",
            "MatrixSkipIndex", "MatrixAt", "SignedDet2", "SignedMatrixProduct",
            "Beta", "Lt", "Le",
        ),
        caveat=(
            "Historical partial components only: this chapter proves arbitrary signed "
            "cofactor minors and exact signed determinants through dimension four. "
            "T13 is now closed by the separate Alpha-v27 integer-linear-algebra "
            "branch: arbitrary determinant data, rank, and integer column spans, "
            "without a claim of lattice index or normal forms."
        ),
    ),
    Family(
        slug="polynomial-hensel",
        campaign=FrontierV24Campaign.POLYNOMIAL_HENSEL,
        prefix="HD",
        title="Formal polynomial differentiation and Hensel foundations",
        kicker="Exact Horner derivatives · constructive traces · G095 partial",
        description=(
            "Independently checked constructive theorems build coupled beta-coded "
            "Horner value and formal-derivative traces for arbitrary natural "
            "polynomials, including exact successor laws and uniqueness."
        ),
        formula="∀b,c,t,ℓ. ∃!n,z. HornerDerivative(b,c,t,ℓ,n,z)",
        domain="D04",
        family_id="F10",
        milestones=("G095",),
        roots=(
            "beta_horner_derivative_value_exists",
            "beta_horner_derivative_successor_decompose",
            "beta_horner_derivative_functional",
            "beta_horner_derivative_only_exists_unique",
            "beta_horner_derivative_exists_unique",
        ),
        definitions=(
            "HornerDerivativeOnly", "HornerDerivative", "HornerDerivativeTrace",
            "Horner", "Beta", "Lt", "Prime", "ModEq", "Pow",
        ),
        caveat=(
            "Historical partial components only: this chapter proves arbitrary "
            "natural polynomial values and unique formal derivatives. G095 is now "
            "closed in the separate Alpha-v27 hensel-lifting branch for integer "
            "polynomials, unrestricted input roots, unique canonical lifts, and "
            "every positive prime power."
        ),
    ),
    Family(
        slug="generalized-crt-fold",
        campaign=FrontierV24Campaign.GENERALIZED_CRT_FOLD,
        prefix="CR",
        title="Finite Chinese remainder theorem and canonical LCM solutions",
        kicker="Arbitrary finite pairwise-coprime lists · exact LCM · G011 partial",
        description=(
            "Twenty-seven independently checked constructive theorems compute the "
            "universal-property LCM of arbitrary finite modulus lists and prove "
            "existence and canonical uniqueness for every positive pairwise-coprime "
            "finite congruence system."
        ),
        formula="∀ finite coprime positive lists. ∃!x<lcm(mᵢ). ∀i. x≡aᵢ (mod mᵢ)",
        domain="D01",
        family_id="F02",
        milestones=("G011",),
        roots=(
            "crt_prefix_lcm_exists_unique",
            "crt_pairwise_coprime_prefix_solution_exists",
            "crt_prefix_solution_class_iff_lcm",
            "crt_pairwise_coprime_prefix_canonical_exists_unique",
        ),
        definitions=(
            "CRTCanonicalPrefixSolution", "CRTPrefixLCM", "CRTPrefixSolution",
            "CRTPairwiseCoprimePrefix", "CRTPositiveModuliPrefix", "Coprime",
            "IsGCD", "Dvd", "ModEq", "Beta", "Lt", "Le",
        ),
        caveat=(
            "Historical partial components only: this chapter proves canonical "
            "solutions for finite positive pairwise-coprime systems and exact LCM "
            "solution classes. G011 is now closed in the separate Alpha-v27 "
            "generalized-crt branch for arbitrary pairwise-compatible systems, "
            "including noncoprime moduli."
        ),
    ),
)


@lru_cache(maxsize=1)
def _definition_specs() -> dict[str, DefinitionSpec]:
    definitions = dict(HISTORICAL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
    if (
        len(definitions) != EXPECTED_REVIEWED_DEFINITION_COUNT
        or len({item.stable_id for item in definitions.values()})
        != EXPECTED_REVIEWED_DEFINITION_COUNT
        or definitions.get("Mod4Three") is None
        or definitions["Mod4Three"].stable_id != "PD0012"
    ):
        raise ResearchLayerExplorerError("the historical reviewed Alpha-v25 registry changed")
    for definition in definitions.values():
        dependencies = definition.conceptual_dependencies
        if (
            len(dependencies) != len(set(dependencies))
            or definition.name in dependencies
            or not set(dependencies) <= set(definitions)
        ):
            raise ResearchLayerExplorerError(
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
            raise ResearchLayerExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise ResearchLayerExplorerError(f"unknown constructive definition {name!r}")
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
    campaign: FrontierV24Campaign,
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
        raise ResearchLayerExplorerError(f"exact checked Alpha-v24 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v24_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "research_layer"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "research_layer"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise ResearchLayerExplorerError(
            f"theorem lacks its independently dependency-closed kernel proof: {spec.name}"
        )


def _load_inputs() -> dict[str, Any]:
    """Authenticate v24 admission and the separately completed v27 milestones."""

    if (
        v24.EXPECTED_ALPHA_V24_COUNT <= PARENT_ALPHA_V23_COUNT
        or FRONTIER_V24_EXPECTED_COUNT <= 0
        or EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT <= 0
    ):
        raise ResearchLayerExplorerError("the Alpha-v24 research release is not sealed")
    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    current_raw_catalog = CURRENT_CATALOG.read_bytes()
    if _digest(current_raw_catalog) != original.EXPECTED_CURRENT_CATALOG_SHA256:
        raise ResearchLayerExplorerError("the current immutable Alpha-v30 catalog bytes changed or remain unsealed")
    current_catalog = json.loads(current_raw_catalog)
    channels = json.loads(CHANNELS.read_bytes())
    parent_channels_raw = CHANNELS.with_name("channels-v29.json").read_bytes()
    parent_channels = json.loads(parent_channels_raw)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v24"
        or catalog.get("theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or catalog.get("checked_use_count") != v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v24.ALPHA_V24_ENROLLMENT_SHA256
        or catalog.get("frontier_v24_campaign_counts") != expected_counts
        or catalog.get("frontier_v24_ordered_names_sha256")
        != FRONTIER_V24_EXPECTED_NAMES_SHA256
    ):
        raise ResearchLayerExplorerError("the sealed fully checked Alpha-v24 catalog changed")
    channel = channels.get("channels", {}).get("alpha", {})
    original._audit_current_parent(current_catalog, channels, error_type=ResearchLayerExplorerError)
    current_parent = current_catalog.get("parent_alpha_v25", {})
    if (
        channels.get("schema") != "peano-library-channels-v30"
        or channels.get("default_channel") != "stable"
        or channels.get("parent_channels_v29", {}).get("path")
        != "artifacts/peano-library/channels-v29.json"
        or channels.get("parent_channels_v29", {}).get("sha256")
        != _digest(parent_channels_raw)
        or channels.get("channels", {}).get("stable")
        != parent_channels.get("channels", {}).get("stable")
        or channel.get("artifact_path") != "artifacts/peano-library/alpha/catalog-v30.json"
        or channel.get("artifact_sha256") != _digest(current_raw_catalog)
        or channel.get("parent_alpha_v24_sha256") != _digest(raw_catalog)
        or channel.get("parent_alpha_v25_sha256")
        != _file_digest(CURRENT_CATALOG.with_name("catalog-v25.json"))
        or channel.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or channel.get("checked_use_count") != current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or channel.get("edition_identity_sha256") != current_alpha.ALPHA_V30_IDENTITY_SHA256
        or channel.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V30_ENROLLMENT_SHA256
        or current_catalog.get("schema") != "peano-library-alpha-snapshot-v30"
        or current_catalog.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog.get("checked_use_count")
        != current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or current_catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or current_catalog.get("edition_identity_sha256")
        != current_alpha.ALPHA_V30_IDENTITY_SHA256
        or current_catalog.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V30_ENROLLMENT_SHA256
        or not isinstance(current_parent, dict)
        or current_parent.get("schema") != "peano-library-alpha-snapshot-v25"
        or current_parent.get("theorem_count") != v25.EXPECTED_ALPHA_V25_COUNT
        or current_parent.get("edition_identity_sha256") != v25.ALPHA_V25_IDENTITY_SHA256
        or current_parent.get("ordered_enrollment_root_sha256")
        != v25.ALPHA_V25_ENROLLMENT_SHA256
        or not isinstance(current_parent.get("artifacts"), dict)
        or current_parent.get("artifacts", {}).get("catalog") != {
            "path": "artifacts/peano-library/alpha/catalog-v25.json",
            "sha256": channel.get("parent_alpha_v25_sha256"),
        }
        or not isinstance(current_catalog.get("theorems"), list)
        or len(current_catalog["theorems"]) != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog["theorems"][:v24.EXPECTED_ALPHA_V24_COUNT]
        != catalog.get("theorems")
        or tuple(current_alpha.ALPHA_ENTRIES[: v24.EXPECTED_ALPHA_V24_COUNT])
        != v24.ALPHA_ENTRIES
        or any(
            newer is not historical
            for newer, historical in zip(current_alpha.ALPHA_ENTRIES, v24.ALPHA_ENTRIES)
        )
    ):
        raise ResearchLayerExplorerError(
            "the current Alpha-v30 channel changed its sealed historical Alpha-v24 admission"
        )
    parent = catalog.get("parent_alpha_v23")
    if (
        not isinstance(parent, dict)
        or parent.get("schema") != "peano-library-alpha-snapshot-v23"
        or parent.get("theorem_count") != PARENT_ALPHA_V23_COUNT
        or parent.get("edition_identity_sha256") != v23.ALPHA_V23_IDENTITY_SHA256
        or not isinstance(parent.get("artifacts"), dict)
        or not isinstance(parent["artifacts"].get("catalog"), dict)
        or parent["artifacts"]["catalog"].get("sha256") != _file_digest(PARENT_CATALOG)
    ):
        raise ResearchLayerExplorerError("Alpha-v24 lost its exact immutable Alpha-v23 parent")
    promotion = catalog.get("alpha_v24_research_layer_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V24_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("parent_theorem_count") != PARENT_ALPHA_V23_COUNT
        or promotion.get("independent_lean_bundle_verified") is not True
    ):
        raise ResearchLayerExplorerError(
            "Alpha-v24 lacks complete independently original-kernel- and Lean-verified admission"
        )
    bundle = promotion.get("proof_bundle")
    if (
        not isinstance(bundle, dict)
        or bundle.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle.get("node_count") != EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V24_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT - FRONTIER_V24_EXPECTED_COUNT - 1
        or bundle.get("independent_lean_bundle_verified") is not True
    ):
        raise ResearchLayerExplorerError("Alpha-v24 lacks its exact independently Lean-verified proof")
    artifact = (REPO / EXPECTED_BUNDLE_PATH).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise ResearchLayerExplorerError("the sealed Alpha-v24 research proof-bundle bytes changed")

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != v24.EXPECTED_ALPHA_V24_COUNT:
        raise ResearchLayerExplorerError("Alpha-v24 lacks its complete checked theorem inventory")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ResearchLayerExplorerError("malformed Alpha-v24 theorem row")
        if row["name"] in by_name:
            raise ResearchLayerExplorerError(f"duplicate Alpha-v24 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_bytes())
    graph = json.loads(GLOBAL_DEFINITIONS.read_bytes())
    original._audit_current_atlas(campaign, graph, error_type=ResearchLayerExplorerError)
    blueprint = campaign.get("definitions")
    if not isinstance(blueprint, dict):
        raise ResearchLayerExplorerError("the global atlas has no exact named definition registry")
    goals = {item["id"]: item for item in campaign.get("nodes", ())}
    for goal in original.SECOND_WAVE_COMPLETIONS:
        original._audit_second_wave_milestone(
            goal, goals.get(goal), current_catalog, error_type=ResearchLayerExplorerError
        )

    enrollment = alpha_v24_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V24_EXPECTED_COUNT:
        raise ResearchLayerExplorerError("Alpha-v24 enrollment changed its checked additions")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise ResearchLayerExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
        _validate_theorem(
            row,
            spec=spec,
            campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name],
            bundle=bundle,
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


def _definition_records(
    family: Family, inputs: Mapping[str, Any]
) -> tuple[tuple[DefinitionSpec, ...], list[dict[str, Any]]]:
    specs = _definition_closure(family.definitions)
    by_name = {item.name: item for item in specs}
    reviewed_links = original._preferred_reviewed_matches(inputs["global_graph"])
    global_reviewed = {
        row["name"]: row for row in inputs["global_graph"]["reviewed_definitions"]
    }
    routes = {
        definition.name: route
        for route, group in (
            *NEXT_LAYER_REGISTRIES,
            *ADVANCED_LAYER_REGISTRIES,
            *TRANSPORT_LAYER_REGISTRIES,
            *MILESTONE_CLOSURE_REGISTRIES,
            *RESEARCH_LAYER_REGISTRIES,
        )
        for definition in group
    }
    by_id: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        if not set(direct) <= set(by_id):
            raise ResearchLayerExplorerError("the reviewed definition DAG is not dependency-first")
        ancestors = set(direct)
        for identifier in direct:
            ancestors.update(by_id[identifier]["transitive_dependencies"])
        layer = max((by_id[item]["topological_layer"] + 1 for item in direct), default=0)
        custom = definition.stable_id.startswith("ND")
        blueprint = inputs["blueprint"].get(definition.name)
        global_name: str | None = None
        positions: list[int] | None = None
        reviewed_id: str | None = None
        reviewed_route: str | None = None
        if custom:
            shared = (
                RESEARCH_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
                or MILESTONE_CLOSURE_DEFINITIONS_BY_NAME.get(definition.name)
                or TRANSPORT_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
                or ADVANCED_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
                or NEXT_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
            )
            record = global_reviewed.get(definition.name)
            if (
                shared is not definition
                or record is None
                or record.get("id") != definition.stable_id
                or tuple(record.get("parameters", ())) != definition.parameters
                or record.get("expansion_sha256") != _digest(definition.template_source)
                or record.get("dependencies") != list(definition.conceptual_dependencies)
                or record.get("route") != routes.get(definition.name)
            ):
                raise ResearchLayerExplorerError(
                    f"definition {definition.name!r} is not its immutable shared reviewed object"
                )
            reviewed_id = definition.stable_id
            reviewed_route = record["route"]
        if custom and blueprint is not None:
            if tuple(blueprint.get("parameters", ())) != definition.parameters:
                raise ResearchLayerExplorerError(
                    f"research definition {definition.name!r} changed its atlas signature"
                )
            global_name, positions = definition.name, list(range(definition.arity))
            if definition.name == "Beta":
                canonical = _definition_specs()["BetaAt"]
                if (
                    canonical.parameters != definition.parameters
                    or canonical.template_formula != definition.template_formula
                ):
                    raise ResearchLayerExplorerError("canonical Beta no longer equals reviewed BetaAt")
                reviewed_id = canonical.stable_id
                reviewed_route = reviewed_links["BetaAt"]["route"]
            else:
                link = reviewed_links.get(definition.name)
                if (
                    link is None
                    or link.get("reviewed_id") != definition.stable_id
                    or link.get("blueprint_name") != definition.name
                    or link.get("route") != routes.get(definition.name)
                    or link.get("reviewed_expansion_sha256")
                    != _digest(definition.template_source)
                ):
                    raise ResearchLayerExplorerError(
                        f"the global atlas does not share exact definition {definition.name!r}"
                    )
        elif not custom and definition.name in reviewed_links:
            link = reviewed_links[definition.name]
            if (
                link.get("reviewed_id") != definition.stable_id
                or tuple(link.get("reviewed_parameters", ())) != definition.parameters
            ):
                raise ResearchLayerExplorerError(
                    f"reviewed definition {definition.name!r} changed its atlas signature"
                )
            global_name = link["blueprint_name"]
            positions = list(link["reviewed_argument_blueprint_positions"])
            reviewed_id = definition.stable_id
            reviewed_route = link["route"]
        if global_name is not None and (
            global_name not in inputs["blueprint"]
            or len(positions or ()) != definition.arity
            or sorted(positions or ()) != list(range(definition.arity))
        ):
            raise ResearchLayerExplorerError("global definition argument alignment is invalid")
        record = {
            "id": definition.stable_id,
            "name": definition.name,
            "parameters": list(definition.parameters),
            "arity": definition.arity,
            "signature": f"{definition.name}({','.join(definition.parameters)})",
            "summary": definition.summary,
            "expanded_template": definition.template_source,
            "expansion_sha256": _digest(definition.template_source),
            "dependencies": direct,
            "dependency_names": list(definition.conceptual_dependencies),
            "topological_layer": layer,
            "transitive_dependencies": sorted(ancestors),
            "origin": (
                "shared-reviewed-hygienic-conservative-definition"
                if custom else "reviewed-conservative-definition"
            ),
            "reviewed_definition_id": reviewed_id,
            "reviewed_definition_route": reviewed_route,
            "shared_definition_identity": definition.stable_id if custom else None,
            "global_definition": global_name,
            "global_argument_positions": positions,
            "exact_ast_verified": True,
            "kernel_signature_unchanged": True,
        }
        by_id[definition.stable_id] = record
        records.append(record)
    return specs, records


def _factory_name(campaign: FrontierV24Campaign) -> str:
    return {
        FrontierV24Campaign.MATRIX_DETERMINANT_MINORS: (
            "make_matrix_determinant_minors_candidate_theorems"
        ),
        FrontierV24Campaign.POLYNOMIAL_HENSEL: (
            "make_polynomial_hensel_candidate_theorems"
        ),
        FrontierV24Campaign.GENERALIZED_CRT_FOLD: (
            "make_generalized_crt_fold_candidate_theorems"
        ),
    }[campaign]


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    enrollment = inputs["enrollment"]
    specs = tuple(
        item for item in enrollment.frontier_specs
        if enrollment.campaign_by_name[item.name] is family.campaign
    )
    if len(specs) != EXPECTED_CAMPAIGN_COUNTS[family.campaign]:
        raise ResearchLayerExplorerError(f"checked family cardinality changed: {family.slug}")
    definition_specs, definitions = _definition_records(family, inputs)
    compactor = original._FormulaCompactor(definition_specs)
    tags = {item.name: f"{family.prefix}{index:04X}" for index, item in enumerate(specs, 1)}
    nodes: list[dict[str, Any]] = []
    for item in specs:
        row = inputs["by_name"][item.name]
        closure = row["empty_context_closure"]
        source = enrollment.source_by_name[item.name]
        nodes.append({
            "id": tags[item.name],
            "name": item.name,
            "summary": item.summary,
            "statement": item.statement,
            "statement_sha256": row["statement_sha256"],
            "script": list(item.script),
            "dependencies": list(item.dependencies),
            "source_module": source,
            "factory": _factory_name(family.campaign),
            "sources": [{
                "source_module": source,
                "factory": _factory_name(family.campaign),
                "selected": True,
                "statement_sha256": row["statement_sha256"],
                "script_sha256": row["script_sha256"],
            }],
            "status": STATUS,
            "enrolled_in_alpha": True,
            "alpha_evidence": "alpha_closed",
            "alpha_checked_use": True,
            "alpha_edition_version": "v30",
            "alpha_first_enrolled_version": "v24",
            "stable_member": False,
            "admitted_to_alpha": True,
            "admitted_to_stable": False,
            "checked_use": True,
            "independent_lean_bundle_verified": True,
            "proof_bundle_node_id": closure["bundle_node_id"],
            "proof_bundle_sha256": closure["certificate_sha256"],
            "body_proof_nodes": closure["body_proof_nodes"],
            "body_proof_depth": closure["body_proof_depth"],
            "campaign_milestone": family.milestones[-1],
            "defined": compactor.compact(item.statement),
        })
    for name in family.roots:
        if name not in tags:
            raise ResearchLayerExplorerError(
                f"published root is absent from its independently checked family: {name}"
            )
    external_names = sorted({
        dependency for node in nodes for dependency in node["dependencies"]
        if dependency not in tags
    })
    external: list[dict[str, Any]] = []
    for name in external_names:
        row = inputs["by_name"].get(name)
        if row is None or row.get("checked_use") is not True:
            raise ResearchLayerExplorerError(f"unchecked external prerequisite: {name}")
        stable = row.get("membership") == "stable"
        external.append({
            "name": name,
            "evidence": row["evidence_status"],
            "alpha_evidence": row["evidence_status"],
            "alpha_checked_use": True,
            "enrolled_in_alpha": True,
            "admitted_to_alpha": True,
            "admitted_to_stable": stable,
            "kind": "stable-admitted-theorem" if stable else "alpha-admitted-theorem",
            "statement_sha256": row["statement_sha256"],
        })
    layers: dict[str, int] = {}
    critical_paths: dict[str, list[str]] = {}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if not set(internal) <= set(layers):
            raise ResearchLayerExplorerError("theorem DAG has a forward or circular dependency")
        layers[node["name"]] = max((layers[name] + 1 for name in internal), default=0)
        previous = max(internal, key=lambda name: len(critical_paths[name]), default=None)
        critical_paths[node["name"]] = (
            ([] if previous is None else critical_paths[previous]) + [tags[node["name"]]]
        )
    adjacency = {
        node["name"]: {
            "dependencies": [name for name in node["dependencies"] if name in tags],
            "dependents": [item["name"] for item in nodes if node["name"] in item["dependencies"]],
            "critical_root_path": critical_paths[node["name"]],
        }
        for node in nodes
    }
    proof_edges = [
        {"kind": "proof_dependency", "source": tags[name], "target": tags[node["name"]]}
        for node in nodes for name in node["dependencies"] if name in tags
    ]
    usage_edges = [
        {
            "kind": "uses_definition",
            "source": tags[node["name"]],
            "target": identifier,
            "occurrence_count": count,
            "statement_occurrences": count,
            "local_proposition_occurrences": 0,
        }
        for node in nodes
        for identifier, count in node["defined"]["statement_definition_uses"].items()
    ]
    notation_edges = [
        {"kind": "definition_uses_definition", "source": item["id"], "target": parent}
        for item in definitions for parent in item["dependencies"]
    ]
    return {
        "schema": SCHEMA,
        "family_slug": family.slug,
        "family_title": family.title,
        "campaign_domain_id": family.domain,
        "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1],
        "campaign_milestone_ids": list(family.milestones),
        **original._completed_milestone_metadata(family.milestones[-1]),
        "milestone_caveat": family.caveat,
        "root_names": list(family.roots),
        "nodes": nodes,
        "definitions": definitions,
        "external_dependencies": external,
        "edges": proof_edges + usage_edges + notation_edges,
        "node_count": len(nodes),
        "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges),
        "external_dependency_count": len(external),
        "definition_count": len(definitions),
        "definition_dependency_count": len(notation_edges),
        "definition_layer_count": max(
            (item["topological_layer"] + 1 for item in definitions), default=0
        ),
        "definition_topological_order": [item["id"] for item in definitions],
        "statement_definition_use_count": len(usage_edges),
        "formal_line_count": sum(len(node["script"]) for node in nodes),
        "candidate_status": STATUS,
        "alpha_edition_version": "v30",
        "alpha_first_enrolled_version": "v24",
        "alpha_edition_identity_sha256": inputs["catalog"]["edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"],
        "alpha_first_enrollment_catalog_sha256": inputs["first_admission_catalog_sha256"],
        "alpha_proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "independent_lean_bundle_verified": True,
        "alpha_enrolled_node_count": len(nodes),
        "alpha_checked_use_node_count": len(nodes),
        "stable_admitted_node_count": 0,
        "tags": tags,
        "layers": layers,
        "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in critical_paths.items()},
        "path_policy": "proof_dependency_edges_only",
    }


def _graph_payload(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> dict[str, Any]:
    graph = original._graph_payload(family, corpus, revision=revision)
    graph["schema"] = f"{SCHEMA}-graph"
    graph["alpha_edition_version"] = "v30"
    graph["alpha_first_enrolled_version"] = "v24"
    graph.update(original._completed_milestone_metadata(family.milestones[-1]))
    graph["milestone_caveat"] = family.caveat
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            node["alpha_edition_version"] = "v30"
            node["alpha_first_enrolled_version"] = "v24"
    return graph


def _retarget(document: bytes, family: Family, *, include_caveat: bool = False) -> bytes:
    text = document.decode("utf-8")
    old_caveat = (
        "Every displayed theorem was first admitted in Alpha v20, remains independently "
        "kernel- and Lean-verified for current Alpha v30 checked use, and has not been "
        "promoted to Stable."
    )
    text = text.replace(old_caveat, family.caveat)
    text = text.replace("first admitted v20", "first admitted v24")
    text = text.replace("FIRST ADMITTED v20", "FIRST ADMITTED v24")
    text = text.replace("First admission</dt><dd>Alpha v20", "First admission</dt><dd>Alpha v24")
    for version in ("v20", "v21", "v22", "v23"):
        text = text.replace(f"Alpha {version}", "Alpha v24")
        text = text.replace(f"ALPHA {version}", "ALPHA v24")
        text = text.replace(f"Alpha-{version}", "Alpha-v24")
    count = EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
    text = text.replace("590-node bundle", f"{count}-node bundle")
    text = text.replace("all 590 exact bundle nodes", f"all {count} exact bundle nodes")
    text = text.replace(" / 590</dd>", f" / {count}</dd>")
    if include_caveat and _e(family.caveat) not in text:
        marker = '<section class="pd-statement">'
        callout = f'<p class="pd-callout">{_e(family.caveat)}</p>'
        if marker in text:
            text = text.replace(marker, callout + marker, 1)
        elif family.caveat not in text and "</section>\n</main>" in text:
            text = text.replace("</section>\n</main>", f"{callout}</section>\n</main>", 1)
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
 <p class="eyebrow">ALPHA v30 · HISTORICAL v24 INDEPENDENTLY VERIFIED RESEARCH FOUNDATIONS</p>
 <h1>Signed matrix minors, formal derivatives, and finite Chinese remaindering</h1>
 <p>Independently original-kernel- and Lean-verified historical foundations, with links to the separate second-wave proofs that now complete their broader milestones.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Complete number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>Each displayed theorem first admitted in historical Alpha v24 retains current Alpha-v30 checked-use authority. These old components retain their partial scope; the separate second-wave branches now close T13, G095 and G011. Stable remains an unchanged separate edition.</p></main>"""
    return original._document(
        FAMILIES[0], title="Three Constructive Number-Theory Research Foundations",
        body=body, prefix="", defined=False,
    )


def build_files() -> dict[str, bytes]:
    """Build exact QR-style proof surfaces only after sealed v24 verification."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise ResearchLayerExplorerError(f"reviewed shared explorer asset changed: {name}")
        files[f"assets/{name}"] = payload

    built: list[tuple[Family, Mapping[str, Any]]] = []
    for family in FAMILIES:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        prefix = family.slug
        files[f"{prefix}/index.html"] = render_canonical_family_landing(
            family, corpus, revision=revision,
            current_alpha_version="v30", first_admitted_version="v24",
            bundle_node_count=EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
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
    inventory = [
        {"path": name, "bytes": len(payload), "sha256": _digest(payload)}
        for name, payload in sorted(files.items())
    ]
    manifest = {
        "schema": f"{SCHEMA}-manifest",
        "alpha_edition_version": "v30",
        "alpha_first_enrolled_version": "v24",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["first_admission_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["catalog"]["edition_identity_sha256"],
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "alpha_edition_version": "v30",
                "alpha_first_enrolled_version": "v24",
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


def _write(root: Path, files: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name, payload in sorted(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != payload:
            path.write_bytes(payload)


def _check(root: Path, files: Mapping[str, bytes]) -> bool:
    if not root.is_dir():
        return False
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    return actual == set(files) and all(
        (root / name).read_bytes() == payload for name, payload in files.items()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    try:
        files = build_files()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"constructive research-layer explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive research-layer explorer is stale", file=sys.stderr)
            return 1
        print(
            f"constructive research-layer explorer: {len(files)} files, "
            f"{FRONTIER_V24_EXPECTED_COUNT} checked theorems"
        )
        return 0
    _write(options.output, files)
    print(
        f"constructive research-layer explorer: wrote {len(files)} files, "
        f"{FRONTIER_V24_EXPECTED_COUNT} checked theorems"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
