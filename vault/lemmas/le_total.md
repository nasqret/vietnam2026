---
title: "Lemma: le_total"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_total`

Every pair of natural numbers is comparable in the defined order.

## Closed Peano statement

```text
forall n m. n <= m \/ m <= n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[division_remainder_unique]]
- [[mod_eq_lcm_merge]]

## Verification record

- Independently checked from the empty context.
- Certificate: **49 nodes**, depth **17**.
- Authored script length: **23 commands**.
- Runtime card: `pa lib le_total`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
