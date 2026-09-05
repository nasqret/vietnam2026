#!/usr/bin/env python3
"""Canonical, evidence-backed reading maps for the seven second-wave targets.

The generator only writes local deterministic snapshots. It does not publish,
admit a theorem, replay a browser tactic, or modify any historical release.
Every new row must match both its exact authoring specification and the sealed
self-contained bundle, checked by the original kernel and compiled Lean.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(REPO / "peano-lab/py"))

from constructive_formula_compactor import _FormulaCompactor
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_proof_explorer_template import render_canonical_family_landing
from constructive_second_wave_definition_graph import build_definition_graph, reviewed_registry
from constructive_second_wave_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME, SECOND_WAVE_REGISTRIES, definition_closure,
)
from constructive_second_wave_explorer_renderer import (
    ASSET_DIGESTS, SCHEMA, STATUS, _asset, _atlas_navigation, _defined_definition,
    _defined_graph, _defined_index, _defined_theorem, _e, _graph_payload, _versioned,
)
from peano_lab.library import campaign_second_wave_closure as closure
from peano_lab.library.defined_syntax import DefinitionSpec
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec


OUTPUT = REPO / "book/_static/constructive-second-wave-explorer"
CATALOG = REPO / "artifacts/peano-library/alpha/catalog-v27.json"
CHANNELS = REPO / "artifacts/peano-library/channels-v27.json"
CAMPAIGN = REPO / "book/_static/constructive-grand-campaign/campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_BUNDLE_PATH = "research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json"
PARENT_ARTIFACTS = {
    "catalog": {"path": closure.PARENT_CATALOG, "sha256": closure.PARENT_CATALOG_SHA256},
    "channels": {"path": "artifacts/peano-library/channels-v26.json", "sha256": "319d19275ca810b043305428320fb3999af03d34c0035acab70b4d6d33ae97d3"},
    "dependency_graph": {"path": "artifacts/peano-library/alpha/dependency-graph-v26.mmd", "sha256": "244713db3ee03c5ea50d0d0959ad3e0f3516d2e73fec25a354f945e663aadc9b"},
    "metrics": {"path": "artifacts/peano-library/alpha/metrics-v26.json", "sha256": "e1bf8b3cd778df62555abeb365b0d866e7f51cb380fd597a69483944aeffd894"},
}
ASSET_SOURCES = {
    "defined-explorer.css": REPO / "book/_static/pa-proof-explorer/defined/assets/explorer.css",
    "defined-explorer.js": REPO / "book/_static/pa-proof-explorer/defined/assets/explorer.js",
    "exact-explorer.css": REPO / "book/_static/pa-proof-explorer/assets/explorer.css",
    "exact-explorer.js": REPO / "book/_static/pa-proof-explorer/assets/explorer.js",
    "proofs.css": REPO / "deploy/proofs/proofs.css",
}
# These five tracked, clean source/audit files were revised in historical
# commits before this campaign. Preserve the inherited release bindings and
# explicitly distinguish their later checked-in versions. No proof bundle,
# theorem specification, kernel source, or new v27 document is excepted.
INHERITED_REVISED_SOURCE_SHA256 = {
    "peano-lab/py/tests/test_library_editions_v19_admission.py": "27b789cca2650a2c83fb0cd3eb185607111eac7075a1f44cee9cd274832ee9a1",
    "peano-lab/py/tests/test_linear_congruence_complete_candidate.py": "8a4d2588fe63a8c13477349899040f3122b0d1226b75adbfcb926364e0088736",
    "research/arithmetic-library/ha-bertrand-b6-release-tranche-rfc-v1.md": "820fd1e4a262295bb85a50bbe2f9b5361c9cc3ce403fda443a1ff1b2a2d129ec",
    "research/arithmetic-library/linear-congruence-complete-rfc-v1.md": "ce32b9b9922e46be8abb8a61ae4a4cb3461f2dea6eeb56a65bfbc2684991cf35",
    "research/arithmetic-library/wmi-qr-replay.md": "41b22f2291a4ef69746acedbfee346bf4044e67afb8f2ee77ded06156a0ca67b",
}


class SecondWaveExplorerError(ValueError):
    """A theorem, notation, independent check, or immutable boundary changed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: str
    prefix: str
    title: str
    kicker: str
    description: str
    formula: str
    domain: str
    family_id: str
    milestones: tuple[str, ...]
    roots: tuple[str, ...]
    definition_routes: tuple[str, ...]
    extra_definitions: tuple[str, ...]
    caveat: str


