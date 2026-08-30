"use strict";
/*
 * Peano Lab evaluation worker.
 *
 * Pyodide, the tactic engine, and the independent PA kernel all run off the
 * main thread. Terminating this worker is therefore a real Stop operation: a
 * divergent search cannot leave the page unresponsive.
 *
 * Protocol:
 *   main -> worker : {type: "init", build}
 *                    {type: "run", id, line}
 *   worker -> main : {type: "boot", msg}
 *                    {type: "ready", banner}
 *                    {type: "error", msg}
 *                    {type: "result", id, out, failed, download: null|string}
 */

const PY_FILES = [
  "py/peano_lab/__init__.py",
  "py/peano_lab/batch.py",
  "py/peano_lab/engine/__init__.py",
  "py/peano_lab/engine/compact_arith.py",
  "py/peano_lab/engine/decide.py",
  "py/peano_lab/engine/induction.py",
  "py/peano_lab/engine/norm_num.py",
  "py/peano_lab/engine/proof_reduction.py",
  "py/peano_lab/engine/rewrite.py",
  "py/peano_lab/engine/ring.py",
  "py/peano_lab/engine/search.py",
  "py/peano_lab/engine/state.py",
  "py/peano_lab/engine/tacticals.py",
  "py/peano_lab/engine/tactics.py",
  "py/peano_lab/engine/trace.py",
  "py/peano_lab/experimental/__init__.py",
  "py/peano_lab/experimental/closed_proof_dag.py",
  "py/peano_lab/experimental/layered_cut_bundle.py",
  "py/peano_lab/experimental/quadratic_reciprocity_layered.py",
  "py/peano_lab/kernel/__init__.py",
  "py/peano_lab/kernel/checker.py",
  "py/peano_lab/kernel/formulas.py",
  "py/peano_lab/kernel/proofs.py",
  "py/peano_lab/kernel/subst.py",
  "py/peano_lab/kernel/terms.py",
  "py/peano_lab/library/__init__.py",
  "py/peano_lab/library/alpha_enrollment.py",
  "py/peano_lab/library/alpha_enrollment_v10.py",
  "py/peano_lab/library/alpha_enrollment_v11.py",
  "py/peano_lab/library/alpha_enrollment_v12.py",
  "py/peano_lab/library/alpha_enrollment_v13.py",
  "py/peano_lab/library/alpha_enrollment_v14.py",
  "py/peano_lab/library/alpha_enrollment_v15.py",
  "py/peano_lab/library/alpha_enrollment_v19.py",
  "py/peano_lab/library/alpha_enrollment_v2.py",
  "py/peano_lab/library/alpha_enrollment_v20.py",
  "py/peano_lab/library/alpha_enrollment_v21.py",
  "py/peano_lab/library/alpha_enrollment_v22.py",
  "py/peano_lab/library/alpha_enrollment_v23.py",
  "py/peano_lab/library/alpha_enrollment_v24.py",
  "py/peano_lab/library/alpha_enrollment_v25.py",
  "py/peano_lab/library/alpha_enrollment_v26.py",
  "py/peano_lab/library/alpha_enrollment_v27.py",
  "py/peano_lab/library/alpha_enrollment_v28.py",
  "py/peano_lab/library/alpha_enrollment_v29.py",
  "py/peano_lab/library/alpha_enrollment_v3.py",
  "py/peano_lab/library/alpha_enrollment_v30.py",
  "py/peano_lab/library/alpha_enrollment_v31.py",
  "py/peano_lab/library/alpha_enrollment_v32.py",
  "py/peano_lab/library/alpha_enrollment_v4.py",
  "py/peano_lab/library/alpha_enrollment_v5.py",
  "py/peano_lab/library/alpha_enrollment_v6.py",
  "py/peano_lab/library/alpha_enrollment_v7.py",
  "py/peano_lab/library/alpha_enrollment_v8.py",
  "py/peano_lab/library/alpha_enrollment_v9.py",
  "py/peano_lab/library/arithmetic_multiplicative_candidate.py",
  "py/peano_lab/library/arithmetic_table_extension_candidate.py",
  "py/peano_lab/library/bertrand_b5_central_upper_candidate.py",
  "py/peano_lab/library/bertrand_b5_contribution_split_candidate.py",
  "py/peano_lab/library/bertrand_b5_order_quotient_candidate.py",
  "py/peano_lab/library/bertrand_b5_range_boundaries_candidate.py",
  "py/peano_lab/library/bertrand_b6_growth_candidate.py",
  "py/peano_lab/library/bertrand_b6_main_inequality_candidate.py",
  "py/peano_lab/library/bertrand_b7_eventual_candidate.py",
  "py/peano_lab/library/bertrand_b8_covering_candidate.py",
  "py/peano_lab/library/bertrand_b8_prime_certificates_candidate.py",
  "py/peano_lab/library/bertrand_b8_small_candidate.py",
  "py/peano_lab/library/bertrand_balanced_v1_successor_candidate.py",
  "py/peano_lab/library/bertrand_bp01_candidate.py",
  "py/peano_lab/library/bertrand_bp02_candidate.py",
  "py/peano_lab/library/bertrand_ceil_sqrt_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_carry_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_factor_ranges_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_growth_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_lower_bound_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_lower_seed_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_prime_support_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_recurrence_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_square_tail_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_succ_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_upper_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_valuation_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_zero_candidate.py",
  "py/peano_lab/library/bertrand_central_binom_zero_range_candidate.py",
  "py/peano_lab/library/bertrand_choose_diagonal_candidate.py",
  "py/peano_lab/library/bertrand_choose_factorial_bridge_candidate.py",
  "py/peano_lab/library/bertrand_choose_factorial_support_candidate.py",
  "py/peano_lab/library/bertrand_choose_foundation_candidate.py",
  "py/peano_lab/library/bertrand_choose_laws_candidate.py",
  "py/peano_lab/library/bertrand_choose_pascal_candidate.py",
  "py/peano_lab/library/bertrand_choose_positive_candidate.py",
  "py/peano_lab/library/bertrand_choose_recurrence_candidate.py",
  "py/peano_lab/library/bertrand_choose_row_functional_candidate.py",
  "py/peano_lab/library/bertrand_choose_symmetry_candidate.py",
  "py/peano_lab/library/bertrand_choose_table_row_functional_candidate.py",
  "py/peano_lab/library/bertrand_choose_weighted_vertical_candidate.py",
  "py/peano_lab/library/bertrand_complete_closure.py",
  "py/peano_lab/library/bertrand_defined_edition.py",
  "py/peano_lab/library/bertrand_factorial_legendre_candidate.py",
  "py/peano_lab/library/bertrand_factorial_valuation_candidate.py",
  "py/peano_lab/library/bertrand_floor_sqrt_total_candidate.py",
  "py/peano_lab/library/bertrand_hj_all_s_candidate.py",
  "py/peano_lab/library/bertrand_hj_base_thirty_two_candidate.py",
  "py/peano_lab/library/bertrand_hj_base_window_candidate.py",
  "py/peano_lab/library/bertrand_hj_transport_candidate.py",
  "py/peano_lab/library/bertrand_initial_segment_constructor_candidate.py",
  "py/peano_lab/library/bertrand_integer_envelope_candidate.py",
  "py/peano_lab/library/bertrand_legendre_recurrence_candidate.py",
  "py/peano_lab/library/bertrand_legendre_successor_candidate.py",
  "py/peano_lab/library/bertrand_legendre_sum_candidate.py",
  "py/peano_lab/library/bertrand_legendre_valuation_bridge_candidate.py",
  "py/peano_lab/library/bertrand_power_bridge_candidate.py",
  "py/peano_lab/library/bertrand_power_divisibility_candidate.py",
  "py/peano_lab/library/bertrand_power_growth_candidate.py",
  "py/peano_lab/library/bertrand_power_order_candidate.py",
  "py/peano_lab/library/bertrand_power_seed_balanced_candidate.py",
  "py/peano_lab/library/bertrand_power_total_candidate.py",
  "py/peano_lab/library/bertrand_power_valuation_candidate.py",
  "py/peano_lab/library/bertrand_power_valuation_laws_candidate.py",
  "py/peano_lab/library/bertrand_prime_campaign_candidate.py",
  "py/peano_lab/library/bertrand_prime_contribution_candidate.py",
  "py/peano_lab/library/bertrand_prime_contribution_complete_candidate.py",
  "py/peano_lab/library/bertrand_prime_interval_candidate.py",
  "py/peano_lab/library/bertrand_primorial_choose_interval_candidate.py",
  "py/peano_lab/library/bertrand_primorial_duplicate_free_candidate.py",
  "py/peano_lab/library/bertrand_primorial_foundation_candidate.py",
  "py/peano_lab/library/bertrand_primorial_four_power_candidate.py",
  "py/peano_lab/library/bertrand_primorial_interval_candidate.py",
  "py/peano_lab/library/bertrand_primorial_membership_candidate.py",
  "py/peano_lab/library/bertrand_promotion.py",
  "py/peano_lab/library/bertrand_quotient_budget_candidate.py",
  "py/peano_lab/library/bertrand_threshold_base_candidate.py",
  "py/peano_lab/library/binary_digit_extraction_candidate.py",
  "py/peano_lab/library/binary_length_candidate.py",
  "py/peano_lab/library/binary_modular_execution_candidate.py",
  "py/peano_lab/library/binary_modular_exponentiation_candidate.py",
  "py/peano_lab/library/campaign_advanced_layer_closure.py",
  "py/peano_lab/library/campaign_bottom_layer_closure.py",
  "py/peano_lab/library/campaign_breakthrough_layer_closure.py",
  "py/peano_lab/library/campaign_completed_lower_closure.py",
  "py/peano_lab/library/campaign_first_wave_closure.py",
  "py/peano_lab/library/campaign_frontier_closure.py",
  "py/peano_lab/library/campaign_gaussian_factorization_closure.py",
  "py/peano_lab/library/campaign_lower_layer_closure.py",
  "py/peano_lab/library/campaign_milestone_closure.py",
  "py/peano_lab/library/campaign_next_layer_closure.py",
  "py/peano_lab/library/campaign_priority_layer_closure.py",
  "py/peano_lab/library/campaign_research_layer_closure.py",
  "py/peano_lab/library/campaign_research_v32_closure.py",
  "py/peano_lab/library/campaign_residual_closure.py",
  "py/peano_lab/library/campaign_second_wave_closure.py",
  "py/peano_lab/library/campaign_transport_layer_closure.py",
  "py/peano_lab/library/candidate_validation.py",
  "py/peano_lab/library/cauchy_davenport_candidate.py",
  "py/peano_lab/library/continued_fraction_approximation_candidate.py",
  "py/peano_lab/library/continued_fraction_candidate.py",
  "py/peano_lab/library/continued_fraction_convergents_candidate.py",
  "py/peano_lab/library/coprime_divisor_decomposition_candidate.py",
  "py/peano_lab/library/coprime_square_factor_candidate.py",
  "py/peano_lab/library/cornacchia_candidate.py",
  "py/peano_lab/library/defined_edition.py",
  "py/peano_lab/library/defined_syntax.py",
  "py/peano_lab/library/dirichlet_associativity_candidate.py",
  "py/peano_lab/library/dirichlet_commutativity_candidate.py",
  "py/peano_lab/library/dirichlet_convolution_candidate.py",
  "py/peano_lab/library/dirichlet_fubini_candidate.py",
  "py/peano_lab/library/dirichlet_inverse_candidate.py",
  "py/peano_lab/library/dirichlet_multiplicative_candidate.py",
  "py/peano_lab/library/dirichlet_multiplicative_entry_candidate.py",
  "py/peano_lab/library/dirichlet_multiplicative_support_candidate.py",
  "py/peano_lab/library/dirichlet_signed_unit_candidate.py",
  "py/peano_lab/library/dirichlet_triangular_candidate.py",
  "py/peano_lab/library/dirichlet_units_candidate.py",
  "py/peano_lab/library/distinct_primes_nondivisibility_candidate.py",
  "py/peano_lab/library/divisor_involution_candidate.py",
  "py/peano_lab/library/divisor_mask_candidate.py",
  "py/peano_lab/library/divisor_pair_index_candidate.py",
  "py/peano_lab/library/divisor_sum_algebra_candidate.py",
  "py/peano_lab/library/divisor_sum_reindex_candidate.py",
  "py/peano_lab/library/divisor_sum_table_candidate.py",
  "py/peano_lab/library/editions.py",
  "py/peano_lab/library/editions_v10.py",
  "py/peano_lab/library/editions_v11.py",
  "py/peano_lab/library/editions_v12.py",
  "py/peano_lab/library/editions_v13.py",
  "py/peano_lab/library/editions_v14.py",
  "py/peano_lab/library/editions_v15.py",
  "py/peano_lab/library/editions_v16.py",
  "py/peano_lab/library/editions_v17.py",
  "py/peano_lab/library/editions_v18.py",
  "py/peano_lab/library/editions_v19.py",
  "py/peano_lab/library/editions_v2.py",
  "py/peano_lab/library/editions_v20.py",
  "py/peano_lab/library/editions_v21.py",
  "py/peano_lab/library/editions_v22.py",
  "py/peano_lab/library/editions_v23.py",
  "py/peano_lab/library/editions_v24.py",
  "py/peano_lab/library/editions_v25.py",
  "py/peano_lab/library/editions_v26.py",
  "py/peano_lab/library/editions_v27.py",
  "py/peano_lab/library/editions_v28.py",
  "py/peano_lab/library/editions_v29.py",
  "py/peano_lab/library/editions_v3.py",
  "py/peano_lab/library/editions_v30.py",
  "py/peano_lab/library/editions_v31.py",
  "py/peano_lab/library/editions_v32.py",
  "py/peano_lab/library/editions_v4.py",
  "py/peano_lab/library/editions_v5.py",
  "py/peano_lab/library/editions_v6.py",
  "py/peano_lab/library/editions_v7.py",
  "py/peano_lab/library/editions_v8.py",
  "py/peano_lab/library/editions_v9.py",
  "py/peano_lab/library/eisenstein_division_threshold_candidate.py",
  "py/peano_lab/library/eisenstein_euclidean_candidate.py",
  "py/peano_lab/library/eisenstein_fubini_row_decomposition_candidate.py",
  "py/peano_lab/library/eisenstein_fubini_total_candidate.py",
  "py/peano_lab/library/eisenstein_initial_segment_count_candidate.py",
  "py/peano_lab/library/eisenstein_lattice_orientation_candidate.py",
  "py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py",
  "py/peano_lab/library/eisenstein_quotient_bound_candidate.py",
  "py/peano_lab/library/eisenstein_quotient_sum_identity_candidate.py",
  "py/peano_lab/library/eisenstein_rectangle_count_candidate.py",
  "py/peano_lab/library/eisenstein_remainder_nonzero_candidate.py",
  "py/peano_lab/library/eisenstein_row_indicator_candidate.py",
  "py/peano_lab/library/eisenstein_row_quotient_candidate.py",
  "py/peano_lab/library/eisenstein_scaled_division_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_cell_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_column_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_column_count_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py",
  "py/peano_lab/library/euclidean_complexity_candidate.py",
  "py/peano_lab/library/euclidean_gcd_transport_candidate.py",
  "py/peano_lab/library/euclidean_logarithmic_bound_candidate.py",
  "py/peano_lab/library/euler_criterion_arbitrary_candidate.py",
  "py/peano_lab/library/euler_criterion_bounded_candidate.py",
  "py/peano_lab/library/euler_criterion_residue_candidate.py",
  "py/peano_lab/library/euler_nonresidue_endpoint_candidate.py",
  "py/peano_lab/library/euler_pair_product_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_prefix_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_prefix_extensional_candidate.py",
  "py/peano_lab/library/euler_scaled_pair_order_entrance_candidate.py",
  "py/peano_lab/library/euler_scaled_pair_order_iteration_candidate.py",
  "py/peano_lab/library/euler_totient_algebra_candidate.py",
  "py/peano_lab/library/euler_totient_count_candidate.py",
  "py/peano_lab/library/euler_totient_interval_candidate.py",
  "py/peano_lab/library/euler_totient_prime_step_candidate.py",
  "py/peano_lab/library/euler_totient_product_candidate.py",
  "py/peano_lab/library/euler_units_candidate.py",
  "py/peano_lab/library/euler_units_product_candidate.py",
  "py/peano_lab/library/euler_units_residue_candidate.py",
  "py/peano_lab/library/fermat_endpoints_candidate.py",
  "py/peano_lab/library/fermat_four_descent_candidate.py",
  "py/peano_lab/library/fermat_product_balance_candidate.py",
  "py/peano_lab/library/fermat_residue_map_candidate.py",
  "py/peano_lab/library/fermat_residue_product_candidate.py",
  "py/peano_lab/library/fermat_residue_reindex_candidate.py",
  "py/peano_lab/library/fermat_scale_product_candidate.py",
  "py/peano_lab/library/fermat_two_squares_brahmagupta_candidate.py",
  "py/peano_lab/library/fermat_two_squares_candidate.py",
  "py/peano_lab/library/fermat_two_squares_classification_candidate.py",
  "py/peano_lab/library/fermat_two_squares_collision_norm_candidate.py",
  "py/peano_lab/library/fermat_two_squares_factor_fold_candidate.py",
  "py/peano_lab/library/fermat_two_squares_pairing_candidate.py",
  "py/peano_lab/library/fermat_two_squares_pigeonhole_candidate.py",
  "py/peano_lab/library/fermat_two_squares_prime_candidate.py",
  "py/peano_lab/library/fermat_two_squares_residue_grid_candidate.py",
  "py/peano_lab/library/fermat_two_squares_valuation_candidate.py",
  "py/peano_lab/library/finite_bitcount_complement_candidate.py",
  "py/peano_lab/library/finite_bitcount_theorems.py",
  "py/peano_lab/library/finite_congruence_theorems.py",
  "py/peano_lab/library/finite_division_prefix_candidate.py",
  "py/peano_lab/library/finite_factorial_theorems.py",
  "py/peano_lab/library/finite_fold_surface.py",
  "py/peano_lab/library/finite_fold_theorems.py",
  "py/peano_lab/library/finite_modular_set_candidate.py",
  "py/peano_lab/library/finite_omission_candidate.py",
  "py/peano_lab/library/finite_permutation_theorems.py",
  "py/peano_lab/library/finite_pointwise_mul_product_candidate.py",
  "py/peano_lab/library/finite_pointwise_mul_recode_candidate.py",
  "py/peano_lab/library/finite_prefix_collision_decision_candidate.py",
  "py/peano_lab/library/finite_prime_product_coprime_candidate.py",
  "py/peano_lab/library/finite_product_order_candidate.py",
  "py/peano_lab/library/finite_product_permutation_theorems.py",
  "py/peano_lab/library/finite_product_prefix_suffix_candidate.py",
  "py/peano_lab/library/finite_product_reindex_candidate.py",
  "py/peano_lab/library/finite_product_reindex_support.py",
  "py/peano_lab/library/finite_range_theorems.py",
  "py/peano_lab/library/finite_repeat_sum_candidate.py",
  "py/peano_lab/library/finite_sum_permutation_candidate.py",
  "py/peano_lab/library/finite_sum_pointwise_add_candidate.py",
  "py/peano_lab/library/finite_sum_pointwise_mod_candidate.py",
  "py/peano_lab/library/finite_sum_reindex_candidate.py",
  "py/peano_lab/library/finite_sum_theorems.py",
  "py/peano_lab/library/finite_sum_transport_candidate.py",
  "py/peano_lab/library/formula_dag.py",
  "py/peano_lab/library/foundation_saturation_candidate.py",
  "py/peano_lab/library/four_square_bounded_seed_candidate.py",
  "py/peano_lab/library/four_square_branch_descent_candidate.py",
  "py/peano_lab/library/four_square_complete_closure.py",
  "py/peano_lab/library/four_square_conjugate_identity_candidate.py",
  "py/peano_lab/library/four_square_cross_pigeonhole_candidate.py",
  "py/peano_lab/library/four_square_descent_candidate.py",
  "py/peano_lab/library/four_square_euler_candidate.py",
  "py/peano_lab/library/four_square_frontier_promotion.py",
  "py/peano_lab/library/four_square_identity_candidate.py",
  "py/peano_lab/library/four_square_lagrange_bridge_candidate.py",
  "py/peano_lab/library/four_square_lagrange_candidate.py",
  "py/peano_lab/library/four_square_lagrange_final_candidate.py",
  "py/peano_lab/library/four_square_parity_selection_candidate.py",
  "py/peano_lab/library/four_square_residue_intersection_candidate.py",
  "py/peano_lab/library/four_square_signed_block_negative_candidate.py",
  "py/peano_lab/library/four_square_signed_cases_candidate.py",
  "py/peano_lab/library/four_square_signed_orientation_candidate.py",
  "py/peano_lab/library/four_square_signed_quaternion_candidate.py",
  "py/peano_lab/library/frontier_promotion.py",
  "py/peano_lab/library/gauss_count_sum_parity_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_data_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_pointwise_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_sum_candidate.py",
  "py/peano_lab/library/gauss_half_range.py",
  "py/peano_lab/library/gauss_lemma_arbitrary_candidate.py",
  "py/peano_lab/library/gauss_lemma_bounded_candidate.py",
  "py/peano_lab/library/gauss_lemma_endpoint_candidate.py",
  "py/peano_lab/library/gauss_magnitude_coprime_candidate.py",
  "py/peano_lab/library/gauss_magnitude_permutation_candidate.py",
  "py/peano_lab/library/gauss_magnitude_product_candidate.py",
  "py/peano_lab/library/gauss_product_composition_candidate.py",
  "py/peano_lab/library/gauss_sign_bridge.py",
  "py/peano_lab/library/gauss_sign_factor_recode_candidate.py",
  "py/peano_lab/library/gauss_sign_product_candidate.py",
  "py/peano_lab/library/gauss_signed_division_alignment_candidate.py",
  "py/peano_lab/library/gauss_signed_half_candidate.py",
  "py/peano_lab/library/gauss_signed_pointwise_product_candidate.py",
  "py/peano_lab/library/gauss_signed_prefix_candidate.py",
  "py/peano_lab/library/gaussian_divisibility_candidate.py",
  "py/peano_lab/library/gaussian_euclidean_candidate.py",
  "py/peano_lab/library/gaussian_factor_permutation_candidate.py",
  "py/peano_lab/library/gaussian_factor_search_candidate.py",
  "py/peano_lab/library/gaussian_factorization_candidate.py",
  "py/peano_lab/library/gaussian_gcd_candidate.py",
  "py/peano_lab/library/gaussian_product_reindex_candidate.py",
  "py/peano_lab/library/gaussian_ring_candidate.py",
  "py/peano_lab/library/generalized_crt_compatibility_candidate.py",
  "py/peano_lab/library/generalized_crt_fold_candidate.py",
  "py/peano_lab/library/generalized_crt_full_candidate.py",
  "py/peano_lab/library/ha_canonical_congruence_candidate.py",
  "py/peano_lab/library/ha_canonical_gcd_candidate.py",
  "py/peano_lab/library/ha_canonical_gcd_edges_candidate.py",
  "py/peano_lab/library/ha_canonical_remainder_candidate.py",
  "py/peano_lab/library/ha_cell_bounds_candidate.py",
  "py/peano_lab/library/ha_cell_functional_candidate.py",
  "py/peano_lab/library/ha_cell_history_candidate.py",
  "py/peano_lab/library/ha_cell_history_prefix_preservation_candidate.py",
  "py/peano_lab/library/ha_cell_list_equations_candidate.py",
  "py/peano_lab/library/ha_cell_list_extensional_candidate.py",
  "py/peano_lab/library/ha_cell_list_interface_candidate.py",
  "py/peano_lab/library/ha_cell_list_length_bound_candidate.py",
  "py/peano_lab/library/ha_cell_list_length_functional_candidate.py",
  "py/peano_lab/library/ha_cell_list_length_total_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_domain_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_exists_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_external_bound_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_functional_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_head_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_history_independent_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_succ_candidate.py",
  "py/peano_lab/library/ha_cell_list_lookup_surface_candidate.py",
  "py/peano_lab/library/ha_cell_list_membership_candidate.py",
  "py/peano_lab/library/ha_cell_list_membership_surface_candidate.py",
  "py/peano_lab/library/ha_cell_list_validity_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_classification_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_congruence_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_decision_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py",
  "py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py",
  "py/peano_lab/library/ha_lcm_totality_bridge_candidate.py",
  "py/peano_lab/library/ha_modular_inverse_candidate.py",
  "py/peano_lab/library/ha_pair_cell_seed_candidate.py",
  "py/peano_lab/library/ha_pair_injective_candidate.py",
  "py/peano_lab/library/ha_pair_shell_candidate.py",
  "py/peano_lab/library/ha_relational_lcm_candidate.py",
  "py/peano_lab/library/ha_signed_add_associative_candidate.py",
  "py/peano_lab/library/ha_signed_add_candidate.py",
  "py/peano_lab/library/ha_signed_add_laws_candidate.py",
  "py/peano_lab/library/ha_signed_balance_candidate.py",
  "py/peano_lab/library/ha_signed_balance_complete_candidate.py",
  "py/peano_lab/library/ha_signed_bezout_candidate.py",
  "py/peano_lab/library/ha_signed_bezout_gcd_candidate.py",
  "py/peano_lab/library/ha_signed_code_extensional_candidate.py",
  "py/peano_lab/library/ha_signed_decode_candidate.py",
  "py/peano_lab/library/ha_signed_mul_associative_candidate.py",
  "py/peano_lab/library/ha_signed_mul_candidate.py",
  "py/peano_lab/library/ha_signed_mul_distributive_candidate.py",
  "py/peano_lab/library/ha_signed_mul_laws_candidate.py",
  "py/peano_lab/library/ha_signed_nat_scale_candidate.py",
  "py/peano_lab/library/ha_signed_nat_scale_laws_candidate.py",
  "py/peano_lab/library/ha_signed_negate_candidate.py",
  "py/peano_lab/library/ha_signed_parity_candidate.py",
  "py/peano_lab/library/hensel_prime_power_candidate.py",
  "py/peano_lab/library/hensel_simple_root_criterion_candidate.py",
  "py/peano_lab/library/integer_column_span_candidate.py",
  "py/peano_lab/library/kummer_carry_candidate.py",
  "py/peano_lab/library/kummer_complete_closure.py",
  "py/peano_lab/library/kummer_valuation_candidate.py",
  "py/peano_lab/library/layered_replay.py",
  "py/peano_lab/library/lean.py",
  "py/peano_lab/library/lean_certified.py",
  "py/peano_lab/library/lean_presentation.py",
  "py/peano_lab/library/lean_proof_reconstruction.py",
  "py/peano_lab/library/lean_proof_strand.py",
  "py/peano_lab/library/linear_congruence_complete_candidate.py",
  "py/peano_lab/library/lucas_block_digit_candidate.py",
  "py/peano_lab/library/lucas_complete_closure.py",
  "py/peano_lab/library/lucas_convolution_candidate.py",
  "py/peano_lab/library/lucas_digit_candidate.py",
  "py/peano_lab/library/lucas_low_digit_candidate.py",
  "py/peano_lab/library/lucas_mixed_promotion.py",
  "py/peano_lab/library/lucas_multidigit_candidate.py",
  "py/peano_lab/library/matrix_coded_product_candidate.py",
  "py/peano_lab/library/matrix_cofactor_expansion_candidate.py",
  "py/peano_lab/library/matrix_determinant_minors_candidate.py",
  "py/peano_lab/library/matrix_dot_product_candidate.py",
  "py/peano_lab/library/matrix_integer_invariance_candidate.py",
  "py/peano_lab/library/matrix_lattice_data_candidate.py",
  "py/peano_lab/library/matrix_rank_certificate_candidate.py",
  "py/peano_lab/library/matrix_rank_finite_coding_candidate.py",
  "py/peano_lab/library/matrix_rank_integer_invariance_candidate.py",
  "py/peano_lab/library/matrix_rank_selected_minors_candidate.py",
  "py/peano_lab/library/matrix_recursive_determinant_candidate.py",
  "py/peano_lab/library/matrix_recursive_determinant_extensional_candidate.py",
  "py/peano_lab/library/mobius_divisor_cancellation_candidate.py",
  "py/peano_lab/library/mobius_inversion_candidate.py",
  "py/peano_lab/library/mobius_prime_step_candidate.py",
  "py/peano_lab/library/mobius_table_candidate.py",
  "py/peano_lab/library/mobius_value_candidate.py",
  "py/peano_lab/library/multinomial_kummer_candidate.py",
  "py/peano_lab/library/odd_prime_lte_candidate.py",
  "py/peano_lab/library/parity.py",
  "py/peano_lab/library/parity_mod_two_candidate.py",
  "py/peano_lab/library/parity_odd_division_candidate.py",
  "py/peano_lab/library/parity_odd_half_mod_four_candidate.py",
  "py/peano_lab/library/parity_sum_classification_candidate.py",
  "py/peano_lab/library/perfect_power_profile_candidate.py",
  "py/peano_lab/library/polynomial_hensel_candidate.py",
  "py/peano_lab/library/polynomial_horner_candidate.py",
  "py/peano_lab/library/polynomial_taylor_hensel_candidate.py",
  "py/peano_lab/library/power_algebra_theorems.py",
  "py/peano_lab/library/power_congruence_theorems.py",
  "py/peano_lab/library/prime_count_chebyshev_candidate.py",
  "py/peano_lab/library/prime_enumeration_candidate.py",
  "py/peano_lab/library/prime_factorization_permutation_candidate.py",
  "py/peano_lab/library/prime_field_arithmetic_candidate.py",
  "py/peano_lab/library/prime_field_finiteness_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_convolution_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_degree_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_evaluation_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_monic_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_subtraction_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_synthetic_candidate.py",
  "py/peano_lab/library/prime_field_polynomial_trim_candidate.py",
  "py/peano_lab/library/prime_field_tables_candidate.py",
  "py/peano_lab/library/prime_valuation_support_candidate.py",
  "py/peano_lab/library/primes_one_mod_four_candidate.py",
  "py/peano_lab/library/primes_three_mod_four_candidate.py",
  "py/peano_lab/library/proof_bundle.py",
  "py/peano_lab/library/pythagorean_fermat_four_candidate.py",
  "py/peano_lab/library/pythagorean_inverse_candidate.py",
  "py/peano_lab/library/pythagorean_primitive_candidate.py",
  "py/peano_lab/library/qr_bounded_units.py",
  "py/peano_lab/library/qr_prime_units.py",
  "py/peano_lab/library/qr_small_moduli.py",
  "py/peano_lab/library/quadratic_reciprocity_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_closure.py",
  "py/peano_lab/library/quadratic_reciprocity_conditional_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_parity_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_stack.py",
  "py/peano_lab/library/quadratic_reciprocity_stack_runtime.py",
  "py/peano_lab/library/quadratic_residue_surface.py",
  "py/peano_lab/library/quadratic_residue_theorems.py",
  "py/peano_lab/library/quadratic_supplement_minus_one_candidate.py",
  "py/peano_lab/library/quadratic_supplement_two_candidate.py",
  "py/peano_lab/library/signed_block_sum_candidate.py",
  "py/peano_lab/library/signed_cartesian_product_candidate.py",
  "py/peano_lab/library/signed_division_parity_bridge_candidate.py",
  "py/peano_lab/library/signed_finite_support_candidate.py",
  "py/peano_lab/library/signed_hensel_lifting_candidate.py",
  "py/peano_lab/library/signed_integer_division_candidate.py",
  "py/peano_lab/library/signed_rectangular_slice_candidate.py",
  "py/peano_lab/library/signed_rectangular_sums_candidate.py",
  "py/peano_lab/library/signed_sum_linearity_candidate.py",
  "py/peano_lab/library/signed_support_reindex_candidate.py",
  "py/peano_lab/library/signed_table_operations_candidate.py",
  "py/peano_lab/library/signed_weighted_sum_candidate.py",
  "py/peano_lab/library/squarefree_decomposition_candidate.py",
  "py/peano_lab/library/supplementary_laws_closure.py",
  "py/peano_lab/library/theorems.py",
  "py/peano_lab/library/two_square_complete_closure.py",
  "py/peano_lab/library/valuation_shared_promotion.py",
  "py/peano_lab/library/wilson_endpoint_restoration_candidate.py",
  "py/peano_lab/library/wilson_inverse_endpoints_candidate.py",
  "py/peano_lab/library/wilson_inverse_involution_candidate.py",
  "py/peano_lab/library/wilson_inverse_orbit_candidate.py",
  "py/peano_lab/library/wilson_inverse_point_candidate.py",
  "py/peano_lab/library/wilson_inverse_prefix_candidate.py",
  "py/peano_lab/library/wilson_pair_order_candidate.py",
  "py/peano_lab/library/wilson_pair_order_induction_candidate.py",
  "py/peano_lab/library/wilson_pair_order_iteration_candidate.py",
  "py/peano_lab/library/wilson_pair_order_paired_iteration_candidate.py",
  "py/peano_lab/library/wilson_pair_product_candidate.py",
  "py/peano_lab/library/wilson_square_one_candidate.py",
  "py/peano_lab/library/wilson_successor_lift_candidate.py",
  "py/peano_lab/library/wilson_terminal_product_candidate.py",
  "py/peano_lab/ui/__init__.py",
  "py/peano_lab/ui/data_kb.py",
  "py/peano_lab/ui/data_library.py",
  "py/peano_lab/ui/data_tactics.py",
  "py/peano_lab/ui/data_tutorials.py",
  "py/peano_lab/ui/panels.py",
  "py/peano_lab/ui/prove.py",
  "py/peano_lab/ui/tutorial.py",
  "py/driver.py",
];

