"""Constructive polynomial congruence, Taylor remainders, and Hensel corrections.

All public relations in this candidate expand immediately into the unchanged
first-order Heyting-arithmetic language.  In particular, polynomial values,
formal derivatives, balanced congruence, canonical residue bounds, and Taylor
remainder witnesses are not new axioms, function symbols, or kernel rules.

The exact simple-root Hensel milestone is deliberately not asserted unless its
complete unrestricted-input existence and uniqueness script is independently
accepted by the original kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Any, Callable, Iterable

from .finite_fold_surface import _binders, _identifier, _lt, _variables
from .finite_sum_theorems import _at
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq
from .ha_modular_inverse_candidate import bounded_modular_inverse, coprime
from .polynomial_hensel_candidate import (
    PolynomialHenselError,
    _paired_terms,
    evaluate_horner_derivative,
)
from .polynomial_horner_candidate import (
    MAX_HORNER_COEFFICIENTS,
    MAX_HORNER_OUTPUT_BITS,
    _horner_relation_terms,
)


class PolynomialTaylorHenselError(ValueError):
    """A Taylor relation, canonical correction, or bounded example is invalid."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "polynomial Taylor binder tag")
    except ValueError as error:
        raise PolynomialTaylorHenselError(str(error)) from error


def _arguments(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        arguments = _variables(*labelled)
        if len(arguments) != len(set(arguments)):
            raise ValueError("polynomial Taylor arguments must be distinct")
        if any(
            value.startswith(("ff_", "fs_", "ph_", "hd_", "pth_", "hgcrt_", "hmi_"))
            for value in arguments
        ):
            raise ValueError("generated polynomial Taylor binder captures an argument")
        return arguments
    except ValueError as error:
        raise PolynomialTaylorHenselError(str(error)) from error


def _mod(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    try:
        return balanced_mod_eq(
            modulus,
            left,
            right,
            tag=f"pth_{_safe(tag)}",
            variables=context,
        )
    except ValueError as error:
        raise PolynomialTaylorHenselError(str(error)) from error


def _correction_terms(
    derivative: str,
    modulus: str,
    quotient: str,
    digit: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    bound = _lt(digit, modulus, tag=f"pth_{_safe(tag)}_bound", avoid=context)
    annihilation = _mod(
        modulus,
        f"{quotient} + {derivative} * {digit}",
        "0",
        tag=f"{tag}_annihilation",
        context=context,
    )
    return f"(({bound}) /\\ ({annihilation}))"


def hensel_correction_relation(
    derivative: str,
    modulus: str,
    quotient: str,
    digit: str,
    *,
    tag: str,
) -> str:
    """Expand ``digit < modulus ∧ quotient+derivative*digit ≡ 0``."""

    arguments = _arguments(
        (derivative, "formal derivative"),
        (modulus, "correction modulus"),
        (quotient, "root quotient"),
        (digit, "bounded correction digit"),
    )
    return _correction_terms(*arguments, tag=_safe(tag), context=arguments)


def _taylor_terms(
    code: str,
    scale: str,
    point: str,
    shift: str,
    length: str,
    value: str,
    derivative: str,
    shifted_value: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    pair = _paired_terms(
        code,
        scale,
        point,
        length,
        value,
        derivative,
        tag=f"pth_{safe}_pair",
    )
    shifted = _horner_relation_terms(
        code,
        scale,
        f"({point} + {shift})",
        length,
        shifted_value,
        tag=f"pth_{safe}_shifted",
    )
    identity = (
        f"{shifted_value} = ({value} + {shift} * {derivative}) + "
        f"({shift} * {shift}) * {remainder}"
    )
    return f"(({pair}) /\\ (({shifted}) /\\ ({identity})))"


def horner_taylor_remainder_relation(
    code: str,
    scale: str,
    point: str,
    shift: str,
    length: str,
    value: str,
    derivative: str,
    shifted_value: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand an exact natural Taylor identity with a real remainder witness."""

    arguments = _arguments(
        (code, "coefficient code"),
        (scale, "coefficient scale"),
        (point, "evaluation point"),
        (shift, "natural shift"),
        (length, "coefficient length"),
        (value, "polynomial value"),
        (derivative, "formal derivative"),
        (shifted_value, "shifted polynomial value"),
        (remainder, "quadratic Taylor remainder"),
    )
    return _taylor_terms(*arguments, tag=_safe(tag))


def _right_associated_sum(terms: tuple[str, ...]) -> str:
    if not terms:
        raise PolynomialTaylorHenselError("an algebraic sum cannot be empty")
    if len(terms) == 1:
        return terms[0]
    return f"({terms[0]} + {_right_associated_sum(terms[1:])})"


def _sum_permutation_script(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    """Produce checked adjacent transpositions; never assume a ring tactic."""

    if len(left) != len(right) or sorted(left) != sorted(right):
        raise PolynomialTaylorHenselError("additive permutation changed its summands")
    current = list(left)
    commands: list[str] = []
    for target_index, term in enumerate(right):
        source_index = current.index(term, target_index)
        while source_index > target_index:
            swap_index = source_index - 1
            current[swap_index], current[source_index] = (
                current[source_index], current[swap_index]
            )
            commands.append("trans " + _right_associated_sum(tuple(current)))
            for _ in range(swap_index):
                commands.extend(("congr", "refl"))
            commands.append(
                "apply hensel_add_swap_nested"
                if source_index + 1 < len(current)
                else "apply add_comm"
            )
            source_index -= 1
    commands.append("refl")
    return tuple(commands)


def make_polynomial_taylor_hensel_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return dependency-ordered, original-kernel-checkable Hensel foundations."""

    neg_context = ("k", "q")
    negative = _mod("S k", "q + k * q", "0", tag="negative", context=neg_context)

    correction_context = ("d", "p", "q", "t", "u")
    correction_t = _correction_terms(
        "d", "p", "q", "t", tag="correction_t", context=correction_context
    )
    correction_u = _correction_terms(
        "d", "p", "q", "u", tag="correction_u", context=correction_context
    )
    correction_exists = _correction_terms(
        "d", "p", "q", "t", tag="correction_exists", context=("d", "p", "q", "t")
    )
    coprime_dp = coprime("d", "p", tag="pth_correction")

    step_context = ("m", "x", "y", "r", "s", "a")
    base_mod = _mod("m", "x", "y", tag="step_base", context=step_context)
    prefix_mod = _mod("m", "r", "s", tag="step_prefix", context=step_context)
    step_mod = _mod(
        "m", "r * x + a", "s * y + a", tag="step_result", context=step_context
    )

    dstep_context = ("m", "x", "y", "r", "s", "d", "e")
    dstep_base = _mod("m", "x", "y", tag="dstep_base", context=dstep_context)
    dstep_value = _mod("m", "r", "s", tag="dstep_value", context=dstep_context)
    dstep_derivative = _mod("m", "d", "e", tag="dstep_derivative", context=dstep_context)
    dstep_result = _mod(
        "m", "d * x + r", "e * y + s", tag="dstep_result", context=dstep_context
    )

    eval_context = ("b", "c", "m", "t", "s", "l", "n", "z")
    eval_base = _mod("m", "t", "s", tag="eval_base", context=eval_context)
    eval_left = _horner_relation_terms("b", "c", "t", "l", "n", tag="pth_eval_left")
    eval_right = _horner_relation_terms("b", "c", "s", "l", "z", tag="pth_eval_right")
    eval_result = _mod("m", "n", "z", tag="eval_result", context=eval_context)

    pair_context = ("b", "c", "m", "t", "s", "l", "n", "d", "z", "e")
    pair_base = _mod("m", "t", "s", tag="pair_base", context=pair_context)
    pair_left = _paired_terms("b", "c", "t", "l", "n", "d", tag="pth_pair_left")
    pair_right = _paired_terms("b", "c", "s", "l", "z", "e", tag="pth_pair_right")
    pair_value_result = _mod("m", "n", "z", tag="pair_value_result", context=pair_context)
    pair_derivative_result = _mod(
        "m", "d", "e", tag="pair_derivative_result", context=pair_context
    )

    taylor_pair = _paired_terms("b", "c", "t", "l", "n", "d", tag="pth_taylor_pair")
    taylor_shifted = _horner_relation_terms(
        "b", "c", "(t + h)", "l", "z", tag="pth_taylor_shifted"
    )
    taylor_square = _mod(
        "h * h", "z", "n + h * d", tag="taylor_square",
        context=("b", "c", "t", "h", "l", "n", "d", "z"),
    )
    total_taylor = _taylor_terms(
        "b", "c", "t", "h", "l", "n", "d", "z", "q", tag="total"
    )
    inverse_pair = _paired_terms(
        "b", "c", "a", "l", "n", "d", tag="pth_inverse_pair"
    )
    inverse_result = bounded_modular_inverse("d", "p", "u", tag="pth_root_inverse")
    lift_pair = _paired_terms("b", "c", "a", "l", "n", "d", tag="pth_lift_pair")
    lift_value = _horner_relation_terms(
        "b", "c", "(a + m * t)", "l", "y", tag="pth_lift_value"
    )
    lift_correction = _correction_terms(
        "d", "p", "q", "t", tag="lift_correction",
        context=("b", "c", "a", "l", "n", "d", "m", "p", "s", "q", "t", "y"),
    )

    return (
        spec(
            "hensel_predecessor_annihilates_residue",
            f"forall k q. ({negative})",
            ("mod_eq_predecessor_cancel", "zero_add"),
            (
                "intro k",
                "intro q",
                "specialize mod_eq_predecessor_cancel k",
                "specialize mod_eq_predecessor_cancel 0",
                "specialize mod_eq_predecessor_cancel q",
                "have hz : 0 + q = q",
                "apply zero_add",
                "rewrite hz at mod_eq_predecessor_cancel",
                "exact mod_eq_predecessor_cancel",
            ),
            "The predecessor of every positive modulus gives a witnessed subtraction-free negative residue.",
        ),
        spec(
            "horner_mod_congruence_successor_step",
            f"forall m x y r s a. ({base_mod}) -> ({prefix_mod}) -> ({step_mod})",
            ("mod_eq_mul", "mod_eq_refl", "mod_eq_add"),
            (
                "intro m", "intro x", "intro y", "intro r", "intro s", "intro a",
                "intro hbase", "intro hprefix",
                "have hproduct : "
                + _mod("m", "r * x", "s * y", tag="step_product", context=step_context),
                "specialize mod_eq_mul m", "specialize mod_eq_mul r",
                "specialize mod_eq_mul s", "specialize mod_eq_mul x",
                "specialize mod_eq_mul y", "apply mod_eq_mul",
                "exact hprefix", "exact hbase",
                "have hcoefficient : "
                + _mod("m", "a", "a", tag="step_coefficient", context=step_context),
                "specialize mod_eq_refl m", "specialize mod_eq_refl a",
                "apply mod_eq_refl",
                "specialize mod_eq_add m", "specialize mod_eq_add (r * x)",
                "specialize mod_eq_add (s * y)", "specialize mod_eq_add a",
                "specialize mod_eq_add a", "apply mod_eq_add",
                "exact hproduct", "exact hcoefficient",
            ),
            "One genuine Horner value transition preserves balanced congruence at congruent evaluation points.",
        ),
        spec(
            "horner_derivative_mod_congruence_successor_step",
            f"forall m x y r s d e. ({dstep_base}) -> ({dstep_value}) -> "
            f"({dstep_derivative}) -> ({dstep_result})",
            ("mod_eq_mul", "mod_eq_add"),
            (
                "intro m", "intro x", "intro y", "intro r", "intro s",
                "intro d", "intro e", "intro hbase", "intro hvalue", "intro hderivative",
                "have hproduct : "
                + _mod("m", "d * x", "e * y", tag="dstep_product", context=dstep_context),
                "specialize mod_eq_mul m", "specialize mod_eq_mul d",
                "specialize mod_eq_mul e", "specialize mod_eq_mul x",
                "specialize mod_eq_mul y", "apply mod_eq_mul",
                "exact hderivative", "exact hbase",
                "specialize mod_eq_add m", "specialize mod_eq_add (d * x)",
                "specialize mod_eq_add (e * y)", "specialize mod_eq_add r",
                "specialize mod_eq_add s", "apply mod_eq_add",
                "exact hproduct", "exact hvalue",
            ),
            "One coupled formal-derivative Horner transition preserves balanced value and derivative congruence.",
        ),
        spec(
            "beta_horner_eval_mod_congruence",
            f"forall b c m t s l n z. ({eval_base}) -> ({eval_left}) -> "
            f"({eval_right}) -> ({eval_result})",
            (
                "beta_horner_eval_empty",
                "beta_horner_eval_successor_decompose",
                "beta_at_unique",
                "mod_eq_refl",
                "horner_mod_congruence_successor_step",
            ),
            (
                "intro b", "intro c", "intro m", "intro t", "intro s", "induction l",
                "intro n", "intro z", "intro hbase", "intro hleft", "intro hright",
                "have hzero_left : n = 0",
                "specialize beta_horner_eval_empty b", "specialize beta_horner_eval_empty c",
                "specialize beta_horner_eval_empty t", "specialize beta_horner_eval_empty n",
                "apply beta_horner_eval_empty", "exact hleft",
                "have hzero_right : z = 0",
                "specialize beta_horner_eval_empty b", "specialize beta_horner_eval_empty c",
                "specialize beta_horner_eval_empty s", "specialize beta_horner_eval_empty z",
                "apply beta_horner_eval_empty", "exact hright",
                "rewrite hzero_left", "rewrite hzero_right",
                "specialize mod_eq_refl m", "specialize mod_eq_refl 0", "apply mod_eq_refl",
                "intro n", "intro z", "intro hbase", "intro hleft", "intro hright",
                "have hfirst : exists a r. (("
                + _at("b", "c", "l", "a", tag="pth_eval_first_coefficient")
                + ") /\\ (("
                + _horner_relation_terms("b", "c", "t", "l", "r", tag="pth_eval_first_prefix")
                + ") /\\ n = r * t + a))",
                "specialize beta_horner_eval_successor_decompose b",
                "specialize beta_horner_eval_successor_decompose c",
                "specialize beta_horner_eval_successor_decompose t",
                "specialize beta_horner_eval_successor_decompose l",
                "specialize beta_horner_eval_successor_decompose n",
                "apply beta_horner_eval_successor_decompose", "exact hleft",
                "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness",
                "cases hfirst_witness_witness_right",
                "have hsecond : exists a r. (("
                + _at("b", "c", "l", "a", tag="pth_eval_second_coefficient")
                + ") /\\ (("
                + _horner_relation_terms("b", "c", "s", "l", "r", tag="pth_eval_second_prefix")
                + ") /\\ z = r * s + a))",
                "specialize beta_horner_eval_successor_decompose b",
                "specialize beta_horner_eval_successor_decompose c",
                "specialize beta_horner_eval_successor_decompose s",
                "specialize beta_horner_eval_successor_decompose l",
                "specialize beta_horner_eval_successor_decompose z",
                "apply beta_horner_eval_successor_decompose", "exact hright",
                "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_right",
                "have hcoefficient : x = x2",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique x",
                "specialize beta_at_unique x2", "apply beta_at_unique",
                "exact hfirst_witness_witness_left", "exact hsecond_witness_witness_left",
                "have hprefix : "
                + _mod(
                    "m", "x1", "x3", tag="eval_prefix",
                    context=("b", "c", "m", "t", "s", "l", "n", "z", "x", "x1", "x2", "x3"),
                ),
                "specialize IH x1", "specialize IH x3", "apply IH",
                "exact hbase", "exact hfirst_witness_witness_right_left",
                "exact hsecond_witness_witness_right_left",
                "have hstep : "
                + _mod(
                    "m", "x1 * t + x", "x3 * s + x", tag="eval_step",
                    context=("b", "c", "m", "t", "s", "l", "n", "z", "x", "x1", "x2", "x3"),
                ),
                "specialize horner_mod_congruence_successor_step m",
                "specialize horner_mod_congruence_successor_step t",
                "specialize horner_mod_congruence_successor_step s",
                "specialize horner_mod_congruence_successor_step x1",
                "specialize horner_mod_congruence_successor_step x3",
                "specialize horner_mod_congruence_successor_step x",
                "apply horner_mod_congruence_successor_step", "exact hbase", "exact hprefix",
                "rewrite hfirst_witness_witness_right_right",
                "rewrite hsecond_witness_witness_right_right",
                "rewrite <- hcoefficient", "exact hstep",
            ),
            "Every arbitrary beta-coded natural polynomial preserves balanced congruence between evaluation points.",
        ),
        spec(
            "beta_horner_derivative_mod_congruence",
            f"forall b c m t s l n d z e. ({pair_base}) -> ({pair_left}) -> "
            f"({pair_right}) -> (({pair_value_result}) /\\ ({pair_derivative_result}))",
            (
                "beta_horner_derivative_empty",
                "beta_horner_derivative_successor_decompose",
                "beta_at_unique",
                "mod_eq_refl",
                "horner_mod_congruence_successor_step",
                "horner_derivative_mod_congruence_successor_step",
            ),
            (
                "intro b", "intro c", "intro m", "intro t", "intro s", "induction l",
                "intro n", "intro d", "intro z", "intro e",
                "intro hbase", "intro hleft", "intro hright",
                "have hzero_left : (n = 0 /\\ d = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty t",
                "specialize beta_horner_derivative_empty n",
                "specialize beta_horner_derivative_empty d",
                "apply beta_horner_derivative_empty", "exact hleft",
                "have hzero_right : (z = 0 /\\ e = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty s",
                "specialize beta_horner_derivative_empty z",
                "specialize beta_horner_derivative_empty e",
                "apply beta_horner_derivative_empty", "exact hright",
                "cases hzero_left", "cases hzero_right", "split",
                "rewrite hzero_left_left", "rewrite hzero_right_left",
                "specialize mod_eq_refl m", "specialize mod_eq_refl 0", "apply mod_eq_refl",
                "rewrite hzero_left_right", "rewrite hzero_right_right",
                "specialize mod_eq_refl m", "specialize mod_eq_refl 0", "apply mod_eq_refl",
                "intro n", "intro d", "intro z", "intro e",
                "intro hbase", "intro hleft", "intro hright",
                "have hfirst : exists a r q. (("
                + _at("b", "c", "l", "a", tag="pth_pair_first_coefficient")
                + ") /\\ (("
                + _paired_terms("b", "c", "t", "l", "r", "q", tag="pth_pair_first_prefix")
                + ") /\\ ((n = r * t + a) /\\ d = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose l",
                "specialize beta_horner_derivative_successor_decompose n",
                "specialize beta_horner_derivative_successor_decompose d",
                "apply beta_horner_derivative_successor_decompose", "exact hleft",
                "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness",
                "cases hfirst_witness_witness_witness",
                "cases hfirst_witness_witness_witness_right",
                "cases hfirst_witness_witness_witness_right_right",
                "have hsecond : exists a r q. (("
                + _at("b", "c", "l", "a", tag="pth_pair_second_coefficient")
                + ") /\\ (("
                + _paired_terms("b", "c", "s", "l", "r", "q", tag="pth_pair_second_prefix")
                + ") /\\ ((z = r * s + a) /\\ e = q * s + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose s",
                "specialize beta_horner_derivative_successor_decompose l",
                "specialize beta_horner_derivative_successor_decompose z",
                "specialize beta_horner_derivative_successor_decompose e",
                "apply beta_horner_derivative_successor_decompose", "exact hright",
                "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_witness",
                "cases hsecond_witness_witness_witness_right",
                "cases hsecond_witness_witness_witness_right_right",
                "have hcoefficient : x = x3",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique x",
                "specialize beta_at_unique x3", "apply beta_at_unique",
                "exact hfirst_witness_witness_witness_left",
                "exact hsecond_witness_witness_witness_left",
                "have hprefix : (("
                + _mod(
                    "m", "x1", "x4", tag="pair_prefix_value",
                    context=("b", "c", "m", "t", "s", "l", "n", "d", "z", "e", "x", "x1", "x2", "x3", "x4", "x5"),
                )
                + ") /\\ ("
                + _mod(
                    "m", "x2", "x5", tag="pair_prefix_derivative",
                    context=("b", "c", "m", "t", "s", "l", "n", "d", "z", "e", "x", "x1", "x2", "x3", "x4", "x5"),
                )
                + "))",
                "specialize IH x1", "specialize IH x2",
                "specialize IH x4", "specialize IH x5", "apply IH", "exact hbase",
                "exact hfirst_witness_witness_witness_right_left",
                "exact hsecond_witness_witness_witness_right_left", "cases hprefix",
                "have hvalue : "
                + _mod(
                    "m", "x1 * t + x", "x4 * s + x", tag="pair_value_step",
                    context=("b", "c", "m", "t", "s", "l", "n", "d", "z", "e", "x", "x1", "x2", "x3", "x4", "x5"),
                ),
                "specialize horner_mod_congruence_successor_step m",
                "specialize horner_mod_congruence_successor_step t",
                "specialize horner_mod_congruence_successor_step s",
                "specialize horner_mod_congruence_successor_step x1",
                "specialize horner_mod_congruence_successor_step x4",
                "specialize horner_mod_congruence_successor_step x",
                "apply horner_mod_congruence_successor_step", "exact hbase",
                "exact hprefix_left",
                "have hderivative : "
                + _mod(
                    "m", "x2 * t + x1", "x5 * s + x4", tag="pair_derivative_step",
                    context=("b", "c", "m", "t", "s", "l", "n", "d", "z", "e", "x", "x1", "x2", "x3", "x4", "x5"),
                ),
                "specialize horner_derivative_mod_congruence_successor_step m",
                "specialize horner_derivative_mod_congruence_successor_step t",
                "specialize horner_derivative_mod_congruence_successor_step s",
                "specialize horner_derivative_mod_congruence_successor_step x1",
                "specialize horner_derivative_mod_congruence_successor_step x4",
                "specialize horner_derivative_mod_congruence_successor_step x2",
                "specialize horner_derivative_mod_congruence_successor_step x5",
                "apply horner_derivative_mod_congruence_successor_step",
                "exact hbase", "exact hprefix_left", "exact hprefix_right", "split",
                "rewrite hfirst_witness_witness_witness_right_right_left",
                "rewrite hsecond_witness_witness_witness_right_right_left",
                "rewrite <- hcoefficient", "exact hvalue",
                "rewrite hfirst_witness_witness_witness_right_right_right",
                "rewrite hsecond_witness_witness_witness_right_right_right",
                "exact hderivative",
            ),
            "Every beta-coded natural polynomial and its exact formal derivative simultaneously preserve balanced congruence.",
        ),
        spec(
            "hensel_add_swap_nested",
            "forall a b c. a + (b + c) = b + (a + c)",
            ("add_assoc", "add_comm"),
            (
                "intro a", "intro b", "intro c",
                "trans (a + b) + c", "symm", "apply add_assoc",
                "trans (b + a) + c", "congr", "apply add_comm", "refl",
                "apply add_assoc",
            ),
            "Two adjacent natural summands can be swapped inside a right-associated finite sum.",
        ),
        spec(
            "horner_taylor_successor_identity",
            "forall r d h q t a. "
            "(((r + h * d) + (h * h) * q) * (t + h) + a) = "
            "((r * t + a) + h * (d * t + r)) + "
            "(h * h) * (q * (t + h) + d)",
            (
                "add_mul", "mul_add", "mul_assoc", "mul_comm", "add_assoc",
                "add_comm", "hensel_add_swap_nested",
            ),
            (
                "intro r", "intro d", "intro h", "intro q", "intro t", "intro a",
                "simp [add_mul, mul_add, mul_assoc, add_assoc]",
                "have hrh : r * h = h * r", "apply mul_comm",
                "have hdh : d * h = h * d", "apply mul_comm",
                "rewrite hrh", "rewrite hdh",
                "congr", "refl",
            )
            + _sum_permutation_script(
                (
                    "h * r",
                    "h * (d * t)",
                    "h * (h * d)",
                    "h * (h * (q * t))",
                    "h * (h * (q * h))",
                    "a",
                ),
                (
                    "a",
                    "h * (d * t)",
                    "h * r",
                    "h * (h * (q * t))",
                    "h * (h * (q * h))",
                    "h * (h * d)",
                ),
            ),
            "The successor Horner transition has an exact subtraction-free quadratic Taylor remainder.",
        ),
        spec(
            "beta_horner_taylor_remainder_exists",
            f"forall b c t h l n d z. ({taylor_pair}) -> ({taylor_shifted}) -> "
            "exists q. z = (n + h * d) + (h * h) * q",
            (
                "beta_horner_derivative_empty",
                "beta_horner_eval_empty",
                "beta_horner_derivative_successor_decompose",
                "beta_horner_eval_successor_decompose",
                "beta_at_unique",
                "horner_taylor_successor_identity",
            ),
            (
                "intro b", "intro c", "intro t", "intro h", "induction l",
                "intro n", "intro d", "intro z", "intro hpair", "intro hshifted",
                "have hzero_pair : (n = 0 /\\ d = 0)",
                "specialize beta_horner_derivative_empty b",
                "specialize beta_horner_derivative_empty c",
                "specialize beta_horner_derivative_empty t",
                "specialize beta_horner_derivative_empty n",
                "specialize beta_horner_derivative_empty d",
                "apply beta_horner_derivative_empty", "exact hpair",
                "have hzero_shifted : z = 0",
                "specialize beta_horner_eval_empty b",
                "specialize beta_horner_eval_empty c",
                "specialize beta_horner_eval_empty (t + h)",
                "specialize beta_horner_eval_empty z",
                "apply beta_horner_eval_empty", "exact hshifted",
                "cases hzero_pair", "exists 0",
                "rewrite hzero_shifted", "rewrite hzero_pair_left",
                "rewrite hzero_pair_right", "simp",
                "intro n", "intro d", "intro z", "intro hpair", "intro hshifted",
                "have hfirst : exists a r q. (("
                + _at("b", "c", "l", "a", tag="pth_taylor_first_coefficient")
                + ") /\\ (("
                + _paired_terms("b", "c", "t", "l", "r", "q", tag="pth_taylor_first_prefix")
                + ") /\\ ((n = r * t + a) /\\ d = q * t + r)))",
                "specialize beta_horner_derivative_successor_decompose b",
                "specialize beta_horner_derivative_successor_decompose c",
                "specialize beta_horner_derivative_successor_decompose t",
                "specialize beta_horner_derivative_successor_decompose l",
                "specialize beta_horner_derivative_successor_decompose n",
                "specialize beta_horner_derivative_successor_decompose d",
                "apply beta_horner_derivative_successor_decompose", "exact hpair",
                "cases hfirst", "cases hfirst_witness", "cases hfirst_witness_witness",
                "cases hfirst_witness_witness_witness",
                "cases hfirst_witness_witness_witness_right",
                "cases hfirst_witness_witness_witness_right_right",
                "have hsecond : exists a r. (("
                + _at("b", "c", "l", "a", tag="pth_taylor_second_coefficient")
                + ") /\\ (("
                + _horner_relation_terms(
                    "b", "c", "(t + h)", "l", "r", tag="pth_taylor_second_prefix"
                )
                + ") /\\ z = r * (t + h) + a))",
                "specialize beta_horner_eval_successor_decompose b",
                "specialize beta_horner_eval_successor_decompose c",
                "specialize beta_horner_eval_successor_decompose (t + h)",
                "specialize beta_horner_eval_successor_decompose l",
                "specialize beta_horner_eval_successor_decompose z",
                "apply beta_horner_eval_successor_decompose", "exact hshifted",
                "cases hsecond", "cases hsecond_witness", "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_right",
                "have hcoefficient : x = x3",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique x",
                "specialize beta_at_unique x3", "apply beta_at_unique",
                "exact hfirst_witness_witness_witness_left",
                "exact hsecond_witness_witness_left",
                "have hprefix : exists q. x4 = (x1 + h * x2) + (h * h) * q",
                "specialize IH x1", "specialize IH x2", "specialize IH x4",
                "apply IH", "exact hfirst_witness_witness_witness_right_left",
                "exact hsecond_witness_witness_right_left", "cases hprefix",
                "exists x5 * (t + h) + x2",
                "rewrite hsecond_witness_witness_right_right",
                "rewrite hfirst_witness_witness_witness_right_right_left",
                "rewrite hfirst_witness_witness_witness_right_right_right",
                "rewrite hprefix_witness", "rewrite <- hcoefficient",
                "specialize horner_taylor_successor_identity x1",
                "specialize horner_taylor_successor_identity x2",
                "specialize horner_taylor_successor_identity h",
                "specialize horner_taylor_successor_identity x5",
                "specialize horner_taylor_successor_identity t",
                "specialize horner_taylor_successor_identity x",
                "exact horner_taylor_successor_identity",
            ),
            "Every beta-coded natural polynomial has an exact witnessed quadratic Taylor remainder at every natural shift.",
        ),
        spec(
            "hensel_correction_exists",
            f"forall d p q. ~(p = 0) -> ({coprime_dp}) -> "
            f"exists t. ({correction_exists})",
            (
                "nonzero_is_succ",
                "coprime_to_is_gcd_one",
                "one_mul",
                "linear_congruence_nonzero_modulus_bounded_constructor",
                "hensel_predecessor_annihilates_residue",
                "mod_eq_refl",
                "mod_eq_add",
                "mod_eq_trans",
            ),
            (
                "intro d", "intro p", "intro q", "intro hp", "intro hcop",
                "have hsuccessor : exists k. p = S k",
                "specialize nonzero_is_succ p", "apply nonzero_is_succ", "exact hp",
                "cases hsuccessor",
                "have hgcd : (((exists r. d = 1 * r) /\\ "
                "(exists s. p = 1 * s)) /\\ forall j. "
                "(exists u. d = j * u) -> (exists v. p = j * v) -> "
                "exists w. 1 = j * w)",
                "specialize coprime_to_is_gcd_one d",
                "specialize coprime_to_is_gcd_one p",
                "apply coprime_to_is_gcd_one", "exact hcop",
                "have hdivisor : exists w. x * q = 1 * w",
                "exists x * q", "symm", "apply one_mul",
                "have hsolution : exists t. ((exists h. h + S t = p) /\\ ("
                + _mod(
                    "p", "d * t", "x * q", tag="correction_solution",
                    context=("d", "p", "q", "x", "t"),
                )
                + "))",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor d",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor p",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor (x * q)",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor 1",
                "apply linear_congruence_nonzero_modulus_bounded_constructor",
                "exact hgcd", "exact hp", "exact hdivisor",
                "cases hsolution", "cases hsolution_witness",
                "have hsame : "
                + _mod("p", "q", "q", tag="correction_same", context=("d", "p", "q", "x", "x1")),
                "specialize mod_eq_refl p", "specialize mod_eq_refl q",
                "apply mod_eq_refl",
                "have hsum : "
                + _mod(
                    "p", "q + d * x1", "q + x * q", tag="correction_sum",
                    context=("d", "p", "q", "x", "x1"),
                ),
                "specialize mod_eq_add p", "specialize mod_eq_add q",
                "specialize mod_eq_add q", "specialize mod_eq_add (d * x1)",
                "specialize mod_eq_add (x * q)", "apply mod_eq_add",
                "exact hsame", "exact hsolution_witness_right",
                "have hnegative : "
                + _mod(
                    "p", "q + x * q", "0", tag="correction_negative",
                    context=("d", "p", "q", "x", "x1"),
                ),
                "specialize hensel_predecessor_annihilates_residue x",
                "specialize hensel_predecessor_annihilates_residue q",
                "rewrite <- hsuccessor_witness at hensel_predecessor_annihilates_residue",
                "rewrite <- hsuccessor_witness at hensel_predecessor_annihilates_residue",
                "exact hensel_predecessor_annihilates_residue",
                "have hresult : "
                + _mod(
                    "p", "q + d * x1", "0", tag="correction_final",
                    context=("d", "p", "q", "x", "x1"),
                ),
                "specialize mod_eq_trans p", "specialize mod_eq_trans (q + d * x1)",
                "specialize mod_eq_trans (q + x * q)", "specialize mod_eq_trans 0",
                "apply mod_eq_trans", "exact hsum", "exact hnegative",
                "exists x1", "split", "exact hsolution_witness_left", "exact hresult",
            ),
            "Every coprime derivative at a nonzero modulus has an actual strictly bounded subtraction-free root correction.",
        ),
        spec(
            "hensel_correction_unique",
            f"forall d p q t u. ~(p = 0) -> ({coprime_dp}) -> "
            f"({correction_t}) -> ({correction_u}) -> t = u",
            (
                "mod_eq_symm",
                "mod_eq_trans",
                "mod_eq_add_cancel_left",
                "mod_eq_cancel_coprime",
                "mod_eq_bounded_unique",
            ),
            (
                "intro d", "intro p", "intro q", "intro t", "intro u",
                "intro hp", "intro hcop", "intro ht", "intro hu",
                "cases ht", "cases hu",
                "have hreverse : "
                + _mod("p", "0", "q + d * u", tag="correction_reverse", context=correction_context),
                "specialize mod_eq_symm p", "specialize mod_eq_symm (q + d * u)",
                "specialize mod_eq_symm 0", "apply mod_eq_symm", "exact hu_right",
                "have hboth : "
                + _mod(
                    "p", "q + d * t", "q + d * u", tag="correction_both", context=correction_context
                ),
                "specialize mod_eq_trans p", "specialize mod_eq_trans (q + d * t)",
                "specialize mod_eq_trans 0", "specialize mod_eq_trans (q + d * u)",
                "apply mod_eq_trans", "exact ht_right", "exact hreverse",
                "have hscaled : "
                + _mod("p", "d * t", "d * u", tag="correction_scaled", context=correction_context),
                "specialize mod_eq_add_cancel_left p", "specialize mod_eq_add_cancel_left q",
                "specialize mod_eq_add_cancel_left (d * t)",
                "specialize mod_eq_add_cancel_left (d * u)",
                "apply mod_eq_add_cancel_left", "exact hboth",
                "have hdigits : "
                + _mod("p", "t", "u", tag="correction_digits", context=correction_context),
                "specialize mod_eq_cancel_coprime p", "specialize mod_eq_cancel_coprime d",
                "specialize mod_eq_cancel_coprime t", "specialize mod_eq_cancel_coprime u",
                "apply mod_eq_cancel_coprime", "exact hp", "exact hcop", "exact hscaled",
                "specialize mod_eq_bounded_unique p", "specialize mod_eq_bounded_unique t",
                "specialize mod_eq_bounded_unique u", "apply mod_eq_bounded_unique",
                "exact ht_left", "exact hu_left", "exact hdigits",
            ),
            "At every nonzero modulus a coprime derivative has at most one strictly bounded root-correction digit.",
        ),
        spec(
            "hensel_correction_exists_unique",
            f"forall d p q. ~(p = 0) -> ({coprime_dp}) -> exists t. "
            f"(({correction_t}) /\\ forall u. ({correction_u}) -> u = t)",
            ("hensel_correction_exists", "hensel_correction_unique"),
            (
                "intro d", "intro p", "intro q", "intro hp", "intro hcop",
                "have hexists : exists t. ("
                + _correction_terms(
                    "d", "p", "q", "t", tag="unique_exists", context=("d", "p", "q", "t")
                )
                + ")",
                "specialize hensel_correction_exists d",
                "specialize hensel_correction_exists p",
                "specialize hensel_correction_exists q",
                "apply hensel_correction_exists", "exact hp", "exact hcop",
                "cases hexists", "exists x", "split", "exact hexists_witness",
                "intro u", "intro hu",
                "specialize hensel_correction_unique d",
                "specialize hensel_correction_unique p",
                "specialize hensel_correction_unique q",
                "specialize hensel_correction_unique u",
                "specialize hensel_correction_unique x",
                "apply hensel_correction_unique", "exact hp", "exact hcop",
                "exact hu", "exact hexists_witness",
            ),
            "Every coprime formal derivative at a nonzero modulus has exactly one canonical bounded correction digit.",
        ),
        spec(
            "horner_derivative_coprime_bounded_inverse",
            f"forall b c a l n d p. ({inverse_pair}) -> ~(p = 0) -> "
            f"({coprime_dp}) -> exists u. ({inverse_result})",
            ("coprime_bounded_mod_inverse",),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d",
                "intro p", "intro hpair", "intro hp", "intro hcop",
                "specialize coprime_bounded_mod_inverse d",
                "specialize coprime_bounded_mod_inverse p",
                "apply coprime_bounded_mod_inverse", "exact hp", "exact hcop",
            ),
            "An actual evaluated coprime formal derivative has a strictly bounded constructive modular inverse.",
        ),
        spec(
            "beta_horner_taylor_square_congruence",
            f"forall b c t h l n d z. ({taylor_pair}) -> ({taylor_shifted}) -> "
            f"({taylor_square})",
            ("beta_horner_taylor_remainder_exists",),
            (
                "intro b", "intro c", "intro t", "intro h", "intro l", "intro n",
                "intro d", "intro z", "intro hpair", "intro hshifted",
                "have hrem : exists q. z = (n + h * d) + (h * h) * q",
                "specialize beta_horner_taylor_remainder_exists b",
                "specialize beta_horner_taylor_remainder_exists c",
                "specialize beta_horner_taylor_remainder_exists t",
                "specialize beta_horner_taylor_remainder_exists h",
                "specialize beta_horner_taylor_remainder_exists l",
                "specialize beta_horner_taylor_remainder_exists n",
                "specialize beta_horner_taylor_remainder_exists d",
                "specialize beta_horner_taylor_remainder_exists z",
                "apply beta_horner_taylor_remainder_exists", "exact hpair",
                "exact hshifted", "cases hrem", "exists 0", "exists x",
                "rewrite PA5", "rewrite PA3", "exact hrem_witness",
            ),
            "Every polynomial value at a shifted natural point is congruent to its exact first-order Taylor linearization modulo the square shift.",
        ),
        spec(
            "beta_horner_taylor_remainder_total",
            f"forall b c t h l. exists n d z q. ({total_taylor})",
            (
                "beta_horner_derivative_value_exists",
                "beta_horner_eval_exists",
                "beta_horner_taylor_remainder_exists",
            ),
            (
                "intro b", "intro c", "intro t", "intro h", "intro l",
                "have hpair : exists n d. ("
                + _paired_terms("b", "c", "t", "l", "n", "d", tag="pth_total_pair")
                + ")",
                "specialize beta_horner_derivative_value_exists b",
                "specialize beta_horner_derivative_value_exists c",
                "specialize beta_horner_derivative_value_exists t",
                "specialize beta_horner_derivative_value_exists l",
                "exact beta_horner_derivative_value_exists", "cases hpair",
                "cases hpair_witness",
                "have hshifted : exists z. ("
                + _horner_relation_terms(
                    "b", "c", "(t + h)", "l", "z", tag="pth_total_shifted"
                )
                + ")",
                "specialize beta_horner_eval_exists b",
                "specialize beta_horner_eval_exists c",
                "specialize beta_horner_eval_exists (t + h)",
                "specialize beta_horner_eval_exists l", "exact beta_horner_eval_exists",
                "cases hshifted",
                "have hrem : exists q. x2 = (x + h * x1) + (h * h) * q",
                "specialize beta_horner_taylor_remainder_exists b",
                "specialize beta_horner_taylor_remainder_exists c",
                "specialize beta_horner_taylor_remainder_exists t",
                "specialize beta_horner_taylor_remainder_exists h",
                "specialize beta_horner_taylor_remainder_exists l",
                "specialize beta_horner_taylor_remainder_exists x",
                "specialize beta_horner_taylor_remainder_exists x1",
                "specialize beta_horner_taylor_remainder_exists x2",
                "apply beta_horner_taylor_remainder_exists",
                "exact hpair_witness_witness", "exact hshifted_witness",
                "cases hrem", "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hpair_witness_witness", "split",
                "exact hshifted_witness", "exact hrem_witness",
            ),
            "Every coefficient list, natural evaluation point, and natural shift has actual polynomial, derivative, shifted-value, and quadratic-remainder witnesses.",
        ),
        spec(
            "hensel_correction_implies_multiple",
            f"forall d p q t. ~(p = 0) -> ({correction_exists}) -> "
            "exists w. q + d * t = p * w",
            ("mod_eq_zero_to_dvd_nonzero",),
            (
                "intro d", "intro p", "intro q", "intro t", "intro hp", "intro ht",
                "cases ht", "specialize mod_eq_zero_to_dvd_nonzero p",
                "specialize mod_eq_zero_to_dvd_nonzero (q + d * t)",
                "apply mod_eq_zero_to_dvd_nonzero", "exact hp", "exact ht_right",
            ),
            "Every verified bounded Hensel correction supplies an actual natural divisibility witness for its annihilated linear residual.",
        ),
        spec(
            "hensel_linear_correction_multiple",
            "forall m d q t p. (exists w. q + d * t = p * w) -> "
            "exists w. m * q + (m * t) * d = (p * m) * w",
            ("mul_add", "mul_assoc", "mul_comm"),
            (
                "intro m", "intro d", "intro q", "intro t", "intro p", "intro hmultiple",
                "cases hmultiple", "exists x", "trans m * (q + d * t)",
                "symm", "trans m * q + m * (d * t)", "apply mul_add", "congr", "refl",
                "trans m * (t * d)", "congr", "refl", "apply mul_comm",
                "symm", "apply mul_assoc", "rewrite hmultiple_witness",
                "trans (m * p) * x", "symm", "apply mul_assoc",
                "congr", "apply mul_comm", "refl",
            ),
            "A root-correction divisibility witness makes the complete first-order lifted value a multiple of the next modulus.",
        ),
        spec(
            "hensel_square_shift_multiple",
            "forall m t p s. m = p * s -> "
            "exists w. (m * t) * (m * t) = (p * m) * w",
            ("mul_shuffle_four", "mul_assoc", "mul_comm"),
            (
                "intro m", "intro t", "intro p", "intro s", "intro hfactor",
                "exists s * (t * t)", "trans (m * m) * (t * t)",
                "apply mul_shuffle_four",
                "trans ((p * m) * s) * (t * t)", "congr",
                "trans (p * s) * m", "congr", "exact hfactor", "refl",
                "trans p * (s * m)", "apply mul_assoc",
                "trans p * (m * s)", "congr", "refl", "apply mul_comm",
                "symm", "apply mul_assoc", "refl", "apply mul_assoc",
            ),
            "Whenever the old modulus contains its lifting factor, every squared modulus shift is divisible by the next modulus.",
        ),
        spec(
            "beta_horner_hensel_lift_divisibility",
            f"forall b c a l n d m p s q t y. ~(p = 0) -> ({lift_pair}) -> "
            f"({lift_value}) -> m = p * s -> n = m * q -> ({lift_correction}) -> "
            "exists w. y = (p * m) * w",
            (
                "beta_horner_taylor_remainder_exists",
                "hensel_correction_implies_multiple",
                "hensel_linear_correction_multiple",
                "hensel_square_shift_multiple",
                "multiple_mul_right",
                "multiple_add",
            ),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d",
                "intro m", "intro p", "intro s", "intro q", "intro t", "intro y",
                "intro hp", "intro hpair", "intro hvalue", "intro hfactor",
                "intro hroot", "intro hcorrection",
                "have htaylor : exists w. y = (n + (m * t) * d) + "
                "((m * t) * (m * t)) * w",
                "specialize beta_horner_taylor_remainder_exists b",
                "specialize beta_horner_taylor_remainder_exists c",
                "specialize beta_horner_taylor_remainder_exists a",
                "specialize beta_horner_taylor_remainder_exists (m * t)",
                "specialize beta_horner_taylor_remainder_exists l",
                "specialize beta_horner_taylor_remainder_exists n",
                "specialize beta_horner_taylor_remainder_exists d",
                "specialize beta_horner_taylor_remainder_exists y",
                "apply beta_horner_taylor_remainder_exists", "exact hpair",
                "exact hvalue", "cases htaylor",
                "have hcorrection_multiple : exists w. q + d * t = p * w",
                "specialize hensel_correction_implies_multiple d",
                "specialize hensel_correction_implies_multiple p",
                "specialize hensel_correction_implies_multiple q",
                "specialize hensel_correction_implies_multiple t",
                "apply hensel_correction_implies_multiple", "exact hp", "exact hcorrection",
                "have hlinear : exists w. n + (m * t) * d = (p * m) * w",
                "rewrite hroot", "specialize hensel_linear_correction_multiple m",
                "specialize hensel_linear_correction_multiple d",
                "specialize hensel_linear_correction_multiple q",
                "specialize hensel_linear_correction_multiple t",
                "specialize hensel_linear_correction_multiple p",
                "apply hensel_linear_correction_multiple", "exact hcorrection_multiple",
                "have hsquare : exists w. (m * t) * (m * t) = (p * m) * w",
                "specialize hensel_square_shift_multiple m",
                "specialize hensel_square_shift_multiple t",
                "specialize hensel_square_shift_multiple p",
                "specialize hensel_square_shift_multiple s",
                "apply hensel_square_shift_multiple", "exact hfactor",
                "have hquadratic : exists w. ((m * t) * (m * t)) * x = (p * m) * w",
                "specialize multiple_mul_right (p * m)",
                "specialize multiple_mul_right ((m * t) * (m * t))",
                "specialize multiple_mul_right x", "apply multiple_mul_right",
                "exact hsquare",
                "have hsum : exists w. (n + (m * t) * d) + "
                "((m * t) * (m * t)) * x = (p * m) * w",
                "specialize multiple_add (p * m)",
                "specialize multiple_add (n + (m * t) * d)",
                "specialize multiple_add (((m * t) * (m * t)) * x)",
                "apply multiple_add", "exact hlinear", "exact hquadratic",
                "cases hsum", "exists x1", "trans (n + (m * t) * d) + "
                "((m * t) * (m * t)) * x", "exact htaylor_witness",
                "exact hsum_witness",
            ),
            "A real bounded simple-root correction lifts an arbitrary beta-coded polynomial root from m to p*m whenever p divides m.",
        ),
        spec(
            "beta_horner_hensel_lift_exists",
            f"forall b c a l n d m p s q. ~(p = 0) -> ({lift_pair}) -> "
            "m = p * s -> n = m * q -> "
            f"({coprime_dp}) -> exists t y. (({lift_correction}) /\\ "
            f"(({lift_value}) /\\ exists w. y = (p * m) * w))",
            (
                "hensel_correction_exists",
                "beta_horner_eval_exists",
                "beta_horner_hensel_lift_divisibility",
            ),
            (
                "intro b", "intro c", "intro a", "intro l", "intro n", "intro d",
                "intro m", "intro p", "intro s", "intro q", "intro hp", "intro hpair",
                "intro hfactor", "intro hroot", "intro hcop",
                "have hcorrection : exists t. ("
                + _correction_terms(
                    "d", "p", "q", "t", tag="lift_exists_correction",
                    context=("b", "c", "a", "l", "n", "d", "m", "p", "s", "q", "t"),
                )
                + ")",
                "specialize hensel_correction_exists d",
                "specialize hensel_correction_exists p",
                "specialize hensel_correction_exists q",
                "apply hensel_correction_exists", "exact hp", "exact hcop",
                "cases hcorrection",
                "have hvalue : exists y. ("
                + _horner_relation_terms(
                    "b", "c", "(a + m * x)", "l", "y", tag="pth_lift_exists_value"
                )
                + ")",
                "specialize beta_horner_eval_exists b",
                "specialize beta_horner_eval_exists c",
                "specialize beta_horner_eval_exists (a + m * x)",
                "specialize beta_horner_eval_exists l", "exact beta_horner_eval_exists",
                "cases hvalue", "exists x", "exists x1", "split",
                "exact hcorrection_witness", "split", "exact hvalue_witness",
                "specialize beta_horner_hensel_lift_divisibility b",
                "specialize beta_horner_hensel_lift_divisibility c",
                "specialize beta_horner_hensel_lift_divisibility a",
                "specialize beta_horner_hensel_lift_divisibility l",
                "specialize beta_horner_hensel_lift_divisibility n",
                "specialize beta_horner_hensel_lift_divisibility d",
                "specialize beta_horner_hensel_lift_divisibility m",
                "specialize beta_horner_hensel_lift_divisibility p",
                "specialize beta_horner_hensel_lift_divisibility s",
                "specialize beta_horner_hensel_lift_divisibility q",
                "specialize beta_horner_hensel_lift_divisibility x",
                "specialize beta_horner_hensel_lift_divisibility x1",
                "apply beta_horner_hensel_lift_divisibility", "exact hp", "exact hpair",
                "exact hvalue_witness", "exact hfactor", "exact hroot",
                "exact hcorrection_witness",
            ),
            "Every genuinely evaluated coprime simple root modulo a p-divisible modulus has an actual bounded correction and an actual polynomial root modulo the next modulus.",
        ),
    )


@dataclass(frozen=True, slots=True)
class HornerTaylorEvaluation:
    """Bounded illustrative values, never a substitute for a kernel proof."""

    coefficients: tuple[int, ...]
    point: int
    shift: int
    value: int
    derivative: int
    shifted_value: int
    remainder: int


@dataclass(frozen=True, slots=True)
class HenselCorrectionReceipt:
    """A reproducible canonical correction at a genuinely invertible residue."""

    derivative: int
    modulus: int
    quotient: int
    inverse: int
    digit: int


def evaluate_horner_taylor(
    coefficients: Iterable[int], point: int, shift: int
) -> HornerTaylorEvaluation:
    """Compute the exact first-order natural Taylor identity within hard budgets."""

    if type(point) is not int or point < 0:
        raise PolynomialTaylorHenselError("the evaluation point must be a natural integer")
    if type(shift) is not int or shift < 0:
        raise PolynomialTaylorHenselError("the Taylor shift must be a natural integer")
    try:
        values = tuple(coefficients)
    except TypeError as error:
        raise PolynomialTaylorHenselError("coefficients must be a finite natural iterable") from error
    if len(values) > MAX_HORNER_COEFFICIENTS:
        raise PolynomialTaylorHenselError("polynomial exceeds the bounded certificate size")
    if point.bit_length() > MAX_HORNER_OUTPUT_BITS or shift.bit_length() > MAX_HORNER_OUTPUT_BITS:
        raise PolynomialTaylorHenselError("evaluation inputs exceed the bounded Taylor bit budget")
    try:
        initial = evaluate_horner_derivative(values, point)
        shifted = evaluate_horner_derivative(values, point + shift)
    except PolynomialHenselError as error:
        raise PolynomialTaylorHenselError(str(error)) from error
    residual = shifted.value - initial.value - shift * initial.derivative
    if residual < 0:
        raise PolynomialTaylorHenselError("the natural Taylor residual cannot be negative")
    if shift == 0:
        if residual != 0:
            raise PolynomialTaylorHenselError("zero shift must have zero Taylor residual")
        remainder = 0
    else:
        remainder, residue = divmod(residual, shift * shift)
        if residue:
            raise PolynomialTaylorHenselError("the Taylor residual is not square-divisible")
    return HornerTaylorEvaluation(
        values,
        point,
        shift,
        initial.value,
        initial.derivative,
        shifted.value,
        remainder,
    )


def verify_horner_taylor_evaluation(receipt: HornerTaylorEvaluation) -> bool:
    """Fail closed under every malformed or mutated illustrative receipt."""

    if type(receipt) is not HornerTaylorEvaluation or type(receipt.coefficients) is not tuple:
        return False
    if any(
        type(value) is not int
        for value in (
            receipt.point,
            receipt.shift,
            receipt.value,
            receipt.derivative,
            receipt.shifted_value,
            receipt.remainder,
        )
    ):
        return False
    try:
        expected = evaluate_horner_taylor(receipt.coefficients, receipt.point, receipt.shift)
    except (PolynomialTaylorHenselError, ArithmeticError, TypeError, OverflowError):
        return False
    return receipt == expected


def compute_hensel_correction(
    derivative: int,
    modulus: int,
    quotient: int,
) -> HenselCorrectionReceipt:
    """Compute the unique bounded residue without introducing formal proof power."""

    for name, value in (
        ("derivative", derivative),
        ("modulus", modulus),
        ("root quotient", quotient),
    ):
        if type(value) is not int or value < 0:
            raise PolynomialTaylorHenselError(f"the {name} must be a natural integer")
        if value.bit_length() > MAX_HORNER_OUTPUT_BITS:
            raise PolynomialTaylorHenselError(f"the {name} exceeds the bounded bit budget")
    if modulus == 0:
        raise PolynomialTaylorHenselError("the correction modulus must be nonzero")
    if gcd(derivative, modulus) != 1:
        raise PolynomialTaylorHenselError("the formal derivative and modulus must be coprime")
    inverse = pow(derivative, -1, modulus)
    digit = (-quotient * inverse) % modulus
    if not 0 <= digit < modulus or (quotient + derivative * digit) % modulus:
        raise PolynomialTaylorHenselError("the canonical correction failed verification")
    return HenselCorrectionReceipt(derivative, modulus, quotient, inverse, digit)


def verify_hensel_correction(receipt: HenselCorrectionReceipt) -> bool:
    if type(receipt) is not HenselCorrectionReceipt:
        return False
    if any(
        type(value) is not int
        for value in (
            receipt.derivative,
            receipt.modulus,
            receipt.quotient,
            receipt.inverse,
            receipt.digit,
        )
    ):
        return False
    try:
        expected = compute_hensel_correction(
            receipt.derivative,
            receipt.modulus,
            receipt.quotient,
        )
    except (PolynomialTaylorHenselError, ArithmeticError, TypeError, OverflowError):
        return False
    return receipt == expected


__all__ = [
    "HenselCorrectionReceipt",
    "HornerTaylorEvaluation",
    "PolynomialTaylorHenselError",
    "compute_hensel_correction",
    "evaluate_horner_taylor",
    "hensel_correction_relation",
    "horner_taylor_remainder_relation",
    "make_polynomial_taylor_hensel_candidate_theorems",
    "verify_hensel_correction",
    "verify_horner_taylor_evaluation",
]
