"""All-exponents evaluation preserves whole support, units and scaling."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_finite_power_evaluation as evaluation


def test_exact_constructed_power_and_all_value_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = evaluation.frozen_finite_power_evaluation_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==6 and len(premises)==1 and type(conclusion) is Exists
    assert evaluation.json_hash(encode_formula(target))==evaluation.TARGET_SHA256
    assert len(evaluation.canonical(encode_formula(target)))==17227
    c = evaluation.source_contract()
    assert c["actual_power_trace_constructed"] is c["actual_input_horner_and_two_scaling_powers_constructed"] is True
    assert c["all_supplied_row_values_through_K"] is c["unit_at_exponent_zero_retained"] is True
    assert c["zero_multiplier_and_empty_input_allowed"] is c["no_nonzero_factor_cancelled"] is True
    assert c["support_complete_width"]=="1+K*L <= J+1"
    assert c["arbitrary_truncation_evaluation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_power_and_horner_definitions_are_unchanged():
    registry = evaluation.definition_registry()
    assert evaluation.source_contract()["new_definition_ids"]==[]
    for name,d in evaluation.power_registry().items():
        assert registry[name].template_formula==d.template_formula
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_omitted_width_or_scaling_is_rejected():
    for source in (evaluation.NAMED_SOURCE.replace(evaluation.WIDTH+" -> ",""),
                   evaluation.NAMED_SOURCE.replace("a*y=(v*b)*c","y=c"),
                   evaluation.NAMED_SOURCE.replace("Pow(p,k,a) -> ",""),
                   evaluation.NAMED_SOURCE.replace("NatPowerRow(pb,pc,qb,qc,k,ub,uc) -> ","")):
        with patch.object(evaluation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            evaluation.frozen_finite_power_evaluation_target()


def test_helper_targets_and_owned_actual_ancestors():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = evaluation.definition_registry()
    assert {n:evaluation.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in evaluation.HELPER_SOURCES.items()}==evaluation.HELPER_TARGET_SHA256
    found = set()
    for pin in evaluation.ARCHIVES:
        rows = evaluation.read_mixed_archive(pin)
        for name,source in evaluation.ENDPOINT_SOURCES.items():
            if evaluation.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==evaluation.ENDPOINT_SOURCES.keys()


def test_changed_archives_and_invalid_multiplicative_reconstruction():
    from peano_lab.kernel.terms import Mul,Var
    from sqrt2_power_quadratic_trace_exists import Scope
    for original in evaluation.ARCHIVES:
        changed = dict(original);changed["sha256"] = "0"*64
        with pytest.raises(ValueError):
            evaluation.read_mixed_archive(changed)
    scope = Scope().hypothesis("mul_assoc").hypothesis("mul_comm")
    with pytest.raises(ValueError):
        evaluation._multiplicative_equal(scope,Var(0),Var(1))
    term = Var(0)
    for _ in range(16):
        term = Mul(Var(0),term)
    with pytest.raises(ValueError):
        evaluation._multiplicative_equal(scope,term,term)


def test_all_exponents_model_and_missing_width_counterexample():
    def horner(coefficients,t):
        y = 0
        for a in coefficients:
            y = t*y+a
        return y
    def convolve(A,B,H):
        return [sum(A[i]*B[j-i] for i in range(len(A)) if 0<=j-i<len(B)) for j in range(H)]
    for A in ([],[0],[2],[1,2],[0,1,2]):
        L = len(A)
        for K in range(4):
            for padding in range(2):
                J = K*L+padding;H = J+1
                row = [1]+[0]*J
                for k in range(K+1):
                    for t in range(4):
                        x,p,v = horner(A,t),t**L,t**J
                        y = horner(row,t)
                        assert p**k*y==(v*t**k)*x**k
                    row = convolve(A,row,H)
    A,row,t = [1,1],[1],3
    assert (t**len(A))*horner(convolve(A,row,1),t)!=(t**0*t)*horner(A,t)


def test_ordinary_replay_and_forged_unit_value_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = evaluation.prove_finite_power_evaluation()
    assert result.receipt.target==evaluation.frozen_finite_power_evaluation_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(evaluation.HELPER_SOURCES["unit_value"],registry=evaluation.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
