---
title: "Lemma: prime_divisor_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_divisor_exists`

Every nonzero nonunit natural has a prime divisor.

## Closed Peano statement

```text
forall n. ~(n = 0) -> ~(n = 1) -> exists p. ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\ exists k. n = p * k)
```

## Dependencies

- [[le_refl]]
- [[prime_divisor_exists_up_to]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2977 nodes**, depth **80**.
- Authored script length: **9 commands**.
- Runtime card: `pa lib prime_divisor_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