FAMILIES = (
    Family(
        "integer-linear-algebra", "matrix_determinants", "DL",
        "Integer determinants, rank, and lattice data",
        "Arbitrary dimensions · genuine minors · integer coefficient witnesses",
        "Construct actual recursive determinants, exhaustive rectangular rank witnesses, and integer column spans, with representation-independent signed arithmetic and explicit finite codes.",
        "det(M) exists · ∃!r.Rank(M,r) · u,v∈Span(M) ⇒ u+v,−u∈Span(M)",
        "D05", "F12", ("T13",),
        ("signed_recursive_determinant_exists_unique", "integer_column_span_add_exists",
         "integer_column_span_negate_exists", "rectangular_matrix_rank_exists_unique",
         "signed_recursive_determinant_integer_invariant", "rectangular_matrix_rank_integer_invariant",
         "absolute_recursive_determinant_exists_unique", "positive_determinant_matrix_data_exists_unique",
         "positive_determinant_matrix_data_full_rank"),
        ("integer-linear-algebra",), (),
        "This branch proves the finite determinant/rank/span substrate. It does not claim Smith or Hermite normal form, lattice index equals determinant, determinant multiplicativity, lattice reduction, or geometry-of-numbers theorems.",
    ),
    Family(
        "hensel-lifting", "hensel", "HL", "Full constructive simple-root Hensel lifting",
        "Integer polynomials · unrestricted roots · every prime power",
        "Evaluate actual signed polynomials, derive the derivative inverse from nonvanishing modulo the prime, and construct the unique canonical lift at every positive prime-power precision.",
        "f(a)≡0 (mod p) ∧ f′(a)≢0 (mod p) ⇒ ∀k>0. ∃!r<pᵏ. r≡a (mod p) ∧ f(r)≡0 (mod pᵏ)",
        "D04", "F10", ("G095",),
        ("integer_polynomial_prime_power_hensel_lift_exists_unique",
         "integer_polynomial_prime_power_hensel_iterated_exists_unique",
         "integer_polynomial_prime_simple_root_lifts_all_positive_powers"),
        ("hensel-lifting",), ("Prime", "Pow", "Le"),
        "The derivative-nonzero criterion supplies no inverse or power witness: both are constructed. Roots may be arbitrary natural representatives of signed integer polynomials. Singular-root classification and p-adic completion are separate milestones.",
    ),
    Family(
        "generalized-crt", "generalized_crt", "FC", "Complete finite generalized Chinese remainder theorem",
        "Pairwise gcd compatibility · arbitrary noncoprime lists · zero moduli",
        "Construct a simultaneous solution for every finite pairwise-compatible list, prove the exact LCM solution class, and obtain unique normalized representatives without a supplied compatible prefix or dominating last modulus.",
        "PairwiseCompatible(aᵢ,mᵢ) ⇔ ∃x.∀i.x≡aᵢ (mod mᵢ)",
        "D01", "F02", ("G011",),
        ("crt_pairwise_compatible_prefix_solvable_iff",
         "crt_pairwise_compatible_prefix_canonical_exists_unique",
         "crt_pairwise_compatible_prefix_normalized_exists_unique"),
        ("generalized-crt",), ("CRTPairwiseCompatiblePrefix", "CRTPositiveModuliPrefix", "IsGCD", "Le"),
        "All finite lists are included, even the empty list and zero moduli. A positive LCM gives x<M; at zero LCM congruence is exact equality and normalization deliberately does not require the impossible x<0.",
    ),
    Family(
        "multinomial-kummer", "multinomial_kummer", "MK", "Kummer for arbitrary finite multinomials",
        "Actual coefficients · quotient-column carries · empty and zero parts",
        "Build the finite product of actual binomial factors and prove that its exact prime valuation equals the total column-carry count in successive addition of every part.",
        "Prime(p) ∧ Multinomial(parts,n,z) ⇒ ∃e. vₚ(z)=e ∧ CarryCountMany(p,parts,e)",
        "D01", "F04", ("G035",),
        ("multinomial_exists", "multinomial_empty_values", "multinomial_empty_carry_count",
         "multinomial_kummer_carry_valuation"),
        ("multinomial-kummer",), ("Prime", "Le", "PrimePowerValuation"),
        "The carry relation contains actual quotient columns and carry bits, not the desired valuation. The theorem includes all finite lists and zero parts. It uses sequential binary-column carries; a separate simultaneous-grid or permutation-invariance theorem is not asserted.",
    ),
    Family(
        "prime-count-chebyshev", "chebyshev", "PC", "Effective Chebyshev prime-count bounds",
        "Exact prime masks · binary length · explicit constants",
        "Count every prime through N with a complete decidable finite mask and prove both integer Chebyshev bounds using actual central binomial and primorial estimates.",
        "N≥2 ∧ BitLen(N,ℓ) ∧ PrimeCount(N,k) ⇒ N≤8kℓ ∧ kℓ≤8N",
        "D02", "F03", ("G027",),
        ("prime_count_chebyshev_bounds",),
        ("prime-count-chebyshev",), ("BitLen", "Primorial", "CentralBinom", "Pow", "Le"),
        "These are the exact finite integer inequalities with constant 8, for every N≥2. The proof uses constructive binomial and primorial infrastructure; it does not assume logarithms, asymptotic estimates, the prime number theorem, or a factorization oracle.",
    ),
    Family(
        "cornacchia", "cornacchia", "CN", "Cornacchia’s sum-of-two-squares algorithm",
        "Actual Euclidean history · first stopping point · proved representation",
        "Construct the square root of −1, run a genuine finite quotient/remainder trace, and prove that its first square-bounded stopping state represents every prime congruent to one modulo four.",
        "Prime(p) ∧ p≡1 (mod 4) ⇒ ∃R,T,trace. CornacchiaTrace(p,trace,R,T) ∧ p=R²+T²",
        "D04", "F11", ("G107",),
        ("cornacchia_prime_two_squares_complete",),
        ("cornacchia",), ("Le",),
        "The output equation is proved from the real first-stop execution; it is not a trace-definition assumption. This is the prime sum-of-two-squares Cornacchia theorem, not a general x²+d y² solver.",
    ),
    Family(
        "cauchy-davenport", "cauchy_davenport", "CD", "Constructive Cauchy–Davenport",
        "Actual finite prime-field sets · exact cardinalities · Dyson descent",
        "Construct genuine finite modular sets and their sumsets, then prove the sharp prime-field inequality by a witnessed cardinality-preserving transform and strict descent.",
        "∅≠A,B⊆𝔽ₚ ⇒ |A+B|≥min(p,|A|+|B|−1)",
        "D03", "F06", ("G051",),
        ("prime_cauchy_davenport_cover_bound", "prime_cauchy_davenport_sumset_exists",
         "prime_cauchy_davenport_sumset_bound"),
        ("cauchy-davenport",), ("BitCount", "Prime", "Le"),
        "Sets are complete characteristic-bit codes with actual finite cardinality witnesses. The proof constructs translations and the sumset; no finite-choice oracle, supplied cardinality conclusion, or unproved polynomial-method premise is used.",
    ),
)


