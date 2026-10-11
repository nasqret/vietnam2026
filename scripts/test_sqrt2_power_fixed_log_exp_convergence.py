"""Keep the fixed log prefix and exp degree while transporting the cutoff."""
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_log_exp_convergence as fixed


def test_uniform_quantifiers_and_exact_existing_logarithm_interface():
    import sqrt2_power_finite_odd_log_series as interpretation
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    registry=fixed.definition_registry();n,premises,conclusion=strip_target(fixed.frozen_fixed_log_exp_convergence_target())
    assert n==1 and not premises and type(conclusion) is Exists
    body=conclusion.body
    assert body.left==parse_named('Pow(2,n,r)',('r','n'),registry)
    assert body.right.left==parse_named('~r=0',('r','n'),registry)
    assert body.right.right==parse_named(fixed.LATER_SOURCE,('r','n'),registry)
    m,actual,conclusion=strip_target(body.right.right);names=tuple(reversed(fixed.PARAMETERS))+('r','n')
    assert m==10 and len(actual)==8 and actual==[parse_named(p,names,registry) for p in fixed.PREMISES]
    assert conclusion==parse_named(fixed.CONCLUSION,names,registry)
    assert fixed.PREMISES[2:5]==(interpretation.PREFIX,interpretation.VALUE,'Pow(3,S(2*k),p)')
    assert interpretation.PARAMETERS==('d','ab','ac','k','x','p')
    assert 'AP020' not in {p['case'] for p in fixed.ARCHIVES}
    c=fixed.source_contract()
    assert c['fixed_logarithm_prefix_length']=='2*k+1' and c['fixed_exp_degree']=='k+2'
    assert c['root_quotient_accuracy_claimed'] is c['analytic_limit_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_same_thirteen_conservative_definitions_without_new_aliases():
    import sqrt2_power_log_exp_uniform_two as original
    registry=fixed.definition_registry();seen=set();ids=set()
    assert len(registry)==13 and dict(registry)==dict(original.definition_registry())
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert fixed.source_contract()['new_definition_ids']==[]


def test_changed_schedule_threshold_quantifiers_and_errors_are_rejected():
    source=fixed.NAMED_SOURCE;registry=fixed.definition_registry()
    for changed in (source.replace('exists r.','forall r.'),source.replace('18*r','18'),
                    source.replace('S(2*k)','S k'),source.replace('NatScaledExpRecurrence(d*p,3*x,tb,tc,S(S k))','NatScaledExpRecurrence(d*p,3*x,tb,tc,S k)'),
                    source.replace('Sum(tb,tc,S(S(S k)),y)','Sum(tb,tc,S(S k),y)'),source.replace('(r*2)*h+2*h','(r*2)*h+h')):
        assert changed!=source
        with patch.object(fixed,'NAMED_SOURCE',changed),pytest.raises(ValueError):fixed.frozen_fixed_log_exp_convergence_target(_registry=registry)


def test_constructed_gap_and_both_actual_index_alignments():
    examples=0;zero_offset=0
    for M in range(24):
        for offset in range(24):
            k=M+offset;l=k+offset+1;N=offset+1
            assert 2*k+1==M+l and k+2==(M+1)+N
            assert k+3==(M+1)+N+1
            assert k+2!=(M+1)+offset  # Dropping the successor loses one term.
            assert max(2*k+1,k+3,M+l).bit_length()<=128
            examples+=1;zero_offset+=offset==0
    assert examples==576 and zero_offset==24
    for n in range(4):
        r=2**n;M=18*r+2
        for offset in range(8):
            k=M+offset
            assert M<=k and (2*k+1)-M==k+offset+1 and (k+2)-(M+1)==offset+1
    # These are index-contract checks, not large exponential-table evaluations.


def test_seven_endpoints_have_exact_actual_archive_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=fixed.definition_registry();found={}
    for pin in fixed.ARCHIVES:
        rows=fixed.read_mixed_archive(pin)
        for name,source in fixed.ENDPOINT_SOURCES.items():
            if fixed.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==7 and found['uniform']==('AP084',fixed.UNIFORM_ARCHIVE['root']) and found['le_gap']==('AP007',157)
    with pytest.raises(ValueError):fixed.read_mixed_archive(dict(fixed.UNIFORM_ARCHIVE,target_ast_sha256='0'*64))


def test_sources_and_frozen_solver_index_identity_are_bound():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=fixed.fixed_log_exp_convergence_source_pins()
    for pin in fixed.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert 'scripts/sqrt2_power_finite_odd_log_series.py' in pins and 'scripts/sqrt2_power_odd_horner_quotient.py' in pins
    target,digest,_=target_for('AP085-indices')
    assert target==parse_named(fixed.HELPER_SOURCES['indices'],registry=fixed.definition_registry())
    assert digest==fixed.HELPER_TARGET_SHA256['indices']
    with patch.dict(fixed.HELPER_TARGET_SHA256,indices='0'*64),pytest.raises(ValueError):target_for('AP085-indices')


def test_complete_fixed_schedule_root_replays_without_new_induction_or_axioms():
    result=fixed.prove_fixed_log_exp_convergence()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=fixed.prove_fixed_log_exp_convergence()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
