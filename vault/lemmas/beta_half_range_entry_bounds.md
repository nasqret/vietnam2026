---
title: "Lemma: beta_half_range_entry_bounds"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_half_range_entry_bounds`

Entries 1 through h in an odd half-range are nonzero and below p.

## Closed Peano statement

```text
forall p h b c i x. p = 2 * h + 1 -> (forall gh_i_half. (exists gh_lt_half_bound. gh_lt_half_bound + S gh_i_half = h) -> (((exists gh_h_half. gh_h_half + S (1 + gh_i_half) = S ((S gh_i_half) * c)) /\ exists gh_q_half. b = gh_q_half * S ((S gh_i_half) * c) + (1 + gh_i_half)))) -> (exists gh_lt_half_i. gh_lt_half_i + S i = h) -> (((exists ff_h_half_i. ff_h_half_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_half_i. b = ff_q_half_i * S ((S (i)) * c) + (x))) -> (~(x = 0) /\ (exists gh_lt_half_value. gh_lt_half_value + S x = p))
```

## Dependencies

- [[beta_range_entry_eq]]
- [[zero_add]]
- [[add_succ_left]]
- [[mul_succ_left]]
- [[mul_zero_left]]
- [[add_assoc]]
- [[lt_of_le_of_lt]]

## Checked dependents

- [[beta_half_range_mod_eq_value]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1585 nodes**, depth **61**.
- Authored script length: **53 commands**.
- Runtime card: `pa lib beta_half_range_entry_bounds`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
