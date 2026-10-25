"""Integer-coefficient Hensel lifting via exact natural polynomial recoding.

A signed polynomial is an arbitrary pair of finite natural coefficient
prefixes, interpreted by their difference.  No coefficient normalization or
subtraction primitive is required.  For a desired modulus M=S h, the actual
natural recoding G=Fplus+h*Fminus preserves the signed value and derivative
modulo M.  All recoding, linearity, and lifting statements are ordinary HA.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import repeat_relation
from .fermat_residue_product_candidate import prime
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .finite_sum_theorems import _at
from .hensel_prime_power_candidate import (
    _arguments as _natural_arguments,
    _call,
    _cop,
    _eval,
    _lift as _natural_lift,
    _lt,
    _mod,
    _pair,
    _power,
    _root as _natural_root,
    _safe as _natural_safe,
)
from .matrix_coded_product_candidate import pointwise_add_prefix_relation


class SignedHenselError(ValueError):
    """A signed-polynomial abbreviation is invalid or captures an argument."""


def _safe(tag: str) -> str:
    try:
        return _natural_safe(tag)
    except ValueError as error:
        raise SignedHenselError(str(error)) from error


def _arguments(*values: str) -> tuple[str, ...]:
    try:
        result = _natural_arguments(*values)
        if any(value.startswith(("sph_", "mcp_", "fpmp_")) for value in result):
            raise ValueError("generated signed-Hensel binder captures an argument")
        return result
    except ValueError as error:
        raise SignedHenselError(str(error)) from error


def _blend(
    pb: str, pc: str, nb: str, nc: str, gb: str, gc: str,
    h: str, l: str, *, tag: str = "blend",
) -> str:
    i, A, B, C = (f"sph_{name}_{_safe(tag)}" for name in ("i", "A", "B", "C"))
    return (
        f"forall {i} {A} {B} {C}. ({_lt(i, l, tag=tag)}) -> "
        f"({_at(pb, pc, i, A, tag=f'sph_{tag}_positive')}) -> "
        f"({_at(nb, nc, i, B, tag=f'sph_{tag}_negative')}) -> "
        f"({_at(gb, gc, i, C, tag=f'sph_{tag}_combined')}) -> {C} = {A} + {h} * {B}"
    )


def horner_coefficient_blend_relation(
    positive_code: str, positive_scale: str, negative_code: str, negative_scale: str,
    combined_code: str, combined_scale: str, weight: str, length: str, *, tag: str,
) -> str:
    """An actual finite coefficient prefix equals positive+weight*negative."""

    return _blend(*_arguments(
        positive_code, positive_scale, negative_code, negative_scale,
        combined_code, combined_scale, weight, length,
    ), tag=_safe(tag))


def _signed_pair(
    pb: str, pc: str, nb: str, nc: str, a: str, l: str,
    vp: str, dp: str, vn: str, dn: str, *, tag: str = "pair",
) -> str:
    return (
        f"(({_pair(pb, pc, a, l, vp, dp, tag=f'sph_{tag}_positive')}) /\\ "
        f"({_pair(nb, nc, a, l, vn, dn, tag=f'sph_{tag}_negative')}))"
    )


def signed_horner_value_derivative_relation(
    positive_code: str, positive_scale: str, negative_code: str, negative_scale: str,
    point: str, length: str, positive_value: str, positive_derivative: str,
    negative_value: str, negative_derivative: str, *, tag: str,
) -> str:
    """Two actual natural Horner pairs represent the integer value/derivative."""

    return _signed_pair(*_arguments(
        positive_code, positive_scale, negative_code, negative_scale, point, length,
        positive_value, positive_derivative, negative_value, negative_derivative,
    ), tag=_safe(tag))


def _unit(p: str, dp: str, dn: str, *, tag: str = "unit") -> str:
    u = f"sph_inverse_{_safe(tag)}"
    return (
        f"exists {u}. (({_lt(u, p, tag=tag)}) /\\ "
        f"({_mod(p, f'{dp} * {u}', f'1 + {dn} * {u}', tag=tag)}))"
    )


def signed_derivative_unit_relation(
    modulus: str, positive_derivative: str, negative_derivative: str, *, tag: str,
) -> str:
    """A bounded inverse of the signed derivative, using balanced congruence."""

    return _unit(*_arguments(modulus, positive_derivative, negative_derivative), tag=_safe(tag))


def _root(
    pb: str, pc: str, nb: str, nc: str, a: str, l: str, m: str, *, tag: str = "root",
) -> str:
    vp, vn = f"sph_positive_{_safe(tag)}", f"sph_negative_{_safe(tag)}"
    return (
        f"exists {vp} {vn}. (({_eval(pb, pc, a, l, vp, tag=f'sph_{tag}_positive')}) /\\ "
        f"(({_eval(nb, nc, a, l, vn, tag=f'sph_{tag}_negative')}) /\\ ({_mod(m, vp, vn, tag=tag)})))"
    )


def signed_horner_root_relation(
    positive_code: str, positive_scale: str, negative_code: str, negative_scale: str,
    point: str, length: str, modulus: str, *, tag: str,
) -> str:
    """An integer polynomial is a root exactly when its two values agree modulo m."""

    return _root(*_arguments(
        positive_code, positive_scale, negative_code, negative_scale,
        point, length, modulus,
    ), tag=_safe(tag))


def _simple(
    pb: str, pc: str, nb: str, nc: str, a: str, l: str, m: str, p: str,
    *, tag: str = "simple",
) -> str:
    vp, dp, vn, dn = (f"sph_{name}_{_safe(tag)}" for name in ("vp", "dp", "vn", "dn"))
    return (
        f"exists {vp} {dp} {vn} {dn}. "
        f"(({_signed_pair(pb, pc, nb, nc, a, l, vp, dp, vn, dn, tag=tag)}) /\\ "
        f"(({_mod(m, vp, vn, tag=tag)}) /\\ ({_unit(p, dp, dn, tag=tag)})))"
    )


def signed_simple_horner_root_relation(
    positive_code: str, positive_scale: str, negative_code: str, negative_scale: str,
    point: str, length: str, root_modulus: str, derivative_modulus: str, *, tag: str,
) -> str:
    """An actual integer-polynomial root with an actual invertible derivative."""

    return _simple(*_arguments(
        positive_code, positive_scale, negative_code, negative_scale,
        point, length, root_modulus, derivative_modulus,
    ), tag=_safe(tag))


def _lift(
    pb: str, pc: str, nb: str, nc: str, l: str, m: str, a: str, M: str, r: str,
    *, tag: str = "lift",
) -> str:
    return (
        f"(({_lt(r, M, tag=tag)}) /\\ (({_mod(m, r, a, tag=tag)}) /\\ "
        f"({_root(pb, pc, nb, nc, r, l, M, tag=tag)})))"
    )


def canonical_signed_horner_lift_relation(
    positive_code: str, positive_scale: str, negative_code: str, negative_scale: str,
    length: str, old_modulus: str, source_point: str, new_modulus: str, lift_point: str,
    *, tag: str,
) -> str:
    """A unique-lift candidate for an arbitrary integer-coefficient polynomial."""

    return _lift(*_arguments(
        positive_code, positive_scale, negative_code, negative_scale,
        length, old_modulus, source_point, new_modulus, lift_point,
    ), tag=_safe(tag))


def _decomposition(b: str, c: str, a: str, l: str, v: str, d: str, *, tag: str) -> str:
    A, R, D = (f"sph_{name}_{_safe(tag)}" for name in ("coefficient", "value", "derivative"))
    return (
        f"exists {A} {R} {D}. (({_at(b, c, l, A, tag=f'sph_{tag}_coefficient')}) /\\ "
        f"(({_pair(b, c, a, l, R, D, tag=f'sph_{tag}_prefix')}) /\\ "
        f"({v} = {R} * {a} + {A} /\\ {d} = {D} * {a} + {R})))"
    )


def make_signed_hensel_lifting_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Construct signed-polynomial bridge proofs without admitting an edition."""

    return (
        spec(
            "beta_horner_coefficient_blend_exists",
            f"forall pb pc nb nc h l. exists gb gc. ({_blend('pb', 'pc', 'nb', 'nc', 'gb', 'gc', 'h', 'l')})",
            ("beta_repeat_exists", "beta_pointwise_mul_prefix_exists", "beta_pointwise_add_prefix_exists", "beta_at_exists"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro h", "intro l",
                f"have hrepeated : exists rb rc. ({repeat_relation('rb', 'rc', 'h', 'l', tag='sph_repeat')})",
                *_call("beta_repeat_exists", "h", "l"), "cases hrepeated", "cases hrepeated_witness",
                f"have hscaled : exists sb sc. ({pointwise_mul_prefix('x', 'x1', 'nb', 'nc', 'sb', 'sc', 'l', tag='sph_scale')})",
                *_call("beta_pointwise_mul_prefix_exists", "x", "x1", "nb", "nc", "l"), "cases hscaled", "cases hscaled_witness",
                f"have hadded : exists gb gc. ({pointwise_add_prefix_relation('pb', 'pc', 'x2', 'x3', 'gb', 'gc', 'l', tag='sph_add')})",
                *_call("beta_pointwise_add_prefix_exists", "pb", "pc", "x2", "x3", "l"), "cases hadded", "cases hadded_witness",
                "exists x4", "exists x5", "intro i", "intro A", "intro B", "intro C", "intro hi", "intro hA", "intro hB", "intro hC",
                f"have hentry : exists w. ({_at('x2', 'x3', 'i', 'w', tag='sph_entry')})",
                *_call("beta_at_exists", "x2", "x3", "i"), "cases hentry",
                "have hscale : x6 = h * B", "specialize hscaled_witness_witness i", "specialize hscaled_witness_witness h",
                "specialize hscaled_witness_witness B", "specialize hscaled_witness_witness x6", "apply hscaled_witness_witness",
                "exact hi", "specialize hrepeated_witness_witness i", "apply hrepeated_witness_witness", "exact hi", "exact hB", "exact hentry_witness",
                "trans A + x6", "specialize hadded_witness_witness i", "specialize hadded_witness_witness A",
                "specialize hadded_witness_witness x6", "specialize hadded_witness_witness C", "apply hadded_witness_witness",
                "exact hi", "exact hA", "exact hentry_witness", "exact hC", "rewrite hscale", "refl",
            ),
            "Every pair of finite integer-coefficient component codes admits an actual natural positive+weight*negative coefficient code.",
        ),
        spec(
            "hensel_horner_linear_successor_identity",
            "forall h a u v A B. (u + h * v) * a + (A + h * B) = (u * a + A) + h * (v * a + B)",
            ("add_mul", "mul_add", "mul_assoc", "add_shuffle_middle"),
            (
                "intro h", "intro a", "intro u", "intro v", "intro A", "intro B",
                "trans (u * a + (h * v) * a) + (A + h * B)", "congr", "apply add_mul", "refl",
                "trans (u * a + A) + ((h * v) * a + h * B)", "apply add_shuffle_middle", "congr", "refl",
                "trans h * (v * a) + h * B", "congr", "apply mul_assoc", "refl", "symm", "apply mul_add",
            ),
            "Both the Horner value and derivative transitions preserve an exact weighted coefficient combination.",
        ),
        spec(
            "beta_horner_coefficient_blend_value_derivative",
            f"forall pb pc nb nc gb gc h a l vp dp vn dn vg dg. "
            f"({_blend('pb', 'pc', 'nb', 'nc', 'gb', 'gc', 'h', 'l')}) -> "
            f"({_pair('pb', 'pc', 'a', 'l', 'vp', 'dp')}) -> ({_pair('nb', 'nc', 'a', 'l', 'vn', 'dn')}) -> "
            f"({_pair('gb', 'gc', 'a', 'l', 'vg', 'dg')}) -> vg = vp + h * vn /\\ dg = dp + h * dn",
            ("beta_horner_derivative_empty", "beta_horner_derivative_successor_decompose", "le_succ", "le_refl", "hensel_horner_linear_successor_identity"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro gb", "intro gc", "intro h", "intro a", "induction l",
                "intro vp", "intro dp", "intro vn", "intro dn", "intro vg", "intro dg", "intro hblend", "intro hpositive", "intro hnegative", "intro hcombined",
                "have hP : vp = 0 /\\ dp = 0", *_call("beta_horner_derivative_empty", "pb", "pc", "a", "vp", "dp"), "exact hpositive", "cases hP",
                "have hN : vn = 0 /\\ dn = 0", *_call("beta_horner_derivative_empty", "nb", "nc", "a", "vn", "dn"), "exact hnegative", "cases hN",
                "have hG : vg = 0 /\\ dg = 0", *_call("beta_horner_derivative_empty", "gb", "gc", "a", "vg", "dg"), "exact hcombined", "cases hG", "split",
                "rewrite hG_left", "rewrite hP_left", "rewrite hN_left", "simp",
                "rewrite hG_right", "rewrite hP_right", "rewrite hN_right", "simp",
                "intro vp", "intro dp", "intro vn", "intro dn", "intro vg", "intro dg", "intro hblend", "intro hpositive", "intro hnegative", "intro hcombined",
                f"have hP : {_decomposition('pb', 'pc', 'a', 'l', 'vp', 'dp', tag='positive')}",
                *_call("beta_horner_derivative_successor_decompose", "pb", "pc", "a", "l", "vp", "dp"), "exact hpositive",
                "cases hP", "cases hP_witness", "cases hP_witness_witness", "cases hP_witness_witness_witness", "cases hP_witness_witness_witness_right", "cases hP_witness_witness_witness_right_right",
                f"have hN : {_decomposition('nb', 'nc', 'a', 'l', 'vn', 'dn', tag='negative')}",
                *_call("beta_horner_derivative_successor_decompose", "nb", "nc", "a", "l", "vn", "dn"), "exact hnegative",
                "cases hN", "cases hN_witness", "cases hN_witness_witness", "cases hN_witness_witness_witness", "cases hN_witness_witness_witness_right", "cases hN_witness_witness_witness_right_right",
                f"have hG : {_decomposition('gb', 'gc', 'a', 'l', 'vg', 'dg', tag='combined')}",
                *_call("beta_horner_derivative_successor_decompose", "gb", "gc", "a", "l", "vg", "dg"), "exact hcombined",
                "cases hG", "cases hG_witness", "cases hG_witness_witness", "cases hG_witness_witness_witness", "cases hG_witness_witness_witness_right", "cases hG_witness_witness_witness_right_right",
                f"have hprefix_blend : {_blend('pb', 'pc', 'nb', 'nc', 'gb', 'gc', 'h', 'l')}",
                "intro i", "intro A", "intro B", "intro C", "intro hi", "intro hA", "intro hB", "intro hC",
                "specialize hblend i", "specialize hblend A", "specialize hblend B", "specialize hblend C", "apply hblend",
                *_call("le_succ", "(S i)", "l"), "exact hi", "exact hA", "exact hB", "exact hC",
                "have hprefix : x7 = x1 + h * x4 /\\ x8 = x2 + h * x5",
                "specialize IH x1", "specialize IH x2", "specialize IH x4", "specialize IH x5", "specialize IH x7", "specialize IH x8", "apply IH",
                "exact hprefix_blend", "exact hP_witness_witness_witness_right_left", "exact hN_witness_witness_witness_right_left", "exact hG_witness_witness_witness_right_left", "cases hprefix",
                "have hlast : x6 = x + h * x3", "specialize hblend l", "specialize hblend x", "specialize hblend x3", "specialize hblend x6", "apply hblend",
                *_call("le_refl", "(S l)"), "exact hP_witness_witness_witness_left", "exact hN_witness_witness_witness_left", "exact hG_witness_witness_witness_left", "split",
                "rewrite hG_witness_witness_witness_right_right_left", "rewrite hP_witness_witness_witness_right_right_left", "rewrite hN_witness_witness_witness_right_right_left",
                "rewrite hprefix_left", "rewrite hlast", *_call("hensel_horner_linear_successor_identity", "h", "a", "x1", "x4", "x", "x3"),
                "rewrite hG_witness_witness_witness_right_right_right", "rewrite hP_witness_witness_witness_right_right_right", "rewrite hN_witness_witness_witness_right_right_right",
                "rewrite hprefix_right", "rewrite hprefix_left", *_call("hensel_horner_linear_successor_identity", "h", "a", "x2", "x5", "x1", "x4"),
            ),
            "For every finite coefficient list, the actual recoded polynomial and its actual formal derivative are the exact weighted combinations of their signed components.",
        ),
    ) + _make_modular_bridge_theorems(spec) + _make_root_bridge_theorems(spec) + _make_signed_lifting_theorems(spec)


