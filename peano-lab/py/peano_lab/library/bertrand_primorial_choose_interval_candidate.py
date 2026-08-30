"""Prime divisibility and Choose bounds for Primorial intervals.

This isolated ten-row tranche connects the beta-coded factorial, Choose, and
offset Primorial-interval relations.  It proves that an interval product whose
prime candidates lie strictly above both factorial denominator indices divides
the corresponding binomial coefficient, then specializes that fact to the
even central and odd middle coefficients used by the Bertrand bound.

Every helper below expands to ordinary first-order Peano arithmetic before
parsing.  The module deliberately performs no registry or edition mutation.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
)
from peano_lab.library.bertrand_primorial_duplicate_free_candidate import (
    _coprime_term,
    _divides_term,
    _le_term,
    _pointwise_divides_term,
    _product_term,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _factor_choice_rendered,
    _lt_term,
    _prime_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.bertrand_primorial_interval_candidate import (
    _primorial_interval_factor_prefix_term,
    _primorial_interval_relation_term,
)
from peano_lab.library.finite_factorial_theorems import factorial_relation


FACTORIAL_PRIME_DIVIDES_OF_LE = "factorial_prime_divides_of_le"
FACTORIAL_PRIME_LE_OF_DIVIDES = "factorial_prime_le_of_divides"
CHOOSE_PRIME_DIVIDES_BETWEEN = "choose_prime_divides_between"
BETA_PAIRWISE_COPRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE = (
    "beta_pairwise_coprime_product_divides_common_multiple"
)
PRIMORIAL_INTERVAL_PAIRWISE_COPRIME = (
    "primorial_interval_pairwise_coprime"
)
PRIMORIAL_INTERVAL_DIVIDES_CHOOSE_BETWEEN = (
    "primorial_interval_divides_choose_between"
)
PRIMORIAL_EVEN_INTERVAL_DIVIDES_CENTRAL = (
    "primorial_even_interval_divides_central"
)
PRIMORIAL_ODD_INTERVAL_DIVIDES_MIDDLE = (
    "primorial_odd_interval_divides_middle"
)
PRIMORIAL_EVEN_INTERVAL_LE_CENTRAL = (
    "primorial_even_interval_le_central"
)
PRIMORIAL_ODD_INTERVAL_LE_MIDDLE = (
    "primorial_odd_interval_le_middle"
)


def _prime_relation_term(
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered = _render_term(value, label="prime term", context=context)
    return _prime_term(rendered, tag=tag, avoid=context)


def _pairwise_coprime_prefix_term(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered_code = _render_term(code, label="pairwise code", context=context)
    rendered_scale = _render_term(
        scale,
        label="pairwise scale",
        context=context,
    )
    rendered_length = _render_term(
        length,
        label="pairwise length",
        context=context,
    )
    i, j, p, q = _binders(
        tag,
        context,
        ("left_index", "right_index", "left_value", "right_value"),
    )
    local = context + (i, j, p, q)
    left_bound = _lt_term(
        i,
        rendered_length,
        tag=f"{tag}_left_bound",
        avoid=local,
    )
    right_bound = _lt_term(
        j,
        rendered_length,
        tag=f"{tag}_right_bound",
        avoid=local,
    )
    left_at = _beta_at_term(
        rendered_code,
        rendered_scale,
        i,
        p,
        tag=f"{tag}_left_at",
        avoid=local,
    )
    right_at = _beta_at_term(
        rendered_code,
        rendered_scale,
        j,
        q,
        tag=f"{tag}_right_at",
        avoid=local,
    )
    coprime = _coprime_term(
        p,
        q,
        tag=f"{tag}_coprime",
        variables=local,
    )
    return (
        f"forall {i} {j} {p} {q}. ({left_bound}) -> ({right_bound}) -> "
        f"({left_at}) -> ({right_at}) -> ~({i} = {j}) -> ({coprime})"
    )


def make_bertrand_primorial_choose_interval_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered Primorial/Choose interval tranche."""

    factorial_variables = ("p", "n", "F")
    factorial_prime = _prime_relation_term(
        "p",
        tag="bfpdol_prime",
        variables=factorial_variables,
    )
    factorial_bound = _le_term(
        "p",
        "n",
        tag="bfpdol_bound",
        variables=factorial_variables,
    )
    factorial_source = factorial_relation("n", "F", tag="bfpdol_source")
    factorial_divides = _divides_term(
        "p",
        "F",
        tag="bfpdol_result",
        variables=factorial_variables,
    )
    factorial_entry = _beta_at_term(
        "x1",
        "x2",
        "S x",
        "1 + S x",
        tag="bfpdol_entry",
        avoid=("p", "n", "F", "x", "x1", "x2"),
    )

    reverse_variables = ("p", "n", "F")
    reverse_prime = _prime_relation_term(
        "p",
        tag="bfplod_prime",
        variables=reverse_variables,
    )
    reverse_source = factorial_relation("n", "F", tag="bfplod_source")
    reverse_divides = _divides_term(
        "p",
        "F",
        tag="bfplod_divides",
        variables=reverse_variables,
    )
    reverse_bound = _le_term(
        "p",
        "n",
        tag="bfplod_result",
        variables=reverse_variables,
    )
    reverse_previous = factorial_relation("n", "r", tag="bfplod_previous")
    reverse_decomposition = (
        f"exists r. ({reverse_previous}) /\\ F = r * S n"
    )
    reverse_split_left = _divides_term(
        "p",
        "x",
        tag="bfplod_split_left",
        variables=("p", "n", "F", "x"),
    )
    reverse_split_right = _divides_term(
        "p",
        "S n",
        tag="bfplod_split_right",
        variables=("p", "n", "F", "x"),
    )
    reverse_split = f"({reverse_split_left}) \\/ ({reverse_split_right})"

    choose_variables = ("n", "k", "j", "p", "c")
    choose_prime = _prime_relation_term(
        "p",
        tag="bcpdb_prime",
        variables=choose_variables,
    )
    choose_left_bound = _lt_term(
        "k",
        "p",
        tag="bcpdb_left_bound",
        avoid=choose_variables,
    )
    choose_right_bound = _lt_term(
        "j",
        "p",
        tag="bcpdb_right_bound",
        avoid=choose_variables,
    )
    choose_upper_bound = _le_term(
        "p",
        "n",
        tag="bcpdb_upper_bound",
        variables=choose_variables,
    )
    choose_source = _choose_relation_term(
        "n",
        "k",
        "c",
        tag="bcpdb_source",
        variables=choose_variables,
    )
    choose_result = _divides_term(
        "p",
        "c",
        tag="bcpdb_result",
        variables=choose_variables,
    )
    choose_total_factorial = factorial_relation(
        "n", "F", tag="bcpdb_total_factorial"
    )
    choose_left_factorial = factorial_relation(
        "k", "K", tag="bcpdb_left_factorial"
    )
    choose_right_factorial = factorial_relation(
        "j", "J", tag="bcpdb_right_factorial"
    )
    choose_total_divides = _divides_term(
        "p",
        "x",
        tag="bcpdb_total_divides",
        variables=choose_variables + ("x", "x1", "x2"),
    )
    choose_split_outer_left = _divides_term(
        "p",
        "x1 * x2",
        tag="bcpdb_outer_left",
        variables=choose_variables + ("x", "x1", "x2"),
    )
    choose_split_outer_right = _divides_term(
        "p",
        "c",
        tag="bcpdb_outer_right",
        variables=choose_variables + ("x", "x1", "x2"),
    )
    choose_split_outer = (
        f"({choose_split_outer_left}) \\/ ({choose_split_outer_right})"
    )
    choose_split_inner_left = _divides_term(
        "p",
        "x1",
        tag="bcpdb_inner_left",
        variables=choose_variables + ("x", "x1", "x2"),
    )
    choose_split_inner_right = _divides_term(
        "p",
        "x2",
        tag="bcpdb_inner_right",
        variables=choose_variables + ("x", "x1", "x2"),
    )
    choose_split_inner = (
        f"({choose_split_inner_left}) \\/ ({choose_split_inner_right})"
    )

    product_variables = ("b", "c", "l", "n", "z")
    product_pairwise = _pairwise_coprime_prefix_term(
        "b",
        "c",
        "l",
        tag="bpcpdcm_pairwise",
        variables=product_variables,
    )
    product_pointwise = _pointwise_divides_term(
        "b",
        "c",
        "l",
        "z",
        tag="bpcpdcm_pointwise",
        variables=product_variables,
    )
    product_source = _product_term(
        "b",
        "c",
        "l",
        "n",
        tag="bpcpdcm_source",
        variables=product_variables,
    )
    product_result = _divides_term(
        "n",
        "z",
        tag="bpcpdcm_result",
        variables=product_variables,
    )
    product_last_at = _beta_at_term(
        "b",
        "c",
        "l",
        "p",
        tag="bpcpdcm_last",
        avoid=("b", "c", "l", "n", "z", "p", "r"),
    )
    product_prefix = _product_term(
        "b",
        "c",
        "l",
        "r",
        tag="bpcpdcm_prefix",
        variables=("b", "c", "l", "n", "z", "p", "r"),
    )
    product_decomposition = (
        f"exists p r. ({product_last_at}) /\\ "
        f"(({product_prefix}) /\\ n = r * p)"
    )
    product_prefix_pairwise = _pairwise_coprime_prefix_term(
        "b",
        "c",
        "l",
        tag="bpcpdcm_prefix_pairwise",
        variables=("b", "c", "l", "n", "z", "p", "r"),
    )
    product_prefix_pointwise = _pointwise_divides_term(
        "b",
        "c",
        "l",
        "z",
        tag="bpcpdcm_prefix_pointwise",
        variables=("b", "c", "l", "n", "z", "p", "r"),
    )
    product_local_coprime = _coprime_term(
        "x1",
        "x",
        tag="bpcpdcm_local_coprime",
        variables=("b", "c", "l", "n", "z", "x", "x1"),
    )

    pairwise_variables = ("a", "b", "c", "l")
    pairwise_prefix = _primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "l",
        tag="bpipc_source",
        variables=pairwise_variables,
    )
    pairwise_result = _pairwise_coprime_prefix_term(
        "b",
        "c",
        "l",
        tag="bpipc_result",
        variables=pairwise_variables,
    )
    pairwise_left_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bpipc_left_entry",
        avoid=("a", "b", "c", "l", "i", "j", "p", "q", "x"),
    )
    pairwise_left_choice = _factor_choice_rendered(
        "a + i",
        "x",
        tag="bpipc_left_choice",
        avoid=("a", "b", "c", "l", "i", "j", "p", "q", "x"),
    )
    pairwise_right_entry = _beta_at_term(
        "b",
        "c",
        "j",
        "x1",
        tag="bpipc_right_entry",
        avoid=(
            "a",
            "b",
            "c",
            "l",
            "i",
            "j",
            "p",
            "q",
            "x",
            "x1",
        ),
    )
    pairwise_right_choice = _factor_choice_rendered(
        "a + j",
        "x1",
        tag="bpipc_right_choice",
        avoid=(
            "a",
            "b",
            "c",
            "l",
            "i",
            "j",
            "p",
            "q",
            "x",
            "x1",
        ),
    )

    interval_variables = ("a", "l", "n", "k", "j", "c", "z")
    interval_choose = _choose_relation_term(
        "n",
        "k",
        "c",
        tag="bpidcb_choose",
        variables=interval_variables,
    )
    interval_source = _primorial_interval_relation_term(
        "a",
        "l",
        "z",
        tag="bpidcb_interval",
        variables=interval_variables,
    )
    interval_result = _divides_term(
        "z",
        "c",
        tag="bpidcb_result",
        variables=interval_variables,
    )
    interval_bound_index = "bpr_index_bpidcb_bounds"
    interval_bound_local = interval_variables + (interval_bound_index,)
    interval_index_bound = _lt_term(
        interval_bound_index,
        "l",
        tag="bpidcb_bounds_index",
        avoid=interval_bound_local,
    )
    interval_candidate = f"S (a + {interval_bound_index})"
    interval_left_bound = _lt_term(
        "k",
        interval_candidate,
        tag="bpidcb_bounds_left",
        avoid=interval_bound_local,
    )
    interval_right_bound = _lt_term(
        "j",
        interval_candidate,
        tag="bpidcb_bounds_right",
        avoid=interval_bound_local,
    )
    interval_upper_bound = _le_term(
        interval_candidate,
        "n",
        tag="bpidcb_bounds_upper",
        variables=interval_bound_local,
    )
    interval_bounds = (
        f"forall {interval_bound_index}. ({interval_index_bound}) -> "
        f"(({interval_left_bound}) /\\ (({interval_right_bound}) /\\ "
        f"({interval_upper_bound})))"
    )
    interval_pairwise = _pairwise_coprime_prefix_term(
        "x",
        "x1",
        "l",
        tag="bpidcb_pairwise",
        variables=interval_variables + ("x", "x1"),
    )
    interval_pointwise = _pointwise_divides_term(
        "x",
        "x1",
        "l",
        "c",
        tag="bpidcb_pointwise",
        variables=interval_variables + ("x", "x1"),
    )
    interval_local_entry = _beta_at_term(
        "x",
        "x1",
        "i",
        "x2",
        tag="bpidcb_local_entry",
        avoid=interval_variables + ("x", "x1", "i", "p", "x2"),
    )
    interval_local_choice = _factor_choice_rendered(
        "a + i",
        "x2",
        tag="bpidcb_local_choice",
        avoid=interval_variables + ("x", "x1", "i", "p", "x2"),
    )
    interval_local_variables = interval_variables + (
        "x",
        "x1",
        "i",
        "p",
        "x2",
    )
    interval_local_left_bound = _lt_term(
        "k",
        "S (a + i)",
        tag="bpidcb_local_left",
        avoid=interval_local_variables,
    )
    interval_local_right_bound = _lt_term(
        "j",
        "S (a + i)",
        tag="bpidcb_local_right",
        avoid=interval_local_variables,
    )
    interval_local_upper_bound = _le_term(
        "S (a + i)",
        "n",
        tag="bpidcb_local_upper",
        variables=interval_local_variables,
    )

    even_variables = ("n", "z", "c")
    even_interval = _primorial_interval_relation_term(
        "n",
        "n",
        "z",
        tag="bpeidc_interval",
        variables=even_variables,
    )
    even_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bpeidc_central",
        variables=even_variables,
    )
    even_divides = _divides_term(
        "z",
        "c",
        tag="bpeidc_result",
        variables=even_variables,
    )

    odd_variables = ("n", "z", "c")
    odd_interval = _primorial_interval_relation_term(
        "S n",
        "n",
        "z",
        tag="bpoidm_interval",
        variables=odd_variables,
    )
    odd_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "c",
        tag="bpoidm_middle",
        variables=odd_variables,
    )
    odd_divides = _divides_term(
        "z",
        "c",
        tag="bpoidm_result",
        variables=odd_variables,
    )

    even_le = _le_term(
        "z",
        "c",
        tag="bpeilc_result",
        variables=even_variables,
    )
    odd_le = _le_term(
        "z",
        "c",
        tag="bpoilm_result",
        variables=odd_variables,
    )

    return (
        spec(
            FACTORIAL_PRIME_DIVIDES_OF_LE,
            "forall p n F. "
            f"({factorial_prime}) -> ({factorial_bound}) -> "
            f"({factorial_source}) -> ({factorial_divides})",
            (
                "prime_is_succ_succ",
                "beta_factor_divides_product",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro p",
                "intro n",
                "intro F",
                "intro hp",
                "intro hle",
                "intro hfactorial",
                "have hshape : exists k. p = S (S k)",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hshape",
                "rewrite hshape_witness at hle",
                "cases hfactorial",
                "cases hfactorial_witness",
                "cases hfactorial_witness_witness",
                f"have hentry : {factorial_entry}",
                "apply hfactorial_witness_witness_left",
                "exact hle",
                "have hraw : exists q. F = (1 + S x) * q",
                "specialize beta_factor_divides_product x1",
                "specialize beta_factor_divides_product x2",
                "specialize beta_factor_divides_product n",
                "specialize beta_factor_divides_product F",
                "specialize beta_factor_divides_product (S x)",
                "specialize beta_factor_divides_product (1 + S x)",
                "apply beta_factor_divides_product",
                "exact hle",
                "exact hentry",
                "exact hfactorial_witness_witness_right",
                "cases hraw",
                "exists x3",
                "rewrite hshape_witness",
                "trans (1 + S x) * x3",
                "exact hraw_witness",
                "congr",
                "trans S (1 + x)",
                "apply PA4",
                "congr",
                "trans S (0 + x)",
                "specialize add_succ_left 0",
                "specialize add_succ_left x",
                "apply add_succ_left",
                "congr",
                "apply zero_add",
                "refl",
            ),
            "Every prime at most n divides the relational factorial n!.",
        ),
        spec(
            FACTORIAL_PRIME_LE_OF_DIVIDES,
            "forall p n F. "
            f"({reverse_prime}) -> ({reverse_source}) -> "
            f"({reverse_divides}) -> ({reverse_bound})",
            (
                "divisor_one",
                "le_succ",
                "euclid_prime_dvd_product",
                "divisor_le_nonzero",
                "succ_ne_zero",
                "factorial_zero",
                "factorial_succ_decompose",
            ),
            (
                "intro p",
                "induction n",
                "intro F",
                "intro hp",
                "cases hp",
                "intro hfactorial",
                "intro hdivides",
                "have hF_one : F = 1",
                "specialize factorial_zero 0",
                "specialize factorial_zero F",
                "apply factorial_zero",
                "refl",
                "exact hfactorial",
                "rewrite hF_one at hdivides",
                "have hp_one : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hdivides",
                "exfalso",
                "apply hp_left",
                "exact hp_one",
                "intro F",
                "intro hp",
                "cases hp",
                "intro hfactorial",
                "intro hdivides",
                f"have hdecomposition : {reverse_decomposition}",
                "specialize factorial_succ_decompose n",
                "specialize factorial_succ_decompose (S n)",
                "specialize factorial_succ_decompose F",
                "apply factorial_succ_decompose",
                "refl",
                "exact hfactorial",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "rewrite hdecomposition_witness_right at hdivides",
                f"have hsplit : {reverse_split}",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product x",
                "specialize euclid_prime_dvd_product (S n)",
                "apply euclid_prime_dvd_product",
                "split",
                "exact hp_left",
                "exact hp_right",
                "exact hdivides",
                "cases hsplit",
                "have hprevious : exists g. g + p = n",
                "specialize IH x",
                "apply IH",
                "split",
                "exact hp_left",
                "exact hp_right",
                "exact hdecomposition_witness_left",
                "exact hsplit_left",
                "specialize le_succ p",
                "specialize le_succ n",
                "apply le_succ",
                "exact hprevious",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero (S n)",
                "apply divisor_le_nonzero",
                "specialize succ_ne_zero n",
                "exact succ_ne_zero",
                "exact hsplit_right",
            ),
            "Every prime divisor of n! is at most n.",
        ),
        spec(
            CHOOSE_PRIME_DIVIDES_BETWEEN,
            "forall n k j p c. k + j = n -> "
            f"({choose_prime}) -> ({choose_left_bound}) -> "
            f"({choose_right_bound}) -> ({choose_upper_bound}) -> "
            f"({choose_source}) -> ({choose_result})",
            (
                "factorial_exists",
                "choose_factorial_bridge",
                FACTORIAL_PRIME_DIVIDES_OF_LE,
                "euclid_prime_dvd_product",
                FACTORIAL_PRIME_LE_OF_DIVIDES,
                "lt_not_le",
            ),
            (
                "intro n",
                "intro k",
                "intro j",
                "intro p",
                "intro c",
                "intro hsum",
                "intro hp",
                "intro hk",
                "intro hj",
                "intro hpn",
                "intro hchoose",
                f"have hF : exists F. ({choose_total_factorial})",
                "apply factorial_exists",
                "cases hF",
                f"have hK : exists K. ({choose_left_factorial})",
                "apply factorial_exists",
                "cases hK",
                f"have hJ : exists J. ({choose_right_factorial})",
                "apply factorial_exists",
                "cases hJ",
                "have hbridge : x = (x1 * x2) * c",
                "specialize choose_factorial_bridge n",
                "specialize choose_factorial_bridge k",
                "specialize choose_factorial_bridge j",
                "specialize choose_factorial_bridge c",
                "specialize choose_factorial_bridge x",
                "specialize choose_factorial_bridge x1",
                "specialize choose_factorial_bridge x2",
                "apply choose_factorial_bridge",
                "exact hsum",
                "exact hchoose",
                "exact hF_witness",
                "exact hK_witness",
                "exact hJ_witness",
                f"have htotal : {choose_total_divides}",
                "specialize factorial_prime_divides_of_le p",
                "specialize factorial_prime_divides_of_le n",
                "specialize factorial_prime_divides_of_le x",
                "apply factorial_prime_divides_of_le",
                "exact hp",
                "exact hpn",
                "exact hF_witness",
                "rewrite hbridge at htotal",
                f"have houter : {choose_split_outer}",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product (x1 * x2)",
                "specialize euclid_prime_dvd_product c",
                "apply euclid_prime_dvd_product",
                "exact hp",
                "exact htotal",
                "cases houter",
                f"have hinner : {choose_split_inner}",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product x1",
                "specialize euclid_prime_dvd_product x2",
                "apply euclid_prime_dvd_product",
                "exact hp",
                "exact houter_left",
                "cases hinner",
                "have hpk : exists g. g + p = k",
                "specialize factorial_prime_le_of_divides p",
                "specialize factorial_prime_le_of_divides k",
                "specialize factorial_prime_le_of_divides x1",
                "apply factorial_prime_le_of_divides",
                "exact hp",
                "exact hK_witness",
                "exact hinner_left",
                "exfalso",
                "specialize lt_not_le k",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hk",
                "exact hpk",
                "have hpj : exists g. g + p = j",
                "specialize factorial_prime_le_of_divides p",
                "specialize factorial_prime_le_of_divides j",
                "specialize factorial_prime_le_of_divides x2",
                "apply factorial_prime_le_of_divides",
                "exact hp",
                "exact hJ_witness",
                "exact hinner_right",
                "exfalso",
                "specialize lt_not_le j",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hj",
                "exact hpj",
                "exact houter_right",
            ),
            "A prime between both denominator indices and the row divides Choose.",
        ),
        spec(
            BETA_PAIRWISE_COPRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE,
            "forall b c l n z. "
            f"({product_pairwise}) -> ({product_pointwise}) -> "
            f"({product_source}) -> ({product_result})",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "one_multiple",
                "lt_irrefl_expanded",
                "beta_product_pointwise_coprime",
                "coprime_product_is_lcm",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro n",
                "intro z",
                "intro hpairwise",
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
                "intro hpairwise",
                "intro hpointwise",
                "intro hproduct",
                f"have hdecomposition : {product_decomposition}",
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
                f"have hprefix_pairwise : {product_prefix_pairwise}",
                "intro i",
                "intro j",
                "intro p",
                "intro q",
                "intro hi",
                "intro hj",
                "intro hp",
                "intro hq",
                "intro hij",
                "specialize hpairwise i",
                "specialize hpairwise j",
                "specialize hpairwise p",
                "specialize hpairwise q",
                "apply hpairwise",
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
                f"have hprefix_pointwise : {product_prefix_pointwise}",
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
                "exact hprefix_pairwise",
                "exact hprefix_pointwise",
                "exact hdecomposition_witness_witness_right_left",
                "have hlast_divides : exists q. z = x * q",
                "specialize hpointwise l",
                "specialize hpointwise x",
                "apply hpointwise",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_left",
                f"have hcoprime : {product_local_coprime}",
                "specialize beta_product_pointwise_coprime x",
                "specialize beta_product_pointwise_coprime b",
                "specialize beta_product_pointwise_coprime c",
                "specialize beta_product_pointwise_coprime l",
                "specialize beta_product_pointwise_coprime x1",
                "apply beta_product_pointwise_coprime",
                "intro i",
                "intro q",
                "intro hi",
                "intro hq",
                "specialize hpairwise i",
                "specialize hpairwise l",
                "specialize hpairwise q",
                "specialize hpairwise x",
                "apply hpairwise",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hq",
                "exact hdecomposition_witness_witness_left",
                "intro hil",
                "rewrite hil at hi",
                "specialize lt_irrefl_expanded l",
                "apply lt_irrefl_expanded",
                "exact hi",
                "exact hdecomposition_witness_witness_right_left",
                "have hlcm : ((((exists u. x1 * x = x1 * u) /\\ "
                "exists v. x1 * x = x * v) /\\ forall t. "
                "(exists a. t = x1 * a) -> "
                "(exists d. t = x * d) -> "
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
            "A pairwise-coprime product divides every common multiple of its factors.",
        ),
        spec(
            PRIMORIAL_INTERVAL_PAIRWISE_COPRIME,
            "forall a b c l. "
            f"({pairwise_prefix}) -> ({pairwise_result})",
            (
                "beta_at_unique",
                "add_left_cancel",
                "distinct_primes_coprime",
                "coprime_one_left",
                "coprime_one_right",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro l",
                "intro hprefix",
                "intro i",
                "intro j",
                "intro p",
                "intro q",
                "intro hi",
                "intro hj",
                "intro hp",
                "intro hq",
                "intro hij",
                f"have hleft : exists x. ({pairwise_left_entry}) /\\ "
                f"({pairwise_left_choice})",
                "apply hprefix",
                "exact hi",
                "cases hleft",
                "cases hleft_witness",
                f"have hright : exists x1. ({pairwise_right_entry}) /\\ "
                f"({pairwise_right_choice})",
                "apply hprefix",
                "exact hj",
                "cases hright",
                "cases hright_witness",
                "have hxp : x = p",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hleft_witness_left",
                "exact hp",
                "have hxq : x1 = q",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique q",
                "apply beta_at_unique",
                "exact hright_witness_left",
                "exact hq",
                "cases hleft_witness_right",
                "cases hright_witness_right",
                "cases hleft_witness_right_left",
                "cases hright_witness_right_left",
                "have hp_candidate : p = S (a + i)",
                "trans x",
                "symm",
                "exact hxp",
                "exact hleft_witness_right_left_right",
                "have hq_candidate : q = S (a + j)",
                "trans x1",
                "symm",
                "exact hxq",
                "exact hright_witness_right_left_right",
                "specialize distinct_primes_coprime p",
                "specialize distinct_primes_coprime q",
                "apply distinct_primes_coprime",
                "rewrite hp_candidate",
                "rewrite hp_candidate",
                "exact hleft_witness_right_left_left",
                "rewrite hq_candidate",
                "rewrite hq_candidate",
                "exact hright_witness_right_left_left",
                "intro hpq",
                "apply hij",
                "specialize add_left_cancel a",
                "specialize add_left_cancel i",
                "specialize add_left_cancel j",
                "apply add_left_cancel",
                "apply PA2",
                "trans p",
                "symm",
                "exact hp_candidate",
                "trans q",
                "exact hpq",
                "exact hq_candidate",
                "cases hleft_witness_right_left",
                "cases hright_witness_right_right",
                "have hp_candidate : p = S (a + i)",
                "trans x",
                "symm",
                "exact hxp",
                "exact hleft_witness_right_left_right",
                "have hq_one : q = 1",
                "trans x1",
                "symm",
                "exact hxq",
                "exact hright_witness_right_right_right",
                "rewrite hq_one",
                "specialize coprime_one_right p",
                "exact coprime_one_right",
                "cases hright_witness_right",
                "cases hleft_witness_right_right",
                "cases hright_witness_right_left",
                "have hp_one : p = 1",
                "trans x",
                "symm",
                "exact hxp",
                "exact hleft_witness_right_right_right",
                "rewrite hp_one",
                "specialize coprime_one_left q",
                "exact coprime_one_left",
                "cases hleft_witness_right_right",
                "cases hright_witness_right_right",
                "have hp_one : p = 1",
                "trans x",
                "symm",
                "exact hxp",
                "exact hleft_witness_right_right_right",
                "rewrite hp_one",
                "specialize coprime_one_left q",
                "exact coprime_one_left",
            ),
            "Distinct positions in an interval decode coprime selector factors.",
        ),
        spec(
            PRIMORIAL_INTERVAL_DIVIDES_CHOOSE_BETWEEN,
            "forall a l n k j c z. k + j = n -> "
            f"({interval_choose}) -> ({interval_source}) -> "
            f"({interval_bounds}) -> ({interval_result})",
            (
                "beta_at_unique",
                "one_multiple",
                CHOOSE_PRIME_DIVIDES_BETWEEN,
                PRIMORIAL_INTERVAL_PAIRWISE_COPRIME,
                BETA_PAIRWISE_COPRIME_PRODUCT_DIVIDES_COMMON_MULTIPLE,
            ),
            (
                "intro a",
                "intro l",
                "intro n",
                "intro k",
                "intro j",
                "intro c",
                "intro z",
                "intro hsum",
                "intro hchoose",
                "intro hinterval",
                "intro hbounds",
                "cases hinterval",
                "cases hinterval_witness",
                "cases hinterval_witness_witness",
                f"have hpairwise : {interval_pairwise}",
                "specialize primorial_interval_pairwise_coprime a",
                "specialize primorial_interval_pairwise_coprime x",
                "specialize primorial_interval_pairwise_coprime x1",
                "specialize primorial_interval_pairwise_coprime l",
                "apply primorial_interval_pairwise_coprime",
                "exact hinterval_witness_witness_left",
                f"have hpointwise : {interval_pointwise}",
                "intro i",
                "intro p",
                "intro hi",
                "intro hp",
                f"have hentry : exists x2. ({interval_local_entry}) /\\ "
                f"({interval_local_choice})",
                "apply hinterval_witness_witness_left",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "have hxp : x2 = p",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique p",
                "apply beta_at_unique",
                "exact hentry_witness_left",
                "exact hp",
                "cases hentry_witness_right",
                "cases hentry_witness_right_left",
                "have hcandidate : p = S (a + i)",
                "trans x2",
                "symm",
                "exact hxp",
                "exact hentry_witness_right_left_right",
                "have hlocal_bounds : "
                f"({interval_local_left_bound}) /\\ "
                f"(({interval_local_right_bound}) /\\ "
                f"({interval_local_upper_bound}))",
                "specialize hbounds i",
                "apply hbounds",
                "exact hi",
                "cases hlocal_bounds",
                "cases hlocal_bounds_right",
                "specialize choose_prime_divides_between n",
                "specialize choose_prime_divides_between k",
                "specialize choose_prime_divides_between j",
                "specialize choose_prime_divides_between p",
                "specialize choose_prime_divides_between c",
                "apply choose_prime_divides_between",
                "exact hsum",
                "rewrite hcandidate",
                "rewrite hcandidate",
                "exact hentry_witness_right_left_left",
                "rewrite hcandidate",
                "exact hlocal_bounds_left",
                "rewrite hcandidate",
                "exact hlocal_bounds_right_left",
                "rewrite hcandidate",
                "exact hlocal_bounds_right_right",
                "exact hchoose",
                "cases hentry_witness_right_right",
                "have hp_one : p = 1",
                "trans x2",
                "symm",
                "exact hxp",
                "exact hentry_witness_right_right_right",
                "rewrite hp_one",
                "specialize one_multiple c",
                "exact one_multiple",
                "specialize beta_pairwise_coprime_product_divides_common_multiple x",
                "specialize beta_pairwise_coprime_product_divides_common_multiple x1",
                "specialize beta_pairwise_coprime_product_divides_common_multiple l",
                "specialize beta_pairwise_coprime_product_divides_common_multiple z",
                "specialize beta_pairwise_coprime_product_divides_common_multiple c",
                "apply beta_pairwise_coprime_product_divides_common_multiple",
                "exact hpairwise",
                "exact hpointwise",
                "exact hinterval_witness_witness_right",
            ),
            "A selector interval between both denominator indices divides Choose.",
        ),
        spec(
            PRIMORIAL_EVEN_INTERVAL_DIVIDES_CENTRAL,
            "forall n z c. "
            f"({even_interval}) -> ({even_central}) -> ({even_divides})",
            (
                "add_comm",
                "add_le_add_left",
                PRIMORIAL_INTERVAL_DIVIDES_CHOOSE_BETWEEN,
            ),
            (
                "intro n",
                "intro z",
                "intro c",
                "intro hinterval",
                "intro hcentral",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between (n + n)",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between c",
                "specialize primorial_interval_divides_choose_between z",
                "apply primorial_interval_divides_choose_between",
                "refl",
                "exact hcentral",
                "exact hinterval",
                "intro i",
                "intro hi",
                "have hlower : exists g. g + S n = S (n + i)",
                "exists i",
                "trans S (i + n)",
                "apply PA4",
                "congr",
                "apply add_comm",
                "have hupper : exists g. g + S (n + i) = n + n",
                "have hraw : exists g. g + (n + S i) = n + n",
                "specialize add_le_add_left (S i)",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hi",
                "have hadd : n + S i = S (n + i)",
                "apply PA4",
                "rewrite hadd at hraw",
                "exact hraw",
                "split",
                "exact hlower",
                "split",
                "exact hlower",
                "exact hupper",
            ),
            "The selector interval (n,2n] divides the central coefficient.",
        ),
        spec(
            PRIMORIAL_ODD_INTERVAL_DIVIDES_MIDDLE,
            "forall n z c. "
            f"({odd_interval}) -> ({odd_middle}) -> ({odd_divides})",
            (
                "add_comm",
                "add_succ_left",
                "add_le_add_left",
                "le_refl",
                "lt_trans",
                PRIMORIAL_INTERVAL_DIVIDES_CHOOSE_BETWEEN,
            ),
            (
                "intro n",
                "intro z",
                "intro c",
                "intro hinterval",
                "intro hmiddle",
                "specialize primorial_interval_divides_choose_between (S n)",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between (S (n + n))",
                "specialize primorial_interval_divides_choose_between n",
                "specialize primorial_interval_divides_choose_between (S n)",
                "specialize primorial_interval_divides_choose_between c",
                "specialize primorial_interval_divides_choose_between z",
                "apply primorial_interval_divides_choose_between",
                "apply PA4",
                "exact hmiddle",
                "exact hinterval",
                "intro i",
                "intro hi",
                "have hright : exists g. g + S (S n) = S (S n + i)",
                "exists i",
                "trans S (i + S n)",
                "apply PA4",
                "congr",
                "apply add_comm",
                "have hleft : exists g. g + S n = S (S n + i)",
                "specialize lt_trans n",
                "specialize lt_trans (S n)",
                "specialize lt_trans (S (S n + i))",
                "apply lt_trans",
                "specialize le_refl (S n)",
                "exact le_refl",
                "exact hright",
                "have hupper : exists g. g + S (S n + i) = S (n + n)",
                "have hraw : exists g. g + (S n + S i) = S n + n",
                "specialize add_le_add_left (S i)",
                "specialize add_le_add_left n",
                "specialize add_le_add_left (S n)",
                "apply add_le_add_left",
                "exact hi",
                "have hadd_left : S n + S i = S (S n + i)",
                "apply PA4",
                "rewrite hadd_left at hraw",
                "have hadd_right : S n + n = S (n + n)",
                "specialize add_succ_left n",
                "specialize add_succ_left n",
                "apply add_succ_left",
                "rewrite hadd_right at hraw",
                "exact hraw",
                "split",
                "exact hleft",
                "split",
                "exact hright",
                "exact hupper",
            ),
            "The selector interval (n+1,2n+1] divides the odd middle coefficient.",
        ),
        spec(
            PRIMORIAL_EVEN_INTERVAL_LE_CENTRAL,
            "forall n z c. "
            f"({even_interval}) -> ({even_central}) -> ({even_le})",
            (
                PRIMORIAL_EVEN_INTERVAL_DIVIDES_CENTRAL,
                "central_binom_positive",
                "divisor_le_nonzero",
            ),
            (
                "intro n",
                "intro z",
                "intro c",
                "intro hinterval",
                "intro hcentral",
                "have hdivides : exists q. c = z * q",
                "apply primorial_even_interval_divides_central",
                "exact hinterval",
                "exact hcentral",
                "have hpositive : exists r. c = S r",
                "specialize central_binom_positive n",
                "specialize central_binom_positive c",
                "apply central_binom_positive",
                "exact hcentral",
                "specialize divisor_le_nonzero z",
                "specialize divisor_le_nonzero c",
                "apply divisor_le_nonzero",
                "intro hc",
                "rewrite hc at hpositive",
                "cases hpositive",
                "apply PA1",
                "symm",
                "exact hpositive_witness",
                "exact hdivides",
            ),
            "The even Primorial interval is bounded by the central coefficient.",
        ),
        spec(
            PRIMORIAL_ODD_INTERVAL_LE_MIDDLE,
            "forall n z c. "
            f"({odd_interval}) -> ({odd_middle}) -> ({odd_le})",
            (
                PRIMORIAL_ODD_INTERVAL_DIVIDES_MIDDLE,
                "choose_positive",
                "add_succ_left",
                "divisor_le_nonzero",
            ),
            (
                "intro n",
                "intro z",
                "intro c",
                "intro hinterval",
                "intro hmiddle",
                "have hdivides : exists q. c = z * q",
                "apply primorial_odd_interval_divides_middle",
                "exact hinterval",
                "exact hmiddle",
                "have hpositive : exists r. c = S r",
                "specialize choose_positive (S (n + n))",
                "specialize choose_positive n",
                "specialize choose_positive c",
                "apply choose_positive",
                "exists S n",
                "specialize add_succ_left n",
                "specialize add_succ_left n",
                "exact add_succ_left",
                "exact hmiddle",
                "specialize divisor_le_nonzero z",
                "specialize divisor_le_nonzero c",
                "apply divisor_le_nonzero",
                "intro hc",
                "rewrite hc at hpositive",
                "cases hpositive",
                "apply PA1",
                "symm",
                "exact hpositive_witness",
                "exact hdivides",
            ),
            "The odd Primorial interval is bounded by the odd middle coefficient.",
        ),
    )


__all__ = ["make_bertrand_primorial_choose_interval_candidate_theorems"]
