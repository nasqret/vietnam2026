---
title: "Lemma: coprime_to_is_gcd_one"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `coprime_to_is_gcd_one`

Expanded coprimality constructs the relational gcd witness one.

## Closed Peano statement

```text
forall a b. (forall d. (exists x. a = d * x) -> (exists y. b = d * y) -> d = 1) -> (((exists x. a = 1 * x) /\ (exists y. b = 1 * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. 1 = c * w)
```

## Dependencies

- [[one_multiple]]
- [[one_mul]]
- [[mul_one]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **106 nodes**, depth **23**.
- Authored script length: **22 commands**.
- Runtime card: `pa lib coprime_to_is_gcd_one`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
