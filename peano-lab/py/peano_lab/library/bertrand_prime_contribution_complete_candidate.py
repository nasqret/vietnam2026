"""Complete prime-contribution reconstruction for Bertrand B5.

The preceding contribution foundation constructs a finite product of complete
prime-power contributions and proves that it divides its source number.  This
tranche proves the converse direction once the prefix contains every prime
divisor of the source.  The key constructive step takes a hypothetical prime
divisor of the remaining cofactor and raises its already selected valuation
power, contradicting valuation maximality.

The final two rows specialize the generic reconstruction to central binomial
values and expose the reviewed small, middle, and neutral contribution ranges
pointwise on the beta prefix.  Every readable relation is expanded into the
unchanged first-order Peano language before parsing.  Importing this module
grants no theorem authority and changes no library edition.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_prime_support_candidate import (
    _no_bertrand_closed_term,
)
from .bertrand_prime_contribution_candidate import (
    _divides_rendered,
    _le_rendered,
    _power_divides_rendered,
    _power_rendered,
    _power_valuation_rendered,
    _prime_contribution_choice_term,
    _prime_contribution_prefix_term,
    _prime_contribution_product_term,
)
from .bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
)


PRIME_CONTRIBUTION_SELECTED_ENTRY = (
    "prime_contribution_selected_entry"
)
PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES = (
    "prime_contribution_selected_successor_divides"
)
PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION = (
    "prime_contribution_cofactor_prime_contradiction"
)
PRIME_CONTRIBUTION_COFACTOR_EQ_ONE = (
    "prime_contribution_cofactor_eq_one"
)
PRIME_CONTRIBUTION_REVERSE_DIVIDES = (
    "prime_contribution_reverse_divides"
)
PRIME_CONTRIBUTION_PRODUCT_EQ = "prime_contribution_product_eq"
PRIME_CONTRIBUTION_COMPLETE_EXISTS = (
    "prime_contribution_complete_exists"
)
CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS = (
    "central_binom_prime_contribution_product_exists"
)
NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES = (
    "no_bertrand_central_contribution_choice_ranges"
)
NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES = (
    "no_bertrand_central_contribution_prefix_ranges"
)


def _prime_support_rendered(
    number: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand the assertion that every prime divisor lies in the prefix."""

    (prime,) = _binders(tag, avoid, ("support_prime",))
    local = avoid + (prime,)
    primality = _prime_term(
        prime,
        tag=f"{tag}_prime",
        avoid=local,
    )
    divides = _divides_rendered(
        prime,
        number,
        tag=f"{tag}_divides",
        avoid=local,
    )
    bound = _le_rendered(
        prime,
        length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    return (
        f"forall {prime}. ({primality}) -> ({divides}) -> ({bound})"
    )


def make_bertrand_prime_contribution_complete_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered contribution reconstruction rows."""

    selected_variables = ("n", "m", "z", "i")
    selected_prime = _prime_term(
        "S i",
        tag="bpcse_prime",
        avoid=selected_variables,
    )
    selected_bound = _le_rendered(
        "S i",
        "m",
        tag="bpcse_bound",
        avoid=selected_variables,
    )
    selected_source = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcse_source",
        variables=selected_variables,
    )
    selected_exponent, selected_value = _binders(
        "bpcse_result",
        selected_variables,
        ("selected_exponent", "selected_value"),
    )
    selected_local = selected_variables + (
        selected_exponent,
        selected_value,
    )
    selected_valuation = _power_valuation_rendered(
        "S i",
        "n",
        selected_exponent,
        tag="bpcse_result_valuation",
        avoid=selected_local,
    )
    selected_power = _power_rendered(
        "S i",
        selected_exponent,
        selected_value,
        tag="bpcse_result_power",
        avoid=selected_local,
    )
    selected_divides = _divides_rendered(
        selected_value,
        "z",
        tag="bpcse_result_divides",
        avoid=selected_local,
    )
    selected_result = (
        f"exists {selected_exponent} {selected_value}. "
        f"(({selected_valuation}) /\\ "
        f"(({selected_power}) /\\ ({selected_divides})))"
    )
    selected_entry_local = selected_variables + ("x", "x1", "a")
    selected_entry_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "a",
        tag="bpcse_entry_decoded",
        avoid=selected_entry_local,
    )
    selected_entry_choice = _prime_contribution_choice_term(
        "n",
        "i",
        "a",
        tag="bpcse_entry_choice",
        variables=selected_entry_local,
    )
    selected_entry = (
        f"exists a. ({selected_entry_decoded}) /\\ "
        f"({selected_entry_choice})"
    )
    selected_factor = _divides_rendered(
        "x2",
        "z",
        tag="bpcse_factor",
        avoid=selected_variables + ("x", "x1", "x2"),
    )

    successor_variables = ("p", "e", "a", "z", "q", "n")
    successor_power = _power_rendered(
        "p",
        "e",
        "a",
        tag="bpcssd_power",
        avoid=successor_variables,
    )
    successor_factor = _divides_rendered(
        "a",
        "z",
        tag="bpcssd_factor",
        avoid=successor_variables,
    )
    successor_prime_factor = _divides_rendered(
        "p",
        "q",
        tag="bpcssd_prime_factor",
        avoid=successor_variables,
    )
    successor_result = _power_divides_rendered(
        "p",
        "S e",
        "n",
        tag="bpcssd_result",
        avoid=successor_variables,
    )
    successor_cofactor = _divides_rendered(
        "p",
        "x * q",
        tag="bpcssd_cofactor",
        avoid=successor_variables + ("x",),
    )

    contradiction_variables = ("n", "m", "z", "q", "p")
    contradiction_support = _prime_support_rendered(
        "n",
        "m",
        tag="bpccpc_support",
        avoid=contradiction_variables,
    )
    contradiction_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpccpc_product",
        variables=contradiction_variables,
    )
    contradiction_prime = _prime_term(
        "p",
        tag="bpccpc_prime",
        avoid=contradiction_variables,
    )
    contradiction_divides = _divides_rendered(
        "p",
        "q",
        tag="bpccpc_divides",
        avoid=contradiction_variables,
    )
    contradiction_source_divides = _divides_rendered(
        "p",
        "n",
        tag="bpccpc_source_divides",
        avoid=contradiction_variables,
    )
    contradiction_bound = _le_rendered(
        "p",
        "m",
        tag="bpccpc_bound",
        avoid=contradiction_variables,
    )
    contradiction_scaled = _divides_rendered(
        "p",
        "z * q",
        tag="bpccpc_scaled",
        avoid=contradiction_variables,
    )
    contradiction_selected_local = contradiction_variables + (
        "x",
        "e",
        "a",
    )
    contradiction_selected_valuation = _power_valuation_rendered(
        "S (S x)",
        "n",
        "e",
        tag="bpccpc_selected_valuation",
        avoid=contradiction_selected_local,
    )
    contradiction_selected_power = _power_rendered(
        "S (S x)",
        "e",
        "a",
        tag="bpccpc_selected_power",
        avoid=contradiction_selected_local,
    )
    contradiction_selected_divides = _divides_rendered(
        "a",
        "z",
        tag="bpccpc_selected_divides",
        avoid=contradiction_selected_local,
    )
    contradiction_selected = (
        "exists e a. "
        f"({contradiction_selected_valuation}) /\\ "
        f"(({contradiction_selected_power}) /\\ "
        f"({contradiction_selected_divides}))"
    )
    contradiction_successor = _power_divides_rendered(
        "S (S x)",
        "S x1",
        "n",
        tag="bpccpc_successor",
        avoid=contradiction_variables + ("x", "x1", "x2"),
    )

    cofactor_variables = ("n", "m", "z", "q")
    cofactor_support = _prime_support_rendered(
        "n",
        "m",
        tag="bpcceo_support",
        avoid=cofactor_variables,
    )
    cofactor_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcceo_product",
        variables=cofactor_variables,
    )
    cofactor_prime = _prime_term(
        "p",
        tag="bpcceo_prime",
        avoid=cofactor_variables + ("p",),
    )
    cofactor_divides = _divides_rendered(
        "p",
        "q",
        tag="bpcceo_divides",
        avoid=cofactor_variables + ("p",),
    )
    cofactor_prime_witness = (
        f"exists p. ({cofactor_prime}) /\\ ({cofactor_divides})"
    )

    reverse_variables = ("n", "m", "z")
    reverse_support = _prime_support_rendered(
        "n",
        "m",
        tag="bpcrd_support",
        avoid=reverse_variables,
    )
    reverse_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcrd_product",
        variables=reverse_variables,
    )
    reverse_result = _divides_rendered(
        "n",
        "z",
        tag="bpcrd_result",
        avoid=reverse_variables,
    )
    reverse_forward = _divides_rendered(
        "z",
        "n",
        tag="bpcrd_forward",
        avoid=reverse_variables,
    )

    equality_support = _prime_support_rendered(
        "n",
        "m",
        tag="bpcpeq_support",
        avoid=reverse_variables,
    )
    equality_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcpeq_product",
        variables=reverse_variables,
    )
    equality_reverse = _divides_rendered(
        "n",
        "z",
        tag="bpcpeq_reverse",
        avoid=reverse_variables,
    )
    equality_forward = _divides_rendered(
        "z",
        "n",
        tag="bpcpeq_forward",
        avoid=reverse_variables,
    )

    complete_variables = ("n", "m")
    complete_support = _prime_support_rendered(
        "n",
        "m",
        tag="bpcce_support",
        avoid=complete_variables,
    )
    complete_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcce_product",
        variables=complete_variables + ("z",),
    )

    central_variables = ("n", "C")
    central_source = _central_binom_relation_term(
        "n",
        "C",
        tag="bcbpcpe_central",
        variables=central_variables,
    )
    central_product = _prime_contribution_product_term(
        "C",
        "n + n",
        "z",
        tag="bcbpcpe_product",
        variables=central_variables + ("z",),
    )
    central_support = _prime_support_rendered(
        "C",
        "n + n",
        tag="bcbpcpe_support",
        avoid=central_variables,
    )

    range_variables = ("n", "s", "q", "r", "C", "i", "a")
    range_exclusion = _no_bertrand_closed_term(
        "n",
        tag="bnbccr_exclusion",
        variables=range_variables,
    )
    range_positive = _lt_term(
        "2",
        "n",
        tag="bnbccr_positive",
        avoid=range_variables,
    )
    range_floor = floor_sqrt_relation(
        "n + n",
        "s",
        tag="bnbccr_floor",
    )
    range_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bnbccr_division",
        variables=range_variables,
    )
    range_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bnbccr_central",
        variables=range_variables,
    )
    range_choice = _prime_contribution_choice_term(
        "C",
        "i",
        "a",
        tag="bnbccr_choice",
        variables=range_variables,
    )
    range_small_prime = _le_rendered(
        "S i",
        "s",
        tag="bnbccr_small_prime",
        avoid=range_variables,
    )
    range_small_value = _le_rendered(
        "a",
        "n + n",
        tag="bnbccr_small_value",
        avoid=range_variables,
    )
    range_above = _lt_term(
        "s",
        "S i",
        tag="bnbccr_above",
        avoid=range_variables,
    )
    range_middle = _le_rendered(
        "S i",
        "q",
        tag="bnbccr_middle",
        avoid=range_variables,
    )
    range_result = (
        f"((({range_small_prime}) /\\ ({range_small_value})) \\/ "
        f"((({range_above}) /\\ ({range_middle})) /\\ a = S i)) \\/ "
        "a = 1"
    )

    prefix_variables = ("n", "s", "q", "r", "C", "b", "c")
    prefix_exclusion = _no_bertrand_closed_term(
        "n",
        tag="bnbcpr_exclusion",
        variables=prefix_variables,
    )
    prefix_positive = _lt_term(
        "2",
        "n",
        tag="bnbcpr_positive",
        avoid=prefix_variables,
    )
    prefix_floor = floor_sqrt_relation(
        "n + n",
        "s",
        tag="bnbcpr_floor",
    )
    prefix_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bnbcpr_division",
        variables=prefix_variables,
    )
    prefix_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bnbcpr_central",
        variables=prefix_variables,
    )
    prefix_source = _prime_contribution_prefix_term(
        "C",
        "b",
        "c",
        "n + n",
        tag="bnbcpr_source",
        variables=prefix_variables,
    )
    prefix_local = prefix_variables + ("i", "a")
    prefix_bound = _lt_term(
        "i",
        "n + n",
        tag="bnbcpr_bound",
        avoid=prefix_local,
    )
    prefix_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="bnbcpr_decoded",
        avoid=prefix_local,
    )
    prefix_small_prime = _le_rendered(
        "S i",
        "s",
        tag="bnbcpr_small_prime",
        avoid=prefix_local,
    )
    prefix_small_value = _le_rendered(
        "a",
        "n + n",
        tag="bnbcpr_small_value",
        avoid=prefix_local,
    )
    prefix_above = _lt_term(
        "s",
        "S i",
        tag="bnbcpr_above",
        avoid=prefix_local,
    )
    prefix_middle = _le_rendered(
        "S i",
        "q",
        tag="bnbcpr_middle",
        avoid=prefix_local,
    )
    prefix_result = (
        f"((({prefix_small_prime}) /\\ ({prefix_small_value})) \\/ "
        f"((({prefix_above}) /\\ ({prefix_middle})) /\\ a = S i)) "
        "\\/ a = 1"
    )
    prefix_entry_local = prefix_local + ("x",)
    prefix_entry_decoded = _beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bnbcpr_entry_decoded",
        avoid=prefix_entry_local,
    )
    prefix_entry_choice = _prime_contribution_choice_term(
        "C",
        "i",
        "x",
        tag="bnbcpr_entry_choice",
        variables=prefix_entry_local,
    )
    prefix_entry = (
        f"exists x. ({prefix_entry_decoded}) /\\ "
        f"({prefix_entry_choice})"
    )
    prefix_entry_range_variables = range_variables
    prefix_entry_range_small_value = _le_rendered(
        "x",
        "n + n",
        tag="bnbcpr_entry_small_value",
        avoid=prefix_entry_range_variables + ("x",),
    )
    prefix_entry_range = (
        f"((({range_small_prime}) /\\ "
        f"({prefix_entry_range_small_value})) \\/ "
        f"((({range_above}) /\\ ({range_middle})) /\\ x = S i)) "
        "\\/ x = 1"
    )

    return (
        spec(
            PRIME_CONTRIBUTION_SELECTED_ENTRY,
            "forall n m z i. "
            f"({selected_prime}) -> ({selected_bound}) -> "
            f"({selected_source}) -> ({selected_result})",
            ("beta_factor_divides_product",),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro i",
                "intro hp",
                "intro hbound",
                "intro hproduct",
                "cases hproduct",
                "cases hproduct_witness",
                "cases hproduct_witness_witness",
                f"have hentry : {selected_entry}",
                "apply hproduct_witness_witness_left",
                "exact hbound",
                "cases hentry",
                "cases hentry_witness",
                f"have hfactor : {selected_factor}",
                "specialize beta_factor_divides_product x",
                "specialize beta_factor_divides_product x1",
                "specialize beta_factor_divides_product m",
                "specialize beta_factor_divides_product z",
                "specialize beta_factor_divides_product i",
                "specialize beta_factor_divides_product x2",
                "apply beta_factor_divides_product",
                "exact hbound",
                "exact hentry_witness_left",
                "exact hproduct_witness_witness_right",
                "cases hentry_witness_right",
                "cases hentry_witness_right_left",
                "cases hentry_witness_right_left_right",
                "cases hentry_witness_right_left_right_witness",
                "exists x3",
                "exists x2",
                "split",
                "exact hentry_witness_right_left_right_witness_left",
                "split",
                "exact hentry_witness_right_left_right_witness_right",
                "exact hfactor",
                "cases hentry_witness_right_right",
                "exfalso",
                "apply hentry_witness_right_right_left",
                "exact hp",
            ),
            "A selected prime position exposes its valuation power in the product.",
        ),
        spec(
            PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES,
            "forall p e a z q n. "
            f"({successor_power}) -> ({successor_factor}) -> "
            f"({successor_prime_factor}) -> n = z * q -> "
            f"({successor_result})",
            (
                "mul_assoc",
                "multiple_mul_left",
                "power_divides_successor_of_cofactor",
            ),
            (
                "intro p",
                "intro e",
                "intro a",
                "intro z",
                "intro q",
                "intro n",
                "intro hpower",
                "intro hfactor",
                "intro hprime",
                "intro htotal",
                "cases hfactor",
                f"have hcofactor : {successor_cofactor}",
                "specialize multiple_mul_left p",
                "specialize multiple_mul_left q",
                "specialize multiple_mul_left x",
                "apply multiple_mul_left",
                "exact hprime",
                "have haligned : n = a * (x * q)",
                "trans z * q",
                "exact htotal",
                "rewrite hfactor_witness",
                "apply mul_assoc",
                "specialize power_divides_successor_of_cofactor p",
                "specialize power_divides_successor_of_cofactor e",
                "specialize power_divides_successor_of_cofactor n",
                "specialize power_divides_successor_of_cofactor a",
                "specialize power_divides_successor_of_cofactor (x * q)",
                "apply power_divides_successor_of_cofactor",
                "exact hpower",
                "exact haligned",
                "exact hcofactor",
            ),
            "A prime in the remaining cofactor raises a selected power.",
        ),
        spec(
            PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION,
            "forall n m z q p. ~(n = 0) -> "
            f"({contradiction_support}) -> ({contradiction_product}) -> "
            f"n = z * q -> ({contradiction_prime}) -> "
            f"({contradiction_divides}) -> false",
            (
                "prime_is_succ_succ",
                "multiple_mul_left",
                PRIME_CONTRIBUTION_SELECTED_ENTRY,
                PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES,
                "power_valuation_successor_not_divides",
            ),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro q",
                "intro p",
                "intro hn",
                "intro hsupport",
                "intro hproduct",
                "intro hfactor",
                "intro hp",
                "intro hprime",
                f"have hscaled : {contradiction_scaled}",
                "specialize multiple_mul_left p",
                "specialize multiple_mul_left q",
                "specialize multiple_mul_left z",
                "apply multiple_mul_left",
                "exact hprime",
                f"have hsource : {contradiction_source_divides}",
                "cases hscaled",
                "exists x",
                "trans z * q",
                "exact hfactor",
                "exact hscaled_witness",
                f"have hbound : {contradiction_bound}",
                "specialize hsupport p",
                "apply hsupport",
                "exact hp",
                "exact hsource",
                "have hshape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hshape",
                "rewrite hshape_witness at hp",
                "rewrite hshape_witness at hp",
                "rewrite hshape_witness at hbound",
                "rewrite hshape_witness at hprime",
                f"have hselected : {contradiction_selected}",
                "specialize prime_contribution_selected_entry n",
                "specialize prime_contribution_selected_entry m",
                "specialize prime_contribution_selected_entry z",
                "specialize prime_contribution_selected_entry (S x)",
                "apply prime_contribution_selected_entry",
                "exact hp",
                "exact hbound",
                "exact hproduct",
                "cases hselected",
                "cases hselected_witness",
                "cases hselected_witness_witness",
                "cases hselected_witness_witness_right",
                f"have hsuccessor : {contradiction_successor}",
                "specialize prime_contribution_selected_successor_divides "
                "(S (S x))",
                "specialize prime_contribution_selected_successor_divides x1",
                "specialize prime_contribution_selected_successor_divides x2",
                "specialize prime_contribution_selected_successor_divides z",
                "specialize prime_contribution_selected_successor_divides q",
                "specialize prime_contribution_selected_successor_divides n",
                "apply prime_contribution_selected_successor_divides",
                "exact hselected_witness_witness_right_left",
                "exact hselected_witness_witness_right_right",
                "exact hprime",
                "exact hfactor",
                "specialize power_valuation_successor_not_divides "
                "(S (S x))",
                "specialize power_valuation_successor_not_divides n",
                "specialize power_valuation_successor_not_divides x1",
                "apply power_valuation_successor_not_divides",
                "exact hp",
                "exact hn",
                "exact hselected_witness_witness_left",
                "exact hsuccessor",
            ),
            "A prime divisor of the remaining cofactor contradicts maximality.",
        ),
        spec(
            PRIME_CONTRIBUTION_COFACTOR_EQ_ONE,
            "forall n m z q. ~(n = 0) -> "
            f"({cofactor_support}) -> ({cofactor_product}) -> "
            "n = z * q -> q = 1",
            (
                "eq_decidable",
                "prime_divisor_exists",
                PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION,
            ),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro q",
                "intro hn",
                "intro hsupport",
                "intro hproduct",
                "intro hfactor",
                "have hcases : q = 1 \\/ ~(q = 1)",
                "specialize eq_decidable q",
                "specialize eq_decidable 1",
                "exact eq_decidable",
                "cases hcases",
                "exact hcases_left",
                "have hq0 : ~(q = 0)",
                "intro hqzero",
                "apply hn",
                "trans z * q",
                "exact hfactor",
                "rewrite hqzero",
                "apply PA5",
                f"have hprime : {cofactor_prime_witness}",
                "specialize prime_divisor_exists q",
                "apply prime_divisor_exists",
                "exact hq0",
                "exact hcases_right",
                "cases hprime",
                "cases hprime_witness",
                "exfalso",
                "specialize prime_contribution_cofactor_prime_contradiction n",
                "specialize prime_contribution_cofactor_prime_contradiction m",
                "specialize prime_contribution_cofactor_prime_contradiction z",
                "specialize prime_contribution_cofactor_prime_contradiction q",
                "specialize prime_contribution_cofactor_prime_contradiction x",
                "apply prime_contribution_cofactor_prime_contradiction",
                "exact hn",
                "exact hsupport",
                "exact hproduct",
                "exact hfactor",
                "exact hprime_witness_left",
                "exact hprime_witness_right",
            ),
            "A supported contribution cofactor is the multiplicative unit.",
        ),
        spec(
            PRIME_CONTRIBUTION_REVERSE_DIVIDES,
            "forall n m z. ~(n = 0) -> "
            f"({reverse_support}) -> ({reverse_product}) -> "
            f"({reverse_result})",
            (
                "mul_one",
                "prime_contribution_product_divides",
                PRIME_CONTRIBUTION_COFACTOR_EQ_ONE,
            ),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro hn",
                "intro hsupport",
                "intro hproduct",
                f"have hforward : {reverse_forward}",
                "apply prime_contribution_product_divides",
                "exact hproduct",
                "cases hforward",
                "have hunit : x = 1",
                "specialize prime_contribution_cofactor_eq_one n",
                "specialize prime_contribution_cofactor_eq_one m",
                "specialize prime_contribution_cofactor_eq_one z",
                "specialize prime_contribution_cofactor_eq_one x",
                "apply prime_contribution_cofactor_eq_one",
                "exact hn",
                "exact hsupport",
                "exact hproduct",
                "exact hforward_witness",
                "have heq : n = z",
                "trans z * x",
                "exact hforward_witness",
                "rewrite hunit",
                "apply mul_one",
                "exists 1",
                "trans n",
                "symm",
                "exact heq",
                "symm",
                "apply mul_one",
            ),
            "A supported complete contribution product is a multiple of its source.",
        ),
        spec(
            PRIME_CONTRIBUTION_PRODUCT_EQ,
            "forall n m z. ~(n = 0) -> "
            f"({equality_support}) -> ({equality_product}) -> n = z",
            (
                "multiple_antisymm",
                "prime_contribution_product_divides",
                PRIME_CONTRIBUTION_REVERSE_DIVIDES,
            ),
            (
                "intro n",
                "intro m",
                "intro z",
                "intro hn",
                "intro hsupport",
                "intro hproduct",
                f"have hreverse : {equality_reverse}",
                "apply prime_contribution_reverse_divides",
                "exact hn",
                "exact hsupport",
                "exact hproduct",
                f"have hforward : {equality_forward}",
                "apply prime_contribution_product_divides",
                "exact hproduct",
                "specialize multiple_antisymm n",
                "specialize multiple_antisymm z",
                "apply multiple_antisymm",
                "exact hreverse",
                "exact hforward",
            ),
            "Every supported complete contribution product equals its source.",
        ),
        spec(
            PRIME_CONTRIBUTION_COMPLETE_EXISTS,
            "forall n m. ~(n = 0) -> "
            f"({complete_support}) -> exists z. "
            f"({complete_product}) /\\ n = z",
            (
                "prime_contribution_product_exists",
                PRIME_CONTRIBUTION_PRODUCT_EQ,
            ),
            (
                "intro n",
                "intro m",
                "intro hn",
                "intro hsupport",
                f"have hproduct : exists z. ({complete_product})",
                "specialize prime_contribution_product_exists n",
                "specialize prime_contribution_product_exists m",
                "exact prime_contribution_product_exists",
                "cases hproduct",
                "have heq : n = x",
                "specialize prime_contribution_product_eq n",
                "specialize prime_contribution_product_eq m",
                "specialize prime_contribution_product_eq x",
                "apply prime_contribution_product_eq",
                "exact hn",
                "exact hsupport",
                "exact hproduct_witness",
                "exists x",
                "split",
                "exact hproduct_witness",
                "exact heq",
            ),
            "Every nonzero source has an exact supported contribution product.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS,
            "forall n C. "
            f"({central_source}) -> exists z. ({central_product}) /\\ C = z",
            (
                "central_binom_positive",
                "central_binom_prime_divisor_le_double",
                PRIME_CONTRIBUTION_COMPLETE_EXISTS,
            ),
            (
                "intro n",
                "intro C",
                "intro hcentral",
                "have hpositive : exists r. C = S r",
                "specialize central_binom_positive n",
                "specialize central_binom_positive C",
                "apply central_binom_positive",
                "exact hcentral",
                "cases hpositive",
                "have hnonzero : ~(C = 0)",
                "intro hzero",
                "apply PA1",
                "trans C",
                "symm",
                "exact hpositive_witness",
                "exact hzero",
                f"have hsupport : {central_support}",
                "intro p",
                "intro hp",
                "intro hdivides",
                "specialize central_binom_prime_divisor_le_double n",
                "specialize central_binom_prime_divisor_le_double C",
                "specialize central_binom_prime_divisor_le_double p",
                "apply central_binom_prime_divisor_le_double",
                "exact hp",
                "exact hcentral",
                "exact hdivides",
                "specialize prime_contribution_complete_exists C",
                "specialize prime_contribution_complete_exists (n + n)",
                "apply prime_contribution_complete_exists",
                "exact hnonzero",
                "exact hsupport",
            ),
            "A central coefficient is exactly its complete contribution product.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES,
            "forall n s q r C i a. "
            f"({range_exclusion}) -> ({range_positive}) -> "
            f"({range_floor}) -> ({range_division}) -> "
            f"({range_central}) -> ({range_choice}) -> ({range_result})",
            ("no_bertrand_central_prime_contribution_ranges",),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro i",
                "intro a",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hchoice",
                "cases hchoice",
                "cases hchoice_left",
                "cases hchoice_left_right",
                "cases hchoice_left_right_witness",
                "specialize no_bertrand_central_prime_contribution_ranges n",
                "specialize no_bertrand_central_prime_contribution_ranges s",
                "specialize no_bertrand_central_prime_contribution_ranges q",
                "specialize no_bertrand_central_prime_contribution_ranges r",
                "specialize no_bertrand_central_prime_contribution_ranges C",
                "specialize no_bertrand_central_prime_contribution_ranges "
                "(S i)",
                "specialize no_bertrand_central_prime_contribution_ranges x",
                "specialize no_bertrand_central_prime_contribution_ranges a",
                "apply no_bertrand_central_prime_contribution_ranges",
                "exact hexclusion",
                "exact hchoice_left_left",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hchoice_left_right_witness_left",
                "exact hchoice_left_right_witness_right",
                "cases hchoice_right",
                "right",
                "exact hchoice_right_right",
            ),
            "Each central contribution lies in a reviewed factor range.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES,
            "forall n s q r C b c. "
            f"({prefix_exclusion}) -> ({prefix_positive}) -> "
            f"({prefix_floor}) -> ({prefix_division}) -> "
            f"({prefix_central}) -> ({prefix_source}) -> "
            f"forall i a. ({prefix_bound}) -> ({prefix_decoded}) -> "
            f"({prefix_result})",
            (
                "beta_at_unique",
                NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro b",
                "intro c",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hprefix",
                "intro i",
                "intro a",
                "intro hbound",
                "intro hdecoded",
                f"have hentry : {prefix_entry}",
                "apply hprefix",
                "exact hbound",
                "cases hentry",
                "cases hentry_witness",
                "have heq : a = x",
                "apply beta_at_unique",
                "exact hdecoded",
                "exact hentry_witness_left",
                f"have hrange : {prefix_entry_range}",
                "specialize no_bertrand_central_contribution_choice_ranges n",
                "specialize no_bertrand_central_contribution_choice_ranges s",
                "specialize no_bertrand_central_contribution_choice_ranges q",
                "specialize no_bertrand_central_contribution_choice_ranges r",
                "specialize no_bertrand_central_contribution_choice_ranges C",
                "specialize no_bertrand_central_contribution_choice_ranges i",
                "specialize no_bertrand_central_contribution_choice_ranges x",
                "apply no_bertrand_central_contribution_choice_ranges",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hentry_witness_right",
                "rewrite heq",
                "rewrite heq",
                "rewrite heq",
                "exact hrange",
            ),
            "Every decoded central contribution inherits the reviewed ranges.",
        ),
    )


__all__ = [
    "make_bertrand_prime_contribution_complete_candidate_theorems",
    "PRIME_CONTRIBUTION_SELECTED_ENTRY",
    "PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES",
    "PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION",
    "PRIME_CONTRIBUTION_COFACTOR_EQ_ONE",
    "PRIME_CONTRIBUTION_REVERSE_DIVIDES",
    "PRIME_CONTRIBUTION_PRODUCT_EQ",
    "PRIME_CONTRIBUTION_COMPLETE_EXISTS",
    "CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS",
    "NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES",
    "NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES",
]
