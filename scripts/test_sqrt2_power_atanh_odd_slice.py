"""The supplied coefficient table, not an assumed series identity, is decoded."""
from dataclasses import replace
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_atanh_odd_slice as odd_slice


def test_exact_constructed_odd_slice_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=odd_slice.frozen_atanh_odd_slice_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==1 and type(conclusion) is Exists
    assert len(odd_slice.canonical(encode_formula(target)))==2257
    c=odd_slice.source_contract()
    assert c["actual_supplied_atanh_prefix_preserved"] is c["actual_odd_index_slice_constructed"] is True
    assert c["empty_slice_and_zero_scale_allowed"] is c["parity_uses_actual_even_not_odd_certificate"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_minimal_existing_six_definition_dag_is_preserved():
    source=odd_slice.source_registry();registry=odd_slice.definition_registry();seen=set();ids=set()
    assert set(registry)=={"Le","Lt","BetaAt","NatAffineSlice","NatAtanhCoefficient","NatAtanhPrefix"}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert registry["NatAffineSlice"].stable_id=="ND0411"
    assert odd_slice.source_contract()["new_definition_ids"]==[]


def test_target_rejects_wrong_slice_stride_parity_or_quotient():
    source=odd_slice.NAMED_SOURCE
    for changed in (source.replace("NatAffineSlice(ab,ac,1,2,bb,bc,k)","NatAffineSlice(ab,ac,0,2,bb,bc,k)"),
                    source.replace("S(2*k)","2*k"),source.replace("(S(2*j))*a=2*d","(S(2*j))*a=d"),
                    source.replace("BetaAt(ab,ac,2*j,a)","BetaAt(ab,ac,S(2*j),a)")):
        assert changed!=source
        with patch.object(odd_slice,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            odd_slice.frozen_atanh_odd_slice_target()


def test_real_parity_affine_slice_and_order_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=odd_slice.definition_registry();found=set()
    for pin in odd_slice.ARCHIVES:
        rows=odd_slice.read_mixed_archive(pin)
        for name,source in odd_slice.ENDPOINT_SOURCES.items():
            if odd_slice.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            odd_slice.read_mixed_archive(bad)
    assert found==odd_slice.ENDPOINT_SOURCES.keys()


def test_exact_odd_reciprocal_models_include_empty_and_zero_scale():
    for k in range(14):
        for scale in range(3):
            d=scale*(lcm(*range(1,2*k,2)) if k else 1)
            original=[0 if i%2==0 else 2*d//i for i in range(2*k+1)]
            selected=original[1:2*k:2]
            assert len(selected)==k
            for j,a in enumerate(selected):
                assert selected[j]==original[1+2*j] and (2*j+1)*a==2*d
                assert 2*j+1<2*k+1
            for j in range(k+1):
                assert original[2*j]==0 and 2*j<2*k+1


def test_complete_odd_slice_replay_needs_no_new_induction_or_axioms():
    result=odd_slice.prove_atanh_odd_slice()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_parity_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=odd_slice.prove_atanh_odd_slice();node=result.provenance["helper_bundle_indices"]["even_coefficient"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
