"""Total finite simple continued fractions in unchanged first-order HA.

This isolated G071 candidate does not add lists, division functions, a new
predicate, or any trusted kernel rule.  A single beta stream stores a reverse
Euclidean history whose entries are doubled-Cantor encodings of
``(dividend, divisor, forward_quotient_list)``.  The initial history entry is
``(g, 0, nil)``.  Every subsequent entry witnesses a genuine bounded division
and prepends its quotient to the checked tagged-cell list.  Consequently the
terminal list has the ordinary, forward continued-fraction order even though
the auxiliary certificate is constructed backwards.

All readable relations below are hygienic authoring expansions.  The kernel
only receives closed formulas over zero, successor, addition, multiplication,
equality, first-order quantifiers, and intuitionistic connectives.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import _beta_at_term, _identifier, _lt
from .ha_pair_cell_seed_candidate import cell


CONTINUED_FRACTION_INITIAL_STATE_EXISTS = "continued_fraction_initial_state_exists"
CONTINUED_FRACTION_EMPTY_TRACE = "continued_fraction_empty_trace"
CONTINUED_FRACTION_EMPTY_TRACE_EXISTS = "continued_fraction_empty_trace_exists"
CONTINUED_FRACTION_TRACE_EXTEND = "continued_fraction_trace_extend"
CONTINUED_FRACTION_TRACE_EXISTS_UP_TO = "continued_fraction_trace_exists_up_to"
CONTINUED_FRACTION_TRACE_EXISTS = "continued_fraction_trace_exists"
CONTINUED_FRACTION_NONZERO_DIVISOR_EXISTS = (
    "continued_fraction_nonzero_divisor_exists"
)
CONTINUED_FRACTION_POSITIVE_NONEMPTY_EXISTS = (
    "continued_fraction_positive_nonempty_exists"
)
CONTINUED_FRACTION_POSITIVE_EXISTS = "continued_fraction_positive_exists"


def _pair_term(left: str, right: str) -> str:
    """Assemble trusted internal terms using the checked doubled-Cantor code."""

    return f"(({left}) + ({right})) * S (({left}) + ({right})) + (({right}) + ({right}))"


def _packed_state(dividend: str, divisor: str, quotient_list: str) -> str:
    """The exact nested doubled-Cantor code ``Pair(a, Pair(b, list))``."""

    return _pair_term(dividend, _pair_term(divisor, quotient_list))


def _state_at_term(
    code: str,
    scale: str,
    index: str,
    dividend: str,
    divisor: str,
    quotient_list: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    return _beta_at_term(
        code,
        scale,
        index,
        _packed_state(dividend, divisor, quotient_list),
        tag=f"cf_{tag}_state",
        avoid=avoid,
    )


def _fresh(tag: str, arguments: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "continued-fraction binder tag")
    names = tuple(f"cf_{role}_{safe_tag}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(arguments):
        raise ValueError("generated continued-fraction binder captures an argument")
    return names


def _trace_term(
    dividend: str,
    divisor: str,
    quotient_list: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    arguments: tuple[str, ...],
) -> str:
    start, index, old_a, old_b, tail, new_a, new_b, head, quotient = _fresh(
        tag,
        arguments,
        "gcd",
        "index",
        "old_a",
        "old_b",
        "tail",
        "new_a",
        "new_b",
        "head",
        "quotient",
    )
    owned = arguments + (
        start,
        index,
        old_a,
        old_b,
        tail,
        new_a,
        new_b,
        head,
        quotient,
    )
    initial = _state_at_term(
        code, scale, "0", start, "0", "0", tag=f"{tag}_initial", avoid=owned
    )
    terminal = _state_at_term(
        code,
        scale,
        length,
        dividend,
        divisor,
        quotient_list,
        tag=f"{tag}_terminal",
        avoid=owned,
    )
    bound = _lt(index, length, tag=f"cf_{tag}_index", avoid=owned)
    previous = _state_at_term(
        code,
        scale,
        index,
        old_a,
        old_b,
        tail,
        tag=f"{tag}_previous",
        avoid=owned,
    )
    following = _state_at_term(
        code,
        scale,
        f"S {index}",
        new_a,
        new_b,
        head,
        tag=f"{tag}_following",
        avoid=owned,
    )
    remainder_bound = _lt(old_b, new_b, tag=f"cf_{tag}_remainder", avoid=owned)
    return (
        f"exists {start}. (({initial}) /\\ (({terminal}) /\\ "
        f"forall {index}. ({bound}) -> exists {old_a} {old_b} {tail} "
        f"{new_a} {new_b} {head} {quotient}. (({previous}) /\\ "
        f"(({following}) /\\ ({new_b} = {old_a} /\\ "
        f"({new_a} = {new_b} * {quotient} + {old_b} /\\ "
        f"(({remainder_bound}) /\\ ({cell(head, quotient, tail)}))))))))"
    )


def continued_fraction_trace(
    dividend: str,
    divisor: str,
    quotient_list: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a complete, strictly decreasing beta-coded Euclidean history."""

    arguments = tuple(
        _identifier(value, label)
        for value, label in (
            (dividend, "dividend"),
            (divisor, "divisor"),
            (quotient_list, "quotient list"),
            (code, "history code"),
            (scale, "history scale"),
            (length, "history length"),
        )
    )
    return _trace_term(*arguments, tag=tag, arguments=arguments)


