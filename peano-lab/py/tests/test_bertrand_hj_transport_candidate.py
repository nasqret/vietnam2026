"""Strict-HA and capacity audit for six-step Bertrand H/J transport."""

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
    ceil_div_six_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
)
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.bertrand_hj_base_window_candidate import (
    make_bertrand_hj_base_window_candidate_theorems,
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
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "bertrand_h_six_step_transport_from_total",
    "bertrand_j_six_step_transport_from_total",
    "bertrand_hj_six_step_from_total",
)

EXPECTED_DEPENDENCIES = {
    "bertrand_h_six_step_transport_from_total": (
        "ceil_div_six_square_six_step",
        "two_mul_eq_add_self",
        "pow_base_monotone",
        "pow_mul_base",
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "pow_add",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "add_assoc",
        "add_comm",
        "add_succ_left",
    ),
    "bertrand_j_six_step_transport_from_total": (
        "two_mul_eq_add_self",
        "pow_base_monotone",
        "pow_mul_base",
        "pow_two_seed_bundle_from_total",
        "pow_mul_exp_from_total",
        "pow_add",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "add_assoc",
        "add_comm",
    ),
    "bertrand_hj_six_step_from_total": (
        "bertrand_h_six_step_transport_from_total",
        "bertrand_j_six_step_transport_from_total",
    ),
}

EXPECTED_STATEMENTS = {
    "bertrand_h_six_step_transport_from_total": (
        19_945,
        "8e21331b84fc205db1c40bbaa5c75a13e7634c8c33f209188580ddf98df2f40d",
    ),
    "bertrand_j_six_step_transport_from_total": (
        13_797,
        "682eee24d4191ac1c1c3f105ee19fa64a84d7a8dc858169b95b50c06d11643b8",
    ),
    "bertrand_hj_six_step_from_total": (
        30_013,
        "2141a08819c3e280bc2a7b9047c3bf425cce38c69aa9bded4a030837ebae5d2e",
    ),
}

EXPECTED_BODIES = {
    "bertrand_h_six_step_transport_from_total": (
        13,
        201,
        800,
        116,
        692,
        799,
        108,
    ),
    "bertrand_j_six_step_transport_from_total": (
        11,
        113,
        637,
        101,
        576,
        636,
        61,
    ),
    "bertrand_hj_six_step_from_total": (2, 64, 82, 49, 82, 81, 0),
}

EXPECTED_CLOSURES = {
    "bertrand_h_six_step_transport_from_total": (
        42_970,
        148,
        4_895,
        5_114,
        220,
    ),
    "bertrand_j_six_step_transport_from_total": (
        41_015,
        147,
        4_368,
        4_526,
        159,
    ),
    "bertrand_hj_six_step_from_total": (
        84_067,
        149,
        5_550,
        5_844,
        295,
    ),
}

POW_TOTAL_TAGS = {
    "bertrand_h_six_step_transport_from_total": "hjt_h",
    "bertrand_j_six_step_transport_from_total": "hjt_j",
    "bertrand_hj_six_step_from_total": "hjt_combined",
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
        *make_bertrand_hj_base_window_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_hj_transport_candidate_theorems(TheoremSpec)


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


def test_hj_transport_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_hj_transport_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: (len(item.statement), sha256(item.statement.encode()).hexdigest())
        for item in specs
    } == EXPECTED_STATEMENTS

    forbidden_dependencies = {
        "bertrand_guard_base_residue",
        "bertrand_guard_six_step_transport",
        "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
        "pow_two_twelve_eq_pow_four_six",
        "pow_exists",
        "pow_mul_exp",
    }
    public = _specs_by_name()
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


def test_hj_transport_bodies_are_constructive_and_every_edge_is_live() -> None:
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
    assert removed_edges == 26


def test_hj_transport_false_and_pow_total_mutations_are_rejected() -> None:
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


def test_hj_transport_boundary_mutations_are_rejected() -> None:
    specs = {item.name: item for item in _specs()}
    hrow = specs["bertrand_h_six_step_transport_from_total"]
    jrow = specs["bertrand_j_six_step_transport_from_total"]
    combined = specs["bertrand_hj_six_step_from_total"]

    mutations = (
        replace(hrow, statement=hrow.statement.replace(
            witness_le("5", "s", tag="hjt_h_lower"),
            witness_le("4", "s", tag="hjt_h_lower"),
        )),
        replace(hrow, statement=hrow.statement.replace(
            ceil_div_six_relation(
                "(s + 6) * (s + 6)", "f", tag="hjt_h_next_ceiling"
            ),
            ceil_div_six_relation(
                "(s + 5) * (s + 5)", "f", tag="hjt_h_next_ceiling"
            ),
        )),
        replace(hrow, statement=hrow.statement.replace(
            _power_terms("s + 7", "2 * s + 14", "hn", tag="hjt_h_next"),
            _power_terms("s + 7", "2 * s + 15", "hn", tag="hjt_h_next"),
        )),
        replace(hrow, statement=hrow.statement.replace(
            _power_terms("s + 7", "12", "j", tag="hjt_h_guard"),
            _power_terms("s + 7", "11", "j", tag="hjt_h_guard"),
        )),
        replace(jrow, statement=jrow.statement.replace(
            _power_terms("s + 13", "12", "jn", tag="hjt_j_next"),
            _power_terms("s + 14", "12", "jn", tag="hjt_j_next"),
        )),
        replace(jrow, statement=jrow.statement.replace(
            _power_terms("4", "s + 11", "gn", tag="hjt_j_next_bound"),
            _power_terms("4", "s + 10", "gn", tag="hjt_j_next_bound"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("5", "s", tag="hjt_combined_lower"),
            witness_le("4", "s", tag="hjt_combined_lower"),
        )),
        replace(combined, statement=combined.statement.replace(
            _power_terms(
                "s + 7", "2 * s + 14", "hn", tag="hjt_combined_h_next"
            ),
            _power_terms(
                "s + 7", "2 * s + 15", "hn", tag="hjt_combined_h_next"
            ),
        )),
        replace(combined, statement=combined.statement.replace(
            _power_terms("s + 13", "12", "jn", tag="hjt_combined_j_next"),
            _power_terms("s + 14", "12", "jn", tag="hjt_combined_j_next"),
        )),
    )
    for mutated in mutations:
        original = specs[mutated.name]
        assert mutated.statement != original.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=_available())


