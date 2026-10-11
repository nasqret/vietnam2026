"""Same-witness finite composition normalization, not an analytic assertion."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_normalized_composition as composition


def test_exact_same_witness_target_and_honest_scope():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = composition.frozen_normalized_composition_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and len(premises)==1 and type(conclusion) is Exists
    assert composition.json_hash(encode_formula(target))==composition.TARGET_SHA256
    assert len(composition.canonical(encode_formula(target)))==25731
    c = composition.source_contract()
    for name in ("whole_actual_computation_constructed","same_composition_weight_witnesses",
                 "nonzero_common_denominator_constructed","factorial_and_power_values_constructed",
                 "all_in_range_coefficients_identified","all_weight_factorial_identities_proved"):
        assert c[name] is True
    assert c["rational_evaluation_identity"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_preserves_exact_coefficient_data_and_conservative_definition_dag():
    from sqrt2_power_definitions import parse_named
    r = composition.definition_registry()
    source = "forall N. Lt(1,N) -> exists "+" ".join(composition.COMPOSITION_OUTPUTS)+". "+composition.COEFFICIENT_DATA
    assert parse_named(source,registry=r)==parse_named(composition.COEFFICIENT_SOURCE,registry=r)
    assert composition.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_changed_witness_or_removed_width_is_rejected():
    for source in (composition.NAMED_SOURCE.replace("z=fn*pn","z=fn+pn"),
                   composition.NAMED_SOURCE.replace("Lt(1,N) -> ","",1),
                   composition.NAMED_SOURCE.replace("(w*f)*p=z","(w*f)*p=d")):
        with patch.object(composition,"NAMED_SOURCE",source),pytest.raises(ValueError):
            composition.frozen_normalized_composition_target()


def test_actual_owned_endpoints_and_conditional_invariant_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = composition.definition_registry()
    found = set()
    for pin in composition.ARCHIVES:
        rows = composition.read_mixed_archive(pin)
        for name,source in composition.ENDPOINT_SOURCES.items():
            if composition.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==composition.ENDPOINT_SOURCES.keys()
    assert "weights_exists" not in composition.ENDPOINT_SOURCES


def test_changed_actual_archive_is_rejected():
    for original in composition.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                composition.read_mixed_archive(changed)


def test_exact_finite_normalized_composition_model():
    from fractions import Fraction
    from math import factorial,lcm
    for N in range(2,8):
        d = lcm(*range(1,N+1))
        a = [0 if i%2==0 else 2*(d//i) for i in range(N)]
        z = factorial(N)*d**N
        w = [z//(factorial(j)*d**j) for j in range(N+1)]
        power,c = [1]+[0]*(N-1),[0]*N
        rational = [Fraction(0)]*N
        for j in range(N+1):
            for i in range(N):
                c[i] += w[j]*power[i]
                rational[i] += Fraction(power[i],factorial(j)*d**j)
            power = [sum(a[k]*power[i-k] for k in range(i+1)) for i in range(N)]
        assert c==[z]+[2*z]*(N-1)
        assert rational==[Fraction(v,z) for v in c]
    # A finite coefficient identity is not equality to the untruncated exp.


def test_guarded_same_witness_proof_and_false_target_rejection():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = composition.prove_normalized_composition()
    assert result.receipt.target==composition.frozen_normalized_composition_target()
    assert len(result.bundle.nodes)==272
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==21575
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["endpoint_archive_selection"]["invariant"]["case"]=="CV030"
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
