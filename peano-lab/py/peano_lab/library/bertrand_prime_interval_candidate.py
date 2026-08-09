"""Constructive bounded prime-interval search for the Bertrand campaign.

The public helpers in this module are conservative surface notation only:
they expand immediately to the existing first-order language of Peano Lab.
In particular, ``prime_in_open_closed_interval(l, u, p)`` means

    Prime(p) /\ l < p /\ p <= u,

with primality, strict order, and weak order fully expanded.  The companion
``prime_free_open_closed_interval`` is positive data: it maps every candidate
in the interval to a refutation of primality.  This explicit negative
certificate is the constructive branch needed by the eventual Bertrand
argument; no double-negation elimination is used.

The candidate factory is deliberately isolated from the public registry.
Admission, channel enrollment, and documentation are separate review steps.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import at_most, prime, strictly_below


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binder(tag: str, variables: tuple[str, ...], stem: str) -> str:
    safe_tag = _identifier(tag, "binder tag")
    name = f"bpi_{stem}_{safe_tag}"
    if name in variables:
        raise ValueError("generated Bertrand interval binder captures an argument")
    return name


def prime_strictly_above(lower: str, value: str, *, tag: str) -> str:
    """Expand ``Prime(value) /\ lower < value`` in unchanged PA syntax."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((lower, "lower endpoint"), (value, "prime candidate"))
    )
    primality = prime(value, tag=f"bpi_{tag}_prime")
    lower_bound = strictly_below(lower, value, tag=f"bpi_{tag}_lower")
    return f"(({primality}) /\\ ({lower_bound}))"


def prime_in_open_closed_interval(
    lower: str,
    upper: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``Prime(value) /\ lower < value /\ value <= upper``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (lower, "lower endpoint"),
            (upper, "upper endpoint"),
            (value, "prime candidate"),
        )
    )
    primality = prime(value, tag=f"bpi_{tag}_prime")
    lower_bound = strictly_below(lower, value, tag=f"bpi_{tag}_lower")
    upper_bound = at_most(value, upper, tag=f"bpi_{tag}_upper")
    return f"(({primality}) /\\ (({lower_bound}) /\\ ({upper_bound})))"


def prime_interval_witness(lower: str, upper: str, *, tag: str) -> str:
    """Expand existence of a prime in the open-closed interval ``(l,u]``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((lower, "lower endpoint"), (upper, "upper endpoint"))
    )
    value = _binder(tag, variables, "value")
    interval = prime_in_open_closed_interval(
        lower,
        upper,
        value,
        tag=f"{tag}_interval",
    )
    return f"exists {value}. ({interval})"


def prime_free_open_closed_interval(lower: str, upper: str, *, tag: str) -> str:
    """Expand an explicit certificate that ``(lower, upper]`` has no prime."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((lower, "lower endpoint"), (upper, "upper endpoint"))
    )
    value = _binder(tag, variables, "value")
    primality = prime(value, tag=f"bpi_{tag}_prime")
    lower_bound = strictly_below(lower, value, tag=f"bpi_{tag}_lower")
    upper_bound = at_most(value, upper, tag=f"bpi_{tag}_upper")
    return f"forall {value}. (({lower_bound}) /\\ ({upper_bound})) -> ~({primality})"


