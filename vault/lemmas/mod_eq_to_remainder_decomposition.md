---
title: "Lemma: mod_eq_to_remainder_decomposition"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_to_remainder_decomposition`

A bounded balanced residue has a directed quotient/remainder witness.

## Closed Peano statement

```text
forall m b x. ~(m = 0) -> (exists h. h + S x = m) -> (exists u v. b + m * u = x + m * v) -> exists q. b = q * m + x
```

## Dependencies

- [[division_remainder_exists]]
- [[add_comm]]
- [[mul_comm]]
- [[mod_eq_trans]]
- [[mod_eq_bounded_unique]]

## Checked dependents

- [[beta_at_of_mod_eq_bound]]
- [[binary_crt_remainders]]
- [[mod_eq_common_remainder_decomposition]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1793 nodes**, depth **64**.
- Authored script length: **51 commands**.
- Runtime card: `pa lib mod_eq_to_remainder_decomposition`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
