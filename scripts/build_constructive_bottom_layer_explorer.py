#!/usr/bin/env python3
"""Local-only QR explorers for genuine, non-admitting bottom-layer checkpoints.

The unchanged canonical published renderer requires Alpha admission, so the
new local renderer copies its layout while explicitly denying that authority.
This builder calls the independent checkpoint verifier before rendering any
verified claim. Stored receipts, labels, and hashes never replace proof checks.
No existing publication, catalogue, definition registry, or asset is rewritten.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import gc
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))

import constructive_bottom_layer_checkpoints as checkpoints
import constructive_bottom_layer_explorer_renderer as render
from constructive_formula_compactor import _FormulaCompactor
from peano_lab.engine.state import proof_metrics
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


OUTPUT = ROOT / "book/_static/constructive-bottom-layer-explorer"
SCHEMA = "peano-lab-local-bottom-layer-proof-explorers-v1"
HTML_REVISION = "ac7111ec14ff"
GLOBAL_ATLAS = "../../constructive-gaussian-campaign/"
MAX_PRESENTATION_SOURCE_BYTES = 2 * 1024 * 1024
ASSET_SOURCES = {
    "defined-explorer.css": ROOT / "book/_static/pa-proof-explorer/defined/assets/explorer.css",
    "defined-explorer.js": ROOT / "book/_static/pa-proof-explorer/defined/assets/explorer.js",
    "exact-explorer.css": ROOT / "book/_static/pa-proof-explorer/assets/explorer.css",
    "exact-explorer.js": ROOT / "book/_static/pa-proof-explorer/assets/explorer.js",
    "proofs.css": ROOT / "deploy/proofs/proofs.css",
}
ASSET_DIGESTS = {
    **render.ASSET_DIGESTS,
    "proofs.css": "44ac9983416435ac33efada9eaa3ff914588845fe55932f5e8c54623b28c9285",
}
CANONICAL_TEMPLATE_DIGESTS = {
    "scripts/constructive_proof_explorer_template.py": "ae0ce39837e84fb1a5d68834234d3cd39c9a4f9f6f03a611f508d399b1c9d105",
    "scripts/constructive_checked_explorer_renderer.py": "7648803e39e73175db7e80adbf1d75079bc0603bbf8a621cbb258b72dda0da31",
    "scripts/constructive_frontier_exact_explorer.py": "9a7b2c6fec9a678193039a9661c83ca1db835f20188dd6a579b414e2fa516555",
}


class BottomLayerExplorerError(ValueError):
    """An exact checkpoint, notation, template, or local-only boundary failed."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    prefix: str
    title: str
    kicker: str
    description: str
    formula: str
    domain: str
    family_id: str
    milestones: tuple[str, ...]
    roots: tuple[str, ...]
    definition_route: str
    extra_definitions: tuple[str, ...]
    caveat: str
    goal_scope: str


