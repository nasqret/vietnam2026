---
title: "Lemma: mul_left_cancel_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_left_cancel_nonzero`

A nonzero common left factor can be cancelled.

## Closed Peano statement

```text
forall a b c. ~(a = 0) -> a * b = a * c -> b = c
```

## Dependencies

- [[mul_eq_zero]]
- [[mul_ne_zero]]
- [[add_right_cancel]]
- [[succ_ne_zero]]

## Checked dependents

- [[mul_right_cancel_nonzero]]
- [[multiple_antisymm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **224 nodes**, depth **23**.
- Authored script length: **42 commands**.
- Runtime card: `pa lib mul_left_cancel_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
