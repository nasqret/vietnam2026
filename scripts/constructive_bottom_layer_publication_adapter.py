"""Presentation-only public delivery of unchanged, non-admitting checkpoints.

The canonical QR assets and the frozen local proof renderer are not edited.
This adapter changes delivery text, typed presentation metadata, and navigation
only. It preserves exact statements, tactics, definitions, bundles, and prior
verification receipts. Its caller must freshly run both real proof verifiers;
neither this module nor a stored manifest is a proof-admission mechanism.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Mapping
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "peano-lab-public-bottom-layer-checkpoints-v1"
SCOPE = "public_research_checkpoint"
REVISION = "ac7111ec14ff"
ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"
PUBLIC_BASE = "/proofs/checkpoints/"
LOCAL_MANIFEST_SHA256 = "d9bd86fe6860edb19c2adab5455d9ead395b0c3f0828baeb3f1037d4bf4955bb"
LOCAL_CHECKPOINT_DIGEST = "fc592c0a4a0c385178528860634b18678e846327e9206b410cab043eb2ce7d48"
LOCAL_FILE_COUNT = 493
FAMILY_COUNTS = {"euler-units": 32, "prime-fields": 87, "mobius-values": 21, "signed-sums": 30}
ADMISSION_FLAGS = ("enrolled_in_alpha", "admitted_to_alpha", "alpha_checked_use",
                   "checked_use", "stable_member", "admitted_to_stable")
OLD_STATUS = ("Local checkpoint: original HA and independently compiled Lean verified; "
              "not Alpha-enrolled, no Alpha checked-use authority; not Stable")
STATUS = OLD_STATUS.replace("Local checkpoint:", "Public research checkpoint:")
OLD_GRAPH_LABEL = "Local HA + independent Lean checkpoint — not Alpha-enrolled; no checked-use authority; not Stable"
GRAPH_LABEL = "Public research checkpoint: HA + independent Lean — not Alpha-enrolled; no checked-use authority; not Stable"
SERVICE_NOTE = ("Public research checkpoint, not admitted to Alpha or Stable. Alpha v30 remains 3222 "
                "checked-use theorems; Stable remains 432. The on-demand Alpha Lean service does not "
                "yet expose these checkpoint theorems; their independently checked literal bundles "
                "and unchanged sources are available below.")


class PublicCheckpointError(ValueError):
    """A delivery transform would alter evidence or misrepresent authority."""


def digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def strict_json(payload: bytes | str):
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise PublicCheckpointError("duplicate JSON member")
            result[name] = value
        return result
    def reject(value):
        raise PublicCheckpointError("non-finite JSON value: " + value)
    return json.loads(payload, object_pairs_hook=pairs, parse_constant=reject)


def read_pinned(path: Path, size: int, expected_sha256: str) -> bytes:
    if (type(size) is not int or size <= 0 or path.is_symlink()
            or not path.is_file() or path.stat().st_size != size):
        raise PublicCheckpointError("missing, unsafe, or wrongly sized pinned source: " + str(path))
    with path.open("rb") as handle:
        payload = handle.read(size + 1)
    if len(payload) != size or digest(payload) != expected_sha256:
        raise PublicCheckpointError("pinned source changed: " + str(path))
    return payload


@dataclass(frozen=True, slots=True)
class RouteIndex:
    path: str
    size: int
    sha256: str
    public_family: str
    source_family: str
    frontier_prefix: str = ""


# These are literal current v30 delivery inventories, not new admission
# evidence. A route is accepted only when its exact expanded statement agrees
# with the prerequisite freshly checked inside the complete checkpoint bundle.
ROUTE_INDEXES = (
    RouteIndex("constructive-advanced-layer-explorer/binary-modular-exponentiation/api/corpus.json", 159107, "580c75157c94bf9ecf8f3ed1b4f26d760a9f4c89ba568eb43b0819b903bc558b", "binary-modular-exponentiation/", "constructive-advanced-layer-explorer/binary-modular-exponentiation/"),
    RouteIndex("constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/api/corpus.json", 584462, "d014a6ee9469eca19f9a79710cc7f0d2d0f8046d4885b5be99a26c5b82f10100", "matrix-cofactor-expansion/", "constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/"),
    RouteIndex("constructive-second-wave-explorer-v30/cauchy-davenport/api/corpus.json", 1992206, "26695c3395431e7c215f7eef4f56b7988cf4950dc96d914f70bf78d8fb8da677", "cauchy-davenport/", "constructive-second-wave-explorer-v30/cauchy-davenport/"),
    RouteIndex("constructive-second-wave-explorer-v30/hensel-lifting/api/corpus.json", 1797414, "51036cb928ea48d411f61d92ec852d7edcbc0fcc4378c65371e84ebd63832a62", "hensel-lifting/", "constructive-second-wave-explorer-v30/hensel-lifting/"),
    RouteIndex("constructive-second-wave-explorer-v30/integer-linear-algebra/api/corpus.json", 15094624, "1c27c9bf9053795f4f5146546a48e6f8f479d659e3a8c0c96b4de36096eb49ca", "integer-linear-algebra/", "constructive-second-wave-explorer-v30/integer-linear-algebra/"),
    RouteIndex("constructive-lower-layer-explorer-v30/arithmetic-foundations/api/corpus.json", 921932, "037d0deead674e444650b1e8d1fd165d2b088f789d83a1b24239d305bd3930ca", "arithmetic-foundations/", "constructive-lower-layer-explorer-v30/arithmetic-foundations/"),
    RouteIndex("constructive-lower-layer-explorer-v30/gaussian-integers/api/corpus.json", 2159283, "2485862cd60e264d8ca4d974e416f1ba99fc694f65eb56df72ac852c43702815", "gaussian-integers/", "constructive-lower-layer-explorer-v30/gaussian-integers/"),
    RouteIndex("constructive-priority-layer-explorer-v30/squarefree-kernels/api/corpus.json", 2037215, "0b075de1032f6123a40806f5dde110373cfddca6356d90d624dc8f90497682e7", "squarefree-kernels/", "constructive-priority-layer-explorer-v30/squarefree-kernels/"),
    RouteIndex("constructive-priority-layer-explorer-v30/totient-products/api/corpus.json", 2777243, "79deafc1e309ad3d269db14a9ecc757d3a1bceced797e839634e85e68919ef8f", "totient-products/", "constructive-priority-layer-explorer-v30/totient-products/"),
    RouteIndex("constructive-frontier-explorer/two-squares/api/corpus.json", 2455790, "d6589c8dd111a50edfa5e3c5e10c7928d5cce52b667a424f5eb04614b789f886", "two-squares/", "constructive-frontier-explorer/two-squares/", "TS"),
    RouteIndex("pa-proof-explorer/api/corpus.json", 17229311, "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a", "quadratic-reciprocity/explorer/", "pa-proof-explorer/"),
    RouteIndex("bertrand-proof-explorer/api/corpus.json", 15707214, "50d1f69e62745b8a39d1980abf38d75dec587a90f64c5664ce446a0e8aea8651", "bertrand-postulate/explorer/", "bertrand-proof-explorer/"),
)
NO_STANDALONE_PAGE = frozenset((
    "all_prime_succ_intro", "all_prime_transport", "beta_factor_prefix_product_append",
    "coprime_bounded_mod_inverse", "factor_nonzero_left", "mod_inverse_implies_coprime",
    "signed_balance_extensional", "signed_balance_functional", "signed_balance_total",
    "signed_balance_zero_iff", "signed_decode_functional", "signed_negate_symmetric",
    "signed_negate_to_swapped_decode", "signed_negate_total", "signed_negate_zero",
))


def validate_local_files(files: Mapping[str, bytes]) -> dict:
    if len(files) != LOCAL_FILE_COUNT or digest(files.get("manifest.json", b"")) != LOCAL_MANIFEST_SHA256:
        raise PublicCheckpointError("the exact frozen local snapshot changed")
    manifest = strict_json(files["manifest.json"])
    if set(files) != set(manifest["files"]) | {"manifest.json"}:
        raise PublicCheckpointError("the local snapshot has an unexpected file inventory")
    for name, expected in manifest["files"].items():
        path = PurePosixPath(name)
        payload = files[name]
        if (path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name
                or type(payload) is not bytes or len(payload) != expected["bytes"]
                or digest(payload) != expected["sha256"]):
            raise PublicCheckpointError("a literal local snapshot file changed: " + name)
    inventory = strict_json(files["checkpoints.json"])
    if (inventory["checkpoint_digest"] != LOCAL_CHECKPOINT_DIGEST
            or inventory["published"] is not False
            or inventory["alpha_admission_performed"] is not False
            or inventory["stable_admission_performed"] is not False):
        raise PublicCheckpointError("the local inventory has invalid non-admission metadata")
    return inventory


def _base36(number: int) -> str:
    alphabet, value = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", ""
    while number:
        number, remainder = divmod(number, 36)
        value = alphabet[remainder] + value
    return value or "0"


def inherited_routes(corpora: Mapping[str, dict], *, root: Path = ROOT) -> dict[str, dict]:
    wanted = {}
    for corpus in corpora.values():
        for row in corpus["external_dependencies"]:
            previous = wanted.setdefault(row["name"], row)
            if previous["statement"] != row["statement"]:
                raise PublicCheckpointError("inherited prerequisite statement differs between bundles")
    if len(wanted) != 107:
        raise PublicCheckpointError("unexpected inherited prerequisite inventory")
    result = {}
    for index in ROUTE_INDEXES:
        corpus = strict_json(read_pinned(root / "book/_static" / index.path, index.size, index.sha256))
        rows = corpus.get("nodes", corpus.get("theorems", ()))
        for position, row in enumerate(rows):
            name = row["name"]
            if name not in wanted or name in result:
                continue
            expected = wanted[name]
            if (row["statement"] != expected["statement"]
                    or digest(row["statement"].encode()) != expected["statement_sha256"]):
                raise PublicCheckpointError("historical route names a different exact statement: " + name)
            tag = row.get("id") or row.get("tag") or corpus.get("tags", {}).get(name)
            if tag is None and index.frontier_prefix:
                tag = index.frontier_prefix + _base36(position).zfill(4)
            if not isinstance(tag, str) or re.fullmatch(r"[A-Z0-9]{4,10}", tag) is None:
                raise PublicCheckpointError("historical proof has no exact route tag: " + name)
            suffix = "defined/tag/" + tag + ".html"
            if not index.public_family.endswith("/explorer/"):
                suffix = "explorer/" + suffix
            source_suffix = suffix.removeprefix("explorer/") if index.source_family in ("pa-proof-explorer/", "bertrand-proof-explorer/") else suffix
            source = root / "book/_static" / (index.source_family + source_suffix)
            if source.is_symlink() or not source.is_file():
                raise PublicCheckpointError("the exact historical theorem page is absent: " + str(source))
            result[name] = {"name": name, "statement_sha256": expected["statement_sha256"],
                            "standalone_page": True, "public_path": "/proofs/" + index.public_family + suffix,
                            "source_page": source.relative_to(root).as_posix(),
                            "route_index": index.path, "route_index_sha256": index.sha256}
    if set(wanted) - result.keys() != NO_STANDALONE_PAGE or len(result) != 92:
        raise PublicCheckpointError("standalone historical route coverage changed")
    for name in sorted(NO_STANDALONE_PAGE):
        result[name] = {"name": name, "statement_sha256": wanted[name]["statement_sha256"],
                        "standalone_page": False,
                        "note": "Inherited Alpha proof; no standalone historical explorer page. Its exact statement and freshly checked complete-bundle node remain linked."}
    return dict(sorted(result.items()))


def public_corpus(original: dict, routes: Mapping[str, dict]) -> dict:
    corpus = deepcopy(original)
    slug = corpus["family_slug"]
    if slug not in FAMILY_COUNTS or corpus["node_count"] != FAMILY_COUNTS[slug]:
        raise PublicCheckpointError("unexpected public checkpoint family or theorem count")
    for node in (corpus, *corpus["nodes"]):
        if (any(node.get(key) is not False for key in ADMISSION_FLAGS)
                or node.get("local_checkpoint_verified") is not True
                or node.get("original_ha_bundle_verified") is not True
                or node.get("independent_lean_bundle_verified") is not True):
            raise PublicCheckpointError("public delivery cannot confer library authority")
    corpus["schema"] = SCHEMA
    corpus["publication_scope"] = SCOPE
    corpus["candidate_status"] = STATUS
    corpus["campaign_goal_scope"] = corpus["campaign_goal_scope"].replace("locally_proved", "proved_in_checkpoint")
    for node in corpus["nodes"]:
        if node["status"] != OLD_STATUS:
            raise PublicCheckpointError("unexpected theorem status before publication")
        node["status"] = STATUS
    corpus["external_theorem_routes"] = {
        row["name"]: (routes[row["name"]]["public_path"] if routes[row["name"]]["standalone_page"]
                      else PUBLIC_BASE + slug + "/checkpoint.html#theorem-" + row["name"])
        for row in corpus["external_dependencies"]}
    corpus["external_route_boundary"] = "Exact inherited statements; explicit bundle-receipt fallback when no standalone historical page exists."
    corpus["on_demand_alpha_lean_service_exposes_frontier"] = False
    return corpus


def public_graph(original: dict) -> dict:
    graph = deepcopy(original)
    if (graph.get("publication_scope") != "local-only-checkpoint"
            or any(graph.get(key) is not False for key in ADMISSION_FLAGS)):
        raise PublicCheckpointError("graph authority or original scope changed")
    graph["schema"] = SCHEMA + "-graph"
    graph["publication_scope"] = SCOPE
    return graph


# Only delivery-language phrases are transformed. In particular, "local
# proposition" and genuine theorem summaries are mathematical text, not a
# claim about whether this copy is publicly accessible.
PROSE = (
    (OLD_STATUS, STATUS),
    ("Local-only independently verified checkpoint:", "Public research checkpoint, independently verified:"),
    ("Local original-HA + independent Lean checkpoint only", "Public original-HA + independent Lean research checkpoint; no library admission"),
    ("This local checkpoint grants no Alpha checked-use authority or Stable membership.", "Public delivery grants no Alpha checked-use authority or Stable membership."),
    ("none — local checkpoint only", "none — non-admitting research checkpoint"),
    ("Literal bundle and local receipt", "Literal bundle and unchanged verification receipt"),
    ("Exact local checkpoint receipt", "Exact research checkpoint receipt"),
    ("Exact local checkpoint — ", "Exact research checkpoint — "),
    ("Local bottom-layer proof checkpoints", "Public bottom-layer proof checkpoints"),
    ("Local proof checkpoints", "Research proof checkpoints"),
    ("Local checkpoint map", "Research checkpoint map"),
    ("local checkpoint map", "research checkpoint map"),
    ("Constructive arithmetic · local-only development", "Constructive arithmetic · public research checkpoints"),
    ("This map is a local dispatch page, not an updated global campaign or a new Alpha release.", "This public checkpoint map is separate from the unchanged global campaign and is not a new Alpha release."),
    ("new local theorems", "new checkpoint theorems"),
    ("G014 is locally complete.", "The exact G014 statement is proved in this checkpoint, without Alpha admission."),
    ("The exact G014 theorem is proved locally for", "The exact G014 theorem is proved in this research checkpoint for"),
    ("locally kernel- and Lean-verified theorems", "kernel- and independently Lean-verified checkpoint theorems"),
    ("Locally HA/Lean verified", "HA/Lean checkpoint verified"),
    ("locally verified theorems", "verified checkpoint theorems"),
    ("Inspect the local definition DAG", "Inspect the family definition DAG"),
)


def _prose(text: str) -> str:
    for old, new in PROSE:
        text = text.replace(old, new)
    return text


def _relative(page: str, public_path: str) -> str:
    parsed = urlsplit(public_path)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/proofs/"):
        raise PublicCheckpointError("public navigation escaped the proof library")
    path = posixpath.relpath(parsed.path, posixpath.dirname(PUBLIC_BASE + page))
    if parsed.path.endswith("/"):
        path += "/"
    query = parsed.query + ("&" if parsed.query else "") + "v=" + REVISION
    return urlunsplit(("", "", path, query, parsed.fragment))


def _attribute(raw: str, name: str, value: str) -> str:
    pattern = re.compile(r"(\s" + re.escape(name) + r"\s*=\s*)([\"'])(.*?)\2", re.DOTALL)
    raw, count = pattern.subn(lambda match: match[1] + '"' + escape(value, quote=True) + '"', raw)
    if count != 1:
        raise PublicCheckpointError("expected exactly one quoted HTML attribute: " + name)
    return raw


class PublicHTML(HTMLParser):
    """Context-aware transform; never a raw replacement over HTML or scripts."""

    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"))

    def __init__(self, page: str, routes: Mapping[str, dict], graph: dict | None = None, original_graph: dict | None = None):
        super().__init__(convert_charrefs=False)
        self.page, self.routes, self.graph, self.original_graph = page, routes, graph, original_graph
        self.output, self.stack = [], []
        self.script = None
        self.notice_count = self.nav_count = self.head_count = self.graph_count = 0

    @property
    def protected(self):
        return any(tag in {"pre", "code", "script", "style"} for tag, _, _ in self.stack)

    def _external(self, name):
        route = self.routes[name]
        target = (route["public_path"] if route["standalone_page"] else
                  PUBLIC_BASE + self.page.split("/", 1)[0] + "/checkpoint.html#theorem-" + name)
        return _relative(self.page, target)

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if len(attrs) != len(pairs):
            raise PublicCheckpointError("duplicate HTML attribute")
        raw = self.get_starttag_text()
        out_tag = tag
        if tag == "meta" and attrs.get("name") == "robots":
            return
        if tag == "link" and attrs.get("rel") == "canonical":
            return
        if tag == "meta" and attrs.get("property") in {"og:url", "og:image", "og:type"}:
            return
        if tag == "meta" and attrs.get("name") == "proof-publication-scope":
            return  # one uniform explicit public scope is added at </head>
        if tag == "meta" and (attrs.get("name") == "description" or attrs.get("property") in {"og:title", "og:description"}):
            raw = _attribute(raw, "content", _prose(attrs["content"]))
        if not self.protected:
            if "data-search" in attrs and attrs["data-search"]:
                updated = _prose(attrs["data-search"])
                if updated != attrs["data-search"]:
                    raw = _attribute(raw, "data-search", updated)
            if "href" in attrs:
                old = urlsplit(attrs["href"])
                if "constructive-gaussian-campaign" in old.path.split("/"):
                    path = old.path.replace("constructive-gaussian-campaign", "grand-campaign")
                    raw = _attribute(raw, "href", urlunsplit((old.scheme, old.netloc, path, old.query, old.fragment)))
                elif old.fragment.startswith("theorem-") and old.path.endswith("checkpoint.html"):
                    name = old.fragment.removeprefix("theorem-")
                    if name in self.routes:
                        raw = _attribute(raw, "href", self._external(name))
            if tag == "span" and "data-external-name" in attrs:
                name = attrs["data-external-name"]
                if name not in self.routes:
                    raise PublicCheckpointError("unknown external theorem chip")
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
        # None of the frozen pages uses non-void XML-style elements.
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
                prefix, suffix = "window.PA_DEFINED_GRAPH=", ";"
                if not source.startswith(prefix) or not source.endswith(suffix):
                    raise PublicCheckpointError("unknown graph assignment")
                if strict_json(source[len(prefix):-1]) != self.original_graph or self.graph is None:
                    raise PublicCheckpointError("embedded graph differs from the exact graph API")
                source = prefix + json.dumps(self.graph, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + suffix
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
            raise PublicCheckpointError("unexpected or unbalanced HTML boundary: " + tag)
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

    def handle_data(self, text):
        if self.script is not None:
            self.script[1].append(text)
            return
        if self.protected:
            self.output.append(text)
            return
        if self.stack and self.stack[-1][0] == "head" and text.isspace():
            # Removing local-only metadata may leave an indented blank line.
            # Join only adjacent head-whitespace chunks separated by a removed
            # tag. Preserve indentation before retained tags and every byte of
            # proof/code/script text; trim only complete whitespace-only lines.
            if self.output and self.output[-1].isspace():
                text = self.output.pop() + text
            text = re.sub(r"(?m)^[ \t]+(?=\r?\n)", "", text)
        if text == "Inherited Alpha v30 premise, freshly checked in this complete bundle":
            article = next((attrs for tag, _, attrs in reversed(self.stack) if tag == "article"), {})
            name = str(article.get("id", "")).removeprefix("theorem-")
            if name not in self.routes:
                raise PublicCheckpointError("unknown inherited receipt theorem")
            route = self.routes[name]
            label = ("Read the exact inherited Alpha proof" if route["standalone_page"] else
                     "Inherited Alpha proof; no standalone historical explorer page")
            text = ('<a href="' + escape(self._external(name), quote=True) + '">' + label + '</a>'
                    ' · freshly checked in this complete bundle; exact statement and bundle node below.')
            self.output.append(text)
        else:
            self.output.append(_prose(text))

    def handle_entityref(self, name):
        self.output.append("&" + name + ";")

    def handle_charref(self, name):
        self.output.append("&#" + name + ";")

    def handle_decl(self, declaration):
        self.output.append("<!" + declaration + ">")

    def handle_comment(self, text):
        self.output.append("<!--" + text + "-->")

    def finish(self, payload: bytes) -> bytes:
        self.feed(payload.decode("utf-8"))
        self.close()
        if (self.stack or self.script is not None or self.head_count != 1
                or self.notice_count != 1 or self.nav_count != 1
                or self.graph_count != (1 if self.graph is not None else 0)):
            raise PublicCheckpointError("incomplete public HTML adaptation")
        return "".join(self.output).encode()


def adapt_files(local_files: Mapping[str, bytes], *, root: Path = ROOT) -> dict[str, bytes]:
    """Pure delivery transform over a freshly verified, exact local snapshot."""
    inventory = validate_local_files(local_files)
    old_corpora = {slug: strict_json(local_files[slug + "/api/corpus.json"]) for slug in FAMILY_COUNTS}
    routes = inherited_routes(old_corpora, root=root)
    corpora = {slug: public_corpus(corpus, routes) for slug, corpus in old_corpora.items()}
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
        files[slug + "/api/corpus.json"] = json_bytes(corpora[slug])
        files[slug + "/api/graph.json"] = json_bytes(graphs[slug])
        files[slug + "/explorer/defined/api/graph.json"] = json_bytes(graphs[slug])
    # The stored local report is historical evidence and remains literal. In
    # particular, its published:false flag is not silently rewritten to true.
    files["receipts/local-checkpoints.json"] = local_files["checkpoints.json"]
    files["historical-prerequisites.json"] = json_bytes({
        "schema": SCHEMA + "-inherited-routes", "navigation_revision": REVISION,
        "standalone_historical_pages": 92, "explicit_complete_bundle_fallbacks": 15,
        "routes": routes,
    })
    public_inventory = {
        "schema": SCHEMA, "publication_scope": SCOPE, "public_base_path": PUBLIC_BASE,
        "delivery_metadata_only": True, "alpha_admission_performed": False,
        "stable_admission_performed": False, "on_demand_alpha_lean_service_exposes_frontier": False,
        "navigation_revision": REVISION, "checkpoint_digest": inventory["checkpoint_digest"],
        "parent": inventory["parent"], "independent_checker": inventory["independent_checker"],
        "historical_local_inventory": {"path": "receipts/local-checkpoints.json",
                                       "bytes": len(local_files["checkpoints.json"]),
                                       "sha256": digest(local_files["checkpoints.json"])},
        "verification_boundary": "The generator freshly invokes original HA and the pinned independently compiled Lean verifier. Literal prior local-stage receipts are preserved, not promoted to admission.",
        "checkpoints": inventory["checkpoints"], "families": FAMILY_COUNTS,
        "new_theorem_count": 170, "alpha_checked_use_node_count": 0, "stable_admitted_node_count": 0,
    }
    files["checkpoints.json"] = json_bytes(public_inventory)
    files["manifest.json"] = json_bytes({
        "schema": SCHEMA + "-manifest", "publication_scope": SCOPE,
        "checkpoint_digest": LOCAL_CHECKPOINT_DIGEST, "navigation_revision": REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {name: {"bytes": len(payload), "sha256": digest(payload)} for name, payload in sorted(files.items())},
    })
    return files
