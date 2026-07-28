---
title: "Lemma: zero_or_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `zero_or_succ`

Every natural is either zero or the successor of a natural.

## Closed Peano statement

```text
forall n. n = 0 \/ exists k. n = S k
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[le_eq_or_lt]]
- [[division_remainder_succ]]
- [[division_remainder_exists]]
- [[division_remainder_unique]]
- [[multiple_has_zero_remainder]]
- [[multiple_antisymm]]
- [[bounded_common_multiple_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **8 nodes**, depth **6**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib zero_or_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
