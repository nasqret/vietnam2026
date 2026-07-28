---
title: "Lemma: mod5_fourth_power_residue_four"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_fourth_power_residue_four`

A number congruent to four modulo five has fourth power congruent to one.

## Closed Peano statement

```text
forall q. exists w. (5 * q + 4) * (5 * q + 4) * (5 * q + 4) * (5 * q + 4) = 5 * w + 1
```

## Dependencies

- [[mod5_square_residue_four]]
- [[mod5_square_residue_one]]
- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4221 nodes**, depth **59**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib mod5_fourth_power_residue_four`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
