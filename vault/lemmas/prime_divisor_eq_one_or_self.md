---
title: "Lemma: prime_divisor_eq_one_or_self"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_divisor_eq_one_or_self`

Every divisor of a prime is one or the prime itself.

## Closed Peano statement

```text
forall p g. (~(p = 1) /\ forall c d. p = c * d -> c = 1 \/ d = 1) -> (exists x. p = g * x) -> g = 1 \/ p = g
```

## Dependencies

- [[mul_one]]

## Checked dependents

- [[euclid_prime_dvd_product]]

## Verification record

- Independently checked from the empty context.
- Certificate: **57 nodes**, depth **12**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib prime_divisor_eq_one_or_self`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
