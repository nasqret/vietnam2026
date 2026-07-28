---
title: Foundational arithmetic library
tags: [peano-arithmetic, library, number-theory]
---

The **foundational arithmetic library** is a versioned dependency graph for
[[peano-lab]], organized from equality and semiring laws through [[divisibility]],
[[arithmetic-congruence]], [[quotient-and-remainder]], gcd, primes, and
factorization.

Its current snapshot has 149 closed, independently checked theorems: the
original 23-node [[theorem-ladder]] and 126 unique post-baseline additions.
The latter combine 114 general arithmetic facts with twelve additional modular
capstones. The 158-node research catalog separates 23 `checked_existing`,
126 `checked_m20`, five
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

The generated snapshot contains 67,844 structural proof nodes and 1,800
self-contained Cuts; 109 of the 149 certificates contain a Cut. Its maximum
certificate is [[euclid_prime_dvd_product]] at 5,382 nodes, and its maximum
depth is 80 at [[prime_divisor_exists]]. These are representation metrics, not
proof authority.

One theorem name identifies its executable entry, generated artifact node,
Obsidian lemma page, and book discussion. [[lemma-dependency-dag]] records the
ordering; [[arithmetic-library-provenance]] records why facts were selected and
how external material may be reused. Replay discharges dependency edges with
[[self-contained-proof-sharing]], embedding full checked certificates rather
than granting names or hashes kernel authority.

The [[fundamental-theorem-of-arithmetic]] is a destination, not a primitive.
A conservative [[godel-beta-sequence]] representation is selected and a Lean
companion checks the full list theorem, while Peano admission still requires
greatest-prime descent and the encoded β-value/CRT, finite-prefix,
prefix-product, and finite-product certificates.

## Related

[[arithmetic-library-moc]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[self-contained-proof-sharing]] · [[trusted-kernel]]
