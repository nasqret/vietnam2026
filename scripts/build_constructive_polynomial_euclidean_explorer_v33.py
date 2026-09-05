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
from constructive_polynomial_euclidean_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME, EUCLIDEAN_DEFINITIONS, definition_closure,
)
from constructive_proof_explorer_template import render_canonical_family_landing
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[1]
SLUG, PREFIX = "polynomial-euclidean-division", "PX"
SCHEMA = "peano-lab-alpha-v33-polynomial-euclidean-explorer-v1"
OUTPUT_NAME = "constructive-polynomial-euclidean-explorer-v33"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
SPECS_SHA256 = "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
NAMES_SHA256 = "80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc"
BUNDLE_SHA256 = "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf"
BUNDLE_BYTES, BUNDLE_NODES, BUNDLE_EDGES, BUNDLE_BODY_NODES = 2449379, 377, 1071, 30527
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_division_execution_functional",
    "prime_field_polynomial_division_execution_exists_unique",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent",
    "prime_field_polynomial_convolution_both_left_paddings_exists",
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
PRINCIPAL_NODE_IDS = (343, 344, 366, 367, 368, 371, 372, 375)
FACTORIES = (
    ("prime_field_polynomial_convolution_triangular_candidate", 8, 16677,
     "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("prime_field_polynomial_representation_candidate", 30, 42623,
     "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("prime_field_polynomial_division_candidate", 25, 47986,
     "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("prime_field_polynomial_distributivity_candidate", 18, 26118,
     "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("prime_field_polynomial_division_uniqueness_candidate", 9, 23258,
     "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15"),
    ("prime_field_polynomial_convolution_padding_candidate", 23, 39740,
     "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007"),
    ("prime_field_polynomial_equivalence_candidate", 5, 10469,
     "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373"),
    ("prime_field_polynomial_convolution_congruence_candidate", 3, 8183,
     "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70"),
)
TEMPLATE_PINS = {
    "scripts/constructive_proof_explorer_template.py": "ae0ce39837e84fb1a5d68834234d3cd39c9a4f9f6f03a611f508d399b1c9d105",
    "scripts/constructive_checked_explorer_renderer.py": "7648803e39e73175db7e80adbf1d75079bc0603bbf8a621cbb258b72dda0da31",
    "scripts/constructive_frontier_exact_explorer.py": "9a7b2c6fec9a678193039a9661c83ca1db835f20188dd6a579b414e2fa516555",
}

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


def family() -> Family:
    """Source-only scope; the descriptor cannot confer theorem authority."""
    return Family(
        SLUG, PREFIX, "Prime-Field Polynomial Euclidean Division",
        "Actual division executions · formal coefficient equivalence",
        "Construct quotient and remainder executions over prime fields, prove their formal identity and degree bounds, and transport arithmetic across different highest-degree-first representations.",
        "Prime(p) ∧ BetaPrefixInto(ab,ac,L,p) ∧ FpRepresentedDegree(p,bb,bc,S d,d) ⇒ ∃qb qc q rb rc R. FpPolynomialDivisionExecution(p,ab,ac,L,bb,bc,d,qb,qc,q,rb,rc,R)",
        "D04", "F10", ("G091",), PRINCIPAL_ROOTS, SLUG,
        ("BetaPrefixInto", "FpPolyAdd", "FpPolyScale", "FpInv", "FpConvolutionPrefix",
         "FpConvolutionCoefficient", "FpCoefficientSubtraction", "FpPolynomialTrim",
         "FpRepresentedDegree", "MatrixAffineSlice"),
        "Coefficients are highest-degree-first. The divisor has a nonzero decoded head; primality supplies its actual inverse. Empty quotients and remainders are included. Functionality compares the constructed execution lengths and decoded coefficients, never arbitrary beta codes. Formal polynomial equivalence compares every coefficient, not evaluations on a finite field. The formal identity and remainder-degree bound are proved separately, not assumed by the execution graph. Arbitrary quotient/remainder-pair uniqueness from a formal identity, multiplication associativity, gcd/Bezout, irreducible-polynomial existence, and the full G091 prime-power-field goal remain open. The seven displayed new names are conservative first-order notation, not new kernel primitives.",
        "constructive_division_execution_and_representation_compatibility; full_G091_open",
    )


