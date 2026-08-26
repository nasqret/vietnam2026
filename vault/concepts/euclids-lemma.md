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
second, $p=g$ and the gcd's divisibility witness yields $p\mid a$.

Constructive prime production is a separate proof problem, now solved by
[[prime_divisor_exists]] through [[factor_search_up_to]],
[[prime_or_composite]], [[proper_factor_lt]], and the bounded descent theorem
[[prime_divisor_exists_up_to]]. Euclid's lemma remains the uniqueness-side
tool; prime-divisor existence is the arithmetic entrance to factorization
existence.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[gcd-and-coprimality]]
