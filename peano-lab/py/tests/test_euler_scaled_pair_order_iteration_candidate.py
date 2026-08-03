"""Focused constructive audit for Euler's terminal scaled PairOrder iteration."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

import peano_lab.library.euler_scaled_pair_order_iteration_candidate as iteration_module
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
)
from peano_lab.library.euler_scaled_pair_order_iteration_candidate import (
    adjacent_scaled_orbit_history,
    make_euler_scaled_pair_order_iteration_candidate_theorems,
    scaled_pair_order_state,
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
from peano_lab.library.wilson_pair_order_induction_candidate import (
    make_wilson_pair_order_induction_candidate_theorems,
)
from peano_lab.library.wilson_pair_order_paired_iteration_candidate import (
    make_wilson_pair_order_paired_iteration_candidate_theorems,
)


EXPECTED_NAMES = (
    "scaled_orbit_closed_prefix_zero",
    "adjacent_scaled_orbit_history_zero",
    "adjacent_scaled_orbit_history_append",
    "scaled_pair_order_state_zero",
    "scaled_inverse_pair_order_paired_state_step",
    "euler_pair_iteration_previous_balance",
    "euler_pair_iteration_step_short",
    "scaled_inverse_pair_order_paired_iteration",
    "scaled_inverse_pair_order_terminal_package",
    "scaled_inverse_pair_order_terminal_coverage",
)

EXPECTED_DEPENDENCIES = {
    "scaled_orbit_closed_prefix_zero": (
        "add_eq_zero_right",
        "succ_ne_zero",
    ),
    "adjacent_scaled_orbit_history_zero": (
        "add_eq_zero_right",
        "succ_ne_zero",
    ),
    "adjacent_scaled_orbit_history_append": (
        "finite_lt_succ_eq_or_lt",
        "pair_index_left_below_double",
        "pair_index_right_below_double",
    ),
    "scaled_pair_order_state_zero": (
        "scaled_orbit_closed_prefix_zero",
        "bounded_into_zero",
        "injective_prefix_zero",
    ),
    "scaled_inverse_pair_order_paired_state_step": (
        "scaled_inverse_pair_order_choose_append",
        "beta_prefix_append_two_bounded_into",
        "adjacent_scaled_orbit_history_append",
    ),
    "euler_pair_iteration_previous_balance": (
        "add_succ_left",
        "add_assoc",
        "add_comm",
    ),
    "euler_pair_iteration_step_short": (
        "add_succ_left",
        "add_comm",
    ),
    "scaled_inverse_pair_order_paired_iteration": (
        "scaled_pair_order_state_zero",
        "adjacent_scaled_orbit_history_zero",
        "euler_pair_iteration_previous_balance",
        "euler_pair_iteration_step_short",
        "scaled_inverse_pair_order_paired_state_step",
        "pair_order_double_succ_length",
    ),
    "scaled_inverse_pair_order_terminal_package": (
        "scaled_inverse_pair_order_paired_iteration",
    ),
    "scaled_inverse_pair_order_terminal_coverage": (
        "scaled_inverse_pair_order_terminal_package",
        "finite_bounded_injective_surjective",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "scaled_orbit_closed_prefix_zero": (
        "d4c1db9208a726c5914bc5f6114577a0959ee25192e810a41d2abcdf905726d2"
    ),
    "adjacent_scaled_orbit_history_zero": (
        "5342ed29762640625fb76aa7c879e34059d7a487a14b9144a6b28e74e0a89c2d"
    ),
    "adjacent_scaled_orbit_history_append": (
        "367935274dbab8eb04fd14e26c356100fe8b89855f502e719bf82f30fc817a6a"
    ),
    "scaled_pair_order_state_zero": (
        "798fabbdde18aa750da9a16fec462e090af9931376f85248b11ec992b6eaae56"
    ),
    "scaled_inverse_pair_order_paired_state_step": (
        "16d2ae4d05559057c79d040e57fbf96ebd01659ac48ba41284a8f3faec6cb65c"
    ),
    "euler_pair_iteration_previous_balance": (
        "87a7d54325a0a8d4ba58e4208299c055463d22bad190ac8391cbe37e506c6058"
    ),
    "euler_pair_iteration_step_short": (
        "a709717d083cc38609af795158cacbe201767717df9fe5cb97afca50c1c2373f"
    ),
    "scaled_inverse_pair_order_paired_iteration": (
        "1c1580b1b47cb2a61fd402b6aa6c99b9c84b3c824587386d999d111d168a47b6"
    ),
    "scaled_inverse_pair_order_terminal_package": (
        "756362b22515d9bd625f5d0eecb0e0e32d1338a0ffbd0c6ef8c370240ba82149"
    ),
    "scaled_inverse_pair_order_terminal_coverage": (
        "f8dcd3a0956f00fc14e7def42da828de0612129adad920219267199dea8d2ed0"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "scaled_orbit_closed_prefix_zero": (2, 20, 23, 19, 23, 22, 0),
    "adjacent_scaled_orbit_history_zero": (2, 16, 19, 15, 19, 18, 0),
    "adjacent_scaled_orbit_history_append": (3, 73, 114, 31, 114, 113, 0),
    "scaled_pair_order_state_zero": (3, 19, 49, 18, 49, 48, 0),
    "scaled_inverse_pair_order_paired_state_step": (
        3,
        88,
        125,
        40,
        125,
        124,
        0,
    ),
    "euler_pair_iteration_previous_balance": (3, 3, 80, 24, 70, 79, 10),
    "euler_pair_iteration_step_short": (2, 3, 40, 15, 36, 39, 4),
    "scaled_inverse_pair_order_paired_iteration": (
        6,
        101,
        155,
        39,
        151,
        154,
        4,
    ),
    "scaled_inverse_pair_order_terminal_package": (1, 29, 41, 25, 40, 40, 1),
    "scaled_inverse_pair_order_terminal_coverage": (2, 58, 64, 26, 64, 63, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_euler_scaled_pair_order_iteration_candidate_theorems(
        TheoremSpec
    )


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_euler_scaled_inverse_prefix_candidate_theorems,
        make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
        make_finite_omission_candidate_theorems,
        make_wilson_pair_order_candidate_theorems,
        make_wilson_pair_order_induction_candidate_theorems,
        make_wilson_pair_order_paired_iteration_candidate_theorems,
        make_euler_scaled_pair_order_entrance_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            assert item.name not in core
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
        raise TimeoutError(
            f"Euler PairOrder iteration replay exceeded {seconds}s CPU"
        )

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

    for item in specs:
        with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
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


def test_euler_pair_order_iteration_contract_is_exact_and_isolated() -> None:
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
    assert "euler_scaled_pair_order_iteration_candidate" not in registry_source


def test_euler_iteration_surfaces_are_hygienic_expanded_native_pa() -> None:
    state_left = scaled_pair_order_state(
        "u", "v", "b", "c", "l", "n", tag="alpha_left"
    )
    state_right = scaled_pair_order_state(
        "u", "v", "b", "c", "l", "n", tag="alpha_right"
    )
    history_left = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "m", tag="alpha_left"
    )
    history_right = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "m", tag="alpha_right"
    )

    assert state_left != state_right
    assert parse_formula(state_left) == parse_formula(state_right)
    _, state_free_names = parse_formula_with_names(state_left)
    assert set(state_free_names) == {"u", "v", "b", "c", "l", "n"}

    assert history_left != history_right
    assert parse_formula(history_left) == parse_formula(history_right)
    _, history_free_names = parse_formula_with_names(history_left)
    assert set(history_free_names) == {"u", "v", "b", "c", "m"}
    assert "espi_pair_alpha_left" in history_left
    assert "S espi_right_alpha_left" in history_left

    with pytest.raises(ValueError, match="identifier"):
        scaled_pair_order_state(
            "u + 1", "v", "b", "c", "l", "n", tag="bad"
        )
    with pytest.raises(ValueError, match="captures"):
        scaled_pair_order_state(
            "espo_position_capture_closed",
            "v",
            "b",
            "c",
            "l",
            "n",
            tag="capture",
        )
    with pytest.raises(ValueError, match="captures"):
        adjacent_scaled_orbit_history(
            "espi_pair_capture", "v", "b", "c", "m", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        adjacent_scaled_orbit_history(
            "u", "v", "b", "c", "m", tag="bad tag"
        )

    forbidden = (
        "At(",
        "BetaAt(",
        "BoundedInto(",
        "Injective(",
        "PairOrder(",
        "Prime(",
        "QRes(",
        "ScaledInverse(",
        "%",
        "^",
        "<",
        "∣",
        "≡",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)
        assert all("DNE" not in command for command in item.script)


def test_euler_iteration_witness_shapes_preserve_shift_and_parentheses() -> None:
    specs = _candidate_specs()
    state_step = specs[4]
    terminal = specs[-1]
    raw_step = next(
        command for command in state_step.script if command.startswith("have hraw")
    )

    assert "S (S (m + m))" in raw_step
    assert "S (S m + m)" not in raw_step
    assert "S j" in raw_step
    assert terminal.statement.startswith("forall p a n u v h. p = S n ->")
    assert "terminal_surjective" in terminal.statement

    source = Path(iteration_module.__file__).read_text()
    assert ".replace(" not in source
    assert "step_payload_placeholder" not in source


def test_euler_pair_order_iteration_bodies_are_constructive_and_bounded() -> None:
    rows = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:] for row in rows} == EXPECTED_BODY_RECEIPTS

    for name, dependencies, commands, nodes, depth, objects, edges, reused in rows:
        print(
            "EULER PAIR ITERATION BODY RECEIPT "
            f"name={name} dependencies={dependencies} commands={commands} "
            f"nodes={nodes} depth={depth} objects={objects} edges={edges} "
            f"reused={reused}",
            flush=True,
        )
