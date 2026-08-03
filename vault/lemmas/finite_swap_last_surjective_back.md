---
title: "Lemma: finite_swap_last_surjective_back"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_swap_last_surjective_back`

Surjectivity of a swapped successor prefix transports back to the original code.

## Closed Peano statement

```text
forall b c z d n sn i x y. sn = S n -> (exists h. h + S i = n) -> (((exists ff_h_swap_surj_old_i. ff_h_swap_surj_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_swap_surj_old_i. b = ff_q_swap_surj_old_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_swap_surj_old_n. ff_h_swap_surj_old_n + S (y) = S ((S (n)) * c)) /\ exists ff_q_swap_surj_old_n. b = ff_q_swap_surj_old_n * S ((S (n)) * c) + (y))) -> (((exists ff_h_swap_surj_new_i. ff_h_swap_surj_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_swap_surj_new_i. z = ff_q_swap_surj_new_i * S ((S (i)) * d) + (y))) -> (((exists ff_h_swap_surj_new_n. ff_h_swap_surj_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_swap_surj_new_n. z = ff_q_swap_surj_new_n * S ((S (n)) * d) + (x))) -> (forall j a. (exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> (((exists ff_h_swap_surj_old_j. ff_h_swap_surj_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_swap_surj_old_j. b = ff_q_swap_surj_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_swap_surj_new_j. ff_h_swap_surj_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_swap_surj_new_j. z = ff_q_swap_surj_new_j * S ((S (j)) * d) + (a)))) -> (forall fp_value_swap_surj_new. (exists fp_gap_swap_surj_new_value. fp_gap_swap_surj_new_value + S fp_value_swap_surj_new = sn) -> exists fp_i_swap_surj_new. ((exists fp_gap_swap_surj_new_index. fp_gap_swap_surj_new_index + S fp_i_swap_surj_new = sn) /\ (((exists ff_h_swap_surj_new_entry. ff_h_swap_surj_new_entry + S (fp_value_swap_surj_new) = S ((S (fp_i_swap_surj_new)) * d)) /\ exists ff_q_swap_surj_new_entry. z = ff_q_swap_surj_new_entry * S ((S (fp_i_swap_surj_new)) * d) + (fp_value_swap_surj_new))))) -> (forall fp_value_swap_surj_old. (exists fp_gap_swap_surj_old_value. fp_gap_swap_surj_old_value + S fp_value_swap_surj_old = sn) -> exists fp_i_swap_surj_old. ((exists fp_gap_swap_surj_old_index. fp_gap_swap_surj_old_index + S fp_i_swap_surj_old = sn) /\ (((exists ff_h_swap_surj_old_entry. ff_h_swap_surj_old_entry + S (fp_value_swap_surj_old) = S ((S (fp_i_swap_surj_old)) * c)) /\ exists ff_q_swap_surj_old_entry. b = ff_q_swap_surj_old_entry * S ((S (fp_i_swap_surj_old)) * c) + (fp_value_swap_surj_old)))))
```

## Dependencies

- [[beta_prefix_swap_last_reflect]]
- [[le_succ]]
- [[le_refl]]

## Checked dependents

- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1929 nodes**, depth **63**.
- Authored script length: **80 commands**.
- Runtime card: `pa lib finite_swap_last_surjective_back`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
