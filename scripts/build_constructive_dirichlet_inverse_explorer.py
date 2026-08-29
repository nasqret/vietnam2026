#!/usr/bin/env python3
"""Canonical local readers for actual general signed Dirichlet inverses.

Thirteen fresh proof jobs precede a separately bounded pure-render child.
The reviewed earlier transport and QR readers are reused in this module's
private scope, never by patching historical globals or accepting a saved
success receipt. All four earlier research generations remain distinct
from Alpha and from the genuinely new theorem inventory.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import gc
from importlib import import_module
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import secrets
import selectors
import signal
import sys
from tempfile import TemporaryDirectory
import time
from types import FunctionType
from typing import Any

import build_constructive_bottom_layer_explorer as model
import build_constructive_dirichlet_explorer as previous_model
import check_constructive_dirichlet_inverse as audit
import constructive_bottom_layer_checkpoints as bottom
import constructive_bottom_layer_explorer_renderer as render
import constructive_dirichlet_inverse_checkpoints as checkpoints
from constructive_dirichlet_inverse_definitions import (
    DIRICHLET_INVERSE_REGISTRIES, definition_closure,
)
from constructive_dirichlet_inverse_support import SupportSelection, previous_rows
from constructive_formula_compactor import _FormulaCompactor
from peano_lab.engine.state import proof_metrics
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.bertrand_defined_edition import ALL_BERTRAND_DEFINITIONS
from peano_lab.library.proof_bundle import ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec


ROOT = model.ROOT
OUTPUT = ROOT / "book/_static/constructive-dirichlet-inverse-explorer"
SCHEMA = "peano-lab-local-dirichlet-inverse-proof-explorers-v1"
HTML_REVISION = model.HTML_REVISION
ASSET_DIGESTS = model.ASSET_DIGESTS
ExplorerError, Family = model.BottomLayerExplorerError, model.Family
_digest, _json = model._digest, model._json
EXPECTED_FAMILIES = ("dirichlet-signed-units", "dirichlet-triangular", "dirichlet-inverses")
DIRICHLET_REGISTRIES = DIRICHLET_INVERSE_REGISTRIES  # Parameter of the reused pure corpus formatter.
COMPANION_RFCS = {}
RENDER_SCHEMA = "peano-lab-dirichlet-inverse-fresh-render-v1"
RENDER_WALL_SECONDS = audit.WALL_SECONDS
RENDER_TIMEOUT_SECONDS = audit.PARENT_TIMEOUT_SECONDS
MAX_RENDER_MESSAGE_BYTES = audit.MAX_STDERR_BYTES
MAX_RENDER_FILES = closure.DEFAULT_BUNDLE_LIMITS.max_nodes
CONTROLLER_WALL_SECONDS = audit.CONTROLLER_WALL_SECONDS + RENDER_TIMEOUT_SECONDS
PRIOR_RENDER_SOURCE = "scripts/build_constructive_dirichlet_explorer.py"
PRIOR_RENDER_SOURCE_BYTES = 56199
PRIOR_RENDER_SOURCE_SHA256 = "9af696515cbf99a7238e0b8e4c56b0ee17d2ad99463673a6883389b031158c67"
PRIOR_MANIFEST = "book/_static/constructive-dirichlet-explorer/manifest.json"
PRIOR_MANIFEST_BYTES = 72102
PRIOR_MANIFEST_SHA256 = "9755ca72a5e0341e6f42aa8f05253009d36e0950678a917a400961201b36f921"
RENDER_SOURCES = (
    "scripts/build_constructive_dirichlet_inverse_explorer.py",
    "scripts/constructive_dirichlet_inverse_definitions.py",
    "scripts/constructive_dirichlet_inverse_definition_graph.py",
    "scripts/constructive_dirichlet_inverse_defined_adapter.py",
    "peano-lab/py/tests/test_constructive_dirichlet_inverse_explorer.py",
    "peano-lab/py/tests/test_constructive_dirichlet_inverse_render_process.py",
    "peano-lab/py/tests/test_constructive_dirichlet_inverse_render_binding.py",
    *previous_model.RENDER_SOURCES,
)
IMMUTABLE_PRESENTATION_INPUTS = (
    *previous_model.IMMUTABLE_PRESENTATION_INPUTS,
    PRIOR_MANIFEST,
    *previous_model.RENDER_SOURCES,
)


# These are display-only containers, not CheckedProofBundle or kernel receipts.
RenderProcessError = previous_model.RenderProcessError
_RenderResult = previous_model._RenderResult
_FreshRenderEvidence = previous_model._FreshRenderEvidence


def _reuse(function):
    """Bind unchanged reviewed code to this module, leaving old globals alone."""
    scoped = FunctionType(function.__code__, globals(), function.__name__,
                          function.__defaults__, function.__closure__)
    scoped.__kwdefaults__ = None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
    scoped.__annotations__ = dict(function.__annotations__)
    return scoped


if (previous_model.ROOT != ROOT or previous_model.audit.CPU_LIMITS != audit.CPU_LIMITS
        or previous_model.RENDER_WALL_SECONDS != RENDER_WALL_SECONDS
        or previous_model.RENDER_TIMEOUT_SECONDS != RENDER_TIMEOUT_SECONDS
        or previous_model.audit.MAX_RSS_BYTES != audit.MAX_RSS_BYTES
        or previous_model.MAX_RENDER_MESSAGE_BYTES != MAX_RENDER_MESSAGE_BYTES):
    raise RuntimeError("the unchanged pure-render transport contract differs")


_fresh_projection = _reuse(previous_model._fresh_projection)
_checkpoint = _reuse(previous_model._checkpoint)
_definition_records = _reuse(previous_model._definition_records)
_scoped_family_corpus = _reuse(previous_model.family_corpus)
_assert_snapshot_binding = _reuse(previous_model._assert_snapshot_binding)
_validate_render_message = _reuse(previous_model._validate_render_message)
_read_rendered_files = _reuse(previous_model._read_rendered_files)
_render_child = _reuse(previous_model._render_child)
_fork_render_phase = _reuse(previous_model._fork_render_phase)
_build_verified = _reuse(previous_model._build_verified)


def _safe_relative(value, *, prefix="", suffix="") -> bool:
    return (type(value) is str and bool(value) and not PurePosixPath(value).is_absolute()
            and PurePosixPath(value).as_posix() == value
            and all(part not in ("", ".", "..") for part in value.split("/"))
            and value.startswith(prefix) and value.endswith(suffix))


def _checkpoint_metadata():
    """Validate display-input metadata without reparsing theorem statements."""
    groups = (audit.prior_bottom.CHECKPOINTS, audit.prior_lower.CHECKPOINTS,
              audit.prior_continuation.CHECKPOINTS, audit.prior_dirichlet.CHECKPOINTS,
              checkpoints.CHECKPOINTS)
    if any(type(items) is not tuple or not items
           or any(type(item) is not checkpoints.Checkpoint for item in items) for items in groups):
        raise ExplorerError("a registered presentation checkpoint group changed type")
    families()  # Exact current order, cardinalities and three principal roots.
    if any(type(item.principal_roots) is not tuple or len(item.principal_roots) != 3
           for item in checkpoints.CHECKPOINTS):
        raise ExplorerError("the exact three principal roots per current family changed")
    result, artifacts = [], set()
    for items, count in zip(groups, (170, 126, 125, 113, 40), strict=True):
        if type(items) is not tuple or not items:
            raise ExplorerError("a registered presentation checkpoint group changed type")
        records, slugs = [], set()
        for item in items:
            if (type(item) is not checkpoints.Checkpoint or type(item.slug) is not str
                    or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item.slug) is None
                    or item.slug in slugs or type(item.frontier_count) is not int or item.frontier_count < 1
                    or type(item.modules) is not tuple or not item.modules
                    or type(item.principal_roots) is not tuple or not item.principal_roots
                    or len(set(item.principal_roots)) != len(item.principal_roots)
                    or any(type(name) is not str or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", name) is None
                           for name in item.principal_roots)
                    or len(item.principal_roots) > item.frontier_count
                    or not _safe_relative(item.artifact, prefix="research/arithmetic-library/artifacts/", suffix=".json")
                    or item.artifact in artifacts
                    or not _safe_relative(item.rfc, prefix="research/arithmetic-library/", suffix=".md")
                    or type(item.artifact_bytes) is not int
                    or not 0 < item.artifact_bytes <= closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                    or any(type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None
                           for value in (item.artifact_sha256, item.frontier_specs_sha256))):
                raise ExplorerError("registered checkpoint metadata is malformed")
            modules, names = [], set()
            for pin in item.modules:
                if (type(pin) is not checkpoints.ModulePin or type(pin.module) is not str
                        or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", pin.module) is None or pin.module in names
                        or type(pin.sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", pin.sha256) is None
                        or pin.path != f"peano-lab/py/peano_lab/library/{pin.module}.py"
                        or pin.factory != f"make_{pin.module}_theorems"):
                    raise ExplorerError("registered module or factory metadata is malformed")
                modules.append({**asdict(pin), "path": pin.path, "factory": pin.factory})
                names.add(pin.module)
            records.append({**asdict(item), "modules": modules})
            slugs.add(item.slug); artifacts.add(item.artifact)
        if sum(item.frontier_count for item in items) != count:
            raise ExplorerError("a registered research generation changed cardinality")
        result.append(records)
    if sum(map(len, groups)) != 19:
        raise ExplorerError("the exact nineteen registered bundles changed")
    return groups, result


def _render_binding() -> str:
    """Fresh byte/metadata boundary, not a semantic or proof-check receipt.

    The unchanged auditor separately revalidates the complete source/spec
    inventory before and after all thirteen actual proof jobs. Presentation
    boundaries re-read all its inputs but do not reparse 534 old statements.
    No timestamp, previous hash, or successful verification is cached here.
    """
    groups, metadata = _checkpoint_metadata()
    closure._read_pinned(ROOT / PRIOR_RENDER_SOURCE, PRIOR_RENDER_SOURCE_BYTES, PRIOR_RENDER_SOURCE_SHA256)
    sources, bundles, rfcs = {}, [], set()
    for items in groups:
        for item in items:
            for pin in item.modules:
                sources[pin.path] = _digest(bottom._source_bytes(pin))
            closure._read_pinned(ROOT / item.artifact, item.artifact_bytes, item.artifact_sha256)
            bundles.append((item.artifact, item.artifact_bytes, item.artifact_sha256))
            rfcs.add(item.rfc)
    closure._read_pinned(ROOT / closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256)
    bottom._check_lean_binary()
    companions = (*COMPANION_RFCS.values(), *previous_model.COMPANION_RFCS.values())
    paths = (*audit.CONTROL_SOURCES, *RENDER_SOURCES, *IMMUTABLE_PRESENTATION_INPUTS,
             *sorted(rfcs), *(relative for values in companions for relative in values))
    for relative in dict.fromkeys(paths):
        if not _safe_relative(relative):
            raise ExplorerError("a presentation source path is malformed")
        if relative != closure.PARENT_CATALOG:
            sources[relative] = _digest(model._bounded_source(ROOT / relative))
    raw = closure._read_pinned(ROOT / PRIOR_MANIFEST, PRIOR_MANIFEST_BYTES, PRIOR_MANIFEST_SHA256)
    manifest = json.loads(raw)
    if _json(manifest) != raw or type(manifest.get("files")) is not dict:
        raise ExplorerError("the immutable prior snapshot manifest is not canonical")
    for relative, pin in manifest["files"].items():
        if (not _safe_relative(relative) or type(pin) is not dict or set(pin) != {"bytes", "sha256"}
                or type(pin["bytes"]) is not int or not 0 < pin["bytes"] <= closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                or type(pin["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is None):
            raise ExplorerError("an immutable prior snapshot file pin is malformed")
        closure._read_pinned(ROOT / Path(PRIOR_MANIFEST).parent / relative, pin["bytes"], pin["sha256"])
    assets = [(name, _digest(payload)) for name, payload in sorted(model._assets().items())]
    return _digest(audit._canonical({
        "checkpoint_metadata": metadata, "sources": sorted(sources.items()), "bundles": bundles,
        "control_source_order": list(audit.CONTROL_SOURCES), "render_source_order": list(RENDER_SOURCES),
        "immutable_input_order": list(IMMUTABLE_PRESENTATION_INPUTS), "companion_rfcs": companions,
        "parent": [closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256],
        "checker": [str(bottom.LEAN_BINARY), bottom.LEAN_BINARY_BYTES, bottom.LEAN_BINARY_SHA256,
                    checkpoints.LEAN_BINARY_BYTES, checkpoints.LEAN_BINARY_SHA256],
        "prior_snapshot": [PRIOR_MANIFEST, PRIOR_MANIFEST_BYTES, PRIOR_MANIFEST_SHA256], "assets": assets,
    }))


def _retained_table(syntax):
    """Pure lookup from live selected syntax, never a second support search."""
    if type(syntax) is not dict or tuple(syntax) != EXPECTED_FAMILIES:
        raise ExplorerError("all three freshly retained syntax projections are required")
    parent = closure.parent_snapshot().specs
    table = {row.name: row for row in parent}
    if len(table) != len(parent):
        raise ExplorerError("the immutable Alpha syntax has duplicate names")
    for checkpoint in checkpoints.CHECKPOINTS:
        cached = syntax[checkpoint.slug]
        if (type(cached) is not tuple or len(cached) != 2 or type(cached[0]) is not SupportSelection
                or type(cached[1]) is not bytes):
            raise ExplorerError("a fresh audit syntax projection is missing")
        selected, encoded = cached
        expected = audit._decode_message(encoded)
        if (type(expected) is not dict or type(selected.plan) is not closure.BottomLayerPlan
                or type(selected.plan.rows) is not tuple
                or type(selected.owned) is not tuple or type(selected.frontier) is not tuple or not selected.frontier
                or any(type(row) is not TheoremSpec for row in (*selected.owned, *selected.frontier))
                or len(selected.owned) != checkpoint.frontier_count
                or closure._specs_digest(selected.owned) != checkpoint.frontier_specs_sha256
                or closure._specs_digest(selected.frontier) != expected.get("complete_non_alpha_specs_sha256")
                or selected.plan.frontier_specs_sha256 != expected.get("complete_non_alpha_specs_sha256")
                or expected.get("slug") != checkpoint.slug
                or expected.get("new_specs_sha256") != checkpoint.frontier_specs_sha256
                or tuple(row.name for row in selected.frontier) != selected.plan.frontier_names):
            raise ExplorerError("retained syntax differs from its actual source-bound metadata")
        inventory = (*parent, *selected.frontier)
        positions = {row.name: index for index, row in enumerate(inventory)}
        local = {row.name: row for row in inventory}
        if len(local) != len(inventory) or any(local.get(row.name) != row for row in selected.owned):
            raise ExplorerError("retained syntax shadows or omits an actual theorem")
        frontier_names = {row.name for row in selected.frontier}
        role_fields = (("bottom_support", "prior_bottom_layer_theorems"),
                       ("lower_support", "prior_lower_tier_theorems"),
                       ("continuation_support", "prior_lower_continuation_theorems"),
                       ("dirichlet_support", "prior_dirichlet_theorems"),
                       ("current_support", "current_cross_track_theorems"))
        support = expected.get("support", {})
        roles = [getattr(selected, attribute) for attribute, _ in role_fields]
        if (type(support) is not dict
                or any(type(names) is not tuple or any(type(name) is not str for name in names)
                       or list(names) != support.get(key) for names, (_, key) in zip(roles, role_fields, strict=True))):
            raise ExplorerError("retained prerequisite roles differ from the live metadata")
        role_names = tuple(name for names in roles for name in names)
        if (len(set(role_names)) != len(role_names)
                or set(role_names) != frontier_names - {row.name for row in selected.owned}):
            raise ExplorerError("retained prerequisite roles do not partition actual support")
        used = {name for row in selected.frontier for name in row.dependencies}
        roots = tuple(row.name for row in selected.frontier if row.name not in used)
        if roots != selected.plan.root_names:
            raise ExplorerError("the retained maximal proof roots changed")
        seen = set()
        for index, node in enumerate(selected.plan.rows):
            row = local.get(node.name)
            if (type(node) is not closure.BottomLayerRow or row is None or node.name in seen
                    or type(node.node_id) is not int or node.node_id != index
                    or type(node.inventory_index) is not int or node.inventory_index != positions[node.name]
                    or node.statement_sha256 != _digest(row.statement) or node.dependencies != row.dependencies
                    or type(node.is_frontier) is not bool or node.is_frontier != (node.name in frontier_names)
                    or not set(node.dependencies) <= seen):
                raise ExplorerError("a retained proof-plan row differs from its exact theorem")
            seen.add(node.name)
        reached, pending = set(), list(roots)
        while pending:
            name = pending.pop()
            if name not in reached:
                if name not in local:
                    raise ExplorerError("a retained proof prerequisite is missing")
                reached.add(name); pending.extend(local[name].dependencies)
        if (seen != reached or not frontier_names <= seen
                or selected.plan.dependency_edge_count != sum(len(row.dependencies) for row in selected.plan.rows)
                or selected.plan.ordered_names_sha256 != _digest("\n".join(row.name for row in selected.plan.rows))):
            raise ExplorerError("retained proof-plan coverage is incomplete")
        for row in selected.frontier:
            if row.name in table and table[row.name] != row:
                raise ExplorerError("conflicting retained theorem representations")
            table[row.name] = row
    return table


def _validate_fresh_audit(report) -> None:
    if (type(report) is not dict or type(report.get("checkpoints")) is not list
            or report.get("general_dirichlet_inverse_criterion_proved") is not True):
        raise ExplorerError("rendering requires the complete fresh audit and actual inverse principal roots")
    try:
        expected = checkpoints._aggregate_reports(report["checkpoints"])
    except (KeyError, TypeError, ValueError) as error:
        raise ExplorerError("the fresh inverse audit inventory is malformed") from error
    if audit._canonical(report) != audit._canonical(expected):
        raise ExplorerError("the fresh audit scope or inventory changed before rendering")


def _immutable_test_state():
    paths = set(IMMUTABLE_PRESENTATION_INPUTS)
    payload = closure._read_pinned(ROOT / PRIOR_MANIFEST, PRIOR_MANIFEST_BYTES, PRIOR_MANIFEST_SHA256)
    old_manifest = json.loads(payload)
    prior_directory = Path(PRIOR_MANIFEST).parent
    for relative, pin in old_manifest["files"].items():
        path = prior_directory / relative
        closure._read_pinned(ROOT / path, pin["bytes"], pin["sha256"])
        paths.add(path.as_posix())
    for checkpoint in previous_model.checkpoints.CHECKPOINTS:
        paths.update((checkpoint.artifact, checkpoint.rfc))
        for pin in checkpoint.modules:
            paths.add(pin.path)
            paths.add("peano-lab/py/tests/test_" + pin.module + ".py")
    paths.update(previous_model.audit.CONTROL_SOURCES)
    paths.update(relative for values in previous_model.COMPANION_RFCS.values() for relative in values)
    paths.update("peano-lab/py/tests/" + name for name in (
        "test_check_constructive_dirichlet.py", "test_constructive_dirichlet_checkpoints.py",
        "test_constructive_dirichlet_support.py", "test_export_constructive_dirichlet.py",
        "test_constructive_dirichlet_definitions.py", "test_constructive_dirichlet_explorer.py",
        "test_constructive_dirichlet_render_process.py",
    ))
    return ({relative: _digest((ROOT / relative).read_bytes()) for relative in sorted(paths)},
            (model.OUTPUT, model.FAMILIES, previous_model.OUTPUT, previous_model.checkpoints.CHECKPOINTS,
             previous_model.EXPECTED_FAMILIES, previous_model.audit.RECEIPT,
             previous_model._fresh_projection.__globals__["audit"]))


@dataclass(frozen=True, slots=True, eq=False)
class _FreshSnapshotTests:
    """Only this process's live verified snapshot is handed to the UI tests."""

    files: dict[str, bytes]
    binding: str
    immutable_before: tuple

    def pytest_configure(self, config):
        config._dirichlet_inverse_fresh_snapshot = self


