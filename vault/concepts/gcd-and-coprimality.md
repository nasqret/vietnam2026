---
title: GCD and coprimality as relations
tags: [number-theory, gcd, coprimality, peano-arithmetic]
---

Until Peano Lab has user-defined functions, `IsGCD(g,a,b)` is best represented
relationally: $g$ divides both inputs and every common divisor divides $g$.
Existence follows the Euclidean algorithm; uniqueness uses divisibility
antisymmetry.

Coprimality means that one satisfies this relation. Bézout coefficients can be
encoded by four naturals:

$$
a x_+ + b y_+ = 1 + a x_- + b y_-.
$$

That subtraction-free form is sufficient for Gauss cancellation and
[[euclids-lemma]].

## Related

[[arithmetic-library-moc]] · [[divisibility]] · [[quotient-and-remainder]] ·
[[prime-number]]
