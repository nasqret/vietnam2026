---
title: "Lemma: lcm_exists_relational"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lcm_exists_relational`

Every pair of naturals has a relational LCM; this is the direct LCM projection of the compatible pair theorem.

## Closed Peano statement

```text
forall a b. exists l. ((((exists hlcm_left_factor_existence. l = a * hlcm_left_factor_existence) /\ (exists hlcm_right_factor_existence. l = b * hlcm_right_factor_existence)) /\ forall hlcm_common_existence. (exists hlcm_left_common_existence. hlcm_common_existence = a * hlcm_left_common_existence) -> (exists hlcm_right_common_existence. hlcm_common_existence = b * hlcm_right_common_existence) -> exists hlcm_least_factor_existence. hlcm_common_existence = l * hlcm_least_factor_existence))
```

## Dependencies

- [[gcd_lcm_compatible_exists]]

## Checked dependents

- [[canonical_lcm_exists_unique]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9071 nodes**, depth **61**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib lcm_exists_relational`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
