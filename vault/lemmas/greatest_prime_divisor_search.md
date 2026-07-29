---
title: "Lemma: greatest_prime_divisor_search"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `greatest_prime_divisor_search`

Bounded search either excludes all prime divisors or returns a greatest one in the bound.

## Closed Peano statement

```text
forall B n. ((forall r. (exists h. h + r = B) -> ~(((~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) /\ (exists k. n = r * k)))) \/ exists p. (((exists h. h + p = B) /\ ((~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1) /\ (exists k. n = p * k))) /\ forall r. (exists h. h + r = B) -> ((~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) /\ (exists k. n = r * k)) -> (exists h. h + r = p)))
```

## Dependencies

- [[prime_nonzero]]
- [[le_zero]]
- [[prime_divides_decidable]]
- [[le_refl]]
- [[le_eq_or_lt]]
- [[le_of_succ_le_succ]]
- [[le_succ]]

## Checked dependents

- [[greatest_prime_divisor_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3949 nodes**, depth **77**.
- Authored script length: **92 commands**.
- Runtime card: `pa lib greatest_prime_divisor_search`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
