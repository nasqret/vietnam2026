"""Constructive one-digit carry and prime-row foundations for Lucas.

These isolated candidates characterize exactly when a prime divides the
binomial coefficient of two individual base-p digits and construct actual
first-order quotient/digit witnesses, including beta-coded finite digit
prefixes. They reuse existing factorial, division, and beta-coding machinery
without adding primitive digits, polynomials, finite sequences, classical
logic, or theorem authority to the unchanged first-order kernel. The full
multi-digit Lucas congruence is deliberately not claimed.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_choose_foundation_candidate import _choose_relation_term
from .fermat_residue_map_candidate import prime
from .finite_division_prefix_candidate import division_prefix
from .finite_factorial_theorems import factorial_relation
from .finite_fold_surface import beta_at


LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES = (
    "lucas_digit_carry_implies_prime_divides"
)
LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE = "lucas_prime_row_interior_divisible"
LUCAS_CHOOSE_PRIME_DIVISOR_BOUND = "lucas_choose_prime_divisor_bound"
LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES = (
    "lucas_digit_carry_iff_prime_divides"
)
LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES = (
    "lucas_digit_no_carry_iff_not_divides"
)
LUCAS_BASE_P_DIGIT_TOTAL = "lucas_base_p_digit_total"
LUCAS_PRIME_BASE_DIGIT_TOTAL = "lucas_prime_base_digit_total"
LUCAS_BASE_P_DIGIT_FUNCTIONAL = "lucas_base_p_digit_functional"
LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE = "lucas_base_p_digit_of_small_value"
LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES = "lucas_base_p_zero_digit_iff_divides"
LUCAS_BASE_P_DIGIT_PREFIX_EXISTS = "lucas_base_p_digit_prefix_exists"
LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS = "lucas_prime_base_digit_prefix_exists"
LUCAS_BASE_P_DIGIT_PREFIX_POINT = "lucas_base_p_digit_prefix_point"
LUCAS_BASE_P_TWO_DIGIT_TOTAL = "lucas_base_p_two_digit_total"
LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL = "lucas_prime_base_two_digit_total"
LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION = "lucas_base_p_two_digit_reconstruction"
LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE = (
    "lucas_prime_row_initial_coefficient_one"
)
LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE = (
    "lucas_prime_row_terminal_coefficient_one"
)
LUCAS_PRIME_ROW_SPARSE_COMPLETE = "lucas_prime_row_sparse_complete"


def _lt(left: str, right: str, *, tag: str) -> str:
    gap = f"ldc_lt_{tag}"
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _le(left: str, right: str, *, tag: str) -> str:
    gap = f"ldc_le_{tag}"
    return f"exists {gap}. {gap} + ({left}) = {right}"


def _divides(divisor: str, value: str, *, tag: str) -> str:
    quotient = f"ldc_quotient_{tag}"
    return f"exists {quotient}. {value} = {divisor} * {quotient}"


def _base_p_digit(
    base: str,
    value: str,
    quotient: str,
    digit: str,
    *,
    tag: str,
) -> str:
    """Expand the exact native first-order base-p quotient/digit relation."""

    return (
        f"(({value}) = ({base}) * ({quotient}) + ({digit})) /\\ "
        f"({_lt(digit, base, tag=f'{tag}_bound')})"
    )


def _iff(left: str, right: str) -> str:
    return f"((({left}) -> ({right})) /\\ (({right}) -> ({left})))"


def make_lucas_digit_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build checked digit extraction and one-digit boundaries, not full Lucas."""

    digit_variables = ("p", "a", "b", "C")
    digit_prime = prime("p", tag="lucas_digit_prime")
    digit_left = _lt("a", "p", tag="left")
    digit_right = _lt("b", "p", tag="right")
    digit_carry = _le("p", "a + b", tag="carry")
    digit_no_carry = _lt("a + b", "p", tag="no_carry")
    digit_choose = _choose_relation_term(
        "a + b", "a", "C", tag="lucas_digit_choose", variables=digit_variables
    )
    digit_divides = _divides("p", "C", tag="digit")

    row_variables = ("p", "k", "j", "C")
    row_prime = prime("p", tag="lucas_row_prime")
    row_left = _lt("k", "p", tag="row_left")
    row_right = _lt("j", "p", tag="row_right")
    row_choose = _choose_relation_term(
        "p", "k", "C", tag="lucas_row_choose", variables=row_variables
    )
    row_initial = _choose_relation_term(
        "p", "0", "C0", tag="lucas_row_initial", variables=("p", "C0")
    )
    row_terminal = _choose_relation_term(
        "p", "p", "Cp", tag="lucas_row_terminal", variables=("p", "Cp")
    )
    row_divides = _divides("p", "C", tag="row")

    bound_variables = ("n", "k", "j", "p", "C")
    bound_prime = prime("p", tag="lucas_bound_prime")
    bound_choose = _choose_relation_term(
        "n", "k", "C", tag="lucas_bound_choose", variables=bound_variables
    )
    bound_divides = _divides("p", "C", tag="bound")
    prime_bound = _le("p", "n", tag="prime_bound")
    total_factorial = factorial_relation("n", "F", tag="lucas_bound_total")
    left_factorial = factorial_relation("k", "K", tag="lucas_bound_left")
    right_factorial = factorial_relation("j", "J", tag="lucas_bound_right")

    native_digit = _base_p_digit("p", "n", "q", "d", tag="native")
    alternate_digit = _base_p_digit("p", "n", "Q", "D", tag="alternate")
    small_value = _lt("n", "p", tag="small_value")
    value_divides = _divides("p", "n", tag="native_zero")
    prefix = division_prefix(
        "p", "b", "c", "qb", "qc", "db", "dc", "l", tag="lucas_digits"
    )
    prefix_bound = _lt("i", "l", tag="prefix_index")
    source_entry = beta_at("b", "c", "i", "n", tag="lucas_source")
    quotient_entry = beta_at("qb", "qc", "i", "q", tag="lucas_quotient")
    digit_entry = beta_at("db", "dc", "i", "d", tag="lucas_digit")
    point_result = (
        f"exists q d. (({quotient_entry}) /\\ "
        f"(({digit_entry}) /\\ ({native_digit})))"
    )
    first_extracted = _base_p_digit("p", "n", "q0", "d0", tag="first")
    second_extracted = _base_p_digit("p", "q0", "q1", "d1", tag="second")
    two_extracted = f"(({first_extracted}) /\\ ({second_extracted}))"

    return (
        spec(
            LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES,
            f"forall p a b C. ({digit_prime}) -> ({digit_left}) -> "
            f"({digit_right}) -> ({digit_carry}) -> ({digit_choose}) -> "
            f"({digit_divides})",
            ("choose_prime_divides_between",),
            (
                "intro p", "intro a", "intro b", "intro C", "intro hp",
                "intro ha", "intro hb", "intro hcarry", "intro hchoose",
                "specialize choose_prime_divides_between (a + b)",
                "specialize choose_prime_divides_between a",
                "specialize choose_prime_divides_between b",
                "specialize choose_prime_divides_between p",
                "specialize choose_prime_divides_between C",
                "apply choose_prime_divides_between", "refl", "exact hp",
                "exact ha", "exact hb", "exact hcarry", "exact hchoose",
            ),
            "For two genuine base-p digits, an addition carry forces p to "
            "divide their relational binomial coefficient.",
        ),
        spec(
            LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE,
            f"forall p k j C. ({row_prime}) -> k + j = p -> "
            f"({row_left}) -> ({row_right}) -> ({row_choose}) -> ({row_divides})",
            ("choose_prime_divides_between", "le_refl"),
            (
                "intro p", "intro k", "intro j", "intro C", "intro hp",
                "intro hsum", "intro hk", "intro hj", "intro hchoose",
                "specialize choose_prime_divides_between p",
                "specialize choose_prime_divides_between k",
                "specialize choose_prime_divides_between j",
                "specialize choose_prime_divides_between p",
                "specialize choose_prime_divides_between C",
                "apply choose_prime_divides_between", "exact hsum", "exact hp",
                "exact hk", "exact hj", "specialize le_refl p", "exact le_refl",
                "exact hchoose",
            ),
            "Every interior coefficient in prime Pascal row p is divisible by p.",
        ),
        spec(
            LUCAS_CHOOSE_PRIME_DIVISOR_BOUND,
            f"forall n k j p C. k + j = n -> ({bound_prime}) -> "
            f"({bound_choose}) -> ({bound_divides}) -> ({prime_bound})",
            (
                "factorial_exists", "choose_factorial_bridge",
                "multiple_mul_left", "factorial_prime_le_of_divides",
            ),
            (
                "intro n", "intro k", "intro j", "intro p", "intro C",
                "intro hsum", "intro hp", "intro hchoose", "intro hdivides",
                f"have htotal : exists F. ({total_factorial})",
                "specialize factorial_exists n", "exact factorial_exists",
                "cases htotal",
                f"have hleft : exists K. ({left_factorial})",
                "specialize factorial_exists k", "exact factorial_exists",
                "cases hleft",
                f"have hright : exists J. ({right_factorial})",
                "specialize factorial_exists j", "exact factorial_exists",
                "cases hright",
                "have hbridge : x = (x1 * x2) * C",
                "specialize choose_factorial_bridge n",
                "specialize choose_factorial_bridge k",
                "specialize choose_factorial_bridge j",
                "specialize choose_factorial_bridge C",
                "specialize choose_factorial_bridge x",
                "specialize choose_factorial_bridge x1",
                "specialize choose_factorial_bridge x2",
                "apply choose_factorial_bridge", "exact hsum", "exact hchoose",
                "exact htotal_witness", "exact hleft_witness", "exact hright_witness",
                "have hfactorial_divides : exists z. x = p * z",
                "rewrite hbridge", "specialize multiple_mul_left p",
                "specialize multiple_mul_left C",
                "specialize multiple_mul_left (x1 * x2)",
                "apply multiple_mul_left", "exact hdivides",
                "specialize factorial_prime_le_of_divides p",
                "specialize factorial_prime_le_of_divides n",
                "specialize factorial_prime_le_of_divides x",
                "apply factorial_prime_le_of_divides", "exact hp",
                "exact htotal_witness", "exact hfactorial_divides",
            ),
            "Every prime divisor of a relational binomial coefficient is "
            "at most its Pascal-row index.",
        ),
        spec(
            LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES,
            f"forall p a b C. ({digit_prime}) -> ({digit_left}) -> "
            f"({digit_right}) -> ({digit_choose}) -> "
            f"({_iff(digit_carry, digit_divides)})",
            (
                LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES,
                LUCAS_CHOOSE_PRIME_DIVISOR_BOUND,
            ),
            (
                "intro p", "intro a", "intro b", "intro C", "intro hp",
                "intro ha", "intro hb", "intro hchoose", "split",
                "intro hcarry",
                "specialize lucas_digit_carry_implies_prime_divides p",
                "specialize lucas_digit_carry_implies_prime_divides a",
                "specialize lucas_digit_carry_implies_prime_divides b",
                "specialize lucas_digit_carry_implies_prime_divides C",
                "apply lucas_digit_carry_implies_prime_divides", "exact hp",
                "exact ha", "exact hb", "exact hcarry", "exact hchoose",
                "intro hdivides",
                "specialize lucas_choose_prime_divisor_bound (a + b)",
                "specialize lucas_choose_prime_divisor_bound a",
                "specialize lucas_choose_prime_divisor_bound b",
                "specialize lucas_choose_prime_divisor_bound p",
                "specialize lucas_choose_prime_divisor_bound C",
                "apply lucas_choose_prime_divisor_bound", "refl", "exact hp",
                "exact hchoose", "exact hdivides",
            ),
            "For two base-p digits, carrying is equivalent to prime "
            "divisibility of their binomial coefficient.",
        ),
        spec(
            LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES,
            f"forall p a b C. ({digit_prime}) -> ({digit_left}) -> "
            f"({digit_right}) -> ({digit_choose}) -> "
            f"({_iff(digit_no_carry, f'~({digit_divides})')})",
            (
                LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES,
                "lt_not_le", "le_or_lt",
            ),
            (
                "intro p", "intro a", "intro b", "intro C", "intro hp",
                "intro ha", "intro hb", "intro hchoose",
                f"have hclassification : {_iff(digit_carry, digit_divides)}",
                "specialize lucas_digit_carry_iff_prime_divides p",
                "specialize lucas_digit_carry_iff_prime_divides a",
                "specialize lucas_digit_carry_iff_prime_divides b",
                "specialize lucas_digit_carry_iff_prime_divides C",
                "apply lucas_digit_carry_iff_prime_divides", "exact hp",
                "exact ha", "exact hb", "exact hchoose",
                "cases hclassification", "split", "intro hnocarrry",
                "intro hdivides", "specialize lt_not_le (a + b)",
                "specialize lt_not_le p", "apply lt_not_le", "exact hnocarrry",
                "apply hclassification_right", "exact hdivides",
                "intro hnotdivides", "specialize le_or_lt p",
                "specialize le_or_lt (a + b)", "cases le_or_lt", "exfalso",
                "apply hnotdivides", "apply hclassification_left",
                "exact le_or_lt_left", "exact le_or_lt_right",
            ),
            "For two base-p digits, a carry-free sum is equivalent to "
            "constructive nondivisibility of their binomial coefficient.",
        ),
        spec(
            LUCAS_BASE_P_DIGIT_TOTAL,
            f"forall p n. ~(p = 0) -> exists q d. ({native_digit})",
            ("division_remainder_exists",),
            (
                "intro p",
                "intro n",
                "intro hnonzero",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists n",
                "apply division_remainder_exists",
                "exact hnonzero",
            ),
            "Every natural value has an actual quotient and strictly bounded base-p digit for every nonzero base.",
        ),
        spec(
            LUCAS_PRIME_BASE_DIGIT_TOTAL,
            f"forall p n. ({prime('p', tag='lucas_digit_total_prime')}) -> "
            f"exists q d. ({native_digit})",
            ("prime_nonzero", LUCAS_BASE_P_DIGIT_TOTAL),
            (
                "intro p",
                "intro n",
                "intro hprime",
                "specialize lucas_base_p_digit_total p",
                "specialize lucas_base_p_digit_total n",
                "apply lucas_base_p_digit_total",
                "intro hzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hzero",
            ),
            "Every prime base constructively provides a quotient and canonical least-significant digit for every natural.",
        ),
        spec(
            LUCAS_BASE_P_DIGIT_FUNCTIONAL,
            f"forall p n q d Q D. ({native_digit}) -> ({alternate_digit}) -> "
            "((q = Q) /\\ (d = D))",
            ("division_remainder_unique",),
            (
                "intro p",
                "intro n",
                "intro q",
                "intro d",
                "intro Q",
                "intro D",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "specialize division_remainder_unique p",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique Q",
                "specialize division_remainder_unique D",
                "apply division_remainder_unique",
                "exact hfirst_left",
                "exact hfirst_right",
                "exact hsecond_left",
                "exact hsecond_right",
            ),
            "Both the quotient and the bounded base-p digit are constructively functional.",
        ),
        spec(
            LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE,
            f"forall p n q d. ({small_value}) -> ({native_digit}) -> "
            "((q = 0) /\\ (d = n))",
            ("division_remainder_unique", "zero_add"),
            (
                "intro p",
                "intro n",
                "intro q",
                "intro d",
                "intro hsmall",
                "intro hdigit",
                "cases hdigit",
                "specialize division_remainder_unique p",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique 0",
                "specialize division_remainder_unique n",
                "apply division_remainder_unique",
                "exact hdigit_left",
                "exact hdigit_right",
                "simp [zero_add]",
                "exact hsmall",
            ),
            "A value strictly below its base has quotient zero and itself as its unique canonical digit.",
        ),
        spec(
            LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES,
            f"forall p n q d. ({native_digit}) -> "
            f"({_iff('d = 0', value_divides)})",
            (
                "zero_remainder_implies_multiple",
                "eq_decidable",
                "nonzero_remainder_not_multiple",
            ),
            (
                "intro p",
                "intro n",
                "intro q",
                "intro d",
                "intro hdigit",
                "cases hdigit",
                "split",
                "intro hzero",
                "rewrite hzero at hdigit_left",
                "specialize zero_remainder_implies_multiple p",
                "specialize zero_remainder_implies_multiple n",
                "specialize zero_remainder_implies_multiple q",
                "apply zero_remainder_implies_multiple",
                "exact hdigit_left",
                "intro hdivides",
                "specialize eq_decidable d",
                "specialize eq_decidable 0",
                "cases eq_decidable",
                "exact eq_decidable_left",
                "exfalso",
                "specialize nonzero_remainder_not_multiple p",
                "specialize nonzero_remainder_not_multiple n",
                "specialize nonzero_remainder_not_multiple q",
                "specialize nonzero_remainder_not_multiple d",
                "apply nonzero_remainder_not_multiple",
                "exact hdigit_left",
                "exact eq_decidable_right",
                "exact hdigit_right",
                "exact hdivides",
            ),
            "The canonical least-significant base-p digit is zero exactly when its value is divisible by p.",
        ),
        spec(
            LUCAS_BASE_P_DIGIT_PREFIX_EXISTS,
            f"forall p b c l. ~(p = 0) -> exists qb qc db dc. ({prefix})",
            ("beta_division_prefix_exists",),
            (
                "intro p",
                "intro b",
                "intro c",
                "intro l",
                "intro hnonzero",
                "specialize beta_division_prefix_exists p",
                "specialize beta_division_prefix_exists b",
                "specialize beta_division_prefix_exists c",
                "specialize beta_division_prefix_exists l",
                "apply beta_division_prefix_exists",
                "exact hnonzero",
            ),
            "Every finite beta-coded natural prefix has actual beta-coded quotient and least-significant digit prefixes for each nonzero base.",
        ),
        spec(
            LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS,
            f"forall p b c l. ({prime('p', tag='lucas_prefix_prime')}) -> "
            f"exists qb qc db dc. ({prefix})",
            ("prime_nonzero", LUCAS_BASE_P_DIGIT_PREFIX_EXISTS),
            (
                "intro p",
                "intro b",
                "intro c",
                "intro l",
                "intro hprime",
                "specialize lucas_base_p_digit_prefix_exists p",
                "specialize lucas_base_p_digit_prefix_exists b",
                "specialize lucas_base_p_digit_prefix_exists c",
                "specialize lucas_base_p_digit_prefix_exists l",
                "apply lucas_base_p_digit_prefix_exists",
                "intro hzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hzero",
            ),
            "Every prime base constructively digitizes an entire finite beta-coded source prefix.",
        ),
        spec(
            LUCAS_BASE_P_DIGIT_PREFIX_POINT,
            f"forall p b c qb qc db dc l i n. ({prefix}) -> "
            f"({prefix_bound}) -> ({source_entry}) -> ({point_result})",
            ("beta_at_unique",),
            (
                "intro p",
                "intro b",
                "intro c",
                "intro qb",
                "intro qc",
                "intro db",
                "intro dc",
                "intro l",
                "intro i",
                "intro n",
                "intro hprefix",
                "intro hbound",
                "intro hsource",
                "specialize hprefix i",
                "have hpoint : exists value quotient remainder. "
                f"({beta_at('b', 'c', 'i', 'value', tag='lucas_point_source')}) /\\ "
                f"(({beta_at('qb', 'qc', 'i', 'quotient', tag='lucas_point_quotient')}) /\\ "
                f"(({beta_at('db', 'dc', 'i', 'remainder', tag='lucas_point_remainder')}) /\\ "
                f"(value = p * quotient + remainder /\\ "
                f"({_lt('remainder', 'p', tag='point_digit_bound')}))))",
                "apply hprefix",
                "exact hbound",
                "cases hpoint",
                "cases hpoint_witness",
                "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_right",
                "cases hpoint_witness_witness_witness_right_right",
                "cases hpoint_witness_witness_witness_right_right_right",
                "have hvalue : x = n",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique n",
                "apply beta_at_unique",
                "exact hpoint_witness_witness_witness_left",
                "exact hsource",
                "exists x1",
                "exists x2",
                "split",
                "exact hpoint_witness_witness_witness_right_left",
                "split",
                "exact hpoint_witness_witness_witness_right_right_left",
                "split",
                "rewrite <- hvalue",
                "exact hpoint_witness_witness_witness_right_right_right_left",
                "exact hpoint_witness_witness_witness_right_right_right_right",
            ),
            "At every source beta index, the quotient and digit beta prefixes expose the unique actual quotient/digit witnesses of that source value.",
        ),
        spec(
            LUCAS_BASE_P_TWO_DIGIT_TOTAL,
            f"forall p n. ~(p = 0) -> exists q0 d0 q1 d1. ({two_extracted})",
            (LUCAS_BASE_P_DIGIT_TOTAL,),
            (
                "intro p",
                "intro n",
                "intro hnonzero",
                f"have hfirst : exists q0 d0. ({first_extracted})",
                "specialize lucas_base_p_digit_total p",
                "specialize lucas_base_p_digit_total n",
                "apply lucas_base_p_digit_total",
                "exact hnonzero",
                "cases hfirst",
                "cases hfirst_witness",
                "have hsecond : exists q1 d1. "
                f"({_base_p_digit('p', 'x', 'q1', 'd1', tag='second_exists')})",
                "specialize lucas_base_p_digit_total p",
                "specialize lucas_base_p_digit_total x",
                "apply lucas_base_p_digit_total",
                "exact hnonzero",
                "cases hsecond",
                "cases hsecond_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hfirst_witness_witness",
                "exact hsecond_witness_witness",
            ),
            "Every nonzero base constructively extracts two genuinely successive digits: the second source is exactly the first quotient.",
        ),
        spec(
            LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL,
            f"forall p n. ({prime('p', tag='lucas_two_digit_prime')}) -> "
            f"exists q0 d0 q1 d1. ({two_extracted})",
            ("prime_nonzero", LUCAS_BASE_P_TWO_DIGIT_TOTAL),
            (
                "intro p",
                "intro n",
                "intro hprime",
                "specialize lucas_base_p_two_digit_total p",
                "specialize lucas_base_p_two_digit_total n",
                "apply lucas_base_p_two_digit_total",
                "intro hzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hzero",
            ),
            "Every prime base constructively provides two coherent successive digits and their remaining quotient.",
        ),
        spec(
            LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION,
            f"forall p n q0 d0 q1 d1. ({first_extracted}) -> "
            f"({second_extracted}) -> "
            "n = (p * p) * q1 + (p * d1 + d0)",
            ("mul_add", "mul_assoc", "add_assoc"),
            (
                "intro p",
                "intro n",
                "intro q0",
                "intro d0",
                "intro q1",
                "intro d1",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "rewrite hsecond_left at hfirst_left",
                "trans p * (p * q1 + d1) + d0",
                "exact hfirst_left",
                "trans (p * (p * q1) + p * d1) + d0",
                "congr",
                "apply mul_add",
                "refl",
                "trans ((p * p) * q1 + p * d1) + d0",
                "congr",
                "congr",
                "symm",
                "apply mul_assoc",
                "refl",
                "refl",
                "apply add_assoc",
            ),
            "Two coherent bounded base-p digits reconstruct the exact natural n = p²*q1 + p*d1 + d0 without introducing exponentiation.",
        ),
        spec(
            LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE,
            f"forall p C0. ({row_initial}) -> C0 = S (0)",
            ("choose_zero",),
            (
                "intro p",
                "intro C0",
                "intro hchoose",
                "specialize choose_zero p",
                "specialize choose_zero C0",
                "apply choose_zero",
                "exact hchoose",
            ),
            "The initial coefficient of every relational Pascal row is exactly one.",
        ),
        spec(
            LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE,
            f"forall p Cp. ({row_terminal}) -> Cp = S (0)",
            ("choose_self",),
            (
                "intro p",
                "intro Cp",
                "intro hchoose",
                "specialize choose_self p",
                "specialize choose_self Cp",
                "apply choose_self",
                "exact hchoose",
            ),
            "The terminal coefficient of every relational Pascal row is exactly one.",
        ),
        spec(
            LUCAS_PRIME_ROW_SPARSE_COMPLETE,
            f"forall p k j C C0 Cp. ({row_prime}) -> k + j = p -> "
            f"({row_left}) -> ({row_right}) -> ({row_initial}) -> "
            f"({row_terminal}) -> ({row_choose}) -> "
            f"((C0 = S (0)) /\\ ((Cp = S (0)) /\\ ({row_divides})))",
            (
                LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE,
                LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE,
                LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE,
            ),
            (
                "intro p",
                "intro k",
                "intro j",
                "intro C",
                "intro C0",
                "intro Cp",
                "intro hprime",
                "intro hsum",
                "intro hk",
                "intro hj",
                "intro hinitial",
                "intro hterminal",
                "intro hinterior",
                "split",
                "specialize lucas_prime_row_initial_coefficient_one p",
                "specialize lucas_prime_row_initial_coefficient_one C0",
                "apply lucas_prime_row_initial_coefficient_one",
                "exact hinitial",
                "split",
                "specialize lucas_prime_row_terminal_coefficient_one p",
                "specialize lucas_prime_row_terminal_coefficient_one Cp",
                "apply lucas_prime_row_terminal_coefficient_one",
                "exact hterminal",
                "specialize lucas_prime_row_interior_divisible p",
                "specialize lucas_prime_row_interior_divisible k",
                "specialize lucas_prime_row_interior_divisible j",
                "specialize lucas_prime_row_interior_divisible C",
                "apply lucas_prime_row_interior_divisible",
                "exact hprime",
                "exact hsum",
                "exact hk",
                "exact hj",
                "exact hinterior",
            ),
            "Every prime Pascal row has exact boundary coefficients one and every interior coefficient divisible by its prime modulus.",
        ),
    )


