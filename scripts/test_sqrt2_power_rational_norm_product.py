"""RN002 exact original HA, denominator, model and hostile-certificate tests."""
from dataclasses import replace
from hashlib import sha256
import itertools
import sys

import pytest
import sqrt2_power_rational_norm_product as norm
from sqrt2_power_binary_dag import BinaryDAGLimits
from sqrt2_power_native import strip_target
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Forall, Imp, pretty_formula
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import ProofBundleError, check_encoded_proof_bundle, check_proof_bundle


@pytest.fixture(scope="module")
def certificate():
    return norm.prove_rational_norm_product()


def curried(bundle,node):
    target = node.target
    for i in reversed(node.dependencies):
        target = Imp(bundle.nodes[i].target,target)
    return target


def test_exact_named_formula_and_denominator_contract():
    target = norm.frozen_rational_norm_product_target()
    assert norm.formula_sha256(target) == norm.TARGET_SHA256
    binders,premises,_ = strip_target(target)
    assert binders == 20 and len(premises) == 10
    assert "IRatMul(a,2*b,u*u,c,2*d,v*v,r,2*t,(u*v)*(u*v))" in norm.NAMED_SOURCE
    assert norm.closed_formula(pretty_formula(target,[])) == target
    assert "peano_lab.library.theorems" not in sys.modules


def test_source_pins_and_unchanged_parent():
    pins = norm.rational_norm_product_source_pins()
    assert pins["scripts/sqrt2_power_quadratic_norm_product.py"]["sha256"] == norm.PARENT_PRODUCER_SHA256
    for name,pin in pins.items():
        raw = (norm.ROOT/name).read_bytes()
        assert pin == dict(bytes=len(raw),sha256=sha256(raw).hexdigest())


def test_host_signed_models_include_negative_shifted_and_unequal_denominators():
    # Counterexample/model calibration only, never universal proof authority.
    for A,B,C,D in itertools.product(range(-2,3),repeat=4):
        for u,v in ((1,1),(2,3),(7,2)):
            R,T = A*C+2*B*D,A*D+B*C
            a,b,c,d,r,t = A*A,B*B,C*C,D*D,R*R,T*T
            assert (r-2*t)*(u*u)*(v*v) == (a*c+4*b*d-2*(a*d+b*c))*(u*v)**2
            for shift in (0,5):
                rp,rn = max(R,0)+shift,max(-R,0)+shift
                assert rp*rp+rn*rn == r+rp*rn+rn*rp
    assert (2*3)**2 != 2*3  # The missing-square variant is genuinely different.


def test_fresh_original_ha_and_complete_parent_replay(certificate):
    result = certificate
    assert result.target == result.receipt.target == norm.frozen_rational_norm_product_target()
    assert len(result.bundle.nodes) == result.receipt.kernel_calls == 46
    assert result.receipt.total_body_nodes == 42483
    assert result.bundle.nodes[result.bundle.root].dependencies[0] == 36
    assert result.provenance["SN003_bundle_sha256"] == norm.PARENT_BUNDLE_SHA256
    assert result.provenance["IR_parents_closed"] == result.provenance["library_admissions"] == 0
    assert result.provenance["new_definitions"] == result.provenance["new_axioms"] == []
    assert check_encoded_proof_bundle(result.payload).target == result.target


def test_omitting_any_premise_or_denominator_square_does_not_reuse_proof(certificate):
    bundle = certificate.bundle
    root = bundle.nodes[bundle.root]
    binders,premises,conclusion = strip_target(root.target)
    for omitted in range(len(premises)):
        changed = conclusion
        for i in reversed(range(len(premises))):
            if i != omitted:
                changed = Imp(premises[i],changed)
        for _ in range(binders):
            changed = Forall(changed)
        assert not check((),root.body,curried(bundle,replace(root,target=changed)))
    changed_source = norm.NAMED_SOURCE.replace("r,2*t,(u*v)*(u*v))","r,2*t,u*v)")
    changed = norm.parse_named(changed_source,registry=norm.definition_registry())
    assert changed != root.target
    assert not check((),root.body,curried(bundle,replace(root,target=changed)))


def test_forged_root_ancestor_and_missing_parent_rejected(certificate):
    bundle = certificate.bundle
    for identifier in (0,bundle.root):
        nodes = tuple(replace(n,body=EqRefl(Zero())) if n.node_id == identifier else n for n in bundle.nodes)
        with pytest.raises(ProofBundleError):
            check_proof_bundle(replace(bundle,nodes=nodes),certificate.target)
    root = bundle.nodes[bundle.root]
    nodes = (*bundle.nodes[:-1],replace(root,dependencies=root.dependencies[1:]))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(replace(bundle,nodes=nodes),certificate.target)


def test_resource_limits_fail_closed_before_large_generation():
    with pytest.raises(norm.RationalNormProductError,match="node budget"):
        norm.prove_rational_norm_product(limits=BinaryDAGLimits(max_nodes=45))
    with pytest.raises(norm.RationalNormProductError,match="resource limits"):
        norm.prove_rational_norm_product(limits={})


def test_changed_target_and_parent_pins_fail_closed(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(norm,"TARGET_SHA256","0"*64)
        with pytest.raises(norm.RationalNormProductError,match="target AST"):
            norm.frozen_rational_norm_product_target()
    with monkeypatch.context() as m:
        m.setattr(norm,"PARENT_PRODUCER_SHA256","0"*64)
        with pytest.raises(norm.RationalNormProductError,match="producer changed"):
            norm.rational_norm_product_source_pins()
