"""M13 low-level checked numeral certificates and bounded equality previews."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

import peano_lab.engine.decide as decide_module
import peano_lab.engine.norm_num as norm_module
from peano_lab.engine.decide import (
    DecisionError,
    NumeralCertificate,
    prove_closed_equation,
    prove_closed_term,
)
from peano_lab.engine.norm_num import (
    DEFAULT_NORM_NUM_LIMITS,
    NormNumError,
    NormNumLimit,
    NormNumLimits,
    normalize_equality,
)
from peano_lab.engine.state import MetaVar
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, parse_formula
from peano_lab.kernel.proofs import Axiom, Hyp, Proof
from peano_lab.kernel.terms import Add, Succ, Var, Zero, parse_term


ZERO = Zero()


def test_bounded_closed_term_certificate_is_checked_against_exact_endpoints() -> None:
    source = parse_term("(1 + 2) * 2")

    result = prove_closed_term(source)

    assert result.value == 6
    assert result.source == source
    assert result.normal_form == parse_term("6")
    assert check((), result.certificate, Eq(source, result.normal_form))


@pytest.mark.parametrize("max_value", (-1, True, 1.5, "8"))
def test_closed_term_certificate_rejects_invalid_value_limits(max_value: object) -> None:
    with pytest.raises(DecisionError, match="non-negative integer"):
        prove_closed_term(ZERO, max_value=max_value)  # type: ignore[arg-type]


def test_closed_term_bound_checks_before_oversized_multiplication() -> None:
    compact_large_term = parse_term("((2 * 2) * (2 * 2)) * ((2 * 2) * (2 * 2))")

    with pytest.raises(DecisionError, match="exceeds the explicit 128 limit"):
        prove_closed_term(compact_large_term)


def test_closed_term_certificate_rejects_open_and_malformed_terms() -> None:
    for term in (Var(0), Var(-1), MetaVar(0), object()):
        with pytest.raises(DecisionError):
            prove_closed_term(term)  # type: ignore[arg-type]


def test_legacy_closed_equation_maps_post_normalization_recursion(monkeypatch) -> None:
    def overflow(_term: object) -> None:
        raise RecursionError

    monkeypatch.setattr(decide_module, "_normalization_proof", overflow)
    with pytest.raises(DecisionError, match="too deeply nested"):
        prove_closed_equation(parse_formula("0 = 0"))


def test_mixed_equality_normalizes_one_maximal_closed_island_and_closes() -> None:
    equation = parse_formula("n + ((1 + 2) * (3 + 4)) = n + 21")
    assert type(equation) is Eq

    result = normalize_equality(equation, clock=lambda: 0.0)

    assert result.computations == 1
    assert result.steps[0].source == parse_term("(1 + 2) * (3 + 4)")
    assert result.steps[0].value == 21
    assert result.made_progress
    assert result.closes
    assert result.certificate is not None
    assert check((), result.certificate, equation)


def test_changed_open_equality_returns_one_checked_residual_bridge() -> None:
    equation = parse_formula("n + (1 + 2) = m + (2 + 2)")
    assert type(equation) is Eq

    result = normalize_equality(equation, clock=lambda: 0.0)
    bridge = result.transport_back(Hyp(0))

    assert result.normal_form == parse_formula("n + 3 = m + 4")
    assert result.computations == 2
    assert result.made_progress
    assert not result.closes
    assert result.certificate is None
    assert check((result.normal_form,), bridge, equation)


def test_closed_unequal_result_is_an_untrusted_preview_not_a_certificate() -> None:
    equation = parse_formula("2 + 2 = 5")
    assert type(equation) is Eq

    result = normalize_equality(equation, clock=lambda: 0.0)

    assert result.fully_closed
    assert result.normal_form == parse_formula("4 = 5")
    assert result.certificate is None
    assert result.made_progress


def test_reflexive_open_equality_can_close_without_computation() -> None:
    equation = Eq(Add(Var(0), ZERO), Add(Var(0), ZERO))

    result = normalize_equality(equation, clock=lambda: 0.0)

    assert result.computations == 0
    assert not result.made_progress
    assert result.closes
    assert result.applicable
    assert result.certificate is not None
    assert check((), result.certificate, equation)


def test_normalization_result_and_certificate_are_structurally_deterministic() -> None:
    equation = parse_formula("x + (2 * 3) = x + 6")
    assert type(equation) is Eq

    first = normalize_equality(equation, clock=lambda: 0.0)
    second = normalize_equality(equation, clock=lambda: 0.0)

    assert first == second


@pytest.mark.parametrize(
    ("source", "limits", "message"),
    (
        (
            "0 = 0",
            replace(DEFAULT_NORM_NUM_LIMITS, max_ast_nodes=1),
            "1-AST-node",
        ),
        (
            "S 0 = S 0",
            replace(DEFAULT_NORM_NUM_LIMITS, max_ast_depth=1),
            "1-AST-depth",
        ),
        (
            "(1 + 1) + x = x + (1 + 1)",
            replace(DEFAULT_NORM_NUM_LIMITS, max_computations=1),
            "1-computation",
        ),
        (
            "(2 * 2) + x = x + 4",
            replace(DEFAULT_NORM_NUM_LIMITS, max_value=3),
            "value-3",
        ),
        (
            "0 = 0",
            replace(DEFAULT_NORM_NUM_LIMITS, max_work_units=1),
            "1-work-unit",
        ),
        (
            "1 + 1 = x",
            replace(DEFAULT_NORM_NUM_LIMITS, max_proof_nodes=1),
            "1-proof-node",
        ),
        (
            "1 + 1 = x",
            replace(DEFAULT_NORM_NUM_LIMITS, max_proof_depth=1),
            "1-proof-depth",
        ),
    ),
)
def test_every_structural_resource_limit_is_typed(
    source: str,
    limits: NormNumLimits,
    message: str,
) -> None:
    equation = parse_formula(source)
    assert type(equation) is Eq

    with pytest.raises(NormNumLimit, match=message):
        normalize_equality(equation, limits=limits, clock=lambda: 0.0)


def test_fake_clock_exhausts_the_time_limit_deterministically() -> None:
    readings = iter((10.0, 12.0))
    equation = parse_formula("0 = 0")
    assert type(equation) is Eq

    with pytest.raises(NormNumLimit, match="1-second time limit"):
        normalize_equality(
            equation,
            limits=replace(DEFAULT_NORM_NUM_LIMITS, max_seconds=1.0),
            clock=lambda: next(readings, 12.0),
        )


@pytest.mark.parametrize(
    "kwargs",
    (
        {"max_ast_nodes": 0},
        {"max_work_units": True},
        {"max_seconds": 0},
        {"max_seconds": float("nan")},
        {"max_seconds": float("inf")},
        {"max_seconds": 10**10_000},
    ),
)
def test_norm_num_limits_reject_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="norm_num (?:integer|time) limit"):
        NormNumLimits(**kwargs)  # type: ignore[arg-type]


def test_non_equations_metas_subclasses_and_uninitialized_nodes_are_rejected() -> None:
    with pytest.raises(NormNumError, match="needs an equality"):
        normalize_equality(parse_formula("false"))  # type: ignore[arg-type]
    with pytest.raises(NormNumError, match="no unresolved metavariables"):
        normalize_equality(Eq(MetaVar(7), ZERO))

    class PretendEquation(Eq):
        pass

    with pytest.raises(NormNumError, match="needs an equality"):
        normalize_equality(PretendEquation(ZERO, ZERO))
    with pytest.raises(NormNumError, match="malformed equality syntax"):
        normalize_equality(object.__new__(Eq))


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


def test_mutating_a_numerical_leaf_is_rejected_by_the_kernel() -> None:
    equation = parse_formula("(1 + 2) * 2 = 6")
    assert type(equation) is Eq
    result = normalize_equality(equation, clock=lambda: 0.0)
    assert result.certificate is not None

    mutation, changed = _mutate_first_axiom(result.certificate)

    assert changed
    assert not check((), mutation, equation)


def test_inconsistent_closed_term_metadata_is_rejected(monkeypatch) -> None:
    source = parse_term("1 + 1")
    wrong = NumeralCertificate(source, 3, parse_term("3"), Axiom("PA3"))
    monkeypatch.setattr(norm_module, "prove_closed_term", lambda *_args, **_kwargs: wrong)
    equation = Eq(source, parse_term("2"))

    with pytest.raises(NormNumError, match="inconsistent metadata"):
        normalize_equality(equation, clock=lambda: 0.0)


def test_closed_generator_recursion_maps_to_a_typed_norm_num_limit(monkeypatch) -> None:
    def overflow(*_args, **_kwargs):
        raise DecisionError("cannot prove term: expression is too deeply nested")

    monkeypatch.setattr(norm_module, "prove_closed_term", overflow)
    equation = parse_formula("1 + 1 = 2")
    assert type(equation) is Eq

    with pytest.raises(NormNumLimit, match="host recursion limit"):
        normalize_equality(equation, clock=lambda: 0.0)
