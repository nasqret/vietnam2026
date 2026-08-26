---
title: Constructive prime unboundedness
tags: [peano-arithmetic, primes, divisibility, induction]
---

# Constructive prime unboundedness

The checked theorem `prime_unbounded` states, with primality expanded into its
factor-pair formula, that every natural `n` has a prime `p` with `n < p`.
Its proof does not require a factorial function or the
[[fundamental-theorem-of-arithmetic]].

First, [[bounded_common_multiple_exists]] constructs a nonzero `c` divisible
by every positive natural at most `n`. Then [[prime_divisor_exists]] supplies a
prime `p` dividing `S c`. If `p <= n`, [[prime_nonzero]] and the bounded common
multiple property also give `p | c`. The checked consecutive-number remainder
lemma makes a divisor of both `c` and `S c` divide one, and [[divisor_one]]
then forces `p = 1`, contradicting the expanded prime premise. Therefore
`n < p`.

The exact certificate has 4,595 structural nodes, depth 82, and 146
self-contained Cuts. Its SHA-256 is
`8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
It uses PA1–PA6 only, contains no DNE, and passes exact-statement,
dependency-slot, PA-leaf, authored-hypothesis, and live-use audits.

## Related

[[foundational-arithmetic-library]] · [[lemma-dependency-dag]] ·
[[prime_divisor_exists]] · [[bounded_common_multiple_exists]] ·
[[intuitionistic-logic]]
