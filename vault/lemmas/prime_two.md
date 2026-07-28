---
title: "Lemma: prime_two"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_two`

Two is prime in the expanded first-order prime predicate.

## Closed Peano statement

```text
~(2 = 1) /\ forall a b. 2 = a * b -> a = 1 \/ b = 1
```

## Dependencies

- [[mul_zero_left]]
- [[two_large_factors_impossible]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **395 nodes**, depth **59**.
- Authored script length: **35 commands**.
- Runtime card: `pa lib prime_two`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
