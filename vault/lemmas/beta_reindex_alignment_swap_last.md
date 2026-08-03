---
title: "Lemma: beta_reindex_alignment_swap_last"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_reindex_alignment_swap_last`

Simultaneous interior/final swaps of an index code and target factors preserve alignment.

## Closed Peano statement

```text
forall r s u v b c z d w e n i m x y. (((exists ff_h_align_swap_map_i. ff_h_align_swap_map_i + S (m) = S ((S (i)) * v)) /\ exists ff_q_align_swap_map_i. u = ff_q_align_swap_map_i * S ((S (i)) * v) + (m))) -> (((exists ff_h_align_swap_map_n. ff_h_align_swap_map_n + S (n) = S ((S (n)) * v)) /\ exists ff_q_align_swap_map_n. u = ff_q_align_swap_map_n * S ((S (n)) * v) + (n))) -> (forall k j. (exists h. h + S k = S n) -> ~(k = i) -> ~(k = n) -> (((exists ff_h_align_swap_map_old. ff_h_align_swap_map_old + S (j) = S ((S (k)) * s)) /\ exists ff_q_align_swap_map_old. r = ff_q_align_swap_map_old * S ((S (k)) * s) + (j))) -> (((exists ff_h_align_swap_map_new. ff_h_align_swap_map_new + S (j) = S ((S (k)) * v)) /\ exists ff_q_align_swap_map_new. u = ff_q_align_swap_map_new * S ((S (k)) * v) + (j)))) -> (((exists ff_h_align_swap_source_m. ff_h_align_swap_source_m + S (y) = S ((S (m)) * c)) /\ exists ff_q_align_swap_source_m. b = ff_q_align_swap_source_m * S ((S (m)) * c) + (y))) -> (((exists ff_h_align_swap_source_n. ff_h_align_swap_source_n + S (x) = S ((S (n)) * c)) /\ exists ff_q_align_swap_source_n. b = ff_q_align_swap_source_n * S ((S (n)) * c) + (x))) -> (((exists ff_h_align_swap_target_i. ff_h_align_swap_target_i + S (y) = S ((S (i)) * e)) /\ exists ff_q_align_swap_target_i. w = ff_q_align_swap_target_i * S ((S (i)) * e) + (y))) -> (((exists ff_h_align_swap_target_n. ff_h_align_swap_target_n + S (x) = S ((S (n)) * e)) /\ exists ff_q_align_swap_target_n. w = ff_q_align_swap_target_n * S ((S (n)) * e) + (x))) -> (forall k a. (exists h. h + S k = S n) -> ~(k = i) -> ~(k = n) -> (((exists ff_h_align_swap_target_old. ff_h_align_swap_target_old + S (a) = S ((S (k)) * d)) /\ exists ff_q_align_swap_target_old. z = ff_q_align_swap_target_old * S ((S (k)) * d) + (a))) -> (((exists ff_h_align_swap_target_new. ff_h_align_swap_target_new + S (a) = S ((S (k)) * e)) /\ exists ff_q_align_swap_target_new. w = ff_q_align_swap_target_new * S ((S (k)) * e) + (a)))) -> (forall fpr_i_align_swap_old fpr_j_align_swap_old fpr_x_align_swap_old. (exists fpr_h_align_swap_old. fpr_h_align_swap_old + S fpr_i_align_swap_old = S n) -> (((exists ff_h_align_swap_old_map. ff_h_align_swap_old_map + S (fpr_j_align_swap_old) = S ((S (fpr_i_align_swap_old)) * s)) /\ exists ff_q_align_swap_old_map. r = ff_q_align_swap_old_map * S ((S (fpr_i_align_swap_old)) * s) + (fpr_j_align_swap_old))) -> (((exists ff_h_align_swap_old_source. ff_h_align_swap_old_source + S (fpr_x_align_swap_old) = S ((S (fpr_j_align_swap_old)) * c)) /\ exists ff_q_align_swap_old_source. b = ff_q_align_swap_old_source * S ((S (fpr_j_align_swap_old)) * c) + (fpr_x_align_swap_old))) -> (((exists ff_h_align_swap_old_target. ff_h_align_swap_old_target + S (fpr_x_align_swap_old) = S ((S (fpr_i_align_swap_old)) * d)) /\ exists ff_q_align_swap_old_target. z = ff_q_align_swap_old_target * S ((S (fpr_i_align_swap_old)) * d) + (fpr_x_align_swap_old)))) -> (forall fpr_i_align_swap_new fpr_j_align_swap_new fpr_x_align_swap_new. (exists fpr_h_align_swap_new. fpr_h_align_swap_new + S fpr_i_align_swap_new = S n) -> (((exists ff_h_align_swap_new_map. ff_h_align_swap_new_map + S (fpr_j_align_swap_new) = S ((S (fpr_i_align_swap_new)) * v)) /\ exists ff_q_align_swap_new_map. u = ff_q_align_swap_new_map * S ((S (fpr_i_align_swap_new)) * v) + (fpr_j_align_swap_new))) -> (((exists ff_h_align_swap_new_source. ff_h_align_swap_new_source + S (fpr_x_align_swap_new) = S ((S (fpr_j_align_swap_new)) * c)) /\ exists ff_q_align_swap_new_source. b = ff_q_align_swap_new_source * S ((S (fpr_j_align_swap_new)) * c) + (fpr_x_align_swap_new))) -> (((exists ff_h_align_swap_new_target. ff_h_align_swap_new_target + S (fpr_x_align_swap_new) = S ((S (fpr_i_align_swap_new)) * e)) /\ exists ff_q_align_swap_new_target. w = ff_q_align_swap_new_target * S ((S (fpr_i_align_swap_new)) * e) + (fpr_x_align_swap_new))))
```

## Dependencies

- [[beta_prefix_swap_last_reflect]]
- [[beta_at_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **3057 nodes**, depth **63**.
- Authored script length: **102 commands**.
- Runtime card: `pa lib beta_reindex_alignment_swap_last`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
