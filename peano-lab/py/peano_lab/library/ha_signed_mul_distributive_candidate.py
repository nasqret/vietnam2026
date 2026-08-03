"""Strict-HA distributivity candidates for canonical signed arithmetic.

The module separates the natural-number calculation from transport through
the exact RFC D05 ``SignedAdd`` and D06 ``SignedMul`` graphs.  Left
distributivity is proved directly from decoded contribution equations.  The
right law is then transported through graph-level commutativity, avoiding a
second copy of the same large witness calculation.

Every statement expands to the unchanged first-order language
``{0,S,+,*,=}``.  The candidates are constructive, dependency-curried,
unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_add_candidate import signed_add
from peano_lab.library.ha_signed_mul_candidate import signed_mul


def make_ha_signed_mul_distributive_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build natural helpers and both canonical distributivity graphs."""

    add_bc = signed_add("b", "c", "bc", tag="distrib_left_bc")
    mul_ab = signed_mul("a", "b", "ab", tag="distrib_left_ab")
    mul_ac = signed_mul("a", "c", "ac", tag="distrib_left_ac")
    mul_abc = signed_mul("a", "bc", "out", tag="distrib_left_abc")
    add_products = signed_add(
        "ab", "ac", "out", tag="distrib_left_products"
    )

    right_add_bc = signed_add("b", "c", "bc", tag="distrib_right_bc")
    right_mul_ba = signed_mul("b", "a", "ba", tag="distrib_right_ba")
    right_mul_ca = signed_mul("c", "a", "ca", tag="distrib_right_ca")
    right_mul_bca = signed_mul(
        "bc", "a", "out", tag="distrib_right_bca"
    )
    right_add_products = signed_add(
        "ba", "ca", "out", tag="distrib_right_products"
    )

    return (
        spec(
            "add_shuffle_middle",
            "forall a b c d. (a + b) + (c + d) = "
            "(a + c) + (b + d)",
            ("add_comm", "add_permute_outer"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans (b + a) + (c + d)",
                "congr",
                "apply add_comm",
                "refl",
                "trans (c + a) + (b + d)",
                "apply add_permute_outer",
                "congr",
                "apply add_comm",
                "refl",
            ),
            "Four additive contributions can be regrouped by swapping the "
            "middle pair.",
        ),
        spec(
            "add_cross_sum_pairwise",
            "forall a b c d e f g h. a + b = c + d -> "
            "e + f = g + h -> "
            "(a + e) + (b + f) = (c + g) + (d + h)",
            ("add_shuffle_middle",),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro h",
                "intro hfirst",
                "intro hsecond",
                "trans (a + b) + (e + f)",
                "symm",
                "apply add_shuffle_middle",
                "trans (c + d) + (g + h)",
                "congr",
                "exact hfirst",
                "exact hsecond",
                "apply add_shuffle_middle",
            ),
            "Two subtraction-free cross-sum equations compose componentwise.",
        ),
        spec(
            "signed_mul_distributive_component",
            "forall a b c d e f. "
            "a * (b + e) + c * (d + f) = "
            "(a * b + c * d) + (a * e + c * f)",
            ("mul_add", "add_shuffle_middle"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "trans (a * b + a * e) + (c * d + c * f)",
                "congr",
                "apply mul_add",
                "apply mul_add",
                "apply add_shuffle_middle",
            ),
            "One positive/negative component of a signed product "
            "distributes over a componentwise sum.",
        ),
        spec(
            "add_balance_outputs_compose",
            "forall p1 v1 n1 u1 p2 v2 n2 u2 w z. "
            "p1 + v1 = n1 + u1 -> p2 + v2 = n2 + u2 -> "
            "(p1 + p2) + w = (n1 + n2) + z -> "
            "(u1 + u2) + w = (v1 + v2) + z",
            ("add_cross_sum_pairwise", "add_cross_sum_chain", "add_comm"),
            (
                "intro p1",
                "intro v1",
                "intro n1",
                "intro u1",
                "intro p2",
                "intro v2",
                "intro n2",
                "intro u2",
                "intro w",
                "intro z",
                "intro hfirst",
                "intro hsecond",
                "intro htotal",
                "have hpair : "
                "(p1 + p2) + (v1 + v2) = "
                "(n1 + n2) + (u1 + u2)",
                "specialize add_cross_sum_pairwise p1",
                "specialize add_cross_sum_pairwise v1",
                "specialize add_cross_sum_pairwise n1",
                "specialize add_cross_sum_pairwise u1",
                "specialize add_cross_sum_pairwise p2",
                "specialize add_cross_sum_pairwise v2",
                "specialize add_cross_sum_pairwise n2",
                "specialize add_cross_sum_pairwise u2",
                "apply add_cross_sum_pairwise",
                "exact hfirst",
                "exact hsecond",
                "have hreordered : "
                "(u1 + u2) + (n1 + n2) = "
                "(v1 + v2) + (p1 + p2)",
                "trans (n1 + n2) + (u1 + u2)",
                "apply add_comm",
                "trans (p1 + p2) + (v1 + v2)",
                "symm",
                "exact hpair",
                "apply add_comm",
                "specialize add_cross_sum_chain (u1 + u2)",
                "specialize add_cross_sum_chain (v1 + v2)",
                "specialize add_cross_sum_chain (n1 + n2)",
                "specialize add_cross_sum_chain (p1 + p2)",
                "specialize add_cross_sum_chain w",
                "specialize add_cross_sum_chain z",
                "apply add_cross_sum_chain",
                "exact hreordered",
                "exact htotal",
            ),
            "Two balanced input equations transport their combined total "
            "equation to the output pair without subtraction.",
        ),
        spec(
            "signed_mul_left_cross_sum_distributes",
            "forall ap an bp bn cp cn bcp bcn. "
            "(bp + cp) + bcn = (bn + cn) + bcp -> "
            "(((ap * bp + an * bn) + (ap * cp + an * cn)) + "
            "(ap * bcn + an * bcp) = "
            "((ap * bn + an * bp) + (ap * cn + an * cp)) + "
            "(ap * bcp + an * bcn))",
            (
                "signed_pair_mul_cross_transport",
                "signed_mul_distributive_component",
            ),
            (
                "intro ap",
                "intro an",
                "intro bp",
                "intro bn",
                "intro cp",
                "intro cn",
                "intro bcp",
                "intro bcn",
                "intro hbc",
                "have hpair : "
                "((((bp + cp) * ap + (bn + cn) * an) + "
                "(bcp * an + bcn * ap) = "
                "((bp + cp) * an + (bn + cn) * ap) + "
                "(bcp * ap + bcn * an)) /\\ "
                "((ap * (bp + cp) + an * (bn + cn)) + "
                "(ap * bcn + an * bcp) = "
                "(ap * (bn + cn) + an * (bp + cp)) + "
                "(ap * bcp + an * bcn)))",
                "specialize signed_pair_mul_cross_transport (bp + cp)",
                "specialize signed_pair_mul_cross_transport (bn + cn)",
                "specialize signed_pair_mul_cross_transport bcp",
                "specialize signed_pair_mul_cross_transport bcn",
                "specialize signed_pair_mul_cross_transport ap",
                "specialize signed_pair_mul_cross_transport an",
                "apply signed_pair_mul_cross_transport",
                "exact hbc",
                "cases hpair",
                "have htransport : "
                "(ap * (bp + cp) + an * (bn + cn)) + "
                "(ap * bcn + an * bcp) = "
                "(ap * (bn + cn) + an * (bp + cp)) + "
                "(ap * bcp + an * bcn)",
                "exact hpair_right",
                "trans (ap * (bp + cp) + an * (bn + cn)) + "
                "(ap * bcn + an * bcp)",
                "congr",
                "symm",
                "specialize signed_mul_distributive_component ap",
                "specialize signed_mul_distributive_component bp",
                "specialize signed_mul_distributive_component an",
                "specialize signed_mul_distributive_component bn",
                "specialize signed_mul_distributive_component cp",
                "specialize signed_mul_distributive_component cn",
                "apply signed_mul_distributive_component",
                "refl",
                "trans (ap * (bn + cn) + an * (bp + cp)) + "
                "(ap * bcp + an * bcn)",
                "exact htransport",
                "congr",
                "specialize signed_mul_distributive_component ap",
                "specialize signed_mul_distributive_component bn",
                "specialize signed_mul_distributive_component an",
                "specialize signed_mul_distributive_component bp",
                "specialize signed_mul_distributive_component cn",
                "specialize signed_mul_distributive_component cp",
                "apply signed_mul_distributive_component",
                "refl",
            ),
            "The positive/negative contribution equation for a product "
            "respects a decoded signed sum in its right input.",
        ),
        spec(
            "signed_mul_left_distributive",
            "forall a b c bc ab ac out. "
            f"({add_bc}) -> ({mul_ab}) -> ({mul_ac}) -> ({mul_abc}) -> "
            f"({add_products})",
            (
                "signed_mul_to_decoded_equation",
                "add_balance_outputs_compose",
                "signed_mul_left_cross_sum_distributes",
                "add_cross_sum_chain",
                "signed_add_of_decoded_equation",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro bc",
                "intro ab",
                "intro ac",
                "intro out",
                "intro hbc",
                "intro hab",
                "intro hac",
                "intro hout",
                "cases hbc",
                "cases hbc_witness",
                "cases hbc_witness_witness",
                "cases hbc_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness_witness_witness",
                "cases "
                "hbc_witness_witness_witness_witness_witness_witness_right",
                "cases "
                "hbc_witness_witness_witness_witness_witness_witness_right_right",
                "cases hab",
                "cases hab_witness",
                "cases hab_witness_witness",
                "cases hab_witness_witness_witness",
                "cases hab_witness_witness_witness_witness",
                "cases hab_witness_witness_witness_witness_witness",
                "cases hab_witness_witness_witness_witness_witness_witness",
                "cases "
                "hab_witness_witness_witness_witness_witness_witness_right",
                "cases "
                "hab_witness_witness_witness_witness_witness_witness_right_right",
                "cases hac",
                "cases hac_witness",
                "cases hac_witness_witness",
                "cases hac_witness_witness_witness",
                "cases hac_witness_witness_witness_witness",
                "cases hac_witness_witness_witness_witness_witness",
                "cases hac_witness_witness_witness_witness_witness_witness",
                "cases "
                "hac_witness_witness_witness_witness_witness_witness_right",
                "cases "
                "hac_witness_witness_witness_witness_witness_witness_right_right",
                "cases hout",
                "cases hout_witness",
                "cases hout_witness_witness",
                "cases hout_witness_witness_witness",
                "cases hout_witness_witness_witness_witness",
                "cases hout_witness_witness_witness_witness_witness",
                "cases hout_witness_witness_witness_witness_witness_witness",
                "cases "
                "hout_witness_witness_witness_witness_witness_witness_right",
                "cases "
                "hout_witness_witness_witness_witness_witness_witness_right_right",
                "have hequation_ab : "
                "(x6 * x + x7 * x1) + x11 = "
                "(x6 * x1 + x7 * x) + x10",
                "specialize signed_mul_to_decoded_equation a",
                "specialize signed_mul_to_decoded_equation b",
                "specialize signed_mul_to_decoded_equation ab",
                "specialize signed_mul_to_decoded_equation x6",
                "specialize signed_mul_to_decoded_equation x7",
                "specialize signed_mul_to_decoded_equation x",
                "specialize signed_mul_to_decoded_equation x1",
                "specialize signed_mul_to_decoded_equation x10",
                "specialize signed_mul_to_decoded_equation x11",
                "apply signed_mul_to_decoded_equation",
                "exact "
                "hab_witness_witness_witness_witness_witness_witness_left",
                "exact "
                "hbc_witness_witness_witness_witness_witness_witness_left",
                "exact "
                "hab_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hab",
                "have hequation_ac : "
                "(x6 * x2 + x7 * x3) + x17 = "
                "(x6 * x3 + x7 * x2) + x16",
                "specialize signed_mul_to_decoded_equation a",
                "specialize signed_mul_to_decoded_equation c",
                "specialize signed_mul_to_decoded_equation ac",
                "specialize signed_mul_to_decoded_equation x6",
                "specialize signed_mul_to_decoded_equation x7",
                "specialize signed_mul_to_decoded_equation x2",
                "specialize signed_mul_to_decoded_equation x3",
                "specialize signed_mul_to_decoded_equation x16",
                "specialize signed_mul_to_decoded_equation x17",
                "apply signed_mul_to_decoded_equation",
                "exact "
                "hab_witness_witness_witness_witness_witness_witness_left",
                "exact "
                "hbc_witness_witness_witness_witness_witness_witness_right_left",
                "exact "
                "hac_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hac",
                "have hequation_out : "
                "(x6 * x4 + x7 * x5) + x23 = "
                "(x6 * x5 + x7 * x4) + x22",
                "specialize signed_mul_to_decoded_equation a",
                "specialize signed_mul_to_decoded_equation bc",
                "specialize signed_mul_to_decoded_equation out",
                "specialize signed_mul_to_decoded_equation x6",
                "specialize signed_mul_to_decoded_equation x7",
                "specialize signed_mul_to_decoded_equation x4",
                "specialize signed_mul_to_decoded_equation x5",
                "specialize signed_mul_to_decoded_equation x22",
                "specialize signed_mul_to_decoded_equation x23",
                "apply signed_mul_to_decoded_equation",
                "exact "
                "hab_witness_witness_witness_witness_witness_witness_left",
                "exact "
                "hbc_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact "
                "hout_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hout",
                "have hbalance : "
                "((x6 * x + x7 * x1) + (x6 * x2 + x7 * x3)) + "
                "(x6 * x5 + x7 * x4) = "
                "((x6 * x1 + x7 * x) + (x6 * x3 + x7 * x2)) + "
                "(x6 * x4 + x7 * x5)",
                "specialize signed_mul_left_cross_sum_distributes x6",
                "specialize signed_mul_left_cross_sum_distributes x7",
                "specialize signed_mul_left_cross_sum_distributes x",
                "specialize signed_mul_left_cross_sum_distributes x1",
                "specialize signed_mul_left_cross_sum_distributes x2",
                "specialize signed_mul_left_cross_sum_distributes x3",
                "specialize signed_mul_left_cross_sum_distributes x4",
                "specialize signed_mul_left_cross_sum_distributes x5",
                "apply signed_mul_left_cross_sum_distributes",
                "exact "
                "hbc_witness_witness_witness_witness_witness_witness_right_right_right",
                "have htotal : "
                "((x6 * x + x7 * x1) + (x6 * x2 + x7 * x3)) + "
                "x23 = "
                "((x6 * x1 + x7 * x) + (x6 * x3 + x7 * x2)) + x22",
                "specialize add_cross_sum_chain "
                "((x6 * x + x7 * x1) + (x6 * x2 + x7 * x3))",
                "specialize add_cross_sum_chain "
                "((x6 * x1 + x7 * x) + (x6 * x3 + x7 * x2))",
                "specialize add_cross_sum_chain "
                "(x6 * x5 + x7 * x4)",
                "specialize add_cross_sum_chain "
                "(x6 * x4 + x7 * x5)",
                "specialize add_cross_sum_chain x23",
                "specialize add_cross_sum_chain x22",
                "apply add_cross_sum_chain",
                "exact hbalance",
                "exact hequation_out",
                "have htarget : "
                "(x10 + x16) + x23 = (x11 + x17) + x22",
                "specialize add_balance_outputs_compose "
                "(x6 * x + x7 * x1)",
                "specialize add_balance_outputs_compose x11",
                "specialize add_balance_outputs_compose "
                "(x6 * x1 + x7 * x)",
                "specialize add_balance_outputs_compose x10",
                "specialize add_balance_outputs_compose "
                "(x6 * x2 + x7 * x3)",
                "specialize add_balance_outputs_compose x17",
                "specialize add_balance_outputs_compose "
                "(x6 * x3 + x7 * x2)",
                "specialize add_balance_outputs_compose x16",
                "specialize add_balance_outputs_compose x23",
                "specialize add_balance_outputs_compose x22",
                "apply add_balance_outputs_compose",
                "exact hequation_ab",
                "exact hequation_ac",
                "exact htotal",
                "specialize signed_add_of_decoded_equation ab",
                "specialize signed_add_of_decoded_equation ac",
                "specialize signed_add_of_decoded_equation out",
                "specialize signed_add_of_decoded_equation x10",
                "specialize signed_add_of_decoded_equation x11",
                "specialize signed_add_of_decoded_equation x16",
                "specialize signed_add_of_decoded_equation x17",
                "specialize signed_add_of_decoded_equation x22",
                "specialize signed_add_of_decoded_equation x23",
                "apply signed_add_of_decoded_equation",
                "exact "
                "hab_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact "
                "hac_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact "
                "hout_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact htarget",
            ),
            "Canonical signed multiplication distributes on the left over "
            "canonical signed addition.",
        ),
        spec(
            "signed_mul_right_distributive",
            "forall a b c bc ba ca out. "
            f"({right_add_bc}) -> ({right_mul_ba}) -> ({right_mul_ca}) -> "
            f"({right_mul_bca}) -> ({right_add_products})",
            (
                "signed_mul_commutative",
                "signed_mul_left_distributive",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro bc",
                "intro ba",
                "intro ca",
                "intro out",
                "intro hbc",
                "intro hba",
                "intro hca",
                "intro hout",
                "have hab : "
                f"({signed_mul('a', 'b', 'ba', tag='distrib_right_ab')})",
                "specialize signed_mul_commutative b",
                "specialize signed_mul_commutative a",
                "specialize signed_mul_commutative ba",
                "apply signed_mul_commutative",
                "exact hba",
                "have hac : "
                f"({signed_mul('a', 'c', 'ca', tag='distrib_right_ac')})",
                "specialize signed_mul_commutative c",
                "specialize signed_mul_commutative a",
                "specialize signed_mul_commutative ca",
                "apply signed_mul_commutative",
                "exact hca",
                "have haout : "
                f"({signed_mul('a', 'bc', 'out', tag='distrib_right_abc')})",
                "specialize signed_mul_commutative bc",
                "specialize signed_mul_commutative a",
                "specialize signed_mul_commutative out",
                "apply signed_mul_commutative",
                "exact hout",
                "specialize signed_mul_left_distributive a",
                "specialize signed_mul_left_distributive b",
                "specialize signed_mul_left_distributive c",
                "specialize signed_mul_left_distributive bc",
                "specialize signed_mul_left_distributive ba",
                "specialize signed_mul_left_distributive ca",
                "specialize signed_mul_left_distributive out",
                "apply signed_mul_left_distributive",
                "exact hbc",
                "exact hab",
                "exact hac",
                "exact haout",
            ),
            "Right distributivity follows by commuting each multiplication "
            "graph into the already checked left-distributive orientation.",
        ),
    )


__all__ = ["make_ha_signed_mul_distributive_candidate_theorems"]