def _make_modular_bridge_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "hensel_signed_blend_balance",
            "forall h A B. (A + h * B) + B = A + (S h) * B",
            ("add_assoc", "mul_comm"),
            (
                "intro h", "intro A", "intro B", "trans A + (h * B + B)", "apply add_assoc", "congr", "refl", "symm",
                "trans B * S h", "apply mul_comm", "rewrite PA6", "congr", "apply mul_comm", "refl",
            ),
            "The natural recoding and its negative component balance to the positive component plus a full modulus multiple.",
        ),
        spec(
            "hensel_signed_blend_mod_iff",
            f"forall m M h A B C R. M = S h -> (exists q. M = m * q) -> C = A + h * B -> "
            f"((({_mod('m', 'C', 'R')}) -> ({_mod('m', 'A', 'R + B')})) /\\ "
            f"(({_mod('m', 'A', 'R + B')}) -> ({_mod('m', 'C', 'R')})))",
            ("hensel_signed_blend_balance", "multiple_mul_right", "multiple_implies_balanced_zero_congruence", "mod_eq_add", "mod_eq_refl", "mod_eq_trans", "mod_eq_symm", "mod_eq_add_cancel_right"),
            (
                "intro m", "intro M", "intro h", "intro A", "intro B", "intro C", "intro R", "intro hM", "intro hdiv", "intro hC",
                "have hbalance : C + B = A + M * B", "rewrite hC", "rewrite hM", *_call("hensel_signed_blend_balance", "h", "A", "B"),
                f"have hmultiple : {_mod('m', 'M * B', '0')}",
                *_call("multiple_implies_balanced_zero_congruence", "m", "(M * B)"), *_call("multiple_mul_right", "m", "M", "B"), "exact hdiv",
                f"have hdrop : {_mod('m', 'A + M * B', 'A + 0')}",
                *_call("mod_eq_add", "m", "A", "A", "(M * B)", "0"), *_call("mod_eq_refl", "m", "A"), "exact hmultiple",
                "have hzero : A + 0 = A", "simp", "rewrite hzero at hdrop", "split", "intro hsource",
                *_call("mod_eq_trans", "m", "A", "(A + M * B)", "(R + B)"),
                *_call("mod_eq_symm", "m", "(A + M * B)", "A"), "exact hdrop", "rewrite <- hbalance",
                *_call("mod_eq_add", "m", "C", "R", "B", "B"), "exact hsource", *_call("mod_eq_refl", "m", "B"),
                "intro hsource", *_call("mod_eq_add_cancel_right", "m", "C", "R", "B"), "rewrite hbalance",
                *_call("mod_eq_trans", "m", "(A + M * B)", "A", "(R + B)"), "exact hdrop", "exact hsource",
            ),
            "Natural recoding preserves every signed residue modulo every divisor of the selected final modulus.",
        ),
        spec(
            "hensel_signed_blend_zero_iff",
            f"forall m M h A B C. M = S h -> (exists q. M = m * q) -> C = A + h * B -> "
            f"((({_mod('m', 'C', '0')}) -> ({_mod('m', 'A', 'B')})) /\\ "
            f"(({_mod('m', 'A', 'B')}) -> ({_mod('m', 'C', '0')})))",
            ("hensel_signed_blend_mod_iff", "zero_add"),
            (
                "intro m", "intro M", "intro h", "intro A", "intro B", "intro C", "intro hM", "intro hdiv", "intro hC",
                f"have hiff : ((({_mod('m', 'C', '0')}) -> ({_mod('m', 'A', '0 + B')})) /\\ (({_mod('m', 'A', '0 + B')}) -> ({_mod('m', 'C', '0')})))",
                *_call("hensel_signed_blend_mod_iff", "m", "M", "h", "A", "B", "C", "0"), "exact hM", "exact hdiv", "exact hC",
                "have hzero : 0 + B = B", "apply zero_add", "rewrite hzero at hiff", "rewrite hzero at hiff", "exact hiff",
            ),
            "The recoded natural value is zero modulo an old or new modulus exactly when the original signed value is zero there.",
        ),
        spec(
            "hensel_signed_blend_unit_coprime",
            f"forall p M h dp dn dg. M = S h -> (exists q. M = p * q) -> "
            f"dg = dp + h * dn -> ({_unit('p', 'dp', 'dn')}) -> ({_cop('dg', 'p')})",
            ("hensel_signed_blend_mod_iff", "mod_inverse_implies_coprime", "add_mul", "mul_assoc"),
            (
                "intro p", "intro M", "intro h", "intro dp", "intro dn", "intro dg", "intro hM", "intro hdiv", "intro hdg", "intro hunit",
                "cases hunit", "cases hunit_witness",
                "have hproduct : dg * x = dp * x + h * (dn * x)", "rewrite hdg",
                "trans dp * x + (h * dn) * x", "apply add_mul", "congr", "refl", "apply mul_assoc",
                f"have hiff : ((({_mod('p', 'dg * x', '1')}) -> ({_mod('p', 'dp * x', '1 + dn * x')})) /\\ (({_mod('p', 'dp * x', '1 + dn * x')}) -> ({_mod('p', 'dg * x', '1')})))",
                *_call("hensel_signed_blend_mod_iff", "p", "M", "h", "(dp * x)", "(dn * x)", "(dg * x)", "1"),
                "exact hM", "exact hdiv", "exact hproduct", "cases hiff",
                *_call("mod_inverse_implies_coprime", "dg", "p", "x"), "apply hiff_right", "exact hunit_witness_right",
            ),
            "An actual inverse of the integer derivative proves the recoded natural derivative coprime to the lifting base.",
        ),
    )


