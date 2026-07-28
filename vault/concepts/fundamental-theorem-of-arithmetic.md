---
title: Fundamental Theorem of Arithmetic
tags: [number-theory, factorization, prime, language-boundary]
---

The **Fundamental Theorem of Arithmetic** has two parts: every natural greater
than one is a finite product of primes, and that product is unique up to order
or prime multiplicity.

Strong induction and prime-divisor existence support existence;
[[euclids-lemma]] supports uniqueness. The present Peano term language cannot
naturally quantify over arbitrary finite lists, multisets, exponent maps, or
products. The theorem is therefore `blocked_by_language` on a reviewed
finite-factorization representation.

Gödel coding could remain inside first-order arithmetic, but it would make a
poor reusable interface. The preferred milestone adds an explicit finite
sequence or multiset layer and proves its product/permutation laws before FTA
is exposed through `pa lib`.

## Related

[[arithmetic-library-moc]] · [[prime-number]] · [[lemma-dependency-dag]] ·
[[trusted-kernel]]
