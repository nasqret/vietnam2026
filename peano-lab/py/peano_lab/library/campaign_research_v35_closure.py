"""Exact Jordan v35 provider: raw96 proof identities, 95 novel admissions.

Metadata is not proof authority. Checked use authenticates and checks every
actual HA body; compiled-Lean verification belongs to fresh release gates.
The immutable Jordan artifact keeps its original dependency-first order.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from ..kernel.formulas import Formula
from .campaign_lower_layer_closure import _packaging_root, _specs_digest
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, CheckedProofBundle, ProofBundle,
    check_proof_bundle,
)
from .theorems import TheoremSpec, _closed_formula


class ResearchClosureError(ValueError):
    """A frozen source, exact dependency, target, proof, or resource gate failed."""


@dataclass(frozen=True, slots=True)
class ResearchFactory:
    campaign: str
    module: str
    factory: str
    rfc: str
    source_bytes: int
    source_sha256: str
    count: int
    specs_sha256: str
    test_filename: str

    @property
    def source(self) -> str:
        return f"peano-lab/py/peano_lab/library/{self.module}.py"

    @property
    def test(self) -> str:
        return "peano-lab/py/tests/" + self.test_filename


@dataclass(frozen=True, slots=True)
class ResearchFamily:
    slug: str
    research_checkpoint_slug: str
    artifact: str
    artifact_bytes: int
    artifact_sha256: str
    count: int
    specs_sha256: str
    names_sha256: str
    edge_count: int
    command_count: int
    rfc: str
    owned_names: tuple[str, ...]
    principal_roots: tuple[str, ...]
    theorem_count: int
    root_names: tuple[str, ...]
    node_count: int
    dependency_edges: int
    bundle_edges: int
    body_nodes: int
    ordered_cone_names_sha256: str
    ordered_cone_names: tuple[str, ...]
    complete_specs_sha256: str
    complete_non_alpha_specs_sha256: str
    modules: tuple[str, ...]
    principal_pins: tuple[tuple[str, str], ...]

    @property
    def artifact_filename(self) -> str:
        return self.artifact.rsplit("/", 1)[-1]

    @property
    def principal_statement_sha256(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self.principal_pins))


@dataclass(frozen=True, slots=True)
class ResearchRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    campaign: str | None
    is_owned: bool


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    family: ResearchFamily
    rows: tuple[ResearchRow, ...]
    specs: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    owned_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    frontier_specs_sha256: str

    @property
    def positions(self) -> Mapping[str, int]:
        return MappingProxyType({row.name: row.node_id for row in self.rows})


from . import research_source_plan_v35 as source_plan

PARENT_ALPHA_V34_COUNT = 4223
PARENT_ALPHA_V34_SPECS_SHA256 = '6e053740edfc66cb4f339ef731cc020dc00d1fa56126336ebce96780e3ea6c23'
PARENT_ALPHA_V34_IDENTITY_SHA256 = "ee93c0250bdb5bfc362ef6362be5346d1373a01330d1b6a9c6466965cea3b3ff"
PARENT_ALPHA_V34_ENROLLMENT_SHA256 = "07df5c9e467358a8ba9964b037d21d0576cafb4b7c02831336c96b2929b3cb08"
REGISTRATION_COMPLETE = True
EXPECTED_RESEARCH_COUNT = 95
EXPECTED_RAW_OWNED_COUNT = 96
EXPECTED_RESEARCH_EDGE_COUNT = 254
EXPECTED_RESEARCH_COMMAND_COUNT = 5335
EXPECTED_RESEARCH_FAMILY_COUNT = 1
EXPECTED_RESEARCH_FACTORY_COUNT = 11
MAX_SOURCE_BYTES = 2 * 1024 * 1024
EXPECTED_RESEARCH_NAMES_SHA256 = '78e95a158fe086881f861b6971779f6f9261e1d60d785ad8ac3871b57ecb321c'
EXPECTED_RESEARCH_SPECS_SHA256 = '8c3b074fba5e922bbfd5d7ffc3f49d6a3f1d19678b97c41c545e37f316936b52'
EXPECTED_RESEARCH_METADATA_SHA256 = 'f054b171f8776d681d8584f50e1e790760cdb2f21753f514790dfb8fb14d67d9'
FACTORIES = tuple(ResearchFactory(*row) for row in (('jordan-totient', 'jordan_totient_candidate', 'make_jordan_totient_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 21, '6ed2ab9fcc95ccd70a1050dc41c3a58034f6deb19c94718b73a25e3d6e8ab50c', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_totient_candidate', 'make_jordan_enumeration_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 8, '3a91b922ca480e1b0a200f8c518baaca270168b8abf7256e0575ecf5a6401217', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_totient_candidate', 'make_jordan_enumeration_bridge_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 8, '57ebe192ac431f0b00d0dc50cf5d58fc8e0922687cbf5fd1e28619f7e965e637', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_totient_candidate', 'make_jordan_scan_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 4, '7cd02dc2b2ed9447b2939e5781100257f97859b4e6db69082ac52f70f5ab11aa', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_totient_candidate', 'make_jordan_crt_tuple_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 5, '32f5fe9f2e46f213908791a5732a210b358922fec47355007114d8b3511e95ab', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_totient_candidate', 'make_jordan_canonical_crt_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 68642, 'ec2f9c368b4d30dfb8ffe0a2c89dca6e82966d3c8819ce10d29123189fe7052c', 5, '6a961649fab86d1ff096efff1b4bd6a7478b54e3174e1c015f11f265bb083d54', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_multiplicativity_candidate', 'make_jordan_multiplicativity_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 38826, 'aeff3b3adb320e30388290654fc88beea3ccbe9c84adba543b47e741c5a11b86', 24, 'a04aad8b0bc375fe20c0d095a906e762a5af4a48f85f58c55ef12b58be0514b3', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_count_uniqueness_candidate', 'make_jordan_count_uniqueness_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 15791, '06e609a6f14b837eeb8d913d92e6090d4703dfd8b0d25aa4e348fcbd50b57074', 10, 'f2b507138a4a7a39d9a17d40a0092783fd39713644574b507b9092e3dcd69382', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_multiplicativity_unique_candidate', 'make_jordan_multiplicativity_unique_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 1304, 'c2e3f94ee6777659c30b449472b471697c0e6039f28f9052c4c1ebf2cb8fe99f', 1, '6cfd078202334d0e34e11dbb039f80e4f172dee9b0ba84c8c7973dbb4fa1caee', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_unit_modulus_candidate', 'make_jordan_unit_modulus_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 5562, '8fdeb1c10bed3e445b700b10ebbf2c9ff16e29802756ba21001cd5c4fff100a8', 6, '6f8acc8c99940c95eae3e8355bcf45ed8c3c7e3af1f22f636b0b165f9dae5966', 'test_campaign_research_v35_closure.py'), ('jordan-totient', 'jordan_prime_power_characterization_candidate', 'make_jordan_prime_power_characterization_candidate_theorems', 'alpha-v35-jordan-promotion-rfc-v1.md', 6441, '6f7d65e91dfe8c818b2bf5a3d0e8b1754f75fe631cc943543c5081820a299f11', 4, '8500fe3c22993269ae4ca2d3d87f3f369c7218ccde805c57ae77efc0d8071f4b', 'test_campaign_research_v35_closure.py')))
RESEARCH_FAMILIES = (ResearchFamily(*('jordan-totient', 'working-jordan-prime-power-unit-prefix-96', 'research/arithmetic-library/artifacts/jordan-totient-prime-power-unit-proof-bundle-v1.json', 1620004, '9164d35758d1fa15d18ec792a429cbb33fd4c511df5651b9f15d37bececf5ea7', 95, '8c3b074fba5e922bbfd5d7ffc3f49d6a3f1d19678b97c41c545e37f316936b52', '78e95a158fe086881f861b6971779f6f9261e1d60d785ad8ac3871b57ecb321c', 254, 5335, 'research/arithmetic-library/alpha-v35-jordan-promotion-rfc-v1.md', ('jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant'), ('jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_totient_multiplicativity_exists', 'jordan_totient_multiplicativity_unique_counts', 'jordan_totient_at_one_unique', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant'), 358, ('jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'jordan_totient_multiplicativity_exists', 'jordan_totient_multiplicativity_unique_counts', 'jordan_totient_at_one_unique', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant'), 359, 949, 956, 22165, '0490b6af80f4a904e49361479a77e0db4e021e4dc17d95dc4e99d9081380289f', ('zero_add', 'add_succ_left', 'add_comm', 'add_assoc', 'mul_zero_left', 'mul_succ_left', 'mul_comm', 'mul_add', 'mul_assoc', 'one_mul', 'mul_one', 'add_mul', 'succ_ne_zero', 'le_refl', 'le_trans', 'no_succ_add_fixed', 'drop_add_prefix_from_fixed', 'antisymm_from_witnesses', 'le_antisymm', 'le_total', 'add_eq_zero_right', 'mul_eq_zero', 'zero_or_succ', 'nonzero_is_succ', 'mul_congr', 'add_right_cancel', 'add_left_cancel', 'zero_le', 'le_succ_self', 'le_zero', 'one_le_of_ne_zero', 'ne_zero_of_one_le', 'le_add_left', 'le_add_right', 'add_le_add_right', 'add_le_add_left', 'succ_le_succ', 'le_of_succ_le_succ', 'le_succ', 'lt_to_le', 'lt_irrefl_expanded', 'le_eq_or_lt', 'lt_of_lt_of_le', 'le_or_lt', 'lt_trichotomy', 'lt_not_le', 'lt_not_eq_add_middle', 'mul_le_mul_left', 'mul_le_mul_right', 'mul_lt_mul_succ_left_nonzero', 'division_remainder_succ', 'division_remainder_exists', 'positive_quotient_gap_impossible', 'division_remainder_unique', 'multiple_has_zero_remainder', 'add_eq_zero_left', 'mul_eq_one_components', 'mul_ne_zero', 'mul_left_cancel_nonzero', 'multiple_zero', 'one_multiple', 'multiple_refl', 'multiple_mul_right', 'multiple_trans', 'divisor_le_nonzero', 'divisor_one', 'multiple_antisymm', 'factor_difference', 'divides_remainder', 'divides_linear_step', 'is_gcd_zero_right', 'is_gcd_symm', 'is_gcd_dvd_left', 'is_gcd_dvd_right', 'is_gcd_greatest', 'is_gcd_of_dvd', 'is_gcd_unique', 'is_gcd_euclid_forward', 'gcd_exists_up_to', 'gcd_exists_relational', 'coprime_symm', 'coprime_one_left', 'is_gcd_one_to_coprime', 'add_permute_outer', 'balanced_bezout_euclid_step', 'gcd_balanced_bezout_exists_up_to', 'gcd_balanced_bezout_exists', 'balanced_combination_scale_right', 'common_divisor_divides_balanced_result', 'coprime_balanced_bezout', 'gauss_coprime_cancel', 'eq_decidable', 'multiple_decidable_nonzero', 'multiple_decidable', 'factor_property_succ', 'factor_search_up_to', 'prime_or_composite', 'prime_nonzero', 'factor_nonzero_left', 'proper_factor_lt', 'prime_divisor_exists_up_to', 'prime_divisor_exists', 'prime_divisor_eq_one_or_self', 'euclid_prime_dvd_product', 'mod_eq_refl', 'mod_eq_symm', 'mod_eq_trans', 'mod_eq_add', 'mod_eq_mul_right', 'mod_eq_mul_left', 'remainder_decomposition_to_mod_eq', 'mod_eq_bounded_unique', 'mod_eq_to_remainder_decomposition', 'beta_modulus_nonzero', 'beta_at_self_of_bound', 'beta_at_exists', 'beta_at_unique', 'beta_at_of_mod_eq_bound', 'dvd_to_mod_zero', 'bezout_mod_left', 'bezout_mod_right', 'mod_eq_predecessor_cancel', 'binary_crt', 'beta_modulus_coprime_base', 'common_divisor_beta_moduli_divides_gap_times_c', 'beta_moduli_coprime_of_gap_dvd', 'bounded_common_multiple_step', 'bounded_common_multiple_exists', 'beta_moduli_coprime_of_lt_bounded_common_multiple', 'beta_moduli_pairwise_coprime_bounded', 'coprime_mul_left', 'mod_eq_of_mod_eq_multiple', 'binary_crt_fold_step', 'right_factor_divides_product', 'beta_value_le_code', 'base_le_beta_modulus', 'le_scaled_nonzero', 'scaled_bounded_common_multiple', 'beta_value_lt_scaled_base', 'new_value_lt_scaled_base', 'beta_exclusive_accumulated_product_step', 'beta_exclusive_recode_congruence_step', 'beta_exclusive_recode_invariant_step', 'bounded_beta_exclusive_recode_invariant', 'beta_prefix_extend', 'beta_prefix_product_trace_exists', 'beta_product_exists', 'beta_product_functional', 'beta_product_zero', 'beta_product_succ_decompose', 'beta_product_transport_prefix', 'beta_repeat_empty', 'beta_repeat_succ_extend', 'beta_repeat_exists', 'beta_repeat_entry_eq', 'beta_repeat_transport_entry', 'pow_exists', 'pow_zero', 'pow_functional', 'pow_successor_decompose', 'pow_one_from_zero_successor', 'pow_one', 'pow_successor_pair_mul', 'pow_add', 'finite_surjective_zero', 'finite_injective_prefix_succ', 'finite_lt_succ_eq_or_lt', 'finite_bounded_entry_lt', 'beta_prefix_replace_exists', 'beta_prefix_swap_last_from_entries', 'beta_prefix_swap_last_reflect', 'finite_swap_last_bounded', 'finite_swap_last_injective', 'finite_swap_last_surjective_back', 'finite_contains_decidable', 'finite_bounded_prefix_without_top', 'finite_bounded_last_succ', 'finite_surjective_succ_intro', 'finite_last_is_top_from_prefix_surjective', 'finite_surjective_succ_from_prefix', 'finite_no_top_successor_gate', 'finite_bounded_injective_surjective', 'prime_is_succ_succ', 'is_lcm_least', 'coprime_product_is_lcm', 'is_gcd_quotients_coprime_nonzero', 'mod_eq_ordered_gap_multiple', 'mod_eq_lcm_merge', 'distinct_primes_left_not_divide_right', 'beta_division_prefix_extend', 'beta_division_prefix_exists', 'canonical_gcd_exists', 'factor_nonzero_right', 'le_mul_of_one_le_right', 'one_le_pow', 'pow_nonzero_of_one_le', 'power_divides_decidable', 'power_divides_zero', 'bounded_power_valuation_search', 'bounded_power_valuation_exists', 'power_valuation_exists', 'power_valuation_power_divides', 'power_valuation_dominates', 'prime_two_le', 'succ_le_mul_of_two_le_right', 'prime_power_exponent_le', 'prime_power_divides_exponent_le_value', 'power_valuation_successor_not_divides', 'power_valuation_selected_and_successor_not_divides', 'mul_shuffle_four', 'power_divides_exponent_antitone', 'power_divides_add_mul', 'power_divides_successor_of_cofactor', 'prime_power_successor_cancel_cofactor', 'prime_nondivisor_mul', 'power_valuation_exact_cofactor', 'power_valuation_mul_successor_not_divides', 'power_valuation_mul_lower', 'power_valuation_mul_upper', 'prime_power_valuation_mul', 'prime_power_valuation_one_zero', 'prime_power_divides_exponent_le_valuation', 'power_valuation_nonzero_exponent_divides_base', 'prime_divisor_power_valuation_nonzero', 'power_valuation_value_eq_transport', 'finite_bounded_into_oversized_not_injective', 'prime_power_valuation_zero_iff_not_divides', 'linear_congruence_zero_residue_divides', 'crt_coprime_divisor_pair', 'crt_balanced_bezout_scale', 'crt_is_gcd_scale', 'crt_is_gcd_coprime_factor_remove', 'crt_product_witness', 'crt_is_gcd_coprime_product', 'matrix_rank_bounded_prefix_value', 'matrix_rank_common_multiple_divides', 'matrix_rank_beta_moduli_common_multiple', 'matrix_rank_recode_congruences_exists', 'matrix_rank_bounded_recode_in_fixed_box', 'matrix_rank_uniform_beta_prefix_box_exists', 'matrix_rank_no_index_below_zero', 'matrix_rank_bounded_prefix_empty', 'matrix_rank_bounded_prefix_drop_last', 'matrix_rank_bounded_prefix_extend', 'matrix_rank_bounded_prefix_decidable', 'finite_add_le_add', 'finite_add_lt_of_le_of_lt', 'finite_beta_zero_code', 'prime_valuation_exponent_eq_transport', 'prime_valuation_zero_of_nondivisor', 'prime_valuation_nondivisor_of_zero', 'prime_power_valuation_pow_value', 'prime_power_valuation_pow', 'pow_positive_exponent_base_divides', 'prime_valuation_distinct_prime_power_zero', 'prime_divisor_of_prime_power', 'jordan_tuple_equal_refl', 'jordan_tuple_equal_symm', 'jordan_tuple_equal_trans', 'jordan_tuple_common_divisor_transport', 'jordan_primitive_tuple_transport', 'jordan_primitive_tuple_divisor_modulus', 'jordan_tuple_divisor_downward', 'jordan_primitive_tuple_modulus_one', 'jordan_order_zero_excluded', 'jordan_modulus_zero_excluded', 'coprime_divisor_gcd_product', 'coprime_divisor_factor_pair_exists', 'jordan_primitive_tuple_coprime_product', 'jordan_primitive_tuple_product_components', 'jordan_divisibility_congruence_transport', 'jordan_tuple_congruence_symm', 'jordan_primitive_tuple_congruence_transport', 'jordan_tuple_all_divisible_empty', 'jordan_tuple_all_divisible_extend', 'jordan_tuple_all_divisible_decidable', 'jordan_tuple_divisor_test_decidable', 'jordan_tuple_primitive_bounded_decidable', 'jordan_primitive_tuple_decidable', 'jordan_tuple_equal_empty', 'jordan_tuple_equal_drop_last', 'jordan_tuple_equal_extend', 'jordan_tuple_equal_decidable', 'jordan_tuple_listed_empty', 'jordan_tuple_listed_lift', 'jordan_tuple_listed_decidable', 'jordan_tuple_scan_empty', 'jordan_tuple_prefix_equal', 'jordan_tuple_equal_entry', 'jordan_tuple_bounded_transport', 'jordan_tuple_outer_append_exists', 'jordan_tuple_listed_equal_transport', 'jordan_tuple_scan_skip', 'jordan_tuple_scan_complete', 'jordan_totient_from_complete_scan', 'jordan_tuple_scan_append', 'jordan_tuple_scan_exists', 'jordan_tuple_representatives_exists', 'jordan_totient_exists', 'jordan_crt_tuple_empty', 'jordan_crt_tuple_extend', 'jordan_crt_tuple_exists', 'jordan_crt_tuple_left', 'jordan_crt_tuple_right', 'prime_field_polynomial_normalization_from_division', 'prime_field_polynomial_normalization_exists', 'prime_field_polynomial_normalization_bounded', 'prime_field_polynomial_normalization_entry', 'jordan_tuple_normalize_exists', 'jordan_tuple_congruence_trans', 'jordan_tuple_congruence_divisor', 'jordan_canonical_crt_tuple_exists', 'jordan_primitive_crt_tuple_exists', 'jordan_rectangle_width_nonzero', 'jordan_rectangle_quotient_bound', 'jordan_rectangle_flat_bound', 'jordan_rectangle_pair_unique', 'jordan_tuple_equal_congruence', 'jordan_tuple_bounded_congruence_equal', 'jordan_tuple_congruence_coprime_product', 'jordan_crt_component_recovery', 'jordan_canonical_crt_tuple_unique', 'jordan_enumeration_actual_value', 'jordan_enumeration_complete', 'jordan_enumeration_distinct', 'jordan_rectangle_crt_append', 'jordan_rectangle_crt_successor', 'jordan_rectangle_crt_exists', 'jordan_rectangle_crt_actual_entry', 'jordan_rectangle_crt_pair_value', 'jordan_enumeration_reduce_primitive', 'jordan_rectangle_crt_distinct', 'jordan_rectangle_crt_covers', 'jordan_rectangle_crt_enumeration', 'jordan_product_enumeration_exists', 'jordan_totient_coprime_product', 'jordan_totient_multiplicativity_exists', 'jordan_enumeration_position_match_from_entries', 'jordan_enumeration_position_match_exists', 'jordan_enumeration_index_map_empty', 'jordan_enumeration_index_map_append', 'jordan_enumeration_index_map_exists', 'jordan_enumeration_index_map_entry', 'jordan_enumeration_index_map_bounded_injective', 'jordan_enumeration_cardinality_le', 'jordan_enumeration_cardinality_unique', 'jordan_totient_count_unique', 'jordan_totient_multiplicativity_unique_counts', 'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one', 'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration', 'jordan_totient_at_one', 'jordan_totient_at_one_unique', 'jordan_primitive_tuple_avoids_prime_common_divisor', 'jordan_prime_power_tuple_primitive_of_not_all_divisible', 'jordan_prime_power_tuple_primitive_characterization', 'jordan_prime_power_tuple_primitivity_invariant'), '466695ea20089c9a24f951002af27c81a8aa2807922a1c09eab676caed533738', 'f4029a8f1990be4853f0ffd056802cb2a0fbae769ea465750b63b787927cb0b8', ('jordan_totient_candidate', 'jordan_multiplicativity_candidate', 'jordan_count_uniqueness_candidate', 'jordan_multiplicativity_unique_candidate', 'jordan_unit_modulus_candidate', 'jordan_prime_power_characterization_candidate'), (('jordan_order_zero_excluded', '9c29eb8742288a4957bdafa4570f8c0abcf391f2a2ae34ac0823772b25bfeb8a'), ('jordan_modulus_zero_excluded', '3cad9a4091db3795271f289596cd4daea0429e8e006b5e21503688bec46b29c9'), ('jordan_totient_multiplicativity_exists', '5b4bbb844653f4befd6755a95510eaf54b8d8df88897b82fe25a530af55e981c'), ('jordan_totient_multiplicativity_unique_counts', 'f906f76472bff7fa58b3907e0e99149a6345cfcb15d7a19e72326169e26a4e13'), ('jordan_totient_at_one_unique', '5b09d9d06efe4146b0de5993af4aa823488e535f7667d9497839d0885ae9a3d8'), ('jordan_prime_power_tuple_primitive_characterization', '84696e7e875bc4b25237a038ac8f985066642f8e2e9313d672136e66f19d617b'), ('jordan_prime_power_tuple_primitivity_invariant', '612a3716b3aed0ebb86fd8b210b974a2a6d99739f166b23db7cbd8c30a68f8a7')))),)
FAMILIES = RESEARCH_FAMILIES
FAMILY_BY_SLUG = MappingProxyType({row.slug: row for row in FAMILIES})
FAMILY_BY_NAME = MappingProxyType({name: FAMILIES[0] for name in source_plan.ADMITTED_NAMES})
FACTORY_BY_MODULE = MappingProxyType({name: tuple(row for row in FACTORIES if row.module == name) for name in FAMILIES[0].modules})
FRONTIER_NEW_NAMES = source_plan.ADMITTED_NAMES
RAW_OWNED_NAMES = source_plan.RAW_NAMES
ALIASES = source_plan.ALIASES
_SOURCE_OWNER_INDICES = {'jordan_tuple_equal_refl': 0, 'jordan_tuple_equal_symm': 0, 'jordan_tuple_equal_trans': 0, 'jordan_tuple_common_divisor_transport': 0, 'jordan_primitive_tuple_transport': 0, 'jordan_primitive_tuple_divisor_modulus': 0, 'jordan_tuple_divisor_downward': 0, 'jordan_primitive_tuple_modulus_one': 0, 'jordan_order_zero_excluded': 0, 'jordan_modulus_zero_excluded': 0, 'jordan_primitive_tuple_coprime_product': 0, 'jordan_primitive_tuple_product_components': 0, 'jordan_divisibility_congruence_transport': 0, 'jordan_tuple_congruence_symm': 0, 'jordan_primitive_tuple_congruence_transport': 0, 'jordan_tuple_all_divisible_empty': 0, 'jordan_tuple_all_divisible_extend': 0, 'jordan_tuple_all_divisible_decidable': 0, 'jordan_tuple_divisor_test_decidable': 0, 'jordan_tuple_primitive_bounded_decidable': 0, 'jordan_primitive_tuple_decidable': 0, 'jordan_tuple_equal_empty': 1, 'jordan_tuple_equal_drop_last': 1, 'jordan_tuple_equal_extend': 1, 'jordan_tuple_equal_decidable': 1, 'jordan_tuple_listed_empty': 1, 'jordan_tuple_listed_lift': 1, 'jordan_tuple_listed_decidable': 1, 'jordan_tuple_scan_empty': 1, 'jordan_tuple_prefix_equal': 2, 'jordan_tuple_equal_entry': 2, 'jordan_tuple_bounded_transport': 2, 'jordan_tuple_outer_append_exists': 2, 'jordan_tuple_listed_equal_transport': 2, 'jordan_tuple_scan_skip': 2, 'jordan_tuple_scan_complete': 2, 'jordan_totient_from_complete_scan': 2, 'jordan_tuple_scan_append': 3, 'jordan_tuple_scan_exists': 3, 'jordan_tuple_representatives_exists': 3, 'jordan_totient_exists': 3, 'jordan_crt_tuple_empty': 4, 'jordan_crt_tuple_extend': 4, 'jordan_crt_tuple_exists': 4, 'jordan_crt_tuple_left': 4, 'jordan_crt_tuple_right': 4, 'jordan_tuple_normalize_exists': 5, 'jordan_tuple_congruence_trans': 5, 'jordan_tuple_congruence_divisor': 5, 'jordan_canonical_crt_tuple_exists': 5, 'jordan_primitive_crt_tuple_exists': 5, 'jordan_rectangle_width_nonzero': 6, 'jordan_rectangle_quotient_bound': 6, 'jordan_rectangle_flat_bound': 6, 'jordan_rectangle_pair_unique': 6, 'jordan_tuple_equal_congruence': 6, 'jordan_tuple_bounded_congruence_equal': 6, 'jordan_tuple_congruence_coprime_product': 6, 'jordan_crt_component_recovery': 6, 'jordan_canonical_crt_tuple_unique': 6, 'jordan_enumeration_actual_value': 6, 'jordan_enumeration_complete': 6, 'jordan_enumeration_distinct': 6, 'jordan_rectangle_crt_append': 6, 'jordan_rectangle_crt_successor': 6, 'jordan_rectangle_crt_exists': 6, 'jordan_rectangle_crt_actual_entry': 6, 'jordan_rectangle_crt_pair_value': 6, 'jordan_enumeration_reduce_primitive': 6, 'jordan_rectangle_crt_distinct': 6, 'jordan_rectangle_crt_covers': 6, 'jordan_rectangle_crt_enumeration': 6, 'jordan_product_enumeration_exists': 6, 'jordan_totient_coprime_product': 6, 'jordan_totient_multiplicativity_exists': 6, 'jordan_enumeration_position_match_from_entries': 7, 'jordan_enumeration_position_match_exists': 7, 'jordan_enumeration_index_map_empty': 7, 'jordan_enumeration_index_map_append': 7, 'jordan_enumeration_index_map_exists': 7, 'jordan_enumeration_index_map_entry': 7, 'jordan_enumeration_index_map_bounded_injective': 7, 'jordan_enumeration_cardinality_le': 7, 'jordan_enumeration_cardinality_unique': 7, 'jordan_totient_count_unique': 7, 'jordan_totient_multiplicativity_unique_counts': 8, 'jordan_tuple_bounded_one_entry_zero': 9, 'jordan_zero_tuple_bounded_one': 9, 'jordan_tuples_bounded_one_equal': 9, 'jordan_unit_modulus_singleton_enumeration': 9, 'jordan_totient_at_one': 9, 'jordan_totient_at_one_unique': 9, 'jordan_primitive_tuple_avoids_prime_common_divisor': 10, 'jordan_prime_power_tuple_primitive_of_not_all_divisible': 10, 'jordan_prime_power_tuple_primitive_characterization': 10, 'jordan_prime_power_tuple_primitivity_invariant': 10}
_FACTORY_FIELDS = ("campaign", "module", "factory", "rfc", "source_bytes", "source_sha256", "count", "specs_sha256", "test_filename")
_FAMILY_FIELDS = ("slug", "research_checkpoint_slug", "artifact", "artifact_bytes", "artifact_sha256", "count", "specs_sha256", "names_sha256", "edge_count", "command_count", "rfc", "owned_names", "principal_roots", "theorem_count", "root_names", "node_count", "dependency_edges", "bundle_edges", "body_nodes", "ordered_cone_names_sha256", "ordered_cone_names", "complete_specs_sha256", "complete_non_alpha_specs_sha256", "modules", "principal_pins")


def _metadata_digest() -> str:
    payload = (
        tuple(tuple(getattr(owner, field) for field in _FACTORY_FIELDS) for owner in FACTORIES),
        tuple(tuple(getattr(family, field) for field in _FAMILY_FIELDS) for family in FAMILIES),
    )
    return sha256(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def _validate_research_metadata():
    """Literal eligibility only; metadata never substitutes for proof checking."""
    expected_owners = {}
    offset = 0
    for index, owner in enumerate(FACTORIES):
        for name in RAW_OWNED_NAMES[offset:offset + owner.count]:
            expected_owners[name] = index
        offset += owner.count
    if (REGISTRATION_COMPLETE is not True or _metadata_digest() != EXPECTED_RESEARCH_METADATA_SHA256
            or type(FACTORIES) is not tuple or len(FACTORIES) != 11
            or type(FAMILIES) is not tuple or FAMILIES is not RESEARCH_FAMILIES or len(FAMILIES) != 1
            or any(type(row) is not ResearchFactory for row in FACTORIES)
            or any(type(row) is not ResearchFamily for row in FAMILIES)
            or tuple(FAMILY_BY_SLUG.values()) != FAMILIES
            or tuple(FAMILY_BY_NAME) != FRONTIER_NEW_NAMES
            or any(value is not FAMILIES[0] for value in FAMILY_BY_NAME.values())
            or tuple(FACTORY_BY_MODULE) != FAMILIES[0].modules
            or tuple(row for group in FACTORY_BY_MODULE.values() for row in group) != FACTORIES
            or tuple(_SOURCE_OWNER_INDICES) != RAW_OWNED_NAMES
            or _SOURCE_OWNER_INDICES != expected_owners
            or sum(row.count for row in FACTORIES) != 96
            or FAMILIES[0].count != 95 or FAMILIES[0].owned_names != FRONTIER_NEW_NAMES
            or FAMILIES[0].artifact_bytes > DEFAULT_BUNDLE_LIMITS.max_payload_bytes
            or FAMILIES[0].node_count > DEFAULT_BUNDLE_LIMITS.max_nodes
            or FAMILIES[0].bundle_edges > DEFAULT_BUNDLE_LIMITS.max_edges
            or FAMILIES[0].body_nodes > DEFAULT_BUNDLE_LIMITS.max_total_body_nodes):
        raise ResearchClosureError("the exact research-v35 metadata seal changed")


def validate_research_metadata():
    try:
        _validate_research_metadata()
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResearchClosureError):
            raise
        raise ResearchClosureError("malformed research-v35 metadata") from error


def source_root():
    return Path(__file__).resolve().parent


def source_for(name):
    validate_research_metadata()
    if name not in _SOURCE_OWNER_INDICES:
        raise ResearchClosureError("no Jordan source owns this theorem")
    owner = FACTORIES[_SOURCE_OWNER_INDICES[name]]
    return dict(module=owner.module, path=owner.source, bytes=owner.source_bytes,
                sha256=owner.source_sha256, factory=owner.factory)

def research_family(slug: str) -> ResearchFamily:
    validate_research_metadata()
    if type(slug) is not str or slug not in FAMILY_BY_SLUG:
        raise ResearchClosureError(f"unknown research-v35 family {slug!r}")
    return FAMILY_BY_SLUG[slug]


def _read_pinned(path: Path, size: int, digest: str, *, maximum: int) -> bytes:
    """Bound before allocation/parse; a successful hash is provenance only."""
    if (type(size) is not int or not 0 < size <= maximum
            or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
        raise ResearchClosureError("invalid bounded source pin")
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ResearchClosureError(f"sealed source size/type changed: {path.name}")
        with path.open("rb") as source:
            payload = source.read(size + 1)
    except OSError as error:
        raise ResearchClosureError(f"sealed source unavailable: {path.name}") from error
    if len(payload) != size or sha256(payload).hexdigest() != digest:
        raise ResearchClosureError(f"sealed source bytes changed: {path.name}")
    return payload


def validate_research_source_bytes() -> tuple[ResearchFactory, ...]:
    """Authenticate every new mathematical source without opening proof artifacts."""
    validate_research_metadata()
    for owner in FACTORIES:
        _read_pinned(Path(__file__).with_name(owner.module + ".py"),
                     owner.source_bytes, owner.source_sha256, maximum=MAX_SOURCE_BYTES)
    return FACTORIES


def read_research_bundle_bytes(slug: str, source: str | Path) -> bytes:
    """Read exactly one bounded frozen artifact; no acceptance claim."""
    family = research_family(slug)
    if not isinstance(source, (str, Path)):
        raise ResearchClosureError("a research-v35 proof source must be a filesystem path")
    return _read_pinned(Path(source), family.artifact_bytes, family.artifact_sha256,
                        maximum=DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


def raw_owned_specs():
    validate_research_source_bytes()
    try:
        return source_plan.raw_owned_specs()
    except source_plan.SourcePlanError as error:
        raise ResearchClosureError(str(error)) from error


def normalize_owned_specs(rows, parent=None):
    validate_research_source_bytes()
    try:
        return source_plan.normalize_owned_specs(rows, parent)
    except source_plan.SourcePlanError as error:
        raise ResearchClosureError(str(error)) from error


def normalized_spec(spec, parent=None):
    return source_plan.normalized_spec(spec, parent)


def research_specs():
    return normalize_owned_specs(raw_owned_specs())


def clear_research_metadata_cache():
    source_plan.clear_source_cache()


def source_selection(slug="jordan-totient", *, parent=None):
    validate_research_source_bytes()
    try:
        return source_plan.source_cone(slug, parent=parent)
    except source_plan.SourcePlanError as error:
        raise ResearchClosureError(str(error)) from error


def research_plan(slug, *, parent_specs=None):
    """Original proof identities and ordering; the inherited alias is not enrolled."""
    family = research_family(slug)
    selected = source_selection(slug, parent=parent_specs)
    parent = source_plan.parent_specs(parent_specs)
    indices = {row.name: i for i, row in enumerate((*parent, *selected.owned_specs))}
    owned = frozenset(family.owned_names)
    rows = tuple(ResearchRow(i, indices[row.name], row.name,
        sha256(row.statement.encode()).hexdigest(), row.dependencies,
        slug if row.name in RAW_OWNED_NAMES else None, row.name in owned)
        for i, row in enumerate(selected.specs))
    return ResearchPlan(family, rows, selected.specs, selected.root_names,
        RAW_OWNED_NAMES, family.owned_names, 949, family.ordered_cone_names_sha256,
        source_plan.RAW_SPECS_SHA256)


def check_research_proof_bundle(
    slug: str, bundle: ProofBundle, target: Formula, *,
    parent_specs: tuple[TheoremSpec, ...] | None = None,
) -> CheckedProofBundle:
    """Check exact targets/ordered premises/packaging, then EVERY original HA body."""
    plan = research_plan(slug, parent_specs=parent_specs)
    family = plan.family
    positions = plan.positions
    if (type(bundle) is not ProofBundle or type(bundle.nodes) is not tuple
            or len(bundle.nodes) != family.node_count
            or type(bundle.root) is not int or bundle.root != len(plan.rows)):
        raise ResearchClosureError("the complete artifact inventory or root changed")
    for row, spec, node in zip(plan.rows, plan.specs, bundle.nodes[:-1], strict=True):
        if (type(node) is not BundleNode or type(node.node_id) is not int
                or node.node_id != row.node_id
                or node.target != _closed_formula(spec.statement)
                or type(node.dependencies) is not tuple
                or any(type(value) is not int for value in node.dependencies)
                or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise ResearchClosureError(f"an exact target or ordered premise changed: {row.name}")
    by_name = {row.name: row for row in plan.specs}
    expected_target, expected_body = _packaging_root(tuple(
        _closed_formula(by_name[name].statement) for name in plan.root_names
    ))
    final = bundle.nodes[-1]
    if (type(final) is not BundleNode or type(final.node_id) is not int
            or final.node_id != len(plan.rows) or final.target != expected_target
            or final.body != expected_body or type(final.dependencies) is not tuple
            or any(type(value) is not int for value in final.dependencies)
            or final.dependencies != tuple(positions[name] for name in plan.root_names)
            or target != expected_target):
        raise ResearchClosureError("the exact maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle, target)
    if (type(receipt) is not CheckedProofBundle or receipt.target != target
            or receipt.root != bundle.root or receipt.node_count != family.node_count
            or receipt.kernel_calls != family.node_count
            or receipt.topological_order != tuple(range(family.node_count))
            or receipt.dependency_edges != family.bundle_edges
            or receipt.total_body_nodes != family.body_nodes):
        raise ResearchClosureError("a complete original-kernel check or exact body metric changed")
    return receipt
