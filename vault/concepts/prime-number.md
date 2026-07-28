---
title: Prime number in Peano Lab
tags: [number-theory, prime, peano-arithmetic]
---

A natural $p$ is prime when $p\ne1$ and every factorization $p=a\cdot b$ has
$a=1$ or $b=1$. This is equivalent over the naturals to saying every divisor
is either one or $p$. In Peano Lab the condition expands to multiplication and
quantifiers; `Prime` is not a kernel atom.

The checked theorem [[prime_two]] is the first concrete instance of that fully
expanded predicate. [[prime_nonzero]] proves the general boundary fact,
[[prime_divisor_eq_one_or_self]] supplies the reusable divisor
characterization, and [[euclids-lemma]] is checked independently.

The constructive decision/search spine is now checked as well:

- [[eq_decidable]] → [[multiple_decidable_nonzero]] →
  [[factor_search_up_to]] → [[prime_or_composite]] →
  [[prime_decidable]];
- [[prime_or_composite]] + [[proper_factor_lt]] →
  [[prime_divisor_exists_up_to]] → [[prime_divisor_exists]].

Here [[multiple_decidable]] includes the zero-divisor case,
[[factor_property_succ]] extends the bounded universal factor condition, and
[[factor_nonzero_left]] isolates a reusable nonzero-factor fact. The search
returns an explicit factor pair before descending; it does not infer a witness
from a negated prime formula.

Their gcd prerequisite has advanced: [[gcd_exists_up_to]] and
[[gcd_exists_relational]] construct a relational gcd for every pair, while
[[gcd_balanced_bezout_exists]], [[coprime_balanced_bezout]], and
[[gauss_coprime_cancel]] close the constructive route to Euclid's lemma.
Prime-divisor search remains logically independent from Euclid's lemma:
[[prime_divisor_exists]] produces a prime, whereas Euclid controls a prime
already supplied. Both directions are now present. The remaining prime targets
are primes above every bound and greatest-prime-divisor descent for the sorted
[[fundamental-theorem-of-arithmetic|factorization]] construction.

## Related

[[arithmetic-library-moc]] · [[gcd-and-coprimality]] ·
[[fundamental-theorem-of-arithmetic]]