def _make_root_bridge_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "beta_signed_horner_blend_root_equivalence",
            f"forall pb pc nb nc gb gc h a l M m. M = S h -> (exists q. M = m * q) -> "
            f"({_blend('pb', 'pc', 'nb', 'nc', 'gb', 'gc', 'h', 'l')}) -> "
            f"((({_natural_root('gb', 'gc', 'a', 'l', 'm')}) -> ({_root('pb', 'pc', 'nb', 'nc', 'a', 'l', 'm')})) /\\ "
            f"(({_root('pb', 'pc', 'nb', 'nc', 'a', 'l', 'm')}) -> ({_natural_root('gb', 'gc', 'a', 'l', 'm')})))",
            ("beta_horner_derivative_value_exists", "beta_horner_coefficient_blend_value_derivative", "hensel_signed_blend_zero_iff", "beta_horner_derivative_value_projection", "beta_horner_eval_functional"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro gb", "intro gc", "intro h", "intro a", "intro l", "intro M", "intro m",
                "intro hM", "intro hdiv", "intro hblend",
                f"have hP : exists vp dp. ({_pair('pb', 'pc', 'a', 'l', 'vp', 'dp')})",
                *_call("beta_horner_derivative_value_exists", "pb", "pc", "a", "l"), "cases hP", "cases hP_witness",
                f"have hN : exists vn dn. ({_pair('nb', 'nc', 'a', 'l', 'vn', 'dn')})",
                *_call("beta_horner_derivative_value_exists", "nb", "nc", "a", "l"), "cases hN", "cases hN_witness",
                f"have hG : exists vg dg. ({_pair('gb', 'gc', 'a', 'l', 'vg', 'dg')})",
                *_call("beta_horner_derivative_value_exists", "gb", "gc", "a", "l"), "cases hG", "cases hG_witness",
                "have hlinear : x4 = x + h * x2 /\\ x5 = x1 + h * x3",
                *_call("beta_horner_coefficient_blend_value_derivative", "pb", "pc", "nb", "nc", "gb", "gc", "h", "a", "l", "x", "x1", "x2", "x3", "x4", "x5"),
                "exact hblend", "exact hP_witness_witness", "exact hN_witness_witness", "exact hG_witness_witness", "cases hlinear",
                f"have hiff : ((({_mod('m', 'x4', '0')}) -> ({_mod('m', 'x', 'x2')})) /\\ (({_mod('m', 'x', 'x2')}) -> ({_mod('m', 'x4', '0')})))",
                *_call("hensel_signed_blend_zero_iff", "m", "M", "h", "x", "x2", "x4"), "exact hM", "exact hdiv", "exact hlinear_left", "cases hiff", "split",
                "intro hnatural", "cases hnatural", "cases hnatural_witness", "have hvalue : x4 = x6",
                *_call("beta_horner_eval_functional", "gb", "gc", "a", "l", "x4", "x6"),
                *_call("beta_horner_derivative_value_projection", "gb", "gc", "a", "l", "x4", "x5"), "exact hG_witness_witness", "exact hnatural_witness_left",
                "exists x", "exists x2", "split", *_call("beta_horner_derivative_value_projection", "pb", "pc", "a", "l", "x", "x1"), "exact hP_witness_witness", "split",
                *_call("beta_horner_derivative_value_projection", "nb", "nc", "a", "l", "x2", "x3"), "exact hN_witness_witness",
                "apply hiff_left", "rewrite hvalue", "exact hnatural_witness_right",
                "intro hsigned", "cases hsigned", "cases hsigned_witness", "cases hsigned_witness_witness", "cases hsigned_witness_witness_right",
                "have hpositive : x = x6", *_call("beta_horner_eval_functional", "pb", "pc", "a", "l", "x", "x6"),
                *_call("beta_horner_derivative_value_projection", "pb", "pc", "a", "l", "x", "x1"), "exact hP_witness_witness", "exact hsigned_witness_witness_left",
                "have hnegative : x2 = x7", *_call("beta_horner_eval_functional", "nb", "nc", "a", "l", "x2", "x7"),
                *_call("beta_horner_derivative_value_projection", "nb", "nc", "a", "l", "x2", "x3"), "exact hN_witness_witness", "exact hsigned_witness_witness_right_left",
                "exists x4", "split", *_call("beta_horner_derivative_value_projection", "gb", "gc", "a", "l", "x4", "x5"), "exact hG_witness_witness",
                "apply hiff_right", "rewrite hpositive", "rewrite hnegative", "exact hsigned_witness_witness_right_right",
            ),
            "At every natural point the recoded natural root condition is equivalent to the original integer-polynomial root condition, not merely implied by it.",
        ),
        spec(
            "beta_signed_horner_root_value_derivative_exists",
            f"forall pb pc nb nc a l M. ({_root('pb', 'pc', 'nb', 'nc', 'a', 'l', 'M')}) -> "
            f"exists vp dp vn dn. (({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) /\\ ({_mod('M', 'vp', 'vn')}))",
            ("beta_horner_derivative_value_exists", "beta_horner_derivative_value_projection", "beta_horner_eval_functional"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro M", "intro hroot",
                f"have hP : exists vp dp. ({_pair('pb', 'pc', 'a', 'l', 'vp', 'dp')})",
                *_call("beta_horner_derivative_value_exists", "pb", "pc", "a", "l"), "cases hP", "cases hP_witness",
                f"have hN : exists vn dn. ({_pair('nb', 'nc', 'a', 'l', 'vn', 'dn')})",
                *_call("beta_horner_derivative_value_exists", "nb", "nc", "a", "l"), "cases hN", "cases hN_witness",
                "cases hroot", "cases hroot_witness", "cases hroot_witness_witness", "cases hroot_witness_witness_right",
                "have hpositive : x = x4", *_call("beta_horner_eval_functional", "pb", "pc", "a", "l", "x", "x4"),
                *_call("beta_horner_derivative_value_projection", "pb", "pc", "a", "l", "x", "x1"), "exact hP_witness_witness", "exact hroot_witness_witness_left",
                "have hnegative : x2 = x5", *_call("beta_horner_eval_functional", "nb", "nc", "a", "l", "x2", "x5"),
                *_call("beta_horner_derivative_value_projection", "nb", "nc", "a", "l", "x2", "x3"), "exact hN_witness_witness", "exact hroot_witness_witness_right_left",
                "exists x", "exists x1", "exists x2", "exists x3", "split", "split", "exact hP_witness_witness", "exact hN_witness_witness",
                "rewrite hpositive", "rewrite hnegative", "exact hroot_witness_witness_right_right",
            ),
            "Every actual signed-polynomial root has actual positive/negative value and formal-derivative traces consistent with its witnessed root equation.",
        ),
    )


