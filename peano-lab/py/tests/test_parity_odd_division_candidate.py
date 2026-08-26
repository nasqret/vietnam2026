"""Focused native-body audit for odd-multiplier division parity."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.parity_odd_division_candidate import (
    make_parity_odd_division_candidate_theorems,
)
from peano_lab.library.parity_sum_classification_candidate import (
    make_parity_sum_classification_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "odd_multiplier_even_product_iff",
    "odd_multiplier_odd_product_iff",
    "odd_multiplier_parity_iff",
    "odd_division_even_iff",
    "odd_division_odd_iff",
    "odd_division_parity_iff",
)

EXPECTED_DEPENDENCIES = {
    "odd_multiplier_even_product_iff": (
        "parity_cases",
        "odd_mul_odd",
        "even_not_odd",
        "even_mul_right",
    ),
    "odd_multiplier_odd_product_iff": (
        "parity_cases",
        "even_mul_right",
        "odd_not_even",
        "odd_mul_odd",
    ),
    "odd_multiplier_parity_iff": (
        "odd_multiplier_even_product_iff",
        "odd_multiplier_odd_product_iff",
    ),
    "odd_division_even_iff": (
        "odd_multiplier_even_product_iff",
        "odd_multiplier_odd_product_iff",
        "even_sum_iff_same_parity",
    ),
    "odd_division_odd_iff": (
        "odd_multiplier_even_product_iff",
        "odd_multiplier_odd_product_iff",
        "odd_sum_iff_opposite_parity",
    ),
    "odd_division_parity_iff": (
        "odd_division_even_iff",
        "odd_division_odd_iff",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "odd_multiplier_even_product_iff": (
        "e58a6819e8301cc6994d8ab5800006c4057ef3c2ee19f1cd49a4b3d9db57af4e"
    ),
    "odd_multiplier_odd_product_iff": (
        "e46edf9fc0d2c24991f8e4e902c2efaeb2bcf2a7117409de25975e7dcbaba12c"
    ),
    "odd_multiplier_parity_iff": (
        "520e38c5a87bfc2808ad7e8a7da317f4ae67a223d24c72702048e1b43e72ceee"
    ),
    "odd_division_even_iff": (
        "4896421c853157f85afd94c3cf35db6922e18c4e552736a6c30080fbec0b105e"
    ),
    "odd_division_odd_iff": (
        "17c30d8fead71ac118a929024d789fec47e79b87a4620ff2a7d4659a194b88b0"
    ),
    "odd_division_parity_iff": (
        "c7247008edeef923f955a268155980da1be959ffe3f04c37e56c2d777df7e1ce"
    ),
}

# dependency count, command count, nodes, depth, objects, edges, reuse
EXPECTED_BODY_RECEIPTS = {
    "odd_multiplier_even_product_iff": (4, 29, 36, 18, 36, 35, 0),
    "odd_multiplier_odd_product_iff": (4, 29, 36, 17, 36, 35, 0),
    "odd_multiplier_parity_iff": (2, 12, 28, 12, 28, 27, 0),
    "odd_division_even_iff": (3, 71, 93, 22, 93, 92, 0),
    "odd_division_odd_iff": (3, 71, 93, 22, 93, 92, 0),
    "odd_division_parity_iff": (2, 21, 51, 20, 51, 50, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"odd-division parity replay exceeded {seconds}s CPU")

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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_parity_odd_division_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update(
        (item.name, item)
        for item in make_parity_sum_classification_candidate_theorems(TheoremSpec)
    )
    return core


def test_odd_division_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert _candidate_specs() == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "parity_odd_division_candidate" not in registry_source


def test_odd_division_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "Even(",
        "Odd(",
        "Parity(",
        "DivRem(",
        "%",
        "<",
        "<=",
        "↔",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    even_mul, odd_mul, combined_mul, even_div, odd_div, combined_div = (
        _candidate_specs()
    )
    for item in (even_mul, odd_mul, combined_mul):
        assert item.statement.startswith("forall p q.")
        assert "p = 2 *" in item.statement
        assert "p * q" in item.statement
    for item in (even_div, odd_div, combined_div):
        assert item.statement.startswith("forall p q r n.")
        assert "n = p * q + r" in item.statement
        assert "q + r" in item.statement


def test_odd_division_scripts_have_no_classical_or_automation_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    forbidden = ("by_contra", "classical", "sorry", "auto", "ring", "DNE")
    assert all(token not in command for command in commands for token in forbidden)


def test_odd_division_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
    elapsed = perf_counter() - started

    observed = {
        item.name: (
            item.dependency_count,
            item.command_count,
            item.proof_nodes,
            item.proof_depth,
            item.proof_objects,
            item.proof_edges,
            item.reused_objects,
        )
        for item in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert elapsed < _BODY_CPU_LIMIT_SECONDS