def _digest(value: bytes | str) -> str:
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()


def _strict_json(payload: bytes) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise SecondWaveExplorerError(f"duplicate JSON field {name!r}")
            result[name] = value
        return result
    value = json.loads(payload, object_pairs_hook=pairs)
    if type(value) is not dict:
        raise SecondWaveExplorerError("a proof product must be a JSON object")
    return value


def _factory_rows() -> tuple[tuple[closure.SecondWaveFactory, TheoremSpec], ...]:
    return tuple((owner, row) for owner in closure.FACTORIES
                 for row in getattr(import_module(f"peano_lab.library.{owner.module}"), owner.factory)(TheoremSpec))


def _audit_parent_release_chain(catalog: Mapping[str, Any], channels: Mapping[str, Any]) -> None:
    expected = {
        "artifacts": PARENT_ARTIFACTS, "schema": "peano-library-alpha-snapshot-v26",
        "theorem_count": closure.PARENT_COUNT, "edition_identity_sha256": closure.PARENT_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": closure.PARENT_ENROLLMENT_SHA256,
    }
    if (catalog.get("parent_alpha_v26") != expected
        or channels.get("parent_channels_v26") != PARENT_ARTIFACTS["channels"]):
        raise SecondWaveExplorerError("the immutable parent release chain changed")
    for record in PARENT_ARTIFACTS.values():
        if _digest((REPO / record["path"]).read_bytes()) != record["sha256"]:
            raise SecondWaveExplorerError("an immutable parent artifact changed")