// This namespace is derived from the pinned vendor manifest.  It is part of
// the URL, rather than only a query string, because Pyodide constructs the
// URLs for its own .wasm and standard-library files from indexURL.
const VENDOR_ROOT = "../../vendor/v-85fb3352e49c/";
const PROOF_ARTIFACT_FILES = [
  "proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json",
  "proof-artifacts/supplementary-laws-proof-bundle-v1.json",
  "proof-artifacts/lucas-proof-bundle-v1.json",
  "proof-artifacts/kummer-proof-bundle-v1.json",
  "proof-artifacts/bertrand-proof-bundle-v1.json",
  "proof-artifacts/four-square-proof-bundle-v1.json",
  "proof-artifacts/two-square-proof-bundle-v1.json",
  "proof-artifacts/alpha-v19-residual-proof-bundle-v1.json",
  "proof-artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json",
  "proof-artifacts/alpha-v20-next-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v22-transport-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json",
  "proof-artifacts/alpha-v24-research-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v26-first-wave-proof-bundle-v1.json",
  "proof-artifacts/alpha-v27-second-wave-proof-bundle-v1.json",
  "proof-artifacts/alpha-v28-lower-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v29-priority-layer-proof-bundle-v1.json",
  "proof-artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json",
  "proof-artifacts/bottom-layer-euler-units-proof-bundle-v2.json",
  "proof-artifacts/bottom-layer-prime-fields-proof-bundle-v1.json",
  "proof-artifacts/bottom-layer-mobius-values-proof-bundle-v1.json",
  "proof-artifacts/bottom-layer-signed-sums-proof-bundle-v1.json",
  "proof-artifacts/lower-tier-divisor-sums-proof-bundle-v1.json",
  "proof-artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json",
  "proof-artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
  "proof-artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json",
  "proof-artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json",
  "proof-artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json",
  "proof-artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-finite-support-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-convolution-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-fubini-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-units-proof-bundle-v1.json",
  "proof-artifacts/mobius-inversion-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-signed-units-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-triangular-proof-bundle-v1.json",
  "proof-artifacts/dirichlet-inverses-proof-bundle-v1.json",
  "proof-artifacts/g009-multiplicative-convolution-proof-bundle-v1.json",
  "proof-artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",
];

