"""Canonical height, representation counterexamples and guarded HA checks."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_height as height


def mass(values):
    a, b, c, d = values
    return a+b+2*(c+d)


def canonical_product(A, B):
    ap, an, bp, bn = A
    cp, cn, dp, dn = B
    return ((ap*cp+an*cn)+2*(bp*dp+bn*dn),
            (ap*cn+an*cp)+2*(bp*dn+bn*dp),
            (ap*dp+an*dn)+(bp*cp+bn*cn),
            (ap*dn+an*dp)+(bp*cn+bn*cp))


def test_exact_height_statement_and_explicit_canonical_scope():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = height.frozen_quadratic_height_target()
    binders, premises, conclusion = strip_target(target)
    assert binders == 15 and len(premises) == 4 and type(conclusion) is Exists
    assert height.json_hash(encode_formula(target)) == height.TARGET_SHA256
    assert len(height.canonical(encode_formula(target))) == 1349
    contract = height.source_contract()
    assert contract["canonical_outputs_required"] is True
    for key in ("arbitrary_representatives_bounded", "finite_trace_height_bound", "real_interpretation",
                "closes_IR046", "closes_IR072", "original_HA_checked"):
        assert contract[key] is False
    assert contract["definition_admissions"] == contract["library_admissions"] == 0


def test_conservative_definition_templates_and_capture_safe_expansion():
    from sqrt2_power_definitions import parse_named
    registry = height.definition_registry()
    assert registry["IQuadCanonicalProduct"].stable_id == "ND0394"
    assert registry["IQuadCanonicalProduct"].arity == 12
    assert registry["IQuadHeight"].stable_id == "ND0395"
    assert registry["IQuadHeight"].arity == 5
    for name in ("IQuadCanonicalProduct", "IQuadHeight"):
        assert registry[name].conceptual_dependencies == ()
    names = ("a", "b", "c", "d", "h")
    assert parse_named("IQuadHeight(a+b,b,c,d,h)", names, registry) == parse_named(
        "h=((a+b)+b)+2*(c+d)", names, registry)
    assert "exists" not in height.DEFINITION_ROWS[0][3]
    assert "exists" not in height.DEFINITION_ROWS[1][3]


def test_definitions_and_target_mutations_fail_closed():
    for index, old, new in ((0, "2*", "3*"), (1, "2*", "1*")):
        rows = list(height.DEFINITION_ROWS)
        row = list(rows[index])
        row[3] = row[3].replace(old, new, 1)
        rows[index] = tuple(row)
        with patch.object(height, "DEFINITION_ROWS", tuple(rows)), pytest.raises(ValueError):
            height.definition_registry()
    rows = list(height.DEFINITION_ROWS)
    row = list(rows[0])
    row[0] = 390
    rows[0] = tuple(row)
    with patch.object(height, "DEFINITION_ROWS", tuple(rows)), pytest.raises(ValueError):
        height.definition_registry()
    old = height.named("IQuadCanonicalProduct", *height.A, *height.B, *height.C)+" -> "
    with patch.object(height, "NAMED_SOURCE", height.NAMED_SOURCE.replace(old, "")), pytest.raises(ValueError):
        height.frozen_quadratic_height_target()


def test_gap_identity_including_zero_and_noncanonical_inputs():
    for values in product(range(3), repeat=8):
        A, B = values[:4], values[4:]
        C = canonical_product(A, B)
        gap = 2*(A[2]+A[3])*(B[2]+B[3])
        assert gap+mass(C) == mass(A)*mass(B)


def test_arbitrary_balanced_output_counterexample_is_not_a_height_theorem():
    from test_sqrt2_power_quadratic_product_trace import balances
    A = B = (1, 0, 0, 0)
    C = (11, 10, 7, 7)  # still represents the same quadratic integer 1
    assert balances(A,B,C) == (True,True)
    assert mass(C) > mass(A)*mass(B)
    assert C != canonical_product(A,B)


def test_additive_reconstructor_rejects_missing_atoms_and_oversized_inputs():
    from peano_lab.kernel.terms import Add, Var
    s = height.Scope().hypothesis("add_assoc").hypothesis("add_comm")
    with pytest.raises(ValueError):
        height._additive_equal(s, Add(Var(0),Var(1)), Add(Var(0),Var(2)))
    too_large = height._sum(tuple(Var(i) for i in range(17)))
    with pytest.raises(ValueError):
        height._additive_equal(s, too_large, too_large)


def test_original_four_identities_and_shared_dependency_order_are_frozen():
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    seen = set(height.BASIS_SOURCES) | {"double"}
    for name, source, digest in height.HELPERS:
        assert height.json_hash(encode_formula(closed_formula(source))) == digest
        assert set(height.HELPER_DEPENDENCIES[name]) <= seen
        seen.add(name)


def test_guarded_full_HA_canonical_replay_and_forgery_rejection():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle, ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = height.prove_quadratic_height()
    assert result.receipt.target == height.frozen_quadratic_height_target()
    assert len(result.bundle.nodes) == 13
    assert result.provenance["ring_normalizer_calls"] == 0
    assert result.provenance["new_axioms"] == []
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle, nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id == result.bundle.root else n for n in result.bundle.nodes))
    for bundle, target in ((result.bundle,Bot()), (forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
