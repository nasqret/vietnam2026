---
title: "Lemma: beta_moduli_coprime_of_gap_dvd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_moduli_coprime_of_gap_dvd`

Beta moduli at an additive index gap dividing c are coprime.

## Closed Peano statement

```text
forall c i j gap. j = i + gap -> (exists k. c = gap * k) -> forall d. (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1
```

## Dependencies

- [[beta_modulus_coprime_base]]
- [[common_divisor_beta_moduli_divides_gap_times_c]]
- [[multiple_trans]]
- [[multiple_refl]]
- [[gauss_coprime_cancel]]
- [[mul_comm]]

## Checked dependents

- [[binary_crt_beta_pair_of_gap_dvd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **6007 nodes**, depth **56**.
- Authored script length: **59 commands**.
- Runtime card: `pa lib beta_moduli_coprime_of_gap_dvd`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