let runLine = null;
let runLineResult = null;
let banner = null;
let takeDownload = null;

async function fetchRuntimeFiles(paths) {
  return Promise.all(paths.map(async (relativePath) => {
    try {
      const response = await fetch(relativePath);
      if (!response.ok) {
        return {
          relativePath,
          ok: false,
          message: "could not load " + relativePath + " (" + response.status + ")",
        };
      }
      return { relativePath, ok: true, source: await response.text() };
    } catch (_error) {
      return {
        relativePath,
        ok: false,
        message: "could not load " + relativePath + " (network error)",
      };
    }
  }));
}

async function fetchPythonSources() {
  return fetchRuntimeFiles(PY_FILES);
}

async function fetchProofArtifacts() {
  // Start all requests alongside Pyodide, but retain only their response
  // headers. Complete proof bundles are consumed one at a time below; reading
  // them all into UTF-16 strings here multiplied peak browser memory use.
  return Promise.all(PROOF_ARTIFACT_FILES.map(async (relativePath) => {
    try {
      const response = await fetch(relativePath);
      if (!response.ok) {
        return {
          relativePath,
          ok: false,
          message: "could not load " + relativePath + " (" + response.status + ")",
        };
      }
      return { relativePath, ok: true, response };
    } catch (_error) {
      return {
        relativePath,
        ok: false,
        message: "could not load " + relativePath + " (network error)",
      };
    }
  }));
}

