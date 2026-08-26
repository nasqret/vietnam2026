---
title: "Lemma: beta_modulus_coprime_base"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_modulus_coprime_base`

Every beta-shaped successor modulus is coprime to its base c.

## Closed Peano statement

```text
forall c k d. (exists u. S (k * c) = d * u) -> (exists v. c = d * v) -> d = 1
```

## Dependencies

- [[divides_remainder]]
- [[divisor_one]]
- [[mul_comm]]

## Checked dependents

- [[beta_moduli_coprime_of_gap_dvd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **874 nodes**, depth **30**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib beta_modulus_coprime_base`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
