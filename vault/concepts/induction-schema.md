---
title: Induction schema
tags: [peano-lab, arithmetic, induction]
---

# Induction schema

First-order Peano arithmetic does not quantify over predicates. Consequently induction is not one
second-order axiom but a **schema**: for every first-order formula $\varphi(n)$, there is an axiom

$$
\bigl(\varphi(0) \land \forall n\,(\varphi(n) \to \varphi(Sn))\bigr)
\to \forall n\,\varphi(n).
$$

Peano Lab's induction certificate records the chosen formula family plus proofs of its base and
step cases. The [[trusted-kernel]] instantiates the schema and checks both branches. The tactic is
only a convenient way to construct that certificate.

This distinction explains the first important rung of the [[theorem-ladder]]: $n+0=n$ is a defining
equation, while $0+n=n$ needs induction because recursion is on the second argument.

## Related

- [[peano-lab]]
- [[proof-certificate]]
- [[theorem-ladder]]
