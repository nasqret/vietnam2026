"""Bounded inverse authoring: real seeds and HA, never admission receipts.

The positive prefix is an actual new signed-unit theorem. Its proof artifact
is checked again with the original whole-cone checker. A corrupted unused
seed body and a simulated RSS rejection both fail before output; no proof
checker is replaced with an accepting stub. Exact counts were fixed only
after all three mathematical factories were frozen and checked.
"""

from dataclasses import replace
from hashlib import sha256
import ast
import inspect
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/"scripts"))
import export_constructive_dirichlet_inverse as exporter
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import ProofBundle, decode_proof_bundle, encode_proof_bundle


SCRIPT = ROOT/"scripts/export_constructive_dirichlet_inverse.py"
SEED = ROOT/"research/arithmetic-library/artifacts/mobius-inversion-proof-bundle-v1.json"
SEED_BYTES = 6488786
SEED_SHA256 = "22e7e61d5d4567df695d67830b465664fbe5a070f0367196e5cfd542ccba5b75"
MAX_RSS_BYTES = 1536*1024*1024
MAX_OUTPUT_BYTES = 128*1024
GROUPS = (
    ("dirichlet-signed-units", ("dirichlet_signed_unit_candidate",)),
    ("dirichlet-triangular", ("dirichlet_triangular_candidate",)),
    ("dirichlet-inverses", ("dirichlet_inverse_candidate",)),
)


def _run(*arguments, script=SCRIPT):
    environment = dict(os.environ,PYTHONMALLOC="malloc",
                       PYTHONPATH=os.pathsep.join((str(ROOT/"peano-lab/py"),str(ROOT/"scripts"))))
    result = subprocess.run((sys.executable,str(script),*map(str,arguments)),cwd=ROOT,env=environment,
                            capture_output=True,timeout=185)
    assert len(result.stdout) <= MAX_OUTPUT_BYTES and len(result.stderr) <= MAX_OUTPUT_BYTES
    return result


def _prefix(output, seed=SEED):
    return ("--family","dirichlet-signed-units","--through","1","--seed-only",
            "--seed",str(seed),"--output",str(output))


def _calls(function):
    return tuple(node for node in ast.walk(ast.parse(inspect.getsource(function))) if isinstance(node,ast.Call))


def _name(call):
    return call.func.id if isinstance(call.func,ast.Name) else (
        call.func.attr if isinstance(call.func,ast.Attribute) else None)


def test_exact_three_frozen_authoring_groups_have_40_rows_132_edges_1712_commands():
    assert exporter.AUTHORING_GROUPS == GROUPS
    rows = tuple(row for _,modules in GROUPS for module in modules for row in exporter.module_rows(module))
    assert exporter.authoring_rows() == rows
    assert len(rows) == len({row.name for row in rows}) == 40
    assert sum(len(row.dependencies) for row in rows) == 132
    assert sum(len(row.script) for row in rows) == 1712
    assert tuple(len(tuple(row for module in modules for row in exporter.module_rows(module)))
                 for _,modules in GROUPS) == (9,10,21)
    assert rows[0].name == "dirichlet_signed_unit_self_product"


def test_original_caps_and_prewrite_rss_guard_surround_real_ha_construction():
    assert exporter.CPU_LIMITS == (170,175) and exporter.WALL_SECONDS == 180
    main_calls = _calls(exporter.main)
    limits = next(call for call in main_calls if _name(call) == "setrlimit")
    assert limits.args[0].attr == "RLIMIT_CPU" and limits.args[1].id == "CPU_LIMITS"
    assert next(call for call in main_calls if _name(call) == "alarm").args[0].id == "WALL_SECONDS"
    calls = sorted(_calls(exporter.export_authoring_bundle),key=lambda call:call.lineno)
    names = tuple(map(_name,calls))
    assert {"previous_seed_paths","select_support","assemble_bottom_layer_bundle","encode_proof_bundle","authoring_rss_bytes","open"} <= set(names)
    assert not {"_lean_check","verify_all","verify_checkpoint","verify_in_fresh_windows","CheckedProofBundle"} & set(names)
    by_name = {name:next(call for call in calls if _name(call) == name)
               for name in ("previous_seed_paths","select_support","assemble_bottom_layer_bundle","encode_proof_bundle","open")}
    assert by_name["previous_seed_paths"].lineno < by_name["select_support"].lineno < by_name["assemble_bottom_layer_bundle"].lineno
    assert by_name["assemble_bottom_layer_bundle"].lineno < by_name["encode_proof_bundle"].lineno < by_name["open"].lineno
    assert ast.literal_eval(by_name["open"].args[0]) == "xb"
    rss = [call.lineno for call in calls if _name(call) == "authoring_rss_bytes"]
    assert any(by_name["assemble_bottom_layer_bundle"].lineno < line < by_name["encode_proof_bundle"].lineno for line in rss)
    assert any(by_name["encode_proof_bundle"].lineno < line < by_name["open"].lineno for line in rss)
    assert any(line > by_name["open"].lineno for line in rss)
    assert next(keyword.value.value for keyword in by_name["assemble_bottom_layer_bundle"].keywords if keyword.arg == "batch_size") == 1
    body = ast.parse(inspect.getsource(exporter.export_authoring_bundle)).body[0].body
    assert any(isinstance(stmt,ast.Assign) and isinstance(stmt.value,ast.Call)
               and _name(stmt.value) == "previous_seed_paths" for stmt in body)


