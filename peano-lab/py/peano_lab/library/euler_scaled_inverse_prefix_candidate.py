"""Isolated beta-prefix candidates for Euler's scaled inverse map.

At zero-based position ``i`` the decoded value ``y`` represents the actual
unit residue ``S i`` and satisfies ``(S i) * y == a (mod p)``.  This is the
finite bridge between the pointwise scaled-inverse API and the fixed-point-free
pairing needed by Euler's criterion.  All helpers expand to unchanged native
first-order PA; nothing is registered pending recursive WMI review.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import (
    _balanced_mod,
    _identifier,
    prime,
)
from .finite_fold_surface import beta_at


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"esip_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Euler scaled-prefix binder captures an argument")
    return names


def _strictly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _scaled_inverse_term(
    modulus: str,
    target: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    left_bound = _strictly_below_term(
        left,
        modulus,
        tag=f"{tag}_left_bound",
        variables=variables,
    )
    right_bound = _strictly_below_term(
        right,
        modulus,
        tag=f"{tag}_right_bound",
        variables=variables,
    )
    congruence = _balanced_mod(
        modulus,
        f"({left}) * {right}",
        target,
        variables=variables,
        tag=f"{tag}_mod",
    )
    left_unit = f"(~(({left}) = 0) /\\ ({left_bound}))"
    right_unit = f"(~({right} = 0) /\\ ({right_bound}))"
    return f"(({left_unit}) /\\ (({right_unit}) /\\ ({congruence})))"


def _scaled_inverse_index_term(
    modulus: str,
    target: str,
    bound: str,
    index: str,
    mate: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index_bound = _strictly_below_term(
        index,
        bound,
        tag=f"{tag}_index_bound",
        variables=variables,
    )
    scaled = _scaled_inverse_term(
        modulus,
        target,
        f"S {index}",
        mate,
        tag=f"{tag}_scaled",
        variables=variables,
    )
    return f"({index_bound}) /\\ ({scaled})"


def scaled_inverse_index(
    modulus: str,
    target: str,
    bound: str,
    index: str,
    mate: str,
    *,
    tag: str,
) -> str:
    """Expand one zero-based source/actual-value scaled-inverse entry."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (target, "target"),
            (bound, "index bound"),
            (index, "source index"),
            (mate, "decoded mate"),
        )
    )
    modulus, target, bound, index, mate = variables
    return _scaled_inverse_index_term(
        modulus,
        target,
        bound,
        index,
        mate,
        tag=tag,
        variables=variables,
    )


def _scaled_inverse_prefix_term(
    modulus: str,
    target: str,
    bound: str,
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, mate = _binders(tag, variables, ("index", "mate"))
    nested = variables + (index, mate)
    prefix_bound = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_prefix_bound",
        variables=nested,
    )
    entry = beta_at(code, scale, index, mate, tag=f"esip_{tag}_entry")
    relation = _scaled_inverse_index_term(
        modulus,
        target,
        bound,
        index,
        mate,
        tag=f"{tag}_relation",
        variables=nested,
    )
    return (
        f"forall {index}. ({prefix_bound}) -> exists {mate}. "
        f"(({entry}) /\\ ({relation}))"
    )


def scaled_inverse_prefix(
    modulus: str,
    target: str,
    bound: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand a beta-coded prefix of the scaled inverse map."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (target, "target"),
            (bound, "index bound"),
            (code, "code"),
            (scale, "scale"),
            (length, "prefix length"),
        )
    )
    modulus, target, bound, code, scale, length = variables
    return _scaled_inverse_prefix_term(
        modulus,
        target,
        bound,
        code,
        scale,
        length,
        tag=tag,
        variables=variables,
    )


