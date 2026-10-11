"""Pointwise weighted order is conservative notation; finite sum bounds are proved."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_sum_linear_bound as bound


def test_exact_three_supplied_sums_and_pointwise_bound_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=bound.frozen_sum_linear_bound_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==13 and len(premises)==4 and type(conclusion) is Exists
    assert len(bound.canonical(encode_formula(target)))==5249
    c=bound.source_contract()
    assert c["three_supplied_sum_values_preserved"] is c["explicit_pointwise_bound_required"] is True
    assert c["independent_input_and_sum_history_codes_allowed"] is c["empty_prefix_and_zero_weights_allowed"] is True
    assert c["definition_contains_sum_or_accuracy_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False
    assert c["new_definition_ids"]==["ND0445"]
    assert c["definition_admissions"]==c["IR_parents_closed"]==0


def test_exact_conservative_definition_dag_and_roundtrip_without_sum():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import parse_formula_in_context,pretty_formula
    from peano_lab.library.proof_bundle import encode_formula
    base=bound.base_registry();registry=bound.definition_registry()
    assert set(registry)==set(base)|{"NatLinearBound"}
    assert all(registry[name]==definition for name,definition in base.items())
    identifier,name,params,source,deps,digest=bound.DEFINITIONS[0]
    assert identifier=="ND0445" and name=="NatLinearBound"
    assert deps==("Lt","BetaAt","Le") and set(deps)<=base.keys()
    assert "Sum(" not in source and "Approx" not in source
    expanded=parse_named(source,params,base)
    assert registry[name].template_formula==expanded
    assert parse_formula_in_context(pretty_formula(expanded,list(params)),list(params))==expanded
    assert bound.json_hash(encode_formula(expanded))==digest


def test_definition_collision_forward_dependency_and_changed_expansion_rejected():
    original=bound.DEFINITIONS[0]
    old=next(iter(bound.base_registry().values()))
    bad=(
        (old.stable_id,)+original[1:],
        original[:4]+(("FutureBound",),)+original[5:],
        original[:3]+(original[3].replace("Le(gamma*c,alpha*a+beta*b)","Le(alpha*a+beta*b,gamma*c)"),)+original[4:],
    )
    for definition in bad:
        with patch.object(bound,"DEFINITIONS",(definition,)),pytest.raises(ValueError):
            bound.definition_registry()


def test_changed_actual_sums_weight_or_pointwise_premise_is_rejected():
    original=bound.NAMED_SOURCE
    registry=bound.definition_registry()
    for source in (original.replace(bound.GRAPH+" -> ",""),
                   original.replace("Sum(ab,ac,N,u) -> ",""),
                   original.replace("Sum(cb,cc,N,w)","Sum(cb,cc,S N,w)"),
                   original.replace("Le(gamma*w,alpha*u+beta*v)","Le(gamma*u,alpha*w+beta*v)")):
        assert source!=original
        with patch.object(bound,"definition_registry",return_value=registry),patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_sum_linear_bound_target()


def test_owned_actual_sum_decomposition_and_order_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=bound.definition_registry();found=set()
    for pin in bound.ARCHIVES:
        rows=bound.read_mixed_archive(pin)
        for name,source in bound.ENDPOINT_SOURCES.items():
            if bound.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            bound.read_mixed_archive(altered)
    assert found==bound.ENDPOINT_SOURCES.keys()


def test_finite_weighted_order_models_empty_prefix_and_zero_weights():
    for N in range(9):
        A=[i%3+1 for i in range(N)];B=[(2*i+1)%5 for i in range(N)]
        for alpha in range(4):
            for beta in range(4):
                for gamma in range(4):
                    C=[(alpha*a+beta*b)//gamma if gamma else 7*i for i,(a,b) in enumerate(zip(A,B))]
                    assert all(gamma*c<=alpha*a+beta*b for a,b,c in zip(A,B,C))
                    assert gamma*sum(C)<=alpha*sum(A)+beta*sum(B)
    # Three sums by themselves do not imply a pointwise-majorized total.
    assert sum([1])>sum([0])+sum([0])


def test_complete_ordinary_replay_with_one_explicit_induction_no_axioms():
    result=bound.prove_sum_linear_bound()
    assert result.receipt.target==bound.frozen_sum_linear_bound_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_weighted_combination_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=bound.prove_sum_linear_bound();node=result.provenance["helper_bundle_indices"]["combine"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
