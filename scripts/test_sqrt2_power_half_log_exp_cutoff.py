"""The original cutoff budgets also pay the explicitly halved arguments."""
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_exp_cutoff as cutoff
from test_sqrt2_power_log_exp_refinement import _atanh,_exp


def test_exact_cutoff_preserves_log_data_and_explicit_half_arguments():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    registry=cutoff.definition_registry();n,premises,conclusion=strip_target(cutoff.frozen_half_log_exp_cutoff_target(_registry=registry))
    names=tuple(reversed(cutoff.PARAMETERS))
    assert n==22 and len(premises)==15 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in cutoff.PREMISES]
    assert conclusion==parse_named(cutoff.CONCLUSION,names,registry)
    assert not any('Le(' in p for p in cutoff.PREMISES)
    assert cutoff.PREMISES[:8]==cutoff.FULL_PREMISES[:8] and cutoff.PREMISES[10:]==cutoff.FULL_PREMISES[10:]
    assert cutoff.PREMISES[8].startswith('NatScaledExpRecurrence(2*(d*p),3*x,')
    assert cutoff.PREMISES[9].startswith('NatScaledExpRecurrence(2*(e*q),3*z,')
    c=cutoff.source_contract()
    assert c['budgets_proved_not_assumed']==['54*r<=3^M','4*r<=2^M']
    assert c['sqrt2_identification_claimed'] is c['analytic_limit_claimed'] is c['closes_IR072'] is False
    assert c['new_arithmetic_helper_needed'] is False


def test_fifteen_existing_definitions_and_checked_native_constructor_are_reused():
    import sqrt2_power_log_exp_cutoff_refinement as original
    registry=cutoff.definition_registry();seen=set();ids=set()
    assert len(registry)==15 and registry==original.definition_registry()
    assert cutoff._root is original._root and cutoff.PARAMETERS==original.PARAMETERS
    assert cutoff.ENDPOINT_SOURCES['budgets']==original.HELPER_SOURCES['budgets']
    assert cutoff.ENDPOINT_SOURCES['arithmetic']==original.HELPER_SOURCES['arithmetic']
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert cutoff.source_contract()['new_definition_ids']==[]


def test_changed_original_scales_half_argument_cutoff_or_error_is_rejected():
    source=cutoff.NAMED_SOURCE;registry=cutoff.definition_registry()
    for changed in (source.replace('18*r','18'),source.replace('NatAtanhPrefix(d,','NatAtanhPrefix(2*d,'),
                    source.replace('NatScaledExpRecurrence(2*(d*p),','NatScaledExpRecurrence(d*p,'),
                    source.replace('Pow(2,S(S(18*r)),P)','Pow(2,r,P)'),source.replace('(S(S(S(18*r))))+N','(S(S(18*r)))+N'),
                    source.replace('r*(a0*v),r*(b0*u)+a0*b0','r*(a0*v),r*(b0*u)')):
        assert changed!=source
        with patch.object(cutoff,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            cutoff.frozen_half_log_exp_cutoff_target(_registry=registry)


def test_actual_cutoff_budgets_and_small_half_exponential_computations():
    # Positive-r checks are budget arithmetic, not enormous exponential
    # tables. Complete tables below use r=0 and respect the 128-bit guard.
    examples=0;positive=0;strict=0
    for r in range(3):
        M=18*r+2;p=3**M;P=2**M
        assert 54*r<=p and 4*r<=P
        for a in range(1,4):
            for b in range(1,4):
                for u in range(9):
                    for v in range(9):
                        lhs=(p*P)*(a*v);rhs=(p*P)*(b*u)+(27*P+2*p)*(a*b)
                        assert max(lhs,rhs).bit_length()<=128
                        if lhs>rhs:continue
                        assert r*(a*v)<=r*(b*u)+a*b
                        examples+=1;positive+=r>0;strict+=a*v>b*u
    assert examples>1000 and positive and strict
    for p,P in ((1,4),(54,1)):
        assert (p*P)*2<=27*P+2*p and not 2<=1 and (54<=p)!=(4<=P)
    full=0;r=0;M=2;P=4
    for l in range(3):
        for ds,es in ((1,1),(1,3),(2,1)):
            d,x,p=_atanh(M,ds);e,z,q=_atanh(M+l,es)
            for N in range(3):
                a,u=_exp(3*x,2*(d*p),M);b,v=_exp(3*z,2*(e*q),M+1+N)
                assert b*u<=a*v and r*(a*v)<=r*(b*u)+a*b
                assert max((p*P)*(a*v),(p*P)*(b*u)+(27*P+2*p)*(a*b)).bit_length()<=128
                full+=1
    assert full==27


def test_three_exact_endpoints_retain_actual_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=cutoff.definition_registry();found={}
    for pin in cutoff.ARCHIVES:
        rows=cutoff.read_mixed_archive(pin)
        for name,source in cutoff.ENDPOINT_SOURCES.items():
            if cutoff.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found==dict(refinement=('AP087',230),budgets=('AP083',235),arithmetic=('AP083',236))
    with pytest.raises(ValueError):cutoff.read_mixed_archive(dict(cutoff.REFINEMENT_ARCHIVE,raw_sha256='0'*64))


def test_sources_and_actual_archives_include_both_reused_producers():
    pins=cutoff.half_log_exp_cutoff_source_pins()
    for pin in cutoff.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert pins['scripts/sqrt2_power_half_log_exp_refinement.py']['sha256']=='19d862af59e8bc76e8a984390788a447bb870efb11d6776d02bb4f3c7f604929'
    assert pins['scripts/sqrt2_power_log_exp_cutoff_refinement.py']['sha256']=='22c1f5539cf98203ad5f4750858c4b1d14aa7ba42009ff6fa6709e5f7b8ae383'
    assert 'scripts/sqrt2_power_half_log_exp_cutoff.py' in pins


def test_complete_half_cutoff_replays_without_new_induction_or_axioms():
    result=cutoff.prove_half_log_exp_cutoff()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['helper_statement_ast_sha256']=={} and result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=cutoff.prove_half_log_exp_cutoff()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
