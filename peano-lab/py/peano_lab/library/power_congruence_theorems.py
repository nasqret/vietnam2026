"""Relational powers and balanced congruence in native Peano arithmetic.

This is an isolated, untrusted theorem-spec factory.  ``Pow`` and ``ModEq``
remain authoring names only: every public contract below is assembled from
the hygienic surfaces into an ordinary first-order PA formula, and every
script must replay through the independent kernel before admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation
from .quadratic_residue_surface import congruent_mod


def _mod_eq_terms(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand balanced congruence for trusted, module-owned term fragments."""

    return (
        f"exists pc_u_{tag} pc_v_{tag}. "
        f"({left}) + {modulus} * pc_u_{tag} = "
        f"({right}) + {modulus} * pc_v_{tag}"
    )


def make_power_congruence_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered relational-power congruence tranche."""

    one_power = power_relation("a", "e", "n", tag="one")
    one_carrier_power = power_relation("a", "e", "n", tag="one_carrier")
    one_predecessor = power_relation("a", "z", "r", tag="one_predecessor")
    one_step = f"exists r. ({one_predecessor}) /\\ n = r * a"

    pair_predecessor = power_relation("a", "e", "r", tag="pair_predecessor")
    pair_successor = power_relation("a", "se", "n", tag="pair_successor")
    decomposed_predecessor = power_relation(
        "a", "e", "z", tag="pair_decomposed"
    )
    pair_step = (
        f"exists z. ({decomposed_predecessor}) /\\ n = z * a"
    )

    base_congruence = congruent_mod("m", "a", "b", tag="base")
    left_power = power_relation("a", "e", "x", tag="left")
    right_power = power_relation("b", "e", "y", tag="right")
    result_congruence = congruent_mod("m", "x", "y", tag="result")
    power_congruence = (
        f"forall m a b e x y. ({base_congruence}) -> "
        f"({left_power}) -> ({right_power}) -> ({result_congruence})"
    )

    left_step = (
        f"exists r. ({power_relation('a', 'e', 'r', tag='left_step')}) /\\ "
        "x = r * a"
    )
    right_step = (
        f"exists r. ({power_relation('b', 'e', 'r', tag='right_step')}) /\\ "
        "y = r * b"
    )

    return (
        spec(
            "pow_one_from_zero_successor",
            f"forall a z e n. z = 0 -> e = S z -> "
            f"({one_carrier_power}) -> n = a",
            ("pow_successor_decompose", "pow_zero", "one_mul"),
            (
                "intro a",
                "intro z",
                "intro e",
                "intro n",
                "intro hz",
                "intro he",
                "intro hpow",
                f"have hstep : {one_step}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose z",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose n",
                "apply pow_successor_decompose",
                "exact he",
                "exact hpow",
                "cases hstep",
                "cases hstep_witness",
                "have hr : x = 1",
                "specialize pow_zero a",
                "specialize pow_zero z",
                "specialize pow_zero x",
                "apply pow_zero",
                "exact hz",
                "exact hstep_witness_left",
                "trans x * a",
                "exact hstep_witness_right",
                "rewrite hr",
                "specialize one_mul a",
                "exact one_mul",
            ),
            "A successor of a zero exponent gives the relational first power.",
        ),
        spec(
            "pow_one",
            f"forall a e n. e = 1 -> ({one_power}) -> n = a",
            ("pow_one_from_zero_successor",),
            (
                "intro a",
                "intro e",
                "intro n",
                "intro he",
                "intro hpow",
                "specialize pow_one_from_zero_successor a",
                "specialize pow_one_from_zero_successor 0",
                "specialize pow_one_from_zero_successor e",
                "specialize pow_one_from_zero_successor n",
                "apply pow_one_from_zero_successor",
                "refl",
                "exact he",
                "exact hpow",
            ),
            "The relational first power of a natural is the natural itself.",
        ),
        spec(
            "pow_successor_pair_mul",
            f"forall a e se r n. se = S e -> ({pair_predecessor}) -> "
            f"({pair_successor}) -> n = r * a",
            ("pow_successor_decompose", "pow_functional"),
            (
                "intro a",
                "intro e",
                "intro se",
                "intro r",
                "intro n",
                "intro hse",
                "intro hprevious",
                "intro hsuccessor",
                f"have hstep : {pair_step}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose se",
                "specialize pow_successor_decompose n",
                "apply pow_successor_decompose",
                "exact hse",
                "exact hsuccessor",
                "cases hstep",
                "cases hstep_witness",
                "have hz : x = r",
                "specialize pow_functional a",
                "specialize pow_functional e",
                "specialize pow_functional x",
                "specialize pow_functional r",
                "apply pow_functional",
                "exact hstep_witness_left",
                "exact hprevious",
                "trans x * a",
                "exact hstep_witness_right",
                "rewrite hz",
                "refl",
            ),
            "A successor power paired with its predecessor equals predecessor times base.",
        ),
        spec(
            "pow_mod_congruent",
            power_congruence,
            (
                "pow_zero",
                "pow_successor_decompose",
                "pow_successor_pair_mul",
                "mod_eq_refl",
                "mod_eq_mul",
            ),
            (
                "intro m",
                "intro a",
                "intro b",
                "induction e",
                "intro x",
                "intro y",
                "intro hab",
                "intro hx",
                "intro hy",
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
                "rewrite hx1",
                "rewrite hy1",
                "specialize mod_eq_refl m",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro x",
                "intro y",
                "intro hab",
                "intro hx",
                "intro hy",
                f"have hleft : {left_step}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "refl",
                "exact hx",
                "cases hleft",
                "cases hleft_witness",
                f"have hright : {right_step}",
                "specialize pow_successor_decompose b",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hright",
                "cases hright_witness",
                "have hxmul : x = x1 * a",
                "specialize pow_successor_pair_mul a",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul (S e)",
                "specialize pow_successor_pair_mul x1",
                "specialize pow_successor_pair_mul x",
                "apply pow_successor_pair_mul",
                "refl",
                "exact hleft_witness_left",
                "exact hx",
                "have hymul : y = x2 * b",
                "specialize pow_successor_pair_mul b",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul (S e)",
                "specialize pow_successor_pair_mul x2",
                "specialize pow_successor_pair_mul y",
                "apply pow_successor_pair_mul",
                "refl",
                "exact hright_witness_left",
                "exact hy",
                "have hpre : "
                f"{congruent_mod('m', 'x1', 'x2', tag='predecessors')}",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "exact hab",
                "exact hleft_witness_left",
                "exact hright_witness_left",
                "have hmul : "
                f"{_mod_eq_terms('m', 'x1 * a', 'x2 * b', tag='products')}",
                "specialize mod_eq_mul m",
                "specialize mod_eq_mul x1",
                "specialize mod_eq_mul x2",
                "specialize mod_eq_mul a",
                "specialize mod_eq_mul b",
                "apply mod_eq_mul",
                "exact hpre",
                "exact hab",
                "rewrite hxmul",
                "rewrite hymul",
                "exact hmul",
            ),
            "Balanced-congruent bases have congruent relational powers at every exponent.",
        ),
    )


__all__ = ["make_power_congruence_theorems"]
