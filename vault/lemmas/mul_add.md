---
title: "Lemma: mul_add"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_add`

Multiplication distributes over addition on the right.

## Closed Peano statement

```text
forall n m k. n * (m + k) = n * m + n * k
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- [[mul_assoc]]
- [[add_mul]]
- [[mul_le_mul_left]]
- [[positive_quotient_gap_impossible]]
- [[multiple_add]]
- [[divides_linear_step]]
- [[add_residue]]
- [[add_residue_lift]]
- [[square_decomp]]
- [[mod5_square_residue_one]]
- [[mod5_square_residue_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **71 nodes**, depth **22**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib mul_add`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
