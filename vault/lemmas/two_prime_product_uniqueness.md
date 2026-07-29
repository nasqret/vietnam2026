---
title: "Lemma: two_prime_product_uniqueness"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `two_prime_product_uniqueness`

A product of two primes determines its factors up to swapping them.

## Closed Peano statement

```text
forall p q r s. (~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) -> (~(q = 1) /\ forall c d. q = c * d -> c = 1 \/ d = 1) -> (~(r = 1) /\ forall e f. r = e * f -> e = 1 \/ f = 1) -> (~(s = 1) /\ forall g h. s = g * h -> g = 1 \/ h = 1) -> p * q = r * s -> (p = r /\ q = s) \/ (p = s /\ q = r)
```

## Dependencies

- [[euclid_prime_dvd_product]]
- [[prime_divisor_eq_one_or_self]]
- [[prime_nonzero]]
- [[mul_left_cancel_nonzero]]
- [[mul_comm]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6035 nodes**, depth **56**.
- Authored script length: **77 commands**.
- Runtime card: `pa lib two_prime_product_uniqueness`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