FAMILIES = (
    Family(
        "euler-units", "EU", "Euler's theorem for units",
        "Actual unit permutations · independently counted totients",
        "Follow the constructed multiplier permutation, the weighted finite product, and the count-prefix induction to an actual power congruent to one.",
        "m>1 ∧ Unit(a,m) ∧ Phi(m,t) ⇒ ∃w. Pow(a,t,w) ∧ ModEq(m,w,1)",
        "D01", "F02", ("G014",),
        ("euler_multiplier_permutation_exists", "euler_unit_product_coprime",
         "euler_unit_count_product_balance", "euler_coprime_totient_power",
         "euler_theorem_for_units"),
        "euler-units", ("Phi", "UnitCount", "PermutationPrefix"),
        "The exact G014 theorem is proved locally for m>1 and genuinely invertible a. Phi counts coprime residues independently of the conclusion. The broader coprime theorem also handles m=1 by congruence, not by asserting that one is a canonical remainder. No multiplicative-order or RSA theorem is claimed. The published atlas and Alpha membership are unchanged.",
        "full_statement_locally_proved_not_admitted",
    ),
    Family(
        "prime-fields", "FP", "Prime-field arithmetic and finite tables",
        "Canonical operations · actual tables · cardinality and characteristic",
        "Construct the actual operations on representatives below a prime, complete beta-coded tables, a finite enumeration, and addition-of-one histories proving exact characteristic.",
        "Prime(p) ⇒ ∃ab ac mb mc nb nc ib ic eb ec. FpFiniteStructure(p,ab,ac,mb,mc,nb,nc,ib,ic,eb,ec)",
        "D04", "F10", ("G091",),
        ("prime_field_arithmetic_laws", "prime_field_operation_tables_exists",
         "prime_field_of_prime_order_exists"),
        "prime-fields", (),
        "This checkpoint constructs prime-order fields (k=1), with genuine finite arithmetic tables, cardinality, and characteristic. Inversion is proved only for nonzero elements; the table's zero entry is a zero-to-zero convention. G091 for every prime power p^k, with an irreducible polynomial of degree k, remains open. No extension-field construction or G091 closure is claimed.",
        "prime_order_subgoal_only_full_G091_open",
    ),
    Family(
        "mobius-values", "MV", "Möbius values and prime adjunction",
        "Independent signed values · squarefreeness · genuine factor lists",
        "Define Möbius values from squarefreeness and the parity of actual prime-factor lists, prove unique values, and trace how a fresh prime changes the sign.",
        "n>0 ⇒ ∃!z. Mobius(n,z); Prime(p) ∧ n>0 ∧ p∤n ⇒ μ(pn)=−μ(n)",
        "D01", "F01", ("G007",),
        ("mobius_value_exists_unique", "mobius_one", "mobius_fresh_prime_negates"),
        "mobius-inversion", ("SignedNegate",),
        "Mobius(n,z) is defined only for positive n. The canonical signed codes are 0 for zero, 2 for +1, and 1 for −1. The function is defined independently of any divisor-sum identity. These values and prime-step lemmas are prerequisites for G007; divisor-sum cancellation and full Möbius inversion remain open in this checkpoint. No signed-table proof is included here.",
        "value_and_prime_step_subgoals_only_full_G007_open",
    ),
    Family(
        "signed-sums", "SS", "Signed arithmetic tables and finite sums",
        "Actual packed tables · witnessed reindexing · permutation invariance",
        "Construct finite signed tables, form their actual prefix sums, and prove that a witnessed permutation preserves the signed sum.",
        "PermutationPrefix(r,s,l) ∧ ArithReindex(F,G,r,s,l) ∧ SignedPrefixSum(F,l,u) ∧ SignedPrefixSum(G,l,v) ⇒ u=v",
        "D01", "F01", ("G007",),
        ("divisor_signed_table_reindex_exists", "divisor_signed_sum_permutation_invariant"),
        "signed-arithmetic", ("PermutationPrefix",),
        "These are genuine signed-table and finite-sum foundations, not full divisor-sum cancellation or Möbius inversion. G007 remains open. The historical MatrixMinorFourCode definition is reused solely as generic nested pairing of four beta parameters; no matrix-specific hypothesis is imported. Equality is equality of represented signed values, not equality of arbitrary component codes.",
        "signed_table_subgoals_only_full_G007_open",
    ),
)


# These unpublished v1 slots belonged to exact duplicates of existing v30
# theorems. Never recycle them or renumber the remaining Euler proof links.
RESERVED_TAG_SLOTS = {
    "euler-units": {3: "euler_modulus_above_one_nonzero", 28: "euler_product_scale_shuffle"},
}


def _tags(family: Family, rows: tuple[TheoremSpec, ...]) -> dict[str, str]:
    reserved = RESERVED_TAG_SLOTS.get(family.slug, {})
    if {row.name for row in rows} & set(reserved.values()):
        raise BottomLayerExplorerError("a superseded duplicate was restored to a reserved proof tag")
    result = {}
    slot = 1
    for row in rows:
        while slot in reserved:
            slot += 1
        result[row.name] = f"{family.prefix}{slot:04X}"
        slot += 1
    return result


def _digest(value: bytes | str) -> str:
    return sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _bounded_source(path: Path, expected_sha256: str | None = None) -> bytes:
    if (not path.is_file() or path.is_symlink()
            or not 0 < path.stat().st_size <= MAX_PRESENTATION_SOURCE_BYTES):
        raise BottomLayerExplorerError(f"missing or unsafe presentation source: {path}")
    with path.open("rb") as handle:
        payload = handle.read(MAX_PRESENTATION_SOURCE_BYTES + 1)
    if len(payload) > MAX_PRESENTATION_SOURCE_BYTES or (
        expected_sha256 is not None and _digest(payload) != expected_sha256
    ):
        raise BottomLayerExplorerError(f"the exact presentation source changed: {path}")
    return payload


