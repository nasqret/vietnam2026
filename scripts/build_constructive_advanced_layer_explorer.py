#!/usr/bin/env python3
"""Publish checked Alpha-v21 families under current immutable Alpha-v24 authority.

This is an evidence-reading static documentation generator, never a theorem
provider.  The sealed Alpha-v21 catalog must authenticate a complete
209-node ordinary intuitionistic proof bundle and its independently compiled
Lean-verifier receipt.  The artifact is stream-hashed but never decoded,
replayed, imported as proof data or used to grant theorem authority.

The exact and defined reading surfaces deliberately reuse the original
quadratic-reciprocity explorer templates, stylesheets and JavaScript.
The original G101/G102 campaigns were open at their Alpha-v21 first
admission and are completely closed under current Alpha-v24 authority. T13
remains honestly open for arbitrary-dimensional determinant and lattice data.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

import build_constructive_next_layer_explorer as original  # noqa: E402
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS,
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
    ADVANCED_LAYER_REGISTRIES,
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from constructive_frontier_exact_explorer import (  # noqa: E402
    render_exact_index,
    render_exact_theorem,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS_BY_NAME,
    NEXT_LAYER_REGISTRIES,
)
from constructive_proof_explorer_template import (  # noqa: E402
    render_canonical_family_landing,
)
from constructive_research_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as CURRENT_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from peano_lab.library import editions_v20 as v20  # noqa: E402
from peano_lab.library import editions_v21 as v21  # noqa: E402
from peano_lab.library import editions_v24 as current_alpha  # noqa: E402
from peano_lab.library.alpha_enrollment_v21 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V21_EXPECTED_COUNT,
    FRONTIER_V21_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V20_COUNT,
    FrontierV21Campaign,
    alpha_v21_enrollment,
)
from peano_lab.library.defined_syntax import DefinitionSpec  # noqa: E402
from peano_lab.library.campaign_milestone_closure import (  # noqa: E402
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256,
    milestone_closure_plan,
)
from peano_lab.library.campaign_research_layer_closure import (  # noqa: E402
    EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256,
    research_layer_plan,
)


OUTPUT = REPO / "book" / "_static" / "constructive-advanced-layer-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v21.json"
PARENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v20.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
CURRENT_CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v24.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_ALPHA_COUNT = 1_830
EXPECTED_STABLE_COUNT = 432
EXPECTED_BUNDLE_NODE_COUNT = 209
EXPECTED_BUNDLE_PATH = (
    "research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json"
)
SCHEMA = "peano-lab-constructive-advanced-layer-explorer-v1"
STATUS = (
    "Alpha v24 checked-use · first admitted v21 · independently kernel and Lean verified; not Stable"
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


class AdvancedLayerExplorerError(ValueError):
    """A sealed v21 receipt, exact definition or published campaign changed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV21Campaign
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
        slug="matrix-coded-products",
        campaign=FrontierV21Campaign.MATRIX_CODED_PRODUCT,
        prefix="MC",
        title="Constructive signed matrix multiplication",
        kicker="Beta-coded slices · arbitrary signed products · exact signed determinants",
        description=(
            "Twenty-three independently checked constructive theorems establish arbitrary "
            "natural and signed matrix multiplication, unique signed dot products, and "
            "genuine signed two- and three-dimensional determinants."
        ),
        formula="(A⁺−A⁻)(B⁺−B⁻) = (A⁺B⁺+A⁻B⁻) − (A⁺B⁻+A⁻B⁺)",
        domain="D05",
        family_id="F12",
        milestones=("T13",),
        roots=(
            "beta_matrix_product_exists",
            "beta_signed_dot_product_exists_unique",
            "signed_matrix_three_full_determinant_exists",
            "beta_signed_matrix_product_exists",
        ),
        definitions=(
            "MatrixAt",
            "DotProduct",
            "SignedDet2",
            "MatrixAffineSlice",
            "MatrixProductCell",
            "MatrixProductPrefix",
            "MatrixPointwiseAdd",
            "SignedDotProduct",
            "SignedMatrixProduct",
        ),
        caveat=(
            "T13 remains OPEN: arbitrary natural and signed matrix multiplication and "
            "signed two-/three-dimensional determinants are proved, but arbitrary-dimensional "
            "determinants, rank and lattice foundations are not."
        ),
    ),
    Family(
        slug="euclidean-complexity",
        campaign=FrontierV21Campaign.EUCLIDEAN_COMPLEXITY,
        prefix="EC",
        title="Constructive Euclidean execution and complexity",
        kicker="Actual Euclidean histories · independent gcd witnesses · strict two-step halving",
        description=(
            "Fifteen independently checked constructive theorems produce complete beta-coded "
            "Euclidean histories, independent relational gcd witnesses, strict two-step "
            "halving and an actual linear step bound."
        ),
        formula="a = bq+r · r<b · 2rᵢ₊₂<rᵢ · steps≤b",
        domain="D04",
        family_id="F11",
        milestones=("G101",),
        roots=(
            "euclidean_two_step_halving",
            "euclidean_execution_exists",
            "euclidean_gcd_execution_linear_bound",
        ),
        definitions=(
            "EuclideanDivision",
            "EuclideanHalving",
            "EuclideanExecution",
            "ContinuedFractionTrace",
            "IsGCD",
        ),
        caveat=(
            "G101 was OPEN when this family was first admitted in Alpha v21. "
            "It is now CLOSED in Alpha v23: the actual anchored Euclidean "
            "history, terminal gcd, and exact bound steps≤2*BitLen(b)+1 are proved."
        ),
    ),
    Family(
        slug="binary-modular-exponentiation",
        campaign=FrontierV21Campaign.BINARY_MODULAR_EXPONENTIATION,
        prefix="BX",
        title="Constructive binary modular exponentiation",
        kicker="Parity splitting · exact square-and-multiply · canonical modular powers",
        description=(
            "Sixteen independently checked constructive theorems establish exact binary "
            "decomposition, square-and-multiply transitions, and existence and uniqueness "
            "of the bounded canonical modular power."
        ),
        formula="e=2h+b · x′≡x²aᵇ (mod m) · 0≤r<m",
        domain="D04",
        family_id="F11",
        milestones=("G102",),
        roots=(
            "binary_exponent_split_exists",
            "binary_modular_step_functional",
            "binary_modular_exponentiation_result_exists_unique",
        ),
        definitions=(
            "BinaryModulus",
            "BinaryExponentSplit",
            "CanonicalModularResidue",
            "BinaryDoubledPower",
            "BinaryOddPower",
            "BinaryModularStep",
            "BinaryModularPower",
        ),
        caveat=(
            "G102 was OPEN when this family was first admitted in Alpha v21. "
            "It is now CLOSED in Alpha v23: every arbitrary exponent has "
            "actual canonical beta-coded digits, a complete modular execution, "
            "and exact counted bound operations≤3*BitLen(e)+2."
        ),
    ),
)


