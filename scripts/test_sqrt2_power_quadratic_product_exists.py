"""QF003 exact statements, full-body composition and hostile proof checks."""
from dataclasses import replace
import gc
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_product_exists as product_exists


def test_exact_nine_parameters_one_premise_twelve_constructed_witnesses():
    from peano_lab.kernel.formulas import Forall, Exists, Imp, And
    from peano_lab.library.proof_bundle import encode_formula
    target = product_exists.frozen_quadratic_product_exists_target()
    encoded = encode_formula(target)
    assert product_exists.json_hash(encoded) == product_exists.TARGET_SHA256
    assert len(product_exists.canonical(encoded)) == 7074
    for _ in range(9):
        assert type(target) is Forall
        target = target.body
    assert type(target) is Imp
    target = target.consequent
    for _ in range(12):
        assert type(target) is Exists
        target = target.body
    assert type(target) is And and type(target.right) is And


def test_honest_integer_scope_has_no_trace_or_value_premise():
    contract = product_exists.source_contract()
    assert contract["premise_count"] == 1
    for key in ("supplied_trace_required", "supplied_terminal_value_required", "height_bound",
                "rational_denominator_claim", "real_interpretation", "closes_IR046", "closes_IR072",
                "original_HA_checked"):
        assert contract[key] is False
    assert contract["reused_definition_ids"] == ["ND0390", "ND0391", "ND0392", "ND0393"]
    assert contract["IR_parents_closed"] == contract["library_admissions"] == 0


def test_frozen_target_rejects_added_trace_premise_and_dropped_nonzero_factors():
    source = product_exists.NAMED_SOURCE
    factors = product_exists.named("IQuadNonzeroFactors", *product_exists.F, "L") + " -> "
    for changed in (source.replace(factors, ""), source.replace("exists ub", "0=0 -> exists ub"),
                    source.replace("~(rp=rn /\\ sp=sn)", "rp=rn /\\ sp=sn")):
        with patch.object(product_exists, "NAMED_SOURCE", changed), pytest.raises(ValueError):
            product_exists.frozen_quadratic_product_exists_target()


def test_exact_archives_keep_full_bodies_and_decode_endpoint():
    for pin in product_exists.ARCHIVES:
        rows = product_exists.read_archive(pin)
        assert len(rows) == pin["nodes"]
        assert product_exists.json_hash(rows[pin["root"]][1]) == pin["target_ast_sha256"]
        if pin["case"] == "QF002":
            assert product_exists.json_hash(rows[103][1]) == product_exists.DECODE_TARGET_SHA256
        del rows
        gc.collect()


def test_merge_preserves_actual_first_archive_and_ordered_dependencies():
    original = product_exists.read_archive(product_exists.ARCHIVES[0])
    original_bytes = product_exists.canonical(original)
    del original
    gc.collect()
    rows, endpoints, count, depth = product_exists.merge_actual_rows()
    assert product_exists.canonical(rows[:224]) == original_bytes
    assert endpoints["QF001"] == 223
    assert product_exists.json_hash(rows[endpoints["QF002"]][1]) == product_exists.ARCHIVES[1]["target_ast_sha256"]
    assert product_exists.json_hash(rows[endpoints["decode"]][1]) == product_exists.DECODE_TARGET_SHA256
    assert 81603 < count < 200000 and depth <= 256
    for index, row in enumerate(rows):
        assert len(set(row[2])) == len(row[2]) and all(d < index for d in row[2])


def test_changed_full_archive_bytes_and_decode_endpoint_are_rejected():
    pin = dict(product_exists.ARCHIVES[1], sha256="0"*64)
    with pytest.raises(ValueError):
        product_exists.read_archive(pin)
    with patch.object(product_exists, "DECODE_TARGET_SHA256", "0"*64), pytest.raises(ValueError):
        product_exists.merge_actual_rows()


def test_guarded_full_canonical_HA_and_forged_body_false_target_rejection():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle, ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = product_exists.prove_quadratic_product_exists()
    assert result.receipt.target == product_exists.frozen_quadratic_product_exists_target()
    assert result.provenance["constructed_trace_and_terminal_tuple"] is True
    assert result.provenance["integer_product_nonzero_proved"] is True
    assert result.provenance["height_bound"] is False
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["new_axioms"] == result.provenance["external_certificate_references"] == []
    forged = replace(result.bundle, nodes=tuple(replace(n, body=EqRefl(Zero()))
        if n.node_id == result.bundle.root else n for n in result.bundle.nodes))
    for bundle, target in ((result.bundle, Bot()), (forged, result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle, target, limits=BinaryDAGLimits().bundle_limits())
