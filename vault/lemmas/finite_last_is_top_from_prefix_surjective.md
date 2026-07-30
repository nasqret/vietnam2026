---
title: "Lemma: finite_last_is_top_from_prefix_surjective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_last_is_top_from_prefix_surjective`

A bounded injective successor sequence must place the new value last once its prefix is surjective.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_i_bounded_succ. (exists fp_gap_bounded_succ_index. fp_gap_bounded_succ_index + S fp_i_bounded_succ = sn) -> exists fp_value_bounded_succ. ((((exists ff_h_bounded_succ_entry. ff_h_bounded_succ_entry + S (fp_value_bounded_succ) = S ((S (fp_i_bounded_succ)) * c)) /\ exists ff_q_bounded_succ_entry. b = ff_q_bounded_succ_entry * S ((S (fp_i_bounded_succ)) * c) + (fp_value_bounded_succ))) /\ (exists fp_gap_bounded_succ_value. fp_gap_bounded_succ_value + S fp_value_bounded_succ = sn))) -> (forall fp_i_inj_succ fp_j_inj_succ fp_value_inj_succ. (exists fp_gap_inj_succ_i. fp_gap_inj_succ_i + S fp_i_inj_succ = sn) -> (exists fp_gap_inj_succ_j. fp_gap_inj_succ_j + S fp_j_inj_succ = sn) -> (((exists ff_h_inj_succ_left. ff_h_inj_succ_left + S (fp_value_inj_succ) = S ((S (fp_i_inj_succ)) * c)) /\ exists ff_q_inj_succ_left. b = ff_q_inj_succ_left * S ((S (fp_i_inj_succ)) * c) + (fp_value_inj_succ))) -> (((exists ff_h_inj_succ_right. ff_h_inj_succ_right + S (fp_value_inj_succ) = S ((S (fp_j_inj_succ)) * c)) /\ exists ff_q_inj_succ_right. b = ff_q_inj_succ_right * S ((S (fp_j_inj_succ)) * c) + (fp_value_inj_succ))) -> fp_i_inj_succ = fp_j_inj_succ) -> (forall fp_value_surj_n. (exists fp_gap_surj_n_value. fp_gap_surj_n_value + S fp_value_surj_n = n) -> exists fp_i_surj_n. ((exists fp_gap_surj_n_index. fp_gap_surj_n_index + S fp_i_surj_n = n) /\ (((exists ff_h_surj_n_entry. ff_h_surj_n_entry + S (fp_value_surj_n) = S ((S (fp_i_surj_n)) * c)) /\ exists ff_q_surj_n_entry. b = ff_q_surj_n_entry * S ((S (fp_i_surj_n)) * c) + (fp_value_surj_n))))) -> (((exists ff_h_last_n. ff_h_last_n + S (n) = S ((S (n)) * c)) /\ exists ff_q_last_n. b = ff_q_last_n * S ((S (n)) * c) + (n)))
```

## Dependencies

- [[finite_bounded_last_succ]]
- [[finite_lt_succ_eq_or_lt]]
- [[le_refl]]
- [[le_succ]]
- [[lt_irrefl_expanded]]

## Checked dependents

- [[finite_surjective_succ_from_prefix]]

## Verification record

- Independently checked from the empty context.
- Certificate: **402 nodes**, depth **30**.
- Authored script length: **53 commands**.
- Runtime card: `pa lib finite_last_is_top_from_prefix_surjective`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
