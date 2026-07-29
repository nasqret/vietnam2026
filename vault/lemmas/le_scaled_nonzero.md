---
title: "Lemma: le_scaled_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_scaled_nonzero`

Scaling by a nonzero natural does not decrease a natural.

## Closed Peano statement

```text
forall C B. ~(C = 0) -> exists h. h + B = C * B
```

## Dependencies

- [[one_le_of_ne_zero]]
- [[mul_le_mul_right]]
- [[one_mul]]

## Checked dependents

- [[beta_value_lt_scaled_base]]
- [[new_value_lt_scaled_base]]

## Verification record

- Independently checked from the empty context.
- Certificate: **407 nodes**, depth **28**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib le_scaled_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
