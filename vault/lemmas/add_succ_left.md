---
title: "Lemma: add_succ_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_succ_left`

A successor can move through addition on the left.

## Closed Peano statement

```text
forall n m. S n + m = S (n + m)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[add_comm]]
- [[drop_add_prefix_from_fixed]]
- [[le_succ_self]]
- [[le_succ]]
- [[lt_to_le]]
- [[lt_irrefl_expanded]]
- [[le_eq_or_lt]]
- [[lt_trans]]
- [[lt_not_eq_add_middle]]
- [[division_remainder_succ]]

## Verification record

- Independently checked from the empty context.
- Certificate: **27 nodes**, depth **10**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib add_succ_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
