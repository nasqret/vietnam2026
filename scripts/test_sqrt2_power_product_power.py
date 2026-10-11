"""Product powers retain independent actual computations at every exponent."""
from unittest.mock import patch

import pytest
import sqrt2_power_product_power as product


def test_exact_product_power_identity_has_no_positivity_guard():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    n,premises,conclusion=strip_target(product.frozen_product_power_target())
    names=tuple(reversed(product.PARAMETERS));registry=product.definition_registry()
    assert n==6 and len(premises)==3 and type(conclusion) is Eq
    assert premises==[parse_named(p,names,registry) for p in product.PREMISES]
    assert conclusion==parse_named('w=u*v',names,registry)
    c=product.source_contract()
    assert c['actual_previous_powers_constructed'] is c['actual_successor_values_identified_by_uniqueness'] is True
    assert c['positive_bases_required'] is c['code_number_equality_claimed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==1


def test_only_the_five_existing_power_definitions_are_exposed():
    registry=product.definition_registry();source=product.power_registry();seen=set();ids=set()
    assert tuple(registry)==('Lt','BetaAt','Product','Repeat','Pow')
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_product_exponent_or_value_is_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('Pow(a*b,k,w)','Pow(a+b,k,w)'),source.replace('Pow(a,k,u)','Pow(a,S k,u)'),
                    source.replace('Pow(b,k,v)','Pow(b,0,v)'),source.replace('w=u*v','w=u+v')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):product.frozen_product_power_target(_registry=registry)


def test_actual_models_include_zero_bases_and_zero_exponent():
    examples=0;zero_base=0;zero_exponent=0
    for a in range(8):
        for b in range(8):
            for k in range(10):
                u=a**k;v=b**k;w=(a*b)**k
                assert w==u*v and max(w,u*v).bit_length()<=128
                assert a**(k+1)==u*a and b**(k+1)==v*b
                examples+=1;zero_base+=a==0 or b==0;zero_exponent+=k==0
    assert examples==640 and zero_base==150 and zero_exponent==64
    assert 0**0==1 and (2+3)**2!=2**2*3**2


def test_seven_endpoints_are_owned_actual_proof_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==7 and found['power_unique']==('AP010',118) and found['power_exists']==('AP010',110)
    assert found['power_zero']==('AP010',112) and found['power_step']==('AP010',113)
    with pytest.raises(ValueError):product.read_mixed_archive(dict(product.POWER_ARCHIVE,sha256='0'*64))


def test_source_pins_and_successor_helper_statement_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    pins=product.product_power_source_pins()
    for pin in product.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    helper=parse_named(product.HELPER_SOURCES['successor_value'],registry=product.definition_registry())
    assert product.json_hash(encode_formula(helper))==product.HELPER_TARGET_SHA256['successor_value']


def test_complete_product_power_replays_with_one_new_induction_no_new_axioms():
    result=product.prove_product_power()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=product.prove_product_power()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
