"""All actual Cauchy row sums, with explicit diagonal and padding boundaries."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_cauchy_row_sum as rows


def test_exact_constructed_grid_and_all_row_sum_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = rows.frozen_cauchy_row_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert rows.json_hash(encode_formula(target))==rows.TARGET_SHA256
    assert len(rows.canonical(encode_formula(target)))==6512
    c = rows.source_contract()
    assert c["actual_whole_grid_and_all_row_sums_constructed"] is c["all_row_sums_are_actual_convolution_coefficients"] is True
    assert c["diagonal_zero_tail_proved"] is True
    assert c["column_sum_identities"] is c["full_convolution_evaluation"] is c["closes_IR072"] is False


def test_row_definition_is_hygienic_computation_not_a_sum_law():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = rows.definition_registry()
    d = registry["NatCauchyRow"]
    assert d.stable_id=="ND0434" and rows.source_contract()["new_definition_ids"]==["ND0434"]
    assert d.template_formula==parse_named(rows.DEFINITION_SOURCE,rows.ROW_PARAMETERS,registry)
    assert rows.json_hash(encode_formula(d.template_formula))==rows.DEFINITION_SHA256
    assert parse_formula_in_context(pretty_formula(d.template_formula,list(rows.ROW_PARAMETERS)),list(rows.ROW_PARAMETERS))==d.template_formula
    assert "Sum(" not in rows.DEFINITION_SOURCE
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()


def test_changed_sum_length_or_row_offset_is_rejected():
    for source in (rows.NAMED_SOURCE.replace("NatAffineSum(gb,gc,(S N)*k,1,S N,u)","NatAffineSum(gb,gc,(S N)*k,1,N,u)"),
                   rows.NAMED_SOURCE.replace("(S N)*k,1,S N,u","(S N)+k,1,S N,u")):
        with patch.object(rows,"NAMED_SOURCE",source),pytest.raises(ValueError):
            rows.frozen_cauchy_row_sum_target()


def test_exact_helpers_and_actual_owned_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = rows.definition_registry()
    assert {name:rows.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in rows.HELPER_SOURCES.items()}==rows.HELPER_TARGET_SHA256
    found = set()
    for pin in rows.ARCHIVES:
        actual = rows.read_mixed_archive(pin)
        for name,source in rows.ENDPOINT_SOURCES.items():
            if rows.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,r in enumerate(actual) if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and actual[matches[0]][3]
            found.add(name)
    assert found==rows.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in rows.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                rows.read_mixed_archive(changed)


def test_finite_row_models_include_empty_inputs_and_diagonal_zero_tails():
    for L in range(5):
        for M in range(5):
            a,b = [j+1 for j in range(L)],[j*j+2 for j in range(M)]
            for k in range(6):
                coefficient = sum(a[j]*b[k-j] for j in range(L) if 0<=k-j<M)
                for T in range(k+1,k+5):
                    values = [a[j]*b[k-j] if j<=k and j<L and k-j<M else 0 for j in range(T)]
                    assert sum(values)==coefficient
                    assert values[k+1:]==[0]*(T-k-1)
    assert sum([6,10])!=sum([6,10,12])


def test_ordinary_replay_rejects_false_target_and_forged_zero_tail():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = rows.prove_cauchy_row_sum()
    assert result.receipt.target==rows.frozen_cauchy_row_sum_target()
    assert len(result.bundle.nodes)==136
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7126
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(rows.ENDPOINT_SOURCES["zero_tail"],registry=rows.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