@lru_cache(maxsize=1)
def _definition_specs() -> dict[str, DefinitionSpec]:
    definitions = dict(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
    if len(definitions) != 79 or len({item.stable_id for item in definitions.values()}) != 79:
        raise AdvancedLayerExplorerError("the immutable reviewed constructive registry changed")
    for definition in definitions.values():
        dependencies = definition.conceptual_dependencies
        if (
            len(dependencies) != len(set(dependencies))
            or definition.name in dependencies
            or not set(dependencies) <= set(definitions)
        ):
            raise AdvancedLayerExplorerError(
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
            raise AdvancedLayerExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise AdvancedLayerExplorerError(f"unknown constructive definition {name!r}")
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
    campaign: FrontierV21Campaign,
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
        raise AdvancedLayerExplorerError(f"exact checked Alpha-v21 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v21_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "advanced_layer"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "advanced_layer"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise AdvancedLayerExplorerError(
            f"theorem lacks its original-kernel dependency-closed proof: {spec.name}"
        )


def _load_inputs() -> dict[str, Any]:
    """Authenticate release, Lean receipt, ancestor and global DAG; never decode."""

    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v21"
        or catalog.get("theorem_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("checked_use_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v21.ALPHA_V21_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v21.ALPHA_V21_ENROLLMENT_SHA256
        or catalog.get("frontier_v21_campaign_counts") != expected_counts
        or catalog.get("frontier_v21_ordered_names_sha256") != FRONTIER_V21_EXPECTED_NAMES_SHA256
    ):
        raise AdvancedLayerExplorerError("the sealed fully checked Alpha-v21 catalog changed")
    parent = catalog.get("parent_alpha_v20")
    if (
        not isinstance(parent, dict)
        or parent.get("schema") != "peano-library-alpha-snapshot-v20"
        or parent.get("theorem_count") != PARENT_ALPHA_V20_COUNT
        or parent.get("edition_identity_sha256") != v20.ALPHA_V20_IDENTITY_SHA256
        or not isinstance(parent.get("artifacts"), dict)
        or not isinstance(parent["artifacts"].get("catalog"), dict)
        or parent["artifacts"]["catalog"].get("sha256") != _file_digest(PARENT_CATALOG)
    ):
        raise AdvancedLayerExplorerError("Alpha-v21 lost its exact immutable Alpha-v20 parent")
    promotion = catalog.get("alpha_v21_advanced_layer_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V21_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("parent_theorem_count") != PARENT_ALPHA_V20_COUNT
        or promotion.get("independent_lean_bundle_verified") is not True
    ):
        raise AdvancedLayerExplorerError(
            "Alpha-v21 lacks complete independently kernel- and Lean-verified admission evidence"
        )
    bundle = promotion.get("proof_bundle")
    if (
        not isinstance(bundle, dict)
        or bundle.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle.get("node_count") != EXPECTED_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V21_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_BUNDLE_NODE_COUNT - FRONTIER_V21_EXPECTED_COUNT - 1
        or bundle.get("independent_lean_bundle_verified") is not True
    ):
        raise AdvancedLayerExplorerError("Alpha-v21 lacks its exact independently Lean-verified proof receipt")
    artifact = (REPO / EXPECTED_BUNDLE_PATH).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise AdvancedLayerExplorerError("the sealed advanced proof-bundle bytes changed")

    channels = json.loads(CURRENT_CHANNELS.read_text(encoding="utf-8"))
    current = channels.get("channels", {}).get("alpha", {})
    current_digest = _file_digest(CURRENT_CATALOG)
    if (
        channels.get("schema") != "peano-library-channels-v24"
        or channels.get("default_channel") != "stable"
        or channels.get("parent_channels_v23", {}).get("path")
        != "artifacts/peano-library/channels-v23.json"
        or current.get("artifact_path") != "artifacts/peano-library/alpha/catalog-v24.json"
        or current.get("artifact_sha256") != current_digest
        or current.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V24_COUNT
        or current.get("checked_use_count")
        != current_alpha.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or current.get("edition_identity_sha256")
        != current_alpha.ALPHA_V24_IDENTITY_SHA256
        or current.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V24_ENROLLMENT_SHA256
        or current.get("parent_alpha_v21_sha256") != _digest(raw_catalog)
        or tuple(current_alpha.ALPHA_ENTRIES[:EXPECTED_ALPHA_COUNT]) != v21.ALPHA_ENTRIES
        or any(
            newer is not historical
            for newer, historical in zip(current_alpha.ALPHA_ENTRIES, v21.ALPHA_ENTRIES)
        )
    ):
        raise AdvancedLayerExplorerError(
            "the current immutable Alpha-v24 release changed its exact Alpha-v21 parent"
        )

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != EXPECTED_ALPHA_COUNT:
        raise AdvancedLayerExplorerError("Alpha-v21 does not contain its complete theorem inventory")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise AdvancedLayerExplorerError("malformed Alpha-v21 theorem row")
        if row["name"] in by_name:
            raise AdvancedLayerExplorerError(f"duplicate Alpha-v21 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    graph = json.loads(GLOBAL_DEFINITIONS.read_text(encoding="utf-8"))
    canonical = json.dumps(
        campaign,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if (
        campaign.get("meta", {}).get("current_alpha_version") != "v24"
        or campaign.get("meta", {}).get("current_alpha_checked_use_count")
        != current_alpha.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or graph.get("definition_count") != len(campaign.get("definitions", ()))
        or graph.get("reviewed_definition_count")
        != len(CURRENT_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
        or graph.get("campaign_snapshot_sha256") != _digest(canonical)
    ):
        raise AdvancedLayerExplorerError("the global Alpha-v24 atlas definition artifact is stale")
    blueprint = campaign.get("definitions")
    if not isinstance(blueprint, dict):
        raise AdvancedLayerExplorerError("the global atlas has no named definition registry")
    goals = {item["id"]: item for item in campaign.get("nodes", ())}
    milestone_roots = {
        "T13": ("beta_signed_matrix_minor_exists", "v24"),
        "G101": ("euclidean_gcd_execution_logarithmic_bound", "v23"),
        "G102": ("binary_modular_execution_logarithmic_bound", "v23"),
    }
    milestone_positions = {
        row.name: row.node_id for row in milestone_closure_plan().rows
    }
    research_positions = {row.name: row.node_id for row in research_layer_plan().rows}
    for goal, (root, evidence_version) in milestone_roots.items():
        node = goals.get(goal)
        evidence = node.get("evidence") if isinstance(node, dict) else None
        current_theorem = current_alpha.entry(root, edition="alpha")
        partial = goal == "T13"
        theorem_digest = (
            _digest(current_theorem.spec.statement) if current_theorem is not None else None
        )
        expected_bundle_sha256 = (
            EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256
            if partial
            else EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256
        )
        expected_bundle_node_count = (
            EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
            if partial
            else EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
        )
        expected_node_id = (
            research_positions.get(root)
            if partial
            else milestone_positions.get(root)
        )
        name_key = "partial_theorem_name" if partial else "theorem_name"
        digest_key = (
            "partial_theorem_statement_sha256" if partial else "theorem_statement_sha256"
        )
        if (
            not isinstance(node, dict)
            or node.get("status") != ("open" if partial else "alpha_closed")
            or not isinstance(evidence, dict)
            or evidence.get("implementation")
            != ("independently_closed_partial" if partial else "independently_closed")
            or evidence.get("alpha_version") != evidence_version
            or evidence.get("checked_use") is not (False if partial else True)
            or (partial and evidence.get("partial_component_checked_use") is not True)
            or (not partial and evidence.get("full_empty_context_closure") is not True)
            or evidence.get("independent_lean_bundle_verified") is not True
            or evidence.get(name_key) != root
            or current_theorem is None
            or evidence.get(digest_key) != theorem_digest
            or evidence.get("bundle_sha256") != expected_bundle_sha256
            or evidence.get("bundle_nodes") != expected_bundle_node_count
            or evidence.get("bundle_node_id") != expected_node_id
            or (
                not partial
                and evidence.get("bundle_dependencies")
                != EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT
            )
        ):
            raise AdvancedLayerExplorerError(
                f"advanced milestone lacks its exact historical or independently closed evidence: {goal}"
            )
    if (
        goals["T13"]["evidence"].get("full_arbitrary_signed_matrix_product_proved")
        is not True
        or goals["T13"]["evidence"].get("full_arbitrary_signed_minor_proved")
        is not True
        or goals["T13"]["evidence"].get("signed_four_by_four_determinant_proved")
        is not True
        or goals["T13"]["evidence"].get("full_arbitrary_determinant_proved") is not False
        or goals["G101"]["evidence"].get("formal_logarithmic_bound_proved") is not True
        or goals["G101"]["evidence"].get("terminal_state_identified_with_gcd_proved")
        is not True
        or goals["G101"]["evidence"].get("formal_bit_length_proved") is not True
        or goals["G102"]["evidence"].get("formal_complete_binary_execution_proved")
        is not True
        or goals["G102"]["evidence"].get("formal_bit_length_proved") is not True
        or goals["G102"]["evidence"].get("arbitrary_exponent_binary_digits_proved")
        is not True
        or goals["G102"]["evidence"].get("formal_logarithmic_bound_proved") is not True
    ):
        raise AdvancedLayerExplorerError(
            "a closed advanced milestone omitted its genuine formal endpoint, or open T13 was falsely closed"
        )

    enrollment = alpha_v21_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V21_EXPECTED_COUNT:
        raise AdvancedLayerExplorerError("Alpha-v21 enrollment no longer has exactly 54 checked additions")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise AdvancedLayerExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
        _validate_theorem(
            row,
            spec=spec,
            campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name],
            bundle=bundle,
        )
        current_row = current_alpha.entry(spec.name, edition="alpha")
        if current_row is None or current_row.spec != spec or not current_row.checked_use:
            raise AdvancedLayerExplorerError(
                f"Alpha-v24 lost the exact historically proved Alpha-v21 theorem {spec.name!r}"
            )
    return {
        "catalog": catalog,
        "catalog_sha256": current_digest,
        "historical_catalog_sha256": _digest(raw_catalog),
        "current_edition_identity_sha256": current_alpha.ALPHA_V24_IDENTITY_SHA256,
        "revision": current_digest[:12],
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
    reviewed_links = {
        row["reviewed_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    global_reviewed = {
        row["name"]: row for row in inputs["global_graph"]["reviewed_definitions"]
    }
    routes = {
        definition.name: route
        for route, group in (*NEXT_LAYER_REGISTRIES, *ADVANCED_LAYER_REGISTRIES)
        for definition in group
    }
    by_id: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        if not set(direct) <= set(by_id):
            raise AdvancedLayerExplorerError("the reviewed definition DAG is not dependency-first")
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
                ADVANCED_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
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
                raise AdvancedLayerExplorerError(
                    f"definition {definition.name!r} is not its immutable shared reviewed object"
                )
            reviewed_id = definition.stable_id
            reviewed_route = record["route"]
        if custom and blueprint is not None:
            if tuple(blueprint.get("parameters", ())) != definition.parameters:
                raise AdvancedLayerExplorerError(
                    f"advanced definition {definition.name!r} changed its global argument signature"
                )
            global_name, positions = definition.name, list(range(definition.arity))
            if definition.name == "Beta":
                canonical = _definition_specs()["BetaAt"]
                if (
                    canonical.parameters != definition.parameters
                    or canonical.template_formula != definition.template_formula
                ):
                    raise AdvancedLayerExplorerError("canonical Beta no longer equals reviewed BetaAt")
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
                    raise AdvancedLayerExplorerError(
                        f"the global atlas does not share exact definition {definition.name!r}"
                    )
        elif not custom and definition.name in reviewed_links:
            link = reviewed_links[definition.name]
            if (
                link.get("reviewed_id") != definition.stable_id
                or tuple(link.get("reviewed_parameters", ())) != definition.parameters
            ):
                raise AdvancedLayerExplorerError(
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
            raise AdvancedLayerExplorerError("global definition argument alignment is invalid")
        item = {
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
        by_id[definition.stable_id] = item
        records.append(item)
    return specs, records


def _factory_name(campaign: FrontierV21Campaign) -> str:
    return {
        FrontierV21Campaign.MATRIX_CODED_PRODUCT: "make_matrix_coded_product_candidate_theorems",
        FrontierV21Campaign.EUCLIDEAN_COMPLEXITY: "make_euclidean_complexity_candidate_theorems",
        FrontierV21Campaign.BINARY_MODULAR_EXPONENTIATION: (
            "make_binary_modular_exponentiation_candidate_theorems"
        ),
    }[campaign]


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    enrollment = inputs["enrollment"]
    specs = tuple(
        spec for spec in enrollment.frontier_specs
        if enrollment.campaign_by_name[spec.name] is family.campaign
    )
    if len(specs) != EXPECTED_CAMPAIGN_COUNTS[family.campaign]:
        raise AdvancedLayerExplorerError(f"checked family cardinality changed: {family.slug}")
    definition_specs, definitions = _definition_records(family, inputs)
    compactor = original._FormulaCompactor(definition_specs)
    tags = {spec.name: f"{family.prefix}{index:04X}" for index, spec in enumerate(specs, 1)}
    nodes: list[dict[str, Any]] = []
    for spec in specs:
        row = inputs["by_name"][spec.name]
        closure = row["empty_context_closure"]
        source = enrollment.source_by_name[spec.name]
        nodes.append({
            "id": tags[spec.name],
            "name": spec.name,
            "summary": spec.summary,
            "statement": spec.statement,
            "statement_sha256": row["statement_sha256"],
            "script": list(spec.script),
            "dependencies": list(spec.dependencies),
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
            "alpha_edition_version": "v24",
            "alpha_first_enrolled_version": "v21",
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
            "defined": compactor.compact(spec.statement),
        })
    for name in family.roots:
        if name not in tags:
            raise AdvancedLayerExplorerError(f"published root is absent from checked family: {name}")
    external_names = sorted({
        dependency for node in nodes for dependency in node["dependencies"]
        if dependency not in tags
    })
    external: list[dict[str, Any]] = []
    for name in external_names:
        row = inputs["by_name"].get(name)
        if row is None or row.get("checked_use") is not True:
            raise AdvancedLayerExplorerError(f"unchecked external prerequisite: {name}")
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
            raise AdvancedLayerExplorerError("theorem DAG has a forward or circular dependency")
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
        "milestone_status": inputs["milestones"][family.milestones[-1]]["status"],
        "milestone_checked_use": inputs["milestones"][family.milestones[-1]]["evidence"][
            "checked_use"
        ],
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
        "alpha_edition_version": "v24",
        "alpha_first_enrolled_version": "v21",
        "alpha_edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"],
        "alpha_first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
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
    graph["alpha_edition_version"] = "v24"
    graph["alpha_first_enrolled_version"] = "v21"
    graph["milestone_status"] = corpus["milestone_status"]
    graph["milestone_caveat"] = family.caveat
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            node["alpha_edition_version"] = "v24"
            node["alpha_first_enrolled_version"] = "v21"
    return graph


def _retarget(document: bytes, family: Family, *, include_caveat: bool = False) -> bytes:
    text = document.decode("utf-8")
    text = text.replace("Alpha v20", "Alpha v21")
    text = text.replace("ALPHA v20", "ALPHA v21")
    text = text.replace("Alpha-v20", "Alpha-v21")
    text = text.replace("first admitted v20", "first admitted v21")
    text = text.replace("FIRST ADMITTED v20", "FIRST ADMITTED v21")
    text = text.replace("HISTORICAL v20 FIRST ADMISSION", "HISTORICAL v21 FIRST ADMISSION")
    text = text.replace("590-node bundle", "209-node bundle")
    text = text.replace("all 590 exact bundle nodes", "all 209 exact bundle nodes")
    text = text.replace(" / 590</dd>", " / 209</dd>")
    text = text.replace(
        "The broader T13 milestone remains OPEN: these ten verified matrix and dot-product "
        "components do not prove its full matrix-ring or Cayley–Hamilton target.",
        family.caveat,
    )
    text = text.replace(
        "T13 remains open: this proof is an independently checked "
        "finite matrix/dot-product component, not a proof of the full matrix-ring or "
        "Cayley–Hamilton milestone.",
        family.caveat,
    )
    if family.domain == "D05" and include_caveat:
        text = re.sub(
            r"<p>The broader T13 milestone remains OPEN:.*?</p>",
            f"<p>{_e(family.caveat)}</p>",
            text,
            count=1,
            flags=re.DOTALL,
        )
    if include_caveat and family.domain != "D05":
        marker = '<section class="pd-statement">'
        callout = f'<p class="pd-callout">{_e(family.caveat)}</p>'
        if marker in text:
            text = text.replace(marker, callout + marker, 1)
        elif "</section>\n</main>" in text:
            text = text.replace(
                "</section>\n</main>",
                f'<p class="pd-callout">{_e(family.caveat)}</p></section>\n</main>',
                1,
            )
    return text.encode("utf-8")


def _top_index(
    corpora: Sequence[tuple[Family, Mapping[str, Any]]], *, revision: str
) -> bytes:
    entries = "".join(
        f'<article class="proof-card"><h2><a href="{_versioned(family.slug + "/", revision)}">'
        f"{_e(family.title)}</a></h2><p>{_e(family.description)}</p>"
        f"<p>{corpus['node_count']} independently kernel- and Lean-verified theorems · "
        f"{corpus['definition_count']} conservative definitions</p>"
        f'<p class="pd-callout">{_e(family.caveat)}</p></article>'
        for family, corpus in corpora
    )
    body = f"""<main class="proof-home proof-library-home"><header class="proof-hero">
 <p class="eyebrow">ALPHA v24 · HISTORICAL v21 CONSTRUCTIVE ADVANCED LAYER</p>
 <h1>Three independently checked constructive research campaigns</h1>
 <p>Fifty-four completed intuitionistic Heyting-arithmetic proofs independently accepted by both the original kernel and the compiled Lean verifier, exposed with their exact original scripts, genuine proof DAGs and shared hygienic conservative definitions.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Full number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>Every displayed theorem was independently first admitted in Alpha v21 and retains Alpha-v24 checked-use authority; Stable remains separate. G101 and G102 were fully closed in Alpha v23; arbitrary signed minors and exact four-dimensional determinants are proved in Alpha v24, while T13 remains open for arbitrary-dimensional determinants, rank, and lattice foundations.</p></main>"""
    return original._document(
        FAMILIES[0],
        title="Constructive Advanced-Layer Proof Library",
        body=body,
        prefix="",
        defined=False,
    )


def build_files() -> dict[str, bytes]:
    """Return exact proof-reading assets without loading the proof bundle."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise AdvancedLayerExplorerError(f"reviewed shared explorer asset changed: {name}")
        files[f"assets/{name}"] = payload

    built: list[tuple[Family, Mapping[str, Any]]] = []
    for family in FAMILIES:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        prefix = family.slug
        files[f"{prefix}/index.html"] = render_canonical_family_landing(
            family,
            corpus,
            revision=revision,
            current_alpha_version="v24",
            first_admitted_version="v21",
            bundle_node_count=EXPECTED_BUNDLE_NODE_COUNT,
        )
        files[f"{prefix}/api/corpus.json"] = _json(corpus)
        files[f"{prefix}/explorer/index.html"] = original._inject_atlas_navigation(
            render_exact_index(
                family,
                corpus,
                corpus["tags"],
                corpus["layers"],
                stylesheet_href=_asset("exact-explorer.css", "../../"),
                script_href=_asset("exact-explorer.js", "../../"),
                html_revision=revision,
            ),
            family,
            prefix="../../",
            revision=revision,
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
            files[f"{prefix}/explorer/tag/{tag}.html"] = original._inject_atlas_navigation(
                render_exact_theorem(
                    family,
                    corpus,
                    node,
                    corpus["tags"],
                    corpus["layers"],
                    stylesheet_href=_asset("exact-explorer.css", "../../../"),
                    script_href=_asset("exact-explorer.js", "../../../"),
                    html_revision=revision,
                ),
                family,
                prefix="../../../",
                revision=revision,
                goal=node["campaign_milestone"],
            )
            files[f"{prefix}/explorer/defined/tag/{tag}.html"] = _retarget(
                original._defined_theorem(family, corpus, node, revision=revision),
                family,
                include_caveat=True,
            )
        for definition in corpus["definitions"]:
            files[f"{prefix}/explorer/defined/definition/{definition['id']}.html"] = (
                original._defined_definition(family, corpus, definition, revision=revision)
            )
        built.append((family, corpus))
    files["index.html"] = _top_index(built, revision=revision)
    inventory = [
        {"path": name, "bytes": len(payload), "sha256": _digest(payload)}
        for name, payload in sorted(files.items())
    ]
    manifest = {
        "schema": f"{SCHEMA}-manifest",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_edition_version": "v24",
        "alpha_first_enrolled_version": "v21",
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": EXPECTED_BUNDLE_NODE_COUNT,
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "domain": family.domain,
                "family": family.family_id,
                "milestones": list(family.milestones),
                "milestone_status": corpus["milestone_status"],
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
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file()
    }
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
        print(f"constructive advanced-layer explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive advanced-layer explorer is stale", file=sys.stderr)
            return 1
        print(f"constructive advanced-layer explorer: {len(files)} files, 54 checked theorems")
        return 0
    _write(options.output, files)
    print(f"constructive advanced-layer explorer: wrote {len(files)} files, 54 checked theorems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
