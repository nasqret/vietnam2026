---
title: "Lemma: zero_add"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `zero_add`

Zero is a left identity for addition; unlike PA3, this needs induction.

## Closed Peano statement

```text
forall n. 0 + n = n
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[add_comm]]
- [[mul_one]]
- [[le_refl]]
- [[drop_add_prefix_from_fixed]]
- [[le_succ_self]]
- [[le_eq_or_lt]]
- [[division_remainder_succ]]
- [[division_remainder_unique]]
- [[factor_difference]]
- [[gcd_balanced_bezout_exists_up_to]]
- [[beta_at_self_of_bound]]
- [[dvd_to_mod_zero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **17 nodes**, depth **8**.
- Authored script length: **3 commands**.
- Runtime card: `pa lib zero_add`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
