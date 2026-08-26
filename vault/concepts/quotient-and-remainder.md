---
title: Quotient and remainder
tags: [number-theory, division-algorithm, peano-arithmetic]
---

For positive divisor $m$, the division algorithm gives $q,r$ with

$$
n=mq+r,\qquad r<m.
$$

Existence needs induction; uniqueness needs order and cancellation. Both are
now checked natively. `division_remainder_exists` constructs a quotient and a
strictly bounded remainder for every nonzero divisor;
`division_remainder_unique` proves that any two such decompositions have the
same quotient and remainder. Its certificate has 1,442 nodes and depth 47.

The supporting checked ladder includes `remainder_bound_step`,
`division_block_upper`, `positive_quotient_gap_impossible`, and
`remainder_unique_same_quotient`. The bridges
`zero_remainder_implies_multiple` and `multiple_has_zero_remainder` connect
division back to [[divisibility]]. No primitive division or remainder symbol
was added.

Canonical remainders connect [[divisibility]] to [[arithmetic-congruence]] and
provide the computational basis for Euclidean gcd proofs.

## Related

[[arithmetic-library-moc]] · [[gcd-and-coprimality]] · [[division_remainder_exists]] ·
[[division_remainder_unique]] · [[add_left_cancel]]
