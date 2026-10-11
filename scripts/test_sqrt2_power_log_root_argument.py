"""Actual logarithm/root quotient computations, not an accuracy definition."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_log_root_argument as argument


def test_exact_unconditional_finite_argument_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=argument.frozen_log_root_argument_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(argument.canonical(encode_formula(target)))==6675
    c=argument.source_contract()
    assert c["prefix_length"]=="S(2*k)" and c["argument_numerator"]=="(3*x)*d" and c["argument_denominator"]=="(D*p)*s"
    assert c["denominator_nonzero_proved"] is c["argument_upper_one_proved"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_logarithm_identity"] is c["closes_IR072"] is False


def test_exact_minimal_computation_definition_dag_and_no_accuracy_clause():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=argument.definition_registry();seen=set();ids=set()
    assert len(registry)==16
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    spec=registry[argument.DEFINITION_NAME]
    assert spec.stable_id=="ND0447" and spec.conceptual_dependencies==argument.DEFINITION_DEPENDENCIES
    expected=parse_named(argument.DEFINITION_SOURCE,argument.DEFINITION_PARAMETERS,registry)
    assert spec.template_formula==expected
    assert argument.json_hash(encode_formula(expected))==argument.DEFINITION_AST_SHA256
    assert all(fragment not in argument.DEFINITION_SOURCE for fragment in ("Le(","~","CApprox","Exp","Accuracy"))
    assert argument.source_contract()["bounds_are_definition_clauses"] is False


def test_changed_quotient_length_range_or_graph_is_rejected():
    source=argument.NAMED_SOURCE
    for changed in (source.replace("~((D*p)*s)=0","((D*p)*s)=0"),
                    source.replace("(3*x)*d","(3*x)*s"),source.replace("Le((3*x)*d,(D*p)*s)","Le((D*p)*s,(3*x)*d)")):
        assert changed!=source
        with patch.object(argument,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            argument.frozen_log_root_argument_target()
    with patch.object(argument,"DEFINITION_SOURCE",argument.DEFINITION_SOURCE.replace("S(2*k)","2*k")),pytest.raises(ValueError):
        argument.definition_registry()


def test_shared_definition_identity_or_id_collision_cannot_be_silently_merged():
    registry=dict(argument.dyadic_registry())
    registry["Pow"]=replace(registry["Pow"],stable_id="PD9999")
    with patch.object(argument,"dyadic_registry",return_value=registry),pytest.raises(ValueError):
        argument.computation_registry()
    with patch.object(argument,"DEFINITION_ID","ND0446"),pytest.raises(ValueError):
        argument.definition_registry()


def test_exact_constructive_computations_and_bounds_have_actual_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=argument.definition_registry();found=set()
    for pin in argument.ARCHIVES:
        rows=argument.read_mixed_archive(pin)
        for name,source in argument.ENDPOINT_SOURCES.items():
            if argument.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            argument.read_mixed_archive(altered)
    assert found==argument.ENDPOINT_SOURCES.keys()


def test_finite_quotient_models_with_even_zero_padding_and_independent_scales():
    for k in range(9):
        d=2**k;s=isqrt(2*d*d);N=2*k+1
        common=lcm(*range(1,N,2)) if k else 1
        for scale in (1,2,3):
            D=scale*common;x=0
            for i in range(N):
                a=0 if i%2==0 else 2*D//i
                assert a==0 if i%2==0 else i*a==2*D
                x=3*x+a
            p=3**N
            L=sum((Fraction(2,(2*j+1)*3**(2*j+1)) for j in range(k)),Fraction())
            assert Fraction(3*x,D*p)==L and 3*x+3*D<=D*p
            assert D*p*s>0 and (3*x)*d<=(D*p)*s
            assert Fraction(3*x*d,D*p*s)==L*Fraction(d,s)


def test_complete_argument_construction_replay_without_new_induction_or_axioms():
    result=argument.prove_log_root_argument()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_range_lemma_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=argument.prove_log_root_argument();node=result.provenance["helper_bundle_indices"]["bounds"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
