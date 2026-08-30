"""Complete constructive solvability of a natural linear congruence.

The fixed object language remains first-order Heyting arithmetic.  Relational
gcd, bounded natural order, divisibility, and balanced congruence below are
only hygienic authoring abbreviations; their fully expanded formulas are the
actual statements seen by the unchanged independent kernel.

The crucial construction reduces ``a*x = b (mod m)`` to the already checked
binary CRT problem ``y = 0 (mod a)``, ``y = b (mod m)``.  This works even
when either modulus is zero.  At nonzero ``m``, an independently constructed
canonical remainder produces the exact bounded witness demanded by campaign
milestone G012.  These are isolated dependency-curried candidates: no Alpha
or Stable enrollment, checked-use admission, or empty-context closure follows
merely from importing this module.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq


LINEAR_CONGRUENCE_ZERO_RESIDUE_DIVIDES = "linear_congruence_zero_residue_divides"
LINEAR_CONGRUENCE_SOLUTION_FORCES_GCD_DIVISIBILITY = (
    "linear_congruence_solution_forces_gcd_divisibility"
)
LINEAR_CONGRUENCE_GCD_DIVISIBILITY_CONSTRUCTS_SOLUTION = (
    "linear_congruence_gcd_divisibility_constructs_solution"
)
LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES = (
    "linear_congruence_all_moduli_solvable_iff_gcd_divides"
)
LINEAR_CONGRUENCE_NONZERO_MODULUS_BOUNDED_CONSTRUCTOR = (
    "linear_congruence_nonzero_modulus_bounded_constructor"
)
LINEAR_CONGRUENCE_SOLVABLE_IFF_GCD_DIVIDES = (
    "linear_congruence_solvable_iff_gcd_divides"
)
LINEAR_CONGRUENCE_ZERO_MODULUS_EXACT_DIVISIBILITY = (
    "linear_congruence_zero_modulus_exact_divisibility"
)
LINEAR_CONGRUENCE_CERTIFIED_DECISION = "linear_congruence_certified_decision"
LINEAR_CONGRUENCE_COPRIME_BOUNDED_SOLUTION_UNIQUE = (
    "linear_congruence_coprime_bounded_solution_unique"
)


def _mod(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    return balanced_mod_eq(
        modulus,
        left,
        right,
        tag=f"linear_{tag}",
        variables=variables,
    )


def _divides(divisor: str, value: str, *, tag: str) -> str:
    witness = f"linear_quotient_{tag}"
    return f"exists {witness}. ({value}) = ({divisor}) * {witness}"


def _less_than(left: str, right: str, *, tag: str) -> str:
    gap = f"linear_gap_{tag}"
    return f"exists {gap}. {gap} + S ({left}) = ({right})"


def make_linear_congruence_complete_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the complete nine-row dependency-ordered G012 proof campaign."""

    zero_variables = ("d", "n")
    zero_residue = _mod("d", "n", "0", tag="zero_residue", variables=zero_variables)
    zero_divides = _divides("d", "n", tag="zero_result")

    variables = ("a", "m", "b", "g", "x")
    gcd_necessity = is_gcd("g", "a", "m", tag="linear_necessity")
    solution_necessity = _mod(
        "m", "a * x", "b", tag="necessity_solution", variables=variables
    )
    zero_first_necessity = _mod(
        "a", "a * x", "0", tag="necessity_first", variables=variables
    )
    compatibility_necessity = _mod(
        "g", "0", "b", tag="necessity_compatibility", variables=variables
    )
    reverse_necessity = _mod(
        "g", "b", "0", tag="necessity_reverse", variables=variables
    )
    divisor_necessity = _divides("g", "b", tag="necessity")

    sufficiency_variables = ("a", "m", "b", "g", "y")
    gcd_sufficiency = is_gcd("g", "a", "m", tag="linear_sufficiency")
    divisor_sufficiency = _divides("g", "b", tag="sufficiency")
    compatibility_sufficiency = _mod(
        "g", "0", "b", tag="sufficiency_compatibility", variables=sufficiency_variables
    )
    reverse_sufficiency = _mod(
        "g", "b", "0", tag="sufficiency_reverse", variables=sufficiency_variables
    )
    first_sufficiency = _mod(
        "a", "y", "0", tag="sufficiency_first", variables=sufficiency_variables
    )
    second_sufficiency = _mod(
        "m", "y", "b", tag="sufficiency_second", variables=sufficiency_variables
    )
    solution_sufficiency = _mod(
        "m", "a * x", "b", tag="sufficiency_result", variables=variables
    )

    gcd_all = is_gcd("g", "a", "m", tag="linear_all_moduli")
    divisor_all = _divides("g", "b", tag="all_moduli")
    solution_all = _mod(
        "m", "a * x", "b", tag="all_moduli_solution", variables=variables
    )
    all_solvable = f"exists x. ({solution_all})"

    gcd_bounded = is_gcd("g", "a", "m", tag="linear_bounded")
    divisor_bounded = _divides("g", "b", tag="bounded")
    bound_bounded = _less_than("x", "m", tag="bounded")
    solution_bounded = _mod(
        "m", "a * x", "b", tag="bounded_solution", variables=variables
    )
    bounded_solvable = f"exists x. (({bound_bounded}) /\\ ({solution_bounded}))"

    gcd_root = is_gcd("g", "a", "m", tag="linear_root")
    divisor_root = _divides("g", "b", tag="root")
    bound_root = _less_than("x", "m", tag="root")
    solution_root = _mod(
        "m", "a * x", "b", tag="root_solution", variables=variables
    )
    root_solvable = f"exists x. (({bound_root}) /\\ ({solution_root}))"

    zero_modulus_gcd = is_gcd("g", "a", "m", tag="linear_zero_modulus")
    zero_modulus_divisor = _divides("g", "b", tag="zero_modulus")
    zero_modulus_solution = _mod(
        "m", "a * x", "b", tag="zero_modulus_solution", variables=variables
    )

    gcd_decision = is_gcd("g", "a", "m", tag="linear_decision")
    divisor_decision = _divides("g", "b", tag="decision")
    decision_solution = _mod(
        "m", "a * x", "b", tag="decision_solution", variables=variables
    )
    decision_solvable = f"exists x. ({decision_solution})"

    unique_variables = ("a", "m", "b", "x", "y")
    first_unique = _mod(
        "m", "a * x", "b", tag="unique_first", variables=unique_variables
    )
    second_unique = _mod(
        "m", "a * y", "b", tag="unique_second", variables=unique_variables
    )
    reverse_unique = _mod(
        "m", "b", "a * y", tag="unique_reverse", variables=unique_variables
    )
    scaled_unique = _mod(
        "m", "a * x", "a * y", tag="unique_scaled", variables=unique_variables
    )
    canceled_unique = _mod(
        "m", "x", "y", tag="unique_canceled", variables=unique_variables
    )
    first_bound = _less_than("x", "m", tag="unique_first")
    second_bound = _less_than("y", "m", tag="unique_second")
    coprime = (
        "forall d. (exists u. a = d * u) -> "
        "(exists v. m = d * v) -> d = 1"
    )

    return (
        spec(
            LINEAR_CONGRUENCE_ZERO_RESIDUE_DIVIDES,
            f"forall d n. ({zero_residue}) -> ({zero_divides})",
            ("factor_difference", "zero_add", "add_comm"),
            (
                "intro d",
                "intro n",
                "intro hmod",
                "cases hmod",
                "cases hmod_witness",
                "specialize factor_difference d",
                "specialize factor_difference x1",
                "specialize factor_difference x",
                "specialize factor_difference n",
                "apply factor_difference",
                "trans 0 + d * x1",
                "symm",
                "apply zero_add",
                "trans n + d * x",
                "symm",
                "exact hmod_witness_witness",
                "apply add_comm",
            ),
            "A balanced natural congruence to zero yields an actual divisibility witness, including divisor zero.",
        ),
        spec(
            LINEAR_CONGRUENCE_SOLUTION_FORCES_GCD_DIVISIBILITY,
            f"forall a m b g x. ({gcd_necessity}) -> "
            f"({solution_necessity}) -> ({divisor_necessity})",
            (
                "dvd_to_mod_zero",
                "crt_common_solution_implies_gcd_compatible",
                "mod_eq_symm",
                LINEAR_CONGRUENCE_ZERO_RESIDUE_DIVIDES,
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro x",
                "intro hgcd",
                "intro hsolution",
                f"have hfirst : {zero_first_necessity}",
                "specialize dvd_to_mod_zero a",
                "specialize dvd_to_mod_zero (a * x)",
                "apply dvd_to_mod_zero",
                "exists x",
                "refl",
                f"have hcompatibility : {compatibility_necessity}",
                "specialize crt_common_solution_implies_gcd_compatible g",
                "specialize crt_common_solution_implies_gcd_compatible a",
                "specialize crt_common_solution_implies_gcd_compatible m",
                "specialize crt_common_solution_implies_gcd_compatible 0",
                "specialize crt_common_solution_implies_gcd_compatible b",
                "specialize crt_common_solution_implies_gcd_compatible (a * x)",
                "apply crt_common_solution_implies_gcd_compatible",
                "exact hgcd",
                "split",
                "exact hfirst",
                "exact hsolution",
                f"have hreverse : {reverse_necessity}",
                "specialize mod_eq_symm g",
                "specialize mod_eq_symm 0",
                "specialize mod_eq_symm b",
                "apply mod_eq_symm",
                "exact hcompatibility",
                "specialize linear_congruence_zero_residue_divides g",
                "specialize linear_congruence_zero_residue_divides b",
                "apply linear_congruence_zero_residue_divides",
                "exact hreverse",
            ),
            "Every natural solution of a linear congruence forces its relational gcd to divide the right-hand side.",
        ),
        spec(
            LINEAR_CONGRUENCE_GCD_DIVISIBILITY_CONSTRUCTS_SOLUTION,
            f"forall a m b g. ({gcd_sufficiency}) -> "
            f"({divisor_sufficiency}) -> exists x. ({solution_sufficiency})",
            (
                "dvd_to_mod_zero",
                "mod_eq_symm",
                "generalized_binary_crt_sufficient",
                LINEAR_CONGRUENCE_ZERO_RESIDUE_DIVIDES,
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                "intro hdivides",
                f"have hreverse : {reverse_sufficiency}",
                "specialize dvd_to_mod_zero g",
                "specialize dvd_to_mod_zero b",
                "apply dvd_to_mod_zero",
                "exact hdivides",
                f"have hcompatibility : {compatibility_sufficiency}",
                "specialize mod_eq_symm g",
                "specialize mod_eq_symm b",
                "specialize mod_eq_symm 0",
                "apply mod_eq_symm",
                "exact hreverse",
                f"have hcrt : exists y. (({first_sufficiency}) /\\ ({second_sufficiency}))",
                "specialize generalized_binary_crt_sufficient g",
                "specialize generalized_binary_crt_sufficient a",
                "specialize generalized_binary_crt_sufficient m",
                "specialize generalized_binary_crt_sufficient 0",
                "specialize generalized_binary_crt_sufficient b",
                "apply generalized_binary_crt_sufficient",
                "exact hgcd",
                "exact hcompatibility",
                "cases hcrt",
                "cases hcrt_witness",
                "have hmultiple : exists q. x = a * q",
                "specialize linear_congruence_zero_residue_divides a",
                "specialize linear_congruence_zero_residue_divides x",
                "apply linear_congruence_zero_residue_divides",
                "exact hcrt_witness_left",
                "cases hmultiple",
                "exists x1",
                "rewrite <- hmultiple_witness",
                "exact hcrt_witness_right",
            ),
            "Binary generalized CRT explicitly constructs a linear-congruence solution whenever the relational gcd divides the target, including zero moduli.",
        ),
        spec(
            LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES,
            f"forall a m b g. ({gcd_all}) -> "
            f"((({all_solvable}) -> ({divisor_all})) /\\ "
            f"(({divisor_all}) -> ({all_solvable})))",
            (
                LINEAR_CONGRUENCE_SOLUTION_FORCES_GCD_DIVISIBILITY,
                LINEAR_CONGRUENCE_GCD_DIVISIBILITY_CONSTRUCTS_SOLUTION,
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                "split",
                "intro hsolution",
                "cases hsolution",
                "specialize linear_congruence_solution_forces_gcd_divisibility a",
                "specialize linear_congruence_solution_forces_gcd_divisibility m",
                "specialize linear_congruence_solution_forces_gcd_divisibility b",
                "specialize linear_congruence_solution_forces_gcd_divisibility g",
                "specialize linear_congruence_solution_forces_gcd_divisibility x",
                "apply linear_congruence_solution_forces_gcd_divisibility",
                "exact hgcd",
                "exact hsolution_witness",
                "intro hdivides",
                "specialize linear_congruence_gcd_divisibility_constructs_solution a",
                "specialize linear_congruence_gcd_divisibility_constructs_solution m",
                "specialize linear_congruence_gcd_divisibility_constructs_solution b",
                "specialize linear_congruence_gcd_divisibility_constructs_solution g",
                "apply linear_congruence_gcd_divisibility_constructs_solution",
                "exact hgcd",
                "exact hdivides",
            ),
            "For every natural modulus, including zero, a linear congruence has a natural solution exactly when the relational gcd divides its target.",
        ),
        spec(
            LINEAR_CONGRUENCE_NONZERO_MODULUS_BOUNDED_CONSTRUCTOR,
            f"forall a m b g. ({gcd_bounded}) -> ~(m = 0) -> "
            f"({divisor_bounded}) -> ({bounded_solvable})",
            (
                LINEAR_CONGRUENCE_GCD_DIVISIBILITY_CONSTRUCTS_SOLUTION,
                "canonical_remainder_exists",
                "add_comm",
                "mod_eq_mul_left",
                "mod_eq_trans",
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                "intro hnonzero",
                "intro hdivides",
                f"have hsolution : exists x. ({solution_bounded})",
                "specialize linear_congruence_gcd_divisibility_constructs_solution a",
                "specialize linear_congruence_gcd_divisibility_constructs_solution m",
                "specialize linear_congruence_gcd_divisibility_constructs_solution b",
                "specialize linear_congruence_gcd_divisibility_constructs_solution g",
                "apply linear_congruence_gcd_divisibility_constructs_solution",
                "exact hgcd",
                "exact hdivides",
                "cases hsolution",
                "have hcanonical : exists r. ((exists q. x = m * q + r) /\\ "
                "(exists h. h + S r = m))",
                "specialize canonical_remainder_exists m",
                "specialize canonical_remainder_exists x",
                "apply canonical_remainder_exists",
                "exact hnonzero",
                "cases hcanonical",
                "cases hcanonical_witness",
                "cases hcanonical_witness_left",
                "exists x1",
                "split",
                "exact hcanonical_witness_right",
                "have hreverse : exists u v. x1 + m * u = x + m * v",
                "exists x2",
                "exists 0",
                "trans m * x2 + x1",
                "apply add_comm",
                "trans x",
                "symm",
                "exact hcanonical_witness_left_witness",
                "simp",
                "have hscaled : exists u v. (a * x1) + m * u = (a * x) + m * v",
                "specialize mod_eq_mul_left m",
                "specialize mod_eq_mul_left x1",
                "specialize mod_eq_mul_left x",
                "specialize mod_eq_mul_left a",
                "apply mod_eq_mul_left",
                "exact hreverse",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans (a * x1)",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans b",
                "apply mod_eq_trans",
                "exact hscaled",
                "exact hsolution_witness",
            ),
            "At every nonzero natural modulus, gcd divisibility constructs a canonical strictly bounded linear-congruence witness.",
        ),
        spec(
            LINEAR_CONGRUENCE_SOLVABLE_IFF_GCD_DIVIDES,
            f"forall a m b g. ({gcd_root}) -> ~(m = 0) -> "
            f"((({root_solvable}) -> ({divisor_root})) /\\ "
            f"(({divisor_root}) -> ({root_solvable})))",
            (
                LINEAR_CONGRUENCE_SOLUTION_FORCES_GCD_DIVISIBILITY,
                LINEAR_CONGRUENCE_NONZERO_MODULUS_BOUNDED_CONSTRUCTOR,
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                "intro hnonzero",
                "split",
                "intro hsolution",
                "cases hsolution",
                "cases hsolution_witness",
                "specialize linear_congruence_solution_forces_gcd_divisibility a",
                "specialize linear_congruence_solution_forces_gcd_divisibility m",
                "specialize linear_congruence_solution_forces_gcd_divisibility b",
                "specialize linear_congruence_solution_forces_gcd_divisibility g",
                "specialize linear_congruence_solution_forces_gcd_divisibility x",
                "apply linear_congruence_solution_forces_gcd_divisibility",
                "exact hgcd",
                "exact hsolution_witness_right",
                "intro hdivides",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor a",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor m",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor b",
                "specialize linear_congruence_nonzero_modulus_bounded_constructor g",
                "apply linear_congruence_nonzero_modulus_bounded_constructor",
                "exact hgcd",
                "exact hnonzero",
                "exact hdivides",
            ),
            "Complete linear-congruence milestone G012: at every nonzero modulus, a strictly bounded solution exists exactly when the relational gcd divides the right-hand side.",
        ),
        spec(
            LINEAR_CONGRUENCE_ZERO_MODULUS_EXACT_DIVISIBILITY,
            f"forall a m b g. ({zero_modulus_gcd}) -> m = 0 -> "
            f"((((exists x. a * x = b)) -> ({zero_modulus_divisor})) /\\ "
            f"(({zero_modulus_divisor}) -> (exists x. a * x = b)))",
            (
                LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES,
                "mod_eq_zero_iff_eq",
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                "intro hzero",
                f"have hiff : (((exists x. ({zero_modulus_solution})) -> "
                f"({zero_modulus_divisor})) /\\ "
                f"(({zero_modulus_divisor}) -> (exists x. ({zero_modulus_solution}))))",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides a",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides m",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides b",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides g",
                "apply linear_congruence_all_moduli_solvable_iff_gcd_divides",
                "exact hgcd",
                "cases hiff",
                "split",
                "intro hexact",
                "apply hiff_left",
                "cases hexact",
                "exists x",
                "rewrite hzero",
                "rewrite hzero",
                "specialize mod_eq_zero_iff_eq (a * x)",
                "specialize mod_eq_zero_iff_eq b",
                "cases mod_eq_zero_iff_eq",
                "apply mod_eq_zero_iff_eq_right",
                "exact hexact_witness",
                "intro hdivides",
                "have hsolution : exists x. (" + zero_modulus_solution + ")",
                "apply hiff_right",
                "exact hdivides",
                "cases hsolution",
                "exists x",
                "rewrite hzero at hsolution_witness",
                "rewrite hzero at hsolution_witness",
                "specialize mod_eq_zero_iff_eq (a * x)",
                "specialize mod_eq_zero_iff_eq b",
                "cases mod_eq_zero_iff_eq",
                "apply mod_eq_zero_iff_eq_left",
                "exact hsolution_witness",
            ),
            "At modulus zero the same gcd criterion is exactly ordinary natural divisibility, with no fictitious strictly bounded residue.",
        ),
        spec(
            LINEAR_CONGRUENCE_CERTIFIED_DECISION,
            f"forall a m b g. ({gcd_decision}) -> "
            f"(({decision_solvable}) \\/ ~({decision_solvable}))",
            (
                "multiple_decidable",
                LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES,
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro g",
                "intro hgcd",
                f"have hiff : ((({decision_solvable}) -> ({divisor_decision})) /\\ "
                f"(({divisor_decision}) -> ({decision_solvable})))",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides a",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides m",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides b",
                "specialize linear_congruence_all_moduli_solvable_iff_gcd_divides g",
                "apply linear_congruence_all_moduli_solvable_iff_gcd_divides",
                "exact hgcd",
                "cases hiff",
                f"have hdecision : ({divisor_decision}) \\/ ~({divisor_decision})",
                "specialize multiple_decidable g",
                "specialize multiple_decidable b",
                "exact multiple_decidable",
                "cases hdecision",
                "left",
                "apply hiff_right",
                "exact hdecision_left",
                "right",
                "intro hsolution",
                "apply hdecision_right",
                "apply hiff_left",
                "exact hsolution",
            ),
            "Every natural linear congruence has a constructive witnessed solution or a genuine gcd-divisibility obstruction, including zero modulus.",
        ),
        spec(
            LINEAR_CONGRUENCE_COPRIME_BOUNDED_SOLUTION_UNIQUE,
            "forall a m b x y. ~(m = 0) -> "
            f"({coprime}) -> ({first_bound}) -> ({second_bound}) -> "
            f"({first_unique}) -> ({second_unique}) -> x = y",
            (
                "mod_eq_symm",
                "mod_eq_trans",
                "mod_eq_cancel_coprime",
                "mod_eq_bounded_unique",
            ),
            (
                "intro a",
                "intro m",
                "intro b",
                "intro x",
                "intro y",
                "intro hnonzero",
                "intro hcoprime",
                "intro hxbound",
                "intro hybound",
                "intro hxsolution",
                "intro hysolution",
                f"have hreverse : {reverse_unique}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm (a * y)",
                "specialize mod_eq_symm b",
                "apply mod_eq_symm",
                "exact hysolution",
                f"have hscaled : {scaled_unique}",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans b",
                "specialize mod_eq_trans (a * y)",
                "apply mod_eq_trans",
                "exact hxsolution",
                "exact hreverse",
                f"have hcanceled : {canceled_unique}",
                "specialize mod_eq_cancel_coprime m",
                "specialize mod_eq_cancel_coprime a",
                "specialize mod_eq_cancel_coprime x",
                "specialize mod_eq_cancel_coprime y",
                "apply mod_eq_cancel_coprime",
                "exact hnonzero",
                "exact hcoprime",
                "exact hscaled",
                "specialize mod_eq_bounded_unique m",
                "specialize mod_eq_bounded_unique x",
                "specialize mod_eq_bounded_unique y",
                "apply mod_eq_bounded_unique",
                "exact hxbound",
                "exact hybound",
                "exact hcanceled",
            ),
            "For a coprime coefficient at nonzero modulus, any two strictly bounded natural linear-congruence solutions are equal.",
        ),
    )


__all__ = [
    "LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES",
    "LINEAR_CONGRUENCE_CERTIFIED_DECISION",
    "LINEAR_CONGRUENCE_COPRIME_BOUNDED_SOLUTION_UNIQUE",
    "LINEAR_CONGRUENCE_GCD_DIVISIBILITY_CONSTRUCTS_SOLUTION",
    "LINEAR_CONGRUENCE_NONZERO_MODULUS_BOUNDED_CONSTRUCTOR",
    "LINEAR_CONGRUENCE_SOLUTION_FORCES_GCD_DIVISIBILITY",
    "LINEAR_CONGRUENCE_SOLVABLE_IFF_GCD_DIVIDES",
    "LINEAR_CONGRUENCE_ZERO_MODULUS_EXACT_DIVISIBILITY",
    "LINEAR_CONGRUENCE_ZERO_RESIDUE_DIVIDES",
    "make_linear_congruence_complete_candidate_theorems",
]
