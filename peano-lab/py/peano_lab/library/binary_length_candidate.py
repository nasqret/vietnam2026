"""Constructive, conservative binary digits, powers of two, and bit length.

``BitLen(0, 1)`` deliberately follows the grand-campaign blueprint: zero has
one displayed binary digit.  Every relation expands entirely into the old
first-order Heyting-arithmetic language; powers use the existing beta-coded
``Pow`` graph and no exponentiation term, axiom, or kernel rule is added.

Concrete certificates below are bounded executable examples only.  Admission
and proof authority belong solely to the original proof checker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .binary_modular_exponentiation_candidate import binary_exponent_split
from .finite_fold_surface import _binders, _identifier, _variables
from .power_algebra_theorems import _power_terms


BINARY_LENGTH_DIGIT_BOUNDED = "binary_length_digit_bounded"
BINARY_LENGTH_DIGIT_SPLIT_EXISTS = "binary_length_digit_split_exists"
BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL = "binary_length_digit_split_functional"
BINARY_LENGTH_DIGIT_SPLIT_EXISTS_UNIQUE = "binary_length_digit_split_exists_unique"
BINARY_POWER_TWO_EXISTS = "binary_power_two_exists"
BINARY_POWER_TWO_FUNCTIONAL = "binary_power_two_functional"
BINARY_POWER_TWO_ZERO_VALUE = "binary_power_two_zero_value"
BINARY_POWER_TWO_NONZERO = "binary_power_two_nonzero"
BINARY_POWER_TWO_SUCCESSOR_DOUBLE = "binary_power_two_successor_double"
BINARY_POWER_TWO_STRICT_GROWTH = "binary_power_two_strict_growth"
BINARY_POWER_TWO_EXPONENT_MONOTONE = "binary_power_two_exponent_monotone"
BINARY_POWER_TWO_EXPONENT_STRICT = "binary_power_two_exponent_strict"
BINARY_LENGTH_ZERO = "binary_length_zero"
BINARY_LENGTH_ONE = "binary_length_one"
BINARY_LENGTH_ZERO_INPUT_VALUE = "binary_length_zero_input_value"
BINARY_LENGTH_ZERO_INPUT_GENERAL = "binary_length_zero_input_general"
BINARY_LENGTH_SUCCESSOR_STEP = "binary_length_successor_step"
BINARY_LENGTH_EXISTS = "binary_length_exists"
BINARY_LENGTH_FUNCTIONAL = "binary_length_functional"
BINARY_LENGTH_EXISTS_UNIQUE = "binary_length_exists_unique"
BINARY_LENGTH_POWER_EXACT = "binary_length_power_exact"

MAX_BINARY_LENGTH_VALUE_BITS = 4096
MAX_BINARY_LENGTH_HISTORY_ENTRIES = 4096


class BinaryLengthError(ValueError):
    """A binary authoring surface or bounded concrete certificate is invalid."""


def _context(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        variables = tuple(dict.fromkeys(_variables(*labelled)))
    except ValueError as error:
        raise BinaryLengthError(str(error)) from error
    if any(variable.startswith("pa_") for variable in variables):
        raise BinaryLengthError("generated power binder captures an argument")
    return variables


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "binary-length binder tag")
    except ValueError as error:
        raise BinaryLengthError(str(error)) from error


def _power_two_terms(exponent: str, value: str, *, tag: str) -> str:
    """Expand ``Pow(2, exponent, value)`` for audited module-owned terms."""

    return _power_terms("2", exponent, value, tag=f"bl_{_safe_tag(tag)}")


def binary_power_relation(exponent: str, value: str, *, tag: str) -> str:
    """Expand the exact conservative two-ary ``PowTwo(exponent,value)``."""

    _context((exponent, "binary power exponent"), (value, "binary power value"))
    return _power_two_terms(exponent, value, tag=tag)


def binary_digit_relation(value: str, half: str, bit: str, *, tag: str) -> str:
    """Expand the existing exact decomposition ``value=2*half+bit``."""

    _context(
        (value, "binary digit value"),
        (half, "binary digit quotient"),
        (bit, "binary digit bit"),
    )
    try:
        return binary_exponent_split(value, half, bit, tag=f"bl_{_safe_tag(tag)}")
    except ValueError as error:
        raise BinaryLengthError(str(error)) from error


def _length_terms(
    value: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    safe_tag = _safe_tag(tag)
    try:
        exponent, lower, upper, positive, lower_gap, upper_gap = _binders(
            f"bl_{safe_tag}",
            variables,
            ("exponent", "lower", "upper", "positive", "lower_gap", "upper_gap"),
        )
    except ValueError as error:
        raise BinaryLengthError(str(error)) from error
    lower_power = _power_two_terms(exponent, lower, tag=f"{safe_tag}_lower")
    upper_power = _power_two_terms(length, upper, tag=f"{safe_tag}_upper")
    return (
        f"((({value}) = 0 /\\ ({length}) = 1) \\/ "
        f"exists {exponent} {lower} {upper}. "
        f"((({length}) = S {exponent}) /\\ "
        f"((exists {positive}. {positive} + 1 = ({value})) /\\ "
        f"(({lower_power}) /\\ (({upper_power}) /\\ "
        f"((exists {lower_gap}. {lower_gap} + ({lower}) = ({value})) /\\ "
        f"(exists {upper_gap}. {upper_gap} + S ({value}) = ({upper}))))))))"
    )


def binary_length_relation(value: str, length: str, *, tag: str) -> str:
    """Expand blueprint ``BitLen`` with its required ``BitLen(0,1)`` case."""

    variables = _context((value, "binary-length value"), (length, "binary length"))
    return _length_terms(value, length, tag=tag, variables=variables)


def make_binary_length_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return dependency-ordered original-kernel constructive candidates."""

    digit = binary_digit_relation("n", "h", "b", tag="digit")
    other_digit = binary_digit_relation("n", "k", "c", tag="other_digit")
    power = binary_power_relation("e", "p", tag="power")
    other_power = binary_power_relation("e", "q", tag="other_power")
    next_power = _power_two_terms("S e", "q", tag="next_power")
    later_power = binary_power_relation("f", "q", tag="later_power")
    length = binary_length_relation("n", "l", tag="length")
    other_length = binary_length_relation("n", "L", tag="other_length")
    zero_length = _length_terms("0", "1", tag="zero", variables=())
    one_length = _length_terms("1", "1", tag="one", variables=())
    successor_length = _length_terms("S n", "L", tag="successor", variables=("n", "L"))
    exact_length = _length_terms("p", "S e", tag="exact", variables=("e", "p"))
    return (
        spec(
            BINARY_LENGTH_DIGIT_BOUNDED,
            "forall b. (b = 0 \\/ b = 1) -> exists gap. gap + S b = 2",
            (),
            (
                "intro b", "intro hbit", "cases hbit",
                "exists 1", "rewrite hbit_left", "simp",
                "exists 0", "rewrite hbit_right", "simp",
            ),
            "Every witnessed binary digit is strictly below two.",
        ),
        spec(
            BINARY_LENGTH_DIGIT_SPLIT_EXISTS,
            f"forall n. exists h b. ({digit})",
            ("binary_exponent_split_exists",),
            (
                "intro n", "specialize binary_exponent_split_exists n",
                "exact binary_exponent_split_exists",
            ),
            "Every natural number has an exact binary quotient and zero-or-one digit.",
        ),
        spec(
            BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL,
            f"forall n h b k c. ({digit}) -> ({other_digit}) -> (h = k /\\ b = c)",
            (
                BINARY_LENGTH_DIGIT_BOUNDED,
                "two_mul_eq_add_self",
                "division_remainder_unique",
            ),
            (
                "intro n", "intro h", "intro b", "intro k", "intro c",
                "intro hfirst", "intro hsecond", "cases hfirst", "cases hsecond",
                "have hbound : exists gap. gap + S b = 2",
                f"specialize {BINARY_LENGTH_DIGIT_BOUNDED} b",
                f"apply {BINARY_LENGTH_DIGIT_BOUNDED}", "exact hfirst_left",
                "have kbound : exists gap. gap + S c = 2",
                f"specialize {BINARY_LENGTH_DIGIT_BOUNDED} c",
                f"apply {BINARY_LENGTH_DIGIT_BOUNDED}", "exact hsecond_left",
                "have hequation : n = 2 * h + b",
                "trans (h + h) + b", "exact hfirst_right", "congr",
                "symm", "apply two_mul_eq_add_self", "refl",
                "have kequation : n = 2 * k + c",
                "trans (k + k) + c", "exact hsecond_right", "congr",
                "symm", "apply two_mul_eq_add_self", "refl",
                "specialize division_remainder_unique 2",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique h",
                "specialize division_remainder_unique b",
                "specialize division_remainder_unique k",
                "specialize division_remainder_unique c",
                "apply division_remainder_unique", "exact hequation",
                "exact hbound", "exact kequation", "exact kbound",
            ),
            "Binary division by two has a unique quotient and unique digit.",
        ),
        spec(
            BINARY_LENGTH_DIGIT_SPLIT_EXISTS_UNIQUE,
            f"forall n. exists h b. (({digit}) /\\ "
            f"forall k c. ({other_digit}) -> (h = k /\\ b = c))",
            (BINARY_LENGTH_DIGIT_SPLIT_EXISTS, BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL),
            (
                "intro n", f"specialize {BINARY_LENGTH_DIGIT_SPLIT_EXISTS} n",
                f"cases {BINARY_LENGTH_DIGIT_SPLIT_EXISTS}",
                f"cases {BINARY_LENGTH_DIGIT_SPLIT_EXISTS}_witness",
                "exists x", "exists x1", "split",
                f"exact {BINARY_LENGTH_DIGIT_SPLIT_EXISTS}_witness_witness",
                "intro k", "intro c", "intro hother",
                f"specialize {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL} n",
                f"specialize {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL} x",
                f"specialize {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL} x1",
                f"specialize {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL} k",
                f"specialize {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL} c",
                f"apply {BINARY_LENGTH_DIGIT_SPLIT_FUNCTIONAL}",
                f"exact {BINARY_LENGTH_DIGIT_SPLIT_EXISTS}_witness_witness",
                "exact hother",
            ),
            "Every natural has exactly one fully witnessed binary quotient/digit pair.",
        ),
        spec(
            BINARY_POWER_TWO_EXISTS,
            f"forall e. exists p. ({power})",
            ("pow_exists",),
            (
                "intro e", "specialize pow_exists 2", "specialize pow_exists e",
                "exact pow_exists",
            ),
            "Every natural exponent has a witnessed beta-coded power of two.",
        ),
        spec(
            BINARY_POWER_TWO_FUNCTIONAL,
            f"forall e p q. ({power}) -> ({other_power}) -> p = q",
            ("pow_functional",),
            (
                "intro e", "intro p", "intro q", "intro hp", "intro hq",
                "specialize pow_functional 2", "specialize pow_functional e",
                "specialize pow_functional p", "specialize pow_functional q",
                "apply pow_functional", "exact hp", "exact hq",
            ),
            "The relational power of two is functional at every exponent.",
        ),
        spec(
            BINARY_POWER_TWO_ZERO_VALUE,
            f"forall p. ({_power_two_terms('0', 'p', tag='zero_power')}) -> p = 1",
            ("pow_zero",),
            (
                "intro p", "intro hp", "specialize pow_zero 2",
                "specialize pow_zero 0", "specialize pow_zero p",
                "apply pow_zero", "refl", "exact hp",
            ),
            "The beta-coded zeroth power of two is exactly one.",
        ),
        spec(
            BINARY_POWER_TWO_NONZERO,
            f"forall e p. ({power}) -> ~(p = 0)",
            ("pow_nonzero_of_one_le",),
            (
                "intro e", "intro p", "intro hp", "intro hzero",
                "specialize pow_nonzero_of_one_le 2",
                "specialize pow_nonzero_of_one_le e",
                "specialize pow_nonzero_of_one_le p",
                "apply pow_nonzero_of_one_le", "exists 1", "simp", "exact hp",
                "exact hzero",
            ),
            "Every beta-coded power of two is constructively nonzero.",
        ),
        spec(
            BINARY_POWER_TWO_SUCCESSOR_DOUBLE,
            f"forall e p q. ({power}) -> ({next_power}) -> q = p + p",
            ("pow_successor_pair_mul", "mul_comm", "two_mul_eq_add_self"),
            (
                "intro e", "intro p", "intro q", "intro hp", "intro hq",
                "have hproduct : q = p * 2",
                "specialize pow_successor_pair_mul 2",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul (S e)",
                "specialize pow_successor_pair_mul p",
                "specialize pow_successor_pair_mul q",
                "apply pow_successor_pair_mul", "refl", "exact hp", "exact hq",
                "trans p * 2", "exact hproduct",
                "trans 2 * p", "apply mul_comm", "apply two_mul_eq_add_self",
            ),
            "A successor power of two is exactly the sum of two predecessor powers.",
        ),
        spec(
            BINARY_POWER_TWO_STRICT_GROWTH,
            f"forall e p q. ({power}) -> ({next_power}) -> "
            "exists gap. gap + S p = q",
            (
                BINARY_POWER_TWO_NONZERO,
                BINARY_POWER_TWO_SUCCESSOR_DOUBLE,
                "four_square_branch_positive_half_strict",
                "two_mul_eq_add_self",
            ),
            (
                "intro e", "intro p", "intro q", "intro hp", "intro hq",
                "have hnonzero : ~(p = 0)",
                "intro hzero",
                f"specialize {BINARY_POWER_TWO_NONZERO} e",
                f"specialize {BINARY_POWER_TWO_NONZERO} p",
                f"apply {BINARY_POWER_TWO_NONZERO}", "exact hp", "exact hzero",
                "have hdouble : q = p + p",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} e",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} p",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} q",
                f"apply {BINARY_POWER_TWO_SUCCESSOR_DOUBLE}", "exact hp", "exact hq",
                "have hstrict : exists gap. gap + S p = 2 * p",
                "specialize four_square_branch_positive_half_strict p",
                "apply four_square_branch_positive_half_strict", "exact hnonzero",
                "cases hstrict", "exists x", "trans 2 * p", "exact hstrict_witness",
                "trans p + p", "apply two_mul_eq_add_self", "symm", "exact hdouble",
            ),
            "Successive beta-coded powers of two grow strictly.",
        ),
        spec(
            BINARY_POWER_TWO_EXPONENT_MONOTONE,
            f"forall e f p q. (exists gap. gap + e = f) -> "
            f"({power}) -> ({later_power}) -> exists gap. gap + p = q",
            ("pow_exponent_monotone",),
            (
                "intro e", "intro f", "intro p", "intro q", "intro horder",
                "intro hp", "intro hq", "specialize pow_exponent_monotone 2",
                "specialize pow_exponent_monotone e",
                "specialize pow_exponent_monotone f",
                "specialize pow_exponent_monotone p",
                "specialize pow_exponent_monotone q", "apply pow_exponent_monotone",
                "exists 1", "simp", "exact horder", "exact hp", "exact hq",
            ),
            "The relational powers of two preserve non-strict exponent ordering.",
        ),
        spec(
            BINARY_POWER_TWO_EXPONENT_STRICT,
            f"forall e f p q. (exists gap. gap + S e = f) -> "
            f"({power}) -> ({later_power}) -> exists gap. gap + S p = q",
            (
                BINARY_POWER_TWO_EXISTS,
                BINARY_POWER_TWO_STRICT_GROWTH,
                BINARY_POWER_TWO_EXPONENT_MONOTONE,
                "lt_of_lt_of_le",
            ),
            (
                "intro e", "intro f", "intro p", "intro q", "intro horder",
                "intro hp", "intro hq",
                f"have hnext : exists z. ({_power_two_terms('S e','z',tag='strict_next')})",
                f"specialize {BINARY_POWER_TWO_EXISTS} (S e)",
                f"exact {BINARY_POWER_TWO_EXISTS}", "cases hnext",
                "have hfirst : exists gap. gap + S p = x",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} e",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} p",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} x",
                f"apply {BINARY_POWER_TWO_STRICT_GROWTH}", "exact hp", "exact hnext_witness",
                "have hsecond : exists gap. gap + x = q",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} (S e)",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} f",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} q",
                f"apply {BINARY_POWER_TWO_EXPONENT_MONOTONE}", "exact horder",
                "exact hnext_witness", "exact hq",
                "specialize lt_of_lt_of_le p", "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le q", "apply lt_of_lt_of_le",
                "exact hfirst", "exact hsecond",
            ),
            "Strictly ordered exponents have strictly ordered powers of two.",
        ),
        spec(
            BINARY_LENGTH_ZERO,
            zero_length,
            (),
            ("left", "split", "refl", "refl"),
            "The blueprint convention gives zero exactly one displayed binary digit.",
        ),
        spec(
            BINARY_LENGTH_ONE,
            one_length,
            (
                BINARY_POWER_TWO_EXISTS,
                BINARY_POWER_TWO_ZERO_VALUE,
                BINARY_POWER_TWO_SUCCESSOR_DOUBLE,
            ),
            (
                f"have hzero : exists p. ({_power_two_terms('0','p',tag='one_lower')})",
                f"specialize {BINARY_POWER_TWO_EXISTS} 0",
                f"exact {BINARY_POWER_TWO_EXISTS}", "cases hzero",
                f"have hone : exists q. ({_power_two_terms('1','q',tag='one_upper')})",
                f"specialize {BINARY_POWER_TWO_EXISTS} 1",
                f"exact {BINARY_POWER_TWO_EXISTS}", "cases hone",
                "have hvalue : x = 1",
                f"specialize {BINARY_POWER_TWO_ZERO_VALUE} x",
                f"apply {BINARY_POWER_TWO_ZERO_VALUE}", "exact hzero_witness",
                "have hdouble : x1 = x + x",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} 0",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} x",
                f"specialize {BINARY_POWER_TWO_SUCCESSOR_DOUBLE} x1",
                f"apply {BINARY_POWER_TWO_SUCCESSOR_DOUBLE}",
                "exact hzero_witness", "exact hone_witness",
                "right", "exists 0", "exists x", "exists x1", "split", "refl",
                "split", "exists 0", "simp", "split", "exact hzero_witness",
                "split", "exact hone_witness", "split", "exists 0",
                "rewrite hvalue", "simp", "exists 0", "rewrite hdouble",
                "rewrite hvalue", "rewrite hvalue", "simp",
            ),
            "The positive integer one has exactly one binary digit.",
        ),
        spec(
            BINARY_LENGTH_ZERO_INPUT_VALUE,
            f"forall l. ({_length_terms('0','l',tag='zero_input',variables=('l',))}) -> l = 1",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro l", "intro hlength", "cases hlength",
                "cases hlength_left", "exact hlength_left_right",
                "cases hlength_right", "cases hlength_right_witness",
                "cases hlength_right_witness_witness",
                "cases hlength_right_witness_witness_witness",
                "cases hlength_right_witness_witness_witness_right",
                "cases hlength_right_witness_witness_witness_right_left",
                "exfalso", "specialize succ_ne_zero 0", "apply succ_ne_zero",
                "specialize add_eq_zero_right x3",
                "specialize add_eq_zero_right 1", "apply add_eq_zero_right",
                "exact hlength_right_witness_witness_witness_right_left_witness",
            ),
            "Any binary-length witness for zero is necessarily one.",
        ),
        spec(
            BINARY_LENGTH_SUCCESSOR_STEP,
            f"forall n l. ({length}) -> exists L. ({successor_length})",
            (
                BINARY_LENGTH_ONE,
                BINARY_POWER_TWO_EXISTS,
                BINARY_POWER_TWO_STRICT_GROWTH,
                "le_eq_or_lt",
                "le_succ",
                "le_refl",
            ),
            (
                "intro n", "intro l", "intro hlength", "cases hlength",
                "cases hlength_left", "exists 1",
                "rewrite hlength_left_left", "rewrite hlength_left_left",
                "rewrite hlength_left_left", "rewrite hlength_left_left",
                f"exact {BINARY_LENGTH_ONE}",
                "cases hlength_right", "cases hlength_right_witness",
                "cases hlength_right_witness_witness",
                "cases hlength_right_witness_witness_witness",
                "cases hlength_right_witness_witness_witness_right",
                "cases hlength_right_witness_witness_witness_right_right",
                "cases hlength_right_witness_witness_witness_right_right_right",
                "cases hlength_right_witness_witness_witness_right_right_right_right",
                "have hcases : S n = x2 \\/ exists gap. gap + S (S n) = x2",
                "specialize le_eq_or_lt (S n)", "specialize le_eq_or_lt x2",
                "apply le_eq_or_lt",
                "exact hlength_right_witness_witness_witness_right_right_right_right_right",
                "cases hcases",
                f"have hnext : exists q. ({_power_two_terms('S l','q',tag='successor_next')})",
                f"specialize {BINARY_POWER_TWO_EXISTS} (S l)",
                f"exact {BINARY_POWER_TWO_EXISTS}", "cases hnext",
                "have hstrict : exists gap. gap + S x2 = x3",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} l",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} x2",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} x3",
                f"apply {BINARY_POWER_TWO_STRICT_GROWTH}",
                "exact hlength_right_witness_witness_witness_right_right_right_left",
                "exact hnext_witness",
                "exists S l", "right", "exists l", "exists x2", "exists x3",
                "split", "refl", "split", "exists n", "simp", "split",
                "exact hlength_right_witness_witness_witness_right_right_right_left",
                "split", "exact hnext_witness", "split", "rewrite hcases_left",
                "apply le_refl", "rewrite hcases_left", "exact hstrict",
                "exists l", "right", "exists x", "exists x1", "exists x2",
                "split", "exact hlength_right_witness_witness_witness_left",
                "split", "exists n", "simp", "split",
                "exact hlength_right_witness_witness_witness_right_right_left",
                "split",
                "exact hlength_right_witness_witness_witness_right_right_right_left",
                "split", "specialize le_succ x1", "specialize le_succ n",
                "apply le_succ",
                "exact hlength_right_witness_witness_witness_right_right_right_right_left",
                "exact hcases_right",
            ),
            "A binary-length witness for n constructively produces one for S n.",
        ),
        spec(
            BINARY_LENGTH_EXISTS,
            f"forall n. exists l. ({length})",
            (BINARY_LENGTH_ZERO, BINARY_LENGTH_SUCCESSOR_STEP),
            (
                "induction n", "exists 1", f"exact {BINARY_LENGTH_ZERO}",
                "cases IH", f"specialize {BINARY_LENGTH_SUCCESSOR_STEP} n",
                f"specialize {BINARY_LENGTH_SUCCESSOR_STEP} x",
                f"apply {BINARY_LENGTH_SUCCESSOR_STEP}", "exact IH_witness",
            ),
            "Every natural number has a constructively witnessed canonical bit length.",
        ),
        spec(
            BINARY_LENGTH_ZERO_INPUT_GENERAL,
            f"forall n l. n = 0 -> ({length}) -> l = 1",
            (BINARY_LENGTH_ZERO_INPUT_VALUE,),
            (
                "intro n", "intro l", "intro hzero", "intro hlength",
                "rewrite hzero at hlength", "rewrite hzero at hlength",
                "rewrite hzero at hlength", "rewrite hzero at hlength",
                f"specialize {BINARY_LENGTH_ZERO_INPUT_VALUE} l",
                f"apply {BINARY_LENGTH_ZERO_INPUT_VALUE}", "exact hlength",
            ),
            "Any canonical bit-length witness at an input equal to zero is one.",
        ),
        spec(
            BINARY_LENGTH_FUNCTIONAL,
            f"forall n l L. ({length}) -> ({other_length}) -> l = L",
            (
                BINARY_LENGTH_ZERO_INPUT_GENERAL,
                "le_total",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                BINARY_POWER_TWO_EXPONENT_MONOTONE,
                "le_trans",
                "lt_not_le",
            ),
            (
                "intro n", "intro l", "intro L", "intro hfirst", "intro hsecond",
                "cases hfirst", "cases hfirst_left",
                "have hother : L = 1",
                f"specialize {BINARY_LENGTH_ZERO_INPUT_GENERAL} n",
                f"specialize {BINARY_LENGTH_ZERO_INPUT_GENERAL} L",
                f"apply {BINARY_LENGTH_ZERO_INPUT_GENERAL}",
                "exact hfirst_left_left", "exact hsecond",
                "trans 1", "exact hfirst_left_right", "symm", "exact hother",
                "cases hsecond", "cases hsecond_left",
                "have hself : l = 1",
                f"specialize {BINARY_LENGTH_ZERO_INPUT_GENERAL} n",
                f"specialize {BINARY_LENGTH_ZERO_INPUT_GENERAL} l",
                f"apply {BINARY_LENGTH_ZERO_INPUT_GENERAL}",
                "exact hsecond_left_left", "right", "exact hfirst_right",
                "trans 1", "exact hself", "symm", "exact hsecond_left_right",
                "cases hfirst_right", "cases hfirst_right_witness",
                "cases hfirst_right_witness_witness",
                "cases hfirst_right_witness_witness_witness",
                "cases hfirst_right_witness_witness_witness_right",
                "cases hfirst_right_witness_witness_witness_right_right",
                "cases hfirst_right_witness_witness_witness_right_right_right",
                "cases hfirst_right_witness_witness_witness_right_right_right_right",
                "cases hsecond_right", "cases hsecond_right_witness",
                "cases hsecond_right_witness_witness",
                "cases hsecond_right_witness_witness_witness",
                "cases hsecond_right_witness_witness_witness_right",
                "cases hsecond_right_witness_witness_witness_right_right",
                "cases hsecond_right_witness_witness_witness_right_right_right",
                "cases hsecond_right_witness_witness_witness_right_right_right_right",
                "specialize le_total l", "specialize le_total L", "cases le_total",
                "have hcases : l = L \\/ exists gap. gap + S l = L",
                "specialize le_eq_or_lt l", "specialize le_eq_or_lt L",
                "apply le_eq_or_lt", "exact le_total_left", "cases hcases",
                "exact hcases_left",
                "have hexponent : exists gap. gap + l = x3",
                "specialize le_of_succ_le_succ l",
                "specialize le_of_succ_le_succ x3",
                "apply le_of_succ_le_succ",
                "rewrite hsecond_right_witness_witness_witness_left at hcases_right",
                "exact hcases_right",
                "have hpowers : exists gap. gap + x2 = x4",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} l",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x3",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x2",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x4",
                f"apply {BINARY_POWER_TWO_EXPONENT_MONOTONE}", "exact hexponent",
                "exact hfirst_right_witness_witness_witness_right_right_right_left",
                "exact hsecond_right_witness_witness_witness_right_right_left",
                "have hreverse : exists gap. gap + x2 = n",
                "specialize le_trans x2", "specialize le_trans x4",
                "specialize le_trans n", "apply le_trans", "exact hpowers",
                "exact hsecond_right_witness_witness_witness_right_right_right_right_left",
                "exfalso", "specialize lt_not_le n", "specialize lt_not_le x2",
                "apply lt_not_le",
                "exact hfirst_right_witness_witness_witness_right_right_right_right_right",
                "exact hreverse",
                "have hcases : L = l \\/ exists gap. gap + S L = l",
                "specialize le_eq_or_lt L", "specialize le_eq_or_lt l",
                "apply le_eq_or_lt", "exact le_total_right", "cases hcases",
                "symm", "exact hcases_left",
                "have hexponent : exists gap. gap + L = x",
                "specialize le_of_succ_le_succ L",
                "specialize le_of_succ_le_succ x",
                "apply le_of_succ_le_succ",
                "rewrite hfirst_right_witness_witness_witness_left at hcases_right",
                "exact hcases_right",
                "have hpowers : exists gap. gap + x5 = x1",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} L",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x5",
                f"specialize {BINARY_POWER_TWO_EXPONENT_MONOTONE} x1",
                f"apply {BINARY_POWER_TWO_EXPONENT_MONOTONE}", "exact hexponent",
                "exact hsecond_right_witness_witness_witness_right_right_right_left",
                "exact hfirst_right_witness_witness_witness_right_right_left",
                "have hreverse : exists gap. gap + x5 = n",
                "specialize le_trans x5", "specialize le_trans x1",
                "specialize le_trans n", "apply le_trans", "exact hpowers",
                "exact hfirst_right_witness_witness_witness_right_right_right_right_left",
                "exfalso", "specialize lt_not_le n", "specialize lt_not_le x5",
                "apply lt_not_le",
                "exact hsecond_right_witness_witness_witness_right_right_right_right_right",
                "exact hreverse",
            ),
            "Two complete constructive binary-length witnesses for one input agree.",
        ),
        spec(
            BINARY_LENGTH_EXISTS_UNIQUE,
            f"forall n. exists l. (({length}) /\\ forall L. ({other_length}) -> l = L)",
            (BINARY_LENGTH_EXISTS, BINARY_LENGTH_FUNCTIONAL),
            (
                "intro n", f"specialize {BINARY_LENGTH_EXISTS} n",
                f"cases {BINARY_LENGTH_EXISTS}", "exists x", "split",
                f"exact {BINARY_LENGTH_EXISTS}_witness",
                "intro L", "intro hother",
                f"specialize {BINARY_LENGTH_FUNCTIONAL} n",
                f"specialize {BINARY_LENGTH_FUNCTIONAL} x",
                f"specialize {BINARY_LENGTH_FUNCTIONAL} L",
                f"apply {BINARY_LENGTH_FUNCTIONAL}",
                f"exact {BINARY_LENGTH_EXISTS}_witness", "exact hother",
            ),
            "Every natural has exactly one canonical blueprint-compatible bit length.",
        ),
        spec(
            BINARY_LENGTH_POWER_EXACT,
            f"forall e p. ({power}) -> ({exact_length})",
            (
                BINARY_POWER_TWO_NONZERO,
                BINARY_POWER_TWO_EXISTS,
                BINARY_POWER_TWO_STRICT_GROWTH,
                "one_le_of_ne_zero",
                "le_refl",
            ),
            (
                "intro e", "intro p", "intro hp",
                "have hnonzero : ~(p = 0)", "intro hzero",
                f"specialize {BINARY_POWER_TWO_NONZERO} e",
                f"specialize {BINARY_POWER_TWO_NONZERO} p",
                f"apply {BINARY_POWER_TWO_NONZERO}", "exact hp", "exact hzero",
                "have hpositive : exists gap. gap + 1 = p",
                "specialize one_le_of_ne_zero p", "apply one_le_of_ne_zero",
                "exact hnonzero",
                f"have hnext : exists q. ({_power_two_terms('S e','q',tag='exact_next')})",
                f"specialize {BINARY_POWER_TWO_EXISTS} (S e)",
                f"exact {BINARY_POWER_TWO_EXISTS}", "cases hnext",
                "have hstrict : exists gap. gap + S p = x",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} e",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} p",
                f"specialize {BINARY_POWER_TWO_STRICT_GROWTH} x",
                f"apply {BINARY_POWER_TWO_STRICT_GROWTH}", "exact hp",
                "exact hnext_witness",
                "right", "exists e", "exists p", "exists x", "split", "refl",
                "split", "exact hpositive", "split", "exact hp", "split",
                "exact hnext_witness", "split", "apply le_refl", "exact hstrict",
            ),
            "The exact beta-coded power 2^e has canonical binary length e+1.",
        ),
    )


