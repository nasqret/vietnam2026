---
title: "Lemma: lt_five_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_five_cases`

Every natural strictly below five is one of its canonical values.

## Closed Peano statement

```text
forall x. (exists h. h + S x = 5) -> x = 0 \/ x = 1 \/ x = 2 \/ x = 3 \/ x = 4
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[lt_three_cases]]

## Checked dependents

- [[lt_seven_cases]]
- [[bounded_square_mod5_classify]]

## Verification record

- Independently checked from the empty context.
- Certificate: **331 nodes**, depth **24**.
- Authored script length: **33 commands**.
- Runtime card: `pa lib lt_five_cases`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