def _make_signed_lifting_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "hensel_signed_derivative_unit_mod_transport",
            f"forall p dp dn ep en. ({_mod('p', 'dp', 'ep')}) -> ({_mod('p', 'dn', 'en')}) -> "
            f"({_unit('p', 'dp', 'dn')}) -> ({_unit('p', 'ep', 'en')})",
            ("mod_eq_trans", "mod_eq_mul_right", "mod_eq_symm", "mod_eq_add", "mod_eq_refl"),
            (
                "intro p", "intro dp", "intro dn", "intro ep", "intro en", "intro hpositive", "intro hnegative", "intro hunit",
                "cases hunit", "cases hunit_witness",
                f"have hmiddle : {_mod('p', 'dp * x', '1 + en * x')}",
                *_call("mod_eq_trans", "p", "(dp * x)", "(1 + dn * x)", "(1 + en * x)"), "exact hunit_witness_right",
                *_call("mod_eq_add", "p", "1", "1", "(dn * x)", "(en * x)"), *_call("mod_eq_refl", "p", "1"),
                *_call("mod_eq_mul_right", "p", "dn", "en", "x"), "exact hnegative",
                "exists x", "split", "exact hunit_witness_left",
                *_call("mod_eq_trans", "p", "(ep * x)", "(dp * x)", "(1 + en * x)"),
                *_call("mod_eq_mul_right", "p", "ep", "dp", "x"), *_call("mod_eq_symm", "p", "dp", "ep"), "exact hpositive", "exact hmiddle",
            ),
            "The same bounded inverse transports an integer derivative through congruent positive and negative components.",
        ),
        spec(
            "beta_signed_horner_lift_preserves_simplicity",
            f"forall pb pc nb nc a l vp dp vn dn m p s M r. "
            f"({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) -> "
            f"({_unit('p', 'dp', 'dn')}) -> m = p * s -> ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'r')}) -> "
            f"({_simple('pb', 'pc', 'nb', 'nc', 'r', 'l', 'M', 'p')})",
            ("beta_signed_horner_root_value_derivative_exists", "beta_horner_derivative_mod_congruence", "mod_eq_of_mod_eq_multiple", "mod_eq_symm", "hensel_signed_derivative_unit_mod_transport"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro vp", "intro dp", "intro vn", "intro dn",
                "intro m", "intro p", "intro s", "intro M", "intro r", "intro hpair", "intro hunit", "intro hfactor", "intro hlift",
                "cases hpair", "cases hlift", "cases hlift_right",
                f"have hactual : exists P D N E. (({_signed_pair('pb', 'pc', 'nb', 'nc', 'r', 'l', 'P', 'D', 'N', 'E')}) /\\ ({_mod('M', 'P', 'N')}))",
                *_call("beta_signed_horner_root_value_derivative_exists", "pb", "pc", "nb", "nc", "r", "l", "M"), "exact hlift_right_right",
                "cases hactual", "cases hactual_witness", "cases hactual_witness_witness", "cases hactual_witness_witness_witness",
                "cases hactual_witness_witness_witness_witness", "cases hactual_witness_witness_witness_witness_left",
                f"have hpoint : {_mod('p', 'a', 'r')}", *_call("mod_eq_of_mod_eq_multiple", "p", "m", "a", "r"),
                "exists s", "exact hfactor", *_call("mod_eq_symm", "m", "r", "a"), "exact hlift_right_left",
                f"have hpositive : ({_mod('p', 'vp', 'x')}) /\\ ({_mod('p', 'dp', 'x1')})",
                *_call("beta_horner_derivative_mod_congruence", "pb", "pc", "p", "a", "r", "l", "vp", "dp", "x", "x1"),
                "exact hpoint", "exact hpair_left", "exact hactual_witness_witness_witness_witness_left_left", "cases hpositive",
                f"have hnegative : ({_mod('p', 'vn', 'x2')}) /\\ ({_mod('p', 'dn', 'x3')})",
                *_call("beta_horner_derivative_mod_congruence", "nb", "nc", "p", "a", "r", "l", "vn", "dn", "x2", "x3"),
                "exact hpoint", "exact hpair_right", "exact hactual_witness_witness_witness_witness_left_right", "cases hnegative",
                "exists x", "exists x1", "exists x2", "exists x3", "split", "split",
                "exact hactual_witness_witness_witness_witness_left_left", "exact hactual_witness_witness_witness_witness_left_right", "split",
                "exact hactual_witness_witness_witness_witness_right",
                *_call("hensel_signed_derivative_unit_mod_transport", "p", "dp", "dn", "x1", "x3"), "exact hpositive_right", "exact hnegative_right", "exact hunit",
            ),
            "Every canonical integer-polynomial lift retains an actual invertible formal derivative, with explicit coupled traces for both signed components.",
        ),
        spec(
            "beta_signed_horner_hensel_iterated_exists_unique",
            f"forall pb pc nb nc a l vp dp vn dn m p s j q. ~(p = 0) -> ~(m = 0) -> m = p * s -> "
            f"({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) -> "
            f"({_mod('m', 'vp', 'vn')}) -> ({_unit('p', 'dp', 'dn')}) -> ({_power('p', 'j', 'q')}) -> "
            f"exists r. (({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'm * q', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'm * q', 'z')}) -> z = r)",
            (
                "pow_nonzero_of_one_le", "one_le_of_ne_zero", "mul_ne_zero", "nonzero_is_succ", "mul_assoc", "mul_one",
                "beta_horner_coefficient_blend_exists", "beta_horner_derivative_value_exists", "beta_horner_coefficient_blend_value_derivative",
                "hensel_signed_blend_zero_iff", "hensel_signed_blend_unit_coprime", "beta_horner_hensel_iterated_exists_unique", "beta_signed_horner_blend_root_equivalence",
            ),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro vp", "intro dp", "intro vn", "intro dn",
                "intro m", "intro p", "intro s", "intro j", "intro q", "intro hp", "intro hm", "intro hfactor", "intro hpair", "intro hroot", "intro hunit", "intro hpower", "cases hpair",
                "have hq : ~(q = 0)", "intro hzero", *_call("pow_nonzero_of_one_le", "p", "j", "q"), *_call("one_le_of_ne_zero", "p"), "exact hp", "exact hpower", "exact hzero",
                "have hnonzero : ~(m * q = 0)", "intro hzero", *_call("mul_ne_zero", "m", "q"), "exact hm", "exact hq", "exact hzero",
                "have hmodulus : exists h. m * q = S h", *_call("nonzero_is_succ", "(m * q)"), "exact hnonzero", "cases hmodulus",
                f"have hrecoded : exists gb gc. ({_blend('pb', 'pc', 'nb', 'nc', 'gb', 'gc', 'x', 'l')})",
                *_call("beta_horner_coefficient_blend_exists", "pb", "pc", "nb", "nc", "x", "l"), "cases hrecoded", "cases hrecoded_witness",
                f"have hG : exists v d. ({_pair('x1', 'x2', 'a', 'l', 'v', 'd')})",
                *_call("beta_horner_derivative_value_exists", "x1", "x2", "a", "l"), "cases hG", "cases hG_witness",
                "have hlinear : x3 = vp + x * vn /\\ x4 = dp + x * dn",
                *_call("beta_horner_coefficient_blend_value_derivative", "pb", "pc", "nb", "nc", "x1", "x2", "x", "a", "l", "vp", "dp", "vn", "dn", "x3", "x4"),
                "exact hrecoded_witness_witness", "exact hpair_left", "exact hpair_right", "exact hG_witness_witness", "cases hlinear",
                f"have hrootG : {_mod('m', 'x3', '0')}",
                f"have hiff : ((({_mod('m', 'x3', '0')}) -> ({_mod('m', 'vp', 'vn')})) /\\ (({_mod('m', 'vp', 'vn')}) -> ({_mod('m', 'x3', '0')})))",
                *_call("hensel_signed_blend_zero_iff", "m", "(m * q)", "x", "vp", "vn", "x3"),
                "exact hmodulus_witness", "exists q", "refl", "exact hlinear_left", "cases hiff", "apply hiff_right", "exact hroot",
                f"have hcopG : {_cop('x4', 'p')}", *_call("hensel_signed_blend_unit_coprime", "p", "(m * q)", "x", "dp", "dn", "x4"),
                "exact hmodulus_witness", "exists s * q", "rewrite hfactor", "apply mul_assoc", "exact hlinear_right", "exact hunit",
                f"have hiteration : forall e Q. ({_power('p', 'e', 'Q')}) -> exists r. (({_natural_lift('x1', 'x2', 'l', 'm', 'a', 'm * Q', 'r')}) /\\ forall z. ({_natural_lift('x1', 'x2', 'l', 'm', 'a', 'm * Q', 'z')}) -> z = r)",
                *_call("beta_horner_hensel_iterated_exists_unique", "x1", "x2", "a", "l", "x3", "x4", "m", "p", "s"),
                "exact hp", "exact hm", "exact hG_witness_witness", "exact hfactor", "exact hrootG", "exact hcopG",
                f"have hresult : exists r. (({_natural_lift('x1', 'x2', 'l', 'm', 'a', 'm * q', 'r')}) /\\ forall z. ({_natural_lift('x1', 'x2', 'l', 'm', 'a', 'm * q', 'z')}) -> z = r)",
                "specialize hiteration j", "specialize hiteration q", "apply hiteration", "exact hpower",
                f"have hequivalence : forall t. ((({_natural_root('x1', 'x2', 't', 'l', 'm * q')}) -> ({_root('pb', 'pc', 'nb', 'nc', 't', 'l', 'm * q')})) /\\ (({_root('pb', 'pc', 'nb', 'nc', 't', 'l', 'm * q')}) -> ({_natural_root('x1', 'x2', 't', 'l', 'm * q')})))",
                "intro t", *_call("beta_signed_horner_blend_root_equivalence", "pb", "pc", "nb", "nc", "x1", "x2", "x", "t", "l", "(m * q)", "(m * q)"),
                "exact hmodulus_witness", "exists 1", "symm", "apply mul_one", "exact hrecoded_witness_witness",
                "cases hresult", "cases hresult_witness", "cases hresult_witness_left", "cases hresult_witness_left_right",
                "exists x5", "split", "split", "exact hresult_witness_left_left", "split", "exact hresult_witness_left_right_left",
                "specialize hequivalence x5", "cases hequivalence", "apply hequivalence_left", "exact hresult_witness_left_right_right",
                "intro z", "intro hz", "cases hz", "cases hz_right", "specialize hresult_witness_right z", "apply hresult_witness_right",
                "split", "exact hz_left", "split", "exact hz_right_left", "specialize hequivalence z", "cases hequivalence", "apply hequivalence_right", "exact hz_right_right",
            ),
            "Every arbitrary integer-coefficient simple root has unique canonical lifts through any finite number of prime-power steps; both existence and all-root uniqueness transport from an actually constructed natural polynomial.",
        ),
        spec(
            "beta_signed_horner_simple_root_hensel_lift_exists_unique",
            f"forall pb pc nb nc a l vp dp vn dn m p s. ~(p = 0) -> ~(m = 0) -> m = p * s -> "
            f"({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) -> "
            f"({_mod('m', 'vp', 'vn')}) -> ({_unit('p', 'dp', 'dn')}) -> "
            f"exists r. (({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'm * p', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'm * p', 'z')}) -> z = r)",
            ("pow_exists", "pow_one", "beta_signed_horner_hensel_iterated_exists_unique"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro vp", "intro dp", "intro vn", "intro dn", "intro m", "intro p", "intro s",
                "intro hp", "intro hm", "intro hfactor", "intro hpair", "intro hroot", "intro hunit",
                f"have hpower : {_power('p', '1', 'p')}",
                f"have hexists : exists q. ({_power('p', '1', 'q')})", *_call("pow_exists", "p", "1"), "cases hexists",
                "have heq : x = p", *_call("pow_one", "p", "1", "x"), "refl", "exact hexists_witness",
                "rewrite heq at hexists_witness", "rewrite heq at hexists_witness", "exact hexists_witness",
                *_call("beta_signed_horner_hensel_iterated_exists_unique", "pb", "pc", "nb", "nc", "a", "l", "vp", "dp", "vn", "dn", "m", "p", "s", "1", "p"),
                "exact hp", "exact hm", "exact hfactor", "exact hpair", "exact hroot", "exact hunit", "exact hpower",
            ),
            "An unrestricted root of any finite integer-coefficient polynomial has exactly one canonical next-modulus lift whenever its actual integer derivative is a unit.",
        ),
        spec(
            "beta_signed_horner_prime_power_hensel_lift_exists_unique",
            f"forall pb pc nb nc a l vp dp vn dn p k m. ~(p = 0) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) -> "
            f"({_mod('m', 'vp', 'vn')}) -> ({_unit('p', 'dp', 'dn')}) -> exists M. "
            f"(({_power('p', 'S k', 'M')}) /\\ exists r. "
            f"(({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("hensel_positive_power_factor", "pow_successor_compose", "beta_signed_horner_simple_root_hensel_lift_exists_unique"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro vp", "intro dp", "intro vn", "intro dn", "intro p", "intro k", "intro m",
                "intro hp", "intro hk", "intro hpower", "intro hpair", "intro hroot", "intro hunit",
                "have hfactor : ~(m = 0) /\\ exists s. m = p * s", *_call("hensel_positive_power_factor", "p", "k", "m"), "exact hp", "exact hk", "exact hpower",
                "cases hfactor", "cases hfactor_right", "exists m * p", "split",
                *_call("pow_successor_compose", "p", "k", "m", "(m * p)"), "exact hpower", "refl",
                *_call("beta_signed_horner_simple_root_hensel_lift_exists_unique", "pb", "pc", "nb", "nc", "a", "l", "vp", "dp", "vn", "dn", "m", "p", "x"),
                "exact hp", "exact hfactor_left", "exact hfactor_right_witness", "exact hpair", "exact hroot", "exact hunit",
            ),
            "Full integer-coefficient simple-root Hensel lifting constructs the actual next power and its unique bounded root, with no bound on the original input and no supplied correction.",
        ),
        spec(
            "beta_signed_horner_prime_power_iterated_lifts_exists_unique",
            f"forall pb pc nb nc a l vp dp vn dn p k j m. ~(p = 0) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_signed_pair('pb', 'pc', 'nb', 'nc', 'a', 'l', 'vp', 'dp', 'vn', 'dn')}) -> "
            f"({_mod('m', 'vp', 'vn')}) -> ({_unit('p', 'dp', 'dn')}) -> exists M. "
            f"(({_power('p', 'k + j', 'M')}) /\\ exists r. "
            f"(({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("hensel_positive_power_factor", "pow_exists", "pow_add", "beta_signed_horner_hensel_iterated_exists_unique"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro vp", "intro dp", "intro vn", "intro dn", "intro p", "intro k", "intro j", "intro m",
                "intro hp", "intro hk", "intro hpower", "intro hpair", "intro hroot", "intro hunit",
                "have hfactor : ~(m = 0) /\\ exists s. m = p * s", *_call("hensel_positive_power_factor", "p", "k", "m"), "exact hp", "exact hk", "exact hpower",
                "cases hfactor", "cases hfactor_right",
                f"have hmultiplier : exists q. ({_power('p', 'j', 'q')})", *_call("pow_exists", "p", "j"), "cases hmultiplier",
                f"have htarget : exists M. ({_power('p', 'k + j', 'M')})", *_call("pow_exists", "p", "(k + j)"), "cases htarget",
                "have hM : x2 = m * x1", *_call("pow_add", "p", "k", "j", "(k + j)", "m", "x1", "x2"),
                "refl", "exact hpower", "exact hmultiplier_witness", "exact htarget_witness",
                "exists x2", "split", "exact htarget_witness", *("rewrite hM",) * 6,
                *_call("beta_signed_horner_hensel_iterated_exists_unique", "pb", "pc", "nb", "nc", "a", "l", "vp", "dp", "vn", "dn", "m", "p", "x", "j", "x1"),
                "exact hp", "exact hfactor_left", "exact hfactor_right_witness", "exact hpair", "exact hroot", "exact hunit", "exact hmultiplier_witness",
            ),
            "Full integer-coefficient Hensel iteration constructs the actual arbitrary higher power and the unique canonical root in the entire original prime-power residue class.",
        ),
        spec(
            "integer_polynomial_prime_power_hensel_lift_exists_unique",
            f"forall pb pc nb nc a l p k m. ({prime('p', tag='sph_hensel_prime')}) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_simple('pb', 'pc', 'nb', 'nc', 'a', 'l', 'm', 'p')}) -> exists M. "
            f"(({_power('p', 'S k', 'M')}) /\\ exists r. "
            f"(({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("prime_nonzero", "beta_signed_horner_prime_power_hensel_lift_exists_unique"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro p", "intro k", "intro m",
                "intro hprime", "intro hk", "intro hpower", "intro hsimple",
                "cases hsimple", "cases hsimple_witness", "cases hsimple_witness_witness", "cases hsimple_witness_witness_witness",
                "cases hsimple_witness_witness_witness_witness", "cases hsimple_witness_witness_witness_witness_right",
                *_call("beta_signed_horner_prime_power_hensel_lift_exists_unique", "pb", "pc", "nb", "nc", "a", "l", "x", "x1", "x2", "x3", "p", "k", "m"),
                "intro hzero", *_call("prime_nonzero", "p"), "exact hprime", "exact hzero", "exact hk", "exact hpower",
                "exact hsimple_witness_witness_witness_witness_left", "exact hsimple_witness_witness_witness_witness_right_left", "exact hsimple_witness_witness_witness_witness_right_right",
            ),
            "G095: every integer-polynomial simple root at any natural representative modulo a positive prime power has one and only one canonical lift modulo the next actual power.",
        ),
        spec(
            "integer_polynomial_prime_power_hensel_iterated_exists_unique",
            f"forall pb pc nb nc a l p k j m. ({prime('p', tag='sph_iterated_prime')}) -> ~(k = 0) -> "
            f"({_power('p', 'k', 'm')}) -> ({_simple('pb', 'pc', 'nb', 'nc', 'a', 'l', 'm', 'p')}) -> exists M. "
            f"(({_power('p', 'k + j', 'M')}) /\\ exists r. "
            f"(({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'r')}) /\\ "
            f"forall z. ({_lift('pb', 'pc', 'nb', 'nc', 'l', 'm', 'a', 'M', 'z')}) -> z = r))",
            ("prime_nonzero", "beta_signed_horner_prime_power_iterated_lifts_exists_unique"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro a", "intro l", "intro p", "intro k", "intro j", "intro m",
                "intro hprime", "intro hk", "intro hpower", "intro hsimple",
                "cases hsimple", "cases hsimple_witness", "cases hsimple_witness_witness", "cases hsimple_witness_witness_witness",
                "cases hsimple_witness_witness_witness_witness", "cases hsimple_witness_witness_witness_witness_right",
                *_call("beta_signed_horner_prime_power_iterated_lifts_exists_unique", "pb", "pc", "nb", "nc", "a", "l", "x", "x1", "x2", "x3", "p", "k", "j", "m"),
                "intro hzero", *_call("prime_nonzero", "p"), "exact hprime", "exact hzero", "exact hk", "exact hpower",
                "exact hsimple_witness_witness_witness_witness_left", "exact hsimple_witness_witness_witness_witness_right_left", "exact hsimple_witness_witness_witness_witness_right_right",
            ),
            "For arbitrary finite j, an integer-polynomial simple root modulo p^k has a unique canonical lift modulo the actually constructed p^(k+j), retaining its full original residue class.",
        ),
    )


__all__ = [
    "SignedHenselError",
    "canonical_signed_horner_lift_relation",
    "horner_coefficient_blend_relation",
    "make_signed_hensel_lifting_candidate_theorems",
    "signed_derivative_unit_relation",
    "signed_horner_root_relation",
    "signed_horner_value_derivative_relation",
    "signed_simple_horner_root_relation",
]
