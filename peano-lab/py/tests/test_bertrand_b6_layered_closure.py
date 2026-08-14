"""Isolated empty-context LayeredReplay audits for the Bertrand B6 rows.

The two growth roots are deliberately independent: each candidate pool adds
only the selected growth row to its exact prior manifest.  The three main
roots are canonical dependency closures.  They rebuild every reachable
non-Stable theorem body, including both growth rows and the complete all-root
H/J graph, and stop only at the checked Stable registry boundary.

The balanced exact-power seed is substituted only in the heavy main pools
where that seed is reachable.  Prior candidate closure receipts are never
loaded as theorem authority.  Structural body interning and LayeredReplay are
untrusted construction steps; every interned body and every final candidate
is checked by the unchanged kernel before a receipt may be frozen.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import (
    bertrand_power_seed_balanced_candidate as balanced_seed_provider,
)
from peano_lab.library.bertrand_b6_growth_candidate import (
    make_bertrand_b6_growth_candidate_theorems,
)
from peano_lab.library.bertrand_b6_main_inequality_candidate import (
    make_bertrand_b6_main_inequality_candidate_theorems,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.bertrand_hj_all_s_candidate import (
    make_bertrand_hj_all_s_candidate_theorems,
)
from peano_lab.library.bertrand_hj_base_thirty_two_candidate import (
    make_bertrand_hj_base_thirty_two_candidate_theorems,
)
from peano_lab.library.bertrand_hj_transport_candidate import (
    make_bertrand_hj_transport_candidate_theorems,
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
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
)
from peano_lab.library.bertrand_threshold_base_candidate import (
    make_bertrand_threshold_base_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
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


GROWTH_ROOTS = (
    "bertrand_floor_power_product_le_h_from_total",
    "bertrand_four_power_product_le_of_sum_from_total",
)
MAIN_ROOTS = (
    "bertrand_main_inequality_factorized_from_total",
    "bertrand_main_inequality_factorized",
    "bertrand_main_inequality_nat",
)
ROOTS = (*GROWTH_ROOTS, *MAIN_ROOTS)

EXPECTED_ROOT_DEPENDENCIES = {
    "bertrand_floor_power_product_le_h_from_total": (
        "floor_sqrt_strict_upper_bound",
        "lt_to_le",
        "le_add_right",
        "two_mul_eq_add_self",
        "le_trans",
        "pow_two",
        "pow_base_monotone",
        "pow_mul_exp_from_total",
        "pow_add",
        "mul_le_mul",
        "mul_comm",
    ),
    "bertrand_four_power_product_le_of_sum_from_total": (
        "pow_add",
        "pow_exponent_monotone_from_total",
        "mul_comm",
    ),
    "bertrand_main_inequality_factorized_from_total": (
        "floor_sqrt_factorized_threshold_thirty_two",
        "ceil_div_six_total",
        "bertrand_hj_envelope_thirty_two",
        "floor_ceil_division_budget",
        "bertrand_floor_power_product_le_h_from_total",
        "bertrand_four_power_product_le_of_sum_from_total",
        "mul_le_mul_right",
        "le_trans",
    ),
    "bertrand_main_inequality_factorized": (
        "pow_exists",
        "bertrand_main_inequality_factorized_from_total",
    ),
    "bertrand_main_inequality_nat": (
        "two_mul_eq_add_self",
        "bertrand_main_inequality_factorized",
    ),
}

BALANCED_SEED_PROVIDER_NAMES = (
    "eight_times_eight_eq_sixty_four",
    "eight_times_sixteen_eq_one_twenty_eight",
    "pow_two_seed_bundle_from_total",
)
BALANCED_SEED_NAME = BALANCED_SEED_PROVIDER_NAMES[-1]
BALANCED_SEED_PROVIDER_SOURCE_SHA256 = (
    "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
)
BALANCED_SEED_PROVIDER_SCRIPT_SHA256 = (
    "2b83f8e5ff38b9fd620570de270cbd79e928b933ac49e0db4a5ac042e69d267b"
)
BALANCED_SEED_PROVIDER_LOGICAL_SHA256 = (
    "2f16ad95b11aa3044770df1f3312bfefb3c0fd2aa32f1da2403641daa97f12ea"
)

PENDING_LAYERED_CLOSURE = "PENDING_B6_LAYERED_CLOSURE"
EXPECTED_LAYERED_CLOSURES: dict[str, dict[str, object] | str] = {
    "bertrand_floor_power_product_le_h_from_total": {
        "root_name": "bertrand_floor_power_product_le_h_from_total",
        "topology_sha256": (
            "f095c240d68ad4cd99ebe408eec992acd912a7a447664a21977d2e98132cb654"
        ),
        "candidate_pool_count": 26,
        "candidate_pool_script_sha256": (
            "a9014139b418bbada216630e71a0506a9f87bd38eaa09835c44d244aab8b92ca"
        ),
        "candidate_pool_logical_sha256": (
            "4452235ba34254be5b48e63dacb394e45ad63fecd233d9b39e0ede4a08927244"
        ),
        "unreachable_candidate_count": 20,
        "unreachable_candidate_names_sha256": (
            "0dab2f95c302a28044299cc99477b50bd1405787f4d39178c3d1172c93f7a25d"
        ),
        "balanced_seed_substituted": False,
        "balanced_seed_provider_source_sha256": None,
        "balanced_seed_provider_script_sha256": None,
        "balanced_seed_provider_logical_sha256": None,
        "node_count": 18,
        "stable_atomic_count": 12,
        "candidate_body_count": 6,
        "dependency_edge_count": 23,
        "layer_sizes": (13, 3, 1, 1),
        "max_fan_in": 11,
        "raw_body_union_objects": 2_229,
        "interned_body_union_objects": 1_500,
        "body_union_object_savings": 729,
        "proof_nodes": 18_459,
        "proof_depth": 73,
        "proof_objects": 1_641,
        "proof_edges": 2_143,
        "reused_objects": 503,
        "annotation_occurrences": 80_696,
        "envelope_depth": 73,
        "package_formula_occurrences": 3_343,
        "package_formula_depth": 40,
        "proof_dag_sha256": (
            "da2a48076c582e44eece6a69b98404c7739dd6ab8a8e17ac6f1efccfe04a453c"
        ),
    },
    "bertrand_four_power_product_le_of_sum_from_total": {
        "root_name": "bertrand_four_power_product_le_of_sum_from_total",
        "topology_sha256": (
            "42c24594239106ae412230b020d65afd3431b4402cf897728878b5e89b7a8657"
        ),
        "candidate_pool_count": 26,
        "candidate_pool_script_sha256": (
            "9ebb93d7f819bd9c101aff8e600aadf70dd230a44e1c28828a2fc5620577e6ae"
        ),
        "candidate_pool_logical_sha256": (
            "58bde20ca6a5416b1159ac00e41123b5911373f6e92c767095b2fbf06136c4e3"
        ),
        "unreachable_candidate_count": 22,
        "unreachable_candidate_names_sha256": (
            "d6ac65cf1d9ac1cc6ce1bb4d150149d09cecd1e5699f801039ea596c7a307d2e"
        ),
        "balanced_seed_substituted": False,
        "balanced_seed_provider_source_sha256": None,
        "balanced_seed_provider_script_sha256": None,
        "balanced_seed_provider_logical_sha256": None,
        "node_count": 13,
        "stable_atomic_count": 9,
        "candidate_body_count": 4,
        "dependency_edge_count": 14,
        "layer_sizes": (9, 1, 1, 1, 1),
        "max_fan_in": 5,
        "raw_body_union_objects": 1_777,
        "interned_body_union_objects": 1_218,
        "body_union_object_savings": 559,
        "proof_nodes": 11_293,
        "proof_depth": 70,
        "proof_objects": 1_292,
        "proof_edges": 1_699,
        "reused_objects": 408,
        "annotation_occurrences": 51_664,
        "envelope_depth": 70,
        "package_formula_occurrences": 2_832,
        "package_formula_depth": 39,
        "proof_dag_sha256": (
            "08cbeb657890b2c76ca47f7dfef7dd960219ded31a57237f607f91b058ccfe0e"
        ),
    },
    "bertrand_main_inequality_factorized_from_total": {
        "root_name": "bertrand_main_inequality_factorized_from_total",
        "topology_sha256": (
            "b9f0f9fb2e5e4067daf9df4eb04022e2cf13767ec95c33297470c7483dfdabae"
        ),
        "candidate_pool_count": 88,
        "candidate_pool_script_sha256": (
            "1f84f11cdeabf6cce8dbe83ac964753517bb143ef83609eed75347b275ceac89"
        ),
        "candidate_pool_logical_sha256": (
            "ce44bb36af7c6124c9869139c9c5577df6a504b2de0b5489c3ea8b9dc0b45f83"
        ),
        "unreachable_candidate_count": 18,
        "unreachable_candidate_names_sha256": (
            "808f77afec6f6d2ed797d16d96c4a6236c11140356aba6de1a4d5cc3f8a702fb"
        ),
        "balanced_seed_substituted": True,
        "balanced_seed_provider_source_sha256": (
            "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
        ),
        "balanced_seed_provider_script_sha256": (
            "2b83f8e5ff38b9fd620570de270cbd79e928b933ac49e0db4a5ac042e69d267b"
        ),
        "balanced_seed_provider_logical_sha256": (
            "2f16ad95b11aa3044770df1f3312bfefb3c0fd2aa32f1da2403641daa97f12ea"
        ),
        "node_count": 111,
        "stable_atomic_count": 41,
        "candidate_body_count": 70,
        "dependency_edge_count": 363,
        "layer_sizes": (43, 19, 16, 11, 7, 4, 7, 1, 1, 1, 1),
        "max_fan_in": 13,
        "raw_body_union_objects": 102_906,
        "interned_body_union_objects": 14_613,
        "body_union_object_savings": 88_293,
        "proof_nodes": 196_517,
        "proof_depth": 179,
        "proof_objects": 17_207,
        "proof_edges": 23_028,
        "reused_objects": 5_822,
        "annotation_occurrences": 1_096_030,
        "envelope_depth": 209,
        "package_formula_occurrences": 36_839,
        "package_formula_depth": 147,
        "proof_dag_sha256": (
            "b312f9d46c6ad4c7b61b8740011b5bdb9a34ddc46d434ec9914f3778abd18f17"
        ),
    },
    "bertrand_main_inequality_factorized": {
        "root_name": "bertrand_main_inequality_factorized",
        "topology_sha256": (
            "145d4e47f3e405a726bc212474bd850894253bd7dcd660f47978f5c9b341fe98"
        ),
        "candidate_pool_count": 89,
        "candidate_pool_script_sha256": (
            "1f6ed04aaee53e71d13df58a33310ce3670bc1542bbae4087fdab191298f5e1c"
        ),
        "candidate_pool_logical_sha256": (
            "c11064518af962f11d83675143e43da3ef7029a4082e093eb6d54f7c31681cc2"
        ),
        "unreachable_candidate_count": 18,
        "unreachable_candidate_names_sha256": (
            "808f77afec6f6d2ed797d16d96c4a6236c11140356aba6de1a4d5cc3f8a702fb"
        ),
        "balanced_seed_substituted": True,
        "balanced_seed_provider_source_sha256": (
            "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
        ),
        "balanced_seed_provider_script_sha256": (
            "2b83f8e5ff38b9fd620570de270cbd79e928b933ac49e0db4a5ac042e69d267b"
        ),
        "balanced_seed_provider_logical_sha256": (
            "2f16ad95b11aa3044770df1f3312bfefb3c0fd2aa32f1da2403641daa97f12ea"
        ),
        "node_count": 112,
        "stable_atomic_count": 41,
        "candidate_body_count": 71,
        "dependency_edge_count": 365,
        "layer_sizes": (43, 19, 16, 11, 7, 4, 7, 1, 1, 1, 1, 1),
        "max_fan_in": 13,
        "raw_body_union_objects": 102_947,
        "interned_body_union_objects": 14_637,
        "body_union_object_savings": 88_310,
        "proof_nodes": 196_568,
        "proof_depth": 179,
        "proof_objects": 17_241,
        "proof_edges": 23_070,
        "reused_objects": 5_830,
        "annotation_occurrences": 1_095_387,
        "envelope_depth": 209,
        "package_formula_occurrences": 37_547,
        "package_formula_depth": 147,
        "proof_dag_sha256": (
            "e06b155d5aae8c527168604accca11dcf1175964622ef8224f4c3a081afd7276"
        ),
    },
    "bertrand_main_inequality_nat": {
        "root_name": "bertrand_main_inequality_nat",
        "topology_sha256": (
            "bd4bb0c71190b0d7babde408e47a4d8f667f2898fc879f40583801af99a1db04"
        ),
        "candidate_pool_count": 90,
        "candidate_pool_script_sha256": (
            "ed2b4bfbb30007f3dec28ceb18fcea5a0cc922c507b45501d9e0487a9fa1df4c"
        ),
        "candidate_pool_logical_sha256": (
            "63821d5cea25cfaa2170c47aa3548a6d0c9ce65143edddd0eb21bad85f119cd4"
        ),
        "unreachable_candidate_count": 18,
        "unreachable_candidate_names_sha256": (
            "808f77afec6f6d2ed797d16d96c4a6236c11140356aba6de1a4d5cc3f8a702fb"
        ),
        "balanced_seed_substituted": True,
        "balanced_seed_provider_source_sha256": (
            "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
        ),
        "balanced_seed_provider_script_sha256": (
            "2b83f8e5ff38b9fd620570de270cbd79e928b933ac49e0db4a5ac042e69d267b"
        ),
        "balanced_seed_provider_logical_sha256": (
            "2f16ad95b11aa3044770df1f3312bfefb3c0fd2aa32f1da2403641daa97f12ea"
        ),
        "node_count": 113,
        "stable_atomic_count": 41,
        "candidate_body_count": 72,
        "dependency_edge_count": 367,
        "layer_sizes": (43, 19, 16, 11, 7, 4, 7, 1, 1, 1, 1, 1, 1),
        "max_fan_in": 13,
        "raw_body_union_objects": 103_002,
        "interned_body_union_objects": 14_664,
        "body_union_object_savings": 88_338,
        "proof_nodes": 196_618,
        "proof_depth": 179,
        "proof_objects": 17_263,
        "proof_edges": 23_104,
        "reused_objects": 5_842,
        "annotation_occurrences": 1_097_116,
        "envelope_depth": 210,
        "package_formula_occurrences": 38_245,
        "package_formula_depth": 147,
        "proof_dag_sha256": (
            "5e2907e91cb6bd2108a92b4a313b18d11da2097ae9044af47006884693c09082"
        ),
    },
}


@dataclass(frozen=True, slots=True)
class _Blueprint:
    """One root-pruned local-ID graph with Stable certificates as leaves."""

    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    kinds: tuple[str, ...]
    root: int
    topology_sha256: str


@lru_cache(maxsize=1)
def _growth_prior_specs() -> tuple[TheoremSpec, ...]:
    """Exact candidate manifest used by the focused growth-body audit."""

    rows = (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
    )
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=1)
def _main_prior_specs() -> tuple[TheoremSpec, ...]:
    """Exact pre-all-root manifest used by the all-s closure audit."""

    rows = (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
        *make_bertrand_threshold_base_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_transport_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_base_thirty_two_candidate_theorems(TheoremSpec),
    )
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=1)
def _growth_specs() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b6_growth_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == GROWTH_ROOTS
    return rows


@lru_cache(maxsize=1)
def _all_s_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_all_s_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _main_specs() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b6_main_inequality_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == MAIN_ROOTS
    return rows


def _provider_script_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((item.name, *item.script)) for item in rows
    )
    return sha256(payload.encode()).hexdigest()


def _provider_logical_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((item.name, item.statement, *item.dependencies))
        for item in rows
    )
    return sha256(payload.encode()).hexdigest()


@lru_cache(maxsize=1)
def _balanced_seed_specs() -> tuple[TheoremSpec, ...]:
    rows = balanced_seed_provider.make_bertrand_power_seed_balanced_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == BALANCED_SEED_PROVIDER_NAMES
    assert len({row.name for row in rows}) == len(rows)
    assert not (set(BALANCED_SEED_PROVIDER_NAMES) & set(_specs_by_name()))
    assert sha256(
        Path(balanced_seed_provider.__file__).read_bytes()
    ).hexdigest() == BALANCED_SEED_PROVIDER_SOURCE_SHA256
    assert (
        _provider_script_sha256(rows)
        == BALANCED_SEED_PROVIDER_SCRIPT_SHA256
    )
    assert (
        _provider_logical_sha256(rows)
        == BALANCED_SEED_PROVIDER_LOGICAL_SHA256
    )

    old_rows = tuple(
        row for row in _main_prior_specs() if row.name == BALANCED_SEED_NAME
    )
    assert len(old_rows) == 1
    old_seed = old_rows[0]
    replacement = rows[-1]
    assert replacement.name == old_seed.name
    assert replacement.statement == old_seed.statement
    assert replacement.dependencies != old_seed.dependencies
    assert replacement.script != old_seed.script
    return rows


@lru_cache(maxsize=1)
def _balanced_main_prior_specs() -> tuple[TheoremSpec, ...]:
    prior = _main_prior_specs()
    provider = _balanced_seed_specs()
    old_seed = next(row for row in prior if row.name == BALANCED_SEED_NAME)
    old_index = prior.index(old_seed)
    rows = (
        *prior[:old_index],
        *provider,
        *prior[old_index + 1 :],
    )
    assert rows[:old_index] == prior[:old_index]
    assert rows[old_index : old_index + len(provider)] == provider
    assert rows[old_index + len(provider) :] == prior[old_index + 1 :]
    assert all(row is not old_seed for row in rows)
    assert sum(row.name == BALANCED_SEED_NAME for row in rows) == 1
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=None)
def _candidate_pool(root_name: str) -> tuple[TheoremSpec, ...]:
    """Return the exact independent or canonical pool for one root."""

    if root_name in GROWTH_ROOTS:
        selected = next(
            row for row in _growth_specs() if row.name == root_name
        )
        rows = (*_growth_prior_specs(), selected)
        assert sum(row.name == root_name for row in rows) == 1
        assert not (
            (set(GROWTH_ROOTS) - {root_name})
            & {row.name for row in rows}
        )
        assert not (
            set(BALANCED_SEED_PROVIDER_NAMES[:-1])
            & {row.name for row in rows}
        )
    elif root_name in MAIN_ROOTS:
        prefix_length = MAIN_ROOTS.index(root_name) + 1
        rows = (
            *_balanced_main_prior_specs(),
            *_all_s_specs(),
            *_growth_specs(),
            *_main_specs()[:prefix_length],
        )
        assert tuple(row.name for row in rows[-prefix_length:]) == (
            MAIN_ROOTS[:prefix_length]
        )
        assert tuple(
            row
            for row in rows
            if row.name in BALANCED_SEED_PROVIDER_NAMES
        ) == _balanced_seed_specs()
        old_seed = next(
            row
            for row in _main_prior_specs()
            if row.name == BALANCED_SEED_NAME
        )
        assert all(row is not old_seed for row in rows)
    else:
        raise AssertionError(f"unknown B6 layered root {root_name!r}")

    assert len({row.name for row in rows}) == len(rows)
    public = _specs_by_name()
    collisions = set(public) & {row.name for row in rows}
    by_name = {row.name: row for row in rows}
    assert all(public[name] == by_name[name] for name in collisions)
    return rows


def _pool_script_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, *row.script)) for row in rows
    )
    return sha256(payload.encode()).hexdigest()


def _pool_logical_sha256(rows: tuple[TheoremSpec, ...]) -> str:
    payload = "\x1c".join(
        "\x1f".join((row.name, row.statement, *row.dependencies))
        for row in rows
    )
    return sha256(payload.encode()).hexdigest()


@lru_cache(maxsize=None)
def _blueprint(root_name: str) -> _Blueprint:
    """Prune one root transitively and stop only at Stable theorems."""

    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    for name in set(public) & set(candidates):
        assert public[name] == candidates[name]

    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        if item is None:
            raise AssertionError(
                f"unknown dependency {name!r} below B6 root {root_name!r}"
            )
        mark = marks.get(name, 0)
        if mark == 1:
            raise AssertionError(
                f"cyclic dependency at {name!r} below {root_name!r}"
            )
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(root_name)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {name: index for index, name in enumerate(names)}
    assert len(positions) == len(names)

    kinds = tuple(
        "stable_atomic" if name in stable_names else "candidate_body"
        for name in names
    )
    selected_specs = tuple(
        public[name] if name in stable_names else candidates[name]
        for name in names
    )
    targets = tuple(_closed_formula(item.statement) for item in selected_specs)
    dependencies = tuple(
        ()
        if kind == "stable_atomic"
        else tuple(positions[name] for name in item.dependencies)
        for kind, item in zip(kinds, selected_specs, strict=True)
    )

    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        if any(dependency >= node_id for dependency in node_dependencies):
            raise AssertionError(
                f"dependency did not precede node {node_id} below {root_name!r}"
            )
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[item] for item in node_dependencies)
        )
    layer_lists: list[list[int]] = [
        [] for _ in range(1 + max(depths, default=0))
    ]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)

    topology_rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                selected_specs[node_id].statement,
                "\x1e".join(
                    names[dependency]
                    for dependency in dependencies[node_id]
                ),
            )
        )
        for node_id, name in enumerate(names)
    )
    return _Blueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        kinds=kinds,
        root=positions[root_name],
        topology_sha256=sha256(
            "\x1c".join(topology_rows).encode()
        ).hexdigest(),
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
    target = targets_by_name[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets_by_name[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        if tactic == "use":
            raise AssertionError(
                f"candidate body {item.name!r} delegated through use"
            )
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=None)
def _bundle(root_name: str) -> LayeredReplayBundle:
    blueprint = _blueprint(root_name)
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    targets_by_name = dict(
        zip(blueprint.names, blueprint.targets, strict=True)
    )
    nodes: list[LayeredReplayNode] = []
    built_candidates: list[str] = []
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            theorem = replay(name)
            assert theorem.formula == blueprint.targets[node_id]
            assert theorem.spec == public[name]
            body = theorem.certificate
        else:
            built_candidates.append(name)
            body = _dependency_curried_body(
                candidates[name], targets_by_name
            )
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=blueprint.targets[node_id],
                dependencies=blueprint.dependencies[node_id],
                body=body,
            )
        )
    assert tuple(built_candidates) == tuple(
        name
        for name, kind in zip(
            blueprint.names, blueprint.kinds, strict=True
        )
        if kind == "candidate_body"
    )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


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


def _proof_union_object_count(proofs: tuple[Proof, ...]) -> int:
    pending = list(proofs)
    seen: set[int] = set()
    while pending:
        proof = pending.pop()
        identity = id(proof)
        if identity in seen:
            continue
        seen.add(identity)
        pending.extend(_proof_children(proof))
    return len(seen)


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
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)]
                if isinstance(value, Proof)
                else repr(value)
            )
        digests[identity] = sha256(
            "\x1f".join(payload).encode()
        ).hexdigest()
    return digests[id(proof)]


def test_b6_layered_closure_static_manifest_is_fail_closed() -> None:
    assert ROOTS == (*GROWTH_ROOTS, *MAIN_ROOTS)
    assert tuple(EXPECTED_ROOT_DEPENDENCIES) == ROOTS
    assert tuple(EXPECTED_LAYERED_CLOSURES) == ROOTS
    assert all(
        expected == PENDING_LAYERED_CLOSURE
        or isinstance(expected, dict)
        for expected in EXPECTED_LAYERED_CLOSURES.values()
    )
    assert tuple(row.name for row in _growth_specs()) == GROWTH_ROOTS
    assert tuple(row.name for row in _main_specs()) == MAIN_ROOTS
    assert tuple(row.name for row in _balanced_seed_specs()) == (
        BALANCED_SEED_PROVIDER_NAMES
    )
    for root_name in ROOTS:
        root = next(
            row
            for row in _candidate_pool(root_name)
            if row.name == root_name
        )
        assert root.dependencies == EXPECTED_ROOT_DEPENDENCIES[root_name]


@pytest.mark.parametrize("root_name", ROOTS, ids=ROOTS)
def test_b6_root_pruned_layered_empty_context_closure(
    root_name: str,
) -> None:
    """Compile and kernel-check exactly one B6 root in a fresh process."""

    blueprint = _blueprint(root_name)
    pool = _candidate_pool(root_name)
    candidates = {row.name: row for row in pool}
    public = _specs_by_name()
    stable_names = {
        name
        for name, kind in zip(
            blueprint.names, blueprint.kinds, strict=True
        )
        if kind == "stable_atomic"
    }
    candidate_names = set(blueprint.names) - stable_names
    unreachable_candidates = set(candidates) - set(blueprint.names)

    assert blueprint.names[blueprint.root] == root_name
    assert blueprint.targets[blueprint.root] == _closed_formula(
        candidates[root_name].statement
    )
    assert stable_names <= set(public)
    assert not (candidate_names & set(public))
    assert candidate_names <= set(candidates)
    assert set(blueprint.kinds) <= {"stable_atomic", "candidate_body"}
    assert blueprint.kinds == (
        ("stable_atomic",) * len(stable_names)
        + ("candidate_body",) * len(candidate_names)
    )
    assert tuple(
        blueprint.names[dependency]
        for dependency in blueprint.dependencies[blueprint.root]
    ) == EXPECTED_ROOT_DEPENDENCIES[root_name]
    assert blueprint.root in blueprint.layers[-1]
    assert all(tuple(sorted(layer)) == layer for layer in blueprint.layers)
    assert {
        node_id for layer in blueprint.layers for node_id in layer
    } == set(range(len(blueprint.names)))
    assert all(
        dependency < node_id
        for node_id, dependencies in enumerate(blueprint.dependencies)
        for dependency in dependencies
    )
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            assert blueprint.dependencies[node_id] == ()
        else:
            assert tuple(
                blueprint.names[dependency]
                for dependency in blueprint.dependencies[node_id]
            ) == candidates[name].dependencies

    reachable: set[int] = set()
    pending = [blueprint.root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(blueprint.dependencies[node_id])
    assert reachable == set(range(len(blueprint.names)))

    if root_name in GROWTH_ROOTS:
        assert not (
            set(BALANCED_SEED_PROVIDER_NAMES) & set(blueprint.names)
        )
        assert not (
            (set(GROWTH_ROOTS) - {root_name}) & set(candidates)
        )
        balanced_seed_substituted = False
    else:
        assert set(BALANCED_SEED_PROVIDER_NAMES) <= candidate_names
        assert {
            "bertrand_hj_six_block_iterate_from_total",
            "bertrand_hj_envelope_thirty_two",
            *GROWTH_ROOTS,
        } <= candidate_names
        required_main_prefix = set(
            MAIN_ROOTS[: MAIN_ROOTS.index(root_name) + 1]
        )
        assert required_main_prefix <= candidate_names
        balanced_seed_substituted = True

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    assert len(blueprint.names) <= limits.max_nodes
    assert sum(map(len, blueprint.dependencies)) <= (
        limits.max_dependency_edges
    )
    assert max(map(len, blueprint.dependencies)) <= (
        limits.max_dependencies_per_node
    )

    raw_bundle = _bundle(root_name)
    interned_bundle = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=limits,
    )
    assert type(interned_bundle) is LayeredReplayBundle
    assert interned_bundle.root == raw_bundle.root
    assert len(interned_bundle.nodes) == len(raw_bundle.nodes)
    for raw_node, interned_node in zip(
        raw_bundle.nodes, interned_bundle.nodes, strict=True
    ):
        assert type(interned_node) is LayeredReplayNode
        assert interned_node.node_id == raw_node.node_id
        assert interned_node.target is raw_node.target
        assert interned_node.dependencies is raw_node.dependencies
        assert interned_node.body == raw_node.body

    raw_body_union_objects = _proof_union_object_count(
        tuple(node.body for node in raw_bundle.nodes)
    )
    interned_body_union_objects = _proof_union_object_count(
        tuple(node.body for node in interned_bundle.nodes)
    )
    assert interned_body_union_objects <= raw_body_union_objects
    body_union_object_savings = (
        raw_body_union_objects - interned_body_union_objects
    )

    targets_by_id = {
        node.node_id: node.target for node in interned_bundle.nodes
    }
    for node in interned_bundle.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(targets_by_id[dependency], body_target)
        assert check((), node.body, body_target), (
            f"interned body failed exact kernel judgment at {node.node_id} "
            f"({blueprint.names[node.node_id]!r}) below {root_name!r}"
        )
        assert not any(type(item) is DNE for item in _walk(node.body))

    compilation = compile_layered_replay(
        interned_bundle,
        blueprint.targets[blueprint.root],
        limits=limits,
    )
    assert type(compilation) is LayeredReplayCandidate
    assert compilation.target == blueprint.targets[blueprint.root]
    assert compilation.layers == blueprint.layers
    assert len(compilation.package_formulas) == len(blueprint.layers)
    assert compilation.package_formula_occurrences <= (
        limits.max_package_formula_occurrences
    )
    assert compilation.maximum_package_formula_depth <= (
        limits.max_package_formula_depth
    )
    assert compilation.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compilation.proof_objects <= limits.max_candidate_proof_objects
    assert compilation.proof_depth <= limits.max_candidate_proof_depth
    assert compilation.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compilation.proof_envelope_depth <= (
        limits.max_candidate_envelope_depth
    )
    assert compilation.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert compilation.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert compilation.proof_objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(
        type(item) is DNE for item in _walk(compilation.certificate)
    )

    kernel_accepted = check(
        (), compilation.certificate, compilation.target
    )
    proof_dag_sha256 = _proof_dag_sha256(compilation.certificate)
    actual: dict[str, object] = {
        "root_name": root_name,
        "topology_sha256": blueprint.topology_sha256,
        "candidate_pool_count": len(pool),
        "candidate_pool_script_sha256": _pool_script_sha256(pool),
        "candidate_pool_logical_sha256": _pool_logical_sha256(pool),
        "unreachable_candidate_count": len(unreachable_candidates),
        "unreachable_candidate_names_sha256": sha256(
            "\0".join(sorted(unreachable_candidates)).encode()
        ).hexdigest(),
        "balanced_seed_substituted": balanced_seed_substituted,
        "balanced_seed_provider_source_sha256": (
            BALANCED_SEED_PROVIDER_SOURCE_SHA256
            if balanced_seed_substituted
            else None
        ),
        "balanced_seed_provider_script_sha256": (
            BALANCED_SEED_PROVIDER_SCRIPT_SHA256
            if balanced_seed_substituted
            else None
        ),
        "balanced_seed_provider_logical_sha256": (
            BALANCED_SEED_PROVIDER_LOGICAL_SHA256
            if balanced_seed_substituted
            else None
        ),
        "node_count": len(blueprint.names),
        "stable_atomic_count": len(stable_names),
        "candidate_body_count": len(candidate_names),
        "dependency_edge_count": sum(map(len, blueprint.dependencies)),
        "layer_sizes": tuple(map(len, blueprint.layers)),
        "max_fan_in": max(map(len, blueprint.dependencies)),
        "raw_body_union_objects": raw_body_union_objects,
        "interned_body_union_objects": interned_body_union_objects,
        "body_union_object_savings": body_union_object_savings,
        "proof_nodes": compilation.proof_nodes,
        "proof_depth": compilation.proof_depth,
        "proof_objects": compilation.proof_objects,
        "proof_edges": compilation.proof_edges,
        "reused_objects": compilation.reused_objects,
        "annotation_occurrences": (
            compilation.proof_annotation_occurrences
        ),
        "envelope_depth": compilation.proof_envelope_depth,
        "package_formula_occurrences": (
            compilation.package_formula_occurrences
        ),
        "package_formula_depth": (
            compilation.maximum_package_formula_depth
        ),
        "proof_dag_sha256": proof_dag_sha256,
    }
    print(
        "BERTRAND B6 LAYERED CLOSURE RECEIPT "
        f"root={root_name!r} actual={actual!r} "
        f"kernel_accepted={kernel_accepted}",
        flush=True,
    )
    assert kernel_accepted
    expected = EXPECTED_LAYERED_CLOSURES[root_name]
    assert isinstance(expected, dict), (
        f"freeze the isolated receipt for {root_name!r} only after the "
        f"kernel accepts it: {actual!r}"
    )
    assert actual == expected
