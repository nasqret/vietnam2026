---
title: "Lemma: pow_mod_congruent"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_mod_congruent`

Balanced-congruent bases have congruent relational powers at every exponent.

## Closed Peano statement

```text
forall m a b e x y. (exists qr_u_base qr_v_base. a + m * qr_u_base = b + m * qr_v_base) -> (exists ff_b_left ff_c_left. ((forall ff_i_left_repeat. (exists ff_lt_left_repeat_bound. ff_lt_left_repeat_bound + S ff_i_left_repeat = e) -> (((exists ff_h_left_repeat_decoded. ff_h_left_repeat_decoded + S (a) = S ((S (ff_i_left_repeat)) * ff_c_left)) /\ exists ff_q_left_repeat_decoded. ff_b_left = ff_q_left_repeat_decoded * S ((S (ff_i_left_repeat)) * ff_c_left) + (a)))) /\ (exists ff_u_left_product ff_v_left_product. ((((exists ff_h_left_product_start. ff_h_left_product_start + S (1) = S ((S (0)) * ff_v_left_product)) /\ exists ff_q_left_product_start. ff_u_left_product = ff_q_left_product_start * S ((S (0)) * ff_v_left_product) + (1))) /\ ((((exists ff_h_left_product_terminal. ff_h_left_product_terminal + S (x) = S ((S (e)) * ff_v_left_product)) /\ exists ff_q_left_product_terminal. ff_u_left_product = ff_q_left_product_terminal * S ((S (e)) * ff_v_left_product) + (x))) /\ forall ff_i_left_product. (exists ff_lt_left_product_bound. ff_lt_left_product_bound + S ff_i_left_product = e) -> exists ff_p_left_product ff_r_left_product ff_s_left_product. ((((exists ff_h_left_product_factor. ff_h_left_product_factor + S (ff_p_left_product) = S ((S (ff_i_left_product)) * ff_c_left)) /\ exists ff_q_left_product_factor. ff_b_left = ff_q_left_product_factor * S ((S (ff_i_left_product)) * ff_c_left) + (ff_p_left_product))) /\ ((((exists ff_h_left_product_partial. ff_h_left_product_partial + S (ff_r_left_product) = S ((S (ff_i_left_product)) * ff_v_left_product)) /\ exists ff_q_left_product_partial. ff_u_left_product = ff_q_left_product_partial * S ((S (ff_i_left_product)) * ff_v_left_product) + (ff_r_left_product))) /\ ((((exists ff_h_left_product_successor. ff_h_left_product_successor + S (ff_s_left_product) = S ((S (S ff_i_left_product)) * ff_v_left_product)) /\ exists ff_q_left_product_successor. ff_u_left_product = ff_q_left_product_successor * S ((S (S ff_i_left_product)) * ff_v_left_product) + (ff_s_left_product))) /\ ff_s_left_product = ff_r_left_product * ff_p_left_product)))))))) -> (exists ff_b_right ff_c_right. ((forall ff_i_right_repeat. (exists ff_lt_right_repeat_bound. ff_lt_right_repeat_bound + S ff_i_right_repeat = e) -> (((exists ff_h_right_repeat_decoded. ff_h_right_repeat_decoded + S (b) = S ((S (ff_i_right_repeat)) * ff_c_right)) /\ exists ff_q_right_repeat_decoded. ff_b_right = ff_q_right_repeat_decoded * S ((S (ff_i_right_repeat)) * ff_c_right) + (b)))) /\ (exists ff_u_right_product ff_v_right_product. ((((exists ff_h_right_product_start. ff_h_right_product_start + S (1) = S ((S (0)) * ff_v_right_product)) /\ exists ff_q_right_product_start. ff_u_right_product = ff_q_right_product_start * S ((S (0)) * ff_v_right_product) + (1))) /\ ((((exists ff_h_right_product_terminal. ff_h_right_product_terminal + S (y) = S ((S (e)) * ff_v_right_product)) /\ exists ff_q_right_product_terminal. ff_u_right_product = ff_q_right_product_terminal * S ((S (e)) * ff_v_right_product) + (y))) /\ forall ff_i_right_product. (exists ff_lt_right_product_bound. ff_lt_right_product_bound + S ff_i_right_product = e) -> exists ff_p_right_product ff_r_right_product ff_s_right_product. ((((exists ff_h_right_product_factor. ff_h_right_product_factor + S (ff_p_right_product) = S ((S (ff_i_right_product)) * ff_c_right)) /\ exists ff_q_right_product_factor. ff_b_right = ff_q_right_product_factor * S ((S (ff_i_right_product)) * ff_c_right) + (ff_p_right_product))) /\ ((((exists ff_h_right_product_partial. ff_h_right_product_partial + S (ff_r_right_product) = S ((S (ff_i_right_product)) * ff_v_right_product)) /\ exists ff_q_right_product_partial. ff_u_right_product = ff_q_right_product_partial * S ((S (ff_i_right_product)) * ff_v_right_product) + (ff_r_right_product))) /\ ((((exists ff_h_right_product_successor. ff_h_right_product_successor + S (ff_s_right_product) = S ((S (S ff_i_right_product)) * ff_v_right_product)) /\ exists ff_q_right_product_successor. ff_u_right_product = ff_q_right_product_successor * S ((S (S ff_i_right_product)) * ff_v_right_product) + (ff_s_right_product))) /\ ff_s_right_product = ff_r_right_product * ff_p_right_product)))))))) -> (exists qr_u_result qr_v_result. x + m * qr_u_result = y + m * qr_v_result)
```

## Dependencies

- [[pow_zero]]
- [[pow_successor_decompose]]
- [[pow_successor_pair_mul]]
- [[mod_eq_refl]]
- [[mod_eq_mul]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **10671 nodes**, depth **68**.
- Authored script length: **92 commands**.
- Runtime card: `pa lib pow_mod_congruent`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
