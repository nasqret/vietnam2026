---
title: "Lemma: all_prime_succ_elim_last"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_prime_succ_elim_last`

Extract the final decoded prime from an AllPrime successor prefix.

## Closed Peano statement

```text
forall b c l. (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> exists p. (((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))
```

## Dependencies

- [[le_refl]]

## Checked dependents

- [[beta_canonical_append_general]]
- [[beta_canonical_last_factor_bound]]
- [[beta_prime_divisor_product_member]]
- [[beta_nonempty_all_prime_product_ne_one]]
- [[beta_canonical_last_factors_equal]]
- [[beta_canonical_product_cancel_last]]

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **11**.
- Authored script length: **8 commands**.
- Runtime card: `pa lib all_prime_succ_elim_last`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
