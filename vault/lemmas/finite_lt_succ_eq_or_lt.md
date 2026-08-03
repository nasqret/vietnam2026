---
title: "Lemma: finite_lt_succ_eq_or_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_lt_succ_eq_or_lt`

A value below a successor is the predecessor or lies below it.

## Closed Peano statement

```text
forall n x. (exists h. h + S x = S n) -> x = n \/ exists h. h + S x = n
```

## Dependencies

- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- [[beta_prefix_replace_exists]]
- [[finite_contains_decidable]]
- [[finite_bounded_prefix_without_top]]
- [[finite_surjective_succ_intro]]
- [[finite_last_is_top_from_prefix_surjective]]
- [[beta_product_replace_balance]]

## Verification record

- Independently checked from the empty context.
- Certificate: **128 nodes**, depth **21**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib finite_lt_succ_eq_or_lt`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
