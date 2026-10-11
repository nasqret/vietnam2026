"""Actual power comparison: constructive induction, no positive small base."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest
import sqrt2_power_positive_power_comparison as comparison


def test_exact_supplied_power_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target=comparison.frozen_positive_power_comparison_target()
    binders,premises,_=strip_target(target)
    assert binders==6 and len(premises)==4
    assert len(comparison.canonical(encode_formula(target)))==3691
    c=comparison.source_contract()
    assert c["zero_smaller_base_exponent_and_increment_allowed"] is c["larger_base_nonzero_required"] is True
    assert c["same_exponent_base_comparison_by_explicit_induction"] is True
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_only_existing_power_definition_dependencies_are_exposed():
    before=comparison.argument_registry();after=comparison.definition_registry();seen=set();ids=set()
    assert tuple(after)==("Lt","BetaAt","Product","Repeat","Pow","Le")
    for name,spec in after.items():
        assert spec==before[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert comparison.source_contract()["new_definition_ids"]==[]


def test_target_rejects_missing_order_positivity_or_changed_powers():
    source=comparison.NAMED_SOURCE
    for changed in (source.replace("Le(a,b) -> ",""),source.replace("~b=0 -> ",""),
                    source.replace("Pow(b,k+l,y)","Pow(b,l,y)"),source.replace("Le(x,y)","Le(y,x)")):
        with patch.object(comparison,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            comparison.frozen_positive_power_comparison_target()


def test_actual_power_laws_and_explicit_unambiguous_archive_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=comparison.definition_registry();found=set()
    assert comparison.ENDPOINT_OWNERS["mul_left_mono"]=="CV071"
    for pin in comparison.ARCHIVES:
        rows=comparison.read_mixed_archive(pin)
        for name,source in comparison.ENDPOINT_SOURCES.items():
            if comparison.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            comparison.read_mixed_archive(bad)
    assert found==comparison.ENDPOINT_SOURCES.keys()


def test_natural_models_zero_boundaries_and_necessary_positive_large_base():
    count=0
    for a,b,k,l in product(range(6),range(1,6),range(6),range(6)):
        if a<=b:
            assert a**k<=b**(k+l)
            count+=1
    assert count>100
    assert not 0**0<=0**1  # Dropping the nonzero larger-base guard is unsound.
    for a,b,x,y in product(range(4),repeat=4):
        if a<=b and x<=y:
            assert x*a<=y*b
        if b:
            assert a<=a*b


def test_complete_power_replay_uses_exactly_one_new_induction_and_no_axioms():
    result=comparison.prove_positive_power_comparison()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_induction_body_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=comparison.prove_positive_power_comparison();node=result.provenance["helper_bundle_indices"]["base_monotone"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
