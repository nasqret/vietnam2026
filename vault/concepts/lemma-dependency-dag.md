---
title: Lemma dependency DAG
tags: [library, dependency-graph, peano-arithmetic]
---

A **lemma dependency DAG** makes prerequisite structure executable. Every
checked theorem depends only on earlier nodes, so replay can construct a
temporary curried target, package closed dependency certificates in nested
[[self-contained-proof-sharing|self-contained Cuts]], and ask the
[[trusted-kernel]] to check the original formula from the empty context. Each
Cut embeds its full formula and proof rather than a dependency name or hash.

The exact checked graph is generated as
`artifacts/peano-library/dependency-graph.mmd`. The research graph is larger:
its nodes carry `checked_existing`, `checked_m20`, `planned_expressible`, or
`blocked_by_language` status. A blocked node must name the missing representation
or interface rather than masquerading as a theorem.

The current executable DAG contains 176 checked nodes: 23 baseline, 141
general foundational, and twelve fixed modular capstones. The 183-node
research graph adds three planned and four language-blocked endpoints.

The main spine is

$$
\text{equality}\to\text{semiring}\to\text{order}\to
\text{divisibility}\to\text{congruence}\to\text{division}\to\gcd\to
\text{primes}\to\text{factorization}.
$$

## Related

[[arithmetic-library-moc]] · [[foundational-arithmetic-library]] ·
[[theorem-ladder]] · [[proof-certificate]] · [[self-contained-proof-sharing]]
