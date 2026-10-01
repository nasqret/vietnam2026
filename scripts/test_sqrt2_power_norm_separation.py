"""SN002/NG001 original-kernel, exact-source, model, and hostile-input checks.

Root owns execution. Host integers below only check models/counterexamples;
they are never substitutes for the checked universal ordinary proof bundles.
"""
from dataclasses import replace
from hashlib import sha256
import json
import sys

import pytest

import sqrt2_power_norm_separation as separation
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Exists, Forall, Imp, Or
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import (
    ProofBundleError, check_encoded_proof_bundle, check_proof_bundle, encode_proof,
)


@pytest.fixture(scope="module")
def gap_certificate():
    return separation.prove_natural_gap()


@pytest.fixture(scope="module")
def norm_certificate():
    return separation.prove_norm_separation()


def _curried(bundle, node):
    formula = node.target
    for dependency in reversed(node.dependencies):
        formula = Imp(bundle.nodes[dependency].target, formula)
    return formula


def _omit_premise(index):
    formula = separation.frozen_norm_separation_target()
    for _ in range(6):
        formula = formula.body
    premises = []
    for _ in range(3):
        assert type(formula) is Imp
        premises.append(formula.left)
        formula = formula.right
    assert type(formula) is Exists
    for i in reversed(range(3)):
        if i != index:
            formula = Imp(premises[i], formula)
    for _ in range(6):
        formula = Forall(formula)
    return formula


def test_exact_frozen_statements_and_existing_nd0157_roundtrip():
    from sqrt2_power_definitions import parse_named
    definition = separation.signed_difference_definition()
    assert definition.stable_id == "ND0157"
    named = ("forall ap an bp bn s t. SignedDifferenceSquare(ap,an,s) -> "
        "SignedDifferenceSquare(bp,bn,t) -> ~(ap=an /\\ bp=bn) -> "
        "exists k. (s+S k=(S(S 0))*t \\/ (S(S 0))*t+S k=s)")
    target = parse_named(named, registry={definition.name: definition})
    assert target == separation.frozen_norm_separation_target()
    assert separation.formula_sha256(target) == separation.NORM_SEPARATION_TARGET_SHA256
    gap = separation.frozen_natural_gap_target()
    assert separation.formula_sha256(gap) == separation.NATURAL_GAP_TARGET_SHA256
    assert type(gap.body.body.right) is Exists
    assert type(gap.body.body.right.body) is Or
    assert "peano_lab.library.theorems" not in sys.modules


