"""Strict-HA associativity candidates for canonical signed multiplication.

The tranche separates the natural-number algebra from the exact RFC D06
graph.  A reusable cross-equation transport lemma proves that equivalent
positive/negative pairs remain equivalent after multiplication on either
side.  A second lemma proves the two raw component identities for associating
pair multiplication.  The decoded associator composes those facts, and the
last theorem transports three exact ``SignedMul`` graphs through it.

Every relation occurrence expands hygienically into the unchanged
first-order language ``{0,S,+,*,=}``.  All proofs are constructive,
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_mul_candidate import signed_mul


def make_ha_signed_mul_associative_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build pair transport, component algebra, and D06 associativity."""

    mul_ab = signed_mul("a", "b", "ab", tag="assoc_ab")
    mul_abc = signed_mul("ab", "c", "abc", tag="assoc_abc")
    mul_bc = signed_mul("b", "c", "bc", tag="assoc_bc")
    mul_target = signed_mul("a", "bc", "abc", tag="assoc_target")

    return (
        spec(
            "signed_pair_mul_cross_transport",
            "forall p n u v cp cn. p + v = n + u -> "
            "(((p * cp + n * cn) + (u * cn + v * cp) = "
            "(p * cn + n * cp) + (u * cp + v * cn)) /\\ "
            "((cp * p + cn * n) + (cp * v + cn * u) = "
            "(cp * n + cn * p) + (cp * u + cn * v)))",
            ("add_mul", "mul_add", "add_comm", "add_permute_outer"),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro cp",
                "intro cn",
                "intro hcross",
                "have hshuffle : forall a b c d. "
                "(a + b) + (c + d) = (a + c) + (b + d)",
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
                "have hcp : p * cp + v * cp = n * cp + u * cp",
                "trans (p + v) * cp",
                "symm",
                "apply add_mul",
                "trans (n + u) * cp",
                "congr",
                "exact hcross",
                "refl",
                "apply add_mul",
                "have hcn : p * cn + v * cn = n * cn + u * cn",
                "trans (p + v) * cn",
                "symm",
                "apply add_mul",
                "trans (n + u) * cn",
                "congr",
                "exact hcross",
                "refl",
                "apply add_mul",
                "split",
                "trans (p * cp + n * cn) + (v * cp + u * cn)",
                "congr",
                "refl",
                "apply add_comm",
                "trans (p * cp + v * cp) + (n * cn + u * cn)",
                "apply hshuffle",
                "trans (n * cp + u * cp) + (n * cn + u * cn)",
                "congr",
                "exact hcp",
                "refl",
                "trans (n * cp + u * cp) + (p * cn + v * cn)",
                "congr",
                "refl",
                "symm",
                "exact hcn",
                "trans (n * cp + p * cn) + (u * cp + v * cn)",
                "apply hshuffle",
                "congr",
                "apply add_comm",
                "refl",
                "trans (cp * p + cp * v) + (cn * n + cn * u)",
                "apply hshuffle",
                "trans cp * (p + v) + cn * (n + u)",
                "congr",
                "symm",
                "apply mul_add",
                "symm",
                "apply mul_add",
                "trans cp * (n + u) + cn * (p + v)",
                "congr",
                "congr",
                "refl",
                "exact hcross",
                "congr",
                "refl",
                "symm",
                "exact hcross",
                "trans (cp * n + cp * u) + (cn * p + cn * v)",
                "congr",
                "apply mul_add",
                "apply mul_add",
                "apply hshuffle",
            ),
            "A subtraction-free pair equality is preserved by the signed "
            "pair-product formula on either the right or the left.",
        ),
        spec(
            "signed_pair_mul_components_associate",
            "forall ap an bp bn cp cn. "
            "((((ap * bp + an * bn) * cp + "
            "(ap * bn + an * bp) * cn) = "
            "ap * (bp * cp + bn * cn) + "
            "an * (bp * cn + bn * cp)) /\\ "
            "(((ap * bp + an * bn) * cn + "
            "(ap * bn + an * bp) * cp) = "
            "ap * (bp * cn + bn * cp) + "
            "an * (bp * cp + bn * cn)))",
            ("add_mul", "mul_add", "mul_assoc", "add_comm", "add_permute_outer"),
            (
                "intro ap",
                "intro an",
                "intro bp",
                "intro bn",
                "intro cp",
                "intro cn",
                "have hshuffle : forall a b c d. "
                "(a + b) + (c + d) = (a + c) + (b + d)",
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
                "split",
                "trans ((ap * bp) * cp + (an * bn) * cp) + "
                "((ap * bn) * cn + (an * bp) * cn)",
                "congr",
                "apply add_mul",
                "apply add_mul",
                "trans (ap * (bp * cp) + an * (bn * cp)) + "
                "(ap * (bn * cn) + an * (bp * cn))",
                "congr",
                "congr",
                "apply mul_assoc",
                "apply mul_assoc",
                "congr",
                "apply mul_assoc",
                "apply mul_assoc",
                "trans (ap * (bp * cp) + ap * (bn * cn)) + "
                "(an * (bn * cp) + an * (bp * cn))",
                "apply hshuffle",
                "trans ap * (bp * cp + bn * cn) + "
                "an * (bn * cp + bp * cn)",
                "congr",
                "symm",
                "apply mul_add",
                "symm",
                "apply mul_add",
                "congr",
                "refl",
                "congr",
                "refl",
                "apply add_comm",
                "trans ((ap * bp) * cn + (an * bn) * cn) + "
                "((ap * bn) * cp + (an * bp) * cp)",
                "congr",
                "apply add_mul",
                "apply add_mul",
                "trans (ap * (bp * cn) + an * (bn * cn)) + "
                "(ap * (bn * cp) + an * (bp * cp))",
                "congr",
                "congr",
                "apply mul_assoc",
                "apply mul_assoc",
                "congr",
                "apply mul_assoc",
                "apply mul_assoc",
                "trans (ap * (bp * cn) + ap * (bn * cp)) + "
                "(an * (bn * cn) + an * (bp * cp))",
                "apply hshuffle",
                "trans ap * (bp * cn + bn * cp) + "
                "an * (bn * cn + bp * cp)",
                "congr",
                "symm",
                "apply mul_add",
                "symm",
                "apply mul_add",
                "congr",
                "refl",
                "congr",
                "refl",
                "apply add_comm",
            ),
            "The positive and negative natural components of signed-pair "
            "multiplication associate before any decoder is involved.",
        ),
        spec(
            "signed_mul_equations_associate",
            "forall ap an bp bn cp cn abp abn bcp bcn outp outn. "
            "((ap * bp + an * bn) + abn = "
            "(ap * bn + an * bp) + abp) -> "
            "((abp * cp + abn * cn) + outn = "
            "(abp * cn + abn * cp) + outp) -> "
            "((bp * cp + bn * cn) + bcn = "
            "(bp * cn + bn * cp) + bcp) -> "
            "(ap * bcp + an * bcn) + outn = "
            "(ap * bcn + an * bcp) + outp",
            (
                "signed_pair_mul_cross_transport",
                "signed_pair_mul_components_associate",
                "add_cross_sum_chain",
                "add_comm",
            ),
            (
                "intro ap",
                "intro an",
                "intro bp",
                "intro bn",
                "intro cp",
                "intro cn",
                "intro abp",
                "intro abn",
                "intro bcp",
                "intro bcn",
                "intro outp",
                "intro outn",
                "intro hab",
                "intro habc",
                "intro hbc",
                "have hab_lift : "
                "((((ap * bp + an * bn) * cp + "
                "(ap * bn + an * bp) * cn) + "
                "(abp * cn + abn * cp) = "
                "((ap * bp + an * bn) * cn + "
                "(ap * bn + an * bp) * cp) + "
                "(abp * cp + abn * cn)) /\\ "
                "((cp * (ap * bp + an * bn) + "
                "cn * (ap * bn + an * bp)) + "
                "(cp * abn + cn * abp) = "
                "(cp * (ap * bn + an * bp) + "
                "cn * (ap * bp + an * bn)) + "
                "(cp * abp + cn * abn)))",
                "specialize signed_pair_mul_cross_transport "
                "(ap * bp + an * bn)",
                "specialize signed_pair_mul_cross_transport "
                "(ap * bn + an * bp)",
                "specialize signed_pair_mul_cross_transport abp",
                "specialize signed_pair_mul_cross_transport abn",
                "specialize signed_pair_mul_cross_transport cp",
                "specialize signed_pair_mul_cross_transport cn",
                "apply signed_pair_mul_cross_transport",
                "exact hab",
                "cases hab_lift",
                "have hraw_out : "
                "((ap * bp + an * bn) * cp + "
                "(ap * bn + an * bp) * cn) + outn = "
                "((ap * bp + an * bn) * cn + "
                "(ap * bn + an * bp) * cp) + outp",
                "specialize add_cross_sum_chain "
                "((ap * bp + an * bn) * cp + "
                "(ap * bn + an * bp) * cn)",
                "specialize add_cross_sum_chain "
                "((ap * bp + an * bn) * cn + "
                "(ap * bn + an * bp) * cp)",
                "specialize add_cross_sum_chain (abp * cn + abn * cp)",
                "specialize add_cross_sum_chain (abp * cp + abn * cn)",
                "specialize add_cross_sum_chain outn",
                "specialize add_cross_sum_chain outp",
                "apply add_cross_sum_chain",
                "exact hab_lift_left",
                "exact habc",
                "have hassoc : "
                "((((ap * bp + an * bn) * cp + "
                "(ap * bn + an * bp) * cn) = "
                "ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp)) /\\ "
                "(((ap * bp + an * bn) * cn + "
                "(ap * bn + an * bp) * cp) = "
                "ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn)))",
                "specialize signed_pair_mul_components_associate ap",
                "specialize signed_pair_mul_components_associate an",
                "specialize signed_pair_mul_components_associate bp",
                "specialize signed_pair_mul_components_associate bn",
                "specialize signed_pair_mul_components_associate cp",
                "specialize signed_pair_mul_components_associate cn",
                "exact signed_pair_mul_components_associate",
                "cases hassoc",
                "have hraw_bc_out : "
                "(ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp)) + outn = "
                "(ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn)) + outp",
                "trans ((ap * bp + an * bn) * cp + "
                "(ap * bn + an * bp) * cn) + outn",
                "congr",
                "symm",
                "exact hassoc_left",
                "refl",
                "trans ((ap * bp + an * bn) * cn + "
                "(ap * bn + an * bp) * cp) + outp",
                "exact hraw_out",
                "congr",
                "exact hassoc_right",
                "refl",
                "have hbc_lift : "
                "((((bp * cp + bn * cn) * ap + "
                "(bp * cn + bn * cp) * an) + "
                "(bcp * an + bcn * ap) = "
                "((bp * cp + bn * cn) * an + "
                "(bp * cn + bn * cp) * ap) + "
                "(bcp * ap + bcn * an)) /\\ "
                "((ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp)) + "
                "(ap * bcn + an * bcp) = "
                "(ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn)) + "
                "(ap * bcp + an * bcn)))",
                "specialize signed_pair_mul_cross_transport "
                "(bp * cp + bn * cn)",
                "specialize signed_pair_mul_cross_transport "
                "(bp * cn + bn * cp)",
                "specialize signed_pair_mul_cross_transport bcp",
                "specialize signed_pair_mul_cross_transport bcn",
                "specialize signed_pair_mul_cross_transport ap",
                "specialize signed_pair_mul_cross_transport an",
                "apply signed_pair_mul_cross_transport",
                "exact hbc",
                "cases hbc_lift",
                "have hbc_inverse : "
                "(ap * bcp + an * bcn) + "
                "(ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn)) = "
                "(ap * bcn + an * bcp) + "
                "(ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp))",
                "trans (ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn)) + "
                "(ap * bcp + an * bcn)",
                "apply add_comm",
                "trans (ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp)) + "
                "(ap * bcn + an * bcp)",
                "symm",
                "exact hbc_lift_right",
                "apply add_comm",
                "specialize add_cross_sum_chain (ap * bcp + an * bcn)",
                "specialize add_cross_sum_chain (ap * bcn + an * bcp)",
                "specialize add_cross_sum_chain "
                "(ap * (bp * cn + bn * cp) + "
                "an * (bp * cp + bn * cn))",
                "specialize add_cross_sum_chain "
                "(ap * (bp * cp + bn * cn) + "
                "an * (bp * cn + bn * cp))",
                "specialize add_cross_sum_chain outn",
                "specialize add_cross_sum_chain outp",
                "apply add_cross_sum_chain",
                "exact hbc_inverse",
                "exact hraw_bc_out",
            ),
            "The decoded contribution equations for both parenthesizations "
            "of a signed product imply the target product equation.",
        ),
        spec(
            "signed_mul_associative",
            "forall a b c ab bc abc. "
            f"({mul_ab}) -> ({mul_abc}) -> ({mul_bc}) -> ({mul_target})",
            (
                "signed_mul_to_decoded_equation",
                "signed_mul_equations_associate",
                "signed_mul_of_decoded_equation",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro ab",
                "intro bc",
                "intro abc",
                "intro hab",
                "intro habc",
                "intro hbc",
                "cases hab",
                "cases hab_witness",
                "cases hab_witness_witness",
                "cases hab_witness_witness_witness",
                "cases hab_witness_witness_witness_witness",
                "cases hab_witness_witness_witness_witness_witness",
                "cases hab_witness_witness_witness_witness_witness_witness",
                "cases hab_witness_witness_witness_witness_witness_witness_right",
                "cases hab_witness_witness_witness_witness_witness_witness_right_right",
                "cases habc",
                "cases habc_witness",
                "cases habc_witness_witness",
                "cases habc_witness_witness_witness",
                "cases habc_witness_witness_witness_witness",
                "cases habc_witness_witness_witness_witness_witness",
                "cases habc_witness_witness_witness_witness_witness_witness",
                "cases habc_witness_witness_witness_witness_witness_witness_right",
                "cases habc_witness_witness_witness_witness_witness_witness_right_right",
                "cases hbc",
                "cases hbc_witness",
                "cases hbc_witness_witness",
                "cases hbc_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness_witness_witness",
                "cases hbc_witness_witness_witness_witness_witness_witness_right",
                "cases hbc_witness_witness_witness_witness_witness_witness_right_right",
                "have hequation_abc : "
                "(x4 * x8 + x5 * x9) + x11 = "
                "(x4 * x9 + x5 * x8) + x10",
                "specialize signed_mul_to_decoded_equation ab",
                "specialize signed_mul_to_decoded_equation c",
                "specialize signed_mul_to_decoded_equation abc",
                "specialize signed_mul_to_decoded_equation x4",
                "specialize signed_mul_to_decoded_equation x5",
                "specialize signed_mul_to_decoded_equation x8",
                "specialize signed_mul_to_decoded_equation x9",
                "specialize signed_mul_to_decoded_equation x10",
                "specialize signed_mul_to_decoded_equation x11",
                "apply signed_mul_to_decoded_equation",
                "exact hab_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact habc_witness_witness_witness_witness_witness_witness_right_left",
                "exact habc_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact habc",
                "have hequation_bc : "
                "(x2 * x8 + x3 * x9) + x17 = "
                "(x2 * x9 + x3 * x8) + x16",
                "specialize signed_mul_to_decoded_equation b",
                "specialize signed_mul_to_decoded_equation c",
                "specialize signed_mul_to_decoded_equation bc",
                "specialize signed_mul_to_decoded_equation x2",
                "specialize signed_mul_to_decoded_equation x3",
                "specialize signed_mul_to_decoded_equation x8",
                "specialize signed_mul_to_decoded_equation x9",
                "specialize signed_mul_to_decoded_equation x16",
                "specialize signed_mul_to_decoded_equation x17",
                "apply signed_mul_to_decoded_equation",
                "exact hab_witness_witness_witness_witness_witness_witness_right_left",
                "exact habc_witness_witness_witness_witness_witness_witness_right_left",
                "exact hbc_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hbc",
                "have htarget_equation : "
                "(x * x16 + x1 * x17) + x11 = "
                "(x * x17 + x1 * x16) + x10",
                "specialize signed_mul_equations_associate x",
                "specialize signed_mul_equations_associate x1",
                "specialize signed_mul_equations_associate x2",
                "specialize signed_mul_equations_associate x3",
                "specialize signed_mul_equations_associate x8",
                "specialize signed_mul_equations_associate x9",
                "specialize signed_mul_equations_associate x4",
                "specialize signed_mul_equations_associate x5",
                "specialize signed_mul_equations_associate x16",
                "specialize signed_mul_equations_associate x17",
                "specialize signed_mul_equations_associate x10",
                "specialize signed_mul_equations_associate x11",
                "apply signed_mul_equations_associate",
                "exact hab_witness_witness_witness_witness_witness_witness_right_right_right",
                "exact hequation_abc",
                "exact hequation_bc",
                "specialize signed_mul_of_decoded_equation a",
                "specialize signed_mul_of_decoded_equation bc",
                "specialize signed_mul_of_decoded_equation abc",
                "specialize signed_mul_of_decoded_equation x",
                "specialize signed_mul_of_decoded_equation x1",
                "specialize signed_mul_of_decoded_equation x16",
                "specialize signed_mul_of_decoded_equation x17",
                "specialize signed_mul_of_decoded_equation x10",
                "specialize signed_mul_of_decoded_equation x11",
                "apply signed_mul_of_decoded_equation",
                "exact hab_witness_witness_witness_witness_witness_witness_left",
                "exact hbc_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact habc_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact htarget_equation",
            ),
            "Canonical signed multiplication is associative as an exact "
            "RFC D06 graph relation.",
        ),
    )


__all__ = ["make_ha_signed_mul_associative_candidate_theorems"]
