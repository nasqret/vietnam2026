"""Canonical Jordan source plans; original proof identities and novel admissions differ.

The immutable 358-node proof graph retains the original reflexivity name.
A single explicitly checked same-AST alias is omitted from Alpha enrollment.
No proof file, kernel judgment, working controller or edition is loaded here
except when a caller explicitly requests the installed parent specification.
"""
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
import re

from .theorems import TheoremSpec, _closed_formula
from .campaign_lower_layer_closure import _specs_digest

HERE = Path(__file__).resolve().parent
MAX_SOURCE_BYTES = 2 * 1024 * 1024
RAW_NAMES = ('jordan_tuple_equal_refl', 'jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant')
ADMITTED_NAMES = ('jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant')
ALIASES = {'jordan_tuple_equal_refl': 'integer_vector_equal_components_zero'}
RAW_SPECS_SHA256 = 'f4029a8f1990be4853f0ffd056802cb2a0fbae769ea465750b63b787927cb0b8'
ADMITTED_SPECS_SHA256 = '8c3b074fba5e922bbfd5d7ffc3f49d6a3f1d19678b97c41c545e37f316936b52'
PARENT_SPECS_SHA256 = '6e053740edfc66cb4f339ef731cc020dc00d1fa56126336ebce96780e3ea6c23'
COMPLETE_SPECS_SHA256 = '466695ea20089c9a24f951002af27c81a8aa2807922a1c09eab676caed533738'
ORDERED_CONE_NAMES = ('zero_add', 'add_succ_left', 'add_comm', 'add_assoc', 'mul_zero_left', 'mul_succ_left', 'mul_comm', 'mul_add', 'mul_assoc', 'one_mul', 'mul_one', 'add_mul', 'succ_ne_zero', 'le_refl', 'le_trans', 'no_succ_add_fixed', 'drop_add_prefix_from_fixed', 'antisymm_from_witnesses', 'le_antisymm', 'le_total', 'add_eq_zero_right', 'mul_eq_zero', 'zero_or_succ', 'nonzero_is_succ', 'mul_congr', 'add_right_cancel', 'add_left_cancel', 'zero_le', 'le_succ_self', 'le_zero', 'one_le_of_ne_zero', 'ne_zero_of_one_le', 'le_add_left', 'le_add_right', 'add_le_add_right', 'add_le_add_left', 'succ_le_succ', 'le_of_succ_le_succ', 'le_succ', 'lt_to_le', 'lt_irrefl_expanded', 'le_eq_or_lt', 'lt_of_lt_of_le', 'le_or_lt', 'lt_trichotomy', 'lt_not_le', 'lt_not_eq_add_middle', 'mul_le_mul_left', 'mul_le_mul_right', 'mul_lt_mul_succ_left_nonzero', 'division_remainder_succ', 'division_remainder_exists', 'positive_quotient_gap_impossible', 'division_remainder_unique', 'multiple_has_zero_remainder', 'add_eq_zero_left', 'mul_eq_one_components', 'mul_ne_zero', 'mul_left_cancel_nonzero', 'multiple_zero', 'one_multiple', 'multiple_refl', 'multiple_mul_right', 'multiple_trans', 'divisor_le_nonzero', 'divisor_one', 'multiple_antisymm', 'factor_difference', 'divides_remainder', 'divides_linear_step', 'is_gcd_zero_right', 'is_gcd_symm', 'is_gcd_dvd_left', 'is_gcd_dvd_right', 'is_gcd_greatest', 'is_gcd_of_dvd', 'is_gcd_unique', 'is_gcd_euclid_forward', 'gcd_exists_up_to', 'gcd_exists_relational', 'coprime_symm', 'coprime_one_left', 'is_gcd_one_to_coprime', 'add_permute_outer', 'balanced_bezout_euclid_step', 'gcd_balanced_bezout_exists_up_to', 'gcd_balanced_bezout_exists', 'balanced_combination_scale_right', 'common_divisor_divides_balanced_result', 'coprime_balanced_bezout', 'gauss_coprime_cancel', 'eq_decidable', 'multiple_decidable_nonzero', 'multiple_decidable', 'factor_property_succ', 'factor_search_up_to', 'prime_or_composite', 'prime_nonzero', 'factor_nonzero_left', 'proper_factor_lt', 'prime_divisor_exists_up_to', 'prime_divisor_exists', 'prime_divisor_eq_one_or_self', 'euclid_prime_dvd_product', 'mod_eq_refl', 'mod_eq_symm', 'mod_eq_trans', 'mod_eq_add', 'mod_eq_mul_right', 'mod_eq_mul_left', 'remainder_decomposition_to_mod_eq', 'mod_eq_bounded_unique', 'mod_eq_to_remainder_decomposition', 'beta_modulus_nonzero', 'beta_at_self_of_bound', 'beta_at_exists', 'beta_at_unique', 'beta_at_of_mod_eq_bound', 'dvd_to_mod_zero', 'bezout_mod_left', 'bezout_mod_right', 'mod_eq_predecessor_cancel', 'binary_crt', 'beta_modulus_coprime_base', 'common_divisor_beta_moduli_divides_gap_times_c', 'beta_moduli_coprime_of_gap_dvd', 'bounded_common_multiple_step', 'bounded_common_multiple_exists', 'beta_moduli_coprime_of_lt_bounded_common_multiple', 'beta_moduli_pairwise_coprime_bounded', 'coprime_mul_left', 'mod_eq_of_mod_eq_multiple', 'binary_crt_fold_step', 'right_factor_divides_product', 'beta_value_le_code', 'base_le_beta_modulus', 'le_scaled_nonzero', 'scaled_bounded_common_multiple', 'beta_value_lt_scaled_base', 'new_value_lt_scaled_base', 'beta_exclusive_accumulated_product_step', 'beta_exclusive_recode_congruence_step', 'beta_exclusive_recode_invariant_step', 'bounded_beta_exclusive_recode_invariant', 'beta_prefix_extend', 'beta_prefix_product_trace_exists', 'beta_product_exists', 'beta_product_functional', 'beta_product_zero', 'beta_product_succ_decompose', 'beta_product_transport_prefix', 'beta_repeat_empty', 'beta_repeat_succ_extend', 'beta_repeat_exists', 'beta_repeat_entry_eq', 'beta_repeat_transport_entry', 'pow_exists', 'pow_zero', 'pow_functional', 'pow_successor_decompose', 'pow_one_from_zero_successor', 'pow_one', 'pow_successor_pair_mul', 'pow_add', 'finite_surjective_zero', 'finite_injective_prefix_succ', 'finite_lt_succ_eq_or_lt', 'finite_bounded_entry_lt', 'beta_prefix_replace_exists', 'beta_prefix_swap_last_from_entries', 'beta_prefix_swap_last_reflect', 'finite_swap_last_bounded', 'finite_swap_last_injective', 'finite_swap_last_surjective_back', 'finite_contains_decidable', 'finite_bounded_prefix_without_top', 'finite_bounded_last_succ', 'finite_surjective_succ_intro', 'finite_last_is_top_from_prefix_surjective', 'finite_surjective_succ_from_prefix', 'finite_no_top_successor_gate', 'finite_bounded_injective_surjective', 'prime_is_succ_succ', 'is_lcm_least', 'coprime_product_is_lcm', 'is_gcd_quotients_coprime_nonzero', 'mod_eq_ordered_gap_multiple', 'mod_eq_lcm_merge', 'distinct_primes_left_not_divide_right', 'beta_division_prefix_extend', 'beta_division_prefix_exists', 'canonical_gcd_exists', 'factor_nonzero_right', 'le_mul_of_one_le_right', 'one_le_pow', 'pow_nonzero_of_one_le', 'power_divides_decidable', 'power_divides_zero', 'bounded_power_valuation_search', 'bounded_power_valuation_exists', 'power_valuation_exists', 'power_valuation_power_divides', 'power_valuation_dominates', 'prime_two_le', 'succ_le_mul_of_two_le_right', 'prime_power_exponent_le', 'prime_power_divides_exponent_le_value', 'power_valuation_successor_not_divides', 'power_valuation_selected_and_successor_not_divides', 'mul_shuffle_four', 'power_divides_exponent_antitone', 'power_divides_add_mul', 'power_divides_successor_of_cofactor', 'prime_power_successor_cancel_cofactor', 'prime_nondivisor_mul', 'power_valuation_exact_cofactor', 'power_valuation_mul_successor_not_divides', 'power_valuation_mul_lower', 'power_valuation_mul_upper', 'prime_power_valuation_mul', 'prime_power_valuation_one_zero', 'prime_power_divides_exponent_le_valuation', 'power_valuation_nonzero_exponent_divides_base', 'prime_divisor_power_valuation_nonzero', 'power_valuation_value_eq_transport', 'finite_bounded_into_oversized_not_injective', 'prime_power_valuation_zero_iff_not_divides', 'linear_congruence_zero_residue_divides', 'crt_coprime_divisor_pair', 'crt_balanced_bezout_scale', 'crt_is_gcd_scale', 'crt_is_gcd_coprime_factor_remove', 'crt_product_witness', 'crt_is_gcd_coprime_product', 'matrix_rank_bounded_prefix_value', 'matrix_rank_common_multiple_divides', 'matrix_rank_beta_moduli_common_multiple', 'matrix_rank_recode_congruences_exists', 'matrix_rank_bounded_recode_in_fixed_box', 'matrix_rank_uniform_beta_prefix_box_exists', 'matrix_rank_no_index_below_zero', 'matrix_rank_bounded_prefix_empty', 'matrix_rank_bounded_prefix_drop_last', 'matrix_rank_bounded_prefix_extend', 'matrix_rank_bounded_prefix_decidable', 'finite_add_le_add', 'finite_add_lt_of_le_of_lt', 'finite_beta_zero_code', 'prime_valuation_exponent_eq_transport', 'prime_valuation_zero_of_nondivisor', 'prime_valuation_nondivisor_of_zero', 'prime_power_valuation_pow_value', 'prime_power_valuation_pow', 'pow_positive_exponent_base_divides', 'prime_valuation_distinct_prime_power_zero', 'prime_divisor_of_prime_power', 'jordan_tuple_equal_refl', 'jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'coprime_divisor_gcd_product', 'coprime_divisor_factor_pair_exists', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'prime_field_polynomial_normalization_from_division', 'prime_field_polynomial_normalization_exists', 'prime_field_polynomial_normalization_bounded', 'prime_field_polynomial_normalization_entry', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant')
ROOT_NAMES = ('jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_totient_multiplicativity_exists', 'jordan_totient_multiplicativity_unique_counts', 'jordan_totient_at_one_unique', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant')
FACTORY_RECORDS = [('jordan_totient_candidate', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', ('make_jordan_totient_candidate_theorems', 'make_jordan_enumeration_candidate_theorems', 'make_jordan_enumeration_bridge_candidate_theorems', 'make_jordan_scan_candidate_theorems', 'make_jordan_crt_tuple_candidate_theorems', 'make_jordan_canonical_crt_candidate_theorems'), 51, '60572855097779d4999aa009ed484cf16cc7c460c0558e6096b6c8ce2dff78d6', ('jordan_tuple_equal_refl', 'jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists')), ('jordan_multiplicativity_candidate', 38826, 'aeff3b3adb320e30388290654fc88beea3ccbe9c84adba543b47e741c5a11b86', ('make_jordan_multiplicativity_candidate_theorems',), 24, 'a04aad8b0bc375fe20c0d095a906e762a5af4a48f85f58c55ef12b58be0514b3', ('jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists')), ('jordan_count_uniqueness_candidate', 15791, '06e609a6f14b837eeb8d913d92e6090d4703dfd8b0d25aa4e348fcbd50b57074', ('make_jordan_count_uniqueness_candidate_theorems',), 10, 'f2b507138a4a7a39d9a17d40a0092783fd39713644574b507b9092e3dcd69382', ('jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique')), ('jordan_multiplicativity_unique_candidate', 1304, 'c2e3f94ee6777659c30b449472b471697c0e6039f28f9052c4c1ebf2cb8fe99f', ('make_jordan_multiplicativity_unique_candidate_theorems',), 1, '6cfd078202334d0e34e11dbb039f80e4f172dee9b0ba84c8c7973dbb4fa1caee', ('jordan_totient_multiplicativity_unique_counts',)), ('jordan_unit_modulus_candidate', 5562, '8fdeb1c10bed3e445b700b10ebbf2c9ff16e29802756ba21001cd5c4fff100a8', ('make_jordan_unit_modulus_candidate_theorems',), 6, '6f8acc8c99940c95eae3e8355bcf45ed8c3c7e3af1f22f636b0b165f9dae5966', ('jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique')), ('jordan_prime_power_characterization_candidate', 6441, '6f7d65e91dfe8c818b2bf5a3d0e8b1754f75fe631cc943543c5081820a299f11', ('make_jordan_prime_power_characterization_candidate_theorems',), 4, '8500fe3c22993269ae4ca2d3d87f3f369c7218ccde805c57ae77efc0d8071f4b', ('jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant'))]
ADMITTED_EDGES = 254
ADMITTED_COMMANDS = 5335
RAW_EDGES = 255
RAW_COMMANDS = 5352

ALIASES = MappingProxyType(ALIASES)
PARENT_COUNT = 4223
RAW_ASSEMBLER_FRONTIER_NAMES = ('jordan_tuple_equal_refl', 'jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'coprime_divisor_gcd_product', 'coprime_divisor_factor_pair_exists', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'prime_field_polynomial_normalization_from_division', 'prime_field_polynomial_normalization_exists', 'prime_field_polynomial_normalization_bounded', 'prime_field_polynomial_normalization_entry', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant')
RAW_ASSEMBLER_FRONTIER_SHA256 = '7a66ab57c070aa44a121554652233edbd8cb7e93a8b47eac7833aa15f14d9450'

class SourcePlanError(ValueError):
    """A literal source, exact formula or original proof dependency changed."""

def require(condition, message):
    if not condition:
        raise SourcePlanError(message)

def source_records():
    return tuple(dict(path="peano-lab/py/peano_lab/library/" + row[0] + ".py",
        module=row[0], bytes=row[1], sha256=row[2], factories=row[3],
        count=row[4], specs_sha256=row[5], names=row[6]) for row in FACTORY_RECORDS)

def validate_source_bytes():
    for name, size, digest, *_ in FACTORY_RECORDS:
        path = HERE / (name + ".py")
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == size
            and 0 < size <= MAX_SOURCE_BYTES, "canonical Jordan source type/size changed")
        with path.open("rb") as stream:
            data = stream.read(size + 1)
        require(len(data) == size and sha256(data).hexdigest() == digest,
            "canonical Jordan source bytes changed: " + name)
    return source_records()

@lru_cache(maxsize=1)
def _raw_owned_specs():
    result = []
    for name, size, digest, factories, count, specs_digest, names in FACTORY_RECORDS:
        module = import_module("." + name, package=__package__)
        path = str(HERE / (name + ".py"))
        require(module.__file__ == path and module.__spec__.origin == path,
            "foreign canonical Jordan source owner")
        rows = []
        for factory_name in factories:
            factory = getattr(module, factory_name)
            require(callable(factory) and factory.__module__ == module.__name__,
                "foreign canonical Jordan factory")
            part = factory(TheoremSpec)
            require(type(part) is tuple and all(type(row) is TheoremSpec for row in part),
                "invalid actual Jordan theorem factory")
            rows.extend(part)
        rows = tuple(rows)
        require(len(rows) == count and tuple(row.name for row in rows) == names
            and _specs_digest(rows) == specs_digest, "canonical factory changed original Jordan specifications")
        result.extend(rows)
    result = tuple(result)
    require(tuple(row.name for row in result) == RAW_NAMES and _specs_digest(result) == RAW_SPECS_SHA256,
        "complete original Jordan96 source identity changed")
    return result

def raw_owned_specs():
    validate_source_bytes()
    return _raw_owned_specs()

def parent_specs(specs=None):
    if specs is None:
        from . import editions_v34
        specs = editions_v34.ALPHA_CHECKED_SPECS
    require(type(specs) is tuple and len(specs) == PARENT_COUNT
        and all(type(row) is TheoremSpec for row in specs)
        and _specs_digest(specs) == PARENT_SPECS_SHA256, "exact Alpha-v34 parent syntax changed")
    return specs

def validate_aliases(parent):
    raw = {row.name: row for row in raw_owned_specs()}
    prior = {row.name: row for row in parent_specs(parent)}
    require(dict(ALIASES) == {"jordan_tuple_equal_refl": "integer_vector_equal_components_zero"},
        "unregistered alias mapping")
    for name, canonical in ALIASES.items():
        require(name in raw and canonical in prior and name not in prior,
            "alias source or canonical parent is absent")
        left, right = raw[name], prior[canonical]
        require(_closed_formula(left.statement) == _closed_formula(right.statement)
            and left.dependencies == right.dependencies,
            "alias does not preserve exact closed AST and ordered premises")
    return ALIASES

def rename_reference(command):
    """Rename ONLY an explicit tactic reference; no formula or binder rewrite."""
    pieces = command.split(maxsplit=2)
    if len(pieces) > 1 and pieces[1] in ALIASES:
        require(pieces[0] in ("specialize", "forall_elim", "apply", "exact"),
            "unsupported alias-reference command")
        return " ".join((pieces[0], ALIASES[pieces[1]], *pieces[2:]))
    require(not any(name in command for name in ALIASES),
        "alias appears outside a reviewed tactic-reference position")
    return command

def normalize_owned_specs(originals, parent=None):
    """Normalize the exact raw96 inventory, never arbitrary supplied syntax."""
    prior = parent_specs(parent)
    validate_aliases(prior)
    require(type(originals) is tuple and originals == raw_owned_specs(),
        "normalization requires the exact original Jordan96 specifications")
    table = {row.name: row for row in (*prior, *originals)}
    normalized = []
    for row in originals:
        if row.name in ALIASES:
            continue
        dependencies = tuple(ALIASES.get(name, name) for name in row.dependencies)
        require(len(set(dependencies)) == len(dependencies), "alias would merge distinct premise positions")
        for before, after in zip(row.dependencies, dependencies):
            require(_closed_formula(table[before].statement) == _closed_formula(table[after].statement),
                "admission alias changed an actual premise formula")
        new = replace(row, dependencies=dependencies, script=tuple(rename_reference(c) for c in row.script))
        require(new.statement == row.statement and new.summary == row.summary, "admission changed a theorem contract")
        normalized.append(new)
    normalized = tuple(normalized)
    require(tuple(row.name for row in normalized) == ADMITTED_NAMES
        and _specs_digest(normalized) == ADMITTED_SPECS_SHA256,
        "exact 95 novel Jordan admission specifications changed")
    return normalized

def admitted_specs(parent=None):
    return normalize_owned_specs(raw_owned_specs(), parent)

def normalized_spec(spec, parent=None):
    """Map one actual raw-cone row to its exact admitted specification."""
    prior = parent_specs(parent)
    raw = {row.name: row for row in raw_owned_specs()}
    table = {row.name: row for row in prior}
    if spec.name in raw:
        require(spec == raw[spec.name], "a raw alias/admission source changed")
        if spec.name in ALIASES:
            validate_aliases(prior)
            return table[ALIASES[spec.name]]
        return next(row for row in admitted_specs(prior) if row.name == spec.name)
    require(table.get(spec.name) == spec, "a raw cone prerequisite changed")
    return spec

@dataclass(frozen=True, slots=True)
class SourceSelection:
    specs: tuple
    owned_specs: tuple
    admitted_specs: tuple
    root_names: tuple
    frontier: tuple

    @property
    def frontier_specs(self):
        return self.owned_specs

    @property
    def positions(self):
        return MappingProxyType({row.name: i for i, row in enumerate(self.specs)})

def source_cone(slug="jordan-totient", *, parent=None):
    require(slug == "jordan-totient", "unknown exact Jordan proof family")
    prior = parent_specs(parent)
    raw = raw_owned_specs()
    table = {row.name: row for row in (*prior, *raw)}
    require(len(table) == len(prior) + len(raw), "Jordan source overwrites an admitted name")
    included, active = set(), set()
    def visit(name):
        require(name in table and name not in active, "unknown or cyclic original proof premise")
        if name in included:
            return
        require(len(active) < 4096, "original source traversal exceeds the graph bound")
        active.add(name)
        for dependency in table[name].dependencies:
            visit(dependency)
        active.remove(name)
        included.add(name)
    for row in raw:
        visit(row.name)
    require(set(ORDERED_CONE_NAMES) == included and len(ORDERED_CONE_NAMES) == len(included) == 358,
        "the exact original 358-theorem proof cone changed")
    selected = tuple(table[name] for name in ORDERED_CONE_NAMES)
    available = set()
    for row in selected:
        require(type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies)
            and set(row.dependencies) <= available, "original proof order or premises changed")
        available.add(row.name)
    used = {name for row in selected for name in row.dependencies}
    roots = tuple(row.name for row in selected if row.name not in used)
    require(roots == ROOT_NAMES and _specs_digest(selected) == COMPLETE_SPECS_SHA256
        and sum(len(row.dependencies) for row in selected) == 949,
        "original complete source specifications or maximal roots changed")
    assembler_frontier = tuple(table[name] for name in RAW_ASSEMBLER_FRONTIER_NAMES)
    require(len(assembler_frontier) == 102
        and _specs_digest(assembler_frontier) == RAW_ASSEMBLER_FRONTIER_SHA256,
        "the original v30-plus-102 assembler frontier changed")
    return SourceSelection(selected, raw, admitted_specs(prior), roots, assembler_frontier)

def normalized_cone_specs(selection, parent=None):
    prior = parent_specs(parent)
    require(type(selection) is SourceSelection, "invalid original source selection")
    admitted = normalize_owned_specs(selection.owned_specs, prior)
    table = {row.name: row for row in (*prior, *admitted)}
    require(selection.specs == source_cone(parent=prior).specs, "altered original source cone")
    result = tuple(table[ALIASES.get(row.name, row.name)] for row in selection.specs)
    for raw, normalized in zip(selection.specs, result, strict=True):
        require(_closed_formula(raw.statement) == _closed_formula(normalized.statement)
            and tuple(ALIASES.get(name, name) for name in raw.dependencies) == normalized.dependencies,
            "normalization changed a closed target or ordered premise identity")
    return result

source_selection = source_cone

def clear_source_cache():
    _raw_owned_specs.cache_clear()