def test_hj_transport_direction_mutations_are_rejected() -> None:
    specs = {item.name: item for item in _specs()}
    hrow = specs["bertrand_h_six_step_transport_from_total"]
    jrow = specs["bertrand_j_six_step_transport_from_total"]
    combined = specs["bertrand_hj_six_step_from_total"]

    mutations = (
        replace(hrow, statement=hrow.statement.replace(
            witness_le("5", "s", tag="hjt_h_lower"),
            witness_le("s", "5", tag="hjt_h_lower"),
        )),
        replace(hrow, statement=hrow.statement.replace(
            witness_le("h", "u", tag="hjt_h_now_result"),
            witness_le("u", "h", tag="hjt_h_now_result"),
        )),
        replace(hrow, statement=hrow.statement.replace(
            witness_le("j", "g", tag="hjt_h_guard_result"),
            witness_le("g", "j", tag="hjt_h_guard_result"),
        )),
        replace(hrow, statement=hrow.statement.replace(
            witness_le("hn", "un", tag="hjt_h_next_result"),
            witness_le("un", "hn", tag="hjt_h_next_result"),
        )),
        replace(jrow, statement=jrow.statement.replace(
            witness_le("j", "g", tag="hjt_j_now_result"),
            witness_le("g", "j", tag="hjt_j_now_result"),
        )),
        replace(jrow, statement=jrow.statement.replace(
            witness_le("jn", "gn", tag="hjt_j_next_result"),
            witness_le("gn", "jn", tag="hjt_j_next_result"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("5", "s", tag="hjt_combined_lower"),
            witness_le("s", "5", tag="hjt_combined_lower"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("h", "u", tag="hjt_combined_h_result"),
            witness_le("u", "h", tag="hjt_combined_h_result"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("j", "g", tag="hjt_combined_j_result"),
            witness_le("g", "j", tag="hjt_combined_j_result"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("hn", "un", tag="hjt_combined_h_next_result"),
            witness_le("un", "hn", tag="hjt_combined_h_next_result"),
        )),
        replace(combined, statement=combined.statement.replace(
            witness_le("jn", "gn", tag="hjt_combined_j_next_result"),
            witness_le("gn", "jn", tag="hjt_combined_j_next_result"),
        )),
    )
    for mutated in mutations:
        original = specs[mutated.name]
        assert mutated.statement != original.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=_available())


def test_hj_transport_closures_are_small_and_every_direct_cut_is_live() -> None:
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
        assert nodes < 100_000
        assert MAX_LIVE_PROOF_NODES - nodes > 400_000
        assert not any(type(node) is DNE for node in _walk(certificate))
        for index in range(len(item.dependencies)):
            assert not check((), _mutate_direct_cut(certificate, index), formula)
            cut_mutations += 1

    assert actual == EXPECTED_CLOSURES
    assert cut_mutations == sum(len(item.dependencies) for item in _specs()) == 26


def test_hj_transport_standard_natural_semantics_are_regression_only() -> None:
    # Host arithmetic checks the chosen orientations and finite examples.  It
    # never constructs or validates a Peano proof certificate.
    for root in range(5, 100):
        ceiling = (root * root + 5) // 6
        next_ceiling = ((root + 6) * (root + 6) + 5) // 6
        assert next_ceiling == ceiling + 2 * root + 6
        assert root + 7 <= 2 * (root + 1)

        h_value = (root + 1) ** (2 * root + 2)
        h_bound = 4**ceiling
        j_value = (root + 7) ** 12
        j_bound = 4 ** (root + 5)
        h_next = (root + 7) ** (2 * root + 14)
        h_next_bound = 4**next_ceiling
        j_next = (root + 13) ** 12
        j_next_bound = 4 ** (root + 11)

        assert h_next == (root + 7) ** (2 * root + 2) * j_value
        assert h_next_bound == (4 ** (root + 1) * h_bound) * j_bound
        if h_value <= h_bound and j_value <= j_bound:
            assert h_next <= h_next_bound
        if j_value <= j_bound:
            assert j_next <= j_next_bound

    for residue_root in range(64, 70):
        root = residue_root
        for _step in range(6):
            ceiling = (root * root + 5) // 6
            assert (root + 1) ** (2 * root + 2) <= 4**ceiling
            assert (root + 7) ** 12 <= 4 ** (root + 5)
            root += 6
