"""Constructive extraction of natural square factors over unchanged HA.

The square-product endpoint uses reduced gcd cofactors and Gauss cancellation,
not prime factorization or a classical choice principle.  Every script is an
ordinary dependency-curried proof for the original kernel; this candidate
module neither admits its rows nor changes any sealed Alpha edition.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import coprime


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def make_coprime_square_factor_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build zero-inclusive square-root and coprime square-factor proofs."""

    return (
        spec(
            "square_lt_strict",
            "forall a b. (exists k. k + S a = b) -> exists k. k + S (a * a) = b * b",
            ("square_lt_successor_square", "natural_square_monotone_expanded", "lt_of_lt_of_le"),
            (
                "intro a", "intro b", "intro hlt",
                *_call("lt_of_lt_of_le", "(a * a)", "(S a * S a)", "(b * b)"),
                *_call("square_lt_successor_square", "a"),
                *_call("natural_square_monotone_expanded", "(S a)", "b"), "exact hlt",
            ),
            "Squaring strictly preserves witnessed order on all natural numbers.",
        ),
        spec(
            "square_le_reflect",
            "forall a b. (exists k. k + a * a = b * b) -> exists k. k + a = b",
            ("le_or_lt", "square_lt_strict", "lt_not_le"),
            (
                "intro a", "intro b", "intro hle",
                "specialize le_or_lt a", "specialize le_or_lt b", "cases le_or_lt",
                "exact le_or_lt_left", "exfalso",
                *_call("lt_not_le", "(b * b)", "(a * a)"),
                *_call("square_lt_strict", "b", "a"), "exact le_or_lt_right", "exact hle",
            ),
            "A witnessed weak inequality between natural squares reflects to their roots.",
        ),
        spec(
            "square_lt_reflect",
            "forall a b. (exists k. k + S (a * a) = b * b) -> exists k. k + S a = b",
            ("le_or_lt", "natural_square_monotone_expanded", "lt_not_le"),
            (
                "intro a", "intro b", "intro hlt",
                "specialize le_or_lt b", "specialize le_or_lt a", "cases le_or_lt",
                "exfalso", *_call("lt_not_le", "(a * a)", "(b * b)"), "exact hlt",
                *_call("natural_square_monotone_expanded", "b", "a"), "exact le_or_lt_left",
                "exact le_or_lt_right",
            ),
            "A witnessed strict inequality between natural squares reflects to their roots.",
        ),
        spec(
            "square_eq_injective",
            "forall a b. a * a = b * b -> a = b",
            ("square_le_reflect", "le_refl", "le_antisymm"),
            (
                "intro a", "intro b", "intro heq", *_call("le_antisymm", "a", "b"),
                *_call("square_le_reflect", "a", "b"), "rewrite heq", *_call("le_refl", "(b * b)"),
                *_call("square_le_reflect", "b", "a"), "rewrite heq", *_call("le_refl", "(b * b)"),
            ),
            "Natural square roots are unique, including zero.",
        ),
        spec(
            "square_zero_root",
            "forall a. a * a = 0 -> a = 0",
            ("mul_eq_zero",),
            (
                "intro a", "intro heq", "have hzero : a = 0 \\/ a = 0",
                *_call("mul_eq_zero", "a", "a"), "exact heq", "cases hzero",
                "exact hzero_left", "exact hzero_right",
            ),
            "An actual natural square is zero only when its root is zero.",
        ),
        spec(
            "coprime_square_reduced_factors",
            "forall a b z g A Z. ~(g = 0) -> ~(Z = 0) -> "
            "a = g * A -> z = g * Z -> a * b = z * z -> "
            f"({coprime('a', 'b', tag='csf_reduced_original')}) -> "
            f"({coprime('A', 'Z', tag='csf_reduced_quotients')}) -> "
            "a = A * A /\\ b = Z * Z",
            (
                "mul_left_cancel_nonzero", "mul_right_cancel_nonzero", "mul_assoc",
                "mul_comm", "four_square_product_square",
                "four_square_descent_nonzero_square", "coprime_symm", "coprime_mul_left",
                "gauss_coprime_cancel", "mul_one", "one_mul",
            ),
            (
                "intro a", "intro b", "intro z", "intro g", "intro A", "intro Z",
                "intro hg", "intro hZ", "intro ha", "intro hz", "intro heq", "intro hab", "intro hAZ",
                "have hreduced : A * b = g * (Z * Z)",
                *_call("mul_left_cancel_nonzero", "g", "(A * b)", "(g * (Z * Z))"), "exact hg",
                "trans a * b", "rewrite ha", "symm", "apply mul_assoc",
                "trans z * z", "exact heq", "rewrite hz", "rewrite hz", "trans (g * g) * (Z * Z)",
                "apply four_square_product_square", "apply mul_assoc",
                f"have hZA : {coprime('Z', 'A', tag='csf_reduced_swapped')}",
                *_call("coprime_symm", "A", "Z"), "exact hAZ",
                "have hZsquareA : forall d. (exists x. Z * Z = d * x) -> (exists y. A = d * y) -> d = 1",
                *_call("coprime_mul_left", "Z", "Z", "A"), "exact hZA", "exact hZA",
                "have hbquot : exists k. b = (Z * Z) * k",
                *_call("gauss_coprime_cancel", "(Z * Z)", "A", "b"), "exact hZsquareA",
                "exists g", "trans g * (Z * Z)", "exact hreduced", "apply mul_comm", "cases hbquot",
                "have hscale : A * x = g",
                *_call("mul_right_cancel_nonzero", "(A * x)", "g", "(Z * Z)"),
                "intro hzero", *_call("four_square_descent_nonzero_square", "Z"), "exact hZ", "exact hzero",
                "trans A * b", "rewrite hbquot_witness", "trans A * (x * (Z * Z))",
                "apply mul_assoc", "congr", "refl", "apply mul_comm", "exact hreduced",
                "have haquot : a = x * (A * A)",
                "trans g * A", "exact ha", "rewrite <- hscale",
                "trans (x * A) * A", "congr", "apply mul_comm", "refl", "apply mul_assoc",
                "have hxone : x = 1", "specialize hab x", "apply hab",
                "exists (A * A)", "exact haquot", "exists (Z * Z)",
                "trans (Z * Z) * x", "exact hbquot_witness", "apply mul_comm",
                "split", "rewrite hxone at haquot", "trans 1 * (A * A)", "exact haquot", "apply one_mul",
                "rewrite hxone at hbquot_witness", "trans (Z * Z) * 1", "exact hbquot_witness", "apply mul_one",
            ),
            "For coprime original factors, reducing a factor and the product root by their gcd exposes the two exact square roots.",
        ),
        spec(
            "coprime_square_product_factors",
            "forall a b z. "
            f"({coprime('a', 'b', tag='csf_product')}) -> "
            "a * b = z * z -> exists u v. a = u * u /\\ b = v * v",
            (
                "eq_decidable", "mul_eq_zero", "mul_one",
                "canonical_gcd_exists", "is_gcd_dvd_left", "is_gcd_dvd_right",
                "factor_nonzero_left", "factor_nonzero_right", "is_gcd_quotients_coprime_nonzero",
                "coprime_square_reduced_factors",
            ),
            (
                "intro a", "intro b", "intro z", "intro hcop", "intro heq",
                "specialize eq_decidable z", "specialize eq_decidable 0", "cases eq_decidable",
                "have habzero : a * b = 0", "trans z * z", "exact heq", "rewrite eq_decidable_left", "rewrite eq_decidable_left", "simp",
                "have hzero : a = 0 \\/ b = 0", *_call("mul_eq_zero", "a", "b"), "exact habzero", "cases hzero",
                "have hbone : b = 1", "specialize hcop b", "apply hcop", "exists 0", "rewrite hzero_left", "simp",
                "exists 1", "symm", "apply mul_one", "exists 0", "exists 1", "split", "rewrite hzero_left", "simp",
                "rewrite hbone", "simp",
                "have haone : a = 1", "specialize hcop a", "apply hcop", "exists 1", "symm", "apply mul_one",
                "exists 0", "rewrite hzero_right", "simp", "exists 1", "exists 0", "split", "rewrite haone", "simp", "rewrite hzero_right", "simp",
                "specialize canonical_gcd_exists a", "specialize canonical_gcd_exists z", "cases canonical_gcd_exists",
                "have haquot : exists A. a = x * A", *_call("is_gcd_dvd_left", "x", "a", "z"),
                "exact canonical_gcd_exists_witness", "cases haquot",
                "have hzquot : exists Z. z = x * Z", *_call("is_gcd_dvd_right", "x", "a", "z"),
                "exact canonical_gcd_exists_witness", "cases hzquot",
                "have hgnonzero : ~(x = 0)", "intro hzero", *_call("factor_nonzero_left", "z", "x", "x2"),
                "exact eq_decidable_right", "exact hzquot_witness", "exact hzero",
                "have hZnonzero : ~(x2 = 0)", "intro hzero", *_call("factor_nonzero_right", "z", "x", "x2"),
                "exact eq_decidable_right", "exact hzquot_witness", "exact hzero",
                f"have hquotcop : {coprime('x1', 'x2', tag='csf_product_reduced')}",
                *_call("is_gcd_quotients_coprime_nonzero", "x", "a", "z", "x1", "x2"),
                "exact canonical_gcd_exists_witness", "exact hgnonzero", "exact haquot_witness", "exact hzquot_witness",
                "exists x1", "exists x2", *_call("coprime_square_reduced_factors", "a", "b", "z", "x", "x1", "x2"),
                "exact hgnonzero", "exact hZnonzero", "exact haquot_witness", "exact hzquot_witness", "exact heq", "exact hcop", "exact hquotcop",
            ),
            "If two coprime naturals have square product, each has a constructed natural square root, including both zero boundary cases.",
        ),
        spec(
            "square_divides_square_reduced_root",
            "forall a b g A B q. ~(g = 0) -> a = g * A -> b = g * B -> "
            f"({coprime('A', 'B', tag='csf_divisibility_reduced')}) -> "
            "b * b = (a * a) * q -> exists k. b = a * k",
            ("four_square_descent_square_factor_cancel", "four_square_product_square", "mul_assoc", "coprime_mul_right", "mul_one"),
            (
                "intro a", "intro b", "intro g", "intro A", "intro B", "intro q",
                "intro hg", "intro ha", "intro hb", "intro hcop", "intro heq",
                "have hreduce : B * B = (A * A) * q",
                *_call("four_square_descent_square_factor_cancel", "g", "(B * B)", "((A * A) * q)"), "exact hg",
                "trans b * b", "rewrite hb", "rewrite hb", "symm", "apply four_square_product_square",
                "trans (a * a) * q", "exact heq", "rewrite ha", "rewrite ha",
                "trans ((g * g) * (A * A)) * q", "congr", "apply four_square_product_square", "refl", "apply mul_assoc",
                "have hcop_square : forall d. (exists x. A = d * x) -> (exists y. B * B = d * y) -> d = 1",
                *_call("coprime_mul_right", "A", "B", "B"), "exact hcop", "exact hcop",
                "have hAone : A = 1", "specialize hcop_square A", "apply hcop_square",
                "exists 1", "symm", "apply mul_one", "exists (A * q)",
                "trans (A * A) * q", "exact hreduce", "apply mul_assoc",
                "exists B", "trans g * B", "exact hb", "rewrite ha", "rewrite hAone", "congr", "symm", "apply mul_one", "refl",
            ),
            "A square divisibility equation between reduced coprime cofactors forces the denominator cofactor to be one.",
        ),
        spec(
            "square_divides_square_root",
            "forall a b. (exists q. b * b = (a * a) * q) -> exists k. b = a * k",
            (
                "eq_decidable", "mul_zero_left", "square_zero_root", "canonical_gcd_exists",
                "is_gcd_dvd_left", "is_gcd_dvd_right", "factor_nonzero_left",
                "is_gcd_quotients_coprime_nonzero", "square_divides_square_reduced_root",
            ),
            (
                "intro a", "intro b", "intro hdiv", "cases hdiv",
                "specialize eq_decidable a", "specialize eq_decidable 0", "cases eq_decidable",
                "have hbzero : b = 0", *_call("square_zero_root", "b"),
                "trans (a * a) * x", "exact hdiv_witness", "rewrite eq_decidable_left", "simp [mul_zero_left]",
                "exists 0", "rewrite hbzero", "simp",
                "specialize canonical_gcd_exists a", "specialize canonical_gcd_exists b", "cases canonical_gcd_exists",
                "have haquot : exists A. a = x1 * A", *_call("is_gcd_dvd_left", "x1", "a", "b"),
                "exact canonical_gcd_exists_witness", "cases haquot",
                "have hbquot : exists B. b = x1 * B", *_call("is_gcd_dvd_right", "x1", "a", "b"),
                "exact canonical_gcd_exists_witness", "cases hbquot",
                "have hgnonzero : ~(x1 = 0)", "intro hzero", *_call("factor_nonzero_left", "a", "x1", "x2"),
                "exact eq_decidable_right", "exact haquot_witness", "exact hzero",
                f"have hquotcop : {coprime('x2', 'x3', tag='csf_divisibility_quotients')}",
                *_call("is_gcd_quotients_coprime_nonzero", "x1", "a", "b", "x2", "x3"),
                "exact canonical_gcd_exists_witness", "exact hgnonzero", "exact haquot_witness", "exact hbquot_witness",
                *_call("square_divides_square_reduced_root", "a", "b", "x1", "x2", "x3", "x"),
                "exact hgnonzero", "exact haquot_witness", "exact hbquot_witness", "exact hquotcop", "exact hdiv_witness",
            ),
            "For all naturals, if a squared divisor divides a squared value, the unsquared divisor divides the unsquared value.",
        ),
    )


__all__ = ["make_coprime_square_factor_candidate_theorems"]
