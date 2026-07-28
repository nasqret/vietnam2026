---
title: "Lemma: is_gcd_euclid_backward"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_euclid_backward`

A relational gcd of dividend and divisor is a gcd of divisor and remainder.

## Closed Peano statement

```text
forall d a b q r. a = b * q + r -> (((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w) -> (((exists x. b = d * x) /\ (exists y. r = d * y)) /\ forall c. (exists u. b = c * u) -> (exists v. r = c * v) -> exists w. d = c * w)
```

## Dependencies

- [[divides_remainder]]
- [[divides_linear_step]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **741 nodes**, depth **37**.
- Authored script length: **35 commands**.
- Runtime card: `pa lib is_gcd_euclid_backward`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
