"""Actual pinned DOM checks and reject-only tests of UI dispatch/accounting.

The 44 positive graph cases execute the real immutable JavaScript twice each.
Synthetic pytest records below are ONLY control-protocol fixtures; they are
never a LiveReleaseContext, proof evidence, or a successful publication run.
"""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_historical_graph_test_support as support


HISTORICAL_SOURCE = ROOT / "scripts/upgrade_constructive_historical_publication_v31.py"
HISTORICAL_PIN = (38330, "329cfb7060a13c1e73ee4465c216969e21cd95742adc16474c19e6b6578f572d")
LARGE_VISIBLE = {
    "quadratic-reciprocity": 595, "bertrand-postulate": 572,
    "two-squares": 168, "four-squares": 231,
    "integer-linear-algebra": 227, "gaussian-factorization": 217,
}


def _read_exact(path, size, digest):
    raw = path.read_bytes()
    assert len(raw) == size and sha256(raw).hexdigest() == digest
    return raw


@pytest.fixture(scope="module")
def actual_graphs():
    """Only actual old source data; no catalogue import or live capability."""
    source = _read_exact(HISTORICAL_SOURCE, *HISTORICAL_PIN)
    tree = ast.parse(source)
    assignment = next(row for row in tree.body if isinstance(row, ast.Assign)
                      and any(isinstance(name, ast.Name) and name.id == "SNAPSHOTS" for name in row.targets))
    records = [tuple(ast.literal_eval(argument) for argument in row.args) for row in assignment.value.elts]
    graphs, manifest_cache = {}, {}
    for record in records:
        directory, size, digest, slugs, *flags = record
        if len(flags) > 1 and flags[1]:
            continue
        flagship = bool(flags and flags[0])
        for slug in slugs:
            folder = ROOT / "book/_static" / directory
            selected = record
            if flagship:
                folder /= "defined"
                selected = next(row for row in records if row[0] == directory + "/defined")
            if folder not in manifest_cache:
                manifest_cache[folder] = json.loads(_read_exact(folder / "manifest.json", selected[1], selected[2]))
            path = "api/graph.json" if flagship else slug + "/explorer/defined/api/graph.json"
            pin = next(row for row in manifest_cache[folder]["files"] if row["path"] == path)
            graphs[slug] = _read_exact(folder / path, pin["bytes"], pin["sha256"])
    assert tuple(graphs) == support.SLUGS and len(graphs) == 44
    return graphs


def _independent_visible(graph):
    by_id = {node["id"]: node for node in graph["nodes"]}
    visible = {key for key, node in by_id.items() if node["kind"] == "theorem"}
    while True:
        next_ids = visible | {edge["target"] for edge in graph["edges"]
                              if edge["kind"] in {"uses_definition", "definition_uses_definition"}
                              and edge["source"] in visible}
        if next_ids == visible:
            return visible
        visible = next_ids


@pytest.mark.parametrize("slug", support.SLUGS)
def test_all44_actual_pinned_graphs_execute_both_unchanged_asset_views(slug, actual_graphs):
    graph = json.loads(actual_graphs[slug])
    before = deepcopy(graph)
    support.assert_graph_views(graph)
    assert graph == before


def test_exact_old155_and_corrected44_case_inventory_is_preserved():
    assert len(support.EXPECTED_CASE_NAMES) == len(set(support.EXPECTED_CASE_NAMES)) == 155
    assert len(support.CORRECTED_CASE_NAMES) == 44
    assert set(support.CORRECTED_CASE_NAMES) < set(support.EXPECTED_CASE_NAMES)
    assert len(set(support.EXPECTED_CASE_NAMES) - set(support.CORRECTED_CASE_NAMES)) == 111
    assert "prime-valuation-support" in support.SLUGS


