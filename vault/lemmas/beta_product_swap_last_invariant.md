---
title: "Lemma: beta_product_swap_last_invariant"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_product_swap_last_invariant`

Swapping an interior beta-coded factor with the last factor preserves the exact finite product.

## Closed Peano statement

```text
forall b c z d n i x y p q. (exists h. h + S i = n) -> (((exists ff_h_product_swap_old_i. ff_h_product_swap_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_product_swap_old_i. b = ff_q_product_swap_old_i * S ((S (i)) * c) + (x))) -> (((exists ff_h_product_swap_old_n. ff_h_product_swap_old_n + S (y) = S ((S (n)) * c)) /\ exists ff_q_product_swap_old_n. b = ff_q_product_swap_old_n * S ((S (n)) * c) + (y))) -> (((exists ff_h_product_swap_new_i. ff_h_product_swap_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_product_swap_new_i. z = ff_q_product_swap_new_i * S ((S (i)) * d) + (y))) -> (((exists ff_h_product_swap_new_n. ff_h_product_swap_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_product_swap_new_n. z = ff_q_product_swap_new_n * S ((S (n)) * d) + (x))) -> (forall j a. (exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> (((exists ff_h_product_swap_old_j. ff_h_product_swap_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_product_swap_old_j. b = ff_q_product_swap_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_product_swap_new_j. ff_h_product_swap_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_product_swap_new_j. z = ff_q_product_swap_new_j * S ((S (j)) * d) + (a)))) -> (exists ff_u_product_swap_old ff_v_product_swap_old. ((((exists ff_h_product_swap_old_start. ff_h_product_swap_old_start + S (1) = S ((S (0)) * ff_v_product_swap_old)) /\ exists ff_q_product_swap_old_start. ff_u_product_swap_old = ff_q_product_swap_old_start * S ((S (0)) * ff_v_product_swap_old) + (1))) /\ ((((exists ff_h_product_swap_old_terminal. ff_h_product_swap_old_terminal + S (p) = S ((S (S n)) * ff_v_product_swap_old)) /\ exists ff_q_product_swap_old_terminal. ff_u_product_swap_old = ff_q_product_swap_old_terminal * S ((S (S n)) * ff_v_product_swap_old) + (p))) /\ forall ff_i_product_swap_old. (exists ff_lt_product_swap_old_bound. ff_lt_product_swap_old_bound + S ff_i_product_swap_old = S n) -> exists ff_p_product_swap_old ff_r_product_swap_old ff_s_product_swap_old. ((((exists ff_h_product_swap_old_factor. ff_h_product_swap_old_factor + S (ff_p_product_swap_old) = S ((S (ff_i_product_swap_old)) * c)) /\ exists ff_q_product_swap_old_factor. b = ff_q_product_swap_old_factor * S ((S (ff_i_product_swap_old)) * c) + (ff_p_product_swap_old))) /\ ((((exists ff_h_product_swap_old_partial. ff_h_product_swap_old_partial + S (ff_r_product_swap_old) = S ((S (ff_i_product_swap_old)) * ff_v_product_swap_old)) /\ exists ff_q_product_swap_old_partial. ff_u_product_swap_old = ff_q_product_swap_old_partial * S ((S (ff_i_product_swap_old)) * ff_v_product_swap_old) + (ff_r_product_swap_old))) /\ ((((exists ff_h_product_swap_old_successor. ff_h_product_swap_old_successor + S (ff_s_product_swap_old) = S ((S (S ff_i_product_swap_old)) * ff_v_product_swap_old)) /\ exists ff_q_product_swap_old_successor. ff_u_product_swap_old = ff_q_product_swap_old_successor * S ((S (S ff_i_product_swap_old)) * ff_v_product_swap_old) + (ff_s_product_swap_old))) /\ ff_s_product_swap_old = ff_r_product_swap_old * ff_p_product_swap_old)))))) -> (exists ff_u_product_swap_new ff_v_product_swap_new. ((((exists ff_h_product_swap_new_start. ff_h_product_swap_new_start + S (1) = S ((S (0)) * ff_v_product_swap_new)) /\ exists ff_q_product_swap_new_start. ff_u_product_swap_new = ff_q_product_swap_new_start * S ((S (0)) * ff_v_product_swap_new) + (1))) /\ ((((exists ff_h_product_swap_new_terminal. ff_h_product_swap_new_terminal + S (q) = S ((S (S n)) * ff_v_product_swap_new)) /\ exists ff_q_product_swap_new_terminal. ff_u_product_swap_new = ff_q_product_swap_new_terminal * S ((S (S n)) * ff_v_product_swap_new) + (q))) /\ forall ff_i_product_swap_new. (exists ff_lt_product_swap_new_bound. ff_lt_product_swap_new_bound + S ff_i_product_swap_new = S n) -> exists ff_p_product_swap_new ff_r_product_swap_new ff_s_product_swap_new. ((((exists ff_h_product_swap_new_factor. ff_h_product_swap_new_factor + S (ff_p_product_swap_new) = S ((S (ff_i_product_swap_new)) * d)) /\ exists ff_q_product_swap_new_factor. z = ff_q_product_swap_new_factor * S ((S (ff_i_product_swap_new)) * d) + (ff_p_product_swap_new))) /\ ((((exists ff_h_product_swap_new_partial. ff_h_product_swap_new_partial + S (ff_r_product_swap_new) = S ((S (ff_i_product_swap_new)) * ff_v_product_swap_new)) /\ exists ff_q_product_swap_new_partial. ff_u_product_swap_new = ff_q_product_swap_new_partial * S ((S (ff_i_product_swap_new)) * ff_v_product_swap_new) + (ff_r_product_swap_new))) /\ ((((exists ff_h_product_swap_new_successor. ff_h_product_swap_new_successor + S (ff_s_product_swap_new) = S ((S (S ff_i_product_swap_new)) * ff_v_product_swap_new)) /\ exists ff_q_product_swap_new_successor. ff_u_product_swap_new = ff_q_product_swap_new_successor * S ((S (S ff_i_product_swap_new)) * ff_v_product_swap_new) + (ff_s_product_swap_new))) /\ ff_s_product_swap_new = ff_r_product_swap_new * ff_p_product_swap_new)))))) -> p = q
```

## Dependencies

- [[beta_product_replace_balance]]
- [[beta_product_succ_decompose]]
- [[beta_at_unique]]
- [[le_succ]]
- [[le_refl]]
- [[lt_irrefl_expanded]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **7439 nodes**, depth **67**.
- Authored script length: **102 commands**.
- Runtime card: `pa lib beta_product_swap_last_invariant`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
