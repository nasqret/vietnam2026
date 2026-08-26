---
title: "Lemma: beta_sum_pointwise_mod_congruent"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_sum_pointwise_mod_congruent`

Pointwise congruent decoded prefixes have congruent finite sums.

## Closed Peano statement

```text
forall m b c d e l n q. (forall i a z. (exists fc_h_sp. fc_h_sp + S i = l) -> (((exists ff_h_sp_la. ff_h_sp_la + S (a) = S ((S (i)) * c)) /\ exists ff_q_sp_la. b = ff_q_sp_la * S ((S (i)) * c) + (a))) -> (((exists ff_h_sp_ra. ff_h_sp_ra + S (z) = S ((S (i)) * e)) /\ exists ff_q_sp_ra. d = ff_q_sp_ra * S ((S (i)) * e) + (z))) -> exists fc_u_sp_me fc_v_sp_me. a + m * fc_u_sp_me = z + m * fc_v_sp_me) -> (exists ff_u_sl ff_v_sl. ((((exists ff_h_sl_start. ff_h_sl_start + S (0) = S ((S (0)) * ff_v_sl)) /\ exists ff_q_sl_start. ff_u_sl = ff_q_sl_start * S ((S (0)) * ff_v_sl) + (0))) /\ ((((exists ff_h_sl_terminal. ff_h_sl_terminal + S (n) = S ((S (l)) * ff_v_sl)) /\ exists ff_q_sl_terminal. ff_u_sl = ff_q_sl_terminal * S ((S (l)) * ff_v_sl) + (n))) /\ forall ff_i_sl. (exists ff_lt_sl_bound. ff_lt_sl_bound + S ff_i_sl = l) -> exists ff_a_sl ff_r_sl ff_s_sl. ((((exists ff_h_sl_summand. ff_h_sl_summand + S (ff_a_sl) = S ((S (ff_i_sl)) * c)) /\ exists ff_q_sl_summand. b = ff_q_sl_summand * S ((S (ff_i_sl)) * c) + (ff_a_sl))) /\ ((((exists ff_h_sl_partial. ff_h_sl_partial + S (ff_r_sl) = S ((S (ff_i_sl)) * ff_v_sl)) /\ exists ff_q_sl_partial. ff_u_sl = ff_q_sl_partial * S ((S (ff_i_sl)) * ff_v_sl) + (ff_r_sl))) /\ ((((exists ff_h_sl_successor. ff_h_sl_successor + S (ff_s_sl) = S ((S (S ff_i_sl)) * ff_v_sl)) /\ exists ff_q_sl_successor. ff_u_sl = ff_q_sl_successor * S ((S (S ff_i_sl)) * ff_v_sl) + (ff_s_sl))) /\ ff_s_sl = ff_r_sl + ff_a_sl)))))) -> (exists ff_u_sr ff_v_sr. ((((exists ff_h_sr_start. ff_h_sr_start + S (0) = S ((S (0)) * ff_v_sr)) /\ exists ff_q_sr_start. ff_u_sr = ff_q_sr_start * S ((S (0)) * ff_v_sr) + (0))) /\ ((((exists ff_h_sr_terminal. ff_h_sr_terminal + S (q) = S ((S (l)) * ff_v_sr)) /\ exists ff_q_sr_terminal. ff_u_sr = ff_q_sr_terminal * S ((S (l)) * ff_v_sr) + (q))) /\ forall ff_i_sr. (exists ff_lt_sr_bound. ff_lt_sr_bound + S ff_i_sr = l) -> exists ff_a_sr ff_r_sr ff_s_sr. ((((exists ff_h_sr_summand. ff_h_sr_summand + S (ff_a_sr) = S ((S (ff_i_sr)) * e)) /\ exists ff_q_sr_summand. d = ff_q_sr_summand * S ((S (ff_i_sr)) * e) + (ff_a_sr))) /\ ((((exists ff_h_sr_partial. ff_h_sr_partial + S (ff_r_sr) = S ((S (ff_i_sr)) * ff_v_sr)) /\ exists ff_q_sr_partial. ff_u_sr = ff_q_sr_partial * S ((S (ff_i_sr)) * ff_v_sr) + (ff_r_sr))) /\ ((((exists ff_h_sr_successor. ff_h_sr_successor + S (ff_s_sr) = S ((S (S ff_i_sr)) * ff_v_sr)) /\ exists ff_q_sr_successor. ff_u_sr = ff_q_sr_successor * S ((S (S ff_i_sr)) * ff_v_sr) + (ff_s_sr))) /\ ff_s_sr = ff_r_sr + ff_a_sr)))))) -> exists fc_u_sv fc_v_sv. n + m * fc_u_sv = q + m * fc_v_sv
```

## Dependencies

- [[beta_sum_zero]]
- [[beta_sum_succ_decompose]]
- [[le_succ]]
- [[le_refl]]
- [[mod_eq_refl]]
- [[mod_eq_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2994 nodes**, depth **64**.
- Authored script length: **100 commands**.
- Runtime card: `pa lib beta_sum_pointwise_mod_congruent`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
