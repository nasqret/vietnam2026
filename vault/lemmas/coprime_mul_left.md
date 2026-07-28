---
title: "Lemma: coprime_mul_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_mul_left`

Coprimality with a fixed right operand is closed under multiplication on the left.

## Closed Peano statement

```text
forall a b n. (forall d. (exists x. a = d * x) -> (exists y. n = d * y) -> d = 1) -> (forall d. (exists x. b = d * x) -> (exists y. n = d * y) -> d = 1) -> forall d. (exists x. a * b = d * x) -> (exists y. n = d * y) -> d = 1
```

## Dependencies

- [[multiple_trans]]
- [[gauss_coprime_cancel]]

## Checked dependents

- [[coprime_mul_right]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3975 nodes**, depth **53**.
- Authored script length: **34 commands**.
- Runtime card: `pa lib coprime_mul_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