def _load_release_inputs() -> dict[str, Any]:
    raw = CATALOG.read_bytes()
    catalog, channels = _strict_json(raw), _strict_json(CHANNELS.read_bytes())
    _audit_parent_release_chain(catalog, channels)
    parent_raw = (REPO / closure.PARENT_CATALOG).read_bytes()
    if _digest(parent_raw) != closure.PARENT_CATALOG_SHA256:
        raise SecondWaveExplorerError("the immutable v26 parent catalogue changed")
    parent = _strict_json(parent_raw)
    parent_channels = _strict_json((REPO / "artifacts/peano-library/channels-v26.json").read_bytes())
    digest = _digest(raw)
    channel = channels.get("channels", {}).get("alpha", {})
    rows = catalog.get("theorems", ())
    frontier = _factory_rows()
    expected_count = closure.PARENT_COUNT + len(frontier)
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v27"
        or catalog.get("channel") != "alpha"
        or catalog.get("theorem_count") != expected_count
        or catalog.get("checked_use_count") != expected_count
        or catalog.get("stable_count") != 432
        or catalog.get("edition_identity_sha256") != "5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05"
        or catalog.get("ordered_enrollment_root_sha256") != "20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e"
        or len(rows) != expected_count
        or rows[:closure.PARENT_COUNT] != parent["theorems"]
        or channels.get("schema") != "peano-library-channels-v27"
        or channels.get("default_channel") != "stable"
        or channels.get("channels", {}).get("stable") != parent_channels["channels"]["stable"]
        or channel.get("artifact_path") != CATALOG.relative_to(REPO).as_posix()
        or channel.get("artifact_sha256") != digest
        or channel.get("theorem_count") != expected_count
        or channel.get("checked_use_count") != expected_count
        or channel.get("edition_identity_sha256") != catalog.get("edition_identity_sha256")
        or channel.get("ordered_enrollment_root_sha256") != catalog.get("ordered_enrollment_root_sha256")
    ):
        raise SecondWaveExplorerError("current v27 authority or exact historical admission changed")
    promotion = catalog.get("alpha_v27_second_wave_promotion", {})
    bundle_record = promotion.get("proof_bundle", {})
    if (promotion.get("frontier_new_count") != len(frontier)
        or promotion.get("remaining_body_checked_count") != 0
        or promotion.get("independent_lean_bundle_verified") is not True
        or bundle_record.get("artifact_path") != EXPECTED_BUNDLE_PATH
        or bundle_record.get("independent_lean_bundle_verified") is not True):
        raise SecondWaveExplorerError("the second wave lacks its complete independent closure")
    artifact = REPO / EXPECTED_BUNDLE_PATH
    payload = artifact.read_bytes()
    if (len(payload) != getattr(closure, "EXPECTED_SECOND_WAVE_BUNDLE_BYTES", 0)
        or _digest(payload) != getattr(closure, "EXPECTED_SECOND_WAVE_BUNDLE_SHA256", None)
        or bundle_record.get("artifact_bytes") != len(payload)
        or bundle_record.get("artifact_sha256") != _digest(payload)):
        raise SecondWaveExplorerError("the sealed self-contained second-wave proof bytes changed")
    bundle, target = decode_proof_bundle(payload.decode())
    checked = closure.check_second_wave_proof_bundle(bundle, target)
    plan = closure.second_wave_plan()
    positions = {row.name: row.node_id for row in plan.rows}
    if (bundle_record.get("node_count") != checked.node_count
        or bundle_record.get("kernel_calls") != checked.kernel_calls
        or bundle_record.get("dependency_edges") != checked.dependency_edges
        or bundle_record.get("body_proof_nodes") != checked.total_body_nodes):
        raise SecondWaveExplorerError("bundle metrics differ from actual original-kernel verification")
    verifier = REPO.parent / "peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify"
    result = subprocess.run([str(verifier), str(artifact)], capture_output=True, text=True, timeout=60)
    words = result.stdout.split()
    if result.returncode or words[:1] != ["ACCEPT"] or words[-2:] != [f"nodes={checked.node_count}", f"root={bundle.root}"]:
        raise SecondWaveExplorerError("the compiled independent Lean verifier rejected the exact bundle")
    for index, ((owner, spec), row) in enumerate(zip(frontier, rows[closure.PARENT_COUNT:]), closure.PARENT_COUNT):
        body = row.get("empty_context_closure", {})
        if (
            row.get("name") != spec.name or row.get("statement") != spec.statement
            or row.get("dependencies") != list(spec.dependencies) or row.get("script") != list(spec.script)
            or row.get("summary") != spec.summary or row.get("enrollment_index") != index
            or row.get("statement_sha256") != _digest(spec.statement)
            or row.get("script_sha256") != _digest("\n".join(spec.script) + "\n")
            or row.get("body_checked") is not True or row.get("checked_use") is not True
            or row.get("membership") != "alpha_only" or row.get("evidence_status") != "alpha_closed"
            or body.get("status") != "checked" or body.get("kernel_mode") != "intuitionistic"
            or body.get("bundle_node_id") != positions[spec.name]
            or body.get("certificate_sha256") != bundle_record["artifact_sha256"]
            or body.get("bundle_path") != EXPECTED_BUNDLE_PATH
            or body.get("node_statement_sha256") != row["statement_sha256"]
            or row.get("source", {}).get("path") != f"peano-lab/py/peano_lab/library/{owner.module}.py"
        ):
            raise SecondWaveExplorerError(f"a displayed theorem differs from its exact checked proof: {spec.name}")
    historical_documents = {document["path"]: document for document in parent["evidence_documents"]}
    current_documents = {document["path"]: document for document in catalog.get("evidence_documents", ())}
    if (len(current_documents) != len(catalog.get("evidence_documents", ()))
        or any(current_documents.get(path) != document for path, document in historical_documents.items())):
        raise SecondWaveExplorerError("historical evidence records were overwritten or omitted")
    revised_sources = []
    for document in catalog.get("evidence_documents", ()):
        relative = Path(document["path"])
        path = (REPO / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(REPO):
            raise SecondWaveExplorerError("unsafe sealed evidence path")
        data = path.read_bytes()
        if len(data) != document["bytes"] or _digest(data) != document["sha256"]:
            if (document["path"] not in historical_documents
                or INHERITED_REVISED_SOURCE_SHA256.get(document["path"]) != _digest(data)):
                raise SecondWaveExplorerError(f"sealed evidence document changed: {relative}")
            revised_sources.append({"path": document["path"], "historical_sha256": document["sha256"],
                                    "later_checked_in_sha256": _digest(data),
                                    "proof_authority": False, "changed_by_second_wave": False})
    return {"catalog": catalog, "catalog_sha256": digest, "revision": digest[:12],
            "by_name": {row["name"]: row for row in rows}, "frontier": frontier,
            "bundle": bundle_record, "current_edition_identity_sha256": catalog["edition_identity_sha256"],
            "inherited_revised_audit_sources": revised_sources}


def _load_inputs() -> dict[str, Any]:
    inputs = _load_release_inputs()
    campaign, graph = _strict_json(CAMPAIGN.read_bytes()), _strict_json(GLOBAL_DEFINITIONS.read_bytes())
    _audit_current_campaign(campaign, graph, inputs)
    return {**inputs, "campaign": campaign, "global_graph": graph}


def _audit_current_campaign(campaign: dict[str, Any], graph: dict[str, Any], inputs: dict[str, Any]) -> None:
    # Import only the pure extension here: no edition import or proof authority
    # is acquired through a generated atlas. The exact checked release above
    # remains the sole source of theorem evidence.
    from extend_constructive_second_wave_campaign import extend_campaign

    if campaign.get("meta", {}).get("current_alpha_version") != "v27" or graph != build_definition_graph(campaign):
        raise SecondWaveExplorerError("the current campaign or conservative definition atlas is stale")
    if _json(campaign) != _json(extend_campaign(campaign, inputs)):
        raise SecondWaveExplorerError("the current atlas differs from its exact checked second-wave contract")
    goals = {row["id"]: row for row in campaign["nodes"]}
    by_name = inputs["by_name"]
    for family in FAMILIES:
        goal = goals[family.milestones[-1]]
        evidence = goal.get("evidence", {})
        if goal.get("status") != "alpha_closed" or evidence.get("checked_use") is not True or evidence.get("stable_member") is not False:
            raise SecondWaveExplorerError(f"a full second-wave milestone is not independently closed: {goal['id']}")
        for root in family.roots:
            if root not in by_name or by_name[root].get("frontier_campaign") != family.campaign:
                raise SecondWaveExplorerError(f"the exact family root is absent: {root}")


def _family_definitions(family: Family) -> tuple[DefinitionSpec, ...]:
    names = tuple(item.name for route, definitions in SECOND_WAVE_REGISTRIES
                  if route in family.definition_routes for item in definitions)
    if not names:
        raise SecondWaveExplorerError(f"the family has no reviewed definition registry: {family.slug}")
    return definition_closure(tuple(dict.fromkeys((*names, *family.extra_definitions))))


def _definition_records(family: Family, inputs: Mapping[str, Any]) -> tuple[tuple[DefinitionSpec, ...], list[dict[str, Any]]]:
    specs = _family_definitions(family)
    reviewed, _, _ = reviewed_registry()
    links = {row["reviewed_name"]: row for row in inputs["global_graph"]["compatible_reviewed_matches"]}
    by_name, by_id, records = {item.name: item for item in specs}, {}, []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        ancestors = set(direct)
        for identifier in direct:
            ancestors.update(by_id[identifier]["transitive_dependencies"])
        identity = reviewed[definition.name]
        if identity["id"] != definition.stable_id or identity["expansion_sha256"] != _digest(definition.template_source):
            raise SecondWaveExplorerError("a historical or new reviewed definition identity changed")
        link = links.get(definition.name)
        if link is not None and (link["reviewed_id"] != definition.stable_id or tuple(link["reviewed_parameters"]) != definition.parameters):
            raise SecondWaveExplorerError("a blueprint alias changed its exact reviewed signature")
        expansion = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
        record = {
            "id": definition.stable_id, "name": definition.name, "parameters": list(definition.parameters),
            "arity": definition.arity, "signature": f"{definition.name}({','.join(definition.parameters)})",
            "summary": definition.summary, "expanded_template": definition.template_source,
            "expansion_sha256": _digest(definition.template_source),
            "defined_template": expansion["defined_statement"], "defined_template_parts": expansion["statement_parts"],
            "dependencies": direct, "dependency_names": list(definition.conceptual_dependencies),
            "topological_layer": max((by_id[value]["topological_layer"] + 1 for value in direct), default=0),
            "transitive_dependencies": sorted(ancestors), "origin": "shared-reviewed-hygienic-conservative-definition",
            "reviewed_definition_id": definition.stable_id, "reviewed_definition_route": identity["route"],
            "shared_definition_identity": definition.stable_id,
            "global_definition": None if link is None else link["blueprint_name"],
            "global_argument_positions": None if link is None else list(link["reviewed_argument_blueprint_positions"]),
            "exact_ast_verified": True, "kernel_signature_unchanged": True,
        }
        by_id[definition.stable_id] = record
        records.append(record)
    return specs, records


def _compact_script(spec: TheoremSpec, compactor: _FormulaCompactor, reading: dict[str, Any]) -> None:
    scripts, script_parts, uses = [], [], Counter()
    for command in spec.script:
        tactic, _, tail = command.partition(" ")
        if tactic == "have" and ":=" in tail:
            from peano_lab.engine.inferred_have import parse_inferred_have
            parse_inferred_have(tail)
            parts = [{"kind": "text", "text": command}]
        elif tactic in {"have", "suffices"}:
            name, separator, proposition = tail.partition(":")
            if not separator or not name.strip() or not proposition.strip():
                raise SecondWaveExplorerError("malformed local proof proposition")
            compact = compactor.compact(proposition.strip())
            if compact["statement_definition_uses"]:
                parts = [{"kind": "text", "text": f"{tactic} {name.strip()} : "}, *compact["statement_parts"]]
                uses.update(compact["statement_definition_uses"])
            else:
                parts = [{"kind": "text", "text": command}]
        else:
            parts = [{"kind": "text", "text": command}]
        scripts.append("".join(part["text"] for part in parts))
        script_parts.append(parts)
    reading.update(defined_script=scripts, script_parts=script_parts,
                   script_definition_uses=dict(sorted(uses.items())),
                   definition_uses=dict(sorted((Counter(reading["statement_definition_uses"]) + uses).items())))


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    selected = [(owner, spec) for owner, spec in inputs["frontier"] if owner.campaign == family.campaign]
    specs, definitions = _definition_records(family, inputs)
    compactor = _FormulaCompactor(specs)
    tags = {spec.name: f"{family.prefix}{index:04X}" for index, (_, spec) in enumerate(selected, 1)}
    nodes = []
    for owner, spec in selected:
        row = inputs["by_name"][spec.name]
        receipt = row["empty_context_closure"]
        reading = compactor.compact(spec.statement)
        _compact_script(spec, compactor, reading)
        nodes.append({
            "id": tags[spec.name], "name": spec.name, "summary": spec.summary,
            "statement": spec.statement, "statement_sha256": row["statement_sha256"],
            "script": list(spec.script), "dependencies": list(spec.dependencies),
            "source_module": f"peano_lab.library.{owner.module}", "factory": owner.factory,
            "sources": [{"source_module": f"peano_lab.library.{owner.module}", "factory": owner.factory,
                         "selected": True, "statement_sha256": row["statement_sha256"], "script_sha256": row["script_sha256"]}],
            "status": STATUS, "enrolled_in_alpha": True, "alpha_evidence": "alpha_closed",
            "alpha_checked_use": True, "alpha_edition_version": "v27", "alpha_first_enrolled_version": "v27",
            "stable_member": False, "admitted_to_alpha": True, "admitted_to_stable": False, "checked_use": True,
            "independent_lean_bundle_verified": True, "proof_bundle_node_id": receipt["bundle_node_id"],
            "proof_bundle_sha256": receipt["certificate_sha256"],
            "body_proof_nodes": receipt["body_proof_nodes"], "body_proof_depth": receipt["body_proof_depth"],
            "campaign_milestone": family.milestones[-1], "defined": reading,
        })
    if not selected or not set(family.roots) <= tags.keys():
        raise SecondWaveExplorerError(f"missing actual proof family or endpoint: {family.slug}")
    external = []
    for name in sorted({dependency for node in nodes for dependency in node["dependencies"] if dependency not in tags}):
        row = inputs["by_name"][name]
        if row.get("checked_use") is not True:
            raise SecondWaveExplorerError("an unproved premise entered a public graph")
        external.append({"name": name, "evidence": row["evidence_status"], "alpha_evidence": row["evidence_status"],
                         "alpha_checked_use": True, "enrolled_in_alpha": True, "admitted_to_alpha": True,
                         "admitted_to_stable": row["membership"] == "stable", "statement_sha256": row["statement_sha256"]})
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if any(name not in layers for name in internal):
            raise SecondWaveExplorerError("a proof dependency is circular or points forward")
        name = node["name"]
        layers[name] = max((layers[dependency] + 1 for dependency in internal), default=0)
        predecessor = max(internal, key=lambda dependency: len(paths[dependency]), default=None)
        paths[name] = ([] if predecessor is None else paths[predecessor]) + [tags[name]]
        adjacency[name] = {"dependencies": internal,
                           "dependents": [other["name"] for other in nodes if name in other["dependencies"]],
                           "critical_root_path": paths[name]}
    proof_edges = [{"kind": "proof_dependency", "source": tags[name], "target": node["id"]}
                   for node in nodes for name in node["dependencies"] if name in tags]
    usage_edges = [{"kind": "uses_definition", "source": node["id"], "target": identifier,
                    "occurrence_count": count,
                    "statement_occurrences": node["defined"]["statement_definition_uses"].get(identifier, 0),
                    "local_proposition_occurrences": node["defined"]["script_definition_uses"].get(identifier, 0)}
                   for node in nodes for identifier, count in node["defined"]["definition_uses"].items()]
    definition_edges = [{"kind": "definition_uses_definition", "source": item["id"], "target": dependency}
                        for item in definitions for dependency in item["dependencies"]]
    return {
        "schema": SCHEMA, "family_slug": family.slug, "family_title": family.title,
        "campaign_domain_id": family.domain, "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1], "campaign_milestone_ids": list(family.milestones),
        "root_names": list(family.roots), "nodes": nodes, "definitions": definitions,
        "external_dependencies": external, "edges": proof_edges + usage_edges + definition_edges,
        "node_count": len(nodes), "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges), "external_dependency_count": len(external),
        "definition_count": len(definitions), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((item["topological_layer"] + 1 for item in definitions), default=0),
        "definition_topological_order": [item["id"] for item in definitions],
        "statement_definition_use_count": sum(bool(edge["statement_occurrences"]) for edge in usage_edges),
        "local_proposition_definition_use_count": sum(bool(edge["local_proposition_occurrences"]) for edge in usage_edges),
        "formal_line_count": sum(len(node["script"]) for node in nodes), "candidate_status": STATUS,
        "alpha_edition_version": "v27", "alpha_first_enrolled_version": "v27",
        "alpha_edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"], "alpha_first_enrollment_catalog_sha256": inputs["catalog_sha256"],
        "alpha_proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": inputs["bundle"]["node_count"], "independent_lean_bundle_verified": True,
        "alpha_enrolled_node_count": len(nodes), "alpha_checked_use_node_count": len(nodes),
        "stable_admitted_node_count": 0, "tags": tags, "layers": layers, "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in paths.items()}, "path_policy": "proof_dependency_edges_only",
    }


