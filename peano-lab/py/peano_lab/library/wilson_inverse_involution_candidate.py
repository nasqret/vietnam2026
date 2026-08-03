"""Static extensional inverse-map candidates for the Wilson route.

The preceding Wilson candidate layers construct a beta-coded map whose
positions and decoded values are zero-based indices for the nonzero residues
``1,...,p-1``.  This module turns that pointwise data into soundness,
completeness, involution, injectivity, surjectivity, and fixed-point facts.

Every displayed relation is expanded by hygienic authoring helpers before it
reaches the unchanged first-order Peano parser.  The factory is deliberately
absent from the public theorem registry pending WMI discovery and a separate
receipt-pinned admission replay.
"""

from __future__ import annotations

from typing import Any, Callable

from .wilson_inverse_prefix_candidate import (
    beta_at,
    inverse_index,
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


def _binder(tag: str, variables: tuple[str, ...], stem: str) -> str:
    safe_tag = _identifier(tag, "binder tag")
    name = f"wii_{stem}_{safe_tag}"
    if name in variables:
        raise ValueError("generated inverse-involution binder captures an argument")
    return name


def successor_positive(index: str, *, tag: str) -> str:
    """Expand the controlled positivity statement ``0 < S index``."""

    variable = _identifier(index, "successor predecessor")
    gap = _binder(tag, (variable,), "positive_gap")
    return f"exists {gap}. {gap} + 1 = S {index}"


def successor_strictly_below(index: str, right: str, *, tag: str) -> str:
    """Expand the controlled strict inequality ``S index < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((index, "successor predecessor"), (right, "upper term"))
    )
    gap = _binder(tag, variables, "successor_gap")
    return f"exists {gap}. {gap} + S (S {index}) = {right}"


def make_wilson_inverse_involution_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered inverse-map and fixed-point candidates."""

    entry_prefix = inverse_prefix(
        "p", "n", "b", "c", "l", tag="entry_prefix"
    )
    entry_index_bound = strictly_below("i", "l", tag="entry_index_bound")
    entry_source = beta_at("b", "c", "i", "j", tag="entry_source")
    entry_result = inverse_index("p", "n", "i", "j", tag="entry_result")
    entry_stored_at = beta_at("b", "c", "i", "k", tag="entry_stored_at")
    entry_stored_inverse = inverse_index(
        "p", "n", "i", "k", tag="entry_stored_inverse"
    )
    entry_stored = (
        f"exists k. (({entry_stored_at}) /\\ ({entry_stored_inverse}))"
    )

    extensional_prefix = inverse_prefix(
        "p", "n", "b", "c", "l", tag="extensional_prefix"
    )
    extensional_index_bound = strictly_below(
        "i", "l", tag="extensional_index_bound"
    )
    extensional_source = inverse_index(
        "p", "n", "i", "j", tag="extensional_source"
    )
    extensional_result = beta_at(
        "b", "c", "i", "j", tag="extensional_result"
    )
    extensional_stored_at = beta_at(
        "b", "c", "i", "k", tag="extensional_stored_at"
    )
    extensional_stored_inverse = inverse_index(
        "p", "n", "i", "k", tag="extensional_stored_inverse"
    )
    extensional_stored = (
        f"exists k. (({extensional_stored_at}) /\\ "
        f"({extensional_stored_inverse}))"
    )

    involutive_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="involutive_prefix"
    )
    involutive_index_bound = strictly_below(
        "i", "n", tag="involutive_index_bound"
    )
    involutive_mate_bound = strictly_below(
        "j", "n", tag="involutive_mate_bound"
    )
    involutive_source = beta_at(
        "b", "c", "i", "j", tag="involutive_source"
    )
    involutive_forward = inverse_index(
        "p", "n", "i", "j", tag="involutive_forward"
    )
    involutive_reverse = inverse_index(
        "p", "n", "j", "i", tag="involutive_reverse"
    )
    involutive_back = beta_at(
        "b", "c", "j", "i", tag="involutive_back"
    )
    involutive_statement = (
        f"forall p n b c i j. p = S n -> ({involutive_prefix}) -> "
        f"({involutive_index_bound}) -> ({involutive_source}) -> "
        f"(({involutive_mate_bound}) /\\ ({involutive_back}))"
    )

    injective_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="injective_prefix"
    )
    injective_left_bound = strictly_below(
        "i", "n", tag="injective_left_bound"
    )
    injective_right_bound = strictly_below(
        "j", "n", tag="injective_right_bound"
    )
    injective_left_entry = beta_at(
        "b", "c", "i", "k", tag="injective_left_entry"
    )
    injective_right_entry = beta_at(
        "b", "c", "j", "k", tag="injective_right_entry"
    )
    injective_left_back_bound = strictly_below(
        "k", "n", tag="injective_left_back_bound"
    )
    injective_left_back = beta_at(
        "b", "c", "k", "i", tag="injective_left_back"
    )
    injective_right_back_bound = strictly_below(
        "k", "n", tag="injective_right_back_bound"
    )
    injective_right_back = beta_at(
        "b", "c", "k", "j", tag="injective_right_back"
    )

    surjective_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="surjective_prefix"
    )
    surjective_value_bound = strictly_below(
        "j", "n", tag="surjective_value_bound"
    )
    surjective_index_bound = strictly_below(
        "i", "n", tag="surjective_index_bound"
    )
    surjective_result_at = beta_at(
        "b", "c", "i", "j", tag="surjective_result_at"
    )
    surjective_forward_at = beta_at(
        "b", "c", "j", "i", tag="surjective_forward_at"
    )
    surjective_forward_inverse = inverse_index(
        "p", "n", "j", "i", tag="surjective_forward_inverse"
    )
    surjective_forward = (
        f"exists i. (({surjective_forward_at}) /\\ "
        f"({surjective_forward_inverse}))"
    )
    surjective_back_bound = strictly_below(
        "x", "n", tag="surjective_back_bound"
    )
    surjective_back_at = beta_at(
        "b", "c", "x", "j", tag="surjective_back_at"
    )

    fixed_prime = prime("p", tag="fixed_prime")
    fixed_prefix = inverse_prefix(
        "p", "n", "b", "c", "n", tag="fixed_prefix"
    )
    fixed_index_bound = strictly_below("i", "n", tag="fixed_index_bound")
    fixed_entry = beta_at("b", "c", "i", "i", tag="fixed_entry")
    fixed_inverse = inverse_index("p", "n", "i", "i", tag="fixed_inverse")
    fixed_positive = successor_positive("i", tag="fixed_positive")
    fixed_residue_bound = successor_strictly_below(
        "i", "p", tag="fixed_residue_bound"
    )

    return (
        spec(
            "inverse_prefix_entry_sound",
            f"forall p n b c l i j. ({entry_prefix}) -> "
            f"({entry_index_bound}) -> ({entry_source}) -> ({entry_result})",
            ("beta_at_unique",),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro j",
                "intro hprefix",
                "intro hi",
                "intro hat",
                f"have hstored : {entry_stored}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have heq : j = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hat",
                "exact hstored_witness_left",
                "rewrite heq",
                "rewrite heq",
                "exact hstored_witness_right",
            ),
            "Every decoded inverse-prefix entry satisfies its stored inverse relation.",
        ),
        spec(
            "inverse_prefix_extensional",
            f"forall p n b c l i j. p = S n -> ({extensional_prefix}) -> "
            f"({extensional_index_bound}) -> ({extensional_source}) -> "
            f"({extensional_result})",
            ("bounded_inverse_index_unique",),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro j",
                "intro hpn",
                "intro hprefix",
                "intro hi",
                "intro hidx",
                f"have hstored : {extensional_stored}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have heq : j = x",
                "specialize bounded_inverse_index_unique p",
                "specialize bounded_inverse_index_unique n",
                "specialize bounded_inverse_index_unique i",
                "specialize bounded_inverse_index_unique j",
                "specialize bounded_inverse_index_unique x",
                "apply bounded_inverse_index_unique",
                "exact hpn",
                "exact hidx",
                "exact hstored_witness_right",
                "rewrite heq",
                "rewrite heq",
                "exact hstored_witness_left",
            ),
            "A full inverse relation at a covered index is decoded by the prefix.",
        ),
        spec(
            "inverse_prefix_involutive",
            involutive_statement,
            (
                "inverse_prefix_entry_sound",
                "inverse_index_symmetric",
                "inverse_prefix_extensional",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro hpn",
                "intro hprefix",
                "intro hi",
                "intro hat",
                f"have hforward : {involutive_forward}",
                "specialize inverse_prefix_entry_sound p",
                "specialize inverse_prefix_entry_sound n",
                "specialize inverse_prefix_entry_sound b",
                "specialize inverse_prefix_entry_sound c",
                "specialize inverse_prefix_entry_sound n",
                "specialize inverse_prefix_entry_sound i",
                "specialize inverse_prefix_entry_sound j",
                "apply inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hat",
                f"have hreverse : {involutive_reverse}",
                "specialize inverse_index_symmetric p",
                "specialize inverse_index_symmetric n",
                "specialize inverse_index_symmetric i",
                "specialize inverse_index_symmetric j",
                "apply inverse_index_symmetric",
                "exact hforward",
                "cases hforward",
                "cases hforward_right",
                "split",
                "exact hforward_right_left",
                "specialize inverse_prefix_extensional p",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional b",
                "specialize inverse_prefix_extensional c",
                "specialize inverse_prefix_extensional n",
                "specialize inverse_prefix_extensional j",
                "specialize inverse_prefix_extensional i",
                "apply inverse_prefix_extensional",
                "exact hpn",
                "exact hprefix",
                "exact hforward_right_left",
                "exact hreverse",
            ),
            "Decoding an inverse mate and decoding again returns the source index.",
        ),
        spec(
            "inverse_prefix_injective",
            f"forall p n b c i j k. p = S n -> ({injective_prefix}) -> "
            f"({injective_left_bound}) -> ({injective_right_bound}) -> "
            f"({injective_left_entry}) -> ({injective_right_entry}) -> i = j",
            (
                "inverse_prefix_involutive",
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro k",
                "intro hpn",
                "intro hprefix",
                "intro hi",
                "intro hj",
                "intro hik",
                "intro hjk",
                f"have hinvolutive_left : {involutive_statement}",
                "exact inverse_prefix_involutive",
                f"have hinvolutive_right : {involutive_statement}",
                "exact inverse_prefix_involutive",
                f"have hki : (({injective_left_back_bound}) /\\ "
                f"({injective_left_back}))",
                "specialize hinvolutive_left p",
                "specialize hinvolutive_left n",
                "specialize hinvolutive_left b",
                "specialize hinvolutive_left c",
                "specialize hinvolutive_left i",
                "specialize hinvolutive_left k",
                "apply hinvolutive_left",
                "exact hpn",
                "exact hprefix",
                "exact hi",
                "exact hik",
                f"have hkj : (({injective_right_back_bound}) /\\ "
                f"({injective_right_back}))",
                "specialize hinvolutive_right p",
                "specialize hinvolutive_right n",
                "specialize hinvolutive_right b",
                "specialize hinvolutive_right c",
                "specialize hinvolutive_right j",
                "specialize hinvolutive_right k",
                "apply hinvolutive_right",
                "exact hpn",
                "exact hprefix",
                "exact hj",
                "exact hjk",
                "cases hki",
                "cases hkj",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique k",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "apply beta_at_unique",
                "exact hki_right",
                "exact hkj_right",
            ),
            "The decoded inverse map is injective on its full bounded prefix.",
        ),
        spec(
            "inverse_prefix_surjective",
            f"forall p n b c j. p = S n -> ({surjective_prefix}) -> "
            f"({surjective_value_bound}) -> exists i. "
            f"(({surjective_index_bound}) /\\ ({surjective_result_at}))",
            ("inverse_prefix_involutive",),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro j",
                "intro hpn",
                "intro hprefix",
                "intro hj",
                f"have hlookup : {surjective_prefix}",
                "exact hprefix",
                f"have hforward : {surjective_forward}",
                "specialize hlookup j",
                "apply hlookup",
                "exact hj",
                "cases hforward",
                "cases hforward_witness",
                f"have hback : (({surjective_back_bound}) /\\ "
                f"({surjective_back_at}))",
                "specialize inverse_prefix_involutive p",
                "specialize inverse_prefix_involutive n",
                "specialize inverse_prefix_involutive b",
                "specialize inverse_prefix_involutive c",
                "specialize inverse_prefix_involutive j",
                "specialize inverse_prefix_involutive x",
                "apply inverse_prefix_involutive",
                "exact hpn",
                "exact hprefix",
                "exact hj",
                "exact hforward_witness_left",
                "exists x",
                "exact hback",
            ),
            "Every bounded value is hit by the full decoded inverse map.",
        ),
        spec(
            "prime_inverse_prefix_fixed_cases",
            f"forall p n b c i. p = S n -> ({fixed_prime}) -> "
            f"({fixed_prefix}) -> ({fixed_index_bound}) -> ({fixed_entry}) -> "
            "i = 0 \\/ S i = n",
            (
                "inverse_prefix_entry_sound",
                "succ_le_succ",
                "prime_bounded_square_one_cases",
                "succ_injective",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hfixed",
                f"have hidx : {fixed_inverse}",
                "specialize inverse_prefix_entry_sound p",
                "specialize inverse_prefix_entry_sound n",
                "specialize inverse_prefix_entry_sound b",
                "specialize inverse_prefix_entry_sound c",
                "specialize inverse_prefix_entry_sound n",
                "specialize inverse_prefix_entry_sound i",
                "specialize inverse_prefix_entry_sound i",
                "apply inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hfixed",
                "cases hidx",
                "cases hidx_right",
                f"have hpositive : {fixed_positive}",
                "exists i",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                f"have hbounded : {fixed_residue_bound}",
                "rewrite hpn",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hidx_left",
                "have hcases : S i = 1 \\/ S i = n",
                "specialize prime_bounded_square_one_cases p",
                "specialize prime_bounded_square_one_cases n",
                "specialize prime_bounded_square_one_cases (S i)",
                "apply prime_bounded_square_one_cases",
                "exact hpn",
                "exact hp",
                "exact hpositive",
                "exact hbounded",
                "exact hidx_right_right",
                "cases hcases",
                "left",
                "specialize succ_injective i",
                "specialize succ_injective 0",
                "apply succ_injective",
                "exact hcases_left",
                "right",
                "exact hcases_right",
            ),
            "A fixed zero-based inverse index is zero or the last index.",
        ),
    )


__all__ = [
    "make_wilson_inverse_involution_candidate_theorems",
    "successor_positive",
    "successor_strictly_below",
]
