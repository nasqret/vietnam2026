---
title: "Lemma: square_residue_witness"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `square_residue_witness`

Existential wrapper for the generic square-residue lift.

## Closed Peano statement

```text
forall a z q r c s. z = a * q + r -> r * r = a * c + s -> exists w. z * z = a * w + s
```

## Dependencies

- [[square_residue_lift]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1601 nodes**, depth **59**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib square_residue_witness`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
