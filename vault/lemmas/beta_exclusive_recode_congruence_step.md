---
title: "Lemma: beta_exclusive_recode_congruence_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_exclusive_recode_congruence_step`

Add the next source value to a target-base CRT code for an exclusive prefix.

## Closed Peano statement

```text
forall N c b e k P z. (exists h. h + S k = N) -> ~(P = 0) -> (forall i. (exists h. h + S i = k) -> exists q. P = S ((S i) * c) * q) -> (forall i a. (exists h. h + S i = k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v) -> (forall j. (exists g. g + k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> exists z2. forall i a. (exists h. h + S i = S k) -> ((exists h. h + S a = S ((S i) * e)) /\ exists q. b = q * S ((S i) * e) + a) -> exists u v. z2 + S ((S i) * c) * u = a + S ((S i) * c) * v
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[le_refl]]
- [[lt_to_le]]
- [[binary_crt_fold_step]]
- [[beta_at_exists]]
- [[beta_at_unique]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]

## Checked dependents

- [[beta_exclusive_recode_invariant_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **7398 nodes**, depth **65**.
- Authored script length: **92 commands**.
- Runtime card: `pa lib beta_exclusive_recode_congruence_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
