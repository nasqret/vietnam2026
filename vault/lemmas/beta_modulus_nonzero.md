---
title: "Lemma: beta_modulus_nonzero"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_modulus_nonzero`

Every Gödel-beta decoding modulus is nonzero.

## Closed Peano statement

```text
forall c i. ~(S ((S i) * c) = 0)
```

## Dependencies

- [[succ_ne_zero]]

## Checked dependents

- [[beta_at_exists]]
- [[beta_at_of_mod_eq_bound]]
- [[binary_crt_beta_pair]]
- [[beta_accumulated_product_step]]
- [[beta_crt_prefix_congruence_step]]
- [[bounded_beta_crt_prefix_invariant]]
- [[beta_exclusive_accumulated_product_step]]
- [[beta_exclusive_recode_congruence_step]]
- [[beta_prefix_extend]]

## Verification record

- Independently checked from the empty context.
- Certificate: **9 nodes**, depth **6**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib beta_modulus_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
