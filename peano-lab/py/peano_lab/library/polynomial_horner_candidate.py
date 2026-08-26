"""Constructive, hygienic beta-coded polynomial evaluation.

The object language remains exactly first-order Heyting arithmetic.  A
polynomial is its existing beta-coded finite coefficient prefix; evaluation is
an independently beta-coded Horner trace starting at zero and satisfying
``next = previous * base + coefficient`` at every position.  None of these
authoring abbreviations adds a predicate, function symbol, axiom, or kernel
rule.

The tactic scripts deliberately reuse the already audited finite-sum induction
skeleton.  Every transformation below is exact and fail-closed; the resulting
distinct Horner propositions must still be checked by the unchanged kernel.
The executable certificate interface is useful for concrete examples but is
not itself formal-theorem evidence or Alpha admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .finite_fold_surface import _binders, _identifier, _variables
from .finite_sum_theorems import (
    _at,
    make_finite_sum_theorems,
)
from .theorems import TheoremSpec


BETA_PREFIX_HORNER_TRACE_EXISTS = "beta_prefix_horner_trace_exists"
BETA_HORNER_EVAL_EXISTS = "beta_horner_eval_exists"
BETA_HORNER_TRACE_FUNCTIONAL = "beta_horner_trace_functional"
BETA_HORNER_EVAL_FUNCTIONAL = "beta_horner_eval_functional"
BETA_HORNER_EVAL_EXISTS_UNIQUE = "beta_horner_eval_exists_unique"
BETA_HORNER_EVAL_EMPTY = "beta_horner_eval_empty"
BETA_HORNER_EVAL_SUCCESSOR_DECOMPOSE = "beta_horner_eval_successor_decompose"

MAX_HORNER_COEFFICIENTS = 4_096
MAX_HORNER_OUTPUT_BITS = 1_048_576


class PolynomialHornerError(ValueError):
    """A conservative definition, immutable script, or concrete trace failed."""


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "Horner binder tag")
    except ValueError as error:
        raise PolynomialHornerError(str(error)) from error


def _horner_steps(
    code: str,
    scale: str,
    base: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    i, coefficient, previous, current = _binders(
        f"ph_{safe_tag}",
        (code, scale, base, trace_code, trace_scale),
        ("i", "coefficient", "previous", "current"),
    )
    bound = f"exists ph_bound_{safe_tag}. ph_bound_{safe_tag} + S {i} = {length}"
    decoded = _at(code, scale, i, coefficient, tag=f"ph_{safe_tag}_coefficient")
    before = _at(trace_code, trace_scale, i, previous, tag=f"ph_{safe_tag}_before")
    after = _at(
        trace_code,
        trace_scale,
        f"S {i}",
        current,
        tag=f"ph_{safe_tag}_after",
    )
    return (
        f"forall {i}. ({bound}) -> exists {coefficient} {previous} {current}. "
        f"(({decoded}) /\\ (({before}) /\\ "
        f"(({after}) /\\ {current} = {previous} * {base} + {coefficient})))"
    )


def _prefix_horner_trace(
    code: str,
    scale: str,
    base: str,
    length: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    trace_code, trace_scale = _binders(
        f"ph_{safe_tag}", (code, scale, base), ("u", "v")
    )
    start = _at(trace_code, trace_scale, "0", "0", tag=f"ph_{safe_tag}_start")
    steps = _horner_steps(
        code,
        scale,
        base,
        length,
        trace_code,
        trace_scale,
        tag=f"{safe_tag}_steps",
    )
    return f"exists {trace_code} {trace_scale}. (({start}) /\\ {steps})"


def _horner_trace_body(
    code: str,
    scale: str,
    base: str,
    length: str,
    result: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    start = _at(trace_code, trace_scale, "0", "0", tag=f"ph_{safe_tag}_start")
    terminal = _at(
        trace_code, trace_scale, length, result, tag=f"ph_{safe_tag}_terminal"
    )
    steps = _horner_steps(
        code,
        scale,
        base,
        length,
        trace_code,
        trace_scale,
        tag=f"{safe_tag}_steps",
    )
    return f"(({start}) /\\ (({terminal}) /\\ {steps}))"


def _horner_relation_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    trace_code, trace_scale = _binders(
        f"ph_{safe_tag}", (code, scale, base, result), ("u", "v")
    )
    body = _horner_trace_body(
        code,
        scale,
        base,
        length,
        result,
        trace_code,
        trace_scale,
        tag=f"{safe_tag}_body",
    )
    return f"exists {trace_code} {trace_scale}. {body}"


def horner_relation(
    code: str,
    scale: str,
    base: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``Horner(code, scale, base, length, result)`` hygienically."""

    try:
        variables = _variables(
            (code, "coefficient code"),
            (scale, "coefficient scale"),
            (base, "evaluation base"),
            (length, "polynomial length"),
            (result, "evaluation result"),
        )
        if len(set(variables)) != len(variables):
            raise ValueError("Horner arguments must be distinct identifiers")
        safe_tag = _safe_tag(tag)
        if set(_binders(f"ph_{safe_tag}", variables, ("u", "v"))) & set(variables):
            raise ValueError("generated Horner binder captures an argument")
        return _horner_relation_terms(*variables, tag=safe_tag)
    except ValueError as error:
        raise PolynomialHornerError(str(error)) from error


