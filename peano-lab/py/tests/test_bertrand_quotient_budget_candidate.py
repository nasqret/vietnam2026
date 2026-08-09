"""Strict-HA audit for the Bertrand quotient/complement budget tranche."""

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
from peano_lab.library.bertrand_quotient_budget_candidate import (
    double_triple_divrem_relation,
    make_bertrand_quotient_budget_candidate_theorems,
    quotient_complement_budget_relation,
    witness_le,
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
    "mul_le_cancel_left_nonzero",
    "three_mul_eq_two_mul_add_self",
    "ceil_div_six_le_of_upper",
    "double_triple_remainder_complement_budget",
    "canonical_double_triple_remainder_complement_budget",
    "floor_ceil_complement_budget",
    "floor_ceil_division_budget",
)
EXPECTED_DEPENDENCIES = {
    "mul_le_cancel_left_nonzero": (
        "add_comm",
        "factor_difference",
        "mul_left_cancel_nonzero",
        "mul_add",
    ),
    "three_mul_eq_two_mul_add_self": ("mul_comm",),
    "ceil_div_six_le_of_upper": (
        "le_or_lt",
        "add_le_add_right",
        "mul_le_mul_left",
        "lt_of_lt_of_le",
        "lt_irrefl_expanded",
    ),
    "double_triple_remainder_complement_budget": (
        "mul_le_mul_right",
        "le_add_right",
        "le_trans",
        "succ_ne_zero",
        "mul_le_cancel_left_nonzero",
        "add_comm",
        "mul_add",
        "three_mul_eq_two_mul_add_self",
        "add_assoc",
        "add_left_cancel",
        "add_le_add_right",
        "mul_le_mul_left",
        "mul_assoc",
    ),
    "canonical_double_triple_remainder_complement_budget": (
        "double_triple_remainder_complement_budget",
    ),
    "floor_ceil_complement_budget": (
        "le_trans",
        "ceil_div_six_le_of_upper",
        "add_le_add_left",
    ),
    "floor_ceil_division_budget": (
        "canonical_double_triple_remainder_complement_budget",
        "floor_ceil_complement_budget",
    ),
}
EXPECTED_STATEMENTS = {
    "mul_le_cancel_left_nonzero": (
        78,
        "6dd2502cef79e8570e29c3b1ba06bf2b94da9e1673f5e6ab4f59d34d96f097a0",
    ),
    "three_mul_eq_two_mul_add_self": (
        27,
        "fd60ac7cbf2e8754e06f24d48aee124c9e6d71fffab65cf83c359b33d0f455c4",
    ),
    "ceil_div_six_le_of_upper": (
        238,
        "8611babfc5c17e21e59427c910d9edfe964c0ea98118fcf3aa1432ee7877af1d",
    ),
    "double_triple_remainder_complement_budget": (
        155,
        "bade16c5089acd290ceb24a8d396444c25d6c7163d9c0f93b3c9651a3037de4d",
    ),
    "canonical_double_triple_remainder_complement_budget": (
        365,
        "dc24b2fb213a7604f3725f1ea6eb7e15c230930d50719fcaa4e45fe1ec691c66",
    ),
    "floor_ceil_complement_budget": (
        720,
        "c89de73132e05e5e7fbd460691cc979483764db9ebdc18f246ee013ea2d45e12",
    ),
    "floor_ceil_division_budget": (
        1_043,
        "1045af75cc6d35471a6468f93e98640387a80e94f030b58c6057e0caad062931",
    ),
}
EXPECTED_BODIES = {
    "mul_le_cancel_left_nonzero": (4, 29, 40, 18, 40, 39, 0),
    "three_mul_eq_two_mul_add_self": (1, 7, 16, 8, 16, 15, 0),
    "ceil_div_six_le_of_upper": (5, 40, 49, 21, 49, 48, 0),
    "double_triple_remainder_complement_budget": (
        13,
        94,
        214,
        39,
        214,
        213,
        0,
    ),
    "canonical_double_triple_remainder_complement_budget": (
        1,
        16,
        18,
        11,
        18,
        17,
        0,
    ),
    "floor_ceil_complement_budget": (3, 34, 52, 22, 52, 51, 0),
    "floor_ceil_division_budget": (2, 34, 42, 24, 42, 41, 0),
}
EXPECTED_CLOSURES = {
    "mul_le_cancel_left_nonzero": (679, 28, 434, 454, 21),
    "three_mul_eq_two_mul_add_self": (238, 25, 216, 237, 22),
    "ceil_div_six_le_of_upper": (404, 21, 327, 339, 13),
    "double_triple_remainder_complement_budget": (2_198, 39, 937, 992, 56),
    "canonical_double_triple_remainder_complement_budget": (
        2_216,
        40,
        955,
        1_010,
        56,
    ),
    "floor_ceil_complement_budget": (648, 23, 450, 469, 20),
    "floor_ceil_division_budget": (2_906, 41, 1_254, 1_316, 63),
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_quotient_budget_candidate_theorems(TheoremSpec)


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


def test_quotient_relation_builders_are_hygienic_and_compound_safe() -> None:
    divrem = double_triple_divrem_relation(
        "n + 1", "q * 2", "r", tag="compound"
    )
    budget = quotient_complement_budget_relation(
        "n + 1", "q", "c + 1", tag="compound"
    )
    order = witness_le("q + e", "n", tag="compound")
    assert parse_formula_with_names(f"forall n q r. {divrem}")[1] == ()
    assert parse_formula_with_names(f"forall n q c. {budget}")[1] == ()
    assert parse_formula_with_names(f"forall q e n. {order}")[1] == ()

    with pytest.raises(ValueError, match="binder tag"):
        witness_le("x", "y", tag="bad-tag")
    with pytest.raises(ValueError, match="captures"):
        quotient_complement_budget_relation(
            "bqb_budget_gap_capture", "q", "c", tag="capture"
        )
    with pytest.raises(ValueError, match="Peano term"):
        double_triple_divrem_relation("n / 2", "q", "r", tag="badterm")


def test_quotient_budget_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_quotient_budget_candidate_theorems(TheoremSpec) == specs
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
                "DivRem(",
                "sqrt(",
                "ceil(",
                "^",
                "<=",
                "<",
                " / ",
                "%",
            )
        )


