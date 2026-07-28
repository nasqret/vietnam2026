---
title: "Lemma: gauss_coprime_cancel"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gauss_coprime_cancel`

Cancel a coprime factor from a divisibility witness (Gauss cancellation).

## Closed Peano statement

```text
forall a b z. (forall d. (exists x. a = d * x) -> (exists y. b = d * y) -> d = 1) -> (exists q. b * z = a * q) -> exists w. z = a * w
```

## Dependencies

- [[multiple_refl]]
- [[one_mul]]
- [[coprime_balanced_bezout]]
- [[balanced_combination_scale_right]]
- [[common_divisor_divides_balanced_result]]

## Checked dependents

- [[euclid_prime_dvd_product]]
- [[beta_moduli_coprime_of_gap_dvd]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3800 nodes**, depth **51**.
- Authored script length: **30 commands**.
- Runtime card: `pa lib gauss_coprime_cancel`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