def _assets() -> dict[str, bytes]:
    for name, digest in CANONICAL_TEMPLATE_DIGESTS.items():
        _bounded_source(ROOT / name, digest)
    return {"assets/" + name: _bounded_source(path, ASSET_DIGESTS[name])
            for name, path in ASSET_SOURCES.items()}


def _checkpoint(family: Family) -> checkpoints.Checkpoint:
    matches = [item for item in checkpoints.CHECKPOINTS if item.slug == family.slug]
    if len(matches) != 1:
        raise BottomLayerExplorerError("a local family has no exact registered checkpoint")
    return matches[0]


def _family_definitions(family: Family):
    from constructive_bottom_layer_definitions import BOTTOM_LAYER_REGISTRIES, definition_closure
    from peano_lab.library.bertrand_defined_edition import ALL_BERTRAND_DEFINITIONS

    names = tuple(dict.fromkeys((
        *(item.name for item in ALL_BERTRAND_DEFINITIONS),
        *family.extra_definitions,
        *(item.name for route, definitions in BOTTOM_LAYER_REGISTRIES
          if route == family.definition_route for item in definitions),
    )))
    return definition_closure(names)


def _definition_records(specs) -> list[dict[str, Any]]:
    from constructive_bottom_layer_definitions import definition_closure

    by_name = {item.name: item for item in specs}
    by_id: dict[str, dict[str, Any]] = {}
    records = []
    for item in specs:
        dependencies = [by_name[name].stable_id for name in item.conceptual_dependencies]
        if any(identifier not in by_id for identifier in dependencies):
            raise BottomLayerExplorerError("definition dependencies are not an acyclic prefix")
        transitive = set(dependencies)
        for identifier in dependencies:
            transitive.update(by_id[identifier]["transitive_dependencies"])
        expansion = _FormulaCompactor(definition_closure(item.conceptual_dependencies)).compact(item.template_source)
        record = {
            "id": item.stable_id, "name": item.name, "parameters": list(item.parameters),
            "arity": item.arity, "signature": f"{item.name}({','.join(item.parameters)})",
            "summary": item.summary, "expanded_template": item.template_source,
            "expansion_sha256": _digest(item.template_source),
            "defined_template": expansion["defined_statement"],
            "defined_template_parts": expansion["statement_parts"],
            "dependencies": dependencies, "dependency_names": list(item.conceptual_dependencies),
            "topological_layer": max((by_id[name]["topological_layer"] + 1 for name in dependencies), default=0),
            "transitive_dependencies": sorted(transitive),
            "origin": "shared-hygienic-conservative-definition-not-proof-authority",
            "reviewed_definition_id": item.stable_id,
            "shared_definition_identity": item.stable_id,
            # This local map does not insert or impersonate any atlas alias.
            "global_definition": None, "global_argument_positions": None,
            "exact_ast_verified": True, "kernel_signature_unchanged": True,
        }
        records.append(record)
        by_id[item.stable_id] = record
    return records


def _compact_script(spec: TheoremSpec, compactor: _FormulaCompactor, reading: dict[str, Any]) -> None:
    scripts, script_parts, uses = [], [], Counter()
    for command in spec.script:
        tactic, _, tail = command.partition(" ")
        if tactic in {"have", "suffices"}:
            name, separator, proposition = tail.partition(":")
            if not separator or not name.strip() or not proposition.strip():
                raise BottomLayerExplorerError("malformed local proof proposition")
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


def _local_flags() -> dict[str, bool]:
    return {**{key: False for key in render.FORBIDDEN_ADMISSION_FIELDS},
            "local_checkpoint_verified": True, "original_ha_bundle_verified": True,
            "independent_lean_bundle_verified": True}


