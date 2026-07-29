---
title: Gödel beta sequence encoding
tags: [peano-arithmetic, sequence, arithmetization, factorization]
---

A finite natural-number sequence can be represented without adding a list sort
to Peano Lab. For code parameters $b,c$, index $i$, and value $x$, define

$$
M(c,i)=1+(i+1)c,
\qquad
\operatorname{At}(b,c,i,x)
\iff x<M(c,i)\land\exists q.\;b=qM(c,i)+x.
$$

All components expand to `0`, `S`, addition, multiplication, equality, and
quantifiers. A second beta sequence records prefix products. Bounded
`[[prime-number]]` conditions and sorted adjacent entries then define a
canonical finite prime factorization.

Codes are not sequence identities: two code pairs may decode the same finite
prefix. Extensional equality therefore compares length and every decoded
bounded entry. Natural [[quotient-and-remainder]] and [[euclids-lemma]] are now
checked. Constructive [[prime_divisor_exists|prime-divisor existence]] is now
checked as well, through [[prime_or_composite]], [[proper_factor_lt]], and
formula-specific bounded descent.

The single-position decoding API is also checked. [[beta_modulus_nonzero]]
records that every modulus is a successor, [[beta_at_self_of_bound]] supplies
the quotient-zero base constructor, and [[beta_at_exists]], [[beta_at_unique]],
and [[beta_at_exists_unique]] prove totality and functionality of the fully
expanded `At` relation. These facts decode one position.
[[beta_at_to_mod_eq]] now connects each directed decoding witness to the
balanced [[arithmetic-congruence]] API. [[mod_eq_bounded_unique]] and
[[mod_eq_to_remainder_decomposition]] prove the reverse direction, exposed for
β values as [[beta_at_of_mod_eq_bound]]. Thus `At(b,c,i,x)` is now equivalent
to the bound on `x` plus congruence of `b` and `x` modulo `M(c,i)`.

The first composition step is now checked. [[binary_crt]] constructs a
solution for two nonzero coprime moduli, and [[binary_crt_beta_pair]]
specializes it to a single code realizing two bounded β values under an
explicit coprimality premise.

Unconditional pairwise coprimality of β moduli is false. With `c=1`,
indices 1 and 4 produce

$$
M(1,1)=3,\qquad M(1,4)=6,
$$

which have common divisor 3. The correct checked theorem is conditional:
[[common_divisor_beta_moduli_divides_gap_times_c]] controls a common divisor
when `j=i+\mathit{gap}`, and [[beta_moduli_coprime_of_gap_dvd]]
proves coprimality when additionally `\mathit{gap}\mid c`.
[[binary_crt_beta_pair_of_gap_dvd]] therefore constructs the two-position code
with no separate coprimality premise.

The other half of the finite-bound strategy is also checked.
[[bounded_common_multiple_step]] and [[bounded_common_multiple_exists]]
construct a nonzero `c` divisible by every positive natural up to a
chosen bound. [[beta_moduli_coprime_of_lt_bounded_common_multiple]] turns this
into ordered coprimality, [[beta_moduli_pairwise_coprime_bounded]] handles both
index orders, and [[bounded_beta_moduli_pairwise_coprime_exists]] packages a
nonzero base for the whole bounded prefix.

The fold algebra is checked as well. [[coprime_mul_left]] and
[[coprime_mul_right]] preserve coprimality under accumulated products,
[[mod_eq_of_mod_eq_multiple]] descends a product-modulus congruence to each
factor, and [[binary_crt_fold_step]] adds one residue while preserving all old
congruences. [[beta_accumulated_product_step]] and
[[beta_crt_prefix_congruence_step]] advance the two invariant components;
[[beta_crt_prefix_invariant_step]] combines them, and
[[bounded_beta_crt_prefix_invariant]] performs the bounded iteration by
ordinary induction. [[bounded_beta_crt_for_existing_code]] then projects a
common witness for residues already decoded from a supplied `BetaAt` code.
Extensionally the supplied code is itself such a witness, so this is not a
theorem coding an arbitrary finite sequence or a β code for a product trace.

The next encoding gate is genuine prefix-product recurrence and bounds, β
finite-prefix recoding, and prefix-product trace
existence/functionality/composition. Greatest-prime-divisor descent remains
needed for the sorted factor order, together with
preservation of bounded primality and sorting, and finite-product
Euclid/cancellation. None of those relations is a trusted primitive, and the
checked existing-code bounded wrapper does not by itself constitute
[[fundamental-theorem-of-arithmetic|FTA]].

## Related

[[fundamental-theorem-of-arithmetic]] · [[trusted-kernel]] ·
[[arithmetic-library-moc]]
