"""Construct actual canonical beta-coded binary digits in first-order HA.

All displayed relations are hygienic authoring abbreviations for formulas in
the unchanged language ``0, S, +, *, =``.  In particular, beta-coded digits,
their base-two Horner value, the Alpha-v22 relational binary length, and actual
modular execution histories remain independent first-order witnesses.

Concrete Python certificates are useful examples, never kernel authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import factorial
from typing import Any, Callable

from .binary_length_candidate import (
    BinaryLengthError,
    MAX_BINARY_LENGTH_VALUE_BITS,
    _length_terms,
    _power_two_terms,
    binary_length_certificate,
    binary_length_relation,
)
from .binary_modular_execution_candidate import (
    BinaryExecutionCertificate,
    BinaryModularExecutionError,
    _digit_prefix_terms,
    _execution_terms,
    execute_binary_digits,
    verify_binary_execution_certificate,
)
from .binary_modular_exponentiation_candidate import (
    binary_exponent_split,
    binary_modular_power,
    binary_modulus_relation,
)
from .finite_fold_surface import _beta_at_term, _binders, _identifier, _variables, all_bits, bit_count
from .polynomial_horner_candidate import _horner_relation_terms


BINARY_DIGIT_CODE_RECODE_EXISTS = "binary_digit_code_recode_exists"
BINARY_DIGIT_PREFIX_RECODE = "binary_digit_prefix_recode"
BINARY_HORNER_PREFIX_RECODE = "binary_horner_prefix_recode"
BINARY_DIGIT_PREFIX_APPEND = "binary_digit_prefix_append"
BINARY_DIGIT_HORNER_APPEND = "binary_digit_horner_append"
BINARY_DIGIT_HALF_BELOW_DOUBLE = "binary_digit_half_below_double"
BINARY_DIGIT_BOUNDED_PREFIX_EXISTS = "binary_digit_bounded_prefix_exists"
BINARY_LENGTH_UPPER_POWER_BOUND = "binary_length_upper_power_bound"
BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH = "binary_exponent_digit_prefix_at_length"
BINARY_EXPONENT_DIGIT_PREFIX_EXISTS = "binary_exponent_digit_prefix_exists"
BINARY_EXPONENT_DIGIT_PREFIX_VALUE_FUNCTIONAL = (
    "binary_exponent_digit_prefix_value_functional"
)
BINARY_CANONICAL_EXPONENT_LENGTH_FUNCTIONAL = (
    "binary_canonical_exponent_length_functional"
)
BINARY_DIGIT_PREFIX_ALL_BITS = "binary_digit_prefix_all_bits"
BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS = "binary_digit_prefix_bit_count_exists"
BINARY_THREE_TIMES_COST_NORMALIZATION = "binary_three_times_cost_normalization"
BINARY_DIGIT_OPERATION_COUNT_EXISTS = "binary_digit_operation_count_exists"
BINARY_DIGIT_OPERATION_COUNT_FUNCTIONAL = "binary_digit_operation_count_functional"
BINARY_DIGIT_OPERATION_COUNT_BOUND = "binary_digit_operation_count_bound"
BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS = (
    "binary_modular_exponent_coded_execution_exists"
)
BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT = (
    "binary_modular_exponent_coded_execution_power_correct"
)
BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL = (
    "binary_modular_exponent_coded_execution_result_functional"
)
BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS_UNIQUE = (
    "binary_modular_exponent_coded_execution_exists_unique"
)
BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND = (
    "binary_modular_execution_bitlength_bound"
)
BINARY_MODULAR_EXECUTION_LOGARITHMIC_BOUND = (
    "binary_modular_execution_logarithmic_bound"
)

MAX_BINARY_DIGIT_EXTRACTION_BITS = min(MAX_BINARY_LENGTH_VALUE_BITS, 4096)
MAX_BINARY_DIGIT_BETA_ENTRIES = 128
MAX_BINARY_DIGIT_BETA_CODE_BITS = 65_536


class BinaryDigitExtractionError(ValueError):
    """A conservative digit relation or bounded example failed validation."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "binary digit extraction binder tag")
    except ValueError as error:
        raise BinaryDigitExtractionError(str(error)) from error


def _arguments(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        result = _variables(*labelled)
        if len(set(result)) != len(result):
            raise ValueError("binary extraction arguments must be distinct identifiers")
        if any(value.startswith(("ff_", "fs_", "pa_", "ph_", "be_", "bd_")) for value in result):
            raise ValueError("generated binary extraction binder captures an argument")
        return result
    except ValueError as error:
        raise BinaryDigitExtractionError(str(error)) from error


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"bd_{_safe(tag)}",
        avoid=tuple(item for item in (code, scale, index, value) if item.isidentifier()),
    )