def _family_corpus(family: Family, evidence: checkpoints.CheckpointEvidence) -> dict[str, Any]:
    """Presentation of the actual verified result, never a proof-check substitute."""
    if (type(evidence) is not checkpoints.CheckpointEvidence
            or evidence.checkpoint != _checkpoint(family)
            or evidence.report.get("membership") != "local_non_admitting_checkpoint"
            or any(evidence.report.get(key) is not False for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"))
            or evidence.report.get("bundle", {}).get("original_ha_checked") is not True
            or evidence.report.get("bundle", {}).get("independent_lean_checked") is not True):
        raise BottomLayerExplorerError("the renderer received no genuine local checkpoint result")
    checkpoint = evidence.checkpoint
    owned_rows = [(pin, row) for pin in checkpoint.modules
                  for row in getattr(import_module(f"peano_lab.library.{pin.module}"), pin.factory)(TheoremSpec)]
    if tuple(row for _, row in owned_rows) != evidence.frontier:
        raise BottomLayerExplorerError("source factories no longer equal the verified frontier")
    tags = _tags(family, evidence.frontier)
    if not set(family.roots) <= tags.keys():
        raise BottomLayerExplorerError("a principal family statement is absent")
    positions = {row.name: row.node_id for row in evidence.plan.rows}
    definitions = _family_definitions(family)
    compactor = _FormulaCompactor(definitions)
    nodes = []
    for owner, row in owned_rows:
        reading = compactor.compact(row.statement)
        _compact_script(row, compactor, reading)
        body_nodes, body_depth = proof_metrics(evidence.bundle.nodes[positions[row.name]].body)
        source = {"source_module": f"peano_lab.library.{owner.module}", "factory": owner.factory,
                  "source_sha256": owner.sha256, "statement_sha256": _digest(row.statement),
                  "script_sha256": _digest("\n".join(row.script) + "\n"), "selected": True}
        nodes.append({
            "id": tags[row.name], "name": row.name, "summary": row.summary,
            "statement": row.statement, "statement_sha256": source["statement_sha256"],
            "script": list(row.script), "dependencies": list(row.dependencies),
            "source_module": source["source_module"], "source_filename": owner.module + ".py",
            "factory": owner.factory, "sources": [source],
            "status": render.STATUS, **_local_flags(),
            "proof_bundle_node_id": positions[row.name], "proof_bundle_sha256": checkpoint.artifact_sha256,
            "body_proof_nodes": body_nodes, "body_proof_depth": body_depth,
            "campaign_milestone": family.milestones[-1], "defined": reading,
        })
    # The broad historical seed supplies familiar notation for compaction;
    # the displayed DAG retains only actual uses, this family's explicit
    # relation vocabulary, and their acyclic ancestors.
    from constructive_bottom_layer_definitions import BOTTOM_LAYER_REGISTRIES, definition_closure
    used_ids = {identifier for node in nodes for identifier in node["defined"]["definition_uses"]}
    family_names = set(family.extra_definitions) | {
        item.name for route, items in BOTTOM_LAYER_REGISTRIES
        if route == family.definition_route for item in items
    }
    displayed = definition_closure(tuple(item.name for item in definitions
                                         if item.stable_id in used_ids or item.name in family_names))
    records = _definition_records(displayed)
    parent_by_name = {row.name: row for row in closure.parent_snapshot().specs}
    external = []
    for name in sorted({name for row in evidence.frontier for name in row.dependencies if name not in tags}):
        if name not in parent_by_name or name not in positions:
            raise BottomLayerExplorerError("an actual closed prerequisite is neither local nor in the pinned parent")
        row = parent_by_name[name]
        external.append({"name": name, "evidence": "inherited_pinned_v30_and_freshly_checked_bundle",
                         "statement": row.statement, "statement_sha256": _digest(row.statement),
                         "proof_bundle_node_id": positions[name], "parent_alpha_version": "v30",
                         "alpha_checked_use": True, "enrolled_in_alpha": True,
                         "admitted_to_alpha": True})
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if any(name not in layers for name in internal):
            raise BottomLayerExplorerError("a theorem dependency is cyclic or forward")
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
    definition_edges = [{"kind": "definition_uses_definition", "source": row["id"], "target": dependency}
                        for row in records for dependency in row["dependencies"]]
    return {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", **_local_flags(),
        "family_slug": family.slug, "family_title": family.title,
        "campaign_domain_id": family.domain, "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1], "campaign_milestone_ids": list(family.milestones),
        "campaign_goal_scope": family.goal_scope, "published_atlas_changed": False,
        "root_names": list(family.roots), "nodes": nodes, "definitions": records,
        "external_dependencies": external,
        "external_theorem_routes": {row["name"]: f"{family.slug}/checkpoint.html#theorem-{row['name']}" for row in external},
        "edges": proof_edges + usage_edges + definition_edges,
        "node_count": len(nodes), "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges), "external_dependency_count": len(external),
        "definition_count": len(records), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((row["topological_layer"] + 1 for row in records), default=0),
        "definition_topological_order": [row["id"] for row in records],
        "formal_line_count": sum(len(node["script"]) for node in nodes), "candidate_status": render.STATUS,
        "proof_bundle_sha256": checkpoint.artifact_sha256,
        "proof_bundle_node_count": evidence.receipt.node_count,
        "checkpoint_report": evidence.report,
        "local_checkpoint_verified_node_count": len(nodes), "alpha_enrolled_node_count": 0,
        "alpha_checked_use_node_count": 0, "stable_admitted_node_count": 0,
        "parent_alpha_edition_version": "v30", "parent_alpha_checked_use_count": 3222,
        "parent_stable_count": 432, "parent_alpha_catalog_sha256": closure.PARENT_CATALOG_SHA256,
        "navigation_revision": HTML_REVISION,
        "reserved_tag_slots": {f"{family.prefix}{slot:04X}": name
                               for slot, name in RESERVED_TAG_SLOTS.get(family.slug, {}).items()},
        "tags": tags, "layers": layers, "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in paths.items()},
        "path_policy": "proof_dependency_edges_only",
    }


def _checkpoint_page(family: Family, corpus: Mapping[str, Any]) -> bytes:
    report = corpus["checkpoint_report"]
    sources = "".join(
        f'<li><a href="{render._versioned("../sources/" + Path(row["path"]).name, HTML_REVISION)}">{render._e(row["path"])}</a> · <code>{row["sha256"]}</code></li>'
        for row in report["sources"])
    theorem_rows = []
    for node in (*corpus["nodes"], *corpus["external_dependencies"]):
        own = node["name"] in corpus["tags"]
        link = (f'<a href="{render._versioned("explorer/defined/tag/" + corpus["tags"][node["name"]] + ".html", HTML_REVISION)}">read theorem</a>'
                if own else "Inherited Alpha v30 premise, freshly checked in this complete bundle")
        theorem_rows.append(
            f'<article class="view-card" id="theorem-{node["name"]}"><h3>{render._e(node["name"])}</h3><p>{link}</p>'
            f'<p>Bundle node {node["proof_bundle_node_id"]}; exact statement SHA-256 <code>{node["statement_sha256"]}</code></p>'
            f'<details><summary>Exact first-order statement</summary><pre>{render._e(node["statement"])}</pre></details></article>')
    bundle_href = render._versioned("../checkpoints/" + Path(report["bundle"]["path"]).name, HTML_REVISION)
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned('./', HTML_REVISION)}">{render._e(family.title)}</a><span>/</span><a href="{render._versioned('../grand-campaign/', HTML_REVISION)}">Local checkpoint map</a></nav>
<h1>Exact local checkpoint receipt</h1><p class="lede">{render._e(render._status(corpus))}</p></div></header>
<main class="shell family-main"><section class="release-note"><strong>Actual complete proof evidence:</strong> {report['bundle']['nodes_including_packaging_root']} original-HA and independent-Lean-checked nodes, {report['bundle']['dependency_edges_including_packaging']} edges including the packaging root. <a href="{bundle_href}">Download literal proof bundle</a>; {report['bundle']['bytes']} bytes; SHA-256 <code>{report['bundle']['sha256']}</code>.</section>
<section class="release-note"><strong>Not a new library edition:</strong> Alpha v30 still has 3222 checked-use theorems; Stable still has 432. This page asserts dependency-closed bundle checks, not a separately replayed ordinary certificate for every root. No Alpha or Stable admission is performed. <a href="{render._versioned('api/checkpoint.json', HTML_REVISION)}">Machine-readable verification report</a>.</section>
<section class="release-note"><strong>Mathematical boundary:</strong> {render._e(family.caveat)}</section>
<section><h2>Exact frozen authoring sources</h2><ul>{sources}</ul><p><a href="{render._versioned('../sources/' + Path(report['rfc']).name, HTML_REVISION)}">Campaign RFC and proof boundary</a></p></section>
<section><h2>Theorems and inherited prerequisites</h2>{''.join(theorem_rows)}</section></main>'''
    return _simple_document("Exact local checkpoint — " + family.title, body, prefix="../")


def _simple_document(title: str, body: str, *, prefix: str) -> bytes:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="proof-publication-scope" content="local-only-checkpoint"><title>{render._e(title)}</title><link rel="stylesheet" href="{render._versioned(prefix + 'assets/proofs.css', HTML_REVISION)}"></head><body class="family-page">{body}</body></html>
'''.encode()


