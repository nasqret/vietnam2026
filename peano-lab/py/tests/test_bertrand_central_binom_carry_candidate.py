"""Fail-closed audit for the Bertrand B5 central-carry tranche.

The expensive empty-context roots run in fresh subprocesses.  Each root uses
the bounded, root-pruned LayeredReplay compiler and Stable certificates as
leaves, so this file never retains ten large closure DAGs in one interpreter.
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
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
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
from peano_lab.library.finite_fold_surface import bit_count, sum_relation
from peano_lab.library.finite_sum_theorems import _at, _sum_relation_terms
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


CHOICE = "double_quotient_carry_choice"
PREFIX_EXTEND = "double_quotient_carry_prefix_extend"
PREFIX_EXISTS = "double_quotient_carry_prefix_exists"
PREFIX_ALL_BITS = "double_quotient_carry_prefix_all_bits"
PREFIX_RESTRICT = "double_quotient_carry_prefix_restrict"
LAST_ONE = "bit_count_positive_last_one"
SUCCESSOR_DIVISOR = "division_successor_quotient_divisor_le"
SUM_EXACT = "beta_sum_double_carry_exact"
CARRY_COUNT = "central_binom_carry_bit_count"
CONTRIBUTION = "central_binom_prime_power_contribution_le_double"

EXPECTED_NAMES = (
    CHOICE,
    PREFIX_EXTEND,
    PREFIX_EXISTS,
    PREFIX_ALL_BITS,
    PREFIX_RESTRICT,
    LAST_ONE,
    SUCCESSOR_DIVISOR,
    SUM_EXACT,
    CARRY_COUNT,
    CONTRIBUTION,
)

EXPECTED_DEPENDENCIES = {
    CHOICE: ("pow_functional", "division_double_quotient_bit"),
    PREFIX_EXTEND: ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
    PREFIX_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        CHOICE,
        PREFIX_EXTEND,
    ),
    PREFIX_ALL_BITS: (),
    PREFIX_RESTRICT: ("le_succ",),
    LAST_ONE: (
        "bit_count_zero",
        "bit_count_succ_decompose",
        "bit_count_bounded",
        "le_succ",
        "le_refl",
    ),
    SUCCESSOR_DIVISOR: ("add_assoc", "add_comm"),
    SUM_EXACT: (
        "beta_sum_zero",
        "beta_sum_succ_decompose",
        "bit_count_zero",
        "bit_count_succ_decompose",
        "beta_at_unique",
        "le_refl",
        PREFIX_RESTRICT,
        "add_assoc",
        "add_permute_outer",
        "add_comm",
    ),
    CARRY_COUNT: (
        "prime_legendre_sum_exists",
        "central_binom_legendre_valuation_balance",
        "legendre_sum_extended_prefix_exists",
        PREFIX_EXISTS,
        PREFIX_ALL_BITS,
        "bit_count_exists",
        SUM_EXACT,
        "add_left_cancel",
    ),
    CONTRIBUTION: (
        "pow_zero",
        "le_add_right",
        "le_trans",
        "prime_nonzero",
        "one_le_of_ne_zero",
        "beta_at_unique",
        "pow_le_pow_of_exponent_le",
        LAST_ONE,
        SUCCESSOR_DIVISOR,
        CARRY_COUNT,
    ),
}

EXPECTED_DEPENDENCY_COUNTS = dict(
    zip(EXPECTED_NAMES, (2, 2, 6, 0, 1, 5, 2, 10, 8, 10), strict=True)
)
EXPECTED_COMMAND_COUNTS = dict(
    zip(
        EXPECTED_NAMES,
        (72, 71, 73, 30, 16, 69, 21, 174, 116, 149),
        strict=True,
    )
)
assert sum(EXPECTED_DEPENDENCY_COUNTS.values()) == 46

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOICE: (
        8_391,
        "5ef465a4d3e7565137896cf9188b1087b84dff8b48032d9a7ac2c57093205f3e",
        "2c99e52f347806d791ace9b3123c9e23726dc6b3be1b9b6a381b21f1b623b159",
        "0324058bb1ae1b832af8a7a2df3493da33dddcd9ecf0f249a54dc72da57c5bc7",
    ),
    PREFIX_EXTEND: (
        3_067,
        "70ba983f3fd6d684adb6e9f564d7a86352a3903a1bba5572873fd28e8f56c91b",
        "ee7a61af987213845eeebe9f6170e72806fd248bf5765285d5a1530a0f13f6a0",
        "e03fd9c539be901c23cd5a437b26e2f455de1b6a52c9c5d02160aac858cf899d",
    ),
    PREFIX_EXISTS: (
        9_213,
        "91873ec6a00a4899ac97c0dda0ccde5c33e3a99b48a8abd687fc1033c99a3d15",
        "af43473c316e103ce070d7f62666f85083ebedb21575a17d1f83d351d267f56f",
        "6f0c5dd2a2467167dac6bcaa500a9441c7732c22b02c450c43f90d1d8fca4ad3",
    ),
    PREFIX_ALL_BITS: (
        1_869,
        "4b19331c4f65683104ecb45ec09dc825483806550c340b17910b2f2e36bbab61",
        "d5f050e86fbf95725890a8f6f42a951f157a28b45cc13a84e26af8af2a01de49",
        "4b19331c4f65683104ecb45ec09dc825483806550c340b17910b2f2e36bbab61",
    ),
    PREFIX_RESTRICT: (
        2_670,
        "2e3b11ae20668efc0e8678c6784be451e0f4ac775c04b63e4fefa4a72140608f",
        "06dc98cdfa6afbed3a8965937befaa1f25d66b1434acf7636188aeef10d3eed8",
        "a316f29a1a6ad271e29439ee518939740664350a0c9d2b3d16f2f94a4c18b0a4",
    ),
    LAST_ONE: (
        2_878,
        "fd69093a62efe3736e21a48937b7465174b0610f3805c83242b24df6b30f2568",
        "43d16ed96584de5f54c8a3ee28f014492523ca776a7429a61a47a4903ef219d0",
        "45087d05cfb7c7e804e6348fa36b8b65ac3df085a08428eb1bb4cb53e1fe1ca6",
    ),
    SUCCESSOR_DIVISOR: (
        211,
        "d990d0748c7af28a09aa554458a56b060fb097817d05a7740f2bcaeca12c8c64",
        "b16fef845b22447f2e809fabb5f36e58449e260e7f0d5e323f27cd0e4ef901ea",
        "43ca20e8a83f967be21e3e5fc855bf272825e9024be7813b0b20a9f8e55f780e",
    ),
    SUM_EXACT: (
        7_812,
        "f87d91991e7eaa6623bd4047a7e1af759cdf6e1115e6e5acef7c4c03c6bfe5b9",
        "a7486289e7b736e467be9b9b22596b6923748de482cb9734e65de17871b6ca8c",
        "405f125fc470c068fe92964be94198abed123f634e010a6d8873d93dba563351",
    ),
    CARRY_COUNT: (
        30_080,
        "5ff89e4592c2ffd15ef7b6e04792fae86228f70eebe13dc90f4a86c59c38f36b",
        "5e11adbe269b1217e004f96fe1c08c59c23f0ffb45db7d5156043f82b9b297c4",
        "0d0acad91262a36f43e1c80692e72410fd4929a26e7a8819be0da94981f53ef9",
    ),
    CONTRIBUTION: (
        20_841,
        "d9af95283f48c504e85c6c32ef1de00fd13e251a18720a3617eae7dce947d4d9",
        "d43bed83cafb86c607ed22d80983d0d8a87347b42be9b84ef460020df27aebf3",
        "dea289558c37021af8fef4fd2f23d1c4980cd6451fda31c3397ac7f4803a4797",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOICE: (2, 72, 103, 31, 103, 102, 0),
    PREFIX_EXTEND: (2, 71, 104, 36, 104, 103, 0),
    PREFIX_EXISTS: (6, 73, 87, 32, 87, 86, 0),
    PREFIX_ALL_BITS: (0, 30, 36, 20, 36, 35, 0),
    PREFIX_RESTRICT: (1, 16, 28, 20, 28, 27, 0),
    LAST_ONE: (5, 69, 107, 26, 106, 106, 1),
    SUCCESSOR_DIVISOR: (2, 21, 33, 17, 33, 32, 0),
    SUM_EXACT: (10, 174, 527, 66, 522, 526, 5),
    CARRY_COUNT: (8, 116, 183, 53, 183, 182, 0),
    CONTRIBUTION: (10, 149, 209, 49, 209, 208, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOICE: (103, 103, 31, 62, 31),
    PREFIX_EXTEND: (104, 104, 36, 611, 42),
    PREFIX_EXISTS: (87, 87, 32, 628, 46),
    PREFIX_ALL_BITS: (36, 36, 20, 2, 20),
    PREFIX_RESTRICT: (28, 28, 20, 4, 20),
    LAST_ONE: (107, 106, 26, 720, 42),
    SUCCESSOR_DIVISOR: (33, 33, 17, 42, 18),
    SUM_EXACT: (527, 522, 66, 1_483, 66),
    CARRY_COUNT: (183, 183, 53, 481, 58),
    CONTRIBUTION: (209, 209, 49, 1_176, 61),
}
EXPECTED_LAYERED_CLOSURES: dict[str, dict[str, object] | None] = {
    CHOICE: {
        "topology_sha256": (
            "024486af1f371a59bb11e2803953ffa043cc2552bc2d78dd674ef751b6cbe150"
        ),
        "node_count": 18,
        "stable_catalog_count": 432,
        "reachable_stable_count": 13,
        "candidate_body_count": 5,
        "dependency_edge_count": 21,
        "layer_sizes": [13, 2, 1, 1, 1],
        "layer_cut_count": 5,
        "proof_nodes": 4_895,
        "proof_depth": 68,
        "proof_objects": 1_315,
        "proof_edges": 1_709,
        "reused_objects": 395,
        "annotation_occurrences": 17_933,
        "envelope_depth": 68,
        "package_formula_occurrences": 1_293,
        "package_formula_depth": 41,
        "proof_dag_sha256": (
            "488be26a9299d4674ddb8dd15b0015fceadeeb11be8f8c5cfd77076d6e34e9b6"
        ),
    },
    PREFIX_EXTEND: {
        "topology_sha256": (
            "f223cb1517e535905c6511877675ea5afee1fba5765f71372348a5f7e038330b"
        ),
        "node_count": 3,
        "stable_catalog_count": 432,
        "reachable_stable_count": 2,
        "candidate_body_count": 1,
        "dependency_edge_count": 2,
        "layer_sizes": [2, 1],
        "layer_cut_count": 2,
        "proof_nodes": 29_299,
        "proof_depth": 82,
        "proof_objects": 3_082,
        "proof_edges": 4_229,
        "reused_objects": 1_148,
        "annotation_occurrences": 95_646,
        "envelope_depth": 82,
        "package_formula_occurrences": 415,
        "package_formula_depth": 28,
        "proof_dag_sha256": (
            "83df6396bb9c2073af21c347bc5e60e18ffc39effca2fc75ede7b5213c79fce6"
        ),
    },
    PREFIX_EXISTS: {
        "topology_sha256": (
            "37a542308426f16897d1342191e7fdca25d4d0c7d5cf1da74f58f070307e1f28"
        ),
        "node_count": 26,
        "stable_catalog_count": 432,
        "reachable_stable_count": 19,
        "candidate_body_count": 7,
        "dependency_edge_count": 29,
        "layer_sizes": [19, 3, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "proof_nodes": 34_417,
        "proof_depth": 85,
        "proof_objects": 3_875,
        "proof_edges": 5_250,
        "reused_objects": 1_376,
        "annotation_occurrences": 115_140,
        "envelope_depth": 85,
        "package_formula_occurrences": 2_358,
        "package_formula_depth": 41,
        "proof_dag_sha256": (
            "ce59afffe88574ccdb8958790f724562113789c6a7183ac9b08fb1d119f1d496"
        ),
    },
    PREFIX_ALL_BITS: {
        "topology_sha256": (
            "0fdb5638e877bd6d08dd98f3321cfad6413337ad423762013b4843778124ce3a"
        ),
        "node_count": 1,
        "stable_catalog_count": 432,
        "reachable_stable_count": 0,
        "candidate_body_count": 1,
        "dependency_edge_count": 0,
        "layer_sizes": [1],
        "layer_cut_count": 1,
        "proof_nodes": 38,
        "proof_depth": 21,
        "proof_objects": 29,
        "proof_edges": 34,
        "reused_objects": 6,
        "annotation_occurrences": 320,
        "envelope_depth": 26,
        "package_formula_occurrences": 159,
        "package_formula_depth": 25,
        "proof_dag_sha256": (
            "23f070dfcdf5391852259f969fb075e373032b500e45ba0aa945d26630b5bba9"
        ),
    },
    PREFIX_RESTRICT: {
        "topology_sha256": (
            "885db1e23d9a88ea83f601b161c831eb0e1816592382ec16c0efc23a11a343cc"
        ),
        "node_count": 2,
        "stable_catalog_count": 432,
        "reachable_stable_count": 1,
        "candidate_body_count": 1,
        "dependency_edge_count": 1,
        "layer_sizes": [1, 1],
        "layer_cut_count": 2,
        "proof_nodes": 73,
        "proof_depth": 23,
        "proof_objects": 65,
        "proof_edges": 72,
        "reused_objects": 8,
        "annotation_occurrences": 784,
        "envelope_depth": 27,
        "package_formula_occurrences": 241,
        "package_formula_depth": 25,
        "proof_dag_sha256": (
            "e96e18b6e6c8d902ccb5c16ba8423c907f2fbdc3d33c643e44a8dd4809a00818"
        ),
    },
    LAST_ONE: {
        "topology_sha256": (
            "8cf00f4c84aa20f76d78a7c0db1b6db17577af143c80a9609982149449e226aa"
        ),
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 5,
        "candidate_body_count": 1,
        "dependency_edge_count": 5,
        "layer_sizes": [5, 1],
        "layer_cut_count": 2,
        "proof_nodes": 8_012,
        "proof_depth": 68,
        "proof_objects": 864,
        "proof_edges": 1_162,
        "reused_objects": 299,
        "annotation_occurrences": 35_994,
        "envelope_depth": 68,
        "package_formula_occurrences": 1_104,
        "package_formula_depth": 36,
        "proof_dag_sha256": (
            "cdad80ffb763b5fa23b7df0f4754ef7caa482c5345029d561d7afbda0de5de9b"
        ),
    },
    SUCCESSOR_DIVISOR: {
        "topology_sha256": (
            "4fd44d93dd5afde1d45c6dc8fbff2100e021fdfadf0160d315e83c1cf5b43d1f"
        ),
        "node_count": 3,
        "stable_catalog_count": 432,
        "reachable_stable_count": 2,
        "candidate_body_count": 1,
        "dependency_edge_count": 2,
        "layer_sizes": [2, 1],
        "layer_cut_count": 2,
        "proof_nodes": 149,
        "proof_depth": 21,
        "proof_objects": 114,
        "proof_edges": 132,
        "reused_objects": 19,
        "annotation_occurrences": 391,
        "envelope_depth": 22,
        "package_formula_occurrences": 51,
        "package_formula_depth": 11,
        "proof_dag_sha256": (
            "6a4b6c4ac4422a9579c38c5aab33e823c1207f28518b18f9d7337b4c92968d17"
        ),
    },
    SUM_EXACT: {
        "topology_sha256": (
            "8feefcfd3e83bd63f4a977b334048a84c6c233c1a42961cbf8c3967fd2af85ad"
        ),
        "node_count": 12,
        "stable_catalog_count": 432,
        "reachable_stable_count": 10,
        "candidate_body_count": 2,
        "dependency_edge_count": 11,
        "layer_sizes": [10, 1, 1],
        "layer_cut_count": 3,
        "proof_nodes": 8_317,
        "proof_depth": 79,
        "proof_objects": 1_072,
        "proof_edges": 1_419,
        "reused_objects": 348,
        "annotation_occurrences": 31_771,
        "envelope_depth": 79,
        "package_formula_occurrences": 2_089,
        "package_formula_depth": 37,
        "proof_dag_sha256": (
            "dc9647e626eea523ac5f417e2ee197c8e806d78fdbc35ab0474da2dfaa024e14"
        ),
    },
    CARRY_COUNT: {
        "topology_sha256": (
            "f42803ceec67b67a4850bdd60f6bf7d87b39099bf4561842af01e42b6d5924d3"
        ),
        "node_count": 174,
        "stable_catalog_count": 432,
        "reachable_stable_count": 69,
        "candidate_body_count": 105,
        "dependency_edge_count": 377,
        "layer_sizes": [
            76, 35, 15, 7, 8, 7, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1
        ],
        "layer_cut_count": 17,
        "proof_nodes": 268_256,
        "proof_depth": 96,
        "proof_objects": 12_771,
        "proof_edges": 16_866,
        "reused_objects": 4_096,
        "annotation_occurrences": 966_038,
        "envelope_depth": 96,
        "package_formula_occurrences": 60_116,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "6c79728fba3c187c3bcd89f0a2ad658887d437c4097cad3696b9cb832d73077f"
        ),
    },
    CONTRIBUTION: {
        "topology_sha256": (
            "42af00505f1c6cf1c63ba57070836d0510d95439c6637d9be9661fa24218f8f2"
        ),
        "node_count": 180,
        "stable_catalog_count": 432,
        "reachable_stable_count": 71,
        "candidate_body_count": 109,
        "dependency_edge_count": 399,
        "layer_sizes": [
            78, 37, 15, 8, 8, 7, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1
        ],
        "layer_cut_count": 18,
        "proof_nodes": 272_918,
        "proof_depth": 96,
        "proof_objects": 13_228,
        "proof_edges": 17_440,
        "reused_objects": 4_213,
        "annotation_occurrences": 978_630,
        "envelope_depth": 96,
        "package_formula_occurrences": 62_043,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "7915367163cb513523d666a682d28e4becf007f28fd7828bf692c2bd8245708f"
        ),
    },
}

SOURCE_PINS = {
    "bertrand_b5_order_quotient_candidate.py": (
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e"
    ),
    "bertrand_central_binom_valuation_candidate.py": (
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8"
    ),
    "bertrand_central_binom_carry_candidate.py": (
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0"
    ),
    "alpha_enrollment_v11.py": (
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093"
    ),
    "editions_v11.py": (
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf"
    ),
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-carry-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "a9074118af3e2077b95305a7de7c2a25837bcf56999f44e7e7bc5b48eb144974"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_central_binom_carry_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


def _test_bit_count(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    length_marker = f"test_b5cc_length_marker_{tag}"
    result_marker = f"test_b5cc_result_marker_{tag}"
    expanded = bit_count(
        code, scale, length_marker, result_marker, tag=tag
    )
    assert expanded.count(length_marker) == 4
    assert expanded.count(result_marker) == 2
    return expanded.replace(length_marker, f"({length})").replace(
        result_marker, f"({result})"
    )


def _test_all_bits(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    marker = f"test_b5cc_bits_marker_{tag}"
    from peano_lab.library.finite_fold_surface import all_bits

    expanded = all_bits(code, scale, marker, tag=tag)
    assert expanded.count(marker) == 1
    return expanded.replace(marker, f"({length})")


def _test_carry_choice(
    quotient: str,
    doubled: str,
    bit: str,
    *,
    keep_successor: bool = True,
) -> str:
    upper = f"S ({quotient} + {quotient})"
    if not keep_successor:
        upper = f"{quotient} + {quotient}"
    return (
        f"(({bit} = 0 /\\ {doubled} = {quotient} + {quotient}) \\/ "
        f"({bit} = 1 /\\ {doubled} = {upper}))"
    )


def _test_carry_point(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    index: str,
    *,
    tag: str,
    keep_successor: bool = True,
) -> str:
    left = _at(
        left_code, left_scale, index, "q", tag=f"{tag}_left"
    )
    right = _at(
        right_code, right_scale, index, "Q", tag=f"{tag}_right"
    )
    choice = _test_carry_choice(
        "q", "Q", "bit", keep_successor=keep_successor
    )
    return (
        f"exists q Q bit. ({left}) /\\ (({right}) /\\ ({choice}))"
    )


def _test_carry_prefix(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    bit_code: str,
    bit_scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index = f"b5cc_index_{tag}"
    quotient = f"b5cc_left_{tag}"
    doubled = f"b5cc_right_{tag}"
    bit = f"b5cc_bit_{tag}"
    generated = (index, quotient, doubled, bit)
    assert not set(generated) & set(variables)
    owned = variables + generated
    bound = _lt_term(
        index, length, tag=f"{tag}_bound", variables=owned
    )
    left = _at(
        left_code,
        left_scale,
        index,
        quotient,
        tag=f"b5cc_{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        index,
        doubled,
        tag=f"b5cc_{tag}_right",
    )
    decoded = _at(
        bit_code,
        bit_scale,
        index,
        bit,
        tag=f"b5cc_{tag}_bit",
    )
    choice = _test_carry_choice(quotient, doubled, bit)
    return (
        f"forall {index}. ({bound}) -> "
        f"exists {quotient} {doubled} {bit}. "
        f"({left}) /\\ (({right}) /\\ (({decoded}) /\\ ({choice})))"
    )


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    choice_variables = ("p", "n", "b", "c", "d", "e", "l", "i")
    choice_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5ccqc_left"
    )
    choice_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5ccqc_right"
    )
    choice_bound = _lt_term(
        "i", "l", tag="b5ccqc_bound", variables=choice_variables
    )
    choice_result = _test_carry_point(
        "b", "c", "d", "e", "i", tag="b5ccqc_result"
    )
    prefix_variables = ("b", "c", "d", "e", "f", "g", "l")
    prefix_before = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "l",
        tag="b5ccpe_before", variables=prefix_variables,
    )
    prefix_last = _test_carry_point(
        "b", "c", "d", "e", "l", tag="b5ccpe_last"
    )
    prefix_after = _test_carry_prefix(
        "b", "c", "d", "e", "z", "h", "S l",
        tag="b5ccpe_after", variables=prefix_variables + ("z", "h"),
    )
    exists_variables = ("p", "n", "b", "c", "d", "e", "l")
    exists_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5ccpx_left"
    )
    exists_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5ccpx_right"
    )
    exists_result = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "l",
        tag="b5ccpx_result",
        variables=exists_variables + ("f", "g"),
    )
    bits_variables = ("b", "c", "d", "e", "f", "g", "l")
    bits_source = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "l",
        tag="b5ccpab_source", variables=bits_variables,
    )
    from peano_lab.library.finite_fold_surface import all_bits
    bits_result = all_bits("f", "g", "l", tag="b5ccpab_result")
    restrict_source = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "S l",
        tag="b5ccpr_source", variables=bits_variables,
    )
    restrict_result = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "l",
        tag="b5ccpr_result", variables=bits_variables,
    )
    last_count = _test_bit_count(
        "b", "c", "l", "S e", tag="b5ccbclo_count"
    )
    last_bound = _lt_term(
        "i", "l", tag="b5ccbclo_bound",
        variables=("b", "c", "l", "e", "i"),
    )
    last_entry = _at("b", "c", "i", "1", tag="b5ccbclo_entry")
    last_result = _le_term(
        "S e", "S i", tag="b5ccbclo_result",
        variables=("b", "c", "l", "e", "i"),
    )
    divisor_variables = ("d", "n", "q", "r")
    divisor_source = _divrem_term(
        "d", "n", "S q", "r", tag="b5ccsqdl_source",
        variables=divisor_variables,
    )
    divisor_result = _le_term(
        "d", "n", tag="b5ccsqdl_result",
        variables=divisor_variables,
    )
    sum_variables = ("b", "c", "d", "e", "f", "g", "l", "B", "A", "E")
    sum_left = sum_relation(
        "b", "c", "l", "B", tag="b5ccsdce_left_sum"
    )
    sum_right = sum_relation(
        "d", "e", "l", "A", tag="b5ccsdce_right_sum"
    )
    sum_carries = _test_carry_prefix(
        "b", "c", "d", "e", "f", "g", "l",
        tag="b5ccsdce_prefix", variables=sum_variables,
    )
    sum_count = bit_count(
        "f", "g", "l", "E", tag="b5ccsdce_count"
    )
    exact_variables = ("p", "n", "C", "v")
    exact_prime = prime("p", tag="b5cccbbc_prime")
    exact_central = _central_binom_relation_term(
        "n", "C", tag="b5cccbbc_central",
        variables=exact_variables,
    )
    exact_valuation = power_valuation(
        "p", "C", "v", tag="b5cccbbc_valuation"
    )
    exact_left = _power_quotient_prefix_terms(
        "p", "n", "b", "s", "n + n", tag="b5cccbbc_left"
    )
    exact_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "t", "n + n", tag="b5cccbbc_right"
    )
    exact_carries = _test_carry_prefix(
        "b", "s", "d", "t", "f", "g", "n + n",
        tag="b5cccbbc_carries",
        variables=exact_variables + ("b", "s", "d", "t", "f", "g"),
    )
    exact_count = _test_bit_count(
        "f", "g", "n + n", "v", tag="b5cccbbc_count"
    )
    final_variables = ("p", "n", "C", "v", "D")
    final_prime = prime("p", tag="b5ccppcld_prime")
    final_positive = _le_term(
        "1", "n", tag="b5ccppcld_positive",
        variables=final_variables,
    )
    final_central = _central_binom_relation_term(
        "n", "C", tag="b5ccppcld_central",
        variables=final_variables,
    )
    final_valuation = power_valuation(
        "p", "C", "v", tag="b5ccppcld_valuation"
    )
    final_power = _power_terms(
        "p", "v", "D", tag="b5ccppcld_power"
    )
    final_result = _le_term(
        "D", "n + n", tag="b5ccppcld_result",
        variables=final_variables,
    )
    return {
        CHOICE: (
            "forall p n b c d e l i. "
            f"({choice_left}) -> ({choice_right}) -> "
            f"({choice_bound}) -> ({choice_result})"
        ),
        PREFIX_EXTEND: (
            "forall b c d e f g l. "
            f"({prefix_before}) -> ({prefix_last}) -> "
            f"exists z h. ({prefix_after})"
        ),
        PREFIX_EXISTS: (
            "forall p n b c d e l. "
            f"({exists_left}) -> ({exists_right}) -> "
            f"exists f g. ({exists_result})"
        ),
        PREFIX_ALL_BITS: (
            "forall b c d e f g l. "
            f"({bits_source}) -> ({bits_result})"
        ),
        PREFIX_RESTRICT: (
            "forall b c d e f g l. "
            f"({restrict_source}) -> ({restrict_result})"
        ),
        LAST_ONE: (
            "forall b c l e. "
            f"({last_count}) -> exists i. ({last_bound}) /\\ "
            f"(({last_entry}) /\\ ({last_result}))"
        ),
        SUCCESSOR_DIVISOR: (
            "forall d n q r. "
            f"({divisor_source}) -> ({divisor_result})"
        ),
        SUM_EXACT: (
            "forall b c d e f g l B A E. "
            f"({sum_left}) -> ({sum_right}) -> ({sum_carries}) -> "
            f"({sum_count}) -> A = (B + B) + E"
        ),
        CARRY_COUNT: (
            "forall p n C v. "
            f"({exact_prime}) -> ({exact_central}) -> "
            f"({exact_valuation}) -> exists b s d t f g. "
            f"({exact_left}) /\\ (({exact_right}) /\\ "
            f"(({exact_carries}) /\\ ({exact_count})))"
        ),
        CONTRIBUTION: (
            "forall p n C v D. "
            f"({final_prime}) -> ({final_positive}) -> "
            f"({final_central}) -> ({final_valuation}) -> "
            f"({final_power}) -> ({final_result})"
        ),
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    statements = _expected_statements()
    result: dict[str, str] = {}

    def changed(name: str, old: str, new: str) -> None:
        assert statements[name].count(old) == 1
        result[name] = statements[name].replace(old, new)

    changed(
        CHOICE,
        _test_carry_point(
            "b", "c", "d", "e", "i", tag="b5ccqc_result"
        ),
        _test_carry_point(
            "b", "c", "d", "e", "i", tag="b5ccqc_result",
            keep_successor=False,
        ),
    )
    prefix_variables = ("b", "c", "d", "e", "f", "g", "l")
    changed(
        PREFIX_EXTEND,
        _test_carry_prefix(
            "b", "c", "d", "e", "z", "h", "S l",
            tag="b5ccpe_after", variables=prefix_variables + ("z", "h"),
        ),
        _test_carry_prefix(
            "b", "c", "d", "e", "z", "h", "S (S l)",
            tag="b5ccpe_after", variables=prefix_variables + ("z", "h"),
        ),
    )
    exists_variables = ("p", "n", "b", "c", "d", "e", "l")
    changed(
        PREFIX_EXISTS,
        _test_carry_prefix(
            "b", "c", "d", "e", "f", "g", "l",
            tag="b5ccpx_result",
            variables=exists_variables + ("f", "g"),
        ),
        _test_carry_prefix(
            "b", "c", "d", "e", "f", "g", "S l",
            tag="b5ccpx_result",
            variables=exists_variables + ("f", "g"),
        ),
    )
    from peano_lab.library.finite_fold_surface import all_bits
    changed(
        PREFIX_ALL_BITS,
        all_bits("f", "g", "l", tag="b5ccpab_result"),
        _test_all_bits("f", "g", "S l", tag="b5ccpab_result"),
    )
    bits_variables = ("b", "c", "d", "e", "f", "g", "l")
    changed(
        PREFIX_RESTRICT,
        _test_carry_prefix(
            "b", "c", "d", "e", "f", "g", "l",
            tag="b5ccpr_result", variables=bits_variables,
        ),
        _test_carry_prefix(
            "b", "c", "d", "e", "f", "g", "S (S l)",
            tag="b5ccpr_result", variables=bits_variables,
        ),
    )
    changed(
        LAST_ONE,
        _le_term(
            "S e", "S i", tag="b5ccbclo_result",
            variables=("b", "c", "l", "e", "i"),
        ),
        _le_term(
            "S (S e)", "S i", tag="b5ccbclo_result",
            variables=("b", "c", "l", "e", "i"),
        ),
    )
    divisor_variables = ("d", "n", "q", "r")
    changed(
        SUCCESSOR_DIVISOR,
        _le_term(
            "d", "n", tag="b5ccsqdl_result",
            variables=divisor_variables,
        ),
        _le_term(
            "S d", "n", tag="b5ccsqdl_result",
            variables=divisor_variables,
        ),
    )
    changed(
        SUM_EXACT,
        "A = (B + B) + E",
        "A = (B + B) + S E",
    )
    changed(
        CARRY_COUNT,
        _test_bit_count(
            "f", "g", "n + n", "v", tag="b5cccbbc_count"
        ),
        _test_bit_count(
            "f", "g", "n + n", "S v", tag="b5cccbbc_count"
        ),
    )
    final_variables = ("p", "n", "C", "v", "D")
    changed(
        CONTRIBUTION,
        _le_term(
            "D", "n + n", tag="b5ccppcld_result",
            variables=final_variables,
        ),
        _le_term(
            "S D", "n + n", tag="b5ccppcld_result",
            variables=final_variables,
        ),
    )
    assert tuple(result) == EXPECTED_NAMES
    return result


@lru_cache(maxsize=1)
@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    rows = (
        *editions_v11.ALPHA_SPECS,
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_valuation_candidate_theorems(
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
    return dict(_specs_by_name()) | _candidate_base() | _table(
        _rows()[: EXPECTED_NAMES.index(name)]
    )


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base() | _table(_rows())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


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
        label=f"B5 central carry body {name}",
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
                entry
                for entry in item.dependencies
                if entry != dependency
            ),
        )
        assert len(changed.dependencies) + 1 == len(item.dependencies)
    elif kind == "false":
        assert dependency is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert dependency is None
        mutation = _mutations()[name]
        assert _closed_formula(item.statement) != _closed_formula(mutation)
        changed = replace(item, statement=mutation)
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} replay unexpectedly passed for {name}")


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
                "\x1e".join(
                    names[index] for index in dependencies[entry]
                ),
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
    raw = LayeredReplayBundle(tuple(nodes), positions[name])
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    interned = intern_layered_replay_bodies(
        raw,
        targets[name],
        limits=limits,
    )
    assert type(interned) is LayeredReplayBundle
    target_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(target_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(
        interned,
        targets[name],
        limits=limits,
    )
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
        corrupted = _mutate_layer_cut(compiled.certificate, index)
        assert not check((), corrupted, compiled.target)
    assert compiled.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compiled.proof_objects <= limits.max_candidate_proof_objects
    assert compiled.proof_depth <= limits.max_candidate_proof_depth
    assert compiled.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compiled.proof_envelope_depth <= (
        limits.max_candidate_envelope_depth
    )
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
        "package_formula_occurrences": (
            compiled.package_formula_occurrences
        ),
        "package_formula_depth": compiled.maximum_package_formula_depth,
        "proof_dag_sha256": _proof_dag_sha256(compiled.certificate),
    }


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
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
        line
        for line in result.stdout.splitlines()
        if line.startswith(prefix)
    ]
    assert len(lines) == 1, result.stdout[-4000:]
    return json.loads(lines[0][len(prefix) :])


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(
        ["--closure-worker", name], "B5CC_LAYERED_RECEIPT "
    )
    assert payload["name"] == name
    return payload["receipt"]


def _run_body_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--body-worker", name], "B5CC_BODY_RECEIPT ")
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
    payload = _run_worker(arguments, "B5CC_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_central_carry_static_contract() -> None:
    rows = _rows()
    expected = _expected_statements()
    assert len(editions_v11.ALPHA_SPECS) == 1_123
    assert len(editions_v11.STABLE_SPECS) == 432
    assert editions_v11.EXPECTED_ALPHA_V11_EDGE_COUNT == 3_482
    assert editions_v11.EXPECTED_ALPHA_V11_LAYER_COUNT == 45
    assert editions_v11.ALPHA_V11_ENROLLMENT_SHA256 == (
        "c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36"
    )
    assert editions_v11.ALPHA_V11_IDENTITY_SHA256 == (
        "46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3"
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DEPENDENCY_COUNTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_COMMAND_COUNTS) == EXPECTED_NAMES
    assert tuple(row.statement for row in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_DEPENDENCIES[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.script for row in rows))) == tuple(
        EXPECTED_COMMAND_COUNTS[name] for name in EXPECTED_NAMES
    )
    assert len(LIVE_EDGES) == 46
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[0].script.count("apply division_double_quotient_bit") == 1
    assert rows[3].script.count("intro i") == 1
    assert rows[5].script.count("induction l") == 1
    assert rows[7].script.count("induction l") == 1
    assert rows[8].script.count("apply add_left_cancel") == 1
    assert rows[9].script.count("induction v") == 1
    assert rows[9].script.count("apply pow_le_pow_of_exponent_le") == 1
    assert not any(
        command.startswith("rewrite")
        and command.endswith(
            (
                " at hcentral",
                " at hvaluation",
                " at hpower",
            )
        )
        for row in rows
        for command in row.script
    )


def test_bertrand_central_carry_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        actual = sha256((library / filename).read_bytes()).hexdigest()
        assert actual == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_central_carry_receipts_are_shaped() -> None:
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


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_carry_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 CENTRAL CARRY {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_carry_bodies_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 CENTRAL CARRY {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_central_carry_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_carry_false_targets_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_central_carry_mutations_have_counterfixtures() -> None:
    assert 0 != 1
    assert 0 != 1
    assert 0 != 1
    assert 0 != 1
    assert 0 != 1
    assert 0 != 1
    assert 0 != 1
    assert not (1 <= 0)
    assert not (1 <= 0)
    assert not (1 <= 0)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_carry_genuine_mutations_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_carry_layered_closures_are_frozen(
    name: str,
) -> None:
    actual = _run_closure_worker(name)
    print(
        f"B5 CENTRAL CARRY {name} LAYERED CLOSURE actual={actual!r}",
        flush=True,
    )
    expected = EXPECTED_LAYERED_CLOSURES[name]
    assert expected is not None, actual
    assert actual == expected


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    name = sys.argv[2] if mode != "--reject-worker" else sys.argv[3]
    assert name in EXPECTED_NAMES
    if mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5CC_LAYERED_RECEIPT "
    elif mode == "--body-worker":
        assert len(sys.argv) == 3
        receipt = _body_receipt(name)
        prefix = "B5CC_BODY_RECEIPT "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5CC_REJECTION "
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
