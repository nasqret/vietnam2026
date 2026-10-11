#!/usr/bin/env python3
"""Source-pinned, sequential proof-DAG/reconstruction observations, not admissions.

Each target is rebound independently in a fresh ordinary HA replay process.
Artifacts are lossless and append-only. Run under the reviewed OS supervisor;
no kernel limits, axioms, parent campaign status, or deployed files are changed.
"""
from dataclasses import replace
from hashlib import sha256
import argparse
import gzip
import json
from pathlib import Path
import sys
import time

from run_sqrt2_power_pilot import (
    ROOT, LeafBudget, controller_deadline, successful, save_new,
)
from sqrt2_power_automation_baseline import runtime
from sqrt2_power_pilot_contracts import canonical
from sqrt2_power_binary_dag import BinaryDAGLimits, formula_sha256
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, ProofBundleError, check_proof_bundle,
    decode_proof_bundle, encode_proof_bundle,
)

SCHEMA = "sqrt2-power-shared-proof-wave-v1"
SCRIPT = Path(__file__).resolve()
FOUNDATION_CASES = dict(RF001="irat_eq_reflexive", RF002="irat_eq_symmetric",
    RF003="irat_eq_transitive", RF004="irat_eq_scale_nonzero",
    RF005="irat_eq_numerator_shift", RF006="irat_eq_negation_compatible")
CHUNK_CASES = tuple(f"P04-C{i:02d}" for i in range(16))
CASES = ("P10", "P08-eprover", "P08-vampire", "P04-ground", "P04-soundness", "IR016",
         "SN001", "NG001", "SN002", "SN003", "CV001", "CV002", "CV003", "CV004", "CV005", "CV006", "CV007", "CV008", "CV009", "CV010", "CV011", "CV012", "CV013", "CV014", "CV015", "CV016", "CV017", "CV018", "CV019", "CV020", "CV021", "CV022", "CV023", "CV024", "CV025", "CV026", "CV027", "CV028", "CV029", "CV030", "CV031", "CV032", "CV033", "CV034", "CV035", "CV036", "CV037", "CV038", "CV039", "CV040", "CV041", "CV042", "RN001", "RN002", "SI001",
         "CV043", "CV044", "CV045", "CV046", "CV047", "CV048", "CV049", "CV050", "CV051", "CV052", "CV053", "CV054", "CV055", "CV056", "CV057", "CV058", "CV059", "CV060", "CV061", "CV062", "CV063", "CV064", "CV065", "CV066", "CV067", "CV068", "CV069", "CV070", "CV071", "CV072", "CV073", "CV074", "CV075", "CV076", "CV077", "CV078", "CV079", "CV080", "CV081", "CV082", "CV083", "CV084", "CV085", "CV086", "CV087", "CV088", "QN001", "QF001", "QF002", "QF003", "QH001", "QF004", "QH002", "QF005", *FOUNDATION_CASES, *CHUNK_CASES)
CASES += ("CV089","CV090","CV091","CV092","CV093","CV094","CV095","CV096","CV097","CV098","CV099","CV100","CV101","CV102")
CASES += ("SQ001","SQ002","SQ003","SQ004","SQ005","SQ006","SQ007","SQ008","SQ009","SQ010")
CASES += ("AP001","AP002","AP003","AP004","AP005","AP006","AP007","AP008","AP009","AP010","AP011","AP012","AP013","AP014","AP015","AP016","AP017","AP018","AP019","AP020","AP021","AP022","AP023","AP024","AP025","AP026","AP027","AP028","AP029","AP030","AP031","AP032","AP033","AP034","AP035","AP036","AP037","AP038","AP039","AP040","AP041","AP042","AP043","AP044","AP045","AP046","AP047")
LIMITS = BinaryDAGLimits().bundle_limits()
CASES += ("AP048","AP049","AP050","AP051","AP052","AP053","AP054","AP055","AP056","AP057","AP058","AP059","AP060","AP061","AP062","AP063","AP064","AP065","AP066","AP067","AP068","AP069","AP070","AP071","AP072","AP073","AP074","AP075")
CASES += ("AP076","AP077","AP078","AP079")
CASES += ("AP080",)
CASES += ("AP081",)
CASES += ("AP082",)
CASES += ("AP083",)
CASES += ("AP084",)
CASES += ("AP085",)
CASES += ("AP086",)
CASES += ("AP087",)
CASES += ("AP088",)
CASES += ("AP089",)
CASES += ("AP090",)
CASES += ("AP091",)
CASES += ("AP092",)
CASES += ("AP093",)
CASES += ("AP094",)
CASES += ("AP095",)


