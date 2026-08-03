---
title: "Lemma: pow_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_functional`

Relational powers have a unique natural value.

## Closed Peano statement

```text
forall a e n m. (exists ff_b_l ff_c_l. ((forall ff_i_l_repeat. (exists ff_lt_l_repeat_bound. ff_lt_l_repeat_bound + S ff_i_l_repeat = e) -> (((exists ff_h_l_repeat_decoded. ff_h_l_repeat_decoded + S (a) = S ((S (ff_i_l_repeat)) * ff_c_l)) /\ exists ff_q_l_repeat_decoded. ff_b_l = ff_q_l_repeat_decoded * S ((S (ff_i_l_repeat)) * ff_c_l) + (a)))) /\ (exists ff_u_l_product ff_v_l_product. ((((exists ff_h_l_product_start. ff_h_l_product_start + S (1) = S ((S (0)) * ff_v_l_product)) /\ exists ff_q_l_product_start. ff_u_l_product = ff_q_l_product_start * S ((S (0)) * ff_v_l_product) + (1))) /\ ((((exists ff_h_l_product_terminal. ff_h_l_product_terminal + S (n) = S ((S (e)) * ff_v_l_product)) /\ exists ff_q_l_product_terminal. ff_u_l_product = ff_q_l_product_terminal * S ((S (e)) * ff_v_l_product) + (n))) /\ forall ff_i_l_product. (exists ff_lt_l_product_bound. ff_lt_l_product_bound + S ff_i_l_product = e) -> exists ff_p_l_product ff_r_l_product ff_s_l_product. ((((exists ff_h_l_product_factor. ff_h_l_product_factor + S (ff_p_l_product) = S ((S (ff_i_l_product)) * ff_c_l)) /\ exists ff_q_l_product_factor. ff_b_l = ff_q_l_product_factor * S ((S (ff_i_l_product)) * ff_c_l) + (ff_p_l_product))) /\ ((((exists ff_h_l_product_partial. ff_h_l_product_partial + S (ff_r_l_product) = S ((S (ff_i_l_product)) * ff_v_l_product)) /\ exists ff_q_l_product_partial. ff_u_l_product = ff_q_l_product_partial * S ((S (ff_i_l_product)) * ff_v_l_product) + (ff_r_l_product))) /\ ((((exists ff_h_l_product_successor. ff_h_l_product_successor + S (ff_s_l_product) = S ((S (S ff_i_l_product)) * ff_v_l_product)) /\ exists ff_q_l_product_successor. ff_u_l_product = ff_q_l_product_successor * S ((S (S ff_i_l_product)) * ff_v_l_product) + (ff_s_l_product))) /\ ff_s_l_product = ff_r_l_product * ff_p_l_product)))))))) -> (exists ff_b_r ff_c_r. ((forall ff_i_r_repeat. (exists ff_lt_r_repeat_bound. ff_lt_r_repeat_bound + S ff_i_r_repeat = e) -> (((exists ff_h_r_repeat_decoded. ff_h_r_repeat_decoded + S (a) = S ((S (ff_i_r_repeat)) * ff_c_r)) /\ exists ff_q_r_repeat_decoded. ff_b_r = ff_q_r_repeat_decoded * S ((S (ff_i_r_repeat)) * ff_c_r) + (a)))) /\ (exists ff_u_r_product ff_v_r_product. ((((exists ff_h_r_product_start. ff_h_r_product_start + S (1) = S ((S (0)) * ff_v_r_product)) /\ exists ff_q_r_product_start. ff_u_r_product = ff_q_r_product_start * S ((S (0)) * ff_v_r_product) + (1))) /\ ((((exists ff_h_r_product_terminal. ff_h_r_product_terminal + S (m) = S ((S (e)) * ff_v_r_product)) /\ exists ff_q_r_product_terminal. ff_u_r_product = ff_q_r_product_terminal * S ((S (e)) * ff_v_r_product) + (m))) /\ forall ff_i_r_product. (exists ff_lt_r_product_bound. ff_lt_r_product_bound + S ff_i_r_product = e) -> exists ff_p_r_product ff_r_r_product ff_s_r_product. ((((exists ff_h_r_product_factor. ff_h_r_product_factor + S (ff_p_r_product) = S ((S (ff_i_r_product)) * ff_c_r)) /\ exists ff_q_r_product_factor. ff_b_r = ff_q_r_product_factor * S ((S (ff_i_r_product)) * ff_c_r) + (ff_p_r_product))) /\ ((((exists ff_h_r_product_partial. ff_h_r_product_partial + S (ff_r_r_product) = S ((S (ff_i_r_product)) * ff_v_r_product)) /\ exists ff_q_r_product_partial. ff_u_r_product = ff_q_r_product_partial * S ((S (ff_i_r_product)) * ff_v_r_product) + (ff_r_r_product))) /\ ((((exists ff_h_r_product_successor. ff_h_r_product_successor + S (ff_s_r_product) = S ((S (S ff_i_r_product)) * ff_v_r_product)) /\ exists ff_q_r_product_successor. ff_u_r_product = ff_q_r_product_successor * S ((S (S ff_i_r_product)) * ff_v_r_product) + (ff_s_r_product))) /\ ff_s_r_product = ff_r_r_product * ff_p_r_product)))))))) -> n = m
```

## Dependencies

- [[beta_repeat_transport_entry]]
- [[beta_product_transport_prefix]]
- [[beta_product_functional]]

## Checked dependents

- [[pow_successor_pair_mul]]
- [[pow_add]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2705 nodes**, depth **63**.
- Authored script length: **56 commands**.
- Runtime card: `pa lib pow_functional`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
