"""Authoring CLI regressions, not an admission or saved-receipt verifier.

The positive example exports two genuine rows from an actual checked finite
support seed and independently checks its complete resulting cone.  Corrupt
seed examples also use the real original kernel, including an invalid body
outside the requested prefix.  No checker is replaced by an accepting stub.
"""

from dataclasses import replace
from hashlib import sha256
import ast
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import export_constructive_dirichlet as exporter
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import (
    ProofBundle, decode_proof_bundle, encode_proof_bundle,
)
from peano_lab.library.theorems import _closed_formula


MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_OUTPUT_BYTES = 128 * 1024
SCRIPT = ROOT / "scripts/export_constructive_dirichlet.py"
FINITE_SEED = ROOT / "research/arithmetic-library/artifacts/dirichlet-finite-support-proof-bundle-v1.json"
FINITE_SEED_BYTES = 587407
FINITE_SEED_SHA256 = "99d889c64fb066f79247afa4310e0143f42bfffbc2cf56e4bd9be3735e0cac47"
EXPECTED_GROUPS = (
    ("finite-support", ("signed_finite_support_candidate",), 8, 25, 312),
    ("dirichlet-convolution", ("dirichlet_convolution_candidate", "dirichlet_commutativity_candidate"), 40, 102, 1754),
    ("dirichlet-fubini", ("dirichlet_fubini_candidate", "dirichlet_associativity_candidate"), 32, 117, 1962),
    ("dirichlet-units", ("dirichlet_units_candidate",), 25, 82, 1109),
    ("mobius-inversion", ("mobius_inversion_candidate",), 8, 28, 458),
)


