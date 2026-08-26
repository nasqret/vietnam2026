---
title: "Lemma: le_add_right"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_add_right`

Adding on the right produces an explicit order witness.

## Closed Peano statement

```text
forall a b. exists k. k + a = a + b
```

## Dependencies

- [[add_comm]]

## Checked dependents

- [[beta_value_lt_scaled_base]]

## Verification record

- Independently checked from the empty context.
- Certificate: **80 nodes**, depth **13**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib le_add_right`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
