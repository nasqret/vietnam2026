"""Focused native-body audit for finite quotient/remainder prefixes."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.finite_division_prefix_candidate import (
    division_prefix,
    make_finite_division_prefix_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "beta_division_prefix_extend",
    "beta_division_prefix_exists",
)

EXPECTED_DEPENDENCIES = {
    "beta_division_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "beta_division_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "beta_at_exists",
        "division_remainder_exists",
        "beta_division_prefix_extend",
    ),
}

EXPECTED_BODY_METRICS = {
    "beta_division_prefix_extend": (132, 41, 132, 131, 0),
    "beta_division_prefix_exists": (71, 30, 71, 70, 0),
}

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_division_prefix_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"finite-division body replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _specs_by_name()
    rows = []

    with _body_deadline(_BODY_DEADLINE_SECONDS):
        for item in specs:
            formula = _closed_formula(item.statement)
            target = formula
            for dependency_name in reversed(item.dependencies):
                dependency = local.get(dependency_name) or core[dependency_name]
                target = Imp(_closed_formula(dependency.statement), target)

            state = start(target)
            for dependency_name in item.dependencies:
                state = apply_tactic(state, "intro", dependency_name)
            for command in item.script:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, target)

            assert check((), certificate, target)
            assert not any(type(node) is DNE for node in _walk(certificate))
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            rows.append(
                (item.name, nodes, depth, objects, edges, reused, len(item.script))
            )

    return tuple(rows)


def test_finite_division_factory_has_exact_isolated_dependency_surface() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES

    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_division_prefix_helper_is_hygienic_native_and_alpha_stable() -> None:
    arguments = ("p", "b", "c", "qb", "qc", "rb", "rc", "l")
    left = division_prefix(*arguments, tag="alpha_left")
    right = division_prefix(*arguments, tag="alpha_right")

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == set(arguments)
    assert "fdp_index_alpha_left" in left
    assert "fdp_index_alpha_right" not in left
    assert "fdp_index_alpha_right" in right

    forbidden_surface_tokens = (
        "BetaAt(",
        "DivisionPrefix(",
        "DivRem(",
        "%",
        "∣",
    )
    assert all(token not in left for token in forbidden_surface_tokens)

    with pytest.raises(ValueError, match="identifier"):
        division_prefix("p", "b + 1", "c", "qb", "qc", "rb", "rc", "l", tag="bad")
    with pytest.raises(ValueError, match="binder tag"):
        division_prefix(*arguments, tag="bad tag")


def test_finite_division_statements_are_closed_expanded_native_pa() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "DivisionPrefix(",
        "DivRem(",
        "%",
        "∣",
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)


def test_finite_division_dependency_curried_bodies_are_constructive() -> None:
    rows = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "FINITE DIVISION BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )
