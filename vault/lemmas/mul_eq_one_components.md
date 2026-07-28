---
title: "Lemma: mul_eq_one_components"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_eq_one_components`

A product is one only when both natural factors are one.

## Closed Peano statement

```text
forall a b. a * b = 1 -> a = 1 /\ b = 1
```

## Dependencies

- [[mul_zero_left]]
- [[add_eq_zero_right]]
- [[one_mul]]

## Checked dependents

- [[divisor_one]]
- [[multiple_antisymm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **191 nodes**, depth **29**.
- Authored script length: **39 commands**.
- Runtime card: `pa lib mul_eq_one_components`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
