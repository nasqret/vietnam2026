"""Supplied-code multiplication requires actual values and support bounds."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supported_horner_values as values


def test_exact_actual_value_product_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target = values.frozen_supported_horner_values_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==23 and len(premises)==12 and type(conclusion) is Eq
    assert values.json_hash(encode_formula(target))==values.TARGET_SHA256
    assert len(values.canonical(encode_formula(target)))==10247
    c = values.source_contract()
    assert c["actual_supplied_convolution_required"] is c["actual_supplied_horner_values_required"] is True
    assert c["input_support_and_length_alignment_required"] is c["actual_supplied_scaling_power_required"] is True
    assert c["arbitrary_code_encodings_allowed"] is c["no_nonzero_factor_cancelled"] is True
    assert c["identity"]=="p*z=t*(x*y)"
    assert c["code_number_equality_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_evaluation_axiom():
    registry = values.definition_registry()
    assert values.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert "NatScaledHornerTrace" in registry and "NatZeroAfter" in registry


def test_missing_actual_data_or_scaling_is_rejected():
    mutations = (values.NAMED_SOURCE.replace("Pow(t,q,p) -> ",""),
        values.NAMED_SOURCE.replace("NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N) -> ",""),
        values.NAMED_SOURCE.replace("BetaAt(chb,chc,N,z) -> ",""),
        values.NAMED_SOURCE.replace("Le(r+s,N) -> ",""),
        values.NAMED_SOURCE.replace("p*z=t*(x*y)","z=x*y"))
    for source in mutations:
        with patch.object(values,"NAMED_SOURCE",source),pytest.raises(ValueError):
            values.frozen_supported_horner_values_target()


def test_actual_unique_owned_ancestor_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = values.definition_registry()
    found = set()
    for pin in values.ARCHIVES:
        rows = values.read_mixed_archive(pin)
        for name,source in values.ENDPOINT_SOURCES.items():
            if values.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,row in enumerate(rows) if row[1]==ast]
            assert len(matches)==1 and rows[matches[0]][3]
            if name=="power_unique":
                assert matches==[142]
            found.add(name)
    assert found==values.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in values.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                values.read_mixed_archive(changed)


def test_supplied_values_model_including_zero_and_empty_cases():
    def horner(a,t):
        h = 0
        for v in a:
            h = t*h+v
        return h
    for a in ([],[0],[1],[2,1],[1,0,2]):
        for b in ([],[0],[3],[1,2]):
            for pad in range(3):
                A,B = a+[0]*pad,b+[0]*pad
                for N in range(len(a)+len(b),len(A)+len(B)+1):
                    C = [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(N)]
                    q = len(A)+len(B)-N
                    for t in range(4):
                        p,x,y,z = t**q,horner(A,t),horner(B,t),horner(C,t)
                        assert p*z==t*(x*y)
    assert 1*3!=3*(2*1)  # A false supplied endpoint cannot be used.


def test_ordinary_replay_and_forged_uniqueness_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = values.prove_supported_horner_values()
    assert result.receipt.target==values.frozen_supported_horner_values_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(values.ENDPOINT_SOURCES["power_unique"],registry=values.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
