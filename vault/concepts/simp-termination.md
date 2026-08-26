---
title: Simplifier termination
tags: [peano-lab, rewriting, automation]
---

# Simplifier termination

An equation is not automatically a safe simplification rule. Orienting equations both ways creates
immediate loops, and even a one-way rule can increase the printed size of a term.

Peano Lab's `simp` uses an explicit ordered rule set. A lexicographic path ordering admits a rewrite
only in a documented decreasing direction, including recursive arithmetic rules whose surface size
may grow. It also remembers the equality proof used at each step, so simplification constructs a
[[proof-certificate]] rather than asking the [[trusted-kernel]] to trust normalization.

Termination here is a property of this finite simplifier and its ordering. It is not a decision
procedure for every theorem of Peano arithmetic.

## Related

- [[theorem-ladder]]
- [[checked-numerical-normalization]]
- [[tactical]]
- [[peano-lab]]
