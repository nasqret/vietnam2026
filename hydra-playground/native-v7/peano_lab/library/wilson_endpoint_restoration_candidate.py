"""Isolated native Wilson endpoint-restoration candidates.

The terminal PairOrder campaign produces the exact product of the consecutive
range ``2,...,p-2``.  Existing beta-prefix extension appends on the right and
existing Product transport preserves length, so neither can insert the
missing leading unit.  The first bridge below instead proves directly that a
Range starting at two has the same product as the factorial one step longer.
One factorial decomposition then restores the final factor ``p-1``.

All displayed relations expand to ordinary first-order Peano arithmetic.
This module is unregistered and introduces no parser or kernel symbol.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_factorial_theorems import factorial_relation
from .finite_fold_surface import (
    _beta_at_term as _fold_beta_at_term,
    _product_relation_term,
    product_relation,
)
from .wilson_inverse_prefix_candidate import prime
from .wilson_inverse_prefix_candidate import inverse_prefix
from .wilson_pair_order_candidate import (
    _beta_at_term as _pair_beta_at_term,
    _lt_term as _pair_lt_term,
)
from .wilson_pair_order_induction_candidate import _pair_order_state_term
from .wilson_pair_order_paired_iteration_candidate import paired_inverse_witness
from .wilson_pair_product_candidate import _mod_eq_term, adjacent_unit_pairs
from .wilson_successor_lift_candidate import _successor_lift_prefix_term
from .wilson_terminal_product_candidate import _conjunction, _range_two_prefix_term


def _range_prefix_term(
    code: str,
    scale: str,
    start_term: str,
    length_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand a trusted consecutive range with possibly compound terms."""

    index = f"wer_range_index_{tag}"
    gap = f"wer_range_gap_{tag}"
    local = avoid + (index, gap)
    bound = f"exists {gap}. {gap} + S {index} = {length_term}"
    decoded = _fold_beta_at_term(
        code,
        scale,
        index,
        f"{start_term} + {index}",
        tag=f"{tag}_decoded",
        avoid=local,
    )
    return f"forall {index}. ({bound}) -> ({decoded})"


