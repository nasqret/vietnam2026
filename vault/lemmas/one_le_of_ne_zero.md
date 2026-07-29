---
title: "Lemma: one_le_of_ne_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `one_le_of_ne_zero`

Every nonzero natural is at least one.

## Closed Peano statement

```text
forall n. ~(n = 0) -> 1 <= n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[divisor_le_nonzero]]
- [[le_scaled_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **20 nodes**, depth **10**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib one_le_of_ne_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