def _recode_terms(
    old_code: str,
    old_scale: str,
    new_code: str,
    new_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    index = f"bd_index_{safe}"
    value = f"bd_value_{safe}"
    gap = f"bd_gap_{safe}"
    return (
        f"forall {index} {value}. (exists {gap}. {gap} + S {index} = {length}) -> "
        f"({_at(old_code, old_scale, index, value, tag=f'{safe}_old')}) -> "
        f"({_at(new_code, new_scale, index, value, tag=f'{safe}_new')})"
    )


def _digit_code_terms(
    exponent: str,
    length: str,
    code: str,
    scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    digits = _digit_prefix_terms(code, scale, length, tag=f"bd_{safe}_digits")
    horner = _horner_relation_terms(code, scale, "2", length, exponent, tag=f"bd_{safe}_horner")
    return f"(({digits}) /\\ ({horner}))"


def binary_exponent_digit_code(
    exponent: str,
    length: str,
    code: str,
    scale: str,
    *,
    tag: str,
) -> str:
    """Expand a genuine beta-coded binary prefix whose Horner value is exact."""

    arguments = _arguments(
        (exponent, "binary exponent"),
        (length, "binary digit length"),
        (code, "binary digit code"),
        (scale, "binary digit scale"),
    )
    return _digit_code_terms(*arguments, tag=tag)


def _canonical_code_terms(
    exponent: str,
    length: str,
    code: str,
    scale: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    length_relation = _length_terms(
        exponent, length, tag=f"bd_{safe}_length", variables=(exponent, length, code, scale)
    )
    code_relation = _digit_code_terms(exponent, length, code, scale, tag=f"{safe}_code")
    return f"(({length_relation}) /\\ ({code_relation}))"


def binary_canonical_exponent_digit_code(
    exponent: str,
    length: str,
    code: str,
    scale: str,
    *,
    tag: str,
) -> str:
    """Expand canonical BitLen plus an actual equally long exponent digit code."""

    arguments = _arguments(
        (exponent, "binary exponent"),
        (length, "canonical binary length"),
        (code, "binary digit code"),
        (scale, "binary digit scale"),
    )
    return _canonical_code_terms(*arguments, tag=tag)


def _complete_execution_terms(
    exponent: str,
    base: str,
    modulus: str,
    length: str,
    code: str,
    scale: str,
    result: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    canonical = _canonical_code_terms(exponent, length, code, scale, tag=f"{safe}_canonical")
    execution = _execution_terms(code, scale, base, modulus, length, result, tag=f"bd_{safe}_execution")
    power = binary_modular_power(base, exponent, modulus, result, tag=f"bd_{safe}_power")
    return f"(({canonical}) /\\ (({execution}) /\\ ({power})))"


def binary_complete_modular_execution(
    exponent: str,
    base: str,
    modulus: str,
    length: str,
    code: str,
    scale: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand exact canonical digits, a real trace, and its modular-power result."""

    arguments = _arguments(
        (exponent, "binary exponent"),
        (base, "square-and-multiply base"),
        (modulus, "square-and-multiply modulus"),
        (length, "canonical binary length"),
        (code, "binary digit code"),
        (scale, "binary digit scale"),
        (result, "terminal modular residue"),
    )
    return _complete_execution_terms(*arguments, tag=tag)


def _operation_count_terms(
    code: str,
    scale: str,
    length: str,
    operations: str,
    *,
    tag: str,
) -> str:
    safe = _safe(tag)
    (ones,) = _binders(f"bd_{safe}", (code, scale, length, operations), ("ones",))
    counted = bit_count(code, scale, length, ones, tag=f"bd_{safe}_count")
    return f"exists {ones}. (({counted}) /\\ {operations} = (2 + ({length} + {length})) + {ones})"


def binary_execution_operation_count(
    code: str,
    scale: str,
    length: str,
    operations: str,
    *,
    tag: str,
) -> str:
    """Expand the actual cost ``2 + 2*length + beta-coded popcount``."""

    arguments = _arguments(
        (code, "binary digit code"),
        (scale, "binary digit scale"),
        (length, "binary execution length"),
        (operations, "square-and-multiply operation count"),
    )
    return _operation_count_terms(*arguments, tag=tag)


def make_binary_digit_extraction_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return dependency-ordered original-kernel canonical-extraction proofs."""

    old_digits = _digit_prefix_terms("b", "c", "l", tag="bd_old")
    new_digits = _digit_prefix_terms("z", "e", "l", tag="bd_new")
    recode = _recode_terms("b", "c", "z", "e", "l", tag="recode")
    old_horner = _horner_relation_terms("b", "c", "2", "l", "n", tag="bd_old")
    new_horner = _horner_relation_terms("z", "e", "2", "l", "n", tag="bd_new")
    recode_result = (
        "exists z e. "
        f"(({_at('z', 'e', 'l', 'd', tag='recode_terminal')}) /\\ "
        f"({_recode_terms('b', 'c', 'z', 'e', 'l', tag='recode_result')}))"
    )
    append_result = (
        "exists z e. "
        f"(({_at('z', 'e', 'l', 'd', tag='append_terminal')}) /\\ "
        f"(({_digit_prefix_terms('z', 'e', 'S l', tag='bd_append')}) /\\ "
        f"({_recode_terms('b', 'c', 'z', 'e', 'l', tag='append_recode')})))"
    )
    horner_append_result = (
        "exists z e. "
        f"(({_digit_prefix_terms('z', 'e', 'S l', tag='bd_horner_append_digits')}) /\\ "
        f"({_horner_relation_terms('z', 'e', '2', 'S l', 'n', tag='bd_horner_append_value')}))"
    )
    old_step = (
        "exists digit previous current. "
        f"(({_at('b', 'c', 'i', 'digit', tag='transport_digit')}) /\\ "
        f"(({_at('x', 'x1', 'i', 'previous', tag='transport_previous')}) /\\ "
        f"(({_at('x', 'x1', 'S i', 'current', tag='transport_current')}) /\\ "
        "current = previous * 2 + digit)))"
    )
    modulus_guard = binary_modulus_relation("m", tag="bd_modulus")
    canonical = _canonical_code_terms("n", "l", "b", "c", tag="modular_canonical")
    modular_run = _execution_terms("b", "c", "a", "m", "l", "r", tag="bd_modular_run")
    modular_power = binary_modular_power("a", "n", "m", "r", tag="bd_modular_power")
    complete_run = _complete_execution_terms("n", "a", "m", "l", "b", "c", "r", tag="full_run")

    return (
        spec(
            BINARY_DIGIT_CODE_RECODE_EXISTS,
            f"forall b c l d. ({recode_result})",
            ("beta_prefix_extend",),
            (
                "intro b", "intro c", "intro l", "intro d",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c", "specialize beta_prefix_extend d",
                "exact beta_prefix_extend",
            ),
            "Every genuine beta-coded prefix can be recoded while appending any exact last digit.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_RECODE,
            f"forall b c z e l. ({old_digits}) -> ({recode}) -> ({new_digits})",
            ("beta_at_exists", "beta_at_unique"),
            (
                "intro b", "intro c", "intro z", "intro e", "intro l",
                "intro hold", "intro hpreserve", "intro i", "intro d",
                "intro hbound", "intro hnew",
                f"have hsource : exists value. ({_at('b', 'c', 'i', 'value', tag='recode_source')})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists i", "exact beta_at_exists",
                "cases hsource",
                f"have htransport : ({_at('z', 'e', 'i', 'x', tag='recode_transport')})",
                "specialize hpreserve i", "specialize hpreserve x", "apply hpreserve",
                "exact hbound", "exact hsource_witness",
                "have hequal : x = d", "specialize beta_at_unique z",
                "specialize beta_at_unique e", "specialize beta_at_unique i",
                "specialize beta_at_unique x", "specialize beta_at_unique d",
                "apply beta_at_unique", "exact htransport", "exact hnew",
                "have hbit : x = 0 \\/ x = 1", "specialize hold i",
                "specialize hold x", "apply hold", "exact hbound",
                "exact hsource_witness", "rewrite hequal at hbit",
                "rewrite hequal at hbit", "exact hbit",
            ),
            "Recoding that preserves every earlier beta entry preserves its actual zero-or-one digit invariant.",
        ),
        spec(
            BINARY_HORNER_PREFIX_RECODE,
            f"forall b c z e l n. ({recode}) -> ({old_horner}) -> ({new_horner})",
            (),
            (
                "intro b", "intro c", "intro z", "intro e", "intro l", "intro n",
                "intro hpreserve", "intro hhorner", "cases hhorner",
                "cases hhorner_witness", "cases hhorner_witness_witness",
                "cases hhorner_witness_witness_right", "exists x", "exists x1",
                "split", "exact hhorner_witness_witness_left", "split",
                "exact hhorner_witness_witness_right_left", "intro i", "intro hbound",
                f"have hstep : {old_step}",
                "specialize hhorner_witness_witness_right_right i",
                "apply hhorner_witness_witness_right_right", "exact hbound",
                "cases hstep", "cases hstep_witness", "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                "exists x2", "exists x3", "exists x4", "split",
                "specialize hpreserve i", "specialize hpreserve x2", "apply hpreserve",
                "exact hbound", "exact hstep_witness_witness_witness_left",
                "exact hstep_witness_witness_witness_right",
            ),
            "An independently witnessed base-two Horner trace remains valid under every exact prefix recoding.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_APPEND,
            f"forall b c l d. ({old_digits}) -> (d = 0 \\/ d = 1) -> ({append_result})",
            (
                BINARY_DIGIT_CODE_RECODE_EXISTS,
                "finite_lt_succ_eq_or_lt",
                "beta_at_exists",
                "beta_at_unique",
            ),
            (
                "intro b", "intro c", "intro l", "intro d", "intro hdigits", "intro hdigit",
                f"have hcode : {recode_result}",
                f"specialize {BINARY_DIGIT_CODE_RECODE_EXISTS} b",
                f"specialize {BINARY_DIGIT_CODE_RECODE_EXISTS} c",
                f"specialize {BINARY_DIGIT_CODE_RECODE_EXISTS} l",
                f"specialize {BINARY_DIGIT_CODE_RECODE_EXISTS} d",
                f"exact {BINARY_DIGIT_CODE_RECODE_EXISTS}",
                "cases hcode", "cases hcode_witness", "cases hcode_witness_witness",
                "exists x", "exists x1", "split", "exact hcode_witness_witness_left",
                "split", "intro i", "intro a", "intro hbound", "intro hentry",
                "have hcases : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hbound", "cases hcases",
                "rewrite hcases_left at hentry", "rewrite hcases_left at hentry",
                "have hlast : d = a", "specialize beta_at_unique x",
                "specialize beta_at_unique x1", "specialize beta_at_unique l",
                "specialize beta_at_unique d", "specialize beta_at_unique a",
                "apply beta_at_unique", "exact hcode_witness_witness_left", "exact hentry",
                "have hlastbit : d = 0 \\/ d = 1", "exact hdigit",
                "rewrite hlast at hlastbit", "rewrite hlast at hlastbit", "exact hlastbit",
                f"have hsource : exists value. ({_at('b', 'c', 'i', 'value', tag='append_source')})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hsource",
                f"have htransport : ({_at('x', 'x1', 'i', 'x2', tag='append_transport')})",
                "specialize hcode_witness_witness_right i",
                "specialize hcode_witness_witness_right x2",
                "apply hcode_witness_witness_right", "exact hcases_right",
                "exact hsource_witness",
                "have holdvalue : x2 = a", "specialize beta_at_unique x",
                "specialize beta_at_unique x1", "specialize beta_at_unique i",
                "specialize beta_at_unique x2", "specialize beta_at_unique a",
                "apply beta_at_unique", "exact htransport", "exact hentry",
                "have holdbit : x2 = 0 \\/ x2 = 1", "specialize hdigits i",
                "specialize hdigits x2", "apply hdigits", "exact hcases_right",
                "exact hsource_witness", "rewrite holdvalue at holdbit",
                "rewrite holdvalue at holdbit", "exact holdbit",
                "exact hcode_witness_witness_right",
            ),
            "Every valid beta-coded binary prefix can append a real zero-or-one digit without changing any older entry.",
        ),
        spec(
            BINARY_DIGIT_HORNER_APPEND,
            f"forall b c l h d n. ({old_digits}) -> "
            f"({_horner_relation_terms('b', 'c', '2', 'l', 'h', tag='bd_append_old_horner')}) -> "
            f"(d = 0 \\/ d = 1) -> n = (h + h) + d -> ({horner_append_result})",
            (
                BINARY_DIGIT_PREFIX_APPEND,
                BINARY_HORNER_PREFIX_RECODE,
                "beta_horner_eval_exists",
                "beta_horner_eval_successor_decompose",
                "beta_at_unique",
                "beta_horner_eval_functional",
                "mul_comm",
                "two_mul_eq_add_self",
            ),
            (
                "intro b", "intro c", "intro l", "intro h", "intro d", "intro n",
                "intro hdigits", "intro hhorner", "intro hdigit", "intro htarget",
                f"have happend : {append_result}",
                f"specialize {BINARY_DIGIT_PREFIX_APPEND} b",
                f"specialize {BINARY_DIGIT_PREFIX_APPEND} c",
                f"specialize {BINARY_DIGIT_PREFIX_APPEND} l",
                f"specialize {BINARY_DIGIT_PREFIX_APPEND} d",
                f"apply {BINARY_DIGIT_PREFIX_APPEND}", "exact hdigits", "exact hdigit",
                "cases happend", "cases happend_witness", "cases happend_witness_witness",
                "cases happend_witness_witness_right",
                f"have hprefix : ({_horner_relation_terms('x', 'x1', '2', 'l', 'h', tag='bd_append_prefix')})",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} b",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} c",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} x",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} x1",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} l",
                f"specialize {BINARY_HORNER_PREFIX_RECODE} h",
                f"apply {BINARY_HORNER_PREFIX_RECODE}",
                "exact happend_witness_witness_right_right", "exact hhorner",
                f"have hevaluation : exists value. ({_horner_relation_terms('x', 'x1', '2', 'S l', 'value', tag='bd_append_evaluation')})",
                "specialize beta_horner_eval_exists x",
                "specialize beta_horner_eval_exists x1",
                "specialize beta_horner_eval_exists 2",
                "specialize beta_horner_eval_exists (S l)", "exact beta_horner_eval_exists",
                "cases hevaluation",
                "have hdecompose : exists digit half. "
                f"(({_at('x', 'x1', 'l', 'digit', tag='bd_append_last')}) /\\ "
                f"(({_horner_relation_terms('x', 'x1', '2', 'l', 'half', tag='bd_append_half')}) /\\ "
                "x2 = half * 2 + digit))",
                "specialize beta_horner_eval_successor_decompose x",
                "specialize beta_horner_eval_successor_decompose x1",
                "specialize beta_horner_eval_successor_decompose 2",
                "specialize beta_horner_eval_successor_decompose l",
                "specialize beta_horner_eval_successor_decompose x2",
                "apply beta_horner_eval_successor_decompose", "exact hevaluation_witness",
                "cases hdecompose", "cases hdecompose_witness",
                "cases hdecompose_witness_witness", "cases hdecompose_witness_witness_right",
                "have hlast : x3 = d", "specialize beta_at_unique x",
                "specialize beta_at_unique x1", "specialize beta_at_unique l",
                "specialize beta_at_unique x3", "specialize beta_at_unique d",
                "apply beta_at_unique", "exact hdecompose_witness_witness_left",
                "exact happend_witness_witness_left",
                "have hhalf : x4 = h", "specialize beta_horner_eval_functional x",
                "specialize beta_horner_eval_functional x1",
                "specialize beta_horner_eval_functional 2",
                "specialize beta_horner_eval_functional l",
                "specialize beta_horner_eval_functional x4",
                "specialize beta_horner_eval_functional h",
                "apply beta_horner_eval_functional",
                "exact hdecompose_witness_witness_right_left", "exact hprefix",
                "have hdouble : h * 2 = h + h", "trans 2 * h",
                "specialize mul_comm h", "specialize mul_comm 2", "exact mul_comm",
                "specialize two_mul_eq_add_self h", "exact two_mul_eq_add_self",
                "rewrite hhalf at hdecompose_witness_witness_right_right",
                "rewrite hlast at hdecompose_witness_witness_right_right",
                "rewrite hdouble at hdecompose_witness_witness_right_right",
                "have hvalue : x2 = n", "trans (h + h) + d",
                "exact hdecompose_witness_witness_right_right", "symm", "exact htarget",
                "exists x", "exists x1", "split",
                "exact happend_witness_witness_right_left",
                "rewrite <- hvalue", "rewrite <- hvalue", "exact hevaluation_witness",
            ),
            "Append a witnessed zero-or-one beta digit and prove that its new Horner value is exactly twice the prior exponent plus that digit.",
        ),
        spec(
            BINARY_DIGIT_HALF_BELOW_DOUBLE,
            f"forall n h d p. ({binary_exponent_split('n', 'h', 'd', tag='bd_half')}) -> "
            "(exists gap. gap + S n = p + p) -> exists gap. gap + S h = p",
            (
                "le_or_lt",
                "four_square_descent_add_le_add",
                "le_add_right",
                "le_trans",
                "lt_not_le",
            ),
            (
                "intro n", "intro h", "intro d", "intro p", "intro hsplit",
                "intro hbound", "cases hsplit", "specialize le_or_lt p",
                "specialize le_or_lt h", "cases le_or_lt",
                "have hdouble : exists gap. gap + (p + p) = h + h",
                "specialize four_square_descent_add_le_add p",
                "specialize four_square_descent_add_le_add h",
                "specialize four_square_descent_add_le_add p",
                "specialize four_square_descent_add_le_add h",
                "apply four_square_descent_add_le_add", "exact le_or_lt_left",
                "exact le_or_lt_left",
                "have hsum : exists gap. gap + (h + h) = n",
                "rewrite hsplit_right", "specialize le_add_right (h + h)",
                "specialize le_add_right d", "exact le_add_right",
                "have hreverse : exists gap. gap + (p + p) = n",
                "specialize le_trans (p + p)", "specialize le_trans (h + h)",
                "specialize le_trans n", "apply le_trans", "exact hdouble", "exact hsum",
                "exfalso", "specialize lt_not_le n", "specialize lt_not_le (p + p)",
                "apply lt_not_le", "exact hbound", "exact hreverse", "exact le_or_lt_right",
            ),
            "If a binary quotient/digit value is below twice a bound, its exact quotient is below that bound.",
        ),
        spec(
            BINARY_DIGIT_BOUNDED_PREFIX_EXISTS,
            f"forall l p n. ({_power_two_terms('l', 'p', tag='bd_bounded_power')}) -> "
            "(exists gap. gap + S n = p) -> exists b c. "
            f"({_digit_code_terms('n', 'l', 'b', 'c', tag='bounded_result')})",
            (
                "binary_power_two_zero_value",
                "le_of_succ_le_succ",
                "le_zero",
                "beta_horner_eval_exists",
                "beta_horner_eval_empty",
                "binary_digit_prefix_empty",
                "binary_power_two_exists",
                "binary_power_two_successor_double",
                "binary_length_digit_split_exists",
                BINARY_DIGIT_HALF_BELOW_DOUBLE,
                BINARY_DIGIT_HORNER_APPEND,
            ),
            (
                "induction l",
                "intro p", "intro n", "intro hpower", "intro hbound",
                "have hone : p = 1", "specialize binary_power_two_zero_value p",
                "apply binary_power_two_zero_value", "exact hpower",
                "rewrite hone at hbound",
                "have hle : exists gap. gap + n = 0",
                "specialize le_of_succ_le_succ n", "specialize le_of_succ_le_succ 0",
                "apply le_of_succ_le_succ", "exact hbound",
                "have hzero : n = 0", "specialize le_zero n", "apply le_zero", "exact hle",
                f"have hvalue : exists value. ({_horner_relation_terms('0', '0', '2', '0', 'value', tag='bd_empty_value')})",
                "specialize beta_horner_eval_exists 0", "specialize beta_horner_eval_exists 0",
                "specialize beta_horner_eval_exists 2", "specialize beta_horner_eval_exists 0",
                "exact beta_horner_eval_exists", "cases hvalue",
                "have hevalzero : x = 0", "specialize beta_horner_eval_empty 0",
                "specialize beta_horner_eval_empty 0", "specialize beta_horner_eval_empty 2",
                "specialize beta_horner_eval_empty x", "apply beta_horner_eval_empty",
                "exact hvalue_witness",
                "have hequal : x = n", "trans 0", "exact hevalzero", "symm", "exact hzero",
                "exists 0", "exists 0", "split", "specialize binary_digit_prefix_empty 0",
                "specialize binary_digit_prefix_empty 0", "exact binary_digit_prefix_empty",
                "rewrite <- hequal", "rewrite <- hequal", "exact hvalue_witness",
                "intro p", "intro n", "intro hpower", "intro hbound",
                f"have hprevious : exists value. ({_power_two_terms('l', 'value', tag='bd_previous_power')})",
                "specialize binary_power_two_exists l", "exact binary_power_two_exists",
                "cases hprevious",
                "have hdouble : p = x + x",
                "specialize binary_power_two_successor_double l",
                "specialize binary_power_two_successor_double x",
                "specialize binary_power_two_successor_double p",
                "apply binary_power_two_successor_double", "exact hprevious_witness", "exact hpower",
                f"have hsplit : exists half digit. ({binary_exponent_split('n', 'half', 'digit', tag='bd_bounded_split')})",
                "specialize binary_length_digit_split_exists n",
                "exact binary_length_digit_split_exists", "cases hsplit", "cases hsplit_witness",
                "have hhalf : exists gap. gap + S x1 = x",
                f"specialize {BINARY_DIGIT_HALF_BELOW_DOUBLE} n",
                f"specialize {BINARY_DIGIT_HALF_BELOW_DOUBLE} x1",
                f"specialize {BINARY_DIGIT_HALF_BELOW_DOUBLE} x2",
                f"specialize {BINARY_DIGIT_HALF_BELOW_DOUBLE} x",
                f"apply {BINARY_DIGIT_HALF_BELOW_DOUBLE}",
                "exact hsplit_witness_witness", "rewrite hdouble at hbound", "exact hbound",
                f"have hprefix : exists b c. ({_digit_code_terms('x1', 'l', 'b', 'c', tag='bounded_predecessor')})",
                "specialize IH x", "specialize IH x1", "apply IH",
                "exact hprevious_witness", "exact hhalf", "cases hprefix", "cases hprefix_witness",
                "cases hprefix_witness_witness", "cases hsplit_witness_witness",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} x3",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} x4",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} l",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} x1",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} x2",
                f"specialize {BINARY_DIGIT_HORNER_APPEND} n",
                f"apply {BINARY_DIGIT_HORNER_APPEND}",
                "exact hprefix_witness_witness_left", "exact hprefix_witness_witness_right",
                "exact hsplit_witness_witness_left", "exact hsplit_witness_witness_right",
            ),
            "Induction on the exact power exponent constructs a genuine length-l beta-coded binary representation of every natural strictly below 2^l.",
        ),
        spec(
            BINARY_LENGTH_UPPER_POWER_BOUND,
            f"forall n l. ({binary_length_relation('n', 'l', tag='bd_upper_length')}) -> "
            f"exists p. (({_power_two_terms('l', 'p', tag='bd_upper_power')}) /\\ "
            "(exists gap. gap + S n = p))",
            (
                "binary_power_two_exists",
                "binary_power_two_nonzero",
                "one_le_of_ne_zero",
            ),
            (
                "intro n", "intro l", "intro hlength", "cases hlength",
                "cases hlength_left",
                f"have hpower : exists value. ({_power_two_terms('l', 'value', tag='bd_zero_upper')})",
                "specialize binary_power_two_exists l", "exact binary_power_two_exists",
                "cases hpower", "exists x", "split", "exact hpower_witness",
                "have hnonzero : ~(x = 0)", "intro hzero",
                "specialize binary_power_two_nonzero l",
                "specialize binary_power_two_nonzero x",
                "apply binary_power_two_nonzero", "exact hpower_witness", "exact hzero",
                "rewrite hlength_left_left", "specialize one_le_of_ne_zero x",
                "apply one_le_of_ne_zero", "exact hnonzero",
                "cases hlength_right", "cases hlength_right_witness",
                "cases hlength_right_witness_witness",
                "cases hlength_right_witness_witness_witness",
                "cases hlength_right_witness_witness_witness_right",
                "cases hlength_right_witness_witness_witness_right_right",
                "cases hlength_right_witness_witness_witness_right_right_right",
                "cases hlength_right_witness_witness_witness_right_right_right_right",
                "exists x2", "split",
                "exact hlength_right_witness_witness_witness_right_right_right_left",
                "exact hlength_right_witness_witness_witness_right_right_right_right_right",
            ),
            "Every actual BitLen witness supplies the exact beta-coded upper power 2^l and the strict inequality n < 2^l, including zero.",
        ),
        spec(
            BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH,
            f"forall n l. ({binary_length_relation('n', 'l', tag='bd_exact_length')}) -> "
            f"exists b c. ({_digit_code_terms('n', 'l', 'b', 'c', tag='exact_length')})",
            (BINARY_LENGTH_UPPER_POWER_BOUND, BINARY_DIGIT_BOUNDED_PREFIX_EXISTS),
            (
                "intro n", "intro l", "intro hlength",
                "have hupper : exists p. "
                f"(({_power_two_terms('l', 'p', tag='bd_exact_upper')}) /\\ "
                "(exists gap. gap + S n = p))",
                f"specialize {BINARY_LENGTH_UPPER_POWER_BOUND} n",
                f"specialize {BINARY_LENGTH_UPPER_POWER_BOUND} l",
                f"apply {BINARY_LENGTH_UPPER_POWER_BOUND}", "exact hlength",
                "cases hupper", "cases hupper_witness",
                f"specialize {BINARY_DIGIT_BOUNDED_PREFIX_EXISTS} l",
                f"specialize {BINARY_DIGIT_BOUNDED_PREFIX_EXISTS} x",
                f"specialize {BINARY_DIGIT_BOUNDED_PREFIX_EXISTS} n",
                f"apply {BINARY_DIGIT_BOUNDED_PREFIX_EXISTS}",
                "exact hupper_witness_left", "exact hupper_witness_right",
            ),
            "Every canonical binary-length witness constructs a genuine beta-coded equally long zero-or-one prefix whose base-two Horner value is the original exponent.",
        ),
        spec(
            BINARY_EXPONENT_DIGIT_PREFIX_EXISTS,
            "forall n. exists l b c. "
            f"({_canonical_code_terms('n', 'l', 'b', 'c', tag='total_canonical')})",
            ("binary_length_exists", BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH),
            (
                "intro n",
                f"have hlength : exists l. ({binary_length_relation('n', 'l', tag='bd_total_length')})",
                "specialize binary_length_exists n", "exact binary_length_exists",
                "cases hlength",
                f"have hdigits : exists b c. ({_digit_code_terms('n', 'x', 'b', 'c', tag='total_digits')})",
                f"specialize {BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH} n",
                f"specialize {BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH} x",
                f"apply {BINARY_EXPONENT_DIGIT_PREFIX_AT_LENGTH}", "exact hlength_witness",
                "cases hdigits", "cases hdigits_witness",
                "exists x", "exists x1", "exists x2", "split",
                "exact hlength_witness", "exact hdigits_witness_witness",
            ),
            "Every arbitrary natural exponent has an actual canonical-length beta-coded binary digit prefix with exactly that exponent as its Horner value.",
        ),
        spec(
            BINARY_EXPONENT_DIGIT_PREFIX_VALUE_FUNCTIONAL,
            f"forall n N l b c. ({_digit_code_terms('n', 'l', 'b', 'c', tag='value_left')}) -> "
            f"({_digit_code_terms('N', 'l', 'b', 'c', tag='value_right')}) -> n = N",
            ("beta_horner_eval_functional",),
            (
                "intro n", "intro N", "intro l", "intro b", "intro c",
                "intro hleft", "intro hright", "cases hleft", "cases hright",
                "specialize beta_horner_eval_functional b",
                "specialize beta_horner_eval_functional c",
                "specialize beta_horner_eval_functional 2",
                "specialize beta_horner_eval_functional l",
                "specialize beta_horner_eval_functional n",
                "specialize beta_horner_eval_functional N",
                "apply beta_horner_eval_functional", "exact hleft_right", "exact hright_right",
            ),
            "A fixed actual beta-coded binary digit sequence represents exactly one natural Horner exponent.",
        ),
        spec(
            BINARY_CANONICAL_EXPONENT_LENGTH_FUNCTIONAL,
            "forall n l b c L B C. "
            f"({_canonical_code_terms('n', 'l', 'b', 'c', tag='length_left')}) -> "
            f"({_canonical_code_terms('n', 'L', 'B', 'C', tag='length_right')}) -> l = L",
            ("binary_length_functional",),
            (
                "intro n", "intro l", "intro b", "intro c", "intro L", "intro B",
                "intro C", "intro hleft", "intro hright", "cases hleft", "cases hright",
                "specialize binary_length_functional n", "specialize binary_length_functional l",
                "specialize binary_length_functional L", "apply binary_length_functional",
                "exact hleft_left", "exact hright_left",
            ),
            "All canonical beta-coded binary representations of one exponent have the identical genuine BitLen length.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_ALL_BITS,
            f"forall b c l. ({old_digits}) -> ({all_bits('b', 'c', 'l', tag='bd_all_bits')})",
            ("beta_at_exists",),
            (
                "intro b", "intro c", "intro l", "intro hdigits", "intro i", "intro hbound",
                f"have hentry : exists digit. ({_at('b', 'c', 'i', 'digit', tag='all_bits_entry')})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hentry",
                "exists x", "split", "exact hentry_witness", "specialize hdigits i",
                "specialize hdigits x", "apply hdigits", "exact hbound", "exact hentry_witness",
            ),
            "Every universal genuine digit-prefix invariant yields actual beta-decoded zero-or-one witnesses at every position.",
        ),
        spec(
            BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS,
            f"forall b c l. ({old_digits}) -> exists ones. "
            f"({bit_count('b', 'c', 'l', 'ones', tag='bd_prefix_count')})",
            (BINARY_DIGIT_PREFIX_ALL_BITS, "bit_count_exists"),
            (
                "intro b", "intro c", "intro l", "intro hdigits",
                f"have hall : ({all_bits('b', 'c', 'l', tag='bd_count_all')})",
                f"specialize {BINARY_DIGIT_PREFIX_ALL_BITS} b",
                f"specialize {BINARY_DIGIT_PREFIX_ALL_BITS} c",
                f"specialize {BINARY_DIGIT_PREFIX_ALL_BITS} l",
                f"apply {BINARY_DIGIT_PREFIX_ALL_BITS}", "exact hdigits",
                "specialize bit_count_exists b", "specialize bit_count_exists c",
                "specialize bit_count_exists l", "apply bit_count_exists", "exact hall",
            ),
            "Every actual beta-coded binary prefix has an independently beta-witnessed exact population count.",
        ),
        spec(
            BINARY_THREE_TIMES_COST_NORMALIZATION,
            "forall l. (2 + (l + l)) + l = 3 * l + 2",
            ("mul_succ_left", "two_mul_eq_add_self", "add_assoc", "add_comm"),
            (
                "intro l", "have hthree : 3 * l = (l + l) + l", "trans 2 * l + l",
                "specialize mul_succ_left 2", "specialize mul_succ_left l",
                "exact mul_succ_left", "congr", "specialize two_mul_eq_add_self l",
                "exact two_mul_eq_add_self", "refl",
                "trans 2 + ((l + l) + l)", "specialize add_assoc 2",
                "specialize add_assoc (l + l)", "specialize add_assoc l", "exact add_assoc",
                "trans ((l + l) + l) + 2", "specialize add_comm 2",
                "specialize add_comm ((l + l) + l)", "exact add_comm",
                "rewrite hthree", "refl",
            ),
            "The initialization-plus-three-per-digit arithmetic expression is exactly 3*l+2 in the unchanged Peano kernel.",
        ),
        spec(
            BINARY_DIGIT_OPERATION_COUNT_EXISTS,
            f"forall b c l. ({old_digits}) -> exists operations. "
            f"({_operation_count_terms('b', 'c', 'l', 'operations', tag='operation_total')})",
            (BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS,),
            (
                "intro b", "intro c", "intro l", "intro hdigits",
                f"have hcount : exists ones. ({bit_count('b', 'c', 'l', 'ones', tag='bd_operation_count')})",
                f"specialize {BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS} b",
                f"specialize {BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS} c",
                f"specialize {BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS} l",
                f"apply {BINARY_DIGIT_PREFIX_BIT_COUNT_EXISTS}", "exact hdigits", "cases hcount",
                "exists (2 + (l + l)) + x", "exists x", "split", "exact hcount_witness", "refl",
            ),
            "Every actual coded digit prefix has a witnessed operation cost of two initializations, two operations per digit, and one optional multiply per one bit.",
        ),
        spec(
            BINARY_DIGIT_OPERATION_COUNT_FUNCTIONAL,
            f"forall b c l s t. ({_operation_count_terms('b', 'c', 'l', 's', tag='cost_left')}) -> "
            f"({_operation_count_terms('b', 'c', 'l', 't', tag='cost_right')}) -> s = t",
            ("bit_count_functional",),
            (
                "intro b", "intro c", "intro l", "intro s", "intro t", "intro hleft",
                "intro hright", "cases hleft", "cases hleft_witness", "cases hright",
                "cases hright_witness", "have hones : x = x1",
                "specialize bit_count_functional b", "specialize bit_count_functional c",
                "specialize bit_count_functional l", "specialize bit_count_functional x",
                "specialize bit_count_functional x1", "apply bit_count_functional",
                "exact hleft_witness_left", "exact hright_witness_left",
                "rewrite hones at hleft_witness_right", "trans (2 + (l + l)) + x1",
                "exact hleft_witness_right", "symm", "exact hright_witness_right",
            ),
            "The independently witnessed initialization/square/multiply operation count is functional for every fixed beta-coded digit prefix.",
        ),
        spec(
            BINARY_DIGIT_OPERATION_COUNT_BOUND,
            f"forall b c l operations. ({_operation_count_terms('b', 'c', 'l', 'operations', tag='operation_bound')}) -> "
            "exists gap. gap + operations = 3 * l + 2",
            (
                "bit_count_bounded",
                "add_le_add_left",
                BINARY_THREE_TIMES_COST_NORMALIZATION,
            ),
            (
                "intro b", "intro c", "intro l", "intro operations", "intro hcost",
                "cases hcost", "cases hcost_witness",
                "have hones : exists gap. gap + x = l", "specialize bit_count_bounded b",
                "specialize bit_count_bounded c", "specialize bit_count_bounded l",
                "specialize bit_count_bounded x", "apply bit_count_bounded",
                "exact hcost_witness_left",
                "have hscaled : exists gap. gap + ((2 + (l + l)) + x) = (2 + (l + l)) + l",
                "specialize add_le_add_left x", "specialize add_le_add_left l",
                "specialize add_le_add_left (2 + (l + l))", "apply add_le_add_left",
                "exact hones",
                f"have hnormal : (2 + (l + l)) + l = 3 * l + 2",
                f"specialize {BINARY_THREE_TIMES_COST_NORMALIZATION} l",
                f"exact {BINARY_THREE_TIMES_COST_NORMALIZATION}",
                "rewrite <- hcost_witness_right at hscaled", "rewrite hnormal at hscaled",
                "exact hscaled",
            ),
            "The actual beta-counted initialization/square/optional-multiply cost of any binary prefix is at most 3*l+2.",
        ),
        spec(
            BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT,
            f"forall n a m l b c r. ({modulus_guard}) -> ({canonical}) -> "
            f"({modular_run}) -> ({modular_power})",
            ("binary_modular_execution_power_correct",),
            (
                "intro n", "intro a", "intro m", "intro l", "intro b", "intro c",
                "intro r", "intro hmodulus", "intro hcanonical", "intro hexecution",
                "cases hcanonical", "cases hcanonical_right",
                "specialize binary_modular_execution_power_correct b",
                "specialize binary_modular_execution_power_correct c",
                "specialize binary_modular_execution_power_correct a",
                "specialize binary_modular_execution_power_correct m",
                "specialize binary_modular_execution_power_correct l",
                "specialize binary_modular_execution_power_correct n",
                "specialize binary_modular_execution_power_correct r",
                "apply binary_modular_execution_power_correct", "exact hmodulus",
                "exact hcanonical_right_right", "exact hexecution",
            ),
            "Every actual execution driven by canonical digits of the supplied arbitrary exponent has exactly that exponent's proved modular power.",
        ),
        spec(
            BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS,
            f"forall n a m. ({modulus_guard}) -> exists l b c r. "
            f"({_complete_execution_terms('n', 'a', 'm', 'l', 'b', 'c', 'r', tag='total_run')})",
            (
                BINARY_EXPONENT_DIGIT_PREFIX_EXISTS,
                "binary_modular_execution_exists",
                BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT,
            ),
            (
                "intro n", "intro a", "intro m", "intro hmodulus",
                "have hcanonical : exists l b c. "
                f"({_canonical_code_terms('n', 'l', 'b', 'c', tag='total_run_canonical')})",
                f"specialize {BINARY_EXPONENT_DIGIT_PREFIX_EXISTS} n",
                f"exact {BINARY_EXPONENT_DIGIT_PREFIX_EXISTS}",
                "cases hcanonical", "cases hcanonical_witness", "cases hcanonical_witness_witness",
                f"have hdigits : ({_digit_prefix_terms('x1', 'x2', 'x', tag='bd_total_run_digits')})",
                "cases hcanonical_witness_witness_witness",
                "cases hcanonical_witness_witness_witness_right",
                "exact hcanonical_witness_witness_witness_right_left",
                f"have hexecution : exists r. ({_execution_terms('x1', 'x2', 'a', 'm', 'x', 'r', tag='bd_total_run_execution')})",
                "specialize binary_modular_execution_exists x1",
                "specialize binary_modular_execution_exists x2",
                "specialize binary_modular_execution_exists a",
                "specialize binary_modular_execution_exists m",
                "specialize binary_modular_execution_exists x",
                "apply binary_modular_execution_exists", "exact hmodulus", "exact hdigits",
                "cases hexecution", "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hcanonical_witness_witness_witness", "split", "exact hexecution_witness",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} n",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} a",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} m",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} x",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} x1",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} x2",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT} x3",
                f"apply {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_POWER_CORRECT}",
                "exact hmodulus", "exact hcanonical_witness_witness_witness", "exact hexecution_witness",
            ),
            "For every arbitrary natural exponent and guarded modulus, construct canonical beta-coded digits, their full genuine square-and-multiply history, and its proved modular-power result.",
        ),
        spec(
            BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL,
            "forall n a m l b c r L B C s. "
            f"({modulus_guard}) -> ({complete_run}) -> "
            f"({_complete_execution_terms('n', 'a', 'm', 'L', 'B', 'C', 's', tag='other_run')}) -> r = s",
            ("binary_modular_exponentiation_result_functional",),
            (
                "intro n", "intro a", "intro m", "intro l", "intro b", "intro c", "intro r",
                "intro L", "intro B", "intro C", "intro s", "intro hmodulus",
                "intro hleft", "intro hright", "cases hleft", "cases hleft_right",
                "cases hright", "cases hright_right",
                "specialize binary_modular_exponentiation_result_functional a",
                "specialize binary_modular_exponentiation_result_functional n",
                "specialize binary_modular_exponentiation_result_functional m",
                "specialize binary_modular_exponentiation_result_functional r",
                "specialize binary_modular_exponentiation_result_functional s",
                "apply binary_modular_exponentiation_result_functional",
                "exact hleft_right_right", "exact hright_right_right",
            ),
            "Complete actual executions for the same arbitrary exponent have identical canonical residues even when their independently constructed digit codes differ.",
        ),
        spec(
            BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS_UNIQUE,
            f"forall n a m. ({modulus_guard}) -> exists r. "
            "((exists l b c. "
            f"({_complete_execution_terms('n', 'a', 'm', 'l', 'b', 'c', 'r', tag='unique_chosen')})) /\\ "
            "forall s. (exists L B C. "
            f"({_complete_execution_terms('n', 'a', 'm', 'L', 'B', 'C', 's', tag='unique_other')})) -> r = s)",
            (
                BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS,
                BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL,
            ),
            (
                "intro n", "intro a", "intro m", "intro hmodulus",
                "have hfull : exists l b c r. "
                f"({_complete_execution_terms('n', 'a', 'm', 'l', 'b', 'c', 'r', tag='unique_source')})",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} n",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} a",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} m",
                f"apply {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS}", "exact hmodulus",
                "cases hfull", "cases hfull_witness", "cases hfull_witness_witness",
                "cases hfull_witness_witness_witness", "exists x3", "split",
                "exists x", "exists x1", "exists x2", "exact hfull_witness_witness_witness_witness",
                "intro s", "intro hother", "cases hother", "cases hother_witness",
                "cases hother_witness_witness",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} n",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} a",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} m",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x1",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x2",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x3",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x4",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x5",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} x6",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL} s",
                f"apply {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_RESULT_FUNCTIONAL}",
                "exact hmodulus", "exact hfull_witness_witness_witness_witness",
                "exact hother_witness_witness_witness",
            ),
            "Every arbitrary natural exponent has exactly one canonical modular result produced by genuine constructed canonical-length beta-coded execution.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND,
            "forall n a m l b c r operations. "
            f"({complete_run}) -> "
            f"({_operation_count_terms('b', 'c', 'l', 'operations', tag='run_bound_cost')}) -> "
            "exists gap. gap + operations = 3 * l + 2",
            (BINARY_DIGIT_OPERATION_COUNT_BOUND,),
            (
                "intro n", "intro a", "intro m", "intro l", "intro b", "intro c", "intro r",
                "intro operations", "intro hexecution", "intro hcost",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_BOUND} b",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_BOUND} c",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_BOUND} l",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_BOUND} operations",
                f"apply {BINARY_DIGIT_OPERATION_COUNT_BOUND}", "exact hcost",
            ),
            "Every complete actual canonical-length square-and-multiply execution has genuine BitCount-measured operation cost at most 3*BitLen(exponent)+2.",
        ),
        spec(
            BINARY_MODULAR_EXECUTION_LOGARITHMIC_BOUND,
            f"forall n a m. ({modulus_guard}) -> exists l b c r operations. "
            f"(({complete_run}) /\\ "
            f"(({_operation_count_terms('b', 'c', 'l', 'operations', tag='logarithmic_cost')}) /\\ "
            "(exists gap. gap + operations = 3 * l + 2)))",
            (
                BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS,
                BINARY_DIGIT_OPERATION_COUNT_EXISTS,
                BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND,
            ),
            (
                "intro n", "intro a", "intro m", "intro hmodulus",
                "have hfull : exists l b c r. "
                f"({_complete_execution_terms('n', 'a', 'm', 'l', 'b', 'c', 'r', tag='logarithmic_run')})",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} n",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} a",
                f"specialize {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS} m",
                f"apply {BINARY_MODULAR_EXPONENT_CODED_EXECUTION_EXISTS}", "exact hmodulus",
                "cases hfull", "cases hfull_witness", "cases hfull_witness_witness",
                "cases hfull_witness_witness_witness",
                f"have hdigits : ({_digit_prefix_terms('x1', 'x2', 'x', tag='bd_logarithmic_digits')})",
                "cases hfull_witness_witness_witness_witness",
                "cases hfull_witness_witness_witness_witness_left",
                "cases hfull_witness_witness_witness_witness_left_right",
                "exact hfull_witness_witness_witness_witness_left_right_left",
                "have hcost : exists operations. "
                f"({_operation_count_terms('x1', 'x2', 'x', 'operations', tag='logarithmic_chosen')})",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_EXISTS} x1",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_EXISTS} x2",
                f"specialize {BINARY_DIGIT_OPERATION_COUNT_EXISTS} x",
                f"apply {BINARY_DIGIT_OPERATION_COUNT_EXISTS}", "exact hdigits",
                "cases hcost", "exists x", "exists x1", "exists x2", "exists x3", "exists x4",
                "split", "exact hfull_witness_witness_witness_witness", "split",
                "exact hcost_witness",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} n",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} a",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} m",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} x",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} x1",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} x2",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} x3",
                f"specialize {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND} x4",
                f"apply {BINARY_MODULAR_EXECUTION_BITLENGTH_BOUND}",
                "exact hfull_witness_witness_witness_witness", "exact hcost_witness",
            ),
            "For every arbitrary natural exponent and guarded modulus, construct canonical BitLen digits, an actual beta-coded square-and-multiply trace and modular power, the exact beta-counted operation cost, and the constructive bound operations <= 3*BitLen(exponent)+2.",
        ),
    )


