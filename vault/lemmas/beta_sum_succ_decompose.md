---
title: "Lemma: beta_sum_succ_decompose"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_succ_decompose`

A successor sum decomposes into its prefix sum and final summand.

## Closed Peano statement

```text
forall b c l n. (exists fs_u_succ fs_v_succ. ((((exists fs_h_succ_body_start. fs_h_succ_body_start + S (0) = S ((S (0)) * fs_v_succ)) /\ exists fs_q_succ_body_start. fs_u_succ = fs_q_succ_body_start * S ((S (0)) * fs_v_succ) + (0))) /\ ((((exists fs_h_succ_body_terminal. fs_h_succ_body_terminal + S (n) = S ((S (S l)) * fs_v_succ)) /\ exists fs_q_succ_body_terminal. fs_u_succ = fs_q_succ_body_terminal * S ((S (S l)) * fs_v_succ) + (n))) /\ forall fs_i_succ_body_steps. (exists fs_lt_succ_body_steps_bound. fs_lt_succ_body_steps_bound + S fs_i_succ_body_steps = S l) -> exists fs_a_succ_body_steps fs_r_succ_body_steps fs_s_succ_body_steps. ((((exists fs_h_succ_body_steps_summand. fs_h_succ_body_steps_summand + S (fs_a_succ_body_steps) = S ((S (fs_i_succ_body_steps)) * c)) /\ exists fs_q_succ_body_steps_summand. b = fs_q_succ_body_steps_summand * S ((S (fs_i_succ_body_steps)) * c) + (fs_a_succ_body_steps))) /\ ((((exists fs_h_succ_body_steps_partial. fs_h_succ_body_steps_partial + S (fs_r_succ_body_steps) = S ((S (fs_i_succ_body_steps)) * fs_v_succ)) /\ exists fs_q_succ_body_steps_partial. fs_u_succ = fs_q_succ_body_steps_partial * S ((S (fs_i_succ_body_steps)) * fs_v_succ) + (fs_r_succ_body_steps))) /\ ((((exists fs_h_succ_body_steps_successor. fs_h_succ_body_steps_successor + S (fs_s_succ_body_steps) = S ((S (S fs_i_succ_body_steps)) * fs_v_succ)) /\ exists fs_q_succ_body_steps_successor. fs_u_succ = fs_q_succ_body_steps_successor * S ((S (S fs_i_succ_body_steps)) * fs_v_succ) + (fs_s_succ_body_steps))) /\ fs_s_succ_body_steps = fs_r_succ_body_steps + fs_a_succ_body_steps)))))) -> exists a r. (((exists fs_h_succ_factor. fs_h_succ_factor + S (a) = S ((S (l)) * c)) /\ exists fs_q_succ_factor. b = fs_q_succ_factor * S ((S (l)) * c) + (a))) /\ ((exists ff_u_prefix ff_v_prefix. ((((exists ff_h_prefix_start. ff_h_prefix_start + S (0) = S ((S (0)) * ff_v_prefix)) /\ exists ff_q_prefix_start. ff_u_prefix = ff_q_prefix_start * S ((S (0)) * ff_v_prefix) + (0))) /\ ((((exists ff_h_prefix_terminal. ff_h_prefix_terminal + S (r) = S ((S (l)) * ff_v_prefix)) /\ exists ff_q_prefix_terminal. ff_u_prefix = ff_q_prefix_terminal * S ((S (l)) * ff_v_prefix) + (r))) /\ forall ff_i_prefix. (exists ff_lt_prefix_bound. ff_lt_prefix_bound + S ff_i_prefix = l) -> exists ff_a_prefix ff_r_prefix ff_s_prefix. ((((exists ff_h_prefix_summand. ff_h_prefix_summand + S (ff_a_prefix) = S ((S (ff_i_prefix)) * c)) /\ exists ff_q_prefix_summand. b = ff_q_prefix_summand * S ((S (ff_i_prefix)) * c) + (ff_a_prefix))) /\ ((((exists ff_h_prefix_partial. ff_h_prefix_partial + S (ff_r_prefix) = S ((S (ff_i_prefix)) * ff_v_prefix)) /\ exists ff_q_prefix_partial. ff_u_prefix = ff_q_prefix_partial * S ((S (ff_i_prefix)) * ff_v_prefix) + (ff_r_prefix))) /\ ((((exists ff_h_prefix_successor. ff_h_prefix_successor + S (ff_s_prefix) = S ((S (S ff_i_prefix)) * ff_v_prefix)) /\ exists ff_q_prefix_successor. ff_u_prefix = ff_q_prefix_successor * S ((S (S ff_i_prefix)) * ff_v_prefix) + (ff_s_prefix))) /\ ff_s_prefix = ff_r_prefix + ff_a_prefix)))))) /\ n = r + a)
```

## Dependencies

- [[le_refl]]
- [[le_succ]]
- [[beta_at_unique]]

## Checked dependents

- [[beta_sum_pointwise_mod_congruent]]
- [[bit_count_succ_decompose]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1257 nodes**, depth **62**.
- Authored script length: **51 commands**.
- Runtime card: `pa lib beta_sum_succ_decompose`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