def _specs_digest(rows) -> str:
    result = sha256()
    for row in rows:
        record = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        result.update((json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return result.hexdigest()


@lru_cache(maxsize=1)
def specs() -> tuple[TheoremSpec, ...]:
    """Exact 121 ordinary factory specifications; no Alpha or proof replay."""
    rows = []
    for module_name, count, _size, _sha in FACTORIES:
        module = import_module("peano_lab.library." + module_name)
        values = tuple(getattr(module, "make_" + module_name + "_theorems")(TheoremSpec))
        if len(values) != count or any(type(row) is not TheoremSpec for row in values):
            raise ExplorerError("canonical polynomial factory ownership changed")
        rows.extend(values)
    result = tuple(rows)
    names = tuple(row.name for row in result)
    if (len(result) != 121 or len(set(names)) != 121 or _specs_digest(result) != SPECS_SHA256
            or digest("\n".join(names)) != NAMES_SHA256
            or sum(len(row.dependencies) for row in result) != 461
            or sum(len(row.script) for row in result) != 9068
            or not set(PRINCIPAL_ROOTS) <= set(names)):
        raise ExplorerError("the exact 121-row canonical polynomial inventory changed")
    return result


def family_metadata() -> dict:
    return {"slug": SLUG, "title": family().title,
            "theorem_count": 121, "checked_use_count": 121, "stable_count": 0,
            "first_admitted_version": "v33",
            "tags": {row.name: f"PX{index:04X}" for index, row in enumerate(specs(), 1)},
            "package": OUTPUT_NAME}


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
    pending = ["scripts/constructive_polynomial_euclidean_definitions.py",
               "scripts/constructive_polynomial_euclidean_definition_graph.py"]
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
    found.update("peano-lab/py/peano_lab/library/" + module + ".py" for module, *_ in FACTORIES)
    found.update((
        "scripts/build_constructive_polynomial_euclidean_explorer_v33.py",
        "scripts/constructive_research_publication_v33.py",
        "scripts/build_constructive_completed_lower_explorer_v31.py",
        "scripts/constructive_formula_compactor.py",
        "scripts/constructive_historical_graph_test_support.py",
        "peano-lab/py/peano_lab/library/defined_syntax.py",
        "peano-lab/py/peano_lab/library/defined_edition.py",
        "peano-lab/py/peano_lab/library/bertrand_defined_edition.py",
        "peano-lab/py/tests/test_constructive_polynomial_euclidean_explorer_v33.py",
        "peano-lab/py/tests/test_constructive_polynomial_euclidean_definitions.py",
        "peano-lab/py/tests/test_constructive_frontier_explorer.py",
        "peano-lab/py/tests/test_constructive_historical_publication_v31.py",
        "peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py",
        "book/_static/pa-proof-explorer/defined/assets/explorer.js",
        "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html",
        "conftest.py", "pytest.ini", "peano-lab/py/tests/conftest.py",
    ))
    return tuple(sorted(found))


def _publication():
    # Importing the source-only family, definitions, or tests never imports the
    # current Alpha edition.  Only this genuine public path needs the guard.
    return import_module("constructive_research_publication_v33")


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
        # Check each of the seven new graphs against each child separately;
        # inherited registry identities and their existing arrows stay exact.
        if item.name in {row.name for row in EUCLIDEAN_DEFINITIONS}:
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


def _source_only_syntax():
    """Exact statement/script compaction, with no proof or admission claim."""
    definitions = definition_closure(tuple(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME))
    compactor = _FormulaCompactor(definitions)
    readings, used = [], set()
    for row in specs():
        reading = compactor.compact(row.statement)
        _compact_script(row, compactor, reading)
        readings.append(reading)
        used.update(reading["definition_uses"])
    mandatory = {item.name for item in EUCLIDEAN_DEFINITIONS} | set(family().extra_definitions)
    displayed = definition_closure(tuple(item.name for item in definitions
                                        if item.stable_id in used or item.name in mandatory))
    return readings, _definition_records(displayed)


def _current_flags() -> dict:
    return {"checked_use": True, "alpha_checked_use": True, "enrolled_in_alpha": True,
            "admitted_to_alpha": True, "stable_member": False, "admitted_to_stable": False,
            "alpha_edition_version": "v33", "alpha_first_enrolled_version": "v33",
            "first_admitted_version": "v33", "alpha_evidence": "alpha_closed",
            "original_ha_bundle_verified": True, "independent_lean_bundle_verified": True}


def _validate_principal_records(principals, positions, by_name):
    """Check normalized family records; only the enclosing report has a slug."""
    keys = {"name", "node_id", "statement_sha256", "complete_ordinary_ha_checked",
            "ordinary_certificate_nodes"}
    if (type(principals) is not list or len(principals) != 8
            or any(type(row) is not dict or set(row) != keys for row in principals)
            or tuple(row["name"] for row in principals) != PRINCIPAL_ROOTS):
        raise ExplorerError("exactly the eight normalized ordinary principals must be recorded")
    for actual, name, node_id in zip(principals, PRINCIPAL_ROOTS, PRINCIPAL_NODE_IDS, strict=True):
        if (type(actual["node_id"]) is not int or actual["node_id"] != node_id
                or positions[name] != node_id
                or actual["statement_sha256"] != by_name[name]["statement_sha256"]
                or actual["complete_ordinary_ha_checked"] is not True
                or type(actual["ordinary_certificate_nodes"]) is not int
                or actual["ordinary_certificate_nodes"] <= 0):
            raise ExplorerError("an ordinary principal was absent, reclassified or unverified")


def _validate_data(context):
    """Private content validation only; a matching dict is never authority."""
    rows = context.catalog.get("theorems")
    expected = specs()
    names = tuple(row.name for row in expected)
    if (type(rows) is not list or len(rows) != 4092
            or context.catalog.get("checked_use_count") != 4092
            or context.catalog.get("stable_count") != 432
            or context.channels.get("default_channel") != "stable"
            or tuple(context.promoted_names) != names
            or tuple(row.get("name") for row in rows[3971:]) != names
            or set(context.families) != {SLUG}
            or not re.fullmatch(r"[0-9a-f]{64}", context.catalog_sha256)
            or context.revision != context.catalog_sha256[:12]
            or context.channels["channels"]["alpha"]["artifact_sha256"] != context.catalog_sha256):
        raise ExplorerError("presentation does not match exact current4092 / first121 / Stable432")
    report = context.families[SLUG]
    if (type(report) is not dict or report.get("slug") != SLUG
            or type(report.get("new_theorem_count")) is not int or report["new_theorem_count"] != 121
            or report.get("specs_sha256") != SPECS_SHA256
            or type(report.get("rows")) is not list or len(report["rows"]) != 121
            or tuple(row.get("name") for row in report["rows"]) != names
            or type(report.get("owned_node_ids")) is not dict
            or set(report["owned_node_ids"]) != set(names)):
        raise ExplorerError("the actual family report lost its exact source inventory")
    bundle = report.get("bundle")
    required = {"bytes": BUNDLE_BYTES, "sha256": BUNDLE_SHA256,
        "nodes_including_packaging_root": BUNDLE_NODES,
        "dependency_edges_including_packaging": BUNDLE_EDGES,
        "body_proof_nodes": BUNDLE_BODY_NODES, "packaging_root_id": 376,
        "kernel_calls": BUNDLE_NODES, "original_ha_checked": True, "independent_lean_checked": True}
    if (type(bundle) is not dict or not transport.safe_relative(bundle.get("path"))
            or any(type(bundle.get(key)) is not type(value) or bundle[key] != value
                   for key, value in required.items())):
        raise ExplorerError("the same-byte complete HA/Lean proof evidence differs")
    principals = report.get("principal_roots")
    by_name = {row["name"]: row for row in rows}
    if len(by_name) != 4092:
        raise ExplorerError("current catalogue repeats a theorem identity")
    seen, pending = set(), list(names)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        if name not in by_name:
            raise ExplorerError("a proof support theorem is absent from the live catalogue")
        seen.add(name)
        pending.extend(by_name[name]["dependencies"])
    complete = [row for row in rows if row["name"] in seen]
    positions = {row["name"]: index for index, row in enumerate(complete)}
    if len(complete) != 376 or len(seen - set(names)) != 255:
        raise ExplorerError("the complete cone must be255 inherited plus121 first-admitted bodies")
    for row in complete:
        if (row.get("checked_use") is not True or row.get("body_checked") is not True
                or any(positions.get(name, 376) >= positions[row["name"]] for name in row["dependencies"])):
            raise ExplorerError("the current proof support has a forward or unchecked dependency")
    owners = [record for record in FACTORIES for _ in range(record[1])]
    for spec, row, observed, owner in zip(expected, rows[3971:], report["rows"], owners, strict=True):
        module, _count, _size, source_sha = owner
        source_path = "peano-lab/py/peano_lab/library/" + module + ".py"
        if (row["statement"] != spec.statement or row["script"] != list(spec.script)
                or row["dependencies"] != list(spec.dependencies) or row["summary"] != spec.summary
                or row.get("statement_sha256") != digest(spec.statement)
                or row.get("script_sha256") != digest("\n".join(spec.script) + "\n")
                or row.get("membership") != "alpha_only"
                or row.get("source", {}).get("path") != source_path
                or row.get("source", {}).get("sha256") != source_sha
                or row.get("frontier_campaign") != SLUG
                or row.get("alpha_v33_frontier_enrollment", {}).get("first_enrolled_version") != "v33"
                or type(observed.get("node_id")) is not int or observed["node_id"] != positions[spec.name]
                or type(report["owned_node_ids"][spec.name]) is not int
                or report["owned_node_ids"][spec.name] != positions[spec.name]
                or observed.get("statement_sha256") != row["statement_sha256"]):
            raise ExplorerError("a first-admission row changed its literal source or proof identity")
        receipt, closed = row.get("body_receipt", {}), row.get("empty_context_closure", {})
        for field in ("proof_nodes", "proof_depth", "proof_objects", "proof_edges", "reused_objects"):
            if (type(observed.get(field)) is not int or observed[field] < 0
                    or receipt.get(field) != observed[field]):
                raise ExplorerError("the displayed proof metrics differ from actual admission")
        if (observed["proof_nodes"] <= 0 or observed["proof_depth"] <= 0
                or closed.get("bundle_node_id") != positions[spec.name]
                or closed.get("certificate_sha256") != BUNDLE_SHA256
                or closed.get("bundle_path") != bundle["path"]
                or closed.get("status") != "checked" or closed.get("kernel_mode") != "intuitionistic"):
            raise ExplorerError("the exact owned dependency-closed certificate binding changed")
    _validate_principal_records(principals, positions, by_name)
    return expected, rows[3971:], report, complete, positions


def _corpus(context) -> dict:
    expected, owned, report, complete, positions = _validate_data(context)
    readings, definitions = _source_only_syntax()
    item, tags = family(), family_metadata()["tags"]
    nodes = []
    owners = [record for record in FACTORIES for _ in range(record[1])]
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
            "inventory_role": "first_admitted_alpha_v33", "status": render._status(_current_flags()),
            **_current_flags(), "proof_bundle_node_id": positions[spec.name],
            "proof_bundle_sha256": BUNDLE_SHA256, "body_proof_nodes": measured["proof_nodes"],
            "body_proof_depth": measured["proof_depth"], "campaign_milestone": "G091",
            "defined": reading})
    direct = {name for row in expected for name in row.dependencies if name not in tags}
    external = [{"name": row["name"], "statement": row["statement"],
        "statement_sha256": row["statement_sha256"], "script": row["script"],
        "script_sha256": row["script_sha256"], "dependencies": row["dependencies"],
        "proof_bundle_node_id": positions[row["name"]], "inventory_role": "inherited_alpha_v32",
        "counted_as_new_owned_theorem": False, "direct_prerequisite_of_owned_theorem": row["name"] in direct,
        "parent_alpha_version": "v32", "alpha_edition_version": "v33", "alpha_checked_use": True,
        "enrolled_in_alpha": True, "admitted_to_alpha": True,
        "stable_member": row.get("membership") == "stable", "first_admission_reclassified": False,
        "source": row["source"], "evidence_links": row.get("evidence_links", []),
        "reference_route": SLUG + "/checkpoint.html#theorem-" + row["name"]}
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
        "family_slug": SLUG, "family_title": item.title, "campaign_domain_id": item.domain,
        "campaign_family_id": item.family_id, "campaign_goal_id": "G091", "campaign_milestone_ids": ["G091"],
        "campaign_goal_scope": item.goal_scope, "current_G091_prime_power_fields_proved": False,
        "arbitrary_formal_identity_quotient_uniqueness_proved": False,
        "convolution_associativity_proved": False, "polynomial_gcd_bezout_proved": False,
        "root_names": list(PRINCIPAL_ROOTS), "nodes": nodes, "definitions": definitions,
        "external_dependencies": external,
        "external_theorem_routes": {row["name"]: row["reference_route"] for row in external},
        "edges": proof_edges + usage_edges + definition_edges, "node_count": 121, "new_theorem_count": 121,
        "edge_count": 461, "internal_edge_count": len(proof_edges), "external_dependency_count": len(direct),
        "inherited_support_count": 255, "complete_theorem_count": 376,
        "definition_count": len(definitions), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((row["topological_layer"] + 1 for row in definitions), default=0),
        "definition_topological_order": [row["id"] for row in definitions],
        "formal_line_count": 9068, "candidate_status": render._status(_current_flags()),
        "proof_bundle_sha256": BUNDLE_SHA256, "alpha_proof_bundle_sha256": BUNDLE_SHA256,
        "proof_bundle_node_count": BUNDLE_NODES, "checkpoint_report": report,
        "first_alpha_admission_report": report, "alpha_enrolled_node_count": 121,
        "alpha_checked_use_node_count": 121, "stable_admitted_node_count": 0,
        "alpha_edition_checked_use_count": 4092, "stable_edition_count": 432,
        "alpha_catalog_sha256": context.catalog_sha256,
        "alpha_first_enrollment_catalog_sha256": context.catalog_sha256,
        "alpha_edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "release_source_binding_sha256": context.source_binding_sha256,
        "parent_alpha_edition_version": "v32", "parent_alpha_checked_use_count": 3971,
        "navigation_revision": context.revision, "reserved_tag_slots": {}, "tags": tags, "layers": layers,
        "proof_adjacency": adjacency, "proof_paths": {tags[name]: path for name, path in paths.items()},
        "path_policy": "proof_dependency_edges_only",
        "graph_scope": "121 first-admitted theorems and conservative definitions;255 inherited bodies linked in exact checkpoint"}


