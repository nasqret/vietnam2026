"""The encoded finite log value is an actual sum of exact odd reciprocals."""
from dataclasses import replace
from fractions import Fraction
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_finite_odd_log_series as series


def test_exact_finite_series_contract_preserves_all_supplied_computations():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,And,Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=series.frozen_finite_odd_log_series_target();binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==4
    for _ in series.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    for _ in range(10):
        assert type(conclusion) is And
        conclusion=conclusion.right
    assert type(conclusion) is Forall and len(series.canonical(encode_formula(target)))==13631
    c=series.source_contract()
    assert c["actual_finite_term_table_and_sum_constructed"] is c["all_actual_terms_identified_with_odd_reciprocals"] is True
    assert c["each_odd_denominator_power_constructed"] is c["all_rational_denominators_proved_nonzero"] is c["empty_sum_allowed"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_logarithm_identity_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_seventeen_existing_definitions_form_a_conservative_dag():
    registry=series.definition_registry();base=series.quotient_registry();extra=series.sum_registry();seen=set();ids=set()
    assert registry.keys()==base.keys()|{"Sum","NatGeometricWeightTable","NatHornerWeightedPrefix"}
    assert len(registry)==17
    for name,spec in registry.items():
        assert spec==(base[name] if name in base else extra[name])
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert series.source_contract()["new_definition_ids"]==[]


def test_target_rejects_wrong_term_odd_index_or_unrelated_sum():
    source=series.NAMED_SOURCE;registry=series.definition_registry()
    for changed in (source.replace("Sum(tb,tc,k,y)","Sum(tb,tc,k,x)"),source.replace("3*c,0,d*q","c,0,d*q"),
                    source.replace("(S(2*j))*r","(2*j)*r"),source.replace("Pow(3,S(2*j),r)","Pow(3,2*j,r)"),
                    source.replace("~d=0 -> ","")):
        assert changed!=source
        with patch.object(series,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            series.frozen_finite_odd_log_series_target(_registry=registry)


def test_sum_and_normalization_require_actual_uniquely_owned_ancestor_bodies():
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


def test_exact_models_identify_every_term_and_empty_sum():
    for k in range(9):
        common=lcm(*range(1,2*k,2)) if k else 1
        for scale in range(1,4):
            d=common*scale;q=9**k;terms=[(2*d//(2*j+1))*9**(k-1-j) for j in range(k)]
            normalized=[]
            for j,c in enumerate(terms):
                r=3**(2*j+1)
                assert d*q>0 and (2*j+1)*r>0
                assert Fraction(3*c,d*q)==Fraction(2,(2*j+1)*r)
                normalized.append(Fraction(2,(2*j+1)*r))
            assert Fraction(3*sum(terms),d*q)==sum(normalized,Fraction(0))
            if k==0:
                assert terms==[] and sum(terms)==0 and q==1


def test_complete_finite_series_replay_adds_no_induction_or_axiom():
    result=series.prove_finite_odd_log_series()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_term_identity_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=series.prove_finite_odd_log_series();node=result.provenance["helper_bundle_indices"]["terms"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
