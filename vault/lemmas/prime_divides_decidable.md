---
title: "Lemma: prime_divides_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_divides_decidable`

The concrete property of being a prime divisor is constructively decidable.

## Closed Peano statement

```text
forall p n. ((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ (exists k. n = p * k)) \/ ~(((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ (exists k. n = p * k)))
```

## Dependencies

- [[prime_decidable]]
- [[multiple_decidable]]

## Checked dependents

- [[greatest_prime_divisor_search]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3573 nodes**, depth **74**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib prime_divides_decidable`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
