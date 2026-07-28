---
title: "Lemma: division_remainder_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `division_remainder_exists`

Every positive divisor admits a quotient and a strictly bounded remainder.

## Closed Peano statement

```text
forall m n. ~(m = 0) -> exists q r. n = m * q + r /\ S r <= m
```

## Dependencies

- [[zero_or_succ]]
- [[division_remainder_succ]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **196 nodes**, depth **37**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib division_remainder_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
