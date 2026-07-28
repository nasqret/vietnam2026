---
title: "Lemma: gcd_exists_relational"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_exists_relational`

Every pair of naturals has a relational greatest common divisor.

## Closed Peano statement

```text
forall a b. exists d. (((exists x. a = d * x) /\ (exists y. b = d * y)) /\ forall c. (exists u. a = c * u) -> (exists v. b = c * v) -> exists w. d = c * w)
```

## Dependencies

- [[le_refl]]
- [[gcd_exists_up_to]]

## Checked dependents

- [[euclid_prime_dvd_product]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1268 nodes**, depth **46**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib gcd_exists_relational`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
