"""Complete column sums retain their required finite-span equality."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_cauchy_column_sum as columns


def test_exact_complete_column_target_and_three_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = columns.frozen_cauchy_column_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==12 and len(premises)==3 and type(conclusion) is Exists
    assert columns.json_hash(encode_formula(target))==columns.TARGET_SHA256
    assert len(columns.canonical(encode_formula(target)))==4738
    c = columns.source_contract()
    assert c["actual_left_padded_value_and_column_required"] is c["complete_span_equality_required"] is True
    assert c["both_actual_sum_values_constructed"] is c["leading_and_trailing_zeros_proved"] is True
    assert c["all_grid_columns_unconditionally_constructed"] is c["full_convolution_evaluation"] is c["closes_IR072"] is False


def test_column_definition_is_hygienic_and_has_no_sum_conclusion():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = columns.definition_registry()
    d = registry["NatCauchyColumn"]
    assert d.stable_id=="ND0435" and columns.source_contract()["new_definition_ids"]==["ND0435"]
    assert d.template_formula==parse_named(columns.DEFINITION_SOURCE,columns.COLUMN_PARAMETERS,registry)
    assert columns.json_hash(encode_formula(d.template_formula))==columns.DEFINITION_SHA256
    assert parse_formula_in_context(pretty_formula(d.template_formula,list(columns.COLUMN_PARAMETERS)),list(columns.COLUMN_PARAMETERS))==d.template_formula
    assert "Sum(" not in columns.DEFINITION_SOURCE
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()


def test_changed_span_or_dropped_scalar_is_rejected():
    for source in (columns.NAMED_SOURCE.replace("(j+M)+q=T","j+q=T"),
                   columns.NAMED_SOURCE.replace("y=a*x","y=x")):
        with patch.object(columns,"NAMED_SOURCE",source),pytest.raises(ValueError):
            columns.frozen_cauchy_column_sum_target()


def test_exact_helpers_and_actual_owned_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = columns.definition_registry()
    assert {name:columns.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in columns.HELPER_SOURCES.items()}==columns.HELPER_TARGET_SHA256
    found = set()
    for pin in columns.ARCHIVES:
        actual = columns.read_mixed_archive(pin)
        for name,source in columns.ENDPOINT_SOURCES.items():
            if columns.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,r in enumerate(actual) if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and actual[matches[0]][3]
            found.add(name)
    assert found==columns.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in columns.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                columns.read_mixed_archive(changed)


def test_finite_complete_column_model_and_truncation_counterexample():
    for L in range(4):
        for M in range(4):
            left,right = [2*i+1 for i in range(L)],[i*i+1 for i in range(M)]
            for j in range(5):
                a = left[j] if j<L else 0
                for q in range(4):
                    T = j+M+q
                    cells = [a*right[k-j] if j<=k<j+M else 0 for k in range(T)]
                    assert sum(cells)==a*sum(right)
    assert sum([0,6])!=2*sum([3,5])


def test_ordinary_replay_and_corrupted_shifted_sum_body_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = columns.prove_cauchy_column_sum()
    assert result.receipt.target==columns.frozen_cauchy_column_sum_target()
    assert len(result.bundle.nodes)==133
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7204
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(columns.ENDPOINT_SOURCES["shifted_sum"],registry=columns.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
