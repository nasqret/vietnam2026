"""Adverse protocol checks using exact historical bytes, not new admissions."""
from copy import deepcopy
import ast
from hashlib import sha256
import gzip
import json
from pathlib import Path

import pytest
import run_sqrt2_power_wave as wave
from peano_lab.library.proof_bundle import ProofBundleError

OBSERVATION = wave.ROOT / "research/arithmetic-library/sqrt2-power/observations/shared-wave-rf001-v1"


@pytest.fixture
def recorded(monkeypatch):
    raw = gzip.decompress((OBSERVATION / "generation-process.json.gz").read_bytes())
    process = json.loads(raw)
    value = json.loads(process["stdout"])
    # Deliberately test replay under its original source boundary. This fixture
    # is never written as a fresh process observation or promoted to evidence.
    monkeypatch.setattr(wave, "pins", lambda _identifier: value["source_pins"])
    return value


def test_original_bound_bytes_and_native_negative_controls(recorded):
    result = wave.replay("RF001", recorded)
    assert result["original_target_checked"]
    assert result["false_target_rejected"] and result["forged_body_rejected"]
    assert result["IR_parents_closed"] == result["library_admissions"] == 0
    assert result["independent_lean_checked"] is False


@pytest.mark.parametrize("field,value", (
    ("case", "RF002"), ("status", "solver_said_unsat"),
    ("target_ast_sha256", "0"*64), ("bundle_sha256", "0"*64),
))
def test_changed_contract_or_digest_rejected(recorded, field, value):
    altered = deepcopy(recorded)
    altered[field] = value
    with pytest.raises(ValueError):
        wave.replay("RF001", altered)


def test_changed_source_pins_rejected(recorded):
    altered = deepcopy(recorded)
    altered["source_pins"] = {}
    with pytest.raises(ValueError, match="unbound"):
        wave.replay("RF001", altered)


@pytest.mark.parametrize("kind", ("different_original_goal", "forged_body", "fake_dependency"))
def test_resealed_hostile_certificate_cannot_self_authorize(recorded, kind):
    altered = deepcopy(recorded)
    tree = json.loads(altered["bundle"])
    if kind == "different_original_goal":
        tree[2] = ["bot"]
    elif kind == "forged_body":
        tree[3][tree[1]][3] = ["eq_refl", ["zero"]]
    else:
        tree[3][tree[1]][2] = [tree[1]]
    altered["bundle"] = json.dumps(tree, separators=(",", ":"))+"\n"
    altered["bundle_sha256"] = sha256(altered["bundle"].encode()).hexdigest()
    with pytest.raises((ValueError, ProofBundleError)):
        wave.replay("RF001", altered)


def test_unknown_case_has_no_ambient_target_lookup():
    for identifier in ("invented_theorem", "P04-invented", [], None):
        with pytest.raises(ValueError):
            wave.target_for(identifier)


def test_target_binding_never_contains_proof_generation_dispatch():
    module = ast.parse(wave.SCRIPT.read_text())
    target = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "target_for")
    for node in ast.walk(target):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert not node.func.id.startswith(("prove_", "reconstruct_", "check_"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert not node.func.attr.startswith(("prove_", "reconstruct_", "check_"))
        if isinstance(node, ast.ImportFrom):
            assert not any(n.name.startswith(("prove_", "reconstruct_", "check_")) for n in node.names)