@dataclass(frozen=True, slots=True)
class BinaryLengthCertificate:
    """A small executable certificate; never proof or admission authority."""

    value: int
    length: int
    lower_power: int
    upper_power: int
    digits_least_significant_first: tuple[int, ...]
    quotient_history: tuple[int, ...]


def binary_length_certificate(value: int) -> BinaryLengthCertificate:
    """Compute and audit a bounded concrete binary length and complete digits."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BinaryLengthError("binary-length input must be a non-negative integer")
    length = max(1, value.bit_length())
    if length > MAX_BINARY_LENGTH_VALUE_BITS:
        raise BinaryLengthError("binary-length input exceeds the bounded bit cap")
    if length > MAX_BINARY_LENGTH_HISTORY_ENTRIES:
        raise BinaryLengthError("binary-length history exceeds the bounded entry cap")

    current = value
    digits: list[int] = []
    history = [current]
    for _ in range(length):
        quotient, bit = divmod(current, 2)
        if current != quotient + quotient + bit or bit not in (0, 1):
            raise BinaryLengthError("binary quotient/digit decomposition failed")
        digits.append(bit)
        current = quotient
        history.append(current)
    if current != 0:
        raise BinaryLengthError("binary history did not terminate after its bit length")

    lower = 1 << (length - 1)
    upper = 1 << length
    if value == 0:
        if length != 1 or tuple(digits) != (0,):
            raise BinaryLengthError("zero does not satisfy the blueprint convention")
    elif not lower <= value < upper:
        raise BinaryLengthError("positive binary value is outside its power bracket")

    return BinaryLengthCertificate(
        value=value,
        length=length,
        lower_power=lower,
        upper_power=upper,
        digits_least_significant_first=tuple(digits),
        quotient_history=tuple(history),
    )


__all__ = [
    "BinaryLengthCertificate",
    "BinaryLengthError",
    "MAX_BINARY_LENGTH_HISTORY_ENTRIES",
    "MAX_BINARY_LENGTH_VALUE_BITS",
    "binary_digit_relation",
    "binary_length_certificate",
    "binary_length_relation",
    "binary_power_relation",
    "make_binary_length_candidate_theorems",
]
