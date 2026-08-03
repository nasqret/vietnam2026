---
title: "Lemma: finite_swap_last_injective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_swap_last_injective`

A swap-last recoding preserves injectivity of the full successor prefix.

## Closed Peano statement

```text
forall b c z d n sn i x y. sn = S n -> (exists h. h + S i = n) -> (forall fp_i_swap_inj_old fp_j_swap_inj_old fp_value_swap_inj_old. (exists fp_gap_swap_inj_old_i. fp_gap_swap_inj_old_i + S fp_i_swap_inj_old = sn) -> (exists fp_gap_swap_inj_old_j. fp_gap_swap_inj_old_j + S fp_j_swap_inj_old = sn) -> (((exists ff_h_swap_inj_old_left. ff_h_swap_inj_old_left + S (fp_value_swap_inj_old) = S ((S (fp_i_swap_inj_old)) * c)) /\ exists ff_q_swap_inj_old_left. b = ff_q_swap_inj_old_left * S ((S (fp_i_swap_inj_old)) * c) + (fp_value_swap_inj_old))) -> (((exists ff_h_swap_inj_old_right. ff_h_swap_inj_old_right + S (fp_value_swap_inj_old) = S ((S (fp_j_swap_inj_old)) * c)) /\ exists ff_q_swap_inj_old_right. b = ff_q_swap_inj_old_right * S ((S (fp_j_swap_inj_old)) * c) + (fp_value_swap_inj_old))) -> fp_i_swap_inj_old = fp_j_swap_inj_old) -> (((exists ff_h_swap_inj_old_i. ff_h_swap_inj_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_swap_inj_old_i. b = ff_q_swap_inj_old_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_swap_inj_old_n. ff_h_swap_inj_old_n + S (y) = S ((S (n)) * c)) /\ exists ff_q_swap_inj_old_n. b = ff_q_swap_inj_old_n * S ((S (n)) * c) + (y))) -> (((exists ff_h_swap_inj_new_i. ff_h_swap_inj_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_swap_inj_new_i. z = ff_q_swap_inj_new_i * S ((S (i)) * d) + (y))) -> (((exists ff_h_swap_inj_new_n. ff_h_swap_inj_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_swap_inj_new_n. z = ff_q_swap_inj_new_n * S ((S (n)) * d) + (x))) -> (forall j a. (exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> (((exists ff_h_swap_inj_old_j. ff_h_swap_inj_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_swap_inj_old_j. b = ff_q_swap_inj_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_swap_inj_new_j. ff_h_swap_inj_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_swap_inj_new_j. z = ff_q_swap_inj_new_j * S ((S (j)) * d) + (a)))) -> (forall fp_i_swap_inj_new fp_j_swap_inj_new fp_value_swap_inj_new. (exists fp_gap_swap_inj_new_i. fp_gap_swap_inj_new_i + S fp_i_swap_inj_new = sn) -> (exists fp_gap_swap_inj_new_j. fp_gap_swap_inj_new_j + S fp_j_swap_inj_new = sn) -> (((exists ff_h_swap_inj_new_left. ff_h_swap_inj_new_left + S (fp_value_swap_inj_new) = S ((S (fp_i_swap_inj_new)) * d)) /\ exists ff_q_swap_inj_new_left. z = ff_q_swap_inj_new_left * S ((S (fp_i_swap_inj_new)) * d) + (fp_value_swap_inj_new))) -> (((exists ff_h_swap_inj_new_right. ff_h_swap_inj_new_right + S (fp_value_swap_inj_new) = S ((S (fp_j_swap_inj_new)) * d)) /\ exists ff_q_swap_inj_new_right. z = ff_q_swap_inj_new_right * S ((S (fp_j_swap_inj_new)) * d) + (fp_value_swap_inj_new))) -> fp_i_swap_inj_new = fp_j_swap_inj_new)
```

## Dependencies

- [[beta_prefix_swap_last_reflect]]
- [[le_succ]]
- [[le_refl]]

## Checked dependents

- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2203 nodes**, depth **63**.
- Authored script length: **220 commands**.
- Runtime card: `pa lib finite_swap_last_injective`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
