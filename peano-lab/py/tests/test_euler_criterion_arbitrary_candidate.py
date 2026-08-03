"""Focused native-body audit for arbitrary-representative Euler criterion."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.euler_criterion_arbitrary_candidate import (
    make_euler_criterion_arbitrary_candidate_theorems,
)
from peano_lab.library.euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "nondivisor_canonical_remainder_exists",
    "quadratic_residue_mod_equiv",
    "pow_congruent_base_witness",
    "arbitrary_euler_criterion_residue_iff",
    "arbitrary_euler_criterion_nonresidue_iff",
    "arbitrary_euler_criterion_complete",
)

EXPECTED_DEPENDENCIES = {
    "nondivisor_canonical_remainder_exists": (
        "division_remainder_exists",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
    ),
    "quadratic_residue_mod_equiv": ("mod_eq_symm", "mod_eq_trans"),
    "pow_congruent_base_witness": ("pow_exists", "pow_mod_congruent"),
    "arbitrary_euler_criterion_residue_iff": (
        "prime_nonzero",
        "nondivisor_canonical_remainder_exists",
        "quadratic_residue_mod_equiv",
        "pow_congruent_base_witness",
        "bounded_euler_criterion_residue_iff",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "arbitrary_euler_criterion_nonresidue_iff": (
        "prime_nonzero",
        "nondivisor_canonical_remainder_exists",
        "quadratic_residue_mod_equiv",
        "pow_congruent_base_witness",
        "bounded_euler_criterion_nonresidue_iff",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "arbitrary_euler_criterion_complete": (
        "arbitrary_euler_criterion_residue_iff",
        "arbitrary_euler_criterion_nonresidue_iff",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "nondivisor_canonical_remainder_exists": (
        "137b67a996eca1050a6fb1bae94426a1a389f5d55221bf794cc2537de8202729"
    ),
    "quadratic_residue_mod_equiv": (
        "f52b8637eb5303a24e0654796771cda40bece27e6e79113eab35cff8d25b3697"
    ),
    "pow_congruent_base_witness": (
        "c9adb4cc300a04445139299b0c44b0a4b050d2a65499cef5f86e22e0300c3d10"
    ),
    "arbitrary_euler_criterion_residue_iff": (
        "4fcd971b71f75a2b8ebce2247cfa55eec9eed9bc5f9cc67d9a30379a94d6111f"
    ),
    "arbitrary_euler_criterion_nonresidue_iff": (
        "f11ff00a7e5979b142ed8f7b395deae4519b79d275b21ba42cb162f434e88f85"
    ),
    "arbitrary_euler_criterion_complete": (
        "ea7a7d0f895fdeecaa399b5ee1dc4fad0a20a4e1648145a46bbf7b4485d34e43"
    ),
}

# dependency count, command count, nodes, depth, objects, edges, reuse
EXPECTED_BODY_RECEIPTS = {
    "nondivisor_canonical_remainder_exists": (3, 39, 49, 20, 49, 48, 0),
    "quadratic_residue_mod_equiv": (2, 31, 38, 17, 38, 37, 0),
    "pow_congruent_base_witness": (2, 25, 29, 22, 29, 28, 0),
    "arbitrary_euler_criterion_residue_iff": (7, 92, 140, 36, 140, 139, 0),
    "arbitrary_euler_criterion_nonresidue_iff": (
        7,
        98,
        146,
        37,
        146,
        145,
        0,
    ),
    "arbitrary_euler_criterion_complete": (2, 33, 75, 29, 75, 74, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"arbitrary Euler replay exceeded {seconds}s CPU")

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
    return make_euler_criterion_arbitrary_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update(
        (item.name, item)
        for item in make_euler_criterion_bounded_candidate_theorems(TheoremSpec)
    )
    return core


def test_arbitrary_euler_factory_is_exact_and_isolated() -> None:
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
    assert "euler_criterion_arbitrary_candidate" not in registry_source


def test_arbitrary_euler_contracts_are_closed_expanded_native_pa() -> None:
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

    canonical, qres_transport, power_transport, residue, nonresidue, complete = (
        _candidate_specs()
    )
    assert canonical.statement.startswith("forall p a. ~(p = 0) ->")
    assert "exists r. ~(r = 0)" in canonical.statement
    assert qres_transport.statement.startswith("forall p a r.")
    assert power_transport.statement.startswith("forall p a r h A.")
    for endpoint in (residue, nonresidue, complete):
        assert endpoint.statement.startswith("forall p a n h A. p = S n ->")
        assert "frm_factor_eca_not_divisor" in endpoint.statement
        assert "n = h + h" in endpoint.statement


def test_arbitrary_euler_scripts_have_no_classical_or_automation_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    forbidden = ("by_contra", "classical", "sorry", "auto", "ring")
    assert all(token not in command for command in commands for token in forbidden)


def test_arbitrary_euler_bodies_are_kernel_checked_and_bounded() -> None:
    with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )

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

