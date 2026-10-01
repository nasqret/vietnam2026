"""SN001 exact-target, provenance, signed-model, and adversarial checks.

Root owns native execution. Finite models are explicitly not proof receipts;
the universal claim requires actual original-HA canonical-bundle replay.
"""
from dataclasses import replace
from hashlib import sha256
import json
import sys

import pytest

import sqrt2_power_signed_norm as signed
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Forall, Imp
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Var, Zero
from peano_lab.library.proof_bundle import (
    ProofBundleError, check_encoded_proof_bundle, check_proof_bundle, encode_proof,
)


@pytest.fixture(scope="module")
def certificate():
    return signed.prove_signed_norm_zero()


def _curried(bundle, node):
    formula = node.target
    for dependency in reversed(node.dependencies):
        formula = Imp(bundle.nodes[dependency].target, formula)
    return formula


def _omit_premise(index):
    formula = signed.frozen_signed_norm_target()
    for _ in range(6):
        assert type(formula) is Forall
        formula = formula.body
    premises = []
    for _ in range(3):
        assert type(formula) is Imp
        premises.append(formula.left)
        formula = formula.right
    assert type(formula) is And
    for i in reversed(range(3)):
        if i != index:
            formula = Imp(premises[i], formula)
    for _ in range(6):
        formula = Forall(formula)
    return formula


def _model(ap, an, bp, bn, s, t, coefficient=2):
    return (ap*ap + an*an == s + ap*an + an*ap,
            bp*bp + bn*bn == t + bp*bn + bn*bp,
            s == coefficient*t), (ap == an and bp == bn)


def test_exact_target_and_reused_registered_definition_roundtrip():
    from sqrt2_power_definitions import parse_named
    definition = signed.signed_difference_definition()
    assert definition.stable_id == "ND0157"
    assert definition.name == "SignedDifferenceSquare"
    assert definition.parameters == ("p", "n", "s")
    assert definition.conceptual_dependencies == ()
    assert definition.template_formula == signed.signed_square(Var(0), Var(1), Var(2))
    assert sha256(definition.template_source.encode()).hexdigest() == signed.DEFINITION_EXPANSION_SHA256
    target = parse_named(
        "forall ap an bp bn s t. SignedDifferenceSquare(ap,an,s) -> "
        "SignedDifferenceSquare(bp,bn,t) -> s=(S(S 0))*t -> (ap=an /\\ bp=bn)",
        registry={definition.name: definition})
    assert target == signed.frozen_signed_norm_target()
    assert signed.formula_sha256(target) == signed.SIGNED_NORM_TARGET_SHA256
    # The established alias also survives binder names shared with parameters.
    shadowed = parse_named("forall s p n. SignedDifferenceSquare(s,n,p)",
                          registry={definition.name: definition})
    assert shadowed == signed.closed_formula("forall s p n. s*s+n*n=p+(s*n+n*s)")


