---
title: "Lemma: bounded_common_multiple_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_common_multiple_exists`

Every finite initial interval has a nonzero common-multiple surrogate.

## Closed Peano statement

```text
forall B. exists c. (~(c = 0) /\ forall t. (exists h. S t + S h = S B) -> exists k. c = S t * k)
```

## Dependencies

- [[bounded_common_multiple_step]]
- [[succ_ne_zero]]
- [[add_eq_zero_left]]

## Checked dependents

- [[bounded_beta_moduli_pairwise_coprime_exists]]
- [[prime_unbounded]]
- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **640 nodes**, depth **30**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib bounded_common_multiple_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