def test_all44_actual_graphs_have_exact_six_compact_cases(actual_graphs):
    observed = {slug: len(_independent_visible(json.loads(raw))) for slug, raw in actual_graphs.items()}
    assert {slug: count for slug, count in observed.items() if count > 160} == LARGE_VISIBLE
    assert sum(count <= 160 for count in observed.values()) == 38


def test_actual_prime_valuation_definition_is_unused_not_a_missing_graph_node(actual_graphs):
    graph = json.loads(actual_graphs["prime-valuation-support"])
    first = next(node for node in graph["nodes"] if node["kind"] == "definition")
    assert first["id"] == "ND0177" and first["name"] == "NaturalPair"
    assert first["id"] not in _independent_visible(graph)
    model = support._model(graph)
    assert support._expected(model, complete_family=True)[1] == "PV0014"
    assert support._expected(model, complete_family=False)[1] == "ND0177"
    full = support.observe_graph(graph, "PV0014", "ND0177", complete_family=True, visible_definitions=True)
    narrow = support.observe_graph(graph, "PV0014", "ND0177", complete_family=False, visible_definitions=False)
    assert full["selectedNodeIds"] == ["PV0014"] and full["svgAnchorCount"] == 35
    assert narrow["selectedNodeIds"] == ["ND0177"] and narrow["svgAnchorCount"] == 3
    assert full["renderedArrowCount"] == 125


def test_only_exact_canonical_asset_is_executed_and_frozen_source_bytes_stay_literal():
    sources = support.require_frozen_sources()
    assert support.ASSET_FILE == "book/_static/pa-proof-explorer/defined/assets/explorer.js"
    for path, size, digest in support.SOURCE_PINS:
        assert len(sources[path]) == size and sha256(sources[path]).hexdigest() == digest
    program = support._runtime_program(sources, visible_definitions=True)
    asset = sources[support.ASSET_FILE].decode()
    assert program.count(asset) == 1
    assert "Object.defineProperty(this, \"href\"" in program
    assert "&view=corpus&definitions=visible&edges=all" in program
    assert "svgHref === null ? null" in program
    assert "}) : null," in program
    assert "pd-graph-node-compact" in program
    assert support.require_frozen_sources() == sources


@pytest.fixture(scope="module")
def small_observation(actual_graphs):
    graph = json.loads(actual_graphs["polynomial-horner"])
    model = support._model(graph)
    report = support.observe_graph(graph, model.theorem_ids[-1], model.definition_ids[0],
                                   complete_family=True, visible_definitions=True)
    support._assert_observation(model, report, complete_family=True)
    return model, report


OBSERVATION_ATTACKS = (
    "missing_node", "extra_node", "duplicate_node", "wrong_selected", "missing_selected",
    "arrow_count", "arrow_bool", "sidebar", "sidebar_label", "title", "viewport_absent",
    "viewport_nan", "viewport_inf", "viewport_zero", "viewport_negative", "viewport_short",
    "viewport_nonnumeric", "missing_positions", "nan_position", "bad_position", "compact_marks",
    "zero_anchors", "bool_anchors", "null_href", "empty_href", "wrong_href", "getter_false", "getter_bool_int",
    "getter_null", "all_getter_false", "all_getter_bool_int", "all_getter_null",
    "url_target", "url_focus", "url_view", "url_definitions", "url_edges", "url_duplicate_target",
    "missing_field", "extra_field",
)


