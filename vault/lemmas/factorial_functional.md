---
title: "Lemma: factorial_functional"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factorial_functional`

The beta-coded relational factorial has a unique value.

## Closed Peano statement

```text
forall n z w. (exists ff_b_functional_l ff_c_functional_l. ((forall ff_i_functional_l_range. (exists ff_lt_functional_l_range_bound. ff_lt_functional_l_range_bound + S ff_i_functional_l_range = n) -> (((exists ff_h_functional_l_range_decoded. ff_h_functional_l_range_decoded + S (1 + ff_i_functional_l_range) = S ((S (ff_i_functional_l_range)) * ff_c_functional_l)) /\ exists ff_q_functional_l_range_decoded. ff_b_functional_l = ff_q_functional_l_range_decoded * S ((S (ff_i_functional_l_range)) * ff_c_functional_l) + (1 + ff_i_functional_l_range)))) /\ (exists ff_u_functional_l_product ff_v_functional_l_product. ((((exists ff_h_functional_l_product_start. ff_h_functional_l_product_start + S (1) = S ((S (0)) * ff_v_functional_l_product)) /\ exists ff_q_functional_l_product_start. ff_u_functional_l_product = ff_q_functional_l_product_start * S ((S (0)) * ff_v_functional_l_product) + (1))) /\ ((((exists ff_h_functional_l_product_terminal. ff_h_functional_l_product_terminal + S (z) = S ((S (n)) * ff_v_functional_l_product)) /\ exists ff_q_functional_l_product_terminal. ff_u_functional_l_product = ff_q_functional_l_product_terminal * S ((S (n)) * ff_v_functional_l_product) + (z))) /\ forall ff_i_functional_l_product. (exists ff_lt_functional_l_product_bound. ff_lt_functional_l_product_bound + S ff_i_functional_l_product = n) -> exists ff_p_functional_l_product ff_r_functional_l_product ff_s_functional_l_product. ((((exists ff_h_functional_l_product_factor. ff_h_functional_l_product_factor + S (ff_p_functional_l_product) = S ((S (ff_i_functional_l_product)) * ff_c_functional_l)) /\ exists ff_q_functional_l_product_factor. ff_b_functional_l = ff_q_functional_l_product_factor * S ((S (ff_i_functional_l_product)) * ff_c_functional_l) + (ff_p_functional_l_product))) /\ ((((exists ff_h_functional_l_product_partial. ff_h_functional_l_product_partial + S (ff_r_functional_l_product) = S ((S (ff_i_functional_l_product)) * ff_v_functional_l_product)) /\ exists ff_q_functional_l_product_partial. ff_u_functional_l_product = ff_q_functional_l_product_partial * S ((S (ff_i_functional_l_product)) * ff_v_functional_l_product) + (ff_r_functional_l_product))) /\ ((((exists ff_h_functional_l_product_successor. ff_h_functional_l_product_successor + S (ff_s_functional_l_product) = S ((S (S ff_i_functional_l_product)) * ff_v_functional_l_product)) /\ exists ff_q_functional_l_product_successor. ff_u_functional_l_product = ff_q_functional_l_product_successor * S ((S (S ff_i_functional_l_product)) * ff_v_functional_l_product) + (ff_s_functional_l_product))) /\ ff_s_functional_l_product = ff_r_functional_l_product * ff_p_functional_l_product)))))))) -> (exists ff_b_functional_r ff_c_functional_r. ((forall ff_i_functional_r_range. (exists ff_lt_functional_r_range_bound. ff_lt_functional_r_range_bound + S ff_i_functional_r_range = n) -> (((exists ff_h_functional_r_range_decoded. ff_h_functional_r_range_decoded + S (1 + ff_i_functional_r_range) = S ((S (ff_i_functional_r_range)) * ff_c_functional_r)) /\ exists ff_q_functional_r_range_decoded. ff_b_functional_r = ff_q_functional_r_range_decoded * S ((S (ff_i_functional_r_range)) * ff_c_functional_r) + (1 + ff_i_functional_r_range)))) /\ (exists ff_u_functional_r_product ff_v_functional_r_product. ((((exists ff_h_functional_r_product_start. ff_h_functional_r_product_start + S (1) = S ((S (0)) * ff_v_functional_r_product)) /\ exists ff_q_functional_r_product_start. ff_u_functional_r_product = ff_q_functional_r_product_start * S ((S (0)) * ff_v_functional_r_product) + (1))) /\ ((((exists ff_h_functional_r_product_terminal. ff_h_functional_r_product_terminal + S (w) = S ((S (n)) * ff_v_functional_r_product)) /\ exists ff_q_functional_r_product_terminal. ff_u_functional_r_product = ff_q_functional_r_product_terminal * S ((S (n)) * ff_v_functional_r_product) + (w))) /\ forall ff_i_functional_r_product. (exists ff_lt_functional_r_product_bound. ff_lt_functional_r_product_bound + S ff_i_functional_r_product = n) -> exists ff_p_functional_r_product ff_r_functional_r_product ff_s_functional_r_product. ((((exists ff_h_functional_r_product_factor. ff_h_functional_r_product_factor + S (ff_p_functional_r_product) = S ((S (ff_i_functional_r_product)) * ff_c_functional_r)) /\ exists ff_q_functional_r_product_factor. ff_b_functional_r = ff_q_functional_r_product_factor * S ((S (ff_i_functional_r_product)) * ff_c_functional_r) + (ff_p_functional_r_product))) /\ ((((exists ff_h_functional_r_product_partial. ff_h_functional_r_product_partial + S (ff_r_functional_r_product) = S ((S (ff_i_functional_r_product)) * ff_v_functional_r_product)) /\ exists ff_q_functional_r_product_partial. ff_u_functional_r_product = ff_q_functional_r_product_partial * S ((S (ff_i_functional_r_product)) * ff_v_functional_r_product) + (ff_r_functional_r_product))) /\ ((((exists ff_h_functional_r_product_successor. ff_h_functional_r_product_successor + S (ff_s_functional_r_product) = S ((S (S ff_i_functional_r_product)) * ff_v_functional_r_product)) /\ exists ff_q_functional_r_product_successor. ff_u_functional_r_product = ff_q_functional_r_product_successor * S ((S (S ff_i_functional_r_product)) * ff_v_functional_r_product) + (ff_s_functional_r_product))) /\ ff_s_functional_r_product = ff_r_functional_r_product * ff_p_functional_r_product)))))))) -> z = w
```

## Dependencies

- [[beta_range_transport_entry]]
- [[beta_product_transport_prefix]]
- [[beta_product_functional]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **2704 nodes**, depth **63**.
- Authored script length: **55 commands**.
- Runtime card: `pa lib factorial_functional`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
