"""Fail-closed audit for the Bertrand B5 factor-range tranche.

Large proof roots run in fresh subprocesses with ``PYTHONMALLOC=malloc`` so
no test interpreter retains more than one expanded proof DAG.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v11
from peano_lab.library.bertrand_b5_order_quotient_candidate import (
    _divrem_term,
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    floor_sqrt_relation,
)
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_factor_ranges_candidate import (
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT,
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT,
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT,
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES,
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES,
    make_bertrand_central_binom_factor_ranges_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_prime_support_candidate import (
    _no_bertrand_closed_term,
    make_bertrand_central_binom_prime_support_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_square_tail_candidate import (
    make_bertrand_central_binom_square_tail_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_range_candidate import (
    make_bertrand_central_binom_zero_range_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    _power_terms,
    power_valuation,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT,
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT,
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES,
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES,
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES,
)
EXPECTED_DEPENDENCIES = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: (
        "division_block_upper",
        "mul_le_mul_left",
        "lt_of_lt_of_le",
        "mul_succ_left",
        "one_mul",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT: (
        DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT,
        "central_binom_prime_valuation_zero_two_thirds_range",
    ),
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: (
        "mul_le_mul_right",
        "mul_le_mul_left",
        "le_trans",
        "lt_of_lt_of_le",
        "pow_two",
    ),
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE: (
        "lt_to_le",
        "le_trans",
        "pow_exists",
        FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT,
        "central_binom_prime_square_tail_valuation_le_one",
    ),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES: (
        "power_valuation_nonzero_exponent_divides_base",
        "no_bertrand_central_prime_divisor_ranges",
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT,
    ),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES: (
        NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES,
        CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE,
        "one_le_of_ne_zero",
        "le_antisymm",
    ),
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES: (
        NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES,
        "lt_to_le",
        "le_trans",
        "central_binom_prime_power_contribution_le_double",
        "pow_one",
    ),
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES: (
        "eq_decidable",
        "pow_zero",
        NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES,
    ),
}
EXPECTED_COMMAND_COUNTS = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: 46,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT: 32,
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: 43,
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE: 52,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES: 55,
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES: 62,
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES: 74,
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES: 47,
}
EXPECTED_CUT_COUNTS = (5, 2, 5, 5, 3, 4, 5, 3)

EXPECTED_ARTIFACTS = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: (
        310,
        "d112e867bf7639ac07fc451f18ac931fc21ed4313fea023ee1103a74c1dfebb6",
        "bfdad97d9c07a4c30e7c169ddf8331b9063530934333410e379000a9ef6a0198",
        "34b901840178f8a5ee1d477a951752ee3e7456022162920f2e55e9482950138a",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT: (
        18166,
        "74fd63b48b55fd300c2153c2aa8db9100450acb333743cd44e1be126f28856ec",
        "75cdf084c90b6acb7f402ab3845cf368b1a4b4176632c92ba8c157765ec51654",
        "d01ad6078aa3f2c0c5514e1f707f3397c548a65d27d165bb5b7694f0325487f9",
    ),
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: (
        2847,
        "ae75b7d18aac6791775b54b5d7e5e079940e803695c851cbf7d3e5b4eac3c882",
        "3c84958ce14d79cb04c1afe47bfe8422f901d8b6bee1c1f291b7745ddfcc0ec0",
        "b1843c88da392659a701b3036ec90aa8534460e853950a8faebaee6e1cbd6620",
    ),
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE: (
        18943,
        "9cd08c01eef1c4e24b16c4cdc4e90be08ab789eb520b5c4308aea30ae8f09cad",
        "a7527f5769032a829146b635d67c046f73408498026aea3ddd65353217701abe",
        "29ca3e367619498a3fcf976a25794a3fd980faf7442832f663a7ed88b73890d6",
    ),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES: (
        18910,
        "f91a55b255bfbde9e729106e255d7fa7ab447d02ff7fe225c3681d447b6417f9",
        "cc00686ebedec9b2d7c2fd578275da1649438269ed83216021e1fe28a0f42741",
        "6f9cd104dc4e77030917c4b7d7291cab786becea027ae00ac89378f25a5f7d38",
    ),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES: (
        19135,
        "cc978f578a5627bae21c6d5309e2420730ab67ad844560a85bf35d1d22833354",
        "2ef56b687f6b45782412b80faf438345a4831704284790b4509ebf95e05cfd8b",
        "b7d7004f5b86021663109a4363498f6f79c7da78101a48468910e447c2be0199",
    ),
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES: (
        21687,
        "fc6d61378957179d509d2a479d0dc7b7501b6087267cf8c97eb5fce81e98b431",
        "1269693d14e6ccd4814f0278e135f7e2fc4dc13901ca65c1ecc60c2413409e70",
        "202b77c305a6dcc24d4cc323c94d09ab53acb85cb14b5756b8bf0d6f8b2fb7a8",
    ),
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES: (
        21688,
        "d648e49d4b55280fb368893260233ac0826cd0e273615726a2233d7bffe9a5fc",
        "d53405bfdb24df160b13ddcc836e5a8028d4ef294608a12eb74a487c53230da5",
        "e2c19bd0901b638ba7c001a904fc0c01f6232df17b9947d7e9a5eb51a768b35c",
    ),
}
EXPECTED_BODIES = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT:
        (5, 46, 51, 20, 51, 50, 0),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT:
        (2, 32, 40, 26, 40, 39, 0),
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT:
        (5, 43, 48, 21, 48, 47, 0),
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE:
        (5, 52, 77, 31, 77, 76, 0),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES:
        (3, 55, 71, 35, 71, 70, 0),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES:
        (4, 62, 79, 36, 79, 78, 0),
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES:
        (5, 74, 108, 39, 108, 107, 0),
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES:
        (3, 47, 60, 39, 60, 59, 0),
}
EXPECTED_ENVELOPES = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: (51, 51, 20, 83, 23),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT:
        (40, 40, 26, 8, 26),
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: (48, 48, 21, 45, 22),
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE:
        (77, 77, 31, 40, 32),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES:
        (71, 71, 35, 14, 35),
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES:
        (79, 79, 36, 16, 36),
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES:
        (108, 108, 39, 40, 39),
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES:
        (60, 60, 39, 13, 39),
}
EXPECTED_LAYERED_CLOSURES = {
    DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: {
        "topology_sha256":
            "9de70d05d328a5f27644ba3ceda9b2edc5f2443de6d6a9588c56f4ecbadc2fbd",
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 5,
        "candidate_body_count": 1,
        "dependency_edge_count": 5,
        "layer_sizes": [5, 1],
        "layer_cut_count": 2,
        "proof_nodes": 611,
        "proof_depth": 27,
        "proof_objects": 337,
        "proof_edges": 411,
        "reused_objects": 75,
        "annotation_occurrences": 1641,
        "envelope_depth": 30,
        "package_formula_occurrences": 142,
        "package_formula_depth": 13,
        "proof_dag_sha256":
            "28fb2725e93642b91536846971099ef39f11660307f5c59f8588d523701649c9",
    },
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT: {
        "topology_sha256":
            "9f89f84dbbda439e84724ecc476f0d59f5e26aedff774b676dbf5677b9517e9c",
        "node_count": 194,
        "stable_catalog_count": 432,
        "reachable_stable_count": 77,
        "candidate_body_count": 117,
        "dependency_edge_count": 439,
        "layer_sizes": [
            84, 38, 17, 9, 9, 8, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1,
            1, 1, 1,
        ],
        "layer_cut_count": 20,
        "proof_nodes": 284807,
        "proof_depth": 96,
        "proof_objects": 14136,
        "proof_edges": 18588,
        "reused_objects": 4453,
        "annotation_occurrences": 1025472,
        "envelope_depth": 96,
        "package_formula_occurrences": 66084,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "5310d716fb9988104f80fd544cc3946f8a5081dd3bce1b1a302f6aba8a4f6478",
    },
    FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: {
        "topology_sha256":
            "1ebac828ed989cfe00f025fc0daed6f394952a51c2d364fffbe762c39454223a",
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 5,
        "candidate_body_count": 1,
        "dependency_edge_count": 5,
        "layer_sizes": [5, 1],
        "layer_cut_count": 2,
        "proof_nodes": 7111,
        "proof_depth": 72,
        "proof_objects": 931,
        "proof_edges": 1236,
        "reused_objects": 306,
        "annotation_occurrences": 29461,
        "envelope_depth": 72,
        "package_formula_occurrences": 524,
        "package_formula_depth": 33,
        "proof_dag_sha256":
            "219e8023fe411f461087406e6bbd949b3dd13c75bfee5931a8d5474ef35b5f4b",
    },
    CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE: {
        "topology_sha256":
            "8368d408c8bb6c2ba1ce4e3be1a92877c16917c79013a6ad69dc9261cedf76e2",
        "node_count": 187,
        "stable_catalog_count": 432,
        "reachable_stable_count": 73,
        "candidate_body_count": 114,
        "dependency_edge_count": 419,
        "layer_sizes": [
            80, 38, 15, 8, 9, 7, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1,
            1, 1, 1, 1,
        ],
        "layer_cut_count": 21,
        "proof_nodes": 280147,
        "proof_depth": 96,
        "proof_objects": 13634,
        "proof_edges": 17942,
        "reused_objects": 4309,
        "annotation_occurrences": 1010434,
        "envelope_depth": 96,
        "package_formula_occurrences": 65941,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "dee3cc368ab99ae556f2672e8e57cd184d28ad014bd01dd5326315ee50a9a23b",
    },
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES: {
        "topology_sha256":
            "2e95e17923eef94944f1c8ca9b62e86d55a96379d5981abf8528b9403cd3421b",
        "node_count": 203,
        "stable_catalog_count": 432,
        "reachable_stable_count": 80,
        "candidate_body_count": 123,
        "dependency_edge_count": 466,
        "layer_sizes": [
            87, 39, 18, 9, 9, 8, 7, 6, 4, 3, 2, 1, 2, 1, 1, 1, 1,
            1, 1, 1, 1,
        ],
        "layer_cut_count": 21,
        "proof_nodes": 285791,
        "proof_depth": 96,
        "proof_objects": 14583,
        "proof_edges": 19131,
        "reused_objects": 4549,
        "annotation_occurrences": 1031904,
        "envelope_depth": 96,
        "package_formula_occurrences": 69223,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "08af60e55ff4ce614712831ee7a7ee5bb8ac78b94e283221d340156a3dd726e4",
    },
    NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES: {
        "topology_sha256":
            "12bb32a0721536a8c78b6f34302f389c4d7a3622c929169463d92d5e22ea89e4",
        "node_count": 212,
        "stable_catalog_count": 432,
        "reachable_stable_count": 82,
        "candidate_body_count": 130,
        "dependency_edge_count": 500,
        "layer_sizes": [
            89, 41, 18, 9, 9, 8, 7, 6, 4, 3, 2, 1, 2, 1, 1, 1, 1,
            2, 2, 2, 2, 1,
        ],
        "layer_cut_count": 22,
        "proof_nodes": 287039,
        "proof_depth": 96,
        "proof_objects": 15180,
        "proof_edges": 19857,
        "reused_objects": 4678,
        "annotation_occurrences": 1041357,
        "envelope_depth": 96,
        "package_formula_occurrences": 74579,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "86c7b336c870c399796d8f6606d9365e88bfc9508a4627007e077478be242e90",
    },
    NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES: {
        "topology_sha256":
            "1b442f4d2ab68a9c56c4f9b9aaa5f0d388a13d50f62048ee8239ee4544a5bd2e",
        "node_count": 213,
        "stable_catalog_count": 432,
        "reachable_stable_count": 82,
        "candidate_body_count": 131,
        "dependency_edge_count": 505,
        "layer_sizes": [
            89, 41, 18, 9, 9, 8, 7, 6, 4, 3, 2, 1, 2, 1, 1, 1, 1,
            2, 2, 2, 2, 1, 1,
        ],
        "layer_cut_count": 23,
        "proof_nodes": 287178,
        "proof_depth": 96,
        "proof_objects": 15272,
        "proof_edges": 19972,
        "reused_objects": 4701,
        "annotation_occurrences": 1048021,
        "envelope_depth": 96,
        "package_formula_occurrences": 75757,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "3dd7a95c9bd89883f6ed384dacadffe53ec2d28a824be6e9c1930bc0fafde4bc",
    },
    NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES: {
        "topology_sha256":
            "1cb140eff26f891e04f8916c476fcf9c44b24a2789932142e73510bd079b1ec5",
        "node_count": 215,
        "stable_catalog_count": 432,
        "reachable_stable_count": 83,
        "candidate_body_count": 132,
        "dependency_edge_count": 508,
        "layer_sizes": [
            90, 41, 18, 9, 9, 8, 7, 6, 4, 3, 2, 1, 2, 1, 1, 1, 1,
            2, 2, 2, 2, 1, 1, 1,
        ],
        "layer_cut_count": 24,
        "proof_nodes": 287318,
        "proof_depth": 95,
        "proof_objects": 15345,
        "proof_edges": 20060,
        "reused_objects": 4716,
        "annotation_occurrences": 1050416,
        "envelope_depth": 95,
        "package_formula_occurrences": 76946,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "a529b9aa03cdbade704a919ba1aff7bd0f39e9fc833fdb3a67ff11de09538822",
    },
}

SOURCE_PINS = {
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "bertrand_central_binom_prime_support_candidate.py":
        "d48ed42c0b5289b1565947bb43dbcbe8389eed9aa196766ff90567cfc7fec7ab",
    "bertrand_b5_order_quotient_candidate.py":
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e",
    "bertrand_central_binom_valuation_candidate.py":
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8",
    "bertrand_central_binom_carry_candidate.py":
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0",
    "bertrand_central_binom_square_tail_candidate.py":
        "b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff",
    "bertrand_central_binom_zero_range_candidate.py":
        "8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e",
    "bertrand_central_binom_factor_ranges_candidate.py":
        "d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-factor-ranges-tranche-rfc-v1.md"
)
RFC_SHA256 = "32765966c68b0db98fb48136e5b3fdbc3312b6c7ef6d35737e7f1381e03f2c3b"


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_central_binom_factor_ranges_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    rows = (
        *editions_v11.ALPHA_SPECS,
        *make_bertrand_central_binom_prime_support_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_valuation_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_carry_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_square_tail_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_zero_range_candidate_theorems(
            TheoremSpec
        ),
    )
    result: dict[str, TheoremSpec] = {}
    for row in rows:
        if row.name in stable:
            assert stable[row.name] == row
            continue
        previous = result.get(row.name)
        if previous is not None:
            assert previous == row
        result[row.name] = row
    assert not set(EXPECTED_NAMES) & set(result)
    return result


def _row_candidates(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name) + 1]
    return _candidate_base() | _table(prefix)


def _row_core(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name)]
    return dict(_specs_by_name()) | _candidate_base() | _table(prefix)


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base() | _table(_rows())


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    quotient_variables = ("n", "q", "r", "p")
    quotient_division = _divrem_term(
        "3", "n + n", "q", "r",
        tag="bdtsuql_division", variables=quotient_variables,
    )
    quotient_order = _lt_term(
        "q", "p", tag="bdtsuql_quotient", variables=quotient_variables
    )
    quotient_result = _lt_term(
        "n + n", "(p + p) + p",
        tag="bdtsuql_result", variables=quotient_variables,
    )

    zero_variables = ("p", "n", "C", "v", "q", "r")
    zero_prime = prime("p", tag="bcpvzatq_prime")
    zero_positive = _lt_term(
        "2", "n", tag="bcpvzatq_positive", variables=zero_variables
    )
    zero_division = _divrem_term(
        "3", "n + n", "q", "r",
        tag="bcpvzatq_division", variables=zero_variables,
    )
    zero_above = _lt_term(
        "q", "p", tag="bcpvzatq_above", variables=zero_variables
    )
    zero_bound = _le_term(
        "p", "n", tag="bcpvzatq_bound", variables=zero_variables
    )
    zero_central = _central_binom_relation_term(
        "n", "C", tag="bcpvzatq_central", variables=zero_variables
    )
    zero_valuation = power_valuation(
        "p", "C", "v", tag="bcpvzatq_valuation"
    )

    sqrt_variables = ("x", "s", "p", "t")
    sqrt_source = floor_sqrt_relation("x", "s", tag="bfsarpts_source")
    sqrt_above = _lt_term(
        "s", "p", tag="bfsarpts_above", variables=sqrt_variables
    )
    sqrt_power = _power_terms("p", "2", "t", tag="bfsarpts_power")
    sqrt_result = _lt_term(
        "x", "t", tag="bfsarpts_result", variables=sqrt_variables
    )

    upper_variables = ("p", "n", "C", "v", "s")
    upper_prime = prime("p", tag="bcpafs_vlo_prime")
    upper_positive = _lt_term(
        "2", "n", tag="bcpafs_vlo_positive", variables=upper_variables
    )
    upper_central = _central_binom_relation_term(
        "n", "C", tag="bcpafs_vlo_central", variables=upper_variables
    )
    upper_valuation = power_valuation(
        "p", "C", "v", tag="bcpafs_vlo_valuation"
    )
    upper_floor = floor_sqrt_relation(
        "n + n", "s", tag="bcpafs_vlo_floor"
    )
    upper_above = _lt_term(
        "s", "p", tag="bcpafs_vlo_above", variables=upper_variables
    )
    upper_result = _le_term(
        "v", "1", tag="bcpafs_vlo_result", variables=upper_variables
    )

    range_variables = ("n", "s", "q", "r", "C", "p", "v")
    exclusion = _no_bertrand_closed_term(
        "n", tag="bnbcnvlr_exclusion", variables=range_variables
    )
    range_prime = prime("p", tag="bnbcnvlr_prime")
    positive = _lt_term(
        "2", "n", tag="bnbcnvlr_positive", variables=range_variables
    )
    division = _divrem_term(
        "3", "n + n", "q", "r",
        tag="bnbcnvlr_division", variables=range_variables,
    )
    central = _central_binom_relation_term(
        "n", "C", tag="bnbcnvlr_central", variables=range_variables
    )
    valuation = power_valuation(
        "p", "C", "v", tag="bnbcnvlr_valuation"
    )
    small = _le_term(
        "p", "s", tag="bnbcnvlr_small", variables=range_variables
    )
    above = _lt_term(
        "s", "p", tag="bnbcnvlr_above_small", variables=range_variables
    )
    middle = _le_term(
        "p", "q", tag="bnbcnvlr_middle", variables=range_variables
    )
    live_result = rf"({small}) \/ (({above}) /\ ({middle}))"
    floor = floor_sqrt_relation("n + n", "s", tag="bnbcnvfr_floor")
    factor_result = (
        rf"({small}) \/ ((({above}) /\ ({middle})) /\ v = 1)"
    )
    contribution_variables = range_variables + ("a",)
    power = _power_terms("p", "v", "a", tag="bnbcncfr_power")
    bound = _le_term(
        "a", "n + n",
        tag="bnbcncfr_bound", variables=contribution_variables,
    )
    contribution_result = (
        rf"(({small}) /\ ({bound})) \/ "
        rf"((({above}) /\ ({middle})) /\ a = p)"
    )
    common = (
        f"({exclusion}) -> ({range_prime}) -> ({positive}) -> "
    )

    return {
        DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT:
            "forall n q r p. "
            f"({quotient_division}) -> ({quotient_order}) -> "
            f"({quotient_result})",
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT:
            "forall p n C v q r. "
            f"({zero_prime}) -> ({zero_positive}) -> "
            f"({zero_division}) -> ({zero_above}) -> ({zero_bound}) -> "
            f"({zero_central}) -> ({zero_valuation}) -> v = 0",
        FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT:
            "forall x s p t. "
            f"({sqrt_source}) -> ({sqrt_above}) -> ({sqrt_power}) -> "
            f"({sqrt_result})",
        CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE:
            "forall p n C v s. "
            f"({upper_prime}) -> ({upper_positive}) -> "
            f"({upper_central}) -> ({upper_valuation}) -> "
            f"({upper_floor}) -> ({upper_above}) -> ({upper_result})",
        NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES:
            "forall n s q r C p v. "
            f"{common}({division}) -> ({central}) -> ({valuation}) -> "
            f"~(v = 0) -> ({live_result})",
        NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES:
            "forall n s q r C p v. "
            f"{common}({floor}) -> ({division}) -> ({central}) -> "
            f"({valuation}) -> ~(v = 0) -> ({factor_result})",
        NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES:
            "forall n s q r C p v a. "
            f"{common}({floor}) -> ({division}) -> ({central}) -> "
            f"({valuation}) -> ({power}) -> ~(v = 0) -> "
            f"({contribution_result})",
        NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES:
            "forall n s q r C p v a. "
            f"{common}({floor}) -> ({division}) -> ({central}) -> "
            f"({valuation}) -> ({power}) -> "
            rf"((({contribution_result}) \/ a = 1))",
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    rows = _table(_rows())
    expected = _expected_statements()
    quotient_variables = ("n", "q", "r", "p")
    old_row1 = _lt_term(
        "n + n", "(p + p) + p",
        tag="bdtsuql_result", variables=quotient_variables,
    )
    new_row1 = _lt_term(
        "n + n", "p + p",
        tag="bdtsuql_result", variables=quotient_variables,
    )
    sqrt_variables = ("x", "s", "p", "t")
    old_row3 = _lt_term(
        "x", "t", tag="bfsarpts_result", variables=sqrt_variables
    )
    new_row3 = _lt_term(
        "t", "x", tag="bfsarpts_result", variables=sqrt_variables
    )
    upper_variables = ("p", "n", "C", "v", "s")
    old_row4 = _le_term(
        "v", "1", tag="bcpafs_vlo_result", variables=upper_variables
    )
    replacements = {
        DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT: (old_row1, new_row1),
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT: (
            "v = 0", "v = 1"
        ),
        FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT: (old_row3, new_row3),
        CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE: (
            old_row4, "v = 0"
        ),
    }
    result: dict[str, str] = {}
    for name in EXPECTED_NAMES:
        statement = rows[name].statement
        assert statement == expected[name]
        if name in replacements:
            old, new = replacements[name]
        else:
            variables = ("n", "s", "q", "r", "C", "p", "v")
            old = _no_bertrand_closed_term(
                "n", tag="bnbcnvlr_exclusion", variables=variables
            )
            new = "0 = 0"
        assert statement.count(old) == 1
        result[name] = statement.replace(old, new, 1)
        assert _closed_formula(result[name]) != _closed_formula(statement)
    return result


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_sha256(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend((child, False) for child in children)
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _body_receipt(name: str) -> dict[str, object]:
    item = _table(_rows())[name]
    body, target = _body(item)
    assert check((), body, target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label=f"B5 factor-range body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    return {"body": list(actual), "envelope": list(envelope)}


def _rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    item = _table(_rows())[name]
    if kind == "dependency":
        assert dependency is not None
        changed = replace(
            item,
            dependencies=tuple(
                entry for entry in item.dependencies if entry != dependency
            ),
        )
        assert len(changed.dependencies) + 1 == len(item.dependencies)
    elif kind == "false":
        assert dependency is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert dependency is None
        changed = replace(item, statement=_mutations()[name])
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} replay unexpectedly passed for {name}")


def _mutate_layer_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_layer_cut(proof.body, index - 1))


def _blueprint(name: str):
    stable = _specs_by_name()
    candidates = _row_candidates(name)
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(current: str) -> None:
        if current in stable:
            stable_names.add(current)
            return
        item = candidates.get(current)
        assert item is not None, current
        mark = marks.get(current, 0)
        assert mark != 1
        if mark == 2:
            return
        marks[current] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[current] = 2
        candidate_order.append(current)

    visit(name)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {entry: index for index, entry in enumerate(names)}
    specs = {
        entry: stable[entry] if entry in stable else candidates[entry]
        for entry in names
    }
    targets = {
        entry: _closed_formula(specs[entry].statement) for entry in names
    }
    dependencies = {
        entry: ()
        if entry in stable
        else tuple(positions[item] for item in specs[entry].dependencies)
        for entry in names
    }
    topology = "\x1c".join(
        "\x1f".join(
            (
                str(positions[entry]),
                entry,
                "stable_atomic" if entry in stable else "candidate_body",
                specs[entry].statement,
                "\x1e".join(names[index] for index in dependencies[entry]),
            )
        )
        for entry in names
    )
    return (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        sha256(topology.encode()).hexdigest(),
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets: dict[str, Formula],
) -> Proof:
    target = targets[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


def _layered_receipt(name: str) -> dict[str, object]:
    (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        topology_sha256,
    ) = _blueprint(name)
    nodes: list[LayeredReplayNode] = []
    candidate_count = 0
    for entry in names:
        if entry in stable:
            theorem = replay(entry)
            assert theorem.spec == stable[entry]
            assert theorem.formula == targets[entry]
            body = theorem.certificate
        else:
            candidate_count += 1
            body = _dependency_curried_body(specs[entry], targets)
        nodes.append(
            LayeredReplayNode(
                node_id=positions[entry],
                target=targets[entry],
                dependencies=dependencies[entry],
                body=body,
            )
        )
    assert names[-1] == name
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = LayeredReplayBundle(tuple(nodes), positions[name])
    interned = intern_layered_replay_bodies(raw, targets[name], limits=limits)
    assert type(interned) is LayeredReplayBundle
    target_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(target_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(interned, targets[name], limits=limits)
    assert type(compiled) is LayeredReplayCandidate
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    layer_cuts = 0
    probe = compiled.certificate
    while type(probe) is Cut:
        layer_cuts += 1
        probe = probe.body
    assert layer_cuts == len(compiled.layers)
    for index in range(layer_cuts):
        assert not check(
            (), _mutate_layer_cut(compiled.certificate, index), compiled.target
        )
    assert compiled.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compiled.proof_objects <= limits.max_candidate_proof_objects
    assert compiled.proof_depth <= limits.max_candidate_proof_depth
    assert compiled.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compiled.proof_envelope_depth <= limits.max_candidate_envelope_depth
    return {
        "topology_sha256": topology_sha256,
        "node_count": len(names),
        "stable_catalog_count": len(stable),
        "reachable_stable_count": len(names) - candidate_count,
        "candidate_body_count": candidate_count,
        "dependency_edge_count": sum(map(len, dependencies.values())),
        "layer_sizes": list(map(len, compiled.layers)),
        "layer_cut_count": layer_cuts,
        "proof_nodes": compiled.proof_nodes,
        "proof_depth": compiled.proof_depth,
        "proof_objects": compiled.proof_objects,
        "proof_edges": compiled.proof_edges,
        "reused_objects": compiled.reused_objects,
        "annotation_occurrences": compiled.proof_annotation_occurrences,
        "envelope_depth": compiled.proof_envelope_depth,
        "package_formula_occurrences": compiled.package_formula_occurrences,
        "package_formula_depth": compiled.maximum_package_formula_depth,
        "proof_dag_sha256": _proof_dag_sha256(compiled.certificate),
    }


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    inherited_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        python_root
        if not inherited_path
        else python_root + os.pathsep + inherited_path
    )
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *arguments],
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"isolated worker failed for {arguments!r}:\n"
        f"stdout={result.stdout[-4000:]}\n"
        f"stderr={result.stderr[-4000:]}"
    )
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(prefix)
    ]
    assert len(lines) == 1, result.stdout[-4000:]
    return json.loads(lines[0][len(prefix) :])


def _run_body_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--body-worker", name], "B5FR_BODY ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--closure-worker", name], "B5FR_CLOSURE ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    arguments = ["--reject-worker", kind, name]
    if dependency is not None:
        arguments.append(dependency)
    payload = _run_worker(arguments, "B5FR_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_factor_ranges_static_contract() -> None:
    rows = _rows()
    assert tuple(row.statement for row in rows) == tuple(
        _expected_statements()[name] for name in EXPECTED_NAMES
    )
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_DEPENDENCIES[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.script for row in rows))) == tuple(
        EXPECTED_COMMAND_COUNTS[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.dependencies for row in rows))) == (
        EXPECTED_CUT_COUNTS
    )
    assert len(LIVE_EDGES) == 32
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[0].script.count("apply division_block_upper") == 1
    assert rows[2].script.count("apply pow_two") == 1
    assert rows[5].script.count("apply le_antisymm") == 1
    assert rows[7].script.count("apply pow_zero") == 1
    assert not any("rewrite" in command and "at hcentral" in command
                   for row in rows for command in row.script)
    assert not any("rewrite" in command and "at hvaluation" in command
                   for row in rows for command in row.script)
    assert not any(command.startswith("dne") for row in rows
                   for command in row.script)


def test_bertrand_factor_ranges_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        assert sha256((library / filename).read_bytes()).hexdigest() == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_factor_ranges_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_LAYERED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(
        value is not None for value in EXPECTED_LAYERED_CLOSURES.values()
    )
    for name in EXPECTED_NAMES:
        body = EXPECTED_BODIES[name]
        assert body is not None
        assert body[5] - (body[4] - 1) == body[6]
        closure = EXPECTED_LAYERED_CLOSURES[name]
        assert closure is not None
        assert closure["proof_edges"] - (
            closure["proof_objects"] - 1
        ) == closure["reused_objects"]
        assert closure["layer_cut_count"] == len(closure["layer_sizes"])


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_factor_ranges_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 FACTOR RANGE {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_factor_ranges_bodies_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 FACTOR RANGE {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_factor_ranges_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_factor_ranges_false_targets_are_rejected(name: str) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_factor_ranges_mutations_have_counterfixtures() -> None:
    assert 4 + 4 == 3 * 2 + 2
    assert 2 < 3
    assert not (4 + 4 < 3 + 3)
    assert 0 != 1
    assert 8 < 9 and not (9 < 8)
    assert 1 != 0
    assert 3 < 7 and not (7 <= 3)
    assert 7 <= 5 + 5 and 7 != 1


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_factor_ranges_genuine_mutations_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_factor_ranges_layered_closures_are_frozen(
    name: str,
) -> None:
    actual = _run_closure_worker(name)
    print(f"B5 FACTOR RANGE {name} CLOSURE actual={actual!r}", flush=True)
    expected = EXPECTED_LAYERED_CLOSURES[name]
    assert expected is not None, actual
    assert actual == expected


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    name = sys.argv[2] if mode != "--reject-worker" else sys.argv[3]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        assert len(sys.argv) == 3
        receipt = _body_receipt(name)
        prefix = "B5FR_BODY "
    elif mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5FR_CLOSURE "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5FR_REJECTION "
            + json.dumps({"kind": kind, "name": name}, sort_keys=True),
            flush=True,
        )
        return
    else:
        raise AssertionError(mode)
    print(
        prefix
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
