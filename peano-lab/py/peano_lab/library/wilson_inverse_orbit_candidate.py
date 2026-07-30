"""Static nonfixed inverse-orbit candidates for the native Wilson route.

The beta-coded inverse map uses zero-based indices: position ``i`` denotes
the nonzero residue ``S i``.  This isolated layer proves that a decoded entry
whose source is neither endpoint cannot be fixed, and that its decoded mate
is neither endpoint either.

Every readable helper expands before parsing to the unchanged first-order
Peano language.  The factory is deliberately absent from the public theorem
registry pending WMI discovery and a separate receipt-pinned admission replay.
"""

from __future__ import annotations

from typing import Any, Callable

from .wilson_inverse_prefix_candidate import (
    beta_at,
    inverse_prefix,
    prime,
    strictly_below,
)


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


def _identifier_or_zero(value: str, label: str) -> str:
    if value == "0":
        return value
    return _identifier(value, label)


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"wio_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated inverse-orbit binder captures an argument")
    return names


def nonendpoint(index: str, bound: str) -> str:
    """Expand the zero-based assertion that ``index`` is not an endpoint."""

    checked_index = _identifier(index, "orbit index")
    checked_bound = _identifier(bound, "orbit bound")
    return f"(~({checked_index} = 0) /\\ ~((S {checked_index}) = {checked_bound}))"


