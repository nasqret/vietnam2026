"""Exact geometric error, actual powers and coefficient-premise boundaries."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_geometric_horner as geometric


def test_exact_geometric_horner_target_and_scope():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = geometric.frozen_geometric_horner_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and len(premises)==1 and type(premises[0]) is Forall and type(conclusion) is Exists
    assert geometric.json_hash(encode_formula(target))==geometric.TARGET_SHA256
    assert len(geometric.canonical(encode_formula(target)))==3913
    c = geometric.source_contract()
    assert c["coefficient_pattern_required"] is c["actual_horner_trace_constructed"] is True
    assert c["actual_nonzero_power_constructed"] is c["exact_integer_remainder_identity"] is True
    assert c["composition_witnesses_constructed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_definitions_keep_an_exact_conservative_dag():
    from sqrt2_power_definitions import parse_named
    r = geometric.definition_registry()
    assert geometric.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("a","b","k","p")
    assert parse_named("Pow(a,b,p)",names,r)==parse_named(
        "exists u v. Repeat(u,v,a,b) /\\ Product(u,v,b,p)",names,r)


def test_wrong_base_remainder_or_missing_pattern_is_rejected():
    for source in (geometric.NAMED_SOURCE.replace("Pow(3,k,p)","Pow(2,k,p)"),
                   geometric.NAMED_SOURCE.replace("r+z=(2*z)*p","r=(2*z)*p"),
                   geometric.NAMED_SOURCE.replace("("+geometric.pattern("S k")+") -> ","",1)):
        with patch.object(geometric,"NAMED_SOURCE",source),pytest.raises(ValueError):
            geometric.frozen_geometric_horner_target()


def test_exact_helpers_and_owned_proof_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = geometric.definition_registry()
    assert {name:geometric.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in geometric.HELPER_SOURCES.items()}==geometric.HELPER_TARGET_SHA256
    found = set()
    for pin in geometric.ARCHIVES:
        rows = geometric.read_mixed_archive(pin)
        for name,source in geometric.ENDPOINT_SOURCES.items():
            if geometric.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==geometric.ENDPOINT_SOURCES.keys()


def test_modified_actual_archive_is_rejected():
    for original in geometric.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                geometric.read_mixed_archive(changed)


def test_exact_integer_and_rational_model_with_necessary_pattern():
    from fractions import Fraction
    for z in range(6):
        for k in range(12):
            h = 0
            for a in [z]+[2*z]*k:
                h = 3*h+a
            p = 3**k
            assert p>0 and h+z==2*z*p
            if z:
                assert Fraction(h,z*p)==2-Fraction(1,p)
    h = 3*1+3
    assert h+1!=2*1*3  # One incorrect positive coefficient breaks the identity.


def test_guarded_geometric_evaluation_certificate_rejects_false_proof():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = geometric.prove_geometric_horner()
    assert result.receipt.target==geometric.frozen_geometric_horner_target()
    assert len(result.bundle.nodes)==126
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6175
    assert result.provenance["new_induction_count"]==2
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
