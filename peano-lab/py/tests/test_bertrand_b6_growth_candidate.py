"""Focused strict-HA audit for the two Bertrand B6 growth rows."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
)
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.bertrand_b6_growth_candidate import (
    make_bertrand_b6_growth_candidate_theorems,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    floor_sqrt_relation,
    make_bertrand_ceil_sqrt_candidate_theorems,
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
from peano_lab.library.bertrand_quotient_budget_candidate import witness_le
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "bertrand_floor_power_product_le_h_from_total",
    "bertrand_four_power_product_le_of_sum_from_total",
)

EXPECTED_DEPENDENCIES = {
    "bertrand_floor_power_product_le_h_from_total": (
        "floor_sqrt_strict_upper_bound",
        "lt_to_le",
        "le_add_right",
        "two_mul_eq_add_self",
        "le_trans",
        "pow_two",
        "pow_base_monotone",
        "pow_mul_exp_from_total",
        "pow_add",
        "mul_le_mul",
        "mul_comm",
    ),
    "bertrand_four_power_product_le_of_sum_from_total": (
        "pow_add",
        "pow_exponent_monotone_from_total",
        "mul_comm",
    ),
}

EXPECTED_STATEMENTS = {
    "bertrand_floor_power_product_le_h_from_total": (
        11_221,
        "fe6d2b4d96702540ce1840db77d67bdb9b4a491777ca3e0f40d21ee407976c32",
    ),
    "bertrand_four_power_product_le_of_sum_from_total": (
        12_956,
        "f3eda74b14fd8e7f4ec70ee2adc22e2cc50923a05de660211903f117df33e842",
    ),
}

EXPECTED_ARTIFACT_SHA256 = {
    "bertrand_floor_power_product_le_h_from_total": (
        "a4a44e28b78a2a43fba94dd09b849db9a4d00ce8c052f413a0962924cf38ad8c",
        "4466f68feaeec41e71a2c390f50d61b20e6e50cd34406b3ce61047ae53e7bce9",
    ),
    "bertrand_four_power_product_le_of_sum_from_total": (
        "07bb661df6c24d5320640a704927a7b931f0401b268317a37b89011f2347063d",
        "9bb407a3f678bc3983dafc6e84daa93eda0115208bdf814c4e0962f0b3a3351b",
    ),
}

EXPECTED_BODIES = {
    "bertrand_floor_power_product_le_h_from_total": (
        11,
        121,
        181,
        39,
        175,
        180,
        6,
    ),
    "bertrand_four_power_product_le_of_sum_from_total": (
        3,
        51,
        76,
        29,
        76,
        75,
        0,
    ),
}

BOUNDARY_MUTATION_CASES = (
    (
        "floor_product__reverse_result",
        "bertrand_floor_power_product_le_h_from_total",
        witness_le("n * A", "H", tag="b6_floor_product_result"),
        witness_le("H", "n * A", tag="b6_floor_product_result_reversed"),
    ),
    (
        "four_product__reverse_exponent_sum_order",
        "bertrand_four_power_product_le_of_sum_from_total",
        witness_le("q + e", "n", tag="b6_four_product_sum"),
        witness_le("n", "q + e", tag="b6_four_product_sum_reversed"),
    ),
)


def _expected_statements() -> dict[str, str]:
    """Reconstruct the exact frozen expanded public surfaces independently."""

    floor_total = power_total_relation(tag="b6_floor_product")
    floor_root = floor_sqrt_relation(
        "2 * n", "s", tag="b6_floor_product_root"
    )
    floor_power = _power_terms(
        "2 * n", "s", "A", tag="b6_floor_product_power"
    )
    floor_envelope = _power_terms(
        "s + 1",
        "2 * s + 2",
        "H",
        tag="b6_floor_product_envelope",
    )
    floor_result = witness_le(
        "n * A", "H", tag="b6_floor_product_result"
    )

    sum_total = power_total_relation(tag="b6_four_product")
    sum_order = witness_le("q + e", "n", tag="b6_four_product_sum")
    sum_q_power = _power_terms(
        "4", "q", "B", tag="b6_four_product_q"
    )
    sum_e_power = _power_terms(
        "4", "e", "U", tag="b6_four_product_e"
    )
    sum_n_power = _power_terms(
        "4", "n", "F", tag="b6_four_product_n"
    )
    sum_result = witness_le(
        "U * B", "F", tag="b6_four_product_result"
    )

    return {
        "bertrand_floor_power_product_le_h_from_total": (
            "forall n s A H. "
            f"({floor_total}) -> ({floor_root}) -> ({floor_power}) -> "
            f"({floor_envelope}) -> ({floor_result})"
        ),
        "bertrand_four_power_product_le_of_sum_from_total": (
            "forall q e n B U F. "
            f"({sum_total}) -> ({sum_order}) -> ({sum_q_power}) -> "
            f"({sum_e_power}) -> ({sum_n_power}) -> ({sum_result})"
        ),
    }


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_ceil_sqrt_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_b6_growth_candidate_theorems(TheoremSpec)


def _core() -> dict[str, TheoremSpec]:
    prior = _prior_specs()
    prior_by_name = {item.name: item for item in prior}
    assert len(prior_by_name) == len(prior)
    public = dict(_specs_by_name())
    collisions = set(public) & set(prior_by_name)
    assert all(public[name] == prior_by_name[name] for name in collisions)
    return public | {
        name: item
        for name, item in prior_by_name.items()
        if name not in public
    }


def _available() -> dict[str, TheoremSpec]:
    return _core() | {item.name: item for item in _specs()}


def test_b6_growth_factory_is_frozen_expanded_and_isolated() -> None:
    specs = _specs()
    assert make_bertrand_b6_growth_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == _expected_statements()
    assert {
        item.name: (
            len(item.statement),
            sha256(item.statement.encode()).hexdigest(),
        )
        for item in specs
    } == EXPECTED_STATEMENTS
    assert {
        item.name: (
            sha256("\0".join(item.script).encode()).hexdigest(),
            sha256(
                "\0".join((item.statement, *item.dependencies)).encode()
            ).hexdigest(),
        )
        for item in specs
    } == EXPECTED_ARTIFACT_SHA256

    public = dict(_specs_by_name())
    prior = {item.name for item in _prior_specs()}
    assert not ({item.name for item in specs} & set(public))
    assert not ({item.name for item in specs} & prior)
    _core()  # Assert every prior/public collision is byte-for-byte compatible.
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "PowTotal",
                "FloorSqrt(",
                "Pow(",
                "Le(",
                "<",
                "<=",
                "^",
                "DNE",
            )
        )


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_b6_growth_body_checks_constructively_within_live_limits(
    row_name: str,
) -> None:
    item = {spec.name: spec for spec in _specs()}[row_name]
    receipt = replay_candidate_bodies((item,), core=_core())[0]
    actual = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert receipt.name == row_name
    assert actual == EXPECTED_BODIES[row_name]
    assert receipt.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert receipt.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert receipt.proof_objects <= MAX_LIVE_PROOF_OBJECTS

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


@pytest.mark.parametrize(
    ("row_name", "dependency"),
    tuple(
        (row_name, dependency)
        for row_name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_b6_growth_every_direct_dependency_is_live(
    row_name: str, dependency: str
) -> None:
    item = {spec.name: spec for spec in _specs()}[row_name]
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_available())


@pytest.mark.parametrize("row_name", EXPECTED_NAMES)
def test_b6_growth_false_conclusions_are_rejected(row_name: str) -> None:
    item = {spec.name: spec for spec in _specs()}[row_name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())


@pytest.mark.parametrize(
    ("case_id", "row_name", "old", "new"),
    BOUNDARY_MUTATION_CASES,
    ids=tuple(case[0] for case in BOUNDARY_MUTATION_CASES),
)
def test_b6_growth_boundary_mutations_are_rejected(
    case_id: str,
    row_name: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = {spec.name: spec for spec in _specs()}[row_name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())


def test_b6_growth_orientation_matches_standard_naturals() -> None:
    # Concrete counterexamples certify that both boundary mutations above
    # are genuinely false in the standard naturals, not cosmetic rewrites.
    assert not 16 <= 1 * 2  # n=s=1, A=2, H=16 refutes reversed row 1.
    assert not 4 * 4 <= 4  # q=e=n=1 refutes reversed q+e/n in row 2.

    for n in range(1, 65):
        s = int((2 * n) ** 0.5)
        A = (2 * n) ** s
        H = (s + 1) ** (2 * s + 2)
        assert s * s <= 2 * n < (s + 1) * (s + 1)
        assert n * A <= H

    for q in range(9):
        for e in range(9):
            for n in range(q + e, 18):
                B = 4**q
                U = 4**e
                F = 4**n
                assert U * B <= F
