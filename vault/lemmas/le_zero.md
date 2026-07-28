---
title: "Lemma: le_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_zero`

Only zero is less than or equal to zero.

## Closed Peano statement

```text
forall n. n <= 0 -> n = 0
```

## Dependencies

- [[add_eq_zero_right]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **22 nodes**, depth **15**.
- Authored script length: **5 commands**.
- Runtime card: `pa lib le_zero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
