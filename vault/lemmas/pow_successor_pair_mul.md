---
title: "Lemma: pow_successor_pair_mul"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_successor_pair_mul`

A successor power paired with its predecessor equals predecessor times base.

## Closed Peano statement

```text
forall a e se r n. se = S e -> (exists ff_b_pair_predecessor ff_c_pair_predecessor. ((forall ff_i_pair_predecessor_repeat. (exists ff_lt_pair_predecessor_repeat_bound. ff_lt_pair_predecessor_repeat_bound + S ff_i_pair_predecessor_repeat = e) -> (((exists ff_h_pair_predecessor_repeat_decoded. ff_h_pair_predecessor_repeat_decoded + S (a) = S ((S (ff_i_pair_predecessor_repeat)) * ff_c_pair_predecessor)) /\ exists ff_q_pair_predecessor_repeat_decoded. ff_b_pair_predecessor = ff_q_pair_predecessor_repeat_decoded * S ((S (ff_i_pair_predecessor_repeat)) * ff_c_pair_predecessor) + (a)))) /\ (exists ff_u_pair_predecessor_product ff_v_pair_predecessor_product. ((((exists ff_h_pair_predecessor_product_start. ff_h_pair_predecessor_product_start + S (1) = S ((S (0)) * ff_v_pair_predecessor_product)) /\ exists ff_q_pair_predecessor_product_start. ff_u_pair_predecessor_product = ff_q_pair_predecessor_product_start * S ((S (0)) * ff_v_pair_predecessor_product) + (1))) /\ ((((exists ff_h_pair_predecessor_product_terminal. ff_h_pair_predecessor_product_terminal + S (r) = S ((S (e)) * ff_v_pair_predecessor_product)) /\ exists ff_q_pair_predecessor_product_terminal. ff_u_pair_predecessor_product = ff_q_pair_predecessor_product_terminal * S ((S (e)) * ff_v_pair_predecessor_product) + (r))) /\ forall ff_i_pair_predecessor_product. (exists ff_lt_pair_predecessor_product_bound. ff_lt_pair_predecessor_product_bound + S ff_i_pair_predecessor_product = e) -> exists ff_p_pair_predecessor_product ff_r_pair_predecessor_product ff_s_pair_predecessor_product. ((((exists ff_h_pair_predecessor_product_factor. ff_h_pair_predecessor_product_factor + S (ff_p_pair_predecessor_product) = S ((S (ff_i_pair_predecessor_product)) * ff_c_pair_predecessor)) /\ exists ff_q_pair_predecessor_product_factor. ff_b_pair_predecessor = ff_q_pair_predecessor_product_factor * S ((S (ff_i_pair_predecessor_product)) * ff_c_pair_predecessor) + (ff_p_pair_predecessor_product))) /\ ((((exists ff_h_pair_predecessor_product_partial. ff_h_pair_predecessor_product_partial + S (ff_r_pair_predecessor_product) = S ((S (ff_i_pair_predecessor_product)) * ff_v_pair_predecessor_product)) /\ exists ff_q_pair_predecessor_product_partial. ff_u_pair_predecessor_product = ff_q_pair_predecessor_product_partial * S ((S (ff_i_pair_predecessor_product)) * ff_v_pair_predecessor_product) + (ff_r_pair_predecessor_product))) /\ ((((exists ff_h_pair_predecessor_product_successor. ff_h_pair_predecessor_product_successor + S (ff_s_pair_predecessor_product) = S ((S (S ff_i_pair_predecessor_product)) * ff_v_pair_predecessor_product)) /\ exists ff_q_pair_predecessor_product_successor. ff_u_pair_predecessor_product = ff_q_pair_predecessor_product_successor * S ((S (S ff_i_pair_predecessor_product)) * ff_v_pair_predecessor_product) + (ff_s_pair_predecessor_product))) /\ ff_s_pair_predecessor_product = ff_r_pair_predecessor_product * ff_p_pair_predecessor_product)))))))) -> (exists ff_b_pair_successor ff_c_pair_successor. ((forall ff_i_pair_successor_repeat. (exists ff_lt_pair_successor_repeat_bound. ff_lt_pair_successor_repeat_bound + S ff_i_pair_successor_repeat = se) -> (((exists ff_h_pair_successor_repeat_decoded. ff_h_pair_successor_repeat_decoded + S (a) = S ((S (ff_i_pair_successor_repeat)) * ff_c_pair_successor)) /\ exists ff_q_pair_successor_repeat_decoded. ff_b_pair_successor = ff_q_pair_successor_repeat_decoded * S ((S (ff_i_pair_successor_repeat)) * ff_c_pair_successor) + (a)))) /\ (exists ff_u_pair_successor_product ff_v_pair_successor_product. ((((exists ff_h_pair_successor_product_start. ff_h_pair_successor_product_start + S (1) = S ((S (0)) * ff_v_pair_successor_product)) /\ exists ff_q_pair_successor_product_start. ff_u_pair_successor_product = ff_q_pair_successor_product_start * S ((S (0)) * ff_v_pair_successor_product) + (1))) /\ ((((exists ff_h_pair_successor_product_terminal. ff_h_pair_successor_product_terminal + S (n) = S ((S (se)) * ff_v_pair_successor_product)) /\ exists ff_q_pair_successor_product_terminal. ff_u_pair_successor_product = ff_q_pair_successor_product_terminal * S ((S (se)) * ff_v_pair_successor_product) + (n))) /\ forall ff_i_pair_successor_product. (exists ff_lt_pair_successor_product_bound. ff_lt_pair_successor_product_bound + S ff_i_pair_successor_product = se) -> exists ff_p_pair_successor_product ff_r_pair_successor_product ff_s_pair_successor_product. ((((exists ff_h_pair_successor_product_factor. ff_h_pair_successor_product_factor + S (ff_p_pair_successor_product) = S ((S (ff_i_pair_successor_product)) * ff_c_pair_successor)) /\ exists ff_q_pair_successor_product_factor. ff_b_pair_successor = ff_q_pair_successor_product_factor * S ((S (ff_i_pair_successor_product)) * ff_c_pair_successor) + (ff_p_pair_successor_product))) /\ ((((exists ff_h_pair_successor_product_partial. ff_h_pair_successor_product_partial + S (ff_r_pair_successor_product) = S ((S (ff_i_pair_successor_product)) * ff_v_pair_successor_product)) /\ exists ff_q_pair_successor_product_partial. ff_u_pair_successor_product = ff_q_pair_successor_product_partial * S ((S (ff_i_pair_successor_product)) * ff_v_pair_successor_product) + (ff_r_pair_successor_product))) /\ ((((exists ff_h_pair_successor_product_successor. ff_h_pair_successor_product_successor + S (ff_s_pair_successor_product) = S ((S (S ff_i_pair_successor_product)) * ff_v_pair_successor_product)) /\ exists ff_q_pair_successor_product_successor. ff_u_pair_successor_product = ff_q_pair_successor_product_successor * S ((S (S ff_i_pair_successor_product)) * ff_v_pair_successor_product) + (ff_s_pair_successor_product))) /\ ff_s_pair_successor_product = ff_r_pair_successor_product * ff_p_pair_successor_product)))))))) -> n = r * a
```

## Dependencies

- [[pow_successor_decompose]]
- [[pow_functional]]

## Checked dependents

- [[pow_mod_congruent]]

## Verification record

- Independently checked from the empty context.
- Certificate: **5282 nodes**, depth **65**.
- Authored script length: **30 commands**.
- Runtime card: `pa lib pow_successor_pair_mul`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
