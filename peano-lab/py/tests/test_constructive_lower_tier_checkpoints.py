"""Actual HA/Lean closures, exact sources, hostile proofs, and honest counts."""

from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_bottom_layer_checkpoints as previous
import constructive_lower_tier_checkpoints as checkpoints
import constructive_lower_tier_support as support
from peano_lab.kernel.proofs import EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import ProofBundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


def test_exact_new_inventory_and_immutable_earlier_authority_boundaries():
    assert [(item.slug, item.frontier_count) for item in checkpoints.CHECKPOINTS] == [
        ("divisor-sums", 37), ("signed-weighted-sums", 40), ("prime-field-polynomials", 49),
    ]
    rows = checkpoints.all_new_rows()
    assert len(rows) == len({row.name for row in rows}) == 126
    assert len(support.previous_rows()) == 170
    assert support.closure.PARENT_COUNT == 3222
    assert checkpoints.LEAN_BINARY_SHA256 == previous.LEAN_BINARY_SHA256
    assert checkpoints.LEAN_BINARY_BYTES == 106_787_344
    assert [(item.slug, item.frontier_count) for item in previous.CHECKPOINTS] == [
        ("euler-units", 32), ("prime-fields", 87), ("mobius-values", 21), ("signed-sums", 30),
    ]


def test_exact_ast_novelty_against_all_3392_prior_statements_and_each_new_row():
    assert support.statement_duplicates(checkpoints.all_new_rows()) == ()


@pytest.fixture(scope="module", params=checkpoints.CHECKPOINTS, ids=lambda item: item.slug)
def actual_evidence(request):
    # Real unchanged original HA and pinned compiled Lean.  No receipt flag,
    # monkeypatched proof checker or assumed old checkpoint supplies evidence.
    return checkpoints.verify_checkpoint(request.param)


