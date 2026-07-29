---
title: "Lemma: mul_succ_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_succ_left`

A successor can move through multiplication on the left.

## Closed Peano statement

```text
forall n m. S n * m = n * m + m
```

## Dependencies

- [[add_comm]]
- [[add_assoc]]

## Checked dependents

- [[mul_comm]]
- [[two_large_factors_impossible]]
- [[mod_eq_predecessor_cancel]]
- [[base_le_beta_modulus]]
- [[prime_three]]
- [[mod5_square_residue_one]]
- [[mod5_square_residue_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **172 nodes**, depth **22**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib mul_succ_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
