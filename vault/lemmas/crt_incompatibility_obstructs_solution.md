---
title: "Lemma: crt_incompatibility_obstructs_solution"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `crt_incompatibility_obstructs_solution`

Failure of gcd compatibility constructively refutes every common CRT solution.

## Closed Peano statement

```text
forall g m n a b. ((((exists hag_left_factor_crt_obstruction. m = g * hag_left_factor_crt_obstruction) /\ (exists hag_right_factor_crt_obstruction. n = g * hag_right_factor_crt_obstruction)) /\ forall hag_divisor_crt_obstruction. (exists hag_common_left_crt_obstruction. m = hag_divisor_crt_obstruction * hag_common_left_crt_obstruction) -> (exists hag_common_right_crt_obstruction. n = hag_divisor_crt_obstruction * hag_common_right_crt_obstruction) -> exists hag_greatest_factor_crt_obstruction. g = hag_divisor_crt_obstruction * hag_greatest_factor_crt_obstruction)) -> ~(exists hgcrt_mod_left_obstruction_compatibility hgcrt_mod_right_obstruction_compatibility. a + g * hgcrt_mod_left_obstruction_compatibility = b + g * hgcrt_mod_right_obstruction_compatibility) -> ~(exists x. (((exists hgcrt_mod_left_obstruction_solution_left hgcrt_mod_right_obstruction_solution_left. x + m * hgcrt_mod_left_obstruction_solution_left = a + m * hgcrt_mod_right_obstruction_solution_left) /\ (exists hgcrt_mod_left_obstruction_solution_right hgcrt_mod_right_obstruction_solution_right. x + n * hgcrt_mod_left_obstruction_solution_right = b + n * hgcrt_mod_right_obstruction_solution_right))))
```

## Dependencies

- [[crt_common_solution_implies_gcd_compatible]]

## Checked dependents

- [[generalized_binary_crt_solution_or_obstruction]]

## Verification record

- Independently checked from the empty context.
- Certificate: **560 nodes**, depth **35**.
- Authored script length: **19 commands**.
- Runtime card: `pa lib crt_incompatibility_obstructs_solution`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
