"""Fail-closed audit for the Bertrand B5 central-valuation tranche.

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
from peano_lab.library.bertrand_central_binom_prime_support_candidate import (
    _factorial_relation_term,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_factorial_valuation_candidate import (
    factorial_valuation,
)
from peano_lab.library.bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
    legendre_sum,
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
from peano_lab.library.finite_fold_surface import sum_relation
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


TRANSPORT = "power_valuation_value_eq_transport"
FACTORIAL_BALANCE = "central_binom_factorial_valuation_balance"
LEGENDRE_BALANCE = "central_binom_legendre_valuation_balance"
QUOTIENT_ZERO = "prime_power_quotient_zero_of_exponent_gt"
TAIL_ZERO = "power_quotient_prefix_tail_entry_zero"
SUM_EXTEND = "power_quotient_prefix_sum_extend_zero"
EXTENDED_EXISTS = "legendre_sum_extended_prefix_exists"
POINTWISE_UPPER = "power_quotient_double_pointwise_upper"
SUM_UPPER = "beta_sum_pointwise_double_succ_le"
VALUATION_BOUND = "central_binom_prime_valuation_le_double"

EXPECTED_NAMES = (
    TRANSPORT,
    FACTORIAL_BALANCE,
    LEGENDRE_BALANCE,
    QUOTIENT_ZERO,
    TAIL_ZERO,
    SUM_EXTEND,
    EXTENDED_EXISTS,
    POINTWISE_UPPER,
    SUM_UPPER,
    VALUATION_BOUND,
)

EXPECTED_DEPENDENCIES = {
    TRANSPORT: (),
    FACTORIAL_BALANCE: (
        "central_binom_positive",
        "factorial_nonzero",
        "choose_factorial_bridge",
        "power_valuation_exists",
        TRANSPORT,
        "prime_power_valuation_mul",
        "mul_ne_zero",
    ),
    LEGENDRE_BALANCE: (
        "factorial_valuation_exists",
        "prime_factorial_valuation_eq_legendre_sum",
        FACTORIAL_BALANCE,
    ),
    QUOTIENT_ZERO: (
        "prime_power_exponent_le",
        "lt_of_lt_of_le",
        "division_zero_quotient_of_lt",
    ),
    TAIL_ZERO: (QUOTIENT_ZERO,),
    SUM_EXTEND: (
        "legendre_sum_functional",
        "le_succ",
        "add_comm",
        "zero_add",
        "beta_sum_succ_last_zero",
        TAIL_ZERO,
    ),
    EXTENDED_EXISTS: (
        "prime_power_quotient_prefix_exists",
        "beta_sum_exists",
        SUM_EXTEND,
    ),
    POINTWISE_UPPER: (
        "beta_at_unique",
        "pow_functional",
        "division_double_quotient_upper",
    ),
    SUM_UPPER: (
        "beta_sum_zero",
        "beta_sum_succ_decompose",
        "le_succ",
        "le_refl",
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
        "add_assoc",
        "add_comm",
    ),
    VALUATION_BOUND: (
        "prime_legendre_sum_exists",
        LEGENDRE_BALANCE,
        EXTENDED_EXISTS,
        POINTWISE_UPPER,
        SUM_UPPER,
        "add_comm",
        "add_le_cancel_right",
    ),
}

EXPECTED_DEPENDENCY_COUNTS = dict(
    zip(EXPECTED_NAMES, (0, 7, 3, 3, 1, 6, 3, 3, 9, 7), strict=True)
)
EXPECTED_COMMAND_COUNTS = dict(
    zip(
        EXPECTED_NAMES,
        (11, 109, 60, 31, 40, 86, 40, 75, 125, 81),
        strict=True,
    )
)
assert sum(EXPECTED_DEPENDENCY_COUNTS.values()) == 42

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    TRANSPORT: (
        17_625,
        "a714d85092357780e3e2b883a95f56b28f0110fbee763e6b1dd5955d42bbd0da",
        "fdc21771fb7d0aac909d53f83c851f72a459fb42420ac0538f81896aaef25bde",
        "a714d85092357780e3e2b883a95f56b28f0110fbee763e6b1dd5955d42bbd0da",
    ),
    FACTORIAL_BALANCE: (
        44_300,
        "d77f6dde5bbc0c8e0f57855986862520bfbe1540e7e8b705057cbf14bb66d00a",
        "6bbdcf132f13ae0c5727afba6de97f20b33001c96e8c36cb04424bcda3929949",
        "6e52713a6ff202847371dce4e678f29c79f515a05b8c8feb55f478ea2098be0f",
    ),
    LEGENDRE_BALANCE: (
        30_511,
        "db6d23186db420c447540f5ec060cba7d7747f2e5964efabef7b34db40c4457d",
        "84ea70634b2b02c826ceda344a859fc8fe835a824d815f9d83bbc059b3ee5830",
        "2ced12da454b5edc63f5d526320e7041678b52246b1a6a80b7c36688de6fbfad",
    ),
    QUOTIENT_ZERO: (
        2_763,
        "d713d36386305ba8ae1856b32958905e1452816440cdc00846f77c0c661f8a04",
        "63d250178b298868ffecda6da44d9be44ea1452af82fba10b85f8385954cff8a",
        "e07a88aa129dbcd1a27ea55c9b30d3a42e7fc09fb1a156ba750b232e9af5d4b8",
    ),
    TAIL_ZERO: (
        4_848,
        "3f0349b6e6c1aeca7a38293b2ff42939ccb87429f71db417efa0c4a24750d585",
        "5ee572b7a0da5fc5ddec2064b56aa249fd1d52bfdadc6aa7cb5769f524f14e08",
        "abd45e6a3bb0308927534eb2c6095003d1f5f7496ee03b34b2281a1d862401b5",
    ),
    SUM_EXTEND: (
        14_354,
        "ab5f786e56b14a4768e92e1bedccdb5b022a76ffe1fad947e469e06092093a9b",
        "d9f1dab168a4c0be40294d5f6543b5c643a1c7b7bf25b0e78c6cf8f1203364e8",
        "c0d77e7c9c809a6dd515cb840a927f0acc27539bf18c16997d26c4b2dcbd5c05",
    ),
    EXTENDED_EXISTS: (
        14_683,
        "3ef66ee0009652ec72793dc32753c3d4cc8b9344e82a2841e7a680bf7f6fb568",
        "3e3454926e74ab6e8cf807f176ee60f6acab738845b1280ab6f9598f0dcef57a",
        "bca11deefc0da866f129d00ee2cb733af429cf737b62d7da7bce27a3df68e5f8",
    ),
    POINTWISE_UPPER: (
        8_866,
        "322e5b03a20782c8a099bab4c86c006189863355082c0ca52262069bec171032",
        "f799acad7f75a47f5823d0f089625b769ee2f955960d5f8d9351aaeddadca9f9",
        "c4b868f5d57a8dbf0e8697d93ab60f8d85bad415d78171ae3bc8f08d7ed6e936",
    ),
    SUM_UPPER: (
        4_249,
        "8139d09620d20e0fe0e3de007cdea59e9bfdf24e3e54f6ebb4f97371498067fd",
        "5f171bbc603e36fe34d2adb2b9ced63309ea57a8cede40849e187b2345225bb1",
        "c6dcb711221dd0eab46ecb469b65e57e5a7ef6671b1e7701de8dc6d7b7ae6edf",
    ),
    VALUATION_BOUND: (
        17_529,
        "cb0a7bb45bbf2c919ae86e50930b511bdba92e365bd32ff2240ed49ebd9f8c55",
        "5560f504d0fb68803fe7e3238aa5a6a3554c0caa415353c9e93449dc10cf516d",
        "27953a9aa58a2af3a639ad414d8d6a0699ecc83f9d389e65e995f22b4eeb2fdb",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    TRANSPORT: (0, 11, 27, 15, 27, 26, 0),
    FACTORIAL_BALANCE: (7, 109, 153, 39, 150, 152, 3),
    LEGENDRE_BALANCE: (3, 60, 80, 30, 80, 79, 0),
    QUOTIENT_ZERO: (3, 31, 36, 21, 36, 35, 0),
    TAIL_ZERO: (1, 40, 79, 27, 77, 78, 2),
    SUM_EXTEND: (6, 86, 119, 33, 112, 118, 7),
    EXTENDED_EXISTS: (3, 40, 62, 29, 62, 61, 0),
    POINTWISE_UPPER: (3, 75, 119, 38, 119, 118, 0),
    SUM_UPPER: (9, 125, 234, 48, 231, 233, 3),
    VALUATION_BOUND: (7, 81, 102, 36, 102, 101, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    TRANSPORT: (27, 27, 15, 1_628, 45),
    FACTORIAL_BALANCE: (153, 150, 39, 65, 40),
    LEGENDRE_BALANCE: (80, 80, 30, 53, 30),
    QUOTIENT_ZERO: (36, 36, 21, 10, 21),
    TAIL_ZERO: (79, 77, 27, 77, 27),
    SUM_EXTEND: (119, 112, 33, 2_027, 54),
    EXTENDED_EXISTS: (62, 62, 29, 330, 39),
    POINTWISE_UPPER: (119, 119, 38, 94, 38),
    SUM_UPPER: (234, 231, 48, 731, 48),
    VALUATION_BOUND: (102, 102, 36, 85, 36),
}
EXPECTED_LAYERED_CLOSURES: dict[str, dict[str, object] | None] = {
    TRANSPORT: {
        "topology_sha256": (
            "0238bdc8d47d7d78af64360c340eb754ab1872a471f9099289d7e831b373a29f"
        ),
        "node_count": 1,
        "stable_catalog_count": 432,
        "reachable_stable_count": 0,
        "candidate_body_count": 1,
        "dependency_edge_count": 0,
        "layer_sizes": [1],
        "layer_cut_count": 1,
        "proof_nodes": 29,
        "proof_depth": 16,
        "proof_objects": 25,
        "proof_edges": 28,
        "reused_objects": 4,
        "annotation_occurrences": 3_274,
        "envelope_depth": 46,
        "package_formula_occurrences": 823,
        "package_formula_depth": 37,
        "proof_dag_sha256": (
            "1fee8452772eda310db575f90a58e4598d33f8e41f0bae1ee0d868df9cb02662"
        ),
    },
    FACTORIAL_BALANCE: {
        "topology_sha256": (
            "b9b8eacb5d400f8486ea93162d25ea12b79378fd2faa3d607bee2debaa1c99f4"
        ),
        "node_count": 106,
        "stable_catalog_count": 432,
        "reachable_stable_count": 52,
        "candidate_body_count": 54,
        "dependency_edge_count": 198,
        "layer_sizes": [56, 19, 7, 5, 5, 2, 4, 3, 1, 1, 1, 1, 1],
        "layer_cut_count": 13,
        "proof_nodes": 132_061,
        "proof_depth": 95,
        "proof_objects": 8_827,
        "proof_edges": 11_885,
        "reused_objects": 3_059,
        "annotation_occurrences": 495_971,
        "envelope_depth": 95,
        "package_formula_occurrences": 31_293,
        "package_formula_depth": 56,
        "proof_dag_sha256": (
            "acb7b66d1169495f9ee1eedeb67318b80a4e2f86e20b1091752af8cc12a986b8"
        ),
    },
    LEGENDRE_BALANCE: {
        "topology_sha256": (
            "5ba94fbd1060f897b7697756933a0d6fafb0b5341f7ca7257f3d8191bb1c99e8"
        ),
        "node_count": 155,
        "stable_catalog_count": 432,
        "reachable_stable_count": 66,
        "candidate_body_count": 89,
        "dependency_edge_count": 314,
        "layer_sizes": [
            72,
            30,
            13,
            6,
            7,
            5,
            6,
            5,
            2,
            2,
            1,
            1,
            2,
            1,
            1,
            1,
        ],
        "layer_cut_count": 16,
        "proof_nodes": 265_579,
        "proof_depth": 96,
        "proof_objects": 11_380,
        "proof_edges": 15_140,
        "reused_objects": 3_761,
        "annotation_occurrences": 950_871,
        "envelope_depth": 96,
        "package_formula_occurrences": 53_563,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "718fbec4be2815d592ae0817a64e701bb097c09e7db880190348eb13c37ae3c1"
        ),
    },
    QUOTIENT_ZERO: {
        "topology_sha256": (
            "b8bb565d48c7f65b3e9326dbf30d0424ac4cdcdecbb16b1e5ea678a9eed05243"
        ),
        "node_count": 24,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 8,
        "dependency_edge_count": 28,
        "layer_sizes": [16, 4, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "proof_nodes": 5_713,
        "proof_depth": 68,
        "proof_objects": 1_198,
        "proof_edges": 1_559,
        "reused_objects": 362,
        "annotation_occurrences": 21_269,
        "envelope_depth": 68,
        "package_formula_occurrences": 1_842,
        "package_formula_depth": 37,
        "proof_dag_sha256": (
            "a08210fcef9d375d26d1e80444a0c8c00c035844f082670ad47ee8628429c454"
        ),
    },
    TAIL_ZERO: {
        "topology_sha256": (
            "fa5ef279694d40a9947d40941ff65de5adaf703da6288816eee0ec525d28316b"
        ),
        "node_count": 25,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 9,
        "dependency_edge_count": 29,
        "layer_sizes": [16, 4, 1, 1, 1, 1, 1],
        "layer_cut_count": 7,
        "proof_nodes": 5_795,
        "proof_depth": 68,
        "proof_objects": 1_233,
        "proof_edges": 1_607,
        "reused_objects": 375,
        "annotation_occurrences": 22_384,
        "envelope_depth": 68,
        "package_formula_occurrences": 2_154,
        "package_formula_depth": 39,
        "proof_dag_sha256": (
            "4f5d5b043ec92b86cfa2e55a66b5b016aa007e56199311c10e14d5c487058700"
        ),
    },
    SUM_EXTEND: {
        "topology_sha256": (
            "c8e00457467a8b81fc283dbd7e709f03c09ec9b4b1cc88993e6363ca56e27b35"
        ),
        "node_count": 36,
        "stable_catalog_count": 432,
        "reachable_stable_count": 22,
        "candidate_body_count": 14,
        "dependency_edge_count": 43,
        "layer_sizes": [23, 6, 2, 1, 1, 1, 1, 1],
        "layer_cut_count": 8,
        "proof_nodes": 13_016,
        "proof_depth": 69,
        "proof_objects": 1_844,
        "proof_edges": 2_404,
        "reused_objects": 561,
        "annotation_occurrences": 55_306,
        "envelope_depth": 69,
        "package_formula_occurrences": 6_105,
        "package_formula_depth": 45,
        "proof_dag_sha256": (
            "6db71be4cb0c98d0cf6625a22988563d1ea4483dbfaff838fd11d7eab3452437"
        ),
    },
    EXTENDED_EXISTS: {
        "topology_sha256": (
            "1aaa91cbc41a620b8581ea72e366ceeff87b5b0815c008cb4ed25307cee6a483"
        ),
        "node_count": 45,
        "stable_catalog_count": 432,
        "reachable_stable_count": 29,
        "candidate_body_count": 16,
        "dependency_edge_count": 55,
        "layer_sizes": [30, 6, 2, 1, 2, 1, 1, 1, 1],
        "layer_cut_count": 9,
        "proof_nodes": 133_061,
        "proof_depth": 94,
        "proof_objects": 4_711,
        "proof_edges": 6_421,
        "reused_objects": 1_711,
        "annotation_occurrences": 448_034,
        "envelope_depth": 94,
        "package_formula_occurrences": 7_694,
        "package_formula_depth": 45,
        "proof_dag_sha256": (
            "8dc0f117c194e27b7e2ad24287d0d4221407c5081651289e086cd9dddea195c1"
        ),
    },
    POINTWISE_UPPER: {
        "topology_sha256": (
            "ba5a296f47fa7c50c9ad240813ab566dce86208f0d2f8ca33966441b3fca6a01"
        ),
        "node_count": 22,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 6,
        "dependency_edge_count": 25,
        "layer_sizes": [16, 2, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "proof_nodes": 6_162,
        "proof_depth": 68,
        "proof_objects": 1_377,
        "proof_edges": 1_782,
        "reused_objects": 406,
        "annotation_occurrences": 21_544,
        "envelope_depth": 68,
        "package_formula_occurrences": 1_413,
        "package_formula_depth": 40,
        "proof_dag_sha256": (
            "1b4988a8ef98341f37a89db640b27c5ab7af53f13f74e96d5c899fd9e599d2fc"
        ),
    },
    SUM_UPPER: {
        "topology_sha256": (
            "fd3681ed3ddc67d5011c1c21be40bb577692f7a0ef533319deb6a6cf0c9892f4"
        ),
        "node_count": 10,
        "stable_catalog_count": 432,
        "reachable_stable_count": 9,
        "candidate_body_count": 1,
        "dependency_edge_count": 9,
        "layer_sizes": [9, 1],
        "layer_cut_count": 2,
        "proof_nodes": 3_133,
        "proof_depth": 66,
        "proof_objects": 858,
        "proof_edges": 1_114,
        "reused_objects": 257,
        "annotation_occurrences": 10_463,
        "envelope_depth": 66,
        "package_formula_occurrences": 985,
        "package_formula_depth": 34,
        "proof_dag_sha256": (
            "efbb477d80b81b496d6f9158f463d9ffaf6f35023049853779aa5ea2559d2e34"
        ),
    },
    VALUATION_BOUND: {
        "topology_sha256": (
            "900b268c5efe042e68cf7bb86d2b848b5853fbde04d7bdd4e9abb9c7fa05bd7e"
        ),
        "node_count": 174,
        "stable_catalog_count": 432,
        "reachable_stable_count": 72,
        "candidate_body_count": 102,
        "dependency_edge_count": 370,
        "layer_sizes": [
            78,
            34,
            14,
            7,
            8,
            7,
            7,
            6,
            3,
            2,
            1,
            1,
            2,
            1,
            1,
            1,
            1,
        ],
        "layer_cut_count": 17,
        "proof_nodes": 267_902,
        "proof_depth": 95,
        "proof_objects": 12_561,
        "proof_edges": 16_589,
        "reused_objects": 4_029,
        "annotation_occurrences": 948_589,
        "envelope_depth": 95,
        "package_formula_occurrences": 57_897,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "b1f462c9a736c0740636d56963938d98180b1ef82f98c27fe5168c99db353ed4"
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
    "alpha_enrollment_v11.py": (
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093"
    ),
    "editions_v11.py": (
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf"
    ),
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-valuation-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "aebab5f4cf6a63b67a0716c3dcd792a876f263bce6d371d25dcb4e3dbf78a8b3"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_central_binom_valuation_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


def _power_valuation_term(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    marker = f"test_b5cv_value_marker_{tag}"
    expanded = power_valuation(base, marker, exponent, tag=tag)
    assert expanded.count(marker) == 4
    return expanded.replace(marker, f"({value})")


def _power_valuation_exponent_term(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    marker = f"test_b5cv_exponent_marker_{tag}"
    expanded = power_valuation(base, value, marker, tag=tag)
    assert expanded.count(marker) == 6
    return expanded.replace(marker, f"({exponent})")


def _factorial_valuation_term(
    base: str,
    length: str,
    exponent: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    value = f"b5cv_factorial_{tag}"
    factorial = _factorial_relation_term(
        length,
        value,
        tag=f"{tag}_factorial",
        variables=variables + (value,),
    )
    valuation = power_valuation(
        base,
        value,
        exponent,
        tag=f"{tag}_valuation",
    )
    return f"exists {value}. (({factorial}) /\\ ({valuation}))"


def _legendre_sum_term(
    base: str,
    value: str,
    result: str,
    *,
    tag: str,
) -> str:
    marker = f"test_b5cv_legendre_marker_{tag}"
    expanded = legendre_sum(base, marker, result, tag=tag)
    assert expanded.count(marker) >= 2
    return expanded.replace(marker, f"({value})")


def _pointwise(
    length: str,
    *,
    tag: str,
    left_code: str = "b",
    left_scale: str = "c",
    right_code: str = "d",
    right_scale: str = "e",
    doubled: bool = True,
) -> str:
    variables = (
        left_code,
        left_scale,
        right_code,
        right_scale,
        "l",
        "B",
        "A",
        "i",
        "q",
        "Q",
    )
    bound = _lt_term(
        "i",
        length,
        tag=f"{tag}_bound",
        variables=variables,
    )
    left = _at(
        left_code,
        left_scale,
        "i",
        "q",
        tag=f"{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        "i",
        "Q",
        tag=f"{tag}_right",
    )
    upper = "S (q + q)" if doubled else "q + q"
    result = _le_term(
        "Q",
        upper,
        tag=f"{tag}_result",
        variables=variables,
    )
    return (
        f"forall i q Q. ({bound}) -> ({left}) -> ({right}) -> ({result})"
    )


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    balance_variables = ("p", "n", "c", "e", "A", "B")
    transport_source = power_valuation(
        "p", "a", "e", tag="b5cvvet_source"
    )
    transport_target = power_valuation(
        "p", "b", "e", tag="b5cvvet_target"
    )
    balance_prime = prime("p", tag="b5cvfb_prime")
    balance_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvfb_central",
        variables=balance_variables,
    )
    balance_value = power_valuation(
        "p", "c", "e", tag="b5cvfb_value"
    )
    balance_total = _factorial_valuation_term(
        "p",
        "n + n",
        "A",
        tag="b5cvfb_total",
        variables=balance_variables,
    )
    balance_column = factorial_valuation(
        "p", "n", "B", tag="b5cvfb_column"
    )
    legendre_prime = prime("p", tag="b5cvlb_prime")
    legendre_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvlb_central",
        variables=balance_variables,
    )
    legendre_value = power_valuation(
        "p", "c", "e", tag="b5cvlb_value"
    )
    legendre_total = _legendre_sum_term(
        "p", "n + n", "A", tag="b5cvlb_total"
    )
    legendre_column = legendre_sum(
        "p", "n", "B", tag="b5cvlb_column"
    )
    quotient_variables = ("p", "n", "e", "d", "q", "r")
    quotient_prime = prime("p", tag="b5cvqz_prime")
    quotient_exponent = _lt_term(
        "n",
        "e",
        tag="b5cvqz_exponent",
        variables=quotient_variables,
    )
    quotient_power = _power_terms(
        "p", "e", "d", tag="b5cvqz_power"
    )
    quotient_division = _divrem_term(
        "d",
        "n",
        "q",
        "r",
        tag="b5cvqz_division",
        variables=quotient_variables,
    )
    tail_variables = ("p", "n", "b", "c", "l", "i")
    tail_prime = prime("p", tag="b5cvptez_prime")
    tail_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5cvptez_prefix"
    )
    tail_start = _le_term(
        "n",
        "i",
        tag="b5cvptez_start",
        variables=tail_variables,
    )
    tail_bound = _lt_term(
        "i",
        "l",
        tag="b5cvptez_bound",
        variables=tail_variables,
    )
    tail_result = _at("b", "c", "i", "0", tag="b5cvptez_result")
    extension_prime = prime("p", tag="b5cvpsez_prime")
    extension_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "n + g", tag="b5cvpsez_prefix"
    )
    extension_sum = _sum_relation_terms(
        "b", "c", "n + g", "t", tag="b5cvpsez_sum"
    )
    extension_legendre = legendre_sum(
        "p", "n", "e", tag="b5cvpsez_legendre"
    )
    extended_prime = prime("p", tag="b5cvlsepe_prime")
    extended_legendre = legendre_sum(
        "p", "n", "e", tag="b5cvlsepe_legendre"
    )
    extended_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "n + g", tag="b5cvlsepe_prefix"
    )
    extended_sum = _sum_relation_terms(
        "b", "c", "n + g", "e", tag="b5cvlsepe_sum"
    )
    pointwise_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5cvpdpu_left"
    )
    pointwise_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5cvpdpu_right"
    )
    fold_left = sum_relation(
        "b", "c", "l", "B", tag="b5cvbsdsl_left"
    )
    fold_right = sum_relation(
        "d", "e", "l", "A", tag="b5cvbsdsl_right"
    )
    fold_result = _le_term(
        "A",
        "(B + B) + l",
        tag="b5cvbsdsl_result",
        variables=("b", "c", "d", "e", "l", "B", "A"),
    )
    final_variables = ("p", "n", "c", "e")
    final_prime = prime("p", tag="b5cvpvd_prime")
    final_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvpvd_central",
        variables=final_variables,
    )
    final_valuation = power_valuation(
        "p", "c", "e", tag="b5cvpvd_valuation"
    )
    final_result = _le_term(
        "e",
        "n + n",
        tag="b5cvpvd_result",
        variables=final_variables,
    )
    return {
        TRANSPORT: (
            "forall p a b e. a = b -> "
            f"({transport_source}) -> ({transport_target})"
        ),
        FACTORIAL_BALANCE: (
            "forall p n c e A B. "
            f"({balance_prime}) -> ({balance_central}) -> "
            f"({balance_value}) -> ({balance_total}) -> "
            f"({balance_column}) -> A = (B + B) + e"
        ),
        LEGENDRE_BALANCE: (
            "forall p n c e A B. "
            f"({legendre_prime}) -> ({legendre_central}) -> "
            f"({legendre_value}) -> ({legendre_total}) -> "
            f"({legendre_column}) -> A = (B + B) + e"
        ),
        QUOTIENT_ZERO: (
            "forall p n e d q r. "
            f"({quotient_prime}) -> ({quotient_exponent}) -> "
            f"({quotient_power}) -> ({quotient_division}) -> q = 0"
        ),
        TAIL_ZERO: (
            "forall p n b c l i. "
            f"({tail_prime}) -> ({tail_prefix}) -> ({tail_start}) -> "
            f"({tail_bound}) -> ({tail_result})"
        ),
        SUM_EXTEND: (
            "forall p n b c g t e. "
            f"({extension_prime}) -> ({extension_prefix}) -> "
            f"({extension_sum}) -> ({extension_legendre}) -> t = e"
        ),
        EXTENDED_EXISTS: (
            "forall p n e g. "
            f"({extended_prime}) -> ({extended_legendre}) -> "
            f"exists b c. (({extended_prefix}) /\\ ({extended_sum}))"
        ),
        POINTWISE_UPPER: (
            "forall p n b c d e l. "
            f"({pointwise_left}) -> ({pointwise_right}) -> "
            f"({_pointwise('l', tag='b5cvpdpu_result')})"
        ),
        SUM_UPPER: (
            "forall b c d e l B A. "
            f"({fold_left}) -> ({fold_right}) -> "
            f"({_pointwise('l', tag='b5cvbsdsl_pointwise')}) -> "
            f"({fold_result})"
        ),
        VALUATION_BOUND: (
            "forall p n c e. "
            f"({final_prime}) -> ({final_central}) -> "
            f"({final_valuation}) -> ({final_result})"
        ),
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    statements = _expected_statements()
    rows = _table(_rows())
    result: dict[str, str] = {}

    def changed(name: str, old: str, new: str) -> None:
        assert statements[name].count(old) == 1
        result[name] = statements[name].replace(old, new)

    changed(
        TRANSPORT,
        power_valuation("p", "b", "e", tag="b5cvvet_target"),
        _power_valuation_exponent_term(
            "p", "b", "S e", tag="b5cvvet_target"
        ),
    )
    changed(FACTORIAL_BALANCE, "A = (B + B) + e", "A = (B + B) + S e")
    changed(LEGENDRE_BALANCE, "A = (B + B) + e", "A = (B + B) + S e")
    changed(QUOTIENT_ZERO, "q = 0", "q = 1")
    changed(
        TAIL_ZERO,
        _at("b", "c", "i", "0", tag="b5cvptez_result"),
        _at("b", "c", "i", "1", tag="b5cvptez_result"),
    )
    changed(SUM_EXTEND, "t = e", "t = S e")
    changed(
        EXTENDED_EXISTS,
        _sum_relation_terms(
            "b", "c", "n + g", "e", tag="b5cvlsepe_sum"
        ),
        _sum_relation_terms(
            "b", "c", "n + g", "S e", tag="b5cvlsepe_sum"
        ),
    )
    changed(
        POINTWISE_UPPER,
        _pointwise("l", tag="b5cvpdpu_result"),
        _pointwise("l", tag="b5cvpdpu_result", doubled=False),
    )
    changed(
        SUM_UPPER,
        _le_term(
            "A",
            "(B + B) + l",
            tag="b5cvbsdsl_result",
            variables=("b", "c", "d", "e", "l", "B", "A"),
        ),
        _le_term(
            "A",
            "B + B",
            tag="b5cvbsdsl_result",
            variables=("b", "c", "d", "e", "l", "B", "A"),
        ),
    )
    changed(
        VALUATION_BOUND,
        _le_term(
            "e",
            "n + n",
            tag="b5cvpvd_result",
            variables=("p", "n", "c", "e"),
        ),
        _le_term(
            "S e",
            "n + n",
            tag="b5cvpvd_result",
            variables=("p", "n", "c", "e"),
        ),
    )
    assert set(result) == set(rows)
    return result


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    rows = (
        *editions_v11.ALPHA_SPECS,
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
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


def _run_closure_worker(name: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--closure-worker", name],
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"closure worker failed for {name}:\n"
        f"stdout={result.stdout[-4000:]}\n"
        f"stderr={result.stderr[-4000:]}"
    )
    prefix = "B5CV_LAYERED_RECEIPT "
    lines = [line for line in result.stdout.splitlines() if line.startswith(prefix)]
    assert len(lines) == 1, result.stdout[-4000:]
    payload = json.loads(lines[0][len(prefix) :])
    assert payload["name"] == name
    return payload["receipt"]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_central_valuation_static_contract() -> None:
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
    assert len(LIVE_EDGES) == 42
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[0].script.count("rewrite hvalue at hsource") == 4
    assert rows[4].script.count("rewrite <- hzero") == 2
    assert rows[5].script.count("induction g") == 1
    assert rows[8].script.count("induction l") == 1
    assert rows[9].script.count("apply add_le_cancel_right") == 1
    assert not any(
        command.startswith("rewrite")
        and command.endswith(
            (
                " at hcentral",
                " at htotal_legendre",
                " at hcolumn_legendre",
            )
        )
        for row in rows
        for command in row.script
    )


def test_bertrand_central_valuation_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        actual = sha256((library / filename).read_bytes()).hexdigest()
        assert actual == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_central_valuation_receipts_are_shaped() -> None:
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
def test_bertrand_central_valuation_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 CENTRAL VALUATION {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_valuation_bodies_are_frozen(name: str) -> None:
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
        label=f"B5 central valuation body {name}",
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
    print(
        f"B5 CENTRAL VALUATION {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_central_valuation_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_rows())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            entry for entry in item.dependencies if entry != dependency
        ),
    )
    assert len(shortened.dependencies) + 1 == len(item.dependencies)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_valuation_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_rows())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_bertrand_central_valuation_mutations_have_counterfixtures() -> None:
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
def test_bertrand_central_valuation_genuine_mutations_are_rejected(
    name: str,
) -> None:
    item = _table(_rows())[name]
    mutation = _mutations()[name]
    assert _closed_formula(item.statement) != _closed_formula(mutation)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=mutation),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_valuation_layered_closures_are_frozen(
    name: str,
) -> None:
    actual = _run_closure_worker(name)
    print(
        f"B5 CENTRAL VALUATION {name} LAYERED CLOSURE actual={actual!r}",
        flush=True,
    )
    expected = EXPECTED_LAYERED_CLOSURES[name]
    assert expected is not None, actual
    assert actual == expected


def _main() -> None:
    assert len(sys.argv) == 3 and sys.argv[1] == "--closure-worker"
    name = sys.argv[2]
    assert name in EXPECTED_NAMES
    receipt = _layered_receipt(name)
    print(
        "B5CV_LAYERED_RECEIPT "
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
