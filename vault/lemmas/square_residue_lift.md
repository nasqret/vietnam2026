---
title: "Lemma: square_residue_lift"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `square_residue_lift`

Lift one quotient-and-remainder equation through squaring.

## Closed Peano statement

```text
forall a z q r c s. z = a * q + r -> r * r = a * c + s -> z * z = a * ((q * z + r * q) + c) + s
```

## Dependencies

- [[square_decomp]]
- [[add_residue]]

## Checked dependents

- [[square_residue_witness]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1600 nodes**, depth **58**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib square_residue_lift`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
