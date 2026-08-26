---
title: "Lemma: multiple_decidable_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `multiple_decidable_nonzero`

Divisibility by a nonzero natural is constructively decidable.

## Closed Peano statement

```text
forall d n. ~(d = 0) -> (exists q. n = d * q) \/ ~(exists q. n = d * q)
```

## Dependencies

- [[eq_decidable]]
- [[division_remainder_exists]]
- [[multiple_has_zero_remainder]]
- [[division_remainder_unique]]

## Checked dependents

- [[multiple_decidable]]
- [[factor_search_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1242 nodes**, depth **61**.
- Authored script length: **40 commands**.
- Runtime card: `pa lib multiple_decidable_nonzero`.
- Book route: *Divisibility and congruence* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
