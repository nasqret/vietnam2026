"""Constructive orientation of Eisenstein half-rectangle lattice cells.

For distinct odd primes ``p = 2*h+1`` and ``q = 2*k+1``, no positive bounded
lattice point lies on the diagonal ``q*x = p*y``.  Euclid's lemma reduces a
hypothetical equality to ``p | q`` or ``p | x``; prime rigidity rules out the
first alternative and the strict half-range bound rules out the second.

The checked natural-order trichotomy then orients every cell strictly to one
side of the diagonal, with the opposite orientation constructively excluded.
The final relation quantifies over the entire ``h`` by ``k`` rectangle and is
the pointwise input a later two-dimensional indicator count needs.  The
current fold API has one-dimensional ``Sum`` and ``BitCount`` relations but no
reviewed rectangular indicator/double-sum relation, so this module stops at
that clean representation boundary.

All bounds and orientations expand to first-order PA before parsing.  No
division, rational comparison, pair type, finite set, or classical principle
is added, and these candidates remain outside the public registry.
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
        or not all(character.isalnum() or character in "_'" for character in value[1:])
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
    names = tuple(f"elo_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein-orientation binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def exclusive_lattice_cell_orientation(
    prime_p: str,
    prime_q: str,
    p_index: str,
    q_index: str,
    *,
    tag: str,
) -> str:
    """Expand exclusive comparison of ``q*(1+i)`` with ``p*(1+j)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (p_index, "first half index"),
            (q_index, "second half index"),
        )
    )
    left = f"{prime_q} * S {p_index}"
    right = f"{prime_p} * S {q_index}"
    left_lt = _lt_term(
        left,
        right,
        tag=f"{tag}_left",
        variables=variables,
    )
    right_lt = _lt_term(
        right,
        left,
        tag=f"{tag}_right",
        variables=variables,
    )
    return (
        f"((({left_lt}) /\\ ~({right_lt})) \/ "
        f"(({right_lt}) /\\ ~({left_lt})))"
    )


