"""Non-admitting delivery of the frozen 126-theorem lower-tier checkpoint.

Only presentation metadata, prose and navigation change. Exact proofs,
definitions, scripts, sources, bundles and historical receipts stay literal.
The caller must freshly run the original HA and compiled Lean verifiers.
"""

from __future__ import annotations

from copy import deepcopy
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import constructive_bottom_layer_publication_adapter as previous


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "peano-lab-public-lower-tier-checkpoints-v1"
SCOPE = previous.SCOPE
REVISION = previous.REVISION
ORIGIN = previous.ORIGIN
PUBLIC_BASE = "/proofs/checkpoints/lower-tier/"
LOCAL_BASE = "/book/_static/constructive-lower-tier-explorer/"
LOCAL_MANIFEST_SHA256 = "ac6c7b3f53a27ba3812969031d7a3eea25bc0c2abeb7944c45f240ca5bb59c32"
LOCAL_CHECKPOINT_DIGEST = "fc8f85092b7a4ae03f3614e940c4ca4ab5cdf4da63710ea692cb10ca8be5bca9"
FAMILY_COUNTS = {"divisor-sums": 37, "signed-weighted-sums": 40, "prime-field-polynomials": 49}
ADMISSION_FLAGS = previous.ADMISSION_FLAGS
OLD_STATUS, STATUS = previous.OLD_STATUS, previous.STATUS
OLD_GRAPH_LABEL, GRAPH_LABEL = previous.OLD_GRAPH_LABEL, previous.GRAPH_LABEL
SERVICE_NOTE = previous.SERVICE_NOTE
PublicCheckpointError = previous.PublicCheckpointError
digest, strict_json, json_bytes, read_pinned = previous.digest, previous.strict_json, previous.json_bytes, previous.read_pinned

PREVIOUS_INDEXES = (
    ("euler-units", 707046, "0515c9f2be505382486c87ffd118a39772a68f2fd54a8c413b35ec19c561027d"),
    ("prime-fields", 1665138, "333ce22866c8e27361917ad834f70158be1cd1682d2b71851d8ef31442a96b06"),
    ("mobius-values", 493760, "40ccbee992aa0083b6ed045f394ec8e8962f744edf59277961ba645ee0e0cc2f"),
    ("signed-sums", 1029244, "59f499d6cebdbc7f5b7ec05829df383b7d32ca2e409ab3eea459f6278ff2517d"),
)
ADDITIONAL_ALPHA_INDEXES = (
    previous.RouteIndex("constructive-next-layer-explorer/polynomial-horner/api/corpus.json", 88306, "d91f62bfec89263036f4895cf6e742a63c00c19028af3333f6d5123575ff6685", "polynomial-horner/", "constructive-next-layer-explorer/polynomial-horner/"),
    previous.RouteIndex("constructive-advanced-layer-explorer/matrix-coded-products/api/corpus.json", 565213, "d82f51dee7cb1d0d3daa0796d2cc310ca75cd2457b244162297fdba677ee329e", "matrix-coded-products/", "constructive-advanced-layer-explorer/matrix-coded-products/"),
)
ALPHA_ROLE = "inherited_alpha_v30"
PREVIOUS_ROLE = "inherited_published_non_admitted_checkpoint"
CROSS_ROLE = "new_cross_track_support"


def validate_local_files(files: Mapping[str, bytes]) -> dict:
    if len(files) != 371 or digest(files.get("manifest.json", b"")) != LOCAL_MANIFEST_SHA256:
        raise PublicCheckpointError("the exact frozen 126-theorem local snapshot changed")
    manifest = strict_json(files["manifest.json"])
    if set(files) != set(manifest["files"]) | {"manifest.json"}:
        raise PublicCheckpointError("the local snapshot inventory changed")
    for name, expected in manifest["files"].items():
        path, payload = PurePosixPath(name), files[name]
        if (path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name
                or type(payload) is not bytes or len(payload) != expected["bytes"]
                or digest(payload) != expected["sha256"]):
            raise PublicCheckpointError("a literal local snapshot file changed: " + name)
    inventory = strict_json(files["checkpoints.json"])
    if (inventory["checkpoint_digest"] != LOCAL_CHECKPOINT_DIGEST
            or inventory["published"] is not False or inventory["new_theorems"] != 126
            or inventory["previous_research_theorems"] != 170
            or inventory["alpha_admission_performed"] is not False
            or inventory["stable_admission_performed"] is not False):
        raise PublicCheckpointError("invalid local non-admission inventory")
    return inventory


