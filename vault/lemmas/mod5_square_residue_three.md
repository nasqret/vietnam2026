---
title: "Lemma: mod5_square_residue_three"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_square_residue_three`

Squaring residue three modulo five gives residue four.

## Closed Peano statement

```text
forall z q. z = 5 * q + 3 -> z * z = 5 * ((q * z + 3 * q) + 1) + 4
```

## Dependencies

- [[square_residue_lift]]

## Checked dependents

- [[mod5_fourth_power_residue_three]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1757 nodes**, depth **53**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib mod5_square_residue_three`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
