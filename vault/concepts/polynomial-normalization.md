---
title: Certificate-producing polynomial normalization
tags: [peano-lab, arithmetic, normal-form, proof-certificate, tactics]
---

Peano Lab's `ring` turns a rigid equality over `0`, successor, `+`, and `·` into two deterministic
sparse polynomials. Monomials are ordered by total degree and then by their de Bruijn
variable/exponent tuples. Equal normal forms choose a proof path; they are not themselves evidence.

Every successful step is justified by PA3--PA6 or a rechecked certificate from the
[[commutative-semiring-basis]]. The generated [[proof-certificate]] is checked before the tactic
closes its goal, and QED checks the complete theorem again in the [[trusted-kernel]].

`ring` is intentionally argument-free and does not consume hypotheses. Conditional algebra remains
visible: introduce an equality with `trans`, prove the first identity, `rewrite` by the named
hypothesis, and prove the remaining identity. Different polynomials fail transactionally rather
than inviting heuristic search.

The normalizer also has explicit AST, variable, degree, monomial, coefficient, work, proof-size,
proof-depth, and wall-clock limits. Exceeding one is an honest tactic limit and leaves the
[[tactic-mode]] state unchanged.

## Related

[[normal-form]] · [[checked-numerical-normalization]] · [[simp-termination]] · [[theorem-ladder]] ·
[[de-bruijn-criterion]]
