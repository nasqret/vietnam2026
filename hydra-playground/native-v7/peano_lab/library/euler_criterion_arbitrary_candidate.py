"""Arbitrary-representative packaging of the native Euler criterion.

The bounded Euler criterion assumes ``0 < a < p``.  This isolated candidate
module removes that presentation restriction without changing the object
language.  A nonmultiple is reduced to its nonzero canonical remainder,
quadratic residuosity is transported across balanced congruence, and a fresh
relational power of the remainder is connected to the supplied power by the
generic ``pow_mod_congruent`` theorem.

All surfaces below expand to ordinary first-order Peano arithmetic.  The
factory is dependency-curried, unregistered, constructive, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import not_divides, prime
from .finite_fold_surface import power_relation
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import _lt_term
from .wilson_pair_product_candidate import _mod_eq_term


def make_euler_criterion_arbitrary_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build representative reduction and the unrestricted Euler endpoint."""

    canonical_variables = ("p", "a", "r")
    canonical_not_divisor = not_divides(
        "p", "a", tag="eca_canonical_not_divisor"
    )
    canonical_bound = _lt_term(
        "r",
        "p",
        tag="eca_canonical_bound",
        avoid=canonical_variables,
    )
    canonical_mod = _mod_eq_term(
        "p",
        "a",
        "r",
        tag="eca_canonical_mod",
        avoid=canonical_variables,
    )
    canonical_result = (
        f"exists r. ~(r = 0) /\\ (({canonical_bound}) /\\ ({canonical_mod}))"
    )

    transport_variables = ("p", "a", "r")
    transport_mod = _mod_eq_term(
        "p",
        "a",
        "r",
        tag="eca_qres_transport_mod",
        avoid=transport_variables,
    )
    qres_a_transport = quadratic_residue(
        "p", "a", tag="eca_qres_transport_a"
    )
    qres_r_transport = quadratic_residue(
        "p", "r", tag="eca_qres_transport_r"
    )
    qres_transport_result = (
        f"((({qres_a_transport}) -> ({qres_r_transport})) /\\ "
        f"(({qres_r_transport}) -> ({qres_a_transport})))"
    )

    power_variables = ("p", "a", "r", "h", "A", "R")
    power_base_mod = _mod_eq_term(
        "p",
        "a",
        "r",
        tag="eca_power_base_mod",
        avoid=power_variables,
    )
    power_a = power_relation("a", "h", "A", tag="eca_power_a")
    power_r = power_relation("r", "h", "R", tag="eca_power_r")
    power_result_mod = _mod_eq_term(
        "p",
        "A",
        "R",
        tag="eca_power_result_mod",
        avoid=power_variables,
    )
    power_transport_result = (
        f"exists R. ({power_r}) /\\ ({power_result_mod})"
    )

    variables = ("p", "a", "n", "h", "A")
    prime_p = prime("p", tag="eca_prime")
    not_divisor = not_divides("p", "a", tag="eca_not_divisor")
    qres_a = quadratic_residue("p", "a", tag="eca_qres_a")
    power_a_endpoint = power_relation("a", "h", "A", tag="eca_power_endpoint")
    mod_one = _mod_eq_term(
        "p", "A", "1", tag="eca_mod_one", avoid=variables
    )
    mod_predecessor = _mod_eq_term(
        "p", "A", "n", tag="eca_mod_predecessor", avoid=variables
    )
    residue_iff = f"((({qres_a}) -> ({mod_one})) /\\ (({mod_one}) -> ({qres_a})))"
    nonresidue_iff = (
        f"((~({qres_a}) -> ({mod_predecessor})) /\\ "
        f"(({mod_predecessor}) -> ~({qres_a})))"
    )

    # Proof-local canonical representative surfaces.  Their binder tags are
    # distinct from the public contracts so capture and accidental textual
    # coupling remain easy to audit.
    local_variables = ("p", "a", "n", "h", "A", "r", "R")
    local_r_bound = _lt_term(
        "r", "p", tag="eca_local_r_bound", avoid=local_variables
    )
    local_a_r = _mod_eq_term(
        "p", "a", "r", tag="eca_local_a_r", avoid=local_variables
    )

    # After eliminating the two existential packages, Peano Lab names their
    # witnesses ``x`` and ``x1``.  Keep matching proof-local surfaces explicit
    # rather than relying on unavailable source-level aliases for ``r``/``R``.
    proof_variables = ("p", "a", "n", "h", "A", "x", "x1", "R")
    proof_power_x_R = power_relation("x", "h", "R", tag="eca_proof_power_x_R")
    proof_A_R = _mod_eq_term(
        "p", "A", "R", tag="eca_proof_A_R", avoid=proof_variables
    )
    proof_A_x1 = _mod_eq_term(
        "p", "A", "x1", tag="eca_proof_A_x1", avoid=proof_variables
    )
    proof_x1_A = _mod_eq_term(
        "p", "x1", "A", tag="eca_proof_x1_A", avoid=proof_variables
    )
    proof_x1_one = _mod_eq_term(
        "p", "x1", "1", tag="eca_proof_x1_one", avoid=proof_variables
    )
    proof_x1_predecessor = _mod_eq_term(
        "p", "x1", "n", tag="eca_proof_x1_predecessor", avoid=proof_variables
    )
    proof_qres_x = quadratic_residue("p", "x", tag="eca_proof_qres_x")
    proof_qres_equiv = (
        f"((({qres_a}) -> ({proof_qres_x})) /\\ "
        f"(({proof_qres_x}) -> ({qres_a})))"
    )
    proof_bounded_residue_iff = (
        f"((({proof_qres_x}) -> ({proof_x1_one})) /\\ "
        f"(({proof_x1_one}) -> ({proof_qres_x})))"
    )
    proof_bounded_nonresidue_iff = (
        f"((~({proof_qres_x}) -> ({proof_x1_predecessor})) /\\ "
        f"(({proof_x1_predecessor}) -> ~({proof_qres_x})))"
    )

    common_prefix = (
        "forall p a n h A. p = S n -> "
        f"({prime_p}) -> ({not_divisor}) -> n = h + h -> "
        f"({power_a_endpoint}) -> "
    )

    return (
        spec(
            "nondivisor_canonical_remainder_exists",
            f"forall p a. ~(p = 0) -> ({canonical_not_divisor}) -> "
            f"({canonical_result})",
            (
                "division_remainder_exists",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
            ),
            (
                "intro p",
                "intro a",
                "intro hp0",
                "intro hnotdiv",
                "have hdivision : exists q r. a = p * q + r /\\ "
                "exists gap. gap + S r = p",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists a",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "have hr0 : ~(x1 = 0)",
                "intro hrzero",
                "apply hnotdiv",
                "exists x",
                "trans p * x + x1",
                "exact hdivision_witness_witness_left",
                "rewrite hrzero",
                "simp",
                "have hdecomposition : a = x * p + x1",
                "trans p * x + x1",
                "exact hdivision_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hmod : {_mod_eq_term('p', 'a', 'x1', tag='eca_canonical_proof_mod', avoid=('p', 'a', 'x', 'x1'))}",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq a",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x1",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomposition",
                "exists x1",
                "split",
                "exact hr0",
                "split",
                "exact hdivision_witness_witness_right",
                "exact hmod",
            ),
            "Every nonmultiple has a nonzero canonical remainder congruent to it.",
        ),
        spec(
            "quadratic_residue_mod_equiv",
            f"forall p a r. ({transport_mod}) -> ({qres_transport_result})",
            ("mod_eq_symm", "mod_eq_trans"),
            (
                "intro p",
                "intro a",
                "intro r",
                "intro har",
                "split",
                "intro hqa",
                "cases hqa",
                "exists x",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (x * x)",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans r",
                "apply mod_eq_trans",
                "exact hqa_witness",
                "exact har",
                "intro hqr",
                "cases hqr",
                "exists x",
                f"have hra : {_mod_eq_term('p', 'r', 'a', tag='eca_qres_proof_reverse', avoid=('p', 'a', 'r', 'x'))}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm a",
                "specialize mod_eq_symm r",
                "apply mod_eq_symm",
                "exact har",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (x * x)",
                "specialize mod_eq_trans r",
                "specialize mod_eq_trans a",
                "apply mod_eq_trans",
                "exact hqr_witness",
                "exact hra",
            ),
            "Quadratic residuosity depends only on the balanced congruence class.",
        ),
        spec(
            "pow_congruent_base_witness",
            f"forall p a r h A. ({power_base_mod}) -> ({power_a}) -> "
            f"({power_transport_result})",
            ("pow_exists", "pow_mod_congruent"),
            (
                "intro p",
                "intro a",
                "intro r",
                "intro h",
                "intro A",
                "intro har",
                "intro hpower",
                f"have hrpower : exists R. ({power_relation('r', 'h', 'R', tag='eca_power_proof_exists')})",
                "specialize pow_exists r",
                "specialize pow_exists h",
                "exact pow_exists",
                "cases hrpower",
                "exists x",
                "split",
                "exact hrpower_witness",
                "specialize pow_mod_congruent p",
                "specialize pow_mod_congruent a",
                "specialize pow_mod_congruent r",
                "specialize pow_mod_congruent h",
                "specialize pow_mod_congruent A",
                "specialize pow_mod_congruent x",
                "apply pow_mod_congruent",
                "exact har",
                "exact hpower",
                "exact hrpower_witness",
            ),
            "A congruent base has a relational power congruent to the supplied power.",
        ),
        spec(
            "arbitrary_euler_criterion_residue_iff",
            f"{common_prefix}({residue_iff})",
            (
                "prime_nonzero",
                "nondivisor_canonical_remainder_exists",
                "quadratic_residue_mod_equiv",
                "pow_congruent_base_witness",
                "bounded_euler_criterion_residue_iff",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro heven",
                "intro hpower",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hcanonical : exists r. ~(r = 0) /\\ (({local_r_bound}) /\\ ({local_a_r}))",
                "specialize nondivisor_canonical_remainder_exists p",
                "specialize nondivisor_canonical_remainder_exists a",
                "apply nondivisor_canonical_remainder_exists",
                "exact hp0",
                "exact hnotdiv",
                "cases hcanonical",
                "cases hcanonical_witness",
                "cases hcanonical_witness_right",
                f"have hpower_transport : exists R. ({proof_power_x_R}) /\\ ({proof_A_R})",
                "specialize pow_congruent_base_witness p",
                "specialize pow_congruent_base_witness a",
                "specialize pow_congruent_base_witness x",
                "specialize pow_congruent_base_witness h",
                "specialize pow_congruent_base_witness A",
                "apply pow_congruent_base_witness",
                "exact hcanonical_witness_right_right",
                "exact hpower",
                "cases hpower_transport",
                "cases hpower_transport_witness",
                f"have hqres_equiv : {proof_qres_equiv}",
                "specialize quadratic_residue_mod_equiv p",
                "specialize quadratic_residue_mod_equiv a",
                "specialize quadratic_residue_mod_equiv x",
                "apply quadratic_residue_mod_equiv",
                "exact hcanonical_witness_right_right",
                f"have hbounded : {proof_bounded_residue_iff}",
                "specialize bounded_euler_criterion_residue_iff p",
                "specialize bounded_euler_criterion_residue_iff x",
                "specialize bounded_euler_criterion_residue_iff n",
                "specialize bounded_euler_criterion_residue_iff h",
                "specialize bounded_euler_criterion_residue_iff x1",
                "apply bounded_euler_criterion_residue_iff",
                "exact hpn",
                "exact hp",
                "exact hcanonical_witness_left",
                "exact hcanonical_witness_right_left",
                "exact heven",
                "exact hpower_transport_witness_left",
                "cases hqres_equiv",
                "cases hbounded",
                "split",
                "intro hqa",
                f"have hqr : {proof_qres_x}",
                "apply hqres_equiv_left",
                "exact hqa",
                f"have hRone : {proof_x1_one}",
                "apply hbounded_left",
                "exact hqr",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hpower_transport_witness_right",
                "exact hRone",
                "intro hAone",
                f"have hRA : {proof_x1_A}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm A",
                "specialize mod_eq_symm x1",
                "apply mod_eq_symm",
                "exact hpower_transport_witness_right",
                f"have hRone : {proof_x1_one}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans 1",
                "apply mod_eq_trans",
                "exact hRA",
                "exact hAone",
                f"have hqr : {proof_qres_x}",
                "apply hbounded_right",
                "exact hRone",
                "apply hqres_equiv_right",
                "exact hqr",
            ),
            "Euler's residue equivalence for an arbitrary nonmultiple representative.",
        ),
        spec(
            "arbitrary_euler_criterion_nonresidue_iff",
            f"{common_prefix}({nonresidue_iff})",
            (
                "prime_nonzero",
                "nondivisor_canonical_remainder_exists",
                "quadratic_residue_mod_equiv",
                "pow_congruent_base_witness",
                "bounded_euler_criterion_nonresidue_iff",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro heven",
                "intro hpower",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hcanonical : exists r. ~(r = 0) /\\ (({local_r_bound}) /\\ ({local_a_r}))",
                "specialize nondivisor_canonical_remainder_exists p",
                "specialize nondivisor_canonical_remainder_exists a",
                "apply nondivisor_canonical_remainder_exists",
                "exact hp0",
                "exact hnotdiv",
                "cases hcanonical",
                "cases hcanonical_witness",
                "cases hcanonical_witness_right",
                f"have hpower_transport : exists R. ({proof_power_x_R}) /\\ ({proof_A_R})",
                "specialize pow_congruent_base_witness p",
                "specialize pow_congruent_base_witness a",
                "specialize pow_congruent_base_witness x",
                "specialize pow_congruent_base_witness h",
                "specialize pow_congruent_base_witness A",
                "apply pow_congruent_base_witness",
                "exact hcanonical_witness_right_right",
                "exact hpower",
                "cases hpower_transport",
                "cases hpower_transport_witness",
                f"have hqres_equiv : {proof_qres_equiv}",
                "specialize quadratic_residue_mod_equiv p",
                "specialize quadratic_residue_mod_equiv a",
                "specialize quadratic_residue_mod_equiv x",
                "apply quadratic_residue_mod_equiv",
                "exact hcanonical_witness_right_right",
                f"have hbounded : {proof_bounded_nonresidue_iff}",
                "specialize bounded_euler_criterion_nonresidue_iff p",
                "specialize bounded_euler_criterion_nonresidue_iff x",
                "specialize bounded_euler_criterion_nonresidue_iff n",
                "specialize bounded_euler_criterion_nonresidue_iff h",
                "specialize bounded_euler_criterion_nonresidue_iff x1",
                "apply bounded_euler_criterion_nonresidue_iff",
                "exact hpn",
                "exact hp",
                "exact hcanonical_witness_left",
                "exact hcanonical_witness_right_left",
                "exact heven",
                "exact hpower_transport_witness_left",
                "cases hqres_equiv",
                "cases hbounded",
                "split",
                "intro hnqa",
                f"have hnqr : ~({proof_qres_x})",
                "intro hqr",
                "apply hnqa",
                "apply hqres_equiv_right",
                "exact hqr",
                f"have hRminus : {proof_x1_predecessor}",
                "apply hbounded_left",
                "exact hnqr",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans n",
                "apply mod_eq_trans",
                "exact hpower_transport_witness_right",
                "exact hRminus",
                "intro hAminus",
                f"have hRA : {proof_x1_A}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm A",
                "specialize mod_eq_symm x1",
                "apply mod_eq_symm",
                "exact hpower_transport_witness_right",
                f"have hRminus : {proof_x1_predecessor}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans x1",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans n",
                "apply mod_eq_trans",
                "exact hRA",
                "exact hAminus",
                f"have hnqr : ~({proof_qres_x})",
                "intro hqr",
                "apply hbounded_right",
                "exact hRminus",
                "exact hqr",
                "intro hqa",
                "apply hnqr",
                "apply hqres_equiv_left",
                "exact hqa",
            ),
            "Euler's nonresidue equivalence for an arbitrary nonmultiple representative.",
        ),
        spec(
            "arbitrary_euler_criterion_complete",
            f"{common_prefix}(({residue_iff}) /\\ ({nonresidue_iff}))",
            (
                "arbitrary_euler_criterion_residue_iff",
                "arbitrary_euler_criterion_nonresidue_iff",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro heven",
                "intro hpower",
                "split",
                "specialize arbitrary_euler_criterion_residue_iff p",
                "specialize arbitrary_euler_criterion_residue_iff a",
                "specialize arbitrary_euler_criterion_residue_iff n",
                "specialize arbitrary_euler_criterion_residue_iff h",
                "specialize arbitrary_euler_criterion_residue_iff A",
                "apply arbitrary_euler_criterion_residue_iff",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "exact heven",
                "exact hpower",
                "specialize arbitrary_euler_criterion_nonresidue_iff p",
                "specialize arbitrary_euler_criterion_nonresidue_iff a",
                "specialize arbitrary_euler_criterion_nonresidue_iff n",
                "specialize arbitrary_euler_criterion_nonresidue_iff h",
                "specialize arbitrary_euler_criterion_nonresidue_iff A",
                "apply arbitrary_euler_criterion_nonresidue_iff",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "exact heven",
                "exact hpower",
            ),
            "Complete Euler criterion for every representative coprime to the prime.",
        ),
    )


__all__ = ["make_euler_criterion_arbitrary_candidate_theorems"]