def pins(identifier):
    from sqrt2_power_solver_hints import source_pins
    result = source_pins()
    for name in (SCRIPT.name, "run_sqrt2_power_pilot.py", "sqrt2_power_binary_dag.py",
                 "sqrt2_power_pilot_instances.py"):
        path = ROOT / "scripts" / name
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier.startswith("P04-"):
        path = ROOT / "scripts/sqrt2_power_formal_composition.py"
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier in CHUNK_CASES:
        path = ROOT / "scripts/sqrt2_power_composition_chunks.py"
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import source_pins as foundation_pins
        result.update(foundation_pins())
    if identifier == "IR016":
        from sqrt2_power_even_square import FERMAT_ARTIFACT, FERMAT_SOURCE_PATH
        for path in (ROOT / "scripts/sqrt2_power_even_square.py", FERMAT_ARTIFACT, ROOT / FERMAT_SOURCE_PATH):
            result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier == "SN001":
        from sqrt2_power_signed_norm import signed_norm_source_pins
        result.update(signed_norm_source_pins())
    if identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import norm_separation_source_pins
        result.update(norm_separation_source_pins())
    if identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import norm_product_source_pins
        result.update(norm_product_source_pins())
    if identifier == "CV001":
        from sqrt2_power_convolution_vanishing import convolution_source_pins
        result.update(convolution_source_pins())
    if identifier == "CV002":
        from sqrt2_power_logexp_recurrence import logexp_recurrence_source_pins
        result.update(logexp_recurrence_source_pins())
    if identifier == "CV003":
        from sqrt2_power_natural_convolution import natural_convolution_source_pins
        result.update(natural_convolution_source_pins())
    if identifier == "CV004":
        from sqrt2_power_series_power_trace import series_power_trace_source_pins
        result.update(series_power_trace_source_pins())
    if identifier == "CV005":
        from sqrt2_power_series_power_vanishing import series_power_vanishing_source_pins
        result.update(series_power_vanishing_source_pins())
    if identifier == "CV006":
        from sqrt2_power_sum_linearity import sum_linearity_source_pins
        result.update(sum_linearity_source_pins())
    if identifier == "CV007":
        from sqrt2_power_euler_product import euler_product_source_pins
        result.update(euler_product_source_pins())
    if identifier == "CV008":
        from sqrt2_power_natural_fubini import natural_fubini_source_pins
        result.update(natural_fubini_source_pins())
    if identifier == "CV009":
        from sqrt2_power_sum_splitting import sum_splitting_source_pins
        result.update(sum_splitting_source_pins())
    if identifier == "CV010":
        from sqrt2_power_convolution_commutative import convolution_commutative_source_pins
        result.update(convolution_commutative_source_pins())
    if identifier == "CV011":
        from sqrt2_power_sum_zero_tail import sum_zero_tail_source_pins
        result.update(sum_zero_tail_source_pins())
    if identifier == "CV012":
        from sqrt2_power_triple_grid import triple_grid_source_pins
        result.update(triple_grid_source_pins())
    if identifier == "CV013":
        from sqrt2_power_triple_row_sum import triple_row_sum_source_pins
        result.update(triple_row_sum_source_pins())
    if identifier == "CV014":
        from sqrt2_power_convolution_associative import convolution_associative_source_pins
        result.update(convolution_associative_source_pins())
    if identifier == "CV015":
        from sqrt2_power_convolution_linearity import convolution_linearity_source_pins
        result.update(convolution_linearity_source_pins())
    if identifier == "CV016":
        from sqrt2_power_convolution_unit import convolution_unit_source_pins
        result.update(convolution_unit_source_pins())
    if identifier == "CV017":
        from sqrt2_power_series_power_euler import series_power_euler_source_pins
        result.update(series_power_euler_source_pins())
    if identifier == "CV018":
        from sqrt2_power_series_linear_combination import series_linear_combination_source_pins
        result.update(series_linear_combination_source_pins())
    if identifier == "CV019":
        from sqrt2_power_weighted_series_trace import weighted_series_trace_source_pins
        result.update(weighted_series_trace_source_pins())
    if identifier == "CV020":
        from sqrt2_power_shifted_euler_prefix import shifted_euler_prefix_source_pins
        result.update(shifted_euler_prefix_source_pins())
    if identifier == "CV021":
        from sqrt2_power_finite_composition_euler import finite_composition_euler_source_pins
        result.update(finite_composition_euler_source_pins())
    if identifier == "CV022":
        from sqrt2_power_exponential_weights import exponential_weights_source_pins
        result.update(exponential_weights_source_pins())
    if identifier == "CV023":
        from sqrt2_power_weighted_series_scaling import weighted_series_scaling_source_pins
        result.update(weighted_series_scaling_source_pins())
    if identifier == "CV024":
        from sqrt2_power_denominator_euler import denominator_euler_source_pins
        result.update(denominator_euler_source_pins())
    if identifier == "CV025":
        from sqrt2_power_atanh_coefficients import atanh_coefficients_source_pins
        result.update(atanh_coefficients_source_pins())
    if identifier == "CV026":
        from sqrt2_power_atanh_euler import atanh_euler_source_pins
        result.update(atanh_euler_source_pins())
    if identifier == "CV027":
        from sqrt2_power_periodic_convolution import periodic_convolution_source_pins
        result.update(periodic_convolution_source_pins())
    if identifier == "CV028":
        from sqrt2_power_composition_recurrence import composition_recurrence_source_pins
        result.update(composition_recurrence_source_pins())
    if identifier == "CV029":
        from sqrt2_power_composition_coefficients import composition_coefficients_source_pins
        result.update(composition_coefficients_source_pins())
    if identifier == "CV030":
        from sqrt2_power_weight_factorials import weight_factorials_source_pins
        result.update(weight_factorials_source_pins())
    if identifier == "CV031":
        from sqrt2_power_normalized_composition import normalized_composition_source_pins
        result.update(normalized_composition_source_pins())
    if identifier == "CV032":
        from sqrt2_power_horner_trace import horner_trace_source_pins
        result.update(horner_trace_source_pins())
    if identifier == "CV033":
        from sqrt2_power_geometric_horner import geometric_horner_source_pins
        result.update(geometric_horner_source_pins())
    if identifier == "CV034":
        from sqrt2_power_composition_evaluation import composition_evaluation_source_pins
        result.update(composition_evaluation_source_pins())
    if identifier == "CV035":
        from sqrt2_power_horner_linearity import horner_linearity_source_pins
        result.update(horner_linearity_source_pins())
    if identifier == "CV036":
        from sqrt2_power_horner_zero_tail import horner_zero_tail_source_pins
        result.update(horner_zero_tail_source_pins())
    if identifier == "CV037":
        from sqrt2_power_horner_weighted_sum import horner_weighted_sum_source_pins
        result.update(horner_weighted_sum_source_pins())
    if identifier == "CV038":
        from sqrt2_power_geometric_weights import geometric_weights_source_pins
        result.update(geometric_weights_source_pins())
    if identifier == "CV039":
        from sqrt2_power_constructed_horner_sum import constructed_horner_sum_source_pins
        result.update(constructed_horner_sum_source_pins())
    if identifier == "CV040":
        from sqrt2_power_horner_monomials import horner_monomials_source_pins
        result.update(horner_monomials_source_pins())
    if identifier == "CV041":
        from sqrt2_power_convolution_weights import convolution_weights_source_pins
        result.update(convolution_weights_source_pins())
    if identifier == "CV042":
        from sqrt2_power_weighted_convolution import weighted_convolution_source_pins
        result.update(weighted_convolution_source_pins())
    if identifier == "CV043":
        from sqrt2_power_shifted_scaled_sum import shifted_scaled_sum_source_pins
        result.update(shifted_scaled_sum_source_pins())
    if identifier == "CV044":
        from sqrt2_power_cauchy_grid import cauchy_grid_source_pins
        result.update(cauchy_grid_source_pins())
    if identifier == "CV045":
        from sqrt2_power_cauchy_row_sum import cauchy_row_sum_source_pins
        result.update(cauchy_row_sum_source_pins())
    if identifier == "CV046":
        from sqrt2_power_cauchy_column_sum import cauchy_column_sum_source_pins
        result.update(cauchy_column_sum_source_pins())
    if identifier == "CV047":
        from sqrt2_power_cauchy_grid_sums import cauchy_grid_sums_source_pins
        result.update(cauchy_grid_sums_source_pins())
    if identifier == "CV048":
        from sqrt2_power_convolution_total import convolution_total_source_pins
        result.update(convolution_total_source_pins())
    if identifier == "CV049":
        from sqrt2_power_horner_product import horner_product_source_pins
        result.update(horner_product_source_pins())
    if identifier == "CV050":
        from sqrt2_power_convolution_locality import convolution_locality_source_pins
        result.update(convolution_locality_source_pins())
    if identifier == "CV051":
        from sqrt2_power_power_width_transport import power_width_transport_source_pins
        result.update(power_width_transport_source_pins())
    if identifier == "CV052":
        from sqrt2_power_composition_width_transport import composition_width_transport_source_pins
        result.update(composition_width_transport_source_pins())
    if identifier == "CV053":
        from sqrt2_power_convolution_upper_support import convolution_upper_support_source_pins
        result.update(convolution_upper_support_source_pins())
    if identifier == "CV054":
        from sqrt2_power_power_upper_support import power_upper_support_source_pins
        result.update(power_upper_support_source_pins())
    if identifier == "CV055":
        from sqrt2_power_horner_prefix_transport import horner_prefix_transport_source_pins
        result.update(horner_prefix_transport_source_pins())
    if identifier == "CV056":
        from sqrt2_power_supported_horner_product import supported_horner_product_source_pins
        result.update(supported_horner_product_source_pins())
    if identifier == "CV057":
        from sqrt2_power_supported_horner_values import supported_horner_values_source_pins
        result.update(supported_horner_values_source_pins())
    if identifier == "CV058":
        from sqrt2_power_finite_power_evaluation import finite_power_evaluation_source_pins
        result.update(finite_power_evaluation_source_pins())
    if identifier == "CV059":
        from sqrt2_power_row_horner_values import row_horner_values_source_pins
        result.update(row_horner_values_source_pins())
    if identifier == "CV060":
        from sqrt2_power_weighted_accumulation_evaluation import weighted_accumulation_evaluation_source_pins
        result.update(weighted_accumulation_evaluation_source_pins())
    if identifier == "CV061":
        from sqrt2_power_full_composition_evaluation import full_composition_evaluation_source_pins
        result.update(full_composition_evaluation_source_pins())
    if identifier == "CV062":
        from sqrt2_power_horner_splitting import horner_splitting_source_pins
        result.update(horner_splitting_source_pins())
    if identifier == "CV063":
        from sqrt2_power_horner_base_comparison import horner_base_comparison_source_pins
        result.update(horner_base_comparison_source_pins())
    if identifier == "CV064":
        from sqrt2_power_horner_tail_majorant import horner_tail_majorant_source_pins
        result.update(horner_tail_majorant_source_pins())
    if identifier == "CV065":
        from sqrt2_power_bounded_horner import bounded_horner_source_pins
        result.update(bounded_horner_source_pins())
    if identifier == "CV066":
        from sqrt2_power_atanh_majorant import atanh_majorant_source_pins
        result.update(atanh_majorant_source_pins())
    if identifier == "CV067":
        from sqrt2_power_factorial_majorant import factorial_majorant_source_pins
        result.update(factorial_majorant_source_pins())
    if identifier == "CV068":
        from sqrt2_power_ratio_sum_bound import ratio_sum_bound_source_pins
        result.update(ratio_sum_bound_source_pins())
    if identifier == "CV069":
        from sqrt2_power_power_weighted_prefix import power_weighted_prefix_source_pins
        result.update(power_weighted_prefix_source_pins())
    if identifier == "CV070":
        from sqrt2_power_scaled_exp_terms import scaled_exp_terms_source_pins
        result.update(scaled_exp_terms_source_pins())
    if identifier == "CV071":
        from sqrt2_power_scaled_exp_bound import scaled_exp_bound_source_pins
        result.update(scaled_exp_bound_source_pins())
    if identifier == "CV072":
        from sqrt2_power_monomial_recurrence import monomial_recurrence_source_pins
        result.update(monomial_recurrence_source_pins())
    if identifier == "CV073":
        from sqrt2_power_weighted_monomial_recurrence import weighted_monomial_recurrence_source_pins
        result.update(weighted_monomial_recurrence_source_pins())
    if identifier == "CV074":
        from sqrt2_power_composition_majorant import composition_majorant_source_pins
        result.update(composition_majorant_source_pins())
    if identifier == "CV075":
        from sqrt2_power_rational_tail_majorant import rational_tail_majorant_source_pins
        result.update(rational_tail_majorant_source_pins())
    if identifier == "CV076":
        from sqrt2_power_composition_tail_bound import composition_tail_bound_source_pins
        result.update(composition_tail_bound_source_pins())
    if identifier == "CV077":
        from sqrt2_power_supplied_composition_bound import supplied_composition_bound_source_pins
        result.update(supplied_composition_bound_source_pins())
    if identifier == "CV078":
        from sqrt2_power_consumed_row_transport import consumed_row_transport_source_pins
        result.update(consumed_row_transport_source_pins())
    if identifier == "CV079":
        from sqrt2_power_successor_composition_transport import successor_composition_transport_source_pins
        result.update(successor_composition_transport_source_pins())
    if identifier == "CV080":
        from sqrt2_power_same_table_composition import same_table_composition_source_pins
        result.update(same_table_composition_source_pins())
    if identifier == "CV081":
        from sqrt2_power_supplied_composition_evaluation import supplied_composition_evaluation_source_pins
        result.update(supplied_composition_evaluation_source_pins())
    if identifier == "CV082":
        from sqrt2_power_supplied_horner_splitting import supplied_horner_splitting_source_pins
        result.update(supplied_horner_splitting_source_pins())
    if identifier == "CV083":
        from sqrt2_power_geometric_tail_sandwich import geometric_tail_sandwich_source_pins
        result.update(geometric_tail_sandwich_source_pins())
    if identifier == "CV084":
        from sqrt2_power_supplied_geometric_error import supplied_geometric_error_source_pins
        result.update(supplied_geometric_error_source_pins())
    if identifier == "CV085":
        from sqrt2_power_constructed_composition_error import constructed_composition_error_source_pins
        result.update(constructed_composition_error_source_pins())
    if identifier == "CV086":
        from sqrt2_power_ternary_atanh_bound import ternary_atanh_bound_source_pins
        result.update(ternary_atanh_bound_source_pins())
    if identifier == "CV087":
        from sqrt2_power_scaled_exp_tail import scaled_exp_tail_source_pins
        result.update(scaled_exp_tail_source_pins())
    if identifier == "CV088":
        from sqrt2_power_scaled_exp_tail_decay import scaled_exp_tail_decay_source_pins
        result.update(scaled_exp_tail_decay_source_pins())
    if identifier == "CV089":
        from sqrt2_power_ternary_prefix_bound import ternary_prefix_bound_source_pins
        result.update(ternary_prefix_bound_source_pins())
    if identifier == "CV090":
        from sqrt2_power_atanh_truncation import atanh_truncation_source_pins
        result.update(atanh_truncation_source_pins())
    if identifier == "CV091":
        from sqrt2_power_atanh_rational_truncation import atanh_rational_truncation_source_pins
        result.update(atanh_rational_truncation_source_pins())
    if identifier == "CV092":
        from sqrt2_power_atanh_scale_independence import atanh_scale_independence_source_pins
        result.update(atanh_scale_independence_source_pins())
    if identifier == "CV093":
        from sqrt2_power_independent_atanh_truncation import independent_atanh_truncation_source_pins
        result.update(independent_atanh_truncation_source_pins())
    if identifier == "CV094":
        from sqrt2_power_exp_term_difference import exp_term_difference_source_pins
        result.update(exp_term_difference_source_pins())
    if identifier == "CV095":
        from sqrt2_power_sum_linear_bound import sum_linear_bound_source_pins
        result.update(sum_linear_bound_source_pins())
    if identifier == "CV096":
        from sqrt2_power_exp_sum_continuity import exp_sum_continuity_source_pins
        result.update(exp_sum_continuity_source_pins())
    if identifier == "CV097":
        from sqrt2_power_exp_rescaling import exp_rescaling_source_pins
        result.update(exp_rescaling_source_pins())
    if identifier == "CV098":
        from sqrt2_power_exp_cross_continuity import exp_cross_continuity_source_pins
        result.update(exp_cross_continuity_source_pins())
    if identifier == "CV099":
        from sqrt2_power_exp_rational_continuity import exp_rational_continuity_source_pins
        result.update(exp_rational_continuity_source_pins())
    if identifier == "CV100":
        from sqrt2_power_exp_truncation import exp_truncation_source_pins
        result.update(exp_truncation_source_pins())
    if identifier == "CV101":
        from sqrt2_power_exp_two_error_bound import exp_two_error_bound_source_pins
        result.update(exp_two_error_bound_source_pins())
    if identifier == "CV102":
        from sqrt2_power_exp_rational_two_error import exp_rational_two_error_source_pins
        result.update(exp_rational_two_error_source_pins())
    if identifier == "SQ001":
        from sqrt2_power_floor_sqrt import floor_sqrt_source_pins
        result.update(floor_sqrt_source_pins())
    if identifier == "SQ002":
        from sqrt2_power_floor_sqrt_comparison import floor_sqrt_comparison_source_pins
        result.update(floor_sqrt_comparison_source_pins())
    if identifier == "SQ003":
        from sqrt2_power_scaled_sqrt2 import scaled_sqrt2_source_pins
        result.update(scaled_sqrt2_source_pins())
    if identifier == "SQ004":
        from sqrt2_power_dyadic_sqrt2 import dyadic_sqrt2_source_pins
        result.update(dyadic_sqrt2_source_pins())
    if identifier == "SQ005":
        from sqrt2_power_floor_sqrt_scaling import floor_sqrt_scaling_source_pins
        result.update(floor_sqrt_scaling_source_pins())
    if identifier == "SQ006":
        from sqrt2_power_dyadic_sqrt2_refinement import dyadic_sqrt2_refinement_source_pins
        result.update(dyadic_sqrt2_refinement_source_pins())
    if identifier == "SQ007":
        from sqrt2_power_dyadic_sqrt2_intervals import dyadic_sqrt2_intervals_source_pins
        result.update(dyadic_sqrt2_intervals_source_pins())
    if identifier == "SQ008":
        from sqrt2_power_dyadic_sqrt2_modulus import dyadic_sqrt2_modulus_source_pins
        result.update(dyadic_sqrt2_modulus_source_pins())
    if identifier == "SQ009":
        from sqrt2_power_dyadic_sqrt2_square_error import dyadic_sqrt2_square_error_source_pins
        result.update(dyadic_sqrt2_square_error_source_pins())
    if identifier == "SQ010":
        from sqrt2_power_dyadic_sqrt2_reciprocal import dyadic_sqrt2_reciprocal_source_pins
        result.update(dyadic_sqrt2_reciprocal_source_pins())
    if identifier == "AP001":
        from sqrt2_power_log_root_argument import log_root_argument_source_pins
        result.update(log_root_argument_source_pins())
    if identifier == "AP002":
        from sqrt2_power_exp_sample import exp_sample_source_pins
        result.update(exp_sample_source_pins())
    if identifier == "AP003":
        from sqrt2_power_log_root_independence import log_root_independence_source_pins
        result.update(log_root_independence_source_pins())
    if identifier == "AP004":
        from sqrt2_power_supplied_exp_sample import supplied_exp_sample_source_pins
        result.update(supplied_exp_sample_source_pins())
    if identifier == "AP005":
        from sqrt2_power_exp_sample_independence import exp_sample_independence_source_pins
        result.update(exp_sample_independence_source_pins())
    if identifier == "AP006":
        from sqrt2_power_argument_modulus import argument_modulus_source_pins
        result.update(argument_modulus_source_pins())
    if identifier == "AP007":
        from sqrt2_power_exp_two_sided_continuity import exp_two_sided_continuity_source_pins
        result.update(exp_two_sided_continuity_source_pins())
    if identifier == "AP008":
        from sqrt2_power_exp_two_sided_horizons import exp_two_sided_horizons_source_pins
        result.update(exp_two_sided_horizons_source_pins())
    if identifier == "AP009":
        from sqrt2_power_exp_sample_modulus import exp_sample_modulus_source_pins
        result.update(exp_sample_modulus_source_pins())
    if identifier == "AP010":
        from sqrt2_power_positive_power_comparison import positive_power_comparison_source_pins
        result.update(positive_power_comparison_source_pins())
    if identifier == "AP011":
        from sqrt2_power_approximation_power_bounds import approximation_power_bounds_source_pins
        result.update(approximation_power_bounds_source_pins())
    if identifier == "AP012":
        from sqrt2_power_exp_sample_uniform_error import exp_sample_uniform_error_source_pins
        result.update(exp_sample_uniform_error_source_pins())
    if identifier == "AP013":
        from sqrt2_power_exp_sample_all_precision import exp_sample_all_precision_source_pins
        result.update(exp_sample_all_precision_source_pins())
    if identifier == "AP014":
        from sqrt2_power_fixed_precision_threshold import fixed_precision_threshold_source_pins
        result.update(fixed_precision_threshold_source_pins())
    if identifier == "AP015":
        from sqrt2_power_exp_sample_dyadic_error import exp_sample_dyadic_error_source_pins
        result.update(exp_sample_dyadic_error_source_pins())
    if identifier == "AP016":
        from sqrt2_power_atanh_odd_slice import atanh_odd_slice_source_pins
        result.update(atanh_odd_slice_source_pins())
    if identifier == "AP017":
        from sqrt2_power_paired_horner import paired_horner_source_pins
        result.update(paired_horner_source_pins())
    if identifier == "AP018":
        from sqrt2_power_paired_power import paired_power_source_pins
        result.update(paired_power_source_pins())
    if identifier == "AP019":
        from sqrt2_power_odd_horner_quotient import odd_horner_quotient_source_pins
        result.update(odd_horner_quotient_source_pins())
    if identifier == "AP020":
        from sqrt2_power_finite_odd_log_series import finite_odd_log_series_source_pins
        result.update(finite_odd_log_series_source_pins())
    if identifier == "AP021":
        from sqrt2_power_finite_exp_series import finite_exp_series_source_pins
        result.update(finite_exp_series_source_pins())
    if identifier == "AP022":
        from sqrt2_power_factorial_atanh_prefix import factorial_atanh_prefix_source_pins
        result.update(factorial_atanh_prefix_source_pins())
    if identifier == "AP023":
        from sqrt2_power_factorial_exp_sample import factorial_exp_sample_source_pins
        result.update(factorial_exp_sample_source_pins())
    if identifier == "AP024":
        from sqrt2_power_atomic_computation_decisions import atomic_computation_decisions_source_pins
        result.update(atomic_computation_decisions_source_pins())
    if identifier == "AP025":
        from sqrt2_power_approximation_component_decisions import approximation_component_decisions_source_pins
        result.update(approximation_component_decisions_source_pins())
    if identifier == "AP026":
        from sqrt2_power_finite_table_decisions import finite_table_decisions_source_pins
        result.update(finite_table_decisions_source_pins())
    if identifier == "AP027":
        from sqrt2_power_prescribed_sample_decision import prescribed_sample_decision_source_pins
        result.update(prescribed_sample_decision_source_pins())
    if identifier == "AP028":
        from sqrt2_power_approximation_record_exists import approximation_record_exists_source_pins
        result.update(approximation_record_exists_source_pins())
    if identifier == "AP029":
        from sqrt2_power_approximation_record_decision import approximation_record_decision_source_pins
        result.update(approximation_record_decision_source_pins())
    if identifier == "AP030":
        from sqrt2_power_approximation_record_independence import approximation_record_independence_source_pins
        result.update(approximation_record_independence_source_pins())
    if identifier == "AP031":
        from sqrt2_power_approximation_record_error import approximation_record_error_source_pins
        result.update(approximation_record_error_source_pins())
    if identifier == "AP032":
        from sqrt2_power_log_exp_witness import log_exp_witness_source_pins
        result.update(log_exp_witness_source_pins())
    if identifier == "AP033":
        from sqrt2_power_log_exp_budget import log_exp_budget_source_pins
        result.update(log_exp_budget_source_pins())
    if identifier == "AP034":
        from sqrt2_power_log_exp_dyadic_witness import log_exp_dyadic_witness_source_pins
        result.update(log_exp_dyadic_witness_source_pins())
    if identifier == "AP035":
        from sqrt2_power_exp_recurrence_normalization import exp_recurrence_normalization_source_pins
        result.update(exp_recurrence_normalization_source_pins())
    if identifier == "AP036":
        from sqrt2_power_exp_recurrence_series import exp_recurrence_series_source_pins
        result.update(exp_recurrence_series_source_pins())
    if identifier == "AP037":
        from sqrt2_power_convolution_shift import convolution_shift_source_pins
        result.update(convolution_shift_source_pins())
    if identifier == "AP038":
        from sqrt2_power_exp_convolution_recurrence import exp_convolution_recurrence_source_pins
        result.update(exp_convolution_recurrence_source_pins())
    if identifier == "AP039":
        from sqrt2_power_exp_convolution_prefix import exp_convolution_prefix_source_pins
        result.update(exp_convolution_prefix_source_pins())
    if identifier == "AP040":
        from sqrt2_power_convolution_prefix_order import convolution_prefix_order_source_pins
        result.update(convolution_prefix_order_source_pins())
    if identifier == "AP041":
        from sqrt2_power_convolution_sum_sandwich import convolution_sum_sandwich_source_pins
        result.update(convolution_sum_sandwich_source_pins())
    if identifier == "AP042":
        from sqrt2_power_exp_product_error import exp_product_error_source_pins
        result.update(exp_product_error_source_pins())
    if identifier == "AP043":
        from sqrt2_power_exp_supplied_product import exp_supplied_product_source_pins
        result.update(exp_supplied_product_source_pins())
    if identifier == "AP044":
        from sqrt2_power_exp_half_square import exp_half_square_source_pins
        result.update(exp_half_square_source_pins())
    if identifier == "AP045":
        from sqrt2_power_half_square_error_transfer import half_square_error_transfer_source_pins
        result.update(half_square_error_transfer_source_pins())
    if identifier == "AP046":
        from sqrt2_power_half_log_precision import half_log_precision_source_pins
        result.update(half_log_precision_source_pins())
    if identifier == "AP047":
        from sqrt2_power_half_log_square import half_log_square_source_pins
        result.update(half_log_square_source_pins())
    if identifier == "AP048":
        from sqrt2_power_square_error_linear import square_error_linear_source_pins
        result.update(square_error_linear_source_pins())
    if identifier == "AP049":
        from sqrt2_power_half_log_root_comparison import half_log_root_comparison_source_pins
        result.update(half_log_root_comparison_source_pins())
    if identifier == "AP050":
        from sqrt2_power_half_log_root_witness import half_log_root_witness_source_pins
        result.update(half_log_root_witness_source_pins())
    if identifier == "AP051":
        from sqrt2_power_exp_large_argument_ratio import exp_large_argument_ratio_source_pins
        result.update(exp_large_argument_ratio_source_pins())
    if identifier == "AP052":
        from sqrt2_power_exp_large_argument_tail import exp_large_argument_tail_source_pins
        result.update(exp_large_argument_tail_source_pins())
    if identifier == "AP053":
        from sqrt2_power_halving_prefix_decay import halving_prefix_decay_source_pins
        result.update(halving_prefix_decay_source_pins())
    if identifier == "AP054":
        from sqrt2_power_exp_large_argument_decay import exp_large_argument_decay_source_pins
        result.update(exp_large_argument_decay_source_pins())
    if identifier == "AP055":
        from sqrt2_power_exp_large_argument_truncation import exp_large_argument_truncation_source_pins
        result.update(exp_large_argument_truncation_source_pins())
    if identifier == "AP056":
        from sqrt2_power_exp_geometric_majorant import exp_geometric_majorant_source_pins
        result.update(exp_geometric_majorant_source_pins())
    if identifier == "AP057":
        from sqrt2_power_exp_normalized_truncation import exp_normalized_truncation_source_pins
        result.update(exp_normalized_truncation_source_pins())
    if identifier == "AP058":
        from sqrt2_power_exp_normalized_witness import exp_normalized_witness_source_pins
        result.update(exp_normalized_witness_source_pins())
    if identifier == "AP059":
        from sqrt2_power_exp_large_argument_product import exp_large_argument_product_source_pins
        result.update(exp_large_argument_product_source_pins())
    if identifier == "AP060":
        from sqrt2_power_exp_recurrence_independence import exp_recurrence_independence_source_pins
        result.update(exp_recurrence_independence_source_pins())
    if identifier == "AP061":
        from sqrt2_power_exp_supplied_large_product import exp_supplied_large_product_source_pins
        result.update(exp_supplied_large_product_source_pins())
    if identifier == "AP062":
        from sqrt2_power_exp_binary_budget import exp_binary_budget_source_pins
        result.update(exp_binary_budget_source_pins())
    if identifier == "AP063":
        from sqrt2_power_exp_requested_truncation import exp_requested_truncation_source_pins
        result.update(exp_requested_truncation_source_pins())
    if identifier == "AP064":
        from sqrt2_power_exp_requested_product import exp_requested_product_source_pins
        result.update(exp_requested_product_source_pins())
    if identifier == "AP065":
        from sqrt2_power_exp_independent_horizon import exp_independent_horizon_source_pins
        result.update(exp_independent_horizon_source_pins())
    if identifier == "AP066":
        from sqrt2_power_exp_uniform_witness import exp_uniform_witness_source_pins
        result.update(exp_uniform_witness_source_pins())
    if identifier == "AP067":
        from sqrt2_power_exp_product_witness import exp_product_witness_source_pins
        result.update(exp_product_witness_source_pins())
    if identifier == "AP068":
        from sqrt2_power_exp_relative_continuity import exp_relative_continuity_source_pins
        result.update(exp_relative_continuity_source_pins())
    if identifier == "AP069":
        from sqrt2_power_exp_relative_cross_continuity import exp_relative_cross_continuity_source_pins
        result.update(exp_relative_cross_continuity_source_pins())
    if identifier == "AP070":
        from sqrt2_power_exp_absolute_continuity import exp_absolute_continuity_source_pins
        result.update(exp_absolute_continuity_source_pins())
    if identifier == "AP071":
        from sqrt2_power_exp_submultiplicative import exp_submultiplicative_source_pins
        result.update(exp_submultiplicative_source_pins())
    if identifier == "AP072":
        from sqrt2_power_exp_integer_majorant import exp_integer_majorant_source_pins
        result.update(exp_integer_majorant_source_pins())
    if identifier == "AP073":
        from sqrt2_power_exp_bounded_majorant import exp_bounded_majorant_source_pins
        result.update(exp_bounded_majorant_source_pins())
    if identifier == "AP074":
        from sqrt2_power_exp_bounded_continuity import exp_bounded_continuity_source_pins
        result.update(exp_bounded_continuity_source_pins())
    if identifier == "AP075":
        from sqrt2_power_exp_dyadic_continuity import exp_dyadic_continuity_source_pins
        result.update(exp_dyadic_continuity_source_pins())
    if identifier == "AP076":
        from sqrt2_power_ordered_power_difference import ordered_power_difference_source_pins
        result.update(ordered_power_difference_source_pins())
    if identifier == "AP077":
        from sqrt2_power_symmetric_power_difference import symmetric_power_difference_source_pins
        result.update(symmetric_power_difference_source_pins())
    if identifier == "AP078":
        from sqrt2_power_product_power import product_power_source_pins
        result.update(product_power_source_pins())
    if identifier == "AP079":
        from sqrt2_power_rational_power_difference import rational_power_difference_source_pins
        result.update(rational_power_difference_source_pins())
    if identifier == "AP080":
        from sqrt2_power_requested_power_precision import requested_power_precision_source_pins
        result.update(requested_power_precision_source_pins())
    if identifier == "AP081":
        from sqrt2_power_exp_joint_error import exp_joint_error_source_pins
        result.update(exp_joint_error_source_pins())
    if identifier == "AP082":
        from sqrt2_power_log_exp_refinement import log_exp_refinement_source_pins
        result.update(log_exp_refinement_source_pins())
    if identifier == "AP083":
        from sqrt2_power_log_exp_cutoff_refinement import log_exp_cutoff_refinement_source_pins
        result.update(log_exp_cutoff_refinement_source_pins())
    if identifier == "AP084":
        from sqrt2_power_log_exp_uniform_two import log_exp_uniform_two_source_pins
        result.update(log_exp_uniform_two_source_pins())
    if identifier == "AP085":
        from sqrt2_power_fixed_log_exp_convergence import fixed_log_exp_convergence_source_pins
        result.update(fixed_log_exp_convergence_source_pins())
    if identifier == "AP086":
        from sqrt2_power_fixed_log_exp_witness import fixed_log_exp_witness_source_pins
        result.update(fixed_log_exp_witness_source_pins())
    if identifier == "AP087":
        from sqrt2_power_half_log_exp_refinement import half_log_exp_refinement_source_pins
        result.update(half_log_exp_refinement_source_pins())
    if identifier == "AP088":
        from sqrt2_power_half_log_exp_cutoff import half_log_exp_cutoff_source_pins
        result.update(half_log_exp_cutoff_source_pins())
    if identifier == "AP089":
        from sqrt2_power_half_log_root_uniform import half_log_root_uniform_source_pins
        result.update(half_log_root_uniform_source_pins())
    if identifier == "AP090":
        from sqrt2_power_fixed_half_log_root import fixed_half_log_root_source_pins
        result.update(fixed_half_log_root_source_pins())
    if identifier == "AP091":
        from sqrt2_power_fixed_half_log_root_witness import fixed_half_log_root_witness_source_pins
        result.update(fixed_half_log_root_witness_source_pins())
    if identifier == "AP092":
        from sqrt2_power_fixed_half_log_fine_root import fixed_half_log_fine_root_source_pins
        result.update(fixed_half_log_fine_root_source_pins())
    if identifier == "AP093":
        from sqrt2_power_log_root_half_argument import log_root_half_argument_source_pins
        result.update(log_root_half_argument_source_pins())
    if identifier == "AP094":
        from sqrt2_power_exp_log_root_half_transport import exp_log_root_half_transport_source_pins
        result.update(exp_log_root_half_transport_source_pins())
    if identifier == "AP095":
        from sqrt2_power_requested_half_transport import requested_half_transport_source_pins
        result.update(requested_half_transport_source_pins())
    if identifier == "RN002":
        from sqrt2_power_rational_norm_product import rational_norm_product_source_pins
        result.update(rational_norm_product_source_pins())
    if identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import signed_product_nonzero_source_pins
        result.update(signed_product_nonzero_source_pins())
    if identifier == "RN001":
        from sqrt2_power_rational_norm_transport import rational_norm_transport_source_pins
        result.update(rational_norm_transport_source_pins())
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import quadratic_nonzero_source_pins
        result.update(quadratic_nonzero_source_pins())
    if identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import quadratic_product_trace_source_pins
        result.update(quadratic_product_trace_source_pins())
    if identifier == "QF002":
        from sqrt2_power_quadratic_trace_exists import quadratic_trace_exists_source_pins
        result.update(quadratic_trace_exists_source_pins())
    if identifier == "QF003":
        from sqrt2_power_quadratic_product_exists import quadratic_product_exists_source_pins
        result.update(quadratic_product_exists_source_pins())
    if identifier == "QH001":
        from sqrt2_power_quadratic_height import quadratic_height_source_pins
        result.update(quadratic_height_source_pins())
    if identifier == "QF004":
        from sqrt2_power_canonical_quadratic_trace import canonical_quadratic_trace_source_pins
        result.update(canonical_quadratic_trace_source_pins())
    if identifier == "QH002":
        from sqrt2_power_quadratic_trace_height import quadratic_trace_height_source_pins
        result.update(quadratic_trace_height_source_pins())
    if identifier == "QF005":
        from sqrt2_power_bounded_quadratic_product import bounded_quadratic_product_source_pins
        result.update(bounded_quadratic_product_source_pins())
    return result


