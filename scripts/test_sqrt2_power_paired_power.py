"""Odd powers normalize using actual paired successor computations."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_paired_power as paired


def test_exact_two_actual_powers_contract_allows_zero_base():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    target=paired.frozen_paired_power_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==2 and type(conclusion) is Eq
    c=paired.source_contract()
    assert c["both_actual_supplied_power_graphs_preserved"] is c["zero_base_and_zero_index_allowed"] is True
    assert c["even_power_compared_by_explicit_induction"] is True
    assert c["cancellation_used"] is c["positivity_premise_required"] is False
    assert c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_exact_five_definition_power_dag_is_reused():
    source=paired.source_registry();registry=paired.definition_registry();seen=set();ids=set()
    assert set(registry)=={"Lt","BetaAt","Product","Repeat","Pow"}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert paired.source_contract()["new_definition_ids"]==[]


def test_target_rejects_wrong_doubled_exponent_squared_base_or_factor():
    source=paired.NAMED_SOURCE
    for changed in (source.replace("S(2*k)","2*k"),source.replace("Pow(t*t,k,y)","Pow(t,k,y)"),
                    source.replace("x=t*y","x=y"),source.replace("Pow(t,S(2*k),x)","Pow(t,S(2*k),y)")):
        assert changed!=source
        with patch.object(paired,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            paired.frozen_paired_power_target()


def test_actual_power_successor_and_doubling_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=paired.definition_registry();found=set()
    for pin in paired.ARCHIVES:
        rows=paired.read_mixed_archive(pin)
        for name,source in paired.ENDPOINT_SOURCES.items():
            if paired.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            paired.read_mixed_archive(bad)
    assert found==paired.ENDPOINT_SOURCES.keys()


def test_integer_models_cover_zero_to_zero_power_convention():
    for t in range(7):
        for k in range(10):
            assert t**(2*k)==(t*t)**k
            assert t**(2*k+1)==t*(t*t)**k
    assert 0**0==1 and 0**1==0 and 3**(2*0+1)==3


def test_complete_paired_power_replay_uses_one_induction_without_axioms():
    result=paired.prove_paired_power()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_paired_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=paired.prove_paired_power();node=result.provenance["helper_bundle_indices"]["even_power"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
