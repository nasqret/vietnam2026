"""Actual auxiliary cutoffs pay the logarithm and exponential errors."""
from fractions import Fraction
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_cutoff_refinement as cutoff


def test_exact_cutoffs_powers_and_independent_computations_are_preserved():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    registry=cutoff.definition_registry();n,premises,conclusion=strip_target(cutoff.frozen_log_exp_cutoff_refinement_target())
    names=tuple(reversed(cutoff.PARAMETERS))
    assert n==22 and len(premises)==15 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in cutoff.PREMISES]
    assert conclusion==parse_named(cutoff.CONCLUSION,names,registry)
    assert not any('Le(' in p for p in cutoff.PREMISES)
    c=cutoff.source_contract()
    assert c['budgets_proved_not_assumed']==['54*r<=3^M','4*r<=2^M']
    assert c['fixed_approximation_program_changed'] is c['analytic_log_exp_identity_claimed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_fifteen_unchanged_definitions_are_topological_and_conservative():
    import sqrt2_power_log_exp_refinement as original
    registry=cutoff.definition_registry();seen=set();ids=set()
    assert len(registry)==15 and dict(registry)==dict(original.definition_registry())
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert cutoff.source_contract()['new_definition_ids']==[]


def test_changed_cutoffs_computations_and_requested_error_are_rejected():
    source=cutoff.NAMED_SOURCE;registry=cutoff.definition_registry()
    for changed in (source.replace('18*r','18'),source.replace('NatAtanhPrefix(e,bb,bc,','NatAtanhPrefix(d,bb,bc,'),
                    source.replace('Pow(2,S(S(18*r)),P)','Pow(2,r,P)'),source.replace('(S(S(S(18*r))))+N','(S(S(18*r)))+N'),
                    source.replace('r*(a0*v),r*(b0*u)+a0*b0','r*(a0*v),r*(b0*u)')):
        assert changed!=source
        with patch.object(cutoff,'NAMED_SOURCE',changed),pytest.raises(ValueError):cutoff.frozen_log_exp_cutoff_refinement_target(_registry=registry)


def test_actual_power_budgets_arithmetic_models_and_zero_scale_computations():
    # The nonzero-r checks exercise actual cutoff powers and the exact budget
    # implication. Full rational exponential tables at M=20 exceed the 128-bit
    # example ceiling, so they are NOT silently evaluated or counted here.
    examples=0;strict=0;positive=0
    for r in range(3):
        M=18*r+2;p=3**M;P=2**M
        assert 54*r<=p and 4*r<=P
        for a in range(1,4):
            for b in range(1,4):
                for u in range(9):
                    for v in range(9):
                        left=(p*P)*(a*v);right=(p*P)*(b*u)+(27*P+2*p)*(a*b)
                        assert max(left,right).bit_length()<=128
                        if left>right:continue
                        assert r*(a*v)<=r*(b*u)+a*b
                        examples+=1;positive+=r>0;strict+=a*v>b*u
    assert examples>1000 and positive>0 and strict>0
    for p,P in ((1,4),(54,1)):
        assert (p*P)*2<=(27*P+2*p)
        assert not 2<=1
        assert (54<=p)!=(4<=P)  # Neither budget can simply be omitted.
    full=0
    def log(M,s):
        d=s*lcm(*(j for j in range(1,M,2)));x=0
        for j in range(M):x=3*x+(0 if j%2==0 else 2*d//j)
        return d,x,3**M
    def exp(x,d,N):
        values=[Fraction(1)]
        for j in range(N):values.append(values[-1]*Fraction(x,(j+1)*d))
        h=lcm(*(v.denominator for v in values));terms=[int(h*v) for v in values]
        assert all((j+1)*d*terms[j+1]==x*terms[j] for j in range(N))
        return h,sum(terms)
    r=0;M=2;P=4
    for l in range(3):
        for ds,es in ((1,1),(1,3),(2,1)):
            d,x,p=log(M,ds);e,z,q=log(M+l,es)
            for N in range(3):
                a,u=exp(3*x,d*p,M);b,v=exp(3*z,e*q,M+1+N)
                assert b*u<=a*v and r*(a*v)<=r*(b*u)+a*b
                assert max((p*P)*(a*v),(p*P)*(b*u)+(27*P+2*p)*(a*b)).bit_length()<=128
                full+=1
    assert full==27


def test_nineteen_endpoints_retain_exact_actual_archive_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=cutoff.definition_registry();found={}
    for pin in cutoff.ARCHIVES:
        rows=cutoff.read_mixed_archive(pin)
        for name,source in cutoff.ENDPOINT_SOURCES.items():
            if cutoff.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==19 and found['refinement']==('AP082',cutoff.REFINEMENT_ARCHIVE['root'])
    assert found['binary_growth'][0]=='AP046' and found['ternary_growth'][0]=='AP033'
    with pytest.raises(ValueError):cutoff.read_mixed_archive(dict(cutoff.PRECISION_ARCHIVE,raw_sha256='0'*64))


def test_source_closure_and_exact_solver_arithmetic_are_bound():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=cutoff.log_exp_cutoff_refinement_source_pins()
    for pin in cutoff.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=target_for('AP083-arithmetic')
    assert target==parse_named(cutoff.HELPER_SOURCES['arithmetic'],registry=cutoff.definition_registry())
    assert digest==cutoff.HELPER_TARGET_SHA256['arithmetic']
    with patch.dict(cutoff.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP083-arithmetic')


def test_complete_cutoff_refinement_replays_without_new_induction_or_axioms():
    result=cutoff.prove_log_exp_cutoff_refinement()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_root_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=cutoff.prove_log_exp_cutoff_refinement()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
