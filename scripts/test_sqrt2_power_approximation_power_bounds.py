"""The sample cutoff estimates use the actual powers, including precision zero."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_power_bounds as bounds


def test_exact_three_actual_powers_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=bounds.frozen_approximation_power_bounds_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==3 and type(conclusion) is And
    assert len(bounds.canonical(encode_formula(target)))==5825
    c=bounds.source_contract()
    assert c["all_three_denominators_proved_nonzero"] is c["all_precision_indices_including_zero"] is True
    assert c["domination_bounds"]=="d<=p; d<=r"
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_six_definition_power_dag_is_reused():
    from sqrt2_power_positive_power_comparison import definition_registry
    before=definition_registry();after=bounds.definition_registry();seen=set();ids=set()
    assert len(after)==6 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert bounds.source_contract()["new_definition_ids"]==[]


def test_target_rejects_changed_exponent_base_or_domination_direction():
    source=bounds.NAMED_SOURCE
    for changed in (source.replace("Pow(2,k,d)","Pow(2,k,p)"),source.replace("Pow(3,S(2*k),p)","Pow(3,k,p)"),
                    source.replace("Pow(2,k+2,r)","Pow(2,2,r)"),source.replace("Le(d,p)","Le(p,d)")):
        with patch.object(bounds,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            bounds.frozen_approximation_power_bounds_target()


def test_actual_general_comparison_and_arithmetic_ancestor_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=bounds.definition_registry();found=set()
    for pin in bounds.ARCHIVES:
        rows=bounds.read_mixed_archive(pin)
        for name,source in bounds.ENDPOINT_SOURCES.items():
            if bounds.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            bounds.read_mixed_archive(bad)
    assert found==bounds.ENDPOINT_SOURCES.keys()


def test_exact_integer_power_models_include_zero_precision():
    for k in range(33):
        d,p,r=2**k,3**(2*k+1),2**(k+2)
        assert d>0 and p>0 and r>0 and d<=p and d<=r
        assert 2*k+1==k+(k+1)


def test_complete_power_bounds_replay_needs_no_new_induction_or_axiom():
    result=bounds.prove_approximation_power_bounds()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_length_identity_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=bounds.prove_approximation_power_bounds();node=result.provenance["helper_bundle_indices"]["length"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
