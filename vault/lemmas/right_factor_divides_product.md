---
title: "Lemma: right_factor_divides_product"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `right_factor_divides_product`

The right factor divides a product.

## Closed Peano statement

```text
forall a b. exists k. a * b = b * k
```

## Dependencies

- [[mul_comm]]

## Checked dependents

- [[beta_accumulated_product_step]]
- [[beta_exclusive_accumulated_product_step]]

## Verification record

- Independently checked from the empty context.
- Certificate: **229 nodes**, depth **25**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib right_factor_divides_product`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
