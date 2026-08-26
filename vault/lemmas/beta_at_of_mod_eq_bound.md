---
title: "Lemma: beta_at_of_mod_eq_bound"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_of_mod_eq_bound`

A bounded value congruent to a code is its expanded Gödel-beta value.

## Closed Peano statement

```text
forall b c i x. (exists h. h + S x = S ((S i) * c)) -> (exists u v. b + S ((S i) * c) * u = x + S ((S i) * c) * v) -> ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x)
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[mod_eq_to_remainder_decomposition]]

## Checked dependents

- [[binary_crt_beta_pair]]
- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1839 nodes**, depth **66**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib beta_at_of_mod_eq_bound`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
