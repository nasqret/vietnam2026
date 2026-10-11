"""Actual finite triple-grid construction, coordinate bounds and hygiene."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_triple_grid as grid


def test_exact_unconditional_actual_grid_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = grid.frozen_triple_grid_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==10 and not premises and type(conclusion) is Exists
    assert grid.json_hash(encode_formula(target))==grid.TARGET_SHA256
    assert len(grid.canonical(encode_formula(target)))==2153
    contract = grid.source_contract()
    assert contract["whole_finite_grid_constructed"] is True
    assert contract["actual_quotient_remainder_coordinates"] is True
    assert contract["row_column_sum_identities"] is False
    assert contract["natural_convolution_associativity"] is contract["closes_IR072"] is False


def test_conservative_definition_dag_and_hygienic_complement_witness():
    from sqrt2_power_definitions import parse_named
    registry = grid.definition_registry()
    for number,name,parameters,source,dependencies,digest in grid.DEFINITION_ROWS:
        d = registry[name]
        assert d.stable_id==f"ND{number:04d}" and d.arity==len(parameters)
        assert d.conceptual_dependencies==dependencies
        assert "Sum(" not in source and "Convolution" not in source
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    names = ("k","a","L","bb","bc","M","cb","cc","K","i","j","l","z")
    aliased = parse_named("NatTripleCell(k,a,L,bb,bc,M,cb,cc,K,i,j,l,z)",names,registry)
    explicit = parse_named("(exists r x y w. j+(r+l)=i /\\ (BetaZeroExtend(k,a,L,j,x) /\\ (BetaZeroExtend(bb,bc,M,r,y) /\\ (BetaZeroExtend(cb,cc,K,l,w) /\\ z=x*(y*w))))) \\/ (Lt(i,j+l) /\\ z=0)",names,registry)
    assert aliased==explicit


def test_changed_layout_or_wrong_zero_case_is_rejected():
    for position,old,new in ((0,"z=0","z=1"),(3,"(S i)*j+l","(S i)*l+j")):
        rows = list(grid.DEFINITION_ROWS)
        row = list(rows[position])
        row[3] = row[3].replace(old,new)
        assert row[3]!=rows[position][3]
        rows[position] = tuple(row)
        with patch.object(grid,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
            grid.definition_registry()


def test_exact_actual_ancestor_targets_are_unique():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    rows = grid.read_archive(grid.CONVOLUTION_ARCHIVE)
    registry = grid.definition_registry()
    for source in grid.ENDPOINT_SOURCES.values():
        formula = encode_formula(parse_named(source,registry=registry))
        assert sum(row[1]==formula for row in rows)==1


def test_changed_actual_ancestor_archive_is_rejected():
    for field in ("sha256","raw_sha256","bundle_sha256","target_ast_sha256"):
        changed = dict(grid.CONVOLUTION_ARCHIVE)
        changed[field] = "0"*64
        with pytest.raises(ValueError):
            grid.read_archive(changed)


def test_finite_grid_model_and_coordinate_bijection():
    seqs = [list(row) for n in range(3) for row in product(range(2),repeat=n)]
    def at(a,j):
        return a[j] if j<len(a) else 0
    def coefficient(a,b,i):
        return sum(at(a,j)*at(b,i-j) for j in range(i+1))
    def cell(a,b,c,i,j,l):
        return at(a,j)*at(b,i-j-l)*at(c,l) if j+l<=i else 0
    for a,b,c in product(seqs,repeat=3):
        for i in range(4):
            H = i+1
            values = [cell(a,b,c,i,*divmod(t,H)) for t in range(H*H)]
            for j,l in product(range(H),repeat=2):
                assert divmod(H*j+l,H)==(j,l)
                assert 0<=H*j+l<H*H
                assert values[H*j+l]==cell(a,b,c,i,j,l)
            # Semantic checks of the intended later bridge, not HA evidence for it.
            for j in range(H):
                assert sum(values[H*j+l] for l in range(H))==at(a,j)*coefficient(b,c,i-j)
            for l in range(H):
                assert sum(values[H*j+l] for j in range(H))==coefficient(a,b,i-l)*at(c,l)
    assert cell([1,1],[1,1],[1,1],1,1,1)==0


def test_guarded_actual_grid_and_forgery_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = grid.prove_triple_grid()
    assert result.receipt.target==grid.frozen_triple_grid_target()
    assert len(result.bundle.nodes)==110
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5165
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["actual_triple_grid_constructed"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
