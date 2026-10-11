"""The sqrt(2) bracket is computed, unique, positive and strictly bounded."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_scaled_sqrt2 as scaled


def test_exact_constructed_scaled_root_and_positivity_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=scaled.frozen_scaled_sqrt2_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and len(premises)==1 and type(conclusion) is Exists
    assert len(scaled.canonical(encode_formula(target)))==925
    c=scaled.source_contract()
    assert c["actual_floor_root_constructed"] is c["floor_root_unique"] is c["root_nonzero_proved"] is True
    assert c["nonzero_input_scale_required"] is c["arbitrary_positive_scale"] is True
    assert c["integer_bounds"]=="d<=s<2*d"
    assert c["new_induction_needed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_floor_graph_does_not_include_promised_bounds():
    from sqrt2_power_floor_sqrt import definition_registry
    assert scaled.definition_registry is definition_registry
    c=scaled.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0
    assert set(scaled.definition_registry())=={"Le","Lt","FloorSqrt"}


def test_changed_input_guard_radical_or_bound_is_rejected():
    original=scaled.NAMED_SOURCE
    for source in (original.replace("~d=0 -> ",""),original.replace("2*(d*d)","3*(d*d)"),
                   original.replace("Lt(s,2*d)","Lt(s,d)"),original.replace("~s=0","s=0"),
                   original.replace("t=s","t=d")):
        assert source!=original
        with patch.object(scaled,"NAMED_SOURCE",source),pytest.raises(ValueError):
            scaled.frozen_scaled_sqrt2_target()


def test_exact_total_unique_comparison_and_positive_arithmetic_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=scaled.definition_registry();found=set()
    for pin in scaled.ARCHIVES:
        rows=scaled.read_mixed_archive(pin)
        for name,source in scaled.ENDPOINT_SOURCES.items():
            if scaled.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            scaled.read_mixed_archive(altered)
    assert found==scaled.ENDPOINT_SOURCES.keys()


def test_positive_scale_models_and_zero_scale_counterexample():
    for d in range(1,129):
        n=2*d*d;s=isqrt(n)
        assert s*s<=n<(s+1)*(s+1) and d<=s<2*d and s!=0
        assert d*d<=n<(2*d)*(2*d)
        assert [t for t in range(s+2) if t*t<=n<(t+1)*(t+1)]==[s]
    d=s=0
    assert s*s<=2*d*d<(s+1)*(s+1)
    assert not s<2*d and not s!=0


def test_complete_replay_has_no_new_induction_axioms_or_external_authority():
    result=scaled.prove_scaled_sqrt2()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["solver_calls"]==0 and result.provenance["external_certificate_references"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_arithmetic_bound_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=scaled.prove_scaled_sqrt2();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
