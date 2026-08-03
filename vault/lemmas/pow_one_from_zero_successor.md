---
title: "Lemma: pow_one_from_zero_successor"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_one_from_zero_successor`

A successor of a zero exponent gives the relational first power.

## Closed Peano statement

```text
forall a z e n. z = 0 -> e = S z -> (exists ff_b_one_carrier ff_c_one_carrier. ((forall ff_i_one_carrier_repeat. (exists ff_lt_one_carrier_repeat_bound. ff_lt_one_carrier_repeat_bound + S ff_i_one_carrier_repeat = e) -> (((exists ff_h_one_carrier_repeat_decoded. ff_h_one_carrier_repeat_decoded + S (a) = S ((S (ff_i_one_carrier_repeat)) * ff_c_one_carrier)) /\ exists ff_q_one_carrier_repeat_decoded. ff_b_one_carrier = ff_q_one_carrier_repeat_decoded * S ((S (ff_i_one_carrier_repeat)) * ff_c_one_carrier) + (a)))) /\ (exists ff_u_one_carrier_product ff_v_one_carrier_product. ((((exists ff_h_one_carrier_product_start. ff_h_one_carrier_product_start + S (1) = S ((S (0)) * ff_v_one_carrier_product)) /\ exists ff_q_one_carrier_product_start. ff_u_one_carrier_product = ff_q_one_carrier_product_start * S ((S (0)) * ff_v_one_carrier_product) + (1))) /\ ((((exists ff_h_one_carrier_product_terminal. ff_h_one_carrier_product_terminal + S (n) = S ((S (e)) * ff_v_one_carrier_product)) /\ exists ff_q_one_carrier_product_terminal. ff_u_one_carrier_product = ff_q_one_carrier_product_terminal * S ((S (e)) * ff_v_one_carrier_product) + (n))) /\ forall ff_i_one_carrier_product. (exists ff_lt_one_carrier_product_bound. ff_lt_one_carrier_product_bound + S ff_i_one_carrier_product = e) -> exists ff_p_one_carrier_product ff_r_one_carrier_product ff_s_one_carrier_product. ((((exists ff_h_one_carrier_product_factor. ff_h_one_carrier_product_factor + S (ff_p_one_carrier_product) = S ((S (ff_i_one_carrier_product)) * ff_c_one_carrier)) /\ exists ff_q_one_carrier_product_factor. ff_b_one_carrier = ff_q_one_carrier_product_factor * S ((S (ff_i_one_carrier_product)) * ff_c_one_carrier) + (ff_p_one_carrier_product))) /\ ((((exists ff_h_one_carrier_product_partial. ff_h_one_carrier_product_partial + S (ff_r_one_carrier_product) = S ((S (ff_i_one_carrier_product)) * ff_v_one_carrier_product)) /\ exists ff_q_one_carrier_product_partial. ff_u_one_carrier_product = ff_q_one_carrier_product_partial * S ((S (ff_i_one_carrier_product)) * ff_v_one_carrier_product) + (ff_r_one_carrier_product))) /\ ((((exists ff_h_one_carrier_product_successor. ff_h_one_carrier_product_successor + S (ff_s_one_carrier_product) = S ((S (S ff_i_one_carrier_product)) * ff_v_one_carrier_product)) /\ exists ff_q_one_carrier_product_successor. ff_u_one_carrier_product = ff_q_one_carrier_product_successor * S ((S (S ff_i_one_carrier_product)) * ff_v_one_carrier_product) + (ff_s_one_carrier_product))) /\ ff_s_one_carrier_product = ff_r_one_carrier_product * ff_p_one_carrier_product)))))))) -> n = a
```

## Dependencies

- [[pow_successor_decompose]]
- [[pow_zero]]
- [[one_mul]]

## Checked dependents

- [[pow_one]]

## Verification record

- Independently checked from the empty context.
- Certificate: **3827 nodes**, depth **64**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib pow_one_from_zero_successor`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
