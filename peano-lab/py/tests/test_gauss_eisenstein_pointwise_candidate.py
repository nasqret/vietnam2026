"""Focused body audit for the beta-level Gauss--Eisenstein join."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.gauss_eisenstein_pointwise_candidate import (
    make_gauss_eisenstein_pointwise_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from peano_lab.library.gauss_signed_division_alignment_candidate import (
    make_gauss_signed_division_alignment_candidate_theorems,
)
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
    "odd_signed_division_congruence_mod_two",
    "gauss_eisenstein_prefix_pointwise_mod_two",
)
EXPECTED_DEPENDENCIES = {
    "odd_signed_division_congruence_mod_two": (
        "odd_signed_division_branch_exact",
        "odd_scaled_division_signed_mod_two",
    ),
    "gauss_eisenstein_prefix_pointwise_mod_two": (
        "beta_at_unique",
        "odd_signed_division_congruence_mod_two",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "odd_signed_division_congruence_mod_two":
        "3b12bb1ac959dd2f25dbed82fbd7be0391fead0804f7c23c2b7d5c2e482203cc",
    "gauss_eisenstein_prefix_pointwise_mod_two":
        "84b039612f162c0c0935ebf49e1ffadf0cdf8e660914f583b7f490744175884e",
}
EXPECTED_STATEMENT_LENGTH = {
    "odd_signed_division_congruence_mod_two": 830,
    "gauss_eisenstein_prefix_pointwise_mod_two": 5_440,
}
EXPECTED_BODY_RECEIPTS = {
    "odd_signed_division_congruence_mod_two": (2, 50, 58, 34, 58, 57, 0),
    "gauss_eisenstein_prefix_pointwise_mod_two": (2, 155, 250, 61, 250, 249, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_eisenstein_pointwise_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_parity_mod_two_candidate_theorems,
        make_parity_odd_division_candidate_theorems,
        make_signed_division_parity_bridge_candidate_theorems,
        make_gauss_magnitude_coprime_candidate_theorems,
        make_gauss_signed_division_alignment_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Gauss--Eisenstein pointwise replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_gauss_eisenstein_pointwise_factory_is_exact_and_isolated() -> None:
    first = _candidate_specs()
    assert make_gauss_eisenstein_pointwise_candidate_theorems(TheoremSpec) == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in first} == EXPECTED_STATEMENT_LENGTH
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_gauss_eisenstein_pointwise_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(", "DivRem(", "HalfRange(", "ModEq(",
                "SignedHalfPrefix(", "%", "<", "<=",
            )
        )
    endpoint = _candidate_specs()[-1].statement
    assert endpoint.startswith("forall p h a b c tb tc qb qc rb rc mb mc sb sc.")
    assert "(x) + 2 *" in endpoint
    assert "(q + m + s) + 2 *" in endpoint


def test_gauss_eisenstein_pointwise_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply odd_signed_division_branch_exact" in commands
    assert "apply odd_scaled_division_signed_mod_two" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_gauss_eisenstein_pointwise_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
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
