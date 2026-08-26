---
title: "Lemma: beta_sum_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_exists_unique`

Every decoded beta prefix has exactly one relational finite sum.

## Closed Peano statement

```text
forall b c l. exists n. ((exists ff_u_unique_value ff_v_unique_value. ((((exists ff_h_unique_value_start. ff_h_unique_value_start + S (0) = S ((S (0)) * ff_v_unique_value)) /\ exists ff_q_unique_value_start. ff_u_unique_value = ff_q_unique_value_start * S ((S (0)) * ff_v_unique_value) + (0))) /\ ((((exists ff_h_unique_value_terminal. ff_h_unique_value_terminal + S (n) = S ((S (l)) * ff_v_unique_value)) /\ exists ff_q_unique_value_terminal. ff_u_unique_value = ff_q_unique_value_terminal * S ((S (l)) * ff_v_unique_value) + (n))) /\ forall ff_i_unique_value. (exists ff_lt_unique_value_bound. ff_lt_unique_value_bound + S ff_i_unique_value = l) -> exists ff_a_unique_value ff_r_unique_value ff_s_unique_value. ((((exists ff_h_unique_value_summand. ff_h_unique_value_summand + S (ff_a_unique_value) = S ((S (ff_i_unique_value)) * c)) /\ exists ff_q_unique_value_summand. b = ff_q_unique_value_summand * S ((S (ff_i_unique_value)) * c) + (ff_a_unique_value))) /\ ((((exists ff_h_unique_value_partial. ff_h_unique_value_partial + S (ff_r_unique_value) = S ((S (ff_i_unique_value)) * ff_v_unique_value)) /\ exists ff_q_unique_value_partial. ff_u_unique_value = ff_q_unique_value_partial * S ((S (ff_i_unique_value)) * ff_v_unique_value) + (ff_r_unique_value))) /\ ((((exists ff_h_unique_value_successor. ff_h_unique_value_successor + S (ff_s_unique_value) = S ((S (S ff_i_unique_value)) * ff_v_unique_value)) /\ exists ff_q_unique_value_successor. ff_u_unique_value = ff_q_unique_value_successor * S ((S (S ff_i_unique_value)) * ff_v_unique_value) + (ff_s_unique_value))) /\ ff_s_unique_value = ff_r_unique_value + ff_a_unique_value)))))) /\ forall m. (exists ff_u_unique_other ff_v_unique_other. ((((exists ff_h_unique_other_start. ff_h_unique_other_start + S (0) = S ((S (0)) * ff_v_unique_other)) /\ exists ff_q_unique_other_start. ff_u_unique_other = ff_q_unique_other_start * S ((S (0)) * ff_v_unique_other) + (0))) /\ ((((exists ff_h_unique_other_terminal. ff_h_unique_other_terminal + S (m) = S ((S (l)) * ff_v_unique_other)) /\ exists ff_q_unique_other_terminal. ff_u_unique_other = ff_q_unique_other_terminal * S ((S (l)) * ff_v_unique_other) + (m))) /\ forall ff_i_unique_other. (exists ff_lt_unique_other_bound. ff_lt_unique_other_bound + S ff_i_unique_other = l) -> exists ff_a_unique_other ff_r_unique_other ff_s_unique_other. ((((exists ff_h_unique_other_summand. ff_h_unique_other_summand + S (ff_a_unique_other) = S ((S (ff_i_unique_other)) * c)) /\ exists ff_q_unique_other_summand. b = ff_q_unique_other_summand * S ((S (ff_i_unique_other)) * c) + (ff_a_unique_other))) /\ ((((exists ff_h_unique_other_partial. ff_h_unique_other_partial + S (ff_r_unique_other) = S ((S (ff_i_unique_other)) * ff_v_unique_other)) /\ exists ff_q_unique_other_partial. ff_u_unique_other = ff_q_unique_other_partial * S ((S (ff_i_unique_other)) * ff_v_unique_other) + (ff_r_unique_other))) /\ ((((exists ff_h_unique_other_successor. ff_h_unique_other_successor + S (ff_s_unique_other) = S ((S (S ff_i_unique_other)) * ff_v_unique_other)) /\ exists ff_q_unique_other_successor. ff_u_unique_other = ff_q_unique_other_successor * S ((S (S ff_i_unique_other)) * ff_v_unique_other) + (ff_s_unique_other))) /\ ff_s_unique_other = ff_r_unique_other + ff_a_unique_other)))))) -> n = m)
```

## Dependencies

- [[beta_sum_exists]]
- [[beta_sum_functional]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **31979 nodes**, depth **87**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib beta_sum_exists_unique`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
