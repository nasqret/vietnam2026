"""Actual dyadic roots are positive and their squares have explicit error."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2_square_error as square


def test_exact_supplied_positive_square_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=square.frozen_dyadic_sqrt2_square_error_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==3 and len(premises)==1 and type(conclusion) is And
    assert len(square.canonical(encode_formula(target)))==2677
    c=square.source_contract()
    assert c["supplied_actual_computation_preserved"] is c["denominator_and_root_nonzero_proved"] is c["zero_precision_allowed"] is True
    assert c["integer_square_error"]=="s*s<=2*d*d<=s*s+4*d"
    assert c["new_induction_needed"] is c["real_square_root_identity_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_computation_graph_without_square_error_clause():
    from sqrt2_power_dyadic_sqrt2 import definition_registry,DEFINITION_SOURCE
    assert square.definition_registry is definition_registry
    assert DEFINITION_SOURCE=="Pow(2,k,d) /\\ FloorSqrt(2*(d*d),s)"
    c=square.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_changed_root_guard_or_residual_factor_is_rejected():
    original=square.NAMED_SOURCE
    for source in (original.replace("~s=0","s=0"),original.replace("Le(d,s)","Lt(d,s)"),
                   original.replace("s*s+2*(2*d)","s*s"),original.replace("2*(d*d)","3*(d*d)")):
        assert source!=original
        with patch.object(square,"NAMED_SOURCE",source),pytest.raises(ValueError):
            square.frozen_dyadic_sqrt2_square_error_target()


def test_actual_scaled_root_positive_power_and_order_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=square.definition_registry();found=set()
    for pin in square.ARCHIVES:
        rows=square.read_mixed_archive(pin)
        for name,source in square.ENDPOINT_SOURCES.items():
            if square.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            square.read_mixed_archive(altered)
    assert found==square.ENDPOINT_SOURCES.keys()


def test_finite_floor_residual_and_dyadic_square_error_models():
    for n in range(400):
        s=isqrt(n)
        assert s*s<=n<=s*s+s+s
    for k in range(15):
        d=2**k;s=isqrt(2*d*d)
        assert d!=0 and s!=0 and d<=s<2*d
        assert s*s<=2*d*d<=s*s+4*d
        assert 0<=2-Fraction(s,d)**2<=Fraction(4,d)


def test_complete_square_error_replay_without_new_induction_or_axioms():
    result=square.prove_dyadic_sqrt2_square_error()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_floor_residual_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=square.prove_dyadic_sqrt2_square_error();node=result.provenance["helper_bundle_indices"]["floor_residual"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
