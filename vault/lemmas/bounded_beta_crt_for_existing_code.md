---
title: "Lemma: bounded_beta_crt_for_existing_code"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `bounded_beta_crt_for_existing_code`

Fold-produced bounded CRT witness for residues decoded from an already supplied beta code.

## Closed Peano statement

```text
forall N c b. (forall t. (exists h. S t + S h = S N) -> exists q. c = S t * q) -> exists z. forall i a. (exists h. h + i = N) -> ((exists h. h + S a = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + a) -> exists u v. z + S ((S i) * c) * u = a + S ((S i) * c) * v
```

## Dependencies

- [[bounded_beta_crt_prefix_invariant]]
- [[le_refl]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **25545 nodes**, depth **79**.
- Authored script length: **22 commands**.
- Runtime card: `pa lib bounded_beta_crt_for_existing_code`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
