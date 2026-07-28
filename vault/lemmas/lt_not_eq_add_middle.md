---
title: "Lemma: lt_not_eq_add_middle"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_not_eq_add_middle`

A strict upper bound prevents the lower term from containing that bound as an additive middle block.

## Closed Peano statement

```text
forall r m a b. (exists k. k + S r = m) -> ~(r = (a + m) + b)
```

## Dependencies

- [[add_succ_left]]

## Checked dependents

- [[positive_quotient_gap_impossible]]

## Verification record

- Independently checked from the empty context.
- Certificate: **95 nodes**, depth **28**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib lt_not_eq_add_middle`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
