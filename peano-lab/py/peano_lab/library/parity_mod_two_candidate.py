"""Balanced congruence modulo two as a native parity interface.

Evenness is congruence to zero modulo two and oddness is congruence to one.
The final candidate uses symmetry and transitivity of balanced congruence to
show that congruent naturals have exactly the same constructive parity status.

All predicates below are expanded formula text in unchanged first-order PA.
The candidates remain dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists pmt_u_{tag} pmt_v_{tag}. "
        f"{left} + 2 * pmt_u_{tag} = {right} + 2 * pmt_v_{tag}"
    )


def _even(term: str, *, tag: str) -> str:
    return f"exists pmt_even_{tag}. {term} = 2 * pmt_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists pmt_odd_{tag}. {term} = 2 * pmt_odd_{tag} + 1"


def make_parity_mod_two_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build parity/congruence conversion and transport candidates."""

    n_even = _even("n", tag="n")
    m_even = _even("m", tag="m")
    n_odd = _odd("n", tag="n")
    m_odd = _odd("m", tag="m")
    n_zero = _mod_two("n", "0", tag="n_zero")
    m_zero = _mod_two("m", "0", tag="m_zero")
    n_one = _mod_two("n", "1", tag="n_one")
    m_one = _mod_two("m", "1", tag="m_one")
    n_m = _mod_two("n", "m", tag="n_m")
    m_n = _mod_two("m", "n", tag="m_n")
    even_iff = (
        f"((({n_even}) -> ({m_even})) /\\ (({m_even}) -> ({n_even})))"
    )
    odd_iff = f"((({n_odd}) -> ({m_odd})) /\\ (({m_odd}) -> ({n_odd})))"

    return (
        spec(
            "even_to_mod_two_zero",
            f"forall n. ({n_even}) -> ({n_zero})",
            ("dvd_to_mod_zero",),
            (
                "intro n",
                "intro heven",
                "specialize dvd_to_mod_zero 2",
                "specialize dvd_to_mod_zero n",
                "apply dvd_to_mod_zero",
                "exact heven",
            ),
            "Every even natural is congruent to zero modulo two.",
        ),
        spec(
            "mod_two_zero_to_even",
            f"forall n. ({n_zero}) -> ({n_even})",
            ("mod_eq_zero_to_dvd_nonzero",),
            (
                "intro n",
                "intro hzero",
                "specialize mod_eq_zero_to_dvd_nonzero 2",
                "specialize mod_eq_zero_to_dvd_nonzero n",
                "apply mod_eq_zero_to_dvd_nonzero",
                "intro htwo",
                "apply PA1",
                "exact htwo",
                "exact hzero",
            ),
            "Congruence to zero modulo two supplies an even witness.",
        ),
        spec(
            "odd_to_mod_two_one",
            f"forall n. ({n_odd}) -> ({n_one})",
            ("add_comm",),
            (
                "intro n",
                "intro hodd",
                "cases hodd",
                "exists 0",
                "exists x",
                "rewrite hodd_witness",
                "simp",
                "symm",
                "trans 2 * x + 1",
                "apply add_comm",
                "simp",
            ),
            "Every odd natural is congruent to one modulo two.",
        ),
        spec(
            "mod_two_one_to_odd",
            f"forall n. ({n_one}) -> ({n_odd})",
            ("mod_eq_to_remainder_decomposition", "mul_comm"),
            (
                "intro n",
                "intro hone",
                "have hdecomp : exists q. n = q * 2 + 1",
                "specialize mod_eq_to_remainder_decomposition 2",
                "specialize mod_eq_to_remainder_decomposition n",
                "specialize mod_eq_to_remainder_decomposition 1",
                "apply mod_eq_to_remainder_decomposition",
                "intro htwo",
                "apply PA1",
                "exact htwo",
                "exists 0",
                "norm_num",
                "exact hone",
                "cases hdecomp",
                "exists x",
                "trans x * 2 + 1",
                "exact hdecomp_witness",
                "congr",
                "apply mul_comm",
                "refl",
            ),
            "Congruence to one modulo two supplies an odd witness.",
        ),
        spec(
            "mod_two_preserves_parity",
            f"forall n m. ({n_m}) -> (({even_iff}) /\\ ({odd_iff}))",
            (
                "even_to_mod_two_zero",
                "mod_two_zero_to_even",
                "odd_to_mod_two_one",
                "mod_two_one_to_odd",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro n",
                "intro m",
                "intro hmod",
                f"have hback : {m_n}",
                "specialize mod_eq_symm 2",
                "specialize mod_eq_symm n",
                "specialize mod_eq_symm m",
                "apply mod_eq_symm",
                "exact hmod",
                "split",
                "split",
                "intro hneven",
                f"have hnzero : {n_zero}",
                "specialize even_to_mod_two_zero n",
                "apply even_to_mod_two_zero",
                "exact hneven",
                f"have hmzero : {m_zero}",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hback",
                "exact hnzero",
                "specialize mod_two_zero_to_even m",
                "apply mod_two_zero_to_even",
                "exact hmzero",
                "intro hmeven",
                f"have hmzero : {m_zero}",
                "specialize even_to_mod_two_zero m",
                "apply even_to_mod_two_zero",
                "exact hmeven",
                f"have hnzero : {n_zero}",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hmod",
                "exact hmzero",
                "specialize mod_two_zero_to_even n",
                "apply mod_two_zero_to_even",
                "exact hnzero",
                "split",
                "intro hnodd",
                f"have hnone : {n_one}",
                "specialize odd_to_mod_two_one n",
                "apply odd_to_mod_two_one",
                "exact hnodd",
                f"have hmone : {m_one}",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hback",
                "exact hnone",
                "specialize mod_two_one_to_odd m",
                "apply mod_two_one_to_odd",
                "exact hmone",
                "intro hmodd",
                f"have hmone : {m_one}",
                "specialize odd_to_mod_two_one m",
                "apply odd_to_mod_two_one",
                "exact hmodd",
                f"have hnone : {n_one}",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hmod",
                "exact hmone",
                "specialize mod_two_one_to_odd n",
                "apply mod_two_one_to_odd",
                "exact hnone",
            ),
            "Balanced congruence modulo two preserves both parity predicates.",
        ),
    )


__all__ = ["make_parity_mod_two_candidate_theorems"]
