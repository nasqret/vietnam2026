"""Static beta-coded inverse-prefix candidates for the Wilson route.

Decoded values are zero-based mate indices.  Thus entry ``j`` at position
``i`` represents the modular inverse relation
``S i * S j == 1 (mod p)``.  Every helper below expands immediately to the
unchanged first-order Peano language, and the three theorem specs remain
outside the public registry pending WMI discovery and receipt-pinned
admission.
"""

from __future__ import annotations

from typing import Any, Callable


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
    names = tuple(f"wip_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated inverse-prefix binder captures an argument")
    return names


def _strictly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    return _strictly_below_term(left, right, tag=tag, avoid=variables)


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the nonunit factor-pair definition."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("beta_height", "beta_quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def beta_at(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand the checked ``BetaAt(code,scale,index,value)`` convention."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "code"),
            (scale, "scale"),
            (index, "index"),
            (value, "decoded value"),
        )
    )
    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=tag,
        avoid=variables,
    )


def _inverse_index_term(
    modulus: str,
    bound: str,
    index: str,
    mate: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index_bound = _strictly_below_term(
        index,
        bound,
        tag=f"{tag}_index_bound",
        avoid=avoid,
    )
    mate_bound = _strictly_below_term(
        mate,
        bound,
        tag=f"{tag}_mate_bound",
        avoid=avoid,
    )
    left_witness, right_witness = _binders(
        f"{tag}_mod",
        avoid,
        ("mod_left", "mod_right"),
    )
    congruence = (
        f"exists {left_witness} {right_witness}. "
        f"((S {index}) * S {mate}) + {modulus} * {left_witness} = "
        f"1 + {modulus} * {right_witness}"
    )
    return f"({index_bound}) /\\ (({mate_bound}) /\\ ({congruence}))"


def inverse_index(
    modulus: str,
    bound: str,
    index: str,
    mate: str,
    *,
    tag: str,
) -> str:
    """Expand bounded zero-based modular inverse data ``InvIdx``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (bound, "index bound"),
            (index, "source index"),
            (mate, "mate index"),
        )
    )
    return _inverse_index_term(
        modulus,
        bound,
        index,
        mate,
        tag=tag,
        avoid=variables,
    )


def _inverse_prefix_term(
    modulus: str,
    bound: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, mate = _binders(tag, avoid, ("index", "mate"))
    nested_avoid = avoid + (index, mate)
    index_in_prefix = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_prefix_bound",
        avoid=nested_avoid,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        mate,
        tag=f"{tag}_decoded",
        avoid=nested_avoid,
    )
    inverse = _inverse_index_term(
        modulus,
        bound,
        index,
        mate,
        tag=f"{tag}_inverse",
        avoid=nested_avoid,
    )
    return (
        f"forall {index}. ({index_in_prefix}) -> exists {mate}. "
        f"(({decoded}) /\\ ({inverse}))"
    )


def inverse_prefix(
    modulus: str,
    bound: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand existential-total beta-coded inverse data ``InvPrefix``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (bound, "index bound"),
            (code, "code"),
            (scale, "scale"),
            (length, "prefix length"),
        )
    )
    return _inverse_prefix_term(
        modulus,
        bound,
        code,
        scale,
        length,
        tag=tag,
        avoid=variables,
    )


def inverse_prefix_successor(
    modulus: str,
    bound: str,
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand ``InvPrefix`` at the controlled length ``S predecessor``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (bound, "index bound"),
            (code, "code"),
            (scale, "scale"),
            (predecessor, "prefix predecessor"),
        )
    )
    return _inverse_prefix_term(
        modulus,
        bound,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        avoid=variables,
    )


def make_wilson_inverse_prefix_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the extension, bounded-existence, and full-prefix candidates."""

    extend_prime = prime("p", tag="extend_prime")
    extend_length_bound = strictly_below("l", "n", tag="extend_length")
    extend_before = inverse_prefix(
        "p", "n", "b", "c", "l", tag="extend_before"
    )
    extend_after = inverse_prefix_successor(
        "p", "n", "z", "d", "l", tag="extend_after"
    )
    extend_new_inverse = inverse_index(
        "p", "n", "l", "j", tag="extend_new_inverse"
    )
    extend_new_entry = beta_at(
        "x1", "x2", "l", "x", tag="extend_new_entry"
    )
    extend_old_entry = beta_at(
        "b", "c", "i", "j", tag="extend_old_entry"
    )
    extend_old_inverse = inverse_index(
        "p", "n", "i", "j", tag="extend_old_inverse"
    )
    extend_old_result = (
        f"exists j. (({extend_old_entry}) /\\ ({extend_old_inverse}))"
    )

    bounded_prime = prime("p", tag="bounded_prime")
    bounded_length = (
        "exists wip_weak_gap_bounded_length. "
        "wip_weak_gap_bounded_length + l = n"
    )
    bounded_result = inverse_prefix(
        "p", "n", "b", "c", "l", tag="bounded_result"
    )
    bounded_previous = inverse_prefix(
        "p", "n", "b", "c", "l", tag="bounded_previous"
    )
    bounded_successor = inverse_prefix_successor(
        "p", "n", "z", "d", "l", tag="bounded_successor"
    )

    full_prime = prime("p", tag="full_prime")
    full_result = inverse_prefix(
        "p", "n", "b", "c", "n", tag="full_result"
    )

    return (
        spec(
            "prime_inverse_prefix_extend",
            f"forall p n b c l. p = S n -> ({extend_prime}) -> "
            f"({extend_length_bound}) -> ({extend_before}) -> "
            f"exists z d. ({extend_after})",
            (
                "prime_inverse_index_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro hpn",
                "intro hp",
                "intro hln",
                "intro hprefix",
                f"have hnew : exists j. ({extend_new_inverse})",
                "specialize prime_inverse_index_exists p",
                "specialize prime_inverse_index_exists n",
                "specialize prime_inverse_index_exists l",
                "apply prime_inverse_index_exists",
                "exact hpn",
                "exact hp",
                "exact hln",
                "cases hnew",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend x",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x1",
                "exists x2",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists h. h + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                f"have hnew_entry : {extend_new_entry}",
                "exact beta_prefix_extend_witness_witness_left",
                "exact hnew_entry",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hnew_witness",
                f"have hold : {extend_old_result}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x3",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append one bounded zero-based inverse index to an inverse prefix.",
        ),
        spec(
            "prime_inverse_prefix_exists_bounded",
            f"forall p n l. p = S n -> ({bounded_prime}) -> "
            f"({bounded_length}) -> exists b c. ({bounded_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "lt_to_le",
                "prime_inverse_prefix_extend",
            ),
            (
                "intro p",
                "intro n",
                "induction l",
                "intro hpn",
                "intro hp",
                "intro hln",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro hpn",
                "intro hp",
                "intro hln",
                "have hprev_bound : exists h. h + l = n",
                "specialize lt_to_le l",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hln",
                f"have hprev : exists b c. ({bounded_previous})",
                "apply IH",
                "exact hpn",
                "exact hp",
                "exact hprev_bound",
                "cases hprev",
                "cases hprev_witness",
                f"have hnext : exists z d. ({bounded_successor})",
                "specialize prime_inverse_prefix_extend p",
                "specialize prime_inverse_prefix_extend n",
                "specialize prime_inverse_prefix_extend x",
                "specialize prime_inverse_prefix_extend x1",
                "specialize prime_inverse_prefix_extend l",
                "apply prime_inverse_prefix_extend",
                "exact hpn",
                "exact hp",
                "exact hln",
                "exact hprev_witness_witness",
                "cases hnext",
                "cases hnext_witness",
                "exists x2",
                "exists x3",
                "exact hnext_witness_witness",
            ),
            "Every length bounded by p-1 has a beta-coded inverse prefix.",
        ),
        spec(
            "prime_inverse_prefix_exists",
            f"forall p n. p = S n -> ({full_prime}) -> "
            f"exists b c. ({full_result})",
            (
                "le_refl",
                "prime_inverse_prefix_exists_bounded",
            ),
            (
                "intro p",
                "intro n",
                "intro hpn",
                "intro hp",
                "specialize prime_inverse_prefix_exists_bounded p",
                "specialize prime_inverse_prefix_exists_bounded n",
                "specialize prime_inverse_prefix_exists_bounded n",
                "apply prime_inverse_prefix_exists_bounded",
                "exact hpn",
                "exact hp",
                "specialize le_refl n",
                "exact le_refl",
            ),
            "A prime predecessor interval has a full beta-coded inverse map.",
        ),
    )


__all__ = [
    "beta_at",
    "inverse_index",
    "inverse_prefix",
    "inverse_prefix_successor",
    "make_wilson_inverse_prefix_candidate_theorems",
    "prime",
    "strictly_below",
]
