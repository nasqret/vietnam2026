---
title: "Lemma: beta_crt_prefix_congruence_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_crt_prefix_congruence_step`

Extend balanced congruence to one more decoded beta position using the CRT fold step.

## Closed Peano statement

```text
forall N c b k P z. (exists h. h + S k = N) -> ~(P = 0) -> (forall i. (exists h. h + i = k) -> exists q. P = S ((S i) * c) * q) -> (forall i a. (exists h. h + i = k) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v) -> (forall j. (exists g. g + S k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> exists z2. forall i a. (exists h. h + i = S k) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> exists u v. z2 + S ((S i) * c) * u = a + S ((S i) * c) * v
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[le_refl]]
- [[binary_crt_fold_step]]
- [[beta_at_exists]]
- [[beta_at_unique]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]

## Checked dependents

- [[beta_crt_prefix_invariant_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **7352 nodes**, depth **64**.
- Authored script length: **88 commands**.
- Runtime card: `pa lib beta_crt_prefix_congruence_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
