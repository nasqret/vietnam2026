---
title: "Lemma: square_decomp"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `square_decomp`

Expand a square while retaining an explicit quotient and remainder.

## Closed Peano statement

```text
forall a z q r. z = a * q + r -> z * z = a * (q * z + r * q) + r * r
```

## Dependencies

- [[add_assoc]]
- [[mul_comm]]
- [[mul_add]]
- [[add_mul]]
- [[mul_assoc]]

## Checked dependents

- [[square_residue_lift]]

## Verification record

- Independently checked from the empty context.
- Certificate: **847 nodes**, depth **29**.
- Authored script length: **45 commands**.
- Runtime card: `pa lib square_decomp`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
