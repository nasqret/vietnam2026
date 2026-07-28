---
title: Foundational arithmetic library
tags: [peano-arithmetic, library, number-theory]
---

The **foundational arithmetic library** is a versioned dependency graph for
[[peano-lab]], organized from equality and semiring laws through [[divisibility]],
[[arithmetic-congruence]], gcd, primes, and factorization.

Its first snapshot has 51 closed, independently checked theorems: the original
23-node [[theorem-ladder]] and 28 general additions. The 75-node research
catalog separates 23 `checked_existing`, 28 `checked_m20`, 20
`planned_expressible`, and four `blocked_by_language` nodes, but only replayed
certificates appear in `pa lib`. The M20 additions now include [[prime_two]],
the first checked instance of the fully expanded prime predicate.

One theorem name identifies its executable entry, generated artifact node,
Obsidian lemma page, and book discussion. [[lemma-dependency-dag]] records the
ordering; [[arithmetic-library-provenance]] records why facts were selected and
how external material may be reused.

The [[fundamental-theorem-of-arithmetic]] is a destination, not a primitive.
Its current blocker is a readable finite-factorization representation.

## Related

[[arithmetic-library-moc]] · [[proof-certificate]] · [[checked-theorem-reuse]] ·
[[trusted-kernel]]
