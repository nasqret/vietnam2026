"""Focused constructive audit for Euler's first scaled PairOrder append."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.euler_scaled_inverse_prefix_candidate import (
    make_euler_scaled_inverse_prefix_candidate_theorems,
)
from peano_lab.library.euler_scaled_inverse_prefix_extensional_candidate import (
    make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
)
from peano_lab.library.euler_scaled_pair_order_entrance_candidate import (
    make_euler_scaled_pair_order_entrance_candidate_theorems,
    scaled_orbit_closed_prefix,
)
from peano_lab.library.finite_omission_candidate import (
    make_finite_omission_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)
from peano_lab.library.wilson_pair_order_candidate import (
    make_wilson_pair_order_candidate_theorems,
)


EXPECTED_NAMES = (
    "scaled_orbit_closed_unused_mate",
    "beta_prefix_append_two_scaled_orbit_closed",
    "scaled_inverse_prefix_choose_omitted_orbit",
    "scaled_inverse_pair_order_choose_append",
)

EXPECTED_DEPENDENCIES = {
    "scaled_orbit_closed_unused_mate": (),
    "beta_prefix_append_two_scaled_orbit_closed": (
        "beta_prefix_append_two_reflect",
        "beta_at_unique",
        "succ_injective",
        "le_refl",
        "le_succ",
    ),
    "scaled_inverse_prefix_choose_omitted_orbit": (
        "finite_short_prefix_omits",
        "scaled_inverse_prefix_involutive",
        "scaled_inverse_prefix_no_fixed_of_not_qres",
    ),
    "scaled_inverse_pair_order_choose_append": (
        "scaled_inverse_prefix_choose_omitted_orbit",
        "scaled_orbit_closed_unused_mate",
        "beta_prefix_append_two_exists",
        "beta_prefix_append_two_scaled_orbit_closed",
        "beta_prefix_append_two_injective",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "scaled_orbit_closed_unused_mate": (
        "ebcdb08b307933f444969ca61bd05ffeca8fd30028ccad0828904630d8ad0b6d"
    ),
    "beta_prefix_append_two_scaled_orbit_closed": (
        "f52ea2e97ebef604c508bd5370257295a5b61b5232622dd6007d69f1d37281af"
    ),
    "scaled_inverse_prefix_choose_omitted_orbit": (
        "809bfef13daf3ceca2f45b7e7a34060e6da28b2369c82b92f627e3283c248305"
    ),
    "scaled_inverse_pair_order_choose_append": (
        "b7fed858a6331bdd9393df61da127eb257785f8aeb461d1b1d9ea8e9ac6b7b7b"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "scaled_orbit_closed_unused_mate": (0, 28, 34, 20, 34, 33, 0),
    "beta_prefix_append_two_scaled_orbit_closed": (
        5,
        119,
        184,
        40,
        184,
        183,
        0,
    ),
    "scaled_inverse_prefix_choose_omitted_orbit": (
        3,
        78,
        107,
        38,
        107,
        106,
        0,
    ),
    "scaled_inverse_pair_order_choose_append": (
        5,
        114,
        190,
        52,
        189,
        189,
        1,
    ),
}

_BODY_CPU_LIMIT_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_euler_scaled_pair_order_entrance_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_euler_scaled_inverse_prefix_candidate_theorems,
        make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
        make_finite_omission_candidate_theorems,
        make_wilson_pair_order_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


def _walk(proof: Proof):
    pending = [proof]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Euler PairOrder entrance replay exceeded {seconds}s CPU")

    previous_handler = signal.signal(signal.SIGPROF, expired)
    previous_timer = signal.getitimer(signal.ITIMER_PROF)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_PROF, *previous_timer)


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _dependency_core()
    rows = []

    with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
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
                (
                    item.name,
                    len(item.dependencies),
                    len(item.script),
                    nodes,
                    depth,
                    objects,
                    edges,
                    reused,
                )
            )
    return tuple(rows)


def test_euler_pair_order_entrance_contract_is_exact_and_isolated() -> None:
    first = _candidate_specs()
    assert _candidate_specs() == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "euler_scaled_pair_order_entrance_candidate" not in registry_source


def test_euler_scaled_orbit_surface_is_hygienic_expanded_native_pa() -> None:
    left = scaled_orbit_closed_prefix("u", "v", "b", "c", "l", tag="alpha_left")
    right = scaled_orbit_closed_prefix(
        "u", "v", "b", "c", "l", tag="alpha_right"
    )
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"u", "v", "b", "c", "l"}

    with pytest.raises(ValueError, match="identifier"):
        scaled_orbit_closed_prefix("u + 1", "v", "b", "c", "l", tag="bad")
    with pytest.raises(ValueError, match="captures"):
        scaled_orbit_closed_prefix(
            "espo_position_capture", "v", "b", "c", "l", tag="capture"
        )

    forbidden = (
        "BetaAt(",
        "OrbitClosed(",
        "Prime(",
        "QRes(",
        "ScaledInverse(",
        "%",
        "^",
        "∣",
        "≡",
    )
    for item in _candidate_specs():
        formula, statement_free_names = parse_formula_with_names(item.statement)
        assert not statement_free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)
        assert all("DNE" not in command for command in item.script)


def test_euler_pair_order_entrance_bodies_are_constructive_and_bounded() -> None:
    rows = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:] for row in rows} == EXPECTED_BODY_RECEIPTS

