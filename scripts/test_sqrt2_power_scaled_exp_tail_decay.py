"""Uniform finite outer-exponential tail decay with actual cutoff powers."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_scaled_exp_tail_decay as decay


def test_exact_uniform_cutoff_decay_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=decay.frozen_scaled_exp_tail_decay_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==7 and len(premises)==4 and type(conclusion) is Exists
    assert decay.json_hash(encode_formula(target))==decay.TARGET_SHA256
    assert len(decay.canonical(encode_formula(target)))==6101
    assert len(decay.OUTPUTS)==5 and len(decay.PARTS)==7
    c=decay.source_contract()
    assert c["actual_power_first_omitted_term_slice_ratio_and_sum_constructed"] is True
    assert c["uniform_in_extra_finite_horizon"] is c["supplied_term_table_and_initial_scale_preserved"] is True
    assert c["infinite_remainder_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_hidden_nonzero_initial_scale():
    from sqrt2_power_scaled_exp_tail import definition_registry
    assert decay.definition_registry()==definition_registry()
    assert decay.source_contract()["new_definition_ids"]==[]
    assert decay.source_contract()["definition_admissions"]==decay.source_contract()["IR_parents_closed"]==0
    assert "~a0=0" not in decay.NAMED_SOURCE


def test_changed_cutoff_power_scale_or_supplied_trace_is_rejected():
    original=decay.NAMED_SOURCE
    for source in (original.replace("~d=0 -> ",""),
                   original.replace("Pow(2,m,p)","Pow(2,S m,p)"),
                   original.replace("BetaAt(tb,tc,0,a0)","BetaAt(tc,tb,0,a0)"),
                   original.replace("Le(p*a,a0)","Le(p*a,a)"),
                   original.replace("Le(p*s,2*a0)","Le(p*s,a0)")):
        assert source!=original
        with patch.object(decay,"NAMED_SOURCE",source),pytest.raises(ValueError):
            decay.frozen_scaled_exp_tail_decay_target()


def test_owned_actual_tail_power_and_order_proofs():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decay.definition_registry();found=set()
    for pin in decay.ARCHIVES:
        rows=decay.read_mixed_archive(pin)
        for name,source in decay.ENDPOINT_SOURCES.items():
            if decay.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            decay.read_mixed_archive(altered)
    assert found==decay.ENDPOINT_SOURCES.keys()


def test_finite_exponential_decay_including_zero_argument_and_scale():
    from math import factorial
    for d in range(1,5):
        for x in range(d+1):
            for scale in (0,1,3):
                for m in range(5):
                    for N in range(5):
                        M=m+1;L=M+N;p=2**m
                        T=[scale*factorial(L)//factorial(j)*d**(L-j)*x**j for j in range(L+1)]
                        assert all(((j+1)*d)*T[j+1]==x*T[j] for j in range(L))
                        assert all(2**k*T[k+1]<=T[0] for k in range(L))
                        U=T[M:]
                        assert p*U[0]<=T[0] and p*sum(U)<=2*T[0]
    assert 2*[1,1][1]>[1,1][0]  # The bound fails with the stronger power 2^(m+1).


def test_ordinary_replay_has_one_explicit_decay_induction():
    result=decay.prove_scaled_exp_tail_decay()
    assert result.receipt.target==decay.frozen_scaled_exp_tail_decay_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_decay_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decay.prove_scaled_exp_tail_decay();node=result.provenance["helper_bundle_indices"]["term_decay"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
