---
title: "Lemma: finite_surjective_succ_intro"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_surjective_succ_intro`

A surjective prefix plus its new top value is surjective at successor length.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_value_surj_n. (exists fp_gap_surj_n_value. fp_gap_surj_n_value + S fp_value_surj_n = n) -> exists fp_i_surj_n. ((exists fp_gap_surj_n_index. fp_gap_surj_n_index + S fp_i_surj_n = n) /\ (((exists ff_h_surj_n_entry. ff_h_surj_n_entry + S (fp_value_surj_n) = S ((S (fp_i_surj_n)) * c)) /\ exists ff_q_surj_n_entry. b = ff_q_surj_n_entry * S ((S (fp_i_surj_n)) * c) + (fp_value_surj_n))))) -> (((exists ff_h_last_n. ff_h_last_n + S (n) = S ((S (n)) * c)) /\ exists ff_q_last_n. b = ff_q_last_n * S ((S (n)) * c) + (n))) -> (forall fp_value_surj_succ. (exists fp_gap_surj_succ_value. fp_gap_surj_succ_value + S fp_value_surj_succ = sn) -> exists fp_i_surj_succ. ((exists fp_gap_surj_succ_index. fp_gap_surj_succ_index + S fp_i_surj_succ = sn) /\ (((exists ff_h_surj_succ_entry. ff_h_surj_succ_entry + S (fp_value_surj_succ) = S ((S (fp_i_surj_succ)) * c)) /\ exists ff_q_surj_succ_entry. b = ff_q_surj_succ_entry * S ((S (fp_i_surj_succ)) * c) + (fp_value_surj_succ)))))
```

## Dependencies

- [[finite_lt_succ_eq_or_lt]]
- [[le_refl]]
- [[le_succ]]

## Checked dependents

- [[finite_surjective_succ_from_prefix]]

## Verification record

- Independently checked from the empty context.
- Certificate: **243 nodes**, depth **22**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib finite_surjective_succ_intro`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