@pytest.mark.parametrize("arguments", (
    (), ("--family","dirichlet-signed-units"), ("--output","unused"),
    ("--family","foreign","--output","unused"),
    ("--family","dirichlet-signed-units","--output","unused","--through","true"),
    ("--family","dirichlet-signed-units","--output","unused","--through","1.5"),
    ("--family","dirichlet-signed-units","--output","unused","--admit"),
    ("--family","dirichlet-signed-units","--output","unused","--skip-kernel"),
    ("--family","dirichlet-signed-units","--output","unused","--skip-novelty"),
    ("--family","dirichlet-signed-units","--output","unused","--receipt","old.json"),
))
def test_malformed_cli_and_unsupported_authority_flags_fail_closed(arguments,tmp_path):
    output = tmp_path/"unused.json"
    result = _run(*(str(output) if item == "unused" else item for item in arguments))
    assert result.returncode == 2 and b"error:" in result.stderr and not output.exists()


@pytest.mark.parametrize("prefix", ("-1","0","999999"))
def test_prefix_requires_a_nonempty_in_range_family(prefix,tmp_path):
    output = tmp_path/"invalid.json"
    result = _run("--family","dirichlet-signed-units","--through",prefix,"--output",output)
    assert result.returncode == 2 and b"nonempty in-range family prefix" in result.stderr
    assert not output.exists()


def test_seed_only_requires_an_explicit_actual_seed(tmp_path):
    output = tmp_path/"no-seed.json"
    result = _run("--family","dirichlet-signed-units","--through","1","--seed-only","--output",output)
    assert result.returncode == 2 and b"requires actual explicit proof data" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("seed_only,seeds", ((None,()),(1,()),("yes",()),(False,[]),(True,())))
def test_programmatic_seed_options_reject_before_authentication(seed_only,seeds,tmp_path,monkeypatch):
    monkeypatch.setattr(exporter,"previous_seed_paths",lambda:pytest.fail("authenticated malformed options"))
    output = tmp_path/"invalid-options.json"
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle((),(),output,seed_bundles=seeds,seed_only=seed_only)
    assert not output.exists()


@pytest.mark.parametrize("kind", ("file","directory","live_symlink","dangling_symlink"))
def test_existing_or_symlink_outputs_are_preserved(kind,tmp_path):
    output = tmp_path/"protected.json";target = tmp_path/"target.json";original = b"user bytes\x00\xff"
    if kind == "file": output.write_bytes(original)
    elif kind == "directory": output.mkdir()
    else:
        if kind == "live_symlink": target.write_bytes(original)
        output.symlink_to(target)
    result = _run(*_prefix(output))
    assert result.returncode == 2 and b"refusing to overwrite" in result.stderr
    if kind == "file": assert output.read_bytes() == original
    elif kind == "directory": assert output.is_dir() and not tuple(output.iterdir())
    else:
        assert output.is_symlink() and output.readlink() == target
        if kind == "live_symlink": assert target.read_bytes() == original
        else: assert not target.exists()


@pytest.fixture(scope="module")
def actual_seed():
    payload = SEED.read_bytes()
    assert len(payload) == SEED_BYTES and sha256(payload).hexdigest() == SEED_SHA256
    return decode_proof_bundle(payload.decode("utf-8"))


@pytest.fixture(scope="module")
def prefix_selection():
    first = exporter.module_rows("dirichlet_signed_unit_candidate")[0]
    assert first.name == "dirichlet_signed_unit_self_product"
    return exporter.select_support(exporter.authoring_rows(),(first.name,))


@pytest.fixture(scope="module")
def actual_prefix_export(tmp_path_factory,prefix_selection,actual_seed):
    output = tmp_path_factory.mktemp("inverse-actual-prefix")/"first-unit.json"
    result = _run(*_prefix(output))
    assert result.returncode == 0, result.stderr.decode("utf-8",errors="replace")
    bundle,target = decode_proof_bundle(output.read_text(encoding="utf-8"))
    # An independent fresh complete original-HA check, not trusting stdout.
    receipt = exporter.closure.check_bottom_layer_bundle(prefix_selection.frontier,bundle,target)
    return output,result,bundle,target,receipt


