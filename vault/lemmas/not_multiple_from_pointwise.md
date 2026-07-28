---
title: "Lemma: not_multiple_from_pointwise"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `not_multiple_from_pointwise`

Reconstruct a negated existential from pointwise inequalities.

## Closed Peano statement

```text
forall a n. (forall q. ~(n = a * q)) -> ~(exists q. n = a * q)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **13 nodes**, depth **9**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib not_multiple_from_pointwise`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