def _checkpoint_page(corpus: Mapping, revision: str) -> bytes:
    report = corpus["first_alpha_admission_report"]
    principal_by_name = {row["name"]: row for row in report["principal_roots"]}
    principal_rows = "".join('<li><a href="' + render._versioned("explorer/defined/tag/" + corpus["tags"][name] + ".html", revision)
        + '">' + escape(name) + '</a> · actual ordinary HA certificate: '
        + str(principal_by_name[name]["ordinary_certificate_nodes"]) + ' nodes</li>' for name in PRINCIPAL_ROOTS)
    external = "".join('<details id="theorem-' + escape(row["name"], quote=True) + '"><summary>'
        + escape(row["name"]) + ' · inherited Alpha-v32 support'
        + (' · Stable member' if row["stable_member"] else ' · not Stable')
        + '</summary><p>Not a new v33 admission. Bundle node ' + str(row["proof_bundle_node_id"])
        + ' · statement SHA-256 <code>' + row["statement_sha256"] + '</code></p><pre><code>'
        + escape(row["statement"]) + '</code></pre><ol>'
        + ''.join('<li><code>' + escape(line) + '</code></li>' for line in row["script"])
        + '</ol></details>' for row in corpus["external_dependencies"])
    body = '<header class="family-hero"><div class="shell"><nav><a href="' + render._versioned("./", revision) + '">'
    body += escape(family().title) + '</a> · <a href="' + render._versioned("../grand-campaign/?view=goal&focus=G091", revision)
    body += '">G091 campaign context</a></nav><h1>Exact admission and proof evidence</h1>'
    body += '<p>121 first admissions to Alpha v33; current Alpha4092 and Stable432. The same complete377-node bundle was checked by original HA and independently by compiled Lean. Its376 theorem bodies comprise121 new and255 unchanged inherited records; one final packaging node is not a theorem.</p></div></header>'
    body += '<main class="shell family-main"><section class="release-note">' + escape(family().caveat) + '</section>'
    body += '<section><h2>Eight complete ordinary-certificate checks</h2><ul>' + principal_rows + '</ul></section>'
    body += '<section><h2>Literal artifacts and first admission</h2><ul>'
    for href, label in (("api/checkpoint.json", "Actual fresh admission report"),
                        ("api/first-admission.json", "Exact first-admission catalogue records"),
                        ("../artifacts/" + Path(report["bundle"]["path"]).name, "Same-byte complete HA/Lean proof bundle")):
        body += '<li><a href="' + render._versioned(href, revision) + '">' + label + '</a></li>'
    for module, *_ in FACTORIES:
        body += '<li><a href="' + render._versioned("../sources/" + module + ".py", revision) + '">' + escape(module) + ': exact canonical source</a></li>'
    body += '</ul><p>All121 bodies have complete bundle checking. Only the eight listed endpoints claim a separately expanded ordinary-certificate run. Historical working observations are not authority for this admission.</p></section>'
    body += '<section><h2>All255 inherited support bodies</h2>' + external + '</section></main>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Polynomial Euclidean division — exact evidence</title><link rel="stylesheet" href="../assets/proofs.css"></head>'
        '<body class="proof-library-site">' + body + '</body></html>').encode()