def beta_at_zero_index(
    code: str,
    scale: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,0,value)`` for the controlled zero index."""

    checked_code = _identifier(code, "beta code")
    checked_scale = _identifier(scale, "beta scale")
    checked_value = _identifier_or_zero(value, "decoded beta value")
    variables = (checked_code, checked_scale)
    if checked_value != "0":
        variables += (checked_value,)
    height, quotient = _binders(
        tag,
        variables,
        ("beta_height", "beta_quotient"),
    )
    modulus = f"S ((S (0)) * {checked_scale})"
    return (
        f"((exists {height}. {height} + S ({checked_value}) = {modulus}) /\\ "
        f"exists {quotient}. {checked_code} = "
        f"{quotient} * {modulus} + ({checked_value}))"
    )


def make_wilson_inverse_orbit_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first two isolated nonfixed inverse-orbit candidates."""

    prime_p = prime("p", tag="orbit_prime")
    full_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="orbit_prefix"
    )
    source_bound = strictly_below("i", "n", tag="orbit_source_bound")
    source_entry = beta_at("b", "c", "i", "j", tag="orbit_source_entry")
    source_nonendpoint = nonendpoint("i", "n")
    source_fixed = beta_at("b", "c", "i", "i", tag="orbit_source_fixed")

    mate_bound = strictly_below("j", "n", tag="orbit_mate_bound")
    back_entry = beta_at("b", "c", "j", "i", tag="orbit_back_entry")
    orbit_back = f"(({mate_bound}) /\\ ({back_entry}))"
    mate_nonendpoint = nonendpoint("j", "n")

    zero_fixed = beta_at_zero_index("b", "c", "0", tag="orbit_zero_fixed")
    back_at_zero = beta_at_zero_index("b", "c", "i", tag="orbit_back_zero")
    last_fixed = beta_at("b", "c", "x", "x", tag="orbit_last_fixed")
    back_at_last = beta_at("b", "c", "x", "i", tag="orbit_back_last")

    return (
        spec(
            "prime_inverse_prefix_nonendpoint_not_fixed",
            f"forall p n b c i j. p = S n -> ({prime_p}) -> "
            f"({full_prefix}) -> ({source_bound}) -> ({source_entry}) -> "
            f"({source_nonendpoint}) -> ~(i = j)",
            ("prime_inverse_prefix_fixed_cases",),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hat",
                "intro hnonendpoint",
                "cases hnonendpoint",
                "intro heq",
                f"have hfixed : {source_fixed}",
                "rewrite <- heq at hat",
                "rewrite <- heq at hat",
                "exact hat",
                "have hcases : i = 0 \\/ S i = n",
                "specialize prime_inverse_prefix_fixed_cases p",
                "specialize prime_inverse_prefix_fixed_cases n",
                "specialize prime_inverse_prefix_fixed_cases b",
                "specialize prime_inverse_prefix_fixed_cases c",
                "specialize prime_inverse_prefix_fixed_cases i",
                "apply prime_inverse_prefix_fixed_cases",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hi",
                "exact hfixed",
                "cases hcases",
                "apply hnonendpoint_left",
                "exact hcases_left",
                "apply hnonendpoint_right",
                "exact hcases_right",
            ),
            "A decoded inverse entry from a nonendpoint source is not fixed.",
        ),
        spec(
            "prime_inverse_prefix_nonendpoint_mate",
            f"forall p n b c i j. p = S n -> ({prime_p}) -> "
            f"({full_prefix}) -> ({source_bound}) -> ({source_entry}) -> "
            f"({source_nonendpoint}) -> ({mate_nonendpoint})",
            (
                "prime_inverse_prefix_nonendpoint_not_fixed",
                "inverse_prefix_involutive",
                "prime_is_succ_succ",
                "succ_injective",
                "inverse_prefix_zero_fixed",
                "inverse_prefix_last_fixed",
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hat",
                "intro hnonendpoint",
                "have hnonfixed : ~(i = j)",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed p",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed n",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed b",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed c",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed i",
                "specialize prime_inverse_prefix_nonendpoint_not_fixed j",
                "intro hij",
                "apply prime_inverse_prefix_nonendpoint_not_fixed",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hi",
                "exact hat",
                "exact hnonendpoint",
                "exact hij",
                f"have horbit : {orbit_back}",
                "specialize inverse_prefix_involutive p",
                "specialize inverse_prefix_involutive n",
                "specialize inverse_prefix_involutive b",
                "specialize inverse_prefix_involutive c",
                "specialize inverse_prefix_involutive i",
                "specialize inverse_prefix_involutive j",
                "apply inverse_prefix_involutive",
                "exact hpn",
                "exact hprefix",
                "exact hi",
                "exact hat",
                "cases horbit",
                "have hsucc_shape : forall a d. S a = S d -> a = d",
                "exact succ_injective",
                "have hsucc_mate : forall a d. S a = S d -> a = d",
                "exact succ_injective",
                "have hprime_shape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hprime_shape",
                "have hnk : n = S x",
                "specialize hsucc_shape n",
                "specialize hsucc_shape (S x)",
                "apply hsucc_shape",
                "trans p",
                "symm",
                "exact hpn",
                "exact hprime_shape_witness",
                f"have hzero : {zero_fixed}",
                "specialize inverse_prefix_zero_fixed p",
                "specialize inverse_prefix_zero_fixed n",
                "specialize inverse_prefix_zero_fixed x",
                "specialize inverse_prefix_zero_fixed b",
                "specialize inverse_prefix_zero_fixed c",
                "apply inverse_prefix_zero_fixed",
                "exact hpn",
                "exact hnk",
                "exact hprefix",
                f"have hlast : {last_fixed}",
                "specialize inverse_prefix_last_fixed p",
                "specialize inverse_prefix_last_fixed n",
                "specialize inverse_prefix_last_fixed x",
                "specialize inverse_prefix_last_fixed b",
                "specialize inverse_prefix_last_fixed c",
                "apply inverse_prefix_last_fixed",
                "exact hpn",
                "exact hnk",
                "exact hprefix",
                "split",
                "intro hjzero",
                f"have hback_zero_raw : {back_entry}",
                "exact horbit_right",
                f"have hback_zero : {back_at_zero}",
                "rewrite hjzero at hback_zero_raw",
                "rewrite hjzero at hback_zero_raw",
                "exact hback_zero_raw",
                "have hi0 : i = 0",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique i",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact hback_zero",
                "exact hzero",
                "apply hnonfixed",
                "trans 0",
                "exact hi0",
                "symm",
                "exact hjzero",
                "intro hjlast",
                "have hjx : j = x",
                "specialize hsucc_mate j",
                "specialize hsucc_mate x",
                "apply hsucc_mate",
                "trans n",
                "exact hjlast",
                "exact hnk",
                f"have hback_last_raw : {back_entry}",
                "exact horbit_right",
                f"have hback_last : {back_at_last}",
                "rewrite hjx at hback_last_raw",
                "rewrite hjx at hback_last_raw",
                "exact hback_last_raw",
                "have hix : i = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique x",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hback_last",
                "exact hlast",
                "apply hnonfixed",
                "trans x",
                "exact hix",
                "symm",
                "exact hjx",
            ),
            "The decoded mate of a nonendpoint inverse index is also a nonendpoint.",
        ),
    )


__all__ = [
    "beta_at_zero_index",
    "make_wilson_inverse_orbit_candidate_theorems",
    "nonendpoint",
]
