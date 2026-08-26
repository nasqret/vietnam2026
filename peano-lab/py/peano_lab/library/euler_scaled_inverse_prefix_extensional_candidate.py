"""Extensional candidates for the beta-coded Euler scaled-inverse map.

The prefix stores actual mate residues while source positions are zero-based.
This layer proves decoded soundness/extensionality, extracts the predecessor of
every positive mate, rules out decoded fixed points under ``~QRes``, and
decodes the involutive return edge.  All statements expand to native PA and
remain unregistered pending recursive WMI review.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import prime
from .euler_scaled_inverse_prefix_candidate import (
    _scaled_inverse_index_term,
    _scaled_inverse_term,
    _strictly_below_term,
    scaled_inverse_index,
    scaled_inverse_prefix,
)
from .finite_fold_surface import _beta_at_term, beta_at
from .quadratic_residue_surface import quadratic_residue


def make_euler_scaled_inverse_prefix_extensional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build soundness, extensionality, fixed freedom, and involution."""

    entry_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="ext_entry_prefix"
    )
    entry_bound = _strictly_below_term(
        "i",
        "l",
        tag="ext_entry_bound",
        variables=("p", "a", "n", "b", "c", "l", "i", "y"),
    )
    entry_at = beta_at("b", "c", "i", "y", tag="esipe_entry_at")
    entry_relation = scaled_inverse_index(
        "p", "a", "n", "i", "y", tag="ext_entry_relation"
    )
    stored_at = beta_at("b", "c", "i", "z", tag="esipe_stored_at")
    stored_relation = scaled_inverse_index(
        "p", "a", "n", "i", "z", tag="ext_stored_relation"
    )
    stored = f"exists z. (({stored_at}) /\\ ({stored_relation}))"

    ext_prime = prime("p", tag="esipe_ext_prime")
    ext_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="extensional_prefix"
    )
    ext_bound = _strictly_below_term(
        "i",
        "l",
        tag="extensional_bound",
        variables=("p", "a", "n", "b", "c", "l", "i", "y"),
    )
    ext_relation = scaled_inverse_index(
        "p", "a", "n", "i", "y", tag="extensional_relation"
    )
    ext_result = beta_at("b", "c", "i", "y", tag="esipe_extensional_result")
    ext_stored_at = beta_at(
        "b", "c", "i", "z", tag="esipe_extensional_stored_at"
    )
    ext_stored_relation = scaled_inverse_index(
        "p", "a", "n", "i", "z", tag="extensional_stored_relation"
    )
    ext_stored = (
        f"exists z. (({ext_stored_at}) /\\ ({ext_stored_relation}))"
    )

    fixed_nonresidue = quadratic_residue("p", "a", tag="esipe_fixed_nonresidue")
    fixed_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="fixed_prefix"
    )
    fixed_bound = _strictly_below_term(
        "i",
        "l",
        tag="fixed_bound",
        variables=("p", "a", "n", "b", "c", "l", "i"),
    )
    fixed_at = _beta_at_term(
        "b",
        "c",
        "i",
        "S i",
        tag="esipe_fixed_at",
        avoid=("p", "a", "n", "b", "c", "l", "i"),
    )
    fixed_relation = _scaled_inverse_index_term(
        "p",
        "a",
        "n",
        "i",
        "S i",
        tag="fixed_relation",
        variables=("p", "a", "n", "b", "c", "l", "i"),
    )

    predecessor_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "n", tag="predecessor_prefix"
    )
    predecessor_bound = _strictly_below_term(
        "i",
        "n",
        tag="predecessor_source_bound",
        variables=("p", "a", "n", "b", "c", "i", "y"),
    )
    predecessor_at = beta_at(
        "b", "c", "i", "y", tag="esipe_predecessor_at"
    )
    predecessor_relation = scaled_inverse_index(
        "p", "a", "n", "i", "y", tag="predecessor_relation"
    )
    predecessor_result_bound = _strictly_below_term(
        "j",
        "n",
        tag="predecessor_result_bound",
        variables=("p", "a", "n", "b", "c", "i", "y", "j"),
    )

    involutive_prime = prime("p", tag="esipe_involutive_prime")
    involutive_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "n", tag="involutive_prefix"
    )
    involutive_bound = _strictly_below_term(
        "i",
        "n",
        tag="involutive_bound",
        variables=("p", "a", "n", "b", "c", "i", "y"),
    )
    involutive_at = beta_at(
        "b", "c", "i", "y", tag="esipe_involutive_at"
    )
    involutive_mate_bound = _strictly_below_term(
        "j",
        "n",
        tag="involutive_mate_bound",
        variables=("p", "a", "n", "b", "c", "i", "y", "j"),
    )
    involutive_back = _beta_at_term(
        "b",
        "c",
        "j",
        "S i",
        tag="esipe_involutive_back",
        avoid=("p", "a", "n", "b", "c", "i", "y", "j"),
    )
    forward_relation = scaled_inverse_index(
        "p", "a", "n", "i", "y", tag="involutive_forward_relation"
    )
    forward_scaled_x = _scaled_inverse_term(
        "p",
        "a",
        "S i",
        "S x",
        tag="involutive_forward_scaled",
        variables=("p", "a", "n", "b", "c", "i", "y", "x"),
    )
    reverse_scaled_x = _scaled_inverse_term(
        "p",
        "a",
        "S x",
        "S i",
        tag="involutive_reverse_scaled",
        variables=("p", "a", "n", "b", "c", "i", "y", "x"),
    )
    reverse_relation_x = _scaled_inverse_index_term(
        "p",
        "a",
        "n",
        "x",
        "S i",
        tag="involutive_reverse_relation",
        variables=("p", "a", "n", "b", "c", "i", "y", "x"),
    )
    involutive_back_x = _beta_at_term(
        "b",
        "c",
        "x",
        "S i",
        tag="esipe_involutive_back",
        avoid=("p", "a", "n", "b", "c", "i", "y", "x"),
    )

    injective_prime = prime("p", tag="esipe_injective_prime")
    injective_prefix = scaled_inverse_prefix(
        "p", "a", "n", "b", "c", "l", tag="injective_prefix"
    )
    injective_left_bound = _strictly_below_term(
        "i",
        "l",
        tag="injective_left_bound",
        variables=("p", "a", "n", "b", "c", "l", "i", "j", "y"),
    )
    injective_right_bound = _strictly_below_term(
        "j",
        "l",
        tag="injective_right_bound",
        variables=("p", "a", "n", "b", "c", "l", "i", "j", "y"),
    )
    injective_left_at = beta_at(
        "b", "c", "i", "y", tag="esipe_injective_left_at"
    )
    injective_right_at = beta_at(
        "b", "c", "j", "y", tag="esipe_injective_right_at"
    )
    injective_left_relation = scaled_inverse_index(
        "p", "a", "n", "i", "y", tag="injective_left_relation"
    )
    injective_right_relation = scaled_inverse_index(
        "p", "a", "n", "j", "y", tag="injective_right_relation"
    )
    injective_left_reverse = _scaled_inverse_term(
        "p",
        "a",
        "y",
        "S i",
        tag="injective_left_reverse",
        variables=("p", "a", "n", "b", "c", "l", "i", "j", "y"),
    )
    injective_right_reverse = _scaled_inverse_term(
        "p",
        "a",
        "y",
        "S j",
        tag="injective_right_reverse",
        variables=("p", "a", "n", "b", "c", "l", "i", "j", "y"),
    )

    return (
        spec(
            "scaled_inverse_prefix_entry_sound",
            f"forall p a n b c l i y. ({entry_prefix}) -> "
            f"({entry_bound}) -> ({entry_at}) -> ({entry_relation})",
            ("beta_at_unique",),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro y",
                "intro hprefix",
                "intro hi",
                "intro hat",
                f"have hstored : {stored}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have heq : y = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique y",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hat",
                "exact hstored_witness_left",
                "rewrite heq",
                "rewrite heq",
                "rewrite heq",
                "exact hstored_witness_right",
            ),
            "Every decoded scaled-inverse prefix entry satisfies its stored relation.",
        ),
        spec(
            "scaled_inverse_prefix_extensional",
            f"forall p a n b c l i y. ({ext_prime}) -> ({ext_prefix}) -> "
            f"({ext_bound}) -> ({ext_relation}) -> ({ext_result})",
            ("prime_scaled_inverse_unique",),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro y",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hrelation",
                f"have hstored : {ext_stored}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "cases hrelation",
                "cases hstored_witness_right",
                "have heq : y = x",
                "specialize prime_scaled_inverse_unique p",
                "specialize prime_scaled_inverse_unique a",
                "specialize prime_scaled_inverse_unique (S i)",
                "specialize prime_scaled_inverse_unique y",
                "specialize prime_scaled_inverse_unique x",
                "apply prime_scaled_inverse_unique",
                "exact hp",
                "exact hrelation_right",
                "exact hstored_witness_right_right",
                "rewrite heq",
                "rewrite heq",
                "exact hstored_witness_left",
            ),
            "A valid scaled inverse at a covered source is decoded by the prefix.",
        ),
        spec(
            "scaled_inverse_prefix_no_fixed_of_not_qres",
            f"forall p a n b c l i. ~({fixed_nonresidue}) -> "
            f"({fixed_prefix}) -> ({fixed_bound}) -> ~({fixed_at})",
            (
                "scaled_inverse_prefix_entry_sound",
                "scaled_inverse_no_fixed_of_not_qres",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro hnotqres",
                "intro hprefix",
                "intro hi",
                "intro hfixed",
                f"have hrelation : {fixed_relation}",
                "specialize scaled_inverse_prefix_entry_sound p",
                "specialize scaled_inverse_prefix_entry_sound a",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound b",
                "specialize scaled_inverse_prefix_entry_sound c",
                "specialize scaled_inverse_prefix_entry_sound l",
                "specialize scaled_inverse_prefix_entry_sound i",
                "specialize scaled_inverse_prefix_entry_sound (S i)",
                "apply scaled_inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hfixed",
                "cases hrelation",
                "specialize scaled_inverse_no_fixed_of_not_qres p",
                "specialize scaled_inverse_no_fixed_of_not_qres a",
                "specialize scaled_inverse_no_fixed_of_not_qres (S i)",
                "apply scaled_inverse_no_fixed_of_not_qres",
                "exact hnotqres",
                "exact hrelation_right",
            ),
            "A nonresidue scaled-inverse prefix has no decoded fixed point.",
        ),
        spec(
            "scaled_inverse_prefix_mate_predecessor",
            f"forall p a n b c i y. p = S n -> ({predecessor_prefix}) -> "
            f"({predecessor_bound}) -> ({predecessor_at}) -> exists j. "
            f"y = S j /\\ ({predecessor_result_bound})",
            (
                "scaled_inverse_prefix_entry_sound",
                "nonzero_is_succ",
                "le_of_succ_le_succ",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro y",
                "intro hpn",
                "intro hprefix",
                "intro hi",
                "intro hat",
                f"have hrelation : {predecessor_relation}",
                "specialize scaled_inverse_prefix_entry_sound p",
                "specialize scaled_inverse_prefix_entry_sound a",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound b",
                "specialize scaled_inverse_prefix_entry_sound c",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound i",
                "specialize scaled_inverse_prefix_entry_sound y",
                "apply scaled_inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hat",
                "cases hrelation",
                "cases hrelation_right",
                "cases hrelation_right_right",
                "cases hrelation_right_right_left",
                "have hshape : exists j. y = S j",
                "specialize nonzero_is_succ y",
                "apply nonzero_is_succ",
                "exact hrelation_right_right_left_left",
                "cases hshape",
                "have hjn : exists h. h + S x = n",
                "rewrite hshape_witness at hrelation_right_right_left_right",
                "rewrite hpn at hrelation_right_right_left_right",
                "specialize le_of_succ_le_succ (S x)",
                "specialize le_of_succ_le_succ n",
                "apply le_of_succ_le_succ",
                "exact hrelation_right_right_left_right",
                "exists x",
                "split",
                "exact hshape_witness",
                "exact hjn",
            ),
            "Every positive decoded mate has a predecessor inside the source bound.",
        ),
        spec(
            "scaled_inverse_prefix_involutive",
            f"forall p a n b c i y. p = S n -> ({involutive_prime}) -> "
            f"({involutive_prefix}) -> ({involutive_bound}) -> "
            f"({involutive_at}) -> exists j. y = S j /\\ "
            f"(({involutive_mate_bound}) /\\ ({involutive_back}))",
            (
                "scaled_inverse_prefix_mate_predecessor",
                "scaled_inverse_prefix_entry_sound",
                "scaled_inverse_symmetric",
                "scaled_inverse_prefix_extensional",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro i",
                "intro y",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hat",
                "have hpredecessor : exists j. y = S j /\\ "
                f"({involutive_mate_bound})",
                "specialize scaled_inverse_prefix_mate_predecessor p",
                "specialize scaled_inverse_prefix_mate_predecessor a",
                "specialize scaled_inverse_prefix_mate_predecessor n",
                "specialize scaled_inverse_prefix_mate_predecessor b",
                "specialize scaled_inverse_prefix_mate_predecessor c",
                "specialize scaled_inverse_prefix_mate_predecessor i",
                "specialize scaled_inverse_prefix_mate_predecessor y",
                "apply scaled_inverse_prefix_mate_predecessor",
                "exact hpn",
                "exact hprefix",
                "exact hi",
                "exact hat",
                "cases hpredecessor",
                "cases hpredecessor_witness",
                f"have hforward_relation : {forward_relation}",
                "specialize scaled_inverse_prefix_entry_sound p",
                "specialize scaled_inverse_prefix_entry_sound a",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound b",
                "specialize scaled_inverse_prefix_entry_sound c",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound i",
                "specialize scaled_inverse_prefix_entry_sound y",
                "apply scaled_inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hat",
                "cases hforward_relation",
                f"have hforward : {forward_scaled_x}",
                "rewrite hpredecessor_witness_left at hforward_relation_right",
                "rewrite hpredecessor_witness_left at hforward_relation_right",
                "rewrite hpredecessor_witness_left at hforward_relation_right",
                "exact hforward_relation_right",
                f"have hreverse : {reverse_scaled_x}",
                "specialize scaled_inverse_symmetric p",
                "specialize scaled_inverse_symmetric a",
                "specialize scaled_inverse_symmetric (S i)",
                "specialize scaled_inverse_symmetric (S x)",
                "apply scaled_inverse_symmetric",
                "exact hforward",
                f"have hreverse_relation : {reverse_relation_x}",
                "split",
                "exact hpredecessor_witness_right",
                "exact hreverse",
                "have hback : " + involutive_back_x,
                "specialize scaled_inverse_prefix_extensional p",
                "specialize scaled_inverse_prefix_extensional a",
                "specialize scaled_inverse_prefix_extensional n",
                "specialize scaled_inverse_prefix_extensional b",
                "specialize scaled_inverse_prefix_extensional c",
                "specialize scaled_inverse_prefix_extensional n",
                "specialize scaled_inverse_prefix_extensional x",
                "specialize scaled_inverse_prefix_extensional (S i)",
                "apply scaled_inverse_prefix_extensional",
                "exact hp",
                "exact hprefix",
                "exact hpredecessor_witness_right",
                "exact hreverse_relation",
                "exists x",
                "split",
                "exact hpredecessor_witness_left",
                "split",
                "exact hpredecessor_witness_right",
                "exact hback",
            ),
            "Decoding a scaled-inverse mate and decoding its predecessor returns the source residue.",
        ),
        spec(
            "scaled_inverse_prefix_injective",
            f"forall p a n b c l i j y. ({injective_prime}) -> "
            f"({injective_prefix}) -> ({injective_left_bound}) -> "
            f"({injective_right_bound}) -> ({injective_left_at}) -> "
            f"({injective_right_at}) -> i = j",
            (
                "scaled_inverse_prefix_entry_sound",
                "scaled_inverse_symmetric",
                "prime_scaled_inverse_unique",
                "succ_injective",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro j",
                "intro y",
                "intro hp",
                "intro hprefix",
                "intro hi",
                "intro hj",
                "intro hiy",
                "intro hjy",
                f"have hleft_relation : {injective_left_relation}",
                "specialize scaled_inverse_prefix_entry_sound p",
                "specialize scaled_inverse_prefix_entry_sound a",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound b",
                "specialize scaled_inverse_prefix_entry_sound c",
                "specialize scaled_inverse_prefix_entry_sound l",
                "specialize scaled_inverse_prefix_entry_sound i",
                "specialize scaled_inverse_prefix_entry_sound y",
                "apply scaled_inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hi",
                "exact hiy",
                f"have hright_relation : {injective_right_relation}",
                "specialize scaled_inverse_prefix_entry_sound p",
                "specialize scaled_inverse_prefix_entry_sound a",
                "specialize scaled_inverse_prefix_entry_sound n",
                "specialize scaled_inverse_prefix_entry_sound b",
                "specialize scaled_inverse_prefix_entry_sound c",
                "specialize scaled_inverse_prefix_entry_sound l",
                "specialize scaled_inverse_prefix_entry_sound j",
                "specialize scaled_inverse_prefix_entry_sound y",
                "apply scaled_inverse_prefix_entry_sound",
                "exact hprefix",
                "exact hj",
                "exact hjy",
                "cases hleft_relation",
                "cases hright_relation",
                f"have hleft_reverse : {injective_left_reverse}",
                "specialize scaled_inverse_symmetric p",
                "specialize scaled_inverse_symmetric a",
                "specialize scaled_inverse_symmetric (S i)",
                "specialize scaled_inverse_symmetric y",
                "apply scaled_inverse_symmetric",
                "exact hleft_relation_right",
                f"have hright_reverse : {injective_right_reverse}",
                "specialize scaled_inverse_symmetric p",
                "specialize scaled_inverse_symmetric a",
                "specialize scaled_inverse_symmetric (S j)",
                "specialize scaled_inverse_symmetric y",
                "apply scaled_inverse_symmetric",
                "exact hright_relation_right",
                "have hsucc : S i = S j",
                "specialize prime_scaled_inverse_unique p",
                "specialize prime_scaled_inverse_unique a",
                "specialize prime_scaled_inverse_unique y",
                "specialize prime_scaled_inverse_unique (S i)",
                "specialize prime_scaled_inverse_unique (S j)",
                "apply prime_scaled_inverse_unique",
                "exact hp",
                "exact hleft_reverse",
                "exact hright_reverse",
                "specialize succ_injective i",
                "specialize succ_injective j",
                "apply succ_injective",
                "exact hsucc",
            ),
            "The decoded scaled-inverse prefix is injective on every covered interval.",
        ),
    )


__all__ = ["make_euler_scaled_inverse_prefix_extensional_candidate_theorems"]
