"""The factorial lower bound retains exact offsets and actual values."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_factorial_majorant as majorant


def test_exact_constructed_factorial_lower_bound_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_factorial_majorant_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==3683
    c = majorant.source_contract()
    assert c["actual_factorial_and_power_constructed"] is c["arbitrary_supplied_values_helper"] is True
    assert c["factorial_index"]=="k+2" and c["power"]=="3^k" and c["inequality"]=="2*p<=f"
    assert c["finite_exp_sum_bound_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_factorial_definition_and_conservative_dag_preserved():
    registry = majorant.definition_registry()
    assert majorant.source_contract()["new_definition_ids"]==[]
    for base in (majorant.previous_registry(),majorant.factorial_registry()):
        for name,d in base.items():
            assert registry[name].stable_id==d.stable_id
            assert registry[name].template_formula==d.template_formula
    assert registry["Factorial"].stable_id=="PD0023"
    assert registry["Pow"].stable_id=="PD0020"
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_changed_factorial_offset_base_or_constant_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace("Factorial(S(S k),f)","Factorial(S k,f)"),
                   majorant.NAMED_SOURCE.replace("Pow(3,k,p)","Pow(4,k,p)"),
                   majorant.NAMED_SOURCE.replace("Le(2*p,f)","Le(3*p,f)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_factorial_majorant_target()


def test_owned_actual_factorial_power_and_order_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry()
    found = set()
    for pin in majorant.ARCHIVES:
        rows = majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==majorant.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in majorant.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                majorant.read_mixed_archive(pin)


def test_exact_factorial_model_and_geometric_tail_comparison():
    from math import factorial
    from fractions import Fraction
    for k in range(41):
        f,p = factorial(k+2),3**k
        assert 2*p<=f
        assert Fraction(2**(k+2),f)<=2*Fraction(2,3)**k
    assert 2*3**0==factorial(2)
    assert 2*3**1==factorial(3)
    assert not 2*3**0<=factorial(1)
    assert not 3*3**0<=factorial(2)
    assert not 2*4**1<=factorial(3)


def test_ordinary_replay_and_forged_factorial_step_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_factorial_majorant()
    assert result.receipt.target==majorant.frozen_factorial_majorant_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["factorial_step"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
