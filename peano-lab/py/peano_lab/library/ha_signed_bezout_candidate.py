"""Strict-HA bridge between balanced and canonical signed Bezout forms.

``SignedBezout(result,a,b,x,y)`` decodes the canonical signed-natural codes
``x`` and ``y`` and states the subtraction-free equation

``a * xp + b * yp = result + (a * xn + b * yn)``.

The relation is hygienic surface notation only: each occurrence expands to
the unchanged first-order language ``{0,S,+,*,=}``.  The four candidates in
this isolated D08 tranche transport a raw four-natural Bezout witness to
canonical coefficient codes, recover a raw witness from those codes, and
package the two implications.  They are constructive, dependency-curried,
unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_balance_candidate import signed_balance
from peano_lab.library.ha_signed_decode_candidate import signed_decode


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def signed_bezout(
    result: str,
    a: str,
    b: str,
    x: str,
    y: str,
    *,
    tag: str,
) -> str:
    """Expand RFC ``HA-K3-SIGNED-D08`` hygienically."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (result, "result"),
            (a, "first natural coefficient"),
            (b, "second natural coefficient"),
            (x, "first signed code"),
            (y, "second signed code"),
        )
    )
    result, a, b, x, y = variables
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sbz_{role}_{safe_tag}"
        for role in ("xp", "xn", "yp", "yn")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedBezout binder captures an argument")

    x_decode = signed_decode(
        x, names["xp"], names["xn"], tag=f"{safe_tag}_x"
    )
    y_decode = signed_decode(
        y, names["yp"], names["yn"], tag=f"{safe_tag}_y"
    )
    equation = (
        f"{a} * {names['xp']} + {b} * {names['yp']} = "
        f"{result} + ({a} * {names['xn']} + {b} * {names['yn']})"
    )
    return (
        f"exists {names['xp']} {names['xn']} {names['yp']} "
        f"{names['yn']}. (({x_decode}) /\\ "
        f"(({y_decode}) /\\ {equation}))"
    )


