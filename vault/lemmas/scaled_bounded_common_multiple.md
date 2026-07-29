---
title: "Lemma: scaled_bounded_common_multiple"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `scaled_bounded_common_multiple`

A right multiple of a bounded common multiple remains such a common multiple.

## Closed Peano statement

```text
forall N C B. (forall t. (exists h. S t + S h = S N) -> exists q. C = S t * q) -> forall t. (exists h. S t + S h = S N) -> exists q. C * B = S t * q
```

## Dependencies

- [[multiple_mul_right]]

## Checked dependents

- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **147 nodes**, depth **19**.
- Authored script length: **15 commands**.
- Runtime card: `pa lib scaled_bounded_common_multiple`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
