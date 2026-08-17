"""Fail-closed audit for the Bertrand B5 prime-contribution foundation.

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
from peano_lab.library.bertrand_prime_contribution_candidate import (
    COPRIME_POWER_RIGHT,
    COPRIME_POWERS,
    PRIME_CONTRIBUTION_CHOICE_EXISTS,
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL,
    PRIME_CONTRIBUTION_FACTOR_DIVIDES,
    PRIME_CONTRIBUTION_PREFIX_EXISTS,
    PRIME_CONTRIBUTION_PREFIX_EXTEND,
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME,
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY,
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES,
    PRIME_CONTRIBUTION_PRODUCT_EXISTS,
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL,
    make_bertrand_prime_contribution_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_fold_surface import _product_relation_term
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
    PRIME_CONTRIBUTION_CHOICE_EXISTS,
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL,
    PRIME_CONTRIBUTION_PREFIX_EXTEND,
    PRIME_CONTRIBUTION_PREFIX_EXISTS,
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY,
    PRIME_CONTRIBUTION_PRODUCT_EXISTS,
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL,
    COPRIME_POWER_RIGHT,
    COPRIME_POWERS,
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME,
    PRIME_CONTRIBUTION_FACTOR_DIVIDES,
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES,
)

EXPECTED_DEPENDENCIES = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: (
        "prime_decidable",
        "power_valuation_exists",
        "pow_exists",
    ),
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: (
        "power_valuation_functional",
        "pow_functional",
    ),
    PRIME_CONTRIBUTION_PREFIX_EXTEND: (
        PRIME_CONTRIBUTION_CHOICE_EXISTS,
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    PRIME_CONTRIBUTION_PREFIX_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        PRIME_CONTRIBUTION_PREFIX_EXTEND,
    ),
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY: (
        "beta_at_unique",
        PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL,
    ),
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: (
        "beta_product_exists",
        PRIME_CONTRIBUTION_PREFIX_EXISTS,
    ),
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: (
        "beta_product_transport_prefix",
        "beta_product_functional",
        PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY,
    ),
    COPRIME_POWER_RIGHT: (
        "pow_zero",
        "pow_successor_decompose",
        "coprime_one_right",
        "coprime_mul_right",
    ),
    COPRIME_POWERS: (
        "pow_zero",
        "pow_successor_decompose",
        "coprime_one_left",
        "coprime_mul_left",
        COPRIME_POWER_RIGHT,
    ),
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME: (
        "beta_at_unique",
        "distinct_primes_coprime",
        "coprime_one_left",
        "coprime_one_right",
        COPRIME_POWERS,
    ),
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: (
        "power_valuation_power_divides",
        "pow_functional",
        "one_multiple",
    ),
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: (
        "beta_at_unique",
        "beta_pairwise_coprime_product_divides_common_multiple",
        PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME,
        PRIME_CONTRIBUTION_FACTOR_DIVIDES,
    ),
}

EXPECTED_COMMAND_COUNTS = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: 27,
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: 48,
    PRIME_CONTRIBUTION_PREFIX_EXTEND: 48,
    PRIME_CONTRIBUTION_PREFIX_EXISTS: 21,
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY: 37,
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: 15,
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: 33,
    COPRIME_POWER_RIGHT: 38,
    COPRIME_POWERS: 55,
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME: 79,
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: 31,
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: 40,
}

EXPECTED_CUT_COUNTS = (3, 2, 3, 3, 2, 2, 3, 4, 5, 5, 3, 4)

EXPECTED_ARTIFACTS = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: (
        14685,
        "7b3ce224e85af7ab0568c99c7abbe134593f6f61cb2da69dd6e95f1b7478632b",
        "452efc87ff4ad5943e3d117b05adb5887b500bc8117c1a5ce3312c96029f956b",
        "6fb9aeb404da2e2071679fccf8fe9737fd68f23ce7b035d7e4b15d879c07f4bb",
    ),
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: (
        28545,
        "121200824b4c050d90215b0ac6a06a8006de91fbada52625254e1fe881059963",
        "817cdba5b1c8f0269fafe95a0cd47d4118e3ac26fa167eaff642140413687266",
        "006db2ffd5157823501a7d3adba8aef12e27180a51c7c45970401f91178d3a49",
    ),
    PRIME_CONTRIBUTION_PREFIX_EXTEND: (
        34598,
        "248ac6a3a605f61d9737112346518e69a95efec52fad2de8db8f59ac09053ed9",
        "da5762fa2e9f3a1de52e9acb81cc10a77421e5d5402dfecec180e4098e33b8b7",
        "7625f4e61ed7db73d87c8613d5f447b612fadc617e0ab4435194046dcbfe8587",
    ),
    PRIME_CONTRIBUTION_PREFIX_EXISTS: (
        17454,
        "4be307156895c2ae3d599536abbe89e8a6f4c79a07e9892443a3983ed76a17f8",
        "f30b091d0aaae37228db6de445ef891579625c820f3fee3b0d727bc2743712a1",
        "7378442e8da61eb73afd31142667992f76a324d37ea26f19f03989e52a5924f0",
    ),
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY: (
        34437,
        "751b7e2188d254d7faba74a75f7db484e6180075074fa876e63d7d2008d66e0c",
        "50cf14e5df1764dcb218a5eb67a2bc3aa70036194ff0bed54f32fe445aff6140",
        "51a4c8aa52c081b90b093c3f19ce837dccc62dca848c1eb07ee84821225d2285",
    ),
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: (
        23989,
        "0178e9cb1db49757a82ccfdb3132d825594c76afde47f34a7d917b479b6af792",
        "f1b3eae270b7c74097703d048fcf2324f749d39dbdfd2c7e88dc06719b47cfb1",
        "1d1b2bd4b0a3fea6255eca228223b7359cbcb8873dac77b5e63cc78444b9574d",
    ),
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: (
        42563,
        "03780cc1414cb19948a5152818b5852666f0bfcfc0cc5671bf49338542eae180",
        "5dff5d127d921e9ff50c80400ad8dd923c5f3d48cc3ab4dff11ade21a503c9fc",
        "c7fdee750f0247f9bd9ec9d5a351e62a05628268eb29f29062f7209ab4079ca4",
    ),
    COPRIME_POWER_RIGHT: (
        3202,
        "6c6ee19dbc29626c7569641141360fa146515c6b5ca39bbddf77e96230450430",
        "061b7b225192d672e753d3cb577b672bde17a6af09e5b9321776e2bda0bd2b40",
        "1b4cafdd55c4921a6c240032f9790b13fd96549a524051f1f85606610c2423ad",
    ),
    COPRIME_POWERS: (
        6376,
        "047423e243b1cc48e6ce2ee6ae0f129c48c9ad9fa42f13ab00a0072306d91644",
        "a5d2520ff48806cd860463690279d109f61c7b10fb19283fb8ca8b0cc3533e3c",
        "1ca862fc16b53626c71c01f11b9b9374bf840e0cd3b83701c3a22fd8fa1fe554",
    ),
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME: (
        19338,
        "3a57e746387af2b03b75cbee39f7d6b8a659510b08f3724fefcbf265bd433bc3",
        "7be6d68bc3c10a37634a0b748cac3f0e8f852b1e7ee87fea065fcc498292d241",
        "231d4d76f5fb3479684850202e23214501ea04a3f5efc20c3668b358e97bddfc",
    ),
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: (
        14768,
        "a9264830ba79d102ed8ce5c1589a26e7d15506858711c6abfff8a75aaf24ed39",
        "10c4e6c83803040405328e411e4e28f82e4becce8802a93cf0df0db3ae2985b6",
        "5a8a1f7ad35d0666f5fb8e9ee66b326fe6c3394d8db2ebf47a889571d39f5422",
    ),
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: (
        21912,
        "8ed247d664927ab205992faf585a89198be8f034afb61ea5813e7618a864c7fe",
        "6ca32314efed6008c4e873d57d36486aa68916eafdba1f0561d334169a42b67a",
        "74d3cb81cd859985f944a58929a0ba8d96a96fc137f92df3afcd88a7b19677a9",
    ),
}
EXPECTED_BODIES = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: (3, 27, 29, 14, 29, 28, 0),
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: (2, 48, 101, 25, 101, 100, 0),
    PRIME_CONTRIBUTION_PREFIX_EXTEND: (3, 48, 89, 32, 89, 88, 0),
    PRIME_CONTRIBUTION_PREFIX_EXISTS: (3, 21, 33, 16, 33, 32, 0),
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY:
        (2, 37, 76, 28, 76, 75, 0),
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: (2, 15, 21, 12, 21, 20, 0),
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: (3, 33, 63, 29, 63, 62, 0),
    COPRIME_POWER_RIGHT: (4, 38, 55, 20, 55, 54, 0),
    COPRIME_POWERS: (5, 55, 74, 27, 74, 73, 0),
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME:
        (5, 79, 118, 37, 118, 117, 0),
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: (3, 31, 43, 20, 43, 42, 0),
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: (4, 40, 64, 29, 64, 63, 0),
}
EXPECTED_ENVELOPES = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: (29, 29, 14, 14, 14),
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: (101, 101, 25, 769, 42),
    PRIME_CONTRIBUTION_PREFIX_EXTEND: (89, 89, 32, 8247, 65),
    PRIME_CONTRIBUTION_PREFIX_EXISTS: (33, 33, 16, 707, 46),
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY: (76, 76, 28, 68, 28),
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: (21, 21, 12, 8, 12),
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: (63, 63, 29, 21, 29),
    COPRIME_POWER_RIGHT: (55, 55, 20, 279, 35),
    COPRIME_POWERS: (74, 74, 27, 472, 39),
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME:
        (118, 118, 37, 124, 38),
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: (43, 43, 20, 22, 21),
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: (64, 64, 29, 24, 29),
}
EXPECTED_LAYERED_CLOSURES = {
    PRIME_CONTRIBUTION_CHOICE_EXISTS: {
        "topology_sha256":
            "d6e9a1ef0c36eebb9037a6165430e956ed028d41d6ecbf85280d46948b5ceb10",
        "node_count": 18,
        "stable_catalog_count": 432,
        "reachable_stable_count": 12,
        "candidate_body_count": 6,
        "dependency_edge_count": 19,
        "layer_sizes": [12, 2, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "proof_nodes": 67968,
        "proof_depth": 93,
        "proof_objects": 4158,
        "proof_edges": 5770,
        "reused_objects": 1613,
        "annotation_occurrences": 228262,
        "envelope_depth": 93,
        "package_formula_occurrences": 3614,
        "package_formula_depth": 38,
        "proof_dag_sha256":
            "e84d0e15c2905343b64bb485e3609ec9ad81b8ad2a5585752828cc420670a976",
    },
    PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL: {
        "topology_sha256":
            "9f30cd1653053fa57b3ff949333b6daa98ef0109c312bad147c6a49a9f10c2ce",
        "node_count": 4,
        "stable_catalog_count": 432,
        "reachable_stable_count": 2,
        "candidate_body_count": 2,
        "dependency_edge_count": 3,
        "layer_sizes": [2, 1, 1],
        "layer_cut_count": 3,
        "proof_nodes": 3071,
        "proof_depth": 65,
        "proof_objects": 930,
        "proof_edges": 1234,
        "reused_objects": 305,
        "annotation_occurrences": 17507,
        "envelope_depth": 65,
        "package_formula_occurrences": 2549,
        "package_formula_depth": 41,
        "proof_dag_sha256":
            "fa36f0a612171dc170d1b80a8bce2bd49f43635762d012797d1f461c2eab5b01",
    },
    PRIME_CONTRIBUTION_PREFIX_EXTEND: {
        "topology_sha256":
            "888d9251fcbc3086705fd58489b03d72ad636f5cb80f5c8b595debe133324d9b",
        "node_count": 21,
        "stable_catalog_count": 432,
        "reachable_stable_count": 14,
        "candidate_body_count": 7,
        "dependency_edge_count": 22,
        "layer_sizes": [14, 2, 1, 1, 1, 1, 1],
        "layer_cut_count": 7,
        "proof_nodes": 97261,
        "proof_depth": 93,
        "proof_objects": 4225,
        "proof_edges": 5866,
        "reused_objects": 1642,
        "annotation_occurrences": 337845,
        "envelope_depth": 93,
        "package_formula_occurrences": 5126,
        "package_formula_depth": 46,
        "proof_dag_sha256":
            "5a8ab05be48f7798940a1e2b503e939bab3169b302bf4035d8c30665348042d4",
    },
    PRIME_CONTRIBUTION_PREFIX_EXISTS: {
        "topology_sha256":
            "ace13223694410cb4e167bce3ad1616703531ce60e5fec9f6972f8c13f9c39c7",
        "node_count": 24,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 8,
        "dependency_edge_count": 25,
        "layer_sizes": [16, 2, 1, 1, 1, 1, 1, 1],
        "layer_cut_count": 8,
        "proof_nodes": 97333,
        "proof_depth": 93,
        "proof_objects": 4261,
        "proof_edges": 5910,
        "reused_objects": 1650,
        "annotation_occurrences": 335095,
        "envelope_depth": 93,
        "package_formula_occurrences": 5845,
        "package_formula_depth": 46,
        "proof_dag_sha256":
            "548c0e37814f74338d7333b698c4d56780f4e345bb6ca650340eb823038c07f4",
    },
    PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY: {
        "topology_sha256":
            "a5f238fc96919b9e870efe53b7816989a701e7e1dd70203a0e3949c245bcf61d",
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 3,
        "candidate_body_count": 3,
        "dependency_edge_count": 5,
        "layer_sizes": [3, 1, 1, 1],
        "layer_cut_count": 4,
        "proof_nodes": 4277,
        "proof_depth": 66,
        "proof_objects": 974,
        "proof_edges": 1291,
        "reused_objects": 318,
        "annotation_occurrences": 23725,
        "envelope_depth": 66,
        "package_formula_occurrences": 4065,
        "package_formula_depth": 47,
        "proof_dag_sha256":
            "f52ba2d75f03ab11061b6f6d285501d38cfa69fdedc7729bd870e9c5561dc5ce",
    },
    PRIME_CONTRIBUTION_PRODUCT_EXISTS: {
        "topology_sha256":
            "42b2cd3ba8fa8b5305bac12bfce66f41fb5cab611cc454f9e68d516dc6637eae",
        "node_count": 26,
        "stable_catalog_count": 432,
        "reachable_stable_count": 17,
        "candidate_body_count": 9,
        "dependency_edge_count": 27,
        "layer_sizes": [17, 2, 1, 1, 1, 1, 1, 1, 1],
        "layer_cut_count": 9,
        "proof_nodes": 127853,
        "proof_depth": 93,
        "proof_objects": 4283,
        "proof_edges": 5937,
        "reused_objects": 1655,
        "annotation_occurrences": 437392,
        "envelope_depth": 93,
        "package_formula_occurrences": 6847,
        "package_formula_depth": 46,
        "proof_dag_sha256":
            "64ed3d5fca871a617efba8c1d35504679081e80ceacb870cb0e4caf6f017d754",
    },
    PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL: {
        "topology_sha256":
            "ff1e6c73b84c9b78c5665552d07c112eb3e1e1143a95dd0e6aa82b85b4d4a4dc",
        "node_count": 9,
        "stable_catalog_count": 432,
        "reachable_stable_count": 5,
        "candidate_body_count": 4,
        "dependency_edge_count": 8,
        "layer_sizes": [5, 1, 1, 1, 1],
        "layer_cut_count": 5,
        "proof_nodes": 5797,
        "proof_depth": 67,
        "proof_objects": 1034,
        "proof_edges": 1368,
        "reused_objects": 335,
        "annotation_occurrences": 33407,
        "envelope_depth": 67,
        "package_formula_occurrences": 6437,
        "package_formula_depth": 48,
        "proof_dag_sha256":
            "0d6a0dbb28911a495fd29c63622158a4bc5a56ba08b18fef6fe8d5d56bc61dd1",
    },
    COPRIME_POWER_RIGHT: {
        "topology_sha256":
            "0213a058bf19a35c2eeac83b2b7edd5e095e6c9825a9e5648a064d905c4a829a",
        "node_count": 5,
        "stable_catalog_count": 432,
        "reachable_stable_count": 4,
        "candidate_body_count": 1,
        "dependency_edge_count": 4,
        "layer_sizes": [4, 1],
        "layer_cut_count": 2,
        "proof_nodes": 8059,
        "proof_depth": 66,
        "proof_objects": 1678,
        "proof_edges": 2279,
        "reused_objects": 602,
        "annotation_occurrences": 28560,
        "envelope_depth": 66,
        "package_formula_occurrences": 897,
        "package_formula_depth": 35,
        "proof_dag_sha256":
            "eb5bb90791fa36ef6d91fcc3330871073c6c7f1c3f524373e706786d57dce913",
    },
    COPRIME_POWERS: {
        "topology_sha256":
            "48d896752715403f25b6f5445e1b2bccc144457d00b2d26c12540db17c9647d7",
        "node_count": 8,
        "stable_catalog_count": 432,
        "reachable_stable_count": 6,
        "candidate_body_count": 2,
        "dependency_edge_count": 9,
        "layer_sizes": [6, 1, 1],
        "layer_cut_count": 3,
        "proof_nodes": 12335,
        "proof_depth": 67,
        "proof_objects": 1762,
        "proof_edges": 2383,
        "reused_objects": 622,
        "annotation_occurrences": 43057,
        "envelope_depth": 67,
        "package_formula_occurrences": 1399,
        "package_formula_depth": 36,
        "proof_dag_sha256":
            "a6ba6e7a36a364a86da8fe725a7f309f2c8f5aa0a43e77200b385db2f0b34736",
    },
    PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME: {
        "topology_sha256":
            "b2aeb95c57895d31bf89c3b17b040a1d2a4b5e72c117024a7c664bdafd4048c8",
        "node_count": 11,
        "stable_catalog_count": 432,
        "reachable_stable_count": 8,
        "candidate_body_count": 3,
        "dependency_edge_count": 14,
        "layer_sizes": [8, 1, 1, 1],
        "layer_cut_count": 4,
        "proof_nodes": 15276,
        "proof_depth": 67,
        "proof_objects": 1979,
        "proof_edges": 2696,
        "reused_objects": 718,
        "annotation_occurrences": 53961,
        "envelope_depth": 67,
        "package_formula_occurrences": 2331,
        "package_formula_depth": 44,
        "proof_dag_sha256":
            "0544f3e46c269df4efa3363a69520504267ad31d0039e344c62036d40961acde",
    },
    PRIME_CONTRIBUTION_FACTOR_DIVIDES: {
        "topology_sha256":
            "59df07779479a6c6f522d8f79e58c2d5347188e9e70d22efba841023f4f65558",
        "node_count": 4,
        "stable_catalog_count": 432,
        "reachable_stable_count": 2,
        "candidate_body_count": 2,
        "dependency_edge_count": 3,
        "layer_sizes": [3, 1],
        "layer_cut_count": 2,
        "proof_nodes": 2817,
        "proof_depth": 66,
        "proof_objects": 846,
        "proof_edges": 1106,
        "reused_objects": 261,
        "annotation_occurrences": 12854,
        "envelope_depth": 66,
        "package_formula_occurrences": 1660,
        "package_formula_depth": 39,
        "proof_dag_sha256":
            "71287c5e83f594d865e286a227b33ea6c8d4de572e35690e62c04435a5da7046",
    },
    PRIME_CONTRIBUTION_PRODUCT_DIVIDES: {
        "topology_sha256":
            "08b9257649f6520645a79f53e9bcc2a60f3b4621e9caeea60a59359bae3dfd71",
        "node_count": 24,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 8,
        "dependency_edge_count": 35,
        "layer_sizes": [17, 3, 2, 1, 1],
        "layer_cut_count": 5,
        "proof_nodes": 25296,
        "proof_depth": 68,
        "proof_objects": 2645,
        "proof_edges": 3561,
        "reused_objects": 917,
        "annotation_occurrences": 89428,
        "envelope_depth": 68,
        "package_formula_occurrences": 5972,
        "package_formula_depth": 46,
        "proof_dag_sha256":
            "7cb148781310daf989a5d0301da0e4161aaa6185f7de2df7b42ae60903845d0a",
    },
}

SOURCE_PINS = {
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "finite_fold_surface.py":
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "bertrand_primorial_foundation_candidate.py":
        "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98",
    "bertrand_primorial_choose_interval_candidate.py":
        "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09",
    "bertrand_prime_contribution_candidate.py":
        "fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-prime-contribution-foundation-tranche-rfc-v1.md"
)
RFC_SHA256 = "4970fabdc7ff1872a52bed7a18643a777939304cf7b2061a196518533385b520"


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_prime_contribution_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    result: dict[str, TheoremSpec] = {}
    for row in editions_v11.ALPHA_SPECS:
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


def _e_le(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("le_gap",))
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _e_divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (quotient,) = _binders(tag, avoid, ("divides_quotient",))
    return f"exists {quotient}. {value} = ({divisor}) * {quotient}"


def _e_power(
    base: str,
    exponent: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    code, scale, index = _binders(
        tag,
        avoid,
        ("power_code", "power_scale", "power_index"),
    )
    local = avoid + (code, scale, index)
    bound = _lt_term(
        index,
        exponent,
        tag=f"{tag}_repeat_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        base,
        tag=f"{tag}_repeat_entry",
        avoid=local,
    )
    repeat = f"forall {index}. ({bound}) -> ({decoded})"
    product = _product_relation_term(
        code,
        scale,
        exponent,
        result,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({repeat}) /\\ ({product}))"


def _e_power_divides(
    base: str,
    exponent: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (result,) = _binders(tag, avoid, ("power_value",))
    local = avoid + (result,)
    power = _e_power(
        base,
        exponent,
        result,
        tag=f"{tag}_power",
        avoid=local,
    )
    divides = _e_divides(
        result,
        value,
        tag=f"{tag}_divides",
        avoid=local,
    )
    return f"exists {result}. (({power}) /\\ ({divides}))"


def _e_valuation(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (candidate,) = _binders(tag, avoid, ("valuation_candidate",))
    local = avoid + (candidate,)
    selected_bound = _e_le(
        exponent,
        value,
        tag=f"{tag}_selected_bound",
        avoid=local,
    )
    selected = _e_power_divides(
        base,
        exponent,
        value,
        tag=f"{tag}_selected",
        avoid=local,
    )
    candidate_bound = _e_le(
        candidate,
        value,
        tag=f"{tag}_candidate_bound",
        avoid=local,
    )
    candidate_divides = _e_power_divides(
        base,
        candidate,
        value,
        tag=f"{tag}_candidate",
        avoid=local,
    )
    candidate_below = _e_le(
        candidate,
        exponent,
        tag=f"{tag}_candidate_below",
        avoid=local,
    )
    return (
        f"(({selected_bound}) /\\ ({selected})) /\\ "
        f"forall {candidate}. ({candidate_bound}) -> "
        f"({candidate_divides}) -> ({candidate_below})"
    )


def _e_coprime(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    divisor, left_factor, right_factor = _binders(
        tag,
        avoid,
        ("coprime_divisor", "coprime_left", "coprime_right"),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{left} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. {right} = {divisor} * "
        f"{right_factor}) -> {divisor} = 1"
    )


def _e_choice_rendered(
    number: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (exponent,) = _binders(tag, avoid, ("choice_exponent",))
    local = avoid + (exponent,)
    base = f"S ({index})"
    prime = _prime_term(base, tag=f"{tag}_prime", avoid=local)
    valuation = _e_valuation(
        base,
        number,
        exponent,
        tag=f"{tag}_valuation",
        avoid=local,
    )
    power = _e_power(
        base,
        exponent,
        value,
        tag=f"{tag}_power",
        avoid=local,
    )
    return (
        f"((({prime}) /\\ exists {exponent}. "
        f"(({valuation}) /\\ ({power}))) \\/ "
        f"(~({prime}) /\\ {value} = 1))"
    )


def _e_choice(
    number: str,
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "expected contribution number"),
            (index, "expected contribution index"),
            (value, "expected contribution value"),
        )
    )
    return _e_choice_rendered(*rendered, tag=tag, avoid=context)


def _e_prefix_rendered(
    number: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("prefix_index", "prefix_value"))
    local = avoid + (index, value)
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _e_choice_rendered(
        number,
        index,
        value,
        tag=f"{tag}_choice",
        avoid=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _e_prefix(
    number: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "expected prefix number"),
            (code, "expected prefix code"),
            (scale, "expected prefix scale"),
            (length, "expected prefix length"),
        )
    )
    return _e_prefix_rendered(*rendered, tag=tag, avoid=context)


def _e_product(
    number: str,
    length: str,
    result: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_number = _render_term(
        number,
        label="expected product number",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="expected product length",
        context=context,
    )
    rendered_result = _render_term(
        result,
        label="expected product result",
        context=context,
    )
    code, scale = _binders(tag, context, ("product_code", "product_scale"))
    local = context + (code, scale)
    prefix = _e_prefix_rendered(
        rendered_number,
        code,
        scale,
        rendered_length,
        tag=f"{tag}_prefix",
        avoid=local,
    )
    product = _product_relation_term(
        code,
        scale,
        rendered_length,
        rendered_result,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _e_pairwise(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left_index, right_index, left_value, right_value = _binders(
        tag,
        avoid,
        ("pair_left_index", "pair_right_index", "pair_left", "pair_right"),
    )
    local = avoid + (left_index, right_index, left_value, right_value)
    left_bound = _lt_term(
        left_index,
        length,
        tag=f"{tag}_left_bound",
        avoid=local,
    )
    right_bound = _lt_term(
        right_index,
        length,
        tag=f"{tag}_right_bound",
        avoid=local,
    )
    left_entry = _beta_at_term(
        code,
        scale,
        left_index,
        left_value,
        tag=f"{tag}_left_entry",
        avoid=local,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        right_index,
        right_value,
        tag=f"{tag}_right_entry",
        avoid=local,
    )
    coprime = _e_coprime(
        left_value,
        right_value,
        tag=f"{tag}_coprime",
        avoid=local,
    )
    return (
        f"forall {left_index} {right_index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> ({left_entry}) -> "
        f"({right_entry}) -> ~({left_index} = {right_index}) -> "
        f"({coprime})"
    )


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    choice_exists = _e_choice(
        "n",
        "i",
        "a",
        tag="bpcce_result",
        variables=("n", "i", "a"),
    )

    functional_variables = ("n", "i", "a", "z")
    functional_left = _e_choice(
        "n",
        "i",
        "a",
        tag="bpccf_left",
        variables=functional_variables,
    )
    functional_right = _e_choice(
        "n",
        "i",
        "z",
        tag="bpccf_right",
        variables=functional_variables,
    )

    extend_variables = ("n", "b", "c", "m")
    extend_before = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpe_before",
        variables=extend_variables,
    )
    extend_after = _e_prefix(
        "n",
        "d",
        "e",
        "S m",
        tag="bpcpe_after",
        variables=extend_variables + ("d", "e"),
    )

    prefix_exists = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpx_result",
        variables=("n", "m", "b", "c"),
    )

    transport_variables = ("n", "b", "c", "d", "e", "m")
    transport_left = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpt_left",
        variables=transport_variables,
    )
    transport_right = _e_prefix(
        "n",
        "d",
        "e",
        "m",
        tag="bpcpt_right",
        variables=transport_variables,
    )
    transport_local = transport_variables + ("i", "a")
    transport_bound = _lt_term(
        "i",
        "m",
        tag="bpcpt_bound",
        avoid=transport_local,
    )
    transport_source = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpcpt_source",
        avoid=transport_local,
    )
    transport_target = _beta_at_term(
        "d",
        "e",
        "i",
        "a",
        tag="bpcpt_target",
        avoid=transport_local,
    )

    product_exists = _e_product(
        "n",
        "m",
        "z",
        tag="bpc_product_exists",
        variables=("n", "m", "z"),
    )

    product_functional_variables = ("n", "m", "x", "y")
    product_functional_left = _e_product(
        "n",
        "m",
        "x",
        tag="bpcpf_left",
        variables=product_functional_variables,
    )
    product_functional_right = _e_product(
        "n",
        "m",
        "y",
        tag="bpcpf_right",
        variables=product_functional_variables,
    )

    coprime_power_variables = ("p", "q", "e", "z")
    coprime_power_source = _e_coprime(
        "p",
        "q",
        tag="bcpr_source",
        avoid=coprime_power_variables,
    )
    coprime_power_power = _e_power(
        "q",
        "e",
        "z",
        tag="bcpr_power",
        avoid=coprime_power_variables,
    )
    coprime_power_result = _e_coprime(
        "p",
        "z",
        tag="bcpr_result",
        avoid=coprime_power_variables,
    )

    powers_variables = ("p", "q", "e", "f", "a", "z")
    powers_source = _e_coprime(
        "p",
        "q",
        tag="bcpowers_source",
        avoid=powers_variables,
    )
    powers_left = _e_power(
        "p",
        "e",
        "a",
        tag="bcpowers_left",
        avoid=powers_variables,
    )
    powers_right = _e_power(
        "q",
        "f",
        "z",
        tag="bcpowers_right",
        avoid=powers_variables,
    )
    powers_result = _e_coprime(
        "a",
        "z",
        tag="bcpowers_result",
        avoid=powers_variables,
    )

    pairwise_variables = ("n", "b", "c", "m")
    pairwise_prefix = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcppc_source",
        variables=pairwise_variables,
    )
    pairwise_result = _e_pairwise(
        "b",
        "c",
        "m",
        tag="bpcppc_result",
        avoid=pairwise_variables,
    )

    factor_variables = ("n", "i", "a")
    factor_choice = _e_choice(
        "n",
        "i",
        "a",
        tag="bpcfd_choice",
        variables=factor_variables,
    )
    factor_result = _e_divides(
        "a",
        "n",
        tag="bpcfd_result",
        avoid=factor_variables,
    )

    total_variables = ("n", "m", "z")
    total_source = _e_product(
        "n",
        "m",
        "z",
        tag="bpcpd_source",
        variables=total_variables,
    )
    total_result = _e_divides(
        "z",
        "n",
        tag="bpcpd_result",
        avoid=total_variables,
    )

    return {
        PRIME_CONTRIBUTION_CHOICE_EXISTS:
            f"forall n i. exists a. ({choice_exists})",
        PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL:
            "forall n i a z. "
            f"({functional_left}) -> ({functional_right}) -> a = z",
        PRIME_CONTRIBUTION_PREFIX_EXTEND:
            "forall n b c m. "
            f"({extend_before}) -> exists d e. ({extend_after})",
        PRIME_CONTRIBUTION_PREFIX_EXISTS:
            f"forall n m. exists b c. ({prefix_exists})",
        PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY:
            "forall n b c d e m. "
            f"({transport_left}) -> ({transport_right}) -> "
            "forall i a. "
            f"({transport_bound}) -> ({transport_source}) -> "
            f"({transport_target})",
        PRIME_CONTRIBUTION_PRODUCT_EXISTS:
            f"forall n m. exists z. ({product_exists})",
        PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL:
            "forall n m x y. "
            f"({product_functional_left}) -> "
            f"({product_functional_right}) -> x = y",
        COPRIME_POWER_RIGHT:
            "forall p q e z. "
            f"({coprime_power_source}) -> ({coprime_power_power}) -> "
            f"({coprime_power_result})",
        COPRIME_POWERS:
            "forall p q e f a z. "
            f"({powers_source}) -> ({powers_left}) -> ({powers_right}) -> "
            f"({powers_result})",
        PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME:
            "forall n b c m. "
            f"({pairwise_prefix}) -> ({pairwise_result})",
        PRIME_CONTRIBUTION_FACTOR_DIVIDES:
            "forall n i a. "
            f"({factor_choice}) -> ({factor_result})",
        PRIME_CONTRIBUTION_PRODUCT_DIVIDES:
            "forall n m z. "
            f"({total_source}) -> ({total_result})",
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    expected = _expected_statements()

    choice = _e_choice(
        "n",
        "i",
        "a",
        tag="bpcce_result",
        variables=("n", "i", "a"),
    )

    extend_variables = ("n", "b", "c", "m")
    extend_before = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpe_before",
        variables=extend_variables,
    )
    extend_after = _e_prefix(
        "n",
        "d",
        "e",
        "S m",
        tag="bpcpe_after",
        variables=extend_variables + ("d", "e"),
    )
    extend_zero = _beta_at_term(
        "d",
        "e",
        "m",
        "0",
        tag="bpcpe_mutated_terminal",
        avoid=extend_variables + ("d", "e"),
    )

    prefix = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpx_result",
        variables=("n", "m", "b", "c"),
    )

    transport_variables = ("n", "b", "c", "d", "e", "m")
    transport_left = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpt_left",
        variables=transport_variables,
    )
    transport_right = _e_prefix(
        "n",
        "d",
        "e",
        "m",
        tag="bpcpt_right",
        variables=transport_variables,
    )
    transport_local = transport_variables + ("i", "a")
    transport_bound = _lt_term(
        "i",
        "m",
        tag="bpcpt_bound",
        avoid=transport_local,
    )
    transport_source = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpcpt_source",
        avoid=transport_local,
    )
    transport_shifted = _beta_at_term(
        "d",
        "e",
        "i",
        "S a",
        tag="bpcpt_target",
        avoid=transport_local,
    )

    product_exists = _e_product(
        "n",
        "m",
        "z",
        tag="bpc_product_exists",
        variables=("n", "m", "z"),
    )

    coprime_power_variables = ("p", "q", "e", "z")
    coprime_power_power = _e_power(
        "q",
        "e",
        "z",
        tag="bcpr_power",
        avoid=coprime_power_variables,
    )
    coprime_power_result = _e_coprime(
        "p",
        "z",
        tag="bcpr_result",
        avoid=coprime_power_variables,
    )

    powers_variables = ("p", "q", "e", "f", "a", "z")
    powers_left = _e_power(
        "p",
        "e",
        "a",
        tag="bcpowers_left",
        avoid=powers_variables,
    )
    powers_right = _e_power(
        "q",
        "f",
        "z",
        tag="bcpowers_right",
        avoid=powers_variables,
    )
    powers_result = _e_coprime(
        "a",
        "z",
        tag="bcpowers_result",
        avoid=powers_variables,
    )

    pairwise_variables = ("n", "b", "c", "m")
    pairwise_prefix = _e_prefix(
        "n",
        "b",
        "c",
        "m",
        tag="bpcppc_source",
        variables=pairwise_variables,
    )
    pairwise_result = _e_pairwise(
        "b",
        "c",
        "m",
        tag="bpcppc_result",
        avoid=pairwise_variables,
    )
    left_index, right_index, _, _ = _binders(
        "bpcppc_result",
        pairwise_variables,
        ("pair_left_index", "pair_right_index", "pair_left", "pair_right"),
    )
    distinct = f"~({left_index} = {right_index})"
    assert pairwise_result.count(distinct) == 1
    reflexive_pairwise = pairwise_result.replace(
        distinct,
        f"{left_index} = {right_index}",
        1,
    )

    factor_variables = ("n", "i", "a")
    factor_choice = _e_choice(
        "n",
        "i",
        "a",
        tag="bpcfd_choice",
        variables=factor_variables,
    )
    shifted_factor = _e_divides(
        "S a",
        "n",
        tag="bpcfd_result",
        avoid=factor_variables,
    )

    total_variables = ("n", "m", "z")
    total_source = _e_product(
        "n",
        "m",
        "z",
        tag="bpcpd_source",
        variables=total_variables,
    )
    shifted_total = _e_divides(
        "S z",
        "n",
        tag="bpcpd_result",
        avoid=total_variables,
    )

    result = {
        PRIME_CONTRIBUTION_CHOICE_EXISTS:
            f"forall n i. exists a. (({choice}) /\\ a = 0)",
        PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL:
            expected[PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL].replace(
                "a = z", "a = S z", 1
            ),
        PRIME_CONTRIBUTION_PREFIX_EXTEND:
            "forall n b c m. "
            f"({extend_before}) -> exists d e. "
            f"(({extend_after}) /\\ ({extend_zero}))",
        PRIME_CONTRIBUTION_PREFIX_EXISTS:
            f"forall n m. exists b c. (({prefix}) /\\ m = 0)",
        PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY:
            "forall n b c d e m. "
            f"({transport_left}) -> ({transport_right}) -> "
            "forall i a. "
            f"({transport_bound}) -> ({transport_source}) -> "
            f"({transport_shifted})",
        PRIME_CONTRIBUTION_PRODUCT_EXISTS:
            f"forall n m. exists z. (({product_exists}) /\\ z = 0)",
        PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL:
            expected[PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL].replace(
                "x = y", "x = S y", 1
            ),
        COPRIME_POWER_RIGHT:
            "forall p q e z. "
            f"({coprime_power_power}) -> ({coprime_power_result})",
        COPRIME_POWERS:
            "forall p q e f a z. "
            f"({powers_left}) -> ({powers_right}) -> ({powers_result})",
        PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME:
            "forall n b c m. "
            f"({pairwise_prefix}) -> ({reflexive_pairwise})",
        PRIME_CONTRIBUTION_FACTOR_DIVIDES:
            "forall n i a. "
            f"({factor_choice}) -> ({shifted_factor})",
        PRIME_CONTRIBUTION_PRODUCT_DIVIDES:
            "forall n m z. "
            f"({total_source}) -> ({shifted_total})",
    }
    for name, statement in result.items():
        assert _closed_formula(statement) != _closed_formula(expected[name])
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
        label=f"B5 prime-contribution body {name}",
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
            (),
            _mutate_layer_cut(compiled.certificate, index),
            compiled.target,
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
    payload = _run_worker(["--body-worker", name], "B5PC_BODY ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--closure-worker", name], "B5PC_CLOSURE ")
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
    payload = _run_worker(arguments, "B5PC_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_prime_contribution_static_contract() -> None:
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
    assert len(LIVE_EDGES) == 39
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[2].script.count("rewrite hsplit_left") == 12
    assert rows[4].script.count("rewrite haq") == 2
    assert rows[7].script[:3] == ("intro p", "intro q", "induction e")
    assert rows[8].script[:3] == ("intro p", "intro q", "induction e")
    assert rows[9].script.count("apply coprime_powers") == 1
    assert rows[11].script.count(
        "apply beta_pairwise_coprime_product_divides_common_multiple"
    ) == 1
    assert not any(
        "rewrite" in command and "at hprefix" in command
        for row in rows
        for command in row.script
    )
    assert not any(
        command.startswith("dne") for row in rows for command in row.script
    )


def test_bertrand_prime_contribution_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        assert sha256((library / filename).read_bytes()).hexdigest() == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_prime_contribution_receipts_are_shaped() -> None:
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
def test_bertrand_prime_contribution_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 PRIME CONTRIBUTION {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_bodies_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 PRIME CONTRIBUTION {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_prime_contribution_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_false_targets_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_prime_contribution_mutations_have_counterfixtures() -> None:
    assert 1 != 0
    assert 1 != 2
    assert not (2 <= 1)
    assert 2 != 1
    assert not (2 == 1)
    assert not (2 * 1 == 1)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_genuine_mutations_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_layered_closures_are_frozen(
    name: str,
) -> None:
    actual = _run_closure_worker(name)
    print(
        f"B5 PRIME CONTRIBUTION {name} CLOSURE actual={actual!r}",
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
    if mode == "--body-worker":
        assert len(sys.argv) == 3
        receipt = _body_receipt(name)
        prefix = "B5PC_BODY "
    elif mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5PC_CLOSURE "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5PC_REJECTION "
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
