"""Conservative authoring surface for the quadratic-reciprocity campaign.

This module has no theorem authority and is not imported by the checked
library ladder.  Its helpers emit ordinary Peano Lab formula text containing
only equality, ``0``, ``S``, ``+``, ``*``, quantifiers, and logical
connectives.  The unchanged formula parser expands numerals and negation
before the unchanged kernel sees a target.

The helpers deliberately accept variable identifiers rather than arbitrary
term text.  That small interface makes binder capture auditable while the
campaign is still a prototype.  A future general macro layer must construct
syntax trees hygienically; it must not weaken this contract by interpolating
unparsed terms.
"""

from __future__ import annotations


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


def _binders(tag: str, variables: tuple[str, ...], stems: tuple[str, ...]) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"qr_{stem}_{safe_tag}" for stem in stems)
    if set(names) & set(variables):
        raise ValueError("generated quadratic-residue binder captures an argument")
    return names


def congruent_mod(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand ``left = right (mod modulus)`` as balanced natural equality."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (left, "left term"),
            (right, "right term"),
        )
    )
    u, v = _binders(tag, variables, ("u", "v"))
    return f"exists {u} {v}. {left} + {modulus} * {u} = {right} + {modulus} * {v}"


def _square_congruent(modulus: str, value: str, root: str, *, tag: str) -> str:
    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (value, "value"),
            (root, "square root"),
        )
    )
    u, v = _binders(tag, variables, ("u", "v"))
    return (
        f"exists {u} {v}. {root} * {root} + {modulus} * {u} = "
        f"{value} + {modulus} * {v}"
    )


def quadratic_residue(modulus: str, value: str, *, tag: str) -> str:
    """Expand the unbounded quadratic-residue relation ``QRes(modulus,value)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (value, "value"))
    )
    (x,) = _binders(tag, variables, ("x",))
    return f"exists {x}. {_square_congruent(modulus, value, x, tag=tag)}"


def bounded_quadratic_residue(modulus: str, value: str, *, tag: str) -> str:
    """Expand ``QRes`` with a canonical root strictly below the modulus."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (value, "value"))
    )
    x, h = _binders(tag, variables, ("x", "h"))
    return (
        f"exists {x}. (exists {h}. {h} + S {x} = {modulus}) /\\ "
        f"{_square_congruent(modulus, value, x, tag=tag)}"
    )


def _prime(value: str, *, tag: str) -> str:
    variable = _identifier(value, "prime candidate")
    a, b = _binders(tag, (variable,), ("factor_a", "factor_b"))
    return (
        f"(~({value} = 1) /\\ forall {a} {b}. {value} = {a} * {b} -> "
        f"{a} = 1 \\/ {b} = 1)"
    )


def _odd(value: str, *, tag: str) -> str:
    variable = _identifier(value, "odd candidate")
    (half,) = _binders(tag, (variable,), ("half",))
    return f"exists {half}. {value} = 2 * {half} + 1"


def _one_mod_four(value: str, *, tag: str) -> str:
    variable = _identifier(value, "residue candidate")
    (quotient,) = _binders(tag, (variable,), ("mod4",))
    return f"exists {quotient}. {value} = 4 * {quotient} + 1"


def _three_mod_four(value: str, *, tag: str) -> str:
    variable = _identifier(value, "residue candidate")
    (quotient,) = _binders(tag, (variable,), ("mod4",))
    return f"exists {quotient}. {value} = 4 * {quotient} + 3"


def _same_truth(left: str, right: str) -> str:
    return f"(({left}) /\\ ({right})) \\/ (~({left}) /\\ ~({right}))"


def _opposite_truth(left: str, right: str) -> str:
    return f"(({left}) /\\ ~({right})) \\/ (~({left}) /\\ ({right}))"


_Q_PQ = quadratic_residue("p", "q", tag="p_q")
_Q_QP = quadratic_residue("q", "p", tag="q_p")
_COMMON = (
    f"forall p q. {_prime('p', tag='prime_p')} -> "
    f"{_prime('q', tag='prime_q')} -> ~(p = q) -> "
    f"({_odd('p', tag='odd_p')}) -> ({_odd('q', tag='odd_q')}) -> "
)
_SAME_CASE = (
    f"({_one_mod_four('p', tag='one_p')}) \\/ "
    f"({_one_mod_four('q', tag='one_q')})"
)
_OPPOSITE_CASE = (
    f"({_three_mod_four('p', tag='three_p')}) /\\ "
    f"({_three_mod_four('q', tag='three_q')})"
)
_SAME_CONCLUSION = _same_truth(_Q_PQ, _Q_QP)
_OPPOSITE_CONCLUSION = _opposite_truth(_Q_PQ, _Q_QP)


QUADRATIC_RECIPROCITY_SAME_CASE = (
    f"{_COMMON}({_SAME_CASE}) -> ({_SAME_CONCLUSION})"
)
"""Distinct odd primes: a 1-mod-4 input makes the two residue facts agree."""


QUADRATIC_RECIPROCITY_OPPOSITE_CASE = (
    f"{_COMMON}({_OPPOSITE_CASE}) -> ({_OPPOSITE_CONCLUSION})"
)
"""Distinct 3-mod-4 odd primes: exactly one cross-residue fact holds."""


