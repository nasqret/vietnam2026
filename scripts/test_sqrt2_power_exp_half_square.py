"""Half-argument squares are constructed finite estimates, not analytic axioms."""
from dataclasses import replace
from fractions import Fraction
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_exp_half_square as half


def test_exact_constructed_half_argument_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=half.frozen_exp_half_square_target();binders,premises,conclusion=strip_target(target)
    assert binders==8 and len(premises)==6 and type(conclusion) is Exists
    assert len(half.canonical(encode_formula(target)))==15956
    c=half.source_contract()
    assert c['half_normalization_proved_nonzero'] is c['actual_weight_table_terms_factorial_power_head_and_both_sums_constructed'] is True
    assert c['half_argument']=='x/(2*d)' and c['compared_sums_degree']=='n'
    assert c['analytic_half_exponential_square_identity'] is c['logarithm_or_sqrt2_identification'] is c['closes_IR072'] is False


def test_twelve_existing_computation_definitions_form_exact_dag():
    registry=half.definition_registry();pool=half.source_registry();seen=set();ids=set()
    assert len(registry)==12 and 'Sum' in registry
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert half.source_contract()['new_definition_ids']==[]


def test_changed_half_argument_head_degree_and_error_rejected():
    source=half.NAMED_SOURCE;registry=half.definition_registry()
    for changed in (source.replace('2*d','d'),source.replace('~h=0','h=0'),source.replace('(S n)+n','n'),
                    source.replace('Sum(ab,ac,S n,u)','Sum(ab,ac,n,u)'),source.replace('Pow(2,n,p)','Pow(2,S n,p)'),
                    source.replace('2*(b0*(h*h))','b0*(h*h)')):
        assert changed!=source
        with patch.object(half,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            half.frozen_exp_half_square_target(_registry=registry)


def test_actual_construction_product_and_sum_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=half.definition_registry();found={}
    assert {k:half.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in half.HELPER_SOURCES.items()}==half.HELPER_TARGET_SHA256
    for pin in half.ARCHIVES:
        rows=half.read_mixed_archive(pin)
        for name,source in half.ENDPOINT_SOURCES.items():
            if half.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['product']==('AP043',277) and found['terms_exists']==('CV070',143)
    assert found['sum_exists']==('CV003',107)
    bad=dict(half.EXP_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): half.read_mixed_archive(bad)


def test_actual_integer_models_cover_zero_argument_head_and_cutoff():
    for n in range(4):
        H=2*n+1
        for d in range(1,5):
            for x in range(d+1):
                h=factorial(H)*(2*d)**H
                a=[Fraction(h*x**j,(2*d)**j*factorial(j)) for j in range(H+1)]
                assert h>0 and all(v.denominator==1 for v in a)
                assert all((j+1)*(2*d)*a[j+1]==x*a[j] for j in range(H))
                for scale in (0,1,3):
                    b0=scale*factorial(n)*d**n
                    b=[Fraction(b0*x**j,d**j*factorial(j)) for j in range(n+1)]
                    assert all(v.denominator==1 for v in b)
                    u,v=sum(a[:n+1]),sum(b)
                    assert h*h*v<=b0*u*u
                    assert 2**n*(b0*u*u)<=2**n*(h*h*v)+2*b0*h*h


def test_halving_is_essential_and_finite_square_is_not_exact_equality():
    # n=1, x=d=1: E_1(1/2)^2=9/4, whereas E_1(1)=2.
    assert (1+Fraction(1,2))**2!=2
    assert (1+1)**2>2+Fraction(2,2)  # Omitting the halving breaks the error.


def test_complete_half_square_replays_without_new_induction():
    result=half.prove_exp_half_square()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_recurrence_scaling_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=half.prove_exp_half_square();node=result.provenance['helper_bundle_indices']['scale_recurrence']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
