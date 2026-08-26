---
title: "Lemma: beta_value_lt_scaled_base"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_value_lt_scaled_base`

An old beta value fits every modulus after a constructive scaled-base rebase.

## Closed Peano statement

```text
forall b c i x C s j. ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x) -> ~(C = 0) -> exists h. h + S x = S ((S j) * (C * S (b + s)))
```

## Dependencies

- [[beta_value_le_code]]
- [[le_add_right]]
- [[succ_le_succ]]
- [[le_trans]]
- [[le_scaled_nonzero]]
- [[base_le_beta_modulus]]

## Checked dependents

- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **863 nodes**, depth **33**.
- Authored script length: **54 commands**.
- Runtime card: `pa lib beta_value_lt_scaled_base`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
