"""IR016 source provenance, independent model, and original-kernel checks.

Execute in the root-owned supervised worker. No resource failure is an xfail,
and no historical Fermat receipt substitutes for checking its actual bodies.
"""
from dataclasses import replace
from hashlib import sha256
import json
import sys

import pytest

import sqrt2_power_even_square as even
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Forall, Imp
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import (
    ProofBundleError, check_encoded_proof_bundle, check_proof_bundle,
    decode_proof_bundle,
)


def _curried(bundle, node):
    target = node.target
    for dependency in reversed(node.dependencies):
        target = Imp(bundle.nodes[dependency].target, target)
    return target


@pytest.fixture(scope="module")
def certificate():
    return even.prove_ir016()


def test_exact_original_ir016_ast():
    a, b, zero = Var(1), Var(0), Zero()
    expected = Forall(Forall(Imp(
        Eq(Mul(a, a), Mul(Mul(Succ(Succ(zero)), b), b)),
        And(Eq(a, zero), Eq(b, zero)),
    )))
    assert even.frozen_ir016_target() == expected
    assert even.formula_sha256(expected) == even.IR016_TARGET_SHA256


def test_independent_finite_model_and_coefficient_one_counterexample():
    # Only a model check: the universal proof comes from the actual kernel test.
    for a in range(65):
        for b in range(65):
            if a * a == 2 * b * b:
                assert a == b == 0
    # Removing the coefficient two is a mathematically false mutation.
    a = b = 1
    assert a * a == 1 * b * b
    assert not (a == 0 and b == 0)
    altered = even.closed_formula(r"forall a b. a*a=(S 0)*b*b -> (a=0 /\ b=0)")
    assert even.formula_sha256(altered) != even.IR016_TARGET_SHA256


def test_actual_fermat_dependency_provenance_without_registry_import():
    cone = even.load_frozen_fermat_cone()
    assert len(cone.nodes) == 180 and cone.root == 179
    assert sum(len(n.dependencies) for n in cone.nodes) == 450
    assert cone.original_ids[-1] == 211
    assert even._json_hash(cone.original_ids) == even.FERMAT_ANCESTOR_IDS_SHA256
    raw = even.FERMAT_ARTIFACT.read_bytes()
    assert sha256(raw).hexdigest() == even.FERMAT_ARTIFACT_SHA256
    original, _ = decode_proof_bundle(raw.decode())
    remap = {old: new for new, old in enumerate(cone.original_ids)}
    for node, old in zip(cone.nodes, cone.original_ids):
        previous = original.nodes[old]
        assert node.target == previous.target
        assert node.body == previous.body and node.fuel == previous.fuel
        assert node.dependencies == tuple(remap[d] for d in previous.dependencies)
    assert "peano_lab.library.theorems" not in sys.modules


def test_original_ha_and_same_byte_canonical_replay(certificate):
    result = certificate
    assert result.target == result.receipt.target == even.frozen_ir016_target()
    assert result.target_ast_sha256 == even.IR016_TARGET_SHA256
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 182
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.bundle.root == 181
    root = result.bundle.nodes[result.bundle.root]
    assert root.dependencies == (result.fermat_node, result.mul_eq_zero_node) == (179, 180)
    assert result.bundle.nodes[180].dependencies == ()
    assert result.bundle.nodes[179].target == even.closed_formula(even.FERMAT_SOURCE)
    assert check_encoded_proof_bundle(result.payload).target == result.target
    assert result.provenance["fermat_replayed_nodes"] == 180
    assert result.provenance["fermat_artifact_sha256"] == even.FERMAT_ARTIFACT_SHA256
    assert result.provenance["ordinary_HA_checked_from_canonical_bytes"] is True
    assert "peano_lab.library.theorems" not in sys.modules


def test_coefficient_one_goal_is_rejected(certificate):
    altered = even.closed_formula(r"forall a b. a*a=(S 0)*b*b -> (a=0 /\ b=0)")
    root = certificate.bundle.nodes[certificate.bundle.root]
    assert not check((), root.body, _curried(certificate.bundle, replace(root, target=altered)))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(certificate.bundle, altered)


def test_bad_root_body_and_missing_typed_dependency_are_rejected(certificate):
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    bad_root = replace(root, body=EqRefl(Zero()))
    assert not check((), bad_root.body, _curried(bundle, bad_root))
    omitted = replace(root, dependencies=(certificate.fermat_node,))
    assert not check((), omitted.body, _curried(bundle, omitted))
    # Direct ordinary root-body checks avoid repeatedly replaying the full cone
    # merely to demonstrate a local mutation's rejection.
    wrong_law = replace(bundle.nodes[180], target=even.closed_formula("0 = 0"))
    changed = replace(bundle, nodes=bundle.nodes[:180] + (wrong_law, root))
    assert not check((), root.body, _curried(changed, root))


def test_pinned_ancestor_body_and_dependency_mutations_fail_closed(tmp_path):
    raw = even.FERMAT_ARTIFACT.read_bytes()
    for field, value in ((3, ["eq_refl", ["zero"]]), (2, [78, 208])):
        changed = json.loads(raw)
        changed[3][211][field] = value
        artifact = tmp_path / ("altered-" + str(field) + ".json")
        artifact.write_text(json.dumps(changed, separators=(",", ":")) + "\n")
        with pytest.raises(even.EvenSquareError, match="source hash"):
            even.load_frozen_fermat_cone(artifact)


def test_changed_original_target_fails_before_proof_generation(monkeypatch):
    monkeypatch.setattr(even, "IR016_SOURCE", r"forall a b. a*a=(S 0)*b*b -> (a=0 /\ b=0)")
    with pytest.raises(even.EvenSquareError, match="target AST pin"):
        even.frozen_ir016_target()


def test_node_budget_stops_before_basis_replay(monkeypatch):
    def forbidden():
        raise AssertionError("node-cap failure reached native basis replay")
    monkeypatch.setattr(even, "Basis", forbidden)
    with pytest.raises(even.EvenSquareError, match="node budget"):
        even.prove_ir016(limits=even.BinaryDAGLimits(max_nodes=181))
