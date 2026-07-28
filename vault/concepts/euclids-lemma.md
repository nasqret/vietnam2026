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
[[fundamental-theorem-of-arithmetic]]. It is now admitted natively as
[[euclid_prime_dvd_product]], with the factor-pair definition of primality and
all divisibility relations expanded in the stored first-order formula. Its
closed shared certificate has 5,382 nodes and depth 55 and checks in the
intuitionistic kernel.

The proof chooses a relational gcd $g$ of $(p,a)$.
[[prime_divisor_eq_one_or_self]] turns $g\mid p$ into $g=1$ or $p=g$. In the
first branch,
[[is_gcd_one_to_coprime]] and [[gauss_coprime_cancel]] yield $p\mid b$; in the
second, $p=g$ and the gcd's divisibility witness yields $p\mid a$. Constructive
prime-divisor existence is still a separate theorem.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[gcd-and-coprimality]]
