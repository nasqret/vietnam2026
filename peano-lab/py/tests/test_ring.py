"""M12 bounded polynomial normalization produces ordinary PA certificates."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import peano_lab.engine.ring as ring_module
from peano_lab.engine.proof_reduction import ProofReductionError
from peano_lab.engine.ring import (
    DEFAULT_RING_LIMITS,
    RING_LAW_NAMES,
    RingLaw,
    RingLimits,
    prove_ring_equation,
    ring_checked,
)
from peano_lab.engine.state import MetaVar, start
from peano_lab.engine.tactics import TacticError, TacticLimit, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, Proof
from peano_lab.kernel.terms import Add, Succ, Var, Zero
from peano_lab.library.theorems import replay


ZERO = Zero()
ONE = Succ(ZERO)


def _equation(source: str) -> tuple[Eq, tuple[str, ...]]:
    formula, names = parse_formula_with_names(source)
    assert type(formula) is Eq
    return formula, names


@pytest.fixture(scope="module")
def ring_laws() -> tuple[RingLaw, ...]:
    result: list[RingLaw] = []
    for name in RING_LAW_NAMES:
        theorem = replay(name)
        result.append(RingLaw(name, theorem.formula, theorem.certificate))
    return tuple(result)


@pytest.mark.parametrize(
    "source",
    (
        "x + y = y + x",
        "(x + y) + z = x + (y + z)",
        "x * (y + z) = x * y + x * z",
        "(x + y) * z = x * z + y * z",
        "(x + y) * (z + 1) = x * z + x + (y * z + y)",
        "S x = x + 1",
        "2 * 3 + 4 = 10",
    ),
)
def test_basic_ring_identities_have_independently_valid_certificates(
    source: str,
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation(source)

    result = prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)

    assert result.equation == equation
    assert result.proof_nodes > 0
    assert result.proof_depth > 0
    assert result.work_units > 0
    assert check((), result.certificate, equation)


@pytest.mark.parametrize(
    "source",
    (
        (
            "(2 * S n + 1) * (2 * S n + 1) = "
            "8 * S n + (2 * n + 1) * (2 * n + 1)"
        ),
        "8 * S n + (8 * x + 1) = 8 * (S n + x) + 1",
    ),
)
def test_exact_odd_square_induction_algebra_is_certified(
    source: str,
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation(source)

    result = prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)

    assert check((), result.certificate, equation)


def test_ring_result_is_structurally_deterministic(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation("(x + 2) * (x + 3) = x * x + 5 * x + 6")

    first = prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)
    second = prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)

    assert first == second


def test_false_polynomial_identity_is_rejected(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation("x + x = x")

    with pytest.raises(TacticError, match="different polynomial normal forms"):
        prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)


def test_non_equations_and_unresolved_metavariables_are_rejected(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    with pytest.raises(TacticError, match="needs an equality goal"):
        prove_ring_equation(  # type: ignore[arg-type]
            parse_formula("false"), ring_laws, clock=lambda: 0.0
        )

    unresolved = Eq(Add(MetaVar(17), ONE), Add(MetaVar(17), ONE))
    with pytest.raises(TacticError, match="no unresolved metavariables"):
        prove_ring_equation(unresolved, ring_laws, clock=lambda: 0.0)

    state = start(unresolved)
    before = state
    with pytest.raises(TacticError, match="cannot guess unresolved term metavariables"):
        ring_checked(state, ring_laws, clock=lambda: 0.0)
    assert state == before


def test_forged_missing_and_duplicate_laws_are_rejected(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation("x + 0 = x")
    forged = replace(ring_laws[0], certificate=Axiom("PA5"))

    with pytest.raises(TacticError, match="independent kernel rejected ring law"):
        prove_ring_equation(
            equation,
            (forged,) + ring_laws[1:],
            clock=lambda: 0.0,
        )

    with pytest.raises(TacticError, match="missing checked ring law"):
        prove_ring_equation(equation, ring_laws[:-1], clock=lambda: 0.0)

    with pytest.raises(TacticError, match="duplicate ring law"):
        prove_ring_equation(
            equation,
            ring_laws + (ring_laws[0],),
            clock=lambda: 0.0,
        )


@pytest.mark.parametrize(
    ("source", "limits", "message"),
    (
        (
            "x = x",
            replace(DEFAULT_RING_LIMITS, max_ast_nodes=1),
            "1-AST-node",
        ),
        (
            "S S x = S S x",
            replace(DEFAULT_RING_LIMITS, max_ast_depth=2),
            "2-AST-depth",
        ),
        (
            "x + y = y + x",
            replace(DEFAULT_RING_LIMITS, max_variables=1),
            "1-variable",
        ),
        (
            "x * x = x * x",
            replace(DEFAULT_RING_LIMITS, max_degree=1),
            "degree-1",
        ),
        (
            "x + y = y + x",
            replace(DEFAULT_RING_LIMITS, max_monomials=1),
            "1-monomial",
        ),
        (
            "2 = 2",
            replace(DEFAULT_RING_LIMITS, max_coefficient=1),
            "coefficient-1",
        ),
        (
            "0 = 0",
            replace(DEFAULT_RING_LIMITS, max_work_units=1),
            "1-work-unit",
        ),
        (
            "x = x",
            replace(DEFAULT_RING_LIMITS, max_proof_nodes=1),
            "1-proof-node",
        ),
        (
            "x = x",
            replace(DEFAULT_RING_LIMITS, max_proof_depth=1),
            "1-proof-depth",
        ),
    ),
)
def test_each_structural_resource_limit_is_explicit(
    source: str,
    limits: RingLimits,
    message: str,
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation(source)

    with pytest.raises(TacticLimit, match=message):
        prove_ring_equation(
            equation,
            ring_laws,
            limits=limits,
            clock=lambda: 0.0,
        )


def test_fake_clock_deterministically_exhausts_the_time_limit(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    readings = iter((10.0, 12.0))

    def clock() -> float:
        return next(readings, 12.0)

    equation, _ = _equation("0 = 0")
    limits = replace(DEFAULT_RING_LIMITS, max_seconds=1.0)

    with pytest.raises(TacticLimit, match="1-second time limit"):
        prove_ring_equation(equation, ring_laws, limits=limits, clock=clock)


def test_generated_certificate_has_its_own_node_and_depth_limits(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    commutativity, _ = _equation("x + y = y + x")
    with pytest.raises(TacticLimit, match="800-proof-node limit"):
        prove_ring_equation(
            commutativity,
            ring_laws,
            limits=replace(DEFAULT_RING_LIMITS, max_proof_nodes=800),
            clock=lambda: 0.0,
        )

    square, _ = _equation("(x + 1) * (x + 1) = x * x + 2 * x + 1")
    baseline = prove_ring_equation(
        square,
        ring_laws,
        clock=lambda: 0.0,
    )
    adversarial_depth = baseline.proof_depth - 1
    with pytest.raises(
        TacticLimit,
        match=rf"{adversarial_depth}-proof-depth limit",
    ):
        prove_ring_equation(
            square,
            ring_laws,
            limits=replace(
                DEFAULT_RING_LIMITS,
                max_proof_depth=adversarial_depth,
            ),
            clock=lambda: 0.0,
        )


def test_time_limit_is_checked_after_the_final_kernel_call(
    monkeypatch,
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation("0 = 0")
    real_check = ring_module.check
    final_check_finished = False

    def timed_check(context, proof, target):
        nonlocal final_check_finished
        accepted = real_check(context, proof, target)
        if target == equation:
            final_check_finished = True
        return accepted

    monkeypatch.setattr(ring_module, "check", timed_check)

    with pytest.raises(TacticLimit, match="5-second time limit"):
        prove_ring_equation(
            equation,
            ring_laws,
            clock=lambda: 6.0 if final_check_finished else 0.0,
        )


def test_cut_reduction_recursion_exhaustion_is_a_typed_limit(
    monkeypatch,
    ring_laws: tuple[RingLaw, ...],
) -> None:
    def overflow(_proof: Proof) -> Proof:
        raise ProofReductionError("cut normalization exceeded the host recursion limit")

    monkeypatch.setattr(ring_module, "normalise_cuts", overflow)
    equation, _ = _equation("0 = 0")

    with pytest.raises(TacticLimit, match="host recursion limit"):
        prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)


@pytest.mark.parametrize(
    "kwargs",
    (
        {"max_ast_nodes": 0},
        {"max_work_units": True},
        {"max_seconds": 0},
        {"max_seconds": "slow"},
        {"max_seconds": float("nan")},
        {"max_seconds": float("inf")},
        {"max_seconds": 10**10_000},
    ),
)
def test_ring_limits_reject_non_positive_and_non_numeric_values(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match=r"ring (?:integer limits|time limit) must be positive",
    ):
        RingLimits(**kwargs)  # type: ignore[arg-type]


def test_default_ring_limits_pin_the_documented_browser_contract() -> None:
    assert DEFAULT_RING_LIMITS == RingLimits(
        max_ast_nodes=256,
        max_ast_depth=64,
        max_variables=16,
        max_degree=16,
        max_monomials=64,
        max_coefficient=128,
        max_work_units=25_000,
        max_proof_nodes=100_000,
        max_proof_depth=256,
        max_seconds=5.0,
    )


def test_ring_checked_closes_transactionally_and_finalizes_against_original(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, names = _equation("(x + 1) * (x + 1) = x * x + 2 * x + 1")
    initial = start(equation, names)

    completed = ring_checked(initial, ring_laws, clock=lambda: 0.0)
    certificate = checked_final(completed, equation)

    assert initial.current() is not None
    assert initial.history == ()
    assert completed.is_done()
    assert len(completed.history) == 1
    assert completed.history[0].tactic == "ring"
    assert completed.history[0].state_before == initial
    assert check((), certificate, equation)


def test_ring_checked_failure_leaves_the_exact_state_unchanged(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, names = _equation("x + x = x")
    initial = start(equation, names)
    goals = initial.goals
    partial = initial.partial
    history = initial.history

    with pytest.raises(TacticError, match="different polynomial normal forms"):
        ring_checked(initial, ring_laws, clock=lambda: 0.0)

    assert initial.goals is goals
    assert initial.partial is partial
    assert initial.history is history


def _mutate_first_axiom(proof: Proof) -> tuple[Proof, bool]:
    if type(proof) is Axiom:
        replacement = "PA5" if proof.name != "PA5" else "PA3"
        return Axiom(replacement), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        changed_child, changed = _mutate_first_axiom(child)
        if changed:
            return replace(proof, **{item.name: changed_child}), True
    return proof, False


def test_mutating_a_generated_arithmetic_leaf_is_rejected_by_the_kernel(
    ring_laws: tuple[RingLaw, ...],
) -> None:
    equation, _ = _equation("S x = x + 1")
    result = prove_ring_equation(equation, ring_laws, clock=lambda: 0.0)

    mutation, changed = _mutate_first_axiom(result.certificate)

    assert changed
    assert mutation != result.certificate
    assert not check((), mutation, equation)
