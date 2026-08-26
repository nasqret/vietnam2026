---
title: "Lemma: pow_predecessor_parity_mod"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_predecessor_parity_mod`

Powers of the predecessor of p alternate between one and the predecessor modulo p.

## Closed Peano statement

```text
forall p r e z. p = S r -> (exists ff_b_main ff_c_main. ((forall ff_i_main_repeat. (exists ff_lt_main_repeat_bound. ff_lt_main_repeat_bound + S ff_i_main_repeat = e) -> (((exists ff_h_main_repeat_decoded. ff_h_main_repeat_decoded + S (r) = S ((S (ff_i_main_repeat)) * ff_c_main)) /\ exists ff_q_main_repeat_decoded. ff_b_main = ff_q_main_repeat_decoded * S ((S (ff_i_main_repeat)) * ff_c_main) + (r)))) /\ (exists ff_u_main_product ff_v_main_product. ((((exists ff_h_main_product_start. ff_h_main_product_start + S (1) = S ((S (0)) * ff_v_main_product)) /\ exists ff_q_main_product_start. ff_u_main_product = ff_q_main_product_start * S ((S (0)) * ff_v_main_product) + (1))) /\ ((((exists ff_h_main_product_terminal. ff_h_main_product_terminal + S (z) = S ((S (e)) * ff_v_main_product)) /\ exists ff_q_main_product_terminal. ff_u_main_product = ff_q_main_product_terminal * S ((S (e)) * ff_v_main_product) + (z))) /\ forall ff_i_main_product. (exists ff_lt_main_product_bound. ff_lt_main_product_bound + S ff_i_main_product = e) -> exists ff_p_main_product ff_r_main_product ff_s_main_product. ((((exists ff_h_main_product_factor. ff_h_main_product_factor + S (ff_p_main_product) = S ((S (ff_i_main_product)) * ff_c_main)) /\ exists ff_q_main_product_factor. ff_b_main = ff_q_main_product_factor * S ((S (ff_i_main_product)) * ff_c_main) + (ff_p_main_product))) /\ ((((exists ff_h_main_product_partial. ff_h_main_product_partial + S (ff_r_main_product) = S ((S (ff_i_main_product)) * ff_v_main_product)) /\ exists ff_q_main_product_partial. ff_u_main_product = ff_q_main_product_partial * S ((S (ff_i_main_product)) * ff_v_main_product) + (ff_r_main_product))) /\ ((((exists ff_h_main_product_successor. ff_h_main_product_successor + S (ff_s_main_product) = S ((S (S ff_i_main_product)) * ff_v_main_product)) /\ exists ff_q_main_product_successor. ff_u_main_product = ff_q_main_product_successor * S ((S (S ff_i_main_product)) * ff_v_main_product) + (ff_s_main_product))) /\ ff_s_main_product = ff_r_main_product * ff_p_main_product)))))))) -> (((exists gs_even_main. e = 2 * gs_even_main) -> (exists gs_u_result_even gs_v_result_even. (z) + p * gs_u_result_even = (1) + p * gs_v_result_even)) /\ ((exists gs_odd_main. e = 2 * gs_odd_main + 1) -> (exists gs_u_result_odd gs_v_result_odd. (z) + p * gs_u_result_odd = (r) + p * gs_v_result_odd)))
```

## Dependencies

- [[pow_zero]]
- [[pow_successor_decompose]]
- [[odd_not_even]]
- [[even_successor_to_odd]]
- [[odd_successor_to_even]]
- [[predecessor_square_mod_one]]
- [[mod_eq_refl]]
- [[mod_eq_mul]]
- [[mod_eq_trans]]
- [[one_mul]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **9249 nodes**, depth **67**.
- Authored script length: **107 commands**.
- Runtime card: `pa lib pow_predecessor_parity_mod`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