def target_for(identifier):
    if type(identifier) is not str or identifier not in CASES:
        raise ValueError("unknown exact wave target")
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import frozen_quadratic_nonzero_target
        return frozen_quadratic_nonzero_target()
    if identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import frozen_quadratic_product_trace_target
        return frozen_quadratic_product_trace_target()
    if identifier == "QF002":
        from sqrt2_power_quadratic_trace_exists import frozen_quadratic_trace_exists_target
        return frozen_quadratic_trace_exists_target()
    if identifier == "QF003":
        from sqrt2_power_quadratic_product_exists import frozen_quadratic_product_exists_target
        return frozen_quadratic_product_exists_target()
    if identifier == "QH001":
        from sqrt2_power_quadratic_height import frozen_quadratic_height_target
        return frozen_quadratic_height_target()
    if identifier == "QF004":
        from sqrt2_power_canonical_quadratic_trace import frozen_canonical_quadratic_trace_target
        return frozen_canonical_quadratic_trace_target()
    if identifier == "QH002":
        from sqrt2_power_quadratic_trace_height import frozen_quadratic_trace_height_target
        return frozen_quadratic_trace_height_target()
    if identifier == "QF005":
        from sqrt2_power_bounded_quadratic_product import frozen_bounded_quadratic_product_target
        return frozen_bounded_quadratic_product_target()
    if identifier == "RN001":
        from sqrt2_power_rational_norm_transport import frozen_rational_norm_transport_target
        return frozen_rational_norm_transport_target()
    if identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import frozen_signed_product_nonzero_target
        return frozen_signed_product_nonzero_target()
    if identifier == "RN002":
        from sqrt2_power_rational_norm_product import frozen_rational_norm_product_target
        return frozen_rational_norm_product_target()
    if identifier == "CV001":
        from sqrt2_power_convolution_vanishing import frozen_convolution_vanishing_target
        return frozen_convolution_vanishing_target()
    if identifier == "CV002":
        from sqrt2_power_logexp_recurrence import frozen_logexp_recurrence_target
        return frozen_logexp_recurrence_target()
    if identifier == "CV003":
        from sqrt2_power_natural_convolution import frozen_natural_convolution_target
        return frozen_natural_convolution_target()
    if identifier == "CV004":
        from sqrt2_power_series_power_trace import frozen_series_power_trace_target
        return frozen_series_power_trace_target()
    if identifier == "CV005":
        from sqrt2_power_series_power_vanishing import frozen_series_power_vanishing_target
        return frozen_series_power_vanishing_target()
    if identifier == "CV006":
        from sqrt2_power_sum_linearity import frozen_sum_linearity_target
        return frozen_sum_linearity_target()
    if identifier == "CV007":
        from sqrt2_power_euler_product import frozen_euler_product_target
        return frozen_euler_product_target()
    if identifier == "CV008":
        from sqrt2_power_natural_fubini import frozen_natural_fubini_target
        return frozen_natural_fubini_target()
    if identifier == "CV009":
        from sqrt2_power_sum_splitting import frozen_sum_splitting_target
        return frozen_sum_splitting_target()
    if identifier == "CV010":
        from sqrt2_power_convolution_commutative import frozen_convolution_commutative_target
        return frozen_convolution_commutative_target()
    if identifier == "CV011":
        from sqrt2_power_sum_zero_tail import frozen_sum_zero_tail_target
        return frozen_sum_zero_tail_target()
    if identifier == "CV012":
        from sqrt2_power_triple_grid import frozen_triple_grid_target
        return frozen_triple_grid_target()
    if identifier == "CV013":
        from sqrt2_power_triple_row_sum import frozen_triple_row_sum_target
        return frozen_triple_row_sum_target()
    if identifier == "CV014":
        from sqrt2_power_convolution_associative import frozen_convolution_associative_target
        return frozen_convolution_associative_target()
    if identifier == "CV015":
        from sqrt2_power_convolution_linearity import frozen_convolution_linearity_target
        return frozen_convolution_linearity_target()
    if identifier == "CV016":
        from sqrt2_power_convolution_unit import frozen_convolution_unit_target
        return frozen_convolution_unit_target()
    if identifier == "CV017":
        from sqrt2_power_series_power_euler import frozen_series_power_euler_target
        return frozen_series_power_euler_target()
    if identifier == "CV018":
        from sqrt2_power_series_linear_combination import frozen_series_linear_combination_target
        return frozen_series_linear_combination_target()
    if identifier == "CV019":
        from sqrt2_power_weighted_series_trace import frozen_weighted_series_trace_target
        return frozen_weighted_series_trace_target()
    if identifier == "CV020":
        from sqrt2_power_shifted_euler_prefix import frozen_shifted_euler_prefix_target
        return frozen_shifted_euler_prefix_target()
    if identifier == "CV021":
        from sqrt2_power_finite_composition_euler import frozen_finite_composition_euler_target
        return frozen_finite_composition_euler_target()
    if identifier == "CV022":
        from sqrt2_power_exponential_weights import frozen_exponential_weights_target
        return frozen_exponential_weights_target()
    if identifier == "CV023":
        from sqrt2_power_weighted_series_scaling import frozen_weighted_series_scaling_target
        return frozen_weighted_series_scaling_target()
    if identifier == "CV024":
        from sqrt2_power_denominator_euler import frozen_denominator_euler_target
        return frozen_denominator_euler_target()
    if identifier == "CV025":
        from sqrt2_power_atanh_coefficients import frozen_atanh_coefficients_target
        return frozen_atanh_coefficients_target()
    if identifier == "CV026":
        from sqrt2_power_atanh_euler import frozen_atanh_euler_target
        return frozen_atanh_euler_target()
    if identifier == "CV027":
        from sqrt2_power_periodic_convolution import frozen_periodic_convolution_target
        return frozen_periodic_convolution_target()
    if identifier == "CV028":
        from sqrt2_power_composition_recurrence import frozen_composition_recurrence_target
        return frozen_composition_recurrence_target()
    if identifier == "CV029":
        from sqrt2_power_composition_coefficients import frozen_composition_coefficients_target
        return frozen_composition_coefficients_target()
    if identifier == "CV030":
        from sqrt2_power_weight_factorials import frozen_weight_factorials_target
        return frozen_weight_factorials_target()
    if identifier == "CV031":
        from sqrt2_power_normalized_composition import frozen_normalized_composition_target
        return frozen_normalized_composition_target()
    if identifier == "CV032":
        from sqrt2_power_horner_trace import frozen_horner_trace_target
        return frozen_horner_trace_target()
    if identifier == "CV033":
        from sqrt2_power_geometric_horner import frozen_geometric_horner_target
        return frozen_geometric_horner_target()
    if identifier == "CV034":
        from sqrt2_power_composition_evaluation import frozen_composition_evaluation_target
        return frozen_composition_evaluation_target()
    if identifier == "CV035":
        from sqrt2_power_horner_linearity import frozen_horner_linearity_target
        return frozen_horner_linearity_target()
    if identifier == "CV036":
        from sqrt2_power_horner_zero_tail import frozen_horner_zero_tail_target
        return frozen_horner_zero_tail_target()
    if identifier == "CV037":
        from sqrt2_power_horner_weighted_sum import frozen_horner_weighted_sum_target
        return frozen_horner_weighted_sum_target()
    if identifier == "CV038":
        from sqrt2_power_geometric_weights import frozen_geometric_weights_target
        return frozen_geometric_weights_target()
    if identifier == "CV039":
        from sqrt2_power_constructed_horner_sum import frozen_constructed_horner_sum_target
        return frozen_constructed_horner_sum_target()
    if identifier == "CV040":
        from sqrt2_power_horner_monomials import frozen_horner_monomials_target
        return frozen_horner_monomials_target()
    if identifier == "CV041":
        from sqrt2_power_convolution_weights import frozen_convolution_weights_target
        return frozen_convolution_weights_target()
    if identifier == "CV042":
        from sqrt2_power_weighted_convolution import frozen_weighted_convolution_target
        return frozen_weighted_convolution_target()
    if identifier == "CV043":
        from sqrt2_power_shifted_scaled_sum import frozen_shifted_scaled_sum_target
        return frozen_shifted_scaled_sum_target()
    if identifier == "CV044":
        from sqrt2_power_cauchy_grid import frozen_cauchy_grid_target
        return frozen_cauchy_grid_target()
    if identifier == "CV045":
        from sqrt2_power_cauchy_row_sum import frozen_cauchy_row_sum_target
        return frozen_cauchy_row_sum_target()
    if identifier == "CV046":
        from sqrt2_power_cauchy_column_sum import frozen_cauchy_column_sum_target
        return frozen_cauchy_column_sum_target()
    if identifier == "CV047":
        from sqrt2_power_cauchy_grid_sums import frozen_cauchy_grid_sums_target
        return frozen_cauchy_grid_sums_target()
    if identifier == "CV048":
        from sqrt2_power_convolution_total import frozen_convolution_total_target
        return frozen_convolution_total_target()
    if identifier == "CV049":
        from sqrt2_power_horner_product import frozen_horner_product_target
        return frozen_horner_product_target()
    if identifier == "CV050":
        from sqrt2_power_convolution_locality import frozen_convolution_locality_target
        return frozen_convolution_locality_target()
    if identifier == "CV051":
        from sqrt2_power_power_width_transport import frozen_power_width_transport_target
        return frozen_power_width_transport_target()
    if identifier == "CV052":
        from sqrt2_power_composition_width_transport import frozen_composition_width_transport_target
        return frozen_composition_width_transport_target()
    if identifier == "CV053":
        from sqrt2_power_convolution_upper_support import frozen_convolution_upper_support_target
        return frozen_convolution_upper_support_target()
    if identifier == "CV054":
        from sqrt2_power_power_upper_support import frozen_power_upper_support_target
        return frozen_power_upper_support_target()
    if identifier == "CV055":
        from sqrt2_power_horner_prefix_transport import frozen_horner_prefix_transport_target
        return frozen_horner_prefix_transport_target()
    if identifier == "CV056":
        from sqrt2_power_supported_horner_product import frozen_supported_horner_product_target
        return frozen_supported_horner_product_target()
    if identifier == "CV057":
        from sqrt2_power_supported_horner_values import frozen_supported_horner_values_target
        return frozen_supported_horner_values_target()
    if identifier == "CV058":
        from sqrt2_power_finite_power_evaluation import frozen_finite_power_evaluation_target
        return frozen_finite_power_evaluation_target()
    if identifier == "CV059":
        from sqrt2_power_row_horner_values import frozen_row_horner_values_target
        return frozen_row_horner_values_target()
    if identifier == "CV060":
        from sqrt2_power_weighted_accumulation_evaluation import frozen_weighted_accumulation_evaluation_target
        return frozen_weighted_accumulation_evaluation_target()
    if identifier == "CV061":
        from sqrt2_power_full_composition_evaluation import frozen_full_composition_evaluation_target
        return frozen_full_composition_evaluation_target()
    if identifier == "CV062":
        from sqrt2_power_horner_splitting import frozen_horner_splitting_target
        return frozen_horner_splitting_target()
    if identifier == "CV063":
        from sqrt2_power_horner_base_comparison import frozen_horner_base_comparison_target
        return frozen_horner_base_comparison_target()
    if identifier == "CV064":
        from sqrt2_power_horner_tail_majorant import frozen_horner_tail_majorant_target
        return frozen_horner_tail_majorant_target()
    if identifier == "CV065":
        from sqrt2_power_bounded_horner import frozen_bounded_horner_target
        return frozen_bounded_horner_target()
    if identifier == "CV066":
        from sqrt2_power_atanh_majorant import frozen_atanh_majorant_target
        return frozen_atanh_majorant_target()
    if identifier == "CV067":
        from sqrt2_power_factorial_majorant import frozen_factorial_majorant_target
        return frozen_factorial_majorant_target()
    if identifier == "CV068":
        from sqrt2_power_ratio_sum_bound import frozen_ratio_sum_bound_target
        return frozen_ratio_sum_bound_target()
    if identifier == "CV069":
        from sqrt2_power_power_weighted_prefix import frozen_power_weighted_prefix_target
        return frozen_power_weighted_prefix_target()
    if identifier == "CV070":
        from sqrt2_power_scaled_exp_terms import frozen_scaled_exp_terms_target
        return frozen_scaled_exp_terms_target()
    if identifier == "CV071":
        from sqrt2_power_scaled_exp_bound import frozen_scaled_exp_bound_target
        return frozen_scaled_exp_bound_target()
    if identifier == "CV072":
        from sqrt2_power_monomial_recurrence import frozen_monomial_recurrence_target
        return frozen_monomial_recurrence_target()
    if identifier == "CV073":
        from sqrt2_power_weighted_monomial_recurrence import frozen_weighted_monomial_recurrence_target
        return frozen_weighted_monomial_recurrence_target()
    if identifier == "CV074":
        from sqrt2_power_composition_majorant import frozen_composition_majorant_target
        return frozen_composition_majorant_target()
    if identifier == "CV075":
        from sqrt2_power_rational_tail_majorant import frozen_rational_tail_majorant_target
        return frozen_rational_tail_majorant_target()
    if identifier == "CV076":
        from sqrt2_power_composition_tail_bound import frozen_composition_tail_bound_target
        return frozen_composition_tail_bound_target()
    if identifier == "CV077":
        from sqrt2_power_supplied_composition_bound import frozen_supplied_composition_bound_target
        return frozen_supplied_composition_bound_target()
    if identifier == "CV078":
        from sqrt2_power_consumed_row_transport import frozen_consumed_row_transport_target
        return frozen_consumed_row_transport_target()
    if identifier == "CV079":
        from sqrt2_power_successor_composition_transport import frozen_successor_composition_transport_target
        return frozen_successor_composition_transport_target()
    if identifier == "CV080":
        from sqrt2_power_same_table_composition import frozen_same_table_composition_target
        return frozen_same_table_composition_target()
    if identifier == "CV081":
        from sqrt2_power_supplied_composition_evaluation import frozen_supplied_composition_evaluation_target
        return frozen_supplied_composition_evaluation_target()
    if identifier == "CV082":
        from sqrt2_power_supplied_horner_splitting import frozen_supplied_horner_splitting_target
        return frozen_supplied_horner_splitting_target()
    if identifier == "CV083":
        from sqrt2_power_geometric_tail_sandwich import frozen_geometric_tail_sandwich_target
        return frozen_geometric_tail_sandwich_target()
    if identifier == "CV084":
        from sqrt2_power_supplied_geometric_error import frozen_supplied_geometric_error_target
        return frozen_supplied_geometric_error_target()
    if identifier == "CV085":
        from sqrt2_power_constructed_composition_error import frozen_constructed_composition_error_target
        return frozen_constructed_composition_error_target()
    if identifier == "CV086":
        from sqrt2_power_ternary_atanh_bound import frozen_ternary_atanh_bound_target
        return frozen_ternary_atanh_bound_target()
    if identifier == "CV087":
        from sqrt2_power_scaled_exp_tail import frozen_scaled_exp_tail_target
        return frozen_scaled_exp_tail_target()
    if identifier == "CV088":
        from sqrt2_power_scaled_exp_tail_decay import frozen_scaled_exp_tail_decay_target
        return frozen_scaled_exp_tail_decay_target()
    if identifier == "CV089":
        from sqrt2_power_ternary_prefix_bound import frozen_ternary_prefix_bound_target
        return frozen_ternary_prefix_bound_target()
    if identifier == "CV090":
        from sqrt2_power_atanh_truncation import frozen_atanh_truncation_target
        return frozen_atanh_truncation_target()
    if identifier == "CV091":
        from sqrt2_power_atanh_rational_truncation import frozen_atanh_rational_truncation_target
        return frozen_atanh_rational_truncation_target()
    if identifier == "CV092":
        from sqrt2_power_atanh_scale_independence import frozen_atanh_scale_independence_target
        return frozen_atanh_scale_independence_target()
    if identifier == "CV093":
        from sqrt2_power_independent_atanh_truncation import frozen_independent_atanh_truncation_target
        return frozen_independent_atanh_truncation_target()
    if identifier == "CV094":
        from sqrt2_power_exp_term_difference import frozen_exp_term_difference_target
        return frozen_exp_term_difference_target()
    if identifier == "CV095":
        from sqrt2_power_sum_linear_bound import frozen_sum_linear_bound_target
        return frozen_sum_linear_bound_target()
    if identifier == "CV096":
        from sqrt2_power_exp_sum_continuity import frozen_exp_sum_continuity_target
        return frozen_exp_sum_continuity_target()
    if identifier == "CV097":
        from sqrt2_power_exp_rescaling import frozen_exp_rescaling_target
        return frozen_exp_rescaling_target()
    if identifier == "CV098":
        from sqrt2_power_exp_cross_continuity import frozen_exp_cross_continuity_target
        return frozen_exp_cross_continuity_target()
    if identifier == "CV099":
        from sqrt2_power_exp_rational_continuity import frozen_exp_rational_continuity_target
        return frozen_exp_rational_continuity_target()
    if identifier == "CV100":
        from sqrt2_power_exp_truncation import frozen_exp_truncation_target
        return frozen_exp_truncation_target()
    if identifier == "CV101":
        from sqrt2_power_exp_two_error_bound import frozen_exp_two_error_bound_target
        return frozen_exp_two_error_bound_target()
    if identifier == "CV102":
        from sqrt2_power_exp_rational_two_error import frozen_exp_rational_two_error_target
        return frozen_exp_rational_two_error_target()
    if identifier == "SQ001":
        from sqrt2_power_floor_sqrt import frozen_floor_sqrt_target
        return frozen_floor_sqrt_target()
    if identifier == "SQ002":
        from sqrt2_power_floor_sqrt_comparison import frozen_floor_sqrt_comparison_target
        return frozen_floor_sqrt_comparison_target()
    if identifier == "SQ003":
        from sqrt2_power_scaled_sqrt2 import frozen_scaled_sqrt2_target
        return frozen_scaled_sqrt2_target()
    if identifier == "SQ004":
        from sqrt2_power_dyadic_sqrt2 import frozen_dyadic_sqrt2_target
        return frozen_dyadic_sqrt2_target()
    if identifier == "SQ005":
        from sqrt2_power_floor_sqrt_scaling import frozen_floor_sqrt_scaling_target
        return frozen_floor_sqrt_scaling_target()
    if identifier == "SQ006":
        from sqrt2_power_dyadic_sqrt2_refinement import frozen_dyadic_sqrt2_refinement_target
        return frozen_dyadic_sqrt2_refinement_target()
    if identifier == "SQ007":
        from sqrt2_power_dyadic_sqrt2_intervals import frozen_dyadic_sqrt2_intervals_target
        return frozen_dyadic_sqrt2_intervals_target()
    if identifier == "SQ008":
        from sqrt2_power_dyadic_sqrt2_modulus import frozen_dyadic_sqrt2_modulus_target
        return frozen_dyadic_sqrt2_modulus_target()
    if identifier == "SQ009":
        from sqrt2_power_dyadic_sqrt2_square_error import frozen_dyadic_sqrt2_square_error_target
        return frozen_dyadic_sqrt2_square_error_target()
    if identifier == "SQ010":
        from sqrt2_power_dyadic_sqrt2_reciprocal import frozen_dyadic_sqrt2_reciprocal_target
        return frozen_dyadic_sqrt2_reciprocal_target()
    if identifier == "AP001":
        from sqrt2_power_log_root_argument import frozen_log_root_argument_target
        return frozen_log_root_argument_target()
    if identifier == "AP002":
        from sqrt2_power_exp_sample import frozen_exp_sample_target
        return frozen_exp_sample_target()
    if identifier == "AP003":
        from sqrt2_power_log_root_independence import frozen_log_root_independence_target
        return frozen_log_root_independence_target()
    if identifier == "AP004":
        from sqrt2_power_supplied_exp_sample import frozen_supplied_exp_sample_target
        return frozen_supplied_exp_sample_target()
    if identifier == "AP005":
        from sqrt2_power_exp_sample_independence import frozen_exp_sample_independence_target
        return frozen_exp_sample_independence_target()
    if identifier == "AP006":
        from sqrt2_power_argument_modulus import frozen_argument_modulus_target
        return frozen_argument_modulus_target()
    if identifier == "AP007":
        from sqrt2_power_exp_two_sided_continuity import frozen_exp_two_sided_continuity_target
        return frozen_exp_two_sided_continuity_target()
    if identifier == "AP008":
        from sqrt2_power_exp_two_sided_horizons import frozen_exp_two_sided_horizons_target
        return frozen_exp_two_sided_horizons_target()
    if identifier == "AP009":
        from sqrt2_power_exp_sample_modulus import frozen_exp_sample_modulus_target
        return frozen_exp_sample_modulus_target()
    if identifier == "AP010":
        from sqrt2_power_positive_power_comparison import frozen_positive_power_comparison_target
        return frozen_positive_power_comparison_target()
    if identifier == "AP011":
        from sqrt2_power_approximation_power_bounds import frozen_approximation_power_bounds_target
        return frozen_approximation_power_bounds_target()
    if identifier == "AP012":
        from sqrt2_power_exp_sample_uniform_error import frozen_exp_sample_uniform_error_target
        return frozen_exp_sample_uniform_error_target()
    if identifier == "AP013":
        from sqrt2_power_exp_sample_all_precision import frozen_exp_sample_all_precision_target
        return frozen_exp_sample_all_precision_target()
    if identifier == "AP014":
        from sqrt2_power_fixed_precision_threshold import frozen_fixed_precision_threshold_target
        return frozen_fixed_precision_threshold_target()
    if identifier == "AP015":
        from sqrt2_power_exp_sample_dyadic_error import frozen_exp_sample_dyadic_error_target
        return frozen_exp_sample_dyadic_error_target()
    if identifier == "AP016":
        from sqrt2_power_atanh_odd_slice import frozen_atanh_odd_slice_target
        return frozen_atanh_odd_slice_target()
    if identifier == "AP017":
        from sqrt2_power_paired_horner import frozen_paired_horner_target
        return frozen_paired_horner_target()
    if identifier == "AP018":
        from sqrt2_power_paired_power import frozen_paired_power_target
        return frozen_paired_power_target()
    if identifier == "AP019":
        from sqrt2_power_odd_horner_quotient import frozen_odd_horner_quotient_target
        return frozen_odd_horner_quotient_target()
    if identifier == "AP020":
        from sqrt2_power_finite_odd_log_series import frozen_finite_odd_log_series_target
        return frozen_finite_odd_log_series_target()
    if identifier == "AP021":
        from sqrt2_power_finite_exp_series import frozen_finite_exp_series_target
        return frozen_finite_exp_series_target()
    if identifier == "AP022":
        from sqrt2_power_factorial_atanh_prefix import frozen_factorial_atanh_prefix_target
        return frozen_factorial_atanh_prefix_target()
    if identifier == "AP023":
        from sqrt2_power_factorial_exp_sample import frozen_factorial_exp_sample_target
        return frozen_factorial_exp_sample_target()
    if identifier == "AP024":
        from sqrt2_power_atomic_computation_decisions import frozen_atomic_computation_decisions_target
        return frozen_atomic_computation_decisions_target()
    if identifier == "AP025":
        from sqrt2_power_approximation_component_decisions import frozen_approximation_component_decisions_target
        return frozen_approximation_component_decisions_target()
    if identifier == "AP026":
        from sqrt2_power_finite_table_decisions import frozen_finite_table_decisions_target
        return frozen_finite_table_decisions_target()
    if identifier == "AP027":
        from sqrt2_power_prescribed_sample_decision import frozen_prescribed_sample_decision_target
        return frozen_prescribed_sample_decision_target()
    if identifier == "AP028":
        from sqrt2_power_approximation_record_exists import frozen_approximation_record_exists_target
        return frozen_approximation_record_exists_target()
    if identifier == "AP029":
        from sqrt2_power_approximation_record_decision import frozen_approximation_record_decision_target
        return frozen_approximation_record_decision_target()
    if identifier == "AP030":
        from sqrt2_power_approximation_record_independence import frozen_approximation_record_independence_target
        return frozen_approximation_record_independence_target()
    if identifier == "AP031":
        from sqrt2_power_approximation_record_error import frozen_approximation_record_error_target
        return frozen_approximation_record_error_target()
    if identifier == "AP032":
        from sqrt2_power_log_exp_witness import frozen_log_exp_witness_target
        return frozen_log_exp_witness_target()
    if identifier == "AP033":
        from sqrt2_power_log_exp_budget import frozen_log_exp_budget_target
        return frozen_log_exp_budget_target()
    if identifier == "AP034":
        from sqrt2_power_log_exp_dyadic_witness import frozen_log_exp_dyadic_witness_target
        return frozen_log_exp_dyadic_witness_target()
    if identifier == "AP035":
        from sqrt2_power_exp_recurrence_normalization import frozen_exp_recurrence_normalization_target
        return frozen_exp_recurrence_normalization_target()
    if identifier == "AP036":
        from sqrt2_power_exp_recurrence_series import frozen_exp_recurrence_series_target
        return frozen_exp_recurrence_series_target()
    if identifier == "AP037":
        from sqrt2_power_convolution_shift import frozen_convolution_shift_target
        return frozen_convolution_shift_target()
    if identifier == "AP038":
        from sqrt2_power_exp_convolution_recurrence import frozen_exp_convolution_recurrence_target
        return frozen_exp_convolution_recurrence_target()
    if identifier == "AP039":
        from sqrt2_power_exp_convolution_prefix import frozen_exp_convolution_prefix_target
        return frozen_exp_convolution_prefix_target()
    if identifier == "AP040":
        from sqrt2_power_convolution_prefix_order import frozen_convolution_prefix_order_target
        return frozen_convolution_prefix_order_target()
    if identifier == "AP041":
        from sqrt2_power_convolution_sum_sandwich import frozen_convolution_sum_sandwich_target
        return frozen_convolution_sum_sandwich_target()
    if identifier == "AP042":
        from sqrt2_power_exp_product_error import frozen_exp_product_error_target
        return frozen_exp_product_error_target()
    if identifier == "AP043":
        from sqrt2_power_exp_supplied_product import frozen_exp_supplied_product_target
        return frozen_exp_supplied_product_target()
    if identifier == "AP044":
        from sqrt2_power_exp_half_square import frozen_exp_half_square_target
        return frozen_exp_half_square_target()
    if identifier == "AP045":
        from sqrt2_power_half_square_error_transfer import frozen_half_square_error_transfer_target
        return frozen_half_square_error_transfer_target()
    if identifier == "AP046":
        from sqrt2_power_half_log_precision import frozen_half_log_precision_target
        return frozen_half_log_precision_target()
    if identifier == "AP047":
        from sqrt2_power_half_log_square import frozen_half_log_square_target
        return frozen_half_log_square_target()
    if identifier == "AP048":
        from sqrt2_power_square_error_linear import frozen_square_error_linear_target
        return frozen_square_error_linear_target()
    if identifier == "AP049":
        from sqrt2_power_half_log_root_comparison import frozen_half_log_root_comparison_target
        return frozen_half_log_root_comparison_target()
    if identifier == "AP050":
        from sqrt2_power_half_log_root_witness import frozen_half_log_root_witness_target
        return frozen_half_log_root_witness_target()
    if identifier == "AP051":
        from sqrt2_power_exp_large_argument_ratio import frozen_exp_large_argument_ratio_target
        return frozen_exp_large_argument_ratio_target()
    if identifier == "AP052":
        from sqrt2_power_exp_large_argument_tail import frozen_exp_large_argument_tail_target
        return frozen_exp_large_argument_tail_target()
    if identifier == "AP053":
        from sqrt2_power_halving_prefix_decay import frozen_halving_prefix_decay_target
        return frozen_halving_prefix_decay_target()
    if identifier == "AP054":
        from sqrt2_power_exp_large_argument_decay import frozen_exp_large_argument_decay_target
        return frozen_exp_large_argument_decay_target()
    if identifier == "AP055":
        from sqrt2_power_exp_large_argument_truncation import frozen_exp_large_argument_truncation_target
        return frozen_exp_large_argument_truncation_target()
    if identifier == "AP056":
        from sqrt2_power_exp_geometric_majorant import frozen_exp_geometric_majorant_target
        return frozen_exp_geometric_majorant_target()
    if identifier == "AP057":
        from sqrt2_power_exp_normalized_truncation import frozen_exp_normalized_truncation_target
        return frozen_exp_normalized_truncation_target()
    if identifier == "AP058":
        from sqrt2_power_exp_normalized_witness import frozen_exp_normalized_witness_target
        return frozen_exp_normalized_witness_target()
    if identifier == "AP059":
        from sqrt2_power_exp_large_argument_product import frozen_exp_large_argument_product_target
        return frozen_exp_large_argument_product_target()
    if identifier == "AP060":
        from sqrt2_power_exp_recurrence_independence import frozen_exp_recurrence_independence_target
        return frozen_exp_recurrence_independence_target()
    if identifier == "AP061":
        from sqrt2_power_exp_supplied_large_product import frozen_exp_supplied_large_product_target
        return frozen_exp_supplied_large_product_target()
    if identifier == "AP062":
        from sqrt2_power_exp_binary_budget import frozen_exp_binary_budget_target
        return frozen_exp_binary_budget_target()
    if identifier == "AP063":
        from sqrt2_power_exp_requested_truncation import frozen_exp_requested_truncation_target
        return frozen_exp_requested_truncation_target()
    if identifier == "AP064":
        from sqrt2_power_exp_requested_product import frozen_exp_requested_product_target
        return frozen_exp_requested_product_target()
    if identifier == "AP065":
        from sqrt2_power_exp_independent_horizon import frozen_exp_independent_horizon_target
        return frozen_exp_independent_horizon_target()
    if identifier == "AP066":
        from sqrt2_power_exp_uniform_witness import frozen_exp_uniform_witness_target
        return frozen_exp_uniform_witness_target()
    if identifier == "AP067":
        from sqrt2_power_exp_product_witness import frozen_exp_product_witness_target
        return frozen_exp_product_witness_target()
    if identifier == "AP068":
        from sqrt2_power_exp_relative_continuity import frozen_exp_relative_continuity_target
        return frozen_exp_relative_continuity_target()
    if identifier == "AP069":
        from sqrt2_power_exp_relative_cross_continuity import frozen_exp_relative_cross_continuity_target
        return frozen_exp_relative_cross_continuity_target()
    if identifier == "AP070":
        from sqrt2_power_exp_absolute_continuity import frozen_exp_absolute_continuity_target
        return frozen_exp_absolute_continuity_target()
    if identifier == "AP071":
        from sqrt2_power_exp_submultiplicative import frozen_exp_submultiplicative_target
        return frozen_exp_submultiplicative_target()
    if identifier == "AP072":
        from sqrt2_power_exp_integer_majorant import frozen_exp_integer_majorant_target
        return frozen_exp_integer_majorant_target()
    if identifier == "AP073":
        from sqrt2_power_exp_bounded_majorant import frozen_exp_bounded_majorant_target
        return frozen_exp_bounded_majorant_target()
    if identifier == "AP074":
        from sqrt2_power_exp_bounded_continuity import frozen_exp_bounded_continuity_target
        return frozen_exp_bounded_continuity_target()
    if identifier == "AP075":
        from sqrt2_power_exp_dyadic_continuity import frozen_exp_dyadic_continuity_target
        return frozen_exp_dyadic_continuity_target()
    if identifier == "AP076":
        from sqrt2_power_ordered_power_difference import frozen_ordered_power_difference_target
        return frozen_ordered_power_difference_target()
    if identifier == "AP077":
        from sqrt2_power_symmetric_power_difference import frozen_symmetric_power_difference_target
        return frozen_symmetric_power_difference_target()
    if identifier == "AP078":
        from sqrt2_power_product_power import frozen_product_power_target
        return frozen_product_power_target()
    if identifier == "AP079":
        from sqrt2_power_rational_power_difference import frozen_rational_power_difference_target
        return frozen_rational_power_difference_target()
    if identifier == "AP080":
        from sqrt2_power_requested_power_precision import frozen_requested_power_precision_target
        return frozen_requested_power_precision_target()
    if identifier == "AP081":
        from sqrt2_power_exp_joint_error import frozen_exp_joint_error_target
        return frozen_exp_joint_error_target()
    if identifier == "AP082":
        from sqrt2_power_log_exp_refinement import frozen_log_exp_refinement_target
        return frozen_log_exp_refinement_target()
    if identifier == "AP083":
        from sqrt2_power_log_exp_cutoff_refinement import frozen_log_exp_cutoff_refinement_target
        return frozen_log_exp_cutoff_refinement_target()
    if identifier == "AP084":
        from sqrt2_power_log_exp_uniform_two import frozen_log_exp_uniform_two_target
        return frozen_log_exp_uniform_two_target()
    if identifier == "AP085":
        from sqrt2_power_fixed_log_exp_convergence import frozen_fixed_log_exp_convergence_target
        return frozen_fixed_log_exp_convergence_target()
    if identifier == "AP086":
        from sqrt2_power_fixed_log_exp_witness import frozen_fixed_log_exp_witness_target
        return frozen_fixed_log_exp_witness_target()
    if identifier == "AP087":
        from sqrt2_power_half_log_exp_refinement import frozen_half_log_exp_refinement_target
        return frozen_half_log_exp_refinement_target()
    if identifier == "AP088":
        from sqrt2_power_half_log_exp_cutoff import frozen_half_log_exp_cutoff_target
        return frozen_half_log_exp_cutoff_target()
    if identifier == "AP089":
        from sqrt2_power_half_log_root_uniform import frozen_half_log_root_uniform_target
        return frozen_half_log_root_uniform_target()
    if identifier == "AP090":
        from sqrt2_power_fixed_half_log_root import frozen_fixed_half_log_root_target
        return frozen_fixed_half_log_root_target()
    if identifier == "AP091":
        from sqrt2_power_fixed_half_log_root_witness import frozen_fixed_half_log_root_witness_target
        return frozen_fixed_half_log_root_witness_target()
    if identifier == "AP092":
        from sqrt2_power_fixed_half_log_fine_root import frozen_fixed_half_log_fine_root_target
        return frozen_fixed_half_log_fine_root_target()
    if identifier == "AP093":
        from sqrt2_power_log_root_half_argument import frozen_log_root_half_argument_target
        return frozen_log_root_half_argument_target()
    if identifier == "AP094":
        from sqrt2_power_exp_log_root_half_transport import frozen_exp_log_root_half_transport_target
        return frozen_exp_log_root_half_transport_target()
    if identifier == "AP095":
        from sqrt2_power_requested_half_transport import frozen_requested_half_transport_target
        return frozen_requested_half_transport_target()
    if identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import frozen_natural_gap_target, frozen_norm_separation_target
        return frozen_natural_gap_target() if identifier == "NG001" else frozen_norm_separation_target()
    if identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import frozen_quadratic_norm_product_target
        return frozen_quadratic_norm_product_target()
    if identifier == "SN001":
        from sqrt2_power_signed_norm import frozen_signed_norm_target
        return frozen_signed_norm_target()
    if identifier == "IR016":
        from sqrt2_power_even_square import frozen_ir016_target
        return frozen_ir016_target()
    if identifier == "P10":
        from sqrt2_power_binary_dag import frozen_p10_targets
        return frozen_p10_targets()[0]
    if identifier in ("P08-eprover", "P08-vampire"):
        from sqrt2_power_solver_hints import P08_SOURCE
        from sqrt2_power_native import closed_formula
        return closed_formula(P08_SOURCE)
    if identifier in CHUNK_CASES:
        from sqrt2_power_composition_chunks import chunk_contract
        from sqrt2_power_native import closed_formula
        return closed_formula(chunk_contract(identifier)["source"])
    if identifier.startswith("P04-"):
        from sqrt2_power_formal_composition import contracts
        from sqrt2_power_native import closed_formula
        kind = "ground_instance" if identifier == "P04-ground" else "trace_soundness"
        return closed_formula(next(r for r in contracts() if r["target_kind"] == kind)["source"])
    if identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import foundation_target
        return foundation_target(FOUNDATION_CASES[identifier])
    raise ValueError("unknown exact wave target")


