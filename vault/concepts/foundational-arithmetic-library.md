---
title: Foundational arithmetic library
tags: [peano-arithmetic, library, number-theory]
---

The **foundational arithmetic library** is a versioned dependency graph for
[[peano-lab]], organized from equality and semiring laws through [[divisibility]],
[[arithmetic-congruence]], [[quotient-and-remainder]], gcd, primes, and
factorization.

Its current snapshot has 183 closed, independently checked theorems: the
original 23-node [[theorem-ladder]] and 160 unique post-baseline additions.
The latter combine 148 general arithmetic facts with twelve additional modular
capstones. The 190-node research catalog separates 23 `checked_existing`,
160 `checked_m20`, three
`planned_expressible`, and four `blocked_by_language` nodes, but only replayed
certificates appear in `pa lib`. The M20 additions now include [[prime_two]],
the first checked instance of the fully expanded prime predicate, and native
[[quotient-and-remainder]] existence and uniqueness.
It also contains the relational [[gcd-and-coprimality]] API through uniqueness
and Euclidean-step invariance, plus [[gcd_exists_up_to|bounded]] and
[[gcd_exists_relational|general]] relational gcd existence. The checked
[[gcd_balanced_bezout_exists|balanced gcd/Bézout construction]] now feeds
[[coprime_balanced_bezout]], [[gauss_coprime_cancel]],
[[prime_divisor_eq_one_or_self]], and
[[euclid_prime_dvd_product|Euclid's lemma]].

The newest constructive search chain starts with [[eq_decidable]],
[[multiple_decidable_nonzero]], and [[multiple_decidable]]. It extends bounded
factor properties via [[factor_property_succ]] and [[factor_search_up_to]],
uses [[factor_nonzero_left]] and [[proper_factor_lt]] for descent, and exposes
[[prime_nonzero]], [[prime_or_composite]], [[prime_decidable]],
[[prime_divisor_exists_up_to]], and [[prime_divisor_exists]]. Thus both
primality decision and prime-divisor existence are native checked results, not
classical witness extraction.

The congruence API now includes [[mod_eq_trans]] and [[mod_eq_add]]. The first
conservative sequence layer includes [[beta_modulus_nonzero]],
[[beta_at_self_of_bound]], [[beta_at_exists]], [[beta_at_unique]], and
[[beta_at_exists_unique]], proving total and functional decoding at one
Gödel-β position without adding a sequence primitive.
The next pre-CRT layer closes multiplication compatibility through
[[mod_eq_mul]] and links directed remainders and decoded β values via
[[remainder_decomposition_to_mod_eq]] and [[beta_at_to_mod_eq]].
The reverse bridge is now checked too: [[mod_eq_bounded_unique]],
[[mod_eq_to_remainder_decomposition]], and [[beta_at_of_mod_eq_bound]] recover
directed remainder and β witnesses from bounded congruence.
The newest six-node layer projects balanced Bézout identities through
[[bezout_mod_left]] and [[bezout_mod_right]], implements subtraction-free
successor-modulus cancellation with [[mod_eq_predecessor_cancel]], and checks
[[binary_crt]], [[binary_crt_remainders]], and [[binary_crt_beta_pair]]. The
last theorem constructs one code for two bounded β values under an explicit
coprimality premise.

The new six-node β arithmetic layer proves
[[beta_modulus_coprime_base]], shows with
[[common_divisor_beta_moduli_divides_gap_times_c]] that every common divisor
of two ordered β moduli divides the index gap times `c`, and derives
[[beta_moduli_coprime_of_gap_dvd]]. Thus
[[binary_crt_beta_pair_of_gap_dvd]] discharges the earlier CRT premise when
`j = i + gap` and `gap | c`. Independently,
[[bounded_common_multiple_step]] and [[bounded_common_multiple_exists]]
construct a nonzero `c` divisible by all positive naturals through a
chosen bound. Arbitrary β moduli are not pairwise coprime; `c = 1` at
indices 1 and 4 gives the counterexample 3 and 6.

The next seven-node layer closes the finite-bound glue:
[[beta_moduli_coprime_of_lt_bounded_common_multiple]],
[[beta_moduli_pairwise_coprime_bounded]], and
[[bounded_beta_moduli_pairwise_coprime_exists]] construct one nonzero base
whose distinct β moduli through a chosen bound are pairwise coprime.
[[coprime_mul_left]] and [[coprime_mul_right]] lift that invariant to
accumulated products; [[mod_eq_of_mod_eq_multiple]] descends congruence from a
product modulus to its factors; and [[binary_crt_fold_step]] performs one CRT
extension while preserving every earlier congruence whose modulus divides the
accumulated product.

The generated snapshot contains 154,220 structural proof nodes and 4,293
self-contained Cuts; 143 of the 183 certificates contain a Cut. Its maximum
certificate is [[binary_crt_beta_pair_of_gap_dvd]] at 12,980 nodes and 378 Cuts, and its
maximum depth is 80 at [[prime_divisor_exists]]. The ordered snapshot root is
`09359430226349a7d5fdd1fd67376d345bc1bb5f707e746e8b58c2799086f2d6`.
These are representation metrics, not proof authority.

The checkpoint passed all 1,098 Peano tests. The independent Lambda Lab
regression remains green at 360 tests plus 36 subtests; the arithmetic changes
do not alter that calculus or its kernel.

One theorem name identifies its executable entry, generated artifact node,
Obsidian lemma page, and book discussion. [[lemma-dependency-dag]] records the
ordering; [[arithmetic-library-provenance]] records why facts were selected and
how external material may be reused. Replay discharges dependency edges with
[[self-contained-proof-sharing]], embedding full checked certificates rather
than granting names or hashes kernel authority.

The [[fundamental-theorem-of-arithmetic]] is a destination, not a primitive.
A conservative [[godel-beta-sequence]] representation is selected and a Lean
companion checks the full list theorem, while Peano admission still requires
greatest-prime descent, the actual bounded CRT fold and its encoded-product
invariant, β finite-prefix recoding, prefix-product, and finite-product
certificates.

## Related

[[arithmetic-library-moc]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[self-contained-proof-sharing]] · [[trusted-kernel]]
