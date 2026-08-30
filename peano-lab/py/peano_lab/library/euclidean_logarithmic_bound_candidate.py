"""Genuine logarithmic Euclidean histories in unchanged Heyting arithmetic.

Every displayed relation expands hygienically into the existing first-order
language.  The central argument performs induction on a *witnessed* power of
two, constructs actual beta-coded Euclidean histories, and applies the already
checked strict two-division halving theorem.  No host-language calculation,
new arithmetic primitive, classical principle, or additional kernel rule is
used as mathematical evidence.
"""

from __future__ import annotations

from typing import Any, Callable

from .binary_length_candidate import (
    _power_two_terms,
    binary_length_relation,
)
from .continued_fraction_candidate import _state_at_term, _trace_term
from .euclidean_complexity_candidate import euclidean_division
from .euclidean_gcd_transport_candidate import euclidean_anchored_execution
from .finite_fold_surface import _identifier, _lt
from .ha_canonical_gcd_candidate import is_gcd


EUCLIDEAN_LOG_DOUBLE_MONOTONE = "euclidean_log_double_monotone"
EUCLIDEAN_LOG_STRICT_HALF_CANCEL = "euclidean_log_strict_half_cancel"
EUCLIDEAN_LOG_HALVING_POWER_DROP = "euclidean_log_halving_power_drop"
EUCLIDEAN_LOG_DOUBLE_SUCCESSOR = "euclidean_log_double_successor"
EUCLIDEAN_LOG_BUDGET_WEAKEN = "euclidean_log_budget_weaken"
EUCLIDEAN_LOG_BUDGET_EXTEND = "euclidean_log_budget_extend"
EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE = "euclidean_log_budget_extend_twice"
EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR = "euclidean_log_budget_zero_divisor"
EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER = "euclidean_log_budget_successor_power"
EUCLIDEAN_LOG_ZERO_BELOW_POWER = "euclidean_log_zero_below_power"
EUCLIDEAN_LOG_POWER_ZERO_DIVISOR = "euclidean_log_power_zero_divisor"
EUCLIDEAN_LOG_TRACE_BELOW_POWER = "euclidean_log_trace_below_power"
EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER = "euclidean_log_binary_length_upper_power"
EUCLIDEAN_LOG_TRACE_BOUND = "euclidean_log_trace_bound"
EUCLIDEAN_LOG_EXECUTION_STRONG = "euclidean_log_execution_strong"
EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND = "euclidean_gcd_execution_logarithmic_bound"
EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_EXISTS = "euclidean_gcd_execution_logarithmic_exists"


def _arguments(*items: tuple[str, str]) -> tuple[str, ...]:
    return tuple(_identifier(value, label) for value, label in items)


