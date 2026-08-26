"""Constructive simultaneous polynomial value/formal-derivative evaluation.

The derivative is not an oracle or an additional function symbol.  Given a
beta-coded Horner value trace ``v[0]=0`` and ``v[i+1]=v[i]*t+a[i]``, a second
ordinary beta-coded Horner trace on the *first trace itself* satisfies
``d[0]=0`` and ``d[i+1]=d[i]*t+v[i]``.  Consequently its final entry is the
exact formal derivative of the finite coefficient polynomial.

All relations below expand into the unchanged first-order Heyting-arithmetic
signature.  Concrete Python receipts are illustrative, never theorem evidence.
In particular this tranche does not assert unproved simple-root Hensel lifting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .finite_fold_surface import _binders, _identifier, _variables
from .finite_sum_theorems import _at
from .polynomial_horner_candidate import (
    MAX_HORNER_COEFFICIENTS,
    MAX_HORNER_OUTPUT_BITS,
    _horner_relation_terms,
    _horner_steps,
    _horner_trace_body,
)


class PolynomialHenselError(ValueError):
    """A conservative derivative definition or bounded example is malformed."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "polynomial derivative binder tag")
    except ValueError as error:
        raise PolynomialHenselError(str(error)) from error


def _arguments(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        values = _variables(*labelled)
        if len(values) != len(set(values)):
            raise ValueError("polynomial derivative arguments must be distinct")
        if any(value.startswith(("ff_", "fs_", "ph_", "hd_")) for value in values):
            raise ValueError("generated polynomial derivative binder captures an argument")
        return values
    except ValueError as error:
        raise PolynomialHenselError(str(error)) from error


def _prefix_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    start = _at(trace_code, trace_scale, "0", "0", tag=f"hd_{safe}_start")
    steps = _horner_steps(
        code,
        scale,
        base,
        length,
        trace_code,
        trace_scale,
        tag=f"hd_{safe}_steps",
    )
    return f"(({start}) /\\ ({steps}))"


def _trace_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    value_code: str,
    value_scale: str,
    derivative_code: str,
    derivative_scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    value = _prefix_terms(
        code,
        scale,
        base,
        length,
        value_code,
        value_scale,
        tag=f"{safe}_value",
    )
    derivative = _prefix_terms(
        value_code,
        value_scale,
        base,
        length,
        derivative_code,
        derivative_scale,
        tag=f"{safe}_derivative",
    )
    return f"(({value}) /\\ ({derivative}))"


def horner_derivative_trace_relation(
    code: str,
    scale: str,
    base: str,
    length: str,
    value_code: str,
    value_scale: str,
    derivative_code: str,
    derivative_scale: str,
    *,
    tag: str,
) -> str:
    """Expand two genuine coupled beta traces for a polynomial and its derivative."""

    values = _arguments(
        (code, "coefficient code"),
        (scale, "coefficient scale"),
        (base, "evaluation point"),
        (length, "coefficient length"),
        (value_code, "value trace code"),
        (value_scale, "value trace scale"),
        (derivative_code, "derivative trace code"),
        (derivative_scale, "derivative trace scale"),
    )
    return _trace_terms(*values, tag=_safe(tag))


def _paired_body_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    value: str,
    derivative: str,
    value_code: str,
    value_scale: str,
    derivative_code: str,
    derivative_scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    value_body = _horner_trace_body(
        code,
        scale,
        base,
        length,
        value,
        value_code,
        value_scale,
        tag=f"hd_{safe}_value",
    )
    derivative_body = _horner_trace_body(
        value_code,
        value_scale,
        base,
        length,
        derivative,
        derivative_code,
        derivative_scale,
        tag=f"hd_{safe}_derivative",
    )
    return f"(({value_body}) /\\ ({derivative_body}))"


def _paired_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    value: str,
    derivative: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    value_code, value_scale, derivative_code, derivative_scale = _binders(
        f"hd_{safe}",
        (code, scale, base, length, value, derivative),
        ("u", "v", "d", "e"),
    )
    body = _paired_body_terms(
        code,
        scale,
        base,
        length,
        value,
        derivative,
        value_code,
        value_scale,
        derivative_code,
        derivative_scale,
        tag=f"{safe}_body",
    )
    return f"exists {value_code} {value_scale} {derivative_code} {derivative_scale}. {body}"


def horner_derivative_relation(
    code: str,
    scale: str,
    base: str,
    length: str,
    value: str,
    derivative: str,
    *,
    tag: str,
) -> str:
    """Expand exact simultaneously evaluated polynomial value and derivative."""

    values = _arguments(
        (code, "coefficient code"),
        (scale, "coefficient scale"),
        (base, "evaluation point"),
        (length, "coefficient length"),
        (value, "polynomial value"),
        (derivative, "formal derivative value"),
    )
    return _paired_terms(*values, tag=_safe(tag))


def _derivative_only_terms(
    code: str,
    scale: str,
    base: str,
    length: str,
    derivative: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    (value,) = _binders(f"hd_{safe}", (code, scale, base, length, derivative), ("value",))
    return (
        f"exists {value}. "
        f"({_paired_terms(code, scale, base, length, value, derivative, tag=f'{safe}_pair')})"
    )


def horner_derivative_only_relation(
    code: str,
    scale: str,
    base: str,
    length: str,
    derivative: str,
    *,
    tag: str,
) -> str:
    """Expand the exact natural formal-derivative value of a beta polynomial."""

    values = _arguments(
        (code, "coefficient code"),
        (scale, "coefficient scale"),
        (base, "evaluation point"),
        (length, "coefficient length"),
        (derivative, "formal derivative value"),
    )
    return _derivative_only_terms(*values, tag=_safe(tag))


def make_polynomial_hensel_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return exact dependency-ordered constructive polynomial-derivative proofs."""

    trace = _trace_terms("b", "c", "t", "l", "u", "v", "d", "e", tag="trace")
    pair = _paired_terms("b", "c", "t", "l", "n", "z", tag="pair")
    other = _paired_terms("b", "c", "t", "l", "m", "w", tag="other")
    value = _horner_relation_terms("b", "c", "t", "l", "n", tag="hd_value")
    derivative = _derivative_only_terms("b", "c", "t", "l", "z", tag="only")
    other_derivative = _derivative_only_terms("b", "c", "t", "l", "w", tag="only_other")
    empty = _paired_terms("b", "c", "t", "0", "n", "z", tag="empty")
    successor = _paired_terms("b", "c", "t", "S l", "n", "z", tag="successor")
    constant = _paired_terms("b", "c", "t", "S 0", "n", "z", tag="constant")
    linear = _paired_terms("b", "c", "t", "S S 0", "n", "z", tag="linear")
    prefix = _paired_terms("b", "c", "t", "l", "r", "q", tag="successor_prefix")
    coefficient = _at("b", "c", "l", "a", tag="hd_successor_coefficient")

    return (
        spec(
            "beta_horner_derivative_trace_exists",
            f"forall b c t l. exists u v d e. ({trace})",
            ("beta_prefix_horner_trace_exists",),
            (
                "intro b", "intro c", "intro t", "intro l",
                "have hvalue : exists u v. "
                f"({_prefix_terms('b','c','t','l','u','v',tag='trace_value_exists')})",
                "specialize beta_prefix_horner_trace_exists b",
                "specialize beta_prefix_horner_trace_exists c",
                "specialize beta_prefix_horner_trace_exists t",
                "specialize beta_prefix_horner_trace_exists l",
                "exact beta_prefix_horner_trace_exists",
                "cases hvalue", "cases hvalue_witness",
                "have hderivative : exists d e. "
                f"({_prefix_terms('x','x1','t','l','d','e',tag='trace_derivative_exists')})",
                "specialize beta_prefix_horner_trace_exists x",
                "specialize beta_prefix_horner_trace_exists x1",
                "specialize beta_prefix_horner_trace_exists t",
                "specialize beta_prefix_horner_trace_exists l",
                "exact beta_prefix_horner_trace_exists",
                "cases hderivative", "cases hderivative_witness",
                "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hvalue_witness_witness", "exact hderivative_witness_witness",
            ),
            "Every beta-coded polynomial has two actual coupled Horner traces, the second being its formal derivative trace.",
        ),
        spec(
            "beta_horner_derivative_value_exists",
            f"forall b c t l. exists n z. ({pair})",
            ("beta_horner_derivative_trace_exists", "beta_at_exists"),
            (
                "intro b", "intro c", "intro t", "intro l",
                "specialize beta_horner_derivative_trace_exists b",
                "specialize beta_horner_derivative_trace_exists c",
                "specialize beta_horner_derivative_trace_exists t",
                "specialize beta_horner_derivative_trace_exists l",
                "cases beta_horner_derivative_trace_exists",
                "cases beta_horner_derivative_trace_exists_witness",
                "cases beta_horner_derivative_trace_exists_witness_witness",
                "cases beta_horner_derivative_trace_exists_witness_witness_witness",
                "cases beta_horner_derivative_trace_exists_witness_witness_witness_witness",
                "cases beta_horner_derivative_trace_exists_witness_witness_witness_witness_left",
                "cases beta_horner_derivative_trace_exists_witness_witness_witness_witness_right",
                "have hvalue : exists n. "
                f"({_at('x','x1','l','n',tag='hd_value_terminal')})",
                "specialize beta_at_exists x", "specialize beta_at_exists x1",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hvalue",
                "have hderivative : exists z. "
                f"({_at('x2','x3','l','z',tag='hd_derivative_terminal')})",
                "specialize beta_at_exists x2", "specialize beta_at_exists x3",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hderivative",
                "exists x4", "exists x5", "exists x", "exists x1", "exists x2", "exists x3",
                "split", "split",
                "exact beta_horner_derivative_trace_exists_witness_witness_witness_witness_left_left",
                "split", "exact hvalue_witness",
                "exact beta_horner_derivative_trace_exists_witness_witness_witness_witness_left_right",
                "split",
                "exact beta_horner_derivative_trace_exists_witness_witness_witness_witness_right_left",
                "split", "exact hderivative_witness",
                "exact beta_horner_derivative_trace_exists_witness_witness_witness_witness_right_right",
            ),
            "Every arbitrary beta-coded natural polynomial has an actual simultaneous value and exact formal derivative.",
        ),
        spec(
            "beta_horner_derivative_value_projection",
            f"forall b c t l n z. ({pair}) -> ({value})",
            (),
            (
                "intro b", "intro c", "intro t", "intro l", "intro n", "intro z",
                "intro hpair", "cases hpair", "cases hpair_witness",
                "cases hpair_witness_witness", "cases hpair_witness_witness_witness",
                "cases hpair_witness_witness_witness_witness",
                "exists x", "exists x1",
                "exact hpair_witness_witness_witness_witness_left",
            ),
            "The first component of simultaneous formal differentiation is exactly the preexisting polynomial Horner value.",
        ),
        spec(
            "beta_horner_derivative_only_projection",
            f"forall b c t l n z. ({pair}) -> ({derivative})",
            (),
            (
                "intro b", "intro c", "intro t", "intro l", "intro n", "intro z",
                "intro hpair", "exists n", "exact hpair",
            ),
            "A simultaneously evaluated polynomial pair yields an actual formal-derivative witness.",
        ),
        spec(
            "beta_horner_derivative_only_exists",
            f"forall b c t l. exists z. ({derivative})",
            ("beta_horner_derivative_value_exists",),
            (
                "intro b", "intro c", "intro t", "intro l",
                "specialize beta_horner_derivative_value_exists b",
                "specialize beta_horner_derivative_value_exists c",
                "specialize beta_horner_derivative_value_exists t",
                "specialize beta_horner_derivative_value_exists l",
                "cases beta_horner_derivative_value_exists",
                "cases beta_horner_derivative_value_exists_witness",
                "exists x1", "exists x",
                "exact beta_horner_derivative_value_exists_witness_witness",
            ),
            "The exact formal derivative of every arbitrary beta-coded natural polynomial exists.",
        ),
        spec(
            "beta_horner_derivative_first_component_functional",
            f"forall b c t l n z m w. ({pair}) -> ({other}) -> n = m",
            ("beta_horner_derivative_value_projection", "beta_horner_eval_functional"),
            (
                "intro b", "intro c", "intro t", "intro l", "intro n", "intro z",
                "intro m", "intro w", "intro hleft", "intro hright",
                "specialize beta_horner_eval_functional b",
                "specialize beta_horner_eval_functional c",
                "specialize beta_horner_eval_functional t",
                "specialize beta_horner_eval_functional l",
                "specialize beta_horner_eval_functional n",
                "specialize beta_horner_eval_functional m",
                "apply beta_horner_eval_functional",
                "specialize beta_horner_derivative_value_projection b",
                "specialize beta_horner_derivative_value_projection c",
                "specialize beta_horner_derivative_value_projection t",
                "specialize beta_horner_derivative_value_projection l",
                "specialize beta_horner_derivative_value_projection n",
                "specialize beta_horner_derivative_value_projection z",
                "apply beta_horner_derivative_value_projection", "exact hleft",
                "specialize beta_horner_derivative_value_projection b",
                "specialize beta_horner_derivative_value_projection c",
                "specialize beta_horner_derivative_value_projection t",
                "specialize beta_horner_derivative_value_projection l",
                "specialize beta_horner_derivative_value_projection m",
                "specialize beta_horner_derivative_value_projection w",
                "apply beta_horner_derivative_value_projection", "exact hright",
            ),
            "The value component of every simultaneous polynomial/derivative evaluation is unique.",
        ),
        spec(
            "beta_horner_derivative_empty",
            f"forall b c t n z. ({empty}) -> (n = 0 /\\ z = 0)",
            ("beta_horner_eval_empty",),
            (
                "intro b", "intro c", "intro t", "intro n", "intro z", "intro hpair",
                "cases hpair", "cases hpair_witness", "cases hpair_witness_witness",
                "cases hpair_witness_witness_witness",
                "cases hpair_witness_witness_witness_witness", "split",
                "specialize beta_horner_eval_empty b",
                "specialize beta_horner_eval_empty c",
                "specialize beta_horner_eval_empty t",
                "specialize beta_horner_eval_empty n",
                "apply beta_horner_eval_empty", "exists x", "exists x1",
                "exact hpair_witness_witness_witness_witness_left",
                "specialize beta_horner_eval_empty x",
                "specialize beta_horner_eval_empty x1",
                "specialize beta_horner_eval_empty t",
                "specialize beta_horner_eval_empty z",
                "apply beta_horner_eval_empty", "exists x2", "exists x3",
                "exact hpair_witness_witness_witness_witness_right",
            ),
            "The empty beta-coded polynomial and its exact formal derivative both evaluate to zero.",
        ),
        spec(
            "beta_horner_derivative_successor_decompose",
            f"forall b c t l n z. ({successor}) -> exists a r q. "
            f"(({coefficient}) /\\ (({prefix}) /\\ "
            f"((n = r * t + a) /\\ z = q * t + r)))",
            ("le_refl", "le_succ", "beta_at_unique"),
            (
                "intro b", "intro c", "intro t", "intro l", "intro n", "intro z",
                "intro hpair", "cases hpair", "cases hpair_witness",
                "cases hpair_witness_witness", "cases hpair_witness_witness_witness",
                "cases hpair_witness_witness_witness_witness",
                "cases hpair_witness_witness_witness_witness_left",
                "cases hpair_witness_witness_witness_witness_left_right",
                "cases hpair_witness_witness_witness_witness_right",
                "cases hpair_witness_witness_witness_witness_right_right",
                "have hvalue_step : exists a r s. "
                f"(({_at('b','c','l','a',tag='hd_step_coefficient')}) /\\ "
                f"(({_at('x','x1','l','r',tag='hd_step_value_previous')}) /\\ "
                f"(({_at('x','x1','S l','s',tag='hd_step_value_next')}) /\\ "
                "s = r * t + a)))",
                "specialize hpair_witness_witness_witness_witness_left_right_right l",
                "apply hpair_witness_witness_witness_witness_left_right_right",
                "specialize le_refl (S l)", "exact le_refl",
                "cases hvalue_step", "cases hvalue_step_witness",
                "cases hvalue_step_witness_witness",
                "cases hvalue_step_witness_witness_witness",
                "cases hvalue_step_witness_witness_witness_right",
                "cases hvalue_step_witness_witness_witness_right_right",
                "have hderivative_step : exists a q s. "
                f"(({_at('x','x1','l','a',tag='hd_step_derivative_coefficient')}) /\\ "
                f"(({_at('x2','x3','l','q',tag='hd_step_derivative_previous')}) /\\ "
                f"(({_at('x2','x3','S l','s',tag='hd_step_derivative_next')}) /\\ "
                "s = q * t + a)))",
                "specialize hpair_witness_witness_witness_witness_right_right_right l",
                "apply hpair_witness_witness_witness_witness_right_right_right",
                "specialize le_refl (S l)", "exact le_refl",
                "cases hderivative_step", "cases hderivative_step_witness",
                "cases hderivative_step_witness_witness",
                "cases hderivative_step_witness_witness_witness",
                "cases hderivative_step_witness_witness_witness_right",
                "cases hderivative_step_witness_witness_witness_right_right",
                "have hcoefficient : x7 = x5",
                "specialize beta_at_unique x", "specialize beta_at_unique x1",
                "specialize beta_at_unique l", "specialize beta_at_unique x7",
                "specialize beta_at_unique x5", "apply beta_at_unique",
                "exact hderivative_step_witness_witness_witness_left",
                "exact hvalue_step_witness_witness_witness_right_left",
                "have hfinal_value : n = x6",
                "specialize beta_at_unique x", "specialize beta_at_unique x1",
                "specialize beta_at_unique (S l)", "specialize beta_at_unique n",
                "specialize beta_at_unique x6", "apply beta_at_unique",
                "exact hpair_witness_witness_witness_witness_left_right_left",
                "exact hvalue_step_witness_witness_witness_right_right_left",
                "have hfinal_derivative : z = x9",
                "specialize beta_at_unique x2", "specialize beta_at_unique x3",
                "specialize beta_at_unique (S l)", "specialize beta_at_unique z",
                "specialize beta_at_unique x9", "apply beta_at_unique",
                "exact hpair_witness_witness_witness_witness_right_right_left",
                "exact hderivative_step_witness_witness_witness_right_right_left",
                "exists x4", "exists x5", "exists x8", "split",
                "exact hvalue_step_witness_witness_witness_left", "split",
                "exists x", "exists x1", "exists x2", "exists x3", "split", "split",
                "exact hpair_witness_witness_witness_witness_left_left", "split",
                "exact hvalue_step_witness_witness_witness_right_left",
                "intro i", "intro hi",
                "specialize hpair_witness_witness_witness_witness_left_right_right i",
                "apply hpair_witness_witness_witness_witness_left_right_right",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ",
                "exact hi", "split",
                "exact hpair_witness_witness_witness_witness_right_left", "split",
                "exact hderivative_step_witness_witness_witness_right_left",
                "intro i", "intro hi",
                "specialize hpair_witness_witness_witness_witness_right_right_right i",
                "apply hpair_witness_witness_witness_witness_right_right_right",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ",
                "exact hi", "split", "rewrite hfinal_value",
                "exact hvalue_step_witness_witness_witness_right_right_right",
                "rewrite hfinal_derivative", "rewrite <- hcoefficient",
                "exact hderivative_step_witness_witness_witness_right_right_right",
            ),
            "A successor polynomial obeys both exact Horner recurrences: f_new=f_old*t+a and f'_new=f'_old*t+f_old.",
        ),
        spec(
            "beta_horner_derivative_functional",
            f"forall b c t l n z m w. ({pair}) -> ({other}) -> (n = m /\\ z = w)",
            (
                "beta_horner_derivative_empty",
                "beta_horner_derivative_successor_decompose",
                "beta_at_unique",
            ),
            (
                "intro b", "intro c", "intro t", "induction l",
                "intro n", "intro z", "intro m", "intro w", "intro hleft", "intro hright",
                "have hleft_zero : (n = 0 /\\ z = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty t",
                "specialize beta_horner_derivative_empty n",
                "specialize beta_horner_derivative_empty z",
                "apply beta_horner_derivative_empty", "exact hleft",
                "have hright_zero : (m = 0 /\\ w = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty t",
                "specialize beta_horner_derivative_empty m",
                "specialize beta_horner_derivative_empty w",
                "apply beta_horner_derivative_empty", "exact hright",
                "cases hleft_zero", "cases hright_zero", "split",
                "trans 0", "exact hleft_zero_left", "symm", "exact hright_zero_left",
                "trans 0", "exact hleft_zero_right", "symm", "exact hright_zero_right",
                "intro n", "intro z", "intro m", "intro w", "intro hleft", "intro hright",
                "have hfirst : exists a r q. "
                f"(({_at('b','c','l','a',tag='hd_functional_left_coefficient')}) /\\ "
                f"(({_paired_terms('b','c','t','l','r','q',tag='functional_left_prefix')}) /\\ "
                "((n = r * t + a) /\\ z = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose l",
                "specialize beta_horner_derivative_successor_decompose n",
                "specialize beta_horner_derivative_successor_decompose z",
                "apply beta_horner_derivative_successor_decompose", "exact hleft",
                "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness",
                "cases hfirst_witness_witness_witness",
                "cases hfirst_witness_witness_witness_right",
                "cases hfirst_witness_witness_witness_right_right",
                "have hsecond : exists a r q. "
                f"(({_at('b','c','l','a',tag='hd_functional_right_coefficient')}) /\\ "
                f"(({_paired_terms('b','c','t','l','r','q',tag='functional_right_prefix')}) /\\ "
                "((m = r * t + a) /\\ w = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose l",
                "specialize beta_horner_derivative_successor_decompose m",
                "specialize beta_horner_derivative_successor_decompose w",
                "apply beta_horner_derivative_successor_decompose", "exact hright",
                "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_witness",
                "cases hsecond_witness_witness_witness_right",
                "cases hsecond_witness_witness_witness_right_right",
                "have hprefix_equal : (x1 = x4 /\\ x2 = x5)",
                "specialize IH x1", "specialize IH x2", "specialize IH x4",
                "specialize IH x5", "apply IH",
                "exact hfirst_witness_witness_witness_right_left",
                "exact hsecond_witness_witness_witness_right_left",
                "cases hprefix_equal",
                "have hcoefficient_equal : x = x3",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique x",
                "specialize beta_at_unique x3", "apply beta_at_unique",
                "exact hfirst_witness_witness_witness_left",
                "exact hsecond_witness_witness_witness_left", "split",
                "trans x1 * t + x",
                "exact hfirst_witness_witness_witness_right_right_left",
                "trans x4 * t + x3", "congr", "congr",
                "exact hprefix_equal_left", "refl", "exact hcoefficient_equal",
                "symm", "exact hsecond_witness_witness_witness_right_right_left",
                "trans x2 * t + x1",
                "exact hfirst_witness_witness_witness_right_right_right",
                "trans x5 * t + x4", "congr", "congr",
                "exact hprefix_equal_right", "refl", "exact hprefix_equal_left",
                "symm", "exact hsecond_witness_witness_witness_right_right_right",
            ),
            "Both the value and exact formal derivative of every beta-coded polynomial are simultaneously unique.",
        ),
        spec(
            "beta_horner_derivative_second_component_functional",
            f"forall b c t l n z m w. ({pair}) -> ({other}) -> z = w",
            ("beta_horner_derivative_functional",),
            (
                "intro b", "intro c", "intro t", "intro l", "intro n", "intro z",
                "intro m", "intro w", "intro hleft", "intro hright",
                "have hequal : (n = m /\\ z = w)",
                "specialize beta_horner_derivative_functional b",
                "specialize beta_horner_derivative_functional c",
                "specialize beta_horner_derivative_functional t",
                "specialize beta_horner_derivative_functional l",
                "specialize beta_horner_derivative_functional n",
                "specialize beta_horner_derivative_functional z",
                "specialize beta_horner_derivative_functional m",
                "specialize beta_horner_derivative_functional w",
                "apply beta_horner_derivative_functional", "exact hleft", "exact hright",
                "cases hequal", "exact hequal_right",
            ),
            "The formal derivative component is independent of every possible choice of coupled beta trace.",
        ),
        spec(
            "beta_horner_derivative_exists_unique",
            f"forall b c t l. exists n z. (({pair}) /\\ "
            f"forall m w. ({other}) -> (n = m /\\ z = w))",
            ("beta_horner_derivative_value_exists", "beta_horner_derivative_functional"),
            (
                "intro b", "intro c", "intro t", "intro l",
                "specialize beta_horner_derivative_value_exists b",
                "specialize beta_horner_derivative_value_exists c",
                "specialize beta_horner_derivative_value_exists t",
                "specialize beta_horner_derivative_value_exists l",
                "cases beta_horner_derivative_value_exists",
                "cases beta_horner_derivative_value_exists_witness",
                "exists x", "exists x1", "split",
                "exact beta_horner_derivative_value_exists_witness_witness",
                "intro m", "intro w", "intro hother",
                "specialize beta_horner_derivative_functional b",
                "specialize beta_horner_derivative_functional c",
                "specialize beta_horner_derivative_functional t",
                "specialize beta_horner_derivative_functional l",
                "specialize beta_horner_derivative_functional x",
                "specialize beta_horner_derivative_functional x1",
                "specialize beta_horner_derivative_functional m",
                "specialize beta_horner_derivative_functional w",
                "apply beta_horner_derivative_functional",
                "exact beta_horner_derivative_value_exists_witness_witness", "exact hother",
            ),
            "Every arbitrary beta-coded natural polynomial has exactly one simultaneously evaluated value/formal-derivative pair.",
        ),
        spec(
            "beta_horner_derivative_only_functional",
            f"forall b c t l z w. ({derivative}) -> ({other_derivative}) -> z = w",
            ("beta_horner_derivative_second_component_functional",),
            (
                "intro b", "intro c", "intro t", "intro l", "intro z", "intro w",
                "intro hleft", "intro hright", "cases hleft", "cases hright",
                "specialize beta_horner_derivative_second_component_functional b",
                "specialize beta_horner_derivative_second_component_functional c",
                "specialize beta_horner_derivative_second_component_functional t",
                "specialize beta_horner_derivative_second_component_functional l",
                "specialize beta_horner_derivative_second_component_functional x",
                "specialize beta_horner_derivative_second_component_functional z",
                "specialize beta_horner_derivative_second_component_functional x1",
                "specialize beta_horner_derivative_second_component_functional w",
                "apply beta_horner_derivative_second_component_functional",
                "exact hleft_witness", "exact hright_witness",
            ),
            "The exact formal derivative, considered without its accompanying polynomial value, is functional.",
        ),
        spec(
            "beta_horner_derivative_only_exists_unique",
            f"forall b c t l. exists z. (({derivative}) /\\ "
            f"forall w. ({other_derivative}) -> z = w)",
            ("beta_horner_derivative_only_exists", "beta_horner_derivative_only_functional"),
            (
                "intro b", "intro c", "intro t", "intro l",
                "specialize beta_horner_derivative_only_exists b",
                "specialize beta_horner_derivative_only_exists c",
                "specialize beta_horner_derivative_only_exists t",
                "specialize beta_horner_derivative_only_exists l",
                "cases beta_horner_derivative_only_exists", "exists x", "split",
                "exact beta_horner_derivative_only_exists_witness", "intro w", "intro hw",
                "specialize beta_horner_derivative_only_functional b",
                "specialize beta_horner_derivative_only_functional c",
                "specialize beta_horner_derivative_only_functional t",
                "specialize beta_horner_derivative_only_functional l",
                "specialize beta_horner_derivative_only_functional x",
                "specialize beta_horner_derivative_only_functional w",
                "apply beta_horner_derivative_only_functional",
                "exact beta_horner_derivative_only_exists_witness", "exact hw",
            ),
            "Every beta-coded natural polynomial has one and only one exact formal derivative at every evaluation point.",
        ),
        spec(
            "beta_horner_derivative_constant",
            f"forall b c t n z. ({constant}) -> exists a. "
            f"(({_at('b','c','0','a',tag='hd_constant_coefficient')}) /\\ "
            "((n = a) /\\ z = 0))",
            (
                "beta_horner_derivative_successor_decompose",
                "beta_horner_derivative_empty",
                "mul_zero_left",
                "zero_add",
            ),
            (
                "intro b", "intro c", "intro t", "intro n", "intro z", "intro hpair",
                "have hdecomposition : exists a r q. "
                f"(({_at('b','c','0','a',tag='hd_constant_step')}) /\\ "
                f"(({_paired_terms('b','c','t','0','r','q',tag='constant_prefix')}) /\\ "
                "((n = r * t + a) /\\ z = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose 0",
                "specialize beta_horner_derivative_successor_decompose n",
                "specialize beta_horner_derivative_successor_decompose z",
                "apply beta_horner_derivative_successor_decompose", "exact hpair",
                "cases hdecomposition", "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_witness",
                "cases hdecomposition_witness_witness_witness_right",
                "cases hdecomposition_witness_witness_witness_right_right",
                "have hzero : (x1 = 0 /\\ x2 = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty t",
                "specialize beta_horner_derivative_empty x1",
                "specialize beta_horner_derivative_empty x2",
                "apply beta_horner_derivative_empty",
                "exact hdecomposition_witness_witness_witness_right_left",
                "cases hzero", "exists x", "split",
                "exact hdecomposition_witness_witness_witness_left", "split",
                "trans x1 * t + x",
                "exact hdecomposition_witness_witness_witness_right_right_left",
                "rewrite hzero_left", "specialize mul_zero_left t",
                "rewrite mul_zero_left", "specialize zero_add x", "exact zero_add",
                "trans x2 * t + x1",
                "exact hdecomposition_witness_witness_witness_right_right_right",
                "rewrite hzero_right", "rewrite hzero_left",
                "specialize mul_zero_left t", "rewrite mul_zero_left",
                "specialize zero_add 0", "exact zero_add",
            ),
            "A one-coefficient polynomial evaluates to its actual decoded constant and has formal derivative zero.",
        ),
        spec(
            "beta_horner_derivative_linear",
            f"forall b c t n z. ({linear}) -> exists a k. "
            f"(({_at('b','c','0','a',tag='hd_linear_leading')}) /\\ "
            f"(({_at('b','c','S 0','k',tag='hd_linear_constant')}) /\\ "
            "((n = a * t + k) /\\ z = a)))",
            (
                "beta_horner_derivative_successor_decompose",
                "beta_horner_derivative_constant",
                "mul_zero_left",
                "zero_add",
            ),
            (
                "intro b", "intro c", "intro t", "intro n", "intro z", "intro hpair",
                "have hdecomposition : exists a r q. "
                f"(({_at('b','c','S 0','a',tag='hd_linear_step')}) /\\ "
                f"(({_paired_terms('b','c','t','S 0','r','q',tag='linear_prefix')}) /\\ "
                "((n = r * t + a) /\\ z = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose (S 0)",
                "specialize beta_horner_derivative_successor_decompose n",
                "specialize beta_horner_derivative_successor_decompose z",
                "apply beta_horner_derivative_successor_decompose", "exact hpair",
                "cases hdecomposition", "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_witness",
                "cases hdecomposition_witness_witness_witness_right",
                "cases hdecomposition_witness_witness_witness_right_right",
                "have hconstant : exists a. "
                f"(({_at('b','c','0','a',tag='hd_linear_prefix_coefficient')}) /\\ "
                "((x1 = a) /\\ x2 = 0))",
                "specialize beta_horner_derivative_constant b",
                "specialize beta_horner_derivative_constant c",
                "specialize beta_horner_derivative_constant t",
                "specialize beta_horner_derivative_constant x1",
                "specialize beta_horner_derivative_constant x2",
                "apply beta_horner_derivative_constant",
                "exact hdecomposition_witness_witness_witness_right_left",
                "cases hconstant", "cases hconstant_witness", "cases hconstant_witness_right",
                "exists x3", "exists x", "split", "exact hconstant_witness_left",
                "split", "exact hdecomposition_witness_witness_witness_left", "split",
                "trans x1 * t + x",
                "exact hdecomposition_witness_witness_witness_right_right_left",
                "rewrite hconstant_witness_right_left", "refl",
                "trans x2 * t + x1",
                "exact hdecomposition_witness_witness_witness_right_right_right",
                "rewrite hconstant_witness_right_right",
                "rewrite hconstant_witness_right_left",
                "specialize mul_zero_left t", "rewrite mul_zero_left",
                "specialize zero_add x3", "exact zero_add",
            ),
            "A genuine two-coefficient polynomial a*t+k has the exact decoded formal derivative a.",
        ),
    )


@dataclass(frozen=True, slots=True)
class HornerDerivativeStep:
    index: int
    coefficient: int
    previous_value: int
    previous_derivative: int
    value: int
    derivative: int


@dataclass(frozen=True, slots=True)
class HornerDerivativeEvaluation:
    base: int
    coefficients: tuple[int, ...]
    value: int
    derivative: int
    steps: tuple[HornerDerivativeStep, ...]


def evaluate_horner_derivative(
    coefficients: Iterable[int],
    base: int,
) -> HornerDerivativeEvaluation:
    """Compute exact paired Horner values within explicit safe size budgets."""

    if type(base) is not int or base < 0:
        raise PolynomialHenselError("the evaluation point must be a natural integer")
    try:
        values = tuple(coefficients)
    except TypeError as error:
        raise PolynomialHenselError("coefficients must be a finite natural iterable") from error
    if len(values) > MAX_HORNER_COEFFICIENTS:
        raise PolynomialHenselError("polynomial exceeds the bounded certificate size")
    if any(type(item) is not int or item < 0 for item in values):
        raise PolynomialHenselError("every polynomial coefficient must be a natural integer")
    maximum = max((item.bit_length() for item in values), default=0)
    if maximum + len(values) * max(1, base.bit_length()) > MAX_HORNER_OUTPUT_BITS:
        raise PolynomialHenselError("polynomial exceeds the bounded derivative bit budget")
    value = derivative = 0
    steps: list[HornerDerivativeStep] = []
    for index, coefficient in enumerate(values):
        previous_value, previous_derivative = value, derivative
        derivative = previous_derivative * base + previous_value
        value = previous_value * base + coefficient
        steps.append(
            HornerDerivativeStep(
                index,
                coefficient,
                previous_value,
                previous_derivative,
                value,
                derivative,
            )
        )
    return HornerDerivativeEvaluation(base, values, value, derivative, tuple(steps))


def verify_horner_derivative_evaluation(receipt: HornerDerivativeEvaluation) -> bool:
    if type(receipt) is not HornerDerivativeEvaluation:
        return False
    if type(receipt.coefficients) is not tuple or type(receipt.steps) is not tuple:
        return False
    try:
        expected = evaluate_horner_derivative(receipt.coefficients, receipt.base)
    except (PolynomialHenselError, OverflowError, TypeError, ValueError):
        return False
    return type(receipt.value) is int and type(receipt.derivative) is int and receipt == expected


__all__ = (
    "HornerDerivativeEvaluation",
    "HornerDerivativeStep",
    "PolynomialHenselError",
    "evaluate_horner_derivative",
    "horner_derivative_only_relation",
    "horner_derivative_relation",
    "horner_derivative_trace_relation",
    "make_polynomial_hensel_candidate_theorems",
    "verify_horner_derivative_evaluation",
)
