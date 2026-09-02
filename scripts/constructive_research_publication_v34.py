"""Canonical v34 reader projections requiring genuine same-live admission.

The four v33 reader packages are immutable presentation parents, not new
proof authority. Current metadata changes; exact mathematics, non-admitted
aliases and original first-admission evidence do not. The new131-row inventory
is authenticated separately by its complete HA/Lean and ordinary-root audit.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import constructive_completed_lower_publication_v31 as publication
import constructive_checked_explorer_renderer as render
import constructive_research_publication_v33 as previous
import upgrade_constructive_historical_publication_v31 as historical

ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION, CURRENT_COUNT, STABLE_COUNT = "v34", 4223, 432
SCHEMA = "peano-lab-alpha-v34-canonical-publication-v1"
PublicationError = publication.PublicationError
digest, json_bytes, strict_json = publication.digest, publication.json_bytes, publication.strict_json
safe_relative, read_pinned = publication.safe_relative, publication.read_pinned
OUTPUT_NAMES = {'gcd-congruence': 'constructive-gcd-congruence-explorer-v34', 'polynomial': 'constructive-polynomial-euclidean-explorer-v34', 'research': 'constructive-research-explorer-v34', 'completed': 'constructive-completed-lower-explorer-v34', 'historical': 'constructive-historical-explorers-v34', 'atlas': 'constructive-research-campaign-v34'}
OLDER = {'polynomial': ('constructive-polynomial-euclidean-explorer-v33', 64446, 'c73a62e85d0907f71f1ed5cab32f5115cc8d4452ff615c06d168545b47dc6bda'), 'research': ('constructive-research-explorer-v33', 100746, 'ac763c90cc1098d73ed3e8d6ceae1c07de68468d3484fb79114d482e9a82fa58'), 'completed': ('constructive-completed-lower-explorer-v33', 368852, '769bd7b5938b5a46961b4794e6c7460ef6564306deb30fcbab378ac92f76660d'), 'historical': ('constructive-historical-explorers-v33', 1780999, 'fc2040db768deac43a23c420e4da9069e26f2853e391e7dd890ff91900d91735')}
RESEARCH_SLUGS = ("multiplicative-convolution", "polynomial-division-prerequisites")
NEW_SLUGS = ("polynomial-gcd-bezout", "congruence-arithmetic")
LEGACY_DOCUMENTATION_ROUTES = previous.LEGACY_DOCUMENTATION_ROUTES
ASSET_DIGESTS = previous.ASSET_DIGESTS
_CURRENT_FIELDS = historical._CURRENT_FIELDS
_MATHEMATICAL_FIELDS = historical._MATHEMATICAL_FIELDS
_AUTHORITY_FIELDS = historical._AUTHORITY_FIELDS
FAMILY_ORDER = historical.FAMILY_ORDER
_RENDER_TOKEN = object()
_snapshot, _source = previous._snapshot, previous._source
canonical_bytes = historical.canonical_bytes
_check_literal_row = previous._check_literal_row


def require_live(context):
    # Reject ordinary observations without importing a catalogue/edition stack.
    # This is only an early rejection: a lookalike still must pass the exact
    # canonical class-identity check below and its genuine capability seal.
    kind = type(context)
    if kind is not BoundPresentation and (kind.__module__, kind.__name__) != (
            "verify_peano_library_channels_v34", "LiveReleaseContext"):
        raise PublicationError("only a genuine live v34 release can authorize publication")
    from verify_peano_library_channels_v34 import LiveReleaseContext
    if type(context) not in (LiveReleaseContext, BoundPresentation):
        raise PublicationError("only a genuine live v34 release can authorize publication")
    context.require_unchanged()
    rows = context.catalog.get("theorems")
    if (type(rows) is not list or len(rows) != CURRENT_COUNT
            or context.catalog.get("checked_use_count") != CURRENT_COUNT
            or context.catalog.get("stable_count") != STABLE_COUNT
            or context.channels.get("default_channel") != "stable"
            or len(context.promoted_names) != 131
            or tuple(row["name"] for row in rows[4092:]) != context.promoted_names
            or tuple(context.families) != NEW_SLUGS
            or context.revision != context.catalog_sha256[:12]
            or context.channels["channels"]["alpha"]["artifact_sha256"] != context.catalog_sha256):
        raise PublicationError("live publication scope differs from exact4092+131 admission")


def require_render_inputs():
    # Reuse the immutable ancestor's complete transitive presentation binding;
    # this never accepts its v33 capability or changes its module globals.
    records = [("immutable_v33_presentation_sources", previous.require_render_inputs())]
    for directory, size, expected in OLDER.values():
        root, manifest = _snapshot(directory, size, expected)
        records.append((directory, size, expected))
        for name, pin in sorted(manifest["files"].items()):
            _source(root, manifest, name)
            records.append((directory + "/" + name, pin["bytes"], pin["sha256"]))
    paths = (
        "scripts/constructive_research_publication_v34.py",
        "scripts/constructive_alpha_v34_publication_process.py",
        "scripts/publish_constructive_research_v34.py",
        "scripts/build_constructive_gcd_congruence_explorer_v34.py",
        "scripts/constructive_polynomial_gcd_definitions_v34.py",
        "scripts/constructive_polynomial_gcd_definition_graph_v34.py",
        "scripts/extend_constructive_research_campaign_v34.py",
        "scripts/test_constructive_research_publication_source_v34.py",
        "peano-lab/py/tests/test_constructive_research_publication_v34.py",
        "peano-lab/py/tests/test_constructive_alpha_v34_publication_process.py",
        "scripts/test_constructive_gcd_congruence_explorer_v34.py",
        "scripts/test_constructive_polynomial_gcd_definitions_v34.py",
        "peano-lab/py/tests/test_constructive_research_campaign_v34.py",
    )
    from check_alpha_v34_research import _file_digest
    from build_constructive_gcd_congruence_explorer_v34 import source_paths
    for relative in dict.fromkeys((*paths, *source_paths())):
        records.append((relative, *_file_digest(relative, 4 * 1024 * 1024)))
    from extend_constructive_research_campaign_v34 import parent_files, PARENT_RELATIVE
    for name, raw in parent_files().items():
        records.append((PARENT_RELATIVE + "/" + name, len(raw), digest(raw)))
    return digest(json_bytes(records))


class BoundPresentation:
    __slots__=("_token","_release","render_source_binding_sha256")

    def __init__(self,token,context,binding):
        if token is not _RENDER_TOKEN:
            raise PublicationError("stored metadata cannot mint a presentation capability")
        self._token,self._release,self.render_source_binding_sha256=token,context,binding

    def __getattr__(self,name):
        return getattr(self._release,name)

    def require_unchanged(self):
        if self._token is not _RENDER_TOKEN:
            raise PublicationError("foreign presentation capability")
        self._release.require_unchanged()
        if require_render_inputs() != self.render_source_binding_sha256:
            raise PublicationError("renderer or original snapshot changed during publication")


def bind_live_context(context):
    require_live(context)
    from verify_peano_library_channels_v34 import LiveReleaseContext
    if type(context) is not LiveReleaseContext:
        raise PublicationError("binding presentation requires the original live release capability")
    return BoundPresentation(_RENDER_TOKEN,context,require_render_inputs())

def _current_metadata(context):
    return {"alpha_edition_version":"v34","alpha_edition_checked_use_count":4223,
        "alpha_edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "alpha_catalog_sha256":context.catalog_sha256,"catalog_sha256":context.catalog_sha256,
        "edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "navigation_revision":context.revision,"html_revision":context.revision}

def _current_text(text):
    """Refresh current labels only; first admissions and quoted math survive."""
    text = re.sub(r"\bAlpha v33(?= (?:checked-use|checked use|independently verified))", "Alpha v34", text)
    return (text.replace("Current Alpha: 4,092", "Current Alpha: 4,223")
        .replace("Current Alpha has 4,092", "Current Alpha has 4,223")
        .replace("current Alpha v33", "current Alpha v34")
        .replace("Current Alpha v33", "Current Alpha v34")
        .replace("among 4092 checked release theorems", "among 4223 checked release theorems"))


def _refresh_document(original: dict, by_name: Mapping[str, dict], current: Mapping[str, object]) -> dict:
    """Pure metadata projection: source syntax and historical flags are fixed."""
    if type(original) is not dict:
        raise publication.PublicationError("historical API must be a JSON object")
    result = deepcopy(original)
    for key in _CURRENT_FIELDS & result.keys():
        result[key] = current[key]
    for field in ("candidate_status",):
        if type(result.get(field)) is str:
            result[field] = _current_text(result[field])
    for key in ("nodes", "theorems", "external_dependencies"):
        if key not in result:
            continue
        if type(result[key]) is not list:
            raise publication.PublicationError("historical API node list changed type")
        for old, node in zip(original[key], result[key], strict=True):
            if node.get("kind") == "definition":
                continue
            name = node.get("name")
            if type(name) is not str:
                raise publication.PublicationError("historical API theorem name changed")
            row = by_name.get(name)
            claimed = node.get("alpha_checked_use") is True or node.get("checked_use") is True
            if claimed:
                if (row is None or row.get("checked_use") is not True or row.get("body_checked") is not True):
                    raise publication.PublicationError("an old checked-use claim has no exact current theorem")
                for statement, digest_field in (("statement", "statement_sha256"), ("explicit_statement", "explicit_statement_sha256")):
                    if statement in node and (node[statement] != row["statement"]
                            or node.get(digest_field) != row["statement_sha256"]):
                        raise publication.PublicationError("a historical checked theorem changed its exact statement")
                stable = node.get("stable_member", node.get("admitted_to_stable"))
                if stable is not None and stable is not (row.get("membership") == "stable"):
                    raise publication.PublicationError("historical Stable membership changed")
            # False or absent authority remains false or absent, even if a
            # similarly named theorem exists in the current catalogue.
            for field in _CURRENT_FIELDS & node.keys():
                node[field] = current[field]
            for field in ("status", "status_label"):
                if type(node.get(field)) is str:
                    node[field] = _current_text(node[field])
            for field in (*_MATHEMATICAL_FIELDS, *_AUTHORITY_FIELDS):
                if old.get(field) != node.get(field) or (field in old) != (field in node):
                    raise publication.PublicationError("publication changed historical syntax or authority")
    return result


def _navigation_href(value: str, revision: str) -> str:
    parsed = urlsplit(value)
    own = parsed.scheme == "https" and parsed.netloc == "bnaskrecki.faculty.wmi.amu.edu.pl" and parsed.path.startswith("/proofs/")
    if ((parsed.scheme or parsed.netloc) and not own) or not parsed.path or parsed.path.endswith((".css", ".js", ".png", ".svg", ".jpg", ".woff2")):
        return value
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    pairs = [(key, item) for key, item in pairs if key != "v"]
    pairs.append(("v", revision))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(pairs), parsed.fragment))


class _HistoricalHTML(HTMLParser):
    """Only HTML navigation/current metadata and typed graph data are revised."""

    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"))
    GRAPH_IDS = {"pa-defined-graph-data": "PA_DEFINED_GRAPH", "pa-proof-graph-data": "PA_PROOF_GRAPH"}
    RELEASE_IDS = frozenset(("pa-proof-release-evidence", "pa-defined-release-evidence",
                             "pa-bertrand-release-evidence", "pa-bertrand-defined-release-evidence"))

    def __init__(self, page: str, revision: str, *, graph: dict | None, portable_script: str,
                 protected_summaries: frozenset[str] = frozenset()):
        super().__init__(convert_charrefs=False)
        self.page, self.revision, self.graph, self.portable_script = page, revision, graph, portable_script
        self.protected_summaries = protected_summaries
        self.stack, self.parts = [], []
        self.script_id = None
        self.script_parts = []
        self.heads = self.bodies = self.graphs = 0
        self.canonical = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if len(values) != len(attributes):
            raise publication.PublicationError("duplicate historical HTML attribute")
        if self.skip_depth:
            if tag not in self.VOID:
                self.skip_depth += 1
            return
        if tag == "p" and "data-current-release" in values:
            self.skip_depth = 1
            return
        if tag == "meta" and values.get("name") == "proof-publication-scope":
            return
        raw = self.get_starttag_text()
        changed = False
        if tag == "a" and "href" in values:
            revised = _navigation_href(values["href"], self.revision)
            changed = revised != values["href"]
            values["href"] = revised
        if tag == "link" and values.get("rel") == "canonical":
            old = urlsplit(values.get("href", ""))
            if old.scheme or old.netloc:
                if old.scheme != "https" or old.netloc != "bnaskrecki.faculty.wmi.amu.edu.pl" or not old.path.startswith("/proofs/"):
                    raise publication.PublicationError("foreign historical canonical route")
                canonical = urlunsplit((old.scheme, old.netloc, old.path, "", ""))
            else:
                target = posixpath.normpath(posixpath.join(posixpath.dirname(self.page), unquote(old.path)))
                if not publication.safe_relative(target):
                    raise publication.PublicationError("historical canonical route escapes its reader")
                canonical = "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + target.removesuffix("index.html")
            values["href"] = canonical
            self.canonical, changed = True, True
        if tag == "meta" and values.get("property") == "og:url":
            values["content"] = "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + self.page.removesuffix("index.html")
            changed = True
        if changed:
            raw = "<" + tag + "".join(" " + key + ("" if value is None else '="' + escape(value, quote=True) + '"') for key, value in values.items()) + ">"
        self.parts.append(raw)
        if tag == "main":
            slug = self.page.split("/", 1)[0]
            detail = posixpath.relpath(slug + "/api/first-admission.json", posixpath.dirname(self.page) or ".")
            first_link = (' <a href="' + escape(_navigation_href(detail, self.revision), quote=True)
                          + '">Exact original first-admission records</a>.') if slug in FAMILY_ORDER else ""
            self.parts.append('<p class="pa-callout pd-callout" data-current-release="v34">Current library: Alpha v34, 4,223 checked-use theorems; Stable remains 432. Historical first admissions, original proof editions, and non-admitted aliases are preserved.' + first_link + '</p>')
        if tag == "script":
            self.script_id = values.get("id")
            self.script_parts = []
        if tag not in self.VOID:
            self.stack.append((tag, values))

    def handle_startendtag(self, tag, attributes):
        if tag not in self.VOID:
            raise publication.PublicationError("unexpected historical self-closing element")
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if not self.stack or self.stack[-1][0] != tag:
            raise publication.PublicationError("unbalanced historical HTML: " + tag)
        self.stack.pop()
        if tag == "script":
            data = "".join(self.script_parts)
            if self.script_id in self.GRAPH_IDS:
                variable = self.GRAPH_IDS[self.script_id]
                match = re.fullmatch(r"\s*window\." + variable + r"\s*=\s*(\{.*\});\s*", data, re.S)
                if match is None or self.graph is None:
                    raise publication.PublicationError("historical inline graph has no exact typed API peer")
                publication.strict_json(match[1])
                data = "window." + variable + "=" + canonical_bytes(self.graph).decode("utf-8").replace("<", "\\u003c") + ";"
                self.graphs += 1
            elif self.script_id in self.RELEASE_IDS:
                # Only the frozen release-label adapter, never proof scripts
                # or arbitrary JavaScript strings, receives current prose.
                data = _current_text(data)
            self.parts.append(data)
            self.script_id, self.script_parts = None, []
        if tag == "head":
            if not self.canonical:
                self.parts.append('<link rel="canonical" href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/' + escape(self.page.removesuffix("index.html"), quote=True) + '">')
            self.parts.append('<meta name="proof-publication-scope" content="alpha-v34-historical-first-admission-preserved">')
            self.heads += 1
        if tag == "body":
            self.parts.append(self.portable_script)
            self.bodies += 1
        self.parts.append("</" + tag + ">")

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.stack and self.stack[-1][0] == "script":
            self.script_parts.append(data)
        elif any(tag in {"pre", "code", "style"} for tag, _ in self.stack) or data.strip() in self.protected_summaries:
            self.parts.append(data)
        else:
            self.parts.append(_current_text(data))

    def handle_entityref(self, name):
        if not self.skip_depth:
            self.parts.append("&" + name + ";")

    def handle_charref(self, name):
        if not self.skip_depth:
            self.parts.append("&#" + name + ";")

    def handle_comment(self, data):
        if not self.skip_depth:
            self.parts.append("<!--" + data + "-->")

    def handle_decl(self, decl):
        self.parts.append("<!" + decl + ">")

    def finish(self, payload: bytes) -> bytes:
        self.feed(payload.decode("utf-8"))
        self.close()
        if (self.stack or self.skip_depth or self.heads != 1 or self.bodies != 1
                or (self.graph is not None and self.graphs != 1)):
            raise publication.PublicationError("historical reader lost its exact HTML/graph structure")
        return "".join(self.parts).encode("utf-8")


def _new_family_metadata():
    from build_constructive_gcd_congruence_explorer_v34 import family_metadata
    return tuple(family_metadata(slug) for slug in NEW_SLUGS)


def _all_family_metadata():
    result = []
    for phase, snapshot in OLDER.items():
        _root, manifest = _snapshot(*snapshot)
        for item in manifest["families"]:
            result.append({**item, "package": OUTPUT_NAMES[phase]})
    result.extend(_new_family_metadata())
    if len(result) != 68 or len({row["slug"] for row in result}) != 68:
        raise PublicationError("the exact68-family inventory changed")
    return tuple(result)


def _routes():
    routes = {}
    for snapshot in OLDER.values():
        root, manifest = _snapshot(*snapshot)
        for name in manifest["files"]:
            if name.count("/") == 2 and name.endswith("/api/corpus.json"):
                corpus = strict_json(_source(root, manifest, name))
                slug = name.split("/", 1)[0]
                for node in historical._nodes(corpus):
                    tag, theorem = node.get("id", node.get("tag")), node.get("name")
                    if (node.get("kind") != "definition" and type(theorem) is str
                            and type(tag) is str and re.fullmatch(r"[A-Z]+[0-9A-F]{4}", tag)):
                        exact = slug + "/explorer/defined/tag/" + tag + ".html"
                        if exact in manifest["files"]:
                            routes.setdefault(theorem, exact)
    for family in _new_family_metadata():
        for name, tag in family["tags"].items():
            if name in routes:
                raise PublicationError("a new theorem shadows an older route")
            routes[name] = family["slug"] + "/explorer/defined/tag/" + tag + ".html"
    return routes


def _portable_script():
    packages = {row["slug"]: row["package"] for row in _all_family_metadata()}
    from build_constructive_completed_lower_explorer_v31 import _portable_script as original
    raw = original(packages)
    raw = raw.replace(json.dumps(["/" + publication.OUTPUT_NAME + "/", "/" + publication.HISTORICAL_OUTPUT_NAME + "/"]),
        json.dumps(["/" + name + "/" for name in OUTPUT_NAMES.values()]))
    return raw.replace("/" + publication.ATLAS_NAME + "/index.html", "/" + OUTPUT_NAMES["atlas"] + "/index.html")


def _assets():
    root, manifest = _snapshot(*OLDER["research"])
    for name, expected_hash in ASSET_DIGESTS.items():
        raw = _source(root, manifest, "assets/" + name)
        if digest(raw) != expected_hash:
            raise PublicationError("canonical QR asset changed: " + name)
        yield "assets/" + name, raw


_family_models = previous._family_models
_dashboard_enhancement = previous._dashboard_enhancement


def _phase_index(phase,metadata,revision):
    cards="".join('<article class="family-card"><h2>'+escape(row["title"])+'</h2><p>'
        +str(row["checked_use_count"])+' checked-use records.</p><a class="primary-action" href="'
        +escape(_navigation_href(row["slug"]+"/",revision),quote=True)+'">Explore the proof map</a></article>'
        for row in metadata)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Constructive proof families — Alpha v34</title><link rel="stylesheet" href="assets/proofs.css"></head>'
        '<body><header class="hero"><div class="shell"><p class="eyebrow">Alpha v34 · Stable 432 unchanged</p>'
        '<h1>'+escape(phase.title())+' proof families</h1><p class="lede">Current Alpha has 4,223 checked-use entries. '
        'Original first admissions and exact proofs are preserved.</p></div></header><main class="shell"><section class="family-grid">'
        +cards+'</section><section class="release-note">Full finite signed G009 is admitted; G091 prime-power fields remain open.</section></main></body></html>').encode()

def _publication_manifest(context,phase,pins,metadata,**extra):
    return json_bytes({"schema":SCHEMA+"-manifest","publication_scope":"alpha_checked_use_publication",
        "alpha_edition_version":"v34","alpha_edition_checked_use_count":4223,"stable_edition_count":432,
        "catalog_sha256":context.catalog_sha256,"edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "html_revision":context.revision,"families":list(metadata),"phase":phase,
        "file_count_excluding_manifest":len(pins),"files":dict(sorted(pins.items())),
        "release_source_binding_sha256":context.source_binding_sha256,
        "render_source_binding_sha256":context.render_source_binding_sha256,
        "current_G009_multiplicative_closure_proved":True,"current_G091_prime_power_fields_proved":False,**extra})

def _refresh_schema(value):
    result=deepcopy(value)
    def visit(node):
        if type(node) is dict:
            fields=node.get("properties")
            if type(fields) is dict and "alpha_edition_version" in fields:
                field=fields["alpha_edition_version"]
                if "const" in field:
                    if type(field["const"]) is not str or field["const"]!="v33":
                        raise PublicationError("unreviewed historical edition constraint")
                    field["const"]="v34"
            for item in node.values(): visit(item)
        elif type(node) is list:
            for item in node: visit(item)
    visit(result)
    return result


def _older_projection_entries(context,phase):
    """Private pure formatter; all immutable inputs remain byte-pinned."""
    root,manifest=_snapshot(*OLDER[phase])
    by_name={row["name"]:row for row in context.catalog["theorems"]}
    current=_current_metadata(context)
    metadata=[row for row in _all_family_metadata() if row["package"]==OUTPUT_NAMES[phase]]
    portable=_portable_script()
    pins={}
    def output(name,raw):
        if name in pins:
            raise PublicationError("duplicate historical projection output")
        pins[name]={"bytes":len(raw),"sha256":digest(raw)}
        return name,raw
    for family in metadata:
        slug=family["slug"]
        corpus=strict_json(_source(root,manifest,slug+"/api/corpus.json"))
        summaries=frozenset(row["summary"] for row in historical._nodes(corpus) if type(row.get("summary")) is str)
        graphs={}
        for name in manifest["files"]:
            if not name.startswith(slug+"/"):
                continue
            raw=_source(root,manifest,name)
            if name.endswith(".json") and Path(name).name in {"corpus.json","current-corpus.json","graph.json"}:
                revised=_refresh_document(strict_json(raw),by_name,current)
                if type(revised.get("schema")) is str:
                    revised["schema"]=revised["schema"].replace("alpha-v33-","alpha-v34-")
                raw=json_bytes(revised)
                if name.endswith("/api/graph.json"):
                    graphs[name.removesuffix("api/graph.json")+"graph.html"]=revised
            elif name.endswith("api/graph.schema.json"):
                raw=json_bytes(_refresh_schema(strict_json(raw)))
            elif name.endswith(".html"):
                graph=None
                if name.endswith("/graph.html"):
                    graph_name=name.removesuffix("graph.html")+"api/graph.json"
                    if graph_name in manifest["files"]:
                        graph=graphs.get(name)
                        if graph is None:
                            graph=_refresh_document(strict_json(_source(root,manifest,graph_name)),by_name,current)
                            if type(graph.get("schema")) is str:
                                graph["schema"]=graph["schema"].replace("alpha-v33-","alpha-v34-")
                raw=_HistoricalHTML(name,context.revision,graph=graph,portable_script=portable,
                    protected_summaries=summaries).finish(raw)
            yield output(name,raw)
    family_slugs={row["slug"] for row in metadata}
    for name in manifest["files"]:
        if name.split("/",1)[0] in family_slugs or name in {"index.html","publication.json"}:
            continue
        # Literal historical evidence, sources and bundles are never relabeled.
        yield output(name,_source(root,manifest,name))
    prior_name="historical/"+root.name+"/manifest.json"
    yield output(prior_name,read_pinned(root/"manifest.json",OLDER[phase][1],OLDER[phase][2]))
    info={"schema":SCHEMA,"phase":phase,"alpha_edition_version":"v34",
        "alpha_first_enrolled_version":"v31" if phase=="completed" else "v32" if phase=="research" else "v33" if phase=="polynomial" else "mixed_preserved",
        "alpha_edition_checked_use_count":4223,"stable_edition_count":432,
        "families":metadata,"catalog_sha256":context.catalog_sha256,
        "current_G009_multiplicative_closure_proved":True,"current_G091_prime_power_fields_proved":False,
        "proof_verification_provenance":"unchanged_prior_admission_authenticated_by_current_v34_parent; not_a_fresh_replay_of_all_parent_proofs"}
    yield output("publication.json",json_bytes(info))
    raw=_phase_index(phase,metadata,context.revision)
    yield output("index.html",_HistoricalHTML("index.html",context.revision,graph=None,portable_script=portable).finish(raw))
    yield "manifest.json",_publication_manifest(context,phase,pins,metadata,
        alpha_first_enrolled_version=info["alpha_first_enrolled_version"],
        theorem_count=manifest["theorem_count"],checked_use_count=manifest["checked_use_count"],
        stable_count=manifest["stable_count"],historical_parent={"directory":root.name,"bytes":OLDER[phase][1],"sha256":OLDER[phase][2]})


def iter_phase_entries(context, phase):
    require_live(context)
    if phase in OLDER:
        yield from _older_projection_entries(context, phase)
    elif phase == "gcd-congruence":
        from build_constructive_gcd_congruence_explorer_v34 import build_files_from_live
        yield from build_files_from_live(context).items()
    elif phase == "atlas":
        from extend_constructive_research_campaign_v34 import build_files_from_live
        yield from build_files_from_live(context).items()
    else:
        raise PublicationError("unregistered publication phase")
    require_live(context)