def _fresh(tag: str, arguments: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    safe = _identifier(tag, "logarithmic Euclidean binder tag")
    names = tuple(f"elb_{role}_{safe}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(arguments):
        raise ValueError("generated logarithmic Euclidean binder captures an argument")
    return names


def _budget_term(
    dividend: str,
    divisor: str,
    budget: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    quotient_list, history, scale, steps, gap = _fresh(
        tag, arguments, "list", "history", "scale", "steps", "gap"
    )
    owned = arguments + (quotient_list, history, scale, steps, gap)
    trace = _trace_term(
        dividend,
        divisor,
        quotient_list,
        history,
        scale,
        steps,
        tag=f"elb_{tag}_budget",
        arguments=owned,
    )
    return (
        f"exists {quotient_list} {history} {scale} {steps}. "
        f"(({trace}) /\\ exists {gap}. {gap} + {steps} = ({budget}))"
    )


def euclidean_bounded_trace(
    dividend: str,
    divisor: str,
    budget: str,
    *,
    tag: str,
) -> str:
    """Expand a genuine complete beta-history with ``steps <= budget``."""

    arguments = _arguments(
        (dividend, "logarithmic Euclidean dividend"),
        (divisor, "logarithmic Euclidean divisor"),
        (budget, "logarithmic Euclidean budget"),
    )
    return _budget_term(*arguments, tag=tag, arguments=arguments)


def euclidean_logarithmic_execution(
    dividend: str,
    divisor: str,
    length: str,
    result: str,
    steps: str,
    *,
    tag: str,
) -> str:
    """Expand ``BitLen /\ AnchoredExecution /\ steps <= 2*length+1``."""

    arguments = _arguments(
        (dividend, "logarithmic Euclidean dividend"),
        (divisor, "logarithmic Euclidean divisor"),
        (length, "logarithmic Euclidean bit length"),
        (result, "logarithmic Euclidean gcd output"),
        (steps, "logarithmic Euclidean step count"),
    )
    safe = _identifier(tag, "logarithmic Euclidean binder tag")
    (gap,) = _fresh(safe, arguments, "bound_gap")
    bit_length = binary_length_relation(divisor, length, tag=f"elb_{safe}_length")
    execution = euclidean_anchored_execution(
        dividend, divisor, result, steps, tag=f"elb_{safe}_execution"
    )
    return (
        f"(({bit_length}) /\\ (({execution}) /\\ "
        f"exists {gap}. {gap} + {steps} = 2 * {length} + 1))"
    )


def _power(exponent: str, value: str, *, tag: str) -> str:
    return _power_two_terms(exponent, value, tag=f"elb_{tag}")


def _less(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    return _lt(left, right, tag=f"elb_{tag}", avoid=avoid)


def make_euclidean_logarithmic_bound_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return ordered original-kernel proofs for the exact G101 bound."""

    base = _budget_term("a", "b", "B", tag="base", arguments=("a", "b", "B"))
    weakened = _budget_term(
        "a", "b", "S B", tag="weakened", arguments=("a", "b", "B")
    )
    reduced = _budget_term("b", "r", "B", tag="reduced", arguments=("a", "b", "q", "r", "B"))
    extended = _budget_term(
        "a", "b", "S B", tag="extended", arguments=("a", "b", "q", "r", "B")
    )
    first = euclidean_division("a", "b", "q", "r", tag="elb_first")
    second = euclidean_division("b", "r", "Q", "t", tag="elb_second")
    twice_reduced = _budget_term(
        "r", "t", "B", tag="twice_reduced", arguments=("a", "b", "q", "r", "Q", "t", "B")
    )
    twice_extended = _budget_term(
        "a", "b", "S (S B)", tag="twice_extended", arguments=("a", "b", "q", "r", "Q", "t", "B")
    )
    power = _power("n", "p", tag="power")
    zero_power = _power("0", "p", tag="zero_power")
    below = _less("b", "p", tag="below", avoid=("n", "p", "b"))
    doubled_budget = _budget_term(
        "a", "b", "S (S (n + n))", tag="doubled", arguments=("a", "b", "n")
    )
    successor_budget = _budget_term(
        "a", "b", "(S n + S n)", tag="successor", arguments=("a", "b", "n")
    )
    induction_budget = _budget_term(
        "a", "b", "(n + n)", tag="induction", arguments=("n", "p", "b", "a")
    )
    bit_length = binary_length_relation("b", "l", tag="elb_length")
    bit_power = _power("l", "p", tag="length_upper")
    bit_below = _less("b", "p", tag="length_upper", avoid=("b", "l", "p"))
    length_budget = _budget_term(
        "a", "b", "(l + l)", tag="length_budget", arguments=("a", "b", "l")
    )
    anchored = euclidean_anchored_execution("a", "b", "g", "k", tag="elb_anchored")
    logarithmic = euclidean_logarithmic_execution("a", "b", "l", "g", "k", tag="root")

    return (
        spec(
            EUCLIDEAN_LOG_DOUBLE_MONOTONE,
            "forall a b. (exists gap. gap + a = b) -> "
            "exists gap. gap + (a + a) = b + b",
            ("add_le_add_right", "add_le_add_left", "le_trans"),
            (
                "intro a", "intro b", "intro hle",
                "have hfirst : exists gap. gap + (a + a) = b + a",
                "specialize add_le_add_right a", "specialize add_le_add_right b",
                "specialize add_le_add_right a", "apply add_le_add_right", "exact hle",
                "have hsecond : exists gap. gap + (b + a) = b + b",
                "specialize add_le_add_left a", "specialize add_le_add_left b",
                "specialize add_le_add_left b", "apply add_le_add_left", "exact hle",
                "specialize le_trans (a + a)", "specialize le_trans (b + a)",
                "specialize le_trans (b + b)", "apply le_trans", "exact hfirst",
                "exact hsecond",
            ),
            "Constructive natural doubling preserves witnessed non-strict order.",
        ),
        spec(
            EUCLIDEAN_LOG_STRICT_HALF_CANCEL,
            "forall t p. (exists gap. gap + S (t + t) = p + p) -> "
            "exists gap. gap + S t = p",
            (
                "le_total", "le_eq_or_lt", EUCLIDEAN_LOG_DOUBLE_MONOTONE,
                "lt_not_le", "lt_irrefl_expanded",
            ),
            (
                "intro t", "intro p", "intro hstrict",
                "specialize le_total p", "specialize le_total t", "cases le_total",
                "exfalso", "specialize lt_not_le (t + t)",
                "specialize lt_not_le (p + p)", "apply lt_not_le", "exact hstrict",
                f"specialize {EUCLIDEAN_LOG_DOUBLE_MONOTONE} p",
                f"specialize {EUCLIDEAN_LOG_DOUBLE_MONOTONE} t",
                f"apply {EUCLIDEAN_LOG_DOUBLE_MONOTONE}", "exact le_total_left",
                "specialize le_eq_or_lt t", "specialize le_eq_or_lt p",
                "have hcases : t = p \\/ exists gap. gap + S t = p",
                "apply le_eq_or_lt", "exact le_total_right", "cases hcases",
                "exfalso", "specialize lt_irrefl_expanded (p + p)",
                "apply lt_irrefl_expanded", "rewrite hcases_left at hstrict",
                "rewrite hcases_left at hstrict", "exact hstrict",
                "exact hcases_right",
            ),
            "Strict comparison of two exact doubles constructively cancels the factor two.",
        ),
        spec(
            EUCLIDEAN_LOG_HALVING_POWER_DROP,
            "forall b t p. (exists gap. gap + S (t + t) = b) -> "
            "(exists gap. gap + S b = p + p) -> exists gap. gap + S t = p",
            ("lt_trans", EUCLIDEAN_LOG_STRICT_HALF_CANCEL),
            (
                "intro b", "intro t", "intro p", "intro hhalf", "intro hupper",
                f"specialize {EUCLIDEAN_LOG_STRICT_HALF_CANCEL} t",
                f"specialize {EUCLIDEAN_LOG_STRICT_HALF_CANCEL} p",
                f"apply {EUCLIDEAN_LOG_STRICT_HALF_CANCEL}",
                "specialize lt_trans (t + t)", "specialize lt_trans b",
                "specialize lt_trans (p + p)", "apply lt_trans",
                "exact hhalf", "exact hupper",
            ),
            "A genuine two-step strict halving below twice a power lies below that power.",
        ),
        spec(
            EUCLIDEAN_LOG_DOUBLE_SUCCESSOR,
            "forall n. S n + S n = S (S (n + n))",
            ("add_succ_left",),
            (
                "intro n", "specialize add_succ_left n",
                "specialize add_succ_left (S n)", "rewrite add_succ_left",
                "rewrite PA4", "refl",
            ),
            "The exact two-step budget for a successor exponent grows by two.",
        ),
        spec(
            EUCLIDEAN_LOG_BUDGET_WEAKEN,
            f"forall a b B. ({base}) -> ({weakened})",
            ("le_succ",),
            (
                "intro a", "intro b", "intro B", "intro htrace",
                "cases htrace", "cases htrace_witness", "cases htrace_witness_witness",
                "cases htrace_witness_witness_witness",
                "cases htrace_witness_witness_witness_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact htrace_witness_witness_witness_witness_left",
                "specialize le_succ x3", "specialize le_succ B", "apply le_succ",
                "exact htrace_witness_witness_witness_witness_right",
            ),
            "Any actual complete Euclidean beta-history remains valid under one extra budget unit.",
        ),
        spec(
            EUCLIDEAN_LOG_BUDGET_EXTEND,
            f"forall a b q r B. ({first}) -> ({reduced}) -> ({extended})",
            ("continued_fraction_trace_extend", "succ_le_succ"),
            (
                "intro a", "intro b", "intro q", "intro r", "intro B",
                "intro hdivision", "intro htrace", "cases hdivision",
                "cases htrace", "cases htrace_witness", "cases htrace_witness_witness",
                "cases htrace_witness_witness_witness",
                "cases htrace_witness_witness_witness_witness",
                "specialize continued_fraction_trace_extend a",
                "specialize continued_fraction_trace_extend b",
                "specialize continued_fraction_trace_extend q",
                "specialize continued_fraction_trace_extend r",
                "specialize continued_fraction_trace_extend x",
                "specialize continued_fraction_trace_extend x1",
                "specialize continued_fraction_trace_extend x2",
                "specialize continued_fraction_trace_extend x3",
                "have hextension : exists s z c. "
                "((s = S ((q + x) * S (q + x) + (x + x))) /\\ "
                f"({_trace_term('a','b','s','z','c','S x3',tag='elb_extend_have',arguments=('a','b','q','r','B','x','x1','x2','x3','s','z','c'))}))",
                "apply continued_fraction_trace_extend", "exact hdivision_left",
                "exact hdivision_right",
                "exact htrace_witness_witness_witness_witness_left",
                "cases hextension", "cases hextension_witness",
                "cases hextension_witness_witness",
                "cases hextension_witness_witness_witness",
                "exists x4", "exists x5", "exists x6", "exists S x3", "split",
                "exact hextension_witness_witness_witness_right",
                "specialize succ_le_succ x3", "specialize succ_le_succ B",
                "apply succ_le_succ",
                "exact htrace_witness_witness_witness_witness_right",
            ),
            "One actual strict Euclidean division extends a genuine bounded beta-history by exactly one step.",
        ),
        spec(
            EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE,
            f"forall a b q r Q t B. ({first}) -> ({second}) -> "
            f"({twice_reduced}) -> ({twice_extended})",
            (EUCLIDEAN_LOG_BUDGET_EXTEND,),
            (
                "intro a", "intro b", "intro q", "intro r", "intro Q", "intro t",
                "intro B", "intro hfirst", "intro hsecond", "intro htrace",
                "have hcopy : forall a b q r B. "
                f"({first}) -> ({reduced}) -> ({extended})",
                f"exact {EUCLIDEAN_LOG_BUDGET_EXTEND}",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} r",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} Q",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} t",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} B",
                f"have hmiddle : {_budget_term('b','r','S B',tag='twice_middle',arguments=('a','b','q','r','Q','t','B'))}",
                f"apply {EUCLIDEAN_LOG_BUDGET_EXTEND}", "exact hsecond", "exact htrace",
                "specialize hcopy a", "specialize hcopy b", "specialize hcopy q",
                "specialize hcopy r", "specialize hcopy (S B)", "apply hcopy",
                "exact hfirst", "exact hmiddle",
            ),
            "Two genuine consecutive Euclidean divisions extend a complete beta-history by exactly two steps.",
        ),
        spec(
            EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR,
            f"forall a b B. b = 0 -> ({base})",
            ("euclidean_trace_exists_linear", "le_zero"),
            (
                "intro a", "intro b", "intro B", "intro hzero",
                "specialize euclidean_trace_exists_linear a",
                "specialize euclidean_trace_exists_linear b",
                "cases euclidean_trace_exists_linear",
                "cases euclidean_trace_exists_linear_witness",
                "cases euclidean_trace_exists_linear_witness_witness",
                "cases euclidean_trace_exists_linear_witness_witness_witness",
                "cases euclidean_trace_exists_linear_witness_witness_witness_witness",
                "have hsteps : x3 = 0", "specialize le_zero x3", "apply le_zero",
                "rewrite hzero at euclidean_trace_exists_linear_witness_witness_witness_witness_right",
                "exact euclidean_trace_exists_linear_witness_witness_witness_witness_right",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact euclidean_trace_exists_linear_witness_witness_witness_witness_left",
                "exists B", "rewrite hsteps", "simp",
            ),
            "A zero-divisor input has a genuine zero-step Euclidean history within every supplied budget.",
        ),
        spec(
            EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER,
            f"forall a b n. ({doubled_budget}) -> ({successor_budget})",
            (EUCLIDEAN_LOG_DOUBLE_SUCCESSOR,),
            (
                "intro a", "intro b", "intro n", "intro htrace",
                f"specialize {EUCLIDEAN_LOG_DOUBLE_SUCCESSOR} n",
                f"rewrite {EUCLIDEAN_LOG_DOUBLE_SUCCESSOR}", "exact htrace",
            ),
            "An exact two-step budget is identically the doubled successor-exponent budget.",
        ),
        spec(
            EUCLIDEAN_LOG_ZERO_BELOW_POWER,
            f"forall n p b. ({power}) -> b = 0 -> ({below})",
            ("binary_power_two_nonzero", "one_le_of_ne_zero"),
            (
                "intro n", "intro p", "intro b", "intro hpower", "intro hzero",
                "specialize binary_power_two_nonzero n",
                "specialize binary_power_two_nonzero p",
                "have hnonzero : ~(p = 0)", "intro hpzero",
                "apply binary_power_two_nonzero", "exact hpower", "exact hpzero",
                "specialize one_le_of_ne_zero p", "have hpositive : exists gap. gap + 1 = p",
                "apply one_le_of_ne_zero", "exact hnonzero", "cases hpositive",
                "exists x", "rewrite hzero", "exact hpositive_witness",
            ),
            "The zero Euclidean divisor is strictly below every witnessed power of two.",
        ),
        spec(
            EUCLIDEAN_LOG_POWER_ZERO_DIVISOR,
            f"forall p b. ({zero_power}) -> ({below}) -> b = 0",
            ("binary_power_two_zero_value", "le_of_succ_le_succ", "le_zero"),
            (
                "intro p", "intro b", "intro hpower", "intro hbelow",
                "specialize binary_power_two_zero_value p",
                "have hvalue : p = 1", "apply binary_power_two_zero_value", "exact hpower",
                "rewrite hvalue at hbelow",
                "specialize le_of_succ_le_succ b", "specialize le_of_succ_le_succ 0",
                "have hzero : exists gap. gap + b = 0",
                "apply le_of_succ_le_succ", "exact hbelow",
                "specialize le_zero b", "apply le_zero", "exact hzero",
            ),
            "A natural strictly below the witnessed zeroth power of two must be zero.",
        ),
        spec(
            EUCLIDEAN_LOG_TRACE_BELOW_POWER,
            f"forall n p. ({power}) -> forall b. ({below}) -> forall a. "
            f"({induction_budget})",
            (
                EUCLIDEAN_LOG_POWER_ZERO_DIVISOR,
                EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR,
                "binary_power_two_exists",
                "binary_power_two_successor_double",
                "eq_decidable",
                "euclidean_division_step_exists",
                "zero_or_succ",
                EUCLIDEAN_LOG_BUDGET_EXTEND,
                EUCLIDEAN_LOG_BUDGET_WEAKEN,
                EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER,
                "division_remainder_exists",
                "euclidean_two_step_halving",
                EUCLIDEAN_LOG_HALVING_POWER_DROP,
                EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE,
            ),
            (
                "induction n",
                "intro p", "intro hpower", "intro b", "intro hbelow", "intro a",
                "have hzero : b = 0",
                f"specialize {EUCLIDEAN_LOG_POWER_ZERO_DIVISOR} p",
                f"specialize {EUCLIDEAN_LOG_POWER_ZERO_DIVISOR} b",
                f"apply {EUCLIDEAN_LOG_POWER_ZERO_DIVISOR}", "exact hpower", "exact hbelow",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} (0 + 0)",
                f"apply {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR}", "exact hzero",
                "intro p", "intro hpower", "intro b", "intro hbelow", "intro a",
                "specialize binary_power_two_exists n", "cases binary_power_two_exists",
                "have hdouble : p = x + x",
                "specialize binary_power_two_successor_double n",
                "specialize binary_power_two_successor_double x",
                "specialize binary_power_two_successor_double p",
                "apply binary_power_two_successor_double",
                "exact binary_power_two_exists_witness", "exact hpower",
                "specialize eq_decidable b", "specialize eq_decidable 0",
                "cases eq_decidable",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} (S n + S n)",
                f"apply {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR}", "exact eq_decidable_left",
                f"have hfirst : exists q r. ({euclidean_division('a','b','q','r',tag='elb_induction_first')})",
                "specialize euclidean_division_step_exists a",
                "specialize euclidean_division_step_exists b",
                "apply euclidean_division_step_exists", "exact eq_decidable_right",
                "cases hfirst", "cases hfirst_witness",
                "specialize zero_or_succ x2", "cases zero_or_succ",
                f"have hsmall : {_budget_term('b','x2','(n + n)',tag='zero_remainder',arguments=('n','p','b','a','x','x1','x2'))}",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} x2",
                f"specialize {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR} (n + n)",
                f"apply {EUCLIDEAN_LOG_BUDGET_ZERO_DIVISOR}", "exact zero_or_succ_left",
                f"have hfirst_budget : {_budget_term('a','b','S (n + n)',tag='first_budget',arguments=('n','p','b','a','x','x1','x2'))}",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} x1",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} x2",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND} (n + n)",
                f"apply {EUCLIDEAN_LOG_BUDGET_EXTEND}", "exact hfirst_witness_witness",
                "exact hsmall",
                f"have hweakened : {_budget_term('a','b','S (S (n + n))',tag='one_weakened',arguments=('n','p','b','a','x','x1','x2'))}",
                f"specialize {EUCLIDEAN_LOG_BUDGET_WEAKEN} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_WEAKEN} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_WEAKEN} (S (n + n))",
                f"apply {EUCLIDEAN_LOG_BUDGET_WEAKEN}", "exact hfirst_budget",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} n",
                f"apply {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER}", "exact hweakened",
                "cases zero_or_succ_right",
                "have hnonzero : ~(x2 = 0)", "intro hzero", "apply PA1",
                "trans x2", "symm", "exact zero_or_succ_right_witness", "exact hzero",
                "specialize division_remainder_exists x2",
                "specialize division_remainder_exists b",
                "have hsecond : exists Q t. "
                f"({euclidean_division('b','x2','Q','t',tag='elb_induction_second')})",
                "apply division_remainder_exists", "exact hnonzero",
                "cases hsecond", "cases hsecond_witness",
                "have hhalf : exists gap. gap + S (x5 + x5) = b",
                "specialize euclidean_two_step_halving a",
                "specialize euclidean_two_step_halving b",
                "specialize euclidean_two_step_halving x1",
                "specialize euclidean_two_step_halving x2",
                "specialize euclidean_two_step_halving x4",
                "specialize euclidean_two_step_halving x5",
                "apply euclidean_two_step_halving", "exact hfirst_witness_witness",
                "exact hsecond_witness_witness",
                "have hupper : exists gap. gap + S b = x + x",
                "rewrite hdouble at hbelow", "exact hbelow",
                "have hdrop : exists gap. gap + S x5 = x",
                f"specialize {EUCLIDEAN_LOG_HALVING_POWER_DROP} b",
                f"specialize {EUCLIDEAN_LOG_HALVING_POWER_DROP} x5",
                f"specialize {EUCLIDEAN_LOG_HALVING_POWER_DROP} x",
                f"apply {EUCLIDEAN_LOG_HALVING_POWER_DROP}", "exact hhalf", "exact hupper",
                "specialize IH x",
                "have hbounded : forall b. (exists gap. gap + S b = x) -> forall a. "
                f"({_budget_term('a','b','(n + n)',tag='ih_bounded',arguments=('n','p','x','b','a'))})",
                "apply IH", "exact binary_power_two_exists_witness",
                "specialize hbounded x5",
                "have hall : forall z. "
                f"({_budget_term('z','x5','(n + n)',tag='ih_all',arguments=('n','p','b','a','x','x1','x2','x3','x4','x5','z'))})",
                "apply hbounded", "exact hdrop", "specialize hall x2",
                f"have htwice : {_budget_term('a','b','S (S (n + n))',tag='twice_budget',arguments=('n','p','b','a','x','x1','x2','x3','x4','x5'))}",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} x1",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} x2",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} x4",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} x5",
                f"specialize {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE} (n + n)",
                f"apply {EUCLIDEAN_LOG_BUDGET_EXTEND_TWICE}",
                "exact hfirst_witness_witness", "exact hsecond_witness_witness", "exact hall",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} a",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} b",
                f"specialize {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER} n",
                f"apply {EUCLIDEAN_LOG_BUDGET_SUCCESSOR_POWER}", "exact htwice",
            ),
            "Induction on a witnessed power of two constructs genuine complete Euclidean beta histories in at most twice the exponent, using strict halving across every actual pair of divisions.",
        ),
        spec(
            EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER,
            f"forall b l. ({bit_length}) -> exists p. (({bit_power}) /\\ ({bit_below}))",
            ("binary_power_two_exists", EUCLIDEAN_LOG_ZERO_BELOW_POWER),
            (
                "intro b", "intro l", "intro hlength", "cases hlength",
                "cases hlength_left", "specialize binary_power_two_exists l",
                "cases binary_power_two_exists", "exists x", "split",
                "exact binary_power_two_exists_witness",
                f"specialize {EUCLIDEAN_LOG_ZERO_BELOW_POWER} l",
                f"specialize {EUCLIDEAN_LOG_ZERO_BELOW_POWER} x",
                f"specialize {EUCLIDEAN_LOG_ZERO_BELOW_POWER} b",
                f"apply {EUCLIDEAN_LOG_ZERO_BELOW_POWER}",
                "exact binary_power_two_exists_witness", "exact hlength_left_left",
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
            "Every genuine BitLen witness, including the zero-has-one-digit convention, supplies a witnessed strict upper power of two.",
        ),
        spec(
            EUCLIDEAN_LOG_TRACE_BOUND,
            f"forall a b l. ({bit_length}) -> ({length_budget})",
            (EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER, EUCLIDEAN_LOG_TRACE_BELOW_POWER),
            (
                "intro a", "intro b", "intro l", "intro hlength",
                f"specialize {EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER} b",
                f"specialize {EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER} l",
                f"have hupper : exists p. (({bit_power}) /\\ ({bit_below}))",
                f"apply {EUCLIDEAN_LOG_BINARY_LENGTH_UPPER_POWER}", "exact hlength",
                "cases hupper", "cases hupper_witness",
                f"specialize {EUCLIDEAN_LOG_TRACE_BELOW_POWER} l",
                f"specialize {EUCLIDEAN_LOG_TRACE_BELOW_POWER} x",
                "have hdivisor : forall b. (exists gap. gap + S b = x) -> forall a. "
                f"({_budget_term('a','b','(l + l)',tag='length_divisor',arguments=('a','b','l','x'))})",
                f"apply {EUCLIDEAN_LOG_TRACE_BELOW_POWER}", "exact hupper_witness_left",
                "specialize hdivisor b",
                "have hall : forall z. "
                f"({_budget_term('z','b','(l + l)',tag='length_all',arguments=('a','b','l','x','z'))})",
                "apply hdivisor", "exact hupper_witness_right", "specialize hall a",
                "exact hall",
            ),
            "Every genuine BitLen witness constructively bounds an actual complete Euclidean beta history by twice its length.",
        ),
        spec(
            EUCLIDEAN_LOG_EXECUTION_STRONG,
            f"forall a b l. ({bit_length}) -> exists g k. "
            f"(({anchored}) /\\ exists gap. gap + k = l + l)",
            (EUCLIDEAN_LOG_TRACE_BOUND, "euclidean_trace_terminal_gcd_exists"),
            (
                "intro a", "intro b", "intro l", "intro hlength",
                f"specialize {EUCLIDEAN_LOG_TRACE_BOUND} a",
                f"specialize {EUCLIDEAN_LOG_TRACE_BOUND} b",
                f"specialize {EUCLIDEAN_LOG_TRACE_BOUND} l",
                f"have hbounded : {length_budget}",
                f"apply {EUCLIDEAN_LOG_TRACE_BOUND}", "exact hlength",
                "cases hbounded", "cases hbounded_witness", "cases hbounded_witness_witness",
                "cases hbounded_witness_witness_witness",
                "cases hbounded_witness_witness_witness_witness",
                "have hterminal : exists g. "
                f"(({_state_at_term('x1','x2','0','g','0','0',tag='elb_terminal',avoid=('a','b','l','x','x1','x2','x3','g'))}) /\\ "
                f"({is_gcd('g','a','b',tag='elb_terminal')}))",
                "specialize euclidean_trace_terminal_gcd_exists a",
                "specialize euclidean_trace_terminal_gcd_exists b",
                "specialize euclidean_trace_terminal_gcd_exists x",
                "specialize euclidean_trace_terminal_gcd_exists x1",
                "specialize euclidean_trace_terminal_gcd_exists x2",
                "specialize euclidean_trace_terminal_gcd_exists x3",
                "apply euclidean_trace_terminal_gcd_exists",
                "exact hbounded_witness_witness_witness_witness_left",
                "cases hterminal", "cases hterminal_witness",
                "exists x4", "exists x3", "split", "exists x", "exists x1", "exists x2",
                "split", "exact hbounded_witness_witness_witness_witness_left", "split",
                "exact hterminal_witness_left", "exact hterminal_witness_right",
                "exact hbounded_witness_witness_witness_witness_right",
            ),
            "Every bit-length witness constructs a genuine complete beta execution whose actual terminal state is its gcd and whose exact step count is at most twice that length.",
        ),
        spec(
            EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND,
            f"forall a b l. ({bit_length}) -> exists g k. "
            f"(({anchored}) /\\ exists gap. gap + k = 2 * l + 1)",
            (EUCLIDEAN_LOG_EXECUTION_STRONG, "le_succ", "two_mul_eq_add_self"),
            (
                "intro a", "intro b", "intro l", "intro hlength",
                f"specialize {EUCLIDEAN_LOG_EXECUTION_STRONG} a",
                f"specialize {EUCLIDEAN_LOG_EXECUTION_STRONG} b",
                f"specialize {EUCLIDEAN_LOG_EXECUTION_STRONG} l",
                f"have hstrong : exists g k. (({anchored}) /\\ exists gap. gap + k = l + l)",
                f"apply {EUCLIDEAN_LOG_EXECUTION_STRONG}", "exact hlength",
                "cases hstrong", "cases hstrong_witness", "cases hstrong_witness_witness",
                "exists x", "exists x1", "split", "exact hstrong_witness_witness_left",
                "specialize le_succ x1", "specialize le_succ (l + l)",
                "have hweakened : exists gap. gap + x1 = S (l + l)",
                "apply le_succ", "exact hstrong_witness_witness_right", "cases hweakened",
                "exists x2", "specialize two_mul_eq_add_self l",
                "rewrite two_mul_eq_add_self", "rewrite PA4", "rewrite PA3",
                "exact hweakened_witness",
            ),
            "Exact G101: every witnessed BitLen(b,l) yields a genuine gcd-anchored Euclidean beta execution with steps <= 2*l+1 in unchanged constructive HA.",
        ),
        spec(
            EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_EXISTS,
            f"forall a b. exists l g k. ({logarithmic})",
            ("binary_length_exists", EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND),
            (
                "intro a", "intro b", "specialize binary_length_exists b",
                "cases binary_length_exists",
                f"specialize {EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND} a",
                f"specialize {EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND} b",
                f"specialize {EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND} x",
                "have hexecution : exists g k. "
                f"(({euclidean_anchored_execution('a','b','g','k',tag='elb_total')}) /\\ "
                "exists gap. gap + k = 2 * x + 1)",
                f"apply {EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND}",
                "exact binary_length_exists_witness",
                "cases hexecution", "cases hexecution_witness",
                "cases hexecution_witness_witness", "exists x", "exists x1", "exists x2",
                "split", "exact binary_length_exists_witness", "split",
                "exact hexecution_witness_witness_left",
                "exact hexecution_witness_witness_right",
            ),
            "For every pair of naturals construct all witnesses at once: canonical bit length, an actual terminal-gcd Euclidean beta execution, and the exact logarithmic step bound 2*BitLen(b)+1.",
        ),
    )


__all__ = [
    "euclidean_bounded_trace",
    "euclidean_logarithmic_execution",
    "make_euclidean_logarithmic_bound_candidate_theorems",
]
