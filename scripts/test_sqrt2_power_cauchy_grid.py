"""Conservative Cauchy-grid definitions, actual construction and negative controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_cauchy_grid as grid


def test_exact_unconditional_grid_target_and_scope():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = grid.frozen_cauchy_grid_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert grid.json_hash(encode_formula(target))==grid.TARGET_SHA256
    assert len(grid.canonical(encode_formula(target)))==1653
    c = grid.source_contract()
    assert c["actual_whole_cauchy_grid_constructed"] is c["triangular_zero_region_explicit"] is True
    assert c["grid_width"]=="S N" and c["arbitrary_input_lengths_and_grid_parameter"] is True
    assert c["row_column_sum_identities"] is c["full_convolution_evaluation"] is c["closes_IR072"] is False


def test_exact_new_definitions_form_a_conservative_acyclic_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = grid.definition_registry()
    earlier = set(grid.convolution_registry())
    for number,name,parameters,source,deps,digest in grid.DEFINITION_ROWS:
        d = registry[name]
        assert d.stable_id==f"ND{number:04d}" and set(deps)<=earlier
        assert d.template_formula==parse_named(source,parameters,registry)
        assert grid.json_hash(encode_formula(d.template_formula))==digest
        assert parse_formula_in_context(pretty_formula(d.template_formula,list(parameters)),list(parameters))==d.template_formula
        assert "Sum(" not in source and "Horner" not in source
        earlier.add(name)
    assert grid.source_contract()["new_definition_ids"]==["ND0430","ND0431","ND0432","ND0433"]


def test_changed_triangular_region_or_grid_width_is_rejected():
    changed = list(grid.DEFINITION_ROWS)
    row = list(changed[0]);row[3] = row[3].replace("Lt(k,j)","Lt(j,k)");changed[0] = tuple(row)
    with patch.object(grid,"DEFINITION_ROWS",tuple(changed)),pytest.raises(ValueError):
        grid.definition_registry()
    with patch.object(grid,"NAMED_SOURCE",grid.NAMED_SOURCE.replace(",N,gb,gc)",",S N,gb,gc)")),pytest.raises(ValueError):
        grid.frozen_cauchy_grid_target()


def test_exact_helpers_and_actual_owned_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = grid.definition_registry()
    assert {name:grid.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in grid.HELPER_SOURCES.items()}==grid.HELPER_TARGET_SHA256
    found = set()
    for pin in grid.ARCHIVES:
        rows = grid.read_mixed_archive(pin)
        for name,source in grid.ENDPOINT_SOURCES.items():
            if grid.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,row in enumerate(rows) if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and rows[matches[0]][3]
            found.add(name)
    assert found==grid.ENDPOINT_SOURCES.keys()


def test_changed_actual_archive_is_rejected():
    for original in grid.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                grid.read_mixed_archive(changed)


def test_finite_grid_model_has_correct_quotient_remainder_and_zero_region():
    for N in range(5):
        H = N+1
        for L in range(5):
            for M in range(5):
                a,b = [j+2 for j in range(L)],[2*j+1 for j in range(M)]
                cells = []
                for v in range(H*H):
                    k,j = divmod(v,H)
                    z = a[j]*b[k-j] if j<=k and j<L and k-j<M else 0
                    cells.append(z)
                for k in range(H):
                    for j in range(H):
                        assert divmod(H*k+j,H)==(k,j)
                        if k<j:
                            assert cells[H*k+j]==0
                    expected = sum(a[j]*b[k-j] for j in range(L) if 0<=k-j<M)
                    assert sum(cells[H*k:H*(k+1)])==expected


def test_ordinary_replay_and_forged_import_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = grid.prove_cauchy_grid()
    assert result.receipt.target==grid.frozen_cauchy_grid_target()
    assert len(result.bundle.nodes)==110
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5103
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(grid.ENDPOINT_SOURCES["grid_index_bound"],registry=grid.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
