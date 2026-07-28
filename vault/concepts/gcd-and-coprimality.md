---
title: GCD and coprimality as relations
tags: [number-theory, gcd, coprimality, peano-arithmetic]
---

Until Peano Lab has user-defined functions, `IsGCD(g,a,b)` is best represented
relationally: $g$ divides both inputs and every common divisor divides $g$.
Existence and uniqueness are now both checked. For uniqueness,
[[multiple_antisymm]] feeds [[is_gcd_unique]], while [[is_gcd_symm]],
[[is_gcd_dvd_left]], [[is_gcd_dvd_right]], and [[is_gcd_greatest]] expose the
relation's basic API. [[is_gcd_of_dvd]] handles the case in which one input
divides the other.

The checked Euclidean step begins at [[is_gcd_zero_right]]. The
subtraction-free bridge [[factor_difference]] supports
[[divides_remainder]] and [[divides_linear_step]], which in turn establish
[[is_gcd_euclid_forward]] and [[is_gcd_euclid_backward]]. These theorems show
that a division step preserves the relational gcd.

The constructive existence proof uses ordinary induction on a formula-specific
bound. [[gcd_exists_up_to]] proves that $b\le B$ implies every pair $(a,b)$ has
a relational gcd. In a successor step it divides $a=bq+r$, recursively obtains
a gcd for the smaller pair $(b,r)$, and transports it back through
[[is_gcd_euclid_forward]]. [[gcd_exists_relational]] then chooses $B=b$ using
[[le_refl]]. Their empty-context shared certificates have respectively
1,232 nodes/depth 44 and 1,268 nodes/depth 46; neither uses classical logic,
subtraction, or a primitive gcd function.

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
records the checked Euclidean-invariance certificates, the bounded
formula-specific induction route to existence, and the original
proof-composition failure. The reviewed [[self-contained-proof-sharing]] rule
removed that architectural gate, and the two existence scripts have now passed
fresh empty-context kernel checks. Balanced Bézout is the next missing bridge.

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[quotient-and-remainder]] ·
[[prime-number]] · [[self-contained-proof-sharing]]
