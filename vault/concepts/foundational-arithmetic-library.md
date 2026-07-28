---
title: Foundational arithmetic library
tags: [peano-arithmetic, library, number-theory]
---

The **foundational arithmetic library** is a versioned dependency graph for
[[peano-lab]], organized from equality and semiring laws through [[divisibility]],
[[arithmetic-congruence]], gcd, primes, and factorization.

Its current snapshot has 63 closed, independently checked theorems: the
original 23-node [[theorem-ladder]] and 40 unique post-baseline additions.
The latter combine 28 general M20 facts with twelve additional modular
capstones; fourteen records shared by both source branches are identical and
deduplicated. The 87-node research catalog separates 23 `checked_existing`,
40 `checked_m20`, 20
`planned_expressible`, and four `blocked_by_language` nodes, but only replayed
certificates appear in `pa lib`. The M20 additions now include [[prime_two]],
the first checked instance of the fully expanded prime predicate.

One theorem name identifies its executable entry, generated artifact node,
Obsidian lemma page, and book discussion. [[lemma-dependency-dag]] records the
ordering; [[arithmetic-library-provenance]] records why facts were selected and
how external material may be reused.

The [[fundamental-theorem-of-arithmetic]] is a destination, not a primitive.
A conservative [[godel-beta-sequence]] representation is selected and a Lean
companion checks the full list theorem, while Peano admission still requires
the encoded sequence/product and arithmetic certificates.

## Related

[[arithmetic-library-moc]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[trusted-kernel]]
