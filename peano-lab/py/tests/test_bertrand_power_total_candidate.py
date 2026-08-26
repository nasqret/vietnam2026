"""Strict-HA and capacity audit for shared ``PowTotal`` candidates."""

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
    "pow_successor_compose_from_total",
    "pow_mul_exp_from_total",
    "pow_exponent_monotone_from_total",
    "pow_two_seed_bundle_from_total",
)

EXPECTED_DEPENDENCIES = {
    "pow_successor_compose_from_total": ("pow_successor_pair_mul",),
    "pow_mul_exp_from_total": (
        "pow_zero",
        "pow_successor_decompose",
        "pow_add",
    ),
    "pow_exponent_monotone_from_total": (
        "pow_add",
        "one_le_pow",
        "le_mul_of_one_le_right",
        "add_comm",
    ),
    "pow_two_seed_bundle_from_total": (
        "pow_successor_compose_from_total",
        "pow_two_base_two_value_four",
    ),
}

EXPECTED_STATEMENTS = {
    "pow_successor_compose_from_total": (
        8_852,
        "2062d7502ce8adbd938da50a48d8e5cf3c250600dde5bc98ba32b599d56ce22c",
    ),
    "pow_mul_exp_from_total": (
        11_150,
        "680a0cad3e1efd52904d2e67b7c3af9f7c33e912df4bc56b6700e9ab43db982b",
    ),
    "pow_exponent_monotone_from_total": (
        8_727,
        "08127312b672e5ec0610f0735d18d85235db46909c878123f466f1cb7ed959a5",
    ),
    "pow_two_seed_bundle_from_total": (
        8_248,
        "8631f7c13e6e77fa51ae1b98393eadbebd792e592528a10725a38f5405fee5f6",
    ),
}

EXPECTED_BODIES = {
    "pow_successor_compose_from_total": (1, 30, 45, 21, 45, 44, 0),
    "pow_mul_exp_from_total": (3, 95, 121, 34, 118, 120, 3),
    "pow_exponent_monotone_from_total": (4, 48, 55, 30, 55, 54, 0),
    "pow_two_seed_bundle_from_total": (2, 266, 1_484, 143, 1_484, 1_483, 0),
}

# Filled by a cold local closure replay and frozen below.  The comparison
# theorem names are historical metrics only; no old certificate is trusted as
# an oracle for these candidates.
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int]] = {
    "pow_successor_compose_from_total": (5_327, 66, 1_338, 1_383, 46),
    "pow_mul_exp_from_total": (10_630, 69, 1_648, 1_711, 64),
    "pow_exponent_monotone_from_total": (11_062, 67, 1_701, 1_767, 67),
    "pow_two_seed_bundle_from_total": (13_336, 143, 3_140, 3_192, 53),
}

OLD_CLOSED_NODES = {
    "pow_successor_compose_from_total": 65_163,
    "pow_mul_exp_from_total": 70_463,
    "pow_exponent_monotone_from_total": 70_898,
    # The old 2^7 row has 2^2 only transitively, while the new row returns both.
    "pow_two_seed_bundle_from_total": 132_988,
}

TOTAL_TAGS = {
    "pow_successor_compose_from_total": "successor",
    "pow_mul_exp_from_total": "mul_exp",
    "pow_exponent_monotone_from_total": "exponent",
    "pow_two_seed_bundle_from_total": "seed",
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_total_candidate_theorems(TheoremSpec)


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


def test_power_total_authoring_formula_is_closed_hygienic_and_existing_pa() -> None:
    left = power_total_relation(tag="left")
    right = power_total_relation(tag="right")
    left_formula, left_names = parse_formula_with_names(left)
    right_formula, right_names = parse_formula_with_names(right)
    assert not left_names
    assert not right_names
    assert left_formula == right_formula
    assert left_formula == _closed_formula(_specs_by_name()["pow_exists"].statement)
    assert all(token not in left for token in ("Pow(", "^", "**"))

    for invalid in ("", "forall", "bad-tag", "2bad"):
        with pytest.raises(ValueError):
            power_total_relation(tag=invalid)


def test_power_total_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_power_total_candidate_theorems(TheoremSpec) == specs
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
            for token in ("Pow(", "PowTotal", "^", "**", "<=")
        )


def test_power_total_bodies_are_constructive_and_every_edge_is_live() -> None:
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


def test_false_contracts_and_pow_total_antecedent_mutations_are_rejected() -> None:
    core = _available()
    for item in _specs():
        false_contract = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_contract,), core=core)

        total = power_total_relation(tag=TOTAL_TAGS[item.name])
        assert item.statement.count(total) == 1
        weakened = replace(item, statement=item.statement.replace(total, "0 = 0"))
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((weakened,), core=core)


def test_strengthened_and_off_by_one_contracts_are_rejected() -> None:
    specs = {item.name: item for item in _specs()}
    mutations = {
        "pow_successor_compose_from_total": specs[
            "pow_successor_compose_from_total"
        ].statement.replace("n = r * a ->", "S n = r * a ->"),
        "pow_mul_exp_from_total": specs["pow_mul_exp_from_total"].statement.replace(
            "-> y = z", "-> S y = z"
        ),
        "pow_exponent_monotone_from_total": specs[
            "pow_exponent_monotone_from_total"
        ].statement.replace(
            "bpt_gap_exponent_result + x = y",
            "bpt_gap_exponent_result + S x = y",
        ),
        "pow_two_seed_bundle_from_total": specs[
            "pow_two_seed_bundle_from_total"
        ].statement.replace(
            _power_terms("2", "7", "128", tag="bpt_seed_seven"),
            _power_terms("2", "7", "127", tag="bpt_seed_seven"),
        ),
    }
    assert set(mutations) == set(EXPECTED_NAMES)
    for name, statement in mutations.items():
        assert statement != specs[name].statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(
                (replace(specs[name], statement=statement),),
                core=_available(),
            )


def test_power_total_closures_save_nodes_and_every_direct_cut_is_live() -> None:
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
        assert nodes < OLD_CLOSED_NODES[item.name]
        assert OLD_CLOSED_NODES[item.name] - nodes >= 59_000
        for index in range(len(item.dependencies)):
            assert not check((), _mutate_direct_cut(certificate, index), formula)
            cut_mutations += 1

    assert actual == EXPECTED_CLOSURES
    assert cut_mutations == sum(len(item.dependencies) for item in _specs()) == 10


def test_power_total_standard_natural_semantics_are_regression_only() -> None:
    # Host arithmetic validates orientation only; it produces no certificate.
    for base in range(0, 8):
        for exponent in range(0, 8):
            value = base**exponent
            assert base ** (exponent + 1) == value * base
            for outer in range(0, 6):
                assert (base**exponent) ** outer == base ** (exponent * outer)
            for larger in range(exponent, 8):
                if 1 <= base:
                    assert value <= base**larger
    assert 2**2 == 4
    assert 2**7 == 128