def _balanced_bezout(
    result: str,
    a: str,
    b: str,
    *,
    tag: str,
) -> str:
    """Expand the reviewed four-natural BalancedBezout relation."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (result, "result"),
            (a, "first natural coefficient"),
            (b, "second natural coefficient"),
        )
    )
    result, a, b = variables
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"bb_{role}_{safe_tag}"
        for role in ("xp", "yp", "xn", "yn")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated BalancedBezout binder captures an argument")
    return (
        f"exists {names['xp']} {names['yp']} {names['xn']} "
        f"{names['yn']}. {a} * {names['xp']} + {b} * {names['yp']} = "
        f"{result} + ({a} * {names['xn']} + {b} * {names['yn']})"
    )


def make_ha_signed_bezout_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the four canonical D08 balanced-Bezout bridge candidates."""

    forward_balanced = _balanced_bezout(
        "result", "a", "b", tag="forward"
    )
    forward_signed = signed_bezout(
        "result", "a", "b", "x", "y", tag="forward"
    )
    reverse_balanced = _balanced_bezout(
        "result", "a", "b", tag="reverse"
    )
    reverse_signed = signed_bezout(
        "result", "a", "b", "x", "y", tag="reverse"
    )
    iff_left = _balanced_bezout(
        "result", "a", "b", tag="iff_left"
    )
    iff_forward = signed_bezout(
        "result", "a", "b", "x", "y", tag="iff_forward"
    )
    iff_reverse = signed_bezout(
        "result", "a", "b", "x", "y", tag="iff_reverse"
    )
    iff_right = _balanced_bezout(
        "result", "a", "b", tag="iff_right"
    )
    balance_x = signed_balance(
        "xcode", "x", "x2", tag="bezout_x"
    )
    balance_y = signed_balance(
        "ycode", "x1", "x3", tag="bezout_y"
    )

    return (
        spec(
            "balanced_bezout_equation_transport",
            "forall result a b xp yp xn yn xcp xcn ycp ycn. "
            "xp + xcn = xn + xcp -> yp + ycn = yn + ycp -> "
            "a * xp + b * yp = result + (a * xn + b * yn) -> "
            "a * xcp + b * ycp = result + (a * xcn + b * ycn)",
            (
                "mul_cross_sum_left",
                "add_balance_outputs_compose",
                "add_comm",
            ),
            (
                "intro result",
                "intro a",
                "intro b",
                "intro xp",
                "intro yp",
                "intro xn",
                "intro yn",
                "intro xcp",
                "intro xcn",
                "intro ycp",
                "intro ycn",
                "intro hx",
                "intro hy",
                "intro hraw",
                "have hxscaled : "
                "a * xp + a * xcn = a * xn + a * xcp",
                "specialize mul_cross_sum_left a",
                "specialize mul_cross_sum_left xp",
                "specialize mul_cross_sum_left xcn",
                "specialize mul_cross_sum_left xn",
                "specialize mul_cross_sum_left xcp",
                "apply mul_cross_sum_left",
                "exact hx",
                "have hyscaled : "
                "b * yp + b * ycn = b * yn + b * ycp",
                "specialize mul_cross_sum_left b",
                "specialize mul_cross_sum_left yp",
                "specialize mul_cross_sum_left ycn",
                "specialize mul_cross_sum_left yn",
                "specialize mul_cross_sum_left ycp",
                "apply mul_cross_sum_left",
                "exact hy",
                "have htotal : "
                "(a * xp + b * yp) + 0 = "
                "(a * xn + b * yn) + result",
                "rewrite PA3",
                "trans result + (a * xn + b * yn)",
                "exact hraw",
                "apply add_comm",
                "have hout : "
                "(a * xcp + b * ycp) + 0 = "
                "(a * xcn + b * ycn) + result",
                "specialize add_balance_outputs_compose (a * xp)",
                "specialize add_balance_outputs_compose (a * xcn)",
                "specialize add_balance_outputs_compose (a * xn)",
                "specialize add_balance_outputs_compose (a * xcp)",
                "specialize add_balance_outputs_compose (b * yp)",
                "specialize add_balance_outputs_compose (b * ycn)",
                "specialize add_balance_outputs_compose (b * yn)",
                "specialize add_balance_outputs_compose (b * ycp)",
                "specialize add_balance_outputs_compose 0",
                "specialize add_balance_outputs_compose result",
                "apply add_balance_outputs_compose",
                "exact hxscaled",
                "exact hyscaled",
                "exact htotal",
                "trans (a * xcp + b * ycp) + 0",
                "symm",
                "apply PA3",
                "trans (a * xcn + b * ycn) + result",
                "exact hout",
                "apply add_comm",
            ),
            "Balanced coefficient pairs can be normalized without changing "
            "their subtraction-free Bezout equation.",
        ),
        spec(
            "balanced_bezout_to_signed_bezout",
            f"forall result a b. ({forward_balanced}) -> "
            f"exists x y. ({forward_signed})",
            (
                "signed_balance_total",
                "balanced_bezout_equation_transport",
            ),
            (
                "intro result",
                "intro a",
                "intro b",
                "intro hbalanced",
                "cases hbalanced",
                "cases hbalanced_witness",
                "cases hbalanced_witness_witness",
                "cases hbalanced_witness_witness_witness",
                f"have hx : exists xcode. ({balance_x})",
                "specialize signed_balance_total x",
                "specialize signed_balance_total x2",
                "apply signed_balance_total",
                "cases hx",
                "cases hx_witness",
                "cases hx_witness_witness",
                "cases hx_witness_witness_witness",
                f"have hy : exists ycode. ({balance_y})",
                "specialize signed_balance_total x1",
                "specialize signed_balance_total x3",
                "apply signed_balance_total",
                "cases hy",
                "cases hy_witness",
                "cases hy_witness_witness",
                "cases hy_witness_witness_witness",
                "have htransported : "
                "a * x5 + b * x8 = result + (a * x6 + b * x9)",
                "specialize balanced_bezout_equation_transport result",
                "specialize balanced_bezout_equation_transport a",
                "specialize balanced_bezout_equation_transport b",
                "specialize balanced_bezout_equation_transport x",
                "specialize balanced_bezout_equation_transport x1",
                "specialize balanced_bezout_equation_transport x2",
                "specialize balanced_bezout_equation_transport x3",
                "specialize balanced_bezout_equation_transport x5",
                "specialize balanced_bezout_equation_transport x6",
                "specialize balanced_bezout_equation_transport x8",
                "specialize balanced_bezout_equation_transport x9",
                "apply balanced_bezout_equation_transport",
                "exact hx_witness_witness_witness_right",
                "exact hy_witness_witness_witness_right",
                "exact hbalanced_witness_witness_witness_witness",
                "exists x4",
                "exists x7",
                "exists x5",
                "exists x6",
                "exists x8",
                "exists x9",
                "split",
                "exact hx_witness_witness_witness_left",
                "split",
                "exact hy_witness_witness_witness_left",
                "exact htransported",
            ),
            "Every four-natural balanced Bezout witness has canonical signed "
            "coefficient codes.",
        ),
        spec(
            "signed_bezout_to_balanced_bezout",
            "forall result a b x y. "
            f"({reverse_signed}) -> ({reverse_balanced})",
            (),
            (
                "intro result",
                "intro a",
                "intro b",
                "intro x",
                "intro y",
                "intro hsigned",
                "cases hsigned",
                "cases hsigned_witness",
                "cases hsigned_witness_witness",
                "cases hsigned_witness_witness_witness",
                "cases hsigned_witness_witness_witness_witness",
                "cases hsigned_witness_witness_witness_witness_right",
                "exists x1",
                "exists x3",
                "exists x2",
                "exists x4",
                "exact hsigned_witness_witness_witness_witness_right_right",
            ),
            "A SignedBezout graph directly exposes a four-natural balanced "
            "Bezout witness in the legacy witness order.",
        ),
        spec(
            "balanced_bezout_iff_signed_bezout_exists",
            f"forall result a b. ((({iff_left}) -> exists x y. "
            f"({iff_forward})) /\\ ((exists x y. ({iff_reverse})) -> "
            f"({iff_right})))",
            (
                "balanced_bezout_to_signed_bezout",
                "signed_bezout_to_balanced_bezout",
            ),
            (
                "intro result",
                "intro a",
                "intro b",
                "split",
                "intro hbalanced",
                "specialize balanced_bezout_to_signed_bezout result",
                "specialize balanced_bezout_to_signed_bezout a",
                "specialize balanced_bezout_to_signed_bezout b",
                "apply balanced_bezout_to_signed_bezout",
                "exact hbalanced",
                "intro hsigned",
                "cases hsigned",
                "cases hsigned_witness",
                "specialize signed_bezout_to_balanced_bezout result",
                "specialize signed_bezout_to_balanced_bezout a",
                "specialize signed_bezout_to_balanced_bezout b",
                "specialize signed_bezout_to_balanced_bezout x",
                "specialize signed_bezout_to_balanced_bezout x1",
                "apply signed_bezout_to_balanced_bezout",
                "exact hsigned_witness_witness",
            ),
            "BalancedBezout holds exactly when canonical SignedBezout "
            "coefficient codes exist.",
        ),
    )


__all__ = [
    "make_ha_signed_bezout_candidate_theorems",
    "signed_bezout",
]
