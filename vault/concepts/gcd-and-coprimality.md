---
title: GCD and coprimality as relations
tags: [number-theory, gcd, coprimality, peano-arithmetic]
---

Until Peano Lab has user-defined functions, `IsGCD(g,a,b)` is best represented
relationally: $g$ divides both inputs and every common divisor divides $g$.
Existence will follow the Euclidean algorithm. Uniqueness is already checked:
[[multiple_antisymm]] feeds [[is_gcd_unique]], while [[is_gcd_symm]],
[[is_gcd_dvd_left]], [[is_gcd_dvd_right]], and [[is_gcd_greatest]] expose the
relation's basic API. [[is_gcd_of_dvd]] handles the case in which one input
divides the other.

Coprimality means that one satisfies this relation. Bézout coefficients can be
encoded by four naturals:

$$
a x_+ + b y_+ = 1 + a x_- + b y_-.
$$

That subtraction-free form is sufficient for Gauss cancellation and
[[euclids-lemma]].

The checked unit bridge consists of [[mul_eq_one_components]], [[divisor_one]],
[[coprime_one_left]], [[coprime_one_right]], [[coprime_to_is_gcd_one]], and
[[is_gcd_one_to_coprime]]. It establishes the exact equivalence between the
expanded common-divisor definition of coprimality and `IsGCD(1,a,b)`.

The [native gcd/Bézout roadmap](../../research/arithmetic-library/gcd-bezout-roadmap.md)
records the prototype Euclidean-invariance certificates, the bounded
formula-specific induction route to existence, and the current proof-sharing
gate.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[quotient-and-remainder]] ·
[[prime-number]]
