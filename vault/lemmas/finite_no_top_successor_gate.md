---
title: "Lemma: finite_no_top_successor_gate"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_no_top_successor_gate`

The no-top branch of the constructive successor induction is complete.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_i_bounded_succ. (exists fp_gap_bounded_succ_index. fp_gap_bounded_succ_index + S fp_i_bounded_succ = sn) -> exists fp_value_bounded_succ. ((((exists ff_h_bounded_succ_entry. ff_h_bounded_succ_entry + S (fp_value_bounded_succ) = S ((S (fp_i_bounded_succ)) * c)) /\ exists ff_q_bounded_succ_entry. b = ff_q_bounded_succ_entry * S ((S (fp_i_bounded_succ)) * c) + (fp_value_bounded_succ))) /\ (exists fp_gap_bounded_succ_value. fp_gap_bounded_succ_value + S fp_value_bounded_succ = sn))) -> (forall fp_i_inj_succ fp_j_inj_succ fp_value_inj_succ. (exists fp_gap_inj_succ_i. fp_gap_inj_succ_i + S fp_i_inj_succ = sn) -> (exists fp_gap_inj_succ_j. fp_gap_inj_succ_j + S fp_j_inj_succ = sn) -> (((exists ff_h_inj_succ_left. ff_h_inj_succ_left + S (fp_value_inj_succ) = S ((S (fp_i_inj_succ)) * c)) /\ exists ff_q_inj_succ_left. b = ff_q_inj_succ_left * S ((S (fp_i_inj_succ)) * c) + (fp_value_inj_succ))) -> (((exists ff_h_inj_succ_right. ff_h_inj_succ_right + S (fp_value_inj_succ) = S ((S (fp_j_inj_succ)) * c)) /\ exists ff_q_inj_succ_right. b = ff_q_inj_succ_right * S ((S (fp_j_inj_succ)) * c) + (fp_value_inj_succ))) -> fp_i_inj_succ = fp_j_inj_succ) -> ~(exists fp_i_contains_top. ((exists fp_gap_contains_top_index. fp_gap_contains_top_index + S fp_i_contains_top = n) /\ (((exists ff_h_contains_top_entry. ff_h_contains_top_entry + S (n) = S ((S (fp_i_contains_top)) * c)) /\ exists ff_q_contains_top_entry. b = ff_q_contains_top_entry * S ((S (fp_i_contains_top)) * c) + (n))))) -> ((forall fp_i_bounded_prefix. (exists fp_gap_bounded_prefix_index. fp_gap_bounded_prefix_index + S fp_i_bounded_prefix = n) -> exists fp_value_bounded_prefix. ((((exists ff_h_bounded_prefix_entry. ff_h_bounded_prefix_entry + S (fp_value_bounded_prefix) = S ((S (fp_i_bounded_prefix)) * c)) /\ exists ff_q_bounded_prefix_entry. b = ff_q_bounded_prefix_entry * S ((S (fp_i_bounded_prefix)) * c) + (fp_value_bounded_prefix))) /\ (exists fp_gap_bounded_prefix_value. fp_gap_bounded_prefix_value + S fp_value_bounded_prefix = n))) -> (forall fp_i_inj_prefix fp_j_inj_prefix fp_value_inj_prefix. (exists fp_gap_inj_prefix_i. fp_gap_inj_prefix_i + S fp_i_inj_prefix = n) -> (exists fp_gap_inj_prefix_j. fp_gap_inj_prefix_j + S fp_j_inj_prefix = n) -> (((exists ff_h_inj_prefix_left. ff_h_inj_prefix_left + S (fp_value_inj_prefix) = S ((S (fp_i_inj_prefix)) * c)) /\ exists ff_q_inj_prefix_left. b = ff_q_inj_prefix_left * S ((S (fp_i_inj_prefix)) * c) + (fp_value_inj_prefix))) -> (((exists ff_h_inj_prefix_right. ff_h_inj_prefix_right + S (fp_value_inj_prefix) = S ((S (fp_j_inj_prefix)) * c)) /\ exists ff_q_inj_prefix_right. b = ff_q_inj_prefix_right * S ((S (fp_j_inj_prefix)) * c) + (fp_value_inj_prefix))) -> fp_i_inj_prefix = fp_j_inj_prefix) -> (forall fp_value_surj_n. (exists fp_gap_surj_n_value. fp_gap_surj_n_value + S fp_value_surj_n = n) -> exists fp_i_surj_n. ((exists fp_gap_surj_n_index. fp_gap_surj_n_index + S fp_i_surj_n = n) /\ (((exists ff_h_surj_n_entry. ff_h_surj_n_entry + S (fp_value_surj_n) = S ((S (fp_i_surj_n)) * c)) /\ exists ff_q_surj_n_entry. b = ff_q_surj_n_entry * S ((S (fp_i_surj_n)) * c) + (fp_value_surj_n)))))) -> (forall fp_value_surj_succ. (exists fp_gap_surj_succ_value. fp_gap_surj_succ_value + S fp_value_surj_succ = sn) -> exists fp_i_surj_succ. ((exists fp_gap_surj_succ_index. fp_gap_surj_succ_index + S fp_i_surj_succ = sn) /\ (((exists ff_h_surj_succ_entry. ff_h_surj_succ_entry + S (fp_value_surj_succ) = S ((S (fp_i_surj_succ)) * c)) /\ exists ff_q_surj_succ_entry. b = ff_q_surj_succ_entry * S ((S (fp_i_surj_succ)) * c) + (fp_value_surj_succ)))))
```

## Dependencies

- [[finite_bounded_prefix_without_top]]
- [[finite_injective_prefix_succ]]
- [[finite_surjective_succ_from_prefix]]

## Checked dependents

- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1054 nodes**, depth **36**.
- Authored script length: **48 commands**.
- Runtime card: `pa lib finite_no_top_successor_gate`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