def _replace_once(
    commands: list[str], old: str, replacements: tuple[str, ...]
) -> None:
    positions = [index for index, command in enumerate(commands) if command == old]
    if len(positions) != 1:
        raise PolynomialHornerError(f"immutable finite-sum script command changed: {old!r}")
    index = positions[0]
    commands[index : index + 1] = replacements


def _replace_prefixed_once(commands: list[str], prefix: str, replacement: str) -> None:
    positions = [index for index, command in enumerate(commands) if command.startswith(prefix)]
    if len(positions) != 1:
        raise PolynomialHornerError(f"immutable finite-sum script surface changed: {prefix!r}")
    commands[positions[0]] = replacement


def _with_fixed_base(commands: Iterable[str]) -> list[str]:
    result = list(commands)
    _replace_once(result, "intro c", ("intro c", "intro t"))
    return result


def _trace_existence_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    _replace_prefixed_once(
        commands,
        "have htrace : ",
        f"have htrace : {_prefix_horner_trace('b', 'c', 't', 'l', tag='induction')}",
    )
    commands = [command.replace("x3 + x2", "x3 * t + x2") for command in commands]
    _replace_prefixed_once(
        commands,
        "have hold : ",
        "have hold : exists p r s. "
        f"(({_at('b', 'c', 'i', 'p', tag='ph_hold_coefficient')}) /\\ "
        f"(({_at('x', 'x1', 'i', 'r', tag='ph_hold_previous')}) /\\ "
        f"(({_at('x', 'x1', 'S i', 's', tag='ph_hold_current')}) /\\ "
        "s = r * t + p)))",
    )
    return tuple(commands)


def _trace_functionality_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    commands = [command.replace("s = r + a", "s = r * t + a") for command in commands]
    _replace_prefixed_once(
        commands,
        "have hsum1 : ",
        "have hsum1 : "
        + _horner_trace_body('b', 'c', 't', 'l', 'x1', 'u', 'v', tag='prefix_left'),
    )
    _replace_prefixed_once(
        commands,
        "have hsum2 : ",
        "have hsum2 : "
        + _horner_trace_body('b', 'c', 't', 'l', 'x4', 'w', 'd', tag='prefix_right'),
    )
    _replace_once(
        commands,
        "have hadd : x1 + x = x4 + x3",
        ("have hadd : x1 * t + x = x4 * t + x3",),
    )
    _replace_once(commands, "specialize add_congr x1", ("specialize add_congr (x1 * t)",))
    _replace_once(commands, "specialize add_congr x4", ("specialize add_congr (x4 * t)",))
    _replace_once(
        commands,
        "exact hprev",
        (
            "specialize mul_congr x1",
            "specialize mul_congr x4",
            "specialize mul_congr t",
            "specialize mul_congr t",
            "apply mul_congr",
            "exact hprev",
            "refl",
        ),
    )
    _replace_once(commands, "trans x1 + x", ("trans x1 * t + x",))
    _replace_once(commands, "trans x4 + x3", ("trans x4 * t + x3",))
    return tuple(commands)