def test_quotient_budget_bodies_are_constructive_and_dependency_live() -> None:
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


def test_false_and_off_by_one_quotient_contracts_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {item.name: item for item in _prior_specs()}
    for index, item in enumerate(specs):
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)

    boundary_mutations = {
        "mul_le_cancel_left_nonzero": specs[0].statement.replace(
            "exists k. k + a = b", "exists k. k + S a = b"
        ),
        "three_mul_eq_two_mul_add_self": specs[1].statement.replace(
            "3 * a = 2 * a + a", "4 * a = 2 * a + a"
        ),
        "ceil_div_six_le_of_upper": specs[2].statement.replace(
            "(exists k. k + x = 6 * c)",
            "(exists k. k + x = 6 * c + 1)",
        ),
        "double_triple_remainder_complement_budget": specs[3].statement.replace(
            "= 6 * (c)", "= 5 * (c)"
        ),
        "canonical_double_triple_remainder_complement_budget": specs[
            4
        ].statement.replace("+ S (r) = 3", "+ S (r) = 4", 1),
        "floor_ceil_complement_budget": specs[5].statement.replace(
            "+ (q + e) = (n)", "+ S (q + e) = (n)"
        ),
        "floor_ceil_division_budget": specs[6].statement.replace(
            "+ (q + e) = (n)", "+ S (q + e) = (n)"
        ),
    }
    for name, statement in boundary_mutations.items():
        index = EXPECTED_NAMES.index(name)
        assert statement != specs[index].statement
        mutated = replace(specs[index], statement=statement)
        stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(stack, core=core)


def test_quotient_budget_closures_and_cuts_check_within_policy() -> None:
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
    assert cut_mutations == 29
    assert actual == EXPECTED_CLOSURES


def test_quotient_and_floor_ceiling_budget_semantic_oracles() -> None:
    # Regression only: host integer operations never produce proof objects.
    for dividend in range(0, 1_024):
        quotient, remainder = divmod(2 * dividend, 3)
        complement = dividend - quotient
        assert remainder < 3
        assert quotient + complement == dividend
        assert 2 * dividend <= 6 * complement

        root = isqrt(2 * dividend)
        ceiling = (root * root + 5) // 6
        assert root * root <= 2 * dividend
        assert ceiling <= complement
        assert quotient + ceiling <= dividend

    # The strong complement theorem genuinely needs only its equation.
    for dividend in range(0, 128):
        for quotient in range(0, 2 * dividend // 3 + 1):
            remainder = 2 * dividend - 3 * quotient
            complement = dividend - quotient
            assert 2 * dividend == 3 * quotient + remainder
            assert quotient + complement == dividend
            assert 2 * dividend <= 6 * complement
