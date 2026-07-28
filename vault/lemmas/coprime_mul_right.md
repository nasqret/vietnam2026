---
title: "Lemma: coprime_mul_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_mul_right`

Coprimality with a fixed left operand is closed under multiplication on the right.

## Closed Peano statement

```text
forall n a b. (forall d. (exists x. n = d * x) -> (exists y. a = d * y) -> d = 1) -> (forall d. (exists x. n = d * x) -> (exists y. b = d * y) -> d = 1) -> forall d. (exists x. n = d * x) -> (exists y. a * b = d * y) -> d = 1
```

## Dependencies

- [[coprime_mul_left]]
- [[coprime_symm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4017 nodes**, depth **54**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib coprime_mul_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