def test_small_source_map_and_actual_trichotomy_body_provenance():
    pins = separation.norm_separation_source_pins()
    assert str(separation.signed.V28_ARTIFACT.relative_to(separation.ROOT)) not in pins
    for name, row in pins.items():
        raw = (separation.ROOT / name).read_bytes()
        assert row == {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        assert len(raw) <= 16 * 1024**2
    node = separation.load_frozen_trichotomy()
    original = json.loads(separation.signed._read_v28(separation.signed.V28_ARTIFACT))[3][48]
    assert node.dependencies == ()
    assert encode_proof(node.body) == original[3]
    assert node.fuel == original[0]
    assert separation.signed._json_hash(original) == separation.TRICHOTOMY_ROW_SHA256
    assert separation.formula_sha256(node.target) == separation.TRICHOTOMY_TARGET_SHA256


@pytest.mark.parametrize("ap,an,bp,bn,expected_gap", (
    (0, 1, 0, 1, 1),       # negative representatives; norm -1
    (0, 3, 0, 2, 1),       # negative representatives; norm +1
    (4, 7, 5, 7, 1),       # same values after harmless common shifts
    (1, 0, 0, 0, 1),
    (0, 0, 1, 0, 2),
    (6, 1, 7, 10, 7),
))
def test_signed_gap_models_not_proof_receipts(ap, an, bp, bn, expected_gap):
    s, t = (ap-an)**2, (bp-bn)**2
    assert not (ap == an and bp == bn)
    assert s != 2*t
    k = abs(s-2*t)-1
    assert k >= 0 and k+1 == expected_gap
    assert s+k+1 == 2*t or 2*t+k+1 == s


@pytest.mark.parametrize("a,b", ((0, 1), (1, 0), (3, 19), (19, 3)))
def test_natural_gap_independent_models(a, b):
    assert a != b
    k = abs(a-b)-1
    assert k >= 0 and (a+k+1 == b or b+k+1 == a)


@pytest.mark.parametrize("omitted,values", (
    (0, (1, 0, 0, 0, 0, 0)),
    (1, (0, 0, 1, 0, 0, 0)),
    (2, (5, 5, 7, 7, 0, 0)),
))
def test_each_omitted_norm_premise_has_a_counterexample(omitted, values):
    ap, an, bp, bn, s, t = values
    premises = (ap*ap+an*an == s+ap*an+an*ap,
                bp*bp+bn*bn == t+bp*bn+bn*bp,
                not (ap == an and bp == bn))
    assert all(p for i, p in enumerate(premises) if i != omitted)
    # Equal naturals cannot have a positive additive gap in either direction.
    assert s == 2*t
    assert _omit_premise(omitted) != separation.frozen_norm_separation_target()


def test_wrong_coefficient_and_stronger_gap_have_counterexamples():
    # Two genuine squares of a nonzero signed pair become equal with coefficient1.
    ap, an, bp, bn = 1, 0, 1, 0
    s, t = (ap-an)**2, (bp-bn)**2
    assert not (ap == an and bp == bn) and s == 1*t
    # Even coefficient2 permits gap exactly1, not a universally stronger gap>=2.
    assert abs(s-2*t) == 1


def test_removing_natural_inequality_guard_has_counterexample():
    a = b = 7
    assert a == b  # hence no positive k+1 can bridge the equality


def test_ng001_original_ha_and_fresh_canonical_replay(gap_certificate):
    result = gap_certificate
    assert result.target == result.receipt.target == separation.frozen_natural_gap_target()
    assert result.target_ast_sha256 == separation.NATURAL_GAP_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 3
    assert result.bundle.nodes[2].dependencies == (0, 1)
    assert result.provenance["trichotomy_original_node"] == 48
    assert result.provenance["trichotomy_original_dependencies"] == []
    assert check_encoded_proof_bundle(result.payload).target == result.target


def test_sn002_all_bodies_and_fresh_canonical_replay(norm_certificate):
    result = norm_certificate
    assert result.target == result.receipt.target == separation.frozen_norm_separation_target()
    assert result.target_ast_sha256 == separation.NORM_SEPARATION_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 210
    assert result.bundle.root == 209
    assert result.bundle.nodes[209].dependencies == (205, 208)
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.provenance["SN001_replayed_nodes"] == 206
    assert result.provenance["NG001_replayed_nodes"] == 3
    assert result.provenance["definition"]["id"] == "ND0157"
    assert result.provenance["definition"]["new_definition"] is False
    assert result.provenance["IR_parents_closed"] == result.provenance["library_admissions"] == 0
    assert check_encoded_proof_bundle(result.payload).target == result.target
    assert "peano_lab.library.theorems" not in sys.modules


@pytest.mark.parametrize("omitted", (0, 1, 2))
def test_native_rejects_omitted_norm_premise(norm_certificate, omitted):
    bundle = norm_certificate.bundle
    root = bundle.nodes[bundle.root]
    changed = _omit_premise(omitted)
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(bundle, changed)


def test_native_rejects_wrong_coefficient_gap_and_body(norm_certificate):
    bundle = norm_certificate.bundle
    root = bundle.nodes[bundle.root]
    for source in (separation.NORM_SEPARATION_SOURCE.replace("(S(S 0))*t", "(S 0)*t"),
                   separation.NORM_SEPARATION_SOURCE.replace("+S k", "+S(S k)")):
        changed = separation.closed_formula(source)
        assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    missing = replace(root, dependencies=(205,))
    assert not check((), missing.body, _curried(bundle, missing))


def test_native_rejects_missing_ng_guard_and_forged_trichotomy(gap_certificate):
    bundle = gap_certificate.bundle
    root = bundle.nodes[2]
    changed = separation.closed_formula(r"forall a b. exists k. (a+S k=b \/ b+S k=a)")
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    forged = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(forged, *bundle.nodes[1:])), gap_certificate.target)


def test_changed_target_and_archive_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(separation, "NORM_SEPARATION_SOURCE",
                        separation.NORM_SEPARATION_SOURCE.replace("(S(S 0))*t", "(S 0)*t"))
    with pytest.raises(separation.NormSeparationError, match="target AST pin"):
        separation.frozen_norm_separation_target()
    monkeypatch.setattr(separation, "NATURAL_GAP_SOURCE", "0=0")
    with pytest.raises(separation.NormSeparationError, match="target AST pin"):
        separation.frozen_natural_gap_target()
    artifact = tmp_path / "changed-v28.json"
    artifact.write_bytes(b"[]\n")
    with pytest.raises(separation.signed.SignedNormError, match="size/source hash"):
        separation.load_frozen_trichotomy(artifact)


@pytest.mark.parametrize("case,cap", (("NG001", 2), ("SN002", 209)))
def test_node_caps_fail_before_any_proof_generation(monkeypatch, case, cap):
    def forbidden(*_a, **_k):
        raise AssertionError("node budget reached a proof producer")
    monkeypatch.setattr(separation, "Basis", forbidden)
    monkeypatch.setattr(separation.signed, "prove_signed_norm_zero", forbidden)
    producer = separation.prove_natural_gap if case == "NG001" else separation.prove_norm_separation
    with pytest.raises(separation.NormSeparationError, match="node budget"):
        producer(limits=separation.BinaryDAGLimits(max_nodes=cap))
