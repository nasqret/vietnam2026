"""Exact seven-role support and 3,756-row FormulaDAG novelty regressions.

Restated rows below are syntax-only fixtures, never newly claimed theorems.
No old auditor is run and no success receipt is accepted. Actual novelty
probes and the deliberately false-body rejection keep the original checker.
"""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_dirichlet_inverse_support as support
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


MAX_RSS_BYTES = 1536 * 1024 * 1024


def _registries():
    prior = support.previous
    return (prior.previous.first.previous, prior.previous.lower, prior.continuation, support.dirichlet)


@pytest.fixture(scope="module")
def dirichlet_root():
    return next(row for row in support.dirichlet.load_rows(support.dirichlet.CHECKPOINTS[-1])
                if row.name == "mobius_inversion_iff")


def _child(row, name="dirichlet_inverse_support_fixture"):
    return replace(row, name=name, dependencies=(row.name,), script=("exact " + row.name,))


def test_all_534_research_rows_keep_the_exact_four_generation_order():
    registries = _registries()
    generations = tuple(tuple(row for item in registry.CHECKPOINTS for row in registry.load_rows(item))
                        for registry in registries)
    rows = support.previous_rows()
    assert tuple(map(len, generations)) == support.PRIOR_RESEARCH_COUNTS == (170, 126, 125, 113)
    assert rows == tuple(row for generation in generations for row in generation)
    assert len(rows) == len({row.name for row in rows}) == support.PRIOR_RESEARCH_COUNT == 534
    assert len(support.closure.parent_snapshot().specs) + len(rows) == support.PRIOR_THEOREM_COUNT == 3756


def test_actual_ancestry_separates_all_seven_roles_without_recounting(dirichlet_root):
    cross = _child(dirichlet_root)
    owned = _child(cross, "dirichlet_inverse_support_owned_fixture")
    unused = TheoremSpec("dirichlet_inverse_support_unused", "0=0", (), ("refl",), "Syntax only.")
    selected = support.select_support((cross, owned, unused), (owned.name,))
    assert selected.owned == (owned,) and selected.current_support == (cross.name,)
    assert dirichlet_root.name in selected.dirichlet_support
    assert selected.published_support == selected.bottom_support + selected.lower_support
    assert selected.local_support == selected.continuation_support + selected.dirichlet_support
    assert selected.inherited_support == selected.published_support + selected.local_support
    alpha = {row.name for row in selected.plan.rows} - {row.name for row in selected.frontier}
    groups = (
        ({owned.name}, "new_owned_theorem"), ({cross.name}, "new_cross_track_support"),
        (set(selected.bottom_support), "inherited_published_bottom_layer_checkpoint"),
        (set(selected.lower_support), "inherited_published_lower_tier_checkpoint"),
        (set(selected.continuation_support), "inherited_local_lower_continuation_checkpoint"),
        (set(selected.dirichlet_support), "inherited_local_dirichlet_checkpoint"),
        (alpha, "inherited_alpha_v30"),
    )
    assert all(names for names, _ in groups)
    assert sum(len(names) for names, _ in groups) == len(set().union(*(names for names, _ in groups)))
    assert set().union(*(names for names, _ in groups)) == {row.name for row in selected.plan.rows}
    for names, role in groups:
        assert all(selected.role(name) == role for name in names)
    assert not set(selected.local_support) & set(selected.published_support)
    assert set(selected.plan.root_names) <= {owned.name}
    with pytest.raises(support.SupportError):
        selected.role(unused.name)
    with pytest.raises(FrozenInstanceError):
        selected.dirichlet_support = ()
    # Independently traverse actual dependency names, not imported modules.
    table = {row.name: row for row in (*support.closure.parent_snapshot().specs,
                                      *support.previous_rows(), cross, owned, unused)}
    included, pending = set(), [owned.name]
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    assert included == {row.name for row in selected.plan.rows}


@pytest.mark.parametrize("bad", (None, (), [], "x", (1,), ("missing",),
                                 ("mobius_inversion_iff",), ("mobius_divisor_sum_cancellation",),
                                 ("signed_divisor_sum_exists_unique",),
                                 ("prime_field_no_zero_divisors",), ("add_comm",)))
def test_inherited_and_invalid_names_cannot_be_owned(dirichlet_root, bad):
    with pytest.raises((ValueError, TypeError)):
        support.select_support((_child(dirichlet_root),), bad)