def _dispatch(corpora: list[dict[str, Any]], *, atlas: bool) -> bytes:
    prefix = "../" if atlas else ""
    cards = []
    for family, corpus in zip(FAMILIES, corpora, strict=True):
        goal = family.milestones[-1]
        global_href = render._versioned((GLOBAL_ATLAS if atlas else "../constructive-gaussian-campaign/") + f"?view=goal&focus={goal}", HTML_REVISION)
        cards.append(f'''<article class="view-card" id="{family.slug}" data-local-family="{family.family_id}" data-local-domain="{family.domain}" data-local-goal="{goal}"><p class="card-kicker">{goal} · {render._e(family.family_id)}</p><h2>{render._e(family.title)}</h2><p>{render._e(family.description)}</p><p>{corpus['node_count']} locally verified theorems · {corpus['definition_count']} conservative definitions</p><a href="{render._versioned(prefix + family.slug + '/', HTML_REVISION)}">Enter proof family →</a><p><a href="{render._versioned(prefix + family.slug + '/explorer/defined/graph.html?target=' + corpus['tags'][family.roots[-1]], HTML_REVISION)}">Explore the proof and definition DAG →</a></p><p><a data-campaign-link="historical-goal" href="{global_href}">View unchanged published {goal} roadmap →</a></p><p>{render._e(family.caveat)}</p></article>''')
    global_href = render._versioned(GLOBAL_ATLAS if atlas else "../constructive-gaussian-campaign/", HTML_REVISION)
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned(prefix or './', HTML_REVISION)}">Local proof checkpoints</a><span>/</span><a href="{global_href}">Unchanged published research atlas</a></nav><p class="eyebrow">Constructive arithmetic · local-only development</p><h1>Bottom-layer proof checkpoints</h1><p class="lede">Four actual original-HA and independently compiled Lean checkpoints. This map is a local dispatch page, not an updated global campaign or a new Alpha release.</p></div></header><main class="shell family-main"><section class="view-grid">{''.join(cards)}</section><section class="release-note"><strong>Evidence boundary:</strong> {sum(corpus['node_count'] for corpus in corpora)} new local theorems; no Alpha or Stable admissions. Alpha v30: 3222; Stable: 432. G014 is locally complete. Full G007 and G091 remain open. <a href="{render._versioned(prefix + 'checkpoints.json', HTML_REVISION)}">Inspect exact checkpoint inventory</a>.</section></main>'''
    # The dispatch map has only four local families. Unknown views remain the
    # full local overview; it never edits or impersonates the published atlas.
    body += '''<script>
(function () {
  "use strict";
  var query = new URL(window.location.href).searchParams;
  var field = {family: "data-local-family", domain: "data-local-domain", goal: "data-local-goal"}[query.get("view")];
  var focus = query.get("focus");
  var cards = Array.from(document.querySelectorAll("[data-local-family]"));
  if (!field || !focus || !cards.some(function (card) { return card.getAttribute(field) === focus; })) return;
  cards.forEach(function (card) { card.hidden = card.getAttribute(field) !== focus; });
})();
</script>'''
    return _simple_document("Local bottom-layer proof checkpoints", body, prefix=prefix)