def _exact_navigation(document: bytes, family: Family, *, prefix: str, revision: str) -> bytes:
    if document.count(b"</nav>") != 1:
        raise SecondWaveExplorerError("the original exact renderer changed its navigation contract")
    extra = _atlas_navigation(family, prefix=prefix, revision=revision).encode()
    return document.replace(b"</nav>", extra + b"</nav>", 1)


LOCAL_NAVIGATION = r'''<script>
(function () {
  "use strict";
  var marker = "/constructive-second-wave-explorer/";
  var offset = location.pathname.indexOf(marker);
  if (offset < 0) return;
  var staticRoot = location.pathname.slice(0, offset);
  var repository = staticRoot.replace(/\/book\/_static$/, "");
  document.querySelectorAll("a[href]").forEach(function (link) {
    var original = link.getAttribute("href");
    if (!original || /^(?:https?:|mailto:|#)/.test(original)) return;
    var destination = new URL(original, location.href);
    if (destination.pathname.indexOf("/grand-campaign/") >= 0) {
      destination.pathname = staticRoot + "/constructive-grand-campaign/";
    } else if (/\/artifacts\/alpha-v27-second-wave-/.test(destination.pathname)) {
      var filename = destination.pathname.slice(destination.pathname.lastIndexOf("/") + 1);
      destination.pathname = repository + "/research/arithmetic-library/" +
        (filename.endsWith(".json") ? "artifacts/" : "") + filename;
    } else return;
    link.setAttribute("href", destination.href);
  });
})();
</script>'''