def inherited_routes(corpora: Mapping[str, dict], *, root: Path = ROOT) -> dict[str, dict]:
    """Resolve routes by exact expanded statement and genuine inventory role."""
    wanted, result = {}, {}
    for corpus in corpora.values():
        for row in corpus["external_dependencies"]:
            old = wanted.setdefault(row["name"], row)
            if (old["statement"], old["inventory_role"]) != (row["statement"], row["inventory_role"]):
                raise PublicCheckpointError("inconsistent inherited statement or authority")

    def attach(row, role, tag, public_path, source_page, index, index_sha):
        name = row["name"]
        if name not in wanted or name in result:
            return
        expected = wanted[name]
        if (expected["inventory_role"] != role or expected["statement"] != row["statement"]
                or digest(row["statement"].encode()) != expected["statement_sha256"]):
            raise PublicCheckpointError("route names a different exact theorem or authority: " + name)
        if not isinstance(tag, str) or re.fullmatch(r"[A-Z0-9]{4,10}", tag) is None:
            raise PublicCheckpointError("route has no stable theorem tag: " + name)
        source = root / source_page
        if source.is_symlink() or not source.is_file():
            raise PublicCheckpointError("exact prerequisite page is absent: " + source_page)
        result[name] = {"name": name, "statement_sha256": expected["statement_sha256"],
                        "inventory_role": role, "standalone_page": True, "public_path": public_path,
                        "source_page": source_page, "route_index": index, "route_index_sha256": index_sha}

    for slug, corpus in corpora.items():
        index = "constructive-lower-tier-explorer/" + slug + "/api/corpus.json"
        payload = json_bytes(corpus)
        index_sha = digest(payload)
        read_pinned(root / "book/_static" / index, len(payload), index_sha)
        for row in corpus["nodes"]:
            suffix = slug + "/explorer/defined/tag/" + row["id"] + ".html"
            attach(row, CROSS_ROLE, row["id"], PUBLIC_BASE + suffix,
                   "book/_static/constructive-lower-tier-explorer/" + suffix, index, index_sha)
    for slug, size, expected_sha in PREVIOUS_INDEXES:
        index = "constructive-bottom-layer-publication/" + slug + "/api/corpus.json"
        corpus = strict_json(read_pinned(root / "book/_static" / index, size, expected_sha))
        for row in corpus["nodes"]:
            if any(row.get(flag) is not False for flag in ADMISSION_FLAGS):
                raise PublicCheckpointError("prior research route acquired library authority")
            suffix = slug + "/explorer/defined/tag/" + row["id"] + ".html"
            attach(row, PREVIOUS_ROLE, row["id"], "/proofs/checkpoints/" + suffix,
                   "book/_static/constructive-bottom-layer-publication/" + suffix, index, expected_sha)
    for index in (*previous.ROUTE_INDEXES, *ADDITIONAL_ALPHA_INDEXES):
        corpus = strict_json(read_pinned(root / "book/_static" / index.path, index.size, index.sha256))
        for position, row in enumerate(corpus.get("nodes", corpus.get("theorems", ()))):
            if row["name"] not in wanted or row["name"] in result:
                continue
            tag = row.get("id") or row.get("tag") or corpus.get("tags", {}).get(row["name"])
            if tag is None and index.frontier_prefix:
                tag = index.frontier_prefix + previous._base36(position).zfill(4)
            if not isinstance(tag, str):
                raise PublicCheckpointError("historical theorem has no stable tag")
            suffix = "defined/tag/" + tag + ".html"
            if not index.public_family.endswith("/explorer/"):
                suffix = "explorer/" + suffix
            source_suffix = suffix.removeprefix("explorer/") if index.source_family in ("pa-proof-explorer/", "bertrand-proof-explorer/") else suffix
            attach(row, ALPHA_ROLE, tag, "/proofs/" + index.public_family + suffix,
                   "book/_static/" + index.source_family + source_suffix, index.path, index.sha256)
    for name in sorted(wanted.keys() - result.keys()):
        row = wanted[name]
        if row["inventory_role"] != ALPHA_ROLE:
            raise PublicCheckpointError("non-admitted prerequisite has no owning proof page: " + name)
        result[name] = {"name": name, "statement_sha256": row["statement_sha256"],
                        "inventory_role": ALPHA_ROLE, "standalone_page": False,
                        "note": "Inherited Alpha proof; no standalone historical explorer page. Exact statement and freshly checked complete-bundle node are linked."}
    return dict(sorted(result.items()))


