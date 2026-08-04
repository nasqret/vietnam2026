---
title: "Lemma: is_gcd_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_unique`

The fully expanded relational greatest common divisor is unique.

## Closed Peano statement

```text
forall g h a b. (((exists x. a = g * x) /\ (exists y. b = g * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. g = c * w) -> (((exists x. a = h * x) /\ (exists y. b = h * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. h = c * w) -> g = h
```

## Dependencies

- [[multiple_antisymm]]

## Checked dependents

- [[gcd_lcm_product]]

## Verification record

- Independently checked from the empty context.
- Certificate: **680 nodes**, depth **34**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib is_gcd_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
