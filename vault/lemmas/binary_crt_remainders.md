---
title: "Lemma: binary_crt_remainders"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `binary_crt_remainders`

Binary CRT with bounded residues exposed as directed quotient/remainder equations.

## Closed Peano statement

```text
forall m n a b. ~(m = 0) -> ~(n = 0) -> (forall d. (exists u. m = d * u) -> (exists v. n = d * v) -> d = 1) -> (exists ha. ha + S a = m) -> (exists hb. hb + S b = n) -> exists x q r. (x = q * m + a /\ x = r * n + b)
```

## Dependencies

- [[binary_crt]]
- [[mod_eq_to_remainder_decomposition]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **6890 nodes**, depth **66**.
- Authored script length: **44 commands**.
- Runtime card: `pa lib binary_crt_remainders`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
