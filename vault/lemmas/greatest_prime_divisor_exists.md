---
title: "Lemma: greatest_prime_divisor_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `greatest_prime_divisor_exists`

Every nonzero nonunit has a greatest prime divisor in the ordinary natural order.

## Closed Peano statement

```text
forall n. ~(n = 0) -> ~(n = 1) -> exists p. (((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ (exists k. n = p * k)) /\ forall r. ((~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) /\ (exists k. n = r * k)) -> (exists h. h + r = p))
```

## Dependencies

- [[prime_divisor_exists]]
- [[divisor_le_nonzero]]
- [[greatest_prime_divisor_search]]

## Checked dependents

- [[greatest_prime_divisor_descent]]

## Verification record

- Independently checked from the empty context.
- Certificate: **7052 nodes**, depth **81**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib greatest_prime_divisor_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
