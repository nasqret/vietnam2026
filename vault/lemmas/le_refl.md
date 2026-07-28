---
title: "Lemma: le_refl"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_refl`

The defined order is reflexive; zero is its witness.

## Closed Peano statement

```text
forall n. n <= n
```

## Dependencies

- [[zero_add]]

## Checked dependents

- [[gcd_exists_relational]]
- [[gcd_balanced_bezout_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **25 nodes**, depth **9**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib le_refl`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
