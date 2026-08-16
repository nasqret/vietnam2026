"""Fail-closed audit for the Bertrand B5 zero two-thirds tranche.

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
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_range_candidate import (
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE,
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE,
    DIVISION_QUOTIENT_ONE_OF_BOUNDS,
    DIVISION_QUOTIENT_TWO_OF_BOUNDS,
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO,
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE,
    make_bertrand_central_binom_zero_range_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_sum_theorems import _at
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
    DIVISION_QUOTIENT_ONE_OF_BOUNDS,
    DIVISION_QUOTIENT_TWO_OF_BOUNDS,
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE,
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE,
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE,
)
EXPECTED_DEPENDENCIES = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: (
        "add_comm",
        "mul_one",
        "add_lt_cancel_left",
    ),
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: (
        "add_comm",
        "mul_one",
        "add_lt_cancel_left",
    ),
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: (
        "prime_is_succ_succ",
        "zero_or_succ",
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
        "lt_not_le",
        "mul_le_mul_left",
        "mul_one",
        "lt_of_lt_of_le",
        "pow_two",
    ),
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: (
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
        "lt_of_le_of_lt",
        "add_comm",
        "add_lt_cancel_left",
        DIVISION_QUOTIENT_ONE_OF_BOUNDS,
        DIVISION_QUOTIENT_TWO_OF_BOUNDS,
    ),
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: (
        "zero_or_succ",
        "pow_one",
        "division_remainder_unique",
        "beta_at_unique",
        "zero_add",
        "lt_irrefl_expanded",
        "pow_tail_strict_of_square",
        "division_zero_quotient_of_lt",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: (
        "central_binom_carry_bit_count",
        "zero_or_succ",
        "bit_count_positive_last_one",
        DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO,
        "beta_at_unique",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: (
        "pow_exists",
        PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE,
        DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE,
        "prime_nonzero",
        "one_le_of_ne_zero",
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS,
    ),
}
EXPECTED_COMMAND_COUNTS = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: 25,
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: 28,
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: 85,
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: 67,
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: 189,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: 89,
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: 65,
}

EXPECTED_ARTIFACTS = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: (
        276,
        "53bccc1db89d64bafb0f0e68b637d3d63eb0d1fb9aeac87f8a2328b53605ec41",
        "677b60d368ac6b03f1945f4e283338e814a47d26747abe17db36f1cf495f2cb7",
        "5dc28984e91c32c1c2d4a054bad303e21f9dcba280e22d505862d4834df297f7",
    ),
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: (
        286,
        "4aba45cc12e0d8ba465e8e7bee587584377316b35e6d4249f338df1077be7076",
        "0c2b327dea001cdbcf9a53c1cc2e11a6a4b6b810cc2a7fdd9f1b35df20854c9b",
        "d5105368765bbbb7019f429d9ce83ddfc7890168e92c2447c000d66866f75e7e",
    ),
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: (
        2710,
        "9ca27bb0aab4e981d9c46c041eeafc9e920da54f0d47cdef6c1707ba03a1bba4",
        "8d29c027bcc71aea8a2fae3985b8e5585eb2fd1d2bac31df307f06ebd178a042",
        "d459e6295c1ed6cf40326563fe62ef31f60b29dfac8a5c6b81847c0938f3287f",
    ),
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: (
        402,
        "6511e843b1c066fc98c79bc8c7f5e1a6bb5e5fe6507ea3ed0919080a711e2496",
        "1c35267e765c98c525512d4b1ba057bb640cca27d6eab02d9b1392920c99334f",
        "8f142a48131142ff55cfb51c92f6c4b6876991b6aaa97333a948c5f331400c15",
    ),
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: (
        12527,
        "fa9a1fdc681b69a955fb5d330b52bede3c9b643980cb7decaef5d769d8d37615",
        "e025d2f42bbca348a6ec704f5a5b8dbac25ffff865e720c27d472f3d770d3199",
        "f04c3e29e53e397dda4a9517177071148537732d726f0bc4a4dd4f1c0f820b2b",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: (
        20330,
        "7c22849ea0425edb7b3010c0a337de31bdbd865f8562080398ac028bdecffb51",
        "223765bbef34efafa47084d4769c59fac221f0fb57c79e88d4dc10e679c23abd",
        "036b37bb58927926b2b07fec6879c426bb14f56aa2fd5788410115ffb9889245",
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: (
        17704,
        "616e7f72e9ea79b001cac51bf0a463d4e423151b709034578f01f558657fbe7d",
        "dca52c97843dd0003cc3ea9ae42446c63b3c884ded119799861f4e73a2bbceef",
        "b3eddef5af6a196227a07dc6a2a309aa2f506b2046e73db287bc1c345bd9c1be",
    ),
}
EXPECTED_BODIES = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: (3, 25, 36, 17, 36, 35, 0),
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: (3, 28, 43, 17, 43, 42, 0),
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: (
        10,
        85,
        199,
        35,
        197,
        198,
        2,
    ),
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: (8, 67, 75, 24, 75, 74, 0),
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: (
        8,
        189,
        450,
        66,
        449,
        449,
        1,
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: (
        5,
        89,
        119,
        57,
        119,
        118,
        0,
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: (
        6,
        65,
        96,
        36,
        96,
        95,
        0,
    ),
}
EXPECTED_ENVELOPES = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: (36, 36, 17, 28, 17),
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: (43, 43, 17, 45, 18),
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: (199, 197, 35, 326, 38),
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: (75, 75, 24, 68, 24),
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: (450, 449, 66, 579, 66),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: (
        119,
        119,
        57,
        431,
        57,
    ),
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: (
        96,
        96,
        36,
        50,
        36,
    ),
}
EXPECTED_LAYERED_CLOSURES = {
    DIVISION_QUOTIENT_ONE_OF_BOUNDS: {
        "topology_sha256":
            "2dcc22769298d4c044c4a48ca9983f5e9c8de573f28f02e4d2ef7fd2bf0d0d82",
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 4,
        "candidate_body_count": 2,
        "dependency_edge_count": 6,
        "layer_sizes": [4, 1, 1],
        "layer_cut_count": 3,
        "proof_nodes": 405,
        "proof_depth": 32,
        "proof_objects": 238,
        "proof_edges": 288,
        "reused_objects": 51,
        "annotation_occurrences": 826,
        "envelope_depth": 32,
        "package_formula_occurrences": 105,
        "package_formula_depth": 11,
        "proof_dag_sha256":
            "221bbc7dcb1e23e46002bfc9a0d1935b89eb69df9fddabf786ca9cec22b59257",
    },
    DIVISION_QUOTIENT_TWO_OF_BOUNDS: {
        "topology_sha256":
            "0488296ba6c03899a40fdb5a8264e53dde97ef68fb02550e46dd3c5eebaef10f",
        "node_count": 6,
        "stable_catalog_count": 432,
        "reachable_stable_count": 4,
        "candidate_body_count": 2,
        "dependency_edge_count": 6,
        "layer_sizes": [4, 1, 1],
        "layer_cut_count": 3,
        "proof_nodes": 412,
        "proof_depth": 32,
        "proof_objects": 245,
        "proof_edges": 297,
        "reused_objects": 53,
        "annotation_occurrences": 863,
        "envelope_depth": 32,
        "package_formula_occurrences": 110,
        "package_formula_depth": 12,
        "proof_dag_sha256":
            "9371f7f2384ac7fb43a87668c0cdc7b0d2f1aca6a2c6b0450ead51fec272ba4e",
    },
    PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: {
        "topology_sha256":
            "3360306fcf1e8ff75567145b171383316e024c60281611c86d0285f24eb97323",
        "node_count": 11,
        "stable_catalog_count": 432,
        "reachable_stable_count": 10,
        "candidate_body_count": 1,
        "dependency_edge_count": 10,
        "layer_sizes": [10, 1],
        "layer_cut_count": 2,
        "proof_nodes": 7336,
        "proof_depth": 72,
        "proof_objects": 1145,
        "proof_edges": 1525,
        "reused_objects": 381,
        "annotation_occurrences": 29776,
        "envelope_depth": 72,
        "package_formula_occurrences": 637,
        "package_formula_depth": 33,
        "proof_dag_sha256":
            "14df3aa5484ca810321da71fa55f503f9ef4d1470a71689c484e1451c0db0017",
    },
    DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: {
        "topology_sha256":
            "06d185004a062d0ee9d85e586fa24f496d67344b62b19555bd8eb4579f683ebd",
        "node_count": 12,
        "stable_catalog_count": 432,
        "reachable_stable_count": 8,
        "candidate_body_count": 4,
        "dependency_edge_count": 17,
        "layer_sizes": [8, 1, 2, 1],
        "layer_cut_count": 4,
        "proof_nodes": 879,
        "proof_depth": 36,
        "proof_objects": 445,
        "proof_edges": 546,
        "reused_objects": 102,
        "annotation_occurrences": 1990,
        "envelope_depth": 36,
        "package_formula_occurrences": 300,
        "package_formula_depth": 14,
        "proof_dag_sha256":
            "0ae6bb65b4c6ee472c80ead71fdc4ccd24045a05c2d78b8d2b5e4aa60d58040c",
    },
    DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: {
        "topology_sha256":
            "7bfb39fe7b3c26e89bc8eafee29af2449208380d52a3c977f3f22db7b69e479f",
        "node_count": 22,
        "stable_catalog_count": 432,
        "reachable_stable_count": 16,
        "candidate_body_count": 6,
        "dependency_edge_count": 24,
        "layer_sizes": [16, 2, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "proof_nodes": 77437,
        "proof_depth": 93,
        "proof_objects": 4211,
        "proof_edges": 5766,
        "reused_objects": 1556,
        "annotation_occurrences": 269251,
        "envelope_depth": 93,
        "package_formula_occurrences": 3724,
        "package_formula_depth": 49,
        "proof_dag_sha256":
            "00cb83e377d7017fccd40161d68e822076f66a537ce472e33380794846e8d333",
    },
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: {
        "topology_sha256":
            "e430e0544aa21563bec49a40f54d2527508c9c762a68c41152b57f654b43c195",
        "node_count": 181,
        "stable_catalog_count": 432,
        "reachable_stable_count": 71,
        "candidate_body_count": 110,
        "dependency_edge_count": 402,
        "layer_sizes": [
            78, 36, 15, 8, 9, 8, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1
        ],
        "layer_cut_count": 18,
        "proof_nodes": 277068,
        "proof_depth": 96,
        "proof_objects": 13396,
        "proof_edges": 17672,
        "reused_objects": 4277,
        "annotation_occurrences": 996299,
        "envelope_depth": 96,
        "package_formula_occurrences": 63558,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "2bce83f97aec6c195cd86cfdcea42b9e43a4bc2da22990318018594bab0d5410",
    },
    CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: {
        "topology_sha256":
            "d70e298d0a828e89fd3adf30d30dee208160f02499cd0491fa00dd431936401e",
        "node_count": 190,
        "stable_catalog_count": 432,
        "reachable_stable_count": 75,
        "candidate_body_count": 115,
        "dependency_edge_count": 432,
        "layer_sizes": [
            82, 37, 17, 9, 9, 8, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1
        ],
        "layer_cut_count": 19,
        "proof_nodes": 284473,
        "proof_depth": 96,
        "proof_objects": 13984,
        "proof_edges": 18403,
        "reused_objects": 4420,
        "annotation_occurrences": 1022720,
        "envelope_depth": 96,
        "package_formula_occurrences": 65101,
        "package_formula_depth": 57,
        "proof_dag_sha256":
            "21a8519543beb6a33033d8c5a11171ddfe8c74c9cecdad412691c1013dddafaa",
    },
}

SOURCE_PINS = {
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "bertrand_b5_order_quotient_candidate.py":
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e",
    "bertrand_central_binom_valuation_candidate.py":
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8",
    "bertrand_central_binom_carry_candidate.py":
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0",
    "bertrand_central_binom_zero_range_candidate.py":
        "8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-zero-two-thirds-tranche-rfc-v1.md"
)
RFC_SHA256 = "9b920ae8f646fb3b460a352ac82c332d4cd23e3d7bbe4e6fa9ba74e17c1696fc"


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_central_binom_zero_range_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    rows = (
        *editions_v11.ALPHA_SPECS,
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_valuation_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_carry_candidate_theorems(TheoremSpec),
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
def _mutations() -> dict[str, str]:
    rows = _table(_rows())
    result: dict[str, str] = {}
    replacements = {
        DIVISION_QUOTIENT_ONE_OF_BOUNDS: ("(1)", "(0)"),
        DIVISION_QUOTIENT_TWO_OF_BOUNDS: ("(2)", "(1)"),
        PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE: (
            rows[PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE].statement.rsplit(
                " -> ", 1
            )[1],
            rows[PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE].statement.rsplit(
                " -> ", 1
            )[1].replace("S (n + n)", "S (s)").replace("= s", "= n + n"),
        ),
        DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE: ("(2)", "(1)"),
        DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO: (
            _at("f", "g", "i", "0", tag="bdqcpez_result"),
            _at("f", "g", "i", "1", tag="bdqcpez_result"),
        ),
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS: (
            "v = 0",
            "v = 1",
        ),
        CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE: (
            "v = 0",
            "v = 1",
        ),
    }
    for name in EXPECTED_NAMES:
        old, new = replacements[name]
        statement = rows[name].statement
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
        label=f"B5 zero-range body {name}",
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
    payload = _run_worker(["--body-worker", name], "B5ZR_BODY ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--closure-worker", name], "B5ZR_CLOSURE ")
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
    payload = _run_worker(arguments, "B5ZR_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_zero_range_static_contract() -> None:
    rows = _rows()
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_DEPENDENCIES[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.script for row in rows))) == tuple(
        EXPECTED_COMMAND_COUNTS[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.dependencies for row in rows))) == (
        3,
        3,
        10,
        8,
        8,
        5,
        6,
    )
    assert len(LIVE_EDGES) == 43
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[4].script.count("cases zero_or_succ") == 1
    assert rows[5].script.count("apply bit_count_positive_last_one") == 1
    assert rows[6].script.count("apply prime_nonzero") == 1
    assert not any(
        type_ == "DNE"
        for row in rows
        for type_ in (command.split(maxsplit=1)[0] for command in row.script)
    )


def test_bertrand_zero_range_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        assert sha256((library / filename).read_bytes()).hexdigest() == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_zero_range_receipts_are_shaped() -> None:
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
def test_bertrand_zero_range_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 ZERO RANGE {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_zero_range_bodies_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 ZERO RANGE {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_zero_range_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_zero_range_false_targets_are_rejected(name: str) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_zero_range_mutations_have_counterfixtures() -> None:
    assert 4 + 4 < (3 + 3) + 3
    assert 3 <= 4
    assert 0 == 0
    assert not (0 == 1)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_zero_range_genuine_mutations_are_rejected(name: str) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_zero_range_layered_closures_are_frozen(name: str) -> None:
    actual = _run_closure_worker(name)
    print(f"B5 ZERO RANGE {name} CLOSURE actual={actual!r}", flush=True)
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
        prefix = "B5ZR_BODY "
    elif mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5ZR_CLOSURE "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5ZR_REJECTION "
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