@dataclass(frozen=True, slots=True)
class CanonicalBinaryDigitCode:
    """A small actual Gödel-beta digit code; not a kernel proof certificate."""

    exponent: int
    length: int
    code: int
    scale: int
    digits: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CanonicalBinaryExecutionCertificate:
    """Bounded canonical digits, actual execution, and exact operation cost."""

    base: int
    exponent: int
    modulus: int
    bit_length: int
    digits: tuple[int, ...]
    one_count: int
    operation_count: int
    execution: BinaryExecutionCertificate

    @property
    def result(self) -> int:
        return self.execution.result


def _natural(value: int, label: str) -> None:
    if type(value) is not int or value < 0:
        raise BinaryDigitExtractionError(f"{label} must be a non-negative integer")


def encode_canonical_binary_digits(exponent: int) -> CanonicalBinaryDigitCode:
    """Actually CRT-encode a bounded canonical MSB-first beta digit prefix."""

    _natural(exponent, "binary exponent")
    if exponent.bit_length() > MAX_BINARY_DIGIT_EXTRACTION_BITS:
        raise BinaryDigitExtractionError("binary exponent exceeds the bounded extraction bit cap")
    try:
        length = binary_length_certificate(exponent)
    except BinaryLengthError as error:
        raise BinaryDigitExtractionError(str(error)) from error
    digits = tuple(reversed(length.digits_least_significant_first))
    if len(digits) > MAX_BINARY_DIGIT_BETA_ENTRIES:
        raise BinaryDigitExtractionError("binary digit beta prefix exceeds the bounded entry cap")
    scale = 2 * factorial(len(digits))
    projected_bits = sum((1 + (index + 1) * scale).bit_length() for index in range(len(digits)))
    if projected_bits > MAX_BINARY_DIGIT_BETA_CODE_BITS:
        raise BinaryDigitExtractionError("binary digit beta prefix exceeds the bounded code budget")
    code = 0
    previous_modulus = 1
    for index, digit in enumerate(digits):
        modulus = 1 + (index + 1) * scale
        correction = ((digit - code) * pow(previous_modulus, -1, modulus)) % modulus
        code += previous_modulus * correction
        previous_modulus *= modulus
    if code.bit_length() > MAX_BINARY_DIGIT_BETA_CODE_BITS:
        raise BinaryDigitExtractionError("encoded binary digit beta prefix exceeded its code budget")
    encoded = CanonicalBinaryDigitCode(exponent, length.length, code, scale, digits)
    verify_canonical_binary_digit_code(encoded)
    return encoded


