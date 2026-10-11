"""Large rational arguments, exact recurrence and necessary finite guards."""
from itertools import product
from unittest.mock import patch

import pytest
import sqrt2_power_exp_large_argument_ratio as ratio


def test_exact_halving_threshold_and_no_large_argument_upper_one_assumption():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=ratio.frozen_exp_large_argument_ratio_target();n,premises,conclusion=strip_target(target)
    assert n==6 and len(premises)==4 and type(conclusion) is Exists
    assert len(ratio.canonical(encode_formula(target)))==494
    c=ratio.source_contract()
    assert c['argument_bound']=='x<=L*d' and c['threshold']=='2*L<=j+1'
    assert c['zero_x_L_a_b_allowed'] is True
    assert c['sum_or_tail_constructed'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_order_definition_is_the_only_notation():
    registry=ratio.definition_registry()
    assert tuple(registry)==('Le',) and not registry['Le'].conceptual_dependencies
    assert ratio.source_contract()['new_definition_ids']==[]


def test_changed_denominator_guard_threshold_recurrence_or_conclusion_is_rejected():
    source=ratio.NAMED_SOURCE
    for changed in (source.replace('~d=0','d=0'),source.replace('Le(x,L*d)','Le(x,d)'),
                    source.replace('Le(2*L,S j)','Le(L,S j)'),source.replace('((S j)*d)*b=x*a','((S j)*d)*a=x*b'),
                    source.replace('Le(2*b,a)','Le(3*b,a)')):
        assert changed!=source
        with patch.object(ratio,'NAMED_SOURCE',changed),pytest.raises(ValueError):ratio.frozen_exp_large_argument_ratio_target()


def test_small_exact_models_and_counterexamples_to_removed_guards():
    accepted=0;zero_L=False;large_argument=False
    for d,x,L,j,a,b in product(range(1,4),range(10),range(4),range(9),range(6),range(6)):
        if x<=L*d and 2*L<=j+1 and ((j+1)*d)*b==x*a:
            assert 2*b<=a;accepted+=1;zero_L|=L==0;large_argument|=x>d
    assert accepted>100 and zero_L and large_argument
    # d=0 admits a false halving conclusion if positivity is removed.
    d,x,L,j,a,b=0,0,0,0,0,1
    assert x<=L*d and 2*L<=j+1 and ((j+1)*d)*b==x*a and not 2*b<=a
    # At j=0 the x/d=1 term need not halve; the cutoff is substantive.
    d,x,L,j,a,b=1,1,1,0,1,1
    assert d>0 and x<=L*d and ((j+1)*d)*b==x*a and not 2*b<=a


def test_all_eight_arithmetic_dependencies_have_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    rows=ratio.read_mixed_archive(ratio.BOUND_ARCHIVE);registry=ratio.definition_registry()
    for name,source in ratio.ENDPOINT_SOURCES.items():
        exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
        assert len(matches)==1 and rows[matches[0]][3] and ratio.ENDPOINT_OWNERS[name]=='CV071'
    with pytest.raises(ValueError):ratio.read_mixed_archive(dict(ratio.BOUND_ARCHIVE,sha256='0'*64))


def test_source_archive_pins_and_detached_solver_binding_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=ratio.exp_large_argument_ratio_source_pins();assert len(pins)==341
    target,digest,_=observer.target_for('AP051-ratio')
    assert target==parse_named(ratio.HELPER_SOURCES['ratio'],registry=ratio.definition_registry())
    assert digest==ratio.HELPER_TARGET_SHA256['ratio']
    assert pins[ratio.BOUND_ARCHIVE['path']]['sha256']==ratio.BOUND_ARCHIVE['sha256']


def test_complete_certificate_is_ordinary_without_new_induction():
    result=ratio.prove_exp_large_argument_ratio()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=ratio.prove_exp_large_argument_ratio()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
