---
title: "Lemma: mul_comm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_comm`

Multiplication is commutative.

## Closed Peano statement

```text
forall n m. n * m = m * n
```

## Dependencies

- [[mul_zero_left]]
- [[mul_succ_left]]

## Checked dependents

- [[add_mul]]
- [[mul_right_cancel_nonzero]]
- [[multiple_mul_left]]
- [[balanced_combination_scale_right]]
- [[square_decomp]]

## Verification record

- Independently checked from the empty context.
- Certificate: **222 nodes**, depth **24**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib mul_comm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