@pytest.mark.parametrize("attack", OBSERVATION_ATTACKS)
def test_genuine_small_dom_observations_reject_every_wrong_surface(attack, small_observation):
    model, actual = small_observation
    value = deepcopy(actual)
    if attack == "missing_node": value["renderedNodeIds"].pop()
    elif attack == "extra_node": value["renderedNodeIds"].append("ND9999")
    elif attack == "duplicate_node": value["renderedNodeIds"].append(value["renderedNodeIds"][0])
    elif attack == "wrong_selected": value["selectedNodeIds"] = [model.theorem_ids[-1]]
    elif attack == "missing_selected": value["selectedNodeIds"] = []
    elif attack == "arrow_count": value["renderedArrowCount"] += 1
    elif attack == "arrow_bool": value["renderedArrowCount"] = True
    elif attack == "sidebar": value["sidebarHref"] = "foreign.html"
    elif attack == "sidebar_label": value["sidebarLabel"] = "Open theorem →"
    elif attack == "title": value["title"] = "A different node"
    elif attack == "viewport_absent": value["viewportRendered"] = False
    elif attack.startswith("viewport_"):
        value["viewport"] = {"viewport_nan": "0 0 NaN 1", "viewport_inf": "0 0 inf 1",
                             "viewport_zero": "0 0 0 1", "viewport_negative": "0 0 1 -1",
                             "viewport_short": "0 0 1", "viewport_nonnumeric": "no viewport"}[attack]
    elif attack == "missing_positions": value["nodeTransforms"].pop()
    elif attack == "nan_position": value["nodeTransforms"][0] = "translate(NaN 0)"
    elif attack == "bad_position": value["nodeTransforms"][0] = "translate(0)"
    elif attack == "compact_marks": value["compactNodeIds"] = value["renderedNodeIds"]
    elif attack == "zero_anchors": value["svgAnchorCount"] = 0
    elif attack == "bool_anchors": value["svgAnchorCount"] = True
    elif attack == "null_href": value["firstSvgHref"] = None
    elif attack == "empty_href": value["firstSvgHref"] = ""
    elif attack == "wrong_href": value["firstSvgHref"] = "wrong-tag.html"
    elif attack == "missing_field": value.pop("summary")
    elif attack == "extra_field": value["unchecked_claim"] = True
    elif attack.startswith("all_getter_"):
        value["allSvgHrefsAreGetterOnly"] = {"all_getter_false": False, "all_getter_bool_int": 1, "all_getter_null": None}[attack]
    elif attack.startswith("getter_"):
        value["svgHrefIsGetterOnly"] = {"getter_false": False, "getter_bool_int": 1, "getter_null": None}[attack]
    elif attack == "url_duplicate_target": value["currentAddress"] += "&target=OTHER"
    else:
        field = attack.removeprefix("url_")
        import re
        value["currentAddress"] = re.sub(r"([?&]" + field + r"=)[^&]*", r"\g<1>WRONG", value["currentAddress"])
    with pytest.raises(support.GraphTestError):
        support._assert_observation(model, value, complete_family=True)


@pytest.fixture(scope="module")
def compact_observation(actual_graphs):
    graph = json.loads(actual_graphs["quadratic-reciprocity"])
    model = support._model(graph)
    report = support.observe_graph(graph, model.theorem_ids[-1], model.definition_ids[0],
                                   complete_family=True, visible_definitions=True)
    support._assert_observation(model, report, complete_family=True)
    return model, report


@pytest.mark.parametrize("attack", ("first_href", "getter_true", "getter_false", "all_true", "all_false",
                                  "one_anchor", "missing_compact", "wrong_compact", "empty_nodes",
                                  "missing_href", "missing_getter", "missing_all_getters"))
def test_actual_compact_canvas_never_reports_vacuous_svg_link_success(attack, compact_observation):
    model, actual = compact_observation
    assert actual["svgAnchorCount"] == 0
    assert actual["firstSvgHref"] is actual["svgHrefIsGetterOnly"] is actual["allSvgHrefsAreGetterOnly"] is None
    value = deepcopy(actual)
    if attack == "first_href": value["firstSvgHref"] = "invented.html"
    elif attack == "getter_true": value["svgHrefIsGetterOnly"] = True
    elif attack == "getter_false": value["svgHrefIsGetterOnly"] = False
    elif attack == "all_true": value["allSvgHrefsAreGetterOnly"] = True
    elif attack == "all_false": value["allSvgHrefsAreGetterOnly"] = False
    elif attack == "one_anchor": value["svgAnchorCount"] = 1
    elif attack == "missing_compact": value["compactNodeIds"].pop()
    elif attack == "wrong_compact": value["compactNodeIds"] = []
    elif attack == "missing_href": value.pop("firstSvgHref")
    elif attack == "missing_getter": value.pop("svgHrefIsGetterOnly")
    elif attack == "missing_all_getters": value.pop("allSvgHrefsAreGetterOnly")
    else: value["renderedNodeIds"] = []
    with pytest.raises(support.GraphTestError):
        support._assert_observation(model, value, complete_family=True)


