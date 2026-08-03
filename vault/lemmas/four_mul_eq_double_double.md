---
title: "Lemma: four_mul_eq_double_double"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `four_mul_eq_double_double`

Multiplication by four is iterated doubling.

## Closed Peano statement

```text
forall a. 4 * a = 2 * (2 * a)
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- [[odd_mod4_cases]]
- [[mod4_one_is_odd]]
- [[mod4_three_is_odd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **178 nodes**, depth **19**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib four_mul_eq_double_double`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
