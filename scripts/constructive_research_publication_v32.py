"""Canonical v32 reader projections; only a genuine live release may publish.

All older reader files are byte-pinned presentation inputs, not proof receipts.
Exact current catalogue rows and fresh bundle evidence authenticate admission.
Original statements, scripts, tags, definitions and first admissions survive.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
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
import upgrade_constructive_historical_publication_v31 as historical
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_proof_explorer_template import render_canonical_family_landing


ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION, CURRENT_COUNT, STABLE_COUNT = "v32", 3971, 432
SCHEMA = "peano-lab-alpha-v32-canonical-publication-v1"
PublicationError = publication.PublicationError
digest, json_bytes, strict_json = publication.digest, publication.json_bytes, publication.strict_json
safe_relative, read_pinned = publication.safe_relative, publication.read_pinned
OUTPUT_NAMES = {"research": "constructive-research-explorer-v32",
    "completed": "constructive-completed-lower-explorer-v32",
    "historical": "constructive-historical-explorers-v32",
    "atlas": "constructive-research-campaign-v32"}
LEGACY_DOCUMENTATION_ROUTES = (
    "arithmetic-library/bertrand-campaign.html",
    "arithmetic-library/defined-proof-explorer.html",
    "arithmetic-library/quadratic-reciprocity.html",
)
RESEARCH = (
    ("multiplicative-convolution", "constructive-g009-explorer", 45222,
     "3882fba2f018961d90d8afd1ffbe317ec49e85320b7a0d6adb9e97d48db91f20"),
    ("polynomial-division-prerequisites", "constructive-polynomial-division-explorer", 41433,
     "754c4b665f568fc21ce8f810bda24430199f572a4c3f1edd9e08e633d43b6afe"),
)
OLDER = {
    "completed": ("constructive-completed-lower-explorer-v31", 368715,
                  "3fd1e3ceac74d898800030bb0429198c3ec873a3c67ee41d3c06b07b8dc3f1f8"),
    "historical": ("constructive-historical-explorers-v31", 1496113,
                   "e6805a7a4a09754c4cbaec214b4de6720e6226f609ac4f1a9ad6514cae524372"),
}
ASSET_DIGESTS = {**render.ASSET_DIGESTS,
    "proofs.css": "44ac9983416435ac33efada9eaa3ff914588845fe55932f5e8c54623b28c9285"}
_CURRENT_FIELDS = historical._CURRENT_FIELDS
_MATHEMATICAL_FIELDS = historical._MATHEMATICAL_FIELDS
_AUTHORITY_FIELDS = historical._AUTHORITY_FIELDS
FAMILY_ORDER = historical.FAMILY_ORDER
_RENDER_TOKEN = object()


def _snapshot(directory, size, expected):
    root = ROOT/"book/_static"/directory
    value = strict_json(read_pinned(root/"manifest.json",size,expected))
    files = value.get("files")
    if (type(files) is not dict or len(files) != value.get("file_count_excluding_manifest")
            or not 0 < len(files) <= 20000):
        raise PublicationError("invalid exact source-reader inventory")
    for name,pin in files.items():
        if (not safe_relative(name) or type(pin) is not dict
                or set(pin) != {"bytes","sha256"} or type(pin["bytes"]) is not int
                or not 0 < pin["bytes"] <= 64*1024*1024
                or type(pin["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}",pin["sha256"]) is None):
            raise PublicationError("unsafe source-reader file binding")
    return root,value


def _source(root, manifest, name):
    if name not in manifest["files"]:
        raise PublicationError("unregistered original reader file: " + name)
    pin = manifest["files"][name]
    return read_pinned(root/name,pin["bytes"],pin["sha256"])


def require_live(context):
    from verify_peano_library_channels_v32 import LiveReleaseContext
    if type(context) not in (LiveReleaseContext,BoundPresentation):
        raise PublicationError("only a genuine live v32 release can authorize publication")
    context.require_unchanged()
    rows = context.catalog.get("theorems")
    if (type(rows) is not list or len(rows) != 3971
            or context.catalog.get("checked_use_count") != 3971
            or context.catalog.get("stable_count") != 432
            or context.channels.get("default_channel") != "stable"
            or tuple(row["name"] for row in rows[3796:]) != context.promoted_names
            or set(context.families) != {row[0] for row in RESEARCH}
            or context.revision != context.catalog_sha256[:12]
            or context.channels["channels"]["alpha"]["artifact_sha256"] != context.catalog_sha256):
        raise PublicationError("live publication scope differs from exact v32 admission")


def require_render_inputs():
    from build_constructive_polynomial_division_explorer import _definition_input_paths
    records=[]
    for directory,size,expected in (*OLDER.values(),*(row[1:] for row in RESEARCH)):
        root,manifest=_snapshot(directory,size,expected)
        records.append((directory,size,expected))
        for name,pin in sorted(manifest["files"].items()):
            _source(root,manifest,name)
            records.append((directory+"/"+name,pin["bytes"],pin["sha256"]))
    paths=(Path(__file__),ROOT/"scripts/constructive_alpha_v32_publication_process.py",
        ROOT/"scripts/publish_constructive_research_v32.py",
        ROOT/"peano-lab/py/tests/test_constructive_research_publication_v32.py",
        ROOT/"peano-lab/py/tests/test_constructive_alpha_v32_publication_process.py",
        ROOT/"scripts/constructive_proof_explorer_template.py",
        ROOT/"scripts/constructive_checked_explorer_renderer.py",
        ROOT/"scripts/constructive_frontier_exact_explorer.py",
        ROOT/"scripts/constructive_polynomial_division_definition_graph.py",
        ROOT/"scripts/constructive_polynomial_division_definitions.py",
        ROOT/"scripts/extend_constructive_research_campaign_v32.py",
        ROOT/"peano-lab/py/tests/test_constructive_research_campaign_v32.py",
        ROOT/"scripts/constructive_historical_graph_test_support.py",
        *(ROOT/"peano-lab/py/tests"/name for name in (
            "test_constructive_completed_lower_explorer_v31.py",
            "test_constructive_historical_publication_v31.py",
            "test_constructive_bottom_layer_explorer.py",
            "test_constructive_frontier_explorer.py")),
        ROOT/"scripts/build_constructive_g009_explorer.py",
        ROOT/"scripts/build_constructive_polynomial_division_explorer.py",
        ROOT/"scripts/build_constructive_completed_lower_explorer_v31.py",
        ROOT/"scripts/upgrade_constructive_historical_publication_v31.py",
        ROOT/"scripts/constructive_completed_lower_publication_v31.py",
        ROOT/"scripts/sync_constructive_grand_campaign.py",*_definition_input_paths(),
        ROOT/"scripts/extend_constructive_second_wave_campaign.py",
        *(ROOT/"deploy/proofs"/name for name in LEGACY_DOCUMENTATION_ROUTES),
        *(ROOT/"peano-lab/py/peano_lab/library"/name for name in (
            "defined_syntax.py","defined_edition.py","bertrand_defined_edition.py")))
    from check_alpha_v32_research import _file_digest
    for path in paths:
        relative=path.relative_to(ROOT).as_posix()
        records.append((relative,*_file_digest(relative,4*1024*1024)))
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
    from verify_peano_library_channels_v32 import LiveReleaseContext
    if type(context) is not LiveReleaseContext:
        raise PublicationError("binding presentation requires the original live release capability")
    require_live(context)
    return BoundPresentation(_RENDER_TOKEN,context,require_render_inputs())

def _current_metadata(context):
    return {"alpha_edition_version":"v32","alpha_edition_checked_use_count":3971,
        "alpha_edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "alpha_catalog_sha256":context.catalog_sha256,"catalog_sha256":context.catalog_sha256,
        "edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "navigation_revision":context.revision,"html_revision":context.revision}

def _current_text(text):
    text = re.sub(r"\bAlpha v31(?= (?:checked-use|checked use|independently verified))","Alpha v32",text)
    return (text.replace("Current Alpha: 3,796","Current Alpha: 3,971")
        .replace("Current Alpha has 3,796","Current Alpha has 3,971")
        .replace("current Alpha v31","current Alpha v32")
        .replace("Current Alpha v31","Current Alpha v32")
        .replace("among 3796 checked release theorems","among 3971 checked release theorems")
        .replace("Full G009 still requires multiplicative-function closure;","Full G009 multiplicative-function closure is proved and admitted in Alpha v32;")
        .replace("Full G009 still requires multiplicative-function closure.","Full G009 multiplicative-function closure is now admitted in the separate Alpha-v32 multiplicative-convolution family.")
        .replace("Full G009 multiplicative closure and G091 prime-power fields remain open.","Full G009 multiplicative closure is admitted in Alpha v32; G091 prime-power fields remain open.")
        .replace("Multiplicative-function closure and full G009 remain open.","Multiplicative-function closure and full finite signed G009 are admitted in the separate Alpha-v32 multiplicative-convolution family.")
        .replace("full G009 multiplicative closure remains open","full G009 multiplicative closure is now admitted"))

canonical_bytes = historical.canonical_bytes

def _check_literal_row(node: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    for key in ("name", "statement", "script", "dependencies", "summary", "statement_sha256"):
        if node.get(key) != row.get(key):
            raise PublicationError("the reader differs from its actual admitted theorem: " + str(node.get("name")))
    if (row.get("statement_sha256") != digest(row["statement"])
            or row.get("script_sha256") != digest("\n".join(row["script"]) + "\n")
            or row.get("body_checked") is not True or row.get("checked_use") is not True
            or row.get("membership") != "alpha_only" or row.get("evidence_status") != "alpha_closed"):
        raise PublicationError("the displayed new theorem lacks genuine Alpha checked-use evidence")


def _promote_corpus(original: dict, report: Mapping[str, Any], context: LiveReleaseContext,
                    by_name: Mapping[str, dict], routes: Mapping[str, str]) -> dict:
    """Private pure projection, reached only after the live capability guard."""
    slug = original["family_slug"]
    bundle = report["bundle"]
    owned = report["owned_node_ids"]
    metrics = {row["name"]: row for row in report["rows"]}
    expected_names = tuple(node["name"] for node in original["nodes"])
    principals = report["principal_roots"]
    if (set(owned) != set(expected_names) or set(metrics) != set(expected_names)
            or len(metrics) != len(report["rows"])
            or bundle.get("original_ha_checked") is not True
            or bundle.get("independent_lean_checked") is not True
            or bundle.get("sha256") != original["proof_bundle_sha256"]
            or bundle.get("nodes_including_packaging_root") != original["proof_bundle_node_count"]
            or bundle.get("kernel_calls") != bundle["nodes_including_packaging_root"]
            or not principals or len({row["name"] for row in principals}) != len(principals)
            or any(row.get("complete_ordinary_ha_checked") is not True
                   or type(row.get("ordinary_certificate_nodes")) is not int
                   or not 0 < row["ordinary_certificate_nodes"] <= 500000
                   or row["name"] not in owned or row["node_id"] != owned[row["name"]]
                   or row["statement_sha256"] != by_name[row["name"]]["statement_sha256"]
                   for row in principals)):
        raise PublicationError("the family lacks its exact freshly checked proof and ordinary roots")
    corpus = deepcopy(original)
    status = "Alpha v32 checked-use · first admitted v32 · independently kernel and Lean verified; not Stable"
    for node in corpus["nodes"]:
        row, observed = by_name[node["name"]], metrics[node["name"]]
        _check_literal_row(node, row)
        receipt = row["empty_context_closure"]
        if (receipt.get("status") != "checked" or receipt.get("kernel_mode") != "intuitionistic"
                or receipt.get("certificate_sha256") != bundle["sha256"]
                or receipt.get("bundle_node_id") != owned[node["name"]]
                or node["proof_bundle_node_id"] != owned[node["name"]]
                or observed.get("node_id") != owned[node["name"]]
                or observed.get("statement_sha256") != node["statement_sha256"]
                or observed.get("proof_nodes") != node["body_proof_nodes"]
                or observed.get("proof_depth") != node["body_proof_depth"]
                or receipt.get("body_proof_nodes") != observed["proof_nodes"]
                or receipt.get("body_proof_depth") != observed["proof_depth"]):
            raise PublicationError("a displayed proof node differs from the fresh checked bundle")
        node.update(status=status, enrolled_in_alpha=True, admitted_to_alpha=True,
                    alpha_checked_use=True, checked_use=True, alpha_evidence="alpha_closed",
                    alpha_edition_version=CURRENT_VERSION, alpha_first_enrolled_version=CURRENT_VERSION,
                    stable_member=False, admitted_to_stable=False)
    for external in corpus["external_dependencies"]:
        row = by_name.get(external["name"])
        if (row is None or row.get("checked_use") is not True or row.get("body_checked") is not True
                or external.get("statement") != row["statement"]
                or external.get("statement_sha256") != row["statement_sha256"]):
            raise PublicationError("an external reader prerequisite differs from the current checked theorem")
        external["historical_inventory_role"] = external.get("inventory_role")
        external.update(inventory_role="current_alpha_checked_prerequisite", evidence=row["evidence_status"],
                        alpha_evidence=row["evidence_status"], enrolled_in_alpha=True,
                        admitted_to_alpha=True, alpha_checked_use=True, checked_use=True,
                        alpha_edition_version=CURRENT_VERSION, stable_member=row["membership"] == "stable",
                        admitted_to_stable=row["membership"] == "stable")
    corpus["historical_checkpoint_report"] = corpus.pop("checkpoint_report")
    corpus["historical_goal_scope"] = corpus["campaign_goal_scope"]
    corpus.update(
        schema=SCHEMA, publication_scope="alpha_checked_use_publication", candidate_status=status,
        enrolled_in_alpha=True, admitted_to_alpha=True, alpha_checked_use=True, checked_use=True,
        stable_member=False, admitted_to_stable=False, alpha_enrolled_node_count=len(expected_names),
        alpha_checked_use_node_count=len(expected_names), stable_admitted_node_count=0,
        alpha_edition_version=CURRENT_VERSION, alpha_first_enrolled_version=CURRENT_VERSION,
        alpha_catalog_sha256=context.catalog_sha256,
        alpha_first_enrollment_catalog_sha256=context.catalog_sha256,
        alpha_edition_identity_sha256=context.catalog["edition_identity_sha256"],
        alpha_edition_checked_use_count=CURRENT_COUNT, navigation_revision=context.revision,
        alpha_proof_bundle_sha256=bundle["sha256"], first_alpha_admission_report=deepcopy(report),
        external_theorem_routes={name: route for name, route in routes.items() if name not in corpus["tags"]},
        render_evidence_provenance="actual_same_live_v32_release_verifier_capability",
        release_source_binding_sha256=context.source_binding_sha256,
    )
    corpus["first_admitted_version"] = "v32"
    corpus["alpha_evidence"] = "alpha_closed"
    corpus["current_G009_multiplicative_closure_proved"] = True
    corpus["current_G091_prime_power_fields_proved"] = False
    if slug == "multiplicative-convolution":
        corpus["campaign_goal_scope"] = "full_G009_finite_signed_multiplicative_convolution_alpha_closed"
    elif slug == "polynomial-division-prerequisites":
        corpus["campaign_goal_scope"] = "polynomial_division_prerequisites_alpha_closed_full_G091_open"
    else:
        raise PublicationError("unregistered newly admitted family")
    return corpus

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
    for key in ("nodes", "theorems"):
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
            self.parts.append('<p class="pa-callout pd-callout" data-current-release="v32">Current library: Alpha v32, 3,971 checked-use theorems; Stable remains 432. Historical first admissions, original proof editions, and non-admitted aliases are preserved.' + first_link + '</p>')
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
            self.parts.append('<meta name="proof-publication-scope" content="alpha-v32-historical-first-admission-preserved">')
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


def _all_family_metadata():
    result=[]
    for phase,(directory,size,expected) in OLDER.items():
        root,manifest=_snapshot(directory,size,expected)
        for item in manifest["families"]:
            current={**item,"package":OUTPUT_NAMES[phase]}
            if phase=="completed":
                # This pinned tranche has574/574 checked rows and no Stable rows.
                current.update(checked_use_count=item["theorem_count"],stable_count=0,
                               first_admitted_version="v31")
            result.append(current)
    for slug,directory,size,expected in RESEARCH:
        root,manifest=_snapshot(directory,size,expected)
        corpus=strict_json(_source(root,manifest,slug+"/api/corpus.json"))
        result.append({"slug":slug,"title":corpus["family_title"],"theorem_count":len(corpus["nodes"]),
            "checked_use_count":len(corpus["nodes"]),"stable_count":0,"first_admitted_version":"v32",
            "tags":corpus["tags"],"package":OUTPUT_NAMES["research"]})
    if len(result)!=65 or len({row["slug"] for row in result})!=65:
        raise PublicationError("the exact 65-family inventory changed")
    return tuple(result)


def _routes():
    routes={}
    for directory,size,expected in (*OLDER.values(),*(row[1:] for row in RESEARCH)):
        root,manifest=_snapshot(directory,size,expected)
        for name in manifest["files"]:
            if name.count("/")==2 and name.endswith("/api/corpus.json"):
                corpus=strict_json(_source(root,manifest,name))
                slug=name.split("/",1)[0]
                for node in historical._nodes(corpus):
                    tag=node.get("id",node.get("tag"))
                    theorem=node.get("name")
                    if (node.get("kind")!="definition" and type(theorem) is str and type(tag) is str
                            and re.fullmatch(r"[A-Z]+[0-9A-F]{4}",tag)):
                        exact=slug+"/explorer/defined/tag/"+tag+".html"
                        if exact in manifest["files"]:
                            routes.setdefault(theorem,exact)
    return routes


def _portable_script():
    packages={row["slug"]:row["package"] for row in _all_family_metadata()}
    from build_constructive_completed_lower_explorer_v31 import _portable_script as original
    raw=original(packages)
    raw=raw.replace(json.dumps(["/"+publication.OUTPUT_NAME+"/","/"+publication.HISTORICAL_OUTPUT_NAME+"/"]),
        json.dumps(["/"+name+"/" for name in OUTPUT_NAMES.values()]))
    return raw.replace("/"+publication.ATLAS_NAME+"/index.html","/"+OUTPUT_NAMES["atlas"]+"/index.html")


def _assets():
    _slug,directory,size,expected=RESEARCH[0]
    root,manifest=_snapshot(directory,size,expected)
    for name,expected_hash in ASSET_DIGESTS.items():
        raw=_source(root,manifest,"assets/"+name)
        if digest(raw)!=expected_hash:
            raise PublicationError("canonical QR asset changed: "+name)
        yield "assets/"+name,raw


def _family_models():
    from build_constructive_g009_explorer import family as g009
    from build_constructive_polynomial_division_explorer import family as polynomial
    result=[]
    for factory in (g009,polynomial):
        item=factory()
        caveat=item.caveat
        for sentence in ("This local research checkpoint performs no Alpha or Stable admission.",
                         "This is a local research checkpoint, not an Alpha or Stable admission."):
            caveat=caveat.replace(sentence,"")
        caveat=caveat.strip()+" These exact theorems are first admitted to Alpha v32; Stable remains unchanged."
        result.append(replace(item,caveat=caveat))
    return tuple(result)


def _dashboard_enhancement():
    """Copy the literal, already-reviewed local three-filter extension."""
    slug,directory,size,expected=RESEARCH[1]
    root,manifest=_snapshot(directory,size,expected)
    raw=_source(root,manifest,slug+"/explorer/defined/index.html").decode("utf-8")
    matches=re.findall(r'<script\b[^>]*\bdata-local-dashboard-enhancement(?:="[^"]*")?[^>]*>.*?</script>',raw,re.S)
    if len(matches)!=1:
        raise PublicationError("the exact local dashboard extension is missing or ambiguous")
    return matches[0]


def _checkpoint_page(family,corpus,report,revision):
    bundle=report["bundle"]
    rows=[]
    for node in (*corpus["nodes"],*corpus["external_dependencies"]):
        rows.append('<li id="theorem-'+escape(node["name"],quote=True)+'"><code>'+escape(node["name"])
            +'</code><details><summary>Exact checked statement</summary><pre><code>'+escape(node["statement"])
            +'</code></pre></details></li>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>'+escape(family.title)+' — exact admission evidence</title><link rel="stylesheet" href="../assets/proofs.css"></head>'
        '<body class="family-page"><header class="family-hero"><div class="shell"><nav class="crumbs"><a href="./?v='+revision+'">Proof family</a>'
        '<a href="../grand-campaign/?v='+revision+'">Grand campaign</a></nav><h1>'+escape(family.title)+' — exact evidence</h1>'
        '<p class="lede">Current Alpha v32 checked use; first admitted v32; not Stable. The complete artifact was freshly checked in original HA and independently compiled Lean.</p>'
        '</div></header><main class="shell family-main"><section class="release-note"><p>'+str(bundle["nodes_including_packaging_root"])
        +' checked bundle nodes; '+str(bundle["dependency_edges_including_packaging"])+ ' dependency edges.</p><p>'
        '<a href="../artifacts/'+escape(Path(bundle["path"]).name,quote=True)+'">Literal checked proof bundle</a> · SHA-256 <code>'
        +bundle["sha256"]+'</code></p><p>Full G009 is admitted. Full G091 remains open; polynomial prerequisites do not prove arbitrary prime-power fields.</p></section>'
        '<section><h2>Exact theorem nodes and inherited prerequisites</h2><ul>'+''.join(rows)+'</ul></section></main></body></html>').encode()


def _render_family(family, corpus: dict, report: Mapping[str, Any], revision: str) -> dict[str, bytes]:
    base = family.slug + "/"
    graph = render._graph_payload(family, corpus, revision=revision)
    files = {
        base + "index.html": render_canonical_family_landing(
            family, corpus, revision=revision, current_alpha_version="v32", first_admitted_version="v32",
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


def _phase_index(phase,metadata,revision):
    cards="".join('<article class="family-card"><h2>'+escape(row["title"])+'</h2><p>'
        +str(row["checked_use_count"])+' checked-use records.</p><a class="primary-action" href="'
        +escape(_navigation_href(row["slug"]+"/",revision),quote=True)+'">Explore the proof map</a></article>'
        for row in metadata)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Constructive proof families — Alpha v32</title><link rel="stylesheet" href="assets/proofs.css"></head>'
        '<body><header class="hero"><div class="shell"><p class="eyebrow">Alpha v32 · Stable 432 unchanged</p>'
        '<h1>'+escape(phase.title())+' proof families</h1><p class="lede">Current Alpha has 3,971 checked-use entries. '
        'Original first admissions and exact proofs are preserved.</p></div></header><main class="shell"><section class="family-grid">'
        +cards+'</section><section class="release-note">Full finite signed G009 is admitted; G091 prime-power fields remain open.</section></main></body></html>').encode()

def _publication_manifest(context,phase,pins,metadata,**extra):
    return json_bytes({"schema":SCHEMA+"-manifest","publication_scope":"alpha_checked_use_publication",
        "alpha_edition_version":"v32","alpha_edition_checked_use_count":3971,"stable_edition_count":432,
        "catalog_sha256":context.catalog_sha256,"edition_identity_sha256":context.catalog["edition_identity_sha256"],
        "html_revision":context.revision,"families":list(metadata),"phase":phase,
        "file_count_excluding_manifest":len(pins),"files":dict(sorted(pins.items())),
        "release_source_binding_sha256":context.source_binding_sha256,
        "render_source_binding_sha256":context.render_source_binding_sha256,
        "current_G009_multiplicative_closure_proved":True,"current_G091_prime_power_fields_proved":False,**extra})

def _research_projection_entries(context):
    """Private pure formatter; its output alone confers no proof authority."""
    routes=_routes()
    by_name={row["name"]:row for row in context.catalog["theorems"]}
    models={row.slug:row for row in _family_models()}
    metadata=[row for row in _all_family_metadata() if row["package"]==OUTPUT_NAMES["research"]]
    pins={}
    portable=_portable_script()
    dashboard=_dashboard_enhancement()
    from build_constructive_completed_lower_explorer_v31 import _CurrentHTML, _definition_and_statement_identity
    def output(name,raw):
        if name in pins:
            if pins[name]!={"bytes":len(raw),"sha256":digest(raw)}:
                raise PublicationError("conflicting shared research output")
            return None
        pins[name]={"bytes":len(raw),"sha256":digest(raw)}
        return name,raw
    for name,raw in _assets():
        yield output(name,raw)
    for slug,directory,size,expected in RESEARCH:
        root,manifest=_snapshot(directory,size,expected)
        original=strict_json(_source(root,manifest,slug+"/api/corpus.json"))
        report=context.families[slug]
        family_routes=dict(routes)
        for external in original["external_dependencies"]:
            family_routes.setdefault(external["name"],slug+"/checkpoint.html#theorem-"+external["name"])
        corpus=_promote_corpus(original,report,context,by_name,family_routes)
        _definition_and_statement_identity(original,corpus)
        files=_render_family(models[slug],corpus,report,context.revision)
        graph=strict_json(files[slug+"/api/graph.json"])
        for name,raw in files.items():
            if name.endswith(".html"):
                is_dashboard=name.endswith("/explorer/defined/index.html")
                layers=tuple(sorted(set(corpus["layers"].values())|{row["topological_layer"] for row in corpus["definitions"]})) if is_dashboard else None
                raw=_CurrentHTML(name,context.revision,portable_script=dashboard if is_dashboard else "",layer_choices=layers).finish(raw)
                raw=_HistoricalHTML(name,context.revision,graph=graph if name.endswith("/defined/graph.html") else None,
                    portable_script=portable,protected_summaries=frozenset(node["summary"] for node in corpus["nodes"])).finish(raw)
            yield output(name,raw)
        bundle=report["bundle"]
        yield output("artifacts/"+Path(bundle["path"]).name,read_pinned(ROOT/bundle["path"],bundle["bytes"],bundle["sha256"]))
        yield output("historical/"+directory+"/manifest.json",read_pinned(root/"manifest.json",size,expected))
        for name in manifest["files"]:
            if name.startswith("sources/"):
                raw=_source(root,manifest,name)
                pair=output(name,raw)
                if pair is not None: yield pair
                yield output("historical/"+directory+"/"+name,raw)
            elif name in {"checkpoints.json","proof-audit.json"}:
                yield output("historical/"+directory+"/"+name,_source(root,manifest,name))
    raw=_phase_index("research",metadata,context.revision)
    raw=_HistoricalHTML("index.html",context.revision,graph=None,portable_script=portable).finish(raw)
    yield output("index.html",raw)
    yield "manifest.json",_publication_manifest(context,"research",pins,metadata,
        alpha_first_enrolled_version="v32",theorem_count=175,checked_use_count=175,stable_count=0)


def _refresh_schema(value):
    result=deepcopy(value)
    def visit(node):
        if type(node) is dict:
            fields=node.get("properties")
            if type(fields) is dict and "alpha_edition_version" in fields:
                field=fields["alpha_edition_version"]
                if "const" in field:
                    if type(field["const"]) is not str or field["const"]!="v31":
                        raise PublicationError("unreviewed historical edition constraint")
                    field["const"]="v32"
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
                    revised["schema"]=revised["schema"].replace("alpha-v31-","alpha-v32-")
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
                                graph["schema"]=graph["schema"].replace("alpha-v31-","alpha-v32-")
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
    info={"schema":SCHEMA,"phase":phase,"alpha_edition_version":"v32",
        "alpha_first_enrolled_version":"v31" if phase=="completed" else "mixed_preserved",
        "alpha_edition_checked_use_count":3971,"stable_edition_count":432,
        "families":metadata,"catalog_sha256":context.catalog_sha256,
        "current_G009_multiplicative_closure_proved":True,"current_G091_prime_power_fields_proved":False,
        "proof_verification_provenance":"unchanged_prior_admission_authenticated_by_current_v32_parent; not_a_fresh_replay_of_all_parent_proofs"}
    yield output("publication.json",json_bytes(info))
    raw=_phase_index(phase,metadata,context.revision)
    yield output("index.html",_HistoricalHTML("index.html",context.revision,graph=None,portable_script=portable).finish(raw))
    yield "manifest.json",_publication_manifest(context,phase,pins,metadata,
        alpha_first_enrolled_version=info["alpha_first_enrolled_version"],
        theorem_count=manifest["theorem_count"],checked_use_count=manifest["checked_use_count"],
        stable_count=manifest["stable_count"],historical_parent={"directory":root.name,"bytes":OLDER[phase][1],"sha256":OLDER[phase][2]})


def iter_phase_entries(context,phase):
    require_live(context)
    if phase=="research":
        yield from _research_projection_entries(context)
    elif phase in OLDER:
        yield from _older_projection_entries(context,phase)
    elif phase=="atlas":
        from extend_constructive_research_campaign_v32 import build_files_from_live
        yield from build_files_from_live(context).items()
    else:
        raise PublicationError("unregistered publication phase")
    require_live(context)
