"""Fail-closed audit for the Bertrand B5 central upper bound."""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v11,
    editions_v11,
    finite_fold_surface,
    theorems as stable_module,
)
from peano_lab.library import bertrand_b5_central_upper_candidate as module
from peano_lab.library.bertrand_b5_central_upper_candidate import (
    BETA_PRODUCT_ALL_ONE_EXACT,
    CENTRAL_BINOM_FACTORIZATION_SMALL,
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME,
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
    make_bertrand_b5_central_upper_candidate_theorems,
)
from peano_lab.library.bertrand_b5_contribution_split_candidate import (
    make_bertrand_b5_contribution_split_candidate_theorems,
)
from peano_lab.library.bertrand_b5_order_quotient_candidate import (
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_b5_range_boundaries_candidate import (
    make_bertrand_b5_range_boundaries_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_factor_ranges_candidate import (
    make_bertrand_central_binom_factor_ranges_candidate_theorems,
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
from peano_lab.library.bertrand_prime_contribution_candidate import (
    make_bertrand_prime_contribution_candidate_theorems,
)
from peano_lab.library.bertrand_prime_contribution_complete_candidate import (
    make_bertrand_prime_contribution_complete_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_product_order_candidate import (
    make_finite_product_order_candidate_theorems,
)
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
    BETA_PRODUCT_ALL_ONE_EXACT,
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
    CENTRAL_BINOM_FACTORIZATION_SMALL,
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME,
)
EXPECTED_DEPENDENCIES = {
    BETA_PRODUCT_ALL_ONE_EXACT: (
        "beta_product_zero",
        "beta_product_succ_decompose",
        "le_succ",
        "le_refl",
        "mul_one",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE: (
        "lt_not_le",
        "lt_to_le",
        "le_trans",
        "le_add_right",
        "no_bertrand_central_contribution_choice_ranges",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR: (
        "lt_not_le",
        "le_refl",
        "no_bertrand_central_contribution_choice_ranges",
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE: (
        "le_trans",
        "lt_not_le",
        "floor_sqrt_le_third_quotient",
        "no_bertrand_central_contribution_choice_ranges",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER: (
        "beta_at_unique",
        "beta_product_uniform_le_pow",
        NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL: (
        "add_comm",
        "add_le_add_left",
        "beta_at_unique",
        "beta_product_pointwise_le",
        NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW: (
        "le_trans",
        "le_mul_of_one_le_left",
        "primorial_exists",
        "primorial_index_eq_transport",
        "primorial_positive",
        "primorial_prefix_interval_split",
        "primorial_le_four_pow",
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE: (
        "add_comm",
        "beta_at_unique",
        BETA_PRODUCT_ALL_ONE_EXACT,
        NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
    ),
    CENTRAL_BINOM_FACTORIZATION_SMALL: (
        "mul_one",
        "prime_contribution_product_length_eq_transport",
        "prime_contribution_prefix_interval_split",
        NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
    ),
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME: (
        "mul_le_mul",
        "floor_third_double_gap_package",
        "central_binom_prime_contribution_product_exists",
        NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
        CENTRAL_BINOM_FACTORIZATION_SMALL,
    ),
}
EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (5, 5, 3, 4, 3, 5, 8, 4, 4, 6), strict=True)
)
assert sum(EXPECTED_DIRECT_CUTS.values()) == 47

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    BETA_PRODUCT_ALL_ONE_EXACT: (
        2023,
        "99f1d8890732f1647b00147549962feea3d0ad39e2450af238d05451833fee1e",
        "43d5b4b41bd02c2135b5a8fcee9b0523ada68c2b2760abf8d9bc82804f8ac5d8",
        "c8cade79b817dbf80dd2c80e25cf4a091e0c0225d2d56ff087ecea2d08e1f0bb",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE: (
        24320,
        "af85d8737c384de4c5eac9dbdc78f2b54ebce4e1649fc18aaf402eb101d2b142",
        "deef91b33580198f2047f9df389fc748a74e3fd5b067ffb4bd68ceb1c0e705a6",
        "66319d1c32e272ed25a5235305ae400ae7604e38eb693493bc442f8e8540cf3d",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR: (
        24926,
        "222f7ce2989a6f4f9ade3c96970ce20dee8a6fd52653af68c97197ea615c1deb",
        "cf048c3587c81bf7d6e11a3ff6a3b120acbab5ed41c16de69d20d10f7aa34f52",
        "bbdff1e51648e1a35e7e9922fffed2970d3d1ec97b917354b5d60251b0bfa7b2",
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE: (
        24252,
        "f96fc54731b3bf20011541d11b963f01926c37f45f4ed33f477a955a68fa8f81",
        "5262e6fcae81d7fe7ce5353d314334c2763cfb2d035bfefa14040a71e9e6bf9a",
        "9ecd0dc1fbf1e5db441e92d80b74ad40455441ff7f75e261bf9e6884566f40e1",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER: (
        35208,
        "3a5436e1a2f9156dafa4d730c8d32dddf04144b589b260fdb9918c2026aebc7d",
        "13fccdfe312a51df1e1d81a23d89403535e68de0de5c67b9eda7ea65301a8efc",
        "8b9b21a85bc885b67d8a47f5ce5396acc4741b9613fb92c5fc6d1465a4936d98",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL: (
        39581,
        "90467a81e734b566a79d8bde0fedd5d88c15eb48e6a138a53a54958d9f99b235",
        "54b11cf3ad6e5dbc0b9e8038d41779d7742bc3a8e83c7a308550c1a4277e7c14",
        "93fa002b77b37522f279bb433cd6c4c1e54c628eaed83a4b49669a96a227951f",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW: (
        37831,
        "23395c47cf63832d7522e6b71b9173fc82bbdd9f793ed792fda76de2a40bc8ee",
        "8ef082778f829638d26cda91a28f8daed5f4644c6a1395b453d67645fefd86ca",
        "d2bf70bd4f8923b8576d58edaa7ceab088df1a9e2e462afa48fff161833e17a6",
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE: (
        33143,
        "e6576b0c2ddb9e04d3758532b4db649a5122e6d2eca2c7260eb2b4f65c9745cf",
        "1de234109cc4e2807917d1ccd69e0af764f39c2b0eb3a782d27c86325516392a",
        "48809d29c0955b86247311360ff908bf134cb344265453f4030ea708f85c4d4a",
    ),
    CENTRAL_BINOM_FACTORIZATION_SMALL: (
        74841,
        "2f10dc55c4b4b3f8d4e843902642d00fc7d863b50655b1709bce0416fff4bb29",
        "4b0c441ec9981e5eb4196748fde707d89262d8ff39e167da4d73c7d09fe9acf0",
        "54c7054e739d5ad50c844a527468e83aa6a8044ba24bfc60c5723fd9ce7261f2",
    ),
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME: (
        14800,
        "9737027fbe14bd7866fd65d6d11cf67cfb730e4e04c499a1305c30e45820355a",
        "e6de0135ec256fdf24cd92b77a25eac415e9bbb23784c3281f988e4cfe93c2fa",
        "402ca6aac689e50d4cecc00953aad9a38ff3c13ff6f5807c0ffe5f2a868e3dc6",
    ),
}
EXPECTED_BODIES: dict[str, tuple[int, ...] | None] = {
    BETA_PRODUCT_ALL_ONE_EXACT: (5, 55, 74, 30, 74, 73, 0),
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE:
        (5, 67, 96, 34, 96, 95, 0),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR:
        (3, 64, 100, 36, 100, 99, 0),
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE:
        (4, 63, 78, 33, 78, 77, 0),
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER:
        (3, 64, 80, 43, 80, 79, 0),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL:
        (5, 110, 136, 56, 136, 135, 0),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW:
        (8, 96, 121, 50, 121, 120, 0),
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE:
        (4, 68, 84, 42, 84, 83, 0),
    CENTRAL_BINOM_FACTORIZATION_SMALL: (4, 87, 103, 46, 103, 102, 0),
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME:
        (6, 100, 138, 45, 138, 137, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, ...] | None] = {
    BETA_PRODUCT_ALL_ONE_EXACT: (74, 74, 30, 230, 33),
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE:
        (96, 96, 34, 51, 34),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR:
        (100, 100, 36, 68, 36),
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE:
        (78, 78, 33, 21, 33),
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER:
        (80, 80, 43, 29, 43),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL:
        (136, 136, 56, 69, 56),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW:
        (121, 121, 50, 59, 50),
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE:
        (84, 84, 42, 28, 42),
    CENTRAL_BINOM_FACTORIZATION_SMALL: (103, 103, 46, 50, 46),
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME: (138, 138, 45, 49, 45),
}
EXPECTED_CLOSURES: dict[str, tuple[object, ...] | None] = {
    BETA_PRODUCT_ALL_ONE_EXACT: (
        2629,
        65,
        674,
        885,
        212,
        8577,
        65,
        "1ee842fd4a84e6c40cd2131ce8d8d298fdb670bb99af3343259addffedcf6a60",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE: (
        287548,
        95,
        15483,
        20243,
        4761,
        1055743,
        95,
        "3ea662e5127d146ab4f92dc4ae99c0bab3b6f522b7989b4e5c46352d20858a93",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR: (
        287535,
        95,
        15474,
        20241,
        4768,
        1057758,
        95,
        "df02edc77a9a85081c553d45e8695968d2eb8dd47dc165da64b0a34f3b2761d3",
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE: (
        288507,
        96,
        15976,
        20848,
        4873,
        1056903,
        96,
        "a84405a38867ea808130437952fa1f9b06e6bd97f37cbc30f9a7e94325d60a35",
    ),
    NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER: (
        291503,
        96,
        15752,
        20574,
        4823,
        1080203,
        96,
        "86edc5b621935c0018b653bcc22a21f8c769f20ab886f575cca81cd4cee2acde",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL: (
        290350,
        96,
        15746,
        20576,
        4831,
        1079714,
        96,
        "aed390ca565c4ed547202254d5a5c1e50d1843d009403fca25b10528aa35fe27",
    ),
    NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW: (
        371953,
        96,
        19902,
        25803,
        5902,
        1373274,
        96,
        "5cb8a3668a1b6e1a02d89b7aaa0bd78b4a310f5fd0b18dfb63aa47c6f93d6756",
    ),
    NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE: (
        291209,
        96,
        16184,
        21091,
        4908,
        1072802,
        96,
        "d373bac4cb1ef957f5191be7bba684161628ae1dbc0f8b44f0d05fc68c70f584",
    ),
    CENTRAL_BINOM_FACTORIZATION_SMALL: (
        354318,
        96,
        17068,
        22260,
        5193,
        1354950,
        96,
        "aa4de0f59887e337b0f6154ddebeb4ee6a2f5f6eb690d59f8a2a3cd846e70cc7",
    ),
    CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME: (
        385293,
        96,
        22578,
        29123,
        6546,
        1442517,
        96,
        "f294a58afc851e09a07efed56223643203b4fe5f4072ebd97e22cf70a3d3eac3",
    ),
}

SOURCE_PINS = {
    "theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "finite_fold_surface.py":
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "bertrand_prime_contribution_candidate.py":
        "fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33",
    "bertrand_central_binom_valuation_candidate.py":
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8",
    "bertrand_b5_order_quotient_candidate.py":
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e",
    "bertrand_central_binom_carry_candidate.py":
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0",
    "bertrand_central_binom_square_tail_candidate.py":
        "b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff",
    "bertrand_central_binom_zero_range_candidate.py":
        "8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e",
    "bertrand_central_binom_factor_ranges_candidate.py":
        "d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae",
    "bertrand_prime_contribution_complete_candidate.py":
        "7e07f6c8908170d4aa12a3d234efb7b3200bd40f854de577ef12485ddca2f67d",
    "bertrand_b5_range_boundaries_candidate.py":
        "767e574d2e93639e967b9cd497de83a80a266a051a7315990d0d9bd27613e95e",
    "finite_product_order_candidate.py":
        "4a502fe8e233c631305ebb644cec9e3c877e1830e0348995f8e6e481fff1b433",
    "bertrand_b5_contribution_split_candidate.py":
        "a5b1e955cdd903adc6ada446fbcdb56d620a8e89372e3c3b71183ec22cfe1b7b",
    "bertrand_b5_central_upper_candidate.py":
        "95b11876de61baa50ed1b7ff4debc2ce9afb52a35aeb2a83ff5920ca81ca77a7",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-central-upper-tranche-rfc-v1.md"
)
RFC_SHA256 = "c40e10fb041aa0fdccd07d830afde12c0d9ddac5431207abe91f85196f465b98"


SUPPORT_FACTORIES = (
    make_bertrand_prime_contribution_candidate_theorems,
    make_bertrand_central_binom_valuation_candidate_theorems,
    make_bertrand_b5_order_quotient_candidate_theorems,
    make_bertrand_central_binom_carry_candidate_theorems,
    make_bertrand_central_binom_square_tail_candidate_theorems,
    make_bertrand_central_binom_zero_range_candidate_theorems,
    make_bertrand_central_binom_factor_ranges_candidate_theorems,
    make_bertrand_prime_contribution_complete_candidate_theorems,
    make_bertrand_b5_range_boundaries_candidate_theorems,
    make_finite_product_order_candidate_theorems,
    make_bertrand_b5_contribution_split_candidate_theorems,
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b5_central_upper_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    result: dict[str, TheoremSpec] = {}
    for row in editions_v11.ALPHA_SPECS:
        if row.name in stable:
            assert stable[row.name] == row
        else:
            result[row.name] = row
    for factory in SUPPORT_FACTORIES:
        for row in factory(TheoremSpec):
            previous = result.get(row.name)
            if previous is not None:
                assert previous == row
            elif row.name not in stable:
                result[row.name] = row
    assert not set(EXPECTED_NAMES) & set(result)
    return result


def _row_core(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name)]
    return dict(_specs_by_name()) | _candidate_base() | _table(prefix)


def _row_candidates(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name) + 1]
    return _candidate_base() | _table(prefix)


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base() | _table(_rows())


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


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(_available()[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
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
        label=f"B5 central-upper body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    return {
        "body": [
            len(item.dependencies),
            len(item.script),
            nodes,
            depth,
            objects,
            edges,
            reused,
        ],
        "envelope": list(envelope),
    }


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


def _reject_each_layer_cut(proof: Proof, target: Formula) -> int:
    context: tuple[Formula, ...] = ()
    probe = proof
    count = 0
    bad_lemma = EqRefl(Zero())
    while type(probe) is Cut:
        assert probe.conclusion == target
        assert probe.proposition != Eq(Zero(), Zero())
        assert not check(context, replace(probe, lemma=bad_lemma), target)
        context = (probe.proposition,) + context
        probe = probe.body
        count += 1
    return count


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
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = LayeredReplayBundle(tuple(nodes), positions[name])
    interned = intern_layered_replay_bodies(raw, targets[name], limits=limits)
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
    assert not any(
        type(item) is DNE for item in _walk(compiled.certificate)
    )
    layer_cuts = _reject_each_layer_cut(
        compiled.certificate,
        compiled.target,
    )
    assert layer_cuts == len(compiled.layers)
    return {
        "topology_sha256": topology_sha256,
        "node_count": len(names),
        "candidate_body_count": candidate_count,
        "dependency_edge_count": sum(map(len, dependencies.values())),
        "layer_sizes": list(map(len, compiled.layers)),
        "layer_cut_count": layer_cuts,
        "closure": [
            compiled.proof_nodes,
            compiled.proof_depth,
            compiled.proof_objects,
            compiled.proof_edges,
            compiled.reused_objects,
            compiled.proof_annotation_occurrences,
            compiled.proof_envelope_depth,
            _proof_dag_sha256(compiled.certificate),
        ],
    }


def _run_worker(mode: str, name: str) -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    inherited_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        python_root
        if not inherited_path
        else python_root + os.pathsep + inherited_path
    )
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), mode, name],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=Path(__file__).resolve().parents[3],
    )
    assert completed.returncode == 0, (
        f"worker failed for {mode} {name}:\n"
        f"stdout={completed.stdout[-4000:]}\n"
        f"stderr={completed.stderr[-4000:]}"
    )
    prefix = "B5CU "
    lines = [line for line in completed.stdout.splitlines() if line.startswith(prefix)]
    assert len(lines) == 1, completed.stdout
    return json.loads(lines[0][len(prefix):])


def test_bertrand_b5_central_upper_contract_is_exact() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {row.name: row.dependencies for row in rows} == EXPECTED_DEPENDENCIES
    assert tuple(len(row.script) for row in rows) == (
        55, 67, 64, 63, 64, 110, 96, 68, 87, 100,
    )
    assert module.__all__ == [
        "make_bertrand_b5_central_upper_candidate_theorems"
    ]
    for row in rows:
        parsed, free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert parsed == _closed_formula(row.statement)
        assert len(row.dependencies) == EXPECTED_DIRECT_CUTS[row.name]
        assert not any(
            token in command
            for command in row.script
            for token in ("DNE", "classical", "sorry", "compact_arith")
        )
    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v11.ALPHA_ENTRIES}
    assert not set(EXPECTED_NAMES) & (stable | alpha)
    provider = "bertrand_b5_central_upper_candidate"
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        assert provider not in Path(authority.__file__).read_text()


def test_bertrand_b5_central_upper_sources_and_rfc_are_pinned() -> None:
    providers = (
        stable_module,
        finite_fold_surface,
        alpha_enrollment_v11,
        editions_v11,
    )
    library = Path(module.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        candidates = [path for path in library.glob(filename)]
        if filename in {Path(item.__file__).name for item in providers}:
            candidates = [
                Path(item.__file__)
                for item in providers
                if Path(item.__file__).name == filename
            ]
        assert len(candidates) == 1, filename
        assert sha256(candidates[0].read_bytes()).hexdigest() == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_central_upper_artifacts(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    print(f"B5 CENTRAL UPPER {name} ARTIFACT {actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_central_upper_bodies(name: str) -> None:
    receipt = _run_worker("--body-worker", name)
    body = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(f"B5 CENTRAL UPPER {name} BODY {body!r}", flush=True)
    print(f"B5 CENTRAL UPPER {name} ENVELOPE {envelope!r}", flush=True)
    assert EXPECTED_BODIES[name] is not None, body
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert body == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 47


def _mutations() -> dict[str, str]:
    rows = _table(_rows())

    def relaxed(
        name: str,
        *,
        exclusion_tag: str,
        variables: tuple[str, ...],
    ) -> str:
        statement = rows[name].statement
        exclusion = module._no_bertrand_closed_term(
            "n",
            tag=exclusion_tag,
            variables=variables,
        )
        assert statement.count(exclusion) == 1, name
        return statement.replace(exclusion, "n = n", 1)

    result = {
        BETA_PRODUCT_ALL_ONE_EXACT: rows[
            BETA_PRODUCT_ALL_ONE_EXACT
        ].statement.replace("-> z = 1", "-> z = 0", 1),
        NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE: relaxed(
            NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
            exclusion_tag="b5nbscc_exclusion",
            variables=("n", "s", "q", "r", "C", "i", "a"),
        ),
        NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR: relaxed(
            NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
            exclusion_tag="b5nbmcc_exclusion",
            variables=("n", "s", "q", "r", "C", "i", "a", "p"),
        ),
        NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE: relaxed(
            NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
            exclusion_tag="b5nbhcc_exclusion",
            variables=("n", "s", "q", "r", "C", "i", "a"),
        ),
        NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER: relaxed(
            NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
            exclusion_tag="b5nbscplp_exclusion",
            variables=("n", "s", "q", "r", "C", "z", "A"),
        ),
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL:
            relaxed(
                NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
                exclusion_tag="b5nbmcilpi_exclusion",
                variables=("n", "s", "q", "r", "C", "g", "y", "P"),
            ),
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW: relaxed(
            NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
            exclusion_tag="b5nbmcilfp_exclusion",
            variables=("n", "s", "q", "r", "C", "g", "y", "B"),
        ),
        NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE: relaxed(
            NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
            exclusion_tag="b5nbhcieu_exclusion",
            variables=("n", "s", "q", "r", "C", "h", "w"),
        ),
        CENTRAL_BINOM_FACTORIZATION_SMALL: relaxed(
            CENTRAL_BINOM_FACTORIZATION_SMALL,
            exclusion_tag="b5cbfs_exclusion",
            variables=("n", "s", "q", "r", "C", "g", "h", "z"),
        ),
        CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME: relaxed(
            CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME,
            exclusion_tag="b5cblonbp_exclusion",
            variables=("n", "s", "q", "r", "C", "A", "B"),
        ),
    }

    def replace_once(name: str, old: str, new: str) -> None:
        assert result[name].count(old) == 1, name
        result[name] = result[name].replace(old, new, 1)

    replace_once(
        NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
        module._le_term(
            "a",
            "n + n",
            tag="b5nbscc_result",
            variables=("n", "s", "q", "r", "C", "i", "a"),
        ),
        module._le_term(
            "a",
            "n",
            tag="b5nbscc_result",
            variables=("n", "s", "q", "r", "C", "i", "a"),
        ),
    )
    replace_once(
        NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
        module._le_term(
            "a",
            "p",
            tag="b5nbmcc_result",
            variables=("n", "s", "q", "r", "C", "i", "a", "p"),
        ),
        module._le_term(
            "S a",
            "p",
            tag="b5nbmcc_result",
            variables=("n", "s", "q", "r", "C", "i", "a", "p"),
        ),
    )
    replace_once(
        NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
        module._le_term(
            "z",
            "A",
            tag="b5nbscplp_result",
            variables=("n", "s", "q", "r", "C", "z", "A"),
        ),
        module._le_term(
            "A",
            "z",
            tag="b5nbscplp_result",
            variables=("n", "s", "q", "r", "C", "z", "A"),
        ),
    )
    replace_once(
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
        module._le_term(
            "y",
            "P",
            tag="b5nbmcilpi_result",
            variables=("n", "s", "q", "r", "C", "g", "y", "P"),
        ),
        module._le_term(
            "S y",
            "P",
            tag="b5nbmcilpi_result",
            variables=("n", "s", "q", "r", "C", "g", "y", "P"),
        ),
    )
    replace_once(
        NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
        module._le_term(
            "y",
            "B",
            tag="b5nbmcilfp_result",
            variables=("n", "s", "q", "r", "C", "g", "y", "B"),
        ),
        module._le_term(
            "B",
            "y",
            tag="b5nbmcilfp_result",
            variables=("n", "s", "q", "r", "C", "g", "y", "B"),
        ),
    )
    replace_once(
        CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME,
        module._le_term(
            "C",
            "A * B",
            tag="b5cblonbp_result",
            variables=("n", "s", "q", "r", "C", "A", "B"),
        ),
        module._le_term(
            "A * B",
            "C",
            tag="b5cblonbp_result",
            variables=("n", "s", "q", "r", "C", "A", "B"),
        ),
    )
    assert tuple(result) == EXPECTED_NAMES
    return result


MUTATIONS = _mutations()


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_b5_central_upper_dependencies_are_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_rows())[name]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_central_upper_false_targets_fail(name: str) -> None:
    item = _table(_rows())[name]
    changed = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


def test_bertrand_b5_central_upper_mutation_counterfixtures() -> None:
    # Empty all-one Product: z=1, so the mutated z=0 conclusion fails.
    assert 1 != 0
    # n=3, C(6,3)=20: the 2-contribution is 4, not <= n.
    assert not (4 <= 3)
    # n=8, C(16,8)=12870: middle contribution and selector are both 5.
    assert not (5 + 1 <= 5)
    # n=3: the high-range prime 5 contributes 5, not the unit.
    assert 5 != 1
    # n=3: small Product=4 and Pow(6,2)=36; the reverse bound fails.
    assert not (36 <= 4)
    # n=8: the one-factor middle interval and Primorial interval both equal 5.
    assert not (5 + 1 <= 5)
    # n=8: its middle interval is 5, while Pow(4,5)=1024.
    assert not (1024 <= 5)
    # n=3: the high interval contains the contribution 5, hence Product=5.
    assert 5 != 1
    # n=3: z=C(6,3)=20, but the first two range Products are 4 and 1.
    assert 20 != 4 * 1
    # n=3: the reversed final result would require 36*16 <= 20.
    assert not (36 * 16 <= 20)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_central_upper_genuine_mutations_fail(name: str) -> None:
    item = _table(_rows())[name]
    changed = replace(item, statement=MUTATIONS[name])
    assert _closed_formula(changed.statement) != _closed_formula(item.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_central_upper_closures(name: str) -> None:
    receipt = _run_worker("--closure-worker", name)
    actual = tuple(receipt["closure"])
    print(f"B5 CENTRAL UPPER {name} CLOSURE {actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]


def _main() -> None:
    assert len(sys.argv) == 3
    mode, name = sys.argv[1:]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        receipt = _body_receipt(name)
    elif mode == "--closure-worker":
        receipt = _layered_receipt(name)
    else:
        raise AssertionError(mode)
    print("B5CU " + json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main()
