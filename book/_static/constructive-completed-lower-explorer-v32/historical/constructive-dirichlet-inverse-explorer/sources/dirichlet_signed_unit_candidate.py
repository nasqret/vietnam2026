"""Canonical signed units and constructive affine equations over ordinary HA.

The canonical signed codes of +1 and -1 are respectively 2 and 1.  ``Unit``
below names that two-element predicate, not an assumed cancellation law or
an inverse oracle.  Its equivalence with an actual signed inverse is proved.
All operations are the unchanged SignedDecode/SignedAdd/SignedMul graphs.
These additive candidate bodies neither enroll nor admit a theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .finite_fold_surface import _identifier
from .gaussian_euclidean_candidate import _sd
from .mobius_prime_step_candidate import _negate
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _public, _rewrite,
)
from .signed_table_operations_candidate import _mul_code


def _unit(u: str, tag: str) -> str:
    _identifier(tag, "signed-unit definition tag")
    return f"(({u}) = 2 \\/ ({u}) = 1)"


def dirichlet_signed_unit_relation(
    u: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Exactly the canonical codes +1 and -1, in an explicit term context."""
    return _public(_unit, (u,), tag=tag, variables=variables)


def _one_decode() -> tuple[str, ...]:
    return ("left", "split", "symm", "apply mul_one", "refl")


def _minus_one_decode() -> tuple[str, ...]:
    return ("right", "exists 0", "split", "split", "rewrite PA5",
            "symm", "apply zero_add", "refl", "refl")


