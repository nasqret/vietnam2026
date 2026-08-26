---
title: "Lemma: pow_zero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_zero`

The relational zeroth power is one.

## Closed Peano statement

```text
forall a e n. e = 0 -> (exists ff_b_z ff_c_z. ((forall ff_i_z_repeat. (exists ff_lt_z_repeat_bound. ff_lt_z_repeat_bound + S ff_i_z_repeat = e) -> (((exists ff_h_z_repeat_decoded. ff_h_z_repeat_decoded + S (a) = S ((S (ff_i_z_repeat)) * ff_c_z)) /\ exists ff_q_z_repeat_decoded. ff_b_z = ff_q_z_repeat_decoded * S ((S (ff_i_z_repeat)) * ff_c_z) + (a)))) /\ (exists ff_u_z_product ff_v_z_product. ((((exists ff_h_z_product_start. ff_h_z_product_start + S (1) = S ((S (0)) * ff_v_z_product)) /\ exists ff_q_z_product_start. ff_u_z_product = ff_q_z_product_start * S ((S (0)) * ff_v_z_product) + (1))) /\ ((((exists ff_h_z_product_terminal. ff_h_z_product_terminal + S (n) = S ((S (e)) * ff_v_z_product)) /\ exists ff_q_z_product_terminal. ff_u_z_product = ff_q_z_product_terminal * S ((S (e)) * ff_v_z_product) + (n))) /\ forall ff_i_z_product. (exists ff_lt_z_product_bound. ff_lt_z_product_bound + S ff_i_z_product = e) -> exists ff_p_z_product ff_r_z_product ff_s_z_product. ((((exists ff_h_z_product_factor. ff_h_z_product_factor + S (ff_p_z_product) = S ((S (ff_i_z_product)) * ff_c_z)) /\ exists ff_q_z_product_factor. ff_b_z = ff_q_z_product_factor * S ((S (ff_i_z_product)) * ff_c_z) + (ff_p_z_product))) /\ ((((exists ff_h_z_product_partial. ff_h_z_product_partial + S (ff_r_z_product) = S ((S (ff_i_z_product)) * ff_v_z_product)) /\ exists ff_q_z_product_partial. ff_u_z_product = ff_q_z_product_partial * S ((S (ff_i_z_product)) * ff_v_z_product) + (ff_r_z_product))) /\ ((((exists ff_h_z_product_successor. ff_h_z_product_successor + S (ff_s_z_product) = S ((S (S ff_i_z_product)) * ff_v_z_product)) /\ exists ff_q_z_product_successor. ff_u_z_product = ff_q_z_product_successor * S ((S (S ff_i_z_product)) * ff_v_z_product) + (ff_s_z_product))) /\ ff_s_z_product = ff_r_z_product * ff_p_z_product)))))))) -> n = 1
```

## Dependencies

- [[beta_product_zero]]

## Checked dependents

- [[pow_one_from_zero_successor]]
- [[pow_mod_congruent]]
- [[pow_add]]
- [[pow_mul_exp]]
- [[pow_predecessor_parity_mod]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1224 nodes**, depth **61**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib pow_zero`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
