---
title: "Lemma: division_remainder_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `division_remainder_succ`

Every dividend has a quotient and bounded remainder for a successor divisor.

## Closed Peano statement

```text
forall d n. exists q r. n = S d * q + r /\ S r <= S d
```

## Dependencies

- [[zero_add]]
- [[add_succ_left]]
- [[zero_or_succ]]

## Checked dependents

- [[division_remainder_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **179 nodes**, depth **26**.
- Authored script length: **38 commands**.
- Runtime card: `pa lib division_remainder_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
