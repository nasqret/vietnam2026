"""Focused body audit for the two-orientation count-sum parity join."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.gauss_count_sum_parity_candidate import (
    make_gauss_count_sum_parity_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAME = "gauss_count_sum_mod_two_from_quotient_sums"
EXPECTED_DEPENDENCIES = ("mod_eq_add",)
EXPECTED_STATEMENT_SHA256 = "1a2ed39c34c998bebfc9c3164427725eca4b1d137e657daf2dc2a8c19b2b6526"
EXPECTED_STATEMENT_LENGTH = 298
EXPECTED_BODY_RECEIPT = (1, 20, 22, 19, 22, 21, 0)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_count_sum_parity_candidate_theorems(TheoremSpec)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"count-sum parity replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_count_sum_parity_factory_is_exact_and_isolated() -> None:
    (item,) = _candidate_specs()
    assert make_gauss_count_sum_parity_candidate_theorems(TheoremSpec) == (item,)
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert len(item.statement) == EXPECTED_STATEMENT_LENGTH
    assert item.name not in _specs_by_name()


def test_count_sum_parity_contract_is_closed_expanded_native_pa() -> None:
    (item,) = _candidate_specs()
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.endswith("h * k + 2 * gcsp_v_sum_product)")
    assert all(token not in item.statement for token in ("ModEq(", "%", "<", "<="))


def test_count_sum_parity_script_is_constructive_and_explicit() -> None:
    (item,) = _candidate_specs()
    assert "apply mod_eq_add" in item.script
    assert all(not command.startswith(("auto", "ring")) for command in item.script)
    assert all("DNE" not in command for command in item.script)
    assert all("sorry" not in command for command in item.script)


def test_count_sum_parity_body_kernel_checks_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        (receipt,) = replay_candidate_bodies(
            _candidate_specs(), core=dict(_specs_by_name())
        )
    observed = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert observed == EXPECTED_BODY_RECEIPT
