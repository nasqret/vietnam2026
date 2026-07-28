---
title: "Lemma: beta_moduli_pairwise_coprime_bounded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_moduli_pairwise_coprime_bounded`

Distinct indices in a bounded prefix have pairwise coprime beta moduli under a bounded common-multiple invariant.

## Closed Peano statement

```text
forall B c. (forall t. (exists h. S t + S h = S B) -> exists k. c = S t * k) -> forall i j. ~(i = j) -> (exists hi. hi + i = B) -> (exists hj. hj + j = B) -> forall d. (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1
```

## Dependencies

- [[lt_trichotomy]]
- [[beta_moduli_coprime_of_lt_bounded_common_multiple]]

## Checked dependents

- [[bounded_beta_moduli_pairwise_coprime_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **6348 nodes**, depth **59**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib beta_moduli_pairwise_coprime_bounded`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
