"""One actual grid, one shared right sum, and exactly L+M entries per sum."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_cauchy_grid_sums as sums


def test_exact_unconditional_shared_grid_sum_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = sums.frozen_cauchy_grid_sums_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==6 and not premises and type(conclusion) is Exists
    assert sums.json_hash(encode_formula(target))==sums.TARGET_SHA256
    assert len(sums.canonical(encode_formula(target)))==10450
    c = sums.source_contract()
    assert c["actual_common_grid_and_sum_witnesses_constructed"] is c["all_length_L_plus_M_row_and_column_sums_identified"] is True
    assert c["shared_actual_right_input_sum"] is c["outside_left_support_columns_proved_zero"] is c["empty_inputs_allowed"] is True
    assert c["grid_width"]=="S N" and c["summation_width"]=="N" and c["constructed_length"]=="L+M"
    assert c["full_convolution_sum_product"] is c["full_convolution_evaluation"] is c["closes_IR072"] is False


def test_shared_conservative_definition_dag_and_same_grid_codes():
    registry = sums.definition_registry()
    assert sums.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert "NatAffineSum(gb,gc,(S N)*k,1,N,u)" in sums.ALL_ROWS
    assert "NatAffineSum(gb,gc,j,S N,N,y)" in sums.ALL_COLUMNS
    assert "y=a*x" in sums.ALL_COLUMNS and "Sum(bb,bc,M,x)" in sums.DATA


def test_changed_summation_length_or_input_total_is_rejected():
    for source in (sums.NAMED_SOURCE.replace("(S N)*k,1,N,u)","(S N)*k,1,S N,u)"),
                   sums.NAMED_SOURCE.replace("N=L+M","N=L*M")):
        with patch.object(sums,"NAMED_SOURCE",source),pytest.raises(ValueError):
            sums.frozen_cauchy_grid_sums_target()


def test_exact_helpers_and_owned_actual_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = sums.definition_registry()
    assert {name:sums.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in sums.HELPER_SOURCES.items()}==sums.HELPER_TARGET_SHA256
    found = set()
    for pin in sums.ARCHIVES:
        actual = sums.read_mixed_archive(pin)
        for name,source in sums.ENDPOINT_SOURCES.items():
            if sums.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,r in enumerate(actual) if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and actual[matches[0]][3]
            found.add(name)
    assert found==sums.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in sums.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                sums.read_mixed_archive(changed)


def test_finite_same_grid_rows_columns_empty_inputs_and_outside_support():
    for L in range(6):
        for M in range(6):
            a,b = [2*i+1 for i in range(L)],[i*i+2 for i in range(M)]
            N = L+M
            H = N+1
            grid = [0]*(H*H)
            for k in range(H):
                for j in range(H):
                    grid[H*k+j] = a[j]*b[k-j] if j<=k and j<L and k-j<M else 0
            for k in range(N):
                coefficient = sum(a[j]*b[k-j] for j in range(L) if 0<=k-j<M)
                assert sum(grid[H*k+j] for j in range(N))==coefficient
            for j in range(N):
                value = a[j] if j<L else 0
                assert sum(grid[H*k+j] for k in range(N))==value*sum(b)
                if j>=L:
                    assert all(grid[H*k+j]==0 for k in range(N))


def test_ordinary_replay_and_imported_column_body_corruption_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = sums.prove_cauchy_grid_sums()
    assert result.receipt.target==sums.frozen_cauchy_grid_sums_target()
    assert len(result.bundle.nodes)==149
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==8381
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(sums.ENDPOINT_SOURCES["column_total"],registry=sums.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
