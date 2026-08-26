---
title: "Lemma: beta_sum_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_functional`

The relational finite sum has a unique natural value.

## Closed Peano statement

```text
forall b c l n m. (exists ff_u_l ff_v_l. ((((exists ff_h_l_start. ff_h_l_start + S (0) = S ((S (0)) * ff_v_l)) /\ exists ff_q_l_start. ff_u_l = ff_q_l_start * S ((S (0)) * ff_v_l) + (0))) /\ ((((exists ff_h_l_terminal. ff_h_l_terminal + S (n) = S ((S (l)) * ff_v_l)) /\ exists ff_q_l_terminal. ff_u_l = ff_q_l_terminal * S ((S (l)) * ff_v_l) + (n))) /\ forall ff_i_l. (exists ff_lt_l_bound. ff_lt_l_bound + S ff_i_l = l) -> exists ff_a_l ff_r_l ff_s_l. ((((exists ff_h_l_summand. ff_h_l_summand + S (ff_a_l) = S ((S (ff_i_l)) * c)) /\ exists ff_q_l_summand. b = ff_q_l_summand * S ((S (ff_i_l)) * c) + (ff_a_l))) /\ ((((exists ff_h_l_partial. ff_h_l_partial + S (ff_r_l) = S ((S (ff_i_l)) * ff_v_l)) /\ exists ff_q_l_partial. ff_u_l = ff_q_l_partial * S ((S (ff_i_l)) * ff_v_l) + (ff_r_l))) /\ ((((exists ff_h_l_successor. ff_h_l_successor + S (ff_s_l) = S ((S (S ff_i_l)) * ff_v_l)) /\ exists ff_q_l_successor. ff_u_l = ff_q_l_successor * S ((S (S ff_i_l)) * ff_v_l) + (ff_s_l))) /\ ff_s_l = ff_r_l + ff_a_l)))))) -> (exists ff_u_r ff_v_r. ((((exists ff_h_r_start. ff_h_r_start + S (0) = S ((S (0)) * ff_v_r)) /\ exists ff_q_r_start. ff_u_r = ff_q_r_start * S ((S (0)) * ff_v_r) + (0))) /\ ((((exists ff_h_r_terminal. ff_h_r_terminal + S (m) = S ((S (l)) * ff_v_r)) /\ exists ff_q_r_terminal. ff_u_r = ff_q_r_terminal * S ((S (l)) * ff_v_r) + (m))) /\ forall ff_i_r. (exists ff_lt_r_bound. ff_lt_r_bound + S ff_i_r = l) -> exists ff_a_r ff_r_r ff_s_r. ((((exists ff_h_r_summand. ff_h_r_summand + S (ff_a_r) = S ((S (ff_i_r)) * c)) /\ exists ff_q_r_summand. b = ff_q_r_summand * S ((S (ff_i_r)) * c) + (ff_a_r))) /\ ((((exists ff_h_r_partial. ff_h_r_partial + S (ff_r_r) = S ((S (ff_i_r)) * ff_v_r)) /\ exists ff_q_r_partial. ff_u_r = ff_q_r_partial * S ((S (ff_i_r)) * ff_v_r) + (ff_r_r))) /\ ((((exists ff_h_r_successor. ff_h_r_successor + S (ff_s_r) = S ((S (S ff_i_r)) * ff_v_r)) /\ exists ff_q_r_successor. ff_u_r = ff_q_r_successor * S ((S (S ff_i_r)) * ff_v_r) + (ff_s_r))) /\ ff_s_r = ff_r_r + ff_a_r)))))) -> n = m
```

## Dependencies

- [[beta_sum_trace_functional]]

## Checked dependents

- [[beta_sum_exists_unique]]
- [[bit_count_functional]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1439 nodes**, depth **61**.
- Authored script length: **23 commands**.
- Runtime card: `pa lib beta_sum_functional`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
