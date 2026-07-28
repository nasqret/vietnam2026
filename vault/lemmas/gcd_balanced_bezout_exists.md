---
title: "Lemma: gcd_balanced_bezout_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_balanced_bezout_exists`

Every pair has a relational gcd together with balanced natural Bezout witnesses.

## Closed Peano statement

```text
forall a b. exists d. ((((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w) /\ exists xp yp xn yn. a * xp + b * yp = d + (a * xn + b * yn))
```

## Dependencies

- [[le_refl]]
- [[gcd_balanced_bezout_exists_up_to]]

## Checked dependents

- [[coprime_balanced_bezout]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2269 nodes**, depth **47**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib gcd_balanced_bezout_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
