"""Constructive power-product growth rows for the Bertrand B6 route.

This isolated candidate layer converts the all-root H/J envelope into the two
multiplicative comparisons needed by the final natural-number inequality.
The first row uses the strict upper half of ``FloorSqrt(2*n,s)`` to compare
``(2*n)^s`` with a power of ``(s+1)^2``.  The second row folds the exponents
``q`` and ``e`` and transports their fourth-power product along ``q+e <= n``.

``PowTotal``, ``FloorSqrt``, ``Pow``, and ``Le`` are authoring notation only.
Every occurrence is expanded hygienically into the existing first-order
Peano language before a theorem specification is returned.  The proofs use
only supplied relational witnesses and constructive power algebra.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import witness_le
from .power_algebra_theorems import _power_terms


def make_bertrand_b6_growth_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the two frozen B6 power-product growth candidates."""

    floor_total = power_total_relation(tag="b6_floor_product")
    floor_root = floor_sqrt_relation(
        "2 * n", "s", tag="b6_floor_product_root"
    )
    floor_power = _power_terms(
        "2 * n", "s", "A", tag="b6_floor_product_power"
    )
    floor_envelope = _power_terms(
        "s + 1",
        "2 * s + 2",
        "H",
        tag="b6_floor_product_envelope",
    )
    floor_result = witness_le(
        "n * A", "H", tag="b6_floor_product_result"
    )

    floor_square_power = _power_terms(
        "s + 1", "2", "v", tag="b6_floor_product_square"
    )
    floor_square_outer = _power_terms(
        "x", "s", "u", tag="b6_floor_product_square_outer"
    )
    floor_square_flat = _power_terms(
        "s + 1", "2 * s", "z", tag="b6_floor_product_square_flat"
    )
    floor_base_order = witness_le(
        "2 * n", "x", tag="b6_floor_product_base_order"
    )
    floor_power_order = witness_le(
        "A", "x1", tag="b6_floor_product_power_order"
    )
    floor_n_double_order = witness_le(
        "n", "2 * n", tag="b6_floor_product_n_double"
    )
    floor_n_square_order = witness_le(
        "n", "x", tag="b6_floor_product_n_square"
    )
    floor_product_order = witness_le(
        "n * A", "x * x2", tag="b6_floor_product_intermediate"
    )

    sum_total = power_total_relation(tag="b6_four_product")
    sum_order = witness_le("q + e", "n", tag="b6_four_product_sum")
    sum_q_power = _power_terms(
        "4", "q", "B", tag="b6_four_product_q"
    )
    sum_e_power = _power_terms(
        "4", "e", "U", tag="b6_four_product_e"
    )
    sum_n_power = _power_terms(
        "4", "n", "F", tag="b6_four_product_n"
    )
    sum_result = witness_le(
        "U * B", "F", tag="b6_four_product_result"
    )
    sum_combined_power = _power_terms(
        "4", "q + e", "x", tag="b6_four_product_combined"
    )
    sum_combined_order = witness_le(
        "x", "F", tag="b6_four_product_combined_order"
    )
    four_at_least_one = witness_le(
        "1", "4", tag="b6_four_product_base_positive"
    )

    return (
        spec(
            "bertrand_floor_power_product_le_h_from_total",
            "forall n s A H. "
            f"({floor_total}) -> ({floor_root}) -> ({floor_power}) -> "
            f"({floor_envelope}) -> ({floor_result})",
            (
                "floor_sqrt_strict_upper_bound",
                "lt_to_le",
                "le_add_right",
                "two_mul_eq_add_self",
                "le_trans",
                "pow_two",
                "pow_base_monotone",
                "pow_mul_exp_from_total",
                "pow_add",
                "mul_le_mul",
                "mul_comm",
            ),
            (
                "intro n",
                "intro s",
                "intro A",
                "intro H",
                "intro htotal",
                "intro hfloor",
                "intro hA",
                "intro hH",
                "have hstrict : exists k. k + S (2 * n) = S s * S s",
                "specialize floor_sqrt_strict_upper_bound (2 * n)",
                "specialize floor_sqrt_strict_upper_bound s",
                "apply floor_sqrt_strict_upper_bound",
                "exact hfloor",
                "have hweak : exists k. k + 2 * n = S s * S s",
                "specialize lt_to_le (2 * n)",
                "specialize lt_to_le (S s * S s)",
                "apply lt_to_le",
                "exact hstrict",
                "have hsucc : s + 1 = S s",
                "rewrite PA4",
                "congr",
                "apply PA3",
                f"have hv_exists : exists v. ({floor_square_power})",
                "specialize htotal (s + 1)",
                "specialize htotal 2",
                "exact htotal",
                "cases hv_exists",
                "have hv_square : x = (s + 1) * (s + 1)",
                "specialize pow_two (s + 1)",
                "specialize pow_two 2",
                "specialize pow_two x",
                "apply pow_two",
                "refl",
                "exact hv_exists_witness",
                f"have hbase : {floor_base_order}",
                "rewrite hv_square",
                "rewrite hsucc",
                "rewrite hsucc",
                "exact hweak",
                f"have hu_exists : exists u. ({floor_square_outer})",
                "specialize htotal x",
                "specialize htotal s",
                "exact htotal",
                "cases hu_exists",
                f"have hpower : {floor_power_order}",
                "specialize pow_base_monotone (2 * n)",
                "specialize pow_base_monotone x",
                "specialize pow_base_monotone s",
                "specialize pow_base_monotone A",
                "specialize pow_base_monotone x1",
                "apply pow_base_monotone",
                "exact hbase",
                "exact hA",
                "exact hu_exists_witness",
                f"have hz_exists : exists z. ({floor_square_flat})",
                "specialize htotal (s + 1)",
                "specialize htotal (2 * s)",
                "exact htotal",
                "cases hz_exists",
                "have huz : x1 = x2",
                "specialize pow_mul_exp_from_total (s + 1)",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total s",
                "specialize pow_mul_exp_from_total (2 * s)",
                "specialize pow_mul_exp_from_total x",
                "specialize pow_mul_exp_from_total x1",
                "specialize pow_mul_exp_from_total x2",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "refl",
                "exact hv_exists_witness",
                "exact hu_exists_witness",
                "exact hz_exists_witness",
                "have hfactor : H = x2 * x",
                "specialize pow_add (s + 1)",
                "specialize pow_add (2 * s)",
                "specialize pow_add 2",
                "specialize pow_add (2 * s + 2)",
                "specialize pow_add x2",
                "specialize pow_add x",
                "specialize pow_add H",
                "apply pow_add",
                "refl",
                "exact hz_exists_witness",
                "exact hv_exists_witness",
                "exact hH",
                "have hn_double_sum : exists k. k + n = n + n",
                "specialize le_add_right n",
                "specialize le_add_right n",
                "exact le_add_right",
                "have hdouble : 2 * n = n + n",
                "specialize two_mul_eq_add_self n",
                "exact two_mul_eq_add_self",
                f"have hn_double : {floor_n_double_order}",
                "rewrite hdouble",
                "exact hn_double_sum",
                f"have hn_square : {floor_n_square_order}",
                "specialize le_trans n",
                "specialize le_trans (2 * n)",
                "specialize le_trans x",
                "apply le_trans",
                "exact hn_double",
                "exact hbase",
                "have hAz : exists k. k + A = x2",
                "rewrite <- huz",
                "exact hpower",
                f"have hproduct : {floor_product_order}",
                "specialize mul_le_mul n",
                "specialize mul_le_mul x",
                "specialize mul_le_mul A",
                "specialize mul_le_mul x2",
                "apply mul_le_mul",
                "exact hn_square",
                "exact hAz",
                "have hcomm : x * x2 = x2 * x",
                "specialize mul_comm x",
                "specialize mul_comm x2",
                "exact mul_comm",
                "rewrite hcomm at hproduct",
                "rewrite <- hfactor at hproduct",
                "exact hproduct",
            ),
            "The floor-root power product is bounded by the H envelope using one supplied power-totality premise.",
        ),
        spec(
            "bertrand_four_power_product_le_of_sum_from_total",
            "forall q e n B U F. "
            f"({sum_total}) -> ({sum_order}) -> ({sum_q_power}) -> "
            f"({sum_e_power}) -> ({sum_n_power}) -> ({sum_result})",
            (
                "pow_add",
                "pow_exponent_monotone_from_total",
                "mul_comm",
            ),
            (
                "intro q",
                "intro e",
                "intro n",
                "intro B",
                "intro U",
                "intro F",
                "intro htotal",
                "intro hsum",
                "intro hB",
                "intro hU",
                "intro hF",
                f"have hx_exists : exists x. ({sum_combined_power})",
                "specialize htotal 4",
                "specialize htotal (q + e)",
                "exact htotal",
                "cases hx_exists",
                "have hfactor : x = B * U",
                "specialize pow_add 4",
                "specialize pow_add q",
                "specialize pow_add e",
                "specialize pow_add (q + e)",
                "specialize pow_add B",
                "specialize pow_add U",
                "specialize pow_add x",
                "apply pow_add",
                "refl",
                "exact hB",
                "exact hU",
                "exact hx_exists_witness",
                f"have hfour : {four_at_least_one}",
                "exists 3",
                "norm_num",
                f"have hcombined : {sum_combined_order}",
                "specialize pow_exponent_monotone_from_total 4",
                "specialize pow_exponent_monotone_from_total (q + e)",
                "specialize pow_exponent_monotone_from_total n",
                "specialize pow_exponent_monotone_from_total x",
                "specialize pow_exponent_monotone_from_total F",
                "apply pow_exponent_monotone_from_total",
                "exact htotal",
                "exact hfour",
                "exact hsum",
                "exact hx_exists_witness",
                "exact hF",
                "rewrite hfactor at hcombined",
                "have hcomm : U * B = B * U",
                "specialize mul_comm U",
                "specialize mul_comm B",
                "exact mul_comm",
                "rewrite hcomm",
                "exact hcombined",
            ),
            "Fourth-power factors are bounded by the power at every larger exponent sum.",
        ),
    )


__all__ = ["make_bertrand_b6_growth_candidate_theorems"]
