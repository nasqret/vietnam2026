---
title: "Lemma: beta_prefix_swap_last_from_entries"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_swap_last_from_entries`

Swap a chosen interior beta entry with the last entry, given both decoded values.

## Closed Peano statement

```text
forall b c n i x y. (exists h. h + S i = n) -> (((exists ff_h_swap_old_i. ff_h_swap_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_swap_old_i. b = ff_q_swap_old_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_swap_old_n. ff_h_swap_old_n + S (y) = S ((S (n)) * c)) /\ exists ff_q_swap_old_n. b = ff_q_swap_old_n * S ((S (n)) * c) + (y))) -> exists z d. ((((exists ff_h_swap_new_i. ff_h_swap_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_swap_new_i. z = ff_q_swap_new_i * S ((S (i)) * d) + (y))) /\ ((((exists ff_h_swap_new_n. ff_h_swap_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_swap_new_n. z = ff_q_swap_new_n * S ((S (n)) * d) + (x))) /\ forall j a. (exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> (((exists ff_h_swap_old_j. ff_h_swap_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_swap_old_j. b = ff_q_swap_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_swap_new_j. ff_h_swap_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_swap_new_j. z = ff_q_swap_new_j * S ((S (j)) * d) + (a)))))
```

## Dependencies

- [[beta_prefix_replace_exists]]
- [[le_succ]]
- [[le_refl]]
- [[lt_irrefl_expanded]]

## Checked dependents

- [[beta_prefix_swap_last_exists]]
- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **31221 nodes**, depth **85**.
- Authored script length: **87 commands**.
- Runtime card: `pa lib beta_prefix_swap_last_from_entries`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
