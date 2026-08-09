"""Strict-HA audit for the Bertrand ceiling-by-six/floor-square tranche."""

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
    ceil_div_six_relation,
    floor_sqrt_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
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
    "ceil_div_six_shift",
    "ceil_div_six_total",
    "ceil_div_six_functional",
    "ceil_div_six_exists_unique",
    "square_six_shift_identity",
    "ceil_div_six_square_six_step",
    "floor_sqrt_lower_bound",
    "floor_sqrt_strict_upper_bound",
    "floor_sqrt_functional",
)
EXPECTED_DEPENDENCIES = {
    "ceil_div_six_shift": ("mul_add", "add_assoc", "add_comm", "add_succ_left"),
    "ceil_div_six_total": (
        "division_remainder_exists",
        "succ_ne_zero",
        "zero_or_succ",
        "zero_add",
        "lt_to_le",
        "add_le_add_left",
        "add_comm",
    ),
    "ceil_div_six_functional": (
        "lt_trichotomy",
        "add_le_add_right",
        "mul_le_mul_left",
        "lt_of_lt_of_le",
        "lt_irrefl_expanded",
    ),
    "ceil_div_six_exists_unique": (
        "ceil_div_six_total",
        "ceil_div_six_functional",
    ),
    "square_six_shift_identity": (
        "two_mul_eq_add_self",
        "mul_add",
        "add_mul",
        "mul_comm",
        "add_assoc",
    ),
    "ceil_div_six_square_six_step": (
        "ceil_div_six_shift",
        "square_six_shift_identity",
        "ceil_div_six_functional",
    ),
    "floor_sqrt_lower_bound": (),
    "floor_sqrt_strict_upper_bound": (),
    "floor_sqrt_functional": (
        "lt_trichotomy",
        "mul_le_mul_right",
        "mul_le_mul_left",
        "le_trans",
        "lt_of_lt_of_le",
        "lt_irrefl_expanded",
    ),
}
EXPECTED_STATEMENTS = {
    "ceil_div_six_shift": (
        386,
        "16902721d9f4edde9e97edbd0a9e465400501db75bb7dcbc54c342165dbc4c66",
    ),
    "ceil_div_six_total": (
        192,
        "5b2d027ec7ea85bb4cce6dcf69973cd6c949bd42bc100ab2659ed5c190424509",
    ),
    "ceil_div_six_functional": (
        399,
        "47b92c522400ca61ad962efdfaa76d76ce9897aed6eebfe0f34bf37c6f5a7f4f",
    ),
    "ceil_div_six_exists_unique": (
        413,
        "8612e551fccf92c4fcd3c0f396aa377f807ebfcfe1323a065256ee0b025737f5",
    ),
    "square_six_shift_identity": (
        53,
        "1ad3af94d3014bd7a148c11e3045efd01150f3b80e4331ee2b2b778189248816",
    ),
    "ceil_div_six_square_six_step": (
        433,
        "c472789d420a8e6af73359d2d7fb1021ab046e8f4a05ac616661fb066008d7f1",
    ),
    "floor_sqrt_lower_bound": (
        225,
        "ebf1a61c69adc2d74bd22380b06c94ca4d9441b596b8d0c691bff222d82d959c",
    ),
    "floor_sqrt_strict_upper_bound": (
        231,
        "df9fbd83265c098574a625eae9ecc7c93515d08743a606ab316ea541fb5316f2",
    ),
    "floor_sqrt_functional": (
        483,
        "5b1535d5cd594d89c22818709b0fc0f535a3053eaae4b6ba696b7d8697482893",
    ),
}
EXPECTED_BODIES = {
    "ceil_div_six_shift": (4, 39, 71, 22, 71, 70, 0),
    "ceil_div_six_total": (7, 56, 215, 45, 195, 214, 20),
    "ceil_div_six_functional": (5, 72, 87, 22, 87, 86, 0),
    "ceil_div_six_exists_unique": (2, 16, 19, 14, 19, 18, 0),
    "square_six_shift_identity": (5, 39, 64, 18, 64, 63, 0),
    "ceil_div_six_square_six_step": (3, 24, 27, 16, 27, 26, 0),
    "floor_sqrt_lower_bound": (0, 5, 12, 8, 12, 11, 0),
    "floor_sqrt_strict_upper_bound": (0, 5, 12, 8, 12, 11, 0),
    "floor_sqrt_functional": (6, 74, 94, 25, 94, 93, 0),
}
EXPECTED_CLOSURES = {
    "ceil_div_six_shift": (281, 22, 206, 222, 17),
    "ceil_div_six_total": (712, 45, 490, 541, 52),
    "ceil_div_six_functional": (460, 22, 383, 395, 13),
    "ceil_div_six_exists_unique": (1_191, 46, 837, 898, 62),
    "square_six_shift_identity": (997, 28, 361, 398, 38),
    "ceil_div_six_square_six_step": (1_765, 30, 749, 794, 46),
    "floor_sqrt_lower_bound": (12, 8, 12, 11, 0),
    "floor_sqrt_strict_upper_bound": (12, 8, 12, 11, 0),
    "floor_sqrt_functional": (817, 28, 560, 594, 35),
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_integer_envelope_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec)


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


