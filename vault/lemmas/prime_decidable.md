---
title: "Lemma: prime_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_decidable`

Primality of every natural number is constructively decidable.

## Closed Peano statement

```text
forall n. ((~(n = 1) /\ forall a b. n = a * b -> a = 1 \/ b = 1) \/ ~((~(n = 1) /\ forall a b. n = a * b -> a = 1 \/ b = 1)))
```

## Dependencies

- [[eq_decidable]]
- [[prime_or_composite]]
- [[prime_nonzero]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2194 nodes**, depth **73**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib prime_decidable`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