def public_target(name: str, slug: str, routes: Mapping[str, dict]) -> str:
    row = routes[name]
    return (row["public_path"] if row["standalone_page"] else
            PUBLIC_BASE + slug + "/checkpoint.html#theorem-" + name)


def public_corpus(original: dict, routes: Mapping[str, dict]) -> dict:
    corpus = deepcopy(original)
    slug = corpus["family_slug"]
    if (slug not in FAMILY_COUNTS or corpus["node_count"] != FAMILY_COUNTS[slug]
            or len(corpus["nodes"]) != FAMILY_COUNTS[slug]):
        raise PublicCheckpointError("unexpected public checkpoint family")
    for node in (corpus, *corpus["nodes"]):
        if (any(node.get(key) is not False for key in ADMISSION_FLAGS)
                or any(node.get(key) is not True for key in ("local_checkpoint_verified", "original_ha_bundle_verified", "independent_lean_bundle_verified"))):
            raise PublicCheckpointError("public delivery cannot confer library authority")
    corpus.update(schema=SCHEMA, publication_scope=SCOPE, candidate_status=STATUS,
                  on_demand_alpha_lean_service_exposes_frontier=False)
    for node in corpus["nodes"]:
        if node["status"] != OLD_STATUS:
            raise PublicCheckpointError("unexpected original theorem status")
        node["status"] = STATUS
    corpus["external_theorem_routes"] = {row["name"]: public_target(row["name"], slug, routes)
                                         for row in corpus["external_dependencies"]}
    for row in corpus["external_dependencies"]:
        row["reference_route"] = corpus["external_theorem_routes"][row["name"]]
    corpus["external_route_boundary"] = "Exact owning proof pages, separately labelled Alpha, prior research and current cross-track support; explicit complete-bundle fallback when no historical page exists."
    return corpus


def public_graph(original: dict) -> dict:
    if (original.get("publication_scope") != "local-only-checkpoint"
            or any(original.get(key) is not False for key in ADMISSION_FLAGS)):
        raise PublicCheckpointError("graph authority or original scope changed")
    return deepcopy(original) | {"schema": SCHEMA + "-graph", "publication_scope": SCOPE}


PROSE = previous.PROSE + (
    ("Local lower-tier proof checkpoints", "Public lower-tier proof checkpoints"),
    ("Local lower-tier checkpoints", "Lower-tier research checkpoints"),
    ("Constructive arithmetic · local development", "Constructive arithmetic · public research checkpoints"),
    ("This additive local map does not alter the published atlas or grant Alpha membership.",
     "This additive research map preserves the Alpha atlas and grants no Alpha or Stable membership."),
)


def _prose(value: str) -> str:
    for old, new in PROSE:
        value = value.replace(old, new)
    return value


def _relative(page: str, target: str) -> str:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/proofs/"):
        raise PublicCheckpointError("navigation escaped the proof library")
    path = posixpath.relpath(parsed.path, posixpath.dirname(PUBLIC_BASE + page))
    if parsed.path.endswith("/"):
        path += "/"
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "v"]
    query.append(("v", REVISION))
    return urlunsplit(("", "", path, urlencode(query), parsed.fragment))


