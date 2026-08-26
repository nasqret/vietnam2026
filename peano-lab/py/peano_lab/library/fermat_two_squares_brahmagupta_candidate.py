"""Constructive Brahmagupta--Fibonacci multiplication of two-square norms.

Natural coordinates cannot directly express ``a*d-b*c``.  An existing
constructive absolute-difference theorem supplies its magnitude and a genuine
choice of sign.  The polynomial identity is proved by small first-order
commutative-semiring certificates, without a ring tactic, subtraction,
excluded middle, registry enrollment, or release-evidence changes.
"""

from __future__ import annotations

from typing import Any, Callable


def make_fermat_two_squares_brahmagupta_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the complete, explicitly witnessed two-square product identity."""

    product_norm = "(a * a + b * b) * (c * c + d * d)"
    first_coordinate = "a * c + b * d"
    represented_norm = f"({first_coordinate}) * ({first_coordinate}) + m * m"
    expanded_norm = (
        "((a * c) * (a * c) + (b * d) * (b * d)) + "
        "((a * d) * (a * d) + (b * c) * (b * c))"
    )
    difference = "((a * d = b * c + m) \\/ (b * c = a * d + m))"

    return (
        spec(
            "two_square_add_left_comm",
            "forall x y z. x + (y + z) = y + (x + z)",
            ("add_assoc", "add_comm"),
            (
                "intro x",
                "intro y",
                "intro z",
                "trans (x + y) + z",
                "symm",
                "apply add_assoc",
                "trans (y + x) + z",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "Associativity and commutativity swap the first two entries of a right-associated natural sum.",
        ),
        spec(
            "two_square_mul_left_comm",
            "forall x y z. x * (y * z) = y * (x * z)",
            ("mul_assoc", "mul_comm"),
            (
                "intro x",
                "intro y",
                "intro z",
                "trans (x * y) * z",
                "symm",
                "apply mul_assoc",
                "trans (y * x) * z",
                "congr",
                "apply mul_comm",
                "refl",
                "apply mul_assoc",
            ),
            "Associativity and commutativity swap the first two factors of a right-associated natural product.",
        ),
        spec(
            "two_square_cross_products_equal",
            "forall a b c d. (a * c) * (b * d) = (a * d) * (b * c)",
            ("mul_assoc", "mul_comm", "two_square_mul_left_comm"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "simp [mul_assoc, mul_comm, two_square_mul_left_comm]",
            ),
            "The two cross products in the Brahmagupta identity are exactly equal.",
        ),
        spec(
            "two_square_product_norm_expanded",
            f"forall a b c d. {product_norm} = {expanded_norm}",
            (
                "add_assoc",
                "add_comm",
                "two_square_add_left_comm",
                "mul_assoc",
                "mul_comm",
                "two_square_mul_left_comm",
                "mul_add",
                "add_mul",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "simp [mul_add, add_mul, add_assoc, add_comm, "
                "two_square_add_left_comm, mul_assoc, mul_comm, "
                "two_square_mul_left_comm]",
            ),
            "The product of two natural two-square norms expands into its four squared coordinate products.",
        ),
        spec(
            "two_square_balanced_difference_identity",
            "forall A B C D m. A * B = C * D -> C = D + m -> "
            "(A * A + B * B) + (C * C + D * D) = "
            "(A + B) * (A + B) + m * m",
            (
                "add_assoc",
                "add_comm",
                "mul_comm",
                "mul_add",
                "add_mul",
                "two_square_add_left_comm",
            ),
            (
                "intro A",
                "intro B",
                "intro C",
                "intro D",
                "intro m",
                "intro hcross",
                "intro hdifference",
                "rewrite hdifference at hcross",
                "have hproduct : B * A = D * D + m * D",
                "trans A * B",
                "apply mul_comm",
                "trans (D + m) * D",
                "exact hcross",
                "apply add_mul",
                "rewrite hdifference",
                "rewrite hdifference",
                "simp [mul_add, add_mul, add_assoc, add_comm, "
                "two_square_add_left_comm, mul_comm, hproduct]",
            ),
            "Equal cross products and a witnessed natural difference imply the exact balanced sum-of-two-squares identity.",
        ),
        spec(
            "two_square_product_difference_forward",
            f"forall a b c d m. a * d = b * c + m -> "
            f"{product_norm} = {represented_norm}",
            (
                "two_square_product_norm_expanded",
                "two_square_cross_products_equal",
                "two_square_balanced_difference_identity",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro m",
                "intro hdifference",
                "specialize two_square_product_norm_expanded a",
                "specialize two_square_product_norm_expanded b",
                "specialize two_square_product_norm_expanded c",
                "specialize two_square_product_norm_expanded d",
                "rewrite two_square_product_norm_expanded",
                "specialize two_square_balanced_difference_identity (a * c)",
                "specialize two_square_balanced_difference_identity (b * d)",
                "specialize two_square_balanced_difference_identity (a * d)",
                "specialize two_square_balanced_difference_identity (b * c)",
                "specialize two_square_balanced_difference_identity m",
                "apply two_square_balanced_difference_identity",
                "specialize two_square_cross_products_equal a",
                "specialize two_square_cross_products_equal b",
                "specialize two_square_cross_products_equal c",
                "specialize two_square_cross_products_equal d",
                "exact two_square_cross_products_equal",
                "exact hdifference",
            ),
            "The nonnegative a*d-b*c branch gives an explicit natural Brahmagupta representation.",
        ),
        spec(
            "two_square_product_difference_reverse",
            f"forall a b c d m. b * c = a * d + m -> "
            f"{product_norm} = {represented_norm}",
            (
                "two_square_product_norm_expanded",
                "two_square_cross_products_equal",
                "two_square_balanced_difference_identity",
                "add_comm",
                "mul_comm",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro m",
                "intro hdifference",
                "specialize two_square_product_norm_expanded a",
                "specialize two_square_product_norm_expanded b",
                "specialize two_square_product_norm_expanded c",
                "specialize two_square_product_norm_expanded d",
                "rewrite two_square_product_norm_expanded",
                "have hswap : (a * d) * (a * d) + (b * c) * (b * c) = "
                "(b * c) * (b * c) + (a * d) * (a * d)",
                "apply add_comm",
                "rewrite hswap",
                "specialize two_square_cross_products_equal a",
                "specialize two_square_cross_products_equal b",
                "specialize two_square_cross_products_equal c",
                "specialize two_square_cross_products_equal d",
                "have hcross : (a * c) * (b * d) = (b * c) * (a * d)",
                "trans (a * d) * (b * c)",
                "exact two_square_cross_products_equal",
                "apply mul_comm",
                "specialize two_square_balanced_difference_identity (a * c)",
                "specialize two_square_balanced_difference_identity (b * d)",
                "specialize two_square_balanced_difference_identity (b * c)",
                "specialize two_square_balanced_difference_identity (a * d)",
                "specialize two_square_balanced_difference_identity m",
                "apply two_square_balanced_difference_identity",
                "exact hcross",
                "exact hdifference",
            ),
            "The nonnegative b*c-a*d branch gives the same natural Brahmagupta representation.",
        ),
        spec(
            "two_square_product_explicit_witness",
            f"forall a b c d. exists m. (({difference}) /\\ "
            f"({product_norm} = {represented_norm}))",
            (
                "natural_absolute_difference_exists",
                "two_square_product_difference_forward",
                "two_square_product_difference_reverse",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "specialize natural_absolute_difference_exists (a * d)",
                "specialize natural_absolute_difference_exists (b * c)",
                "cases natural_absolute_difference_exists",
                "exists x",
                "split",
                "exact natural_absolute_difference_exists_witness",
                "cases natural_absolute_difference_exists_witness",
                "specialize two_square_product_difference_forward a",
                "specialize two_square_product_difference_forward b",
                "specialize two_square_product_difference_forward c",
                "specialize two_square_product_difference_forward d",
                "specialize two_square_product_difference_forward x",
                "apply two_square_product_difference_forward",
                "exact natural_absolute_difference_exists_witness_left",
                "specialize two_square_product_difference_reverse a",
                "specialize two_square_product_difference_reverse b",
                "specialize two_square_product_difference_reverse c",
                "specialize two_square_product_difference_reverse d",
                "specialize two_square_product_difference_reverse x",
                "apply two_square_product_difference_reverse",
                "exact natural_absolute_difference_exists_witness_right",
            ),
            "The product of two two-square norms has the explicit coordinates a*c+b*d and a constructively witnessed absolute difference |a*d-b*c|.",
        ),
        spec(
            "two_square_product_is_two_square",
            f"forall a b c d. exists x y. {product_norm} = x * x + y * y",
            ("two_square_product_explicit_witness",),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "specialize two_square_product_explicit_witness a",
                "specialize two_square_product_explicit_witness b",
                "specialize two_square_product_explicit_witness c",
                "specialize two_square_product_explicit_witness d",
                "cases two_square_product_explicit_witness",
                "cases two_square_product_explicit_witness_witness",
                "exists a * c + b * d",
                "exists x",
                "exact two_square_product_explicit_witness_witness_right",
            ),
            "The complete constructive Brahmagupta--Fibonacci identity supplies actual natural coordinates for every product of two-square norms.",
        ),
        spec(
            "two_square_representations_closed_under_multiplication",
            "forall m n. (exists a b. m = a * a + b * b) -> "
            "(exists c d. n = c * c + d * d) -> "
            "exists x y. m * n = x * x + y * y",
            ("two_square_product_is_two_square",),
            (
                "intro m",
                "intro n",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hfirst_witness",
                "cases hsecond",
                "cases hsecond_witness",
                "rewrite hfirst_witness_witness",
                "rewrite hsecond_witness_witness",
                "specialize two_square_product_is_two_square x",
                "specialize two_square_product_is_two_square x1",
                "specialize two_square_product_is_two_square x2",
                "specialize two_square_product_is_two_square x3",
                "exact two_square_product_is_two_square",
            ),
            "Two explicitly represented sums of two natural squares multiply to another explicitly represented sum of two squares.",
        ),
    )


__all__ = ["make_fermat_two_squares_brahmagupta_candidate_theorems"]
