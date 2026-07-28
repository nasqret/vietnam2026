---
title: "Lemma: add_le_add_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_le_add_right`

Adding the same right summand preserves the witness-defined order.

## Closed Peano statement

```text
forall a b c. (exists k. k + a = b) -> exists r. r + (a + c) = b + c
```

## Dependencies

- [[add_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **44 nodes**, depth **19**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib add_le_add_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
