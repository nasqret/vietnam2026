"""Non-authorizing unit tests for exact v31 metadata and resource boundaries.

Fixtures model only an internal projection. They contain no theorem proof,
FreshProofAudit, LiveReleaseContext, or saved-receipt authority. The unmodified
private validator function bodies are loaded from their actual source ASTs
with isolated syntax-only dependencies; no public verification/publishing
entrypoint is executed, and no release artifact is written.
"""

from __future__ import annotations

import ast
import builtins
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_peano_library_channels_v31.py"
VERIFIER = ROOT / "scripts/verify_peano_library_channels_v31.py"
AUDIT = ROOT / "scripts/check_alpha_v31_completed_lower.py"


def _tree(path):
    return ast.parse(path.read_text(), filename=str(path))


def _function(path, name):
    return next(node for node in _tree(path).body if isinstance(node, ast.FunctionDef) and node.name == name)


def _literal(path, name):
    node = next(node for node in _tree(path).body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
    return ast.literal_eval(node.value)


def _private_functions(path, names, namespace):
    """Execute only the actual named private functions, without rewriting them."""
    nodes = [node for node in _tree(path).body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


def _compact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _pretty(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()


def _digest(value):
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


@pytest.fixture
def projection():
    # Every value below is syntax-only test data, not an accepted proof report.
    inventory = _literal(AUDIT, "EXPECTED_INVENTORY")
    ordinary_count = 52
    edition = SimpleNamespace(
        EXPECTED_ALPHA_V31_EDGE_COUNT=12248, EXPECTED_ALPHA_V31_LAYER_COUNT=53,
        ALPHA_V31_IDENTITY_SHA256=_digest("projection-only edition"),
        ALPHA_ENTRIES=("projection-only, not EditionEntry",),
        FRONTIER_NEW_NAMES=("projection_only_not_a_theorem",),
    )
    audit = SimpleNamespace(report={"fixture_notice": "NOT PROOF EVIDENCE", "ordinary_principal_count": ordinary_count})
    proof_audit = SimpleNamespace(
        EXPECTED_INVENTORY=inventory,
        PARENT_SHA256="ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7",
        registry=lambda: tuple(SimpleNamespace(slug=slug) for slug, _ in inventory),
    )
    families = {slug: {"bundle": {"fixture_notice": "NO PROOF", "slug": slug}} for slug, _ in inventory}
    parent_binding = {"fixture_notice": "projection-only parent binding"}
    paths = {name: Path("/synthetic-metadata-only") / name for name in (
        "catalog-v31.json", "catalog-v31-delta.json", "metrics-v31.json", "dependency-graph-v31.mmd",
        "metrics-v30.json", "channels-v30.json", "receipt.json",
    )}
    builder = SimpleNamespace(
        SCHEMA="peano-library-alpha-snapshot-v31", METRICS_SCHEMA="peano-library-alpha-metrics-v31",
        CHANNEL_SCHEMA="peano-library-channels-v31", compact=_compact, pretty=_pretty, digest=_digest,
        relative=lambda path: path.name, _parent_binding=lambda: parent_binding,
        strict_json=json.loads, DEFAULT_ALPHA=paths["catalog-v31.json"],
        DEFAULT_DELTA=paths["catalog-v31-delta.json"], DEFAULT_METRICS=paths["metrics-v31.json"],
        DEFAULT_GRAPH=paths["dependency-graph-v31.mmd"], DEFAULT_RECEIPT=paths["receipt.json"],
        PARENT_METRICS=paths["metrics-v30.json"], PARENT_CHANNELS=paths["channels-v30.json"],
        EXPECTED_PARENT_PINS={"channels": (paths["channels-v30.json"], _digest("parent channels"))},
        historical_evidence=SimpleNamespace(archive_bindings=lambda: [{"fixture_notice": "syntax-only archive binding"}]),
    )
    base = SimpleNamespace(
        _ordered_root=lambda _entries, *, include_origin: _digest("origin" if include_origin else "spec"),
        _membership_root=lambda _rows: _digest("membership"), _evidence_root=lambda _rows: _digest("evidence"),
    )
    roots = {
        "edition_identity_sha256": edition.ALPHA_V31_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": _digest("origin"), "ordered_spec_root_sha256": _digest("spec"),
        "membership_root_sha256": _digest("membership"), "evidence_root_sha256": _digest("evidence"),
    }
    counts = {"theorem_count": 3796, "checked_use_count": 3796, "stable_count": 432,
              "alpha_only_count": 3364, "edge_count": 12248, "layer_count": 53}
    parent = {
        "schema": "peano-library-alpha-snapshot-v30", **counts, **roots,
        "theorems": [], "enrollment_origin_counts": {"ha": 2790, "stable": 432},
        "evidence_counts": {"alpha_closed": 2790, "stable_closed": 432},
        "membership_counts": {"alpha_only": 2790, "stable": 432},
        "canonical_order": ["synthetic historical ordering"], "evidence_documents": [],
        "historical_projection_marker": {"first_admission": "unchanged"},
    }
    parent["theorem_count"] = parent["checked_use_count"] = 3222
    parent["alpha_only_count"] = 2790
    names_hash = _digest("\n".join(edition.FRONTIER_NEW_NAMES))
    promotion = {
        "status": "kernel_checked_complete_dependency_closed_additive_edition",
        "parent_theorem_count": 3222, "frontier_new_count": 574,
        "checked_use_before": 3222, "checked_use_after": 3796, "campaign_counts": dict(inventory),
        "frontier_ordered_names_sha256": names_hash, "proof_bundle_count": 19,
        "proof_bundles": [families[slug]["bundle"] for slug, _ in inventory],
        "independent_lean_bundle_verified": True, "ordinary_principal_count": ordinary_count,
        "remaining_body_checked_count": 0, "receipt_path": "receipt.json", "receipt_sha256": _digest(_pretty(audit.report)),
        "completed_named_targets": ["G007", "G014"], "open_named_targets": ["G009", "G091"],
        "historical_evidence_archives": builder.historical_evidence.archive_bindings(),
    }
    catalog = {
        **deepcopy(parent), **counts, **roots, "schema": builder.SCHEMA,
        "enrollment_origin_counts": {"ha": 3364, "stable": 432},
        "evidence_counts": {"alpha_closed": 3364, "stable_closed": 432},
        "membership_counts": {"alpha_only": 3364, "stable": 432},
        "canonical_order": [*parent["canonical_order"], *(f"Constructive Alpha-v31 {slug} ({count})" for slug, count in inventory)],
        "frontier_v31_campaign_counts": dict(inventory), "frontier_v31_ordered_names_sha256": names_hash,
        "parent_alpha_v30": parent_binding, "alpha_v31_completed_lower_promotion": promotion,
    }
    parent_metrics = {
        "schema": "parent-metadata-only", "theorem_count": 3222, "checked_use_count": 3222,
        "catalog_path": "catalog-v30.json", "catalog_sha256": _digest("parent"),
        "evidence_counts": parent["evidence_counts"],
        "edition_identity_sha256": _digest("old edition"), "ordered_enrollment_root_sha256": _digest("old origin"),
        "ordered_spec_root_sha256": _digest("old spec"), "dependency_graph": {},
        "dependency_graph_path": "dependency-graph-v30.mmd", "dependency_graph_sha256": _digest("old graph"),
        "checked_closure_metrics": {
            "certificate_digest_kinds": {"self-contained-proof-bundle-sha256": 2790},
            "metric_bearing_theorem_count": 3222, "missing_empty_context_metric_count": 0,
            "old_receipt_semantics": {"preserve": True},
        },
        "promotion_gates": {
            "canonical_topology": {"theorem_count": 3222, "declared_edge_count": 10588},
            "dependency_link_analysis": {"reachability_redundant_direct_dependency_count": 0},
            "source_integrity": {"source_bound_theorem_count": 3222},
            "full_alpha_empty_context_compilation": {"checked": 3222, "required": 3222, "missing": 0, "status": "passed"},
            "historical_gate": {"preserve": True},
        },
        "historical_metrics_marker": {"preserve": True},
    }
    topology = {"reachability_redundant_direct_dependency_count": 1}
    graph_bytes = b"syntax-only graph fixture, not proof evidence\n"
    builder._topology = lambda _rows, _parent: (topology, graph_bytes)
    manifest_hash = _digest("manifest")
    metrics = deepcopy(parent_metrics)
    metrics.update(
        schema=builder.METRICS_SCHEMA, theorem_count=3796, checked_use_count=3796,
        catalog_path="catalog-v31.json", catalog_sha256=manifest_hash, dependency_graph=topology,
        dependency_graph_path="dependency-graph-v31.mmd", dependency_graph_sha256=_digest(graph_bytes),
        **{key: catalog[key] for key in ("evidence_counts", "edition_identity_sha256", "ordered_enrollment_root_sha256",
           "ordered_spec_root_sha256", "frontier_v31_campaign_counts", "frontier_v31_ordered_names_sha256", "parent_alpha_v30")},
        alpha_v31_completed_lower_promotion=promotion,
    )
    metrics["checked_closure_metrics"].update(
        certificate_digest_kinds={"self-contained-proof-bundle-sha256": 3364},
        metric_bearing_theorem_count=3796, missing_empty_context_metric_count=0,
        campaign_v31_bundle_accounting={
            "campaign_count": 19, "campaign_counts": dict(inventory), "new_checked_theorem_count": 574,
            "proof_bundles": promotion["proof_bundles"],
            "totals_policy": "Nineteen complete checked artifacts; inherited bodies and packaging roots are never counted as new theorems.",
        },
    )
    gates = metrics["promotion_gates"]
    gates["canonical_topology"].update(theorem_count=3796, declared_edge_count=12248)
    gates["dependency_link_analysis"]["reachability_redundant_direct_dependency_count"] = 1
    gates["source_integrity"]["source_bound_theorem_count"] = 3796
    gates["full_alpha_empty_context_compilation"].update(checked=3796, required=3796)
    gates["complete_constructive_alpha_v31_completed_lower"] = {**promotion, "status": "passed"}
    parent_alpha = {
        "artifact_path": "catalog-v30.json", "artifact_sha256": _digest("parent catalog"), "artifacts": {},
        "theorem_count": 3222, "checked_use_count": 3222, "evidence_counts": parent["evidence_counts"],
        **roots, "historical_first_admission_count": 315,
    }
    parent_channels = {"channels": {"alpha": parent_alpha, "stable": {"unchanged_stable": 432}},
                       "policy": {"default": "stable"}}
    alpha = {
        **deepcopy(parent_alpha), "artifact_path": "catalog-v31.json", "artifact_sha256": manifest_hash,
        **roots, "theorem_count": 3796, "checked_use_count": 3796, "evidence_counts": catalog["evidence_counts"],
        "alpha_v31_frontier_new_count": 574, "frontier_v31_campaign_counts": dict(inventory),
        "parent_alpha_v30_sha256": proof_audit.PARENT_SHA256,
    }
    channels = {
        "schema": builder.CHANNEL_SCHEMA, "channels": {"alpha": alpha, "stable": parent_channels["channels"]["stable"]},
        "default_channel": "stable", "policy": parent_channels["policy"],
        "parent_channels_v30": {"path": "channels-v30.json", "sha256": builder.EXPECTED_PARENT_PINS["channels"][1]},
    }
    def read_bytes(path):
        # No filesystem is consulted by this projection-only fixture.
        return {
            paths["metrics-v30.json"]: _pretty(parent_metrics), paths["channels-v30.json"]: _pretty(parent_channels),
            paths["catalog-v31.json"]: b"manifest", paths["catalog-v31-delta.json"]: b"delta",
            paths["dependency-graph-v31.mmd"]: graph_bytes, paths["metrics-v31.json"]: _pretty(metrics),
        }[path]
    builder.read_bytes = read_bytes
    def reseal_channel_projection():
        # Recompute ordinary data hashes as an attacker could. This never runs
        # a proof checker or creates an authenticated release capability.
        alpha["artifacts"] = {
            key: {"path": builder.relative(path), "sha256": _digest(read_bytes(path))}
            for key, path in (("catalog", builder.DEFAULT_ALPHA), ("catalog_delta", builder.DEFAULT_DELTA),
                              ("metrics", builder.DEFAULT_METRICS), ("dependency_graph", builder.DEFAULT_GRAPH))
        }
        channels["channel_pointer_root_sha256"] = _digest(_compact(channels["channels"]))
    reseal_channel_projection()
    def isolated_import(name, *args, **kwargs):
        assert name == "peano_lab.library", "projection validator attempted an unexpected import"
        return SimpleNamespace(editions_v31=edition)
    namespace = {
        "__builtins__": {**vars(builtins), "__import__": isolated_import},
        "builder": builder, "proof_audit": proof_audit, "base": base,
        "Counter": Counter, "deepcopy": deepcopy, "ReleaseError": ValueError,
    }
    _private_functions(VERIFIER, ("_same", "_require", "_verify_metadata"), namespace)
    def validate():
        return namespace["_verify_metadata"](catalog, metrics, channels, parent, families, audit, manifest_hash)
    return SimpleNamespace(catalog=catalog, metrics=metrics, channels=channels, audit=audit, validate=validate,
                           reseal=reseal_channel_projection, namespace=namespace)


def test_projection_baseline_is_not_a_proof_or_publication_capability(projection):
    assert projection.validate() is None
    assert not hasattr(projection.audit, "_token")
    assert "FreshProofAudit" not in projection.namespace and "LiveReleaseContext" not in projection.namespace


@pytest.mark.parametrize("field,value", (
    ("completed_named_targets", ["G007"]),
    ("completed_named_targets", ["G007", "G014", "G009"]),
    ("historical_evidence_archives", []),
    ("historical_evidence_archives", [{"invented": "current bytes are old evidence"}]),
))
def test_named_completions_and_literal_archive_bindings_cannot_be_rewritten(projection, field, value):
    projection.catalog["alpha_v31_completed_lower_promotion"][field] = value
    projection.reseal()
    with pytest.raises(ValueError, match="actual proof evidence"):
        projection.validate()


@pytest.mark.parametrize("mutation", ("extra", "new_count", "bundles", "old_accounting", "extra_gate", "old_top_level"))
def test_forged_metrics_fail_even_when_all_ordinary_component_hashes_are_updated(projection, mutation):
    metrics = projection.metrics
    if mutation == "extra": metrics["unreviewed_proof_authority"] = True
    elif mutation == "new_count": metrics["checked_closure_metrics"]["campaign_v31_bundle_accounting"]["new_checked_theorem_count"] = 575
    elif mutation == "bundles": metrics["checked_closure_metrics"]["campaign_v31_bundle_accounting"]["proof_bundles"] = []
    elif mutation == "old_accounting": metrics["checked_closure_metrics"]["old_receipt_semantics"]["preserve"] = False
    elif mutation == "extra_gate": metrics["promotion_gates"]["invented_acceptance"] = {"status": "passed"}
    else: metrics["historical_metrics_marker"]["preserve"] = False
    projection.reseal()
    with pytest.raises(ValueError, match="accounting|promotion gates|metrics"):
        projection.validate()


@pytest.mark.parametrize("mutation", ("third_channel", "extra_field", "first_admission", "parent_pointer"))
def test_forged_channel_metadata_is_not_hidden_by_a_recomputed_pointer_root(projection, mutation):
    channels = projection.channels
    if mutation == "third_channel": channels["channels"]["invented"] = {"checked_use_count": 1000000}
    elif mutation == "extra_field": channels["unreviewed_authority"] = True
    elif mutation == "first_admission": channels["channels"]["alpha"]["historical_first_admission_count"] = 0
    else: channels["parent_channels_v30"]["sha256"] = "0" * 64
    projection.reseal()
    with pytest.raises(ValueError, match="channel|provenance"):
        projection.validate()


@pytest.mark.parametrize("check", (False, True))
def test_rss_failure_stops_the_actual_writer_before_any_read_or_write(tmp_path, check):
    calls = []
    def too_large():
        calls.append("RSS")
        raise RuntimeError("unchanged 1536 MiB limit exceeded")
    def forbidden(*_args, **_kwargs):
        pytest.fail("an output operation preceded the RSS guard")
    namespace = {"proof_audit": SimpleNamespace(authoring_rss_bytes=too_large),
                 "read_bytes": forbidden, "relative": forbidden}
    _private_functions(BUILDER, ("check_or_write",), namespace)
    output = tmp_path / "never-created.json"
    with pytest.raises(RuntimeError, match="1536 MiB"):
        namespace["check_or_write"]({output: b"not a release"}, check=check)
    assert calls == ["RSS"] and not output.exists()


def _expression_calls(function):
    return [(index, ast.unparse(node.value.func)) for index, node in enumerate(function.body)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)]


def test_actual_builder_checks_peak_after_projection_and_before_returning_outputs():
    function = _function(BUILDER, "build_payloads")
    calls = _expression_calls(function)
    guard = next(index for index, name in calls if name == "proof_audit.authoring_rss_bytes")
    binding = max(index for index, name in calls if name == "audit.require_unchanged")
    returned = max(index for index, node in enumerate(function.body) if isinstance(node, ast.Return))
    assert binding < guard < returned
    assert all(not isinstance(node, ast.Assign) for node in function.body[guard + 1:returned])


def test_actual_verifier_checks_peak_after_live_context_construction_and_before_success():
    function = _function(VERIFIER, "context_from_live_audit")
    constructor = next(index for index, node in enumerate(function.body) if isinstance(node, ast.Assign)
                       and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == "LiveReleaseContext")
    guard = next(index for index, name in _expression_calls(function) if name == "proof_audit.authoring_rss_bytes")
    returned = max(index for index, node in enumerate(function.body) if isinstance(node, ast.Return))
    assert constructor < guard < returned
    main_calls = dict((name, index) for index, name in _expression_calls(_function(VERIFIER, "main")))
    assert main_calls["context.require_unchanged"] < main_calls["proof_audit.authoring_rss_bytes"] < main_calls["print"]


@pytest.mark.parametrize("path", ("peano-lab/py/peano_lab/kernel/subst.py", "peano-lab/py/peano_lab/engine/state.py"))
def test_substitution_and_actual_metric_implementations_are_in_the_live_source_binding(path):
    value = next(node.value for node in _tree(AUDIT).body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "CONTROL_SOURCES" for target in node.targets))
    literal_paths = [node.value for node in value.elts if isinstance(node, ast.Constant) and type(node.value) is str]
    assert literal_paths.count(path) == 1 and (ROOT / path).is_file()
    binding = _function(AUDIT, "source_binding")
    controls = next(node.value for node in binding.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "controls" for target in node.targets))
    assert isinstance(controls, ast.DictComp)
    assert isinstance(controls.generators[0].iter, ast.Name) and controls.generators[0].iter.id == "CONTROL_SOURCES"
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_read_file"
               for node in ast.walk(controls))


def test_immutable_parent_rows_are_compared_individually_with_typed_json_equality():
    function = _function(VERIFIER, "_verify_rows")
    comparisons = [node for node in ast.walk(function) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id == "_same"]
    assert any([ast.unparse(arg) for arg in node.args] == ["new", "old"] for node in comparisons)
    assert all(not any(isinstance(arg, ast.Subscript) and ast.unparse(arg).startswith("rows[:3222]")
                       for arg in node.args) for node in comparisons)


def main(argv=None):
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    result = pytest.main([str(Path(__file__).resolve()), "-q", *(sys.argv[1:] if argv is None else argv)])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    elapsed = time.monotonic() - started
    if elapsed > 180 or peak > 1536 * 1024 * 1024:
        raise SystemExit("metadata tests exceeded the unchanged authoring budget")
    print(json.dumps({"status": result, "elapsed_seconds": elapsed, "peak_rss_bytes": peak,
                      "cpu_limits": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024}))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
