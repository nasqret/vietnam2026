"""Finite natural convolution is executed, not supplied as a law or residue."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_natural_convolution as convolution


def test_exact_unconditional_target_constructs_a_coefficientwise_unique_prefix():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = convolution.frozen_natural_convolution_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert convolution.json_hash(encode_formula(target))==convolution.TARGET_SHA256
    assert len(convolution.canonical(encode_formula(target)))==6633
    contract = convolution.source_contract()
    assert contract["output_table_supplied"] is contract["modulus_required"] is False
    assert contract["code_number_uniqueness"] is False
    assert contract["coefficientwise_uniqueness"] is True
    assert contract["closes_IR072"] is contract["closes_IR079"] is False


def test_definition_dag_reuses_actual_diagonal_and_sum_without_algebraic_axioms():
    registry = convolution.definition_registry()
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    coefficient,prefix = registry["NatConvolutionCoefficient"],registry["NatConvolutionPrefix"]
    assert coefficient.stable_id=="ND0401" and coefficient.arity==8
    assert prefix.stable_id=="ND0402" and prefix.arity==9
    assert coefficient.conceptual_dependencies==("PolynomialDiagonalPrefix","Sum")
    assert prefix.conceptual_dependencies==("Lt","BetaAt","NatConvolutionCoefficient")
    source = " ".join(row[3] for row in convolution.DEFINITION_ROWS)
    assert "Residue" not in source and "exists db dc" in source
    assert "Sum(db,dc,S i,n)" in source
    assert "n=0" not in source


def test_target_or_computation_mutations_fail_before_proof_generation():
    with patch.object(convolution,"NAMED_SOURCE",convolution.NAMED_SOURCE.replace("BetaAt(eb,ec,j,a)","BetaAt(eb,ec,j,S a)")),pytest.raises(ValueError):
        convolution.frozen_natural_convolution_target()
    rows = list(convolution.DEFINITION_ROWS)
    row = list(rows[0])
    row[3] = row[3].replace("Sum(db,dc,S i,n)","Sum(db,dc,i,n)")
    rows[0] = tuple(row)
    with patch.object(convolution,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        convolution.definition_registry()


def test_actual_ancestor_cone_binds_all_value_and_coding_operations():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    ids,rows = convolution.inert_convolution_rows()
    assert len(ids)==120 and len(convolution.canonical(rows))==214712
    assert convolution.json_hash(rows)==convolution.ANCESTOR_ROWS_SHA256
    registry,table = convolution.definition_registry(),dict(zip(ids,rows))
    for name,source in convolution.ENDPOINT_SOURCES.items():
        assert table[convolution.ENDPOINT_IDS[name]][1]==encode_formula(parse_named(source,registry=registry))


def test_altered_ancestor_archive_or_endpoint_is_rejected():
    with patch.object(convolution,"ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        convolution.inert_convolution_rows()
    sources = dict(convolution.ENDPOINT_SOURCES)
    sources["sum_exists"] = "forall b c N. exists n. Sum(b,c,S N,n)"
    with patch.object(convolution,"ENDPOINT_SOURCES",sources),pytest.raises(ValueError):
        convolution.inert_convolution_rows()


def test_finite_convolution_model_empty_padding_and_ascending_coefficients():
    def coefficient(left,right,index):
        return sum((left[j] if j<len(left) else 0)*(right[index-j] if index-j<len(right) else 0)
                   for j in range(index+1))
    sequences = [list(values) for length in range(4) for values in product(range(3),repeat=length)]
    for left in sequences:
        for right in sequences:
            for index in range(7):
                expected = sum(a*b for j,a in enumerate(left) for k,b in enumerate(right) if j+k==index)
                assert coefficient(left,right,index)==expected
                if not left or not right or index>=len(left)+len(right)-1:
                    assert expected==0
    assert [coefficient([2,3,4],[5,6],i) for i in range(5)]==[10,27,38,24,0]


def test_guarded_constructive_existence_uniqueness_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = convolution.prove_natural_convolution()
    assert result.receipt.target==convolution.frozen_natural_convolution_target()
    assert len(result.bundle.nodes)==126
    assert result.provenance["finite_convolution_constructed"] is True
    assert result.provenance["root_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
