"""Pointwise congruence and additive cancellation for exact beta sums.

The main theorem lifts

``x_i == q_i + m_i + s_i (mod d)``

over four equally long beta-coded prefixes to the corresponding exact Sum
endpoints.  It uses ordinary induction, successor-sum decomposition, and the
checked binary congruence-addition theorem.  Two small cancellation rungs
then remove a common additive term, including the exact shape needed after
the Gauss magnitude sum is identified with the canonical half-range sum.

All displayed relations expand to unchanged first-order PA.  This module is
isolated authoring evidence: it registers and admits nothing.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, sum_relation


def _mod_eq(modulus: str, left: str, right: str, *, tag: str) -> str:
    return (
        f"exists fspm_u_{tag} fspm_v_{tag}. "
        f"({left}) + {modulus} * fspm_u_{tag} = "
        f"({right}) + {modulus} * fspm_v_{tag}"
    )


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = sum_relation(code, scale, length, "r", tag=f"{tag}_prefix")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_finite_sum_pointwise_mod_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build additive cancellation and four-prefix Sum aggregation."""

    cancel_input = _mod_eq("d", "a + b", "a + c", tag="cancel_input")
    cancel_result = _mod_eq("d", "b", "c", tag="cancel_result")
    cancel_middle_input = _mod_eq(
        "2", "x", "q + x + s", tag="cancel_middle_input"
    )
    cancel_middle_result = _mod_eq(
        "2", "0", "q + s", tag="cancel_middle_result"
    )
    zero_sum_input = _mod_eq("2", "0", "q + e", tag="zero_sum_input")
    sum_zero = _mod_eq("2", "q + e", "0", tag="sum_zero")
    q_e_result = _mod_eq("2", "q", "e", tag="zero_sum_result")
    sum_even = "exists fspm_even_sum. q + e = 2 * fspm_even_sum"
    same_parity = (
        "(((exists fspm_even_q. q = 2 * fspm_even_q) /\\ "
        "(exists fspm_even_e. e = 2 * fspm_even_e)) \\/ "
        "((exists fspm_odd_q. q = 2 * fspm_odd_q + 1) /\\ "
        "(exists fspm_odd_e. e = 2 * fspm_odd_e + 1)))"
    )

    source_sum = sum_relation("b", "c", "l", "X", tag="pointmod_source")
    quotient_sum = sum_relation("qb", "qc", "l", "Q", tag="pointmod_quotient")
    magnitude_sum = sum_relation("mb", "mc", "l", "M", tag="pointmod_magnitude")
    sign_sum = sum_relation("sb", "sc", "l", "E", tag="pointmod_sign")
    source_entry = beta_at("b", "c", "i", "x", tag="pointmod_source_entry")
    quotient_entry = beta_at("qb", "qc", "i", "q", tag="pointmod_quotient_entry")
    magnitude_entry = beta_at("mb", "mc", "i", "m", tag="pointmod_magnitude_entry")
    sign_entry = beta_at("sb", "sc", "i", "s", tag="pointmod_sign_entry")
    entry_mod = _mod_eq("d", "x", "q + m + s", tag="pointmod_entry")
    pointwise = (
        "forall i x q m s. (exists h. h + S i = l) -> "
        f"({source_entry}) -> ({quotient_entry}) -> ({magnitude_entry}) -> "
        f"({sign_entry}) -> ({entry_mod})"
    )
    endpoint_mod = _mod_eq("d", "X", "Q + M + E", tag="pointmod_endpoint")

    prefix_source_entry = beta_at(
        "b", "c", "i", "x", tag="pointmod_prefix_source_entry"
    )
    prefix_quotient_entry = beta_at(
        "qb", "qc", "i", "q", tag="pointmod_prefix_quotient_entry"
    )
    prefix_magnitude_entry = beta_at(
        "mb", "mc", "i", "m", tag="pointmod_prefix_magnitude_entry"
    )
    prefix_sign_entry = beta_at(
        "sb", "sc", "i", "s", tag="pointmod_prefix_sign_entry"
    )
    prefix_entry_mod = _mod_eq(
        "d", "x", "q + m + s", tag="pointmod_prefix_entry"
    )
    prefix_pointwise = (
        "forall i x q m s. (exists h. h + S i = l) -> "
        f"({prefix_source_entry}) -> ({prefix_quotient_entry}) -> "
        f"({prefix_magnitude_entry}) -> ({prefix_sign_entry}) -> "
        f"({prefix_entry_mod})"
    )

    source_decomposition = _sum_decomposition(
        "b", "c", "l", "X", tag="pointmod_source_decomp"
    )
    quotient_decomposition = _sum_decomposition(
        "qb", "qc", "l", "Q", tag="pointmod_quotient_decomp"
    )
    magnitude_decomposition = _sum_decomposition(
        "mb", "mc", "l", "M", tag="pointmod_magnitude_decomp"
    )
    sign_decomposition = _sum_decomposition(
        "sb", "sc", "l", "E", tag="pointmod_sign_decomp"
    )
    prefix_mod = _mod_eq("d", "x1", "x3 + x5 + x7", tag="pointmod_prefix")
    last_mod = _mod_eq("d", "x", "x2 + x4 + x6", tag="pointmod_last")
    combined_mod = _mod_eq(
        "d",
        "x1 + x",
        "(x3 + x5 + x7) + (x2 + x4 + x6)",
        tag="pointmod_combined",
    )

    return (
        spec(
            "mod_eq_add_cancel_left",
            f"forall d a b c. ({cancel_input}) -> ({cancel_result})",
            ("add_left_cancel", "add_assoc"),
            (
                "intro d",
                "intro a",
                "intro b",
                "intro c",
                "intro hmod",
                "cases hmod",
                "cases hmod_witness",
                "exists x",
                "exists x1",
                "specialize add_left_cancel a",
                "specialize add_left_cancel (b + d * x)",
                "specialize add_left_cancel (c + d * x1)",
                "apply add_left_cancel",
                "trans (a + b) + d * x",
                "symm",
                "apply add_assoc",
                "trans (a + c) + d * x1",
                "exact hmod_witness_witness",
                "apply add_assoc",
            ),
            "Balanced congruence cancels a common additive left term constructively.",
        ),
        spec(
            "mod_two_cancel_middle",
            f"forall x q s. ({cancel_middle_input}) -> ({cancel_middle_result})",
            ("mod_eq_add_cancel_left", "add_assoc", "add_comm"),
            (
                "intro x",
                "intro q",
                "intro s",
                "intro hmod",
                "have hreorder : q + x + s = x + (q + s)",
                "simp [add_assoc, add_comm]",
                "rewrite hreorder at hmod",
                "specialize mod_eq_add_cancel_left 2",
                "specialize mod_eq_add_cancel_left x",
                "specialize mod_eq_add_cancel_left 0",
                "specialize mod_eq_add_cancel_left (q + s)",
                "apply mod_eq_add_cancel_left",
                "have hxzero : x + 0 = x",
                "apply PA3",
                "rewrite hxzero",
                "exact hmod",
            ),
            "From x == q+x+s modulo two, cancel x and obtain 0 == q+s.",
        ),
        spec(
            "mod_two_zero_sum_to_congruent",
            f"forall q e. ({zero_sum_input}) -> ({q_e_result})",
            (
                "mod_eq_symm",
                "mod_two_zero_to_even",
                "even_sum_parity_cases",
                "matching_parity_mod_two",
            ),
            (
                "intro q",
                "intro e",
                "intro hzero",
                f"have hsum_zero : {sum_zero}",
                "specialize mod_eq_symm 2",
                "specialize mod_eq_symm 0",
                "specialize mod_eq_symm (q + e)",
                "apply mod_eq_symm",
                "exact hzero",
                f"have heven : {sum_even}",
                "specialize mod_two_zero_to_even (q + e)",
                "apply mod_two_zero_to_even",
                "exact hsum_zero",
                f"have hsame : {same_parity}",
                "specialize even_sum_parity_cases q",
                "specialize even_sum_parity_cases e",
                "apply even_sum_parity_cases",
                "exact heven",
                "specialize matching_parity_mod_two q",
                "specialize matching_parity_mod_two e",
                "apply matching_parity_mod_two",
                "exact hsame",
            ),
            "If q+e is zero modulo two, q and e have the same parity and are congruent.",
        ),
        spec(
            "beta_sum_pointwise_mod_three_add",
            "forall d b c qb qc mb mc sb sc l X Q M E. "
            f"({source_sum}) -> ({quotient_sum}) -> ({magnitude_sum}) -> "
            f"({sign_sum}) -> ({pointwise}) -> ({endpoint_mod})",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "mod_eq_add",
                "le_succ",
                "le_refl",
                "add_assoc",
                "add_comm",
                "add_permute_outer",
            ),
            (
                "intro d",
                "intro b",
                "intro c",
                "intro qb",
                "intro qc",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "induction l",
                "intro X",
                "intro Q",
                "intro M",
                "intro E",
                "intro hsource",
                "intro hquotient",
                "intro hmagnitude",
                "intro hsign",
                "intro hpointwise",
                "have hX : X = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero X",
                "apply beta_sum_zero",
                "exact hsource",
                "have hQ : Q = 0",
                "specialize beta_sum_zero qb",
                "specialize beta_sum_zero qc",
                "specialize beta_sum_zero Q",
                "apply beta_sum_zero",
                "exact hquotient",
                "have hM : M = 0",
                "specialize beta_sum_zero mb",
                "specialize beta_sum_zero mc",
                "specialize beta_sum_zero M",
                "apply beta_sum_zero",
                "exact hmagnitude",
                "have hE : E = 0",
                "specialize beta_sum_zero sb",
                "specialize beta_sum_zero sc",
                "specialize beta_sum_zero E",
                "apply beta_sum_zero",
                "exact hsign",
                "rewrite hX",
                "rewrite hQ",
                "rewrite hM",
                "rewrite hE",
                "exists 0",
                "exists 0",
                "norm_num",
                "intro X",
                "intro Q",
                "intro M",
                "intro E",
                "intro hsource",
                "intro hquotient",
                "intro hmagnitude",
                "intro hsign",
                "intro hpointwise",
                f"have hsource_decomp : {source_decomposition}",
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose X",
                "apply beta_sum_succ_decompose",
                "exact hsource",
                "cases hsource_decomp",
                "cases hsource_decomp_witness",
                "cases hsource_decomp_witness_witness",
                "cases hsource_decomp_witness_witness_right",
                f"have hquotient_decomp : {quotient_decomposition}",
                "specialize beta_sum_succ_decompose qb",
                "specialize beta_sum_succ_decompose qc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose Q",
                "apply beta_sum_succ_decompose",
                "exact hquotient",
                "cases hquotient_decomp",
                "cases hquotient_decomp_witness",
                "cases hquotient_decomp_witness_witness",
                "cases hquotient_decomp_witness_witness_right",
                f"have hmagnitude_decomp : {magnitude_decomposition}",
                "specialize beta_sum_succ_decompose mb",
                "specialize beta_sum_succ_decompose mc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose M",
                "apply beta_sum_succ_decompose",
                "exact hmagnitude",
                "cases hmagnitude_decomp",
                "cases hmagnitude_decomp_witness",
                "cases hmagnitude_decomp_witness_witness",
                "cases hmagnitude_decomp_witness_witness_right",
                f"have hsign_decomp : {sign_decomposition}",
                "specialize beta_sum_succ_decompose sb",
                "specialize beta_sum_succ_decompose sc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose E",
                "apply beta_sum_succ_decompose",
                "exact hsign",
                "cases hsign_decomp",
                "cases hsign_decomp_witness",
                "cases hsign_decomp_witness_witness",
                "cases hsign_decomp_witness_witness_right",
                f"have hprefix_pointwise : {prefix_pointwise}",
                "intro i",
                "intro y",
                "intro q",
                "intro m",
                "intro s",
                "intro hi",
                "intro hy",
                "intro hq",
                "intro hm",
                "intro hs",
                "specialize hpointwise i",
                "specialize hpointwise y",
                "specialize hpointwise q",
                "specialize hpointwise m",
                "specialize hpointwise s",
                "apply hpointwise",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hy",
                "exact hq",
                "exact hm",
                "exact hs",
                f"have hprefix : {prefix_mod}",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x5",
                "specialize IH x7",
                "apply IH",
                "exact hsource_decomp_witness_witness_right_left",
                "exact hquotient_decomp_witness_witness_right_left",
                "exact hmagnitude_decomp_witness_witness_right_left",
                "exact hsign_decomp_witness_witness_right_left",
                "exact hprefix_pointwise",
                f"have hlast : {last_mod}",
                "specialize hpointwise l",
                "specialize hpointwise x",
                "specialize hpointwise x2",
                "specialize hpointwise x4",
                "specialize hpointwise x6",
                "apply hpointwise",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hsource_decomp_witness_witness_left",
                "exact hquotient_decomp_witness_witness_left",
                "exact hmagnitude_decomp_witness_witness_left",
                "exact hsign_decomp_witness_witness_left",
                f"have hcombined : {combined_mod}",
                "specialize mod_eq_add d",
                "specialize mod_eq_add x1",
                "specialize mod_eq_add (x3 + x5 + x7)",
                "specialize mod_eq_add x",
                "specialize mod_eq_add (x2 + x4 + x6)",
                "apply mod_eq_add",
                "exact hprefix",
                "exact hlast",
                "have hreorder : (x3 + x5 + x7) + (x2 + x4 + x6) = (x3 + x2) + (x5 + x4) + (x7 + x6)",
                "simp [add_assoc, add_comm, add_permute_outer]",
                "congr",
                "refl",
                "congr",
                "refl",
                "trans (x7 + x4) + (x6 + x2)",
                "symm",
                "apply add_assoc",
                "trans (x4 + x7) + (x6 + x2)",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "rewrite hreorder at hcombined",
                "rewrite hsource_decomp_witness_witness_right_right",
                "rewrite hquotient_decomp_witness_witness_right_right",
                "rewrite hmagnitude_decomp_witness_witness_right_right",
                "rewrite hsign_decomp_witness_witness_right_right",
                "exact hcombined",
            ),
            "Pointwise x==q+m+s congruence lifts to the four exact Sum endpoints.",
        ),
    )


__all__ = [
    "_mod_eq",
    "make_finite_sum_pointwise_mod_candidate_theorems",
]
