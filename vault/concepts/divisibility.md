---
title: Divisibility over the natural numbers
tags: [number-theory, divisibility, peano-arithmetic]
---

In the current Peano language,

$$
a\mid b \quad\Longleftrightarrow\quad \exists q.\ b=a\cdot q.
$$

This is an abbreviation in documentation, not a new trusted predicate. The
checked foundation includes [[multiple_zero]], [[one_multiple]],
[[multiple_refl]], [[multiple_add]], [[multiple_mul_right]],
[[multiple_mul_left]], and [[multiple_trans]]. The pair
[[not_multiple_pointwise]] and [[not_multiple_from_pointwise]] moves between a
negated existential and pointwise inequalities constructively.

Divisibility supports [[arithmetic-congruence]], [[gcd-and-coprimality]], and
the definition of a [[prime-number]].

## Related

[[arithmetic-library-moc]] · [[quotient-and-remainder]] · [[euclids-lemma]]
