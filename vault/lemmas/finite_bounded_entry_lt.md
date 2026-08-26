---
title: "Lemma: finite_bounded_entry_lt"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_bounded_entry_lt`

Every explicitly decoded entry of a bounded prefix satisfies its value bound.

## Closed Peano statement

```text
forall b c l i x. (forall fp_i_entry_bound. (exists fp_gap_entry_bound_index. fp_gap_entry_bound_index + S fp_i_entry_bound = l) -> exists fp_value_entry_bound. ((((exists ff_h_entry_bound_entry. ff_h_entry_bound_entry + S (fp_value_entry_bound) = S ((S (fp_i_entry_bound)) * c)) /\ exists ff_q_entry_bound_entry. b = ff_q_entry_bound_entry * S ((S (fp_i_entry_bound)) * c) + (fp_value_entry_bound))) /\ (exists fp_gap_entry_bound_value. fp_gap_entry_bound_value + S fp_value_entry_bound = l))) -> (exists h. h + S i = l) -> (((exists ff_h_entry_bound_at. ff_h_entry_bound_at + S (x) = S ((S (i)) * c)) /\ exists ff_q_entry_bound_at. b = ff_q_entry_bound_at * S ((S (i)) * c) + (x))) -> exists h. h + S x = l
```

## Dependencies

- [[beta_at_unique]]

## Checked dependents

- [[finite_swap_last_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1150 nodes**, depth **60**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib finite_bounded_entry_lt`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
