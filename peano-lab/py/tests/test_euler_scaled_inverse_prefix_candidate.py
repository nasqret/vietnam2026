"""Focused body audit for the finite Euler scaled-inverse prefix."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.euler_scaled_inverse_candidate import (
    make_euler_scaled_inverse_candidate_theorems,
)
from peano_lab.library.euler_scaled_inverse_prefix_candidate import (
    make_euler_scaled_inverse_prefix_candidate_theorems,
    scaled_inverse_prefix,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "prime_scaled_inverse_prefix_extend",
    "prime_scaled_inverse_prefix_exists_bounded",
    "prime_scaled_inverse_prefix_exists",
)

EXPECTED_DEPENDENCIES = {
    "prime_scaled_inverse_prefix_extend": (
        "succ_ne_zero",
        "succ_le_succ",
        "prime_scaled_inverse_exists",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "prime_scaled_inverse_prefix_exists_bounded": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "lt_to_le",
        "prime_scaled_inverse_prefix_extend",
    ),
    "prime_scaled_inverse_prefix_exists": (
        "le_refl",
        "prime_scaled_inverse_prefix_exists_bounded",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_scaled_inverse_prefix_extend": (
        "7b90c1f0f83f56d03de001c45158c1189d25fa919e7308dff6c0d8095d328fa5"
    ),
    "prime_scaled_inverse_prefix_exists_bounded": (
        "9d93fa44646a57c9a63625d9c54277bd992c00f0ad117241b4eb36ed79df31d0"
    ),
    "prime_scaled_inverse_prefix_exists": (
        "6938cc8157256e9f8aaab6173293e756b0aef4dd733862479750d3f8e9726ab7"
    ),
}

EXPECTED_BODY_METRICS = {
    "prime_scaled_inverse_prefix_extend": (105, 36, 105, 104, 0, 76),
    "prime_scaled_inverse_prefix_exists_bounded": (81, 33, 81, 80, 0, 63),
    "prime_scaled_inverse_prefix_exists": (40, 23, 40, 39, 0, 18),
}


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_euler_scaled_inverse_prefix_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Euler scaled-prefix replay exceeded {seconds}s CPU")

    previous = signal.signal(signal.SIGPROF, expired)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for item in make_euler_scaled_inverse_candidate_theorems(TheoremSpec):
        assert item.name not in core
        core[item.name] = item
    return core


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _dependency_core()
    rows = []

    with _cpu_deadline(60):
        for item in specs:
            target = _closed_formula(item.statement)
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


def test_scaled_inverse_prefix_factory_contract_is_exact_and_isolated() -> None:
    first = _candidate_specs()
    assert _candidate_specs() == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_scaled_inverse_prefix_surface_is_hygienic_and_native() -> None:
    left = scaled_inverse_prefix("p", "a", "n", "b", "c", "l", tag="alpha_left")
    right = scaled_inverse_prefix("p", "a", "n", "b", "c", "l", tag="alpha_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"p", "a", "n", "b", "c", "l"}
    assert "BetaAt(" not in left
    assert "%" not in left

    with pytest.raises(ValueError, match="identifier"):
        scaled_inverse_prefix("p + 1", "a", "n", "b", "c", "l", tag="bad")
    with pytest.raises(ValueError, match="captures"):
        scaled_inverse_prefix(
            "esip_index_capture", "a", "n", "b", "c", "l", tag="capture"
        )


def test_scaled_inverse_prefix_statements_are_closed_expanded_pa() -> None:
    forbidden = (
        "BetaAt(",
        "InvPrefix(",
        "Prime(",
        "ScaledInverse(",
        "%",
        "∣",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)


def test_scaled_inverse_prefix_bodies_are_constructive_and_bounded() -> None:
    rows = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:] for row in rows} == EXPECTED_BODY_METRICS
