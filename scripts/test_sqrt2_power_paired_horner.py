"""Paired evaluation consumes two actual long steps, including the even zero."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest
import sqrt2_power_paired_horner as paired


def test_exact_supplied_histories_and_zero_even_entries_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=paired.frozen_paired_horner_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==8 and len(premises)==4 and type(conclusion) is Eq
    assert len(paired.canonical(encode_formula(target)))==4094
    c=paired.source_contract()
    assert c["actual_supplied_odd_slice_and_both_horner_values_preserved"] is True
    assert c["zero_even_entries_through_terminal_index_required"] is c["zero_base_and_empty_odd_slice_allowed"] is True
    assert c["all_pairs_compared_by_explicit_induction"] is True
    assert c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_seven_existing_definitions_form_the_exact_minimal_dag():
    source=paired.source_registry();registry=paired.definition_registry();seen=set();ids=set()
    assert set(registry)=={"Le","Lt","BetaAt","NatAffineSlice","NatScaledHornerStep","NatScaledHornerTrace","NatHornerValue"}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert paired.source_contract()["new_definition_ids"]==[]


def test_target_rejects_lost_terminal_even_entry_or_wrong_squared_base():
    source=paired.NAMED_SOURCE
    for changed in (source.replace("Le(j,K)","Lt(j,K)"),source.replace("NatHornerValue(bb,bc,t*t,K,y)","NatHornerValue(bb,bc,t,K,y)"),
                    source.replace("NatAffineSlice(ab,ac,1,2,bb,bc,K)","NatAffineSlice(ab,ac,0,2,bb,bc,K)"),
                    source.replace("x=t*y","x=y")):
        assert changed!=source
        with patch.object(paired,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            paired.frozen_paired_horner_target()


def test_actual_index_horner_and_order_ancestor_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=paired.definition_registry();found=set()
    for pin in paired.ARCHIVES:
        rows=paired.read_mixed_archive(pin)
        for name,source in paired.ENDPOINT_SOURCES.items():
            if paired.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            paired.read_mixed_archive(bad)
    assert found==paired.ENDPOINT_SOURCES.keys()


def test_exact_pairwise_models_cover_zero_base_empty_slice_and_terminal_zero():
    def history(values,base):
        rows=[0]
        for a in values:
            rows.append(base*rows[-1]+a)
        return rows
    for K in range(5):
        for odd in product(range(3),repeat=K):
            values=[0]
            for a in odd:
                values.extend((a,0))
            for base in range(5):
                left,right=history(values,base),history(odd,base*base)
                for j in range(K+1):
                    assert left[2*j+1]==base*right[j]
    # The missing terminal-zero premise is mathematically essential.
    assert history([0,0,1],3)[-1]!=3*history([0],9)[-1]
    assert history([1],3)[-1]!=3*history([],9)[-1]


def test_complete_paired_replay_uses_one_explicit_induction_and_no_axiom():
    result=paired.prove_paired_horner()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_pair_step_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=paired.prove_paired_horner();node=result.provenance["helper_bundle_indices"]["paired_step"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
