"""Detached solver status must never become HA or Lean proof authority."""
import json
from unittest.mock import patch

import pytest

import observe_sqrt2_power_tail_steps as observer


def _check_frozen_helper(case):
    from hashlib import sha256
    from peano_lab.library.proof_bundle import encode_formula
    target,digest,pins=observer.target_for(case)
    assert sha256(observer.canonical(encode_formula(target))).hexdigest()==digest
    assert pins()


def test_exact_cv086_step_target():
    _check_frozen_helper("CV086-step")


def test_exact_ap048_one_sided_target():
    _check_frozen_helper("AP048-one-sided")
    assert observer.target_for("AP048-one-sided")[1]=="c60a8c74d0cb8b2fc82bafce5e3d4b1cbba2f2cd389d5b8675bc7a80891eb398"


def test_exact_cv087_ratio_target():
    _check_frozen_helper("CV087-ratio")


def test_exact_cv090_arithmetic_target():
    _check_frozen_helper("CV090-arithmetic")


def test_exact_cv092_coefficient_target():
    _check_frozen_helper("CV092-coefficient")


def test_exact_cv093_orders_target():
    _check_frozen_helper("CV093-orders")


def test_exact_cv094_step_target():
    _check_frozen_helper("CV094-step")


def test_exact_cv101_arithmetic_target():
    _check_frozen_helper("CV101-arithmetic")


def test_exact_sq003_arithmetic_target():
    _check_frozen_helper("SQ003-arithmetic")


def test_exact_sq009_residual_target():
    _check_frozen_helper("SQ009-residual")


def test_exact_sq010_arithmetic_target():
    _check_frozen_helper("SQ010-arithmetic")


def test_exact_ap001_bounds_target():
    _check_frozen_helper("AP001-bounds")


def test_exact_ap003_cross_product_target():
    _check_frozen_helper("AP003-cross-product")


def test_exact_ap005_zero_gaps_target():
    _check_frozen_helper("AP005-zero-gaps")


def test_exact_ap006_arithmetic_target():
    _check_frozen_helper("AP006-arithmetic")


def test_exact_ap007_scaled_gap_target():
    _check_frozen_helper("AP007-scaled-gap")


def test_exact_ap008_arithmetic_target():
    _check_frozen_helper("AP008-arithmetic")


def test_exact_ap009_normalization_target():
    _check_frozen_helper("AP009-normalize")


def test_exact_ap010_step_target():
    _check_frozen_helper("AP010-step")


def test_exact_ap011_length_target():
    _check_frozen_helper("AP011-length")


def test_exact_ap012_arithmetic_target():
    _check_frozen_helper("AP012-arithmetic")


def test_exact_ap014_constant_target():
    _check_frozen_helper("AP014-constant")


def test_exact_ap015_arithmetic_target():
    _check_frozen_helper("AP015-arithmetic")


def test_exact_ap017_paired_step_target():
    _check_frozen_helper("AP017-paired-step")


def test_exact_ap019_quotient_target():
    _check_frozen_helper("AP019-quotient")


def test_exact_ap020_arithmetic_target():
    _check_frozen_helper("AP020-arithmetic")


def test_exact_ap021_normalization_target():
    _check_frozen_helper("AP021-normalize")


def test_unreviewed_targets_have_no_ambient_lookup():
    for case in ("IR072","CV085",None):
        with pytest.raises(ValueError):
            observer.target_for(case)


def test_unsat_hint_stays_untrusted_and_does_not_close_any_parent(tmp_path):
    from peano_lab.kernel.formulas import Eq
    from peano_lab.kernel.terms import Zero
    target=Eq(Zero(),Zero());output=tmp_path/"diagnostic.json"
    record={"capability":{"status":"available"},"observation":{"solver_status":"unsat","proof_shaped_output_present":True}}
    with patch.object(observer,"target_for",return_value=(target,"frozen",lambda:{})),patch.object(observer,"invoke_solver",return_value=record) as solver:
        observer.observe("CV087-ratio",output,("z3",))
    assert solver.call_count==1
    report=json.loads(output.read_bytes())
    assert report["authority"]=="untrusted_classical_hints_only"
    assert report["original_HA_checked"] is report["independent_lean_checked"] is False
    assert report["solver_proofs_reconstructed"]==report["IR_parents_closed"]==report["library_admissions"]==0
    assert report["budget"]["cpu_hard_limit_ceiling_seconds"]==18 and report["budget"]["max_workers"]==1


def test_existing_output_or_duplicate_solver_is_rejected_without_execution(tmp_path):
    output=tmp_path/"exists";output.mkdir()
    with patch.object(observer,"invoke_solver") as solver:
        with pytest.raises(ValueError):
            observer.observe("CV087-ratio",output,("z3",))
        with pytest.raises(ValueError):
            observer.observe("CV087-ratio",tmp_path/"new",("z3","z3"))
    solver.assert_not_called()