def _evaluation_existence_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    _replace_prefixed_once(
        commands,
        "have htrace : ",
        f"have htrace : {_prefix_horner_trace('b', 'c', 't', 'l', tag='exists_trace')}",
    )
    commands = [
        command.replace("beta_prefix_sum_trace_exists", BETA_PREFIX_HORNER_TRACE_EXISTS)
        for command in commands
    ]
    _replace_once(
        commands,
        f"specialize {BETA_PREFIX_HORNER_TRACE_EXISTS} c",
        (
            f"specialize {BETA_PREFIX_HORNER_TRACE_EXISTS} c",
            f"specialize {BETA_PREFIX_HORNER_TRACE_EXISTS} t",
        ),
    )
    return tuple(commands)


def _evaluation_functionality_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    commands = [
        command.replace("beta_sum_trace_functional", BETA_HORNER_TRACE_FUNCTIONAL)
        for command in commands
    ]
    _replace_once(
        commands,
        f"specialize {BETA_HORNER_TRACE_FUNCTIONAL} c",
        (
            f"specialize {BETA_HORNER_TRACE_FUNCTIONAL} c",
            f"specialize {BETA_HORNER_TRACE_FUNCTIONAL} t",
        ),
    )
    return tuple(commands)


def _evaluation_unique_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    commands = [
        command.replace("beta_sum_exists", BETA_HORNER_EVAL_EXISTS)
        .replace("beta_sum_functional", BETA_HORNER_EVAL_FUNCTIONAL)
        for command in commands
    ]
    for name in (BETA_HORNER_EVAL_EXISTS, BETA_HORNER_EVAL_FUNCTIONAL):
        _replace_once(
            commands,
            f"specialize {name} c",
            (f"specialize {name} c", f"specialize {name} t"),
        )
    return tuple(commands)


def _successor_decomposition_script(source: TheoremSpec) -> tuple[str, ...]:
    commands = _with_fixed_base(source.script)
    return tuple(command.replace("s = r + a", "s = r * t + a") for command in commands)


