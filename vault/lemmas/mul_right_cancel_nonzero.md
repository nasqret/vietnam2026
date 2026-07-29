---
title: "Lemma: mul_right_cancel_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_right_cancel_nonzero`

A nonzero common right factor can be cancelled.

## Closed Peano statement

```text
forall a b c. ~(c = 0) -> a * c = b * c -> a = b
```

## Dependencies

- [[mul_comm]]
- [[mul_left_cancel_nonzero]]

## Checked dependents

- [[beta_canonical_product_cancel_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **478 nodes**, depth **25**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib mul_right_cancel_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
