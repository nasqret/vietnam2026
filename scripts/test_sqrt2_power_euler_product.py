"""Actual coefficient product rule, construction, padding and binder hygiene."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_euler_product as euler


def test_exact_unconditional_euler_product_constructs_all_five_data_outputs():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = euler.frozen_euler_product_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert euler.json_hash(encode_formula(target))==euler.TARGET_SHA256
    assert len(euler.canonical(encode_formula(target)))==9401
    contract = euler.source_contract()
    assert contract["both_euler_prefixes_constructed"] is contract["all_three_coefficients_constructed"] is True
    assert contract["ordinary_shifted_derivative"] is False
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_definition_dag_computes_index_multiplication_without_product_rule():
    from sqrt2_power_definitions import parse_named
    registry = euler.definition_registry()
    definition = registry["NatEulerPrefix"]
    assert definition.stable_id=="ND0410" and definition.arity==5
    assert definition.conceptual_dependencies==("Lt","BetaAt")
    assert "Convolution" not in euler.DEFINITION_SOURCE and "Sum(" not in euler.DEFINITION_SOURCE
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    # Free derivative codes deliberately use the same names as the internal
    # coefficient-relation witnesses; exact expansion must avoid capture.
    names = ("db","dc","L","bb","bc","M","i","q")
    aliased = parse_named("NatConvolutionCoefficient(db,dc,L,bb,bc,M,i,q)",names,registry)
    explicit = parse_named("exists x y. PolynomialDiagonalPrefix(db,dc,L,bb,bc,M,i,x,y,S i) /\\ Sum(x,y,S i,q)",names,registry)
    assert aliased==explicit


def test_multiplication_or_product_rule_mutations_fail_before_proof_generation():
    with patch.object(euler,"DEFINITION_SOURCE",euler.DEFINITION_SOURCE.replace("i*a","S i*a")),pytest.raises(ValueError):
        euler.definition_registry()
    with patch.object(euler,"NAMED_SOURCE",euler.NAMED_SOURCE.replace("i*p=q+r","i*p=q*r")),pytest.raises(ValueError):
        euler.frozen_euler_product_target()


def test_actual_convolution_and_linearity_helper_endpoints_are_bound():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = euler.definition_registry()
    rows = euler.read_archive(euler.CONVOLUTION_ARCHIVE)
    for name,(old,source) in euler.ENDPOINT_SOURCES.items():
        assert rows[euler.CONVOLUTION_ANCESTORS.index(old)][1]==encode_formula(parse_named(source,registry=registry))
    rows = euler.read_archive(euler.LINEARITY_ARCHIVE)
    assert rows[107][1]==encode_formula(parse_named(euler.LINEARITY_SOURCE,registry=registry))


def test_forged_actual_archive_hashes_are_rejected():
    for original in (euler.CONVOLUTION_ARCHIVE,euler.LINEARITY_ARCHIVE):
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                euler.read_archive(changed)


def test_finite_euler_product_model_empty_inputs_and_arbitrary_output_index():
    def coefficient(left,right,index):
        return sum(a*b for j,a in enumerate(left) for k,b in enumerate(right) if j+k==index)
    values = [list(row) for length in range(4) for row in product(range(3),repeat=length)]
    for left in values:
        da = [j*a for j,a in enumerate(left)]
        for right in values:
            db = [k*b for k,b in enumerate(right)]
            for i in range(8):
                assert i*coefficient(left,right,i)==coefficient(da,right,i)+coefficient(left,db,i)
    assert coefficient([2,3],[5,7],1)==29
    assert coefficient([0,3],[5,7],1)+coefficient([2,3],[0,7],1)==29


def test_guarded_constructed_product_rule_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = euler.prove_euler_product()
    assert result.receipt.target==euler.frozen_euler_product_target()
    assert len(result.bundle.nodes)==123
    assert sum(n.fuel//8-2 for n in result.bundle.nodes)==6413
    assert result.provenance["coefficientwise_euler_product_rule"] is True
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
