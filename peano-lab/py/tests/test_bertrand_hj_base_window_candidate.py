"""Strict-HA and capacity audit for the uniform Bertrand H/J base window."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256

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
from peano_lab.library.bertrand_hj_base_window_candidate import (
    make_bertrand_hj_base_window_candidate_theorems,
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
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
    "bertrand_hj_base_window_from_total",
)

EXPECTED_DEPENDENCIES = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": (
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "mul_assoc",
    ),
    "bertrand_hj_base_window_from_total": (
        "bertrand_base_residue_linear_bounds",
        "ceil_square_seven_successor_lower",
        "pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "le_trans",
    ),
}

EXPECTED_STATEMENTS = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": (
        8_946,
        "07537a68e8ee9dba1effd896ba6e61adfd904d3c361e24214cbe42400be4012a",
    ),
    "bertrand_hj_base_window_from_total": (
        14_167,
        "0a5b8b8a43798d1bde445634f76fc980afca4d41de7001b7ec61fd72c7a9d6e0",
    ),
}

EXPECTED_BODIES = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": (
        3,
        65,
        340,
        53,
        340,
        339,
        0,
    ),
    "bertrand_hj_base_window_from_total": (
        6,
        145,
        636,
        68,
        636,
        635,
        0,
    ),
}

EXPECTED_CLOSURES = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": (
        24_422,
        144,
        3_768,
        3_841,
        74,
    ),
    "bertrand_hj_base_window_from_total": (
        44_153,
        147,
        6_353,
        6_470,
        118,
    ),
}

# Historical comparison only.  Neither old certificate is a dependency or an
# oracle for the new candidates.
OLD_CLOSED_NODES = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": 331_115,
    "bertrand_hj_base_window_from_total": 467_653,
}

POW_TOTAL_TAGS = {
    "pow_one_twenty_eight_double_eq_pow_four_seven_from_total": "hj_common",
    "bertrand_hj_base_window_from_total": "hj_base",
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
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_base_window_candidate_theorems(TheoremSpec)


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


def test_hj_base_window_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_hj_base_window_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENTS

    public = _specs_by_name()
    forbidden_dependencies = {
        "bertrand_guard_base_residue",
        "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
        "pow_two_twelve_eq_pow_four_six",
        "bertrand_guard_six_step_transport",
    }
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert item.name not in public
        assert forbidden_dependencies.isdisjoint(item.dependencies)
        assert all(
            token not in item.statement
            for token in ("Pow(", "PowTotal", "CeilDivSix(", "^", "**", "<=")
        )


def test_hj_base_window_bodies_are_constructive_and_every_edge_is_live() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _prior_specs()
    }
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
    removed_edges = 0
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
            removed_edges += 1
    assert removed_edges == 9


def test_hj_base_window_false_and_pow_total_mutations_are_rejected() -> None:
    available = _available()
    for item in _specs():
        false_contract = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_contract,), core=available)

        total = power_total_relation(tag=POW_TOTAL_TAGS[item.name])
        assert item.statement.count(total) == 1
        weakened = replace(item, statement=item.statement.replace(total, "0 = 0"))
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((weakened,), core=available)


def test_hj_base_window_boundary_mutations_are_rejected() -> None:
    specs = {item.name: item for item in _specs()}
    helper = specs[
        "pow_one_twenty_eight_double_eq_pow_four_seven_from_total"
    ]
    base = specs["bertrand_hj_base_window_from_total"]

    mutations = (
        replace(helper, statement=helper.statement.replace(
            "d = 2 * m ->", "d = S (2 * m) ->"
        )),
        replace(helper, statement=helper.statement.replace(
            "k = 7 * m ->", "k = S (7 * m) ->"
        )),
        replace(helper, statement=helper.statement.replace(
            "-> x = y", "-> S x = y"
        )),
        replace(base, statement=base.statement.replace(
            witness_le("64", "s", tag="hj_base_lower"),
            witness_le("63", "s", tag="hj_base_lower"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("s", "69", tag="hj_base_upper"),
            witness_le("s", "70", tag="hj_base_upper"),
        )),
        replace(base, statement=base.statement.replace(
            _power_terms("s + 1", "2 * s + 2", "h", tag="hj_base_h"),
            _power_terms("s + 1", "2 * s + 3", "h", tag="hj_base_h"),
        )),
        replace(base, statement=base.statement.replace(
            _power_terms("s + 7", "12", "j", tag="hj_base_j"),
            _power_terms("s + 7", "13", "j", tag="hj_base_j"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("h", "u", tag="hj_base_h_result"),
            witness_le("S h", "u", tag="hj_base_h_result"),
        )),
        replace(base, statement=base.statement.replace(
            witness_le("j", "g", tag="hj_base_j_result"),
            witness_le("S j", "g", tag="hj_base_j_result"),
        )),
    )
    for mutated in mutations:
        original = specs[mutated.name]
        assert mutated.statement != original.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=_available())


def test_hj_base_window_closures_are_small_and_every_direct_cut_is_live() -> None:
    actual: dict[str, tuple[int, int, int, int, int]] = {}
    cut_mutations = 0
    for item in _specs():
        formula, certificate = _close(item.name)
        assert check((), certificate, formula)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        actual[item.name] = (nodes, depth, objects, edges, reused)
        assert nodes < MAX_LIVE_PROOF_NODES
        assert depth <= MAX_LIVE_PROOF_DEPTH
        assert objects < MAX_LIVE_PROOF_OBJECTS
        assert nodes < 50_000
        assert MAX_LIVE_PROOF_NODES - nodes > 450_000
        assert not any(type(node) is DNE for node in _walk(certificate))
        assert nodes < OLD_CLOSED_NODES[item.name]
        assert OLD_CLOSED_NODES[item.name] - nodes > 300_000
        for index in range(len(item.dependencies)):
            assert not check((), _mutate_direct_cut(certificate, index), formula)
            cut_mutations += 1

    assert actual == EXPECTED_CLOSURES
    assert cut_mutations == sum(len(item.dependencies) for item in _specs()) == 9


def test_hj_base_window_standard_natural_semantics_are_regression_only() -> None:
    # Host arithmetic checks orientation and the finite base window only.  It
    # is never used to construct a Peano certificate.
    for multiplier in range(0, 13):
        assert 128 ** (2 * multiplier) == 4 ** (7 * multiplier)

    for root in range(64, 70):
        ceiling = (root * root + 5) // 6
        assert 7 * (root + 1) <= ceiling
        assert root + 1 <= 128
        assert root + 7 <= 128
        assert 42 <= root + 5
        assert (root + 1) ** (2 * root + 2) <= 4**ceiling
        assert (root + 7) ** 12 <= 4 ** (root + 5)
