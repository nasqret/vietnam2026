"""Complementary exponents and actual monomial terms, without subtraction."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_monomials as monomials


def test_exact_constructed_monomial_interpretation_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = monomials.frozen_horner_monomials_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and not premises and type(conclusion) is Exists
    assert monomials.json_hash(encode_formula(target))==monomials.TARGET_SHA256
    assert len(monomials.canonical(encode_formula(target)))==12941
    c = monomials.source_contract()
    assert c["all_actual_weight_product_horner_sum_witnesses_constructed"] is c["same_witnesses_preserved"] is True
    assert c["complementary_weight_power_identity_proved"] is c["all_weighted_terms_identified_with_actual_powers"] is True
    assert c["zero_multiplier_allowed"] is True
    assert c["multiplication_evaluation_identity"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_preserves_exact_computation_data_and_conservative_dag():
    from sqrt2_power_definitions import parse_named
    r = monomials.definition_registry()
    source = "forall ab ac t N. exists "+" ".join(monomials.OUTPUTS)+". "+monomials.CONSTRUCTED_DATA
    assert parse_named(source,registry=r)==parse_named(monomials.CONSTRUCTED_SOURCE,registry=r)
    assert monomials.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_wrong_complement_or_monomial_power_is_rejected():
    for source in (monomials.NAMED_SOURCE.replace("j+e=N","j+e=S N"),
                   monomials.NAMED_SOURCE.replace("(S j)+e=N","j+e=N"),
                   monomials.NAMED_SOURCE.replace("c=a*q","c=a+q")):
        with patch.object(monomials,"NAMED_SOURCE",source),pytest.raises(ValueError):
            monomials.frozen_horner_monomials_target()


def test_helpers_and_owned_actual_power_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = monomials.definition_registry()
    assert {name:monomials.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in monomials.HELPER_SOURCES.items()}==monomials.HELPER_TARGET_SHA256
    found = set()
    for pin in monomials.ARCHIVES:
        rows = monomials.read_mixed_archive(pin)
        for name,source in monomials.ENDPOINT_SOURCES.items():
            if monomials.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==monomials.ENDPOINT_SOURCES.keys()


def test_modified_actual_archive_is_rejected():
    for original in monomials.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                monomials.read_mixed_archive(changed)


def test_complementary_power_and_monomial_model_including_zero_multiplier():
    for N in range(9):
        a = [j*j+2 for j in range(N)]
        for t in range(5):
            w = [1]
            for _ in range(N):
                w = [t*x for x in w]+[1]
            terms = [a[j]*w[j+1] for j in range(N)]
            for j in range(N+1):
                e = N-j
                assert j+e==N and w[j]==t**e
            for j in range(N):
                e = N-j-1
                assert j+1+e==N and terms[j]==a[j]*t**e
            h = 0
            for value in a:
                h = t*h+value
            assert h==sum(terms)


def test_guarded_monomial_certificate_replays_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = monomials.prove_horner_monomials()
    assert result.receipt.target==monomials.frozen_horner_monomials_target()
    assert len(result.bundle.nodes)==142
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7593
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
