---
title: "Lemma: mul_ne_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_ne_zero`

A product of two nonzero naturals is nonzero.

## Closed Peano statement

```text
forall a b. ~(a = 0) -> ~(b = 0) -> ~(a * b = 0)
```

## Dependencies

- [[mul_eq_zero]]

## Checked dependents

- [[mul_left_cancel_nonzero]]
- [[beta_accumulated_product_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **65 nodes**, depth **18**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib mul_ne_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
