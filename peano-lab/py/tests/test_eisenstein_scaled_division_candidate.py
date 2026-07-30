"""Focused native-body audit for exact Eisenstein scaled floor-sum data."""

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
from peano_lab.library.eisenstein_scaled_division_candidate import (
    make_eisenstein_scaled_division_candidate_theorems,
    scaled_successor_prefix,
)
from peano_lab.library.finite_division_prefix_candidate import (
    make_finite_division_prefix_candidate_theorems,
)
from peano_lab.library.finite_pointwise_mul_recode_candidate import (
    make_finite_pointwise_mul_recode_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "beta_scaled_successor_prefix_from_pointwise",
    "prime_scaled_half_division_prefix_exists",
    "prime_scaled_half_quotient_sum_exists",
)

EXPECTED_DEPENDENCIES = {
    "beta_scaled_successor_prefix_from_pointwise": (),
    "prime_scaled_half_division_prefix_exists": (
        "beta_repeat_exists",
        "beta_pointwise_mul_prefix_exists",
        "beta_scaled_successor_prefix_from_pointwise",
        "prime_nonzero",
        "beta_division_prefix_exists",
    ),
    "prime_scaled_half_quotient_sum_exists": (
        "prime_scaled_half_division_prefix_exists",
        "beta_sum_exists",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "beta_scaled_successor_prefix_from_pointwise": (
        "44ef56466ad3436cb4776b3d2482a1c7d9edc5030947d3e5b3477dfa7b4a6215"
    ),
    "prime_scaled_half_division_prefix_exists": (
        "852a1160fa94363baf7efce001de11fa75318c8be594f2341d8a332e97622d64"
    ),
    "prime_scaled_half_quotient_sum_exists": (
        "01d2649cda6bbc475f0a61dec44646fe5519911f798a6a524b4d44d6c4ea6c94"
    ),
}

EXPECTED_BODY_METRICS = {
    "beta_scaled_successor_prefix_from_pointwise": (34, 24, 34, 33, 0),
    "prime_scaled_half_division_prefix_exists": (71, 40, 71, 70, 0),
    "prime_scaled_half_quotient_sum_exists": (52, 28, 52, 51, 0),
}

_DEPENDENCY_FACTORIES = (
    make_finite_pointwise_mul_recode_candidate_theorems,
    make_finite_division_prefix_candidate_theorems,
)

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_scaled_division_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein scaled-division replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in _DEPENDENCY_FACTORIES:
        for dependency in factory(TheoremSpec):
            assert dependency.name not in core
            core[dependency.name] = dependency
    return core


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _explicit_dependency_core()
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


def test_eisenstein_scaled_division_factory_has_exact_isolated_contract() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_scaled_successor_helper_is_hygienic_alpha_native_and_exact() -> None:
    left = scaled_successor_prefix("a", "tb", "tc", "h", tag="alpha_left")
    right = scaled_successor_prefix("a", "tb", "tc", "h", tag="alpha_right")

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"a", "tb", "tc", "h"}
    assert "esd_index_alpha_left" in left
    assert "a * (1 + esd_index_alpha_left)" in left
    assert "BetaAt(" not in left
    assert "%" not in left

    with pytest.raises(ValueError, match="Peano identifier"):
        scaled_successor_prefix("a + 1", "tb", "tc", "h", tag="bad")
    with pytest.raises(ValueError, match="captures an argument"):
        scaled_successor_prefix(
            "esd_index_capture", "tb", "tc", "h", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        scaled_successor_prefix("a", "tb", "tc", "h", tag="bad tag")


def test_eisenstein_contracts_are_closed_expanded_native_floor_data() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "DivisionPrefix(",
        "Floor(",
        "HalfRange(",
        "PointwiseMul(",
        "Prime(",
        "Repeat(",
        "Sum(",
        "%",
        "⌊",
        "∣",
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)

    capstone = _candidate_specs()[-1].statement
    assert capstone.startswith("forall p h a b c. p = 2 * h + 1 ->")
    assert "exists tb tc qb qc rb rc Q." in capstone
    assert "a * (1 + esd_index_eisenstein_scaled_exact)" in capstone
    assert "ff_s_eisenstein_quotient_sum" in capstone


def test_eisenstein_dependency_curried_bodies_are_constructive_and_bounded() -> None:
    rows = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "EISENSTEIN SCALED DIVISION BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )

