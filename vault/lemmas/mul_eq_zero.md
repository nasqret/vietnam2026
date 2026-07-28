---
title: "Lemma: mul_eq_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_eq_zero`

Zero products have a zero factor: the 23-entry core capstone.

## Closed Peano statement

```text
forall n m. n * m = 0 -> n = 0 \/ m = 0
```

## Dependencies

- [[add_eq_zero_right]]

## Checked dependents

- [[mul_ne_zero]]
- [[two_large_factors_impossible]]

## Verification record

- Independently checked from the empty context.
- Certificate: **31 nodes**, depth **18**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib mul_eq_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
