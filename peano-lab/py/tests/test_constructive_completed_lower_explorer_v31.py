"""Exact v31 readers and hostile-SVG JavaScript in two explicit test modes.

Publication always supplies its genuine live capability and private fresh
files. Ordinary pytest inspects the actual published files through a read-only,
non-authorizing view: that mode checks UI consistency, never fresh HA or Lean.
An invalid live plugin cannot fall back to the static mode.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_completed_lower_publication_v31 as publication
import build_constructive_completed_lower_explorer_v31 as builder
from constructive_dirichlet_inverse_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names


SLUGS = publication.FAMILY_ORDER
DRIVER_PINS = {
    "test_constructive_bottom_layer_explorer.py": "8638006e9d71da804b9dc9b226af48fdd4507ae82b5597fbf9add5a904dddbb9",
    "test_constructive_frontier_explorer.py": "9692861c8354409ad114e0537b98e71811e8bfd31c1ea3fe345a9b3e1ae57792",
}


class FileTree(Mapping):
    """Read literal private page bytes lazily; never decode proof authority."""
    def __init__(self, directory, pins):
        self.directory, self.pins = Path(directory), pins
    def __len__(self):
        return len(self.pins)
    def __iter__(self):
        return iter(self.pins)
    def __getitem__(self, path):
        pin = self.pins[path]
        return publication.read_pinned(self.directory / path, pin["bytes"], pin["sha256"])


def _immutable_error(*args, **kwargs):
    raise TypeError("published UI observations are read-only, not proof authority")


class _ReadOnlyDict(dict):
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable_error
    def __deepcopy__(self, memo):
        return {deepcopy(key, memo): deepcopy(value, memo) for key, value in self.items()}


class _ReadOnlyList(list):
    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = reverse = sort = __iadd__ = __imul__ = _immutable_error
    def __deepcopy__(self, memo):
        return [deepcopy(value, memo) for value in self]


def _readonly(value):
    if type(value) is dict:
        return _ReadOnlyDict((key, _readonly(item)) for key, item in value.items())
    if type(value) is list:
        return _ReadOnlyList(_readonly(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class PublishedReleaseView:
    """Test-only observations; deliberately no live token or require_unchanged."""
    catalog: Mapping
    channels: Mapping
    families: Mapping
    catalog_sha256: str
    revision: str
    promoted_names: tuple[str, ...]
    source_binding_sha256: str


def _observed_bytes(path):
    """Bounded ordinary bytes; a computed hash is identity, not proof evidence."""
    size = path.stat().st_size
    assert 0 < size <= 64 * 1024 * 1024
    with path.open("rb") as stream:
        raw = stream.read(size + 1)
    assert len(raw) == size
    return publication.read_pinned(path, size, sha256(raw).hexdigest())


def _published_input(pytestconfig, phase):
    from peano_catalog_shards import load_catalog

    context = getattr(pytestconfig, "_alpha_v31_static_observations", None)
    if context is None:
        catalog_path = ROOT / "artifacts/peano-library/alpha/catalog-v31.json"
        catalog_hash = sha256(_observed_bytes(catalog_path)).hexdigest()
        catalog = load_catalog(catalog_path, expected_sha256=catalog_hash)
        channels = publication.strict_json(_observed_bytes(ROOT / "artifacts/peano-library/channels-v31.json"))
        assert catalog["theorem_count"] == catalog["checked_use_count"] == 3796
        assert catalog["stable_count"] == 432 and channels["default_channel"] == "stable"
        assert channels["channels"]["alpha"]["artifact_sha256"] == catalog_hash
        receipt_path = "research/arithmetic-library/artifacts/alpha-v31-completed-lower-receipt-v1.json"
        documents = {row["path"]: row for row in catalog["evidence_documents"]}
        pin = documents[receipt_path]
        receipt = publication.strict_json(publication.read_pinned(ROOT / receipt_path, pin["bytes"], pin["sha256"]))
        families = {row["slug"]: row for row in receipt["families"]}
        assert tuple(families) == SLUGS and len(receipt["families"]) == 19
        assert receipt["new_theorems"] == 574 and receipt["alpha_theorem_count"] == 3796
        context = PublishedReleaseView(_readonly(catalog), _readonly(channels), _readonly(families),
                                       catalog_hash, catalog_hash[:12],
                                       tuple(row["name"] for row in catalog["theorems"][3222:]),
                                       receipt["source_binding_sha256"])
        pytestconfig._alpha_v31_static_observations = context
    assert type(context) is PublishedReleaseView and not hasattr(context, "require_unchanged")
    directory = ROOT / "book/_static" / {
        "completed": "constructive-completed-lower-explorer-v31",
        "historical": "constructive-historical-explorers-v31",
        "atlas": "constructive-completed-lower-campaign-v31",
    }[phase]
    if phase == "atlas":
        pins = {}
        for name in ("campaign.json", "definitions.json", "index.html", "dag-audit.json"):
            raw = _observed_bytes(directory / name)
            pins[name] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    else:
        raw = _observed_bytes(directory / "manifest.json")
        manifest = publication.strict_json(raw)
        assert manifest["catalog_sha256"] == context.catalog_sha256
        pins = dict(manifest["files"])
        assert "manifest.json" not in pins
        pins["manifest.json"] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    actual_paths = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
    assert actual_paths == set(pins)
    inventory = {"files": pins, "file_count": len(pins),
                 "html_count": sum(name.endswith(".html") for name in pins),
                 "total_bytes": sum(pin["bytes"] for pin in pins.values())}
    return {"phase": phase, "context": context, "directory": directory, "inventory": inventory,
            "test_evidence_mode": "static_published_ui_only_no_fresh_proof_claim"}


def live_input(pytestconfig, phase):
    if not hasattr(pytestconfig, "_alpha_v31_publication"):
        return _published_input(pytestconfig, phase)
    supplied = pytestconfig._alpha_v31_publication
    assert type(supplied) is dict, "an invalid live plugin cannot use static observations"
    assert supplied["phase"] == phase
    publication.require_live(supplied["context"])
    return supplied


def test_published_release_view_cannot_authorize_any_public_builder():
    import upgrade_constructive_historical_publication_v31 as historical
    import extend_constructive_completed_lower_campaign_v31 as atlas
    view = PublishedReleaseView(_readonly({}), _readonly({}), _readonly({}), "0" * 64, "0" * 12, (), "0" * 64)
    assert not hasattr(view, "require_unchanged")
    with pytest.raises(TypeError):
        view.catalog["theorems"] = []
    for action in (publication.require_live, builder.build_files_from_live,
                   historical.build_files_from_live, atlas.build_files_from_live):
        with pytest.raises(publication.PublicationError):
            action(view)
    with pytest.raises(AssertionError, match="invalid live plugin"):
        live_input(SimpleNamespace(_alpha_v31_publication=None), "completed")


def drivers():
    """Reuse literal audited canonical DOM harnesses, not another graph engine."""
    for filename, expected in DRIVER_PINS.items():
        assert sha256((ROOT / "peano-lab/py/tests" / filename).read_bytes()).hexdigest() == expected
    path = ROOT / "peano-lab/py/tests/test_constructive_bottom_layer_explorer.py"
    names = {"Document", "_strict_json", "_graph_runtime", "_landing_structure",
             "test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters",
             "test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes"}
    selected = [node for node in ast.parse(path.read_text()).body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected} == names
    for node in selected:
        node.decorator_list = []
    namespace = {
        "ROOT": ROOT, "ast": ast, "json": json, "HTMLParser": HTMLParser, "Path": Path,
        "subprocess": subprocess, "SimpleNamespace": SimpleNamespace,
        "builder": SimpleNamespace(ASSET_SOURCES={name: ROOT / "book/_static/constructive-bottom-layer-explorer/assets" / name
                                                 for name in builder.ASSET_DIGESTS}),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


@pytest.fixture(scope="module")
def actual(pytestconfig):
    return live_input(pytestconfig, "completed")


@pytest.fixture(scope="module")
def files(actual):
    return FileTree(actual["directory"], actual["inventory"]["files"])


@pytest.fixture(scope="module")
def corpora(files):
    return {slug: publication.strict_json(files[slug + "/api/corpus.json"]) for slug in SLUGS}


@pytest.fixture(scope="module")
def original():
    return publication.frozen_corpora(publication.authenticate_snapshots())


@pytest.fixture(scope="module")
def runtime():
    return drivers()


def test_live_exact_574_promotions_with_separate_current_and_first_authority(actual, files, corpora):
    context = actual["context"]
    assert sum(row["node_count"] for row in corpora.values()) == len(context.promoted_names) == 574
    assert Counter(node["name"] for corpus in corpora.values() for node in corpus["nodes"]) == Counter(context.promoted_names)
    assert {slug: corpus["node_count"] for slug, corpus in corpora.items()} == publication.FAMILY_COUNTS
    inventory = publication.strict_json(files["publication.json"])
    assert inventory["alpha_edition_version"] == inventory["alpha_first_enrolled_version"] == "v31"
    assert inventory["alpha_checked_use_count"] == 3796 and inventory["stable_count"] == 432
    assert inventory["full_G007_finite_signed_mobius_inversion_proved"] is True
    assert inventory["full_G014_euler_units_proved"] is True
    assert inventory["general_finite_signed_inverse_criterion_proved"] is True
    assert inventory["full_G009_multiplicative_closure_proved"] is False
    assert inventory["full_G091_prime_power_fields_proved"] is False
    assert inventory["source_binding_sha256"] == context.source_binding_sha256
    assert inventory["definitions"]["definition_count"] == 372
    assert inventory["definitions"]["definition_dependency_count"] == 787
    assert corpora["dirichlet-inverses"]["tags"][corpora["dirichlet-inverses"]["root_names"][-1]] == "IV0013"
    assert "EU0003" not in corpora["euler-units"]["tags"].values()
    assert "EU001C" not in corpora["euler-units"]["tags"].values()


@pytest.mark.parametrize("slug", SLUGS)
def test_live_every_exact_statement_script_definition_and_actual_bundle_identity(slug, actual, files, corpora, original):
    context, corpus, old = actual["context"], corpora[slug], original[slug]
    rows = {row["name"]: row for row in context.catalog["theorems"]}
    report = context.families[slug]
    assert publication.strict_json(files[slug + "/api/checkpoint.json"]) == report == corpus["first_alpha_admission_report"]
    bundle = report["bundle"]
    raw = files["artifacts/" + Path(bundle["path"]).name]
    assert len(raw) == bundle["bytes"] and sha256(raw).hexdigest() == bundle["sha256"]
    assert raw == (ROOT / bundle["path"]).read_bytes()
    assert bundle["original_ha_checked"] is bundle["independent_lean_checked"] is True
    assert bundle["kernel_calls"] == bundle["nodes_including_packaging_root"]
    assert all(row["complete_ordinary_ha_checked"] is True for row in report["principal_roots"])
    builder._definition_and_statement_identity(old, corpus)
    assert corpus["historical_checkpoint_report"] == old["checkpoint_report"]
    assert corpus["alpha_catalog_sha256"] == corpus["alpha_first_enrollment_catalog_sha256"] == context.catalog_sha256
    for node in corpus["nodes"]:
        publication._check_literal_row(node, rows[node["name"]])
        assert node["alpha_checked_use"] is node["checked_use"] is node["admitted_to_alpha"] is True
        assert node["stable_member"] is node["admitted_to_stable"] is False
        assert node["alpha_edition_version"] == node["alpha_first_enrolled_version"] == "v31"
        assert node["proof_bundle_node_id"] == report["owned_node_ids"][node["name"]]
        parser = _LocalDefinedParser(node["defined"]["defined_statement"], DEFINITIONS)
        assert parser.parse() == parse_formula_with_names(node["statement"])[0] and not parser.free
    assert corpus["definitions"] == old["definitions"]
    graph = publication.strict_json(files[slug + "/api/graph.json"])
    assert graph["edges"] == old["edges"]
    assert {edge["kind"] for edge in graph["edges"]} <= {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["alpha_checked_use_node_count"] == corpus["node_count"]
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            assert node["alpha_checked_use"] is True and node["stable_member"] is False
            assert node["alpha_first_enrolled_version"] == "v31"


@pytest.mark.parametrize("slug", SLUGS)
def test_live_canonical_qr_structure_all_theorem_definition_routes_and_fragments(slug, files, corpora, runtime):
    corpus = corpora[slug]
    reference = ROOT / "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html"
    assert runtime["_landing_structure"](files[slug + "/index.html"]) == runtime["_landing_structure"](reference.read_bytes())
    landing = runtime["Document"](files[slug + "/index.html"])
    assert any(attrs.get("rel") == "canonical" for _, attrs in landing.tags)
    assert not any(attrs.get("name") == "robots" and attrs.get("content") == "noindex" for _, attrs in landing.tags)
    assert sum("view-card" in attrs.get("class", "").split() for _, attrs in landing.tags) == 3
    for node in corpus["nodes"]:
        for prefix in ("explorer/tag/", "explorer/defined/tag/"):
            document = runtime["Document"](files[slug + "/" + prefix + node["id"] + ".html"])
            lines = [attrs["id"] for _, attrs in document.tags if "pd-proof-line" in attrs.get("class", "").split()
                     or "pa-proof-line" in attrs.get("class", "").split()]
            assert lines == [f"proof-line-{i:04d}" for i in range(1, len(node["script"]) + 1)]
            assert node["statement"] in document.codes
    for definition in corpus["definitions"]:
        assert slug + "/explorer/defined/definition/" + definition["id"] + ".html" in files


@pytest.mark.parametrize("slug", SLUGS)
@pytest.mark.parametrize("focus_kind", ("theorem", "definition"))
def test_live_actual_canonical_svg_graph_supports_getter_only_href(slug, focus_kind, files, runtime):
    graph = publication.strict_json(files[slug + "/api/graph.json"])
    target = graph["root_ids"][-1]
    focus = target if focus_kind == "theorem" else next(row["id"] for row in graph["nodes"] if row["kind"] == "definition")
    actual = runtime["_graph_runtime"](graph, target, focus, complete_family=True, visible_definitions=True)
    assert actual["svgHrefIsGetterOnly"] is actual["allSvgHrefsAreGetterOnly"] is actual["viewportRendered"] is True
    assert actual["selectedNodeIds"] == [focus]
    assert actual["sidebarHref"] == next(row["href"] for row in graph["nodes"] if row["id"] == focus)
    assert {row["id"] for row in graph["nodes"] if row["kind"] == "theorem"} <= set(actual["renderedNodeIds"])


@pytest.mark.parametrize("slug", SLUGS)
def test_live_actual_three_filter_dashboard_and_hash_highlighting(slug, files, corpora, runtime):
    family = next(row for row in publication.family_models() if row.slug == slug)
    runtime["test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters"](family, "loading", True, files, corpora)
    runtime["test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters"](family, "complete", False, files, corpora)
    runtime["test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes"](family, files, corpora)


def test_live_all_inline_js_parses_and_mixed_graph_json_is_exact(files, runtime):
    scripts, graphs = [], 0
    for name in files:
        if not name.endswith(".html"):
            continue
        for attrs, source in runtime["Document"](files[name]).scripts:
            if attrs.get("type", "").lower() in {"application/json", "application/ld+json"}:
                publication.strict_json(source)
            elif "src" not in attrs:
                scripts.append({"name": name, "source": source})
            if attrs.get("id") == "pa-defined-graph-data":
                assert source.startswith("window.PA_DEFINED_GRAPH=") and source.endswith(";")
                assert publication.strict_json(source[len("window.PA_DEFINED_GRAPH="):-1]) == publication.strict_json(files[name.replace("graph.html", "api/graph.json")])
                graphs += 1
    program = 'const vm=require("node:vm"),r=JSON.parse(require("node:fs").readFileSync(0,"utf8"));r.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(r.length));'
    result = subprocess.run(["node", "-e", program], input=json.dumps(scripts), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(scripts) and graphs == 19


def test_live_exact_graph_navigation_uses_only_the_existing_defined_link(files, runtime):
    cases = []
    for name in files:
        if "/explorer/" not in name or "/defined/" in name or not name.endswith(".html"):
            continue
        document = runtime["Document"](files[name])
        links = [attrs["href"] for tag, attrs in document.header_tags if tag == "a" and "data-graph-navigation" in attrs]
        assert len(links) == 1 and "defined/graph.html" in links[0]
        page = next(attrs["data-page"] for tag, attrs in document.tags if tag == "body")
        cases.append({"name": name, "page": page, "href": links[0]})
    source = files["assets/exact-explorer.js"].decode()
    start = source.index("  function initializeGraphNavigation()"); end = source.index("\n  function ", start + 1)
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
input.cases.forEach(row=>{const anchor={getAttribute(){return row.href;}};const header={querySelector(s){if(s==="[data-graph-navigation]")return anchor;throw Error(s);}};
const document={body:{dataset:{page:row.page}},querySelector(s){if(s===".pa-proof-header")return header;throw Error(s);},createElement(){throw Error("bad graph injection: "+row.name);}};
vm.runInNewContext(input.source+"\\ninitializeGraphNavigation();",{document});});process.stdout.write(String(input.cases.length));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"source": source[start:end], "cases": cases}), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(cases) == 574 + 19


def test_live_all_navigation_and_fragments_use_real_current_or_frozen_routes(files, actual, runtime):
    import upgrade_constructive_historical_publication_v31 as historical
    old_paths = {}
    for item in historical.SNAPSHOTS:
        source = historical.source_manifest(item)
        for pin in source["files"]:
            name = pin["path"]
            if item.flagship:
                destination = item.slugs[0] + "/explorer/" + ("defined/" if item.defined else "") + name
            elif name.split("/", 1)[0] in item.slugs:
                destination = name
            else:
                continue
            old_paths[destination] = ROOT / "book/_static" / item.directory / name
    ids, cross, atlas = {}, 0, 0
    for name in files:
        if not name.endswith(".html"):
            continue
        document = runtime["Document"](files[name])
        assert len(document.ids) == len(set(document.ids)), name
        ids[name] = set(document.ids)
        for tag, attrs in document.tags:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                url = urlsplit(attrs[key])
                if url.scheme or url.netloc:
                    assert url.scheme == "https" and url.netloc == "bnaskrecki.faculty.wmi.amu.edu.pl", (name, attrs[key])
                    continue
                assert not url.path.startswith("/"), (name, attrs[key])
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
                if url.path.endswith("/"):
                    target = posixpath.normpath(target + "/index.html")
                if target == "grand-campaign/index.html":
                    assert not url.fragment
                    atlas += 1
                elif target in files:
                    if url.fragment:
                        if target not in ids:
                            ids[target] = set(runtime["Document"](files[target]).ids)
                        assert unquote(url.fragment) in ids[target], (name, attrs[key])
                else:
                    assert target in old_paths, (name, attrs[key], target)
                    if url.fragment:
                        if target not in ids:
                            ids[target] = set(runtime["Document"](old_paths[target].read_bytes()).ids)
                        assert unquote(url.fragment) in ids[target], (name, attrs[key])
                    cross += 1
                if url.path:
                    filename = Path(url.path).name
                    expected = (builder.ASSET_DIGESTS[filename][:12]
                                if tag in {"script", "link"} and filename in builder.render.ASSET_DIGESTS
                                else actual["context"].revision)
                    assert parse_qs(url.query).get("v") == [expected], (name, attrs[key])
    assert cross > 0 and atlas > 0


def test_live_portable_links_route_all63_families_without_assigning_href(files):
    import upgrade_constructive_historical_publication_v31 as historical
    packages = {**{slug: publication.HISTORICAL_OUTPUT_NAME for slug in historical.FAMILY_ORDER},
                **{slug: publication.OUTPUT_NAME for slug in SLUGS}}
    script = builder._portable_script(packages).removeprefix("<script>").removesuffix("</script>\n")
    paths = ["../../" + slug + "/explorer/defined/?v=123456789abc#proof-line-0001" for slug in packages]
    paths.append("../../grand-campaign/?view=goal&focus=G007&v=123456789abc")
    code = '''const vm=require("node:vm"),i=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const links=i.paths.map(value=>({value,getAttribute(){return this.value;},setAttribute(k,v){if(k!=="href")throw Error(k);this.value=v;},get href(){return this.value;},set href(x){throw Error("read-only href");}}));
const location=new URL("file:///repo/book/_static/constructive-completed-lower-explorer-v31/euler-units/explorer/index.html");
vm.runInNewContext(i.source,{URL,location,document:{querySelectorAll(s){if(s!=="a[href]")throw Error(s);return links;}}});process.stdout.write(JSON.stringify(links.map(x=>x.value)));'''
    result = subprocess.run(["node", "-e", code], input=json.dumps({"source": script, "paths": paths}), text=True, capture_output=True, check=True, timeout=20)
    outputs = json.loads(result.stdout)
    for (slug, package), url in zip(packages.items(), outputs[:-1], strict=True):
        assert url == "file:///repo/book/_static/" + package + "/" + slug + "/explorer/defined/?v=123456789abc#proof-line-0001"
    assert outputs[-1] == "file:///repo/book/_static/" + publication.ATLAS_NAME + "/index.html?view=goal&focus=G007&v=123456789abc"


def test_live_manifest_all_assets_and_frozen_historical_inputs(files, actual):
    manifest = publication.strict_json(files["manifest.json"])
    assert len(files["manifest.json"]) <= 2 * 1024 * 1024
    assert manifest["schema"] == publication.SCHEMA + "-manifest"
    assert manifest["catalog_sha256"] == manifest["first_enrollment_catalog_sha256"] == actual["context"].catalog_sha256
    assert manifest["files"] == {name: {"bytes": len(files[name]), "sha256": sha256(files[name]).hexdigest()} for name in files if name != "manifest.json"}
    for name, expected in builder.ASSET_DIGESTS.items():
        assert sha256(files["assets/" + name]).hexdigest() == expected
    manifests = publication.authenticate_snapshots()
    for item in publication.SNAPSHOTS:
        prefix = "historical/" + item.directory + "/"
        assert sha256(files[prefix + "manifest.json"]).hexdigest() == item.manifest_sha256
        for path in manifests[item.directory]["files"]:
            if path.startswith(("sources/", "receipts/")) or path in {"checkpoints.json", "proof-audit.json"}:
                assert files[prefix + path] == publication.snapshot_file(item, manifests[item.directory], path)


@pytest.mark.parametrize("mutation", ("kernel", "lean", "principal", "owned", "body", "statement"))
def test_live_real_family_report_counterfactual_is_rejected(mutation, actual, original):
    context = actual["context"]
    slug = "dirichlet-inverses"
    report = deepcopy(context.families[slug])
    if mutation == "kernel": report["bundle"]["original_ha_checked"] = False
    elif mutation == "lean": report["bundle"]["independent_lean_checked"] = False
    elif mutation == "principal": report["principal_roots"][0]["complete_ordinary_ha_checked"] = False
    elif mutation == "owned": report["owned_node_ids"].pop(next(iter(report["owned_node_ids"])))
    elif mutation == "body": report["rows"][0]["proof_nodes"] += 1
    else: report["rows"][0]["statement_sha256"] = "0" * 64
    with pytest.raises(publication.PublicationError):
        publication._promote_corpus(original[slug], report, context, {row["name"]: row for row in context.catalog["theorems"]}, {})


@pytest.fixture(scope="module")
def atlas_actual(pytestconfig):
    return live_input(pytestconfig, "atlas")


def test_live_atlas_exact_120_goals_current_release_and_honest_open_boundaries(atlas_actual):
    files = FileTree(atlas_actual["directory"], atlas_actual["inventory"]["files"])
    assert set(files) == {"campaign.json", "definitions.json", "index.html", "dag-audit.json"}
    campaign = publication.strict_json(files["campaign.json"])
    goals = {row["id"]: row for row in campaign["nodes"]}
    assert len(goals) == 144 and sum(row["kind"] == "goal" for row in goals.values()) == 120
    assert campaign["meta"]["current_alpha_version"] == "v31"
    assert campaign["meta"]["current_alpha_checked_use_count"] == 3796
    assert goals["G007"]["status"] == goals["G014"]["status"] == "alpha_closed"
    assert goals["G007"]["evidence"]["proof_tag"] == "MI0006"
    assert goals["G009"]["status"] == goals["G091"]["status"] == "open"
    assert goals["G009"]["evidence"]["partial_component_checked_use"] is True
    assert goals["G009"]["evidence"]["checked_use"] is False
    graph = publication.strict_json(files["definitions.json"])
    assert graph["reviewed_definition_count"] == 372 and graph["reviewed_definition_edge_count"] == 787


def test_live_atlas_embedded_payload_and_actual_javascript_match(atlas_actual):
    files = FileTree(atlas_actual["directory"], atlas_actual["inventory"]["files"])
    document = drivers()["Document"](files["index.html"])
    embedded = [source for attrs, source in document.scripts if attrs.get("id") == "campaign-data"]
    assert len(embedded) == 1 and publication.strict_json(embedded[0]) == publication.strict_json(files["campaign.json"])
    scripts = [source for attrs, source in document.scripts if attrs.get("type") != "application/json" and "src" not in attrs]
    code = 'const vm=require("node:vm"),r=JSON.parse(require("node:fs").readFileSync(0,"utf8"));r.forEach(s=>new vm.Script(s));process.stdout.write(String(r.length));'
    result = subprocess.run(["node", "-e", code], input=json.dumps(scripts), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(scripts) > 0