def test_every_real_bundle_body_is_checked_and_support_is_not_counted_as_new(actual_evidence):
    evidence = actual_evidence
    report, selection = evidence.report, evidence.selection
    assert report["new_theorem_count"] == len(evidence.owned) == evidence.checkpoint.frontier_count
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert report["bundle"]["nodes_including_packaging_root"] == len(evidence.plan.rows) + 1
    assert evidence.receipt.kernel_calls == len(evidence.plan.rows) + 1
    inherited = report["support"]
    assert inherited["counted_as_new_owned_theorems"] is False
    assert (report["new_theorem_count"] + inherited["published_non_admitted_count"]
            + inherited["current_cross_track_count"] + inherited["alpha_v30_count"] + 1
            == evidence.receipt.node_count)
    assert tuple(inherited["published_non_admitted_theorems"]) == selection.published_support
    assert tuple(inherited["current_cross_track_theorems"]) == selection.current_support
    assert not set(selection.published_support) & set(selection.current_support)
    assert set(selection.published_support) <= {row.name for row in support.previous_rows()}
    assert set(selection.current_support) <= {row.name for row in checkpoints.all_new_rows()} - {row.name for row in evidence.owned}
    assert set(evidence.plan.root_names) <= {row.name for row in evidence.owned}
    assert report["membership"] == "local_non_admitting_checkpoint"
    assert all(report[key] is False for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"))
    assert all(record["complete_ordinary_ha_checked"] is False for record in report["principal_roots"])
    assert all("ordinary_certificate_nodes" not in record for record in report["principal_roots"])
    payload = (ROOT / evidence.checkpoint.artifact).read_bytes()
    assert len(payload) == evidence.checkpoint.artifact_bytes
    assert sha256(payload).hexdigest() == evidence.checkpoint.artifact_sha256


@pytest.mark.parametrize("mutation", ["false_old_body", "false_new_body", "omitted_support", "missing_premise", "swapped_premises", "wrong_target"])
def test_actual_closed_bundles_reject_corrupt_support_and_targets(actual_evidence, mutation):
    evidence = actual_evidence
    nodes = list(evidence.bundle.nodes)
    old = next(row.node_id for row in evidence.plan.rows
               if evidence.selection.role(row.name) == "inherited_published_non_admitted_checkpoint")
    new = next(row.node_id for row in evidence.plan.rows
               if evidence.selection.role(row.name) == "new_owned_theorem" and len(row.dependencies) > 1)
    target = evidence.target
    if mutation == "false_old_body":
        nodes[old] = replace(nodes[old], body=Hyp(0))
    elif mutation == "false_new_body":
        nodes[new] = replace(nodes[new], body=Hyp(0))
    elif mutation == "omitted_support":
        nodes.pop(old)
    elif mutation == "missing_premise":
        nodes[new] = replace(nodes[new], dependencies=nodes[new].dependencies[1:])
    elif mutation == "swapped_premises":
        dependencies = nodes[new].dependencies
        nodes[new] = replace(nodes[new], dependencies=(dependencies[1], dependencies[0], *dependencies[2:]))
    else:
        target = _closed_formula("0=1")
    with pytest.raises(ValueError):
        checkpoints.closure.check_bottom_layer_bundle(
            evidence.selection.frontier, ProofBundle(tuple(nodes), evidence.bundle.root), target)


@pytest.mark.parametrize("value", [None, False, {}, "divisor-sums"])
def test_unregistered_records_fail_before_source_reads(monkeypatch, value):
    monkeypatch.setattr(previous, "_source_bytes", lambda _: pytest.fail("invalid record read a source"))
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.load_rows(value)


def test_old_and_new_checkpoint_registries_cannot_impersonate_each_other():
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.load_rows(previous.CHECKPOINTS[0])
    with pytest.raises(previous.CheckpointError, match="literal registered"):
        previous.load_rows(checkpoints.CHECKPOINTS[0])
    changed = replace(checkpoints.CHECKPOINTS[0], frontier_count=1)
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.load_rows(changed)


@pytest.mark.parametrize("flag", [None, 0, 1, "yes", (), []])
def test_nonboolean_ordinary_replay_flag_fails_before_source_reads(monkeypatch, flag):
    monkeypatch.setattr(checkpoints, "load_rows", lambda _: pytest.fail("invalid flag read sources"))
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_checkpoint(checkpoints.CHECKPOINTS[0], ordinary_roots=flag)
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_all(ordinary_roots=flag)


@pytest.mark.parametrize("field,value", [
    ("name", "cached_factory_counterfeit"), ("statement", "0=0"), ("dependencies", ()),
    ("script", ("refl",)), ("summary", "counterfeit cached prose"),
])
def test_source_pin_cannot_authenticate_poisoned_cached_factory_output(monkeypatch, field, value):
    checkpoint = checkpoints.CHECKPOINTS[0]
    pin = checkpoint.modules[0]
    module = import_module("peano_lab.library." + pin.module)
    rows = getattr(module, pin.factory)(TheoremSpec)
    assert getattr(rows[0], field) != value
    altered = (replace(rows[0], **{field: value}), *rows[1:])
    monkeypatch.setattr(module, pin.factory, lambda _: altered)
    with pytest.raises(checkpoints.CheckpointError, match="literal ordered"):
        checkpoints.load_rows(checkpoint)


@pytest.mark.parametrize("mutation", ["open_hypothesis", "other_formula", "other_spec"])
def test_ordinary_receipts_require_the_exact_empty_context_certificate(monkeypatch, mutation):
    checkpoint = checkpoints.CHECKPOINTS[0]
    spec = next(row for row in checkpoints.load_rows(checkpoint) if row.name == checkpoint.principal_roots[0])
    replacement = SimpleNamespace(spec=spec, formula=_closed_formula(spec.statement), certificate=Hyp(0), proof_nodes=1)
    if mutation == "other_formula":
        replacement.formula = _closed_formula("0=0")
        replacement.certificate = EqRefl(Zero())
    elif mutation == "other_spec":
        replacement.spec = TheoremSpec("unrelated", "0=0", (), ("refl",), "unrelated")
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: replacement)
    with pytest.raises(checkpoints.CheckpointError, match="empty-context certificate"):
        checkpoints.verify_checkpoint(checkpoint, ordinary_roots=True)


def test_import_and_new_inventory_never_import_admission_code():
    program = (
        "import sys;sys.path[:0]=['scripts','peano-lab/py'];"
        "from constructive_lower_tier_checkpoints import all_new_rows;"
        "assert len(all_new_rows())==126;"
        "assert not any(n.startswith(('peano_lab.library.editions','peano_lab.library.alpha_enrollment')) for n in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", program], cwd=ROOT, check=True, timeout=45)


def test_unfinished_empty_registry_never_produces_a_successful_audit(monkeypatch):
    monkeypatch.setattr(checkpoints, "CHECKPOINTS", ())
    with pytest.raises(checkpoints.CheckpointError, match="no completed"):
        checkpoints.verify_all()
