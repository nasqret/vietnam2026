"""Focused strict-HA scaffold for the all-root Bertrand H/J package.

The six theorem surfaces and their dependency order are frozen here before
any expensive replay is attempted.  ``16*32`` is intentionally the native
threshold carrier; its value 512 is checked below only by host arithmetic and
is never proof authority.  Statement, artifact, and body receipts are frozen
only from successful isolated gates; recursive closure remains pending.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.library import (
    bertrand_power_seed_balanced_candidate as balanced_seed_provider,
)
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
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
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
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "scaled_factor_square_identity",
    "thirty_two_square_eq_twice_sixteen_times_thirty_two",
    "floor_sqrt_factorized_threshold_thirty_two",
    "six_block_window_decomposition_above_thirty_two",
    "bertrand_hj_six_block_iterate_from_total",
    "bertrand_hj_envelope_thirty_two",
)

EXPECTED_DEPENDENCIES = {
    "scaled_factor_square_identity": ("mul_assoc",),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "scaled_factor_square_identity",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        "thirty_two_square_eq_twice_sixteen_times_thirty_two",
        "zero_add",
        "square_lt_successor_square",
        "mul_le_mul_left",
        "floor_sqrt_monotone",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        "division_remainder_exists",
        "succ_ne_zero",
        "le_of_succ_le_succ",
        "le_add_right",
        "add_le_add_left",
        "add_assoc",
        "add_comm",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        "bertrand_hj_base_window_thirty_two_from_total",
        "bertrand_hj_six_step_from_total",
        "ceil_div_six_total",
        "le_add_right",
        "le_trans",
        "mul_add",
        "add_assoc",
    ),
    "bertrand_hj_envelope_thirty_two": (
        "pow_exists",
        "six_block_window_decomposition_above_thirty_two",
        "bertrand_hj_six_block_iterate_from_total",
    ),
}


def _threshold_statement() -> str:
    return (
        "forall n s. "
        f"({witness_le('16 * 32', 'n', tag='hjas_threshold_input')}) -> "
        f"({floor_sqrt_relation('2 * n', 's', tag='hjas_threshold_floor')}) -> "
        f"({witness_le('32', 's', tag='hjas_threshold_result')})"
    )


def _decomposition_statement() -> str:
    lower = witness_le("32", "b", tag="hjas_decomposition_base_lower")
    upper = witness_le("b", "37", tag="hjas_decomposition_base_upper")
    return (
        "forall s. "
        f"({witness_le('32', 's', tag='hjas_decomposition_source')}) -> "
        f"exists b k. ((({lower}) /\\ ({upper})) /\\ s = b + 6 * k)"
    )


def _iterator_statement() -> str:
    root = "b + 6 * k"
    ceiling = ceil_div_six_relation(
        f"({root}) * ({root})", "e", tag="hjas_iterator_ceiling"
    )
    h_power = _power_terms(
        f"({root}) + 1",
        f"2 * ({root}) + 2",
        "h",
        tag="hjas_iterator_h",
    )
    h_bound = _power_terms("4", "e", "u", tag="hjas_iterator_h_bound")
    j_power = _power_terms(
        f"({root}) + 7", "12", "j", tag="hjas_iterator_j"
    )
    j_bound = _power_terms(
        "4", f"({root}) + 5", "g", tag="hjas_iterator_j_bound"
    )
    h_result = witness_le("h", "u", tag="hjas_iterator_h_result")
    j_result = witness_le("j", "g", tag="hjas_iterator_j_result")
    return (
        "forall b. "
        f"({power_total_relation(tag='hjas_iterator')}) -> "
        f"({witness_le('32', 'b', tag='hjas_iterator_base_lower')}) -> "
        f"({witness_le('b', '37', tag='hjas_iterator_base_upper')}) -> "
        "forall k e h u j g. "
        f"({ceiling}) -> ({h_power}) -> ({h_bound}) -> "
        f"({j_power}) -> ({j_bound}) -> "
        f"((({h_result}) /\\ ({j_result})))"
    )


def _envelope_statement() -> str:
    ceiling = ceil_div_six_relation("s * s", "e", tag="hjas_envelope_ceiling")
    h_power = _power_terms(
        "s + 1", "2 * s + 2", "h", tag="hjas_envelope_h"
    )
    h_bound = _power_terms("4", "e", "u", tag="hjas_envelope_h_bound")
    j_power = _power_terms("s + 7", "12", "j", tag="hjas_envelope_j")
    j_bound = _power_terms("4", "s + 5", "g", tag="hjas_envelope_j_bound")
    h_result = witness_le("h", "u", tag="hjas_envelope_h_result")
    j_result = witness_le("j", "g", tag="hjas_envelope_j_result")
    return (
        "forall s e h u j g. "
        f"({witness_le('32', 's', tag='hjas_envelope_lower')}) -> "
        f"({ceiling}) -> ({h_power}) -> ({h_bound}) -> "
        f"({j_power}) -> ({j_bound}) -> "
        f"((({h_result}) /\\ ({j_result})))"
    )


EXPECTED_SURFACES = {
    "scaled_factor_square_identity": (
        "forall c d a. a = c * d -> a * a = c * (d * a)"
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "32 * 32 = 2 * (16 * 32)"
    ),
    "floor_sqrt_factorized_threshold_thirty_two": _threshold_statement(),
    "six_block_window_decomposition_above_thirty_two": (
        _decomposition_statement()
    ),
    "bertrand_hj_six_block_iterate_from_total": _iterator_statement(),
    "bertrand_hj_envelope_thirty_two": _envelope_statement(),
}

# Every receipt class requires isolated execution.  The unskipped readiness
# test below fails for each pending class, so the still-pending closure gate
# cannot be mistaken for a completed candidate audit.
PENDING_CANDIDATE_ONLY = "PENDING_CANDIDATE_ONLY_ISOLATED_AUDIT"
EXPECTED_STATEMENTS: dict[str, tuple[int, str]] | str = {
    "scaled_factor_square_identity": (
        46,
        "62d09740def9373ccc36fa4952c3bf1712c8e627fc215e841b329f9b291a3b8b",
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        23,
        "1956cceff6dca8891691473c37f03d16b21ddba5e96f453c927387edd3045492",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        433,
        "8ffc7797e2501d7a6202f6f0212ebd96b42b406b0045ab2eb353627adf8a452e",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        355,
        "bccb76e88db4f479d9d7bc946efeaee34e2b34ad16d091db3b593fe1d45a5b9a",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        16_717,
        "ddf4cf517f3f775e0d2063ba6385a9a388943d708f90d27cfe3c082df6f02095",
    ),
    "bertrand_hj_envelope_thirty_two": (
        12_794,
        "6eb3d0386aad3792f827c0c93ccc7581400634cfa2d264dee5aae562bc146a6f",
    ),
}

# Successful isolated observations are retained here in theorem order.  The
# full table is promoted below only because all six body gates are now green.
CHECKPOINT_BODY_RECEIPTS: dict[
    str, tuple[int, int, int, int, int, int, int]
] = {
    "scaled_factor_square_identity": (1, 6, 12, 10, 12, 11, 0),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        1,
        7,
        339,
        59,
        339,
        338,
        0,
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        5,
        27,
        34,
        17,
        34,
        33,
        0,
    ),
    "six_block_window_decomposition_above_thirty_two": (
        7,
        57,
        137,
        53,
        137,
        136,
        0,
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        7,
        177,
        2_388,
        96,
        1_986,
        2_387,
        402,
    ),
    "bertrand_hj_envelope_thirty_two": (
        3,
        68,
        102,
        36,
        102,
        101,
        0,
    ),
}
EXPECTED_BODIES: (
    dict[str, tuple[int, int, int, int, int, int, int]] | str
) = dict(CHECKPOINT_BODY_RECEIPTS)
EXPECTED_ARTIFACT_SHA256: dict[str, tuple[str, str]] | str = {
    "scaled_factor_square_identity": (
        "9b1b24c8a7483be234aed26af7e4722b6a1d518e20f058f908b5d17d6bcb1a40",
        "c83bbf482315783db9f0c28042228428e3951c70820474f0af673f13f9e63b86",
    ),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        "19ad9b11be26805e4f3430c099c32a0da2ab11cfc6e8f1307e2afad7198881ec",
        "6f199664eacb96193a0291d2629fc895f641fdb038949ad887e2e8b08d10fb4b",
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        "f088ea48bfe2a3ad62791729743ffd804d2cf4fb54a54ca63d1e6a461108e0c0",
        "ea4b7cfeba6afa11591683bbd8f972259df59b4fc2e76070b86e3a4ab0d07c65",
    ),
    "six_block_window_decomposition_above_thirty_two": (
        "23441fc82fee1af689013ffc9f0457f6f0ebb821f33bc89038b93edc983db558",
        "070fdbbc018d091582a71769967c90712bf8090a81e7d2025a427ae8b15c11d3",
    ),
    "bertrand_hj_six_block_iterate_from_total": (
        "2e6f41166070f330f912d5c01923c97562f6b8239182391ff525facc520c2768",
        "647620ce8053ea7381a3575a345d295b2e6d26b16d93ea358d820ab9a2b9c32d",
    ),
    "bertrand_hj_envelope_thirty_two": (
        "cccc5ad9c8e22fbb6e9a5ee7cdfea4268f21f339eabf0d7a47344724d177fbea",
        "6d83e785bc4f0965be8aa658f4fede1a0d15c0a507836527c30883e91680bf15",
    ),
}
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int]] | str = (
    PENDING_CANDIDATE_ONLY
)

# The four light roots do not traverse the large H/J power graph.  Their
# receipts are frozen independently, one fresh process per row, before the
# two heavy roots receive a root-pruned LayeredReplay audit.
LIGHT_CLOSURE_NAMES = EXPECTED_NAMES[:4]
EXPECTED_LIGHT_CLOSURES: dict[str, tuple[int, int, int, int, int]] = {
    "scaled_factor_square_identity": (128, 18, 116, 127, 12),
    "thirty_two_square_eq_twice_sixteen_times_thirty_two": (
        467,
        59,
        455,
        466,
        12,
    ),
    "floor_sqrt_factorized_threshold_thirty_two": (
        1_941,
        60,
        1_025,
        1_071,
        47,
    ),
    "six_block_window_decomposition_above_thirty_two": (
        694,
        53,
        441,
        468,
        28,
    ),
}

# Row five is audited separately from the final envelope.  Its first isolated
# root-pruned LayeredReplay pass must print a complete topology and closure
# receipt before this placeholder can be replaced.  Leaving the placeholder
# in place is intentionally a failing gate, never a skipped closure claim.
HEAVY_ITERATOR_ROOT = "bertrand_hj_six_block_iterate_from_total"
BALANCED_SEED_PROVIDER_NAMES = (
    "eight_times_eight_eq_sixty_four",
    "eight_times_sixteen_eq_one_twenty_eight",
    "pow_two_seed_bundle_from_total",
)
BALANCED_SEED_PROVIDER_SOURCE_SHA256 = (
    "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
)
PENDING_HEAVY_ITERATOR_LAYERED_AUDIT = (
    "PENDING_HEAVY_ITERATOR_LAYERED_AUDIT"
)
EXPECTED_HEAVY_ITERATOR_LAYERED_AUDIT: dict[str, object] | str = {
    "topology_sha256": (
        "dbaf90bdf12ee69c96d5b06ffb0d9040de9c538dc64b06405c4075f3b87f49b7"
    ),
    "balanced_seed_provider_names": (
        "eight_times_eight_eq_sixty_four",
        "eight_times_sixteen_eq_one_twenty_eight",
        "pow_two_seed_bundle_from_total",
    ),
    "balanced_seed_provider_source_sha256": (
        "76f290ee51d70fe62b14d81777488f5823050597249a9aa1beafcfdaad894eab"
    ),
    "balanced_seed_provider_script_sha256": (
        "2b83f8e5ff38b9fd620570de270cbd79e928b933ac49e0db4a5ac042e69d267b"
    ),
    "balanced_seed_provider_logical_sha256": (
        "2f16ad95b11aa3044770df1f3312bfefb3c0fd2aa32f1da2403641daa97f12ea"
    ),
    "candidate_pool_count": 84,
    "unreachable_candidate_count": 31,
    "unreachable_candidate_names_sha256": (
        "518cacc189c1f6730510a2ce86ca6ec6dc5d2b628b77728de3f255a9f127ed54"
    ),
    "node_count": 87,
    "stable_atomic_count": 34,
    "candidate_body_count": 53,
    "dependency_edge_count": 288,
    "layer_sizes": (35, 13, 13, 8, 5, 4, 7, 1, 1),
    "max_fan_in": 13,
    "raw_body_union_objects": 97_700,
    "interned_body_union_objects": 11_718,
    "body_union_object_savings": 85_982,
    "proof_nodes": 134_034,
    "proof_depth": 179,
    "proof_objects": 13_633,
    "proof_edges": 18_279,
    "reused_objects": 4_647,
    "annotation_occurrences": 892_269,
    "envelope_depth": 208,
    "package_formula_occurrences": 32_239,
    "package_formula_depth": 147,
    "proof_dag_sha256": (
        "1d2a6ff4398f14ee3a793c9adfb8f59bb29320e79b1dda186f0a88c878df06b3"
    ),
}


@dataclass(frozen=True, slots=True)
class _HeavyIteratorBlueprint:
    """Root-pruned local-ID graph with Stable proofs as atomic leaves."""

    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    kinds: tuple[str, ...]
    root: int
    topology_sha256: str


STATEMENT_RECEIPTS_READY = isinstance(EXPECTED_STATEMENTS, dict)
BODY_RECEIPTS_READY = isinstance(EXPECTED_BODIES, dict)
ARTIFACT_RECEIPTS_READY = isinstance(EXPECTED_ARTIFACT_SHA256, dict)
REPLAY_AUDIT_READY = (
    STATEMENT_RECEIPTS_READY
    and BODY_RECEIPTS_READY
    and ARTIFACT_RECEIPTS_READY
)

LIVENESS_CASES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
FALSE_TARGET_CASES = EXPECTED_NAMES

BOUNDARY_MUTATION_CASES = (
    (
        "scaled_identity__boundary__successor_square",
        "scaled_factor_square_identity",
        "a * a = c * (d * a)",
        "S (a * a) = c * (d * a)",
    ),
    (
        "factorized_bridge__boundary__factor_three",
        "thirty_two_square_eq_twice_sixteen_times_thirty_two",
        "32 * 32 = 2 * (16 * 32)",
        "32 * 32 = 3 * (16 * 32)",
    ),
    (
        "threshold__boundary__root_thirty_three",
        "floor_sqrt_factorized_threshold_thirty_two",
        witness_le("32", "s", tag="hjas_threshold_result"),
        witness_le("33", "s", tag="hjas_threshold_result"),
    ),
    (
        "decomposition__boundary__upper_thirty_six",
        "six_block_window_decomposition_above_thirty_two",
        witness_le("b", "37", tag="hjas_decomposition_base_upper"),
        witness_le("b", "36", tag="hjas_decomposition_base_upper"),
    ),
    (
        "iterator__boundary__reverse_h_result",
        "bertrand_hj_six_block_iterate_from_total",
        witness_le("h", "u", tag="hjas_iterator_h_result"),
        witness_le("u", "h", tag="hjas_iterator_h_result"),
    ),
    (
        "envelope__boundary__reverse_j_result",
        "bertrand_hj_envelope_thirty_two",
        witness_le("j", "g", tag="hjas_envelope_j_result"),
        witness_le("g", "j", tag="hjas_envelope_j_result"),
    ),
)

EXPECTED_MANIFEST_COUNTS = {
    "theorems": 6,
    "declared_dependencies": 24,
    "liveness_cases": 24,
    "false_target_cases": 6,
    "boundary_mutation_cases": 6,
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
        *make_bertrand_hj_transport_candidate_theorems(TheoremSpec),
        *make_bertrand_hj_base_thirty_two_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_all_s_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


@lru_cache(maxsize=1)
def _heavy_iterator_balanced_seed_provider() -> tuple[TheoremSpec, ...]:
    """Freeze the local-only shallow provider and its exact replacement."""

    rows = balanced_seed_provider.make_bertrand_power_seed_balanced_candidate_theorems(
        TheoremSpec
    )
    assert tuple(item.name for item in rows) == BALANCED_SEED_PROVIDER_NAMES
    assert len({item.name for item in rows}) == len(rows)
    assert not (set(BALANCED_SEED_PROVIDER_NAMES) & set(_specs_by_name()))
    assert sha256(
        Path(balanced_seed_provider.__file__).read_bytes()
    ).hexdigest() == BALANCED_SEED_PROVIDER_SOURCE_SHA256

    old_rows = tuple(
        item
        for item in _prior_specs()
        if item.name == BALANCED_SEED_PROVIDER_NAMES[-1]
    )
    assert len(old_rows) == 1
    old_seed = old_rows[0]
    replacement = rows[-1]
    assert replacement.name == old_seed.name
    assert replacement.statement == old_seed.statement
    assert replacement.dependencies != old_seed.dependencies
    assert replacement.script != old_seed.script
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
def _heavy_iterator_candidate_pool() -> tuple[TheoremSpec, ...]:
    """Substitute the shallow seed only in the heavy row-five graph."""

    prior = _prior_specs()
    provider = _heavy_iterator_balanced_seed_provider()
    seed_name = BALANCED_SEED_PROVIDER_NAMES[-1]
    old_seeds = tuple(item for item in prior if item.name == seed_name)
    assert len(old_seeds) == 1
    old_seed = old_seeds[0]
    old_index = prior.index(old_seed)
    replaced_prior = (
        *prior[:old_index],
        *provider,
        *prior[old_index + 1 :],
    )
    assert replaced_prior[:old_index] == prior[:old_index]
    assert replaced_prior[old_index : old_index + len(provider)] == provider
    assert replaced_prior[old_index + len(provider) :] == prior[old_index + 1 :]
    assert all(item is not old_seed for item in replaced_prior)
    assert sum(item.name == seed_name for item in replaced_prior) == 1

    rows = (*replaced_prior, *_specs()[:5])
    assert len({item.name for item in rows}) == len(rows)
    assert all(item is not old_seed for item in rows)
    assert rows[old_index : old_index + len(provider)] == provider
    return rows


@lru_cache(maxsize=1)
def _heavy_iterator_blueprint() -> _HeavyIteratorBlueprint:
    """Prune row five at its root and stop at the Stable boundary."""

    public = _specs_by_name()
    candidates = {
        item.name: item for item in _heavy_iterator_candidate_pool()
    }
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
            raise AssertionError(f"unknown heavy iterator dependency {name!r}")
        mark = marks.get(name, 0)
        if mark == 1:
            raise AssertionError(
                f"cyclic heavy iterator dependency at {name!r}"
            )
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(HEAVY_ITERATOR_ROOT)
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
                "heavy iterator dependency did not precede its node"
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

    rows = (
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
    return _HeavyIteratorBlueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        kinds=kinds,
        root=positions[HEAVY_ITERATOR_ROOT],
        topology_sha256=sha256("\x1c".join(rows).encode()).hexdigest(),
    )


def _heavy_iterator_dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
    """Build one checked candidate body without closing its dependencies."""

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
                f"heavy iterator body {item.name!r} delegated through use"
            )
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=1)
def _heavy_iterator_bundle() -> LayeredReplayBundle:
    """Attach each Stable proof or candidate body exactly once."""

    blueprint = _heavy_iterator_blueprint()
    public = _specs_by_name()
    candidates = {
        item.name: item for item in _heavy_iterator_candidate_pool()
    }
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
            body = _heavy_iterator_dependency_curried_body(
                candidates[name],
                targets_by_name,
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
            blueprint.names,
            blueprint.kinds,
            strict=True,
        )
        if kind == "candidate_body"
    )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


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


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        theorem = replay(name)
        return theorem.formula, theorem.certificate

    item = _local()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body

    formula = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _close(dependency)
        body = Cut(dependency_formula, formula, dependency_proof, body)
    return formula, body


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
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _proof_union_object_count(proofs: tuple[Proof, ...]) -> int:
    """Count immutable proof identities once across several body roots."""

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
    """Hash an immutable proof DAG by constructor and child content."""

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
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def test_hj_all_s_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_hj_all_s_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == EXPECTED_SURFACES

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
                "FloorSqrt(",
                "^",
                "**",
                "<=",
            )
        )


def test_hj_all_s_threshold_retains_the_factorized_native_carrier() -> None:
    specs = {item.name: item for item in _specs()}
    identity = specs["scaled_factor_square_identity"]
    bridge = specs["thirty_two_square_eq_twice_sixteen_times_thirty_two"]
    threshold = specs["floor_sqrt_factorized_threshold_thirty_two"]
    assert identity.statement == (
        "forall c d a. a = c * d -> a * a = c * (d * a)"
    )
    assert bridge.statement == "32 * 32 = 2 * (16 * 32)"
    assert threshold.statement == _threshold_statement()
    for item in specs.values():
        assert "512" not in item.statement
        assert all("512" not in command for command in item.script)


def test_hj_all_s_threshold_value_is_host_regression_only() -> None:
    # This standard-natural calculation documents the RFC representation; it
    # is neither imported into a native proof nor accepted as kernel authority.
    assert 16 * 32 == 512
    assert 32 * 32 == 2 * (16 * 32)


def test_hj_all_s_block_surfaces_preserve_one_total_then_discharge_it() -> None:
    specs = {item.name: item for item in _specs()}
    decomposition = specs["six_block_window_decomposition_above_thirty_two"]
    iterator = specs["bertrand_hj_six_block_iterate_from_total"]
    envelope = specs["bertrand_hj_envelope_thirty_two"]

    assert decomposition.statement == _decomposition_statement()
    total = power_total_relation(tag="hjas_iterator")
    assert iterator.statement == _iterator_statement()
    assert iterator.statement.count(total) == 1
    assert envelope.statement == _envelope_statement()
    assert "bpt_a_" not in envelope.statement
    assert envelope.dependencies[0] == "pow_exists"
    assert sum(command.startswith("have htotal :") for command in envelope.script) == 1


def test_hj_all_s_scripts_are_constructive_and_deterministic() -> None:
    first = _specs()
    second = make_bertrand_hj_all_s_candidate_theorems(TheoremSpec)
    assert tuple(item.script for item in first) == tuple(item.script for item in second)
    for item in first:
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


def test_hj_all_s_static_audit_manifests_are_frozen() -> None:
    assert len(EXPECTED_NAMES) == EXPECTED_MANIFEST_COUNTS["theorems"]
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(CHECKPOINT_BODY_RECEIPTS) == EXPECTED_NAMES
    assert all(len(receipt) == 7 for receipt in CHECKPOINT_BODY_RECEIPTS.values())
    assert sum(len(row) for row in EXPECTED_DEPENDENCIES.values()) == (
        EXPECTED_MANIFEST_COUNTS["declared_dependencies"]
    )
    assert len(LIVENESS_CASES) == EXPECTED_MANIFEST_COUNTS["liveness_cases"]
    assert len(FALSE_TARGET_CASES) == (
        EXPECTED_MANIFEST_COUNTS["false_target_cases"]
    )
    assert len(BOUNDARY_MUTATION_CASES) == (
        EXPECTED_MANIFEST_COUNTS["boundary_mutation_cases"]
    )

    liveness_ids = tuple(
        f"{name}__without__{dependency}"
        for name, dependency in LIVENESS_CASES
    )
    false_ids = tuple(f"{name}__false_target" for name in FALSE_TARGET_CASES)
    boundary_ids = tuple(case_id for case_id, *_rest in BOUNDARY_MUTATION_CASES)
    for ids in (liveness_ids, false_ids, boundary_ids):
        assert len(ids) == len(set(ids))
    all_ids = (*liveness_ids, *false_ids, *boundary_ids)
    assert len(all_ids) == len(set(all_ids))

    surfaces = {item.name: item.statement for item in _specs()}
    for _case_id, name, old, new in BOUNDARY_MUTATION_CASES:
        assert old != new
        assert old in surfaces[name]
        assert surfaces[name].replace(old, new, 1) != surfaces[name]


@pytest.mark.parametrize(
    ("receipt_class", "receipts"),
    (
        ("statement fingerprints", EXPECTED_STATEMENTS),
        ("body receipts", EXPECTED_BODIES),
        ("script/logical-spec fingerprints", EXPECTED_ARTIFACT_SHA256),
        ("closure receipts", EXPECTED_CLOSURES),
    ),
    ids=("statements", "bodies", "artifacts", "closures"),
)
def test_hj_all_s_candidate_only_receipt_gate_is_fail_closed(
    receipt_class: str,
    receipts: object,
) -> None:
    assert receipts != PENDING_CANDIDATE_ONLY, (
        f"{receipt_class} remain candidate-only pending; run their isolated "
        "audit before admission"
    )
    assert isinstance(receipts, dict)
    assert tuple(receipts) == EXPECTED_NAMES


@pytest.mark.skipif(
    not STATEMENT_RECEIPTS_READY,
    reason="statement fingerprints await the first successful isolated replay",
)
def test_hj_all_s_statement_fingerprints_are_frozen() -> None:
    assert isinstance(EXPECTED_STATEMENTS, dict)
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in _specs()
    } == EXPECTED_STATEMENTS


@pytest.mark.skipif(
    not ARTIFACT_RECEIPTS_READY,
    reason="script/logical-spec fingerprints await isolated factory inspection",
)
def test_hj_all_s_script_and_logical_spec_fingerprints_are_frozen() -> None:
    assert isinstance(EXPECTED_ARTIFACT_SHA256, dict)
    assert {
        item.name: (
            sha256("\0".join(item.script).encode()).hexdigest(),
            sha256(
                "\0".join((item.statement, *item.dependencies)).encode()
            ).hexdigest(),
        )
        for item in _specs()
    } == EXPECTED_ARTIFACT_SHA256


@pytest.mark.skipif(
    not isinstance(EXPECTED_CLOSURES, dict),
    reason="closure receipts remain a later candidate-only isolated gate",
)
def test_hj_all_s_closure_receipts_require_the_isolated_closure_gate() -> None:
    assert isinstance(EXPECTED_CLOSURES, dict)
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    pytest.fail(
        "candidate-only closure receipts are not admissible until the isolated "
        "closure validator is wired"
    )


@pytest.mark.parametrize("name", LIGHT_CLOSURE_NAMES, ids=LIGHT_CLOSURE_NAMES)
def test_hj_all_s_light_closure_is_checked_and_frozen(name: str) -> None:
    item = next(item for item in _specs() if item.name == name)
    formula, certificate = _close(name)
    assert check((), certificate, formula)
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    receipt = (nodes, depth, objects, edges, reused)
    assert nodes < MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects < MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(certificate))
    for index in range(len(item.dependencies)):
        assert not check((), _mutate_direct_cut(certificate, index), formula)
    assert name in EXPECTED_LIGHT_CLOSURES, (
        f"freeze light closure receipt for {name}: {receipt!r}"
    )
    assert receipt == EXPECTED_LIGHT_CLOSURES[name]


def test_hj_all_s_row_five_root_pruned_layered_empty_context_closure() -> None:
    """Audit only the heavy iterator root in one isolated process."""

    blueprint = _heavy_iterator_blueprint()
    public = _specs_by_name()
    pool = _heavy_iterator_candidate_pool()
    provider = _heavy_iterator_balanced_seed_provider()
    candidates = {item.name: item for item in pool}
    stable_names = {
        name
        for name, kind in zip(
            blueprint.names,
            blueprint.kinds,
            strict=True,
        )
        if kind == "stable_atomic"
    }
    candidate_names = set(blueprint.names) - stable_names
    pool_names = set(candidates)
    unreachable_candidates = pool_names - set(blueprint.names)

    old_seed = next(
        item
        for item in _prior_specs()
        if item.name == BALANCED_SEED_PROVIDER_NAMES[-1]
    )
    assert pool[-5:] == _specs()[:5]
    assert tuple(
        item for item in pool if item.name in BALANCED_SEED_PROVIDER_NAMES
    ) == provider
    assert all(item is not old_seed for item in pool)
    assert BALANCED_SEED_PROVIDER_NAMES[-1] not in public
    assert stable_names <= set(public)
    assert not (candidate_names & set(public))
    assert candidate_names <= pool_names
    assert set(BALANCED_SEED_PROVIDER_NAMES) <= candidate_names
    assert blueprint.kinds == (
        ("stable_atomic",) * len(stable_names)
        + ("candidate_body",) * len(candidate_names)
    )
    assert blueprint.names[blueprint.root] == HEAVY_ITERATOR_ROOT
    assert blueprint.targets[blueprint.root] == _closed_formula(
        _specs()[4].statement
    )
    assert "bertrand_hj_envelope_thirty_two" not in candidates
    assert "bertrand_hj_envelope_thirty_two" not in blueprint.names
    assert tuple(
        blueprint.names[dependency]
        for dependency in blueprint.dependencies[blueprint.root]
    ) == EXPECTED_DEPENDENCIES[HEAVY_ITERATOR_ROOT]
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
    assert len(blueprint.names) <= DEFAULT_LAYERED_REPLAY_LIMITS.max_nodes
    assert (
        sum(map(len, blueprint.dependencies))
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_dependency_edges
    )
    assert (
        max(map(len, blueprint.dependencies))
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_dependencies_per_node
    )

    raw_bundle = _heavy_iterator_bundle()
    interned_bundle = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert type(interned_bundle) is LayeredReplayBundle
    assert interned_bundle.root == raw_bundle.root
    assert len(interned_bundle.nodes) == len(raw_bundle.nodes)
    for raw_node, interned_node in zip(
        raw_bundle.nodes,
        interned_bundle.nodes,
        strict=True,
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
    body_union_object_savings = (
        raw_body_union_objects - interned_body_union_objects
    )
    assert body_union_object_savings > 0
    print(
        "BERTRAND HJ ROW FIVE BODY INTERNING "
        f"raw_body_union_objects={raw_body_union_objects} "
        f"interned_body_union_objects={interned_body_union_objects} "
        f"savings={body_union_object_savings}",
        flush=True,
    )

    targets_by_id = {
        node.node_id: node.target for node in interned_bundle.nodes
    }
    for node in interned_bundle.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(targets_by_id[dependency], body_target)
        assert check((), node.body, body_target), (
            "interned heavy iterator body failed its exact dependency-curried "
            f"kernel judgment at node {node.node_id} "
            f"({blueprint.names[node.node_id]!r})"
        )

    compilation = compile_layered_replay(
        interned_bundle,
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert type(compilation) is LayeredReplayCandidate
    assert compilation.target == blueprint.targets[blueprint.root]
    assert compilation.layers == blueprint.layers
    assert len(compilation.package_formulas) == len(blueprint.layers)
    assert (
        compilation.package_formula_occurrences
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_package_formula_occurrences
    )
    assert (
        compilation.maximum_package_formula_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_package_formula_depth
    )
    assert (
        compilation.proof_nodes
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
    )
    assert (
        compilation.proof_objects
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_objects
    )
    assert (
        compilation.proof_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_depth
    )
    assert (
        compilation.proof_annotation_occurrences
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_annotation_occurrences
    )
    assert (
        compilation.proof_envelope_depth
        <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_envelope_depth
    )
    assert compilation.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert compilation.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert compilation.proof_objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(
        type(node) is DNE for node in _walk(compilation.certificate)
    )

    proof_dag_sha256 = _proof_dag_sha256(compilation.certificate)
    provider_source_sha256 = sha256(
        Path(balanced_seed_provider.__file__).read_bytes()
    ).hexdigest()
    assert provider_source_sha256 == BALANCED_SEED_PROVIDER_SOURCE_SHA256
    provider_script_sha256 = _provider_script_sha256(provider)
    provider_logical_sha256 = _provider_logical_sha256(provider)
    kernel_accepted = check(
        (),
        compilation.certificate,
        compilation.target,
    )
    actual: dict[str, object] = {
        "topology_sha256": blueprint.topology_sha256,
        "balanced_seed_provider_names": BALANCED_SEED_PROVIDER_NAMES,
        "balanced_seed_provider_source_sha256": provider_source_sha256,
        "balanced_seed_provider_script_sha256": provider_script_sha256,
        "balanced_seed_provider_logical_sha256": provider_logical_sha256,
        "candidate_pool_count": len(pool),
        "unreachable_candidate_count": len(unreachable_candidates),
        "unreachable_candidate_names_sha256": sha256(
            "\0".join(sorted(unreachable_candidates)).encode()
        ).hexdigest(),
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
        "BERTRAND HJ ROW FIVE LAYERED CLOSURE RECEIPT "
        f"actual={actual!r} kernel_accepted={kernel_accepted}",
        flush=True,
    )
    assert kernel_accepted
    assert isinstance(EXPECTED_HEAVY_ITERATOR_LAYERED_AUDIT, dict), (
        "freeze the isolated row-five LayeredReplay receipt only after the "
        f"kernel accepts it: {actual!r}"
    )
    assert actual == EXPECTED_HEAVY_ITERATOR_LAYERED_AUDIT


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="body receipts await the first successful isolated replay",
)
@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_hj_all_s_bodies_are_constructive(name: str) -> None:
    assert isinstance(EXPECTED_BODIES, dict)
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


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="dependency liveness awaits the first successful isolated replay",
)
@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVENESS_CASES,
    ids=[f"{name}__without__{dependency}" for name, dependency in LIVENESS_CASES],
)
def test_hj_all_s_every_declared_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = next(item for item in _specs() if item.name == name)
    shortened = replace(
        item,
        dependencies=tuple(
            candidate for candidate in item.dependencies if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_available())


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="negative replay awaits the first successful isolated replay",
)
@pytest.mark.parametrize(
    "name",
    FALSE_TARGET_CASES,
    ids=[f"{name}__false_target" for name in FALSE_TARGET_CASES],
)
def test_hj_all_s_false_target_is_rejected(name: str) -> None:
    item = next(item for item in _specs() if item.name == name)
    false_contract = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_contract,), core=_available())


@pytest.mark.skipif(
    not REPLAY_AUDIT_READY,
    reason="boundary mutations await the first successful isolated replay",
)
@pytest.mark.parametrize(
    ("case_id", "name", "old", "new"),
    BOUNDARY_MUTATION_CASES,
    ids=[case_id for case_id, *_rest in BOUNDARY_MUTATION_CASES],
)
def test_hj_all_s_boundary_mutation_is_rejected(
    case_id: str,
    name: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = next(item for item in _specs() if item.name == name)
    assert old in item.statement
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    assert mutated.statement != item.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())