async function boot(build) {
  try {
    postMessage({ type: "boot", msg: "loading Python and prover sources (self-hosted)…" });
    // scripts/fetch_vendor.sh pins and fetches this local runtime. No CDN is
    // consulted by the browser, so the lab also works on an isolated network.
    importScripts(VENDOR_ROOT + "pyodide/pyodide.js");

    // Start the large runtime first, then overlap it with all small source
    // transfers. Promise.all retains PY_FILES order; each task returns an
    // envelope instead of rejecting, so the first reported failure is also
    // deterministic in PY_FILES order rather than network-completion order.
    const pyodidePromise = loadPyodide({ indexURL: VENDOR_ROOT + "pyodide/" });
    const sourcesPromise = fetchPythonSources();
    const artifactsPromise = fetchProofArtifacts();
    const pyodide = await pyodidePromise;
    const [sources, artifacts] = await Promise.all([sourcesPromise, artifactsPromise]);
    const failure = sources.find((entry) => !entry.ok)
      || artifacts.find((entry) => !entry.ok);
    if (failure) throw new Error(failure.message);

    postMessage({ type: "boot", msg: "mounting the Peano kernel and tactic engine…" });
    for (const entry of sources) {
      const relativePath = entry.relativePath;
      const destination = "/lab/" + relativePath.replace(/^py\//, "");
      pyodide.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
      pyodide.FS.writeFile(destination, entry.source);
    }
    for (const entry of artifacts) {
      const destination = "/lab/" + entry.relativePath;
      pyodide.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
      let body;
      try {
        const response = entry.response;
        entry.response = null;
        body = new Uint8Array(await response.arrayBuffer());
      } catch (_error) {
        throw new Error("could not load " + entry.relativePath + " (response body error)");
      }
      pyodide.FS.writeFile(destination, body);
    }

    pyodide.runPython("import sys; sys.path.insert(0, '/lab')");
    const driver = pyodide.pyimport("driver");
    runLine = function (line) { return driver.run_line(line); };
    runLineResult = function (line) {
      return JSON.parse(String(driver.run_line_result(line)));
    };
    banner = function () { return driver.banner(); };
    takeDownload = function () { return driver.take_download(); };
    postMessage({ type: "ready", banner: String(banner()) });
  } catch (error) {
    postMessage({ type: "error", msg: (error && error.message) ? error.message : String(error) });
  }
}

onmessage = function (event) {
  const message = event.data || {};
  if (message.type === "init") {
    boot(message.build);
    return;
  }
  if (message.type === "run") {
    let output = "";
    let failed = false;
    let download = null;
    try {
      if (runLineResult) {
        const result = runLineResult(message.line);
        output = String(result.out === undefined ? "" : result.out);
        failed = result.failed === true;
      } else {
        output = runLine
          ? String(runLine(message.line))
          : "\x1b[93mThe engine is still starting — try again in a moment.\x1b[0m";
        failed = true;
      }
      if (takeDownload) {
        const body = String(takeDownload());
        download = body || null;
      }
    } catch (error) {
      output = "\x1b[91m" + ((error && error.message) ? error.message : String(error)) + "\x1b[0m";
      failed = true;
    }
    postMessage({ type: "result", id: message.id, out: output, failed: failed, download: download });
  }
};
