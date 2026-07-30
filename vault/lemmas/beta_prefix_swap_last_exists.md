---
title: "Lemma: beta_prefix_swap_last_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_swap_last_exists`

Construct an extensional beta code with an interior entry swapped with the last.

## Closed Peano statement

```text
forall b c n i. (exists h. h + S i = n) -> exists z d x y. ((((exists ff_h_swap_exists_old_i. ff_h_swap_exists_old_i + S (x) = S ((S (i)) * c)) /\ exists ff_q_swap_exists_old_i. b = ff_q_swap_exists_old_i * S ((S (i)) * c) + (x))) /\ ((((exists ff_h_swap_exists_old_n. ff_h_swap_exists_old_n + S (y) = S ((S (n)) * c)) /\ exists ff_q_swap_exists_old_n. b = ff_q_swap_exists_old_n * S ((S (n)) * c) + (y))) /\ ((((exists ff_h_swap_exists_new_i. ff_h_swap_exists_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_swap_exists_new_i. z = ff_q_swap_exists_new_i * S ((S (i)) * d) + (y))) /\ ((((exists ff_h_swap_exists_new_n. ff_h_swap_exists_new_n + S (x) = S ((S (n)) * d)) /\ exists ff_q_swap_exists_new_n. z = ff_q_swap_exists_new_n * S ((S (n)) * d) + (x))) /\ forall j a. (exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> (((exists ff_h_swap_exists_old_j. ff_h_swap_exists_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_swap_exists_old_j. b = ff_q_swap_exists_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_swap_exists_new_j. ff_h_swap_exists_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_swap_exists_new_j. z = ff_q_swap_exists_new_j * S ((S (j)) * d) + (a)))))))
```

## Dependencies

- [[beta_at_exists]]
- [[beta_prefix_swap_last_from_entries]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **31742 nodes**, depth **87**.
- Authored script length: **39 commands**.
- Runtime card: `pa lib beta_prefix_swap_last_exists`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
