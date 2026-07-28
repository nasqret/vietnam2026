---
title: "Lemma: mod5_square_residue_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_square_residue_one`

Squaring residue one modulo five preserves residue one.

## Closed Peano statement

```text
forall z q. z = 5 * q + 1 -> z * z = 5 * (q * z + q) + 1
```

## Dependencies

- [[add_assoc]]
- [[mul_add]]
- [[mul_assoc]]
- [[mul_succ_left]]

## Checked dependents

- [[mod5_fourth_power_residue_one]]
- [[mod5_fourth_power_residue_four]]

## Verification record

- Independently checked from the empty context.
- Certificate: **416 nodes**, depth **38**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib mod5_square_residue_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
