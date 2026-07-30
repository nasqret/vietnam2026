"""Focused native-body audit for the complete bounded Euler criterion."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from peano_lab.library.euler_criterion_residue_candidate import (
    make_euler_criterion_residue_candidate_theorems,
)
from peano_lab.library.euler_nonresidue_endpoint_candidate import (
    make_euler_nonresidue_endpoint_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "bounded_nonzero_not_divides",
    "double_predecessor_ne_one",
    "odd_prime_one_not_mod_predecessor",
    "bounded_euler_criterion_dichotomy",
    "bounded_euler_criterion_residue_iff",
    "bounded_euler_criterion_nonresidue_iff",
    "bounded_euler_criterion_complete",
)

EXPECTED_DEPENDENCIES = {
    "bounded_nonzero_not_divides": ("divisor_le_nonzero", "lt_not_le"),
    "double_predecessor_ne_one": (
        "even_odd_exclusive_pointwise",
        "mul_comm",
        "zero_add",
    ),
    "odd_prime_one_not_mod_predecessor": (
        "double_predecessor_ne_one",
        "prime_is_succ_succ",
        "mod_eq_bounded_unique",
        "zero_add",
    ),
    "bounded_euler_criterion_dichotomy": (
        "prime_nonzero",
        "bounded_nonzero_not_divides",
        "quadratic_residue_decidable_nonzero",
        "quadratic_residue_half_power_mod_one",
        "quadratic_nonresidue_half_power_mod_predecessor",
        "add_succ_left",
        "mul_comm",
        "zero_add",
    ),
    "bounded_euler_criterion_residue_iff": (
        "bounded_euler_criterion_dichotomy",
        "odd_prime_one_not_mod_predecessor",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "bounded_euler_criterion_nonresidue_iff": (
        "bounded_euler_criterion_dichotomy",
        "bounded_euler_criterion_residue_iff",
        "odd_prime_one_not_mod_predecessor",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "bounded_euler_criterion_complete": (
        "bounded_euler_criterion_residue_iff",
        "bounded_euler_criterion_nonresidue_iff",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "bounded_nonzero_not_divides": (
        "31a889c59a8c3ede8dfdc0695a1aa436d607343b02f30e871b4488b4223a6cde"
    ),
    "double_predecessor_ne_one": (
        "aaad871fbea2ffbb5ba8d1ba7a9dcf86413c6c2d30c14489818e3df6a1d7ab36"
    ),
    "odd_prime_one_not_mod_predecessor": (
        "4237bb484891edcb4fd54a1ff38769d9182f02ab4c5e0941a505409b408ecbd6"
    ),
    "bounded_euler_criterion_dichotomy": (
        "63ca00984b6812c22e47b9217cf3e1d473c7bbb3a698677d61551f49be8abaa6"
    ),
    "bounded_euler_criterion_residue_iff": (
        "7250ddc0eba28282199ebad7d8fc77e8cb9c84f5db897b204e71909b90169075"
    ),
    "bounded_euler_criterion_nonresidue_iff": (
        "54db8702c453678cca6e17ac5756130f17375cdb49fd2f3436b7ac0b2fcbf220"
    ),
    "bounded_euler_criterion_complete": (
        "54c35c149ef7b63ffbfe7e2264bf443bae295345eb66e221df6638e61f6f3b60"
    ),
}

# dependency count, command count, nodes, depth, objects, edges, reuse
EXPECTED_BODY_RECEIPTS = {
    "bounded_nonzero_not_divides": (2, 16, 20, 13, 20, 19, 0),
    "double_predecessor_ne_one": (3, 21, 65, 19, 64, 64, 1),
    "odd_prime_one_not_mod_predecessor": (4, 36, 56, 25, 55, 55, 1),
    "bounded_euler_criterion_dichotomy": (8, 72, 120, 39, 119, 119, 1),
    "bounded_euler_criterion_residue_iff": (4, 63, 92, 30, 92, 91, 0),
    "bounded_euler_criterion_nonresidue_iff": (5, 76, 91, 37, 91, 90, 0),
    "bounded_euler_criterion_complete": (2, 36, 80, 31, 80, 79, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_euler_criterion_bounded_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_euler_criterion_residue_candidate_theorems,
        make_euler_nonresidue_endpoint_candidate_theorems,
    ):
        core.update((item.name, item) for item in factory(TheoremSpec))
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
        raise TimeoutError(f"bounded Euler replay exceeded {seconds}s CPU")

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


def test_bounded_euler_factory_is_exact_and_isolated() -> None:
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
    assert "euler_criterion_bounded_candidate" not in registry_source


def test_bounded_euler_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "Dvd(",
        "Factorial(",
        "ModEq(",
        "Pow(",
        "Prime(",
        "Product(",
        "QRes(",
        "%",
        "<",
        "∣",
        "≡",
        "↔",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    nondivisor, _, separation, dichotomy, residue, nonresidue, complete = (
        _candidate_specs()
    )
    assert nondivisor.statement.startswith("forall p a. ~(a = 0) ->")
    assert separation.statement.startswith("forall p n h. p = S n ->")
    assert dichotomy.statement.startswith("forall p a n h A. p = S n ->")
    assert "n = h + h" in complete.statement
    assert "exists qr_x_ecb_qres" in complete.statement
    assert "exists ff_b_ecb_power" in complete.statement
    assert residue.statement != nonresidue.statement
    assert len(complete.statement) > len(residue.statement)


def test_bounded_euler_scripts_use_no_classical_or_heavy_escape() -> None:
    commands = tuple(
        command for item in _candidate_specs() for command in item.script
    )
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)
    assert all(command != "auto" for command in commands)
    assert all(command != "ring" for command in commands)


def test_bounded_euler_bodies_are_constructive_and_bounded() -> None:
    observed = {
        name: (dependencies, commands, nodes, depth, objects, edges, reused)
        for (
            name,
            dependencies,
            commands,
            nodes,
            depth,
            objects,
            edges,
            reused,
        ) in _body_receipts()
    }
    assert observed == EXPECTED_BODY_RECEIPTS

