"""Strict-HA audit for the Bertrand B6 exact relational-power bridge."""

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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_bridge_candidate import (
    make_bertrand_power_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
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
    "pow_successor_compose",
    "pow_two_two_exact",
    "pow_two_seven_exact",
    "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
    "bertrand_guard_base_residue",
)

EXPECTED_DEPENDENCIES = {
    "pow_successor_compose": ("pow_exists", "pow_successor_pair_mul"),
    "pow_two_two_exact": ("pow_exists", "pow_two_base_two_value_four"),
    "pow_two_seven_exact": (
        "pow_successor_compose",
        "pow_two_two_exact",
    ),
    "pow_one_twenty_eight_twelve_eq_pow_four_forty_two": (
        "pow_exists",
        "pow_two_two_exact",
        "pow_two_seven_exact",
        "pow_mul_exp",
    ),
    "bertrand_guard_base_residue": (
        "bertrand_base_residue_linear_bounds",
        "pow_exists",
        "pow_base_monotone",
        "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
        "pow_exponent_monotone",
        "le_trans",
        "zero_add",
    ),
}

EXPECTED_STATEMENTS = {
    "pow_successor_compose": (
        5_547,
        "cd3d87e6dbf9f918d0f8675b9cb32a80870746bbcf0a33e3330d9910ee8f2a4a",
    ),
    "pow_two_two_exact": (
        2_529,
        "2c865019367937274ec7de4b0d60b5b1bcb3c12030b314c9e0882ab053fd06a1",
    ),
    "pow_two_seven_exact": (
        2_681,
        "3cc3a56da282b3089b33f989c49f6bec2b22407ab91036163e1abaa768947785",
    ),
    "pow_one_twenty_eight_twelve_eq_pow_four_forty_two": (
        6_801,
        "d35792ac91668e59431ef0a0325daf018b1c1ad6e1ccb9ac26ae341403d385e9",
    ),
    "bertrand_guard_base_residue": (
        5_875,
        "321f7e35a12d0405d4d0596aca1c6de9912d6b7a1f94d6969808e5d2cb5a81ca",
    ),
}

EXPECTED_BODIES = {
    "pow_successor_compose": (2, 29, 45, 21, 45, 44, 0),
    "pow_two_two_exact": (2, 12, 17, 8, 17, 16, 0),
    "pow_two_seven_exact": (2, 243, 1_447, 140, 1_447, 1_446, 0),
    "pow_one_twenty_eight_twelve_eq_pow_four_forty_two": (
        4,
        39,
        1_450,
        150,
        1_450,
        1_449,
        0,
    ),
    "bertrand_guard_base_residue": (7, 71, 106, 29, 106, 105, 0),
}

# Filled from cold kernel closures below; these values are exact regression
# receipts, not adjustable resource allowances.
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int]] = {
    "pow_successor_compose": (65_163, 89, 5_527, 5_777, 251),
    "pow_two_two_exact": (66_378, 89, 5_384, 5_633, 250),
    "pow_two_seven_exact": (132_988, 140, 7_287, 7_542, 256),
    "pow_one_twenty_eight_twelve_eq_pow_four_forty_two": (
        331_115,
        150,
        8_974,
        9_245,
        272,
    ),
    "bertrand_guard_base_residue": (
        467_653,
        154,
        10_157,
        10_453,
        297,
    ),
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
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_bridge_candidate_theorems(TheoremSpec)


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


def test_power_bridge_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_power_bridge_candidate_theorems(TheoremSpec) == specs
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
            for token in ("Pow(", "<=", "^", "**", "sqrt(", "ceil(")
        )


def test_power_bridge_bodies_are_constructive_and_every_edge_is_live() -> None:
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


def test_power_bridge_false_and_off_by_one_contracts_are_rejected() -> None:
    specs = _specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in _prior_specs()
    }
    available = core | {item.name: item for item in specs}

    for item in specs:
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=available)

    mutations = {
        "pow_successor_compose": specs[0].statement.replace(
            "n = r * a ->", "S n = r * a ->"
        ),
        "pow_two_two_exact": _power_terms(
            "2", "2", "5", tag="bpb_two_two"
        ),
        "pow_two_seven_exact": _power_terms(
            "2", "7", "127", tag="bpb_two_seven"
        ),
        "pow_one_twenty_eight_twelve_eq_pow_four_forty_two": (
            specs[3].statement.replace("128", "127")
        ),
        "bertrand_guard_base_residue": specs[4].statement.replace(
            witness_le("x", "y", tag="bpb_guard_result"),
            witness_le("S x", "y", tag="bpb_guard_result"),
        ),
    }
    assert set(mutations) == set(EXPECTED_NAMES)
    for item in specs:
        mutated = replace(item, statement=mutations[item.name])
        assert mutated.statement != item.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutated,), core=available)


def test_power_bridge_closures_and_every_direct_cut_mutation() -> None:
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
        assert not any(type(node) is DNE for node in _walk(certificate))
        for index in range(len(item.dependencies)):
            mutated = _mutate_direct_cut(certificate, index)
            assert not check((), mutated, formula)
            cut_mutations += 1

    print(actual)
    assert actual == EXPECTED_CLOSURES
    assert cut_mutations == sum(len(item.dependencies) for item in _specs()) == 17


def test_power_bridge_integer_oracles_are_regression_only() -> None:
    # Host arithmetic is a bounded semantic fixture, never proof authority.
    for base in range(0, 9):
        for exponent in range(0, 8):
            assert base ** (exponent + 1) == base**exponent * base
    assert 2**2 == 4
    assert 2**7 == 128
    assert 7 * 12 == 2 * 42 == 84
    assert 128**12 == 4**42
    for root in range(64, 70):
        assert (root + 7) ** 12 <= 4 ** (root + 5)
