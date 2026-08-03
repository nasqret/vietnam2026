"""Focused body audit for exact sums of constant beta prefixes."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_repeat_sum_candidate import (
    make_finite_repeat_sum_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "beta_repeat_sum_exact",
    "beta_repeat_sum_exists_exact",
)
EXPECTED_DEPENDENCIES = {
    "beta_repeat_sum_exact": (
        "beta_sum_zero",
        "beta_sum_succ_decompose",
        "le_succ",
        "le_refl",
        "beta_repeat_entry_eq",
        "mul_zero_left",
        "mul_succ_left",
    ),
    "beta_repeat_sum_exists_exact": (
        "beta_repeat_exists",
        "beta_sum_exists",
        "beta_repeat_sum_exact",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "beta_repeat_sum_exact": (
        "23d4db00ce4416e5516a6c9dc938a937725631c60c72d4dc7e0c76c61d5ed540"
    ),
    "beta_repeat_sum_exists_exact": (
        "1e523564c7f79a5889640f87ed5fc3a2107f4b00004a21c76e2e3e8d705e3156"
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "beta_repeat_sum_exact": (7, 64, 85, 32, 85, 84, 0),
    "beta_repeat_sum_exists_exact": (3, 31, 33, 21, 33, 32, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_repeat_sum_candidate_theorems(TheoremSpec)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"constant beta-sum replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_repeat_sum_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_finite_repeat_sum_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_repeat_sum_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = ("BetaAt(", "Repeat(", "Sum(", "List(", "<=", "<", "%", "∣")
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    exact, existence = _candidate_specs()
    assert exact.statement.startswith("forall b c a l n.")
    assert exact.statement.endswith("n = l * a")
    assert existence.statement.startswith("forall a l. exists b c n.")
    assert existence.statement.endswith("n = l * a)")


def test_repeat_sum_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_repeat_sum_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs())
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
        f"CONSTANT BETA SUM BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
