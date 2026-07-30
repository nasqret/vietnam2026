---
title: "Lemma: pow_two_from_one_successor"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `pow_two_from_one_successor`

A successor of exponent one gives the relational square.

## Closed Peano statement

```text
forall a o e n. o = 1 -> e = S o -> (exists ff_b_two_carrier ff_c_two_carrier. ((forall ff_i_two_carrier_repeat. (exists ff_lt_two_carrier_repeat_bound. ff_lt_two_carrier_repeat_bound + S ff_i_two_carrier_repeat = e) -> (((exists ff_h_two_carrier_repeat_decoded. ff_h_two_carrier_repeat_decoded + S (a) = S ((S (ff_i_two_carrier_repeat)) * ff_c_two_carrier)) /\ exists ff_q_two_carrier_repeat_decoded. ff_b_two_carrier = ff_q_two_carrier_repeat_decoded * S ((S (ff_i_two_carrier_repeat)) * ff_c_two_carrier) + (a)))) /\ (exists ff_u_two_carrier_product ff_v_two_carrier_product. ((((exists ff_h_two_carrier_product_start. ff_h_two_carrier_product_start + S (1) = S ((S (0)) * ff_v_two_carrier_product)) /\ exists ff_q_two_carrier_product_start. ff_u_two_carrier_product = ff_q_two_carrier_product_start * S ((S (0)) * ff_v_two_carrier_product) + (1))) /\ ((((exists ff_h_two_carrier_product_terminal. ff_h_two_carrier_product_terminal + S (n) = S ((S (e)) * ff_v_two_carrier_product)) /\ exists ff_q_two_carrier_product_terminal. ff_u_two_carrier_product = ff_q_two_carrier_product_terminal * S ((S (e)) * ff_v_two_carrier_product) + (n))) /\ forall ff_i_two_carrier_product. (exists ff_lt_two_carrier_product_bound. ff_lt_two_carrier_product_bound + S ff_i_two_carrier_product = e) -> exists ff_p_two_carrier_product ff_r_two_carrier_product ff_s_two_carrier_product. ((((exists ff_h_two_carrier_product_factor. ff_h_two_carrier_product_factor + S (ff_p_two_carrier_product) = S ((S (ff_i_two_carrier_product)) * ff_c_two_carrier)) /\ exists ff_q_two_carrier_product_factor. ff_b_two_carrier = ff_q_two_carrier_product_factor * S ((S (ff_i_two_carrier_product)) * ff_c_two_carrier) + (ff_p_two_carrier_product))) /\ ((((exists ff_h_two_carrier_product_partial. ff_h_two_carrier_product_partial + S (ff_r_two_carrier_product) = S ((S (ff_i_two_carrier_product)) * ff_v_two_carrier_product)) /\ exists ff_q_two_carrier_product_partial. ff_u_two_carrier_product = ff_q_two_carrier_product_partial * S ((S (ff_i_two_carrier_product)) * ff_v_two_carrier_product) + (ff_r_two_carrier_product))) /\ ((((exists ff_h_two_carrier_product_successor. ff_h_two_carrier_product_successor + S (ff_s_two_carrier_product) = S ((S (S ff_i_two_carrier_product)) * ff_v_two_carrier_product)) /\ exists ff_q_two_carrier_product_successor. ff_u_two_carrier_product = ff_q_two_carrier_product_successor * S ((S (S ff_i_two_carrier_product)) * ff_v_two_carrier_product) + (ff_s_two_carrier_product))) /\ ff_s_two_carrier_product = ff_r_two_carrier_product * ff_p_two_carrier_product)))))))) -> n = a * a
```

## Dependencies

- [[pow_successor_decompose]]
- [[pow_one]]

## Checked dependents

- [[pow_two]]

## Verification record

- Independently checked from the empty context.
- Certificate: **6431 nodes**, depth **67**.
- Authored script length: **28 commands**.
- Runtime card: `pa lib pow_two_from_one_successor`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