def verify_canonical_binary_digit_code(encoded: CanonicalBinaryDigitCode) -> None:
    """Reject noncanonical, oversized, altered, and non-beta concrete digits."""

    if type(encoded) is not CanonicalBinaryDigitCode:
        raise BinaryDigitExtractionError("expected an exact immutable binary digit beta code")
    for name in ("exponent", "length", "code", "scale"):
        _natural(getattr(encoded, name), name)
    if (
        encoded.length < 1
        or encoded.length > MAX_BINARY_DIGIT_BETA_ENTRIES
        or encoded.exponent.bit_length() > MAX_BINARY_DIGIT_EXTRACTION_BITS
        or encoded.code.bit_length() > MAX_BINARY_DIGIT_BETA_CODE_BITS
        or encoded.scale.bit_length() > MAX_BINARY_DIGIT_BETA_CODE_BITS
        or type(encoded.digits) is not tuple
        or len(encoded.digits) != encoded.length
    ):
        raise BinaryDigitExtractionError("binary digit beta code violates its bounded shape")
    if any(type(digit) is not int or digit not in (0, 1) for digit in encoded.digits):
        raise BinaryDigitExtractionError("binary digit beta code contains a non-binary entry")
    expected_length = max(1, encoded.exponent.bit_length())
    if encoded.length != expected_length or encoded.scale != 2 * factorial(encoded.length):
        raise BinaryDigitExtractionError("binary digit beta code has a noncanonical length or scale")
    exponent = 0
    for index, digit in enumerate(encoded.digits):
        if encoded.code % (1 + (index + 1) * encoded.scale) != digit:
            raise BinaryDigitExtractionError("binary digit beta code has a forged decoded entry")
        exponent = exponent * 2 + digit
    if exponent != encoded.exponent or (encoded.exponent and encoded.digits[0] != 1):
        raise BinaryDigitExtractionError("binary digit beta code has a forged Horner exponent")


