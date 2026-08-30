"""Integer-only power-envelope candidates for Bertrand's postulate.

The B6 route does not reify a real inequality.  It reduces the target to a
six-step induction on the integer square-root value.  This isolated module
starts that route with the missing multiplicative-base law for the existing
relational ``Pow`` graph.  Later rows in this same candidate surface will use
it to certify the six-step guard

    (s + 7)^12 <= 4^(s + 5)

without logarithms, division in the metalanguage, or evaluated host powers.
All ``Pow`` occurrences below are expanded before parsing.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation
from .power_algebra_theorems import _power_terms


def make_bertrand_integer_envelope_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build reusable power algebra required by the six-step envelope."""

    left_power = power_relation("a", "e", "x", tag="bie_mul_left")
    right_power = power_relation("b", "e", "y", tag="bie_mul_right")
    product_power = _power_terms("a * b", "e", "z", tag="bie_mul_product")
    left_prefix = power_relation("a", "e", "r", tag="bie_mul_left_prefix")
    right_prefix = power_relation("b", "e", "r", tag="bie_mul_right_prefix")
    product_prefix = _power_terms(
        "a * b", "e", "r", tag="bie_mul_product_prefix"
    )

    two_two_power = _power_terms("2", "2", "x", tag="bie_two_two")
    two_twelve_power = _power_terms("2", "12", "x", tag="bie_two_twelve")
    four_six_power = _power_terms("4", "6", "y", tag="bie_four_six")

    guard_now = _power_terms("s + 7", "12", "x", tag="bie_guard_now")
    guard_bound_now = _power_terms(
        "4", "s + 5", "y", tag="bie_guard_bound_now"
    )
    guard_next = _power_terms("s + 13", "12", "z", tag="bie_guard_next")
    guard_bound_next = _power_terms(
        "4", "s + 11", "w", tag="bie_guard_bound_next"
    )
    doubled_guard = _power_terms(
        "2 * (s + 7)", "12", "t", tag="bie_guard_doubled"
    )
    two_twelve_u = _power_terms("2", "12", "u", tag="bie_guard_two")
    four_six_v = _power_terms("4", "6", "v", tag="bie_guard_four")

    return (
        spec(
            "two_mul_eq_add_self",
            "forall n. 2 * n = n + n",
            ("mul_comm", "mul_one"),
            (
                "intro n",
                "trans n * 2",
                "apply mul_comm",
                "rewrite PA6",
                "specialize mul_one n",
                "rewrite mul_one",
                "refl",
            ),
            "Left multiplication by two is explicit doubling.",
        ),
        spec(
            "pow_mul_base",
            "forall a b e x y z. "
            f"({left_power}) -> ({right_power}) -> ({product_power}) -> "
            "z = x * y",
            (
                "pow_zero",
                "pow_successor_decompose",
                "mul_one",
                "mul_assoc",
                "mul_comm",
            ),
            (
                "intro a",
                "intro b",
                "intro e",
                "induction e",
                "intro x",
                "intro y",
                "intro z",
                "intro hx",
                "intro hy",
                "intro hz",
                "have hx1 : x = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero x",
                "apply pow_zero",
                "refl",
                "exact hx",
                "have hy1 : y = 1",
                "specialize pow_zero b",
                "specialize pow_zero 0",
                "specialize pow_zero y",
                "apply pow_zero",
                "refl",
                "exact hy",
                "have hz1 : z = 1",
                "specialize pow_zero (a * b)",
                "specialize pow_zero 0",
                "specialize pow_zero z",
                "apply pow_zero",
                "refl",
                "exact hz",
                "rewrite hz1",
                "rewrite hx1",
                "rewrite hy1",
                "symm",
                "specialize mul_one 1",
                "exact mul_one",
                "intro x",
                "intro y",
                "intro z",
                "intro hx",
                "intro hy",
                "intro hz",
                f"have hxstep : exists r. ({left_prefix}) /\\ x = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "refl",
                "exact hx",
                "cases hxstep",
                "cases hxstep_witness",
                f"have hystep : exists r. ({right_prefix}) /\\ y = r * b",
                "specialize pow_successor_decompose b",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hystep",
                "cases hystep_witness",
                f"have hzstep : exists r. ({product_prefix}) /\\ z = r * (a * b)",
                "specialize pow_successor_decompose (a * b)",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose z",
                "apply pow_successor_decompose",
                "refl",
                "exact hz",
                "cases hzstep",
                "cases hzstep_witness",
                "have hprefix : x3 = x1 * x2",
                "specialize IH x1",
                "specialize IH x2",
                "specialize IH x3",
                "apply IH",
                "exact hxstep_witness_left",
                "exact hystep_witness_left",
                "exact hzstep_witness_left",
                "trans x3 * (a * b)",
                "exact hzstep_witness_right",
                "trans (x1 * x2) * (a * b)",
                "congr",
                "exact hprefix",
                "refl",
                "trans x1 * (x2 * (a * b))",
                "apply mul_assoc",
                "trans x1 * ((x2 * a) * b)",
                "congr",
                "refl",
                "symm",
                "apply mul_assoc",
                "trans x1 * ((a * x2) * b)",
                "congr",
                "refl",
                "congr",
                "apply mul_comm",
                "refl",
                "trans x1 * (a * (x2 * b))",
                "congr",
                "refl",
                "apply mul_assoc",
                "trans (x1 * a) * (x2 * b)",
                "symm",
                "apply mul_assoc",
                "rewrite <- hxstep_witness_right",
                "rewrite <- hystep_witness_right",
                "refl",
            ),
            "A relational power of a product is the product of the powers.",
        ),
        spec(
            "pow_two_base_two_value_four",
            f"forall x. ({two_two_power}) -> x = 4",
            ("pow_two",),
            (
                "intro x",
                "intro hx",
                "have hxx : x = 2 * 2",
                "specialize pow_two 2",
                "specialize pow_two 2",
                "specialize pow_two x",
                "apply pow_two",
                "refl",
                "exact hx",
                "trans 2 * 2",
                "exact hxx",
                "norm_num",
            ),
            "The relational square of two has the concrete value four.",
        ),
        spec(
            "pow_two_twelve_eq_pow_four_six",
            f"forall x y. ({two_twelve_power}) -> ({four_six_power}) -> x = y",
            (
                "pow_exists",
                "pow_two_base_two_value_four",
                "pow_mul_exp",
            ),
            (
                "intro x",
                "intro y",
                "intro hx",
                "intro hy",
                "have htwo_exists : exists z. "
                f"({_power_terms('2', '2', 'z', tag='bie_two_two_exists')})",
                "specialize pow_exists 2",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases htwo_exists",
                "have hvalue : x1 = 4",
                "specialize pow_two_base_two_value_four x1",
                "apply pow_two_base_two_value_four",
                "exact htwo_exists_witness",
                "have htwo_four : "
                f"({_power_terms('2', '2', '4', tag='bie_two_two_exists')})",
                "rewrite <- hvalue",
                "rewrite <- hvalue",
                "exact htwo_exists_witness",
                "have hyx : y = x",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp 6",
                "specialize pow_mul_exp 12",
                "specialize pow_mul_exp 4",
                "specialize pow_mul_exp y",
                "specialize pow_mul_exp x",
                "apply pow_mul_exp",
                "norm_num",
                "exact htwo_four",
                "exact hy",
                "exact hx",
                "symm",
                "exact hyx",
            ),
            "The exact identity 2^12 = 4^6 in the relational power graph.",
        ),
        spec(
            "bertrand_guard_six_step_transport",
            "forall s x y z w. "
            f"({guard_now}) -> ({guard_bound_now}) -> "
            f"(exists k. k + x = y) -> ({guard_next}) -> "
            f"({guard_bound_next}) -> exists k. k + z = w",
            (
                "pow_exists",
                "pow_base_monotone",
                "pow_mul_base",
                "pow_two_twelve_eq_pow_four_six",
                "pow_add",
                "mul_le_mul",
                "le_refl",
                "le_trans",
                "add_assoc",
                "add_comm",
                "two_mul_eq_add_self",
            ),
            (
                "intro s",
                "intro x",
                "intro y",
                "intro z",
                "intro w",
                "intro hx",
                "intro hy",
                "intro hxy",
                "intro hz",
                "intro hw",
                "have hbase : exists k. k + (s + 13) = 2 * (s + 7)",
                "exists S s",
                "simp [two_mul_eq_add_self, add_assoc, add_comm]",
                f"have hdouble : exists t. ({doubled_guard})",
                "specialize pow_exists (2 * (s + 7))",
                "specialize pow_exists 12",
                "exact pow_exists",
                "cases hdouble",
                "have hzt : exists k. k + z = x1",
                "specialize pow_base_monotone (s + 13)",
                "specialize pow_base_monotone (2 * (s + 7))",
                "specialize pow_base_monotone 12",
                "specialize pow_base_monotone z",
                "specialize pow_base_monotone x1",
                "apply pow_base_monotone",
                "exact hbase",
                "exact hz",
                "exact hdouble_witness",
                f"have htwo : exists u. ({two_twelve_u})",
                "specialize pow_exists 2",
                "specialize pow_exists 12",
                "exact pow_exists",
                "cases htwo",
                "have hfactor : x1 = x2 * x",
                "specialize pow_mul_base 2",
                "specialize pow_mul_base (s + 7)",
                "specialize pow_mul_base 12",
                "specialize pow_mul_base x2",
                "specialize pow_mul_base x",
                "specialize pow_mul_base x1",
                "apply pow_mul_base",
                "exact htwo_witness",
                "exact hx",
                "exact hdouble_witness",
                f"have hsix : exists v. ({four_six_v})",
                "specialize pow_exists 4",
                "specialize pow_exists 6",
                "exact pow_exists",
                "cases hsix",
                "have htwosix : x2 = x3",
                "specialize pow_two_twelve_eq_pow_four_six x2",
                "specialize pow_two_twelve_eq_pow_four_six x3",
                "apply pow_two_twelve_eq_pow_four_six",
                "exact htwo_witness",
                "exact hsix_witness",
                "have hsum : s + 11 = 6 + (s + 5)",
                "trans s + (6 + 5)",
                "congr",
                "refl",
                "norm_num",
                "trans (s + 6) + 5",
                "symm",
                "apply add_assoc",
                "trans (6 + s) + 5",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "have hboundfactor : w = x3 * y",
                "specialize pow_add 4",
                "specialize pow_add 6",
                "specialize pow_add (s + 5)",
                "specialize pow_add (s + 11)",
                "specialize pow_add x3",
                "specialize pow_add y",
                "specialize pow_add w",
                "apply pow_add",
                "exact hsum",
                "exact hsix_witness",
                "exact hy",
                "exact hw",
                "have hproducts : exists k. k + (x2 * x) = x3 * y",
                "rewrite htwosix",
                "specialize mul_le_mul x3",
                "specialize mul_le_mul x3",
                "specialize mul_le_mul x",
                "specialize mul_le_mul y",
                "apply mul_le_mul",
                "specialize le_refl x3",
                "exact le_refl",
                "exact hxy",
                "specialize le_trans z",
                "specialize le_trans x1",
                "specialize le_trans w",
                "apply le_trans",
                "exact hzt",
                "rewrite hfactor",
                "rewrite hboundfactor",
                "exact hproducts",
            ),
            "The guard (s+7)^12 <= 4^(s+5) propagates from s to s+6.",
        ),
    )


__all__ = ["make_bertrand_integer_envelope_candidate_theorems"]
