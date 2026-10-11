"""Exact half-logarithm transport: unchanged prefixes, doubled exp denominators."""
import ast
import gzip
import json
from hashlib import sha256
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_exp_refinement as refinement
from test_sqrt2_power_log_exp_refinement import _atanh,_exp


def test_exact_half_refinement_preserves_every_actual_logarithm_computation():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(refinement.frozen_half_log_exp_refinement_target())
    names=tuple(reversed(refinement.PARAMETERS));registry=refinement.definition_registry()
    assert n==23 and len(premises)==15 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in refinement.PREMISES]
    assert conclusion==parse_named(refinement.CONCLUSION,names,registry)
    assert refinement.PREMISES[:8]==refinement.FULL_PREMISES[:8]
    assert refinement.PREMISES[10:]==refinement.FULL_PREMISES[10:]
    assert refinement.PREMISES[8]=='NatScaledExpRecurrence(2*(d*p),3*x,cb,cc,m)'
    assert refinement.PREMISES[9]=='NatScaledExpRecurrence(2*(e*q),3*z,eb,ec,(S m)+N)'
    c=refinement.source_contract()
    assert c['original_logarithm_prefix_and_horner_scales_unchanged'] is c['exponential_arguments_explicitly_halved'] is True
    assert c['analytic_limit_claimed'] is c['sqrt2_identification_claimed'] is c['closes_IR072'] is False


def test_exact_existing_definition_dag_is_reused_without_new_aliases():
    from sqrt2_power_log_exp_refinement import definition_registry
    registry=refinement.definition_registry();seen=set();ids=set()
    assert registry==definition_registry() and len(registry)==15
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert refinement.source_contract()['new_definition_ids']==[]
    assert 'NatSqrt2LogArgument' not in registry


def test_changed_coefficient_scale_half_argument_horizon_or_error_is_rejected():
    source=refinement.NAMED_SOURCE;registry=refinement.definition_registry()
    for changed in (source.replace('NatAtanhPrefix(d,','NatAtanhPrefix(2*d,'),
                    source.replace('NatHornerValue(ab,ac,3,','NatHornerValue(ab,ac,2,'),
                    source.replace('NatScaledExpRecurrence(2*(d*p),','NatScaledExpRecurrence(d*p,'),
                    source.replace('NatScaledExpRecurrence(2*(e*q),','NatScaledExpRecurrence(e*q,'),
                    source.replace('(S m)+N','m+N'),source.replace('Pow(2,m,P)','Pow(2,k,P)'),
                    source.replace('(9*3)*P+2*p','9*P+2*p')):
        assert changed!=source
        with patch.object(refinement,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            refinement.frozen_half_log_exp_refinement_target(_registry=registry)


def test_actual_independent_half_log_models_and_necessary_scaling_guards():
    examples=0;strict_gap=0;zero_heads=0;equal_log_length=0;unequal_scales=0
    for k in range(3):
        for l in range(3):
            for ds in (1,2):
                for es in (1,3):
                    d,x,p=_atanh(k+1,ds);e,z,q=_atanh(k+1+l,es);F=d*(e*q)
                    gap=(d*p)*(3*z)-(e*q)*(3*x)
                    assert 0<=gap<=3*F and 3*z<=e*q
                    assert (2*(d*p))*(3*z)==(2*(e*q))*(3*x)+2*gap
                    assert 2*gap<=3*((2*2)*F) and 3*z<=2*(e*q)
                    for m in range(3):
                        for N in range(2):
                            ah,us=_exp(3*x,2*(d*p),m);bh,vs=_exp(3*z,2*(e*q),m+1+N);P=2**m
                            for sa,sb in ((0,0),(0,1),(1,0),(1,1),(2,3)):
                                a,b,u,v=sa*ah,sb*bh,sa*us,sb*vs
                                assert b*u<=a*v and (p*P)*(a*v)<=(p*P)*(b*u)+((9*3)*P+2*p)*(a*b)
                                assert max((p*P)*(a*v),(p*P)*(b*u)+((9*3)*P+2*p)*(a*b),4*F).bit_length()<=128
                                examples+=1;strict_gap+=gap>0;zero_heads+=a==0 or b==0;equal_log_length+=l==0;unequal_scales+=d!=e
    assert examples==1080 and strict_gap>0 and zero_heads==648 and equal_log_length==360 and unequal_scales>0
    # A scaled gap is not the same gap. The unscaled error budget cannot
    # simply be reused without multiplication/cancellation proof.
    d=1;e=3;x=0;z=g=3;F=1
    assert d*z==e*x+g and g<=3*F and z<=e
    assert (2*d)*z!=(2*e)*x+g and not 2*g<=3*F
    F=0;p=P=a=b=1;g=u=0;v=30
    assert (p*F)*(P*(a*v))<=(p*F)*(P*(b*u))+(9*(g*P)+2*(p*F))*(a*b)
    assert not (p*P)*(a*v)<=(p*P)*(b*u)+((9*3)*P+2*p)*(a*b)


def test_twenty_three_endpoints_have_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=refinement.definition_registry();found={}
    for pin in refinement.ARCHIVES:
        rows=refinement.read_mixed_archive(pin)
        for name,source in refinement.ENDPOINT_SOURCES.items():
            if refinement.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==23 and found['normalize']==('AP082',227) and found['bound_two']==('AP007',156)
    assert found['logarithm']==('CV093',154) and found['two_error']==('CV101',188)
    with pytest.raises(ValueError):refinement.read_mixed_archive(dict(refinement.NORMALIZE_ARCHIVE,sha256='0'*64))


def test_solver_contract_is_frozen_before_native_factories_and_sources_are_bound():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=refinement.half_log_exp_refinement_source_pins()
    for pin in refinement.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=target_for('AP087-scaled-gap')
    assert target==parse_named(refinement.HELPER_SOURCES['scaled_gap'],registry=refinement.definition_registry())
    assert digest==refinement.HELPER_TARGET_SHA256['scaled_gap']
    base=refinement.ROOT/'research/arithmetic-library/sqrt2-power/observations'
    observed=json.loads((base/'half-log-exp-refinement-solvers-v1.json').read_bytes())
    name='scripts/sqrt2_power_half_log_exp_refinement.py';pin=observed['producer_source_pins'][name]
    with gzip.open(base/'half-log-exp-refinement-preconstruction-source-v1.py.gz','rb') as f:old=f.read(pin['bytes']+1)
    assert len(old)==pin['bytes'] and sha256(old).hexdigest()==pin['sha256']
    before=ast.parse(old);now=ast.parse((refinement.ROOT/name).read_bytes())
    assert [ast.dump(n,include_attributes=False) for n in before.body]==[ast.dump(n,include_attributes=False) for n in now.body[:len(before.body)]]
    assert [n.name for n in now.body[len(before.body):]]==['_scaled_gap','_root','prove_half_log_exp_refinement']
    assert all(pins[key]==value for key,value in observed['producer_source_pins'].items() if key!=name)
    assert observed['target_ast_sha256']==digest and observed['solver_proofs_reconstructed']==0
    assert observed['authority']=='untrusted_classical_hints_only' and observed['original_HA_checked'] is False
    with patch.dict(refinement.HELPER_TARGET_SHA256,scaled_gap='0'*64),pytest.raises(ValueError):target_for('AP087-scaled-gap')


def test_complete_half_refinement_replays_without_new_induction_or_axioms():
    result=refinement.prove_half_log_exp_refinement()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=refinement.prove_half_log_exp_refinement()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
