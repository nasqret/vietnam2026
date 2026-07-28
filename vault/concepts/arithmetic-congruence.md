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

The checked [[add_residue]], [[add_residue_lift]], [[square_decomp]],
[[square_residue_lift]], and [[square_residue_witness]] already manipulate
explicit quotient-and-remainder equations generically. Fixed-modulus residue
exhaustions should be clients of [[quotient-and-remainder]], not separate
foundations.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[prime-number]]
