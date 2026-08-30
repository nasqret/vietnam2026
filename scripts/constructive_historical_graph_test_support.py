"""Current observations for two obsolete assumptions in a frozen UI test.

This is explicitly UI-test implementation supersession, not proof authority.
The old 155-case file, its fixtures, the canonical DOM harness, and the actual
JavaScript asset remain immutable.  Only the 44 graph cases are dispatched to
the checks below.  Large corpus maps intentionally omit SVG links; an unused
definition is intentionally hidden by the ``visible`` notation filter.

No theorem, graph, fixture, pytest item object, or original module is patched.
Publication still supplies and authenticates its own genuine live capability.
"""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import inspect
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "scripts/constructive_historical_graph_test_support.py"
IMPLEMENTATION = "v31-historical-graph-ui-observations-v1"
ORIGINAL_FILE = "peano-lab/py/tests/test_constructive_historical_publication_v31.py"
ORIGINAL_NAME = "test_live_all44_actual_mixed_graphs_keep_getter_only_svg_hrefs"
HARNESS_FILE = "peano-lab/py/tests/test_constructive_frontier_explorer.py"
ASSET_FILE = "book/_static/pa-proof-explorer/defined/assets/explorer.js"
SOURCE_PINS = (
    (HARNESS_FILE, 129142, "9692861c8354409ad114e0537b98e71811e8bfd31c1ea3fe345a9b3e1ae57792"),
    (ORIGINAL_FILE, 15147, "da2979c6547e0d3b29c12a2ace8be64270f40203ee9b7084d80aaf6af27296fa"),
    (ASSET_FILE, 29840, "1b95ce2289502ba87f76708096aa76c07961be733d37dd56f64711b04621d982"),
)
SLUGS = (
    "quadratic-reciprocity", "bertrand-postulate", "supplementary-laws", "kummer",
    "two-squares", "four-squares", "lucas", "pythagorean-fermat-four",
    "polynomial-horner", "matrix-dot-product", "bertrand-prime-chains", "continued-fractions",
    "matrix-coded-products", "euclidean-complexity", "binary-modular-exponentiation",
    "binary-length", "euclidean-gcd-transport", "binary-modular-execution",
    "euclidean-logarithmic-bound", "binary-digit-extraction", "primes-three-mod-four",
    "matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold",
    "matrix-cofactor-expansion", "polynomial-taylor-hensel", "generalized-crt-compatibility",
    "integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer",
    "prime-count-chebyshev", "cornacchia", "cauchy-davenport", "arithmetic-foundations",
    "prime-enumeration", "gaussian-integers", "eisenstein-integers", "prime-valuation-support",
    "best-approximation", "totient-products", "squarefree-kernels", "exponent-lifting",
    "gaussian-factorization",
)
MAX_GRAPH_BYTES = 64 * 1024 * 1024
MAX_REPORT_BYTES = 4 * 1024 * 1024
NODE_TIMEOUT_SECONDS = 20
REPORT_FIELDS = frozenset((
    "sidebarHref", "sidebarLabel", "title", "summary", "svgAnchorCount", "firstSvgHref",
    "svgHrefIsGetterOnly", "allSvgHrefsAreGetterOnly", "renderedNodeIds", "compactNodeIds",
    "nodeTransforms", "selectedNodeIds", "renderedArrowCount", "currentAddress", "viewport",
    "viewportRendered",
))


