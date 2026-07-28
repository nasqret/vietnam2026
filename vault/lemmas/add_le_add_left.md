---
title: "Lemma: add_le_add_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_le_add_left`

Adding the same left summand preserves the witness-defined order.

## Closed Peano statement

```text
forall a b c. (exists k. k + a = b) -> exists r. r + (c + a) = c + b
```

## Dependencies

- [[add_assoc]]
- [[add_comm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **147 nodes**, depth **26**.
- Authored script length: **18 commands**.
- Runtime card: `pa lib add_le_add_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
