"""Focused native-body audit for the signed division parity bridge."""

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
from peano_lab.library.parity_mod_two_candidate import (
    make_parity_mod_two_candidate_theorems,
)
from peano_lab.library.parity_odd_division_candidate import (
    make_parity_odd_division_candidate_theorems,
)
from peano_lab.library.signed_division_parity_bridge_candidate import (
    make_signed_division_parity_bridge_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "matching_parity_mod_two",
    "odd_product_division_mod_two",
    "odd_reflected_remainder_mod_two",
    "signed_remainder_sum_mod_two",
    "odd_scaled_division_signed_mod_two",
)

EXPECTED_DEPENDENCIES = {
    "matching_parity_mod_two": (
        "even_to_mod_two_zero",
        "odd_to_mod_two_one",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "odd_product_division_mod_two": (
        "parity_cases",
        "odd_multiplier_parity_iff",
        "odd_division_parity_iff",
        "matching_parity_mod_two",
    ),
    "odd_reflected_remainder_mod_two": (
        "add_assoc",
        "add_comm",
        "mul_comm",
        "zero_add",
        "add_succ_left",
    ),
    "signed_remainder_sum_mod_two": (
        "odd_reflected_remainder_mod_two",
        "mod_eq_refl",
        "mod_eq_add",
        "add_assoc",
    ),
    "odd_scaled_division_signed_mod_two": (
        "odd_product_division_mod_two",
        "signed_remainder_sum_mod_two",
        "mod_eq_trans",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "matching_parity_mod_two": (
        "7f7db531947e615d8f955b4304129cf782668102c57eb722c35f5a90639c41e8"
    ),
    "odd_product_division_mod_two": (
        "1032d49fc7e661e7733cceae686abb85caa7d4768ff6a9ae5a89b9a70f9a5c2a"
    ),
    "odd_reflected_remainder_mod_two": (
        "ef6841f0a5d9b6177a37b19c966a3497ba13ae1866eea7fc3aa46e853d533279"
    ),
    "signed_remainder_sum_mod_two": (
        "9a0570468aaf17a567546996b77231e7786b9f927d4c976d08c4ed82ed363efd"
    ),
    "odd_scaled_division_signed_mod_two": (
        "81afdfe25ad109befd7ca9f55ec8e756c0eb0c926ac07c091b6d88abf5cdedf2"
    ),
}

# dependency count, command count, nodes, depth, objects, edges, reuse
EXPECTED_BODY_RECEIPTS = {
    "matching_parity_mod_two": (4, 48, 53, 15, 53, 52, 0),
    "odd_product_division_mod_two": (4, 58, 77, 27, 77, 76, 0),
    "odd_reflected_remainder_mod_two": (5, 27, 87, 27, 83, 86, 4),
    "signed_remainder_sum_mod_two": (4, 44, 64, 22, 64, 63, 0),
    "odd_scaled_division_signed_mod_two": (3, 37, 43, 25, 43, 42, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"signed division parity replay exceeded {seconds}s CPU")

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
    return make_signed_division_parity_bridge_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_parity_mod_two_candidate_theorems,
        make_parity_odd_division_candidate_theorems,
    ):
        core.update((item.name, item) for item in factory(TheoremSpec))
    return core


def test_signed_division_factory_is_exact_ordered_and_isolated() -> None:
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
    assert "signed_division_parity_bridge_candidate" not in registry_source


def test_signed_division_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "Even(",
        "Odd(",
        "Parity(",
        "ModEq(",
        "DivRem(",
        "Bit(",
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

    endpoint = _candidate_specs()[-1].statement
    assert endpoint.startswith("forall p a x q r m s.")
    assert "a * x = p * q + r" in endpoint
    assert "s = 0 /\\ r = m" in endpoint
    assert "s = 1 /\\ r + m = p" in endpoint
    assert "(x) + 2 *" in endpoint
    assert "(q + m + s) + 2 *" in endpoint
    # The signed branch itself proves s=0 or s=1; no redundant bit premise.
    assert "s = 0 \\/ s = 1" not in endpoint


def test_signed_endpoint_small_standard_model_audit() -> None:
    for p in range(1, 12, 2):
        for a in range(1, 12, 2):
            for x in range(12):
                product = a * x
                for q in range(product // p + 1):
                    r = product - p * q
                    lower = q + r
                    assert (x - lower) % 2 == 0
                    if r <= p:
                        m = p - r
                        upper = q + m + 1
                        assert r + m == p
                        assert (x - upper) % 2 == 0


def test_signed_division_scripts_have_no_classical_or_automation_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    forbidden = ("by_contra", "classical", "sorry", "auto", "ring", "DNE")
    assert all(token not in command for command in commands for token in forbidden)


def test_signed_division_bodies_kernel_check_within_laptop_limit() -> None:
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

