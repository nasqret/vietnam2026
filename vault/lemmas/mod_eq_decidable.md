---
title: "Lemma: mod_eq_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_decidable`

Balanced congruence is constructively decidable for every natural modulus.

## Closed Peano statement

```text
forall d a b. (exists hgcrt_mod_left_decision_yes hgcrt_mod_right_decision_yes. a + d * hgcrt_mod_left_decision_yes = b + d * hgcrt_mod_right_decision_yes) \/ ~(exists hgcrt_mod_left_decision_no hgcrt_mod_right_decision_no. a + d * hgcrt_mod_left_decision_no = b + d * hgcrt_mod_right_decision_no)
```

## Dependencies

- [[eq_decidable]]
- [[mod_eq_zero_iff_eq]]
- [[mod_eq_decidable_nonzero]]

## Checked dependents

- [[generalized_binary_crt_solution_or_obstruction]]

## Verification record

- Independently checked from the empty context.
- Certificate: **2339 nodes**, depth **70**.
- Authored script length: **35 commands**.
- Runtime card: `pa lib mod_eq_decidable`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
