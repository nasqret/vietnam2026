---
title: "Lemma: mod5_fourth_power_residue_three"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_fourth_power_residue_three`

A number congruent to three modulo five has fourth power congruent to one.

## Closed Peano statement

```text
forall q. exists w. (5 * q + 3) * (5 * q + 3) * (5 * q + 3) * (5 * q + 3) = 5 * w + 1
```

## Dependencies

- [[mod5_square_residue_three]]
- [[mod5_square_residue_four]]
- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **5464 nodes**, depth **60**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib mod5_fourth_power_residue_three`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
