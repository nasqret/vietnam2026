"""Exact QF002 contracts, hostile mutations and guarded native proof replay."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_trace_exists as total


def test_unconditional_nine_universal_eight_existential_exact_target():
    from peano_lab.kernel.formulas import Forall, Exists, And
    from peano_lab.library.proof_bundle import encode_formula
    target = total.frozen_quadratic_trace_exists_target()
    assert total.json_hash(encode_formula(target)) == total.TARGET_SHA256
    assert len(total.canonical(encode_formula(target))) == 4891
    for kind, count in ((Forall, 9), (Exists, 8)):
        for _ in range(count):
            assert type(target) is kind
            target = target.body
    assert type(target) is And
    contract = total.source_contract()
    assert contract["premise_count"] == 0
    assert contract["nonzero_factors_required"] is False
    assert contract["conditional_on_actual_trace"] is False
    assert contract["original_HA_checked"] is False
    assert contract["closes_IR046"] is False and contract["closes_IR072"] is False
    assert contract["library_admissions"] == 0


def test_exact_helpers_reuse_definitions_and_backward_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = total.definition_registry()
    seen = set(total.ENDPOINTS)
    for name, source, dependencies in total.HELPERS:
        assert set(dependencies) <= seen
        assert len(set(dependencies)) == len(dependencies)
        target = parse_named(source, registry=registry)
        assert total.json_hash(encode_formula(target)) == total.HELPER_TARGET_SHA256[name]
        seen.add(name)
    assert registry["IQuadProductTrace"].stable_id == "ND0392"
    assert "IQuadNonzeroFactors" not in total.NAMED_SOURCE


def test_dropped_quantifier_changed_length_and_hidden_premise_rejected():
    for changed in (total.NAMED_SOURCE.replace("forall ab", "forall"),
                    total.NAMED_SOURCE.replace(",L)", ",S L)"),
                    total.NAMED_SOURCE.replace("exists ub", "0=0 -> exists ub")):
        with patch.object(total, "NAMED_SOURCE", changed), pytest.raises(ValueError):
            total.frozen_quadratic_trace_exists_target()


def test_ancestor_bytes_not_receipts_and_exact_endpoint_formulas():
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    ids, rows = total.inert_ancestor_rows()
    assert len(ids) == 103
    assert total.json_hash(rows) == total.ANCESTOR_ROWS_SHA256
    assert len(total.canonical(rows)) == 150740
    table = dict(zip(ids, rows))
    for old, (_, source, digest) in total.ENDPOINTS.items():
        assert table[old][1] == encode_formula(closed_formula(source))
        assert total.json_hash(table[old]) == digest
        assert all(parent < old for parent in table[old][2])


def test_changed_archive_and_endpoint_pins_fail_closed():
    with patch.object(total, "V28_ARTIFACT_SHA256", "0"*64), pytest.raises(ValueError):
        total.inert_ancestor_rows()
    endpoints = dict(total.ENDPOINTS)
    name, source, digest = endpoints[121]
    endpoints[121] = name, source.replace("exists x.", "forall x."), digest
    with patch.object(total, "ENDPOINTS", endpoints), pytest.raises(ValueError):
        total.inert_ancestor_rows()


def test_scoped_names_are_hygienic_and_unknown_names_fail():
    from peano_lab.kernel.terms import Var
    from peano_lab.kernel.proofs import Hyp
    s = total.Scope().variable("a").hypothesis("left").variable("b").hypothesis("right")
    assert s.term("a") == Var(1) and s.term("b") == Var(0)
    assert s.hyp("left") == Hyp(1) and s.hyp("right") == Hyp(0)
    for action in (lambda: s.variable("a"), lambda: s.hypothesis("right"),
                   lambda: s.term("missing"), lambda: s.hyp("missing")):
        with pytest.raises(ValueError):
            action()


def test_canonical_product_terms_include_zero_and_noncanonical_representatives():
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    s = total.Scope()
    for name in total.A+total.B:
        s = s.variable(name)
    terms = total.products(s)
    def evaluate(term, values):
        if type(term) is Zero:
            return 0
        if type(term) is Var:
            return values[s.variables[term.index]]
        if type(term) is Succ:
            return evaluate(term.term, values)+1
        left, right = evaluate(term.left, values), evaluate(term.right, values)
        return left+right if type(term) is Add else left*right
    for entries in product(range(2), repeat=8):
        values = dict(zip(total.A+total.B, entries))
        ap, an, bp, bn, cp, cn, dp, dn = entries
        rp, rn, sp, sn = [evaluate(t, values) for t in terms]
        assert rp-rn == (ap-an)*(cp-cn)+2*(bp-bn)*(dp-dn)
        assert sp-sn == (ap-an)*(dp-dn)+(bp-bn)*(cp-cn)


def test_guarded_full_canonical_HA_and_false_target_forged_root_rejection():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle, ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = total.prove_quadratic_trace_exists()
    assert result.receipt.target == total.frozen_quadratic_trace_exists_target()
    assert len(result.bundle.nodes) == 108
    assert result.provenance["trace_existence_proved"] is True
    assert result.provenance["root_induction_count"] == 1
    assert result.provenance["new_axioms"] == []
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle, nodes=tuple(replace(n, body=EqRefl(Zero()))
        if n.node_id == result.bundle.root else n for n in result.bundle.nodes))
    for bundle, target in ((result.bundle, Bot()), (forged, result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle, target, limits=BinaryDAGLimits().bundle_limits())
