"""Focused strict-HA audit for the Bertrand root-32 H/J base tranche."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.bertrand_hj_base_thirty_two_candidate import (
    make_bertrand_hj_base_thirty_two_candidate_theorems,
)
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_total_candidate import (
    make_bertrand_power_total_candidate_theorems,
    power_total_relation,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
    witness_le,
)
from peano_lab.library.bertrand_threshold_base_candidate import (
    make_bertrand_threshold_base_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "pow_block_bound_from_total",
    "pow_three_five_le_pow_four_four_from_total",
    "pow_eleven_two_le_pow_two_seven_from_total",
    "pow_six_ten_le_pow_four_thirteen_from_total",
    "linear_square_budget",
    "bertrand_scaled_budget_root_32",
    "bertrand_scaled_budget_root_33",
    "bertrand_scaled_budget_root_34",
    "bertrand_scaled_budget_root_35",
    "bertrand_scaled_budget_root_36",
    "bertrand_scaled_budget_root_37",
    "ceil_div_six_budget_of_scaled_le",
    "pow_six_six_le_pow_four_eight_from_total",
    "pow_six_four_le_pow_four_six_from_total",
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
    "pow_two_double_eq_pow_four_from_total",
    "pow_two_successor_double_le_pow_four_successor_from_total",
    "pow_eleven_double_block_le_pow_two_seven_block_from_total",
    "pow_eleven_double_block_le_pow_four_even_from_total",
    "pow_eleven_double_block_le_pow_four_odd_from_total",
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
    "bertrand_h_root_32_from_total",
    "bertrand_h_root_33_from_total",
    "bertrand_h_root_34_from_total",
    "bertrand_h_root_35_from_total",
    "bertrand_h_root_36_from_total",
    "bertrand_h_root_37_from_total",
    "bertrand_j_base_thirty_two_window_from_total",
    "bertrand_hj_base_window_thirty_two_from_total",
)

EXPECTED_DEPENDENCIES = {
    "pow_block_bound_from_total": (
        "pow_mul_exp_from_total",
        "pow_base_monotone",
    ),
    "pow_three_five_le_pow_four_four_from_total": (
        "pow_zero",
        "pow_successor_compose_from_total",
        "pow_functional",
        "add_mul",
        "add_assoc",
        "add_comm",
    ),
    "pow_eleven_two_le_pow_two_seven_from_total": (
        "pow_two",
        "pow_two_seed_bundle_from_total",
        "pow_successor_compose_from_total",
        "pow_functional",
        "pow_add",
        "add_mul",
        "mul_add",
        "add_assoc",
        "add_comm",
    ),
    "pow_six_ten_le_pow_four_thirteen_from_total": (
        "pow_block_bound_from_total",
        "pow_three_five_le_pow_four_four_from_total",
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "pow_mul_base",
        "pow_add",
        "mul_le_mul",
        "le_refl",
    ),
    "linear_square_budget": (
        "mul_add",
        "mul_assoc",
        "add_assoc",
        "add_comm",
        "add_mul",
    ),
    "bertrand_scaled_budget_root_32": (
        "linear_square_budget",
        "mul_add",
        "add_assoc",
        "add_comm",
    ),
    "bertrand_scaled_budget_root_33": (
        "linear_square_budget",
        "add_mul",
        "mul_add",
        "add_assoc",
    ),
    "bertrand_scaled_budget_root_34": (
        "linear_square_budget",
        "add_mul",
        "mul_add",
        "add_assoc",
    ),
    "bertrand_scaled_budget_root_35": (
        "linear_square_budget",
        "mul_add",
        "add_mul",
        "add_assoc",
    ),
    "bertrand_scaled_budget_root_36": (
        "linear_square_budget",
        "mul_add",
        "mul_assoc",
        "mul_comm",
        "add_mul",
        "add_assoc",
        "add_comm",
    ),
    "bertrand_scaled_budget_root_37": (
        "linear_square_budget",
        "mul_add",
        "mul_assoc",
        "mul_comm",
        "add_mul",
        "add_assoc",
        "add_comm",
    ),
    "ceil_div_six_budget_of_scaled_le": (
        "le_trans",
        "succ_ne_zero",
        "mul_le_cancel_left_nonzero",
    ),
    "pow_six_six_le_pow_four_eight_from_total": (
        "pow_three_five_le_pow_four_four_from_total",
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "mul_le_mul",
        "le_refl",
    ),
    "pow_six_four_le_pow_four_six_from_total": (
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "mul_le_mul",
        "le_refl",
    ),
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total": (
        "pow_block_bound_from_total",
        "pow_three_five_le_pow_four_four_from_total",
        "pow_add",
        "pow_base_monotone",
        "mul_le_mul",
    ),
    "pow_two_double_eq_pow_four_from_total": (
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
    ),
    "pow_two_successor_double_le_pow_four_successor_from_total": (
        "pow_two_double_eq_pow_four_from_total",
        "pow_base_monotone",
        "pow_add",
        "mul_le_mul",
        "le_refl",
    ),
    "pow_eleven_double_block_le_pow_two_seven_block_from_total": (
        "pow_block_bound_from_total",
        "pow_eleven_two_le_pow_two_seven_from_total",
    ),
    "pow_eleven_double_block_le_pow_four_even_from_total": (
        "pow_eleven_double_block_le_pow_two_seven_block_from_total",
        "pow_two_double_eq_pow_four_from_total",
    ),
    "pow_eleven_double_block_le_pow_four_odd_from_total": (
        "pow_eleven_double_block_le_pow_two_seven_block_from_total",
        "pow_two_successor_double_le_pow_four_successor_from_total",
        "le_trans",
    ),
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total": (
        "pow_block_bound_from_total",
        "pow_six_ten_le_pow_four_thirteen_from_total",
    ),
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total": (
        "pow_two",
        "pow_mul_exp_from_total",
        "mul_assoc",
    ),
    "bertrand_h_root_32_from_total": (
        "bertrand_scaled_budget_root_32",
        "ceil_div_six_budget_of_scaled_le",
        "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
        "pow_eleven_double_block_le_pow_four_odd_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "mul_assoc",
        "add_assoc",
    ),
    "bertrand_h_root_33_from_total": (
        "bertrand_scaled_budget_root_33",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_six_six_le_pow_four_eight_from_total",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "add_mul",
        "add_assoc",
    ),
    "bertrand_h_root_34_from_total": (
        "bertrand_scaled_budget_root_34",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "le_trans",
        "mul_assoc",
    ),
    "bertrand_h_root_35_from_total": (
        "bertrand_scaled_budget_root_35",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_six_four_le_pow_four_six_from_total",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "mul_assoc",
    ),
    "bertrand_h_root_36_from_total": (
        "bertrand_scaled_budget_root_36",
        "ceil_div_six_budget_of_scaled_le",
        "pow_eleven_double_block_le_pow_four_odd_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "mul_add",
        "mul_assoc",
        "add_assoc",
    ),
    "bertrand_h_root_37_from_total": (
        "bertrand_scaled_budget_root_37",
        "ceil_div_six_budget_of_scaled_le",
        "pow_eleven_double_block_le_pow_four_even_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "mul_assoc",
        "mul_comm",
    ),
    "bertrand_j_base_thirty_two_window_from_total": (
        "pow_eleven_double_block_le_pow_four_even_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "add_le_add_right",
    ),
    "bertrand_hj_base_window_thirty_two_from_total": (
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "le_antisymm",
        "bertrand_h_root_32_from_total",
        "bertrand_h_root_33_from_total",
        "bertrand_h_root_34_from_total",
        "bertrand_h_root_35_from_total",
        "bertrand_h_root_36_from_total",
        "bertrand_h_root_37_from_total",
        "bertrand_j_base_thirty_two_window_from_total",
    ),
}

ROOT_BUDGET_TERMS = {
    32: "(4 * 13 + 1) + 4 * 29",
    33: "13 * 13 + 8",
    34: "13 * 14",
    35: "13 * 14 + 6",
    36: "2 * 37 + 2 * (5 * 13)",
    37: "2 * 38 + 7 * 19",
}

# Frozen only after every dependency-curried body had replayed independently.
EXPECTED_STATEMENTS = {
    "pow_block_bound_from_total": (15830, "3e8ef02f4f5e09e76f346e12d476c615bffcd96a16925940fddfed877efefe3d"),
    "pow_three_five_le_pow_four_four_from_total": (9504, "39a9fab75e121d02eae52798539204668f5e21058f7d870303d6996c03691dd7"),
    "pow_eleven_two_le_pow_two_seven_from_total": (10394, "2524eb112bf3f6937f709c1a1d50ed4548aec4d62c6a42c5e5fb0518be1dd0ff"),
    "pow_six_ten_le_pow_four_thirteen_from_total": (9695, "05ef800d076ef32fc2420f0deffeb51f86c1c475eea234602eae7a1b06ff6e25"),
    "linear_square_budget": (180, "d25d3950df05c7f8f0dc8038d2e0e2d851569613e982cf7efcc7e48bb0a484d2"),
    "bertrand_scaled_budget_root_32": (127, "a86fad0808f9e4c7a0ff2a6e9028f013c01fffe67bd7a93c78b8c209f8675313"),
    "bertrand_scaled_budget_root_33": (117, "109c6a56bb513aeff4609d057f457135a64509e4f60023bad0077e98dec15273"),
    "bertrand_scaled_budget_root_34": (113, "5b04769e46e0fbfb8726e60afad92cf40f0876cccd4264c32806ef17639f9c7d"),
    "bertrand_scaled_budget_root_35": (117, "b4ac7d45746ffe090f74143d50fec5f5a11296a05a995013d2f811b7f76c894e"),
    "bertrand_scaled_budget_root_36": (127, "cbfb5e595786e6a39db4b0e4f633e40cba58f1fdfea05806865b543f619c3ca3"),
    "bertrand_scaled_budget_root_37": (121, "33e9dda43ebd888a93b6b519ff8e9ac4c0cc86ddb3f169d73591a648be219b63"),
    "ceil_div_six_budget_of_scaled_le": (424, "8608e834e58fff2af398f37a8fd65f65cb4056c9dfb2008d0cf0fe317da1c8d2"),
    "pow_six_six_le_pow_four_eight_from_total": (10862, "eba20ec10c45ae82254ef4709e11333b467175fb3e71c32d5a316379286c3b68"),
    "pow_six_four_le_pow_four_six_from_total": (11097, "1bd623079b79be434f843878c8ceb3f4b70bbc431b7c0e142bbd4cb1e908b423"),
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total": (10458, "153eab8c7d300aebc4f910f3068f5214ebfc100cbb7d7c5b968ea4fa3ff089b4"),
    "pow_two_double_eq_pow_four_from_total": (10326, "276457d3ef602f882e3d0b84b1f70c9b40e8cebf0ec2717120dfeaf54b404e63"),
    "pow_two_successor_double_le_pow_four_successor_from_total": (9737, "f8401c3369c76d36a9b09fbb5cbbe6cff7abf7a5fe1337004e02d44a808b7400"),
    "pow_eleven_double_block_le_pow_two_seven_block_from_total": (10898, "8dac0e2aaf87b1d914b6032de0261eae644bf26053376ce9aa2bd1f4791f1149"),
    "pow_eleven_double_block_le_pow_four_even_from_total": (10666, "ca9620b6811c9aef7893575d1d3b0f312afc3dfaa66f3a897342965805e64cae"),
    "pow_eleven_double_block_le_pow_four_odd_from_total": (10451, "64ce4baa652207f250465515f02ebb1da786c3f63803da9149183e54fa926689"),
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total": (10199, "af31e86a820506fdc53be4672bee8eafa8608a484eaf6642e65b6d790904a14f"),
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total": (10854, "da9d5adb809b32f6512050b0b65cd4dc5cae42ff3c6ad236a5829123f9d68c39"),
    "bertrand_h_root_32_from_total": (9915, "8ed8f20053034a0c7479a3ab23b557f86831203b0bbe36f0bc31a7bba35268a2"),
    "bertrand_h_root_33_from_total": (9915, "95e40beb76922c8ae934384f38cc969147ab6cc64048f664064ed38b93d630e2"),
    "bertrand_h_root_34_from_total": (9915, "6d2f2b1ab70835b9cce6b0a3399f04bb49845bfaab6847b90c7a1f8e36cf352b"),
    "bertrand_h_root_35_from_total": (9915, "76a9b285acc2678a81badb32610e31eb950a1d84e0f9961e097f1d0c5e33c065"),
    "bertrand_h_root_36_from_total": (9915, "813ea3e8252f546d077f94066ad7916d5be63dfcec045fe763b29dc5dc416a35"),
    "bertrand_h_root_37_from_total": (9915, "beed574e2fcbeb060371a31947363326b96668677edc3e5db680de73c8ad82b0"),
    "bertrand_j_base_thirty_two_window_from_total": (9102, "2d4d990d1099d20a4e7ab696403651feea0b4ff975b72967e129a496407d803a"),
    "bertrand_hj_base_window_thirty_two_from_total": (14953, "33ad1148bf10e9a4341c5485d75ce8cb641099356cb4b4809078d2db64657b5c"),
}

EXPECTED_BODIES = {
    "pow_block_bound_from_total": (2, 66, 75, 34, 75, 74, 0),
    "pow_three_five_le_pow_four_four_from_total": (6, 171, 2812, 131, 2812, 2811, 0),
    "pow_eleven_two_le_pow_two_seven_from_total": (9, 121, 1383, 97, 1383, 1382, 0),
    "pow_six_ten_le_pow_four_thirteen_from_total": (8, 136, 1116, 50, 1019, 1115, 97),
    "linear_square_budget": (5, 61, 69, 30, 69, 68, 0),
    "bertrand_scaled_budget_root_32": (4, 60, 4311, 117, 4311, 4310, 0),
    "bertrand_scaled_budget_root_33": (4, 54, 4963, 153, 4963, 4962, 0),
    "bertrand_scaled_budget_root_34": (4, 54, 4336, 110, 4336, 4335, 0),
    "bertrand_scaled_budget_root_35": (4, 86, 4170, 168, 4170, 4169, 0),
    "bertrand_scaled_budget_root_36": (7, 99, 2558, 129, 2558, 2557, 0),
    "bertrand_scaled_budget_root_37": (7, 167, 4062, 132, 4062, 4061, 0),
    "ceil_div_six_budget_of_scaled_le": (3, 20, 25, 15, 25, 24, 0),
    "pow_six_six_le_pow_four_eight_from_total": (8, 164, 510, 49, 497, 509, 13),
    "pow_six_four_le_pow_four_six_from_total": (7, 101, 373, 41, 360, 372, 13),
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total": (5, 110, 150, 37, 150, 149, 0),
    "pow_two_double_eq_pow_four_from_total": (2, 26, 30, 22, 30, 29, 0),
    "pow_two_successor_double_le_pow_four_successor_from_total": (5, 88, 121, 30, 121, 120, 0),
    "pow_eleven_double_block_le_pow_two_seven_block_from_total": (2, 41, 46, 26, 46, 45, 0),
    "pow_eleven_double_block_le_pow_four_even_from_total": (2, 37, 43, 19, 43, 42, 0),
    "pow_eleven_double_block_le_pow_four_odd_from_total": (3, 41, 49, 21, 49, 48, 0),
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total": (2, 41, 46, 26, 46, 45, 0),
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total": (3, 47, 623, 49, 574, 622, 49),
    "bertrand_h_root_32_from_total": (12, 204, 18054, 144, 15590, 18053, 2464),
    "bertrand_h_root_33_from_total": (13, 206, 7557, 149, 6736, 7556, 821),
    "bertrand_h_root_34_from_total": (8, 148, 9093, 144, 7843, 9092, 1250),
    "bertrand_h_root_35_from_total": (12, 201, 7158, 154, 6289, 7157, 869),
    "bertrand_h_root_36_from_total": (13, 244, 12787, 155, 11176, 12786, 1611),
    "bertrand_h_root_37_from_total": (12, 167, 7772, 157, 6788, 7771, 984),
    "bertrand_j_base_thirty_two_window_from_total": (9, 166, 2758, 103, 2616, 2757, 142),
    "bertrand_hj_base_window_thirty_two_from_total": (10, 241, 452, 44, 452, 451, 0),
}

# Each pair is (exact tactic-script SHA-256, statement-plus-dependencies SHA-256).
# NUL separators make command and dependency boundaries unambiguous.
EXPECTED_ARTIFACT_SHA256 = {
    "pow_block_bound_from_total": (
        "761701af400087d348d4ec4d1da135c60c5323b718e9267ba3bc495757e86217",
        "05abe65c2f2e6b7e51c67499a056725c5c8c958fa7f933c3f535d095ba5d425f",
    ),
    "pow_three_five_le_pow_four_four_from_total": (
        "c6bbf24362b330bf8d4436d4aaea43529327ff2741f77fb53a96c95cd3c8212d",
        "6eee34b2db5b01c298b929e7257c65f0dc671d8e2584d19971c90f9c67448626",
    ),
    "pow_eleven_two_le_pow_two_seven_from_total": (
        "5ef971e746a62dc0abab2ae3ccb8a0bfdcbef83e235ba1de078001814b47a040",
        "563e77ee31f4bfe1f42eb62ac40bd18443ae712713f8501b70153212d0983363",
    ),
    "pow_six_ten_le_pow_four_thirteen_from_total": (
        "dca6e705f2fb649442e0a33c71b5c0383aaf6e792d7032777bbb70107c06cf14",
        "e4e4a665a422ee6e8822b11cb2e8a68641e90a17ed3352102ebb3da66aee5a77",
    ),
    "linear_square_budget": (
        "a66c92983bb177afbd8a9e3201fcac1f226b9cb303c9277c22e32fc955ace678",
        "bbe11c315819ca807310809cc0d79823956920b0b75f4cc03770cd285a1920d3",
    ),
    "bertrand_scaled_budget_root_32": (
        "d0d4658925e41230535151879ef0969368a383acfe477989298422010abe4513",
        "a408471f8b7d425b66f34470170d62cecb1eb5fce5da897b9a634a386b39e287",
    ),
    "bertrand_scaled_budget_root_33": (
        "25f6b4694461e2fa207c5547955d0c1357eb9088ac4fabcbcc879ff45004203c",
        "382103e4a911edbc1c3ef81efe45893e40719db379f830f50739dddbe77c8a79",
    ),
    "bertrand_scaled_budget_root_34": (
        "4d2819f8dac5b088a7bb309c5eb872beb96b1ee0025d8370b0372181b25c7ebd",
        "cb5c9df42f783de2c48b27fefb7cef28b235589fc712e9f1c8bf8441b476aed0",
    ),
    "bertrand_scaled_budget_root_35": (
        "786902e615d622915e15de425f405a458df2828c3f13b26210bcdddbd415ff85",
        "e7374acf843795e2062c53c775d5f00bce53a3fba344b70dfc5647b403f9ec02",
    ),
    "bertrand_scaled_budget_root_36": (
        "187d12214fc0c1673f9146ed2fe04a54653e62af5387550c960812460c2b41a2",
        "52be022411c81dc11adb22c80ac64a8d38a238567efde4828cc66bf925b376eb",
    ),
    "bertrand_scaled_budget_root_37": (
        "e66e6f2444ad5145000837d51d5b9ad5931a62ef3fa192fa66536d07346b96b2",
        "8c293c6bce13dccadf34cc7f5e74c4dbeae680a3ca9f6fb04beb6e39e8164c7f",
    ),
    "ceil_div_six_budget_of_scaled_le": (
        "837d24697f8b21d4ef1c6be1ac8d5545d7d8fdf002938719ef1d36308745d12d",
        "95fb018071d447b4ecd2b005a346c570abaaf02646eca89fa21ff03b5941acf5",
    ),
    "pow_six_six_le_pow_four_eight_from_total": (
        "5c3441590a13f3171ca97fd14d67ae8ae7828ee21b6a19035d46f07cfb117702",
        "73573c1b1418923f7a7ea66547d86f344edac8aae55ef467e3540ba02a309184",
    ),
    "pow_six_four_le_pow_four_six_from_total": (
        "57d2757e6f4cf7b34844353227cdc1bfd3daa10abba05884bb20a4c8438cc711",
        "a3e2e03536e01c986592ce8d082c1e4a4777221c5ae287ef5db9ba390686e819",
    ),
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total": (
        "0cc91ce3eabae6e1ad45786786fbad37773cc4c6f737e44546c16318ce8f18ed",
        "0b726582f6d4bf438ce3ec5afa3eb2b212556404e0862743a8b2e0775ef32631",
    ),
    "pow_two_double_eq_pow_four_from_total": (
        "b052a80262a90b217cff10e319f0200d2ff027181692354c2c6c5e106ca25d15",
        "19826ca46770f69be3056446187fdc374599b0650f0fb1162399e925c33b6c17",
    ),
    "pow_two_successor_double_le_pow_four_successor_from_total": (
        "fa83be5836ea157ba996b0c2ab375cad3c5a7b1f96cc75a15bf49170fa28a956",
        "2f78666abce4bc9debfece85b3d34701124ca14ba5ad45dd2261456b4aff48ed",
    ),
    "pow_eleven_double_block_le_pow_two_seven_block_from_total": (
        "8b466a85c4f8ece422123e95dec26f5b3704ba9b998200bc5c1ffe00c3456e3f",
        "205d6c8f7944a1a2d0a7574033b77c99efc14881da9159ae31f06e211eabdf16",
    ),
    "pow_eleven_double_block_le_pow_four_even_from_total": (
        "4059f683de8723ac4b1ddbb5c6c63ff7c368b5f41c599ed074a791bee113a037",
        "deab84c065fba4d9f8d0715cef733b095fd16a3c6f793bf0a5a1a8fc9e7137e8",
    ),
    "pow_eleven_double_block_le_pow_four_odd_from_total": (
        "13a248ac57fc90297fcb0d47187b6656bc69446d9abf499291601e5f3f79f2e2",
        "1c0cc921de32ae42190d169147a238a8541111a228a0623699ecaa2ea161449c",
    ),
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total": (
        "e6f0b83a7ad8194f1f24314e676ee7371cd09828bb94106476d655999c687901",
        "5221fa8503cb5d412befb133a642386974fd9e5ba2b43b8e57495725a4c59fe2",
    ),
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total": (
        "c29eb70625b917410a7074623e6c2fba30978d96186c55537b8c9fb690fe5f4f",
        "f39bfe852cb185b827486c10c5f1d0ba4117be317f1904241445a994fe157fb7",
    ),
    "bertrand_h_root_32_from_total": (
        "a47471af64b1828701d774e76d12627711f707a0c3fc8bff4452157c0033c832",
        "c54ffc5a1a9282bd57159286c75d2ea36ea7c242aab34be748a719939165ca97",
    ),
    "bertrand_h_root_33_from_total": (
        "c74626204487195e1782c7e9b14bc51912f3c75460aba547076e65afc5698255",
        "d67259e988fc17e6d24c46107647090c5359374a2b2641a18037d6ec2ec54e4b",
    ),
    "bertrand_h_root_34_from_total": (
        "814728e30a9f4c918caab6bd615916244415911777cd919a4ae3e5395b56c3e5",
        "48ed963238987150e2966b03642881bd18d765597b8d70ade609d368a5aa787e",
    ),
    "bertrand_h_root_35_from_total": (
        "3a45ff093aacfe922aced7bde934f213a7c9b54e267e31e54a893d11cec7af32",
        "090b92899ae360f489ed969681047badaab5fe55702a5db6e6ff1d43619ce75c",
    ),
    "bertrand_h_root_36_from_total": (
        "7439a11576decb97bf15afb384ac0b457ad4777e9174b206671369a00c7c1b11",
        "b46162c9e580225a070513532012ed2149946a00318407e00adf6b4e052bc954",
    ),
    "bertrand_h_root_37_from_total": (
        "e7a6072ca94ea40c2455ab256d5ac9bea219782169b0f7055219693ec890b548",
        "c6237d629617984c01e98dbe7fe6a082b92fe856428275a8975475affcf8a90b",
    ),
    "bertrand_j_base_thirty_two_window_from_total": (
        "025375dc6e84fd84afb02edf2377922bf1dfe00de7e7f1360f9a726fab7fa67e",
        "949b2048547b85692ac8ce5527edba51643b1be225ef90853d0c15e4222f67b2",
    ),
    "bertrand_hj_base_window_thirty_two_from_total": (
        "a6ca3892739b73fb84266a15ca7b2957cc1cfad25d38320d6a4632818b807127",
        "3289096b88f7c9e82e89c756adc422583672cb14e2a149d1f03cf8f07da692ce",
    ),
}

POW_TOTAL_TAGS = {
    "pow_block_bound_from_total": "hj32_block",
    "pow_three_five_le_pow_four_four_from_total": "hj32_three_four",
    "pow_eleven_two_le_pow_two_seven_from_total": "hj32_eleven_two",
    "pow_six_ten_le_pow_four_thirteen_from_total": "hj32_six_ten",
    "pow_six_six_le_pow_four_eight_from_total": "hj32_residual_six",
    "pow_six_four_le_pow_four_six_from_total": "hj32_residual_four",
    "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total": "hj32_three_plus",
    "pow_two_double_eq_pow_four_from_total": "hj32_two_double",
    "pow_two_successor_double_le_pow_four_successor_from_total": "hj32_two_odd",
    "pow_eleven_double_block_le_pow_two_seven_block_from_total": "hj32_eleven_block",
    "pow_eleven_double_block_le_pow_four_even_from_total": "hj32_eleven_even",
    "pow_eleven_double_block_le_pow_four_odd_from_total": "hj32_eleven_odd",
    "pow_six_ten_block_le_pow_four_thirteen_block_from_total": "hj32_six_block",
    "pow_thirty_six_double_block_eq_pow_six_four_block_from_total": "hj32_thirty_six_block",
    **{
        f"bertrand_h_root_{root}_from_total": f"hj32_h_root_{root}"
        for root in range(32, 38)
    },
    "bertrand_j_base_thirty_two_window_from_total": "hj32_base",
    "bertrand_hj_base_window_thirty_two_from_total": "hj32_base",
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
        *make_bertrand_threshold_base_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_base_thirty_two_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


def test_hj_base_thirty_two_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_hj_base_thirty_two_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENTS
    assert {
        item.name: (
            sha256("\0".join(item.script).encode()).hexdigest(),
            sha256(
                "\0".join((item.statement, *item.dependencies)).encode()
            ).hexdigest(),
        )
        for item in specs
    } == EXPECTED_ARTIFACT_SHA256

    public = _specs_by_name()
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert item.name not in public
        assert all(
            token not in item.statement
            for token in (
                "Pow(",
                "PowTotal",
                "CeilDivSix(",
                "^",
                "**",
                "<=",
            )
        )


def test_hj_base_thirty_two_h_rows_reuse_canonical_budget_terms() -> None:
    specs = {item.name: item for item in _specs()}
    for root, budget in ROOT_BUDGET_TERMS.items():
        budget_commands = specs[f"bertrand_scaled_budget_root_{root}"].script
        h_commands = specs[f"bertrand_h_root_{root}_from_total"].script

        assert f"specialize linear_square_budget ({budget})" in budget_commands
        assert (
            f"specialize ceil_div_six_budget_of_scaled_le ({budget})"
            in h_commands
        )
        assert (
            f"specialize pow_exponent_monotone_from_total {budget}"
            in h_commands
        )
        assert any(
            command.startswith(f"have h{root}")
            and "_p4_" in command
            and budget in command
            for command in h_commands
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_hj_base_thirty_two_bodies_are_constructive(name: str) -> None:
    item = next(item for item in _specs() if item.name == name)
    receipt = replay_candidate_bodies((item,), core=_available())[0]
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODIES[name]

    assert all(
        forbidden not in command
        for command in item.script
        for forbidden in (
            "DNE",
            "classical",
            "by_contra",
            "sorry",
            "auto",
            "compact_arith",
            "ring",
        )
    )


def test_hj_base_thirty_two_every_declared_dependency_is_live() -> None:
    available = _available()
    removed_edges = 0
    for item in _specs():
        for dependency in item.dependencies:
            shortened = replace(
                item,
                dependencies=tuple(
                    name for name in item.dependencies if name != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((shortened,), core=available)
            removed_edges += 1
    assert removed_edges == sum(len(item.dependencies) for item in _specs())


def test_hj_base_thirty_two_false_and_totality_mutations_are_rejected() -> None:
    available = _available()
    for item in _specs():
        false_contract = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_contract,), core=available)

    specs = {item.name: item for item in _specs()}
    for name, tag in POW_TOTAL_TAGS.items():
        item = specs[name]
        total = power_total_relation(tag=tag)
        assert item.statement.count(total) == 1
        weakened = replace(item, statement=item.statement.replace(total, "0 = 0"))
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((weakened,), core=available)


def test_hj_base_thirty_two_boundary_mutations_are_rejected() -> None:
    specs = {item.name: item for item in _specs()}
    block = specs["pow_block_bound_from_total"]
    three_four = specs["pow_three_five_le_pow_four_four_from_total"]
    eleven_two = specs["pow_eleven_two_le_pow_two_seven_from_total"]
    six_ten = specs["pow_six_ten_le_pow_four_thirteen_from_total"]
    linear = specs["linear_square_budget"]
    root_32_budget = specs["bertrand_scaled_budget_root_32"]
    ceil_budget = specs["ceil_div_six_budget_of_scaled_le"]
    residual_six = specs["pow_six_six_le_pow_four_eight_from_total"]
    residual_four = specs["pow_six_four_le_pow_four_six_from_total"]
    three_plus = specs[
        "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total"
    ]
    two_double = specs["pow_two_double_eq_pow_four_from_total"]
    two_odd = specs["pow_two_successor_double_le_pow_four_successor_from_total"]
    eleven_block = specs[
        "pow_eleven_double_block_le_pow_two_seven_block_from_total"
    ]
    eleven_even = specs["pow_eleven_double_block_le_pow_four_even_from_total"]
    eleven_odd = specs["pow_eleven_double_block_le_pow_four_odd_from_total"]
    six_block = specs[
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total"
    ]
    thirty_six = specs[
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total"
    ]
    h_32 = specs["bertrand_h_root_32_from_total"]
    h_37 = specs["bertrand_h_root_37_from_total"]
    j_window = specs["bertrand_j_base_thirty_two_window_from_total"]
    base = specs["bertrand_hj_base_window_thirty_two_from_total"]
    mutations = (
        replace(block, statement=block.statement.replace("d * m", "S (d * m)", 1)),
        replace(three_four, statement=three_four.statement.replace(
            _power_terms("3", "5", "x", tag="hj32_three_five"),
            _power_terms("3", "6", "x", tag="hj32_three_five"),
        )),
        replace(eleven_two, statement=eleven_two.statement.replace(
            _power_terms("2", "7", "y", tag="hj32_eleven_two_right"),
            _power_terms("2", "6", "y", tag="hj32_eleven_two_right"),
        )),
        replace(six_ten, statement=six_ten.statement.replace(
            witness_le("x", "y", tag="hj32_six_ten_result"),
            witness_le("S x", "y", tag="hj32_six_ten_result"),
        )),
        replace(linear, statement=linear.statement.replace(
            witness_le("a * k", "r * r", tag="hj32_linear_square_budget"),
            witness_le("S (a * k)", "r * r", tag="hj32_linear_square_budget"),
        )),
        replace(root_32_budget, statement=root_32_budget.statement.replace(
            witness_le(
                "6 * ((4 * 13 + 1) + 4 * 29)",
                "32 * 32",
                tag="hj32_scaled_budget_root_32",
            ),
            witness_le(
                "S (6 * ((4 * 13 + 1) + 4 * 29))",
                "32 * 32",
                tag="hj32_scaled_budget_root_32",
            ),
        )),
        replace(ceil_budget, statement=ceil_budget.statement.replace(
            witness_le("k", "e", tag="hj32_ceil_budget_result"),
            witness_le("S k", "e", tag="hj32_ceil_budget_result"),
        )),
        replace(residual_six, statement=residual_six.statement.replace(
            _power_terms("4", "8", "y", tag="hj32_residual_six_right"),
            _power_terms("4", "7", "y", tag="hj32_residual_six_right"),
        )),
        replace(residual_four, statement=residual_four.statement.replace(
            _power_terms("4", "6", "y", tag="hj32_residual_four_right"),
            _power_terms("4", "5", "y", tag="hj32_residual_four_right"),
        )),
        replace(three_plus, statement=three_plus.statement.replace(
            _power_terms(
                "3", "5 * m + 1", "x", tag="hj32_three_plus_left"
            ),
            _power_terms(
                "3", "5 * m + 2", "x", tag="hj32_three_plus_left"
            ),
        )),
        replace(two_double, statement=two_double.statement.replace(
            " -> x = y", " -> S x = y", 1
        )),
        replace(two_odd, statement=two_odd.statement.replace(
            witness_le("x", "y", tag="hj32_two_odd_result"),
            witness_le("S x", "y", tag="hj32_two_odd_result"),
        )),
        replace(eleven_block, statement=eleven_block.statement.replace(
            _power_terms(
                "11", "2 * m", "x", tag="hj32_eleven_block_left"
            ),
            _power_terms(
                "11", "2 * m + 1", "x", tag="hj32_eleven_block_left"
            ),
        )),
        replace(eleven_even, statement=eleven_even.statement.replace(
            " -> 7 * m = 2 * k ->", " -> 7 * m = 2 * k + 1 ->", 1
        )),
        replace(eleven_odd, statement=eleven_odd.statement.replace(
            " -> 7 * m = 2 * k + 1 ->", " -> 7 * m = 2 * k + 2 ->", 1
        )),
        replace(six_block, statement=six_block.statement.replace(
            _power_terms(
                "4", "13 * m", "y", tag="hj32_six_block_right"
            ),
            _power_terms(
                "4", "12 * m", "y", tag="hj32_six_block_right"
            ),
        )),
        replace(thirty_six, statement=thirty_six.statement.replace(
            " -> x = y", " -> S x = y", 1
        )),
        replace(h_32, statement=h_32.statement.replace(
            witness_le("h", "u", tag="hj32_h_root_32_result"),
            witness_le("S h", "u", tag="hj32_h_root_32_result"),
        )),
        replace(h_37, statement=h_37.statement.replace(
            witness_le("h", "u", tag="hj32_h_root_37_result"),
            witness_le("S h", "u", tag="hj32_h_root_37_result"),
        )),
        replace(j_window, statement=j_window.statement.replace(
            witness_le("32", "s", tag="hj32_base_lower"),
            witness_le("31", "s", tag="hj32_base_lower"),
        )),
        replace(j_window, statement=j_window.statement.replace(
            witness_le("s", "37", tag="hj32_base_upper"),
            witness_le("s", "38", tag="hj32_base_upper"),
        )),
        replace(j_window, statement=j_window.statement.replace(
            witness_le("j", "g", tag="hj32_base_j_result"),
            witness_le("S j", "g", tag="hj32_base_j_result"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("32", "s", tag="hj32_base_lower"),
            witness_le("31", "s", tag="hj32_base_lower"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("s", "37", tag="hj32_base_upper"),
            witness_le("s", "38", tag="hj32_base_upper"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("h", "u", tag="hj32_base_h_result"),
            witness_le("S h", "u", tag="hj32_base_h_result"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("j", "g", tag="hj32_base_j_result"),
            witness_le("S j", "g", tag="hj32_base_j_result"),
        )),
    )
    for mutated in mutations:
        assert mutated.statement != specs[mutated.name].statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=_available())


def test_hj_base_thirty_two_standard_natural_semantics_are_regression_only() -> None:
    assert 3**5 == 243 <= 256 == 4**4
    assert 11**2 == 121 <= 128 == 2**7
    assert 6**10 == 60_466_176 <= 67_108_864 == 4**13

    budgets = {32: 169, 33: 177, 34: 182, 35: 188, 36: 204, 37: 209}
    for root, budget in budgets.items():
        ceiling = (root * root + 5) // 6
        assert 6 * budget <= root * root <= 6 * ceiling
        assert (root + 1) ** (2 * root + 2) <= 4**budget <= 4**ceiling
        assert (root + 7) ** 12 <= 4**33 <= 4 ** (root + 5)

    # The lower ceiling half used in the proof is the exact authoring surface.
    ceiling_formula = ceil_div_six_relation("s * s", "e", tag="hj32_base_ceiling")
    assert "s * s" in ceiling_formula
    assert "6 * (e)" in ceiling_formula
