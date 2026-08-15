"""Offset selector intervals and prefix splitting for the Bertrand primorial.

``PrimorialInterval(a,l,z)`` is the Product of ``l`` selector factors whose
local position ``i`` selects at global position ``a + i``.  It therefore
represents the prime-or-one candidates ``a+1`` through ``a+l``.  The final
row splits ``Primorial(a+l,z)`` into ``Primorial(a,x)`` and such an interval
without identifying independently constructed beta codes.

Every helper expands to ordinary first-order Peano arithmetic before parsing.
The module is deliberately absent from the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _factor_choice_rendered,
    _lt_term,
    _primorial_factor_prefix_term,
    _primorial_relation_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.finite_fold_surface import _product_relation_term


PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXTEND = (
    "primorial_interval_factor_prefix_extend"
)
PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXISTS = (
    "primorial_interval_factor_prefix_exists"
)
PRIMORIAL_INTERVAL_FACTOR_PREFIX_TRANSPORT_ENTRY = (
    "primorial_interval_factor_prefix_transport_entry"
)
PRIMORIAL_INTERVAL_EXISTS = "primorial_interval_exists"
PRIMORIAL_INTERVAL_FUNCTIONAL = "primorial_interval_functional"
PRIMORIAL_INTERVAL_FACTOR_PREFIX_SHIFT = (
    "primorial_interval_factor_prefix_shift"
)
PRIMORIAL_FACTOR_PREFIX_RESTRICT_ADD = (
    "primorial_factor_prefix_restrict_add"
)
PRIMORIAL_PREFIX_INTERVAL_SPLIT = "primorial_prefix_interval_split"


def _interval_factor_prefix_rendered(
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("index", "value"))
    local_avoid = avoid + (index, value)
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
        avoid=local_avoid,
    )
    decoded = _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local_avoid,
    )
    choice = _factor_choice_rendered(
        f"{offset} + {index}",
        value,
        tag=f"{tag}_choice",
        avoid=local_avoid,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _primorial_interval_factor_prefix_term(
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_offset = _render_term(
        offset,
        label="primorial interval offset",
        context=context,
    )
    rendered_code = _render_term(
        code,
        label="primorial interval factor code",
        context=context,
    )
    rendered_scale = _render_term(
        scale,
        label="primorial interval factor scale",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="primorial interval length",
        context=context,
    )
    return _interval_factor_prefix_rendered(
        rendered_offset,
        rendered_code,
        rendered_scale,
        rendered_length,
        tag=tag,
        avoid=context,
    )


def _primorial_interval_relation_term(
    offset: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_offset = _render_term(
        offset,
        label="primorial interval offset",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="primorial interval length",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="primorial interval value",
        context=context,
    )
    code, scale = _binders(tag, context, ("code", "scale"))
    local_avoid = context + (code, scale)
    prefix = _interval_factor_prefix_rendered(
        rendered_offset,
        code,
        scale,
        rendered_length,
        tag=f"{tag}_mask",
        avoid=local_avoid,
    )
    product = _product_relation_term(
        code,
        scale,
        rendered_length,
        rendered_value,
        tag=f"{tag}_product",
        avoid=local_avoid,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def make_bertrand_primorial_interval_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered Primorial interval and split tranche."""

    extend_variables = ("a", "b", "c", "l")
    extend_before = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpifpe_before",
        variables=extend_variables,
    )
    extend_after = _primorial_interval_factor_prefix_term(
        "a",
        "d",
        "e",
        "S l",
        tag="bpifpe_after",
        variables=("a", "b", "c", "l", "d", "e"),
    )
    extend_choice = _factor_choice_rendered(
        "a + l",
        "x",
        tag="bpifpe_last_choice",
        avoid=("a", "b", "c", "l", "x"),
    )
    extend_avoid = ("a", "b", "c", "l", "x", "d", "e", "i", "p")
    extend_append = _beta_at_term(
        "d",
        "e",
        "l",
        "x",
        tag="bpifpe_append",
        avoid=extend_avoid,
    )
    extend_old_bound = _lt_term(
        "i",
        "l",
        tag="bpifpe_old_bound",
        avoid=extend_avoid,
    )
    extend_old_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpifpe_old",
        avoid=extend_avoid,
    )
    extend_new_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpifpe_new",
        avoid=extend_avoid,
    )
    extend_relation = (
        f"exists d e. (({extend_append}) /\\ forall i p. "
        f"({extend_old_bound}) -> ({extend_old_decoded}) -> "
        f"({extend_new_decoded}))"
    )
    extend_hold_variables = (
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
        tag="bpifpe_hold_decoded",
        avoid=extend_hold_variables,
    )
    extend_hold_choice = _factor_choice_rendered(
        "a + i",
        "p",
        tag="bpifpe_hold_choice",
        avoid=extend_hold_variables,
    )
    extend_old_entry = (
        f"exists p. (({extend_hold_decoded}) /\\ ({extend_hold_choice}))"
    )

    prefix_exists = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpifpx_result",
        variables=("a", "l", "b", "c"),
    )
    prefix_previous = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpifpx_previous",
        variables=("a", "l", "b", "c"),
    )
    prefix_successor = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "S l",
        tag="bpifpx_successor",
        variables=("a", "l", "b", "c"),
    )

    transport_variables = ("a", "b", "c", "d", "e", "l", "i", "p")
    transport_left = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpifpt_left",
        variables=transport_variables,
    )
    transport_right = _primorial_interval_factor_prefix_term(
        "a",
        "d",
        "e",
        "l",
        tag="bpifpt_right",
        variables=transport_variables,
    )
    transport_bound = _lt_term(
        "i",
        "l",
        tag="bpifpt_bound",
        avoid=transport_variables,
    )
    transport_source = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpifpt_source",
        avoid=transport_variables,
    )
    transport_target = _beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpifpt_target",
        avoid=transport_variables,
    )
    transport_left_entry_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "q",
        tag="bpifpt_left_entry",
        avoid=transport_variables + ("q",),
    )
    transport_left_entry_choice = _factor_choice_rendered(
        "a + i",
        "q",
        tag="bpifpt_left_choice",
        avoid=transport_variables + ("q",),
    )
    transport_left_entry = (
        f"exists q. (({transport_left_entry_decoded}) /\\ "
        f"({transport_left_entry_choice}))"
    )
    transport_right_entry_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "r",
        tag="bpifpt_right_entry",
        avoid=transport_variables + ("q", "r"),
    )
    transport_right_entry_choice = _factor_choice_rendered(
        "a + i",
        "r",
        tag="bpifpt_right_choice",
        avoid=transport_variables + ("q", "r"),
    )
    transport_right_entry = (
        f"exists r. (({transport_right_entry_decoded}) /\\ "
        f"({transport_right_entry_choice}))"
    )

    exists_relation = _primorial_interval_relation_term(
        "a",
        "l",
        "z",
        tag="bpi_exists",
        variables=("a", "l", "z"),
    )
    exists_prefix = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpi_exists_prefix",
        variables=("a", "l", "b", "c"),
    )
    exists_product = _product_relation_term(
        "x",
        "x1",
        "l",
        "z",
        tag="bpi_exists_product",
        avoid=("a", "l", "x", "x1", "z"),
    )

    functional_variables = ("a", "l", "x", "y")
    functional_left = _primorial_interval_relation_term(
        "a",
        "l",
        "x",
        tag="bpi_functional_left",
        variables=functional_variables,
    )
    functional_right = _primorial_interval_relation_term(
        "a",
        "l",
        "y",
        tag="bpi_functional_right",
        variables=functional_variables,
    )
    functional_local_variables = (
        "a",
        "l",
        "x",
        "y",
        "x1",
        "x2",
        "x3",
        "x4",
        "i",
        "p",
    )
    functional_bound = _lt_term(
        "i",
        "l",
        tag="bpi_functional_bound",
        avoid=functional_local_variables,
    )
    functional_source_entry = _beta_at_term(
        "x1",
        "x2",
        "i",
        "p",
        tag="bpi_functional_source_entry",
        avoid=functional_local_variables,
    )
    functional_target_entry = _beta_at_term(
        "x3",
        "x4",
        "i",
        "p",
        tag="bpi_functional_target_entry",
        avoid=functional_local_variables,
    )
    functional_transport_product = _product_relation_term(
        "x3",
        "x4",
        "l",
        "x",
        tag="bpi_functional_transport",
        avoid=("a", "l", "x", "y", "x1", "x2", "x3", "x4"),
    )

    shift_variables = ("a", "b", "c", "d", "e", "l", "i", "p")
    shift_source_prefix = _primorial_factor_prefix_term(
        "b",
        "c",
        "a + l",
        tag="bpifps_source",
        variables=shift_variables,
    )
    shift_interval_prefix = _primorial_interval_factor_prefix_term(
        "a",
        "d",
        "e",
        "l",
        tag="bpifps_interval",
        variables=shift_variables,
    )
    shift_bound = _lt_term(
        "i",
        "l",
        tag="bpifps_bound",
        avoid=shift_variables,
    )
    shift_source_entry = _beta_at_term(
        "b",
        "c",
        "a + i",
        "p",
        tag="bpifps_source_entry",
        avoid=shift_variables,
    )
    shift_target_entry = _beta_at_term(
        "d",
        "e",
        "i",
        "p",
        tag="bpifps_target_entry",
        avoid=shift_variables,
    )
    shift_source_bound = _lt_term(
        "a + i",
        "a + l",
        tag="bpifps_source_bound",
        avoid=shift_variables,
    )
    (shift_bound_gap,) = _binders(
        "bpifps_shifted_bound",
        shift_variables,
        ("gap",),
    )
    shift_source_bound_raw = (
        f"exists {shift_bound_gap}. "
        f"{shift_bound_gap} + (a + S i) = a + l"
    )
    shift_source_local_decoded = _beta_at_term(
        "b",
        "c",
        "a + i",
        "q",
        tag="bpifps_source_local",
        avoid=shift_variables + ("q",),
    )
    shift_source_local_choice = _factor_choice_rendered(
        "a + i",
        "q",
        tag="bpifps_source_choice",
        avoid=shift_variables + ("q",),
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
        tag="bpifps_interval_local",
        avoid=shift_variables + ("q", "r"),
    )
    shift_interval_local_choice = _factor_choice_rendered(
        "a + i",
        "r",
        tag="bpifps_interval_choice",
        avoid=shift_variables + ("q", "r"),
    )
    shift_interval_local = (
        f"exists r. (({shift_interval_local_decoded}) /\\ "
        f"({shift_interval_local_choice}))"
    )

    restrict_variables = ("a", "b", "c", "l")
    restrict_source = _primorial_factor_prefix_term(
        "b",
        "c",
        "a + l",
        tag="bpfpra_source",
        variables=restrict_variables,
    )
    restrict_target = _primorial_factor_prefix_term(
        "b",
        "c",
        "a",
        tag="bpfpra_target",
        variables=restrict_variables,
    )

    split_source = _primorial_relation_term(
        "a + l",
        "z",
        tag="bppis_source",
        variables=("a", "l", "z"),
    )
    split_prefix = _primorial_relation_term(
        "a",
        "x",
        tag="bppis_prefix",
        variables=("a", "l", "z", "x", "y"),
    )
    split_interval = _primorial_interval_relation_term(
        "a",
        "l",
        "y",
        tag="bppis_interval",
        variables=("a", "l", "z", "x", "y"),
    )
    split_result = (
        f"exists x y. ({split_prefix}) /\\ "
        f"(({split_interval}) /\\ z = x * y)"
    )
    split_restricted_prefix = _primorial_factor_prefix_term(
        "x",
        "x1",
        "a",
        tag="bppis_restricted",
        variables=("a", "l", "z", "x", "x1"),
    )
    split_interval_prefix = _primorial_interval_factor_prefix_term(
        "a",
        "d",
        "e",
        "l",
        tag="bppis_interval_prefix",
        variables=("a", "l", "z", "x", "x1", "d", "e"),
    )
    split_shift_bound = _lt_term(
        "i",
        "l",
        tag="bppis_shift_bound",
        avoid=("a", "l", "z", "x", "x1", "d", "e", "i", "p"),
    )
    split_shift_source = _beta_at_term(
        "x",
        "x1",
        "a + i",
        "p",
        tag="bppis_shift_source",
        avoid=("a", "l", "z", "x", "x1", "d", "e", "i", "p"),
    )
    split_shift_target = _beta_at_term(
        "x2",
        "x3",
        "i",
        "p",
        tag="bppis_shift_target",
        avoid=("a", "l", "z", "x", "x1", "x2", "x3", "i", "p"),
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
        tag="bppis_prefix_product",
        avoid=("a", "l", "z", "x", "x1", "d", "e", "p", "q"),
    )
    split_interval_product = _product_relation_term(
        "x2",
        "x3",
        "l",
        "q",
        tag="bppis_interval_product",
        avoid=("a", "l", "z", "x", "x1", "x2", "x3", "p", "q"),
    )
    split_products = (
        f"exists p q. ({split_prefix_product}) /\\ "
        f"(({split_interval_product}) /\\ z = p * q)"
    )

    return (
        spec(
            PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXTEND,
            "forall a b c l. "
            f"({extend_before}) -> exists d e. ({extend_after})",
            (
                "primorial_factor_choice_exists",
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro l",
                "intro hprefix",
                f"have hchoice : exists x. ({extend_choice})",
                "apply primorial_factor_choice_exists",
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
                "have hsplit : i = l \/ exists gap. gap + S i = l",
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
            "Append one offset selector while preserving the prior interval.",
        ),
        spec(
            PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXISTS,
            f"forall a l. exists b c. ({prefix_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXTEND,
            ),
            (
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
                "apply primorial_interval_factor_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every offset and length has a beta-coded selector interval.",
        ),
        spec(
            PRIMORIAL_INTERVAL_FACTOR_PREFIX_TRANSPORT_ENTRY,
            "forall a b c d e l. "
            f"({transport_left}) -> ({transport_right}) -> forall i p. "
            f"({transport_bound}) -> ({transport_source}) -> "
            f"({transport_target})",
            (
                "beta_at_unique",
                "primorial_factor_choice_functional",
            ),
            (
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
                "have hpq : p = x",
                "apply beta_at_unique",
                "exact hp",
                "exact hleft_entry_witness_left",
                "have hqr : x = x1",
                "apply primorial_factor_choice_functional",
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
            "Any two offset selector prefixes decode the same bounded entry.",
        ),
        spec(
            PRIMORIAL_INTERVAL_EXISTS,
            f"forall a l. exists z. ({exists_relation})",
            (
                "beta_product_exists",
                PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXISTS,
            ),
            (
                "intro a",
                "intro l",
                f"have hprefix : exists b c. ({exists_prefix})",
                "apply primorial_interval_factor_prefix_exists",
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
            "Every offset interval has a relational product value.",
        ),
        spec(
            PRIMORIAL_INTERVAL_FUNCTIONAL,
            "forall a l x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y",
            (
                "beta_product_transport_prefix",
                "beta_product_functional",
                PRIMORIAL_INTERVAL_FACTOR_PREFIX_TRANSPORT_ENTRY,
            ),
            (
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
                "specialize primorial_interval_factor_prefix_transport_entry a",
                "specialize primorial_interval_factor_prefix_transport_entry x1",
                "specialize primorial_interval_factor_prefix_transport_entry x2",
                "specialize primorial_interval_factor_prefix_transport_entry x3",
                "specialize primorial_interval_factor_prefix_transport_entry x4",
                "specialize primorial_interval_factor_prefix_transport_entry l",
                "apply primorial_interval_factor_prefix_transport_entry",
                "exact hleft_witness_witness_left",
                "exact hright_witness_witness_left",
                f"have htransport : {functional_transport_product}",
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
            "The relational value of a fixed Primorial interval is unique.",
        ),
        spec(
            PRIMORIAL_INTERVAL_FACTOR_PREFIX_SHIFT,
            "forall a b c d e l. "
            f"({shift_source_prefix}) -> ({shift_interval_prefix}) -> "
            f"forall i p. ({shift_bound}) -> ({shift_source_entry}) -> "
            f"({shift_target_entry})",
            (
                "add_le_add_left",
                "beta_at_unique",
                "primorial_factor_choice_functional",
            ),
            (
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
                "apply primorial_factor_choice_functional",
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
            "Align a full Primorial mask with an independent offset interval.",
        ),
        spec(
            PRIMORIAL_FACTOR_PREFIX_RESTRICT_ADD,
            "forall a b c l. "
            f"({restrict_source}) -> ({restrict_target})",
            (
                "le_add_right",
                "lt_of_lt_of_le",
            ),
            (
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
            "Restrict a selector prefix of length a+l to its first a entries.",
        ),
        spec(
            PRIMORIAL_PREFIX_INTERVAL_SPLIT,
            "forall a l z. "
            f"({split_source}) -> ({split_result})",
            (
                "beta_product_prefix_suffix_split",
                PRIMORIAL_INTERVAL_FACTOR_PREFIX_EXISTS,
                PRIMORIAL_INTERVAL_FACTOR_PREFIX_SHIFT,
                PRIMORIAL_FACTOR_PREFIX_RESTRICT_ADD,
            ),
            (
                "intro a",
                "intro l",
                "intro z",
                "intro hprimorial",
                "cases hprimorial",
                "cases hprimorial_witness",
                "cases hprimorial_witness_witness",
                f"have hrestricted : {split_restricted_prefix}",
                "apply primorial_factor_prefix_restrict_add",
                "exact hprimorial_witness_witness_left",
                f"have hinterval : exists d e. ({split_interval_prefix})",
                "apply primorial_interval_factor_prefix_exists",
                "cases hinterval",
                "cases hinterval_witness",
                f"have hshift : {split_shift}",
                "specialize primorial_interval_factor_prefix_shift a",
                "specialize primorial_interval_factor_prefix_shift x",
                "specialize primorial_interval_factor_prefix_shift x1",
                "specialize primorial_interval_factor_prefix_shift x2",
                "specialize primorial_interval_factor_prefix_shift x3",
                "specialize primorial_interval_factor_prefix_shift l",
                "apply primorial_interval_factor_prefix_shift",
                "exact hprimorial_witness_witness_left",
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
                "exact hprimorial_witness_witness_right",
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
            "Split Primorial(a+l) into its prefix and offset interval product.",
        ),
    )


__all__ = ["make_bertrand_primorial_interval_candidate_theorems"]