def worker(identifier, hint=None):
    before = pins(identifier)
    target = target_for(identifier)
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import prove_quadratic_nonzero
        result = prove_quadratic_nonzero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="quadratic_integer_binary_nonzero_not_finite_IR046")
    elif identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import prove_quadratic_product_trace
        result = prove_quadratic_product_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="quadratic_finite_trace_nonzero_not_trace_totality_or_real_IR046")
    elif identifier == "QF002":
        from sqrt2_power_quadratic_trace_exists import prove_quadratic_trace_exists
        result = prove_quadratic_trace_exists()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="unconditional_integer_quadratic_product_trace_existence_not_real_IR046")
    elif identifier == "QF003":
        from sqrt2_power_quadratic_product_exists import prove_quadratic_product_exists
        result = prove_quadratic_product_exists()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="witnessed_nonzero_integer_quadratic_finite_product_not_real_IR046")
    elif identifier == "QH001":
        from sqrt2_power_quadratic_height import prove_quadratic_height
        result = prove_quadratic_height()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="canonical_integer_quadratic_binary_height_not_finite_or_real_IR046")
    elif identifier == "QF004":
        from sqrt2_power_canonical_quadratic_trace import prove_canonical_quadratic_trace
        result = prove_canonical_quadratic_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="canonical_integer_quadratic_trace_existence_not_finite_height_or_real_IR046")
    elif identifier == "QH002":
        from sqrt2_power_quadratic_trace_height import prove_quadratic_trace_height
        result = prove_quadratic_trace_height()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="canonical_integer_quadratic_finite_height_not_real_IR046")
    elif identifier == "QF005":
        from sqrt2_power_bounded_quadratic_product import prove_bounded_quadratic_product
        result = prove_bounded_quadratic_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_bounded_nonzero_integer_quadratic_finite_product_not_real_IR046")
    elif identifier == "RN001":
        from sqrt2_power_rational_norm_transport import prove_rational_norm_transport
        result = prove_rational_norm_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="rational_norm_representative_transport_not_full_IR031")
    elif identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import prove_signed_product_nonzero
        result = prove_signed_product_nonzero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_integer_binary_nonzero_not_quadratic_finite_IR046")
    elif identifier == "RN002":
        from sqrt2_power_rational_norm_product import prove_rational_norm_product
        result = prove_rational_norm_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="rational_norm_product_denominator_not_full_IR031")
    elif identifier == "CV001":
        from sqrt2_power_convolution_vanishing import prove_convolution_vanishing
        result = prove_convolution_vanishing()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="universal_natural_convolution_vanishing_not_IR079")
    elif identifier == "CV002":
        from sqrt2_power_logexp_recurrence import prove_logexp_recurrence
        result = prove_logexp_recurrence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="all_indices_natural_logexp_recurrence_solution_not_composition_or_analytic_IR080")
    elif identifier == "CV003":
        from sqrt2_power_natural_convolution import prove_natural_convolution
        result = prove_natural_convolution()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_unique_finite_natural_convolution_not_power_tables_or_IR079")
    elif identifier == "CV004":
        from sqrt2_power_series_power_trace import prove_series_power_trace
        result = prove_series_power_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_finite_natural_power_tables_not_vanishing_or_composition_IR079")
    elif identifier == "CV005":
        from sqrt2_power_series_power_vanishing import prove_series_power_vanishing
        result = prove_series_power_vanishing()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_natural_power_tables_vanish_below_exponent_not_composition_IR079")
    elif identifier == "CV006":
        from sqrt2_power_sum_linearity import prove_sum_linearity
        result = prove_sum_linearity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_weighted_natural_sum_linearity_not_formal_derivative_IR079")
    elif identifier == "CV007":
        from sqrt2_power_euler_product import prove_euler_product
        result = prove_euler_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_coefficientwise_natural_euler_product_rule_not_composition_IR079")
    elif identifier == "CV008":
        from sqrt2_power_natural_fubini import prove_natural_fubini
        result = prove_natural_fubini()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_all_rectangles_natural_fubini_not_convolution_associativity")
    elif identifier == "CV009":
        from sqrt2_power_sum_splitting import prove_sum_splitting
        result = prove_sum_splitting()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_natural_prefix_tail_sum_splitting_not_convolution_associativity")
    elif identifier == "CV010":
        from sqrt2_power_convolution_commutative import prove_convolution_commutative
        result = prove_convolution_commutative()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_commutative_natural_convolution_coefficients_not_associativity")
    elif identifier == "CV011":
        from sqrt2_power_sum_zero_tail import prove_sum_zero_tail
        result = prove_sum_zero_tail()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_zero_tail_finite_sum_transport_not_convolution_associativity")
    elif identifier == "CV012":
        from sqrt2_power_triple_grid import prove_triple_grid
        result = prove_triple_grid()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_finite_triple_product_grid_not_sum_identities_or_associativity")
    elif identifier == "CV013":
        from sqrt2_power_triple_row_sum import prove_triple_row_sum
        result = prove_triple_row_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_triple_row_sum_as_scaled_convolution_not_associativity")
    elif identifier == "CV014":
        from sqrt2_power_convolution_associative import prove_convolution_associative
        result = prove_convolution_associative()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_natural_convolution_associativity_below_common_width_not_composition")
    elif identifier == "CV015":
        from sqrt2_power_convolution_linearity import prove_convolution_linearity
        result = prove_convolution_linearity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_weighted_natural_convolution_linearity_not_composition")
    elif identifier == "CV016":
        from sqrt2_power_convolution_unit import prove_convolution_unit
        result = prove_convolution_unit()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_natural_convolution_unit_below_width_not_composition")
    elif identifier == "CV017":
        from sqrt2_power_series_power_euler import prove_series_power_euler
        result = prove_series_power_euler()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_all_exponents_natural_euler_power_rule_not_composition")
    elif identifier == "CV018":
        from sqrt2_power_series_linear_combination import prove_series_linear_combination
        result = prove_series_linear_combination()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_weighted_natural_prefix_and_convolution_values_not_composition")
    elif identifier == "CV019":
        from sqrt2_power_weighted_series_trace import prove_weighted_series_trace
        result = prove_weighted_series_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_all_lengths_weighted_series_accumulation_trace_not_chain_rule")
    elif identifier == "CV020":
        from sqrt2_power_shifted_euler_prefix import prove_shifted_euler_prefix
        result = prove_shifted_euler_prefix()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_shifted_euler_coefficient_table_not_chain_rule_or_analytic_derivative")
    elif identifier == "CV021":
        from sqrt2_power_finite_composition_euler import prove_finite_composition_euler
        result = prove_finite_composition_euler()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_finite_composition_euler_chain_rule_not_exponential_or_analytic_identity")
    elif identifier == "CV022":
        from sqrt2_power_exponential_weights import prove_exponential_weights
        result = prove_exponential_weights()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_terminal_one_exponential_weight_recurrence_and_nonvanishing_not_factorial_interpretation")
    elif identifier == "CV023":
        from sqrt2_power_weighted_series_scaling import prove_weighted_series_scaling
        result = prove_weighted_series_scaling()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_weighted_traces_with_all_rows_scalar_transport_not_exp_or_analytic_identity")
    elif identifier == "CV024":
        from sqrt2_power_denominator_euler import prove_denominator_euler
        result = prove_denominator_euler()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_denominator_cleared_finite_euler_equation_not_factorial_or_analytic_identity")
    elif identifier == "CV025":
        from sqrt2_power_atanh_coefficients import prove_atanh_coefficients
        result = prove_atanh_coefficients()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_denominator_cleared_odd_reciprocal_prefix_not_logarithm_identity")
    elif identifier == "CV026":
        from sqrt2_power_atanh_euler import prove_atanh_euler
        result = prove_atanh_euler()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_atanh_euler_table_with_initial_values_and_period_two_not_analytic_derivative")
    elif identifier == "CV027":
        from sqrt2_power_periodic_convolution import prove_periodic_convolution
        result = prove_periodic_convolution()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_convolution_coefficients_of_period_two_prefix_not_exp_or_analytic_identity")
    elif identifier == "CV028":
        from sqrt2_power_composition_recurrence import prove_composition_recurrence
        result = prove_composition_recurrence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_finite_composition_three_term_recurrence_not_initial_values_or_analytic_identity")
    elif identifier == "CV029":
        from sqrt2_power_composition_coefficients import prove_composition_coefficients
        result = prove_composition_coefficients()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_finite_composition_initial_and_all_coefficients_not_factorial_or_analytic_identity")
    elif identifier == "CV030":
        from sqrt2_power_weight_factorials import prove_weight_factorials
        result = prove_weight_factorials()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_weight_factorial_power_normalization_not_rational_or_analytic_identity")
    elif identifier == "CV031":
        from sqrt2_power_normalized_composition import prove_normalized_composition
        result = prove_normalized_composition()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_actual_composition_weights_normalized_by_factorial_powers_not_rational_evaluation_or_analytic_identity")
    elif identifier == "CV032":
        from sqrt2_power_horner_trace import prove_horner_trace
        result = prove_horner_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_integer_horner_trace_with_all_in_range_value_uniqueness_not_rational_or_analytic_identity")
    elif identifier == "CV033":
        from sqrt2_power_geometric_horner import prove_geometric_horner
        result = prove_geometric_horner()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_horner_value_and_nonzero_power_with_exact_geometric_remainder_given_all_coefficients_not_analytic_identity")
    elif identifier == "CV034":
        from sqrt2_power_composition_evaluation import prove_composition_evaluation
        result = prove_composition_evaluation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_normalized_composition_and_same_coefficients_horner_value_with_exact_geometric_remainder_not_analytic_identity")
    elif identifier == "CV035":
        from sqrt2_power_horner_linearity import prove_horner_linearity
        result = prove_horner_linearity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_three_horner_evaluations_with_weighted_linearity_from_pointwise_relation_not_multiplication_or_analytic_identity")
    elif identifier == "CV036":
        from sqrt2_power_horner_zero_tail import prove_horner_zero_tail
        result = prove_horner_zero_tail()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_horner_endpoints_and_actual_power_with_exact_zero_tail_scaling_not_multiplication_or_analytic_identity")
    elif identifier == "CV037":
        from sqrt2_power_horner_weighted_sum import prove_horner_weighted_sum
        result = prove_horner_weighted_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_horner_endpoint_equals_actual_sum_given_geometric_weights_and_pointwise_products_not_their_existence_or_analytic_identity")
    elif identifier == "CV038":
        from sqrt2_power_geometric_weights import prove_geometric_weights
        result = prove_geometric_weights()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_terminal_one_geometric_weights_and_actual_power_with_all_weight_power_identities_not_weighted_term_existence_or_analytic_identity")
    elif identifier == "CV039":
        from sqrt2_power_constructed_horner_sum import prove_constructed_horner_sum
        result = prove_constructed_horner_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_geometric_weights_actual_power_pointwise_products_horner_trace_and_actual_sum_for_same_endpoint_not_multiplication_or_analytic_identity")
    elif identifier == "CV040":
        from sqrt2_power_horner_monomials import prove_horner_monomials
        result = prove_horner_monomials()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_same_horner_sum_with_exact_complementary_power_and_monomial_terms_not_multiplication_or_analytic_identity")
    elif identifier == "CV041":
        from sqrt2_power_convolution_weights import prove_convolution_weights
        result = prove_convolution_weights()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_three_geometric_tables_with_convolution_weight_product_law_via_actual_archived_power_add_not_full_evaluation_or_analytic_identity")
    elif identifier == "CV042":
        from sqrt2_power_weighted_convolution import prove_weighted_convolution
        result = prove_weighted_convolution()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_coefficient_weighting_identity_for_all_indices_given_three_weight_tables_and_two_product_prefixes_not_full_evaluation_or_analytic_identity")
    elif identifier == "CV043":
        from sqrt2_power_shifted_scaled_sum import prove_shifted_scaled_sum
        result = prove_shifted_scaled_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_sum_values_for_actual_scaled_shifted_block_with_leading_and_trailing_zeros_not_full_convolution_evaluation_or_analytic_identity")
    elif identifier == "CV044":
        from sqrt2_power_cauchy_grid import prove_cauchy_grid
        result = prove_cauchy_grid()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_square_cauchy_grid_from_actual_zero_padded_antidiagonal_products_and_triangular_zeros_not_row_column_sum_or_evaluation_identity")
    elif identifier == "CV045":
        from sqrt2_power_cauchy_row_sum import prove_cauchy_row_sum
        result = prove_cauchy_row_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_cauchy_grid_and_all_actual_row_sums_identified_with_convolution_coefficients_using_proved_zero_tail_not_column_sums_or_evaluation_identity")
    elif identifier == "CV046":
        from sqrt2_power_cauchy_column_sum import prove_cauchy_column_sum
        result = prove_cauchy_column_sum()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_complete_cauchy_column_sum_equals_padded_left_value_times_right_sum_under_explicit_span_equality_not_unconditional_grid_columns_or_evaluation")
    elif identifier == "CV047":
        from sqrt2_power_cauchy_grid_sums import prove_cauchy_grid_sums
        result = prove_cauchy_grid_sums()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_single_cauchy_grid_and_all_full_length_row_column_sums_with_shared_right_sum_and_zero_columns_not_yet_fubini_sum_product_or_evaluation")
    elif identifier == "CV048":
        from sqrt2_power_convolution_total import prove_convolution_total
        result = prove_convolution_total()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_full_length_natural_convolution_and_all_three_sums_with_output_sum_equal_to_product_of_input_sums_via_actual_fubini_not_horner_or_analytic_identity")
    elif identifier == "CV049":
        from sqrt2_power_horner_product import prove_horner_product
        result = prove_horner_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_full_length_convolution_and_actual_three_horner_traces_with_exact_extra_multiplier_product_law_including_zero_multiplier_not_truncated_evaluation_or_analytic_identity")
    elif identifier == "CV050":
        from sqrt2_power_convolution_locality import prove_convolution_locality
        result = prove_convolution_locality()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_common_actual_coefficient_from_two_local_padded_input_transports_below_explicit_strict_cutoff_not_all_degree_or_analytic_equality")
    elif identifier == "CV051":
        from sqrt2_power_power_width_transport import prove_power_width_transport
        result = prove_power_width_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_two_actual_power_traces_and_all_row_low_coefficient_transport_under_explicit_width_order_not_truncated_full_evaluation_equality")
    elif identifier == "CV052":
        from sqrt2_power_composition_width_transport import prove_composition_width_transport
        result = prove_composition_width_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_cross_width_powers_and_weighted_compositions_preserving_all_low_coefficients_with_same_input_and_weights_not_full_evaluation_or_tail_identity")
    elif identifier == "CV053":
        from sqrt2_power_convolution_upper_support import prove_convolution_upper_support
        result = prove_convolution_upper_support()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_convolution_with_output_zero_after_sum_of_explicit_input_cutoffs_not_power_support_or_analytic_tail_estimate")
    elif identifier == "CV054":
        from sqrt2_power_power_upper_support import prove_power_upper_support
        result = prove_power_upper_support()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_power_trace_with_every_row_zero_at_and_above_one_plus_exponent_times_input_length_including_unit_and_empty_cases_not_evaluation_or_analytic_identity")
    elif identifier == "CV055":
        from sqrt2_power_horner_prefix_transport import prove_horner_prefix_transport
        result = prove_horner_prefix_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_same_actual_horner_history_for_matching_shorter_input_prefix_and_its_endpoint_not_equality_of_different_length_endpoints")
    elif identifier == "CV056":
        from sqrt2_power_supported_horner_product import prove_supported_horner_product
        result = prove_supported_horner_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_support_complete_shorter_convolution_horner_product_with_actual_power_scaling_and_extra_multiplier_no_cancellation_or_arbitrary_truncation_identity")
    elif identifier == "CV057":
        from sqrt2_power_supported_horner_values import prove_supported_horner_values
        result = prove_supported_horner_values()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="support_complete_product_for_supplied_actual_convolution_horner_and_power_values_by_extensional_transport_not_code_equality_or_arbitrary_truncation_identity")
    elif identifier == "CV058":
        from sqrt2_power_finite_power_evaluation import prove_finite_power_evaluation
        result = prove_finite_power_evaluation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_finite_power_trace_with_all_exponent_horner_evaluation_under_explicit_whole_support_width_bound_retaining_unit_and_all_scaling_factors_not_analytic_composition")
    elif identifier == "CV059":
        from sqrt2_power_row_horner_values import prove_row_horner_values
        result = prove_row_horner_values()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_horner_value_prefix_for_arbitrary_coded_rows_with_all_value_extensionality_not_weighted_accumulation_or_analytic_composition")
    elif identifier == "CV060":
        from sqrt2_power_weighted_accumulation_evaluation import prove_weighted_accumulation_evaluation
        result = prove_weighted_accumulation_evaluation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_weighted_accumulation_row_values_pointwise_products_and_sum_with_every_terminal_row_evaluating_to_that_sum_not_analytic_composition")
    elif identifier == "CV061":
        from sqrt2_power_full_composition_evaluation import prove_full_composition_evaluation
        result = prove_full_composition_evaluation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_witness_whole_support_power_trace_weighted_accumulation_row_values_products_and_sum_with_exact_denominator_cleared_monomial_law_not_analytic_exponential_identity")
    elif identifier == "CV062":
        from sqrt2_power_horner_splitting import prove_horner_splitting
        result = prove_horner_splitting()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_shifted_tail_and_prefix_tail_whole_horner_values_with_exact_power_scaled_splitting_including_zero_empty_cases_not_a_tail_estimate")
    elif identifier == "CV063":
        from sqrt2_power_horner_base_comparison import prove_horner_base_comparison
        result = prove_horner_base_comparison()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_horner_values_and_powers_for_ordered_bases_with_power_order_and_exact_length_minus_one_scaled_comparison_including_zero_bases_not_an_analytic_limit")
    elif identifier == "CV064":
        from sqrt2_power_horner_tail_majorant import prove_horner_tail_majorant
        result = prove_horner_tail_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_genuine_tail_and_whole_comparison_values_with_exact_integer_scaled_tail_majorant_for_ordered_bases_not_rational_division_transport_or_analytic_limit")
    elif identifier == "CV065":
        from sqrt2_power_bounded_horner import prove_bounded_horner
        result = prove_bounded_horner()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_horner_value_and_actual_power_with_integer_majorant_from_separate_bounded_coefficients_and_zero_head_including_zero_bound_not_an_analytic_limit")
    elif identifier == "CV066":
        from sqrt2_power_atanh_majorant import prove_atanh_majorant
        result = prove_atanh_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_actual_atanh_coefficient_table_nonzero_denominator_zero_head_and_entry_bounds_with_horner_value_power_and_integer_majorant_not_logarithm_or_rational_division_transport")
    elif identifier == "CV067":
        from sqrt2_power_factorial_majorant import prove_factorial_majorant
        result = prove_factorial_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_factorial_k_plus_two_and_power_three_to_k_with_twice_power_lower_bound_not_yet_a_finite_exponential_sum_bound")
    elif identifier == "CV068":
        from sqrt2_power_ratio_sum_bound import prove_ratio_sum_bound
        result = prove_ratio_sum_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_finite_sum_bounded_by_ratio_head_with_empty_prefix_and_zero_ratio_cases_from_explicit_separate_adjacent_entry_bounds_not_an_analytic_limit")
    elif identifier == "CV069":
        from sqrt2_power_power_weighted_prefix import prove_power_weighted_prefix
        result = prove_power_weighted_prefix()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_weight_times_actual_power_prefix_and_same_prefix_sum_for_arbitrary_weights_including_zero_base_and_empty_prefix_not_factorial_normalization_or_analytic_bound")
    elif identifier == "CV070":
        from sqrt2_power_scaled_exp_terms import prove_scaled_exp_terms
        result = prove_scaled_exp_terms()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_actual_factorial_weights_and_power_terms_with_nonzero_initial_value_exact_scaled_exponential_recurrence_and_factorial_normalization_not_finite_exp_bound_or_analytic_limit")
    elif identifier == "CV071":
        from sqrt2_power_scaled_exp_bound import prove_scaled_exp_bound
        result = prove_scaled_exp_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="all_actual_scaled_exponential_term_data_retained_with_finite_sum_at_most_nine_times_nonzero_initial_weight_under_x_le_twice_nonzero_denominator_not_rational_division_or_analytic_limit")
    elif identifier == "CV072":
        from sqrt2_power_monomial_recurrence import prove_monomial_recurrence
        result = prove_monomial_recurrence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="exact_supplied_composition_monomial_law_implies_actual_head_and_adjacent_row_recurrence_with_nonzero_scale_and_actual_power_cancellation_not_composition_construction_or_analytic_limit")
    elif identifier == "CV073":
        from sqrt2_power_weighted_monomial_recurrence import prove_weighted_monomial_recurrence
        result = prove_weighted_monomial_recurrence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_supplied_factorial_weights_monomial_values_and_pointwise_products_obey_scaled_exponential_recurrence_at_denominator_d_times_p_and_numerator_t_times_x_with_head_w0_times_v_not_yet_constructed_composition_bound")
    elif identifier == "CV074":
        from sqrt2_power_composition_majorant import prove_composition_majorant
        result = prove_composition_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_same_atanh_table_factorial_weights_whole_support_composition_rows_products_and_sum_at_base_two_with_nonzero_normalization_and_sum_at_most_nine_times_w0_times_two_to_J_not_rational_division_or_analytic_limit")
    elif identifier == "CV075":
        from sqrt2_power_rational_tail_majorant import prove_rational_tail_majorant
        result = prove_rational_tail_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructed_actual_nonempty_tail_and_base_three_value_with_actual_powers_nonzero_denominators_and_valid_rational_bound_B_times_two_over_three_to_M_from_supplied_whole_table_majorant_not_analytic_limit_or_empty_tail_case")
    elif identifier == "CV076":
        from sqrt2_power_composition_tail_bound import prove_composition_tail_bound
        result = prove_composition_tail_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="all_actual_composition_majorant_data_retained_with_one_decoded_terminal_row_and_every_in_range_actual_tail_certified_below_nine_times_two_over_three_to_cutoff_in_valid_rational_order_not_analytic_limit")
    elif identifier == "CV077":
        from sqrt2_power_supplied_composition_bound import prove_supplied_composition_bound
        result = prove_supplied_composition_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_atanh_and_weight_codes_preserved_in_constructed_full_composition_majorant_and_every_in_range_actual_rational_tail_with_supplied_nonzero_head_not_table_identity_assumption_or_analytic_limit")
    elif identifier == "CV078":
        from sqrt2_power_consumed_row_transport import prove_consumed_row_transport
        result = prove_consumed_row_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_weighted_accumulation_rows_through_K_preserve_low_coefficients_from_agreement_only_of_consumed_source_rows_below_K_with_same_weights_and_ordered_widths_not_code_equality")
    elif identifier == "CV079":
        from sqrt2_power_successor_composition_transport import prove_successor_composition_transport
        result = prove_successor_composition_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_power_depths_N_and_N_plus_one_transport_all_N_plus_one_weighted_accumulation_rows_by_explicit_large_trace_restriction_and_consumed_row_agreement_with_same_input_and_weights")
    elif identifier == "CV080":
        from sqrt2_power_same_table_composition import prove_same_table_composition
        result = prove_same_table_composition()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="same_actual_full_composition_has_proved_low_coefficient_pattern_geometric_low_prefix_value_factorial_normalization_and_rational_omitted_tail_bound_without_replacing_supplied_inputs_weights_or_assuming_code_equality_not_analytic_limit")
    elif identifier == "CV081":
        from sqrt2_power_supplied_composition_evaluation import prove_supplied_composition_evaluation
        result = prove_supplied_composition_evaluation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="arbitrary_base_evaluation_of_supplied_whole_support_power_and_weighted_accumulation_traces_constructs_actual_row_values_products_sum_and_monomial_law_without_replacing_any_supplied_trace_not_analytic_limit")
    elif identifier == "CV082":
        from sqrt2_power_supplied_horner_splitting import prove_supplied_horner_splitting
        result = prove_supplied_horner_splitting()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_actual_tail_slice_and_independently_computed_prefix_tail_whole_values_obey_exact_scaled_split_using_proved_Horner_value_uniqueness_without_replacing_codes_values_or_cancelling_factors")
    elif identifier == "CV083":
        from sqrt2_power_geometric_tail_sandwich import prove_geometric_tail_sandwich
        result = prove_geometric_tail_sandwich()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="natural_arithmetic_geometric_prefix_plus_actual_split_and_tail_bound_imply_exact_balance_and_both_denominator_cleared_bounds_without_division_cancellation_or_analytic_limit")
    elif identifier == "CV084":
        from sqrt2_power_supplied_geometric_error import prove_supplied_geometric_error
        result = prove_supplied_geometric_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_actual_prefix_tail_and_full_Horner_values_with_actual_power_alignment_and_geometric_tail_premises_give_both_valid_rational_error_bounds_with_all_denominators_proved_nonzero_not_computation_existence_or_analytic_limit")
    elif identifier == "CV085":
        from sqrt2_power_constructed_composition_error import prove_constructed_composition_error
        result = prove_constructed_composition_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="unconditional_same_actual_atanh_input_factorial_weights_whole_support_composition_and_finite_weighted_sum_with_monomial_normalization_and_both_valid_rational_errors_no_geometric_or_tail_premises_no_analytic_limit")
    elif identifier == "CV086":
        from sqrt2_power_ternary_atanh_bound import prove_ternary_atanh_bound
        result = prove_ternary_atanh_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_atanh_prefix_actual_base_three_Horner_value_and_power_obey_three_y_plus_three_d_at_most_d_times_p_by_zero_head_bounded_prefix_induction_no_division_or_analytic_limit")
    elif identifier == "CV087":
        from sqrt2_power_scaled_exp_tail import prove_scaled_exp_tail
        result = prove_scaled_exp_tail()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_shifted_finite_outer_exp_tail_and_sum_with_proved_ratio_half_and_sum_at_most_twice_first_omitted_term_under_nonzero_denominator_and_argument_at_most_one_not_infinite_remainder")
    elif identifier == "CV088":
        from sqrt2_power_scaled_exp_tail_decay import prove_scaled_exp_tail_decay
        result = prove_scaled_exp_tail_decay()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_cutoff_power_two_m_first_omitted_term_slice_ratio_and_sum_with_power_times_first_at_most_head_and_power_times_tail_at_most_twice_head_uniform_in_extra_finite_horizon_not_analytic_limit")
    elif identifier == "CV089":
        from sqrt2_power_ternary_prefix_bound import prove_ternary_prefix_bound
        result = prove_ternary_prefix_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_base_three_Horner_value_and_actual_power_obey_y_plus_D_at_most_D_times_power_for_any_two_D_bounded_prefix_without_zero_head_including_empty_prefix_no_analytic_limit")
    elif identifier == "CV090":
        from sqrt2_power_atanh_truncation import prove_atanh_truncation
        result = prove_atanh_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_actual_atanh_table_prefix_tail_whole_values_and_powers_constructed_with_exact_scaled_split_tail_bound_and_both_cross_multiplied_truncation_bounds_including_zero_lengths_no_division_or_analytic_limit")
    elif identifier == "CV091":
        from sqrt2_power_atanh_rational_truncation import prove_atanh_rational_truncation
        result = prove_atanh_rational_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_actual_atanh_table_prefix_and_whole_values_with_actual_powers_and_all_nonzero_denominators_give_valid_rational_monotonicity_and_error_at_most_three_over_three_to_cutoff_not_analytic_limit")
    elif identifier == "CV092":
        from sqrt2_power_atanh_scale_independence import prove_atanh_scale_independence
        result = prove_atanh_scale_independence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="two_independently_supplied_atanh_tables_and_horner_values_obey_exact_cross_scale_identity_including_zero_scales_base_and_empty_prefix_only_proved_nonzero_odd_index_cancelled_no_code_equality_or_analytic_limit")
    elif identifier == "CV093":
        from sqrt2_power_independent_atanh_truncation import prove_independent_atanh_truncation
        result = prove_independent_atanh_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="independently_supplied_atanh_prefix_and_longer_table_scales_values_and_powers_give_valid_rational_monotonicity_and_uniform_error_three_over_three_to_cutoff_without_code_equality_or_analytic_limit")
    elif identifier == "CV094":
        from sqrt2_power_exp_term_difference import prove_exp_term_difference
        result = prove_exp_term_difference()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_exponential_term_recurrences_with_common_nonzero_denominator_shared_actual_head_and_nonnegative_argument_gap_have_all_index_monotonicity_and_finite_difference_bound_not_derivative_or_infinite_sum")
    elif identifier == "CV095":
        from sqrt2_power_sum_linear_bound import prove_sum_linear_bound
        result = prove_sum_linear_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="explicit_pointwise_weighted_order_transports_to_three_supplied_actual_finite_sums_including_empty_prefix_and_zero_weights_via_conservative_alias_without_sum_accuracy_or_analytic_claim_in_definition")
    elif identifier == "CV096":
        from sqrt2_power_exp_sum_continuity import prove_exp_sum_continuity
        result = prove_exp_sum_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_exponential_recurrences_shared_head_and_sums_at_common_positive_denominator_obey_monotonicity_and_nine_times_argument_gap_bound_via_actual_tail_slices_and_proved_sum_majorant_not_analytic_limit")
    elif identifier == "CV097":
        from sqrt2_power_exp_rescaling import prove_exp_rescaling
        result = prove_exp_rescaling()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_scaled_exponential_table_recurrence_at_common_multiplied_denominator_scaled_head_and_exact_scaled_sum_including_zero_scalars_and_degree_no_code_equality_or_rational_validity_assumption")
    elif identifier == "CV098":
        from sqrt2_power_exp_cross_continuity import prove_exp_cross_continuity
        result = prove_exp_cross_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_exponential_recurrences_with_independent_nonzero_denominators_and_arbitrary_initial_scales_obey_cross_multiplied_continuity_by_constructing_actual_rescaled_tables_and_sums_not_code_equality_or_analytic_limit")
    elif identifier == "CV099":
        from sqrt2_power_exp_rational_continuity import prove_exp_rational_continuity
        result = prove_exp_rational_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_exponential_sums_with_independent_positive_denominators_and_heads_have_valid_rational_monotonicity_and_nine_times_argument_difference_bound_after_explicit_nonzero_denominator_proofs_no_analytic_limit")
    elif identifier == "CV100":
        from sqrt2_power_exp_truncation import prove_exp_truncation
        result = prove_exp_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_exponential_recurrence_head_prefix_and_longer_sum_and_actual_cutoff_power_obey_uniform_finite_truncation_bound_via_constructed_tail_and_actual_affine_sum_uniqueness_no_infinite_remainder_assumption")
    elif identifier == "CV101":
        from sqrt2_power_exp_two_error_bound import prove_exp_two_error_bound
        result = prove_exp_two_error_bound()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_exponential_sums_with_independent_arguments_denominators_heads_and_ordered_horizons_have_combined_argument_and_cutoff_error_via_constructed_middle_prefix_and_checked_polynomial_order_no_analytic_limit")
    elif identifier == "CV102":
        from sqrt2_power_exp_rational_two_error import prove_exp_rational_two_error
        result = prove_exp_rational_two_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="independently_supplied_exponential_computations_at_ordered_arguments_and_distinct_horizons_have_valid_rational_bounds_with_separate_argument_and_dyadic_tail_errors_after_proving_all_denominators_and_cutoff_power_nonzero_no_analytic_limit")
    elif identifier == "SQ001":
        from sqrt2_power_floor_sqrt import prove_floor_sqrt
        result = prove_floor_sqrt()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="unconditional_floor_square_root_totality_and_uniqueness_from_exact_replayed_Bertrand_ancestor_bodies_and_original_conservative_FloorSqrt_definition_not_dyadic_accuracy_or_real_interpretation")
    elif identifier == "SQ002":
        from sqrt2_power_floor_sqrt_comparison import prove_floor_sqrt_comparison
        result = prove_floor_sqrt_comparison()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_floor_root_lies_between_roots_of_supplied_nonstrict_lower_and_strict_upper_square_bounds_via_replayed_natural_decidable_order_no_real_number_or_accuracy_axiom")
    elif identifier == "SQ003":
        from sqrt2_power_scaled_sqrt2 import prove_scaled_sqrt2
        result = prove_scaled_sqrt2()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_unique_actual_floor_root_of_twice_any_positive_scale_squared_and_prove_it_lies_between_the_scale_and_twice_scale_with_nonzero_root_no_analytic_interpretation")
    elif identifier == "SQ004":
        from sqrt2_power_dyadic_sqrt2 import prove_dyadic_sqrt2
        result = prove_dyadic_sqrt2()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="unconditional_total_unique_positive_dyadic_sqrt2_computation_using_actual_power_and_floor_root_graph_with_separate_proved_integer_bounds_no_accuracy_clause_or_analytic_interpretation")
    elif identifier == "SQ005":
        from sqrt2_power_floor_sqrt_scaling import prove_floor_sqrt_scaling
        result = prove_floor_sqrt_scaling()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_floor_root_at_scaled_square_input_is_between_positive_integer_multiples_of_the_original_floor_root_and_its_successor_no_real_limit_assumption")
    elif identifier == "SQ006":
        from sqrt2_power_dyadic_sqrt2_refinement import prove_dyadic_sqrt2_refinement
        result = prove_dyadic_sqrt2_refinement()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="preserve_supplied_dyadic_sqrt2_computations_at_ordered_precisions_construct_actual_intervening_power_prove_denominator_product_and_integer_nesting_without_real_limit")
    elif identifier == "SQ007":
        from sqrt2_power_dyadic_sqrt2_intervals import prove_dyadic_sqrt2_intervals
        result = prove_dyadic_sqrt2_intervals()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_dyadic_sqrt2_intervals_at_ordered_precisions_have_valid_rational_nondecreasing_lower_and_nonincreasing_upper_endpoints_with_proved_denominator_positivity_no_limit")
    elif identifier == "SQ008":
        from sqrt2_power_dyadic_sqrt2_modulus import prove_dyadic_sqrt2_modulus
        result = prove_dyadic_sqrt2_modulus()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_dyadic_sqrt2_computations_at_ordered_precisions_have_explicit_positive_denominators_and_cross_multiplied_error_at_most_one_coarse_denominator_reciprocal_no_analytic_limit")
    elif identifier == "SQ009":
        from sqrt2_power_dyadic_sqrt2_square_error import prove_dyadic_sqrt2_square_error
        result = prove_dyadic_sqrt2_square_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_actual_dyadic_sqrt2_computation_has_positive_denominator_and_root_root_range_and_explicit_square_residual_at_most_four_times_denominator_no_limit_or_square_root_identity_assumption")
    elif identifier == "SQ010":
        from sqrt2_power_dyadic_sqrt2_reciprocal import prove_dyadic_sqrt2_reciprocal
        result = prove_dyadic_sqrt2_reciprocal()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_dyadic_sqrt2_reciprocal_approximants_have_proved_positive_denominators_reversed_order_and_explicit_finite_cross_multiplied_error_at_most_2_to_minus_coarse_precision_no_real_reciprocal_assumption")
    elif identifier == "AP001":
        from sqrt2_power_log_root_argument import prove_log_root_argument
        result = prove_log_root_argument()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_dyadic_root_and_finite_odd_reciprocal_table_horner_value_and_power_prove_positive_quotient_denominator_and_upper_bound_one_no_analytic_logarithm_or_accuracy_assumption")
    elif identifier == "AP002":
        from sqrt2_power_exp_sample import prove_exp_sample
        result = prove_exp_sample()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_finite_exponential_sample_of_log_root_quotient_with_nonzero_normalization_factorial_power_weight_term_tables_sum_recurrence_and_all_index_normalization_no_analytic_identity_or_accuracy_claim")
    elif identifier == "AP003":
        from sqrt2_power_log_root_independence import prove_log_root_independence
        result = prove_log_root_independence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_log_root_quotient_graphs_at_same_precision_with_independent_positive_coefficient_scales_have_identical_dyadic_data_and_powers_positive_denominators_and_exact_rational_value_identity_without_equating_table_codes")
    elif identifier == "AP004":
        from sqrt2_power_supplied_exp_sample import prove_supplied_exp_sample
        result = prove_supplied_exp_sample()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="every_supplied_finite_exponential_sample_with_positive_coefficient_scale_has_nonzero_input_and_output_denominators_input_at_most_one_exact_same_table_recurrence_and_all_index_factorial_normalization_no_replacement_computation")
    elif identifier == "AP005":
        from sqrt2_power_exp_sample_independence import prove_exp_sample_independence
        result = prove_exp_sample_independence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="two_supplied_complete_finite_exponential_samples_at_same_precision_with_independent_positive_coefficient_scales_have_positive_output_denominators_and_exact_rational_value_identity_without_equating_codes_or_scales")
    elif identifier == "AP006":
        from sqrt2_power_argument_modulus import prove_argument_modulus
        result = prove_argument_modulus()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_log_root_quotients_at_ordered_precisions_have_positive_denominators_and_two_sided_asymmetric_finite_error_from_logarithm_tail_and_reciprocal_root_modulus_without_monotonicity_assumption")
    elif identifier == "AP007":
        from sqrt2_power_exp_two_sided_continuity import prove_exp_two_sided_continuity
        result = prove_exp_two_sided_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_same_degree_finite_exponential_sums_have_two_sided_scaled_error_bounds_without_input_monotonicity_by_constructive_natural_order_and_actual_additive_gap_with_independent_denominator_and_head_scales")
    elif identifier == "AP008":
        from sqrt2_power_exp_two_sided_horizons import prove_exp_two_sided_horizons
        result = prove_exp_two_sided_horizons()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="supplied_finite_exponential_sums_at_unequal_horizons_have_two_sided_scaled_error_bounds_from_actual_constructed_prefix_and_supplied_cutoff_power_without_input_monotonicity_or_analytic_limit_assumptions")
    elif identifier == "AP009":
        from sqrt2_power_exp_sample_modulus import prove_exp_sample_modulus
        result = prove_exp_sample_modulus()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_samples_at_k_and_k_plus_positive_increment_have_scale_free_two_sided_finite_errors_with_positive_output_and_cutoff_denominators_without_input_monotonicity_or_analytic_limit_claims")
    elif identifier == "AP010":
        from sqrt2_power_positive_power_comparison import prove_positive_power_comparison
        result = prove_positive_power_comparison()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_natural_powers_are_jointly_monotone_in_ordered_bases_and_additive_exponents_when_the_larger_base_is_nonzero_with_zero_smaller_base_and_zero_exponents_allowed")
    elif identifier == "AP011":
        from sqrt2_power_approximation_power_bounds import prove_approximation_power_bounds
        result = prove_approximation_power_bounds()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_dyadic_logarithm_and_exponential_cutoff_powers_are_positive_and_both_cutoff_powers_dominate_the_actual_dyadic_denominator_including_zero_precision")
    elif identifier == "AP012":
        from sqrt2_power_exp_sample_uniform_error import prove_exp_sample_uniform_error
        result = prove_exp_sample_uniform_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_samples_at_strictly_finer_precision_have_uniform_two_sided_dyadic_error_with_positive_output_denominators_and_internally_constructed_cutoff_power_without_real_accuracy_or_irrationality_claims")
    elif identifier == "AP013":
        from sqrt2_power_exp_sample_all_precision import prove_exp_sample_all_precision
        result = prove_exp_sample_all_precision()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_samples_have_positive_output_denominators_and_uniform_two_sided_dyadic_error_for_every_precision_increment_including_zero_by_constructive_case_split_and_exact_value_independence")
    elif identifier == "AP014":
        from sqrt2_power_fixed_precision_threshold import prove_fixed_precision_threshold
        result = prove_fixed_precision_threshold()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_eighth_power_of_two_is_positive_and_dominates_the_finite_error_constant_via_constructed_fifth_power_and_small_ordinary_HA_arithmetic_without_unary_256_or_new_induction")
    elif identifier == "AP015":
        from sqrt2_power_exp_sample_dyadic_error import prove_exp_sample_dyadic_error
        result = prove_exp_sample_dyadic_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="actual_supplied_samples_at_n_plus_eight_and_any_finer_precision_have_two_sided_finite_error_at_most_one_over_a_constructed_positive_two_to_n_using_the_actual_coarse_power_and_a_constructed_positive_shift_power")
    elif identifier == "AP016":
        from sqrt2_power_atanh_odd_slice import prove_atanh_odd_slice
        result = prove_atanh_odd_slice()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_odd_index_affine_slice_of_a_supplied_atanh_prefix_and_prove_all_odd_quotient_equations_and_all_even_zeros_including_empty_slice_and_zero_scale_without_analytic_identification")
    elif identifier == "AP017":
        from sqrt2_power_paired_horner import prove_paired_horner
        result = prove_paired_horner()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="compare_actual_supplied_horner_histories_by_explicit_pairwise_induction_to_prove_long_value_equals_base_times_odd_slice_value_at_squared_base_with_every_even_coefficient_zero_including_the_terminal_entry")
    elif identifier == "AP018":
        from sqrt2_power_paired_power import prove_paired_power
        result = prove_paired_power()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="normalize_both_actual_supplied_power_computations_to_the_squared_base_by_explicit_doubled_exponent_induction_and_a_final_successor_allowing_zero_base_and_zero_index_without_cancellation")
    elif identifier == "AP019":
        from sqrt2_power_odd_horner_quotient import prove_odd_horner_quotient
        result = prove_odd_horner_quotient()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_odd_slice_horner_value_and_power_at_base_nine_then_prove_the_original_finite_log_quotient_equals_its_odd_horner_quotient_with_every_denominator_nonzero_without_infinite_analytic_identification")
    elif identifier == "AP020":
        from sqrt2_power_finite_odd_log_series import prove_finite_odd_log_series
        result = prove_finite_odd_log_series()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="preserve_the_original_finite_log_computations_and_construct_an_actual_sum_table_identifying_every_normalized_term_with_its_odd_reciprocal_using_constructed_positive_denominator_powers_without_assuming_an_infinite_logarithm_identity")
    elif identifier == "AP021":
        from sqrt2_power_finite_exp_series import prove_finite_exp_series
        result = prove_finite_exp_series()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="preserve_the_actual_supplied_exponential_sample_table_and_sum_and_identify_each_normalized_term_with_its_factorial_series_value_using_constructed_factorials_and_both_powers_with_positive_denominators_without_infinite_exponential_identification")
    elif identifier == "AP022":
        from sqrt2_power_factorial_atanh_prefix import prove_factorial_atanh_prefix
        result = prove_factorial_atanh_prefix()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_positive_factorial_N_as_the_prescribed_logarithm_coefficient_scale_and_the_actual_coefficient_prefix_using_a_proved_positive_divisor_induction_and_existing_prefix_construction_without_claiming_the_whole_canonical_PR_approximation_trace")
    elif identifier == "AP023":
        from sqrt2_power_factorial_exp_sample import prove_factorial_exp_sample
        result = prove_factorial_exp_sample()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_complete_finite_log_root_exponential_sample_with_prescribed_coefficient_scale_factorial_two_k_plus_one_preserving_positive_scale_all_actual_computations_recurrence_and_normalization_without_claiming_the_whole_PR_trace_or_analytic_identification")
    elif identifier == "AP024":
        from sqrt2_power_atomic_computation_decisions import prove_atomic_computation_decisions
        result = prove_atomic_computation_decisions()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructively_decide_natural_equality_order_beta_decoding_powers_factorials_sums_and_integer_square_roots_from_replayed_totality_and_value_uniqueness_without_classical_axioms_or_a_claim_of_a_complete_CApprox_verifier")
    elif identifier == "AP025":
        from sqrt2_power_approximation_component_decisions import prove_approximation_component_decisions
        result = prove_approximation_component_decisions()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructively_decide_the_actual_individual_logarithm_coefficient_Horner_value_and_dyadic_square_root_computation_graphs_for_all_inputs_including_invalid_candidates_without_new_induction_or_a_complete_CApprox_verifier_claim")
    elif identifier == "AP026":
        from sqrt2_power_finite_table_decisions import prove_finite_table_decisions
        result = prove_finite_table_decisions()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="compile_and_replay_actual_beta_power_row_decisions_and_bounded_induction_decisions_for_supplied_coefficient_weight_and_term_tables_including_incorrect_tables_empty_prefixes_and_zero_scales_without_claiming_the_complete_CApprox_record")
    elif identifier == "AP027":
        from sqrt2_power_prescribed_sample_decision import prove_prescribed_sample_decision
        result = prove_prescribed_sample_decision()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructively_decide_the_entire_supplied_prescribed_factorial_sample_and_positive_scale_output_denominator_by_sequentially_checking_every_actual_computation_field_without_assuming_correctness_accuracy_or_canonical_record_construction")
    elif identifier == "AP028":
        from sqrt2_power_approximation_record_exists import prove_approximation_record_exists
        result = prove_approximation_record_exists()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_an_actual_fifteen_field_beta_record_of_the_positive_fixed_factorial_finite_sample_at_precision_n_plus_eight_with_both_code_components_explicit_and_all_decoded_fields_consumed_without_accuracy_or_analytic_clauses")
    elif identifier == "AP029":
        from sqrt2_power_approximation_record_decision import prove_approximation_record_decision
        result = prove_approximation_record_decision()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="constructively_decide_any_supplied_fifteen_field_approximation_record_by_actual_beta_decoding_complete_sample_decision_and_equality_transport_of_all_competing_internal_fields_without_unbounded_search_or_classical_axioms")
    elif identifier == "AP030":
        from sqrt2_power_approximation_record_independence import prove_approximation_record_independence
        result = prove_approximation_record_independence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_positive_output_denominators_and_cross_multiplied_rational_equality_for_two_actual_records_at_the_same_precision_by_replaying_AP005_without_requiring_equal_code_numbers")
    elif identifier == "AP031":
        from sqrt2_power_approximation_record_error import prove_approximation_record_error
        result = prove_approximation_record_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="transport_the_actual_all_finer_finite_dyadic_error_to_two_complete_records_after_proving_the_fixed_precision_shift_alignment_preserving_the_actual_power_and_positive_denominators_without_an_analytic_limit_claim")
    elif identifier == "AP032":
        from sqrt2_power_log_exp_witness import prove_log_exp_witness
        result = prove_log_exp_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_finite_logarithm_coefficients_and_exponential_terms_and_connect_the_same_product_table_to_its_positive_head_recurrence_sum_and_both_errors_near_two_without_asserting_the_infinite_logarithm_identity")
    elif identifier == "AP033":
        from sqrt2_power_log_exp_budget import prove_log_exp_budget
        result = prove_log_exp_budget()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_two_actual_power_inductions_and_the_explicit_cutoff_N_equals_eighteen_r_plus_two_budget_for_both_finite_log_exponential_errors_without_materializing_large_exponentials_or_altering_the_fixed_approximation_program")
    elif identifier == "AP034":
        from sqrt2_power_log_exp_dyadic_witness import prove_log_exp_dyadic_witness
        result = prove_log_exp_dyadic_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_two_to_n_and_the_explicit_finite_log_exponential_computations_with_two_integer_error_bounds_at_most_two_to_minus_n_from_two_retained_stage_proofs_and_positive_comparison_powers_without_infinite_analytic_identification")
    elif identifier == "AP035":
        from sqrt2_power_exp_recurrence_normalization import prove_exp_recurrence_normalization
        result = prove_exp_recurrence_normalization()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="derive_all_index_factorial_power_normalization_from_any_supplied_actual_finite_exponential_recurrence_and_head_by_ordinary_induction_without_cancellation_including_zero_denominator_numerator_head_and_horizon")
    elif identifier == "AP036":
        from sqrt2_power_exp_recurrence_series import prove_exp_recurrence_series
        result = prove_exp_recurrence_series()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="identify_every_actual_supplied_exponential_recurrence_term_with_its_valid_rational_factorial_series_value_constructing_the_factorial_and_both_powers_from_retained_generic_proofs_without_an_infinite_series_claim")
    elif identifier == "AP037":
        from sqrt2_power_convolution_shift import prove_convolution_shift
        result = prove_convolution_shift()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="transport_a_denominator_cleared_one_place_shift_through_actual_finite_convolution_coefficients_using_the_zero_head_and_only_required_local_indices_with_all_input_lengths_and_zero_scalars_allowed")
    elif identifier == "AP038":
        from sqrt2_power_exp_convolution_recurrence import prove_exp_convolution_recurrence
        result = prove_exp_convolution_recurrence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="derive_the_added_argument_exponential_convolution_recurrence_below_the_shared_finite_cutoff_using_actual_euler_tables_product_rule_and_local_denominator_cleared_shift_without_cancellation_or_an_infinite_identity")
    elif identifier == "AP039":
        from sqrt2_power_exp_convolution_prefix import prove_exp_convolution_prefix
        result = prove_exp_convolution_prefix()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_finite_convolution_prefix_and_sum_prove_its_product_head_added_argument_recurrence_and_all_index_factorial_normalization_without_equating_the_truncated_sum_with_the_full_product_of_input_sums")
    elif identifier == "AP040":
        from sqrt2_power_convolution_prefix_order import prove_convolution_prefix_order
        result = prove_convolution_prefix_order()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_order_of_actual_convolution_coefficients_under_both_input_prefix_length_extensions_with_fixed_beta_codes_by_padding_product_and_finite_sum_order_including_empty_lengths_and_all_indices")
    elif identifier == "AP041":
        from sqrt2_power_convolution_sum_sandwich import prove_convolution_sum_sandwich
        result = prove_convolution_sum_sandwich()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_convolution_of_extended_inputs_and_sandwich_the_rectangular_product_of_the_short_input_sums_between_its_short_and_double_length_sums_by_finite_locality_prefix_order_and_the_full_product_identity")
    elif identifier == "AP042":
        from sqrt2_power_exp_product_error import prove_exp_product_error
        result = prove_exp_product_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_added_argument_exponential_convolution_and_bound_the_rectangular_degree_n_product_error_by_two_times_the_product_head_over_two_to_n_using_actual_finite_tails_for_x_plus_y_at_most_d_without_an_infinite_identity")
    elif identifier == "AP043":
        from sqrt2_power_exp_supplied_product import prove_exp_supplied_product
        result = prove_exp_supplied_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="transport_the_finite_exponential_product_error_to_three_actual_supplied_recurrences_heads_and_short_sums_with_independent_output_code_and_normalization_using_checked_cross_value_identity_and_no_infinite_addition")
    elif identifier == "AP044":
        from sqrt2_power_exp_half_square import prove_exp_half_square
        result = prove_exp_half_square()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_positive_factorial_weighted_half_argument_exponential_terms_and_both_actual_sums_and_bound_the_short_sum_square_against_the_supplied_whole_argument_sum_without_logarithm_or_square_root_identification")
    elif identifier == "AP045":
        from sqrt2_power_half_square_error_transfer import prove_half_square_error_transfer
        result = prove_half_square_error_transfer()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="combine_supplied_finite_cross_product_error_two_over_p_and_reference_error_one_over_r_with_r_at_most_p_by_positive_cancellation_to_obtain_upper_error_three_over_r_and_lower_error_one_over_r_without_constructing_or_identifying_any_analytic_object")
    elif identifier == "AP046":
        from sqrt2_power_half_log_precision import prove_half_log_precision
        result = prove_half_log_precision()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_generic_binary_growth_n_plus_one_at_most_two_to_n_by_ordinary_induction_then_bound_the_actual_two_to_eighteen_r_plus_two_cutoff_power_below_by_r_without_materializing_large_ground_powers")
    elif identifier == "AP047":
        from sqrt2_power_half_log_square import prove_half_log_square
        result = prove_half_log_square()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_atanh_horner_half_logarithm_exponential_and_prove_its_short_sum_square_has_upper_error_three_over_two_to_n_and_lower_error_one_over_two_to_n_with_positive_normalization_without_identifying_an_infinite_exponential_or_sqrt_two")
    elif identifier == "AP048":
        from sqrt2_power_square_error_linear import prove_square_error_linear
        result = prove_square_error_linear()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="convert_two_supplied_natural_square_errors_to_linear_errors_by_decidable_order_actual_additive_gaps_difference_of_squares_and_positive_scale_cancellation_without_an_analytic_square_root_assumption")
    elif identifier == "AP049":
        from sqrt2_power_half_log_root_comparison import prove_half_log_root_comparison
        result = prove_half_log_root_comparison()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="compare_supplied_positive_half_log_and_dyadic_root_square_witnesses_at_r_at_most_d_with_forward_error_seven_over_r_and_reverse_error_one_over_r_by_natural_cross_products_without_constructing_witnesses_or_assuming_a_real_identity")
    elif identifier == "AP050":
        from sqrt2_power_half_log_root_witness import prove_half_log_root_witness
        result = prove_half_log_root_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_at_every_precision_the_actual_half_log_exponential_and_same_denominator_dyadic_floor_root_preserving_all_computations_and_square_bounds_and_proving_both_finite_cross_product_errors_without_an_infinite_identity")
    elif identifier == "AP051":
        from sqrt2_power_exp_large_argument_ratio import prove_exp_large_argument_ratio
        result = prove_exp_large_argument_ratio()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_halving_of_each_supplied_exponential_recurrence_step_beyond_twice_an_arbitrary_natural_argument_bound_by_positive_full_coefficient_cancellation_including_zero_argument_without_a_finite_sum_or_analytic_assumption")
    elif identifier == "AP052":
        from sqrt2_power_exp_large_argument_tail import prove_exp_large_argument_tail
        result = prove_exp_large_argument_tail()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_shifted_tail_head_halving_relation_and_sum_of_a_supplied_exponential_recurrence_at_any_cutoff_at_least_twice_its_natural_argument_bound_with_finite_sum_at_most_twice_the_head_including_zero_cutoffs_without_an_infinite_tail")
    elif identifier == "AP053":
        from sqrt2_power_halving_prefix_decay import prove_halving_prefix_decay
        result = prove_halving_prefix_decay()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_symbolic_binary_decay_at_every_bounded_index_of_an_actual_supplied_halving_prefix_by_one_ordinary_HA_induction_including_zero_head_index_and_horizon_without_division_or_an_infinite_sequence")
    elif identifier == "AP054":
        from sqrt2_power_exp_large_argument_decay import prove_exp_large_argument_decay
        result = prove_exp_large_argument_decay()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_powers_heads_shifted_slices_and_sums_with_dyadic_decay_after_every_extra_cutoff_beyond_twice_a_general_natural_argument_bound_including_all_zero_margins_and_without_an_infinite_remainder_claim")
    elif identifier == "AP055":
        from sqrt2_power_exp_large_argument_truncation import prove_exp_large_argument_truncation
        result = prove_exp_large_argument_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="identify_the_constructed_large_argument_tail_with_two_supplied_sum_values_and_prove_both_truncation_orders_with_the_supplied_head_and_binary_power_including_an_empty_short_prefix_without_infinite_analysis")
    elif identifier == "AP056":
        from sqrt2_power_exp_geometric_majorant import prove_exp_geometric_majorant
        result = prove_exp_geometric_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_every_bounded_actual_exponential_term_is_at_most_the_actual_natural_argument_bound_power_times_its_original_head_by_one_ordinary_induction_and_positive_denominator_cancellation_including_zero_argument_bound")
    elif identifier == "AP057":
        from sqrt2_power_exp_normalized_truncation import prove_exp_normalized_truncation
        result = prove_exp_normalized_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_the_large_argument_truncation_error_relative_to_the_original_head_while_retaining_the_supplied_table_sums_and_two_actual_powers_including_zero_head_and_empty_prefix_without_an_analytic_limit")
    elif identifier == "AP058":
        from sqrt2_power_exp_normalized_witness import prove_exp_normalized_witness
        result = prove_exp_normalized_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_actual_factorial_weighted_exponential_tables_positive_original_normalization_both_powers_and_sums_with_original_head_normalized_finite_tail_error_for_arbitrary_bounded_arguments_without_an_analytic_exponential")
    elif identifier == "AP059":
        from sqrt2_power_exp_large_argument_product import prove_exp_large_argument_product
        result = prove_exp_large_argument_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_the_actual_finite_exponential_Cauchy_product_recurrence_head_and_four_sums_with_an_original_head_normalized_quantitative_product_error_for_arbitrarily_bounded_arguments_without_an_exponential_addition_axiom")
    elif identifier == "AP060":
        from sqrt2_power_exp_recurrence_independence import prove_exp_recurrence_independence
        result = prove_exp_recurrence_independence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_cross_value_equality_of_two_actual_supplied_exponential_recurrences_and_sums_at_equal_rational_arguments_without_any_argument_bound_or_positive_head_assumption_by_one_ordinary_induction_and_existing_sum_linearity")
    elif identifier == "AP061":
        from sqrt2_power_exp_supplied_large_product import prove_exp_supplied_large_product
        result = prove_exp_supplied_large_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="retain_three_independently_supplied_exponential_tables_heads_and_sums_with_general_argument_product_error_using_unrestricted_recurrence_value_independence_and_no_analytic_addition_axiom")
    elif identifier == "AP062":
        from sqrt2_power_exp_binary_budget import prove_exp_binary_budget
        result = prove_exp_binary_budget()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_an_explicit_symbolic_dyadic_budget_for_arbitrary_natural_argument_majorants_by_one_ordinary_power_induction_and_actual_power_addition_including_zero_base_exponent_and_precision_without_large_ground_numerals")
    elif identifier == "AP063":
        from sqrt2_power_exp_requested_truncation import prove_exp_requested_truncation
        result = prove_exp_requested_truncation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_requested_dyadic_accuracy_for_two_supplied_finite_exponential_sums_at_an_explicit_large_argument_cutoff_uniformly_in_the_extra_finite_horizon_with_auxiliary_powers_constructed_and_no_analytic_limit")
    elif identifier == "AP064":
        from sqrt2_power_exp_requested_product import prove_exp_requested_product
        result = prove_exp_requested_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_requested_dyadic_accuracy_for_the_product_of_two_independently_supplied_finite_exponential_sums_against_a_third_supplied_sum_at_the_added_argument_with_explicit_symbolic_cutoffs_and_no_analytic_addition_axiom")
    elif identifier == "AP065":
        from sqrt2_power_exp_independent_horizon import prove_exp_independent_horizon
        result = prove_exp_independent_horizon()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_requested_dyadic_Cauchy_accuracy_across_two_independently_supplied_exponential_codes_denominators_and_heads_at_equal_rational_arguments_and_different_finite_horizons_by_constructing_the_actual_fine_short_sum")
    elif identifier == "AP066":
        from sqrt2_power_exp_uniform_witness import prove_exp_uniform_witness
        result = prove_exp_uniform_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_one_positive_factorial_normalized_coarse_exponential_table_and_precision_power_before_the_universal_extra_horizon_then_actual_positive_fine_tables_with_requested_dyadic_error_without_an_analytic_limit")
    elif identifier == "AP067":
        from sqrt2_power_exp_product_witness import prove_exp_product_witness
        result = prove_exp_product_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_three_positive_factorial_normalized_exponential_tables_and_actual_input_prefix_sums_with_requested_dyadic_product_error_retaining_all_indexwise_normalizations_without_an_analytic_addition_axiom")
    elif identifier == "AP068":
        from sqrt2_power_exp_relative_continuity import prove_exp_relative_continuity
        result = prove_exp_relative_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_relative_finite_exponential_sum_continuity_for_arbitrary_nonnegative_arguments_from_actual_tail_slices_without_any_small_argument_bound_or_analytic_limit")
    elif identifier == "AP069":
        from sqrt2_power_exp_relative_cross_continuity import prove_exp_relative_cross_continuity
        result = prove_exp_relative_cross_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_unrestricted_relative_finite_exponential_continuity_across_independent_positive_argument_denominators_arbitrary_heads_and_actual_codes_by_constructing_rescaled_common_head_tables")
    elif identifier == "AP070":
        from sqrt2_power_exp_absolute_continuity import prove_exp_absolute_continuity
        result = prove_exp_absolute_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_requested_absolute_finite_exponential_continuity_from_two_actual_independent_computations_an_explicit_sum_majorant_and_symbolic_precision_budget_without_assuming_the_majorant_or_precision_power_as_an_analytic_axiom")
    elif identifier == "AP071":
        from sqrt2_power_exp_submultiplicative import prove_exp_submultiplicative
        result = prove_exp_submultiplicative()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_unrestricted_submultiplicativity_for_three_actual_finite_exponential_sums_at_the_same_degree_by_constructing_a_Cauchy_table_and_identifying_its_cross_normalized_value_without_extra_horizons_or_analytic_addition")
    elif identifier == "AP072":
        from sqrt2_power_exp_integer_majorant import prove_exp_integer_majorant
        result = prove_exp_integer_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_a_horizon_independent_power_majorant_at_every_integer_argument_by_ordinary_induction_and_actual_positive_successor_factor_tables_without_assuming_positivity_of_the_supplied_head_or_an_analytic_exponential")
    elif identifier == "AP073":
        from sqrt2_power_exp_bounded_majorant import prove_exp_bounded_majorant
        result = prove_exp_bounded_majorant()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_a_horizon_independent_power_majorant_for_every_actual_bounded_rational_argument_by_constructing_a_positive_integer_argument_reference_and_cancelling_only_its_head_without_an_analytic_axiom")
    elif identifier == "AP074":
        from sqrt2_power_exp_bounded_continuity import prove_exp_bounded_continuity
        result = prove_exp_bounded_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_two_sided_absolute_continuity_of_actual_independent_bounded_finite_exponential_computations_by_a_checked_power_majorant_decidable_order_split_and_explicit_precision_budget_without_an_analytic_limit_claim")
    elif identifier == "AP075":
        from sqrt2_power_exp_dyadic_continuity import prove_exp_dyadic_continuity
        result = prove_exp_dyadic_continuity()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_an_explicit_linear_dyadic_input_precision_modulus_for_two_actual_bounded_finite_exponential_computations_by_constructing_the_majorant_power_and_reusing_the_checked_symbolic_binary_budget_without_changing_the_original_approximation_program")
    elif identifier == "AP076":
        from sqrt2_power_ordered_power_difference import prove_ordered_power_difference
        result = prove_ordered_power_difference()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_the_ordered_natural_power_difference_bound_for_three_actual_supplied_powers_by_ordinary_induction_including_zero_bases_without_division_or_analytic_axioms")
    elif identifier == "AP077":
        from sqrt2_power_symmetric_power_difference import prove_symmetric_power_difference
        result = prove_symmetric_power_difference()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_two_sided_error_propagation_for_three_actual_bounded_natural_powers_by_decidable_input_order_and_the_extracted_gap_without_positive_base_assumptions_or_new_induction")
    elif identifier == "AP078":
        from sqrt2_power_product_power import prove_product_power
        result = prove_product_power()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_the_product_of_actual_natural_power_values_by_constructing_previous_powers_and_identifying_supplied_successors_with_uniqueness_including_zero_bases_and_exponent")
    elif identifier == "AP079":
        from sqrt2_power_rational_power_difference import prove_rational_power_difference
        result = prove_rational_power_difference()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_symmetric_error_propagation_for_independently_normalized_nonnegative_rational_powers_by_constructing_actual_cross_numerator_powers_preserving_all_six_supplied_powers_and_proving_output_denominators_nonzero")
    elif identifier == "AP080":
        from sqrt2_power_requested_power_precision import prove_requested_power_precision
        result = prove_requested_power_precision()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_requested_rational_power_precision_under_an_explicit_input_budget_by_constructing_denominator_product_powers_and_replaying_actual_successor_and_product_identities_without_cancellation_or_analytic_axioms")
    elif identifier == "AP081":
        from sqrt2_power_exp_joint_error import prove_exp_joint_error
        result = prove_exp_joint_error()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_explicit_combined_input_and_truncation_errors_for_independent_bounded_finite_exponential_computations_by_constructing_the_actual_middle_prefix_preserving_the_two_error_budgets_without_analytic_limit_assumptions")
    elif identifier == "AP082":
        from sqrt2_power_log_exp_refinement import prove_log_exp_refinement
        result = prove_log_exp_refinement()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_supplied_logarithm_and_exponential_refinement_across_independent_scales_codes_and_horizons_with_explicit_27_over_ternary_power_plus_2_over_binary_power_error_without_limit_or_code_equality_assumptions")
    elif identifier == "AP083":
        from sqrt2_power_log_exp_cutoff_refinement import prove_log_exp_cutoff_refinement
        result = prove_log_exp_cutoff_refinement()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_the_existing_auxiliary_18_r_plus_2_cutoff_pays_both_logarithm_and_exponential_refinement_errors_from_actual_power_computations_without_assuming_the_budgets_or_changing_the_fixed_approximation_program")
    elif identifier == "AP084":
        from sqrt2_power_log_exp_uniform_two import prove_log_exp_uniform_two
        result = prove_log_exp_uniform_two()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_one_actual_dyadic_reference_before_arbitrary_independent_later_logarithm_and_exponential_tables_and_prove_uniform_near_two_bounds_by_positive_reference_head_cancellation_without_assuming_an_analytic_limit")
    elif identifier == "AP085":
        from sqrt2_power_fixed_log_exp_convergence import prove_fixed_log_exp_convergence
        result = prove_fixed_log_exp_convergence()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_uniform_finite_near_two_bounds_for_the_fixed_two_k_plus_one_logarithm_prefix_and_k_plus_two_exponential_degree_by_constructing_the_actual_cutoff_gap_and_proving_both_index_alignments_without_changing_the_computations")
    elif identifier == "AP086":
        from sqrt2_power_fixed_log_exp_witness import prove_fixed_log_exp_witness
        result = prove_fixed_log_exp_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_positive_actual_logarithm_and_factorial_normalized_exponential_computations_at_every_eligible_fixed_schedule_index_after_one_uniform_dyadic_threshold_preserving_all_index_normalization_and_both_near_two_bounds")
    elif identifier == "AP087":
        from sqrt2_power_half_log_exp_refinement import prove_half_log_exp_refinement
        result = prove_half_log_exp_refinement()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="prove_independent_half_logarithm_exponential_refinement_by_explicit_doubled_argument_denominators_and_scaled_gap_transport_while_retaining_the_unchanged_original_logarithm_prefixes_values_and_powers")
    elif identifier == "AP088":
        from sqrt2_power_half_log_exp_cutoff import prove_half_log_exp_cutoff
        result = prove_half_log_exp_cutoff()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="apply_checked_actual_power_cutoff_budgets_and_positive_cancellation_to_independent_half_logarithm_exponential_refinement_without_assuming_the_budgets_changing_the_original_logarithm_computations_or_adding_arithmetic_helpers")
    elif identifier == "AP089":
        from sqrt2_power_half_log_root_uniform import prove_half_log_root_uniform
        result = prove_half_log_root_uniform()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="choose_one_actual_dyadic_root_before_all_later_independent_half_logarithm_exponential_tables_and_prove_both_finite_cross_errors_by_checked_reference_restriction_refinement_and_positive_scale_cancellation")
    elif identifier == "AP090":
        from sqrt2_power_fixed_half_log_root import prove_fixed_half_log_root
        result = prove_fixed_half_log_root()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="align_the_independent_half_logarithm_root_comparison_with_the_original_fixed_logarithm_length_and_exponential_degree_using_checked_gap_and_index_equalities_without_changing_any_computation_or_witness_quantifier_order")
    elif identifier == "AP091":
        from sqrt2_power_fixed_half_log_root_witness import prove_fixed_half_log_root_witness
        result = prove_fixed_half_log_root_witness()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="construct_positive_fixed_schedule_half_logarithm_exponential_tables_after_one_chosen_dyadic_root_and_retain_every_actual_factorial_normalization_and_both_checked_cross_errors")
    elif identifier == "AP092":
        from sqrt2_power_fixed_half_log_fine_root import prove_fixed_half_log_fine_root
        result = prove_fixed_half_log_fine_root()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="transfer_constructed_fixed_schedule_half_logarithm_samples_to_any_supplied_finer_dyadic_root_at_the_same_index_preserving_all_positive_normalizations_and_both_finite_errors")
    elif identifier == "AP093":
        from sqrt2_power_log_root_half_argument import prove_log_root_half_argument
        result = prove_log_root_half_argument()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="compare_supplied_original_log_root_quotient_with_half_root_argument_proving_both_denominators_positive_unit_interval_bounds_and_explicit_two_over_d_square_residual_without_an_exact_finite_or_analytic_identity")
    elif identifier == "AP094":
        from sqrt2_power_exp_log_root_half_transport import prove_exp_log_root_half_transport
        result = prove_exp_log_root_half_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="transport_the_actual_original_finite_exponential_sample_to_an_independent_positive_half_root_recurrence_at_the_same_k_plus_two_degree_with_order_and_eighteen_over_d_error_cancelling_only_proved_nonzero_factors")
    elif identifier == "AP095":
        from sqrt2_power_requested_half_transport import prove_requested_half_transport
        result = prove_requested_half_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="derive_requested_dyadic_half_root_comparison_error_for_the_unchanged_n_plus_eight_sample_by_constructing_actual_powers_and_replaying_AP015_scale_cancellation_preserving_independent_positive_heads_and_original_degree")
    elif identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import prove_natural_gap, prove_norm_separation
        result = prove_natural_gap() if identifier == "NG001" else prove_norm_separation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage=("universal_natural_gap_not_full_campaign"
            if identifier == "NG001" else "signed_norm_integer_gap_not_full_IR032"))
    elif identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import prove_quadratic_norm_product
        result = prove_quadratic_norm_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_norm_multiplicativity_not_rational_IR031")
    elif identifier == "SN001":
        from sqrt2_power_signed_norm import prove_signed_norm_zero
        result = prove_signed_norm_zero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_norm_zero_core_not_IR032")
    elif identifier == "IR016":
        from sqrt2_power_even_square import prove_ir016
        result = prove_ir016()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="IR016_natural_core_not_full_irrationality")
    elif identifier == "P10":
        from sqrt2_power_binary_dag import prove_p10
        result = prove_p10()
        payload = result.payload
        diagnostics = dict(strategy="per_operation_shared_ordinary_HA_DAG",
            local_nodes=len(result.bundle.nodes), body_nodes=result.receipt.total_body_nodes,
            max_proof_depth=result.max_proof_depth, basis_names=result.basis_names,
            subleaf_node=result.subleaf_node, coverage="full_fixed_P10_not_IR064")
    elif identifier in CHUNK_CASES:
        from sqrt2_power_composition_chunks import prove_chunk
        from sqrt2_power_native import Basis
        result = prove_chunk(identifier, Basis(), expected_ast_sha256=formula_sha256(target))
        payload = result.bundle_certificate.payload
        diagnostics = result.manifest
    elif identifier.startswith("P04-"):
        from sqrt2_power_formal_composition import prove_ground_instance_dag, prove_trace_soundness
        from sqrt2_power_native import Basis
        if identifier == "P04-ground":
            result = prove_ground_instance_dag(Basis(), expected_ast_sha256=formula_sha256(target))
            payload = result.bundle_certificate.payload
            diagnostics = result.manifest
        else:
            result = prove_trace_soundness(Basis(), expected_ast_sha256=formula_sha256(target))
            payload = encode_proof_bundle(ProofBundle((BundleNode(0, target, (), result.certificate),), 0), target, limits=LIMITS)
            diagnostics = result.manifest
    elif identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import prove_foundation
        actual, proof, diagnostics = prove_foundation(FOUNDATION_CASES[identifier])
        if actual != target:
            raise ValueError("foundation differs from named target")
        payload = encode_proof_bundle(ProofBundle((BundleNode(0, target, (), proof),), 0), target, limits=LIMITS)
        diagnostics = dict(diagnostics, coverage="full_named_rational_foundation_not_IR001",
            solver_role="independent_Z3_conjecture_check_not_imported_in_native_proof")
    else:
        from sqrt2_power_solver_hints import reconstruct_p08
        if type(hint) is not dict or set(hint) != {"problem", "observed", "contract"}:
            raise ValueError("actual source-bound solver hint required")
        if hint["observed"].get("solver") != identifier[4:]:
            raise ValueError("wrong solver hint")
        actual, proof, diagnostics = reconstruct_p08(hint["problem"], hint["observed"], hint["contract"])
        if actual != target:
            raise ValueError("reconstruction changed target")
        bundle = ProofBundle((BundleNode(0, target, (), proof),), 0)
        payload = encode_proof_bundle(bundle, target, limits=LIMITS)
        receipt = check_proof_bundle(bundle, target, limits=LIMITS)
        diagnostics = dict(diagnostics, body_nodes=receipt.total_body_nodes,
            coverage="P08_supporting_leaf_not_full_pilot")
    if before != pins(identifier):
        raise ValueError("sources changed during generation")
    return dict(schema=SCHEMA, case=identifier, status="native_generated",
        source_pins=before, target_ast_sha256=formula_sha256(target), bundle=payload,
        bundle_sha256=sha256(payload.encode()).hexdigest(), diagnostics=diagnostics,
        IR_parents_closed=0, model_proof_search_calls=0, independent_lean_checked=False)


