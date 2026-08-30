"""Capacity-safe six-step transport for the Bertrand H/J invariant.

The invariant is represented entirely by conservative first-order relations:

    H(s): (s + 1)^(2*s + 2) <= 4^ceil(s*s/6)
    J(s): (s + 7)^12        <= 4^(s + 5)

The two component transports share an ordinary ``PowTotal`` antecedent.  The
combined row advances both relations from ``s`` to ``s + 6``.  No old guard
wrapper or large evaluated-power identity is used.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import ceil_div_six_relation
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import witness_le
from .power_algebra_theorems import _power_terms


def make_bertrand_hj_transport_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build separate H/J transports and their conjunction."""

    h_total = power_total_relation(tag="hjt_h")
    h_lower = witness_le("5", "s", tag="hjt_h_lower")
    h_ceiling = ceil_div_six_relation("s * s", "e", tag="hjt_h_ceiling")
    h_next_ceiling = ceil_div_six_relation(
        "(s + 6) * (s + 6)", "f", tag="hjt_h_next_ceiling"
    )
    h_now = _power_terms("s + 1", "2 * s + 2", "h", tag="hjt_h_now")
    h_now_bound = _power_terms("4", "e", "u", tag="hjt_h_now_bound")
    h_now_result = witness_le("h", "u", tag="hjt_h_now_result")
    h_guard = _power_terms("s + 7", "12", "j", tag="hjt_h_guard")
    h_guard_bound = _power_terms("4", "s + 5", "g", tag="hjt_h_guard_bound")
    h_guard_result = witness_le("j", "g", tag="hjt_h_guard_result")
    h_next = _power_terms("s + 7", "2 * s + 14", "hn", tag="hjt_h_next")
    h_next_bound = _power_terms("4", "f", "un", tag="hjt_h_next_bound")
    h_next_result = witness_le("hn", "un", tag="hjt_h_next_result")

    h_prefix = _power_terms(
        "s + 7", "2 * s + 2", "hp", tag="hjt_h_prefix"
    )
    h_double = _power_terms(
        "2 * (s + 1)", "2 * s + 2", "hd", tag="hjt_h_double"
    )
    h_two_factor = _power_terms(
        "2", "2 * s + 2", "ht", tag="hjt_h_two_factor"
    )
    h_four_factor = _power_terms(
        "4", "s + 1", "hf", tag="hjt_h_four_factor"
    )
    h_bound_prefix = _power_terms(
        "4", "(s + 1) + e", "hb", tag="hjt_h_bound_prefix"
    )
    seed_two_h = _power_terms("2", "2", "4", tag="hjt_h_seed_two")
    seed_seven_h = _power_terms("2", "7", "128", tag="hjt_h_seed_seven")

    j_total = power_total_relation(tag="hjt_j")
    j_now = _power_terms("s + 7", "12", "j", tag="hjt_j_now")
    j_now_bound = _power_terms("4", "s + 5", "g", tag="hjt_j_now_bound")
    j_now_result = witness_le("j", "g", tag="hjt_j_now_result")
    j_next = _power_terms("s + 13", "12", "jn", tag="hjt_j_next")
    j_next_bound = _power_terms("4", "s + 11", "gn", tag="hjt_j_next_bound")
    j_next_result = witness_le("jn", "gn", tag="hjt_j_next_result")
    j_double = _power_terms(
        "2 * (s + 7)", "12", "jd", tag="hjt_j_double"
    )
    j_two_factor = _power_terms("2", "12", "jt", tag="hjt_j_two_factor")
    j_four_factor = _power_terms("4", "6", "jf", tag="hjt_j_four_factor")
    seed_two_j = _power_terms("2", "2", "4", tag="hjt_j_seed_two")
    seed_seven_j = _power_terms("2", "7", "128", tag="hjt_j_seed_seven")

    combined_total = power_total_relation(tag="hjt_combined")
    combined_lower = witness_le("5", "s", tag="hjt_combined_lower")
    combined_ceiling = ceil_div_six_relation(
        "s * s", "e", tag="hjt_combined_ceiling"
    )
    combined_next_ceiling = ceil_div_six_relation(
        "(s + 6) * (s + 6)", "f", tag="hjt_combined_next_ceiling"
    )
    combined_h = _power_terms(
        "s + 1", "2 * s + 2", "h", tag="hjt_combined_h"
    )
    combined_h_bound = _power_terms(
        "4", "e", "u", tag="hjt_combined_h_bound"
    )
    combined_j = _power_terms(
        "s + 7", "12", "j", tag="hjt_combined_j"
    )
    combined_j_bound = _power_terms(
        "4", "s + 5", "g", tag="hjt_combined_j_bound"
    )
    combined_h_result = witness_le(
        "h", "u", tag="hjt_combined_h_result"
    )
    combined_j_result = witness_le(
        "j", "g", tag="hjt_combined_j_result"
    )
    combined_h_next = _power_terms(
        "s + 7", "2 * s + 14", "hn", tag="hjt_combined_h_next"
    )
    combined_h_next_bound = _power_terms(
        "4", "f", "un", tag="hjt_combined_h_next_bound"
    )
    combined_j_next = _power_terms(
        "s + 13", "12", "jn", tag="hjt_combined_j_next"
    )
    combined_j_next_bound = _power_terms(
        "4", "s + 11", "gn", tag="hjt_combined_j_next_bound"
    )
    combined_h_next_result = witness_le(
        "hn", "un", tag="hjt_combined_h_next_result"
    )
    combined_j_next_result = witness_le(
        "jn", "gn", tag="hjt_combined_j_next_result"
    )

    return (
        spec(
            "bertrand_h_six_step_transport_from_total",
            "forall s e f h u j g hn un. "
            f"({h_total}) -> ({h_lower}) -> ({h_ceiling}) -> "
            f"({h_next_ceiling}) -> ({h_now}) -> ({h_now_bound}) -> "
            f"({h_now_result}) -> ({h_guard}) -> ({h_guard_bound}) -> "
            f"({h_guard_result}) -> ({h_next}) -> ({h_next_bound}) -> "
            f"({h_next_result})",
            (
                "ceil_div_six_square_six_step",
                "two_mul_eq_add_self",
                "pow_base_monotone",
                "pow_mul_base",
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "pow_add",
                "mul_le_mul",
                "le_refl",
                "le_trans",
                "add_assoc",
                "add_comm",
                "add_succ_left",
            ),
            (
                "intro s",
                "intro e",
                "intro f",
                "intro h",
                "intro u",
                "intro j",
                "intro g",
                "intro hn",
                "intro un",
                "intro htotal",
                "intro hlower",
                "intro hceiling",
                "intro hnextceiling",
                "intro hh",
                "intro hu",
                "intro hhu",
                "intro hj",
                "intro hg",
                "intro hjg",
                "intro hhn",
                "intro hun",
                "have hceilshift : f = e + (2 * s + 6)",
                "specialize ceil_div_six_square_six_step s",
                "specialize ceil_div_six_square_six_step e",
                "specialize ceil_div_six_square_six_step f",
                "apply ceil_div_six_square_six_step",
                "exact hceiling",
                "exact hnextceiling",
                "cases hlower",
                "have hbase : "
                f"{witness_le('s + 7', '2 * (s + 1)', tag='hjt_h_base')}",
                "exists x",
                "rewrite <- hlower_witness",
                "simp [two_mul_eq_add_self, add_assoc, add_comm]",
                "rewrite <- hlower_witness",
                "rewrite <- hlower_witness",
                "simp [add_assoc, add_comm]",
                "have hone : s + 1 = S s",
                "trans S (s + 0)",
                "apply PA4",
                "congr",
                "apply PA3",
                "have hdouble_exponent : 2 * (s + 1) = 2 * s + 2",
                "rewrite hone",
                "apply PA6",
                f"have hprefix_exists : exists hp. ({h_prefix})",
                "specialize htotal (s + 7)",
                "specialize htotal (2 * s + 2)",
                "exact htotal",
                "cases hprefix_exists",
                f"have hdouble_exists : exists hd. ({h_double})",
                "specialize htotal (2 * (s + 1))",
                "specialize htotal (2 * s + 2)",
                "exact htotal",
                "cases hdouble_exists",
                "have hprefix_double : "
                f"{witness_le('x1', 'x2', tag='hjt_h_prefix_double')}",
                "specialize pow_base_monotone (s + 7)",
                "specialize pow_base_monotone (2 * (s + 1))",
                "specialize pow_base_monotone (2 * s + 2)",
                "specialize pow_base_monotone x1",
                "specialize pow_base_monotone x2",
                "apply pow_base_monotone",
                "exact hbase",
                "exact hprefix_exists_witness",
                "exact hdouble_exists_witness",
                f"have htwo_exists : exists ht. ({h_two_factor})",
                "specialize htotal 2",
                "specialize htotal (2 * s + 2)",
                "exact htotal",
                "cases htwo_exists",
                f"have hfour_exists : exists hf. ({h_four_factor})",
                "specialize htotal 4",
                "specialize htotal (s + 1)",
                "exact htotal",
                "cases hfour_exists",
                f"have hseeds : ({seed_two_h}) /\\ ({seed_seven_h})",
                "apply pow_two_seed_bundle_from_total",
                "exact htotal",
                "cases hseeds",
                "have htwo_four : x3 = x4",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total (s + 1)",
                "specialize pow_mul_exp_from_total (2 * s + 2)",
                "specialize pow_mul_exp_from_total 4",
                "specialize pow_mul_exp_from_total x4",
                "specialize pow_mul_exp_from_total x3",
                "symm",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "symm",
                "exact hdouble_exponent",
                "exact hseeds_left",
                "exact hfour_exists_witness",
                "exact htwo_exists_witness",
                "have hdouble_factor : x2 = x3 * h",
                "specialize pow_mul_base 2",
                "specialize pow_mul_base (s + 1)",
                "specialize pow_mul_base (2 * s + 2)",
                "specialize pow_mul_base x3",
                "specialize pow_mul_base h",
                "specialize pow_mul_base x2",
                "apply pow_mul_base",
                "exact htwo_exists_witness",
                "exact hh",
                "exact hdouble_exists_witness",
                "rewrite hdouble_factor at hprefix_double",
                "rewrite htwo_four at hprefix_double",
                "have hhfactor_bound : "
                f"{witness_le('x4 * h', 'x4 * u', tag='hjt_h_factor_bound')}",
                "specialize mul_le_mul x4",
                "specialize mul_le_mul x4",
                "specialize mul_le_mul h",
                "specialize mul_le_mul u",
                "apply mul_le_mul",
                "specialize le_refl x4",
                "exact le_refl",
                "exact hhu",
                "have hprefix_bound : "
                f"{witness_le('x1', 'x4 * u', tag='hjt_h_prefix_bound')}",
                "specialize le_trans x1",
                "specialize le_trans (x4 * h)",
                "specialize le_trans (x4 * u)",
                "apply le_trans",
                "exact hprefix_double",
                "exact hhfactor_bound",
                "have hnext_sum : 2 * s + 14 = (2 * s + 2) + 12",
                "simp [add_assoc]",
                "have hnext_factor : hn = x1 * j",
                "specialize pow_add (s + 7)",
                "specialize pow_add (2 * s + 2)",
                "specialize pow_add 12",
                "specialize pow_add (2 * s + 14)",
                "specialize pow_add x1",
                "specialize pow_add j",
                "specialize pow_add hn",
                "apply pow_add",
                "exact hnext_sum",
                "exact hprefix_exists_witness",
                "exact hj",
                "exact hhn",
                f"have hbound_prefix_exists : exists hb. ({h_bound_prefix})",
                "specialize htotal 4",
                "specialize htotal ((s + 1) + e)",
                "exact htotal",
                "cases hbound_prefix_exists",
                "have hbound_prefix_factor : x5 = x4 * u",
                "specialize pow_add 4",
                "specialize pow_add (s + 1)",
                "specialize pow_add e",
                "specialize pow_add ((s + 1) + e)",
                "specialize pow_add x4",
                "specialize pow_add u",
                "specialize pow_add x5",
                "apply pow_add",
                "refl",
                "exact hfour_exists_witness",
                "exact hu",
                "exact hbound_prefix_exists_witness",
                "have hbound_sum : f = ((s + 1) + e) + (s + 5)",
                "rewrite hceilshift",
                "simp [two_mul_eq_add_self, add_assoc, add_comm]",
                "congr",
                "congr",
                "congr",
                "congr",
                "congr",
                "trans S (s + (e + s))",
                "congr",
                "trans (e + s) + s",
                "symm",
                "apply add_assoc",
                "trans (s + e) + s",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "symm",
                "apply add_succ_left",
                "have hbound_factor : un = x5 * g",
                "specialize pow_add 4",
                "specialize pow_add ((s + 1) + e)",
                "specialize pow_add (s + 5)",
                "specialize pow_add f",
                "specialize pow_add x5",
                "specialize pow_add g",
                "specialize pow_add un",
                "apply pow_add",
                "exact hbound_sum",
                "exact hbound_prefix_exists_witness",
                "exact hg",
                "exact hun",
                "have hproducts : "
                f"{witness_le('x1 * j', '(x4 * u) * g', tag='hjt_h_products')}",
                "specialize mul_le_mul x1",
                "specialize mul_le_mul (x4 * u)",
                "specialize mul_le_mul j",
                "specialize mul_le_mul g",
                "apply mul_le_mul",
                "exact hprefix_bound",
                "exact hjg",
                "rewrite hnext_factor",
                "rewrite hbound_factor",
                "rewrite hbound_prefix_factor",
                "exact hproducts",
            ),
            "H(s) and J(s) together imply H(s+6).",
        ),
        spec(
            "bertrand_j_six_step_transport_from_total",
            "forall s j g jn gn. "
            f"({j_total}) -> ({j_now}) -> ({j_now_bound}) -> "
            f"({j_now_result}) -> ({j_next}) -> ({j_next_bound}) -> "
            f"({j_next_result})",
            (
                "two_mul_eq_add_self",
                "pow_base_monotone",
                "pow_mul_base",
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "pow_add",
                "mul_le_mul",
                "le_refl",
                "le_trans",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro s",
                "intro j",
                "intro g",
                "intro jn",
                "intro gn",
                "intro htotal",
                "intro hj",
                "intro hg",
                "intro hjg",
                "intro hjn",
                "intro hgn",
                "have hbase : "
                f"{witness_le('s + 13', '2 * (s + 7)', tag='hjt_j_base')}",
                "exists S s",
                "simp [two_mul_eq_add_self, add_assoc, add_comm]",
                f"have hdouble : exists jd. ({j_double})",
                "specialize htotal (2 * (s + 7))",
                "specialize htotal 12",
                "exact htotal",
                "cases hdouble",
                "have hjdouble : "
                f"{witness_le('jn', 'x', tag='hjt_j_next_double')}",
                "specialize pow_base_monotone (s + 13)",
                "specialize pow_base_monotone (2 * (s + 7))",
                "specialize pow_base_monotone 12",
                "specialize pow_base_monotone jn",
                "specialize pow_base_monotone x",
                "apply pow_base_monotone",
                "exact hbase",
                "exact hjn",
                "exact hdouble_witness",
                f"have htwo : exists jt. ({j_two_factor})",
                "specialize htotal 2",
                "specialize htotal 12",
                "exact htotal",
                "cases htwo",
                f"have hfour : exists jf. ({j_four_factor})",
                "specialize htotal 4",
                "specialize htotal 6",
                "exact htotal",
                "cases hfour",
                f"have hseeds : ({seed_two_j}) /\\ ({seed_seven_j})",
                "apply pow_two_seed_bundle_from_total",
                "exact htotal",
                "cases hseeds",
                "have htwo_four : x1 = x2",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 6",
                "specialize pow_mul_exp_from_total 12",
                "specialize pow_mul_exp_from_total 4",
                "specialize pow_mul_exp_from_total x2",
                "specialize pow_mul_exp_from_total x1",
                "symm",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "norm_num",
                "exact hseeds_left",
                "exact hfour_witness",
                "exact htwo_witness",
                "have hdouble_factor : x = x1 * j",
                "specialize pow_mul_base 2",
                "specialize pow_mul_base (s + 7)",
                "specialize pow_mul_base 12",
                "specialize pow_mul_base x1",
                "specialize pow_mul_base j",
                "specialize pow_mul_base x",
                "apply pow_mul_base",
                "exact htwo_witness",
                "exact hj",
                "exact hdouble_witness",
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
                "have hbound_factor : gn = x2 * g",
                "specialize pow_add 4",
                "specialize pow_add 6",
                "specialize pow_add (s + 5)",
                "specialize pow_add (s + 11)",
                "specialize pow_add x2",
                "specialize pow_add g",
                "specialize pow_add gn",
                "apply pow_add",
                "exact hsum",
                "exact hfour_witness",
                "exact hg",
                "exact hgn",
                "have hproducts : "
                f"{witness_le('x1 * j', 'x2 * g', tag='hjt_j_products')}",
                "rewrite htwo_four",
                "specialize mul_le_mul x2",
                "specialize mul_le_mul x2",
                "specialize mul_le_mul j",
                "specialize mul_le_mul g",
                "apply mul_le_mul",
                "specialize le_refl x2",
                "exact le_refl",
                "exact hjg",
                "specialize le_trans jn",
                "specialize le_trans x",
                "specialize le_trans gn",
                "apply le_trans",
                "exact hjdouble",
                "rewrite hdouble_factor",
                "rewrite hbound_factor",
                "exact hproducts",
            ),
            "J(s) implies J(s+6) through the shared 2^12 = 4^6 factor.",
        ),
        spec(
            "bertrand_hj_six_step_from_total",
            "forall s e f h u j g hn un jn gn. "
            f"({combined_total}) -> ({combined_lower}) -> "
            f"({combined_ceiling}) -> ({combined_next_ceiling}) -> "
            f"({combined_h}) -> ({combined_h_bound}) -> "
            f"({combined_j}) -> ({combined_j_bound}) -> "
            f"((({combined_h_result}) /\\ ({combined_j_result}))) -> "
            f"({combined_h_next}) -> ({combined_h_next_bound}) -> "
            f"({combined_j_next}) -> ({combined_j_next_bound}) -> "
            f"((({combined_h_next_result}) /\\ "
            f"({combined_j_next_result})))",
            (
                "bertrand_h_six_step_transport_from_total",
                "bertrand_j_six_step_transport_from_total",
            ),
            (
                "intro s",
                "intro e",
                "intro f",
                "intro h",
                "intro u",
                "intro j",
                "intro g",
                "intro hn",
                "intro un",
                "intro jn",
                "intro gn",
                "intro htotal",
                "intro hlower",
                "intro hceiling",
                "intro hnextceiling",
                "intro hh",
                "intro hu",
                "intro hj",
                "intro hg",
                "intro hcurrent",
                "intro hhn",
                "intro hun",
                "intro hjn",
                "intro hgn",
                "cases hcurrent",
                "have hhnext : "
                f"{witness_le('hn', 'un', tag='hjt_combined_h_local')}",
                "specialize bertrand_h_six_step_transport_from_total s",
                "specialize bertrand_h_six_step_transport_from_total e",
                "specialize bertrand_h_six_step_transport_from_total f",
                "specialize bertrand_h_six_step_transport_from_total h",
                "specialize bertrand_h_six_step_transport_from_total u",
                "specialize bertrand_h_six_step_transport_from_total j",
                "specialize bertrand_h_six_step_transport_from_total g",
                "specialize bertrand_h_six_step_transport_from_total hn",
                "specialize bertrand_h_six_step_transport_from_total un",
                "apply bertrand_h_six_step_transport_from_total",
                "exact htotal",
                "exact hlower",
                "exact hceiling",
                "exact hnextceiling",
                "exact hh",
                "exact hu",
                "exact hcurrent_left",
                "exact hj",
                "exact hg",
                "exact hcurrent_right",
                "exact hhn",
                "exact hun",
                "have hjnext : "
                f"{witness_le('jn', 'gn', tag='hjt_combined_j_local')}",
                "specialize bertrand_j_six_step_transport_from_total s",
                "specialize bertrand_j_six_step_transport_from_total j",
                "specialize bertrand_j_six_step_transport_from_total g",
                "specialize bertrand_j_six_step_transport_from_total jn",
                "specialize bertrand_j_six_step_transport_from_total gn",
                "apply bertrand_j_six_step_transport_from_total",
                "exact htotal",
                "exact hj",
                "exact hg",
                "exact hcurrent_right",
                "exact hjn",
                "exact hgn",
                "split",
                "exact hhnext",
                "exact hjnext",
            ),
            "The paired H/J invariant advances by six under one PowTotal premise.",
        ),
    )


__all__ = ["make_bertrand_hj_transport_candidate_theorems"]
