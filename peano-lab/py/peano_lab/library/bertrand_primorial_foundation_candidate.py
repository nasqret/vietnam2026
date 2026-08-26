"""Conservative dense-mask foundation for the Bertrand primorial.

The authoring relation ``Primorial(m,z)`` is the finite Product of the first
``m`` selector factors.  Selector position ``i`` contributes ``S i`` when it
is prime and contributes one otherwise.  Thus the dense prefix represents
exactly the product of the primes at most ``m`` without adding a list, set,
filter, Product, Prime, or Primorial primitive to the parser or kernel.

Every helper expands to ordinary first-order Peano arithmetic before parsing.
The public primorial helper accepts arbitrary terms in an explicitly supplied
context, so later zero, successor, and compound-index clients do not interpolate
unchecked source fragments.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_in_context, pretty_term
from peano_lab.library.bertrand_choose_foundation_candidate import _identifier
from peano_lab.library.finite_fold_surface import _product_relation_term


PRIMORIAL_FACTOR_CHOICE_EXISTS = "primorial_factor_choice_exists"
PRIMORIAL_FACTOR_CHOICE_FUNCTIONAL = "primorial_factor_choice_functional"
PRIMORIAL_FACTOR_PREFIX_EXTEND = "primorial_factor_prefix_extend"
PRIMORIAL_FACTOR_PREFIX_EXISTS = "primorial_factor_prefix_exists"
PRIMORIAL_FACTOR_PREFIX_TRANSPORT_ENTRY = (
    "primorial_factor_prefix_transport_entry"
)
PRIMORIAL_EXISTS = "primorial_exists"
PRIMORIAL_FUNCTIONAL = "primorial_functional"
PRIMORIAL_ZERO = "primorial_zero"
PRIMORIAL_SUCC_DECOMPOSE = "primorial_succ_decompose"
PRIMORIAL_POSITIVE = "primorial_positive"


def _validated_context(variables: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(variables, tuple):
        raise ValueError("primorial variables must be a tuple")
    context = tuple(
        _identifier(variable, "primorial context variable")
        for variable in variables
    )
    if len(set(context)) != len(context):
        raise ValueError("primorial context variables must be distinct")
    return context


def _render_term(
    source: str,
    *,
    label: str,
    context: tuple[str, ...],
) -> str:
    if not isinstance(source, str) or not source:
        raise ValueError(f"{label} must be a nonempty Peano term")
    try:
        term = parse_term_in_context(source, list(context))
    except ValueError as exc:
        raise ValueError(f"{label} must be a Peano term: {exc}") from None
    return pretty_term(term, list(context)).replace("·", "*")


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "primorial binder tag")
    names = tuple(f"bpr_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated primorial binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("height", "quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def _prime_term(
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left, right = _binders(tag, avoid, ("left", "right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _factor_choice_rendered(
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    selected = f"S ({index})"
    prime = _prime_term(
        selected,
        tag=f"{tag}_prime",
        avoid=avoid,
    )
    return (
        f"((({prime}) /\\ {value} = {selected}) \\/ "
        f"(~({prime}) /\\ {value} = 1))"
    )


def _primorial_factor_choice_term(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_index = _render_term(
        index,
        label="primorial selector index",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="primorial selector value",
        context=context,
    )
    return _factor_choice_rendered(
        rendered_index,
        rendered_value,
        tag=tag,
        avoid=context,
    )


def _factor_prefix_rendered(
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
        index,
        value,
        tag=f"{tag}_choice",
        avoid=local_avoid,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _primorial_factor_prefix_term(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(
        code,
        label="primorial factor code",
        context=context,
    )
    rendered_scale = _render_term(
        scale,
        label="primorial factor scale",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="primorial prefix length",
        context=context,
    )
    return _factor_prefix_rendered(
        rendered_code,
        rendered_scale,
        rendered_length,
        tag=tag,
        avoid=context,
    )


def _primorial_relation_term(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand the dense prime-mask Product at arbitrary Peano terms."""

    context = _validated_context(variables)
    rendered_index = _render_term(
        index,
        label="primorial index",
        context=context,
    )
    rendered_value = _render_term(
        value,
        label="primorial value",
        context=context,
    )
    code, scale = _binders(tag, context, ("code", "scale"))
    local_avoid = context + (code, scale)
    prefix = _factor_prefix_rendered(
        code,
        scale,
        rendered_index,
        tag=f"{tag}_mask",
        avoid=local_avoid,
    )
    product = _product_relation_term(
        code,
        scale,
        rendered_index,
        rendered_value,
        tag=f"{tag}_product",
        avoid=local_avoid,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def make_bertrand_primorial_foundation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered dense-mask Primorial foundation."""

    choice_exists = _primorial_factor_choice_term(
        "i",
        "a",
        tag="bpfc_exists",
        variables=("i", "a"),
    )
    choice_functional_variables = ("i", "a", "z")
    choice_functional_left = _primorial_factor_choice_term(
        "i",
        "a",
        tag="bpfcf_left",
        variables=choice_functional_variables,
    )
    choice_functional_right = _primorial_factor_choice_term(
        "i",
        "z",
        tag="bpfcf_right",
        variables=choice_functional_variables,
    )

    extend_variables = ("b", "c", "m")
    extend_before = _primorial_factor_prefix_term(
        "b",
        "c",
        "m",
        tag="bpfpe_before",
        variables=extend_variables,
    )
    extend_after = _primorial_factor_prefix_term(
        "d",
        "e",
        "S m",
        tag="bpfpe_after",
        variables=("b", "c", "m", "d", "e"),
    )
    extend_choice = _primorial_factor_choice_term(
        "m",
        "x",
        tag="bpfpe_last_choice",
        variables=("b", "c", "m", "x"),
    )
    extend_avoid = ("b", "c", "m", "x", "d", "e", "i", "a")
    extend_append = _beta_at_term(
        "d",
        "e",
        "m",
        "x",
        tag="bpfpe_append",
        avoid=extend_avoid,
    )
    extend_old_bound = _lt_term(
        "i",
        "m",
        tag="bpfpe_old_bound",
        avoid=extend_avoid,
    )
    extend_old_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpfpe_old",
        avoid=extend_avoid,
    )
    extend_new_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "a",
        tag="bpfpe_new",
        avoid=extend_avoid,
    )
    extend_relation = (
        f"exists d e. (({extend_append}) /\\ "
        "forall i a. "
        f"({extend_old_bound}) -> ({extend_old_decoded}) -> "
        f"({extend_new_decoded}))"
    )
    extend_hold_variables = ("b", "c", "m", "x", "x1", "x2", "i", "a")
    extend_hold_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpfpe_hold_decoded",
        avoid=extend_hold_variables,
    )
    extend_hold_choice = _primorial_factor_choice_term(
        "i",
        "a",
        tag="bpfpe_hold_choice",
        variables=extend_hold_variables,
    )
    extend_old_entry = (
        f"exists a. (({extend_hold_decoded}) /\\ ({extend_hold_choice}))"
    )

    prefix_exists = _primorial_factor_prefix_term(
        "b",
        "c",
        "m",
        tag="bpfpx_result",
        variables=("m", "b", "c"),
    )
    prefix_previous = _primorial_factor_prefix_term(
        "b",
        "c",
        "m",
        tag="bpfpx_previous",
        variables=("m", "b", "c"),
    )
    prefix_successor = _primorial_factor_prefix_term(
        "b",
        "c",
        "S m",
        tag="bpfpx_successor",
        variables=("m", "b", "c"),
    )

    transport_variables = ("b", "c", "d", "e", "m", "i", "a")
    transport_left = _primorial_factor_prefix_term(
        "b",
        "c",
        "m",
        tag="bpfpt_left",
        variables=transport_variables,
    )
    transport_right = _primorial_factor_prefix_term(
        "d",
        "e",
        "m",
        tag="bpfpt_right",
        variables=transport_variables,
    )
    transport_bound = _lt_term(
        "i",
        "m",
        tag="bpfpt_bound",
        avoid=transport_variables,
    )
    transport_source = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bpfpt_source",
        avoid=transport_variables,
    )
    transport_target = _beta_at_term(
        "d",
        "e",
        "i",
        "a",
        tag="bpfpt_target",
        avoid=transport_variables,
    )
    transport_left_entry_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "p",
        tag="bpfpt_left_entry",
        avoid=transport_variables + ("p",),
    )
    transport_left_entry_choice = _primorial_factor_choice_term(
        "i",
        "p",
        tag="bpfpt_left_choice",
        variables=transport_variables + ("p",),
    )
    transport_left_entry = (
        f"exists p. (({transport_left_entry_decoded}) /\\ "
        f"({transport_left_entry_choice}))"
    )
    transport_right_entry_decoded = _beta_at_term(
        "d",
        "e",
        "i",
        "q",
        tag="bpfpt_right_entry",
        avoid=transport_variables + ("q",),
    )
    transport_right_entry_choice = _primorial_factor_choice_term(
        "i",
        "q",
        tag="bpfpt_right_choice",
        variables=transport_variables + ("q",),
    )
    transport_right_entry = (
        f"exists q. (({transport_right_entry_decoded}) /\\ "
        f"({transport_right_entry_choice}))"
    )

    exists_relation = _primorial_relation_term(
        "m",
        "z",
        tag="bp_exists",
        variables=("m", "z"),
    )
    exists_product_witness = _product_relation_term(
        "x",
        "x1",
        "m",
        "z",
        tag="bp_exists_product_witness",
        avoid=("m", "x", "x1", "z"),
    )
    functional_variables = ("m", "x", "y")
    functional_left = _primorial_relation_term(
        "m",
        "x",
        tag="bp_functional_left",
        variables=functional_variables,
    )
    functional_right = _primorial_relation_term(
        "m",
        "y",
        tag="bp_functional_right",
        variables=functional_variables,
    )
    functional_local_variables = (
        "m",
        "x",
        "y",
        "x1",
        "x2",
        "x3",
        "x4",
        "i",
        "a",
    )
    functional_bound = _lt_term(
        "i",
        "m",
        tag="bp_functional_bound",
        avoid=functional_local_variables,
    )
    functional_source_entry = _beta_at_term(
        "x1",
        "x2",
        "i",
        "a",
        tag="bp_functional_source_entry",
        avoid=functional_local_variables,
    )
    functional_target_entry = _beta_at_term(
        "x3",
        "x4",
        "i",
        "a",
        tag="bp_functional_target_entry",
        avoid=functional_local_variables,
    )
    functional_transport_product = _product_relation_term(
        "x3",
        "x4",
        "m",
        "x",
        tag="bp_functional_transport",
        avoid=("m", "x", "y", "x1", "x2", "x3", "x4"),
    )

    zero_relation = _primorial_relation_term(
        "0",
        "z",
        tag="bp_zero_source",
        variables=("z",),
    )
    successor_relation = _primorial_relation_term(
        "S m",
        "z",
        tag="bp_succ_source",
        variables=("m", "z"),
    )
    predecessor_variables = ("m", "z", "p", "r")
    predecessor_relation = _primorial_relation_term(
        "m",
        "r",
        tag="bp_succ_predecessor",
        variables=predecessor_variables,
    )
    successor_choice = _primorial_factor_choice_term(
        "m",
        "p",
        tag="bp_succ_factor",
        variables=predecessor_variables,
    )
    successor_result = (
        "exists p r. "
        f"({successor_choice}) /\\ (({predecessor_relation}) /\\ z = r * p)"
    )
    successor_last_factor = _beta_at_term(
        "x",
        "x1",
        "m",
        "p",
        tag="bp_succ_last_factor",
        avoid=("m", "z", "x", "x1", "p", "r"),
    )
    successor_prefix_product = _product_relation_term(
        "x",
        "x1",
        "m",
        "r",
        tag="bp_succ_prefix_product",
        avoid=("m", "z", "x", "x1", "p", "r"),
    )
    successor_mask_terminal = _beta_at_term(
        "x",
        "x1",
        "m",
        "a",
        tag="bp_succ_mask_terminal",
        avoid=("m", "z", "x", "x1", "x2", "x3", "a"),
    )
    successor_mask_choice = _primorial_factor_choice_term(
        "m",
        "a",
        tag="bp_succ_mask_choice",
        variables=("m", "z", "x", "x1", "x2", "x3", "a"),
    )

    positive_relation = _primorial_relation_term(
        "m",
        "z",
        tag="bp_positive_source",
        variables=("m", "z"),
    )

    return (
        spec(
            PRIMORIAL_FACTOR_CHOICE_EXISTS,
            f"forall i. exists a. ({choice_exists})",
            ("prime_decidable",),
            (
                "intro i",
                "specialize prime_decidable (S i)",
                "cases prime_decidable",
                "exists S i",
                "left",
                "split",
                "exact prime_decidable_left",
                "refl",
                "exists 1",
                "right",
                "split",
                "exact prime_decidable_right",
                "refl",
            ),
            "Every index has its exact prime-or-one selector factor.",
        ),
        spec(
            PRIMORIAL_FACTOR_CHOICE_FUNCTIONAL,
            "forall i a z. "
            f"({choice_functional_left}) -> "
            f"({choice_functional_right}) -> a = z",
            (),
            (
                "intro i",
                "intro a",
                "intro z",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_left",
                "cases hright",
                "cases hright_left",
                "trans S i",
                "exact hleft_left_right",
                "symm",
                "exact hright_left_right",
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
            "The prime-or-one selector factor at a fixed index is unique.",
        ),
        spec(
            PRIMORIAL_FACTOR_PREFIX_EXTEND,
            "forall b c m. "
            f"({extend_before}) -> exists d e. ({extend_after})",
            (
                PRIMORIAL_FACTOR_CHOICE_EXISTS,
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
            ),
            (
                "intro b",
                "intro c",
                "intro m",
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
                "have hsplit : i = m \\/ exists gap. gap + S i = m",
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
            "Append one selector factor while preserving the previous prefix.",
        ),
        spec(
            PRIMORIAL_FACTOR_PREFIX_EXISTS,
            f"forall m. exists b c. ({prefix_exists})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                PRIMORIAL_FACTOR_PREFIX_EXTEND,
            ),
            (
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
                "apply primorial_factor_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hnext",
            ),
            "Every finite length has a beta-coded selector prefix.",
        ),
        spec(
            PRIMORIAL_FACTOR_PREFIX_TRANSPORT_ENTRY,
            "forall b c d e m. "
            f"({transport_left}) -> ({transport_right}) -> "
            f"forall i a. ({transport_bound}) -> ({transport_source}) -> "
            f"({transport_target})",
            (
                "beta_at_unique",
                PRIMORIAL_FACTOR_CHOICE_FUNCTIONAL,
            ),
            (
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
                "apply primorial_factor_choice_functional",
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
            "Any two selector-prefix codes decode the same bounded entry.",
        ),
        spec(
            PRIMORIAL_EXISTS,
            f"forall m. exists z. ({exists_relation})",
            (
                "beta_product_exists",
                PRIMORIAL_FACTOR_PREFIX_EXISTS,
            ),
            (
                "intro m",
                f"have hprefix : exists b c. ({prefix_exists})",
                "apply primorial_factor_prefix_exists",
                "cases hprefix",
                "cases hprefix_witness",
                f"have hproduct : exists z. ({exists_product_witness})",
                "apply beta_product_exists",
                "cases hproduct",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "exact hproduct_witness",
            ),
            "Every natural index has a relational primorial value.",
        ),
        spec(
            PRIMORIAL_FUNCTIONAL,
            "forall m x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y",
            (
                "beta_product_transport_prefix",
                "beta_product_functional",
                PRIMORIAL_FACTOR_PREFIX_TRANSPORT_ENTRY,
            ),
            (
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
                f"({functional_bound}) -> ({functional_source_entry}) -> "
                f"({functional_target_entry})",
                "specialize primorial_factor_prefix_transport_entry x1",
                "specialize primorial_factor_prefix_transport_entry x2",
                "specialize primorial_factor_prefix_transport_entry x3",
                "specialize primorial_factor_prefix_transport_entry x4",
                "specialize primorial_factor_prefix_transport_entry m",
                "apply primorial_factor_prefix_transport_entry",
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
            "The relational primorial value at a fixed index is unique.",
        ),
        spec(
            PRIMORIAL_ZERO,
            f"forall z. ({zero_relation}) -> z = 1",
            ("beta_product_zero",),
            (
                "intro z",
                "intro hprimorial",
                "cases hprimorial",
                "cases hprimorial_witness",
                "cases hprimorial_witness_witness",
                "apply beta_product_zero",
                "exact hprimorial_witness_witness_right",
            ),
            "The empty dense selector product is one.",
        ),
        spec(
            PRIMORIAL_SUCC_DECOMPOSE,
            f"forall m z. ({successor_relation}) -> ({successor_result})",
            (
                "beta_product_succ_decompose",
                "beta_at_unique",
                "le_refl",
                "le_succ",
            ),
            (
                "intro m",
                "intro z",
                "intro hprimorial",
                "cases hprimorial",
                "cases hprimorial_witness",
                "cases hprimorial_witness_witness",
                "have hdecomposition : exists p r. "
                f"({successor_last_factor}) /\\ "
                f"(({successor_prefix_product}) /\\ z = r * p)",
                "apply beta_product_succ_decompose",
                "exact hprimorial_witness_witness_right",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "have hterminal : exists a. "
                f"(({successor_mask_terminal}) /\\ "
                f"({successor_mask_choice}))",
                "apply hprimorial_witness_witness_left",
                "apply le_refl",
                "cases hterminal",
                "cases hterminal_witness",
                "have hfactor : x2 = x4",
                "apply beta_at_unique",
                "exact hdecomposition_witness_witness_left",
                "exact hterminal_witness_left",
                "exists x4",
                "exists x3",
                "split",
                "exact hterminal_witness_right",
                "split",
                "exists x",
                "exists x1",
                "split",
                "intro i",
                "intro hi",
                "apply hprimorial_witness_witness_left",
                "apply le_succ",
                "exact hi",
                "exact hdecomposition_witness_witness_right_left",
                "trans x3 * x2",
                "exact hdecomposition_witness_witness_right_right",
                "rewrite hfactor",
                "refl",
            ),
            "A successor primorial splits into its previous value and selector.",
        ),
        spec(
            PRIMORIAL_POSITIVE,
            f"forall m z. ({positive_relation}) -> exists r. z = S r",
            (
                "mul_succ_left",
                PRIMORIAL_ZERO,
                PRIMORIAL_SUCC_DECOMPOSE,
            ),
            (
                "induction m",
                "intro z",
                "intro hprimorial",
                "have hz : z = 1",
                "apply primorial_zero",
                "exact hprimorial",
                "exists 0",
                "trans 1",
                "exact hz",
                "refl",
                "intro z",
                "intro hprimorial",
                f"have hdecomposition : {successor_result}",
                "apply primorial_succ_decompose",
                "exact hprimorial",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                "have hprevious : exists t. x1 = S t",
                "apply IH",
                "exact hdecomposition_witness_witness_right_left",
                "cases hprevious",
                "cases hdecomposition_witness_witness_left",
                "cases hdecomposition_witness_witness_left_left",
                "exists x2 * S m + m",
                "trans x1 * x",
                "exact hdecomposition_witness_witness_right_right",
                "rewrite hprevious_witness",
                "rewrite hdecomposition_witness_witness_left_left_right",
                "trans x2 * S m + S m",
                "apply mul_succ_left",
                "apply PA4",
                "cases hdecomposition_witness_witness_left_right",
                "exists x2 * 1 + 0",
                "trans x1 * x",
                "exact hdecomposition_witness_witness_right_right",
                "rewrite hprevious_witness",
                "rewrite hdecomposition_witness_witness_left_right_right",
                "trans x2 * 1 + 1",
                "apply mul_succ_left",
                "apply PA4",
            ),
            "Every relational primorial value is a successor.",
        ),
    )


__all__ = ["make_bertrand_primorial_foundation_candidate_theorems"]
