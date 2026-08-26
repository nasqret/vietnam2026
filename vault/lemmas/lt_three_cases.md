---
title: "Lemma: lt_three_cases"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_three_cases`

Every natural strictly below three is zero, one, or two.

## Closed Peano statement

```text
forall x. (exists h. h + S x = 3) -> x = 0 \/ x = 1 \/ x = 2
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[le_zero]]

## Checked dependents

- [[lt_five_cases]]
- [[bounded_square_mod3_classify]]

## Verification record

- Independently checked from the empty context.
- Certificate: **182 nodes**, depth **21**.
- Authored script length: **38 commands**.
- Runtime card: `pa lib lt_three_cases`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
