"""Isolated beta recoding for pointwise products of two finite prefixes.

For two beta codes and a finite length, this module constructively builds a
third code whose decoded entry at every bounded position is the product of
the two source entries.  It then packages an exact Product for the new code
and connects it to ``beta_product_pointwise_mul_exact``.

All authoring helpers expand to ordinary first-order Peano arithmetic before
parsing.  No multiplication-map, function, list, or fold primitive is added
to the language, and these candidates are not registered publicly.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation
from .finite_pointwise_mul_product_candidate import (
    pointwise_mul_prefix,
    pointwise_mul_successor_prefix,
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
    names = tuple(f"fpmr_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated pointwise-recode binder captures an argument")
    return names


def _beta_at_term(
    code: str,
    scale: str,
    index_term: str,
    value_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, variables, ("height", "quotient"))
    modulus = f"S ((S ({index_term})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value_term}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value_term}))"
    )


def make_finite_pointwise_mul_recode_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build append, finite recoding, and target-product package candidates."""

    alignment_before = pointwise_mul_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="recode_before"
    )
    left_last = beta_at("mb", "mc", "l", "m", tag="recode_left_last")
    right_last = beta_at("sb", "sc", "l", "s", tag="recode_right_last")
    alignment_after = pointwise_mul_successor_prefix(
        "mb", "mc", "sb", "sc", "z", "d", "l", tag="recode_after"
    )
    appended_product = _beta_at_term(
        "x",
        "x1",
        "l",
        "m * s",
        tag="recode_appended_product",
        variables=(
            "mb",
            "mc",
            "sb",
            "sc",
            "tb",
            "tc",
            "l",
            "m",
            "s",
            "x",
            "x1",
        ),
    )
    old_target_entry = beta_at(
        "tb", "tc", "i", "x2", tag="recode_old_target_entry"
    )
    new_old_target_entry = beta_at(
        "x", "x1", "i", "x2", tag="recode_new_old_target_entry"
    )

    alignment_exists = (
        "exists tb tc. "
        f"({pointwise_mul_prefix('mb', 'mc', 'sb', 'sc', 'tb', 'tc', 'l', tag='recode_exists_result')})"
    )
    previous_alignment_exists = (
        "exists tb tc. "
        f"({pointwise_mul_prefix('mb', 'mc', 'sb', 'sc', 'tb', 'tc', 'l', tag='recode_exists_previous')})"
    )
    successor_alignment_exists = (
        "exists tb tc. "
        f"({pointwise_mul_successor_prefix('mb', 'mc', 'sb', 'sc', 'tb', 'tc', 'l', tag='recode_exists_successor')})"
    )

    left_product = product_relation(
        "mb", "mc", "l", "M", tag="recode_package_left_product"
    )
    right_product = product_relation(
        "sb", "sc", "l", "Sprod", tag="recode_package_right_product"
    )
    package_alignment = pointwise_mul_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="recode_package_alignment"
    )
    package_product = product_relation(
        "tb", "tc", "l", "T", tag="recode_package_target_product"
    )
    package_result = (
        "exists tb tc T. "
        f"(({package_alignment}) /\\ (({package_product}) /\\ "
        "T = M * Sprod))"
    )

    return (
        spec(
            "beta_pointwise_mul_prefix_extend",
            "forall mb mc sb sc tb tc l m s. "
            f"({alignment_before}) -> ({left_last}) -> ({right_last}) -> "
            f"exists z d. ({alignment_after})",
            (
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "beta_at_exists",
                "beta_at_unique",
            ),
            (
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro tb",
                "intro tc",
                "intro l",
                "intro m",
                "intro s",
                "intro haligned",
                "intro hm_last",
                "intro hs_last",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend tb",
                "specialize beta_prefix_extend tc",
                "specialize beta_prefix_extend (m * s)",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "intro i",
                "intro a",
                "intro b",
                "intro t",
                "intro hi",
                "intro ha",
                "intro hb",
                "intro ht",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left at ha",
                "rewrite hsplit_left at ha",
                "rewrite hsplit_left at hb",
                "rewrite hsplit_left at hb",
                "rewrite hsplit_left at ht",
                "rewrite hsplit_left at ht",
                "have hma : m = a",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique m",
                "specialize beta_at_unique a",
                "apply beta_at_unique",
                "exact hm_last",
                "exact ha",
                "have hsb : s = b",
                "specialize beta_at_unique sb",
                "specialize beta_at_unique sc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique s",
                "specialize beta_at_unique b",
                "apply beta_at_unique",
                "exact hs_last",
                "exact hb",
                f"have happended : {appended_product}",
                "exact beta_prefix_extend_witness_witness_left",
                "have ht_product : t = m * s",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique l",
                "specialize beta_at_unique t",
                "specialize beta_at_unique (m * s)",
                "apply beta_at_unique",
                "exact ht",
                "exact happended",
                "trans m * s",
                "exact ht_product",
                "congr",
                "exact hma",
                "exact hsb",
                "have hold_exists : exists u. "
                f"({beta_at('tb', 'tc', 'i', 'u', tag='recode_old_target_exists')})",
                "specialize beta_at_exists tb",
                "specialize beta_at_exists tc",
                "specialize beta_at_exists i",
                "exact beta_at_exists",
                "cases hold_exists",
                f"have hnew_old : {new_old_target_entry}",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x2",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_exists_witness",
                "have htx : t = x2",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique t",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact ht",
                "exact hnew_old",
                "have hold_product : x2 = a * b",
                "specialize haligned i",
                "specialize haligned a",
                "specialize haligned b",
                "specialize haligned x2",
                "apply haligned",
                "exact hsplit_right",
                "exact ha",
                "exact hb",
                "exact hold_exists_witness",
                "trans x2",
                "exact htx",
                "exact hold_product",
            ),
            "Append the product of the two final decoded values and preserve all earlier products.",
        ),
        spec(
            "beta_pointwise_mul_prefix_exists",
            "forall mb mc sb sc l. " + alignment_exists,
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_at_exists",
                "beta_pointwise_mul_prefix_extend",
            ),
            (
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "induction l",
                "exists 0",
                "exists 0",
                "intro i",
                "intro a",
                "intro b",
                "intro t",
                "intro hi",
                "intro ha",
                "intro hb",
                "intro ht",
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
                f"have hprevious : {previous_alignment_exists}",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                "have hleft : exists m. "
                f"({beta_at('mb', 'mc', 'l', 'm', tag='recode_exists_left_last')})",
                "specialize beta_at_exists mb",
                "specialize beta_at_exists mc",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hleft",
                "have hright : exists s. "
                f"({beta_at('sb', 'sc', 'l', 's', tag='recode_exists_right_last')})",
                "specialize beta_at_exists sb",
                "specialize beta_at_exists sc",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hright",
                "specialize beta_pointwise_mul_prefix_extend mb",
                "specialize beta_pointwise_mul_prefix_extend mc",
                "specialize beta_pointwise_mul_prefix_extend sb",
                "specialize beta_pointwise_mul_prefix_extend sc",
                "specialize beta_pointwise_mul_prefix_extend x",
                "specialize beta_pointwise_mul_prefix_extend x1",
                "specialize beta_pointwise_mul_prefix_extend l",
                "specialize beta_pointwise_mul_prefix_extend x2",
                "specialize beta_pointwise_mul_prefix_extend x3",
                "apply beta_pointwise_mul_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hleft_witness",
                "exact hright_witness",
            ),
            "Two beta prefixes admit a third beta prefix of their pointwise products.",
        ),
        spec(
            "beta_pointwise_mul_product_exists",
            "forall mb mc sb sc l M Sprod. "
            f"({left_product}) -> ({right_product}) -> ({package_result})",
            (
                "beta_pointwise_mul_prefix_exists",
                "beta_product_exists",
                "beta_product_pointwise_mul_exact",
            ),
            (
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro l",
                "intro M",
                "intro Sprod",
                "intro hM",
                "intro hS",
                "have halignment_exists : exists tb tc. "
                f"({pointwise_mul_prefix('mb', 'mc', 'sb', 'sc', 'tb', 'tc', 'l', tag='recode_package_alignment_exists')})",
                "specialize beta_pointwise_mul_prefix_exists mb",
                "specialize beta_pointwise_mul_prefix_exists mc",
                "specialize beta_pointwise_mul_prefix_exists sb",
                "specialize beta_pointwise_mul_prefix_exists sc",
                "specialize beta_pointwise_mul_prefix_exists l",
                "exact beta_pointwise_mul_prefix_exists",
                "cases halignment_exists",
                "cases halignment_exists_witness",
                "have htarget_product_exists : exists T. "
                f"({product_relation('x', 'x1', 'l', 'T', tag='recode_package_target_exists')})",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists l",
                "exact beta_product_exists",
                "cases htarget_product_exists",
                "have hequal : x2 = M * Sprod",
                "specialize beta_product_pointwise_mul_exact mb",
                "specialize beta_product_pointwise_mul_exact mc",
                "specialize beta_product_pointwise_mul_exact sb",
                "specialize beta_product_pointwise_mul_exact sc",
                "specialize beta_product_pointwise_mul_exact x",
                "specialize beta_product_pointwise_mul_exact x1",
                "specialize beta_product_pointwise_mul_exact l",
                "specialize beta_product_pointwise_mul_exact M",
                "specialize beta_product_pointwise_mul_exact Sprod",
                "specialize beta_product_pointwise_mul_exact x2",
                "apply beta_product_pointwise_mul_exact",
                "exact halignment_exists_witness_witness",
                "exact hM",
                "exact hS",
                "exact htarget_product_exists_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact halignment_exists_witness_witness",
                "split",
                "exact htarget_product_exists_witness",
                "exact hequal",
            ),
            "The pointwise-product code has a Product equal to the product of the two source Products.",
        ),
    )


__all__ = ["make_finite_pointwise_mul_recode_candidate_theorems"]
