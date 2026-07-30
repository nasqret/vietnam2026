"""Focused body audit for the exact two-orientation Eisenstein quotient sum."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_fubini_total_candidate import (
    make_eisenstein_fubini_total_candidate_theorems,
)
from peano_lab.library.eisenstein_outer_sum_bridge_candidate import (
    make_eisenstein_outer_sum_bridge_candidate_theorems,
)
from peano_lab.library.eisenstein_quotient_sum_identity_candidate import (
    make_eisenstein_quotient_sum_identity_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAME = "distinct_odd_prime_eisenstein_quotient_sum_identity"
EXPECTED_DEPENDENCIES = (
    "beta_sum_exists",
    "distinct_odd_prime_quotient_sum_equals_rectangle_total",
    "eisenstein_rectangle_floor_sum_identity",
)
EXPECTED_STATEMENT_SHA256 = "d10467b948c749bcf5727127213b5337583b3bba415da7d30a1589ede66116ae"
EXPECTED_BODY_RECEIPT = (3, 123, 145, 68, 145, 144, 0)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_quotient_sum_identity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_outer_sum_bridge_candidate_theorems,
        make_eisenstein_fubini_total_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein quotient-sum replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_quotient_sum_factory_is_exact_and_isolated() -> None:
    specs = _candidate_specs()
    assert len(specs) == 1
    item = specs[0]
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert item.name not in _specs_by_name()


def test_quotient_sum_contract_is_closed_expanded_native_pa() -> None:
    item = _candidate_specs()[0]
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith(
        "forall p q h k tb tc qb qc ub uc sb sc vb vc wb wc ab ac bb bc Q U."
    )
    assert item.statement.endswith("Q + U = h * k")
    forbidden = ("BetaAt(", "DivRem(", "Floor(", "Prime(", "Rectangle(", "Sum(", "%", "<=", "<", "⌊", "∣")
    assert all(token not in item.statement for token in forbidden)


def test_quotient_sum_script_has_no_automation_or_classical_escape() -> None:
    commands = _candidate_specs()[0].script
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(fragment not in command for command in commands for fragment in ("DNE", "by_contra", "classical", "sorry"))


def test_quotient_sum_body_kernel_checks_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
    elapsed = perf_counter() - started
    assert len(receipts) == 1
    receipt = receipts[0]
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
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(f"EISENSTEIN QUOTIENT SUM BODY RECEIPT elapsed={elapsed:.3f}s row={observed}", flush=True)