@pytest.mark.parametrize("mode", ("duplicate", "reordered"))
def test_owned_names_require_unique_current_inventory_order(dirichlet_root, mode):
    first = _child(dirichlet_root)
    second = _child(first, "dirichlet_inverse_support_second")
    names = (first.name, first.name) if mode == "duplicate" else (second.name, first.name)
    with pytest.raises(ValueError):
        support.select_support((first, second), names)


@pytest.mark.parametrize("mode", ("unknown", "forward", "cycle", "duplicate_current", "duplicate_dependency",
                                 "shadow_alpha", "shadow_bottom", "shadow_lower", "shadow_continuation", "shadow_dirichlet"))
def test_bad_unused_rows_cannot_hide_outside_the_actual_cone(dirichlet_root, mode):
    child = _child(dirichlet_root)
    other = replace(child, name="dirichlet_inverse_unused_bad", dependencies=("missing",))
    rows = (child, other)
    if mode == "forward":
        rows = (child, replace(other, dependencies=("dirichlet_inverse_later",)),
                replace(child, name="dirichlet_inverse_later"))
    elif mode == "cycle": rows = (child, replace(other, dependencies=(other.name,)))
    elif mode == "duplicate_current": rows = (child, replace(other, name=child.name))
    elif mode == "duplicate_dependency": rows = (child, replace(other, dependencies=(child.name, child.name)))
    elif mode.startswith("shadow_"):
        generations = _registries()
        names = {"shadow_alpha": support.closure.parent_snapshot().specs[0].name,
                 "shadow_bottom": generations[0].load_rows(generations[0].CHECKPOINTS[0])[0].name,
                 "shadow_lower": generations[1].load_rows(generations[1].CHECKPOINTS[0])[0].name,
                 "shadow_continuation": generations[2].load_rows(generations[2].CHECKPOINTS[0])[0].name,
                 "shadow_dirichlet": dirichlet_root.name}
        rows = (child, replace(other, name=names[mode], dependencies=()))
    with pytest.raises(ValueError):
        support.select_support(rows, (child.name,))


@pytest.mark.parametrize("mode", ("empty", "list", "wrong_type", "oracle"))
def test_original_frontier_and_script_guards_are_preserved(dirichlet_root, mode):
    row = _child(dirichlet_root)
    rows = {"empty": (), "list": [row], "wrong_type": ("not a theorem",),
            "oracle": (replace(row, script=("admit",)),)}[mode]
    with pytest.raises(ValueError): support.select_support(rows, (row.name,))
    with pytest.raises(ValueError): support.statement_duplicates(rows)


def test_selection_does_not_grant_proof_authority_to_a_false_statement():
    unproved = TheoremSpec("dirichlet_inverse_false_fixture", "0=1", (), ("refl",), "Not a theorem.")
    selected = support.select_support((unproved,), (unproved.name,))
    assert selected.owned == (unproved,) and selected.plan.root_names == (unproved.name,)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((unproved,), core=support.closure._table(selected.frontier))


@pytest.mark.parametrize("mode", ("missing", "duplicate", "reordered", "wrong_count", "foreign", "list", "wrong_type"))
def test_frozen_113_inventory_is_exact_before_source_or_seed_reads(monkeypatch, mode):
    items = support.dirichlet.CHECKPOINTS
    if mode == "missing": changed = items[:-1]
    elif mode == "duplicate": changed = (*items, items[0])
    elif mode == "reordered": changed = tuple(reversed(items))
    elif mode == "wrong_count": changed = (replace(items[0], frontier_count=9), *items[1:])
    elif mode == "foreign": changed = (replace(items[0], slug="foreign"), *items[1:])
    elif mode == "list": changed = list(items)
    else: changed = (object(), *items[1:])
    monkeypatch.setattr(support.dirichlet, "CHECKPOINTS", changed)
    monkeypatch.setattr(support.dirichlet, "all_new_rows", lambda: pytest.fail("read a foreign inventory"))
    with pytest.raises(ValueError, match="inventory"): support._dirichlet_rows()
    with pytest.raises(ValueError, match="inventory"): support.previous_seed_paths()


