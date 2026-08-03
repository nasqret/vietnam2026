---
title: "Lemma: finite_bounded_injective_surjective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `finite_bounded_injective_surjective`

Every bounded injective beta-coded prefix is surjective onto its finite interval.

## Closed Peano statement

```text
forall n b c. (forall fp_i_pigeon_bounded. (exists fp_gap_pigeon_bounded_index. fp_gap_pigeon_bounded_index + S fp_i_pigeon_bounded = n) -> exists fp_value_pigeon_bounded. ((((exists ff_h_pigeon_bounded_entry. ff_h_pigeon_bounded_entry + S (fp_value_pigeon_bounded) = S ((S (fp_i_pigeon_bounded)) * c)) /\ exists ff_q_pigeon_bounded_entry. b = ff_q_pigeon_bounded_entry * S ((S (fp_i_pigeon_bounded)) * c) + (fp_value_pigeon_bounded))) /\ (exists fp_gap_pigeon_bounded_value. fp_gap_pigeon_bounded_value + S fp_value_pigeon_bounded = n))) -> (forall fp_i_pigeon_injective fp_j_pigeon_injective fp_value_pigeon_injective. (exists fp_gap_pigeon_injective_i. fp_gap_pigeon_injective_i + S fp_i_pigeon_injective = n) -> (exists fp_gap_pigeon_injective_j. fp_gap_pigeon_injective_j + S fp_j_pigeon_injective = n) -> (((exists ff_h_pigeon_injective_left. ff_h_pigeon_injective_left + S (fp_value_pigeon_injective) = S ((S (fp_i_pigeon_injective)) * c)) /\ exists ff_q_pigeon_injective_left. b = ff_q_pigeon_injective_left * S ((S (fp_i_pigeon_injective)) * c) + (fp_value_pigeon_injective))) -> (((exists ff_h_pigeon_injective_right. ff_h_pigeon_injective_right + S (fp_value_pigeon_injective) = S ((S (fp_j_pigeon_injective)) * c)) /\ exists ff_q_pigeon_injective_right. b = ff_q_pigeon_injective_right * S ((S (fp_j_pigeon_injective)) * c) + (fp_value_pigeon_injective))) -> fp_i_pigeon_injective = fp_j_pigeon_injective) -> (forall fp_value_pigeon_surjective. (exists fp_gap_pigeon_surjective_value. fp_gap_pigeon_surjective_value + S fp_value_pigeon_surjective = n) -> exists fp_i_pigeon_surjective. ((exists fp_gap_pigeon_surjective_index. fp_gap_pigeon_surjective_index + S fp_i_pigeon_surjective = n) /\ (((exists ff_h_pigeon_surjective_entry. ff_h_pigeon_surjective_entry + S (fp_value_pigeon_surjective) = S ((S (fp_i_pigeon_surjective)) * c)) /\ exists ff_q_pigeon_surjective_entry. b = ff_q_pigeon_surjective_entry * S ((S (fp_i_pigeon_surjective)) * c) + (fp_value_pigeon_surjective)))))
```

## Dependencies

- [[finite_surjective_zero]]
- [[finite_contains_decidable]]
- [[finite_bounded_last_succ]]
- [[beta_prefix_swap_last_from_entries]]
- [[finite_swap_last_bounded]]
- [[finite_swap_last_injective]]
- [[finite_bounded_prefix_without_top]]
- [[finite_injective_prefix_succ]]
- [[finite_surjective_succ_from_prefix]]
- [[finite_swap_last_surjective_back]]
- [[finite_no_top_successor_gate]]
- [[beta_at_unique]]
- [[le_succ]]
- [[le_refl]]
- [[lt_irrefl_expanded]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **42463 nodes**, depth **89**.
- Authored script length: **178 commands**.
- Runtime card: `pa lib finite_bounded_injective_surjective`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
