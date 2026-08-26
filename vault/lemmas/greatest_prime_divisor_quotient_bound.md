---
title: "Lemma: greatest_prime_divisor_quotient_bound"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `greatest_prime_divisor_quotient_bound`

Every prime divisor of the quotient by a greatest prime divisor is bounded by that divisor.

## Closed Peano statement

```text
forall n p q. n = p * q -> (((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ (exists k. n = p * k)) /\ forall r. ((~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) /\ (exists k. n = r * k)) -> (exists h. h + r = p)) -> forall r. (~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) -> (exists k. q = r * k) -> (exists h. h + r = p)
```

## Dependencies

- [[mul_comm]]
- [[multiple_trans]]

## Checked dependents

- [[greatest_prime_divisor_descent]]

## Verification record

- Independently checked from the empty context.
- Certificate: **388 nodes**, depth **25**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib greatest_prime_divisor_quotient_bound`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
