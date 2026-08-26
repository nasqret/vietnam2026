---
title: "Lemma: prime_three"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_three`

Three is prime in the expanded first-order prime predicate.

## Closed Peano statement

```text
~(3 = 1) /\ forall a b. 3 = a * b -> a = 1 \/ b = 1
```

## Dependencies

- [[mul_succ_left]]
- [[mul_eq_one_components]]
- [[add_eq_zero_left]]
- [[mul_eq_zero]]
- [[mul_zero_left]]
- [[zero_or_succ]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **691 nodes**, depth **43**.
- Authored script length: **94 commands**.
- Runtime card: `pa lib prime_three`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