__all__ = [
    "LUCAS_BASE_P_DIGIT_FUNCTIONAL",
    "LUCAS_BASE_P_DIGIT_OF_SMALL_VALUE",
    "LUCAS_BASE_P_DIGIT_PREFIX_EXISTS",
    "LUCAS_BASE_P_DIGIT_PREFIX_POINT",
    "LUCAS_BASE_P_DIGIT_TOTAL",
    "LUCAS_BASE_P_TWO_DIGIT_RECONSTRUCTION",
    "LUCAS_BASE_P_TWO_DIGIT_TOTAL",
    "LUCAS_BASE_P_ZERO_DIGIT_IFF_DIVIDES",
    "LUCAS_CHOOSE_PRIME_DIVISOR_BOUND",
    "LUCAS_DIGIT_CARRY_IFF_PRIME_DIVIDES",
    "LUCAS_DIGIT_CARRY_IMPLIES_PRIME_DIVIDES",
    "LUCAS_DIGIT_NO_CARRY_IFF_NOT_DIVIDES",
    "LUCAS_PRIME_BASE_DIGIT_PREFIX_EXISTS",
    "LUCAS_PRIME_BASE_DIGIT_TOTAL",
    "LUCAS_PRIME_BASE_TWO_DIGIT_TOTAL",
    "LUCAS_PRIME_ROW_INITIAL_COEFFICIENT_ONE",
    "LUCAS_PRIME_ROW_INTERIOR_DIVISIBLE",
    "LUCAS_PRIME_ROW_SPARSE_COMPLETE",
    "LUCAS_PRIME_ROW_TERMINAL_COEFFICIENT_ONE",
    "make_lucas_digit_candidate_theorems",
]
