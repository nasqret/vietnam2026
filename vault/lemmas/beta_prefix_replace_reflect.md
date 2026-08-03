---
title: "Lemma: beta_prefix_replace_reflect"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_prefix_replace_reflect`

A decoded entry of a one-position replacement is either the replacement or the original entry.

## Closed Peano statement

```text
forall b c z d k i y. (exists h. h + S i = k) -> (((exists ff_h_replace_reflect_new_i. ff_h_replace_reflect_new_i + S (y) = S ((S (i)) * d)) /\ exists ff_q_replace_reflect_new_i. z = ff_q_replace_reflect_new_i * S ((S (i)) * d) + (y))) -> (forall j a. (exists h. h + S j = k) -> ~(j = i) -> (((exists ff_h_replace_reflect_old_j. ff_h_replace_reflect_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_replace_reflect_old_j. b = ff_q_replace_reflect_old_j * S ((S (j)) * c) + (a))) -> (((exists ff_h_replace_reflect_new_j. ff_h_replace_reflect_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_replace_reflect_new_j. z = ff_q_replace_reflect_new_j * S ((S (j)) * d) + (a)))) -> forall j a. (exists h. h + S j = k) -> (((exists ff_h_replace_reflect_new_j. ff_h_replace_reflect_new_j + S (a) = S ((S (j)) * d)) /\ exists ff_q_replace_reflect_new_j. z = ff_q_replace_reflect_new_j * S ((S (j)) * d) + (a))) -> ((j = i /\ a = y) \/ (~(j = i) /\ (((exists ff_h_replace_reflect_old_j. ff_h_replace_reflect_old_j + S (a) = S ((S (j)) * c)) /\ exists ff_q_replace_reflect_old_j. b = ff_q_replace_reflect_old_j * S ((S (j)) * c) + (a)))))
```

## Dependencies

- [[eq_decidable]]
- [[beta_at_exists]]
- [[beta_at_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1735 nodes**, depth **62**.
- Authored script length: **56 commands**.
- Runtime card: `pa lib beta_prefix_replace_reflect`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