def make_bertrand_prime_interval_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated B0 constructive prime-interval tranche."""

    above = prime_strictly_above("l", "p", tag="above_decidable")

    search_witness = prime_interval_witness("l", "u", tag="search_witness")
    search_exclusion = prime_free_open_closed_interval(
        "l", "u", tag="search_exclusion"
    )

    refute_witness = prime_interval_witness("l", "u", tag="refute_witness")
    refute_exclusion = prime_free_open_closed_interval(
        "l", "u", tag="refute_exclusion"
    )

    decide_witness = prime_interval_witness("l", "u", tag="decide_witness")
    decide_search_witness = prime_interval_witness(
        "l", "u", tag="search_witness"
    )
    decide_search_exclusion = prime_free_open_closed_interval(
        "l", "u", tag="search_exclusion"
    )
    decide_refute_witness = prime_interval_witness(
        "l", "u", tag="refute_witness"
    )
    decide_refute_exclusion = prime_free_open_closed_interval(
        "l", "u", tag="refute_exclusion"
    )

    return (
        spec(
            "prime_strictly_above_decidable",
            f"forall l p. ({above}) \\/ ~({above})",
            (
                "prime_decidable",
                "lt_trichotomy",
                "lt_to_le",
                "lt_not_le",
                "le_refl",
            ),
            (
                "intro l",
                "intro p",
                "specialize prime_decidable p",
                "cases prime_decidable",
                "specialize lt_trichotomy l",
                "specialize lt_trichotomy p",
                "cases lt_trichotomy",
                "right",
                "intro habove",
                "cases habove",
                "specialize lt_not_le p",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "rewrite lt_trichotomy_left at habove_right",
                "exact habove_right",
                "specialize le_refl p",
                "exact le_refl",
                "cases lt_trichotomy_right",
                "left",
                "split",
                "exact prime_decidable_left",
                "exact lt_trichotomy_right_left",
                "right",
                "intro habove",
                "cases habove",
                "specialize lt_not_le p",
                "specialize lt_not_le l",
                "apply lt_not_le",
                "exact lt_trichotomy_right_right",
                "specialize lt_to_le l",
                "specialize lt_to_le p",
                "apply lt_to_le",
                "exact habove_right",
                "right",
                "intro habove",
                "cases habove",
                "apply prime_decidable_right",
                "exact habove_left",
            ),
            "Being prime and strictly above a fixed lower endpoint is decidable.",
        ),
        spec(
            "bounded_prime_interval_search",
            f"forall l u. ({search_witness}) \\/ ({search_exclusion})",
            (
                "prime_nonzero",
                "le_zero",
                "prime_strictly_above_decidable",
                "le_refl",
                "le_succ",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
            ),
            (
                "intro l",
                "induction u",
                "right",
                "intro p",
                "intro hbounds",
                "cases hbounds",
                "intro hp",
                "specialize le_zero p",
                "have hzero : p = 0",
                "apply le_zero",
                "exact hbounds_right",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hzero",
                "specialize prime_strictly_above_decidable l",
                "specialize prime_strictly_above_decidable (S u)",
                "cases prime_strictly_above_decidable",
                "left",
                "exists S u",
                "cases prime_strictly_above_decidable_left",
                "split",
                "exact prime_strictly_above_decidable_left_left",
                "split",
                "exact prime_strictly_above_decidable_left_right",
                "specialize le_refl (S u)",
                "exact le_refl",
                "cases IH",
                "left",
                "cases IH_left",
                "exists x",
                "cases IH_left_witness",
                "cases IH_left_witness_right",
                "split",
                "exact IH_left_witness_left",
                "split",
                "exact IH_left_witness_right_left",
                "specialize le_succ x",
                "specialize le_succ u",
                "apply le_succ",
                "exact IH_left_witness_right_right",
                "right",
                "intro p",
                "intro hbounds",
                "cases hbounds",
                "intro hp",
                "specialize le_eq_or_lt p",
                "specialize le_eq_or_lt (S u)",
                "have hsplit : p = S u \\/ exists h. h + S p = S u",
                "apply le_eq_or_lt",
                "exact hbounds_right",
                "cases hsplit",
                "apply prime_strictly_above_decidable_right",
                "split",
                "rewrite hsplit_left at hp",
                "rewrite hsplit_left at hp",
                "exact hp",
                "rewrite hsplit_left at hbounds_left",
                "exact hbounds_left",
                "specialize IH_right p",
                "apply IH_right",
                "split",
                "exact hbounds_left",
                "specialize le_of_succ_le_succ p",
                "specialize le_of_succ_le_succ u",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "exact hp",
            ),
            "Bounded search returns a prime witness or an explicit prime-free interval certificate.",
        ),
        spec(
            "prime_interval_exclusion_refutes_witness",
            f"forall l u. ({refute_exclusion}) -> ~({refute_witness})",
            (),
            (
                "intro l",
                "intro u",
                "intro hexclusion",
                "intro hwitness",
                "cases hwitness",
                "cases hwitness_witness",
                "cases hwitness_witness_right",
                "specialize hexclusion x",
                "apply hexclusion",
                "split",
                "exact hwitness_witness_right_left",
                "exact hwitness_witness_right_right",
                "exact hwitness_witness_left",
            ),
            "An explicit prime-free interval certificate refutes every prime witness.",
        ),
        spec(
            "bounded_prime_interval_decidable",
            f"forall l u. ({decide_witness}) \\/ ~({decide_witness})",
            (
                "bounded_prime_interval_search",
                "prime_interval_exclusion_refutes_witness",
            ),
            (
                "intro l",
                "intro u",
                "specialize bounded_prime_interval_search l",
                "specialize bounded_prime_interval_search u",
                f"have hsearch : ({decide_search_witness}) \\/ ({decide_search_exclusion})",
                "exact bounded_prime_interval_search",
                "cases hsearch",
                "left",
                "exact hsearch_left",
                "right",
                "specialize prime_interval_exclusion_refutes_witness l",
                "specialize prime_interval_exclusion_refutes_witness u",
                f"have hrefute : ({decide_refute_exclusion}) -> ~({decide_refute_witness})",
                "exact prime_interval_exclusion_refutes_witness",
                "intro hwitness",
                "apply hrefute",
                "exact hsearch_right",
                "exact hwitness",
            ),
            "Existence of a prime in any finite open-closed interval is constructively decidable.",
        ),
    )


__all__ = [
    "make_bertrand_prime_interval_candidate_theorems",
    "prime_free_open_closed_interval",
    "prime_in_open_closed_interval",
    "prime_interval_witness",
    "prime_strictly_above",
]
