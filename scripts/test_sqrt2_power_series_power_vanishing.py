"""Actual power vanishing, with the essential zero-input premise exposed."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_series_power_vanishing as vanishing


def test_exact_target_constructs_trace_and_all_rows_vanish_below_their_exponents():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = vanishing.frozen_series_power_vanishing_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==1 and type(conclusion) is Exists
    assert vanishing.json_hash(encode_formula(target))==vanishing.TARGET_SHA256
    assert len(vanishing.canonical(encode_formula(target)))==6721
    contract = vanishing.source_contract()
    assert contract["input_vanishes_below_one_required"] is True
    assert contract["all_rows_through_requested_exponent"] is True
    assert contract["output_trace_supplied"] is contract["execution_contains_vanishing"] is False
    assert contract["exp_composition_recurrence"] is contract["closes_IR079"] is contract["closes_IR072"] is False


def test_definition_dag_keeps_vanishing_separate_from_unchanged_execution():
    from peano_lab.library.proof_bundle import encode_formula
    registry,old = vanishing.definition_registry(),vanishing.power_registry()
    for name in old:
        assert registry[name].template_formula==old[name].template_formula
    definition = registry["NatZeroBefore"]
    assert definition.stable_id=="ND0408" and definition.arity==4
    assert definition.conceptual_dependencies==("Lt","BetaZeroExtend")
    assert vanishing.json_hash(encode_formula(definition.template_formula))==vanishing.DEFINITION_SHA256
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert "NatZeroBefore" not in registry["NatPowerTrace"].conceptual_dependencies


def test_dropping_zero_premise_or_length_restriction_is_rejected():
    for before in (vanishing.INPUT_ZERO+" -> ","Le(k,K) -> "):
        assert before in vanishing.NAMED_SOURCE
        with patch.object(vanishing,"NAMED_SOURCE",vanishing.NAMED_SOURCE.replace(before,"")),pytest.raises(ValueError):
            vanishing.frozen_series_power_vanishing_target()
    with patch.object(vanishing,"DEFINITION_SOURCE",vanishing.DEFINITION_SOURCE.replace("a=0","a=1")),pytest.raises(ValueError):
        vanishing.definition_registry()


def test_all_three_actual_archives_bind_their_original_targets():
    from sqrt2_power_convolution_vanishing import frozen_convolution_vanishing_target
    from sqrt2_power_series_power_trace import frozen_series_power_trace_target
    from sqrt2_power_natural_convolution import frozen_natural_convolution_target
    from peano_lab.library.proof_bundle import encode_formula
    for pin,target in (
        (vanishing.CONVOLUTION_ARCHIVE,frozen_natural_convolution_target()),
        (vanishing.POWER_ARCHIVE,frozen_series_power_trace_target()),
        (vanishing.VANISHING_ARCHIVE,frozen_convolution_vanishing_target()),
    ):
        rows = vanishing.read_archive(pin)
        assert rows[pin["root"]][1]==encode_formula(target)


def test_fabricated_ancestor_target_is_rejected_even_with_original_payload():
    for original in (vanishing.CONVOLUTION_ARCHIVE,vanishing.POWER_ARCHIVE,vanishing.VANISHING_ARCHIVE):
        changed = dict(original)
        changed["target_ast_sha256"] = "0"*64
        with pytest.raises(ValueError):
            vanishing.read_archive(changed)


def test_finite_model_zero_constant_is_necessary_and_empty_width_is_allowed():
    def multiply(left,right,width):
        return [sum((left[j] if j<len(left) else 0)*(right[i-j] if i-j<len(right) else 0)
                    for j in range(i+1)) for i in range(width)]
    for source in ([],[0],[0,1],[0,2,0,3],[0,0,1,4]):
        for width in range(7):
            value = [1]+[0]*(width-1) if width else []
            for exponent in range(8):
                for index in range(exponent):
                    assert (value[index] if index<width else 0)==0
                value = multiply(source,value,width)
    assert multiply([2],[1,0,0],3)[0]==2
    assert multiply([2],[2,0,0],3)[0]==4


def test_guarded_full_constructive_vanishing_induction_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = vanishing.prove_series_power_vanishing()
    assert result.receipt.target==vanishing.frozen_series_power_vanishing_target()
    assert len(result.bundle.nodes)==131 and result.receipt.total_body_nodes==6620
    assert result.provenance["actual_power_rows_constructed"] is True
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
