"""Constructive Euclidean execution and exact, honest G101 prerequisites.

No symbol defined here extends the Peano parser, kernel, or trusted axiom
set.  Human-readable relations are hygienic source expansions into the
unchanged first-order language.  Every theorem is dependency-curried against
already checked Alpha-v20 facts or an earlier row in this same family.

The formal endpoint proves a real beta-coded complete Euclidean execution,
its relational gcd output, and the exact *linear* bound ``steps <= divisor``.
The separate two-step theorem proves the strict halving ingredient required
by the logarithmic analysis.  G101 remains PARTIAL: a checked ``BitLen``
relation and the global logarithmic induction do not yet exist.

The small concrete certificate implementation is an untrusted, aggressively
resource-capped demonstration.  Its numerical bit-length bound is not a
formal theorem and never contributes proof authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd, lcm
from typing import Any, Callable

from .continued_fraction_candidate import _trace_term, continued_fraction_trace
from .finite_fold_surface import _identifier, _lt


MAX_EUCLIDEAN_INPUT_BITS = 128
MAX_EUCLIDEAN_STEPS = 14
MAX_EUCLIDEAN_PACKED_STATE_BITS = 32_768
MAX_EUCLIDEAN_HISTORY_BITS = 262_144


EUCLIDEAN_DIVISION_STEP_EXISTS = "euclidean_division_step_exists"
EUCLIDEAN_DIVISION_STEP_FUNCTIONAL = "euclidean_division_step_functional"
EUCLIDEAN_NEXT_DIVISION_STEP_EXISTS = "euclidean_next_division_step_exists"
EUCLIDEAN_ADD_RIGHT_PRESERVES_LT = "euclidean_add_right_preserves_lt"
EUCLIDEAN_TWO_STEP_QUOTIENT_NONZERO = "euclidean_two_step_quotient_nonzero"
EUCLIDEAN_TWO_STEP_HALVING = "euclidean_two_step_halving"
EUCLIDEAN_TRACE_BOUND_WEAKEN = "euclidean_trace_bound_weaken"
EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR = "euclidean_trace_exists_up_to_linear"
EUCLIDEAN_TRACE_EXISTS_LINEAR = "euclidean_trace_exists_linear"
EUCLIDEAN_EXECUTION_ZERO_DIVISOR = "euclidean_execution_zero_divisor"
EUCLIDEAN_EXECUTION_GCD_CORRECT = "euclidean_execution_gcd_correct"
EUCLIDEAN_EXECUTION_TRACE_CORRECT = "euclidean_execution_trace_correct"
EUCLIDEAN_EXECUTION_EXISTS = "euclidean_execution_exists"
EUCLIDEAN_NONZERO_EXECUTION_EXISTS = "euclidean_nonzero_execution_exists"
EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND = "euclidean_gcd_execution_linear_bound"


def _fresh(tag: str, arguments: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "Euclidean binder tag")
    names = tuple(f"ec_{role}_{safe_tag}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(arguments):
        raise ValueError("generated Euclidean binder captures an argument")
    return names


def _arguments(*items: tuple[str, str]) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in items)


def _gcd_term(
    result: str,
    dividend: str,
    divisor: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    left, right, common, common_left, common_right, greatest = _fresh(
        tag,
        arguments,
        "gcd_left",
        "gcd_right",
        "gcd_common",
        "gcd_common_left",
        "gcd_common_right",
        "gcd_greatest",
    )
    return (
        f"(((exists {left}. {dividend} = {result} * {left}) /\\ "
        f"(exists {right}. {divisor} = {result} * {right})) /\\ "
        f"forall {common}. (exists {common_left}. "
        f"{dividend} = {common} * {common_left}) -> "
        f"(exists {common_right}. {divisor} = {common} * {common_right}) -> "
        f"exists {greatest}. {result} = {common} * {greatest})"
    )


def euclidean_division(
    dividend: str,
    divisor: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand one genuine exact division with a strictly bounded remainder."""

    arguments = _arguments(
        (dividend, "Euclidean dividend"),
        (divisor, "Euclidean divisor"),
        (quotient, "Euclidean quotient"),
        (remainder, "Euclidean remainder"),
    )
    strict = _lt(
        remainder,
        divisor,
        tag=f"ec_{_identifier(tag, 'Euclidean binder tag')}_division",
        avoid=arguments,
    )
    return f"({dividend} = {divisor} * {quotient} + {remainder} /\\ ({strict}))"


