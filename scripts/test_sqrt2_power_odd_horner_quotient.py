"""Finite odd-Horner normalization preserves actual computations and validity."""
from dataclasses import replace
from fractions import Fraction
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_odd_horner_quotient as quotient


def test_exact_four_premise_nine_part_rational_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target=quotient.frozen_odd_horner_quotient_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==4
    for _ in quotient.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    for _ in range(8):
        assert type(conclusion) is And
        conclusion=conclusion.right
    assert len(quotient.canonical(encode_formula(target)))==9453
    c=quotient.source_contract()
    assert c["all_rational_denominators_proved_nonzero"] is c["actual_odd_slice_value_and_power_constructed"] is True
    assert c["empty_odd_slice_allowed"] is c["positive_coefficient_scale_required"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["infinite_odd_sum_identity_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_exact_fourteen_definition_dag_reuses_rational_identities():
    registry=quotient.definition_registry();seen=set();ids=set()
    from sqrt2_power_definitions import DEFINITIONS
    assert set(registry)=={"Le","Lt","BetaAt","NatAffineSlice","NatScaledHornerStep","NatScaledHornerTrace","NatHornerValue",
        "NatAtanhCoefficient","NatAtanhPrefix","Product","Repeat","Pow","IRatValid","IRatEq"}
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert registry["IRatValid"]==DEFINITIONS["IRatValid"] and registry["IRatEq"]==DEFINITIONS["IRatEq"]
    assert quotient.source_contract()["new_definition_ids"]==[]


def test_target_rejects_zero_scale_missing_factor_and_wrong_odd_base():
    source=quotient.NAMED_SOURCE
    for changed in (source.replace("~d=0 -> ",""),source.replace("Pow(9,k,q)","Pow(3,k,q)"),
                    source.replace("x=3*y","x=y"),source.replace("3*y,0,d*q","y,0,d*q"),
                    source.replace("NatAffineSlice(ab,ac,1,2,bb,bc,k)","NatAffineSlice(ab,ac,0,2,bb,bc,k)")):
        assert changed!=source
        with patch.object(quotient,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            quotient.frozen_odd_horner_quotient_target()


def test_actual_paired_and_positivity_ancestors_are_uniquely_owned():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=quotient.definition_registry();found=set()
    for pin in quotient.ARCHIVES:
        rows=quotient.read_mixed_archive(pin)
        for name,source in quotient.ENDPOINT_SOURCES.items():
            if quotient.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            quotient.read_mixed_archive(bad)
    assert found==quotient.ENDPOINT_SOURCES.keys()


def test_exact_rational_models_include_empty_series_and_independent_scale():
    def horner(values,base):
        result=0
        for value in values:
            result=base*result+value
        return result
    for k in range(8):
        common=lcm(*range(1,2*k,2)) if k else 1
        for factor in range(1,4):
            d=common*factor;values=[2*d//i if i%2 else 0 for i in range(2*k+1)]
            odd=values[1::2];x=horner(values,3);y=horner(odd,9);p=3**(2*k+1);q=9**k
            assert x==3*y and p==3*q and d*p>0 and d*q>0
            assert all((2*j+1)*a==2*d for j,a in enumerate(odd))
            assert Fraction(3*x,d*p)==Fraction(3*y,d*q)==sum((Fraction(2,(2*j+1)*3**(2*j+1)) for j in range(k)),Fraction(0))


def test_complete_quotient_replay_has_no_new_induction_or_axiom():
    result=quotient.prove_odd_horner_quotient()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_quotient_body_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=quotient.prove_odd_horner_quotient();node=result.provenance["helper_bundle_indices"]["quotient"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
