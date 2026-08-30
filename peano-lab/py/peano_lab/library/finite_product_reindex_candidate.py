"""Isolated candidate for exact finite-product permutation invariance.

The beta code ``(r,s)`` maps each target position to a source position.  Its
boundedness and injectivity make it a finite permutation by the checked
pigeonhole theorem.  Pointwise alignment then says that the target factor at
``i`` is the source factor at the decoded position.  No relation defined in
this authoring module reaches the parser or kernel: every public contract is
expanded into ordinary first-order PA.

This file is deliberately not imported by the public theorem registry while
the candidate proof is being audited.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation, product_successor_relation
from .finite_permutation_theorems import (
    bounded_prefix,
    bounded_successor_prefix,
    injective_prefix,
    injective_successor_prefix,
    surjective_successor_prefix,
)
from .finite_product_reindex_support import aligned_prefix, aligned_successor_prefix


def make_finite_product_reindex_candidate(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered general product-reindex candidate."""

    fixed_alignment = aligned_successor_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="fra"
    )
    fixed_map_last = beta_at("r", "s", "n", "n", tag="frm")
    fixed_source_product = product_successor_relation(
        "b", "c", "n", "p", tag="frs"
    )
    fixed_target_product = product_successor_relation(
        "z", "d", "n", "q", tag="frt"
    )
    fixed_source_prefix = product_relation(
        "b", "c", "n", "u", tag="fru"
    )
    fixed_target_prefix = product_relation(
        "z", "d", "n", "v", tag="frv"
    )
    fixed_prefix_equality = (
        f"forall u v. ({fixed_source_prefix}) -> ({fixed_target_prefix}) -> u = v"
    )
    fixed_source_last = beta_at(
        "b", "c", "n", "a", tag="fixed_reindex_source_last"
    )
    fixed_target_last = beta_at(
        "z", "d", "n", "a", tag="fixed_reindex_target_last"
    )
    fixed_source_prefix_witness = product_relation(
        "b", "c", "n", "u", tag="fixed_reindex_source_prefix_witness"
    )
    fixed_target_prefix_witness = product_relation(
        "z", "d", "n", "v", tag="fixed_reindex_target_prefix_witness"
    )
    fixed_source_decomposition = (
        f"exists a u. ({fixed_source_last}) /\\ "
        f"(({fixed_source_prefix_witness}) /\\ p = u * a)"
    )
    fixed_target_decomposition = (
        f"exists a v. ({fixed_target_last}) /\\ "
        f"(({fixed_target_prefix_witness}) /\\ q = v * a)"
    )

    bounded = bounded_prefix("r", "s", "l", tag="reindex_bounded")
    injective = injective_prefix("r", "s", "l", tag="reindex_injective")
    aligned = aligned_prefix(
        "r", "s", "b", "c", "z", "d", "l", tag="reindex_aligned"
    )
    source_product = product_relation(
        "b", "c", "l", "p", tag="reindex_source_product"
    )
    target_product = product_relation(
        "z", "d", "l", "q", tag="reindex_target_product"
    )
    statement = (
        f"forall l r s b c z d p q. ({bounded}) -> ({injective}) -> "
        f"({aligned}) -> ({source_product}) -> ({target_product}) -> p = q"
    )

    surjective_succ = surjective_successor_prefix(
        "r", "s", "l", tag="reindex_surjective_succ"
    )
    map_preimage = beta_at("r", "s", "k", "l", tag="reindex_map_preimage")
    source_last = beta_at("b", "c", "l", "a", tag="reindex_source_last")
    target_preimage = beta_at(
        "z", "d", "x", "x1", tag="reindex_target_preimage"
    )
    map_last = beta_at("r", "s", "l", "l", tag="reindex_map_last")
    map_decoded_last = beta_at(
        "r", "s", "l", "m", tag="reindex_map_decoded_last"
    )
    target_decoded_last = beta_at(
        "z", "d", "l", "w", tag="reindex_target_decoded_last"
    )

    bounded_prefix_old = bounded_prefix(
        "r", "s", "l", tag="reindex_bounded_prefix"
    )
    injective_prefix_old = injective_prefix(
        "r", "s", "l", tag="reindex_injective_prefix"
    )
    aligned_prefix_old = aligned_prefix(
        "r", "s", "b", "c", "z", "d", "l", tag="reindex_aligned_prefix"
    )
    source_prefix_product = product_relation(
        "b", "c", "l", "u", tag="reindex_source_prefix_product"
    )
    target_prefix_product = product_relation(
        "z", "d", "l", "v", tag="reindex_target_prefix_product"
    )
    prefix_products_equal = (
        f"forall u v. ({source_prefix_product}) -> "
        f"({target_prefix_product}) -> u = v"
    )

    map_swap_contract = (
        "exists rm sm. "
        f"({beta_at('rm', 'sm', 'x', 'x2', tag='reindex_map_swap_i')}) /\\ "
        f"(({beta_at('rm', 'sm', 'l', 'l', tag='reindex_map_swap_last')}) /\\ "
        "forall j a. (exists h. h + S j = S l) -> ~(j = x) -> "
        f"~(j = l) -> ({beta_at('r', 's', 'j', 'a', tag='reindex_map_swap_old')}) -> "
        f"({beta_at('rm', 'sm', 'j', 'a', tag='reindex_map_swap_new')}))"
    )
    target_swap_contract = (
        "exists tz td. "
        f"({beta_at('tz', 'td', 'x', 'x3', tag='reindex_target_swap_i')}) /\\ "
        f"(({beta_at('tz', 'td', 'l', 'x1', tag='reindex_target_swap_last')}) /\\ "
        "forall j a. (exists h. h + S j = S l) -> ~(j = x) -> "
        f"~(j = l) -> ({beta_at('z', 'd', 'j', 'a', tag='reindex_target_swap_old')}) -> "
        f"({beta_at('tz', 'td', 'j', 'a', tag='reindex_target_swap_new')}))"
    )
    swapped_bounded = bounded_successor_prefix(
        "x4", "x5", "l", tag="reindex_swapped_bounded"
    )
    swapped_injective = injective_successor_prefix(
        "x4", "x5", "l", tag="reindex_swapped_injective"
    )
    swapped_aligned = aligned_successor_prefix(
        "x4", "x5", "b", "c", "x6", "x7", "l", tag="reindex_swapped_aligned"
    )
    swapped_bounded_prefix = bounded_prefix(
        "x4", "x5", "l", tag="reindex_swapped_bounded_prefix"
    )
    swapped_injective_prefix = injective_prefix(
        "x4", "x5", "l", tag="reindex_swapped_injective_prefix"
    )
    swapped_aligned_prefix = aligned_prefix(
        "x4",
        "x5",
        "b",
        "c",
        "x6",
        "x7",
        "l",
        tag="reindex_swapped_aligned_prefix",
    )
    swapped_target_product_exists = (
        "exists t. "
        f"({product_successor_relation('x6', 'x7', 'l', 't', tag='reindex_swapped_target_exists')})"
    )
    swapped_target_product = product_successor_relation(
        "x6", "x7", "l", "x8", tag="reindex_swapped_target_product"
    )
    swapped_target_prefix_product = product_relation(
        "x6", "x7", "l", "v", tag="reindex_swapped_target_prefix_product"
    )
    swapped_prefix_products_equal = (
        f"forall u v. ({source_prefix_product}) -> "
        f"({swapped_target_prefix_product}) -> u = v"
    )
    source_at_map_last = beta_at(
        "b", "c", "x2", "x3", tag="reindex_source_at_map_last"
    )
    target_from_map_last = beta_at(
        "z", "d", "l", "x9", tag="reindex_target_from_map_last"
    )

    return (
        spec(
            "beta_product_reindex_fixed_last",
            "forall r s b c z d n p q. "
            f"({fixed_alignment}) -> ({fixed_map_last}) -> "
            f"({fixed_source_product}) -> ({fixed_target_product}) -> "
            f"({fixed_prefix_equality}) -> p = q",
            ("beta_product_succ_decompose", "beta_at_unique", "le_refl"),
            (
                "intro r",
                "intro s",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro p",
                "intro q",
                "intro haligned",
                "intro hmap_last",
                "intro hsource_product",
                "intro htarget_product",
                "intro hprefix_equal",
                f"have hsource_decomp : {fixed_source_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose n",
                "specialize beta_product_succ_decompose p",
                "apply beta_product_succ_decompose",
                "exact hsource_product",
                f"have htarget_decomp : {fixed_target_decomposition}",
                "specialize beta_product_succ_decompose z",
                "specialize beta_product_succ_decompose d",
                "specialize beta_product_succ_decompose n",
                "specialize beta_product_succ_decompose q",
                "apply beta_product_succ_decompose",
                "exact htarget_product",
                "cases hsource_decomp",
                "cases hsource_decomp_witness",
                "cases hsource_decomp_witness_witness",
                "cases hsource_decomp_witness_witness_right",
                "cases htarget_decomp",
                "cases htarget_decomp_witness",
                "cases htarget_decomp_witness_witness",
                "cases htarget_decomp_witness_witness_right",
                "have htarget_source_last : "
                + beta_at("z", "d", "n", "x", tag="fixed_target_source_last"),
                "specialize haligned n",
                "specialize haligned n",
                "specialize haligned x",
                "apply haligned",
                "specialize le_refl (S n)",
                "exact le_refl",
                "exact hmap_last",
                "exact hsource_decomp_witness_witness_left",
                "have hlast_equal : x2 = x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact htarget_decomp_witness_witness_left",
                "exact htarget_source_last",
                "have hprefixes_equal : x1 = x3",
                "specialize hprefix_equal x1",
                "specialize hprefix_equal x3",
                "apply hprefix_equal",
                "exact hsource_decomp_witness_witness_right_left",
                "exact htarget_decomp_witness_witness_right_left",
                "rewrite hsource_decomp_witness_witness_right_right",
                "rewrite htarget_decomp_witness_witness_right_right",
                "rewrite hlast_equal",
                "rewrite hprefixes_equal",
                "refl",
            ),
            "A fixed-final reindex reduces successor product equality to equality of the two prefix products.",
        ),
        spec(
            "beta_product_permutation_invariant",
            statement,
            (
                "finite_bounded_injective_surjective",
                "finite_lt_succ_eq_or_lt",
                "finite_fixed_last_prefix_bounded",
                "finite_injective_prefix_succ",
                "beta_prefix_swap_last_from_entries",
                "finite_swap_last_bounded",
                "finite_swap_last_injective",
                "beta_product_swap_last_invariant",
                "beta_product_zero",
                "beta_product_exists",
                "beta_at_exists",
                "beta_at_unique",
                "beta_reindex_alignment_swap_last",
                "beta_product_reindex_fixed_last",
                "le_refl",
                "le_succ",
            ),
            (
                "induction l",
                "intro r",
                "intro s",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro p",
                "intro q",
                "intro hbounded",
                "intro hinjective",
                "intro haligned",
                "intro hsource_product",
                "intro htarget_product",
                "have hp : p = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero p",
                "apply beta_product_zero",
                "exact hsource_product",
                "have hq : q = 1",
                "specialize beta_product_zero z",
                "specialize beta_product_zero d",
                "specialize beta_product_zero q",
                "apply beta_product_zero",
                "exact htarget_product",
                "trans 1",
                "exact hp",
                "symm",
                "exact hq",
                "intro r",
                "intro s",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro p",
                "intro q",
                "intro hbounded",
                "intro hinjective",
                "intro haligned",
                "intro hsource_product",
                "intro htarget_product",
                f"have hsurjective : {surjective_succ}",
                "specialize finite_bounded_injective_surjective (S l)",
                "specialize finite_bounded_injective_surjective r",
                "specialize finite_bounded_injective_surjective s",
                "apply finite_bounded_injective_surjective",
                "exact hbounded",
                "exact hinjective",
                "have hlast_bound : exists h. h + S l = S l",
                "specialize le_refl (S l)",
                "exact le_refl",
                "have hpreimage : exists k. "
                f"((exists h. h + S k = S l) /\\ ({map_preimage}))",
                "specialize hsurjective l",
                "apply hsurjective",
                "exact hlast_bound",
                "cases hpreimage",
                "cases hpreimage_witness",
                f"have hsource_last : exists a. ({source_last})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hsource_last",
                f"have htarget_at_preimage : {target_preimage}",
                "specialize haligned x",
                "specialize haligned l",
                "specialize haligned x1",
                "apply haligned",
                "exact hpreimage_witness_left",
                "exact hpreimage_witness_right",
                "exact hsource_last_witness",
                "have hsplit : x = l \\/ exists h. h + S x = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt x",
                "apply finite_lt_succ_eq_or_lt",
                "exact hpreimage_witness_left",
                "cases hsplit",
                f"have hmap_last : {map_last}",
                "rewrite hsplit_left at hpreimage_witness_right",
                "rewrite hsplit_left at hpreimage_witness_right",
                "exact hpreimage_witness_right",
                f"have hbounded_prefix : {bounded_prefix_old}",
                "specialize finite_fixed_last_prefix_bounded r",
                "specialize finite_fixed_last_prefix_bounded s",
                "specialize finite_fixed_last_prefix_bounded l",
                "apply finite_fixed_last_prefix_bounded",
                "exact hbounded",
                "exact hinjective",
                "exact hmap_last",
                f"have hinjective_prefix : {injective_prefix_old}",
                "specialize finite_injective_prefix_succ r",
                "specialize finite_injective_prefix_succ s",
                "specialize finite_injective_prefix_succ l",
                "specialize finite_injective_prefix_succ (S l)",
                "apply finite_injective_prefix_succ",
                "refl",
                "exact hinjective",
                f"have haligned_prefix : {aligned_prefix_old}",
                "intro i",
                "intro j",
                "intro a",
                "intro hi",
                "intro hmap",
                "intro hsource",
                "specialize haligned i",
                "specialize haligned j",
                "specialize haligned a",
                "apply haligned",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hmap",
                "exact hsource",
                f"have hprefix_products_equal : {prefix_products_equal}",
                "intro u",
                "intro v",
                "intro hsource_prefix_product",
                "intro htarget_prefix_product",
                "specialize IH r",
                "specialize IH s",
                "specialize IH b",
                "specialize IH c",
                "specialize IH z",
                "specialize IH d",
                "specialize IH u",
                "specialize IH v",
                "apply IH",
                "exact hbounded_prefix",
                "exact hinjective_prefix",
                "exact haligned_prefix",
                "exact hsource_prefix_product",
                "exact htarget_prefix_product",
                "specialize beta_product_reindex_fixed_last r",
                "specialize beta_product_reindex_fixed_last s",
                "specialize beta_product_reindex_fixed_last b",
                "specialize beta_product_reindex_fixed_last c",
                "specialize beta_product_reindex_fixed_last z",
                "specialize beta_product_reindex_fixed_last d",
                "specialize beta_product_reindex_fixed_last l",
                "specialize beta_product_reindex_fixed_last p",
                "specialize beta_product_reindex_fixed_last q",
                "apply beta_product_reindex_fixed_last",
                "exact haligned",
                "exact hmap_last",
                "exact hsource_product",
                "exact htarget_product",
                "exact hprefix_products_equal",
                f"have hmap_last_decoded : exists m. ({map_decoded_last})",
                "specialize beta_at_exists r",
                "specialize beta_at_exists s",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hmap_last_decoded",
                f"have htarget_last_decoded : exists w. ({target_decoded_last})",
                "specialize beta_at_exists z",
                "specialize beta_at_exists d",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases htarget_last_decoded",
                f"have hmap_swap : {map_swap_contract}",
                "specialize beta_prefix_swap_last_from_entries r",
                "specialize beta_prefix_swap_last_from_entries s",
                "specialize beta_prefix_swap_last_from_entries l",
                "specialize beta_prefix_swap_last_from_entries x",
                "specialize beta_prefix_swap_last_from_entries l",
                "specialize beta_prefix_swap_last_from_entries x2",
                "apply beta_prefix_swap_last_from_entries",
                "exact hsplit_right",
                "exact hpreimage_witness_right",
                "exact hmap_last_decoded_witness",
                "cases hmap_swap",
                "cases hmap_swap_witness",
                "cases hmap_swap_witness_witness",
                "cases hmap_swap_witness_witness_right",
                f"have htarget_swap : {target_swap_contract}",
                "specialize beta_prefix_swap_last_from_entries z",
                "specialize beta_prefix_swap_last_from_entries d",
                "specialize beta_prefix_swap_last_from_entries l",
                "specialize beta_prefix_swap_last_from_entries x",
                "specialize beta_prefix_swap_last_from_entries x1",
                "specialize beta_prefix_swap_last_from_entries x3",
                "apply beta_prefix_swap_last_from_entries",
                "exact hsplit_right",
                "exact htarget_at_preimage",
                "exact htarget_last_decoded_witness",
                "cases htarget_swap",
                "cases htarget_swap_witness",
                "cases htarget_swap_witness_witness",
                "cases htarget_swap_witness_witness_right",
                f"have hswapped_bounded : {swapped_bounded}",
                "specialize finite_swap_last_bounded r",
                "specialize finite_swap_last_bounded s",
                "specialize finite_swap_last_bounded x4",
                "specialize finite_swap_last_bounded x5",
                "specialize finite_swap_last_bounded l",
                "specialize finite_swap_last_bounded (S l)",
                "specialize finite_swap_last_bounded x",
                "specialize finite_swap_last_bounded l",
                "specialize finite_swap_last_bounded x2",
                "apply finite_swap_last_bounded",
                "refl",
                "exact hsplit_right",
                "exact hbounded",
                "exact hpreimage_witness_right",
                "exact hmap_last_decoded_witness",
                "exact hmap_swap_witness_witness_left",
                "exact hmap_swap_witness_witness_right_left",
                "exact hmap_swap_witness_witness_right_right",
                f"have hswapped_injective : {swapped_injective}",
                "specialize finite_swap_last_injective r",
                "specialize finite_swap_last_injective s",
                "specialize finite_swap_last_injective x4",
                "specialize finite_swap_last_injective x5",
                "specialize finite_swap_last_injective l",
                "specialize finite_swap_last_injective (S l)",
                "specialize finite_swap_last_injective x",
                "specialize finite_swap_last_injective l",
                "specialize finite_swap_last_injective x2",
                "apply finite_swap_last_injective",
                "refl",
                "exact hsplit_right",
                "exact hinjective",
                "exact hpreimage_witness_right",
                "exact hmap_last_decoded_witness",
                "exact hmap_swap_witness_witness_left",
                "exact hmap_swap_witness_witness_right_left",
                "exact hmap_swap_witness_witness_right_right",
                f"have hswapped_target_product_exists : {swapped_target_product_exists}",
                "specialize beta_product_exists x6",
                "specialize beta_product_exists x7",
                "specialize beta_product_exists (S l)",
                "exact beta_product_exists",
                "cases hswapped_target_product_exists",
                "have htarget_product_swap : q = x8",
                "specialize beta_product_swap_last_invariant z",
                "specialize beta_product_swap_last_invariant d",
                "specialize beta_product_swap_last_invariant x6",
                "specialize beta_product_swap_last_invariant x7",
                "specialize beta_product_swap_last_invariant l",
                "specialize beta_product_swap_last_invariant x",
                "specialize beta_product_swap_last_invariant x1",
                "specialize beta_product_swap_last_invariant x3",
                "specialize beta_product_swap_last_invariant q",
                "specialize beta_product_swap_last_invariant x8",
                "apply beta_product_swap_last_invariant",
                "exact hsplit_right",
                "exact htarget_at_preimage",
                "exact htarget_last_decoded_witness",
                "exact htarget_swap_witness_witness_left",
                "exact htarget_swap_witness_witness_right_left",
                "exact htarget_swap_witness_witness_right_right",
                "exact htarget_product",
                "exact hswapped_target_product_exists_witness",
                f"have hsource_at_map_last : {source_at_map_last}",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists x2",
                "cases beta_at_exists",
                f"have htarget_from_map_last : {target_from_map_last}",
                "specialize haligned l",
                "specialize haligned x2",
                "specialize haligned x9",
                "apply haligned",
                "exact hlast_bound",
                "exact hmap_last_decoded_witness",
                "exact beta_at_exists_witness",
                "have hmap_last_value : x9 = x3",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x9",
                "specialize beta_at_unique x3",
                "apply beta_at_unique",
                "exact htarget_from_map_last",
                "exact htarget_last_decoded_witness",
                "rewrite hmap_last_value at beta_at_exists_witness",
                "rewrite hmap_last_value at beta_at_exists_witness",
                "exact beta_at_exists_witness",
                f"have hswapped_aligned : {swapped_aligned}",
                "specialize beta_reindex_alignment_swap_last r",
                "specialize beta_reindex_alignment_swap_last s",
                "specialize beta_reindex_alignment_swap_last x4",
                "specialize beta_reindex_alignment_swap_last x5",
                "specialize beta_reindex_alignment_swap_last b",
                "specialize beta_reindex_alignment_swap_last c",
                "specialize beta_reindex_alignment_swap_last z",
                "specialize beta_reindex_alignment_swap_last d",
                "specialize beta_reindex_alignment_swap_last x6",
                "specialize beta_reindex_alignment_swap_last x7",
                "specialize beta_reindex_alignment_swap_last l",
                "specialize beta_reindex_alignment_swap_last x",
                "specialize beta_reindex_alignment_swap_last x2",
                "specialize beta_reindex_alignment_swap_last x1",
                "specialize beta_reindex_alignment_swap_last x3",
                "apply beta_reindex_alignment_swap_last",
                "exact hmap_swap_witness_witness_left",
                "exact hmap_swap_witness_witness_right_left",
                "exact hmap_swap_witness_witness_right_right",
                "exact hsource_at_map_last",
                "exact hsource_last_witness",
                "exact htarget_swap_witness_witness_left",
                "exact htarget_swap_witness_witness_right_left",
                "exact htarget_swap_witness_witness_right_right",
                "exact haligned",
                f"have hswapped_bounded_prefix : {swapped_bounded_prefix}",
                "specialize finite_fixed_last_prefix_bounded x4",
                "specialize finite_fixed_last_prefix_bounded x5",
                "specialize finite_fixed_last_prefix_bounded l",
                "apply finite_fixed_last_prefix_bounded",
                "exact hswapped_bounded",
                "exact hswapped_injective",
                "exact hmap_swap_witness_witness_right_left",
                f"have hswapped_injective_prefix : {swapped_injective_prefix}",
                "specialize finite_injective_prefix_succ x4",
                "specialize finite_injective_prefix_succ x5",
                "specialize finite_injective_prefix_succ l",
                "specialize finite_injective_prefix_succ (S l)",
                "apply finite_injective_prefix_succ",
                "refl",
                "exact hswapped_injective",
                f"have hswapped_aligned_prefix : {swapped_aligned_prefix}",
                "intro i",
                "intro j",
                "intro a",
                "intro hi",
                "intro hmap",
                "intro hsource",
                "specialize hswapped_aligned i",
                "specialize hswapped_aligned j",
                "specialize hswapped_aligned a",
                "apply hswapped_aligned",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hmap",
                "exact hsource",
                f"have hswapped_prefix_products_equal : {swapped_prefix_products_equal}",
                "intro u",
                "intro v",
                "intro hsource_prefix_product",
                "intro htarget_prefix_product",
                "specialize IH x4",
                "specialize IH x5",
                "specialize IH b",
                "specialize IH c",
                "specialize IH x6",
                "specialize IH x7",
                "specialize IH u",
                "specialize IH v",
                "apply IH",
                "exact hswapped_bounded_prefix",
                "exact hswapped_injective_prefix",
                "exact hswapped_aligned_prefix",
                "exact hsource_prefix_product",
                "exact htarget_prefix_product",
                "have hproduct_swapped : p = x8",
                "specialize beta_product_reindex_fixed_last x4",
                "specialize beta_product_reindex_fixed_last x5",
                "specialize beta_product_reindex_fixed_last b",
                "specialize beta_product_reindex_fixed_last c",
                "specialize beta_product_reindex_fixed_last x6",
                "specialize beta_product_reindex_fixed_last x7",
                "specialize beta_product_reindex_fixed_last l",
                "specialize beta_product_reindex_fixed_last p",
                "specialize beta_product_reindex_fixed_last x8",
                "apply beta_product_reindex_fixed_last",
                "exact hswapped_aligned",
                "exact hmap_swap_witness_witness_right_left",
                "exact hsource_product",
                "exact hswapped_target_product_exists_witness",
                "exact hswapped_prefix_products_equal",
                "trans x8",
                "exact hproduct_swapped",
                "symm",
                "exact htarget_product_swap",
            ),
            "A bounded injective beta-coded reindexing preserves the exact finite product.",
        ),
    )


__all__ = ["make_finite_product_reindex_candidate"]
