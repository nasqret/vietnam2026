---
title: "Lemma: mod4_one_three_exclusive_pointwise"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod4_one_three_exclusive_pointwise`

Residues one and three modulo four cannot describe the same natural.

## Closed Peano statement

```text
forall n a b. n = 4 * a + 1 -> n = 4 * b + 3 -> false
```

## Dependencies

- [[division_remainder_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **944 nodes**, depth **58**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib mod4_one_three_exclusive_pointwise`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