def check_forged_root_rejection(bundle):
    """Test the exact bad local body after complete ordinary bundle replay.

    This is precisely the empty-context kernel obligation used for that row
    by check_proof_bundle. No ancestor is assumed as an axiom: dependencies
    are explicit antecedents of the closed curried goal. Replaying already
    checked, unchanged ancestors again is unnecessary for this negative test.
    This helper never establishes the positive bundle or any dependency.
    """
    from peano_lab.kernel import checker as kernel_checker
    from peano_lab.kernel.formulas import Imp
    table = {node.node_id:node for node in bundle.nodes}
    node = table[bundle.root]
    curried = node.target
    for dependency in reversed(node.dependencies):
        curried = Imp(table[dependency].target,curried)
    if kernel_checker.check((),EqRefl(Zero()),curried):
        raise ValueError("forged root accepted by ordinary local kernel check")


def replay(identifier, value):
    before = pins(identifier)
    target = target_for(identifier)
    if (type(value) is not dict or value.get("schema") != SCHEMA
        or value.get("case") != identifier or value.get("source_pins") != before
        or value.get("status") != "native_generated"
        or value.get("target_ast_sha256") != formula_sha256(target)):
        raise ValueError("changed or unbound producer output")
    payload = value.get("bundle")
    if type(payload) is not str or sha256(payload.encode()).hexdigest() != value.get("bundle_sha256"):
        raise ValueError("changed certificate bytes")
    bundle, encoded_target = decode_proof_bundle(payload, limits=LIMITS)
    if encoded_target != target:
        raise ValueError("bundle does not prove exact independently bound target")
    receipt = check_proof_bundle(bundle, target, limits=LIMITS)
    try:
        check_proof_bundle(bundle,Bot(),limits=LIMITS)
    except ProofBundleError:
        pass
    else:
        raise ValueError("false target accepted")
    check_forged_root_rejection(bundle)
    if before != pins(identifier):
        raise ValueError("sources changed during fresh replay")
    return dict(schema=SCHEMA, case=identifier, status="fresh_ordinary_HA_checked",
        target_ast_sha256=formula_sha256(target), bundle_sha256=value["bundle_sha256"],
        source_pins=before, local_nodes=len(bundle.nodes), proof_nodes=receipt.total_body_nodes,
        kernel_calls=receipt.kernel_calls, original_target_checked=True,
        empty_context=True, false_target_rejected=True, forged_body_rejected=True,
        forged_body_check_scope="exact_curried_root_in_ordinary_kernel_after_complete_positive_bundle_replay",
        IR_parents_closed=0, library_admissions=0, independent_lean_checked=False)


