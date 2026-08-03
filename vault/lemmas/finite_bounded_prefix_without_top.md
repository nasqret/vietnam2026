---
title: "Lemma: finite_bounded_prefix_without_top"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_bounded_prefix_without_top`

If a successor prefix omits its top value, its old prefix is bounded by the predecessor.

## Closed Peano statement

```text
forall b c n sn. sn = S n -> (forall fp_i_bounded_succ. (exists fp_gap_bounded_succ_index. fp_gap_bounded_succ_index + S fp_i_bounded_succ = sn) -> exists fp_value_bounded_succ. ((((exists ff_h_bounded_succ_entry. ff_h_bounded_succ_entry + S (fp_value_bounded_succ) = S ((S (fp_i_bounded_succ)) * c)) /\ exists ff_q_bounded_succ_entry. b = ff_q_bounded_succ_entry * S ((S (fp_i_bounded_succ)) * c) + (fp_value_bounded_succ))) /\ (exists fp_gap_bounded_succ_value. fp_gap_bounded_succ_value + S fp_value_bounded_succ = sn))) -> (forall i. (exists h. h + S i = n) -> ~(((exists ff_h_top_i. ff_h_top_i + S (n) = S ((S (i)) * c)) /\ exists ff_q_top_i. b = ff_q_top_i * S ((S (i)) * c) + (n)))) -> (forall fp_i_bounded_prefix. (exists fp_gap_bounded_prefix_index. fp_gap_bounded_prefix_index + S fp_i_bounded_prefix = n) -> exists fp_value_bounded_prefix. ((((exists ff_h_bounded_prefix_entry. ff_h_bounded_prefix_entry + S (fp_value_bounded_prefix) = S ((S (fp_i_bounded_prefix)) * c)) /\ exists ff_q_bounded_prefix_entry. b = ff_q_bounded_prefix_entry * S ((S (fp_i_bounded_prefix)) * c) + (fp_value_bounded_prefix))) /\ (exists fp_gap_bounded_prefix_value. fp_gap_bounded_prefix_value + S fp_value_bounded_prefix = n)))
```

## Dependencies

- [[le_succ]]
- [[finite_lt_succ_eq_or_lt]]

## Checked dependents

- [[finite_no_top_successor_gate]]
- [[finite_bounded_injective_surjective]]
- [[finite_fixed_last_prefix_bounded]]

## Verification record

- Independently checked from the empty context.
- Certificate: **216 nodes**, depth **23**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib finite_bounded_prefix_without_top`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
