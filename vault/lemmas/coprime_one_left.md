---
title: "Lemma: coprime_one_left"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_one_left`

One is coprime to every natural in the expanded common-divisor relation.

## Closed Peano statement

```text
forall a d. (exists x. 1 = d * x) -> (exists y. a = d * y) -> d = 1
```

## Dependencies

- [[divisor_one]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **201 nodes**, depth **36**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib coprime_one_left`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