def euclidean_halving(divisor: str, remainder: str, *, tag: str) -> str:
    """Expand the exact strict two-step drop ``remainder + remainder < divisor``."""

    arguments = _arguments(
        (divisor, "Euclidean starting divisor"),
        (remainder, "Euclidean second remainder"),
    )
    return _lt(
        f"({remainder} + {remainder})",
        divisor,
        tag=f"ec_{_identifier(tag, 'Euclidean binder tag')}_halving",
        avoid=arguments,
    )


def _execution_term(
    dividend: str,
    divisor: str,
    result: str,
    steps: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    quotient_list, history, scale = _fresh(tag, arguments, "list", "history", "scale")
    owned = arguments + (quotient_list, history, scale)
    trace = _trace_term(
        dividend,
        divisor,
        quotient_list,
        history,
        scale,
        steps,
        tag=f"ec_{tag}_trace",
        arguments=owned,
    )
    result_relation = _gcd_term(
        result, dividend, divisor, tag=f"{tag}_result", arguments=owned
    )
    return (
        f"exists {quotient_list} {history} {scale}. "
        f"(({trace}) /\\ ({result_relation}))"
    )


def euclidean_execution(
    dividend: str,
    divisor: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str:
    """Expand a complete actual beta-coded Euclidean history and its gcd."""

    arguments = _arguments(
        (dividend, "Euclidean initial dividend"),
        (divisor, "Euclidean initial divisor"),
        (result, "Euclidean relational gcd"),
        (steps, "Euclidean execution length"),
    )
    return _execution_term(*arguments, tag=tag, arguments=arguments)


def _bounded_trace(dividend: str, divisor: str, bound: str, *, tag: str) -> str:
    safe_tag = _identifier(tag, "bounded Euclidean trace tag")
    trace = continued_fraction_trace(
        dividend, divisor, "s", "h", "e", "l", tag=f"ec_{safe_tag}_bounded"
    )
    (gap,) = _fresh(safe_tag, (dividend, divisor, "s", "h", "e", "l"), "bound_gap")
    return (
        f"exists s h e l. (({trace}) /\\ "
        f"(exists {gap}. {gap} + l = {bound}))"
    )


def make_euclidean_complexity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the ordered, original-kernel, explicitly PARTIAL G101 family."""

    first = euclidean_division("a", "b", "q", "r", tag="first")
    first_other = euclidean_division("a", "b", "Q", "R", tag="other")
    second = euclidean_division("b", "r", "Q", "t", tag="second")
    strict = _lt("r", "b", tag="ec_add_strict", avoid=("r", "b", "t"))
    shifted = _lt(
        "(r + t)", "(b + t)", tag="ec_add_shifted", avoid=("r", "b", "t")
    )
    halving = euclidean_halving("b", "t", tag="two_step")

    bounded = _bounded_trace("a", "b", "B", tag="induction")
    bounded_weakened = _bounded_trace("a", "b", "S B", tag="weakened")
    reduced = _bounded_trace("b", "x1", "B", tag="reduced")
    reduced_all = _bounded_trace("z", "x1", "B", tag="reduced_all")
    smaller_all = _bounded_trace("z", "b", "B", tag="smaller_all")
    extension_arguments = ("a", "b", "x", "x1", "x2", "x5", "s", "z", "c")
    extension_trace = _trace_term(
        "a",
        "b",
        "s",
        "z",
        "c",
        "S x5",
        tag="ec_induction_extension",
        arguments=extension_arguments,
    )
    extension = (
        "exists s z c. "
        f"((s = S ((x + x2) * S (x + x2) + (x2 + x2))) /\\ "
        f"({extension_trace}))"
    )
    total_bounded = _bounded_trace("a", "b", "b", tag="total")
    total_all = _bounded_trace("z", "b", "b", tag="total_all")

    execution = euclidean_execution("a", "b", "g", "l", tag="execution")
    execution_result = _gcd_term(
        "g", "a", "b", tag="execution_correct", arguments=("a", "b", "g", "l")
    )
    execution_trace = continued_fraction_trace(
        "a", "b", "s", "h", "e", "l", tag="execution_projected"
    )
    zero_execution = _execution_term(
        "a", "0", "a", "0", tag="zero", arguments=("a",)
    )
    positive_execution = _execution_term(
        "a", "b", "g", "S k", tag="positive", arguments=("a", "b", "g", "k")
    )
    linear_execution = euclidean_execution("a", "b", "g", "l", tag="linear")

    return (
        spec(
            EUCLIDEAN_DIVISION_STEP_EXISTS,
            f"forall a b. ~(b = 0) -> exists q r. ({first})",
            ("division_remainder_exists",),
            (
                "intro a",
                "intro b",
                "intro hb",
                "specialize division_remainder_exists b",
                "specialize division_remainder_exists a",
                "apply division_remainder_exists",
                "exact hb",
            ),
            "A nonzero Euclidean divisor constructively yields an exact quotient and strictly smaller remainder.",
        ),
        spec(
            EUCLIDEAN_DIVISION_STEP_FUNCTIONAL,
            "forall a b q r Q R. "
            f"({first}) -> ({first_other}) -> q = Q /\\ r = R",
            ("division_remainder_unique",),
            (
                "intro a",
                "intro b",
                "intro q",
                "intro r",
                "intro Q",
                "intro R",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "specialize division_remainder_unique b",
                "specialize division_remainder_unique a",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique r",
                "specialize division_remainder_unique Q",
                "specialize division_remainder_unique R",
                "apply division_remainder_unique",
                "exact hfirst_left",
                "exact hfirst_right",
                "exact hsecond_left",
                "exact hsecond_right",
            ),
            "Two exact bounded Euclidean divisions of the same inputs have identical quotients and remainders.",
        ),
        spec(
            EUCLIDEAN_NEXT_DIVISION_STEP_EXISTS,
            "forall a b q r. "
            f"({first}) -> ~(r = 0) -> exists Q t. ({second})",
            (EUCLIDEAN_DIVISION_STEP_EXISTS,),
            (
                "intro a",
                "intro b",
                "intro q",
                "intro r",
                "intro hfirst",
                "intro hr",
                "specialize euclidean_division_step_exists b",
                "specialize euclidean_division_step_exists r",
                "apply euclidean_division_step_exists",
                "exact hr",
            ),
            "Every nonterminal Euclidean remainder constructively admits the next genuine bounded division.",
        ),
        spec(
            EUCLIDEAN_ADD_RIGHT_PRESERVES_LT,
            f"forall r b t. ({strict}) -> ({shifted})",
            ("add_le_add_right", "add_succ_left"),
            (
                "intro r",
                "intro b",
                "intro t",
                "intro hlt",
                "specialize add_le_add_right (S r)",
                "specialize add_le_add_right b",
                "specialize add_le_add_right t",
                "have hshift : exists gap. gap + (S r + t) = b + t",
                "apply add_le_add_right",
                "exact hlt",
                "cases hshift",
                "exists x",
                "specialize add_succ_left r",
                "specialize add_succ_left t",
                "rewrite add_succ_left at hshift_witness",
                "exact hshift_witness",
            ),
            "Constructive strict natural order remains strict after adding the same right summand.",
        ),
        spec(
            EUCLIDEAN_TWO_STEP_QUOTIENT_NONZERO,
            f"forall a b q r Q t. ({first}) -> ({second}) -> ~(Q = 0)",
            ("lt_trans", "lt_irrefl_expanded", "zero_add"),
            (
                "intro a",
                "intro b",
                "intro q",
                "intro r",
                "intro Q",
                "intro t",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "intro hzero",
                "have hbt : b = t",
                "trans (r * 0 + t)",
                "rewrite hzero at hsecond_left",
                "exact hsecond_left",
                "simp",
                "specialize zero_add t",
                "exact zero_add",
                "specialize lt_irrefl_expanded r",
                "apply lt_irrefl_expanded",
                "specialize lt_trans r",
                "specialize lt_trans t",
                "specialize lt_trans r",
                "apply lt_trans",
                "rewrite hbt at hfirst_right",
                "exact hfirst_right",
                "exact hsecond_right",
            ),
            "After one strict Euclidean decrease, the quotient of the next division cannot be zero.",
        ),
        spec(
            EUCLIDEAN_TWO_STEP_HALVING,
            f"forall a b q r Q t. ({first}) -> ({second}) -> ({halving})",
            (
                EUCLIDEAN_TWO_STEP_QUOTIENT_NONZERO,
                EUCLIDEAN_ADD_RIGHT_PRESERVES_LT,
                "one_le_of_ne_zero",
                "le_mul_of_one_le_right",
                "add_le_add_right",
                "lt_of_lt_of_le",
            ),
            (
                "intro a",
                "intro b",
                "intro q",
                "intro r",
                "intro Q",
                "intro t",
                "intro hfirst",
                "intro hsecond",
                "have hq : ~(Q = 0)",
                "specialize euclidean_two_step_quotient_nonzero a",
                "specialize euclidean_two_step_quotient_nonzero b",
                "specialize euclidean_two_step_quotient_nonzero q",
                "specialize euclidean_two_step_quotient_nonzero r",
                "specialize euclidean_two_step_quotient_nonzero Q",
                "specialize euclidean_two_step_quotient_nonzero t",
                "intro hzero",
                "apply euclidean_two_step_quotient_nonzero",
                "exact hfirst",
                "exact hsecond",
                "exact hzero",
                "cases hsecond",
                "have hone : exists gap. gap + 1 = Q",
                "specialize one_le_of_ne_zero Q",
                "apply one_le_of_ne_zero",
                "exact hq",
                "have hproduct : exists gap. gap + r = r * Q",
                "specialize le_mul_of_one_le_right r",
                "specialize le_mul_of_one_le_right Q",
                "apply le_mul_of_one_le_right",
                "exact hone",
                "have hsum : exists gap. gap + (r + t) = r * Q + t",
                "specialize add_le_add_right r",
                "specialize add_le_add_right (r * Q)",
                "specialize add_le_add_right t",
                "apply add_le_add_right",
                "exact hproduct",
                "have hstrict : exists gap. gap + S (t + t) = r + t",
                "specialize euclidean_add_right_preserves_lt t",
                "specialize euclidean_add_right_preserves_lt r",
                "specialize euclidean_add_right_preserves_lt t",
                "apply euclidean_add_right_preserves_lt",
                "exact hsecond_right",
                "specialize lt_of_lt_of_le (t + t)",
                "specialize lt_of_lt_of_le (r + t)",
                "specialize lt_of_lt_of_le b",
                "apply lt_of_lt_of_le",
                "exact hstrict",
                "rewrite hsecond_left",
                "exact hsum",
            ),
            "Any two consecutive genuine bounded Euclidean divisions strictly halve the starting divisor: twice the second remainder is smaller.",
        ),
        spec(
            EUCLIDEAN_TRACE_BOUND_WEAKEN,
            f"forall a b B. ({bounded}) -> ({bounded_weakened})",
            ("le_succ",),
            (
                "intro a",
                "intro b",
                "intro B",
                "intro htrace",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_witness",
                "cases htrace_witness_witness_witness",
                "cases htrace_witness_witness_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact htrace_witness_witness_witness_witness_left",
                "specialize le_succ x3",
                "specialize le_succ B",
                "apply le_succ",
                "exact htrace_witness_witness_witness_witness_right",
            ),
            "An already witnessed complete beta-coded history remains within the successor of its original linear step budget.",
        ),
        spec(
            EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR,
            f"forall B b. (exists gap. gap + b = B) -> forall a. ({bounded})",
            (
                "le_zero",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "division_remainder_exists",
                "continued_fraction_empty_trace_exists",
                "continued_fraction_trace_extend",
                "le_refl",
                "succ_le_succ",
                EUCLIDEAN_TRACE_BOUND_WEAKEN,
            ),
            (
                "intro B",
                "induction B",
                "intro b",
                "intro hb",
                "intro a",
                "have hb0 : b = 0",
                "apply le_zero",
                "exact hb",
                "specialize continued_fraction_empty_trace_exists a",
                "cases continued_fraction_empty_trace_exists",
                "cases continued_fraction_empty_trace_exists_witness",
                "exists 0",
                "exists x",
                "exists x1",
                "exists 0",
                "split",
                *(("rewrite hb0",) * 16),
                "exact continued_fraction_empty_trace_exists_witness_witness",
                "specialize le_refl 0",
                "exact le_refl",
                "intro b",
                "intro hb",
                "intro a",
                "specialize le_eq_or_lt b",
                "specialize le_eq_or_lt (S B)",
                "have hsplit : b = S B \\/ exists gap. gap + S b = S B",
                "apply le_eq_or_lt",
                "exact hb",
                "cases hsplit",
                "have hb0 : ~(b = 0)",
                "intro hzero",
                "apply PA1",
                "trans b",
                "symm",
                "exact hsplit_left",
                "exact hzero",
                "have hdivision : exists q r. a = b * q + r /\\ exists gap. gap + S r = b",
                "apply division_remainder_exists",
                "exact hb0",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "have hrB : exists gap. gap + x1 = B",
                "apply le_of_succ_le_succ",
                "rewrite hsplit_left at hdivision_witness_witness_right",
                "exact hdivision_witness_witness_right",
                f"have hsmall : {reduced}",
                "specialize IH x1",
                f"have hall : forall z. ({reduced_all})",
                "apply IH",
                "exact hrB",
                "specialize hall b",
                "exact hall",
                "cases hsmall",
                "cases hsmall_witness",
                "cases hsmall_witness_witness",
                "cases hsmall_witness_witness_witness",
                "cases hsmall_witness_witness_witness_witness",
                f"have hextend : {extension}",
                "specialize continued_fraction_trace_extend a",
                "specialize continued_fraction_trace_extend b",
                "specialize continued_fraction_trace_extend x",
                "specialize continued_fraction_trace_extend x1",
                "specialize continued_fraction_trace_extend x2",
                "specialize continued_fraction_trace_extend x3",
                "specialize continued_fraction_trace_extend x4",
                "specialize continued_fraction_trace_extend x5",
                "apply continued_fraction_trace_extend",
                "exact hdivision_witness_witness_left",
                "exact hdivision_witness_witness_right",
                "exact hsmall_witness_witness_witness_witness_left",
                "cases hextend",
                "cases hextend_witness",
                "cases hextend_witness_witness",
                "cases hextend_witness_witness_witness",
                "exists x6",
                "exists x7",
                "exists x8",
                "exists S x5",
                "split",
                "exact hextend_witness_witness_witness_right",
                "specialize succ_le_succ x5",
                "specialize succ_le_succ B",
                "apply succ_le_succ",
                "exact hsmall_witness_witness_witness_witness_right",
                "have hbB : exists gap. gap + b = B",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "specialize IH b",
                f"have hall : forall z. ({smaller_all})",
                "apply IH",
                "exact hbB",
                "specialize hall a",
                "specialize euclidean_trace_bound_weaken a",
                "specialize euclidean_trace_bound_weaken b",
                "specialize euclidean_trace_bound_weaken B",
                "apply euclidean_trace_bound_weaken",
                "exact hall",
            ),
            "Bounded natural induction constructs an authentic complete Euclidean beta-history using at most B divisions whenever the divisor is at most B.",
        ),
        spec(
            EUCLIDEAN_TRACE_EXISTS_LINEAR,
            f"forall a b. ({total_bounded})",
            ("le_refl", EUCLIDEAN_TRACE_EXISTS_UP_TO_LINEAR),
            (
                "intro a",
                "intro b",
                "specialize euclidean_trace_exists_up_to_linear b",
                "specialize euclidean_trace_exists_up_to_linear b",
                "have hbb : exists gap. gap + b = b",
                "apply le_refl",
                f"have hall : forall z. ({total_all})",
                "apply euclidean_trace_exists_up_to_linear",
                "exact hbb",
                "specialize hall a",
                "exact hall",
            ),
            "Every natural input pair admits an actual terminating Euclidean beta-trace whose exact division count is at most its initial divisor.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_ZERO_DIVISOR,
            f"forall a. ({zero_execution})",
            ("continued_fraction_empty_trace_exists", "is_gcd_zero_right"),
            (
                "intro a",
                "specialize continued_fraction_empty_trace_exists a",
                "cases continued_fraction_empty_trace_exists",
                "cases continued_fraction_empty_trace_exists_witness",
                "exists 0",
                "exists x",
                "exists x1",
                "split",
                "exact continued_fraction_empty_trace_exists_witness_witness",
                "specialize is_gcd_zero_right a",
                "exact is_gcd_zero_right",
            ),
            "The zero-divisor boundary has an actual zero-step beta-history and returns the dividend as its checked relational gcd.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_GCD_CORRECT,
            f"forall a b g l. ({execution}) -> ({execution_result})",
            (),
            (
                "intro a",
                "intro b",
                "intro g",
                "intro l",
                "intro hexecution",
                "cases hexecution",
                "cases hexecution_witness",
                "cases hexecution_witness_witness",
                "cases hexecution_witness_witness_witness",
                "exact hexecution_witness_witness_witness_right",
            ),
            "Every expanded Euclidean execution independently certifies its output against the original relational gcd specification.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_TRACE_CORRECT,
            f"forall a b g l. ({execution}) -> exists s h e. ({execution_trace})",
            (),
            (
                "intro a",
                "intro b",
                "intro g",
                "intro l",
                "intro hexecution",
                "cases hexecution",
                "cases hexecution_witness",
                "cases hexecution_witness_witness",
                "cases hexecution_witness_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exact hexecution_witness_witness_witness_left",
            ),
            "Every expanded Euclidean execution contains an actual complete beta-coded history, not an abstract oracle or opaque trace predicate.",
        ),
        spec(
            EUCLIDEAN_EXECUTION_EXISTS,
            f"forall a b. exists g l. ({execution})",
            ("continued_fraction_trace_exists", "gcd_exists_relational"),
            (
                "intro a",
                "intro b",
                "specialize gcd_exists_relational a",
                "specialize gcd_exists_relational b",
                "cases gcd_exists_relational",
                "specialize continued_fraction_trace_exists a",
                "specialize continued_fraction_trace_exists b",
                "cases continued_fraction_trace_exists",
                "cases continued_fraction_trace_exists_witness",
                "cases continued_fraction_trace_exists_witness_witness",
                "cases continued_fraction_trace_exists_witness_witness_witness",
                "exists x",
                "exists x4",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact continued_fraction_trace_exists_witness_witness_witness_witness",
                "exact gcd_exists_relational_witness",
            ),
            "All natural input pairs admit a fully expanded, beta-coded terminating Euclidean execution with a certified relational gcd output.",
        ),
        spec(
            EUCLIDEAN_NONZERO_EXECUTION_EXISTS,
            f"forall a b. ~(b = 0) -> exists g k. ({positive_execution})",
            (
                "continued_fraction_nonzero_divisor_exists",
                "gcd_exists_relational",
            ),
            (
                "intro a",
                "intro b",
                "intro hb",
                "specialize gcd_exists_relational a",
                "specialize gcd_exists_relational b",
                "cases gcd_exists_relational",
                "specialize continued_fraction_nonzero_divisor_exists a",
                "specialize continued_fraction_nonzero_divisor_exists b",
                "have htrace : exists s h e k. (~(s = 0) /\\ "
                f"({_trace_term('a','b','s','h','e','S k',tag='ec_nonzero_have',arguments=('a','b','s','h','e','k'))}))",
                "apply continued_fraction_nonzero_divisor_exists",
                "exact hb",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_witness",
                "cases htrace_witness_witness_witness",
                "cases htrace_witness_witness_witness_witness",
                "exists x",
                "exists x4",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact htrace_witness_witness_witness_witness_right",
                "exact gcd_exists_relational_witness",
            ),
            "For every nonzero initial divisor, an actual certified Euclidean execution exists and makes at least one division.",
        ),
        spec(
            EUCLIDEAN_GCD_EXECUTION_LINEAR_BOUND,
            "forall a b. exists g l. "
            f"(({linear_execution}) /\\ exists gap. gap + l = b)",
            (EUCLIDEAN_TRACE_EXISTS_LINEAR, "gcd_exists_relational"),
            (
                "intro a",
                "intro b",
                "specialize gcd_exists_relational a",
                "specialize gcd_exists_relational b",
                "cases gcd_exists_relational",
                "specialize euclidean_trace_exists_linear a",
                "specialize euclidean_trace_exists_linear b",
                "cases euclidean_trace_exists_linear",
                "cases euclidean_trace_exists_linear_witness",
                "cases euclidean_trace_exists_linear_witness_witness",
                "cases euclidean_trace_exists_linear_witness_witness_witness",
                "cases euclidean_trace_exists_linear_witness_witness_witness_witness",
                "exists x",
                "exists x4",
                "split",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact euclidean_trace_exists_linear_witness_witness_witness_witness_left",
                "exact gcd_exists_relational_witness",
                "exact euclidean_trace_exists_linear_witness_witness_witness_witness_right",
            ),
            "Every pair has a complete actual beta-coded Euclidean execution, a genuinely certified gcd output, and the exact constructive linear bound steps <= initial divisor; the stronger BitLen bound remains open.",
        ),
    )


@dataclass(frozen=True, slots=True)
class EuclideanDivisionStep:
    """One concrete, entirely untrusted Euclidean transition."""

    dividend: int
    divisor: int
    quotient: int
    remainder: int


@dataclass(frozen=True, slots=True)
class EuclideanExecutionCertificate:
    """Small beta-coded numerical witness; never a kernel proof authority."""

    dividend: int
    divisor: int
    result: int
    input_bit_length: int
    steps: tuple[EuclideanDivisionStep, ...]
    quotient_list: int
    history_values: tuple[int, ...]
    history_code: int
    history_scale: int

    @property
    def step_count(self) -> int:
        return len(self.steps)


def _natural(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    if value.bit_length() > MAX_EUCLIDEAN_INPUT_BITS:
        raise ValueError(f"{label} exceeds the Euclidean input bit cap")
    return value


def _pair(left: int, right: int) -> int:
    total = left + right
    if 2 * total.bit_length() + 2 > MAX_EUCLIDEAN_PACKED_STATE_BITS:
        raise ValueError("Euclidean packed state exceeds its bit cap")
    value = total * (total + 1) + right + right
    if value.bit_length() > MAX_EUCLIDEAN_PACKED_STATE_BITS:
        raise ValueError("Euclidean packed state exceeds its bit cap")
    return value


def _history(values: tuple[int, ...]) -> tuple[int, int]:
    if not values or len(values) > MAX_EUCLIDEAN_STEPS + 1:
        raise ValueError("Euclidean history exceeds its step cap")
    largest = max(values)
    scale = lcm(*range(1, len(values) + 1)) * (largest + 1)
    moduli = tuple(1 + (index + 1) * scale for index in range(len(values)))
    estimated = sum(modulus.bit_length() for modulus in moduli)
    if estimated > MAX_EUCLIDEAN_HISTORY_BITS:
        raise ValueError("Euclidean beta history exceeds its bit cap")
    code = 0
    product = 1
    for value, modulus in zip(values, moduli, strict=True):
        if value >= modulus or gcd(product, modulus) != 1:
            raise ValueError("Euclidean beta history has incompatible moduli")
        adjustment = ((value - code) * pow(product, -1, modulus)) % modulus
        code += product * adjustment
        product *= modulus
        if code.bit_length() > MAX_EUCLIDEAN_HISTORY_BITS:
            raise ValueError("Euclidean beta history exceeds its bit cap")
    return code, scale


def certify_euclidean_execution(
    dividend: int, divisor: int
) -> EuclideanExecutionCertificate:
    """Compute a tiny, capped beta history; this is not formal proof evidence."""

    first = _natural(dividend, "Euclidean dividend")
    second = _natural(divisor, "Euclidean divisor")
    steps: list[EuclideanDivisionStep] = []
    left, right = first, second
    while right:
        if len(steps) >= MAX_EUCLIDEAN_STEPS:
            raise ValueError("Euclidean execution exceeds its step cap")
        quotient, remainder = divmod(left, right)
        steps.append(EuclideanDivisionStep(left, right, quotient, remainder))
        left, right = right, remainder

    quotient_list = 0
    states: list[int] = [_pair(left, _pair(0, 0))]
    for step in reversed(steps):
        quotient_list = _pair(step.quotient, quotient_list) + 1
        if quotient_list.bit_length() > MAX_EUCLIDEAN_PACKED_STATE_BITS:
            raise ValueError("Euclidean quotient list exceeds its bit cap")
        states.append(
            _pair(step.dividend, _pair(step.divisor, quotient_list))
        )
    history_code, history_scale = _history(tuple(states))
    return EuclideanExecutionCertificate(
        dividend=first,
        divisor=second,
        result=left,
        input_bit_length=second.bit_length(),
        steps=tuple(steps),
        quotient_list=quotient_list,
        history_values=tuple(states),
        history_code=history_code,
        history_scale=history_scale,
    )


def verify_euclidean_execution(certificate: EuclideanExecutionCertificate) -> bool:
    """Reject tampered numerical witnesses; failure never establishes a theorem."""

    if not isinstance(certificate, EuclideanExecutionCertificate):
        return False
    try:
        expected = certify_euclidean_execution(
            certificate.dividend, certificate.divisor
        )
    except (ArithmeticError, TypeError, ValueError):
        return False
    if certificate != expected:
        return False
    if certificate.step_count > certificate.divisor:
        return False
    if certificate.divisor and (
        certificate.step_count > 2 * certificate.input_bit_length + 1
    ):
        return False
    return all(
        certificate.history_code
        % (1 + (index + 1) * certificate.history_scale)
        == value
        for index, value in enumerate(certificate.history_values)
    )


__all__ = [
    "EuclideanDivisionStep",
    "EuclideanExecutionCertificate",
    "MAX_EUCLIDEAN_HISTORY_BITS",
    "MAX_EUCLIDEAN_INPUT_BITS",
    "MAX_EUCLIDEAN_PACKED_STATE_BITS",
    "MAX_EUCLIDEAN_STEPS",
    "certify_euclidean_execution",
    "euclidean_division",
    "euclidean_execution",
    "euclidean_halving",
    "make_euclidean_complexity_candidate_theorems",
    "verify_euclidean_execution",
]
