"""Isolated sign-factor product boundary for Gauss-style arguments.

The conservative ``sign_factor_prefix`` surface relates a beta bit prefix to
a beta factor prefix: a decoded zero contributes ``1`` and a decoded one
contributes ``r``.  When ``p = S r``, the latter is the natural predecessor
``p - 1`` without adding subtraction to the language.

The candidate below proves the algebraically strongest useful fold boundary:
if the bits have relational count ``e``, the exact factor product equals the
relational power ``r^e``.  All surfaces expand before parsing, no new kernel
symbol is introduced, and this module is not registered publicly.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import (
    beta_at,
    bit_count,
    power_relation,
    product_relation,
)
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    _strictly_below_term,
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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"gspf_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated sign-factor binder captures an argument")
    return names


def _sign_factor_prefix_term(
    bit_code: str,
    bit_scale: str,
    factor_code: str,
    factor_scale: str,
    predecessor: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, bit = _binders(tag, variables, ("index", "bit"))
    owned = variables + (index, bit)
    bound = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_bound",
        variables=owned,
    )
    decoded_bit = beta_at(
        bit_code,
        bit_scale,
        index,
        bit,
        tag=f"gspf_{tag}_bit",
    )
    factor_one = _beta_at_term(
        factor_code,
        factor_scale,
        index,
        "1",
        tag=f"gspf_{tag}_one",
        variables=owned,
    )
    factor_predecessor = beta_at(
        factor_code,
        factor_scale,
        index,
        predecessor,
        tag=f"gspf_{tag}_predecessor",
    )
    return (
        f"forall {index} {bit}. ({bound}) -> ({decoded_bit}) -> "
        f"((({bit} = 0) /\\ ({factor_one})) \\/ "
        f"(({bit} = 1) /\\ ({factor_predecessor})))"
    )


def sign_factor_prefix(
    bit_code: str,
    bit_scale: str,
    factor_code: str,
    factor_scale: str,
    predecessor: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand the bit-to-``1``/``predecessor`` factor relation."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (bit_code, "bit code"),
            (bit_scale, "bit scale"),
            (factor_code, "factor code"),
            (factor_scale, "factor scale"),
            (predecessor, "predecessor"),
            (length, "prefix length"),
        )
    )
    return _sign_factor_prefix_term(
        bit_code,
        bit_scale,
        factor_code,
        factor_scale,
        predecessor,
        length,
        tag=tag,
        variables=variables,
    )


def sign_factor_successor_prefix(
    bit_code: str,
    bit_scale: str,
    factor_code: str,
    factor_scale: str,
    predecessor: str,
    length_predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand the same relation at compound length ``S length_predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (bit_code, "bit code"),
            (bit_scale, "bit scale"),
            (factor_code, "factor code"),
            (factor_scale, "factor scale"),
            (predecessor, "predecessor"),
            (length_predecessor, "length predecessor"),
        )
    )
    return _sign_factor_prefix_term(
        bit_code,
        bit_scale,
        factor_code,
        factor_scale,
        predecessor,
        f"S {length_predecessor}",
        tag=tag,
        variables=variables,
    )


def make_gauss_sign_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the prefix restriction and exact sign-product fold specs."""

    successor_signs = sign_factor_successor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="drop_successor"
    )
    prefix_signs = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="drop_prefix"
    )

    count = bit_count("sb", "sc", "l", "e", tag="sign_product_count")
    signs = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="sign_product_signs"
    )
    product = product_relation(
        "fb", "fc", "l", "F", tag="sign_product_product"
    )
    power = power_relation("r", "e", "R", tag="sign_product_power")

    successor_count = bit_count(
        "sb", "sc", "S_l", "e", tag="sign_product_successor_count"
    )
    last_bit = beta_at(
        "sb", "sc", "l", "a", tag="sign_product_last_bit"
    )
    prefix_count = bit_count(
        "sb", "sc", "l", "k", tag="sign_product_prefix_count"
    )
    count_decomposition = (
        f"exists a k. ({last_bit}) /\\ (({prefix_count}) /\\ "
        f"((a = 0 \\/ a = 1) /\\ e = k + a))"
    )

    successor_product = product_relation(
        "fb", "fc", "S_l", "F", tag="sign_product_successor_product"
    )
    last_factor = beta_at(
        "fb", "fc", "l", "f", tag="sign_product_last_factor"
    )
    prefix_product = product_relation(
        "fb", "fc", "l", "G", tag="sign_product_prefix_product"
    )
    product_decomposition = (
        f"exists f G. ({last_factor}) /\\ "
        f"(({prefix_product}) /\\ F = G * f)"
    )
    successor_sign_relation = sign_factor_successor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="sign_product_successor_signs"
    )
    restricted_sign_relation = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="sign_product_restricted_signs"
    )
    last_sign_case = (
        f"((x = 0) /\\ "
        f"({_beta_at_term('fb', 'fc', 'l', '1', tag='sign_product_last_one', variables=('sb', 'sc', 'fb', 'fc', 'r', 'l', 'e', 'F', 'R', 'a', 'k', 'f', 'G'))})) \\/ "
        f"((x = 1) /\\ ({beta_at('fb', 'fc', 'l', 'r', tag='sign_product_last_predecessor')}))"
    )
    predecessor_power = power_relation(
        "r", "x1", "W", tag="sign_product_predecessor_power"
    )
    power_decomposition = (
        f"exists W. ({predecessor_power}) /\\ R = W * r"
    )

    return (
        spec(
            "beta_sign_factor_prefix_drop_last",
            "forall sb sc fb fc r l. "
            f"({successor_signs}) -> ({prefix_signs})",
            ("le_succ",),
            (
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro r",
                "intro l",
                "intro hsigns",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hsigns i",
                "specialize hsigns a",
                "apply hsigns",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
            ),
            "Dropping the final position preserves the bit-to-sign-factor relation.",
        ),
        spec(
            "beta_sign_factor_product_power",
            "forall sb sc fb fc r l e F R. "
            f"({count}) -> ({signs}) -> ({product}) -> ({power}) -> F = R",
            (
                "bit_count_zero",
                "bit_count_succ_decompose",
                "beta_product_zero",
                "beta_product_succ_decompose",
                "pow_zero",
                "pow_successor_decompose",
                "beta_sign_factor_prefix_drop_last",
                "beta_at_unique",
                "le_refl",
                "mul_one",
            ),
            (
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro r",
                "induction l",
                "intro e",
                "intro F",
                "intro R",
                "intro hcount",
                "intro hsigns",
                "intro hproduct",
                "intro hpower",
                "have he0 : e = 0",
                "specialize bit_count_zero sb",
                "specialize bit_count_zero sc",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero e",
                "apply bit_count_zero",
                "refl",
                "exact hcount",
                "have hF1 : F = 1",
                "specialize beta_product_zero fb",
                "specialize beta_product_zero fc",
                "specialize beta_product_zero F",
                "apply beta_product_zero",
                "exact hproduct",
                "have hR1 : R = 1",
                "specialize pow_zero r",
                "specialize pow_zero e",
                "specialize pow_zero R",
                "apply pow_zero",
                "exact he0",
                "exact hpower",
                "trans 1",
                "exact hF1",
                "symm",
                "exact hR1",
                "intro e",
                "intro F",
                "intro R",
                "intro hcount",
                "intro hsigns",
                "intro hproduct",
                "intro hpower",
                f"have hcount_decomp : {count_decomposition}",
                "specialize bit_count_succ_decompose sb",
                "specialize bit_count_succ_decompose sc",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose e",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hcount_decomp",
                "cases hcount_decomp_witness",
                "cases hcount_decomp_witness_witness",
                "cases hcount_decomp_witness_witness_right",
                "cases hcount_decomp_witness_witness_right_right",
                f"have hproduct_decomp : {product_decomposition}",
                "specialize beta_product_succ_decompose fb",
                "specialize beta_product_succ_decompose fc",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose F",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hproduct_decomp",
                "cases hproduct_decomp_witness",
                "cases hproduct_decomp_witness_witness",
                "cases hproduct_decomp_witness_witness_right",
                f"have hprefix_signs : {restricted_sign_relation}",
                "specialize beta_sign_factor_prefix_drop_last sb",
                "specialize beta_sign_factor_prefix_drop_last sc",
                "specialize beta_sign_factor_prefix_drop_last fb",
                "specialize beta_sign_factor_prefix_drop_last fc",
                "specialize beta_sign_factor_prefix_drop_last r",
                "specialize beta_sign_factor_prefix_drop_last l",
                "apply beta_sign_factor_prefix_drop_last",
                "exact hsigns",
                f"have hlast_case : {last_sign_case}",
                "specialize hsigns l",
                "specialize hsigns x",
                "apply hsigns",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hcount_decomp_witness_witness_left",
                "cases hlast_case",
                "cases hlast_case_left",
                "have hfactor_one : x2 = 1",
                "specialize beta_at_unique fb",
                "specialize beta_at_unique fc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique 1",
                "apply beta_at_unique",
                "exact hproduct_decomp_witness_witness_left",
                "exact hlast_case_left_right",
                "have heqk : e = x1",
                "trans x1 + x",
                "exact hcount_decomp_witness_witness_right_right_right",
                "rewrite hlast_case_left_left",
                "apply PA3",
                "rewrite heqk at hpower",
                "rewrite heqk at hpower",
                "rewrite heqk at hpower",
                "rewrite heqk at hpower",
                "have hprefix_equal : x3 = R",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH R",
                "apply IH",
                "exact hcount_decomp_witness_witness_right_left",
                "exact hprefix_signs",
                "exact hproduct_decomp_witness_witness_right_left",
                "exact hpower",
                "rewrite hproduct_decomp_witness_witness_right_right",
                "rewrite hfactor_one",
                "specialize mul_one x3",
                "rewrite mul_one",
                "exact hprefix_equal",
                "cases hlast_case_right",
                "have hfactor_r : x2 = r",
                "specialize beta_at_unique fb",
                "specialize beta_at_unique fc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique r",
                "apply beta_at_unique",
                "exact hproduct_decomp_witness_witness_left",
                "exact hlast_case_right_right",
                "have hsum : e = x1 + 1",
                "trans x1 + x",
                "exact hcount_decomp_witness_witness_right_right_right",
                "congr",
                "refl",
                "exact hlast_case_right_left",
                "have hsucc : x1 + 1 = S x1",
                "trans S (x1 + 0)",
                "apply PA4",
                "congr",
                "apply PA3",
                "have heqsucc : e = S x1",
                "trans x1 + 1",
                "exact hsum",
                "exact hsucc",
                f"have hpower_decomp : {power_decomposition}",
                "specialize pow_successor_decompose r",
                "specialize pow_successor_decompose x1",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose R",
                "apply pow_successor_decompose",
                "exact heqsucc",
                "exact hpower",
                "cases hpower_decomp",
                "cases hpower_decomp_witness",
                "have hprefix_equal : x3 = x4",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x4",
                "apply IH",
                "exact hcount_decomp_witness_witness_right_left",
                "exact hprefix_signs",
                "exact hproduct_decomp_witness_witness_right_left",
                "exact hpower_decomp_witness_left",
                "rewrite hproduct_decomp_witness_witness_right_right",
                "rewrite hfactor_r",
                "rewrite hprefix_equal",
                "symm",
                "exact hpower_decomp_witness_right",
            ),
            "The product of 1/r sign factors is exactly r to the number of one bits.",
        ),
    )


__all__ = [
    "make_gauss_sign_product_candidate_theorems",
    "sign_factor_prefix",
    "sign_factor_successor_prefix",
]
