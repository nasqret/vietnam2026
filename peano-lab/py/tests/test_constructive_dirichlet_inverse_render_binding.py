"""Fresh byte bindings and retained syntax only, never proof acceptance.

No worker or proof checker is replaced by an accepting mock. The slower
retained fixture derives actual source-selected metadata without executing
proofs or producing verified pages; it is not a saved success receipt.
"""

from dataclasses import replace
import io
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_constructive_dirichlet_inverse_explorer as build


def _forbidden(*_args, **_kwargs):
    pytest.fail("a presentation-only check invoked proof or semantic validation")


@pytest.fixture(scope="module")
def binding():
    return build._render_binding()


def test_binding_freshly_reads_all_nineteen_bundles_sources_checker_and_old_snapshot(binding, monkeypatch):
    pinned, modules, checker = [], [], []
    read = build.closure._read_pinned
    source = build.bottom._source_bytes
    binary = build.bottom._check_lean_binary
    def record(path, size, digest):
        pinned.append((path, size, digest)); return read(path, size, digest)
    def record_source(pin):
        modules.append(pin); return source(pin)
    def record_binary():
        checker.append(True); return binary()
    monkeypatch.setattr(build.closure, "_read_pinned", record)
    monkeypatch.setattr(build.bottom, "_source_bytes", record_source)
    monkeypatch.setattr(build.bottom, "_check_lean_binary", record_binary)
    monkeypatch.setattr(build.audit, "_binding", _forbidden)
    monkeypatch.setattr(build.audit, "verify_in_fresh_windows", _forbidden)
    monkeypatch.setattr(build, "previous_rows", _forbidden)
    monkeypatch.setattr(build.closure, "_validate_frontier", _forbidden)
    assert build._render_binding() == binding
    groups, metadata = build._checkpoint_metadata()
    items = tuple(item for group in groups for item in group)
    assert len(items) == 19 and tuple(sum(item.frontier_count for item in group) for group in groups) == (170, 126, 125, 113, 40)
    assert all((ROOT / item.artifact, item.artifact_bytes, item.artifact_sha256) in pinned for item in items)
    assert modules == [pin for item in items for pin in item.modules]
    assert checker == [True]
    assert (ROOT / build.closure.PARENT_CATALOG, build.closure.PARENT_CATALOG_BYTES,
            build.closure.PARENT_CATALOG_SHA256) in pinned
    assert sum(path.is_relative_to(ROOT / Path(build.PRIOR_MANIFEST).parent) for path, _, _ in pinned) == 424
    assert metadata[-1][0]["modules"][0]["factory"] == "make_dirichlet_signed_unit_candidate_theorems"


def _targets():
    return {
        "source": ROOT / build.checkpoints.CHECKPOINTS[0].modules[0].path,
        "prior_source": ROOT / build.audit.prior_bottom.CHECKPOINTS[0].modules[0].path,
        "control": ROOT / "scripts/check_constructive_dirichlet_inverse.py",
        "renderer": ROOT / "scripts/build_constructive_dirichlet_inverse_explorer.py",
        "rfc": ROOT / build.checkpoints.CHECKPOINTS[-1].rfc,
        "artifact": ROOT / build.checkpoints.CHECKPOINTS[-1].artifact,
        "prior_artifact": ROOT / build.audit.prior_dirichlet.CHECKPOINTS[-1].artifact,
        "parent": ROOT / build.closure.PARENT_CATALOG,
        "checker": build.bottom.LEAN_BINARY,
        "prior_manifest": ROOT / build.PRIOR_MANIFEST,
        "prior_page": ROOT / Path(build.PRIOR_MANIFEST).parent / "index.html",
        "asset": next(iter(build.model.ASSET_SOURCES.values())),
    }


