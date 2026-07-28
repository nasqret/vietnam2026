---
title: Quotient and remainder
tags: [number-theory, division-algorithm, peano-arithmetic]
---

For positive divisor $m$, the division algorithm gives $q,r$ with

$$
n=mq+r,\qquad r<m.
$$

Existence needs induction; uniqueness needs order and cancellation. The
current checked library provides generic equation transport through
[[add_residue]] and [[square_residue_lift]], while bounded remainder existence
and uniqueness remain `planned_expressible` nodes.

Canonical remainders connect [[divisibility]] to [[arithmetic-congruence]] and
provide the computational basis for Euclidean gcd proofs.

## Related

[[arithmetic-library-moc]] · [[gcd-and-coprimality]] · [[add_left_cancel]] ·
[[le_antisymm]]