def half_rectangle_orientation(
    prime_p: str,
    prime_q: str,
    half_p: str,
    half_q: str,
    *,
    tag: str,
) -> str:
    """Expand exclusive orientation for every cell of the half rectangle."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (prime_p, "first prime"),
            (prime_q, "second prime"),
            (half_p, "first half"),
            (half_q, "second half"),
        )
    )
    p_index, q_index = _binders(
        tag, variables, ("p_index", "q_index")
    )
    owned = variables + (p_index, q_index)
    p_bound = _lt_term(
        p_index,
        half_p,
        tag=f"{tag}_p_bound",
        variables=owned,
    )
    q_bound = _lt_term(
        q_index,
        half_q,
        tag=f"{tag}_q_bound",
        variables=owned,
    )
    orientation = exclusive_lattice_cell_orientation(
        prime_p,
        prime_q,
        p_index,
        q_index,
        tag=f"{tag}_cell",
    )
    return (
        f"forall {p_index} {q_index}. ({p_bound}) -> ({q_bound}) -> "
        f"({orientation})"
    )


def make_eisenstein_lattice_orientation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build noncollision, exclusive cell, and rectangle-orientation specs."""

    prime_p = prime("p", tag="lattice_prime_p")
    prime_q = prime("q", tag="lattice_prime_q")
    i_bound = _lt_term(
        "i",
        "h",
        tag="lattice_i_bound",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    j_bound = _lt_term(
        "j",
        "k",
        tag="lattice_j_bound",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    i_below_p = _lt_term(
        "S i",
        "p",
        tag="lattice_i_below_p",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    half_below_p = _lt_term(
        "h",
        "p",
        tag="lattice_half_below_p",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    equality = "q * S i = p * S j"
    cell_orientation = exclusive_lattice_cell_orientation(
        "p", "q", "i", "j", tag="lattice_cell_result"
    )
    left_lt = _lt_term(
        "q * S i",
        "p * S j",
        tag="lattice_cell_result_left",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    right_lt = _lt_term(
        "p * S j",
        "q * S i",
        tag="lattice_cell_result_right",
        variables=("p", "q", "h", "k", "i", "j"),
    )
    rectangle_orientation = half_rectangle_orientation(
        "p", "q", "h", "k", tag="lattice_rectangle_result"
    )

    common_prefix = (
        "forall p q h k i j. p = 2 * h + 1 -> q = 2 * k + 1 -> "
        f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
        f"({i_bound}) -> ({j_bound}) -> "
    )

    return (
        spec(
            "distinct_odd_prime_half_products_ne",
            f"{common_prefix}~({equality})",
            (
                "odd_half_strictly_below_modulus",
                "lt_of_le_of_lt",
                "euclid_prime_dvd_product",
                "prime_divisor_eq_one_or_self",
                "succ_ne_zero",
                "divisor_le_nonzero",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro j",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hj",
                f"have hhalf : {half_below_p}",
                "specialize odd_half_strictly_below_modulus p",
                "specialize odd_half_strictly_below_modulus h",
                "apply odd_half_strictly_below_modulus",
                "exact hpodd",
                f"have hip : {i_below_p}",
                "specialize lt_of_le_of_lt (S i)",
                "specialize lt_of_le_of_lt h",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hi",
                "exact hhalf",
                "intro heq",
                "have hpdiv : exists t. q * S i = p * t",
                "exists S j",
                "exact heq",
                "have hsplit : (exists u. q = p * u) \/ exists v. S i = p * v",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product q",
                "specialize euclid_prime_dvd_product (S i)",
                "apply euclid_prime_dvd_product",
                "exact hp",
                "exact hpdiv",
                "cases hsplit",
                "have hfactor : p = 1 \/ q = p",
                "specialize prime_divisor_eq_one_or_self q",
                "specialize prime_divisor_eq_one_or_self p",
                "apply prime_divisor_eq_one_or_self",
                "exact hq",
                "exact hsplit_left",
                "cases hfactor",
                "cases hp",
                "apply hp_left",
                "exact hfactor_left",
                "apply hpq",
                "symm",
                "exact hfactor_right",
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
            "Distinct odd primes have no bounded positive point on q*x=p*y.",
        ),
        spec(
            "distinct_odd_prime_half_cell_oriented",
            f"{common_prefix}({cell_orientation})",
            (
                "distinct_odd_prime_half_products_ne",
                "lt_trichotomy",
                "lt_to_le",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro j",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hj",
                "have hne : ~(q * S i = p * S j)",
                "intro heq",
                "specialize distinct_odd_prime_half_products_ne p",
                "specialize distinct_odd_prime_half_products_ne q",
                "specialize distinct_odd_prime_half_products_ne h",
                "specialize distinct_odd_prime_half_products_ne k",
                "specialize distinct_odd_prime_half_products_ne i",
                "specialize distinct_odd_prime_half_products_ne j",
                "apply distinct_odd_prime_half_products_ne",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hj",
                "exact heq",
                "specialize lt_trichotomy (q * S i)",
                "specialize lt_trichotomy (p * S j)",
                "cases lt_trichotomy",
                "exfalso",
                "apply hne",
                "exact lt_trichotomy_left",
                "cases lt_trichotomy_right",
                "left",
                "split",
                "exact lt_trichotomy_right_left",
                "intro hreverse",
                "have hle : exists gap. gap + (p * S j) = q * S i",
                "specialize lt_to_le (p * S j)",
                "specialize lt_to_le (q * S i)",
                "apply lt_to_le",
                "exact hreverse",
                "specialize lt_not_le (q * S i)",
                "specialize lt_not_le (p * S j)",
                "apply lt_not_le",
                "exact lt_trichotomy_right_left",
                "exact hle",
                "right",
                "split",
                "exact lt_trichotomy_right_right",
                "intro hreverse",
                "have hle : exists gap. gap + (q * S i) = p * S j",
                "specialize lt_to_le (q * S i)",
                "specialize lt_to_le (p * S j)",
                "apply lt_to_le",
                "exact hreverse",
                "specialize lt_not_le (p * S j)",
                "specialize lt_not_le (q * S i)",
                "apply lt_not_le",
                "exact lt_trichotomy_right_right",
                "exact hle",
            ),
            "Every bounded half-rectangle cell has one exclusive orientation.",
        ),
        spec(
            "distinct_odd_prime_half_rectangle_oriented",
            "forall p q h k. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
            f"({rectangle_orientation})",
            ("distinct_odd_prime_half_cell_oriented",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro i",
                "intro j",
                "intro hi",
                "intro hj",
                "specialize distinct_odd_prime_half_cell_oriented p",
                "specialize distinct_odd_prime_half_cell_oriented q",
                "specialize distinct_odd_prime_half_cell_oriented h",
                "specialize distinct_odd_prime_half_cell_oriented k",
                "specialize distinct_odd_prime_half_cell_oriented i",
                "specialize distinct_odd_prime_half_cell_oriented j",
                "apply distinct_odd_prime_half_cell_oriented",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hj",
            ),
            "The full h-by-k half rectangle is constructively oriented.",
        ),
    )


__all__ = [
    "exclusive_lattice_cell_orientation",
    "half_rectangle_orientation",
    "make_eisenstein_lattice_orientation_candidate_theorems",
]
