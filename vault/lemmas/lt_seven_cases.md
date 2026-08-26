---
title: "Lemma: lt_seven_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_seven_cases`

Every natural strictly below seven is one of its canonical values.

## Closed Peano statement

```text
forall x. (exists h. h + S x = 7) -> x = 0 \/ x = 1 \/ x = 2 \/ x = 3 \/ x = 4 \/ x = 5 \/ x = 6
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[lt_five_cases]]

## Checked dependents

- [[bounded_square_mod7_classify]]

## Verification record

- Independently checked from the empty context.
- Certificate: **480 nodes**, depth **27**.
- Authored script length: **33 commands**.
- Runtime card: `pa lib lt_seven_cases`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
