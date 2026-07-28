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
multiplication compatibility remains planned from [[divisibility]] and
semiring laws.

The checked [[add_residue]], [[add_residue_lift]], [[square_decomp]],
[[square_residue_lift]], and [[square_residue_witness]] already manipulate
explicit quotient-and-remainder equations generically. Fixed-modulus residue
exhaustions should be clients of [[quotient-and-remainder]], not separate
foundations.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[prime-number]]
