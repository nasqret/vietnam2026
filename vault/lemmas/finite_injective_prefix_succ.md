---
title: "Lemma: finite_injective_prefix_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_injective_prefix_succ`

Injectivity of a successor prefix restricts to its old prefix.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_i_inj_succ fp_j_inj_succ fp_value_inj_succ. (exists fp_gap_inj_succ_i. fp_gap_inj_succ_i + S fp_i_inj_succ = sn) -> (exists fp_gap_inj_succ_j. fp_gap_inj_succ_j + S fp_j_inj_succ = sn) -> (((exists ff_h_inj_succ_left. ff_h_inj_succ_left + S (fp_value_inj_succ) = S ((S (fp_i_inj_succ)) * c)) /\ exists ff_q_inj_succ_left. b = ff_q_inj_succ_left * S ((S (fp_i_inj_succ)) * c) + (fp_value_inj_succ))) -> (((exists ff_h_inj_succ_right. ff_h_inj_succ_right + S (fp_value_inj_succ) = S ((S (fp_j_inj_succ)) * c)) /\ exists ff_q_inj_succ_right. b = ff_q_inj_succ_right * S ((S (fp_j_inj_succ)) * c) + (fp_value_inj_succ))) -> fp_i_inj_succ = fp_j_inj_succ) -> (forall fp_i_inj_prefix fp_j_inj_prefix fp_value_inj_prefix. (exists fp_gap_inj_prefix_i. fp_gap_inj_prefix_i + S fp_i_inj_prefix = n) -> (exists fp_gap_inj_prefix_j. fp_gap_inj_prefix_j + S fp_j_inj_prefix = n) -> (((exists ff_h_inj_prefix_left. ff_h_inj_prefix_left + S (fp_value_inj_prefix) = S ((S (fp_i_inj_prefix)) * c)) /\ exists ff_q_inj_prefix_left. b = ff_q_inj_prefix_left * S ((S (fp_i_inj_prefix)) * c) + (fp_value_inj_prefix))) -> (((exists ff_h_inj_prefix_right. ff_h_inj_prefix_right + S (fp_value_inj_prefix) = S ((S (fp_j_inj_prefix)) * c)) /\ exists ff_q_inj_prefix_right. b = ff_q_inj_prefix_right * S ((S (fp_j_inj_prefix)) * c) + (fp_value_inj_prefix))) -> fp_i_inj_prefix = fp_j_inj_prefix)
```

## Dependencies

- [[le_succ]]

## Checked dependents

- [[finite_no_top_successor_gate]]
- [[finite_bounded_injective_surjective]]

## Verification record

- Independently checked from the empty context.
- Certificate: **105 nodes**, depth **34**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib finite_injective_prefix_succ`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
