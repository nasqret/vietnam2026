---
title: "Lemma: divisor_le_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `divisor_le_nonzero`

A divisor of a nonzero natural is bounded by that natural.

## Closed Peano statement

```text
forall d n. ~(n = 0) -> (exists q. n = d * q) -> exists k. k + d = n
```

## Dependencies

- [[one_le_of_ne_zero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **62 nodes**, depth **18**.
- Authored script length: **31 commands**.
- Runtime card: `pa lib divisor_le_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
