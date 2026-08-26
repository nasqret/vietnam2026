---
title: "Lemma: add_residue_lift"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_residue_lift`

Combine two quotient-and-residue summands and normalize the residue.

## Closed Peano statement

```text
forall a x u r q t c s. x = a * q + t -> r + t = a * c + s -> (a * u + r) + x = a * ((u + q) + c) + s
```

## Dependencies

- [[add_comm]]
- [[add_assoc]]
- [[mul_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **259 nodes**, depth **28**.
- Authored script length: **50 commands**.
- Runtime card: `pa lib add_residue_lift`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
