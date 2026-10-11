"""All actual sample terms retain their exact normalized factorial values."""
from dataclasses import replace
from fractions import Fraction
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_finite_exp_series as series


def test_exact_sample_target_preserves_sum_and_constructs_each_term_data():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=series.frozen_finite_exp_series_target();binders,premises,conclusion=strip_target(target)
    assert binders==16 and len(premises)==2
    for _ in range(3):
        assert type(conclusion) is And
        conclusion=conclusion.right
    assert type(conclusion) is Forall and len(series.canonical(encode_formula(target)))==23447
    c=series.source_contract()
    assert c["actual_supplied_sample_term_table_head_and_sum_preserved"] is c["all_in_range_terms_identified_with_factorial_series"] is True
    assert c["each_factorial_and_both_powers_constructed"] is c["output_and_each_term_denominator_proved_nonzero"] is True
    assert c["zero_argument_and_zero_term_index_allowed"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_exponential_identity_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_twenty_five_definitions_reuse_the_sample_and_rational_dags():
    from sqrt2_power_definitions import DEFINITIONS
    registry=series.definition_registry();base=series.sample_registry();seen=set();ids=set()
    assert registry.keys()==base.keys()|{"IRatValid","IRatEq"} and len(registry)==25
    for name,spec in registry.items():
        assert spec==(base[name] if name in base else DEFINITIONS[name])
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert series.source_contract()["new_definition_ids"]==[]


def test_target_rejects_missing_factorial_wrong_power_or_missing_positive_scale():
    source=series.NAMED_SOURCE;registry=series.definition_registry()
    for changed in (source.replace("q0,0,f0*p0","q0,0,p0"),source.replace("Factorial(j,f0)","Factorial(S j,f0)"),
                    source.replace(f"Pow({series.NUMERATOR},j,q0)",f"Pow({series.DENOMINATOR},j,q0)"),
                    source.replace("~D=0 -> ",""),source.replace("Sum(tb,tc,S (k+2),y)","Sum(tb,tc,(k+2),y)")):
        assert changed!=source
        with patch.object(series,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            series.frozen_finite_exp_series_target(_registry=registry)


def test_factorial_existence_positivity_and_sample_laws_need_actual_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=series.definition_registry();found=set()
    for pin in series.ARCHIVES:
        rows=series.read_mixed_archive(pin)
        for name,source in series.ENDPOINT_SOURCES.items():
            if series.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            series.read_mixed_archive(bad)
    assert found==series.ENDPOINT_SOURCES.keys()


def test_factorial_models_cover_zero_argument_zero_index_and_rescaling():
    for N in range(7):
        for V in range(1,5):
            for U in range(V+1):
                for scale in range(1,4):
                    head=scale*factorial(N)*V**N;terms=[]
                    for j in range(N+1):
                        f,p,q=factorial(j),V**j,U**j
                        t,remainder=divmod(head*q,f*p)
                        assert remainder==0 and head>0 and f*p>0
                        assert (t*f)*p==head*q and Fraction(t,head)==Fraction(q,f*p)
                        terms.append(t)
                    assert terms[0]==head
                    assert Fraction(sum(terms),head)==sum((Fraction(U**j,factorial(j)*V**j) for j in range(N+1)),Fraction(0))
                    if U==0:
                        assert terms==[head]+[0]*N


def test_complete_sample_series_replay_has_no_new_induction_or_axiom():
    result=series.prove_finite_exp_series()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_factorial_normalization_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=series.prove_finite_exp_series();node=result.provenance["helper_bundle_indices"]["normalize"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
