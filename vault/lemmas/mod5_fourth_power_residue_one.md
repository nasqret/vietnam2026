---
title: "Lemma: mod5_fourth_power_residue_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_fourth_power_residue_one`

A number congruent to one modulo five has fourth power congruent to one.

## Closed Peano statement

```text
forall q. exists w. (5 * q + 1) * (5 * q + 1) * (5 * q + 1) * (5 * q + 1) = 5 * w + 1
```

## Dependencies

- [[mod5_square_residue_one]]
- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **584 nodes**, depth **27**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib mod5_fourth_power_residue_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