def _portable_navigation(document: bytes) -> bytes:
    """Keep deployed relative links and make raw local snapshots navigable."""
    if document.count(b"</body>") != 1:
        raise SecondWaveExplorerError("a canonical page lost its document boundary")
    return document.replace(b"</body>", LOCAL_NAVIGATION.encode() + b"\n</body>", 1)


def build_files() -> dict[str, bytes]:
    inputs = _load_inputs()
    revision, files, built = inputs["revision"], {}, []
    for name, path in ASSET_SOURCES.items():
        payload = path.read_bytes()
        if name in ASSET_DIGESTS and _digest(payload) != ASSET_DIGESTS[name]:
            raise SecondWaveExplorerError(f"a canonical QR graph asset changed: {name}")
        files[f"assets/{name}"] = payload
    for family in FAMILIES:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        slug = family.slug
        files[f"{slug}/index.html"] = render_canonical_family_landing(
            family, corpus, revision=revision, current_alpha_version="v27", first_admitted_version="v27",
            bundle_node_count=inputs["bundle"]["node_count"],
        )
        files[f"{slug}/api/corpus.json"] = _json(corpus)
        files[f"{slug}/explorer/index.html"] = _exact_navigation(render_exact_index(
            family, corpus, corpus["tags"], corpus["layers"], stylesheet_href=_asset("exact-explorer.css", "../../"),
            script_href=_asset("exact-explorer.js", "../../"), html_revision=revision,
        ), family, prefix="../../", revision=revision)
        files[f"{slug}/explorer/defined/index.html"] = _defined_index(family, corpus, revision=revision)
        files[f"{slug}/explorer/defined/graph.html"] = _defined_graph(family, corpus, graph, revision=revision)
        files[f"{slug}/explorer/defined/api/graph.json"] = _json(graph)
        for node in corpus["nodes"]:
            tag = node["id"]
            files[f"{slug}/explorer/tag/{tag}.html"] = _exact_navigation(render_exact_theorem(
                family, corpus, node, corpus["tags"], corpus["layers"], stylesheet_href=_asset("exact-explorer.css", "../../../"),
                script_href=_asset("exact-explorer.js", "../../../"), html_revision=revision,
            ), family, prefix="../../../", revision=revision)
            files[f"{slug}/explorer/defined/tag/{tag}.html"] = _defined_theorem(family, corpus, node, revision=revision)
        for definition in corpus["definitions"]:
            files[f"{slug}/explorer/defined/definition/{definition['id']}.html"] = _defined_definition(family, corpus, definition, revision=revision)
        built.append((family, corpus))
    cards = "".join(f'<article class="family-card"><p class="card-kicker">{_e(family.kicker)}</p><h2>{_e(family.title)}</h2>'
                    f'<p>{_e(family.description)}</p><dl class="stats"><div><dt>{corpus["node_count"]}</dt><dd>checked theorems</dd></div>'
                    f'<div><dt>{corpus["definition_count"]}</dt><dd>definitions</dd></div><div><dt>{corpus["edge_count"]}</dt><dd>proof edges</dd></div></dl>'
                    f'<a class="primary-action" href="{_versioned(family.slug + "/", revision)}">Explore the proofs <span aria-hidden="true">→</span></a></article>'
                    for family, corpus in built)
    files["index.html"] = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Constructive second wave — Proof library</title><link rel="stylesheet" href="{_versioned('assets/proofs.css',revision)}"></head><body><header class="hero"><div class="shell"><p class="eyebrow">Alpha v27 · unchanged intuitionistic HA · independently checked in Lean</p><h1>Seven completed second-wave targets</h1><p class="lede">422 new theorems, exact proof trees, readable local propositions, and conservative definition DAGs. Stable remains the separate unchanged 432-theorem edition.</p><nav class="hero-actions"><a class="secondary-action" href="{_versioned('../grand-campaign/',revision)}">Full campaign atlas</a><a class="secondary-action" href="{_versioned('../artifacts/alpha-v27-second-wave-receipt.md',revision)}">Verification receipt</a></nav></div></header><main class="shell"><section class="family-grid" aria-label="Second-wave proof families">{cards}</section><section class="release-note"><p>These seven named targets are complete. Broader roadmap directions, including Jacobi, Tonelli–Shanks, Pell, and Gaussian-integer campaigns, remain separate future work. Exact scope limits are stated on each family page.</p></section></main></body></html>'''.encode()
    for name, payload in tuple(files.items()):
        if name.endswith(".html"):
            files[name] = _portable_navigation(payload)
    inventory = [{"path": name, "bytes": len(payload), "sha256": _digest(payload)} for name, payload in sorted(files.items())]
    files["manifest.json"] = _json({
        "schema": f"{SCHEMA}-manifest", "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["catalog_sha256"], "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_edition_version": "v27", "alpha_first_enrolled_version": "v27",
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"], "independent_lean_bundle_verified": True,
        "inherited_revised_audit_sources": inputs["inherited_revised_audit_sources"],
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["node_count"] for _, corpus in built), "stable_count": 0,
        "families": [{"slug": family.slug, "campaign": family.campaign, "domain": family.domain,
                      "family": family.family_id, "milestones": list(family.milestones),
                      "theorem_count": corpus["node_count"], "definition_count": corpus["definition_count"],
                      "root_tags": {name: corpus["tags"][name] for name in family.roots}}
                     for family, corpus in built],
        "file_count": len(inventory), "inventory_sha256": _digest(_json(inventory)), "files": inventory,
    })
    return files


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        files = build_files()
        if arguments.check:
            actual = {path.relative_to(arguments.output).as_posix() for path in arguments.output.rglob("*") if path.is_file()}
            if actual != set(files) or any((arguments.output / name).read_bytes() != data for name, data in files.items()):
                raise SecondWaveExplorerError("the deterministic second-wave snapshot is stale")
        else:
            for name, data in files.items():
                path = arguments.output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() or path.read_bytes() != data:
                    path.write_bytes(data)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"second-wave explorer: FAIL: {error}", file=sys.stderr)
        return 1
    print(f"second-wave explorer: PASS ({len(files)} deterministic files; no publication)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
