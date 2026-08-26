---
title: "Lemma: all_prime_empty"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `all_prime_empty`

The fully expanded AllPrime predicate holds vacuously on the empty prefix.

## Closed Peano statement

```text
forall b c. (forall i. (exists h. h + S i = 0) -> exists p. (((exists h. h + S p = S ((S i) * c)) /\ exists w. b = w * S ((S i) * c) + p) /\ (~(p = 1) /\ forall a d. p = a * d -> a = 1 \/ d = 1)))
```

## Dependencies

- [[add_eq_zero_right]]
- [[succ_ne_zero]]

## Checked dependents

- [[beta_canonical_append_empty]]
- [[prime_factorization_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **37 nodes**, depth **13**.
- Authored script length: **14 commands**.
- Runtime card: `pa lib all_prime_empty`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
