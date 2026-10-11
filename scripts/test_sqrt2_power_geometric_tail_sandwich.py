"""The finite tail and geometric prefix imply two explicit natural bounds."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_geometric_tail_sandwich as sandwich


def test_exact_geometric_tail_natural_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target = sandwich.frozen_geometric_tail_sandwich_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==9 and len(premises)==4 and type(conclusion) is And
    assert sandwich.json_hash(encode_formula(target))==sandwich.TARGET_SHA256
    assert len(sandwich.canonical(encode_formula(target)))==1136
    c = sandwich.source_contract()
    assert c["supplied_finite_geometric_split_and_scale_identities_required"] is c["supplied_natural_tail_bound_required"] is True
    assert c["no_division_or_cancellation"] is c["all_natural_zero_cases_allowed"] is True
    assert c["actual_horner_or_power_witnesses_constructed"] is c["rational_denominator_validity_claimed"] is c["closes_IR072"] is False


def test_no_new_definition_or_analytic_claim():
    from sqrt2_power_full_composition_evaluation import definition_registry
    assert sandwich.definition_registry()==definition_registry()
    assert sandwich.source_contract()["new_definition_ids"]==[]
    assert sandwich.source_contract()["definition_admissions"]==0
    assert sandwich.source_contract()["analytic_limit_claim"] is False
    assert "IRat" not in sandwich.NAMED_SOURCE and "NatHorner" not in sandwich.NAMED_SOURCE


def test_missing_scale_or_changed_tail_bound_rejected():
    original = sandwich.NAMED_SOURCE
    for source in (original.replace("h=p*b -> ",""),
                   original.replace("Le(u*q,(9*a)*(z*h)) -> ",""),
                   original.replace("Le(y*q,(2*q+9*a)*(z*h))","Le(y*q,(2*q+8*a)*(z*h))"),
                   original.replace("Le((2*p)*(z*h),y*p+z*h)","Le((3*p)*(z*h),y*p+z*h)")):
        assert source!=original
        with patch.object(sandwich,"NAMED_SOURCE",source),pytest.raises(ValueError):
            sandwich.frozen_geometric_tail_sandwich_target()


def test_actual_arithmetic_bodies_and_corrupt_archive_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    pin = sandwich.COMPOSITION_ARCHIVE;rows = sandwich.read_mixed_archive(pin)
    registry = sandwich.definition_registry()
    for source in sandwich.ENDPOINT_SOURCES.values():
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
    for key in ("sha256","target_ast_sha256"):
        changed = dict(pin);changed[key] = "0"*64
        with pytest.raises(ValueError):
            sandwich.read_mixed_archive(changed)


def test_small_natural_model_with_zero_cases():
    from itertools import product
    checked = 0
    for z,p,b,u,q,a in product(range(4),repeat=6):
        r = 2*z*p-z
        if r<0:
            continue
        h = p*b;y = b*r+u
        if u*q>9*a*z*h:
            continue
        assert y+z*b==2*z*h+u
        assert y*q<=(2*q+9*a)*z*h
        assert 2*p*z*h<=y*p+z*h
        checked += 1
    assert checked>1000


def test_tail_premise_cannot_be_dropped_from_upper_bound():
    r,z,p,b,y,u,h,q,a = 1,1,1,1,100,99,1,1,0
    assert r+z==2*z*p and y==b*r+u and h==p*b
    assert u*q>9*a*z*h and y*q>(2*q+9*a)*z*h


def test_ordinary_replay_and_forged_balance_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = sandwich.prove_geometric_tail_sandwich()
    assert result.receipt.target==sandwich.frozen_geometric_tail_sandwich_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    target = parse_named(sandwich.HELPER_SOURCES["balance"],registry=sandwich.definition_registry())
    matches = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(matches)==1
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==matches[0] else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
