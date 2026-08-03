"""Constructive Gauss lemma for an arbitrary prime-unit representative.

The bounded endpoint unnecessarily presents the multiplier ``a`` as a
canonical remainder.  The signed-half construction and its power congruence
already work for every ``a`` not divisible by the odd prime.  This isolated
candidate therefore composes that same witness package with the arbitrary-
representative Euler criterion and retains the original signed prefix and
its exact reflection count ``e``.

The common classification tail is derived from the bounded candidate's
audited tactic recipe.  The derivation is fail-closed at exact sentinels and
changes only the entrance assumptions and the Euler invocation; the resulting
script is independently replayed against the fully expanded theorem below.
No theorem authority is inherited from Python-level source reuse.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import prime
from .fermat_residue_map_candidate import not_divides
from .finite_fold_surface import bit_count
from .gauss_lemma_bounded_candidate import (
    make_gauss_lemma_bounded_candidate_theorems,
)
from .gauss_sign_bridge import _even, _odd
from .gauss_signed_prefix_candidate import half_range, signed_half_prefix
from .quadratic_residue_surface import quadratic_residue


def _bounded_recipe() -> tuple[str, ...]:
    """Extract the audited common tail while rejecting upstream drift."""

    def capture(
        _name: str,
        _statement: str,
        _dependencies: tuple[str, ...],
        script: tuple[str, ...],
        _summary: str,
    ) -> tuple[str, ...]:
        return script

    (commands,) = make_gauss_lemma_bounded_candidate_theorems(capture)
    if not (
        len(commands) == 204
        and commands[:10]
        == (
            "intro p",
            "intro h",
            "intro a",
            "intro b",
            "intro c",
            "intro hpodd",
            "intro hprime",
            "intro hpositive",
            "intro halt",
            "intro hhalf",
        )
        and commands[10] == "have hpsucc : p = S (2 * h)"
        and commands[20] == "have ha0 : ~(a = 0)"
        and commands[34].startswith("have hgauss : exists e A R.")
        and commands[51].startswith("have heuler :")
        and commands[52] == "specialize bounded_euler_criterion_complete p"
        and commands[65] == "cases heuler"
    ):
        raise ValueError("bounded Gauss recipe changed; review the shared tail")

    arbitrary_euler = (
        "specialize arbitrary_euler_criterion_complete p",
        "specialize arbitrary_euler_criterion_complete a",
        "specialize arbitrary_euler_criterion_complete (2 * h)",
        "specialize arbitrary_euler_criterion_complete h",
        "specialize arbitrary_euler_criterion_complete x1",
        "apply arbitrary_euler_criterion_complete",
        "exact hpsucc",
        "exact hprime",
        "exact hnotdiv",
        "symm",
        "exact hdouble",
        "exact hgauss_witness_witness_witness_left",
    )
    return (
        commands[:7]
        + ("intro hnotdiv", "intro hhalf")
        + commands[10:20]
        + commands[34:52]
        + arbitrary_euler
        + commands[65:]
    )


def make_gauss_lemma_arbitrary_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the complete signed-count classification for every prime unit."""

    prime_p = prime("p", tag="gla_prime")
    nondivisor = not_divides("p", "a", tag="gla_nondivisor")
    canonical_half = half_range("b", "c", "h", tag="gla_half_range")
    qres = quadratic_residue("p", "a", tag="gla_qres")
    signed_prefix = signed_half_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "h",
        tag="gla_signed_prefix",
    )
    signed_count = bit_count("sb", "sc", "h", "e", tag="gla_count")
    hidden_signed_count = (
        "exists mb mc sb sc. "
        f"(({signed_prefix}) /\\ ({signed_count}))"
    )
    even_e = _even("e", tag="gla_even")
    odd_e = _odd("e", tag="gla_odd")
    residue_iff_even = f"((({qres}) -> ({even_e})) /\\ (({even_e}) -> ({qres})))"
    nonresidue_iff_odd = (
        f"((~({qres}) -> ({odd_e})) /\\ (({odd_e}) -> ~({qres})))"
    )
    conclusion = (
        "exists e. "
        f"(({hidden_signed_count}) /\\ "
        f"(({residue_iff_even}) /\\ ({nonresidue_iff_odd})))"
    )

    return (
        spec(
            "arbitrary_gauss_lemma_complete",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({nondivisor}) -> ({canonical_half}) -> "
            f"({conclusion})",
            (
                "gauss_lemma_power_congruence_exists",
                "pow_predecessor_parity_mod",
                "arbitrary_euler_criterion_complete",
                "parity_cases",
                "odd_prime_one_not_mod_predecessor",
                "mod_eq_symm",
                "mod_eq_trans",
                "mul_comm",
                "zero_add",
            ),
            _bounded_recipe(),
            "An arbitrary prime unit is a quadratic residue exactly when its "
            "Gauss reflection count is even, and a nonresidue exactly when it "
            "is odd.",
        ),
    )


__all__ = ["make_gauss_lemma_arbitrary_candidate_theorems"]
