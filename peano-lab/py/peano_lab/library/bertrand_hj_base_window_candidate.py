"""Capacity-safe uniform H/J base window for Bertrand B6.

For every root ``64 <= s <= 69`` this isolated candidate tranche proves the
two exponential bounds used by the six-step Bertrand invariant::

    (s + 1)^(2*s + 2) <= 4^ceil(s*s/6)
    (s + 7)^12        <= 4^(s + 5)

All powers and order relations are conservative authoring expansions.  The
proof receives the already-proved power-totality proposition as an ordinary
antecedent and uses the capacity-normalized power laws.  In particular, it
does not depend on the old 467,653-node guard or either large exact-identity
wrapper.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import ceil_div_six_relation
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import witness_le
from .power_algebra_theorems import _power_terms


def make_bertrand_hj_base_window_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build a compact common-power bridge and the uniform H/J bases."""

    common_total = power_total_relation(tag="hj_common")
    common_left = _power_terms(
        "128", "d", "x", tag="hj_common_left"
    )
    common_right = _power_terms(
        "4", "k", "y", tag="hj_common_right"
    )
    common_power = _power_terms(
        "2", "14 * m", "z", tag="hj_common_power"
    )
    seed_two = _power_terms("2", "2", "4", tag="hj_seed_two")
    seed_seven = _power_terms("2", "7", "128", tag="hj_seed_seven")

    base_total = power_total_relation(tag="hj_base")
    base_lower = witness_le("64", "s", tag="hj_base_lower")
    base_upper = witness_le("s", "69", tag="hj_base_upper")
    base_ceiling = ceil_div_six_relation(
        "s * s", "e", tag="hj_base_ceiling"
    )
    base_h = _power_terms(
        "s + 1", "2 * s + 2", "h", tag="hj_base_h"
    )
    base_h_bound = _power_terms("4", "e", "u", tag="hj_base_h_bound")
    base_j = _power_terms("s + 7", "12", "j", tag="hj_base_j")
    base_j_bound = _power_terms(
        "4", "s + 5", "g", tag="hj_base_j_bound"
    )
    base_h_result = witness_le("h", "u", tag="hj_base_h_result")
    base_j_result = witness_le("j", "g", tag="hj_base_j_result")

    h_upper = _power_terms(
        "128", "2 * s + 2", "hhx", tag="hj_h_upper"
    )
    h_bridge = _power_terms(
        "4", "7 * (s + 1)", "hhy", tag="hj_h_bridge"
    )
    j_upper = _power_terms("128", "12", "jjx", tag="hj_j_upper")
    j_bridge = _power_terms("4", "42", "jjy", tag="hj_j_bridge")

    return (
        spec(
            "pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
            "forall m d k x y. "
            f"({common_total}) -> d = 2 * m -> k = 7 * m -> "
            f"({common_left}) -> ({common_right}) -> x = y",
            (
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "mul_assoc",
            ),
            (
                "intro m",
                "intro d",
                "intro k",
                "intro x",
                "intro y",
                "intro htotal",
                "intro hd",
                "intro hk",
                "intro hx",
                "intro hy",
                f"have hseeds : ({seed_two}) /\\ ({seed_seven})",
                "apply pow_two_seed_bundle_from_total",
                "exact htotal",
                "cases hseeds",
                f"have hcommon : exists z. ({common_power})",
                "specialize htotal 2",
                "specialize htotal (14 * m)",
                "exact htotal",
                "cases hcommon",
                "have hleft_exponent : 14 * m = 7 * d",
                "rewrite hd",
                "trans (7 * 2) * m",
                "congr",
                "norm_num",
                "refl",
                "apply mul_assoc",
                "have hleft : x = x1",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 7",
                "specialize pow_mul_exp_from_total d",
                "specialize pow_mul_exp_from_total (14 * m)",
                "specialize pow_mul_exp_from_total 128",
                "specialize pow_mul_exp_from_total x",
                "specialize pow_mul_exp_from_total x1",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "exact hleft_exponent",
                "exact hseeds_right",
                "exact hx",
                "exact hcommon_witness",
                "have hright_exponent : 14 * m = 2 * k",
                "rewrite hk",
                "trans (2 * 7) * m",
                "congr",
                "norm_num",
                "refl",
                "apply mul_assoc",
                "have hright : y = x1",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total k",
                "specialize pow_mul_exp_from_total (14 * m)",
                "specialize pow_mul_exp_from_total 4",
                "specialize pow_mul_exp_from_total y",
                "specialize pow_mul_exp_from_total x1",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "exact hright_exponent",
                "exact hseeds_left",
                "exact hy",
                "exact hcommon_witness",
                "trans x1",
                "exact hleft",
                "symm",
                "exact hright",
            ),
            "128^(2*m) and 4^(7*m) meet at the shared power 2^(14*m).",
        ),
        spec(
            "bertrand_hj_base_window_from_total",
            "forall s e h u j g. "
            f"({base_total}) -> ({base_lower}) -> ({base_upper}) -> "
            f"({base_ceiling}) -> ({base_h}) -> ({base_h_bound}) -> "
            f"({base_j}) -> ({base_j_bound}) -> "
            f"(({base_h_result}) /\\ ({base_j_result}))",
            (
                "bertrand_base_residue_linear_bounds",
                "ceil_square_seven_successor_lower",
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
                "pow_base_monotone",
                "pow_exponent_monotone_from_total",
                "le_trans",
            ),
            (
                "intro s",
                "intro e",
                "intro h",
                "intro u",
                "intro j",
                "intro g",
                "intro htotal",
                "intro hlower",
                "intro hupper",
                "intro hceiling",
                "intro hh",
                "intro hu",
                "intro hj",
                "intro hg",
                "have hlinear : "
                f"({witness_le('s + 1', '128', tag='hj_linear_successor')}) "
                "/\\ (("
                f"{witness_le('s + 7', '128', tag='hj_linear_guard')}) "
                "/\\ ("
                f"{witness_le('42', 's + 5', tag='hj_linear_exponent')}))",
                "specialize bertrand_base_residue_linear_bounds s",
                "apply bertrand_base_residue_linear_bounds",
                "exact hlower",
                "exact hupper",
                "cases hlinear",
                "cases hlinear_right",
                "have hceil_lower : "
                f"{witness_le('7 * (s + 1)', 'e', tag='hj_ceil_lower')}",
                "specialize ceil_square_seven_successor_lower s",
                "specialize ceil_square_seven_successor_lower e",
                "apply ceil_square_seven_successor_lower",
                "exact hlower",
                "exact hceiling",
                "have hone : s + 1 = S s",
                "trans S (s + 0)",
                "apply PA4",
                "congr",
                "apply PA3",
                "have hdouble : 2 * (s + 1) = 2 * s + 2",
                "rewrite hone",
                "apply PA6",
                f"have hhupper : exists hhx. ({h_upper})",
                "specialize htotal 128",
                "specialize htotal (2 * s + 2)",
                "exact htotal",
                "cases hhupper",
                f"have hhbridge : exists hhy. ({h_bridge})",
                "specialize htotal 4",
                "specialize htotal (7 * (s + 1))",
                "exact htotal",
                "cases hhbridge",
                "have hhmono : "
                f"{witness_le('h', 'x', tag='hj_h_mono')}",
                "specialize pow_base_monotone (s + 1)",
                "specialize pow_base_monotone 128",
                "specialize pow_base_monotone (2 * s + 2)",
                "specialize pow_base_monotone h",
                "specialize pow_base_monotone x",
                "apply pow_base_monotone",
                "exact hlinear_left",
                "exact hh",
                "exact hhupper_witness",
                "have hheq : x = x1",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total "
                "(s + 1)",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total "
                "(2 * s + 2)",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total "
                "(7 * (s + 1))",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total x",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total x1",
                "apply pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
                "exact htotal",
                "symm",
                "exact hdouble",
                "refl",
                "exact hhupper_witness",
                "exact hhbridge_witness",
                "rewrite hheq at hhmono",
                "have hhgrowth : "
                f"{witness_le('x1', 'u', tag='hj_h_growth')}",
                "specialize pow_exponent_monotone_from_total 4",
                "specialize pow_exponent_monotone_from_total (7 * (s + 1))",
                "specialize pow_exponent_monotone_from_total e",
                "specialize pow_exponent_monotone_from_total x1",
                "specialize pow_exponent_monotone_from_total u",
                "apply pow_exponent_monotone_from_total",
                "exact htotal",
                "exists 3",
                "norm_num",
                "exact hceil_lower",
                "exact hhbridge_witness",
                "exact hu",
                "have hhresult : "
                f"{witness_le('h', 'u', tag='hj_h_result_local')}",
                "specialize le_trans h",
                "specialize le_trans x1",
                "specialize le_trans u",
                "apply le_trans",
                "exact hhmono",
                "exact hhgrowth",
                f"have jjupper : exists jjx. ({j_upper})",
                "specialize htotal 128",
                "specialize htotal 12",
                "exact htotal",
                "cases jjupper",
                f"have jjbridge : exists jjy. ({j_bridge})",
                "specialize htotal 4",
                "specialize htotal 42",
                "exact htotal",
                "cases jjbridge",
                "have jjmono : "
                f"{witness_le('j', 'x2', tag='hj_j_mono')}",
                "specialize pow_base_monotone (s + 7)",
                "specialize pow_base_monotone 128",
                "specialize pow_base_monotone 12",
                "specialize pow_base_monotone j",
                "specialize pow_base_monotone x2",
                "apply pow_base_monotone",
                "exact hlinear_right_left",
                "exact hj",
                "exact jjupper_witness",
                "have jjeq : x2 = x3",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total 6",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total 12",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total 42",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total x2",
                "specialize "
                "pow_one_twenty_eight_double_eq_pow_four_seven_from_total x3",
                "apply pow_one_twenty_eight_double_eq_pow_four_seven_from_total",
                "exact htotal",
                "norm_num",
                "norm_num",
                "exact jjupper_witness",
                "exact jjbridge_witness",
                "rewrite jjeq at jjmono",
                "have jjgrowth : "
                f"{witness_le('x3', 'g', tag='hj_j_growth')}",
                "specialize pow_exponent_monotone_from_total 4",
                "specialize pow_exponent_monotone_from_total 42",
                "specialize pow_exponent_monotone_from_total (s + 5)",
                "specialize pow_exponent_monotone_from_total x3",
                "specialize pow_exponent_monotone_from_total g",
                "apply pow_exponent_monotone_from_total",
                "exact htotal",
                "exists 3",
                "norm_num",
                "exact hlinear_right_right",
                "exact jjbridge_witness",
                "exact hg",
                "have jjresult : "
                f"{witness_le('j', 'g', tag='hj_j_result_local')}",
                "specialize le_trans j",
                "specialize le_trans x3",
                "specialize le_trans g",
                "apply le_trans",
                "exact jjmono",
                "exact jjgrowth",
                "split",
                "exact hhresult",
                "exact jjresult",
            ),
            "All six roots 64 through 69 satisfy both H and J base bounds.",
        ),
    )


__all__ = ["make_bertrand_hj_base_window_candidate_theorems"]
