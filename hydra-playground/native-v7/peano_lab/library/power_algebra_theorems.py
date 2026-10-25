"""Constructive algebra for the relational, beta-coded power operation.

This isolated theorem-spec factory is an untrusted authoring layer.  Every
``Pow`` occurrence is expanded by the hygienic finite-fold surface, and sum
or product exponents are represented by explicit equality carriers rather
than by adding a term former to the language or kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation


def _beta_at_terms(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists pa_h_{tag}. pa_h_{tag} + S ({value}) = {modulus}) /\\ "
        f"exists pa_q_{tag}. {code} = pa_q_{tag} * {modulus} + ({value}))"
    )


def _lt_terms(left: str, right: str, *, tag: str) -> str:
    return f"exists pa_lt_{tag}. pa_lt_{tag} + S {left} = {right}"


def _repeat_terms(
    code: str,
    scale: str,
    value: str,
    length: str,
    *,
    tag: str,
) -> str:
    i = f"pa_i_{tag}"
    bound = _lt_terms(i, length, tag=f"{tag}_bound")
    decoded = _beta_at_terms(
        code, scale, i, value, tag=f"{tag}_decoded"
    )
    return f"forall {i}. ({bound}) -> ({decoded})"


def _product_terms(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    u = f"pa_u_{tag}"
    v = f"pa_v_{tag}"
    i = f"pa_i_{tag}"
    p = f"pa_p_{tag}"
    r = f"pa_r_{tag}"
    s = f"pa_s_{tag}"
    start = _beta_at_terms(u, v, "0", "1", tag=f"{tag}_start")
    terminal = _beta_at_terms(
        u, v, length, result, tag=f"{tag}_terminal"
    )
    bound = _lt_terms(i, length, tag=f"{tag}_bound")
    factor = _beta_at_terms(code, scale, i, p, tag=f"{tag}_factor")
    partial = _beta_at_terms(u, v, i, r, tag=f"{tag}_partial")
    successor = _beta_at_terms(
        u, v, f"S {i}", s, tag=f"{tag}_successor"
    )
    return (
        f"exists {u} {v}. (({start}) /\\ (({terminal}) /\\ "
        f"forall {i}. ({bound}) -> exists {p} {r} {s}. "
        f"(({factor}) /\\ (({partial}) /\\ (({successor}) /\\ "
        f"{s} = {r} * {p})))))"
    )


def _power_terms(base: str, exponent: str, result: str, *, tag: str) -> str:
    """Expand Pow for trusted module-owned term fragments such as ``e + f``."""

    code = f"pa_b_{tag}"
    scale = f"pa_c_{tag}"
    repeated = _repeat_terms(
        code, scale, base, exponent, tag=f"{tag}_repeat"
    )
    product = _product_terms(
        code, scale, exponent, result, tag=f"{tag}_product"
    )
    return f"exists {code} {scale}. (({repeated}) /\\ ({product}))"


def make_power_algebra_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build square, additive-exponent, and multiplicative-exponent laws."""

    two_carrier_power = power_relation("a", "e", "n", tag="two_carrier")
    two_predecessor = power_relation("a", "o", "r", tag="two_predecessor")
    two_step = f"exists r. ({two_predecessor}) /\\ n = r * a"
    two_power = power_relation("a", "e", "n", tag="two")

    add_left = power_relation("a", "e", "x", tag="add_left")
    add_right = power_relation("a", "f", "y", tag="add_right")
    add_total = power_relation("a", "s", "z", tag="add_total")
    add_statement = (
        f"forall a e f s x y z. s = e + f -> ({add_left}) -> "
        f"({add_right}) -> ({add_total}) -> z = x * y"
    )

    mul_base = power_relation("a", "e", "x", tag="mul_base")
    mul_outer = power_relation("x", "f", "y", tag="mul_outer")
    mul_total = power_relation("a", "p", "z", tag="mul_total")
    mul_statement = (
        f"forall a e f p x y z. p = e * f -> ({mul_base}) -> "
        f"({mul_outer}) -> ({mul_total}) -> y = z"
    )

    return (
        spec(
            "pow_two_from_one_successor",
            f"forall a o e n. o = 1 -> e = S o -> "
            f"({two_carrier_power}) -> n = a * a",
            ("pow_successor_decompose", "pow_one"),
            (
                "intro a",
                "intro o",
                "intro e",
                "intro n",
                "intro ho",
                "intro he",
                "intro hpow",
                f"have hstep : {two_step}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose o",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose n",
                "apply pow_successor_decompose",
                "exact he",
                "exact hpow",
                "cases hstep",
                "cases hstep_witness",
                "have hr : x = a",
                "specialize pow_one a",
                "specialize pow_one o",
                "specialize pow_one x",
                "apply pow_one",
                "exact ho",
                "exact hstep_witness_left",
                "trans x * a",
                "exact hstep_witness_right",
                "rewrite hr",
                "refl",
            ),
            "A successor of exponent one gives the relational square.",
        ),
        spec(
            "pow_two",
            f"forall a e n. e = 2 -> ({two_power}) -> n = a * a",
            ("pow_two_from_one_successor",),
            (
                "intro a",
                "intro e",
                "intro n",
                "intro he",
                "intro hpow",
                "specialize pow_two_from_one_successor a",
                "specialize pow_two_from_one_successor 1",
                "specialize pow_two_from_one_successor e",
                "specialize pow_two_from_one_successor n",
                "apply pow_two_from_one_successor",
                "refl",
                "exact he",
                "exact hpow",
            ),
            "The relational second power is exactly the square.",
        ),
        spec(
            "pow_add",
            add_statement,
            (
                "pow_zero",
                "pow_functional",
                "pow_successor_decompose",
                "mul_one",
                "mul_assoc",
            ),
            (
                "intro a",
                "intro e",
                "induction f",
                "intro s",
                "intro x",
                "intro y",
                "intro z",
                "intro hs",
                "intro hx",
                "intro hy",
                "intro hz",
                "rewrite PA3 at hs",
                "rewrite hs at hz",
                "rewrite hs at hz",
                "rewrite hs at hz",
                "rewrite hs at hz",
                "have hzx : z = x",
                "specialize pow_functional a",
                "specialize pow_functional e",
                "specialize pow_functional z",
                "specialize pow_functional x",
                "apply pow_functional",
                "exact hz",
                "exact hx",
                "have hy1 : y = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero y",
                "apply pow_zero",
                "refl",
                "exact hy",
                "rewrite hzx",
                "rewrite hy1",
                "specialize mul_one x",
                "symm",
                "exact mul_one",
                "intro s",
                "intro x",
                "intro y",
                "intro z",
                "intro hs",
                "intro hx",
                "intro hy",
                "intro hz",
                "have hy_step : exists r. "
                f"({power_relation('a', 'f', 'r', tag='add_y_prefix')}) /\\ "
                "y = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose f",
                "specialize pow_successor_decompose (S f)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hy_step",
                "cases hy_step_witness",
                "have hst : s = S (e + f)",
                "trans e + S f",
                "exact hs",
                "apply PA4",
                "have hz_step : exists r. "
                f"({_power_terms('a', 'e + f', 'r', tag='add_z_prefix')}) /\\ "
                "z = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose (e + f)",
                "specialize pow_successor_decompose s",
                "specialize pow_successor_decompose z",
                "apply pow_successor_decompose",
                "exact hst",
                "exact hz",
                "cases hz_step",
                "cases hz_step_witness",
                "have hprefix : x2 = x * x1",
                "specialize IH (e + f)",
                "specialize IH x",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "refl",
                "exact hx",
                "exact hy_step_witness_left",
                "exact hz_step_witness_left",
                "trans x2 * a",
                "exact hz_step_witness_right",
                "trans (x * x1) * a",
                "congr",
                "exact hprefix",
                "refl",
                "trans x * (x1 * a)",
                "apply mul_assoc",
                "congr",
                "refl",
                "symm",
                "exact hy_step_witness_right",
            ),
            "Relational powers turn addition of exponents into multiplication.",
        ),
        spec(
            "pow_mul_exp",
            mul_statement,
            (
                "pow_zero",
                "pow_successor_decompose",
                "pow_exists",
                "pow_add",
            ),
            (
                "intro a",
                "intro e",
                "induction f",
                "intro p",
                "intro x",
                "intro y",
                "intro z",
                "intro hp",
                "intro hx",
                "intro hy",
                "intro hz",
                "rewrite PA5 at hp",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "rewrite hp at hz",
                "have hy1 : y = 1",
                "specialize pow_zero x",
                "specialize pow_zero 0",
                "specialize pow_zero y",
                "apply pow_zero",
                "refl",
                "exact hy",
                "have hz1 : z = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero z",
                "apply pow_zero",
                "refl",
                "exact hz",
                "trans 1",
                "exact hy1",
                "symm",
                "exact hz1",
                "intro p",
                "intro x",
                "intro y",
                "intro z",
                "intro hp",
                "intro hx",
                "intro hy",
                "intro hz",
                "have hy_step : exists r. "
                f"({power_relation('x', 'f', 'r', tag='mul_y_prefix')}) /\\ "
                "y = r * x",
                "specialize pow_successor_decompose x",
                "specialize pow_successor_decompose f",
                "specialize pow_successor_decompose (S f)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hy_step",
                "cases hy_step_witness",
                "have hqpow : exists r. "
                f"({_power_terms('a', 'e * f', 'r', tag='mul_total_prefix')})",
                "specialize pow_exists a",
                "specialize pow_exists (e * f)",
                "exact pow_exists",
                "cases hqpow",
                "have hprefix : x1 = x2",
                "specialize IH (e * f)",
                "specialize IH x",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "refl",
                "exact hx",
                "exact hy_step_witness_left",
                "exact hqpow_witness",
                "have hpsum : p = (e * f) + e",
                "trans e * S f",
                "exact hp",
                "apply PA6",
                "have htotal : z = x2 * x",
                "specialize pow_add a",
                "specialize pow_add (e * f)",
                "specialize pow_add e",
                "specialize pow_add p",
                "specialize pow_add x2",
                "specialize pow_add x",
                "specialize pow_add z",
                "apply pow_add",
                "exact hpsum",
                "exact hqpow_witness",
                "exact hx",
                "exact hz",
                "trans x1 * x",
                "exact hy_step_witness_right",
                "trans x2 * x",
                "congr",
                "exact hprefix",
                "refl",
                "symm",
                "exact htotal",
            ),
            "Iterated relational powers multiply their exponents.",
        ),
    )


__all__ = ["make_power_algebra_theorems"]
