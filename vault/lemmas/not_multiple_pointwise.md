---
title: "Lemma: not_multiple_pointwise"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_multiple_pointwise`

Turn a negated existential multiple into pointwise inequalities.

## Closed Peano statement

```text
forall a n. ~(exists q. n = a * q) -> forall q. ~(n = a * q)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **9 nodes**, depth **8**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib not_multiple_pointwise`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