@pytest.mark.parametrize("attack", ("duplicate_node", "unknown_kind", "missing_href", "lowercase_id",
                                  "dangling_edge", "unknown_edge", "duplicate_edge", "conflated_edges"))
def test_typed_graph_model_rejects_wrong_id_and_edge_categories(attack, actual_graphs):
    graph = json.loads(actual_graphs["polynomial-horner"])
    if attack == "duplicate_node": graph["nodes"].append(deepcopy(graph["nodes"][0]))
    elif attack == "unknown_kind": graph["nodes"][0]["kind"] = "axiom"
    elif attack == "missing_href": graph["nodes"][0].pop("href")
    elif attack == "lowercase_id": graph["nodes"][0]["id"] = graph["nodes"][0]["id"].lower()
    elif attack == "dangling_edge": graph["edges"][0]["target"] = "ND9999"
    elif attack == "unknown_edge": graph["edges"][0]["kind"] = "dependency"
    elif attack == "duplicate_edge": graph["edges"].append(deepcopy(graph["edges"][0]))
    else:
        edge = next(edge for edge in graph["edges"] if edge["kind"] == "uses_definition")
        edge["kind"] = "proof_dependency"
    with pytest.raises(support.GraphTestError):
        support._model(graph)


@pytest.mark.parametrize("result", ("exit", "timeout", "startup", "malformed", "duplicate", "nonfinite", "not_object", "oversized"))
def test_runtime_failures_are_bounded_and_never_dump_the_whole_inline_program(result, monkeypatch):
    def reject_or_bad_output(*args, **kwargs):
        if result == "timeout": raise subprocess.TimeoutExpired(args[0], 20, stderr="real timeout marker")
        if result == "startup": raise OSError("node unavailable")
        if result == "exit": return SimpleNamespace(returncode=1, stdout="", stderr="x" * 9000 + "ACTUAL NODE ERROR")
        output = {"malformed": "{", "duplicate": '{"a":1,"a":2}', "nonfinite": '{"a":NaN}',
                  "not_object": "[]", "oversized": "x" * (support.MAX_REPORT_BYTES + 1)}[result]
        return SimpleNamespace(returncode=0, stdout=output, stderr="")
    monkeypatch.setattr(support.subprocess, "run", reject_or_bad_output)
    with pytest.raises(support.GraphTestError) as caught:
        support.observe_graph({}, "X", "Y", complete_family=True, visible_definitions=True)
    assert len(str(caught.value)) < 4500
    assert "const svgAnchors" not in str(caught.value)
    if result == "exit": assert "ACTUAL NODE ERROR" in str(caught.value)


@pytest.mark.parametrize("flag,value", (("complete_family", 1), ("complete_family", None),
                                      ("visible_definitions", 0), ("visible_definitions", "true")))
def test_runtime_flags_do_not_accept_boolean_lookalikes(flag, value):
    kwargs = {"complete_family": True, "visible_definitions": True, flag: value}
    with pytest.raises(support.GraphTestError, match="exact booleans"):
        support.observe_graph({}, "X", "Y", **kwargs)


def _copy_sources(tmp_path):
    for path, _, _ in support.SOURCE_PINS:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    return tmp_path


