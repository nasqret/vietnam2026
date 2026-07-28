---
title: "Lemma: multiple_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_trans`

The multiple relation is transitive.

## Closed Peano statement

```text
forall a b n. (exists q. n = a * q) -> (exists r. a = b * r) -> exists s. n = b * s
```

## Dependencies

- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **119 nodes**, depth **40**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib multiple_trans`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
