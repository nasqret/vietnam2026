"""Static residue-reindex candidates for the native Fermat route.

The five theorems in this module refine the multiplication-residue map into
the exact bounded, injective, aligned beta-coded reindexing needed by finite
product permutation invariance.  The readable relations are hygienic
authoring abbreviations only: every statement expands to the unchanged
first-order Peano language before it reaches the parser or kernel.

This module is deliberately absent from the public theorem registry until a
content-addressed WMI discovery replay and a separate receipt-pinned admission
replay both succeed.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import (
    beta_at_successor_value,
    index_map,
    index_map_at,
    not_divides,
    prime,
)
from .fermat_residue_product_candidate import range_one
from .fermat_scale_product_candidate import scale_mod_prefix
from .finite_fold_surface import beta_at
from .finite_permutation_theorems import bounded_prefix, injective_prefix
from .finite_product_reindex_support import aligned_prefix


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
    names = tuple(f"frr_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-reindex binder captures an argument")
    return names


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def successor_lift_prefix(
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise successor-lifting of one beta-coded prefix."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "length"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    index, value, gap = _binders(
        safe_tag,
        variables,
        ("index", "value", "gap"),
    )
    bound = f"exists {gap}. {gap} + S {index} = {length}"
    source = beta_at(
        source_code,
        source_scale,
        index,
        value,
        tag=f"frr_{safe_tag}_source",
    )
    target = beta_at_successor_value(
        target_code,
        target_scale,
        index,
        value,
        tag=f"frr_{safe_tag}_target",
    )
    return (
        f"forall {index} {value}. ({bound}) -> ({source}) -> ({target})"
    )


def bounded_entry_at(
    code: str,
    scale: str,
    index: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand one existential projection of finite-prefix boundedness."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (index, "index"),
            (length, "length"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    value, gap = _binders(safe_tag, variables, ("value", "gap"))
    entry = beta_at(code, scale, index, value, tag=f"frr_{safe_tag}_entry")
    bound = f"exists {gap}. {gap} + S {value} = {length}"
    return f"exists {value}. ({entry}) /\\ ({bound})"


def scaled_indices_mod(
    modulus: str,
    multiplier: str,
    left_index: str,
    right_index: str,
    *,
    tag: str,
) -> str:
    """Expand ``a*S(i) == a*S(k) (mod p)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (multiplier, "multiplier"),
            (left_index, "left index"),
            (right_index, "right index"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("scaled_left", "scaled_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{multiplier} * S {left_index} + {modulus} * {left_witness} = "
        f"{multiplier} * S {right_index} + {modulus} * {right_witness}"
    )


def successor_to_scaled_mod(
    modulus: str,
    residue_predecessor: str,
    multiplier: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand ``S(w) == a*S(k) (mod p)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (residue_predecessor, "residue predecessor"),
            (multiplier, "multiplier"),
            (index, "index"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("reverse_left", "reverse_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"S {residue_predecessor} + {modulus} * {left_witness} = "
        f"{multiplier} * S {index} + {modulus} * {right_witness}"
    )


def successor_indices_mod(
    modulus: str,
    left_index: str,
    right_index: str,
    *,
    tag: str,
) -> str:
    """Expand ``S(i) == S(k) (mod p)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (left_index, "left index"),
            (right_index, "right index"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("cancel_left", "cancel_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"S {left_index} + {modulus} * {left_witness} = "
        f"S {right_index} + {modulus} * {right_witness}"
    )


def successor_below(index: str, modulus: str, *, tag: str) -> str:
    """Expand ``S(index) < modulus`` without accepting a compound term."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((index, "index"), (modulus, "modulus"))
    )
    (gap,) = _binders(tag, variables, ("successor_bound",))
    return f"exists {gap}. {gap} + S (S {index}) = {modulus}"


def make_fermat_residue_reindex_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered residue-reindex candidate tranche."""

    map_n = index_map("r", "s", "n", "n", "p", "a", tag="bounded_map")
    bounded_n = bounded_prefix("r", "s", "n", tag="bounded_result")
    map_at_i = index_map_at("r", "s", "i", "n", "p", "a", tag="injective_i")
    map_at_k = index_map_at("r", "s", "k", "n", "p", "a", tag="injective_k")
    injective_n = injective_prefix("r", "s", "n", tag="injective_result")
    prime_p = prime("p", tag="injective_prime")
    nonzero_a = not_divides("p", "a", tag="injective_multiplier")
    reverse_k = successor_to_scaled_mod(
        "p", "value", "a", "k", tag="injective_reverse"
    )
    scaled_i_k = scaled_indices_mod(
        "p", "a", "i", "k", tag="injective_scaled"
    )
    canceled_i_k = successor_indices_mod(
        "p", "i", "k", tag="injective_canceled"
    )
    successor_i_below_p = successor_below("i", "p", tag="injective_i_bound")
    successor_k_below_p = successor_below("k", "p", tag="injective_k_bound")

    bounded_alignment = bounded_prefix("r", "s", "n", tag="aligned_bounded")
    range_alignment = range_one("b", "c", "n", tag="aligned_range")
    lift_alignment = successor_lift_prefix(
        "r", "s", "z", "d", "n", tag="aligned_lift"
    )
    aligned_n = aligned_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="aligned_result"
    )
    bounded_at_i = bounded_entry_at(
        "r", "s", "i", "n", tag="aligned_entry"
    )
    j_below_n = strictly_below("j", "n", tag="aligned_j_bound")
    target_at_successor_j = beta_at_successor_value(
        "z", "d", "i", "j", tag="aligned_target"
    )

    scale_map = index_map("r", "s", "n", "n", "p", "a", tag="scale_map")
    scale_range = range_one("b", "c", "n", tag="scale_range")
    scale_lift = successor_lift_prefix(
        "r", "s", "z", "d", "n", tag="scale_lift"
    )
    scale_n = scale_mod_prefix(
        "p", "a", "b", "c", "z", "d", "n", tag="scale_result"
    )
    scale_map_at_i = index_map_at(
        "r", "s", "i", "n", "p", "a", tag="scale_at_i"
    )
    target_at_successor_x = beta_at_successor_value(
        "z", "d", "i", "x", tag="scale_target"
    )

    package_map = index_map("r", "s", "n", "n", "p", "a", tag="package_map")
    package_lift = successor_lift_prefix(
        "x", "x1", "z", "d", "n", tag="package_lift"
    )
    package_bounded = bounded_prefix("x", "x1", "n", tag="package_bounded")
    package_injective = injective_prefix(
        "x", "x1", "n", tag="package_injective"
    )
    package_aligned = aligned_prefix(
        "x", "x1", "b", "c", "x2", "x3", "n", tag="package_aligned"
    )
    package_scale = scale_mod_prefix(
        "p", "a", "b", "c", "x2", "x3", "n", tag="package_scale"
    )
    package_prime = prime("p", tag="package_prime")
    package_nonzero_a = not_divides("p", "a", tag="package_multiplier")
    package_range = range_one("b", "c", "n", tag="package_range")

    return (
        spec(
            "fermat_index_map_bounded",
            f"forall r s n p a. ({map_n}) -> ({bounded_n})",
            (),
            (
                "intro r",
                "intro s",
                "intro n",
                "intro p",
                "intro a",
                "intro hmap",
                "intro i",
                "intro hi",
                f"have hentry : {index_map_at('r', 's', 'i', 'n', 'p', 'a', tag='bounded_at_i')}",
                "specialize hmap i",
                "apply hmap",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_right",
                "exists x",
                "split",
                "exact hentry_witness_right_left",
                "exact hentry_witness_left",
            ),
            "The canonical multiplication-residue index map is bounded.",
        ),
        spec(
            "prime_mul_index_map_injective",
            f"forall p n a r s. p = S n -> ({prime_p}) -> ({nonzero_a}) -> "
            f"({index_map('r', 's', 'n', 'n', 'p', 'a', tag='injective_map')}) -> "
            f"({injective_n})",
            (
                "beta_at_unique",
                "succ_le_succ",
                "mod_eq_symm",
                "mod_eq_trans",
                "prime_mod_cancel",
                "mod_eq_bounded_unique",
                "succ_injective",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro r",
                "intro s",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro hmap",
                "intro i",
                "intro k",
                "intro value",
                "intro hi",
                "intro hk",
                "intro hri",
                "intro hrk",
                f"have hmi : {map_at_i}",
                "specialize hmap i",
                "apply hmap",
                "exact hi",
                "cases hmi",
                "cases hmi_witness",
                "cases hmi_witness_right",
                f"have hmk : {map_at_k}",
                "specialize hmap k",
                "apply hmap",
                "exact hk",
                "cases hmk",
                "cases hmk_witness",
                "cases hmk_witness_right",
                "have hvalue_i : value = x",
                "specialize beta_at_unique r",
                "specialize beta_at_unique s",
                "specialize beta_at_unique i",
                "specialize beta_at_unique value",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hri",
                "exact hmi_witness_right_left",
                "have hvalue_k : value = x1",
                "specialize beta_at_unique r",
                "specialize beta_at_unique s",
                "specialize beta_at_unique k",
                "specialize beta_at_unique value",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hrk",
                "exact hmk_witness_right_left",
                "rewrite <- hvalue_i at hmi_witness_right_right",
                "rewrite <- hvalue_k at hmk_witness_right_right",
                f"have hreverse : {reverse_k}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (a * S k)",
                "specialize mod_eq_symm (S value)",
                "apply mod_eq_symm",
                "exact hmk_witness_right_right",
                f"have hscaled : {scaled_i_k}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (a * S i)",
                "specialize mod_eq_trans (S value)",
                "specialize mod_eq_trans (a * S k)",
                "apply mod_eq_trans",
                "exact hmi_witness_right_right",
                "exact hreverse",
                f"have hcancel : {canceled_i_k}",
                "specialize prime_mod_cancel p",
                "specialize prime_mod_cancel a",
                "specialize prime_mod_cancel (S i)",
                "specialize prime_mod_cancel (S k)",
                "apply prime_mod_cancel",
                "exact hp",
                "exact hnotdiv",
                "exact hscaled",
                f"have hibound : {successor_i_below_p}",
                "rewrite hpn",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hi",
                f"have hkbound : {successor_k_below_p}",
                "rewrite hpn",
                "specialize succ_le_succ (S k)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hk",
                "have hsucc : S i = S k",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique (S i)",
                "specialize mod_eq_bounded_unique (S k)",
                "apply mod_eq_bounded_unique",
                "exact hibound",
                "exact hkbound",
                "exact hcancel",
                "specialize succ_injective i",
                "specialize succ_injective k",
                "apply succ_injective",
                "exact hsucc",
            ),
            "Multiplication by a nonzero prime residue is injective on 0,...,p-2.",
        ),
        spec(
            "beta_successor_range_reindex_aligned",
            f"forall r s b c z d n. ({bounded_alignment}) -> "
            f"({range_alignment}) -> ({lift_alignment}) -> ({aligned_n})",
            (
                "beta_at_unique",
                "beta_range_one_entry_eq_succ",
            ),
            (
                "intro r",
                "intro s",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro hbounded",
                "intro hrange",
                "intro hlift",
                "intro i",
                "intro j",
                "intro value",
                "intro hi",
                "intro hmap",
                "intro hsource",
                f"have hbounded_i : {bounded_at_i}",
                "specialize hbounded i",
                "apply hbounded",
                "exact hi",
                "cases hbounded_i",
                "cases hbounded_i_witness",
                "have hjx : j = x",
                "specialize beta_at_unique r",
                "specialize beta_at_unique s",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hmap",
                "exact hbounded_i_witness_left",
                f"have hjbound : {j_below_n}",
                "rewrite hjx",
                "exact hbounded_i_witness_right",
                "have hvalue : value = S j",
                "specialize beta_range_one_entry_eq_succ b",
                "specialize beta_range_one_entry_eq_succ c",
                "specialize beta_range_one_entry_eq_succ n",
                "specialize beta_range_one_entry_eq_succ j",
                "specialize beta_range_one_entry_eq_succ value",
                "apply beta_range_one_entry_eq_succ",
                "exact hrange",
                "exact hjbound",
                "exact hsource",
                f"have htarget_succ : {target_at_successor_j}",
                "specialize hlift i",
                "specialize hlift j",
                "apply hlift",
                "exact hi",
                "exact hmap",
                "rewrite hvalue",
                "rewrite hvalue",
                "exact htarget_succ",
            ),
            "A bounded residue map aligns the range 1,...,n with its successor lift.",
        ),
        spec(
            "beta_successor_range_scale_mod",
            f"forall p n a r s b c z d. ({scale_map}) -> "
            f"({scale_range}) -> ({scale_lift}) -> ({scale_n})",
            (
                "beta_range_one_entry_eq_succ",
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro r",
                "intro s",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro hmap",
                "intro hrange",
                "intro hlift",
                "intro i",
                "intro source",
                "intro target",
                "intro hi",
                "intro hsource",
                "intro htarget",
                f"have hmi : {scale_map_at_i}",
                "specialize hmap i",
                "apply hmap",
                "exact hi",
                "cases hmi",
                "cases hmi_witness",
                "cases hmi_witness_right",
                "have hsource_value : source = S i",
                "specialize beta_range_one_entry_eq_succ b",
                "specialize beta_range_one_entry_eq_succ c",
                "specialize beta_range_one_entry_eq_succ n",
                "specialize beta_range_one_entry_eq_succ i",
                "specialize beta_range_one_entry_eq_succ source",
                "apply beta_range_one_entry_eq_succ",
                "exact hrange",
                "exact hi",
                "exact hsource",
                f"have htarget_succ : {target_at_successor_x}",
                "specialize hlift i",
                "specialize hlift x",
                "apply hlift",
                "exact hi",
                "exact hmi_witness_right_left",
                "have htarget_value : target = S x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique i",
                "specialize beta_at_unique target",
                "specialize beta_at_unique (S x)",
                "apply beta_at_unique",
                "exact htarget",
                "exact htarget_succ",
                "rewrite hsource_value",
                "rewrite htarget_value",
                "exact hmi_witness_right_right",
            ),
            "The range and its successor-lifted residue map are pointwise congruent after scaling.",
        ),
        spec(
            "prime_mul_residue_reindex_exists",
            "forall p n a b c. "
            f"p = S n -> ({package_prime}) -> ({package_nonzero_a}) -> "
            f"({package_range}) -> exists r s z d. "
            f"({bounded_prefix('r', 's', 'n', tag='package_result_bounded')}) /\\ "
            f"(({injective_prefix('r', 's', 'n', tag='package_result_injective')}) /\\ "
            f"(({aligned_prefix('r', 's', 'b', 'c', 'z', 'd', 'n', tag='package_result_aligned')}) /\\ "
            f"({scale_mod_prefix('p', 'a', 'b', 'c', 'z', 'd', 'n', tag='package_result_scale')})))",
            (
                "le_refl",
                "prime_mul_index_map_exists_up_to",
                "beta_successor_lift_exists",
                "fermat_index_map_bounded",
                "prime_mul_index_map_injective",
                "beta_successor_range_reindex_aligned",
                "beta_successor_range_scale_mod",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro hrange",
                f"have hmaps : exists r s. ({package_map})",
                "specialize prime_mul_index_map_exists_up_to n",
                "specialize prime_mul_index_map_exists_up_to n",
                "specialize prime_mul_index_map_exists_up_to p",
                "specialize prime_mul_index_map_exists_up_to a",
                "apply prime_mul_index_map_exists_up_to",
                "specialize le_refl n",
                "exact le_refl",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "cases hmaps",
                "cases hmaps_witness",
                f"have hlifts : exists z d. ({package_lift})",
                "specialize beta_successor_lift_exists x",
                "specialize beta_successor_lift_exists x1",
                "specialize beta_successor_lift_exists n",
                "exact beta_successor_lift_exists",
                "cases hlifts",
                "cases hlifts_witness",
                f"have hbounded : {package_bounded}",
                "specialize fermat_index_map_bounded x",
                "specialize fermat_index_map_bounded x1",
                "specialize fermat_index_map_bounded n",
                "specialize fermat_index_map_bounded p",
                "specialize fermat_index_map_bounded a",
                "apply fermat_index_map_bounded",
                "exact hmaps_witness_witness",
                f"have hinjective : {package_injective}",
                "specialize prime_mul_index_map_injective p",
                "specialize prime_mul_index_map_injective n",
                "specialize prime_mul_index_map_injective a",
                "specialize prime_mul_index_map_injective x",
                "specialize prime_mul_index_map_injective x1",
                "apply prime_mul_index_map_injective",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "exact hmaps_witness_witness",
                f"have haligned : {package_aligned}",
                "specialize beta_successor_range_reindex_aligned x",
                "specialize beta_successor_range_reindex_aligned x1",
                "specialize beta_successor_range_reindex_aligned b",
                "specialize beta_successor_range_reindex_aligned c",
                "specialize beta_successor_range_reindex_aligned x2",
                "specialize beta_successor_range_reindex_aligned x3",
                "specialize beta_successor_range_reindex_aligned n",
                "apply beta_successor_range_reindex_aligned",
                "exact hbounded",
                "exact hrange",
                "exact hlifts_witness_witness",
                f"have hscale : {package_scale}",
                "specialize beta_successor_range_scale_mod p",
                "specialize beta_successor_range_scale_mod n",
                "specialize beta_successor_range_scale_mod a",
                "specialize beta_successor_range_scale_mod x",
                "specialize beta_successor_range_scale_mod x1",
                "specialize beta_successor_range_scale_mod b",
                "specialize beta_successor_range_scale_mod c",
                "specialize beta_successor_range_scale_mod x2",
                "specialize beta_successor_range_scale_mod x3",
                "apply beta_successor_range_scale_mod",
                "exact hmaps_witness_witness",
                "exact hrange",
                "exact hlifts_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hbounded",
                "split",
                "exact hinjective",
                "split",
                "exact haligned",
                "exact hscale",
            ),
            "A nonzero multiplier modulo a prime induces a beta-coded residue reindexing.",
        ),
    )


__all__ = [
    "bounded_entry_at",
    "make_fermat_residue_reindex_candidate_theorems",
    "scaled_indices_mod",
    "strictly_below",
    "successor_below",
    "successor_indices_mod",
    "successor_lift_prefix",
    "successor_to_scaled_mod",
]
