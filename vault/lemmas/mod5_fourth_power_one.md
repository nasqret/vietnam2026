---
title: "Lemma: mod5_fourth_power_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod5_fourth_power_one`

A fourth power of a nonmultiple of five is one modulo five.

## Closed Peano statement

```text
forall n. ~(exists x. n = 5 * x) -> exists x. n * n * n * n = 5 * x + 1
```

## Dependencies

- [[mod5_residue_complete]]
- [[square_residue_lift]]
- [[mul_assoc]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2675 nodes**, depth **38**.
- Authored script length: **52 commands**.
- Runtime card: `pa lib mod5_fourth_power_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
