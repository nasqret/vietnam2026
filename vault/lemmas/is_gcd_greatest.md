---
title: "Lemma: is_gcd_greatest"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_greatest`

Every common divisor of the inputs divides their relational gcd.

## Closed Peano statement

```text
forall g a b c. (((exists x. a = g * x) /\ (exists y. b = g * y)) /\ forall d. (exists u. a = d * u) -> (exists v. b = d * v) -> exists w. g = d * w) -> (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. g = c * w
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[is_gcd_quotients_coprime_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **24 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib is_gcd_greatest`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
