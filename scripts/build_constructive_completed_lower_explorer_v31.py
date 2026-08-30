#!/usr/bin/env python3
"""Additive QR-model publication, gated by actual live Alpha-v31 verification.

No saved checkpoint report is accepted as proof authority.  The orchestrator
may pass the capability it has just obtained from the release verifier; the
standalone entry point always invokes that verifier itself.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import constructive_completed_lower_publication_v31 as publication
import constructive_checked_explorer_renderer as render
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_proof_explorer_template import render_canonical_family_landing

if TYPE_CHECKING:
    from verify_peano_library_channels_v31 import LiveReleaseContext


ROOT = publication.ROOT
OUTPUT = ROOT / "book/_static" / publication.OUTPUT_NAME
ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"
ASSET_DIGESTS = {
    **render.ASSET_DIGESTS,
    "proofs.css": "44ac9983416435ac33efada9eaa3ff914588845fe55932f5e8c54623b28c9285",
}


class _CurrentHTML(HTMLParser):
    """Add metadata and the real graph marker without touching math/scripts."""

    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"))

    def __init__(self, page: str, revision: str, *, portable_script: str = "", layer_choices: tuple[int, ...] | None = None):
        super().__init__(convert_charrefs=False)
        self.page, self.revision = page, revision
        self.portable_script = portable_script
        self.layer_choices, self.layer_select = layer_choices, False
        self.parts, self.stack = [], []
        self.exact = False
        self.graph_links = self.heads = self.bodies = 0
        self.canonical = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if len(attrs) != len(attributes):
            raise publication.PublicationError("duplicate HTML attribute")
        raw = self.get_starttag_text()
        protected = any(name in {"pre", "code", "script", "style"} for name, _ in self.stack)
        if not protected and tag == "li" and "pd-proof-line" in attrs.get("class", "").split():
            identifier = attrs.get("id", "")
            if re.fullmatch(r"L[1-9][0-9]*", identifier):
                raw = raw.replace('id="' + identifier + '"', 'id="proof-line-' + f'{int(identifier[1:]):04d}' + '"', 1)
        if not protected and tag == "a" and "pd-line-number" in attrs.get("class", "").split():
            reference = attrs.get("href", "")
            if re.fullmatch(r"#L[1-9][0-9]*", reference):
                raw = raw.replace('href="' + reference + '"', 'href="#proof-line-' + f'{int(reference[2:]):04d}' + '"', 1)
        if tag == "body":
            self.exact = "pa-proof-site" in attrs.get("class", "").split()
        if tag == "link" and attrs.get("rel") == "canonical":
            if attrs.get("href") != ORIGIN + "/proofs/" + self.page.removesuffix("index.html"):
                raise publication.PublicationError("a canonical route disagrees with its reader path")
            self.canonical = True
        if (tag == "a" and not protected
                and any(name == "header" and "pa-proof-header" in old.get("class", "").split()
                        for name, old in self.stack)
                and urlsplit(attrs.get("href", "")).path.endswith("defined/graph.html")):
            self.graph_links += 1
            if "data-graph-navigation" not in attrs:
                raw = raw[:-1] + " data-graph-navigation>"
        if not self.layer_select:
            self.parts.append(raw)
        if tag == "select" and "data-layer" in attrs and self.layer_choices is not None:
            if self.layer_select:
                raise publication.PublicationError("nested dashboard layer control")
            self.layer_select = True
        if tag not in self.VOID:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attributes):
        if tag not in self.VOID:
            raise publication.PublicationError("unexpected non-void self-closing HTML")
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise publication.PublicationError("unbalanced current reader HTML: " + tag)
        self.stack.pop()
        if self.layer_select:
            if tag == "select":
                self.parts.append('<option value="all">All layers</option>' + ''.join(f'<option value="{value}">{value}</option>' for value in self.layer_choices))
                self.layer_select = False
            else:
                return
        if tag == "head":
            canonical = ORIGIN + "/proofs/" + self.page.removesuffix("index.html")
            if not self.canonical:
                self.parts.append('<link rel="canonical" href="' + escape(canonical, quote=True) + '">')
            self.parts.append('<meta name="proof-publication-scope" content="alpha-v31-checked-use">')
            self.heads += 1
        if tag == "body":
            self.parts.append(self.portable_script)
            self.bodies += 1
        self.parts.append("</" + tag + ">")

    def handle_data(self, data):
        if not self.layer_select:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append("&" + name + ";")

    def handle_charref(self, name):
        self.parts.append("&#" + name + ";")

    def handle_comment(self, data):
        self.parts.append("<!--" + data + "-->")

    def handle_decl(self, decl):
        self.parts.append("<!" + decl + ">")

    def finish(self, payload: bytes) -> bytes:
        self.feed(payload.decode("utf-8"))
        self.close()
        if self.stack or self.heads != 1 or self.bodies != 1 or (self.exact and self.graph_links != 1):
            raise publication.PublicationError("the current reader lost its exact HTML/graph contract")
        return "".join(self.parts).encode("utf-8")


def _portable_script(family_packages: Mapping[str, str]) -> str:
    """Make the same relative links work in the raw tree and deployed site."""
    script = r'''<script>
(function () {
  "use strict";
  var markers = __MARKERS__, packages = __PACKAGES__;
  var marker = markers.find(function (value) { return location.pathname.indexOf(value) >= 0; });
  if (!marker) return;
  var staticRoot = location.pathname.slice(0, location.pathname.indexOf(marker));
  document.querySelectorAll("a[href]").forEach(function (link) {
    var original = link.getAttribute("href");
    if (!original || /^(?:https?:|mailto:|#)/.test(original)) return;
    var target = new URL(original, location.href);
    if (target.pathname.indexOf("/grand-campaign/") >= 0) {
      target.pathname = staticRoot + "/__ATLAS__/index.html";
    } else {
      var slug = Object.keys(packages).find(function (value) { return target.pathname.indexOf("/" + value + "/") >= 0; });
      if (!slug) return;
      target.pathname = staticRoot + "/" + packages[slug] + target.pathname.slice(target.pathname.indexOf("/" + slug + "/"));
    }
    link.setAttribute("href", target.href);
  });
})();
</script>'''.replace("__MARKERS__", json.dumps([
        "/" + publication.OUTPUT_NAME + "/", "/" + publication.HISTORICAL_OUTPUT_NAME + "/",
    ])).replace("__PACKAGES__", json.dumps(dict(family_packages), sort_keys=True)).replace("__ATLAS__", publication.ATLAS_NAME)
    return script + "\n"


def _source_snapshot(slug: str):
    return next(snapshot for snapshot in publication.SNAPSHOTS if slug in dict(snapshot.families))


def _asset_files(manifests: Mapping[str, dict]) -> dict[str, bytes]:
    first = publication.SNAPSHOTS[0]
    files = {}
    for name, sha in ASSET_DIGESTS.items():
        payload = publication.snapshot_file(first, manifests[first.directory], "assets/" + name)
        if publication.digest(payload) != sha:
            raise publication.PublicationError("a canonical QR asset changed: " + name)
        files["assets/" + name] = payload
    return files


def _dashboard_enhancement(manifests: Mapping[str, dict]) -> str:
    """Reuse the already-tested three-filter script from a pinned old reader."""
    class Extract(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.recording = False
            self.scripts = []
        def handle_starttag(self, tag, attrs):
            if tag == "script" and "data-local-dashboard-enhancement" in dict(attrs):
                self.recording = True
                self.scripts.append([self.get_starttag_text()])
        def handle_data(self, data):
            if self.recording:
                self.scripts[-1].append(data)
        def handle_endtag(self, tag):
            if tag == "script" and self.recording:
                self.scripts[-1].append("</script>")
                self.recording = False
    first = publication.SNAPSHOTS[0]
    source = publication.snapshot_file(first, manifests[first.directory], "euler-units/explorer/defined/index.html")
    parser = Extract()
    parser.feed(source.decode("utf-8")); parser.close()
    if len(parser.scripts) != 1 or parser.recording:
        raise publication.PublicationError("the pinned three-filter dashboard enhancement changed")
    return "".join(parser.scripts[0])


def _definition_and_statement_identity(original: Mapping[str, Any], revised: Mapping[str, Any]) -> None:
    for key in ("definitions", "edges", "tags", "layers", "proof_adjacency", "proof_paths",
                "root_names", "definition_topological_order", "node_count", "edge_count", "formal_line_count"):
        if original[key] != revised[key]:
            raise publication.PublicationError("publication changed a mathematical reader field: " + key)
    for old, new in zip(original["nodes"], revised["nodes"], strict=True):
        for key in ("name", "id", "statement", "statement_sha256", "script", "dependencies", "summary", "defined", "sources"):
            if old[key] != new[key]:
                raise publication.PublicationError("publication changed exact theorem or notation syntax")


def _checkpoint_page(family, corpus: dict, report: Mapping[str, Any], revision: str) -> bytes:
    snapshot = _source_snapshot(family.slug)
    historical = "../historical/" + snapshot.directory + "/"
    bundle = report["bundle"]
    source_rows = []
    for node in corpus["nodes"]:
        source_rows.append(f'<li id="theorem-{escape(node["name"], quote=True)}"><a href="{render._versioned("explorer/defined/tag/" + node["id"] + ".html", revision)}"><code>{escape(node["id"])} {escape(node["name"])}</code></a> · actual bundle node {node["proof_bundle_node_id"]}</li>')
    for row in corpus["external_dependencies"]:
        source_rows.append(f'<li id="theorem-{escape(row["name"], quote=True)}"><code>{escape(row["name"])}</code> · checked inherited prerequisite<details><summary>Exact statement in the checked dependency cone</summary><pre><code>{escape(row["statement"])}</code></pre></details></li>')
    source_names = sorted({node["source_filename"] for node in corpus["nodes"]})
    source_links = " · ".join(f'<a href="{render._versioned(historical + "sources/" + name, revision)}">{escape(name)}</a>' for name in source_names)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(family.title)} — Alpha admission evidence</title><link rel="stylesheet" href="{render._versioned('../assets/proofs.css', revision)}"></head><body class="family-page"><header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned('./', revision)}">Family reader</a><a href="{render._versioned('../grand-campaign/', revision)}">Grand campaign</a></nav><h1>{escape(family.title)} — exact evidence</h1><p class="lede">Current Alpha v31 checked use; first admitted v31; not Stable. Original HA and the independently compiled Lean checker have freshly verified the complete bundle before this page was generated.</p></div></header><main class="shell family-main"><section class="release-note"><p>{bundle['nodes_including_packaging_root']} checked bundle nodes · {bundle['dependency_edges_including_packaging']} proof edges · {bundle['body_proof_nodes']} body proof nodes.</p><p><a href="{render._versioned('../artifacts/' + Path(bundle['path']).name, revision)}">Literal self-contained proof bundle</a> · SHA-256 <code>{escape(bundle['sha256'])}</code></p><p>{source_links}</p><p><a href="{render._versioned(historical + 'checkpoints.json', revision)}">Unchanged historical local checkpoint record</a> · <a href="{render._versioned(historical + 'manifest.json', revision)}">Historical snapshot manifest</a>. Those records retain their original non-admitting flags; current authority comes from the separate freshly verified v31 release.</p></section><section><h2>Exact theorem nodes and inherited prerequisites</h2><ul>{''.join(source_rows)}</ul></section></main></body></html>'''.encode("utf-8")


def _render_family(family, corpus: dict, report: Mapping[str, Any], revision: str) -> dict[str, bytes]:
    base = family.slug + "/"
    graph = render._graph_payload(family, corpus, revision=revision)
    files = {
        base + "index.html": render_canonical_family_landing(
            family, corpus, revision=revision, current_alpha_version="v31", first_admitted_version="v31",
            bundle_node_count=report["bundle"]["nodes_including_packaging_root"]),
        base + "checkpoint.html": _checkpoint_page(family, corpus, report, revision),
        base + "api/corpus.json": publication.json_bytes(corpus),
        base + "api/graph.json": publication.json_bytes(graph),
        base + "api/checkpoint.json": publication.json_bytes(report),
        base + "explorer/defined/api/graph.json": publication.json_bytes(graph),
        base + "explorer/defined/index.html": render._defined_index(family, corpus, revision=revision),
        base + "explorer/defined/graph.html": render._defined_graph(family, corpus, graph, revision=revision),
        base + "explorer/index.html": render_exact_index(
            family, corpus, corpus["tags"], corpus["layers"],
            stylesheet_href="../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
            script_href="../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=revision),
    }
    for node in corpus["nodes"]:
        files[base + f"explorer/tag/{node['id']}.html"] = render_exact_theorem(
            family, corpus, node, corpus["tags"], corpus["layers"],
            stylesheet_href="../../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
            script_href="../../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=revision)
        files[base + f"explorer/defined/tag/{node['id']}.html"] = render._defined_theorem(family, corpus, node, revision=revision)
    for definition in corpus["definitions"]:
        files[base + f"explorer/defined/definition/{definition['id']}.html"] = render._defined_definition(family, corpus, definition, revision=revision)
    return files


def build_files_from_live(context: LiveReleaseContext) -> dict[str, bytes]:
    publication.require_live(context)
    manifests = publication.authenticate_snapshots()
    originals = publication.frozen_corpora(manifests)
    definitions = publication.validate_definition_identities(originals)
    metadata = publication.family_metadata(originals)
    names = {node["name"] for corpus in originals.values() for node in corpus["nodes"]}
    if names != set(context.promoted_names):
        raise publication.PublicationError("the admitted v31 slice differs from the nineteen frozen readers")
    by_name = {row["name"]: row for row in context.catalog["theorems"]}
    if len(by_name) != publication.CURRENT_COUNT:
        raise publication.PublicationError("the live catalog contains duplicate theorem names")
    import upgrade_constructive_historical_publication_v31 as historical
    historical_metadata = historical.family_metadata()
    routes = {**historical.theorem_routes(historical_metadata),
              **{name: family["slug"] + "/explorer/defined/tag/" + tag + ".html"
                 for family in metadata for name, tag in family["tags"].items()}}
    files, corpora = _asset_files(manifests), []
    for family in publication.family_models():
        original, report = originals[family.slug], context.families[family.slug]
        family_routes = dict(routes)
        for external in original["external_dependencies"]:
            family_routes.setdefault(external["name"], family.slug + "/checkpoint.html#theorem-" + external["name"])
        corpus = publication._promote_corpus(original, report, context, by_name, family_routes)
        _definition_and_statement_identity(original, corpus)
        files.update(_render_family(family, corpus, report, context.revision))
        bundle = report["bundle"]
        if not publication.safe_relative(bundle["path"]):
            raise publication.PublicationError("the fresh release supplied an unsafe proof-bundle path")
        files["artifacts/" + Path(bundle["path"]).name] = publication.read_pinned(ROOT / bundle["path"], bundle["bytes"], bundle["sha256"])
        corpora.append(corpus)
    for snapshot in publication.SNAPSHOTS:
        manifest = manifests[snapshot.directory]
        prefix = "historical/" + snapshot.directory + "/"
        files[prefix + "manifest.json"] = publication.read_pinned(ROOT / "book/_static" / snapshot.directory / "manifest.json", snapshot.manifest_bytes, snapshot.manifest_sha256)
        for relative in manifest["files"]:
            if relative.startswith("sources/") or relative.startswith("receipts/") or relative in {"checkpoints.json", "proof-audit.json"}:
                files[prefix + relative] = publication.snapshot_file(snapshot, manifest, relative)
    cards = "".join(f'<article class="family-card"><h2>{escape(family["title"])}</h2><p>{family["theorem_count"]} actual Alpha checked-use theorems; first admitted v31.</p><a class="primary-action" href="{render._versioned(family["slug"] + "/", context.revision)}">Explore the proof map</a></article>' for family in metadata)
    files["index.html"] = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Completed constructive lower layers — Alpha v31</title><link rel="stylesheet" href="{render._versioned('assets/proofs.css', context.revision)}"></head><body><header class="hero"><div class="shell"><p class="eyebrow">Alpha v31 · original HA · independent compiled Lean</p><h1>Nineteen completed lower-layer proof families</h1><p class="lede">574 newly admitted theorems. Current Alpha has 3,796 checked-use entries; Stable remains the separate unchanged 432-theorem edition.</p><nav><a href="{render._versioned('../grand-campaign/', context.revision)}">Grand campaign</a></nav></div></header><main class="shell"><section class="family-grid">{cards}</section><section class="release-note">Full finite signed Möbius inversion (G007) and Euler's theorem for units (G014) are admitted with their actual proof witnesses. General signed finite inverse existence is characterized by N=0 or a unit value at one. Full G009 still requires multiplicative-function closure; full G091 requires prime-power extension fields. Historical research records are retained literally and do not themselves grant admission.</section></main></body></html>'''.encode("utf-8")
    packages = {**{slug: publication.HISTORICAL_OUTPUT_NAME for slug in historical.FAMILY_ORDER},
                **{slug: publication.OUTPUT_NAME for slug in publication.FAMILY_ORDER}}
    by_slug = {corpus["family_slug"]: corpus for corpus in corpora}
    dashboard = _dashboard_enhancement(manifests)
    for path, payload in tuple(files.items()):
        if path.endswith(".html"):
            layers, scripts = None, _portable_script(packages)
            if path.endswith("/explorer/defined/index.html"):
                corpus = by_slug[path.split("/", 1)[0]]
                layers = tuple(sorted(set(corpus["layers"].values()) | {row["topological_layer"] for row in corpus["definitions"]}))
                scripts = dashboard + scripts
            files[path] = _CurrentHTML(path, context.revision, portable_script=scripts, layer_choices=layers).finish(payload)
    inventory = {
        "schema": publication.SCHEMA, "publication_scope": "alpha_checked_use_publication",
        "alpha_edition_version": "v31", "alpha_first_enrolled_version": "v31",
        "alpha_catalog_sha256": context.catalog_sha256,
        "alpha_edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "alpha_checked_use_count": 3796, "newly_admitted_theorem_count": 574, "stable_count": 432,
        "full_G007_finite_signed_mobius_inversion_proved": True,
        "full_G014_euler_units_proved": True,
        "general_finite_signed_inverse_criterion_proved": True,
        "full_G009_multiplicative_closure_proved": False,
        "full_G091_prime_power_fields_proved": False,
        "families": list(metadata), "definitions": definitions,
        "proof_verification_provenance": "same_live_v31_release_context",
        "source_binding_sha256": context.source_binding_sha256,
        "historical_reader_manifests": [{"directory": item.directory, "bytes": item.manifest_bytes, "sha256": item.manifest_sha256} for item in publication.SNAPSHOTS],
    }
    files["publication.json"] = publication.json_bytes(inventory)
    files["manifest.json"] = publication.json_bytes({
        "schema": publication.SCHEMA + "-manifest", "alpha_edition_version": "v31",
        "alpha_first_enrolled_version": "v31", "catalog_sha256": context.catalog_sha256,
        "first_enrollment_catalog_sha256": context.catalog_sha256,
        "edition_identity_sha256": context.catalog["edition_identity_sha256"], "html_revision": context.revision,
        "theorem_count": 574, "checked_use_count": 574, "stable_count": 0,
        "families": list(metadata), "file_count_excluding_manifest": len(files),
        "files": {path: {"bytes": len(payload), "sha256": publication.digest(payload)} for path, payload in sorted(files.items())},
    })
    publication.require_live(context)
    publication.authenticate_snapshots()
    return files


def build_files() -> dict[str, bytes]:
    from verify_peano_library_channels_v31 import verify_for_publication
    from constructive_alpha_v31_publication_process import _fork_phase
    from tempfile import TemporaryDirectory

    context = verify_for_publication()
    with TemporaryDirectory(prefix="peano-v31-completed-reader-") as directory:
        result = _fork_phase(context, "completed", output=Path(directory) / "files", check=False)
        return {name: publication.read_pinned(result.directory / name, pin["bytes"], pin["sha256"])
                for name, pin in result.inventory["files"].items()}


def publish_from_live_context(context: LiveReleaseContext, check: bool):
    """Three bounded pure phases, including mandatory same-live UI tests."""
    from constructive_alpha_v31_publication_process import publish_from_live_context as publish

    return publish(context, check)


def main(argv: list[str] | None = None) -> int:
    import resource
    import signal
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    # The verifier owns its sequential fresh proof-worker schedule. Rendering
    # must subsequently run in an independently bounded pure-render window.
    from verify_peano_library_channels_v31 import verify_for_publication, proof_audit

    resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)
    jobs = 1 + len(proof_audit.registry()) + sum(len(item.principal_roots) for item in proof_audit.registry())
    signal.alarm(jobs * proof_audit.PARENT_TIMEOUT_SECONDS + 4 * proof_audit.WALL_SECONDS)
    context = verify_for_publication()
    publish_from_live_context(context, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
