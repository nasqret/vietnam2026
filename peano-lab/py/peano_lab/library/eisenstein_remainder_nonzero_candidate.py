"""Sound nonzero-remainder bridges for scaled Eisenstein entries.

The reusable core says that if ``p`` is prime, ``p`` does not divide ``q``,
``S i < p``, and ``q*S i = p*d+r``, then ``r`` is nonzero.  Notice that no
remainder upper bound is needed.  A distinct-prime wrapper derives the
nondivisibility assumption, and an odd-half wrapper derives ``S i < p`` from
an index bounded by the divisor's own half.

Bounding the index by the *other* prime's half is unsound.  The originally
suggested shape ``p=2*k+1``, ``q=2*h+1``, ``i<h`` has the counterexample
``p=3``, ``k=1``, ``q=7``, ``h=3``, ``i=2``: then
``q*S i = 21 = p*7+0``.  Accordingly, this module states no such wrapper.  Its
correct half-level endpoint assumes ``i<k``, where ``k`` is the half belonging
to the divisor ``p``; the half representation of ``q`` is irrelevant.

All strict bounds and primality predicates expand before parsing to ordinary
first-order PA.  The candidates are dependency-curried, unregistered, and
use no classical principle.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import prime


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'" for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"ern_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein-remainder binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def prime_nondivisor_scaled_remainder_data(
    divisor: str,
    multiplier: str,
    index: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand the weakest reusable assumptions implying nonzero remainder."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (divisor, "divisor"),
            (multiplier, "multiplier"),
            (index, "scaled index"),
            (quotient, "quotient"),
            (remainder, "remainder"),
        )
    )
    (factor,) = _binders(tag, variables, ("factor",))
    divisor_prime = prime(divisor, tag=f"remainder_nonzero_{tag}_prime")
    multiplier_nondivisible = (
        f"~(exists {factor}. {multiplier} = {divisor} * {factor})"
    )
    index_bound = _lt_term(
        f"S {index}",
        divisor,
        tag=f"{tag}_index_bound",
        variables=variables,
    )
    decomposition = (
        f"{multiplier} * S {index} = "
        f"{divisor} * {quotient} + {remainder}"
    )
    return (
        f"(({divisor_prime}) /\\ (({multiplier_nondivisible}) /\\ "
        f"(({index_bound}) /\\ {decomposition})))"
    )


def make_eisenstein_remainder_nonzero_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build generic, distinct-prime, and corrected odd-half candidates."""

    prime_p = prime("p", tag="remainder_nonzero_prime_p")
    prime_q = prime("q", tag="remainder_nonzero_prime_q")
    p_nondivides_q = (
        "~(exists factor. q = p * factor)"
    )
    index_below_p = _lt_term(
        "S i",
        "p",
        tag="remainder_nonzero_index_below_p",
        variables=("p", "q", "k", "i", "d", "r"),
    )
    own_half_bound = _lt_term(
        "i",
        "k",
        tag="remainder_nonzero_own_half_bound",
        variables=("p", "q", "k", "i", "d", "r"),
    )
    half_below_p = _lt_term(
        "k",
        "p",
        tag="remainder_nonzero_half_below_p",
        variables=("p", "q", "k", "i", "d", "r"),
    )
    decomposition = "q * S i = p * d + r"

    return (
        spec(
            "prime_nondivisor_bounded_scaled_remainder_nonzero",
            "forall p q i d r. "
            f"({prime_p}) -> ({p_nondivides_q}) -> ({index_below_p}) -> "
            f"{decomposition} -> ~(r = 0)",
            (
                "euclid_prime_dvd_product",
                "succ_ne_zero",
                "divisor_le_nonzero",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro d",
                "intro r",
                "intro hp",
                "intro hpq",
                "intro hip",
                "intro hdivision",
                "intro hr0",
                "have hmultiple : exists t. q * S i = p * t",
                "exists d",
                "trans p * d + r",
                "exact hdivision",
                "rewrite hr0",
                "apply PA3",
                "have hsplit : (exists u. q = p * u) \\/ exists v. S i = p * v",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product q",
                "specialize euclid_prime_dvd_product (S i)",
                "apply euclid_prime_dvd_product",
                "exact hp",
                "exact hmultiple",
                "cases hsplit",
                "apply hpq",
                "exact hsplit_left",
                "have hsi0 : ~(S i = 0)",
                "specialize succ_ne_zero i",
                "exact succ_ne_zero",
                "have hle : exists gap. gap + p = S i",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero (S i)",
                "apply divisor_le_nonzero",
                "exact hsi0",
                "exact hsplit_right",
                "specialize lt_not_le (S i)",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hip",
                "exact hle",
            ),
            "A bounded positive factor times a prime nondivisor cannot have zero remainder modulo that prime.",
        ),
        spec(
            "distinct_primes_bounded_scaled_remainder_nonzero",
            "forall p q i d r. "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
            f"({index_below_p}) -> {decomposition} -> ~(r = 0)",
            (
                "prime_divisor_eq_one_or_self",
                "prime_nondivisor_bounded_scaled_remainder_nonzero",
            ),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro d",
                "intro r",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hip",
                "intro hdivision",
                f"have hnotdiv : {p_nondivides_q}",
                "intro hdiv",
                "have hfactor : p = 1 \\/ q = p",
                "specialize prime_divisor_eq_one_or_self q",
                "specialize prime_divisor_eq_one_or_self p",
                "apply prime_divisor_eq_one_or_self",
                "exact hq",
                "exact hdiv",
                "cases hfactor",
                "cases hp",
                "apply hp_left",
                "exact hfactor_left",
                "apply hpq",
                "symm",
                "exact hfactor_right",
                "intro hr0",
                "specialize prime_nondivisor_bounded_scaled_remainder_nonzero p",
                "specialize prime_nondivisor_bounded_scaled_remainder_nonzero q",
                "specialize prime_nondivisor_bounded_scaled_remainder_nonzero i",
                "specialize prime_nondivisor_bounded_scaled_remainder_nonzero d",
                "specialize prime_nondivisor_bounded_scaled_remainder_nonzero r",
                "apply prime_nondivisor_bounded_scaled_remainder_nonzero",
                "exact hp",
                "exact hnotdiv",
                "exact hip",
                "exact hdivision",
                "exact hr0",
            ),
            "Distinct primes give the nondivisibility needed by the bounded scaled-remainder theorem.",
        ),
        spec(
            "distinct_primes_own_odd_half_scaled_remainder_nonzero",
            "forall p q k i d r. p = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
            f"({own_half_bound}) -> {decomposition} -> ~(r = 0)",
            (
                "odd_half_strictly_below_modulus",
                "lt_of_le_of_lt",
                "distinct_primes_bounded_scaled_remainder_nonzero",
            ),
            (
                "intro p",
                "intro q",
                "intro k",
                "intro i",
                "intro d",
                "intro r",
                "intro hpodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hik",
                "intro hdivision",
                "intro hr0",
                f"have hkp : {half_below_p}",
                "specialize odd_half_strictly_below_modulus p",
                "specialize odd_half_strictly_below_modulus k",
                "apply odd_half_strictly_below_modulus",
                "exact hpodd",
                f"have hip : {index_below_p}",
                "specialize lt_of_le_of_lt (S i)",
                "specialize lt_of_le_of_lt k",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hik",
                "exact hkp",
                "specialize distinct_primes_bounded_scaled_remainder_nonzero p",
                "specialize distinct_primes_bounded_scaled_remainder_nonzero q",
                "specialize distinct_primes_bounded_scaled_remainder_nonzero i",
                "specialize distinct_primes_bounded_scaled_remainder_nonzero d",
                "specialize distinct_primes_bounded_scaled_remainder_nonzero r",
                "apply distinct_primes_bounded_scaled_remainder_nonzero",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hip",
                "exact hdivision",
                "exact hr0",
            ),
            "An index below the divisor's own odd half has nonzero scaled remainder for a distinct prime multiplier.",
        ),
    )


__all__ = [
    "make_eisenstein_remainder_nonzero_candidate_theorems",
    "prime_nondivisor_scaled_remainder_data",
]
