---
title: "Lemma: prime_or_composite"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_or_composite`

Every nonzero nonunit natural is constructively prime or has a nontrivial factor pair.

## Closed Peano statement

```text
forall n. ~(n = 0) -> ~(n = 1) -> ((~(n = 1) /\ forall a b. n = a * b -> a = 1 \/ b = 1) \/ exists c d. ((~(c = 1) /\ ~(d = 1)) /\ n = c * d))
```

## Dependencies

- [[divisor_le_nonzero]]
- [[factor_search_up_to]]

## Checked dependents

- [[prime_decidable]]
- [[prime_divisor_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2038 nodes**, depth **71**.
- Authored script length: **38 commands**.
- Runtime card: `pa lib prime_or_composite`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
