"""The common coefficient scale is an actual prescribed factorial."""
from dataclasses import replace
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_factorial_atanh_prefix as prefix


def test_exact_unconditional_prescribed_factorial_prefix_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target=prefix.frozen_factorial_atanh_prefix_target();binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises
    for _ in range(3):
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    assert type(conclusion) is And and len(prefix.canonical(encode_formula(target)))==2977
    c=prefix.source_contract()
    assert c["prescribed_scale"]=="N!"
    assert c["actual_factorial_and_coefficient_table_constructed"] is c["factorial_positive_and_every_required_divisibility_proved"] is True
    assert c["empty_prefix_allowed"] is c["zero_initial_coefficient_proved"] is True
    assert c["code_number_canonicality_claim"] is c["canonical_PR_approximation_algorithm_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_ten_existing_definitions_form_the_minimal_factorial_prefix_dag():
    registry=prefix.definition_registry();source=prefix.source_registry();seen=set();ids=set()
    assert set(registry)=={"Lt","BetaAt","Product","Le","NatAtanhCoefficient","NatAtanhPrefix","BetaZeroExtend","NatZeroBefore","Range","Factorial"}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert prefix.source_contract()["new_definition_ids"]==[]


def test_target_rejects_arbitrary_scale_or_wrong_prefix_length():
    source=prefix.NAMED_SOURCE;registry=prefix.definition_registry()
    for changed in (source.replace("Factorial(N,d)","Factorial(S N,d)"),source.replace("~d=0","d=0"),
                    source.replace("NatAtanhPrefix(d,ab,ac,N)","NatAtanhPrefix(d,ab,ac,S N)"),
                    source.replace("NatZeroBefore(ab,ac,N,1)","NatZeroBefore(ab,ac,N,2)")):
        assert changed!=source
        with patch.object(prefix,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            prefix.frozen_factorial_atanh_prefix_target(_registry=registry)


def test_actual_prefix_constructor_and_factorial_steps_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=prefix.definition_registry();found=set()
    for pin in prefix.ARCHIVES:
        rows=prefix.read_mixed_archive(pin)
        for name,source in prefix.ENDPOINT_SOURCES.items():
            if prefix.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            prefix.read_mixed_archive(bad)
    assert found==prefix.ENDPOINT_SOURCES.keys()


def test_factorial_models_cover_all_required_divisors_and_empty_prefix():
    for N in range(17):
        d=factorial(N);assert d>0
        assert all(d%i==0 for i in range(1,N+1))
        values=[0 if i%2==0 else 2*d//i for i in range(N)]
        for i,a in enumerate(values):
            assert a==0 if i%2==0 else i*a==2*d
        if N:
            assert values[0]==0
        else:
            assert d==1 and values==[]
    # Positivity and the range restriction on factorial divisors are essential.
    assert factorial(0)%2!=0 and factorial(2)%3!=0


def test_complete_factorial_prefix_replay_adds_one_explicit_induction():
    result=prefix.prove_factorial_atanh_prefix()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_divisibility_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=prefix.prove_factorial_atanh_prefix();node=result.provenance["helper_bundle_indices"]["factorial_divisor"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
