"""Finite natural Fubini: actual construction, hygiene and negative controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_natural_fubini as fubini


def test_exact_target_constructs_both_orders_without_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = fubini.frozen_natural_fubini_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert fubini.json_hash(encode_formula(target))==fubini.TARGET_SHA256
    assert len(fubini.canonical(encode_formula(target)))==7591
    contract = fubini.source_contract()
    assert contract["both_sum_orders_constructed"] is True
    assert contract["all_dimensions_and_strides_allowed"] is True
    assert contract["natural_convolution_associativity"] is False
    assert contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_conservative_definition_dag_contains_no_interchange_identity():
    from sqrt2_power_definitions import parse_named
    registry = fubini.definition_registry()
    for number,name,parameters,source,dependencies,digest in fubini.DEFINITION_ROWS:
        d = registry[name]
        assert d.stable_id==f"ND{number:04d}" and d.arity==len(parameters)
        assert d.conceptual_dependencies==dependencies
        assert "=" not in source
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    # Deliberately collide free source code names with local slice witnesses.
    names = ("ub","uc","o","t","N","z")
    actual = parse_named("NatAffineSum(ub,uc,o,t,N,z)",names,registry)
    explicit = parse_named("exists x y. NatAffineSlice(ub,uc,o,t,x,y,N) /\\ Sum(x,y,N,z)",names,registry)
    assert actual==explicit


def test_wrong_stride_and_wrong_common_total_fail_exact_statement_gates():
    changed = list(fubini.DEFINITION_ROWS)
    row = list(changed[0])
    row[3] = row[3].replace("o+t*i","o+t+i")
    changed[0] = tuple(row)
    with patch.object(fubini,"DEFINITION_ROWS",tuple(changed)),pytest.raises(ValueError):
        fubini.definition_registry()
    with patch.object(fubini,"NAMED_SOURCE",fubini.NAMED_SOURCE.replace("Sum(cb,cc,n,z)","Sum(cb,cc,n,S z)")),pytest.raises(ValueError):
        fubini.frozen_natural_fubini_target()


def test_actual_ancestor_endpoints_match_frozen_formulas():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = fubini.definition_registry()
    found = set()
    for pin,ids in ((fubini.CONVOLUTION_ARCHIVE,fubini.CONVOLUTION_ANCESTORS),(fubini.LINEARITY_ARCHIVE,fubini.LINEARITY_ANCESTORS)):
        rows = fubini.read_archive(pin)
        for name,(old,source) in fubini.ENDPOINT_SOURCES.items():
            if old in ids:
                assert rows[ids.index(old)][1]==encode_formula(parse_named(source,registry=registry))
                found.add(name)
        if pin["case"]=="CV006":
            assert rows[107][1]==encode_formula(parse_named(fubini.LINEARITY_SOURCE,registry=registry))
    assert found==fubini.ENDPOINT_SOURCES.keys()


def test_forged_actual_archives_are_rejected_before_their_use():
    for original in (fubini.CONVOLUTION_ARCHIVE,fubini.LINEARITY_ARCHIVE):
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                fubini.read_archive(changed)


def test_finite_affine_model_includes_empty_rectangles_and_repeated_indices():
    def beta(b,c,i):
        return b % (1+(i+1)*c)
    for b,c,o,s,t,m,n in product(range(4),range(3),range(2),range(3),range(3),range(4),range(4)):
        rows = [sum(beta(b,c,(o+s*i)+t*j) for j in range(n)) for i in range(m)]
        columns = [sum(beta(b,c,(o+t*j)+s*i) for i in range(m)) for j in range(n)]
        assert sum(rows)==sum(columns)
        if not m or not n:
            assert sum(rows)==0
    # The stride in the cell index really matters; a malformed version fails.
    assert sum(beta(17,3,i+2*j) for i in range(2) for j in range(3)) != sum(beta(17,3,2*i+j) for i in range(2) for j in range(3))


def test_guarded_four_inductions_actual_bodies_and_forgery_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = fubini.prove_natural_fubini()
    assert result.receipt.target==fubini.frozen_natural_fubini_target()
    assert len(result.bundle.nodes)==126
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6597
    assert result.provenance["new_induction_count"]==4
    assert result.provenance["all_rectangles_interchange"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["helper_bundle_indices"]["fubini"]==124
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