@pytest.mark.parametrize("relative,size,digest", support.SOURCE_PINS, ids=("harness", "old_ui", "canonical_js"))
@pytest.mark.parametrize("attack", ("missing", "short", "appended", "same_size_poison", "symlink", "hardlink", "fifo"))
def test_all_three_frozen_source_pins_reject_bad_bytes_or_nonordinary_nodes(relative, size, digest, attack, tmp_path):
    root = _copy_sources(tmp_path)
    path = root / relative
    original = path.read_bytes()
    if attack == "missing": path.unlink()
    elif attack == "short": path.write_bytes(original[:-1])
    elif attack == "appended": path.write_bytes(original + b" ")
    elif attack == "same_size_poison": path.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
    elif attack == "symlink":
        path.unlink(); path.symlink_to(ROOT / relative)
    elif attack == "hardlink": os.link(path, root / "second-hard-link")
    else:
        path.unlink(); os.mkfifo(path)
    with pytest.raises((support.GraphTestError, OSError)):
        support.require_frozen_sources(root=root)


def test_frozen_source_ancestor_symlink_is_rejected(tmp_path):
    (tmp_path / "peano-lab").symlink_to(ROOT / "peano-lab", target_is_directory=True)
    with pytest.raises(support.GraphTestError, match="ancestor"):
        support._pinned(*support.SOURCE_PINS[0], root=tmp_path)


def test_frozen_source_changed_between_stat_and_open_is_rejected(tmp_path, monkeypatch):
    root = _copy_sources(tmp_path)
    path = root / support.HARNESS_FILE
    real_open = support.os.open
    def changed_open(candidate, flags):
        if Path(candidate) == path:
            other = path.with_name("substituted-source")
            other.write_bytes(path.read_bytes())
            other.replace(path)
        return real_open(candidate, flags)
    monkeypatch.setattr(support.os, "open", changed_open)
    with pytest.raises(support.GraphTestError, match="changed before read"):
        support.require_frozen_sources(root=root)


def _frozen_function_module():
    """Real frozen function syntax in isolation, never a publication context."""
    path = ROOT / support.ORIGINAL_FILE
    raw = _read_exact(path, support.SOURCE_PINS[1][1], support.SOURCE_PINS[1][2])
    function = next(row for row in ast.parse(raw).body if isinstance(row, ast.FunctionDef)
                    and row.name == support.ORIGINAL_NAME)
    function.decorator_list = []
    module = ModuleType("tests.test_constructive_historical_publication_v31")
    module.__file__ = str(path)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def _item(slug="polynomial-horner", *, raw=None, module=None):
    module = _frozen_function_module() if module is None else module
    name = support.ORIGINAL_NAME + "[" + slug + "]"
    return SimpleNamespace(path=ROOT / support.ORIGINAL_FILE, originalname=support.ORIGINAL_NAME,
                           module=module, obj=getattr(module, support.ORIGINAL_NAME),
                           callspec=SimpleNamespace(params={"slug": slug}), name=name,
                           nodeid=support.ORIGINAL_FILE + "::" + name,
                           funcargs={"slug": slug, "files": {} if raw is None else {slug + "/api/graph.json": raw}},
                           user_properties=[])


def _config(*, phase=None, collectonly=False):
    config = SimpleNamespace(getoption=lambda key: collectonly if key == "collectonly" else False)
    if phase is not None:
        # Pure accounting-mode marker only: no context, proof report, files,
        # inventory or capability exists in these reject-only fixtures.
        config._alpha_v31_publication = {"phase": phase}
    return config


def _collect(plugin, items, config=None):
    config = _config() if config is None else config
    plugin.pytest_configure(config)
    wrapper = plugin.pytest_collection_modifyitems(SimpleNamespace(config=config), config, items)
    next(wrapper)
    with pytest.raises(StopIteration):
        next(wrapper)


