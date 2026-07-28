---
title: "Lemma: binary_crt_beta_pair_of_gap_dvd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `binary_crt_beta_pair_of_gap_dvd`

Discharge the beta-pair CRT coprimality premise from a divisible index gap.

## Closed Peano statement

```text
forall c i j gap a b. j = i + gap -> (exists k. c = gap * k) -> (exists ha. ha + S a = S ((S i) * c)) -> (exists hb. hb + S b = S ((S j) * c)) -> exists code. (((exists ha. ha + S a = S ((S i) * c)) /\ exists q. code = q * S ((S i) * c) + a) /\ ((exists hb. hb + S b = S ((S j) * c)) /\ exists r. code = r * S ((S j) * c) + b))
```

## Dependencies

- [[beta_moduli_coprime_of_gap_dvd]]
- [[binary_crt_beta_pair]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **12980 nodes**, depth **71**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib binary_crt_beta_pair_of_gap_dvd`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
