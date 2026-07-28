---
title: "Lemma: lt_of_le_of_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_of_le_of_lt`

Weak order followed by strict order remains strict.

## Closed Peano statement

```text
forall a b c. (exists k. k + a = b) -> (exists k. k + S b = c) -> exists k. k + S a = c
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **58 nodes**, depth **15**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib lt_of_le_of_lt`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
