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

## Verification record

- Independently checked from the empty context.
- Certificate: **9 nodes**, depth **6**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib beta_modulus_nonzero`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
