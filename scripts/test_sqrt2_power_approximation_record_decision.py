"""Arbitrary-record decisions and exact encoded computation calibration."""
from dataclasses import replace
from math import factorial,isqrt,prod
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_record_decision as decision


def test_exact_unconditional_supplied_record_decision():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or,Imp,Bot
    from peano_lab.library.proof_bundle import encode_formula
    target=decision.frozen_approximation_record_decision_target();binders,premises,conclusion=strip_target(target)
    assert binders==5 and not premises and type(conclusion) is Or
    assert type(conclusion.right) is Imp and type(conclusion.right.consequent) is Bot
    assert conclusion.left==conclusion.right.antecedent
    assert len(decision.canonical(encode_formula(target)))==51551
    c=decision.source_contract()
    assert c['record_code_components']==2 and c['all_thirteen_internal_values_actually_decoded'] is True
    assert c['all_competing_fields_transported_by_actual_beta_uniqueness'] is True
    assert c['two_output_slots_checked'] is c['supplied_full_computation_decision_replayed'] is True
    assert c['unbounded_existential_search_used'] is c['classical_axioms_used'] is c['markov_principle_used'] is c['canonical_PR_approximation_algorithm_claim'] is c['closes_IR072'] is False


def test_record_definition_and_all_twenty_four_dag_nodes_remain_unchanged():
    from sqrt2_power_approximation_record_exists import definition_registry
    registry=decision.definition_registry();original=definition_registry();seen=set();ids=set()
    assert dict(registry)==dict(original) and len(registry)==24
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decision.source_contract()['new_definition_ids']==[]


def test_wrong_record_order_or_precision_is_rejected():
    source=decision.NAMED_SOURCE;registry=decision.definition_registry()
    for changed in (source.replace('n,up,ud,rb,rc','S n,up,ud,rb,rc'),
                    source.replace('n,up,ud,rb,rc','n,ud,up,rb,rc'),
                    source.replace('n,up,ud,rb,rc','n,up,ud,rc,rb')):
        assert changed!=source
        with patch.object(decision,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decision.frozen_approximation_record_decision_target(_registry=registry)


def test_exact_sample_decision_and_beta_computation_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decision.definition_registry();found=set()
    for pin in decision.ARCHIVES:
        rows=decision.read_mixed_archive(pin)
        for name,source in decision.ENDPOINT_SOURCES.items():
            if decision.ENDPOINT_OWNERS[name]!=pin['case']:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad['sha256']='0'*64
        with pytest.raises(ValueError):
            decision.read_mixed_archive(bad)
    assert found==decision.ENDPOINT_SOURCES.keys()


def _encode(values):
    c=factorial(len(values))*(max(values)+1)
    moduli=[1+(i+1)*c for i in range(len(values))];M=prod(moduli)
    b=sum(v*(M//m)*pow(M//m,-1,m) for v,m in zip(values,moduli))%M
    return b,c,M


def _beta(b,c,i):
    return b%(1+(i+1)*c)


def _sample_values(k):
    d=2**k;s=isqrt(2*d*d);D=factorial(2*k+1)
    A=[0 if i%2==0 else 2*D//i for i in range(2*k+1)]
    ab,ac,_=_encode(A);x=0
    for a in A:
        x=3*x+a
    p=3**(2*k+1);U=3*x*d;V=D*p*s;N=k+2;f=factorial(N);h=V**N
    W=[factorial(N)//factorial(j)*V**(N-j) for j in range(N+1)]
    T=[W[j]*U**j for j in range(N+1)]
    wb,wc,_=_encode(W);tb,tc,_=_encode(T)
    return (d,s,D,ab,ac,x,p,wb,wc,tb,tc,W[0],f,h,sum(T))


def _record_holds(n,up,ud,rb,rc):
    # Bounded small-model calibration; this Python function is not HA authority.
    assert n in (0,1)
    values=[_beta(rb,rc,i) for i in range(15)]
    d,s,D,ab,ac,x,p,wb,wc,tb,tc,w0,f,h,y=values;k=n+8;N=k+2
    if not (up==y and ud==w0 and ud!=0 and D==factorial(2*k+1) and D!=0):
        return False
    if not (d==2**k and s*s<=2*d*d<(s+1)**2 and p==3**(2*k+1)):
        return False
    A=[_beta(ab,ac,i) for i in range(2*k+1)];value=0
    for i,a in enumerate(A):
        if not ((i%2==0 and a==0) or (i%2==1 and i*a==2*D)):
            return False
        value=3*value+a
    if x!=value:
        return False
    U=3*x*d;V=D*p*s
    W=[_beta(wb,wc,j) for j in range(N+1)];T=[_beta(tb,tc,j) for j in range(N+1)]
    return (W[N]==1 and all(W[j]==((j+1)*V)*W[j+1] for j in range(N))
        and all(T[j]==W[j]*U**j for j in range(N+1))
        and W[0]==w0 and T[0]==w0 and f==factorial(N) and h==V**N
        and w0==f*h and y==sum(T))


def test_complete_encoded_precision_zero_record_and_noncanonical_code():
    values=_sample_values(8);rb,rc,M=_encode(values);ud=values[11];up=values[14]
    assert _record_holds(0,up,ud,rb,rc)
    assert _record_holds(0,up,ud,rb+M,rc) and rb+M!=rb
    assert not _record_holds(0,up+1,ud,rb,rc)
    assert not _record_holds(0,up,ud+1,rb,rc)
    assert not _record_holds(0,up,0,rb,rc)
    assert not _record_holds(0,up,ud,0,0)


def test_reencoded_records_with_corrupted_computation_scalars_are_rejected():
    values=_sample_values(8);ud=values[11];up=values[14]
    for index in (0,1,2,5,6,11,12,13,14):
        changed=list(values);changed[index]+=1
        rb,rc,_=_encode(changed)
        assert not _record_holds(0,up,ud,rb,rc)


def test_complete_record_decision_replays_without_new_induction():
    result=decision.prove_approximation_record_decision()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_forged_field_transport_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decision.prove_approximation_record_decision();node=result.provenance['helper_bundle_indices']['transport']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