@pytest.mark.parametrize("field,value", (
    ("artifact", "research/arithmetic-library/artifacts/foreign.json"),
    ("artifact_bytes", 587408), ("artifact_sha256", "0"*64),
    ("frontier_specs_sha256", "0"*64), ("principal_roots", ("unknown",)),
    ("rfc", "foreign.md"),
))
def test_entire_frozen_113_metadata_not_just_family_counts_is_pinned(monkeypatch, field, value):
    items = support.dirichlet.CHECKPOINTS
    monkeypatch.setattr(support.dirichlet, "CHECKPOINTS", (replace(items[0], **{field: value}), *items[1:]))
    with pytest.raises(ValueError, match="metadata"): support._dirichlet_rows()
    with pytest.raises(ValueError, match="metadata"): support.previous_seed_paths()


@pytest.mark.parametrize("generation", range(4))
@pytest.mark.parametrize("field", ("name", "statement", "dependencies", "script"))
def test_cached_factory_tampering_cannot_change_any_prior_generation(monkeypatch, generation, field):
    registry = _registries()[generation]
    pin = registry.CHECKPOINTS[0].modules[0]
    module = import_module("peano_lab.library." + pin.module)
    actual = getattr(module, pin.factory)(TheoremSpec)
    values = {"name": "forged_prior_row", "statement": "0=1",
              "dependencies": ("missing",), "script": ("exact missing",)}
    poisoned = (replace(actual[0], **{field: values[field]}), *actual[1:])
    monkeypatch.setattr(module, pin.factory, lambda _: poisoned)
    with pytest.raises(ValueError): support.previous_rows()


@pytest.mark.parametrize("generation", range(4))
def test_source_authentication_of_all_four_generations_is_retained(monkeypatch, generation):
    registry = _registries()[generation]
    items = registry.CHECKPOINTS
    first = items[0]
    pin = replace(first.modules[0], sha256="0"*64)
    monkeypatch.setattr(registry, "CHECKPOINTS", (replace(first, modules=(pin, *first.modules[1:])), *items[1:]))
    with pytest.raises(ValueError, match="source changed|metadata"): support.previous_rows()


def test_exact_whole_113_spec_pin_rejects_a_cached_loader_substitution(monkeypatch):
    rows = support.dirichlet.all_new_rows()
    changed = (replace(rows[0], statement="0=1"), *rows[1:])
    monkeypatch.setattr(support.dirichlet, "all_new_rows", lambda: changed)
    with pytest.raises(ValueError, match="specifications"): support._dirichlet_rows()


def test_all_sixteen_real_seed_files_match_literal_paths_sizes_and_hashes():
    paths = support.previous_seed_paths()
    assert len(paths) == len(set(paths)) == support.PRIOR_SEED_COUNT == 16
    assert paths[:11] == support.previous.previous_seed_paths()
    expected = tuple(item for registry in _registries() for item in registry.CHECKPOINTS)
    assert paths == tuple(ROOT/item.artifact for item in expected)
    for path, item in zip(paths, expected, strict=True):
        payload = support.closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        assert len(payload) == item.artifact_bytes and sha256(payload).hexdigest() == item.artifact_sha256


@pytest.mark.parametrize("generation", range(4))
@pytest.mark.parametrize("field", ("artifact_bytes", "artifact_sha256"))
def test_changed_seed_size_or_digest_is_rejected_before_proof_reuse(monkeypatch, generation, field):
    registry = _registries()[generation]
    items = registry.CHECKPOINTS
    value = items[0].artifact_bytes+1 if field == "artifact_bytes" else "0"*64
    monkeypatch.setattr(registry, "CHECKPOINTS", (replace(items[0], **{field: value}), *items[1:]))
    with pytest.raises(ValueError, match="sealed source|metadata"): support.previous_seed_paths()


def test_no_old_audit_is_called_or_consumed_and_all_frozen_113_files_remain_exact(dirichlet_root, monkeypatch):
    import check_constructive_dirichlet as old_audit
    snapshot = ROOT/"book/_static/constructive-dirichlet-explorer"
    manifest = json.loads((snapshot/"manifest.json").read_bytes())
    paths = {snapshot/name for name in (*manifest["files"], "manifest.json")}
    controls = ("constructive_dirichlet_support", "constructive_dirichlet_checkpoints", "constructive_dirichlet_definitions",
                "constructive_dirichlet_definition_graph", "constructive_dirichlet_defined_adapter",
                "export_constructive_dirichlet", "check_constructive_dirichlet", "build_constructive_dirichlet_explorer")
    paths.update(ROOT/"scripts"/(name+".py") for name in controls)
    for registry in _registries():
        for item in registry.CHECKPOINTS:
            paths.add(ROOT/item.artifact)
            paths.update(ROOT/pin.path for pin in item.modules)
    before = {path: sha256(path.read_bytes()).hexdigest() for path in paths}
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in {"bottom-layer-checkpoints-v2.json", "lower-tier-checkpoints-v1.json",
                         "lower-continuation-checkpoints-v1.json", "dirichlet-checkpoints-v1.json"}:
            raise AssertionError("an old successful audit was consulted")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(old_audit, "verify_in_fresh_windows", lambda **_: pytest.fail("reran the frozen old 21-job audit"))
    monkeypatch.setattr(support.dirichlet, "verify_checkpoint", lambda *a, **k: pytest.fail("source selection claimed proof acceptance"))
    monkeypatch.setattr(support.dirichlet, "verify_principal_root", lambda *a, **k: pytest.fail("source selection replayed an old principal"))
    support.previous_rows();support.previous_seed_paths()
    row = _child(dirichlet_root)
    support.select_support((row,), (row.name,))
    assert {path: sha256(path.read_bytes()).hexdigest() for path in paths} == before


