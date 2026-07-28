---
title: "Lemma: is_gcd_one_to_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_one_to_coprime`

A relational gcd witness one implies expanded coprimality.

## Closed Peano statement

```text
forall a b. (((exists x. a = 1 * x) /\ (exists y. b = 1 * y)) /\ forall d. (exists u. a = d * u) -> (exists v. b = d * v) -> exists w. 1 = d * w) -> forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> c = 1
```

## Dependencies

- [[divisor_one]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **205 nodes**, depth **29**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib is_gcd_one_to_coprime`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
