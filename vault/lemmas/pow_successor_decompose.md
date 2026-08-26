---
title: "Lemma: pow_successor_decompose"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_successor_decompose`

A successor relational power is its predecessor power times the base.

## Closed Peano statement

```text
forall a e se n. se = S e -> (exists ff_b_s ff_c_s. ((forall ff_i_s_repeat. (exists ff_lt_s_repeat_bound. ff_lt_s_repeat_bound + S ff_i_s_repeat = se) -> (((exists ff_h_s_repeat_decoded. ff_h_s_repeat_decoded + S (a) = S ((S (ff_i_s_repeat)) * ff_c_s)) /\ exists ff_q_s_repeat_decoded. ff_b_s = ff_q_s_repeat_decoded * S ((S (ff_i_s_repeat)) * ff_c_s) + (a)))) /\ (exists ff_u_s_product ff_v_s_product. ((((exists ff_h_s_product_start. ff_h_s_product_start + S (1) = S ((S (0)) * ff_v_s_product)) /\ exists ff_q_s_product_start. ff_u_s_product = ff_q_s_product_start * S ((S (0)) * ff_v_s_product) + (1))) /\ ((((exists ff_h_s_product_terminal. ff_h_s_product_terminal + S (n) = S ((S (se)) * ff_v_s_product)) /\ exists ff_q_s_product_terminal. ff_u_s_product = ff_q_s_product_terminal * S ((S (se)) * ff_v_s_product) + (n))) /\ forall ff_i_s_product. (exists ff_lt_s_product_bound. ff_lt_s_product_bound + S ff_i_s_product = se) -> exists ff_p_s_product ff_r_s_product ff_s_s_product. ((((exists ff_h_s_product_factor. ff_h_s_product_factor + S (ff_p_s_product) = S ((S (ff_i_s_product)) * ff_c_s)) /\ exists ff_q_s_product_factor. ff_b_s = ff_q_s_product_factor * S ((S (ff_i_s_product)) * ff_c_s) + (ff_p_s_product))) /\ ((((exists ff_h_s_product_partial. ff_h_s_product_partial + S (ff_r_s_product) = S ((S (ff_i_s_product)) * ff_v_s_product)) /\ exists ff_q_s_product_partial. ff_u_s_product = ff_q_s_product_partial * S ((S (ff_i_s_product)) * ff_v_s_product) + (ff_r_s_product))) /\ ((((exists ff_h_s_product_successor. ff_h_s_product_successor + S (ff_s_s_product) = S ((S (S ff_i_s_product)) * ff_v_s_product)) /\ exists ff_q_s_product_successor. ff_u_s_product = ff_q_s_product_successor * S ((S (S ff_i_s_product)) * ff_v_s_product) + (ff_s_s_product))) /\ ff_s_s_product = ff_r_s_product * ff_p_s_product)))))))) -> exists r. (exists ff_b_p ff_c_p. ((forall ff_i_p_repeat. (exists ff_lt_p_repeat_bound. ff_lt_p_repeat_bound + S ff_i_p_repeat = e) -> (((exists ff_h_p_repeat_decoded. ff_h_p_repeat_decoded + S (a) = S ((S (ff_i_p_repeat)) * ff_c_p)) /\ exists ff_q_p_repeat_decoded. ff_b_p = ff_q_p_repeat_decoded * S ((S (ff_i_p_repeat)) * ff_c_p) + (a)))) /\ (exists ff_u_p_product ff_v_p_product. ((((exists ff_h_p_product_start. ff_h_p_product_start + S (1) = S ((S (0)) * ff_v_p_product)) /\ exists ff_q_p_product_start. ff_u_p_product = ff_q_p_product_start * S ((S (0)) * ff_v_p_product) + (1))) /\ ((((exists ff_h_p_product_terminal. ff_h_p_product_terminal + S (r) = S ((S (e)) * ff_v_p_product)) /\ exists ff_q_p_product_terminal. ff_u_p_product = ff_q_p_product_terminal * S ((S (e)) * ff_v_p_product) + (r))) /\ forall ff_i_p_product. (exists ff_lt_p_product_bound. ff_lt_p_product_bound + S ff_i_p_product = e) -> exists ff_p_p_product ff_r_p_product ff_s_p_product. ((((exists ff_h_p_product_factor. ff_h_p_product_factor + S (ff_p_p_product) = S ((S (ff_i_p_product)) * ff_c_p)) /\ exists ff_q_p_product_factor. ff_b_p = ff_q_p_product_factor * S ((S (ff_i_p_product)) * ff_c_p) + (ff_p_p_product))) /\ ((((exists ff_h_p_product_partial. ff_h_p_product_partial + S (ff_r_p_product) = S ((S (ff_i_p_product)) * ff_v_p_product)) /\ exists ff_q_p_product_partial. ff_u_p_product = ff_q_p_product_partial * S ((S (ff_i_p_product)) * ff_v_p_product) + (ff_r_p_product))) /\ ((((exists ff_h_p_product_successor. ff_h_p_product_successor + S (ff_s_p_product) = S ((S (S ff_i_p_product)) * ff_v_p_product)) /\ exists ff_q_p_product_successor. ff_u_p_product = ff_q_p_product_successor * S ((S (S ff_i_p_product)) * ff_v_p_product) + (ff_s_p_product))) /\ ff_s_p_product = ff_r_p_product * ff_p_p_product)))))))) /\ n = r * a
```

## Dependencies

- [[beta_product_succ_decompose]]
- [[beta_repeat_entry_eq]]
- [[le_refl]]
- [[le_succ]]

## Checked dependents

- [[pow_one_from_zero_successor]]
- [[pow_successor_pair_mul]]
- [[pow_mod_congruent]]
- [[pow_two_from_one_successor]]
- [[pow_add]]
- [[pow_mul_exp]]
- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2541 nodes**, depth **63**.
- Authored script length: **54 commands**.
- Runtime card: `pa lib pow_successor_decompose`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
