---
title: "Lemma: new_value_lt_scaled_base"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `new_value_lt_scaled_base`

The appended value fits every modulus after the same constructive scaled-base rebase.

## Closed Peano statement

```text
forall b s C j. ~(C = 0) -> exists h. h + S s = S ((S j) * (C * S (b + s)))
```

## Dependencies

- [[le_add_left]]
- [[succ_le_succ]]
- [[le_scaled_nonzero]]
- [[le_trans]]
- [[base_le_beta_modulus]]

## Checked dependents

- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **751 nodes**, depth **31**.
- Authored script length: **36 commands**.
- Runtime card: `pa lib new_value_lt_scaled_base`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
