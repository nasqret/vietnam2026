---
title: "Lemma: remainder_bound_step"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `remainder_bound_step`

A bounded remainder either reaches the divisor or remains bounded after successor.

## Closed Peano statement

```text
forall r d. (exists k. k + S r = d) -> S r = d \/ exists k. k + S (S r) = d
```

## Dependencies

- [[le_eq_or_lt]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **78 nodes**, depth **21**.
- Authored script length: **7 commands**.
- Runtime card: `pa lib remainder_bound_step`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
