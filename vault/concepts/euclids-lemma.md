---
title: Euclid's lemma
tags: [number-theory, prime, divisibility]
---

**Euclid's lemma** says that if a [[prime-number]] $p$ divides $ab$, then it
divides $a$ or $b$. Its proof route in this library is explicit:

$$
\text{division}\to\gcd\to\text{Bézout}\to
\text{Gauss cancellation}\to\text{Euclid's lemma}.
$$

It is the central uniqueness tool for the
[[fundamental-theorem-of-arithmetic]]. It is first-order expressible today, but
the prerequisite gcd/Bézout nodes must be checked before admission.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[gcd-and-coprimality]]
