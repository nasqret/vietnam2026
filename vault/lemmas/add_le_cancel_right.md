---
title: "Lemma: add_le_cancel_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_le_cancel_right`

A common right summand can be cancelled from an order comparison.

## Closed Peano statement

```text
forall a b c. (exists k. k + (a + c) = b + c) -> exists r. r + a = b
```

## Dependencies

- [[add_assoc]]
- [[add_right_cancel]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **103 nodes**, depth **20**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib add_le_cancel_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
