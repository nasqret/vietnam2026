"""Offset contribution intervals and the checked three-range B5 split.

``ContributionInterval(n,a,l,z)`` is the Product of ``l`` complete
prime-power contribution choices for ``n`` at global positions ``a+i``.
The final row splits one complete contribution Product first at ``q`` and
then at ``s``, using explicit additive gaps.  Every readable relation is
expanded before parsing; importing this module grants no theorem authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_prime_contribution_candidate import (
    _prime_contribution_choice_term,
    _prime_contribution_prefix_term,
    _prime_contribution_product_term,
)
from .bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _render_term,
    _validated_context,
)
from .finite_fold_surface import _product_relation_term


PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXTEND = (
    "prime_contribution_interval_prefix_extend"
)
PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS = (
    "prime_contribution_interval_prefix_exists"
)
PRIME_CONTRIBUTION_INTERVAL_PREFIX_TRANSPORT_ENTRY = (
    "prime_contribution_interval_prefix_transport_entry"
)
PRIME_CONTRIBUTION_INTERVAL_EXISTS = "prime_contribution_interval_exists"
PRIME_CONTRIBUTION_INTERVAL_FUNCTIONAL = (
    "prime_contribution_interval_functional"
)
PRIME_CONTRIBUTION_INTERVAL_PREFIX_SHIFT = (
    "prime_contribution_interval_prefix_shift"
)
PRIME_CONTRIBUTION_PREFIX_RESTRICT_ADD = (
    "prime_contribution_prefix_restrict_add"
)
PRIME_CONTRIBUTION_PREFIX_INTERVAL_SPLIT = (
    "prime_contribution_prefix_interval_split"
)
PRIME_CONTRIBUTION_PRODUCT_LENGTH_EQ_TRANSPORT = (
    "prime_contribution_product_length_eq_transport"
)
PRIME_CONTRIBUTION_THREE_RANGE_SPLIT = (
    "prime_contribution_three_range_split"
)


def _interval_prefix_term(
    number: str,
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand an offset complete-contribution selector prefix."""

    context = _validated_context(variables)
    rendered = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "contribution interval number"),
            (offset, "contribution interval offset"),
            (code, "contribution interval code"),
            (scale, "contribution interval scale"),
            (length, "contribution interval length"),
        )
    )
    number_term, offset_term, code_term, scale_term, length_term = rendered
    index, value = _binders(tag, context, ("index", "value"))
    local = context + (index, value)
    bound = _lt_term(
        index,
        length_term,
        tag=f"{tag}_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code_term,
        scale_term,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _prime_contribution_choice_term(
        number_term,
        f"{offset_term} + {index}",
        value,
        tag=f"{tag}_choice",
        variables=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _interval_relation_term(
    number: str,
    offset: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand one offset contribution Product relation."""

    context = _validated_context(variables)
    number_term, offset_term, length_term, value_term = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "contribution interval number"),
            (offset, "contribution interval offset"),
            (length, "contribution interval length"),
            (value, "contribution interval value"),
        )
    )
    code, scale = _binders(tag, context, ("code", "scale"))
    local = context + (code, scale)
    prefix = _interval_prefix_term(
        number_term,
        offset_term,
        code,
        scale,
        length_term,
        tag=f"{tag}_prefix",
        variables=local,
    )
    product = _product_relation_term(
        code,
        scale,
        length_term,
        value_term,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def make_bertrand_b5_contribution_split_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered contribution interval split rows."""

    extend_variables = ("n", "a", "b", "c", "l")
    extend_before = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "l",
        tag="bpcifpe_before",
        variables=extend_variables,
    )
    extend_after = _interval_prefix_term(
        "n",
        "a",
        "d",
        "e",
        "S l",
        tag="bpcifpe_after",
        variables=extend_variables + ("d", "e"),
    )
    extend_choice = _prime_contribution_choice_term(
        "n",
        "a + l",
        "x",
        tag="bpcifpe_last_choice",
        variables=extend_variables + ("x",),
    )
    extend_avoid = extend_variables + ("x", "d", "e", "i", "p")
    extend_append = _beta_at_term(
        "d", "e", "l", "x", tag="bpcifpe_append", avoid=extend_avoid
    )
    extend_old_bound = _lt_term(
        "i", "l", tag="bpcifpe_old_bound", avoid=extend_avoid
    )
    extend_old_decoded = _beta_at_term(
        "b", "c", "i", "p", tag="bpcifpe_old", avoid=extend_avoid
    )
    extend_new_decoded = _beta_at_term(
        "d", "e", "i", "p", tag="bpcifpe_new", avoid=extend_avoid
    )
    extend_relation = (
        f"exists d e. (({extend_append}) /\\ forall i p. "
        f"({extend_old_bound}) -> ({extend_old_decoded}) -> "
        f"({extend_new_decoded}))"
    )
    extend_hold_variables = (
        "n",
        "a",
        "b",
        "c",
        "l",
        "x",
        "x1",
        "x2",
        "i",
        "p",
    )
    extend_hold_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpcifpe_hold_decoded",
        avoid=extend_hold_variables,
    )
    extend_hold_choice = _prime_contribution_choice_term(
        "n",
        "a + i",
        "p",
        tag="bpcifpe_hold_choice",
        variables=extend_hold_variables,
    )
    extend_old_entry = (
        f"exists p. (({extend_hold_decoded}) /\\ ({extend_hold_choice}))"
    )

    prefix_exists = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "l",
        tag="bpcipx_result",
        variables=("n", "a", "l", "b", "c"),
    )
    prefix_previous = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "l",
        tag="bpcipx_previous",
        variables=("n", "a", "l", "b", "c"),
    )
    prefix_successor = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "S l",
        tag="bpcipx_successor",
        variables=("n", "a", "l", "b", "c"),
    )

    transport_variables = ("n", "a", "b", "c", "d", "e", "l", "i", "p")
    transport_left = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "l",
        tag="bpcipt_left",
        variables=transport_variables,
    )
    transport_right = _interval_prefix_term(
        "n",
        "a",
        "d",
        "e",
        "l",
        tag="bpcipt_right",
        variables=transport_variables,
    )
    transport_bound = _lt_term(
        "i", "l", tag="bpcipt_bound", avoid=transport_variables
    )
    transport_source = _beta_at_term(
        "b", "c", "i", "p", tag="bpcipt_source", avoid=transport_variables
    )
    transport_target = _beta_at_term(
        "d", "e", "i", "p", tag="bpcipt_target", avoid=transport_variables
    )
    left_entry_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "q",
        tag="bpcipt_left_entry",
        avoid=transport_variables + ("q",),
    )
    left_entry_choice = _prime_contribution_choice_term(
        "n",
        "a + i",
        "q",
        tag="bpcipt_left_choice",
        variables=transport_variables + ("q",),
    )
    left_entry = (
        f"exists q. (({left_entry_decoded}) /\\ ({left_entry_choice}))"
    )
    right_entry_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "r",
        tag="bpcipt_right_entry",
        avoid=transport_variables + ("q", "r"),
    )
    right_entry_choice = _prime_contribution_choice_term(
        "n",
        "a + i",
        "r",
        tag="bpcipt_right_choice",
        variables=transport_variables + ("q", "r"),
    )
    right_entry = (
        f"exists r. (({right_entry_decoded}) /\\ ({right_entry_choice}))"
    )

    exists_relation = _interval_relation_term(
        "n",
        "a",
        "l",
        "z",
        tag="bpci_exists",
        variables=("n", "a", "l", "z"),
    )
    exists_prefix = _interval_prefix_term(
        "n",
        "a",
        "b",
        "c",
        "l",
        tag="bpci_exists_prefix",
        variables=("n", "a", "l", "b", "c"),
    )
    exists_product = _product_relation_term(
        "x",
        "x1",
        "l",
        "z",
        tag="bpci_exists_product",
        avoid=("n", "a", "l", "x", "x1", "z"),
    )

    functional_variables = ("n", "a", "l", "x", "y")
    functional_left = _interval_relation_term(
        "n",
        "a",
        "l",
        "x",
        tag="bpci_functional_left",
        variables=functional_variables,
    )
    functional_right = _interval_relation_term(
        "n",
        "a",
        "l",
        "y",
        tag="bpci_functional_right",
        variables=functional_variables,
    )
    functional_local = functional_variables + (
        "x1",
        "x2",
        "x3",
        "x4",
        "i",
        "p",
    )
    functional_bound = _lt_term(
        "i", "l", tag="bpci_functional_bound", avoid=functional_local
    )
    functional_source_entry = _beta_at_term(
        "x1",
        "x2",
        "i",
        "p",
        tag="bpci_functional_source_entry",
        avoid=functional_local,
    )
    functional_target_entry = _beta_at_term(
        "x3",
        "x4",
        "i",
        "p",
        tag="bpci_functional_target_entry",
        avoid=functional_local,
    )
    functional_transport = _product_relation_term(
        "x3",
        "x4",
        "l",
        "x",
        tag="bpci_functional_transport",
        avoid=functional_variables + ("x1", "x2", "x3", "x4"),
    )

    shift_variables = ("n", "a", "b", "c", "d", "e", "l", "i", "p")
    shift_source_prefix = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "a + l",
        tag="bpcips_source",
        variables=shift_variables,
    )
    shift_interval_prefix = _interval_prefix_term(
        "n",
        "a",
        "d",
        "e",
        "l",
        tag="bpcips_interval",
        variables=shift_variables,
    )
    shift_bound = _lt_term(
        "i", "l", tag="bpcips_bound", avoid=shift_variables
    )
    shift_source_entry = _beta_at_term(
        "b",
        "c",
        "a + i",
        "p",
        tag="bpcips_source_entry",
        avoid=shift_variables,
    )
    shift_target_entry = _beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpcips_target_entry",
        avoid=shift_variables,
    )
    shift_source_bound = _lt_term(
        "a + i", "a + l", tag="bpcips_source_bound", avoid=shift_variables
    )
    (shift_gap,) = _binders(
        "bpcips_shifted_bound", shift_variables, ("gap",)
    )
    shift_source_bound_raw = (
        f"exists {shift_gap}. {shift_gap} + (a + S i) = a + l"
    )
    shift_source_local_decoded = _beta_at_term(
        "b",
        "c",
        "a + i",
        "q",
        tag="bpcips_source_local",
        avoid=shift_variables + ("q",),
    )
    shift_source_local_choice = _prime_contribution_choice_term(
        "n",
        "a + i",
        "q",
        tag="bpcips_source_choice",
        variables=shift_variables + ("q",),
    )
    shift_source_local = (
        f"exists q. (({shift_source_local_decoded}) /\\ "
        f"({shift_source_local_choice}))"
    )
    shift_interval_local_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "r",
        tag="bpcips_interval_local",
        avoid=shift_variables + ("q", "r"),
    )
    shift_interval_local_choice = _prime_contribution_choice_term(
        "n",
        "a + i",
        "r",
        tag="bpcips_interval_choice",
        variables=shift_variables + ("q", "r"),
    )
    shift_interval_local = (
        f"exists r. (({shift_interval_local_decoded}) /\\ "
        f"({shift_interval_local_choice}))"
    )

    restrict_variables = ("n", "a", "b", "c", "l")
    restrict_source = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "a + l",
        tag="bpcpra_source",
        variables=restrict_variables,
    )
    restrict_target = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "a",
        tag="bpcpra_target",
        variables=restrict_variables,
    )

    split_variables = ("n", "a", "l", "z")
    split_source = _prime_contribution_product_term(
        "n",
        "a + l",
        "z",
        tag="bpcpis_source",
        variables=split_variables,
    )
    split_prefix = _prime_contribution_product_term(
        "n",
        "a",
        "x",
        tag="bpcpis_prefix",
        variables=split_variables + ("x", "y"),
    )
    split_interval = _interval_relation_term(
        "n",
        "a",
        "l",
        "y",
        tag="bpcpis_interval",
        variables=split_variables + ("x", "y"),
    )
    split_result = (
        f"exists x y. ({split_prefix}) /\\ "
        f"(({split_interval}) /\\ z = x * y)"
    )
    split_restricted = _prime_contribution_prefix_term(
        "n",
        "x",
        "x1",
        "a",
        tag="bpcpis_restricted",
        variables=split_variables + ("x", "x1"),
    )
    split_interval_prefix = _interval_prefix_term(
        "n",
        "a",
        "d",
        "e",
        "l",
        tag="bpcpis_interval_prefix",
        variables=split_variables + ("x", "x1", "d", "e"),
    )
    split_shift_variables = (
        "n",
        "a",
        "l",
        "z",
        "x",
        "x1",
        "x2",
        "x3",
        "i",
        "p",
    )
    split_shift_bound = _lt_term(
        "i", "l", tag="bpcpis_shift_bound", avoid=split_shift_variables
    )
    split_shift_source = _beta_at_term(
        "x",
        "x1",
        "a + i",
        "p",
        tag="bpcpis_shift_source",
        avoid=split_shift_variables,
    )
    split_shift_target = _beta_at_term(
        "x2",
        "x3",
        "i",
        "p",
        tag="bpcpis_shift_target",
        avoid=split_shift_variables,
    )
    split_shift = (
        "forall i p. "
        f"({split_shift_bound}) -> ({split_shift_source}) -> "
        f"({split_shift_target})"
    )
    split_prefix_product = _product_relation_term(
        "x",
        "x1",
        "a",
        "p",
        tag="bpcpis_prefix_product",
        avoid=split_variables + ("x", "x1", "d", "e", "p", "q"),
    )
    split_interval_product = _product_relation_term(
        "x2",
        "x3",
        "l",
        "q",
        tag="bpcpis_interval_product",
        avoid=split_variables + ("x", "x1", "x2", "x3", "p", "q"),
    )
    split_products = (
        f"exists p q. ({split_prefix_product}) /\\ "
        f"(({split_interval_product}) /\\ z = p * q)"
    )

    transport_variables = ("n", "l", "m", "z")
    length_source = _prime_contribution_product_term(
        "n",
        "l",
        "z",
        tag="bpcplet_source",
        variables=transport_variables,
    )
    length_target = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcplet_target",
        variables=transport_variables,
    )

    three_variables = ("n", "s", "q", "g", "h", "z")
    three_source = _prime_contribution_product_term(
        "n",
        "n + n",
        "z",
        tag="bpctrs_source",
        variables=three_variables,
    )
    three_small = _prime_contribution_product_term(
        "n",
        "s",
        "x",
        tag="bpctrs_small",
        variables=three_variables + ("x", "y", "w"),
    )
    three_middle = _interval_relation_term(
        "n",
        "s",
        "g",
        "y",
        tag="bpctrs_middle",
        variables=three_variables + ("x", "y", "w"),
    )
    three_high = _interval_relation_term(
        "n",
        "q",
        "h",
        "w",
        tag="bpctrs_high",
        variables=three_variables + ("x", "y", "w"),
    )
    three_result = (
        f"exists x y w. ({three_small}) /\\ (({three_middle}) /\\ "
        f"(({three_high}) /\\ z = (x * y) * w))"
    )
    three_outer_source = _prime_contribution_product_term(
        "n",
        "q + h",
        "z",
        tag="bpctrs_outer_source",
        variables=three_variables,
    )
    three_outer_prefix = _prime_contribution_product_term(
        "n",
        "q",
        "x",
        tag="bpctrs_outer_prefix",
        variables=three_variables + ("x", "w"),
    )
    three_outer_high = _interval_relation_term(
        "n",
        "q",
        "h",
        "w",
        tag="bpctrs_outer_high",
        variables=three_variables + ("x", "w"),
    )
    three_outer = (
        f"exists x w. ({three_outer_prefix}) /\\ "
        f"(({three_outer_high}) /\\ z = x * w)"
    )
    three_inner_source = _prime_contribution_product_term(
        "n",
        "s + g",
        "x",
        tag="bpctrs_inner_source",
        variables=three_variables + ("x", "w"),
    )
    three_inner_small = _prime_contribution_product_term(
        "n",
        "s",
        "u",
        tag="bpctrs_inner_small",
        variables=three_variables + ("x", "w", "u", "v"),
    )
    three_inner_middle = _interval_relation_term(
        "n",
        "s",
        "g",
        "v",
        tag="bpctrs_inner_middle",
        variables=three_variables + ("x", "w", "u", "v"),
    )
    three_inner = (
        f"exists u v. ({three_inner_small}) /\\ "
        f"(({three_inner_middle}) /\\ x = u * v)"
    )

    return (
        spec(
            PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXTEND,
            "forall n a b c l. "
            f"({extend_before}) -> exists d e. ({extend_after})",
            (
                "prime_contribution_choice_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro l",
                "intro hprefix",
                f"have hchoice : exists x. ({extend_choice})",
                "specialize prime_contribution_choice_exists n",
                "specialize prime_contribution_choice_exists (a + l)",
                "exact prime_contribution_choice_exists",
                "cases hchoice",
                f"have hext : {extend_relation}",
                "apply beta_prefix_extend",
                "cases hext",
                "cases hext_witness",
                "cases hext_witness_witness",
                "exists x1",
                "exists x2",
                "intro i",
                "intro hi",
                r"have hsplit : i = l \/ exists gap. gap + S i = l",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exists x",
                "split",
                "exact hext_witness_witness_left",
                "exact hchoice_witness",
                f"have hold : {extend_old_entry}",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "exists x3",
                "split",
                "apply hext_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "Append one contribution choice to an offset interval prefix.",
        ),
        spec(
            PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS,
            f"forall n a l. exists b c. ({prefix_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXTEND,
            ),
            (
                "intro n",
                "intro a",
                "induction l",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "apply succ_ne_zero",
                "exact hsi",
                f"have hprevious : exists b c. ({prefix_previous})",
                "exact IH",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hnext : exists b c. ({prefix_successor})",
                "apply prime_contribution_interval_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every number, offset, and length has a contribution prefix.",
        ),
        spec(
            PRIME_CONTRIBUTION_INTERVAL_PREFIX_TRANSPORT_ENTRY,
            "forall n a b c d e l. "
            f"({transport_left}) -> ({transport_right}) -> forall i p. "
            f"({transport_bound}) -> ({transport_source}) -> "
            f"({transport_target})",
            ("beta_at_unique", "prime_contribution_choice_functional"),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro l",
                "intro hleft",
                "intro hright",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                f"have hleft_entry : {left_entry}",
                "apply hleft",
                "exact hi",
                "cases hleft_entry",
                "cases hleft_entry_witness",
                f"have hright_entry : {right_entry}",
                "apply hright",
                "exact hi",
                "cases hright_entry",
                "cases hright_entry_witness",
                "have hpq : p = x",
                "apply beta_at_unique",
                "exact hp",
                "exact hleft_entry_witness_left",
                "have hqr : x = x1",
                "specialize prime_contribution_choice_functional n",
                "specialize prime_contribution_choice_functional (a + i)",
                "specialize prime_contribution_choice_functional x",
                "specialize prime_contribution_choice_functional x1",
                "apply prime_contribution_choice_functional",
                "exact hleft_entry_witness_right",
                "exact hright_entry_witness_right",
                "have hpr : p = x1",
                "trans x",
                "exact hpq",
                "exact hqr",
                "rewrite hpr",
                "rewrite hpr",
                "exact hright_entry_witness_left",
            ),
            "Independently coded contribution intervals decode the same entry.",
        ),
        spec(
            PRIME_CONTRIBUTION_INTERVAL_EXISTS,
            f"forall n a l. exists z. ({exists_relation})",
            (
                "beta_product_exists",
                PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS,
            ),
            (
                "intro n",
                "intro a",
                "intro l",
                f"have hprefix : exists b c. ({exists_prefix})",
                "apply prime_contribution_interval_prefix_exists",
                "cases hprefix",
                "cases hprefix_witness",
                f"have hproduct : exists z. ({exists_product})",
                "apply beta_product_exists",
                "cases hproduct",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "exact hproduct_witness",
            ),
            "Every contribution interval has a relational Product value.",
        ),
        spec(
            PRIME_CONTRIBUTION_INTERVAL_FUNCTIONAL,
            "forall n a l x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y",
            (
                "beta_product_transport_prefix",
                "beta_product_functional",
                PRIME_CONTRIBUTION_INTERVAL_PREFIX_TRANSPORT_ENTRY,
            ),
            (
                "intro n",
                "intro a",
                "intro l",
                "intro x",
                "intro y",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_witness",
                "cases hleft_witness_witness",
                "cases hright",
                "cases hright_witness",
                "cases hright_witness_witness",
                "have hpres : forall i p. "
                f"({functional_bound}) -> ({functional_source_entry}) -> "
                f"({functional_target_entry})",
                "specialize prime_contribution_interval_prefix_transport_entry n",
                "specialize prime_contribution_interval_prefix_transport_entry a",
                "specialize prime_contribution_interval_prefix_transport_entry x1",
                "specialize prime_contribution_interval_prefix_transport_entry x2",
                "specialize prime_contribution_interval_prefix_transport_entry x3",
                "specialize prime_contribution_interval_prefix_transport_entry x4",
                "specialize prime_contribution_interval_prefix_transport_entry l",
                "apply prime_contribution_interval_prefix_transport_entry",
                "exact hleft_witness_witness_left",
                "exact hright_witness_witness_left",
                f"have htransport : {functional_transport}",
                "apply beta_product_transport_prefix",
                "exact hleft_witness_witness_right",
                "exact hpres",
                "cases htransport",
                "cases htransport_witness",
                "cases hright_witness_witness_right",
                "cases hright_witness_witness_right_witness",
                "apply beta_product_functional",
                "exact htransport_witness_witness",
                "exact hright_witness_witness_right_witness_witness",
            ),
            "A fixed contribution interval has one extensional Product value.",
        ),
        spec(
            PRIME_CONTRIBUTION_INTERVAL_PREFIX_SHIFT,
            "forall n a b c d e l. "
            f"({shift_source_prefix}) -> ({shift_interval_prefix}) -> "
            f"forall i p. ({shift_bound}) -> ({shift_source_entry}) -> "
            f"({shift_target_entry})",
            (
                "add_le_add_left",
                "beta_at_unique",
                "prime_contribution_choice_functional",
            ),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro l",
                "intro hsource",
                "intro hinterval",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                f"have hsource_bound_raw : {shift_source_bound_raw}",
                "specialize add_le_add_left (S i)",
                "specialize add_le_add_left l",
                "specialize add_le_add_left a",
                "apply add_le_add_left",
                "exact hi",
                "have hadd_succ : a + S i = S (a + i)",
                "apply PA4",
                "rewrite hadd_succ at hsource_bound_raw",
                f"have hsource_bound : {shift_source_bound}",
                "exact hsource_bound_raw",
                f"have hsource_entry : {shift_source_local}",
                "apply hsource",
                "exact hsource_bound",
                "cases hsource_entry",
                "cases hsource_entry_witness",
                f"have hinterval_entry : {shift_interval_local}",
                "apply hinterval",
                "exact hi",
                "cases hinterval_entry",
                "cases hinterval_entry_witness",
                "have hpq : p = x",
                "apply beta_at_unique",
                "exact hp",
                "exact hsource_entry_witness_left",
                "have hqr : x = x1",
                "specialize prime_contribution_choice_functional n",
                "specialize prime_contribution_choice_functional (a + i)",
                "specialize prime_contribution_choice_functional x",
                "specialize prime_contribution_choice_functional x1",
                "apply prime_contribution_choice_functional",
                "exact hsource_entry_witness_right",
                "exact hinterval_entry_witness_right",
                "have hpr : p = x1",
                "trans x",
                "exact hpq",
                "exact hqr",
                "rewrite hpr",
                "rewrite hpr",
                "exact hinterval_entry_witness_left",
            ),
            "Align a full contribution prefix with its independent suffix.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_RESTRICT_ADD,
            "forall n a b c l. "
            f"({restrict_source}) -> ({restrict_target})",
            ("le_add_right", "lt_of_lt_of_le"),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro l",
                "intro hsource",
                "intro i",
                "intro hi",
                "apply hsource",
                "specialize lt_of_lt_of_le i",
                "specialize lt_of_lt_of_le a",
                "specialize lt_of_lt_of_le (a + l)",
                "apply lt_of_lt_of_le",
                "exact hi",
                "specialize le_add_right a",
                "specialize le_add_right l",
                "exact le_add_right",
            ),
            "Restrict a contribution prefix of length a+l to length a.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_INTERVAL_SPLIT,
            "forall n a l z. "
            f"({split_source}) -> ({split_result})",
            (
                "beta_product_prefix_suffix_split",
                PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS,
                PRIME_CONTRIBUTION_INTERVAL_PREFIX_SHIFT,
                PRIME_CONTRIBUTION_PREFIX_RESTRICT_ADD,
            ),
            (
                "intro n",
                "intro a",
                "intro l",
                "intro z",
                "intro hproduct",
                "cases hproduct",
                "cases hproduct_witness",
                "cases hproduct_witness_witness",
                f"have hrestricted : {split_restricted}",
                "apply prime_contribution_prefix_restrict_add",
                "exact hproduct_witness_witness_left",
                f"have hinterval : exists d e. ({split_interval_prefix})",
                "apply prime_contribution_interval_prefix_exists",
                "cases hinterval",
                "cases hinterval_witness",
                f"have hshift : {split_shift}",
                "specialize prime_contribution_interval_prefix_shift n",
                "specialize prime_contribution_interval_prefix_shift a",
                "specialize prime_contribution_interval_prefix_shift x",
                "specialize prime_contribution_interval_prefix_shift x1",
                "specialize prime_contribution_interval_prefix_shift x2",
                "specialize prime_contribution_interval_prefix_shift x3",
                "specialize prime_contribution_interval_prefix_shift l",
                "apply prime_contribution_interval_prefix_shift",
                "exact hproduct_witness_witness_left",
                "exact hinterval_witness_witness",
                f"have hsplit : {split_products}",
                "specialize beta_product_prefix_suffix_split x",
                "specialize beta_product_prefix_suffix_split x1",
                "specialize beta_product_prefix_suffix_split x2",
                "specialize beta_product_prefix_suffix_split x3",
                "specialize beta_product_prefix_suffix_split a",
                "specialize beta_product_prefix_suffix_split l",
                "specialize beta_product_prefix_suffix_split z",
                "apply beta_product_prefix_suffix_split",
                "exact hshift",
                "exact hproduct_witness_witness_right",
                "cases hsplit",
                "cases hsplit_witness",
                "cases hsplit_witness_witness",
                "cases hsplit_witness_witness_right",
                "exists x4",
                "exists x5",
                "split",
                "exists x",
                "exists x1",
                "split",
                "exact hrestricted",
                "exact hsplit_witness_witness_left",
                "split",
                "exists x2",
                "exists x3",
                "split",
                "exact hinterval_witness_witness",
                "exact hsplit_witness_witness_right_left",
                "exact hsplit_witness_witness_right_right",
            ),
            "Split a contribution Product into prefix and offset interval.",
        ),
        spec(
            PRIME_CONTRIBUTION_PRODUCT_LENGTH_EQ_TRANSPORT,
            "forall n l m z. l = m -> "
            f"({length_source}) -> ({length_target})",
            (),
            (
                "intro n",
                "intro l",
                "intro m",
                "intro z",
                "intro hlength",
                "intro hsource",
                "rewrite hlength at hsource",
                "rewrite hlength at hsource",
                "rewrite hlength at hsource",
                "rewrite hlength at hsource",
                "exact hsource",
            ),
            "Transport only the length carrier of a contribution Product.",
        ),
        spec(
            PRIME_CONTRIBUTION_THREE_RANGE_SPLIT,
            "forall n s q g h z. s + g = q -> q + h = n + n -> "
            f"({three_source}) -> ({three_result})",
            (
                PRIME_CONTRIBUTION_PRODUCT_LENGTH_EQ_TRANSPORT,
                PRIME_CONTRIBUTION_PREFIX_INTERVAL_SPLIT,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro g",
                "intro h",
                "intro z",
                "intro hfirst",
                "intro hsecond",
                "intro hsource",
                "have hsecond_reverse : n + n = q + h",
                "symm",
                "exact hsecond",
                f"have houter_source : {three_outer_source}",
                "specialize prime_contribution_product_length_eq_transport n",
                "specialize prime_contribution_product_length_eq_transport (n + n)",
                "specialize prime_contribution_product_length_eq_transport (q + h)",
                "specialize prime_contribution_product_length_eq_transport z",
                "apply prime_contribution_product_length_eq_transport",
                "exact hsecond_reverse",
                "exact hsource",
                f"have houter : {three_outer}",
                "specialize prime_contribution_prefix_interval_split n",
                "specialize prime_contribution_prefix_interval_split q",
                "specialize prime_contribution_prefix_interval_split h",
                "specialize prime_contribution_prefix_interval_split z",
                "apply prime_contribution_prefix_interval_split",
                "exact houter_source",
                "cases houter",
                "cases houter_witness",
                "cases houter_witness_witness",
                "cases houter_witness_witness_right",
                "have hfirst_reverse : q = s + g",
                "symm",
                "exact hfirst",
                f"have hinner_source : {three_inner_source}",
                "specialize prime_contribution_product_length_eq_transport n",
                "specialize prime_contribution_product_length_eq_transport q",
                "specialize prime_contribution_product_length_eq_transport (s + g)",
                "specialize prime_contribution_product_length_eq_transport x",
                "apply prime_contribution_product_length_eq_transport",
                "exact hfirst_reverse",
                "exact houter_witness_witness_left",
                f"have hinner : {three_inner}",
                "specialize prime_contribution_prefix_interval_split n",
                "specialize prime_contribution_prefix_interval_split s",
                "specialize prime_contribution_prefix_interval_split g",
                "specialize prime_contribution_prefix_interval_split x",
                "apply prime_contribution_prefix_interval_split",
                "exact hinner_source",
                "cases hinner",
                "cases hinner_witness",
                "cases hinner_witness_witness",
                "cases hinner_witness_witness_right",
                "rewrite hinner_witness_witness_right_right at "
                "houter_witness_witness_right_right",
                "exists x2",
                "exists x3",
                "exists x1",
                "split",
                "exact hinner_witness_witness_left",
                "split",
                "exact hinner_witness_witness_right_left",
                "split",
                "exact houter_witness_witness_right_left",
                "exact houter_witness_witness_right_right",
            ),
            "Split a complete contribution Product into three B5 ranges.",
        ),
    )


__all__ = ["make_bertrand_b5_contribution_split_candidate_theorems"]
