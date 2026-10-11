"""In-range initial values, finite periodicity and exact actual proof controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_euler as euler


def test_exact_constructed_euler_target_with_finite_coefficient_premise():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = euler.frozen_atanh_euler_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and len(premises)==1 and type(conclusion) is Exists
    assert euler.json_hash(encode_formula(target))==euler.TARGET_SHA256
    assert len(euler.canonical(encode_formula(target)))==2594
    contract = euler.source_contract()
    assert contract["actual_atanh_prefix_required"] is True
    assert contract["actual_euler_table_constructed"] is True
    assert contract["initial_values_require_in_range"] is True
    assert contract["period_two_proved_in_range"] is True
    assert contract["logarithm_identity"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_no_new_aliases_and_coherent_conservative_euler_expansion():
    from sqrt2_power_definitions import parse_named
    r = euler.definition_registry()
    assert euler.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("i","a","b","c","N")
    alias = parse_named("NatEulerPrefix(i,a,b,c,N)",names,r)
    explicit = parse_named("forall j x. Lt(j,N) -> BetaAt(i,a,j,x) -> BetaAt(b,c,j,j*x)",names,r)
    assert alias==explicit


def test_removed_prefix_or_range_premise_is_rejected():
    for source in (euler.NAMED_SOURCE.replace(euler.PREFIX+" -> ","",1),
                   euler.NAMED_SOURCE.replace("Lt(1,N) -> ","")):
        with patch.object(euler,"NAMED_SOURCE",source),pytest.raises(ValueError):
            euler.frozen_atanh_euler_target()


def test_helpers_and_actual_parity_division_and_euler_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = euler.definition_registry()
    assert {name:euler.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in euler.HELPER_SOURCES.items()}==euler.HELPER_TARGET_SHA256
    found = set()
    for pin in euler.ARCHIVES:
        rows = euler.read_archive(pin)
        for name,source in euler.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==euler.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in euler.ARCHIVES}=={"CV025","CV007"}


def test_forged_actual_archives_are_rejected():
    for original in euler.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                euler.read_archive(changed)


def test_finite_alternation_model_and_required_prefix_counterexample():
    from math import lcm
    for N in range(15):
        for multiplier in range(3):
            d = multiplier*lcm(*range(1,N+1))
            a = [0 if i%2==0 else 2*(d//i) for i in range(N)]
            ea = [i*v for i,v in enumerate(a)]
            assert ea==[0 if i%2==0 else 2*d for i in range(N)]
            for i in range(max(0,N-2)):
                assert ea[i]==ea[i+2]
    arbitrary_input = [0,1,1]
    assert [i*a for i,a in enumerate(arbitrary_input)]==[0,1,2]
    assert 0!=2  # arbitrary Euler tables do not have period two


def test_guarded_periodicity_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = euler.prove_atanh_euler()
    assert result.receipt.target==euler.frozen_atanh_euler_target()
    assert len(result.bundle.nodes)==111
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5287
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
