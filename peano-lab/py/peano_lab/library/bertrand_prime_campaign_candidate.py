"""Constructive next-layer consequences of the checked strict Bertrand root.

The authoring definitions in this file are *only* hygienic abbreviations for
ordinary first-order Heyting-arithmetic formulas.  In particular a Bertrand
window contains both strict inequalities, a central binomial coefficient is a
fully witnessed Pascal-table value, and valuation one is the existing bounded
prime-power valuation relation at the literal natural ``1``.

The candidate factory grants no edition membership or checked-use authority.
Every dependency-curried script is independently checked by the unchanged
intuitionistic kernel; release enrollment is a deliberately separate gate.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_choose_foundation_candidate import (
    _beta_at_term,
    _binders,
    _identifier,
    _le_term,
    _lt_term,
)
from .bertrand_power_valuation_candidate import (
    _power_terms,
    power_valuation,
)
from .fermat_residue_map_candidate import prime


BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM = (
    "bertrand_window_prime_divides_central_binom"
)
BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE = (
    "bertrand_window_prime_square_exceeds_double"
)
BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE = (
    "bertrand_window_central_valuation_at_most_one"
)
BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO = (
    "bertrand_window_central_valuation_nonzero"
)
BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE = (
    "bertrand_window_central_valuation_equals_one"
)
BERTRAND_WINDOW_CENTRAL_VALUATION_ONE = (
    "bertrand_window_central_valuation_one"
)
CENTRAL_BINOM_PRIME_DIVISOR_MULTIPLICITY_ONE_EXISTS = (
    "central_binom_prime_divisor_multiplicity_one_exists"
)
BERTRAND_CHAIN_SINGLETON_CODE_EXISTS = "bertrand_chain_singleton_code_exists"
BERTRAND_CHAIN_SINGLETON_EXISTS = "bertrand_chain_singleton_exists"
BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD = (
    "bertrand_chain_successor_preserves_guard"
)
BERTRAND_CHAIN_PREFIX_EXTEND = "bertrand_chain_prefix_extend"
BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS = "bertrand_chain_prefix_terminal_exists"
ITERATED_BERTRAND_PRIME_CHAIN_EXISTS = "iterated_bertrand_prime_chain_exists"


def _context(*labelled: tuple[str, str]) -> tuple[str, ...]:
    """Return a deduplicated validated context, preserving argument order."""

    return tuple(
        dict.fromkeys(_identifier(value, label) for value, label in labelled)
    )


def bertrand_window(lower: str, candidate: str, *, tag: str) -> str:
    """Expand ``Prime(candidate) /\ lower<candidate<candidate's bound``.

    The upper endpoint is exactly ``lower + lower`` and is *strict*.  Caller
    terms must be genuine identifiers, preventing interpolation and accidental
    capture.  All binders are owned by the checked legacy surface builders.
    """

    context = _context((lower, "Bertrand lower endpoint"), (candidate, "prime"))
    safe_tag = _identifier(tag, "Bertrand-window tag")
    primality = prime(candidate, tag=f"bpc_{safe_tag}_prime")
    below = _lt_term(
        lower,
        candidate,
        tag=f"bpc_{safe_tag}_lower",
        variables=context,
    )
    above = _lt_term(
        candidate,
        f"{lower} + {lower}",
        tag=f"bpc_{safe_tag}_upper",
        variables=context,
    )
    return f"(({primality}) /\\ (({below}) /\\ ({above})))"


def power_valuation_one(base: str, value: str, *, tag: str) -> str:
    """Expand the existing conservative valuation graph at exponent ``1``."""

    context = _context((base, "prime base"), (value, "nonzero value"))
    safe_tag = _identifier(tag, "valuation-one tag")
    marker = "bpc_one_exponent_marker"
    if marker in context:
        raise ValueError("valuation-one marker captures an argument")
    expanded = power_valuation(base, value, marker, tag=f"bpc_{safe_tag}")
    if expanded.count(marker) != 6:
        raise AssertionError("unexpected frozen valuation exponent occurrences")
    return expanded.replace(marker, "1")


def _bertrand_chain_terms(
    code: str,
    scale: str,
    initial: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Build a capture-checked chain for factory-owned compound lengths."""

    context = tuple(dict.fromkeys(variables))
    safe_tag = _identifier(tag, "Bertrand-chain tag")
    index, previous, following = _binders(
        f"bpc_{safe_tag}_chain", context, ("index", "previous", "following")
    )
    local = (*context, index, previous, following)
    start = _beta_at_term(
        code,
        scale,
        "0",
        initial,
        tag=f"bpc_{safe_tag}_start",
        variables=local,
    )
    bound = _lt_term(
        index,
        length,
        tag=f"bpc_{safe_tag}_index",
        variables=local,
    )
    old_entry = _beta_at_term(
        code,
        scale,
        index,
        previous,
        tag=f"bpc_{safe_tag}_previous",
        variables=local,
    )
    new_entry = _beta_at_term(
        code,
        scale,
        f"S {index}",
        following,
        tag=f"bpc_{safe_tag}_following",
        variables=local,
    )
    window = bertrand_window(
        previous, following, tag=f"{safe_tag}_successor"
    )
    return (
        f"(({start}) /\\ forall {index}. ({bound}) -> "
        f"exists {previous} {following}. "
        f"(({old_entry}) /\\ (({new_entry}) /\\ ({window}))))"
    )


