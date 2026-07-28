---
title: Foundational arithmetic library
tags: [peano-arithmetic, library, number-theory]
---

The **foundational arithmetic library** is a versioned dependency graph for
[[peano-lab]], organized from equality and semiring laws through [[divisibility]],
[[arithmetic-congruence]], [[quotient-and-remainder]], gcd, primes, and
factorization.

Its current snapshot has 137 closed, independently checked theorems: the
original 23-node [[theorem-ladder]] and 114 unique post-baseline additions.
The latter combine 102 general arithmetic facts with twelve additional modular
capstones. The 148-node research catalog separates 23 `checked_existing`,
114 `checked_m20`, seven
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

The generated snapshot contains 52,433 structural proof nodes and 1,345
trusted Cuts; 98 of the 137 certificates contain a Cut. Its maximum
certificate is [[euclid_prime_dvd_product]] at 5,382 nodes, and its maximum
depth is 57. These are representation metrics, not proof authority.

One theorem name identifies its executable entry, generated artifact node,
Obsidian lemma page, and book discussion. [[lemma-dependency-dag]] records the
ordering; [[arithmetic-library-provenance]] records why facts were selected and
how external material may be reused. Replay discharges dependency edges with
[[self-contained-proof-sharing]], embedding full checked certificates rather
than granting names or hashes kernel authority.

The [[fundamental-theorem-of-arithmetic]] is a destination, not a primitive.
A conservative [[godel-beta-sequence]] representation is selected and a Lean
companion checks the full list theorem, while Peano admission still requires
the encoded sequence/product and arithmetic certificates.

## Related

[[arithmetic-library-moc]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[self-contained-proof-sharing]] · [[trusted-kernel]]