def make_polynomial_horner_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the exact dependency-ordered T12 polynomial-evaluation campaign."""

    parents = {
        item.name: item
        for item in make_finite_sum_theorems(TheoremSpec)
    }
    trace = _prefix_horner_trace("b", "c", "t", "l", tag="root_trace")
    value = horner_relation("b", "c", "t", "l", "n", tag="root_value")
    other = horner_relation("b", "c", "t", "l", "m", tag="root_other")
    left = _horner_trace_body("b", "c", "t", "l", "n", "u", "v", tag="left")
    right = _horner_trace_body("b", "c", "t", "l", "m", "w", "d", tag="right")
    zero = _horner_relation_terms("b", "c", "t", "0", "n", tag="zero")
    successor = _horner_relation_terms("b", "c", "t", "S l", "n", tag="successor")
    prefix = horner_relation("b", "c", "t", "l", "r", tag="prefix")
    coefficient = _at("b", "c", "l", "a", tag="ph_final_coefficient")

    return (
        spec(
            BETA_PREFIX_HORNER_TRACE_EXISTS,
            f"forall b c t l. {trace}",
            parents["beta_prefix_sum_trace_exists"].dependencies,
            _trace_existence_script(parents["beta_prefix_sum_trace_exists"]),
            "Every beta-coded coefficient prefix has a complete constructive Horner trace.",
        ),
        spec(
            BETA_HORNER_EVAL_EXISTS,
            f"forall b c t l. exists n. ({value})",
            (BETA_PREFIX_HORNER_TRACE_EXISTS, "beta_at_exists"),
            _evaluation_existence_script(parents["beta_sum_exists"]),
            "Every coded natural polynomial has an actual witnessed Horner evaluation.",
        ),
        spec(
            BETA_HORNER_TRACE_FUNCTIONAL,
            f"forall b c t l n u v m w d. ({left}) -> ({right}) -> n = m",
            ("beta_at_unique", "le_refl", "le_succ", "add_congr", "mul_congr"),
            _trace_functionality_script(parents["beta_sum_trace_functional"]),
            "Any two complete Horner traces over the same polynomial have equal values.",
        ),
        spec(
            BETA_HORNER_EVAL_FUNCTIONAL,
            f"forall b c t l n m. ({value}) -> ({other}) -> n = m",
            (BETA_HORNER_TRACE_FUNCTIONAL,),
            _evaluation_functionality_script(parents["beta_sum_functional"]),
            "The beta-coded polynomial-evaluation relation is functional.",
        ),
        spec(
            BETA_HORNER_EVAL_EXISTS_UNIQUE,
            f"forall b c t l. exists n. (({value}) /\\ forall m. ({other}) -> n = m)",
            (BETA_HORNER_EVAL_EXISTS, BETA_HORNER_EVAL_FUNCTIONAL),
            _evaluation_unique_script(parents["beta_sum_exists_unique"]),
            "Every coded natural polynomial has exactly one witnessed evaluation.",
        ),
        spec(
            BETA_HORNER_EVAL_EMPTY,
            f"forall b c t n. ({zero}) -> n = 0",
            ("beta_at_unique",),
            tuple(_with_fixed_base(parents["beta_sum_zero"].script)),
            "The empty polynomial's exact constructive Horner value is zero.",
        ),
        spec(
            BETA_HORNER_EVAL_SUCCESSOR_DECOMPOSE,
            f"forall b c t l n. ({successor}) -> "
            f"exists a r. (({coefficient}) /\\ (({prefix}) /\\ n = r * t + a))",
            ("le_refl", "le_succ", "beta_at_unique"),
            _successor_decomposition_script(parents["beta_sum_succ_decompose"]),
            "A nonempty polynomial splits into its evaluated prefix and final coefficient.",
        ),
    )


@dataclass(frozen=True, slots=True)
class HornerTraceStep:
    """One concrete checkable multiplication-and-addition step."""

    index: int
    coefficient: int
    previous: int
    result: int


@dataclass(frozen=True, slots=True)
class HornerEvaluation:
    """A concrete immutable certificate, independent of formal theorem authority."""

    base: int
    coefficients: tuple[int, ...]
    value: int
    steps: tuple[HornerTraceStep, ...]


def evaluate_horner(coefficients: Iterable[int], base: int) -> HornerEvaluation:
    """Evaluate a highest-coefficient-first natural polynomial with its trace."""

    if type(base) is not int or base < 0:
        raise PolynomialHornerError("the evaluation base must be a natural integer")
    try:
        values = tuple(coefficients)
    except TypeError as error:
        raise PolynomialHornerError("coefficients must be a finite natural iterable") from error
    if len(values) > MAX_HORNER_COEFFICIENTS:
        raise PolynomialHornerError("polynomial exceeds the bounded certificate size")
    if any(type(value) is not int or value < 0 for value in values):
        raise PolynomialHornerError("every polynomial coefficient must be a natural integer")
    maximum_bits = max((value.bit_length() for value in values), default=0)
    if maximum_bits + len(values) * max(1, base.bit_length()) > MAX_HORNER_OUTPUT_BITS:
        raise PolynomialHornerError("polynomial exceeds the bounded evaluation bit budget")
    result = 0
    steps: list[HornerTraceStep] = []
    for index, coefficient in enumerate(values):
        previous = result
        result = previous * base + coefficient
        steps.append(HornerTraceStep(index, coefficient, previous, result))
    return HornerEvaluation(base, values, result, tuple(steps))


def verify_horner_evaluation(receipt: HornerEvaluation) -> bool:
    """Fail closed on malformed, forged, reordered, omitted, or oversized steps."""

    if type(receipt) is not HornerEvaluation:
        return False
    if type(receipt.coefficients) is not tuple or type(receipt.steps) is not tuple:
        return False
    try:
        expected = evaluate_horner(receipt.coefficients, receipt.base)
    except (PolynomialHornerError, OverflowError, TypeError, ValueError):
        return False
    return type(receipt.value) is int and receipt == expected


__all__ = [
    "BETA_HORNER_EVAL_EMPTY",
    "BETA_HORNER_EVAL_EXISTS",
    "BETA_HORNER_EVAL_EXISTS_UNIQUE",
    "BETA_HORNER_EVAL_FUNCTIONAL",
    "BETA_HORNER_EVAL_SUCCESSOR_DECOMPOSE",
    "BETA_HORNER_TRACE_FUNCTIONAL",
    "BETA_PREFIX_HORNER_TRACE_EXISTS",
    "HornerEvaluation",
    "HornerTraceStep",
    "MAX_HORNER_COEFFICIENTS",
    "MAX_HORNER_OUTPUT_BITS",
    "PolynomialHornerError",
    "evaluate_horner",
    "horner_relation",
    "make_polynomial_horner_candidate_theorems",
    "verify_horner_evaluation",
]