def bertrand_chain(
    code: str,
    scale: str,
    initial: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand an exact beta-coded strict-Bertrand chain of ``length`` steps.

    ``code,scale`` jointly witness the conventional Gödel-beta sequence code;
    there are ``length+1`` entries, the zeroth is ``initial``, and *each*
    successor is prime and lies strictly between its predecessor and twice
    that predecessor.  No sequence primitive, choice axiom, or oracle occurs.
    """

    variables = _context(
        (code, "beta sequence code"),
        (scale, "beta sequence scale"),
        (initial, "initial chain value"),
        (length, "chain length"),
    )
    return _bertrand_chain_terms(
        code, scale, initial, length, tag=tag, variables=variables
    )


def _divides(divisor: str, value: str, *, tag: str) -> str:
    variables = _context((divisor, "divisor"), (value, "dividend"))
    (factor,) = _binders(f"bpc_{tag}_factor", variables, ("quotient",))
    return f"exists {factor}. {value} = {divisor} * {factor}"


def make_bertrand_prime_campaign_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the exact checked-body prime-campaign tranches in DAG order."""

    variables = ("n", "p", "C", "e")
    prime_p = prime("p", tag="bpc_prime")
    index_gt_one = _lt_term("1", "n", tag="bpc_index", variables=variables)
    lower = _lt_term("n", "p", tag="bpc_lower", variables=variables)
    upper = _lt_term("p", "n + n", tag="bpc_upper", variables=variables)
    central = _central_binom_relation_term(
        "n", "C", tag="bpc_central", variables=variables
    )
    divides = _divides("p", "C", tag="bpc_central")
    valuation = power_valuation("p", "C", "e", tag="bpc_value")
    valuation_one = power_valuation_one("p", "C", tag="result")
    square_strict = _lt_term(
        "n + n", "p * p", tag="bpc_square", variables=variables
    )
    exponent_bound = _le_term("e", "1", tag="bpc_e_one", variables=variables)

    chain_variables = ("n", "k", "b", "c", "a", "p", "z", "d")
    singleton_entry = _beta_at_term(
        "b", "c", "0", "n", tag="bpc_singleton", variables=chain_variables
    )
    singleton_chain = _bertrand_chain_terms(
        "b", "c", "n", "0", tag="singleton", variables=chain_variables
    )
    old_chain = _bertrand_chain_terms(
        "b", "c", "n", "k", tag="old", variables=chain_variables
    )
    successor_chain = _bertrand_chain_terms(
        "z", "d", "n", "S k", tag="successor", variables=chain_variables
    )
    old_terminal = _beta_at_term(
        "b", "c", "k", "a", tag="bpc_old_terminal", variables=chain_variables
    )
    successor_terminal = _beta_at_term(
        "z",
        "d",
        "S k",
        "p",
        tag="bpc_successor_terminal",
        variables=chain_variables,
    )
    next_window = bertrand_window("a", "p", tag="next")
    initial_guard = _lt_term(
        "1", "n", tag="bpc_chain_initial", variables=chain_variables
    )
    terminal_guard = _lt_term(
        "1", "a", tag="bpc_chain_terminal", variables=chain_variables
    )
    next_guard = _lt_term(
        "1", "p", tag="bpc_chain_next", variables=chain_variables
    )
    transport_variables = (*chain_variables, "i", "v")
    transport_bound = _lt_term(
        "i", "S k", tag="bpc_transport_bound", variables=transport_variables
    )
    transport_old = _beta_at_term(
        "b", "c", "i", "v", tag="bpc_transport_old", variables=transport_variables
    )
    transport_new = _beta_at_term(
        "z", "d", "i", "v", tag="bpc_transport_new", variables=transport_variables
    )
    extension_data = (
        f"exists z d. (({successor_terminal}) /\\ "
        f"forall i v. ({transport_bound}) -> "
        f"({transport_old}) -> ({transport_new}))"
    )
    step_variables = (*chain_variables, "i", "u", "v")
    previous_old_step = _beta_at_term(
        "b", "c", "i", "u", tag="bpc_step_old", variables=step_variables
    )
    following_old_step = _beta_at_term(
        "b", "c", "S i", "v", tag="bpc_step_next", variables=step_variables
    )
    old_step_window = bertrand_window("u", "v", tag="old_step")
    old_step_data = (
        f"exists u v. (({previous_old_step}) /\\ "
        f"(({following_old_step}) /\\ ({old_step_window})))"
    )

    return (
        spec(
            BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM,
            "forall n p C. "
            f"({prime_p}) -> ({lower}) -> ({upper}) -> "
            f"({central}) -> ({divides})",
            ("lt_to_le", "choose_prime_divides_between"),
            (
                "intro n",
                "intro p",
                "intro C",
                "intro hprime",
                "intro hlower",
                "intro hupper",
                "intro hcentral",
                "specialize choose_prime_divides_between (n + n)",
                "specialize choose_prime_divides_between n",
                "specialize choose_prime_divides_between n",
                "specialize choose_prime_divides_between p",
                "specialize choose_prime_divides_between C",
                "apply choose_prime_divides_between",
                "refl",
                "exact hprime",
                "exact hlower",
                "exact hlower",
                "specialize lt_to_le p",
                "specialize lt_to_le (n + n)",
                "apply lt_to_le",
                "exact hupper",
                "exact hcentral",
            ),
            "Every prime strictly between n and 2n divides C(2n,n).",
        ),
        spec(
            BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE,
            f"forall n p. ({prime_p}) -> ({lower}) -> ({square_strict})",
            (
                "mul_lt_mul_right_nonzero",
                "mul_comm",
                "two_mul_eq_add_self",
                "prime_two_le",
                "mul_le_mul_right",
                "lt_of_lt_of_le",
            ),
            (
                "intro n",
                "intro p",
                "intro hprime",
                "intro hlower",
                "have hscaled : exists q. q + S (n * 2) = p * 2",
                "specialize mul_lt_mul_right_nonzero n",
                "specialize mul_lt_mul_right_nonzero p",
                "specialize mul_lt_mul_right_nonzero 2",
                "apply mul_lt_mul_right_nonzero",
                "exact hlower",
                "intro htwozero",
                "apply PA1",
                "exact htwozero",
                "have hn_double : n * 2 = n + n",
                "trans 2 * n",
                "apply mul_comm",
                "apply two_mul_eq_add_self",
                "have hp_double : p * 2 = p + p",
                "trans 2 * p",
                "apply mul_comm",
                "apply two_mul_eq_add_self",
                "rewrite hn_double at hscaled",
                "rewrite hp_double at hscaled",
                "have htwo : exists q. q + 2 = p",
                "specialize prime_two_le p",
                "apply prime_two_le",
                "exact hprime",
                "have hsquare_bound : exists q. q + (2 * p) = p * p",
                "specialize mul_le_mul_right 2",
                "specialize mul_le_mul_right p",
                "specialize mul_le_mul_right p",
                "apply mul_le_mul_right",
                "exact htwo",
                "have hleft : 2 * p = p + p",
                "apply two_mul_eq_add_self",
                "rewrite hleft at hsquare_bound",
                "specialize lt_of_lt_of_le (n + n)",
                "specialize lt_of_lt_of_le (p + p)",
                "specialize lt_of_lt_of_le (p * p)",
                "apply lt_of_lt_of_le",
                "exact hscaled",
                "exact hsquare_bound",
            ),
            "A prime above n has square strictly larger than 2n.",
        ),
        spec(
            BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE,
            "forall n p C e. "
            f"({index_gt_one}) -> ({prime_p}) -> ({lower}) -> "
            f"({central}) -> ({valuation}) -> ({exponent_bound})",
            (
                "lt_to_le",
                "pow_exists",
                "pow_two",
                BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE,
                "central_binom_prime_square_tail_valuation_le_one",
            ),
            (
                "intro n",
                "intro p",
                "intro C",
                "intro e",
                "intro hindex",
                "intro hprime",
                "intro hlower",
                "intro hcentral",
                "intro hvaluation",
                f"have hpower : exists s. ({_power_terms('p', '2', 's', tag='bpc_square_power')})",
                "specialize pow_exists p",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases hpower",
                "have hvalue : x = p * p",
                "specialize pow_two p",
                "specialize pow_two 2",
                "specialize pow_two x",
                "apply pow_two",
                "refl",
                "exact hpower_witness",
                f"have hsquare : {square_strict}",
                f"specialize {BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE} n",
                f"specialize {BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE} p",
                f"apply {BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE}",
                "exact hprime",
                "exact hlower",
                "have hstrict : exists q. q + S (n + n) = x",
                "rewrite hvalue",
                "exact hsquare",
                "specialize central_binom_prime_square_tail_valuation_le_one p",
                "specialize central_binom_prime_square_tail_valuation_le_one n",
                "specialize central_binom_prime_square_tail_valuation_le_one C",
                "specialize central_binom_prime_square_tail_valuation_le_one e",
                "specialize central_binom_prime_square_tail_valuation_le_one x",
                "apply central_binom_prime_square_tail_valuation_le_one",
                "exact hprime",
                "specialize lt_to_le 1",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hindex",
                "exact hcentral",
                "exact hvaluation",
                "exact hpower_witness",
                "exact hstrict",
            ),
            "Every central-binomial valuation at a Bertrand-window prime is at most one.",
        ),
        spec(
            BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO,
            "forall n p C e. "
            f"({prime_p}) -> ({lower}) -> ({upper}) -> "
            f"({central}) -> ({valuation}) -> ~(e = 0)",
            (
                "central_binom_positive",
                BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM,
                "prime_divisor_power_valuation_nonzero",
            ),
            (
                "intro n",
                "intro p",
                "intro C",
                "intro e",
                "intro hprime",
                "intro hlower",
                "intro hupper",
                "intro hcentral",
                "intro hvaluation",
                "have hpositive : exists a. C = S a",
                "specialize central_binom_positive n",
                "specialize central_binom_positive C",
                "apply central_binom_positive",
                "exact hcentral",
                "cases hpositive",
                "have hnonzero : ~(C = 0)",
                "intro hzero",
                "rewrite hpositive_witness at hzero",
                "apply PA1",
                "exact hzero",
                f"have hdivides : {divides}",
                f"specialize {BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM} n",
                f"specialize {BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM} p",
                f"specialize {BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM} C",
                f"apply {BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM}",
                "exact hprime",
                "exact hlower",
                "exact hupper",
                "exact hcentral",
                "intro hexponent_zero",
                "specialize prime_divisor_power_valuation_nonzero p",
                "specialize prime_divisor_power_valuation_nonzero C",
                "specialize prime_divisor_power_valuation_nonzero e",
                "apply prime_divisor_power_valuation_nonzero",
                "exact hprime",
                "exact hnonzero",
                "exact hvaluation",
                "exact hdivides",
                "exact hexponent_zero",
            ),
            "A Bertrand-window prime divides the positive central coefficient nontrivially.",
        ),
        spec(
            BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE,
            "forall n p C e. "
            f"({index_gt_one}) -> ({prime_p}) -> ({lower}) -> "
            f"({upper}) -> ({central}) -> ({valuation}) -> e = 1",
            (
                BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE,
                BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO,
                "one_le_of_ne_zero",
                "le_antisymm",
            ),
            (
                "intro n",
                "intro p",
                "intro C",
                "intro e",
                "intro hindex",
                "intro hprime",
                "intro hlower",
                "intro hupper",
                "intro hcentral",
                "intro hvaluation",
                f"have hupper_exponent : {exponent_bound}",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE} n",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE} p",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE} C",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE} e",
                f"apply {BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE}",
                "exact hindex",
                "exact hprime",
                "exact hlower",
                "exact hcentral",
                "exact hvaluation",
                "have hnonzero : ~(e = 0)",
                "intro hexponent_zero",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO} n",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO} p",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO} C",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO} e",
                f"apply {BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO}",
                "exact hprime",
                "exact hlower",
                "exact hupper",
                "exact hcentral",
                "exact hvaluation",
                "exact hexponent_zero",
                "specialize le_antisymm e",
                "specialize le_antisymm 1",
                "apply le_antisymm",
                "exact hupper_exponent",
                "specialize one_le_of_ne_zero e",
                "apply one_le_of_ne_zero",
                "exact hnonzero",
            ),
            "Every Bertrand-window prime has exact central-binomial valuation one.",
        ),
        spec(
            BERTRAND_WINDOW_CENTRAL_VALUATION_ONE,
            "forall n p C. "
            f"({index_gt_one}) -> ({prime_p}) -> ({lower}) -> "
            f"({upper}) -> ({central}) -> ({valuation_one})",
            (
                "central_binom_positive",
                "prime_power_valuation_exists",
                BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE,
            ),
            (
                "intro n",
                "intro p",
                "intro C",
                "intro hindex",
                "intro hprime",
                "intro hlower",
                "intro hupper",
                "intro hcentral",
                "have hpositive : exists a. C = S a",
                "specialize central_binom_positive n",
                "specialize central_binom_positive C",
                "apply central_binom_positive",
                "exact hcentral",
                "cases hpositive",
                "have hnonzero : ~(C = 0)",
                "intro hzero",
                "rewrite hpositive_witness at hzero",
                "apply PA1",
                "exact hzero",
                "specialize prime_power_valuation_exists p",
                "specialize prime_power_valuation_exists C",
                "have hvaluation_exists : exists e. "
                f"(((({prime_p}) /\\ ~(C = 0))) /\\ ({valuation}))",
                "apply prime_power_valuation_exists",
                "exact hprime",
                "exact hnonzero",
                "cases hvaluation_exists",
                "cases hvaluation_exists_witness",
                "have hexact : x1 = 1",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE} n",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE} p",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE} C",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE} x1",
                f"apply {BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE}",
                "exact hindex",
                "exact hprime",
                "exact hlower",
                "exact hupper",
                "exact hcentral",
                "exact hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "rewrite hexact at hvaluation_exists_witness_right",
                "exact hvaluation_exists_witness_right",
            ),
            "Every Bertrand-window prime has a witnessed literal valuation-one graph.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_DIVISOR_MULTIPLICITY_ONE_EXISTS,
            f"forall n. ({index_gt_one}) -> exists p C. "
            f"(({prime_p}) /\\ (({lower}) /\\ (({upper}) /\\ "
            f"(({central}) /\\ ({valuation_one})))))",
            (
                "bertrand_strict",
                "central_binom_exists",
                BERTRAND_WINDOW_CENTRAL_VALUATION_ONE,
            ),
            (
                "intro n",
                "intro hindex",
                "specialize bertrand_strict n",
                "have hprime_exists : exists p. "
                f"(({prime_p}) /\\ (({lower}) /\\ ({upper})))",
                "apply bertrand_strict",
                "exact hindex",
                "cases hprime_exists",
                "cases hprime_exists_witness",
                "cases hprime_exists_witness_right",
                "specialize central_binom_exists n",
                f"have hcentral_exists : exists C. ({central})",
                "exact central_binom_exists",
                "cases hcentral_exists",
                "exists x",
                "exists x1",
                "split",
                "exact hprime_exists_witness_left",
                "split",
                "exact hprime_exists_witness_right_left",
                "split",
                "exact hprime_exists_witness_right_right",
                "split",
                "exact hcentral_exists_witness",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_ONE} n",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_ONE} x",
                f"specialize {BERTRAND_WINDOW_CENTRAL_VALUATION_ONE} x1",
                f"apply {BERTRAND_WINDOW_CENTRAL_VALUATION_ONE}",
                "exact hindex",
                "exact hprime_exists_witness_left",
                "exact hprime_exists_witness_right_left",
                "exact hprime_exists_witness_right_right",
                "exact hcentral_exists_witness",
            ),
            "For every n>1, a prime in (n,2n) divides C(2n,n) exactly once.",
        ),
        spec(
            BERTRAND_CHAIN_SINGLETON_CODE_EXISTS,
            f"forall n. exists b c. ({singleton_entry})",
            ("beta_prefix_extend",),
            (
                "intro n",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend 0",
                "specialize beta_prefix_extend n",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "exact beta_prefix_extend_witness_witness_left",
            ),
            "Every initial natural has an exact witnessed singleton Gödel-beta code.",
        ),
        spec(
            BERTRAND_CHAIN_SINGLETON_EXISTS,
            f"forall n. exists b c. ({singleton_chain})",
            (
                BERTRAND_CHAIN_SINGLETON_CODE_EXISTS,
                "add_eq_zero_right",
            ),
            (
                "intro n",
                f"specialize {BERTRAND_CHAIN_SINGLETON_CODE_EXISTS} n",
                f"cases {BERTRAND_CHAIN_SINGLETON_CODE_EXISTS}",
                f"cases {BERTRAND_CHAIN_SINGLETON_CODE_EXISTS}_witness",
                "exists x",
                "exists x1",
                "split",
                f"exact {BERTRAND_CHAIN_SINGLETON_CODE_EXISTS}_witness_witness",
                "intro i",
                "intro hbound",
                "exfalso",
                "cases hbound",
                "have hsuccessor_zero : S i = 0",
                "specialize add_eq_zero_right x2",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hbound_witness",
                "apply PA1",
                "exact hsuccessor_zero",
            ),
            "A singleton beta code is a valid strict-Bertrand chain of zero steps.",
        ),
        spec(
            BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD,
            f"forall a p. ({terminal_guard}) -> ({next_window}) -> ({next_guard})",
            ("lt_trans",),
            (
                "intro a",
                "intro p",
                "intro hguard",
                "intro hwindow",
                "cases hwindow",
                "cases hwindow_right",
                "specialize lt_trans 1",
                "specialize lt_trans a",
                "specialize lt_trans p",
                "apply lt_trans",
                "exact hguard",
                "exact hwindow_right_left",
            ),
            "Every strict Bertrand successor preserves the initial 1<n domain guard.",
        ),
        spec(
            BERTRAND_CHAIN_PREFIX_EXTEND,
            "forall n k b c a p. "
            f"({old_chain}) -> ({old_terminal}) -> ({next_window}) -> "
            f"exists z d. (({successor_chain}) /\\ ({successor_terminal}))",
            (
                "beta_prefix_extend",
                "zero_le",
                "succ_le_succ",
                "le_refl",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro n",
                "intro k",
                "intro b",
                "intro c",
                "intro a",
                "intro p",
                "intro hchain",
                "intro hterminal",
                "intro hwindow",
                "cases hchain",
                f"have hextension : {extension_data}",
                "specialize beta_prefix_extend (S k)",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend p",
                "exact beta_prefix_extend",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "exists x",
                "exists x1",
                "split",
                "split",
                "specialize hextension_witness_witness_right 0",
                "specialize hextension_witness_witness_right n",
                "apply hextension_witness_witness_right",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ k",
                "apply succ_le_succ",
                "specialize zero_le k",
                "exact zero_le",
                "exact hchain_left",
                "intro i",
                "intro hbound",
                "have hsplit : i = k \/ exists gap. gap + S i = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hbound",
                "cases hsplit",
                "exists a",
                "exists p",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "specialize hextension_witness_witness_right k",
                "specialize hextension_witness_witness_right a",
                "apply hextension_witness_witness_right",
                "specialize le_refl (S k)",
                "exact le_refl",
                "exact hterminal",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hextension_witness_witness_left",
                "exact hwindow",
                f"have hold : {old_step_data}",
                "specialize hchain_right i",
                "apply hchain_right",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_right",
                "exists x2",
                "exists x3",
                "split",
                "specialize hextension_witness_witness_right i",
                "specialize hextension_witness_witness_right x2",
                "apply hextension_witness_witness_right",
                "exact hbound",
                "exact hold_witness_witness_left",
                "split",
                "specialize hextension_witness_witness_right (S i)",
                "specialize hextension_witness_witness_right x3",
                "apply hextension_witness_witness_right",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ k",
                "apply succ_le_succ",
                "exact hsplit_right",
                "exact hold_witness_witness_right_left",
                "exact hold_witness_witness_right_right",
                "exact hextension_witness_witness_left",
            ),
            "Appending a strict Bertrand successor recodes and preserves every prior chain edge.",
        ),
        spec(
            BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS,
            f"forall n k. ({initial_guard}) -> exists b c a. "
            f"(({old_chain}) /\\ (({old_terminal}) /\\ ({terminal_guard})))",
            (
                BERTRAND_CHAIN_SINGLETON_EXISTS,
                "bertrand_strict",
                BERTRAND_CHAIN_PREFIX_EXTEND,
                BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD,
            ),
            (
                "intro n",
                "induction k",
                "intro hguard",
                f"specialize {BERTRAND_CHAIN_SINGLETON_EXISTS} n",
                f"cases {BERTRAND_CHAIN_SINGLETON_EXISTS}",
                f"cases {BERTRAND_CHAIN_SINGLETON_EXISTS}_witness",
                "exists x",
                "exists x1",
                "exists n",
                "split",
                f"exact {BERTRAND_CHAIN_SINGLETON_EXISTS}_witness_witness",
                "split",
                f"cases {BERTRAND_CHAIN_SINGLETON_EXISTS}_witness_witness",
                f"exact {BERTRAND_CHAIN_SINGLETON_EXISTS}_witness_witness_left",
                "exact hguard",
                "intro hguard",
                "have hprevious : exists b c a. "
                f"(({old_chain}) /\\ (({old_terminal}) /\\ ({terminal_guard})))",
                "apply IH",
                "exact hguard",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                "cases hprevious_witness_witness_witness_right",
                "have hnext : exists p. "
                f"({bertrand_window('x2', 'p', tag='induction_next')})",
                "specialize bertrand_strict x2",
                "apply bertrand_strict",
                "exact hprevious_witness_witness_witness_right_right",
                "cases hnext",
                "have hextended : exists z d. "
                f"(({_bertrand_chain_terms('z', 'd', 'n', 'S k', tag='induction_new', variables=chain_variables)}) /\\ "
                f"({_beta_at_term('z', 'd', 'S k', 'x3', tag='bpc_induction_terminal', variables=(*chain_variables, 'x3'))}))",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} n",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} k",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} x",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} x1",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} x2",
                f"specialize {BERTRAND_CHAIN_PREFIX_EXTEND} x3",
                f"apply {BERTRAND_CHAIN_PREFIX_EXTEND}",
                "exact hprevious_witness_witness_witness_left",
                "exact hprevious_witness_witness_witness_right_left",
                "exact hnext_witness",
                "cases hextended",
                "cases hextended_witness",
                "cases hextended_witness_witness",
                "exists x4",
                "exists x5",
                "exists x3",
                "split",
                "exact hextended_witness_witness_left",
                "split",
                "exact hextended_witness_witness_right",
                f"specialize {BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD} x2",
                f"specialize {BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD} x3",
                f"apply {BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD}",
                "exact hprevious_witness_witness_witness_right_right",
                "exact hnext_witness",
            ),
            "Induction constructs arbitrary strict prime chains and their guarded terminal values.",
        ),
        spec(
            ITERATED_BERTRAND_PRIME_CHAIN_EXISTS,
            f"forall n k. ({initial_guard}) -> exists b c. ({old_chain})",
            (BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS,),
            (
                "intro n",
                "intro k",
                "intro hguard",
                f"specialize {BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS} n",
                f"specialize {BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS} k",
                "have hwitness : exists b c a. "
                f"(({old_chain}) /\\ (({old_terminal}) /\\ ({terminal_guard})))",
                f"apply {BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS}",
                "exact hguard",
                "cases hwitness",
                "cases hwitness_witness",
                "cases hwitness_witness_witness",
                "cases hwitness_witness_witness_witness",
                "exists x",
                "exists x1",
                "exact hwitness_witness_witness_witness_left",
            ),
            "Every n>1 and finite k admit an exact beta-coded chain of k strict Bertrand primes.",
        ),
    )


