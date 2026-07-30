---
title: "Lemma: beta_prefix_sum_trace_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_sum_trace_exists`

Every decoded beta prefix admits an exact beta-coded prefix-sum trace.

## Closed Peano statement

```text
forall b c l. exists fs_u_trace fs_v_trace. ((((exists fs_h_trace_start. fs_h_trace_start + S (0) = S ((S (0)) * fs_v_trace)) /\ exists fs_q_trace_start. fs_u_trace = fs_q_trace_start * S ((S (0)) * fs_v_trace) + (0))) /\ forall fs_i_trace_steps. (exists fs_lt_trace_steps_bound. fs_lt_trace_steps_bound + S fs_i_trace_steps = l) -> exists fs_a_trace_steps fs_r_trace_steps fs_s_trace_steps. ((((exists fs_h_trace_steps_summand. fs_h_trace_steps_summand + S (fs_a_trace_steps) = S ((S (fs_i_trace_steps)) * c)) /\ exists fs_q_trace_steps_summand. b = fs_q_trace_steps_summand * S ((S (fs_i_trace_steps)) * c) + (fs_a_trace_steps))) /\ ((((exists fs_h_trace_steps_partial. fs_h_trace_steps_partial + S (fs_r_trace_steps) = S ((S (fs_i_trace_steps)) * fs_v_trace)) /\ exists fs_q_trace_steps_partial. fs_u_trace = fs_q_trace_steps_partial * S ((S (fs_i_trace_steps)) * fs_v_trace) + (fs_r_trace_steps))) /\ ((((exists fs_h_trace_steps_successor. fs_h_trace_steps_successor + S (fs_s_trace_steps) = S ((S (S fs_i_trace_steps)) * fs_v_trace)) /\ exists fs_q_trace_steps_successor. fs_u_trace = fs_q_trace_steps_successor * S ((S (S fs_i_trace_steps)) * fs_v_trace) + (fs_s_trace_steps))) /\ fs_s_trace_steps = fs_r_trace_steps + fs_a_trace_steps))))
```

## Dependencies

- [[beta_at_self_of_bound]]
- [[add_eq_zero_right]]
- [[succ_ne_zero]]
- [[beta_at_exists]]
- [[beta_prefix_extend]]
- [[zero_le]]
- [[succ_le_succ]]
- [[le_refl]]
- [[le_of_succ_le_succ]]
- [[le_eq_or_lt]]
- [[one_mul]]

## Checked dependents

- [[beta_sum_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **29985 nodes**, depth **85**.
- Authored script length: **136 commands**.
- Runtime card: `pa lib beta_prefix_sum_trace_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
