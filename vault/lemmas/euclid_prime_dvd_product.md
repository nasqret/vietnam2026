---
title: "Lemma: euclid_prime_dvd_product"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `euclid_prime_dvd_product`

A prime dividing a product divides at least one factor (Euclid's lemma).

## Closed Peano statement

```text
forall p a b. (~(p = 1) /\ forall c d. p = c * d -> c = 1 \/ d = 1) -> (exists k. a * b = p * k) -> (exists u. a = p * u) \/ exists v. b = p * v
```

## Dependencies

- [[prime_divisor_eq_one_or_self]]
- [[gcd_exists_relational]]
- [[is_gcd_one_to_coprime]]
- [[gauss_coprime_cancel]]

## Checked dependents

- [[beta_prime_divisor_product_member]]
- [[two_prime_product_uniqueness]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5382 nodes**, depth **55**.
- Authored script length: **36 commands**.
- Runtime card: `pa lib euclid_prime_dvd_product`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
