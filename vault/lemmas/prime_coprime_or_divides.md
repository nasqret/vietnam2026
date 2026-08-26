---
title: "Lemma: prime_coprime_or_divides"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_coprime_or_divides`

A prime is constructively either coprime to a natural or divides it.

## Closed Peano statement

```text
forall p a. (~(p = 1) /\ forall c e. p = c * e -> c = 1 \/ e = 1) -> (forall d. (exists x. p = d * x) -> (exists y. a = d * y) -> d = 1) \/ exists k. a = p * k
```

## Dependencies

- [[gcd_exists_relational]]
- [[prime_divisor_eq_one_or_self]]
- [[is_gcd_one_to_coprime]]

## Checked dependents

- [[prime_not_divides_coprime]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1572 nodes**, depth **47**.
- Authored script length: **30 commands**.
- Runtime card: `pa lib prime_coprime_or_divides`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