def _rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value*1024


def _novelty_probe(collide):
    generations = _registries()
    specimens = (("alpha", support.closure.parent_snapshot().specs[0]),
                 *((label, registry.load_rows(registry.CHECKPOINTS[0])[0])
                   for label, registry in zip(("bottom", "lower", "continuation", "dirichlet"), generations, strict=True)))
    candidates, expected = [], []
    for label, row in specimens:
        statement = row.statement
        match = re.search(r"\bforall\s+([A-Za-z_][A-Za-z0-9_']*)", statement)
        if match:
            statement = re.sub(r"\b"+re.escape(match.group(1))+r"\b", "inverse_renamed_bound_variable", statement)
        copy = replace(row, name="inverse_duplicate_"+label, statement=" ("+statement+") ",
                       dependencies=(), script=("refl",))
        candidates.append(copy);expected.append((copy.name, row.name))
    peer = replace(candidates[-1], name="inverse_duplicate_peer")
    candidates.append(peer)
    expected.extend(((peer.name, specimens[-1][1].name), (peer.name, candidates[-2].name)))
    distinct = TheoremSpec("inverse_unproved_distinct_fixture", "0=1", (), ("refl",), "Syntax only.")
    candidates.append(distinct)
    comparator = support.previous.previous.first
    original_hash = comparator.sha256
    if collide:
        class Collision:
            def digest(self): return b"\0"*32
        comparator.sha256 = lambda _: Collision()
    try: duplicates = support.statement_duplicates(tuple(candidates))
    finally: comparator.sha256 = original_hash
    assert set(expected) <= set(duplicates)
    assert all(left in {row.name for row in candidates} and left != distinct.name for left, _ in duplicates)
    assert len(support.previous_rows()) == 534
    assert len(support.closure.parent_snapshot().specs)+534 == 3756
    return {"prior_count":3756,"research_count":534,"expected_pairs":expected,
            "duplicates":duplicates,"forced_hash_collision":collide}


@pytest.mark.parametrize("collide", (False, True))
def test_exact_formula_dag_novelty_covers_3756_and_is_not_hash_authority(collide):
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT/"peano-lab/py"),str(ROOT/"scripts"))),PYTHONMALLOC="malloc")
    result = subprocess.run([sys.executable,str(Path(__file__).resolve()),"--novelty","collision" if collide else "normal"],
                            cwd=ROOT,env=environment,text=True,capture_output=True,timeout=185)
    assert result.returncode == 0, result.stdout+result.stderr
    report = json.loads(result.stdout)
    assert (report["prior_count"],report["research_count"]) == (3756,534)
    assert report["cpu_limits"] == [170,175] and report["wall_alarm_seconds"] == 180
    assert 0 < report["peak_rss_bytes"] <= MAX_RSS_BYTES
    assert report["forced_hash_collision"] is collide
    assert set(map(tuple,report["expected_pairs"])) <= set(map(tuple,report["duplicates"]))


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    started = time.monotonic()
    if sys.argv[1:] not in (["--novelty","normal"],["--novelty","collision"]):
        raise SystemExit("expected --novelty normal|collision")
    report = _novelty_probe(sys.argv[2] == "collision")
    report.update(cpu_limits=list(resource.getrlimit(resource.RLIMIT_CPU)),wall_alarm_seconds=180,
                  peak_rss_bytes=_rss(),seconds=time.monotonic()-started)
    assert report["peak_rss_bytes"] <= MAX_RSS_BYTES
    print(json.dumps(report,sort_keys=True),flush=True)
