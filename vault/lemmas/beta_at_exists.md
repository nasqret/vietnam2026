---
title: "Lemma: beta_at_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_exists`

Every Gödel-beta position has a bounded decoded residue.

## Closed Peano statement

```text
forall b c i. exists x. ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x)
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[mul_comm]]
- [[division_remainder_exists]]

## Checked dependents

- [[beta_at_exists_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **479 nodes**, depth **31**.
- Authored script length: **24 commands**.
- Runtime card: `pa lib beta_at_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
