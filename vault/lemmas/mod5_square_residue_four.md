---
title: "Lemma: mod5_square_residue_four"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_square_residue_four`

Squaring residue four modulo five gives residue one.

## Closed Peano statement

```text
forall z q. z = 5 * q + 4 -> z * z = 5 * ((q * z + 4 * q) + 3) + 1
```

## Dependencies

- [[square_residue_lift]]

## Checked dependents

- [[mod5_fourth_power_residue_two]]
- [[mod5_fourth_power_residue_three]]
- [[mod5_fourth_power_residue_four]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1855 nodes**, depth **53**.
- Authored script length: **6 commands**.
- Runtime card: `pa lib mod5_square_residue_four`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