def _run_snapshot_tests(files, immutable_before) -> int:
    import pytest
    plugin = _FreshSnapshotTests(files, _assert_snapshot_binding(files), immutable_before)
    return int(pytest.main(["-q", str(ROOT / "peano-lab/py/tests/test_constructive_dirichlet_inverse_explorer.py")],
                          plugins=[plugin]))


def families() -> tuple[Family, ...]:
    by_slug = {item.slug: item for item in checkpoints.CHECKPOINTS}
    if (tuple((item.slug, item.frontier_count) for item in checkpoints.CHECKPOINTS) != checkpoints.EXPECTED_INVENTORY
            or tuple(by_slug) != EXPECTED_FAMILIES):
        raise ExplorerError("all three exact inverse checkpoints must be frozen before rendering")

    def family(slug, prefix, title, subtitle, description, statement, definitions, caveat, scope):
        roots = by_slug[slug].principal_roots
        if slug == "dirichlet-inverses":
            # Presentation order only: the exact three checked principal
            # records keep their immutable registry order in every report.
            roots = tuple(name for name in roots if name != "dirichlet_inverse_criterion") + ("dirichlet_inverse_criterion",)
        return Family(slug, prefix, title, subtitle, description, statement, "D01", "F01", ("G009",),
                      roots, slug, definitions, caveat, scope)

    return (
        family("dirichlet-signed-units", "ZU", "Actual signed units and affine equations",
            "Canonical +1 and -1 · genuine signed products · constructive solutions",
            "Classify every actual signed product equal to one and solve the affine equation needed for finite inversion.",
            "SignedUnit(u) ⇒ ∃a b. SignedMul(a,u,b) ∧ SignedAdd(r,b,e)",
            ("SignedDecode", "SignedMul", "SignedAdd"),
            "Canonical signed +1 is code 2 and -1 is code 1. The two-case unit graph does not assume an inverse or cancellation law: its actual product characterization and affine existence and uniqueness are proved. These scalar lemmas support the separately checked finite inverse criterion; full G009 remains broader.",
            "actual_signed_units_and_affine_solver_full_G009_open"),
        family("dirichlet-triangular", "DT", "Constructed triangular convolution steps",
            "Strict-prefix folds · real table extension · the value at one",
            "Construct the proper convolution prefix before the new endpoint, then append the actual signed product.",
            "ArithAt(F,1,a) ∧ ArithAt(G,1,b) ⇒ (DirichletSum(F,G,1,z) ⇔ SignedMul(a,b,z))",
            ("ArithTable", "ArithAt", "ArithExtend", "ArithTableEqual", "SignedPrefixSum",
             "SignedMul", "SignedAdd", "DirichletEntry", "DirichletPrefix", "DirichletSum", "DirichletTable"),
            "The strict remainder is an actual inclusive prefix through k with an S k-entry fold; the future input at S k is excluded. A genuine table extension supplies the endpoint. The at-one identity inspects or constructs the real two-entry masked sum. No recurrence, inverse, or omitted summand value is assumed as a conclusion-bearing premise.",
            "actual_triangular_convolution_foundation_full_G009_open"),
        family("dirichlet-inverses", "IV", "General finite signed Dirichlet inverses",
            "Arbitrary-target triangular construction · exact criterion · positive uniqueness",
            "Construct the inverse with any prescribed zeroth value, characterize existence, and prove positive-value uniqueness and compatible restrictions.",
            "ArithTable(N,F) ⇒ ((∃G. DirichletInverse(N,F,G)) ⇔ (N=0 ∨ DirichletUnitAtOne(F)))",
            ("SignedUnit", "ArithExtend", "ArithTableEqual", "ArithPositiveEqual", "SignedAdd", "SignedMul",
             "DirichletPrefix", "DirichletSum", "DirichletTable", "KroneckerDeltaTable"),
            "For an actual table, an inverse exists exactly when N=0 or F(1) is signed +1 or -1. At N>0 this is the usual unit-at-one criterion. At N=0 the positive domain is empty and no condition at one is required. Every inverse has actual delta and both convolution witnesses. Its zeroth value is arbitrary, so uniqueness concerns only positive represented values, not table codes or zero. Multiplicative-function closure and the full G009 theory remain open; Alpha, Stable and publication are unchanged.",
            "general_finite_signed_inverse_criterion_locally_proved_full_G009_open"),
    )


