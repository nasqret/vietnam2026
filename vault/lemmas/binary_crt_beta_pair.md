---
title: "Lemma: binary_crt_beta_pair"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `binary_crt_beta_pair`

Pairwise coprime beta moduli admit a single code realizing two bounded beta values.

## Closed Peano statement

```text
forall c i j a b. (forall d. (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1) -> (exists ha. ha + S a = S ((S i) * c)) -> (exists hb. hb + S b = S ((S j) * c)) -> exists code. (((exists ha. ha + S a = S ((S i) * c)) /\ exists q. code = q * S ((S i) * c) + a) /\ ((exists hb. hb + S b = S ((S j) * c)) /\ exists r. code = r * S ((S j) * c) + b))
```

## Dependencies

- [[beta_modulus_nonzero]]
- [[binary_crt]]
- [[beta_at_of_mod_eq_bound]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6941 nodes**, depth **69**.
- Authored script length: **47 commands**.
- Runtime card: `pa lib binary_crt_beta_pair`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
