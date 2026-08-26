"""Strict-HA audit for constructive FloorSqrt totality and monotonicity."""

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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
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
    "square_lt_successor_square",
    "floor_sqrt_total",
    "floor_sqrt_exists_unique",
    "floor_sqrt_monotone",
)
EXPECTED_DEPENDENCIES = {
    "square_lt_successor_square": (
        "le_succ_self",
        "mul_le_mul_right",
        "succ_ne_zero",
        "mul_lt_mul_succ_left_nonzero",
        "lt_of_le_of_lt",
    ),
    "floor_sqrt_total": (
        "square_lt_successor_square",
        "le_eq_or_lt",
        "zero_add",
        "le_succ",
    ),
    "floor_sqrt_exists_unique": (
        "floor_sqrt_total",
        "floor_sqrt_functional",
    ),
    "floor_sqrt_monotone": (
        "le_or_lt",
        "mul_le_mul_right",
        "mul_le_mul_left",
        "le_trans",
        "lt_of_lt_of_le",
        "lt_not_le",
    ),
}
EXPECTED_STATEMENTS = {
    "square_lt_successor_square": (
        45,
        "e1fcfaa278608620cc59e0ba9665583b5adf2c54d7a94aed6925c184adb36987",
    ),
    "floor_sqrt_total": (
        214,
        "84165f63e36f9fd3955bc6c05678f0cf5bc63f1464a0d97b7464a1bd0db6d224",
    ),
    "floor_sqrt_exists_unique": (
        457,
        "c066330f9a13c9602b00857e49528e1b36281849f2d2778ebee0d8875d13829a",
    ),
    "floor_sqrt_monotone": (
        468,
        "b89d86b820605ec51f29e79e680c5bee0aa461e573c0d3070dd8203d58cea833",
    ),
}
EXPECTED_BODIES = {
    "square_lt_successor_square": (5, 16, 28, 13, 28, 27, 0),
    "floor_sqrt_total": (4, 32, 96, 18, 96, 95, 0),
    "floor_sqrt_exists_unique": (2, 16, 19, 14, 19, 18, 0),
    "floor_sqrt_monotone": (6, 46, 59, 25, 59, 58, 0),
}
EXPECTED_CLOSURES = {
    "square_lt_successor_square": (592, 28, 379, 413, 35),
    "floor_sqrt_total": (843, 29, 542, 580, 39),
    "floor_sqrt_exists_unique": (1_679, 30, 841, 884, 44),
    "floor_sqrt_monotone": (737, 29, 507, 540, 34),
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec)


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


def test_floor_sqrt_total_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENTS

    public = _specs_by_name()
    for item in specs:
        assert item.name not in public
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("FloorSqrt(", "sqrt(", "^", "<=", "<")
        )


def test_floor_sqrt_total_bodies_are_constructive_and_dependency_live() -> None:
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


def test_false_and_floor_boundary_mutations_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {item.name: item for item in _prior_specs()}
    for index, item in enumerate(specs):
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)

    boundary_mutations = {
        "square_lt_successor_square": specs[0].statement.replace(
            "S (s * s)", "S (S (s * s))"
        ),
        "floor_sqrt_total": specs[1].statement.replace(
            "S (s) * S (s)", "(s) * (s)"
        ),
        "floor_sqrt_monotone": specs[3].statement.replace(
            "exists k. k + s = t", "exists k. k + S s = t"
        ),
    }
    for name, statement in boundary_mutations.items():
        index = EXPECTED_NAMES.index(name)
        assert statement != specs[index].statement
        mutated = replace(specs[index], statement=statement)
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)


def test_floor_sqrt_total_closures_and_cuts_check_within_policy() -> None:
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
            cut_mutations += 1
            mutated = _mutate_direct_cut(certificate, index)
            assert not check((), mutated, formula)
    assert cut_mutations == 17
    assert actual == EXPECTED_CLOSURES


def test_floor_sqrt_induction_and_monotonicity_semantic_oracles() -> None:
    # Regression only: these host calculations never produce proof objects.
    previous = 0
    for value in range(0, 4_096):
        root = isqrt(value)
        assert root * root <= value < (root + 1) * (root + 1)
        assert previous <= root
        if value > 0:
            assert root in (previous, previous + 1)
            assert (root == previous + 1) == (value == root * root)
        previous = root

    for left in range(0, 256):
        for right in range(left, 256):
            assert isqrt(left) <= isqrt(right)
