---
title: "Lemma: beta_product_pointwise_mod_congruent"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_pointwise_mod_congruent`

Pointwise congruent decoded prefixes have congruent finite products.

## Closed Peano statement

```text
forall m b c d e l n q. (forall i a z. (exists fc_h_pp. fc_h_pp + S i = l) -> (((exists ff_h_pp_la. ff_h_pp_la + S (a) = S ((S (i)) * c)) /\ exists ff_q_pp_la. b = ff_q_pp_la * S ((S (i)) * c) + (a))) -> (((exists ff_h_pp_ra. ff_h_pp_ra + S (z) = S ((S (i)) * e)) /\ exists ff_q_pp_ra. d = ff_q_pp_ra * S ((S (i)) * e) + (z))) -> exists fc_u_pp_me fc_v_pp_me. a + m * fc_u_pp_me = z + m * fc_v_pp_me) -> (exists ff_u_pl ff_v_pl. ((((exists ff_h_pl_start. ff_h_pl_start + S (1) = S ((S (0)) * ff_v_pl)) /\ exists ff_q_pl_start. ff_u_pl = ff_q_pl_start * S ((S (0)) * ff_v_pl) + (1))) /\ ((((exists ff_h_pl_terminal. ff_h_pl_terminal + S (n) = S ((S (l)) * ff_v_pl)) /\ exists ff_q_pl_terminal. ff_u_pl = ff_q_pl_terminal * S ((S (l)) * ff_v_pl) + (n))) /\ forall ff_i_pl. (exists ff_lt_pl_bound. ff_lt_pl_bound + S ff_i_pl = l) -> exists ff_p_pl ff_r_pl ff_s_pl. ((((exists ff_h_pl_factor. ff_h_pl_factor + S (ff_p_pl) = S ((S (ff_i_pl)) * c)) /\ exists ff_q_pl_factor. b = ff_q_pl_factor * S ((S (ff_i_pl)) * c) + (ff_p_pl))) /\ ((((exists ff_h_pl_partial. ff_h_pl_partial + S (ff_r_pl) = S ((S (ff_i_pl)) * ff_v_pl)) /\ exists ff_q_pl_partial. ff_u_pl = ff_q_pl_partial * S ((S (ff_i_pl)) * ff_v_pl) + (ff_r_pl))) /\ ((((exists ff_h_pl_successor. ff_h_pl_successor + S (ff_s_pl) = S ((S (S ff_i_pl)) * ff_v_pl)) /\ exists ff_q_pl_successor. ff_u_pl = ff_q_pl_successor * S ((S (S ff_i_pl)) * ff_v_pl) + (ff_s_pl))) /\ ff_s_pl = ff_r_pl * ff_p_pl)))))) -> (exists ff_u_pr ff_v_pr. ((((exists ff_h_pr_start. ff_h_pr_start + S (1) = S ((S (0)) * ff_v_pr)) /\ exists ff_q_pr_start. ff_u_pr = ff_q_pr_start * S ((S (0)) * ff_v_pr) + (1))) /\ ((((exists ff_h_pr_terminal. ff_h_pr_terminal + S (q) = S ((S (l)) * ff_v_pr)) /\ exists ff_q_pr_terminal. ff_u_pr = ff_q_pr_terminal * S ((S (l)) * ff_v_pr) + (q))) /\ forall ff_i_pr. (exists ff_lt_pr_bound. ff_lt_pr_bound + S ff_i_pr = l) -> exists ff_p_pr ff_r_pr ff_s_pr. ((((exists ff_h_pr_factor. ff_h_pr_factor + S (ff_p_pr) = S ((S (ff_i_pr)) * e)) /\ exists ff_q_pr_factor. d = ff_q_pr_factor * S ((S (ff_i_pr)) * e) + (ff_p_pr))) /\ ((((exists ff_h_pr_partial. ff_h_pr_partial + S (ff_r_pr) = S ((S (ff_i_pr)) * ff_v_pr)) /\ exists ff_q_pr_partial. ff_u_pr = ff_q_pr_partial * S ((S (ff_i_pr)) * ff_v_pr) + (ff_r_pr))) /\ ((((exists ff_h_pr_successor. ff_h_pr_successor + S (ff_s_pr) = S ((S (S ff_i_pr)) * ff_v_pr)) /\ exists ff_q_pr_successor. ff_u_pr = ff_q_pr_successor * S ((S (S ff_i_pr)) * ff_v_pr) + (ff_s_pr))) /\ ff_s_pr = ff_r_pr * ff_p_pr)))))) -> exists fc_u_pv fc_v_pv. n + m * fc_u_pv = q + m * fc_v_pv
```

## Dependencies

- [[beta_product_zero]]
- [[beta_product_succ_decompose]]
- [[le_succ]]
- [[le_refl]]
- [[mod_eq_refl]]
- [[mod_eq_mul]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **4129 nodes**, depth **64**.
- Authored script length: **100 commands**.
- Runtime card: `pa lib beta_product_pointwise_mod_congruent`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
