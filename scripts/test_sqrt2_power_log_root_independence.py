"""Value identity preserves separate positive scales and actual encodings."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_log_root_independence as independence


def test_exact_supplied_graph_value_independence_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=independence.frozen_log_root_independence_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==15 and len(premises)==4 and type(conclusion) is And
    assert len(independence.canonical(encode_formula(target)))==13123
    c=independence.source_contract()
    assert c["positive_coefficient_scales_required"] is c["coefficient_scales_and_table_codes_not_equated"] is True
    assert c["both_quotient_denominators_proved_nonzero"] is c["exact_rational_cross_product_identity"] is True
    assert c["exponential_output_uniqueness_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_existing_computation_definition_is_unchanged():
    from sqrt2_power_log_root_argument import definition_registry
    assert independence.definition_registry is definition_registry
    c=independence.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_missing_scale_guard_wrong_precision_or_cross_product_is_rejected():
    original=independence.NAMED_SOURCE
    for altered in (original.replace("~D=0 -> ",""),original.replace("~E=0 -> ",""),
                    original.replace("NatSqrt2LogArgument(k,e", "NatSqrt2LogArgument(S k,e"),
                    original.replace("((3*x)*d)*((E*h)*t)","((3*x)*d)*((D*p)*s)")):
        assert altered!=original
        with patch.object(independence,"NAMED_SOURCE",altered),pytest.raises(ValueError):
            independence.frozen_log_root_independence_target()


def test_every_selected_uniqueness_scale_and_nonzero_endpoint_has_actual_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=independence.definition_registry();found=set()
    for pin in independence.ARCHIVES:
        rows=independence.read_mixed_archive(pin)
        for name,source in independence.ENDPOINT_SOURCES.items():
            if independence.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            independence.read_mixed_archive(altered)
    assert found==independence.ENDPOINT_SOURCES.keys()


def test_exact_cross_products_for_different_positive_coefficient_scales():
    for k in range(9):
        N=2*k+1;d=2**k;s=isqrt(2*d*d);p=3**N
        common=lcm(*range(1,N,2)) if k else 1
        values=[]
        for factor in (1,2,3):
            D=factor*common;x=0
            for i in range(N):
                x=3*x+(0 if i%2==0 else 2*D//i)
            values.append((D,x))
        for D,x in values:
            for E,z in values:
                e,t,h=d,s,p
                assert E*x==D*z and D*p*s!=0 and E*h*t!=0
                assert ((3*x)*d)*((E*h)*t)==((3*z)*e)*((D*p)*s)
                assert Fraction(3*x*d,D*p*s)==Fraction(3*z*e,E*h*t)
        assert values[0][0]!=values[1][0]


def test_complete_independence_replay_without_new_induction_or_axioms():
    result=independence.prove_log_root_independence()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_cross_product_helper_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=independence.prove_log_root_independence();node=result.provenance["helper_bundle_indices"]["cross_product"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
