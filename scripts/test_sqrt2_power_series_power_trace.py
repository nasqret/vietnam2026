"""Actual power tables and the boundary between computation and its properties."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_series_power_trace as powers


def test_exact_unconditional_power_target_allows_zero_width_and_exponent():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = powers.frozen_series_power_trace_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and not premises and type(conclusion) is Exists
    assert powers.json_hash(encode_formula(target))==powers.TARGET_SHA256
    assert len(powers.canonical(encode_formula(target)))==5108
    contract = powers.source_contract()
    assert contract["starts_at_truncated_unit"] is True
    assert contract["output_trace_supplied"] is contract["zero_constant_required"] is False
    assert contract["below_degree_vanishing"] is False
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_conservative_definition_dag_contains_execution_not_vanishing():
    registry = powers.definition_registry()
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    for number,name,parameters,source,dependencies,digest in powers.DEFINITION_ROWS:
        d = registry[name]
        assert d.stable_id==f"ND{number:04d}"
        assert d.parameters==parameters and d.arity==len(parameters)
        assert d.conceptual_dependencies==dependencies
    assert registry["NatPowerRow"].arity==7
    assert registry["NatPowerStep"].arity==9
    assert registry["NatPowerTrace"].arity==9
    assert "NatConvolutionPrefix" in powers.DEFINITION_ROWS[3][3]
    assert "vanish" not in " ".join(d[3] for d in powers.DEFINITION_ROWS)
    assert "NatUnitCoefficient" not in powers.DEFINITION_ROWS[3][3]


def test_changed_unit_or_computation_definition_is_rejected():
    for index,before,after in ((0,"a=1","a=0"),(3,"S k","k"),(4,"Lt(k,K)","Lt(k,S K)")):
        rows = list(powers.DEFINITION_ROWS)
        row = list(rows[index])
        assert before in row[3]
        row[3] = row[3].replace(before,after)
        rows[index] = tuple(row)
        with patch.object(powers,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
            powers.frozen_series_power_trace_target()


def test_exact_actual_convolution_archive_and_required_existence_endpoint():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    rows = powers.read_archive(powers.CONVOLUTION_ARCHIVE)
    assert len(rows)==126
    source = "forall ab ac L bb bc M N. exists cb cc. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N)"
    assert rows[123][1]==encode_formula(parse_named(source,registry=powers.definition_registry()))
    for name,(old,source) in powers.EXTRA_ENDPOINTS.items():
        assert rows[powers.CONVOLUTION_ANCESTORS.index(old)][1]==encode_formula(parse_named(source,registry=powers.definition_registry()))


def test_forged_compressed_or_payload_archive_hash_is_rejected():
    for field in ("sha256","bundle_sha256","target_ast_sha256"):
        pin = dict(powers.CONVOLUTION_ARCHIVE)
        pin[field] = "0"*64
        with pytest.raises(ValueError):
            powers.read_archive(pin)


def test_finite_power_model_uses_all_rows_and_truncates_every_successor():
    def multiply(left,right,width):
        return [sum((left[j] if j<len(left) else 0)*(right[i-j] if i-j<len(right) else 0)
                    for j in range(i+1)) for i in range(width)]
    for source in ([],[0],[1],[1,2,3],[0,2,0,3]):
        for width in range(6):
            for exponent in range(6):
                trace = [[1]+[0]*(width-1) if width else []]
                for _ in range(exponent):
                    trace.append(multiply(source,trace[-1],width))
                assert len(trace)==exponent+1
                assert all(len(row)==width for row in trace)
                for k in range(exponent):
                    assert trace[k+1]==multiply(source,trace[k],width)
    # A nonzero constant input is allowed: the definition is not secretly
    # restricted to the positive-degree case needed in the later theorem.
    assert multiply([2],[4,0,0],3)==[8,0,0]


def test_guarded_two_inductions_replay_and_reject_false_target_or_body():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = powers.prove_series_power_trace()
    assert result.receipt.target==powers.frozen_series_power_trace_target()
    assert len(result.bundle.nodes)==121 and result.receipt.total_body_nodes==5826
    assert result.provenance["actual_ancestor_nodes"]==114
    assert result.provenance["discarded_unreachable_ids"]==[21,108,109,111,113,115,116,118,121,122,124,125]
    assert result.provenance["ordered_dependency_remapping_only"] is True
    assert result.provenance["actual_power_rows_constructed"] is True
    assert result.provenance["new_induction_count"]==2
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