class GraphTestError(AssertionError):
    """A source guard, real DOM observation, or complete UI run failed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GraphTestError(message)


def _identity(value: os.stat_result) -> tuple:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _pinned(relative: str, size: int, digest: str, *, root: Path = ROOT) -> bytes:
    """Bounded, ordinary-file reads; identities do not confer proof authority."""
    path = root / relative
    ancestors = tuple(path.parents)
    before_dirs = tuple(os.lstat(parent) for parent in ancestors)
    _require(all(stat.S_ISDIR(row.st_mode) for row in before_dirs), "unsafe frozen source ancestor")
    before = os.lstat(path)
    _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == size,
             "frozen UI source is not an exact ordinary file: " + relative)
    required_flags = ("O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK")
    _require(all(hasattr(os, flag) for flag in required_flags), "safe source-read flags unavailable")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            _require(_identity(os.fstat(stream.fileno())) == _identity(before), "frozen source changed before read")
            raw = stream.read(size + 1)
            after_fd = os.fstat(stream.fileno())
        after = os.lstat(path)
        after_dirs = tuple(os.lstat(parent) for parent in ancestors)
    except OSError as error:
        raise GraphTestError("frozen UI source could not be read safely: " + relative) from error
    _require(_identity(before) == _identity(after_fd) == _identity(after), "frozen UI source changed during read")
    _require(all((a.st_dev, a.st_ino, a.st_mode) == (b.st_dev, b.st_ino, b.st_mode)
                 for a, b in zip(before_dirs, after_dirs, strict=True)), "frozen source ancestor changed")
    _require(len(raw) == size and sha256(raw).hexdigest() == digest, "frozen UI source pin mismatch: " + relative)
    return raw


def require_frozen_sources(*, root: Path = ROOT) -> dict[str, bytes]:
    return {relative: _pinned(relative, size, digest, root=root)
            for relative, size, digest in SOURCE_PINS}


def _once(source: str, before: str, after: str) -> str:
    _require(source.count(before) == 1, "reviewed graph-observer fragment changed")
    return source.replace(before, after, 1)


def _runtime_program(sources: Mapping[str, bytes], *, visible_definitions: bool) -> str:
    """Extract the pinned AST; change only its URL option and report tail."""
    tree = ast.parse(sources[HARNESS_FILE].decode("utf-8"))
    functions = [row for row in tree.body if isinstance(row, ast.FunctionDef)
                 and row.name == "_canonical_graph_runtime"]
    _require(len(functions) == 1, "canonical graph harness is not unique")
    assignments = [row.value for row in functions[0].body if isinstance(row, ast.Assign)
                   and any(isinstance(name, ast.Name) and name.id == "harness" for name in row.targets)]
    _require(len(assignments) == 1, "canonical harness assignment changed")
    expression = assignments[0]
    _require(isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add)
             and isinstance(expression.left, ast.BinOp) and isinstance(expression.left.op, ast.Add),
             "canonical harness concatenation changed")
    prefix_node, asset_node, tail_node = expression.left.left, expression.left.right, expression.right
    _require(isinstance(prefix_node, ast.Constant) and type(prefix_node.value) is str
             and isinstance(tail_node, ast.Constant) and type(tail_node.value) is str,
             "canonical harness literals changed")
    expected_asset = ast.parse("generator.DEFINED_EXPLORER_SCRIPT.read_text()", mode="eval").body
    _require(ast.dump(asset_node) == ast.dump(expected_asset), "canonical asset-loading expression changed")
    prefix, tail = prefix_node.value, tail_node.value
    if visible_definitions:
        prefix = _once(prefix, "&definitions=selected&edges=all", "&definitions=visible&edges=all")
    tail = _once(tail,
        'const svgHref = Object.getOwnPropertyDescriptor(svgAnchors[0], "href");',
        'const svgHref = svgAnchors.length ? Object.getOwnPropertyDescriptor(svgAnchors[0], "href") : null;')
    tail = _once(tail, "firstSvgHref: svgAnchors[0].href.baseVal,",
                 "firstSvgHref: svgAnchors.length ? svgAnchors[0].href.baseVal : null,")
    tail = _once(tail,
        'svgHrefIsGetterOnly: typeof svgHref.get === "function" && svgHref.set === undefined,',
        'svgHrefIsGetterOnly: svgHref === null ? null : typeof svgHref.get === "function" && svgHref.set === undefined,')
    tail = _once(tail, "allSvgHrefsAreGetterOnly: svgAnchors.every(element => {",
                 "allSvgHrefsAreGetterOnly: svgAnchors.length ? svgAnchors.every(element => {")
    tail = _once(tail,
        'return typeof property.get === "function" && property.set === undefined;\n  }),',
        'return typeof property.get === "function" && property.set === undefined;\n  }) : null,')
    tail = _once(tail, "renderedNodeIds: renderedNodes.map(element => element.dataset.graphNode),",
        "renderedNodeIds: renderedNodes.map(element => element.dataset.graphNode),\n"
        "  compactNodeIds: renderedNodes.filter(element =>\n"
        '    element.attributes.class.split(" ").includes("pd-graph-node-compact")\n'
        "  ).map(element => element.dataset.graphNode),\n"
        "  nodeTransforms: renderedNodes.map(element => element.attributes.transform),")
    return prefix + sources[ASSET_FILE].decode("utf-8") + tail


def _strict_json(raw: str | bytes) -> Any:
    def pairs(values):
        result = {}
        for key, value in values:
            _require(key not in result, "duplicate graph/report JSON key")
            result[key] = value
        return result

    def nonfinite(_value):
        raise GraphTestError("nonfinite graph/report JSON number")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeError) as error:
        raise GraphTestError("invalid graph/report JSON") from error


def _stderr(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return (value or "[no stderr]")[-4096:]


def observe_graph(payload: dict, target: str, focus: str, *, complete_family: bool,
                  visible_definitions: bool) -> dict:
    """Run the real, byte-pinned JavaScript.  Node errors remain failures."""
    _require(type(complete_family) is bool and type(visible_definitions) is bool,
             "graph view options must be exact booleans")
    sources = require_frozen_sources()
    program = _runtime_program(sources, visible_definitions=visible_definitions)
    encoded = json.dumps({"payload": payload, "selectedTarget": target,
                          "selectedFocus": focus, "completeFamily": complete_family},
                         ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    _require(len(encoded.encode("utf-8")) <= MAX_GRAPH_BYTES, "graph input exceeds unchanged publication bound")
    try:
        result = subprocess.run(["node", "-e", program], input=encoded, text=True,
                                capture_output=True, timeout=NODE_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired as error:
        raise GraphTestError("canonical graph observation timed out: " + _stderr(error.stderr)) from None
    except OSError as error:
        raise GraphTestError("canonical graph runtime could not start: " + str(error)) from None
    _require(result.returncode == 0,
             "canonical graph observation failed (exit " + str(result.returncode) + "): " + _stderr(result.stderr))
    _require(len(result.stdout.encode("utf-8")) <= MAX_REPORT_BYTES, "graph observation report exceeds bound")
    report = _strict_json(result.stdout)
    _require(type(report) is dict, "graph observation must be an object")
    require_frozen_sources()
    return report


@dataclass(frozen=True)
class GraphModel:
    nodes: Mapping[str, dict]
    edges: tuple[dict, ...]
    theorem_ids: tuple[str, ...]
    definition_ids: tuple[str, ...]
    notation: Mapping[str, tuple[str, ...]]
    payload: Mapping[str, Any]


def _model(graph: dict) -> GraphModel:
    _require(type(graph) is dict and type(graph.get("nodes")) is list
             and type(graph.get("edges")) is list, "actual mixed graph shape changed")
    nodes = {}
    for node in graph["nodes"]:
        _require(type(node) is dict and type(node.get("id")) is str
                 and re.fullmatch(r"[A-Z][A-Z0-9]*", node["id"]) is not None
                 and node["id"] not in nodes and node.get("kind") in {"theorem", "definition"}
                 and type(node.get("name")) is str and type(node.get("href")) is str and bool(node["href"]),
                 "mixed graph node identity changed")
        nodes[node["id"]] = node
    theorem_ids = tuple(key for key, row in nodes.items() if row["kind"] == "theorem")
    definition_ids = tuple(key for key, row in nodes.items() if row["kind"] == "definition")
    _require(bool(theorem_ids) and bool(definition_ids), "historical mixed graph lacks a real theorem or definition")
    notation = defaultdict(list)
    seen_edges = set()
    kinds = {"proof_dependency": ("theorem", "theorem"),
             "uses_definition": ("theorem", "definition"),
             "definition_uses_definition": ("definition", "definition")}
    for edge in graph["edges"]:
        _require(type(edge) is dict and edge.get("kind") in kinds
                 and edge.get("source") in nodes and edge.get("target") in nodes,
                 "mixed graph has an unknown or dangling typed edge")
        key = edge["source"], edge["target"], edge["kind"]
        _require(key not in seen_edges, "mixed graph repeats a typed edge")
        seen_edges.add(key)
        _require((nodes[edge["source"]]["kind"], nodes[edge["target"]]["kind"]) == kinds[edge["kind"]],
                 "proof and notation edge categories were conflated")
        if edge["kind"] != "proof_dependency":
            notation[edge["source"]].append(edge["target"])
    return GraphModel(nodes, tuple(graph["edges"]), theorem_ids, definition_ids,
                      {key: tuple(value) for key, value in notation.items()}, graph)


def _notation_closure(model: GraphModel, starts) -> set[str]:
    seen, pending = set(starts), list(starts)
    while pending:
        for target in model.notation.get(pending.pop(), ()):
            if target not in seen:
                seen.add(target)
                pending.append(target)
    return seen


def _expected(model: GraphModel, *, complete_family: bool) -> tuple[set[str], str, int]:
    target, definition = model.theorem_ids[-1], model.definition_ids[0]
    if complete_family:
        visible = _notation_closure(model, model.theorem_ids)
        focus = definition if definition in visible else target
        arrows = sum(edge["source"] in visible and edge["target"] in visible for edge in model.edges)
        return visible, focus, arrows
    neighbors = {target}
    for edge in model.edges:
        if edge["kind"] == "proof_dependency":
            if edge["target"] == target: neighbors.add(edge["source"])
            if edge["source"] == target: neighbors.add(edge["target"])
    visible = neighbors | _notation_closure(model, (definition,))
    adjacency = model.payload.get("proof_adjacency", {})
    row = adjacency.get(target, {}) if isinstance(adjacency, Mapping) else {}
    path = row.get("critical_root_path") if isinstance(row, Mapping) else None
    path = [key for key in path if key in model.nodes and model.nodes[key]["kind"] == "theorem"] if type(path) is list else [target]
    route = set(zip(path, path[1:]))
    arrows = sum(edge["source"] in visible and edge["target"] in visible
                 and (definition in (edge["source"], edge["target"])
                      or (edge["kind"] == "proof_dependency" and (edge["source"], edge["target"]) in route))
                 for edge in model.edges)
    return visible, definition, arrows


def _id_set(value: Any, message: str) -> set[str]:
    _require(type(value) is list and all(type(item) is str for item in value)
             and len(value) == len(set(value)), message)
    return set(value)


def _assert_observation(model: GraphModel, report: dict, *, complete_family: bool) -> None:
    _require(type(report) is dict and set(report) == REPORT_FIELDS,
             "actual graph observation fields are missing or unexpected")
    visible, focus, arrows = _expected(model, complete_family=complete_family)
    _require(_id_set(report.get("renderedNodeIds"), "rendered node observations changed") == visible,
             "actual rendered theorem/definition set is not the exact graph selection")
    _require(report.get("selectedNodeIds") == [focus], "graph selection or legitimate hidden-definition fallback changed")
    _require(type(report.get("renderedArrowCount")) is int and report["renderedArrowCount"] == arrows,
             "actual typed-arrow count changed")
    node = model.nodes[focus]
    _require(report.get("sidebarHref") == node["href"]
             and report.get("title") == focus + " · " + node["name"]
             and report.get("sidebarLabel") == ("Open definition →" if node["kind"] == "definition" else "Open theorem →"),
             "actual sidebar does not describe the selected graph node")
    _require(report.get("viewportRendered") is True and type(report.get("viewport")) is str,
             "actual graph viewport is absent")
    try:
        viewport = tuple(float(part) for part in report["viewport"].split())
    except ValueError:
        raise GraphTestError("graph viewport is not numeric") from None
    _require(len(viewport) == 4 and all(math.isfinite(part) for part in viewport)
             and viewport[2] > 0 and viewport[3] > 0, "graph viewport is not finite and positive")
    transforms = report.get("nodeTransforms")
    _require(type(transforms) is list and len(transforms) == len(visible), "actual node positions are missing")
    for transform in transforms:
        _require(type(transform) is str, "actual node transform is not text")
        match = re.fullmatch(r"translate\(([^ ]+) ([^ ]+)\)", transform)
        _require(match is not None, "actual node transform has an unexpected shape")
        try:
            coordinates = tuple(float(value) for value in match.groups())
        except ValueError:
            raise GraphTestError("actual node position is not numeric") from None
        _require(all(math.isfinite(value) for value in coordinates), "actual node position is not finite")
    compact = len(visible) > 160
    _require(complete_family or not compact, "narrow view no longer exercises real SVG links")
    _require(_id_set(report.get("compactNodeIds"), "compact-node observations changed") == (visible if compact else set()),
             "actual compact-node classes differ from the canonical threshold")
    _require(type(report.get("svgAnchorCount")) is int
             and report["svgAnchorCount"] == (0 if compact else len(visible)), "actual SVG anchor count changed")
    if compact:
        _require(all(report.get(key) is None for key in
                     ("firstSvgHref", "svgHrefIsGetterOnly", "allSvgHrefsAreGetterOnly")),
                 "absent SVG links must be observed as null, never a vacuous href pass")
    else:
        first = next(key for key in model.theorem_ids if key in visible)
        _require(report["svgAnchorCount"] > 0 and type(report.get("firstSvgHref")) is str
                 and report["firstSvgHref"] == model.nodes[first]["href"] and report.get("svgHrefIsGetterOnly") is True
                 and report.get("allSvgHrefsAreGetterOnly") is True, "actual nonempty SVG links lost getter-only href behavior")
    address = report.get("currentAddress")
    _require(type(address) is str, "actual synchronized graph address is absent")
    parameters = parse_qs(urlsplit(address).query)
    _require(parameters.get("target") == [model.theorem_ids[-1]] and parameters.get("focus") == [focus]
             and parameters.get("view") == ["corpus" if complete_family else "neighborhood"]
             and parameters.get("definitions") == ["visible" if complete_family else "selected"]
             and parameters.get("edges") == ["all" if complete_family else "focus"],
             "actual graph URL no longer describes the checked direct view")


def assert_graph_views(graph: dict) -> None:
    """Check the real full corpus and a genuinely nonempty narrow link view."""
    model = _model(graph)
    target, focus = model.theorem_ids[-1], model.definition_ids[0]
    full = observe_graph(graph, target, focus, complete_family=True, visible_definitions=True)
    _assert_observation(model, full, complete_family=True)
    narrow = observe_graph(graph, target, focus, complete_family=False, visible_definitions=False)
    _assert_observation(model, narrow, complete_family=False)


def check_historical_graph_case(slug: str, files: Mapping[str, bytes]) -> None:
    _require(type(slug) is str and slug in SLUGS, "unreviewed historical graph family")
    _require(isinstance(files, Mapping), "original files fixture is not a mapping")
    raw = files[slug + "/api/graph.json"]
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_GRAPH_BYTES, "actual graph fixture bytes are absent or oversized")
    assert_graph_views(_strict_json(raw))


def _case_names() -> tuple[str, ...]:
    rows = ["test_exact_pinned_44_readers_distinguish_visible_and_admitted_counts"]
    rows += ["test_exact_original_first_records_and_compact_sidecar_pins[" + slug + "]" for slug in SLUGS]
    rows += ["test_source_only_projection_never_upgrades_real_nonadmitted_aliases[" + slug + "-" + str(count) + "]"
             for slug, count in (("kummer", 2), ("supplementary-laws", 2), ("two-squares", 26), ("four-squares", 39), ("lucas", 20))]
    rows += ["test_actual_old_checked_row_requires_exact_current_catalogue_evidence[" + change + "]"
             for change in ("missing", "checked", "body", "statement", "statement_sha", "stable")]
    rows += ["test_historical_canonical_name_alias_still_targets_its_real_tag",
             "test_typed_graph_projection_preserves_protected_data_and_real_main_boundary"]
    rows += ["test_html_context_faults_fail_closed[" + change + "]"
             for change in ("duplicate_attr", "unbalanced", "missing_graph_peer", "malformed_graph", "foreign_canonical")]
    rows += ["test_only_current_graph_schema_constraint_changes_not_proof_edition",
             "test_live_manifest_stays_bounded_and_authenticates_all44_exact_sidecars"]
    rows += ["test_live_all_historical_theorem_first_and_source_records_remain_literal[" + slug + "]" for slug in SLUGS]
    rows += [ORIGINAL_NAME + "[" + slug + "]" for slug in SLUGS]
    rows += ["test_live_all_actual_inline_javascript_and_graph_api_pairs",
             "test_live_original_alpha_v21_prerequisite_summaries_and_all_frozen_inputs_unchanged"]
    return tuple(rows)


EXPECTED_CASE_NAMES = _case_names()
CORRECTED_CASE_NAMES = tuple(ORIGINAL_NAME + "[" + slug + "]" for slug in SLUGS)
_require(len(SLUGS) == len(set(SLUGS)) == 44 and len(EXPECTED_CASE_NAMES) == len(set(EXPECTED_CASE_NAMES)) == 155,
         "literal historical UI inventory is inconsistent")


def _original_path(value: Any) -> bool:
    try:
        path = Path(value)
    except TypeError:
        return False
    return path.absolute() == ROOT / ORIGINAL_FILE


def _original_item(item) -> tuple[str, Any] | None:
    if not _original_path(getattr(item, "path", None)):
        return None
    if getattr(item, "originalname", None) != ORIGINAL_NAME:
        return None
    require_frozen_sources()
    module, original = getattr(item, "module", None), getattr(item, "obj", None)
    _require(module is not None and _original_path(getattr(module, "__file__", None))
             and inspect.isfunction(original) and original is getattr(module, ORIGINAL_NAME, None)
             and original.__globals__ is vars(module) and original.__module__ == module.__name__
             and original.__name__ == original.__qualname__ == ORIGINAL_NAME
             and _original_path(original.__code__.co_filename) and not hasattr(original, "__wrapped__"),
             "current UI dispatch did not receive the exact original frozen function object")
    signature = inspect.signature(original)
    _require(tuple(signature.parameters) == ("slug", "files") and signature.return_annotation is inspect.Signature.empty
             and all(row.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                     and row.default is inspect.Parameter.empty and row.annotation is inspect.Parameter.empty
                     for row in signature.parameters.values()), "frozen graph-case signature changed")
    parameters = getattr(getattr(item, "callspec", None), "params", None)
    _require(type(parameters) is dict and set(parameters) == {"slug"}
             and type(parameters["slug"]) is str and parameters["slug"] in SLUGS,
             "frozen graph parametrization changed")
    slug = parameters["slug"]
    _require(getattr(item, "name", None) == ORIGINAL_NAME + "[" + slug + "]"
             and type(getattr(item, "nodeid", None)) is str
             and item.nodeid.endswith("::" + item.name), "frozen graph case ID changed")
    return slug, original


class HistoricalGraphUIPlugin:
    """Public pytest dispatch, scoped to one pinned function's 44 instances."""

    def __init__(self):
        self.config = None
        self.bindings = {}
        self.selected = ()
        self.handled = set()
        self.reports = defaultdict(list)
        self.problems = []
        self.deselected = 0

    def pytest_configure(self, config):
        self.config = config

    def _complete_phase(self) -> bool:
        value = getattr(self.config, "_alpha_v31_publication", None)
        # This only asks for complete UI accounting. It does not validate or
        # manufacture the live capability checked by the original fixtures.
        return type(value) is dict and value.get("phase") == "historical"

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, session, config, items):
        yield
        original_items = [item for item in items if _original_path(getattr(item, "path", None))]
        if original_items or self._complete_phase():
            require_frozen_sources()
        bindings = {}
        for item in original_items:
            matched = _original_item(item)
            if matched is None:
                continue
            _require(item.nodeid not in bindings, "duplicate corrected historical UI case")
            slug, function = matched
            bindings[item.nodeid] = (slug, function, function.__code__)
            item.user_properties.append(("ui_test_implementation", IMPLEMENTATION))
            item.user_properties.append(("ui_test_original_source_sha256", SOURCE_PINS[1][2]))
        self.bindings = bindings
        self.selected = tuple(item.nodeid for item in items)
        if self._complete_phase():
            _require(not config.getoption("collectonly"), "same-live historical UI cannot be collection-only")
            names = [item.name for item in items]
            _require(len(original_items) == len(items) == len(set(self.selected)) == 155
                     and len(set(names)) == 155 and set(names) == set(EXPECTED_CASE_NAMES)
                     and len(bindings) == 44, "same-live historical UI must execute the exact original155 case IDs and corrected44")
            _require(self.deselected == 0, "same-live historical UI cannot deselect cases")

    @pytest.hookimpl(tryfirst=True)
    def pytest_pyfunc_call(self, pyfuncitem):
        matched = _original_item(pyfuncitem)
        if matched is None:
            return None
        slug, function = matched
        expected = self.bindings.get(pyfuncitem.nodeid)
        _require(expected is not None and expected[0] == slug and expected[1] is function
                 and expected[2] is function.__code__, "historical UI function changed after collection")
        _require(pyfuncitem.nodeid not in self.handled, "historical UI case was executed more than once")
        _require(pyfuncitem.funcargs.get("slug") == slug, "resolved historical slug fixture changed")
        result = check_historical_graph_case(slug, pyfuncitem.funcargs["files"])
        _require(result is None, "corrected graph checker did not complete synchronously")
        self.handled.add(pyfuncitem.nodeid)
        # Public pytest first-result protocol: True means the REAL checker
        # above completed. Exceptions are never caught or converted to success.
        return True

    def pytest_deselected(self, items):
        if self._complete_phase():
            self.deselected += len(items)

    def pytest_collectreport(self, report):
        if self._complete_phase() and report.outcome != "passed":
            self.problems.append("historical collection did not pass: " + report.nodeid)

    def pytest_runtest_logreport(self, report):
        if self._complete_phase():
            self.reports[report.nodeid].append((report.when, report.outcome, hasattr(report, "wasxfail")))

    def completion_errors(self, *, collectonly: bool = False) -> tuple[str, ...]:
        """A reject-only ledger, not a function which can grant proof authority."""
        errors = list(self.problems)
        if collectonly: errors.append("historical publication was collection-only")
        if self.deselected: errors.append("historical publication deselected tests")
        if len(self.selected) != len(set(self.selected)) or len(self.selected) != 155:
            errors.append("historical publication lacks155 unique selected cases")
        if len(self.bindings) != 44 or self.handled != set(self.bindings):
            errors.append("historical publication did not run all44 corrected graph checks")
        if set(self.reports) != set(self.selected):
            errors.append("historical publication reports do not cover its exact selection")
        for nodeid, rows in self.reports.items():
            if Counter(when for when, _, _ in rows) != Counter(("setup", "call", "teardown")):
                errors.append("historical case lacks exactly three execution reports: " + nodeid)
            if any(outcome != "passed" or xfail for _, outcome, xfail in rows):
                errors.append("historical case was failed/skipped/xfail: " + nodeid)
        return tuple(errors)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session, exitstatus):
        if not self._complete_phase():
            return
        errors = self.completion_errors(collectonly=session.config.getoption("collectonly"))
        if errors:
            self.problems = list(dict.fromkeys(errors))
            # Never manufacture success or overwrite a pre-existing nonzero
            # outcome. This hook can only turn an incomplete zero into failure.
            if int(session.exitstatus) == 0:
                session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        if self.bindings:
            terminalreporter.write_line("UI-test implementation supersession: " + IMPLEMENTATION
                                       + "; actual corrected graph cases completed=" + str(len(self.handled)))
        if self._complete_phase() and self.problems:
            for problem in self.problems[:12]:
                terminalreporter.write_line("Historical UI completeness failure: " + problem)
