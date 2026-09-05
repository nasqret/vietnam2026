"""Canonical polynomial Euclidean reader from a genuine live v33 admission.

This module formats authenticated syntax and evidence; it does not check a
proof, accept a stored receipt, write a tree, or deploy anything.  The public
entry point requires the original v33 live capability both before and after
rendering.  Its private formatters are deliberately non-authorizing.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from html import escape
from importlib import import_module
import json
import os
from pathlib import Path
import re
import stat

import constructive_checked_explorer_renderer as render
import constructive_completed_lower_publication_v31 as transport
from constructive_formula_compactor import _FormulaCompactor
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_polynomial_gcd_definitions_v34 import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME, GCD_DEFINITIONS, definition_closure,
)
from constructive_proof_explorer_template import render_canonical_family_landing
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("polynomial-gcd-bezout", "congruence-arithmetic")
SCHEMA = "peano-lab-alpha-v34-gcd-congruence-explorer-v1"
OUTPUT_NAME = "constructive-gcd-congruence-explorer-v34"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
from build_constructive_polynomial_euclidean_explorer_v33 import TEMPLATE_PINS
ExplorerError = transport.PublicationError
digest, json_bytes, strict_json = transport.digest, transport.json_bytes, transport.strict_json

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

def registration(slug):
    if type(slug) is not str or slug not in SLUGS:
        raise ExplorerError("unregistered v34 reader family")
    from peano_lab.library import campaign_research_v34_closure as research
    return research.research_family(slug)


def factories(slug):
    from peano_lab.library import campaign_research_v34_closure as research
    registration(slug)
    return tuple((x.module,x.count,x.source_bytes,x.source_sha256)
                 for x in research.FACTORIES if x.campaign == slug)


def family(slug):
    record=registration(slug)
    if slug == SLUGS[0]:
        return Family(slug,"PG","Prime-Field Polynomial GCD and Bézout",
            "Actual Euclidean descent · normalized gcd · formal uniqueness",
            "Construct a zero-or-monic greatest common right divisor with actual Bézout coefficients over every prime field, including empty and all-zero inputs.",
            "Prime(p) ∧ Coeff(A) ∧ Coeff(B) ⇒ ∃ G U V. NormalizedGcd(G,A,B) ∧ Bezout(A,B,G,U,V)",
            "D04","F10",("G091",),record.principal_roots,slug,
            tuple(x.name for x in GCD_DEFINITIONS),
            "All products and sums use actual beta-coded coefficients; equality is formal coefficient equivalence, not equality of evaluations or raw codes. The zero gcd is included. Uniqueness is up to formal equivalence, not unique Bézout coefficients. This proves the polynomial gcd component, not G091 irreducible-polynomial existence or arbitrary prime-power-field construction.",
            "normalized_polynomial_gcd_bezout_and_formal_uniqueness; full_G091_open")
    return Family(slug,"CG","Congruence Arithmetic",
        "Exact modular equations · actual arithmetic witnesses",
        "Explore the exact twelve newly checked congruence arithmetic statements and their complete original proofs.",
        "Exact registered congruence arithmetic contracts; see each fully quantified theorem.",
        "D01","F02",("G012",),record.principal_roots,slug,(),
        "Each statement retains its explicit modulus, coprimality and divisibility assumptions. These twelve arithmetic laws do not assert all order, primitive-root, Carmichael, exponential or simultaneous-polynomial congruence goals are finished.",
        "exact_registered_congruence_arithmetic_laws; broader_F02_open")

def _specs_digest(rows) -> str:
    result = sha256()
    for row in rows:
        record = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        result.update((json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return result.hexdigest()

def specs(slug):
    record=registration(slug)
    from peano_lab.library import campaign_research_v34_closure as research
    rows=tuple(row for row in research.research_specs() if row.name in set(record.owned_names))
    if (tuple(row.name for row in rows) != record.owned_names or len(rows) != record.count
            or _specs_digest(rows) != record.specs_sha256):
        raise ExplorerError("exact canonical family syntax changed")
    return rows


def family_metadata(slug):
    record=registration(slug); item=family(slug)
    return {"slug":slug,"title":item.title,"theorem_count":record.count,
        "checked_use_count":record.count,"stable_count":0,"first_admitted_version":"v34",
        "tags":{name:f"{item.prefix}{i:04X}" for i,name in enumerate(record.owned_names,1)},
        "package":OUTPUT_NAME}

def _source(relative: str, *, size: int | None = None, expected: str | None = None) -> bytes:
    """Bounded ordinary source read; the enclosing live binding is authority."""
    if not transport.safe_relative(relative):
        raise ExplorerError("foreign or unsafe reader source path")
    path = ROOT / relative
    try:
        ancestors = tuple(path.parents)
        dirs = tuple(parent.lstat() for parent in ancestors)
        if not all(stat.S_ISDIR(row.st_mode) for row in dirs):
            raise ExplorerError("reader source has a symlink or foreign ancestor")
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= MAX_SOURCE_BYTES
                or (size is not None and before.st_size != size)):
            raise ExplorerError("reader source is not an exact bounded ordinary file")
        identity = lambda row: (row.st_dev, row.st_ino, row.st_mode, row.st_nlink,
                                row.st_size, row.st_mtime_ns, row.st_ctime_ns)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            if identity(os.fstat(stream.fileno())) != identity(before):
                raise ExplorerError("reader source changed while opening")
            raw = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
        if (identity(before) != identity(after) or identity(after) != identity(path.lstat())
                or any((a.st_dev, a.st_ino, a.st_mode) != (b.st_dev, b.st_ino, b.st_mode)
                       for a, b in zip(dirs, (parent.lstat() for parent in ancestors), strict=True))):
            raise ExplorerError("reader source changed during bounded read")
    except OSError as error:
        raise ExplorerError("missing or unsafe reader source: " + relative) from error
    if len(raw) != before.st_size or (expected is not None and digest(raw) != expected):
        raise ExplorerError("reader source bytes differ from the exact registration")
    return raw

def source_paths() -> tuple[str, ...]:
    """Relative identities for every directly consumed presentation input."""
    pending = ["scripts/constructive_polynomial_gcd_definitions_v34.py",
               "scripts/constructive_polynomial_gcd_definition_graph_v34.py"]
    found = set()
    while pending:
        relative = pending.pop()
        if relative in found:
            continue
        if len(found) >= 64:
            raise ExplorerError("the bounded notation import graph grew unexpectedly")
        found.add(relative)
        for node in ast.walk(ast.parse(_source(relative))):
            modules = ((node.module,) if isinstance(node, ast.ImportFrom) and node.module
                       else tuple(alias.name for alias in node.names) if isinstance(node, ast.Import)
                       else ())
            for module in modules:
                if re.fullmatch(r"constructive_(?:[a-z0-9_]+_)?(?:definitions|definition_graph|defined_adapter)", module):
                    pending.append("scripts/" + module + ".py")
    found.update(TEMPLATE_PINS)
    found.update("peano-lab/py/peano_lab/library/" + module + ".py" for slug in SLUGS for module, *_ in factories(slug))
    found.update((
        "scripts/build_constructive_gcd_congruence_explorer_v34.py",
        "scripts/constructive_research_publication_v34.py",
        "scripts/build_constructive_completed_lower_explorer_v31.py",
        "scripts/constructive_formula_compactor.py",
        "scripts/constructive_historical_graph_test_support.py",
        "peano-lab/py/peano_lab/library/defined_syntax.py",
        "peano-lab/py/peano_lab/library/defined_edition.py",
        "peano-lab/py/peano_lab/library/bertrand_defined_edition.py",
        "scripts/test_constructive_gcd_congruence_explorer_v34.py",
        "scripts/test_constructive_polynomial_gcd_definitions_v34.py",
        "peano-lab/py/tests/test_constructive_research_publication_v34.py",
        "peano-lab/py/tests/test_constructive_frontier_explorer.py",
        "peano-lab/py/tests/test_constructive_historical_publication_v31.py",
        "peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py",
        "book/_static/pa-proof-explorer/defined/assets/explorer.js",
        "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html",
        "conftest.py", "pytest.ini", "peano-lab/py/tests/conftest.py",
    ))
    found.add("scripts/build_constructive_polynomial_euclidean_explorer_v33.py")
    found.add("scripts/test_constructive_research_publication_source_v34.py")
    return tuple(sorted(found))

def _publication():
    # Importing the source-only family, definitions, or tests never imports the
    # current Alpha edition.  Only this genuine public path needs the guard.
    return import_module("constructive_research_publication_v34")

def _compact_script(row: TheoremSpec, compactor: _FormulaCompactor, reading: dict) -> None:
    """Use the original have/suffices-only conservative display algorithm."""
    scripts, script_parts, uses = [], [], Counter()
    for command in row.script:
        tactic, _, tail = command.partition(" ")
        if tactic == "have" and ":=" in tail:
            from peano_lab.engine.inferred_have import parse_inferred_have
            parse_inferred_have(tail)
            parts = [{"kind": "text", "text": command}]
        elif tactic in {"have", "suffices"}:
            name, separator, proposition = tail.partition(":")
            if not separator or not name.strip() or not proposition.strip():
                raise ExplorerError("malformed actual local proof proposition")
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

def _definition_records(definitions) -> list[dict]:
    by_name, by_id, records = {row.name: row for row in definitions}, {}, []
    for item in definitions:
        dependencies = [by_name[name].stable_id for name in item.conceptual_dependencies]
        if any(identifier not in by_id for identifier in dependencies):
            raise ExplorerError("notation dependencies are not an acyclic prefix")
        transitive = set(dependencies)
        for identifier in dependencies:
            transitive.update(by_id[identifier]["transitive_dependencies"])
        expansion = _FormulaCompactor(definition_closure(item.conceptual_dependencies)).compact(item.template_source)
        # A larger abbreviation can hide a smaller dependency in the display.
        # Check each of the ten new graphs against each child separately;
        # inherited registry identities and their existing arrows stay exact.
        if item.name in {row.name for row in GCD_DEFINITIONS}:
            for name in item.conceptual_dependencies:
                observed = _FormulaCompactor((by_name[name],)).compact(item.template_source)
                if by_name[name].stable_id not in observed["statement_definition_uses"]:
                    raise ExplorerError("a new notation dependency has no actual expansion occurrence")
        record = {"id": item.stable_id, "name": item.name, "parameters": list(item.parameters),
            "arity": item.arity, "signature": f"{item.name}({','.join(item.parameters)})",
            "summary": item.summary, "expanded_template": item.template_source,
            "expansion_sha256": digest(item.template_source),
            "defined_template": expansion["defined_statement"],
            "defined_template_parts": expansion["statement_parts"],
            "dependencies": dependencies, "dependency_names": list(item.conceptual_dependencies),
            "topological_layer": max((by_id[value]["topological_layer"] + 1 for value in dependencies), default=0),
            "transitive_dependencies": sorted(transitive),
            "origin": "shared-hygienic-conservative-definition-not-proof-authority",
            "reviewed_definition_id": item.stable_id, "shared_definition_identity": item.stable_id,
            "global_definition": None, "global_argument_positions": None,
            "exact_ast_verified": True, "kernel_signature_unchanged": True}
        records.append(record)
        by_id[item.stable_id] = record
    return records

def _source_only_syntax(slug):
    """Exact statement/script compaction, with no proof or admission claim."""
    definitions = definition_closure(tuple(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME))
    compactor = _FormulaCompactor(definitions)
    readings, used = [], set()
    for row in specs(slug):
        reading = compactor.compact(row.statement)
        _compact_script(row, compactor, reading)
        readings.append(reading)
        used.update(reading["definition_uses"])
    mandatory = set(family(slug).extra_definitions)
    displayed = definition_closure(tuple(item.name for item in definitions
                                        if item.stable_id in used or item.name in mandatory))
    return readings, _definition_records(displayed)

def _current_flags() -> dict:
    return {"checked_use": True, "alpha_checked_use": True, "enrolled_in_alpha": True,
            "admitted_to_alpha": True, "stable_member": False, "admitted_to_stable": False,
            "alpha_edition_version": "v34", "alpha_first_enrolled_version": "v34",
            "first_admitted_version": "v34", "alpha_evidence": "alpha_closed",
            "original_ha_bundle_verified": True, "independent_lean_bundle_verified": True}

def _validate_principal_records(principals, positions, by_name, slug):
    record=registration(slug)
    keys={"name","node_id","statement_sha256","complete_ordinary_ha_checked","ordinary_certificate_nodes"}
    if (type(principals) is not list or len(principals)!=len(record.principal_roots)
            or any(type(row) is not dict or set(row)!=keys for row in principals)
            or tuple(row["name"] for row in principals)!=record.principal_roots):
        raise ExplorerError("the exact separately checked ordinary roots changed")
    for actual,name in zip(principals,record.principal_roots,strict=True):
        if (type(actual["node_id"]) is not int or actual["node_id"]!=positions[name]
                or actual["statement_sha256"]!=by_name[name]["statement_sha256"]
                or actual["statement_sha256"]!=record.principal_statement_sha256[name]
                or actual["complete_ordinary_ha_checked"] is not True
                or type(actual["ordinary_certificate_nodes"]) is not int
                or actual["ordinary_certificate_nodes"]<=0):
            raise ExplorerError("an actual ordinary certificate was absent or reclassified")


def _validate_data(context,slug):
    """Private content check only; exact-looking metadata never grants authority."""
    from peano_lab.library import campaign_research_v34_closure as research
    record=registration(slug); expected=specs(slug); rows=context.catalog.get("theorems")
    all_names=research.FRONTIER_NEW_NAMES; names=record.owned_names
    if (type(rows) is not list or len(rows)!=4223 or context.catalog.get("checked_use_count")!=4223
            or context.catalog.get("stable_count")!=432 or context.channels.get("default_channel")!="stable"
            or type(context.promoted_names) is not tuple or context.promoted_names!=all_names
            or tuple(row.get("name") for row in rows[4092:])!=all_names
            or tuple(context.families)!=SLUGS or not re.fullmatch(r"[0-9a-f]{64}",context.catalog_sha256)
            or context.revision!=context.catalog_sha256[:12]
            or context.channels["channels"]["alpha"]["artifact_sha256"]!=context.catalog_sha256):
        raise ExplorerError("exact current4223/new131/Stable432 presentation differs")
    report=context.families[slug]
    if (type(report) is not dict or report.get("slug")!=slug
            or type(report.get("new_theorem_count")) is not int or report["new_theorem_count"]!=record.count
            or report.get("specs_sha256")!=record.specs_sha256
            or type(report.get("rows")) is not list or tuple(r.get("name") for r in report["rows"])!=names
            or type(report.get("owned_node_ids")) is not dict or set(report["owned_node_ids"])!=set(names)):
        raise ExplorerError("the source-bound family observation changed")
    bundle=report.get("bundle")
    required={"path":record.artifact,"bytes":record.artifact_bytes,"sha256":record.artifact_sha256,
        "nodes_including_packaging_root":record.node_count,"dependency_edges_including_packaging":record.bundle_edges,
        "body_proof_nodes":record.body_nodes,"packaging_root_id":record.theorem_count,
        "kernel_calls":record.node_count,"original_ha_checked":True,"independent_lean_checked":True}
    if type(bundle) is not dict or any(type(bundle.get(k)) is not type(v) or bundle[k]!=v for k,v in required.items()):
        raise ExplorerError("actual same-byte whole HA/Lean bundle evidence changed")
    by_name={row["name"]:row for row in rows}
    if len(by_name)!=4223: raise ExplorerError("duplicate catalogue theorem identity")
    complete=[]; seen=set(); active=set()
    def visit(name):
        if name not in by_name or name in active: raise ExplorerError("missing or cyclic exact prerequisite")
        if name in seen:return
        active.add(name);row=by_name[name]
        if row.get("checked_use") is not True or row.get("body_checked") is not True:
            raise ExplorerError("unchecked source cone")
        for dependency in row["dependencies"]:visit(dependency)
        active.remove(name);seen.add(name);complete.append(row)
    for name in names:visit(name)
    # Reachability traversal is not the original assembler's artifact order.
    # The immutable v30-prefix/frontier plan determines the literal node IDs.
    if (type(record.ordered_cone_names) is not tuple
            or len(record.ordered_cone_names)!=len(seen)
            or set(record.ordered_cone_names)!=seen):
        raise ExplorerError("the registered artifact order differs from the complete source cone")
    complete=[by_name[name] for name in record.ordered_cone_names]
    positions={row["name"]:i for i,row in enumerate(complete)}
    if (len(complete)!=record.theorem_count or len(seen-set(names))!=record.theorem_count-record.count
            or digest("\n".join(row["name"] for row in complete))!=record.ordered_cone_names_sha256):
        raise ExplorerError("the original assembler artifact node order or complete cone changed")
    for row in complete:
        if any(positions[dependency]>=positions[row["name"]] for dependency in row["dependencies"]):
            raise ExplorerError("the registered artifact order has a forward premise")
    owned=[by_name[name] for name in names]
    owners=[owner for owner in factories(slug) for _ in range(owner[1])]
    for spec,row,observed,owner in zip(expected,owned,report["rows"],owners,strict=True):
        module,_count,_size,source_sha=owner
        if (row["statement"]!=spec.statement or row["script"]!=list(spec.script)
                or row["dependencies"]!=list(spec.dependencies) or row["summary"]!=spec.summary
                or row.get("statement_sha256")!=digest(spec.statement)
                or row.get("script_sha256")!=digest("\n".join(spec.script)+"\n")
                or row.get("membership")!="alpha_only" or row.get("frontier_campaign")!=slug
                or row.get("source",{}).get("path")!="peano-lab/py/peano_lab/library/"+module+".py"
                or row.get("source",{}).get("sha256")!=source_sha
                or row.get("alpha_v34_frontier_enrollment",{}).get("first_enrolled_version")!="v34"
                or type(observed.get("node_id")) is not int or observed["node_id"]!=positions[spec.name]
                or type(report["owned_node_ids"][spec.name]) is not int
                or report["owned_node_ids"][spec.name]!=positions[spec.name]
                or observed.get("statement_sha256")!=row["statement_sha256"]):
            raise ExplorerError("first admission differs from actual source or artifact position")
        receipt,closed=row.get("body_receipt",{}),row.get("empty_context_closure",{})
        for field in ("proof_nodes","proof_depth","proof_objects","proof_edges","reused_objects"):
            if type(observed.get(field)) is not int or observed[field]<0 or receipt.get(field)!=observed[field]:
                raise ExplorerError("displayed metrics differ from actual proof evidence")
        if (observed["proof_nodes"]<=0 or observed["proof_depth"]<=0
                or closed.get("bundle_node_id")!=positions[spec.name]
                or closed.get("certificate_sha256")!=record.artifact_sha256
                or closed.get("bundle_path")!=record.artifact or closed.get("status")!="checked"
                or closed.get("kernel_mode")!="intuitionistic"):
            raise ExplorerError("the owned closed certificate binding changed")
    _validate_principal_records(report.get("principal_roots"),positions,by_name,slug)
    return expected,owned,report,complete,positions

def _corpus(context, slug) -> dict:
    expected, owned, report, complete, positions = _validate_data(context,slug)
    readings, definitions = _source_only_syntax(slug)
    item, tags = family(slug), family_metadata(slug)["tags"]
    nodes = []
    owners = [record for record in factories(slug) for _ in range(record[1])]
    for spec, row, reading, owner, measured in zip(expected, owned, readings, owners, report["rows"], strict=True):
        module, _count, _size, source_sha = owner
        nodes.append({"id": tags[spec.name], "name": spec.name, "summary": spec.summary,
            "statement": spec.statement, "statement_sha256": row["statement_sha256"],
            "script": list(spec.script), "script_sha256": row["script_sha256"],
            "dependencies": list(spec.dependencies), "source_module": "peano_lab.library." + module,
            "source_filename": module + ".py", "factory": "make_" + module + "_theorems",
            "sources": [{"source_module": "peano_lab.library." + module,
                "factory": "make_" + module + "_theorems", "source_sha256": source_sha,
                "statement_sha256": row["statement_sha256"], "script_sha256": row["script_sha256"], "selected": True}],
            "inventory_role": "first_admitted_alpha_v34", "status": render._status(_current_flags()),
            **_current_flags(), "proof_bundle_node_id": positions[spec.name],
            "proof_bundle_sha256": registration(slug).artifact_sha256, "body_proof_nodes": measured["proof_nodes"],
            "body_proof_depth": measured["proof_depth"], "campaign_milestone": item.milestones[0],
            "defined": reading})
    direct = {name for row in expected for name in row.dependencies if name not in tags}
    external = [{"name": row["name"], "statement": row["statement"],
        "statement_sha256": row["statement_sha256"], "script": row["script"],
        "script_sha256": row["script_sha256"], "dependencies": row["dependencies"],
        "proof_bundle_node_id": positions[row["name"]], "inventory_role": "inherited_alpha_v33",
        "counted_as_new_owned_theorem": False, "direct_prerequisite_of_owned_theorem": row["name"] in direct,
        "parent_alpha_version": "v33", "alpha_edition_version": "v34", "alpha_checked_use": True,
        "enrolled_in_alpha": True, "admitted_to_alpha": True,
        "stable_member": row.get("membership") == "stable", "first_admission_reclassified": False,
        "source": row["source"], "evidence_links": row.get("evidence_links", []),
        "reference_route": slug + "/checkpoint.html#theorem-" + row["name"]}
        for row in complete if row["name"] not in tags]
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        name = node["name"]
        parents = [value for value in node["dependencies"] if value in tags]
        if not set(parents) <= layers.keys():
            raise ExplorerError("the family proof graph is not a topological prefix")
        layers[name] = max((layers[parent] + 1 for parent in parents), default=0)
        longest = max(parents, key=lambda parent: len(paths[parent]), default=None)
        paths[name] = ([] if longest is None else paths[longest]) + [tags[name]]
        adjacency[name] = {"dependencies": parents,
            "dependents": [other["name"] for other in nodes if name in other["dependencies"]],
            "critical_root_path": paths[name]}
    proof_edges = [{"kind": "proof_dependency", "source": tags[name], "target": row["id"]}
                   for row in nodes for name in row["dependencies"] if name in tags]
    usage_edges = [{"kind": "uses_definition", "source": row["id"], "target": name,
        "occurrence_count": count,
        "statement_occurrences": row["defined"]["statement_definition_uses"].get(name, 0),
        "local_proposition_occurrences": row["defined"]["script_definition_uses"].get(name, 0)}
        for row in nodes for name, count in row["defined"]["definition_uses"].items()]
    definition_edges = [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                        for row in definitions for parent in row["dependencies"]]
    return {"schema": SCHEMA, "publication_scope": "alpha_checked_use_publication", **_current_flags(),
        "family_slug": slug, "family_title": item.title, "campaign_domain_id": item.domain,
        "campaign_family_id": item.family_id, "campaign_goal_id": item.milestones[0], "campaign_milestone_ids": list(item.milestones),
        "campaign_goal_scope": item.goal_scope, "current_G091_prime_power_fields_proved": False,
        "arbitrary_formal_identity_quotient_uniqueness_proved": False,
        "convolution_associativity_proved": slug == SLUGS[0], "polynomial_gcd_bezout_proved": slug == SLUGS[0],
        "root_names": list(registration(slug).principal_roots), "nodes": nodes, "definitions": definitions,
        "external_dependencies": external,
        "external_theorem_routes": {row["name"]: row["reference_route"] for row in external},
        "edges": proof_edges + usage_edges + definition_edges, "node_count": registration(slug).count, "new_theorem_count": registration(slug).count,
        "edge_count": registration(slug).edge_count, "internal_edge_count": len(proof_edges), "external_dependency_count": len(direct),
        "inherited_support_count": len(complete)-len(owned), "complete_theorem_count": len(complete),
        "definition_count": len(definitions), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((row["topological_layer"] + 1 for row in definitions), default=0),
        "definition_topological_order": [row["id"] for row in definitions],
        "formal_line_count": registration(slug).command_count, "candidate_status": render._status(_current_flags()),
        "proof_bundle_sha256": registration(slug).artifact_sha256, "alpha_proof_bundle_sha256": registration(slug).artifact_sha256,
        "proof_bundle_node_count": registration(slug).node_count, "checkpoint_report": report,
        "first_alpha_admission_report": report, "alpha_enrolled_node_count": len(owned),
        "alpha_checked_use_node_count": len(owned), "stable_admitted_node_count": 0,
        "alpha_edition_checked_use_count": 4223, "stable_edition_count": 432,
        "alpha_catalog_sha256": context.catalog_sha256,
        "alpha_first_enrollment_catalog_sha256": context.catalog_sha256,
        "alpha_edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "release_source_binding_sha256": context.source_binding_sha256,
        "parent_alpha_edition_version": "v33", "parent_alpha_checked_use_count": 4092,
        "navigation_revision": context.revision, "reserved_tag_slots": {}, "tags": tags, "layers": layers,
        "proof_adjacency": adjacency, "proof_paths": {tags[name]: path for name, path in paths.items()},
        "path_policy": "proof_dependency_edges_only",
        "graph_scope": "Exact owned admissions and conservative definitions; inherited bodies linked in exact checkpoint"}

def _checkpoint_page(corpus, revision):
    slug=corpus["family_slug"];item=family(slug);record=registration(slug)
    report=corpus["first_alpha_admission_report"]
    principals="".join('<li>'+escape(row["name"])+': '+str(row["ordinary_certificate_nodes"])+
        ' actual ordinary certificate nodes</li>' for row in report["principal_roots"])
    external="".join('<details id="theorem-'+escape(row["name"],quote=True)+'"><summary>'+escape(row["name"])+
        ' · unchanged support, not a new admission</summary><pre>'+escape(row["statement"])+
        '</pre><ol>'+''.join('<li><code>'+escape(line)+'</code></li>' for line in row["script"])+
        '</ol></details>' for row in corpus["external_dependencies"])
    body='<header class="family-hero"><div class="shell"><h1>'+escape(item.title)+' — exact evidence</h1><p>'
    body+=str(record.count)+' new Alpha v34 admissions; current4223/Stable432. Complete '+str(record.node_count)
    body+='-node bundle checked by original HA and independent compiled Lean. Only the '+str(len(record.principal_roots))+' listed roots claim separate ordinary-certificate checks.</p></div></header>'
    body+='<main class="shell family-main"><p>'+escape(item.caveat)+'</p><ul>'+principals+'</ul><p><a href="api/checkpoint.json">Actual same-live report</a> · <a href="api/first-admission.json">Exact first admissions</a></p>'+external+'</main>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'+escape(item.title)+
        '</title><link rel="stylesheet" href="../assets/proofs.css"></head><body class="proof-library-site">'+body+'</body></html>').encode()

def _render_family(context, corpus: dict) -> dict[str, bytes]:
    """Private presentation; calling it cannot obtain a live capability."""
    slug=corpus["family_slug"];record=registration(slug)
    publication = _publication()
    metadata = family_metadata(slug)
    if metadata not in publication._new_family_metadata() or publication.OUTPUT_NAMES["gcd-congruence"] != OUTPUT_NAME:
        raise ExplorerError("publisher and reader disagree on source-only family routing")
    for relative, expected in TEMPLATE_PINS.items():
        _source(relative, expected=expected)
    item, revision, report = family(slug), context.revision, corpus["first_alpha_admission_report"]
    graph = render._graph_payload(item, corpus, revision=revision)
    graph.update(inherited_support_count=corpus["inherited_support_count"], complete_theorem_count=corpus["complete_theorem_count"],
                 graph_scope=corpus["graph_scope"], current_G091_prime_power_fields_proved=False)
    files = dict(publication._assets())
    base = slug + "/"
    files[base + "index.html"] = render_canonical_family_landing(item, corpus, revision=revision,
        current_alpha_version="v34", first_admitted_version="v34", bundle_node_count=record.node_count)
    files[base + "checkpoint.html"] = _checkpoint_page(corpus, revision)
    files[base + "api/corpus.json"] = json_bytes(corpus)
    files[base + "api/checkpoint.json"] = json_bytes(report)
    files[base + "api/first-admission.json"] = json_bytes([row for row in context.catalog["theorems"] if row["name"] in corpus["tags"]])
    files[base + "api/graph.json"] = files[base + "explorer/defined/api/graph.json"] = json_bytes(graph)
    files[base + "explorer/index.html"] = render_exact_index(item, corpus, corpus["tags"], corpus["layers"],
        stylesheet_href="../../assets/exact-explorer.css?v=" + render.ASSET_DIGESTS["exact-explorer.css"][:12],
        script_href="../../assets/exact-explorer.js?v=" + render.ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=revision)
    files[base + "explorer/defined/index.html"] = render._defined_index(item, corpus, revision=revision)
    files[base + "explorer/defined/graph.html"] = render._defined_graph(item, corpus, graph, revision=revision)
    for node in corpus["nodes"]:
        tag = node["id"]
        files[base + f"explorer/tag/{tag}.html"] = render_exact_theorem(item, corpus, node, corpus["tags"], corpus["layers"],
            stylesheet_href="../../../assets/exact-explorer.css?v=" + render.ASSET_DIGESTS["exact-explorer.css"][:12],
            script_href="../../../assets/exact-explorer.js?v=" + render.ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=revision)
        files[base + f"explorer/defined/tag/{tag}.html"] = render._defined_theorem(item, corpus, node, revision=revision)
    for definition in corpus["definitions"]:
        files[base + f'explorer/defined/definition/{definition["id"]}.html'] = render._defined_definition(item, corpus, definition, revision=revision)
    for module, _count, size, expected in factories(slug):
        files["sources/" + module + ".py"] = _source("peano-lab/py/peano_lab/library/" + module + ".py", size=size, expected=expected)
    bundle = report["bundle"]
    files["artifacts/" + Path(bundle["path"]).name] = transport.read_pinned(ROOT / bundle["path"], record.artifact_bytes, record.artifact_sha256)
    portable = publication._portable_script()
    dashboard = publication._dashboard_enhancement()
    from build_constructive_completed_lower_explorer_v31 import _CurrentHTML
    summaries = frozenset(row["summary"] for row in corpus["nodes"])
    for name in tuple(files):
        if name.endswith(".html"):
            is_dashboard = name == base + "explorer/defined/index.html"
            layers = tuple(sorted(set(corpus["layers"].values())
                                  | {row["topological_layer"] for row in corpus["definitions"]})) if is_dashboard else None
            files[name] = _CurrentHTML(name, revision,
                portable_script=dashboard if is_dashboard else "", layer_choices=layers).finish(files[name])
            files[name] = publication._HistoricalHTML(name, revision,
                graph=graph if name == base + "explorer/defined/graph.html" else None,
                portable_script=portable, protected_summaries=summaries).finish(files[name])
    if any(not transport.safe_relative(name) or type(raw) is not bytes or not raw for name, raw in files.items()):
        raise ExplorerError("a canonical reader output is unsafe or not literal bytes")
    return files

def _render_files(context, corpora):
    publication=_publication();files={}
    metadata=publication._new_family_metadata()
    for corpus in corpora:
        for name,raw in _render_family(context,corpus).items():
            if name in files and files[name]!=raw:raise ExplorerError("conflicting family output")
            files[name]=raw
    files["index.html"]=publication._HistoricalHTML("index.html",context.revision,graph=None,
        portable_script=publication._portable_script()).finish(
            publication._phase_index("gcd-congruence",metadata,context.revision))
    files["publication.json"]=json_bytes({"schema":publication.SCHEMA,"phase":"gcd-congruence",
        "publication_scope":"alpha_checked_use_publication","families":metadata,
        "alpha_edition_version":"v34","alpha_first_enrolled_version":"v34",
        "alpha_edition_checked_use_count":4223,"stable_edition_count":432,"new_theorems":131,
        "catalog_sha256":context.catalog_sha256,"current_G091_prime_power_fields_proved":False,
        "proof_verification_provenance":"genuine_same_live_v34_admission; never_stored_observations"})
    pins={name:{"bytes":len(raw),"sha256":digest(raw)} for name,raw in sorted(files.items())}
    files["manifest.json"]=publication._publication_manifest(context,"gcd-congruence",pins,metadata,
        alpha_first_enrolled_version="v34",theorem_count=131,checked_use_count=131,stable_count=0,
        new_theorem_count=131,ordinary_principal_count=sum(len(registration(slug).principal_roots) for slug in SLUGS))
    return files


def build_files_from_live(context):
    publication=_publication();publication.require_live(context)
    files=_render_files(context,tuple(_corpus(context,slug) for slug in SLUGS))
    publication.require_live(context)
    return files


def _assert_published_content(files,context):
    """Non-authorizing pure output checks; no capability is minted here."""
    files=dict(files)
    manifest=strict_json(files["manifest.json"])
    if (manifest["schema"]!=_publication().SCHEMA+"-manifest"
            or manifest["phase"]!="gcd-congruence" or manifest["theorem_count"]!=131
            or manifest["checked_use_count"]!=131 or manifest["stable_count"]!=0
            or manifest["families"]!=list(_publication()._new_family_metadata())
            or manifest["alpha_edition_version"]!="v34"
            or manifest["alpha_first_enrolled_version"]!="v34"
            or manifest["catalog_sha256"]!=context.catalog_sha256
            or manifest["release_source_binding_sha256"]!=context.source_binding_sha256
            or manifest["file_count_excluding_manifest"]!=len(files)-1
            or set(manifest["files"])!=set(files)-{"manifest.json"}):
        raise ExplorerError("wrong new-family publication scope")
    for name,pin in manifest["files"].items():
        if name not in files or len(files[name])!=pin["bytes"] or digest(files[name])!=pin["sha256"]:
            raise ExplorerError("published bytes differ from exact manifest")
    for slug in SLUGS:
        _validate_data(context,slug)
        corpus=strict_json(files[slug+"/api/corpus.json"])
        if corpus["tags"]!=family_metadata(slug)["tags"] or corpus["alpha_catalog_sha256"]!=context.catalog_sha256:
            raise ExplorerError("published identity or theorem routes changed")
    return True


def _assert_published_files(files,context):
    _publication().require_live(context)
    result=_assert_published_content(files,context)
    _publication().require_live(context)
    return result
