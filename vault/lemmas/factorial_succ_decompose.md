---
title: "Lemma: factorial_succ_decompose"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factorial_succ_decompose`

A successor factorial is its predecessor factorial times the successor.

## Closed Peano statement

```text
forall n sn z. sn = S n -> (exists ff_b_successor ff_c_successor. ((forall ff_i_successor_range. (exists ff_lt_successor_range_bound. ff_lt_successor_range_bound + S ff_i_successor_range = sn) -> (((exists ff_h_successor_range_decoded. ff_h_successor_range_decoded + S (1 + ff_i_successor_range) = S ((S (ff_i_successor_range)) * ff_c_successor)) /\ exists ff_q_successor_range_decoded. ff_b_successor = ff_q_successor_range_decoded * S ((S (ff_i_successor_range)) * ff_c_successor) + (1 + ff_i_successor_range)))) /\ (exists ff_u_successor_product ff_v_successor_product. ((((exists ff_h_successor_product_start. ff_h_successor_product_start + S (1) = S ((S (0)) * ff_v_successor_product)) /\ exists ff_q_successor_product_start. ff_u_successor_product = ff_q_successor_product_start * S ((S (0)) * ff_v_successor_product) + (1))) /\ ((((exists ff_h_successor_product_terminal. ff_h_successor_product_terminal + S (z) = S ((S (sn)) * ff_v_successor_product)) /\ exists ff_q_successor_product_terminal. ff_u_successor_product = ff_q_successor_product_terminal * S ((S (sn)) * ff_v_successor_product) + (z))) /\ forall ff_i_successor_product. (exists ff_lt_successor_product_bound. ff_lt_successor_product_bound + S ff_i_successor_product = sn) -> exists ff_p_successor_product ff_r_successor_product ff_s_successor_product. ((((exists ff_h_successor_product_factor. ff_h_successor_product_factor + S (ff_p_successor_product) = S ((S (ff_i_successor_product)) * ff_c_successor)) /\ exists ff_q_successor_product_factor. ff_b_successor = ff_q_successor_product_factor * S ((S (ff_i_successor_product)) * ff_c_successor) + (ff_p_successor_product))) /\ ((((exists ff_h_successor_product_partial. ff_h_successor_product_partial + S (ff_r_successor_product) = S ((S (ff_i_successor_product)) * ff_v_successor_product)) /\ exists ff_q_successor_product_partial. ff_u_successor_product = ff_q_successor_product_partial * S ((S (ff_i_successor_product)) * ff_v_successor_product) + (ff_r_successor_product))) /\ ((((exists ff_h_successor_product_successor. ff_h_successor_product_successor + S (ff_s_successor_product) = S ((S (S ff_i_successor_product)) * ff_v_successor_product)) /\ exists ff_q_successor_product_successor. ff_u_successor_product = ff_q_successor_product_successor * S ((S (S ff_i_successor_product)) * ff_v_successor_product) + (ff_s_successor_product))) /\ ff_s_successor_product = ff_r_successor_product * ff_p_successor_product)))))))) -> exists r. (exists ff_b_predecessor ff_c_predecessor. ((forall ff_i_predecessor_range. (exists ff_lt_predecessor_range_bound. ff_lt_predecessor_range_bound + S ff_i_predecessor_range = n) -> (((exists ff_h_predecessor_range_decoded. ff_h_predecessor_range_decoded + S (1 + ff_i_predecessor_range) = S ((S (ff_i_predecessor_range)) * ff_c_predecessor)) /\ exists ff_q_predecessor_range_decoded. ff_b_predecessor = ff_q_predecessor_range_decoded * S ((S (ff_i_predecessor_range)) * ff_c_predecessor) + (1 + ff_i_predecessor_range)))) /\ (exists ff_u_predecessor_product ff_v_predecessor_product. ((((exists ff_h_predecessor_product_start. ff_h_predecessor_product_start + S (1) = S ((S (0)) * ff_v_predecessor_product)) /\ exists ff_q_predecessor_product_start. ff_u_predecessor_product = ff_q_predecessor_product_start * S ((S (0)) * ff_v_predecessor_product) + (1))) /\ ((((exists ff_h_predecessor_product_terminal. ff_h_predecessor_product_terminal + S (r) = S ((S (n)) * ff_v_predecessor_product)) /\ exists ff_q_predecessor_product_terminal. ff_u_predecessor_product = ff_q_predecessor_product_terminal * S ((S (n)) * ff_v_predecessor_product) + (r))) /\ forall ff_i_predecessor_product. (exists ff_lt_predecessor_product_bound. ff_lt_predecessor_product_bound + S ff_i_predecessor_product = n) -> exists ff_p_predecessor_product ff_r_predecessor_product ff_s_predecessor_product. ((((exists ff_h_predecessor_product_factor. ff_h_predecessor_product_factor + S (ff_p_predecessor_product) = S ((S (ff_i_predecessor_product)) * ff_c_predecessor)) /\ exists ff_q_predecessor_product_factor. ff_b_predecessor = ff_q_predecessor_product_factor * S ((S (ff_i_predecessor_product)) * ff_c_predecessor) + (ff_p_predecessor_product))) /\ ((((exists ff_h_predecessor_product_partial. ff_h_predecessor_product_partial + S (ff_r_predecessor_product) = S ((S (ff_i_predecessor_product)) * ff_v_predecessor_product)) /\ exists ff_q_predecessor_product_partial. ff_u_predecessor_product = ff_q_predecessor_product_partial * S ((S (ff_i_predecessor_product)) * ff_v_predecessor_product) + (ff_r_predecessor_product))) /\ ((((exists ff_h_predecessor_product_successor. ff_h_predecessor_product_successor + S (ff_s_predecessor_product) = S ((S (S ff_i_predecessor_product)) * ff_v_predecessor_product)) /\ exists ff_q_predecessor_product_successor. ff_u_predecessor_product = ff_q_predecessor_product_successor * S ((S (S ff_i_predecessor_product)) * ff_v_predecessor_product) + (ff_s_predecessor_product))) /\ ff_s_predecessor_product = ff_r_predecessor_product * ff_p_predecessor_product)))))))) /\ z = r * S n
```

## Dependencies

- [[beta_product_succ_decompose]]
- [[beta_range_entry_eq]]
- [[le_refl]]
- [[le_succ]]
- [[add_succ_left]]
- [[zero_add]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2594 nodes**, depth **63**.
- Authored script length: **60 commands**.
- Runtime card: `pa lib factorial_succ_decompose`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
