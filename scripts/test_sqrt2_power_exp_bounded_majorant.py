"""Uniform majorants preserve the supplied rational argument and actual table."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_bounded_majorant as majorant


def test_exact_bounded_argument_statement_preserves_six_premises():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    n,premises,conclusion=strip_target(majorant.frozen_exp_bounded_majorant_target())
    names=tuple(reversed(majorant.PARAMETERS));registry=majorant.definition_registry()
    assert n==9 and len(premises)==6 and type(conclusion) is Exists
    assert premises==[parse_named(p,names,registry) for p in majorant.PREMISES]
    assert conclusion==parse_named('Le(s,C*h)',names,registry)
    c=majorant.source_contract()
    assert c['uniform_in_finite_horizon'] is c['only_reference_head_cancelled'] is c['actual_positive_integer_reference_constructed'] is True
    assert c['new_induction_count']==0 and c['analytic_exponential_claimed'] is c['closes_IR072'] is False


def test_existing_twelve_definition_dag_is_conservative_and_unchanged():
    registry=majorant.definition_registry();source=majorant.source_registry();seen=set();ids=set()
    assert len(registry)==12 and 'NatExpWeightTable' in registry and 'Pow' in registry
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert majorant.source_contract()['new_definition_ids']==[]


def test_changed_argument_bound_power_horizon_or_head_is_rejected():
    source=majorant.NAMED_SOURCE;registry=majorant.definition_registry()
    for changed in (source.replace('Le(x,L*d)','Le(x,L+d)'),source.replace('~d=0','d=0'),
                    source.replace('d,x,ab,ac,N','d,L*d,ab,ac,N'),source.replace('Pow(9,S L,C)','Pow(9,S N,C)'),
                    source.replace('Le(s,C*h)','Le(s,C)'),source.replace('Sum(ab,ac,S N,s)','Sum(ab,ac,N,s)')):
        assert changed!=source
        with patch.object(majorant,'NAMED_SOURCE',changed),pytest.raises(ValueError):majorant.frozen_exp_bounded_majorant_target(_registry=registry)


def test_actual_bounded_rational_models_cover_zero_heads_and_nonstrict_bounds():
    from math import factorial
    examples=0;zeroheads=0;endpoints=0;interior=0
    for L in range(6):
        C=9**(L+1)
        for d in (1,2,3):
            for x in range(L*d+1):
                for N in range(7):
                    base=factorial(N)*d**N
                    b=2*base
                    reference=[b*(L*d)**j//(factorial(j)*d**j) for j in range(N+1)]
                    v=sum(reference)
                    assert b>0 and reference[0]==b and v<=C*b
                    for scale in (0,1,3):
                        h=scale*base
                        values=[h*x**j//(factorial(j)*d**j) for j in range(N+1)]
                        s=sum(values);k=L*d-x
                        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
                        assert all(((j+1)*d)*reference[j+1]==(L*d)*reference[j] for j in range(N))
                        assert d*(L*d)==d*x+d*k and b*s<=h*v<=b*(C*h) and s<=C*h
                        assert max(b*s,h*v,b*(C*h)).bit_length()<=128
                        examples+=1;zeroheads+=scale==0;endpoints+=x==L*d;interior+=x<L*d
    assert examples==2268 and zeroheads==756 and endpoints==378 and interior==1890
    # The argument bound is essential even with a genuine positive computation.
    L,d,x,N,h,C=0,1,10,1,1,9
    assert not x<=L*d and h*(1+x)>C*h


def test_ten_endpoints_resolve_to_actual_owned_proof_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=majorant.definition_registry();found={}
    for pin in majorant.ARCHIVES:
        rows=majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==10 and found['integer']==('AP072',majorant.INTEGER_ARCHIVE['root'])
    assert found['relative']==('AP069',143) and found['constructed']==('CV070',143)
    with pytest.raises(ValueError):majorant.read_mixed_archive(dict(majorant.INTEGER_ARCHIVE,sha256='0'*64))


def test_source_pins_bind_the_integer_and_relative_ancestors():
    pins=majorant.exp_bounded_majorant_source_pins()
    for pin in majorant.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert all('sha256' in pins[name] for name in ('scripts/sqrt2_power_exp_integer_majorant.py','scripts/sqrt2_power_exp_relative_cross_continuity.py','scripts/sqrt2_power_exp_bounded_majorant.py'))


def test_complete_bounded_majorant_uses_no_new_induction_or_axiom():
    result=majorant.prove_exp_bounded_majorant()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=majorant.prove_exp_bounded_majorant()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