__all__ = [
    "BERTRAND_WINDOW_PRIME_DIVIDES_CENTRAL_BINOM",
    "BERTRAND_WINDOW_PRIME_SQUARE_EXCEEDS_DOUBLE",
    "BERTRAND_WINDOW_CENTRAL_VALUATION_AT_MOST_ONE",
    "BERTRAND_WINDOW_CENTRAL_VALUATION_NONZERO",
    "BERTRAND_WINDOW_CENTRAL_VALUATION_EQUALS_ONE",
    "BERTRAND_WINDOW_CENTRAL_VALUATION_ONE",
    "CENTRAL_BINOM_PRIME_DIVISOR_MULTIPLICITY_ONE_EXISTS",
    "BERTRAND_CHAIN_SINGLETON_CODE_EXISTS",
    "BERTRAND_CHAIN_SINGLETON_EXISTS",
    "BERTRAND_CHAIN_SUCCESSOR_PRESERVES_GUARD",
    "BERTRAND_CHAIN_PREFIX_EXTEND",
    "BERTRAND_CHAIN_PREFIX_TERMINAL_EXISTS",
    "ITERATED_BERTRAND_PRIME_CHAIN_EXISTS",
    "bertrand_chain",
    "bertrand_window",
    "make_bertrand_prime_campaign_candidate_theorems",
    "power_valuation_one",
]
