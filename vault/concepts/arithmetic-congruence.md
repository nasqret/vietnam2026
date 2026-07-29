---
title: Modular congruence without subtraction
tags: [number-theory, modular-arithmetic, peano-arithmetic]
---

A symmetric natural-number encoding is

$$
a\equiv b\pmod m
\quad\Longleftrightarrow\quad
\exists u\,v.\ a+m u=b+m v.
$$

It needs neither integer subtraction nor a remainder primitive. Reflexivity,
symmetry, and transitivity are checked as [[mod_eq_refl]], [[mod_eq_symm]], and
[[mod_eq_trans]]. Addition compatibility is checked as [[mod_eq_add]];
multiplication compatibility is checked through [[mod_eq_mul_right]],
[[mod_eq_mul_left]], and [[mod_eq_mul]].

[[remainder_decomposition_to_mod_eq]] turns a directed quotient/remainder
equation into this balanced relation. [[beta_at_to_mod_eq]] specializes that
bridge to the fully expanded Gödel-β decoding formula, providing the interface
needed before a constructive CRT proof. In the reverse direction,
[[mod_eq_bounded_unique]] identifies bounded representatives and
[[mod_eq_to_remainder_decomposition]] reconstructs the directed quotient.
[[beta_at_of_mod_eq_bound]] packages the corresponding reverse β bridge.

The checked CRT layer stays inside the same subtraction-free interface.
[[bezout_mod_left]] and [[bezout_mod_right]] project balanced natural Bézout
coefficients into the two modular inverse equations, while
[[mod_eq_predecessor_cancel]] implements the required minus-one behavior
modulo a successor. [[binary_crt]] then constructs one solution to two
balanced congruences for nonzero coprime moduli, and
[[binary_crt_remainders]] converts bounded requested residues back to directed
quotient/remainder equations.

This is binary CRT, not bounded CRT iteration. In the original β specialization
[[binary_crt_beta_pair]], coprimality of the two β moduli remains an explicit
premise. [[beta_moduli_coprime_of_gap_dvd]] now proves that premise when
`j = i + gap` and `gap | c`, and
[[binary_crt_beta_pair_of_gap_dvd]] applies it directly. The companion
[[bounded_common_multiple_exists]] constructs a nonzero `c` divisible
by every positive gap through a chosen bound.
[[beta_moduli_pairwise_coprime_bounded]] and
[[bounded_beta_moduli_pairwise_coprime_exists]] now close the bounded-prefix
pairwise-coprimality theorem. [[coprime_mul_left]] and
[[coprime_mul_right]] support accumulated product moduli,
[[mod_eq_of_mod_eq_multiple]] recovers every earlier congruence from the
product congruence, and [[binary_crt_fold_step]] checks one preservation step.
The accumulated-product and decoded-congruence successor lemmas are now
combined in [[beta_crt_prefix_invariant_step]] and folded by ordinary induction
in [[bounded_beta_crt_prefix_invariant]]. Its wrapper
[[bounded_beta_crt_for_existing_code]] applies only to residues already
decoded from a supplied `BetaAt` code; it is not arbitrary finite-sequence
coding. Genuine prefix-product recurrence and bounds remain next.

The checked [[add_residue]], [[add_residue_lift]], [[square_decomp]],
[[square_residue_lift]], and [[square_residue_witness]] already manipulate
explicit quotient-and-remainder equations generically. Fixed-modulus residue
exhaustions should be clients of [[quotient-and-remainder]], not separate
foundations.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[prime-number]] ·
[[godel-beta-sequence]]