def test_relation_builders_are_hygienic_and_compound_term_safe() -> None:
    ceiling = ceil_div_six_relation("x * x + 6", "e + 1", tag="compound")
    square = floor_sqrt_relation("2 * n", "s + 1", tag="compound")
    assert parse_formula_with_names(f"forall x e. {ceiling}")[1] == ()
    assert parse_formula_with_names(f"forall n s. {square}")[1] == ()

    with pytest.raises(ValueError, match="binder tag"):
        ceil_div_six_relation("x", "e", tag="bad-tag")
    with pytest.raises(ValueError, match="captures"):
        ceil_div_six_relation(
            "bcs_lower_gap_capture", "e", tag="capture"
        )
    with pytest.raises(ValueError, match="Peano term"):
        floor_sqrt_relation("x / 6", "s", tag="malformed")


def test_ceil_sqrt_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec) == specs
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
            for token in (
                "CeilDivSix(",
                "FloorSqrt(",
                "^",
                "<=",
                "<",
                "ceil(",
                "sqrt(",
            )
        )


def test_ceil_sqrt_bodies_are_constructive_exact_and_dependency_live() -> None:
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


def test_false_and_off_by_one_contract_mutations_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {item.name: item for item in _prior_specs()}
    for index, item in enumerate(specs):
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)

    boundary_mutations = {
        "ceil_div_six_total": _specs()[1].statement.replace(
            "= (x) + 6", "= (x) + 5"
        ),
        "ceil_div_six_square_six_step": _specs()[5].statement.replace(
            "f = e + (2 * s + 6)", "f = e + (2 * s + 5)"
        ),
        "floor_sqrt_strict_upper_bound": _specs()[7].statement.replace(
            "S s * S s", "s * s"
        ),
    }
    for name, statement in boundary_mutations.items():
        index = EXPECTED_NAMES.index(name)
        assert statement != specs[index].statement
        mutated = replace(specs[index], statement=statement)
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)


def test_ceil_sqrt_closures_and_direct_cuts_check_within_policy() -> None:
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

        for index in range(len(item.dependencies)):
            mutated = _mutate_direct_cut(certificate, index)
            assert not check((), mutated, formula)
    assert actual == EXPECTED_CLOSURES


def test_integer_relations_have_the_intended_unique_semantics() -> None:
    # Regression only: host integers are never used to produce a certificate.
    for value in range(0, 384):
        ceilings = [
            ceiling
            for ceiling in range(0, 80)
            if value <= 6 * ceiling < value + 6
        ]
        assert ceilings == [(value + 5) // 6]

    for root in range(0, 96):
        current = (root * root + 5) // 6
        successor = ((root + 6) * (root + 6) + 5) // 6
        assert successor == current + 2 * root + 6

    for value in range(0, 1_024):
        roots = [
            root
            for root in range(0, 40)
            if root * root <= value < (root + 1) * (root + 1)
        ]
        assert roots == [isqrt(value)]
