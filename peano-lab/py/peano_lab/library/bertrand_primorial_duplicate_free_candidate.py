"""Duplicate-free prime-product comparison for the Bertrand primorial.

The ten rows in this isolated candidate factory give an explicit pairwise
distinctness predicate for beta-coded prefixes, prove that a product of
distinct primes divides every common multiple of its factors, and specialize
that result to the dense ``Primorial`` relation.  All readable predicates are
expanded into ordinary first-order Peano arithmetic before parsing.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_primorial_foundation_candidate import (
    PRIMORIAL_POSITIVE,
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
    _primorial_relation_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.bertrand_primorial_membership_candidate import (
    PRIMORIAL_PRIME_DIVIDES_OF_LE,
)
from peano_lab.library.finite_fold_surface import _product_relation_term


BETA_DISTINCT_EMPTY = "beta_distinct_empty"
BETA_DISTINCT_SUCC_INTRO = "beta_distinct_succ_intro"
BETA_DISTINCT_SUCC_ELIM_PREFIX = "beta_distinct_succ_elim_prefix"
BETA_DISTINCT_SUCC_LAST_NE = "beta_distinct_succ_last_ne"
BETA_DISTINCT_TRANSPORT = "beta_distinct_transport"
BETA_DISTINCT_PRIME_PRODUCT_COPRIME_LAST = (
    "beta_distinct_prime_product_coprime_last"
)
BETA_DISTINCT_PRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE = (
    "beta_distinct_prime_product_divides_common_multiple"
)
BETA_BOUNDED_PRIME_PREFIX_DIVIDES_PRIMORIAL_POINTWISE = (
    "beta_bounded_prime_prefix_divides_primorial_pointwise"
)
BETA_DISTINCT_BOUNDED_PRIME_PRODUCT_DIVIDES_PRIMORIAL = (
    "beta_distinct_bounded_prime_product_divides_primorial"
)
BETA_DISTINCT_BOUNDED_PRIME_PRODUCT_LE_PRIMORIAL = (
    "beta_distinct_bounded_prime_product_le_primorial"
)


def _le_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_left = _render_term(left, label="order left term", context=context)
    rendered_right = _render_term(
        right,
        label="order right term",
        context=context,
    )
    (gap,) = _binders(tag, context, ("le_gap",))
    return f"exists {gap}. {gap} + ({rendered_left}) = ({rendered_right})"


def _divides_term(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_divisor = _render_term(
        divisor,
        label="divisor term",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="dividend term",
        context=context,
    )
    (quotient,) = _binders(tag, context, ("quotient",))
    return (
        f"exists {quotient}. {rendered_value} = "
        f"({rendered_divisor}) * {quotient}"
    )


def _coprime_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_left = _render_term(
        left,
        label="coprime left term",
        context=context,
    )
    rendered_right = _render_term(
        right,
        label="coprime right term",
        context=context,
    )
    divisor, left_factor, right_factor = _binders(
        tag,
        context,
        ("coprime_divisor", "coprime_left_factor", "coprime_right_factor"),
    )
    return (
        f"forall {divisor}. (exists {left_factor}. "
        f"{rendered_left} = {divisor} * {left_factor}) -> "
        f"(exists {right_factor}. "
        f"{rendered_right} = {divisor} * {right_factor}) -> "
        f"{divisor} = 1"
    )


def _all_prime_prefix_term(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(code, label="prime-prefix code", context=context)
    rendered_scale = _render_term(
        scale,
        label="prime-prefix scale",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="prime-prefix length",
        context=context,
    )
    index, value = _binders(tag, context, ("prime_index", "prime_value"))
    local = context + (index, value)
    bound = _lt_term(
        index,
        rendered_length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        rendered_code,
        rendered_scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    prime = _prime_term(value, tag=f"{tag}_prime", avoid=local)
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({prime}))"
    )


def _distinct_prefix_term(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(code, label="distinct code", context=context)
    rendered_scale = _render_term(
        scale,
        label="distinct scale",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="distinct length",
        context=context,
    )
    left_index, right_index, left_value, right_value = _binders(
        tag,
        context,
        ("left_index", "right_index", "left_value", "right_value"),
    )
    local = context + (
        left_index,
        right_index,
        left_value,
        right_value,
    )
    left_bound = _lt_term(
        left_index,
        rendered_length,
        tag=f"{tag}_left_bound",
        avoid=local,
    )
    right_bound = _lt_term(
        right_index,
        rendered_length,
        tag=f"{tag}_right_bound",
        avoid=local,
    )
    left_decoded = _beta_at_term(
        rendered_code,
        rendered_scale,
        left_index,
        left_value,
        tag=f"{tag}_left_decoded",
        avoid=local,
    )
    right_decoded = _beta_at_term(
        rendered_code,
        rendered_scale,
        right_index,
        right_value,
        tag=f"{tag}_right_decoded",
        avoid=local,
    )
    return (
        f"forall {left_index} {right_index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_decoded}) -> ({right_decoded}) -> "
        f"~({left_index} = {right_index}) -> "
        f"~({left_value} = {right_value})"
    )


def _pointwise_le_term(
    code: str,
    scale: str,
    length: str,
    bound_value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(code, label="bounded code", context=context)
    rendered_scale = _render_term(scale, label="bounded scale", context=context)
    rendered_length = _render_term(
        length,
        label="bounded length",
        context=context,
    )
    rendered_bound = _render_term(
        bound_value,
        label="bounded value",
        context=context,
    )
    index, value = _binders(tag, context, ("bound_index", "bound_value"))
    local = context + (index, value)
    index_bound = _lt_term(
        index,
        rendered_length,
        tag=f"{tag}_index_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        rendered_code,
        rendered_scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    (gap,) = _binders(f"{tag}_value_bound", local, ("le_gap",))
    return (
        f"forall {index} {value}. ({index_bound}) -> ({decoded}) -> "
        f"exists {gap}. {gap} + ({value}) = ({rendered_bound})"
    )


def _pointwise_divides_term(
    code: str,
    scale: str,
    length: str,
    target: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(code, label="divisor code", context=context)
    rendered_scale = _render_term(scale, label="divisor scale", context=context)
    rendered_length = _render_term(
        length,
        label="divisor length",
        context=context,
    )
    rendered_target = _render_term(
        target,
        label="common multiple",
        context=context,
    )
    index, value = _binders(tag, context, ("divisor_index", "divisor_value"))
    local = context + (index, value)
    index_bound = _lt_term(
        index,
        rendered_length,
        tag=f"{tag}_index_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        rendered_code,
        rendered_scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    (quotient,) = _binders(f"{tag}_result", local, ("quotient",))
    return (
        f"forall {index} {value}. ({index_bound}) -> ({decoded}) -> "
        f"exists {quotient}. {rendered_target} = {value} * {quotient}"
    )


def _product_term(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    return _product_relation_term(
        _render_term(code, label="product code", context=context),
        _render_term(scale, label="product scale", context=context),
        _render_term(length, label="product length", context=context),
        _render_term(value, label="product value", context=context),
        tag=tag,
        avoid=context,
    )


def make_bertrand_primorial_duplicate_free_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the explicit duplicate-free product comparison microbatch."""

    empty_distinct = _distinct_prefix_term(
        "b", "c", "0", tag="bpdf_empty", variables=("b", "c")
    )

    intro_variables = ("b", "c", "l", "p")
    intro_prefix = _distinct_prefix_term(
        "b", "c", "l", tag="bpdfsi_prefix", variables=intro_variables
    )
    intro_last = _beta_at_term(
        "b",
        "c",
        "l",
        "p",
        tag="bpdfsi_last",
        avoid=intro_variables,
    )
    intro_prior_variables = intro_variables + ("i", "q")
    intro_prior_bound = _lt_term(
        "i",
        "l",
        tag="bpdfsi_prior_bound",
        avoid=intro_prior_variables,
    )
    intro_prior = _beta_at_term(
        "b",
        "c",
        "i",
        "q",
        tag="bpdfsi_prior",
        avoid=intro_prior_variables,
    )
    intro_last_ne = (
        "forall i q. "
        f"({intro_prior_bound}) -> ({intro_prior}) -> "
        "~(q = p)"
    )
    intro_result = _distinct_prefix_term(
        "b", "c", "S l", tag="bpdfsi_result", variables=intro_variables
    )

    elim_variables = ("b", "c", "l")
    elim_source = _distinct_prefix_term(
        "b", "c", "S l", tag="bpdfsep_source", variables=elim_variables
    )
    elim_result = _distinct_prefix_term(
        "b", "c", "l", tag="bpdfsep_result", variables=elim_variables
    )

    last_variables = ("b", "c", "l", "i", "p", "q")
    last_distinct = _distinct_prefix_term(
        "b", "c", "S l", tag="bpdfsln_distinct", variables=last_variables
    )
    last_bound = _lt_term(
        "i", "l", tag="bpdfsln_bound", avoid=last_variables
    )
    last_left = _beta_at_term(
        "b", "c", "i", "p", tag="bpdfsln_left", avoid=last_variables
    )
    last_right = _beta_at_term(
        "b", "c", "l", "q", tag="bpdfsln_right", avoid=last_variables
    )

    transport_variables = ("b", "c", "d", "e", "l")
    transport_source = _distinct_prefix_term(
        "b",
        "c",
        "l",
        tag="bpdft_source",
        variables=transport_variables,
    )
    transport_entry_variables = transport_variables + ("i", "p")
    transport_bound = _lt_term(
        "i",
        "l",
        tag="bpdft_bound",
        avoid=transport_entry_variables,
    )
    transport_source_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpdft_source_entry",
        avoid=transport_entry_variables,
    )
    transport_target_entry = _beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpdft_target_entry",
        avoid=transport_entry_variables,
    )
    transport_entries = (
        "forall i p. "
        f"({transport_bound}) -> ({transport_source_entry}) -> "
        f"({transport_target_entry})"
    )
    transport_result = _distinct_prefix_term(
        "d",
        "e",
        "l",
        tag="bpdft_result",
        variables=transport_variables,
    )

    coprime_variables = ("b", "c", "l", "r", "p")
    coprime_primes = _all_prime_prefix_term(
        "b", "c", "S l", tag="bpdfcp_primes", variables=coprime_variables
    )
    coprime_distinct = _distinct_prefix_term(
        "b", "c", "S l", tag="bpdfcp_distinct", variables=coprime_variables
    )
    coprime_product = _product_term(
        "b", "c", "l", "r", tag="bpdfcp_product", variables=coprime_variables
    )
    coprime_last = _beta_at_term(
        "b", "c", "l", "p", tag="bpdfcp_last", avoid=coprime_variables
    )
    coprime_result = _coprime_term(
        "r", "p", tag="bpdfcp_result", variables=coprime_variables
    )

    divide_variables = ("b", "c", "l", "n", "z")
    divide_primes = _all_prime_prefix_term(
        "b", "c", "l", tag="bpdfdcm_primes", variables=divide_variables
    )
    divide_distinct = _distinct_prefix_term(
        "b", "c", "l", tag="bpdfdcm_distinct", variables=divide_variables
    )
    divide_pointwise = _pointwise_divides_term(
        "b", "c", "l", "z", tag="bpdfdcm_pointwise", variables=divide_variables
    )
    divide_product = _product_term(
        "b", "c", "l", "n", tag="bpdfdcm_product", variables=divide_variables
    )
    divide_result = _divides_term(
        "n", "z", tag="bpdfdcm_result", variables=divide_variables
    )

    pointwise_variables = ("m", "z", "b", "c", "l")
    pointwise_primorial = _primorial_relation_term(
        "m", "z", tag="bpbpdp_primorial", variables=pointwise_variables
    )
    pointwise_primes = _all_prime_prefix_term(
        "b", "c", "l", tag="bpbpdp_primes", variables=pointwise_variables
    )
    pointwise_bounds = _pointwise_le_term(
        "b", "c", "l", "m", tag="bpbpdp_bounds", variables=pointwise_variables
    )
    pointwise_result = _pointwise_divides_term(
        "b", "c", "l", "z", tag="bpbpdp_result", variables=pointwise_variables
    )

    bounded_variables = ("m", "z", "b", "c", "l", "n")
    bounded_primorial = _primorial_relation_term(
        "m", "z", tag="bpdfbdp_primorial", variables=bounded_variables
    )
    bounded_primes = _all_prime_prefix_term(
        "b", "c", "l", tag="bpdfbdp_primes", variables=bounded_variables
    )
    bounded_distinct = _distinct_prefix_term(
        "b", "c", "l", tag="bpdfbdp_distinct", variables=bounded_variables
    )
    bounded_bounds = _pointwise_le_term(
        "b", "c", "l", "m", tag="bpdfbdp_bounds", variables=bounded_variables
    )
    bounded_product = _product_term(
        "b", "c", "l", "n", tag="bpdfbdp_product", variables=bounded_variables
    )
    bounded_divides = _divides_term(
        "n", "z", tag="bpdfbdp_result", variables=bounded_variables
    )

    comparison_primorial = _primorial_relation_term(
        "m", "z", tag="bpdfblp_primorial", variables=bounded_variables
    )
    comparison_primes = _all_prime_prefix_term(
        "b", "c", "l", tag="bpdfblp_primes", variables=bounded_variables
    )
    comparison_distinct = _distinct_prefix_term(
        "b", "c", "l", tag="bpdfblp_distinct", variables=bounded_variables
    )
    comparison_bounds = _pointwise_le_term(
        "b", "c", "l", "m", tag="bpdfblp_bounds", variables=bounded_variables
    )
    comparison_product = _product_term(
        "b", "c", "l", "n", tag="bpdfblp_product", variables=bounded_variables
    )
    comparison_result = _le_term(
        "n", "z", tag="bpdfblp_result", variables=bounded_variables
    )

    transport_source_p = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpdft_local_source_p",
        avoid=transport_variables + ("i", "j", "p", "q", "a"),
    )
    transport_target_p = _beta_at_term(
        "d",
        "e",
        "i",
        "x",
        tag="bpdft_local_target_p",
        avoid=transport_variables + ("i", "j", "p", "q", "x"),
    )
    transport_source_q = _beta_at_term(
        "b",
        "c",
        "j",
        "a",
        tag="bpdft_local_source_q",
        avoid=transport_variables + ("i", "j", "p", "q", "a"),
    )
    transport_target_q = _beta_at_term(
        "d",
        "e",
        "j",
        "x1",
        tag="bpdft_local_target_q",
        avoid=transport_variables + ("i", "j", "p", "q", "x1"),
    )
    coprime_local_last_at = _beta_at_term(
        "b",
        "c",
        "l",
        "q",
        tag="bpdfcp_local_last",
        avoid=coprime_variables + ("q",),
    )
    coprime_local_last_prime = _prime_term(
        "q",
        tag="bpdfcp_local_last_prime",
        avoid=coprime_variables + ("q",),
    )
    coprime_local_prefix_at = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpdfcp_local_prefix",
        avoid=coprime_variables + ("i", "q", "a"),
    )
    coprime_local_prefix_prime = _prime_term(
        "a",
        tag="bpdfcp_local_prefix_prime",
        avoid=coprime_variables + ("i", "q", "a"),
    )
    divide_local_variables = divide_variables + ("p", "r")
    divide_local_last = _beta_at_term(
        "b",
        "c",
        "l",
        "p",
        tag="bpdfdcm_local_last",
        avoid=divide_local_variables,
    )
    divide_local_prefix_product = _product_term(
        "b",
        "c",
        "l",
        "r",
        tag="bpdfdcm_local_prefix_product",
        variables=divide_local_variables,
    )
    divide_witness_variables = divide_variables + ("x", "x1")
    divide_local_prefix_primes = _all_prime_prefix_term(
        "b",
        "c",
        "l",
        tag="bpdfdcm_local_prefix_primes",
        variables=divide_witness_variables,
    )
    divide_local_prefix_distinct = _distinct_prefix_term(
        "b",
        "c",
        "l",
        tag="bpdfdcm_local_prefix_distinct",
        variables=divide_witness_variables,
    )
    divide_local_prefix_pointwise = _pointwise_divides_term(
        "b",
        "c",
        "l",
        "z",
        tag="bpdfdcm_local_prefix_pointwise",
        variables=divide_witness_variables,
    )
    divide_local_coprime = _coprime_term(
        "x1",
        "x",
        tag="bpdfdcm_local_coprime",
        variables=divide_witness_variables,
    )
    pointwise_local_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "q",
        tag="bpbpdp_local_entry",
        avoid=pointwise_variables + ("i", "p", "q"),
    )
    pointwise_local_prime = _prime_term(
        "q",
        tag="bpbpdp_local_prime",
        avoid=pointwise_variables + ("i", "p", "q"),
    )
    bounded_local_pointwise = _pointwise_divides_term(
        "b",
        "c",
        "l",
        "z",
        tag="bpdfbdp_local_pointwise",
        variables=bounded_variables,
    )

    return (
        spec(
            BETA_DISTINCT_EMPTY,
            f"forall b c. ({empty_distinct})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro p",
                "intro q",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hzero : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hzero",
            ),
            "The empty beta prefix is pairwise value-distinct.",
        ),
        spec(
            BETA_DISTINCT_SUCC_INTRO,
            "forall b c l p. "
            f"({intro_prefix}) -> ({intro_last}) -> "
            f"({intro_last_ne}) -> ({intro_result})",
            ("le_of_succ_le_succ", "le_eq_or_lt", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro p",
                "intro hprefix",
                "intro hlast",
                "intro hlast_ne",
                "intro i",
                "intro j",
                "intro a",
                "intro q",
                "intro hi",
                "intro hj",
                "intro ha",
                "intro hq",
                "intro hij",
                "have hil : exists h. h + i = l",
                "specialize le_of_succ_le_succ i",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hi",
                "have hjl : exists h. h + j = l",
                "specialize le_of_succ_le_succ j",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hj",
                "have hisplit : i = l \/ exists h. h + S i = l",
                "specialize le_eq_or_lt i",
                "specialize le_eq_or_lt l",
                "apply le_eq_or_lt",
                "exact hil",
                "have hjsplit : j = l \/ exists h. h + S j = l",
                "specialize le_eq_or_lt j",
                "specialize le_eq_or_lt l",
                "apply le_eq_or_lt",
                "exact hjl",
                "cases hisplit",
                "cases hjsplit",
                "exfalso",
                "apply hij",
                "trans l",
                "exact hisplit_left",
                "symm",
                "exact hjsplit_left",
                "have haq : a = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique a",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "rewrite <- hisplit_left",
                "rewrite <- hisplit_left",
                "exact ha",
                "exact hlast",
                "intro haqvalue",
                "specialize hlast_ne j",
                "specialize hlast_ne q",
                "apply hlast_ne",
                "exact hjsplit_right",
                "exact hq",
                "trans a",
                "symm",
                "exact haqvalue",
                "exact haq",
                "cases hjsplit",
                "have hqeq : q = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique q",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "rewrite <- hjsplit_left",
                "rewrite <- hjsplit_left",
                "exact hq",
                "exact hlast",
                "intro haqvalue",
                "specialize hlast_ne i",
                "specialize hlast_ne a",
                "apply hlast_ne",
                "exact hisplit_right",
                "exact ha",
                "trans q",
                "exact haqvalue",
                "exact hqeq",
                "specialize hprefix i",
                "specialize hprefix j",
                "specialize hprefix a",
                "specialize hprefix q",
                "intro heq",
                "apply hprefix",
                "exact hisplit_right",
                "exact hjsplit_right",
                "exact ha",
                "exact hq",
                "exact hij",
                "exact heq",
            ),
            "Append a fresh decoded value to a distinct beta prefix.",
        ),
        spec(
            BETA_DISTINCT_SUCC_ELIM_PREFIX,
            f"forall b c l. ({elim_source}) -> ({elim_result})",
            ("le_succ",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro hdistinct",
                "intro i",
                "intro j",
                "intro p",
                "intro q",
                "intro hi",
                "intro hj",
                "intro hp",
                "intro hq",
                "intro hij",
                "intro hpq",
                "specialize hdistinct i",
                "specialize hdistinct j",
                "specialize hdistinct p",
                "specialize hdistinct q",
                "apply hdistinct",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "specialize le_succ (S j)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hj",
                "exact hp",
                "exact hq",
                "exact hij",
                "exact hpq",
            ),
            "A distinct successor prefix restricts to a distinct prefix.",
        ),
        spec(
            BETA_DISTINCT_SUCC_LAST_NE,
            "forall b c l i p q. "
            f"({last_distinct}) -> ({last_bound}) -> "
            f"({last_left}) -> ({last_right}) -> ~(p = q)",
            ("le_succ", "le_refl", "lt_irrefl_expanded"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro p",
                "intro q",
                "intro hdistinct",
                "intro hi",
                "intro hp",
                "intro hq",
                "intro hpq",
                "specialize hdistinct i",
                "specialize hdistinct l",
                "specialize hdistinct p",
                "specialize hdistinct q",
                "apply hdistinct",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hp",
                "exact hq",
                "intro hil",
                "rewrite hil at hi",
                "specialize lt_irrefl_expanded l",
                "apply lt_irrefl_expanded",
                "exact hi",
                "exact hpq",
            ),
            "Every old value differs from the last value of a distinct prefix.",
        ),
        spec(
            BETA_DISTINCT_TRANSPORT,
            "forall b c d e l. "
            f"({transport_source}) -> ({transport_entries}) -> "
            f"({transport_result})",
            ("beta_at_exists", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro l",
                "intro hdistinct",
                "intro htransport",
                "intro i",
                "intro j",
                "intro p",
                "intro q",
                "intro hi",
                "intro hj",
                "intro hp",
                "intro hq",
                "intro hij",
                f"have hsource_p : exists a. ({transport_source_p})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists i",
                "exact beta_at_exists",
                "cases hsource_p",
                f"have htarget_p : {transport_target_p}",
                "specialize htransport i",
                "specialize htransport x",
                "apply htransport",
                "exact hi",
                "exact hsource_p_witness",
                "have hpeq : x = p",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact htarget_p",
                "exact hp",
                f"have hsource_q : exists a. ({transport_source_q})",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists j",
                "exact beta_at_exists",
                "cases hsource_q",
                f"have htarget_q : {transport_target_q}",
                "specialize htransport j",
                "specialize htransport x1",
                "apply htransport",
                "exact hj",
                "exact hsource_q_witness",
                "have hqeq : x1 = q",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact htarget_q",
                "exact hq",
                "have hsource_ne : ~(x = x1)",
                "intro hsource_eq",
                "specialize hdistinct i",
                "specialize hdistinct j",
                "specialize hdistinct x",
                "specialize hdistinct x1",
                "apply hdistinct",
                "exact hi",
                "exact hj",
                "exact hsource_p_witness",
                "exact hsource_q_witness",
                "exact hij",
                "exact hsource_eq",
                "intro heq",
                "apply hsource_ne",
                "trans p",
                "exact hpeq",
                "trans q",
                "exact heq",
                "symm",
                "exact hqeq",
            ),
            "Pointwise value-preserving recoding preserves distinctness.",
        ),
        spec(
            BETA_DISTINCT_PRIME_PRODUCT_COPRIME_LAST,
            "forall b c l r p. "
            f"({coprime_primes}) -> ({coprime_distinct}) -> "
            f"({coprime_product}) -> ({coprime_last}) -> "
            f"({coprime_result})",
            (
                "le_succ",
                "le_refl",
                "beta_at_unique",
                "distinct_primes_coprime",
                "beta_product_pointwise_coprime",
                BETA_DISTINCT_SUCC_LAST_NE,
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro p",
                "intro hprimes",
                "intro hdistinct",
                "intro hproduct",
                "intro hlast",
                "have hlast_prime : exists q. "
                f"(({coprime_local_last_at}) /\\ "
                f"({coprime_local_last_prime}))",
                "specialize hprimes l",
                "apply hprimes",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hlast_prime",
                "cases hlast_prime_witness",
                "have hlast_eq : x = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hlast_prime_witness_left",
                "exact hlast",
                "specialize beta_product_pointwise_coprime p",
                "specialize beta_product_pointwise_coprime b",
                "specialize beta_product_pointwise_coprime c",
                "specialize beta_product_pointwise_coprime l",
                "specialize beta_product_pointwise_coprime r",
                "apply beta_product_pointwise_coprime",
                "intro i",
                "intro q",
                "intro hi",
                "intro hq",
                "have hq_prime : exists a. "
                f"(({coprime_local_prefix_at}) /\\ "
                f"({coprime_local_prefix_prime}))",
                "specialize hprimes i",
                "apply hprimes",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "cases hq_prime",
                "cases hq_prime_witness",
                "have hq_eq : x1 = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact hq_prime_witness_left",
                "exact hq",
                "specialize distinct_primes_coprime q",
                "specialize distinct_primes_coprime p",
                "apply distinct_primes_coprime",
                "rewrite <- hq_eq",
                "rewrite <- hq_eq",
                "exact hq_prime_witness_right",
                "rewrite <- hlast_eq",
                "rewrite <- hlast_eq",
                "exact hlast_prime_witness_right",
                "intro hqp",
                "specialize beta_distinct_succ_last_ne b",
                "specialize beta_distinct_succ_last_ne c",
                "specialize beta_distinct_succ_last_ne l",
                "specialize beta_distinct_succ_last_ne i",
                "specialize beta_distinct_succ_last_ne q",
                "specialize beta_distinct_succ_last_ne p",
                "apply beta_distinct_succ_last_ne",
                "exact hdistinct",
                "exact hi",
                "exact hq",
                "exact hlast",
                "exact hqp",
                "exact hproduct",
            ),
            "The last prime is coprime to the product of a distinct prefix.",
        ),
        spec(
            BETA_DISTINCT_PRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE,
            "forall b c l n z. "
            f"({divide_primes}) -> ({divide_distinct}) -> "
            f"({divide_pointwise}) -> ({divide_product}) -> "
            f"({divide_result})",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "one_multiple",
                "coprime_product_is_lcm",
                BETA_DISTINCT_SUCC_ELIM_PREFIX,
                BETA_DISTINCT_PRIME_PRODUCT_COPRIME_LAST,
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro n",
                "intro z",
                "intro hprimes",
                "intro hdistinct",
                "intro hpointwise",
                "intro hproduct",
                "have hn : n = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero n",
                "apply beta_product_zero",
                "exact hproduct",
                "rewrite hn",
                "specialize one_multiple z",
                "exact one_multiple",
                "intro n",
                "intro z",
                "intro hprimes",
                "intro hdistinct",
                "intro hpointwise",
                "intro hproduct",
                "have hdecomposition : exists p r. "
                f"(({divide_local_last}) /\\ "
                f"(({divide_local_prefix_product}) /\\ n = r * p))",
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
                f"have hprefix_primes : {divide_local_prefix_primes}",
                "intro i",
                "intro hi",
                "specialize hprimes i",
                "apply hprimes",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                f"have hprefix_distinct : {divide_local_prefix_distinct}",
                "specialize beta_distinct_succ_elim_prefix b",
                "specialize beta_distinct_succ_elim_prefix c",
                "specialize beta_distinct_succ_elim_prefix l",
                "apply beta_distinct_succ_elim_prefix",
                "exact hdistinct",
                f"have hprefix_pointwise : {divide_local_prefix_pointwise}",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                "specialize hpointwise i",
                "specialize hpointwise p",
                "apply hpointwise",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hp",
                "have hprefix_divides : exists q. z = x1 * q",
                "specialize IH x1",
                "specialize IH z",
                "apply IH",
                "exact hprefix_primes",
                "exact hprefix_distinct",
                "exact hprefix_pointwise",
                "exact hdecomposition_witness_witness_right_left",
                "have hlast_divides : exists q. z = x * q",
                "specialize hpointwise l",
                "specialize hpointwise x",
                "apply hpointwise",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_left",
                f"have hcoprime : {divide_local_coprime}",
                "specialize beta_distinct_prime_product_coprime_last b",
                "specialize beta_distinct_prime_product_coprime_last c",
                "specialize beta_distinct_prime_product_coprime_last l",
                "specialize beta_distinct_prime_product_coprime_last x1",
                "specialize beta_distinct_prime_product_coprime_last x",
                "apply beta_distinct_prime_product_coprime_last",
                "exact hprimes",
                "exact hdistinct",
                "exact hdecomposition_witness_witness_right_left",
                "exact hdecomposition_witness_witness_left",
                "have hlcm : "
                "((((exists u. x1 * x = x1 * u) /\\ exists v. x1 * x = x * v) /\\ "
                "forall t. (exists a. t = x1 * a) -> (exists d. t = x * d) -> "
                "exists q. t = (x1 * x) * q))",
                "specialize coprime_product_is_lcm x1",
                "specialize coprime_product_is_lcm x",
                "apply coprime_product_is_lcm",
                "exact hcoprime",
                "cases hlcm",
                "cases hlcm_left",
                "have hresult : exists q. z = (x1 * x) * q",
                "specialize hlcm_right z",
                "apply hlcm_right",
                "exact hprefix_divides",
                "exact hlast_divides",
                "rewrite hdecomposition_witness_witness_right_right",
                "exact hresult",
            ),
            "A distinct prime product divides every common multiple of its factors.",
        ),
        spec(
            BETA_BOUNDED_PRIME_PREFIX_DIVIDES_PRIMORIAL_POINTWISE,
            "forall m z b c l. "
            f"({pointwise_primorial}) -> ({pointwise_primes}) -> "
            f"({pointwise_bounds}) -> ({pointwise_result})",
            ("beta_at_unique", PRIMORIAL_PRIME_DIVIDES_OF_LE),
            (
                "intro m",
                "intro z",
                "intro b",
                "intro c",
                "intro l",
                "intro hprimorial",
                "intro hprimes",
                "intro hbounds",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                "have hprime : exists q. "
                f"(({pointwise_local_entry}) /\\ "
                f"({pointwise_local_prime}))",
                "specialize hprimes i",
                "apply hprimes",
                "exact hi",
                "cases hprime",
                "cases hprime_witness",
                "have heq : x = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hprime_witness_left",
                "exact hp",
                "specialize primorial_prime_divides_of_le p",
                "specialize primorial_prime_divides_of_le m",
                "specialize primorial_prime_divides_of_le z",
                "apply primorial_prime_divides_of_le",
                "rewrite <- heq",
                "rewrite <- heq",
                "exact hprime_witness_right",
                "specialize hbounds i",
                "specialize hbounds p",
                "apply hbounds",
                "exact hi",
                "exact hp",
                "exact hprimorial",
            ),
            "Every bounded prime entry divides the corresponding Primorial.",
        ),
        spec(
            BETA_DISTINCT_BOUNDED_PRIME_PRODUCT_DIVIDES_PRIMORIAL,
            "forall m z b c l n. "
            f"({bounded_primorial}) -> ({bounded_primes}) -> "
            f"({bounded_distinct}) -> ({bounded_bounds}) -> "
            f"({bounded_product}) -> ({bounded_divides})",
            (
                BETA_BOUNDED_PRIME_PREFIX_DIVIDES_PRIMORIAL_POINTWISE,
                BETA_DISTINCT_PRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE,
            ),
            (
                "intro m",
                "intro z",
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hprimorial",
                "intro hprimes",
                "intro hdistinct",
                "intro hbounds",
                "intro hproduct",
                f"have hpointwise : {bounded_local_pointwise}",
                "specialize beta_bounded_prime_prefix_divides_primorial_pointwise m",
                "specialize beta_bounded_prime_prefix_divides_primorial_pointwise z",
                "specialize beta_bounded_prime_prefix_divides_primorial_pointwise b",
                "specialize beta_bounded_prime_prefix_divides_primorial_pointwise c",
                "specialize beta_bounded_prime_prefix_divides_primorial_pointwise l",
                "apply beta_bounded_prime_prefix_divides_primorial_pointwise",
                "exact hprimorial",
                "exact hprimes",
                "exact hbounds",
                "specialize beta_distinct_prime_product_divides_common_multiple b",
                "specialize beta_distinct_prime_product_divides_common_multiple c",
                "specialize beta_distinct_prime_product_divides_common_multiple l",
                "specialize beta_distinct_prime_product_divides_common_multiple n",
                "specialize beta_distinct_prime_product_divides_common_multiple z",
                "apply beta_distinct_prime_product_divides_common_multiple",
                "exact hprimes",
                "exact hdistinct",
                "exact hpointwise",
                "exact hproduct",
            ),
            "Every duplicate-free bounded prime product divides Primorial.",
        ),
        spec(
            BETA_DISTINCT_BOUNDED_PRIME_PRODUCT_LE_PRIMORIAL,
            "forall m z b c l n. "
            f"({comparison_primorial}) -> ({comparison_primes}) -> "
            f"({comparison_distinct}) -> ({comparison_bounds}) -> "
            f"({comparison_product}) -> ({comparison_result})",
            (
                "divisor_le_nonzero",
                PRIMORIAL_POSITIVE,
                BETA_DISTINCT_BOUNDED_PRIME_PRODUCT_DIVIDES_PRIMORIAL,
            ),
            (
                "intro m",
                "intro z",
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hprimorial",
                "intro hprimes",
                "intro hdistinct",
                "intro hbounds",
                "intro hproduct",
                "have hdivides : exists q. z = n * q",
                "specialize beta_distinct_bounded_prime_product_divides_primorial m",
                "specialize beta_distinct_bounded_prime_product_divides_primorial z",
                "specialize beta_distinct_bounded_prime_product_divides_primorial b",
                "specialize beta_distinct_bounded_prime_product_divides_primorial c",
                "specialize beta_distinct_bounded_prime_product_divides_primorial l",
                "specialize beta_distinct_bounded_prime_product_divides_primorial n",
                "apply beta_distinct_bounded_prime_product_divides_primorial",
                "exact hprimorial",
                "exact hprimes",
                "exact hdistinct",
                "exact hbounds",
                "exact hproduct",
                "have hpositive : exists r. z = S r",
                "specialize primorial_positive m",
                "specialize primorial_positive z",
                "apply primorial_positive",
                "exact hprimorial",
                "cases hpositive",
                "specialize divisor_le_nonzero n",
                "specialize divisor_le_nonzero z",
                "apply divisor_le_nonzero",
                "intro hz",
                "rewrite hz at hpositive_witness",
                "apply PA1",
                "symm",
                "exact hpositive_witness",
                "exact hdivides",
            ),
            "Every duplicate-free bounded prime product is at most Primorial.",
        ),
    )


__all__ = ["make_bertrand_primorial_duplicate_free_candidate_theorems"]
