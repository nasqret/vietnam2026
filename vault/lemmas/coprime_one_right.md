---
title: "Lemma: coprime_one_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_one_right`

Every natural is coprime to one in the expanded common-divisor relation.

## Closed Peano statement

```text
forall a d. (exists x. a = d * x) -> (exists y. 1 = d * y) -> d = 1
```

## Dependencies

- [[divisor_one]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **200 nodes**, depth **29**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib coprime_one_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
