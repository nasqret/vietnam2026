---
title: Prime number in Peano Lab
tags: [number-theory, prime, peano-arithmetic]
---

A natural $p$ is prime when $p\ne1$ and every factorization $p=a\cdot b$ has
$a=1$ or $b=1$. This is equivalent over the naturals to saying every divisor
is either one or $p$. In Peano Lab the condition expands to multiplication and
quantifiers; `Prime` is not a kernel atom.

The checked theorem [[prime_two]] is the first concrete instance of that fully
expanded predicate. [[prime_divisor_eq_one_or_self]] supplies the reusable
general divisor characterization, and [[euclids-lemma]] is also now checked. The
remaining prime ladder proves zero and one non-prime, that every number at
least two has a prime divisor, and that primes occur above every bound. Those
remaining claims are expressible in the current first-order language but are
not yet checked library entries.

Their gcd prerequisite has advanced: [[gcd_exists_up_to]] and
[[gcd_exists_relational]] construct a relational gcd for every pair, while
[[gcd_balanced_bezout_exists]], [[coprime_balanced_bezout]], and
[[gauss_coprime_cancel]] close the constructive route to Euclid's lemma.
Bounded prime-divisor search remains independent: Euclid's lemma controls a
prime that is already given; it does not produce one.

## Related

[[arithmetic-library-moc]] · [[gcd-and-coprimality]] ·
[[fundamental-theorem-of-arithmetic]]
