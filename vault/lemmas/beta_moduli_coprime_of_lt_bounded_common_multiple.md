---
title: "Lemma: beta_moduli_coprime_of_lt_bounded_common_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_moduli_coprime_of_lt_bounded_common_multiple`

Ordered bounded indices have coprime beta moduli when c is a common multiple of the bounded positive gaps.

## Closed Peano statement

```text
forall B c i j. (forall t. (exists h. S t + S h = S B) -> exists k. c = S t * k) -> (exists g. g + S i = j) -> (exists h. h + j = B) -> forall d. (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1
```

## Dependencies

- [[beta_moduli_coprime_of_gap_dvd]]
- [[add_comm]]
- [[le_trans]]

## Checked dependents

- [[beta_moduli_pairwise_coprime_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **6227 nodes**, depth **57**.
- Authored script length: **49 commands**.
- Runtime card: `pa lib beta_moduli_coprime_of_lt_bounded_common_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
