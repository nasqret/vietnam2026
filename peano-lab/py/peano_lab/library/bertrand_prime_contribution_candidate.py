"""Extensional complete-prime-contribution products for Bertrand B5.

For a natural ``n`` and position ``i``, ``PrimeContribution(n,i,a)`` selects
the complete ``(S i)``-power contribution to ``n`` when ``S i`` is prime,
and selects one otherwise.  The relation is fully expanded into the existing
Prime, PowerVal, Pow, BetaAt, and Product encodings before parsing.

The twelve rows below construct and characterize finite beta prefixes of
these contributions.  Distinct positions have coprime factors, every factor
divides ``n``, and therefore every finite contribution Product divides ``n``.
The converse divisibility needed to reconstruct ``n`` remains a later,
explicit theorem obligation.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.finite_fold_surface import _product_relation_term


PRIME_CONTRIBUTION_CHOICE_EXISTS = "prime_contribution_choice_exists"
PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL = (
    "prime_contribution_choice_functional"
)
PRIME_CONTRIBUTION_PREFIX_EXTEND = "prime_contribution_prefix_extend"
PRIME_CONTRIBUTION_PREFIX_EXISTS = "prime_contribution_prefix_exists"
PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY = (
    "prime_contribution_prefix_transport_entry"
)
PRIME_CONTRIBUTION_PRODUCT_EXISTS = "prime_contribution_product_exists"
PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL = (
    "prime_contribution_product_functional"
)
COPRIME_POWER_RIGHT = "coprime_power_right"
COPRIME_POWERS = "coprime_powers"
PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME = (
    "prime_contribution_prefix_pairwise_coprime"
)
PRIME_CONTRIBUTION_FACTOR_DIVIDES = "prime_contribution_factor_divides"
PRIME_CONTRIBUTION_PRODUCT_DIVIDES = "prime_contribution_product_divides"


def _le_rendered(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("le_gap",))
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _divides_rendered(
    divisor: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (quotient,) = _binders(tag, avoid, ("divides_quotient",))
    return f"exists {quotient}. {value} = ({divisor}) * {quotient}"


def _power_rendered(
    base: str,
    exponent: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    code, scale, index = _binders(
        tag,
        avoid,
        ("power_code", "power_scale", "power_index"),
    )
    local = avoid + (code, scale, index)
    bound = _lt_term(
        index,
        exponent,
        tag=f"{tag}_repeat_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        base,
        tag=f"{tag}_repeat_entry",
        avoid=local,
    )
    repeat = f"forall {index}. ({bound}) -> ({decoded})"
    product = _product_relation_term(
        code,
        scale,
        exponent,
        result,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({repeat}) /\\ ({product}))"


def _power_divides_rendered(
    base: str,
    exponent: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (result,) = _binders(tag, avoid, ("power_value",))
    local = avoid + (result,)
    power = _power_rendered(
        base,
        exponent,
        result,
        tag=f"{tag}_power",
        avoid=local,
    )
    divides = _divides_rendered(
        result,
        value,
        tag=f"{tag}_divides",
        avoid=local,
    )
    return f"exists {result}. (({power}) /\\ ({divides}))"


def _power_valuation_rendered(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (candidate,) = _binders(tag, avoid, ("valuation_candidate",))
    local = avoid + (candidate,)
    selected_bound = _le_rendered(
        exponent,
        value,
        tag=f"{tag}_selected_bound",
        avoid=local,
    )
    selected = _power_divides_rendered(
        base,
        exponent,
        value,
        tag=f"{tag}_selected",
        avoid=local,
    )
    candidate_bound = _le_rendered(
        candidate,
        value,
        tag=f"{tag}_candidate_bound",
        avoid=local,
    )
    candidate_divides = _power_divides_rendered(
        base,
        candidate,
        value,
        tag=f"{tag}_candidate",
        avoid=local,
    )
    candidate_below = _le_rendered(
        candidate,
        exponent,
        tag=f"{tag}_candidate_below",
        avoid=local,
    )
    return (
        f"(({selected_bound}) /\\ ({selected})) /\\ "
        f"forall {candidate}. ({candidate_bound}) -> "
        f"({candidate_divides}) -> ({candidate_below})"
    )


def _coprime_rendered(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    divisor, left_factor, right_factor = _binders(
        tag,
        avoid,
        ("coprime_divisor", "coprime_left", "coprime_right"),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{left} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. {right} = {divisor} * "
        f"{right_factor}) -> {divisor} = 1"
    )


def _choice_rendered(
    number: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (exponent,) = _binders(tag, avoid, ("choice_exponent",))
    local = avoid + (exponent,)
    base = f"S ({index})"
    prime = _prime_term(
        base,
        tag=f"{tag}_prime",
        avoid=local,
    )
    valuation = _power_valuation_rendered(
        base,
        number,
        exponent,
        tag=f"{tag}_valuation",
        avoid=local,
    )
    power = _power_rendered(
        base,
        exponent,
        value,
        tag=f"{tag}_power",
        avoid=local,
    )
    return (
        f"((({prime}) /\\ exists {exponent}. "
        f"(({valuation}) /\\ ({power}))) \\/ "
        f"(~({prime}) /\\ {value} = 1))"
    )


def _prime_contribution_choice_term(
    number: str,
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_number = _render_term(
        number,
        label="contribution number",
        context=context,
    )
    rendered_index = _render_term(
        index,
        label="contribution index",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="contribution value",
        context=context,
    )
    return _choice_rendered(
        rendered_number,
        rendered_index,
        rendered_value,
        tag=tag,
        avoid=context,
    )


def _prefix_rendered(
    number: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("prefix_index", "prefix_value"))
    local = avoid + (index, value)
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _choice_rendered(
        number,
        index,
        value,
        tag=f"{tag}_choice",
        avoid=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _prime_contribution_prefix_term(
    number: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "contribution number"),
            (code, "contribution code"),
            (scale, "contribution scale"),
            (length, "contribution length"),
        )
    )
    return _prefix_rendered(*rendered, tag=tag, avoid=context)


def _prime_contribution_product_term(
    number: str,
    length: str,
    result: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_number = _render_term(
        number,
        label="contribution product number",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="contribution product length",
        context=context,
    )
    rendered_result = _render_term(
        result,
        label="contribution product result",
        context=context,
    )
    code, scale = _binders(tag, context, ("product_code", "product_scale"))
    local = context + (code, scale)
    prefix = _prefix_rendered(
        rendered_number,
        code,
        scale,
        rendered_length,
        tag=f"{tag}_prefix",
        avoid=local,
    )
    product = _product_relation_term(
        code,
        scale,
        rendered_length,
        rendered_result,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _pairwise_coprime_prefix_rendered(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left_index, right_index, left_value, right_value = _binders(
        tag,
        avoid,
        ("pair_left_index", "pair_right_index", "pair_left", "pair_right"),
    )
    local = avoid + (left_index, right_index, left_value, right_value)
    left_bound = _lt_term(
        left_index,
        length,
        tag=f"{tag}_left_bound",
        avoid=local,
    )
    right_bound = _lt_term(
        right_index,
        length,
        tag=f"{tag}_right_bound",
        avoid=local,
    )
    left_entry = _beta_at_term(
        code,
        scale,
        left_index,
        left_value,
        tag=f"{tag}_left_entry",
        avoid=local,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        right_index,
        right_value,
        tag=f"{tag}_right_entry",
        avoid=local,
    )
    coprime = _coprime_rendered(
        left_value,
        right_value,
        tag=f"{tag}_coprime",
        avoid=local,
    )
    return (
        f"forall {left_index} {right_index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> ({left_entry}) -> "
        f"({right_entry}) -> ~({left_index} = {right_index}) -> "
        f"({coprime})"
    )


def _pointwise_divides_rendered(
    code: str,
    scale: str,
    length: str,
    target: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("divide_index", "divide_value"))
    local = avoid + (index, value)
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    entry = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_entry",
        avoid=local,
    )
    divides = _divides_rendered(
        value,
        target,
        tag=f"{tag}_divides",
        avoid=local,
    )
    return (
        f"forall {index} {value}. ({bound}) -> ({entry}) -> ({divides})"
    )


def make_bertrand_prime_contribution_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered prime-contribution foundation."""

    choice_exists = _prime_contribution_choice_term(
        "n", "i", "a", tag="bpcce_result", variables=("n", "i", "a")
    )
    choice_exists_valuation = _power_valuation_rendered(
        "S i",
        "n",
        "e",
        tag="bpcce_valuation",
        avoid=("n", "i", "e"),
    )
    choice_exists_power = _power_rendered(
        "S i",
        "x",
        "a",
        tag="bpcce_power",
        avoid=("n", "i", "x", "a"),
    )

    functional_variables = ("n", "i", "a", "z")
    choice_functional_left = _prime_contribution_choice_term(
        "n",
        "i",
        "a",
        tag="bpccf_left",
        variables=functional_variables,
    )
    choice_functional_right = _prime_contribution_choice_term(
        "n",
        "i",
        "z",
        tag="bpccf_right",
        variables=functional_variables,
    )

    extend_variables = ("n", "b", "c", "m")
    extend_before = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpe_before",
        variables=extend_variables,
    )
    extend_after = _prime_contribution_prefix_term(
        "n",
        "d",
        "e",
        "S m",
        tag="bpcpe_after",
        variables=extend_variables + ("d", "e"),
    )
    extend_choice = _prime_contribution_choice_term(
        "n",
        "m",
        "x",
        tag="bpcpe_choice",
        variables=extend_variables + ("x",),
    )
    extend_local = extend_variables + ("x", "d", "e", "i", "a")
    extend_old_bound = _lt_term(
        "i", "m", tag="bpcpe_old_bound", avoid=extend_local
    )
    extend_old_source = _beta_at_term(
        "b", "c", "i", "a", tag="bpcpe_old_source", avoid=extend_local
    )
    extend_old_target = _beta_at_term(
        "d", "e", "i", "a", tag="bpcpe_old_target", avoid=extend_local
    )
    extend_old_decoded = _beta_at_term(
        "b", "c", "i", "a", tag="bpcpe_old_entry", avoid=extend_local
    )
    extend_old_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "a",
        tag="bpcpe_old_choice",
        variables=extend_local,
    )
    extend_relation = (
        "exists d e. "
        + _beta_at_term(
            "d",
            "e",
            "m",
            "x",
            tag="bpcpe_new_entry",
            avoid=extend_variables + ("x", "d", "e"),
        )
        + " /\\ forall i a. "
        + f"({extend_old_bound}) "
        + "-> "
        + f"({extend_old_source}) "
        + "-> "
        + f"({extend_old_target})"
    )
    extend_old_entry = (
        "exists a. "
        + f"({extend_old_decoded}) "
        + "/\\ "
        + f"({extend_old_choice})"
    )

    prefix_exists = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpx_result",
        variables=("n", "m", "b", "c"),
    )
    prefix_previous = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpx_previous",
        variables=("n", "m", "b", "c"),
    )
    prefix_successor = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "S m",
        tag="bpcpx_successor",
        variables=("n", "m", "b", "c"),
    )

    transport_variables = ("n", "b", "c", "d", "e", "m")
    transport_left = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "m",
        tag="bpcpt_left",
        variables=transport_variables,
    )
    transport_right = _prime_contribution_prefix_term(
        "n",
        "d",
        "e",
        "m",
        tag="bpcpt_right",
        variables=transport_variables,
    )
    transport_bound = _lt_term(
        "i",
        "m",
        tag="bpcpt_bound",
        avoid=transport_variables + ("i", "a"),
    )
    transport_source = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpcpt_source",
        avoid=transport_variables + ("i", "a"),
    )
    transport_target = _beta_at_term(
        "d",
        "e",
        "i",
        "a",
        tag="bpcpt_target",
        avoid=transport_variables + ("i", "a"),
    )
    transport_left_local = transport_variables + ("i", "a", "p")
    transport_left_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpcpt_left_entry",
        avoid=transport_left_local,
    )
    transport_left_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "p",
        tag="bpcpt_left_choice",
        variables=transport_left_local,
    )
    transport_left_entry = (
        f"exists p. ({transport_left_decoded}) /\\ "
        f"({transport_left_choice})"
    )
    transport_right_local = transport_variables + ("i", "a", "q")
    transport_right_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "q",
        tag="bpcpt_right_entry",
        avoid=transport_right_local,
    )
    transport_right_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "q",
        tag="bpcpt_right_choice",
        variables=transport_right_local,
    )
    transport_right_entry = (
        f"exists q. ({transport_right_decoded}) /\\ "
        f"({transport_right_choice})"
    )

    product_exists = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpc_product_exists",
        variables=("n", "m", "z"),
    )
    product_exists_product = _product_relation_term(
        "x",
        "x1",
        "m",
        "z",
        tag="bpc_product_exists_witness",
        avoid=("n", "m", "x", "x1", "z"),
    )

    product_functional_variables = ("n", "m", "x", "y")
    product_functional_left = _prime_contribution_product_term(
        "n",
        "m",
        "x",
        tag="bpcpf_left",
        variables=product_functional_variables,
    )
    product_functional_right = _prime_contribution_product_term(
        "n",
        "m",
        "y",
        tag="bpcpf_right",
        variables=product_functional_variables,
    )
    product_functional_bound = _lt_term(
        "i",
        "m",
        tag="bpcpf_bound",
        avoid=product_functional_variables
        + ("x1", "x2", "x3", "x4", "i", "a"),
    )
    product_functional_source = _beta_at_term(
        "x1",
        "x2",
        "i",
        "a",
        tag="bpcpf_source_entry",
        avoid=product_functional_variables
        + ("x1", "x2", "x3", "x4", "i", "a"),
    )
    product_functional_target = _beta_at_term(
        "x3",
        "x4",
        "i",
        "a",
        tag="bpcpf_target_entry",
        avoid=product_functional_variables
        + ("x1", "x2", "x3", "x4", "i", "a"),
    )
    product_functional_transport = _product_relation_term(
        "x3",
        "x4",
        "m",
        "x",
        tag="bpcpf_transport",
        avoid=product_functional_variables + ("x1", "x2", "x3", "x4"),
    )

    coprime_power_variables = ("p", "q", "e", "z")
    coprime_power_source = _coprime_rendered(
        "p", "q", tag="bcpr_source", avoid=coprime_power_variables
    )
    coprime_power_power = _power_rendered(
        "q", "e", "z", tag="bcpr_power", avoid=coprime_power_variables
    )
    coprime_power_result = _coprime_rendered(
        "p", "z", tag="bcpr_result", avoid=coprime_power_variables
    )
    coprime_power_previous = _power_rendered(
        "q",
        "e",
        "r",
        tag="bcpr_previous",
        avoid=coprime_power_variables + ("r",),
    )

    powers_variables = ("p", "q", "e", "f", "a", "z")
    powers_source = _coprime_rendered(
        "p", "q", tag="bcpowers_source", avoid=powers_variables
    )
    powers_left = _power_rendered(
        "p", "e", "a", tag="bcpowers_left", avoid=powers_variables
    )
    powers_right = _power_rendered(
        "q", "f", "z", tag="bcpowers_right", avoid=powers_variables
    )
    powers_result = _coprime_rendered(
        "a", "z", tag="bcpowers_result", avoid=powers_variables
    )
    powers_previous = _power_rendered(
        "p",
        "e",
        "r",
        tag="bcpowers_previous",
        avoid=powers_variables + ("r",),
    )

    pairwise_variables = ("n", "b", "c", "m")
    pairwise_prefix = _prime_contribution_prefix_term(
        "n",
        "b",
        "c",
        "m",
        tag="bpcppc_source",
        variables=pairwise_variables,
    )
    pairwise_result = _pairwise_coprime_prefix_rendered(
        "b",
        "c",
        "m",
        tag="bpcppc_result",
        avoid=pairwise_variables,
    )
    pairwise_local = pairwise_variables + ("i", "j", "a", "z", "x", "x1")
    pairwise_left_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bpcppc_left_entry",
        avoid=pairwise_local,
    )
    pairwise_left_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "x",
        tag="bpcppc_left_choice",
        variables=pairwise_local,
    )
    pairwise_left = (
        f"exists x. ({pairwise_left_decoded}) /\\ "
        f"({pairwise_left_choice})"
    )
    pairwise_right_decoded = _beta_at_term(
        "b",
        "c",
        "j",
        "x1",
        tag="bpcppc_right_entry",
        avoid=pairwise_local,
    )
    pairwise_right_choice = _prime_contribution_choice_term(
        "n",
        "j",
        "x1",
        tag="bpcppc_right_choice",
        variables=pairwise_local,
    )
    pairwise_right = (
        f"exists x1. ({pairwise_right_decoded}) /\\ "
        f"({pairwise_right_choice})"
    )

    factor_variables = ("n", "i", "a")
    factor_choice = _prime_contribution_choice_term(
        "n", "i", "a", tag="bpcfd_choice", variables=factor_variables
    )
    factor_result = _divides_rendered(
        "a", "n", tag="bpcfd_result", avoid=factor_variables
    )
    factor_selected = _power_divides_rendered(
        "S i",
        "x",
        "n",
        tag="bpcfd_selected",
        avoid=factor_variables + ("x",),
    )

    total_variables = ("n", "m", "z")
    total_source = _prime_contribution_product_term(
        "n", "m", "z", tag="bpcpd_source", variables=total_variables
    )
    total_result = _divides_rendered(
        "z", "n", tag="bpcpd_result", avoid=total_variables
    )
    total_pairwise = _pairwise_coprime_prefix_rendered(
        "x",
        "x1",
        "m",
        tag="bpcpd_pairwise",
        avoid=total_variables + ("x", "x1"),
    )
    total_pointwise = _pointwise_divides_rendered(
        "x",
        "x1",
        "m",
        "n",
        tag="bpcpd_pointwise",
        avoid=total_variables + ("x", "x1"),
    )
    total_entry_local = total_variables + ("x", "x1", "i", "a", "q")
    total_entry_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "q",
        tag="bpcpd_entry",
        avoid=total_entry_local,
    )
    total_entry_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "q",
        tag="bpcpd_choice",
        variables=total_entry_local,
    )
    total_entry = (
        f"exists q. ({total_entry_decoded}) /\\ ({total_entry_choice})"
    )

    return (
        spec(
            PRIME_CONTRIBUTION_CHOICE_EXISTS,
            f"forall n i. exists a. ({choice_exists})",
            ("prime_decidable", "power_valuation_exists", "pow_exists"),
            (
                "intro n",
                "intro i",
                "specialize prime_decidable (S i)",
                "cases prime_decidable",
                f"have hvaluation : exists e. ({choice_exists_valuation})",
                "specialize power_valuation_exists (S i)",
                "specialize power_valuation_exists n",
                "exact power_valuation_exists",
                "cases hvaluation",
                f"have hpower : exists a. ({choice_exists_power})",
                "specialize pow_exists (S i)",
                "specialize pow_exists x",
                "exact pow_exists",
                "cases hpower",
                "exists x1",
                "left",
                "split",
                "exact prime_decidable_left",
                "exists x",
                "split",
                "exact hvaluation_witness",
                "exact hpower_witness",
                "exists 1",
                "right",
                "split",
                "exact prime_decidable_right",
                "refl",
            ),
            "Every index has its complete prime-power contribution or one.",
        ),
        spec(
            PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL,
            "forall n i a z. "
            f"({choice_functional_left}) -> "
            f"({choice_functional_right}) -> a = z",
            ("power_valuation_functional", "pow_functional"),
            (
                "intro n",
                "intro i",
                "intro a",
                "intro z",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_left",
                "cases hleft_left_right",
                "cases hleft_left_right_witness",
                "cases hright",
                "cases hright_left",
                "cases hright_left_right",
                "cases hright_left_right_witness",
                "have hexponent : x = x1",
                "specialize power_valuation_functional (S i)",
                "specialize power_valuation_functional n",
                "specialize power_valuation_functional x",
                "specialize power_valuation_functional x1",
                "apply power_valuation_functional",
                "exact hleft_left_right_witness_left",
                "exact hright_left_right_witness_left",
                "rewrite <- hexponent at hright_left_right_witness_right",
                "rewrite <- hexponent at hright_left_right_witness_right",
                "rewrite <- hexponent at hright_left_right_witness_right",
                "rewrite <- hexponent at hright_left_right_witness_right",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional a",
                "specialize pow_functional z",
                "apply pow_functional",
                "exact hleft_left_right_witness_right",
                "exact hright_left_right_witness_right",
                "cases hright_right",
                "exfalso",
                "apply hright_right_left",
                "exact hleft_left_left",
                "cases hleft_right",
                "cases hright",
                "cases hright_left",
                "exfalso",
                "apply hleft_right_left",
                "exact hright_left_left",
                "cases hright_right",
                "trans 1",
                "exact hleft_right_right",
                "symm",
                "exact hright_right_right",
            ),
            "The complete contribution at a fixed index is unique.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_EXTEND,
            "forall n b c m. "
            f"({extend_before}) -> exists d e. ({extend_after})",
            (
                PRIME_CONTRIBUTION_CHOICE_EXISTS,
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro n",
                "intro b",
                "intro c",
                "intro m",
                "intro hprefix",
                f"have hchoice : exists x. ({extend_choice})",
                "apply prime_contribution_choice_exists",
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
                "have hsplit : i = m \/ exists gap. gap + S i = m",
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
            "Append one contribution while preserving the old prefix.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_EXISTS,
            f"forall n m. exists b c. ({prefix_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                PRIME_CONTRIBUTION_PREFIX_EXTEND,
            ),
            (
                "intro n",
                "induction m",
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
                "apply prime_contribution_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every number and finite length has a contribution prefix.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY,
            "forall n b c d e m. "
            f"({transport_left}) -> ({transport_right}) -> "
            f"forall i a. ({transport_bound}) -> ({transport_source}) -> "
            f"({transport_target})",
            ("beta_at_unique", PRIME_CONTRIBUTION_CHOICE_FUNCTIONAL),
            (
                "intro n",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro m",
                "intro hleft",
                "intro hright",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                f"have hleft_entry : {transport_left_entry}",
                "apply hleft",
                "exact hi",
                "cases hleft_entry",
                "cases hleft_entry_witness",
                f"have hright_entry : {transport_right_entry}",
                "apply hright",
                "exact hi",
                "cases hright_entry",
                "cases hright_entry_witness",
                "have hap : a = x",
                "apply beta_at_unique",
                "exact ha",
                "exact hleft_entry_witness_left",
                "have hpq : x = x1",
                "apply prime_contribution_choice_functional",
                "exact hleft_entry_witness_right",
                "exact hright_entry_witness_right",
                "have haq : a = x1",
                "trans x",
                "exact hap",
                "exact hpq",
                "rewrite haq",
                "rewrite haq",
                "exact hright_entry_witness_left",
            ),
            "Any two contribution-prefix codes decode the same bounded entry.",
        ),
        spec(
            PRIME_CONTRIBUTION_PRODUCT_EXISTS,
            f"forall n m. exists z. ({product_exists})",
            ("beta_product_exists", PRIME_CONTRIBUTION_PREFIX_EXISTS),
            (
                "intro n",
                "intro m",
                f"have hprefix : exists b c. ({prefix_exists})",
                "apply prime_contribution_prefix_exists",
                "cases hprefix",
                "cases hprefix_witness",
                f"have hproduct : exists z. ({product_exists_product})",
                "apply beta_product_exists",
                "cases hproduct",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "exact hproduct_witness",
            ),
            "Every number and finite length has a contribution Product.",
        ),
        spec(
            PRIME_CONTRIBUTION_PRODUCT_FUNCTIONAL,
            "forall n m x y. "
            f"({product_functional_left}) -> "
            f"({product_functional_right}) -> x = y",
            (
                "beta_product_transport_prefix",
                "beta_product_functional",
                PRIME_CONTRIBUTION_PREFIX_TRANSPORT_ENTRY,
            ),
            (
                "intro n",
                "intro m",
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
                "have hpres : forall i a. "
                f"({product_functional_bound}) -> "
                f"({product_functional_source}) -> "
                f"({product_functional_target})",
                "specialize prime_contribution_prefix_transport_entry n",
                "specialize prime_contribution_prefix_transport_entry x1",
                "specialize prime_contribution_prefix_transport_entry x2",
                "specialize prime_contribution_prefix_transport_entry x3",
                "specialize prime_contribution_prefix_transport_entry x4",
                "specialize prime_contribution_prefix_transport_entry m",
                "apply prime_contribution_prefix_transport_entry",
                "exact hleft_witness_witness_left",
                "exact hright_witness_witness_left",
                f"have htransport : {product_functional_transport}",
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
            "The contribution Product is functional in its terminal value.",
        ),
        spec(
            COPRIME_POWER_RIGHT,
            "forall p q e z. "
            f"({coprime_power_source}) -> ({coprime_power_power}) -> "
            f"({coprime_power_result})",
            (
                "pow_zero",
                "pow_successor_decompose",
                "coprime_one_right",
                "coprime_mul_right",
            ),
            (
                "intro p",
                "intro q",
                "induction e",
                "intro z",
                "intro hcoprime",
                "intro hpower",
                "have hvalue : z = 1",
                "specialize pow_zero q",
                "specialize pow_zero 0",
                "specialize pow_zero z",
                "apply pow_zero",
                "refl",
                "exact hpower",
                "rewrite hvalue",
                "specialize coprime_one_right p",
                "apply coprime_one_right",
                "intro z",
                "intro hcoprime",
                "intro hpower",
                "have hdecomposition : exists r. "
                f"({coprime_power_previous}) /\\ z = r * q",
                "specialize pow_successor_decompose q",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose z",
                "apply pow_successor_decompose",
                "refl",
                "exact hpower",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "have hprefix : forall d. (exists a. p = d * a) -> "
                "(exists b. x = d * b) -> d = 1",
                "specialize IH x",
                "apply IH",
                "exact hcoprime",
                "exact hdecomposition_witness_left",
                "rewrite hdecomposition_witness_right",
                "apply coprime_mul_right",
                "exact hprefix",
                "exact hcoprime",
            ),
            "A power preserves coprimality with a fixed left operand.",
        ),
        spec(
            COPRIME_POWERS,
            "forall p q e f a z. "
            f"({powers_source}) -> ({powers_left}) -> ({powers_right}) -> "
            f"({powers_result})",
            (
                "pow_zero",
                "pow_successor_decompose",
                "coprime_one_left",
                "coprime_mul_left",
                COPRIME_POWER_RIGHT,
            ),
            (
                "intro p",
                "intro q",
                "induction e",
                "intro f",
                "intro a",
                "intro z",
                "intro hcoprime",
                "intro hleft",
                "intro hright",
                "have hvalue : a = 1",
                "specialize pow_zero p",
                "specialize pow_zero 0",
                "specialize pow_zero a",
                "apply pow_zero",
                "refl",
                "exact hleft",
                "rewrite hvalue",
                "specialize coprime_one_left z",
                "apply coprime_one_left",
                "intro f",
                "intro a",
                "intro z",
                "intro hcoprime",
                "intro hleft",
                "intro hright",
                "have hdecomposition : exists r. "
                f"({powers_previous}) /\\ a = r * p",
                "specialize pow_successor_decompose p",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose a",
                "apply pow_successor_decompose",
                "refl",
                "exact hleft",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "have hprefix : forall d. (exists u. x = d * u) -> "
                "(exists v. z = d * v) -> d = 1",
                "specialize IH f",
                "specialize IH x",
                "specialize IH z",
                "apply IH",
                "exact hcoprime",
                "exact hdecomposition_witness_left",
                "exact hright",
                "have hlast : forall d. (exists u. p = d * u) -> "
                "(exists v. z = d * v) -> d = 1",
                "specialize coprime_power_right p",
                "specialize coprime_power_right q",
                "specialize coprime_power_right f",
                "specialize coprime_power_right z",
                "apply coprime_power_right",
                "exact hcoprime",
                "exact hright",
                "rewrite hdecomposition_witness_right",
                "apply coprime_mul_left",
                "exact hprefix",
                "exact hlast",
            ),
            "Powers of coprime bases are coprime.",
        ),
        spec(
            PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME,
            "forall n b c m. "
            f"({pairwise_prefix}) -> ({pairwise_result})",
            (
                "beta_at_unique",
                "distinct_primes_coprime",
                "coprime_one_left",
                "coprime_one_right",
                COPRIME_POWERS,
            ),
            (
                "intro n",
                "intro b",
                "intro c",
                "intro m",
                "intro hprefix",
                "intro i",
                "intro j",
                "intro a",
                "intro z",
                "intro hi",
                "intro hj",
                "intro ha",
                "intro hz",
                "intro hij",
                f"have hleft : {pairwise_left}",
                "apply hprefix",
                "exact hi",
                "cases hleft",
                "cases hleft_witness",
                f"have hright : {pairwise_right}",
                "apply hprefix",
                "exact hj",
                "cases hright",
                "cases hright_witness",
                "have hax : x = a",
                "apply beta_at_unique",
                "exact hleft_witness_left",
                "exact ha",
                "have hxz : x1 = z",
                "apply beta_at_unique",
                "exact hright_witness_left",
                "exact hz",
                "have hcoprime : forall d. (exists u. x = d * u) -> "
                "(exists v. x1 = d * v) -> d = 1",
                "cases hleft_witness_right",
                "cases hleft_witness_right_left",
                "cases hleft_witness_right_left_right",
                "cases hleft_witness_right_left_right_witness",
                "cases hright_witness_right",
                "cases hright_witness_right_left",
                "cases hright_witness_right_left_right",
                "cases hright_witness_right_left_right_witness",
                "have hbase_ne : ~(S i = S j)",
                "intro hbase",
                "apply hij",
                "apply PA2",
                "exact hbase",
                "have hbase_coprime : forall d. "
                "(exists u. S i = d * u) -> "
                "(exists v. S j = d * v) -> d = 1",
                "specialize distinct_primes_coprime (S i)",
                "specialize distinct_primes_coprime (S j)",
                "apply distinct_primes_coprime",
                "exact hleft_witness_right_left_left",
                "exact hright_witness_right_left_left",
                "exact hbase_ne",
                "specialize coprime_powers (S i)",
                "specialize coprime_powers (S j)",
                "specialize coprime_powers x2",
                "specialize coprime_powers x3",
                "specialize coprime_powers x",
                "specialize coprime_powers x1",
                "apply coprime_powers",
                "exact hbase_coprime",
                "exact hleft_witness_right_left_right_witness_right",
                "exact hright_witness_right_left_right_witness_right",
                "cases hright_witness_right_right",
                "rewrite hright_witness_right_right_right",
                "specialize coprime_one_right x",
                "apply coprime_one_right",
                "cases hleft_witness_right_right",
                "cases hright_witness_right",
                "rewrite hleft_witness_right_right_right",
                "specialize coprime_one_left x1",
                "apply coprime_one_left",
                "cases hright_witness_right_right",
                "rewrite hleft_witness_right_right_right",
                "specialize coprime_one_left x1",
                "apply coprime_one_left",
                "rewrite <- hax",
                "rewrite <- hxz",
                "exact hcoprime",
            ),
            "Distinct contribution positions decode pairwise-coprime values.",
        ),
        spec(
            PRIME_CONTRIBUTION_FACTOR_DIVIDES,
            "forall n i a. "
            f"({factor_choice}) -> ({factor_result})",
            ("power_valuation_power_divides", "pow_functional", "one_multiple"),
            (
                "intro n",
                "intro i",
                "intro a",
                "intro hchoice",
                "cases hchoice",
                "cases hchoice_left",
                "cases hchoice_left_right",
                "cases hchoice_left_right_witness",
                f"have hselected : {factor_selected}",
                "specialize power_valuation_power_divides (S i)",
                "specialize power_valuation_power_divides n",
                "specialize power_valuation_power_divides x",
                "apply power_valuation_power_divides",
                "exact hchoice_left_right_witness_left",
                "cases hselected",
                "cases hselected_witness",
                "cases hselected_witness_right",
                "have hvalue : x1 = a",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional x1",
                "specialize pow_functional a",
                "apply pow_functional",
                "exact hselected_witness_left",
                "exact hchoice_left_right_witness_right",
                "exists x2",
                "rewrite <- hvalue",
                "exact hselected_witness_right_witness",
                "cases hchoice_right",
                "rewrite hchoice_right_right",
                "apply one_multiple",
            ),
            "Every complete contribution factor divides its source number.",
        ),
        spec(
            PRIME_CONTRIBUTION_PRODUCT_DIVIDES,
            "forall n m z. "
            f"({total_source}) -> ({total_result})",
            (
                "beta_at_unique",
                "beta_pairwise_coprime_product_divides_common_multiple",
                PRIME_CONTRIBUTION_PREFIX_PAIRWISE_COPRIME,
                PRIME_CONTRIBUTION_FACTOR_DIVIDES,
            ),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro hsource",
                "cases hsource",
                "cases hsource_witness",
                "cases hsource_witness_witness",
                f"have hpairwise : {total_pairwise}",
                "apply prime_contribution_prefix_pairwise_coprime",
                "exact hsource_witness_witness_left",
                f"have hpointwise : {total_pointwise}",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                f"have hentry : {total_entry}",
                "apply hsource_witness_witness_left",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "have haq : a = x2",
                "apply beta_at_unique",
                "exact ha",
                "exact hentry_witness_left",
                "have hdivides : exists q. n = x2 * q",
                "apply prime_contribution_factor_divides",
                "exact hentry_witness_right",
                "cases hdivides",
                "exists x3",
                "rewrite haq",
                "exact hdivides_witness",
                "specialize beta_pairwise_coprime_product_divides_common_multiple x",
                "specialize beta_pairwise_coprime_product_divides_common_multiple x1",
                "specialize beta_pairwise_coprime_product_divides_common_multiple m",
                "specialize beta_pairwise_coprime_product_divides_common_multiple z",
                "specialize beta_pairwise_coprime_product_divides_common_multiple n",
                "apply beta_pairwise_coprime_product_divides_common_multiple",
                "exact hpairwise",
                "exact hpointwise",
                "exact hsource_witness_witness_right",
            ),
            "Every finite complete-contribution Product divides its source.",
        ),
    )


__all__ = [
    "make_bertrand_prime_contribution_candidate_theorems",
    "_prime_contribution_choice_term",
    "_prime_contribution_prefix_term",
    "_prime_contribution_product_term",
]