def _unit_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    self_product = _intro("u", "hu") + ("cases hu",)
    self_product += _rewrite("hu_left", _mul_code("u", "u", "2", "self_pos"), "u")
    self_product += _call("signed_mul_one_right", "2")
    self_product += _rewrite("hu_right", _mul_code("u", "u", "2", "self_neg"), "u")
    self_product += _call("signed_mul_of_decoded_equation", "1", "1", "2",
                          "0", "1", "0", "1", "1", "0")
    self_product += _minus_one_decode() + _minus_one_decode() + _one_decode()
    self_product += ("simp",)

    classify = _intro("a", "b", "hmul")
    for code, hyp in (("a", "ha"), ("b", "hb")):
        classify += (f"have {hyp} : exists p n. ({_sd(code, 'p', 'n', hyp+'decode')})",)
        classify += _call("signed_decode_total", code) + _cases(hyp, 2)
    classify += (f"have hplus : {_sd('2','1','0','positive_decode')}",) + _one_decode()
    classify += (f"have hminus : {_sd('1','0','1','negative_decode')}",) + _minus_one_decode()
    equation = "(x*x2 + x1*x3)+0 = (x*x3 + x1*x2)+1"
    classify += (f"have he : {equation}",)
    classify += _call("signed_mul_to_decoded_equation", "a", "b", "2",
                      "x", "x1", "x2", "x3", "1", "0")
    classify += ("exact ha_witness_witness", "exact hb_witness_witness",
                 "exact hplus", "exact hmul", "have hna : x=0 \\/ x1=0")
    classify += _call("signed_decode_normal", "a", "x", "x1")
    classify += ("exact ha_witness_witness", "have hnb : x2=0 \\/ x3=0")
    classify += _call("signed_decode_normal", "b", "x2", "x3")
    classify += ("exact hb_witness_witness", "cases hna", "cases hnb")

    # Both positive components vanish: the negative magnitudes multiply to 1.
    classify += ("have hm : x1*x3=1", "trans (x*x2+x1*x3)+0", "symm",
                 "simp [hna_left, hnb_left, mul_zero_left, zero_add]",
                 "trans (x*x3+x1*x2)+1", "exact he",
                 "simp [hna_left, hnb_left, mul_zero_left, zero_add]",
                 "have hparts : x1=1 /\\ x3=1")
    classify += _call("mul_eq_one_components", "x1", "x3")
    classify += ("exact hm", "cases hparts", "right", "split")
    for code, pos, neg, hyp, zero, one in (
        ("a", "x", "x1", "ha", "hna_left", "hparts_left"),
        ("b", "x2", "x3", "hb", "hnb_left", "hparts_right"),
    ):
        classify += _call("signed_decoded_balance_implies_code_eq", code, pos, neg,
                          "1", "0", "1")
        classify += (f"exact {hyp}_witness_witness", "exact hminus",
                     f"simp [{zero}, {one}, zero_add]")

    # Opposite signs cannot yield positive one.
    classify += ("have hm : 0=S(x1*x2)", "trans (x*x2+x1*x3)+0",
                 "symm", "simp [hna_left, hnb_right, mul_zero_left, zero_add]",
                 "trans (x*x3+x1*x2)+1", "exact he",
                 "simp [hna_left, hnb_right, mul_zero_left, zero_add]",
                 "exfalso", "apply PA1", "symm", "exact hm", "cases hnb",
                 "have hm : 0=S(x*x3)", "trans (x*x2+x1*x3)+0", "symm",
                 "simp [hna_right, hnb_left, mul_zero_left, zero_add]",
                 "trans (x*x3+x1*x2)+1", "exact he",
                 "simp [hna_right, hnb_left, mul_zero_left, zero_add]",
                 "exfalso", "apply PA1", "symm", "exact hm")

    # Both negative components vanish: the positive magnitudes multiply to 1.
    classify += ("have hm : x*x2=1", "trans (x*x2+x1*x3)+0", "symm",
                 "simp [hna_right, hnb_right, mul_zero_left, zero_add]",
                 "trans (x*x3+x1*x2)+1", "exact he",
                 "simp [hna_right, hnb_right, mul_zero_left, zero_add]",
                 "have hparts : x=1 /\\ x2=1")
    classify += _call("mul_eq_one_components", "x", "x2")
    classify += ("exact hm", "cases hparts", "left", "split")
    for code, pos, neg, hyp, one, zero in (
        ("a", "x", "x1", "ha", "hparts_left", "hna_right"),
        ("b", "x2", "x3", "hb", "hparts_right", "hnb_right"),
    ):
        classify += _call("signed_decoded_balance_implies_code_eq", code, pos, neg,
                          "2", "1", "0")
        classify += (f"exact {hyp}_witness_witness", "exact hplus",
                     f"simp [{one}, {zero}, zero_add]")

    inverse = _intro("u") + ("split", "intro h", "cases h",
                            "have hc : (u=2 /\\ x=2) \\/ (u=1 /\\ x=1)")
    inverse += _call("dirichlet_signed_unit_product_classification", "u", "x")
    inverse += ("exact h_witness", "cases hc", "cases hc_left", "left", "exact hc_left_left",
                "cases hc_right", "right", "exact hc_right_left", "intro hu", "exists u")
    inverse += _call("dirichlet_signed_unit_self_product", "u") + ("exact hu",)

    return (
        spec(
            "dirichlet_signed_unit_self_product",
            f"forall u. ({_unit('u','self_unit')}) -> ({_mul_code('u','u','2','self_product')})",
            ("signed_mul_one_right", "signed_mul_of_decoded_equation", "mul_one", "zero_add"),
            self_product,
            "Each of the two canonical signed units has an actual signed square equal to positive one.",
        ),
        spec(
            "dirichlet_signed_unit_product_classification",
            f"forall a b. ({_mul_code('a','b','2','classify')}) -> ((a=2 /\\ b=2) \\/ (a=1 /\\ b=1))",
            ("signed_decode_total", "mul_one", "zero_add", "signed_mul_to_decoded_equation",
             "signed_decode_normal", "mul_zero_left", "mul_eq_one_components",
             "signed_decoded_balance_implies_code_eq"),
            classify,
            "An actual signed product is positive one only for the two equal canonical units; mixed signs are constructively impossible.",
        ),
        spec(
            "dirichlet_signed_unit_inverse_iff",
            f"forall u. ((exists v. ({_mul_code('u','v','2','inverse_forward')})) -> ({_unit('u','inverse_unit')})) /\\ "
            f"(({_unit('u','inverse_unit_back')}) -> exists v. ({_mul_code('u','v','2','inverse_backward')}))",
            ("dirichlet_signed_unit_product_classification", "dirichlet_signed_unit_self_product"),
            inverse,
            "The finite signed-unit predicate is equivalent to existence of an actual signed multiplicative inverse, not defined by an inverse oracle.",
        ),
    )


