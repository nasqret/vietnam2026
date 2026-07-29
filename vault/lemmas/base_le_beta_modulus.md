---
title: "Lemma: base_le_beta_modulus"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `base_le_beta_modulus`

A beta base is at most every beta modulus over that base.

## Closed Peano statement

```text
forall c i. exists h. h + c = S ((S i) * c)
```

## Dependencies

- [[le_add_left]]
- [[mul_succ_left]]
- [[le_succ]]

## Checked dependents

- [[beta_value_lt_scaled_base]]
- [[new_value_lt_scaled_base]]

## Verification record

- Independently checked from the empty context.
- Certificate: **233 nodes**, depth **24**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib base_le_beta_modulus`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
