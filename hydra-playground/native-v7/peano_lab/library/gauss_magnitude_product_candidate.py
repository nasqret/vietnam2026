"""Isolated product boundary for the Gauss magnitude permutation.

This untrusted authoring module is deliberately downstream of
``gauss_magnitude_permutation_candidate``.  It leaves that WMI-packaged
source untouched and records only the next modular boundary:

* predecessor-code surjectivity transports to coverage of all successors
  ``1,...,h`` by the magnitude prefix;
* the predecessor code aligns the canonical half range with that prefix; and
* the existing finite-product permutation theorem identifies their products.

Every helper imported here expands into the unchanged first-order language of
Peano arithmetic.  No sequence, subtraction, permutation, or product symbol is
added to the parser or kernel, and this candidate is not registered publicly.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation
from .finite_permutation_theorems import (
    bounded_prefix,
    injective_prefix,
    surjective_prefix,
)
from .finite_product_reindex_support import aligned_prefix
from .gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    _strictly_below_term,
    half_range,
)


def make_gauss_magnitude_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the successor-coverage, alignment, and product boundary specs."""

    magnitude_range = magnitude_range_prefix(
        "mb", "mc", "h", "h", tag="product_magnitude_range"
    )
    magnitude_injective = injective_prefix(
        "mb", "mc", "h", tag="product_magnitude_injective"
    )
    predecessor_recode = predecessor_recode_prefix(
        "mb", "mc", "rb", "rc", "h", tag="product_predecessor_recode"
    )
    predecessor_bounded = bounded_prefix(
        "rb", "rc", "h", tag="product_predecessor_bounded"
    )
    predecessor_injective = injective_prefix(
        "rb", "rc", "h", tag="product_predecessor_injective"
    )
    predecessor_surjective = surjective_prefix(
        "rb", "rc", "h", tag="product_predecessor_surjective"
    )
    canonical_half_range = half_range(
        "b", "c", "h", tag="product_canonical_half_range"
    )
    alignment = aligned_prefix(
        "rb", "rc", "b", "c", "mb", "mc", "h", tag="product_alignment"
    )
    canonical_product = product_relation(
        "b", "c", "h", "P", tag="product_canonical_product"
    )
    magnitude_product = product_relation(
        "mb", "mc", "h", "Q", tag="product_magnitude_product"
    )

    coverage_variables = ("mb", "mc", "rb", "rc", "h", "j", "i")
    coverage_value_bound = _strictly_below_term(
        "j",
        "h",
        tag="product_coverage_value_bound",
        variables=coverage_variables,
    )
    coverage_index_bound = _strictly_below_term(
        "i",
        "h",
        tag="product_coverage_index_bound",
        variables=coverage_variables,
    )
    coverage_predecessor_entry = beta_at(
        "rb", "rc", "i", "j", tag="product_coverage_predecessor_entry"
    )
    coverage_magnitude_entry = _beta_at_term(
        "mb",
        "mc",
        "i",
        "S j",
        tag="product_coverage_magnitude_entry",
        variables=coverage_variables,
    )
    coverage_result = (
        f"forall j. ({coverage_value_bound}) -> exists i. "
        f"(({coverage_index_bound}) /\\ ({coverage_magnitude_entry}))"
    )

    alignment_predecessor_entry = beta_at(
        "rb", "rc", "i", "j", tag="product_alignment_predecessor_entry"
    )
    alignment_magnitude_successor = _beta_at_term(
        "mb",
        "mc",
        "i",
        "S j",
        tag="product_alignment_magnitude_successor",
        variables=("mb", "mc", "rb", "rc", "b", "c", "h", "i", "j", "x"),
    )

    return (
        spec(
            "gauss_magnitude_successor_coverage",
            "forall mb mc rb rc h. "
            f"({magnitude_range}) -> ({magnitude_injective}) -> "
            f"({predecessor_recode}) -> ({coverage_result})",
            (
                "beta_magnitude_predecessor_recode_surjective",
                "beta_magnitude_predecessor_recode_reflect",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro h",
                "intro hrange",
                "intro hmagnitude_injective",
                "intro hrecode",
                f"have hsurjective : {predecessor_surjective}",
                "specialize beta_magnitude_predecessor_recode_surjective mb",
                "specialize beta_magnitude_predecessor_recode_surjective mc",
                "specialize beta_magnitude_predecessor_recode_surjective rb",
                "specialize beta_magnitude_predecessor_recode_surjective rc",
                "specialize beta_magnitude_predecessor_recode_surjective h",
                "apply beta_magnitude_predecessor_recode_surjective",
                "exact hrange",
                "exact hmagnitude_injective",
                "exact hrecode",
                "intro j",
                "intro hj",
                "have hpreimage : exists i. "
                f"(({coverage_index_bound}) /\\ ({coverage_predecessor_entry}))",
                "specialize hsurjective j",
                "apply hsurjective",
                "exact hj",
                "cases hpreimage",
                "cases hpreimage_witness",
                "exists x",
                "split",
                "exact hpreimage_witness_left",
                "specialize beta_magnitude_predecessor_recode_reflect mb",
                "specialize beta_magnitude_predecessor_recode_reflect mc",
                "specialize beta_magnitude_predecessor_recode_reflect rb",
                "specialize beta_magnitude_predecessor_recode_reflect rc",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect x",
                "specialize beta_magnitude_predecessor_recode_reflect j",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hpreimage_witness_left",
                "exact hpreimage_witness_right",
            ),
            "Surjectivity of predecessor values transports every j<h to a decoded magnitude S j.",
        ),
        spec(
            "gauss_predecessor_half_range_aligned",
            "forall mb mc rb rc b c h. "
            f"({magnitude_range}) -> ({predecessor_recode}) -> "
            f"({canonical_half_range}) -> ({alignment})",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_reflect",
                "beta_at_unique",
                "beta_range_entry_eq",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro b",
                "intro c",
                "intro h",
                "intro hrange",
                "intro hrecode",
                "intro hhalf",
                f"have hbounded : {predecessor_bounded}",
                "specialize beta_magnitude_predecessor_recode_bounded mb",
                "specialize beta_magnitude_predecessor_recode_bounded mc",
                "specialize beta_magnitude_predecessor_recode_bounded rb",
                "specialize beta_magnitude_predecessor_recode_bounded rc",
                "specialize beta_magnitude_predecessor_recode_bounded h",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                "intro i",
                "intro j",
                "intro x",
                "intro hi",
                "intro hmap",
                "intro hsource",
                "have hjdata : exists y. "
                f"(({beta_at('rb', 'rc', 'i', 'y', tag='product_alignment_bounded_entry')}) /\\ "
                f"({_strictly_below_term('y', 'h', tag='product_alignment_bounded_value', variables=('mb', 'mc', 'rb', 'rc', 'b', 'c', 'h', 'i', 'j', 'x', 'y'))}))",
                "specialize hbounded i",
                "apply hbounded",
                "exact hi",
                "cases hjdata",
                "cases hjdata_witness",
                "have hjy : j = x1",
                "specialize beta_at_unique rb",
                "specialize beta_at_unique rc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hmap",
                "exact hjdata_witness_left",
                f"have hj : {_strictly_below_term('j', 'h', tag='product_alignment_j_bound', variables=('mb', 'mc', 'rb', 'rc', 'b', 'c', 'h', 'i', 'j', 'x', 'x1'))}",
                "rewrite hjy",
                "exact hjdata_witness_right",
                f"have hmagnitude : {alignment_magnitude_successor}",
                "specialize beta_magnitude_predecessor_recode_reflect mb",
                "specialize beta_magnitude_predecessor_recode_reflect mc",
                "specialize beta_magnitude_predecessor_recode_reflect rb",
                "specialize beta_magnitude_predecessor_recode_reflect rc",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect h",
                "specialize beta_magnitude_predecessor_recode_reflect i",
                "specialize beta_magnitude_predecessor_recode_reflect j",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hi",
                "exact hmap",
                "have hxraw : x = 1 + j",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq h",
                "specialize beta_range_entry_eq j",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hhalf",
                "exact hj",
                "exact hsource",
                "have hone : 1 + j = S j",
                "trans S (0 + j)",
                "specialize add_succ_left 0",
                "specialize add_succ_left j",
                "exact add_succ_left",
                "congr",
                "specialize zero_add j",
                "exact zero_add",
                "have hxsucc : x = S j",
                "trans 1 + j",
                "exact hxraw",
                "exact hone",
                "rewrite hxsucc",
                "rewrite hxsucc",
                "exact hmagnitude",
            ),
            "The predecessor map aligns canonical factor 1+j with magnitude S j at every position.",
        ),
        spec(
            "gauss_magnitude_product_eq_half_range",
            "forall mb mc rb rc b c h P Q. "
            f"({magnitude_range}) -> ({magnitude_injective}) -> "
            f"({predecessor_recode}) -> ({canonical_half_range}) -> "
            f"({canonical_product}) -> ({magnitude_product}) -> P = Q",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_injective",
                "gauss_predecessor_half_range_aligned",
                "beta_product_permutation_invariant",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro b",
                "intro c",
                "intro h",
                "intro P",
                "intro Q",
                "intro hrange",
                "intro hmagnitude_injective",
                "intro hrecode",
                "intro hhalf",
                "intro hcanonical_product",
                "intro hmagnitude_product",
                f"have hbounded : {predecessor_bounded}",
                "specialize beta_magnitude_predecessor_recode_bounded mb",
                "specialize beta_magnitude_predecessor_recode_bounded mc",
                "specialize beta_magnitude_predecessor_recode_bounded rb",
                "specialize beta_magnitude_predecessor_recode_bounded rc",
                "specialize beta_magnitude_predecessor_recode_bounded h",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                f"have hinjective : {predecessor_injective}",
                "specialize beta_magnitude_predecessor_recode_injective mb",
                "specialize beta_magnitude_predecessor_recode_injective mc",
                "specialize beta_magnitude_predecessor_recode_injective rb",
                "specialize beta_magnitude_predecessor_recode_injective rc",
                "specialize beta_magnitude_predecessor_recode_injective h",
                "apply beta_magnitude_predecessor_recode_injective",
                "exact hrange",
                "exact hmagnitude_injective",
                "exact hrecode",
                f"have haligned : {alignment}",
                "specialize gauss_predecessor_half_range_aligned mb",
                "specialize gauss_predecessor_half_range_aligned mc",
                "specialize gauss_predecessor_half_range_aligned rb",
                "specialize gauss_predecessor_half_range_aligned rc",
                "specialize gauss_predecessor_half_range_aligned b",
                "specialize gauss_predecessor_half_range_aligned c",
                "specialize gauss_predecessor_half_range_aligned h",
                "apply gauss_predecessor_half_range_aligned",
                "exact hrange",
                "exact hrecode",
                "exact hhalf",
                "specialize beta_product_permutation_invariant h",
                "specialize beta_product_permutation_invariant rb",
                "specialize beta_product_permutation_invariant rc",
                "specialize beta_product_permutation_invariant b",
                "specialize beta_product_permutation_invariant c",
                "specialize beta_product_permutation_invariant mb",
                "specialize beta_product_permutation_invariant mc",
                "specialize beta_product_permutation_invariant P",
                "specialize beta_product_permutation_invariant Q",
                "apply beta_product_permutation_invariant",
                "exact hbounded",
                "exact hinjective",
                "exact haligned",
                "exact hcanonical_product",
                "exact hmagnitude_product",
            ),
            "A magnitude permutation has exactly the product of the canonical half range.",
        ),
    )


__all__ = ["make_gauss_magnitude_product_candidate_theorems"]