def _affine_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    cancel = _intro("r", "a", "b", "e", "ha", "hb")
    cancel += (f"have hn : exists n. ({_negate('r','n','cancel_negate')})",)
    cancel += _call("signed_negate_total", "r") + ("cases hn",)
    cancel += _call("signed_add_functional", "x", "e", "a", "b")
    for value, hyp in (("a", "ha"), ("b", "hb")):
        cancel += _call("signed_add_associative", "x", "r", value, "0", "e", value)
        cancel += _call("signed_add_negate_left_zero", "r", "x") + ("exact hn_witness",)
        cancel += _call("signed_add_zero_left", value) + (f"exact {hyp}",)

    solve = _intro("r", "e") + (f"have hn : exists n. ({_negate('r','n','solve_negate')})",)
    solve += _call("signed_negate_total", "r") + ("cases hn",)
    solve += (f"have hy : exists y. ({_add_code('x','e','y','solve_addend')})",)
    solve += _call("signed_add_total", "x", "e") + ("cases hy", "exists x1")
    solve += _call("signed_add_associative", "r", "x", "e", "0", "x1", "e")
    solve += _call("signed_add_negate_right_zero", "r", "x") + ("exact hn_witness",)
    solve += _call("signed_add_zero_left", "e") + ("exact hy_witness",)

    involution = _intro("u", "a", "b", "hu", "hab")
    involution += (f"have hc : exists c. ({_mul_code('b','u','c','involution_construct')})",)
    involution += _call("signed_mul_total", "b", "u") + ("cases hc", "have heq : x=a")
    involution += _call("signed_mul_functional", "a", "2", "x", "a")
    involution += _call("signed_mul_associative", "a", "u", "u", "b", "2", "x")
    involution += ("exact hab", "exact hc_witness")
    involution += _call("dirichlet_signed_unit_self_product", "u") + ("exact hu",)
    involution += _call("signed_mul_one_right", "a")
    involution += _rewrite("heq", _mul_code("b", "u", "x", "involution_rewrite"), "x", "hc_witness")
    involution += ("exact hc_witness",)

    mul_cancel = _intro("u", "a", "b", "z", "hu", "ha", "hb")
    mul_cancel += _call("signed_mul_functional", "z", "u", "a", "b")
    for value, hyp in (("a", "ha"), ("b", "hb")):
        mul_cancel += _call("dirichlet_signed_unit_multiply_involution", "u", value, "z")
        mul_cancel += ("exact hu", f"exact {hyp}")

    affine = _intro("r", "u", "e", "hu")
    affine += (f"have hy : exists y. ({_add_code('r','y','e','affine_addend')})",)
    affine += _call("dirichlet_signed_add_solve", "r", "e") + ("cases hy",)
    affine += (f"have hx : exists a. ({_mul_code('x','u','a','affine_preimage')})",)
    affine += _call("signed_mul_total", "x", "u") + ("cases hx", "exists x1", "exists x", "split")
    affine += _call("dirichlet_signed_unit_multiply_involution", "u", "x", "x1")
    affine += ("exact hu", "exact hx_witness", "exact hy_witness")

    unique = _intro("r", "u", "e", "a", "b", "c", "d", "hu", "hab", "hbe", "hcd", "hde")
    unique += ("have heq : b=d",) + _call("dirichlet_signed_add_cancel_left", "r", "b", "d", "e")
    unique += ("exact hbe", "exact hde", "split")
    unique += _call("dirichlet_signed_unit_multiply_cancel_right", "u", "a", "c", "d")
    unique += ("exact hu",) + _rewrite("heq", _mul_code("a", "u", "b", "unique_rewrite"), "b", "hab")
    unique += ("exact hab", "exact hcd", "exact heq")

    return (
        spec(
            "dirichlet_signed_add_cancel_left",
            f"forall r a b e. ({_add_code('r','a','e','cancel_first')}) -> ({_add_code('r','b','e','cancel_second')}) -> a=b",
            ("signed_negate_total", "signed_add_functional", "signed_add_associative",
             "signed_add_negate_left_zero", "signed_add_zero_left"),
            cancel,
            "Cancellation of a common canonical signed summand follows by constructing its actual additive inverse.",
        ),
        spec(
            "dirichlet_signed_add_solve",
            f"forall r e. exists y. ({_add_code('r','y','e','add_solve')})",
            ("signed_negate_total", "signed_add_total", "signed_add_associative",
             "signed_add_negate_right_zero", "signed_add_zero_left"),
            solve,
            "Construct the signed addend taking any canonical signed r to any canonical signed e, including zero and negative values.",
        ),
        spec(
            "dirichlet_signed_unit_multiply_involution",
            f"forall u a b. ({_unit('u','involution_unit')}) -> ({_mul_code('a','u','b','involution_source')}) -> ({_mul_code('b','u','a','involution_target')})",
            ("signed_mul_total", "signed_mul_functional", "signed_mul_associative",
             "dirichlet_signed_unit_self_product", "signed_mul_one_right"),
            involution,
            "Multiplication by either actual signed unit is an involution on canonical signed codes.",
        ),
        spec(
            "dirichlet_signed_unit_multiply_cancel_right",
            f"forall u a b z. ({_unit('u','multiply_cancel_unit')}) -> ({_mul_code('a','u','z','multiply_cancel_first')}) -> ({_mul_code('b','u','z','multiply_cancel_second')}) -> a=b",
            ("signed_mul_functional", "dirichlet_signed_unit_multiply_involution"),
            mul_cancel,
            "An actual signed unit can be cancelled from a common right factor without cancelling arbitrary zero or nonunit factors.",
        ),
        spec(
            "dirichlet_signed_unit_affine_solve",
            f"forall r u e. ({_unit('u','affine_unit')}) -> exists x y. "
            + _and(_mul_code("x", "u", "y", "affine_product"), _add_code("r", "y", "e", "affine_result")),
            ("dirichlet_signed_add_solve", "signed_mul_total", "dirichlet_signed_unit_multiply_involution"),
            affine,
            "Given either actual signed unit, construct both x and its actual product y with r+y=e; no difference, product or solution witness is supplied.",
        ),
        spec(
            "dirichlet_signed_unit_affine_unique",
            f"forall r u e a b c d. ({_unit('u','affine_unique_unit')}) -> "
            f"({_mul_code('a','u','b','affine_unique_first_product')}) -> ({_add_code('r','b','e','affine_unique_first_sum')}) -> "
            f"({_mul_code('c','u','d','affine_unique_second_product')}) -> ({_add_code('r','d','e','affine_unique_second_sum')}) -> a=c /\\ b=d",
            ("dirichlet_signed_add_cancel_left", "dirichlet_signed_unit_multiply_cancel_right"),
            unique,
            "Any two witnessed solutions of the same unit-affine equation have equal canonical inputs and equal actual product outputs.",
        ),
    )


def make_dirichlet_signed_unit_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return additive native-HA unit and affine-equation candidates in order."""
    return (*_unit_rows(spec), *_affine_rows(spec))


__all__ = ("dirichlet_signed_unit_relation", "make_dirichlet_signed_unit_candidate_theorems")
