---
title: "Lemma: mod5_square_residue_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_square_residue_two`

Squaring residue two modulo five gives residue four.

## Closed Peano statement

```text
forall z q. z = 5 * q + 2 -> z * z = 5 * ((q * z + q) + q) + 4
```

## Dependencies

- [[add_comm]]
- [[add_assoc]]
- [[mul_add]]
- [[mul_assoc]]
- [[mul_succ_left]]

## Checked dependents

- [[mod5_fourth_power_residue_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1002 nodes**, depth **54**.
- Authored script length: **30 commands**.
- Runtime card: `pa lib mod5_square_residue_two`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