def test_actual_dispatch_uses_original_fixtures_without_mutating_frozen_objects(actual_graphs):
    item = _item(raw=actual_graphs["polynomial-horner"])
    original, code, namespace, args = item.obj, item.obj.__code__, dict(vars(item.module)), item.funcargs
    plugin = support.HistoricalGraphUIPlugin()
    _collect(plugin, [item])
    assert plugin.pytest_pyfunc_call(item) is True  # Executes two real Node views.
    assert plugin.handled == {item.nodeid}
    assert item.obj is original and original.__code__ is code
    assert vars(item.module) == namespace and item.funcargs is args
    assert item.user_properties == [("ui_test_implementation", support.IMPLEMENTATION),
                                    ("ui_test_original_source_sha256", support.SOURCE_PINS[1][2])]
    with pytest.raises(support.GraphTestError, match="more than once"):
        plugin.pytest_pyfunc_call(item)


@pytest.mark.parametrize("name", tuple(name for name in support.EXPECTED_CASE_NAMES if name not in support.CORRECTED_CASE_NAMES))
def test_every_one_of_the_other111_original_cases_is_untouched(name):
    marker = object()
    item = SimpleNamespace(path=ROOT / support.ORIGINAL_FILE, originalname=name.split("[", 1)[0],
                           name=name, obj=marker, funcargs=marker)
    plugin = support.HistoricalGraphUIPlugin()
    assert plugin.pytest_pyfunc_call(item) is None
    assert item.obj is item.funcargs is marker and not plugin.handled


@pytest.mark.parametrize("attack", ("other_path", "same_basename", "other_function", "missing_path", "bad_path_type"))
def test_nearby_or_unrelated_items_do_not_enter_the_dispatch(attack):
    item = _item()
    if attack == "other_path": item.path = ROOT / "scripts/other.py"
    elif attack == "same_basename": item.path = ROOT / "other" / Path(support.ORIGINAL_FILE).name
    elif attack == "other_function": item.originalname += "_copy"
    elif attack == "missing_path": del item.path
    else: item.path = object()
    assert support.HistoricalGraphUIPlugin().pytest_pyfunc_call(item) is None


IDENTITY_ATTACKS = (
    "module_path", "different_object", "module_rebound", "wrong_globals", "wrong_module",
    "wrong_name", "wrong_qualname", "wrong_code_path", "wrapped", "default", "annotation",
    "missing_callspec", "extra_parameter", "unknown_slug", "numeric_slug", "wrong_case_name", "wrong_node_id",
)


@pytest.mark.parametrize("attack", IDENTITY_ATTACKS)
def test_only_exact_original_function_identity_signature_and_parameter_can_be_dispatched(attack):
    item = _item()
    if attack == "module_path": item.module.__file__ = str(ROOT / "other.py")
    elif attack == "different_object": item.obj = lambda slug, files: None
    elif attack == "module_rebound": setattr(item.module, support.ORIGINAL_NAME, lambda slug, files: None)
    elif attack == "wrong_globals":
        from types import FunctionType
        altered = FunctionType(item.obj.__code__, {"__name__": item.module.__name__})
        item.obj = altered; setattr(item.module, support.ORIGINAL_NAME, altered)
    elif attack == "wrong_module": item.obj.__module__ = "unrelated"
    elif attack == "wrong_name": item.obj.__name__ = "unrelated"
    elif attack == "wrong_qualname": item.obj.__qualname__ = "unrelated"
    elif attack == "wrong_code_path": item.obj.__code__ = item.obj.__code__.replace(co_filename=str(ROOT / "other.py"))
    elif attack == "wrapped": item.obj.__wrapped__ = item.obj
    elif attack == "default": item.obj.__defaults__ = (None,)
    elif attack == "annotation": item.obj.__annotations__ = {"slug": str}
    elif attack == "missing_callspec": del item.callspec
    elif attack == "extra_parameter": item.callspec.params["extra"] = 1
    elif attack == "unknown_slug": item.callspec.params["slug"] = "unreviewed"
    elif attack == "numeric_slug": item.callspec.params["slug"] = 0
    elif attack == "wrong_case_name": item.name = support.ORIGINAL_NAME + "[foreign]"
    else: item.nodeid = "wrong-case"
    with pytest.raises(support.GraphTestError):
        support.HistoricalGraphUIPlugin().pytest_pyfunc_call(item)