def execute_canonical_binary_modular_exponentiation(
    base: int,
    exponent: int,
    modulus: int,
) -> CanonicalBinaryExecutionCertificate:
    """Run the actual canonical-length trace and count its optional multiplies."""

    _natural(exponent, "binary exponent")
    if exponent.bit_length() > MAX_BINARY_DIGIT_EXTRACTION_BITS:
        raise BinaryDigitExtractionError("binary exponent exceeds the bounded extraction bit cap")
    try:
        length = binary_length_certificate(exponent)
        digits = tuple(reversed(length.digits_least_significant_first))
        execution = execute_binary_digits(base, modulus, digits)
    except (BinaryLengthError, BinaryModularExecutionError) as error:
        raise BinaryDigitExtractionError(str(error)) from error
    ones = sum(digits)
    certificate = CanonicalBinaryExecutionCertificate(
        base,
        exponent,
        modulus,
        length.length,
        digits,
        ones,
        2 + 2 * length.length + ones,
        execution,
    )
    verify_canonical_binary_execution(certificate)
    return certificate


def verify_canonical_binary_execution(certificate: CanonicalBinaryExecutionCertificate) -> None:
    """Audit bounded examples independently; never grant theorem authority."""

    if type(certificate) is not CanonicalBinaryExecutionCertificate:
        raise BinaryDigitExtractionError("expected an exact immutable canonical execution certificate")
    for name in ("base", "exponent", "modulus", "bit_length", "one_count", "operation_count"):
        _natural(getattr(certificate, name), name)
    if (
        certificate.modulus <= 1
        or certificate.bit_length < 1
        or certificate.bit_length > MAX_BINARY_DIGIT_EXTRACTION_BITS
        or certificate.exponent.bit_length() > MAX_BINARY_DIGIT_EXTRACTION_BITS
        or type(certificate.digits) is not tuple
        or len(certificate.digits) != certificate.bit_length
    ):
        raise BinaryDigitExtractionError("canonical execution violates its bounded shape")
    if any(type(digit) is not int or digit not in (0, 1) for digit in certificate.digits):
        raise BinaryDigitExtractionError("canonical execution contains a non-binary digit")
    if certificate.bit_length != max(1, certificate.exponent.bit_length()):
        raise BinaryDigitExtractionError("canonical execution has a forged binary length")
    if certificate.exponent == 0 and certificate.digits != (0,):
        raise BinaryDigitExtractionError("canonical zero execution must contain exactly one zero digit")
    if certificate.exponent and certificate.digits[0] != 1:
        raise BinaryDigitExtractionError("canonical positive execution has a forged leading digit")
    if certificate.one_count != sum(certificate.digits):
        raise BinaryDigitExtractionError("canonical execution has a forged population count")
    if certificate.operation_count != 2 + 2 * certificate.bit_length + certificate.one_count:
        raise BinaryDigitExtractionError("canonical execution has a forged operation count")
    if certificate.operation_count > 3 * certificate.bit_length + 2:
        raise BinaryDigitExtractionError("canonical execution exceeds its proved operation bound")
    try:
        verify_binary_execution_certificate(certificate.execution)
    except BinaryModularExecutionError as error:
        raise BinaryDigitExtractionError(str(error)) from error
    if (
        certificate.execution.base != certificate.base
        or certificate.execution.modulus != certificate.modulus
        or certificate.execution.digits != certificate.digits
        or certificate.execution.exponent != certificate.exponent
        or certificate.execution.result != pow(certificate.base, certificate.exponent, certificate.modulus)
    ):
        raise BinaryDigitExtractionError("canonical execution has a forged underlying trace or result")


__all__ = [
    "CanonicalBinaryDigitCode",
    "CanonicalBinaryExecutionCertificate",
    "BinaryDigitExtractionError",
    "MAX_BINARY_DIGIT_BETA_CODE_BITS",
    "MAX_BINARY_DIGIT_BETA_ENTRIES",
    "MAX_BINARY_DIGIT_EXTRACTION_BITS",
    "binary_canonical_exponent_digit_code",
    "binary_complete_modular_execution",
    "binary_execution_operation_count",
    "binary_exponent_digit_code",
    "encode_canonical_binary_digits",
    "execute_canonical_binary_modular_exponentiation",
    "make_binary_digit_extraction_candidate_theorems",
    "verify_canonical_binary_digit_code",
    "verify_canonical_binary_execution",
]
