---
title: "Lemma: remainder_decomposition_to_mod_eq"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `remainder_decomposition_to_mod_eq`

A directed quotient/remainder equation gives balanced congruence to its remainder.

## Closed Peano statement

```text
forall m b q x. b = q * m + x -> exists u v. b + m * u = x + m * v
```

## Dependencies

- [[add_comm]]
- [[mul_comm]]

## Checked dependents

- [[beta_at_to_mod_eq]]

## Verification record

- Independently checked from the empty context.
- Certificate: **323 nodes**, depth **26**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib remainder_decomposition_to_mod_eq`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