def _render_files(context, corpus: dict) -> dict[str, bytes]:
    """Private presentation; calling it cannot obtain a live capability."""
    publication = _publication()
    metadata = family_metadata()
    if metadata != publication._new_family_metadata() or publication.OUTPUT_NAMES["polynomial"] != OUTPUT_NAME:
        raise ExplorerError("publisher and reader disagree on source-only family routing")
    for relative, expected in TEMPLATE_PINS.items():
        _source(relative, expected=expected)
    item, revision, report = family(), context.revision, corpus["first_alpha_admission_report"]
    graph = render._graph_payload(item, corpus, revision=revision)
    graph.update(inherited_support_count=255, complete_theorem_count=376,
                 graph_scope=corpus["graph_scope"], current_G091_prime_power_fields_proved=False)
    files = dict(publication._assets())
    base = SLUG + "/"
    files[base + "index.html"] = render_canonical_family_landing(item, corpus, revision=revision,
        current_alpha_version="v33", first_admitted_version="v33", bundle_node_count=BUNDLE_NODES)
    files[base + "checkpoint.html"] = _checkpoint_page(corpus, revision)
    files[base + "api/corpus.json"] = json_bytes(corpus)
    files[base + "api/checkpoint.json"] = json_bytes(report)
    files[base + "api/first-admission.json"] = json_bytes(context.catalog["theorems"][3971:])
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
    for module, _count, size, expected in FACTORIES:
        files["sources/" + module + ".py"] = _source("peano-lab/py/peano_lab/library/" + module + ".py", size=size, expected=expected)
    bundle = report["bundle"]
    files["artifacts/" + Path(bundle["path"]).name] = transport.read_pinned(ROOT / bundle["path"], BUNDLE_BYTES, BUNDLE_SHA256)
    files["index.html"] = publication._phase_index("polynomial", [metadata], revision)
    files["publication.json"] = json_bytes({"schema": publication.SCHEMA, "phase": "polynomial",
        "publication_scope": "alpha_checked_use_publication", "families": [metadata],
        "alpha_edition_version": "v33", "alpha_first_enrolled_version": "v33",
        "alpha_edition_checked_use_count": 4092, "stable_edition_count": 432,
        "catalog_sha256": context.catalog_sha256, "same_byte_ha_and_lean_bundle": BUNDLE_SHA256,
        "ordinary_principal_names": list(PRINCIPAL_ROOTS), "new_theorems": 121,
        "inherited_theorems_not_readmitted": 255, "current_G091_prime_power_fields_proved": False,
        "proof_verification_provenance": "genuine_current_alpha_v33_live_admission; not_stored_working_observations"})
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
    pins = {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in sorted(files.items())}
    files["manifest.json"] = publication._publication_manifest(context, "polynomial", pins, [metadata],
        alpha_first_enrolled_version="v33", theorem_count=121, checked_use_count=121, stable_count=0,
        new_theorem_count=121, inherited_support_count=255, ordinary_principal_count=8,
        proof_bundle_sha256=BUNDLE_SHA256)
    if any(not transport.safe_relative(name) or type(raw) is not bytes or not raw for name, raw in files.items()):
        raise ExplorerError("a canonical reader output is unsafe or not literal bytes")
    return files


def build_files_from_live(context) -> dict[str, bytes]:
    """Only genuine same-live v33 admission can authorize checked-use pages."""
    publication = _publication()
    publication.require_live(context)
    corpus = _corpus(context)
    files = _render_files(context, corpus)
    publication.require_live(context)
    return files


__all__ = ("family", "specs", "family_metadata", "source_paths", "build_files_from_live")
