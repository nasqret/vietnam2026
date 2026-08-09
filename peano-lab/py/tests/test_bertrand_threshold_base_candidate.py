"""Strict-HA audit for the Bertrand B6 threshold/base scalar tranche."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import isqrt

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
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
)
from peano_lab.library.bertrand_threshold_base_candidate import (
    make_bertrand_threshold_base_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "forty_two_le_sixty_four",
    "forty_three_le_sixty_four",
    "seventy_le_one_twenty_eight",
    "seventy_six_le_one_twenty_eight",
    "floor_sqrt_threshold_sixty_four",
    "forty_two_successor_le_square_of_sixty_four_le",
    "ceil_square_seven_successor_lower",
    "bertrand_base_residue_linear_bounds",
)

EXPECTED_DEPENDENCIES = {
    "forty_two_le_sixty_four": ("le_add_right",),
    "forty_three_le_sixty_four": ("le_add_right",),
    "seventy_le_one_twenty_eight": ("le_add_right",),
    "seventy_six_le_one_twenty_eight": ("le_add_right",),
    "floor_sqrt_threshold_sixty_four": (
        "zero_add",
        "square_lt_successor_square",
        "floor_sqrt_monotone",
    ),
    "forty_two_successor_le_square_of_sixty_four_le": (
        "forty_two_le_sixty_four",
        "forty_three_le_sixty_four",
        "le_trans",
        "add_le_add_left",
        "mul_le_mul_right",
        "mul_succ_left",
    ),
    "ceil_square_seven_successor_lower": (
        "forty_two_successor_le_square_of_sixty_four_le",
        "le_trans",
        "mul_assoc",
        "succ_ne_zero",
        "mul_le_cancel_left_nonzero",
    ),
    "bertrand_base_residue_linear_bounds": (
        "add_le_add_right",
        "le_trans",
        "le_add_right",
        "forty_two_le_sixty_four",
        "seventy_le_one_twenty_eight",
        "seventy_six_le_one_twenty_eight",
    ),
}

EXPECTED_STATEMENTS = {
    "forty_two_le_sixty_four": (
        21,
        "268da28d809845795cede4d25752db01b679bd0e67eaabbe143aed59cf4c623f",
    ),
    "forty_three_le_sixty_four": (
        21,
        "e7e54619563c7f508e289adf172e968bb9b8c3170c9b6a1d7bb658108e005418",
    ),
    "seventy_le_one_twenty_eight": (
        22,
        "31f6d54a64826906e73f8859666ea9766dad23da6c9ea55e0e04a29cfe623fc6",
    ),
    "seventy_six_le_one_twenty_eight": (
        22,
        "17c5e5a36f526f5374e6a26efbd0aa2d5b75805209e5581149456ba097816ea4",
    ),
    "floor_sqrt_threshold_sixty_four": (
        397,
        "fec4e639f5b4306635ecee79298a912bdb66b434301fcba065eaeec6022b2b28",
    ),
    "forty_two_successor_le_square_of_sixty_four_le": (
        170,
        "7036244d5e3992e3d6e34cab68b59c6c26265a80b14d314433438963e8779d47",
    ),
    "ceil_square_seven_successor_lower": (
        359,
        "4cc9a8cc3cc5174a69f0a161a36e244bac79bdcb8ae2e850dfe77ff2c70e84ab",
    ),
    "bertrand_base_residue_linear_bounds": (
        418,
        "6f03817daa2faf058c1e2828e29881fba7319ffd8f26bf517ed23e25248f12f0",
    ),
}

EXPECTED_BODIES = {
    "forty_two_le_sixty_four": (1, 31, 120, 28, 120, 119, 0),
    "forty_three_le_sixty_four": (1, 30, 115, 27, 115, 114, 0),
    "seventy_le_one_twenty_eight": (1, 67, 300, 64, 300, 299, 0),
    "seventy_six_le_one_twenty_eight": (1, 61, 270, 58, 270, 269, 0),
    "floor_sqrt_threshold_sixty_four": (3, 18, 23, 15, 23, 22, 0),
    "forty_two_successor_le_square_of_sixty_four_le": (
        6,
        50,
        58,
        18,
        58,
        57,
        0,
    ),
    "ceil_square_seven_successor_lower": (5, 35, 339, 50, 339, 338, 0),
    "bertrand_base_residue_linear_bounds": (6, 68, 106, 25, 106, 105, 0),
}

EXPECTED_CLOSURES = {
    "forty_two_le_sixty_four": (200, 28, 194, 199, 6),
    "forty_three_le_sixty_four": (195, 27, 189, 194, 6),
    "seventy_le_one_twenty_eight": (380, 64, 374, 379, 6),
    "seventy_six_le_one_twenty_eight": (350, 58, 344, 349, 6),
    "floor_sqrt_threshold_sixty_four": (1_369, 32, 629, 668, 40),
    "forty_two_successor_le_square_of_sixty_four_le": (
        1_160,
        31,
        633,
        669,
        37,
    ),
    "ceil_square_seven_successor_lower": (2_352, 50, 1_305, 1_357, 53),
    "bertrand_base_residue_linear_bounds": (1_223, 69, 939, 953, 15),
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
        *make_bertrand_quotient_budget_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_threshold_base_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


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


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def test_threshold_base_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_threshold_base_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENTS

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "FloorSqrt(",
                "CeilDivSix(",
                "Pow(",
                "<=",
                "^",
                "sqrt(",
                "ceil(",
            )
        )


def test_threshold_base_bodies_are_constructive_and_every_edge_is_live() -> None:
    core = dict(_specs_by_name()) | {item.name: item for item in _prior_specs()}
    receipts = replay_candidate_bodies(_specs(), core=core)
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODIES

    commands = tuple(command for item in _specs() for command in item.script)
    assert all(
        forbidden not in command
        for command in commands
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
    available = core | {item.name: item for item in _specs()}
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


def test_threshold_base_false_and_off_by_one_contracts_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {item.name: item for item in _prior_specs()}
    available = core | {item.name: item for item in specs}

    for item in specs:
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=available)

    mutations = {
        "forty_two_le_sixty_four": specs[0].statement.replace("= 64", "= 63"),
        "forty_three_le_sixty_four": specs[1].statement.replace("= 64", "= 63"),
        "seventy_le_one_twenty_eight": specs[2].statement.replace(
            "= 128", "= 127"
        ),
        "seventy_six_le_one_twenty_eight": specs[3].statement.replace(
            "= 128", "= 127"
        ),
        "floor_sqrt_threshold_sixty_four": specs[4].statement.replace(
            "+ (64) = (s)", "+ (65) = (s)"
        ),
        "forty_two_successor_le_square_of_sixty_four_le": specs[5].statement.replace(
            "42 * (s + 1)", "43 * (s + 1)"
        ),
        "ceil_square_seven_successor_lower": specs[6].statement.replace(
            "7 * (s + 1)", "8 * (s + 1)"
        ),
        "bertrand_base_residue_linear_bounds": specs[7].statement.replace(
            "s + 7", "s + 8"
        ),
    }
    assert set(mutations) == set(EXPECTED_NAMES)
    for item in specs:
        mutated = replace(item, statement=mutations[item.name])
        assert mutated.statement != item.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=available)


def test_threshold_base_closures_and_every_direct_cut_mutation() -> None:
    actual: dict[str, tuple[int, int, int, int, int]] = {}
    cut_mutations = 0
    for item in _specs():
        formula, certificate = _close(item.name)
        assert check((), certificate, formula)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        actual[item.name] = (nodes, depth, objects, edges, reused)
        assert nodes <= MAX_LIVE_PROOF_NODES
        assert depth <= MAX_LIVE_PROOF_DEPTH
        assert objects <= MAX_LIVE_PROOF_OBJECTS
        assert not any(type(node) is DNE for node in _walk(certificate))
        for index in range(len(item.dependencies)):
            mutated = _mutate_direct_cut(certificate, index)
            assert not check((), mutated, formula)
            cut_mutations += 1

    assert actual == EXPECTED_CLOSURES
    assert cut_mutations == sum(len(item.dependencies) for item in _specs()) == 24


def test_threshold_base_integer_oracles_are_regression_only() -> None:
    # Host arithmetic is a bounded regression oracle, never certificate authority.
    for root in range(64, 70):
        assert 42 * (root + 1) <= root * root
        ceiling = (root * root + 5) // 6
        assert 7 * (root + 1) <= ceiling
        assert root + 1 <= 128
        assert root + 7 <= 128
        assert 42 <= root + 5

    for value in range(2_048, 2_112):
        root = isqrt(2 * value)
        assert 64 * 64 <= 2 * value
        assert 64 <= root
