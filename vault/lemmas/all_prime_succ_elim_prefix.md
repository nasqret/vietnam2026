---
title: "Lemma: all_prime_succ_elim_prefix"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_prime_succ_elim_prefix`

Restrict an AllPrime successor prefix to its old prefix.

## Closed Peano statement

```text
forall b c l. (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (forall i. (exists h. h + S i = l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1)))
```

## Dependencies

- [[le_succ]]

## Checked dependents

- [[beta_prime_divisor_product_member]]
- [[beta_canonical_product_cancel_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **64 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib all_prime_succ_elim_prefix`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
