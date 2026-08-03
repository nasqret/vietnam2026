---
title: "Lemma: beta_sum_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_exists`

Every decoded beta prefix has a relational finite sum.

## Closed Peano statement

```text
forall b c l. exists n. (exists ff_u_x ff_v_x. ((((exists ff_h_x_start. ff_h_x_start + S (0) = S ((S (0)) * ff_v_x)) /\ exists ff_q_x_start. ff_u_x = ff_q_x_start * S ((S (0)) * ff_v_x) + (0))) /\ ((((exists ff_h_x_terminal. ff_h_x_terminal + S (n) = S ((S (l)) * ff_v_x)) /\ exists ff_q_x_terminal. ff_u_x = ff_q_x_terminal * S ((S (l)) * ff_v_x) + (n))) /\ forall ff_i_x. (exists ff_lt_x_bound. ff_lt_x_bound + S ff_i_x = l) -> exists ff_a_x ff_r_x ff_s_x. ((((exists ff_h_x_summand. ff_h_x_summand + S (ff_a_x) = S ((S (ff_i_x)) * c)) /\ exists ff_q_x_summand. b = ff_q_x_summand * S ((S (ff_i_x)) * c) + (ff_a_x))) /\ ((((exists ff_h_x_partial. ff_h_x_partial + S (ff_r_x) = S ((S (ff_i_x)) * ff_v_x)) /\ exists ff_q_x_partial. ff_u_x = ff_q_x_partial * S ((S (ff_i_x)) * ff_v_x) + (ff_r_x))) /\ ((((exists ff_h_x_successor. ff_h_x_successor + S (ff_s_x) = S ((S (S ff_i_x)) * ff_v_x)) /\ exists ff_q_x_successor. ff_u_x = ff_q_x_successor * S ((S (S ff_i_x)) * ff_v_x) + (ff_s_x))) /\ ff_s_x = ff_r_x + ff_a_x))))))
```

## Dependencies

- [[beta_prefix_sum_trace_exists]]
- [[beta_at_exists]]

## Checked dependents

- [[beta_sum_exists_unique]]
- [[bit_count_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **30491 nodes**, depth **86**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib beta_sum_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
