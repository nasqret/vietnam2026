#!/usr/bin/env python3
"""Observe a tiny sequential classical solver portfolio; never admit a proof.

The exact natural arithmetic targets are independently bound to the proof
producers' helper ASTs. Solver status and logs are hints only. Ordinary HA
reconstruction and fresh Lean remain separate requirements. No installation,
network access, global theorem-registry import, or portfolio parallelism.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from run_sqrt2_power_pilot import ROOT,save_new
from sqrt2_power_definitions import parse_named
from sqrt2_power_external import ExternalBudget,export_problem,invoke_solver,validate_export
from sqrt2_power_pilot_contracts import canonical
from peano_lab.library.proof_bundle import encode_formula


def target_for(case):
    if case=="CV086-step":
        import sqrt2_power_ternary_atanh_bound as producer
        helper,pins = "step_bound",producer.ternary_atanh_bound_source_pins
    elif case=="CV087-ratio":
        import sqrt2_power_scaled_exp_tail as producer
        helper,pins = "ratio",producer.scaled_exp_tail_source_pins
    elif case=="CV090-arithmetic":
        import sqrt2_power_atanh_truncation as producer
        helper,pins = "arithmetic",producer.atanh_truncation_source_pins
    elif case=="CV092-coefficient":
        import sqrt2_power_atanh_scale_independence as producer
        helper,pins = "coefficient_cross",producer.atanh_scale_independence_source_pins
    elif case=="CV093-orders":
        import sqrt2_power_independent_atanh_truncation as producer
        helper,pins = "cross_orders",producer.independent_atanh_truncation_source_pins
    elif case=="CV094-step":
        import sqrt2_power_exp_term_difference as producer
        helper,pins = "step",producer.exp_term_difference_source_pins
    elif case=="CV101-arithmetic":
        import sqrt2_power_exp_two_error_bound as producer
        helper,pins = "arithmetic",producer.exp_two_error_bound_source_pins
    elif case=="SQ003-arithmetic":
        import sqrt2_power_scaled_sqrt2 as producer
        helper,pins = "arithmetic",producer.scaled_sqrt2_source_pins
    elif case=="SQ009-residual":
        import sqrt2_power_dyadic_sqrt2_square_error as producer
        helper,pins = "floor_residual",producer.dyadic_sqrt2_square_error_source_pins
    elif case=="SQ010-arithmetic":
        import sqrt2_power_dyadic_sqrt2_reciprocal as producer
        helper,pins = "arithmetic",producer.dyadic_sqrt2_reciprocal_source_pins
    elif case=="AP001-bounds":
        import sqrt2_power_log_root_argument as producer
        helper,pins = "bounds",producer.log_root_argument_source_pins
    elif case=="AP003-cross-product":
        import sqrt2_power_log_root_independence as producer
        helper,pins = "cross_product",producer.log_root_independence_source_pins
    elif case=="AP005-zero-gaps":
        import sqrt2_power_exp_sample_independence as producer
        helper,pins = "zero_gaps",producer.exp_sample_independence_source_pins
    elif case=="AP006-arithmetic":
        import sqrt2_power_argument_modulus as producer
        helper,pins = "arithmetic",producer.argument_modulus_source_pins
    elif case=="AP007-scaled-gap":
        import sqrt2_power_exp_two_sided_continuity as producer
        helper,pins = "scaled_gap",producer.exp_two_sided_continuity_source_pins
    elif case=="AP008-arithmetic":
        import sqrt2_power_exp_two_sided_horizons as producer
        helper,pins = "arithmetic",producer.exp_two_sided_horizons_source_pins
    elif case=="AP009-normalize":
        import sqrt2_power_exp_sample_modulus as producer
        helper,pins = "normalize",producer.exp_sample_modulus_source_pins
    elif case=="AP010-step":
        import sqrt2_power_positive_power_comparison as producer
        helper,pins = "step",producer.positive_power_comparison_source_pins
    elif case=="AP011-length":
        import sqrt2_power_approximation_power_bounds as producer
        helper,pins = "length",producer.approximation_power_bounds_source_pins
    elif case=="AP012-arithmetic":
        import sqrt2_power_exp_sample_uniform_error as producer
        helper,pins = "arithmetic",producer.exp_sample_uniform_error_source_pins
    elif case=="AP014-constant":
        import sqrt2_power_fixed_precision_threshold as producer
        helper,pins = "constant_bound",producer.fixed_precision_threshold_source_pins
    elif case=="AP015-arithmetic":
        import sqrt2_power_exp_sample_dyadic_error as producer
        helper,pins = "arithmetic",producer.exp_sample_dyadic_error_source_pins
    elif case=="AP017-paired-step":
        import sqrt2_power_paired_horner as producer
        helper,pins = "paired_step",producer.paired_horner_source_pins
    elif case=="AP019-quotient":
        import sqrt2_power_odd_horner_quotient as producer
        helper,pins = "quotient",producer.odd_horner_quotient_source_pins
    elif case=="AP020-arithmetic":
        import sqrt2_power_finite_odd_log_series as producer
        helper,pins = "arithmetic",producer.finite_odd_log_series_source_pins
    elif case=="AP021-normalize":
        import sqrt2_power_finite_exp_series as producer
        helper,pins = "normalize",producer.finite_exp_series_source_pins
    elif case in ("AP033-step","AP033-budget"):
        import sqrt2_power_log_exp_budget as producer
        helper,pins = case.split("-",1)[1],producer.log_exp_budget_source_pins
    elif case=="AP038-arithmetic":
        import sqrt2_power_exp_convolution_recurrence as producer
        helper,pins = 'arithmetic',producer.exp_convolution_recurrence_source_pins
    elif case=="AP043-arithmetic":
        import sqrt2_power_exp_supplied_product as producer
        helper,pins = 'arithmetic',producer.exp_supplied_product_source_pins
    elif case=="AP048-one-sided":
        import sqrt2_power_square_error_linear as producer
        helper,pins = 'one_sided',producer.square_error_linear_source_pins
    elif case=="AP051-ratio":
        import sqrt2_power_exp_large_argument_ratio as producer
        helper,pins = 'ratio',producer.exp_large_argument_ratio_source_pins
    elif case=="AP056-step":
        import sqrt2_power_exp_geometric_majorant as producer
        helper,pins = 'step',producer.exp_geometric_majorant_source_pins
    elif case=="AP060-cross-step":
        import sqrt2_power_exp_recurrence_independence as producer
        helper,pins = 'cross_step',producer.exp_recurrence_independence_source_pins
    elif case=="AP061-arithmetic":
        import sqrt2_power_exp_supplied_large_product as producer
        helper,pins = 'arithmetic',producer.exp_supplied_large_product_source_pins
    elif case=="AP062-arithmetic":
        import sqrt2_power_exp_binary_budget as producer
        helper,pins = 'arithmetic',producer.exp_binary_budget_source_pins
    elif case=="AP063-arithmetic":
        import sqrt2_power_exp_requested_truncation as producer
        helper,pins = 'arithmetic',producer.exp_requested_truncation_source_pins
    elif case=="AP065-arithmetic":
        import sqrt2_power_exp_independent_horizon as producer
        helper,pins = 'arithmetic',producer.exp_independent_horizon_source_pins
    elif case=="AP068-arithmetic":
        import sqrt2_power_exp_relative_continuity as producer
        helper,pins = 'arithmetic',producer.exp_relative_continuity_source_pins
    elif case=="AP070-arithmetic":
        import sqrt2_power_exp_absolute_continuity as producer
        helper,pins = 'arithmetic',producer.exp_absolute_continuity_source_pins
    elif case=="AP072-arithmetic":
        import sqrt2_power_exp_integer_majorant as producer
        helper,pins = 'arithmetic',producer.exp_integer_majorant_source_pins
    elif case=="AP075-arithmetic":
        import sqrt2_power_exp_dyadic_continuity as producer
        helper,pins = 'arithmetic',producer.exp_dyadic_continuity_source_pins
    elif case=="AP076-arithmetic":
        import sqrt2_power_ordered_power_difference as producer
        helper,pins = 'arithmetic',producer.ordered_power_difference_source_pins
    elif case=="AP080-arithmetic":
        import sqrt2_power_requested_power_precision as producer
        helper,pins = 'arithmetic',producer.requested_power_precision_source_pins
    elif case=="AP081-arithmetic":
        import sqrt2_power_exp_joint_error as producer
        helper,pins = 'arithmetic',producer.exp_joint_error_source_pins
    elif case=="AP082-arithmetic":
        import sqrt2_power_log_exp_refinement as producer
        helper,pins = 'arithmetic',producer.log_exp_refinement_source_pins
    elif case=="AP083-arithmetic":
        import sqrt2_power_log_exp_cutoff_refinement as producer
        helper,pins = 'arithmetic',producer.log_exp_cutoff_refinement_source_pins
    elif case=="AP084-arithmetic":
        import sqrt2_power_log_exp_uniform_two as producer
        helper,pins = 'arithmetic',producer.log_exp_uniform_two_source_pins
    elif case=="AP085-indices":
        import sqrt2_power_fixed_log_exp_convergence as producer
        helper,pins = 'indices',producer.fixed_log_exp_convergence_source_pins
    elif case=="AP087-scaled-gap":
        import sqrt2_power_half_log_exp_refinement as producer
        helper,pins = 'scaled_gap',producer.half_log_exp_refinement_source_pins
    elif case=="AP089-arithmetic":
        import sqrt2_power_half_log_root_uniform as producer
        helper,pins = 'arithmetic',producer.half_log_root_uniform_source_pins
    elif case=="AP092-arithmetic":
        import sqrt2_power_fixed_half_log_fine_root as producer
        helper,pins = 'arithmetic',producer.fixed_half_log_fine_root_source_pins
    elif case=="AP093-arithmetic":
        import sqrt2_power_log_root_half_argument as producer
        helper,pins = 'arithmetic',producer.log_root_half_argument_source_pins
    elif case=="AP094-arithmetic":
        import sqrt2_power_exp_log_root_half_transport as producer
        helper,pins = 'arithmetic',producer.exp_log_root_half_transport_source_pins
    else:
        raise ValueError("unreviewed finite arithmetic solver target")
    target = parse_named(producer.HELPER_SOURCES[helper],registry=producer.definition_registry())
    digest = sha256(canonical(encode_formula(target))).hexdigest()
    if digest!=producer.HELPER_TARGET_SHA256[helper]:
        raise ValueError("helper formula differs from independently frozen producer target")
    return target,digest,pins


def observe(case,output,solvers,vampire=None):
    if output.exists() or output.is_symlink() or len(solvers)!=len(set(solvers)):
        raise ValueError("new output and distinct sequential solvers required")
    target,digest,pins = target_for(case);before = pins()
    budget = ExternalBudget(cpu_seconds=18,wall_seconds=25);observations = []
    for solver in solvers:
        exported = export_problem(target,format="smt2" if solver=="z3" else "tptp")
        validate_export(exported,target)
        record = invoke_solver(exported,solver,budget=budget,seconds=3,
            executable=vampire if solver=="vampire" else None)
        observations.append(dict(export=exported,observation=record))
        print(json.dumps(dict(case=case,solver=solver,capability=record["capability"]["status"],
            result=record["observation"],ha_authority=False)),flush=True)
    if pins()!=before or target_for(case)[1]!=digest:
        raise ValueError("proof producer changed during detached solver observation")
    report = dict(schema="sqrt2-power-finite-tail-solver-observation-v1",case=case,
        target_ast_sha256=digest,producer_source_pins=before,
        observer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),observations=observations,
        budget=budget.snapshot(),authority="untrusted_classical_hints_only",
        original_HA_checked=False,independent_lean_checked=False,
        solver_proofs_reconstructed=0,IR_parents_closed=0,library_admissions=0)
    save_new(output,canonical(report)+b"\n")


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",required=True,choices=("CV086-step","CV087-ratio","CV090-arithmetic","CV092-coefficient","CV093-orders","CV094-step","CV101-arithmetic","AP010-step","AP011-length","AP012-arithmetic","AP014-constant","AP015-arithmetic","AP017-paired-step","AP019-quotient","AP020-arithmetic","AP021-normalize","AP033-step","AP033-budget","AP038-arithmetic","AP043-arithmetic","AP048-one-sided","AP051-ratio","AP056-step","AP060-cross-step","AP061-arithmetic","AP062-arithmetic","AP063-arithmetic","AP065-arithmetic","AP068-arithmetic","AP070-arithmetic","AP072-arithmetic","AP075-arithmetic","AP076-arithmetic","AP080-arithmetic","AP081-arithmetic","AP082-arithmetic","AP083-arithmetic","AP084-arithmetic","AP085-indices","SQ003-arithmetic","SQ009-residual","SQ010-arithmetic","AP001-bounds","AP003-cross-product","AP005-zero-gaps","AP006-arithmetic","AP007-scaled-gap","AP008-arithmetic","AP009-normalize"))
    parser._option_string_actions['--case'].choices += ('AP087-scaled-gap','AP089-arithmetic','AP092-arithmetic','AP093-arithmetic','AP094-arithmetic')
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--solvers",nargs="+",choices=("z3","eprover","vampire"),default=("z3","eprover","vampire"))
    parser.add_argument("--vampire",type=Path)
    args = parser.parse_args()
    observe(args.case,args.output,tuple(args.solvers),args.vampire)
