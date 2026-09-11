"""Versioned Jordan reader using the unchanged Quadratic Reciprocity template.

Only the v35 publisher's genuine same-live context authorizes public output.
Private formatters and source compaction provide no proof/admission authority.
There are 95 new theorem pages, 96 raw source lemmas and one inherited alias.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from importlib import import_module
import json
from pathlib import Path
import re

import constructive_checked_explorer_renderer as render
import constructive_completed_lower_publication_v31 as transport
from constructive_formula_compactor import _FormulaCompactor
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_proof_explorer_template import render_canonical_family_landing
from constructive_jordan_definitions_v35 import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME, JORDAN_DEFINITIONS, definition_closure,
)
from build_constructive_gcd_congruence_explorer_v34 import _compact_script, _source, TEMPLATE_PINS

ROOT = Path(__file__).resolve().parents[1]
SLUG = "jordan-totient"
OUTPUT_NAME = "constructive-jordan-explorer-v35"
SCHEMA = "peano-lab-alpha-v35-jordan-explorer-v1"
json_bytes, digest = transport.json_bytes, transport.digest
ExplorerError = transport.PublicationError
ALIASES = {"jordan_tuple_equal_refl": "integer_vector_equal_components_zero"}
ALIAS_TARGET = "integer-linear-algebra/explorer/defined/tag/DL0071.html"
ALIAS_PARENT_PAGE = "book/_static/constructive-historical-explorers-v34/" + ALIAS_TARGET
ALIAS_PARENT_PIN = (31982, "9ef2db482a116faaf019f956526a168c8c8f403071288ea77c17693cde5197e7")


def _require(value, message):
    if not value:
        raise ExplorerError(message)


def research():
    from peano_lab.library import campaign_research_v35_closure
    return campaign_research_v35_closure


def registration():
    return research().research_family(SLUG)


def raw_specs():
    provider = research()
    rows = tuple(provider.raw_owned_specs())
    _require(len(rows) == 96 and len({row.name for row in rows}) == 96,
             "the exact96 source-owned Jordan lemmas changed")
    return rows


def specs():
    rows = tuple(row for row in raw_specs() if row.name not in ALIASES)
    _require(tuple(row.name for row in rows) == registration().owned_names and len(rows) == 95,
             "the95 novel Jordan source rows differ from registration")
    return rows


@dataclass(frozen=True, slots=True)
class Family:
    slug: str = SLUG
    title: str = "Jordan Totients and Primitive Tuples"
    kicker: str = "Actual finite enumerations · tuple CRT · multiplicativity"
    description: str = ("Construct and count primitive tuples, prove Jordan-totient multiplicativity, "
        "and explore exact unit-modulus and prime-power primitivity laws.")
    formula: str = "k>0 ∧ a>0 ∧ b>0 ∧ Coprime(a,b) ⇒ Jₖ(a·b)=Jₖ(a)·Jₖ(b)"
    domain: str = "D01"
    family_id: str = "F01"
    milestones: tuple = ("G008",)
    roots: tuple = ()
    caveat: str = ("95 new Alpha admissions come from 96 source lemmas: tuple equality reflexivity "
        "reuses an already-admitted theorem and is not counted twice. All counts use actual finite "
        "beta-coded enumerations. G008 multiplicativity is proved; the general prime-power count "
        "and distinct-prime product formula are further goals. General prime-power fields (G091) "
        "remain open. Stable is unchanged.")


def family():
    roots = registration().principal_roots
    main = "jordan_totient_multiplicativity_exists"
    return Family(roots=tuple(name for name in roots if name != main) + (main,))


def family_metadata():
    all_tags = {row.name: f"JT{i:04X}" for i, row in enumerate(raw_specs(), 1)}
    return dict(slug=SLUG, title=family().title, theorem_count=95,
        source_owned_theorem_count=96, checked_use_count=95, stable_count=0,
        first_admitted_version="v35", tags={name: tag for name, tag in all_tags.items() if name not in ALIASES},
        package=OUTPUT_NAME, aliases=dict(ALIASES))


def _definition_records(definitions):
    """Same conservative formatter; only eleven new exact syntax arrows audited."""
    by_name, by_id, rows = {d.name: d for d in definitions}, {}, []
    new_names = {d.name for d in JORDAN_DEFINITIONS}
    for item in definitions:
        parents = [by_name[name].stable_id for name in item.conceptual_dependencies]
        _require(set(parents) <= by_id.keys(), "definition parents are not a topological prefix")
        transitive = set(parents)
        for parent in parents:
            transitive.update(by_id[parent]["transitive_dependencies"])
        expansion = _FormulaCompactor(definition_closure(item.conceptual_dependencies)).compact(item.template_source)
        if item.name in new_names:
            for name in item.conceptual_dependencies:
                actual = _FormulaCompactor((by_name[name],)).compact(item.template_source)
                _require(by_name[name].stable_id in actual["statement_definition_uses"],
                         "a Jordan definition arrow lacks an actual expansion occurrence")
        record = dict(id=item.stable_id, name=item.name, parameters=list(item.parameters), arity=item.arity,
            signature=f"{item.name}({','.join(item.parameters)})", summary=item.summary,
            expanded_template=item.template_source, expansion_sha256=digest(item.template_source),
            defined_template=expansion["defined_statement"], defined_template_parts=expansion["statement_parts"],
            dependencies=parents, dependency_names=list(item.conceptual_dependencies),
            topological_layer=max((by_id[p]["topological_layer"] + 1 for p in parents), default=0),
            transitive_dependencies=sorted(transitive),
            origin="shared-hygienic-conservative-definition-not-proof-authority",
            reviewed_definition_id=item.stable_id, shared_definition_identity=item.stable_id,
            global_definition=None, global_argument_positions=None,
            exact_ast_verified=True, kernel_signature_unchanged=True)
        rows.append(record)
        by_id[item.stable_id] = record
    return rows


def _source_only_syntax():
    definitions = definition_closure(tuple(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME))
    compactor = _FormulaCompactor(definitions)
    readings, used = [], set()
    for row in specs():
        reading = compactor.compact(row.statement)
        _compact_script(row, compactor, reading)
        readings.append(reading)
        used.update(reading["definition_uses"])
    mandatory = {row.name for row in JORDAN_DEFINITIONS}
    displayed = definition_closure(tuple(d.name for d in definitions if d.stable_id in used or d.name in mandatory))
    return readings, _definition_records(displayed)


def _flags():
    return dict(checked_use=True, alpha_checked_use=True, enrolled_in_alpha=True,
        admitted_to_alpha=True, stable_member=False, admitted_to_stable=False,
        alpha_edition_version="v35", alpha_first_enrolled_version="v35", first_admitted_version="v35",
        alpha_evidence="alpha_closed", original_ha_bundle_verified=True, independent_lean_bundle_verified=True)


def _validate_data(context):
    """Content validation alone never grants publication authority."""
    record, expected = registration(), specs()
    rows = context.catalog.get("theorems")
    promoted = tuple(row.name for row in research().research_specs())
    _require(type(rows) is list and len(rows) == 4318 and context.catalog.get("checked_use_count") == 4318
        and context.catalog.get("stable_count") == 432 and len(promoted) == 95
        and tuple(context.promoted_names) == promoted
        and tuple(row.get("name") for row in rows[4223:]) == promoted
        and re.fullmatch(r"[a-f0-9]{64}", context.catalog_sha256)
        and context.revision == context.catalog_sha256[:12]
        and context.channels.get("default_channel") == "stable"
        and context.channels["channels"]["alpha"]["artifact_sha256"] == context.catalog_sha256,
        "current Alpha4318/new95/Stable432 source binding changed")
    by_name = {row["name"]: row for row in rows}
    _require(len(by_name) == 4318 and not (set(ALIASES) & by_name.keys())
             and set(ALIASES.values()) <= by_name.keys(), "inherited source alias was recounted")
    from peano_lab.library.theorems import _closed_formula
    raw_by_name = {row.name: row for row in raw_specs()}
    for alias, canonical in ALIASES.items():
        _require(_closed_formula(raw_by_name[alias].statement) == _closed_formula(by_name[canonical]["statement"]),
                 "the source alias is not the identical admitted theorem AST")
    alias_page = transport.read_pinned(ROOT / ALIAS_PARENT_PAGE, *ALIAS_PARENT_PIN)
    _require(b"integer_vector_equal_components_zero" in alias_page and b"first admitted v27" in alias_page,
             "the inherited alias destination or first admission changed")
    report = context.families[SLUG]
    _require(report.get("slug") == SLUG and report.get("new_theorem_count") == 95
        and tuple(row.get("name") for row in report.get("rows", ())) == promoted,
        "Jordan family report differs from95 genuine novel admissions")
    plan = research().research_plan(SLUG)
    positions = plan.positions
    _require(len(plan.specs) == 358 and set(row.name for row in raw_specs()) <= positions.keys(),
             "the exact358-node raw theorem cone changed")
    bundle = report.get("bundle", {})
    required = dict(path=record.artifact, bytes=record.artifact_bytes, sha256=record.artifact_sha256,
        nodes_including_packaging_root=359, dependency_edges_including_packaging=956,
        body_proof_nodes=22165, original_ha_checked=True, independent_lean_checked=True)
    _require(all(type(bundle.get(k)) is type(v) and bundle[k] == v for k, v in required.items()),
             "the exact same-byte whole HA/Lean Jordan96 bundle was not checked")
    normalized = {row.name: row for row in research().research_specs()}
    measurements = {row["name"]: row for row in report["rows"]}
    for spec in expected:
        row, canonical, measured = by_name[spec.name], normalized[spec.name], measurements[spec.name]
        _require(row.get("statement") == canonical.statement == spec.statement
            and row.get("script") == list(canonical.script)
            and row.get("dependencies") == list(canonical.dependencies)
            and row.get("checked_use") is True and row.get("body_checked") is True
            and row.get("membership") == "alpha_only" and measured.get("node_id") == positions[spec.name]
            and measured.get("statement_sha256") == digest(spec.statement)
            and measured.get("proof_nodes", 0) > 0 and measured.get("proof_depth", 0) > 0,
            "an exact Jordan source or checked body differs from current admission")
        closure = row.get("empty_context_closure", {})
        _require(closure.get("status") == "checked" and closure.get("kernel_mode") == "intuitionistic"
            and closure.get("certificate_sha256") == record.artifact_sha256
            and closure.get("bundle_node_id") == positions[spec.name], "a Jordan body lost its exact closed certificate")
    principals = report.get("principal_roots", ())
    _require(tuple(row.get("name") for row in principals) == record.principal_roots
        and all(row.get("complete_ordinary_ha_checked") is True
            and row.get("ordinary_certificate_nodes", 0) > 0
            and row.get("node_id") == positions[row["name"]]
            and row.get("statement_sha256") == digest(normalized[row["name"]].statement)
            for row in principals), "a separate original-HA principal certificate is missing")
    return expected, by_name, report, plan, measurements


def _corpus(context):
    expected, catalog, report, plan, measurements = _validate_data(context)
    readings, definitions = _source_only_syntax()
    tags = family_metadata()["tags"]
    record = registration()
    nodes = []
    for spec, reading in zip(expected, readings, strict=True):
        owner = research().source_for(spec.name)
        measured = measurements[spec.name]
        script_sha = digest("\n".join(spec.script) + "\n")
        nodes.append(dict(id=tags[spec.name], name=spec.name, summary=spec.summary,
            statement=spec.statement, statement_sha256=digest(spec.statement), script=list(spec.script),
            script_sha256=script_sha, dependencies=list(spec.dependencies),
            admission_dependencies=catalog[spec.name]["dependencies"],
            source_module="peano_lab.library." + owner["module"], source_filename=owner["module"] + ".py",
            factory=owner["factory"], sources=[dict(source_module="peano_lab.library." + owner["module"],
                factory=owner["factory"], source_sha256=owner["sha256"], statement_sha256=digest(spec.statement),
                script_sha256=script_sha, selected=True)],
            inventory_role="first_admitted_alpha_v35", status=render._status(_flags()), **_flags(),
            proof_bundle_node_id=plan.positions[spec.name], proof_bundle_sha256=record.artifact_sha256,
            body_proof_nodes=measured["proof_nodes"], body_proof_depth=measured["proof_depth"],
            campaign_milestone="G008", defined=reading))
    direct = {name for spec in expected for name in spec.dependencies if name not in tags}
    external = []
    for spec in plan.specs:
        if spec.name in tags:
            continue
        canonical = ALIASES.get(spec.name, spec.name)
        row = catalog[canonical]
        _require(row.get("checked_use") is True, "a source prerequisite has no admitted meaning")
        external.append(dict(name=spec.name, canonical_admission_name=canonical,
            is_inherited_source_alias=spec.name in ALIASES, statement=spec.statement,
            statement_sha256=digest(spec.statement), script=list(spec.script),
            script_sha256=digest("\n".join(spec.script) + "\n"), dependencies=list(spec.dependencies),
            proof_bundle_node_id=plan.positions[spec.name], inventory_role="inherited_alpha_v34",
            counted_as_new_owned_theorem=False, direct_prerequisite_of_owned_theorem=spec.name in direct,
            parent_alpha_version="v34", alpha_edition_version="v35", alpha_checked_use=True,
            enrolled_in_alpha=True, admitted_to_alpha=True, stable_member=row.get("membership") == "stable",
            first_admission_reclassified=False, source=row.get("source"), evidence_links=row.get("evidence_links", []),
            canonical_catalog_record=row,
            canonical_theorem_route=ALIAS_TARGET if spec.name in ALIASES else None,
            alpha_first_enrolled_version="v27" if spec.name in ALIASES else None,
            reference_route=SLUG + "/checkpoint.html#theorem-" + spec.name))
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        name = node["name"]
        parents = [p for p in node["dependencies"] if p in tags]
        _require(set(parents) <= layers.keys(), "a Jordan proof dependency points forward")
        layers[name] = max((layers[p] + 1 for p in parents), default=0)
        longest = max(parents, key=lambda p: len(paths[p]), default=None)
        paths[name] = ([] if longest is None else paths[longest]) + [tags[name]]
        adjacency[name] = dict(dependencies=parents,
            dependents=[n["name"] for n in nodes if name in n["dependencies"]], critical_root_path=paths[name])
    proof_edges = [dict(kind="proof_dependency", source=tags[p], target=n["id"])
                   for n in nodes for p in n["dependencies"] if p in tags]
    uses = [dict(kind="uses_definition", source=n["id"], target=identifier, occurrence_count=count,
        statement_occurrences=n["defined"]["statement_definition_uses"].get(identifier, 0),
        local_proposition_occurrences=n["defined"]["script_definition_uses"].get(identifier, 0))
        for n in nodes for identifier, count in n["defined"]["definition_uses"].items()]
    definition_edges = [dict(kind="definition_uses_definition", source=d["id"], target=p)
                        for d in definitions for p in d["dependencies"]]
    return dict(schema=SCHEMA, publication_scope="alpha_checked_use_publication", **_flags(),
        family_slug=SLUG, family_title=family().title, campaign_domain_id="D01", campaign_family_id="F01",
        campaign_goal_id="G008", campaign_milestone_ids=["G008"],
        campaign_goal_scope="full_G008_multiplicativity; prime_power_count_and_product_formula_open",
        current_G091_prime_power_fields_proved=False, jordan_prime_power_product_formula_proved=False,
        root_names=list(family().roots), bundle_root_names=list(record.principal_roots), nodes=nodes, definitions=definitions,
        external_dependencies=external, external_theorem_routes={d["name"]: d["reference_route"] for d in external},
        edges=proof_edges + uses + definition_edges, node_count=95, new_theorem_count=95,
        source_owned_theorem_count=96, source_aliases=dict(ALIASES),
        edge_count=sum(len(row.dependencies) for row in expected), internal_edge_count=len(proof_edges),
        external_dependency_count=len(direct), inherited_support_count=263, raw_inherited_support_count=262,
        complete_theorem_count=358, definition_count=len(definitions),
        definition_dependency_count=len(definition_edges),
        definition_layer_count=max((d["topological_layer"] + 1 for d in definitions), default=0),
        definition_topological_order=[d["id"] for d in definitions],
        formal_line_count=sum(len(row.script) for row in expected), candidate_status=render._status(_flags()),
        proof_bundle_sha256=record.artifact_sha256, alpha_proof_bundle_sha256=record.artifact_sha256,
        proof_bundle_node_count=359, checkpoint_report=report, first_alpha_admission_report=report,
        alpha_enrolled_node_count=95, alpha_checked_use_node_count=95, stable_admitted_node_count=0,
        alpha_edition_checked_use_count=4318, stable_edition_count=432, alpha_catalog_sha256=context.catalog_sha256,
        alpha_first_enrollment_catalog_sha256=context.catalog_sha256,
        alpha_edition_identity_sha256=context.catalog["edition_identity_sha256"],
        release_source_binding_sha256=context.source_binding_sha256,
        parent_alpha_edition_version="v34", parent_alpha_checked_use_count=4223,
        navigation_revision=context.revision,
        reserved_tag_slots={f"JT{i:04X}": dict(alias=row.name,
            canonical_admission_name=ALIASES[row.name], counted_as_new=False)
            for i, row in enumerate(raw_specs(), 1) if row.name in ALIASES},
        tags=tags, layers=layers, proof_adjacency=adjacency,
        proof_paths={tags[name]: path for name, path in paths.items()}, path_policy="proof_dependency_edges_only",
        graph_scope="95 novel admissions plus exact inherited support; syntax arrows are not proof premises")


def _checkpoint_page(corpus):
    principals = "".join("<li>" + escape(row["name"]) + ": " + str(row["ordinary_certificate_nodes"])
        + " ordinary certificate nodes</li>" for row in corpus["checkpoint_report"]["principal_roots"])
    external = "".join('<details id="theorem-' + escape(row["name"], quote=True) + '"><summary>'
        + escape(row["name"]) + " — inherited admission: " + escape(row["canonical_admission_name"])
        + '</summary><p>Not a new admission. '
        + ('<a href="../' + row["canonical_theorem_route"] + '">Original DL0071 theorem, first admitted v27</a>. '
           if row["canonical_theorem_route"] else '')
        + '<a href="api/corpus.json">Exact provenance and historical catalog record</a>.</p><pre>'
        + escape(row["statement"]) + "</pre><ol>" + "".join("<li><code>" + escape(line) + "</code></li>"
            for line in row["script"]) + "</ol></details>" for row in corpus["external_dependencies"])
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Jordan totients — exact evidence</title><link rel="stylesheet" href="../assets/proofs.css"></head>'
        '<body class="family-page"><header class="family-hero"><div class="shell"><nav><a href="../">Proof library</a> · '
        '<a href="./">Jordan explorer</a> · <a href="../grand-campaign/?view=goal&amp;focus=G008">G008 atlas</a></nav>'
        '<h1>Jordan totients — exact evidence</h1><p>95 new admissions; 96 original source lemmas. '
        'The tuple-reflexivity source alias reuses integer_vector_equal_components_zero. '
        'Current Alpha 4,318; Stable 432 unchanged. The original HA and independent compiled Lean '
        'checks cover all 359 nodes of the same exact bundle.</p></div></header><main class="shell family-main"><p>'
        + escape(family().caveat) + '</p><h2>Separately checked ordinary roots</h2><ul>' + principals
        + '</ul><p><a href="api/checkpoint.json">Actual live report</a> · <a href="api/first-admission.json">95 first admissions</a></p>'
        + external + '</main></body></html>').encode()


def _render_family(context, corpus):
    """Pure output formatter, not a validator or a publication capability."""
    for relative, expected in TEMPLATE_PINS.items():
        _source(relative, expected=expected)
    item, revision = family(), context.revision
    graph = render._graph_payload(item, corpus, revision=revision)
    graph.update(source_owned_theorem_count=96, new_theorem_count=95, source_aliases=dict(ALIASES),
                 current_G091_prime_power_fields_proved=False)
    base = SLUG + "/"
    files = {base + "index.html": render_canonical_family_landing(item, corpus, revision=revision,
        current_alpha_version="v35", first_admitted_version="v35", bundle_node_count=359),
        base + "checkpoint.html": _checkpoint_page(corpus), base + "api/corpus.json": json_bytes(corpus),
        base + "api/checkpoint.json": json_bytes(corpus["checkpoint_report"]),
        base + "api/first-admission.json": json_bytes([r for r in context.catalog["theorems"] if r["name"] in corpus["tags"]]),
        base + "api/graph.json": json_bytes(graph), base + "explorer/defined/api/graph.json": json_bytes(graph)}
    from constructive_research_publication_v34 import _assets
    files.update(dict(_assets()))
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
    owners = {research().source_for(row.name)["module"]: research().source_for(row.name) for row in raw_specs()}
    for owner in owners.values():
        files["sources/" + owner["module"] + ".py"] = _source(owner["path"], size=owner["bytes"], expected=owner["sha256"])
    record = registration()
    files["artifacts/" + Path(record.artifact).name] = transport.read_pinned(ROOT / record.artifact, record.artifact_bytes, record.artifact_sha256)
    from build_constructive_completed_lower_explorer_v31 import _CurrentHTML, _portable_script
    from constructive_research_publication_v34 import _dashboard_enhancement
    from extend_constructive_jordan_campaign_v35 import parent_files
    packages = json.loads(parent_files()["campaign.json"])["current_proof_family_packages"]
    packages = {**packages, SLUG: OUTPUT_NAME}
    portable = _portable_script(packages)
    old_markers = json.dumps(["/" + transport.OUTPUT_NAME + "/", "/" + transport.HISTORICAL_OUTPUT_NAME + "/"])
    _require(portable.count(old_markers) == 1, "the canonical portable-navigation marker changed")
    portable = portable.replace(old_markers, json.dumps(["/" + OUTPUT_NAME + "/"]), 1)
    portable = portable.replace("/" + transport.ATLAS_NAME + "/index.html", "/constructive-jordan-campaign-v35/index.html")
    dashboard = base + "explorer/defined/index.html"
    for name in tuple(files):
        if name.endswith(".html"):
            is_dashboard = name == dashboard
            layer_choices = tuple(sorted(set(corpus["layers"].values()) |
                {d["topological_layer"] for d in corpus["definitions"]})) if is_dashboard else None
            raw = _CurrentHTML(name, revision,
                portable_script=portable + (_dashboard_enhancement() if is_dashboard else ""),
                layer_choices=layer_choices).finish(files[name])
            marker = b'<meta name="proof-publication-scope" content="alpha-v31-checked-use">'
            _require(raw.count(marker) == 1, "the inherited presentation-only metadata extension changed")
            files[name] = raw.replace(marker,
                b'<meta name="proof-publication-scope" content="alpha-v35-checked-use">', 1)
    _require(all(transport.safe_relative(name) and type(raw) is bytes and raw for name, raw in files.items()),
             "an unsafe or empty canonical reader output was produced")
    return files


def build_files_from_live(context):
    publication = import_module("constructive_jordan_publication_v35")
    publication.require_live(context)
    result = _render_family(context, _corpus(context))
    publication.require_live(context)
    return result
