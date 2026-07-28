---
title: "Lemma: is_gcd_of_dvd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_of_dvd`

If the left input divides the right, the left input is their relational gcd.

## Closed Peano statement

```text
forall a b. (exists y. b = a * y) -> (((exists x. a = a * x) /\ (exists y. b = a * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. a = c * w)
```

## Dependencies

- [[multiple_refl]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **55 nodes**, depth **11**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib is_gcd_of_dvd`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