def scaled_inverse_prefix_successor(
    modulus: str,
    target: str,
    bound: str,
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand a scaled-inverse prefix at the controlled length `S l`."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (target, "target"),
            (bound, "index bound"),
            (code, "code"),
            (scale, "scale"),
            (predecessor, "prefix predecessor"),
        )
    )
    modulus, target, bound, code, scale, predecessor = variables
    return _scaled_inverse_prefix_term(
        modulus,
        target,
        bound,
        code,
        scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def make_euler_scaled_inverse_prefix_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build extension, bounded existence, and full-prefix candidates."""

    extend_prime = prime("p", tag="esip_extend_prime")
    target_bound = _strictly_below_term(
        "a",
        "p",
        tag="extend_target_bound",
        variables=("p", "a", "n", "b", "c", "l"),
    )
    length_bound = _strictly_below_term(
        "l",
        "n",
        tag="extend_length_bound",
        variables=("p", "a", "n", "b", "c", "l"),
    )
    before = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="extend_before"
    )
    after = scaled_inverse_prefix(
        "p", "a", "n", "z", "d", "sl", tag="extend_after"
    )
    source_bound = _strictly_below_term(
        "S l",
        "p",
        tag="extend_source_bound",
        variables=("p", "a", "n", "b", "c", "l"),
    )
    new_scaled = _scaled_inverse_term(
        "p",
        "a",
        "S l",
        "j",
        tag="extend_new_scaled",
        variables=("p", "a", "n", "b", "c", "l", "j"),
    )
    new_entry = beta_at("x1", "x2", "l", "x", tag="esip_extend_new_entry")
    old_entry = beta_at("b", "c", "i", "j", tag="esip_extend_old_entry")
    old_relation = scaled_inverse_index(
        "p", "a", "n", "i", "j", tag="extend_old_relation"
    )
    old_result = f"exists j. (({old_entry}) /\\ ({old_relation}))"

    bounded_prime = prime("p", tag="esip_bounded_prime")
    bounded_target_bound = _strictly_below_term(
        "a",
        "p",
        tag="bounded_target_bound",
        variables=("p", "a", "n", "l"),
    )
    bounded_length = "exists esip_weak_gap_bounded. esip_weak_gap_bounded + l = n"
    bounded_result = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="bounded_result"
    )
    bounded_previous = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="bounded_previous"
    )
    bounded_successor = scaled_inverse_prefix_successor(
        "p", "a", "n", "z", "d", "l", tag="bounded_successor"
    )

    full_prime = prime("p", tag="esip_full_prime")
    full_target_bound = _strictly_below_term(
        "a",
        "p",
        tag="full_target_bound",
        variables=("p", "a", "n"),
    )
    full_result = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "n", tag="full_result"
    )

    return (
        spec(
            "prime_scaled_inverse_prefix_extend",
            f"forall p a n b c l sl. p = S n -> ({extend_prime}) -> "
            f"~(a = 0) -> ({target_bound}) -> ({length_bound}) -> "
            f"sl = S l -> ({before}) -> exists z d. ({after})",
            (
                "succ_ne_zero",
                "succ_le_succ",
                "prime_scaled_inverse_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro sl",
                "intro hpn",
                "intro hp",
                "intro ha0",
                "intro hap",
                "intro hln",
                "intro hsl",
                "intro hprefix",
                f"have hsource_bound : {source_bound}",
                "rewrite hpn",
                "specialize succ_le_succ (S l)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hln",
                f"have hnew : exists j. ({new_scaled})",
                "specialize prime_scaled_inverse_exists p",
                "specialize prime_scaled_inverse_exists a",
                "specialize prime_scaled_inverse_exists (S l)",
                "apply prime_scaled_inverse_exists",
                "exact hp",
                "exact ha0",
                "exact hap",
                "specialize succ_ne_zero l",
                "exact succ_ne_zero",
                "exact hsource_bound",
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
                "rewrite hsl at hi",
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
                "exact beta_prefix_extend_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "exact hln",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hnew_witness",
                f"have hold : {old_result}",
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
            "Append one actual scaled-inverse value to a zero-based source prefix.",
        ),
        spec(
            "prime_scaled_inverse_prefix_exists_bounded",
            f"forall p a n l. p = S n -> ({bounded_prime}) -> ~(a = 0) -> "
            f"({bounded_target_bound}) -> ({bounded_length}) -> "
            f"exists b c. ({bounded_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "lt_to_le",
                "prime_scaled_inverse_prefix_extend",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "induction l",
                "intro hpn",
                "intro hp",
                "intro ha0",
                "intro hap",
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
                "intro ha0",
                "intro hap",
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
                "exact ha0",
                "exact hap",
                "exact hprev_bound",
                "cases hprev",
                "cases hprev_witness",
                f"have hnext : exists z d. ({bounded_successor})",
                "specialize prime_scaled_inverse_prefix_extend p",
                "specialize prime_scaled_inverse_prefix_extend a",
                "specialize prime_scaled_inverse_prefix_extend n",
                "specialize prime_scaled_inverse_prefix_extend x",
                "specialize prime_scaled_inverse_prefix_extend x1",
                "specialize prime_scaled_inverse_prefix_extend l",
                "specialize prime_scaled_inverse_prefix_extend (S l)",
                "apply prime_scaled_inverse_prefix_extend",
                "exact hpn",
                "exact hp",
                "exact ha0",
                "exact hap",
                "exact hln",
                "refl",
                "exact hprev_witness_witness",
                "cases hnext",
                "cases hnext_witness",
                "exists x2",
                "exists x3",
                "exact hnext_witness_witness",
            ),
            "Every bounded predecessor length has a beta-coded scaled-inverse prefix.",
        ),
        spec(
            "prime_scaled_inverse_prefix_exists",
            f"forall p a n. p = S n -> ({full_prime}) -> ~(a = 0) -> "
            f"({full_target_bound}) -> exists b c. ({full_result})",
            (
                "le_refl",
                "prime_scaled_inverse_prefix_exists_bounded",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro hpn",
                "intro hp",
                "intro ha0",
                "intro hap",
                "specialize prime_scaled_inverse_prefix_exists_bounded p",
                "specialize prime_scaled_inverse_prefix_exists_bounded a",
                "specialize prime_scaled_inverse_prefix_exists_bounded n",
                "specialize prime_scaled_inverse_prefix_exists_bounded n",
                "apply prime_scaled_inverse_prefix_exists_bounded",
                "exact hpn",
                "exact hp",
                "exact ha0",
                "exact hap",
                "specialize le_refl n",
                "exact le_refl",
            ),
            "A prime predecessor interval has a full beta-coded scaled-inverse map.",
        ),
    )


__all__ = [
    "make_euler_scaled_inverse_prefix_candidate_theorems",
    "scaled_inverse_index",
    "scaled_inverse_prefix",
    "scaled_inverse_prefix_successor",
]
