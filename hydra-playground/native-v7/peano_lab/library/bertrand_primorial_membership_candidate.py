"""Prime membership and monotonicity for the dense Bertrand primorial.

The eleven candidates in this module build on the conservative ``Primorial``
relation.  They characterize its prime divisors, expose one-step and additive
length divisibility, and finish with an explicit positive quotient and numeric
monotonicity.  Every displayed helper expands into ordinary first-order Peano
arithmetic before parsing; this module adds no predicate or kernel primitive.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_primorial_foundation_candidate import (
    PRIMORIAL_EXISTS,
    PRIMORIAL_FUNCTIONAL,
    PRIMORIAL_POSITIVE,
    PRIMORIAL_SUCC_DECOMPOSE,
    PRIMORIAL_ZERO,
    _beta_at_term,
    _binders,
    _primorial_factor_choice_term,
    _primorial_relation_term,
    _prime_term,
    _render_term,
    _validated_context,
)


PRIMORIAL_INDEX_EQ_TRANSPORT = "primorial_index_eq_transport"
PRIMORIAL_FACTOR_CHOICE_PRIME_DIVISOR_EQ = (
    "primorial_factor_choice_prime_divisor_eq"
)
PRIMORIAL_PRIME_DIVIDES_OF_LE = "primorial_prime_divides_of_le"
PRIMORIAL_PRIME_LE_OF_DIVIDES = "primorial_prime_le_of_divides"
PRIMORIAL_PRIME_DIVIDES_IFF_LE = "primorial_prime_divides_iff_le"
PRIMORIAL_SUCC_FACTOR = "primorial_succ_factor"
PRIMORIAL_SUCC_DIVIDES = "primorial_succ_divides"
PRIMORIAL_ADD_LENGTH_DIVIDES = "primorial_add_length_divides"
PRIMORIAL_LE_DIVIDES = "primorial_le_divides"
PRIMORIAL_LE_POSITIVE_QUOTIENT = "primorial_le_positive_quotient"
PRIMORIAL_LE_MONOTONE = "primorial_le_monotone"


def _le_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_left = _render_term(
        left,
        label="primorial order left term",
        context=context,
    )
    rendered_right = _render_term(
        right,
        label="primorial order right term",
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
        label="primorial divisor term",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="primorial dividend term",
        context=context,
    )
    (quotient,) = _binders(tag, context, ("quotient",))
    return (
        f"exists {quotient}. {rendered_value} = "
        f"({rendered_divisor}) * {quotient}"
    )


def _prime_relation_term(
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_value = _render_term(
        value,
        label="primorial prime term",
        context=context,
    )
    return _prime_term(rendered_value, tag=tag, avoid=context)


def make_bertrand_primorial_membership_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the frozen membership and monotonicity microbatch."""

    transport_variables = ("n", "m", "z")
    transport_source = _primorial_relation_term(
        "n",
        "z",
        tag="bpmit_source",
        variables=transport_variables,
    )
    transport_target = _primorial_relation_term(
        "m",
        "z",
        tag="bpmit_target",
        variables=transport_variables,
    )

    choice_variables = ("i", "a", "p")
    choice_prime = _prime_relation_term(
        "p",
        tag="bpfcpde_prime",
        variables=choice_variables,
    )
    choice_relation = _primorial_factor_choice_term(
        "i",
        "a",
        tag="bpfcpde_choice",
        variables=choice_variables,
    )
    choice_divides = _divides_term(
        "p",
        "a",
        tag="bpfcpde_divides",
        variables=choice_variables,
    )

    forward_variables = ("p", "m", "z")
    forward_prime = _prime_relation_term(
        "p",
        tag="bppdol_prime",
        variables=forward_variables,
    )
    forward_bound = _le_term(
        "p",
        "m",
        tag="bppdol_bound",
        variables=forward_variables,
    )
    forward_source = _primorial_relation_term(
        "m",
        "z",
        tag="bppdol_source",
        variables=forward_variables,
    )
    forward_result = _divides_term(
        "p",
        "z",
        tag="bppdol_result",
        variables=forward_variables,
    )
    forward_local_variables = (
        "p",
        "m",
        "z",
        "x",
        "x1",
        "x2",
        "a",
    )
    forward_entry_decoded = _beta_at_term(
        "x1",
        "x2",
        "S x",
        "a",
        tag="bppdol_local_entry",
        avoid=forward_local_variables,
    )
    forward_entry_choice = _primorial_factor_choice_term(
        "S x",
        "a",
        tag="bppdol_local_choice",
        variables=forward_local_variables,
    )
    forward_entry = (
        f"exists a. (({forward_entry_decoded}) /\\ "
        f"({forward_entry_choice}))"
    )

    reverse_prime = _prime_relation_term(
        "p",
        tag="bpplod_prime",
        variables=forward_variables,
    )
    reverse_source = _primorial_relation_term(
        "m",
        "z",
        tag="bpplod_source",
        variables=forward_variables,
    )
    reverse_divides = _divides_term(
        "p",
        "z",
        tag="bpplod_divides",
        variables=forward_variables,
    )
    reverse_result = _le_term(
        "p",
        "m",
        tag="bpplod_result",
        variables=forward_variables,
    )
    reverse_step_variables = ("p", "m", "z", "a", "r")
    reverse_step_choice = _primorial_factor_choice_term(
        "m",
        "a",
        tag="bpplod_local_factor",
        variables=reverse_step_variables,
    )
    reverse_step_previous = _primorial_relation_term(
        "m",
        "r",
        tag="bpplod_local_previous",
        variables=reverse_step_variables,
    )
    reverse_decomposition = (
        "exists a r. "
        f"({reverse_step_choice}) /\\ "
        f"(({reverse_step_previous}) /\\ z = r * a)"
    )
    reverse_local_variables = ("p", "m", "z", "x", "x1")
    reverse_left_divides = _divides_term(
        "p",
        "x1",
        tag="bpplod_local_left_divides",
        variables=reverse_local_variables,
    )
    reverse_right_divides = _divides_term(
        "p",
        "x",
        tag="bpplod_local_right_divides",
        variables=reverse_local_variables,
    )
    reverse_split = (
        f"({reverse_left_divides}) \\/ ({reverse_right_divides})"
    )
    reverse_previous_bound = _le_term(
        "p",
        "m",
        tag="bpplod_local_previous_bound",
        variables=reverse_local_variables,
    )

    iff_prime = _prime_relation_term(
        "p",
        tag="bppdil_prime",
        variables=forward_variables,
    )
    iff_source = _primorial_relation_term(
        "m",
        "z",
        tag="bppdil_source",
        variables=forward_variables,
    )
    iff_divides_left = _divides_term(
        "p",
        "z",
        tag="bppdil_divides_left",
        variables=forward_variables,
    )
    iff_bound_left = _le_term(
        "p",
        "m",
        tag="bppdil_bound_left",
        variables=forward_variables,
    )
    iff_bound_right = _le_term(
        "p",
        "m",
        tag="bppdil_bound_right",
        variables=forward_variables,
    )
    iff_divides_right = _divides_term(
        "p",
        "z",
        tag="bppdil_divides_right",
        variables=forward_variables,
    )

    step_variables = ("m", "x", "y")
    factor_before = _primorial_relation_term(
        "m",
        "x",
        tag="bpsf_before",
        variables=step_variables,
    )
    factor_after = _primorial_relation_term(
        "S m",
        "y",
        tag="bpsf_after",
        variables=step_variables,
    )
    factor_choice = _primorial_factor_choice_term(
        "m",
        "p",
        tag="bpsf_factor",
        variables=step_variables + ("p",),
    )
    factor_result = f"exists p. ({factor_choice}) /\\ y = x * p"
    factor_local_previous = _primorial_relation_term(
        "m",
        "r",
        tag="bpsf_local_previous",
        variables=step_variables + ("p", "r"),
    )
    factor_decomposition = (
        "exists p r. "
        f"({factor_choice}) /\\ "
        f"(({factor_local_previous}) /\\ y = r * p)"
    )

    divides_before = _primorial_relation_term(
        "m",
        "x",
        tag="bpsd_before",
        variables=step_variables,
    )
    divides_after = _primorial_relation_term(
        "S m",
        "y",
        tag="bpsd_after",
        variables=step_variables,
    )
    divides_result = _divides_term(
        "x",
        "y",
        tag="bpsd_result",
        variables=step_variables,
    )
    divides_local_choice = _primorial_factor_choice_term(
        "m",
        "p",
        tag="bpsd_local_factor",
        variables=step_variables + ("p",),
    )
    divides_local_factor = (
        f"exists p. ({divides_local_choice}) /\\ y = x * p"
    )

    add_variables = ("g", "m", "x", "y")
    add_before = _primorial_relation_term(
        "m",
        "x",
        tag="bpald_before",
        variables=add_variables,
    )
    add_after = _primorial_relation_term(
        "g + m",
        "y",
        tag="bpald_after",
        variables=add_variables,
    )
    add_result = _divides_term(
        "x",
        "y",
        tag="bpald_result",
        variables=add_variables,
    )
    add_zero_target = _primorial_relation_term(
        "m",
        "y",
        tag="bpald_local_zero_target",
        variables=add_variables,
    )
    add_step_target = _primorial_relation_term(
        "S (g + m)",
        "y",
        tag="bpald_local_step_target",
        variables=add_variables,
    )
    add_middle = _primorial_relation_term(
        "g + m",
        "r",
        tag="bpald_local_middle",
        variables=add_variables + ("r",),
    )
    add_middle_exists = f"exists r. ({add_middle})"
    add_left_divides = _divides_term(
        "x",
        "x1",
        tag="bpald_local_left_divides",
        variables=add_variables + ("x1",),
    )
    add_right_divides = _divides_term(
        "x1",
        "y",
        tag="bpald_local_right_divides",
        variables=add_variables + ("x1",),
    )

    le_variables = ("m", "n", "x", "y")
    le_index_bound = _le_term(
        "m",
        "n",
        tag="bpld_index_bound",
        variables=le_variables,
    )
    le_before = _primorial_relation_term(
        "m",
        "x",
        tag="bpld_before",
        variables=le_variables,
    )
    le_after = _primorial_relation_term(
        "n",
        "y",
        tag="bpld_after",
        variables=le_variables,
    )
    le_result = _divides_term(
        "x",
        "y",
        tag="bpld_result",
        variables=le_variables,
    )
    le_shifted_after = _primorial_relation_term(
        "x1 + m",
        "y",
        tag="bpld_local_shifted_after",
        variables=le_variables + ("x1",),
    )

    positive_index_bound = _le_term(
        "m",
        "n",
        tag="bplpq_index_bound",
        variables=le_variables,
    )
    positive_before = _primorial_relation_term(
        "m",
        "x",
        tag="bplpq_before",
        variables=le_variables,
    )
    positive_after = _primorial_relation_term(
        "n",
        "y",
        tag="bplpq_after",
        variables=le_variables,
    )
    positive_divides = _divides_term(
        "x",
        "y",
        tag="bplpq_local_divides",
        variables=le_variables,
    )

    monotone_index_bound = _le_term(
        "m",
        "n",
        tag="bplm_index_bound",
        variables=le_variables,
    )
    monotone_before = _primorial_relation_term(
        "m",
        "x",
        tag="bplm_before",
        variables=le_variables,
    )
    monotone_after = _primorial_relation_term(
        "n",
        "y",
        tag="bplm_after",
        variables=le_variables,
    )
    monotone_result = _le_term(
        "x",
        "y",
        tag="bplm_result",
        variables=le_variables,
    )

    return (
        spec(
            PRIMORIAL_INDEX_EQ_TRANSPORT,
            "forall n m z. n = m -> "
            f"({transport_source}) -> ({transport_target})",
            (),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro hindex",
                "intro hsource",
                "rewrite hindex at hsource",
                "rewrite hindex at hsource",
                "rewrite hindex at hsource",
                "rewrite hindex at hsource",
                "exact hsource",
            ),
            "Equal indices transport the expanded Primorial relation.",
        ),
        spec(
            PRIMORIAL_FACTOR_CHOICE_PRIME_DIVISOR_EQ,
            "forall i a p. "
            f"({choice_prime}) -> ({choice_relation}) -> "
            f"({choice_divides}) -> p = S i",
            ("divisor_one", "prime_divisor_eq_one_or_self"),
            (
                "intro i",
                "intro a",
                "intro p",
                "intro hp",
                "cases hp",
                "intro hchoice",
                "intro hdivides",
                "cases hchoice",
                "cases hchoice_left",
                "rewrite hchoice_left_right at hdivides",
                "have hsplit : p = 1 \\/ S i = p",
                "specialize prime_divisor_eq_one_or_self (S i)",
                "specialize prime_divisor_eq_one_or_self p",
                "apply prime_divisor_eq_one_or_self",
                "exact hchoice_left_left",
                "exact hdivides",
                "cases hsplit",
                "exfalso",
                "apply hp_left",
                "exact hsplit_left",
                "symm",
                "exact hsplit_right",
                "cases hchoice_right",
                "rewrite hchoice_right_right at hdivides",
                "have hpone : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hdivides",
                "exfalso",
                "apply hp_left",
                "exact hpone",
            ),
            "A prime divisor of one selector factor is its candidate.",
        ),
        spec(
            PRIMORIAL_PRIME_DIVIDES_OF_LE,
            "forall p m z. "
            f"({forward_prime}) -> ({forward_bound}) -> "
            f"({forward_source}) -> ({forward_result})",
            ("prime_is_succ_succ", "beta_factor_divides_product"),
            (
                "intro p",
                "intro m",
                "intro z",
                "intro hp",
                "intro hle",
                "intro hprimorial",
                "have hshape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hshape",
                "rewrite hshape_witness at hp",
                "rewrite hshape_witness at hp",
                "rewrite hshape_witness at hle",
                "cases hprimorial",
                "cases hprimorial_witness",
                "cases hprimorial_witness_witness",
                f"have hentry : {forward_entry}",
                "apply hprimorial_witness_witness_left",
                "exact hle",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_right",
                "cases hentry_witness_right_left",
                "have hfactor_value : x3 = p",
                "trans S (S x)",
                "exact hentry_witness_right_left_right",
                "symm",
                "exact hshape_witness",
                "rewrite hfactor_value at hentry_witness_left",
                "rewrite hfactor_value at hentry_witness_left",
                "specialize beta_factor_divides_product x1",
                "specialize beta_factor_divides_product x2",
                "specialize beta_factor_divides_product m",
                "specialize beta_factor_divides_product z",
                "specialize beta_factor_divides_product (S x)",
                "specialize beta_factor_divides_product p",
                "apply beta_factor_divides_product",
                "exact hle",
                "exact hentry_witness_left",
                "exact hprimorial_witness_witness_right",
                "cases hentry_witness_right_right",
                "exfalso",
                "apply hentry_witness_right_right_left",
                "exact hp",
            ),
            "Every prime at most the index divides the Primorial value.",
        ),
        spec(
            PRIMORIAL_PRIME_LE_OF_DIVIDES,
            "forall p m z. "
            f"({reverse_prime}) -> ({reverse_source}) -> "
            f"({reverse_divides}) -> ({reverse_result})",
            (
                "divisor_one",
                "le_refl",
                "le_succ",
                "euclid_prime_dvd_product",
                PRIMORIAL_ZERO,
                PRIMORIAL_SUCC_DECOMPOSE,
                PRIMORIAL_FACTOR_CHOICE_PRIME_DIVISOR_EQ,
            ),
            (
                "intro p",
                "intro m",
                "induction m",
                "intro z",
                "intro hp",
                "cases hp",
                "intro hprimorial",
                "intro hdivides",
                "have hz : z = 1",
                "specialize primorial_zero z",
                "apply primorial_zero",
                "exact hprimorial",
                "rewrite hz at hdivides",
                "have hpone : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hdivides",
                "exfalso",
                "apply hp_left",
                "exact hpone",
                "intro z",
                "intro hp",
                "cases hp",
                "intro hprimorial",
                "intro hdivides",
                f"have hdecomposition : {reverse_decomposition}",
                "specialize primorial_succ_decompose m",
                "specialize primorial_succ_decompose z",
                "apply primorial_succ_decompose",
                "exact hprimorial",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "rewrite hdecomposition_witness_witness_right_right at hdivides",
                f"have hsplit : {reverse_split}",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product x1",
                "specialize euclid_prime_dvd_product x",
                "apply euclid_prime_dvd_product",
                "split",
                "exact hp_left",
                "exact hp_right",
                "exact hdivides",
                "cases hsplit",
                f"have hprevious : {reverse_previous_bound}",
                "specialize IH x1",
                "apply IH",
                "split",
                "exact hp_left",
                "exact hp_right",
                "exact hdecomposition_witness_witness_right_left",
                "exact hsplit_left",
                "specialize le_succ p",
                "specialize le_succ m",
                "apply le_succ",
                "exact hprevious",
                "have hterminal : p = S m",
                "specialize primorial_factor_choice_prime_divisor_eq m",
                "specialize primorial_factor_choice_prime_divisor_eq x",
                "specialize primorial_factor_choice_prime_divisor_eq p",
                "apply primorial_factor_choice_prime_divisor_eq",
                "split",
                "exact hp_left",
                "exact hp_right",
                "exact hdecomposition_witness_witness_left",
                "exact hsplit_right",
                "rewrite hterminal",
                "specialize le_refl (S m)",
                "exact le_refl",
            ),
            "Every prime divisor of a Primorial lies at most at its index.",
        ),
        spec(
            PRIMORIAL_PRIME_DIVIDES_IFF_LE,
            "forall p m z. "
            f"({iff_prime}) -> ({iff_source}) -> "
            f"((({iff_divides_left}) -> ({iff_bound_left})) /\\ "
            f"(({iff_bound_right}) -> ({iff_divides_right})))",
            (
                PRIMORIAL_PRIME_LE_OF_DIVIDES,
                PRIMORIAL_PRIME_DIVIDES_OF_LE,
            ),
            (
                "intro p",
                "intro m",
                "intro z",
                "intro hp",
                "intro hprimorial",
                "split",
                "intro hdivides",
                "specialize primorial_prime_le_of_divides p",
                "specialize primorial_prime_le_of_divides m",
                "specialize primorial_prime_le_of_divides z",
                "apply primorial_prime_le_of_divides",
                "exact hp",
                "exact hprimorial",
                "exact hdivides",
                "intro hle",
                "specialize primorial_prime_divides_of_le p",
                "specialize primorial_prime_divides_of_le m",
                "specialize primorial_prime_divides_of_le z",
                "apply primorial_prime_divides_of_le",
                "exact hp",
                "exact hle",
                "exact hprimorial",
            ),
            "Prime divisibility of a Primorial is equivalent to index order.",
        ),
        spec(
            PRIMORIAL_SUCC_FACTOR,
            "forall m x y. "
            f"({factor_before}) -> ({factor_after}) -> ({factor_result})",
            (PRIMORIAL_SUCC_DECOMPOSE, PRIMORIAL_FUNCTIONAL),
            (
                "intro m",
                "intro x",
                "intro y",
                "intro hbefore",
                "intro hafter",
                f"have hdecomposition : {factor_decomposition}",
                "specialize primorial_succ_decompose m",
                "specialize primorial_succ_decompose y",
                "apply primorial_succ_decompose",
                "exact hafter",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "have hprevious : x = x2",
                "specialize primorial_functional m",
                "specialize primorial_functional x",
                "specialize primorial_functional x2",
                "apply primorial_functional",
                "exact hbefore",
                "exact hdecomposition_witness_witness_right_left",
                "exists x1",
                "split",
                "exact hdecomposition_witness_witness_left",
                "rewrite hprevious",
                "exact hdecomposition_witness_witness_right_right",
            ),
            "A successor Primorial is the previous value times its selector.",
        ),
        spec(
            PRIMORIAL_SUCC_DIVIDES,
            "forall m x y. "
            f"({divides_before}) -> ({divides_after}) -> ({divides_result})",
            (PRIMORIAL_SUCC_FACTOR,),
            (
                "intro m",
                "intro x",
                "intro y",
                "intro hbefore",
                "intro hafter",
                f"have hfactor : {divides_local_factor}",
                "specialize primorial_succ_factor m",
                "specialize primorial_succ_factor x",
                "specialize primorial_succ_factor y",
                "apply primorial_succ_factor",
                "exact hbefore",
                "exact hafter",
                "cases hfactor",
                "cases hfactor_witness",
                "exists x1",
                "exact hfactor_witness_right",
            ),
            "Each Primorial value divides the next one.",
        ),
        spec(
            PRIMORIAL_ADD_LENGTH_DIVIDES,
            "forall g m x y. "
            f"({add_before}) -> ({add_after}) -> ({add_result})",
            (
                "zero_add",
                "add_succ_left",
                PRIMORIAL_INDEX_EQ_TRANSPORT,
                PRIMORIAL_FUNCTIONAL,
                "multiple_refl",
                PRIMORIAL_EXISTS,
                PRIMORIAL_SUCC_DIVIDES,
                "multiple_trans",
            ),
            (
                "induction g",
                "intro m",
                "intro x",
                "intro y",
                "intro hbefore",
                "intro hafter",
                "have hzero : 0 + m = m",
                "specialize zero_add m",
                "exact zero_add",
                f"have htarget : {add_zero_target}",
                "specialize primorial_index_eq_transport (0 + m)",
                "specialize primorial_index_eq_transport m",
                "specialize primorial_index_eq_transport y",
                "apply primorial_index_eq_transport",
                "exact hzero",
                "exact hafter",
                "have hequal : x = y",
                "specialize primorial_functional m",
                "specialize primorial_functional x",
                "specialize primorial_functional y",
                "apply primorial_functional",
                "exact hbefore",
                "exact htarget",
                "rewrite <- hequal",
                "specialize multiple_refl x",
                "exact multiple_refl",
                "intro m",
                "intro x",
                "intro y",
                "intro hbefore",
                "intro hafter",
                "have hstep : S g + m = S (g + m)",
                "specialize add_succ_left g",
                "specialize add_succ_left m",
                "exact add_succ_left",
                f"have htarget : {add_step_target}",
                "specialize primorial_index_eq_transport (S g + m)",
                "specialize primorial_index_eq_transport (S (g + m))",
                "specialize primorial_index_eq_transport y",
                "apply primorial_index_eq_transport",
                "exact hstep",
                "exact hafter",
                f"have hmiddle : {add_middle_exists}",
                "specialize primorial_exists (g + m)",
                "exact primorial_exists",
                "cases hmiddle",
                f"have hleft : {add_left_divides}",
                "specialize IH m",
                "specialize IH x",
                "specialize IH x1",
                "apply IH",
                "exact hbefore",
                "exact hmiddle_witness",
                f"have hright : {add_right_divides}",
                "specialize primorial_succ_divides (g + m)",
                "specialize primorial_succ_divides x1",
                "specialize primorial_succ_divides y",
                "apply primorial_succ_divides",
                "exact hmiddle_witness",
                "exact htarget",
                "specialize multiple_trans x1",
                "specialize multiple_trans x",
                "specialize multiple_trans y",
                "apply multiple_trans",
                "exact hright",
                "exact hleft",
            ),
            "Adding any index gap preserves Primorial divisibility.",
        ),
        spec(
            PRIMORIAL_LE_DIVIDES,
            "forall m n x y. "
            f"({le_index_bound}) -> ({le_before}) -> ({le_after}) -> "
            f"({le_result})",
            (PRIMORIAL_INDEX_EQ_TRANSPORT, PRIMORIAL_ADD_LENGTH_DIVIDES),
            (
                "intro m",
                "intro n",
                "intro x",
                "intro y",
                "intro hle",
                "intro hbefore",
                "intro hafter",
                "cases hle",
                "have hindex : n = x1 + m",
                "symm",
                "exact hle_witness",
                f"have hshifted : {le_shifted_after}",
                "specialize primorial_index_eq_transport n",
                "specialize primorial_index_eq_transport (x1 + m)",
                "specialize primorial_index_eq_transport y",
                "apply primorial_index_eq_transport",
                "exact hindex",
                "exact hafter",
                "specialize primorial_add_length_divides x1",
                "specialize primorial_add_length_divides m",
                "specialize primorial_add_length_divides x",
                "specialize primorial_add_length_divides y",
                "apply primorial_add_length_divides",
                "exact hbefore",
                "exact hshifted",
            ),
            "Index order induces divisibility between Primorial values.",
        ),
        spec(
            PRIMORIAL_LE_POSITIVE_QUOTIENT,
            "forall m n x y. "
            f"({positive_index_bound}) -> ({positive_before}) -> "
            f"({positive_after}) -> exists q. y = x * S q",
            ("zero_or_succ", PRIMORIAL_POSITIVE, PRIMORIAL_LE_DIVIDES),
            (
                "intro m",
                "intro n",
                "intro x",
                "intro y",
                "intro hle",
                "intro hbefore",
                "intro hafter",
                f"have hdivides : {positive_divides}",
                "specialize primorial_le_divides m",
                "specialize primorial_le_divides n",
                "specialize primorial_le_divides x",
                "specialize primorial_le_divides y",
                "apply primorial_le_divides",
                "exact hle",
                "exact hbefore",
                "exact hafter",
                "cases hdivides",
                "have hpositive : exists r. y = S r",
                "specialize primorial_positive n",
                "specialize primorial_positive y",
                "apply primorial_positive",
                "exact hafter",
                "cases hpositive",
                "specialize zero_or_succ x1",
                "cases zero_or_succ",
                "rewrite zero_or_succ_left at hdivides_witness",
                "rewrite PA5 at hdivides_witness",
                "rewrite hpositive_witness at hdivides_witness",
                "exfalso",
                "apply PA1",
                "exact hdivides_witness",
                "cases zero_or_succ_right",
                "exists x3",
                "rewrite zero_or_succ_right_witness at hdivides_witness",
                "exact hdivides_witness",
            ),
            "The quotient supplied by Primorial monotonicity is positive.",
        ),
        spec(
            PRIMORIAL_LE_MONOTONE,
            "forall m n x y. "
            f"({monotone_index_bound}) -> ({monotone_before}) -> "
            f"({monotone_after}) -> ({monotone_result})",
            (PRIMORIAL_LE_POSITIVE_QUOTIENT,),
            (
                "intro m",
                "intro n",
                "intro x",
                "intro y",
                "intro hle",
                "intro hbefore",
                "intro hafter",
                "have hquotient : exists q. y = x * S q",
                "specialize primorial_le_positive_quotient m",
                "specialize primorial_le_positive_quotient n",
                "specialize primorial_le_positive_quotient x",
                "specialize primorial_le_positive_quotient y",
                "apply primorial_le_positive_quotient",
                "exact hle",
                "exact hbefore",
                "exact hafter",
                "cases hquotient",
                "exists x * x1",
                "trans x * S x1",
                "symm",
                "apply PA6",
                "symm",
                "exact hquotient_witness",
            ),
            "Primorial is weakly increasing in its inclusive index.",
        ),
    )


__all__ = ["make_bertrand_primorial_membership_candidate_theorems"]
