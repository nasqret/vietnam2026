"""The near-two sum is the actual finite exponential, not just a polynomial."""
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_witness as witness


def test_exact_unconditional_finite_log_exp_contract():
    from sqrt2_power_native import strip_target
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_log_exp_witness_target(_registry=registry)
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(witness.canonical(encode_formula(target)))==11262
    assert len(witness.OUTPUTS)==11 and len(witness.PARTS)==16
    for _ in witness.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    actual=[]
    for _ in range(15):
        assert type(conclusion) is And
        actual.append(conclusion.left);conclusion=conclusion.right
    actual.append(conclusion);names=tuple(reversed(('K',)+witness.OUTPUTS))
    assert actual==[parse_named(source,names,registry) for source in witness.PARTS]
    c=witness.source_contract()
    assert c['same_product_table_used_for_recurrence_and_errors'] is c['all_rational_denominators_proved_nonzero'] is True
    assert c['actual_CV073_recurrence_replayed'] is c['argument_upper_one_proved'] is True
    assert c['redundant_CV085_root_replayed'] is c['analytic_logarithm_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_definition_dag_is_preserved():
    from sqrt2_power_same_table_composition import definition_registry
    registry=witness.definition_registry();seen=set();ids=set()
    assert registry==definition_registry() and len(registry)==53
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_recurrence_power_or_near_two_error_is_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('d*p,3*x,tb,tc','d,3*x,tb,tc'),
                    source.replace('BetaAt(tb,tc,0,h)','BetaAt(tc,tb,0,h)'),
                    source.replace('Pow(3,S K,r)','Pow(3,S(S K),r)'),
                    source.replace('2*p+9*a','2*p'),source.replace('~h=0','h=0')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            witness.frozen_log_exp_witness_target(_registry=registry)


def test_actual_stage_and_recurrence_bodies_are_owned_exactly():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();found={}
    for pin in witness.ARCHIVES:
        rows=witness.read_mixed_archive(pin)
        for name,source in witness.ENDPOINT_SOURCES.items():
            if witness.ENDPOINT_OWNERS[name]!=pin['case']:
                continue
            target=encode_formula(parse_named(source,registry=registry))
            matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3]
            found[name]=matches[0]
    assert found['computation']==432 and found['evaluation']==433 and found['recurrence']==121
    assert found.keys()==witness.ENDPOINT_SOURCES.keys()
    bad=dict(witness.COMPOSITION_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError):
        witness.read_mixed_archive(bad)


def test_actual_finite_terms_obey_recurrence_and_both_error_bounds():
    from fractions import Fraction
    from math import factorial,lcm
    for K in range(6):
        N=K+2;p=3**N;v=3**((N+1)*N);r=3**(K+1);a=2**N
        for scale in (1,2,5):
            d=scale*lcm(*range(1,N,2));coeff=[2*d//i if i%2 else 0 for i in range(N)]
            x=0
            for c in coeff: x=3*x+c
            weights=[factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
            monomials=[]
            for j in range(N+1):
                value,rem=divmod(v*3**j*x**j,p**j);assert rem==0;monomials.append(value)
            terms=[w*t for w,t in zip(weights,monomials)];h=weights[0]*v;y=sum(terms)
            assert min(d,p,r,h,d*p)>0 and 3*x<=d*p and terms[0]==h
            assert all(((j+1)*(d*p))*terms[j+1]==(3*x)*terms[j] for j in range(N))
            assert Fraction(y,h)==sum((Fraction(3*x,d*p)**j/factorial(j) for j in range(N+1)),Fraction(0))
            assert Fraction(y,h)<=2+Fraction(9*a,p) and 2<=Fraction(y,h)+Fraction(1,r)
            assert Fraction(y,h)>1


def test_flat_source_closure_is_rechecked_and_changed_manifest_rejected():
    pins=witness.log_exp_witness_source_pins()
    assert len(pins)==217 and pins[witness.COMPOSITION_ARCHIVE['path']]['sha256']==witness.COMPOSITION_ARCHIVE['sha256']
    with patch.object(witness,'SOURCE_CLOSURE_SHA256','0'*64),pytest.raises(ValueError):
        witness.log_exp_witness_source_pins()


def test_complete_finite_log_exp_certificate_replays_without_new_induction():
    result=witness.prove_log_exp_witness()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False
    assert result.provenance['endpoint_archive_selection']['computation']['original_node']==432
    assert result.provenance['endpoint_archive_selection']['evaluation']['original_node']==433


def test_forged_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_log_exp_witness()
    check_forged_root_rejection(result.bundle)
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
