---
title: "Lemma: distinct_primes_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `distinct_primes_coprime`

Distinct primes are coprime in the expanded common-divisor relation.

## Closed Peano statement

```text
forall p q. (~(p = 1) /\ forall c e. p = c * e -> c = 1 \/ e = 1) -> (~(q = 1) /\ forall c e. q = c * e -> c = 1 \/ e = 1) -> ~(p = q) -> forall d. (exists x. p = d * x) -> (exists y. q = d * y) -> d = 1
```

## Dependencies

- [[prime_divisor_eq_one_or_self]]
- [[prime_not_divides_coprime]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1675 nodes**, depth **50**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib distinct_primes_coprime`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
