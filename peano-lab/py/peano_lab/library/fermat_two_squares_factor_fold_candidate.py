"""Constructive beta-coded folds of witnessed two-square representations.

These dependency-curried candidates prove that a finite beta-coded product
inherits a two-square representation from each decoded factor.  They also
give a genuinely constructive sufficient prime-factor condition and allow an
arbitrary additional square cofactor.  No factorization/valuation equivalence,
Alpha enrollment, Stable admission, or new logical primitive is asserted.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .finite_fold_surface import (
    _beta_at_term,
    _product_relation_term,
    beta_at,
    product_relation,
    product_successor_relation,
)


def _two_square(value: str, *, tag: str) -> str:
    first = f"ftsf_first_{tag}"
    second = f"ftsf_second_{tag}"
    return f"exists {first} {second}. ({value}) = {first} * {first} + {second} * {second}"


def _bound(index: str, length: str, *, tag: str) -> str:
    gap = f"ftsf_gap_{tag}"
    return f"exists {gap}. {gap} + S {index} = ({length})"


def represented_factor_prefix(
    code: str, scale: str, length: str, *, tag: str
) -> str:
    """Expand: every decoded factor at an index below length is represented."""

    index = f"ftsf_index_{tag}"
    factor = f"ftsf_factor_{tag}"
    bound = _bound(index, length, tag=f"{tag}_bound")
    entry = beta_at(code, scale, index, factor, tag=f"ftsf_{tag}_entry")
    representation = _two_square(factor, tag=f"{tag}_representation")
    return f"forall {index} {factor}. ({bound}) -> ({entry}) -> ({representation})"


def witnessed_represented_factor_prefix(
    code: str, scale: str, length: str, *, tag: str
) -> str:
    """Expand: every bounded index carries a represented decoded factor."""

    index = f"ftsf_index_{tag}"
    factor = f"ftsf_factor_{tag}"
    first = f"ftsf_coordinate_first_{tag}"
    second = f"ftsf_coordinate_second_{tag}"
    bound = _bound(index, length, tag=f"{tag}_bound")
    entry = beta_at(code, scale, index, factor, tag=f"ftsf_{tag}_entry")
    return (
        f"forall {index}. ({bound}) -> exists {factor} {first} {second}. "
        f"(({entry}) /\\ {factor} = {first} * {first} + {second} * {second})"
    )


def all_prime_factor_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand the existing canonical-factorization AllPrime surface."""

    index = f"ftsf_index_{tag}"
    factor = f"ftsf_factor_{tag}"
    bound = _bound(index, length, tag=f"{tag}_bound")
    entry = beta_at(code, scale, index, factor, tag=f"ftsf_{tag}_entry")
    primality = prime(factor, tag=f"ftsf_{tag}_prime")
    return f"forall {index}. ({bound}) -> exists {factor}. (({entry}) /\\ ({primality}))"


def admissible_prime_factor_prefix(
    code: str, scale: str, length: str, *, tag: str
) -> str:
    """Expand: every decoded factor is a prime equal to two or one modulo four."""

    index = f"ftsf_index_{tag}"
    factor = f"ftsf_factor_{tag}"
    residue = f"ftsf_residue_{tag}"
    bound = _bound(index, length, tag=f"{tag}_bound")
    entry = beta_at(code, scale, index, factor, tag=f"ftsf_{tag}_entry")
    primality = prime(factor, tag=f"ftsf_{tag}_prime")
    return (
        f"forall {index} {factor}. ({bound}) -> ({entry}) -> "
        f"(({primality}) /\\ ({factor} = 2 \\/ "
        f"exists {residue}. {factor} = 4 * {residue} + 1))"
    )