@pytest.mark.parametrize("attack", ("uncollected", "code_changed", "resolved_slug", "missing_files", "invalid_json", "bad_graph"))
def test_dispatch_never_converts_missing_checks_or_bad_actual_inputs_into_success(attack, actual_graphs):
    item = _item(raw=actual_graphs["polynomial-horner"])
    plugin = support.HistoricalGraphUIPlugin()
    if attack != "uncollected": _collect(plugin, [item])
    if attack == "code_changed": item.obj.__code__ = item.obj.__code__.replace(co_consts=item.obj.__code__.co_consts + ("changed",))
    elif attack == "resolved_slug": item.funcargs["slug"] = "kummer"
    elif attack == "missing_files": item.funcargs["files"] = {}
    elif attack == "invalid_json": item.funcargs["files"] = {"polynomial-horner/api/graph.json": b"{"}
    elif attack == "bad_graph": item.funcargs["files"] = {"polynomial-horner/api/graph.json": b'{}'}
    with pytest.raises((support.GraphTestError, KeyError)):
        plugin.pytest_pyfunc_call(item)
    assert not plugin.handled


def _all_case_items():
    module = _frozen_function_module()
    result = []
    for name in support.EXPECTED_CASE_NAMES:
        if name in support.CORRECTED_CASE_NAMES:
            slug = name[len(support.ORIGINAL_NAME) + 1:-1]
            result.append(_item(slug, module=module))
        else:
            result.append(SimpleNamespace(path=ROOT / support.ORIGINAL_FILE, originalname=name.split("[", 1)[0],
                                          name=name, nodeid=support.ORIGINAL_FILE + "::" + name))
    return result


@pytest.mark.parametrize("attack", ("missing", "duplicate", "foreign_item", "renamed_case", "collect_only", "deselected"))
def test_same_live_accounting_rejects_incomplete_or_changed155_collection(attack):
    plugin = support.HistoricalGraphUIPlugin()
    config = _config(phase="historical", collectonly=attack == "collect_only")
    items = _all_case_items()
    if attack == "missing": items.pop()
    elif attack == "duplicate": items[-1] = items[0]
    elif attack == "foreign_item": items[0].path = ROOT / "other.py"
    elif attack == "renamed_case": items[0].name += "_invented"
    elif attack == "deselected": plugin.deselected = 1
    with pytest.raises(support.GraphTestError):
        _collect(plugin, items, config)


def test_normal_targeted_selection_is_allowed_but_never_a_complete_publication_claim(actual_graphs):
    plugin = support.HistoricalGraphUIPlugin()
    item = _item(raw=actual_graphs["polynomial-horner"])
    _collect(plugin, [item])
    assert plugin.pytest_pyfunc_call(item) is True  # Genuine bounded Node calls.
    assert plugin.completion_errors()  # One real case is NOT the whole155 gate.
    session = SimpleNamespace(config=_config(), exitstatus=0)
    plugin.pytest_sessionfinish(session, 0)
    assert session.exitstatus == 0  # Ordinary targeted pytest, no live claim.


def _reject_only_accounting_fixture():
    """Synthetic baseline used ONLY after poisoning; it grants no evidence."""
    plugin = support.HistoricalGraphUIPlugin()
    plugin.pytest_configure(_config(phase="historical"))
    plugin.selected = tuple(support.ORIGINAL_FILE + "::" + name for name in support.EXPECTED_CASE_NAMES)
    plugin.bindings = {support.ORIGINAL_FILE + "::" + name: object() for name in support.CORRECTED_CASE_NAMES}
    plugin.handled = set(plugin.bindings)
    plugin.reports = {nodeid: [(phase, "passed", False) for phase in ("setup", "call", "teardown")]
                      for nodeid in plugin.selected}
    return plugin


