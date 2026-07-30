"""Focused native-body audit for exact beta-coded sum swaps."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_sum_permutation_candidate import (
    make_finite_sum_permutation_candidate_theorems,
)
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "beta_sum_replace_balance",
    "beta_sum_swap_last_invariant",
)
EXPECTED_DEPENDENCIES = {
    "beta_sum_replace_balance": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_lt_succ_eq_or_lt",
        "beta_sum_succ_decompose",
        "beta_sum_transport_prefix",
        "beta_sum_trace_functional",
        "beta_at_unique",
        "add_assoc",
        "add_comm",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "beta_sum_swap_last_invariant": (
        "beta_sum_replace_balance",
        "beta_sum_succ_decompose",
        "beta_at_unique",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "beta_sum_replace_balance": (
        "917852c2c8daeb8b20723ca5e5ac580a2f0531ce4fdebc57b9a8023e305f2b09"
    ),
    "beta_sum_swap_last_invariant": (
        "498c2e6dfba66dd4805b88f5ca4f8563a13ac2d9558d406bca6fe5e124ed4008"
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "beta_sum_replace_balance": (12, 202, 327, 59, 327, 326, 0),
    "beta_sum_swap_last_invariant": (6, 102, 133, 50, 133, 132, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_sum_permutation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for item in make_finite_sum_transport_candidate_theorems(TheoremSpec):
        core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"finite-sum swap replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_sum_permutation_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_finite_sum_permutation_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_sum_permutation_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AlignedPrefix(",
        "BetaAt(",
        "Permutation(",
        "Product(",
        "Sum(",
        "%",
        "<=",
        "<",
        "^",
        "∣",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(token not in item.statement for token in forbidden)

    balance, swap = _candidate_specs()
    assert balance.statement.startswith("forall k b c z d i x y p q.")
    assert balance.statement.endswith("q + x = p + y")
    assert swap.statement.startswith("forall b c z d n i x y p q.")
    assert swap.statement.endswith("p = q")
    assert "ff_s_balance_old = ff_r_balance_old + ff_a_balance_old" in (
        balance.statement
    )


def test_sum_permutation_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_sum_permutation_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
    elapsed = perf_counter() - started
    observed = {
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
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        f"FINITE SUM SWAP BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
