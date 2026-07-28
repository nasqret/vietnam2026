---
title: "Lemma: add_residue"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_residue`

Absorb a second quotient into an existing residue equation.

## Closed Peano statement

```text
forall a u c r s. r = a * c + s -> a * u + r = a * (u + c) + s
```

## Dependencies

- [[add_assoc]]
- [[mul_add]]

## Checked dependents

- [[square_residue_lift]]

## Verification record

- Independently checked from the empty context.
- Certificate: **117 nodes**, depth **31**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib add_residue`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
