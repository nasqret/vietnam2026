---
title: "Lemma: finite_fixed_last_prefix_bounded"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_fixed_last_prefix_bounded`

A bounded injective successor reindexing fixed at its last position is bounded on the old prefix.

## Closed Peano statement

```text
forall r s n. (forall fp_i_fixed_last_bounded_succ. (exists fp_gap_fixed_last_bounded_succ_index. fp_gap_fixed_last_bounded_succ_index + S fp_i_fixed_last_bounded_succ = S n) -> exists fp_value_fixed_last_bounded_succ. ((((exists ff_h_fixed_last_bounded_succ_entry. ff_h_fixed_last_bounded_succ_entry + S (fp_value_fixed_last_bounded_succ) = S ((S (fp_i_fixed_last_bounded_succ)) * s)) /\ exists ff_q_fixed_last_bounded_succ_entry. r = ff_q_fixed_last_bounded_succ_entry * S ((S (fp_i_fixed_last_bounded_succ)) * s) + (fp_value_fixed_last_bounded_succ))) /\ (exists fp_gap_fixed_last_bounded_succ_value. fp_gap_fixed_last_bounded_succ_value + S fp_value_fixed_last_bounded_succ = S n))) -> (forall fp_i_fixed_last_injective_succ fp_j_fixed_last_injective_succ fp_value_fixed_last_injective_succ. (exists fp_gap_fixed_last_injective_succ_i. fp_gap_fixed_last_injective_succ_i + S fp_i_fixed_last_injective_succ = S n) -> (exists fp_gap_fixed_last_injective_succ_j. fp_gap_fixed_last_injective_succ_j + S fp_j_fixed_last_injective_succ = S n) -> (((exists ff_h_fixed_last_injective_succ_left. ff_h_fixed_last_injective_succ_left + S (fp_value_fixed_last_injective_succ) = S ((S (fp_i_fixed_last_injective_succ)) * s)) /\ exists ff_q_fixed_last_injective_succ_left. r = ff_q_fixed_last_injective_succ_left * S ((S (fp_i_fixed_last_injective_succ)) * s) + (fp_value_fixed_last_injective_succ))) -> (((exists ff_h_fixed_last_injective_succ_right. ff_h_fixed_last_injective_succ_right + S (fp_value_fixed_last_injective_succ) = S ((S (fp_j_fixed_last_injective_succ)) * s)) /\ exists ff_q_fixed_last_injective_succ_right. r = ff_q_fixed_last_injective_succ_right * S ((S (fp_j_fixed_last_injective_succ)) * s) + (fp_value_fixed_last_injective_succ))) -> fp_i_fixed_last_injective_succ = fp_j_fixed_last_injective_succ) -> (((exists ff_h_fixed_last_entry. ff_h_fixed_last_entry + S (n) = S ((S (n)) * s)) /\ exists ff_q_fixed_last_entry. r = ff_q_fixed_last_entry * S ((S (n)) * s) + (n))) -> (forall fp_i_fixed_last_bounded_prefix. (exists fp_gap_fixed_last_bounded_prefix_index. fp_gap_fixed_last_bounded_prefix_index + S fp_i_fixed_last_bounded_prefix = n) -> exists fp_value_fixed_last_bounded_prefix. ((((exists ff_h_fixed_last_bounded_prefix_entry. ff_h_fixed_last_bounded_prefix_entry + S (fp_value_fixed_last_bounded_prefix) = S ((S (fp_i_fixed_last_bounded_prefix)) * s)) /\ exists ff_q_fixed_last_bounded_prefix_entry. r = ff_q_fixed_last_bounded_prefix_entry * S ((S (fp_i_fixed_last_bounded_prefix)) * s) + (fp_value_fixed_last_bounded_prefix))) /\ (exists fp_gap_fixed_last_bounded_prefix_value. fp_gap_fixed_last_bounded_prefix_value + S fp_value_fixed_last_bounded_prefix = n)))
```

## Dependencies

- [[finite_bounded_prefix_without_top]]
- [[le_succ]]
- [[le_refl]]
- [[lt_irrefl_expanded]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **409 nodes**, depth **24**.
- Authored script length: **39 commands**.
- Runtime card: `pa lib finite_fixed_last_prefix_bounded`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
