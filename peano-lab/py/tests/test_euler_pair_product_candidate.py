"""Focused dependency-curried audit for the generic Euler pair product."""

from __future__ import annotations

import signal
from dataclasses import fields
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.euler_pair_product_candidate import (
    adjacent_target_pairs,
    make_euler_pair_product_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)
from peano_lab.library.wilson_pair_product_candidate import (
    make_wilson_pair_product_candidate_theorems,
)


NAME = "beta_adjacent_target_pairs_product_power"
EXPECTED_DEPENDENCIES = (
    "beta_product_double_succ_decompose",
    "beta_product_zero",
    "pow_zero",
    "pow_successor_decompose",
    "le_succ",
    "le_refl",
    "mod_eq_refl",
    "mod_eq_mul",
    "add_succ_left",
    "mul_assoc",
)
EXPECTED_STATEMENT_SHA256 = (
    "c83f5bbead64e338492918107d11ebb4e4da4e36281eeb9874bba192e1783982"
)
EXPECTED_BODY_METRICS = (171, 47, 169, 170, 2, 118)
_BODY_DEADLINE_SECONDS = 60


def _spec() -> TheoremSpec:
    return make_euler_pair_product_candidate_theorems(TheoremSpec)[0]


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _body_certificate() -> tuple[Proof, object]:
    item = _spec()
    core = dict(_specs_by_name())
    core.update(
        (dependency.name, dependency)
        for dependency in make_wilson_pair_product_candidate_theorems(
            TheoremSpec
        )
    )
    formula = _closed_formula(item.statement)
    target = formula
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(core[dependency_name].statement), target)

    state = start(target)
    for dependency_name in item.dependencies:
        state = apply_tactic(state, "intro", dependency_name)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    certificate = checked_final(state, target)
    return certificate, target


def test_euler_pair_product_factory_is_exact_and_isolated() -> None:
    first = make_euler_pair_product_candidate_theorems(TheoremSpec)
    second = make_euler_pair_product_candidate_theorems(TheoremSpec)

    assert first == second
    assert len(first) == 1
    assert first[0].name == NAME
    assert first[0].dependencies == EXPECTED_DEPENDENCIES
    assert sha256(first[0].statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert NAME not in _specs_by_name()


def test_adjacent_target_surface_is_hygienic_and_native() -> None:
    left = adjacent_target_pairs("p", "a", "b", "c", "m", tag="alpha_l")
    right = adjacent_target_pairs("p", "a", "b", "c", "m", tag="alpha_r")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"p", "a", "b", "c", "m"}
    assert "forall wpp_pair_alpha_l" in left
    assert "wpp_left_alpha_l * wpp_right_alpha_l" in left
    assert all(
        token not in left
        for token in ("AdjacentPairs(", "BetaAt(", "ModEq(", "<", "≡")
    )

    with pytest.raises(ValueError, match="Peano identifier"):
        adjacent_target_pairs("p", "a + 1", "b", "c", "m", tag="bad")
    with pytest.raises(ValueError, match="captures an argument"):
        adjacent_target_pairs(
            "p", "a", "wpp_pair_capture", "c", "m", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        adjacent_target_pairs("p", "a", "b", "c", "m", tag="bad tag")


def test_euler_pair_product_contract_is_closed_expanded_pa() -> None:
    item = _spec()
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall p a b c m Q A.")
    assert "forall wpp_pair_pairs" in item.statement
    assert "exists ff_b_target_power ff_c_target_power" in item.statement
    assert all(
        token not in item.statement
        for token in (
            "AdjacentPairs(",
            "BetaAt(",
            "ModEq(",
            "Pow(",
            "Product(",
            "%",
            "<",
            "≡",
        )
    )


def test_euler_pair_product_body_is_constructive_and_bounded() -> None:
    def expired(_signum, _frame):
        raise TimeoutError("Euler pair-product body replay exceeded 60s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, _BODY_DEADLINE_SECONDS)
    try:
        certificate, target = _body_certificate()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)

    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk(certificate))
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    metrics = (nodes, depth, objects, edges, reused, len(_spec().script))
    assert metrics == EXPECTED_BODY_METRICS
    print(
        "EULER PAIR PRODUCT BODY RECEIPT "
        f"name={NAME} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands={len(_spec().script)}",
        flush=True,
    )