def grouped_prime_square_factor_prefix(
    code: str, scale: str, length: str, *, tag: str
) -> str:
    """Expand represented prime singletons and paired bad-prime square blocks."""

    index = f"ftsf_index_{tag}"
    factor = f"ftsf_factor_{tag}"
    good_residue = f"ftsf_good_residue_{tag}"
    bad_prime = f"ftsf_bad_prime_{tag}"
    bad_residue = f"ftsf_bad_residue_{tag}"
    bound = _bound(index, length, tag=f"{tag}_bound")
    entry = beta_at(code, scale, index, factor, tag=f"ftsf_{tag}_entry")
    good_prime = prime(factor, tag=f"ftsf_{tag}_good_prime")
    bad_primality = prime(bad_prime, tag=f"ftsf_{tag}_bad_prime")
    return (
        f"forall {index} {factor}. ({bound}) -> ({entry}) -> "
        f"((({good_prime}) /\\ ({factor} = 2 \\/ exists {good_residue}. "
        f"{factor} = 4 * {good_residue} + 1)) \\/ "
        f"exists {bad_prime} {bad_residue}. "
        f"(({bad_primality}) /\\ ({bad_prime} = 4 * {bad_residue} + 3 /\\ "
        f"{factor} = {bad_prime} * {bad_prime})))"
    )


def _good_prime_divisors(value: str, *, tag: str) -> str:
    divisor = f"ftsf_divisor_{tag}"
    quotient = f"ftsf_quotient_{tag}"
    residue = f"ftsf_residue_{tag}"
    primality = prime(divisor, tag=f"ftsf_{tag}_prime")
    return (
        f"forall {divisor}. ({primality}) -> "
        f"(exists {quotient}. ({value}) = {divisor} * {quotient}) -> "
        f"({divisor} = 2 \\/ exists {residue}. "
        f"{divisor} = 4 * {residue} + 1)"
    )


