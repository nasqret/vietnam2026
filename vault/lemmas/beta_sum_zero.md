---
title: "Lemma: beta_sum_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_zero`

The sum of an empty decoded prefix is zero.

## Closed Peano statement

```text
forall b c n. (exists fs_u_zero fs_v_zero. ((((exists fs_h_zero_body_start. fs_h_zero_body_start + S (0) = S ((S (0)) * fs_v_zero)) /\ exists fs_q_zero_body_start. fs_u_zero = fs_q_zero_body_start * S ((S (0)) * fs_v_zero) + (0))) /\ ((((exists fs_h_zero_body_terminal. fs_h_zero_body_terminal + S (n) = S ((S (0)) * fs_v_zero)) /\ exists fs_q_zero_body_terminal. fs_u_zero = fs_q_zero_body_terminal * S ((S (0)) * fs_v_zero) + (n))) /\ forall fs_i_zero_body_steps. (exists fs_lt_zero_body_steps_bound. fs_lt_zero_body_steps_bound + S fs_i_zero_body_steps = 0) -> exists fs_a_zero_body_steps fs_r_zero_body_steps fs_s_zero_body_steps. ((((exists fs_h_zero_body_steps_summand. fs_h_zero_body_steps_summand + S (fs_a_zero_body_steps) = S ((S (fs_i_zero_body_steps)) * c)) /\ exists fs_q_zero_body_steps_summand. b = fs_q_zero_body_steps_summand * S ((S (fs_i_zero_body_steps)) * c) + (fs_a_zero_body_steps))) /\ ((((exists fs_h_zero_body_steps_partial. fs_h_zero_body_steps_partial + S (fs_r_zero_body_steps) = S ((S (fs_i_zero_body_steps)) * fs_v_zero)) /\ exists fs_q_zero_body_steps_partial. fs_u_zero = fs_q_zero_body_steps_partial * S ((S (fs_i_zero_body_steps)) * fs_v_zero) + (fs_r_zero_body_steps))) /\ ((((exists fs_h_zero_body_steps_successor. fs_h_zero_body_steps_successor + S (fs_s_zero_body_steps) = S ((S (S fs_i_zero_body_steps)) * fs_v_zero)) /\ exists fs_q_zero_body_steps_successor. fs_u_zero = fs_q_zero_body_steps_successor * S ((S (S fs_i_zero_body_steps)) * fs_v_zero) + (fs_s_zero_body_steps))) /\ fs_s_zero_body_steps = fs_r_zero_body_steps + fs_a_zero_body_steps)))))) -> n = 0
```

## Dependencies

- [[beta_at_unique]]

## Checked dependents

- [[beta_sum_pointwise_mod_congruent]]
- [[bit_count_zero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1171 nodes**, depth **60**.
- Authored script length: **16 commands**.
- Runtime card: `pa lib beta_sum_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