QUADRATIC_RECIPROCITY_COMBINED = (
    f"{_COMMON}((({_SAME_CASE}) -> ({_SAME_CONCLUSION})) /\\ "
    f"((({_OPPOSITE_CASE}) -> ({_OPPOSITE_CONCLUSION}))))"
)
"""The exact sign-free, two-case native quadratic-reciprocity endpoint."""


MOD_EQ_DECIDABLE_NONZERO = (
    "forall p a b. ~(p = 0) -> "
    f"({congruent_mod('p', 'a', 'b', tag='dec_yes')}) \\/ "
    f"~({congruent_mod('p', 'a', 'b', tag='dec_no')})"
)
"""Planned bridge: balanced congruence is decidable for nonzero modulus."""


_Q_UNBOUNDED = quadratic_residue("p", "a", tag="unbounded")
_Q_BOUNDED = bounded_quadratic_residue("p", "a", tag="bounded")


QUADRATIC_RESIDUE_BOUNDED_EQUIV = (
    f"forall p a. ~(p = 0) -> ((({_Q_UNBOUNDED}) -> ({_Q_BOUNDED})) /\\ "
    f"(({_Q_BOUNDED}) -> ({_Q_UNBOUNDED})))"
)
"""Planned reduction of an arbitrary square root to one below the modulus."""


_SEARCH_YES_X, _SEARCH_YES_H = _binders(
    "search_yes", ("B", "p", "a"), ("x", "bound")
)
_SEARCH_NO_X, _SEARCH_NO_H = _binders(
    "search_no", ("B", "p", "a"), ("x", "bound")
)
_SEARCH_YES_SQUARE = _square_congruent(
    "p", "a", _SEARCH_YES_X, tag="search_yes"
)
_SEARCH_NO_SQUARE = _square_congruent(
    "p", "a", _SEARCH_NO_X, tag="search_no"
)


QUADRATIC_RESIDUE_SEARCH_UP_TO = (
    "forall B p a. ~(p = 0) -> "
    f"((exists {_SEARCH_YES_X}. "
    f"(exists {_SEARCH_YES_H}. {_SEARCH_YES_H} + {_SEARCH_YES_X} = B) /\\ "
    f"({_SEARCH_YES_SQUARE})) \\/ "
    f"(forall {_SEARCH_NO_X}. "
    f"(exists {_SEARCH_NO_H}. {_SEARCH_NO_H} + {_SEARCH_NO_X} = B) -> "
    f"~({_SEARCH_NO_SQUARE})))"
)
"""Planned concrete search for a square root in the inclusive range x <= B."""


QUADRATIC_RESIDUE_BOUNDED_DECIDABLE_NONZERO = (
    f"forall p a. ~(p = 0) -> ({_Q_BOUNDED}) \\/ ~({_Q_BOUNDED})"
)
"""Planned constructive decision theorem for the bounded relation."""


QUADRATIC_RESIDUE_DECIDABLE_NONZERO = (
    f"forall p a. ~(p = 0) -> ({_Q_UNBOUNDED}) \\/ ~({_Q_UNBOUNDED})"
)
"""Planned constructive decision theorem used by the sign-free endpoint."""


SURFACE_FORMULAS = {
    "mod_eq_decidable_nonzero": MOD_EQ_DECIDABLE_NONZERO,
    "quadratic_residue_bounded_equiv": QUADRATIC_RESIDUE_BOUNDED_EQUIV,
    "quadratic_residue_search_up_to": QUADRATIC_RESIDUE_SEARCH_UP_TO,
    "quadratic_residue_bounded_decidable_nonzero": (
        QUADRATIC_RESIDUE_BOUNDED_DECIDABLE_NONZERO
    ),
    "quadratic_residue_decidable_nonzero": QUADRATIC_RESIDUE_DECIDABLE_NONZERO,
    "quadratic_reciprocity_same_case": QUADRATIC_RECIPROCITY_SAME_CASE,
    "quadratic_reciprocity_opposite_case": QUADRATIC_RECIPROCITY_OPPOSITE_CASE,
    "quadratic_reciprocity_combined": QUADRATIC_RECIPROCITY_COMBINED,
}
"""Closed expanded formulas whose parse and size are regression-tested."""


__all__ = [
    "MOD_EQ_DECIDABLE_NONZERO",
    "QUADRATIC_RECIPROCITY_COMBINED",
    "QUADRATIC_RECIPROCITY_OPPOSITE_CASE",
    "QUADRATIC_RECIPROCITY_SAME_CASE",
    "QUADRATIC_RESIDUE_BOUNDED_EQUIV",
    "QUADRATIC_RESIDUE_BOUNDED_DECIDABLE_NONZERO",
    "QUADRATIC_RESIDUE_DECIDABLE_NONZERO",
    "QUADRATIC_RESIDUE_SEARCH_UP_TO",
    "SURFACE_FORMULAS",
    "bounded_quadratic_residue",
    "congruent_mod",
    "quadratic_residue",
]