@pytest.mark.parametrize("kind", tuple(_targets()))
def test_same_length_literal_byte_changes_are_never_cached_or_accepted(kind, binding, monkeypatch):
    target = _targets()[kind]
    original = Path.open
    reads = []
    def changed(path, mode="r", *args, **kwargs):
        if path == target and mode == "rb":
            with original(path, mode, *args, **kwargs) as stream:
                raw = stream.read()
            reads.append(True)
            return io.BytesIO(bytes((raw[0] ^ 1,)) + raw[1:])
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", changed)
    try:
        changed_binding = build._render_binding()
    except ValueError:
        pass
    else:
        assert changed_binding != binding
    assert reads, kind


@pytest.mark.parametrize("kind", ("source", "control", "artifact", "parent", "checker", "prior_page", "asset"))
@pytest.mark.parametrize("fault", ("missing", "nonregular", "symlink", "oversized"))
def test_missing_symlink_nonregular_and_oversized_inputs_fail_before_read(kind, fault, monkeypatch):
    target = _targets()[kind]
    old_file, old_link, old_stat, old_open = Path.is_file, Path.is_symlink, Path.stat, Path.open
    monkeypatch.setattr(Path, "is_file", lambda path: False if path == target and fault in ("missing", "nonregular") else old_file(path))
    monkeypatch.setattr(Path, "is_symlink", lambda path: True if path == target and fault == "symlink" else old_link(path))
    def changed_stat(path, *args, **kwargs):
        result = old_stat(path, *args, **kwargs)
        if path == target and fault == "oversized":
            return SimpleNamespace(st_size=build.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes + 1, st_mode=result.st_mode)
        return result
    monkeypatch.setattr(Path, "stat", changed_stat)
    def guarded_open(path, *args, **kwargs):
        if path == target: pytest.fail("unsafe input was read")
        return old_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded_open)
    with pytest.raises(ValueError): build._render_binding()


@pytest.mark.parametrize("field,value", (
    ("slug", "../foreign"), ("slug", 7), ("frontier_count", True), ("frontier_count", 0),
    ("modules", []), ("modules", ()), ("modules", (SimpleNamespace(module="foreign"),)),
    ("principal_roots", []), ("principal_roots", ("duplicate", "duplicate", "root")),
    ("principal_roots", ("bad name", "second", "third")),
    ("artifact", "/absolute.json"), ("artifact", "research/arithmetic-library/artifacts/../bad.json"),
    ("artifact_bytes", True), ("artifact_bytes", 0), ("artifact_bytes", 10**30),
    ("artifact_sha256", "F" * 64), ("frontier_specs_sha256", "0" * 63),
    ("rfc", "../other.md"), ("rfc", None),
))
def test_malformed_registered_checkpoint_metadata_fails_closed(field, value, monkeypatch):
    item, *tail = build.checkpoints.CHECKPOINTS
    monkeypatch.setattr(build.checkpoints, "CHECKPOINTS", (replace(item, **{field: value}), *tail))
    with pytest.raises((ValueError, TypeError)): build._render_binding()


@pytest.mark.parametrize("generation", range(5))
@pytest.mark.parametrize("change", ("principal", "spec_pin", "rfc"))
def test_each_prior_or_current_registry_metadata_change_alters_the_fingerprint(generation, change, binding, monkeypatch):
    owner = (build.audit.prior_bottom, build.audit.prior_lower, build.audit.prior_continuation,
             build.audit.prior_dirichlet, build.checkpoints)[generation]
    item, *tail = owner.CHECKPOINTS
    values = {
        "principal": {"principal_roots": ("different_principal", *item.principal_roots[1:])},
        "spec_pin": {"frontier_specs_sha256": "0" * 64},
        "rfc": {"rfc": build.checkpoints.CHECKPOINTS[-1].rfc},
    }[change]
    assert any(getattr(item, key) != value for key, value in values.items())
    monkeypatch.setattr(owner, "CHECKPOINTS", (replace(item, **values), *tail))
    assert build._render_binding() != binding


def test_module_and_factory_metadata_are_bound_without_claiming_proof_success(binding, monkeypatch):
    item, *tail = build.checkpoints.CHECKPOINTS
    replacement = replace(item, modules=build.checkpoints.CHECKPOINTS[1].modules)
    monkeypatch.setattr(build.checkpoints, "CHECKPOINTS", (replacement, *tail))
    assert build._render_binding() != binding
    monkeypatch.setattr(build.checkpoints.ModulePin, "factory", property(lambda _pin: "forged_factory"))
    with pytest.raises(build.ExplorerError, match="factory metadata"): build._render_binding()


