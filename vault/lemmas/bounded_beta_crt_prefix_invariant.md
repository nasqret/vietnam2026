---
title: "Lemma: bounded_beta_crt_prefix_invariant"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_beta_crt_prefix_invariant`

Concrete ordinary-induction fold of the beta CRT invariant through every bounded prefix.

## Closed Peano statement

```text
forall N c b. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> forall k. (exists h. h + k = N) -> exists P z. (~(P = 0) /\ ((forall i. (exists h. h + i = k) -> exists q. P = S ((S i) * c) * q) /\ ((forall i a. (exists h. h + i = k) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v) /\ forall j. (exists g. g + S k = j) -> (exists h. h + j = N) -> forall d. (exists u. P = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1)))
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[le_zero]]
- [[multiple_refl]]
- [[beta_at_to_mod_eq]]
- [[beta_moduli_coprime_of_lt_bounded_common_multiple]]
- [[le_succ_self]]
- [[le_trans]]
- [[beta_crt_prefix_invariant_step]]

## Checked dependents

- [[bounded_beta_crt_for_existing_code]]

## Verification record

- Independently checked from the empty context.
- Certificate: **25496 nodes**, depth **78**.
- Authored script length: **81 commands**.
- Runtime card: `pa lib bounded_beta_crt_prefix_invariant`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