def generation_phase_limits(identifier):
    """Recorded CV085 protocol-only retry: redistribute, never enlarge, 58 CPU."""
    return (30,40) if identifier=="CV085" else (28,40)


def replay_phase_limits(identifier):
    """Recorded owner-approved phase allocations for AP089 and AP090.

    AP089 keeps generation at 28 seconds: (28+1)+(30+1)=60 including
    hard-limit margins. The approval covers one additional v3 attempt only,
    not further retries, another case, or any larger aggregate/kernel cap.
    A subsequent explicit approval covers one AP090 v1 attempt with the
    same allocation, not a general extension to later cases or retries.
    """
    if identifier=="AP089":
        return (30,40)
    if identifier=="AP090":
        return (30,40)
    return (26,40) if identifier=="CV085" else (20,30)


def run(identifier, output, vampire=None):
    if output.exists() or output.is_symlink():
        raise ValueError("observation path must be new")
    before = pins(identifier)
    started = time.monotonic()
    deadline = started + 90
    records, results = {}, {}
    report = dict(schema=SCHEMA, case=identifier, source_pins=before,
        authority="local_observation_not_library_admission", source_snapshots={},
        status="not_checked", IR_parents_closed=0, library_admissions=0,
        independent_lean_checked=False, model_proof_search_calls=0)
    with controller_deadline(deadline):
        budget = LeafBudget(deadline)
        worker_input = b""
        if identifier.startswith("P08-"):
            from sqrt2_power_external import ExternalBudget, export_problem, invoke_solver
            from sqrt2_power_pilot_contracts import contracts
            contract = next(r for r in contracts() if r["pilot_id"] == "P08")
            solver = identifier[4:]
            problem = export_problem(contract["source"], tuple((r["name"], r["source"])
                for r in contract["allowed_external_premises"]), format="tptp")
            external_budget = ExternalBudget(cpu_seconds=6, wall_seconds=8)
            observed = invoke_solver(problem, solver, budget=external_budget, seconds=2,
                executable=vampire if solver == "vampire" else None)
            # Same outer case budget; no reservation refund after a fast solver.
            budget.reserved_cpu += external_budget.snapshot()["cpu_hard_limit_reserved_seconds"]
            hint = dict(problem=problem, observed=observed, contract=contract)
            worker_input = canonical(hint)
            save_new(output / "live-solver-input-and-observation.json.gz", gzip.compress(worker_input, mtime=0))
            report["live_external"] = dict(solver=solver, status=observed["observation"],
                binary=observed["capability"].get("binary"), budget=external_budget.snapshot(),
                observation_sha256=sha256(worker_input).hexdigest(), HA_authority=False)
        elif identifier in FOUNDATION_CASES or identifier in ("NG001", "RN001", "RN002", "SI001", "QH001"):
            from sqrt2_power_external import ExternalBudget, export_problem, invoke_solver
            from peano_lab.kernel.formulas import pretty_formula
            problem = export_problem(pretty_formula(target_for(identifier), []), format="smt2")
            external_budget = ExternalBudget(cpu_seconds=6, wall_seconds=8)
            observed = invoke_solver(problem, "z3", budget=external_budget, seconds=2)
            budget.reserved_cpu += external_budget.snapshot()["cpu_hard_limit_reserved_seconds"]
            raw_external = canonical(dict(problem=problem, observed=observed))
            save_new(output / "live-solver-input-and-observation.json.gz", gzip.compress(raw_external, mtime=0))
            report["live_external"] = dict(solver="z3", status=observed["observation"],
                binary=observed["capability"].get("binary"), budget=external_budget.snapshot(),
                observation_sha256=sha256(raw_external).hexdigest(), HA_authority=False,
                role="independent_conjecture_check_not_used_for_reconstruction")
        generation_cpu,generation_wall = generation_phase_limits(identifier)
        generated = budget.run((sys.executable, "-B", str(SCRIPT), "--worker", identifier),
            cpu=generation_cpu, wall=generation_wall, input_bytes=worker_input)
        records["generation"] = generated
        if successful(generated):
            value = json.loads(generated["stdout"])
            if value.get("source_pins") != before:
                raise ValueError("producer did not use controller sources")
            results["generation"] = {k:v for k,v in value.items() if k != "bundle"}
            replay_cpu,replay_wall = replay_phase_limits(identifier)
            checked = budget.run((sys.executable, "-B", str(SCRIPT), "--replay", identifier),
                cpu=replay_cpu, wall=replay_wall, input_bytes=canonical(value))
            records["fresh_replay"] = checked
            if successful(checked):
                accepted = json.loads(checked["stdout"])
                if (accepted.get("status") != "fresh_ordinary_HA_checked"
                    or accepted.get("source_pins") != before
                    or accepted.get("bundle_sha256") != value.get("bundle_sha256")):
                    raise ValueError("unexpected fresh replay result")
                results["fresh_replay"] = accepted
                report["status"] = "fresh_ordinary_HA_checked"
        if pins(identifier) != before:
            raise ValueError("controller inputs changed before archival")
        for name, pin in before.items():
            raw = (ROOT / name).read_bytes()
            if sha256(raw).hexdigest() != pin["sha256"] or len(raw) != pin["bytes"]:
                raise ValueError("changed source snapshot")
            stored = "sources/" + name + ".gz"
            save_new(output / stored, gzip.compress(raw, mtime=0))
            report["source_snapshots"][name] = stored
        for phase, process in records.items():
            raw = canonical(process)
            save_new(output / (phase + "-process.json.gz"), gzip.compress(raw, mtime=0))
        report.update(results=results, process_records={phase: dict(path=phase+"-process.json.gz",
            raw_sha256=sha256(canonical(process)).hexdigest(), reason=process["reason"],
            returncode=process["returncode"], resources=process["resources"])
            for phase, process in records.items() if process is not None},
            elapsed_wall_seconds=time.monotonic()-started,
            budget=dict(cpu_seconds=60, wall_seconds=90, max_workers=1, rss_bytes=768*1024**2,
                reserved_cpu_seconds=budget.reserved_cpu,
                note="CPU reservations include each worker's one-second hard-limit margin"))
        save_new(output / "report.json", json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return {key: report[key] for key in ("case", "status", "elapsed_wall_seconds", "process_records")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker", choices=CASES)
    group.add_argument("--replay", choices=CASES)
    group.add_argument("--run", choices=CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--vampire", type=Path)
    args = parser.parse_args()
    if args.worker:
        hint = None
        if args.worker.startswith("P08-"):
            raw = sys.stdin.buffer.read(8*1024**2+1)
            if len(raw) > 8*1024**2:
                raise ValueError("solver hint input exceeds bound")
            hint = json.loads(raw)
        value = worker(args.worker, hint)
    elif args.replay:
        raw = sys.stdin.buffer.read(8*1024**2+1)
        if len(raw) > 8*1024**2:
            raise ValueError("replay input exceeds bound")
        value = replay(args.replay, json.loads(raw))
    else:
        if args.output is None:
            parser.error("--run requires --output")
        value = run(args.run, args.output, args.vampire)
    if "peano_lab.library.theorems" in sys.modules:
        raise ValueError("worker unexpectedly imported full theorem registry")
    print(canonical(value).decode(), flush=True)