def make_fermat_two_squares_factor_fold_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build independently kernel-checkable constructive factor-fold rows."""

    old_prefix = represented_factor_prefix("b", "c", "l", tag="drop_old")
    next_prefix = represented_factor_prefix("b", "c", "S l", tag="drop_next")
    witness_prefix = witnessed_represented_factor_prefix(
        "b", "c", "l", tag="witness_source"
    )
    pointwise_prefix = represented_factor_prefix("b", "c", "l", tag="witness_result")
    last_entry = beta_at("b", "c", "l", "a", tag="ftsf_last_entry")
    last_representation = _two_square("a", tag="last_result")
    generic_product = product_relation("b", "c", "l", "n", tag="ftsf_fold_product")
    generic_prefix = represented_factor_prefix("b", "c", "l", tag="fold_prefix")
    generic_result = _two_square("n", tag="fold_result")
    local_prefix = represented_factor_prefix("b", "c", "l", tag="fold_local_prefix")
    local_product = product_relation("b", "c", "l", "r", tag="ftsf_fold_local")
    local_last = beta_at("b", "c", "l", "a", tag="ftsf_fold_last")
    decomposition = (
        f"exists a r. (({local_last}) /\\ (({local_product}) /\\ n = r * a))"
    )
    witnessed_product = product_relation("b", "c", "l", "n", tag="ftsf_witness_product")
    witnessed_source = witnessed_represented_factor_prefix(
        "b", "c", "l", tag="witness_product_source"
    )
    prime_p = prime("p", tag="ftsf_admissible_prime")
    prime_result = _two_square("p", tag="prime_result")
    all_prime = all_prime_factor_prefix("b", "c", "l", tag="all_prime_source")
    selected_entry = beta_at("b", "c", "i", "p", tag="ftsf_selected_entry")
    admissible_prefix = admissible_prime_factor_prefix(
        "b", "c", "l", tag="admissible_source"
    )
    admissible_product = product_relation(
        "b", "c", "l", "n", tag="ftsf_admissible_product"
    )
    square_product = product_relation("b", "c", "l", "m", tag="ftsf_square_product")
    square_prefix = represented_factor_prefix("b", "c", "l", tag="square_prefix")
    good_divisors = _good_prime_divisors("n", tag="canonical_source")
    grouped_prefix = grouped_prime_square_factor_prefix(
        "b", "c", "l", tag="grouped_source"
    )
    grouped_product = product_relation("b", "c", "l", "n", tag="ftsf_grouped_product")
    pair_product = _product_relation_term(
        "b", "c", "S S l", "n", tag="ftsf_pair_product", avoid=("b", "c", "l", "n")
    )
    pair_first = beta_at("b", "c", "l", "q", tag="ftsf_pair_first")
    pair_second = _beta_at_term(
        "b", "c", "S l", "q", tag="ftsf_pair_second", avoid=("b", "c", "l", "q")
    )
    pair_local_product = product_relation("b", "c", "l", "r", tag="ftsf_pair_local")
    pair_outer_entry = _beta_at_term(
        "b", "c", "S l", "a", tag="ftsf_pair_outer", avoid=("b", "c", "l", "a")
    )
    pair_outer_product = product_successor_relation(
        "b", "c", "l", "t", tag="ftsf_pair_outer_product"
    )
    pair_outer_decomposition = (
        f"exists a t. (({pair_outer_entry}) /\\ "
        f"(({pair_outer_product}) /\\ n = t * a))"
    )
    pair_inner_entry = beta_at("b", "c", "l", "a", tag="ftsf_pair_inner")
    pair_inner_product = product_relation("b", "c", "l", "r", tag="ftsf_pair_inner_product")
    pair_inner_decomposition = (
        f"exists a r. (({pair_inner_entry}) /\\ "
        f"(({pair_inner_product}) /\\ x1 = r * a))"
    )

    return (
        spec(
            "beta_two_square_prefix_drop_last",
            f"forall b c l. ({next_prefix}) -> ({old_prefix})",
            ("le_succ",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro hprefix",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hprefix i",
                "specialize hprefix a",
                "apply hprefix",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
            ),
            "Restricting a successor-length prefix preserves every witnessed two-square factor representation.",
        ),
        spec(
            "beta_witnessed_two_square_prefix_implies_pointwise",
            f"forall b c l. ({witness_prefix}) -> ({pointwise_prefix})",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro hwitnessed",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hwitnessed i",
                "have hfactor : exists p x y. "
                f"(({beta_at('b', 'c', 'i', 'p', tag='ftsf_witnessed_local')}) "
                "/\\ p = x * x + y * y)",
                "apply hwitnessed",
                "exact hi",
                "cases hfactor",
                "cases hfactor_witness",
                "cases hfactor_witness_witness",
                "cases hfactor_witness_witness_witness",
                "have hequal : a = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact ha",
                "exact hfactor_witness_witness_witness_left",
                "exists x1",
                "exists x2",
                "rewrite hequal",
                "exact hfactor_witness_witness_witness_right",
            ),
            "Existentially witnessed represented entries imply representation of every actual decoded value by beta uniqueness.",
        ),
        spec(
            "beta_two_square_prefix_last_represented",
            f"forall b c l a. ({next_prefix}) -> ({last_entry}) -> ({last_representation})",
            ("le_refl",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro a",
                "intro hprefix",
                "intro hlast",
                "specialize hprefix l",
                "specialize hprefix a",
                "apply hprefix",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hlast",
            ),
            "The final decoded factor of a represented successor prefix has its own explicit two-square witnesses.",
        ),
        spec(
            "beta_two_square_represented_factor_product",
            f"forall b c l n. ({generic_product}) -> ({generic_prefix}) -> ({generic_result})",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "beta_two_square_prefix_drop_last",
                "beta_two_square_prefix_last_represented",
                "two_square_representation_multiplicatively_closed",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro n",
                "intro hproduct",
                "intro hprefix",
                "have hunit : n = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero n",
                "apply beta_product_zero",
                "exact hproduct",
                "exists 1",
                "exists 0",
                "rewrite hunit",
                "norm_num",
                "intro n",
                "intro hproduct",
                "intro hprefix",
                f"have hdecomposition : {decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose n",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                f"have hrestricted : {local_prefix}",
                "specialize beta_two_square_prefix_drop_last b",
                "specialize beta_two_square_prefix_drop_last c",
                "specialize beta_two_square_prefix_drop_last l",
                "apply beta_two_square_prefix_drop_last",
                "exact hprefix",
                f"have hpartial : {_two_square('x1', tag='fold_partial')}",
                "specialize IH x1",
                "apply IH",
                "exact hdecomposition_witness_witness_right_left",
                "exact hrestricted",
                f"have hlast : {_two_square('x', tag='fold_last_representation')}",
                "specialize beta_two_square_prefix_last_represented b",
                "specialize beta_two_square_prefix_last_represented c",
                "specialize beta_two_square_prefix_last_represented l",
                "specialize beta_two_square_prefix_last_represented x",
                "apply beta_two_square_prefix_last_represented",
                "exact hprefix",
                "exact hdecomposition_witness_witness_left",
                "rewrite hdecomposition_witness_witness_right_right",
                "specialize two_square_representation_multiplicatively_closed x1",
                "specialize two_square_representation_multiplicatively_closed x",
                "apply two_square_representation_multiplicatively_closed",
                "exact hpartial",
                "exact hlast",
            ),
            "Induction on an arbitrary beta-coded product constructs a two-square representation from represented decoded factors.",
        ),
        spec(
            "beta_witnessed_two_square_factor_product",
            f"forall b c l n. ({witnessed_product}) -> ({witnessed_source}) -> "
            f"({_two_square('n', tag='witness_product_result')})",
            (
                "beta_witnessed_two_square_prefix_implies_pointwise",
                "beta_two_square_represented_factor_product",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hproduct",
                "intro hwitnessed",
                "specialize beta_two_square_represented_factor_product b",
                "specialize beta_two_square_represented_factor_product c",
                "specialize beta_two_square_represented_factor_product l",
                "specialize beta_two_square_represented_factor_product n",
                "apply beta_two_square_represented_factor_product",
                "exact hproduct",
                "specialize beta_witnessed_two_square_prefix_implies_pointwise b",
                "specialize beta_witnessed_two_square_prefix_implies_pointwise c",
                "specialize beta_witnessed_two_square_prefix_implies_pointwise l",
                "apply beta_witnessed_two_square_prefix_implies_pointwise",
                "exact hwitnessed",
            ),
            "A represented decoded factor supplied existentially at every bounded index suffices for an explicit representation of the whole product.",
        ),
        spec(
            "prime_two_or_one_mod_four_is_sum_of_two_squares",
            f"forall p. ({prime_p}) -> "
            f"(p = 2 \\/ exists t. p = 4 * t + 1) -> ({prime_result})",
            ("zero_or_succ", "prime_nonzero", "prime_mod_four_one_is_sum_of_two_squares"),
            (
                "intro p",
                "intro hprime",
                "intro hclass",
                "cases hclass",
                "exists 1",
                "exists 1",
                "rewrite hclass_left",
                "norm_num",
                "specialize zero_or_succ p",
                "cases zero_or_succ",
                "exfalso",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact zero_or_succ_left",
                "cases zero_or_succ_right",
                "specialize prime_mod_four_one_is_sum_of_two_squares p",
                "specialize prime_mod_four_one_is_sum_of_two_squares x",
                "apply prime_mod_four_one_is_sum_of_two_squares",
                "exact zero_or_succ_right_witness",
                "exact hprime",
                "exact hclass_right",
            ),
            "The exceptional prime two and every prime congruent to one modulo four have explicit constructive two-square representations.",
        ),
        spec(
            "beta_all_prime_entry_is_prime",
            f"forall b c l i p. ({all_prime}) -> "
            f"({_bound('i', 'l', tag='all_prime_entry')}) -> ({selected_entry}) -> "
            f"({prime('p', tag='ftsf_selected_prime')})",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro p",
                "intro hall",
                "intro hi",
                "intro hp",
                "specialize hall i",
                "have hentry : exists a. "
                f"(({beta_at('b', 'c', 'i', 'a', tag='ftsf_prime_local')}) /\\ "
                f"({prime('a', tag='ftsf_prime_local')}))",
                "apply hall",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "have hequal : p = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique p",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hp",
                "exact hentry_witness_left",
                "rewrite hequal",
                "rewrite hequal",
                "exact hentry_witness_right",
            ),
            "Every concrete decoded entry in the canonical all-prime prefix is prime, by uniqueness of beta decoding.",
        ),
        spec(
            "beta_admissible_prime_factor_product_is_two_square",
            f"forall b c l n. ({admissible_product}) -> ({admissible_prefix}) -> "
            f"({_two_square('n', tag='admissible_result')})",
            (
                "beta_two_square_represented_factor_product",
                "prime_two_or_one_mod_four_is_sum_of_two_squares",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hproduct",
                "intro hadmissible",
                "specialize beta_two_square_represented_factor_product b",
                "specialize beta_two_square_represented_factor_product c",
                "specialize beta_two_square_represented_factor_product l",
                "specialize beta_two_square_represented_factor_product n",
                "apply beta_two_square_represented_factor_product",
                "exact hproduct",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                "specialize hadmissible i",
                "specialize hadmissible p",
                "have hclass : "
                f"({prime('p', tag='ftsf_admissible_local')}) /\\ "
                "(p = 2 \\/ exists t. p = 4 * t + 1)",
                "apply hadmissible",
                "exact hi",
                "exact hp",
                "cases hclass",
                "specialize prime_two_or_one_mod_four_is_sum_of_two_squares p",
                "apply prime_two_or_one_mod_four_is_sum_of_two_squares",
                "exact hclass_left",
                "exact hclass_right",
            ),
            "Any finite product whose decoded factors are prime two or prime one modulo four is constructively a sum of two squares.",
        ),
        spec(
            "represented_factor_product_times_square_is_two_square",
            f"forall b c l m z n. ({square_product}) -> ({square_prefix}) -> "
            f"n = m * (z * z) -> ({_two_square('n', tag='square_result')})",
            (
                "beta_two_square_represented_factor_product",
                "every_natural_square_is_sum_of_two_squares",
                "two_square_representation_multiplicatively_closed",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro m",
                "intro z",
                "intro n",
                "intro hproduct",
                "intro hprefix",
                "intro hdecomposition",
                f"have hbase : {_two_square('m', tag='square_local_base')}",
                "specialize beta_two_square_represented_factor_product b",
                "specialize beta_two_square_represented_factor_product c",
                "specialize beta_two_square_represented_factor_product l",
                "specialize beta_two_square_represented_factor_product m",
                "apply beta_two_square_represented_factor_product",
                "exact hproduct",
                "exact hprefix",
                f"have hsquare : {_two_square('z * z', tag='square_local_factor')}",
                "specialize every_natural_square_is_sum_of_two_squares z",
                "exact every_natural_square_is_sum_of_two_squares",
                "rewrite hdecomposition",
                "specialize two_square_representation_multiplicatively_closed m",
                "specialize two_square_representation_multiplicatively_closed (z * z)",
                "apply two_square_representation_multiplicatively_closed",
                "exact hbase",
                "exact hsquare",
            ),
            "A represented-factor beta product remains constructively representable after multiplication by any explicitly witnessed natural square.",
        ),
        spec(
            "beta_grouped_prime_square_factor_product_is_two_square",
            f"forall b c l n. ({grouped_product}) -> ({grouped_prefix}) -> "
            f"({_two_square('n', tag='grouped_result')})",
            (
                "beta_two_square_represented_factor_product",
                "prime_two_or_one_mod_four_is_sum_of_two_squares",
                "every_natural_square_is_sum_of_two_squares",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hproduct",
                "intro hgrouped",
                "specialize beta_two_square_represented_factor_product b",
                "specialize beta_two_square_represented_factor_product c",
                "specialize beta_two_square_represented_factor_product l",
                "specialize beta_two_square_represented_factor_product n",
                "apply beta_two_square_represented_factor_product",
                "exact hproduct",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                "specialize hgrouped i",
                "specialize hgrouped p",
                "have hblock : "
                f"((({prime('p', tag='ftsf_grouped_local_good')}) /\\ "
                "(p = 2 \\/ exists t. p = 4 * t + 1)) \\/ "
                "exists q t. (("
                f"{prime('q', tag='ftsf_grouped_local_bad')}"
                ") /\\ (q = 4 * t + 3 /\\ p = q * q)))",
                "apply hgrouped",
                "exact hi",
                "exact hp",
                "cases hblock",
                "cases hblock_left",
                "specialize prime_two_or_one_mod_four_is_sum_of_two_squares p",
                "apply prime_two_or_one_mod_four_is_sum_of_two_squares",
                "exact hblock_left_left",
                "exact hblock_left_right",
                "cases hblock_right",
                "cases hblock_right_witness",
                "cases hblock_right_witness_witness",
                "cases hblock_right_witness_witness_right",
                "rewrite hblock_right_witness_witness_right_right",
                "specialize every_natural_square_is_sum_of_two_squares x",
                "exact every_natural_square_is_sum_of_two_squares",
            ),
            "A beta-coded grouped product folds represented prime singletons together with explicit square blocks pairing primes congruent to three modulo four.",
        ),
        spec(
            "beta_product_adjacent_equal_pair_decomposes_as_square",
            f"forall b c l n q. ({pair_product}) -> ({pair_first}) -> "
            f"({pair_second}) -> exists r. (({pair_local_product}) /\\ "
            "n = r * (q * q))",
            ("beta_product_succ_decompose", "beta_at_unique", "mul_assoc"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro q",
                "intro hproduct",
                "intro hfirst",
                "intro hsecond",
                f"have houter : {pair_outer_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose (S l)",
                "specialize beta_product_succ_decompose n",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases houter",
                "cases houter_witness",
                "cases houter_witness_witness",
                "cases houter_witness_witness_right",
                f"have hinner : {pair_inner_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose x1",
                "apply beta_product_succ_decompose",
                "exact houter_witness_witness_right_left",
                "cases hinner",
                "cases hinner_witness",
                "cases hinner_witness_witness",
                "cases hinner_witness_witness_right",
                "have hlast_equal : x = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique x",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact houter_witness_witness_left",
                "exact hsecond",
                "have hfirst_equal : x2 = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact hinner_witness_witness_left",
                "exact hfirst",
                "exists x3",
                "split",
                "exact hinner_witness_witness_right_left",
                "trans x1 * x",
                "exact houter_witness_witness_right_right",
                "trans (x3 * x2) * x",
                "congr",
                "exact hinner_witness_witness_right_right",
                "refl",
                "rewrite hfirst_equal",
                "rewrite hlast_equal",
                "apply mul_assoc",
            ),
            "Two equal adjacent decoded suffix factors collapse constructively to one explicit square times the shorter beta-coded prefix product.",
        ),
        spec(
            "beta_two_square_prefix_append_equal_pair",
            f"forall b c l n q. ({pair_product}) -> ({old_prefix}) -> "
            f"({pair_first}) -> ({pair_second}) -> "
            f"({_two_square('n', tag='pair_result')})",
            (
                "beta_product_adjacent_equal_pair_decomposes_as_square",
                "represented_factor_product_times_square_is_two_square",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro q",
                "intro hproduct",
                "intro hprefix",
                "intro hfirst",
                "intro hsecond",
                "specialize beta_product_adjacent_equal_pair_decomposes_as_square b",
                "specialize beta_product_adjacent_equal_pair_decomposes_as_square c",
                "specialize beta_product_adjacent_equal_pair_decomposes_as_square l",
                "specialize beta_product_adjacent_equal_pair_decomposes_as_square n",
                "specialize beta_product_adjacent_equal_pair_decomposes_as_square q",
                f"have hdecomposition : exists r. (({pair_local_product}) /\\ "
                "n = r * (q * q))",
                "apply beta_product_adjacent_equal_pair_decomposes_as_square",
                "exact hproduct",
                "exact hfirst",
                "exact hsecond",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "specialize represented_factor_product_times_square_is_two_square b",
                "specialize represented_factor_product_times_square_is_two_square c",
                "specialize represented_factor_product_times_square_is_two_square l",
                "specialize represented_factor_product_times_square_is_two_square x",
                "specialize represented_factor_product_times_square_is_two_square q",
                "specialize represented_factor_product_times_square_is_two_square n",
                "apply represented_factor_product_times_square_is_two_square",
                "exact hdecomposition_witness_left",
                "exact hprefix",
                "exact hdecomposition_witness_right",
            ),
            "Appending two equal adjacent decoded factors to any represented beta-coded prefix preserves constructive two-square representability.",
        ),
        spec(
            "positive_number_with_admissible_prime_divisors_is_two_square",
            f"forall n. ~(n = 0) -> ({good_divisors}) -> "
            f"({_two_square('n', tag='canonical_result')})",
            (
                "prime_factorization_existence",
                "beta_all_prime_entry_is_prime",
                "beta_factor_divides_product",
                "beta_admissible_prime_factor_product_is_two_square",
            ),
            (
                "intro n",
                "intro hnonzero",
                "intro hdivisors",
                "specialize prime_factorization_existence n",
                "have hfactorization : exists l b c. "
                f"(({product_relation('b', 'c', 'l', 'n', tag='ftsf_canonical_product')}) "
                "/\\ (("
                f"{all_prime_factor_prefix('b', 'c', 'l', tag='canonical_all_prime')}"
                ") /\\ (forall i. "
                f"({_bound('S i', 'l', tag='canonical_sorted_bound')}) -> "
                "exists p q. (("
                f"{beta_at('b', 'c', 'i', 'p', tag='ftsf_canonical_sorted_left')}"
                ") /\\ (("
                f"{_beta_at_term('b', 'c', 'S i', 'q', tag='ftsf_canonical_sorted_right', avoid=('b', 'c', 'i', 'q'))}"
                ") /\\ (exists h. h + p = q))))))",
                "apply prime_factorization_existence",
                "exact hnonzero",
                "cases hfactorization",
                "cases hfactorization_witness",
                "cases hfactorization_witness_witness",
                "cases hfactorization_witness_witness_witness",
                "cases hfactorization_witness_witness_witness_right",
                "specialize beta_admissible_prime_factor_product_is_two_square x1",
                "specialize beta_admissible_prime_factor_product_is_two_square x2",
                "specialize beta_admissible_prime_factor_product_is_two_square x",
                "specialize beta_admissible_prime_factor_product_is_two_square n",
                "apply beta_admissible_prime_factor_product_is_two_square",
                "exact hfactorization_witness_witness_witness_left",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                f"have hprime : {prime('p', tag='ftsf_canonical_local_prime')}",
                "specialize beta_all_prime_entry_is_prime x1",
                "specialize beta_all_prime_entry_is_prime x2",
                "specialize beta_all_prime_entry_is_prime x",
                "specialize beta_all_prime_entry_is_prime i",
                "specialize beta_all_prime_entry_is_prime p",
                "apply beta_all_prime_entry_is_prime",
                "exact hfactorization_witness_witness_witness_right_left",
                "exact hi",
                "exact hp",
                "split",
                "exact hprime",
                "specialize hdivisors p",
                "apply hdivisors",
                "exact hprime",
                "specialize beta_factor_divides_product x1",
                "specialize beta_factor_divides_product x2",
                "specialize beta_factor_divides_product x",
                "specialize beta_factor_divides_product n",
                "specialize beta_factor_divides_product i",
                "specialize beta_factor_divides_product p",
                "apply beta_factor_divides_product",
                "exact hi",
                "exact hp",
                "exact hfactorization_witness_witness_witness_left",
            ),
            "A positive natural number all of whose prime divisors are two or one modulo four has an explicitly constructed two-square representation via its canonical prime factorization.",
        ),
    )
