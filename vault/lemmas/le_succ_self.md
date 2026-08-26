---
title: "Lemma: le_succ_self"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_succ_self`

Every natural number is below its successor.

## Closed Peano statement

```text
forall n. n <= S n
```

## Dependencies

- [[zero_add]]
- [[add_succ_left]]

## Checked dependents

- [[beta_accumulated_product_step]]
- [[bounded_beta_crt_prefix_invariant]]
- [[beta_exclusive_accumulated_product_step]]
- [[bounded_beta_exclusive_recode_invariant]]

## Verification record

- Independently checked from the empty context.
- Certificate: **58 nodes**, depth **12**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib le_succ_self`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
