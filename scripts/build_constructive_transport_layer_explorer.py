#!/usr/bin/env python3
"""Publish three historical Alpha-v22 proof families under current v30 authority.

The static presentation authenticates the complete sealed original-kernel
transport-layer bundle and its independent compiled-Lean-verifier receipt. It
only stream-hashes that artifact: it never decodes, replays, or trusts a proof
bundle as an alternative source of theorem authority.

Every notation graph reuses exact, hygienic reviewed first-order definitions.
Full unique bit length, Euclidean terminal/gcd identification, and supplied-
digit-prefix execution correctness retain their exact historical Alpha-v22
proof evidence. The broader G101/G102 milestones were open in that edition
and were independently, completely closed in historical Alpha v23.
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
from constructive_frontier_exact_explorer import (  # noqa: E402
    render_exact_index,
    render_exact_theorem,
)
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as CURRENT_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS_BY_NAME,
    NEXT_LAYER_REGISTRIES,
)
from constructive_proof_explorer_template import (  # noqa: E402
    render_canonical_family_landing,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_REGISTRIES,
)
from peano_lab.library import editions_v21 as v21  # noqa: E402
from peano_lab.library import editions_v22 as v22  # noqa: E402
from peano_lab.library import editions_v30 as current_alpha  # noqa: E402
from peano_lab.library.alpha_enrollment_v22 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V22_EXPECTED_COUNT,
    FRONTIER_V22_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V21_COUNT,
    FrontierV22Campaign,
    alpha_v22_enrollment,
)
from peano_lab.library.campaign_transport_layer_closure import (  # noqa: E402
    EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT,
)
from peano_lab.library.campaign_milestone_closure import (  # noqa: E402
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256,
    milestone_closure_plan,
)
from peano_lab.library.defined_syntax import DefinitionSpec  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "constructive-transport-layer-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v22.json"
PARENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v21.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v30.json"
CURRENT_CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v30.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-gaussian-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_ALPHA_COUNT = 1_890
EXPECTED_STABLE_COUNT = 432
EXPECTED_REVIEWED_DEFINITION_COUNT = 89
EXPECTED_BUNDLE_PATH = (
    "research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json"
)
SCHEMA = "peano-lab-constructive-transport-layer-explorer-v1"
STATUS = (
    "Alpha v30 checked-use · first admitted v22 · "
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


class TransportLayerExplorerError(ValueError):
    """An independently sealed Alpha-v22 theorem, definition, or goal changed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV22Campaign
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
        slug="binary-length",
        campaign=FrontierV22Campaign.BINARY_LENGTH,
        prefix="BL",
        title="Constructive binary length and powers of two",
        kicker="Unique binary digits · strictly increasing powers · full unique bit length",
        description=(
            "Twenty-one independently checked constructive theorems prove unique binary "
            "digit decomposition, strict power-of-two growth, and existence and uniqueness "
            "of the exact canonical bit length for every natural number."
        ),
        formula="BitLen(0,1) · n>0 ⇒ 2^(ℓ−1)≤n<2^ℓ · ∀n ∃!ℓ BitLen(n,ℓ)",
        domain="D04",
        family_id="F11",
        milestones=("G101", "G102"),
        roots=(
            "binary_length_exists",
            "binary_length_functional",
            "binary_length_power_exact",
            "binary_length_exists_unique",
        ),
        definitions=(
            "PowTwo",
            "BinaryDigit",
            "BitLen",
            "BinaryExponentSplit",
            "Le",
            "Lt",
        ),
        caveat=(
            "G101 and G102 were OPEN when these BitLen foundations were first admitted "
            "in Alpha v22. Both are now CLOSED in Alpha v23: complete canonical "
            "exponent digits and both exact logarithmic execution bounds are proved."
        ),
    ),
    Family(
        slug="euclidean-gcd-transport",
        campaign=FrontierV22Campaign.EUCLIDEAN_GCD_TRANSPORT,
        prefix="GT",
        title="Constructive Euclidean gcd transport and anchored traces",
        kicker="Common-divisor invariance · terminal-state identification · anchored linear bound",
        description=(
            "Twenty independently checked constructive theorems transport divisibility "
            "and gcd invariants through actual Euclidean steps, identify the terminal "
            "history state with its gcd, and establish a complete anchored linear bound."
        ),
        formula="gcd(a,b)=gcd(b,a mod b) · terminal(a,b)=gcd(a,b) · steps≤b",
        domain="D04",
        family_id="F11",
        milestones=("G101",),
        roots=(
            "euclidean_trace_terminal_gcd_exists",
            "euclidean_execution_terminal_identified",
            "euclidean_anchored_execution_exists",
            "euclidean_anchored_execution_linear_bound",
        ),
        definitions=(
            "EuclideanCommonDivisor",
            "EuclideanStateAt",
            "EuclideanAnchoredExecution",
            "EuclideanDivision",
            "EuclideanHalving",
            "EuclideanExecution",
            "ContinuedFractionTrace",
            "IsGCD",
            "BitLen",
        ),
        caveat=(
            "G101 was OPEN at this family's Alpha-v22 first admission: its complete "
            "anchored trace and actual terminal gcd were proved but its logarithmic "
            "bound was not. G101 is now CLOSED in Alpha v23, including the exact "
            "first-order bound steps≤2*BitLen(b)+1."
        ),
    ),
    Family(
        slug="binary-modular-execution",
        campaign=FrontierV22Campaign.BINARY_MODULAR_EXECUTION,
        prefix="BE",
        title="Constructive binary modular execution and power correctness",
        kicker="Complete beta-coded traces · Horner power invariants · unique modular output",
        description=(
            "Nineteen independently checked constructive theorems build complete "
            "square-and-multiply traces for any supplied valid beta-coded digit prefix, "
            "prove the exact Horner/exponent power invariant, and give a unique result."
        ),
        formula="digits∈{0,1} · rᵢ₊₁≡rᵢ²a^digitᵢ (mod m) · r≡a^Horner(digits)",
        domain="D04",
        family_id="F11",
        milestones=("G102",),
        roots=(
            "binary_execution_prefix_exists",
            "binary_modular_execution_exists",
            "binary_modular_execution_power_correct",
            "binary_modular_execution_horner_exists",
            "binary_modular_execution_result_exists_unique",
        ),
        definitions=(
            "BinaryDigitPrefix",
            "BinaryExecutionTrace",
            "BinaryModularExecution",
            "BinaryExecutionPowerInvariant",
            "BinaryModulus",
            "BinaryExponentSplit",
            "CanonicalModularResidue",
            "BinaryModularStep",
            "BinaryModularPower",
            "Horner",
            "BitLen",
        ),
        caveat=(
            "G102 was OPEN at this family's Alpha-v22 first admission: complete "
            "execution was proved only for a supplied valid beta-coded digit prefix. "
            "G102 is now CLOSED in Alpha v23 for every arbitrary exponent, with "
            "actual canonical digits and operations≤3*BitLen(e)+2."
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
    ):
        raise TransportLayerExplorerError("the immutable reviewed constructive registry changed")
    for definition in definitions.values():
        dependencies = definition.conceptual_dependencies
        if (
            len(dependencies) != len(set(dependencies))
            or definition.name in dependencies
            or not set(dependencies) <= set(definitions)
        ):
            raise TransportLayerExplorerError(
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
            raise TransportLayerExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise TransportLayerExplorerError(f"unknown constructive definition {name!r}")
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
    campaign: FrontierV22Campaign,
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
        raise TransportLayerExplorerError(f"exact checked Alpha-v22 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v22_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "transport_layer"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "transport_layer"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise TransportLayerExplorerError(
            f"theorem lacks its original-kernel dependency-closed proof: {spec.name}"
        )


def _load_inputs() -> dict[str, Any]:
    """Authenticate v22 first admission, current v30, Lean receipts, and DAG."""

    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v22"
        or catalog.get("theorem_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("checked_use_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v22.ALPHA_V22_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v22.ALPHA_V22_ENROLLMENT_SHA256
        or catalog.get("frontier_v22_campaign_counts") != expected_counts
        or catalog.get("frontier_v22_ordered_names_sha256")
        != FRONTIER_V22_EXPECTED_NAMES_SHA256
    ):
        raise TransportLayerExplorerError("the sealed fully checked Alpha-v22 catalog changed")
    parent = catalog.get("parent_alpha_v21")
    if (
        not isinstance(parent, dict)
        or parent.get("schema") != "peano-library-alpha-snapshot-v21"
        or parent.get("theorem_count") != PARENT_ALPHA_V21_COUNT
        or parent.get("edition_identity_sha256") != v21.ALPHA_V21_IDENTITY_SHA256
        or not isinstance(parent.get("artifacts"), dict)
        or not isinstance(parent["artifacts"].get("catalog"), dict)
        or parent["artifacts"]["catalog"].get("sha256") != _file_digest(PARENT_CATALOG)
    ):
        raise TransportLayerExplorerError("Alpha-v22 lost its exact immutable Alpha-v21 parent")
    promotion = catalog.get("alpha_v22_transport_layer_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V22_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("parent_theorem_count") != PARENT_ALPHA_V21_COUNT
        or promotion.get("independent_lean_bundle_verified") is not True
    ):
        raise TransportLayerExplorerError(
            "Alpha-v22 lacks complete independently kernel- and Lean-verified admission evidence"
        )
    bundle = promotion.get("proof_bundle")
    if (
        EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT <= 0
        or not isinstance(bundle, dict)
        or bundle.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle.get("node_count") != EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V22_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT - FRONTIER_V22_EXPECTED_COUNT - 1
        or bundle.get("independent_lean_bundle_verified") is not True
    ):
        raise TransportLayerExplorerError(
            "Alpha-v22 lacks its exact independently Lean-verified proof receipt"
        )
    artifact = (REPO / EXPECTED_BUNDLE_PATH).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise TransportLayerExplorerError("the sealed transport proof-bundle bytes changed")

    channels = json.loads(CURRENT_CHANNELS.read_text(encoding="utf-8"))
    current = channels.get("channels", {}).get("alpha", {})
    current_raw_catalog = CURRENT_CATALOG.read_bytes()
    current_digest = _digest(current_raw_catalog)
    if current_digest != original.EXPECTED_CURRENT_CATALOG_SHA256:
        raise TransportLayerExplorerError("the current immutable Alpha-v30 catalog bytes changed or remain unsealed")
    current_catalog = json.loads(current_raw_catalog)
    original._audit_current_parent(current_catalog, channels, error_type=TransportLayerExplorerError)
    if (
        channels.get("schema") != "peano-library-channels-v30"
        or channels.get("default_channel") != "stable"
        or channels.get("parent_channels_v29", {}).get("path")
        != "artifacts/peano-library/channels-v29.json"
        or channels.get("parent_channels_v29", {}).get("sha256")
        != _file_digest(CURRENT_CHANNELS.with_name("channels-v29.json"))
        or current.get("artifact_path") != "artifacts/peano-library/alpha/catalog-v30.json"
        or current.get("artifact_sha256") != current_digest
        or current.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current.get("checked_use_count")
        != current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or current.get("edition_identity_sha256") != current_alpha.ALPHA_V30_IDENTITY_SHA256
        or current.get("ordered_enrollment_root_sha256")
        != current_alpha.ALPHA_V30_ENROLLMENT_SHA256
        or current.get("parent_alpha_v22_sha256") != _digest(raw_catalog)
        or current_catalog.get("schema") != "peano-library-alpha-snapshot-v30"
        or current_catalog.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog.get("checked_use_count") != current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or current_catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or current_catalog.get("edition_identity_sha256") != current_alpha.ALPHA_V30_IDENTITY_SHA256
        or current_catalog.get("ordered_enrollment_root_sha256") != current_alpha.ALPHA_V30_ENROLLMENT_SHA256
        or not isinstance(current_catalog.get("theorems"), list)
        or len(current_catalog["theorems"]) != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog["theorems"][:EXPECTED_ALPHA_COUNT] != catalog.get("theorems")
        or tuple(current_alpha.ALPHA_ENTRIES[:EXPECTED_ALPHA_COUNT]) != v22.ALPHA_ENTRIES
        or any(
            newer is not historical
            for newer, historical in zip(current_alpha.ALPHA_ENTRIES, v22.ALPHA_ENTRIES)
        )
    ):
        raise TransportLayerExplorerError(
            "the current immutable Alpha-v30 release changed its exact Alpha-v22 first admission"
        )

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != EXPECTED_ALPHA_COUNT:
        raise TransportLayerExplorerError("Alpha-v22 does not contain its complete theorem inventory")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise TransportLayerExplorerError("malformed Alpha-v22 theorem row")
        if row["name"] in by_name:
            raise TransportLayerExplorerError(f"duplicate Alpha-v22 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    graph = json.loads(GLOBAL_DEFINITIONS.read_text(encoding="utf-8"))
    original._audit_current_atlas(campaign, graph, error_type=TransportLayerExplorerError)
    blueprint = campaign.get("definitions")
    if not isinstance(blueprint, dict):
        raise TransportLayerExplorerError("the global atlas has no named definition registry")
    goals = {item["id"]: item for item in campaign.get("nodes", ())}
    closed_roots = {
        "G101": "euclidean_gcd_execution_logarithmic_bound",
        "G102": "binary_modular_execution_logarithmic_bound",
    }
    milestone_positions = {row.name: row.node_id for row in milestone_closure_plan().rows}
    for goal, root in closed_roots.items():
        node = goals.get(goal)
        evidence = node.get("evidence") if isinstance(node, dict) else None
        theorem = current_alpha.entry(root, edition="alpha")
        if (
            not isinstance(node, dict)
            or node.get("status") != "alpha_closed"
            or not isinstance(evidence, dict)
            or evidence.get("implementation") != "independently_closed"
            or evidence.get("alpha_version") != "v23"
            or evidence.get("checked_use") is not True
            or evidence.get("full_empty_context_closure") is not True
            or evidence.get("independent_lean_bundle_verified") is not True
            or evidence.get("theorem_name") != root
            or theorem is None
            or evidence.get("theorem_statement_sha256") != _digest(theorem.spec.statement)
            or evidence.get("bundle_sha256") != EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256
            or evidence.get("bundle_nodes") != EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
            or evidence.get("bundle_dependencies") != EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT
            or evidence.get("bundle_node_id") != milestone_positions.get(root)
        ):
            raise TransportLayerExplorerError(
                f"closed transport milestone lacks its exact independently proved Alpha-v23 root: {goal}"
            )
    euclidean = goals["G101"]["evidence"]
    binary = goals["G102"]["evidence"]
    if (
        euclidean.get("formal_bit_length_proved") is not True
        or euclidean.get("terminal_state_identified_with_gcd_proved") is not True
        or euclidean.get("formal_logarithmic_bound_proved") is not True
        or binary.get("formal_bit_length_proved") is not True
        or binary.get("formal_complete_binary_execution_proved") is not True
        or binary.get("arbitrary_exponent_binary_digits_proved") is not True
        or binary.get("formal_logarithmic_bound_proved") is not True
    ):
        raise TransportLayerExplorerError(
            "a closed transport milestone omitted its exact proved formal endpoint"
        )

    enrollment = alpha_v22_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V22_EXPECTED_COUNT:
        raise TransportLayerExplorerError("Alpha-v22 enrollment no longer has 60 checked additions")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise TransportLayerExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
        _validate_theorem(
            row,
            spec=spec,
            campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name],
            bundle=bundle,
        )
    return {
        "catalog": catalog,
        "current_catalog": current_catalog,
        "catalog_sha256": current_digest,
        "historical_catalog_sha256": _digest(raw_catalog),
        "current_edition_identity_sha256": current_alpha.ALPHA_V30_IDENTITY_SHA256,
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
        )
        for definition in group
    }
    by_id: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        if not set(direct) <= set(by_id):
            raise TransportLayerExplorerError("the reviewed definition DAG is not dependency-first")
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
                TRANSPORT_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
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
                raise TransportLayerExplorerError(
                    f"definition {definition.name!r} is not its immutable shared reviewed object"
                )
            reviewed_id = definition.stable_id
            reviewed_route = record["route"]
        if custom and blueprint is not None:
            if tuple(blueprint.get("parameters", ())) != definition.parameters:
                raise TransportLayerExplorerError(
                    f"transport definition {definition.name!r} changed its global argument signature"
                )
            global_name, positions = definition.name, list(range(definition.arity))
            if definition.name == "Beta":
                canonical = _definition_specs()["BetaAt"]
                if (
                    canonical.parameters != definition.parameters
                    or canonical.template_formula != definition.template_formula
                ):
                    raise TransportLayerExplorerError("canonical Beta no longer equals reviewed BetaAt")
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
                    raise TransportLayerExplorerError(
                        f"the global atlas does not share exact definition {definition.name!r}"
                    )
        elif not custom and definition.name in reviewed_links:
            link = reviewed_links[definition.name]
            if (
                link.get("reviewed_id") != definition.stable_id
                or tuple(link.get("reviewed_parameters", ())) != definition.parameters
            ):
                raise TransportLayerExplorerError(
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
            raise TransportLayerExplorerError("global definition argument alignment is invalid")
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


def _factory_name(campaign: FrontierV22Campaign) -> str:
    return {
        FrontierV22Campaign.BINARY_LENGTH: "make_binary_length_candidate_theorems",
        FrontierV22Campaign.EUCLIDEAN_GCD_TRANSPORT: (
            "make_euclidean_gcd_transport_candidate_theorems"
        ),
        FrontierV22Campaign.BINARY_MODULAR_EXECUTION: (
            "make_binary_modular_execution_candidate_theorems"
        ),
    }[campaign]


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    enrollment = inputs["enrollment"]
    specs = tuple(
        spec for spec in enrollment.frontier_specs
        if enrollment.campaign_by_name[spec.name] is family.campaign
    )
    if len(specs) != EXPECTED_CAMPAIGN_COUNTS[family.campaign]:
        raise TransportLayerExplorerError(f"checked family cardinality changed: {family.slug}")
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
            "alpha_edition_version": "v30",
            "alpha_first_enrolled_version": "v22",
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
            raise TransportLayerExplorerError(f"published root is absent from checked family: {name}")
    external_names = sorted({
        dependency for node in nodes for dependency in node["dependencies"]
        if dependency not in tags
    })
    external: list[dict[str, Any]] = []
    for name in external_names:
        row = inputs["by_name"].get(name)
        if row is None or row.get("checked_use") is not True:
            raise TransportLayerExplorerError(f"unchecked external prerequisite: {name}")
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
            raise TransportLayerExplorerError("theorem DAG has a forward or circular dependency")
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
        "alpha_edition_version": "v30",
        "alpha_first_enrolled_version": "v22",
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
    graph["alpha_edition_version"] = "v30"
    graph["alpha_first_enrolled_version"] = "v22"
    graph["milestone_status"] = corpus["milestone_status"]
    graph["milestone_caveat"] = family.caveat
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            node["alpha_edition_version"] = "v30"
            node["alpha_first_enrolled_version"] = "v22"
    return graph


def _retarget(document: bytes, family: Family, *, include_caveat: bool = False) -> bytes:
    text = document.decode("utf-8")
    old_caveat = (
        "Every displayed theorem was first admitted in Alpha v20, remains independently "
        "kernel- and Lean-verified for current Alpha v30 checked use, and has not been "
        "promoted to Stable."
    )
    text = text.replace(old_caveat, family.caveat)
    text = text.replace("first admitted v20", "first admitted v22")
    text = text.replace("FIRST ADMITTED v20", "FIRST ADMITTED v22")
    text = text.replace("First admission</dt><dd>Alpha v20", "First admission</dt><dd>Alpha v22")
    text = text.replace("Alpha v21", "Alpha v22")
    text = text.replace("ALPHA v21", "ALPHA v22")
    text = text.replace("Alpha-v21", "Alpha-v22")
    text = text.replace("Alpha v20", "Alpha v22")
    text = text.replace("ALPHA v20", "ALPHA v22")
    text = text.replace("Alpha-v20", "Alpha-v22")
    count = EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT
    text = text.replace("590-node bundle", f"{count}-node bundle")
    text = text.replace("all 590 exact bundle nodes", f"all {count} exact bundle nodes")
    text = text.replace(" / 590</dd>", f" / {count}</dd>")
    if include_caveat:
        marker = '<section class="pd-statement">'
        callout = f'<p class="pd-callout">{_e(family.caveat)}</p>'
        if marker in text:
            text = text.replace(marker, callout + marker, 1)
        elif family.caveat not in text and "</section>\n</main>" in text:
            text = text.replace(
                "</section>\n</main>",
                f"{callout}</section>\n</main>",
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
 <p class="eyebrow">ALPHA v30 · HISTORICAL v22 CONSTRUCTIVE TRANSPORT LAYER</p>
 <h1>Three independently checked constructive research campaigns</h1>
 <p>Sixty completed intuitionistic Heyting-arithmetic proofs independently accepted by both the original kernel and the compiled Lean verifier: full unique bit length, terminal-correct Euclidean traces, and exact beta-coded modular executions.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Full number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>Every displayed theorem was first admitted in Alpha v22 and retains Alpha-v30 checked-use authority; Stable remains separate. Both formerly open logarithmic milestones G101 and G102 were completely proved in historical Alpha v23.</p></main>"""
    return original._document(
        FAMILIES[0],
        title="Constructive Transport-Layer Proof Library",
        body=body,
        prefix="",
        defined=False,
    )


def build_files() -> dict[str, bytes]:
    """Build exact proof-reading assets without opening a proof bundle."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise TransportLayerExplorerError(f"reviewed shared explorer asset changed: {name}")
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
            current_alpha_version="v30",
            first_admitted_version="v22",
            bundle_node_count=EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT,
        )
        files[f"{prefix}/api/corpus.json"] = _json(corpus)
        files[f"{prefix}/explorer/index.html"] = _retarget(
            original._inject_atlas_navigation(
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
            ),
            family,
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
                ),
                family,
            )
            files[f"{prefix}/explorer/defined/tag/{tag}.html"] = _retarget(
                original._defined_theorem(family, corpus, node, revision=revision),
                family,
                include_caveat=True,
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
        "alpha_first_enrolled_version": "v22",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT,
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "alpha_edition_version": "v30",
                "alpha_first_enrolled_version": "v22",
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
        print(f"constructive transport-layer explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive transport-layer explorer is stale", file=sys.stderr)
            return 1
        print(
            f"constructive transport-layer explorer: {len(files)} files, "
            f"{FRONTIER_V22_EXPECTED_COUNT} checked theorems"
        )
        return 0
    _write(options.output, files)
    print(
        f"constructive transport-layer explorer: wrote {len(files)} files, "
        f"{FRONTIER_V22_EXPECTED_COUNT} checked theorems"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