def _factorial_term(
    length_term: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand relational Factorial at a trusted compound length."""

    code = f"wer_factor_code_{tag}"
    scale = f"wer_factor_scale_{tag}"
    if code in avoid or scale in avoid:
        raise ValueError("generated factorial witness captures an argument")
    local = avoid + (code, scale)
    range_prefix = _range_prefix_term(
        code,
        scale,
        "1",
        length_term,
        tag=f"{tag}_range",
        avoid=local,
    )
    product = _product_relation_term(
        code,
        scale,
        length_term,
        result,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({range_prefix}) /\\ ({product}))"


def make_wilson_endpoint_restoration_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the unit shift, last-factor restoration, and prime-shape split."""

    one_factorial = factorial_relation("n", "F", tag="wer_one")
    zero_factorial_R = _factorial_term(
        "0", "R", tag="wer_one_zero", avoid=("n", "F", "R")
    )

    variables = ("b", "c", "z", "d", "l", "P", "F", "R", "p", "n")
    range_two = _range_two_prefix_term(
        "b", "c", "l", tag="wer_range_two", avoid=variables
    )
    range_two_product = product_relation(
        "b", "c", "l", "P", tag="wer_range_two_product"
    )
    factorial_successor = _factorial_term(
        "S l", "P", tag="wer_factorial_successor", avoid=variables
    )

    factorial_one_F = _factorial_term(
        "1", "F", tag="wer_factorial_one_F", avoid=variables
    )

    step_variables = variables + ("i", "x", "x1", "x2", "x3", "x4")
    step_prefix_range = _range_two_prefix_term(
        "b", "c", "l", tag="wer_step_prefix_range", avoid=step_variables
    )
    step_factor = _fold_beta_at_term(
        "b",
        "c",
        "l",
        "x",
        tag="wer_step_factor",
        avoid=step_variables,
    )
    step_prefix_product = _product_relation_term(
        "b",
        "c",
        "l",
        "x1",
        tag="wer_step_prefix_product",
        avoid=step_variables,
    )
    step_decomposition = (
        f"exists x x1. (({step_factor}) /\\ "
        f"(({step_prefix_product}) /\\ P = x1 * x))"
    )
    step_prefix_factorial = _factorial_term(
        "S l", "x1", tag="wer_step_prefix_factorial", avoid=step_variables
    )
    step_full_factorial_F = _factorial_term(
        "S (S l)", "F", tag="wer_step_full_factorial_F", avoid=step_variables
    )
    step_previous_factorial = _factorial_term(
        "S l", "x3", tag="wer_step_previous_factorial", avoid=step_variables
    )
    step_factorial_decomposition = (
        f"exists x3. (({step_previous_factorial}) /\\ "
        "x2 = x3 * S (S l))"
    )

    endpoint_factorial = factorial_relation("n", "F", tag="wer_endpoint")
    endpoint_prefix_factorial = _factorial_term(
        "S l", "P", tag="wer_endpoint_prefix_factorial", avoid=variables
    )
    endpoint_previous_factorial = _factorial_term(
        "S l", "R", tag="wer_endpoint_previous_factorial", avoid=variables
    )
    endpoint_decomposition = (
        f"exists R. (({endpoint_previous_factorial}) /\\ "
        "F = R * S (S l))"
    )

    mod_left = _mod_eq_term(
        "p", "P", "1", tag="wer_mod_left", avoid=variables
    )
    mod_result = _mod_eq_term(
        "p", "F", "n", tag="wer_mod_result", avoid=variables
    )
    mod_scaled = _mod_eq_term(
        "p", "P * n", "1 * n", tag="wer_mod_scaled", avoid=variables
    )

    prime_p = prime("p", tag="wer_shape_prime")

    package_variables = (
        "p",
        "n",
        "m",
        "u",
        "v",
        "b",
        "c",
        "f",
        "g",
        "Q",
        "z",
        "d",
        "P",
        "s",
        "q",
    )
    terminal_inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wer_terminal_inverse"
    )
    terminal_coverage_value_bound = _pair_lt_term(
        "s",
        "S (S (m + m))",
        tag="wer_terminal_coverage_value_bound",
        avoid=package_variables,
    )
    terminal_coverage_index_bound = _pair_lt_term(
        "q",
        "m + m",
        tag="wer_terminal_coverage_index_bound",
        avoid=package_variables,
    )
    terminal_coverage_entry = _pair_beta_at_term(
        "b",
        "c",
        "q",
        "s",
        tag="wer_terminal_coverage_entry",
        avoid=package_variables,
    )
    terminal_coverage = (
        f"forall s. ({terminal_coverage_value_bound}) -> "
        "(~(s = 0) /\\ ~((S s) = S (S (m + m)))) -> "
        f"exists q. (({terminal_coverage_index_bound}) /\\ "
        f"({terminal_coverage_entry}))"
    )
    terminal_lift = _successor_lift_prefix_term(
        "b",
        "c",
        "f",
        "g",
        "m + m",
        tag="wer_terminal_lift",
        avoid=package_variables,
    )
    terminal_adjacent = adjacent_unit_pairs(
        "p", "f", "g", "m", tag="wer_terminal_adjacent"
    )
    terminal_lifted_product = _product_relation_term(
        "f",
        "g",
        "m + m",
        "Q",
        tag="wer_terminal_lifted_product",
        avoid=package_variables,
    )
    terminal_mod_one = _mod_eq_term(
        "p", "Q", "1", tag="wer_terminal_mod_one", avoid=package_variables
    )
    terminal_range = _range_two_prefix_term(
        "z",
        "d",
        "m + m",
        tag="wer_terminal_range",
        avoid=package_variables,
    )
    terminal_canonical_product = _product_relation_term(
        "z",
        "d",
        "m + m",
        "P",
        tag="wer_terminal_canonical_product",
        avoid=package_variables,
    )
    terminal_projection = "exists z d P. " + _conjunction(
        terminal_range,
        terminal_canonical_product,
        _mod_eq_term(
            "p",
            "P",
            "1",
            tag="wer_terminal_projection_mod",
            avoid=package_variables,
        ),
    )

    witness_variables = package_variables + (
        "x",
        "x1",
        "x2",
        "x3",
        "x4",
        "x5",
        "x6",
        "x7",
        "x8",
        "x9",
    )
    terminal_state_x = _pair_order_state_term(
        "x",
        "x1",
        "b",
        "c",
        "m + m",
        "n",
        tag="wer_terminal_state_x",
        avoid=witness_variables,
    )
    terminal_history_x = paired_inverse_witness(
        "x", "x1", "b", "c", "m", tag="wer_terminal_history_x"
    )
    terminal_package_x = "exists b c f g Q z d P. " + _conjunction(
        terminal_state_x,
        terminal_history_x,
        terminal_coverage,
        terminal_lift,
        terminal_adjacent,
        terminal_lifted_product,
        terminal_mod_one,
        terminal_range,
        terminal_canonical_product,
        "P = Q",
    )
    witness_state = _pair_order_state_term(
        "x",
        "x1",
        "x2",
        "x3",
        "m + m",
        "n",
        tag="wer_witness_state",
        avoid=witness_variables,
    )
    witness_history = paired_inverse_witness(
        "x", "x1", "x2", "x3", "m", tag="wer_witness_history"
    )
    witness_coverage_entry = _pair_beta_at_term(
        "x2",
        "x3",
        "q",
        "s",
        tag="wer_witness_coverage_entry",
        avoid=witness_variables,
    )
    witness_coverage = (
        f"forall s. ({terminal_coverage_value_bound}) -> "
        "(~(s = 0) /\\ ~((S s) = S (S (m + m)))) -> "
        f"exists q. (({terminal_coverage_index_bound}) /\\ "
        f"({witness_coverage_entry}))"
    )
    witness_lift = _successor_lift_prefix_term(
        "x2",
        "x3",
        "x4",
        "x5",
        "m + m",
        tag="wer_witness_lift",
        avoid=witness_variables,
    )
    witness_adjacent = adjacent_unit_pairs(
        "p", "x4", "x5", "m", tag="wer_witness_adjacent"
    )
    witness_lifted_product = _product_relation_term(
        "x4",
        "x5",
        "m + m",
        "x6",
        tag="wer_witness_lifted_product",
        avoid=witness_variables,
    )
    witness_mod_one = _mod_eq_term(
        "p", "x6", "1", tag="wer_witness_mod_one", avoid=witness_variables
    )
    witness_range = _range_two_prefix_term(
        "x7",
        "x8",
        "m + m",
        tag="wer_witness_range",
        avoid=witness_variables,
    )
    witness_product = _product_relation_term(
        "x7",
        "x8",
        "m + m",
        "x9",
        tag="wer_witness_product",
        avoid=witness_variables,
    )
    witness_mod_product = _mod_eq_term(
        "p",
        "x9",
        "1",
        tag="wer_witness_mod_product",
        avoid=witness_variables,
    )
    terminal_witness_parts = _conjunction(
        witness_state,
        witness_history,
        witness_coverage,
        witness_lift,
        witness_adjacent,
        witness_lifted_product,
        witness_mod_one,
        witness_range,
        witness_product,
        "x9 = x6",
    )

    final_factorial = factorial_relation("n", "F", tag="wer_final_factorial")
    final_mod = _mod_eq_term(
        "p", "F", "n", tag="wer_final_mod", avoid=("p", "n", "F")
    )
    package_body_hypothesis = "hpackage" + "_witness" * 8
    parts_right_six = "hparts" + "_right" * 6
    parts_right_seven = "hparts" + "_right" * 7
    parts_right_eight = "hparts" + "_right" * 8

    return (
        spec(
            "factorial_one_value",
            f"forall n F. n = 1 -> ({one_factorial}) -> F = 1",
            ("factorial_succ_decompose", "factorial_zero", "mul_one"),
            (
                "intro n",
                "intro F",
                "intro hn",
                "intro hfactorial",
                "have hdecomp : exists R. "
                + f"(({zero_factorial_R}) /\\ "
                "F = R * 1)",
                "specialize factorial_succ_decompose 0",
                "specialize factorial_succ_decompose n",
                "specialize factorial_succ_decompose F",
                "apply factorial_succ_decompose",
                "exact hn",
                "exact hfactorial",
                "cases hdecomp",
                "cases hdecomp_witness",
                "have hzero : x = 1",
                "specialize factorial_zero 0",
                "specialize factorial_zero x",
                "apply factorial_zero",
                "refl",
                "exact hdecomp_witness_left",
                "trans x * 1",
                "exact hdecomp_witness_right",
                "trans x",
                "specialize mul_one x",
                "exact mul_one",
                "exact hzero",
            ),
            "The relational factorial of one has value one.",
        ),
        spec(
            "beta_range_two_product_is_factorial_succ",
            "forall l b c P. "
            f"({range_two}) -> ({range_two_product}) -> ({factorial_successor})",
            (
                "factorial_one_value",
                "beta_product_zero",
                "beta_product_succ_decompose",
                "beta_range_entry_eq",
                "factorial_exists",
                "factorial_succ_decompose",
                "factorial_functional",
                "le_succ",
                "le_refl",
                "add_succ_left",
                "zero_add",
                "mul_congr",
            ),
            (
                "intro l",
                "induction l",
                "intro b",
                "intro c",
                "intro P",
                "intro hrange",
                "intro hproduct",
                "have hpone : P = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero P",
                "apply beta_product_zero",
                "exact hproduct",
                f"have hfactorial : exists F. ({factorial_one_F})",
                "specialize factorial_exists 1",
                "exact factorial_exists",
                "cases hfactorial",
                "have hfone : x = 1",
                "specialize factorial_one_value 1",
                "specialize factorial_one_value x",
                "apply factorial_one_value",
                "refl",
                "exact hfactorial_witness",
                "have hpx : P = x",
                "trans 1",
                "exact hpone",
                "symm",
                "exact hfone",
                "rewrite hpx",
                "rewrite hpx",
                "exact hfactorial_witness",
                "intro b",
                "intro c",
                "intro P",
                f"intro hrange",
                f"intro hproduct",
                f"have hrange_prefix : {step_prefix_range}",
                "intro i",
                "intro hi",
                "specialize hrange i",
                "apply hrange",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                f"have hdecomp : {step_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose P",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                f"have hprefix_factorial : {step_prefix_factorial}",
                "specialize IH b",
                "specialize IH c",
                "specialize IH x1",
                "apply IH",
                "exact hrange_prefix",
                "exact hdecomp_witness_witness_right_left",
                "have hfactor_value : x = S (S l)",
                "have hfactor_raw : x = 2 + l",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 2",
                "specialize beta_range_entry_eq (S l)",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomp_witness_witness_left",
                "trans 2 + l",
                "exact hfactor_raw",
                "simp [add_succ_left, zero_add]",
                f"have hfull_factorial : exists F. ({step_full_factorial_F})",
                "specialize factorial_exists (S (S l))",
                "exact factorial_exists",
                "cases hfull_factorial",
                f"have hfactorial_decomp : {step_factorial_decomposition}",
                "specialize factorial_succ_decompose (S l)",
                "specialize factorial_succ_decompose (S (S l))",
                "specialize factorial_succ_decompose x2",
                "apply factorial_succ_decompose",
                "refl",
                "exact hfull_factorial_witness",
                "cases hfactorial_decomp",
                "cases hfactorial_decomp_witness",
                "have hprefix_eq : x1 = x3",
                "specialize factorial_functional (S l)",
                "specialize factorial_functional x1",
                "specialize factorial_functional x3",
                "apply factorial_functional",
                "exact hprefix_factorial",
                "exact hfactorial_decomp_witness_left",
                "have hproduct_eq : P = x2",
                "trans x1 * x",
                "exact hdecomp_witness_witness_right_right",
                "trans x1 * S (S l)",
                "apply mul_congr",
                "refl",
                "exact hfactor_value",
                "trans x3 * S (S l)",
                "apply mul_congr",
                "exact hprefix_eq",
                "refl",
                "symm",
                "exact hfactorial_decomp_witness_right",
                "rewrite hproduct_eq",
                "rewrite hproduct_eq",
                "exact hfull_factorial_witness",
            ),
            "A product of 2,...,l+1 is the factorial of l+1; the missing leading factor is one.",
        ),
        spec(
            "beta_range_two_product_restore_last",
            "forall b c l P n F. n = S (S l) -> "
            f"({range_two}) -> ({range_two_product}) -> "
            f"({endpoint_factorial}) -> F = P * n",
            (
                "beta_range_two_product_is_factorial_succ",
                "factorial_succ_decompose",
                "factorial_functional",
                "mul_congr",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro P",
                "intro n",
                "intro F",
                "intro hterminal",
                "intro hrange",
                "intro hproduct",
                "intro hfactorial",
                f"have hprefix_factorial : {endpoint_prefix_factorial}",
                "specialize beta_range_two_product_is_factorial_succ l",
                "specialize beta_range_two_product_is_factorial_succ b",
                "specialize beta_range_two_product_is_factorial_succ c",
                "specialize beta_range_two_product_is_factorial_succ P",
                "apply beta_range_two_product_is_factorial_succ",
                "exact hrange",
                "exact hproduct",
                f"have hdecomp : {endpoint_decomposition}",
                "specialize factorial_succ_decompose (S l)",
                "specialize factorial_succ_decompose n",
                "specialize factorial_succ_decompose F",
                "apply factorial_succ_decompose",
                "exact hterminal",
                "exact hfactorial",
                "cases hdecomp",
                "cases hdecomp_witness",
                "have hpref : P = x",
                "specialize factorial_functional (S l)",
                "specialize factorial_functional P",
                "specialize factorial_functional x",
                "apply factorial_functional",
                "exact hprefix_factorial",
                "exact hdecomp_witness_left",
                "trans x * S (S l)",
                "exact hdecomp_witness_right",
                "trans P * S (S l)",
                "apply mul_congr",
                "symm",
                "exact hpref",
                "refl",
                "apply mul_congr",
                "refl",
                "symm",
                "exact hterminal",
            ),
            "Restore the final factor l+2 after the leading unit has been absorbed.",
        ),
        spec(
            "mod_one_product_restore_predecessor",
            f"forall p P n F. F = P * n -> ({mod_left}) -> ({mod_result})",
            ("mod_eq_mul_right", "one_mul"),
            (
                "intro p",
                "intro P",
                "intro n",
                "intro F",
                "intro hproduct",
                "intro hmod",
                f"have hscaled : {mod_scaled}",
                "specialize mod_eq_mul_right p",
                "specialize mod_eq_mul_right P",
                "specialize mod_eq_mul_right 1",
                "specialize mod_eq_mul_right n",
                "apply mod_eq_mul_right",
                "exact hmod",
                "have hone : 1 * n = n",
                "specialize one_mul n",
                "exact one_mul",
                "rewrite hone at hscaled",
                "rewrite hproduct",
                "exact hscaled",
            ),
            "Multiplying a residue-one product by n restores the predecessor residue n.",
        ),
        spec(
            "prime_two_or_terminal_odd_shape",
            f"forall p. ({prime_p}) -> "
            "p = 2 \\/ exists m. p = S (S (S (m + m)))",
            (
                "eq_decidable",
                "prime_ne_two_is_odd",
                "nonzero_is_succ",
                "mul_succ_left",
                "mul_zero_left",
                "zero_add",
                "add_succ_left",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro p",
                "intro hp",
                "have hcases : p = 2 \\/ ~(p = 2)",
                "specialize eq_decidable p",
                "specialize eq_decidable 2",
                "exact eq_decidable",
                "cases hcases",
                "left",
                "exact hcases_left",
                "right",
                "have hodd : exists h. p = 2 * h + 1",
                "specialize prime_ne_two_is_odd p",
                "apply prime_ne_two_is_odd",
                "exact hp",
                "exact hcases_right",
                "cases hodd",
                f"have hparts : {prime_p}",
                "exact hp",
                "cases hparts",
                "have hh : ~(x = 0)",
                "intro hxzero",
                "apply hparts_left",
                "trans 2 * x + 1",
                "exact hodd_witness",
                "rewrite hxzero",
                "simp [mul_succ_left, mul_zero_left, zero_add, add_succ_left]",
                "have hsucc : exists m. x = S m",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hh",
                "cases hsucc",
                "exists x1",
                "trans 2 * S x1 + 1",
                "rewrite <- hsucc_witness",
                "exact hodd_witness",
                "simp [mul_succ_left, mul_zero_left, zero_add, "
                "add_succ_left, add_assoc, add_comm]",
            ),
            "A prime is two or has exactly the doubled terminal PairOrder shape.",
        ),
        spec(
            "prime_terminal_range_two_product_mod_one_exists",
            "forall p n m. p = S n -> "
            f"({prime_p}) -> n = S (S (m + m)) -> ({terminal_projection})",
            (
                "prime_inverse_prefix_exists",
                "prime_wilson_terminal_product_package_exists",
            ),
            (
                "intro p",
                "intro n",
                "intro m",
                "intro hpn",
                "intro hp",
                "intro hterminal",
                f"have hinverse : exists u v. ({terminal_inverse})",
                "specialize prime_inverse_prefix_exists p",
                "specialize prime_inverse_prefix_exists n",
                "apply prime_inverse_prefix_exists",
                "exact hpn",
                "exact hp",
                "cases hinverse",
                "cases hinverse_witness",
                f"have hpackage : {terminal_package_x}",
                "specialize prime_wilson_terminal_product_package_exists p",
                "specialize prime_wilson_terminal_product_package_exists n",
                "specialize prime_wilson_terminal_product_package_exists x",
                "specialize prime_wilson_terminal_product_package_exists x1",
                "specialize prime_wilson_terminal_product_package_exists "
                "(S (m + m))",
                "specialize prime_wilson_terminal_product_package_exists m",
                "apply prime_wilson_terminal_product_package_exists",
                "exact hpn",
                "exact hp",
                "exact hinverse_witness_witness",
                "exact hterminal",
                "exact hterminal",
                "cases hpackage",
                "cases hpackage_witness",
                "cases hpackage_witness_witness",
                "cases hpackage_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness_witness",
                f"have hparts : {terminal_witness_parts}",
                f"exact {package_body_hypothesis}",
                "cases hparts",
                "cases hparts_right",
                "cases hparts_right_right",
                "cases hparts_right_right_right",
                "cases hparts_right_right_right_right",
                "cases hparts_right_right_right_right_right",
                f"cases {parts_right_six}",
                f"cases {parts_right_seven}",
                f"cases {parts_right_eight}",
                f"have hmod_product : {witness_mod_product}",
                f"rewrite {parts_right_eight}_right",
                f"exact {parts_right_six}_left",
                "exists x7",
                "exists x8",
                "exists x9",
                "split",
                f"exact {parts_right_seven}_left",
                "split",
                f"exact {parts_right_eight}_left",
                "exact hmod_product",
            ),
            "Project the terminal PairOrder package to its canonical nonendpoint product modulo one.",
        ),
        spec(
            "prime_factorial_wilson_congruence",
            "forall p n F. p = S n -> "
            f"({prime_p}) -> ({final_factorial}) -> ({final_mod})",
            (
                "prime_two_or_terminal_odd_shape",
                "succ_injective",
                "factorial_one_value",
                "mod_eq_refl",
                "prime_terminal_range_two_product_mod_one_exists",
                "beta_range_two_product_restore_last",
                "mod_one_product_restore_predecessor",
            ),
            (
                "intro p",
                "intro n",
                "intro F",
                "intro hpn",
                "intro hp",
                "intro hfactorial",
                "have hshape : p = 2 \\/ exists m. "
                "p = S (S (S (m + m)))",
                "specialize prime_two_or_terminal_odd_shape p",
                "apply prime_two_or_terminal_odd_shape",
                "exact hp",
                "cases hshape",
                "have hn : n = 1",
                "specialize succ_injective n",
                "specialize succ_injective 1",
                "apply succ_injective",
                "trans p",
                "symm",
                "exact hpn",
                "trans 2",
                "exact hshape_left",
                "refl",
                "have hfone : F = 1",
                "specialize factorial_one_value n",
                "specialize factorial_one_value F",
                "apply factorial_one_value",
                "exact hn",
                "exact hfactorial",
                "have hfn : F = n",
                "trans 1",
                "exact hfone",
                "symm",
                "exact hn",
                "rewrite hfn",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl n",
                "exact mod_eq_refl",
                "cases hshape_right",
                "have hnterminal : n = S (S (x + x))",
                "specialize succ_injective n",
                "specialize succ_injective (S (S (x + x)))",
                "apply succ_injective",
                "trans p",
                "symm",
                "exact hpn",
                "exact hshape_right_witness",
                "have hterminal_product : exists z d P. "
                + _conjunction(
                    _range_two_prefix_term(
                        "z",
                        "d",
                        "x + x",
                        tag="wer_final_terminal_range",
                        avoid=("p", "n", "F", "x", "z", "d", "P"),
                    ),
                    _product_relation_term(
                        "z",
                        "d",
                        "x + x",
                        "P",
                        tag="wer_final_terminal_product",
                        avoid=("p", "n", "F", "x", "z", "d", "P"),
                    ),
                    _mod_eq_term(
                        "p",
                        "P",
                        "1",
                        tag="wer_final_terminal_mod",
                        avoid=("p", "n", "F", "x", "z", "d", "P"),
                    ),
                ),
                "specialize prime_terminal_range_two_product_mod_one_exists p",
                "specialize prime_terminal_range_two_product_mod_one_exists n",
                "specialize prime_terminal_range_two_product_mod_one_exists x",
                "apply prime_terminal_range_two_product_mod_one_exists",
                "exact hpn",
                "exact hp",
                "exact hnterminal",
                "cases hterminal_product",
                "cases hterminal_product_witness",
                "cases hterminal_product_witness_witness",
                "cases hterminal_product_witness_witness_witness",
                "cases hterminal_product_witness_witness_witness_right",
                "have hrestored : F = x3 * n",
                "specialize beta_range_two_product_restore_last x1",
                "specialize beta_range_two_product_restore_last x2",
                "specialize beta_range_two_product_restore_last (x + x)",
                "specialize beta_range_two_product_restore_last x3",
                "specialize beta_range_two_product_restore_last n",
                "specialize beta_range_two_product_restore_last F",
                "apply beta_range_two_product_restore_last",
                "exact hnterminal",
                "exact hterminal_product_witness_witness_witness_left",
                "exact hterminal_product_witness_witness_witness_right_left",
                "exact hfactorial",
                "specialize mod_one_product_restore_predecessor p",
                "specialize mod_one_product_restore_predecessor x3",
                "specialize mod_one_product_restore_predecessor n",
                "specialize mod_one_product_restore_predecessor F",
                "apply mod_one_product_restore_predecessor",
                "exact hrestored",
                "exact hterminal_product_witness_witness_witness_right_right",
            ),
            "Wilson's factorial congruence for every prime, with p=2 handled before terminal pairing.",
        ),
    )


__all__ = ["make_wilson_endpoint_restoration_candidate_theorems"]
