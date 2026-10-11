#!/usr/bin/env python3
"""Run bounded regression batches in fresh processes; never widen a failed batch."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from run_sqrt2_power_pilot import ROOT, save_new, successful, controller_deadline
from sqrt2_power_automation_baseline import runtime


def validate(output, files):
    if output.exists() or output.is_symlink():
        raise ValueError("new validation report required")
    validator_sha256 = sha256(Path(__file__).read_bytes()).hexdigest()
    batches, pins = [], {}
    for relative in files:
        path = ROOT / relative
        raw = path.read_bytes()
        pins[relative] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        if path.name == "test_sqrt2_power_campaign.py":
            test_class = next(n for n in ast.parse(raw).body
                if isinstance(n, ast.ClassDef) and n.name == "CampaignPlanTests")
            ordinary, regeneration = [], []
            for node in test_class.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    group = regeneration if node.name == "test_regeneration_is_byte_deterministic" else ordinary
                    group.append(relative+"::CampaignPlanTests::"+node.name)
            if not ordinary or len(regeneration) != 1:
                raise ValueError("campaign regeneration test boundary changed")
            # Fresh regeneration versus the independently built on-disk
            # snapshot has its own allocator lifetime.
            batches.extend((ordinary, regeneration))
        elif path.name in {"test_sqrt2_power_wave_results.py", "test_sqrt2_power_signed_norm.py",
                           "test_sqrt2_power_norm_separation.py", "test_sqrt2_power_quadratic_norm_product.py",
                           "test_sqrt2_power_convolution_vanishing.py", "test_sqrt2_power_rational_norm_product.py",
                           "test_sqrt2_power_rational_norm_transport.py", "test_sqrt2_power_signed_product_nonzero.py",
                           "test_sqrt2_power_quadratic_nonzero.py", "test_sqrt2_power_quadratic_product_trace.py",
                           "test_sqrt2_power_quadratic_trace_exists.py",
                           "test_sqrt2_power_quadratic_product_exists.py",
                           "test_sqrt2_power_quadratic_height.py",
                           "test_sqrt2_power_canonical_quadratic_trace.py",
                           "test_sqrt2_power_quadratic_trace_height.py",
                           "test_sqrt2_power_bounded_quadratic_product.py",
                           "test_sqrt2_power_logexp_recurrence.py",
                           "test_sqrt2_power_natural_convolution.py",
                           "test_sqrt2_power_series_power_trace.py",
                           "test_sqrt2_power_series_power_vanishing.py",
                           "test_sqrt2_power_sum_linearity.py",
                           "test_sqrt2_power_euler_product.py",
                           "test_sqrt2_power_natural_fubini.py",
                           "test_sqrt2_power_sum_splitting.py",
                           "test_sqrt2_power_convolution_commutative.py",
                           "test_sqrt2_power_sum_zero_tail.py",
                           "test_sqrt2_power_triple_grid.py",
                           "test_sqrt2_power_triple_row_sum.py",
                           "test_sqrt2_power_convolution_associative.py",
                           "test_sqrt2_power_convolution_linearity.py",
                           "test_sqrt2_power_convolution_unit.py",
                           "test_sqrt2_power_series_power_euler.py",
                           "test_sqrt2_power_series_linear_combination.py",
                           "test_sqrt2_power_weighted_series_trace.py",
                           "test_sqrt2_power_shifted_euler_prefix.py",
                           "test_sqrt2_power_finite_composition_euler.py",
                           "test_sqrt2_power_exponential_weights.py",
                           "test_sqrt2_power_weighted_series_scaling.py",
                           "test_sqrt2_power_denominator_euler.py",
                           "test_sqrt2_power_atanh_coefficients.py",
                           "test_sqrt2_power_atanh_euler.py",
                           "test_sqrt2_power_periodic_convolution.py",
                           "test_sqrt2_power_composition_recurrence.py",
                           "test_sqrt2_power_composition_coefficients.py",
                           "test_sqrt2_power_weight_factorials.py",
                           "test_sqrt2_power_normalized_composition.py",
                           "test_sqrt2_power_horner_trace.py",
                           "test_sqrt2_power_geometric_horner.py",
                           "test_sqrt2_power_composition_evaluation.py",
                           "test_sqrt2_power_horner_linearity.py",
                           "test_sqrt2_power_horner_zero_tail.py",
                           "test_sqrt2_power_horner_weighted_sum.py",
                           "test_sqrt2_power_geometric_weights.py",
                           "test_sqrt2_power_constructed_horner_sum.py",
                           "test_sqrt2_power_horner_monomials.py",
                           "test_sqrt2_power_convolution_weights.py",
                           "test_sqrt2_power_weighted_convolution.py",
                           "test_sqrt2_power_shifted_scaled_sum.py",
                           "test_sqrt2_power_cauchy_grid.py",
                           "test_sqrt2_power_cauchy_row_sum.py",
                           "test_sqrt2_power_cauchy_column_sum.py",
                           "test_sqrt2_power_cauchy_grid_sums.py",
                           "test_sqrt2_power_convolution_total.py",
                           "test_sqrt2_power_horner_product.py",
                           "test_sqrt2_power_convolution_locality.py",
                           "test_sqrt2_power_power_width_transport.py",
                           "test_sqrt2_power_composition_width_transport.py",
                           "test_sqrt2_power_convolution_upper_support.py",
                           "test_sqrt2_power_power_upper_support.py",
                           "test_sqrt2_power_horner_prefix_transport.py",
                           "test_sqrt2_power_supported_horner_product.py",
                           "test_sqrt2_power_supported_horner_values.py",
                           "test_sqrt2_power_finite_power_evaluation.py",
                           "test_sqrt2_power_row_horner_values.py",
                           "test_sqrt2_power_weighted_accumulation_evaluation.py",
                           "test_sqrt2_power_full_composition_evaluation.py",
                           "test_sqrt2_power_horner_splitting.py",
                           "test_sqrt2_power_horner_base_comparison.py",
                           "test_sqrt2_power_horner_tail_majorant.py",
                           "test_sqrt2_power_bounded_horner.py",
                           "test_sqrt2_power_atanh_majorant.py",
                           "test_sqrt2_power_factorial_majorant.py",
                           "test_sqrt2_power_ratio_sum_bound.py",
                           "test_sqrt2_power_power_weighted_prefix.py",
                           "test_sqrt2_power_scaled_exp_terms.py",
                           "test_sqrt2_power_scaled_exp_bound.py",
                           "test_sqrt2_power_monomial_recurrence.py",
                           "test_sqrt2_power_weighted_monomial_recurrence.py",
                           "test_sqrt2_power_composition_majorant.py",
                           "test_sqrt2_power_rational_tail_majorant.py",
                           "test_sqrt2_power_composition_tail_bound.py",
                           "test_sqrt2_power_supplied_composition_bound.py",
                           "test_sqrt2_power_consumed_row_transport.py",
                           "test_sqrt2_power_successor_composition_transport.py",
                           "test_sqrt2_power_same_table_composition.py",
                           "test_sqrt2_power_supplied_composition_evaluation.py",
                           "test_sqrt2_power_supplied_horner_splitting.py",
                           "test_sqrt2_power_geometric_tail_sandwich.py",
                           "test_sqrt2_power_supplied_geometric_error.py",
                           "test_sqrt2_power_constructed_composition_error.py",
                           "test_sqrt2_power_ternary_atanh_bound.py",
                           "test_sqrt2_power_scaled_exp_tail.py",
                           "test_sqrt2_power_scaled_exp_tail_decay.py",
                           "test_sqrt2_power_ternary_prefix_bound.py",
                           "test_sqrt2_power_atanh_truncation.py",
                           "test_sqrt2_power_atanh_rational_truncation.py",
                           "test_sqrt2_power_atanh_scale_independence.py",
                           "test_sqrt2_power_independent_atanh_truncation.py",
                           "test_sqrt2_power_exp_term_difference.py",
                           "test_sqrt2_power_sum_linear_bound.py",
                           "test_sqrt2_power_exp_sum_continuity.py",
                           "test_sqrt2_power_exp_rescaling.py",
                           "test_sqrt2_power_exp_cross_continuity.py",
                           "test_sqrt2_power_exp_rational_continuity.py",
                           "test_sqrt2_power_exp_truncation.py",
                           "test_sqrt2_power_exp_two_error_bound.py",
                           "test_sqrt2_power_exp_rational_two_error.py",
                           "test_sqrt2_power_floor_sqrt.py",
                           "test_sqrt2_power_floor_sqrt_comparison.py",
                           "test_sqrt2_power_scaled_sqrt2.py",
                           "test_sqrt2_power_dyadic_sqrt2.py",
                           "test_sqrt2_power_floor_sqrt_scaling.py",
                           "test_sqrt2_power_dyadic_sqrt2_refinement.py",
                           "test_sqrt2_power_dyadic_sqrt2_intervals.py",
                           "test_sqrt2_power_dyadic_sqrt2_modulus.py",
                           "test_sqrt2_power_dyadic_sqrt2_square_error.py",
                           "test_sqrt2_power_dyadic_sqrt2_reciprocal.py",
                           "test_sqrt2_power_log_root_argument.py",
                           "test_sqrt2_power_exp_sample.py",
                           "test_sqrt2_power_log_root_independence.py",
                           "test_sqrt2_power_supplied_exp_sample.py",
                           "test_sqrt2_power_exp_sample_independence.py",
                           "test_sqrt2_power_argument_modulus.py",
                           "test_sqrt2_power_exp_two_sided_continuity.py",
                           "test_sqrt2_power_exp_two_sided_horizons.py",
                           "test_sqrt2_power_exp_sample_modulus.py",
                           "test_sqrt2_power_positive_power_comparison.py",
                           "test_sqrt2_power_approximation_power_bounds.py",
                           "test_sqrt2_power_exp_sample_uniform_error.py",
                           "test_sqrt2_power_exp_sample_all_precision.py",
                           "test_sqrt2_power_fixed_precision_threshold.py",
                           "test_sqrt2_power_exp_sample_dyadic_error.py",
                           "test_sqrt2_power_atanh_odd_slice.py",
                           "test_sqrt2_power_paired_horner.py",
                           "test_sqrt2_power_paired_power.py",
                           "test_sqrt2_power_odd_horner_quotient.py",
                           "test_sqrt2_power_finite_odd_log_series.py",
                           "test_sqrt2_power_finite_exp_series.py",
                           "test_sqrt2_power_factorial_atanh_prefix.py",
                           "test_sqrt2_power_factorial_exp_sample.py",
                           "test_sqrt2_power_atomic_computation_decisions.py",
                           "test_sqrt2_power_approximation_component_decisions.py",
                           "test_sqrt2_power_finite_table_decisions.py",
                           "test_sqrt2_power_prescribed_sample_decision.py",
                           "test_sqrt2_power_approximation_record_exists.py",
                           "test_sqrt2_power_approximation_record_decision.py",
                           "test_sqrt2_power_approximation_record_independence.py",
                           "test_sqrt2_power_approximation_record_error.py",
                           "test_sqrt2_power_log_exp_witness.py",
                           "test_sqrt2_power_log_exp_budget.py",
                           "test_sqrt2_power_log_exp_dyadic_witness.py",
                           "test_sqrt2_power_exp_recurrence_normalization.py",
                           "test_sqrt2_power_exp_recurrence_series.py",
                           "test_sqrt2_power_convolution_shift.py",
                           "test_sqrt2_power_exp_convolution_recurrence.py",
                           "test_sqrt2_power_exp_convolution_prefix.py",
                           "test_sqrt2_power_convolution_prefix_order.py",
                           "test_sqrt2_power_convolution_sum_sandwich.py",
                           "test_sqrt2_power_exp_product_error.py",
                           "test_sqrt2_power_exp_supplied_product.py",
                           "test_sqrt2_power_exp_half_square.py",
                           "test_sqrt2_power_half_square_error_transfer.py",
                           "test_sqrt2_power_half_log_precision.py",
                           "test_sqrt2_power_half_log_square.py",
                           "test_sqrt2_power_square_error_linear.py",
                           "test_sqrt2_power_half_log_root_comparison.py",
                           "test_sqrt2_power_half_log_root_witness.py",
                           "test_sqrt2_power_exp_large_argument_ratio.py",
                           "test_sqrt2_power_exp_large_argument_tail.py",
                           "test_sqrt2_power_halving_prefix_decay.py",
                           "test_sqrt2_power_exp_large_argument_decay.py",
                           "test_sqrt2_power_exp_large_argument_truncation.py",
                           "test_sqrt2_power_exp_geometric_majorant.py",
                           "test_sqrt2_power_exp_normalized_truncation.py",
                           "test_sqrt2_power_exp_normalized_witness.py",
                           "test_sqrt2_power_exp_large_argument_product.py",
                           "test_sqrt2_power_exp_recurrence_independence.py",
                           "test_sqrt2_power_exp_supplied_large_product.py",
                           "test_sqrt2_power_exp_binary_budget.py",
                           "test_sqrt2_power_exp_requested_truncation.py",
                           "test_sqrt2_power_exp_requested_product.py",
                           "test_sqrt2_power_exp_independent_horizon.py",
                           "test_sqrt2_power_exp_uniform_witness.py",
                           "test_sqrt2_power_exp_product_witness.py",
                           "test_sqrt2_power_exp_relative_continuity.py",
                           "test_sqrt2_power_exp_relative_cross_continuity.py",
                           "test_sqrt2_power_exp_absolute_continuity.py",
                           "test_sqrt2_power_exp_submultiplicative.py",
                           "test_sqrt2_power_exp_integer_majorant.py",
                           "test_sqrt2_power_exp_bounded_majorant.py",
                           "test_sqrt2_power_exp_bounded_continuity.py",
                           "test_sqrt2_power_exp_dyadic_continuity.py",
                           "test_sqrt2_power_ordered_power_difference.py",
                           "test_sqrt2_power_symmetric_power_difference.py",
                           "test_sqrt2_power_product_power.py",
                           "test_sqrt2_power_rational_power_difference.py",
                           "test_sqrt2_power_requested_power_precision.py",
                           "test_sqrt2_power_exp_joint_error.py",
                           "test_sqrt2_power_log_exp_refinement.py",
                           "test_sqrt2_power_log_exp_cutoff_refinement.py",
                           "test_sqrt2_power_log_exp_uniform_two.py",
                           "test_sqrt2_power_fixed_log_exp_convergence.py",
                           "test_sqrt2_power_fixed_log_exp_witness.py",
                           "test_sqrt2_power_half_log_exp_refinement.py",
                           "test_sqrt2_power_half_log_exp_cutoff.py",
                           "test_sqrt2_power_half_log_root_uniform.py",
                           "test_sqrt2_power_fixed_half_log_root.py",
                           "test_sqrt2_power_tail_solver_observer.py",
                           "test_sqrt2_power_arithmetic_wave.py"}:
            # Expected-exception tests retain large historical payloads within
            # pytest. Bound that lifetime by grouping four source functions.
            names = []
            for node in ast.parse(raw).body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    names.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    names.extend(node.name+"::"+member.name for member in node.body
                                 if isinstance(member, ast.FunctionDef) and member.name.startswith("test_"))
            if not names:
                raise ValueError("fresh-process test inventory is empty")
            # The signed-norm archive tests parse a large historical source.
            # Do not retain that allocator lifetime into a new proof fixture.
            width = 4 if path.name == "test_sqrt2_power_wave_results.py" else 1
            for i in range(0, len(names), width):
                selected = names[i:i+width]
                if (path.name == "test_sqrt2_power_arithmetic_wave.py" and selected ==
                        ["test_exact_new_statements_and_bytes_have_fresh_HA_and_Lean_evidence"]):
                    # Each parameter validates every indexed archive. The
                    # expanded wave no longer fits all parameters into one
                    # CPU-capped process; keep each parameter's lifetime short.
                    assignments = [n for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "ATTEMPTS" for t in n.targets)]
                    if len(assignments) != 1:
                        raise ValueError("exact archive-test parameter inventory changed")
                    attempts = ast.literal_eval(assignments[0].value)
                    for folder, case in attempts[2:]:
                        if not all(isinstance(s, str) and s and "[" not in s and "]" not in s for s in (folder, case)):
                            raise ValueError("unsafe archive-test selector")
                        batches.append([relative+"::"+selected[0]+"["+folder+"-"+case+"]"])
                else:
                    batches.append([relative+"::"+name for name in selected])
        else:
            batches.append([relative])
    results, interruption = [], None
    started = time.monotonic()
    with controller_deadline(started+45*len(batches)):
        for batch in batches:
            command = (sys.executable, "-B", "-m", "pytest", "-q", "-x", "--tb=line",
                       "--disable-warnings", "-p", "no:cacheprovider", *batch)
            limits = runtime().ProcessLimits(cpu_seconds=25, wall_seconds=35,
                rss_bytes=512*1024**2, output_bytes=1024**2)
            try:
                process = runtime().run_bounded(command, cwd=ROOT, limits=limits)
                runtime().validate_process_record(process, command=command, limits=limits)
            except runtime().ReviewRuntimeError as error:
                # The supervisor has already killed/reaped its owned worker.
                # Preserve earlier fully validated process records, but never
                # invent a record or a success for the interrupted process.
                interruption = dict(batch=batch, reason="supervision_failed",
                    exception=type(error).__name__, message=str(error))
                print(json.dumps(dict(interruption, passed=False)), flush=True)
                break
            results.append(process)
            print(json.dumps(dict(batch=batch, passed=successful(process), reason=process["reason"],
                stdout=process["stdout"], resources=process["resources"])), flush=True)
            if not successful(process):
                break
        for name, pin in pins.items():
            if runtime().hash_file(ROOT/name) != pin:
                raise ValueError("test source changed during validation")
        if sha256(Path(__file__).read_bytes()).hexdigest() != validator_sha256:
            raise ValueError("validator source changed during validation")
        report = dict(schema="sqrt2-power-batched-validation-v1", source_pins=pins, processes=results,
            validator_sha256=validator_sha256, interruption=interruption,
            requested_batches=len(batches), completed_batches=len(results), max_workers=1,
            status="passed" if interruption is None and len(results) == len(batches) and all(successful(r) for r in results) else "failed_or_incomplete",
            elapsed_wall_seconds=time.monotonic()-started, IR_parents_closed=0)
        save_new(output, json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return report["status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    status = validate(args.output, args.files)
    raise SystemExit(0 if status == "passed" else 1)
