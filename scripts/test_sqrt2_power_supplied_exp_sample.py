"""The computation graph implies its laws for every supplied witness tuple."""
from dataclasses import replace
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_supplied_exp_sample as supplied


def test_exact_universal_supplied_sample_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=supplied.frozen_supplied_exp_sample_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==16 and len(premises)==2 and type(conclusion) is And
    assert len(supplied.canonical(encode_formula(target)))==22646
    c=supplied.source_contract()
    assert c["all_supplied_graph_witnesses_preserved"] is c["no_replacement_code_or_existential_constructor_used"] is True
    assert c["argument_bound_one_proved"] is c["same_table_recurrence_and_all_index_normalization_proved"] is True
    assert c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_no_accuracy_or_nonzero_clause_added_to_computation_definition():
    from sqrt2_power_exp_sample import definition_registry,DEFINITION_SOURCE
    assert supplied.definition_registry is definition_registry
    assert "~" not in DEFINITION_SOURCE and "Le(" not in DEFINITION_SOURCE
    c=supplied.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_positive_scale_recurrence_normalization_and_head_cannot_be_weakened():
    original=supplied.NAMED_SOURCE
    for changed in (original.replace("~D=0 -> ",""),original.replace("~w0=0","w0=0"),
                    original.replace("w0*q","w0+q"),original.replace("(k+2)","(k+1)")):
        assert changed!=original
        with patch.object(supplied,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            supplied.frozen_supplied_exp_sample_target()


def test_selected_supplied_table_and_factorial_laws_have_exact_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=supplied.definition_registry();found=set()
    assert all("exists" not in name for name in supplied.ENDPOINT_SOURCES)
    for pin in supplied.ARCHIVES:
        rows=supplied.read_mixed_archive(pin)
        for name,source in supplied.ENDPOINT_SOURCES.items():
            if supplied.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            supplied.read_mixed_archive(bad)
    assert found==supplied.ENDPOINT_SOURCES.keys()


def test_finite_arbitrary_positive_denominators_and_zero_arguments():
    for N in range(9):
        f=factorial(N)
        assert f!=0
        for v in range(1,7):
            for u in range(v+1):
                h=v**N;head=f*h
                weights=[(f//factorial(j))*v**(N-j) for j in range(N+1)]
                terms=[weights[j]*u**j for j in range(N+1)]
                assert head!=0 and terms[0]==head
                for j,a in enumerate(terms):
                    assert (a*factorial(j))*v**j==head*u**j
                    if j<N:
                        assert ((j+1)*v)*terms[j+1]==u*a


def test_complete_supplied_sample_replay_has_one_explicit_induction():
    result=supplied.prove_supplied_exp_sample()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_factorial_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=supplied.prove_supplied_exp_sample();node=result.provenance["helper_bundle_indices"]["factorial_nonzero"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