def test_actual_new_signed_unit_prefix_is_a_genuine_complete_ha_cone(actual_prefix_export,prefix_selection):
    _,result,bundle,target,receipt = actual_prefix_export
    assert len(prefix_selection.owned) == len(prefix_selection.frontier) == 1
    assert not prefix_selection.inherited_support and not prefix_selection.current_support
    assert receipt.target == target and receipt.root == bundle.root
    assert receipt.kernel_calls == receipt.node_count == len(prefix_selection.plan.rows)+1
    assert receipt.dependency_edges == prefix_selection.plan.dependency_edge_count+len(prefix_selection.plan.root_names)
    assert receipt.topological_order == tuple(range(receipt.node_count))
    assert b"Exported 1 authored owned rows;" in result.stdout
    assert sha256(SEED.read_bytes()).hexdigest() == SEED_SHA256


def test_every_real_seed_body_is_checked_even_outside_the_new_prefix(actual_prefix_export,actual_seed):
    _,result,*_ = actual_prefix_export
    seed,_ = actual_seed
    assert len(seed.nodes) == 531
    assert f"bottom-layer checked seed {SEED.name}: 531 kernel calls;".encode() in result.stdout


def test_staging_output_has_no_lean_novelty_or_admission_receipt(actual_prefix_export):
    output,result,*_ = actual_prefix_export
    assert b"NON-ADMITTING bottom-layer original-kernel ACCEPT:" in result.stdout
    assert b"exact 3756-prior-row novelty and independent Lean remain mandatory separate gates" in result.stdout
    assert b"No complete-tranche, Alpha/Stable, commit or publication claim" in result.stdout
    match = re.search(rb"peak RSS ([0-9]+) bytes",result.stdout)
    assert match and 0 < int(match.group(1)) <= MAX_RSS_BYTES
    payload = output.read_bytes()
    assert not any(key in payload for key in (b'"original_ha_checked"',b'"independent_lean_checked"',b'"admitted_to_alpha"'))


def test_checked_one_row_prefix_cannot_replace_the_complete_signed_unit_family(actual_prefix_export):
    _,_,bundle,target,_ = actual_prefix_export
    owned = tuple(row.name for row in exporter.module_rows("dirichlet_signed_unit_candidate"))
    assert len(owned) > 1
    selected = exporter.select_support(exporter.authoring_rows(),owned)
    with pytest.raises(ValueError,match="exact complete checkpoint inventory"):
        exporter.closure.check_bottom_layer_bundle(selected.frontier,bundle,target)


@pytest.mark.parametrize("kind", ("missing","directory","malformed_json","duplicate_paths"))
def test_bad_explicit_seeds_fail_without_output(kind,tmp_path):
    output = tmp_path/"rejected.json";seed = tmp_path/"bad-seed.json"
    if kind == "directory": seed.mkdir()
    elif kind == "malformed_json": seed.write_bytes(b'{"not":"proof data"}\n')
    elif kind == "duplicate_paths": seed = SEED
    arguments = _prefix(output,seed)
    if kind == "duplicate_paths": arguments += ("--seed",str(seed))
    result = _run(*arguments)
    assert result.returncode != 0 and not output.exists()
    assert b"NON-ADMITTING bottom-layer original-kernel ACCEPT" not in result.stdout
    expected = b"paths must be distinct" if kind == "duplicate_paths" else (
        b"proof seed is missing" if kind in ("missing","directory") else b"ProofBundleError")
    assert expected in result.stderr


def test_original_kernel_rejects_a_corrupted_unused_real_seed_body(actual_seed,tmp_path):
    seed,target = actual_seed
    damaged = replace(seed.nodes[-1],body=EqRefl(Zero()))
    # The old MI packaging theorem is unrelated to the first new unit row.
    assert damaged.node_id == seed.root
    poisoned = ProofBundle((*seed.nodes[:-1],damaged),seed.root)
    path = tmp_path/"corrupt-unused-seed.json"
    path.write_text(encode_proof_bundle(poisoned,target),encoding="utf-8")
    output = tmp_path/"must-not-exist.json"
    result = _run(*_prefix(output,path))
    assert result.returncode != 0 and b"ProofBundleError" in result.stderr
    assert not output.exists() and b"NON-ADMITTING bottom-layer original-kernel ACCEPT" not in result.stdout


def test_actual_ha_then_resource_failure_still_writes_no_artifact(tmp_path):
    output = tmp_path/"no-overbudget-proof.json"
    result = _run("--reject-rss",output,script=Path(__file__).resolve())
    assert result.returncode == 1 and b"simulated prewrite RSS rejection" in result.stderr
    assert f"bottom-layer checked seed {SEED.name}: 531 kernel calls;".encode() in result.stdout
    assert not output.exists() and b"NON-ADMITTING bottom-layer original-kernel ACCEPT" not in result.stdout


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    if len(sys.argv) != 3 or sys.argv[1] != "--reject-rss":
        raise SystemExit("expected --reject-rss OUTPUT")
    # Failure injection only. The original assemble/checker still executes.
    def reject(): raise RuntimeError("simulated prewrite RSS rejection")
    exporter.authoring_rss_bytes = reject
    raise SystemExit(exporter.main(list(_prefix(Path(sys.argv[2])))))
