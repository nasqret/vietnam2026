#!/usr/bin/env python3
"""Publish historical Alpha-v23 families under current Alpha-v30 authority.

The immutable first-admission Alpha-v23 catalog retains its exact original-
kernel/independent-Lean proof certificate.  Current checked-use authority is
separately authenticated against the sealed additive Alpha-v30 child.  Proof
artifacts are streaming-digested only; presentation never replays or decodes
them, changes a historical bundle node, or substitutes documentation for proof.
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
from constructive_milestone_closure_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
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
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as CURRENT_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_REGISTRIES,
)
from peano_lab.library import editions_v22 as v22  # noqa: E402
from peano_lab.library import editions_v23 as v23  # noqa: E402
from peano_lab.library import editions_v30 as current_alpha  # noqa: E402
from peano_lab.library.alpha_enrollment_v23 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V23_EXPECTED_COUNT,
    FRONTIER_V23_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V22_COUNT,
    FrontierV23Campaign,
    alpha_v23_enrollment,
)
from peano_lab.library.campaign_milestone_closure import (  # noqa: E402
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
)
from peano_lab.library.defined_syntax import DefinitionSpec  # noqa: E402


OUTPUT = REPO / "book" / "_static" / "constructive-milestone-closure-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v23.json"
PARENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v22.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v30.json"
CURRENT_CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v30.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-gaussian-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_ALPHA_COUNT = 1_949
EXPECTED_STABLE_COUNT = 432
EXPECTED_REVIEWED_DEFINITION_COUNT = 97
EXPECTED_COMPATIBLE_DEFINITION_COUNT = 88
EXPECTED_BUNDLE_PATH = (
    "research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json"
)
SCHEMA = "peano-lab-constructive-milestone-closure-explorer-v1"
STATUS = (
    "Alpha v30 checked-use · first admitted v23 · "
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


class MilestoneClosureExplorerError(ValueError):
    """An exact Alpha-v23 theorem, conservative definition, or closed goal changed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV23Campaign
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
        slug="euclidean-logarithmic-bound",
        campaign=FrontierV23Campaign.EUCLIDEAN_LOGARITHMIC_BOUND,
        prefix="EL",
        title="Certified logarithmic Euclidean algorithm",
        kicker="G101 fully proved · actual beta histories · terminal gcd · logarithmic complexity",
        description=(
            "Seventeen independently checked constructive theorems perform genuine power-of-two "
            "induction over actual Euclidean divisions, identify the encoded terminal gcd, "
            "and establish the exact formal logarithmic complexity bound."
        ),
        formula="∀a b ℓ. BitLen(b,ℓ) ⇒ ∃g k. AnchoredEuclid(a,b,g,k) ∧ k≤2ℓ+1",
        domain="D04",
        family_id="F11",
        milestones=("G101",),
        roots=(
            "euclidean_log_trace_below_power",
            "euclidean_log_trace_bound",
            "euclidean_log_execution_strong",
            "euclidean_gcd_execution_logarithmic_bound",
            "euclidean_gcd_execution_logarithmic_exists",
        ),
        definitions=(
            "EuclideanBoundedTrace",
            "EuclideanLogarithmicExecution",
            "EuclideanDivision",
            "EuclideanHalving",
            "EuclideanAnchoredExecution",
            "EuclideanStateAt",
            "ContinuedFractionTrace",
            "IsGCD",
            "PowTwo",
            "BitLen",
            "Le",
            "Lt",
        ),
        caveat=(
            "The exact G101 milestone is fully proved, including the stronger checked "
            "bound k≤2·BitLen(b), a real beta-coded execution, and its actual terminal "
            "gcd. The independent T13 determinant/rank/integer-span substrate is "
            "now closed in the separate Alpha-v27 integer-linear-algebra branch."
        ),
    ),
    Family(
        slug="binary-digit-extraction",
        campaign=FrontierV23Campaign.BINARY_DIGIT_EXTRACTION,
        prefix="BD",
        title="Canonical binary digits and certified repeated squaring",
        kicker="G102 fully proved · arbitrary exponents · actual digit codes · exact cost bound",
        description=(
            "Twenty-four independently checked constructive theorems extract canonical "
            "beta-coded binary digits from every exponent, execute a genuine square-and-" 
            "multiply trace, prove its modular-power result, and certify the exact "
            "logarithmic operation bound."
        ),
        formula="∀a e m>1. ∃r k. BinaryPow(a,e,m,r,k) ∧ r≡aᵉ (mod m) ∧ k≤3·BitLen(e)+2",
        domain="D04",
        family_id="F11",
        milestones=("G102",),
        roots=(
            "binary_exponent_digit_prefix_exists",
            "binary_digit_operation_count_bound",
            "binary_modular_exponent_coded_execution_exists",
            "binary_modular_exponent_coded_execution_exists_unique",
            "binary_modular_execution_bitlength_bound",
            "binary_modular_execution_logarithmic_bound",
        ),
        definitions=(
            "BinaryExponentDigitCode",
            "BinaryCanonicalExponentDigitCode",
            "BinaryCompleteModularExecution",
            "BinaryExecutionOperationCount",
            "BitLen",
            "PowTwo",
            "BinaryDigitPrefix",
            "BinaryExecutionTrace",
            "BinaryModularExecution",
            "BinaryModularPower",
            "BinaryModularStep",
            "BinaryModulus",
            "Horner",
            "AllBits",
            "BitCount",
            "Le",
            "Lt",
        ),
        caveat=(
            "The exact G102 milestone is fully proved for every natural exponent and "
            "every modulus greater than one, including actual canonical digits, a "
            "beta-coded accumulator execution, modular-power correctness, and the "
            "formal bound k≤3·BitLen(e)+2. The independent T13 determinant/rank/"
            "integer-span substrate is now closed in the separate Alpha-v27 "
            "integer-linear-algebra branch."
        ),
    ),
    Family(
        slug="primes-three-mod-four",
        campaign=FrontierV23Campaign.PRIMES_THREE_MOD_FOUR,
        prefix="TF",
        title="Infinitely many primes three modulo four",
        kicker="G025 fully proved · constructive factor search · subtraction-free Euclid witnesses",
        description=(
            "Eighteen independently checked constructive theorems combine finite "
            "factorization, two-square obstructions, a subtraction-free Euclid "
            "construction, and actual bounded prime-divisor search to produce "
            "arbitrarily large primes congruent to three modulo four."
        ),
        formula="∀B. ∃p q. Prime(p) ∧ B<p ∧ p=4q+3",
        domain="D02",
        family_id="F03",
        milestones=("G025",),
        roots=(
            "positive_number_with_admissible_prime_divisors_is_two_square",
            "three_mod_four_prime_divisor_exists",
            "euclid_three_progression_prime_exists",
            "euclid_three_prime_divisor_exceeds_bound",
            "infinitely_many_primes_three_mod_four",
        ),
        definitions=(
            "PrimeThreeModFourDivisor",
            "EuclidThreeNumber",
            "Prime",
            "Mod4Three",
            "Dvd",
            "AllPrime",
            "Product",
            "Beta",
            "Le",
            "Lt",
        ),
        caveat=(
            "The exact G025 progression-prime milestone is fully proved in unchanged "
            "constructive arithmetic; Mod4Three deliberately reuses its existing "
            "Quadratic Reciprocity definition PD0012. The much stronger full "
            "Dirichlet progression-prime milestone G030 remains open."
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
        raise MilestoneClosureExplorerError("the additive reviewed constructive registry changed")
    for definition in definitions.values():
        dependencies = definition.conceptual_dependencies
        if (
            len(dependencies) != len(set(dependencies))
            or definition.name in dependencies
            or not set(dependencies) <= set(definitions)
        ):
            raise MilestoneClosureExplorerError(
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
            raise MilestoneClosureExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise MilestoneClosureExplorerError(f"unknown constructive definition {name!r}")
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
    campaign: FrontierV23Campaign,
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
        raise MilestoneClosureExplorerError(f"exact checked Alpha-v23 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v23_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "milestone_closure"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "milestone_closure"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise MilestoneClosureExplorerError(
            f"theorem lacks its complete original-kernel dependency-closed proof: {spec.name}"
        )


def _load_inputs() -> dict[str, Any]:
    """Authenticate v23 first admission, current v30, Lean proofs, and closed goals."""

    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        FRONTIER_V23_EXPECTED_COUNT <= 0
        or catalog.get("schema") != "peano-library-alpha-snapshot-v23"
        or catalog.get("theorem_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("checked_use_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v23.ALPHA_V23_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v23.ALPHA_V23_ENROLLMENT_SHA256
        or catalog.get("frontier_v23_campaign_counts") != expected_counts
        or catalog.get("frontier_v23_ordered_names_sha256")
        != FRONTIER_V23_EXPECTED_NAMES_SHA256
    ):
        raise MilestoneClosureExplorerError("the sealed fully checked Alpha-v23 catalog changed")
    parent = catalog.get("parent_alpha_v22")
    if (
        not isinstance(parent, dict)
        or parent.get("schema") != "peano-library-alpha-snapshot-v22"
        or parent.get("theorem_count") != PARENT_ALPHA_V22_COUNT
        or parent.get("edition_identity_sha256") != v22.ALPHA_V22_IDENTITY_SHA256
        or not isinstance(parent.get("artifacts"), dict)
        or not isinstance(parent["artifacts"].get("catalog"), dict)
        or parent["artifacts"]["catalog"].get("sha256") != _file_digest(PARENT_CATALOG)
    ):
        raise MilestoneClosureExplorerError("Alpha-v23 lost its exact immutable Alpha-v22 parent")
    promotion = catalog.get("alpha_v23_milestone_closure_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V23_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("parent_theorem_count") != PARENT_ALPHA_V22_COUNT
        or promotion.get("independent_lean_bundle_verified") is not True
    ):
        raise MilestoneClosureExplorerError(
            "Alpha-v23 lacks complete independently kernel- and Lean-verified admission evidence"
        )
    bundle = promotion.get("proof_bundle")
    if (
        EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT <= 0
        or not isinstance(bundle, dict)
        or bundle.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle.get("node_count") != EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V23_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT - FRONTIER_V23_EXPECTED_COUNT - 1
        or bundle.get("independent_lean_bundle_verified") is not True
    ):
        raise MilestoneClosureExplorerError(
            "Alpha-v23 lacks its exact independently Lean-verified proof receipt"
        )
    artifact = (REPO / EXPECTED_BUNDLE_PATH).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise MilestoneClosureExplorerError("the sealed milestone-closure proof-bundle bytes changed")

    channels = json.loads(CURRENT_CHANNELS.read_text(encoding="utf-8"))
    current = channels.get("channels", {}).get("alpha", {})
    current_raw_catalog = CURRENT_CATALOG.read_bytes()
    current_digest = _digest(current_raw_catalog)
    if current_digest != original.EXPECTED_CURRENT_CATALOG_SHA256:
        raise MilestoneClosureExplorerError("the current immutable Alpha-v30 catalog bytes changed or remain unsealed")
    current_catalog = json.loads(current_raw_catalog)
    original._audit_current_parent(current_catalog, channels, error_type=MilestoneClosureExplorerError)
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
        or current.get("parent_alpha_v23_sha256") != _digest(raw_catalog)
        or current_catalog.get("schema") != "peano-library-alpha-snapshot-v30"
        or current_catalog.get("theorem_count") != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog.get("checked_use_count") != current_alpha.EXPECTED_ALPHA_V30_CHECKED_USE_COUNT
        or current_catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or current_catalog.get("edition_identity_sha256") != current_alpha.ALPHA_V30_IDENTITY_SHA256
        or current_catalog.get("ordered_enrollment_root_sha256") != current_alpha.ALPHA_V30_ENROLLMENT_SHA256
        or not isinstance(current_catalog.get("theorems"), list)
        or len(current_catalog["theorems"]) != current_alpha.EXPECTED_ALPHA_V30_COUNT
        or current_catalog["theorems"][:EXPECTED_ALPHA_COUNT] != catalog.get("theorems")
        or tuple(current_alpha.ALPHA_ENTRIES[:EXPECTED_ALPHA_COUNT]) != v23.ALPHA_ENTRIES
        or any(
            newer is not historical
            for newer, historical in zip(current_alpha.ALPHA_ENTRIES, v23.ALPHA_ENTRIES)
        )
    ):
        raise MilestoneClosureExplorerError(
            "the current immutable Alpha-v30 child changed its exact Alpha-v23 first admission"
        )

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != EXPECTED_ALPHA_COUNT:
        raise MilestoneClosureExplorerError("Alpha-v23 lacks its complete theorem inventory")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise MilestoneClosureExplorerError("malformed Alpha-v23 theorem row")
        if row["name"] in by_name:
            raise MilestoneClosureExplorerError(f"duplicate Alpha-v23 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    graph = json.loads(GLOBAL_DEFINITIONS.read_text(encoding="utf-8"))
    original._audit_current_atlas(campaign, graph, error_type=MilestoneClosureExplorerError)
    blueprint = campaign.get("definitions")
    if not isinstance(blueprint, dict):
        raise MilestoneClosureExplorerError("the global atlas has no named definition registry")
    goals = {item["id"]: item for item in campaign.get("nodes", ())}
    closed_roots = {
        "G101": "euclidean_gcd_execution_logarithmic_bound",
        "G102": "binary_modular_execution_logarithmic_bound",
        "G025": "infinitely_many_primes_three_mod_four",
    }
    for goal, root in closed_roots.items():
        node = goals.get(goal)
        evidence = node.get("evidence") if isinstance(node, dict) else None
        theorem = by_name.get(root)
        if (
            not isinstance(node, dict)
            or node.get("status") != "alpha_closed"
            or not isinstance(evidence, dict)
            or evidence.get("alpha_version") != "v23"
            or evidence.get("release_status") != "alpha_closed"
            or evidence.get("checked_use") is not True
            or evidence.get("alpha_enrolled") is not True
            or evidence.get("stable_member") is not False
            or evidence.get("independent_lean_bundle_verified") is not True
            or evidence.get("theorem_name") != root
            or theorem is None
            or evidence.get("theorem_statement_sha256") != theorem.get("statement_sha256")
            or evidence.get("bundle_sha256") != bundle["artifact_sha256"]
            or evidence.get("bundle_node_id")
            != theorem.get("empty_context_closure", {}).get("bundle_node_id")
        ):
            raise MilestoneClosureExplorerError(
                f"closed milestone lacks its exact independently checked theorem evidence: {goal}"
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
        raise MilestoneClosureExplorerError(
            "a closed algorithmic milestone lacks its actual formal execution or logarithmic bound"
        )

    enrollment = alpha_v23_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V23_EXPECTED_COUNT:
        raise MilestoneClosureExplorerError("Alpha-v23 enrollment changed its checked additions")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise MilestoneClosureExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
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
            *MILESTONE_CLOSURE_REGISTRIES,
        )
        for definition in group
    }
    by_id: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        if not set(direct) <= set(by_id):
            raise MilestoneClosureExplorerError("the reviewed definition DAG is not dependency-first")
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
                MILESTONE_CLOSURE_DEFINITIONS_BY_NAME.get(definition.name)
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
                raise MilestoneClosureExplorerError(
                    f"definition {definition.name!r} is not its immutable shared reviewed object"
                )
            reviewed_id = definition.stable_id
            reviewed_route = record["route"]
        if custom and blueprint is not None:
            if tuple(blueprint.get("parameters", ())) != definition.parameters:
                raise MilestoneClosureExplorerError(
                    f"milestone definition {definition.name!r} changed its global argument signature"
                )
            global_name, positions = definition.name, list(range(definition.arity))
            if definition.name == "Beta":
                canonical = _definition_specs()["BetaAt"]
                if (
                    canonical.parameters != definition.parameters
                    or canonical.template_formula != definition.template_formula
                ):
                    raise MilestoneClosureExplorerError("canonical Beta no longer equals reviewed BetaAt")
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
                    raise MilestoneClosureExplorerError(
                        f"the global atlas does not share exact definition {definition.name!r}"
                    )
        elif not custom and definition.name in reviewed_links:
            link = reviewed_links[definition.name]
            if (
                link.get("reviewed_id") != definition.stable_id
                or tuple(link.get("reviewed_parameters", ())) != definition.parameters
            ):
                raise MilestoneClosureExplorerError(
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
            raise MilestoneClosureExplorerError("global definition argument alignment is invalid")
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


def _factory_name(campaign: FrontierV23Campaign) -> str:
    return {
        FrontierV23Campaign.EUCLIDEAN_LOGARITHMIC_BOUND: (
            "make_euclidean_logarithmic_bound_candidate_theorems"
        ),
        FrontierV23Campaign.BINARY_DIGIT_EXTRACTION: (
            "make_binary_digit_extraction_candidate_theorems"
        ),
        FrontierV23Campaign.PRIMES_THREE_MOD_FOUR: (
            "make_primes_three_mod_four_candidate_theorems"
        ),
    }[campaign]


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    enrollment = inputs["enrollment"]
    specs = tuple(
        item for item in enrollment.frontier_specs
        if enrollment.campaign_by_name[item.name] is family.campaign
    )
    if len(specs) != EXPECTED_CAMPAIGN_COUNTS[family.campaign]:
        raise MilestoneClosureExplorerError(f"checked family cardinality changed: {family.slug}")
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
            "alpha_first_enrolled_version": "v23",
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
            raise MilestoneClosureExplorerError(
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
            raise MilestoneClosureExplorerError(f"unchecked external prerequisite: {name}")
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
            raise MilestoneClosureExplorerError("theorem DAG has a forward or circular dependency")
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
        "milestone_status": "alpha_closed",
        "milestone_checked_use": True,
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
        "alpha_first_enrolled_version": "v23",
        "alpha_edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"],
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
    graph["alpha_first_enrolled_version"] = "v23"
    graph["milestone_status"] = "alpha_closed"
    graph["milestone_checked_use"] = True
    graph["milestone_caveat"] = family.caveat
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            node["alpha_edition_version"] = "v30"
            node["alpha_first_enrolled_version"] = "v23"
    return graph


def _retarget(document: bytes, family: Family, *, include_caveat: bool = False) -> bytes:
    text = document.decode("utf-8")
    old_caveat = (
        "Every displayed theorem was first admitted in Alpha v20, remains independently "
        "kernel- and Lean-verified for current Alpha v30 checked use, and has not been "
        "promoted to Stable."
    )
    text = text.replace(old_caveat, family.caveat)
    text = text.replace("first admitted v20", "first admitted v23")
    text = text.replace("FIRST ADMITTED v20", "FIRST ADMITTED v23")
    text = text.replace("First admission</dt><dd>Alpha v20", "First admission</dt><dd>Alpha v23")
    for version in ("v20", "v21", "v22"):
        text = text.replace(f"Alpha {version}", "Alpha v23")
        text = text.replace(f"ALPHA {version}", "ALPHA v23")
        text = text.replace(f"Alpha-{version}", "Alpha-v23")
    count = EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
    text = text.replace("590-node bundle", f"{count}-node bundle")
    text = text.replace("all 590 exact bundle nodes", f"all {count} exact bundle nodes")
    text = text.replace(" / 590</dd>", f" / {count}</dd>")
    if include_caveat:
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
        f"{family.milestones[-1]} fully proved</p>"
        f'<p class="pd-callout">{_e(family.caveat)}</p></article>'
        for family, corpus in corpora
    )
    body = f"""<main class="proof-home proof-library-home"><header class="proof-hero">
 <p class="eyebrow">ALPHA v30 · HISTORICAL v23 CLOSED CONSTRUCTIVE MILESTONES</p>
 <h1>Logarithmic arithmetic and infinitely many progression primes</h1>
 <p>Fifty-nine independently original-kernel- and Lean-verified theorems fully prove certified logarithmic Euclidean complexity, canonical binary repeated squaring, and infinitely many primes three modulo four.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Complete number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>Each of G101, G102, and G025 was fully proved in historical Alpha v23 and retains current Alpha-v30 checked-use authority; Stable remains a separate unchanged edition.</p></main>"""
    return original._document(
        FAMILIES[0],
        title="Three Closed Constructive Number-Theory Milestones",
        body=body,
        prefix="",
        defined=False,
    )


def build_files() -> dict[str, bytes]:
    """Build QR-style historical v23 proof surfaces under current v30 authority."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise MilestoneClosureExplorerError(f"reviewed shared explorer asset changed: {name}")
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
            first_admitted_version="v23",
            bundle_node_count=EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
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
        "alpha_first_enrolled_version": "v23",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "alpha_edition_version": "v30",
                "alpha_first_enrolled_version": "v23",
                "domain": family.domain,
                "family": family.family_id,
                "milestones": list(family.milestones),
                "milestone_status": "alpha_closed",
                "milestone_checked_use": True,
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
        print(f"constructive milestone-closure explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive milestone-closure explorer is stale", file=sys.stderr)
            return 1
        print(
            f"constructive milestone-closure explorer: {len(files)} files, "
            f"{FRONTIER_V23_EXPECTED_COUNT} checked theorems"
        )
        return 0
    _write(options.output, files)
    print(
        f"constructive milestone-closure explorer: wrote {len(files)} files, "
        f"{FRONTIER_V23_EXPECTED_COUNT} checked theorems"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