def test_mutable_assets_and_source_orders_are_bound_every_time(binding, monkeypatch):
    actual_assets = build.model._assets()
    name = next(iter(actual_assets))
    monkeypatch.setattr(build.model, "_assets", lambda: {**actual_assets, name: actual_assets[name] + b" "})
    assert build._render_binding() != binding
    monkeypatch.undo()
    monkeypatch.setattr(build, "RENDER_SOURCES", tuple(reversed(build.RENDER_SOURCES)))
    assert build._render_binding() != binding


@pytest.fixture(scope="module")
def retained():
    syntax = {}
    for checkpoint in build.checkpoints.CHECKPOINTS:
        metadata, selected = build.audit._expected_family_report(checkpoint, with_selection=True)
        syntax[checkpoint.slug] = (selected, build.audit._canonical(metadata))
    return syntax


def test_retained_table_is_exact_actual_plan_union_without_reselecting_support(retained, monkeypatch):
    monkeypatch.setattr(build, "previous_rows", _forbidden)
    monkeypatch.setattr(build.closure, "_validate_frontier", _forbidden)
    monkeypatch.setattr(build.audit, "verify_in_fresh_windows", _forbidden)
    actual = build._retained_table(retained)
    expected = {row.name: row for row in build.closure.parent_snapshot().specs}
    for selected, _ in retained.values():
        expected.update({row.name: row for row in selected.frontier})
        assert {row.name for row in selected.plan.rows} <= actual.keys()
    assert actual == expected and len(actual) < 3756 + 40


def _changed_selection(retained, selected, *, slug=None, expected=None):
    result = dict(retained)
    name = slug or build.EXPECTED_FAMILIES[0]
    result[name] = (selected, result[name][1] if expected is None else build.audit._canonical(expected))
    return result


@pytest.mark.parametrize("fault", ("missing", "extra", "reordered", "list", "cached_list", "saved_report", "metadata_text"))
def test_retained_projection_shape_never_accepts_a_saved_report(retained, fault):
    result = dict(retained)
    first = build.EXPECTED_FAMILIES[0]
    if fault == "missing": del result[first]
    elif fault == "extra": result["foreign"] = result[first]
    elif fault == "reordered": result = dict(reversed(tuple(result.items())))
    elif fault == "list": result = list(result.items())
    elif fault == "cached_list": result[first] = list(result[first])
    elif fault == "saved_report": result[first] = (build.audit._decode_message(result[first][1]), result[first][1])
    else: result[first] = (result[first][0], result[first][1].decode())
    with pytest.raises(ValueError): build._retained_table(result)


@pytest.mark.parametrize("fault", ("owned", "owned_type", "missing_row", "duplicate_row", "reordered_rows",
    "node_id", "inventory_index", "target", "dependency", "frontier_flag", "roots", "frontier_names",
    "edge_count", "ordered_digest", "metadata_slug", "metadata_specs", "metadata_frontier"))
