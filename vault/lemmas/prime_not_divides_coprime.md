---
title: "Lemma: prime_not_divides_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_not_divides_coprime`

A prime not dividing a natural is coprime to that natural.

## Closed Peano statement

```text
forall p a. (~(p = 1) /\ forall c e. p = c * e -> c = 1 \/ e = 1) -> ~(exists k. a = p * k) -> forall d. (exists x. p = d * x) -> (exists y. a = d * y) -> d = 1
```

## Dependencies

- [[prime_coprime_or_divides]]

## Checked dependents

- [[distinct_primes_coprime]]
- [[prime_mod_inverse]]
- [[prime_mod_cancel]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1588 nodes**, depth **48**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib prime_not_divides_coprime`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