def _run(*arguments):
    env = dict(os.environ, PYTHONMALLOC="malloc",
               PYTHONPATH=os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts"))))
    result = subprocess.run((sys.executable, str(SCRIPT), *map(str, arguments)),
                            cwd=ROOT, env=env, capture_output=True, timeout=185)
    assert len(result.stdout) <= MAX_OUTPUT_BYTES
    assert len(result.stderr) <= MAX_OUTPUT_BYTES
    return result


def _prefix_args(output, seed=FINITE_SEED):
    return ("--family", "finite-support", "--through", "2", "--seed-only",
            "--seed", str(seed), "--output", str(output))


def _calls(function):
    tree = ast.parse(inspect.getsource(function))
    return tuple(node for node in ast.walk(tree) if isinstance(node, ast.Call))


def _call_name(call):
    return call.func.id if isinstance(call.func, ast.Name) else (
        call.func.attr if isinstance(call.func, ast.Attribute) else None)


def test_exact_native_authoring_inventory_is_113_rows_354_edges_5595_commands():
    assert exporter.AUTHORING_GROUPS == tuple((slug, modules) for slug, modules, *_ in EXPECTED_GROUPS)
    rows = ()
    for _, modules, count, edges, commands in EXPECTED_GROUPS:
        group = tuple(row for module in modules for row in exporter.module_rows(module))
        assert (len(group), sum(len(row.dependencies) for row in group),
                sum(len(row.script) for row in group)) == (count, edges, commands)
        rows += group
    assert rows == exporter.authoring_rows()
    assert len(rows) == len({row.name for row in rows}) == 113
    assert sum(len(row.dependencies) for row in rows) == 354
    assert sum(len(row.script) for row in rows) == 5595


def test_authoring_caps_authentication_and_original_closure_are_not_optional():
    calls = _calls(exporter.main)
    names = tuple(map(_call_name, calls))
    assert {"setrlimit", "alarm", "previous_seed_paths", "select_support",
            "export_bottom_layer_bundle", "authoring_rss_bytes"} <= set(names)
    limits = next(call for call in calls if _call_name(call) == "setrlimit")
    assert isinstance(limits.args[0], ast.Attribute) and limits.args[0].attr == "RLIMIT_CPU"
    assert ast.literal_eval(limits.args[1]) == (170, 175)
    alarm = next(call for call in calls if _call_name(call) == "alarm")
    assert ast.literal_eval(alarm.args[0]) == 180
    authenticate = next(call for call in calls if _call_name(call) == "previous_seed_paths")
    export = next(call for call in calls if _call_name(call) == "export_bottom_layer_bundle")
    assert authenticate.lineno < export.lineno
    # In particular, seed-only does not put the mandatory authentication
    # inside a conditional branch.  It changes only the checked seed list.
    body = ast.parse(inspect.getsource(exporter.main)).body[0].body
    assert any(isinstance(stmt, ast.Assign) and stmt.value is not None
               and isinstance(stmt.value, ast.Call)
               and _call_name(stmt.value) == "previous_seed_paths" for stmt in body)
    assert {kw.arg: ast.literal_eval(kw.value) for kw in export.keywords
            if kw.arg == "batch_size"} == {"batch_size": 1}
    assert not {"_lean_check", "verify_checkpoint", "verify_all", "_aggregate_reports"} & set(names)


@pytest.mark.parametrize("arguments", (
    (), ("--family", "finite-support"), ("--output", "unused"),
    ("--family", "unknown", "--output", "unused"),
    ("--family", "finite-support", "--output", "unused", "--through", "true"),
    ("--family", "finite-support", "--output", "unused", "--through", "1.5"),
    ("--family", "finite-support", "--output", "unused", "--admit"),
    ("--family", "finite-support", "--output", "unused", "--skip-kernel"),
    ("--family", "finite-support", "--output", "unused", "--skip-novelty"),
))
def test_malformed_cli_or_unsupported_authority_flags_are_rejected(arguments, tmp_path):
    output = tmp_path / "unused.json"
    args = tuple(str(output) if arg == "unused" else arg for arg in arguments)
    result = _run(*args)
    assert result.returncode == 2 and b"error:" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("prefix", ("-1", "0", "9", "999999"))
def test_staging_prefix_is_nonempty_and_within_exact_family(prefix, tmp_path):
    output = tmp_path / "invalid-prefix.json"
    result = _run("--family", "finite-support", "--through", prefix, "--output", output)
    assert result.returncode == 2
    assert b"--through must select a nonempty in-range family prefix" in result.stderr
    assert not output.exists()


def test_seed_only_requires_an_actual_explicit_seed_argument(tmp_path):
    output = tmp_path / "no-seed.json"
    result = _run("--family", "finite-support", "--through", "2", "--seed-only", "--output", output)
    assert result.returncode == 2
    assert b"--seed-only requires actual explicit proof data" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("kind", ("file", "directory", "live_symlink", "dangling_symlink"))
def test_existing_and_symlink_output_targets_are_not_touched(kind, tmp_path):
    output = tmp_path / "protected.json"
    target = tmp_path / "real-target.json"
    original = b"existing user bytes\x00\xff"
    if kind == "file": output.write_bytes(original)
    elif kind == "directory": output.mkdir()
    else:
        if kind == "live_symlink": target.write_bytes(original)
        output.symlink_to(target)
    result = _run(*_prefix_args(output))
    assert result.returncode == 2
    assert b"refusing to overwrite an existing mathematical artifact" in result.stderr
    if kind == "file": assert output.read_bytes() == original
    elif kind == "directory": assert output.is_dir() and not tuple(output.iterdir())
    else:
        assert output.is_symlink() and output.readlink() == target
        if kind == "live_symlink": assert target.read_bytes() == original
        else: assert not target.exists()


@pytest.fixture(scope="module")
def finite_seed():
    raw = FINITE_SEED.read_bytes()
    assert len(raw) == FINITE_SEED_BYTES and sha256(raw).hexdigest() == FINITE_SEED_SHA256
    return decode_proof_bundle(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def prefix_selection():
    rows = exporter.module_rows("signed_finite_support_candidate")[:2]
    assert tuple(row.name for row in rows) == ("signed_zero_window_empty", "signed_zero_window_restrict")
    return exporter.select_support(exporter.authoring_rows(), tuple(row.name for row in rows))


@pytest.fixture(scope="module")
def actual_prefix_export(tmp_path_factory, prefix_selection, finite_seed):
    output = tmp_path_factory.mktemp("dirichlet-export") / "finite-two.json"
    result = _run(*_prefix_args(output))
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    raw = output.read_bytes()
    bundle, target = decode_proof_bundle(raw.decode("utf-8"))
    # This invokes the original whole-cone checker again, independently of
    # the CLI's stdout or any previously stored success receipt.
    receipt = exporter.closure.check_bottom_layer_bundle(prefix_selection.frontier, bundle, target)
    return output, result, bundle, target, receipt


def test_real_seed_only_two_row_export_is_an_exact_original_ha_checked_cone(actual_prefix_export, prefix_selection):
    _, result, bundle, target, receipt = actual_prefix_export
    assert len(prefix_selection.owned) == 2
    assert len(prefix_selection.frontier) == 2
    assert not prefix_selection.current_support
    assert receipt.target == target and receipt.root == bundle.root
    assert receipt.kernel_calls == receipt.node_count == len(prefix_selection.plan.rows) + 1
    assert receipt.dependency_edges == prefix_selection.plan.dependency_edge_count + len(prefix_selection.plan.root_names)
    assert receipt.topological_order == tuple(range(receipt.node_count))
    assert b"Exported 2 authored owned rows;" in result.stdout
    assert f"{len(prefix_selection.plan.rows)}".encode() in result.stdout
    assert sha256(FINITE_SEED.read_bytes()).hexdigest() == FINITE_SEED_SHA256


def test_every_seed_node_is_checked_even_when_only_two_rows_are_needed(actual_prefix_export, finite_seed):
    _, result, *_ = actual_prefix_export
    seed, _ = finite_seed
    expected = f"bottom-layer checked seed {FINITE_SEED.name}: {len(seed.nodes)} kernel calls;".encode()
    assert expected in result.stdout


def test_staging_output_does_not_claim_lean_complete_tranche_or_alpha_authority(actual_prefix_export):
    output, result, *_ = actual_prefix_export
    assert b"NON-ADMITTING bottom-layer original-kernel ACCEPT:" in result.stdout
    assert b"exact novelty and independent Lean remain mandatory separate gates" in result.stdout
    assert b"No complete-tranche, Alpha/Stable, commit or publication claim" in result.stdout
    peak = re.search(rb"peak RSS ([0-9]+) bytes", result.stdout)
    assert peak and 0 < int(peak.group(1)) <= MAX_RSS_BYTES
    assert b'"original_ha_checked"' not in output.read_bytes()
    assert b'"independent_lean_checked"' not in output.read_bytes()
    assert b'"admitted_to_alpha"' not in output.read_bytes()


def test_checked_prefix_cannot_masquerade_as_complete_finite_support_family(actual_prefix_export):
    _, _, bundle, target, _ = actual_prefix_export
    owned = tuple(row.name for row in exporter.module_rows("signed_finite_support_candidate"))
    complete = exporter.select_support(exporter.authoring_rows(), owned)
    with pytest.raises(exporter.closure.BottomLayerClosureError, match="exact complete checkpoint inventory"):
        exporter.closure.check_bottom_layer_bundle(complete.frontier, bundle, target)


@pytest.mark.parametrize("kind", ("missing", "directory", "malformed_json", "duplicate_paths"))
def test_unusable_explicit_seed_fails_without_creating_output(kind, tmp_path):
    output = tmp_path / "rejected.json"
    seed = tmp_path / "bad-seed.json"
    if kind == "directory": seed.mkdir()
    elif kind == "malformed_json": seed.write_bytes(b'{"not": "proof data"}\n')
    elif kind == "duplicate_paths": seed = FINITE_SEED
    args = _prefix_args(output, seed)
    if kind == "duplicate_paths": args += ("--seed", str(seed))
    result = _run(*args)
    assert result.returncode != 0
    assert not output.exists()
    assert b"NON-ADMITTING bottom-layer original-kernel ACCEPT" not in result.stdout
    expected = b"paths must be distinct" if kind == "duplicate_paths" else (
        b"proof seed is missing" if kind in ("missing", "directory") else b"ProofBundleError")
    assert expected in result.stderr


@pytest.mark.parametrize("outside_requested_cone", (False, True))
def test_actual_kernel_rejects_corrupt_seed_body_including_unused_rows(
        outside_requested_cone, finite_seed, prefix_selection, tmp_path):
    seed, target = finite_seed
    rows = exporter.module_rows("signed_finite_support_candidate")
    row = rows[-1] if outside_requested_cone else rows[0]
    in_cone = {item.name for item in prefix_selection.plan.rows}
    assert (row.name not in in_cone) == outside_requested_cone
    matching = [node for node in seed.nodes if node.target == _closed_formula(row.statement)]
    assert len(matching) == 1
    damaged = replace(matching[0], body=EqRefl(Zero()))
    poisoned = ProofBundle(tuple(damaged if node.node_id == damaged.node_id else node for node in seed.nodes), seed.root)
    seed_path = tmp_path / "real-seed-one-invalid-body.json"
    seed_path.write_text(encode_proof_bundle(poisoned, target), encoding="utf-8")
    output = tmp_path / "must-not-exist.json"
    result = _run(*_prefix_args(output, seed_path))
    assert result.returncode != 0
    assert b"ProofBundleError" in result.stderr
    assert not output.exists()
    assert b"NON-ADMITTING bottom-layer original-kernel ACCEPT" not in result.stdout


def test_staging_does_not_remove_the_real_final_whole_tranche_novelty_gate():
    import check_constructive_dirichlet as audit
    import constructive_dirichlet_checkpoints as checkpoints
    assert checkpoints.EXPECTED_INVENTORY == tuple((slug, count) for slug, _, count, *_ in EXPECTED_GROUPS)
    assert "statement_duplicates" in tuple(map(_call_name, _calls(checkpoints.verify_all)))
    calls = _calls(audit._worker)
    assert any(_call_name(call) == "statement_duplicates" and len(call.args) == 1
               and isinstance(call.args[0], ast.Call) and _call_name(call.args[0]) == "_inventory"
               for call in calls)
    jobs = sorted((call for call in _calls(audit.verify_in_fresh_windows)
                   if _call_name(call) == "_run_worker"), key=lambda call: call.lineno)
    assert ast.literal_eval(jobs[0].args[0]) == "novelty"
    assert ast.literal_eval(jobs[0].args[1]) == "all"
    assert "_aggregate_reports" in tuple(map(_call_name, _calls(audit.verify_in_fresh_windows)))
    source = ast.parse((ROOT / "scripts/build_constructive_dirichlet_explorer.py").read_text())
    build = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "build_files")
    names = {_call_name(node) for node in ast.walk(build) if isinstance(node, ast.Call)}
    if "_build_verified" in names:
        verified = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "_build_verified")
        names.update(_call_name(node) for node in ast.walk(verified) if isinstance(node, ast.Call))
    # The renderer can run the exact guard directly or use the same fresh
    # audited worker pipeline; a stored JSON result is neither alternative.
    assert names & {"statement_duplicates", "verify_in_fresh_windows"}
