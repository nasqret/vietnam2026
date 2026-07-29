---
title: "Lemma: mul_congr"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_congr`

Multiplication preserves equality in both arguments.

## Closed Peano statement

```text
forall a b c d. a = b -> c = d -> a * c = b * d
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_product_functional]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9 nodes**, depth **8**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib mul_congr`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