def theorem_routes() -> dict[str, str]:
    """Exact new tags and all four immutable prior research-route generations."""
    routes = {}
    for family in families():
        rows = checkpoints.load_rows(_checkpoint(family))
        routes.update({name: f"{family.slug}/explorer/defined/tag/{tag}.html"
                       for name, tag in model._tags(family, rows).items()})
    for name, route in previous_model.theorem_routes().items():
        routes[name] = route if route.startswith("../") else "../constructive-dirichlet-explorer/" + route
    return routes


def family_corpus(family: Family, evidence: _FreshRenderEvidence, *, table=None, routes=None) -> dict[str, Any]:
    corpus = _scoped_family_corpus(family, evidence, table=table, routes=routes)
    corpus["previous_research_generations"] = [170, 126, 125, 113]
    return corpus


def checkpoint_page(family: Family, corpus: Mapping[str, Any]) -> bytes:
    report, support = corpus["checkpoint_report"], corpus["checkpoint_report"]["support"]
    sources = "".join(
        f'<li><a href="{render._versioned("../sources/" + Path(row["path"]).name, HTML_REVISION)}">{render._e(row["path"])}</a> · <code>{row["sha256"]}</code></li>'
        for row in report["sources"])
    theorem_rows = []
    for node in (*corpus["nodes"], *corpus["external_dependencies"]):
        own = node["name"] in corpus["tags"]
        route = ("explorer/defined/tag/" + corpus["tags"][node["name"]] + ".html"
                 if own else "../" + node["reference_route"])
        theorem_rows.append(
            f'<article class="view-card" id="theorem-{node["name"]}"><h3>{render._e(node["name"])}</h3>'
            f'<p>{render._e(node["inventory_role"].replace("_", " "))} · <a href="{render._versioned(route, HTML_REVISION)}">read exact theorem evidence</a></p>'
            f'<p>Bundle node {node["proof_bundle_node_id"]}; exact statement SHA-256 <code>{node["statement_sha256"]}</code></p>'
            f'<details><summary>Exact first-order statement</summary><pre>{render._e(node["statement"])}</pre></details></article>')
    bundle_href = render._versioned("../checkpoints/" + Path(report["bundle"]["path"]).name, HTML_REVISION)
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned('./', HTML_REVISION)}">{render._e(family.title)}</a><span>/</span><a href="{render._versioned('../grand-campaign/', HTML_REVISION)}">Local checkpoint map</a></nav><h1>Exact local checkpoint receipt</h1><p class="lede">{render._e(render._status(corpus))}</p></div></header>
<main class="shell family-main"><section class="release-note"><strong>Actual complete proof evidence:</strong> {report['bundle']['nodes_including_packaging_root']} original-HA and independently compiled Lean-checked nodes. <a href="{bundle_href}">Download literal proof bundle</a>; {report['bundle']['bytes']} bytes; SHA-256 <code>{report['bundle']['sha256']}</code>.</section>
<section class="release-note"><strong>Exact inventory roles:</strong> {report['new_theorem_count']} new owned theorems, {support['prior_bottom_layer_count']} inherited prerequisites from the published 170, {support['prior_lower_tier_count']} from the published 126, {support['prior_lower_continuation_count']} from the previous local 125, {support['prior_dirichlet_count']} from the previous local 113, {support['current_cross_track_count']} current cross-track prerequisites and {support['alpha_v30_count']} inherited Alpha theorems. Support rows are not recounted as new. Source-helper imports are not proof premises. Alpha v30 remains 3222; Stable remains 432. Complete bundle checking is distinct from ordinary-certificate replay, performed separately for each of this family's three principal roots. <a href="{render._versioned('api/checkpoint.json', HTML_REVISION)}">Machine-readable report</a>.</section>
<section class="release-note"><strong>Mathematical boundary:</strong> {render._e(family.caveat)}</section>
<section><h2>Frozen authoring sources</h2><ul>{sources}</ul><p><a href="{render._versioned('../sources/' + Path(report['rfc']).name, HTML_REVISION)}">Exact campaign RFC</a></p></section>
<section><h2>New results and actual inherited prerequisites</h2>{''.join(theorem_rows)}</section></main>'''
    return model._simple_document("Exact local checkpoint — " + family.title, body, prefix="../")


def dispatch(corpora: list[dict[str, Any]], *, atlas: bool) -> bytes:
    prefix, historical_prefix = ("../", "../../") if atlas else ("", "../")
    cards = []
    for family, corpus in zip(families(), corpora, strict=True):
        goal = family.milestones[-1]
        href = render._versioned(prefix + family.slug + "/", HTML_REVISION)
        root = "dirichlet_inverse_criterion" if family.slug == "dirichlet-inverses" else family.roots[-1]
        graph = render._versioned(prefix + family.slug + "/explorer/defined/graph.html?target=" + corpus["tags"][root] + "&view=prerequisites&definitions=selected&edges=focus", HTML_REVISION)
        roadmap = render._versioned(historical_prefix + "constructive-gaussian-campaign/?view=goal&focus=" + goal, HTML_REVISION)
        cards.append(f'''<article class="view-card" id="{family.slug}" data-local-family="{family.family_id}" data-local-domain="{family.domain}" data-local-goal="{goal}" data-local-goals="{render._e(' '.join(family.milestones))}"><p class="card-kicker">{goal} · {family.family_id}</p><h2>{render._e(family.title)}</h2><p>{render._e(family.description)}</p><p>{corpus['node_count']} genuinely new local theorems · {corpus['definition_count']} conservative definitions</p><a href="{href}">Enter proof family →</a><p><a href="{graph}">Explore actual proof and definition dependencies →</a></p><p><a href="{roadmap}">View unchanged {goal} campaign roadmap →</a></p><p>{render._e(family.caveat)}</p></article>''')
    old_links = "".join(
        f'<span>/</span><a href="{render._versioned(historical_prefix + directory + "/", HTML_REVISION)}">{title}</a>'
        for directory, title in (
            ("constructive-bottom-layer-explorer", "Published 170 research proofs"),
            ("constructive-lower-tier-explorer", "Published 126 research proofs"),
            ("constructive-lower-continuation-explorer", "Previous 125 local proofs"),
            ("constructive-dirichlet-explorer", "Previous 113 local proofs"),
            ("constructive-gaussian-campaign", "Unchanged campaign blueprint"),
        ))
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned(prefix or './', HTML_REVISION)}">Local inverse checkpoints</a>{old_links}</nav><p class="eyebrow">Constructive arithmetic · local development</p><h1>General finite signed Dirichlet inverses</h1><p class="lede">Three actual proof checkpoints, connected to all four earlier research generations. The inverse criterion is proved locally with a separate zero-window case, without changing the published atlas or granting Alpha membership.</p></div></header><main class="shell family-main"><section class="view-grid">{''.join(cards)}</section><section class="release-note"><strong>Evidence boundary:</strong> {sum(corpus['node_count'] for corpus in corpora)} distinct new theorems, excluding 534 earlier research theorems and inherited Alpha support. The earlier generations contain 170 and 126 published non-admitted theorems, followed by 125 and 113 local non-admitted theorems. Alpha v30 remains 3222; Stable remains 432. General finite signed inverse existence is characterized by N=0 or F(1)=+1 or -1. Full G009 still requires multiplicative-function closure; general G091 prime-power fields remain open. The earlier local Möbius inversion checkpoint is retained at its original route. <a href="{render._versioned(prefix + 'checkpoints.json', HTML_REVISION)}">Exact checkpoint inventory</a>.</section></main>'''
    # The existing tiny dispatch interaction is copied literally; its only
    # inputs are actual data-local-* attributes on the new three cards.
    body += '''<script>
(function () {
  "use strict";
  var query = new URL(window.location.href).searchParams;
  var field = {family: "data-local-family", domain: "data-local-domain", goal: "data-local-goal"}[query.get("view")];
  var focus = query.get("focus");
  var cards = Array.from(document.querySelectorAll("[data-local-family]"));
  function matches(card) {
    var values = field === "data-local-goal" ? card.getAttribute("data-local-goals").split(" ") : [card.getAttribute(field)];
    return values.indexOf(focus) !== -1;
  }
  if (!field || !focus || !cards.some(matches)) return;
  cards.forEach(function (card) { card.hidden = !matches(card); });
})();
</script>'''
    return model._simple_document("Local general Dirichlet inverse checkpoints", body, prefix=prefix)