COMPLETION_ATTACKS = (
    "missing_selection", "duplicate_selection", "missing_binding", "unexecuted_case",
    "missing_report", "extra_report", "failed", "skipped", "xfail", "xpass",
    "missing_setup", "missing_call", "missing_teardown", "duplicate_call", "unknown_phase",
    "collection_failed", "deselected", "collectonly",
)


@pytest.mark.parametrize("attack", COMPLETION_ATTACKS)
def test_complete_phase_ledger_only_rejects_missing_false_or_nonpassing_outcomes(attack):
    plugin = _reject_only_accounting_fixture()
    key = plugin.selected[0]
    if attack == "missing_selection": plugin.selected = plugin.selected[:-1]
    elif attack == "duplicate_selection": plugin.selected = (*plugin.selected[:-1], plugin.selected[0])
    elif attack == "missing_binding": plugin.bindings.pop(next(iter(plugin.bindings)))
    elif attack == "unexecuted_case": plugin.handled.pop()
    elif attack == "missing_report": plugin.reports.pop(key)
    elif attack == "extra_report": plugin.reports["foreign"] = [("call", "passed", False)]
    elif attack in {"failed", "skipped"}: plugin.reports[key][1] = ("call", attack, False)
    elif attack in {"xfail", "xpass"}: plugin.reports[key][1] = ("call", "passed" if attack == "xpass" else "skipped", True)
    elif attack.startswith("missing_"): plugin.reports[key] = [row for row in plugin.reports[key] if row[0] != attack.removeprefix("missing_")]
    elif attack == "duplicate_call": plugin.reports[key].append(("call", "passed", False))
    elif attack == "unknown_phase": plugin.reports[key][1] = ("other", "passed", False)
    elif attack == "collection_failed": plugin.problems.append("real collection failure")
    elif attack == "deselected": plugin.deselected = 1
    assert plugin.completion_errors(collectonly=attack == "collectonly")


@pytest.mark.parametrize("exitstatus", (0, 1, 2, 3, 4, 5))
def test_incomplete_live_session_can_only_force_failure_never_success(exitstatus):
    plugin = support.HistoricalGraphUIPlugin()
    config = _config(phase="historical")
    plugin.pytest_configure(config)
    session = SimpleNamespace(config=config, exitstatus=exitstatus)
    plugin.pytest_sessionfinish(session, exitstatus)
    assert int(session.exitstatus) == (1 if exitstatus == 0 else exitstatus)
    assert plugin.problems


def test_public_report_hooks_record_skips_xfail_deselection_and_collection_failures():
    plugin = support.HistoricalGraphUIPlugin()
    plugin.pytest_configure(_config(phase="historical"))
    plugin.pytest_collectreport(SimpleNamespace(outcome="failed", nodeid="old-file"))
    plugin.pytest_deselected([object()])
    plugin.pytest_runtest_logreport(SimpleNamespace(nodeid="case", when="call", outcome="skipped", wasxfail="reason"))
    assert plugin.deselected == 1 and plugin.problems
    assert plugin.reports["case"] == [("call", "skipped", True)]
    assert plugin.completion_errors()


def test_other_phases_do_not_get_historical_accounting_or_exit_overrides():
    for phase in (None, "completed", "atlas"):
        plugin = support.HistoricalGraphUIPlugin()
        config = _config(phase=phase)
        plugin.pytest_configure(config)
        plugin.pytest_deselected([object()])
        plugin.pytest_collectreport(SimpleNamespace(outcome="failed", nodeid="unrelated"))
        plugin.pytest_runtest_logreport(SimpleNamespace(nodeid="unrelated", when="call", outcome="skipped"))
        session = SimpleNamespace(config=config, exitstatus=0)
        plugin.pytest_sessionfinish(session, 0)
        assert not plugin.problems and not plugin.reports and plugin.deselected == 0
        assert session.exitstatus == 0
