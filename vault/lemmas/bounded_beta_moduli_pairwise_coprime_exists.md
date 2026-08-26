---
title: "Lemma: bounded_beta_moduli_pairwise_coprime_exists"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_beta_moduli_pairwise_coprime_exists`

Every finite beta-modulus prefix admits a nonzero base making its distinct positions pairwise coprime.

## Closed Peano statement

```text
forall B. exists c. (~(c = 0) /\ forall i j. ~(i = j) -> (exists hi. hi + i = B) -> (exists hj. hj + j = B) -> forall d. (exists u. S ((S i) * c) = d * u) -> (exists v. S ((S j) * c) = d * v) -> d = 1)
```

## Dependencies

- [[bounded_common_multiple_exists]]
- [[beta_moduli_pairwise_coprime_bounded]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **7019 nodes**, depth **61**.
- Authored script length: **11 commands**.
- Runtime card: `pa lib bounded_beta_moduli_pairwise_coprime_exists`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
