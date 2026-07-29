---
title: "Lemma: prime_unbounded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_unbounded`

Euclid's common-multiple argument constructs a prime above every natural.

## Closed Peano statement

```text
forall n. exists p. (exists k. k + S n = p) /\ (~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1)
```

## Dependencies

- [[bounded_common_multiple_exists]]
- [[prime_divisor_exists]]
- [[prime_nonzero]]
- [[nonzero_is_succ]]
- [[add_succ_left]]
- [[add_comm]]
- [[divides_remainder]]
- [[divisor_one]]
- [[mul_one]]
- [[le_or_lt]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4595 nodes**, depth **82**.
- Authored script length: **84 commands**.
- Runtime card: `pa lib prime_unbounded`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
