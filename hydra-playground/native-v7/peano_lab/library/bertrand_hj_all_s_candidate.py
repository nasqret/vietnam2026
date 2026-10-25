"""Constructive all-root H/J envelope for the exact Bertrand threshold.

This isolated candidate tranche starts from the finite root window ``32``
through ``37`` and iterates the checked six-step H/J transport.  The internal
large-input carrier is the shallow term ``16*32``.  In the standard natural
numbers it has value 512, but that host calculation is regression evidence
only: every native proof below retains the factorized term and never asks the
kernel to compare a depth-512 unary numeral.

``PowTotal``, ``Pow``, ``CeilDivSix``, ``FloorSqrt``, and order notation are
authoring conveniences only.  Every occurrence is expanded into the existing
first-order Peano language before a theorem specification is returned.  The
final row discharges ``PowTotal`` exactly once through the constructive
``pow_exists`` theorem; it does not select an unbounded choice function.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
)
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import witness_le
from .power_algebra_theorems import _power_terms


def make_bertrand_hj_all_s_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the six-row root-32 threshold and all-root H/J package."""

    threshold_input = witness_le(
        "16 * 32", "n", tag="hjas_threshold_input"
    )
    threshold_floor = floor_sqrt_relation(
        "2 * n", "s", tag="hjas_threshold_floor"
    )
    threshold_result = witness_le("32", "s", tag="hjas_threshold_result")
    threshold_base_floor = floor_sqrt_relation(
        "2 * (16 * 32)", "32", tag="hjas_threshold_base_floor"
    )
    threshold_scaled = witness_le(
        "2 * (16 * 32)", "2 * n", tag="hjas_threshold_scaled"
    )

    decomposition_source = witness_le(
        "32", "s", tag="hjas_decomposition_source"
    )
    decomposition_base_lower = witness_le(
        "32", "b", tag="hjas_decomposition_base_lower"
    )
    decomposition_base_upper = witness_le(
        "b", "37", tag="hjas_decomposition_base_upper"
    )
    decomposition_remainder_le = witness_le(
        "x2", "5", tag="hjas_decomposition_remainder_le"
    )
    decomposition_lifted_upper = witness_le(
        "32 + x2", "32 + 5", tag="hjas_decomposition_lifted_upper"
    )

    iterator_total = power_total_relation(tag="hjas_iterator")
    iterator_base_lower = witness_le(
        "32", "b", tag="hjas_iterator_base_lower"
    )
    iterator_base_upper = witness_le(
        "b", "37", tag="hjas_iterator_base_upper"
    )
    iterator_root = "b + 6 * k"
    iterator_ceiling = ceil_div_six_relation(
        f"({iterator_root}) * ({iterator_root})",
        "e",
        tag="hjas_iterator_ceiling",
    )
    iterator_h = _power_terms(
        f"({iterator_root}) + 1",
        f"2 * ({iterator_root}) + 2",
        "h",
        tag="hjas_iterator_h",
    )
    iterator_h_bound = _power_terms(
        "4", "e", "u", tag="hjas_iterator_h_bound"
    )
    iterator_j = _power_terms(
        f"({iterator_root}) + 7", "12", "j", tag="hjas_iterator_j"
    )
    iterator_j_bound = _power_terms(
        "4",
        f"({iterator_root}) + 5",
        "g",
        tag="hjas_iterator_j_bound",
    )
    iterator_h_result = witness_le(
        "h", "u", tag="hjas_iterator_h_result"
    )
    iterator_j_result = witness_le(
        "j", "g", tag="hjas_iterator_j_result"
    )

    iterator_zero_root = "b + 6 * 0"
    iterator_zero_lower = witness_le(
        "32", iterator_zero_root, tag="hjas_iterator_zero_lower"
    )
    iterator_zero_upper = witness_le(
        iterator_zero_root, "37", tag="hjas_iterator_zero_upper"
    )

    current_root = "b + 6 * k"
    current_ceiling_exists = ceil_div_six_relation(
        f"({current_root}) * ({current_root})",
        "ce",
        tag="hjas_current_ceiling_exists",
    )
    current_h_exists = _power_terms(
        f"({current_root}) + 1",
        f"2 * ({current_root}) + 2",
        "hh",
        tag="hjas_current_h_exists",
    )
    # After eliminating the preceding existentials the deterministic local
    # witness names are x=ce, x1=hh, x2=hu, x3=jj, and x4=gg.
    current_u_exists = _power_terms(
        "4", "x", "hu", tag="hjas_current_u_exists"
    )
    current_j_exists = _power_terms(
        f"({current_root}) + 7",
        "12",
        "jj",
        tag="hjas_current_j_exists",
    )
    current_g_exists = _power_terms(
        "4",
        f"({current_root}) + 5",
        "gg",
        tag="hjas_current_g_exists",
    )
    current_h_result = witness_le("x1", "x2", tag="hjas_current_h_result")
    current_j_result = witness_le("x3", "x4", tag="hjas_current_j_result")
    five_le_thirty_two = witness_le(
        "5", "32", tag="hjas_five_le_thirty_two"
    )
    five_le_base = witness_le("5", "b", tag="hjas_five_le_base")
    base_le_current = witness_le(
        "b", current_root, tag="hjas_base_le_current"
    )
    five_le_current = witness_le(
        "5", current_root, tag="hjas_five_le_current"
    )

    transport_next_ceiling = ceil_div_six_relation(
        f"(({current_root}) + 6) * (({current_root}) + 6)",
        "e",
        tag="hjas_transport_next_ceiling",
    )
    transport_next_h = _power_terms(
        f"({current_root}) + 7",
        f"2 * ({current_root}) + 14",
        "h",
        tag="hjas_transport_next_h",
    )
    transport_next_j = _power_terms(
        f"({current_root}) + 13",
        "12",
        "j",
        tag="hjas_transport_next_j",
    )
    transport_next_g = _power_terms(
        "4",
        f"({current_root}) + 11",
        "g",
        tag="hjas_transport_next_g",
    )

    iterator_script = [
        "intro b",
        "intro htotal",
        "intro hlower",
        "intro hupper",
        "induction k",
        "intro e",
        "intro h",
        "intro u",
        "intro j",
        "intro g",
        "intro hceiling",
        "intro hh",
        "intro hu",
        "intro hj",
        "intro hg",
        "have hroot_zero : b + 6 * 0 = b",
        "rewrite PA5",
        "apply PA3",
        f"have hzero_lower : {iterator_zero_lower}",
        "rewrite hroot_zero",
        "exact hlower",
        f"have hzero_upper : {iterator_zero_upper}",
        "rewrite hroot_zero",
        "exact hupper",
        f"specialize bertrand_hj_base_window_thirty_two_from_total ({iterator_zero_root})",
        "specialize bertrand_hj_base_window_thirty_two_from_total e",
        "specialize bertrand_hj_base_window_thirty_two_from_total h",
        "specialize bertrand_hj_base_window_thirty_two_from_total u",
        "specialize bertrand_hj_base_window_thirty_two_from_total j",
        "specialize bertrand_hj_base_window_thirty_two_from_total g",
        "apply bertrand_hj_base_window_thirty_two_from_total",
        "exact htotal",
        "exact hzero_lower",
        "exact hzero_upper",
        "exact hceiling",
        "exact hh",
        "exact hu",
        "exact hj",
        "exact hg",
        "intro e",
        "intro h",
        "intro u",
        "intro j",
        "intro g",
        "intro hceiling",
        "intro hh",
        "intro hu",
        "intro hj",
        "intro hg",
        f"have hcurrent_ceiling : exists ce. ({current_ceiling_exists})",
        f"specialize ceil_div_six_total (({current_root}) * ({current_root}))",
        "exact ceil_div_six_total",
        "cases hcurrent_ceiling",
        f"have hcurrent_h : exists hh. ({current_h_exists})",
        f"specialize htotal (({current_root}) + 1)",
        f"specialize htotal (2 * ({current_root}) + 2)",
        "exact htotal",
        "cases hcurrent_h",
        f"have hcurrent_u : exists hu. ({current_u_exists})",
        "specialize htotal 4",
        "specialize htotal x",
        "exact htotal",
        "cases hcurrent_u",
        f"have hcurrent_j : exists jj. ({current_j_exists})",
        f"specialize htotal (({current_root}) + 7)",
        "specialize htotal 12",
        "exact htotal",
        "cases hcurrent_j",
        f"have hcurrent_g : exists gg. ({current_g_exists})",
        "specialize htotal 4",
        f"specialize htotal (({current_root}) + 5)",
        "exact htotal",
        "cases hcurrent_g",
        f"have hcurrent_bounds : (({current_h_result}) /\\ ({current_j_result}))",
        "specialize IH x",
        "specialize IH x1",
        "specialize IH x2",
        "specialize IH x3",
        "specialize IH x4",
        "apply IH",
        "exact hcurrent_ceiling_witness",
        "exact hcurrent_h_witness",
        "exact hcurrent_u_witness",
        "exact hcurrent_j_witness",
        "exact hcurrent_g_witness",
        "cases hcurrent_bounds",
        f"have hfive_thirty_two : {five_le_thirty_two}",
        "exists 27",
        "norm_num",
        f"have hfive_base : {five_le_base}",
        "specialize le_trans 5",
        "specialize le_trans 32",
        "specialize le_trans b",
        "apply le_trans",
        "exact hfive_thirty_two",
        "exact hlower",
        f"have hbase_current : {base_le_current}",
        "specialize le_add_right b",
        f"specialize le_add_right (6 * k)",
        "exact le_add_right",
        f"have hfive_current : {five_le_current}",
        "specialize le_trans 5",
        "specialize le_trans b",
        f"specialize le_trans ({current_root})",
        "apply le_trans",
        "exact hfive_base",
        "exact hbase_current",
        f"have hroot_step : b + 6 * S k = ({current_root}) + 6",
        "rewrite PA6",
        "symm",
        "specialize add_assoc b",
        "specialize add_assoc (6 * k)",
        "specialize add_assoc 6",
        "apply add_assoc",
        f"have hnext_h_base : (b + 6 * S k) + 1 = ({current_root}) + 7",
        "rewrite hroot_step",
        "simp",
        f"have hnext_h_exponent : 2 * (b + 6 * S k) + 2 = 2 * ({current_root}) + 14",
        "rewrite hroot_step",
        "simp [mul_add, add_assoc]",
        f"have hnext_j_base : (b + 6 * S k) + 7 = ({current_root}) + 13",
        "rewrite hroot_step",
        "simp [add_assoc]",
        f"have hnext_j_exponent : (b + 6 * S k) + 5 = ({current_root}) + 11",
        "rewrite hroot_step",
        "simp [add_assoc]",
        f"have hnext_ceiling : {transport_next_ceiling}",
    ]
    iterator_script.extend(("rewrite <- hroot_step",) * 4)
    iterator_script.extend(
        (
            "exact hceiling",
            f"have hnext_h : {transport_next_h}",
        )
    )
    iterator_script.extend(("rewrite <- hnext_h_base",) * 2)
    iterator_script.extend(("rewrite <- hnext_h_exponent",) * 4)
    iterator_script.extend(("exact hh", f"have hnext_j : {transport_next_j}"))
    iterator_script.extend(("rewrite <- hnext_j_base",) * 2)
    iterator_script.extend(
        ("exact hj", f"have hnext_g : {transport_next_g}")
    )
    iterator_script.extend(("rewrite <- hnext_j_exponent",) * 4)
    iterator_script.extend(
        (
            "exact hg",
            f"specialize bertrand_hj_six_step_from_total ({current_root})",
            "specialize bertrand_hj_six_step_from_total x",
            "specialize bertrand_hj_six_step_from_total e",
            "specialize bertrand_hj_six_step_from_total x1",
            "specialize bertrand_hj_six_step_from_total x2",
            "specialize bertrand_hj_six_step_from_total x3",
            "specialize bertrand_hj_six_step_from_total x4",
            "specialize bertrand_hj_six_step_from_total h",
            "specialize bertrand_hj_six_step_from_total u",
            "specialize bertrand_hj_six_step_from_total j",
            "specialize bertrand_hj_six_step_from_total g",
            "apply bertrand_hj_six_step_from_total",
            "exact htotal",
            "exact hfive_current",
            "exact hcurrent_ceiling_witness",
            "exact hnext_ceiling",
            "exact hcurrent_h_witness",
            "exact hcurrent_u_witness",
            "exact hcurrent_j_witness",
            "exact hcurrent_g_witness",
            "split",
            "exact hcurrent_bounds_left",
            "exact hcurrent_bounds_right",
            "exact hnext_h",
            "exact hu",
            "exact hnext_j",
            "exact hnext_g",
        )
    )

    envelope_lower = witness_le("32", "s", tag="hjas_envelope_lower")
    envelope_ceiling = ceil_div_six_relation(
        "s * s", "e", tag="hjas_envelope_ceiling"
    )
    envelope_h = _power_terms(
        "s + 1", "2 * s + 2", "h", tag="hjas_envelope_h"
    )
    envelope_h_bound = _power_terms(
        "4", "e", "u", tag="hjas_envelope_h_bound"
    )
    envelope_j = _power_terms(
        "s + 7", "12", "j", tag="hjas_envelope_j"
    )
    envelope_j_bound = _power_terms(
        "4", "s + 5", "g", tag="hjas_envelope_j_bound"
    )
    envelope_h_result = witness_le("h", "u", tag="hjas_envelope_h_result")
    envelope_j_result = witness_le("j", "g", tag="hjas_envelope_j_result")
    envelope_total = power_total_relation(tag="hjas_envelope_total")
    envelope_decomposition = (
        f"exists b k. ((({decomposition_base_lower}) /\\ "
        f"({decomposition_base_upper})) /\\ s = b + 6 * k)"
    )

    # After decomposition, x is the base-window root and x1 is the block
    # count.  Discharge the three fixed premises of the nested iterator first,
    # then specialize the resulting family at x1 and the supplied graph data.
    family_root = "x + 6 * kk"
    family_ceiling = ceil_div_six_relation(
        f"({family_root}) * ({family_root})",
        "ee",
        tag="hjas_family_ceiling",
    )
    family_h = _power_terms(
        f"({family_root}) + 1",
        f"2 * ({family_root}) + 2",
        "hh",
        tag="hjas_family_h",
    )
    family_h_bound = _power_terms(
        "4", "ee", "uu", tag="hjas_family_h_bound"
    )
    family_j = _power_terms(
        f"({family_root}) + 7", "12", "jj", tag="hjas_family_j"
    )
    family_j_bound = _power_terms(
        "4",
        f"({family_root}) + 5",
        "gg",
        tag="hjas_family_j_bound",
    )
    family_h_result = witness_le("hh", "uu", tag="hjas_family_h_result")
    family_j_result = witness_le("jj", "gg", tag="hjas_family_j_result")
    family_formula = (
        "forall kk ee hh uu jj gg. "
        f"({family_ceiling}) -> ({family_h}) -> ({family_h_bound}) -> "
        f"({family_j}) -> ({family_j_bound}) -> "
        f"((({family_h_result}) /\\ ({family_j_result})))"
    )

    block_root = "x + 6 * x1"
    block_ceiling = ceil_div_six_relation(
        f"({block_root}) * ({block_root})",
        "e",
        tag="hjas_block_ceiling",
    )
    block_h = _power_terms(
        f"({block_root}) + 1",
        f"2 * ({block_root}) + 2",
        "h",
        tag="hjas_block_h",
    )
    block_j = _power_terms(
        f"({block_root}) + 7", "12", "j", tag="hjas_block_j"
    )
    block_g = _power_terms(
        "4", f"({block_root}) + 5", "g", tag="hjas_block_g"
    )

    envelope_script = [
        "intro s",
        "intro e",
        "intro h",
        "intro u",
        "intro j",
        "intro g",
        "intro hlower",
        "intro hceiling",
        "intro hh",
        "intro hu",
        "intro hj",
        "intro hg",
        f"have htotal : {envelope_total}",
        "intro a",
        "intro d",
        "specialize pow_exists a",
        "specialize pow_exists d",
        "exact pow_exists",
        f"have hdecomposition : {envelope_decomposition}",
        "specialize six_block_window_decomposition_above_thirty_two s",
        "apply six_block_window_decomposition_above_thirty_two",
        "exact hlower",
        "cases hdecomposition",
        "cases hdecomposition_witness",
        "cases hdecomposition_witness_witness",
        "cases hdecomposition_witness_witness_left",
        f"have hfamily : {family_formula}",
        "specialize bertrand_hj_six_block_iterate_from_total x",
        "apply bertrand_hj_six_block_iterate_from_total",
        "exact htotal",
        "exact hdecomposition_witness_witness_left_left",
        "exact hdecomposition_witness_witness_left_right",
        f"have hblock_ceiling : {block_ceiling}",
    ]
    envelope_script.extend(
        ("rewrite <- hdecomposition_witness_witness_right",) * 4
    )
    envelope_script.extend(("exact hceiling", f"have hblock_h : {block_h}"))
    envelope_script.extend(
        ("rewrite <- hdecomposition_witness_witness_right",) * 6
    )
    envelope_script.extend(("exact hh", f"have hblock_j : {block_j}"))
    envelope_script.extend(
        ("rewrite <- hdecomposition_witness_witness_right",) * 2
    )
    envelope_script.extend(("exact hj", f"have hblock_g : {block_g}"))
    envelope_script.extend(
        ("rewrite <- hdecomposition_witness_witness_right",) * 4
    )
    envelope_script.extend(
        (
            "exact hg",
            "specialize hfamily x1",
            "specialize hfamily e",
            "specialize hfamily h",
            "specialize hfamily u",
            "specialize hfamily j",
            "specialize hfamily g",
            "apply hfamily",
            "exact hblock_ceiling",
            "exact hblock_h",
            "exact hu",
            "exact hblock_j",
            "exact hblock_g",
        )
    )

    return (
        spec(
            "scaled_factor_square_identity",
            "forall c d a. a = c * d -> a * a = c * (d * a)",
            ("mul_assoc",),
            (
                "intro c",
                "intro d",
                "intro a",
                "intro ha",
                "rewrite ha",
                "apply mul_assoc",
            ),
            "A factorization of a transports its square without expanding "
            "either factor.",
        ),
        spec(
            "thirty_two_square_eq_twice_sixteen_times_thirty_two",
            "32 * 32 = 2 * (16 * 32)",
            ("scaled_factor_square_identity",),
            (
                "have hfactor : 32 = 2 * 16",
                "norm_num",
                "specialize scaled_factor_square_identity 2",
                "specialize scaled_factor_square_identity 16",
                "specialize scaled_factor_square_identity 32",
                "apply scaled_factor_square_identity",
                "exact hfactor",
            ),
            "The root-32 square identity carried by the shallow factorization 16*32.",
        ),
        spec(
            "floor_sqrt_factorized_threshold_thirty_two",
            "forall n s. "
            f"({threshold_input}) -> ({threshold_floor}) -> "
            f"({threshold_result})",
            (
                "thirty_two_square_eq_twice_sixteen_times_thirty_two",
                "zero_add",
                "square_lt_successor_square",
                "mul_le_mul_left",
                "floor_sqrt_monotone",
            ),
            (
                "intro n",
                "intro s",
                "intro hthreshold",
                "intro hfloor",
                f"have hbase : {threshold_base_floor}",
                "split",
                "exists 0",
                "trans 32 * 32",
                "apply zero_add",
                "exact thirty_two_square_eq_twice_sixteen_times_thirty_two",
                "specialize square_lt_successor_square 32",
                "rewrite "
                "thirty_two_square_eq_twice_sixteen_times_thirty_two "
                "at square_lt_successor_square",
                "exact square_lt_successor_square",
                f"have hscaled : {threshold_scaled}",
                "specialize mul_le_mul_left (16 * 32)",
                "specialize mul_le_mul_left n",
                "specialize mul_le_mul_left 2",
                "apply mul_le_mul_left",
                "exact hthreshold",
                "specialize floor_sqrt_monotone (2 * (16 * 32))",
                "specialize floor_sqrt_monotone (2 * n)",
                "specialize floor_sqrt_monotone 32",
                "specialize floor_sqrt_monotone s",
                "apply floor_sqrt_monotone",
                "exact hbase",
                "exact hfloor",
                "exact hscaled",
            ),
            "The factorized large-input threshold forces every selected root "
            "to be at least 32.",
        ),
        spec(
            "six_block_window_decomposition_above_thirty_two",
            "forall s. "
            f"({decomposition_source}) -> exists b k. "
            f"((({decomposition_base_lower}) /\\ "
            f"({decomposition_base_upper})) /\\ s = b + 6 * k)",
            (
                "division_remainder_exists",
                "succ_ne_zero",
                "le_of_succ_le_succ",
                "le_add_right",
                "add_le_add_left",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro s",
                "intro hsource",
                "cases hsource",
                "have hdivision : exists q r. x = 6 * q + r /\\ "
                "exists h. h + S r = 6",
                "specialize division_remainder_exists 6",
                "specialize division_remainder_exists x",
                "apply division_remainder_exists",
                "intro hzero",
                "specialize succ_ne_zero 5",
                "apply succ_ne_zero",
                "exact hzero",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "exists 32 + x2",
                "exists x1",
                "split",
                "split",
                "specialize le_add_right 32",
                "specialize le_add_right x2",
                "exact le_add_right",
                f"have hremainder : {decomposition_remainder_le}",
                "specialize le_of_succ_le_succ x2",
                "specialize le_of_succ_le_succ 5",
                "apply le_of_succ_le_succ",
                "exact hdivision_witness_witness_right",
                f"have hlifted : {decomposition_lifted_upper}",
                "specialize add_le_add_left x2",
                "specialize add_le_add_left 5",
                "specialize add_le_add_left 32",
                "apply add_le_add_left",
                "exact hremainder",
                "have hthirty_seven : 32 + 5 = 37",
                "norm_num",
                "rewrite hthirty_seven at hlifted",
                "exact hlifted",
                "trans x + 32",
                "symm",
                "exact hsource_witness",
                "trans (6 * x1 + x2) + 32",
                "congr",
                "exact hdivision_witness_witness_left",
                "refl",
                "trans 6 * x1 + (x2 + 32)",
                "specialize add_assoc (6 * x1)",
                "specialize add_assoc x2",
                "specialize add_assoc 32",
                "apply add_assoc",
                "trans 6 * x1 + (32 + x2)",
                "congr",
                "refl",
                "specialize add_comm x2",
                "specialize add_comm 32",
                "apply add_comm",
                "specialize add_comm (6 * x1)",
                "specialize add_comm (32 + x2)",
                "apply add_comm",
            ),
            "Every s>=32 is a six-step iterate of one base root in the exact window 32..37.",
        ),
        spec(
            "bertrand_hj_six_block_iterate_from_total",
            "forall b. "
            f"({iterator_total}) -> ({iterator_base_lower}) -> "
            f"({iterator_base_upper}) -> forall k e h u j g. "
            f"({iterator_ceiling}) -> ({iterator_h}) -> "
            f"({iterator_h_bound}) -> ({iterator_j}) -> "
            f"({iterator_j_bound}) -> "
            f"((({iterator_h_result}) /\\ ({iterator_j_result})))",
            (
                "bertrand_hj_base_window_thirty_two_from_total",
                "bertrand_hj_six_step_from_total",
                "ceil_div_six_total",
                "le_add_right",
                "le_trans",
                "mul_add",
                "add_assoc",
            ),
            tuple(iterator_script),
            "The common H/J invariant iterates constructively over every six-step block.",
        ),
        spec(
            "bertrand_hj_envelope_thirty_two",
            "forall s e h u j g. "
            f"({envelope_lower}) -> ({envelope_ceiling}) -> "
            f"({envelope_h}) -> ({envelope_h_bound}) -> "
            f"({envelope_j}) -> ({envelope_j_bound}) -> "
            f"((({envelope_h_result}) /\\ ({envelope_j_result})))",
            (
                "pow_exists",
                "six_block_window_decomposition_above_thirty_two",
                "bertrand_hj_six_block_iterate_from_total",
            ),
            tuple(envelope_script),
            "All roots s>=32 satisfy both H and J after discharging power totality once.",
        ),
    )


__all__ = ["make_bertrand_hj_all_s_candidate_theorems"]