def _render_files(fresh_report, syntax, binding) -> dict[str, bytes]:
    """Pure projection of this live run; no selection or proof checks here."""
    selected_families = families()
    _validate_fresh_audit(fresh_report)
    if type(syntax) is not dict or tuple(syntax) != EXPECTED_FAMILIES:
        raise ExplorerError("all three freshly retained syntax projections are required")
    if _render_binding() != binding:
        raise ExplorerError("proof or presentation sources changed during the fresh audit")
    reports = {item["slug"]: item for item in fresh_report["checkpoints"]}
    files, corpora = model._assets(), []
    table = _retained_table(syntax)
    routes = theorem_routes()
    for family in selected_families:
        checkpoint = _checkpoint(family)
        evidence = _fresh_projection(checkpoint, reports[family.slug], syntax[family.slug])
        corpus = family_corpus(family, evidence, table=table, routes=routes)
        corpora.append(corpus)
        graph = render.graph_payload(family, corpus, revision=HTML_REVISION)
        base = family.slug + "/"
        files[base + "index.html"] = render.render_local_family_landing(family, corpus, revision=HTML_REVISION,
            bundle_node_count=evidence.report["bundle"]["nodes_including_packaging_root"])
        files[base + "checkpoint.html"] = checkpoint_page(family, corpus)
        files[base + "api/corpus.json"] = _json(corpus)
        files[base + "api/graph.json"] = files[base + "explorer/defined/api/graph.json"] = _json(graph)
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
        files["checkpoints/" + Path(checkpoint.artifact).name] = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
        for pin in checkpoint.modules:
            files["sources/" + Path(pin.path).name] = bottom._source_bytes(pin)
        files["sources/" + Path(checkpoint.rfc).name] = model._bounded_source(ROOT / checkpoint.rfc)
        del evidence
        gc.collect()
    inventory = {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "navigation_revision": HTML_REVISION, "new_theorems": sum(corpus["node_count"] for corpus in corpora),
        "previous_research_theorems": 534, "previous_research_generations": [170, 126, 125, 113],
        "prior_theorem_count_for_exact_ast_novelty_check": 3756,
        "inherited_support_counted_as_new": False,
        "statement_asts_distinct_from_all_3756_prior_and_each_other": True,
        "render_source_binding_sha256": binding,
        "general_dirichlet_inverse_criterion_proved": fresh_report["general_dirichlet_inverse_criterion_proved"],
        "full_G009_dirichlet_convolution_theory_proved": False, "general_G091_prime_power_fields_proved": False,
        "parent": {"alpha_version": "v30", "alpha_checked_use_count": 3222, "stable_count": 432,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256},
        "independent_checker": {"binary_sha256": checkpoints.LEAN_BINARY_SHA256},
        "checkpoints": [corpus["checkpoint_report"] for corpus in corpora],
    }
    inventory["checkpoint_digest"] = _digest(_json(inventory))
    files["checkpoints.json"] = _json(inventory)
    files["proof-audit.json"] = audit.canonical_report(fresh_report).encode("utf-8")
    files["index.html"], files["grand-campaign/index.html"] = dispatch(corpora, atlas=False), dispatch(corpora, atlas=True)
    files["manifest.json"] = _json({
        "schema": SCHEMA + "-manifest", "publication_scope": "local-only-checkpoint",
        "checkpoint_digest": inventory["checkpoint_digest"], "navigation_revision": HTML_REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {path: {"bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())},
    })
    if _render_binding() != binding:
        raise ExplorerError("proof or presentation sources changed while formatting the snapshot")
    return files


def build_files() -> dict[str, bytes]:
    """Fresh proof checks and private rendering; no stored report input."""
    with TemporaryDirectory(prefix="peano-dirichlet-inverse-render-") as directory:
        files, _, _ = _build_verified(output=Path(directory), check=False)
        return files


# The CLI also resolves every checkpoint, path, limit and hook in this new
# module. The old main function and its module registration remain untouched.
main = _reuse(previous_model.main)


if __name__ == "__main__":
    sys.modules.setdefault("build_constructive_dirichlet_inverse_explorer", sys.modules[__name__])
    raise SystemExit(main())
