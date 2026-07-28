---
title: Lemma dependency DAG
tags: [library, dependency-graph, peano-arithmetic]
---

A **lemma dependency DAG** makes prerequisite structure executable. Every
checked theorem depends only on earlier nodes, so replay can construct a
temporary curried target, substitute closed dependency certificates, eliminate
cuts, and ask the [[trusted-kernel]] to check the original formula.

The exact checked graph is generated as
`artifacts/peano-library/dependency-graph.mmd`. The research graph is larger:
its nodes carry `checked_existing`, `checked_m20`, `planned_expressible`, or
`blocked_by_language` status. A blocked node must name the missing representation
or interface rather than masquerading as a theorem.

The main spine is

$$
\text{equality}\to\text{semiring}\to\text{order}\to
\text{divisibility}\to\text{congruence}\to\text{division}\to\gcd\to
\text{primes}\to\text{factorization}.
$$

## Related

[[arithmetic-library-moc]] · [[foundational-arithmetic-library]] ·
[[theorem-ladder]] · [[proof-certificate]]
