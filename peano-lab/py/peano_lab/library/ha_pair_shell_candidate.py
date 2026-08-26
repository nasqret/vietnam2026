"""Constructive doubled-triangular shell arithmetic for ``HA-K3-PAIR-1``.

The doubled Cantor constructor

``(left + right) * S (left + right) + (right + right)``

lies between the consecutive doubled-triangular shell boundaries
``s * S s`` and ``S s * S (S s)``, where ``s = left + right``.  This
isolated candidate layer proves the small arithmetic facts needed to exploit
that observation later.  It contains no pair constructor, projection, cell,
list, beta, CRT, division, remainder, or classical-logic theorem, and nothing
in this file is registered or publicly admitted.

Order is kept in the native witness form: ``a <= b`` is
``exists k. k + a = b`` and ``a < b`` is ``exists k. k + S a = b``.
"""

from __future__ import annotations

from typing import Any, Callable


def make_ha_pair_shell_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the six independent doubled-triangular shell candidates."""

    return (
        spec(
            "dt_shell_successor",
            "forall s. S s * S (S s) = S (S (s * S s + (s + s)))",
            ("mul_succ_left", "add_assoc", "add_comm"),
            (
                "intro s",
                "simp [mul_succ_left, add_assoc, add_comm]",
            ),
            "The next doubled-triangular boundary is the current boundary plus twice the shell and two.",
        ),
        spec(
            "dt_shell_monotone",
            "forall s t. (exists k. k + s = t) -> "
            "exists r. r + s * S s = t * S t",
            (
                "mul_le_mul_right",
                "succ_le_succ",
                "mul_le_mul_left",
                "le_trans",
            ),
            (
                "intro s",
                "intro t",
                "intro hst",
                "have hfirst : exists r. r + s * S s = t * S s",
                "specialize mul_le_mul_right s",
                "specialize mul_le_mul_right t",
                "specialize mul_le_mul_right (S s)",
                "apply mul_le_mul_right",
                "exact hst",
                "have hsucc : exists r. r + S s = S t",
                "specialize succ_le_succ s",
                "specialize succ_le_succ t",
                "apply succ_le_succ",
                "exact hst",
                "have hsecond : exists r. r + t * S s = t * S t",
                "specialize mul_le_mul_left (S s)",
                "specialize mul_le_mul_left (S t)",
                "specialize mul_le_mul_left t",
                "apply mul_le_mul_left",
                "exact hsucc",
                "specialize le_trans (s * S s)",
                "specialize le_trans (t * S s)",
                "specialize le_trans (t * S t)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
            ),
            "Doubled-triangular shell boundaries are monotone in witness order.",
        ),
        spec(
            "dt_right_le_shell",
            "forall left right. exists k. k + (right + right) = "
            "(left + right) + (left + right)",
            (
                "le_add_left",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
            ),
            (
                "intro left",
                "intro right",
                "have hright : exists k. k + right = left + right",
                "specialize le_add_left right",
                "specialize le_add_left left",
                "exact le_add_left",
                "have hfirst : exists k. k + (right + right) = "
                "(left + right) + right",
                "specialize add_le_add_right right",
                "specialize add_le_add_right (left + right)",
                "specialize add_le_add_right right",
                "apply add_le_add_right",
                "exact hright",
                "have hsecond : exists k. k + ((left + right) + right) = "
                "(left + right) + (left + right)",
                "specialize add_le_add_left right",
                "specialize add_le_add_left (left + right)",
                "specialize add_le_add_left (left + right)",
                "apply add_le_add_left",
                "exact hright",
                "specialize le_trans (right + right)",
                "specialize le_trans ((left + right) + right)",
                "specialize le_trans ((left + right) + (left + right))",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
            ),
            "The doubled right offset is bounded by twice its pair shell.",
        ),
        spec(
            "pair_code_shell_lower",
            "forall code left right. "
            "code = (left + right) * S (left + right) + (right + right) -> "
            "exists k. k + (left + right) * S (left + right) = code",
            ("add_comm",),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hcode",
                "exists right + right",
                "rewrite hcode",
                "apply add_comm",
            ),
            "Every doubled-Cantor code lies at or above its shell boundary.",
        ),
        spec(
            "pair_code_below_next_shell",
            "forall code left right. "
            "code = (left + right) * S (left + right) + (right + right) -> "
            "exists k. k + S code = "
            "S (left + right) * S (S (left + right))",
            (
                "dt_right_le_shell",
                "add_le_add_left",
                "le_succ",
                "succ_le_succ",
                "dt_shell_successor",
            ),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hcode",
                "have hright : exists k. k + (right + right) = "
                "(left + right) + (left + right)",
                "specialize dt_right_le_shell left",
                "specialize dt_right_le_shell right",
                "exact dt_right_le_shell",
                "have hcode_le : exists k. k + code = "
                "(left + right) * S (left + right) + "
                "((left + right) + (left + right))",
                "rewrite hcode",
                "specialize add_le_add_left (right + right)",
                "specialize add_le_add_left ((left + right) + (left + right))",
                "specialize add_le_add_left "
                "((left + right) * S (left + right))",
                "apply add_le_add_left",
                "exact hright",
                "have hcode_step : exists k. k + code = "
                "S ((left + right) * S (left + right) + "
                "((left + right) + (left + right)))",
                "specialize le_succ code",
                "specialize le_succ ((left + right) * S (left + right) + "
                "((left + right) + (left + right)))",
                "apply le_succ",
                "exact hcode_le",
                "have hstrict : exists k. k + S code = "
                "S (S ((left + right) * S (left + right) + "
                "((left + right) + (left + right))))",
                "specialize succ_le_succ code",
                "specialize succ_le_succ "
                "(S ((left + right) * S (left + right) + "
                "((left + right) + (left + right))))",
                "apply succ_le_succ",
                "exact hcode_step",
                "specialize dt_shell_successor (left + right)",
                "rewrite dt_shell_successor",
                "exact hstrict",
            ),
            "Every doubled-Cantor code lies strictly below the next shell boundary.",
        ),
        spec(
            "pair_code_shell_separated",
            "forall c1 l1 r1 c2 l2 r2. "
            "c1 = (l1 + r1) * S (l1 + r1) + (r1 + r1) -> "
            "c2 = (l2 + r2) * S (l2 + r2) + (r2 + r2) -> "
            "(exists k. k + S (l1 + r1) = l2 + r2) -> "
            "exists k. k + S c1 = c2",
            (
                "pair_code_below_next_shell",
                "dt_shell_monotone",
                "pair_code_shell_lower",
                "lt_of_lt_of_le",
            ),
            (
                "intro c1",
                "intro l1",
                "intro r1",
                "intro c2",
                "intro l2",
                "intro r2",
                "intro hc1",
                "intro hc2",
                "intro hshell",
                "have hbelow : exists k. k + S c1 = "
                "S (l1 + r1) * S (S (l1 + r1))",
                "specialize pair_code_below_next_shell c1",
                "specialize pair_code_below_next_shell l1",
                "specialize pair_code_below_next_shell r1",
                "apply pair_code_below_next_shell",
                "exact hc1",
                "have hmono : exists k. k + "
                "S (l1 + r1) * S (S (l1 + r1)) = "
                "(l2 + r2) * S (l2 + r2)",
                "specialize dt_shell_monotone (S (l1 + r1))",
                "specialize dt_shell_monotone (l2 + r2)",
                "apply dt_shell_monotone",
                "exact hshell",
                "have hlower : exists k. k + "
                "(l2 + r2) * S (l2 + r2) = c2",
                "specialize pair_code_shell_lower c2",
                "specialize pair_code_shell_lower l2",
                "specialize pair_code_shell_lower r2",
                "apply pair_code_shell_lower",
                "exact hc2",
                "have hfirst : exists k. k + S c1 = "
                "(l2 + r2) * S (l2 + r2)",
                "specialize lt_of_lt_of_le c1",
                "specialize lt_of_lt_of_le "
                "(S (l1 + r1) * S (S (l1 + r1)))",
                "specialize lt_of_lt_of_le "
                "((l2 + r2) * S (l2 + r2))",
                "apply lt_of_lt_of_le",
                "exact hbelow",
                "exact hmono",
                "specialize lt_of_lt_of_le c1",
                "specialize lt_of_lt_of_le "
                "((l2 + r2) * S (l2 + r2))",
                "specialize lt_of_lt_of_le c2",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact hlower",
            ),
            "Codes in strictly ordered doubled-triangular shells are strictly ordered.",
        ),
    )


__all__ = ["make_ha_pair_shell_candidate_theorems"]
