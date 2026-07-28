---
title: "Lemma: is_gcd_euclid_forward"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `is_gcd_euclid_forward`

A relational gcd of divisor and remainder is a gcd of dividend and divisor.

## Closed Peano statement

```text
forall d a b q r. a = b * q + r -> (((exists x. b = d * x) /\ (exists y. r = d * y)) /\ forall c. (exists u. b = c * u) -> (exists v. r = c * v) -> exists w. d = c * w) -> (((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w)
```

## Dependencies

- [[divides_remainder]]
- [[divides_linear_step]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **586 nodes**, depth **51**.
- Authored script length: **35 commands**.
- Runtime card: `pa lib is_gcd_euclid_forward`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
