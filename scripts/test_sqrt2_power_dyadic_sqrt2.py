"""The dyadic computation is total and unique without defining in its bounds."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2 as dyadic


def test_exact_unconditional_dyadic_computation_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=dyadic.frozen_dyadic_sqrt2_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and premises==[] and type(conclusion) is Exists
    assert len(dyadic.canonical(encode_formula(target)))==4435
    c=dyadic.source_contract()
    assert c["actual_power_and_floor_root_constructed"] is c["denominator_and_root_nonzero_proved"] is c["unique_output_pair"] is True
    assert c["all_precision_indices_including_zero"] is True
    assert c["new_induction_needed"] is c["dyadic_interval_width_proved"] is c["real_square_root_interpretation"] is c["closes_IR072"] is False


def test_conservative_computation_definition_and_complete_dependency_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry=dyadic.definition_registry();spec=registry["DyadicSqrt2"]
    assert spec.stable_id=="ND0446" and spec.parameters==("k","d","s")
    assert spec.conceptual_dependencies==("Pow","FloorSqrt")
    assert spec.template_formula==parse_named("Pow(2,k,d) /\\ FloorSqrt(2*(d*d),s)",spec.parameters,registry)
    assert dyadic.json_hash(encode_formula(spec.template_formula))==dyadic.DEFINITION_AST_SHA256
    assert parse_formula_in_context(spec.template_source,list(spec.parameters))==spec.template_formula
    seen=set()
    for name,d in registry.items():
        assert set(d.conceptual_dependencies)<=seen
        seen.add(name)
    assert seen=={"Le","Lt","FloorSqrt","BetaAt","Product","Repeat","Pow","DyadicSqrt2"}
    c=dyadic.source_contract()
    assert c["definition_contains_accuracy_or_bounds"] is False
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_definition_collision_and_hidden_accuracy_clause_are_rejected():
    with patch.object(dyadic,"DEFINITION_ID","ND0445"),pytest.raises(ValueError):
        dyadic.definition_registry()
    with patch.object(dyadic,"DEFINITION_NAME","FloorSqrt"),pytest.raises(ValueError):
        dyadic.definition_registry()
    with patch.object(dyadic,"DEFINITION_SOURCE",dyadic.DEFINITION_SOURCE+" /\\ Le(d,s)"),pytest.raises(ValueError):
        dyadic.definition_registry()
    original=dyadic.NAMED_SOURCE
    for source in (original.replace("~s=0","s=0"),original.replace("Lt(s,2*d)","Lt(s,d)"),original.replace("q=d /\\ t=s","q=s /\\ t=s")):
        assert source!=original
        with patch.object(dyadic,"NAMED_SOURCE",source),pytest.raises(ValueError):
            dyadic.frozen_dyadic_sqrt2_target()


def test_actual_power_totality_uniqueness_nonzero_and_scaled_root_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=dyadic.definition_registry();found=set()
    for pin in dyadic.ARCHIVES:
        rows=dyadic.read_mixed_archive(pin)
        for name,source in dyadic.ENDPOINT_SOURCES.items():
            if dyadic.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            dyadic.read_mixed_archive(altered)
    assert found==dyadic.ENDPOINT_SOURCES.keys()


def test_finite_dyadic_models_include_precision_zero():
    for k in range(12):
        d=2**k;s=isqrt(2*d*d)
        assert d!=0 and s!=0 and d<=s<2*d
        assert s*s<=2*d*d<(s+1)*(s+1)
    assert (2**0,isqrt(2*(2**0)**2))==(1,1)


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result=dyadic.prove_dyadic_sqrt2()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_computation_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=dyadic.prove_dyadic_sqrt2();node=result.provenance["helper_bundle_indices"]["SQ004"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
