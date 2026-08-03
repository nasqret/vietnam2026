---
title: "Lemma: mul_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mul_one`

One is a right identity for multiplication.

## Closed Peano statement

```text
forall n. n * 1 = n
```

## Dependencies

- [[zero_add]]

## Checked dependents

- [[multiple_refl]]
- [[multiple_antisymm]]
- [[coprime_to_is_gcd_one]]
- [[proper_factor_lt]]
- [[prime_divisor_eq_one_or_self]]
- [[binary_crt]]
- [[prime_unbounded]]
- [[mod_eq_cancel_coprime]]
- [[pow_add]]
- [[predecessor_square_mod_one]]
- [[bounded_mod_inverse_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **33 nodes**, depth **9**.
- Authored script length: **2 commands**.
- Runtime card: `pa lib mul_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
