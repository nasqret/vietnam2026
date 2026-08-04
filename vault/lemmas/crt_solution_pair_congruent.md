---
title: "Lemma: crt_solution_pair_congruent"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_solution_pair_congruent`

Any two solutions of one binary CRT problem agree modulo each modulus.

## Closed Peano statement

```text
forall m n a b x y. (((exists hgcrt_mod_left_pair_x_left hgcrt_mod_right_pair_x_left. x + m * hgcrt_mod_left_pair_x_left = a + m * hgcrt_mod_right_pair_x_left) /\ (exists hgcrt_mod_left_pair_x_right hgcrt_mod_right_pair_x_right. x + n * hgcrt_mod_left_pair_x_right = b + n * hgcrt_mod_right_pair_x_right))) -> (((exists hgcrt_mod_left_pair_y_left hgcrt_mod_right_pair_y_left. y + m * hgcrt_mod_left_pair_y_left = a + m * hgcrt_mod_right_pair_y_left) /\ (exists hgcrt_mod_left_pair_y_right hgcrt_mod_right_pair_y_right. y + n * hgcrt_mod_left_pair_y_right = b + n * hgcrt_mod_right_pair_y_right))) -> ((exists hgcrt_mod_left_pair_mod_m hgcrt_mod_right_pair_mod_m. x + m * hgcrt_mod_left_pair_mod_m = y + m * hgcrt_mod_right_pair_mod_m) /\ (exists hgcrt_mod_left_pair_mod_n hgcrt_mod_right_pair_mod_n. x + n * hgcrt_mod_left_pair_mod_n = y + n * hgcrt_mod_right_pair_mod_n))
```

## Dependencies

- [[mod_eq_symm]]
- [[mod_eq_trans]]

## Checked dependents

- [[crt_solution_class_iff_lcm]]

## Verification record

- Independently checked from the empty context.
- Certificate: **307 nodes**, depth **31**.
- Authored script length: **37 commands**.
- Runtime card: `pa lib crt_solution_pair_congruent`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
