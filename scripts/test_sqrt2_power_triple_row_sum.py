"""Actual row-sum identity: necessary premises, hygiene and ordinary replay."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_triple_row_sum as row


def test_exact_target_constructs_coefficient_and_row_sum_with_three_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = row.frozen_triple_row_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==15 and len(premises)==3 and type(conclusion) is Exists
    assert row.json_hash(encode_formula(target))==row.TARGET_SHA256
    assert len(row.canonical(encode_formula(target)))==6579
    contract = row.source_contract()
    assert contract["actual_row_computation_required"] is contract["both_sum_values_constructed"] is True
    assert contract["complementary_degree_required"] is contract["padded_outer_coefficient_required"] is True
    assert contract["column_sum_identity"] is contract["natural_convolution_associativity"] is contract["closes_IR072"] is False


def test_conservative_row_definition_and_binder_hygiene():
    from sqrt2_power_definitions import parse_named
    r = row.definition_registry()
    d = r["NatTripleRowPrefix"]
    assert d.stable_id=="ND0418" and d.arity==13
    assert d.conceptual_dependencies==("Lt","BetaAt","NatTripleCell")
    assert "Sum(" not in row.DEFINITION_SOURCE and "Convolution" not in row.DEFINITION_SOURCE
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = row.P+("i","l","ub","uc")
    actual = parse_named("NatTripleRowPrefix("+",".join(names)+")",names,r)
    explicit = parse_named("forall q z. Lt(q,S i) -> BetaAt(ub,uc,q,z) -> "+row.cell("l","q","z"),names,r)
    assert actual==explicit


def test_changed_degree_or_scaled_total_is_rejected():
    for wrong in (row.NAMED_SOURCE.replace("s=a*t","s=a+t"),row.NAMED_SOURCE.replace("j+r=i -> ","")):
        assert wrong!=row.NAMED_SOURCE
        with patch.object(row,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            row.frozen_triple_row_sum_target()


def test_actual_parent_endpoints_cover_all_row_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = row.definition_registry()
    found = set()
    for pin in (row.CONVOLUTION_ARCHIVE,row.ZERO_TAIL_ARCHIVE):
        rows = row.read_archive(pin)
        for name,source in row.ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [r for r in rows if r[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==row.ENDPOINT_SOURCES.keys()


def test_forged_actual_parent_archives_are_rejected():
    for original in (row.CONVOLUTION_ARCHIVE,row.ZERO_TAIL_ARCHIVE):
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                row.read_archive(changed)


def test_finite_row_model_and_missing_index_premise_counterexample():
    seqs = [list(t) for n in range(3) for t in product(range(2),repeat=n)]
    def at(a,j):
        return a[j] if j<len(a) else 0
    def coefficient(c,b,r):
        return sum(at(c,l)*at(b,r-l) for l in range(r+1))
    for a,b,c in product(seqs,repeat=3):
        for i in range(5):
            for j in range(i+1):
                r = i-j
                values = [at(a,j)*at(b,i-j-l)*at(c,l) if j+l<=i else 0 for l in range(i+1)]
                assert sum(values)==at(a,j)*coefficient(c,b,r)
                assert all(values[l]==0 for l in range(r+1,i+1))
                assert r+1+j==i+1
    assert coefficient([1,3],[1,2],1)!=coefficient([1,3],[1,2],0)
    # A made-up row not satisfying the cell graph does not have the specified sum.
    assert sum([1])!=0*coefficient([1],[1],0)


def test_guarded_actual_row_identity_and_rejection_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = row.prove_triple_row_sum()
    assert result.receipt.target==row.frozen_triple_row_sum_target()
    assert len(result.bundle.nodes)==139
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7443
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["actual_triple_row_sum_identity"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