def build_files() -> dict[str, bytes]:
    """Freshly authenticate and check all four proofs before returning pages."""
    files = _assets()
    corpora = []
    for family in FAMILIES:
        checkpoint = _checkpoint(family)
        evidence = checkpoints.verify_checkpoint(checkpoint, ordinary_roots=False)
        corpus = _family_corpus(family, evidence)
        corpora.append(corpus)
        graph = render.graph_payload(family, corpus, revision=HTML_REVISION)
        base = family.slug + "/"
        files[base + "index.html"] = render.render_local_family_landing(
            family, corpus, revision=HTML_REVISION, bundle_node_count=evidence.receipt.node_count)
        files[base + "checkpoint.html"] = _checkpoint_page(family, corpus)
        files[base + "api/corpus.json"] = _json(corpus)
        files[base + "api/graph.json"] = _json(graph)
        files[base + "explorer/defined/api/graph.json"] = _json(graph)
        files[base + "api/checkpoint.json"] = _json(evidence.report)
        files[base + "explorer/index.html"] = render.render_exact_index(
            family, corpus, corpus["tags"], corpus["layers"],
            stylesheet_href="../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
            script_href="../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=HTML_REVISION)
        files[base + "explorer/defined/index.html"] = render.render_defined_index(family, corpus, revision=HTML_REVISION)
        files[base + "explorer/defined/graph.html"] = render.render_defined_graph(family, corpus, graph, revision=HTML_REVISION)
        for node in corpus["nodes"]:
            tag = corpus["tags"][node["name"]]
            files[base + f"explorer/tag/{tag}.html"] = render.render_exact_theorem(
                family, corpus, node, corpus["tags"], corpus["layers"],
                stylesheet_href="../../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
                script_href="../../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=HTML_REVISION)
            files[base + f"explorer/defined/tag/{tag}.html"] = render.render_defined_theorem(family, corpus, node, revision=HTML_REVISION)
        for definition in corpus["definitions"]:
            files[base + f"explorer/defined/definition/{definition['id']}.html"] = render.render_defined_definition(family, corpus, definition, revision=HTML_REVISION)
        # Reauthenticate bytes at the copy boundary as well: a page never
        # silently links a changed authoring file or a different certificate.
        files["checkpoints/" + Path(checkpoint.artifact).name] = closure._read_pinned(
            ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
        for pin in checkpoint.modules:
            files["sources/" + Path(pin.path).name] = checkpoints._source_bytes(pin)
        files["sources/" + Path(checkpoint.rfc).name] = _bounded_source(ROOT / checkpoint.rfc)
        del evidence
        gc.collect()
    inventory = {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "navigation_revision": HTML_REVISION,
        "parent": {"alpha_version": "v30", "alpha_checked_use_count": 3222, "stable_count": 432,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256},
        "independent_checker": {"binary_sha256": checkpoints.LEAN_BINARY_SHA256},
        "checkpoints": [corpus["checkpoint_report"] for corpus in corpora],
    }
    inventory["checkpoint_digest"] = _digest(_json(inventory))
    files["checkpoints.json"] = _json(inventory)
    files["index.html"] = _dispatch(corpora, atlas=False)
    files["grand-campaign/index.html"] = _dispatch(corpora, atlas=True)
    files["manifest.json"] = _json({
        "schema": SCHEMA + "-manifest", "publication_scope": "local-only-checkpoint",
        "checkpoint_digest": inventory["checkpoint_digest"], "navigation_revision": HTML_REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {path: {"bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())},
    })
    return files


def write_or_check(files: Mapping[str, bytes], *, output: Path = OUTPUT, check: bool = False) -> None:
    """Only the new owned tree; unknown files are never silently removed."""
    for name, payload in files.items():
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or ".." in path.parts or "\\" in name
                or str(path) != name or not isinstance(payload, bytes)):
            raise BottomLayerExplorerError("unsafe snapshot path or nonliteral bytes")
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise BottomLayerExplorerError("snapshot output is not a real owned directory")
    existing = set()
    if output.exists():
        for path in output.rglob("*"):
            if path.is_symlink():
                raise BottomLayerExplorerError("snapshot output contains a symlink")
            if path.is_file():
                existing.add(path.relative_to(output).as_posix())
    if existing - files.keys():
        raise BottomLayerExplorerError("unexpected files in local snapshot; nothing was removed")
    if check:
        if existing != files.keys():
            raise BottomLayerExplorerError("the local proof snapshot is stale or incomplete")
        for name, payload in files.items():
            path = output / name
            if path.stat().st_size != len(payload):
                raise BottomLayerExplorerError("the local proof snapshot has an unexpected file size")
            with path.open("rb") as handle:
                actual = handle.read(len(payload) + 1)
            if actual != payload:
                raise BottomLayerExplorerError("the local proof snapshot is stale or incomplete")
        return
    for name, payload in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fresh HA/Lean checks and byte-for-byte local snapshot validation")
    args = parser.parse_args(argv)
    try:
        files = build_files()
        write_or_check(files, check=args.check)
    except (BottomLayerExplorerError, checkpoints.CheckpointError, closure.BottomLayerClosureError, ValueError, OSError) as error:
        print(f"Local bottom-layer explorer refused: {error}", file=sys.stderr)
        return 1
    total = sum(_checkpoint(family).frontier_count for family in FAMILIES)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} local files; {total} locally HA/Lean-verified theorems; Alpha v30 remains 3222 / Stable 432.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
