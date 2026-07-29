---
title: "Lemma: beta_canonical_last_factor_bound"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_canonical_last_factor_bound`

The last factor of a nonempty AllPrime Product obeys any bound on prime divisors of the product.

## Closed Peano statement

```text
forall b c l n s. (forall i. (exists h. h + S i = S l) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1))) -> (exists u v. (((exists h. h + S 1 = S ((S 0) * v)) /\ exists q. u = q * S ((S 0) * v) + 1) /\ (((exists h. h + S n = S ((S S l) * v)) /\ exists q. u = q * S ((S S l) * v) + n) /\ forall i. (exists h. h + S i = S l) -> exists p r s. (((exists h. h + S p = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + p) /\ (((exists h. h + S r = S ((S i) * v)) /\ exists q. u = q * S ((S i) * v) + r) /\ (((exists h. h + S s = S ((S S i) * v)) /\ exists q. u = q * S ((S S i) * v) + s) /\ s = r * p)))))) -> (forall r. (~(r = 1) /\ forall a d. r = a * d -> a = 1 \/ d = 1) -> (exists k. n = r * k) -> (exists h. h + r = s)) -> exists p. (((exists h. h + S p = S ((S l) * c)) /\ exists w. b = w * S ((S l) * c) + p) /\ (exists h. h + p = s))
```

## Dependencies

- [[all_prime_succ_elim_last]]
- [[beta_factor_divides_product]]
- [[le_refl]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **3079 nodes**, depth **67**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib beta_canonical_last_factor_bound`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
