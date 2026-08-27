#!/usr/bin/env python3
"""Add the exact seven-target second wave to the existing campaign atlas.

Historical milestone wording/evidence is retained separately. An update is
authorized only by the same actual closed-kernel and independent Lean gates
as the canonical new-family generator; this script does not publish a site.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

import build_constructive_second_wave_explorer as explorer
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_second_wave_definition_graph import build_definition_graph
from constructive_second_wave_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS, definition_closure
from peano_lab.kernel.formulas import parse_formula_with_names


PRIMARY_ROOTS = {
    "T13": "rectangular_matrix_rank_exists_unique",
    "G011": "crt_pairwise_compatible_prefix_normalized_exists_unique",
    "G095": "integer_polynomial_prime_simple_root_lifts_all_positive_powers",
    "G035": "multinomial_kummer_carry_valuation",
    "G027": "prime_count_chebyshev_bounds",
    "G051": "prime_cauchy_davenport_sumset_bound",
    "G107": "cornacchia_prime_two_squares_complete",
}
HISTORICAL_PARTIAL_SHA256 = {
    "T13": "fc99bbaa05e917570f1ee7e36ed365d8bed5bc656362ce5a7255fa0eebaa7c1b",
    "G095": "1b1b57bb84b49c6e4ecff1b3eec11426dec337cef0c674a7eb184ea15346326e",
    "G011": "f6f21bb21a20a4c464720e1c9df11d492faae71690c2c9bfaec425bf7787c5be",
}
INTRODUCED_BLUEPRINT_NAMES = frozenset("""
AbsoluteRecursiveDeterminant AllPrime AllSignedMinorsZero BalancedInverse BetaAt
BetaCutoffPrefix BetaSumTrace BetaValuationPrefix BinaryAddCarryPrefix BinaryColumnCarryCount
BoundedNonzeroInverse BoundedPowerValuation BoundedPrefix BoundedQRes CRTNormalizedPrefixSolution
CRTPrefixGcdCongruences CanonicalHornerLift CanonicalSignedHornerLift CarryCountMany CauchyDavenportBound
CeilDivSix CentralBinom Choose ContainsPrefix CornacchiaAlternatingCongruences CornacchiaEuclideanRun
CornacchiaRoot CornacchiaStateAt CornacchiaStateInvariant CornacchiaTrace CornacchiaTransitionAt
DivisionPrefix Factorial FiniteMatrixSelector FloorSqrt HornerCoefficientBlend HornerRootModulo
IdentityMatrixSelector InjectivePrefix IntegerColumnSpan IntegerMatrixEntrywiseEqual IntegerMatrixVectorProduct
IntegerVectorAdd IntegerVectorEqual IntegerVectorNegate IntegerVectorZero InverseIndex InversePrefix IsGCD
Mod4One ModularDysonTransform ModularSetIntersection ModularSetMember ModularSetPullback ModularSetSubset
ModularSetSum ModularSetSumCover ModularSetUnion ModularTranslationBoundary Multinomial
MultinomialBinomialPrefix MultinomialCarryPrefix NonzeroMatrixMinor NonzeroSelectedMinor
PositiveDeterminantMatrixData PowerDivides PowerQuotPrefix PrimeBitPrefix PrimePowerValuation Primorial
Product QRes Range RectangularMatrixRank Repeat ScaledFixedPoint ScaledInverse ScaledInverseIndex
ScaledInversePrefix SignedDerivativeNonzero SignedDerivativeUnit SignedDeterminantChildPrefix
SignedDeterminantHistory SignedDeterminantLocalStep SignedDeterminantNodeAt SignedDeterminantNodeCode
SignedEvaluatedCofactors SignedHornerRoot SignedHornerValueDerivative SignedMatrixPrefixEquality
SignedNonsingularHornerRoot SignedRecursiveDeterminant SignedSelectedDeterminant SignedSelectedSubmatrix
SignedSimpleHornerRoot SimpleHornerRoot Sorted SuccessorInverse SurjectivePrefix UniformBetaPrefixBox UnitResidue
""".split())
ACTUAL_TOOL_PREREQUISITES = {
    "T13": ("T04", "T11"), "G011": ("T04", "T07", "T10"),
    "G095": ("T11", "T12", "T14"), "G035": ("A04", "T09", "T11"),
    "G027": ("T09", "T11"), "G051": ("T04", "T11", "T14", "T15"),
    "G107": ("T06", "T07", "T15"),
}
SUBSTRATE_THEOREMS = {
    "T13": ("beta_signed_matrix_product_exists", "signed_alternating_cofactor_fold_exists"),
    "G011": ("crt_merge_compatible_prefix_solution_exists", "gcd_balanced_bezout_exists"),
    "G095": ("beta_horner_eval_exists", "coprime_bounded_mod_inverse"),
    "G035": ("kummer_binomial_carry_bit_count", "prime_power_valuation_mul", "beta_product_exists"),
    "G027": ("four_pow_lt_mul_central_binom", "primorial_le_four_pow", "central_binom_prime_power_contribution_le_double"),
    "G051": ("beta_sum_exists", "finite_modular_sumset_exists", "prime_cauchy_davenport_normalized_bounded_induction"),
    "G107": ("division_remainder_exists", "quadratic_supplement_minus_one_residue_iff_mod_four_one"),
}
REFINEMENTS = {
    "T13": "An integer matrix is represented by four beta parameters for its positive and negative row-major streams. Rank is an actual nonzero minor and universal vanishing of all higher minors. PositiveDeterminantMatrixData realizes the nondegenerate square-matrix/absolute-determinant data part of Lattice(B,d,D); it is not a proof of lattice index, geometric covolume, or basis independence.",
    "G011": "The residue and modulus lists each have two beta parameters and a shared finite length. CRTNormalizedPrefixSolution includes the exact LCM and all congruences; normalization is x<M for positive M and exact solution equality when M=0.",
    "G095": "Four beta parameters and a length represent the positive and negative coefficient streams of an arbitrary integer polynomial. SignedNonsingularHornerRoot uses an actual derivative that is nonzero modulo p; the inverse and every power witness are constructed, not assumed.",
    "G035": "The opaque planning parts code is refined to (b,c,l); Multinomial(b,c,l,n,z) is the actual iterated-binomial product and CarryCountMany(p,b,c,l,e) is a witnessed sequence of binary quotient-column additions. No arity-three planning symbol is silently identified with these arity-five relations, and no simultaneous-grid or order-invariance theorem is asserted.",
    "G027": "PrimeCount(x,z) is the actual finite sum of a complete primality mask. The exact displayed bound has only N>=2, the supplied actual binary length, and the supplied actual count as premises.",
    "G051": "Each finite subset of canonical residues has two beta parameters and an actual cardinality. The unchanged historical BitCount relation is exactly this characteristic-code/count relation. ModularSetSum specifies all and only sums. CauchyDavenportBound is p<=m or k+l<=m+1, the exact subtraction-free sharp inequality for nonempty input sets.",
    "G107": "The algorithm returns the root of minus one, both output coordinates, and beta history parameters/length. CornacchiaTrace contains every actual quotient/remainder step and the first-stop condition, not the desired two-square equation. The equation is proved from that trace.",
}


def _cone(roots: tuple[str, ...], rows: dict[str, Any]) -> set[str]:
    seen, pending = set(), list(roots)
    while pending:
        name = pending.pop()
        if name not in seen:
            seen.add(name)
            pending.extend(rows[name]["dependencies"])
    return seen


def _blueprint_expansion(definition) -> str:
    # The historical blueprint's three-argument Sum is intentionally NOT the
    # checked four-argument relation. Its already reviewed BetaSum alias has
    # exactly the latter signature; retain the distinction in new DAG edges.
    reading = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    source = re.sub(r"\bSum\(", "BetaSum(", reading["defined_statement"])
    aliases = {**DEFINITIONS, "BetaSum": replace(DEFINITIONS["Sum"], name="BetaSum")}
    exact, names = parse_formula_with_names(definition.template_source)
    parser = _LocalDefinedParser(source, aliases)
    parser.free = list(names)
    if parser.parse() != exact or tuple(parser.free) != names:
        raise explorer.SecondWaveExplorerError("blueprint display alias changed the exact definition")
    return source


def extend_campaign(original: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(original)
    if result.get("schema") != "constructive-grand-campaign-v1" or result.get("meta", {}).get("current_alpha_version") not in {"v26", "v27"}:
        raise explorer.SecondWaveExplorerError("second-wave extension requires the exact v26/v27 campaign")
    if len(INTRODUCED_BLUEPRINT_NAMES) != 101 or not INTRODUCED_BLUEPRINT_NAMES <= DEFINITIONS.keys():
        raise explorer.SecondWaveExplorerError("the additive blueprint definition inventory changed")
    for name, definition in DEFINITIONS.items():
        if name in INTRODUCED_BLUEPRINT_NAMES:
            expected_definition = {
                "parameters": list(definition.parameters), "meaning": definition.summary,
                "expansion": _blueprint_expansion(definition),
                "reviewed_definition_id": definition.stable_id,
                "reviewed_expansion_sha256": explorer._digest(definition.template_source),
                "exact_defined_expansion_equivalence_checked": True,
            }
            if name in result["definitions"] and explorer._json(result["definitions"][name]) != explorer._json(expected_definition):
                raise explorer.SecondWaveExplorerError(f"exact introduced blueprint definition changed: {name}")
            result["definitions"][name] = expected_definition
        elif name not in result["definitions"]:
            raise explorer.SecondWaveExplorerError(f"a historical blueprint definition is missing: {name}")
    metadata = result["meta"]
    metadata.update(current_alpha_version="v27", current_alpha_checked_use_count=inputs["catalog"]["checked_use_count"],
                    second_execution_wave_named_targets=list(PRIMARY_ROOTS), second_execution_wave_new_theorem_count=422)
    if "v26" not in metadata["historical_alpha_versions"]:
        metadata["historical_alpha_versions"].append("v26")
    source_rows = (
        ("S58", "release_manifest", "Current local Alpha v27 independently checked second-wave channels", "artifacts/peano-library/channels-v27.json"),
        ("S59", "independent_proof_artifact", "Complete 1,224-node original-kernel and Lean-verified second-wave proof bundle", explorer.EXPECTED_BUNDLE_PATH),
        ("S60", "independent_closure_record", "Exact seven-target second-wave verification receipt and scope boundaries", "research/arithmetic-library/alpha-v27-second-wave-receipt.md"),
        ("S61", "admission_record", "Immutable additive Alpha v27 second-wave admission contract", "research/arithmetic-library/alpha-v27-second-wave-rfc-v1.md"),
    )
    old_sources = {row["id"]: row for row in result["sources"]}
    for identifier, kind, label, path in source_rows:
        row = {"id": identifier, "kind": kind, "label": label, "path": path}
        if identifier in old_sources and old_sources[identifier] != row:
            raise explorer.SecondWaveExplorerError("second-wave provenance source changed")
        if identifier not in old_sources:
            result["sources"].append(row)
    boundaries = result["ambitious_boundaries"]
    boundaries["alpha_v26_edition"]["role"] = "historical_immutable_release"
    catalog = inputs["catalog"]
    boundaries["alpha_v27_edition"] = {
        "role": "current_immutable_release", "theorem_count": catalog["theorem_count"],
        "stable_closed_count": 432, "alpha_closed_count": catalog["alpha_only_count"],
        "checked_use_count": catalog["checked_use_count"], "body_checked_count": 0,
        "pending_layered_closure_count": 0, "checked_use_promotion_count": 422, "new_theorem_count": 422,
        "dependency_edge_count": catalog["edge_count"], "checked_dependency_edge_count": catalog["edge_count"],
        "layer_count": catalog["layer_count"], "enrollment_sha256": catalog["ordered_enrollment_root_sha256"],
        "parent_enrollment_sha256": explorer.closure.PARENT_ENROLLMENT_SHA256,
        "identity_sha256": catalog["edition_identity_sha256"], "catalog_sha256": inputs["catalog_sha256"],
        "evidence_root_sha256": catalog["evidence_root_sha256"],
        "frontier_new_names_sha256": catalog["frontier_v27_ordered_names_sha256"],
        "stable_unchanged": True, "historical_v26_unchanged": True,
        "independent_lean_bundle_verified": True,
        "promoted_origin": "independently_kernel_and_lean_checked_exact_second_wave_targets",
    }
    bundle = inputs["bundle"]
    boundaries["second_wave_evidence_transition"] = {
        "parent_v26_theorem_count": 2138, "new_theorem_count": 422, "current_v27_theorem_count": 2560,
        "campaign_order": [family.campaign for family in explorer.FAMILIES],
        "new_theorem_counts": dict(Counter(owner.campaign for owner, row in inputs["frontier"])),
        "theorem_node_count": bundle["node_count"] - 1, "bundle_node_count": bundle["node_count"],
        "maximal_root_count": len(explorer.closure.second_wave_plan().root_names),
        "dependency_edge_count": bundle["dependency_edges"], "body_proof_nodes": bundle["body_proof_nodes"],
        "bundle_bytes": bundle["artifact_bytes"], "bundle_sha256": bundle["artifact_sha256"],
        "independent_lean_bundle_verified": True, "original_kernel_call_count": bundle["kernel_calls"],
        "stable_unchanged": True, "historical_v26_unchanged": True,
        "named_targets_complete": list(PRIMARY_ROOTS),
        "broader_roadmap_bullets_automatically_closed": False,
    }
    goals = {node["id"]: node for node in result["nodes"]}
    rows = inputs["by_name"]
    for family in explorer.FAMILIES:
        identifier = family.milestones[-1]
        goal, root = goals[identifier], rows[PRIMARY_ROOTS[identifier]]
        if goal.get("status") == "open" and goal.get("evidence"):
            goal.setdefault("historical_partial_evidence", deepcopy(goal["evidence"]))
        if identifier in HISTORICAL_PARTIAL_SHA256:
            old_evidence = json.dumps(goal.get("historical_partial_evidence"), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
            if sha256(old_evidence.encode()).hexdigest() != HISTORICAL_PARTIAL_SHA256[identifier]:
                raise explorer.SecondWaveExplorerError(f"immutable partial evidence changed for {identifier}")
        goal.setdefault("historical_planned_statement", goal["statement"])
        goal.setdefault("historical_planned_dependencies", deepcopy(goal["deps"]))
        conceptual = list(goal.get("conceptual_refs", ()))
        for dependency in goal["historical_planned_dependencies"]:
            if dependency not in ACTUAL_TOOL_PREREQUISITES[identifier] and dependency not in conceptual:
                conceptual.append(dependency)
        goal["deps"] = list(ACTUAL_TOOL_PREREQUISITES[identifier])
        goal["conceptual_refs"] = [name for name in conceptual if name not in goal["deps"]]
        goal["status"] = "alpha_closed"
        goal["statement"] = _FormulaCompactor(explorer._family_definitions(family)).compact(root["statement"])["defined_statement"]
        goal["why"] = family.description + " " + family.caveat
        goal["representation_refinement"] = REFINEMENTS[identifier]
        goal["definition_refs"] = list(dict.fromkeys(definition.name if definition.name != "Sum" else "BetaSum"
                                                     for definition in explorer._family_definitions(family)))
        goal["references"] = list(dict.fromkeys((*goal.get("references", ()), "S58", "S59", "S60", "S61")))
        selected = [(owner, row) for owner, row in inputs["frontier"] if owner.campaign == family.campaign]
        tags = {row.name: f"{family.prefix}{index:04X}" for index, (_, row) in enumerate(selected, 1)}
        cone = _cone(family.roots, rows)
        if not set(SUBSTRATE_THEOREMS[identifier]) <= cone:
            raise explorer.SecondWaveExplorerError(f"a proposed actual construction prerequisite is not used by {identifier}")
        receipt = root["empty_context_closure"]
        evidence = {
            "implementation": "independently_closed", "alpha_version": "v27", "release_status": "alpha_closed",
            "alpha_enrolled": True, "checked_use": True, "stable_member": False,
            "full_empty_context_closure": True, "independent_lean_bundle_verified": True,
            "theorem_name": root["name"], "theorem_statement_sha256": root["statement_sha256"],
            "theorem_names": list(family.roots), "new_theorem_count": len(selected),
            "bundle_campaign": "second_wave", "bundle_node_id": receipt["bundle_node_id"],
            "bundle_nodes": bundle["node_count"], "bundle_dependencies": bundle["dependency_edges"],
            "bundle_sha256": bundle["artifact_sha256"], "bundle_path": bundle["artifact_path"],
            "route": family.slug + "/", "proof_tag": tags[root["name"]],
            "actual_substrate_theorem_names": list(SUBSTRATE_THEOREMS[identifier]),
            "proof_routes": [{"route": family.slug, "label": name, "tag": tags[name]} for name in family.roots],
        }
        if identifier == "T13":
            evidence.update(full_arbitrary_natural_matrix_product_proved=True, full_arbitrary_signed_matrix_product_proved=True,
                            full_arbitrary_signed_minor_proved=True, signed_four_by_four_determinant_proved=True,
                            full_arbitrary_determinant_proved=True, full_rank_substrate_proved=True,
                            full_lattice_substrate_proved=True, signed_integer_representation_invariance_proved=True,
                            positive_absolute_determinant_data_proved=True, nonzero_determinant_implies_full_rank_proved=True,
                            integer_column_span_zero_add_neg_proved=True, lattice_index_formula_proved=False,
                            determinant_multiplicativity_proved=False, independent_basis_theorem_proved=False,
                            normal_form_or_reduction_proved=False)
        elif identifier == "G011":
            evidence.update(full_generalized_crt_proved=True, general_compatible_non_coprime_fold_proved=True,
                            arbitrary_pairwise_compatibility_implies_merge_compatibility_proved=True,
                            zero_moduli_and_empty_list_included=True, normalized_unique_solution_proved=True)
        elif identifier == "G095":
            evidence.update(full_simple_root_hensel_lift_proved=True, unrestricted_input_canonical_prime_power_lift_proved=True,
                            signed_integer_polynomials_proved=True, lifted_root_uniqueness_proved=True,
                            arbitrary_prime_power_iteration_proved=True, derivative_nonzero_implies_unit_proved=True)
        goal["evidence"] = evidence
    # Rebuilding the full graph is also the missing/forward/cycle audit for all
    # preserved planning definitions and every newly connected exact template.
    build_definition_graph(result)
    return result


def _table_source(name: str, rows: list[dict[str, Any]], *, compatible: bool) -> str:
    lines = []
    for row in rows:
        fields = f'id: {json.dumps(row["reviewed_id"])}, route: {json.dumps(row["route"])}, parameters: {json.dumps(row["reviewed_parameters"])}, name: {json.dumps(row["reviewed_name"])}'
        if compatible:
            positions = row["reviewed_argument_blueprint_positions"]
            if positions != list(range(len(positions))):
                fields += f', argumentOrder: {json.dumps(positions)}'
        lines.append(f'        {row["blueprint_name"]}: {{ {fields} }}')
    return f"      var {name} = {{\n" + ",\n".join(lines) + "\n      };"


def update_atlas_bindings(source: str, campaign: dict[str, Any]) -> str:
    graph = build_definition_graph(campaign)
    for name, key, compatible in (("COMPILED_DEFINITIONS", "compatible_reviewed_matches", True),
                                  ("INCOMPATIBLE_DEFINITIONS", "incompatible_reviewed_matches", False)):
        rows = [{**row, "route": graph.get("definition_page_overrides", {}).get(row["reviewed_id"], {}).get("route", row["route"])} for row in graph[key]]
        source, count = re.subn(r"      var " + name + r" = \{.*?\n      \};", lambda match: _table_source(name, rows, compatible=compatible), source, count=1, flags=re.S)
        if count != 1:
            raise explorer.SecondWaveExplorerError(f"missing original atlas table {name}")
    roots = re.search(r"      var PROOF_ROOTS = \{(.*?)\n      \};", source, flags=re.S)
    if roots is None:
        raise explorer.SecondWaveExplorerError("missing original atlas proof destinations")
    lines = [line.rstrip().rstrip(",") for line in roots.group(1).splitlines() if line.strip()
             and not any(re.match(r"\s*" + identifier + r":", line) for identifier in PRIMARY_ROOTS)]
    goals = {node["id"]: node for node in campaign["nodes"]}
    for identifier in PRIMARY_ROOTS:
        goal = goals[identifier]
        evidence = goal["evidence"]
        lines.append(f'        {identifier}: {{ route: {json.dumps(evidence["route"].rstrip("/"))}, label: {json.dumps(goal["title"],ensure_ascii=False)}, tag: {json.dumps(evidence["proof_tag"])} }}')
    replacement = "      var PROOF_ROOTS = {\n" + ",\n".join(lines) + "\n      };"
    source = source[:roots.start()] + replacement + source[roots.end():]
    source, count = re.subn(r'var HTML_REVISION = "[0-9a-f]{12}";',
                           f'var HTML_REVISION = "{campaign["ambitious_boundaries"]["alpha_v27_edition"]["catalog_sha256"][:12]}";', source, count=1)
    # Some historical atlas revisions derive their cache key from metadata.
    if count == 0 and "HTML_REVISION" in source:
        raise explorer.SecondWaveExplorerError("unknown atlas HTML revision declaration")
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    inputs = explorer._load_release_inputs()
    original = explorer._strict_json(explorer.CAMPAIGN.read_bytes())
    campaign = extend_campaign(original, inputs)
    payload = explorer._json(campaign)
    atlas = explorer.CAMPAIGN.with_name("index.html")
    source = atlas.read_text()
    expected = update_atlas_bindings(source, campaign)
    if arguments.check:
        if campaign != original or source != expected:
            raise explorer.SecondWaveExplorerError("the second-wave campaign extension is stale")
    else:
        if explorer.CAMPAIGN.read_bytes() != payload:
            explorer.CAMPAIGN.write_bytes(payload)
        if source != expected:
            atlas.write_text(expected)
    print("second-wave campaign: PASS (exact targets, historical evidence, distinct DAGs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
