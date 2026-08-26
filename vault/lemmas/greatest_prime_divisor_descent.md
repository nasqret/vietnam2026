---
title: "Lemma: greatest_prime_divisor_descent"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `greatest_prime_divisor_descent`

Choose a greatest prime factor with a nonzero strict quotient and the exact append-order bound.

## Closed Peano statement

```text
forall n. ~(n = 0) -> ~(n = 1) -> exists p q. (((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ n = p * q) /\ (~(q = 0) /\ ((exists h. h + S q = n) /\ forall r. (~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) -> (exists k. q = r * k) -> (exists h. h + r = p))))
```

## Dependencies

- [[greatest_prime_divisor_exists]]
- [[mul_comm]]
- [[factor_nonzero_left]]
- [[proper_factor_lt]]
- [[greatest_prime_divisor_quotient_bound]]

## Checked dependents

- [[prime_factorization_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **8256 nodes**, depth **82**.
- Authored script length: **61 commands**.
- Runtime card: `pa lib greatest_prime_divisor_descent`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