def test_archive_source_map_excludes_large_v28_but_records_actual_sources():
    pins = signed.signed_norm_source_pins()
    assert str(signed.V28_ARTIFACT.relative_to(signed.ROOT)) not in pins
    assert str(signed.even.FERMAT_ARTIFACT.relative_to(signed.ROOT)) in pins
    assert "scripts/sqrt2_power_signed_norm.py" in pins
    assert signed.DEFINITION_PARENT in pins
    for name, row in pins.items():
        raw = (signed.ROOT / name).read_bytes()
        assert row == {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        assert len(raw) <= 16 * 1024**2
    assert "peano_lab.library.theorems" not in sys.modules


def test_selected_22_node_cone_retains_actual_bodies_and_ordered_dependencies():
    cone = signed.load_signed_square_cone()
    assert cone.original_ids == signed.ANCESTOR_IDS
    assert len(cone.nodes) == 22
    assert sum(len(n.dependencies) for n in cone.nodes) == 34
    assert signed._json_hash(cone.original_ids) == signed.ANCESTOR_IDS_SHA256
    # Inert raw JSON comparison; this is provenance checking, not acceptance.
    value = json.loads(signed._read_v28(signed.V28_ARTIFACT))
    remap = {old: new for new, old in enumerate(cone.original_ids)}
    for node, old in zip(cone.nodes, cone.original_ids):
        row = value[3][old]
        assert node.fuel == row[0]
        assert signed.encode_formula(node.target) == row[1]
        assert encode_proof(node.body) == row[3]
        assert node.dependencies == tuple(remap[d] for d in row[2])
    for old, pin in signed.ENDPOINTS.items():
        node = cone.nodes[cone.endpoints[old]]
        assert node.target == signed.closed_formula(pin["source"])
        assert signed.formula_sha256(node.target) == pin["target_sha256"]


@pytest.mark.parametrize("ap,an,bp,bn,norm", (
    (0, 3, 0, 2, 1),       # (-3)^2 - 2*(-2)^2 = 1
    (4, 7, 5, 7, 1),       # same signed values, nonnormalized representatives
    (0, 1, 0, 1, -1),      # signed norm can be negative
    (6, 1, 7, 10, 7),      # positive and negative coefficients
    (5, 5, 7, 7, 0),       # zero values do NOT mean all raw parts are zero
    (0, 0, 0, 0, 0),
))
def test_exact_signed_integer_cases_are_model_checks_only(ap, an, bp, bn, norm):
    s, t = (ap-an)**2, (bp-bn)**2
    premises, conclusion = _model(ap, an, bp, bn, s, t)
    assert premises[:2] == (True, True)
    assert s - 2*t == norm
    if all(premises):
        assert conclusion
    else:
        assert norm != 0


def test_nonzero_raw_components_are_permitted_in_true_zero_case():
    premises, conclusion = _model(5, 5, 7, 7, 0, 0)
    assert all(premises) and conclusion
    assert not (5 == 0 and 7 == 0)


@pytest.mark.parametrize("omitted,values", (
    (0, (1, 0, 0, 0, 0, 0)),
    (1, (0, 0, 1, 0, 0, 0)),
    (2, (1, 0, 0, 0, 1, 0)),
))
def test_omitting_any_premise_has_an_independent_counterexample(omitted, values):
    premises, conclusion = _model(*values)
    assert all(p for i, p in enumerate(premises) if i != omitted)
    assert not conclusion
    assert _omit_premise(omitted) != signed.frozen_signed_norm_target()


def test_coefficient_one_has_an_independent_counterexample():
    premises, conclusion = _model(1, 0, 1, 0, 1, 1, coefficient=1)
    assert all(premises) and not conclusion


def test_native_full_bundle_and_fresh_canonical_replay(certificate):
    result = certificate
    assert result.target == result.receipt.target == signed.frozen_signed_norm_target()
    assert result.target_ast_sha256 == signed.SIGNED_NORM_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 206
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.bundle.root == 205
    assert result.bundle.nodes[205].dependencies == (181, 202, 201, 203, 204)
    assert check_encoded_proof_bundle(result.payload).target == result.target
    provenance = result.provenance
    assert provenance["definition"]["id"] == "ND0157"
    assert provenance["definition"]["new_definition"] is False
    assert provenance["v28_selected_nodes"] == 22
    assert provenance["v28_artifact_sha256"] == signed.V28_ARTIFACT_SHA256
    assert provenance["v28_artifact_bytes"] == signed.V28_ARTIFACT_SIZE
    assert provenance["ir016_replayed_nodes"] == 182
    assert provenance["IR_parents_closed"] == provenance["library_admissions"] == 0
    assert "peano_lab.library.theorems" not in sys.modules


@pytest.mark.parametrize("omitted", (0, 1, 2))
def test_native_rejects_omitted_square_or_zero_norm_hypothesis(certificate, omitted):
    changed = _omit_premise(omitted)
    root = certificate.bundle.nodes[certificate.bundle.root]
    assert not check((), root.body, _curried(certificate.bundle, replace(root, target=changed)))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(certificate.bundle, changed)


def test_native_rejects_wrong_coefficient_and_forged_body(certificate):
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    changed = signed.closed_formula(signed.SIGNED_NORM_SOURCE.replace("(S(S 0))*t", "(S 0)*t"))
    assert not check((), root.body, _curried(bundle, replace(root, target=changed)))
    assert not check((), EqRefl(Zero()), _curried(bundle, root))
    omitted = replace(root, dependencies=root.dependencies[:-1])
    assert not check((), omitted.body, _curried(bundle, omitted))
    # Full bundle mutation fails immediately on node0: no acceptance merely
    # because the new root was generated from apparently correct equations.
    first = replace(bundle.nodes[0], body=EqRefl(Zero()))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(replace(bundle, nodes=(first,) + bundle.nodes[1:]), bundle.nodes[bundle.root].target)


def test_modified_target_definition_and_archive_fail_closed(monkeypatch, tmp_path):
    original = signed.SIGNED_NORM_SOURCE
    monkeypatch.setattr(signed, "SIGNED_NORM_SOURCE", original.replace("(S(S 0))*t", "(S 0)*t"))
    with pytest.raises(signed.SignedNormError, match="target AST pin"):
        signed.frozen_signed_norm_target()
    monkeypatch.setattr(signed, "SIGNED_NORM_SOURCE", original)
    monkeypatch.setattr(signed, "DEFINITION_TEMPLATE", "p=p")
    with pytest.raises(signed.SignedNormError, match="expansion source"):
        signed.signed_difference_definition()
    artifact = tmp_path / "changed-v28.json"
    raw = signed.V28_ARTIFACT.read_bytes()
    # Preserve size, corrupt content: a byte pin is required in addition to size.
    artifact.write_bytes(b" " + raw[1:])
    assert artifact.stat().st_size == signed.V28_ARTIFACT_SIZE
    with pytest.raises(signed.SignedNormError, match="size/source hash"):
        signed.load_signed_square_cone(artifact)


def test_node_cap_stops_before_any_new_proof_worker_work(monkeypatch):
    def forbidden(*_a, **_k):
        raise AssertionError("node cap reached native IR016 producer")
    monkeypatch.setattr(signed.even, "prove_ir016", forbidden)
    with pytest.raises(signed.SignedNormError, match="node budget"):
        signed.prove_signed_norm_zero(limits=signed.BinaryDAGLimits(max_nodes=205))