def continued_fraction(
    dividend: str,
    divisor: str,
    quotient_list: str,
    *,
    tag: str,
) -> str:
    """Expand G071: positive inputs and a nonempty complete quotient list."""

    arguments = tuple(
        _identifier(value, label)
        for value, label in (
            (dividend, "positive dividend"),
            (divisor, "positive divisor"),
            (quotient_list, "quotient list"),
        )
    )
    ap, bp, code, scale, predecessor = _fresh(
        tag, arguments, "a_pred", "b_pred", "code", "scale", "length_pred"
    )
    owned = arguments + (ap, bp, code, scale, predecessor)
    trace = _trace_term(
        dividend,
        divisor,
        quotient_list,
        code,
        scale,
        f"S {predecessor}",
        tag=f"{tag}_trace",
        arguments=owned,
    )
    return (
        f"exists {ap} {bp} {code} {scale} {predecessor}. "
        f"({dividend} = S {ap} /\\ "
        f"({divisor} = S {bp} /\\ ({trace})))"
    )


def make_continued_fraction_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered, original-kernel G071 proof campaign."""

    base_args = ("a", "z", "c")
    initial = _state_at_term(
        "z", "c", "0", "a", "0", "0", tag="initial_exists", avoid=base_args
    )
    empty = _trace_term(
        "a", "0", "0", "z", "c", "0", tag="empty", arguments=base_args
    )

    extend_args = ("a", "b", "q", "r", "t", "h", "e", "l", "s", "z", "c")
    old_trace = continued_fraction_trace("b", "r", "t", "h", "e", "l", tag="old")
    new_trace = _trace_term(
        "a", "b", "s", "z", "c", "S l", tag="new", arguments=extend_args
    )
    strict_remainder = _lt("r", "b", tag="cf_extension_bound", avoid=extend_args)
    index, value = ("j", "v")
    extension_avoid = extend_args + (index, value, "x")
    extension = (
        "exists z c. "
        f"(({_state_at_term('z','c','S l','a','b','x',tag='extension_new',avoid=extension_avoid)}) /\\ "
        f"forall {index} {value}. "
        f"({_lt(index,'S l',tag='cf_extension_prefix_bound',avoid=extension_avoid)}) -> "
        f"({_beta_at_term('h','e',index,value,tag='cf_extension_source',avoid=extension_avoid)}) -> "
        f"({_beta_at_term('z','c',index,value,tag='cf_extension_target',avoid=extension_avoid)}))"
    )

    def exists_trace(a: str, b: str, *, tag: str) -> str:
        return (
            "exists s h e l. "
            f"({continued_fraction_trace(a, b, 's', 'h', 'e', 'l', tag=tag)})"
        )

    bounded_trace = exists_trace("a", "b", tag="bounded")
    reduced_trace = exists_trace("b", "x1", tag="bounded_reduced")
    reduced_all = exists_trace("z", "x1", tag="bounded_reduced_all")
    smaller_all = exists_trace("z", "b", tag="bounded_smaller_all")
    bounded_extension_args = ("a", "b", "x", "x2", "x5", "s", "z", "c")
    bounded_extension = (
        "exists s z c. "
        f"(({cell('s','x','x2')}) /\\ "
        f"({_trace_term('a','b','s','z','c','S x5',tag='bounded_extension',arguments=bounded_extension_args)}))"
    )
    total_trace = exists_trace("a", "b", tag="total")
    total_all = exists_trace("z", "b", tag="total_all")
    nonzero_trace = _trace_term(
        "a",
        "b",
        "s",
        "h",
        "e",
        "S k",
        tag="nonzero_result",
        arguments=("a", "b", "s", "h", "e", "k"),
    )
    nonzero_tail = exists_trace("b", "x1", tag="nonzero_tail")
    nonzero_extension_args = ("a", "b", "x", "x2", "x5", "s", "z", "c")
    nonzero_extension = (
        "exists s z c. "
        f"(({cell('s','x','x2')}) /\\ "
        f"({_trace_term('a','b','s','z','c','S x5',tag='nonzero_extension',arguments=nonzero_extension_args)}))"
    )
    positive = continued_fraction("a", "b", "s", tag="positive_result")

    return (
        spec(
            CONTINUED_FRACTION_INITIAL_STATE_EXISTS,
            f"forall a. exists z c. ({initial})",
            ("beta_prefix_extend",),
            (
                "intro a",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                f"specialize beta_prefix_extend ({_packed_state('a','0','0')})",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "exact beta_prefix_extend_witness_witness_left",
            ),
            "Every natural initializes an actual beta-coded terminal Euclidean state (a,0,nil).",
        ),
        spec(
            CONTINUED_FRACTION_EMPTY_TRACE,
            f"forall a z c. ({initial}) -> ({empty})",
            (),
            (
                "intro a",
                "intro z",
                "intro c",
                "intro hinitial",
                "exists a",
                "split",
                "exact hinitial",
                "split",
                "exact hinitial",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "rewrite PA4 at hi_witness",
                "apply PA1",
                "exact hi_witness",
            ),
            "The zero-divisor Euclidean base case has exactly the empty quotient list and no transitions.",
        ),
        spec(
            CONTINUED_FRACTION_EMPTY_TRACE_EXISTS,
            f"forall a. exists z c. ({empty})",
            (CONTINUED_FRACTION_INITIAL_STATE_EXISTS, CONTINUED_FRACTION_EMPTY_TRACE),
            (
                "intro a",
                "specialize continued_fraction_initial_state_exists a",
                "cases continued_fraction_initial_state_exists",
                "cases continued_fraction_initial_state_exists_witness",
                "exists x",
                "exists x1",
                "apply continued_fraction_empty_trace",
                "exact continued_fraction_initial_state_exists_witness_witness",
            ),
            "For every dividend, a fully witnessed empty reverse Euclidean history exists at divisor zero.",
        ),
        spec(
            CONTINUED_FRACTION_TRACE_EXTEND,
            "forall a b q r t h e l. "
            f"a = b * q + r -> ({strict_remainder}) -> ({old_trace}) -> "
            f"exists s z c. (({cell('s','q','t')}) /\\ ({new_trace}))",
            (
                "cell_constructor",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "zero_add",
                "lt_of_lt_of_le",
                "le_succ_self",
                "succ_le_succ",
            ),
            (
                "intro a",
                "intro b",
                "intro q",
                "intro r",
                "intro t",
                "intro h",
                "intro e",
                "intro l",
                "intro hdivision",
                "intro hbound",
                "intro htrace",
                "specialize cell_constructor q",
                "specialize cell_constructor t",
                "cases cell_constructor",
                "have hs : x = S ((q + t) * S (q + t) + (t + t))",
                "exact cell_constructor_witness",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_right",
                f"have hextension : {extension}",
                "specialize beta_prefix_extend (S l)",
                "specialize beta_prefix_extend h",
                "specialize beta_prefix_extend e",
                f"specialize beta_prefix_extend ({_packed_state('a','b','x')})",
                "exact beta_prefix_extend",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "exists x",
                "exists x2",
                "exists x3",
                "split",
                "exact hs",
                "exists x1",
                "split",
                "specialize hextension_witness_witness_right 0",
                f"specialize hextension_witness_witness_right ({_packed_state('x1','0','0')})",
                "apply hextension_witness_witness_right",
                "exists l",
                "simp",
                "exact htrace_witness_left",
                "split",
                "exact hextension_witness_witness_left",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exists b",
                "exists r",
                "exists t",
                "exists a",
                "exists b",
                "exists x",
                "exists q",
                "split",
                "specialize hextension_witness_witness_right l",
                f"specialize hextension_witness_witness_right ({_packed_state('b','r','t')})",
                "apply hextension_witness_witness_right",
                "exists 0",
                "apply zero_add",
                "exact htrace_witness_right_left",
                "split",
                "exact hextension_witness_witness_left",
                "split",
                "refl",
                "split",
                "exact hdivision",
                "split",
                "exact hbound",
                "exact hs",
                "specialize htrace_witness_right_right i",
                "have hprevious : exists A B T C D U Q. "
                f"(({_state_at_term('h','e','i','A','B','T',tag='previous_old',avoid=extend_args+('i','A','B','T','C','D','U','Q'))}) /\\ "
                f"(({_state_at_term('h','e','S i','C','D','U',tag='previous_new',avoid=extend_args+('i','A','B','T','C','D','U','Q'))}) /\\ "
                "(D = A /\\ (C = D * Q + B /\\ "
                f"(({_lt('B','D',tag='cf_previous_remainder',avoid=extend_args+('i','A','B','T','C','D','U','Q'))}) /\\ "
                f"({cell('U','Q','T')}))))))",
                "apply htrace_witness_right_right",
                "exact hsplit_right",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                "cases hprevious_witness_witness_witness_witness",
                "cases hprevious_witness_witness_witness_witness_witness",
                "cases hprevious_witness_witness_witness_witness_witness_witness",
                "cases hprevious_witness_witness_witness_witness_witness_witness_witness",
                "cases hprevious_witness_witness_witness_witness_witness_witness_witness_right",
                "cases hprevious_witness_witness_witness_witness_witness_witness_witness_right_right",
                "cases hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_right",
                "cases hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "have hipreserve : exists gap. gap + S i = S l",
                "specialize lt_of_lt_of_le i",
                "specialize lt_of_lt_of_le l",
                "specialize lt_of_lt_of_le (S l)",
                "apply lt_of_lt_of_le",
                "exact hsplit_right",
                "specialize le_succ_self l",
                "exact le_succ_self",
                "have hnextpreserve : exists gap. gap + S (S i) = S l",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hsplit_right",
                "exists x4",
                "exists x5",
                "exists x6",
                "exists x7",
                "exists x8",
                "exists x9",
                "exists x10",
                "split",
                "specialize hextension_witness_witness_right i",
                f"specialize hextension_witness_witness_right ({_packed_state('x4','x5','x6')})",
                "apply hextension_witness_witness_right",
                "exact hipreserve",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_left",
                "split",
                "specialize hextension_witness_witness_right (S i)",
                f"specialize hextension_witness_witness_right ({_packed_state('x7','x8','x9')})",
                "apply hextension_witness_witness_right",
                "exact hnextpreserve",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_right_left",
                "split",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_left",
                "split",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_right_left",
                "split",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_right_right_left",
                "exact hprevious_witness_witness_witness_witness_witness_witness_witness_right_right_right_right_right",
            ),
            "A strict Euclidean division prepends its quotient and extends one beta-coded history without changing any earlier state.",
        ),
        spec(
            CONTINUED_FRACTION_TRACE_EXISTS_UP_TO,
            f"forall B b. (exists gap. gap + b = B) -> forall a. ({bounded_trace})",
            (
                "le_zero",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "division_remainder_exists",
                CONTINUED_FRACTION_EMPTY_TRACE_EXISTS,
                CONTINUED_FRACTION_TRACE_EXTEND,
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
                *(("rewrite hb0",) * 16),
                "exact continued_fraction_empty_trace_exists_witness_witness",
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
                f"have hsmall : {reduced_trace}",
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
                f"have hextend : {bounded_extension}",
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
                "exact hsmall_witness_witness_witness_witness",
                "cases hextend",
                "cases hextend_witness",
                "cases hextend_witness_witness",
                "cases hextend_witness_witness_witness",
                "exists x6",
                "exists x7",
                "exists x8",
                "exists S x5",
                "exact hextend_witness_witness_witness_right",
                "have hbB : exists gap. gap + b = B",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "specialize IH b",
                f"have hall : forall z. ({smaller_all})",
                "apply IH",
                "exact hbB",
                "specialize hall a",
                "exact hall",
            ),
            "Bounded natural induction terminates Euclid at zero and builds a complete forward quotient list for every divisor below its bound.",
        ),
        spec(
            CONTINUED_FRACTION_TRACE_EXISTS,
            f"forall a b. ({total_trace})",
            ("le_refl", CONTINUED_FRACTION_TRACE_EXISTS_UP_TO),
            (
                "intro a",
                "intro b",
                "specialize continued_fraction_trace_exists_up_to b",
                "specialize continued_fraction_trace_exists_up_to b",
                "have hbb : exists gap. gap + b = b",
                "apply le_refl",
                f"have hall : forall z. ({total_all})",
                "apply continued_fraction_trace_exists_up_to",
                "exact hbb",
                "specialize hall a",
                "exact hall",
            ),
            "Every pair of natural numbers, including zero-input boundaries, has a finite completely witnessed Euclidean quotient trace.",
        ),
        spec(
            CONTINUED_FRACTION_NONZERO_DIVISOR_EXISTS,
            "forall a b. ~(b = 0) -> "
            f"exists s h e k. (~(s = 0) /\\ ({nonzero_trace}))",
            (
                "division_remainder_exists",
                CONTINUED_FRACTION_TRACE_EXISTS,
                CONTINUED_FRACTION_TRACE_EXTEND,
                "cell_nonzero",
            ),
            (
                "intro a",
                "intro b",
                "intro hb",
                "have hdivision : exists q r. a = b * q + r /\\ exists gap. gap + S r = b",
                "specialize division_remainder_exists b",
                "specialize division_remainder_exists a",
                "apply division_remainder_exists",
                "exact hb",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                f"have htail : {nonzero_tail}",
                "specialize continued_fraction_trace_exists b",
                "specialize continued_fraction_trace_exists x1",
                "exact continued_fraction_trace_exists",
                "cases htail",
                "cases htail_witness",
                "cases htail_witness_witness",
                "cases htail_witness_witness_witness",
                f"have hextend : {nonzero_extension}",
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
                "exact htail_witness_witness_witness_witness",
                "cases hextend",
                "cases hextend_witness",
                "cases hextend_witness_witness",
                "cases hextend_witness_witness_witness",
                "exists x6",
                "exists x7",
                "exists x8",
                "exists x5",
                "split",
                "intro hzero",
                "specialize cell_nonzero x6",
                "specialize cell_nonzero x",
                "specialize cell_nonzero x2",
                "apply cell_nonzero",
                "exact hextend_witness_witness_witness_left",
                "exact hzero",
                "exact hextend_witness_witness_witness_right",
            ),
            "Every nonzero divisor produces a strictly positive trace length and a genuinely nonempty forward quotient list.",
        ),
        spec(
            CONTINUED_FRACTION_POSITIVE_NONEMPTY_EXISTS,
            "forall a b. ~(a = 0) -> ~(b = 0) -> "
            f"exists s. (({positive}) /\\ ~(s = 0))",
            ("nonzero_is_succ", CONTINUED_FRACTION_NONZERO_DIVISOR_EXISTS),
            (
                "intro a",
                "intro b",
                "intro ha",
                "intro hb",
                "have hsucc_b : forall n. ~(n = 0) -> exists p. n = S p",
                "exact nonzero_is_succ",
                "specialize nonzero_is_succ a",
                "have ha_positive : exists p. a = S p",
                "apply nonzero_is_succ",
                "exact ha",
                "cases ha_positive",
                "specialize hsucc_b b",
                "have hb_positive : exists p. b = S p",
                "apply hsucc_b",
                "exact hb",
                "cases hb_positive",
                "specialize continued_fraction_nonzero_divisor_exists a",
                "specialize continued_fraction_nonzero_divisor_exists b",
                "have htrace : exists s h e k. "
                f"(~(s = 0) /\\ ({nonzero_trace}))",
                "apply continued_fraction_nonzero_divisor_exists",
                "exact hb",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_witness",
                "cases htrace_witness_witness_witness",
                "cases htrace_witness_witness_witness_witness",
                "exists x2",
                "split",
                "exists x",
                "exists x1",
                "exists x3",
                "exists x4",
                "exists x5",
                "split",
                "exact ha_positive_witness",
                "split",
                "exact hb_positive_witness",
                "exact htrace_witness_witness_witness_witness_right",
                "exact htrace_witness_witness_witness_witness_left",
            ),
            "Every positive rational input has a complete simple continued fraction whose exact cell-coded quotient list is nonempty.",
        ),
        spec(
            CONTINUED_FRACTION_POSITIVE_EXISTS,
            f"forall a b. ~(a = 0) -> ~(b = 0) -> exists s. ({positive})",
            (CONTINUED_FRACTION_POSITIVE_NONEMPTY_EXISTS,),
            (
                "intro a",
                "intro b",
                "intro ha",
                "intro hb",
                "specialize continued_fraction_positive_nonempty_exists a",
                "specialize continued_fraction_positive_nonempty_exists b",
                "have hpositive : exists s. "
                f"(({positive}) /\\ ~(s = 0))",
                "apply continued_fraction_positive_nonempty_exists",
                "exact ha",
                "exact hb",
                "cases hpositive",
                "cases hpositive_witness",
                "exists x",
                "exact hpositive_witness_left",
            ),
            "G071: every pair of strictly positive naturals admits its complete witnessed finite simple continued-fraction quotient list.",
        ),
    )
