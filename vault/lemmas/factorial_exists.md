---
title: "Lemma: factorial_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `factorial_exists`

Every natural has a beta-coded relational factorial value.

## Closed Peano statement

```text
forall n. exists z. (exists ff_b_exists ff_c_exists. ((forall ff_i_exists_range. (exists ff_lt_exists_range_bound. ff_lt_exists_range_bound + S ff_i_exists_range = n) -> (((exists ff_h_exists_range_decoded. ff_h_exists_range_decoded + S (1 + ff_i_exists_range) = S ((S (ff_i_exists_range)) * ff_c_exists)) /\ exists ff_q_exists_range_decoded. ff_b_exists = ff_q_exists_range_decoded * S ((S (ff_i_exists_range)) * ff_c_exists) + (1 + ff_i_exists_range)))) /\ (exists ff_u_exists_product ff_v_exists_product. ((((exists ff_h_exists_product_start. ff_h_exists_product_start + S (1) = S ((S (0)) * ff_v_exists_product)) /\ exists ff_q_exists_product_start. ff_u_exists_product = ff_q_exists_product_start * S ((S (0)) * ff_v_exists_product) + (1))) /\ ((((exists ff_h_exists_product_terminal. ff_h_exists_product_terminal + S (z) = S ((S (n)) * ff_v_exists_product)) /\ exists ff_q_exists_product_terminal. ff_u_exists_product = ff_q_exists_product_terminal * S ((S (n)) * ff_v_exists_product) + (z))) /\ forall ff_i_exists_product. (exists ff_lt_exists_product_bound. ff_lt_exists_product_bound + S ff_i_exists_product = n) -> exists ff_p_exists_product ff_r_exists_product ff_s_exists_product. ((((exists ff_h_exists_product_factor. ff_h_exists_product_factor + S (ff_p_exists_product) = S ((S (ff_i_exists_product)) * ff_c_exists)) /\ exists ff_q_exists_product_factor. ff_b_exists = ff_q_exists_product_factor * S ((S (ff_i_exists_product)) * ff_c_exists) + (ff_p_exists_product))) /\ ((((exists ff_h_exists_product_partial. ff_h_exists_product_partial + S (ff_r_exists_product) = S ((S (ff_i_exists_product)) * ff_v_exists_product)) /\ exists ff_q_exists_product_partial. ff_u_exists_product = ff_q_exists_product_partial * S ((S (ff_i_exists_product)) * ff_v_exists_product) + (ff_r_exists_product))) /\ ((((exists ff_h_exists_product_successor. ff_h_exists_product_successor + S (ff_s_exists_product) = S ((S (S ff_i_exists_product)) * ff_v_exists_product)) /\ exists ff_q_exists_product_successor. ff_u_exists_product = ff_q_exists_product_successor * S ((S (S ff_i_exists_product)) * ff_v_exists_product) + (ff_s_exists_product))) /\ ff_s_exists_product = ff_r_exists_product * ff_p_exists_product))))))))
```

## Dependencies

- [[beta_range_exists]]
- [[beta_product_exists]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **59841 nodes**, depth **88**.
- Authored script length: **21 commands**.
- Runtime card: `pa lib factorial_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
