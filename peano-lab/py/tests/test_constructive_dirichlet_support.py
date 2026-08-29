"""Exact support/provenance checks, not new mathematical proof contributions.

Synthetic restatements below test selection and rejection only. Novelty runs
in fresh bounded processes against all 3,643 actual prior statements, using
the original FormulaDAG comparator, including a forced hash-collision probe.
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
import constructive_dirichlet_support as support
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


MAX_RSS_BYTES = 1536 * 1024 * 1024


def _registries():
    return (support.previous.first.previous, support.previous.lower, support.continuation)


@pytest.fixture(scope="module")
def local_root():
    return next(row for row in support.continuation.all_new_rows()
                if row.name == "mobius_divisor_sum_cancellation")


def _child(row, name="dirichlet_support_test_child"):
    return replace(row, name=name, dependencies=(row.name,), script=("exact " + row.name,))


def test_all_421_prior_research_rows_remain_in_exact_generation_order():
    rows = support.previous_rows()
    first = support.previous.first.previous_rows()
    second = support.previous.lower.all_new_rows()
    third = support.continuation.all_new_rows()
    assert tuple(map(len, (first, second, third))) == (170, 126, 125)
    assert rows == (*first, *second, *third)
    assert len(rows) == len({row.name for row in rows}) == 421
    assert len(support.closure.parent_snapshot().specs) + len(rows) == 3643


def test_real_dependency_cone_separates_all_six_roles_without_recounting(local_root):
    child = _child(local_root)
    owned = _child(child, "dirichlet_support_test_root")
    unused = TheoremSpec("dirichlet_support_unused", "0=0", (), ("refl",), "Unowned syntax fixture.")
    selected = support.select_support((child, owned, unused), (owned.name,))
    assert selected.owned == (owned,)
    assert selected.current_support == (child.name,)
    assert local_root.name in selected.local_support
    assert selected.bottom_support and selected.lower_support and selected.local_support
    assert selected.published_support == selected.bottom_support + selected.lower_support
    assert selected.inherited_support == selected.published_support + selected.local_support
    assert not set(selected.local_support) & set(selected.published_support)
    alpha = {row.name for row in selected.plan.rows} - {row.name for row in selected.frontier}
    groups = (
        ({owned.name}, "new_owned_theorem"),
        ({child.name}, "new_cross_track_support"),
        (set(selected.bottom_support), "inherited_published_bottom_layer_checkpoint"),
        (set(selected.lower_support), "inherited_published_lower_tier_checkpoint"),
        (set(selected.local_support), "inherited_local_lower_continuation_checkpoint"),
        (alpha, "inherited_alpha_v30"),
    )
    assert all(names for names, _ in groups)
    assert sum(len(names) for names, _ in groups) == len(set().union(*(names for names, _ in groups)))
    assert set().union(*(names for names, _ in groups)) == {row.name for row in selected.plan.rows}
    for names, role in groups:
        assert all(selected.role(name) == role for name in names)
    assert set(selected.plan.root_names) <= {owned.name}
    assert unused.name not in {row.name for row in selected.plan.rows}
    with pytest.raises(support.SupportError):
        selected.role(unused.name)
    with pytest.raises(FrozenInstanceError):
        selected.local_support = ()
    # Independently recompute actual ancestry, not module imports or role flags.
    table = {row.name: row for row in (*support.closure.parent_snapshot().specs,
                                      *support.previous_rows(), child, owned, unused)}
    included, pending = set(), [owned.name]
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    assert included == {row.name for row in selected.plan.rows}


@pytest.mark.parametrize("bad", (None, (), [], "x", (1,), ("missing",),
                                 ("mobius_divisor_sum_cancellation",),
                                 ("signed_divisor_sum_exists_unique",),
                                 ("prime_field_no_zero_divisors",), ("add_comm",)))
def test_inherited_or_invalid_names_cannot_be_owned(local_root, bad):
    with pytest.raises((ValueError, TypeError)):
        support.select_support((_child(local_root),), bad)


@pytest.mark.parametrize("mode", ("duplicate_owned", "reordered_owned"))
def test_owned_names_must_follow_unique_current_inventory_order(local_root, mode):
    first = _child(local_root)
    second = _child(first, "dirichlet_support_second")
    names = (first.name, first.name) if mode == "duplicate_owned" else (second.name, first.name)
    with pytest.raises(ValueError):
        support.select_support((first, second), names)


@pytest.mark.parametrize("mode", ("unknown", "forward", "cycle", "duplicate_current", "duplicate_dependency",
                                 "shadow_alpha", "shadow_bottom", "shadow_lower", "shadow_local"))
def test_bad_unused_rows_cannot_hide_outside_the_selected_cone(local_root, mode):
    child = _child(local_root)
    other = replace(child, name="dirichlet_unused_bad", dependencies=("missing",))
    rows = (child, other)
    if mode == "forward":
        rows = (child, replace(other, dependencies=("dirichlet_later",)),
                replace(child, name="dirichlet_later"))
    elif mode == "cycle":
        rows = (child, replace(other, dependencies=(other.name,)))
    elif mode == "duplicate_current":
        rows = (child, replace(other, name=child.name))
    elif mode == "duplicate_dependency":
        rows = (child, replace(other, dependencies=(child.name, child.name)))
    elif mode.startswith("shadow_"):
        name = {
            "shadow_alpha": support.closure.parent_snapshot().specs[0].name,
            "shadow_bottom": support.previous.first.previous_rows()[0].name,
            "shadow_lower": support.previous.lower.all_new_rows()[0].name,
            "shadow_local": local_root.name,
        }[mode]
        rows = (child, replace(other, name=name, dependencies=()))
    with pytest.raises(ValueError):
        support.select_support(rows, (child.name,))


@pytest.mark.parametrize("mode", ("empty", "list", "wrong_type", "false_script_oracle"))
def test_original_frontier_type_and_script_guards_are_unchanged(local_root, mode):
    row = _child(local_root)
    rows = {"empty": (), "list": [row], "wrong_type": ("not a theorem",),
            "false_script_oracle": (replace(row, script=("admit",)),)}[mode]
    with pytest.raises(ValueError):
        support.select_support(rows, (row.name,))
    with pytest.raises(ValueError):
        support.statement_duplicates(rows)


def test_syntax_selection_does_not_turn_an_unproved_statement_into_proof_authority():
    unproved = TheoremSpec("dirichlet_unproved_fixture", "0=1", (), ("refl",), "Not a theorem.")
    selected = support.select_support((unproved,), (unproved.name,))
    assert selected.owned == (unproved,) and selected.plan.root_names == (unproved.name,)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((unproved,), core=support.closure._table(selected.frontier))


@pytest.mark.parametrize("mode", ("missing", "duplicate", "reordered", "wrong_count", "foreign"))
def test_local_generation_inventory_is_not_an_arbitrary_registry(monkeypatch, mode):
    items = support.continuation.CHECKPOINTS
    if mode == "missing": changed = items[:-1]
    elif mode == "duplicate": changed = (*items, items[0])
    elif mode == "reordered": changed = tuple(reversed(items))
    elif mode == "wrong_count": changed = (replace(items[0], frontier_count=13), *items[1:])
    else: changed = (replace(items[0], slug="foreign"), *items[1:])
    monkeypatch.setattr(support.continuation, "CHECKPOINTS", changed)
    with pytest.raises(ValueError, match="inventory"):
        support.previous_rows()
    with pytest.raises(ValueError, match="inventory"):
        support.previous_seed_paths()


@pytest.mark.parametrize("generation", range(3))
@pytest.mark.parametrize("field", ("name", "statement", "dependencies", "script"))
def test_cached_factory_tampering_cannot_replace_exact_prior_specs(monkeypatch, generation, field):
    registry = _registries()[generation]
    item = registry.CHECKPOINTS[0]
    rows = registry.load_rows(item)
    pin = item.modules[0]
    module = import_module("peano_lab.library." + pin.module)
    # All selected first chapters use the named factory as the first provider;
    # mutate its actual output, not a stored audit success Boolean.
    actual = getattr(module, pin.factory)(TheoremSpec)
    replacements = {"name": "forged_prior_theorem", "statement": "0=1",
                    "dependencies": ("missing_prior_dependency",), "script": ("exact missing",)}
    poisoned = (replace(actual[0], **{field: replacements[field]}), *actual[1:])
    monkeypatch.setattr(module, pin.factory, lambda _: poisoned)
    with pytest.raises(ValueError):
        support.previous_rows()


@pytest.mark.parametrize("generation", range(3))
def test_source_pin_mismatch_reads_real_unchanged_source_and_rejects(monkeypatch, generation):
    registry = _registries()[generation]
    items = registry.CHECKPOINTS
    first = items[0]
    pin = replace(first.modules[0], sha256="0" * 64)
    monkeypatch.setattr(registry, "CHECKPOINTS",
                        (replace(first, modules=(pin, *first.modules[1:])), *items[1:]))
    with pytest.raises(ValueError, match="source changed"):
        support.previous_rows()


def test_all_eleven_real_seed_files_have_the_literal_size_and_digest():
    paths = support.previous_seed_paths()
    assert len(paths) == len(set(paths)) == 11
    assert paths[:7] == support.previous.previous_seed_paths()
    expected = tuple(item for registry in _registries() for item in registry.CHECKPOINTS)
    assert paths == tuple(ROOT/item.artifact for item in expected)
    for path, item in zip(paths, expected, strict=True):
        payload = support.closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        assert len(payload) == item.artifact_bytes
        assert sha256(payload).hexdigest() == item.artifact_sha256


@pytest.mark.parametrize("generation", range(3))
@pytest.mark.parametrize("field", ("artifact_bytes", "artifact_sha256"))
def test_changed_seed_size_or_hash_is_not_treated_as_checked_proof_data(monkeypatch, generation, field):
    registry = _registries()[generation]
    items = registry.CHECKPOINTS
    value = items[0].artifact_bytes + 1 if field == "artifact_bytes" else "0" * 64
    monkeypatch.setattr(registry, "CHECKPOINTS", (replace(items[0], **{field: value}), *items[1:]))
    with pytest.raises(ValueError, match="sealed source"):
        support.previous_seed_paths()


def test_no_audit_success_sidecar_is_consulted_and_no_old_input_is_written(local_root, monkeypatch):
    paths = {ROOT/"scripts"/name for name in (
        "constructive_lower_continuation_support.py", "constructive_lower_continuation_checkpoints.py",
        "constructive_lower_tier_support.py", "constructive_lower_tier_checkpoints.py",
        "constructive_bottom_layer_checkpoints.py")}
    for registry in _registries():
        for item in registry.CHECKPOINTS:
            paths.add(ROOT/item.artifact)
            paths.update(ROOT/pin.path for pin in item.modules)
    before = {path: sha256(path.read_bytes()).hexdigest() for path in paths}
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in {"bottom-layer-checkpoints-v2.json", "lower-tier-checkpoints-v1.json",
                          "lower-continuation-checkpoints-v1.json"}:
            raise AssertionError("a saved success sidecar was consulted")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    support.previous_rows()
    support.previous_seed_paths()
    child = _child(local_root)
    support.select_support((child,), (child.name,))
    assert {path: sha256(path.read_bytes()).hexdigest() for path in paths} == before


def _rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def _novelty_probe(collide):
    inherited = support.previous_rows()
    specimens = (
        ("alpha", support.closure.parent_snapshot().specs[0]),
        ("bottom", support.previous.first.previous_rows()[0]),
        ("lower", support.previous.lower.all_new_rows()[0]),
        ("local", support.continuation.all_new_rows()[0]),
    )
    candidates, expected = [], []
    for label, row in specimens:
        statement = row.statement
        match = re.search(r"\bforall\s+([A-Za-z_][A-Za-z0-9_']*)", statement)
        if match:
            statement = re.sub(r"\b" + re.escape(match.group(1)) + r"\b",
                               "dirichlet_renamed_bound_variable", statement)
        copy = replace(row, name="dirichlet_duplicate_" + label, statement=" (" + statement + ") ",
                       dependencies=(), script=("refl",))
        candidates.append(copy)
        expected.append((copy.name, row.name))
    peer = replace(candidates[-1], name="dirichlet_duplicate_peer")
    candidates.append(peer)
    expected.extend(((peer.name, specimens[-1][1].name), (peer.name, candidates[-2].name)))
    distinct = TheoremSpec("dirichlet_false_unproved_novelty_fixture", "0=1", (), ("refl",), "Syntax only.")
    candidates.append(distinct)
    comparator = support.previous.first
    original_hash = comparator.sha256
    if collide:
        class Collision:
            def digest(self):
                return b"\0" * 32
        comparator.sha256 = lambda _: Collision()
    try:
        duplicates = support.statement_duplicates(tuple(candidates))
    finally:
        comparator.sha256 = original_hash
    assert set(expected) <= set(duplicates)
    assert all(left in {row.name for row in candidates} and left != distinct.name for left, _ in duplicates)
    assert len(inherited) == 421
    assert len(support.closure.parent_snapshot().specs) + len(inherited) == 3643
    return {"prior_count": 3643, "research_count": len(inherited), "new_count": len(candidates),
            "expected_pairs": expected, "duplicates": duplicates, "forced_hash_collision": collide}


@pytest.mark.parametrize("collide", (False, True))
def test_exact_formula_dag_novelty_covers_all_3643_rows_and_not_merely_hashes(collide):
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT/"peano-lab/py"), str(ROOT/"scripts"))),
                       PYTHONMALLOC="malloc")
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--novelty",
                             "collision" if collide else "normal"], cwd=ROOT, env=environment,
                            text=True, capture_output=True, timeout=185)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["prior_count"] == 3643 and report["research_count"] == 421
    assert report["cpu_limits"] == [170, 175] and report["wall_alarm_seconds"] == 180
    assert 0 < report["peak_rss_bytes"] <= MAX_RSS_BYTES
    assert report["forced_hash_collision"] is collide
    assert set(map(tuple, report["expected_pairs"])) <= set(map(tuple, report["duplicates"]))


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    if sys.argv[1:] not in (["--novelty", "normal"], ["--novelty", "collision"]):
        raise SystemExit("expected --novelty normal|collision")
    report = _novelty_probe(sys.argv[2] == "collision")
    report.update(cpu_limits=list(resource.getrlimit(resource.RLIMIT_CPU)), wall_alarm_seconds=180,
                  peak_rss_bytes=_rss(), seconds=time.monotonic() - started)
    assert report["peak_rss_bytes"] <= MAX_RSS_BYTES
    print(json.dumps(report, sort_keys=True), flush=True)
