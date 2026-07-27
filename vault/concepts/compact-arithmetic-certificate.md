---
title: Compact arithmetic certificate
tags: [peano-lab, arithmetic, induction, proof-certificate, optimization]
---

A **compact arithmetic certificate** is an ordinary Peano Lab proof tree selected for small expanded
size by the untrusted `compact_arith` tactic. It is not a compressed assertion, trusted arithmetic
oracle, or new kernel rule.

Version 1 works only on a focused rigid equality. The exact forms are `compact_arith` and
`compact_arith [h, <- k]`; the bracketed list names every local equality the tactic may use and fixes
its orientation. Unlisted context is not mined. The tactic does not choose an outer induction
invariant or existential witness. Those mathematical decisions remain visible in [[tactic-mode]].

The planner follows PA3--PA6's recursion on the second argument and memoizes a finite grammar of
equality paths and seeded [[induction-schema|induction]] recurrence templates. Every candidate is
built from the existing [[proof-certificate]] constructors, cut-normalized, and measured as an
expanded tree. The selected candidate is checked against the exact focused context and target; QED
later checks the whole proof again in the [[trusted-kernel]] against the original theorem.

The motivating parity replay with generic [[polynomial-normalization|ring normalization]] expands
to 30,030 proof-tree nodes. A separate hand-authored construction proves the same theorem in 180
nodes by using the recurrence-normal invariant $n^2+n=2x$, witness $x+S n$, specialized PA
recurrences, and one final whole-existential transport. The 180-node result is a checked upper bound
and current record, not a proof that 179 is impossible.

Peano Lab's current size metric counts occurrences of proof constructors, not the sizes of terms or
induction motives. It also counts a tree rather than a shared DAG. `compact_arith` may therefore
claim only the cheapest candidate in its stated finite grammar and limits, never an absolute global
minimum.

## Related

[[peano-lab]] · [[proof-certificate]] · [[polynomial-normalization]] · [[induction-schema]] ·
[[local-reasoning-cut]] · [[de-bruijn-criterion]] · [[godel-incompleteness]]