class PublicHTML(HTMLParser):
    """Token-aware delivery adaptation, with protected proof/script text."""

    VOID = previous.PublicHTML.VOID

    def __init__(self, page: str, routes: Mapping[str, dict], graph=None, original_graph=None):
        super().__init__(convert_charrefs=False)
        self.page, self.routes, self.graph, self.original_graph = page, routes, graph, original_graph
        self.output, self.stack, self.script = [], [], None
        self.notice_count = self.nav_count = self.head_count = self.graph_count = 0

    @property
    def protected(self):
        return any(tag in {"pre", "code", "script", "style"} for tag, _, _ in self.stack)

    def _external(self, name):
        return _relative(self.page, public_target(name, self.page.split("/", 1)[0], self.routes))

    def _href(self, value):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            return value
        parts = parsed.path.split("/")
        for marker, target in (("constructive-gaussian-campaign", "/proofs/grand-campaign/"),
                               ("constructive-bottom-layer-explorer", "/proofs/checkpoints/")):
            if marker in parts:
                suffix = "/".join(parts[parts.index(marker) + 1:])
                return _relative(self.page, urlunsplit(("", "", target + suffix, parsed.query, parsed.fragment)))
        if parsed.path.endswith("checkpoint.html") and parsed.fragment.startswith("theorem-"):
            name = parsed.fragment.removeprefix("theorem-")
            if name in self.routes:
                return self._external(name)
        return value

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if len(attrs) != len(pairs):
            raise PublicCheckpointError("duplicate HTML attribute")
        raw, out_tag = self.get_starttag_text(), tag
        if (tag == "meta" and (attrs.get("name") in {"robots", "proof-publication-scope"}
                               or attrs.get("property") in {"og:url", "og:image", "og:type"})):
            return
        if tag == "link" and attrs.get("rel") == "canonical":
            return
        if tag == "meta" and (attrs.get("name") == "description" or attrs.get("property") in {"og:title", "og:description"}):
            raw = previous._attribute(raw, "content", _prose(attrs["content"]))
        if not self.protected:
            if attrs.get("data-search"):
                raw = previous._attribute(raw, "data-search", _prose(attrs["data-search"]))
            if "href" in attrs:
                raw = previous._attribute(raw, "href", self._href(attrs["href"]))
            if tag == "span" and "data-external-name" in attrs:
                name = attrs["data-external-name"]
                if name not in self.routes:
                    raise PublicCheckpointError("unknown inherited theorem chip")
                out_tag = "a"
                raw = raw.replace("<span", "<a", 1)[:-1] + ' href="' + escape(self._external(name), quote=True) + '">'
        self.output.append(raw)
        if tag not in self.VOID:
            self.stack.append((tag, out_tag, attrs))
        if tag == "script":
            if self.script is not None:
                raise PublicCheckpointError("nested script")
            self.script = [attrs, []]

    def handle_startendtag(self, tag, attrs):
        if tag not in self.VOID:
            raise PublicCheckpointError("unexpected self-closing HTML element")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "script":
            if self.script is None:
                raise PublicCheckpointError("unmatched script boundary")
            attrs, chunks = self.script
            source = "".join(chunks)
            if attrs.get("id") == "pa-defined-graph-data":
                prefix = "window.PA_DEFINED_GRAPH="
                if (not source.startswith(prefix) or not source.endswith(";") or self.graph is None
                        or strict_json(source[len(prefix):-1]) != self.original_graph):
                    raise PublicCheckpointError("embedded graph differs from exact graph API")
                source = prefix + json.dumps(self.graph, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + ";"
                if "</script" in source.lower():
                    raise PublicCheckpointError("unsafe graph script boundary")
                self.graph_count += 1
            elif OLD_GRAPH_LABEL in source:
                if source.count(OLD_GRAPH_LABEL) != 1 or self.graph is None:
                    raise PublicCheckpointError("unexpected graph authority overlay")
                source = source.replace(OLD_GRAPH_LABEL, GRAPH_LABEL)
            self.output.append(source)
            self.script = None
        if not self.stack or self.stack[-1][0] != tag:
            raise PublicCheckpointError("unbalanced HTML boundary: " + tag)
        _, out_tag, _ = self.stack.pop()
        if tag == "head":
            canonical = ORIGIN + PUBLIC_BASE + self.page.removesuffix("index.html")
            self.output.append('<link rel="canonical" href="' + canonical + '">'
                               '<meta property="og:url" content="' + canonical + '">'
                               '<meta property="og:type" content="website">'
                               '<meta property="og:image" content="' + ORIGIN + '/proofs/assets/proofs-og.png">'
                               '<meta name="proof-publication-scope" content="' + SCOPE + '">')
            self.head_count += 1
        if tag == "nav" and self.nav_count == 0:
            self.output.append('<a data-public-proof-library href="' + escape(_relative(self.page, "/proofs/"), quote=True) + '">Proof library</a>')
            self.nav_count += 1
        self.output.append("</" + out_tag + ">")
        if tag == "h1":
            self.output.append('<p class="pd-callout pa-callout" data-public-checkpoint-notice>' + escape(SERVICE_NOTE) + '</p>')
            self.notice_count += 1

    def handle_data(self, value):
        if self.script is not None:
            self.script[1].append(value)
            return
        if self.protected:
            self.output.append(value)
            return
        if self.stack and self.stack[-1][0] == "head" and value.isspace():
            if self.output and self.output[-1].isspace():
                value = self.output.pop() + value
            value = re.sub(r"(?m)^[ \t]+(?=\r?\n)", "", value)
        if value.startswith("inherited alpha v30 · "):
            article = next((attrs for tag, _, attrs in reversed(self.stack) if tag == "article"), {})
            name = str(article.get("id", "")).removeprefix("theorem-")
            if name not in self.routes:
                raise PublicCheckpointError("unknown inherited receipt theorem")
            if not self.routes[name]["standalone_page"]:
                value = value.replace("inherited alpha v30", "Inherited Alpha proof; no standalone historical explorer page", 1)
        self.output.append(_prose(value))

    def handle_entityref(self, name):
        self.output.append("&" + name + ";")

    def handle_charref(self, name):
        self.output.append("&#" + name + ";")

    def handle_decl(self, declaration):
        self.output.append("<!" + declaration + ">")

    def handle_comment(self, value):
        self.output.append("<!--" + value + "-->")

    def finish(self, payload: bytes) -> bytes:
        self.feed(payload.decode("utf-8"))
        self.close()
        if (self.stack or self.script is not None or self.head_count != 1 or self.nav_count != 1
                or self.notice_count != 1 or self.graph_count != (1 if self.graph is not None else 0)):
            raise PublicCheckpointError("incomplete public HTML adaptation")
        return "".join(self.output).encode()


def adapt_files(local_files: Mapping[str, bytes], *, root: Path = ROOT) -> dict[str, bytes]:
    inventory = validate_local_files(local_files)
    corpora = {slug: strict_json(local_files[slug + "/api/corpus.json"]) for slug in FAMILY_COUNTS}
    routes = inherited_routes(corpora, root=root)
    old_graphs = {slug: strict_json(local_files[slug + "/api/graph.json"]) for slug in FAMILY_COUNTS}
    graphs = {slug: public_graph(graph) for slug, graph in old_graphs.items()}
    files = dict(local_files)
    files.pop("manifest.json")
    for name, payload in local_files.items():
        if name.endswith(".html"):
            slug = name.split("/", 1)[0]
            is_graph = name == slug + "/explorer/defined/graph.html"
            files[name] = PublicHTML(name, routes, graphs[slug] if is_graph else None,
                                     old_graphs[slug] if is_graph else None).finish(payload)
    for slug in FAMILY_COUNTS:
        files[slug + "/api/corpus.json"] = json_bytes(public_corpus(corpora[slug], routes))
        files[slug + "/api/graph.json"] = json_bytes(graphs[slug])
        files[slug + "/explorer/defined/api/graph.json"] = json_bytes(graphs[slug])
    files["receipts/local-checkpoints.json"] = local_files["checkpoints.json"]
    files["historical-prerequisites.json"] = json_bytes({
        "schema": SCHEMA + "-inherited-routes", "navigation_revision": REVISION,
        "standalone_pages": sum(row["standalone_page"] for row in routes.values()),
        "explicit_complete_bundle_fallbacks": sum(not row["standalone_page"] for row in routes.values()),
        "routes": routes,
    })
    files["checkpoints.json"] = json_bytes({
        "schema": SCHEMA, "publication_scope": SCOPE, "public_base_path": PUBLIC_BASE,
        "delivery_metadata_only": True, "alpha_admission_performed": False,
        "stable_admission_performed": False, "on_demand_alpha_lean_service_exposes_frontier": False,
        "navigation_revision": REVISION, "checkpoint_digest": inventory["checkpoint_digest"],
        "parent": inventory["parent"], "independent_checker": inventory["independent_checker"],
        "historical_local_inventory": {"path": "receipts/local-checkpoints.json",
                                       "bytes": len(local_files["checkpoints.json"]),
                                       "sha256": digest(local_files["checkpoints.json"])},
        "verification_boundary": "Fresh original HA and independently compiled Lean verification; literal historical local receipts, not Alpha or Stable admission.",
        "checkpoints": inventory["checkpoints"], "families": FAMILY_COUNTS,
        "new_theorem_count": 126, "previous_research_theorems": 170,
        "inherited_support_counted_as_new": False, "alpha_checked_use_node_count": 0,
        "stable_admitted_node_count": 0,
    })
    files["manifest.json"] = json_bytes({
        "schema": SCHEMA + "-manifest", "publication_scope": SCOPE,
        "checkpoint_digest": LOCAL_CHECKPOINT_DIGEST, "navigation_revision": REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {name: {"bytes": len(payload), "sha256": digest(payload)} for name, payload in sorted(files.items())},
    })
    return files
