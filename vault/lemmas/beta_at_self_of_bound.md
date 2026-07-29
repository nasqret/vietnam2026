---
title: "Lemma: beta_at_self_of_bound"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_self_of_bound`

A value below a Gödel-beta modulus decodes to itself when used as the code.

## Closed Peano statement

```text
forall c i x. (exists h. h + S x = S ((S i) * c)) -> ((exists h. h + S x = S ((S i) * c)) /\ exists q. x = q * S ((S i) * c) + x)
```

## Dependencies

- [[mul_zero_left]]
- [[zero_add]]

## Checked dependents

- [[beta_prefix_product_trace_exists]]
- [[prime_factorization_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **62 nodes**, depth **16**.
- Authored script length: **12 commands**.
- Runtime card: `pa lib beta_at_self_of_bound`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