def test_retained_plan_mutations_are_rejected_without_any_proof_acceptance(retained, fault):
    selected, raw = retained[build.EXPECTED_FAMILIES[0]]
    plan, expected = selected.plan, build.audit._decode_message(raw)
    rows = list(plan.rows)
    if fault == "owned": selected = replace(selected, owned=selected.owned[:-1])
    elif fault == "owned_type": selected = replace(selected, owned=list(selected.owned))
    elif fault == "missing_row": plan = replace(plan, rows=plan.rows[:-1])
    elif fault == "duplicate_row": plan = replace(plan, rows=(*plan.rows, plan.rows[-1]))
    elif fault == "reordered_rows": plan = replace(plan, rows=tuple(reversed(plan.rows)))
    elif fault in ("node_id", "inventory_index", "target", "dependency", "frontier_flag"):
        index = next(index for index, row in enumerate(rows) if row.dependencies)
        changes = {"node_id": {"node_id": True}, "inventory_index": {"inventory_index": -1},
                   "target": {"statement_sha256": "0" * 64}, "dependency": {"dependencies": ()},
                   "frontier_flag": {"is_frontier": not rows[index].is_frontier}}[fault]
        rows[index] = replace(rows[index], **changes); plan = replace(plan, rows=tuple(rows))
    elif fault == "roots": plan = replace(plan, root_names=())
    elif fault == "frontier_names": plan = replace(plan, frontier_names=tuple(reversed(plan.frontier_names)))
    elif fault == "edge_count": plan = replace(plan, dependency_edge_count=plan.dependency_edge_count + 1)
    elif fault == "ordered_digest": plan = replace(plan, ordered_names_sha256="0" * 64)
    elif fault == "metadata_slug": expected["slug"] = "foreign"
    elif fault == "metadata_specs": expected["new_specs_sha256"] = "0" * 64
    else: expected["complete_non_alpha_specs_sha256"] = "0" * 64
    selected = replace(selected, plan=plan)
    with pytest.raises(ValueError): build._retained_table(_changed_selection(retained, selected, expected=expected))


def test_retained_frontiers_reject_conflicting_complete_specs_not_only_targets(retained):
    first, _ = retained[build.EXPECTED_FAMILIES[0]]
    selected, raw = retained[build.EXPECTED_FAMILIES[-1]]
    shared = next(row.name for row in first.frontier if row.name in {value.name for value in selected.frontier})
    frontier = tuple(replace(row, summary=row.summary + " changed") if row.name == shared else row
                     for row in selected.frontier)
    digest = build.closure._specs_digest(frontier)
    expected = build.audit._decode_message(raw); expected["complete_non_alpha_specs_sha256"] = digest
    changed = replace(selected, frontier=frontier, plan=replace(selected.plan, frontier_specs_sha256=digest))
    with pytest.raises(build.ExplorerError, match="conflicting retained"):
        build._retained_table(_changed_selection(retained, changed, slug=build.EXPECTED_FAMILIES[-1], expected=expected))


@pytest.mark.parametrize("field", ("bottom_support", "lower_support", "continuation_support", "dirichlet_support", "current_support"))
def test_retained_role_changes_cannot_misclassify_actual_prerequisites(retained, field):
    selected, _ = retained[build.EXPECTED_FAMILIES[0]]
    changed = replace(selected, **{field: (selected.owned[0].name,)})
    with pytest.raises(build.ExplorerError, match="roles"):
        build._retained_table(_changed_selection(retained, changed))


def test_retained_role_metadata_cannot_count_owned_theorems_as_support(retained):
    selected, raw = retained[build.EXPECTED_FAMILIES[0]]
    names = (selected.owned[0].name,)
    expected = build.audit._decode_message(raw)
    expected["support"]["current_cross_track_theorems"] = list(names)
    changed = replace(selected, current_support=names)
    with pytest.raises(build.ExplorerError, match="partition"):
        build._retained_table(_changed_selection(retained, changed, expected=expected))


def test_retained_plan_cannot_add_an_unreachable_but_correct_alpha_row(retained):
    selected, raw = retained[build.EXPECTED_FAMILIES[0]]
    present = {row.name for row in selected.plan.rows}
    index, extra = next((index, row) for index, row in enumerate(build.closure.parent_snapshot().specs)
                       if row.name not in present and set(row.dependencies) <= present)
    node = build.closure.BottomLayerRow(len(selected.plan.rows), index, extra.name,
        build._digest(extra.statement), extra.dependencies, False)
    rows = (*selected.plan.rows, node)
    plan = replace(selected.plan, rows=rows,
        dependency_edge_count=sum(len(row.dependencies) for row in rows),
        ordered_names_sha256=build._digest("\n".join(row.name for row in rows)))
    with pytest.raises(build.ExplorerError, match="coverage"):
        build._retained_table(_changed_selection(retained, replace(selected, plan=plan)))
