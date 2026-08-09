"""Strict-HA and capacity audit for the first Bertrand B6 envelope spike."""

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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
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
    "two_mul_eq_add_self",
    "pow_mul_base",
    "pow_two_base_two_value_four",
    "pow_two_twelve_eq_pow_four_six",
    "bertrand_guard_six_step_transport",
)
EXPECTED_DEPENDENCIES = {
    "two_mul_eq_add_self": ("mul_comm", "mul_one"),
    "pow_mul_base": (
        "pow_zero",
        "pow_successor_decompose",
        "mul_one",
        "mul_assoc",
        "mul_comm",
    ),
    "pow_two_base_two_value_four": ("pow_two",),
    "pow_two_twelve_eq_pow_four_six": (
        "pow_exists",
        "pow_two_base_two_value_four",
        "pow_mul_exp",
    ),
    "bertrand_guard_six_step_transport": (
        "pow_exists",
        "pow_base_monotone",
        "pow_mul_base",
        "pow_two_twelve_eq_pow_four_six",
        "pow_add",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "add_assoc",
        "add_comm",
        "two_mul_eq_add_self",
    ),
}
EXPECTED_STATEMENTS = {
    "two_mul_eq_add_self": (
        23,
        "c2fb8e5dff4b74e69f8d470029d5dbc303a896aa10bc95323c79e6e392f271d2",
    ),
    "pow_mul_base": (
        8_160,
        "63b9f50fccf4f8960a7c7963f0c9c1533a99ef0091138ad77bb039e6e046289e",
    ),
    "pow_two_base_two_value_four": (
        2_550,
        "921031a46f247977e3f2db871e8cfd927bde5d667c179331a4ab3901825ba9e3",
    ),
    "pow_two_twelve_eq_pow_four_six": (
        5_387,
        "7ee397ffb7b25b82ea6ba4a72357b71a02b1cfe75b6305649f517eabda795336",
    ),
    "bertrand_guard_six_step_transport": (
        11_892,
        "ee621c001ddfe54c1023b1cfe2f44026eb5f98c470aaff667580cb69755e33af",
    ),
}
EXPECTED_BODIES = {
    "two_mul_eq_add_self": (2, 7, 20, 10, 20, 19, 0),
    "pow_mul_base": (5, 110, 147, 33, 147, 146, 0),
    "pow_two_base_two_value_four": (1, 12, 65, 17, 65, 64, 0),
    "pow_two_twelve_eq_pow_four_six": (3, 32, 170, 40, 170, 169, 0),
    "bertrand_guard_six_step_transport": (11, 99, 489, 100, 428, 488, 61),
}


@lru_cache(maxsize=1)
def _order_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_order_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_integer_envelope_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_order_specs(), *_specs())
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


def test_integer_envelope_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_integer_envelope_candidate_theorems(TheoremSpec) == specs
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
            for token in ("Pow(", "FloorSqrt(", "^", "<=", "ceil")
        )


def test_integer_envelope_bodies_are_constructive_exact_and_dependency_live() -> None:
    core = dict(_specs_by_name()) | {item.name: item for item in _order_specs()}
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
        for forbidden in ("DNE", "classical", "by_contra", "sorry", "auto")
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


def test_integer_envelope_false_contracts_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in _order_specs()
    }
    for index, item in enumerate(specs):
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        candidate_stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(candidate_stack, core=core)


def test_integer_envelope_closures_check_within_live_policy() -> None:
    expected = {
        "two_mul_eq_add_self": (275, 25, 234, 258, 25),
        "pow_mul_base": (4_283, 65, 1_180, 1_232, 53),
        "pow_two_base_two_value_four": (6_525, 69, 1_200, 1_247, 48),
        "pow_two_twelve_eq_pow_four_six": (136_994, 94, 6_149, 6_415, 267),
        "bertrand_guard_six_step_transport": (213_731, 100, 6_875, 7_225, 351),
    }
    actual: dict[str, tuple[int, int, int, int, int]] = {}
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
    assert actual == expected

    formula, guard = _close("bertrand_guard_six_step_transport")
    mutated = _mutate_direct_cut(guard, 3)
    assert not check((), mutated, formula)


def test_six_step_invariant_and_target_reduction_hold_as_semantic_oracles() -> None:
    # Regression only: these integer computations are not certificate authority.
    def ceil_div(value: int, divisor: int) -> int:
        return (value + divisor - 1) // divisor

    for square_root in range(32, 160):
        guard = (square_root + 7) ** 12 <= 4 ** (square_root + 5)
        assert guard
        if square_root + 6 < 160:
            assert (square_root + 13) ** 12 <= 2**12 * (square_root + 7) ** 12
            assert 2**12 == 4**6
            assert (square_root + 13) ** 12 <= 4 ** (square_root + 11)

        envelope = (square_root + 1) ** (2 * square_root + 2)
        assert envelope <= 4 ** ceil_div(square_root * square_root, 6)
        next_envelope = (square_root + 7) ** (2 * square_root + 14)
        assert next_envelope <= envelope * 4 ** (2 * square_root + 6)

    for value in range(512, 8_192):
        square_root = isqrt(2 * value)
        quotient = (2 * value) // 3
        complement = value - quotient
        ceiling_square_budget = ceil_div(square_root * square_root, 6)
        envelope = (square_root + 1) ** (2 * square_root + 2)
        assert value * (2 * value) ** square_root <= envelope
        assert ceiling_square_budget <= complement
        assert envelope <= 4**ceiling_square_budget <= 4**complement
        assert value * (2 * value) ** square_root * 4**quotient <= 4**value
