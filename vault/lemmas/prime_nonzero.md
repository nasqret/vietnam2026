---
title: "Lemma: prime_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_nonzero`

Every prime natural is nonzero.

## Closed Peano statement

```text
forall p. (~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) -> ~(p = 0)
```

## Dependencies

- [[mul_zero_left]]
- [[succ_ne_zero]]

## Checked dependents

- [[prime_decidable]]
- [[prime_unbounded]]
- [[greatest_prime_divisor_search]]
- [[beta_canonical_product_cancel_last]]
- [[two_prime_product_uniqueness]]
- [[prime_mod_inverse]]
- [[prime_mod_cancel]]
- [[prime_is_succ_succ]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **49 nodes**, depth **11**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib prime_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
