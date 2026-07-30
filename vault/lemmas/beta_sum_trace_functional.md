---
title: "Lemma: beta_sum_trace_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_trace_functional`

Two exact prefix-sum traces over one decoded prefix have equal endpoints.

## Closed Peano statement

```text
forall b c l n u v m w d. (((((exists fs_h_functional_left_start. fs_h_functional_left_start + S (0) = S ((S (0)) * v)) /\ exists fs_q_functional_left_start. u = fs_q_functional_left_start * S ((S (0)) * v) + (0))) /\ ((((exists fs_h_functional_left_terminal. fs_h_functional_left_terminal + S (n) = S ((S (l)) * v)) /\ exists fs_q_functional_left_terminal. u = fs_q_functional_left_terminal * S ((S (l)) * v) + (n))) /\ forall fs_i_functional_left_steps. (exists fs_lt_functional_left_steps_bound. fs_lt_functional_left_steps_bound + S fs_i_functional_left_steps = l) -> exists fs_a_functional_left_steps fs_r_functional_left_steps fs_s_functional_left_steps. ((((exists fs_h_functional_left_steps_summand. fs_h_functional_left_steps_summand + S (fs_a_functional_left_steps) = S ((S (fs_i_functional_left_steps)) * c)) /\ exists fs_q_functional_left_steps_summand. b = fs_q_functional_left_steps_summand * S ((S (fs_i_functional_left_steps)) * c) + (fs_a_functional_left_steps))) /\ ((((exists fs_h_functional_left_steps_partial. fs_h_functional_left_steps_partial + S (fs_r_functional_left_steps) = S ((S (fs_i_functional_left_steps)) * v)) /\ exists fs_q_functional_left_steps_partial. u = fs_q_functional_left_steps_partial * S ((S (fs_i_functional_left_steps)) * v) + (fs_r_functional_left_steps))) /\ ((((exists fs_h_functional_left_steps_successor. fs_h_functional_left_steps_successor + S (fs_s_functional_left_steps) = S ((S (S fs_i_functional_left_steps)) * v)) /\ exists fs_q_functional_left_steps_successor. u = fs_q_functional_left_steps_successor * S ((S (S fs_i_functional_left_steps)) * v) + (fs_s_functional_left_steps))) /\ fs_s_functional_left_steps = fs_r_functional_left_steps + fs_a_functional_left_steps)))))) -> (((((exists fs_h_functional_right_start. fs_h_functional_right_start + S (0) = S ((S (0)) * d)) /\ exists fs_q_functional_right_start. w = fs_q_functional_right_start * S ((S (0)) * d) + (0))) /\ ((((exists fs_h_functional_right_terminal. fs_h_functional_right_terminal + S (m) = S ((S (l)) * d)) /\ exists fs_q_functional_right_terminal. w = fs_q_functional_right_terminal * S ((S (l)) * d) + (m))) /\ forall fs_i_functional_right_steps. (exists fs_lt_functional_right_steps_bound. fs_lt_functional_right_steps_bound + S fs_i_functional_right_steps = l) -> exists fs_a_functional_right_steps fs_r_functional_right_steps fs_s_functional_right_steps. ((((exists fs_h_functional_right_steps_summand. fs_h_functional_right_steps_summand + S (fs_a_functional_right_steps) = S ((S (fs_i_functional_right_steps)) * c)) /\ exists fs_q_functional_right_steps_summand. b = fs_q_functional_right_steps_summand * S ((S (fs_i_functional_right_steps)) * c) + (fs_a_functional_right_steps))) /\ ((((exists fs_h_functional_right_steps_partial. fs_h_functional_right_steps_partial + S (fs_r_functional_right_steps) = S ((S (fs_i_functional_right_steps)) * d)) /\ exists fs_q_functional_right_steps_partial. w = fs_q_functional_right_steps_partial * S ((S (fs_i_functional_right_steps)) * d) + (fs_r_functional_right_steps))) /\ ((((exists fs_h_functional_right_steps_successor. fs_h_functional_right_steps_successor + S (fs_s_functional_right_steps) = S ((S (S fs_i_functional_right_steps)) * d)) /\ exists fs_q_functional_right_steps_successor. w = fs_q_functional_right_steps_successor * S ((S (S fs_i_functional_right_steps)) * d) + (fs_s_functional_right_steps))) /\ fs_s_functional_right_steps = fs_r_functional_right_steps + fs_a_functional_right_steps)))))) -> n = m
```

## Dependencies

- [[beta_at_unique]]
- [[le_refl]]
- [[le_succ]]
- [[add_congr]]

## Checked dependents

- [[beta_sum_functional]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1382 nodes**, depth **60**.
- Authored script length: **153 commands**.
- Runtime card: `pa lib beta_sum_trace_functional`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
